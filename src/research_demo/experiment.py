"""A small, reproducible analysis of a fictional three-arm savings experiment."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import random
from collections import Counter
from statistics import NormalDist
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RAW_CSV = ROOT / "data" / "raw" / "synthetic_savings_experiment.csv"
RAW_MANIFEST = ROOT / "data" / "raw" / "manifest.json"
PROCESSED_DIR = ROOT / "data" / "processed"
ARMS = ("control", "human", "ai")


def make_synthetic_participants(n: int = 60, seed: int = 20261003) -> list[dict[str, Any]]:
    """Generate balanced fictional participants; a fixed seed makes this repeatable."""
    if n <= 0 or n % len(ARMS):
        raise ValueError("n must be a positive multiple of three")
    rng = random.Random(seed)
    assignments = list(ARMS) * (n // len(ARMS))
    rng.shuffle(assignments)
    baseline = {"control": 250, "human": 320, "ai": 360}
    rows = []
    for i, arm in enumerate(assignments, start=1):
        amount = round(max(0, min(1000, rng.gauss(baseline[arm], 120))))
        # Fixed synthetic exceptions make the pre-registered exclusions visible.
        attention = "fail" if i in {7, 19, 38, 52} else "pass"
        seconds = 95 if i in {11, 24, 47} else rng.randint(130, 300)
        rows.append({
            "participant_id": f"SYN-{i:03d}",
            "consent": "yes",
            "eligible": "yes",
            "arm": arm,
            "saved_nok": amount,
            "attention": attention,
            "seconds": seconds,
        })
    return rows


def write_synthetic_raw(path: Path = RAW_CSV, *, n: int = 60, seed: int = 20261003) -> str:
    """Create the synthetic raw fixture and its checksum manifest."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = make_synthetic_participants(n=n, seed=seed)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    if path == RAW_CSV:
        RAW_MANIFEST.write_text(json.dumps({
            "file": path.name,
            "sha256": checksum,
            "seed": seed,
            "synthetic_only": True,
        }, indent=2) + "\n", encoding="utf-8")
    return checksum


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("There are no rows to write")
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def t_quantile(p: float, df: int) -> float:
    """Approximate quantile of Student's t distribution (standard library only).

    Uses the Cornish-Fisher expansion around the normal quantile. For p = 0.975
    it matches statistical tables to about 0.0001 for df >= 6, which is ample
    for reporting a 95% confidence interval.
    """
    if df < 6:
        raise ValueError("t_quantile needs at least 6 degrees of freedom")
    z = NormalDist().inv_cdf(p)
    g1 = (z**3 + z) / 4
    g2 = (5 * z**5 + 16 * z**3 + 3 * z) / 96
    g3 = (3 * z**7 + 19 * z**5 + 17 * z**3 - 15 * z) / 384
    g4 = (79 * z**9 + 776 * z**7 + 1482 * z**5 - 1920 * z**3 - 945 * z) / 92160
    return z + g1 / df + g2 / df**2 + g3 / df**3 + g4 / df**4


def ols_differences_with_ci(
    values_by_arm: dict[str, list[int]], reference: str = "control", level: float = 0.95
) -> dict[str, dict[str, float | int]]:
    """Each arm minus the reference arm, with an OLS standard error and t-based CI.

    This is the linear regression outcome ~ arm (reference = control) from the
    pre-analysis plan, written out by hand: the residual variance is pooled over
    all arms, so SE(arm - control) = sqrt(s2 * (1/n_arm + 1/n_control)) with
    N - k degrees of freedom.
    """
    groups = {arm: list(values) for arm, values in values_by_arm.items()}
    if any(len(values) < 2 for values in groups.values()):
        raise ValueError("each arm needs at least two included observations")
    means = {arm: sum(values) / len(values) for arm, values in groups.items()}
    residual_ss = sum((x - means[arm]) ** 2 for arm, values in groups.items() for x in values)
    n_total = sum(len(values) for values in groups.values())
    df = n_total - len(groups)
    pooled_variance = residual_ss / df
    t_crit = t_quantile(1 - (1 - level) / 2, df)

    results = {}
    for arm, values in groups.items():
        if arm == reference:
            continue
        difference = means[arm] - means[reference]
        se = math.sqrt(pooled_variance * (1 / len(values) + 1 / len(groups[reference])))
        results[f"{arm}_minus_{reference}"] = {
            "difference": round(difference, 2),
            "standard_error": round(se, 2),
            "ci_lower": round(difference - t_crit * se, 2),
            "ci_upper": round(difference + t_crit * se, 2),
            "degrees_of_freedom": df,
            "t_critical": round(t_crit, 4),
        }
    return results


def _ci_or_reason(values_by_arm: dict[str, list[int]]) -> dict[str, Any]:
    """Confidence intervals, or the reason they cannot be estimated (tiny samples)."""
    try:
        return ols_differences_with_ci(values_by_arm)
    except ValueError as exc:
        return {"not_estimable": str(exc)}


def run_experiment(
    raw_path: Path = RAW_CSV,
    output_dir: Path = PROCESSED_DIR,
    *,
    expected_sha256: str | None = None,
) -> dict[str, Any]:
    """Verify the frozen raw file, apply the pre-registered exclusions, summarize."""
    raw_path = Path(raw_path)
    if expected_sha256 is None and raw_path == RAW_CSV and RAW_MANIFEST.exists():
        expected_sha256 = json.loads(RAW_MANIFEST.read_text(encoding="utf-8"))["sha256"]
    raw_sha256 = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    if expected_sha256 and raw_sha256 != expected_sha256:
        raise ValueError("Raw synthetic data checksum changed; do not overwrite the source file")

    raw_rows = _read_rows(raw_path)
    clean_rows: list[dict[str, Any]] = []
    exclusion_counts: Counter[str] = Counter()
    for row in raw_rows:
        reasons = []
        if row["consent"] != "yes":
            reasons.append("no_consent")
        if row["eligible"] != "yes":
            reasons.append("ineligible")
        if row["attention"] != "pass":
            reasons.append("attention_fail")
        if int(row["seconds"]) < 120:
            reasons.append("under_120_seconds")
        clean_rows.append({**row, "included": "no" if reasons else "yes", "exclusion_reason": ";".join(reasons)})
        exclusion_counts.update(reasons)

    included = [row for row in clean_rows if row["included"] == "yes"]
    group_summary: dict[str, dict[str, float | int]] = {}
    means: dict[str, float] = {}
    values_by_arm: dict[str, list[int]] = {}
    for arm in ARMS:
        values = [int(row["saved_nok"]) for row in included if row["arm"] == arm]
        values_by_arm[arm] = values
        mean = round(sum(values) / len(values), 2) if values else 0.0
        means[arm] = mean
        group_summary[arm] = {"n": len(values), "mean_saved_nok": mean}

    # With a categorical arm and control as the reference, OLS point estimates
    # equal the differences in group means. The 95% CIs use the pooled residual
    # variance from that regression (amendment 1 in docs/preregistration.md).
    summary = {
        "study": "Fictional savings experiment; synthetic data only",
        "raw_file_sha256": raw_sha256,
        "n_raw": len(raw_rows),
        "n_included": len(included),
        "n_excluded": len(raw_rows) - len(included),
        "exclusion_counts_overlap_possible": dict(exclusion_counts),
        "rule": "Include consent=yes, eligible=yes, attention=pass, and seconds>=120",
        "groups": group_summary,
        "ols_point_estimates_nok_vs_control": {
            "human_minus_control": round(means["human"] - means["control"], 2),
            "ai_minus_control": round(means["ai"] - means["control"], 2),
        },
        "ols_differences_vs_control_95ci": _ci_or_reason(values_by_arm),
        "interpretation_note": "Synthetic demonstration only; estimates are not evidence about real people.",
    }
    output_dir = Path(output_dir)
    _write_rows(output_dir / "cleaned_savings_experiment.csv", clean_rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "analysis_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary

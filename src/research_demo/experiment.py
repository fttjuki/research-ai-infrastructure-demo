"""A small, reproducible analysis of a fictional three-arm savings experiment."""

from __future__ import annotations

import csv
import hashlib
import json
import random
from collections import Counter
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
    for arm in ARMS:
        values = [int(row["saved_nok"]) for row in included if row["arm"] == arm]
        mean = round(sum(values) / len(values), 2) if values else 0.0
        means[arm] = mean
        group_summary[arm] = {"n": len(values), "mean_saved_nok": mean}

    # With a categorical arm and control as the reference, OLS point estimates
    # equal group means and the two differences shown here. No p-values are implied.
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
        "interpretation_note": "Synthetic demonstration only; estimates are not evidence about real people.",
    }
    output_dir = Path(output_dir)
    _write_rows(output_dir / "cleaned_savings_experiment.csv", clean_rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "analysis_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary

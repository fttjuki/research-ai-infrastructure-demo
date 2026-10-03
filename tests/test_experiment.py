import csv
import hashlib
import tempfile
import unittest
from pathlib import Path

from research_demo.experiment import (
    make_synthetic_participants,
    ols_differences_with_ci,
    run_experiment,
    t_quantile,
    write_synthetic_raw,
)


class ExperimentTests(unittest.TestCase):
    def test_fixed_seed_makes_balanced_assignments(self):
        rows_a = make_synthetic_participants()
        rows_b = make_synthetic_participants()
        self.assertEqual(rows_a, rows_b)
        arms = [row["arm"] for row in rows_a]
        self.assertEqual([arms.count(arm) for arm in ("control", "human", "ai")], [20, 20, 20])

    def test_run_preserves_raw_and_applies_exclusions(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw = root / "raw.csv"
            checksum = write_synthetic_raw(raw)
            before = hashlib.sha256(raw.read_bytes()).hexdigest()
            report = run_experiment(raw, root / "processed", expected_sha256=checksum)
            after = hashlib.sha256(raw.read_bytes()).hexdigest()
            self.assertEqual(before, after)
            self.assertEqual(report["n_raw"], 60)
            self.assertLess(report["n_included"], report["n_raw"])
            self.assertTrue((root / "processed" / "cleaned_savings_experiment.csv").exists())

    def test_checksum_detects_changed_raw_file(self):
        with tempfile.TemporaryDirectory() as temp:
            raw = Path(temp) / "raw.csv"
            checksum = write_synthetic_raw(raw)
            raw.write_text(raw.read_text() + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "checksum changed"):
                run_experiment(raw, Path(temp) / "processed", expected_sha256=checksum)

    def test_no_consent_record_is_excluded(self):
        with tempfile.TemporaryDirectory() as temp:
            raw = Path(temp) / "raw.csv"
            rows = make_synthetic_participants(3)
            rows[0]["consent"] = "no"
            with raw.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            report = run_experiment(raw, Path(temp) / "processed")
            self.assertEqual(report["n_excluded"], 1)
            self.assertEqual(report["exclusion_counts_overlap_possible"]["no_consent"], 1)

    def test_committed_raw_file_matches_manifest(self):
        """The checked-in raw CSV must pass its own checksum, as users run it."""
        with tempfile.TemporaryDirectory() as temp:
            report = run_experiment(output_dir=Path(temp))
            self.assertEqual(report["n_raw"], 60)

    def test_t_quantile_matches_statistical_tables(self):
        # Published two-sided 95% critical values of Student's t
        for df, table_value in [(6, 2.4469), (10, 2.2281), (30, 2.0423), (50, 2.0086)]:
            self.assertAlmostEqual(t_quantile(0.975, df), table_value, places=3)

    def test_confidence_interval_by_hand(self):
        # Means 2, 3, 5; each arm has residual sum of squares 2, so the pooled
        # variance is 6 / (9 - 3) = 1 and SE(ai - control) = sqrt(1/3 + 1/3).
        result = ols_differences_with_ci({
            "control": [1, 2, 3],
            "human": [2, 3, 4],
            "ai": [4, 5, 6],
        })["ai_minus_control"]
        self.assertEqual(result["difference"], 3.0)
        self.assertEqual(result["standard_error"], 0.82)
        self.assertEqual(result["degrees_of_freedom"], 6)
        half_width = 2.4469 * (2 / 3) ** 0.5
        self.assertAlmostEqual(result["ci_lower"], 3 - half_width, places=2)
        self.assertAlmostEqual(result["ci_upper"], 3 + half_width, places=2)

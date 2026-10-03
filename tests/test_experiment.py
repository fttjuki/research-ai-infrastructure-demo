import csv
import hashlib
import tempfile
import unittest
from pathlib import Path

from research_demo.experiment import make_synthetic_participants, run_experiment, write_synthetic_raw


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

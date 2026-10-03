import tempfile
import unittest
from pathlib import Path

from research_demo.batch import run_resumable_batch


class BatchTests(unittest.TestCase):
    def test_checkpoint_skips_success_and_retries_failure(self):
        records = [{"record_id": f"R-{i}"} for i in range(1, 6)]
        calls = {}

        def processor(record, attempt):
            calls[record["record_id"]] = calls.get(record["record_id"], 0) + 1
            if record["record_id"] == "R-3" and attempt == 1:
                raise RuntimeError("temporary timeout")
            return {"result": "ok"}

        with tempfile.TemporaryDirectory() as temp:
            checkpoint = Path(temp) / "checkpoint.json"
            first = run_resumable_batch(records, processor, checkpoint, max_attempts=3)
            self.assertEqual(first["completed_total"], 2)
            self.assertEqual(first["failed_pending_retry"], 1)
            second = run_resumable_batch(records, processor, checkpoint, max_attempts=10)
            self.assertEqual(second["completed_total"], 5)
            self.assertEqual(second["failed_pending_retry"], 0)
            self.assertEqual(calls["R-1"], 1)
            self.assertEqual(calls["R-3"], 2)

    def test_budget_stops_before_next_attempt(self):
        records = [{"record_id": f"R-{i}"} for i in range(1, 4)]
        with tempfile.TemporaryDirectory() as temp:
            result = run_resumable_batch(
                records, lambda record, attempt: {"result": "ok"}, Path(temp) / "state.json",
                budget_usd=0.01, estimated_usd_per_attempt=0.01,
            )
            self.assertEqual(result["completed_total"], 1)
            self.assertEqual(result["queued"], 2)
            self.assertTrue(result["stopped_for_budget"])

"""Offline example of capped, checkpointed batch processing with retry on rerun."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
CheckpointState = dict[str, Any]


def _save_checkpoint(path: Path, state: CheckpointState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def run_resumable_batch(
    records: list[dict[str, str]],
    processor: Callable[[dict[str, str], int], dict[str, str]],
    checkpoint_path: Path,
    *,
    max_attempts: int = 100,
    budget_usd: float = 1.0,
    estimated_usd_per_attempt: float = 0.001,
) -> dict[str, Any]:
    """Resume successful work, retry previous failures, and stop at a soft budget.

    The budget is a local estimate used before each attempt. It is not a provider
    billing cap, and actual charges from a real provider can differ.
    """
    if max_attempts < 0 or budget_usd < 0 or estimated_usd_per_attempt < 0:
        raise ValueError("attempts and budget values must be non-negative")
    checkpoint_path = Path(checkpoint_path)
    state: CheckpointState = {
        "attempts": {},
        "completed": {},
        "failed": {},
        "estimated_spend_usd": 0.0,
    }
    if checkpoint_path.exists():
        state.update(json.loads(checkpoint_path.read_text(encoding="utf-8")))

    attempted_now = 0
    stopped_for_budget = False
    for record in records:
        record_id = record["record_id"]
        if record_id in state["completed"]:
            continue
        if attempted_now >= max_attempts:
            break
        if state["estimated_spend_usd"] + estimated_usd_per_attempt > budget_usd + 1e-12:
            stopped_for_budget = True
            break

        attempt_number = int(state["attempts"].get(record_id, 0)) + 1
        state["attempts"][record_id] = attempt_number
        state["estimated_spend_usd"] = round(
            state["estimated_spend_usd"] + estimated_usd_per_attempt, 6
        )
        attempted_now += 1
        try:
            state["completed"][record_id] = processor(record, attempt_number)
            state["failed"].pop(record_id, None)
        except Exception as exc:  # Persist the error so the run can resume safely.
            state["failed"][record_id] = {"error": str(exc), "attempt": attempt_number}
        _save_checkpoint(checkpoint_path, state)

    remaining = [r["record_id"] for r in records if r["record_id"] not in state["completed"]]
    return {
        "attempted_this_run": attempted_now,
        "completed_total": len(state["completed"]),
        "failed_pending_retry": len(state["failed"]),
        "queued": len(remaining),
        "estimated_spend_usd": state["estimated_spend_usd"],
        "stopped_for_budget": stopped_for_budget,
        "checkpoint": str(checkpoint_path),
    }


def run_demo() -> list[dict[str, Any]]:
    """Run 100 synthetic records in two passes; two fake errors succeed on retry."""
    records = [
        {"record_id": f"BATCH-{i:03d}", "text": f"Synthetic text example {i:03d}; fictional content."}
        for i in range(1, 101)
    ]

    def fake_processor(record: dict[str, str], attempt: int) -> dict[str, str]:
        if record["record_id"] in {"BATCH-007", "BATCH-031"} and attempt == 1:
            raise RuntimeError("simulated temporary API timeout")
        return {"label": "mock-positive", "source": "offline-simulation"}

    events = []
    with tempfile.TemporaryDirectory(prefix="research-demo-batch-") as temp_dir:
        checkpoint = Path(temp_dir) / "checkpoint.json"
        events.append({"pass": 1, **run_resumable_batch(
            records, fake_processor, checkpoint, max_attempts=45,
            budget_usd=1.0, estimated_usd_per_attempt=0.001,
        )})
        events.append({"pass": 2, **run_resumable_batch(
            records, fake_processor, checkpoint, max_attempts=100,
            budget_usd=1.0, estimated_usd_per_attempt=0.001,
        )})
    return events

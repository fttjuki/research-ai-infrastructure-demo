"""Command-line workflow with a safe, offline-by-default path."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from .api import APIError, analyze_synthetic_text, create_prolific_draft


def run_demo(*, live_llm: bool = False, create_draft: bool = False) -> list[dict[str, Any]]:
    data_path = Path(__file__).resolve().parents[2] / "data" / "synthetic_texts.json"
    records = json.loads(data_path.read_text(encoding="utf-8"))
    audit: list[dict[str, Any]] = []
    for record in records:
        audit.append({
            "step": "load_synthetic_record",
            "record_id": record["record_id"],
            "text_logged": False,
        })
        if live_llm:
            result = analyze_synthetic_text(record["text"])
            entry = {
                "record_id": record["record_id"],
                "label_and_reason": result.text,
                "model": result.model,
                "response_id": result.response_id,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "elapsed_ms": result.elapsed_ms,
            }
            input_rate = os.getenv("INPUT_USD_PER_MILLION")
            output_rate = os.getenv("OUTPUT_USD_PER_MILLION")
            if input_rate and output_rate:
                entry["estimated_cost_usd"] = result.estimated_cost_usd(
                    float(input_rate), float(output_rate)
                )
        else:
            entry = {
                "record_id": record["record_id"],
                "label_and_reason": "offline placeholder; no external model call",
                "model": "mock",
                "input_tokens": 0,
                "output_tokens": 0,
            }
        audit.append({"step": "llm_analysis", **entry})
    if create_draft:
        draft = create_prolific_draft()
        audit.append({"step": "prolific_draft_created", "study_id": draft.get("id")})
    else:
        audit.append({"step": "survey_platform", "status": "not_called"})
    return audit


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic research API demo")
    parser.add_argument("--live-llm", action="store_true", help="call OpenAI for synthetic snippets")
    parser.add_argument(
        "--create-prolific-draft",
        action="store_true",
        help="create an unpublished Prolific draft (no recruitment is started)",
    )
    args = parser.parse_args()
    try:
        for event in run_demo(live_llm=args.live_llm, create_draft=args.create_prolific_draft):
            print(json.dumps(event, ensure_ascii=False))
    except (APIError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()

"""Small HTTP adapters for OpenAI Responses and Prolific study drafts.

Adapters accept an opener so tests can exercise requests without credentials
or network access. They deliberately do not log request bodies or secrets.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

Opener = Callable[..., Any]


class APIError(RuntimeError):
    """A provider request failed or returned an invalid response."""


@dataclass(frozen=True)
class LLMResult:
    text: str
    response_id: str
    model: str
    input_tokens: int
    output_tokens: int
    elapsed_ms: int

    def estimated_cost_usd(
        self, input_usd_per_million: float, output_usd_per_million: float
    ) -> float:
        return (
            self.input_tokens * input_usd_per_million
            + self.output_tokens * output_usd_per_million
        ) / 1_000_000


def _read_json(response: Any) -> dict[str, Any]:
    try:
        payload = json.loads(response.read().decode("utf-8"))
    except (AttributeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise APIError("Provider returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise APIError("Provider returned an unexpected response")
    return payload


def analyze_synthetic_text(
    text: str,
    *,
    api_key: str | None = None,
    model: str | None = None,
    opener: Opener = urlopen,
) -> LLMResult:
    """Classify a synthetic text snippet with OpenAI's Responses API."""
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        raise APIError("Set OPENAI_API_KEY to use the live LLM demo")
    if not text.strip() or len(text) > 4_000:
        raise ValueError("text must contain 1–4000 characters")

    selected_model = model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    body = {
        "model": selected_model,
        "store": False,
        "max_output_tokens": 120,
        "input": (
            "For this synthetic research exercise, label the text as one of "
            "positive, negative, or mixed/unclear. Give one short reason. "
            "Do not infer sensitive traits. Text: " + text
        ),
    }
    request = Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    started = time.monotonic()
    try:
        with opener(request, timeout=30) as response:
            payload = _read_json(response)
    except HTTPError as exc:
        raise APIError(f"OpenAI request failed with HTTP {exc.code}") from exc
    except (TimeoutError, URLError) as exc:
        raise APIError("OpenAI request could not be completed") from exc

    output_text = payload.get("output_text")
    if not isinstance(output_text, str):
        parts: list[str] = []
        for item in payload.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                    parts.append(content["text"])
        output_text = "\n".join(parts)
    usage = payload.get("usage") or {}
    if not output_text or not isinstance(usage, dict):
        raise APIError("OpenAI response is missing text or usage information")
    try:
        return LLMResult(
            text=output_text,
            response_id=str(payload["id"]),
            model=str(payload.get("model", selected_model)),
            input_tokens=int(usage["input_tokens"]),
            output_tokens=int(usage["output_tokens"]),
            elapsed_ms=round((time.monotonic() - started) * 1000),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise APIError("OpenAI response is missing required metadata") from exc


def create_prolific_draft(
    *,
    api_token: str | None = None,
    opener: Opener = urlopen,
) -> dict[str, Any]:
    """Create one unpublished Prolific study draft; never publish or recruit."""
    token = api_token or os.getenv("PROLIFIC_API_TOKEN")
    if not token:
        raise APIError("Set PROLIFIC_API_TOKEN to create a draft")
    payload = {
        "name": "Synthetic research demo (draft only)",
        "description": "Demonstration study using synthetic data; review before use.",
        "external_study_url": "https://example.org/synthetic-survey",
        "prolific_id_option": "url_parameters",
        "total_available_places": 5,
        "estimated_completion_time": 2,
        # Prolific expects the reward in cents of the account currency (100 = 1.00).
        "reward": 100,
        # Required by Prolific. Verify the schema against the current API docs
        # before any live use; this demo only ever creates an unpublished draft.
        "completion_codes": [
            {
                "code": "SYNTHDEMO",
                "code_type": "COMPLETED",
                "actions": [{"action": "MANUALLY_REVIEW"}],
            }
        ],
    }
    request = Request(
        "https://api.prolific.com/api/v1/studies/",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with opener(request, timeout=30) as response:
            result = _read_json(response)
    except HTTPError as exc:
        raise APIError(f"Prolific request failed with HTTP {exc.code}") from exc
    except (TimeoutError, URLError) as exc:
        raise APIError("Prolific request could not be completed") from exc
    return result

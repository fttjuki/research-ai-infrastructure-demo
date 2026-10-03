import json

import unittest

from research_demo.api import APIError, analyze_synthetic_text, create_prolific_draft


class FakeResponse:
    def __init__(self, data):
        self.data = json.dumps(data).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.data


class APITests(unittest.TestCase):
  def test_openai_request_records_usage_without_logging_prompt(self):
    seen = {}

    def opener(request, timeout):
        seen["url"] = request.full_url
        seen["headers"] = request.headers
        seen["body"] = json.loads(request.data)
        seen["timeout"] = timeout
        return FakeResponse({
            "id": "resp_test",
            "model": "gpt-test",
            "output_text": "positive: helpful service",
            "usage": {"input_tokens": 23, "output_tokens": 7},
        })

    result = analyze_synthetic_text("synthetic text", api_key="test-secret", opener=opener)
    self.assertTrue(seen["url"].endswith("/v1/responses"))
    self.assertEqual(seen["headers"]["Authorization"], "Bearer test-secret")
    self.assertFalse(seen["body"]["store"])
    self.assertIn("synthetic text", seen["body"]["input"])
    self.assertEqual(result.input_tokens, 23)
    self.assertEqual(result.output_tokens, 7)
    self.assertAlmostEqual(result.estimated_cost_usd(2, 8), 0.000102)


  def test_openai_requires_key_before_network_call(self):
    import os
    old = os.environ.pop("OPENAI_API_KEY", None)
    try:
      with self.assertRaisesRegex(APIError, "OPENAI_API_KEY"):
        analyze_synthetic_text("text", opener=lambda *_a, **_k: self.fail("network called"))
    finally:
      if old is not None:
        os.environ["OPENAI_API_KEY"] = old


  def test_prolific_only_sends_draft_payload(self):
    seen = {}

    def opener(request, timeout):
        seen["url"] = request.full_url
        seen["headers"] = request.headers
        seen["body"] = json.loads(request.data)
        return FakeResponse({"id": "study_demo", "status": "draft"})

    result = create_prolific_draft(api_token="test-token", opener=opener)
    self.assertEqual(result["status"], "draft")
    self.assertTrue(seen["url"].endswith("/api/v1/studies/"))
    self.assertEqual(seen["headers"]["Authorization"], "Token test-token")
    self.assertEqual(seen["body"]["total_available_places"], 5)
    self.assertNotIn("publish", seen["body"])


  def test_prolific_requires_token_before_network_call(self):
    import os
    old = os.environ.pop("PROLIFIC_API_TOKEN", None)
    try:
      with self.assertRaisesRegex(APIError, "PROLIFIC_API_TOKEN"):
        create_prolific_draft(opener=lambda *_a, **_k: self.fail("network called"))
    finally:
      if old is not None:
        os.environ["PROLIFIC_API_TOKEN"] = old

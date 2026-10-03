import unittest
from research_demo.cli import run_demo


class CLITests(unittest.TestCase):
    def test_default_demo_is_offline_and_auditable(self):
        events = run_demo()
        self.assertEqual(len([event for event in events if event["step"] == "llm_analysis"]), 4)
        self.assertTrue(all(event.get("text_logged") is False for event in events if event["step"] == "load_synthetic_record"))
        self.assertEqual(events[-1], {"step": "survey_platform", "status": "not_called"})

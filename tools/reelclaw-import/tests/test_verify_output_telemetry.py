import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "_shared" / "verify-output.sh"


class VerifyOutputTelemetryTest(unittest.TestCase):
    def test_successful_openai_response_is_recorded_in_shared_usage_ledger(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "/Users/anicca/profitable-claude/bin/record_openai_usage.py", text
        )
        self.assertIn('os.environ.get("ANICCA_LOOP", "media-vision-qa")', text)
        self.assertIn('os.environ.get("ANICCA_TASK_LABEL", "verify-output")', text)
        self.assertIn('"--task-class", "vision-qa"', text)
        self.assertIn('"--operation", "vision_qa"', text)
        self.assertIn("input=json.dumps(payload)", text)
        self.assertIn('v=json.loads(payload["choices"][0]["message"]["content"])', text)


if __name__ == "__main__":
    unittest.main()

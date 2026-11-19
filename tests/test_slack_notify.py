"""slack_notify: report parsing picks the top card and its figures; missing keys skip without error."""

import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/ar_notify/scripts/slack_notify.py"
SPEC = importlib.util.spec_from_file_location("slack_notify", SCRIPT)
SLACK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SLACK)


class SlackNotifyTests(unittest.TestCase):
    def test_report_card_and_figures(self):
        with tempfile.TemporaryDirectory() as temp:
            report = Path(temp) / "v3.x.md"
            (Path(temp) / "figures").mkdir()
            for name in ("a", "b", "c", "d"):
                (Path(temp) / "figures" / f"{name}.png").write_bytes(b"png")
            report.write_text("Debug entrypoint: `run.py`\n\n# Report: v3 head swap\n\n**Date**: x\n\n"
                              "## Experiment Card — Planned vs Actual\n\n| | Planned | Actual |\n|---|---|---|\n"
                              "**Verdict**: passed (ΔAUC 0.012)\n\n![m](figures/a.png)\n![m](figures/b.png)\n"
                              "![m](figures/c.png)\n![m](figures/d.png)\n\n======\n\n## Summary\nlong detail\n")
            title, text, figures = SLACK.from_report(report)
            self.assertEqual(title, "Report: v3 head swap")
            self.assertIn("Verdict", text)
            self.assertNotIn("long detail", text)
            self.assertEqual([f.name for f in figures], ["a.png", "b.png", "c.png"])

    def test_missing_keys_skip(self):
        keys = {"SLACK_WEBHOOK_URL": "", "SLACK_BOT_TOKEN": "", "SLACK_CHANNEL_ID": ""}
        self.assertEqual(SLACK.notify("t", "x", [], keys=keys)["status"], "skipped")

    def test_key_file_parsing(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "slack.env"
            path.write_text("# c\nSLACK_WEBHOOK_URL='https://hooks.slack.com/x'\nSLACK_BOT_TOKEN=\n")
            self.assertEqual(SLACK.load_keys(path)["SLACK_WEBHOOK_URL"], "https://hooks.slack.com/x")


if __name__ == "__main__":
    unittest.main()

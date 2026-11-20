"""ar_notify: report cards become Slack text with text tables; the run wrapper always notifies."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/ar_notify/scripts"
SPEC = importlib.util.spec_from_file_location("slack_notify", SCRIPTS / "slack_notify.py")
SLACK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SLACK)


class SlackNotifyTests(unittest.TestCase):
    def test_report_card_as_text_table(self):
        with tempfile.TemporaryDirectory() as temp:
            report = Path(temp) / "v3.x.md"
            report.write_text("Debug entrypoint: `run.py`\n\n# Report: v3 head swap\n\n"
                              "## Experiment Card — Planned vs Actual\n\n| | Planned | Actual |\n|---|---|---|\n"
                              "| **Metric** | AUC | 0.812 vs 0.800 |\n\n**Verdict**: passed\n\n![m](figures/a.png)\n\n"
                              "======\n\n## Summary\nlong detail\n")
            title, text = SLACK.from_report(report)
            self.assertEqual(title, "Report: v3 head swap")
            self.assertIn("```\n", text)
            self.assertIn("Metric  AUC", text)
            self.assertIn("*Verdict*: passed", text)
            self.assertNotIn("|---", text)
            self.assertNotIn("figures/a.png", text)
            self.assertNotIn("long detail", text)

    def test_missing_webhook_skips(self):
        self.assertEqual(SLACK.notify("t", "x", keys={"SLACK_WEBHOOK_URL": ""})["status"], "skipped")

    def test_key_file_parsing(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "slack.env"
            path.write_text("# c\nSLACK_WEBHOOK_URL='https://hooks.slack.com/x'\nWANDB_URL=https://wandb.ai/me/p/workspace?nw=1\n")
            keys = SLACK.load_keys(path)
            self.assertEqual(keys["SLACK_WEBHOOK_URL"], "https://hooks.slack.com/x")
            self.assertEqual(SLACK.tracking_env(keys), {"WANDB_ENTITY": "me", "WANDB_PROJECT": "p"})
            self.assertIn("W&B: https://wandb.ai/me/p/workspace?nw=1", SLACK.notify("t", "x", keys=keys, dry_run=True)["message"])
            path.write_text("WANDB_URL=https://lab.wandb.io/team/proj\n")
            self.assertEqual(SLACK.tracking_env(SLACK.load_keys(path)),
                             {"WANDB_ENTITY": "team", "WANDB_PROJECT": "proj", "WANDB_BASE_URL": "https://lab.wandb.io"})

    def test_worktree_uses_main_checkout_settings(self):
        with tempfile.TemporaryDirectory() as temp:
            os.environ.pop("AR_SLACK_ENV", None)
            repo = Path(temp) / "proj"
            repo.mkdir()
            run = lambda *a, cwd=repo: subprocess.run(a, cwd=cwd, check=True, capture_output=True)
            run("git", "init", "-q", "-b", "main")
            run("git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "i")
            run("git", "worktree", "add", "-q", str(Path(temp) / "idea"), "-b", "idea/x")
            self.assertEqual(SLACK.env_file(Path(temp) / "idea"), repo / "__board__/project.env")

    def test_run_wrapper_notifies_and_keeps_exit_code(self):
        with tempfile.TemporaryDirectory() as temp:
            env = {**os.environ, "AR_SLACK_ENV": str(Path(temp) / "none.env")}
            for code in (0, 3):
                result = subprocess.run([sys.executable, str(SCRIPTS / "notify_run.py"), "--name", "smoke", "--",
                                         sys.executable, "-c", f"print('epoch 1 loss 0.5'); raise SystemExit({code})"],
                                        cwd=temp, env=env, text=True, capture_output=True)
                self.assertEqual(result.returncode, code)
                self.assertIn("epoch 1 loss 0.5", result.stdout)
                self.assertIn("[ar_notify]", result.stderr)
                self.assertIn('"status": "skipped"', result.stderr)

    def test_run_message_content(self):
        spec = importlib.util.spec_from_file_location("notify_run", SCRIPTS / "notify_run.py")
        run = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(run)
        title, text = run.message("v3 full", "python run.py", 1, 3725, ["Traceback", "ValueError: x"], None)
        self.assertIn("v3 full FAILED (exit 1) in 1h02m", title)
        self.assertIn("ValueError: x", text)


if __name__ == "__main__":
    unittest.main()

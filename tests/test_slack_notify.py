"""Only final development report summaries reach Slack; operational events stay local."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/ar_notify/scripts"
SPEC = importlib.util.spec_from_file_location("slack_notify", SCRIPTS / "slack_notify.py")
SLACK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SLACK)


class SlackNotifyTests(unittest.TestCase):
    def report(self, root):
        report = Path(root) / "__board__/reports/v1/v1.md"
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text("# Final results\n\n## Slack summary\n"
                          "- **Plan**: Compare two heads.\n"
                          "- **Results**: Accuracy 0.98 vs 0.97.\n"
                          "- **Takeaways**: Keep the new head.\n"
                          "- **W&B**: https://wandb.ai/team/project/runs/result\n")
        return report

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

    def test_result_summary_only_for_reports(self):
        with tempfile.TemporaryDirectory() as temp:
            report = Path(temp) / "__board__/reports/v3.x/v3.x.md"
            report.parent.mkdir(parents=True)
            summary = ("## Slack summary\n- **Plan**: Swap the head on MNIST vs the MLP baseline.\n"
                       "- **Results**: Accuracy 0.981 vs 0.975 (4 seeds).\n- **Takeaways**: Keep the head.\n"
                       "- **W&B**: https://wandb.ai/me/p/groups/v3\n")
            report.write_text("# Report: v3 head swap\n\n## Experiment Card\n| a | b |\n\n" + summary)
            title, text = SLACK.result_summary(report)
            self.assertEqual(title, "Report: v3 head swap")
            self.assertEqual(text.count("\n"), 3)
            self.assertIn("*Results:* Accuracy 0.981 vs 0.975 (4 seeds).", text)
            plan = Path(temp) / "plans/v3.x.md"
            plan.parent.mkdir()
            plan.write_text(report.read_text())
            with self.assertRaises(ValueError):
                SLACK.result_summary(plan)
            report.write_text(summary.replace("Keep the head.", "A. B. C. D. E. F."))
            with self.assertRaises(ValueError):
                SLACK.result_summary(report)

    def test_missing_webhook_skips(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(SLACK.notify(report=self.report(temp), keys={"SLACK_WEBHOOK_URL": ""})["status"], "skipped")

    def test_key_file_parsing(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "slack.env"
            path.write_text("# c\nSLACK_WEBHOOK_URL='https://hooks.slack.com/x'\nWANDB_URL=https://wandb.ai/me/p/workspace?nw=1\n")
            keys = SLACK.load_keys(path)
            self.assertEqual(keys["SLACK_WEBHOOK_URL"], "https://hooks.slack.com/x")
            self.assertEqual(SLACK.tracking_env(keys), {"WANDB_ENTITY": "me", "WANDB_PROJECT": "p"})
            self.assertEqual(keys["WANDB_URL"], "https://wandb.ai/me/p/workspace?nw=1")
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
            quiet = subprocess.run([sys.executable, str(SCRIPTS / "notify_run.py"), "--", sys.executable, "-c", "print(1)"],
                                   cwd=temp, env=env, text=True, capture_output=True)
            self.assertNotIn("[ar_notify]", quiet.stderr)                       # part of a task: no Slack
            for code in (0, 3):
                result = subprocess.run([sys.executable, str(SCRIPTS / "notify_run.py"), "--notify", "--name", "smoke", "--",
                                         sys.executable, "-c", f"print('epoch 1 loss 0.5'); raise SystemExit({code})"],
                                        cwd=temp, env=env, text=True, capture_output=True)
                self.assertEqual(result.returncode, code)
                self.assertIn("epoch 1 loss 0.5", result.stdout)
                self.assertNotIn("[ar_notify]", result.stderr)  # even success is quiet without a report

    def test_run_wrapper_sends_only_a_new_valid_report(self):
        with tempfile.TemporaryDirectory() as temp:
            report = self.report(temp)
            body = report.read_text()
            env = {**os.environ, "AR_SLACK_ENV": str(Path(temp) / "none.env")}
            for content, status in ((body, "skipped"), ("# Incomplete report\n", "refused")):
                command = f"from pathlib import Path; Path({str(report)!r}).write_text({content!r}); print('raw log')"
                result = subprocess.run([sys.executable, str(SCRIPTS / "notify_run.py"), "--notify", "--",
                                         sys.executable, "-c", command], cwd=temp, env=env, text=True, capture_output=True)
                self.assertEqual(result.returncode, 0)
                self.assertIn(f'"status": "{status}"', result.stderr)
                self.assertNotIn("raw log", result.stderr)

    def test_flood_guard(self):
        with tempfile.TemporaryDirectory() as temp:
            SLACK.SENT_LOG = Path(temp) / "sent.tsv"
            self.assertEqual(SLACK.throttled("hook", "done 1"), "")
            self.assertIn("duplicate", SLACK.throttled("hook", "done 1"))
            for i in range(2, SLACK.MAX_PER_HOUR + 1):
                self.assertEqual(SLACK.throttled("hook", f"done {i}"), "")
            self.assertIn("this hour", SLACK.throttled("hook", "one too many"))
            self.assertEqual(SLACK.throttled("other-project", "done 1"), "")   # per webhook

    def test_operational_messages_are_refused_before_network_access(self):
        with mock.patch.object(SLACK.urllib.request, "urlopen") as post:
            for title in ("Explainability/localized-x-l-z: agent needs you", "plan ready", "run finished", "ar_goal done"):
                result = SLACK.notify(title, "Open Herdr tab Explainability:localized-x-l-z.",
                                      keys={"SLACK_WEBHOOK_URL": "https://example.invalid/hook"})
                self.assertEqual(result["status"], "refused")
            post.assert_not_called()
        result = subprocess.run([sys.executable, str(SCRIPTS / "slack_notify.py"),
                                 "--title", "agent needs you", "--text", "Open Herdr", "--dry-run"],
                                text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout)["status"], "refused")

    def test_final_report_summary_sends_once_without_extra_details(self):
        with tempfile.TemporaryDirectory() as temp:
            report = self.report(temp)
            keys = {"SLACK_WEBHOOK_URL": "https://example.invalid/hook", "WANDB_URL": "https://example.invalid/project"}
            with mock.patch.object(SLACK, "LEDGER", Path(temp) / "ledger.tsv"), \
                 mock.patch.object(SLACK, "SENT_LOG", Path(temp) / "sent.tsv"), \
                 mock.patch.object(SLACK.urllib.request, "urlopen") as post:
                result = SLACK.notify("ignored title", "ignored details", report=report, keys=keys)
                self.assertEqual(result["status"], "sent")
                message = json.loads(post.call_args.args[0].data)["text"]
                self.assertTrue(message.startswith("*Final results*"))
                self.assertIn("*Results:* Accuracy 0.98 vs 0.97.", message)
                self.assertNotIn("ignored", message)
                self.assertNotIn("https://example.invalid/project", message)
                self.assertEqual(SLACK.notify(report=report, keys=keys)["status"], "suppressed")
                post.assert_called_once()


if __name__ == "__main__":
    unittest.main()

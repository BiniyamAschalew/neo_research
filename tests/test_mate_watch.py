"""mate_watch: announces new plans once and new reports, skips what was already posted and old files."""

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

NEO = Path(__file__).resolve().parents[1]
TREE = NEO / "skills/ar_tree/scripts/ar_tree.py"


def sh(*args, cwd):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True).stdout


class MateWatchTests(unittest.TestCase):
    def test_plan_report_and_dedup(self):
        with tempfile.TemporaryDirectory() as temp:
            os.environ["AR_NOTIFY_LEDGER"] = str(Path(temp) / "ledger.tsv")
            os.environ["AR_SLACK_ENV"] = str(Path(temp) / "none.env")
            spec = importlib.util.spec_from_file_location("mate_watch", NEO / "skills/ar_mate/scripts/mate_watch.py")
            watch = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(watch)
            repo = Path(temp) / "proj"
            repo.mkdir()
            for cmd in (["git", "init", "-q", "-b", "main"], ["git", "config", "user.email", "t@t"], ["git", "config", "user.name", "t"]):
                sh(*cmd, cwd=repo)
            (repo / "a.py").write_text("x\n")
            sh("git", "add", ".", cwd=repo)
            sh("git", "commit", "-q", "-m", "i", cwd=repo)
            env = {**os.environ, "PATH": "/usr/bin:/bin"}
            subprocess.run([sys.executable, str(TREE), "new", "idea1", "--question", "q", "--no-herdr"], cwd=repo, env=env, check=True, capture_output=True)
            work = Path(temp) / "proj/.trees/idea1"
            old = work / "__board__/plans/v0.old.md"
            old.parent.mkdir(parents=True)
            old.write_text("# Plan v0\n")
            state = {"files": {}, "agents": {}, "started": False}
            watch.SLACK.notify = lambda *a, **k: self.fail("the watcher must never post to Slack")
            self.assertEqual(watch.check(repo, state), [])          # existing files are baseline
            plan = work / "__board__/plans/v1.x.md"
            plan.write_text("# Plan v1: x\n\n## Experiment Card\n\n| | |\n|---|---|\n| **Question** | q |\n\n======\n")
            self.assertEqual(len(watch.check(repo, state)), 1)      # plan: logged to the inbox
            plan.write_text(plan.read_text() + "edit\n")
            os.utime(plan, ns=(plan.stat().st_atime_ns, plan.stat().st_mtime_ns + 2_000_000_000))
            self.assertEqual(watch.check(repo, state), [])
            report = work / "__board__/reports/v1.x/v1.x.md"
            report.parent.mkdir(parents=True)
            report.write_text("# Report: v1\n\n## Experiment Card — Planned vs Actual\n\n**Verdict**: passed\n\n======\n")
            self.assertEqual(len(watch.check(repo, state)), 1)      # report: logged (the task posts it itself)
            goal = work / "__board__/goal/summary.md"
            goal.parent.mkdir(parents=True)
            goal.write_text("# Goal\n\nbest 0.91\n")
            self.assertEqual(len(watch.check(repo, state)), 1)      # goal: logged (goal.py posts its own summary)
            new = watch.STATUS.unread(repo)                                     # mate reads events, not agents
            self.assertEqual([("plan ready" in l, "experiment done" in l) for l in new][0], (True, False))
            self.assertTrue(any("experiment done" in l and "v1.x.md" in l for l in new))
            self.assertEqual(watch.STATUS.unread(repo), [])                     # cursor advanced

    def test_ensure_starts_once(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "proj"
            repo.mkdir()
            sh("git", "init", "-q", "-b", "main", cwd=repo)
            env = {**os.environ, "AR_SLACK_ENV": str(Path(temp) / "none.env")}
            watch = NEO / "skills/ar_mate/scripts/mate_watch.py"
            first = subprocess.run([sys.executable, str(watch), "--ensure", "--interval", "1"], cwd=repo, env=env, text=True, capture_output=True)
            self.assertIn("started", first.stdout)
            pid_file = repo / ".git/ar_mate_watch.pid"
            for _ in range(50):
                if pid_file.exists():
                    break
                import time; time.sleep(0.1)
            second = subprocess.run([sys.executable, str(watch), "--ensure"], cwd=repo, env=env, text=True, capture_output=True)
            self.assertIn("already running", second.stdout)
            os.kill(int(pid_file.read_text()), 15)


if __name__ == "__main__":
    unittest.main()

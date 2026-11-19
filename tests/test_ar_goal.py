"""ar_goal: keeps only improving changes, reverts the rest, rejects edits outside allowed files."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/ar_goal/scripts/goal.py"

AGENT = textwrap.dedent("""
    import sys, pathlib
    counter = pathlib.Path(sys.argv[1]); plan = [3, 1, "other", 5, 5]
    n = int(counter.read_text()) if counter.exists() else 0; counter.write_text(str(n + 1))
    step = plan[n] if n < len(plan) else 5
    if step == "other":
        pathlib.Path("eval.py").write_text(pathlib.Path("eval.py").read_text() + "# hack")
    else:
        pathlib.Path("model.py").write_text(f"x = {step}\\n")
    pathlib.Path("__board__/goal/change.txt").write_text(f"set x to {step}")
""")
EVAL = textwrap.dedent("""
    import json, os, pathlib, re
    x = int(re.search(r"x = (\\d+)", pathlib.Path("model.py").read_text()).group(1))
    name = "test_score" if os.environ.get("AR_GOAL_SPLIT") == "test" else "score"
    pathlib.Path("__board__/goal/metrics.json").write_text(json.dumps({name: x}))
""")


def sh(*args, cwd):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)


class GoalTests(unittest.TestCase):
    def test_loop_keeps_improvements_only(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "idea"
            repo.mkdir()
            for cmd in (["git", "init", "-q", "-b", "idea/x"], ["git", "config", "user.email", "t@t"], ["git", "config", "user.name", "t"]):
                sh(*cmd, cwd=repo)
            (repo / "model.py").write_text("x = 2\n")
            (repo / "eval.py").write_text(EVAL)
            (repo / "agent.py").write_text(AGENT)
            sh("git", "add", ".", cwd=repo)
            sh("git", "commit", "-q", "-m", "init", cwd=repo)
            counter = Path(temp) / "counter"
            config = {
                "objective": "raise x", "eval_cmd": f"{sys.executable} eval.py", "metrics_file": "__board__/goal/metrics.json",
                "metric": "score", "test_metric": "test_score", "goal": 5, "allowed": ["model.py"], "max_iters": 6,
                "baseline_repeats": 2, "min_delta": 0, "agent_cmd": [sys.executable, "agent.py", str(counter)],
            }
            (Path(temp) / "goal.json").write_text(json.dumps(config))
            env = {**os.environ, "AR_SLACK_ENV": str(Path(temp) / "none.env")}
            result = subprocess.run([sys.executable, str(SCRIPT), str(Path(temp) / "goal.json")], cwd=repo, env=env,
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            log = (repo / "__board__/goal/log.tsv").read_text()
            decisions = [line.split("\t")[3] for line in log.splitlines()[1:]]
            self.assertEqual(decisions, ["kept", "rejected", "outside:eval.py", "kept"])
            self.assertEqual((repo / "model.py").read_text(), "x = 5\n")
            self.assertNotIn("# hack", (repo / "eval.py").read_text())
            summary = (repo / "__board__/goal/summary.md").read_text()
            self.assertIn("goal reached", summary)
            self.assertIn("**Sealed test**: 5", summary)
            status = subprocess.run(["git", "status", "--porcelain"], cwd=repo, text=True, capture_output=True).stdout
            self.assertEqual(status, "")


if __name__ == "__main__":
    unittest.main()

"""Agent table, ar_mate command construction, and the install script."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

NEO = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("agents", NEO / "skills/references/agents.py")
AGENTS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AGENTS)


class AgentTests(unittest.TestCase):
    def test_skill_syntax_and_rules(self):
        self.assertEqual(AGENTS.skill("ar_plan", "claude"), "/ar_plan")
        self.assertEqual(AGENTS.skill("ar_plan", "codex"), "$ar_plan")
        skill = NEO / "skills/ar_mate/SKILL.md"
        self.assertEqual(AGENTS.AGENTS["claude"]["rules"](skill), ["--append-system-prompt-file", str(skill)])
        flag, value = AGENTS.AGENTS["codex"]["rules"](skill)
        key, text = value.split("=", 1)
        self.assertEqual((flag, key), ("-c", "developer_instructions"))
        self.assertEqual(json.loads(text), skill.read_text())  # a valid quoted TOML/JSON string
        with self.assertRaises(SystemExit):
            AGENTS.spec("definitely-not-an-agent")

    def test_ar_mate_builds_the_agent_command(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "proj"
            project.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=project, check=True)
            subprocess.run([str(NEO / "ar_init"), str(project)], check=True, capture_output=True)
            fake = Path(temp) / "bin"
            fake.mkdir()
            for name in ("claude", "codex"):  # stand-ins that print their argv
                (fake / name).write_text(f"#!{sys.executable}\nimport sys, json; print(json.dumps(sys.argv[1:]))\n")
                (fake / name).chmod(0o755)
            env = {**os.environ, "PATH": f"{fake}:{os.environ['PATH']}"}
            for agent, permission, first in (("claude", ["--permission-mode", "auto", "--settings"], "/ar_mate status"),
                                             ("codex", ["-c", 'approval_policy="on-request"', "-c", 'approvals_reviewer="auto_review"', "-c", "hide_agent_reasoning=true"],
                                              "$ar_mate status")):
                out = subprocess.run([str(NEO / "ar_mate"), agent, "--no-watch", "--", "--model", "x"], cwd=project,
                                     env=env, text=True, capture_output=True, check=True).stdout
                argv = json.loads(out.strip().splitlines()[-1])
                self.assertEqual(argv[:len(permission)], permission)
                self.assertEqual(argv[-3:], ["--model", "x", first])
                asked = subprocess.run([str(NEO / "ar_mate"), agent, "--no-watch", "--ask"], cwd=project,
                                       env=env, text=True, capture_output=True, check=True).stdout
                asked_argv = json.loads(asked.strip().splitlines()[-1])
                self.assertNotIn("auto", asked_argv if agent == "claude" else [])          # no auto mode
                self.assertNotIn('approvals_reviewer="auto_review"', asked_argv)            # --ask: you review

    def test_install_links_commands(self):
        with tempfile.TemporaryDirectory() as temp:
            env = {**os.environ, "AR_BIN": temp}
            subprocess.run([str(NEO / "install")], env=env, check=True, capture_output=True)
            for name in ("ar_init", "ar_mate"):
                self.assertEqual(os.path.realpath(Path(temp) / name), os.path.realpath(NEO / name))

    def test_review_round_uses_other_family(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "proj"
            repo.mkdir()
            run = lambda *a, cwd=repo, env=None: subprocess.run(a, cwd=cwd, env=env, check=True, capture_output=True, text=True)
            run("git", "init", "-q", "-b", "main")
            run("git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "i")
            fake = Path(temp) / "bin"
            fake.mkdir()
            (fake / "codex").write_text(f"#!{sys.executable}\nimport sys; print('1. [blocking] baseline untuned\\nVERDICT: REVISE'); "
                                        "open('argv.txt','w').write(' '.join(sys.argv[1:4]))\n")
            (fake / "codex").chmod(0o755)
            env = {**os.environ, "PATH": f"{fake}:/usr/bin:/bin"}
            run(sys.executable, str(NEO / "skills/ar_tree/scripts/ar_tree.py"), "new", "x", "--question", "q",
                "--no-herdr", "--agent", "claude", env={**env, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                                                         "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})
            work = Path(temp) / "proj/.trees/x"
            out = run(sys.executable, str(NEO / "skills/references/review.py"), "branch", cwd=work, env=env).stdout
            self.assertIn("REVISE", out)
            review = (work / "__board__/REVIEW.md").read_text()
            self.assertIn("reviewer: codex | author: claude", review)
            self.assertIn("baseline untuned", review)
            self.assertEqual((work / "argv.txt").read_text(), "exec -s read-only")

    def test_environment_activation(self):
        spec = importlib.util.spec_from_file_location("slack_notify", NEO / "skills/ar_notify/scripts/slack_notify.py")
        notify = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(notify)
        self.assertEqual(notify.activation({"CONDA_ENV": "opal"}, interactive=True), "conda activate opal")
        self.assertIn("conda shell.bash hook", notify.activation({"CONDA_ENV": "opal"}))
        self.assertEqual(notify.activation({"ENV_ACTIVATE": "source .venv/bin/activate"}), "source .venv/bin/activate")
        self.assertEqual(notify.activation({}), "")

    def test_mate_guard_blocks_code_edits_but_not_the_board(self):
        guard = NEO / "skills/ar_mate/scripts/mate_guard.py"
        def decide(path):
            event = {"cwd": "/p", "tool_name": "Write", "tool_input": {"file_path": path}}
            out = subprocess.run([sys.executable, str(guard)], input=json.dumps(event), text=True, capture_output=True).stdout
            return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out.strip() else "allow"
        self.assertEqual(decide("mnist_mlp.py"), "deny")
        self.assertEqual(decide("/p/models/x.py"), "deny")
        self.assertEqual(decide("__board__/ideas/x.md"), "allow")
        codex = AGENTS.AGENTS["codex"]["guard"](NEO / "skills/ar_mate/mate_review_policy.md")
        self.assertIn('sandbox_mode="read-only"', codex)
        self.assertIn("Deny", json.loads(codex[-1].split("=", 1)[1]))
        settings = json.loads(AGENTS.AGENTS["claude"]["guard"](guard)[1])
        self.assertEqual(settings["hooks"]["PreToolUse"][0]["matcher"], "Edit|Write|NotebookEdit|MultiEdit")


if __name__ == "__main__":
    unittest.main()

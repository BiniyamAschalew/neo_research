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
            for agent, flag, first in (("claude", "--append-system-prompt-file", "/ar_mate status"),
                                       ("codex", "-c", "$ar_mate status")):
                out = subprocess.run([str(NEO / "ar_mate"), agent, "--no-watch", "--", "--model", "x"], cwd=project,
                                     env=env, text=True, capture_output=True, check=True).stdout
                argv = json.loads(out.strip().splitlines()[-1])
                self.assertEqual(argv[0], flag)
                self.assertEqual(argv[-3:], ["--model", "x", first])

    def test_install_links_commands(self):
        with tempfile.TemporaryDirectory() as temp:
            env = {**os.environ, "AR_BIN": temp}
            subprocess.run([str(NEO / "install")], env=env, check=True, capture_output=True)
            for name in ("ar_init", "ar_mate"):
                self.assertEqual(os.path.realpath(Path(temp) / name), os.path.realpath(NEO / name))


if __name__ == "__main__":
    unittest.main()

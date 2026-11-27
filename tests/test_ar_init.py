"""ar_init: fresh setup, and upgrading an older setup without losing project-specific content."""

import importlib.machinery
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

NEO = Path(__file__).resolve().parents[1]
LOADER = importlib.machinery.SourceFileLoader("ar_init", str(NEO / "ar_init"))
SPEC = importlib.util.spec_from_loader("ar_init", LOADER)
AR_INIT = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(AR_INIT)


def status(project):
    return subprocess.run(["git", "status", "--porcelain"], cwd=project, text=True, capture_output=True).stdout


class ArInitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / "proj"
        self.project.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=self.project, check=True)
        AR_INIT.HOST_FILE = Path(self.temp.name) / "host.md"

    def assert_shared(self, relative):
        self.assertEqual(os.path.realpath(self.project / relative), os.path.realpath(NEO / relative), relative)

    def test_fresh_project(self):
        AR_INIT.init(self.project)
        for relative in AR_INIT.SHARED:
            self.assert_shared(relative)
        self.assertTrue((self.project / ".claude").is_dir() and not (self.project / ".claude").is_symlink())
        self.assertEqual(os.path.realpath(self.project / ".claude/settings.local.json"),
                         os.path.realpath(self.project / "__board__/claude/settings.local.json"))
        self.assertTrue((self.project / ".agents/skills/ar_tree/SKILL.md").exists())
        self.assertIn("SLACK_WEBHOOK_URL=", (self.project / "__board__/project.env").read_text())
        self.assertEqual(status(self.project).split(), ["??", ".gitignore", "??", "__board__/"])
        tracked = subprocess.run(["git", "add", "-n", "__board__"], cwd=self.project, text=True, capture_output=True).stdout
        self.assertNotIn("project.env", tracked)
        before = (self.project / "__board__/PROJECT.md").read_text()
        AR_INIT.init(self.project)  # idempotent
        self.assertEqual((self.project / "__board__/PROJECT.md").read_text(), before)

    def test_upgrade_old_setup_keeps_project_content(self):
        p = self.project
        # an older per-entry installation with copies, stale links and project-only additions
        (p / ".agents/skills").mkdir(parents=True)
        (p / ".agents/skills/ar_dev").symlink_to(NEO / "skills/ar_dev")                  # old shared link
        shutil.copytree(NEO / ".agents/skills/ar_note", p / ".agents/skills/ar_note")    # copied shared skill
        (p / ".agents/skills/ar-loop").symlink_to(NEO / "gone/ar-loop")                   # stale, dangling
        (p / ".agents/skills/my_local").mkdir()
        (p / ".agents/skills/my_local/SKILL.md").write_text("project-only skill")
        (p / ".claude/commands").mkdir(parents=True)
        (p / ".claude/commands/ar_plan.md").symlink_to(NEO / "adapters/claude/ar_plan.md")
        (p / ".claude/commands/my_cmd.md").write_text("project-only command")
        shutil.copy(NEO / "AGENTS.md", p / "AGENTS.md")                                   # unchanged shared copy
        (p / ".claude/CLAUDE.md").write_text("# Mine\nUse dataset Z with seed 7.\n")       # customized
        (p / ".claude/settings.local.json").write_text('{"permissions": {"allow": ["Bash(ls)"]}}')
        (p / ".codex").mkdir()
        (p / ".codex/config.toml").write_text('model = "gpt-5"\n')                        # project-specific config
        (p / "__board__/reports/v1").mkdir(parents=True)
        (p / "__board__/reports/v1/v1.md").write_text("results")
        (p / "__board__/STATUS.md").write_text("status")

        AR_INIT.init(p)

        self.assertEqual((p / "__board__/reports/v1/v1.md").read_text(), "results")
        self.assertEqual((p / "__board__/STATUS.md").read_text(), "status")
        self.assertEqual((p / ".agents/skills/my_local/SKILL.md").read_text(), "project-only skill")
        self.assertFalse(os.path.lexists(p / ".agents/skills/ar-loop"))
        for name in ("ar_dev", "ar_note", "ar_tree", "ar_goal", "ar_mate", "ar_notify"):
            self.assert_shared(f".agents/skills/{name}")
        self.assertEqual((p / ".claude/commands/my_cmd.md").read_text(), "project-only command")
        self.assert_shared(".claude/commands/ar_tree.md")
        self.assert_shared("AGENTS.md")
        self.assert_shared(".claude/CLAUDE.md")
        self.assertIn("Use dataset Z with seed 7.", (p / "__board__/PROJECT.md").read_text())
        self.assertIn("Bash(ls)", (p / "__board__/claude/settings.local.json").read_text())
        self.assertEqual((p / ".codex/config.toml").read_text(), 'model = "gpt-5"\n')
        backups = list((p / "__board__/notes/local/ar_init-backup").glob("*"))
        self.assertTrue((backups[0] / ".claude/CLAUDE.md").exists())
        self.assertTrue((backups[0] / ".agents/skills/ar_note/SKILL.md").exists())
        log = "\n".join(AR_INIT.init(p))  # second run: nothing left to change
        self.assertNotIn("replace", log)
        self.assertNotIn("migrate", log)

    def test_whole_folder_links_from_old_setup(self):
        elsewhere = Path(self.temp.name) / "old_neo"
        (elsewhere / ".claude").mkdir(parents=True)
        (self.project / ".claude").symlink_to(elsewhere / ".claude", target_is_directory=True)
        (self.project / ".agents").symlink_to(elsewhere / ".agents", target_is_directory=True)
        AR_INIT.init(self.project)
        self.assertFalse((self.project / ".claude").is_symlink())
        self.assert_shared(".agents")
        self.assertEqual(list((elsewhere / ".claude").iterdir()), [])

    def test_untrack_old_tracked_links(self):
        (self.project / "AGENTS.md").symlink_to("../neo_research/AGENTS.md")
        subprocess.run(["git", "add", "AGENTS.md"], cwd=self.project, check=True)
        log = "\n".join(AR_INIT.init(self.project))
        self.assertIn("--untrack", log)
        AR_INIT.init(self.project, untrack=True)
        self.assertEqual(subprocess.run(["git", "ls-files", "AGENTS.md"], cwd=self.project, text=True,
                                        capture_output=True).stdout, "")

    def test_dry_run_changes_nothing(self):
        AR_INIT.init(self.project, dry_run=True)
        self.assertEqual(list(self.project.iterdir()), [self.project / ".git"])

    def test_results_only_policy_and_index_migration_preserve_source(self):
        source = self.project / "run.py"
        source.write_text("print('local source')\n")
        subprocess.run(["git", "add", "run.py"], cwd=self.project, check=True)
        AR_INIT.init(self.project, untrack=True)
        report = self.project / "__board__/reports/v1/report.md"
        report.parent.mkdir(parents=True)
        report.write_text("result\n")
        raw = report.parent / "local/raw.txt"
        raw.parent.mkdir()
        raw.write_text("raw\n")
        subprocess.run(["git", "add", "."], cwd=self.project, check=True)
        paths = subprocess.check_output(["git", "ls-files"], cwd=self.project, text=True).splitlines()
        self.assertIn(".gitignore", paths)
        self.assertIn("__board__/reports/v1/report.md", paths)
        self.assertTrue(all(p == ".gitignore" or p.startswith("__board__/") for p in paths))
        self.assertNotIn("__board__/project.env", paths)
        self.assertNotIn("__board__/reports/v1/local/raw.txt", paths)
        self.assertEqual(source.read_text(), "print('local source')\n")

    def test_non_git_folder_is_refused(self):
        plain = Path(self.temp.name) / "plain"
        plain.mkdir()
        with self.assertRaises(SystemExit) as error:
            AR_INIT.init(plain)
        self.assertIn("git init", str(error.exception))
        self.assertEqual(list(plain.iterdir()), [])  # nothing created

    def test_repo_without_commits_gets_a_reminder(self):
        log = "\n".join(AR_INIT.init(self.project))
        self.assertIn("no commits yet", log)
    def test_refresh_adds_new_shared_skills_to_merged_folders(self):
        p = self.project
        (p / ".agents/skills/my_local").mkdir(parents=True)
        (p / ".agents/skills/my_local/SKILL.md").write_text("project-only")
        (p / ".agents/skills/ar-removed").symlink_to(NEO / "skills/does-not-exist")   # dangling old link
        AR_INIT.link_agents(p)
        self.assertEqual((p / ".agents/skills/my_local/SKILL.md").read_text(), "project-only")
        self.assertTrue((p / ".agents/skills/ar_branch/SKILL.md").exists())
        self.assertFalse(os.path.lexists(p / ".agents/skills/ar-removed"))

    def test_assets_are_linked_from_the_store(self):
        store = Path(self.temp.name) / "store"
        AR_INIT.init(self.project)
        (self.project / "assets.links").write_text("data/raw = datasets/citation\nmodels/checkpoints = checkpoints/proj\n")
        env = self.project / "__board__/project.env"
        env.write_text(env.read_text().replace("ASSETS_ROOT=", f"ASSETS_ROOT={store}"))
        (store / "datasets/citation").mkdir(parents=True)
        (store / "datasets/citation/x.csv").write_text("1")
        log = "\n".join(AR_INIT.init(self.project))
        self.assertIn("asset    data/raw", log)
        self.assertEqual((self.project / "data/raw/x.csv").read_text(), "1")
        self.assertTrue((store / "checkpoints/proj").is_dir())                  # created empty in the store
        self.assertNotIn("data/raw", status(self.project))                     # links never show in git
        (self.project / "models/real").mkdir(parents=True)
        (self.project / "assets.links").write_text("models/real = checkpoints/other\n")
        self.assertIn("CONFLICT models/real", "\n".join(AR_INIT.init(self.project)))


if __name__ == "__main__":
    unittest.main()

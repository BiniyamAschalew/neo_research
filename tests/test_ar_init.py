"""ar_init: links shared agent files, keeps Claude local state in __board__, never overwrites real files."""

import importlib.machinery
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

NEO = Path(__file__).resolve().parents[1]
LOADER = importlib.machinery.SourceFileLoader("ar_init", str(NEO / "ar_init"))
SPEC = importlib.util.spec_from_loader("ar_init", LOADER)
AR_INIT = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(AR_INIT)


class ArInitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / "proj"
        self.project.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=self.project, check=True)
        os.environ["AR_HOST_FILE"] = str(Path(self.temp.name) / "host.md")
        AR_INIT.HOST_FILE = Path(os.environ["AR_HOST_FILE"])

    def test_fresh_project(self):
        log, conflicts = AR_INIT.init(self.project)
        self.assertEqual(conflicts, [])
        for relative, shared in AR_INIT.SHARED.items():
            self.assertEqual((self.project / relative).resolve(), (NEO / shared).resolve(), relative)
        self.assertTrue((self.project / ".claude").is_dir() and not (self.project / ".claude").is_symlink())
        settings = self.project / ".claude/settings.local.json"
        self.assertEqual(settings.resolve(), (self.project / "__board__/claude/settings.local.json").resolve())
        self.assertTrue((self.project / "__board__/PROJECT.md").exists())
        self.assertTrue((self.project / ".agents/skills/ar_tree/SKILL.md").exists())
        status = subprocess.run(["git", "status", "--porcelain"], cwd=self.project, text=True, capture_output=True).stdout
        self.assertEqual(status.strip(), "?? __board__/")  # links ignored; only the board is project content
        self.assertEqual(AR_INIT.init(self.project)[1], [])  # idempotent

    def test_real_files_are_never_overwritten(self):
        (self.project / "AGENTS.md").write_text("my own notes")
        log, conflicts = AR_INIT.init(self.project)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual((self.project / "AGENTS.md").read_text(), "my own notes")
        AR_INIT.init(self.project, replace=True)
        self.assertTrue((self.project / "AGENTS.md").is_symlink())
        backups = list((self.project / "__board__/notes/local/ar_init-backup").glob("*/AGENTS.md"))
        self.assertEqual(backups[0].read_text(), "my own notes")

    def test_old_whole_claude_link_becomes_local_and_settings_move_to_board(self):
        elsewhere = Path(self.temp.name) / "shared_claude"
        elsewhere.mkdir()
        (self.project / ".claude").symlink_to(elsewhere, target_is_directory=True)
        AR_INIT.init(self.project)
        self.assertFalse((self.project / ".claude").is_symlink())
        self.assertEqual(list(elsewhere.iterdir()), [])  # nothing written into the old shared folder

    def test_dry_run_changes_nothing(self):
        AR_INIT.init(self.project, dry_run=True)
        self.assertEqual(list(self.project.iterdir()), [self.project / ".git"])


if __name__ == "__main__":
    unittest.main()

"""Exercise preservation, alias handling, relocation and transactional failure."""

import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/link_project_skills.py"
SPEC = importlib.util.spec_from_file_location("skill_links", SCRIPT)
LINKS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LINKS)


class SkillLinkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.canonical = self.root / "shared"
        for name in LINKS.SKILLS:
            skill = self.canonical / "skills" / name
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(f"{name}\n")
            adapter = self.canonical / "adapters/claude" / f"{name}.md"
            adapter.parent.mkdir(parents=True, exist_ok=True)
            adapter.write_text(name)
        (self.canonical / "skills/references").mkdir()
        self.project = self.root / "project"
        self.original = self.project / ".agents/skills/ar_dev"
        self.original.mkdir(parents=True)
        (self.original / "SKILL.md").write_text("local changes")
        (self.project / "untouched.txt").write_text("user work")

    def test_preserves_originals_and_is_idempotent(self):
        preview = LINKS.install([self.project], self.canonical)
        self.assertEqual(len(preview["changes"]), 2 * len(LINKS.SKILLS) + 1)
        self.assertEqual((self.original / "SKILL.md").read_text(), "local changes")
        result = LINKS.install([self.project], self.canonical, apply=True)
        self.assertEqual(self.original.resolve(), self.canonical / "skills/ar_dev")
        self.assertFalse(Path(self.original.readlink()).is_absolute())
        saved = next(x["backup"] for x in result["changes"] if x["backup"])
        self.assertEqual((Path(saved) / "SKILL.md").read_text(), "local changes")
        self.assertEqual((self.project / "untouched.txt").read_text(), "user work")
        self.assertEqual(LINKS.install([self.project], self.canonical, apply=True)["changes"], [])

    def test_parent_aliases_are_installed_once(self):
        alias = self.root / "alias"
        alias.mkdir()
        (alias / ".agents").symlink_to("../project/.agents", target_is_directory=True)
        (self.project / ".claude").mkdir()
        (alias / ".claude").symlink_to("../project/.claude", target_is_directory=True)
        result = LINKS.install([self.project, alias], self.canonical, apply=True)
        self.assertEqual(len(result["changes"]), 2 * len(LINKS.SKILLS) + 1)
        self.assertEqual((alias / ".agents/skills/ar_dev").resolve(), self.canonical / "skills/ar_dev")

    def test_broken_entrypoint_link_is_preserved(self):
        path = self.project / ".agents/skills/ar_plan"
        path.symlink_to("missing-old-target")
        result = LINKS.install([self.project], self.canonical, apply=True)
        saved = next(Path(x["backup"]) for x in result["changes"] if x["destination"] == str(path))
        self.assertTrue(saved.is_symlink())
        self.assertEqual(str(saved.readlink()), "missing-old-target")

    def test_missing_source_prevents_any_changes(self):
        shutil.rmtree(self.canonical / "skills/ar_metaplan")
        with self.assertRaises(ValueError):
            LINKS.install([self.project], self.canonical, apply=True)
        self.assertFalse(self.original.is_symlink())
        self.assertFalse((self.canonical / "__board__").exists())

    def test_relative_links_survive_sibling_relocation(self):
        LINKS.install([self.project], self.canonical, apply=True)
        moved = self.root / "moved"
        moved.mkdir()
        shutil.move(str(self.canonical), str(moved / "shared"))
        shutil.move(str(self.project), str(moved / "project"))
        self.assertEqual((moved / "project/.agents/skills/ar_dev/SKILL.md").read_text(), "ar_dev\n")

    def test_link_failure_restores_replaced_entries(self):
        original_symlink = Path.symlink_to
        count = 0

        def fail_once(path, *args, **kwargs):
            nonlocal count
            count += 1
            if count == 3:
                raise OSError("simulated link failure")
            return original_symlink(path, *args, **kwargs)

        with patch.object(Path, "symlink_to", fail_once):
            with self.assertRaises(OSError):
                LINKS.install([self.project], self.canonical, apply=True)
        self.assertFalse(self.original.is_symlink())
        self.assertEqual((self.original / "SKILL.md").read_text(), "local changes")
        self.assertFalse((self.project / ".agents/skills/ar_plan").exists())
        manifest = next((self.canonical / "__board__/notes/local/skill-links").glob("*/manifest.json"))
        self.assertEqual(json.loads(manifest.read_text())["status"], "rolled_back")


if __name__ == "__main__":
    unittest.main()

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("ar.py")
SPEC = importlib.util.spec_from_file_location("addis_ar", MODULE_PATH)
assert SPEC and SPEC.loader
ar = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ar)


class BoardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_init_is_lazy_and_preserves_existing_files(self):
        created = ar.initialize(self.root)
        self.assertEqual(set(created), {"STATUS.md", "record.md", "registry.jsonl", "config.yaml"})
        self.assertFalse((self.root / "__board__" / "runs").exists())
        status = self.root / "__board__" / "STATUS.md"
        status.write_text("custom\n")
        self.assertEqual(ar.initialize(self.root), [])
        self.assertEqual(status.read_text(), "custom\n")

    def test_allocate_is_sequential_and_experiment_only_creates_its_run(self):
        idea = ar.allocate(self.root, "idea", {})
        first = ar.allocate(self.root, "experiment", {"idea_id": idea})
        second = ar.allocate(self.root, "experiment", {"idea_id": idea})
        self.assertEqual((idea, first, second), ("I001", "E001", "E002"))
        self.assertTrue((self.root / "__board__" / "runs" / first).is_dir())
        self.assertFalse((self.root / "__board__" / "runs" / first / "state.json").exists())

    def test_state_and_resume_keep_done_distinct_from_accepted(self):
        experiment = ar.allocate(self.root, "experiment", {})
        ar.set_state(self.root, experiment, "running", {"command": "python3 experiment.py"})
        ar.set_state(self.root, experiment, "done", {})
        pending = ar.resume_state(self.root, None)
        self.assertEqual([run["status"] for run in pending["runs"]], ["done"])
        ar.set_state(self.root, experiment, "accepted", {})
        self.assertEqual(ar.resume_state(self.root, None)["runs"], [])

    def test_hash_changes_with_content(self):
        path = self.root / "result.txt"
        path.write_text("a")
        first = ar.hash_paths(self.root, ["result.txt"])["result.txt"]
        path.write_text("b")
        second = ar.hash_paths(self.root, ["result.txt"])["result.txt"]
        self.assertNotEqual(first, second)

    def test_evidence_checks_csv_json_and_missing_values(self):
        csv_path = self.root / "results.csv"
        csv_path.write_text("method,score\nreference,0.91\nbaseline,0.82\n")
        json_path = self.root / "results.json"
        json_path.write_text(json.dumps({"metrics": {"gap": 0.09}}))

        self.assertEqual(ar.check_evidence(self.root, "results.csv", "0.91", "C1")["status"], "verified")
        self.assertEqual(ar.check_evidence(self.root, "results.json", "0.09", "C2")["status"], "verified")
        self.assertEqual(ar.check_evidence(self.root, "results.csv", "0.99", "C3")["status"], "value_not_found")
        self.assertEqual(ar.check_evidence(self.root, "missing.csv", "1", "C4")["status"], "path_missing")

    def test_all_skills_have_codex_metadata_and_claude_adapters(self):
        package = MODULE_PATH.resolve().parents[2]
        names = {"ar-compact", "ar-dev", "ar-lit", "ar-loop", "ar-note", "ar-plan", "ar-record", "ar-review"}

        for name in names:
            skill = package / ".agents" / "skills" / name
            self.assertTrue((skill / "SKILL.md").is_file(), name)
            self.assertTrue((skill / "agents" / "openai.yaml").is_file(), name)
            self.assertTrue((package / ".claude" / "commands" / f"{name.replace('-', '_')}.md").is_file(), name)

    def test_four_symlinks_keep_boards_project_local(self):
        package = MODULE_PATH.resolve().parents[2]
        projects = [self.root / "p1", self.root / "p2", self.root / "p3"]
        entries = [".agents", ".claude", ".codex", "AGENTS.md"]

        for project in projects:
            project.mkdir()
            for entry in entries:
                (project / entry).symlink_to(package / entry, target_is_directory=(package / entry).is_dir())
            subprocess.run(
                [sys.executable, ".agents/tools/ar.py", "init", "."],
                cwd=project,
                check=True,
                capture_output=True,
                text=True,
            )

        configs = [project / "__board__" / "config.yaml" for project in projects]
        self.assertTrue(all(path.is_file() for path in configs))
        self.assertEqual(len({os.stat(path).st_ino for path in configs}), 3)

        source_skill = package / ".agents" / "skills" / "ar-loop" / "SKILL.md"
        linked_skills = [project / ".agents" / "skills" / "ar-loop" / "SKILL.md" for project in projects]
        self.assertTrue(all(os.stat(path).st_ino == os.stat(source_skill).st_ino for path in linked_skills))


if __name__ == "__main__":
    unittest.main()

"""Idea IDs remain shared across worktrees; evidence survives their retirement."""

from concurrent.futures import ThreadPoolExecutor
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/ar_idea/scripts/idea.py"
SPEC = importlib.util.spec_from_file_location("idea", SCRIPT)
IDEA = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IDEA)


class IdeaTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.git("init", "-q")
        self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "--allow-empty", "-qm", "initial")

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, text=True)

    def test_parallel_allocations_and_slug_reuse(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            paths = list(pool.map(lambda i: IDEA.create(self.root, f"idea-{i}", "question"), range(4)))
        self.assertEqual({p.parent.name.split("-")[0] for p in paths}, {"I001", "I002", "I003", "I004"})
        self.assertEqual(IDEA.create(self.root, "idea-0", "new wording"), paths[0])

    def test_worktree_uses_project_ids_and_preserves_linked_evidence(self):
        first = IDEA.create(self.root, "first", "question")
        work = self.root / ".trees/second"
        self.git("worktree", "add", "-qb", "idea/second", str(work))
        doc = IDEA.create(work, "second", "question")
        self.assertTrue(doc.parent.name.startswith("I002-"))
        self.assertTrue(first.parent.name.startswith("I001-"))
        papers = doc.parent / "papers"
        papers.mkdir()
        (papers / "paper.pdf").write_bytes(b"paper fixture")
        (papers / "summary.md").write_text("# Detailed paper summary\n")
        report = work / "__board__/reports/second/report.md"
        report.parent.mkdir(parents=True)
        report.write_text("[values](results.csv)\n")
        (report.parent / "results.csv").write_text("score\n0.8\n")
        with doc.open("a") as handle:
            handle.write("\n[report](../../reports/second/report.md)\n")
        copied = IDEA.preserve(self.root, work, "second")
        self.assertIn("__board__/reports/second/results.csv", copied)
        self.assertTrue((self.root / doc.relative_to(work)).read_text().endswith("report.md)\n"))
        self.assertEqual((self.root / papers.relative_to(work) / "paper.pdf").read_bytes(), b"paper fixture")

    def test_preservation_refuses_conflicting_evidence(self):
        work = self.root / ".trees/third"
        self.git("worktree", "add", "-qb", "idea/third", str(work))
        doc = IDEA.create(work, "third", "question")
        for base, content in ((self.root, "original"), (work, "different")):
            path = base / "__board__/reports/shared.md"
            path.parent.mkdir(parents=True)
            path.write_text(content)
        with doc.open("a") as handle:
            handle.write("\n[report](../../reports/shared.md)\n")
        with self.assertRaises(ValueError):
            IDEA.preserve(self.root, work, "third")
        self.assertEqual((self.root / "__board__/reports/shared.md").read_text(), "original")

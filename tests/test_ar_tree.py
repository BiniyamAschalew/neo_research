"""ar_tree: create an idea worktree, close it as dead (summary only reaches main), win-merge code only."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/ar_tree/scripts/ar_tree.py"


def sh(*args, cwd):
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=True).stdout


class ArTreeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.repo = base / "proj"
        self.repo.mkdir()
        os.environ["AR_ARCHIVE"] = str(base / "archive")
        os.environ["PATH"] = "/usr/bin:/bin"  # keep any real herdr out of tests
        for cmd in (["git", "init", "-q", "-b", "main"], ["git", "config", "user.email", "t@t"], ["git", "config", "user.name", "t"]):
            sh(*cmd, cwd=self.repo)
        (self.repo / ".gitignore").write_text("local/\n")
        (self.repo / "model.py").write_text("x = 1\n")
        sh("git", "add", ".", cwd=self.repo)
        sh("git", "commit", "-q", "-m", "init", cwd=self.repo)

    def tree(self, *args, cwd=None, check=True):
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd or self.repo, text=True, capture_output=True, check=check)

    def start(self, slug):
        self.tree("new", slug, "--question", "Does it help?", "--no-herdr")
        work = self.repo.parent / "proj.ideas" / slug
        (work / "model.py").write_text("x = 2\n")
        (work / "__board__/reports").mkdir(parents=True)
        (work / "__board__/reports/r.md").write_text("big report\n")
        (work / "local").mkdir()
        (work / "local/preds.npy").write_text("raw")
        sh("git", "add", "model.py", "__board__/reports/r.md", cwd=work)
        sh("git", "commit", "-q", "-m", "try", cwd=work)
        return work

    def fill_summary(self, slug):
        path = self.repo / "__board__/ideas" / f"{slug}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("## Question\nq\n## Approach\na\n## Main results\n| a | b |\n|---|---|\n| 1 | 2 |\n"
                        "## Why it failed\nw\n## Don't retry unless\nd\n")

    def test_dead_keeps_only_summary_on_main(self):
        work = self.start("try-a")
        self.assertIn("try-a", self.tree("list").stdout)
        self.assertNotIn('"status": "done"', self.tree("close", "try-a", "dead", "--yes", check=False).stdout)  # template unfilled
        self.fill_summary("try-a")
        self.assertIn("dry run", self.tree("close", "try-a", "dead").stdout)
        self.assertTrue(work.exists())
        self.assertIn('"status": "done"', self.tree("close", "try-a", "dead", "--yes").stdout)
        self.assertFalse(work.exists())
        self.assertEqual((self.repo / "model.py").read_text(), "x = 1\n")
        self.assertTrue((self.repo / "__board__/ideas/try-a.md").exists())
        self.assertFalse((self.repo / "__board__/reports").exists())
        self.assertIn("archive/try-a", sh("git", "tag", cwd=self.repo))
        self.assertEqual((Path(os.environ["AR_ARCHIVE"]) / "proj/try-a/local/preds.npy").read_text(), "raw")
        self.assertIn("| try-a | dead |", (self.repo / "__board__/ideas.md").read_text())

    def test_win_merges_code_and_results_not_bookkeeping(self):
        work = self.start("try-b")
        (self.repo / "other.py").write_text("main moved on\n")  # main changed after the idea branched
        sh("git", "add", "other.py", cwd=self.repo)
        sh("git", "commit", "-q", "-m", "main work", cwd=self.repo)
        self.fill_summary("try-b")
        self.tree("close", "try-b", "win", "--yes")
        self.assertEqual((self.repo / "model.py").read_text(), "x = 2\n")
        self.assertEqual((self.repo / "other.py").read_text(), "main moved on\n")
        self.assertEqual((self.repo / "__board__/reports/r.md").read_text(), "big report\n")
        self.assertEqual((self.repo / "local/preds.npy").read_text(), "raw")
        self.assertFalse((self.repo / "__board__/IDEA.md").exists())
        self.assertEqual(sh("git", "status", "--porcelain", cwd=self.repo), "")
        self.assertIn("| try-b | merged |", (self.repo / "__board__/ideas.md").read_text())

    def test_win_conflict_changes_nothing(self):
        work = self.start("try-d")
        (self.repo / "model.py").write_text("x = 9\n")  # same file changed on main
        sh("git", "commit", "-q", "-am", "main edit", cwd=self.repo)
        self.fill_summary("try-d")
        result = self.tree("close", "try-d", "win", "--yes", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("model.py", result.stdout + result.stderr)
        self.assertEqual((self.repo / "model.py").read_text(), "x = 9\n")
        self.assertTrue(work.exists())
        self.assertNotIn("archive/try-d", sh("git", "tag", cwd=self.repo))

    def test_dirty_worktree_blocks_close(self):
        work = self.start("try-c")
        (work / "model.py").write_text("dirty\n")
        self.fill_summary("try-c")
        result = self.tree("close", "try-c", "dead", "--yes", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(work.exists())

    def test_bury_removes_old_code_and_tags_it(self):
        (self.repo / "old").mkdir()
        (self.repo / "old/exp.py").write_text("old\n")
        sh("git", "add", ".", cwd=self.repo)
        sh("git", "commit", "-q", "-m", "old exp", cwd=self.repo)
        self.tree("bury", "old-exp", "--question", "q", "--paths", "old")
        self.fill_summary("old-exp")
        self.tree("bury", "old-exp", "--question", "q", "--paths", "old", "--yes")
        self.assertFalse((self.repo / "old").exists())
        self.assertIn("old/exp.py", sh("git", "show", "--name-only", "archive/old-exp", cwd=self.repo))

    def test_parallel_new_keeps_every_row_and_shares_settings(self):
        procs = [subprocess.Popen([sys.executable, str(SCRIPT), "new", f"p{i}", "--question", "q", "--no-herdr"], cwd=self.repo,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) for i in range(4)]
        self.assertEqual([p.wait() for p in procs], [0] * 4)
        registry = (self.repo / "__board__/ideas.md").read_text()
        self.assertEqual(sum(f"| p{i} |" in registry for i in range(4)), 4)
        work = self.repo.parent / "proj.ideas/p0"
        self.assertTrue((work / ".agents/skills/ar_tree/SKILL.md").exists())
        self.assertEqual(Path(os.readlink(work / ".claude/settings.local.json")),
                         self.repo / "__board__/claude/settings.local.json")
        self.assertEqual(sh("git", "status", "--porcelain", cwd=work), "")


if __name__ == "__main__":
    unittest.main()

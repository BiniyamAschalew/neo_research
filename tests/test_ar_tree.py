"""ar_tree: create an idea worktree, close it as dead (summary only reaches main), win-merge code only."""

import json
import os
import shlex
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

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
        work = self.repo / ".trees" / slug
        self.assertNotIn(".trees", sh("git", "status", "--porcelain", cwd=self.repo))  # inside the project, ignored
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

    def fake_herdr(self):
        """A different workspace is focused; the caller's existing max tab is 7."""
        base = Path(self.temp.name)
        binary = base / "bin"
        binary.mkdir()
        self.herdr_log = base / "herdr.jsonl"
        script = binary / "herdr"
        script.write_text(f"#!{sys.executable}\n" +
                          "import json, sys\nfrom pathlib import Path\n" +
                          f"log = Path({str(self.herdr_log)!r})\n" + """
args = sys.argv[1:]
calls = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
with log.open("a") as handle:
    handle.write(json.dumps(args) + "\\n")
if args[:2] == ["tab", "create"]:
    workspace = args[args.index("--workspace") + 1] if "--workspace" in args else "w9"
    previous = sum(call[:2] == ["tab", "create"] for call in calls)
    number = (8 if workspace == "w2" else 2) + previous
    print(json.dumps({"result": {"tab": {"tab_id": f"{workspace}:t{number}"},
                                 "root_pane": {"pane_id": f"{workspace}:p{number + 20}"}}}))
else:
    print("{}")
""")
        script.chmod(0o755)
        return mock.patch.dict(os.environ, {"PATH": f"{binary}:/usr/bin:/bin",
                                            "HERDR_ENV": "1", "HERDR_WORKSPACE_ID": "w2"})

    def assert_herdr_launch(self, index, slug, tab, pane):
        calls = [json.loads(line) for line in self.herdr_log.read_text().splitlines()]
        self.assertEqual(calls[index], ["tab", "create", "--workspace", "w2", "--cwd",
                                       str(self.repo / ".trees" / slug), "--label", f"proj:{slug}", "--no-focus"])
        self.assertEqual(calls[index + 1][:3], ["pane", "run", pane])
        row = next(row for row in json.loads(self.tree("list", "--json").stdout) if row["slug"] == slug)
        self.assertEqual((row["tab"], row["pane"]), (tab, pane))

    def test_new_tabs_stay_in_caller_workspace_and_append(self):
        with self.fake_herdr():
            for index, slug in enumerate(("first", "second")):
                self.tree("new", slug, "--question", "q", "--agent", "codex")
                self.assert_herdr_launch(index * 2, slug, f"w2:t{8 + index}", f"w2:p{28 + index}")
            self.tree("new", "no-tab", "--question", "q", "--no-herdr")
            self.assertEqual(len(self.herdr_log.read_text().splitlines()), 4)

    def test_open_branch_tab_stays_in_caller_workspace(self):
        work = self.start("candidate")
        self.fill_summary("candidate")
        self.compact(work)
        self.tree("branch", "candidate", "--new", "speedups", "--yes")
        with self.fake_herdr():
            self.tree("open", "speedups", "--agent", "codex")
            self.assert_herdr_launch(0, "b1-speedups", "w2:t8", "w2:p28")
            self.tree("open", "speedups")
            self.assertEqual(len(self.herdr_log.read_text().splitlines()), 2)

    def test_tab_creation_without_caller_context_keeps_cli_default(self):
        with self.fake_herdr():
            os.environ.pop("HERDR_WORKSPACE_ID")
            os.environ.pop("HERDR_ENV")
            result = json.loads(self.tree("new", "outside", "--question", "q").stdout)
            self.assertEqual(result["created"]["tab"], "w9:t2")
            calls = [json.loads(line) for line in self.herdr_log.read_text().splitlines()]
            self.assertNotIn("--workspace", calls[0])

    def test_maintenance_handoff_uses_existing_checkout_without_research_artifacts(self):
        script = SCRIPT.parents[2] / "ar_mate/scripts/mate_task.py"
        task = 'Create .gitignore; preserve literal "quotes" and $(text)'
        with self.fake_herdr():
            result = subprocess.run([sys.executable, str(script), task, "--agent", "codex"],
                                    cwd=self.repo, text=True, capture_output=True, check=True)
        launched = json.loads(result.stdout)
        self.assertEqual(launched, {"tab": "w2:t8", "pane": "w2:p28", "agent": "codex", "cwd": str(self.repo)})
        calls = [json.loads(line) for line in self.herdr_log.read_text().splitlines()]
        self.assertEqual(calls[0], ["tab", "create", "--workspace", "w2", "--cwd", str(self.repo),
                                   "--label", "proj:maintenance", "--no-focus"])
        self.assertEqual(calls[1][:3], ["pane", "run", "w2:p28"])
        command = shlex.split(calls[1][3])
        self.assertEqual(command[0], "codex")
        self.assertTrue(command[-1].startswith(f"Routine maintenance task: {task}\n"))
        self.assertNotIn("$ar_plan", command[-1])
        self.assertNotIn("$ar_dev", command[-1])
        self.assertFalse((self.repo / ".trees").exists())
        self.assertFalse((self.repo / "__board__").exists())
        self.assertEqual(sh("git", "status", "--porcelain", cwd=self.repo), "")

    def test_maintenance_without_herdr_does_not_create_research_artifacts(self):
        script = SCRIPT.parents[2] / "ar_mate/scripts/mate_task.py"
        result = subprocess.run([sys.executable, str(script), "Create .gitignore"],
                                cwd=self.repo, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no task was sent", result.stderr)
        self.assertFalse((self.repo / ".trees").exists())
        self.assertFalse((self.repo / "__board__").exists())

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

    def compact(self, work, verdict="ACCEPT", reviewer="codex"):
        self.rounds = getattr(self, "rounds", 0) + 1
        (work / "__board__/COMPACTION.md").write_text(f"# Compaction {self.rounds}\n**Parity**: equal\n")
        sh("git", "add", "__board__/COMPACTION.md", cwd=work)
        sh("git", "commit", "-q", "-m", "compact", cwd=work)
        (work / "__board__/REVIEW.md").write_text(f"# Review\n\n## Round {self.rounds} | stage: x | reviewer: {reviewer} | author: claude\n\n"
                                                  f"1. [minor] ok\nVERDICT: {verdict}\n\n**Verdict**: {verdict}\n")
        sh("git", "add", "__board__/REVIEW.md", cwd=work)
        sh("git", "commit", "-q", "-m", "review", cwd=work)

    def test_branch_requires_compaction_then_builds_branch(self):
        work = self.start("try-b")
        self.fill_summary("try-b")
        gated = self.tree("branch", "try-b", "--new", "speedups", "--yes", check=False)
        self.assertNotEqual(gated.returncode, 0)
        self.assertIn("compaction step", gated.stdout)
        self.compact(work)
        self.tree("branch", "try-b", "--new", "speedups", "--yes")
        self.assertFalse(work.exists())
        self.assertEqual((self.repo / "model.py").read_text(), "x = 1\n")             # main untouched
        self.assertEqual(sh("git", "show", "b1/speedups:model.py", cwd=self.repo), "x = 2\n")
        self.assertIn("__board__/reports/r.md", sh("git", "ls-tree", "-r", "--name-only", "b1/speedups", cwd=self.repo))
        files = sh("git", "ls-tree", "-r", "--name-only", "b1/speedups", cwd=self.repo)
        self.assertNotIn("COMPACTION.md", files)
        self.assertNotIn("IDEA.md", files)
        registry = (self.repo / "__board__/ideas.md").read_text()
        self.assertIn("branched:b1/speedups", registry)
        self.assertIn("| b1-speedups | active |", registry)
        self.assertEqual(sh("git", "status", "--porcelain", cwd=self.repo), "")
        # deepen the direction, then graduate it to main
        deeper = self.tree("new", "try-b2", "--question", "more", "--from", "speedups", "--no-herdr")
        work2 = self.repo / ".trees/try-b2"
        self.assertEqual((work2 / "model.py").read_text(), "x = 2\n")
        (work2 / "model.py").write_text("x = 3\n")
        sh("git", "commit", "-q", "-am", "deeper", cwd=work2)
        self.compact(work2)
        self.fill_summary("try-b2")
        self.tree("branch", "try-b2", "--yes")                         # default: its parent branch b1/speedups
        opened = self.tree("open", "speedups", "--no-herdr")
        dwork = self.repo / ".trees/b1-speedups"
        self.assertTrue(dwork.exists())
        gated = self.tree("merge", "speedups", "--yes", check=False)
        self.assertIn("compaction step", gated.stdout)
        self.compact(dwork)
        summary = self.repo / "__board__/branches/b1-speedups.md"
        summary.parent.mkdir(parents=True, exist_ok=True)
        summary.write_text("## Question\nq\n## Approach\na\n## Main results\n| a |\n|---|\n| 1 |\n## Why it failed\nDid not\n## Don't retry unless\nd\n")
        result = self.tree("merge", "speedups", "--yes", check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr + sh("git", "status", "--porcelain", "--untracked-files=no", cwd=self.repo))
        self.assertEqual((self.repo / "model.py").read_text(), "x = 3\n")
        self.assertFalse((self.repo / "__board__/COMPACTION.md").exists())
        self.assertFalse(dwork.exists())
        self.assertIn("archive/b1-speedups", sh("git", "tag", cwd=self.repo))
        self.assertNotIn("b1/speedups", sh("git", "branch", cwd=self.repo))
        self.assertEqual(sh("git", "status", "--porcelain", cwd=self.repo), "")

    def test_review_gate(self):
        work = self.start("try-r")
        self.fill_summary("try-r")
        self.compact(work, verdict="REVISE")
        out = self.tree("branch", "try-r", "--new", "r", "--yes", check=False).stdout
        self.assertIn("did not ACCEPT", out)
        self.compact(work, reviewer="claude")                      # same family as the author
        out = self.tree("branch", "try-r", "--new", "r", "--yes", check=False).stdout
        self.assertIn("author's own agent", out)
        self.compact(work)
        (work / "model.py").write_text("x = 5\n")                   # code after the review
        sh("git", "commit", "-q", "-am", "late change", cwd=work)
        out = self.tree("branch", "try-r", "--new", "r", "--yes", check=False).stdout
        self.assertIn("compaction step", out)
        self.compact(work)
        self.assertEqual(self.tree("branch", "try-r", "--new", "r", "--yes", check=False).returncode, 0)
        self.assertNotIn("REVIEW.md", sh("git", "ls-tree", "-r", "--name-only", "b1/r", cwd=self.repo))

    def test_branch_conflict_changes_nothing(self):
        work = self.start("try-d")
        self.compact(work)
        self.fill_summary("try-d")
        self.tree("branch", "try-d", "--new", "dirx", "--yes")
        work2 = self.start("try-e")                                   # from main, edits model.py too
        (work2 / "model.py").write_text("x = 7\n")
        sh("git", "commit", "-q", "-am", "conflicting", cwd=work2)
        self.compact(work2)
        self.fill_summary("try-e")
        orphan = self.tree("branch", "try-e", "--yes", check=False)        # started from main: must name a branch
        self.assertIn("give --into", orphan.stdout + orphan.stderr)
        result = self.tree("branch", "try-e", "--into", "dirx", "--yes", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(work2.exists())
        self.assertEqual(sh("git", "show", "b1/dirx:model.py", cwd=self.repo), "x = 2\n")

    def test_board_leftovers_are_committed_but_dirty_code_blocks_close(self):
        work = self.start("try-f")
        (work / "__board__/plans").mkdir(parents=True)
        (work / "__board__/plans/v1.x.md").write_text("plan")              # an uncommitted plan only
        self.fill_summary("try-f")
        self.assertEqual(self.tree("close", "try-f", "dead", "--yes", check=False).returncode, 0)
        self.assertIn("__board__/plans/v1.x.md", sh("git", "show", "--name-only", "archive/try-f", cwd=self.repo))

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
        work = self.repo / ".trees/p0"
        self.assertTrue((work / ".agents/skills/ar_tree/SKILL.md").exists())
        self.assertEqual(Path(os.readlink(work / ".claude/settings.local.json")),
                         self.repo / "__board__/claude/settings.local.json")
        self.assertEqual(sh("git", "status", "--porcelain", cwd=work), "")

    def test_branch_numbering_limit_and_tracker(self):
        names = []
        for i, name in enumerate(["ensembles", "context-compression"]):
            work = self.start(f"t{i}")
            self.compact(work)
            self.fill_summary(f"t{i}")
            self.tree("branch", f"t{i}", "--new", name, "--yes")
        branches = sh("git", "branch", cwd=self.repo)
        self.assertIn("b1/ensembles", branches)
        self.assertIn("b2/context-compression", branches)
        bad = self.tree("branch", "t9", "--new", "a-very-specific-cosine-lr-trick", check=False)
        self.assertNotEqual(bad.returncode, 0)
        self.tree("new", "deeper", "--question", "bagging?", "--from", "b1", "--no-herdr")
        tracker = (self.repo / "__board__/TRACKER.md").read_text()
        self.assertIn("`b1/ensembles`", tracker)
        self.assertIn("worktree `idea/deeper`: bagging?", tracker)
        self.assertIn("2 active, limit", tracker)
        os.environ["AR_MAX_BRANCHES"] = "2"
        try:
            work = self.start("t3")
            self.compact(work)
            self.fill_summary("t3")
            out = self.tree("branch", "t3", "--new", "third", "--yes", check=False).stdout
            self.assertIn("2 branches already active", out)
        finally:
            del os.environ["AR_MAX_BRANCHES"]

    def test_worktrees_get_asset_links(self):
        store = Path(self.temp.name) / "store"
        (store / "datasets/d").mkdir(parents=True)
        (store / "datasets/d/f.txt").write_text("shared")
        (self.repo / "assets.links").write_text("data/raw = datasets/d\n")
        sh("git", "add", "assets.links", cwd=self.repo)
        sh("git", "commit", "-q", "-m", "assets", cwd=self.repo)
        (self.repo / "__board__").mkdir(exist_ok=True)
        (self.repo / "__board__/project.env").write_text(f"ASSETS_ROOT={store}\n")
        self.tree("new", "with-data", "--question", "q", "--no-herdr")
        work = self.repo / ".trees/with-data"
        self.assertEqual((work / "data/raw/f.txt").read_text(), "shared")
        self.assertEqual(sh("git", "status", "--porcelain", cwd=work), "")


if __name__ == "__main__":
    unittest.main()


class AgentCommandTests(unittest.TestCase):
    def test_idea_agents_get_approve_for_me(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("ar_tree_mod", SCRIPT)
        tree = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tree)
        self.assertEqual(tree.agent_command("claude")[-2:], ["--permission-mode", "auto"])
        codex = tree.agent_command("codex")
        self.assertIn('approvals_reviewer="auto_review"', codex)
        self.assertNotIn("--cd", codex)        # idea agents write code; only the mate is sandboxed to __board__


class TaskPromptTests(unittest.TestCase):
    def test_one_handoff_runs_the_whole_chain(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("ar_tree_mod2", SCRIPT)
        tree = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tree)
        full = tree.task_prompt("codex", Path("/p"), "train an MLP on MNIST")
        self.assertTrue(full.startswith("$ar_metaplan train an MLP on MNIST"))
        self.assertIn("$ar_plan and then $ar_dev", full)
        self.assertIn("exactly one Slack message", full)
        self.assertTrue(tree.task_prompt("claude", Path("/p"), "run the specified baseline", quick=True).startswith("/ar_plan run the specified baseline"))

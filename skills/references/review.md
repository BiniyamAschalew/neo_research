# Cross-agent review (step 2 of ar_branch and ar_merge)

A reviewer from the other agent family (Codex for Claude work, Claude for Codex work) must be able to stop a weak result from moving up. Run after compaction, in the worktree being moved.

1. `python .agents/skills/references/review.py branch` (or `merge`) runs the reviewer read-only on the worktree and appends **Round N** (findings marked `[blocking]`/`[minor]` and a `VERDICT`) to `__board__/REVIEW.md`.
2. Answer every blocking finding under that round's **Author response**: fix it (code, rerun, report) and cite the commit, or argue with evidence. Never edit the reviewer's text. If code changed, redo the compaction parity step and refresh `COMPACTION.md`.
3. Commit and run the next round; the reviewer reads earlier rounds and your answers.
4. Stop at `ACCEPT`, or after three rounds bring the open disagreements (both sides' strongest point) to the human and record `**Human decision**: accept | reject — reason`.

The gate in `ar_tree branch|merge`: the last round accepts (or the human decision is accept), its reviewer differs from the author's agent, and `REVIEW.md` was committed after every code change and after `COMPACTION.md`. `--skip-review` is a human-only override. `REVIEW.md` stays with the tier it reviewed; its conclusion goes into the summary.

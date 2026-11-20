---
name: ar_review
description: Cross-agent discussion before ar_tree promote (worktree -> direction) and graduate (direction -> main). A reviewer from the other agent family (Codex for Claude work, Claude for Codex work) critiques evidence, baselines, leakage, compaction parity, code style and fit, read-only; the author answers each finding; up to three rounds, then ACCEPT or the human decides. ar_tree requires an ACCEPT in __board__/REVIEW.md newer than any code change.
---

# AR Review

Run after `ar_compact`, in the worktree being promoted or graduated. The goal is a real discussion, not a stamp: the reviewer must be able to stop a weak result from moving up.

## Rounds

1. `python .agents/skills/ar_review/scripts/review.py promote` (or `graduate`). It picks a reviewer from the other agent family, runs it read-only on this worktree, and appends **Round N** with its findings and `VERDICT` to `__board__/REVIEW.md`.
2. Answer every `[blocking]` finding under that round's **Author response**: fix it (code, rerun, report) and cite the commit, or argue with evidence why it does not apply. Never edit the reviewer's text.
3. If code changed, rerun `ar_compact`'s parity step (and refresh `COMPACTION.md`) before the next round.
4. Commit and run the next round; the reviewer reads the earlier rounds and your answers.
5. Stop at `ACCEPT`, or after three rounds: show the human the open disagreements and record their decision in `REVIEW.md` as `**Human decision**: accept | reject — reason`.

## Gate

`ar_tree promote|graduate` require that the last round in `REVIEW.md` says `**Verdict**: ACCEPT` (or a human decision `accept`), that its reviewer differs from the author's agent, and that `REVIEW.md` was committed after every code change and after `COMPACTION.md`. `--skip-review` is a human-only override. `REVIEW.md` stays with the tier it reviewed (it is not merged upward); its conclusion goes into the idea or direction summary.

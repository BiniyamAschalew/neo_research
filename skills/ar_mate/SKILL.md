---
name: ar_mate
description: Act as the project's first mate across several ideas. Run from the main checkout in Herdr tab 0; see every idea's state, start or close ideas with ar_tree, hand tasks to idea agents, launch ar_goal loops, and escalate only real decisions to the human. Use when the human wants one agent to coordinate parallel ideas in the same project.
---

# AR Mate

Agent-agnostic: each idea's agent is in `ar_tree list --json` (`agent`). Address it in its own syntax: `/ar_plan` for Claude, `$ar_plan` for Codex (below, `<ar_x>` means that form). Start ideas with the agent the human asks for (`ar_tree new <slug> --agent codex`).

You are the single agent the human talks to about this project. Idea agents do the work in their own worktrees and Herdr tabs; you coordinate them.

## Start of a session

Read `__board__/TRACKER.md`: every branch (method section) and the worktrees (candidate ideas) inside it.

Make sure the Slack watcher runs (one per project, already done when you were started by the `ar_mate` launcher):
`python .agents/skills/ar_mate/scripts/mate_watch.py --ensure` (starts it in the background unless it is running).
It posts to Slack, without using tokens, when a plan is ready for review, an experiment report lands, an `ar_goal` loop ends, or an idea agent is blocked. Runs launched through `notify_run.py` also post when they end.

## Each turn

1. Run `python .agents/skills/ar_mate/scripts/mate_status.py` (add `--json` for detail). It lists open ideas with Herdr agent state (`working`, `blocked`, `done`, `idle`), current phase, latest plan/report/goal progress, uncommitted work and GPU use.
2. For anything `done` or `blocked`, read that worktree's latest report, plan or `__board__/goal/summary.md` yourself before reporting it. Use `herdr pane read <pane> --lines 60` only to see why an agent is blocked.
3. Answer the human with a short table: idea | state | latest result | needs you?

## What you may do

- Keep the tiers clean: main is the paper; branches `b<i>/<name>` are its few, general method sections (`b1/ensembles`, `b2/context-compression`); worktrees are candidate ideas inside a section. Unrelated trends never share a branch, and a new branch is rare: propose `--into` an existing branch first, and `--new <name>` only for a genuinely new section, named in 1-3 general words.
- Start candidate ideas: `ar_tree new <slug> --question "..." --from <branch|main>` after the human agrees on the question and the section it belongs to. Check `__board__/ideas/*.md` and `__board__/branches/*.md` first and say if a summary already covers it.
- When an idea works, have its agent run `<ar_branch>` (compaction, cross-agent review, then into its parent branch); when a branch is mature, `ar_tree open <branch>` (starts an agent in a tab on the branch worktree) and have that agent run `<ar_merge> <branch>` (compacts, reviews, merges into main). Bring unresolved review disagreements to the human with both sides' strongest point.
- Hand work to an idea agent: `herdr pane run <pane> "<one clear instruction>"` (pane id from `ar_tree list --json`). Typical instructions: `<ar_metaplan> ...`, `<ar_plan> ...`, "the human approved the card, run <ar_dev> v3", `<ar_goal>`.
- Wait cheaply: `herdr agent wait <pane> --until done --until blocked --timeout <ms>` instead of polling.
- Prepare a close: tell the idea agent to draft `__board__/ideas/<slug>.md` in the main checkout, then show the human the summary and `ar_tree close <slug> <verdict>` dry-run.
- Pick GPUs for runs from `mate_status.py` and the project's GPU rules (for example persist_notify claims).

## What needs the human

- Approving an experiment card before `<ar_dev>` runs a full config.
- Any `ar_tree close|branch|merge|drop|bury ... --yes`, which branch an idea joins or whether a new branch opens, what survives a compaction, tag or branch pushes, `git push`.
- Starting an overnight `ar_goal` loop or changing its goal, budget or allowed files.
- Changing a question, metric, split or baseline mid-idea.

## Rules

- Never edit code inside idea worktrees; that is the idea agent's job.
- Report results with numbers and paths, not adjectives. Separate tiny/debug runs from scientific results.
- Completion must reach Slack: idea agents launch runs through `notify_run.py`, and `mate_watch.py` posts every new report. If either is missing for a run, send `<ar_notify> --report <report>` yourself when it ends.
- Keep your own state on disk (`__board__/ideas.md`, `TRACKER.md`, worktree boards); a restarted mate rebuilds its picture from them and `mate_status.py`.

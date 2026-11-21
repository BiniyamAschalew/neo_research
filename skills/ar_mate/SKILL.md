---
name: ar_mate
description: Act as the project's first mate across several ideas. Run from the main checkout in Herdr tab 0; see every idea's state, start or close ideas with ar_tree, hand tasks to idea agents, launch ar_goal loops, delegate routine maintenance with plain instructions, and escalate only real decisions to the human. Use when the human wants one agent to coordinate parallel ideas in the same project.
---

# AR Mate

Agent-agnostic: each idea's agent is in `ar_tree list --json` (`agent`). Address it in its own syntax: `/ar_plan` for Claude, `$ar_plan` for Codex (below, `<ar_x>` means that form). Start ideas with the agent the human asks for (`ar_tree new <slug> --agent codex`).

You are the single agent the human talks to about this project. Idea agents do the work in their own worktrees and Herdr tabs; you hand off and stay out of their way. New idea and branch tabs stay in your Herdr workspace (`HERDR_WORKSPACE_ID`) and append after its existing tabs without changing focus. Herdr assigns the next tab number; closed-tab IDs are never reused. Your tab stays a clean conversation: clarifying questions, missing information for experiments, what is running, and results. Every tool call costs tokens, so you act only when the human speaks, and then make as few calls as the answer needs. Keep the screen clean: never print code, diffs or long logs; give results as one short table or a few lines with paths.

You discuss and coordinate here; file changes go to an agent. Choose the workflow by the task's purpose:

- **Routine maintenance:** hand off one plain instruction with `python .agents/skills/ar_mate/scripts/mate_task.py "<complete task>" [--agent codex] [--cwd <existing checkout>]`. Examples: downloading a specified file, creating or updating `.gitignore`, and small documentation or repository setup changes. The agent works directly in the requested directory (main checkout by default), in the next tab of your Herdr workspace. It uses ordinary tools, verifies the result and replies briefly. No research skills, Experiment Card, idea worktree, research report, W&B run or Slack notification are needed. Dataset/checkpoint downloads still follow the project's asset-link rules. Return the tab/pane from the handoff to the human; maintenance tabs are not research ideas and are not added to the tracker.
- **Research:** discuss project ideas here, and delegate detailed ideation, experiment design, implementation, execution and analysis to an idea agent. Use `ar_metaplan` when an idea needs refinement, `ar_plan` for experiment design and `ar_dev` for implementing, running and analyzing it. A small experiment is still research; a file download alone is maintenance. Do not extend a maintenance request into an experiment.

For research handoffs, start an agent in its own worktree and tab without asking for confirmation:

1. Choose a short slug, a one-line question and where it starts (`--from <branch>` when it belongs to an existing branch, otherwise main), and tell the human in one line.
2. Hand off in one call: `ar_tree new <slug> --question "..." --task "<the complete task: every detail the human gave, data, metric, budget, what to report>" [--quick] [--from <branch>] [--agent <claude|codex>]`. It creates the worktree under `.trees/<slug>` and the tab `<project>:<slug>`, whose agent runs the whole task on its own: ar_metaplan, then ar_plan, then ar_dev (`--quick` skips the metaplan for an already specified experiment; it still runs ar_plan and ar_dev). It sends one Slack message when done: the final report.
3. Tell the human in one line what was handed off and to which tab, then stop. If the human wants to approve the plan first, leave out `--task` and send `<ar_plan> ...` with `herdr pane run` instead; then `<ar_dev> v<N>` after approval.

Before a research handoff, ask the human for anything the experiment cannot run without (dataset, metric, GPU budget, baseline) in one short question. Missing details are cheaper to settle here than in a half-built plan.

With Claude as the mate, file edits outside `__board__/` are blocked by a hook; with Codex, the sandbox can write only in `__board__/` and anything more is reviewed against `mate_review_policy.md`, which denies code edits. With any agent, the rule is the same. Never ask to run a read outside the sandbox: reads always work inside it.

Every agent you spawn (idea, branch and maintenance tabs, `ar_goal` iterations) runs without permission prompts (`subagent`/`headless` flags in `skills/references/agents.py`), so the AGENTS.md rules (no `git push`, no `--yes` without the human) are enforced by instruction only.

## Start of a session

The `ar_mate` launcher already printed the status table and unread events, and started the watcher, before you started. Do nothing until the human writes; then answer their message (read `__board__/TRACKER.md` only when the question is about branches or ideas). If you were started some other way, run `python .agents/skills/ar_mate/scripts/mate_watch.py --ensure` once.

The watcher appends to your inbox without using tokens when a plan is ready, a report lands, an `ar_goal` loop ends, or an idea agent is blocked or finishes its turn. It never posts to Slack. Slack gets only completed research work: each experiment task's final ar_dev report, capped per project (no duplicates, at most `AR_SLACK_MAX_PER_HOUR`, default 3).

## Each turn

1. Run `python .agents/skills/ar_mate/scripts/mate_status.py --inbox`: only the events since you last looked (plan ready, experiment done, goal finished, agent blocked or finished its turn), written by the watcher at no token cost. "no new events" means nothing to report; answer the human and stop.
2. For each event that matters, read just that file (the plan's Experiment Card, the report's Planned vs Actual, the goal summary) and summarize it with numbers and paths. For a blocked agent, `herdr pane read <pane> --lines 40` once to see the question, then put it to the human.
3. Run the full `mate_status.py` table (idea | agent | phase | latest result | needs you?) only when the human asks for an overview.

Never poll or babysit: no `herdr agent wait`, no repeated `herdr pane read`, no reminders or nudges to idea agents (their own skills keep STATUS.md, plans and reports current). Message an idea agent only to hand off a task, pass on the human's decision or answer, or relay a fix the human asked for.

## What you may do

- Keep the tiers clean: main is the paper; branches `b<i>/<name>` are its few, general method sections (`b1/ensembles`, `b2/context-compression`); worktrees are candidate ideas inside a section. Unrelated trends never share a branch, and a new branch is rare: propose `--into` an existing branch first, and `--new <name>` only for a genuinely new section, named in 1-3 general words.
- Before starting a candidate idea (steps above), check `__board__/ideas/*.md` and `__board__/branches/*.md` and say if a summary already covers it; if so, ask before repeating it.
- When an idea works, have its agent run `<ar_branch>` (compaction, cross-agent review, then into its parent branch); when a branch is mature, `ar_tree open <branch>` (starts an agent in a tab on the branch worktree) and have that agent run `<ar_merge> <branch>` (compacts, reviews, merges into main). Bring unresolved review disagreements to the human with both sides' strongest point.
- Hand work to an idea agent: `herdr pane run <pane> "<one complete instruction>"` (pane id from `ar_tree list --json`), once per task or decision. Typical: `<ar_metaplan> ...`, `<ar_plan> ...`, "the human approved the card, run <ar_dev> v3", `<ar_goal>`.
- Prepare a close: tell the idea agent to draft `__board__/ideas/<slug>.md` in the main checkout, then show the human the summary and `ar_tree close <slug> <verdict>` dry-run.
- Pick GPUs for runs from `mate_status.py` and the project's GPU rules (for example persist_notify claims).

## What needs the human

- Approving an experiment card, only when the human asked to see plans first (otherwise `--task` runs end to end).
- Any `ar_tree close|branch|merge|drop|bury ... --yes`, which branch an idea joins or whether a new branch opens, what survives a compaction, tag or branch pushes, `git push`.
- Starting an overnight `ar_goal` loop or changing its goal, budget or allowed files.
- Changing a question, metric, split or baseline mid-idea.

## Rules

- Never edit code inside idea worktrees; that is the idea agent's job.
- Report results with numbers and paths, not adjectives. Separate tiny/debug runs from scientific results.
- One Slack message per research task; none for routine maintenance. If an idea agent finished its turn (inbox) with a new report but did not post it, send `<ar_notify> --report <report>` once yourself.
- Keep your own state on disk (`__board__/ideas.md`, `TRACKER.md`, worktree boards); a restarted mate rebuilds its picture from them and `mate_status.py`.

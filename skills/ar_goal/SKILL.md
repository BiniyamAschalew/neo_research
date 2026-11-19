---
name: ar_goal
description: Set up and run an unattended (overnight) improvement loop inside an ar_tree idea worktree. Each iteration a fresh agent makes one component change within allowed files; the driver keeps it only if the validation metric beats the best by more than measured noise, reverts otherwise, evaluates the sealed test split once at the end and sends a Slack summary. Use for measurable model tuning with minor component updates, not for open-ended research questions.
---

# AR Goal

The driver `scripts/goal.py` (relative to this skill, following links) runs the loop deterministically. Your job is the setup, which decides whether the result can be trusted.

## Setup (with the human)

1. Work in an idea worktree (`ar_tree new <slug>`); the driver refuses `main`.
2. Make the evaluation honest before the loop starts:
   - `eval_cmd` runs the same pipeline as the experiment, reads `AR_GOAL_SPLIT` (`val` during the loop, `test` once at the end) and writes `metrics_file` as JSON.
   - Prefer the tiny or a bounded validation config so one evaluation fits the budget (`max_iters × eval time` must fit `max_hours`).
   - Evaluation, metric, split and data code must not be in `allowed`; the agent never sees test results.
   - Eval outputs must be git-ignored (default metrics file `__board__/goal/metrics.json` is).
3. Copy `goal.example.yaml` to `__board__/goal.yaml`, fill the objective, metric, goal, allowed files and budget, and commit it. Show the human the config as a short card (objective, metric/goal, allowed files, budget, noise rule) and get approval.
4. Dry run: `python .agents/skills/ar_goal/scripts/goal.py __board__/goal.yaml --dry-run` measures the baseline `baseline_repeats` times and sets the noise threshold (`delta_std_factor × std`, or `min_delta`). If the baseline std is 0 (deterministic eval), set `min_delta` to the smallest gain worth keeping.

## Run

Start it in its own Herdr tab so the mate can see it: `python .agents/skills/ar_goal/scripts/goal.py __board__/goal.yaml`. Rerunning resumes from `__board__/goal/best.json` and `log.tsv`.

Each iteration: fresh agent session (`agent_cmd`) with the objective, best value and history of kept/rejected changes → exactly one change → diff checked against `allowed` → evaluation → commit if better than best by more than the threshold, otherwise `git reset`. Stops on goal reached, `max_iters`, `max_hours` or `max_consecutive_failures`.

## Finish

The driver evaluates the best commit once on the test split, writes `__board__/goal/summary.md` and `progress.png`, commits them, and sends a Slack text summary via `ar_notify` (also on crash or Ctrl+C). Report the test number as the result; the validation number is selection-biased after many iterations. Kept changes are separate commits, so the human can revert or cherry-pick any of them. When the idea closes, use the summary for `__board__/ideas/<slug>.md`.

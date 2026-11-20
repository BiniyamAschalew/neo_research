---
name: ar_plan
description: Write an AutoResearch plan under __board__/plans/ that opens with a short, editable Experiment Card (question, change, concrete flow, comparison, runs, metric, decision rule, budget, editable keys) plus at most two synthetic figure previews, followed by an implementation appendix that reuses the entity-organized code base. The human edits the card before ar_dev runs. For research work, not routine downloads or repository housekeeping.
---

# AR Plan

Use this workflow for research ideation or experiments. For routine maintenance such as downloading a specified file or creating `.gitignore`, complete the task with ordinary tools and a short verification; do not create an experiment plan or report.

Work in the active project (or idea worktree). Read [board conventions](../references/board.md), `__board__/PROJECT.md`, `STATUS.md`, `__board__/IDEA.md` inside an idea worktree, and the main checkout's `TRACKER.md`, `ideas/*.md` and `branches/*.md`: do not re-plan a failed approach unless its "Don't retry unless" condition now holds (say which). Do not write code, except the plan's preview script. Record the actual agent as author.

## Steps

1. Read the relevant reports, notes and `structure.md` (verify the entries you rely on against source). Next `vN` = one above the highest in `__board__/plans/`.
2. Design the smallest change that answers the question, following [code style](../references/code-style.md) and, for executable work, [structured execution](../references/structured-execution.md): which entity code is reused or extended, any new entity and its `_build.py` registration, one `configs/expt/<name>.yaml` per case, tiny/full profile differences, `run.py` constants, the tracked real-data fixture, shared data/checkpoint folders (linked via `assets.links`, never copied), device and weight prerequisites, and what becomes obsolete and is deleted. When runs log to W&B, plan names, group, curves (with x-axis) and tables per [tracking](../references/tracking.md).
3. When the work publishes plots, render at most 2 **synthetic previews** of the deciding figures, matching the planned final plot exactly (chart type, axes, units, conditions, uncertainty, thresholds) and marked `SYNTHETIC PREVIEW` in the image and caption. Save a seeded matplotlib/numpy generator as `__board__/plans/vN.<slug>/preview_plots.py` and images under `__board__/plans/vN.<slug>/figures/<final-figure-name>.png`; run it and look at each image.
4. Write `__board__/plans/vN.<slug>.md`, then end your reply with the plan path, the card itself (so the human can edit it now) and the next command (`ar_dev vN`). If the human already authorized execution, continue with `ar_dev`.

## Template

```markdown
# Plan vN: [Title]

**Created**: YYYY-MM-DD | **Author**: [agent] | **Task**: [original request]

## Experiment Card

| | |
|---|---|
| **Question** | [One sentence.] |
| **Change** | [Baseline + the one component that differs; nothing else changes.] |
| **Flow** | `load(D: n=…, split …) → model(M, key dims) → train(k steps, opt, lr) → eval(metric on val)` |
| **Compare** | A = `configs/expt/<base>.yaml` vs B = `configs/expt/<new>.yaml` |
| **Data / splits** | [Datasets, split roles; test touched only at the end.] |
| **Runs** | [seeds × datasets × arms = total; independent unit.] |
| **Metric** | [Primary metric, direction, aggregation, uncertainty.] |
| **Decide** | [e.g. keep if ΔAUC ≥ 0.01 and 95% CI > 0; else stop the idea.] |
| **Budget** | [GPUs × hours; tiny check first.] |
| **Edit me** | [YAML keys the human may change: `lr`, `k`, `datasets`, `seeds`.] |
| **Out of scope** | [One line.] |

![SYNTHETIC PREVIEW: …](vN.<slug>/figures/<name>.png)
*Preview 1. [What the final plot shows and which comparison decides the question.] Synthetic data, not results.*

======

## Implementation
- **Reuse**: [`path::signature` …]
- **Add / change**: [entity code, `_build.py` registrations, configs]
- **Delete**: [obsolete code and configs]
- **Run**: `run.py` with `EXPERIMENT = "<name>"`, `PROFILE = "tiny"`; command `python .agents/skills/ar_notify/scripts/notify_run.py -- python run.py`
- **Fixture / devices / weights**: [...]
- **W&B**: [group, run names; for training runs: train/val quantities logged during training with `log_every`/`eval_every` and the step axis; summary metrics; final tables]

## Tasks
- [ ] [Task] — Acceptance: [observable result]

## Validation
[Tests and checks to run (exact commands), tiny-profile acceptance, planned figures with backing tables.]

## Notes and risks
[Decisions, risks, debugging checkpoints.]
```

Keep the card at most 20 lines plus 2 previews; it must agree with the appendix. Cite real files and signatures. One coherent iteration per plan.

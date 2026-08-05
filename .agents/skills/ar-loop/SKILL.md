---
name: ar-loop
description: "Run a bounded autonomous Addis research loop from an idea: search literature, reproduce one close paper on a small faithful evaluation, pilot the idea, and iteratively plan, implement, independently review, record, and improve it. Use when the human wants an end-to-end independent researcher for a configured number of cycles."
---

# AR Loop

Read `.agents/references/board.md` and the sibling Addis skills before starting. Initialize the board. This skill orchestrates; sibling skills retain ownership of literature, plans, reviews, development, records, and notes.

## Start Or Resume

1. Read `loop_size` from config and require a positive integer.
2. Preflight routed CLIs and shared project-root access. When routing crosses providers, require project-wide host authorization before starting; if only per-payload approval is available, block now rather than during a later gate.
3. Resolve or allocate one root `I###`. Preserve its problem anchor and non-goals; a materially different root idea starts a new linked idea rather than silently drifting.
4. Run `.agents/tools/ar.py resume . --idea I###`. Resume the first incomplete gate; never rerun accepted work.
5. Before autonomous work, ask once for the human's root-hypothesis prediction, reasoning, and confidence. Store it unchanged in `loop.started`; do not use it to choose methods, metrics, or thresholds.
6. Append `loop.started` with idea ID and configured size unless resuming that loop.

## Foundation: Reproduce First

1. Follow `$ar-lit` for a broad search.
2. Select one reference paper primarily by idea/mechanism similarity, then recency, evaluation relevance, and reproducibility.
3. Preselect one paper evaluation: its own small/synthetic setup when available, otherwise a deterministic excerpt of its most relevant dataset.
4. Select the simplest baseline used by the paper in that evaluation.
5. Follow `$ar-plan` in reproduction mode, `$ar-review` for the plan, `$ar-dev`, result `$ar-review`, then `$ar-record`.

The reproduction must compare the paper's method and simple baseline on the same setup. Aim to approximately recover the paper's result and preserve its method-over-baseline direction. Prefer one close reproduction over weak coverage of several datasets. Repair, obtain a human-approved proxy, or block; never silently skip the foundation.

## Improvement Cycles

For each unfinished cycle from `1..loop_size`:

1. Read accumulated accepted evidence and failed/mixed memory.
2. For cycle 1, test the user's idea with the cheapest decisive synthetic or small real-data pilot. Copy the frozen human prediction into its plan.
3. For later cycles, run targeted `$ar-lit` only when a mechanism, failure, or gap changed. Propose a few distinct directions and choose one by evidence, novelty, information gain, and cost. Record an `Agent Prediction` before results.
4. Reuse the reproduction evaluation, split, metric, and baseline for speed/comparability unless they cannot test the new hypothesis; record any change and why.
5. Follow `$ar-plan`, plan `$ar-review`, `$ar-dev`, result `$ar-review`, and `$ar-record` in order.
6. Append `loop.iteration.completed` with cycle, experiment ID, outcome, and next hypothesis.

One cycle has one primary hypothesis and one new `E###`. Positive, mixed, negative, and inconclusive independently reviewed outcomes count. Execution failure does not count; after bounded repair it blocks the loop. Parameter tuning is valid only when it tests a declared bottleneck.

## Finish

Do not stop because the work seems good enough and do not exceed `loop_size`. Stop early only for a block, exhausted budget, or explicit human request.

After all cycles:

1. Append `loop.completed` with exact member IDs and numeric min/max IDs.
2. Follow `$ar-note` loop-lineage mode to create `__board__/notes/loop_<start_id>_<end_id>.md`.
3. Follow `$ar-record` to summarize the best supported claim, failures, limitations, prediction calibration, and strongest next direction.
4. Update `STATUS.md` and return the lineage note, member reports, final claim status, and blockers.

The loop may execute and measure but may not accept its own plan, code, result, novelty, or claim.

---
name: ar-dev
description: Implement and run an Addis E-numbered plan through a lean reuse-first, YAML-backed, debugger-ready workflow. Use directly for fast development or from ar-loop after plan review.
---

# AR Dev

Execute one plan with minimal context and output. This skill works without `ar-loop`, `ar-lit`, or `ar-record`.

## Start

1. Run `python3 .agents/tools/ar.py init .` and resolve `E###`; if omitted, use the latest planned unfinished run.
2. Resolve `routing.dev` from `__board__/config.yaml`; read the model-routing section of `board.md` only if delegation is needed.
3. Read its `plan.md`, `__board__/structure.md`, and only relevant source/config/tests. Trust source over stale summaries.
4. When invoked by `ar-loop`, require a current accepted plan review. A direct human invocation may run without review; record that fact and never mark its research claim accepted.
5. Set the run state to `running` with its config and debug command.

## Build And Run

1. Reuse existing code and make the smallest plan-scoped change. Avoid new files unless they hold a reusable concept.
2. Keep one argument-free runner: YAML selected by visible constants such as `EXPERIMENT_ID`, `CONFIG_PATH`, `MODEL_IDS`, or `SEEDS`, then `pipeline.run(config)`. Replace runner `argparse` in place.
3. Preflight the config/input/budget, then run `python experiment.py`. Use a small smoke run first only when the full run is costly. Default to one focused repair.
4. In `ar-loop`, run a code/evaluation review only when metric or split meaning changed or the full run is expensive.
5. For reproduction, run the paper method and simplest paper baseline on the same selected small evaluation.
6. Refresh only affected entries in `__board__/structure.md`; remove stale paths and list key signatures, not every symbol.

## Report

Write `__board__/runs/E###/report.md`:

```markdown
Debug: `python experiment.py`
# E### Report
**Outcome**: ...
**Changes/reuse**: ...
**Run**: YAML, selectors, command, runtime
**Verification/results**: ...
**Deviations/limits**: ...
```

For research runs, also record seeds, data/split, raw evidence paths, and exact metrics. A reproduction adds published/reproduced method values, reproduced baseline, and both gaps. Create `artifacts/` only for real outputs and respect `artifact_budget`.

Set state to `done` on execution success or `failed` with the useful diagnostic after the bounded repair. `done` is sufficient for direct development; an accepted research claim still requires `$ar-review E### result`.

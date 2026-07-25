---
name: ar_dev
description: Execute an AutoResearch plan with reuse-first modular code, versioned YAML experiment configs, debugger-ready run files, optional verification, an updated repository structure.md, and a versioned report bundle under __board__/reports/.
---

Execute an AutoResearch plan from `__board__/plans/`.

## Board Bootstrap

Before starting:

1. Treat the current working directory as the project root unless the user gives a different root.
2. Do not create `__board__/` during ordinary session startup. Create it only when this skill is invoked.
3. Ensure only `__board__/` and `__board__/plans/` exist initially, creating them if missing.
4. If `__board__/STATUS.md` is missing, create it from the default template below.
5. Do not create `reports/`, `notes/`, or `refs/` merely for completeness. Create report directories only after selecting an executable plan; read optional directories only if they exist.
6. Save generated research artifacts under `__board__/`; maintain root `structure.md` as project documentation.

```markdown
# Project Status

**Last Updated**: YYYY-MM-DD (initialized)
**Current Phase**: Setup

## Recently Completed

_No completed iterations yet._

## In Progress

_None._

## Next Steps

- [ ] Create the first AutoResearch plan.

## Known Issues

_None yet._

## Notes

_Shared observations for Claude, Codex, and the human._
```

## Plan Selection

- If the user names a plan, resolve it under `__board__/plans/`. Accept `vN.slug`, `vN.slug.md`, or a full path.
- If no plan is named, execute the highest-numbered `vN.*.md` plan.
- If no plan exists, stop and ask the human to run `$ar_plan`.

## Core Development Invariants

- Treat the selected plan, its dependencies, acceptance criteria, and out-of-scope section as the execution contract.
- Follow the plan in order unless source or dependency reality requires a different order; document any deviation.
- Keep changes scoped to the plan and preserve unrelated behavior, user work, and repository conventions.
- When a requirement is ambiguous, make the smallest reasonable decision and document it. Ask the human if the choice would materially expand scope or authority.
- Do not run `git push` without explicit human instruction.

## Verification Policy

The default development path follows the selected plan: implementation, the repository-root debug run, and the tests or checks explicitly included in that plan. Do not add broad verification that is unrelated to the plan.

- Run unit tests when they are part of the selected plan or when the human explicitly requests tests or verification.
- Treat an **extra verification bundle** as opt-in for checks beyond the plan. Keep it small and relevant to the task; do not automatically run every possible config, compile, artifact, or reproducibility check.
- If no tests or checks are included in the plan and none are requested, record `Verification: not required by plan or request` in the report and continue with the primary debug run when the plan includes an experiment.
- Do not install test-only dependencies unless planned tests or an explicit verification request requires them.

## Version Resolution

Resolve `<version>` in this order:

1. Use the version in the plan heading, such as `v3` from `# Plan v3: ...` or `v1.0` from `# Plan v1.0: ...`.
2. Otherwise, use the leading version token in the plan filename.
3. If neither location is unambiguous, ask the human instead of guessing.

Use the exact version for directories, such as `config/v1.0/` and `__board__/reports/v1.0/`. For Python filenames, normalize dots and hyphens to underscores, such as `runs/run_v1_0.py`.

## Modularity and Organization Contract

Before adding code:

1. Read root `structure.md` if it exists and verify relevant entries against source.
2. Inspect existing modules, utilities, tests, configs, and run files for reusable interfaces.
3. Reuse or generalize focused utilities instead of copying experiment logic.
4. When a new function or file would duplicate or fragment existing behavior, perform the smallest safe reorganization that consolidates responsibilities.
5. Keep experiment entrypoints thin and move reusable behavior into cohesive modules.
6. Prefer small explicit functions, clear inputs and outputs, repository-consistent typing, deterministic seeds, and errors that preserve debugging context.
7. Organize by responsibility in folders; avoid root clutter, oversized modules, catch-all utility files, hidden global state, and unrelated refactors.

Do not treat `structure.md` as a substitute for inspecting code. If the plan's architecture conflicts with source reality, choose the most concise safe design and document the decision.

## `structure.md` Contract

Create root `structure.md` during the first development run if it is absent. Refresh it after every run that changes code.

Keep it concise, current, and organized by repository-relative file path. For every maintained source file, include:

- A one-sentence file purpose.
- Every class signature and a one-sentence description.
- Every method signature and a one-sentence description.
- Every function signature and a one-sentence description.
- The debug/run entrypoint and shared callable relationship when applicable.

The repository-root `run.py` is the primary debugger entrypoint. Include its version macro, builder function, and imported versioned `main()` relationship in the map. Version-specific modules remain under `runs/`, but final validation must invoke the root runner.

Use language-native signatures, including parameters and return annotations when present. Include source files, tests, and experiment run files. Exclude dependencies, caches, generated build output, datasets, and `__board__/` artifacts. For files without classes or functions, record the file purpose and relevant entrypoint behavior.

Use this compact shape:

```markdown
# Code Structure

## `path/to/file.py`

Purpose: [One sentence.]

- `class Example(Base)` — [One sentence.]
  - `method(self, value: T) -> R` — [One sentence.]
- `function(config: Config) -> Result` — [One sentence.]
```

Verify documented signatures against the final source and remove stale entries for files or symbols changed by the selected plan.

## Experiment Config and Debug Contract

For every distinct experiment case:

1. Create `config/<version>/<case>.yaml`.
2. Put run parameters in YAML rather than duplicating them in Python. Include seeds and other reproducibility-critical settings.
3. Use portable repository-relative paths; never store secrets or machine-specific absolute paths.
4. Keep a thin version-specific Python entrypoint under `runs/`:
   - One case: `runs/run_<version-id>.py`
   - Multiple cases: `runs/run_<version-id>_<case>.py`
   It must expose a no-argument `main()` callable and may retain an `if __name__ == "__main__"` compatibility block.
5. Define a visible module-level `CONFIG_PATH` constant in the version-specific module pointing to the case YAML.
6. Maintain a repository-root `run.py` as the sole primary debugger entrypoint. It must define a visible macro variable such as `VERSION = "v1"`, set to the latest implemented version, and provide `build_main(version: str) -> Callable[[], object]`. The builder imports the matching `runs.run_<version>` module or matching `runs.run_<version>_*` case module and returns its `main()` callable.
7. Run and debug from the repository root with `python run.py`; do not use a `runs/...` path for the final debug execution.

A root `run.py` should be equivalent to:

```python
from importlib import import_module
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parent
VERSION = "v1"

def build_main(version: str) -> Callable[[], object]:
    module = import_module(f"runs.run_{version}")
    return module.main

if __name__ == "__main__":
    build_main(VERSION)()
```

Keep model, data, training, evaluation, and plotting logic out of both runner layers. Validate that every YAML file loads, contains required fields, and is actually the config used by the versioned `main()`.

## Versioned Result Bundle

Write each completed iteration to:

`__board__/reports/<version>/`

Create only this version's report directory and artifact subdirectories actually needed by the completed iteration.

```text
__board__/reports/<version>/
├── <same-filename-as-plan>.md
├── figures/
│   ├── <descriptive-plot-name>.png
│   └── <descriptive-plot-name>.csv
└── tables/
    └── <descriptive-table-name>.csv
```

- Always place the report inside the version directory, even without experiment artifacts.
- Save every necessary plot as a rendered image and save its underlying values as a same-stem CSV.
- Save every experiment result table as CSV, including tables not discussed in detail.
- Use stable filenames, clear CSV headers, and report-relative artifact links.
- Do not fabricate artifacts. Omit empty artifact directories when appropriate.
- Preserve existing board artifacts and never overwrite another iteration's files.

## Execution Workflow

1. Read `__board__/STATUS.md` and the selected plan fully.
2. Read referenced reports, notes, and refs when those paths exist.
3. Read and verify `structure.md`, or inventory the source directly if this is the first development run.
4. Inspect all source, tests, utilities, configs, and entrypoints relevant to the plan.
5. Resolve the version, config directory, run filenames, and result-bundle path.
6. Implement the smallest reuse-first design; consolidate duplicated or fragmented logic when required.
7. Create one YAML config and thin debug entrypoint per planned experiment case.
8. Prefer `uv` for Python package management when available, but allow `pip install` when necessary. Record installs.
9. Run the tests and checks required by the selected plan, plus any explicitly requested checks. Skip unrelated extra verification. Capture exact commands and output for checks that ran.
10. Run planned experiments through the repository-root debugger entrypoint (`python run.py`) so the tested path matches the documented debugger path.
11. Export figures, plot-data CSVs, and table CSVs into the versioned result bundle.
12. Create or refresh root `structure.md` from the final source.
13. Write `__board__/reports/<version>/<same-filename-as-plan>.md`.
14. Verify the report's first line, config/run mappings, artifact links, CSV headers, any planned or requested verification output, and `structure.md` signatures.
15. Update `__board__/STATUS.md`.

## Report Structure

The absolute first line must name the primary debugger entrypoint and its direct command. The primary entrypoint is always the repository-root `run.py`. Use exactly this form:

```markdown
Debug entrypoint: `run.py` | Command: `python run.py`

# Report: [report name]

**Date**: YYYY-MM-DD
**Author**: Codex (via `$ar_dev`)
**Plan**: `__board__/plans/<plan-file>.md`
**Result Bundle**: `__board__/reports/<version>/`
**Primary Config**: `config/<version>/<case>.yaml`

[Write one concise opening paragraph stating the experiment's core idea, how it was implemented and run, a rudimentary pseudo-example such as `load(CONFIG_PATH) -> run_experiment(config) -> evaluate(result)`, and the headline result.]

## Verification Results

Include this section when tests or checks were required by the selected plan or explicitly requested. If neither applies, write `Verification: not required by plan or request` under Validation, Issues & Caveats instead.

**Command**: `[exact requested verification command(s)]`

**Result**: [exact result and counts when applicable]

```text
[Include actual concise output for the requested checks. Do not replace output with an unsupported pass/fail claim.]
```

## Main Findings

[Move from the overall outcome to detailed evidence. Discuss only the three most important plots or tables when many artifacts exist.]

### [Finding 1]

[Interpret the result and link the relevant figure/table and CSV.]

### [Finding 2]

[Repeat for another major finding.]

### [Finding 3]

[Include only when materially useful.]

## Reproduction and Debugging

| Case | Config | Debug entrypoint | Command |
|------|--------|------------------|---------|
| `[case]` | `../../../config/<version>/<case>.yaml` | `../../../run.py` | `python run.py` |

[State repository-root working directory, environment, seeds, data scope, and key debugger checkpoints. List every case, even when only one is discussed above.]

## Artifact Index

[List all generated figures and CSVs with report-relative links and one-line purposes.]

## Implementation and Structure Notes

[Summarize reused signatures, consolidated code, new interfaces, config/run organization, dependency installs, and the `structure.md` update. Keep routine file lists brief.]

## Validation, Issues & Caveats

[Report the primary debug-run result, planned/requested verification status, limitations, failed runs, technical debt, and unresolved issues with exact commands and numbers.]

## Suggested Next Steps

- [ ] [Concrete next action]
- [ ] [Concrete next action]
```

If the iteration has no experiment, use the most relevant executable validation entrypoint on the first line. Use `N/A` only when no runnable entrypoint exists, and explain why under caveats. Keep the opening paragraph concise and the main findings selective.

## Status Update Rules

Update `__board__/STATUS.md`:

1. Set **Last Updated** to today's date and mention the plan.
2. Update **Current Phase** if appropriate.
3. Add the iteration and versioned result-bundle path to **Recently Completed**; keep only the last 3 items.
4. Update **In Progress**.
5. Replace **Next Steps** with the report's suggested next steps.
6. Update **Known Issues** based on test and experiment results.

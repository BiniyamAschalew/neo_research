---
description: "AutoResearch: plan concise modular experiments with configs and debug entrypoints"
argument-hint: "<task description>"
---

Generate a development plan for: "$ARGUMENTS". Save it under `__board__/plans/` and plan for a compact, human-readable codebase before adding code.

## Board Bootstrap

Before writing:

1. Treat the current working directory as the project root unless the user gives a different root.
2. Do not create `__board__/` during ordinary session startup. Create it only when this command is invoked.
3. Ensure only `__board__/` and `__board__/plans/` exist, creating them if missing.
4. If `__board__/STATUS.md` is missing, create the default status file below.
5. Do not create `reports/`, `notes/`, or `refs/` merely for completeness; read them only if they exist.
6. Never overwrite an existing board file.

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

## Code-Structure Contract

Use root-level `structure.md` as the repository's concise code map.

- Read it fully before planning when it exists, then verify relevant entries against source rather than assuming it is current.
- If it is missing, inspect the code directly and make its creation a required task for the first `/ar_dev` run.
- Whenever a plan changes source code, require `/ar_dev` to refresh `structure.md` after implementation.
- Require `structure.md` to list each maintained source file, its one-sentence purpose, and its classes, methods, and functions in language-native signature form with a one-sentence description.
- Include tests and experiment entrypoints. Exclude dependencies, caches, generated build output, datasets, and `__board__/` artifacts.

## Modularity and Organization Rules

Before proposing a new file, function, or class:

1. Identify existing utilities and interfaces that can be reused.
2. Prefer a small shared implementation plus thin experiment-specific wrappers.
3. If new work would duplicate or fragment existing logic, plan the smallest safe reorganization that consolidates it.
4. Organize files by responsibility in clear folders; avoid root clutter, oversized modules, catch-all utility files, and experiment logic copied between versions.
5. Keep functions small, explicit, typed when the repository uses typing, and easy to unit test and step through.
6. Keep refactoring scoped to what is needed for the planned experiment; do not redesign unrelated code.

Every plan must name the existing signatures to reuse, the new signatures truly required, and any signatures or files to move, consolidate, or retire.

## Experiment Config and Debug Contract

For every distinct experiment case, plan:

- One YAML file at `config/<version>/<case>.yaml`; keep experiment parameters in YAML rather than hard-coding them in Python.
- One thin debug entrypoint under `runs/`. Use `runs/run_<version>.py` for a single case or `runs/run_<version>_<case>.py` for multiple cases. Normalize dots and hyphens in filenames to underscores.
- A module-level `CONFIG_PATH` constant in each run file that already points to its YAML file, followed by a call into shared experiment logic. The file must run in a Python debugger without requiring the user to construct CLI arguments.
- A direct command such as `python runs/run_v35_trial.py`.

Do not put model, dataset, or experiment implementation in the run file. Keep it as a readable debugger entrypoint. Use portable repository-relative paths and never put secrets or machine-specific absolute paths in configs.

## Planning Workflow

1. Read `__board__/STATUS.md`.
2. Scan relevant plans and any existing report bundles, notes, and refs.
3. Determine the next `vN` from `__board__/plans/`.
4. Read and verify `structure.md`, or inspect the repository directly if it does not yet exist.
5. Inspect relevant source, shared utilities, tests, configs, and run files.
6. Design the smallest reusable implementation and identify any required consolidation.
7. Define each YAML config, debug entrypoint, test command, and experiment command.
8. Write `__board__/plans/v{N}.{slug}.md`.

## Plan Template

```markdown
# Plan v{N}: [Plan Title]

**Created**: YYYY-MM-DD
**Author**: Claude (via `/ar_plan`)
**Task**: [Original task description]
**Branch** (suggested): [optional branch name]

## Objective

[State the experiment or implementation outcome in 1-2 sentences.]

## Context

[Summarize current state, relevant prior reports, and whether `structure.md` exists and is current.]

## Existing Structure and Reuse

- **Existing signatures to reuse**: [`module.function(...)`, `Class.method(...)`]
- **Consolidation/reorganization**: [Smallest changes needed to avoid duplication and improve clarity.]
- **New signatures**: [Only interfaces that existing code cannot reasonably provide.]
- **`structure.md` impact**: [Create on first dev run, or list entries that must be refreshed.]

## Experiment and Debug Interfaces

| Case | YAML config | Debug entrypoint | Shared callable | Command |
|------|-------------|------------------|-----------------|---------|
| `[case]` | `config/v{N}/[case].yaml` | `runs/run_v{N}_[case].py` | `module.run_experiment(config)` | `python runs/run_v{N}_[case].py` |

[For a single case, prefer `runs/run_v{N}.py`. State the module-level `CONFIG_PATH` value each entrypoint will contain.]

## Tasks

- [ ] **Reuse-first implementation**: [Concrete shared modules/signatures to reuse, refactor, or add.]
  - Acceptance: [No duplicated experiment logic; focused modules and callable boundaries are verified.]
- [ ] **Configs and debug entrypoints**: [Exact YAML and run files.]
  - Acceptance: [Each run file exposes `CONFIG_PATH` and runs under the debugger with the documented command.]
- [ ] **Tests and experiment execution**: [Exact unit-test and experiment commands.]
  - Acceptance: [Test output and experiment artifacts are captured for the report.]
- [ ] **Refresh repository map**: Create or update root `structure.md`.
  - Acceptance: [Changed source files and every class/method/function signature are accurately documented.]

### Task Dependencies

[State the execution order and dependencies.]

## Test and Debug Validation

- **Unit tests**: `[exact command]`
- **Primary debug command**: `python [run-file]`
- **Config validation**: [How YAML parsing, required fields, and path portability will be checked.]
- **Manual/debug checkpoints**: [Key call boundaries the human can step through.]

## Files Expected to Change

| File | Action | Purpose |
|------|--------|---------|
| `src/...` | Create / Modify / Reorganize | [Shared responsibility and why it belongs here.] |
| `config/v{N}/...yaml` | Create | [Experiment case configuration.] |
| `runs/run_v{N}...py` | Create | [Thin debugger entrypoint.] |
| `tests/...` | Create / Modify | [Unit coverage.] |
| `structure.md` | Create / Update | [Post-implementation signature map.] |

## References

- [Relevant board refs, prior reports, source files, and `structure.md` entries.]

## Notes for Implementation

[Decisions, risks, migration details, and debugging guidance.]

## Notes to Generate

[Standalone notes under `__board__/notes/`, or "None."]

## Out of Scope

[Explicit exclusions.]
```

## Rules

- Cite real files and signatures; do not plan from names alone.
- Prefer reuse and consolidation over additive duplication.
- Give every task observable acceptance criteria.
- Require unit-test output in the final report, not only a pass/fail claim.
- Require the final report's first line to name the primary debug entrypoint and command.
- Keep each plan to one coherent iteration.
- Do not implement code while using this command.
- Keep generated planning output under `__board__/plans/`.

## After Writing

1. Print the plan path.
2. Summarize its reuse strategy, config/run layout, and validation commands.
3. Tell the human they can run Claude `/ar_dev v{N}.{slug}` or Codex `$ar_dev v{N}.{slug}`.

---
name: ar_plan
description: Create an AutoResearch shared-board implementation or experiment plan that prioritizes concise modular code, reuse of existing utilities, versioned full/tiny YAML configs, tracked real-data fixtures, debugger-ready run files, scoped verification, and an up-to-date repository structure.md.
---

Create an AutoResearch development plan under `__board__/plans/`. Plan for a compact, human-readable codebase before planning new code.

## Shared Installation and Project Context

Use the active project as the working root, even when this skill resolves through a link into another repository. Read its applicable AGENTS.md or Claude instructions, status and relevant artifact policy. Project instructions, explicit user amendments and established experiment contracts take precedence over the defaults below. Never move generated research state into the shared skill repository merely because the skill is installed there.

Codex invokes `$ar_plan`/`$ar_dev`/`$ar_metaplan`; Claude uses `/ar_plan`/`/ar_dev`/`/ar_metaplan`. Record the actual assistant as author. Resolve this skill's supporting references and scripts relative to its installation, following links; resolve research/code/config paths against the active project.

Use targeted reads of the affected source and board references. Inspect actual implementations rather than relying on the code map. Preserve historical reports and frozen acquisition protocols; apply new execution conventions to new work or explicitly requested migrations.

## Board Bootstrap

Before writing:

1. Treat the current working directory as the project root unless the user gives a different root.
2. Do not create `__board__/` during ordinary session startup. Create it only when this skill is invoked.
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

- Read its relevant entries before planning and verify them against source rather than assuming the map is current.
- If it is missing, inspect the code directly and make its creation a required task for the first `$ar_dev` run.
- Whenever a plan changes source code, require an incremental `structure.md` refresh for changed/new/retired files and affected signatures after implementation. Do not regenerate unrelated entries by default.
- Require `structure.md` to list each maintained source file, its one-sentence purpose, and its classes, methods, and functions in language-native signature form with a one-sentence description.
- Include tests, the root `run.py` debugger entrypoint, and version-specific experiment modules. Exclude dependencies, caches, generated build output, datasets, and `__board__/` artifacts.

## Modularity and Organization Rules

Before proposing a new file, function, or class:

1. Identify existing utilities and interfaces that can be reused.
2. Prefer a small shared implementation plus thin experiment-specific wrappers.
3. If new work would duplicate or fragment existing logic, plan the smallest safe reorganization that consolidates it.
4. Organize files by responsibility in clear folders; avoid root clutter, oversized modules, catch-all utility files, and experiment logic copied between versions.
5. Keep functions small, explicit, typed when the repository uses typing, and easy to unit test and step through.
6. Keep refactoring scoped to what is needed for the planned experiment; do not redesign unrelated code.

Every plan must name the existing signatures to reuse, the new signatures truly required, and any signatures or files to move, consolidate, or retire.

## Shared Execution Conventions

For executable work, read [structured execution conventions](../references/structured-execution.md). Plan semantic utility reuse and bounded restructuring, full/tiny profiles through one production pipeline, eligible tracked real-data excerpts, and explicit CUDA/MPS/CPU and checkpoint prerequisites. Apply these alongside the repository-specific contracts below; preserve archived experiments and their settings.

## Verification Policy

Plans should preserve the original lightweight validation structure: include unit tests when they are justified by the implementation risk or acceptance criteria, and have `$ar_dev` run those planned tests. Do not add broad extra verification by default. Extra checks beyond the plan are opt-in when the human explicitly requests them. The primary root debug run remains the normal experiment validation path. For new executable work, include the applicable tiny-profile acceptance checks from the shared conventions in the plan; these are scoped acceptance gates, not a broad additional test suite. State which actual hardware is available and which backends will remain unverified.

## Experiment Config and Debug Contract

These are defaults for new Python experiments. Preserve a project's established root runner or report layout when its instructions or selected plan specify one. Adapt the same config-selected, debugger-ready design to the project's language. Code-only work needs no invented experiment scaffold.


For every distinct experiment case, plan:

- A shared scientific configuration with `config/<version>/<case>/full.yaml` and `tiny.yaml`; keep experiment parameters in YAML rather than hard-coding them in Python. Define resolved profile differences and preserve full scientific settings. Tiny uses the same production pipeline and actual architecture/weights, with smaller eligible inputs and bounded work.
- One thin version-specific implementation entrypoint under `runs/`. Use `runs/run_<version>.py` for a single case or `runs/run_<version>_<case>.py` for multiple cases. Normalize dots and hyphens in filenames to underscores. Each module must expose a no-argument `main()` callable and a module-level `CONFIG_PATH`.
- A root-level `run.py` debugger entrypoint with a visible macro such as `VERSION = "v1"`, set to the latest version, and a builder utility `build_main(version: str)` that imports the corresponding `runs.run_<version>` or `runs.run_<version>_*` module and returns its `main()` callable.
- A visible `CONFIG_PATH` in the version-specific module, defaulting to its tiny profile. Select full explicitly through that variable; do not create a separate runner or algorithm for each profile. No argparse flags are needed for normal debugging.
- A direct root command: `python run.py`. The final debug run must be executed from the repository root, never via a `runs/...` path.

Do not put model, dataset, or experiment implementation in either runner file. Keep `run.py` as the version selector/import builder and the version-specific module as a readable config-driven entrypoint. Use portable repository-relative paths and never put secrets or machine-specific absolute paths in configs.

## Planning Workflow

1. Read `__board__/STATUS.md`.
2. Scan relevant plans and any existing report bundles, notes, and refs.
3. Determine the next `vN` from `__board__/plans/`.
4. Read and verify the relevant `structure.md` entries, or inspect affected source directly if it does not yet exist.
5. Inspect relevant source, shared utilities, tests, configs, and run files.
6. Design the smallest reusable implementation and identify any required consolidation.
7. Define each full/tiny YAML pair, shared defaults, fixture manifest, device/weight prerequisites, debug entrypoint, scoped acceptance checks, and experiment command. Reuse existing fixtures with the same input contract.
8. Specify result paths using the project artifact policy when present; otherwise read the [publication defaults](../references/artifact-policy.md). Default new report bundles to `__board__/reports/<plan-basename>/<plan-basename>.md`; preserve an established `<version>/` directory convention.
9. Write `__board__/plans/v{N}.{slug}.md`.

## Two-Part Plan Structure

After the title and metadata, write each plan in two parts:

1. **At a Glance:** Aim for two short paragraphs in plain language for a human reading in a rush. Explain the question, why it matters, the proposed approach and comparison, and what the experiment will let us decide. Keep the important scope, success conditions and limitations visible. Put supporting setup facts in a compact table or simple diagram when that makes them easier to scan; leave exhaustive settings, file lists and implementation steps to the detailed part.
2. Put the exact separator `======` on its own line, with blank lines around it. Then retain the complete detailed plan structure below, starting with Objective. The overview supplements the detailed plan; it does not replace tasks, acceptance criteria, references or implementation guidance. Both parts must agree.

## Plan Template

```markdown
# Plan v{N}: [Plan Title]

**Created**: YYYY-MM-DD
**Author**: [Actual assistant and invocation]
**Task**: [Original task description]
**Branch** (suggested): [optional branch name]

## At a Glance

[Short paragraph: the question, motivation and intended outcome, understandable without reading the detailed plan.]

[Short paragraph: the main approach and comparison, what will determine success, and the most important limitation or boundary.]

[When useful, add a compact table like the one below or a simple diagram. Adapt or omit rows to keep only the relevant details.]

| Detail | Planned setup |
|---|---|
| Scope | [Data, models and main comparison] |
| Success check | [Primary metric and acceptance criterion] |
| Cost / limits | [Relevant resource budget and key scope boundary] |

======

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
| `[case]` | `config/v{N}/[case]/{tiny,full}.yaml` | `run.py` → `runs/run_v{N}_[case].py::main` | `module.run_experiment(config)` | `python run.py` |

[For a single case, use `run.py` as the debugger entrypoint and state the `VERSION` macro plus the version-specific module's `CONFIG_PATH`. List shared defaults, full/tiny differences, actual-data fixture/manifest, output isolation, supported hardware, external weights and clean-checkout prerequisites.]

## Tasks

- [ ] **Reuse-first implementation**: [Concrete shared modules/signatures to reuse, refactor, or add.]
  - Acceptance: [No duplicated experiment logic; focused modules and callable boundaries are verified.]
- [ ] **Configs, fixtures and debug entrypoints**: [Exact full/tiny YAML paths, shared defaults, real-data fixture/manifest, root `run.py`, and version-specific run files.]
  - Acceptance: [The version-specific module exposes `CONFIG_PATH` and `main()`; root `run.py` exposes the latest `VERSION`, builds the matching main function, and runs from the repository root with `python run.py`.]
- [ ] **Validation and experiment execution**: [Exact planned test/check commands and experiment command; mark any additional checks as optional.]
  - Acceptance: [Tests and checks included in the plan are run; unrelated extra verification is skipped unless explicitly requested; outputs and experiment artifacts are captured for the report.]
- [ ] **Refresh repository map**: Create or update root `structure.md`.
  - Acceptance: [Changed source files and every class/method/function signature are accurately documented.]

### Task Dependencies

[State the execution order and dependencies.]

## Test and Debug Validation

- **Unit tests/checks**: `[exact command when included in the plan]`
- **Primary debug command**: `python run.py`
- **Config validation**: [YAML parsing, required fields, portable paths, resolved full/tiny differences and frozen full settings.]
- **Portable tiny acceptance**: [Actual finite forward outputs and, where trainable, optimizer updates through production code with full data unavailable; fixture provenance/hashes/size; separate outputs; explicit device behavior and available-hardware status.]
- **External prerequisites**: [Weight source/version/hash/cache, minimal dependencies and unsupported backend combinations. A runtime-only checkout must not depend on ignored helpers.]
- **Manual/debug checkpoints**: [Key call boundaries the human can step through.]

## Files Expected to Change

| File | Action | Purpose |
|------|--------|---------|
| `src/...` | Create / Modify / Reorganize | [Shared responsibility and why it belongs here.] |
| `config/v{N}/[case]/{full,tiny}.yaml` | Create | [Shared scientific configuration and bounded debug profile.] |
| `tests/fixtures/[contract]/...` | Create / Reuse | [Eligible actual-data excerpt plus provenance/hash manifest.] |
| `run.py` | Create / Update | [Root debugger version selector and main-function builder.] |
| `runs/run_v{N}...py` | Create / Modify | [Thin version-specific config-driven main function.] |
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
- Include output for tests/checks included in the plan or explicitly requested. If neither applies, record that verification was not required by the plan or request.
- Require the final report's first line to name the primary debug entrypoint and command.
- Keep each plan to one coherent iteration.
- Do not implement code while using this skill.
- Keep generated planning output under `__board__/plans/`.

End with the plan path and next invocation. If the user already authorized downstream execution, continue under ar_dev without requesting the same approval again.

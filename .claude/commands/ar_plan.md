---
description: AutoResearch: generate the next shared-board development plan
argument-hint: <task description>
---

Generate a development plan for the task: "$ARGUMENTS"

## Board Bootstrap

Before writing the plan:

1. Treat the current working directory as the project root unless the user gives a different root.
2. Ensure these directories exist, creating only missing directories:
   - `__board__/plans/`
   - `__board__/reports/`
   - `__board__/notes/`
   - `__board__/refs/`
3. If `__board__/STATUS.md` is missing, create it using the template below.
4. Never overwrite existing board files unless this command explicitly created them in the same run.

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

## Before Writing the Plan

1. Read `__board__/STATUS.md`.
2. Scan `__board__/reports/` if reports exist.
3. Scan `__board__/plans/` to determine the next version number:
   - Find the highest `vN` plan filename and use `v{N+1}`.
   - If no plans exist, start with `v1`.
4. Read relevant files in the project source tree and tests before planning changes to them.
5. Read relevant materials in `__board__/refs/` if present.

## Plan Output

Write the plan to `__board__/plans/v{N}.{slug}.md`.

Use this structure:

```markdown
# Plan v{N}: [Plan Title]

**Created**: YYYY-MM-DD
**Author**: Claude (via `/ar_plan`)
**Task**: [Original task description]
**Branch** (suggested): [optional branch name]

## Objective

[1-2 sentences describing what this iteration achieves and why.]

## Context

[Current project state relevant to this task. Mention related board files.]

## Tasks

- [ ] **Task 1 title**: Concrete implementation work and target files.
  - Acceptance: [How to verify completion]
- [ ] **Task 2 title**: Concrete implementation work and target files.
  - Acceptance: [How to verify completion]

### Task Dependencies

[Execution order or dependency graph.]

## Files Expected to Change

| File | Action | Notes |
|------|--------|-------|
| `src/...` | Create / Modify | [what and why] |
| `tests/...` | Create / Modify | [what and why] |

## References

- [Relevant `__board__/refs/`, prior plans, prior reports, or external references]

## Notes for Implementation

[Design guidance, risks, trade-offs, and edge cases.]

## Notes to Generate

[If a standalone note should be written under `__board__/notes/`, specify it. Otherwise write "None."]

## Out of Scope

[Explicit exclusions.]
```

## Rules

- Be specific: reference real file paths, functions, classes, and tests.
- Keep each plan to one coherent iteration.
- Every task must have acceptance criteria.
- Do not implement code in this command.
- Do not modify project files outside `__board__/plans/` and the board bootstrap files/directories.

## After Writing

1. Print the plan path.
2. Summarize the plan in 2-3 lines.
3. Tell the human they can run Claude `/ar_dev v{N}.{slug}` or Codex `$ar_dev v{N}.{slug}`.

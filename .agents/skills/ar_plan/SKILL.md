---
name: ar_plan
description: AutoResearch workflow for Codex to create a shared-board development plan under __board__/plans. Use when the user asks to plan an implementation, next research iteration, experiment, or agent handoff.
---

Create an AutoResearch development plan and save it under the shared `__board__/plans/` directory.

## Board Bootstrap

Before writing anything:

1. Treat the current working directory as the project root unless the user gives a different root.
2. Ensure these directories exist, creating only missing directories: `__board__/plans/`, `__board__/reports/`, `__board__/notes/`, and `__board__/refs/`.
3. If `__board__/STATUS.md` is missing, create the default status file shown below.
4. Never overwrite existing board files unless you created them during this turn.

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

## Planning Workflow

1. Read `__board__/STATUS.md`.
2. Scan `__board__/reports/`, `__board__/plans/`, and relevant `__board__/refs/`.
3. Inspect relevant source and test files before planning changes to them.
4. Determine the next `vN` from existing files in `__board__/plans/`.
5. Write the plan to `__board__/plans/v{N}.{slug}.md`.

## Plan Template

```markdown
# Plan v{N}: [Plan Title]

**Created**: YYYY-MM-DD
**Author**: Codex (via `$ar_plan`)
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

- Be concrete and cite real files, symbols, tests, and board context.
- Keep each plan to one coherent iteration.
- Every task needs acceptance criteria.
- Do not implement code while using this skill.
- All generated planning output must stay under `__board__/plans/`.

End by giving the plan path and telling the human they can run Codex `$ar_dev v{N}.{slug}` or Claude `/ar_dev v{N}.{slug}`.

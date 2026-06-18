---
name: ar_dev
description: AutoResearch workflow for Codex to execute a shared-board plan, update __board__/STATUS.md, and write an implementation report under __board__/reports.
---

Execute an AutoResearch plan from `__board__/plans/`.

## Board Bootstrap

Before starting:

1. Treat the current working directory as the project root unless the user gives a different root.
2. Ensure `__board__/plans/`, `__board__/reports/`, `__board__/notes/`, and `__board__/refs/` exist.
3. Ensure `__board__/STATUS.md` exists. If missing, create the default status file from `$ar_plan`.
4. All implementation reports must be saved under `__board__/reports/`.

## Plan Selection

- If the user names a plan, resolve it under `__board__/plans/`. Accept `vN.slug`, `vN.slug.md`, or a full path.
- If no plan is named, execute the highest-numbered `vN.*.md` plan.
- If no plan exists, stop and ask the human to run `$ar_plan`.

## Execution Workflow

1. Read `__board__/STATUS.md`.
2. Read the selected plan fully.
3. Read referenced board reports, notes, and refs.
4. Inspect source and tests mentioned by the plan before editing.
5. Implement the plan, keeping changes scoped.
6. Prefer `uv` for Python package management when available, but `pip install` is allowed when necessary. Document dependency installs in the report.
7. Run relevant tests or checks. If they cannot run, explain why in the report.
8. Write the implementation report to `__board__/reports/<same-filename-as-plan>.md`.
9. Update `__board__/STATUS.md`.

## Report Template

```markdown
# Report: [report name]

**Date**: YYYY-MM-DD
**Author**: Codex (via `$ar_dev`)
**Plan**: `__board__/plans/<plan-file>.md`

## Summary

[2-3 sentences: goal, result, and current state.]

## Changes Made

- [Files changed, configs changed, dependencies installed]

## Key Decisions

- [Unspecified decisions and rationale]

## Results

[Tests, metrics, benchmarks, experiments. Include exact commands and numbers. If no experiments were run, write "N/A -- no experiments in this iteration."]

## Current Code Structure

[Brief description of relevant architecture after the changes.]

## Issues & Observations

- [Bugs, technical debt, caveats, unexpected behavior]

## Suggested Next Steps

- [ ] [Concrete next action]
- [ ] [Concrete next action]
```

## Status Update Rules

Update `__board__/STATUS.md`:

1. Set **Last Updated** to today's date and mention the plan.
2. Update **Current Phase** if appropriate.
3. Add this iteration to **Recently Completed** and keep only the last 3 items.
4. Update **In Progress**.
5. Replace **Next Steps** with the report's suggested next steps.
6. Update **Known Issues** based on findings.

Do not run `git push` without explicit human instruction.

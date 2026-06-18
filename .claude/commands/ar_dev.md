---
description: AutoResearch: execute a shared-board development plan
argument-hint: [plan version or filename, e.g. v3.model-update]
---

Execute the requested AutoResearch plan. If no argument is supplied, execute the latest plan in `__board__/plans/`.

## Board Bootstrap

Before starting:

1. Treat the current working directory as the project root unless the user gives a different root.
2. Ensure `__board__/plans/`, `__board__/reports/`, `__board__/notes/`, and `__board__/refs/` exist.
3. Ensure `__board__/STATUS.md` exists. If missing, create the default status file from `/ar_plan`.
4. Never write generated state outside `__board__/`.

## Plan Selection

- If `$ARGUMENTS` names a plan, resolve it under `__board__/plans/`. Accept either `vN.slug`, `vN.slug.md`, or a full path.
- If no argument is provided, choose the highest-numbered `vN.*.md` plan in `__board__/plans/`.
- If there is no plan, stop and ask the human to run `/ar_plan`.

## Before Implementation

1. Read `__board__/STATUS.md`.
2. Read the selected plan thoroughly.
3. Read prior reports or notes referenced by the plan.
4. Read any relevant references under `__board__/refs/`.
5. Inspect the source and test files named by the plan before editing.

## During Implementation

- Follow the plan in order unless dependency or code reality requires a different order.
- If requirements are ambiguous, make a reasonable decision, proceed, and document the decision in the report.
- Keep edits scoped to the selected plan.
- Use the existing project environment when possible.
- Prefer `uv` for Python package management when available, but `pip install` is allowed when necessary. Document any installs in the report.
- Run relevant tests after modifying code. If tests cannot be run, explain why in the report.
- Do not run `git push` without explicit human instruction.

## Report Output

After completion, write a report to:

`__board__/reports/<same-filename-as-plan>.md`

Use this structure:

```markdown
# Report: [report name]

**Date**: YYYY-MM-DD
**Author**: Claude (via `/ar_dev`)
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

## Status Update

Update `__board__/STATUS.md`:

1. Set **Last Updated** to today's date and mention the plan.
2. Update **Current Phase** if appropriate.
3. Add this iteration to **Recently Completed** and keep only the last 3 items.
4. Update **In Progress**.
5. Replace **Next Steps** with the report's suggested next steps.
6. Update **Known Issues** based on findings.

## Final Response

Tell the human which plan was executed, where the report was written, which tests or checks ran, and any important unresolved issue.

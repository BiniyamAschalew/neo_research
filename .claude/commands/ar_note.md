---
description: "AutoResearch: write a shared-board technical note"
argument-hint: "<topic>"
---

Generate a technical note about: "$ARGUMENTS"

## Board Bootstrap

Before writing:

1. Treat the current working directory as the project root unless the user gives a different root.
2. Do not create `__board__/` during ordinary session startup. Create it only when this command is invoked.
3. Ensure only `__board__/` and `__board__/notes/` exist, creating them if missing.
4. If `__board__/STATUS.md` is missing, create it from the default template below.
5. Do not create `plans/`, `reports/`, or `refs/` merely for completeness; read them only if they exist.
6. Keep all notes under `__board__/notes/`.

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

## Before Writing

1. Read `__board__/STATUS.md`.
2. Scan `__board__/notes/` to determine the next note number:
   - Find the highest `NN.*.md` and use `NN+1`.
   - If no notes exist, start with `01`.
3. Read relevant reports, plans, notes, and refs from `__board__/` when those paths exist.
4. Inspect relevant source/config files if the note makes claims about code.

## Note Output

Write the note to `__board__/notes/{NN}.{slug}.md`.

Use this structure:

```markdown
# [Note Title]

**Date**: YYYY-MM-DD
**Author**: Claude (via `/ar_note`)
**Related Board Files**: [plans, reports, notes, refs, or "None"]

## TL;DR

[2-4 sentences with the core takeaway.]

## Background

[Why this topic matters and what prompted the note.]

## Methodology

[How the finding was produced. For conceptual notes, replace with "## Scope".]

## Findings

[Concrete findings. Use tables for quantitative comparisons.]

## Discussion

[Interpretation, limitations, caveats.]

## Takeaways

- [Actionable conclusion]
- [Actionable conclusion]
```

## Rules

- Ground claims in board files, code, or explicit external references.
- Include exact numbers and conditions for metrics.
- Label speculation as speculation.
- Keep one note focused on one topic.

## After Writing

1. Print the note path.
2. Summarize the takeaway in 2-3 lines.
3. If implementation should follow, suggest creating a plan with `/ar_plan`.

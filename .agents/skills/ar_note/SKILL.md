---
name: ar_note
description: AutoResearch workflow for Codex to write source-backed technical notes under __board__/notes using plans, reports, refs, and code context.
---

Write an AutoResearch technical note under `__board__/notes/`.

## Board Bootstrap

Before writing:

1. Treat the current working directory as the project root unless the user gives a different root.
2. Ensure `__board__/notes/`, `__board__/reports/`, `__board__/plans/`, and `__board__/refs/` exist.
3. Ensure `__board__/STATUS.md` exists. If missing, create the default status file from `$ar_plan`.
4. All notes must stay under `__board__/notes/`.

## Note Workflow

1. Read `__board__/STATUS.md`.
2. Determine the next note number from `__board__/notes/`:
   - Use `NN+1` from the highest `NN.*.md`.
   - Start with `01` if no notes exist.
3. Read relevant board plans, reports, notes, and refs.
4. Inspect source/config files if making code-specific claims.
5. Write the note to `__board__/notes/{NN}.{slug}.md`.

## Note Template

```markdown
# [Note Title]

**Date**: YYYY-MM-DD
**Author**: Codex (via `$ar_note`)
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

- Ground claims in board files, code, or explicit references.
- Include exact numbers and conditions for metrics.
- Label speculation as speculation.
- Keep one note focused on one topic.
- Do not write note output outside `__board__/notes/`.

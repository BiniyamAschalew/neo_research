---
name: ar_note
description: Write one focused, source-backed technical note under __board__/notes/ (a finding, comparison, debugging insight or design decision) grounded in board files, code and cited references.
---

# AR Note

Read [board conventions](../references/board.md) and `__board__/STATUS.md`, then the plans, reports, notes and code the topic touches. Next number = one above the highest `NN.*.md` in `__board__/notes/` (start at `01`). Write `__board__/notes/NN.<slug>.md`:

```markdown
# [Title]

**Date**: YYYY-MM-DD | **Author**: [agent] | **Related**: [board files or "None"]

## TL;DR
[2-4 sentences: the takeaway, with the key number.]

======

## Background
## Method (or Scope for conceptual notes)
## Findings
[Exact numbers and conditions; tables for comparisons.]
## Discussion
[Interpretation, limits; label speculation as speculation.]
## Takeaways
- [Actionable conclusion]
```

One topic per note. Reply with the path and the takeaway in 2-3 lines; suggest `ar_plan` if implementation should follow.

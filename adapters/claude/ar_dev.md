---
description: "AutoResearch: dev using the shared workflow"
argument-hint: "[plan version or filename]"
---

Use the active project's `.agents/skills/ar_dev/SKILL.md` as the authoritative workflow for this request. Read that file, following its link, and any supporting references required by the task before proceeding.

Arguments: $ARGUMENTS

Keep the active project as the working root; the shared skill's installation directory is not the research destination. Apply the arguments as the user's task or plan selection. Use Claude's `/ar_plan`, `/ar_dev`, and `/ar_metaplan` invocation names and record Claude as author. Follow the shared instructions and the active project's applicable Claude instructions; do not create a separate copy of the workflow here.

---
name: ar_idea
description: Create or refine an ID-bearing research idea grounded in literature and theory, maintain detailed paper summaries, and synthesize experiment takeaways before planning further experiments.
---

# AR Idea

Use one living idea across experiments. Work in the active project; `ar_metaplan` is a compatibility entrypoint.

1. Read project instructions, the relevant idea and related closed-idea summaries. Reuse its ID for the same question; a materially different claim gets a new linked idea.
2. Create with `python .agents/skills/ar_idea/scripts/idea.py <slug> --question "..."`. IDs `I001`, `I002`, ... are project-wide, locked and never reused. A worktree's `__board__/IDEA.md` points to its canonical document.
3. Find the closest work by mechanism and assumptions. Check existing project papers first. Verify scientific claims against primary papers, citing page/section/equation/table. Store accessible PDFs under `papers/`, reusing existing copies when practical while keeping published references portable. Record inaccessible evidence explicitly.
4. Maintain one `papers/summary.md` with a detailed section per paper: citation/link/PDF path, question/contribution, method, assumptions/theoretical results, evaluation/data/splits/baselines/metrics, decisive numbers, limitations, relevance and simplest meaningful result to reproduce. Distinguish the paper's findings from our interpretation. Update sections rather than duplicating them.
5. Refine the hypothesis with definitions, assumptions, derivations, counterexamples and failure cases. Distinguish proof, approximation and conjecture. Empirical claims need a coherent falsifier, not a fabricated theorem. If prior work answers the question, reuse its evidence or justify a small faithful reproduction before a novel experiment.
6. Set disposition: `ready`, `needs refinement`, `reproduce first`, or `stop`. Name the smallest unresolved question worth testing. Create plans/run experiments only when the user also requested that work.

Existing projects need no bulk rewrite: create/link an idea when its next plan or report is touched. Keep legacy `ideas/<slug>.md` close summaries as references. Each idea agent writes only its own document; another agent should return proposed changes rather than overwrite it.

## Living Document

Keep `__board__/ideas/I###-<slug>/idea.md` about one page:

- **ID / question / status**, core hypothesis.
- **Rationale**: essential theoretical argument, assumptions and falsifier; link long derivations to notes.
- **Literature**: links to detailed paper-summary sections and the precise remaining gap.
- **Reference evaluation**: closest method, simplest baseline, small evaluation and published target.
- **Evidence**: one row per linked plan/report: hypothesis, decisive result, `supports | contradicts | mixed | inconclusive` with a brief reason.
- **Current position**: 2–4 sentences on what is known and the next unresolved question.

Preserve the original hypothesis; record revisions with reasons. Empirical agreement is bounded support, not proof. Updating a report replaces its evidence row. Details stay in linked papers, notes and reports.

Return ID, path, disposition and next action. Only ready/reproduction dispositions hand off to `ar_plan`; refinement permits only its named prerequisite check.

---
name: ar_metaplan
description: Refine a research idea into an evidence-backed prompt for ar_plan. Use when the user wants a plan for a plan, an experiment feasibility or novelty check, theoretical refinement, or a more decisive experiment design before implementation planning. Audit existing experiments, analyze the mathematics, and justify baselines, replication, uncertainty, and decision criteria. Produces a shared-board metaplan, not an execution plan.
---

# AutoResearch Metaplanning

Turn an idea into a scientifically defensible input to `$ar_plan`. The deliverable is a research-design brief with a self-contained, copyable planning prompt. Preserve the user's underlying question while challenging the proposed mechanism and experiment. A useful outcome may be reuse of existing evidence, a narrower question, a feasibility study, or a recommendation not to run.

Invocation: `$ar_metaplan <idea, question, or existing draft path>`.

## Shared Installation and Project Context

Use the active project as the working root, even when this skill resolves through a link into another repository. Read its applicable AGENTS.md or Claude instructions, status and relevant artifact policy. Project instructions, explicit user amendments and established experiment contracts take precedence over the defaults below. Never move generated research state into the shared skill repository merely because the skill is installed there.

Codex invokes `$ar_plan`/`$ar_dev`/`$ar_metaplan`; Claude uses `/ar_plan`/`/ar_dev`/`/ar_metaplan`. Record the actual assistant as author. Resolve this skill's supporting references and scripts relative to its installation, following links; resolve research/code/config paths against the active project.

Use targeted reads of the affected source and board references. Inspect actual implementations rather than relying on the code map. Preserve historical reports and frozen acquisition protocols; apply new execution conventions to new work or explicitly requested migrations.

## Scope and project context

- Use the current directory as the project root unless the user specifies another. Read applicable project instructions and `__board__/STATUS.md` if present.
- Read the project's `.agents/skills/ar_plan/SKILL.md` to understand its handoff contract, including the project's entrypoint, report-layout and code-map conventions. If unavailable, report that limitation and still produce a portable planning prompt.
- Inspect relevant plans, reports, notes, references, source, configurations, and tests. Follow links to actual result artifacts when needed to substantiate a finding. Keep searches targeted to the idea and its synonymous mechanisms. Always read the closed-idea summaries `__board__/ideas/*.md` in the main checkout (written by `ar_tree`); a summary marked failed is prior evidence, and its "Don't retry unless" condition must hold before recommending the same approach.
- This skill designs research. Do not implement code, launch experiments, or invoke `ar_plan` automatically. If the user also requests downstream planning or execution, complete this deliverable and then continue under the appropriate skill.
- Save generated research state under `__board__/`. Skill definitions belong in `.agents/skills/`; metaplans do not.

## 1. Recover the question and audit prior work

Separate the scientific question from the proposed implementation. State the intended claim, intervention, comparison, outcome, target population or regime, and constraints. Identify whether the goal is mechanism identification, predictive performance, robustness, replication, or another concrete research purpose.

Search for conceptual overlap, not just matching names. Distinguish work that is proposed, implemented, run, analyzed, or actually supports the claim. A configuration or code path alone does not establish experimental evidence; a missing search hit does not establish novelty.

Record a compact evidence map:

| Related experiment or artifact | Status and evidence location | What it establishes | Remaining gap or reusable component |
|---|---|---|---|

Check whether the idea is already integrated as a baseline, ablation, special case, configuration option, or follow-up. Compare protocols and assumptions before treating results as equivalent. State the scope and limits of the search. Choose whether to reuse, extend, deliberately replicate, or propose a new comparison, and explain the information it adds. Replication can be valuable without claiming novelty.

## 2. Test and refine the theoretical rationale

Define the mathematical objects, estimand, objective, and assumptions at the level needed to assess the claim. Show the key derivation or logical argument; do not substitute labels such as “theoretically motivated” for reasoning.

- Separate exact identities, proved implications, approximations, and conjectures. Check dimensions, conditioning, information available at prediction time, and relevant limiting or degenerate cases.
- Ask whether the claimed improvement follows trivially from the construction, changes the objective being measured, uses unavailable information, or is equivalent to a known method. If so, identify the remaining nontrivial empirical question, if any.
- Identify plausible alternative explanations and conditions under which the proposed mechanism should fail. Use counterexamples, toy cases, or a synthetic setting when they discriminate between explanations.
- Translate the rationale into falsifiable predictions: expected direction or pattern, the conditions required, and an observation that would contradict it. Distinguish performance gains from evidence for a mechanism.
- Use relevant local references and verify external theoretical claims against primary sources when needed. Cite precise sources and assumptions; label original derivations and unverified claims. If evidence is inaccessible, narrow the claim or identify a feasibility gate rather than inventing support.

Refine the idea based on this analysis. Do not manufacture a theorem for a purely empirical question. If the theory already resolves the question, explain whether any experiment would validate a meaningful implementation or assumption; otherwise recommend against a redundant run.

## 3. Design an experiment that can distinguish outcomes

Build the smallest design capable of resolving the refined question, then justify any expansion. Add missing controls or baselines when necessary, explaining which alternative explanation each addresses. Separate essential comparisons from optional extensions so the proposal does not become an unfocused sweep.

Address the following where relevant, explicitly marking material unresolved choices:

- **Comparisons:** Include the current reference method, a simple credible baseline, and targeted ablations or negative controls. Include an oracle only as a labeled diagnostic with its information advantage made explicit. Match data, splits, preprocessing, tuning access, and compute, or report the mismatch as a trade-off.
- **Information boundaries:** Specify training, validation, and test roles; what labels or outcomes selection can access; and where preprocessing is fitted. Prevent test-driven selection and tuning. Previously inspected results motivate exploration, not retrospective confirmation.
- **Replication:** Identify sources of variation separately: model or optimizer seeds, data generation, cohort sampling, dataset choice, and split assignment. Pair methods on common units when appropriate. State which units are independent and the population to which inference applies. More model seeds do not substitute for independently sampled data; repeated folds or rows within a dataset are not automatically independent replicates.
- **Precision and budget:** Justify replication counts using a meaningful effect size, target interval width, power analysis, prior variance, or a bounded pilot. If inputs are unknown, prescribe a pilot and a rule for selecting the final design within a compute cap. Do not invent a universal seed count or promise conclusiveness. Respect project seed conventions while explaining what their replication does and does not cover.
- **Analysis:** Define the primary metric and contrast, aggregation and weighting, uncertainty method and resampling unit, and treatment of dependent observations. Designate secondary or exploratory comparisons and account for multiplicity when making several confirmatory claims. Report effect sizes and uncertainty, not only significance or rankings.
- **Interpretation:** Specify what would support, refute, or leave the claim unresolved. A nonsignificant result alone is not evidence of equivalence. If absence of a meaningful effect matters, define a justified equivalence or practical-effect threshold and require adequate precision. Include heterogeneous effects and mechanism-failure outcomes when relevant.
- **Feasibility and durability:** For executable work, read [structured execution conventions](../references/structured-execution.md). Identify a minimal real-data excerpt and full/tiny production-path feasibility check, eligible redistribution, role/information boundaries, external weight prerequisites and actual CUDA/MPS/CPU support. A tiny debug success is not scientific support for the hypothesis. Defer detailed module/config choices to ar_plan. Identify required data, checkpoints, provenance, and resources. Estimate fits or runs and cost from stated assumptions. Specify a bounded pilot, smoke checks, failure criteria, and conditions for a longer run. Long-running designs should preserve configurations, versions, seeds, intermediate results, resumability, and completion checks. Define stopping or sequential-analysis rules before observing confirmatory outcomes; do not keep adding seeds until significance appears.
- **Evidence artifacts:** Require per-unit or per-run results, an aggregate summary, and plots that reveal each primary comparison and its uncertainty. Follow the active project's `ar_plan`/`ar_dev` report convention with embedded captioned comparison plots and adequate backing CSVs. Default new report directories to the plan basename; preserve an established version-directory convention. Apply `__board__/ARTIFACT_POLICY.md` when present: preserve complete outputs locally and specify selected figures, adequate backing CSVs, core code, and compact metadata for Git. Leave iteration numbering to `ar_plan`.

## 4. Refine until ready or identify a concrete barrier

Review the proposed design against three questions:

1. What will we learn that existing evidence does not already establish?
2. Which mathematical assumption or alternative explanation could invalidate the interpretation?
3. Could positive, negative, and imprecise results each be interpreted honestly under this design?

Resolve weaknesses by revising the claim, comparison, assumptions, or measurement. Record material revisions and their reasons without narrating private deliberation. Do not require arbitrary rounds of review or an open-ended experiment search. Stop when the design supports an actionable handoff or a specific barrier prevents it.

Use one disposition:

- **Ready for planning:** Essential design choices are settled or have bounded decision rules, and the proposed evidence can address the claim.
- **Needs refinement or feasibility evidence:** Name the unresolved issue and the smallest theoretical check, artifact, pilot, or user decision that would resolve it. Provide only a correspondingly scoped handoff.
- **Reuse existing evidence:** Point to the evidence and explain why another run adds little, or how an explicitly motivated replication would differ.
- **Do not run as proposed:** Explain the theoretical flaw, triviality, inability to distinguish explanations, or infeasibility, and offer a defensible reformulation if one exists.

Ask only for missing information that materially changes the question or design. Continue independent analysis while waiting; clearly label assumptions. Do not quietly replace a user's fixed constraint to make the proposal feasible.

## Deliverable and handoff

Save the brief as `__board__/notes/metaplan-YYYY-MM-DD-{slug}.md`. Create only needed directories. Preserve existing board files; use a distinct revision filename for follow-ups unless the user requests an in-place update. Link the previous brief when revising. Do not allocate a `vN` execution-plan number or mark an experiment as running in `STATUS.md`.

## Two-Part Metaplan Structure

After the title and metadata, include **At a Glance**: two short plain-language paragraphs stating the question, what existing evidence establishes, the refined comparison and disposition, the decisive success/failure criteria, and the main limitation or prerequisite. Add a compact facts table when useful. Describe proposed outcomes as proposed; do not present a design as a completed experiment.

Put the exact separator `======` on its own line, with blank lines around it. Follow it with the complete design brief, starting with **Question and Disposition**. Preserve the evidence map, theory, detailed design, sources and copyable handoff; the overview supplements them. Both parts must agree.

Keep the detailed brief proportional to the idea, with these substantive parts:

1. Original idea, refined question, constraints, and disposition.
2. Prior-work evidence map and the precise remaining gap.
3. Theoretical analysis, assumptions, predictions, and failure cases.
4. Proposed comparisons, replication, analysis, budget, and outcome criteria.
5. Material refinements, unresolved issues, and sources.
6. A fenced, ready-to-copy `$ar_plan` prompt when the disposition warrants new work.

Open the planning prompt with a draft Experiment Card in `ar_plan`'s card format (Question, Change, Flow, Compare, Data / splits, Runs, Metric, Decide, Budget, Edit me, Out of scope) so the human sees the experiment's shape before planning. The planning prompt must stand on its own: carry the refined question, evidence-backed gap, required comparisons and controls, information boundaries, primary metric and contrast, independent replication units, replication justification or sizing rule, uncertainty and decision criteria, resource limits, feasibility gates, deliverables, out-of-scope items, and exact supporting artifact paths. Clearly distinguish hard requirements from recommendations and choices left to the planner. For executable work, carry forward full/tiny feasibility, real-data fixture eligibility, device/weight prerequisites and the requirement for production-path debug validation. Preserve the planner's choice of implementation within the local conventions. Include the metaplan path for detailed reasoning, but do not make that path a substitute for the actual design inputs.

For a feasibility disposition, make the prompt explicitly target the prerequisite study and state the condition for later confirmatory planning. For reuse or do-not-run dispositions, do not append a prompt that silently authorizes the rejected experiment.

End with the brief path, disposition, the most consequential refinements, and the copyable prompt or a link to its section. The next step is `$ar_plan` when warranted, not `$ar_dev` directly.

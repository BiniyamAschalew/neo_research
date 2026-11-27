# neo_research

Shared research workflows for Claude Code and Codex. One checkout serves all your projects: the skills are linked in, while each project keeps its own research board (`__board__/`) and settings. Updating means `git pull`.

The organizing idea: **main is the paper, branches are its method sections, worktrees are candidate ideas.** Every idea retains its question, literature and cumulative conclusions. Working ideas move up after compaction and independent review; board evidence moves through Git and approved source transfers locally.

## Setup

```bash
git clone https://github.com/BiniyamAschalew/neo_research.git
cd neo_research && ./install        # once per machine: ar_init and ar_mate on your PATH
ar_init ../my-project               # once per project per machine (must be a git repo with a commit)
```

Then fill in `my-project/__board__/`:  
  
| File | Committed | Contents |
|---|---|---|
| `PROJECT.md` | yes | data paths, conventions that override the defaults |
| `project.env` | **never** | `CONDA_ENV` (or `ENV_ACTIVATE`), `ASSETS_ROOT` (this machine's shared store for datasets and checkpoints), `SLACK_WEBHOOK_URL` ([Incoming Webhook](https://api.slack.com/messaging/webhooks) for this project's channel), `WANDB_URL` (`https://wandb.ai/<entity>/<project>`) |

In the repository root, keep a local `assets.links` describing large folders soft-linked from the store, e.g. `data/raw = datasets/citation`. Worktrees share the datasets and checkpoints through those links.

Research projects track only `.gitignore` and curated `__board__/` content. Source/configs stay local; private settings, backups and raw outputs remain ignored. `ar_init` installs the policy. For an existing project, run `ar_init <project> --dry-run`, then `ar_init <project> --untrack` and commit the index migration; local source files and past history are preserved. The neo_research framework repository itself still tracks its source.

## Ideas Before Experiments

```text
ar_idea "Does the proposed mechanism explain the improvement?"
ar_plan "Test the unresolved claim in I001"
ar_dev v1

__board__/ideas/I001-<slug>/
  idea.md
  papers/
    summary.md
    reference.pdf
```

The concise idea records the hypothesis, theoretical assumptions/falsifier, closest literature, reference reproduction, one evidence row per report and current conclusion. `papers/summary.md` gives detailed source-cited summaries of every reference. Each plan/report links the idea ID and exact hypothesis; development adds a brief result and supports/contradicts/mixed/inconclusive takeaway. An existing published result normally becomes the first small reproduction. `ar_metaplan` remains an alias for this workflow.

Requirements: git, Python 3.9+, Claude Code and/or Codex. Optional: [Herdr](https://herdr.dev) (one tab per agent), W&B, PyYAML (`ar_goal`). Machine-wide rules such as GPU claims go in `~/.config/ar/host.md` (installed from `hosts/` when `ar_init` recognizes the machine).

## How it works

```text
main                          the paper: curated board evidence + __board__/TRACKER.md; source stays local
 ├─ b1/ensembles              branches = method sections: few (≤4 active), general, named b<i>/<name>
 │   └─ worktree idea/bagging     candidate ideas inside a section
 ├─ b2/context-compression
 └─ worktree idea/<slug>      a candidate idea that may open a new section
```

```text
Herdr tab 0:  cd my-project && ar_mate          # or: ar_mate codex   (first mate + local inbox watcher)
You -> mate:  "new idea in b1: does bagging help?"
Mate:         ar_tree new bagging --from b1 --task "..."  -> .trees/bagging + tab whose agent runs
              ar_idea -> ar_plan -> ar_dev on its own (runs log to the project's W&B)
Slack:        one message when ar_dev ends with results: plan, results, takeaways, W&B link (≤7 sentences)
You -> mate:  failed  -> "close it": idea + papers + linked evidence reach main
              works   -> "branch it": ar_branch = compact + cross-agent review + merge into b1
              mature  -> "merge b1":  ar_merge  = compact + review + one squash commit into main
```

New idea and branch agents open at the end of the mate's current Herdr workspace, without changing focus. Herdr assigns the next tab number in that workspace (closed-tab IDs are never reused).

Simple tasks such as downloading a specified file or creating `.gitignore` need only ordinary tools and a short verification. They skip research planning, experiment worktrees, reports and research logging.

The mate keeps its rules in the agent's standing instructions (stays the mate in long sessions), prints the status table itself at start (no tokens), runs with Claude auto mode / Codex "Approve for me" (`--ask` for normal prompts) while every agent it spawns runs with no permission prompts, never edits code itself (routine maintenance goes to a plain agent via `mate_task.py` in the existing checkout; research work goes to an idea worktree with the research skills; enforced by a hook for Claude and, for Codex, a sandbox writable only in `__board__/` plus a mate review policy), and asks you before anything irreversible: full runs, close/branch/merge/drop, new branches, pushes. `__board__/TRACKER.md` on main always shows every branch and worktree.

## Skills

Claude `/ar_<name>`, Codex `$ar_<name>`. Commands and flags: **[SKILLS.md](SKILLS.md)**.

| Skill | Use it to |
|---|---|
| `ar_idea` | literature/theory, stable ID, paper summaries and cumulative experiment takeaways |
| `ar_metaplan` | compatibility entrypoint for `ar_idea` |
| `ar_plan` | write a plan that opens with an editable 20-line Experiment Card |
| `ar_dev` | implement and run it; the report opens with Planned vs Actual |
| `ar_note` | write a focused technical note |
| `ar_tree` | start, close, open and drop ideas and branches; keep the tracker |
| `ar_branch` | worktree → branch: compact, cross-agent review, merge into its parent branch |
| `ar_merge` | branch → main: compact, cross-agent review, one squash commit into main |
| `ar_mate` | first mate: hands each task off once to an idea tab, then reports only watcher events (plans, results, blocked agents); never polls agents |
| `ar_goal` | overnight one-change-at-a-time tuning loop with a sealed test |
| `ar_notify` | Slack text message: final ar_dev report summary only; status alerts and logs stay local |

Conventions every skill follows: [code style](skills/references/code-style.md) (reuse first; `models/`, `methods/`, `data/`, `utils/<topic>/` with `_build.py` registries; data and checkpoints soft-linked from the asset store; hierarchical YAML configs; one `run.py` without argparse; `structure.md` of all signatures; no per-version copies), [W&B tracking](skills/references/tracking.md) (named runs, curves only on real axes, tables for results), [compaction](skills/references/compaction.md) and [review](skills/references/review.md).

## Updating and maintenance

- **Update**: `git pull` in the neo_research checkout. Every linked project sees new skills immediately; `ar_mate` refreshes project links on start, the local inbox watcher restarts itself on new code (including local script edits), and running agent sessions pick up changes when restarted. Nothing is ever written into the checkout, so pulls never conflict.
- **Keep it stable**: the checkout that projects link to should stay on one branch; develop neo_research in a separate clone or `git worktree`.
- **Upgrade an older project**: rerun `ar_init`; shared parts are re-linked, project-specific skills and text are kept (custom `AGENTS.md`/`CLAUDE.md` text moves to `PROJECT.md`), replaced files are backed up, `__board__` content is untouched. `--dry-run` previews, `--untrack` removes old committed links from git.
- **Add a skill**: `skills/<name>/SKILL.md`, link `.agents/skills/<name>`, add `adapters/claude/<name>.md` and link `.claude/commands/<name>.md`. Agents are defined in `skills/references/agents.py`.
- **Tests**: `python -m unittest discover -s tests && python -m unittest discover -s skills/ar_dev/tests`

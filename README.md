# neo_research

Shared research workflows for Claude Code and Codex. One checkout serves all your projects: the skills are linked in, while each project keeps its own research board (`__board__/`) and settings. Updating means `git pull`.

The organizing idea: **main is the paper, branches are its method sections, worktrees are candidate ideas.** Failed ideas leave only a summary; working ideas move up only after their code is compacted and reviewed by a second agent, so main stays small enough to read and debug yourself.

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
| `project.env` | **never** | `CONDA_ENV` (or `ENV_ACTIVATE`), `SLACK_WEBHOOK_URL` ([Incoming Webhook](https://api.slack.com/messaging/webhooks) for this project's channel), `WANDB_URL` (`https://wandb.ai/<entity>/<project>`) |

Requirements: git, Python 3.9+, Claude Code and/or Codex. Optional: [Herdr](https://herdr.dev) (one tab per agent), W&B, PyYAML (`ar_goal`). Machine-wide rules such as GPU claims go in `~/.config/ar/host.md` (installed from `hosts/` when `ar_init` recognizes the machine).

## How it works

```text
main                          the paper: best compacted code + summaries + __board__/TRACKER.md
 ├─ b1/ensembles              branches = method sections: few (≤4 active), general, named b<i>/<name>
 │   └─ worktree idea/bagging     candidate ideas inside a section
 ├─ b2/context-compression
 └─ worktree idea/<slug>      a candidate idea that may open a new section
```

```text
Herdr tab 0:  cd my-project && ar_mate          # or: ar_mate codex   (first mate + Slack watcher)
You -> mate:  "new idea in b1: does bagging help? plan it"
Mate:         ar_tree new bagging --from b1 -> worktree + tab with its own agent, which runs ar_plan
Slack:        "plan ready for review" + Experiment Card    -> you edit the card, tell the mate "approved"
Idea agent:   ar_dev, runs through notify_run.py (logs to the project's W&B)
Slack:        "run finished" (+ duration), then "experiment done" + Planned vs Actual card
You -> mate:  failed  -> "close it": only the summary reaches main
              works   -> "branch it": ar_branch = compact + cross-agent review + merge into b1
              mature  -> "merge b1":  ar_merge  = compact + review + one squash commit into main
```

The mate keeps its rules in the agent's standing instructions (stays the mate in long sessions), runs with Claude auto mode / Codex "Approve for me" (`--ask` for normal prompts), never edits code itself, and asks you before anything irreversible: full runs, close/branch/merge/drop, new branches, pushes. `__board__/TRACKER.md` on main always shows every branch and worktree.

## Skills

Claude `/ar_<name>`, Codex `$ar_<name>`. Commands and flags: **[SKILLS.md](SKILLS.md)**.

| Skill | Use it to |
|---|---|
| `ar_metaplan` | sharpen an idea: prior evidence, theory, decisive experiment design |
| `ar_plan` | write a plan that opens with an editable 20-line Experiment Card |
| `ar_dev` | implement and run it; the report opens with Planned vs Actual |
| `ar_note` | write a focused technical note |
| `ar_tree` | start, close, open and drop ideas and branches; keep the tracker |
| `ar_branch` | worktree → branch: compact, cross-agent review, merge into its parent branch |
| `ar_merge` | branch → main: compact, cross-agent review, one squash commit into main |
| `ar_mate` | first mate coordinating all ideas of a project |
| `ar_goal` | overnight one-change-at-a-time tuning loop with a sealed test |
| `ar_notify` | Slack text message when a run ends |

Conventions every skill follows: [code style](skills/references/code-style.md) (reuse first; `models/`, `methods/`, `data/`, `utils/<topic>/` with `_build.py` registries; hierarchical YAML configs; one `run.py` without argparse; `structure.md` of all signatures; no per-version copies), [W&B tracking](skills/references/tracking.md) (named runs, curves only on real axes, tables for results), [compaction](skills/references/compaction.md) and [review](skills/references/review.md).

## Updating and maintenance

- **Update**: `git pull` in the neo_research checkout. Every linked project sees new skills immediately; `ar_mate` refreshes project links on start, the Slack watcher restarts itself on new code, and running agent sessions pick up changes when restarted. Nothing is ever written into the checkout, so pulls never conflict.
- **Keep it stable**: the checkout that projects link to should stay on one branch; develop neo_research in a separate clone or `git worktree`.
- **Upgrade an older project**: rerun `ar_init`; shared parts are re-linked, project-specific skills and text are kept (custom `AGENTS.md`/`CLAUDE.md` text moves to `PROJECT.md`), replaced files are backed up, `__board__` content is untouched. `--dry-run` previews, `--untrack` removes old committed links from git.
- **Add a skill**: `skills/<name>/SKILL.md`, link `.agents/skills/<name>`, add `adapters/claude/<name>.md` and link `.claude/commands/<name>.md`. Agents are defined in `skills/references/agents.py`.
- **Tests**: `python -m unittest discover -s tests && python -m unittest discover -s skills/ar_dev/tests`

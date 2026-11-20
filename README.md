# neo_research

Shared research workflows for Claude Code and Codex. One checkout serves all your projects: skills are linked in, while each project keeps its own `__board__/` (plans, reports, idea summaries, Slack and tracking settings).

## Quick start

```bash
git clone https://github.com/BiniyamAschalew/neo_research.git
cd neo_research && ./install   # once per machine: ar_init and ar_mate become shell commands
ar_init ../my-project          # once per project per machine; safe to rerun (project must be a git repo with a commit)
```

Then fill in two files in `my-project/__board__/`: 

| File | Committed | Contents |
|---|---|---|
| `PROJECT.md` | yes | conda env, data paths, conventions |
| `project.env` | **never** | `SLACK_WEBHOOK_URL` (this project's channel), `WANDB_URL` (W&B project page; entity and project are read from it) |

Requirements: git, Python 3.8+, and an agent CLI: Claude Code or Codex (others work with fewer guarantees; agents are defined in `skills/references/agents.py`). Optional: [Herdr](https://herdr.dev), a Slack [Incoming Webhook](https://api.slack.com/messaging/webhooks) per project, W&B, PyYAML (for `ar_goal`).

## Example: from idea to Slack

```text
Herdr tab 0:   cd my-project && ar_mate              # or: ar_mate codex   (first mate + Slack watcher)
You -> mate:   "new idea: does a cosine schedule beat step decay on val AUC? plan it"
Mate:          ar_tree new cosine-lr [--agent codex] -> worktree + tab with its own agent, which runs ar_plan
Slack:         "my-project/cosine-lr: plan ready for review" + Experiment Card
You:           edit the card if needed, tell the mate "approved"
Mate:          idea agent runs ar_dev through notify_run.py (logs to this project's W&B)
Slack:         run finished + duration, then "experiment done" + Planned vs Actual card + tracking link
You -> mate:   failed: "close it as dead" -> only its summary returns to main
               works:  "compact and promote it as a new direction" -> ar_compact, then branch dir/schedules
Later:         more explorations --from schedules; when the direction is mature: open, ar_compact, graduate -> main
```

## Branch model: keep main small

```text
main            only the best, compacted, paper-worthy code + summaries of everything tried
 ├─ dir/<name>  a working direction (one per trend: dir/context-compression, dir/ensembling, ...)
 │   └─ worktree  explorations going deeper in that direction
 └─ worktree      new explorations from main
```

Failed explorations leave only a summary (`__board__/ideas/`), never code. Each move up (worktree → direction → main) is gated by `ar_compact`: keep only what the result needs, rewrite it shorter and faster with identical results, prove parity. All tiers follow [code style](skills/references/code-style.md): reuse first, one home per entity (`models/`, `methods/`, `data/`, `utils/<topic>/` with `_build.py` registries), hierarchical YAML configs, one `run.py` with no argparse, and a `structure.md` of every signature.

`ar_mate [agent]` puts the mate rules in the agent's standing instructions (Claude: system prompt; Codex: developer instructions), so it stays the mate through long sessions. Mate and idea agents can differ, e.g. a Claude mate driving Codex ideas. Approvals default to Claude auto mode / Codex "Approve for me" (risky actions still ask); `ar_mate --ask` keeps normal prompts. It asks before anything irreversible (full runs, closes, merges, pushes) and never edits code itself.

## Skills

| Skill | Use it to |
|---|---|
| `ar_metaplan` | sharpen an idea: prior evidence, theory, decisive design |
| `ar_plan` | write a plan that opens with an editable 20-line Experiment Card |
| `ar_dev` | implement and run it; report opens with Planned vs Actual |
| `ar_tree` | explorations (worktrees) → directions (`dir/*` branches) → main; failures return only a summary |
| `ar_compact` | before each promotion: same results, less and cleaner code, with parity proof |
| `ar_mate` | first mate coordinating all ideas of a project |
| `ar_goal` | overnight one-change-at-a-time tuning loop with a sealed test |
| `ar_notify` | Slack text message when a run ends |
| `ar_note` | focused technical note |

Claude: `/ar_<name>`, Codex: `$ar_<name>`; set `AR_AGENT=codex` to make Codex the default for `ar_mate`, `ar_tree` and `ar_goal`. Commands and flags: **[SKILLS.md](SKILLS.md)**.

W&B logging is curated by [tracking conventions](skills/references/tracking.md): descriptive run names and groups, curves only along a real x-axis, one-off results as summary values or tables (no one-dot charts).

## What `ar_init` does

- Links `.agents`, `.codex`, `AGENTS.md`, `.claude/commands`, `.claude/CLAUDE.md` to this checkout; `.claude/` stays a real folder; Claude's local settings live in `__board__/claude/`.
- Creates `__board__/PROJECT.md` and `__board__/project.env` if missing; hides links and `project.env` from git via `.git/info/exclude`.
- On an older setup: re-links anything that came from neo_research, keeps project-only skills/commands, moves custom `AGENTS.md`/`CLAUDE.md` text into `PROJECT.md`, never touches other `__board__/` content, backs up every replaced file to `__board__/notes/local/ar_init-backup/`. `--dry-run` previews; `--untrack` untracks old committed links.
- Idea worktrees get the same links and use the main checkout's `project.env`, so each project's notifications and runs stay in its own channel and workspace.

Linked projects follow this checkout live; keep it on a stable branch and develop neo_research in a separate clone or worktree. Machine-wide rules (e.g. GPU claims) go in `~/.config/ar/host.md`, installed from `hosts/` when recognized.

## Layout and tests

```text
install            make ar_init / ar_mate shell commands
ar_init, ar_mate   setup and first-mate launchers
skills/<name>/     SKILL.md + scripts        adapters/claude/   slash-command wrappers
hosts/             machine rule templates    tests/             tooling tests (not linked)
```

```bash
python -m unittest discover -s tests && python -m unittest discover -s skills/ar_dev/tests
```

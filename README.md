# neo_research

Shared research workflows for Claude Code and Codex. One checkout of this repo serves all your projects: skills are linked into each project, while each project keeps its own research board (`__board__/`) with plans, reports, notes and idea summaries.

## Quick start

```bash
git clone git@github.com:BiniyamAschalew/neo_research.git
cd neo_research
./ar_init ../my-project        # the only setup step
```

Then open `claude` (or `codex`) in `../my-project` and run e.g. `/ar_plan "test X against baseline Y"`.

`./ar_init --dry-run ../my-project` previews; rerunning is safe. Run it once per project on each machine.

**Requirements**: git, Python 3.8+, Claude Code and/or Codex CLI. Optional: [Herdr](https://herdr.dev) (one tab per idea), a Slack Incoming Webhook (run notifications), PyYAML (`ar_goal` configs).

## Example: from idea to Slack

```text
Terminal:      cd neo_research && ./ar_init ../my-project           # once per project (safe to rerun)
Herdr tab 0:   cd ../my-project && claude
               /ar_mate                                  # also starts the Slack watcher (mate-watch tab)
You -> mate:   "new idea: does a cosine schedule beat step decay on val AUC? plan it"
Mate:          ar_tree new cosine-lr  -> new worktree + Herdr tab with its own agent,
               tells it to run /ar_plan (or /ar_metaplan first)
Slack:         "my-project/cosine-lr: plan ready for review" + Experiment Card
You:           read/edit the card in ../my-project.ideas/cosine-lr/__board__/plans/, then tell the mate "approved"
Mate:          tells the idea agent to run /ar_dev; the run goes through notify_run.py
Slack:         run finished/FAILED + duration, then "experiment done" + Planned vs Actual card
You -> mate:   "close it as dead" (or win/parked) -> summary to main, code archived
```

You only talk to the mate; it never edits code and asks before anything irreversible (full runs, closes, merges, pushes). Long tuning runs: ask the mate for an `/ar_goal` loop in the idea.

## Skills

| Skill | Use it to |
|---|---|
| `ar_metaplan` | sharpen an idea: prior evidence, theory, decisive experiment design |
| `ar_plan` | write a plan that opens with an editable 20-line **Experiment Card** |
| `ar_dev` | implement and run the plan; report opens with the card as Planned vs Actual |
| `ar_tree` | give each idea its own worktree; closing returns only a summary to main |
| `ar_mate` | one "first mate" agent that coordinates all ideas in a project |
| `ar_goal` | overnight one-change-at-a-time improvement loop with a sealed test |
| `ar_notify` | Slack text message whenever an experiment run ends |
| `ar_note` | write a focused technical note |

Claude uses `/ar_<name>`, Codex `$ar_<name>`. Commands, flags and the typical flow: **[SKILLS.md](SKILLS.md)**.

## What `ar_init` sets up

```text
my-project/
  .agents            -> neo_research/.agents          shared skills
  .codex             -> neo_research/.codex
  AGENTS.md          -> neo_research/AGENTS.md        shared instructions
  .claude/           real folder (stays per project)
    commands         -> neo_research/.claude/commands
    CLAUDE.md        -> neo_research/.claude/CLAUDE.md
    settings.local.json -> ../__board__/claude/settings.local.json
  __board__/         this project's research state
    PROJECT.md       fill in once: env, data paths, conventions
```

- Rerun it on an already set-up project to upgrade it. Anything that came from neo_research (old links, copied shared skills or commands, old copies of `AGENTS.md`) is replaced by a link; project-only skills and commands stay beside the shared ones; custom text in `AGENTS.md`/`CLAUDE.md` moves into `__board__/PROJECT.md`; Claude's local settings move to `__board__/claude/`. `__board__/` content (status, plans, reports, notes) is never touched. Every replaced real file is backed up to `__board__/notes/local/ar_init-backup/<time>/`.
- If an older setup committed agent files to git, `--untrack` removes them from the index (files stay on disk); commit afterwards.
- Links are absolute and machine-specific, so they are hidden via `.git/info/exclude` and never committed.
- New or updated skills here reach every linked project immediately. Keep the linked checkout on a stable branch and develop neo_research in a separate clone or worktree.

## Per-project and per-machine settings

| File | Scope | Purpose |
|---|---|---|
| `my-project/__board__/PROJECT.md` | project | env, data, conventions that override shared defaults |
| `~/.config/ar/host.md` | machine | e.g. GPU claim rules; `ar_init` installs one from `hosts/` when it recognizes the machine |
| `neo_research/secrets/slack.env` | machine | Slack webhook (see below) |

## Slack notifications

The webhook lives in **`neo_research/secrets/slack.env`**, one file per machine, gitignored (never committed):

```bash
cd neo_research
cp secrets/slack.env.example secrets/slack.env      # if it does not exist yet
# edit secrets/slack.env:
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

Get the URL by creating a Slack app with **Incoming Webhooks** enabled for your channel (https://api.slack.com/messaging/webhooks). Every linked project uses this file; `AR_SLACK_ENV=/other/path` overrides it. Without it, notifications print `skipped` and nothing else changes. Test: `python skills/ar_notify/scripts/slack_notify.py --title test --text hello`.

Messages come from `notify_run.py` (every run's end), `mate_watch.py` (plan ready, experiment report, goal finished, agent blocked) and `ar_goal`; the same report is never posted twice.

## Repository layout

```text
ar_init               project setup command
skills/<name>/        skill definitions (SKILL.md) and their scripts
adapters/claude/      thin Claude slash-command wrappers that load the skills
skills/references/    shared execution and artifact-publication conventions
hosts/                machine rule templates for ~/.config/ar/host.md
tests/                tests for the tooling itself (never linked into projects)
```

To add a skill: create `skills/<name>/SKILL.md`, link it from `.agents/skills/<name>`, add `adapters/claude/<name>.md` and link it from `.claude/commands/<name>.md`. Linked projects see it at once.

## Tests

```bash
python -m unittest discover -s tests -v
python -m unittest discover -s skills/ar_dev/tests -v
```

# neo_research research workflows

Shared instructions for every agent (Codex reads this file; Claude imports it). Skills: Codex `$ar_<name>`, Claude `/ar_<name>`.

## Startup

1. Read `__board__/STATUS.md`, `__board__/PROJECT.md` (project specifics, override defaults) and `~/.config/ar/host.md` (machine rules such as GPU claims; if missing on a GPU server, check `hosts/` in the neo_research checkout) when they exist.
2. In the main checkout read `__board__/TRACKER.md` (branches and worktrees); inside an idea worktree read `__board__/IDEA.md`.
3. Read plans, reports and notes only when the task needs them. Do not create `__board__/` at startup; skills create what they need ([board conventions](.agents/skills/references/board.md)).

## Skills

| Skill | Use it to |
|---|---|
| `ar_metaplan <idea>` | sharpen an idea: prior evidence, theory, decisive experiment design |
| `ar_plan <task>` | write a plan opening with an editable Experiment Card |
| `ar_dev [vN]` | implement and run it; report opens with Planned vs Actual |
| `ar_note <topic>` | focused technical note |
| `ar_tree new\|close\|open\|drop\|tracker` | candidate ideas in worktrees, branches `b<i>/<name>` as method sections, main as the paper |
| `ar_branch <slug>` | compact + cross-agent review + move a working idea into its branch |
| `ar_merge <b>` | compact + cross-agent review + merge a branch into main |
| `ar_mate` | first mate coordinating all ideas of the project |
| `ar_goal` | overnight one-change-at-a-time tuning loop with a sealed test |
| `ar_notify [report]` | Slack text summary of a finished run |

## Rules

- Code follows [code style](.agents/skills/references/code-style.md): reuse first, entity folders with `_build.py` registries, hierarchical YAML configs, one `run.py` without argparse, `structure.md` kept current, no per-version copies.
- Use the project's code environment (`CONDA_ENV` / `ENV_ACTIVATE` in `__board__/project.env`); record any package you install in the report.
- Launch experiment runs through `python .agents/skills/ar_notify/scripts/notify_run.py -- <command>` so every completion posts to this project's Slack channel and runs log to this project's W&B (`WANDB_URL`). Never print or commit `__board__/project.env`.
- Stay within the selected plan; take the smallest reasonable decision on ambiguity and record it; ask when scope or authority would grow.
- Never overwrite another agent's board file. Never `git push`, push tags, or run `--yes` on `ar_tree`/`ar_branch`/`ar_merge` steps without the human's explicit approval.

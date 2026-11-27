# neo_research research workflows

Shared instructions for every agent (Codex reads this file; Claude imports it). Skills: Codex `$ar_<name>`, Claude `/ar_<name>`.

## Startup

1. Read `__board__/STATUS.md`, `__board__/PROJECT.md` (project specifics, override defaults) and `~/.config/ar/host.md` (machine rules such as GPU claims; if missing on a GPU server, check `hosts/` in the neo_research checkout) when they exist.
2. In the main checkout read `__board__/TRACKER.md` (branches and worktrees); inside an idea worktree read `__board__/IDEA.md`.
3. Read plans, reports and notes only when the task needs them. Do not create `__board__/` at startup; skills create what they need ([board conventions](.agents/skills/references/board.md)).

## Skills
  
| Skill | Use it to |
|---|---|
| `ar_idea <idea>` | maintain an ID-bearing idea, literature/theory, paper summaries and cumulative takeaways |
| `ar_metaplan <idea>` | compatibility entrypoint for `ar_idea` |
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

- Before research planning, resolve `__board__/ideas/I###-<slug>/idea.md`. Plans and reports name the idea ID and exact hypothesis. Every development report updates one concise evidence row and the idea's current conclusion. Detailed paper summaries live in that idea's `papers/summary.md`.
- Research projects publish only `.gitignore` and curated `__board__/` content. Code/configs/assets remain local; never force-add them. `ar_init` installs this policy; `ar_init <project> --untrack` migrates previously tracked ignored files without deleting local copies. This framework repository itself remains a normal code repository.
- Reserve `ar_metaplan`, `ar_plan` and `ar_dev` for research ideation, experiment design, implementation, execution and analysis. Routine maintenance (for example downloading a specified file or creating `.gitignore`) uses ordinary tools and proportionate verification; it needs no experiment card, research worktree, report, W&B run or Slack notification.
- Code follows [code style](.agents/skills/references/code-style.md): reuse first, entity folders with `_build.py` registries, hierarchical YAML configs, one `run.py` without argparse, `structure.md` kept current, no per-version copies.
- Datasets, checkpoints and large caches are soft links from the machine's asset store listed in `assets.links` (`ASSETS_ROOT` in `__board__/project.env`): read and write through the repository-relative link path, never copy them into the repo; add a line to `assets.links` and rerun `ar_init .` for a new shared folder.
- Use the project's code environment (`CONDA_ENV` / `ENV_ACTIVATE` in `__board__/project.env`); record any package you install in the report.
- Launch experiment runs through `python .agents/skills/ar_notify/scripts/notify_run.py -- <command>` so runs log to this project's W&B (`WANDB_URL`). Slack is only for ar_dev's final result summary; no agent-status alerts, plans, raw logs or standalone goal-loop messages (`--notify` only for background runs that write a final report). Never print or commit `__board__/project.env`.
- Stay within the selected plan; take the smallest reasonable decision on ambiguity and record it; ask when scope or authority would grow.
- Never overwrite another agent's board file. Never `git push`, push tags, or run `--yes` on `ar_tree`/`ar_branch`/`ar_merge` steps without the human's explicit approval.

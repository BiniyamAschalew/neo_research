#!/usr/bin/env python3
"""ar_goal: overnight hill-climb inside an idea worktree, one component change per iteration.

Each iteration a fresh agent session makes one change within the allowed files; the
driver evaluates it and commits only if the validation metric beats the best by more
than the noise threshold, otherwise it reverts. The sealed test split is evaluated
once, at the end, on the best commit.

    python goal.py goal.yaml            # start or resume
    python goal.py goal.yaml --dry-run  # validate config and baseline eval only
"""

import argparse
from datetime import datetime
import fnmatch
import importlib.util
import json
import os
from pathlib import Path
import shlex
import statistics
import subprocess
import sys
import time

STATE = Path("__board__/goal")
NOTIFY = Path(__file__).resolve().parents[2] / "ar_notify/scripts/slack_notify.py"
DEFAULTS = {
    "direction": "max", "goal": None, "max_iters": 20, "max_hours": 8.0, "baseline_repeats": 3,
    "candidate_repeats": 1, "min_delta": None, "delta_std_factor": 2.0, "max_consecutive_failures": 3,
    "agent": None, "agent_cmd": None, "agent_timeout_min": 30,
    "eval_timeout_min": 120, "gpu_wrapper": "", "final_test": True, "test_metric": None, "history_rows": 15,
}
REQUIRED = ["objective", "eval_cmd", "metrics_file", "metric", "allowed"]
COLUMNS = ["iter", "time", "value", "decision", "gain", "files", "change"]


def load_config(path):
    text = Path(path).read_text()
    if str(path).endswith(".json"):
        config = json.loads(text)
    else:
        import yaml  # conda envs normally ship PyYAML; use goal.json otherwise
        config = yaml.safe_load(text)
    missing = [k for k in REQUIRED if k not in config]
    if missing:
        raise SystemExit(f"goal config missing: {missing}")
    config = {**DEFAULTS, **config}
    if not config["agent_cmd"]:  # agent name -> its headless command (skills/references/agents.py)
        spec = importlib.util.spec_from_file_location("agents", Path(__file__).resolve().parents[2] / "references/agents.py")
        agents = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(agents)
        config["agent_cmd"] = agents.spec(config["agent"])["headless"]
        if not config["agent_cmd"]:
            raise SystemExit(f"No headless command known for agent '{config['agent']}'; set agent_cmd in the goal config.")
    return config


def git(*args, check=True):
    result = subprocess.run(["git", *args], text=True, capture_output=True)
    if check and result.returncode:
        raise SystemExit(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout.strip()


def tracking_env():
    """This project's WANDB_* settings from __board__/project.env, for eval runs."""
    if not NOTIFY.exists():
        return {}
    spec = importlib.util.spec_from_file_location("slack_notify", NOTIFY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.tracking_env(module.load_keys())


def activation():
    """Activate the project's code environment (CONDA_ENV / ENV_ACTIVATE in __board__/project.env) for evals and agents."""
    if not NOTIFY.exists():
        return ""
    spec = importlib.util.spec_from_file_location("slack_notify", NOTIFY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    keys = module.load_keys()
    if keys.get("CONDA_ENV") and keys["CONDA_ENV"] == os.environ.get("CONDA_DEFAULT_ENV"):
        return ""
    return module.activation(keys)


def shell(command, env=None, timeout_min=60):
    prefix = activation()
    command = f"{prefix} && {command}" if prefix else command
    try:
        result = subprocess.run(command, shell=True, executable="/bin/bash", text=True, capture_output=True, env={**os.environ, **(env or {})},
                                timeout=timeout_min * 60)
        return result.returncode, (result.stdout + result.stderr)[-3000:]
    except subprocess.TimeoutExpired:
        return 124, f"timed out after {timeout_min} min"


def lookup(metrics, key):
    for part in key.split("."):
        metrics = metrics[part]
    return float(metrics)


def evaluate(cfg, split, metric, log_name):
    metrics_file = Path(cfg["metrics_file"])
    metrics_file.unlink(missing_ok=True)
    command = f"{cfg['gpu_wrapper']} {cfg['eval_cmd']}".strip()
    branch = git("rev-parse", "--abbrev-ref", "HEAD").replace("/", "-")
    env = {**tracking_env(), "AR_GOAL_SPLIT": split, "WANDB_RUN_GROUP": f"{branch}-goal",
           "WANDB_JOB_TYPE": "goal-eval", "WANDB_NAME": f"{branch}-goal-{log_name}"}
    code, output = shell(command, env, cfg["eval_timeout_min"])
    (STATE / "logs").mkdir(parents=True, exist_ok=True)
    (STATE / "logs" / f"{log_name}.log").write_text(output)
    if code or not metrics_file.exists():
        return None
    try:
        return lookup(json.loads(metrics_file.read_text()), metric)
    except (KeyError, ValueError, TypeError):
        return None


def mean_eval(cfg, repeats, name):
    values = [evaluate(cfg, "val", cfg["metric"], f"{name}-{r}") for r in range(repeats)]
    return None if any(v is None for v in values) else values


def changed_files(ignore=()):
    out = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], text=True, capture_output=True, check=True).stdout
    files = [line[3:].split(" -> ")[-1].strip('"') for line in out.splitlines() if line.strip()]
    return [f for f in files if not f.startswith(str(STATE) + "/") and f not in ignore]


def outside(files, allowed):
    return [f for f in files if not any(fnmatch.fnmatch(f, pattern) for pattern in allowed)]


def revert(files):
    git("reset", "-q", "--hard", "HEAD")
    untracked = [f for f in files if Path(f).exists()]
    if untracked:
        git("clean", "-fq", "--", *untracked)


def better(value, best, delta, direction):
    return value > best + delta if direction == "max" else value < best - delta


def reached(value, goal, direction):
    return goal is not None and (value >= goal if direction == "max" else value <= goal)


def read_log():
    path = STATE / "log.tsv"
    if not path.exists():
        return []
    return [dict(zip(COLUMNS, line.split("\t"))) for line in path.read_text().splitlines()[1:] if line.strip()]


def append_log(row):
    path = STATE / "log.tsv"
    if not path.exists():
        path.write_text("\t".join(COLUMNS) + "\n")
    with path.open("a") as handle:
        handle.write("\t".join(str(row.get(c, "")).replace("\t", " ").replace("\n", " ") for c in COLUMNS) + "\n")


def prompt(cfg, best, rows):
    history = "\n".join(f"- iter {r['iter']}: {r['decision']} ({r['value']}): {r['change']}" for r in rows[-cfg["history_rows"]:]) or "- none yet"
    return f"""You are one iteration of an automated improvement loop (ar_goal). Fresh context; read files as needed.

Objective: {cfg['objective']}
Validation metric: {cfg['metric']} ({cfg['direction']}imize). Current best: {best['value']:.6g}; a change is kept only if it beats this by more than {best['delta']:.3g}.
Allowed files (globs): {', '.join(cfg['allowed'])}

Previous attempts (do not repeat rejected ideas; build on kept ones):
{history}

Make exactly ONE focused component change within the allowed files. Do not run training or evaluation; the driver does that.
Do not touch test-split code, data, evaluation or metric code. Do not commit.
Finally write a one-line description of the change to {STATE}/change.txt."""


class Tracker:
    """One W&B run per loop: val metric and best-so-far as curves over iterations, a final table.
    Inactive unless wandb is installed and WANDB_URL is set in __board__/project.env."""

    def __init__(self, cfg):
        self.run = None
        env = tracking_env()
        try:
            import wandb
        except ImportError:
            return
        if not env.get("WANDB_PROJECT"):
            return
        branch = git("rev-parse", "--abbrev-ref", "HEAD").replace("/", "-")
        try:
            self.run = wandb.init(project=env["WANDB_PROJECT"], entity=env.get("WANDB_ENTITY"), name=f"{branch}-goal",
                                  group=f"{branch}-goal", job_type="goal", config=cfg, resume="allow", id=f"{branch}-goal")
            self.run.define_metric("goal/iteration")
            self.run.define_metric("goal/*", step_metric="goal/iteration")
        except Exception as error:  # tracking must never stop the loop
            print(f"W&B tracking off: {error}")
            self.run = None

    def log(self, row, best):
        if self.run and row.get("value"):
            self.run.log({"goal/iteration": int(row["iter"]), "goal/val": float(row["value"]),
                          "goal/best_val": best["value"], "goal/kept": int(row["decision"] == "kept")})

    def finish(self, rows, best, test_value, reason):
        if not self.run:
            return
        import wandb
        table = wandb.Table(columns=["iter", "val", "decision", "change"],
                            data=[[int(r["iter"]), r["value"], r["decision"], r["change"]] for r in rows])
        self.run.log({"goal/attempts": table})
        self.run.summary.update({"goal/baseline_val": best["baseline"], "goal/best_val": best["value"],
                                 "goal/test": test_value, "goal/stop_reason": reason})
        self.run.finish()


TRACKER = None


def finish(cfg, best, rows, reason, started, final_test=True):
    test_value = None
    if final_test and cfg["final_test"] and best.get("commit"):
        test_value = evaluate(cfg, "test", cfg["test_metric"] or cfg["metric"], "final-test")
    kept = [r for r in rows if r["decision"] == "kept"]
    figure = plot(rows, best)
    lines = [
        f"# ar_goal summary", "",
        f"**Objective**: {cfg['objective']}", f"**Stopped**: {reason} after {len(rows)} iterations, "
        f"{(time.time() - started) / 3600:.1f} h this session",
        f"**Baseline val {cfg['metric']}**: {best['baseline']:.6g} (noise threshold {best['delta']:.3g})",
        f"**Best val**: {best['value']:.6g} at `{best.get('commit') or 'baseline'}` ({len(kept)} kept changes)",
        f"**Sealed test**: {'not run' if test_value is None else f'{test_value:.6g}'} (evaluated once, on the best commit)", "",
        "| iter | val | decision | change |", "|---|---|---|---|",
        *[f"| {r['iter']} | {r['value']} | {r['decision']} | {r['change']} |" for r in rows[-20:]], "",
    ]
    if figure:
        lines += [f"![progress]({figure.name})", "", "*Figure 1. Validation metric per iteration; kept changes in color, rejected in grey; dashed line = baseline.*"]
    summary = STATE / "summary.md"
    summary.write_text("\n".join(lines) + "\n")
    paths = [str(p) for p in (summary, STATE / "log.tsv", STATE / "best.json", STATE / ".gitignore", figure) if p and Path(p).exists()]
    git("add", "-f", "--", *paths)
    git("commit", "-q", "-m", f"goal: summary ({reason})", check=False)
    table = ["| iter | val | decision | change |", "|---|---|---|---|",
             *[f"| {r['iter']} | {r['value']} | {r['decision']} | {r['change'][:48]} |" for r in rows[-8:]]]
    text = (f"Val {cfg['metric']}: baseline {best['baseline']:.4g} → best {best['value']:.4g} "
            f"({len(kept)}/{len(rows)} changes kept, noise {best['delta']:.3g}).\n"
            f"Sealed test: {'not run' if test_value is None else f'{test_value:.4g}'}\n" + "\n".join(table)
            + f"\nSummary: `{summary}`")
    project = Path(git("worktree", "list", "--porcelain").splitlines()[0].split(" ", 1)[1]).name
    notify(f"ar_goal {project}/{git('rev-parse', '--abbrev-ref', 'HEAD')}: {reason}", text)
    if TRACKER:
        TRACKER.finish(rows, best, test_value, reason)
    print(summary.read_text())


def plot(rows, best):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return None
    points = [(int(r["iter"]), float(r["value"]), r["decision"] == "kept") for r in rows if r["value"] not in ("", "None")]
    if not points:
        return None
    fig, ax = plt.subplots(figsize=(6, 3.2))
    ax.scatter([p[0] for p in points if not p[2]], [p[1] for p in points if not p[2]], color="0.7", label="rejected")
    ax.scatter([p[0] for p in points if p[2]], [p[1] for p in points if p[2]], color="tab:blue", label="kept")
    ax.axhline(best["baseline"], linestyle="--", color="k", linewidth=1, label="baseline")
    ax.set_xlabel("iteration")
    ax.set_ylabel("validation metric")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    path = STATE / "progress.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def notify(title, text):
    if not NOTIFY.exists():
        return
    spec = importlib.util.spec_from_file_location("slack_notify", NOTIFY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    print(json.dumps(module.notify(title, module.to_slack(text))))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("config", type=Path)
    parser.add_argument("--dry-run", action="store_true", help="Validate config and baseline only")
    args = parser.parse_args()
    cfg = load_config(args.config)
    os.chdir(git("rev-parse", "--show-toplevel"))
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    if branch in {"main", "master"} or not branch:
        raise SystemExit("Run ar_goal inside an idea worktree branch (ar_tree new ...), never on main.")
    ignore = {cfg["metrics_file"]}
    if changed_files(ignore):
        raise SystemExit("Worktree has uncommitted changes; commit or discard them first.")
    STATE.mkdir(parents=True, exist_ok=True)
    if not (STATE / ".gitignore").exists():
        (STATE / ".gitignore").write_text("logs/\nchange.txt\nmetrics.json\n")
    best_path = STATE / "best.json"
    started = time.time()

    if best_path.exists():
        best = json.loads(best_path.read_text())
    else:
        values = mean_eval(cfg, cfg["baseline_repeats"], "baseline")
        if values is None:
            raise SystemExit(f"Baseline evaluation failed; see {STATE}/logs/. Eval must write {cfg['metrics_file']} with '{cfg['metric']}'.")
        spread = statistics.stdev(values) if len(values) > 1 else 0.0
        delta = cfg["min_delta"] if cfg["min_delta"] is not None else cfg["delta_std_factor"] * spread
        best = {"baseline": statistics.mean(values), "value": statistics.mean(values), "delta": delta,
                "baseline_runs": values, "commit": ""}
        best_path.write_text(json.dumps(best, indent=2))
    print(f"baseline {best['baseline']:.6g}, best {best['value']:.6g}, noise threshold {best['delta']:.3g}")
    if args.dry_run:
        return 0

    global TRACKER
    TRACKER = Tracker(cfg)
    rows = read_log()
    failures, reason = 0, "max_iters"
    clean = True
    try:
        for iteration in range(len(rows) + 1, cfg["max_iters"] + 1):
            if reached(best["value"], cfg["goal"], cfg["direction"]):
                reason = "goal reached"
                break
            if (time.time() - started) / 3600 > cfg["max_hours"]:
                reason = "time budget"
                break
            if failures >= cfg["max_consecutive_failures"]:
                reason = f"{failures} consecutive failures"
                break
            (STATE / "change.txt").unlink(missing_ok=True)
            command = " ".join(shlex.quote(c) for c in cfg["agent_cmd"]) + " " + shlex.quote(prompt(cfg, best, rows))
            code, output = shell(command, timeout_min=cfg["agent_timeout_min"])
            (STATE / "logs").mkdir(exist_ok=True)
            (STATE / "logs" / f"agent-{iteration:03d}.log").write_text(output)
            files = changed_files(ignore)
            change = (STATE / "change.txt").read_text().strip() if (STATE / "change.txt").exists() else "(no description)"
            row = {"iter": iteration, "time": datetime.now().strftime("%H:%M"), "files": ",".join(files), "change": change}
            bad = outside(files, cfg["allowed"])
            if code or not files or bad:
                revert(files)
                failures += 1
                row.update(value="", decision="agent-error" if code else ("no-op" if not files else f"outside:{','.join(bad)}"))
            else:
                values = mean_eval(cfg, cfg["candidate_repeats"], f"iter-{iteration:03d}")
                if values is None:
                    revert(files)
                    failures += 1
                    row.update(value="", decision="eval-failed")
                else:
                    value = statistics.mean(values)
                    gain = value - best["value"] if cfg["direction"] == "max" else best["value"] - value
                    row.update(value=f"{value:.6g}", gain=f"{gain:.3g}")
                    failures = 0
                    if better(value, best["value"], best["delta"], cfg["direction"]):
                        git("add", "-A", "--", *files)
                        git("commit", "-q", "-m", f"goal iter {iteration}: {change} ({cfg['metric']}={value:.6g})")
                        best.update(value=value, commit=git("rev-parse", "--short", "HEAD"))
                        best_path.write_text(json.dumps(best, indent=2))
                        row["decision"] = "kept"
                    else:
                        revert(files)
                        row["decision"] = "rejected"
            append_log(row)
            rows.append(row)
            if TRACKER:
                TRACKER.log(row, best)
            print(f"iter {iteration}: {row['decision']} {row.get('value', '')} {change}")
        else:
            reason = "goal reached" if reached(best["value"], cfg["goal"], cfg["direction"]) else "max_iters"
    except KeyboardInterrupt:
        reason, clean = "interrupted (Ctrl+C)", False
    except BaseException as error:  # notify on any crash, then re-raise below
        reason, clean = f"crashed: {error}", False
        finish(cfg, best, rows, reason, started, final_test=False)
        raise
    finish(cfg, best, rows, reason, started, final_test=clean)
    return 0 if clean else 130


if __name__ == "__main__":
    sys.exit(main())

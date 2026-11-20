#!/usr/bin/env python3
"""One git worktree per research idea; only a short summary returns to main.

    ar_tree.py new <slug> --question "..."     # worktree + branch + Herdr tab
    ar_tree.py list [--json]
    ar_tree.py summary <slug>                  # create/print the summary template path
    ar_tree.py close <slug> dead|parked|win [--yes]
    ar_tree.py bury <slug> --question "..." --paths p1 p2 [--yes]   # clean old main

Destructive commands are dry runs unless --yes is given.
"""

import argparse
from contextlib import contextmanager
from datetime import date, datetime
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

REGISTRY = "__board__/ideas.md"
SUMMARIES = "__board__/ideas"
COLUMNS = ["slug", "status", "question", "branch", "base", "worktree", "tab", "pane", "created", "closed", "agent"]
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,47}$")
REQUIRED = ["## Question", "## Approach", "## Main results", "## Why it failed", "## Don't retry unless"]
AGENT_LINKS = {".claude", ".agents", ".codex", "AGENTS.md"}  # ar_init links, not results
SKIP_ARCHIVE = {"__pycache__", ".pytest_cache", ".venv", ".ipynb_checkpoints", ".DS_Store"}
ARCHIVE = Path(os.environ.get("AR_ARCHIVE", Path.home() / "ar_archive"))
NEO_INIT = Path(__file__).resolve().parents[3] / "ar_init"
_AGENTS = importlib.util.spec_from_file_location("agents", Path(__file__).resolve().parents[2] / "references/agents.py")
AGENTS = importlib.util.module_from_spec(_AGENTS)
_AGENTS.loader.exec_module(AGENTS)


def link_shared(tree, root):
    """Give a new worktree the same shared agent links as the main checkout (ar_init).
    Claude's local settings point at the main checkout's board, so approvals are shared per project."""
    if not NEO_INIT.exists():
        return []
    loader = importlib.machinery.SourceFileLoader("ar_init", str(NEO_INIT))
    spec = importlib.util.spec_from_loader("ar_init", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    log = module.link_agents(tree, settings_target=root / "__board__/claude/settings.local.json")
    module.git_exclude(tree, False, log)
    return log

SUMMARY_TEMPLATE = """# Idea: {slug}

**Status**: {status} | **Closed**: {today} | **Archive**: tag `archive/{slug}` | **Raw results**: `{archive}`

## Question

{question}

## Approach

[2-4 lines: the mechanism tried and the concrete code/config change.]

## Setup

[Data/splits, baseline, metric, seeds, budget actually used.]

## Main results

| Run | Comparison | Metric | Result |
|---|---|---|---|

## Why it failed

[Evidence-backed reason, or "Did not fail" for win/parked.]

## Don't retry unless

[Conditions that would make this worth revisiting.]

## Reusable pieces

[Code or findings worth recovering from the archive tag, with paths.]
"""


def git(*args, cwd, check=True):
    result = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True)
    if check and result.returncode:
        raise SystemExit(f"git {' '.join(args)} failed:\n{result.stderr.strip()}")
    return result.stdout.strip()


def main_root(cwd="."):
    """The primary checkout, even when called from inside an idea worktree."""
    first = git("worktree", "list", "--porcelain", cwd=cwd).splitlines()[0]
    return Path(first.split(" ", 1)[1])


@contextmanager
def registry_lock(root):
    """Serialize registry/main-checkout changes when several agents run ar_tree at once."""
    import fcntl
    common = (root / git("rev-parse", "--git-common-dir", cwd=root)).resolve()
    with open(common / "ar_tree.lock", "w") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def read_rows(root):
    path = root / REGISTRY
    if not path.exists():
        return []
    rows = []
    for line in path.read_text().splitlines()[2:]:
        if line.startswith("| ") and not line.startswith("|---"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            rows.append(dict(zip(COLUMNS, cells + [""] * (len(COLUMNS) - len(cells)))))
    return rows


def write_rows(root, rows):
    path = root / REGISTRY
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["| " + " | ".join(COLUMNS) + " |", "|" + "---|" * len(COLUMNS)]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(c, "")).replace("|", "/") for c in COLUMNS) + " |")
    header = "# Ideas\n\nManaged by `ar_tree`. One row per idea; summaries live in `__board__/ideas/<slug>.md`.\n\n"
    path.write_text(header + "\n".join(lines) + "\n")


def find(rows, slug):
    for row in rows:
        if row["slug"] == slug:
            return row
    raise SystemExit(f"No idea '{slug}' in {REGISTRY}")


def herdr(*args):
    """Run a Herdr CLI command; return parsed JSON or None when Herdr is unavailable."""
    if not shutil.which("herdr"):
        return None
    result = subprocess.run(["herdr", *args], text=True, capture_output=True)
    if result.returncode:
        print(f"herdr {' '.join(args)}: {result.stderr.strip()}", file=sys.stderr)
        return None
    try:
        return json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return {}


def cmd_new(args):
    if not SLUG.match(args.slug):
        raise SystemExit("Slug must be lowercase letters, digits and hyphens (e.g. spectral-warmstart).")
    root = main_root()
    rows = read_rows(root)
    if any(r["slug"] == args.slug for r in rows):
        raise SystemExit(f"Idea '{args.slug}' already exists.")
    tree = root.parent / f"{root.name}.ideas" / args.slug
    branch = f"idea/{args.slug}"
    base_sha = git("rev-parse", "--short", args.base, cwd=root)
    git("worktree", "add", str(tree), "-b", branch, args.base, cwd=root)
    brief = tree / "__board__/IDEA.md"
    brief.parent.mkdir(parents=True, exist_ok=True)
    brief.write_text(f"# Idea: {args.slug}\n\n**Question**: {args.question}\n\n**Branch**: `{branch}` from `{args.base}` @ {base_sha}\n"
                     f"\nWork only inside this worktree. When done, the mate or human runs `ar_tree close {args.slug} ...`.\n")
    git("add", "__board__/IDEA.md", cwd=tree)
    git("commit", "-q", "-m", f"idea: start {args.slug}", cwd=tree)
    link_shared(tree, root)
    row = dict(slug=args.slug, status="active", question=args.question, branch=branch, base=f"{args.base}@{base_sha}",
               worktree=str(tree), tab="", pane="", created=date.today().isoformat(), closed="", agent=args.agent)
    if not args.no_herdr:
        created = herdr("tab", "create", "--cwd", str(tree), "--label", f"{root.name}:{args.slug}", "--no-focus")
        if created:
            row["tab"] = created.get("result", {}).get("tab", {}).get("tab_id", "")
            row["pane"] = created.get("result", {}).get("root_pane", {}).get("pane_id", "")
            env = args.env or os.environ.get("CONDA_DEFAULT_ENV", "")
            prompt = f"Read __board__/IDEA.md and __board__/ideas/ in the main checkout ({root}) before planning."
            launch = shlex.join([*AGENTS.spec(args.agent)["interactive"], prompt])
            if env:
                launch = f"conda activate {shlex.quote(env)} && {launch}"
            if row["pane"]:
                herdr("pane", "run", row["pane"], launch)
    rows.append(row)
    write_rows(root, rows)
    print(json.dumps({"created": row}, indent=2))


def cmd_list(args):
    rows = read_rows(main_root())
    if args.json:
        print(json.dumps(rows, indent=2))
        return
    for row in rows:
        print(f"{row['slug']:<28} {row['status']:<8} {row['question']}")


def summary_path(root, slug):
    return root / SUMMARIES / f"{slug}.md"


def ensure_summary(root, row, status):
    path = summary_path(root, row["slug"])
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        archive = ARCHIVE / root.name / row["slug"]
        path.write_text(SUMMARY_TEMPLATE.format(slug=row["slug"], status=status, today=date.today().isoformat(),
                                                question=row["question"], archive=archive))
    return path


def cmd_summary(args):
    root = main_root()
    row = find(read_rows(root), args.slug)
    print(ensure_summary(root, row, args.status))


def summary_problems(path):
    text = path.read_text() if path.exists() else ""
    missing = [h for h in REQUIRED if h not in text]
    if "[2-4 lines" in text or "| Run | Comparison" in text and text.count("\n|") < 3:
        missing.append("unfilled template")
    return missing


def ignored_paths(tree):
    """Untracked, git-ignored files and folders (raw results) that would vanish with the worktree."""
    out = git("ls-files", "--others", "--ignored", "--exclude-standard", "--directory", cwd=tree)
    return [p.rstrip("/") for p in out.splitlines() if p and not set(Path(p).parts) & SKIP_ARCHIVE
            and Path(p).parts[0] not in AGENT_LINKS and not p.startswith("__board__/claude")]


def unique(path):
    """Never merge into an existing archive (same slug reused, or two projects with one name)."""
    return path if not path.exists() else path.with_name(f"{path.name}-{datetime.now():%Y%m%dT%H%M%S}")


def archive_ignored(tree, dest, paths):  # used by bury
    for relative in paths:
        source = tree / relative
        if source.is_symlink():
            continue
        target = dest / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))


def require_on_base(root, base):
    current = git("rev-parse", "--abbrev-ref", "HEAD", cwd=root)
    if current != base:
        raise SystemExit(f"Main checkout {root} is on '{current}'; check out '{base}' first so the summary lands there.")


IDEA_ONLY = ("__board__/IDEA.md", "__board__/STATUS.md", "__board__/goal")  # never merged into main


def idea_only(path):
    return any(path == p or path.startswith(p + "/") for p in IDEA_ONLY)


def win_preview(root, base, branch):
    """Files a win brings to main (code, configs, plans, reports, notes) and likely conflicts."""
    out = git("diff", "--name-only", "--no-renames", f"{base}...{branch}", cwd=root)
    files = [f for f in out.splitlines() if f and not idea_only(f)]
    fork = git("merge-base", base, branch, cwd=root)
    changed_on_main = set(git("diff", "--name-only", fork, base, cwd=root).splitlines())
    return files, sorted(changed_on_main & set(files))


def squash_merge(root, branch):
    """Stage the idea branch on main (real merge, so later main changes are kept); stop on conflicts."""
    dirty = [l for l in git("status", "--porcelain", "--untracked-files=no", cwd=root).splitlines()
             if not l[3:].startswith(("__board__/ideas.md", "__board__/ideas/"))]  # our own registry edits
    if dirty:
        raise SystemExit(f"Main checkout {root} has uncommitted changes; commit or stash them before a win.")
    merged = subprocess.run(["git", "merge", "--squash", branch], cwd=root, text=True, capture_output=True)
    if merged.returncode:
        conflicts = git("diff", "--name-only", "--diff-filter=U", cwd=root, check=False)
        git("reset", "-q", "--merge", cwd=root, check=False)
        raise SystemExit(f"Merge conflicts, nothing changed on main:\n{conflicts or merged.stderr.strip()}\n"
                         f"In the idea worktree run `git merge {git('rev-parse', '--abbrev-ref', 'HEAD', cwd=root)}`, "
                         "resolve, commit, then rerun close.")
    for path in IDEA_ONLY:  # idea bookkeeping stays with the idea; main keeps its own versions
        if git("ls-tree", "HEAD", "--", path, cwd=root):
            git("restore", "--source=HEAD", "--staged", "--worktree", "--", path, cwd=root, check=False)
        else:
            git("rm", "-r", "-q", "--cached", "--ignore-unmatch", "--", path, cwd=root, check=False)
            target = root / path
            if target.is_dir():
                shutil.rmtree(target)
            elif target.exists():
                target.unlink()


def move_raw(tree, paths, archive, main=None):
    """Git-ignored results: into main at the same path for a win (when free), else to the archive."""
    for relative in paths:
        source = tree / relative
        if source.is_symlink() or not source.exists():
            continue
        target = main / relative if main and not (main / relative).exists() else archive / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))


def cmd_close(args):
    root = main_root()
    rows = read_rows(root)
    row = find(rows, args.slug)
    if row["status"] not in {"active", "parked"}:
        raise SystemExit(f"Idea '{args.slug}' is already {row['status']}.")
    base = row["base"].split("@")[0] or "main"
    tree = Path(row["worktree"]) if row["worktree"] else None
    has_tree = bool(tree and tree.exists())
    if has_tree and git("status", "--porcelain", cwd=tree):
        raise SystemExit(f"{tree} has uncommitted changes; commit or discard them first.")
    win = args.verdict == "win"
    summary = ensure_summary(root, row, args.verdict)
    problems = summary_problems(summary)
    raw = ignored_paths(tree) if has_tree else []
    dest = unique(ARCHIVE / root.name / args.slug)
    files, overlap = win_preview(root, base, row["branch"]) if win else ([], [])
    plan = {
        "verdict": args.verdict,
        "tag": f"archive/{args.slug} -> {row['branch']}",
        "summary": str(summary),
        "summary_problems": problems,
        "merge_to_main": {"files": files, "also_changed_on_main": overlap,
                          "kept_with_idea": list(IDEA_ONLY)} if win else None,
        "raw_results": ({"to_main_same_path": raw, "else_to": str(dest)} if win else {"to": str(dest), "paths": raw}) if raw else None,
        "remove_worktree": str(tree) if has_tree else None,
        "delete_branch": args.verdict != "parked",
    }
    if problems or not args.yes:
        plan["status"] = "fill the summary, then rerun with --yes" if problems else "dry run; rerun with --yes"
        print(json.dumps(plan, indent=2))
        return 1 if problems and args.yes else 0
    require_on_base(root, base)
    if win:
        squash_merge(root, row["branch"])  # raises before anything else changes
    if not git("tag", "--list", f"archive/{args.slug}", cwd=root):
        git("tag", f"archive/{args.slug}", row["branch"], cwd=root)
    if raw:
        move_raw(tree, raw, dest, main=root if win else None)
    tab = row["tab"]
    row.update(status={"dead": "dead", "parked": "parked", "win": "merged"}[args.verdict],
               closed=date.today().isoformat(), worktree="", tab="", pane="")
    write_rows(root, rows)
    paths = [str(summary.relative_to(root)), REGISTRY]
    git("add", "--", *paths, cwd=root)
    message = f"ideas: close {args.slug} ({args.verdict})"
    if win:
        git("commit", "-q", "-m", f"{message}\n\nSquash-merged {row['branch']}: code, configs, plans and reports.", cwd=root)
    else:
        git("commit", "-q", "-m", message, "--", *paths, cwd=root)
    # Only after main has the commit: remove the worktree, tab and branch.
    if has_tree:
        removed = subprocess.run(["git", "worktree", "remove", str(tree)], cwd=root, text=True, capture_output=True)
        if removed.returncode:
            plan["warning"] = f"committed but worktree not removed: {removed.stderr.strip()}"
    if tab:
        herdr("tab", "close", tab)
    if args.verdict != "parked" and "warning" not in plan:
        git("branch", "-D", row["branch"], cwd=root)
    plan["status"] = "done"
    plan["backup_tag"] = f"git push origin archive/{args.slug}"
    print(json.dumps(plan, indent=2))
    return 0


def cmd_bury(args):
    """Summarize and remove an old experiment already on main; its code stays reachable via the tag."""
    root = main_root()
    rows = read_rows(root)
    if not SLUG.match(args.slug) or any(r["slug"] == args.slug for r in rows):
        raise SystemExit(f"Use a new, valid slug (got '{args.slug}').")
    base = git("rev-parse", "--abbrev-ref", "HEAD", cwd=root)
    row = dict(slug=args.slug, status="buried", question=args.question, branch="", base=f"{base}@{git('rev-parse', '--short', 'HEAD', cwd=root)}",
               worktree="", tab="", pane="", created="", closed=date.today().isoformat())
    summary = ensure_summary(root, row, "buried")
    tracked = git("ls-files", "--", *args.paths, cwd=root).splitlines()
    raw = [p for p in git("ls-files", "--others", "--ignored", "--exclude-standard", "--directory", "--", *args.paths, cwd=root).splitlines()
           if p and not set(Path(p.rstrip("/")).parts) & SKIP_ARCHIVE]
    dest = unique(ARCHIVE / root.name / args.slug)
    plan = {"tag": f"archive/{args.slug} -> HEAD", "summary": str(summary), "summary_problems": summary_problems(summary),
            "git_rm_tracked_files": len(tracked), "move_ignored_to": str(dest) if raw else None, "ignored_paths": raw}
    if plan["summary_problems"] or not args.yes:
        plan["status"] = "fill the summary, then rerun with --yes" if plan["summary_problems"] else "dry run; rerun with --yes"
        print(json.dumps(plan, indent=2))
        return 0
    if git("status", "--porcelain", "--", *args.paths, cwd=root):
        raise SystemExit("The paths to bury have uncommitted changes; commit or discard them first.")
    git("tag", f"archive/{args.slug}", "HEAD", cwd=root)
    archive_ignored(root, dest, [p.rstrip("/") for p in raw])
    if tracked:
        git("rm", "-r", "-q", "--", *args.paths, cwd=root)
    rows.append(row)
    write_rows(root, rows)
    git("add", "--", str(summary.relative_to(root)), REGISTRY, cwd=root)
    git("commit", "-q", "-m", f"ideas: bury {args.slug}", cwd=root)
    plan["status"] = "done"
    print(json.dumps(plan, indent=2))
    return 0


def parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)
    new = sub.add_parser("new")
    new.add_argument("slug")
    new.add_argument("--question", required=True)
    new.add_argument("--base", default="main")
    new.add_argument("--agent", default=AGENTS.DEFAULT, help="Agent started in the idea's Herdr tab: claude, codex, ... (default $AR_AGENT or claude)")
    new.add_argument("--env", help="Conda env to activate in the tab (default: current CONDA_DEFAULT_ENV)")
    new.add_argument("--no-herdr", action="store_true")
    lst = sub.add_parser("list")
    lst.add_argument("--json", action="store_true")
    summ = sub.add_parser("summary")
    summ.add_argument("slug")
    summ.add_argument("--status", default="dead")
    close = sub.add_parser("close")
    close.add_argument("slug")
    close.add_argument("verdict", choices=["dead", "parked", "win"])
    close.add_argument("--yes", action="store_true")
    bury = sub.add_parser("bury")
    bury.add_argument("slug")
    bury.add_argument("--question", required=True)
    bury.add_argument("--paths", nargs="+", required=True)
    bury.add_argument("--yes", action="store_true")
    return p


def main():
    args = parser().parse_args()
    handler = {"new": cmd_new, "list": cmd_list, "summary": cmd_summary, "close": cmd_close, "bury": cmd_bury}[args.command]
    if args.command in {"new", "close", "bury"}:
        with registry_lock(main_root()):
            return handler(args) or 0
    return handler(args) or 0


if __name__ == "__main__":
    sys.exit(main())

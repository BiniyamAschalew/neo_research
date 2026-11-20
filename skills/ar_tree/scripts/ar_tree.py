#!/usr/bin/env python3
"""Three tiers of research code. If main is the paper, branches are its method sections and
worktrees are candidate ideas inside a section.

    main            refined, paper-worthy code
    b<i>/<name>     long-lived git branch = one general direction (b1/ensembles, b2/context-compression)
    idea/<slug>     short-lived exploration branch, checked out as a worktree

    ar_tree.py new <slug> --question "..." [--from main|b2|<name>]  # exploration worktree + Herdr tab
    ar_tree.py close <slug> dead|parked [--yes]          # failed exploration: only its summary reaches main
    ar_tree.py branch <slug> [--yes]                     # it works: compacted, reviewed code joins its parent branch
    ar_tree.py branch <slug> --new <name> [--yes]        #   ... or starts the next branch b<i>/<name> (rare)
    ar_tree.py open b2                                    # worktree on a branch (compaction, review)
    ar_tree.py merge b2 [--yes]                           # best, compacted, reviewed version of a branch -> main
    ar_tree.py drop b2 [--yes]                            # branch abandoned: summary to main, archived as a tag
    ar_tree.py list [--json] | tracker | summary <slug> | bury <slug> --question "..." --paths ...

branch and merge (the ar_branch / ar_merge skills) require __board__/COMPACTION.md (compaction step) and an accepting cross-agent
__board__/REVIEW.md (review step), both newer than any code change. __board__/TRACKER.md on main
always shows every branch and worktree. Destructive commands are dry runs unless --yes is given.
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
COLUMNS = ["slug", "status", "question", "branch", "base", "worktree", "tab", "pane", "created", "closed", "agent", "kind"]
BRANCHES = "__board__/branches"
TRACKER = "__board__/TRACKER.md"
REGISTRY_FILES = [REGISTRY, TRACKER]
BRANCH_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+){0,2}$")  # general direction: 1-3 words
MAX_BRANCHES = int(os.environ.get("AR_MAX_BRANCHES", "4"))
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,47}$")
REQUIRED = ["## Question", "## Approach", "## Main results", "## Why it failed", "## Don't retry unless"]
AGENT_LINKS = {".claude", ".agents", ".codex", "AGENTS.md"}  # ar_init links, not results
SKIP_ARCHIVE = {"__pycache__", ".pytest_cache", ".venv", ".ipynb_checkpoints", ".DS_Store"}
ARCHIVE = Path(os.environ.get("AR_ARCHIVE", Path.home() / "ar_archive"))
NEO_INIT = Path(__file__).resolve().parents[3] / "ar_init"
_SLACK = importlib.util.spec_from_file_location("slack_notify", Path(__file__).resolve().parents[2] / "ar_notify/scripts/slack_notify.py")
SLACK = importlib.util.module_from_spec(_SLACK)
_SLACK.loader.exec_module(SLACK)
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
    module.link_assets(tree, main_root=root, log=log)  # same datasets/checkpoints as the main checkout
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
            if cells[0] == "slug":  # the table header
                continue
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
    write_tracker(root, rows)


def is_branch(row):
    return (row.get("kind") or "idea") in {"branch", "direction"}


def phase(row):
    tree = Path(row["worktree"]) if row["worktree"] else None
    status = tree / "__board__/STATUS.md" if tree else None
    if status and status.exists():
        found = re.search(r"\*\*Current Phase\*\*:\s*(.+)", status.read_text())
        if found:
            return found.group(1).strip()
    return ""


def write_tracker(root, rows):
    """Main's map of the research: every branch, the worktrees inside it, and what has been closed."""
    main = git("symbolic-ref", "--short", "-q", "HEAD", cwd=root, check=False) or "main"
    open_ideas = [r for r in rows if not is_branch(r) and r["status"] in {"active", "parked"}]
    branches = [r for r in rows if is_branch(r)]
    lines = ["# Tracker", "", "Generated by `ar_tree` on every change; do not edit. Main = the paper, branches = its",
             "method sections, worktrees = candidate ideas inside a section.", "",
             f"## `{main}` (paper)", ""]
    merged = [b for b in branches if b["status"].startswith(("merged", "graduated"))]
    lines += [f"- merged: `{b['branch']}` ({b['closed']})" for b in merged] or ["- no branch merged yet"]

    def ideas_from(base):
        out = []
        for r in open_ideas:
            if r["base"].split("@")[0] == base:
                extra = ", ".join(x for x in (r["agent"], phase(r), r["status"] if r["status"] != "active" else "") if x)
                out.append(f"  - worktree `{r['branch']}`: {r['question']}" + (f" ({extra})" if extra else ""))
        return out

    from_main = ideas_from(main)
    lines += (["- candidate ideas started from main:"] + from_main) if from_main else []
    active = [b for b in branches if b["status"] == "active"]
    lines += ["", f"## Branches ({len(active)} active, limit {MAX_BRANCHES})", ""]
    for b in active:
        promoted = [r["slug"] for r in rows if r["status"] in {f"branched:{b['branch']}", f"promoted:{b['branch']}"}]
        lines.append(f"- `{b['branch']}`: {b['question']}" + (f" (open at `{b['worktree']}`)" if b["worktree"] else ""))
        lines.append(f"  - ideas in it: {', '.join(promoted) or 'none'}")
        lines += ideas_from(b["branch"])
    closed = [b for b in branches if b["status"] != "active"]
    if closed:
        lines += ["", "## Closed branches", ""] + [f"- `{b['branch']}`: {b['status']} ({b['closed']})" for b in closed]
    dead = [r for r in rows if not is_branch(r) and r["status"] in {"dead", "buried"}]
    lines += ["", "## Closed explorations", "", f"- {len(dead)} closed: see `__board__/ideas/`" +
              (f" (latest: {', '.join(r['slug'] for r in dead[-5:])})" if dead else "")]
    (root / TRACKER).write_text("\n".join(lines) + "\n")


def find(rows, slug):
    for row in rows:
        if row["slug"] == slug:
            return row
    raise SystemExit(f"No idea '{slug}' in {REGISTRY}")


def agent_command(name):
    """Interactive agent for an idea/branch tab, with the same "approve for me" permissions as the mate."""
    agent = AGENTS.spec(name)
    return [*agent["interactive"], *agent.get("mate", [])]


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
    args.base = args.base or git("symbolic-ref", "--short", "HEAD", cwd=root)  # the main checkout's branch
    if not branch_exists(root, args.base) and (found := find_branch(rows, args.base)):
        args.base = found["branch"]  # --from b2 / <name>: a candidate idea inside that branch
    if subprocess.run(["git", "rev-parse", "--verify", "-q", args.base], cwd=root, capture_output=True).returncode:
        raise SystemExit(f"'{args.base}' has no commits yet; commit the project's code once (keep data/results ignored), then retry.")
    base_sha = git("rev-parse", "--short", args.base, cwd=root)
    git("worktree", "add", str(tree), "-b", branch, args.base, cwd=root)
    brief = tree / "__board__/IDEA.md"
    brief.parent.mkdir(parents=True, exist_ok=True)
    brief.write_text(f"# Idea: {args.slug}\n\n**Question**: {args.question}\n\n**Branch**: `{branch}` from `{args.base}` @ {base_sha}\n"
                     f"\nAn exploration: work only inside this worktree. It ends as `ar_tree close {args.slug} dead|parked` "
                     f"(summary only) or, when it works, through ar_branch into its parent branch.\n")
    git("add", "__board__/IDEA.md", cwd=tree)
    git("commit", "-q", "-m", f"idea: start {args.slug}", cwd=tree)
    link_shared(tree, root)
    row = dict(slug=args.slug, status="active", question=args.question, branch=branch, base=f"{args.base}@{base_sha}",
               worktree=str(tree), tab="", pane="", created=date.today().isoformat(), closed="", agent=args.agent,
               kind="idea")
    if not args.no_herdr:
        created = herdr("tab", "create", "--cwd", str(tree), "--label", f"{root.name}:{args.slug}", "--no-focus")
        if created:
            row["tab"] = created.get("result", {}).get("tab", {}).get("tab_id", "")
            row["pane"] = created.get("result", {}).get("root_pane", {}).get("pane_id", "")
            prompt = f"Read __board__/IDEA.md and __board__/ideas/ in the main checkout ({root}) before planning."
            launch = shlex.join([*agent_command(args.agent), prompt])
            activate = f"conda activate {shlex.quote(args.env)}" if args.env else SLACK.activation(SLACK.load_keys(SLACK.env_file(root)), interactive=True)
            if activate:
                launch = f"{activate} && {launch}"
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
        kind = row.get("kind") or "idea"
        print(f"{kind:<10} {row['slug']:<26} {row['status']:<22} {row['branch'] or '-':<28} {row['question']}")


def summary_path(root, slug, kind="idea"):
    return root / (BRANCHES if kind in {"branch", "direction"} else SUMMARIES) / f"{slug}.md"


def ensure_summary(root, row, status):
    kind = row.get("kind") or "idea"
    path = summary_path(root, row["slug"], kind)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        archive = ARCHIVE / root.name / row["slug"]
        text = SUMMARY_TEMPLATE.format(slug=row["slug"], status=status, today=date.today().isoformat(),
                                       question=row["question"], archive=archive)
        if kind in {"branch", "direction"}:
            text = text.replace("# Idea:", "# Branch:").replace(f"`archive/{row['slug']}`", f"`archive/{row['slug']}`")
            text = text.replace("## Approach\n\n[2-4 lines: the mechanism tried and the concrete code/config change.]",
                                "## Approach\n\n[The branch's general direction and the ideas that built it (slugs).]")
        path.write_text(text)
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


IDEA_ONLY = ("__board__/IDEA.md", "__board__/STATUS.md", "__board__/goal",  # per-tier bookkeeping:
             "__board__/COMPACTION.md", "__board__/compaction",             # never merged upward
             "__board__/REVIEW.md")


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
    """Stage `branch` in the checkout `root` (real merge, so later changes there are kept); stop on conflicts."""
    status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=root, text=True,
                            capture_output=True, check=True).stdout  # unstripped: porcelain columns matter
    dirty = [l for l in status.splitlines()
             if not l[3:].startswith(("__board__/ideas.md", "__board__/ideas/", "__board__/branches/", TRACKER))]  # registry edits
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


def find_branch(rows, name, active=True):
    """b2, b2/ensembles or ensembles -> the branch row."""
    for row in rows:
        if not is_branch(row) or (active and row["status"] != "active"):
            continue
        number, _, short = row["branch"].partition("/")
        if name in {row["branch"], number, short, row["slug"]}:
            return row
    return None


def next_branch(root, rows, name):
    """b<i>/<name> with i one above every branch number ever used (rows, branches, archive tags)."""
    if not BRANCH_NAME.match(name):
        raise SystemExit(f"Branch name '{name}' must be a general direction in 1-3 lowercase words "
                         "(e.g. ensembles, context-compression), not a specific idea.")
    refs = git("for-each-ref", "--format=%(refname:short)", "refs/heads/", "refs/tags/archive/", cwd=root).splitlines()
    names = [r["branch"] for r in rows] + refs
    used = [int(m.group(1)) for n in names if (m := re.search(r"(?:^|/)b(\d+)[/-]", n))]
    return f"b{max(used, default=0) + 1}/{name}"


def branch_exists(root, branch):
    return subprocess.run(["git", "rev-parse", "--verify", "-q", f"refs/heads/{branch}"], cwd=root,
                          capture_output=True).returncode == 0


def compaction_problem(root, base, branch):
    """None when __board__/COMPACTION.md was committed after every code change on branch since base."""
    fork = git("merge-base", base, branch, cwd=root)
    code = git("log", "-1", "--format=%H", f"{fork}..{branch}", "--", ".", ":(exclude)__board__", cwd=root)
    if not code:
        return None
    note = git("log", "-1", "--format=%H", f"{fork}..{branch}", "--", "__board__/COMPACTION.md", cwd=root)
    if not note:
        return "no __board__/COMPACTION.md on this branch: run the compaction step first"
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", code, note], cwd=root).returncode == 0
    return None if ancestor else "code changed after the last COMPACTION.md: rerun the compaction step"


def review_problem(root, base, branch, author):
    """None when the last round of __board__/REVIEW.md accepts, comes from another agent family than the
    author, and was committed after every code change and after COMPACTION.md."""
    fork = git("merge-base", base, branch, cwd=root)
    note = git("log", "-1", "--format=%H", f"{fork}..{branch}", "--", "__board__/REVIEW.md", cwd=root)
    if not note:
        return "no __board__/REVIEW.md: run the cross-agent review step first"
    later = git("log", "-1", "--format=%H", f"{fork}..{branch}", "--", ".", ":(exclude)__board__",
                cwd=root) or None
    compaction = git("log", "-1", "--format=%H", f"{fork}..{branch}", "--", "__board__/COMPACTION.md", cwd=root) or None
    for commit in (later, compaction):
        if commit and subprocess.run(["git", "merge-base", "--is-ancestor", commit, note], cwd=root).returncode:
            return "code or COMPACTION.md changed after the last review: run another review round"
    text = git("show", f"{branch}:__board__/REVIEW.md", cwd=root)
    last = text.split("\n## Round ")[-1]
    human = re.search(r"\*\*Human decision\*\*:\s*(accept|reject)", last, re.I)
    if human:
        return None if human.group(1).lower() == "accept" else "the human rejected it in REVIEW.md"
    reviewer = re.search(r"reviewer:\s*([\w.-]+)", last)
    if reviewer and author and reviewer.group(1) == author:
        return f"the reviewer ({reviewer.group(1)}) is the author's own agent; review with another agent family"
    if not re.search(r"\*\*Verdict\*\*:\s*ACCEPT", last):
        return "the last review round did not ACCEPT: answer the findings and run another round (or a human decision)"
    return None


def check_tree(row):
    """Board-only leftovers (plans, reports, notes an agent forgot to commit) are committed automatically;
    uncommitted code is refused, because only the human or the idea agent can judge it."""
    tree = Path(row["worktree"]) if row["worktree"] else None
    has_tree = bool(tree and tree.exists())
    if not has_tree:
        return tree, has_tree
    status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=tree, text=True,
                            capture_output=True, check=True).stdout
    paths = [line[3:].split(" -> ")[-1].strip('"') for line in status.splitlines() if line.strip()]
    code = [p for p in paths if not p.startswith("__board__/")]
    if code:
        raise SystemExit(f"{tree} has uncommitted code ({', '.join(code[:5])}); commit or discard it first.")
    if paths:
        git("add", "-A", "--", "__board__", cwd=tree)
        git("commit", "-q", "-m", "board: commit plans/reports/notes before leaving the worktree", cwd=tree)
    return tree, has_tree


def report(plan, problems, yes):
    """Print the plan; return True when the caller should act."""
    if problems or not yes:
        plan["status"] = ("fix: " + "; ".join(problems)) if problems else "dry run; rerun with --yes"
        print(json.dumps(plan, indent=2))
        return False
    return True


def retire(root, row, tree, has_tree, delete_branch, plan):
    """After the commit: remove worktree, tab and (optionally) branch."""
    if has_tree:
        removed = subprocess.run(["git", "worktree", "remove", str(tree)], cwd=root, text=True, capture_output=True)
        if removed.returncode:
            plan["warning"] = f"committed but worktree not removed: {removed.stderr.strip()}"
    if row["tab"]:
        herdr("tab", "close", row["tab"])
    if delete_branch and "warning" not in plan:
        git("branch", "-D", row["branch"], cwd=root)


def commit_board(root, paths, message):
    git("add", "--", *paths, cwd=root)
    git("commit", "-q", "-m", message, "--", *paths, cwd=root)


def cmd_close(args):
    """Failed or paused exploration: only the summary returns to main."""
    root = main_root()
    rows = read_rows(root)
    row = find(rows, args.slug)
    if row["status"] not in {"active", "parked"}:
        raise SystemExit(f"Idea '{args.slug}' is already {row['status']}.")
    tree, has_tree = check_tree(row)
    summary = ensure_summary(root, row, args.verdict)
    raw = ignored_paths(tree) if has_tree else []
    dest = unique(ARCHIVE / root.name / args.slug)
    plan = {"verdict": args.verdict, "tag": f"archive/{args.slug} -> {row['branch']}", "summary": str(summary),
            "raw_results_to": str(dest) if raw else None, "remove_worktree": str(tree) if has_tree else None,
            "delete_branch": args.verdict != "parked"}
    if not report(plan, summary_problems(summary), args.yes):
        return 1 if summary_problems(summary) and args.yes else 0
    if not git("tag", "--list", f"archive/{args.slug}", cwd=root):
        git("tag", f"archive/{args.slug}", row["branch"], cwd=root)
    if raw:
        move_raw(tree, raw, dest)
    tab = row["tab"]
    row.update(status=args.verdict, closed=date.today().isoformat(), worktree="", tab="", pane="")
    write_rows(root, rows)
    commit_board(root, [str(summary.relative_to(root)), *REGISTRY_FILES], f"ideas: close {args.slug} ({args.verdict})")
    retire(root, {**row, "tab": tab}, tree, has_tree, args.verdict != "parked", plan)
    plan["status"] = "done"
    print(json.dumps(plan, indent=2))
    return 0


def merge_into_branch(root, target, source, message):
    """Squash-merge source into branch target through a temporary worktree (or target's open worktree)."""
    rows = read_rows(root)
    opened = next((Path(r["worktree"]) for r in rows if r["branch"] == target and r["worktree"]), None)
    checkout = opened if opened and opened.exists() else root.parent / f"{root.name}.ideas" / f".merge-{target.replace('/', '-')}"
    temporary = checkout != opened
    if temporary:
        git("worktree", "add", "-q", str(checkout), target, cwd=root)
    try:
        squash_merge(checkout, source)
        git("commit", "-q", "--allow-empty", "-m", message, cwd=checkout)
    finally:
        if temporary:
            subprocess.run(["git", "worktree", "remove", "--force", str(checkout)], cwd=root, capture_output=True)
    return opened if not temporary else None


def cmd_branch(args):
    """A working idea joins its parent branch (or, rarely, starts the next one), after compaction and review."""
    if args.into and args.new:
        raise SystemExit("Give at most one of --into <branch> or --new <name>.")
    root = main_root()
    rows = read_rows(root)
    row = find(rows, args.slug)
    if row["status"] != "active" or is_branch(row):
        raise SystemExit(f"'{args.slug}' is not an active idea.")
    tree, has_tree = check_tree(row)
    base = row["base"].split("@")[0]
    problems = []
    active = [r for r in rows if is_branch(r) and r["status"] == "active"]
    if not args.into and not args.new:  # default: the branch this idea was started from
        if not find_branch(rows, base):
            raise SystemExit(f"'{args.slug}' started from {base}, not from a branch: give --into <branch> "
                             f"(active: {', '.join(r['branch'] for r in active) or 'none'}) or --new <name>.")
        args.into = base
    if args.into:
        existing = find_branch(rows, args.into)
        if existing is None:
            raise SystemExit(f"No active branch '{args.into}'. Active: {', '.join(r['branch'] for r in active) or 'none'}")
        target = existing["branch"]
    else:
        target = next_branch(root, rows, args.new)
        if len(active) >= MAX_BRANCHES and not args.force_new:
            problems.append(f"{len(active)} branches already active ({', '.join(r['branch'] for r in active)}); "
                            "branch --into one of them, merge or drop one first, or --force-new")
        elif active:
            print(f"Consider --into an existing branch first: {', '.join(r['branch'] + ' (' + r['question'] + ')' for r in active)}")
    if not args.skip_compaction and (problem := compaction_problem(root, base, row["branch"])):
        problems.append(problem)
    if not args.skip_review and (problem := review_problem(root, base, row["branch"], row["agent"])):
        problems.append(problem)
    summary = ensure_summary(root, row, f"branched into {target}")
    problems += summary_problems(summary)
    raw = ignored_paths(tree) if has_tree else []
    plan = {"branch": f"{row['branch']} -> {target}" + (f" (new branch from {base})" if args.new else ""),
            "kept_out": list(IDEA_ONLY), "summary": str(summary), "tag": f"archive/{args.slug}",
            "raw_results_to": str(unique(ARCHIVE / root.name / args.slug)) if raw else None}
    if not report(plan, problems, args.yes):
        return 1 if problems and args.yes else 0
    if args.new:
        git("branch", target, base, cwd=root)
    try:
        opened = merge_into_branch(root, target, row["branch"], f"ar_branch: {args.slug} into {target}")
    except SystemExit:
        if args.new:
            git("branch", "-D", target, cwd=root)
        raise
    git("tag", f"archive/{args.slug}", row["branch"], cwd=root)
    if raw:
        move_raw(tree, raw, unique(ARCHIVE / root.name / args.slug), main=opened)
    tab = row["tab"]
    row.update(status=f"branched:{target}", closed=date.today().isoformat(), worktree="", tab="", pane="")
    if args.new:
        rows.append(dict(slug=target.replace("/", "-"), status="active", question=args.question or row["question"],
                         branch=target, base=f"{base}@{git('rev-parse', '--short', base, cwd=root)}", worktree="",
                         tab="", pane="", created=date.today().isoformat(), closed="", agent=row["agent"], kind="branch"))
    write_rows(root, rows)
    commit_board(root, [str(summary.relative_to(root)), *REGISTRY_FILES], f"ideas: {args.slug} branched into {target}")
    retire(root, {**row, "tab": tab}, tree, has_tree, True, plan)
    plan["status"] = "done"
    print(json.dumps(plan, indent=2))
    return 0


def cmd_open(args):
    """Worktree on a branch, for compaction and review before ar_merge, or direct work."""
    root = main_root()
    rows = read_rows(root)
    row = find_branch(rows, args.branch)
    if row is None or not branch_exists(root, row["branch"]):
        raise SystemExit(f"No active branch '{args.branch}'.")
    target = row["branch"]
    tree = root.parent / f"{root.name}.branches" / row["slug"]
    if not tree.exists():
        git("worktree", "add", "-q", str(tree), target, cwd=root)
        link_shared(tree, root)
    row["worktree"] = str(tree)
    if not args.no_herdr and not row["tab"]:
        created = herdr("tab", "create", "--cwd", str(tree), "--label", f"{root.name}:{row['slug']}", "--no-focus")
        if created:
            row["tab"] = created.get("result", {}).get("tab", {}).get("tab_id", "")
            row["pane"] = created.get("result", {}).get("root_pane", {}).get("pane_id", "")
            if row["pane"]:
                herdr("pane", "run", row["pane"], shlex.join(agent_command(args.agent)))
    write_rows(root, rows)
    print(json.dumps({"opened": str(tree), "branch": target}, indent=2))
    return 0


def branch_row(rows, name):
    row = find_branch(rows, name)
    if row is None:
        raise SystemExit(f"No active branch '{name}'.")
    return row


def cmd_merge(args):
    """The refined branch joins main: squash merge after compaction and review, as one commit."""
    root = main_root()
    rows = read_rows(root)
    row = branch_row(rows, args.branch)
    tree, has_tree = check_tree(row)
    main_branch = git("symbolic-ref", "--short", "HEAD", cwd=root)
    problems = []
    if not args.skip_compaction and (problem := compaction_problem(root, main_branch, row["branch"])):
        problems.append(problem)
    if not args.skip_review and (problem := review_problem(root, main_branch, row["branch"], row["agent"])):
        problems.append(problem)
    summary = ensure_summary(root, row, f"merged into {main_branch}")
    problems += summary_problems(summary)
    files, overlap = win_preview(root, main_branch, row["branch"])
    raw = ignored_paths(tree) if has_tree else []
    plan = {"merge": f"{row['branch']} -> {main_branch}", "files": files, "also_changed_on_main": overlap,
            "kept_out": list(IDEA_ONLY), "summary": str(summary), "tag": f"archive/{row['slug']}",
            "raw_results_to_main": raw, "delete_branch": not args.keep}
    if not report(plan, problems, args.yes):
        return 1 if problems and args.yes else 0
    squash_merge(root, row["branch"])
    git("tag", f"archive/{row['slug']}", row["branch"], cwd=root)
    if raw:
        move_raw(tree, raw, unique(ARCHIVE / root.name / row['slug']), main=root)
    tab = row["tab"]
    row.update(status=f"merged:{main_branch}", closed=date.today().isoformat(), worktree="", tab="", pane="")
    write_rows(root, rows)
    git("add", "--", str(summary.relative_to(root)), *REGISTRY_FILES, cwd=root)
    git("commit", "-q", "-m", f"ar_merge: {row['branch']} into {main_branch}\n\nSquash-merged the compacted, reviewed branch.", cwd=root)
    retire(root, {**row, "tab": tab}, tree, has_tree, not args.keep, plan)
    plan["status"] = "done"
    print(json.dumps(plan, indent=2))
    return 0


def cmd_drop(args):
    """An abandoned branch: summary to main, kept only as a tag."""
    root = main_root()
    rows = read_rows(root)
    row = branch_row(rows, args.branch)
    tree, has_tree = check_tree(row)
    summary = ensure_summary(root, row, "dropped")
    raw = ignored_paths(tree) if has_tree else []
    dest = unique(ARCHIVE / root.name / row['slug'])
    plan = {"drop": row["branch"], "tag": f"archive/{row['slug']}", "summary": str(summary),
            "raw_results_to": str(dest) if raw else None}
    problems = summary_problems(summary)
    if not report(plan, problems, args.yes):
        return 1 if problems and args.yes else 0
    git("tag", f"archive/{row['slug']}", row["branch"], cwd=root)
    if raw:
        move_raw(tree, raw, dest)
    tab = row["tab"]
    row.update(status="dropped", closed=date.today().isoformat(), worktree="", tab="", pane="")
    write_rows(root, rows)
    commit_board(root, [str(summary.relative_to(root)), *REGISTRY_FILES], f"branches: drop {row['branch']}")
    retire(root, {**row, "tab": tab}, tree, has_tree, True, plan)
    plan["status"] = "done"
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
    git("add", "--", str(summary.relative_to(root)), *REGISTRY_FILES, cwd=root)
    git("commit", "-q", "-m", f"ideas: bury {args.slug}", cwd=root)
    plan["status"] = "done"
    print(json.dumps(plan, indent=2))
    return 0


def cmd_tracker(args):
    root = main_root()
    write_tracker(root, read_rows(root))
    print((root / TRACKER).read_text())


def parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)
    new = sub.add_parser("new", help="start an exploration worktree")
    new.add_argument("slug")
    new.add_argument("--question", required=True)
    new.add_argument("--from", "--base", dest="base", help="main (default: the main checkout's branch) or a branch: b2, b2/<name> or <name>")
    new.add_argument("--agent", default=AGENTS.DEFAULT, help="Agent started in the idea's Herdr tab: claude, codex, ... (default $AR_AGENT or claude)")
    new.add_argument("--env", help="Conda env for the tab (default: CONDA_ENV / ENV_ACTIVATE in __board__/project.env)")
    new.add_argument("--no-herdr", action="store_true")
    lst = sub.add_parser("list")
    lst.add_argument("--json", action="store_true")
    sub.add_parser("tracker", help="regenerate and print __board__/TRACKER.md")
    summ = sub.add_parser("summary")
    summ.add_argument("slug")
    summ.add_argument("--status", default="dead")
    close = sub.add_parser("close", help="end a failed or paused exploration (summary only)")
    close.add_argument("slug")
    close.add_argument("verdict", choices=["dead", "parked"])
    close.add_argument("--yes", action="store_true")
    branch = sub.add_parser("branch", help="compacted, reviewed idea -> its parent branch (ar_branch)")
    branch.add_argument("slug")
    branch.add_argument("--into", help="another existing branch: b2, b2/<name> or <name> (default: the idea's parent branch)")
    branch.add_argument("--new", help="start the next branch b<i>/<name>; <name> = a general direction (1-3 words)")
    branch.add_argument("--question", help="one-line description of a new branch's direction (default: the idea's question)")
    branch.add_argument("--force-new", action="store_true", help=f"allow more than {MAX_BRANCHES} active branches (human only)")
    branch.add_argument("--skip-compaction", action="store_true", help="human override of the compaction gate")
    branch.add_argument("--skip-review", action="store_true", help="human override of the cross-agent review gate")
    branch.add_argument("--yes", action="store_true")
    opener = sub.add_parser("open", help="worktree on a branch")
    opener.add_argument("branch")
    opener.add_argument("--agent", default=AGENTS.DEFAULT)
    opener.add_argument("--no-herdr", action="store_true")
    grad = sub.add_parser("merge", help="compacted, reviewed branch -> main (ar_merge)")
    grad.add_argument("branch")
    grad.add_argument("--keep", action="store_true", help="keep the branch after merging")
    grad.add_argument("--skip-compaction", action="store_true", help="human override of the compaction gate")
    grad.add_argument("--skip-review", action="store_true", help="human override of the cross-agent review gate")
    grad.add_argument("--yes", action="store_true")
    drop = sub.add_parser("drop", help="abandon a branch (summary only)")
    drop.add_argument("branch")
    drop.add_argument("--yes", action="store_true")
    bury = sub.add_parser("bury", help="summarize and remove an old experiment already on main")
    bury.add_argument("slug")
    bury.add_argument("--question", required=True)
    bury.add_argument("--paths", nargs="+", required=True)
    bury.add_argument("--yes", action="store_true")
    return p


def main():
    args = parser().parse_args()
    handler = {"new": cmd_new, "list": cmd_list, "summary": cmd_summary, "close": cmd_close, "bury": cmd_bury,
               "branch": cmd_branch, "open": cmd_open, "merge": cmd_merge, "drop": cmd_drop,
               "tracker": cmd_tracker}[args.command]
    if args.command in {"new", "close", "bury", "branch", "open", "merge", "drop", "tracker"}:
        with registry_lock(main_root()):
            return handler(args) or 0
    return handler(args) or 0


if __name__ == "__main__":
    sys.exit(main())

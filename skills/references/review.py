#!/usr/bin/env python3
"""Cross-agent review round for ar_branch (idea -> branch) and ar_merge (branch -> main).

    python .agents/skills/references/review.py branch [--reviewer codex]
    python .agents/skills/references/review.py merge

Runs the other agent family read-only on this worktree, appends its critique as a new round
to __board__/REVIEW.md, and prints the verdict (ACCEPT | REVISE | REJECT). The author answers
each round under "### Author response" in REVIEW.md (fixing code or arguing back), commits, and
runs the next round until ACCEPT or the round limit; then the human decides.
"""

import argparse
from datetime import datetime
import importlib.util
from pathlib import Path
import re
import shlex
import subprocess
import sys

HERE = Path(__file__).resolve()
SKILLS = HERE.parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AGENTS = load("agents", SKILLS / "references/agents.py")
TREE = load("ar_tree", SKILLS / "ar_tree/scripts/ar_tree.py")
REVIEW = Path("__board__/REVIEW.md")
VERDICT = re.compile(r"VERDICT:\s*(ACCEPT|REVISE|REJECT)", re.I)
MAX_ROUNDS = 3

QUESTIONS = {
    "branch": "Should this candidate idea become part of the branch {target} (a method section)?",
    "merge": "Should this branch (a method section) become part of {target}, the paper-quality branch?",
}

PROMPT = """You are an independent reviewer ({reviewer}) of research work written by another agent ({author}).
You are read-only: inspect files and git, do not edit anything.

Decision: {question}
Worktree: {tree} (branch {branch}, base {base}). See `git diff --stat {base}...HEAD` and `git diff {base}...HEAD`.
Read directly: the reports under __board__/reports/, __board__/COMPACTION.md, structure.md,
skills/references/code-style.md in .agents/, and the previous rounds in {review} (respond to the author's replies).

Judge, citing files, numbers and lines:
1. Evidence: do the reported numbers exist in the raw artifacts, and do they support the claim at the stated scope?
2. Comparison: fair, equally tuned baselines; seeds and datasets sufficient; no test-set selection or leakage.
3. Compaction: is parity credible (same experiment, seeds, metrics before/after)? Anything kept that the result does not need?
4. Code: reuse, entity layout, hierarchical configs, no per-version copies, readable enough to debug without an agent.
5. Fit: does it belong in {target} rather than another branch, and is anything missing to make it ready?

Answer with numbered findings marked [blocking] or [minor], then a final line exactly:
VERDICT: ACCEPT | REVISE | REJECT
ACCEPT only if there are no blocking findings.
"""


def git(*args):
    return subprocess.run(["git", *args], text=True, capture_output=True, check=True).stdout.strip()


def registry_row():
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    root = TREE.main_root()
    return root, next((r for r in TREE.read_rows(root) if r["branch"] == branch), None)


def rounds(text):
    return len(re.findall(r"^## Round \d+", text, re.M))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["branch", "merge"])
    parser.add_argument("--target", help="Branch it moves into (default: main for merge, the parent branch for branch)")
    parser.add_argument("--reviewer", help="Reviewer agent (default: a different family than the author)")
    parser.add_argument("--author", help="Author agent (default: from the ideas registry)")
    parser.add_argument("--max-rounds", type=int, default=MAX_ROUNDS)
    parser.add_argument("--timeout-min", type=int, default=30)
    args = parser.parse_args()
    root, row = registry_row()
    author = args.author or (row or {}).get("agent") or AGENTS.DEFAULT
    reviewer = args.reviewer or AGENTS.other(author)
    if not reviewer or reviewer == author:
        raise SystemExit(f"No reviewer from another agent family than '{author}' is installed; pass --reviewer, "
                         "or ask the human to review and record it in __board__/REVIEW.md.")
    command = AGENTS.spec(reviewer)["review"]
    if not command:
        raise SystemExit(f"No read-only review command known for '{reviewer}'.")
    text = REVIEW.read_text() if REVIEW.exists() else "# Review\n\nCross-agent review for ar_branch / ar_merge.\n"
    done = rounds(text)
    if done >= args.max_rounds:
        raise SystemExit(f"{done} rounds already; the human decides now (record the decision in {REVIEW}).")
    base = (row or {}).get("base", "").split("@")[0] or "main"
    target = args.target or ("main" if args.stage == "merge" else (base if re.match(r"b\d+/", base) else "a new branch"))
    head = git("rev-parse", "--short", "HEAD")
    prompt = PROMPT.format(reviewer=reviewer, author=author, question=QUESTIONS[args.stage].format(target=target),
                           tree=Path.cwd(), branch=git("rev-parse", "--abbrev-ref", "HEAD"), base=base,
                           review=REVIEW, target=target)
    try:
        result = subprocess.run([*command, prompt], text=True, capture_output=True, timeout=args.timeout_min * 60)
        response = (result.stdout or result.stderr).strip()
    except subprocess.TimeoutExpired:
        response = f"(review timed out after {args.timeout_min} min)\nVERDICT: REVISE"
    found = VERDICT.findall(response)
    verdict = found[-1].upper() if found else "REVISE"
    REVIEW.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    REVIEW.write_text(text.rstrip() + f"\n\n## Round {done + 1} | stage: {args.stage} | reviewer: {reviewer} | "
                      f"author: {author} | commit: {head} | {stamp}\n\n{response}\n\n**Verdict**: {verdict}\n\n"
                      "### Author response\n\n[Reply to each blocking finding: fixed (commit) or why not.]\n")
    print(f"Round {done + 1}: {verdict} (reviewer {reviewer}). Answer in {REVIEW}, commit, "
          + ("then run ar_tree branch / merge." if verdict == "ACCEPT" else "then run the next round."))
    return 0


if __name__ == "__main__":
    sys.exit(main())

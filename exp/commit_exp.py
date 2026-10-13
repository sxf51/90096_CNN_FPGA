#!/usr/bin/env python3
"""Commit only this task's paths after checking protected files and file sizes."""
import subprocess
import sys
import re
from run_exp import ROOT, ARCH_ID, EXPERIMENT_ID, check_protected, lock
from compact_archive import compact

OWNED = ("exp/", "designs/", "experiments/", "docs/0002-overnight-experiments.md",
         "docs/0003-architecture-exploration.md", "docs/0004-t8-weight-loading-plan.md",
         "docs/0005-rom-clock-t4-plan.md")


def commit():
    if len(sys.argv) < 2 or not re.fullmatch(EXPERIMENT_ID, sys.argv[1]):
        raise SystemExit("Usage: python3 exp/commit_exp.py E000|S01|G01|P01|W01|C01|F01 [message]")
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    expected = "exp/explore-arch" if re.fullmatch(ARCH_ID, sys.argv[1]) else "exp/overnight-1011"
    if branch != expected:
        raise SystemExit("Wrong branch")
    check_protected()
    for archive in (ROOT / "experiments").glob(sys.argv[1] + "_*"):
        compact(archive)
    subprocess.run(["git", "status", "--short", "--branch"], cwd=ROOT, check=True)
    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only", "-z"], cwd=ROOT).decode().split("\0")
    if any(p and not p.startswith(OWNED) for p in staged):
        raise SystemExit("Unrelated files already staged; refuse to change their staging")
    tracked = subprocess.check_output(["git", "diff", "--name-only", "-z"], cwd=ROOT).decode().split("\0")
    new = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    paths = sorted({p for p in tracked + new if p and p.startswith(OWNED)})
    for p in paths + [p for p in staged if p]:
        path = ROOT / p
        if path.name.lower() in {"agents.md", "agent.md"}:
            raise SystemExit("Local rules must never be staged")
        if path.is_file() and path.stat().st_size > 50_000_000:
            raise SystemExit("File exceeds 50 MB; manual decision required: " + p)
    if paths:
        subprocess.run(["git", "add", "--", *paths], cwd=ROOT, check=True)
    if not subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT).strip():
        print("No task changes to commit")
        return
    # Vendor reports/logs retain original whitespace; CSV uses standard CRLF.
    subprocess.run(["git", "diff", "--cached", "--check", "--", "exp/", "designs/",
                    ":(exclude)designs/golden_auto/", ":(glob,exclude)exp/tb/replay_*/root/**"], cwd=ROOT, check=True)
    subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", " ".join(sys.argv[1:])], cwd=ROOT, check=True)


if __name__ == "__main__":
    with lock(ROOT / "workspace/exp_runs/.commit.lock", wait_timeout=120):
        commit()

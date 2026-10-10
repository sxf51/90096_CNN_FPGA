#!/usr/bin/env python3
"""Commit only this task's paths after checking protected files and file sizes."""
import subprocess
import sys
from run_exp import ROOT, check_protected

OWNED = ("exp/", "designs/", "experiments/", "docs/0002-overnight-experiments.md")


def main():
    if len(sys.argv) < 2 or not sys.argv[1].startswith("E"):
        raise SystemExit("Usage: python3 exp/commit_exp.py E000 [message]")
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    if branch != "exp/overnight-1011":
        raise SystemExit("Wrong branch")
    check_protected()
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
    # Vendor reports/logs retain original whitespace; CSV uses standard CRLF.
    subprocess.run(["git", "diff", "--cached", "--check", "--", "exp/", "designs/",
                    ":(exclude)designs/golden_auto/"], cwd=ROOT, check=True)
    subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", " ".join(sys.argv[1:])], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""**What would you lose if this disk died right now?**

RS-1. **Awareness, never enforcement** — it exits 0 whatever it finds, and no
gate consults it. A lane mid-experiment is doing exactly what [L-18] permits;
the point is that a session should not *end* without somebody having decided
whether the work on disk is temporary or worth keeping.

### The measurement it exists for

Surveyed on 2026-08-03, minutes after cycle 34 was promoted:

    Signora-QE      lane-qe                    0 dirty   0 untracked   0 unpushed
    Signora-LaneB   lane-b-commercial-profile  17        4             0
    LaneA           lane-a-product-surface     4         3             0

**Every branch on the machine was pushed.** The entire exposure was pre-commit:
seven untracked paths across two lanes — Playwright page objects, an endurance
suite, an interaction-boundaries spec. Not scratch files. **Hours of work git
had never seen**, in exactly one physical location.

### Why there is no disposability taxonomy here

**`.gitignore` already is one, and it is the one the repository maintains.**
Caches, `node_modules`, `.venv`, `.env` and build output never appear in
`git status --porcelain`, so anything this reports is, by the repository's own
declaration, **not** disposable. A second classifier would be a second truth
about the same question, and the copy nobody maintained would be this one.

**What is added is emphasis, not classification**: a lost prompt release or
evaluation dataset costs more than a lost scratch script, so those are named
first — see `WORTH_MORE`.

    python3 infra/unsaved.py                # this working copy
    python3 infra/unsaved.py --workstation  # every Signora clone on this machine

**`--workstation` is how the exposure above was found**, and it is read-only:
it runs `git status` in sibling clones and reports. It never writes, never
stages, and never touches another lane's work — surfacing somebody else's
unsaved work is a finding to hand them, not a thing to fix (`CLAUDE.md` §20e).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Final

REPO_ROOT: Final = Path(__file__).resolve().parent.parent

#: Paths whose loss costs more than the diff suggests. **Emphasis, not
#: classification** — everything reported is already non-disposable, and this
#: only decides what a reader sees first.
#:
#: Prompt releases, evaluation datasets and scenarios are *versioned artifacts*
#: (REPOSITORY_RESILIENCE.md §2): they record what was true at a moment and
#: cannot be regenerated, because regenerating one produces a different artifact
#: rather than the same one back.
WORTH_MORE: Final = (
    ("prompt or release artifact", ("/prompts/", "/evaluation/")),
    ("scenario or dataset", ("/datasets/", "/scenarios/", "/simulation/")),
    ("architecture or register", ("docs/architecture/", "docs/BUGS", "docs/LANE_COORD")),
    ("test suite", ("/tests/",)),
)


def _git(*args: str, cwd: Path) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    ).stdout.rstrip("\n")


def _emphasis(path: str) -> str:
    for label, markers in WORTH_MORE:
        if any(marker in f"/{path}" for marker in markers):
            return label
    return ""


def _unpushed(cwd: Path) -> int:
    """Commits on this branch that no remote has.

    **Reported separately from uncommitted work because the remedy differs**: a
    push, not a commit. It was zero everywhere in the survey, and that is worth
    continuing to confirm rather than assuming — the day it is not, the loss is
    finished work rather than work in progress.
    """
    counted = _git("rev-list", "--count", "@{u}..HEAD", cwd=cwd)
    return int(counted) if counted.isdigit() else 0


def survey(cwd: Path) -> tuple[list[str], list[str], int, str]:
    """Untracked paths, modified paths, unpushed commits, branch."""
    branch = _git("rev-parse", "--abbrev-ref", "HEAD", cwd=cwd)
    untracked, modified = [], []
    # **`-uall`, and the reason is that this tool's own author got it wrong.**
    # `git status --porcelain` collapses an untracked *directory* into one line,
    # so the first survey counted a whole untracked module as a single path and
    # reported "seven untracked paths" across the workstation. The real figure
    # was **27**, including a prompt release and an evaluation dataset — the
    # precise artifacts R-3 says can never be regenerated to recover them.
    # A tool that under-reports the exposure it exists to surface is worse than
    # no tool, because the number is believed.
    for line in _git("status", "--porcelain", "-uall", cwd=cwd).splitlines():
        status, _, path = line[:2], line[2:3], line[3:]
        (untracked if status == "??" else modified).append(path)
    return untracked, modified, _unpushed(cwd), branch


def _report(cwd: Path, label: str) -> bool:
    """One working copy. Returns whether anything is at risk.

    **The commit age is printed, and it is not decoration.** The first
    workstation survey reported 819 modified files in an old clone — a stale
    checkout carrying GitHub workflow files removed from the repository months
    ago, not a day's unsaved work. Without the age beside it, the loudest row in
    the report is the one that matters least, and a report whose largest number
    is noise teaches people to skim it.
    """
    untracked, modified, unpushed, branch = survey(cwd)
    age = _git("log", "-1", "--format=%cr", cwd=cwd) or "no commits"
    if not (untracked or modified or unpushed):
        print(f"  ✓  {label:<28} {branch:<32} nothing unsaved")
        return False

    print(f"\n  {label}  ({branch}, last commit {age})\n")
    if untracked:
        print(f"    {len(untracked)} untracked — git has never seen these:")
        for path in untracked[:10]:
            note = _emphasis(path)
            print(f"      {path}{f'   ← {note}' if note else ''}")
        if len(untracked) > 10:
            print(f"      … and {len(untracked) - 10} more")
    if modified:
        print(f"\n    {len(modified)} modified — the changes exist only here:")
        for path in modified[:6]:
            note = _emphasis(path)
            print(f"      {path}{f'   ← {note}' if note else ''}")
        if len(modified) > 6:
            print(f"      … and {len(modified) - 6} more")
    if unpushed:
        print(f"\n    {unpushed} commit(s) on `{branch}` that no remote has — a push, not a commit")
    return True


def _clones() -> list[tuple[Path, str]]:
    """Every Signora working copy beside this one, including nested ones.

    Nested deliberately: two of the clones found in the survey were one level
    down (`LaneA/signora-lane-a`, `Signora-Demo/Fortune_Signora`), and a survey
    that missed them would have reported a cleaner workstation than the real one.
    """
    projects = REPO_ROOT.parent
    found: list[tuple[Path, str]] = []
    for entry in sorted(projects.iterdir()):
        if not entry.is_dir():
            continue
        if (entry / ".git").exists():
            found.append((entry, entry.name))
            continue
        for nested in sorted(entry.iterdir()) if entry.is_dir() else []:
            if nested.is_dir() and (nested / ".git").exists():
                found.append((nested, f"{entry.name}/{nested.name}"))
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workstation", action="store_true", help="survey every Signora clone on this machine"
    )
    args = parser.parse_args()

    print("\n  Unsaved work — what a disk failure would cost right now\n")

    targets = _clones() if args.workstation else [(REPO_ROOT, REPO_ROOT.name)]
    at_risk = [label for path, label in targets if _report(path, label)]

    if not at_risk:
        print("\n  Everything is committed or pushed. Nothing to decide.\n")
        return 0

    print(
        "\n  **Nothing here is wrong.** A lane mid-experiment is doing exactly what"
        "\n  L-18 permits. The rule is only that a *session* should not end without"
        "\n  somebody having decided: temporary, or worth keeping?"
        "\n"
        "\n  Recoverable is enough — a WIP commit on your lane branch, pushed. Not"
        "\n  merged, not reviewed, not finished."
        "\n"
    )
    if args.workstation and len(at_risk) > 1:
        print(
            "  Work in another lane's clone is **that lane's to decide**. Surfacing it"
            "\n  is a finding to hand them, never a thing to fix for them.\n"
        )
    # **Always 0.** A check that failed would become a gate, and a gate here
    # would punish exactly the experimentation the law is written to allow.
    return 0


if __name__ == "__main__":
    sys.exit(main())

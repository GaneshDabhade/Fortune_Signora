#!/usr/bin/env python3
"""**One command answers *"is this environment ready?"***

TASK-410. **Five tools answer it today and nothing asks all five**, so the
answer lives in whichever ones a session happened to remember. This composes
them and reports **one verdict**.

### It composes; it re-implements nothing

Every check below is an **existing** tool, run as a subprocess exactly as a
human would run it. **None is imported, refactored or reimplemented**, so each
one remains independently runnable and this file cannot drift from them — a
second implementation of a check is the duplicated-truth defect `CLAUDE.md` §2
forbids, and the copy nobody maintains is the one that would decide.

### It repairs nothing, deliberately

`state-check.py` states the reason and it generalises: *"every inconsistency it
finds has more than one correct resolution — a stale dashboard might need
updating, or the promotion might not have finished — and choosing between them
is a governance decision, not a script's."*

**A doctor that fixed things would inherit that problem**, and it would fix the
convenient reading. `workstation.py` is therefore invoked as `--check`, which is
its own reporting mode, and **not one check here is given a repairing flag.**

### Blocking and advisory are different questions

**Blocking** — *you cannot work here until this is fixed.* **Advisory** — *the
repository is telling you something true that does not stop you.*

The split is **read from what the repository already says about each tool**, not
invented here: `state-check.py` is documented as advisory in `CLAUDE.md` §20e and
in its own header, and `event-catalog` is advisory in the `Makefile` *"because
its one finding today can only be cleared by editing a 🔴 file, so gating would
make every lane's run red for a reason no lane could act on — and the cost of
that is every other warning being skimmed."* **That is exactly the failure mode
a doctor is most prone to**, so the distinction is load-bearing rather than
cosmetic.

**A failing advisory is still printed, and still names what to run.**

### What it does not run, and says so

**`make validate` is not in the default run.** It creates a database, migrates
it and executes the suite — minutes, and it is a *gate*, not a readiness probe.
**A doctor nobody runs because it is slow has answered nothing.**

**But it is reported as `not run`, with the reason and the command** — never
omitted. A check absent from a report reads as a check that passed, which is
`missing_gates`' rule (ADR-0032) and the defect
`36-empty-array-checks.md` found nine times in shipped constraints. `--full`
includes it.

    python3 infra/doctor.py            # readiness
    python3 infra/doctor.py --full     # and the suite
    python3 infra/doctor.py --list     # what it would run, and run nothing

**Exit code is the verdict**: `0` ready, `1` a blocking check failed.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parent.parent


@dataclass(frozen=True, slots=True)
class Check:
    """One existing tool, and how to run it without changing anything."""

    name: str
    question: str
    #: Run from the repository root, exactly as a human would.
    command: tuple[str, ...]
    #: False means a failure is reported and does not change the verdict.
    blocking: bool
    #: **What to run when it fails.** A diagnostic that reports a failure
    #: without naming the next command has moved the search, not ended it.
    fix: str
    #: Excluded from the default run, with this reason. Reported as `not run`.
    skip_reason: str | None = None


CHECKS: Final = (
    Check(
        "workstation",
        "are the local environment files present, and do the key halves match?",
        ("python3", "infra/workstation.py", "--check"),
        blocking=True,
        fix=(
            "make workstation  — or nothing, if this clone runs no product. "
            "Lane C holds no ports, database or compose project (CLAUDE.md §20e), "
            "so this check failing on a Product Office clone is expected"
        ),
    ),
    Check(
        "environments",
        "does the environment allocation model agree with RUNNING.md?",
        ("python3", "infra/environments.py", "--check"),
        blocking=False,
        fix='make environments ARGS="--check"  — RUNNING.md is QE\'s to write',
    ),
    Check(
        "state-check",
        "do the governance documents agree with the repository?",
        ("python3", "infra/state-check.py"),
        blocking=False,
        fix="make state-check  — advisory by design; each finding has more than one correct resolution",
    ),
    Check(
        "reachability",
        "can a customer reach every screen that exists?",
        ("python3", "infra/reachability.py"),
        blocking=False,
        fix="make reachability",
    ),
    Check(
        "runtime-composition",
        "does the deployed worker consume what each module projects?",
        ("python3", "infra/runtime-composition.py"),
        blocking=False,
        fix="make runtime-composition",
    ),
    Check(
        "validate",
        "does the suite pass against a database this run creates?",
        ("make", "validate"),
        blocking=True,
        fix="make validate",
        skip_reason="minutes, and a gate rather than a readiness probe — use --full",
    ),
)


def run(check: Check) -> tuple[bool, str]:
    """Run one check. **Its output is captured and never interpreted** — this
    file reports whether a tool succeeded, and the tool remains the authority
    on why."""
    try:
        done = subprocess.run(
            check.command, cwd=ROOT, capture_output=True, text=True, timeout=900
        )
    except FileNotFoundError:
        return False, f"{check.command[0]}: not installed"
    except subprocess.TimeoutExpired:
        return False, "timed out after 900s"
    tail = (done.stdout + done.stderr).strip().splitlines()
    return done.returncode == 0, (tail[-1].strip() if tail else "")


def main() -> int:
    ap = argparse.ArgumentParser(description="Is this environment ready?")
    ap.add_argument("--full", action="store_true", help="include the checks skipped for time")
    ap.add_argument("--list", action="store_true", help="print what would run, and run nothing")
    args = ap.parse_args()

    if args.list:
        for c in CHECKS:
            when = "full only" if c.skip_reason and not args.full else "always"
            kind = "blocking" if c.blocking else "advisory"
            print(f"  {c.name:<21} {kind:<9} {when:<10} {' '.join(c.command)}")
        return 0

    print("\n  Signora — environment doctor\n")
    failed_blocking: list[Check] = []
    findings: list[Check] = []
    skipped: list[Check] = []

    for check in CHECKS:
        if check.skip_reason and not args.full:
            skipped.append(check)
            print(f"  ○ {check.name:<21} not run — {check.skip_reason}")
            continue
        ok, last = run(check)
        if ok:
            print(f"  ✓ {check.name:<21} {check.question}")
            continue
        (failed_blocking if check.blocking else findings).append(check)
        mark = "✗" if check.blocking else "!"
        print(f"  {mark} {check.name:<21} {last[:60]}")

    print()
    for check in failed_blocking + findings:
        label = "BLOCKING" if check.blocking else "advisory"
        print(f"  {label:<9} {check.name} — {check.fix}")

    # **Absence is stated, never allowed to read as a pass.** A verdict that
    # counted only what ran would be a stronger claim than the evidence
    # supports, which is precisely `missing_gates`.
    if skipped:
        print(f"\n  {len(skipped)} check(s) not run. --full runs them.")
    if findings:
        print(f"  {len(findings)} advisory finding(s). They do not block work.")

    if failed_blocking:
        # **The verdict names what it is a verdict about.** "NOT READY" alone
        # would misdiagnose a clone that is *correctly* unable to run the
        # product — Lane C holds no runtime by governance, and a diagnostic
        # that misreads that as a fault is the failure
        # `test_coverage_debt_reader.py` was written about.
        print(f"\n  NOT READY to run Signora here — {len(failed_blocking)} blocking check(s) failed.")
        print("  Governance and documentation work needs none of them.\n")
        return 1
    print("\n  READY to run Signora here" + (" (with advisories above)" if findings else "") + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

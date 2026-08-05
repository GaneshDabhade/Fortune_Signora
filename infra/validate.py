#!/usr/bin/env python3
"""**Stage 1 validation, against a database this run creates.**

*Repository Health · **Configuration Safety**.* The stage-1 sibling of RE-03.

**RE-03 gave `make certify` its own database and stopped there**, and stage 1 is
where QE spends most of its time. Validating a candidate means running the suite
against *that candidate's* schema — and a bare `pytest` resolves
`SIGNORA_TEST_APP_DATABASE_URL` from the shell, which on this workstation points
at a shared database carrying whichever lane migrated it last.

### Three times in one day, all QE's, and one nearly cost a lane

| | |
|---|---|
| **Lane B's first validation** | 27 failures, **13 of them Security Invariants** reading `icp_segment has no workspace_id column`. The migration creates one. **QE was one step from filing a fabricated tenancy defect** against the lane, and only checking their migration before writing the row stopped it |
| **Lane A's** | Ran clean by luck — the shared database happened to match |
| **QE's own gate change** | 26 failures against a database at `0036` while the branch was at `0037` |

> **A gate whose result depends on the shell it was launched from is not a gate**
> (`CLAUDE.md` §2 — *hidden inputs are architecture defects*). B-022 said so, RE-03
> removed it from certification, and **this removes it from the step before.**

### What it does

Creates `signora_validate_<commit>`, migrates it to **the working tree's** head,
runs the suite against it, and drops it in a `finally` — the same shape as
`tests/certification/database.py`, and deliberately not a second implementation
of it: this imports that module.

    python3 infra/validate.py                        # the suite, with coverage
    python3 infra/validate.py --quick                # no coverage — a first look
    python3 infra/validate.py -m security_invariant  # a subset, same safe database

**The third form was added on 2026-08-04, after QE made the very mistake this
file exists to prevent.** Checking one slice's claim about the Security
Invariant count, QE ran `pytest -m security_invariant` by hand — no disposable
database, straight at the shared one — and read **12 failures that were
entirely the invocation's**. The full suite had passed minutes earlier. **The
safe route existed only for the whole suite**, so any narrower question left it
([B-116](../docs/BUGS.md)).

**It is not a second certification.** It runs the suite, because that is the
gate that needs a database — plus two that need *nothing* and are here for the
opposite reason: they take seconds and were in no gate QE ran.

**`tsc --noEmit`**, added 2026-08-04. `main` reached a state where it failed a
check the Definition of Done requires of every lane
([B-111](../docs/BUGS.md)), and QE's own stage 1 could not have caught it.

**`vitest`**, added 2026-08-05. **1255 frontend tests were run by nobody**
([B-123](../docs/BUGS.md)) — a slice whose tests are entirely frontend passed
this command completely, and QE noticed only because the backend count had not
moved. One hand-run caught a real failure immediately.

**The admission rule this file already applies**, and both satisfy it: *needs
nothing, takes seconds, in no other gate.* `lint-imports` and `mypy` stay out
because they belong to certification, and the image build stays out because it
needs a Docker stack.

> **`smoke` cannot cover `vitest`** for the same reason it cannot cover `tsc`:
> `.dockerignore` excludes `tests/`, so the one gate that compiles the frontend
> never sees a test file.
>
> ⚠️ **This closes stage 1 and not certification.** `REQUIRED_GATES` is
> deliberately untouched: adding a seventh would make **every certification
> record ever written unsatisfied**, because none of them ran it — and
> versioning the requirement set changes what certification *means*
> (ADR-0032), which is not a coding session's to decide. **B-123 stays open
> for that half.**
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Final

REPO_ROOT: Final = Path(__file__).resolve().parent.parent
BACKEND: Final = REPO_ROOT / "backend"


def _disposable() -> object:
    """`tests/certification/database.py`, imported rather than reimplemented.

    **The provisioning logic already exists and is tested** — including that a
    failed run still drops its database, which is the property that stops one
    failure blocking every later run at the same commit. A second copy here
    would be the duplicated truth `CLAUDE.md` §2 forbids, and the copy nobody
    maintained would be this one.
    """
    sys.path.insert(0, str(BACKEND))
    from tests.certification import database

    return database


def _vitest_summary(output: str) -> str:
    """The counted line, or the honest admission that it could not be found.

    **Never `"clean"` unconditionally.** A reporter change that stopped printing
    the totals would leave this reporting success for a run it could not read —
    the silent no-op class ([B-125](../docs/BUGS.md)), and the reason the fallback
    names itself rather than guessing.
    """
    for line in output.splitlines():
        if "Tests" in line and "passed" in line:
            return line.strip()
    return "passed — no summary line found in the reporter's output"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="skip coverage")
    args, forwarded = parser.parse_known_args()

    database = _disposable()
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    name = database.name_for(commit).replace("certify", "validate")  # type: ignore[attr-defined]

    print(f"\n  Validating {commit[:12]} against a database this run creates\n")
    with database.disposable(name) as target:  # type: ignore[attr-defined]
        environment = {**os.environ, **target.environment, "SIGNORA_ALLOW_DESTRUCTIVE_TESTS": "1"}

        print(f"  1  migrate       {target.name}")
        migrated = subprocess.run(
            ["uv", "run", "alembic", "upgrade", "head"],
            cwd=BACKEND,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        if migrated.returncode:
            # **Before the suite, and fatal.** An unmigrated database fails
            # hundreds of tests for one reason, and that reason is the least
            # visible line in the output — which is exactly how three QE
            # validations produced misleading failure lists in one day.
            print(f"     FAILED\n\n{migrated.stdout}{migrated.stderr}")
            return 1
        print("     applied to head")

        # **Anything unrecognised goes to pytest**, so a *subset* has a safe
        # route too. Until 2026-08-04 only the whole suite did, and QE ran
        # `pytest -m security_invariant` by hand to check one slice's claim —
        # straight at the shared database, producing **12 failures that were
        # entirely the invocation's**. Caught only because a full green run
        # existed to compare against. Coverage is dropped for a subset: a
        # partial run cannot meet a whole-repository floor, and failing the
        # gate for that reason teaches people to pass `--quick` reflexively.
        command = ["uv", "run", "pytest", "-q", "-p", "no:randomly", *forwarded]
        if not args.quick and not forwarded:
            command.insert(3, "--cov")
        # **Before the suite: seconds, and it needs nothing.** A five-minute
        # suite that passes while the frontend does not compile is five minutes
        # spent measuring the wrong thing (B-111).
        print("  2  tsc --noEmit")
        typescript = subprocess.run(
            ["npx", "tsc", "--noEmit"],
            cwd=REPO_ROOT / "frontend",
            capture_output=True,
            text=True,
            check=False,
        )
        if typescript.returncode:
            print(f"     FAILED\n\n{typescript.stdout}{typescript.stderr}")
            return 1
        print("     clean")

        # **Also before the suite, and for the same reason as `tsc`.** Seconds,
        # no database, no stack — and until 2026-08-05 nothing ran it at all, so
        # a slice whose tests were entirely frontend passed this command
        # completely (B-123). Skipped for a subset run: `-m security_invariant`
        # is a question about the backend, and answering it with the whole
        # frontend suite is the padding that teaches people to pass `--quick`.
        if not forwarded:
            print("  3  vitest")
            frontend = subprocess.run(
                ["npx", "vitest", "run", "--reporter=dot"],
                cwd=REPO_ROOT / "frontend",
                capture_output=True,
                text=True,
                check=False,
            )
            if frontend.returncode:
                print(f"     FAILED\n\n{frontend.stdout}{frontend.stderr}")
                return 1
            print(f"     {_vitest_summary(frontend.stdout)}")

        measured = "--cov" in command
        scope = " ".join(forwarded) if forwarded else "the whole suite"
        step = "4" if not forwarded else "3"
        print(f"  {step}  suite         {scope}, {'with' if measured else 'without'} coverage\n")
        result = subprocess.run(command, cwd=BACKEND, env=environment, check=False)

    print(
        f"\n  {target.name} dropped."
        f"\n  {'PASSED' if result.returncode == 0 else 'FAILED'} — exit {result.returncode}\n"
    )
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())

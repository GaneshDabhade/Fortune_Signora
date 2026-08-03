#!/usr/bin/env python3
"""**One operation owns the shared environment at a time, and the second refuses.**

The repository has exactly one production stack, one set of review ports and one
test database. `certify`, `smoke`, `dr`, `up` and `down` all mutate them, and
until now **nothing knew who was using them.**

**RE-02 was written as *"a lock around `make certify`"*, and challenging it
showed that would not have prevented the incident it came from.** Cycle 25's
contaminated run happened because `make smoke` and `make down` ran *beside* a
certification — not because a second `certify` started. A certify-lock would
have permitted every command that actually did the damage.

**So the lease belongs to the environment, not to a command.** That is the
difference between *"missing capability"* and *"missing ownership"*: the
capability to run these gates was never absent, and nobody owned the thing they
share.

**Prevention rather than detection.** The preflight *detects* a held port and
tells the operator to look; this *refuses to start*. A second operation cannot
contaminate the first, because it never runs.

    python3 infra/environment-lease.py run certify -- make certify
    python3 infra/environment-lease.py status
    python3 infra/environment-lease.py release --force

Exit codes:

    0  the wrapped command's own exit code, or a successful status
    4  the environment is leased by another live operation
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

REPO_ROOT: Final = Path(__file__).resolve().parent.parent
LEASE: Final = REPO_ROOT / ".environment-lease"

#: Passed to the child so a gate that shells out to another gate does not
#: deadlock against itself. `certify` runs `smoke.sh` inside its own run, and
#: without this the second acquisition would block on the first forever.
LEASE_VARIABLE: Final = "SIGNORA_ENV_LEASE"


def _alive(pid: int) -> bool:
    """Whether the recorded holder still exists.

    **A killed run must not hold the environment forever.** `pkill` on a hung
    certification is a legitimate recovery action — it happened twice in cycle
    25 — and a lease that survived it would convert one stuck run into a
    permanently stuck repository.
    """
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # Owned by another user: it exists, and is not ours to judge.
        return True
    return True


def _read() -> dict[str, Any] | None:
    if not LEASE.exists():
        return None
    try:
        return json.loads(LEASE.read_text())
    except json.JSONDecodeError:
        # A partial write from a process killed mid-acquire. Treat as absent
        # rather than as a permanent block.
        return None


def holder() -> dict[str, Any] | None:
    """The live holder, if any. **A stale lease is reclaimed silently** — it
    describes a process that no longer exists, and reporting it as a conflict
    would send the operator hunting for something that already died."""
    current = _read()
    if current is None:
        return None
    if not _alive(int(current.get("pid", -1))):
        LEASE.unlink(missing_ok=True)
        return None
    return current


def _describe(current: dict[str, Any]) -> str:
    started = current.get("started_at", "?")
    return (
        f"    {current.get('label', '?')}  pid {current.get('pid', '?')}"
        f"  since {started}"
    )


def acquire(label: str) -> str:
    """Take the lease, or exit 4 naming who holds it."""
    current = holder()
    if current is not None:
        print("\n  BLOCKED — the environment is leased by another operation\n")
        print(_describe(current))
        print(
            "\n  A second operation would contaminate the first: they share one"
            "\n  production stack, one pair of review ports and one test database."
            "\n  That is how cycle 25 recorded `pytest 134 passed` against a suite"
            "\n  of 2589 — another run truncated its database mid-suite."
            "\n"
            "\n  Wait for it, or release it if you know it is dead:"
            "\n    python3 infra/environment-lease.py release --force"
        )
        raise SystemExit(4)
    identifier = uuid.uuid4().hex[:12]
    LEASE.write_text(
        json.dumps(
            {
                "id": identifier,
                "label": label,
                "pid": os.getpid(),
                "started_at": datetime.now(UTC).isoformat(timespec="seconds"),
            },
            sort_keys=True,
        )
    )
    return identifier


def release(identifier: str | None = None, *, force: bool = False) -> None:
    """Give the lease back. **Only the holder may**, unless forced."""
    current = _read()
    if current is None:
        return
    if force or identifier is None or current.get("id") == identifier:
        LEASE.unlink(missing_ok=True)


def run(label: str, command: list[str]) -> int:
    """Acquire, run, and **always** release.

    Re-entrant: a gate that shells out to another gate inherits the lease
    through the environment rather than deadlocking against itself.
    """
    inherited = os.environ.get(LEASE_VARIABLE)
    if inherited:
        return subprocess.run(command, cwd=REPO_ROOT, check=False).returncode

    identifier = acquire(label)
    environment = {**os.environ, LEASE_VARIABLE: identifier}

    def _hand_back(signum: int, _frame: object) -> None:
        release(identifier)
        raise SystemExit(128 + signum)

    previous = {
        number: signal.signal(number, _hand_back)
        for number in (signal.SIGINT, signal.SIGTERM)
    }
    try:
        return subprocess.run(command, cwd=REPO_ROOT, env=environment, check=False).returncode
    finally:
        for number, original in previous.items():
            signal.signal(number, original)
        release(identifier)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)

    runner = sub.add_parser("run", help="acquire, run a command, release")
    runner.add_argument("label")
    runner.add_argument("command", nargs=argparse.REMAINDER)

    sub.add_parser("status", help="who holds the environment")

    releaser = sub.add_parser("release", help="give the lease back")
    releaser.add_argument("--force", action="store_true")

    args = parser.parse_args()

    if args.action == "run":
        command = [part for part in args.command if part != "--"]
        if not command:
            parser.error("run needs a command after --")
        return run(args.label, command)

    if args.action == "release":
        release(force=args.force)
        print("  lease released" if args.force else "  lease cleared if it was yours")
        return 0

    current = holder()
    if current is None:
        print("\n  FREE — no operation holds the environment\n")
        return 0
    print("\n  LEASED\n")
    print(_describe(current))
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

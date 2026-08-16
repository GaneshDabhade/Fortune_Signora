#!/usr/bin/env python3
"""**One operation owns the shared environment at a time, and the second refuses.**

The **workstation** has exactly one production stack, one set of review ports and
one PostgreSQL server. `certify`, `smoke`, `dr`, `up` and `down` all mutate
them, and until now **nothing knew who was using them.**

**Workstation, not repository — corrected 2026-08-05, and the distinction is
[B-118](../docs/BUGS.md).** The lease lived at `REPO_ROOT/.environment-lease`,
so four clones held four leases over one Docker project and none could see
another's. It now lives beside the resource and is named for it, so every
checkout driving `signora-v2` computes the same path.

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
import re
import signal
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

REPO_ROOT: Final = Path(__file__).resolve().parent.parent

#: **The lease belongs to the contended resource, and the resource is not the
#: clone.** This was `REPO_ROOT / ".environment-lease"`, so every checkout held
#: its own and none could see another's — Lane A holding the environment was
#: invisible to QE *by construction*. [B-118](../docs/BUGS.md) is what that
#: cost: two runs of one commit, minutes apart, gave 40 failures and then 238,
#: with 21 deadlocks and 13 missing catalogs, because two clones were driving
#: one PostgreSQL server.
#:
#: **The module's own argument, applied once more.** It reasoned that a lease
#: belongs to the environment rather than to a command, because cycle 25 was
#: contaminated by `smoke` and `down` running *beside* a certification. The same
#: step says it belongs to the **workstation** rather than to the clone: the
#: contended object is one Docker project, and it does not become four because
#: four directories reference it. **It was correct when written. There was one
#: clone.**
#:
#: `XDG_RUNTIME_DIR` first because it is per-user, already exists, and is
#: cleaned on logout; `/tmp` is the portable fallback. **Never the home
#: directory** — a lease that survives a reboot is a lease that outlives the
#: containers it describes.
LEASE_DIR: Final = Path(
    os.environ.get("XDG_RUNTIME_DIR") or os.environ.get("TMPDIR") or "/tmp"
) / "signora-leases"


def _resource() -> str:
    """**What is actually shared**, and therefore what the lease is named for.

    The Docker Compose project: two containers of the same name in two projects
    are two containers; in one project they are one. Every clone pointing at
    `signora-v2` computes the same lease path and arbitrates correctly, and the
    day [436](../docs/architecture/436-execution-isolation.md) change ② lands,
    each project gets its own path with no edit here.

    **Overridable, because a lane must be able to say which stack it drives.**
    """
    return os.environ.get("COMPOSE_PROJECT_NAME") or _compose_project_from_file() or "signora-v2"


def _compose_project_from_file() -> str | None:
    """The `name:` line of the compose file, read rather than assumed.

    **Parsed with a regex rather than a YAML library on purpose:** PyYAML is not
    a declared dependency, adding one for six characters is a 🔴 that would need
    an ADR, and `tomllib` does not read YAML. One anchored line is enough, and
    an unreadable file falls back rather than crashing a gate.
    """
    compose = REPO_ROOT / "infra" / "docker-compose.yml"
    try:
        for line in compose.read_text().splitlines():
            if m := re.match(r"^name:\s*(\S+)\s*$", line):
                return _expand(m.group(1))
    except OSError:
        return None
    return None


def _expand(value: str) -> str | None:
    """`${VAR:-default}` as Compose reads it, or `None` if it resolves to nothing.

    ⛔ **[B-141](../docs/BUGS.md) / [483](../docs/architecture/483-environment-isolation-audit.md).**
    The compose file's line is `name: ${COMPOSE_PROJECT_NAME:-signora-v2}`.
    **Docker expands that; the regex above did not** — so every clone without
    the variable exported computed the *literal string* as its resource name,
    and they all computed the same one.

    ⚡ **The live lease file was named `${COMPOSE_PROJECT_NAME:-signora-v2}.lease`,
    character for character**, and QE held it while three separate stacks ran.
    **Two aborts this session, 270s and 120s, were that.**

    ⚠️ **The `"signora-v2"` fallback in `_resource()` was also unreachable**: this
    function returned a truthy literal, so the `or` chain never reached its
    third term. **A default nothing can take is not a default.**

    ⛔ **Deliberately not a general shell expander.** It reads the one form the
    compose file uses, and **returns `None` for anything else** so the caller
    falls back rather than inventing a name — `CLAUDE.md` §2's *build for the
    requirement in front of you*.
    """
    if not value.startswith("${"):
        return value or None
    m = re.fullmatch(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}", value)
    if m is None:
        return None
    return os.environ.get(m.group(1)) or m.group(2) or None


def _lease_path() -> Path:
    LEASE_DIR.mkdir(parents=True, exist_ok=True)
    return LEASE_DIR / f"{_resource()}.lease"


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
    lease = _lease_path()
    if not lease.exists():
        return None
    try:
        return json.loads(lease.read_text())
    except json.JSONDecodeError:
        # A partial write from a process killed mid-acquire. Treat as absent
        # rather than as a permanent block.
        return None


def _running_containers() -> list[str] | None:
    """The stack's containers that are up, or ``None`` if nothing can be asked.

    **[B-436](../docs/BUGS.md).** The pid was only ever a *proxy* for the
    question the lease actually asks — *is this stack busy?* This asks the
    stack.

    ⛔ **``None`` and ``[]`` are different answers and must not be collapsed.**
    ``[]`` is *"docker answered, and nothing is running"*; ``None`` is *"nobody
    answered"*. A helper returning ``[]`` for both would turn "I could not tell"
    into "it is free", which is the whole defect this exists to remove.
    """
    project = _compose_project_from_file()
    if project is None:
        return None
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"label=com.docker.compose.project={project}",
             "--format", "{{.Names}}"],
            capture_output=True, text=True, timeout=10, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        # ⚡ No docker on this workstation means no compose stack on it either,
        # so there is nothing a second run could contaminate. Distinct from
        # docker answering with an error, which is handled below.
        return None
    if result.returncode != 0:
        return None
    return [name for name in result.stdout.split() if name]


def holder() -> dict[str, Any] | None:
    """The live holder, if any.

    ## 🔴 A dead pid is evidence about the RECORD, not about the MACHINE — B-436

    **This used to reclaim silently on a dead pid**, and its reasoning was
    sound for the case it was written for: a crashed run leaving a lock nobody
    can clear. ⛔ **It was wrong for the case QE hit** — the recorded pid was
    dead *and* another clone had a live run the record never knew about. **A
    plain retry of ``make dr`` would have reclaimed and run, with no force, no
    prompt and no ``BLOCKED`` message.** QE judged that a dead pid did not prove
    the machine was free and declined to force; this function would have done it
    for them, without the judgement.

    ✅ **So a dead pid now asks the stack before reclaiming.** The fix is
    deliberately neither *never reclaim* nor *always reclaim* — B-436 records
    that both failure modes are real — but a third behaviour: **reclaim only
    where there is evidence the stack is idle, and fall back to the previous
    behaviour only where there is no evidence either way.**

    ⚡ **Strictly better, never worse.** Where nothing can be asked, this does
    exactly what it did before. Where docker answers, it answers the question
    the lease was always trying to ask.
    """
    current = _read()
    if current is None:
        return None
    if _alive(int(current.get("pid", -1))):
        return current

    running = _running_containers()
    if running:
        # 🔴 **The record is stale AND the stack is busy** — precisely QE's
        # near-miss. ⛔ Reclaiming here hands a live stack to a second run.
        # ✅ The containers replace the pid as the evidence, so the operator is
        # sent to something that exists rather than hunting a dead process.
        return {
            **current,
            "pid": "gone",
            "label": current.get("label", "?"),
            "evidence": (
                f"the recorded process is gone, and {len(running)} container(s) "
                f"of this stack are still running: {', '.join(sorted(running)[:4])}"
            ),
        }

    # ✅ Nothing is running, or nothing could be asked. Reclaim, as before.
    _lease_path().unlink(missing_ok=True)
    return None


def _describe(current: dict[str, Any]) -> str:
    started = current.get("started_at", "?")
    clone = current.get("clone")
    # ⚡ **B-436** — where the pid is gone but the stack is up, the containers
    # ARE the evidence, and naming the dead pid would send the operator hunting
    # for something that already died.
    if evidence := current.get("evidence"):
        return f"    {current.get('label', '?')}  — {evidence}"
    where = "" if clone in (None, str(REPO_ROOT)) else f"\n    in {clone}"
    mine = "  (this clone)" if clone == str(REPO_ROOT) else ""
    return (
        f"    {current.get('label', '?')}  pid {current.get('pid', '?')}"
        f"  since {started}{mine}{where}"
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
            "\n  Wait for it. Before forcing, read this:"
            "\n"
            "\n    A DEAD PID IS EVIDENCE ABOUT THIS RECORD, NOT ABOUT THE MACHINE."
            "\n"
            "\n  The pid above being gone proves the record is stale. It does not"
            "\n  prove the environment is free — another clone can be mid-run"
            "\n  under a record this file never saw. On 2026-08-15 exactly that"
            "\n  held: the recorded pid was dead, forcing would have been"
            "\n  technically correct, and a live run in another clone would have"
            "\n  lost its work."
            "\n"
            "\n  So check the machine, not the record:"
            "\n    ss -ltn | grep -E ':(3100|8100|5432)'     ports in use"
            "\n    pgrep -af 'pytest|playwright|smoke.sh'    runs in flight"
            "\n"
            "\n  Only then:"
            "\n    python3 infra/environment-lease.py release --force"
        )
        raise SystemExit(4)
    identifier = uuid.uuid4().hex[:12]
    _lease_path().write_text(
        json.dumps(
            {
                "id": identifier,
                "label": label,
                "pid": os.getpid(),
                # **Which checkout, because four can now answer.** "leased by
                # certify, pid 8231" was actionable when one clone existed; it
                # sends the reader to their own `ps` output when four do.
                "clone": str(REPO_ROOT),
                "resource": _resource(),
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
        _lease_path().unlink(missing_ok=True)


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

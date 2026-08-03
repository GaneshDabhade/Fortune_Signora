#!/usr/bin/env python3
"""**Is the workstation in a state where Release Engineering may begin?**

The repository has two operating modes that want the same two ports, and
until now nothing said so. **Human Review Mode** (`make demo`) runs a frontend
on 3000 and an API on 8000 so a person can use the product. **QE Release Mode**
(`make smoke`, `make certify`, `make dr`) needs those ports free, because the
smoke test builds its own stack on them.

**They are mutually exclusive, and the collision used to be discovered several
minutes into a smoke run** — as *"3 of 24 stages"*, which reads like a
repository defect and is not one. This tells you in under a second, and says
which of the two it is.

**It classifies; it never repairs.** Stopping somebody's review session to make
a gate green is exactly the move `CLAUDE.md` §20e forbids — the authority is to
make a documented gate *runnable*, never to make it *pass*.

    python3 infra/release-preflight.py          # human-readable
    python3 infra/release-preflight.py --quiet  # exit code only

Exit codes are the contract:

    0  ready       — QE Release Mode may begin
    2  waiting     — Human Review Mode is active. **Not a repository failure**
    3  blocked     — something else holds the ports, or a prerequisite is missing
"""

from __future__ import annotations

import argparse
import re
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

REPO_ROOT = Path(__file__).resolve().parent.parent

# The human-review allocation, from docs/RUNNING.md § Running a lane. Lanes get
# 3300/8300 and above precisely so they never contend for these two.
REVIEW_PORTS = (3000, 8000)

# What the review stack actually looks like on the process table. `make demo`
# prints the two commands a reviewer runs by hand, so the preflight recognises
# them rather than a wrapper it could not see.
REVIEW_SIGNATURES = ("next-server", "next dev", "uvicorn", "apps.api.main")


@dataclass(frozen=True)
class Holder:
    port: int
    process: str

    @property
    def is_review_stack(self) -> bool:
        return any(sig in self.process for sig in REVIEW_SIGNATURES)


def _container_holders() -> dict[int, str]:
    """Containers publishing a review port, by port.

    **A published container port belongs to `docker-proxy`, not to the process
    inside it**, so `ss` reports `unknown` and the operator is told to identify
    something the tool could have named. That happened to QE twice in two
    cycles, both times its own `make dr` stack — so the answer is a name, not a
    firmer instruction to go looking.
    """
    if not shutil.which("docker"):
        return {}
    out = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}\t{{.Ports}}"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    found: dict[int, str] = {}
    for line in out.splitlines():
        name, _, ports = line.partition("\t")
        for port in REVIEW_PORTS:
            if re.search(rf"(^|[^0-9]):{port}->", ports):
                found.setdefault(port, name)
    return found


def _listeners() -> list[Holder]:
    """Who is listening on the review ports, and as what.

    `ss` is used rather than `lsof` because it is present on a bare Debian
    container, which is what `RUNNING.md` assumes.
    """
    if not shutil.which("ss"):
        return []
    out = subprocess.run(
        ["ss", "-ltnp"], capture_output=True, text=True, check=False
    ).stdout
    containers = _container_holders()
    holders: list[Holder] = []
    for line in out.splitlines():
        for port in REVIEW_PORTS:
            if not re.search(rf":{port}\s", line):
                continue
            names = re.findall(r'"([^"]+)"', line)
            process = " ".join(names)
            if container := containers.get(port):
                # Name the container, and say what releases it. The operator
                # otherwise reads "unknown" for a stack they started themselves.
                process = f"container {container}" + (
                    "  → `make down` releases it"
                    if container.startswith("signora-prod-")
                    else f" ({process or 'docker'})"
                )
            holders.append(Holder(port=port, process=process or "unknown"))
    return holders


def _prerequisites() -> list[str]:
    """Documented prerequisites, checked before anything long-running starts."""
    missing = []
    for tool in ("docker", "node", "npx", "git"):
        if not shutil.which(tool):
            missing.append(tool)
    return missing


#: Below this, certification degrades rather than fails — which is the worst
#: shape of failure, because it looks like the repository got slower.
MINIMUM_AVAILABLE_GB: Final = 3.0
#: Swap this full means the machine is already trading memory for disk.
SWAP_PRESSURE: Final = 0.75


def _memory_pressure() -> tuple[float, float, list[str]] | None:
    """Available memory, swap saturation, and who is holding the machine.

    **The environment model isolates ports, databases, Redis and compose
    projects. It does not isolate the machine.** Every environment shares RAM,
    and nothing checked it — so a lane's dev server holding 2.7 GB was invisible
    to every gate while degrading certification.

    **The evidence this exists for.** Across 28 runs the smoke gate sat between
    104s and 193s except twice: 4830s and 1096s. The Docker build cache does not
    explain either — `tests/` is excluded from the frontend build context, so the
    4830s run invalidated nothing. What *was* observable afterwards: 4.0 GiB
    available of 15, swap 85% consumed, and a `pytest` that died mid-run leaving
    dots and no traceback — **the OOM-kill signature, not a test failure.**

    **It warns rather than blocks.** A slow certification is still a valid one,
    and refusing to start would trade a diagnosable slowdown for a blocked gate.
    """
    meminfo = Path("/proc/meminfo")
    if not meminfo.exists():
        return None
    values: dict[str, int] = {}
    for line in meminfo.read_text().splitlines():
        name, _, rest = line.partition(":")
        values[name] = int(rest.strip().split()[0])

    available_gb = values.get("MemAvailable", 0) / 1024 / 1024
    swap_total = values.get("SwapTotal", 0)
    swap_used = swap_total - values.get("SwapFree", 0)
    swap_ratio = (swap_used / swap_total) if swap_total else 0.0

    if available_gb >= MINIMUM_AVAILABLE_GB and swap_ratio < SWAP_PRESSURE:
        return None

    # Name the holders. An operator told only "memory is low" goes hunting —
    # the same lesson as naming the container that holds a port.
    # `args`, not `comm`: node reports its *thread* name there, so a VS Code
    # server and a lane's dev server both read as "MainThread" — which names
    # nothing an operator can act on.
    listing = subprocess.run(
        ["ps", "-eo", "rss,args", "--sort=-rss"], capture_output=True, text=True, check=False
    ).stdout.splitlines()[1:8]
    holders = []
    for row in listing:
        parts = row.split(None, 1)
        if len(parts) != 2 or (gigabytes := int(parts[0]) / 1024 / 1024) < 0.5:
            continue
        command = parts[1].strip()
        # A lane dev server is the case worth naming precisely, because it is
        # somebody else's and stopping it is not QE's call (§20e).
        if "next-server" in command or "next dev" in command:
            command = f"{command.split()[0]} — a dev server; check RUNNING.md for whose"
        holders.append(f"{gigabytes:.1f} GB  {command[:72]}")
    return available_gb, swap_ratio, holders


#: Where the suite's database lives. `RUNNING.md` allocates one per lane, all in
#: the development PostgreSQL — which the gates need running and never check.
DEV_DATABASE_PORT: Final = 5432


def _development_stack_missing() -> bool:
    """Whether the database every gate needs is unreachable.

    **RE-04, and it is an integration gap rather than a missing capability**:
    this preflight already existed and already checked prerequisites; nothing
    had taught it about the one service the suite cannot run without.

    The cost of not checking was measured. `pytest` blocked for **22 minutes**
    against an exited container, with no timeout and no diagnostic, and the
    failure looked like a hung suite rather than an absent database.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.5)
        return probe.connect_ex(("127.0.0.1", DEV_DATABASE_PORT)) != 0


def _tree_dirty() -> bool:
    out = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    return bool(out.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quiet", action="store_true", help="exit code only")
    args = parser.parse_args()

    def say(*lines: str) -> None:
        if not args.quiet:
            for line in lines:
                print(line)

    missing = _prerequisites()
    if missing:
        say(
            "",
            "  BLOCKED — a documented prerequisite is missing",
            "",
            f"    not on PATH: {', '.join(missing)}",
            "",
            "  docs/RUNNING.md lists what a workstation needs. Installing these is",
            "  within QE's authority (CLAUDE.md §20e); escalate only if it is not.",
        )
        return 3

    if _development_stack_missing():
        say(
            "",
            "  BLOCKED — the development database is not reachable",
            "",
            f"    nothing is listening on 127.0.0.1:{DEV_DATABASE_PORT}",
            "",
            "  Every gate needs it, and none of them check: `pytest` blocks with no",
            "  timeout and no diagnostic, which reads as a hung suite rather than an",
            "  absent database. That cost 22 minutes once (RE-04).",
            "",
            "    docker compose -f infra/docker-compose.yml up -d --wait",
        )
        return 3

    holders = _listeners()
    if not holders:
        lines = [
            "",
            "  READY — QE Release Mode may begin",
            "",
            f"    ports {REVIEW_PORTS[0]} and {REVIEW_PORTS[1]} are free",
            f"    working tree {'dirty — certify will refuse it' if _tree_dirty() else 'clean'}",
        ]
        if (pressure := _memory_pressure()) is not None:
            available, swap_ratio, holders = pressure
            lines += [
                "",
                "  ⚠️  MEMORY PRESSURE — certification will be slow, and may be killed",
                "",
                f"    {available:.1f} GB available · swap {swap_ratio:.0%} consumed",
                *(f"    {holder}" for holder in holders),
                "",
                "  Ports are isolated per environment; the machine is not. A lane's dev",
                "  server holding memory is invisible to every other gate, and this is",
                "  what turns a 120s smoke run into a 1096s one — or kills pytest",
                "  mid-run, which reads as a test failure and is not one.",
            ]
        say(*lines)
        # A dirty tree is reported but does not block: `make smoke` and `make dr`
        # both run against one, and only `make certify` records it as a condition.
        return 0

    review = [h for h in holders if h.is_review_stack]
    other = [h for h in holders if not h.is_review_stack]

    if review and not other:
        say(
            "",
            "  WAITING — a Human Review session is active",
            "",
            *(f"    :{h.port}  {h.process}" for h in review),
            "",
            "  This is an ENVIRONMENT state, not a repository failure. `make smoke`",
            "  builds its own stack on 3000/8000 and cannot run beside a review",
            "  session; a run started now fails around stage 3 and looks like a defect.",
            "",
            "  Release Engineering waits until the session ends. Do not stop somebody",
            "  else's review to obtain a green pipeline — the authority is to make a",
            "  gate runnable, never to make it pass (CLAUDE.md §20e).",
        )
        return 2

    # `ss` reports a listener per address family, so one holder appears twice.
    seen: set[tuple[int, str]] = set()
    unique = [
        h
        for h in other + review
        if (h.port, h.process) not in seen and not seen.add((h.port, h.process))
    ]
    say(
        "",
        "  BLOCKED — the review ports are held",
        "",
        *(f"    :{h.port}  {h.process}" for h in unique),
        "",
        "  Not the review stack. Identify it before releasing the port: a stray",
        "  lane dev server belongs to that lane, and a stale container is QE's",
        "  to remove.",
    )
    return 3


if __name__ == "__main__":
    raise SystemExit(main())

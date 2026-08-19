#!/usr/bin/env python3
"""**Is the workstation in a state where Release Engineering may begin?**

**The collision this was built for no longer exists**, and the honest thing is
to say so at the top rather than leave a checker guarding a resolved problem.

Human Review runs on **3000/8000**; the production stack that `make smoke`,
`make certify` and `make dr` build now runs on **3100/8100**. They were the same
two ports until 2026-08-03, which made a review session and a certification run
mutually exclusive *by construction* — the product owner could not start a
review because a leftover `make dr` stack held both. The compose file was moved
into the block `infra/environments.py` had recorded as allocated to nobody.

**So why does this still exist?** Because *"the ports are free"* was never the
only precondition, and the rest have each cost a real incident: an unreachable
development database once blocked `pytest` for 22 minutes with no diagnostic
(RE-04), and memory pressure from another environment turned a 130s smoke run
into a 320s one with nothing in the record to explain it.

**What it no longer does is arbitrate between two modes.** A review session on
3000/8000 is now simply *not this stack's business*, and a holder of 3100/8100
is a stale production stack — QE's own, and QE's to remove.

**It classifies; it never repairs.** Stopping somebody's review session to make
a gate green is exactly the move `CLAUDE.md` §20e forbids — the authority is to
make a documented gate *runnable*, never to make it *pass*.

    python3 infra/release-preflight.py          # human-readable
    python3 infra/release-preflight.py --quiet  # exit code only

Exit codes are the contract:

    0  ready       — QE Release Mode may begin
    3  blocked     — something holds 3100/8100, or a prerequisite is missing

**Exit code 2 is retired.** It meant *"a Human Review session is active, and
that is a correct state rather than a failure"* — a distinction that existed
only because the two shared ports. Nothing produces it now.
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

# The production stack's host binding, from infra/docker-compose.prod.yml.
# **Not the review ports any more** — that is the point of the move. Human
# review keeps 3000/8000 and lanes keep 3300/8300 upward, so a holder of these
# two is this stack and nothing else.
REVIEW_PORTS = (3100, 8100)

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


def _container_holders(ports: tuple[int, ...] = REVIEW_PORTS) -> dict[int, str]:
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
        name, _, published = line.partition("\t")
        for port in ports:
            if re.search(rf"(^|[^0-9]):{port}->", published):
                found.setdefault(port, name)
    return found


def _listeners(ports: tuple[int, ...] = REVIEW_PORTS) -> list[Holder]:
    """Who is listening on the given ports, and as what.

    **Parameterised, because a second caller got the wrong answer.**
    `infra/review.py` reuses this to name what holds *its* ports, and when the
    production stack moved to 3100/8100 the constant moved with it — so a live
    review session on 3000/8000 was reported to the reviewer as `unknown`.
    A shared helper that silently answers about somebody else's ports is worse
    than no helper.

    `ss` is used rather than `lsof` because it is present on a bare Debian
    container, which is what `RUNNING.md` assumes.
    """
    if not shutil.which("ss"):
        return []
    out = subprocess.run(
        ["ss", "-ltnp"], capture_output=True, text=True, check=False
    ).stdout
    containers = _container_holders(ports)
    holders: list[Holder] = []
    for line in out.splitlines():
        for port in ports:
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


#: 🔴 **This was `5432` — [B-1028](../docs/BUGS.md), and the comment beside it
#: said the right thing while the value did the wrong one**: *"`RUNNING.md`
#: allocates one per lane"* — and then named slot 0, which is **human review's**.
#:
#: So `make certify` refused to start whenever the reviewer's stack was down,
#: naming a database the lane does not use and must not start. **The mechanism
#: was already imported one directory over**: `environments.py` derives the
#: lane's port and `current()`'s own docstring warns that guessing *"points a
#: suite at another lane's database, which is the class of defect the whole
#: change exists to end."*
def _database_port() -> int | None:
    """The lane's own PostgreSQL port, or `None` when no environment resolves.

    **`None` is not an error here.** `environments.py` returns nothing on
    `main`, on `integration` and on a detached HEAD, and a preflight that
    refused there would block certification on branches it is meant to run
    from. **The check is skipped and says so**, which is honest — where
    guessing `5432` was not.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import environments

    resolved = environments.current()
    return resolved.postgres_port if resolved else None


def _development_stack_missing() -> bool:
    """Whether the database every gate needs is unreachable.

    **RE-04, and it is an integration gap rather than a missing capability**:
    this preflight already existed and already checked prerequisites; nothing
    had taught it about the one service the suite cannot run without.

    The cost of not checking was measured. `pytest` blocked for **22 minutes**
    against an exited container, with no timeout and no diagnostic, and the
    failure looked like a hung suite rather than an absent database.
    """
    port = _database_port()
    if port is None:
        return False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.5)
        return probe.connect_ex(("127.0.0.1", port)) != 0


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
            f"    nothing is listening on 127.0.0.1:{_database_port()} — this lane's own",
            "",
            "  Every gate needs it, and none of them check: `pytest` blocks with no",
            "  timeout and no diagnostic, which reads as a hung suite rather than an",
            "  absent database. That cost 22 minutes once (RE-04).",
            "",
            "    env $(python3 infra/environments.py --exports | grep -v '^#') \\",
            "      docker compose -f infra/docker-compose.yml up -d --wait",
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
            # ⚠️ **`memory_holders`, not `holders`** — [B-435](../docs/BUGS.md).
            # `holders` already means `list[Holder]` ten lines above, bound at
            # `_listeners()` and iterated at the bottom of this function for
            # `.is_review_stack`. `_memory_pressure()` returns `list[str]`.
            #
            # ⛔ **It works today ONLY because this branch always returns 0.**
            # Remove that return, or move this block below the port checks, and
            # the bottom of the function iterates STRINGS looking for an
            # attribute — an `AttributeError` inside the certification preflight.
            #
            # ⚡ Second instance of one shape in one day: `state-check.py` bound
            # `named` twice in one function and worked only because the second
            # binding preceded the second use. **`mypy` is what noticed both,
            # and `infra/` is outside every gate that runs it.**
            available, swap_ratio, memory_holders = pressure
            lines += [
                "",
                "  ⚠️  MEMORY PRESSURE — certification will be slow, and may be killed",
                "",
                f"    {available:.1f} GB available · swap {swap_ratio:.0%} consumed",
                *(f"    {holder}" for holder in memory_holders),
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
        # **A dev server on this block is somebody's misconfiguration, not a
        # review.** Since the production stack moved off 3000/8000, nothing
        # legitimate binds these two except this stack itself — so a `next dev`
        # or a bare `uvicorn` here is an environment pointed at the wrong row of
        # RUNNING.md, and naming that is more useful than waiting for it.
        say(
            "",
            "  BLOCKED — a development server is on the production stack's ports",
            "",
            *(f"    :{h.port}  {h.process}" for h in review),
            "",
            f"  {REVIEW_PORTS[0]}/{REVIEW_PORTS[1]} belong to the local production stack.",
            "  Human review uses 3000/8000 and a lane uses its own row in",
            "  docs/RUNNING.md § Running a lane. Something is pointed at the wrong one.",
            "",
            "  It is not QE's to stop — hand the finding to whoever owns it.",
        )
        return 3

    # `ss` reports a listener per address family, so one holder appears twice.
    # ⚡ **An explicit loop rather than `and not seen.add(...)`** — the
    # comprehension worked, because `set.add` returns `None` and `not None` is
    # `True`, but it reads as a bug to everybody who has not met the idiom.
    # 📁 [§6](../CLAUDE.md): *correctness and clarity outrank cleverness*, and
    # this is the version somebody can check at a glance.
    seen: set[tuple[int, str]] = set()
    unique: list[Holder] = []
    for h in other + review:
        key = (h.port, h.process)
        if key in seen:
            continue
        seen.add(key)
        unique.append(h)
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

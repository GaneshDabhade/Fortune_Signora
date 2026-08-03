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
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

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

    holders = _listeners()
    if not holders:
        say(
            "",
            "  READY — QE Release Mode may begin",
            "",
            f"    ports {REVIEW_PORTS[0]} and {REVIEW_PORTS[1]} are free",
            f"    working tree {'dirty — certify will refuse it' if _tree_dirty() else 'clean'}",
        )
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

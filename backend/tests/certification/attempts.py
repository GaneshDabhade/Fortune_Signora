"""**Every certification attempt, including the ones that left no other trace.**

The manifest records *runs*. This records *attempts*, and the difference is the
whole point.

**Two structural gaps, found by studying the pipeline rather than by guessing**
([`RELEASE_ENGINEERING.md`](../../../docs/RELEASE_ENGINEERING.md)):

**1 · A failed run is erased by the reset the next attempt requires.**
`tree_is_clean()` reads `git status --porcelain`, which covers untracked files
too — so *every* run dirties the tree by writing the manifest and its report. A
**passing** run survives because Closeout commits it. A **failing** run has no
commit to carry it, so the operator's correct next move — `git checkout --
certification/manifest.json` — deletes the only evidence the failure happened.
The tree-clean condition and the failure record are in direct conflict *by
construction*.

**2 · An aborted run writes nothing at all.** `append()` is called once, after
every gate. A run that hangs, is killed, or crashes never reaches it. A
22-minute hang against an exited database left **no record in any file**.

Together those produced a manifest reading *21 runs, 0 failures, 0 reruns* from
a cycle that had two failures and three attempts. **That 100% was survivorship
bias, not a measurement**, and every stability KPI built on it was optimistic.

**Why a separate, git-ignored file rather than the manifest.** They are
different data categories, and `CLAUDE.md` §2 already names the distinction: the
manifest is **repository truth** — which commits are certified, evidence a
customer could audit — while this is **operational history**, the pipeline's
account of its own behaviour. Keeping them apart is not tidiness:

* being git-ignored, this file **never dirties the tree**, so it survives the
  reset that erases a failed manifest entry — which is precisely gap 1;
* the manifest stays a record of *certifications*, not of machine weather.

**It records facts and never infers them.** No field says whether a failure was
the environment's, the operator's or the repository's — that is a judgement, and
a column of guesses is worse than none. What it captures is what a human needs
*to make* that judgement: which gate failed, what was running, how long it took.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final, Literal

REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[3]
ATTEMPTS: Final = REPOSITORY_ROOT / "certification" / "attempts.jsonl"

#: Ports whose occupancy changes what a run measures — the review allocation
#: from `docs/RUNNING.md`, which `make smoke` binds absolutely.
WATCHED_PORTS: Final = (3000, 8000)

Outcome = Literal["certified", "failed"]


@dataclass(frozen=True, slots=True)
class Attempt:
    """One certification attempt. **Started is a fact; finished is not yet.**"""

    identifier: str
    commit: str
    branch: str
    started_at: datetime

    def begin(self, *, path: Path = ATTEMPTS) -> None:
        _write(
            path,
            {
                "attempt": self.identifier,
                "event": "started",
                "commit": self.commit,
                "branch": self.branch,
                "at": self.started_at.isoformat(),
                "environment": _environment(),
            },
        )

    def conclude(
        self,
        *,
        outcome: Outcome,
        failing_gates: tuple[str, ...],
        coverage: float,
        path: Path = ATTEMPTS,
    ) -> None:
        finished = datetime.now(UTC)
        _write(
            path,
            {
                "attempt": self.identifier,
                "event": "finished",
                "outcome": outcome,
                "at": finished.isoformat(),
                "duration_s": round((finished - self.started_at).total_seconds(), 1),
                "failing_gates": list(failing_gates),
                "coverage": coverage,
            },
        )


def start(*, repository_root: Path = REPOSITORY_ROOT, path: Path = ATTEMPTS) -> Attempt:
    """Record that an attempt began, and return the handle that concludes it.

    **Called before the first gate**, so that an attempt which never finishes is
    still visible as a `started` with no `finished` — which is the only way an
    abort can be counted at all.
    """
    attempt = Attempt(
        identifier=uuid.uuid4().hex[:12],
        commit=_git(["rev-parse", "HEAD"], repository_root),
        branch=_git(["rev-parse", "--abbrev-ref", "HEAD"], repository_root),
        started_at=datetime.now(UTC),
    )
    attempt.begin(path=path)
    return attempt


def load(*, path: Path = ATTEMPTS) -> tuple[dict[str, Any], ...]:
    """Every recorded event, oldest first. Missing file means none."""
    if not path.exists():
        return ()
    events: list[dict[str, Any]] = []
    for line in path.read_text().splitlines():
        if line.strip():
            # A truncated final line is the signature of a process killed
            # mid-write. Skipping it loses one event; refusing to read loses
            # the whole history, which is the more expensive failure.
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return tuple(events)


@dataclass(frozen=True, slots=True)
class Stability:
    """What the attempt log can answer that the manifest structurally cannot."""

    attempts: int
    certified: int
    failed: int
    aborted: int
    gate_failures: dict[str, int]

    @property
    def completion_rate(self) -> float:
        """Attempts that reached a verdict. **Not a quality measure** — it says
        how often the pipeline runs to completion, never whether the code is
        good."""
        return round(100.0 * (self.certified + self.failed) / self.attempts, 1) if self.attempts else 0.0

    @property
    def first_pass_rate(self) -> float:
        """Attempts that certified. **The figure the manifest reported as 100%.**"""
        return round(100.0 * self.certified / self.attempts, 1) if self.attempts else 0.0


def stability(*, path: Path = ATTEMPTS) -> Stability:
    """Aggregate the log. **An attempt with no `finished` is an abort** — that
    is the whole reason `started` is written separately."""
    events = load(path=path)
    started = {e["attempt"] for e in events if e.get("event") == "started"}
    finished = {e["attempt"]: e for e in events if e.get("event") == "finished"}
    gate_failures: dict[str, int] = {}
    for event in finished.values():
        for gate in event.get("failing_gates", ()):
            gate_failures[gate] = gate_failures.get(gate, 0) + 1
    return Stability(
        attempts=len(started),
        certified=sum(1 for e in finished.values() if e.get("outcome") == "certified"),
        failed=sum(1 for e in finished.values() if e.get("outcome") == "failed"),
        aborted=len(started - set(finished)),
        gate_failures=dict(sorted(gate_failures.items())),
    )


def _environment() -> dict[str, Any]:
    """What was running when the attempt began.

    **Context for a human classifying a failure**, never a classification. A
    container count of zero beside a `pytest` failure is the difference between
    *"the suite is broken"* and *"the database was not there"* — which is
    exactly the call that took 22 minutes to make by hand.
    """
    return {
        "containers": _container_count(),
        "ports_held": [port for port in WATCHED_PORTS if _port_held(port)],
        "host": socket.gethostname(),
        "test_database": _database_name(),
    }


def _container_count() -> int:
    result = subprocess.run(
        ["docker", "ps", "--quiet"], capture_output=True, text=True, check=False
    )
    return len([line for line in result.stdout.splitlines() if line.strip()])


def _port_held(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.2)
        return probe.connect_ex(("127.0.0.1", port)) == 0


def _database_name() -> str:
    """The database the suite will actually use.

    **Recorded because getting it wrong is a real defect, not a hypothetical**
    ([B-022](../../../docs/BUGS.md)): certification once measured 2238 tests at
    94.34% against the shared database and recorded it as fact.
    """
    url = os.environ.get("SIGNORA_TEST_APP_DATABASE_URL", "")
    return url.rsplit("/", 1)[-1] if "/" in url else "(unset — defaults to shared)"


def _write(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def _git(arguments: list[str], repository_root: Path) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository_root,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()

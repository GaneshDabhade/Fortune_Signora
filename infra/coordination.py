#!/usr/bin/env python3
"""Generate the canonical coordination source — [479](../docs/architecture/479-coordination-architecture.md).

**One file answers what a lane must otherwise assemble from 14,392 lines across
seven documents**, and it answers it without waiting for QE to integrate
anything ([D-142](../docs/DECISION_REGISTER.md)).

⛔ **It is a projection, never a second truth.** `BACKLOG.md` stays
authoritative for scope, `modules.toml` for ownership, `LANE_COORDINATION.md`
for dependencies. This joins them and publishes the join. **A hand-maintained
coordination file would be an eighth place to disagree** (`CLAUDE.md` §2);
a generated one cannot drift, because regenerating it is the only way to
change it.

    python3 infra/coordination.py            # write docs/coordination/coordination.toml
    python3 infra/coordination.py --check    # exit 1 if the published file is stale
    python3 infra/coordination.py --publish  # validate, then move origin/coordination
    python3 infra/coordination.py --self-test  # prove the publish guard refuses

⛔ **Never publish this ref by hand.** `--publish` builds the two-file tree,
validates it against the contract, and only then moves the ref — because on
2026-08-08 a hand-rolled `git push` put the *entire repository tree* on it and
broke every lane's poll ([D-181](../docs/DECISION_REGISTER.md)).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKLOG = ROOT / "docs" / "BACKLOG.md"
MODULES = ROOT / "docs" / "coordination" / "modules.toml"
OUT = ROOT / "docs" / "coordination" / "coordination.toml"

#: **The eight states of [479 §4](../docs/architecture/479-coordination-architecture.md), and there is no ninth.**
#: A task the generator cannot place is an error rather than a row with a
#: blank field — which is how *floating backlog* becomes unrepresentable
#: instead of merely discouraged ([D-142](../docs/DECISION_REGISTER.md) §7).
ASSIGNED = "ASSIGNED"
BLOCKED = "BLOCKED"
SEQUENCED = "SEQUENCED"
WAITING_PRODUCT_OWNER = "WAITING_PRODUCT_OWNER"
WAITING_EXTERNAL = "WAITING_EXTERNAL"
WAITING_ARCHITECTURE = "WAITING_ARCHITECTURE"
FUTURE_MILESTONE = "FUTURE_MILESTONE"
IN_FLIGHT = "IN FLIGHT"

#: Lane-owned and QE-owned execution states. **Product Office never writes one**
#: ([D-123](../docs/DECISION_REGISTER.md)), so they collapse to `IN FLIGHT`
#: here — the coordination source reports that somebody holds the row without
#: ever being able to change which somebody.
_HELD = frozenset({
    "CLAIMED", "IN PROGRESS", "IN VALIDATION", "CHANGES REQUESTED",
    "VERIFIED", "CERTIFIED", "PROMOTED", "DONE",
})
_CLOSED = frozenset({"DONE", "DISPOSED", "PROMOTED"})

#: **Rows a lane can still act on** — B-409, 2026-08-08.
#:
#: ⛔ `IN FLIGHT` collapses eight declared states, and only three of them are
#: work the lane can touch. **`IN VALIDATION` has left the lane entirely**
#: (§20e: *"the lane's responsibility for this task has ended"*), and so have
#: `VERIFIED`, `CERTIFIED`, `PROMOTED` and `DONE`.
#:
#: ⚠️ **This mattered because a check read `in_flight` as "the lane has work".**
#: **Lane A idled 136 cycles holding 48 in-flight rows, every one of them
#: `IN VALIDATION` and untouchable**, while the check that exists to catch an
#: idle lane stayed silent because the number was large.
_ACTIONABLE = frozenset({"CLAIMED", "IN PROGRESS", "CHANGES REQUESTED"})
_STARTABLE = frozenset({"READY", "CHANGES REQUESTED"})

#: Prose forms of a `modules.toml` key. **The registry is keyed
#: `product_surface`; a backlog row writes *Product Surface*.** Enumerated
#: rather than inferred, because a fuzzy match once resolved `TASK-441` —
#: *"Product Surface — Lane A, reads `opportunity_engine`"* — to Lane B, on
#: the module it reads rather than the module it is.
_ALIASES = {
    "product surface": "product_surface",
    "action batch": "action_batch",
    "platform foundation": "platform_foundation",
}


@dataclass(slots=True)
class Task:
    """One backlog row as the coordination source publishes it.

    **A dataclass rather than a dict**, because `dict[str, object]` forced a
    cast at every read and the casts were where the type errors lived — which
    is `CLAUDE.md` §2's *types should make incorrect architecture impossible*
    applied to a generator's own intermediate form.
    """

    id: str
    title: str
    state: str
    declared: str
    lane: str
    depends_on: list[str]
    #: **Why it cannot start**, in the row's own words — not a restatement.
    waiting_for: str = ""
    unblocks: list[str] = field(default_factory=list)
    next_owner: list[str] = field(default_factory=list)
    next_lane: str = "—"
    #: **Longest chain of unfinished predecessors ending here.** `0` means
    #: nothing precedes it. ⚡ **This is what makes a queue an ordering rather
    #: than a list**: the deepest chain is where a lane's supply actually
    #: comes from, and shortening it is worth more than adding a row.
    critical_path: int = 0
    #: **The condition, never a date.** A date would be a forecast this office
    #: cannot make; a condition is checkable by whoever holds the blocker.
    estimated_ready: str = "—"
    #: How long the row has held its current declared state, in days.
    blocked_days: float = 0.0
    #: **Does `origin/integration` agree with this row's declared state?**
    #:
    #: ⛔ **Raised by Lane A, 2026-08-07.** This source is generated from
    #: `lane-c-sync`'s backlog and stamped with `integration`'s commit, so it
    #: advertised five rows as claimable — `TASK-451`, `463`, `467`, `468`,
    #: `471` — that read `SEQUENCED` on `integration`. **A lane taking one
    #: would push a claim contradicting the authoritative backlog.**
    #:
    #: ⚡ **[C-425](../docs/LANE_COORDINATION.md) ruled this exact case and
    #: ruled against this office**: *"where the ref disagrees with
    #: `BACKLOG.md`, the backlog wins and the disagreement is a defect."*
    #: **The ref does not get to be ahead; it gets to be fast.**
    on_integration: bool = True


def _git(*args: str, stdin: str | None = None) -> str:
    """Read-only git. **Returns empty on failure, deliberately** — a missing ref
    is a normal answer to *"what does `integration` say about this row?"*
    """
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, input=stdin
    ).stdout.strip()


class GitFailed(RuntimeError):
    pass


def _git_strict(*args: str, stdin: str | None = None) -> str:
    """Git that **raises when it fails**, for anything that writes.

    ⚡ **D-181's root cause, one layer down.** The published account of that
    failure is *"a command that treated success and failure identically"* — and
    `_git` above is exactly such a command. It is correct for reading, where an
    absent ref is an answer; it is **wrong for a push, where an empty string and
    a successful push are indistinguishable**, which would let `--publish` print
    *published* over a rejection.

    ⛔ **The lesson generalises past the shell: a helper that cannot express
    failure will eventually be used where failure matters.**
    """
    done = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, input=stdin
    )
    if done.returncode != 0:
        raise GitFailed(f"git {' '.join(args[:3])} exited {done.returncode}: "
                        f"{(done.stderr or done.stdout).strip()[:300]}")
    return done.stdout.strip()


def _owners() -> dict[str, str]:
    registry = tomllib.loads(MODULES.read_text())
    return {
        key: row["current_owner"]
        for key, row in registry.items()
        if isinstance(row, dict) and row.get("current_owner")
    }


def _lane_for(
    module_cell: str, body: str, owners: dict[str, str], declared: str = ""
) -> str | None:
    """Which lane owns this row.

    **Precedence matters and was learned the hard way.** An explicit
    ``— Lane X`` in the Module cell is the row's own statement about itself and
    wins; only then a module key; only then the trigger steward. Reading the
    first module key found instead resolved a row to the lane whose module it
    *reads* rather than the lane whose module it *is*.

    ⛔ **A trigger steward supplies an owner, never an executor — 2026-08-10.**
    [D-135](../docs/DECISION_REGISTER.md) introduced the steward in exactly
    those words: *"every task should have an owner even if it cannot yet have
    an executor."* **This function read it as both**, and on a **claimable**
    row that difference is the whole of it — the projection publishes the
    steward in a lane's `backlog`, which is the array §20e step 4 tells a lane
    to select from.

    🔴 **Measured on `TASK-412`, not foreseen.** Its Module cell is absent and
    its steward is Lane C, so the published ref offered **Product Office** a
    row whose own Change Budget is 🟢 ``modules/ai_platform/**`` — a module
    [`modules.toml`](../docs/coordination/modules.toml) settles on Lane A and
    §20e forbids Lane C to implement. **Meanwhile `queues/lane-a.toml` queued
    the same row to Lane A**: one row, two documents, opposite owners, which is
    the [C-213](../docs/LANE_COORDINATION.md) class this ref exists to end.

    ✅ **Withholding it is not a loss of information.** `_classify` already
    renders a startable row with no lane as ``WAITING ARCHITECTURE``, which is
    what `TASK-412` truthfully is: [D-042](../docs/DECISION_REGISTER.md)
    deliberately deferred its module boundary and *"do not force a module
    boundary until implementation naturally reaches it"* is still the ruling.
    **A parked row keeps its steward**, so D-135's purpose is untouched — the
    row still has somebody watching its trigger.
    """
    explicit = re.search(r"—\s*\*?\*?(Lane [ABC])", module_cell) or re.search(
        r"\*\*(Lane [ABC])\*\*", module_cell
    )
    if explicit:
        return explicit.group(1)
    for key, lane in owners.items():
        if re.search(rf"\b{key}\b", module_cell):
            return lane
    for phrase, key in _ALIASES.items():
        if phrase in module_cell.lower() and key in owners:
            return owners[key]
    if declared in _STARTABLE:
        return None
    steward = re.search(r"Trigger steward\*\*\s*\|\s*\*\*(Lane [ABC])", body)
    return steward.group(1) if steward else None


#: The words a blocker clause actually uses, **counted across the backlog
#: rather than guessed**: `predecessor` 9 · `after` 8 · `on` 2 · `behind` 1 ·
#: `predecessors` 1. ⚠️ **The first version omitted `predecessor` and so
#: missed nine edges of thirteen** — the most common form, absent because the
#: pattern was written from three examples somebody remembered.
_BLOCKER_PHRASE = re.compile(
    r"(?:predecessors?|after|on|behind)\s+\*?\*?\[?(TASK-\d+)"
)


def _dependencies(declared: str, status: str) -> list[str]:
    """The tasks this row actually waits on.

    ⛔ **Only from a row that declares itself blocked, and only from the
    clause that follows the state token.** A blocker is written immediately
    after the state — ``BLOCKED on [TASK-472]``, ``SEQUENCED — after
    [TASK-448]`` — and everything past that is narrative.

    **Reading the whole cell instead produced a false edge on the first run**:
    `TASK-440`'s status explains a precedent — *"reversed the identical block
    on TASK-441"* — and a scan for *on TASK-nnn* took the sentence for a
    dependency. **B-101's class inside the graph the graph exists to
    compute**, and a wrong edge is worse than a missing one because a lane
    would wait on it.
    """
    if declared == "READY":
        # ⚡ **A released row keeps its edge — 2026-08-07.**
        # Rewriting `SEQUENCED — after [TASK-457]` into `READY` **deleted the
        # only record of what the row had been waiting for**, so `TASK-458`
        # became claimable with an empty `depends_on` and no check could see
        # that its predecessor was still `CLAIMED`. ⛔ **Releasing a row
        # destroyed the evidence that the release was wrong**, which is the
        # worst shape a planning edit can have. **Lane A found it by opening
        # `people/public/__init__.py` and seeing nothing in it.**
        released = re.search(r"[Rr]eleased from `?(?:SEQUENCED|BLOCKED)`?[^.|]*", status)
        return sorted(set(_BLOCKER_PHRASE.findall(released.group(0)))) if released else []
    if declared not in {"BLOCKED", "SEQUENCED", "WAITING"}:
        return []
    token = re.search(r"`(?:BLOCKED|SEQUENCED|WAITING)`", status)
    if token is None:
        return []
    clause = status[token.end(): token.end() + 130]
    return sorted(set(_BLOCKER_PHRASE.findall(clause)))


def _cell(body: str, label: str) -> str:
    match = re.search(rf"^\|\s*[^|]*\*\*{label}[^|]*\*\*[^|]*\|([^|]*)\|", body, re.M)
    return match.group(1).strip() if match else ""


def _blocker_clause(status: str) -> str:
    """The text stating *why* a row is parked, and nothing after it.

    **Bounded the same way `_dependencies` bounds itself**: from the state
    token to the end of the clause, before the row's narrative resumes.
    ⚠️ **Generous at 260 characters** — wide enough for a real reason with its
    links, narrow enough to exclude the release boilerplate that follows.
    """
    token = re.search(r"`(?:BLOCKED|SEQUENCED|WAITING)`", status)
    return status[token.end(): token.end() + 260] if token else status


def _classify(declared: str, blocker_text: str, lane: str | None) -> str:
    """One of eight, or a refusal.

    **The order is deliberate**: a row a lane is holding is `IN FLIGHT` whoever
    else is waiting on it, because that state is the lane's and this file may
    not contradict it.
    """
    if declared in _HELD:
        return IN_FLIGHT
    if declared in _STARTABLE:
        return ASSIGNED if lane else WAITING_ARCHITECTURE
    low = blocker_text.lower()
    if "product owner" in low:
        return WAITING_PRODUCT_OWNER
    if any(word in low for word in ("credential", "external", "vendor", "hubspot")):
        return WAITING_EXTERNAL
    if "adr" in low or "architecture" in low or "bounded context" in low:
        return WAITING_ARCHITECTURE
    if declared == "BLOCKED":
        return BLOCKED
    if declared == "WAITING":
        return WAITING_EXTERNAL
    if declared == "SEQUENCED":
        return SEQUENCED
    return FUTURE_MILESTONE


#: Lifecycle order, for reconciling two refs that disagree about one row.
#: **Later wins** — a row claimed on `main` is not `READY` merely because a
#: stale `integration` still says so.
_LIFECYCLE = {
    "READY": 1, "SEQUENCED": 1, "BLOCKED": 1, "WAITING": 1,
    "CLAIMED": 2, "IN PROGRESS": 3,
    "IN VALIDATION": 4,
    # ⛔ **`CHANGES REQUESTED` ranks ABOVE `IN VALIDATION`, not below it —
    # [B-163](../docs/BUGS.md), corrected under [D-228](../docs/DECISION_REGISTER.md).**
    #
    # 🔴 **It is the one transition §20e places AFTER `IN VALIDATION`**: *"QE,
    # during validation. Something did not hold. Returned to the implementing
    # lane."* **Every other transition is monotonic; this one is a return.**
    #
    # ⚠️ **Ranked below, "later wins" resolved a returned slice back to `IN
    # VALIDATION`** — so a row QE had handed back read as still waiting on QE,
    # and **the lane that had to act could not see that it had to act.**
    # ⚡ **Reachable precisely in the divergence this function exists for.**
    "CHANGES REQUESTED": 5,
    "VERIFIED": 6, "CERTIFIED": 7, "PROMOTED": 8, "DONE": 9,
}


def _integration_states() -> dict[str, str]:
    """Each row's declared state on `origin/integration`, or empty if unreadable.

    ⚡ **Read once per run.** This is the authoritative backlog every lane
    claims against, and the only thing that makes `on_integration` a fact
    rather than an assumption about how recently QE integrated.
    """
    # ⛔ **`main` is read too, and it is not belt-and-braces — B-221, 2026-08-09.**
    #
    # 🔴 **`integration` can fall BEHIND `main`.** The normal topology is
    # `integration` ahead, then `main` fast-forwards onto it — but when a
    # promotion lands by SHA and `integration` cannot fast-forward, the two
    # diverge (**34 commits on 2026-08-09**) and a row promoted to `main` is
    # then *absent from `integration`*.
    #
    # ⚡ **A lane can reach either ref**, so reporting such a row as unreachable
    # understates the backlog — and this office then looks like it prepared
    # nothing while three promoted rows sat outside the array.
    #
    # ✅ **Reachable if EITHER ref carries it, and the later lifecycle state
    # wins**, so a claim on one ref is never hidden by a `READY` on the other.
    merged: dict[str, str] = {}
    for ref in ("origin/integration", "origin/main"):
        text = _git("show", f"{ref}:docs/BACKLOG.md")
        if not text:
            continue
        for block in re.split(r"(?=^### TASK-\d+)", text, flags=re.M):
            head = re.match(r"^### (TASK-\d+)", block)
            status = _cell(block.split("\n### ", 1)[0], "Status")
            token = re.search(r"`([A-Z][A-Z ]+)`", status) if status else None
            if not (head and token):
                continue
            state, seen = token.group(1).strip(), merged.get(head.group(1))
            if seen is None or _LIFECYCLE.get(state, 0) > _LIFECYCLE.get(seen, 0):
                merged[head.group(1)] = state
    return merged


def tasks() -> list[Task]:
    owners = _owners()
    upstream = _integration_states()
    text = BACKLOG.read_text()
    rows: list[Task] = []
    for block in re.split(r"(?=^### TASK-\d+)", text, flags=re.M):
        head = re.match(r"^### (TASK-\d+) ·([^\n]*)", block)
        if head is None:
            continue
        body = block.split("\n### ", 1)[0]
        status = _cell(body, "Status")
        token = re.search(r"`([A-Z][A-Z ]+)`", status)
        declared = token.group(1).strip() if token else ""
        if declared in _CLOSED:
            continue
        module_cell = _cell(body, "Module")
        lane = _lane_for(module_cell, body, owners, declared)
        depends = _dependencies(declared, status)
        # ⛔ **The blocker clause, not the whole cell — 2026-08-07.**
        # `_classify` substring-matches this for *"product owner"*, *"credential"*,
        # *"adr"* and so on, and a Status cell carries its own history. **This
        # office writes *"placed by the product owner, not here"* on every row it
        # releases**, so a row released and later re-parked read as
        # `WAITING_PRODUCT_OWNER` on its own boilerplate. **`TASK-458` did,
        # within a minute of being re-pointed at `TASK-428`.**
        #
        # ⚡ **`_dependencies` already reads only the clause following the state
        # token**, for exactly this reason and with a comment saying so. **The
        # two functions parse the same cell and only one of them was careful.**
        blocker = _blocker_clause(status) if declared in {"BLOCKED", "SEQUENCED", "WAITING"} else ""
        rows.append(
            Task(
                id=head.group(1),
                title=head.group(2).strip()[:90],
                state=_classify(declared, blocker, lane),
                declared=declared or "(none)",
                lane=lane or "—",
                depends_on=depends,
                waiting_for=blocker.strip()[:200],
                # ⛔ **Empty upstream means unreadable, not disagreeing.** A
                # clone that cannot reach `origin/integration` must not report
                # every row as unsynchronised.
                on_integration=(not upstream) or upstream.get(head.group(1)) == declared,
            )
        )
    # `unblocks` is the inverse of `depends_on`, computed rather than restated:
    # two hand-kept lists are two lists that eventually disagree.
    inverse: dict[str, list[str]] = {}
    for row in rows:
        for dep in row.depends_on:
            inverse.setdefault(dep, []).append(row.id)
    by_id = {r.id: r for r in rows}
    for row in rows:
        row.unblocks = sorted(inverse.get(row.id, []))
        row.next_owner = sorted(
            {by_id[s].lane for s in row.unblocks if by_id[s].lane != "—"}
        )
        row.next_lane = row.next_owner[0] if len(row.next_owner) == 1 else "—"
    _walk(rows, by_id)
    # **Read once, before the loop** — B-145, and the same shape B-144 forced
    # on `metrics_for` a day earlier. The baseline is consulted here and
    # nowhere below, so every row in this pass is aged against one instant.
    baseline = _baseline()
    for row in rows:
        if row.state not in {ASSIGNED, IN_FLIGHT}:
            row.blocked_days = _blocked_days(row, baseline)
    return rows


def _walk(rows: list[Task], by_id: dict[str, Task]) -> None:
    """Depth of the longest unfinished chain ending at each task.

    **[D-143](../docs/DECISION_REGISTER.md) §3: compute executable work by
    walking the graph rather than rediscovering relationships every cycle.**

    ⚠️ **Cycles are treated as depth-0 rather than crashing.** A dependency
    cycle is a real planning defect and the generator should report the rest
    of the graph while it exists — a tool that refuses to run because one row
    is wrong tells a lane nothing about the other eighty-three.
    """
    depth: dict[str, int] = {}
    visiting: set[str] = set()

    def measure(task_id: str) -> int:
        if task_id in depth:
            return depth[task_id]
        if task_id in visiting:      # a cycle; see the docstring
            return 0
        task = by_id.get(task_id)
        if task is None or not task.depends_on:
            depth[task_id] = 0
            return 0
        visiting.add(task_id)
        deepest = max(
            (measure(d) + 1 for d in task.depends_on if d in by_id), default=0
        )
        visiting.discard(task_id)
        depth[task_id] = deepest
        return deepest

    for row in rows:
        row.critical_path = measure(row.id)
        unfinished = [
            by_id[d].id for d in row.depends_on
            if d in by_id and by_id[d].state != ASSIGNED
        ]
        row.estimated_ready = (
            "now" if row.state == ASSIGNED
            else ("when " + ", ".join(unfinished) + " complete") if unfinished
            else (row.waiting_for[:70] or "—")
        )



def _baseline() -> datetime | None:
    """**The commit this file is generated *from*, as an instant** — B-145.

    ⛔ **Never `datetime.now()`.** The published source must be a pure function
    of the repository, and it was not: `_blocked_days` measured against the
    wall clock and baked the result into the file, so **the file drifted stale
    against its own `--check` roughly every 2.4 hours** without a single
    planning fact changing. **A check that goes red on its own is one lanes
    learn to read past**, which is the whole cost.

    ⚡ **The same defect class as [B-144] in this same module, one day apart**:
    an input that changes the output without being part of the declared
    contract (`CLAUDE.md` §2, *hidden inputs are architecture defects*).
    **B-144 was a clone read mid-function; this is a clock read mid-function.**

    ⚠️ **The metric is kept rather than dropped.** [D-144] asked for starvation
    to be *"a measurement rather than a report"*, and dating from the baseline
    keeps every number it wanted. **What changes is only that two regenerations
    of one commit now produce one file.**
    """
    stamp = _git("log", "--format=%cI", "-1", "origin/integration")
    if not stamp:
        return None
    try:
        return datetime.fromisoformat(stamp)
    except ValueError:
        return None


def _blocked_days(task: Task, baseline: datetime | None) -> float:
    """Days the row had held its declared state **as of the baseline commit**.

    **Dated from the commit that introduced the state string**, which is the
    only record the repository actually keeps. ⚠️ **It is a lower bound**: a
    row re-stated in a later commit dates from the re-statement, so this
    under-reports rather than over-reports — the safe direction for a metric
    that triggers a coordination defect.

    ⛔ **`baseline` is an argument rather than a call**, for the reason B-144
    established in this file: a value read inside a function is a hidden input,
    and the caller reads it once so that every row in one pass is measured
    against one instant rather than against whatever the clock said in turn.
    """
    if baseline is None:
        return 0.0
    if not task.declared or task.declared == "(none)":
        return 0.0
    stamp = _git(
        "log", "--format=%cI", "-1", "-S", f"`{task.declared}`", "--", "docs/BACKLOG.md"
    )
    if not stamp:
        return 0.0
    try:
        then = datetime.fromisoformat(stamp)
    except ValueError:
        return 0.0
    # **Clamped at zero.** A row whose state commit is *newer* than the
    # baseline is one written since the last integration — normal on a Product
    # Office branch, and a negative age would read as nonsense.
    return max(0.0, round((baseline - then).total_seconds() / 86400, 1))


_LANE_BRANCH = {
    "Lane A": "origin/lane-a-product-surface",
    "Lane B": "origin/lane-b-commercial-profile",
    "Lane C": "origin/lane-c-sync",
}


def _unpushed(lane: str) -> int | None:
    """Commits on a lane's branch that `integration` does not have.

    **The structural test behind `awaiting_qe_transition`.** ⛔ **Not a proxy
    and not a count of anything textual**: a lane with zero commits ahead of
    `integration` has handed everything over, whatever its rows say.

    Returns `None` when the branch cannot be read, so an unknown is never
    silently reported as a zero.
    """
    branch = _LANE_BRANCH.get(lane)
    if not branch:
        return None
    out = _git("rev-list", "--count", f"origin/integration..{branch}").strip()
    return int(out) if out.isdigit() else None


#: States a lane sets only when its responsibility for the row has **ended**.
#: §20e: `IN VALIDATION` means *"implementation, tests, module documentation and
#: Slice Handoff are all complete."* ⛔ `CLAIMED` and `IN PROGRESS` are not here.
_HANDED_OVER = frozenset({"IN VALIDATION", "VERIFIED", "CERTIFIED"})


def _outstanding_rows(rows: list[Task]) -> frozenset[str]:
    """Ids with a commit on their lane's branch that `integration` lacks.

    ⚡ **Every git call `_delivered` used to make, hoisted to one place** —
    [B-139](../docs/BUGS.md). **The predicate is now a pure function of its
    arguments and this is the only part that reads the clone**, so a test can
    state the world it wants instead of depending on which refs the machine
    happens to have.
    """
    out: set[str] = set()
    for lane, branch in _LANE_BRANCH.items():
        ids = [r.id for r in rows if r.lane == lane]
        if not ids:
            continue
        # ⛔ **`git cherry`, not `git log` — 2026-08-07.** This read
        # `log origin/integration..<branch>`, which is **hash reachability**:
        # after a lane rebases, its commits get new hashes and every one of
        # them reads as outstanding even when the identical content is already
        # upstream. ⚡ **`git cherry` compares by patch-id and prefixes `-` for
        # a commit that has an upstream equivalent**, so only `+` lines are
        # genuinely outstanding.
        #
        # **Found by content, on `TASK-479`.** `people/public/__init__.py` is
        # **byte-identical** on `origin/integration` and
        # `origin/lane-b-commercial-profile` — same blob `56b848f4edd5` — while
        # four commits naming `TASK-457` still showed as ahead. **The row was
        # held against a contract that had already landed.**
        #
        # ⚠️ **This is the proxy Lane B named in [C-235](../docs/LANE_COORDINATION.md)**:
        # *"reachability was the proxy; ref-equality is now the proxy; neither
        # is the property."* **Patch equivalence is nearer the property, and
        # `git cherry` is what already computes it.**
        unmerged = [
            line[2:]
            for line in _git("cherry", "origin/integration", branch).splitlines()
            if line.startswith("+")
        ]
        subjects = "\n".join(
            _git("log", "--format=%s%n%b", "-1", sha.strip()) for sha in unmerged if sha.strip()
        )
        out |= {i for i in ids if i in subjects}
    return frozenset(out)


def _delivered(dep: str, by_id: dict[str, Task], outstanding: frozenset[str]) -> bool:
    """Has this predecessor's work actually been handed over?

    ⚡ **The predicate that ends the sweep this was written after.** On
    2026-08-07 both implementation lanes reported themselves idle while
    twenty-two rows sat `SEQUENCED`, and **every root of that wall was a
    predecessor whose work was already on `main`** — `TASK-432`, `TASK-448`,
    `TASK-449`, `TASK-457`, `TASK-461`. **The rows were correct when written
    and nobody re-asked**, because the only thing that would have moved them is
    `VERIFIED`, which is QE's exclusively (§20e, [D-123](../docs/DECISION_REGISTER.md)).

    ⛔ **The first version of this asked `git log origin/main --grep=TASK-nnn`
    and was wrong.** A grep matches every commit that *mentions* an id —
    including the commit that wrote the row — so **every task ever discussed on
    `main` read as delivered**, and it reported six rows unblocked that were
    not. ⚠️ **[B-101](../docs/BUGS.md)'s class, inside the function written to
    end it**, and the reason it is named here rather than quietly repaired.

    **What replaced it, and both halves are required:**

    **①** the row declares a state a lane sets **only when it has handed over**
    — `IN VALIDATION`, `VERIFIED`, `CERTIFIED`; ⛔ never `CLAIMED` or
    `IN PROGRESS`, which mean somebody is holding it right now — and
    **②** that lane's branch carries no commit **naming this row** that
    `integration` lacks.

    ⚡ **② is what stops a declaration being taken at its word.** A row can say
    `IN VALIDATION` while the branch still carries it; the branch cannot lie.

    ⚠️ **② was lane-scoped and is now row-scoped — corrected 2026-08-07.**
    *"The lane's branch carries nothing"* meant **a lane starting any new work
    made every finished row it owned read as undelivered.** `TASK-427` flipped
    from delivered to not-delivered because Lane B pushed `TASK-462`, which
    has nothing to do with it. ⛔ **A predicate about one row must not depend
    on what else its author is doing.**

    ⛔ **`outstanding` is an argument, and it was a `git log` inside this
    function — [B-139](../docs/BUGS.md), found by QE.** The C-428 change made
    the answer come from real refs in the running clone while the signature
    still took `ahead`, **which the body never read**. ⚡ **So the test did not
    test the function — the parametrised case would pass or fail identically
    with the argument deleted — and the result varied by workstation.** **It
    passed where it was written and failed where it was run.**

    ⚠️ **[§2](../../CLAUDE.md), by name: *hidden inputs are architecture
    defects* — an input that influences behaviour without being part of the
    declared contract makes the same declared inputs produce different
    results.** **Every git call now happens in `_outstanding_rows()`, once, at
    the caller.**

    ⚡ **The `--grep` is deliberate and lives there now.** [B-101](../docs/BUGS.md)
    bites when a grep is asked *"was this delivered?"* — it matches every
    mention, including the commit that wrote the row. **Asked *"is there
    outstanding work for this?"* a spurious match reads as *not delivered*,
    which is the conservative direction.** **The same tool, and the safety
    depends entirely on which way a false match falls.**

    **A predecessor absent from the graph is delivered** — the generator drops
    `DONE`, `DISPOSED` and `PROMOTED`, so absence here means closed.
    """
    row = by_id.get(dep)
    if row is None:
        return True
    if not any(s in row.declared for s in _HANDED_OVER):
        return False
    return dep not in outstanding


def stale_sequencing(rows: list[Task], outstanding: frozenset[str]) -> list[Task]:
    """Rows parked behind a predecessor that has already been handed over.

    ⛔ **Reports; never reclassifies.** **A `SEQUENCED` row is a Product Office
    judgement**, and a generator that silently promoted one would be making a
    fitness decision inside a projection — the *"editing this file makes it
    wrong rather than true"* defect wearing the opposite coat.

    ⚡ **`outstanding` is declared, not fetched** — [B-144](../docs/BUGS.md).
    See `premature_releases` for why all three of these take it.
    """
    by_id = {r.id: r for r in rows}
    return [
        r
        for r in rows
        if r.state in {SEQUENCED, BLOCKED}
        and r.depends_on
        and all(_delivered(dep, by_id, outstanding) for dep in r.depends_on)
    ]


def premature_releases(rows: list[Task], outstanding: frozenset[str]) -> list[Task]:
    """Rows this office set `READY` whose predecessor is **not** handed over.

    ⛔ **`outstanding` is an argument because a gate must answer the same way
    twice — [B-144](../docs/BUGS.md), found by QE.** **This called
    `_outstanding_rows()` internally**, which shells out to `git cherry` and
    greps commit *messages* for task ids. ⚡ **So the answer depended on which
    refs the running clone happened to have fetched, and on what other lanes
    had recently typed in a commit body.** **`origin/main` went from green to
    red with no change to the repository at all**: Lane A pushed `9aa88841`,
    whose body mentions `TASK-432`, and a test building two `Task` objects from
    fixed text started failing. **Same tree, same command, different answer.**

    ⚠️ **This is [B-139](../docs/BUGS.md) relocated rather than resolved, and
    `_outstanding_rows`'s own docstring said so** — *"this is the only part
    that reads the clone, so a test can state the world it wants"*. **That was
    true of `_delivered` and false of every caller of it**, because the hidden
    input had simply moved up one frame and stayed in the call path. ⛔ **The
    repair is applied to all three siblings at once** — `stale_sequencing` and
    `blocked_on_integration` had the identical defect and no test had caught
    them yet. **Fixing only the one the test found is how a hidden input moves
    up one frame a second time.**

    ⚡ **[§2](../../CLAUDE.md), by name: *hidden inputs are architecture
    defects*** — *"it makes the same declared inputs produce different results,
    which defeats replay, regression testing, and every guarantee proven by
    removal."* **A certification gate is exactly where that costs most: a run
    that cannot be reproduced is not evidence.**

    ⚡ **The mirror of `stale_sequencing`, and the half that was missing.**
    That check asks *"is this row parked behind work that is finished?"* — it
    only ever looks at rows still `SEQUENCED`, **so a row released in error
    left its scope the moment the error was made.**

    **`TASK-458`, 2026-08-07.** Released on the reasoning *"`TASK-457` has 6
    commits on `main` and nothing outstanding"* — the `--grep` count that
    [C-427](../docs/LANE_COORDINATION.md) records as B-101's class. `TASK-457`
    is `CLAIMED`: Lane B is holding it, and `people/public/__init__.py` is
    **zero lines**. ⛔ **Lane A found it by opening the file.**
    """
    by_id = {r.id: r for r in rows}
    return [
        r
        for r in rows
        if r.state == ASSIGNED
        and r.depends_on
        and not all(_delivered(dep, by_id, outstanding) for dep in r.depends_on)
    ]


def blocked_on_integration(
    rows: list[Task], lane: str, outstanding: frozenset[str]
) -> list[Task]:
    """This lane's parked rows that would release if QE integrated its own work.

    ⚡ **The distinction the product owner had to ask for, 2026-08-07.** Lane A
    read `claimable = 0` and `current = ""` for four cycles and was reported as
    *not idle* each time — **but nothing in the source said what it was waiting
    on, so *"0 claimable"* and *"starved"* looked identical.**

    ⛔ **They are opposites.** **A starved lane needs planning; a lane waiting on
    integration needs QE, and giving it more rows would be padding.** Lane A had
    shipped four slices in the previous two hours and every one of its next four
    rows sat behind two of them.

    ⚠️ **[C-426](../docs/LANE_COORDINATION.md)'s class exactly**, one level up:
    that was a metric saying *busy* about an idle lane; this is a metric saying
    *nothing to do* about a lane blocked on release.

    ⚡ **`outstanding` is declared, not fetched** — [B-144](../docs/BUGS.md).
    See `premature_releases` for why all three of these take it.
    """
    by_id = {r.id: r for r in rows}
    return [
        r
        for r in rows
        if r.lane == lane
        and r.state in {SEQUENCED, BLOCKED}
        and r.depends_on
        and all(
            (p := by_id.get(dep)) is not None
            and p.lane == lane
            and p.state == IN_FLIGHT
            and dep in outstanding
            for dep in r.depends_on
        )
    ]


def metrics_for(rows: list[Task]) -> dict[str, dict[str, float | int | str]]:
    """Per-lane coordination metrics — [D-143](../docs/DECISION_REGISTER.md) §6.

    ⛔ **`idle_prediction` is the one that matters and the one to read
    carefully.** It divides claimable rows by an observed claim rate, so it is
    a projection of a past week onto a future one. **A lane at zero claimable
    reports `0.0` days, which is not a prediction — it is a statement that
    starvation has already happened.**
    """
    out: dict[str, dict[str, float | int | str]] = {}
    # **Read once, before the loop** — B-144. The clone is consulted here and
    # nowhere below, so every lane in this pass is measured against one world
    # rather than against whatever the refs said when its turn came.
    outstanding = _outstanding_rows(rows)
    for lane in sorted({r.lane for r in rows if r.lane != "—"}):
        mine = [r for r in rows if r.lane == lane]
        claimable = [r for r in mine if r.state == ASSIGNED]
        in_flight = [r for r in mine if r.state == IN_FLIGHT]
        blocked = [r for r in mine if r.state not in {ASSIGNED, IN_FLIGHT}]
        waits = [r.blocked_days for r in blocked if r.blocked_days]
        # **The first thing v1 got wrong in real use, and a lane found it.**
        # `lane_utilization` read 3.6 for a lane with nothing to do, because
        # every row a lane had handed to QE still counted as work in progress.
        # A row at `IN VALIDATION` on a lane whose branch is level with
        # `integration` has nothing outstanding to validate — it is waiting on
        # a state transition only QE may write (§20e), not on engineering.
        ahead = _unpushed(lane)
        stranded = len(in_flight) if ahead == 0 else 0
        working = len(in_flight) - stranded
        pending = len(blocked_on_integration(rows, lane, outstanding))
        # ⛔ **Never let "0 claimable" stand alone.** It is the same number for
        # a starved lane and for one whose next rows are behind its own
        # finished work, and those need opposite responses.
        supply = (
            "working" if claimable
            else "blocked_on_integration" if pending
            else "in_flight_only" if in_flight
            else "starved"
        )
        claimable_now = [r for r in claimable if r.on_integration]
        out[lane] = {
            "claimable_now": len(claimable_now),
            "awaiting_sync": len(claimable) - len(claimable_now),
            "blocked_on_integration": pending,
            "supply_state": supply,
            "claimable": len(claimable),
            "in_flight": len(in_flight),
            # ⚡ **B-409** — the number a starvation check must read. `in_flight`
            # counts eight declared states and only three are work the lane can
            # touch; `IN VALIDATION` has left it entirely (§20e).
            "actionable": sum(1 for r in mine if r.declared in _ACTIONABLE),
            "awaiting_qe_transition": stranded,
            "blocked": len(blocked),
            # **In flight against a five-slice reference**, which is §20e's own
            # number rather than one invented here.
            "lane_utilization": round(working / 5, 2),
            # Claimable ÷ the rate a lane has actually claimed at. **Lane A
            # took seven rows in one day**, so 7/day is measured, not assumed.
            "idle_prediction_days": round(len(claimable) / 7, 1),
            "dependency_wait_days": round(max(waits, default=0.0), 1),
            "blocked_duration_days": round(sum(waits) / len(waits), 1) if waits else 0.0,
            "critical_path_max": max((r.critical_path for r in mine), default=0),
        }
    return out


NOTICES = ROOT / "docs" / "coordination" / "notices.toml"


#: **The projection is a pointer, not a document** — D-144. A notice longer
#: than this belongs in the backlog row, which is where a lane reads detail.
_NOTICE_MAX = 400


def _notice(lane: str, reachable: frozenset[str] | set[str] = frozenset()) -> str:
    """The one thing this lane must know that `BACKLOG.md` cannot tell it.

    ⚡ **`origin/coordination` is the ONLY channel that reaches a lane without
    QE** ([D-144](../docs/DECISION_REGISTER.md)), and this office kept writing
    urgent answers into `queues/lane-a.toml` — **a file a lane reads from
    `integration`, which is exactly the ref the answer is stuck behind.**

    ⛔ **The cost was concrete on 2026-08-08.** Lane A filed [B-214](../docs/BUGS.md)
    and asked for a backlog row. It needs none — `workspace_tenancy` is its own
    module and §20e's 🟢 tier covers *a bug fix inside it*. **That answer sat on
    `lane-c-sync` while Lane A reported the same blocker twice.**

    ⚠️ **One line, deliberately.** A notice that grows into a message log becomes
    a second coordination register, and `LANE_COORDINATION.md` is the first.
    **It carries the answer and points at where the reasoning lives.**
    """
    if not NOTICES.exists():
        return ""
    try:
        text = str(tomllib.loads(NOTICES.read_text()).get(lane, {}).get("notice", ""))
    except tomllib.TOMLDecodeError:
        return ""

    # ⛔ **A notice may carry REASONING. It may never carry STATE — B-216.**
    #
    # 🔴 **Lane A found this on the poll it was published.** The notice read
    # *"TASK-1400 is READY"* while `BACKLOG.md` on `integration` read
    # `SEQUENCED`, **and the tell was three lines below it in the same block:
    # `current = ""` and `claimable_now = 0`.** The counters agreed with the
    # backlog and the prose did not.
    #
    # ⚠️ **Third instance of one class** — [B-148](../docs/BUGS.md),
    # [B-152](../docs/BUGS.md), this — **and every time a projection asserted a
    # state the backlog did not carry.** ⛔ **Twice this office fixed the
    # instance; the class only closes if a projection CANNOT say it.**
    #
    # ✅ **So the state words are refused rather than discouraged.** A notice
    # that names one is dropped and replaced by a pointer to the authority,
    # because [D-144](../docs/DECISION_REGISTER.md) is explicit: *"if the
    # coordination source disagrees with `BACKLOG.md`, the backlog wins."*
    banned = re.search(
        r"\b(is|are|now)\s+`?(READY|CLAIMED|SEQUENCED|BLOCKED|IN PROGRESS|"
        r"IN VALIDATION|PROMOTED|DONE)`?\b", text, re.I)
    if banned:
        return (f"NOTICE WITHHELD — it asserted a task state ('{banned.group(0)}'), "
                f"which only BACKLOG.md may do (D-144, B-216). Read the backlog on "
                f"origin/integration for state; read queues/lane-*.toml for reasoning.")
    # ⛔ **A truncated notice used to end mid-word with nothing to show it had
    # been cut — D-204 §8.** A 1,400-character notice arrived as 400 characters
    # ending in *"so"*, and **the reader has no way to know a sentence is
    # missing**, which is worse than no notice: a partial instruction reads as a
    # complete one. ✅ **The cap stays** — a projection is not a document — **but
    # it now says so, and names where the rest lives.**
    # ⛔ **A notice may not name a row this lane cannot reach — B-221.**
    #
    # 🔴 **Three instances on three consecutive publishes**, and QE's diagnosis
    # is the exact one: *"the array is right every time and the prose is wrong
    # every time — `backlog` is computed from what is SYNCHRONIZED, the notice
    # from what was AUTHORED."*
    #
    # ⚡ **And the third instance had a second cause worth more than the first**:
    # `TASK-1431` is `platform_foundation`, which is **Lane C's own module**, and
    # the notice told Lane A it was *"yours today"*. ⛔ **Not a lag — this office
    # handing its own work to another lane on the one channel that bypasses QE.**
    # ✅ **The reachable set is per-lane, so the guard catches both causes.**
    #
    # ⚡ **Widened from *claimable* to *this lane's, on `integration`* — 2026-08-10.**
    # ⛔ **It was the lane's `backlog` array, which is `ASSIGNED and on_integration`**,
    # so a notice could not name a row the lane was **blocked** on — and answering a
    # blocker is exactly what a notice is for. 🔴 **Measured: Lane A raised `C-269`
    # against `TASK-1439`, released the claim, and this office's answer was withheld
    # for naming the row Lane A had itself asked about.**
    #
    # ✅ **Both recorded causes are untouched, which is why this is safe.** B-221's
    # own diagnosis names them: *"`backlog` is computed from what is SYNCHRONIZED,
    # the notice from what was AUTHORED"* — **an unintegrated row still fails
    # `on_integration`** — and *"this office handing its own work to another lane"*
    # — **another lane's row is still not in `mine`.** ⛔ **What is no longer
    # refused is the one case neither cause covers: this lane's own integrated row,
    # in whatever state the backlog carries it.** **State words remain banned
    # above**, so a notice still cannot say what that state *is*.
    named = set(re.findall(r"TASK-\d+", text))
    unreachable = sorted(named - set(reachable))
    if unreachable:
        return (
            f"NOTICE WITHHELD — it names {', '.join(unreachable)} as work for this lane, "
            f"and none of them is in this lane's computed backlog (D-144, B-221). Either "
            f"the row is not yet integrated, or it belongs to another lane. Read the "
            f"backlog array in this file for what is actually claimable."
        )

    text = text.replace('"', "'")
    if len(text) <= _NOTICE_MAX:
        return text
    cut = text[:_NOTICE_MAX].rsplit(" ", 1)[0]
    return (f"{cut} […TRUNCATED at {_NOTICE_MAX} chars. The full reasoning is in "
            f"docs/coordination/notices.toml, and the DETAIL belongs in the backlog "
            f"rows themselves (D-204 §6) — read those.]")


def render(rows: list[Task]) -> str:
    lanes = sorted({r.lane for r in rows if r.lane != "—"})
    out = [
        "# THE CANONICAL COORDINATION SOURCE — generated, never hand-edited.",
        "#",
        "# Every implementation lane reads this file and nothing else to learn what",
        "# to build next (479, D-142). It is a projection of BACKLOG.md,",
        "# modules.toml and LANE_COORDINATION.md — those stay authoritative, and",
        "# editing this file by hand makes it wrong rather than making it true.",
        "#",
        "# Regenerate: python3 infra/coordination.py",
        "",
        "[meta]",
        'generator      = "infra/coordination.py"',
        # **`origin/integration`, not `HEAD` — B-134.** [479](../docs/architecture/479-coordination-architecture.md)
        # §2 specified *"the integration commit the projection was taken at"*
        # and this line read `HEAD`, which made `--check` **unable to pass by
        # construction**: regenerating stamped the current `HEAD`, committing
        # the file moved `HEAD`, and the next comparison re-rendered a
        # different stamp. ⛔ **The file recorded a value that writing the file
        # invalidated.** ⚡ QE found it on a detached checkout with nothing
        # stale — the honest steady state, where it fails every time.
        f'generated_from = "{_git("rev-parse", "--short=7", "origin/integration") or "unknown"}"',
        f"task_count     = {len(rows)}",
        "",
    ]
    stats = metrics_for(rows)
    for lane in lanes:
        mine = [r for r in rows if r.lane == lane]
        # **The pipeline, three deep** — D-143 §4. Ordered by shallowest
        # critical path first: a row with nothing in front of it is the one a
        # lane can start now, and the ordering is the graph's, not a preference.
        # **Leverage first, then depth, then id — corrected 2026-08-07.**
        # The first version sorted by `(critical_path, id)` alone. ⚠️ Every
        # claimable row sits at depth 0 by definition — nothing unfinished
        # precedes a startable row — **so the tiebreak was doing all the work
        # and the tiebreak was the id.** `TASK-441` came first because 441 <
        # 478, while `TASK-478` releases three rows and 441 releases none.
        # **A queue ordered by identifier is not an ordering**, and the whole
        # point of holding a dependency graph is to know which row buys the
        # most. **This is also what made the queue files and this source
        # disagree**: the queue was hand-ordered by leverage and correct.
        # ⛔ **A row a lane cannot claim yet is not `current` — 2026-08-07.**
        # This source is generated from `lane-c-sync` and read by lanes that
        # claim against `integration`. **Lane A was told to start `TASK-451`
        # while `integration` still read `SEQUENCED`**, and a claim on it would
        # have contradicted the authoritative backlog ([C-425](../docs/LANE_COORDINATION.md)).
        # ⚡ **Ordering by `on_integration` first keeps every benefit of the
        # ref — a lane still sees the row coming — while `current` stays
        # something it can act on today.**
        # ⛔ **`current` may only name a row a lane can ACTUALLY claim — B-152.**
        #
        # 🔴 **Reported by Lane A on 2026-08-09, and it had survived a
        # republication after Lane A said it would file it if it did.** The
        # source advertised `current = TASK-470` while `origin/integration`
        # carried that row as `BLOCKED` — **Lane A had released the claim and
        # this office's branch still said `READY`.**
        #
        # ⚡ **The old sort merely PREFERRED on-integration rows.** With none
        # available it named an off-integration one anyway, which is the
        # [C-425](../docs/LANE_COORDINATION.md) defect the `on_integration`
        # field was added to prevent: *"the ref does not get to be ahead; it
        # gets to be fast."* ⛔ **A preference is not a constraint.**
        #
        # ✅ **Now a filter.** A lane's `current` is empty when nothing is
        # claimable on `integration`, and `claimable` reports what this branch
        # holds so the gap is visible rather than hidden. **An empty `current`
        # beside a non-zero `claimable` says exactly the true thing: work
        # exists and QE has not integrated it.**
        # ⛔ **`current` / `next` / `next_after_that` were REMOVED here, D-203 §2.**
        #
        # [D-198](../docs/DECISION_REGISTER.md) ended dispatching and D-199
        # required it implemented exactly. **The queue FILES lost those fields;
        # this projection went on publishing them to every lane** — so the
        # dispatcher model stayed on the wire for four days after the model that
        # produced it was retired. ⚡ **A field a lane reads is the model, whatever
        # a document says**, and the governance cleanup is where that was caught.
        #
        # ✅ **`backlog` replaces them: EVERY claimable row, in the recommended
        # order, with no row singled out as *the* one.** ⛔ The order is a
        # recommendation and carries no authority over the lane's sequencing —
        # which is precisely why naming a first element as `current` was wrong.
        backlog = sorted(
            (r for r in mine if r.state == ASSIGNED and r.on_integration),
            key=lambda r: (-len(r.unblocks), r.critical_path, r.id),
        )
        m = stats[lane]
        out += [
            f"[lane.{lane.replace(' ', '_')}]",
            f'notice             = "{_notice(lane, {r.id for r in mine if r.on_integration})}"',
            "backlog            = [" + ", ".join(f'"{r.id}"' for r in backlog) + "]",
            f"assigned_total     = {len(mine)}",
            f"claimable          = {m['claimable']}",
            f"claimable_now      = {m['claimable_now']}",
            f"awaiting_sync      = {m['awaiting_sync']}",
            f"in_flight          = {m['in_flight']}",
            f"actionable         = {m['actionable']}",  # ⚡ B-409 — what a starvation check must read
            f"awaiting_qe_transition = {m['awaiting_qe_transition']}",
            f"blocked_on_integration = {m['blocked_on_integration']}",
            f'supply_state       = "{m["supply_state"]}"',
            f"blocked            = {m['blocked']}",
            f"lane_utilization   = {m['lane_utilization']}",
            f"idle_prediction_days   = {m['idle_prediction_days']}",
            f"dependency_wait_days   = {m['dependency_wait_days']}",
            f"blocked_duration_days  = {m['blocked_duration_days']}",
            f"critical_path_max      = {m['critical_path_max']}",
            "",
        ]
    for row in sorted(rows, key=lambda r: (r.lane, r.id)):
        out += [
            "[[task]]",
            f'id            = "{row.id}"',
            f'title         = "{row.title.replace(chr(34), chr(39))}"',
            f'state         = "{row.state}"',
            f'declared      = "{row.declared}"',
            f'lane          = "{row.lane}"',
            "depends_on     = " + str(row.depends_on).replace("'", '"'),
            "unblocks       = " + str(row.unblocks).replace("'", '"'),
            "next_owner     = " + str(row.next_owner).replace("'", '"'),
            f'next_lane      = "{row.next_lane}"',
            f"critical_path  = {row.critical_path}",
            f'estimated_ready = "{row.estimated_ready.replace(chr(34), chr(39))[:110]}"',
            f'waiting_for    = "{row.waiting_for.replace(chr(34), chr(39))[:150]}"',
            f"blocked_days   = {row.blocked_days}",
            f"on_integration = {str(row.on_integration).lower()}",
            "",
        ]
    return "\n".join(out)


def _content(source: str) -> str:
    """The part of the source that staleness is actually about.

    ⛔ **`[meta]` is provenance, not content** — it says *when* and *from what*,
    and comparing it makes the check answer a different question from the one
    it asks. **Belt and braces with the `origin/integration` stamp above**: that
    fix alone would leave `--check` failing whenever `integration` moved, even
    though every task and every metric was still correct, and a check that
    reports *stale* about an accurate file teaches a reader to ignore it.

    **B-134**, found by QE. ⚠️ **I reported this instrument clean last cycle.**
    It was — for the minutes between regenerating and committing, which is
    exactly the window I ran it in. **Running a check only where it passes is
    not running it.**
    """
    body = source.split("\n[lane.", 1)
    return body[1] if len(body) > 1 else source


COORD_REF = "coordination"

#: ⚡ **`BACKLOG.md` joined the contract on 2026-08-10 — TASK-497, under
#: [D-181](../docs/DECISION_REGISTER.md) §6 ruling [C-435](../docs/LANE_COORDINATION.md)
#: Option 3.** [491 §3](../docs/architecture/491-planning-synchronization-architecture.md)
#: states it exactly: *"`BACKLOG.md` moves to `origin/coordination`.
#: `ACTIVE_ASSIGNMENTS.md` stays on `integration`."*
#:
#: 🔴 **The problem it closes.** `coordination.toml` already carries everything a
#: lane needs to *choose* — the backlog array, the dependency graph, the metrics.
#: **What it does not carry is a row's SCOPE**, which is what [§20e](../CLAUDE.md)
#: step 3b sends a lane to `BACKLOG.md` for — **and `BACKLOG.md` reaches a lane
#: only when QE integrates.** So a lane could see *which* row was next at poll
#: cadence and *what it was* only at release cadence.
#:
#: ⛔ **`ACTIVE_ASSIGNMENTS.md` is deliberately absent and must stay absent.**
#: Eligibility (*is this claimable*) and arbitration (*did I claim it first*) are
#: different facts: **one author versus two lanes racing, and only a push to a
#: shared ref is atomic.** A Product Office write to the board could overwrite a
#: lane's claim, which is [D-123](../docs/DECISION_REGISTER.md)'s defect. The
#: `--self-test` proves the guard refuses it rather than trusting this comment.
COORD_CONTRACT = ("BACKLOG.md", "README.md", "coordination.toml")
COORD_SECTIONS = ("meta", "lane", "task")

#: Paths the ref must never carry, checked by name so a rename cannot smuggle one
#: past a count. **`ACTIVE_ASSIGNMENTS.md` is the arbitration point** (above);
#: the rest are the executable surfaces that make this a planning ref rather than
#: a second `integration`.
COORD_FORBIDDEN = ("ACTIVE_ASSIGNMENTS.md", "Makefile", "conftest.py")


def _coordination_findings(tree: str, ref: str) -> list[str]:
    """Everything that must hold before a tree may become `origin/coordination`.

    ⚡ **D-181, and it is written from the failure rather than from foresight.**
    On 2026-08-08 this office pushed the *entire repository tree* onto this ref
    with a hand-rolled `git push`, and the tell was hidden by a `|| echo`
    fallback that made a successful wrong push read like a handled skip. Every
    lane's poll — `git show origin/coordination:coordination.toml` — returned
    `fatal: path does not exist` until it was restored.

    ⛔ **The root cause was not the push; it was that a push existed to hand-roll
    at all.** So the fix is not a warning added beside the old procedure — it is
    that publishing is now one command that refuses to run on a tree that is not
    the contract. **A guard that cannot fail is documentation pretending to be
    code** (§2), and this one is proved able to fail by `--self-test`.

    ⚠️ **The repository-tree case is checked by *name*, deliberately.** A count
    alone would pass a two-file tree holding the wrong two files, and a
    contamination check that looks only for `backend/` would pass a tree whose
    contamination happened to be a `Makefile`.
    """
    findings: list[str] = []

    if ref != COORD_REF:
        findings.append(
            f"destination is `{ref}`, and the only ref this publishes to is "
            f"`{COORD_REF}`. **A planning projection pushed anywhere else is "
            f"either invisible or destructive.**"
        )

    entries = _git("ls-tree", "-r", "-t", "--format=%(objecttype) %(path)", tree)
    listed = [line.split(" ", 1) for line in entries.splitlines() if line]
    names = sorted(path for kind, path in listed if kind == "blob")
    subtrees = sorted(path for kind, path in listed if kind == "tree")

    if subtrees:
        findings.append(
            f"the tree carries {len(subtrees)} director(ies) — {', '.join(subtrees[:6])}. "
            f"**The coordination ref is flat by contract; a directory here means a "
            f"repository tree is being published, which is exactly the 2026-08-08 defect.**"
        )
    # ⛔ **Named refusals first, so the message says WHICH rule was broken.**
    # `unexpected` below would already catch these — but it reports *"unexpected
    # file"*, and `ACTIVE_ASSIGNMENTS.md` reaching this ref is not an untidy
    # tree, it is the arbitration point being overwritten by the one author who
    # must never hold it. **A guard whose message does not name the invariant
    # teaches nobody why it fired.**
    forbidden = [n for n in names if n in COORD_FORBIDDEN]
    if forbidden:
        findings.append(
            f"{len(forbidden)} forbidden path(s) — {', '.join(forbidden)}. "
            f"**`ACTIVE_ASSIGNMENTS.md` is the claim protocol's arbitration point and "
            f"stays on `integration` (D-181 §6, Option 3): eligibility has one author, "
            f"arbitration has two lanes racing, and only a push to a shared ref is "
            f"atomic.** A planning publish that carried it could overwrite a claim."
        )
    unexpected = [n for n in names if n not in COORD_CONTRACT]
    if unexpected:
        findings.append(
            f"{len(unexpected)} unexpected file(s) — {', '.join(unexpected[:6])}"
            + (" …" if len(unexpected) > 6 else "")
            + f". **The contract is exactly {', '.join(COORD_CONTRACT)}.**"
        )
    missing = [n for n in COORD_CONTRACT if n not in names]
    if missing:
        findings.append(
            f"{len(missing)} contract file(s) absent — {', '.join(missing)}. "
            f"**`coordination.toml` missing is a broken poll for every lane; "
            f"`README.md` missing is a ref nobody arriving cold can read.**"
        )

    if "coordination.toml" in names:
        raw = _git("cat-file", "blob", f"{tree}:coordination.toml")
        try:
            parsed = tomllib.loads(raw)
        except tomllib.TOMLDecodeError as exc:
            findings.append(f"`coordination.toml` does not parse — {exc}")
        else:
            absent = [s for s in COORD_SECTIONS if s not in parsed]
            if absent:
                findings.append(
                    f"`coordination.toml` parses but has no {', '.join(absent)} section. "
                    f"**A lane reads `[lane.<its own>]`; a file without one answers nothing.**"
                )
    return findings


def _publish(dry_run: bool) -> int:
    """Build the two-file tree, validate it, and only then move the ref."""
    readme = _git_strict("rev-parse", f"origin/{COORD_REF}:README.md")
    toml_blob = _git_strict("hash-object", "-w", str(OUT))
    # ⚡ **The backlog travels with the projection — TASK-497.** A lane polling
    # this one ref now gets ORDER (`coordination.toml`'s backlog array) and
    # SCOPE (the row itself) together, instead of the first at poll cadence and
    # the second at QE's.
    backlog_blob = _git_strict("hash-object", "-w", str(BACKLOG))
    tree = _git_strict(
        "mktree",
        stdin=(f"100644 blob {backlog_blob}\tBACKLOG.md\n"
               f"100644 blob {readme}\tREADME.md\n"
               f"100644 blob {toml_blob}\tcoordination.toml\n"),
    )

    findings = _coordination_findings(tree, COORD_REF)
    if findings:
        print("coordination: REFUSED — the candidate tree is not the contract", file=sys.stderr)
        for f in findings:
            print(f"  · {f}", file=sys.stderr)
        return 1

    parent = _git("rev-parse", f"origin/{COORD_REF}")
    if _git("rev-parse", f"{parent}^{{tree}}") == tree:
        print(f"coordination: already published at {parent[:8]} — nothing to do")
        return 0

    print(f"coordination: tree {tree[:8]} validated — "
          f"{', '.join(COORD_CONTRACT)}, no subtrees, parses, {len(COORD_SECTIONS)} sections")
    if dry_run:
        print(f"coordination: --dry-run, not pushing. Parent would be {parent[:8]}")
        return 0

    message = (f"Coordination republished — {len(tasks())} task(s)\n\n"
               f"Validated against the D-181 contract before the ref moved: "
               f"{', '.join(COORD_CONTRACT)}, no subtrees, parses, "
               f"{len(COORD_SECTIONS)} sections, destination `{COORD_REF}`.\n")
    commit = _git_strict("commit-tree", tree, "-p", parent, stdin=message)
    _git_strict("push", f"--force-with-lease={COORD_REF}:{parent}",
                "origin", f"{commit}:{COORD_REF}")
    print(f"coordination: published {commit[:8]} → origin/{COORD_REF}")
    return 0


def _self_test() -> int:
    """⚡ Prove the guard fails on the case that caused D-181, not only that it passes."""
    # ⚡ **A tree carrying the arbitration point — TASK-497.** Built here rather
    # than described, because the whole of D-181 §6 Option 3 rests on
    # `ACTIVE_ASSIGNMENTS.md` never reaching this ref, and a claim in a comment
    # is not a guarantee. **The blob content is irrelevant; the NAME is the
    # violation**, so the board's own current blob is used.
    board = _git("rev-parse", "HEAD:docs/ACTIVE_ASSIGNMENTS.md")
    readme = _git("rev-parse", f"origin/{COORD_REF}:README.md")
    toml = _git("rev-parse", f"origin/{COORD_REF}:coordination.toml")
    backlog = _git("rev-parse", "HEAD:docs/BACKLOG.md")
    with_board = _git_strict("mktree", stdin=(
        f"100644 blob {backlog}\tBACKLOG.md\n"
        f"100644 blob {board}\tACTIVE_ASSIGNMENTS.md\n"
        f"100644 blob {readme}\tREADME.md\n"
        f"100644 blob {toml}\tcoordination.toml\n")) if board else ""
    # ⛔ **And a tree with the backlog MISSING**, which is the other half of the
    # widened contract: after TASK-497 a lane polls this ref for scope, so a
    # publish without it is a lane that can see an order and not the work.
    without_backlog = _git_strict("mktree", stdin=(
        f"100644 blob {readme}\tREADME.md\n"
        f"100644 blob {toml}\tcoordination.toml\n"))
    cases = [
        ("the repository tree itself", _git("rev-parse", "HEAD^{tree}"), COORD_REF),
        ("the correct tree, wrong destination", _git("rev-parse", f"origin/{COORD_REF}^{{tree}}"), "integration"),
        ("a tree carrying ACTIVE_ASSIGNMENTS.md — the arbitration point", with_board, COORD_REF),
        ("a tree with BACKLOG.md missing — order without scope", without_backlog, COORD_REF),
    ]
    ok = True
    for name, tree, ref in cases:
        found = _coordination_findings(tree, ref)
        print(f"  {'✅ REFUSED' if found else '🔴 ACCEPTED'}  {name}")
        for f in found:
            print(f"       · {f[:118]}")
        ok = ok and bool(found)
    good = _coordination_findings(_git("rev-parse", f"origin/{COORD_REF}^{{tree}}"), COORD_REF)
    print(f"  {'✅ ACCEPTED' if not good else '🔴 REFUSED'}  the published tree, correct destination")
    ok = ok and not good
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--publish", action="store_true",
                        help="validate against the coordination contract, then move the ref")
    parser.add_argument("--dry-run", action="store_true", help="with --publish: validate only")
    parser.add_argument("--self-test", action="store_true",
                        help="prove the publish guard refuses a repository tree")
    args = parser.parse_args()

    if args.self_test:
        return _self_test()

    rows = tasks()
    fresh = render(rows)
    tomllib.loads(fresh)  # a generator that emits unparseable TOML is worse than none

    if args.check:
        if not OUT.exists():
            print("coordination: docs/coordination/coordination.toml is missing", file=sys.stderr)
            return 1
        if _content(OUT.read_text()) != _content(fresh):
            print(
                "coordination: the published source does not match what the generator "
                "emits today — regenerate it. A stale coordination source instructs "
                "every lane with an answer that was true earlier.",
                file=sys.stderr,
            )
            return 1
        print(f"coordination: current — {len(rows)} task(s)")
        return 0

    OUT.write_text(fresh)

    if args.publish:
        # ⚡ Regenerate first, always. Publishing a stale projection is the
        # failure D-144 created this ref to prevent, and `--publish` reaching
        # for whatever happened to be on disk would reintroduce it quietly.
        try:
            return _publish(args.dry_run)
        except GitFailed as exc:
            print(f"coordination: PUBLISH FAILED — {exc}", file=sys.stderr)
            print("  · ⛔ The ref was NOT moved. **A write that fails must say so** "
                  "— D-181's root cause was a command that could not.", file=sys.stderr)
            return 1

    for lane in sorted({r.lane for r in rows if r.lane != "—"}):
        mine = [r for r in rows if r.lane == lane]
        print(f"  {lane}: {sum(1 for r in mine if r.state == ASSIGNED)} claimable "
              f"of {len(mine)} assigned")
    unplaced = [r for r in rows if r.lane == "—"]
    if unplaced:
        print(f"  ⛔ {len(unplaced)} task(s) resolve to no lane: "
              + ", ".join(r.id for r in unplaced))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

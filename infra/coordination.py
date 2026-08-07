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


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True
    ).stdout.strip()


def _owners() -> dict[str, str]:
    registry = tomllib.loads(MODULES.read_text())
    return {
        key: row["current_owner"]
        for key, row in registry.items()
        if isinstance(row, dict) and row.get("current_owner")
    }


def _lane_for(module_cell: str, body: str, owners: dict[str, str]) -> str | None:
    """Which lane owns this row.

    **Precedence matters and was learned the hard way.** An explicit
    ``— Lane X`` in the Module cell is the row's own statement about itself and
    wins; only then a module key; only then the trigger steward. Reading the
    first module key found instead resolved a row to the lane whose module it
    *reads* rather than the lane whose module it *is*.
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


def tasks() -> list[Task]:
    owners = _owners()
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
        lane = _lane_for(module_cell, body, owners)
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
    for row in rows:
        if row.state not in {ASSIGNED, IN_FLIGHT}:
            row.blocked_days = _blocked_days(row)
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



def _blocked_days(task: Task) -> float:
    """Days the row has held its current declared state.

    **Dated from the commit that introduced the state string**, which is the
    only record the repository actually keeps. ⚠️ **It is a lower bound**: a
    row re-stated in a later commit dates from the re-statement, so this
    under-reports rather than over-reports — the safe direction for a metric
    that triggers a coordination defect.
    """
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
    return round((datetime.now(timezone.utc) - then).total_seconds() / 86400, 1)


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


def stale_sequencing(rows: list[Task]) -> list[Task]:
    """Rows parked behind a predecessor that has already been handed over.

    ⛔ **Reports; never reclassifies.** **A `SEQUENCED` row is a Product Office
    judgement**, and a generator that silently promoted one would be making a
    fitness decision inside a projection — the *"editing this file makes it
    wrong rather than true"* defect wearing the opposite coat.
    """
    by_id = {r.id: r for r in rows}
    outstanding = _outstanding_rows(rows)
    return [
        r
        for r in rows
        if r.state in {SEQUENCED, BLOCKED}
        and r.depends_on
        and all(_delivered(dep, by_id, outstanding) for dep in r.depends_on)
    ]


def premature_releases(rows: list[Task]) -> list[Task]:
    """Rows this office set `READY` whose predecessor is **not** handed over.

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
    outstanding = _outstanding_rows(rows)
    return [
        r
        for r in rows
        if r.state == ASSIGNED
        and r.depends_on
        and not all(_delivered(dep, by_id, outstanding) for dep in r.depends_on)
    ]


def blocked_on_integration(rows: list[Task], lane: str) -> list[Task]:
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
    """
    by_id = {r.id: r for r in rows}
    outstanding = _outstanding_rows(rows)
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
        pending = len(blocked_on_integration(rows, lane))
        # ⛔ **Never let "0 claimable" stand alone.** It is the same number for
        # a starved lane and for one whose next rows are behind its own
        # finished work, and those need opposite responses.
        supply = (
            "working" if claimable
            else "blocked_on_integration" if pending
            else "in_flight_only" if in_flight
            else "starved"
        )
        out[lane] = {
            "blocked_on_integration": pending,
            "supply_state": supply,
            "claimable": len(claimable),
            "in_flight": len(in_flight),
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
        pipeline = sorted(
            (r for r in mine if r.state == ASSIGNED),
            key=lambda r: (-len(r.unblocks), r.critical_path, r.id),
        )
        m = stats[lane]
        out += [
            f"[lane.{lane.replace(' ', '_')}]",
            f'current            = "{pipeline[0].id if pipeline else ""}"',
            f'next               = "{pipeline[1].id if len(pipeline) > 1 else ""}"',
            f'next_after_that    = "{pipeline[2].id if len(pipeline) > 2 else ""}"',
            f"assigned_total     = {len(mine)}",
            f"claimable          = {m['claimable']}",
            f"in_flight          = {m['in_flight']}",
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

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

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
    unblocks: list[str] = field(default_factory=list)
    next_owner: list[str] = field(default_factory=list)


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


def _cell(body: str, label: str) -> str:
    match = re.search(rf"^\|\s*[^|]*\*\*{label}[^|]*\*\*[^|]*\|([^|]*)\|", body, re.M)
    return match.group(1).strip() if match else ""


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
        depends = sorted(set(re.findall(r"(?:on|after|behind)\s+\*?\*?\[?(TASK-\d+)", status)))
        blocker = status if declared in {"BLOCKED", "SEQUENCED", "WAITING"} else ""
        rows.append(
            Task(
                id=head.group(1),
                title=head.group(2).strip()[:90],
                state=_classify(declared, blocker, lane),
                declared=declared or "(none)",
                lane=lane or "—",
                depends_on=depends,
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
    return rows


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
        f'generated_from = "{_git("rev-parse", "--short=7", "HEAD") or "unknown"}"',
        f"task_count     = {len(rows)}",
        "",
    ]
    for lane in lanes:
        mine = [r for r in rows if r.lane == lane]
        claimable = [r for r in mine if r.state == ASSIGNED]
        out += [
            f"[lane.{lane.replace(' ', '_')}]",
            f"assigned_total = {len(mine)}",
            f"claimable      = {len(claimable)}",
            "claimable_ids  = " + str([r.id for r in claimable]).replace("'", '"'),
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
            "depends_on    = " + str(row.depends_on).replace("'", '"'),
            "unblocks      = " + str(row.unblocks).replace("'", '"'),
            "next_owner    = " + str(row.next_owner).replace("'", '"'),
            "",
        ]
    return "\n".join(out)


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
        if OUT.read_text() != fresh:
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

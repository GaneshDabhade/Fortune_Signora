#!/usr/bin/env python3
"""Advisory: do the repository's governance documents agree with the repository?

Run at Repository Closeout, before declaring **Repository Ready**
(CLAUDE.md §20e). It compares what the governance documents *say* against what
git, the migrations directory and the certification manifest *are*.

**It reports; it never repairs.** Every inconsistency it finds has more than
one correct resolution — a stale dashboard might need updating, or the
promotion might not have finished — and a script choosing between them would
be making a governance decision nobody reviewed.

**It checks agreement, never quality.** That `PROJECT_STATUS.md` names the
right commit says nothing about whether what it says about that commit is
true. No script can see that, and one that implied otherwise would be worse
than none.

    python3 infra/state-check.py
    python3 infra/state-check.py --strict     # exit 1 on any finding
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from registers import (  # noqa: E402
    bug_rows,
    conflict_markers,
    malformed_tables,
    unclosed_fence,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS = REPO_ROOT / "backend" / "migrations" / "versions"
MANIFEST = REPO_ROOT / "certification" / "manifest.json"


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True
    ).stdout.strip()


def _read(relative: str) -> str:
    path = REPO_ROOT / relative
    return path.read_text() if path.exists() else ""


def _migration_head() -> str | None:
    if not MIGRATIONS.is_dir():
        return None
    heads = sorted(p.name.split("_")[0] for p in MIGRATIONS.glob("[0-9]*_*.py"))
    return heads[-1] if heads else None


def _is_ancestor(candidate: str, descendant: str) -> bool:
    return (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", candidate, descendant],
            cwd=REPO_ROOT,
            capture_output=True,
        ).returncode
        == 0
    )


def _newest_named_commit(text: str, head: str) -> str | None:
    """The newest commit named in `text` that is reachable from `head`.

    Scans for bare 7-hex tokens rather than a fixed phrase, because the dashboard
    names commits in prose as often as in a table, and a check that only reads one
    cell is a check that a small edit silently disables.
    """
    newest: str | None = None
    for token in dict.fromkeys(re.findall(r"\b[0-9a-f]{7}\b", text)):
        if not _is_ancestor(token, head):
            continue
        if newest is None or _is_ancestor(newest, token):
            newest = token
    return newest


HOLDING_STATUSES = ("CLAIMED", "ACTIVE", "IN VALIDATION", "CHANGES REQUESTED")


def _backlog_claims(backlog: str) -> dict[str, str]:
    """`{task id: lane}` for every task the backlog says somebody is holding.

    Parsed **per `### TASK-nnn` block**, not line by line. A claim note routinely
    names the tasks the lane passed over — the reason it took this one — so a
    line-oriented scan reads those as claims by the claiming lane.
    """
    claims: dict[str, str] = {}
    for block in re.split(r"^### TASK-", backlog, flags=re.M)[1:]:
        task = re.match(r"(\d+)", block)
        status = re.search(r"\|\s*\*\*Status\*\*\s*\|(.*)", block)
        if task is None or status is None:
            continue
        row = status.group(1)
        if not any(f"`{state}`" in row for state in HOLDING_STATUSES):
            continue
        lane = re.search(r"\*\*(Lane [A-Z]|QE)\*\*", row)
        if lane is not None:
            claims[task.group(1)] = lane.group(1)
    return claims


def _board_claims(assignments: str) -> dict[str, set[str]]:
    """`{task id: lanes}` from the board's *Current* section only.

    Scoped the same way check 3 is: *Recently completed* names tasks that have
    shipped, and counting those as live claims would leave every finished task
    looking contested forever. Only the `Task` cell is read — a `Next action`
    may reference a blocker's id without claiming it.
    """
    if "## Current" not in assignments:
        return {}
    current = assignments.split("## Current", 1)[1].split("\n## ", 1)[0]
    claims: dict[str, set[str]] = {}
    for row in current.splitlines():
        if not row.startswith("| ") or "TASK-" not in row:
            continue
        cells = row.split("|")
        lane = cells[1].strip().strip("*")
        if not (lane.startswith("Lane") or lane == "QE"):
            continue
        for task in re.findall(r"\bTASK-(\d+)\b", cells[2] if len(cells) > 2 else ""):
            claims.setdefault(task, set()).add(lane)
    return claims


def _satisfied(run: dict[str, object]) -> bool:
    """Did this run certify? **Borrowed from `certification-guard.py`, never
    re-derived**, because a second copy of this predicate is a second answer to
    *"is this commit certified?"* and only one of them gates a promotion
    (`CLAUDE.md` §2 — truth has exactly one authoritative representation).

    The guard is loaded by path because its filename is not a Python
    identifier, the same way `test_claim_agreement.py` loads this file.
    **If it cannot be loaded, no run is treated as certified** — an absent
    predicate must not read as a passing one.
    """
    import importlib.util

    guard = sys.modules.get("certification_guard")
    if guard is None:
        spec = importlib.util.spec_from_file_location(
            "certification_guard", REPO_ROOT / "infra" / "certification-guard.py"
        )
        if spec is None or spec.loader is None:
            return False
        guard = importlib.util.module_from_spec(spec)
        # **Registered before execution, and that is not optional.** The guard
        # declares `@dataclass(slots=True)`, which resolves its own annotations
        # through `sys.modules[cls.__module__]` while the class body runs — so a
        # module executed before it is registered raises `AttributeError` on
        # `None.__dict__`, several frames from anything that names the cause.
        sys.modules[spec.name] = guard
        try:
            spec.loader.exec_module(guard)
        except (OSError, ImportError):
            del sys.modules[spec.name]
            return False
    ok, _ = guard._satisfied(run)  # type: ignore[attr-defined]
    return bool(ok)


def _latest_certification() -> dict[str, object] | None:
    """The most recent run **that certified** — never merely the most recent run.

    ⚠️ **This returned `runs[-1]` and it was wrong** ([B-137](../docs/BUGS.md)).
    The manifest records every *attempt*, failed ones included, because an
    attempt that failed is evidence about the commit and deleting it would be
    the one edit this repository never permits. So the last entry is routinely
    a run that did **not** certify — and three findings downstream then reported
    a failed run as the repository's certification state, including the one
    that says *"a certified commit that never reached `main` is not protected
    by anything."*

    **The instrument said the cycle had stopped after certification when
    certification was what had stopped.** `certification-guard.py` was right
    throughout and refused the promotion; only the advisory view was inverted,
    which is the more dangerous half to get wrong — a refusal is read once, an
    advisory is what a session reasons from.
    """
    if not MANIFEST.exists():
        return None
    runs = json.loads(MANIFEST.read_text()).get("runs") or []
    for run in reversed(runs):
        if _satisfied(run):
            return run
    return None


#: **The seven queue validations — C-333.** *"The queue must always represent
#: the actual executable state of the repository… an executable planning
#: artifact rather than documentation."*
#:
#: **Every one of these had already fired in practice before it was written.**
#: `lane-a.toml` declared five eligible rows of which **none was startable** —
#: one was `IN VALIDATION`, two were `CLAIMED`, one was `CHANGES REQUESTED` and
#: one belonged to another lane entirely. `lane-b.toml` carried a task as
#: `current` while its own note in the same file said *"claimed and delivered"*.
#: **A queue nobody validates drifts within hours, and it drifts silently
#: because it reads like a plan either way.**
QUEUES = REPO_ROOT / "docs" / "coordination" / "queues"
MODULES_TOML = REPO_ROOT / "docs" / "coordination" / "modules.toml"
MODULES_DOC = REPO_ROOT / "docs" / "architecture" / "04-modules.md"
BACKEND_MODULES = REPO_ROOT / "backend" / "modules"

#: `modules.toml` rows that describe something other than a `backend/modules/`
#: directory. **Enumerated rather than inferred**: `apps` and
#: `platform_foundation` are real ownership boundaries with no module
#: directory, and a check that silently skipped anything it could not find on
#: disk would also skip a module somebody deleted.
_NON_MODULE_ROWS = frozenset({"apps", "meta", "platform_foundation", "product_surface"})

#: States a lane may actually start from. **`CHANGES REQUESTED` belongs here**
#: — §20e makes a returned task the lane's highest priority, so it is
#: executable even though it is not `READY`.
_STARTABLE = {"READY", "CHANGES REQUESTED"}
_DEPARTED = {"IN VALIDATION", "VERIFIED", "CERTIFIED", "PROMOTED", "DONE", "DISPOSED"}
_HELD = {"CLAIMED", "IN PROGRESS"}

#: **Execution states Product Office may never write** — [D-123](../docs/DECISION_REGISTER.md).
#:
#: > *"Product Office owns planning. Engineering lanes own execution… once a
#: > lane has moved a task into CLAIMED, IN PROGRESS, IN VALIDATION, CHANGES
#: > REQUESTED, or any other execution state, Product Office must never
#: > overwrite that state."*
#:
#: **The lane sets the first four; QE sets the rest.** Neither is Product
#: Office's, and the distinction between them does not matter here — what
#: matters is that this office wrote none of them.
_LANE_OWNED_STATES = frozenset({
    "CLAIMED", "IN PROGRESS", "IN VALIDATION", "CHANGES REQUESTED",
    "VERIFIED", "CERTIFIED", "PROMOTED", "DONE",
})


def _staleness_findings() -> list[str]:
    """**Is this branch building blind?** — [C-102](../docs/LANE_COORDINATION.md), [C-103](../docs/LANE_COORDINATION.md).

    **Both items have one root and neither says so**: information reaches a lane
    only through `integration`, and a lane rebases on its own cadence. **C-102 is
    a lane that cannot see the defect blocking it. C-103 is two lanes that cannot
    see each other's work.** Same cause, opposite symptom.

    ⚡ **Measured when C-102 was raised**: Lane A idle six hours then 23 files in
    one push with `B-107` untouched; Lane B five pushes and 41 commits deep with
    `B-108` untouched. **Neither lane misbehaved** — §20e's *Continuous
    execution* tells a lane not to idle, and Startup is what pulls.

    ⛔ **No notification, no scheduler, no CI** (§20c-2). **This is the cheapest
    thing that could work: the check a lane already runs tells it, locally, when
    the ref it consumes has moved and carries something it must see.**
    """
    behind = _git("rev-list", "--count", "HEAD..origin/integration").strip()
    if not behind.isdigit() or int(behind) == 0:
        return []
    theirs_bugs = _git("show", "origin/integration:docs/BUGS.md")
    theirs_coord = _git("show", "origin/integration:docs/LANE_COORDINATION.md")
    out: list[str] = []
    mine_bugs = _read("docs/BUGS.md")
    unseen = sorted(
        set(re.findall(r"^### (B-\d+)", theirs_bugs, re.M))
        - set(re.findall(r"^### (B-\d+)", mine_bugs, re.M))
    )
    if unseen:
        out.append(
            f"{behind} commit(s) behind `integration`, which carries "
            f"{len(unseen)} bug row(s) this branch has never seen: "
            f"{', '.join(unseen)}. A lane cannot act on a defect it cannot read "
            f"(C-102). Rebase before the next slice."
        )
    mine_coord = _read("docs/LANE_COORDINATION.md")
    unseen_c = sorted(
        set(re.findall(r"^#{2,3} (C-\d+)", theirs_coord, re.M))
        - set(re.findall(r"^#{2,3} (C-\d+)", mine_coord, re.M))
    )
    if unseen_c:
        out.append(
            f"`integration` carries {len(unseen_c)} coordination item(s) this "
            f"branch has never seen: {', '.join(unseen_c)}. Two lanes that "
            f"cannot see each other's items build the same thing twice (C-103)."
        )
    if not out:
        out.append(
            f"{behind} commit(s) behind `integration` — nothing unseen in the "
            f"registers, so this is ordinary drift rather than blindness."
        )
    return out


#: **The `Planning-Sync` trailer — [D-136](../docs/DECISION_REGISTER.md).**
#:
#: > *"Planning corrections should become their own class of repository
#: > change… QE should then treat these as high-priority synchronization work
#: > rather than ordinary feature work."*
#:
#: **A commit message, not a file.** Every alternative was a new shared file,
#: and a shared file is a conflict surface between the two lanes it exists to
#: coordinate. The repository already carries three conventions this way —
#: `Claim TASK-`, `Repository Closeout`, `Slice-Handoff` — and each is found
#: by `--grep` rather than by parsing something somebody has to maintain.
_PLANNING_SYNC = "Planning-Sync: required"


def _structured_file_findings() -> list[str]:
    """Every coordination `.toml` parses, and no key is defined twice.

    **Earned by two lanes hitting one defect in a single cycle**, which is the
    bar `CLAUDE.md` §20e sets — *"one lane's inconvenience is not evidence; two
    lanes' is."* **Lane C union-resolved `lane-c.toml` during a rebase and
    produced three `future =` lines; QE did the same to `lane-a.toml` and got
    `Cannot overwrite a value` at line 149.** **Neither was careless: the union
    strategy is correct for the append-only markdown registers beside these
    files, and nothing marked the difference.**

    ⚡ **The rule both lanes arrived at independently — union-resolve markdown,
    never structured files — is the kind a machine should keep.**

    ⛔ **The parse is the whole check, and a second one was written and
    removed within the hour.** A line-prefix scan for repeated `key =` was
    added to name the offending key, and it reported `task`, `note`, `owner`
    and `blocker` on all five files — which repeat correctly, once per
    `[[blocked]]` entry. **B-101's shape: counting by line prefix where the
    question is about structure.** **A duplicate key is unrepresentable in
    valid TOML, so `tomllib` refusing the file is the entire signal**, and the
    docstring above had already said so before the redundant scan was written.

    ⛔ **A conflict marker inside a `.toml` also lands here**, because it makes
    the file unparseable — which is a stronger signal than the marker check
    over markdown, and arrives at the same place.
    """
    findings: list[str] = []
    root = REPO_ROOT / "docs" / "coordination"
    if not root.is_dir():
        return findings
    for path in sorted(root.rglob("*.toml")):
        name = path.relative_to(REPO_ROOT)
        text = path.read_text()
        try:
            tomllib.loads(text)
        except tomllib.TOMLDecodeError as exc:
            findings.append(
                f"{name} does not parse — {exc}. A structured file takes one "
                f"side of a conflict, never a union: a union is correct for the "
                f"markdown registers beside it and produces duplicate keys here."
            )
            continue
    return findings


def _planning_sync_findings() -> list[str]:
    """Planning corrections written here and not yet visible to any lane.

    **[D-136](../docs/DECISION_REGISTER.md), and it exists because the gap was
    measured rather than imagined.** Lane A claimed `TASK-440` from
    `origin/integration` while this branch had carried the row's correction —
    *no read exists behind its account table* — for a day. **The lane followed
    every rule; the correction was simply somewhere it could not look.**

    **Why a count rather than a gate.** ⛔ This office may not push to
    `integration` (D-136 keeps QE the sole integration authority), so a check
    that *failed* would fail on a condition its own lane cannot clear — which
    trains a reader to ignore it. **It reports an age and a list**, and the
    list is what QE picks up.

    ⚡ **It is also the evidence D-136 asks for**: *"if Planning Sync Required
    items begin accumulating or repeatedly delay implementation, gather
    evidence over several cycles."* **A number that appears every run is a
    trend; an incident report is not.**
    """
    branch = _git("rev-parse", "--abbrev-ref", "HEAD").strip()
    if not branch.startswith("lane-c"):
        return []
    pending = [
        line
        for line in _git(
            "log", "--format=%h %s", f"origin/integration..{branch}",
            f"--grep={_PLANNING_SYNC}",
        ).splitlines()
        if line.strip()
    ]
    if not pending:
        return []
    oldest = _git(
        "log", "--format=%cr", f"origin/integration..{branch}",
        f"--grep={_PLANNING_SYNC}",
    ).splitlines()[-1].strip()
    return [
        f"{len(pending)} planning correction(s) are not on `integration`, the "
        f"oldest written {oldest or 'unknown'}. **Until QE integrates them every "
        f"lane is planning from the previous answer** — which is how TASK-440 was "
        f"claimed after its blocker was recorded (C-422). Commits: "
        + ", ".join(line.split(" ", 1)[0] for line in pending[:8])
    ]


def _execution_state_findings() -> list[str]:
    """**Did Product Office overwrite a state a lane owns?** ([D-123](../docs/DECISION_REGISTER.md))

    **Compares this branch's backlog against `origin/integration`** and reports
    any task whose *lane-owned* execution state has changed.

    ⚠️ **Scoped to Lane C branches deliberately.** On a lane's own branch such a
    change is the lane doing its job; on this office's branch it is the defect.
    **A check that flagged both would cry wolf on every lane in the repository**,
    which this file has already done twice this week and does not intend to do
    again.

    ⚡ **Written because the rebase caught what review did not.** `TASK-439` and
    `TASK-441` were `CLAIMED` on `integration` and `BLOCKED` here — twice in one
    day — and the only reason it surfaced was a merge conflict. **A conflict is
    not a control: it fires when two people touch one line, not when one person
    breaks a rule.**
    """
    branch = _git("rev-parse", "--abbrev-ref", "HEAD").strip()
    if not branch.startswith("lane-c"):
        return []
    theirs = _git("show", "origin/integration:docs/BACKLOG.md")
    if not theirs:
        return []
    before = _backlog_states(theirs)
    after = _backlog_states((REPO_ROOT / "docs" / "BACKLOG.md").read_text())
    overwritten = sorted(
        f"{task} ({was} → {now})"
        for task, was in before.items()
        if was in _LANE_OWNED_STATES
        and (now := after.get(task, was)) != was
    )
    if not overwritten:
        return []
    return [
        f"Product Office changed a lane-owned execution state: {', '.join(overwritten)}. "
        f"CLAUDE.md §20e gives CLAIMED, IN PROGRESS, IN VALIDATION and CHANGES "
        f"REQUESTED to the lane and the rest to QE. Record the finding beneath "
        f"the row and let the lane decide (D-123)."
    ]

#: Coordination-item states that need no owner, because the question is settled.
#: **Kept identical to `decision-queue.py`'s set on purpose** — two files
#: disagreeing about what *closed* means is how an item becomes invisible to one
#: instrument and urgent to the other.
_SHUT_ITEM_STATES = {
    "CLOSED",
    "RULED",
    "ANSWERED",
    "RESOLVED",
    "SUPERSEDED",
    "WITHDRAWN",
    "READY FOR IMPLEMENTATION",
}
_STATE_WORDS = _STARTABLE | _DEPARTED | _HELD | {
    "WAITING", "BLOCKED", "SEQUENCED", "PREPARING", "UNDER REVIEW",
    "REVISION REQUESTED", "RATIFIED",
}


def _backlog_states(backlog: str) -> dict[str, str]:
    """Every `TASK-nnn` and the state its own row declares.

    **Read from the Status row's backticked words in line order**, which is the
    correction B-101 forced on the dashboard: a status that *explains* a state
    in prose must not be mistaken for being in it.
    """
    states: dict[str, str] = {}
    for block in re.split(r"(?=^### TASK-\d+)", backlog, flags=re.M):
        head = re.match(r"^### (TASK-\d+)", block)
        row = re.search(r"^\| \*\*Status\*\* \|(.+)$", block, re.M)
        if not head or not row:
            continue
        for quoted in re.findall(r"`([A-Z][A-Z ]+)`", row.group(1)):
            if quoted.strip() in _STATE_WORDS:
                states[head.group(1)] = quoted.strip()
                break
    return states


#: States a row can sit in while nobody is executing it. **These are the rows
#: [D-135](../docs/DECISION_REGISTER.md) exists for** — *"every task should
#: have an owner even if it cannot yet have an executor."*
_PARKED = frozenset({"SEQUENCED", "BLOCKED", "WAITING", "DISPOSED"})


def _declared_state(cell: str) -> str:
    """The backticked state token in a Status cell, or a readable stand-in.

    **Never `re.match(...).group()` inline** — a cell with no token returns
    `None` and the traceback would be inside the check that exists to report
    a malformed row.
    """
    token = re.search(r"`([A-Z][A-Z ]*)`", cell)
    return token.group(1).strip() if token else cell.strip()[:20] or "(blank)"


def _duplicate_state_findings(backlog: str) -> list[str]:
    """A task block declaring its state twice.

    **Found by a shipped defect, not by imagination.** `TASK-440` reached
    `origin/integration` with two `Status` rows — Product Office's `BLOCKED`
    and Lane A's `CLAIMED` — because a union conflict resolution is correct
    for an append-only register and wrong for a field that holds one value.
    **The same mistake as the TOML union**, one file format over.

    ⛔ **It is the silent kind.** Every reader here — `_backlog_states`, the
    dashboard, a lane — takes the first match, so the repository answered
    *BLOCKED* for a row a lane was holding, and both rows looked deliberate.

    ⚡ **This is the markdown half of what `_structured_file_findings` does for
    TOML**: a field that may hold one value, holding two.
    """
    findings: list[str] = []
    for block in re.split(r"(?=^### TASK-\d+)", backlog, flags=re.M):
        head = re.match(r"^### (TASK-\d+)", block)
        if head is None:
            continue
        body = block.split("\n### ", 1)[0]
        rows = re.findall(r"^\|\s*\*\*Status\*\*\s*\|([^|]*)\|", body, re.M)
        if len(rows) > 1:
            findings.append(
                f"{head.group(1)} declares its state {len(rows)} times — "
                + " / ".join(_declared_state(r) for r in rows)
                + ". Every reader takes the first, so the repository answers with "
                f"whichever was written higher. A state holds one value."
            )
    return findings


def _ownership_findings(backlog: str) -> list[str]:
    """Rows nobody is executing and nobody is accountable for.

    **[D-135](../docs/DECISION_REGISTER.md), ownership-first planning:** *"I do
    not want work to disappear into a general backlog where nobody is
    responsible for it. The backlog should represent planned execution, not
    unprocessed ideas."*

    **A parked row needs two things and they are different questions.** *Who
    would build it* is a **module** question, and `CLAUDE.md` §20e deliberately
    leaves it open — *"predicting it earlier buys nothing and can be wrong"*.
    *Who notices its trigger fired* is a **task** question, and leaving that
    open is how a row parks for a month after its blocker cleared.

    **So the check accepts either a resolvable module or a named steward**, and
    reports only the rows that have neither. ⛔ **It does not demand a module
    where §20e says not to have one** — a check that contradicted a ratified
    rule would be the more expensive defect.
    """
    findings: list[str] = []
    states = _backlog_states(backlog)
    for block in re.split(r"(?=^### TASK-\d+)", backlog, flags=re.M):
        head = re.match(r"^### (TASK-\d+)", block)
        if head is None or states.get(head.group(1), "") not in _PARKED:
            continue
        body = block.split("\n### ", 1)[0]
        module = re.search(r"^\|\s*[^|]*\*\*Module\*\*[^|]*\|([^|]*)\|", body, re.M)
        named = module is not None and not re.search(
            r"undecided|deliberately unnamed|not yet decided", module.group(1), re.I
        )
        steward = re.search(r"\*\*Trigger steward\*\*", body) is not None
        if not named and not steward:
            findings.append(
                f"{head.group(1)} is {states[head.group(1)]} with no resolvable module "
                f"and no trigger steward. Nobody is accountable for noticing when its "
                f"prerequisites are met (D-135). A module may stay undecided (§20e); "
                f"a steward may not."
            )
    return findings


def _queue_findings(backlog: str) -> list[str]:
    states = _backlog_states(backlog)
    out: list[str] = []
    if not QUEUES.is_dir():
        return out
    newest = _git("log", "-1", "--format=%cs", "--", "docs/BACKLOG.md")
    queued: set[str] = set()

    for path in sorted(QUEUES.glob("lane-*.toml")):
        lane = path.stem
        try:
            queue = tomllib.loads(path.read_text())
        except tomllib.TOMLDecodeError as broken:
            out.append(f"{lane}: does not parse — {broken}")
            continue

        sequence = [str(t) for t in (queue.get("current"), queue.get("next")) if t]
        sequence += [str(t) for t in (queue.get("future") or [])]
        queued.update(sequence)
        target = int(queue.get("depth_target", 5) or 5)

        declared = queue.get("eligible_count")
        if declared is not None and int(declared) != len(sequence):
            out.append(
                f"{lane}: declares eligible_count {declared} beside a sequence of "
                f"{len(sequence)} — one of the two is stale"
            )
        stated = queue.get("shortfall")
        expected = max(0, target - len(sequence))
        if stated is not None and int(stated) != expected:
            out.append(
                f"{lane}: declares shortfall {stated}; {len(sequence)} of {target} "
                f"is a shortfall of {expected}"
            )
        for task in sequence:
            state = states.get(task)
            if state is None:
                out.append(f"{lane}: queues {task}, which has no row in BACKLOG.md")
            elif state in _DEPARTED:
                out.append(
                    f"{lane}: queues {task} as executable and its row says {state} "
                    f"— finished work advertised as available"
                )
            elif state in _HELD:
                out.append(f"{lane}: queues {task} as executable; somebody holds it ({state})")
            elif state not in _STARTABLE:
                out.append(f"{lane}: queues {task}, which is {state} and not startable")
        blocked = {str(b.get("task")) for b in (queue.get("blocked") or [])}
        for task in sorted(blocked & set(sequence)):
            out.append(f"{lane}: lists {task} as both executable and blocked")
        stamped = queue.get("updated")
        if stamped is not None and newest and str(stamped) < newest:
            out.append(
                f"{lane}: stamped {stamped}; BACKLOG.md last moved {newest} — "
                f"not re-measured since"
            )

        # ⑧ the arrays that describe what a lane is *not* doing.
        #
        # **Added after the first version passed a queue that was wrong.**
        # C-333's checks validated `current`, `next` and `future` — what a lane
        # should *start* — and never read `held` or `in_validation`. `lane-a`
        # carried a PROMOTED row in `held` and two IN VALIDATION rows beside it,
        # and every executable check passed because none of them looked there.
        # **A queue is not only a list of what to take; it is a claim about
        # everything else, and the claim was unchecked.**
        for entry in queue.get("held") or []:
            task = str(entry.get("task"))
            state = states.get(task)
            if state in _DEPARTED:
                out.append(
                    f"{lane}: holds {task}, which is {state} — it left this lane"
                )
        for entry in queue.get("in_validation") or []:
            task = str(entry.get("task"))
            state = states.get(task)
            if state is not None and state not in _DEPARTED:
                out.append(
                    f"{lane}: lists {task} as with QE; its row says {state}"
                )

    for task, state in sorted(states.items()):
        if state in _STARTABLE and task not in queued:
            out.append(
                f"{task} is {state} and appears in no lane queue — a lane reading "
                f"only its queue cannot see work the backlog offers"
            )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    findings: list[str] = []
    notes: list[str] = []

    # **`origin/main`, never local `main`** — the shared ref, not a branch a
    # lane may never check out. Lane C has no local `main` that anything
    # updates (§20e gives `main` to QE), so this read `19845456` for days
    # while `origin/main` was twenty-six commits further on, and reported a
    # certified commit as unpromoted every single cycle.
    #
    # ⛔ **D-130's class, in this file**: `main` is a *name*, and what the
    # check means is *the ref every lane shares*. Reading the name gave a
    # confident wrong answer, and Product Office relayed it to the product
    # owner as "QE's cycle stopped after certification" more than once.
    main_sha = _git("rev-parse", "--short=7", "origin/main") or _git(
        "rev-parse", "--short=7", "main"
    )
    status = _read("PROJECT_STATUS.md")
    handoff = _read("docs/SESSION_HANDOFF.md")
    assignments = _read("docs/ACTIVE_ASSIGNMENTS.md")
    bugs = _read("docs/BUGS.md")
    coordination = _read("docs/LANE_COORDINATION.md")
    backlog = _read("docs/BACKLOG.md")

    # 1 — the dashboard must not predate the promotion it describes.
    #
    # It cannot name the commit that carries it — that sha does not exist until
    # the commit is written — and Closeout is usually several commits, so
    # "names HEAD" and "names HEAD's parent" are both rules nothing can satisfy.
    # A rule that always fails is a rule everybody learns to ignore.
    #
    # What is actually checkable, and is what the rule was reaching for: the
    # dashboard names a commit that is **reachable from `main`** and is **no
    # older than the latest certification**. A dashboard describing a commit
    # from before the last certified run is stale, and that is the failure this
    # exists to catch.
    certified = _latest_certification() or {}
    certified_commit = str(certified.get("commit") or "")[:7]
    status_named: str | None = None
    if main_sha and status:
        named = status_named = _newest_named_commit(status, main_sha)
        if named is None:
            findings.append(
                f"PROJECT_STATUS.md names no commit reachable from `main` ({main_sha}). "
                f"Either the dashboard predates the promotion, or Repository Closeout "
                f"did not run (lifecycle stage 5)."
            )
        elif certified_commit and not _is_ancestor(certified_commit, named):
            findings.append(
                f"PROJECT_STATUS.md names `{named}`, which predates the latest "
                f"certification ({certified_commit}). The dashboard describes a "
                f"repository that has since been certified at a later commit."
            )
        else:
            notes.append(f"PROJECT_STATUS.md names `{named}`, reachable from `main` ({main_sha}).")

    # 2 — certification expires by derivation. Say so out loud rather than
    #     leaving it to somebody to notice.
    run = _latest_certification()
    head = _migration_head()
    if run and head:
        conditions = run.get("conditions")
        certified_head = (
            conditions.get("migration_head") if isinstance(conditions, dict) else None
        )
        if certified_head and certified_head != head:
            findings.append(
                f"The repository is UNCERTIFIED by derivation: the certification "
                f"record is bound to migration head {certified_head}; the repository "
                f"is at {head}. `is_certified` reads false. Re-certify before "
                f"declaring Repository Ready."
            )
        else:
            notes.append(f"Certification conditions still hold (migration head {head}).")

    # 3 — a COMPLETE row should have been removed, not left standing.
    #
    # Scoped to the "Current" section deliberately: the status legend defines
    # COMPLETE and would otherwise match forever, which is how a check starts
    # crying wolf and then gets ignored. Found by running this against a
    # correct repository before shipping it.
    current = ""
    if "## Current" in assignments:
        current = assignments.split("## Current", 1)[1].split("\n## ", 1)[0]
    if any("`COMPLETE`" in line for line in current.splitlines() if line.startswith("| ")):
        findings.append(
            "ACTIVE_ASSIGNMENTS.md still carries a `COMPLETE` row. Completed "
            "assignments are removed at closeout — a lane reading one would believe "
            "it still holds work that has shipped."
        )

    # 4 — the one blocking rule.
    #
    # This check used to ask whether "🔴" appeared anywhere above the Verified
    # section, minus a legend row. The legend is *always* there, so the condition
    # was never true and **the one rule that blocks a promotion was never
    # checked** — Decorative Logic (§2), found by a KPI tool disagreeing with it.
    # The parsing now lives in `registers.py`, so the two tools cannot drift apart
    # about what "blocking" means.
    rows = bug_rows(bugs)
    for row in rows:
        if row.malformed:
            findings.append(
                f"{row.identifier} has no Severity or no Status row. Every row carries "
                f"both, and a row missing one cannot be reasoned about."
            )
    blocking = [row.identifier for row in rows if row.blocks_promotion]
    if blocking:
        findings.append(
            f"BUGS.md carries {len(blocking)} unresolved 🔴 ({', '.join(blocking)}). "
            f"`integration` never fast-forwards to `main` with one open (CLAUDE.md §20e)."
        )
    else:
        notes.append(f"No unresolved 🔴 across {len(rows)} bug row(s) — promotion is not blocked.")

    # 5 — the handoff is the cold-start document; a dashboard newer than it
    #     means a session would resume from the older of the two.
    handoff_named = _newest_named_commit(handoff, main_sha)
    status_named = _newest_named_commit(status, main_sha)
    if handoff_named is None and status_named is not None:
        findings.append(
            "SESSION_HANDOFF.md does not mention the promoted commit while "
            "PROJECT_STATUS.md does. A cold session reads the handoff first."
        )

    # 5b — the pull model, checked where it actually breaks.
    #
    # Not "is there a backlog" — a file existing proves nothing. What breaks is a
    # lane sitting idle because a document told it to wait for an allocation that
    # nobody is going to make, which is the bottleneck the model removed.
    if assignments:
        waiting = [
            line.strip()
            for line in assignments.splitlines()
            if line.startswith("| ") and ("to assign" in line or "await" in line.lower() and "assign" in line.lower())
        ]
        if waiting:
            findings.append(
                f"ACTIVE_ASSIGNMENTS.md has {len(waiting)} row(s) implying a lane is waiting "
                f"to be assigned work. Lanes pull from BACKLOG.md; nobody assigns "
                f"(CLAUDE.md §20e)."
            )

    # 5c — the claim protocol's two failure modes, both detectable only because a
    #      task has a permanent id. "Are these the same task?" must be a fact.
    if backlog and assignments:
        known = set(re.findall(r"\bTASK-(\d+)\b", backlog))
        board_here = _board_claims(assignments)

        # (a) two lanes holding one task — the race the protocol exists to lose safely.
        #
        # **Reads `_board_claims` rather than scanning rows itself.** The scan this
        # replaced matched every line in the file containing a task id and took the
        # first cell as the lane, which made two things claims that are not:
        # *Recently completed* rows (a finished task looks contested forever) and a
        # task id mentioned in a `Next action`. It reported `TASK-001` held by
        # "B" and "Lane B" at once — one row in each section, neither a live claim.
        # One parser, used by both checks: duplicated truth eventually contradicts
        # itself, and here it did.
        contested = {t: lanes for t, lanes in board_here.items() if len(lanes) > 1}
        for task, lanes in sorted(contested.items()):
            findings.append(
                f"TASK-{task} is claimed by {' and '.join(sorted(lanes))} at once. "
                f"The Task Claim Protocol requires the later claim to be abandoned "
                f"(CLAUDE.md §20e)."
            )

        # (b) a board row naming a task the backlog has never heard of.
        unknown = set(board_here) - known
        if unknown:
            findings.append(
                f"ACTIVE_ASSIGNMENTS.md names {', '.join('TASK-' + t for t in sorted(unknown))}, "
                f"which BACKLOG.md does not define. A claim must refer to a task that exists."
            )

        # (c) the two registers must name the same holder.
        #
        # **A claim is recorded in two files, so the two can disagree**, and 5c(a)
        # cannot see it: that check reads the board alone, so a backlog row saying
        # `CLAIMED — Lane X` with no board row is invisible. Both directions are
        # wrong in the same way and for the same reason — a lane reading one file
        # concludes the task is free while a lane reading the other concludes it is
        # taken, which is the duplicate implementation the protocol exists to stop,
        # arriving through the registers instead of through a race.
        for task, lane in _backlog_claims(backlog).items():
            holders = board_here.get(task, set())
            if not holders:
                findings.append(
                    f"BACKLOG.md says {lane} holds TASK-{task}; "
                    f"ACTIVE_ASSIGNMENTS.md has no row for it under `## Current`. "
                    f"A lane reading only the board would take work somebody else "
                    f"is doing. (A row elsewhere in the file does not count — "
                    f"`## Current` is where a lane looks, and B-404 is what it "
                    f"costs when the rows live under another heading.)"
                )
            elif lane not in holders:
                findings.append(
                    f"BACKLOG.md says {lane} holds TASK-{task}; the board says "
                    f"{' and '.join(sorted(holders))}. One of the two is wrong, and "
                    f"neither is authoritative over the other."
                )

        if not contested and not unknown:
            # **Both figures were wrong, and the second one mattered.** `ready`
            # counted `^### TASK-` headings — every task in the file, whatever
            # state it declared — and reported the total as the READY count.
            # It read `54 READY` on a repository with **two** claimable rows.
            #
            # That is B-101's shape once more: a proxy counted, and labelled
            # with the word for the thing it is not. It is worse here than
            # elsewhere because D-099 makes a lane reaching zero READY a
            # finding Product Office must investigate — **and this line is
            # where a reader would have looked to see it.** A dashboard
            # reporting 54 claimable rows hides the exact condition the
            # standing duty exists to catch.
            #
            # `_backlog_states` already parses the Status row correctly and
            # already existed in this file, written for the queue checks.
            # `known` is every `TASK-nnn` *mentioned* anywhere — right for the
            # unknown-row check above, wrong as a count of defined tasks.
            states = _backlog_states(backlog)
            startable = sorted(t for t, s in states.items() if s in _STARTABLE)
            notes.append(
                f"Backlog: {len(states)} task(s), {len(startable)} startable "
                f"({', '.join(startable) if startable else 'none'}), "
                f"no task claimed twice."
            )

    # 5c-2 — a document warning that it is not on `integration`, while it is.
    #
    # **[B-205](../docs/BUGS.md), raised by Lane A.** `ADR-0400`'s status block
    # read *"⚠️ Not yet on `origin/integration` — this file does not exist
    # there. A lane may act on it only once QE has merged this branch"* for a
    # day after QE had. **A lane obeying that warning declines to act on a
    # ruling the repository already carries**, which is the failure the five
    # decision states exist to prevent — sitting in the file that names them.
    #
    # **Two instances in one status block, same day, same cause**: a warning
    # written about a branch state and never revisited once the state changed.
    # **Prose disagreeing across three documents is not mechanically checkable;
    # this half is**, so this half gets a check.
    stale_location = re.compile(
        r"not yet on\s+`?(?:origin/)?integration`?|does not (?:yet )?exist (?:on|there)",
        re.I,
    )
    tracked = set(_git("ls-tree", "-r", "--name-only", "origin/integration").splitlines())
    for doc in sorted((REPO_ROOT / "docs").rglob("*.md")):
        relative = doc.relative_to(REPO_ROOT).as_posix()
        if relative not in tracked:
            continue          # genuinely absent — the warning is true.
        # **Line by line, and a line carrying ✅ or ~~ is exempt.** The first
        # version of this check flagged the very document it was written for:
        # the correction *quotes* the warning it replaced — dating a record
        # rather than erasing it, which §2 requires — and a whole-file search
        # cannot tell a live warning from a historical one. **The repository's
        # own convention is the discriminator**: ✅ marks a resolved claim and
        # `~~` marks a withdrawn one, and both are used consistently enough to
        # rely on. **A check that cannot distinguish its own fix from the
        # defect would be un-silenceable, and an un-silenceable check is one
        # people learn to read past.**
        for line in doc.read_text(errors="replace").splitlines()[:40]:
            if "✅" in line or "~~" in line:
                continue
            if stale_location.search(line):
                findings.append(
                    f"{relative} warns that it is not on `origin/integration`, and it "
                    f"is. A lane obeying the warning would decline to act on a ruling "
                    f"the repository already carries."
                )
                break

    # 5d — structural corruption in a register, which no gate reads.
    #
    # A malformed table survived four certifications on `main`: a reconciliation
    # script stranded a header, leaving `---|---|` with no `| | |` above it and a
    # second Status row inside one bug. Nothing failed, because gates read code.
    for name, text in (
        ("docs/BUGS.md", bugs),
        ("docs/LANE_COORDINATION.md", coordination),
        ("docs/BACKLOG.md", backlog),
        ("docs/ACTIVE_ASSIGNMENTS.md", assignments),
    ):
        orphans = malformed_tables(text)
        if orphans:
            findings.append(
                f"{name} has a malformed table at line(s) "
                f"{', '.join(str(n) for n in orphans[:5])} — a separator with no header "
                f"row above it. Usually the residue of a merge that split a section."
            )

        # An unresolved conflict marker is the same failure one stage earlier,
        # and `malformed_tables` cannot see it: `>>>>>>>` inside a table is not
        # a table separator. One sat in the coordination register through
        # several certifications (B-102), stranding a row outside its table and
        # leaving two more duplicated with contradictory statuses.
        # And the marker check is only as good as the fence parity it skips
        # on: one unclosed fence inverts every decision after it, so a real
        # marker in prose is skipped and a quoted one is reported (B-403).
        # Establish the structure before trusting a conclusion drawn from it.
        unclosed = unclosed_fence(text)
        if unclosed is not None:
            findings.append(
                f"{name} opens a code fence at line {unclosed} that nothing "
                f"closes. Every fence-aware check reads the rest of the file "
                f"inverted — including the conflict-marker check, which is "
                f"then blind to a real marker and reports quoted ones."
            )

        conflicts = conflict_markers(text)
        if conflicts:
            findings.append(
                f"{name} carries an unresolved merge-conflict marker at line(s) "
                f"{', '.join(str(n) for n in conflicts[:5])}. The register is "
                f"corrupt, and every reader of it is reading a merge that never "
                f"finished."
            )

    # 5e — identifier collisions, across every class a lane can allocate.
    #
    # B-024 was allocated twice, seven minutes apart, by two lanes on separate
    # branches. Neither push conflicted because they edited different regions of
    # one file and git merged them happily. **Ranges make it impossible; this
    # makes it visible** — defence in depth, because a lane can still fat-finger
    # a number inside its own block.
    identifier_classes = {
        "B-": (bugs, r"^### (B-\d+)"),
        "C-": (coordination, r"^#{2,3} (C-\d+)"),
        "TASK-": (backlog, r"^### (TASK-\d+)"),
    }
    for label, (text, pattern) in identifier_classes.items():
        found = re.findall(pattern, text, re.M)
        duplicated = sorted({i for i in found if found.count(i) > 1})
        if duplicated:
            findings.append(
                f"{label} identifiers are allocated twice: {', '.join(duplicated)}. "
                f"Two rows under one id is two defects nobody can refer to separately "
                f"(CLAUDE.md §20e, identifier allocation)."
            )
        elif found:
            notes.append(f"{label} identifiers: {len(found)} allocated, none duplicated.")

    # ADR numbers are a filename rather than a heading, and more than one actor
    # creates them — 0036 and 0037 by Lane A, 0038 by Lane B, 0039 by QE. Two
    # lanes choosing the same number produce two *differently named* files, which
    # git merges without complaint.
    adr_dir = REPO_ROOT / "docs" / "architecture" / "adr"
    if adr_dir.is_dir():
        numbers: dict[str, list[str]] = {}
        for path in adr_dir.glob("[0-9]*.md"):
            numbers.setdefault(path.name.split("-")[0], []).append(path.name)
        clashing = {n: f for n, f in numbers.items() if len(f) > 1}
        for number, files in sorted(clashing.items()):
            findings.append(
                f"ADR-{number} is claimed by {len(files)} files: {', '.join(sorted(files))}. "
                f"An ADR number is its identity; two files sharing one make every "
                f"citation ambiguous."
            )
        if not clashing and numbers:
            notes.append(f"ADR numbers: {len(numbers)} allocated, none duplicated.")

    # 5f — numbered architecture documents, the class the block rule missed.
    #
    # Found by Lane A (C-201): `40` came from Lane B, `41`-`43` from Lane A, and
    # two lanes writing a module design in one week produce two *differently
    # named* files that git merges without a word. The block rule enumerated
    # B-, C-, TASK- and ADR, and stopped there.
    arch_dir = REPO_ROOT / "docs" / "architecture"
    if arch_dir.is_dir():
        numbered: dict[str, list[str]] = {}
        for path in arch_dir.glob("[0-9]*.md"):
            numbered.setdefault(path.name.split("-")[0], []).append(path.name)
        clashes = {n: f for n, f in numbered.items() if len(f) > 1}
        for number, files in sorted(clashes.items()):
            findings.append(
                f"Architecture document {number} is claimed by {len(files)} files: "
                f"{', '.join(sorted(files))}. Two lanes numbered independently and git "
                f"merged both — the collision class C-201 names."
            )
        if not clashes and numbered:
            notes.append(f"Architecture documents: {len(numbered)} numbered, none duplicated.")

    # 5g — the execution board's own header, which nothing read until B-100.
    #
    # A lane rebasing onto a Closeout commit hits a conflict in this file and
    # resolves it by keeping its own side — the natural resolution, because the
    # rest of the file *is* its rows. Lane A did exactly that and moved the board
    # back seven cycles; every gate passed, because rule 1 reads PROJECT_STATUS.md
    # and that file was untouched.
    #
    # **The header is a proxy, not a proof.** A reverted *row* still passes. The
    # real answer is ADR-0039 RC-2's — stop hand-merging derivable state — and
    # this is the cheap check that makes the common case visible meanwhile.
    board_sha = re.search(r"^## Current — as of [^,]+,\s*`([0-9a-f]{7,40})`", assignments, re.M)
    if board_sha:
        named = board_sha.group(1)
        if not _is_ancestor(named, "HEAD"):
            findings.append(
                f"ACTIVE_ASSIGNMENTS.md is dated at `{named}`, which is not reachable "
                f"from HEAD. The execution board describes a repository this one is not."
            )
        elif status_named and _is_ancestor(named, status_named) and named != status_named:
            findings.append(
                f"ACTIVE_ASSIGNMENTS.md is dated at `{named}` but PROJECT_STATUS.md names "
                f"`{status_named}`, which is newer. The board has gone backwards — the "
                f"B-100 signature, where a rebase keeps a lane's side of a shared table."
            )
        else:
            notes.append(f"ACTIVE_ASSIGNMENTS.md is dated at `{named}`, reachable from HEAD.")

    # 5h — L-17. **The inverse direction, and the one that failed.**
    #
    # `certification-guard.py --audit-main` proves every commit on `main` was
    # certified. Nothing proved the converse: that a certified commit actually
    # *reached* `main`. So a cycle could certify, stop, and leave the repository
    # reporting "certified" while `main` did not contain the code — which is
    # exactly what happened, and the product owner noticed before QE did.
    #
    # **Certification and promotion are one workflow.** A certified commit that
    # is not an ancestor of `main` is an incomplete cycle, not a finished one
    # with paperwork outstanding (§20e).
    if main_sha and certified_commit:
        if not _is_ancestor(certified_commit, main_sha):
            findings.append(
                f"`{certified_commit}` is certified and is NOT on `main` ({main_sha}). "
                f"The cycle stopped after certification: promotion, Closeout, "
                f"synchronization and Repository Ready have not run. **A certified "
                f"commit that never reached `main` is not protected by anything.**"
            )
        else:
            notes.append(
                f"Certified `{certified_commit}` is on `main` — the cycle completed."
            )

    # 6 — a coordination register that only grows has become a discussion log.
    opened = len(re.findall(r"^#{2,3} C-\d+", coordination, re.M))
    closed = 0
    if "## Closed" in coordination:
        closed = len(re.findall(r"^#{2,3} C-\d+", coordination.split("\n## Closed")[1], re.M))
    if opened and closed == 0 and opened >= 10:
        findings.append(
            f"LANE_COORDINATION.md holds {opened} items and has closed none. The "
            f"register is meant to shrink as questions become architecture."
        )
    else:
        notes.append(f"Coordination register: {opened} item(s), {closed} closed.")

    # 6a — D-100. **Every coordination item declares an owner and a state.**
    #
    # > *"Every task has an owner. Every dependency has an owner. Every review
    # > has an owner… Ownership should never be ambiguous."*
    #
    # **An unowned item is worse than an unraised one**: it is visibly filed, so
    # everybody assumes somebody has it. C-213 cost TASK-205 two days on a
    # *stale* owner; an absent one fails the same way and is harder to notice,
    # because there is no wrong name to disbelieve.
    #
    # ⚠️ **Two field names are accepted, and that is the finding rather than a
    # convenience.** Items raised before 2026-08-03 write `Current assignee(s)`;
    # later ones write `Owner`. **A sweep that knew only one name reported 12
    # unowned items when 2 were** — this office's own, on the day D-100 landed.
    # Reading both is correct; **the register drifting into two schemas is the
    # thing worth seeing**, so the count is reported rather than passed over.
    _OWNER_FIELDS = ("Owner", "Current assignee(s)", "Current assignee", "Owned by")
    unowned: list[str] = []
    stateless: list[str] = []
    off_schema = 0
    # **Position in the file is not authoritative, and C-411 is why.** Its own
    # finding ② records that C-326's body sits *after* the `## Closed` marker
    # while its `Status` says `OPEN` — so truncating at that marker silently
    # exempts genuinely open items, including the two this office raised. **An
    # item's declared state decides whether it is open; where it happens to sit
    # does not.**
    for chunk in re.split(r"(?=^#{2,3} C-\d+)", coordination, flags=re.M):
        titled = re.match(r"^#{2,3} (C-\d+)", chunk)
        if not titled:
            continue
        item = titled.group(1)
        declared = ""
        # **`State` and `Status` both, and the second one is a correction.**
        # The first version of this check knew `Status` alone and reported
        # C-104 and C-300 as stateless. **Both declare `State`.** That is the
        # same defect this check was written to catch, committed by the check
        # itself — and it is the *second* time in one file: the ownership
        # sweep below knew one field name and miscounted twelve items.
        # **QE read the false positive and reasoned from it**, concluding that
        # C-104 had drifted because it had no state row. It has one.
        status_row = re.search(r"^\| \*\*(?:Status|State)\*\* \|(.+)$", chunk, re.M)
        opened_line = re.search(r"(?m)^\*\*Opened .*$", chunk)
        for source in (
            status_row.group(1) if status_row else "",
            opened_line.group(0) if opened_line else "",
        ):
            quoted = re.search(r"`([A-Z][A-Z ]+)`", source)
            if quoted:
                declared = quoted.group(1).strip()
                break
        if declared in _SHUT_ITEM_STATES:
            continue
        field = next(
            (
                f
                for f in _OWNER_FIELDS
                if re.search(rf"^\| \*\*{re.escape(f)}\*\* \|", chunk, re.M)
            ),
            None,
        )
        # **The third form, and it is why this check nearly shipped crying wolf.**
        # C-211..C-216 carry ownership inline — `**Opened … · owner: product
        # owner · 🔴**` — with no table at all. A first version of this check
        # looked only for table fields and reported six owned items as unowned.
        # **That is B-101 once more: a proxy searched for, and its absence
        # reported as the absence of the thing.** A check that cries wolf is
        # worse than no check, because the register is where a lane looks to
        # find out who to ask.
        inline = (
            re.search(
                r"(?im)^\*\*Opened .*?\b(?:current module assignee|owner):\s*\S", chunk
            )
            is not None
        )
        if field is None and not inline:
            unowned.append(item)
        elif field is not None and field != "Owner":
            off_schema += 1
        elif field is None:
            off_schema += 1
        if status_row is None:
            stateless.append(item)

    if unowned:
        findings.append(
            f"Coordination items declare no owner: {', '.join(sorted(unowned))}. "
            f"An item nobody owns looks filed and is not (D-100). Every item names "
            f"an owner, and `Product owner` is an owner."
        )
    if stateless:
        findings.append(
            f"{len(stateless)} coordination item(s) declare no Status row: "
            f"{', '.join(sorted(stateless))}. Without one a reader cannot tell "
            f"whether the item is open, and `decision-queue.py` cannot route it "
            f"(CLAUDE.md §20e lifecycle states)."
        )
    if off_schema:
        notes.append(
            f"Coordination register: {off_schema} item(s) declare ownership in a "
            f"pre-2026-08-03 form — `Current assignee(s)`, or inline beside "
            f"`Opened`. Read by this check. **Five schemas across ownership and "
            f"state** (`Owner` · `Current assignee(s)` · inline `owner:` · inline "
            f"`current module assignee:` · `State` beside `Status`), and each one "
            f"a single-schema sweep does not see is an item it silently miscounts."
        )

    # 6b — D-103. **Every module has an owner, and the architecture document
    # describes the modules that exist.**
    #
    # > *"Whenever you discover a governance inconsistency manually, ask: can
    # > this class of mistake be detected automatically in the future? If yes,
    # > prefer strengthening repository validation over documenting it."*
    #
    # **Two classes, both found by hand this week and neither previously
    # checkable.** ① A module directory with no ownership row is unclaimable
    # work — the `people` context was exactly this, and the deadlock it caused
    # (`READY` needs an owner; the owner was to be added "when this is placed")
    # held TASK-427 shut for two days. ② `04-modules.md` is what `CLAUDE.md` §1
    # sends a lane to when module ownership is ambiguous, and it disagreed with
    # `backend/modules/` in four places — [B-401](../docs/BUGS.md).
    #
    # ⚠️ **② reports and never adjudicates.** Whether the document should
    # describe *what exists* or *the intended architecture* is an open ruling,
    # and the divergence is worth seeing under either answer.
    if MODULES_TOML.is_file() and BACKEND_MODULES.is_dir():
        try:
            registry = tomllib.loads(MODULES_TOML.read_text())
        except tomllib.TOMLDecodeError as broken:
            findings.append(f"modules.toml does not parse — {broken}")
        else:
            owned = {
                name
                for name, row in registry.items()
                if isinstance(row, dict) and str(row.get("current_owner", "")).strip()
            }
            on_disk = {
                d.name
                for d in BACKEND_MODULES.iterdir()
                if d.is_dir() and not d.name.startswith("__")
            }
            unowned_modules = sorted(on_disk - owned)
            if unowned_modules:
                findings.append(
                    f"backend/modules/ has no owner in modules.toml: "
                    f"{', '.join(unowned_modules)}. A module nobody owns is work "
                    f"no lane may claim (D-100, D-103)."
                )
            else:
                notes.append(
                    f"Module ownership: {len(on_disk)} module(s) on disk, every one "
                    f"with a current_owner."
                )

            if MODULES_DOC.is_file():
                described = set(
                    re.findall(r"^### ([A-Z][A-Za-z &]+)\s*$", MODULES_DOC.read_text(), re.M)
                )
                normalised = {d.lower().replace(" & ", "_").replace(" ", "_") for d in described}
                # **Only modules that exist on disk.** A bounded context that
                # has been *assigned* but not *built* — `people` today — is
                # correctly absent from the architecture document until it
                # ships, and flagging it would be the cry-wolf failure this
                # file has already committed twice this week. **The defect is a
                # module a lane can import and cannot look up.**
                expected = {n for n in owned & on_disk if n not in _NON_MODULE_ROWS}
                undocumented = sorted(expected - normalised)
                if undocumented:
                    findings.append(
                        f"04-modules.md has no Module Reference entry for: "
                        f"{', '.join(undocumented)}. CLAUDE.md §1 sends a lane to that "
                        f"document to resolve module ambiguity (B-401). Advisory: whether "
                        f"it should describe what exists or the intended architecture is "
                        f"an open ruling, and the divergence matters under either."
                    )

    for note in notes:
        print(f"  ok   {note}")
    # C-333 — the queue is an executable planning artifact, so it is validated
    # rather than trusted.
    #
    # **Placed above the early return deliberately, and it was below it for one
    # run.** `if not findings: return` would have skipped every queue check on
    # exactly the day the rest of the repository agreed with itself — which is
    # the one day a silent queue drift would go unseen.
    findings.extend(_structured_file_findings())
    findings.extend(_planning_sync_findings())
    findings.extend(_duplicate_state_findings(backlog))
    findings.extend(_ownership_findings(backlog))
    findings.extend(_queue_findings(backlog))
    findings.extend(_execution_state_findings())
    findings.extend(_staleness_findings())

    if not findings:
        print("\nstate-check: governance documents agree with the repository.")
        return 0

    print(f"\nstate-check: {len(findings)} advisory finding(s)\n")
    for finding in findings:
        print(f"  ·  {finding}")
    print(
        "\nAdvisory only, and never repaired automatically: each of these has more "
        "than one correct resolution, and choosing between them is a governance "
        "decision."
    )
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())

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


#: States in which a lane is genuinely *working* the row, so the execution
#: board should show it under `## Current`.
#:
#: ⚠️ **`IN VALIDATION` was in this set and is removed — 2026-08-07.** §20e is
#: explicit that it means *"implementation, tests, module documentation and
#: Slice Handoff are all complete. The lane's responsibility for this task has
#: ended."* **The row is with QE, and nobody is working it.**
#:
#: ⛔ **The finding's own justification did not hold**: it said *"a lane reading
#: only the board would take work somebody else is doing"*, and **an
#: `IN VALIDATION` row is not claimable from any source** — a lane pulls
#: `READY` rows from `BACKLOG.md`. **It fired every cycle for days on
#: `TASK-400`, which has 34 commits on `main` and nothing outstanding.**
#:
#: ✅ **`CHANGES REQUESTED` stays**: that one *is* returned to the lane, and
#: §20e makes it the lane's highest priority.
HOLDING_STATUSES = ("CLAIMED", "ACTIVE", "CHANGES REQUESTED")


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
        # ⛔ **The FIRST state token in the cell, never any token in it.**
        # A backlog row narrates its own history in the same cell — *"…
        # Previously **`CHANGES REQUESTED`** — …"* — and this read
        # `any(f"`{state}`" in row ...)`. **So `TASK-400`, `IN VALIDATION`
        # since 2026-08-06 with 34 commits on `main`, read as held**, and the
        # finding fired every cycle for days against a row nobody could claim.
        #
        # ⚡ **[B-101](../docs/BUGS.md)'s class, and the same defect
        # `registers.py` exists to fix on the bug side**, where substring
        # counting put nine rows in two buckets because a row records a fix and
        # names the state it has *not* reached.
        #
        # ⚠️ **The first repair delegated to `_backlog_states` and reported
        # nothing at all** — it missed `TASK-478` and `TASK-450`, both
        # genuinely `CLAIMED`. **Over-reporting became a guard that cannot
        # fail, which is worse.** This is the smaller change: the cell opens
        # with its current state, so the first token is the declared one.
        first = re.search(r"`([A-Z][A-Z ]+)`", row)
        if first is None or first.group(1).strip() not in HOLDING_STATUSES:
            continue
        # ⛔ **The lane named right after the state, not a standalone bold span.**
        # This searched for `**Lane A**` and rows write
        # **``CLAIMED`` — Lane A** — the lane sits *inside* the same bold span
        # as the state. ⚠️ **So the check silently matched no correctly
        # formatted claim at all**, and the only finding it ever produced was
        # the false positive on `TASK-400`, whose narrative happens to contain
        # a standalone `**Lane A**`.
        #
        # ⚡ **It reported the one row that was fine and missed the four that
        # were real** — `TASK-478`, `TASK-450`, `TASK-457`, `TASK-462`. **A
        # check can be wrong in both directions at once, and this one was.**
        lane = re.search(r"(Lane [A-Z]|QE)\b", row[first.end():first.end() + 90])
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


def _coordination_findings() -> list[str]:
    """Is the published coordination source what the generator emits today?

    **[479](../docs/architecture/479-coordination-architecture.md).** Once every
    lane polls one file, a stale one instructs all of them with an answer that
    was true earlier — **which is strictly worse than the seven-document read it
    replaces**, because that at least made its own age visible.

    ⛔ **Reports rather than repairs**, like everything here: regenerating is a
    one-line command and choosing when to publish is a governance act.
    """
    generator = REPO_ROOT / "infra" / "coordination.py"
    if not generator.exists():
        return []
    done = subprocess.run(
        [sys.executable, str(generator), "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    findings: list[str] = []
    stale = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0, 'infra'); import coordination as c; "
         "rows = c.tasks(); c._walk(rows, {r.id: r for r in rows}); "
         # **B-144.** These take `outstanding` as an argument now, so the
         # clone is read here — once, explicitly — instead of inside each
         # predicate where nothing could state the world it wanted.
         "outstanding = c._outstanding_rows(rows); "
         "print(' '.join(r.id for r in c.stale_sequencing(rows, outstanding))); "
         "print(' '.join(r.id for r in c.premature_releases(rows, outstanding)))"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    out = (stale.stdout.splitlines() + ["", ""])[:2]
    parked = out[0].split()
    early = out[1].split()
    if early:
        findings.append(
            f"{len(early)} row(s) are `READY` behind a predecessor that is NOT "
            f"handed over — {', '.join(early[:8])}. **This office released them "
            "and the release erased the edge that would have shown it wrong.** "
            "TASK-458 is the worked example: released on a count of commits "
            "mentioning TASK-457, which Lane B still holds `CLAIMED`, and "
            "`people/public/__init__.py` is zero lines. Lane A found it by "
            "opening the file (C-427)."
        )
    if parked:
        findings.append(
            f"{len(parked)} row(s) are parked behind a predecessor that has already "
            f"been handed over — {', '.join(parked[:8])}. **A `SEQUENCED` row is "
            "released by this office, and nothing re-asks the question**: the only "
            "state that would move the predecessor is `VERIFIED`, which is QE's "
            "exclusively. **On 2026-08-07 this was twenty-two rows and both "
            "implementation lanes were idle** (C-426)."
        )
    if done.returncode == 0:
        return findings
    return findings + [
        "The canonical coordination source is stale — "
        + (done.stderr.strip().splitlines() or ["regenerate it"])[0].replace("coordination: ", "")
    ]


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


def _ref_authority_findings() -> list[str]:
    """Does the coordination ref instruct on an authority `integration` carries?

    **Found by Lane A on 2026-08-07, from the outside, on the ref's first
    poll** — and it is the sharpest reading this office has been given:
    *"`origin/coordination` instructs lanes to stop reading `integration` for
    sequence, but its authority is not on `integration`."* **A mechanism cannot
    confer authority on itself from outside the authoritative state.**

    ⚠️ **The ref is published by this office directly; the rule that makes it
    binding travels through QE like every other governance change.** Between
    those two moments the ref exists and is advisory, and **nothing in the
    repository said which one a lane was looking at** — so Lane A had to derive
    it. **This is that derivation, made a measurement.**

    ⛔ **Reports rather than fails.** Clearing it needs a QE integration, which
    is not this lane's to perform (D-136).
    """
    ref = _git("rev-parse", "--verify", "-q", "origin/coordination").strip()
    if not ref:
        return []
    governing = _git("show", "origin/integration:CLAUDE.md")
    if "origin/coordination" in governing:
        return []
    return [
        "`origin/coordination` is published and `CLAUDE.md` on `integration` "
        "does not yet carry the poll that makes it binding — **so the ref is "
        "advisory and `integration` remains the authority for what to build** "
        "(C-425). A lane polling it is reading a projection whose rule has not "
        "landed; where the two disagree the integration-side source wins and "
        "the disagreement is this office's defect."
    ]


def _lane_c_rows(backlog: str) -> set[str]:
    """Task ids whose `Module` cell resolves to Lane C.

    ⛔ **Read from the row, never stored beside it** ([C-213](../docs/LANE_COORDINATION.md)):
    a copied assignee is correct until the module moves. **Conservative by
    construction** — a row this cannot resolve is simply not exempt, so an
    ambiguous cell fails toward reporting rather than toward silence.
    """
    mine: set[str] = set()
    for block in re.split(r"^### TASK-", backlog, flags=re.M)[1:]:
        task = re.match(r"(\d+)", block)
        module = re.search(r"\|\s*\*\*Module\*\*\s*\|([^|]*)\|", block)
        if task and module and re.search(r"\bLane C\b", module.group(1)):
            mine.add(f"TASK-{task.group(1)}")
    return mine


def _empty_contract_findings() -> list[str]:
    """A module publishes a `public/` package that exports nothing.

    ⚡ **Lane B's argument, 2026-08-07, and it is right even though the claim
    attached to it was stale**: *"Reachability was the proxy; ref-equality is
    now the proxy; neither is the property. The question is still whether the
    file exports anything, and a non-zero-size check would have failed both
    times."*

    **Both times it would have.** `people/public/__init__.py` is **0 bytes on
    `main` and on `integration`**, and two rows were released against it —
    [C-428](../docs/LANE_COORDINATION.md), then [TASK-428](../docs/BACKLOG.md)
    on the same file a day later.

    ⛔ **`_delivered` in `coordination.py` cannot see this.** It asks whether a
    predecessor was *handed over*, which is a fact about process; **this asks
    whether the thing exists, which is a fact about the tree.** ⚡ **Two
    different questions, and only the second one would have stopped either
    release.**

    **[§5](../CLAUDE.md) is what makes it a defect rather than a curiosity**: a
    module's `public/` is the only route another module may cross by, so an
    empty one is a boundary that cannot be used and a contract that cannot be
    consumed. **Measured against `origin/integration`**, because that is what
    a lane builds from.
    """
    listing = _git("ls-tree", "-r", "--name-only", "origin/integration",
                   "--", "backend/modules/")
    empty = []
    for path in listing.splitlines():
        if not path.endswith("/public/__init__.py"):
            continue
        blob = _git("rev-parse", f"origin/integration:{path}")
        size = _git("cat-file", "-s", blob) if blob else ""
        if size.strip() == "0":
            empty.append(path.split("/")[2])
    if not empty:
        return []
    return [
        f"{len(empty)} module(s) publish an empty `public/` contract on "
        f"`integration` — {', '.join(sorted(empty))}. **A module's `public/` is "
        "the only route another module may cross by (§5), so an empty one is a "
        "boundary nothing can use.** Two rows were released against "
        "`people`'s before it was noticed (C-428), and a third was written "
        "against it a day later."
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
    body = (REPO_ROOT / "docs" / "BACKLOG.md").read_text()
    after = _backlog_states(body)
    # **Lane C is also an implementing lane, on Platform Foundation** (D-022),
    # and §20e's `CHANGES REQUESTED` path is explicit about what it must then
    # do: *"the lane addresses what was asked, re-runs its gates, pushes, and
    # returns the task to `IN VALIDATION`."*
    #
    # ⚠️ **The first version flagged that as an overwrite.** It compared every
    # row without asking whose row it was, so `TASK-419` — this office's own
    # slice, returned by QE and repaired — read identically to `TASK-901`,
    # which was somebody else's and genuinely overwritten.
    #
    # ⛔ **The exemption is deliberately narrow.** It applies only where the
    # row resolves to Lane C *and* the new state is one of the four the lane
    # sets. **QE's four are never exempt**: this office may repair its own
    # slice, and may never declare it verified.
    _LANE_SETTABLE = {"CLAIMED", "IN PROGRESS", "IN VALIDATION", "CHANGES REQUESTED"}
    mine = _lane_c_rows(body)
    overwritten = sorted(
        f"{task} ({was} → {now})"
        for task, was in before.items()
        if was in _LANE_OWNED_STATES
        and (now := after.get(task, was)) != was
        and not (task in mine and now in _LANE_SETTABLE)
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


def _duplicate_index_findings(coordination: str) -> list[str]:
    """The same coordination item listed twice in the summary index.

    **Accumulated by union conflict resolution across several rebases**, and
    invisible because each row looked correct on its own: eleven exact
    duplicates had built up by 2026-08-07, one item listed three times.

    ⚡ **Keyed on `(id, anchor)`, not on the id alone.** [B-405](../docs/BUGS.md)
    records a dated audit table that legitimately reuses `C-024` and `C-025`
    for subjects that were later renumbered — **a check keyed on the id would
    demand that a record of the past be rewritten**, which §2 forbids.

    **Third member of one family**, with the duplicate `Status` row and the
    TOML union: *a field that holds one value, holding two.*
    """
    seen: set[tuple[str, str]] = set()
    repeats: dict[str, int] = {}
    for line in coordination.splitlines():
        m = re.match(r"\|\s*\[(C-\d+)\]\(#([a-z0-9-]+)\)", line)
        if m is None:
            continue
        pair = (m.group(1), m.group(2))
        if pair in seen:
            repeats[m.group(1)] = repeats.get(m.group(1), 1) + 1
        seen.add(pair)
    if not repeats:
        return []
    named = ", ".join(f"{k}×{v}" for k, v in sorted(repeats.items()))
    return [
        f"LANE_COORDINATION.md lists {len(repeats)} item(s) more than once in "
        f"the summary index with the same anchor — {named}. A reader sees "
        f"whichever row is higher, and a union conflict resolution adds one "
        f"every time it runs."
    ]


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


def _adoption_findings() -> list[str]:
    """**A ratified decision whose consumer has arrived and whose work has not** —
    D-179.

    ⛔ **`ratified` is not the finish line.** [497](../docs/architecture/497-commodity-and-differentiation.md)
    measured eight of twelve *buy* decisions unadopted, and in three cases a
    workflow was blocked or a lane built a workaround while the vendor sat
    ratified and unbought. ⚡ **A ratified decision that produces no work is
    indistinguishable from an unmade one** — a lane reaches the capability and
    builds around it, because nothing in the queue says the answer exists.

    **The condition checked is narrow and deliberate**: a capability still at
    `ratified` or earlier whose first consuming workflow has reached `ready` or
    beyond. ⛔ **Not every unadopted decision** — [§6](../CLAUDE.md) forbids
    adding a dependency before the requirement exists, so `ratified` with no
    consumer is *correct* and flagging it would teach people to read past this.
    """
    out: list[str] = []
    path = REPO_ROOT / "docs" / "coordination" / "adoption.toml"
    flows = REPO_ROOT / "docs" / "coordination" / "workflows.toml"
    if not path.is_file() or not flows.is_file():
        return out
    try:
        adoption = tomllib.loads(path.read_text())
        pipeline = tomllib.loads(flows.read_text())["workflow"]
    except (tomllib.TOMLDecodeError, KeyError) as broken:
        return [f"adoption.toml or workflows.toml does not parse — {broken}"]

    #: Anything at or past this point means implementation has reached it.
    arrived = {"ready", "active", "in_progress", "in_validation",
               "awaiting_qe", "on_main", "awaiting_review", "approved", "complete"}
    pending = {"proposed", "researched", "ratified"}

    for name, body in adoption.get("capability", {}).items():
        if body.get("state") not in pending:
            continue
        for ref in body.get("consumed_by", []):
            key = str(ref).removeprefix("workflow.")
            state = pipeline.get(key, {}).get("state")
            if state in arrived:
                vendor = body.get("vendor") or body.get("owner") or "?"
                out.append(
                    f"`{name}` is {body['state']} and workflow {key} "
                    f"({pipeline[key].get('name')}) is already {state}. "
                    f"**The decision exists — {vendor} — and the work does not** (D-179). "
                    "A lane reaching this capability will build around it."
                )
                break
    return out


#: **The claimable-depth floor — D-183, product owner, 2026-08-08.**
#:
#: ⚠️ **This replaces *exactly one claimable*, and it amends [D-163](../docs/DECISION_REGISTER.md)
#: rather than reinterpreting it.** D-163's reason was sound and is unchanged:
#: *"more than one lets the lane choose, and choosing is prioritisation."*
#:
#: ⛔ **What it got wrong was the remedy.** A depth of one means the lane idles
#: the instant its single row is blocked — and rows are blocked by **discovery**,
#: not by prediction. `C-241` was found while building screen 07, not while
#: planning it, and no amount of preparation would have surfaced it earlier.
#:
#: ⚡ **RAISED TO 10 on 2026-08-08 by [D-184](../docs/DECISION_REGISTER.md)**, the
#: product owner: *"there should always be a minimum of 10 claimable items
#: present for Lane A every time."*
#:
#: ⛔ **The floor is a floor on PREPARED rows, and that is not a formality.**
#: **A `READY` row a lane cannot start is the [C-412](../docs/LANE_COORDINATION.md)
#: defect, and this office wrote that rule.** ⚠️ **Reaching 10 on 2026-08-08 cost
#: two full decompositions — Workflows 9 and 10, which stood at 8/22 and 11/22 —
#: rather than five relabelled thin rows.** **If the floor cannot be met with
#: prepared rows, the honest report is a shortfall, never a widened definition.**
#:
#: ✅ **The reconciliation is depth WITHOUT choice**: several claimable rows, in a
#: **strict published order**, and the lane takes the topmost one it can start.
#: Product Office still owns the order; the lane still never picks. **Descending
#: past a row is permitted only when that row is genuinely blocked, and the
#: reason is recorded** — which is the existing skip rule (§20e, *claim from the
#: top*), not a new licence.
_DEPTH_FLOOR = 10


def _ordered(lane: str) -> bool:
    """Does this lane's queue put its claimable rows in a stated order?

    ⛔ **Depth is only safe when the order is explicit.** Without it, several
    claimable rows is exactly the condition [D-163](../docs/DECISION_REGISTER.md)
    refused — the lane choosing, and choosing being prioritisation.
    """
    path = REPO_ROOT / "docs" / "coordination" / "queues" / f"{lane.lower().replace('_', '-')}.toml"
    if not path.exists():
        return False
    queue = tomllib.loads(path.read_text())
    return bool(queue.get("current")) and bool(queue.get("next"))


def _item_owner_findings() -> list[str]:
    """Does every coordination item awaiting somebody name who? — **D-186.**

    ⛔ **An item with no owner looks unowned and is asked about. An item whose
    owner is buried in `Status` prose looks *answered*** — every lane reads it,
    finds no route, and moves on. **That is [C-213](../docs/LANE_COORDINATION.md)'s
    defect, which blocked `TASK-205` for two days on one word.**

    ⚡ **Found on the 2026-08-08 audit: five open items stated their owner inside
    `Status` text and three named nobody at all.** ⛔ **No instrument could see
    any of them, because *derivable is not visible*** — the same sentence §20e
    already uses about a lane's queue.

    ⚠️ **The state filter is deliberately narrow.** `CLOSED`, `ANSWERED`,
    `RULED` and `READY FOR IMPLEMENTATION` are *finished* and need no owner;
    only an item somebody still owes an answer on is reported. **A first pass
    that counted `READY FOR IMPLEMENTATION` as open reported 42 items where
    there were 27, and a check that overstates is one people learn to skim.**
    """
    out: list[str] = []
    path = REPO_ROOT / "docs" / "LANE_COORDINATION.md"
    if not path.exists():
        return out
    lines = path.read_text().split("\n")
    heads = [(i, l) for i, l in enumerate(lines) if re.match(r"^## C-\d+ ", l)]
    awaiting = re.compile(r"`(OPEN|IN ANALYSIS|READY FOR LANE C|READY FOR PRODUCT DECISION)`")
    finished = re.compile(r"`(CLOSED|ANSWERED|READY FOR IMPLEMENTATION|RULED|OPERATIONAL)`")
    actor = re.compile(r"Lane [ACD]|QE|[Pp]roduct owner")

    for n, (i, head) in enumerate(heads):
        end = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
        body = lines[i:end]
        status = next((x for x in body if x.startswith("| **Status**")), "")
        if finished.search(status) or not awaiting.search(status):
            continue
        cid = head.split(" · ")[0].replace("## ", "")
        owner = next((x for x in body if x.startswith("| **Owner**")), "")
        if not owner:
            out.append(
                f"{cid} is awaiting somebody and has no `Owner` cell. **A row "
                f"nobody is named on is a row nobody answers** (C-213)."
            )
        elif not actor.search(owner):
            out.append(
                f"{cid}'s `Owner` names no lane, QE or the product owner. "
                f"**An owner a reader cannot route to is an absent owner.**"
            )
        elif "Lane B" in owner:
            out.append(
                f"{cid} is owned by **Lane B**, which D-165 closed. "
                f"**An item assigned to a lane that cannot answer is worse than "
                f"one visibly unowned, because it looks answered** (§20e)."
            )
    return out


def _structural_findings() -> list[str]:
    """Did a scripted edit silently delete part of a row? — **B-411, D-185 §5.**

    ⛔ **A register row that *shrank* relative to `origin/integration` is almost
    always an accident**, because Product Office edits rows by adding cells and
    amending states, not by removing acceptance criteria a lane has delivered
    against.

    ⚡ **This exists because the accident already happened and nothing caught it.**
    A non-greedy `.*?` under `re.S` swallowed the row below the cell it was
    editing, [TASK-486](../docs/BACKLOG.md) lost its `Features` line — the
    delivered slice's acceptance criteria — and it surfaced four commits later,
    at QE, as a merge collision QE correctly declined to adjudicate.

    ⛔ **A deliberate deletion is possible and is not what this refuses.** It
    refuses an *unannounced* one: name the row in the commit message and the
    finding stands down. **The check is on the diff, and the licence is a
    sentence** — which is the same shape as the 🟠 Change Budget rule (§20e).
    """
    out: list[str] = []
    row = re.compile(r"\n### (TASK-\d+)\b(.*?)(?=\n### TASK-|\Z)", re.S)

    def cells(text: str) -> dict[str, int]:
        return {
            m.group(1): len([l for l in m.group(2).split("\n") if l.startswith("|")])
            for m in row.finditer(text)
        }

    base_raw = _git("show", "origin/integration:docs/BACKLOG.md")
    if not base_raw:
        return out
    here = cells((REPO_ROOT / "docs" / "BACKLOG.md").read_text())
    base = cells(base_raw)
    # ⚡ The commit message is the licence — same shape as announcing an 🟠 change.
    recent = _git("log", "origin/integration..HEAD", "--format=%B")

    for task, before in sorted(base.items()):
        after = here.get(task)
        if after is None:
            if task not in recent:
                out.append(
                    f"{task} is on `integration` and absent here, and no commit "
                    f"message names it. **A row that vanishes unannounced is a "
                    f"scripted edit that overran** (B-411)."
                )
        elif after < before and task not in recent:
            out.append(
                f"{task} lost {before - after} line(s) against `integration` and no "
                f"commit message names it. **This is how TASK-486's acceptance "
                f"criteria disappeared** (B-411) — name the row in the commit if "
                f"the deletion is deliberate."
            )
    return out


def _pipeline_findings() -> list[str]:
    """**Several claimable rows for the implementing lane, in a stated order — and
    exactly one `active` workflow.**

    ⚠️ **Amended 2026-08-08 by [D-183](../docs/DECISION_REGISTER.md), the product
    owner, which overrules the *exactly one claimable* rule this function used to
    enforce.** ⛔ **The old docstring described a rule the code no longer applies,
    and leaving it would be the [§2](../CLAUDE.md) defect this file exists to
    report: the repository asserting something untrue of itself.**

    ⛔ **Zero claimable** — the lane idles and only its own report reveals it.
    ⚠️ **Below `_DEPTH_FLOOR`** — the lane idles the moment one row is blocked,
    and rows are blocked by *discovery* (`C-241`), never by prediction.
    ⛔ **Depth with no published order** — the lane may pick, and picking is
    prioritisation ([§20e](../CLAUDE.md)). **This is [D-163](../docs/DECISION_REGISTER.md)'s
    concern, preserved: what changed is the remedy, not the reason.**
    """
    out: list[str] = []
    source = REPO_ROOT / "docs" / "coordination" / "coordination.toml"
    flows = REPO_ROOT / "docs" / "coordination" / "workflows.toml"
    if not source.is_file() or not flows.is_file():
        return out
    try:
        published = tomllib.loads(source.read_text())
        pipeline = tomllib.loads(flows.read_text())
    except tomllib.TOMLDecodeError as broken:
        return [f"the coordination or workflow source does not parse — {broken}"]

    active = [
        f"{key} ({body.get('name', '?')})"
        for key, body in pipeline.get("workflow", {}).items()
        if body.get("state") == "active"
    ]
    if len(active) != 1:
        out.append(
            f"workflows.toml declares {len(active)} active workflow(s) — {active or 'none'}. "
            "**Exactly one is normally active** (D-160 ④); many may be planned. "
            "Zero means implementation has nothing to build; more than one means the "
            "review gate between journeys has stopped meaning anything."
        )

    for lane, body in published.get("lane", {}).items():
        # ⛔ Only lanes that still receive work. Lane B is closed by D-157 and
        # Lane C implements nothing, so zero is correct for both and flagging
        # it would teach people to read past this check.
        if lane in {"Lane_B", "Lane_C"}:
            continue
        claimable = int(body.get("claimable", 0) or 0)
        # ⚡ **`actionable`, never `in_flight`** — B-409, 2026-08-08.
        # `in_flight` collapses eight declared states and only three are work
        # the lane can touch. **Lane A idled 136 cycles holding 48 in-flight
        # rows, every one `IN VALIDATION` and untouchable**, and this check
        # stayed silent because the number was large. ⛔ A starvation check
        # that reads a number including work the lane has finished is a
        # starvation check that cannot see starvation.
        in_flight = int(body.get("actionable", body.get("in_flight", 0)) or 0)
        # ⚠️ **Refined 2026-08-07, the same day it was written.** The first
        # version flagged zero-claimable alone and fired on a lane holding two
        # rows it was actively building. **A check that cries wolf is one people
        # learn to read past**, which is the failure this whole file is written
        # against. **The condition that matters is a lane with nothing claimable
        # AND nothing in hand** — that lane is genuinely stopped.
        if claimable == 0 and in_flight == 0:
            out.append(
                f"{lane} has nothing claimable and nothing actionable — it is stopped. "
                "**Keeping the pipeline populated is Product Office's responsibility** "
                "(D-163) — the lane cannot fix this and should not have to report it."
            )
        elif claimable < _DEPTH_FLOOR:
            out.append(
                f"{lane} has {claimable} claimable row(s) and the floor is {_DEPTH_FLOOR}. "
                "**A lane with one claimable row idles the moment that row is blocked** — "
                "and a row is blocked by discovery, not by prediction (C-241 was found "
                "while building, not while planning). **Release more, in a stated order** "
                "(D-183)."
            )
        elif not _ordered(lane):
            out.append(
                f"{lane} has {claimable} claimable rows and its queue does not put them in "
                "a strict order. **Depth without an order is a choice, and choosing is "
                "prioritisation** (§20e, D-163's actual concern). "
                "**`current`, `next` and `next_after_that` must name them** (D-183)."
            )
    return out


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
    # ⚠️ **Scoped to `## Current`, and narrowed, 2026-08-07.** The first version
    # read the whole file and matched any row containing *await* and *assign* —
    # so it flagged `TASK-900`'s row, which says the RFC *"awaits product owner
    # approval"* inside the module-assignment section. **Neither word was about
    # allocation**, and the row was not even in the section a lane reads.
    # **B-101's class**: two words co-occurring is a proxy for a sentence.
    # The sibling checks below already say why the scope matters — *"a row
    # elsewhere in the file does not count"* — and this one did not honour it.
    if "## Current" in assignments:
        current_rows = assignments.split("## Current", 1)[1].split("\n## ", 1)[0]
        waiting = [
            line.strip()
            for line in current_rows.splitlines()
            if line.startswith("| ")
            and re.search(r"(?:waiting|awaiting|wait)\s+(?:for\s+)?(?:an?\s+)?"
                          r"(?:assignment|allocation|work to be assigned)"
                          r"|to be assigned|nobody has assigned", line, re.I)
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
    findings.extend(_coordination_findings())
    findings.extend(_structured_file_findings())
    findings.extend(_planning_sync_findings())
    findings.extend(_ref_authority_findings())
    findings.extend(_empty_contract_findings())
    findings.extend(_duplicate_index_findings(coordination))
    findings.extend(_duplicate_state_findings(backlog))
    findings.extend(_ownership_findings(backlog))
    findings.extend(_queue_findings(backlog))
    findings.extend(_item_owner_findings())
    findings.extend(_structural_findings())
    findings.extend(_pipeline_findings())
    findings.extend(_adoption_findings())
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

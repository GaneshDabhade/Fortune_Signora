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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from registers import bug_rows, conflict_markers, malformed_tables  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS = REPO_ROOT / "backend" / "migrations" / "versions"


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


def _latest_certification() -> dict[str, object] | None:
    manifest = REPO_ROOT / "certification" / "manifest.json"
    if not manifest.exists():
        return None
    runs = json.loads(manifest.read_text()).get("runs") or []
    return runs[-1] if runs else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    findings: list[str] = []
    notes: list[str] = []

    main_sha = _git("rev-parse", "--short=7", "main")
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
                    f"BACKLOG.md says {lane} holds TASK-{task}; ACTIVE_ASSIGNMENTS.md "
                    f"has no row for it. A lane reading only the board would take work "
                    f"somebody else is doing."
                )
            elif lane not in holders:
                findings.append(
                    f"BACKLOG.md says {lane} holds TASK-{task}; the board says "
                    f"{' and '.join(sorted(holders))}. One of the two is wrong, and "
                    f"neither is authoritative over the other."
                )

        if not contested and not unknown:
            ready = len(re.findall(r"^### TASK-\d+", backlog, re.M))
            notes.append(
                f"Backlog: {len(known)} task(s), {ready} READY, no task claimed twice."
            )

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

    for note in notes:
        print(f"  ok   {note}")
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

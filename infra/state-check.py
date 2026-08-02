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


HOLDING_STATUSES = ("CLAIMED", "ACTIVE", "IN VALIDATION")


def _backlog_claims(backlog: str) -> dict[str, str]:
    """`{task id: lane}` for every task a backlog says somebody is holding.

    Parsed per `### TASK-nnn` block rather than line by line, because a lane's
    claim note frequently names *other* tasks — the reason it passed them over —
    and a scan that saw only `TASK-nnn` near `Lane X` would read those as claims.
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

    Scoped the same way check 3 is, and for the same reason: *Recently completed*
    names tasks that have shipped, and counting those as live claims would make
    every finished task look contested forever.
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
        if not lane.startswith("Lane") and lane != "QE":
            continue
        # The task cell only. A `Next action` may reference another task.
        for task in re.findall(r"\bTASK-(\d+)\b", cells[2] if len(cells) > 2 else ""):
            claims.setdefault(task, set()).add(lane)
    return claims


def _lane_branches() -> list[str]:
    """Every lane's published branch, from local remote-tracking refs.

    **No network.** These refs are whatever the last `git fetch` left behind, so
    the check is only as current as the caller's fetch — which is stated in the
    finding rather than hidden, because a stale answer presented as a fresh one
    is worse than no answer.
    """
    refs = _git("for-each-ref", "--format=%(refname:short)", "refs/remotes/origin/lane-*")
    return [ref for ref in refs.splitlines() if ref]


def _file_at(ref: str, relative: str) -> str:
    return _git("show", f"{ref}:{relative}")


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
    if main_sha and status:
        named = _newest_named_commit(status, main_sha)
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
    open_section = bugs.split("## Verified")[0] if "## Verified" in bugs else bugs
    if "🔴" in open_section and "| 🔴 | Blocks a milestone |" not in open_section:
        findings.append(
            "BUGS.md appears to carry an open 🔴. `integration` never fast-forwards "
            "to `main` with one open."
        )

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
        board_rows = [
            line for line in assignments.splitlines()
            if line.startswith("| ") and "TASK-" in line
        ]

        # (a) two lanes holding one task — the race the protocol exists to lose safely.
        held: dict[str, list[str]] = {}
        for row in board_rows:
            lane = row.split("|")[1].strip().strip("*")
            for task in re.findall(r"\bTASK-(\d+)\b", row):
                held.setdefault(task, []).append(lane)
        contested = {t: lanes for t, lanes in held.items() if len(set(lanes)) > 1}
        if contested:
            for task, lanes in contested.items():
                findings.append(
                    f"TASK-{task} is claimed by {' and '.join(sorted(set(lanes)))} at once. "
                    f"The Task Claim Protocol requires the later claim to be abandoned "
                    f"(CLAUDE.md §20e)."
                )

        # (b) a board row naming a task the backlog has never heard of.
        unknown = {t for row in board_rows for t in re.findall(r"\bTASK-(\d+)\b", row)} - known
        if unknown:
            findings.append(
                f"ACTIVE_ASSIGNMENTS.md names {', '.join('TASK-' + t for t in sorted(unknown))}, "
                f"which BACKLOG.md does not define. A claim must refer to a task that exists."
            )

        # (c) the backlog and the board must name the same holder.
        #
        # Two files record one claim, so they can disagree — and the disagreement
        # is not cosmetic: a lane reading the backlog and a lane reading the board
        # would reach different conclusions about whether a task is free.
        board_here = _board_claims(assignments)
        for task, lane in _backlog_claims(backlog).items():
            holders = board_here.get(task, set())
            if not holders:
                findings.append(
                    f"BACKLOG.md says {lane} holds TASK-{task}; ACTIVE_ASSIGNMENTS.md "
                    f"has no row for it. A claim is recorded in both, and a lane "
                    f"reading only the board would take work somebody else holds."
                )
            elif lane not in holders:
                findings.append(
                    f"BACKLOG.md says {lane} holds TASK-{task}; the board says "
                    f"{' and '.join(sorted(holders))}. One of the two is wrong."
                )

        if not contested and not unknown:
            ready = len(re.findall(r"^### TASK-\d+", backlog, re.M))
            notes.append(
                f"Backlog: {len(known)} task(s), {ready} READY, no task claimed twice."
            )

    # 5d — the collision the protocol actually loses to, and the one 5c cannot see.
    #
    # **A claim lives on the claiming lane's branch until it merges.** Protocol
    # step 8 pulls `integration` and looks at what came back, so two lanes can each
    # push a claim, each see an unchanged `integration`, and each conclude they
    # were first. By the time both claims are in one file, somebody has already
    # reconciled them — which is why 5c, reading one working tree, can only ever
    # report a race that is already over.
    #
    # Found the hard way: Lane B claimed TASK-002 on 2026-08-02 and discovered
    # Lane A holding it only by reading their branch by hand (C-019).
    #
    # This reads every lane's published backlog instead. It is advisory like
    # everything else here — the protocol decides who abandons, not this script.
    branches = _lane_branches()
    if branches:
        across: dict[str, dict[str, str]] = {}
        for ref in branches:
            published = _file_at(ref, "docs/BACKLOG.md")
            if not published:
                continue
            for task, lane in _backlog_claims(published).items():
                across.setdefault(task, {})[lane] = ref

        collisions = {t: holders for t, holders in across.items() if len(holders) > 1}
        for task, holders in sorted(collisions.items()):
            who = ", ".join(f"{lane} ({ref})" for lane, ref in sorted(holders.items()))
            findings.append(
                f"TASK-{task} is claimed on more than one lane branch: {who}. "
                f"The Task Claim Protocol requires the later claim to be abandoned "
                f"— step 9, and the lane that pushed second is the one that drops it."
            )
        if not collisions:
            notes.append(
                f"No task claimed on two lane branches ({len(branches)} branch(es) "
                f"read from remote-tracking refs — as current as the last fetch)."
            )
    else:
        notes.append(
            "No lane branches in remote-tracking refs; cross-branch claim check "
            "skipped. Run `git fetch origin` for it to mean anything."
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

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
    # The dashboard is written *after* the promotion it describes, so the commit
    # carrying it is one ahead of the commit it names. Accepting `main`'s parent
    # is not a loosening: a check nothing can satisfy would be failed every cycle
    # and then ignored, which is worse than not checking. Anything older than the
    # parent is genuinely stale and still reported.
    parent_sha = _git("rev-parse", "--short=7", "main~1")
    status = _read("PROJECT_STATUS.md")
    handoff = _read("docs/SESSION_HANDOFF.md")
    assignments = _read("docs/ACTIVE_ASSIGNMENTS.md")
    bugs = _read("docs/BUGS.md")
    coordination = _read("docs/LANE_COORDINATION.md")

    # 1 — the dashboard should name the promoted commit.
    if main_sha and status:
        if main_sha not in status and parent_sha not in status:
            findings.append(
                f"PROJECT_STATUS.md does not mention `main` ({main_sha}). Either the "
                f"dashboard predates the promotion, or Repository Closeout did not "
                f"run (lifecycle stage 5)."
            )
        else:
            named = main_sha if main_sha in status else f"{parent_sha}, the commit it closed out"
            notes.append(f"PROJECT_STATUS.md names `main` ({named}).")

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
    handoff_names_head = main_sha in handoff or parent_sha in handoff
    if main_sha and handoff and not handoff_names_head and (main_sha in status or parent_sha in status):
        findings.append(
            "SESSION_HANDOFF.md does not mention the promoted commit while "
            "PROJECT_STATUS.md does. A cold session reads the handoff first."
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

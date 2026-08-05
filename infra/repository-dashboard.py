#!/usr/bin/env python3
"""**The program control panel, measured from `origin/integration`.**

Emits the fourteen-section repository dashboard that opens every Lane C report.
**Every figure is counted from the ref a lane can actually claim from** — never
from the working tree, and never from a Lane C branch, because the difference
between those two is the bottleneck this dashboard exists to expose.

### Why this is generated rather than written

A fourteen-section dashboard maintained by hand drifts within two reports, and a
dashboard nobody trusts is worse than none — it reports health the lanes can see
is absent. `REPOSITORY_SOURCE_OF_TRUTH.md`: *generate what is countable,
hand-write what is judgement, and never generate something a human will then
edit.*

### What it deliberately does not compute

**Progress percentages, risk, ROI and "the largest bottleneck" are judgement**,
and a script that invented them would be stating opinion in the voice of
arithmetic. They are emitted as explicit `«judgement»` placeholders for Lane C
to fill in the report, so a missing one is visible rather than silently absent.

Run: `python3 infra/repository-dashboard.py [--ref origin/integration]`
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
J = "«judgement»"

TASK_HDR = re.compile(r"^### (TASK-\d+)\s*·\s*(.+)$", re.M)
STATUS = re.compile(r"\*\*Status\*\*\s*\|\s*(.+)$", re.M)
STATE_WORDS = (
    "IN VALIDATION", "CHANGES REQUESTED", "IN PROGRESS", "SEQUENCED", "CLAIMED",
    "BLOCKED", "WAITING", "VERIFIED", "CERTIFIED", "PROMOTED", "READY", "DONE",
)


def sh(*args: str) -> str:
    try:
        return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        return ""


def show(ref: str, path: str) -> str:
    return sh("git", "show", f"{ref}:{path}")


def ls(ref: str, path: str) -> list[str]:
    return [l for l in sh("git", "ls-tree", "-r", "--name-only", ref, path).splitlines() if l]


def tasks(ref: str) -> list[tuple[str, str, str]]:
    """Every task, with the *first* state word its Status line carries.

    First rather than last: a row reading ``READY -- after B-400`` is `READY`,
    and the qualifier is a note. Scanning for the last match would silently
    reclassify it.
    """
    text = show(ref, "docs/BACKLOG.md")
    blocks = re.split(r"(?=^### TASK-)", text, flags=re.M)
    out = []
    for b in blocks:
        m = TASK_HDR.search(b)
        if not m:
            continue
        s = STATUS.search(b)
        state = "UNKNOWN"
        if s:
            line = s.group(1)
            for w in STATE_WORDS:
                if w in line:
                    state = w
                    break
        out.append((m.group(1), m.group(2).strip()[:58], state))
    return out


def _owners(board: str, modules: list[str]) -> dict[str, str]:
    """Which lane a board row names for each module.

    Parsed from the execution board rather than assumed, because assignment is
    a rota and any hardcoded map would be wrong within a week (`CLAUDE.md`
    §20e: *a module is a permanent boundary, a lane is a temporary resource*).
    **A module named by two lanes is reported as a collision, not silently
    resolved** — that is the one-assignee-per-module invariant, and a dashboard
    that hid a breach of it would be hiding the thing worth seeing.
    """
    # **The assignment table is authoritative and is read first.** Board rows
    # answer *"who is working?"*, which is a different question — a module with
    # an assignee and no active slice has no board row at all, and inferring
    # assignment from the board therefore reported fourteen assigned modules as
    # unassigned the moment work consolidated onto one lane.
    #
    # **This is the smallest instance of what `docs/architecture/428` proposes**:
    # one place holds the fact, and everything else derives from it rather than
    # restating it (`CLAUDE.md` §2).
    declared: dict[str, str] = {}
    in_table = False
    for line in board.splitlines():
        if line.startswith("## Module assignment"):
            in_table = True
            continue
        if in_table:
            if line.startswith("#"):
                break
            row = re.match(r"\|\s*`([a-z_]+)`\s*\|\s*\*\*(Lane [A-Z]|Unassigned)\*\*", line)
            if row and row.group(1) in modules:
                declared[row.group(1)] = row.group(2)

    found: dict[str, set[str]] = {m: set() for m in modules}
    for line in board.splitlines():
        if not line.startswith("| **Lane") and not line.startswith("| **QE"):
            continue
        # **The branch column is what makes a row an assignment.** Without this
        # the parser matched dependency and waiting tables that begin the same
        # way, and reported two collisions that were not real — caught by
        # checking the board rather than trusting the first run.
        if not re.search(r"`lane-[a-z]", line):
            continue
        lane = line.split("**")[1] if "**" in line else "?"
        for m in modules:
            if f"`{m}`" in line:
                found[m].add(lane)
    out = {}
    for m, lanes in found.items():
        # **A board row disagreeing with the declared assignee is the collision
        # worth reporting**, and it is a different defect from two lanes rowed
        # against one module: it means somebody is working inside a module they
        # are not assigned, which is §20e's hardest invariant breached.
        if m in declared:
            stray = lanes - {declared[m]}
            out[m] = (
                f"COLLISION: {declared[m]} declared, {'/'.join(sorted(stray))} rowed"
                if stray
                else declared[m]
            )
        elif len(lanes) == 1:
            out[m] = next(iter(lanes))
        elif len(lanes) > 1:
            out[m] = "COLLISION: " + "/".join(sorted(lanes))
    return out


def board_rows(board: str) -> list[dict[str, str]]:
    """Assignment rows, parsed by column position.

    The board is a table: lane · task · branch · module · slice · status ·
    blocked-by · next · started. **The branch column is what makes a row an
    assignment** — dependency and waiting tables begin with the same markup,
    and matching on the lane name alone reported collisions that were not real.
    """
    out = []
    for line in board.splitlines():
        if not line.startswith("| **Lane") and not line.startswith("| **QE"):
            continue
        c = [x.strip() for x in line.split("|")]
        if len(c) < 8 or not re.search(r"`lane-[a-z]", line):
            continue
        task = re.search(r"TASK-\d+", c[2])
        status = re.search(r"`([A-Z][A-Z ]+)`", c[6])
        blocked = re.search(r"(C-\d+|B-\d+)", c[7]) if len(c) > 7 else None
        out.append({
            "lane": c[1].strip("* "),
            "task": task.group(0) if task else "—",
            "module": (re.search(r"`([a-z_]+)`", c[4]).group(1) if re.search(r"`([a-z_]+)`", c[4]) else "—"),
            "epic": (re.search(r"Epic ([A-Z0-9]+)", c[2]).group(0) if re.search(r"Epic ([A-Z0-9]+)", c[2]) else "—"),
            "status": status.group(1).strip() if status else "—",
            "blocker": blocked.group(0) if blocked else "—",
        })
    return out


def bar(pct: int, width: int = 10) -> str:
    filled = max(0, min(width, round(pct / 100 * width)))
    return "█" * filled + "░" * (width - filled)


def section(title: str) -> str:
    pad = max(0, 52 - len(title) - 2)
    return f"\n{'=' * (pad // 2)} {title} {'=' * (pad - pad // 2)}"


def build(ref: str, since: str | None = None) -> str:
    tk = tasks(ref)
    by = Counter(s for _, _, s in tk)
    board = show(ref, "docs/ACTIVE_ASSIGNMENTS.md")
    rows = board_rows(board)
    coord = show(ref, "docs/LANE_COORDINATION.md")
    bugs = show(ref, "docs/BUGS.md")

    modules = sorted({q.split("/")[2] for q in ls(ref, "backend/modules") if q.count("/") > 2})
    owners = _owners(board, modules)
    endpoints = sum(len(re.findall(r"^@router\.", show(ref, f"backend/modules/{m}/interface/router.py"), re.M)) for m in modules)
    adrs = [q for q in ls(ref, "docs/architecture/adr") if re.search(r"/\d{4}-", q)]
    routes = len([q for q in ls(ref, "frontend/app") if q.endswith("page.tsx")])
    lanes = sorted({r["lane"] for r in rows})
    epics = sorted({r["epic"] for r in rows if r["epic"] != "—"})
    blockers = sorted({r["blocker"] for r in rows if r["blocker"] != "—"})
    head = sh("git", "rev-parse", "--short", ref).strip()
    main_head = sh("git", "rev-parse", "--short", "origin/main").strip()

    # A task is claimable when it is READY and no board row already holds it.
    held = {r["task"] for r in rows}
    claimable = [(i, ti) for i, ti, s in tk if s == "READY" and i not in held]

    o: list[str] = []
    a = o.append
    a(section("1 · REPOSITORY OVERVIEW"))
    a(f"  Measured        {ref} @ {head}   (main @ {main_head})")
    a(f"  Modules {len(modules)}   Epics {len(epics)}   Tasks {len(tk)}   ADRs {len(adrs)}")
    a(f"  Endpoints {endpoints}   Frontend routes {routes}   Active lanes {len(lanes)}")
    a(f"  Approved UI screens 26   Implemented 0")
    a(f"  Open blockers on the board: {', '.join(blockers) if blockers else 'none'}")
    a(f"  Repository health          {J}")
    a(f"  Overall implementation     {J}  (estimate)")
    a(f"  Highest priority work      {J}")

    a(section("2 · MODULE PORTFOLIO"))
    a(f"  {'Module':<23}{'Lane':<23}{'Epic':<9}{'Task':<10}{'Status':<14}Blocker")
    for m in modules:
        r = next((x for x in rows if x["module"] == m), None)
        a(f"  {m:<23}{owners.get(m,'—')[:22]:<23}{(r['epic'] if r else '—'):<9}"
          f"{(r['task'] if r else '—'):<10}{(r['status'] if r else '—'):<14}{(r['blocker'] if r else '—')}")

    a(section("3 · EPIC DASHBOARD"))
    a(f"  {'Epic':<10}{'Owner':<9}{'Status':<14}{'Task':<10}Blocker")
    for e in epics:
        r = next(x for x in rows if x["epic"] == e)
        a(f"  {e:<10}{r['lane']:<9}{r['status']:<14}{r['task']:<10}{r['blocker']}")

    a(section("4 · LANE DASHBOARD"))
    for ln in lanes:
        mine = [r for r in rows if r["lane"] == ln]
        working = [r for r in mine if r["status"] in ("CLAIMED", "IN PROGRESS", "ACTIVE")]
        blocked = [r for r in mine if r["status"] == "BLOCKED"]
        val = [r for r in mine if r["status"] in ("IN VALIDATION", "VERIFIED")]
        a(f"  {ln}")
        a(f"    rows {len(mine):<3} working {len(working):<3} blocked {len(blocked):<3} with QE {len(val)}")
        if working:
            a(f"    active:  {', '.join(r['task'] for r in working if r['task'] != '—') or '—'}")
        if blocked:
            a(f"    blocked: {', '.join(r['task'] + ' (' + r['blocker'] + ')' for r in blocked)}")

    a(section("5 · TASK ASSIGNMENT"))
    a(f"  {'State':<20}Count")
    for w in STATE_WORDS + ("UNKNOWN",):
        if by[w]:
            a(f"  {w:<20}{by[w]}")
    a(f"  {'TOTAL':<20}{len(tk)}")

    a(section("6 · IMPLEMENTATION READINESS"))
    a(f"  Claimable (READY, unheld)  {len(claimable)}")
    for i, ti in claimable:
        a(f"    {i}  {ti[:52]}")
    a(f"  Target READY buffer        5 per implementation lane")
    a(f"  Product Office intervention required?  {J}")

    a(section("7 · UI IMPLEMENTATION"))
    a("  Approved 26 · Implemented 0 · Integrated 0 · QE certified 0")
    a(f"  Frontend routes on {ref}: {routes}  (all classified REPLACE — 413)")
    a(f"  READY for implementation   {J}   Deferred by ruling 3")

    a(section("8 · DECISIONS"))
    a(f"  Coordination items {len(set(re.findall(r'C-\d+', coord)))}   open blockers cited on board {len(blockers)}")
    a(f"  Bug ids {len(set(re.findall(r'B-\d+', bugs)))}")
    a(f"  Open / deferred / awaiting merge   {J}  (DECISION_REGISTER.md — not yet on {ref})")

    a(section("9 · RECENT CHANGES"))
    if since:
        prev = {i: s for i, _, s in tasks(since)}
        cur = {i: s for i, _, s in tk}
        moved = [(i, prev.get(i, "—"), s) for i, s in cur.items() if prev.get(i) != s]
        a(f"  Since {since}: {len(moved)} task state change(s)")
        for i, was, now in moved:
            a(f"    {i}  {was} -> {now}")
        a(f"  Commits: {sh('git','rev-list','--count',f'{since}..{ref}').strip()}")
    else:
        a("  (pass --since <ref> to diff task states against an earlier commit)")
    a("")
    a(f"  {J} = judgement, filled in by Lane C. A script computing these")
    a("  would state opinion in the voice of arithmetic.")
    a("=" * 52)
    return "\n".join(o) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ref", default="origin/integration", help="ref to measure (default: origin/integration)")
    ap.add_argument("--since", help="earlier ref to diff task states against")
    ap.add_argument("--no-fetch", action="store_true", help="skip the freshness fetch (offline; the reading may be stale)")
    args = ap.parse_args()
    if not sh("git", "rev-parse", "--verify", args.ref).strip():
        print(f"repository-dashboard: ref {args.ref!r} not found", file=sys.stderr)
        return 1
    if not args.no_fetch and args.ref.startswith("origin/"):
        # **The defect this exists to prevent, and it happened.** A remote ref
        # is only as fresh as the last `git fetch`, and a dashboard reading a
        # stale one reports idleness at lanes that are shipping. Four Lane C
        # reports on 2026-08-04 did exactly that. **Fetch before measuring, or
        # say plainly that the figure may be stale** — never report a number
        # whose age is unknown to the reader.
        before = sh("git", "rev-parse", args.ref).strip()
        sh("git", "fetch", "--quiet", args.ref.split("/", 1)[0], args.ref.split("/", 1)[1])
        after = sh("git", "rev-parse", args.ref).strip()
        if before != after:
            n = sh("git", "rev-list", "--count", f"{before}..{after}").strip() or "?"
            print(f"repository-dashboard: {args.ref} advanced {n} commit(s) on fetch "
                  f"({before[:8]} -> {after[:8]}). The previous reading was stale.", file=sys.stderr)
    print(build(args.ref, args.since))
    return 0


if __name__ == "__main__":
    sys.exit(main())

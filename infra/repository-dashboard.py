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
        if len(lanes) == 1:
            out[m] = next(iter(lanes))
        elif len(lanes) > 1:
            out[m] = "COLLISION: " + "/".join(sorted(lanes))
    return out


def bar(pct: int, width: int = 10) -> str:
    filled = max(0, min(width, round(pct / 100 * width)))
    return "█" * filled + "░" * (width - filled)


def section(title: str) -> str:
    pad = max(0, 52 - len(title) - 2)
    return f"\n{'=' * (pad // 2)} {title} {'=' * (pad - pad // 2)}"


def build(ref: str) -> str:
    t = tasks(ref)
    by = Counter(s for _, _, s in t)
    coord = show(ref, "docs/LANE_COORDINATION.md")
    bugs = show(ref, "docs/BUGS.md")
    board = show(ref, "docs/ACTIVE_ASSIGNMENTS.md")

    modules = sorted({p.split("/")[2] for p in ls(ref, "backend/modules") if p.count("/") > 2})
    endpoints = sum(
        len(re.findall(r"^@router\.(get|post|put|patch|delete)\(", show(ref, f"backend/modules/{m}/interface/router.py"), re.M))
        for m in modules
    )
    tables = len(set(re.findall(r'__tablename__ = "([a-z_]+)"', sh("git", "grep", "-h", "__tablename__", ref, "--", "backend"))))
    contracts = show(ref, "backend/pyproject.toml").count("[[tool.importlinter.contracts]]")
    adrs = [p for p in ls(ref, "docs/architecture/adr") if re.search(r"/\d{4}-", p)]
    routes = len([p for p in ls(ref, "frontend/app") if p.endswith("page.tsx")])
    be_tests = len([p for p in ls(ref, "backend/tests") if "/test_" in p])
    fe_tests = len([p for p in ls(ref, "frontend/tests") if p.endswith((".test.tsx", ".spec.ts", ".test.ts"))])
    head = sh("git", "rev-parse", "--short", ref).strip()

    o: list[str] = []
    a = o.append

    a(section("REPOSITORY HEALTH"))
    a(f"  Measured from {ref} @ {head}")
    a(f"  Repository Status        {J}")
    a(f"  Overall Progress         {J}")
    a(f"  Current Delivery Wave    {J}")
    a(f"  Implementation Velocity  {J}")
    a(f"  Highest Priority         {J}")
    a(f"  Largest Bottleneck       {J}")

    a(section("SYNCHRONIZATION"))
    a("  Stage                    Count   Note")
    a(f"  Prepared (Lane C)        {J:<7} on a lane branch — NOT claimable")
    a(f"  Product Owner Approved   {J:<7} authoritative, not yet actionable")
    a(f"  Merged to Integration    {len(t):<7} tasks visible on {ref}")
    a(f"  Claimable                {J:<7} READY, unclaimed, module free to that lane")
    a(f"  Claimed                  {by['CLAIMED']:<7}")
    a(f"  Implementing             {by['IN PROGRESS']:<7}")
    a(f"  QE                       {by['IN VALIDATION'] + by['VERIFIED'] + by['CERTIFIED']:<7}")
    a(f"  Main                     {by['DONE'] + by['PROMOTED']:<7}")

    a(section("TASK STATUS"))
    a(f"  Total {len(t)}")
    for w in STATE_WORDS + ("UNKNOWN",):
        if by[w]:
            a(f"    {w:<20} {by[w]}")

    owners = _owners(board, modules)

    a(section("MODULE PORTFOLIO"))
    a(f"  {'Module':<24}{'Router':>7}{'Endpoints':>11}{'Tests':>7}   Owner")
    for m in modules:
        has = "yes" if show(ref, f"backend/modules/{m}/interface/router.py") else "—"
        n = len(re.findall(r"^@router\.", show(ref, f"backend/modules/{m}/interface/router.py"), re.M))
        tests = len([p for p in ls(ref, f"backend/tests/{m}") if "/test_" in p])
        a(f"  {m:<24}{has:>7}{n:>11}{tests:>7}   {owners.get(m, '—')}")

    a(section("LANE ASSIGNMENT"))
    for lane in ("Lane A", "Lane B", "Lane C", "QE"):
        rows = [ln for ln in board.splitlines() if ln.startswith(f"| **{lane}**")]
        a(f"  {lane:<8} board rows: {len(rows)}")

    a(section("REPOSITORY METRICS"))
    a(f"  Modules {len(modules)}   ADRs {len(adrs)}   Endpoints {endpoints}   Tables {tables}")
    a(f"  Import contracts {contracts}   Frontend routes {routes}")
    a(f"  Backend test files {be_tests}   Frontend test files {fe_tests}")
    a(f"  Coordination items {len(set(re.findall(r'C-\\d+', coord)))}   Bug ids {len(set(re.findall(r'B-\\d+', bugs)))}")
    a(f"  Approved UI screens 26  (410 — the design project; not countable from git)")

    a(section("ROADMAP PROGRESS"))
    a(f"  Wave 1  {bar(0)}  {J}")
    a(f"  Wave 2  {bar(0)}  {J}")
    a(f"  Wave 3  {bar(0)}  {J}")

    a(section("PRODUCT OWNER"))
    a(f"  Requires Action          {J}")
    a(f"  Biggest Repository Risk  {J}")
    a(f"  Highest ROI Decision     {J}")
    a(f"  Highest Priority Task    {J}")
    a("")
    a(f"  {J} = judgement, filled in by Lane C. A script that computed these")
    a("  would state opinion in the voice of arithmetic.")
    a("=" * 52)
    return "\n".join(o) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ref", default="origin/integration", help="ref to measure (default: origin/integration)")
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
    print(build(args.ref))
    return 0


if __name__ == "__main__":
    sys.exit(main())

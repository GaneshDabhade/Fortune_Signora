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
import tomllib
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
    "BLOCKED", "WAITING", "VERIFIED", "CERTIFIED", "PROMOTED", "DISPOSED",
    "PREPARING", "UNDER REVIEW", "REVISION REQUESTED", "APPROVED", "RATIFIED", "READY", "DONE",
)

# **Which states mean what, for pipeline health** (D-070). Named once here so
# the report and the arithmetic cannot drift apart — the failure C-412 recorded
# was two places disagreeing about what `READY` meant for a particular lane.
IN_IMPLEMENTATION = ("CLAIMED", "IN PROGRESS")
WITH_QE = ("IN VALIDATION",)
CERTIFIED = ("VERIFIED", "CERTIFIED", "PROMOTED", "DONE")
UNDER_REVIEW = ("UNDER REVIEW",)
# **`APPROVED` is preparation, not readiness.** A task the product owner has
# approved still needs its owning lane's implementation package under D-060, so
# it belongs in the preparation column rather than in the claimable one.
PREPARING = ("PREPARING", "REVISION REQUESTED", "APPROVED")
# **`RATIFIED` was invented for TASK-900 and not added here, so the row read
# `UNKNOWN` for a day.** A task whose deliverable is an approved decision is
# complete when the decision is ratified — there is no code to promote. The
# scanner reporting `UNKNOWN` rather than failing is the quieter half of the
# defect: **an unclassifiable row still counts, it just counts as nothing.**
NOT_PIPELINE = ("DONE", "DISPOSED", "SEQUENCED", "RATIFIED")


def queues(ref: str) -> dict[str, dict]:
    """Each lane's assigned execution queue, read at `ref`.

    **Absent is not empty.** A missing queue file returns no entry at all rather
    than a lane with zero work, because those two report identically and mean
    opposite things: one is a lane with nothing to do, the other is a lane the
    Product Office has not written a queue for. The second is the finding.
    """
    out: dict[str, dict] = {}
    for path in ls(ref, "docs/coordination/queues"):
        if not path.endswith(".toml"):
            continue
        try:
            q = tomllib.loads(show(ref, path))
        except tomllib.TOMLDecodeError:
            continue
        if lane := q.get("lane"):
            out[lane] = q
    return out


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
    """Every task, with the state its Status line *declares*.

    First rather than last: a row reading ``READY -- after B-400`` is `READY`,
    and the qualifier is a note. Scanning for the last match would silently
    reclassify it.

    **Backticked first, and this is not a style preference.** Scanning the whole
    line for any state word classified `TASK-415` as `UNDER REVIEW` because its
    status *explains* the D-060 loop — *"the assignee prepares, marks it `UNDER
    REVIEW`, and Lane C reviews"*. **A mention is not a declaration**, and
    counting by substring is [B-101](../docs/BUGS.md) exactly: nine bug rows in
    two lifecycle states at once because a cell saying *"`FIXED` — `VERIFIED` is
    QE's to set"* contains both words.

    The repository writes a declared state in backticks, every time. So the
    backticked words are read first and a bare scan is the fallback — which
    keeps older rows working without letting prose vote.
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
            # **In the order the line writes them, not the order this module
            # lists them.** Ranking by STATE_WORDS made `TASK-415` `UNDER
            # REVIEW`: its line declares `APPROVED` first and mentions `UNDER
            # REVIEW` afterwards while explaining the loop, and a fixed
            # precedence let the later mention outrank the earlier declaration.
            quoted = [q.strip() for q in re.findall(r"`([A-Z][A-Z ]+)`", line)]
            for q in quoted:
                if q in STATE_WORDS:
                    state = q
                    break
            else:
                for w in STATE_WORDS:
                    if w in line:
                        state = w
                        break
        out.append((m.group(1), m.group(2).strip()[:58], state))
    return out


def _owners(board: str, modules: list[str], registry: dict) -> dict[str, str]:
    """Which lane a board row names for each module.

    Parsed from the execution board rather than assumed, because assignment is
    a rota and any hardcoded map would be wrong within a week (`CLAUDE.md`
    §20e: *a module is a permanent boundary, a lane is a temporary resource*).
    **A module named by two lanes is reported as a collision, not silently
    resolved** — that is the one-assignee-per-module invariant, and a dashboard
    that hid a breach of it would be hiding the thing worth seeing.
    """
    # **`docs/coordination/modules.toml` is the registry and is read first**
    # (product owner, 2026-08-04). Board rows answer *"who is working?"*, which
    # is a different question — a module with an assignee and no active slice
    # has no board row at all, and inferring assignment from the board reported
    # fourteen assigned modules as unassigned the moment work consolidated.
    #
    # **This function previously scraped a markdown table in the execution
    # board.** That table and the registry would have been two representations
    # of one fact, which is C-213 exactly (§2).
    declared: dict[str, str] = {
        m: e["current_owner"]
        for m, e in registry.items()
        if isinstance(e, dict) and "current_owner" in e
    }

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


def ui_wave_tasks(ref: str) -> frozenset[str]:
    """Backlog rows that render approved UI, **read from the rows themselves.**

    A row declares its screen in an `| **Approved screen** |` field. This reads
    that field; it does not guess from a title and it does not hold a list.

    **This replaced a hardcoded `frozenset({"TASK-417"})` on 2026-08-06**, and
    the comment above it was half right: it argued that *"a heuristic over
    titles would silently miscount the day somebody words one differently — and
    this figure is the product's headline gap, so a quiet miscount is the
    expensive kind."* **Correct about titles, and it chose the wrong
    alternative.** A declared field is neither a heuristic nor a list: the row
    states what it renders, and a row that does not state it is not counted.

    ⚠️ **The cost of the list was exactly the miscount it was written to
    prevent.** By 2026-08-06 the backlog held **nine** screen rows and this set
    named **one** — and not even one of the nine, because `TASK-417`, the first
    screen ever built against the approved UI, carried no field naming its
    screen. **The instrument measuring the product's headline gap could see
    none of the screens.**

    **The failure mode inverts, and that is the point**: a list goes stale
    silently as rows are *added*; a field goes stale visibly, because a row
    that forgets it is absent from a figure somebody reads every cycle.
    """
    out: set[str] = set()
    for block in re.split(r"(?=^### TASK-\d+)", show(ref, "docs/BACKLOG.md"), flags=re.M):
        head = re.match(r"^### (TASK-\d+)", block)
        if head and re.search(r"^\| \*\*Approved screen\*\* \|", block, re.M):
            out.add(head.group(1))
    return frozenset(out)


def _ui_implemented(tk: list[tuple[str, str, str]], ref: str) -> int:
    """Wave rows a lane has finished — past `CLAIMED`, whatever comes next."""
    done = ("IN VALIDATION", "VERIFIED", "CERTIFIED", "PROMOTED", "DONE")
    wave = ui_wave_tasks(ref)
    return sum(1 for i, _, s in tk if i in wave and s in done)


def _ui_integrated() -> int:
    """Wave rows a lane has finished **and `main` carries.**

    **Measured at `origin/main`, not read from a state word.** The first version
    counted rows reading `VERIFIED` or `PROMOTED`, and reported `Integrated 0`
    while wave 1 sat on `main` — because QE reconciles a row at Closeout and the
    code arrives before the word does. **The label said *integrated* and the
    number measured *reconciled*.**

    This is the same shape as the hardcoded `Implemented 0` it replaced, one
    level down: a figure that answers a different question than its name.
    """
    started = ("CLAIMED", "IN PROGRESS", "IN VALIDATION", "CHANGES REQUESTED",
               "VERIFIED", "CERTIFIED", "PROMOTED", "DONE")
    wave = ui_wave_tasks("origin/main")
    return sum(1 for i, _, s in tasks("origin/main")
               if i in wave and s in started)


#: The approved screen set, and the only hand-written number in this view.
#: **16 business + 10 platform foundation = 26**, from
#: `418-platform-foundation-assessment.md` §1. It is a *count of designs the
#: product owner approved* — nothing in the repository derives it, so deriving
#: it would be inventing it. **Everything below is measured against it.**
APPROVED_SCREENS = 26


def screen_coverage(ref: str) -> list[str]:
    """**Which approved screens can be built, and what stops the rest** (D-108).

    Answers the seven questions the directive names, from two sources joined at
    `ref`: the screen rows in `BACKLOG.md` and the ⛔ blockers the Domain
    Discovery Register records per screen.

    ⚡ **The category that matters is the last one** — a screen with **no ⛔
    blocker recorded** and **no row.** Nothing the Register calls blocking
    prevents it; **the only reason it is not moving may be that Product Office
    has not written the row.** Every other category names somebody else's
    dependency. **This one can name this office**, which is why it is computed
    rather than described.

    ⚠️ **It counts ⛔ and nothing else, and the label says so.** The Register
    also records constraints with ⚠️ — *"no search index exists: `meilisearch`
    `tsvector` `trigram` all 0"* for Global Search, and five absent concerns for
    App Shell — **and those are real even though they are not ⛔.** Counting
    them here would need a judgement about which ⚠️ blocks, and a script making
    that call would be stating opinion in the voice of arithmetic. **So the
    figure is deliberately named for the marker it counts**: a screen appearing
    here is a *candidate* for decomposition, not a verdict that it is ready.
    **The alternative — calling it "not blocked" — is B-101's shape: a proxy
    labelled as the thing it stands for.**
    """
    rows = {i: s for i, _, s in tasks(ref) if i in ui_wave_tasks(ref)}
    shipped = ("VERIFIED", "CERTIFIED", "PROMOTED", "DONE")
    flight = ("CLAIMED", "IN PROGRESS", "IN VALIDATION", "CHANGES REQUESTED")

    register = show(ref, "docs/DOMAIN_DISCOVERY_REGISTER.md").split("# Part B")[0]
    blocked: dict[str, list[str]] = {}
    for line in register.splitlines():
        m = re.match(r"^\| \d+ \| \*\*(.+?)\*\*.*?\|(.*)\|$", line)
        if not m:
            continue
        blocked[m.group(1).strip()] = [
            b.strip() for b in re.findall(r"⛔ \*\*([^*]+)\*\*", m.group(2))
        ]

    counts = Counter(
        "implemented" if s in shipped else "in flight" if s in flight
        else "ready" if s == "READY" else "other"
        for s in rows.values()
    )
    # **§20c names the frozen frontend foundation**, and two approved screens
    # *are* it: the Design System and the Application Shell. **A row for either
    # modifies the foundation, which is 🔴 — product owner plus ADR — so it is
    # not Product Office's to write.** They are separated here because
    # "awaiting decomposition" would name the wrong owner: the first list is
    # this office's backlog, the second is the product owner's.
    _FROZEN_FOUNDATION = ("App Shell", "Design System")
    candidates = sorted(s for s, b in blocked.items() if not b)
    frozen = [s for s in candidates if s.startswith(_FROZEN_FOUNDATION)]
    undecomposed = [s for s in candidates if s not in frozen]

    out = [section("SCREEN COVERAGE — product completion (D-108)")]
    out.append(f"  Approved screens           {APPROVED_SCREENS}")
    out.append(f"  With a row at {ref:<14} {len(rows)}")
    out.append(f"    implemented              {counts['implemented']}")
    out.append(f"    in flight                {counts['in flight']}")
    out.append(f"    implementation-ready     {counts['ready']}")
    out.append(f"  Audited, no row, blocked   {sum(1 for b in blocked.values() if b)}")
    out.append(
        f"  ⚡ No ⛔ recorded and no row   {len(undecomposed)}"
        f"   {', '.join(undecomposed) if undecomposed else '—'}"
    )
    out.append("     ^ decomposition candidates. ⚠️ counts ⛔ only — a screen")
    out.append("       constrained by a ⚠️ note appears here and is not ready.")
    out.append(
        f"  🔴 Frozen foundation (§20c)  {len(frozen)}"
        f"   {', '.join(frozen) if frozen else '—'}"
    )
    out.append("     ^ awaiting a RULING, not decomposition — a row here")
    out.append("       modifies the frozen frontend foundation")

    # **D-109: the view must answer *what next*, not only *how much*.**
    # **Ranked by lifecycle distance, because that is the only ordering this
    # script can compute honestly.** A screen already `READY` is nearer
    # shipping than one with no row, and one with no row is nearer than one
    # with a ⛔. ⛔ **Customer value is judgement and is emitted as `J`** — a
    # script ranking screens by worth would be stating opinion in the voice of
    # arithmetic, which this file's docstring forbids.
    out.append("")
    out.append("  NEXT WORK — by lifecycle distance, not by value")
    ready = sorted(i for i, s in rows.items() if s == "READY")
    out.append(f"    claimable now            {', '.join(ready) if ready else '—'}")
    out.append(f"    awaiting decomposition   {', '.join(undecomposed) if undecomposed else '—'}")
    out.append(f"    highest customer value   {J}")
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
    # **The registry, loaded once and passed down.** Read failures are reported
    # where the table is printed, never swallowed into an empty dict that would
    # read as "nothing is assigned".
    try:
        registry = tomllib.loads(show(ref, "docs/coordination/modules.toml"))
    except (tomllib.TOMLDecodeError, ValueError):
        registry = {}
    owners = _owners(board, modules, registry)
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
    a(f"  Approved UI screens {APPROVED_SCREENS}   Implemented {_ui_implemented(tk, ref)}   (wave rows in BACKLOG.md)")
    a(f"  Open blockers on the board: {', '.join(blockers) if blockers else 'none'}")
    a(f"  Repository health          {J}")
    a(f"  Overall implementation     {J}  (estimate)")
    a(f"  Highest priority work      {J}")
    o.extend(screen_coverage(ref))

    # **Every report carries this** (D-070, product owner 2026-08-05):
    # *"Product Office should always be thinking several steps ahead."* The
    # thirteen lines below are the ones asked for, computed rather than stated,
    # so a shortfall is arithmetic instead of an opinion about how busy we feel.
    a(section("1a · PIPELINE HEALTH"))
    qs = queues(ref)
    live = [(i, ti, s) for i, ti, s in tk if s not in NOT_PIPELINE]
    po_wait = [i for i, _, s in tk if s == "BLOCKED"]
    a(f"  Total repository tasks                {len(tk)}")
    a(f"  In implementation                     {sum(by[s] for s in IN_IMPLEMENTATION)}")
    a(f"  Under Product Office review           {sum(by[s] for s in UNDER_REVIEW)}")
    a(f"  Preparing (lane-authored)             {sum(by[s] for s in PREPARING)}")
    a(f"  Waiting for QE                        {sum(by[s] for s in WITH_QE)}")
    a(f"  Certified / promoted / done           {sum(by[s] for s in CERTIFIED)}")
    a(f"  Blocked                               {by['BLOCKED']}")
    a(f"  Not in the pipeline (done/disposed)   {sum(by[s] for s in NOT_PIPELINE)}")
    a("  Tasks by lifecycle state:")
    for s, n in by.most_common():
        a(f"    {s:<20} {n}")

    a("")
    a("  Per lane — buffer against the five-slice target:")
    a(f"    {'Lane':<8} {'assigned':>8} {'eligible':>8} {'blocked':>8} {'with QE':>8}  buffer")
    for lane in sorted(qs) or []:
        q = qs[lane]
        seq = [q.get("current")] + [q.get("next")] + list(q.get("future") or [])
        seq = [t for t in seq if t]
        blocked = q.get("blocked") or []
        val = q.get("in_validation") or []
        # **The declared count is checked, never trusted.** `lane-a.toml`
        # declared 3 beside a sequence of 4 for one commit — a judgement about
        # one entry recorded as a number, next to the list it disagreed with.
        # **That is C-412's defect in this office's own file**, so the
        # disagreement is reported rather than resolved silently in either
        # direction: the field may be right and the list stale, or the reverse.
        declared = q.get("eligible_count")
        elig = int(declared) if declared is not None else len(seq)
        target = int(q.get("depth_target", 5))
        mark = "OK" if elig >= target else f"SHORT by {target - elig}"
        a(f"    {lane:<8} {len(seq):>8} {elig:>8} {len(blocked):>8} {len(val):>8}  {elig}/{target}  {mark}")
        if declared is not None and int(declared) != len(seq):
            a(f"      DRIFT — declares {declared} eligible, sequences {len(seq)}: "
              f"{', '.join(seq)}")
    for lane in ("Lane A", "Lane B"):
        if lane not in qs:
            a(f"    {lane:<8} NO QUEUE FILE — absence is a Product Office finding, not an empty queue")

    # **Prepared-but-unassigned should be zero and is worth computing anyway.**
    # A READY task in nobody's queue is exactly the C-412 defect: a row that
    # advertises work while no lane can see that it is theirs.
    queued = {t for q in qs.values()
              for t in ([q.get("current"), q.get("next")] + list(q.get("future") or [])
                        + [b.get("task") for b in (q.get("blocked") or [])]) if t}
    orphan = [i for i, _, s in tk if s == "READY" and i not in queued]
    a("")
    a(f"  Eligible for preparation              {len(claimable)}")
    a(f"  Prepared but not yet assigned         {len(orphan)}   (target 0)")
    for i in orphan:
        a(f"    ORPHAN {i} — READY and in no lane queue")
    a(f"  Awaiting a product owner decision     {len(po_wait)}   {', '.join(po_wait) or '—'}")
    a(f"  Estimated remaining prepared work     {J}  per lane, in slices — no denominator exists")

    a(section("2 · REPOSITORY EXECUTION DASHBOARD"))
    # **Ownership is read from `docs/coordination/modules.toml`, the registry**
    # (product owner, 2026-08-04 — 428 step 1). It was previously scraped out of
    # 430's markdown table, and before that inferred from board rows: three
    # representations of one fact, which is how C-213 happened.
    #
    # **Only what cannot be derived is read from the registry.** Epic, active
    # slice, execution status, QE status and blocker still come from the
    # execution board, because they change per slice and storing them twice
    # would recreate the defect this closes (§2).
    #
    # **A module absent from the registry prints `?`, never a default** —
    # absence is reported rather than read as agreement (ADR-0032's
    # `missing_gates`, and `36-empty-array-checks.md`).
    reg = {k: v for k, v in registry.items() if k != "meta"}
    meta = registry.get("meta", {})
    if not registry:
        a("  ⚠ registry unreadable or absent — every row below will report `?`.")
    a(f"  {'Module':<23}{'Owner':<8}{'Future':<9}{'Stage':<10}{'Impl':<6}{'Epic':<8}"
      f"{'Slice':<10}{'QE':<10}{'Carries':<9}Next milestone")
    for m in modules + ["product_surface"]:
        e = reg.get(m, {})
        r = next((x for x in rows if x["module"] == m), None)
        st = (r["status"] if r else "—")
        qe = st if st in ("IN VALIDATION", "VERIFIED", "CHANGES REQUESTED") else "—"
        # **`carries` is not `blocked`, and this column claimed it was.**
        # The registry field means *this item travels with the module* (D-057)
        # — C-215 travels with `timeline` and is buildable work; C-214 says in
        # its own words *"Implementation impact. Blocks nothing"*. Printing
        # both under a heading reading `Blocked` reported two modules as
        # obstructed when neither was, and a false blocker is worse than none:
        # it is a reason not to look.
        blocked = ", ".join(e.get("carries", [])) or (r["blocker"] if r else "—")
        a(f"  {m:<23}{e.get('current_owner','?')[:7]:<8}{e.get('future_owner','?')[:8]:<9}"
          f"{e.get('transition','?')[:9]:<10}{str(e.get('implementation','?'))+'%':<6}"
          f"{(r['epic'] if r else '—')[:7]:<8}{(r['task'] if r else '—'):<10}{qe[:9]:<10}"
          f"{blocked[:8]:<9}{e.get('next_milestone','—')[:34]}")
    missing = [m for m in modules if m not in reg]
    if missing:
        a(f"  ⚠ absent from the registry: {', '.join(missing)}")
    a(f"  Review owner: {meta.get('default_review_owner','?')}."
      f"  Ownership precedence: {' > '.join(meta.get('precedence', ['?']))}.")
    a("  Impl is a Lane C estimate, banded to 5 — a module has no denominator in")
    a("  the repository. PROJECT_STATUS.md remains authoritative for measured progress.")
    a("  Preparing/Under review are 0 repository-wide until a module's")
    a("  pre-transition backlog empties (D-060) — see §9.")

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
    # **`Implemented 0` was hardcoded and became false the hour wave 1 landed.**
    # A constant in a dashboard is a stored fact with no expiry — the defect
    # C-213 and C-412 both were, committed here by the office that closed them.
    # **Counted from the wave rows instead**, so the day a wave completes this
    # line changes without anybody remembering to change it.
    a(f"  Approved {APPROVED_SCREENS} · Implemented {_ui_implemented(tk, ref)} · "
      f"Integrated {_ui_integrated()} · QE certified {J}")
    a("  Implemented counts a UI wave row past CLAIMED at the measured ref.")
    a("  Integrated counts it present on `origin/main` — **the code arrives**")
    a("  **before the reconciled word does**, and the label must mean the code.")
    a("  26 is from 410 and is the one figure still stated: an approved screen")
    a("  is a design fact, and nothing in the repository counts it.")
    a(f"  Frontend routes on {ref}: {routes}  (all classified REPLACE — 413)")
    a(f"  READY for implementation   {J}   Deferred by ruling 3")

    a(section("8 · DECISIONS"))
    a(f"  Coordination items {len(set(re.findall(r'C-\d+', coord)))}   open blockers cited on board {len(blockers)}")
    a(f"  Bug ids {len(set(re.findall(r'B-\d+', bugs)))}")
    a(f"  Open / deferred / awaiting merge   {J}  (DECISION_REGISTER.md — not yet on {ref})")

    # **The two queues Distributed Product Development runs on** (`CLAUDE.md`
    # §20e). They are computed rather than reported by a lane because each one
    # measures the office that would be reporting it: **a growing review queue
    # is Product Office becoming the bottleneck at approval instead of at
    # authorship**, and a growing synchronization queue is the failure the
    # model was created to end. **Neither is a lane's claim about itself.**
    a(section("9 · REVIEW QUEUE"))
    prep = [(i, ti, s) for i, ti, s in tk if s in ("PREPARING", "UNDER REVIEW", "REVISION REQUESTED")]
    if prep:
        for i, ti, s in prep:
            a(f"  {s:<20} {i:<10} {ti[:44]}")
        a(f"  awaiting Product Office review: {sum(1 for _,_,s in prep if s == 'UNDER REVIEW')}")
    else:
        a("  empty — no package is preparing, under review or awaiting revision.")
        a("  Correct while every module is still on the pre-transition backlog:")
        a("  the model switches per module, as each module's queue empties.")

    a(section("10 · SYNCHRONIZATION QUEUE"))
    # Approved and not yet claimable is the exact gap §20e names: *prepared work
    # that has not reached `integration` does not exist for planning purposes*.
    # **Corrected 2026-08-05: a commit count is not evidence of content.**
    # This section reported `lane-c-product-office  59 ahead` every run, and Lane
    # B read it at C-329 as "the Product Office document set has never reached
    # integration" — a reasonable inference from the only number on offer, and
    # wrong. The branch is 59 ahead and 243 behind, and **not one file on it is
    # newer than integration's copy.** It holds nothing; it is abandoned, which
    # is a different finding with a different owner.
    #
    # **So `holds` is computed per file rather than per commit**: a file counts
    # only when the branch's newest commit touching it is not reachable from
    # `ref` *and* `ref` has not touched it since. Ahead-ness measures divergence;
    # this measures whether anything would be lost by deleting the branch.
    for br in [b for b in sh("git", "for-each-ref", "--format=%(refname:short)",
                             "refs/remotes/origin").split() if "lane-" in b]:
        ahead = sh("git", "rev-list", "--count", f"{ref}..{br}").strip() or "0"
        if ahead == "0":
            continue
        behind = sh("git", "rev-list", "--count", f"{br}..{ref}").strip() or "0"
        changed = sh("git", "diff", "--name-only", f"{ref}...{br}").split()
        exe = [p for p in changed if not p.startswith("docs/") and not p.endswith(".md")]
        holds = [p for p in changed
                 if sh("git", "rev-list", "--count", f"{ref}..{br}", "--", p).strip() not in ("0", "")
                 and sh("git", "rev-list", "--count", f"{br}..{ref}", "--", p).strip() in ("0", "")]
        a(f"  {br:<40} {ahead:>3} ahead  {behind:>3} behind   "
          f"{len(holds)} file(s) newer here   {len(exe)} executable")
        if not holds:
            a("      holds nothing this ref lacks — ABANDONED, not synchronization backlog")
    a(f"  Measured against {ref}. **A branch ahead of it is not capacity** — it is")
    a("  planning until QE promotes it (CLAUDE.md §20e, the five decision states).")
    a("  **And a branch ahead of it does not necessarily hold anything.** Ahead-ness")
    a("  is divergence; the file count is what would be lost by deleting it.")

    a(section("11 · BOTTLENECK DASHBOARD"))
    po = len([1 for m in re.findall(r"owner[^|]*product owner", coord, re.I)])
    a(f"  governance        {len(blockers)} blocker(s) cited on the board: {', '.join(blockers) or '—'}")
    a(f"                    ~{po} coordination item(s) name the product owner as owner")
    a(f"  synchronization   {sum(1 for b in sh('git','for-each-ref','--format=%(refname:short)','refs/remotes/origin').split() if 'lane-' in b and sh('git','rev-list','--count',f'{ref}..{b}').strip() not in ('0',''))} lane branch(es) ahead of {ref}")
    a(f"  ownership         {sum(1 for v in owners.values() if v.startswith('COLLISION'))} collision(s)"
      f"   {sum(1 for m in modules if m not in owners)} module(s) with no declared assignee")
    a(f"  architecture      {J}  (a 🔴 change with no ADR is one; a script cannot tell)")
    a(f"  external          {J}  (a vendor, a credential, a dataset nobody holds)")

    a(section("12 · RECENT CHANGES"))
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

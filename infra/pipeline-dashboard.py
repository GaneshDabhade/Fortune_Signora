#!/usr/bin/env python3
"""**The Execution Health Dashboard** — [D-204](../docs/DECISION_REGISTER.md) §2.

**Generated, never hand-written.** ⛔ A table a human retypes goes stale between
two cycles — the defect this repository paid for in `eligible_count` five times.

    python3 infra/pipeline-dashboard.py            # the table
    python3 infra/pipeline-dashboard.py --toml     # the same counts, for embedding

## ⚡ One metric leads, and everything else supports it

> 📁 [D-204](../docs/DECISION_REGISTER.md) §2: *"How many implementation tasks
> can Lane A begin immediately without waiting for Product Office?"*

⛔ **This dashboard used to lead with *prepared* rows, which is a Product Office
HOLDING.** ⚡ **A prepared row a lane cannot see is worth nothing** — leading with
it measured this office's output where the question is the repository's
throughput.

**`IMMEDIATELY EXECUTABLE` is the top line, on the strictest available reading:**
a row counts only when it is **in the lane's own backlog file AND reads `READY`
on `origin/integration`** — the ref a lane actually builds from ([§20e](../CLAUDE.md):
*executable work comes from `integration` and nowhere else*). ⛔ **A row ready
only on `lane-c-sync` is not executable**; it is synchronization debt, it is
reported on its own line, and **its owner is QE rather than this office** — which
is why the two shortfalls never print the same sentence.

**`prepared`, `partial` and the workflow counts survive as supporting metrics**
and are still emitted by `--toml`. ⛔ **They no longer lead.**
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKLOG = ROOT / "docs" / "BACKLOG.md"
WORKFLOWS = ROOT / "docs" / "coordination" / "workflows.toml"

#: Rows that have left the lane. **`IN VALIDATION` is included deliberately** —
#: §20e: *"the lane's responsibility for this task has ended."*
DEPARTED = frozenset({"PROMOTED", "DONE", "DISPOSED", "VERIFIED", "CERTIFIED", "IN VALIDATION"})
REQUIRED = ("Definition of Done", "Testing metadata", "Change Budget")
PREPARED_CELLS = 17
PREPARED_FLOOR = 20


def _rows() -> list[tuple[str, str, int, str]]:
    """Every backlog row as (id, state, cell-count, body). **Parsed by line.**

    ⛔ **Not by a regex over the whole file.** That method has now produced ten
    wrong answers in this repository — a `READY` matched inside prose, a
    predecessor matched inside a *(Was:* clause, a title capped at 50 characters,
    a `[[blocked]]` matched inside a comment. **[B-411](../docs/BUGS.md) and
    [B-412](../docs/BUGS.md) are the two that cost content.**
    """
    lines = BACKLOG.read_text().split("\n")
    heads = [(i, l) for i, l in enumerate(lines) if l.startswith("### TASK-")]
    out = []
    for n, (i, head) in enumerate(heads):
        end = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
        body = lines[i:end]
        status = next((x for x in body if x.startswith("| **Status**")), "")
        state = re.search(r"`([A-Z ]+)`", status.split("*(Was:")[0])
        out.append((
            head.split(" · ")[0].replace("### ", ""),
            state.group(1) if state else "?",
            len([x for x in body if x.startswith("|")]),
            "\n".join(body),
        ))
    return out


def counts() -> dict[str, int]:
    rows = _rows()
    live = [r for r in rows if r[1] not in DEPARTED]
    prepared = [r for r in live if r[2] >= PREPARED_CELLS and all(k in r[3] for k in REQUIRED)]
    partial = [r for r in live if r not in prepared and r[2] >= 10]
    flows = tomllib.loads(WORKFLOWS.read_text())["workflow"]
    undecomposed = [k for k, v in flows.items() if not v.get("tasks")]
    decomposed = len(flows) - len(undecomposed)

    # ⛔ **A second `claimable`, computed from `current`/`next`/`future`, stood
    # here until D-203 §2.** D-199 deleted those fields from the queue, so it
    # evaluated to zero on every run — and it was **emitted in the counts and
    # displayed nowhere**, which is why nothing caught it. ⚡ **Dead arithmetic in
    # a dashboard is worse than a wrong number: it is a number waiting to be
    # displayed by somebody who assumes it was maintained.**
    queue_a = tomllib.loads((ROOT / "docs" / "coordination" / "queues" / "lane-a.toml").read_text())
    backlog = [str(x) for x in (queue_a.get("backlog") or [])]
    import subprocess as _sp
    integ = _sp.run(["git", "show", "origin/integration:docs/BACKLOG.md"],
                    cwd=ROOT, capture_output=True, text=True).stdout
    on_int = set()
    for blk in re.split(r"\n(?=### TASK-\d+)", integ):
        h = re.match(r"### (TASK-\d+)", blk)
        if not h:
            continue
        cell = re.search(r"\|\s*\**\s*Status\s*\**\s*\|([^|]*)\|", blk)
        v = re.sub(r"\s+", " ", (cell.group(1) if cell else "")).upper().strip()
        if re.match(r"[^A-Z]*\**`?READY", v):
            on_int.add(h.group(1))

    # ── The six things D-204 §2 asks to be reported ──────────────────────────
    blocked_rows = queue_a.get("blocked") or []
    #: **An implementation blocker is another ROW.** Its input does not exist
    #: yet, and the lane that owns the predecessor can clear it without anybody
    #: ruling on anything.
    impl_blocked = [b for b in blocked_rows
                    if any(str(x).startswith("TASK-") for x in (b.get("blocker") or []))]
    #: **Everything else in `blocked` waits on a decision, a capability or a
    #: credential** — the class no amount of preparation clears.
    arch_blocked = [b for b in blocked_rows if b not in impl_blocked]

    # ⛔ **THE OPERATIVE STATE IS THE FIRST TOKEN IN THE CELL — never a substring.**
    #
    # A first version of this asked `"OPEN" in cell` and reported **70 open items
    # where there are 40**, because the register's convention is to record a
    # ruling and recount what it replaced: *"`CLOSED` — was `OPEN` until
    # 2026-08-07"* contains both words. ⚡ **That is [B-101](../docs/BUGS.md)
    # exactly**, and it was written into this file forty minutes after
    # [B-413](../docs/BUGS.md) fixed the same class in `registers.py` — the rule
    # that file already states: **`min(find(...))`, not `in`.**
    states = ("OPEN", "RULED", "CLOSED", "ANSWERED", "WITHDRAWN", "SUPERSEDED")
    coord = (ROOT / "docs" / "LANE_COORDINATION.md").read_text()
    owner_open = qe_open = 0
    for blk in re.split(r"\n(?=#{2,4} C-\d+)", coord):
        if not re.match(r"#{2,4} C-\d+", blk):
            continue
        cell = re.search(r"^\|\s*\*\*(?:Status|State)\*\*\s*\|([^|]*)\|", blk, re.M)
        if not cell:
            continue
        text = cell.group(1).upper()
        found = [(text.find(s), s) for s in states if s in text]
        if not found or min(found)[1] != "OPEN":
            continue
        own = re.search(r"^\|\s*\*\*Owner\*\*\s*\|([^|]*)\|", blk, re.M)
        who = (own.group(1) if own else "").lower()
        if "product owner" in who:
            owner_open += 1
        elif "qe" in who:
            qe_open += 1

    # ── D-207 §3 — completeness and correctness are different questions ──────
    #
    # ⛔ **Design COMPLETENESS asks *can it be built without inventing behaviour?*
    # Design CORRECTNESS asks *is the behaviour itself logically consistent?***
    # ⚡ **They were reported as one number and they have different owners and
    # different remedies**: a completeness gap is closed by writing a document, a
    # correctness gap only by the Design Authority confirming or amending one.
    clarifications = 0
    for blk in re.split(r"\n(?=#{2,4} C-\d+)", coord):
        if not re.match(r"#{2,4} C-\d+", blk):
            continue
        kl = re.search(r"^\|\s*\*\*Class\*\*\s*\|([^|]*)\|", blk, re.M)
        if not kl or "DESIGN CLARIFICATION" not in kl.group(1).upper():
            continue
        st = re.search(r"^\|\s*\*\*Status\*\*\s*\|([^|]*)\|", blk, re.M)
        c = (st.group(1) if st else "").upper()
        f = [(c.find(s), s) for s in states if s in c]
        if f and min(f)[1] == "OPEN":
            clarifications += 1

    #: **QE's queue, and it is the largest single distortion in the repository.**
    #: A row at `IN VALIDATION` is finished work the lane cannot touch and the
    #: board still counts.
    in_validation = len([r for r in rows if r[1] == "IN VALIDATION"])
    unsynced = _sp.run(["git", "rev-list", "--count", "origin/integration..HEAD"],
                       cwd=ROOT, capture_output=True, text=True).stdout.strip() or "0"

    executable = [t for t in backlog if t in on_int]
    return {
        # 🔴 **THE metric — D-204 §2.** ⛔ Not *"how many prepared tasks Product
        # Office owns"*, which measures this office, but **what Lane A can start
        # right now without waiting for anybody.** ⚡ **Strictest available
        # reading: in the lane's own backlog AND `READY` on `origin/integration`**,
        # the only ref §20e permits executable work to come from.
        "immediately_executable": len(executable),
        "lane_backlog": len(backlog),
        "synchronization_debt": len(backlog) - len(executable),
        "implementation_blockers": len(impl_blocked),
        "architectural_blockers": len(arch_blocked),
        "product_owner_decisions": owner_open,
        "design_clarifications": clarifications,
        "qe_decisions": qe_open,
        "awaiting_qe": in_validation,
        "planning_unsynced": int(unsynced),
        "prepared": len(prepared),
        "partial": len(partial),
        "undecomposed_workflows": len(undecomposed),
        "decomposed_workflows": decomposed,
        "total_workflows": len(flows),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toml", action="store_true", help="emit counts for embedding")
    args = parser.parse_args()
    c = counts()

    if args.toml:
        print("[pipeline]")
        for k, v in c.items():
            print(f"{k:24} = {v}")
        return 0

    def mark(actual: int, target: int, exact: bool = False) -> str:
        ok = actual == target if exact else actual >= target
        return "✅" if ok else "🔴"

    rows = [
        ("IMMEDIATELY EXECUTABLE", c["immediately_executable"], f"≥{PREPARED_FLOOR}",
         mark(c["immediately_executable"], PREPARED_FLOOR)),
        ("  in the lane's backlog", c["lane_backlog"], f"≥{PREPARED_FLOOR}",
         mark(c["lane_backlog"], PREPARED_FLOOR)),
        ("  not yet on integration", c["synchronization_debt"], "0",
         mark(0, c["synchronization_debt"])),
        (None, None, None, None),
        ("Implementation blockers", c["implementation_blockers"], "a lane clears these", "  "),
        ("Architectural blockers", c["architectural_blockers"], "Product Office's", "  "),
        ("Product Owner decisions", c["product_owner_decisions"], "open", "  "),
        ("Design Clarifications", c["design_clarifications"], "Design Authority's", "  "),
        ("QE decisions", c["qe_decisions"], "open", "  "),
        (None, None, None, None),
        ("Awaiting QE — IN VALIDATION", c["awaiting_qe"], "QE's queue", "  "),
        ("Planning not on integration", c["planning_unsynced"], "0",
         mark(0, c["planning_unsynced"])),
        (None, None, None, None),
        ("Workflows decomposed", c["decomposed_workflows"], f"{c['total_workflows']}",
         mark(c["decomposed_workflows"], c["total_workflows"])),
    ]
    width = max(len(r[0]) for r in rows if r[0])
    print("  EXECUTION HEALTH — D-204 §2")
    print(f"  {'Measure'.ljust(width)}  {'Count':>5}  {'Target':<20}")
    print(f"  {'-' * width}  {'-' * 5}  {'-' * 20}")
    for label, count, target, flag in rows:
        if label is None:
            print()
            continue
        print(f"  {label.ljust(width)}  {count:>5}  {target:<20} {flag}")

    # ⛔ **The two shortfalls have DIFFERENT owners and must never print the same
    # sentence.** A backlog too shallow is this office's to fix by decomposing.
    # A backlog the lane cannot see is a synchronization lag — ⚡ **and telling
    # Product Office to prepare more would be exactly the wrong instruction.**
    if c["lane_backlog"] < PREPARED_FLOOR:
        print(f"\n  🔴 Backlog is {PREPARED_FLOOR - c['lane_backlog']} short — "
              f"**PRODUCT OFFICE's.** Close it by decomposing future workflows, "
              f"never by relabelling (D-188 §7).")
    if c["synchronization_debt"]:
        print(f"\n  🔴 {c['synchronization_debt']} prepared row(s) are NOT on "
              f"`origin/integration` — **QE's.** Preparing more would not move "
              f"this number; the lane cannot see what it already has.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

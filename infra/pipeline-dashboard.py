#!/usr/bin/env python3
"""The Prepared Pipeline Dashboard — [D-188](../docs/DECISION_REGISTER.md), §recommendation.

**Generated, never hand-written.** ⛔ The product owner asked for this in *every*
status update, and a table a human retypes each cycle is a table that goes stale
between two of them — which is the defect this repository has now paid for in
`eligible_count` five times.

    python3 infra/pipeline-dashboard.py            # the table
    python3 infra/pipeline-dashboard.py --toml     # the same counts, for embedding

⚡ **"Prepared" is mechanical and matches `state-check.py` exactly**: 17+ cells
carrying a Definition of Done, testing metadata and a Change Budget. ⛔ **A title
cannot satisfy it and neither can a state change** — [D-187](../docs/DECISION_REGISTER.md) §6
and [D-188](../docs/DECISION_REGISTER.md) §7, made unrepresentable rather than promised.
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

    return {
        # ⚡ **D-199 §6 — the metric changed.** ⛔ Not *"how many prepared tasks
        # Product Office owns"* but *"how much uninterrupted implementation work
        # already exists inside Lane A's backlog"*. **Those are different
        # numbers, and only the second one is the product owner's question.**
        "lane_backlog": len(backlog),
        "lane_backlog_live": len([t for t in backlog if t in on_int]),
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
        ("Lane A's backlog — claimable", c["lane_backlog"], f"≥{PREPARED_FLOOR}", mark(c["lane_backlog"], PREPARED_FLOOR)),
        ("  …of those, on integration", c["lane_backlog_live"], "all of them", mark(c["lane_backlog_live"], c["lane_backlog"])),
        ("Partially prepared tasks", c["partial"], "informational", "  "),
        ("Workflows not yet decomposed", c["undecomposed_workflows"], "0 eventually", mark(0, c["undecomposed_workflows"])),
        ("Workflows fully decomposed", c["decomposed_workflows"], f"{c['total_workflows']}", mark(c["decomposed_workflows"], c["total_workflows"])),
    ]
    width = max(len(r[0]) for r in rows)
    print("  LANE A'S IMPLEMENTATION BACKLOG — D-199")
    print(f"  {'Status'.ljust(width)}  {'Count':>5}  {'Target':<14} ")
    print(f"  {'-' * width}  {'-' * 5}  {'-' * 14}")
    for label, count, target, flag in rows:
        print(f"  {label.ljust(width)}  {count:>5}  {target:<14} {flag}")

    if c["prepared"] < PREPARED_FLOOR:
        print(f"\n  🔴 {PREPARED_FLOOR - c['prepared']} short. **Close it by decomposing "
              f"future workflows, never by relabelling** (D-188 §7).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

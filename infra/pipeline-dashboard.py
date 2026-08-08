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
    # ⚡ The one-claimable invariant is per IMPLEMENTATION lane. Lane C's own
    # Platform Foundation rows (D-022) are not implementation tasks for Lane A,
    # and counting them reported two where the invariant was satisfied.
    queue = tomllib.loads((ROOT / "docs" / "coordination" / "queues" / "lane-a.toml").read_text())
    offered = {str(t) for t in [queue.get("current"), queue.get("next")] if t}
    offered |= {str(t) for t in (queue.get("future") or [])}
    claimable = [r for r in rows if r[1] == "READY" and r[0] in offered]

    flows = tomllib.loads(WORKFLOWS.read_text())["workflow"]
    undecomposed = [k for k, v in flows.items() if not v.get("tasks")]
    decomposed = len(flows) - len(undecomposed)

    return {
        "claimable": len(claimable),
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
        ("Current claimable task", c["claimable"], "1", mark(c["claimable"], 1, exact=True)),
        ("Fully prepared tasks", c["prepared"], f"≥{PREPARED_FLOOR}", mark(c["prepared"], PREPARED_FLOOR)),
        ("Partially prepared tasks", c["partial"], "informational", "  "),
        ("Workflows not yet decomposed", c["undecomposed_workflows"], "0 eventually", mark(0, c["undecomposed_workflows"])),
        ("Workflows fully decomposed", c["decomposed_workflows"], f"{c['total_workflows']}", mark(c["decomposed_workflows"], c["total_workflows"])),
    ]
    width = max(len(r[0]) for r in rows)
    print("  PREPARED PIPELINE — D-188")
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

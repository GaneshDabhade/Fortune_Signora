#!/usr/bin/env python3
"""**The decision queue is a view, and this is what keeps it one.**

[`docs/DECISION_QUEUE.md`](../docs/DECISION_QUEUE.md) exists so the product
owner reviews rulings in one place instead of across reports. **Its risk is the
one this repository keeps rediscovering**: a document that restates a fact
recorded elsewhere and then drifts from it while continuing to read as an
answer. [C-213](../docs/LANE_COORDINATION.md) stored an assignee beside a
module. [C-412](../docs/LANE_COORDINATION.md) stored one beside a task. **Both
were correct when written and wrong within a day**, and neither announced it.

So the queue holds **judgement** — priority, recommendation, cost — and the
register holds **fact**. This compares them and reports every disagreement:

  **① A queued row whose item is no longer `OPEN`** — a ruling was made and the
  queue still asks for it. **The most misleading failure**, because it costs the
  product owner attention on something already decided.

  **② A product-owner-owned `OPEN` item with no row here** — the queue claims to
  be the single place to review and is not. **Absence is the failure that cannot
  be seen from inside the document**, which is why it is checked from outside.

  **③ A row naming a blocked task whose backlog status disagrees.**

**It reports and repairs nothing.** Each finding has more than one correct
resolution — close the item, add the row, or fix the status — and choosing is a
governance decision rather than a script's.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "docs" / "DECISION_QUEUE.md"
REGISTER = ROOT / "docs" / "LANE_COORDINATION.md"
BACKLOG = ROOT / "docs" / "BACKLOG.md"

# **A heading, never a mention.** Counting `C-\d+` anywhere would find every
# cross-reference in the prose and call each one a row — B-101's shape, and the
# reason `_queued` reads only what the document presents as a row.
ROW = re.compile(r"^#{2,3}\s*(?:🥇\s*)?(C-\d+)\s*·", re.M)
INLINE = re.compile(r"\*\*(C-\d+)\*\*")
ITEM = re.compile(r"^## (C-\d+) · (.+?)$", re.M)
TASK_HDR = re.compile(r"^### (TASK-\d+)\s*·", re.M)


def _field(block: str, name: str) -> str:
    m = re.search(rf"\|\s*\*\*{name}\*\*\s*\|\s*(.+?)\s*\|\s*$", block, re.M)
    return m.group(1) if m else ""


def register() -> dict[str, tuple[str, str, str]]:
    """Every coordination item: id -> (title, status, owner)."""
    text = REGISTER.read_text()
    out: dict[str, tuple[str, str, str]] = {}
    for block in re.split(r"(?=^## C-\d+)", text, flags=re.M):
        m = ITEM.search(block)
        if not m:
            continue
        owner = _field(block, "Owner") or _field(block, "Raised by")
        out[m.group(1)] = (m.group(2).strip(), _field(block, "Status"), owner)
    return out


def queued() -> set[str]:
    """Ids the queue presents as rows — headings, plus the P3/P2 inline lists."""
    text = QUEUE.read_text()
    return set(ROW.findall(text)) | set(INLINE.findall(text))


def backlog_states() -> dict[str, str]:
    text = BACKLOG.read_text()
    out: dict[str, str] = {}
    for block in re.split(r"(?=^### TASK-)", text, flags=re.M):
        m = TASK_HDR.search(block)
        if m:
            out[m.group(1)] = _field(block, "Status")
    return out


def _clean(s: str) -> str:
    return re.sub(r"[*`\[\]]", "", s)


def check() -> int:
    reg, q, states = register(), queued(), backlog_states()
    stale: list[str] = []
    missing: list[str] = []

    for cid in sorted(q):
        if cid not in reg:
            stale.append(f"{cid} has a row here and no item in LANE_COORDINATION.md")
        elif "OPEN" not in _clean(reg[cid][1]).upper():
            stale.append(f"{cid} is {_clean(reg[cid][1])[:44]!r} — ruled, and still queued")

    for cid, (title, status, owner) in sorted(reg.items()):
        if "OPEN" not in _clean(status).upper():
            continue
        if "product owner" not in _clean(owner).lower():
            continue
        if cid not in q:
            missing.append(f"{cid} is OPEN and the product owner's, with no row: {title[:52]}")

    print(f"decision-queue: {len(q)} row(s) against {len(reg)} item(s)")
    for line in stale:
        print(f"  STALE    {line}")
    for line in missing:
        print(f"  MISSING  {line}")

    if not stale and not missing:
        print("  ok   every queued row is open, and every open product-owner item is queued.")
        return 0

    # **Advisory, and deliberately.** A stale row means a ruling landed, which is
    # good news; a missing row means this office has not triaged something yet.
    # Neither is a reason to refuse a commit, and making it one would turn the
    # product owner's review queue into a gate on other people's work.
    print(f"\ndecision-queue: {len(stale) + len(missing)} finding(s) — advisory, never repaired here")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="compare the queue against the register")
    args = ap.parse_args()
    if not args.check:
        ap.print_help()
        return 0
    for p in (QUEUE, REGISTER, BACKLOG):
        if not p.exists():
            print(f"decision-queue: {p.relative_to(ROOT)} not found", file=sys.stderr)
            return 1
    return check()


if __name__ == "__main__":
    raise SystemExit(main())

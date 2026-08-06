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
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "docs" / "DECISION_QUEUE.md"
REGISTER = ROOT / "docs" / "LANE_COORDINATION.md"
BACKLOG = ROOT / "docs" / "BACKLOG.md"
MODULES = ROOT / "docs" / "coordination" / "modules.toml"

# **A heading, never a mention.** Counting `C-\d+` anywhere would find every
# cross-reference in the prose and call each one a row — B-101's shape, and the
# reason `_queued` reads only what the document presents as a row.
# **Any leading decoration is skipped, not one enumerated emoji.** The pattern
# named `🥇` alone and then missed four rows written with `⛔`, `⏱️` and `📌` —
# reporting them absent from a page they were on. **A heading's emoji is
# presentation and the id is the fact**, so match the id and ignore whatever
# precedes it; enumerating decorations is a list that goes stale the first
# time somebody picks a different one.
ROW = re.compile(r"^#{2,3}[^\w\n]*(C-\d+)\s*·", re.M)
# **A grouped listing is a bold id at the head of a table cell — never a bold
# id in prose.** The pattern required `**C-nnn**` literally, so the linked form
# `**[C-nnn](LANE_COORDINATION.md)**` did not count and twelve rows were
# reported absent from a table they were in. **Widening it to any bold id then
# over-corrected**: a live section citing `**[C-213](…)**` as context was read
# as queueing C-213, and eight decided items came back as stale.
#
# **The anchor is what separates the two.** A listing starts its own row; a
# reference sits inside a sentence. ⛔ **Under-reporting is the dangerous
# direction** — this module exists because absence cannot be seen from inside
# the document — but a check that cries wolf gets muted, which produces the
# same silence more slowly.
INLINE = re.compile(r"^\|\s*\*\*\[?(C-\d+)\]?", re.M)
# **Two heading shapes, because the register has two and pretending otherwise
# hid seven items.** The convention is `## C-nnn · title`; C-210 through C-216
# were written as `### C-nnn — title` (and C-210 as `####`), with an em-dash and
# a deeper level. **This module read only the convention and reported 71 items
# while the file held 78** — so the decision queue was audited against a
# register missing seven rows, one of which (C-215) is fully specified,
# claimable, and was sitting unqueued while its lane ran at three of five.
#
# **Matched rather than normalised.** Rewriting another lane's headings would
# break every `#c-215-…` anchor that links to them. A tool that only reads what
# it wishes the file looked like is the same defect as a guard pointed at the
# wrong ref.
ITEM = re.compile(r"^#{2,4} (C-\d+) [·—-] (.+?)$", re.M)
TASK_HDR = re.compile(r"^### (TASK-\d+)\s*·", re.M)


def _field(block: str, name: str) -> str:
    m = re.search(rf"\|\s*\*\*{name}\*\*\s*\|\s*(.+?)\s*\|\s*$", block, re.M)
    return m.group(1) if m else ""


SPLIT = re.compile(r"(?=^#{2,4} C-\d+ [·—-])", re.M)

# The `###` block writes its metadata as one bold line rather than a table:
# `**Opened 2026-08-03 · Lane A · current module assignee: Lane B · 🟠**`.
OPENED = re.compile(r"\*\*Opened[^*]*\*\*")
# **Both spellings, because both are used and reading one of them invented
# five ownerless items.** `owner: product owner` · `current module assignee:
# Lane B`. Missing these reported C-210, C-211, C-212 and C-216 as owned by
# nobody when their own first line names an owner.
ASSIGNEE = re.compile(r"(?:current module assignee|owner):\s*([^·*(]+)")
# **An owner deferred to the registry is owned, not unowned.** C-214 says
# *"owner: whoever is assigned `ai_platform`"* — which is the **correct** form
# under D-062: name the module and join, never store a lane's name. Reading it
# as ownerless punished the one row that got the rule right.
DEFERRED = re.compile(r"whoever is assigned\s*`?([a-z_]+)`?", re.I)


def _resolve(owner: str, registry: dict[str, object]) -> str:
    if m := DEFERRED.search(owner):
        entry = registry.get(m.group(1))
        if isinstance(entry, dict) and (lane := entry.get("current_owner")):
            return f"{lane} (via modules.toml — {m.group(1)})"
    return owner


def register() -> dict[str, tuple[str, str, str]]:
    """Every coordination item: id -> (title, status, owner).

    **Splitting on the convention alone swallowed seven items.** `^## C-\\d+`
    cannot match `### C-211`, so C-210–C-216 were absorbed into whichever `##`
    block preceded them and never appeared as rows at all — while
    `LANE_COORDINATION.md` reported 78 items and this module reported 71.
    """
    text = REGISTER.read_text()
    try:
        registry = tomllib.loads(MODULES.read_text())
    except (OSError, tomllib.TOMLDecodeError):
        registry = {}      # **No registry, no opinion** — never a default owner.
    out: dict[str, tuple[str, str, str]] = {}
    for block in SPLIT.split(text):
        m = ITEM.search(block)
        if not m:
            continue
        status = _field(block, "Status")
        # **Three field names, and each one I missed invented ownerless items.**
        # `Owner` · `Current assignee(s)` · `Raised by`. Reading only the first
        # two reported C-010, C-011 and C-014 as owned by nobody while all three
        # say **Product owner** under `Current assignee(s)`.
        owner = (_field(block, "Owner")
                 or _field(block, r"Current assignee\(s\)")
                 or _field(block, "Raised by"))
        if not status and (opened := OPENED.search(block)):
            # **No table, so the bold line is the record.** An item in this
            # block is open unless its own text says it closed — the same
            # default the tabled rows carry, stated rather than inferred.
            status = "OPEN" if "closed" not in opened.group(0).lower() else "CLOSED"
            if a := ASSIGNEE.search(opened.group(0)):
                owner = a.group(1).strip()
        out[m.group(1)] = (m.group(2).strip(), status, _resolve(owner, registry))
    return out


#: **A closed list is a record, not a queue**, and reading past this marker made
#: every item the product owner had just closed report as STALE — the queue
#: asking for a ruling that had been made, which is the exact failure this
#: module exists to catch. `LANE_COORDINATION.md` already uses a `## Closed`
#: marker for the same reason.
CLOSED_MARKER = re.compile(r"^#{1,3} Closed\b", re.M | re.I)


#: The register's summary table — `| [C-nnn](#anchor) | … | status | blocks |`.
#: **A second representation of a status the item body already carries**, and
#: therefore the shape this repository keeps paying for: C-213 stored an
#: assignee beside a module, C-412 stored one beside a task, and this stores a
#: status beside an item. **Eighteen rows disagreed when it was first measured**
#: — eleven of them because a ruling was recorded in the body and not the index.
#:
#: **Not removed, because the index is what a lane reads first.** Compared
#: instead, so the lag between a ruling and the index is visible in one command
#: rather than discovered by a lane claiming into it — which is how Lane A
#: found C-206 and C-208 *"a day late"*.
INDEX_ROW = re.compile(r"^\| \[(C-\d+)\]\([^)]*\) \|.*?\| ([^|]*?) \| [^|]*\|\s*$", re.M)


#: The declared state is the first backticked token, never a word in the prose.
#: **Substring matching flagged C-226 on its first run**: its status reads
#: *"`OPEN` — nothing is blocked… this asks whether the class should be closed"*,
#: and the word *closed* in an explanation made an open item read as shut.
#: **That is [B-101](../docs/BUGS.md) — counting by substring — inside the check
#: written to catch its cousin**, found by running it rather than by review.
DECLARED = re.compile(r"`([A-Z][A-Z ]+)`")

_SHUT = {"CLOSED", "RULED", "ANSWERED", "RESOLVED", "SUPERSEDED", "WITHDRAWN",
         # **Decided, and therefore not queued.** The lane may proceed; nobody
         # owes an answer. It is *not* closed — the requesting lane closes it —
         # but it must never sit on the product owner's page.
         "READY FOR IMPLEMENTATION"}

#: **The five §20e lifecycle states that mean *somebody still owes an answer*.**
#: Missing, this set made `READY FOR PRODUCT DECISION` — **the single most open
#: thing an item can be** — read as shut: `_is_open` found no `OPEN` token, fell
#: through to the prose, and the prose does not contain the word. **C-417 was
#: raised, and the check that exists to find unqueued product-owner items said
#: nothing about it**; C-004 and C-201 had been reporting as INDEX drift for the
#: same reason. **Found by using the instrument, which is the only way any of
#: these have been found.**
_OPEN_STATES = {"OPEN", "READY FOR LANE C", "AWAITING LANE C", "IN ANALYSIS",
                "READY FOR PRODUCT DECISION"}


def _is_open(text: str) -> bool:
    for token in DECLARED.findall(text):
        state = token.strip()
        if state in _SHUT:
            return False
        if state in _OPEN_STATES:
            return True
    # **No declared state at all.** Fall back to the prose rather than guess a
    # default: an item with no backticked status is a formatting defect, and
    # reading it as open is the safer of the two wrong answers.
    upper = _clean(text).upper()
    return "OPEN" in upper


def index_absences(reg: dict[str, tuple[str, str, str]]) -> list[str]:
    """Open items the summary table does not list at all.

    **The drift check compares rows that exist, so an item with no row was never
    compared** — 25 of 82 when this was first measured, including C-328 which the
    product owner had ruled that morning and C-412 which this office had
    corrected. **Absence is not a pass**, and a lane reading the index first
    cannot see what the index omits.
    """
    listed = {m.group(1) for m in INDEX_ROW.finditer(REGISTER.read_text())}
    return [f"{cid} is OPEN and has no row in the summary index: {reg[cid][0][:46]}"
            for cid in sorted(set(reg) - listed)
            if _clean(reg[cid][1]).strip() and _is_open(reg[cid][1])]


def index_disagreements(reg: dict[str, tuple[str, str, str]]) -> list[str]:
    """Items whose summary row and body disagree about being open."""
    text = REGISTER.read_text()
    out: list[str] = []
    for m in INDEX_ROW.finditer(text):
        cid, shown = m.group(1), m.group(2)
        if cid not in reg:
            continue
        # **Absent is not closed.** Six items carry no `Status` field at all,
        # and reading an empty string as *not open* would report every one of
        # them as drift — the `missing_gates` rule, which this repository has
        # paid for nine times in CHECK constraints and once in this module.
        if not _clean(reg[cid][1]).strip():
            continue
        if _is_open(shown) != _is_open(reg[cid][1]):
            out.append(f"{cid} index says {_clean(shown).strip()[:28]!r}, "
                       f"body says {_clean(reg[cid][1]).strip()[:28]!r}")
    return out


def queued() -> set[str]:
    """Ids the queue presents as rows — headings, plus the inline groupings.

    **Everything after the `Closed` marker is history and is not read.**
    """
    text = QUEUE.read_text()
    if m := CLOSED_MARKER.search(text):
        text = text[: m.start()]
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

    # **`"OPEN" in status.upper()` is B-101, and it was in this file.** C-416's
    # Status reads *"`RULED` — 2026-08-05, and closed on the same day it was
    # opened"*: **"opened" contains "OPEN"**, so a ruled item reported as the
    # product owner's open work with no queue row — the checker inventing the
    # exact drift it exists to find. `_is_open` reads the *declared* backticked
    # token first and only falls back to prose, which is why the index checks
    # below never had this bug. **Every status read here goes through it now.**
    for cid in sorted(q):
        if cid not in reg:
            stale.append(f"{cid} has a row here and no item in LANE_COORDINATION.md")
        elif not _is_open(reg[cid][1]) and "AWAITING" not in reg[cid][1].upper():
            # **`RULED, awaiting provision` is decided and still needs the
            # product owner** — D-131 ⑤ calls C-334 *operational configuration*:
            # the ruling was taken and the credential is not yet supplied.
            # Dropping it from the queue would hide an action; reporting it as
            # stale would train a reader to ignore this check. **It is neither
            # an open question nor finished work**, and the queue is the only
            # place that difference is visible.
            stale.append(f"{cid} is {_clean(reg[cid][1])[:44]!r} — ruled, and still queued")

    unowned: list[str] = []
    for cid, (title, status, owner) in sorted(reg.items()):
        if not _is_open(status):
            continue
        # **An open item naming no owner is the worse case, and it reported
        # `ok` until this existed.** A product-owner item waits on somebody; an
        # unowned one waits on nobody, and nothing in the repository was
        # looking for that. Five of the seven `###` items are in this state.
        if not _clean(owner).strip():
            unowned.append(f"{cid} is OPEN and names no owner: {title[:52]}")
            continue
        if "product owner" not in _clean(owner).lower():
            continue
        if cid not in q:
            missing.append(f"{cid} is OPEN and the product owner's, with no row: {title[:52]}")

    drift = index_disagreements(reg)
    absent = index_absences(reg)

    print(f"decision-queue: {len(q)} row(s) against {len(reg)} item(s)")
    for line in drift:
        print(f"  INDEX    {line}")
    for line in absent:
        print(f"  UNLISTED {line}")
    for line in stale:
        print(f"  STALE    {line}")
    for line in missing:
        print(f"  MISSING  {line}")
    for line in unowned:
        print(f"  UNOWNED  {line}")

    if not stale and not missing and not unowned and not drift and not absent:
        print("  ok   every queued row is open, and every open product-owner item is queued.")
        return 0

    # **Advisory, and deliberately.** A stale row means a ruling landed, which is
    # good news; a missing row means this office has not triaged something yet.
    # Neither is a reason to refuse a commit, and making it one would turn the
    # product owner's review queue into a gate on other people's work.
    print(f"\ndecision-queue: {len(stale) + len(missing) + len(unowned) + len(drift) + len(absent)} finding(s) — advisory, never repaired here")
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

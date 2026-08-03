#!/usr/bin/env python3
"""**Does the platform emit an event the contract does not name?**

*Repository Health · category: **Documentation Synchronization**.*

`06-events.md` is the catalog every module reads to know what it may consume.
`CLAUDE.md` §9 requires a new event to be added to it **in the same change** that
introduces it. Nothing checked, and one event slipped: `commercial_profile`
publishes `target_accounts_changed` and the catalog does not list it.

### What was measured before this was written

**Twenty-four of twenty-five declared events are correctly catalogued.**

That number is the reason this check is *advisory* rather than alarmed, and it
is worth stating plainly for anyone reading the one finding it reports:

> **C-004 exposed a workflow gap, not poor repository discipline.** The lane
> that emitted the event **may not edit `06-events.md`** — it is 🔴, product
> owner and ADR only — so §9's *"cataloged in the same change"* was
> *unsatisfiable by the lane that incurred it*. The catalog has been maintained
> well by everyone who was allowed to maintain it.

**That workflow will recur**, and fixing it is Lane C's ([C-101](../docs/LANE_COORDINATION.md)), not this checker's. This reports the drift; it does not design the process that prevents it.

### Why advisory, and why that is not weakness

**A gate that fails on something its owner cannot fix teaches people to ignore
gates.** The one finding it reports today can only be cleared by an edit to a
🔴 file — so gating on it would make every lane's run red for a reason no lane
could act on, and the second-order cost of that is every *other* warning being
skimmed. Same reasoning as `doc-drift`, and the same shape: **visible,
measurable, actionable, non-blocking.**

**It becomes gateable the day the catalog can be updated by whoever emits the
event** — which is exactly the workflow C-101 asks Lane C to design.

    python3 infra/event-catalog.py
    python3 infra/event-catalog.py --strict   # exit 1 on drift, for a future gate

The third sibling of a family:

    runtime-composition.py   does the deployed worker consume what a module projects?
    reachability.py          can a customer reach this screen?
    event-catalog.py         is an emitted event in the contract other modules read?
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Final

REPO_ROOT: Final = Path(__file__).resolve().parent.parent
MODULES: Final = REPO_ROOT / "backend" / "modules"
CATALOG: Final = REPO_ROOT / "docs" / "architecture" / "06-events.md"

#: Both spellings a module uses to declare its own event type. **Read from
#: `domain/events.py` only** — an event type is domain vocabulary, and a string
#: that looks like one in an adapter or a test is not a declaration.
_DECLARATION: Final = re.compile(
    r'(?:event_type[^=\n]*|EVENT_TYPE[^=\n]*)= *"([a-z_]+\.[a-z_.]+)"'
)


def declared() -> dict[str, str]:
    """Every event type a module declares, mapped to the module that owns it."""
    found: dict[str, str] = {}
    for path in sorted(MODULES.rglob("domain/events.py")):
        module = path.relative_to(MODULES).parts[0]
        for event in _DECLARATION.findall(path.read_text()):
            found[event] = module
    return found


def catalogued(text: str) -> set[str]:
    """Event types the catalog names.

    **Substring containment, deliberately.** The catalog writes an event type in
    a table cell, in prose, and inside a code fence, and a parser demanding one
    shape would report drift every time somebody reformatted a row — which is
    the false positive that gets a check deleted.
    """
    return {event for event in declared() if event in text}


def report(*, strict: bool) -> int:
    events = declared()
    present = catalogued(CATALOG.read_text())
    missing = sorted(set(events) - present)

    print("\n  Event catalog — is every emitted event in the contract?\n")
    print(f"    declared in code   {len(events)}")
    print(f"    in `06-events.md`  {len(events) - len(missing)}")

    if not missing:
        print("\n  Every declared event is catalogued.\n")
        return 0

    print(f"    MISSING            {len(missing)}\n")
    for event in missing:
        print(f"      {event}   ← owned by `{events[event]}`")
    print(
        "\n  `CLAUDE.md` §9 requires the catalog to be updated in the same change"
        "\n  that introduces an event. **`06-events.md` is 🔴**, so a lane that emits"
        "\n  one cannot satisfy that rule itself — which is the workflow gap"
        "\n  C-101 asks Lane C to design, not a defect in the lane."
        "\n"
        "\n  Advisory: this reports and does not gate. A check that fails on"
        "\n  something its owner cannot fix teaches people to ignore checks.\n"
    )
    return 1 if strict else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict", action="store_true", help="exit 1 on drift (not used by any gate today)"
    )
    return report(strict=parser.parse_args().strict)


if __name__ == "__main__":
    sys.exit(main())

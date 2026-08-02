#!/usr/bin/env python3
"""**What does the deployed worker actually consume?**

Five layers get validated, and the suite covers four of them:

    module implementation      ✅ unit tests
    module tests               ✅ its own suite
    cross-module composition   ✅ integration tests
    runtime composition        ✅ `make smoke`
    deployed composition       ❌ nothing

**A composition root is the one file no module's own suite covers.** Each module
tests its half and assumes the wiring, so a handler that nothing calls passes
every gate — which is how Timeline shipped complete and consumed nothing
([B-301](../docs/BUGS.md)), through four certified promotions.

**This reports; it does not fail a build.** Most unwired consumers here are
*deliberate*: [C-012](../docs/LANE_COORDINATION.md) has recorded since M3A that
`EventHandler` receives no session, so the pipeline runs in-process and the
deployed worker consumes almost nothing. **That is a known, product-owner-blocked
decision, not a defect** — and a check that cried defect at it would be ignored
within a cycle.

**What it is for** is that C-012's claim — *"the deployed worker consumes
nothing"* — has been prose since M3A and nothing re-measured it. This makes it a
number, every cycle, so the gap is visible while it is deliberate and obvious the
moment it stops being.

    python3 infra/runtime-composition.py
    python3 infra/runtime-composition.py --strict   # exit 1 if any is unwired
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULES = REPO_ROOT / "backend" / "modules"

# **Which modules the current architecture expects to be consuming *today*.**
#
# Without this, "8 unwired" reads as eight defects, and it is one. The pipeline
# stages are deliberately unwired under C-012 — `EventHandler` receives no
# session, so they run in-process — and that is a product-owner decision with an
# RFC attached, not a gap.
#
# **A judgement, maintained by QE, re-checked every cycle**, and deliberately a
# short list rather than an inferred one: inferring it would mean guessing which
# blockage is intentional, which is exactly the question a human should answer.
# **Moving a module out of BLOCKED_BY_C012 is how the architecture records that
# it now expects live consumption.**
BLOCKED_BY_C012 = {
    "business_event_engine": "pipeline stage — in-process until C-012",
    "buying_score_engine": "pipeline stage — in-process until C-012",
    "knowledge_graph": "pipeline stage — in-process until C-012",
    "observation_engine": "pipeline stage — in-process until C-012",
    "opportunity_engine": "pipeline stage — in-process until C-012",
    "provider_platform": "pipeline stage — in-process until C-012",
    "signal_engine": "pipeline stage — in-process until C-012",
}
WORKER = REPO_ROOT / "backend" / "apps" / "worker"


def _declared_consumers() -> dict[str, list[str]]:
    """Modules that declare themselves event consumers.

    `CONSUMER_NAME` in a module's `interface/handlers.py` is the repository's
    marker for *"this module consumes events"* — it is what the idempotency
    ledger keys on, so a module that has one intends to be subscribed.
    """
    found: dict[str, list[str]] = {}
    for handlers in sorted(MODULES.glob("*/interface/handlers.py")):
        text = handlers.read_text()
        if "CONSUMER_NAME" not in text:
            continue
        module = handlers.parent.parent.name
        # The handler functions a subscription would name: module-level `async
        # def` taking an envelope. Private helpers are excluded.
        entries = re.findall(r"^async def ([a-z_][a-z0-9_]*)\(", text, re.M)
        found[module] = [e for e in entries if not e.startswith("_")]
    return found


def _worker_text() -> str:
    if not WORKER.is_dir():
        return ""
    return "\n".join(p.read_text() for p in WORKER.rglob("*.py"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    declared = _declared_consumers()
    if not declared:
        print("\n  No module declares a consumer. Nothing to check.")
        return 0

    worker = _worker_text()
    subscriptions = len(re.findall(r"registry\.subscribe\(", worker))

    wired: list[str] = []
    unwired: list[tuple[str, list[str]]] = []
    for module, handlers in sorted(declared.items()):
        # Wired means the deployed worker names one of the module's handlers.
        # Importing the module is not enough — Timeline's package was imported
        # transitively and still consumed nothing.
        if any(re.search(rf"\b{re.escape(h)}\b", worker) for h in handlers):
            wired.append(module)
        else:
            unwired.append((module, handlers))

    blocked = [(m, h) for m, h in unwired if m in BLOCKED_BY_C012]
    unexpected = [(m, h) for m, h in unwired if m not in BLOCKED_BY_C012]
    expected = len(declared) - len(blocked)

    print("\n  Runtime Composition\n")
    print(f"    Modules declaring consumers        {len(declared)}")
    print(f"    Runtime wired                      {len(wired)}")
    print(f"    Waiting on architectural decision  {len(blocked)}   (C-012)")
    print(f"    Expected by current architecture   {expected}")
    print(f"    Unexpected missing wiring          {len(unexpected)}"
          f"{'   ← every one is a defect' if unexpected else ''}")
    print(f"\n    {subscriptions} registry.subscribe() call(s) in apps/worker\n")

    if wired:
        print("    wired:")
        for module in wired:
            print(f"      ✓ {module}")
    if unexpected:
        print("\n    UNEXPECTED — declared, expected to be wired, and is not:")
        for module, handlers in unexpected:
            print(f"      ✗ {module:<26} {', '.join(handlers[:3]) or 'no public handler'}")
    if blocked:
        print("\n    waiting on C-012, deliberately:")
        for module, _ in blocked:
            print(f"      · {module:<26} {BLOCKED_BY_C012[module]}")

    print(
        "\n  This answers *what is deployed today*, never *what should eventually"
        "\n  exist*. The C-012 group is a product-owner decision with an RFC"
        "\n  attached, and counting it as failure would make the number useless."
        "\n"
        "\n  **Unexpected missing wiring is the line that matters.** It was 1"
        "\n  when B-301 was found, and every one of them is a capability that"
        "\n  ships complete and does nothing."
    )
    return 1 if (args.strict and unexpected) else 0


if __name__ == "__main__":
    sys.exit(main())

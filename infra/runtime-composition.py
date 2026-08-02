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

    print(f"\n  Deployed composition — `apps/worker`\n")
    print(f"    {subscriptions} registry.subscribe() call(s)")
    print(f"    {len(wired)} of {len(declared)} modules declaring a consumer are wired\n")

    if wired:
        print("    wired:")
        for module in wired:
            print(f"      ✓ {module}")
    if unwired:
        print("\n    declared but not wired:")
        for module, handlers in unwired:
            names = ", ".join(handlers[:3]) or "no public handler"
            print(f"      · {module:<26} {names}")

    print(
        "\n  Most of these are deliberate. C-012 has recorded since M3A that"
        "\n  `EventHandler` receives no session, so the pipeline runs in-process"
        "\n  and the deployed worker consumes almost nothing. **That is a"
        "\n  product-owner decision, not a defect.**"
        "\n"
        "\n  What this number is for: C-012's claim was prose that nothing"
        "\n  re-measured. Now it moves — up when a module is wired, and visibly"
        "\n  not when one ships expecting to be."
    )
    return 1 if (args.strict and unwired) else 0


if __name__ == "__main__":
    sys.exit(main())

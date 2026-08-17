#!/usr/bin/env python3
"""**What is built, module by module — counted, never claimed.**

Generates `IMPLEMENTATION_STATUS.md`. **Nothing here is a judgement**: every
column is a count taken from the repository at the moment it runs, which is why
this file exists rather than a table somebody maintains by hand.

**The rule it enforces** (`REPOSITORY_SOURCE_OF_TRUTH.md`): *generate what is
countable, hand-write what is judgement, and never generate something a human
will then edit.* A generated file carrying manual edits drifts **and** nobody
trusts the regeneration — the worst of both — so the output says so at the top.

**Why counting is the right instrument here.** The repository's own history is
the divergence between layers: 46 endpoints behind 11 routes. A hand-maintained
matrix would have recorded intent; this records arithmetic, and the gap between
them is the finding worth having.

Run: `python3 infra/implementation-status.py` — writes, or `--check` to compare.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import TypedDict

ROOT = Path(__file__).resolve().parent.parent
MODULES = ROOT / "backend" / "modules"
TESTS = ROOT / "backend" / "tests"
FRONTEND = ROOT / "frontend"
OUT = ROOT / "IMPLEMENTATION_STATUS.md"

#: A decorated route can span several lines, so the verb is counted rather than
#: the path — `@router.get(` is one endpoint whatever follows it.
ROUTE = re.compile(r"^@router\.(get|post|put|patch|delete)\(", re.M)
EVENT = re.compile(r'"[a-z_]+\.[a-z_.]+"')


def _count(path: Path, pattern: re.Pattern[str]) -> int:
    if not path.exists():
        return 0
    return len(pattern.findall(path.read_text(encoding="utf-8", errors="replace")))


def _layers(module: Path) -> dict[str, bool]:
    return {name: (module / name).is_dir() for name in ("domain", "application", "infrastructure", "interface")}


class ModuleRow(TypedDict):
    """One row of the backend table.

    A `TypedDict` rather than `dict[str, object]`, because the renderer sums
    `endpoints` and indexes `layers` — under `object` both are errors the type
    checker cannot see past, so every field read was unverified.
    """

    name: str
    layers: dict[str, bool]
    endpoints: int
    events: int
    public: bool
    tests: int
    design_doc: str


def _module_row(module: Path) -> ModuleRow:
    layers = _layers(module)
    return {
        "name": module.name,
        "layers": layers,
        "endpoints": _count(module / "interface" / "router.py", ROUTE),
        "events": len(set(EVENT.findall((module / "domain" / "events.py").read_text(errors="replace"))))
        if (module / "domain" / "events.py").exists()
        else 0,
        "public": (module / "public").exists() or (module / "public.py").exists(),
        "tests": len(list((TESTS / module.name).rglob("test_*.py"))) if (TESTS / module.name).is_dir() else 0,
        "design_doc": _design_doc(module.name),
    }


def _design_doc(name: str) -> str:
    """A module's design document, found by name rather than by a hardcoded map.

    A map would need editing every time a module arrives, which is the manual
    maintenance this script exists to remove.
    """
    stem = name.replace("_", "-")
    for doc in sorted((ROOT / "docs" / "architecture").glob("[0-9]*.md")):
        if stem in doc.stem or name in doc.read_text(errors="replace")[:400]:
            return doc.name
    return "—"


def _frontend() -> dict[str, int]:
    app = FRONTEND / "app"
    return {
        "routes": len(list(app.rglob("page.tsx"))) if app.is_dir() else 0,
        "api_routes": len(list(app.rglob("route.ts"))) if app.is_dir() else 0,
        "components": len(list((FRONTEND / "components").rglob("*.tsx"))) if (FRONTEND / "components").is_dir() else 0,
        "tests": len(list((FRONTEND / "tests").rglob("*.test.tsx")))
        + len(list((FRONTEND / "tests").rglob("*.spec.ts")))
        if (FRONTEND / "tests").is_dir()
        else 0,
    }


def _head() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:
        return "unknown"


def render() -> str:
    rows = [_module_row(m) for m in sorted(MODULES.iterdir()) if m.is_dir() and not m.name.startswith("_")]
    fe = _frontend()

    def tick(present: bool) -> str:
        return "✅" if present else "—"

    out = [
        "# Implementation Status",
        "",
        "> ⚙️ **GENERATED — do not edit by hand.** Rebuild with `python3 infra/implementation-status.py`.",
        "> **Manual edits are lost on the next run, and a generated file carrying them drifts while nobody trusts the regeneration.**",
        "",
        f"> Counted at `{_head()}`. **Every figure is arithmetic over the repository, never a claim about intent.**",
        "> **What a screen looks like is not counted here** — the approved specification is",
        "> [`410`](docs/architecture/410-approved-ui-specification.md), and UI convergence is tracked in",
        "> [`412`](docs/architecture/412-backend-capability-matrix.md).",
        "",
        "## Backend, by module",
        "",
        "| Module | Domain | Application | Infrastructure | Interface | Endpoints | Events | `public/` | Tests | Design doc |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lay = r["layers"]
        out.append(
            f"| `{r['name']}` | {tick(lay['domain'])} | {tick(lay['application'])} | {tick(lay['infrastructure'])} "
            f"| {tick(lay['interface'])} | {r['endpoints']} | {r['events']} | {tick(r['public'])} | {r['tests']} "
            f"| {r['design_doc']} |"
        )

    reachable = [r for r in rows if r["endpoints"]]
    unreachable = [r for r in rows if not r["layers"]["interface"]]
    out += [
        "",
        f"**{len(rows)} modules · {sum(r['endpoints'] for r in rows)} endpoints across {len(reachable)} routers "
        f"· {sum(r['events'] for r in rows)} event types · {sum(r['tests'] for r in rows)} backend test files.**",
        "",
    ]
    if unreachable:
        names = " · ".join(f"`{r['name']}`" for r in unreachable)
        out += [
            f"> **{len(unreachable)} modules have no `interface/` layer: {names}.**",
            "> **Some of these are correct** — a pipeline stage is not a request surface. **The rest are the recurring",
            "> pattern**: built, tested, published and unreachable. The three-question heuristic decides which is which —",
            "> *does it exist · can a customer reach it · is it consumed elsewhere*.",
            "",
        ]

    out += [
        "## Frontend",
        "",
        "| | Count |",
        "|---|---|",
        f"| Routes (`page.tsx`) | {fe['routes']} |",
        f"| API routes (`route.ts`) | {fe['api_routes']} |",
        f"| Components | {fe['components']} |",
        f"| Test files | {fe['tests']} |",
        "",
        f"> **{sum(r['endpoints'] for r in rows)} endpoints behind {fe['routes']} routes.** That ratio is the repository's",
        "> central fact and the reason this file counts backend and frontend separately rather than blending them into",
        "> one percentage — **one number would hide the only interesting thing here.**",
        "",
    ]
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="exit 1 if the file is stale, and write nothing")
    args = ap.parse_args()
    new = render()
    if args.check:
        current = OUT.read_text() if OUT.exists() else ""
        # The commit line moves on every commit; comparing without it asks the
        # question that matters — has anything *counted* changed?

        def strip(text: str) -> str:
            return "\n".join(l for l in text.splitlines() if not l.startswith("> Counted at"))

        if strip(current) == strip(new):
            print("implementation-status: current.")
            return 0
        print("implementation-status: STALE — run `python3 infra/implementation-status.py`.")
        return 1
    OUT.write_text(new)
    print(f"implementation-status: wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

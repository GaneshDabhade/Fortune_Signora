#!/usr/bin/env python3
"""Advisory check: did a slice change production code without updating its
module's documentation?

**Advisory, deliberately.** It exits 0 unless asked not to. It reports what it
can see mechanically and makes **no judgement about whether documentation is
good** — it cannot, and a check that pretended to would be worse than none,
because a passing run would be read as "the docs are fine".

Three mechanical signals, and nothing else:

  1. production code changed under `backend/modules/<m>/` while that module's
     design document was untouched;
  2. a Slice Handoff whose `Docs:` field is empty on a range that changed
     behaviour;
  3. a module whose design document this script cannot locate — reported as
     unknown rather than silently passing, because an unmapped module is how
     a check quietly stops covering things.

Run it over the range a lane is about to hand to QE:

    python3 infra/doc-drift.py                 # integration..HEAD
    python3 infra/doc-drift.py main..HEAD
    python3 infra/doc-drift.py --strict        # exit 1 on any finding

CLAUDE.md §12 states the rule this reports against; it does not enforce it.
Enforcement is a human reading the finding and deciding.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# A module's documentation of record. Kept explicit rather than derived from a
# naming convention: three modules genuinely have no design document of their
# own, and inferring one would invent a file and report drift against it.
MODULE_DOCS: dict[str, tuple[str, ...]] = {
    "workspace_tenancy": ("docs/architecture/04-modules.md",),
    "provider_platform": ("docs/architecture/20-provider-simulation.md",),
    "provider_normalization": ("docs/architecture/34-knowledge-contract.md",),
    "knowledge_graph": ("docs/architecture/22-knowledge-graph.md",),
    "observation_engine": ("docs/architecture/23-observation-engine.md",),
    "business_event_engine": ("docs/architecture/24-business-event-engine.md",),
    "signal_engine": ("docs/architecture/25-signal-engine.md",),
    "buying_score_engine": ("docs/architecture/26-buying-score-engine.md",),
    "opportunity_engine": ("docs/architecture/27-opportunity-engine.md",),
    "ai_platform": ("docs/architecture/28-ai-platform.md",),
    "ai_reasoning_engine": ("docs/architecture/29-ai-reasoning-engine.md",),
    "ai_research_engine": ("docs/architecture/33-ai-research-engine-scope.md",),
    "commercial_profile": ("docs/architecture/adr/0035-commercial-profile.md",),
}

_MODULE_PATH = re.compile(r"^backend/modules/(?P<module>[a-z_]+)/")
_HANDOFF_DOCS = re.compile(r"^\s*Docs:\s*(?P<value>.*)$", re.MULTILINE)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout


def _changed_files(rev_range: str) -> list[str]:
    return [line for line in _git("diff", "--name-only", rev_range).splitlines() if line]


def _is_production_code(path: str) -> bool:
    """A module's own tests are not production code, and a slice may legitimately
    change only them."""
    return path.endswith(".py") and "/tests/" not in path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rev_range", nargs="?", default="integration..HEAD")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 when anything is found (default: advisory, always exit 0)",
    )
    args = parser.parse_args()

    try:
        changed = _changed_files(args.rev_range)
    except subprocess.CalledProcessError as error:
        print(f"cannot read {args.rev_range}: {error.stderr.strip()}", file=sys.stderr)
        return 2

    if not changed:
        print(f"doc-drift: {args.rev_range} changed nothing.")
        return 0

    touched_modules: set[str] = set()
    for path in changed:
        match = _MODULE_PATH.match(path)
        if match and _is_production_code(path):
            touched_modules.add(match.group("module"))

    findings: list[str] = []

    for module in sorted(touched_modules):
        docs = MODULE_DOCS.get(module)
        if docs is None:
            findings.append(
                f"{module}: production code changed, and this script knows of no "
                f"design document for it. Add one to MODULE_DOCS, or record that "
                f"the module genuinely has none."
            )
            continue
        if not any(doc in changed for doc in docs):
            findings.append(
                f"{module}: production code changed; {' / '.join(docs)} did not. "
                f"Could a lane that has never seen this module continue without "
                f"reading commit history? (CLAUDE.md §12)"
            )

    if touched_modules:
        log = _git("log", "--format=%B", args.rev_range)
        if "Slice-Handoff" in log:
            values = [m.group("value").strip() for m in _HANDOFF_DOCS.finditer(log)]
            if not values or all(v in ("", "none", "None", "-") for v in values):
                findings.append(
                    "Slice Handoff: `Docs:` is empty on a range that changed "
                    "production code."
                )
        else:
            findings.append(
                "No Slice-Handoff block in this range. QE writes the project "
                "status from it (CLAUDE.md §20e)."
            )

    if not findings:
        print(
            f"doc-drift: {args.rev_range} — "
            f"{len(touched_modules)} module(s) touched, documentation moved with them."
        )
        return 0

    print(f"doc-drift: {len(findings)} advisory finding(s) in {args.rev_range}\n")
    for finding in findings:
        print(f"  · {finding}")
    print(
        "\nAdvisory only. This check sees whether a file changed, never whether "
        "what it says is true."
    )
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())

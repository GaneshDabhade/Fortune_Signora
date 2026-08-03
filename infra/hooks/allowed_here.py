#!/usr/bin/env python3
"""**May these paths be committed on this branch?**

Reads staged paths on stdin, exits 0 if every one is allowed and 1 otherwise,
printing the offenders.

**It owns no rules.** `infra/certification-guard.py` already defines what may
live on `main` (a Closeout) and on `integration` (a claim), and those definitions
are imported rather than copied — a second copy would eventually disagree with
the first, and the one nobody is maintaining is the one somebody will trust
(`CLAUDE.md` §2).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

INFRA = Path(__file__).resolve().parent.parent


def _guard() -> ModuleType:
    """Import `certification-guard.py`, whose filename is not an identifier."""
    spec = importlib.util.spec_from_file_location(
        "certification_guard", INFRA / "certification-guard.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def offenders(branch: str, paths: list[str]) -> list[str]:
    guard = _guard()
    if branch == "main":
        return [
            path
            for path in paths
            if not (
                path.startswith(guard.CLOSEOUT_PATHS)
                and path.endswith(guard.CLOSEOUT_SUFFIXES)
            )
        ]
    if branch == "integration":
        return [path for path in paths if path not in guard.CLAIM_PATHS]
    return []


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: allowed_here.py <branch>  (staged paths on stdin)", file=sys.stderr)
        return 2

    branch = sys.argv[1]
    paths = [line.strip() for line in sys.stdin if line.strip()]
    bad = offenders(branch, paths)
    if not bad:
        return 0

    allowed = (
        "a Closeout — documents and certification records only"
        if branch == "main"
        else "a claim — docs/ACTIVE_ASSIGNMENTS.md and docs/BACKLOG.md only"
    )
    print(f"  `{branch}` accepts {allowed}. These do not qualify:\n")
    for path in bad[:8]:
        print(f"    · {path}")
    if len(bad) > 8:
        print(f"    … and {len(bad) - 8} more")
    return 1


if __name__ == "__main__":
    sys.exit(main())

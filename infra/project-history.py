#!/usr/bin/env python3
"""**What happened, and when — the significant events only.**

Generates `PROJECT_HISTORY.md`. **Not a changelog**: `git log` is already the
complete record, and a second copy of it would be a duplicate representation
(`CLAUDE.md` §2). This answers the narrower question a returning session asks —
*what were the turning points?*

**Significance is defined structurally, never by judgement**, because judgement
in a generated file is judgement nobody can review:

  · an ADR              — the repository's own definition of a decision worth recording
  · a Closeout commit   — a completed repository cycle
  · a migration         — the schema changed, and schema changes are irreversible facts
  · a milestone record  — a dated architecture document in the historical range

**Everything else is deliberately excluded.** A commit that fixed a typo is in
`git log`; it is not a turning point, and a history that lists it teaches the
reader to stop reading.

Run: `python3 infra/project-history.py` — writes, or `--check` to compare.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADR = ROOT / "docs" / "architecture" / "adr"
MIGRATIONS = ROOT / "backend" / "migrations" / "versions"
OUT = ROOT / "PROJECT_HISTORY.md"

DATE = re.compile(r"20\d\d-\d\d-\d\d")
#: An ADR's status word, taken from the first 40 lines so a later mention of
#: "proposed" in the prose cannot be mistaken for the status itself.
STATUS = re.compile(r"\b(RATIFIED|PRODUCT OWNER APPROVED|Accepted|Proposed|Superseded|Rejected)\b")


def _git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except Exception:
        return ""


def _adrs() -> list[tuple[str, str, str, str]]:
    rows = []
    for f in sorted(ADR.glob("[0-9]*.md")):
        head = "\n".join(f.read_text(errors="replace").splitlines()[:40])
        date = DATE.search(head)
        status = STATUS.search(head)
        title = f.stem.split("-", 1)[-1].replace("-", " ")
        rows.append((date.group(0) if date else "—", f.stem.split("-")[0], title, status.group(0) if status else "—"))
    return sorted(rows, key=lambda r: (r[0], r[1]))


def _cycles() -> list[tuple[str, str]]:
    """Completed repository cycles, from Closeout commits.

    A Closeout is the one commit type that provably marks a finished cycle —
    `certification-guard.py --audit-main` already relies on that property.
    """
    raw = _git("log", "--date=short", "--pretty=%ad\t%s", "--grep=Repository Closeout", "--regexp-ignore-case")
    out = []
    for line in raw.splitlines():
        if "\t" in line:
            d, s = line.split("\t", 1)
            out.append((d, s.strip()))
    return sorted(set(out))


def _migrations() -> list[str]:
    return sorted(p.stem for p in MIGRATIONS.glob("[0-9]*.py")) if MIGRATIONS.is_dir() else []


def _head() -> str:
    return (_git("rev-parse", "--short", "HEAD") or "unknown").strip()


def render() -> str:
    adrs, cycles, migs = _adrs(), _cycles(), _migrations()
    decided = [a for a in adrs if a[3] in ("RATIFIED", "PRODUCT OWNER APPROVED", "Accepted")]

    out = [
        "# Project History",
        "",
        "> ⚙️ **GENERATED — do not edit by hand.** Rebuild with `python3 infra/project-history.py`.",
        "> **Manual edits are lost on the next run.**",
        "",
        f"> Built at `{_head()}`. **Significant events only** — ADRs, completed repository cycles and schema changes.",
        "> **This is not a changelog.** `git log` is the complete record; **a second copy of it would be a duplicate",
        "> representation** (`CLAUDE.md` §2), and a history listing every commit teaches the reader to stop reading.",
        "",
        f"**{len(adrs)} ADRs · {len(decided)} decided · {len(cycles)} completed cycles · {len(migs)} migrations.**",
        "",
        "## Architectural decisions, in order",
        "",
        "| Date | ADR | Decision | Status |",
        "|---|---|---|---|",
    ]
    out += [f"| {d} | `{n}` | {t} | {s} |" for d, n, t, s in adrs]

    out += ["", "## Completed repository cycles", ""]
    if cycles:
        out += ["| Date | Cycle |", "|---|---|"] + [f"| {d} | {s} |" for d, s in cycles]
    else:
        out.append("*No Closeout commit is reachable from this branch.*")

    out += [
        "",
        "## Schema history",
        "",
        f"**{len(migs)} migrations.** The chain is linear by construction — Alembic's `down_revision` makes a gap a",
        "broken graph rather than a cosmetic oddity, which is why migrations are the one identifier exempt from the",
        "per-lane block rule (`CLAUDE.md` §20e).",
        "",
        f"First: `{migs[0]}`  ·  Latest: `{migs[-1]}`" if migs else "*No migrations found.*",
        "",
        "## What is deliberately absent",
        "",
        "**Product Owner rulings are not here** — most are not ADRs, and a deferral produces no ADR at all.",
        "They live in [`docs/DECISION_REGISTER.md`](docs/DECISION_REGISTER.md), which is **human-authored**, because",
        "**a ruling is a fact about a conversation and cannot be derived from the repository.**",
        "",
    ]
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="exit 1 if stale, and write nothing")
    args = ap.parse_args()
    new = render()
    if args.check:
        current = OUT.read_text() if OUT.exists() else ""
        strip = lambda s: "\n".join(l for l in s.splitlines() if not l.startswith("> Built at"))  # noqa: E731
        if strip(current) == strip(new):
            print("project-history: current.")
            return 0
        print("project-history: STALE — run `python3 infra/project-history.py`.")
        return 1
    OUT.write_text(new)
    print(f"project-history: wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

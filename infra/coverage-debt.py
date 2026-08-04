#!/usr/bin/env python3
"""**Where is the coverage debt, and is it growing?**

`pytest --cov` answers *"does the repository clear the floor?"* — one number,
at the end, and by then a lane has handed over. **This answers the question a
lane needs before it hands over:** which of *my* files are thin, and is my
slice adding debt or paying it down.

**It reads the coverage data pytest already wrote.** It runs nothing, so it is
seconds rather than minutes, and it can be run as often as it is useful.

    make coverage-debt                    # the whole repository, worst first
    make coverage-debt ARGS="timeline"    # one module — what a lane actually wants
    make coverage-debt ARGS="--new"       # files with no coverage at all

**It reports; it never decides.** The 95% floor is the gate's, and a file being
thin is not automatically a defect: some code is genuinely hard to reach and
some is not worth reaching. **What it removes is the excuse of not knowing.**
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND = REPO_ROOT / "backend"


def _coverage_json() -> dict | str:
    """The data pytest already produced, rendered as JSON — or **why not**.

    `coverage json` is used rather than parsing the text report because the
    text table truncates long paths, and a truncated path is not something a
    lane can act on.

    **Returns a reason rather than `None`, and that is the whole change.**
    Every failure here used to collapse into one message — *"No coverage
    data. cd backend && uv run pytest --cov"* — which is correct advice for
    exactly one of the causes and misleading for the rest.

    **QE hit it on 2026-08-04 and recorded the tool as broken.** It was not:
    `backend/.coverage` existed and was 1.2 MB, and the same command succeeded
    minutes later. The subprocess had failed transiently under memory pressure,
    and the tool said *run the suite* — **a five-minute answer to a problem that
    was not the suite.** A lane following that advice would have run it twice
    and learned nothing.

    **A diagnostic that misdiagnoses is worse than one that says nothing**, and
    this one was confidently wrong in the direction of wasted work.
    """
    if not (BACKEND / ".coverage").exists():
        return "no `.coverage` file — the suite has not been run with `--cov` here"
    result = subprocess.run(
        ["uv", "run", "coverage", "json", "-o", "-", "--pretty-print"],
        cwd=BACKEND,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()
        return (
            f"`coverage json` exited {result.returncode}. "
            f"**The data may be fine** — this is the reader failing, not the run.\n"
            + "\n".join(f"      {line}" for line in detail[-4:])
        )
    if not result.stdout.strip():
        return "`coverage json` produced nothing, and did not report an error"
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as broken:
        return f"`coverage json` produced output that is not JSON: {broken}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("module", nargs="?", help="restrict to paths containing this")
    parser.add_argument("--new", action="store_true", help="only files at 0%%")
    parser.add_argument("--limit", type=int, default=15)
    args = parser.parse_args()

    data = _coverage_json()
    if isinstance(data, str):
        print(f"\n  Cannot read coverage:\n\n    {data}\n")
        if data.startswith("no `.coverage`"):
            print(
                "    cd backend && uv run pytest --cov\n\n"
                "  This reads what that run leaves behind; it never runs the suite itself."
            )
        else:
            # **Do not send somebody to re-run a five-minute suite** when the
            # data is present and the reader failed. That advice cost QE two
            # runs on 2026-08-04 and produced a bug row against a working tool.
            print("  The data is present. Re-running the suite will not help; the reader failed.")
        print()
        return 1

    files = data.get("files", {})
    rows = []
    for path, entry in files.items():
        summary = entry.get("summary", {})
        statements = summary.get("num_statements", 0)
        missing = summary.get("missing_lines", 0)
        if not statements:
            continue
        if args.module and args.module not in path:
            continue
        percent = summary.get("percent_covered", 0.0)
        if args.new and percent > 0:
            continue
        if missing:
            rows.append((missing, percent, path))

    if not rows:
        scope = f" in {args.module}" if args.module else ""
        print(f"\n  No uncovered statements{scope}. Nothing to pay down.")
        return 0

    rows.sort(reverse=True)
    total = data.get("totals", {}).get("percent_covered", 0.0)

    print(f"\n  Coverage debt{' — ' + args.module if args.module else ''}"
          f"  ·  repository at {total:.2f}%\n")
    print(f"    {'MISSED':>6}  {'COVER':>6}  FILE")
    for missing, percent, path in rows[: args.limit]:
        mark = "  ←  never executed" if percent == 0 else ""
        print(f"    {missing:>6}  {percent:>5.0f}%  {path}{mark}")

    if len(rows) > args.limit:
        print(f"\n    … {len(rows) - args.limit} more. Use --limit to see them.")

    never = [r for r in rows if r[1] == 0]
    if never:
        print(
            f"\n  {len(never)} file(s) have never been executed by a test."
            "\n  Those are the ones worth looking at first — not because they are"
            "\n  cheapest, but because nothing is known about whether they work."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

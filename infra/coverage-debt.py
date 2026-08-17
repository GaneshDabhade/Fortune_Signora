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
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND = REPO_ROOT / "backend"


def _coverage_json() -> dict[str, Any] | str:
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

    ## 🔴 `--fail-under=0`, and it is the whole of [B-443](../docs/BUGS.md)

    **`coverage json` obeys `fail_under` from `pyproject.toml`.** Below the
    floor it does two things, and both are fatal here:

      · exits `2`, which this function read as *the reader failed*;
      · appends ``Coverage failure: total of N is less than fail-under=95``
        **to stdout, after the closing brace** — so even parsing it anyway
        raises `Extra data`.

    ⛔ **So the tool that names which file is short refused to run in exactly
    the situation where a lane needs it: when coverage is below the floor.**
    Above it, everything worked, which is why it was never noticed.

    **The reader is not the gate.** `--fail-under=0` restores the exit code to
    meaning *did the report generate*, which is the only question this function
    asks.
    """
    if not (BACKEND / ".coverage").exists():
        return "no `.coverage` file — the suite has not been run with `--cov` here"
    result = subprocess.run(
        ["uv", "run", "coverage", "json", "-o", "-", "--pretty-print", "--fail-under=0"],
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
    return _parse(result.stdout)


def _parse(stdout: str) -> dict[str, Any] | str:
    """The JSON object, tolerating anything `coverage` appends after it.

    **`raw_decode` rather than `loads`, and the difference is [B-443](../docs/BUGS.md).**
    `coverage json -o -` writes its `fail_under` failure to *stdout*, after the
    closing brace, so a whole-string parse raises `Extra data` on a report that
    is completely intact up to that point.

    `--fail-under=0` stops that happening. **This stops it mattering** — the
    report is the payload and a trailing message is not part of it. Belt and
    braces is warranted precisely here: this function's own docstring records a
    lane being sent to re-run a five-minute suite because the reader failed and
    said the run had.
    """
    try:
        parsed, _ = json.JSONDecoder().raw_decode(stdout.lstrip())
    except json.JSONDecodeError as broken:
        return f"`coverage json` produced output that is not JSON: {broken}"
    if not isinstance(parsed, dict):
        return f"`coverage json` produced {type(parsed).__name__}, not an object"
    return parsed


Row = tuple[int, float, str]


def ordered(rows: list[Row], *, by_coverage: bool) -> list[Row]:
    """The two questions, in the two orders that answer them.

    **Default — most missing lines first**: what will move the total. Covering
    N lines moves the number the same wherever they are, so this is the right
    ranking for a floor.

    **`by_coverage` — lowest percentage first**: what is least understood. A
    file at 78% can hold more untested *behaviour* than one at 90% with three
    times the missing lines, and on 2026-08-17 that was exactly the difference
    between the file named as the cause and the file that was
    ([B-443](../docs/BUGS.md)). Ties break on missing lines, descending.
    """
    if by_coverage:
        return sorted(rows, key=lambda r: (r[1], -r[0]))
    return sorted(rows, reverse=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("module", nargs="?", help="restrict to paths containing this")
    parser.add_argument("--new", action="store_true", help="only files at 0%%")
    parser.add_argument("--limit", type=int, default=15)
    # **Two questions, and the default answers only one** ([B-443](../docs/BUGS.md)).
    # *Which file moves the number* is missing lines; *which file is least
    # understood* is percentage. On 2026-08-17 a file at 90% was named as the
    # largest gap while the cause sat at 78% — fewer missing lines, more
    # untested behaviour, and the lane found it themselves.
    parser.add_argument("--by-coverage", action="store_true",
                        help="rank by percentage covered rather than by missing lines")
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

    rows = ordered(rows, by_coverage=args.by_coverage)
    total = data.get("totals", {}).get("percent_covered", 0.0)

    print(f"\n  Coverage debt{' — ' + args.module if args.module else ''}"
          f"  ·  repository at {total:.2f}%\n")
    # **The ordering is stated, because the two readings answer different
    # questions and the ordering was the only thing distinguishing them.**
    order = ("lowest coverage first — least understood"
             if args.by_coverage else
             "most missing lines first — moves the number most; --by-coverage for the other question")
    print(f"    {'MISSED':>6}  {'COVER':>6}  FILE        ({order})")
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

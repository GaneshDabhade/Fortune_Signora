"""The tool that names which file is short refused to run below the floor.

**[B-443](../../docs/BUGS.md).** `coverage json` obeys `fail_under` from
`pyproject.toml`. Below the floor it exits `2` *and* appends
``Coverage failure: total of N is less than fail-under=95`` **to stdout, after
the closing brace** — so `coverage-debt` bailed on the exit code, and parsing
anyway would have raised `Extra data` on a report that was completely intact.

⛔ **The tool therefore worked in every situation except the one it exists for.**
Above the floor nobody needs it; below it, it said *"cannot read coverage."*

⚠️ **It has a live cost.** On 2026-08-17 cycle 244 failed at 94.98% and the
per-file gaps were read out of `pytest --cov` by eye instead — naming a file at
90% as the largest gap when the cause was one at 78%.

**Two fixes, and the second is why these tests can exist:** `--fail-under=0` so
the exit code means *did the report generate*, and `raw_decode` so a trailing
message cannot matter even if the flag ever stops working. ⚡ **The fixture below
is the real captured stdout shape, not an invented one.**
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "coverage_debt", Path(__file__).resolve().parents[2] / "infra" / "coverage-debt.py"
)
assert _SPEC is not None and _SPEC.loader is not None
debt = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(debt)


REPORT = {
    "files": {"modules/a.py": {"summary": {"missing_lines": 3, "percent_covered": 90.0}}},
    "totals": {"percent_covered": 94.98},
}

# 🔴 **The exact shape observed**: the JSON, then the failure message, on stdout,
# with no separator. Captured from `uv run coverage json -o - --pretty-print`.
CONTAMINATED = (
    json.dumps(REPORT) + "Coverage failure: total of 0 is less than fail-under=95\n"
)


class TestTheReaderSurvivesAFailingFloor:
    def test_a_trailing_failure_message_does_not_lose_the_report(self) -> None:
        """✅ **The defect, inverted.**

        ⛔ **`json.loads` raises `Extra data` here**, and the report it is
        refusing to return is complete. **The floor failing is the reason to
        read this file, not a reason to refuse.**
        """
        parsed = debt._parse(CONTAMINATED)

        assert isinstance(parsed, dict)
        assert parsed["totals"]["percent_covered"] == 94.98

    def test_the_old_parse_genuinely_fails_on_it(self) -> None:
        """🔴 **The defect reproduced, so the test above proves something.**

        📁 **A regression test whose failure mode was never demonstrated is one
        nobody can trust** — the rule this repository learned twice today.
        """
        try:
            json.loads(CONTAMINATED)
        except json.JSONDecodeError as broken:
            assert "Extra data" in str(broken)
        else:
            raise AssertionError("the fixture no longer reproduces B-443")

    def test_genuine_garbage_is_still_reported_as_garbage(self) -> None:
        """⛔ **Tolerating a trailing message must not become tolerating anything.**

        A truncated or empty report is a real failure and must say so, or the
        tool starts inventing confidence — which is what its own docstring
        already warns about.
        """
        assert isinstance(debt._parse("Coverage failure: no data"), str)
        assert isinstance(debt._parse('{"files": '), str)

    def test_a_json_array_is_not_a_report(self) -> None:
        """A valid JSON document that is not an object answers no question."""
        assert isinstance(debt._parse("[]"), str)


class TestTwoQuestionsTwoOrderings:
    #: **The 2026-08-17 case, as data.** `claims.py` holds less understood
    #: behaviour; `handlers.py` holds more uncovered lines. Both readings are
    #: legitimate and they name different files, which is the whole point.
    ROWS = [
        (30, 90.0, "modules/provider_normalization/interface/handlers.py"),
        (8, 78.0, "modules/provider_normalization/public/claims.py"),
    ]

    def test_the_default_names_what_moves_the_total(self) -> None:
        """✅ **Covering N lines moves the number the same wherever they are.**"""
        first = debt.ordered(self.ROWS, by_coverage=False)[0]

        assert first[2].endswith("handlers.py")

    def test_by_coverage_names_what_is_least_understood(self) -> None:
        """🔴 **The file that was actually the cause, and it is second by the
        default ordering.** ⛔ **A tool offering one ranking silently was the
        thing that made this a judgement call rather than a lookup.**
        """
        first = debt.ordered(self.ROWS, by_coverage=True)[0]

        assert first[2].endswith("claims.py")

    def test_ties_break_on_missing_lines(self) -> None:
        """⚡ **Two files at the same percentage: the bigger gap first.**

        Without this the order of equal-percentage rows depends on dictionary
        iteration, which is a hidden input (`CLAUDE.md` §2).
        """
        rows = [(2, 50.0, "small.py"), (40, 50.0, "large.py")]

        assert debt.ordered(rows, by_coverage=True)[0][2] == "large.py"

    def test_neither_ordering_loses_a_row(self) -> None:
        assert len(debt.ordered(self.ROWS, by_coverage=True)) == len(self.ROWS)
        assert len(debt.ordered(self.ROWS, by_coverage=False)) == len(self.ROWS)

"""A failing gate prints its own output; a passing one prints nothing extra.

**B-140.** Cycle 90 recorded `pytest — 3928 passed` beside a red verdict. The
run that produced it had already been discarded, the identical invocation
passed on re-run, and **there was nothing left to read.** A gate that reports a
verdict without the evidence forces the next step to be *"run it again and
hope"* — which is how a flake becomes indistinguishable from a defect, and how
a real defect gets re-run until it hides.

**The tail, not the whole thing.** `pytest`'s `short test summary info` block is
the last thing it prints and the only part that names anything, so the last
lines are where the answer is. **A full transcript would drown it** and would
be the argument for writing a file instead — which the certification record
must never become: it states what a commit *satisfied*, and a transcript of one
run is not that.
"""

from __future__ import annotations

import pytest

from tests.certification.__main__ import (
    _TAIL_LINES,
    _Outcome,
    _report_gate_output,
)
from tests.certification.record import GateResult


def _gate(name: str, *, passed: bool) -> GateResult:
    return GateResult(name=name, passed=passed, detail="detail")


class TestOnlyFailingGatesSpeak:
    def test_a_failing_gate_prints_its_output(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _report_gate_output(
            [_gate("pytest", passed=False)],
            {"pytest": _Outcome(passed=False, detail="3928 passed", output="FAILED test_x")},
        )

        assert "FAILED test_x" in capsys.readouterr().out

    def test_a_passing_gate_prints_nothing(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """⛔ The half that keeps a green run readable. A gate that always
        printed its transcript would bury the six lines anybody reads."""
        _report_gate_output(
            [_gate("pytest", passed=True)],
            {"pytest": _Outcome(passed=True, detail="ok", output="a lot of text")},
        )

        assert capsys.readouterr().out == ""

    def test_only_the_failing_one_speaks_when_others_passed(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _report_gate_output(
            [_gate("mypy", passed=True), _gate("smoke", passed=False)],
            {
                "mypy": _Outcome(passed=True, detail="clean", output="MYPY NOISE"),
                "smoke": _Outcome(passed=False, detail="2 stages", output="SMOKE FAILED at 2"),
            },
        )
        out = capsys.readouterr().out

        assert "SMOKE FAILED at 2" in out
        assert "MYPY NOISE" not in out


class TestTheTailIsBoundedAndTheElisionIsStated:
    def test_a_long_output_is_cut_to_the_tail(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        output = "\n".join(f"line {i}" for i in range(_TAIL_LINES + 60))

        _report_gate_output(
            [_gate("pytest", passed=False)],
            {"pytest": _Outcome(passed=False, detail="d", output=output)},
        )
        out = capsys.readouterr().out

        assert f"line {_TAIL_LINES + 59}" in out, "the last line is what names the failure"
        assert "line 0" not in out

    def test_it_says_how_much_it_hid(self, capsys: pytest.CaptureFixture[str]) -> None:
        """⚠️ **Silent truncation is a worse instrument than no truncation.**
        A reader who cannot tell that lines were dropped reasons from a tail as
        though it were the whole run."""
        output = "\n".join(f"line {i}" for i in range(_TAIL_LINES + 7))

        _report_gate_output(
            [_gate("pytest", passed=False)],
            {"pytest": _Outcome(passed=False, detail="d", output=output)},
        )

        assert "7 elided" in capsys.readouterr().out

    def test_a_short_output_claims_no_elision(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _report_gate_output(
            [_gate("pytest", passed=False)],
            {"pytest": _Outcome(passed=False, detail="d", output="one\ntwo")},
        )

        assert "elided" not in capsys.readouterr().out


class TestAnAbsentTranscriptIsNeverSilence:
    """§2 — an absent measurement must not read like a clean one. **The same
    rule the plan-shortfall report already applies to itself.**"""

    def test_a_gate_with_no_captured_outcome_says_so(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _report_gate_output([_gate("scenario", passed=False)], {})

        assert "no output was captured" in capsys.readouterr().out

    def test_a_gate_whose_output_is_blank_says_so(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _report_gate_output(
            [_gate("pytest", passed=False)],
            {"pytest": _Outcome(passed=False, detail="d", output="   \n  ")},
        )

        assert "no output was captured" in capsys.readouterr().out

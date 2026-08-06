"""The certification run reports what the Validation Planner required and it did not.

**B-131.** `validation_plan` computes the gates a change requires; the manifest
records the gates that ran. Until this report existed nothing compared them, so
a cycle in which ten required gates never ran looked exactly like one in which
they all passed.

**These tests fix the properties that make the report worth reading**, and each
is one the first draft got wrong:

**it must not restate the gate set** · **it must distinguish "nothing to plan
for" from "could not measure"** · **it must say so when the planner is
unreachable, rather than printing nothing.**
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from tests.certification.__main__ import _load_guard, _plan_shortfall
from tests.certification.record import GateResult

REPO_ROOT = Path(__file__).resolve().parents[3]

CERTIFY_RECORDS = {"import-linter", "mypy", "pytest", "security-invariants", "smoke", "tsc"}


def _gates(names: set[str]) -> tuple[GateResult, ...]:
    return tuple(GateResult(name=n, passed=True, detail="ok") for n in sorted(names))


class TestThePlanIsComputedAndNotRestated:
    def test_the_guard_loads_and_exposes_the_planner(self) -> None:
        """**The report reads `validation_plan`; it does not own a copy of the
        gate set.** Two answers to *"what must run?"* would drift, and the
        unmaintained one would be the copy (`CLAUDE.md` §2)."""
        guard = _load_guard()
        assert guard is not None
        assert callable(guard.validation_plan)  # type: ignore[attr-defined]

    def test_a_dataclass_in_the_guard_survives_loading(self) -> None:
        """**The regression the loader exists for.** Executing the guard without
        registering it in `sys.modules` raises `AttributeError` inside
        `dataclasses`, on the decorator rather than anywhere the caller wrote —
        so a naive loader fails in a place that does not name its own cause."""
        guard = _load_guard()
        assert guard is not None
        plan = guard.validation_plan(["backend/modules/x/domain/y.py"])  # type: ignore[attr-defined]
        assert plan.gates


class TestTheShortfallIsMeasuredAgainstWhatRan:
    """**Written twice.** The first version asserted `plan.gates - set() ==
    plan.gates`, which is a tautology — a test that cannot fail is
    documentation pretending to be code (`CLAUDE.md` §2). These stub the
    planner so the subtraction is the thing under test."""

    @pytest.fixture
    def planner(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import tests.certification.__main__ as runner

        class _Plan:
            gates = ("dr", "mypy", "pytest", "state-check")
            profile = "platform"

        class _Guard:
            @staticmethod
            def validation_plan(paths: list[str]) -> Any:
                assert paths, "the planner must never be asked about an empty change"
                return _Plan()

        monkeypatch.setattr(runner, "_load_guard", lambda: _Guard())
        monkeypatch.setattr(
            runner, "_run", lambda cmd, cwd: (0, "deadbeef\n" if "rev-parse" in cmd else "a.py\n")
        )
        return None

    def test_gates_the_run_did_not_record_are_named(self, planner: None) -> None:
        missing, profile = _plan_shortfall({"mypy", "pytest"})
        assert missing == ["dr", "state-check"]
        assert profile == "platform"

    def test_recording_every_planned_gate_leaves_no_shortfall(self, planner: None) -> None:
        missing, _ = _plan_shortfall({"dr", "mypy", "pytest", "state-check"})
        assert missing == []

    def test_recording_more_than_the_plan_is_not_a_shortfall(self, planner: None) -> None:
        """**Subtraction in one direction only.** A run that executes gates the
        plan did not require is fine; reporting those as a discrepancy would
        make the report noisy on exactly the cycles that were most thorough."""
        missing, _ = _plan_shortfall({"dr", "mypy", "pytest", "state-check", "smoke"})
        assert missing == []


class TestAnAbsentMeasurementIsNeverSilence:
    """**B-125's class, and this file refuses to be its third instance.**

    A check that cannot run must say so. Reporting nothing is indistinguishable
    from reporting success, and it is the failure mode that survives longest
    because nobody sees it.
    """

    @pytest.fixture
    def guard_hidden(self, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
        import tests.certification.__main__ as runner

        monkeypatch.setattr(runner, "_load_guard", lambda: None)
        yield

    def test_it_says_not_measured_when_the_planner_cannot_be_loaded(
        self, guard_hidden: None, capsys: pytest.CaptureFixture[str]
    ) -> None:
        import tests.certification.__main__ as runner

        runner._report_plan_shortfall(_gates(CERTIFY_RECORDS))
        out = capsys.readouterr().out
        assert "NOT MEASURED" in out
        assert "could not be loaded" in out

    def test_nothing_to_plan_for_is_not_reported_as_not_measured(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """**A candidate level with `origin/main` has nothing to plan for.**
        Reporting that as `NOT MEASURED` would file an absent problem as an
        absent measurement, and the two need opposite responses."""
        import tests.certification.__main__ as runner

        monkeypatch.setattr(
            runner, "_plan_shortfall", lambda _: ([], "no change against origin/main")
        )
        runner._report_plan_shortfall(_gates(CERTIFY_RECORDS))
        out = capsys.readouterr().out
        assert "NOT MEASURED" not in out
        assert "nothing changed" in out


class TestItReportsAndRefusesNothing:
    def test_a_shortfall_is_printed_and_names_itself_as_reporting_only(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """⛔ **The report must never read as a verdict.** Enforcing it means
        adding to `REQUIRED_GATES`, which makes every prior record unsatisfied
        — a change to what certification *means* (ADR-0032), and not one a run
        may make about itself."""
        import tests.certification.__main__ as runner

        monkeypatch.setattr(runner, "_plan_shortfall", lambda _: (["dr", "state-check"],
        "platform"))
        runner._report_plan_shortfall(_gates(CERTIFY_RECORDS))
        out = capsys.readouterr().out
        assert "2 planned gate(s) NOT recorded" in out
        assert "· dr" in out and "· state-check" in out
        assert "nothing skipped, nothing refused" in out

    def test_the_report_cannot_fail_a_run(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """**It prints and returns.** A reporting step that could raise would
        turn an observation into a verdict by accident, which is the one thing
        this must not do before `REQUIRED_GATES` changes."""
        import tests.certification.__main__ as runner

        monkeypatch.setattr(runner, "_plan_shortfall", lambda _: (["dr"], "platform"))
        runner._report_plan_shortfall(_gates(CERTIFY_RECORDS))  # must not raise

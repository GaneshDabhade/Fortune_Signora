"""The attempt log answers what the manifest structurally cannot.

**The property under test is survivorship.** The manifest reported *21 runs, 0
failures, 0 reruns* from a cycle that had two failures and three attempts —
because a failed run dirties the tree, and the reset its next attempt requires
deletes the record. An aborted run never wrote one at all.

**Every case here is constructed against a temporary path.** Asserting against
the real log would pass today and pass identically with the module deleted —
the Decorative Logic `CLAUDE.md` §2 names.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from tests.certification import attempts


def _attempt(identifier: str = "aaaa11112222") -> attempts.Attempt:
    return attempts.Attempt(
        identifier=identifier,
        commit="0" * 40,
        branch="integration",
        started_at=datetime.now(UTC) - timedelta(seconds=90),
    )


class TestAnAbortLeavesEvidence:
    """The gap that made a 22-minute hang invisible to every metric."""

    def test_a_started_attempt_is_recorded_before_any_gate(self, tmp_path: Path) -> None:
        log = tmp_path / "attempts.jsonl"
        _attempt().begin(path=log)
        events = attempts.load(path=log)
        assert len(events) == 1
        assert events[0]["event"] == "started"

    def test_an_attempt_that_never_finishes_counts_as_aborted(self, tmp_path: Path) -> None:
        log = tmp_path / "attempts.jsonl"
        _attempt().begin(path=log)
        result = attempts.stability(path=log)
        assert (result.attempts, result.aborted) == (1, 1)
        assert result.certified == 0 and result.failed == 0

    def test_a_finished_attempt_is_not_aborted(self, tmp_path: Path) -> None:
        log = tmp_path / "attempts.jsonl"
        run = _attempt()
        run.begin(path=log)
        run.conclude(outcome="certified", failing_gates=(), coverage=95.5, path=log)
        assert attempts.stability(path=log).aborted == 0


class TestFailuresSurviveTheReset:
    """The circular dependency RE-01 exists to break.

    `tree_is_clean()` reads `git status --porcelain`, which ignores git-ignored
    files. A log that is not tracked cannot be reverted by the `git checkout --`
    a failed run's next attempt requires.
    """

    def test_a_failed_attempt_is_retained_with_its_failing_gates(self, tmp_path: Path) -> None:
        log = tmp_path / "attempts.jsonl"
        run = _attempt()
        run.begin(path=log)
        run.conclude(outcome="failed", failing_gates=("smoke",), coverage=95.51, path=log)
        result = attempts.stability(path=log)
        assert result.failed == 1
        assert result.gate_failures == {"smoke": 1}

    def test_repeated_attempts_at_one_commit_are_all_visible(self, tmp_path: Path) -> None:
        """This cycle: three attempts, one commit. The manifest kept one."""
        log = tmp_path / "attempts.jsonl"
        _attempt("aborted00001").begin(path=log)
        second = _attempt("failed000002")
        second.begin(path=log)
        second.conclude(outcome="failed", failing_gates=("smoke",), coverage=95.51, path=log)
        third = _attempt("passed000003")
        third.begin(path=log)
        third.conclude(outcome="certified", failing_gates=(), coverage=95.51, path=log)

        result = attempts.stability(path=log)
        assert (result.attempts, result.certified, result.failed, result.aborted) == (3, 1, 1, 1)

    def test_the_first_pass_rate_is_not_a_hundred_percent(self, tmp_path: Path) -> None:
        """**The number the manifest could not produce.** Three attempts, one
        certification — 33.3%, where the manifest reported 100%."""
        log = tmp_path / "attempts.jsonl"
        outcomes: tuple[tuple[str, attempts.Outcome | None], ...] = (
            ("a00000000001", None),
            ("a00000000002", "failed"),
            ("a00000000003", "certified"),
        )
        for identifier, outcome in outcomes:
            run = _attempt(identifier)
            run.begin(path=log)
            if outcome:
                run.conclude(outcome=outcome, failing_gates=(), coverage=95.5, path=log)
        result = attempts.stability(path=log)
        assert result.first_pass_rate == 33.3
        assert result.completion_rate == 66.7


class TestTheLogIsRobust:
    def test_a_missing_log_is_not_an_error(self, tmp_path: Path) -> None:
        result = attempts.stability(path=tmp_path / "absent.jsonl")
        assert result.attempts == 0
        assert result.first_pass_rate == 0.0

    def test_a_truncated_final_line_loses_one_event_not_the_history(
        self, tmp_path: Path
    ) -> None:
        """A process killed mid-write leaves a partial line. Refusing to read
        would lose the whole history, which is the more expensive failure."""
        log = tmp_path / "attempts.jsonl"
        run = _attempt()
        run.begin(path=log)
        with log.open("a", encoding="utf-8") as handle:
            handle.write('{"attempt": "broken", "eve')
        assert len(attempts.load(path=log)) == 1

    def test_events_are_appended_never_rewritten(self, tmp_path: Path) -> None:
        log = tmp_path / "attempts.jsonl"
        _attempt("first0000001").begin(path=log)
        _attempt("second000002").begin(path=log)
        assert [e["attempt"] for e in attempts.load(path=log)] == [
            "first0000001",
            "second000002",
        ]


class TestItRecordsFactsAndNeverInfersThem:
    """No field says *whose fault* a failure was.

    A column of guesses is worse than none. What is captured is what a human
    needs in order to make that call.
    """

    def test_the_environment_snapshot_carries_context_not_a_verdict(
        self, tmp_path: Path
    ) -> None:
        log = tmp_path / "attempts.jsonl"
        _attempt().begin(path=log)
        environment = attempts.load(path=log)[0]["environment"]
        assert set(environment) == {"containers", "ports_held", "host", "test_database"}
        assert "cause" not in environment and "blame" not in environment

    def test_an_unset_test_database_is_named_rather_than_guessed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """[B-022](../../../docs/BUGS.md): certification once measured the shared
        database and recorded it as fact."""
        monkeypatch.delenv("SIGNORA_TEST_APP_DATABASE_URL", raising=False)
        assert "unset" in attempts._database_name()

    def test_a_configured_test_database_is_recorded_by_name(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(
            "SIGNORA_TEST_APP_DATABASE_URL",
            "postgresql+asyncpg://u:p@localhost:5432/signora_lane_qe",
        )
        assert attempts._database_name() == "signora_lane_qe"

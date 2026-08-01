"""The request: what a person asked for, and how it is allowed to move.

Pure domain. No database, no session, no model — the transition rules and the
state invariants are the whole subject, and a test that needed infrastructure
to check them would be testing the wiring instead.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from modules.ai_research_engine.domain.request import (
    IN_FLIGHT,
    SETTLED,
    ResearchRequest,
    ResearchRequestError,
    ResearchRequestState,
    ResearchStatus,
    next_state,
    opening_state,
)

NOW = datetime(2026, 8, 1, 9, 0, tzinfo=UTC)


def _request() -> ResearchRequest:
    return ResearchRequest(
        id=uuid4(),
        workspace_id=uuid4(),
        entity_id=uuid4(),
        opportunity_id=uuid4(),
        requested_by=uuid4(),
        requested_at=NOW,
    )


class TestAnAskStartsWhereItStarts:
    def test_the_first_state_is_requested_at_sequence_zero(self) -> None:
        request = _request()
        state = opening_state(request)

        assert state.status is ResearchStatus.REQUESTED
        assert state.sequence == 0
        assert state.occurred_at == request.requested_at

    def test_nothing_has_been_produced_yet(self) -> None:
        state = opening_state(_request())

        assert state.task_id is None
        assert state.detail is None


class TestOnlyLegalHistoriesCanBeBuilt:
    def test_a_request_runs_before_it_completes(self) -> None:
        opening = opening_state(_request())
        running = next_state(opening, ResearchStatus.RUNNING, occurred_at=NOW)
        done = next_state(
            running, ResearchStatus.COMPLETED, occurred_at=NOW, task_id=uuid4()
        )

        assert [s.sequence for s in (opening, running, done)] == [0, 1, 2]

    def test_a_request_cannot_complete_without_running(self) -> None:
        opening = opening_state(_request())

        with pytest.raises(ResearchRequestError, match="cannot become 'completed'"):
            next_state(opening, ResearchStatus.COMPLETED, occurred_at=NOW, task_id=uuid4())

    def test_a_settled_request_never_moves_again(self) -> None:
        """**A retry is a second request, not a second attempt.**

        Advancing a settled request would overwrite the reason the first one
        ended — and the reason is the only thing a customer can act on.
        """
        running = next_state(opening_state(_request()), ResearchStatus.RUNNING, occurred_at=NOW)
        failed = next_state(
            running, ResearchStatus.FAILED, occurred_at=NOW, detail="the model refused"
        )

        with pytest.raises(ResearchRequestError, match="may become: nothing"):
            next_state(failed, ResearchStatus.RUNNING, occurred_at=NOW + timedelta(minutes=1))

    def test_a_replayed_start_is_refused(self) -> None:
        """The event bus deduplicates by `(consumer, event_id)`. A *replay*
        after a ledger reset is a different thing, and this is what stops one
        re-spending a model call."""
        running = next_state(opening_state(_request()), ResearchStatus.RUNNING, occurred_at=NOW)

        with pytest.raises(ResearchRequestError, match="'running' research request cannot"):
            next_state(running, ResearchStatus.RUNNING, occurred_at=NOW)


class TestAStateCannotContradictItself:
    def test_only_a_completed_state_names_an_artifact(self) -> None:
        running = next_state(opening_state(_request()), ResearchStatus.RUNNING, occurred_at=NOW)

        with pytest.raises(ResearchRequestError, match="names its artifact"):
            next_state(
                running,
                ResearchStatus.NOTHING_TO_RESEARCH,
                occurred_at=NOW,
                task_id=uuid4(),
            )

    def test_a_completed_state_must_name_one(self) -> None:
        running = next_state(opening_state(_request()), ResearchStatus.RUNNING, occurred_at=NOW)

        with pytest.raises(ResearchRequestError, match="names its artifact"):
            next_state(running, ResearchStatus.COMPLETED, occurred_at=NOW)

    def test_only_a_failed_state_states_why(self) -> None:
        running = next_state(opening_state(_request()), ResearchStatus.RUNNING, occurred_at=NOW)

        with pytest.raises(ResearchRequestError, match="states why"):
            next_state(
                running, ResearchStatus.NOTHING_TO_RESEARCH, occurred_at=NOW, detail="hmm"
            )

    def test_a_failed_state_must_state_why(self) -> None:
        running = next_state(opening_state(_request()), ResearchStatus.RUNNING, occurred_at=NOW)

        with pytest.raises(ResearchRequestError, match="states why"):
            next_state(running, ResearchStatus.FAILED, occurred_at=NOW)

    def test_a_blank_reason_is_no_reason(self) -> None:
        running = next_state(opening_state(_request()), ResearchStatus.RUNNING, occurred_at=NOW)

        with pytest.raises(ResearchRequestError, match="states why"):
            next_state(running, ResearchStatus.FAILED, occurred_at=NOW, detail="   ")


class TestFindingNothingIsNotFailing:
    def test_nothing_to_research_is_a_settled_status_of_its_own(self) -> None:
        """**The distinction the product depends on.** An account with two
        events from one provider has nothing to corroborate; reporting that as
        an error would have the product apologising for behaving correctly."""
        assert ResearchStatus.NOTHING_TO_RESEARCH in SETTLED
        assert ResearchStatus.NOTHING_TO_RESEARCH not in IN_FLIGHT

    def test_it_names_no_artifact_and_no_reason(self) -> None:
        running = next_state(opening_state(_request()), ResearchStatus.RUNNING, occurred_at=NOW)
        settled = next_state(running, ResearchStatus.NOTHING_TO_RESEARCH, occurred_at=NOW)

        assert settled.task_id is None
        assert settled.detail is None


class TestEveryStatusIsClassified:
    def test_in_flight_and_settled_partition_the_statuses(self) -> None:
        """**The in-flight guard reads `IN_FLIGHT`.** A status belonging to
        neither set would be silently treated as finished by the guard and
        would let a second minute-long run start."""
        assert IN_FLIGHT | SETTLED == set(ResearchStatus)
        assert not IN_FLIGHT & SETTLED


class TestASequenceCannotGoBackwards:
    def test_a_negative_sequence_is_refused(self) -> None:
        with pytest.raises(ResearchRequestError, match="sequence cannot be negative"):
            ResearchRequestState(
                request_id=uuid4(),
                workspace_id=uuid4(),
                sequence=-1,
                status=ResearchStatus.REQUESTED,
                occurred_at=NOW,
            )

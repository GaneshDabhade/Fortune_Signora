"""Recording a decision, and reading the queue it leaves behind.

**Pure application logic.** What the database refuses lives in
`test_resolution_persistence.py`; what the types refuse lives in
`test_resolution.py`. This is the layer between them: who supersedes whom, and
how a state nobody stores is derived.

**The snooze test is the load-bearing one.** *"A snoozed signal returns at the
stated time with its original evidence intact"* is an acceptance criterion, and
the only honest way to satisfy it is for nothing to happen at all — the same
resolution, read at a later moment, produces a different state. A test that
advanced the clock by writing a row would be testing a mechanism the product
does not have.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from modules.signal_engine.application.resolve import ResolveSignal, SignalNotFoundError
from modules.signal_engine.application.triage import QueueState, state_of
from modules.signal_engine.domain.resolution import (
    Actioned,
    Assigned,
    DismissalReason,
    Dismissed,
    Resolution,
    Snoozed,
)
from modules.signal_engine.domain.signal import Signal
from modules.signal_engine.infrastructure.repository import _in_chain_order
from tests.signal_engine.test_catalog_and_history import _signal
from tests.signal_engine.test_generate import FakeSignalRepository

NOW = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)
NEXT_WEEK = NOW + timedelta(days=7)
ACTOR = uuid4()


class FakeResolutions:
    """**Currency read the way the SQL repository reads it** — the superseded
    set, excluded — so a divergence between this double and the query it
    stands in for shows up as a failing test rather than as a green suite."""

    def __init__(self) -> None:
        self.rows: list[Resolution] = []

    async def record(self, resolution: Resolution) -> None:
        self.rows.append(resolution)

    async def current_for_signals(
        self, workspace_id: UUID, signal_ids: Sequence[UUID]
    ) -> dict[UUID, Resolution]:
        replaced = {row.supersedes for row in self.rows if row.supersedes is not None}
        wanted = set(signal_ids)
        return {
            row.signal_id: row
            for row in self.rows
            if row.signal_id in wanted and row.id not in replaced
        }

    async def history_for_signal(
        self, workspace_id: UUID, signal_id: UUID
    ) -> tuple[Resolution, ...]:
        """**Chain order, because the SQL repository uses chain order.**

        This double first sorted by `(recorded_at, id)`, matching what the
        repository then did — and `test_both_records_survive` failed, because
        a fixed clock makes both records share a timestamp and the tie falls to
        a random UUID. The double was right to mirror the query: mirroring it
        is what exposed the defect in both.
        """
        return _in_chain_order(tuple(r for r in self.rows if r.signal_id == signal_id))


def _stored(signals: FakeSignalRepository) -> Signal:
    signal = _signal(evidence=(uuid4(),))
    signals.rows.append(signal)
    return signal


def _resolver(signals: FakeSignalRepository, resolutions: FakeResolutions) -> ResolveSignal:
    return ResolveSignal(signals=signals, resolutions=resolutions, clock=lambda: NOW)


class TestADecisionIsRecordedAgainstARealSignal:
    async def test_the_outcome_and_its_author_are_stored(self) -> None:
        signals, resolutions = FakeSignalRepository(), FakeResolutions()
        signal = _stored(signals)

        recorded = await _resolver(signals, resolutions).execute(
            signal.workspace_id, signal.id, outcome=Actioned(), actor_id=ACTOR
        )

        assert recorded.actor_id == ACTOR
        assert recorded.recorded_at == NOW
        assert resolutions.rows == [recorded]

    async def test_a_signal_this_workspace_cannot_see_is_refused(self) -> None:
        """**404-shaped, and it does not say which of the two it is.** A signal
        that does not exist and one belonging to somebody else must answer
        identically, or the error becomes a way to ask whether a workspace
        holds a particular id."""
        signals, resolutions = FakeSignalRepository(), FakeResolutions()

        with pytest.raises(SignalNotFoundError):
            await _resolver(signals, resolutions).execute(
                uuid4(), uuid4(), outcome=Actioned(), actor_id=ACTOR
            )

        assert resolutions.rows == []

    async def test_the_signal_itself_is_never_written(self) -> None:
        """**The acceptance criterion.** A signal records what Signora
        concluded from evidence; a person disagreeing has not changed what was
        concluded."""
        signals, resolutions = FakeSignalRepository(), FakeResolutions()
        signal = _stored(signals)
        before = list(signals.rows)

        await _resolver(signals, resolutions).execute(
            signal.workspace_id,
            signal.id,
            outcome=Dismissed(reason=DismissalReason("Wrong account.")),
            actor_id=ACTOR,
        )

        assert signals.rows == before


class TestChangingYourMindNamesWhatItReplaces:
    async def test_the_second_decision_supersedes_the_first(self) -> None:
        """**Worked out by the use case, not asked of the caller.** A caller
        that had to pass the resolution it replaces would eventually pass the
        wrong one, and the queue would show two current answers for one
        signal."""
        signals, resolutions = FakeSignalRepository(), FakeResolutions()
        signal = _stored(signals)
        resolver = _resolver(signals, resolutions)

        first = await resolver.execute(
            signal.workspace_id,
            signal.id,
            outcome=Dismissed(reason=DismissalReason("Not relevant.")),
            actor_id=ACTOR,
        )
        second = await resolver.execute(
            signal.workspace_id, signal.id, outcome=Actioned(), actor_id=ACTOR
        )

        assert first.supersedes is None
        assert second.supersedes == first.id

    async def test_both_records_survive(self) -> None:
        """*"Nothing is deleted: every resolution is auditable."*"""
        signals, resolutions = FakeSignalRepository(), FakeResolutions()
        signal = _stored(signals)
        resolver = _resolver(signals, resolutions)

        await resolver.execute(
            signal.workspace_id,
            signal.id,
            outcome=Dismissed(reason=DismissalReason("Not relevant.")),
            actor_id=ACTOR,
        )
        await resolver.execute(signal.workspace_id, signal.id, outcome=Actioned(), actor_id=ACTOR)

        history = await resolutions.history_for_signal(signal.workspace_id, signal.id)
        assert len(history) == 2
        assert isinstance(history[0].outcome, Dismissed)


def _resolution(outcome: object, *, recorded_at: datetime = NOW) -> Resolution:
    return Resolution(
        id=uuid4(),
        workspace_id=uuid4(),
        signal_id=uuid4(),
        outcome=outcome,  # type: ignore[arg-type]
        actor_id=ACTOR,
        recorded_at=recorded_at,
    )


class TestTheStateIsDerivedFromTheOutcomeAndTheClock:
    def test_no_decision_is_open(self) -> None:
        """**Absent is not a decision to do nothing.** That is what `Actioned`
        is for, and conflating the two would lose the difference between work
        somebody finished and work nobody has looked at."""
        assert state_of(None, NOW) is QueueState.OPEN

    def test_acting_closes_it(self) -> None:
        assert state_of(_resolution(Actioned()), NOW) is QueueState.CLOSED

    def test_dismissing_closes_it(self) -> None:
        dismissal = Dismissed(reason=DismissalReason("Wrong account."))

        assert state_of(_resolution(dismissal), NOW) is QueueState.CLOSED

    def test_assigning_leaves_it_open(self) -> None:
        """**Routing is not resolving.** A queue that closed on assignment
        would lose every signal handed to a colleague."""
        assert state_of(_resolution(Assigned(to=uuid4())), NOW) is QueueState.OPEN


class TestASnoozedSignalReturnsWithoutAnythingRunning:
    def test_it_is_snoozed_before_the_stated_time(self) -> None:
        snoozed = _resolution(Snoozed(until=NEXT_WEEK))

        assert state_of(snoozed, NOW + timedelta(days=6)) is QueueState.SNOOZED

    def test_the_same_record_reads_as_open_once_the_time_passes(self) -> None:
        """**The acceptance criterion, and the whole design in one assertion.**
        One resolution, never rewritten, read at two moments. Nothing ran,
        nothing regenerated, and the evidence is intact because nothing touched
        it — so what returns is the signal that was postponed rather than a
        fresh reading that resembles it."""
        snoozed = _resolution(Snoozed(until=NEXT_WEEK))

        assert state_of(snoozed, NEXT_WEEK - timedelta(seconds=1)) is QueueState.SNOOZED
        assert state_of(snoozed, NEXT_WEEK) is QueueState.OPEN

    async def test_a_snooze_that_was_superseded_no_longer_speaks_for_the_signal(self) -> None:
        """**Currency first, state second.** A snooze somebody later replaced
        with a dismissal must not bring the signal back a week afterwards —
        which it would if the state were derived before asking which decision
        is actually in force."""
        signals, resolutions = FakeSignalRepository(), FakeResolutions()
        signal = _stored(signals)
        resolver = _resolver(signals, resolutions)

        await resolver.execute(
            signal.workspace_id, signal.id, outcome=Snoozed(until=NEXT_WEEK), actor_id=ACTOR
        )
        await resolver.execute(
            signal.workspace_id,
            signal.id,
            outcome=Dismissed(reason=DismissalReason("Wrong account.")),
            actor_id=ACTOR,
        )

        current = await resolutions.current_for_signals(signal.workspace_id, [signal.id])
        assert state_of(current[signal.id], NEXT_WEEK) is QueueState.CLOSED


class TestTheAuditTrailCannotRenderOutOfOrder:
    """**Found by a test, not by review.** `history_for_signal` ordered by
    `(recorded_at, id)`. Two corrections in the same instant tie on the
    timestamp and fall through to a random UUID, so a dismissal could render
    *after* the decision that replaced it — in the one surface whose entire
    purpose is showing how the queue got where it is."""

    def test_two_decisions_sharing_a_timestamp_still_order_correctly(self) -> None:
        first = _resolution(Actioned())
        second = Resolution(
            id=uuid4(),
            workspace_id=first.workspace_id,
            signal_id=first.signal_id,
            outcome=Dismissed(reason=DismissalReason("Actually, no.")),
            actor_id=ACTOR,
            recorded_at=first.recorded_at,
            supersedes=first.id,
        )

        for arrival in ((first, second), (second, first)):
            assert _in_chain_order(arrival) == (first, second), (
                "the chain is total; the order rows come back in must not matter"
            )

    def test_a_row_the_chain_cannot_explain_is_kept_rather_than_dropped(self) -> None:
        """An audit trail that silently omitted a row it could not place would
        be the one kind of defect this surface must not have."""
        rooted = _resolution(Actioned())
        orphan = Resolution(
            id=uuid4(),
            workspace_id=rooted.workspace_id,
            signal_id=rooted.signal_id,
            outcome=Actioned(),
            actor_id=ACTOR,
            recorded_at=rooted.recorded_at,
            supersedes=uuid4(),
        )

        ordered = _in_chain_order((rooted, orphan))

        assert set(ordered) == {rooted, orphan}
        assert ordered[0] == rooted

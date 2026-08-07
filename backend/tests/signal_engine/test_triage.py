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

from modules.signal_engine.application.resolve import (
    PRODUCER_MODULE,
    ResolveSignal,
    SignalNotFoundError,
)
from modules.signal_engine.application.triage import QueueState, state_of
from modules.signal_engine.domain.events import SignalResolved
from modules.signal_engine.domain.precision import RulePrecision
from modules.signal_engine.domain.resolution import (
    ACTIONED,
    ASSIGNED,
    DISMISSED,
    SNOOZED,
    Actioned,
    Assigned,
    DismissalReason,
    Dismissed,
    Outcome,
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
#: One correlation id for every decision in this file. The use case does not
#: mint one — it carries the caller's, so a decision is traceable back to the
#: request that made it (§16).
CORRELATION = uuid4()


class FakeResolutions:
    """**Currency read the way the SQL repository reads it** — the superseded
    set, excluded — so a divergence between this double and the query it
    stands in for shows up as a failing test rather than as a green suite."""

    def __init__(self) -> None:
        self.rows: list[Resolution] = []
        #: Which type each signal was, since a resolution names a signal and
        #: not its type — the SQL query gets this from a join.
        self.types: dict[UUID, str] = {}

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

    async def judgements_by_type(self, workspace_id: UUID) -> tuple[RulePrecision, ...]:
        """**The same two exclusions the SQL query makes**, for the same reason
        the methods above mirror it: a double that counts differently turns a
        divergence into a green suite.

        Superseded resolutions are excluded, and only `actioned` and
        `dismissed` are counted — `Assigned` is routing and `Snoozed` is
        deferral.
        """
        replaced = {row.supersedes for row in self.rows if row.supersedes is not None}
        by_type: dict[str, dict[str, int]] = {}
        for row in self.rows:
            if row.id in replaced:
                continue
            outcome = row.outcome
            if not isinstance(outcome, Actioned | Dismissed):
                continue
            signal_type = self.types.get(row.signal_id)
            if signal_type is None:
                continue
            tally = by_type.setdefault(signal_type, {"actioned": 0, "dismissed": 0})
            tally["actioned" if isinstance(outcome, Actioned) else "dismissed"] += 1
        return tuple(
            RulePrecision(signal_type=name, actioned=t["actioned"], dismissed=t["dismissed"])
            for name, t in sorted(by_type.items())
        )


def _stored(signals: FakeSignalRepository) -> Signal:
    signal = _signal(evidence=(uuid4(),))
    signals.rows.append(signal)
    return signal


class FakePublisher:
    """Collects what was announced, in order.

    **Not a spy on `publish` alone — it keeps the events**, because the
    assertion that matters is *what the pipeline was told*, and a call count
    would pass just as happily for an announcement carrying the wrong account.
    """

    def __init__(self) -> None:
        self.published: list[SignalResolved] = []
        self.sessions: list[object] = []
        self.correlations: list[UUID] = []

    async def publish(
        self,
        events: Sequence[SignalResolved],
        *,
        session: object,
        producer_module: str,
        correlation_id: UUID,
    ) -> None:
        self.published.extend(events)
        self.sessions.append(session)
        self.correlations.append(correlation_id)
        self.producer_module = producer_module


class NullSession:
    """The use case hands its session to the publisher and never uses it
    itself, so there is nothing here to implement."""


def _resolver(
    signals: FakeSignalRepository,
    resolutions: FakeResolutions,
    publisher: FakePublisher | None = None,
) -> ResolveSignal:
    return ResolveSignal(
        signals=signals,
        resolutions=resolutions,
        publisher=publisher or FakePublisher(),  # type: ignore[arg-type]
        session=NullSession(),  # type: ignore[arg-type]
        clock=lambda: NOW,
    )


class TestADecisionIsRecordedAgainstARealSignal:
    async def test_the_outcome_and_its_author_are_stored(self) -> None:
        signals, resolutions = FakeSignalRepository(), FakeResolutions()
        signal = _stored(signals)

        recorded = await _resolver(signals, resolutions).execute(
            signal.workspace_id,
            signal.id,
            outcome=Actioned(),
            actor_id=ACTOR,
            correlation_id=CORRELATION,
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
                uuid4(), uuid4(), outcome=Actioned(), actor_id=ACTOR, correlation_id=CORRELATION
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
            correlation_id=CORRELATION,
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
            correlation_id=CORRELATION,
        )
        second = await resolver.execute(
            signal.workspace_id,
            signal.id,
            outcome=Actioned(),
            actor_id=ACTOR,
            correlation_id=CORRELATION,
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
            correlation_id=CORRELATION,
        )
        await resolver.execute(
            signal.workspace_id,
            signal.id,
            outcome=Actioned(),
            actor_id=ACTOR,
            correlation_id=CORRELATION,
        )

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
            signal.workspace_id,
            signal.id,
            outcome=Snoozed(until=NEXT_WEEK),
            actor_id=ACTOR,
            correlation_id=CORRELATION,
        )
        await resolver.execute(
            signal.workspace_id,
            signal.id,
            outcome=Dismissed(reason=DismissalReason("Wrong account.")),
            actor_id=ACTOR,
            correlation_id=CORRELATION,
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


class TestThePipelineHearsTheDecision:
    """**TASK-432 — the one transition in this pipeline that produced no event.**

    Every other stage announces what it concluded. A *human* decision was
    recorded in a row and nowhere else, so `timeline` could not project it and
    nothing measuring whether Signora's judgement was any good had a transition
    to read. **The row recorded the state; nothing recorded the change** — and
    a change nobody published is evidence that cannot be recovered afterwards.
    """

    async def test_recording_a_decision_announces_it(self) -> None:
        signals, resolutions = FakeSignalRepository(), FakeResolutions()
        signal = _stored(signals)
        publisher = FakePublisher()

        await _resolver(signals, resolutions, publisher).execute(
            signal.workspace_id,
            signal.id,
            outcome=Actioned(),
            actor_id=ACTOR,
            correlation_id=CORRELATION,
        )

        assert len(publisher.published) == 1
        assert publisher.published[0].event_type == "signal.resolved"

    async def test_it_names_the_account_the_decision_was_about(self) -> None:
        """**Carried, not looked up.** `timeline` projects per account and does
        not depend on this module's read surface, so an event without
        `entity_id` would be one a consumer could not place."""
        signals, resolutions = FakeSignalRepository(), FakeResolutions()
        signal = _stored(signals)
        publisher = FakePublisher()

        await _resolver(signals, resolutions, publisher).execute(
            signal.workspace_id,
            signal.id,
            outcome=Actioned(),
            actor_id=ACTOR,
            correlation_id=CORRELATION,
        )

        assert publisher.published[0].entity_id == signal.entity_id

    async def test_every_outcome_travels_under_the_name_the_column_stores(self) -> None:
        """**One vocabulary, asserted against the persistence layer's own.**
        The four words used to live privately in `infrastructure/`; publishing
        them made a second copy possible, so they moved to the domain and both
        edges now read the same constants. This is the test that would fail if
        somebody re-introduced the copy and let it drift."""
        cases: list[tuple[Outcome, str]] = [
            (Actioned(), ACTIONED),
            (Assigned(to=uuid4()), ASSIGNED),
            (Snoozed(until=NEXT_WEEK), SNOOZED),
            (Dismissed(reason=DismissalReason("Wrong account.")), DISMISSED),
        ]
        for outcome, expected in cases:
            signals, resolutions = FakeSignalRepository(), FakeResolutions()
            signal = _stored(signals)
            publisher = FakePublisher()

            await _resolver(signals, resolutions, publisher).execute(
                signal.workspace_id,
                signal.id,
                outcome=outcome,
                actor_id=ACTOR,
                correlation_id=CORRELATION,
            )

            assert publisher.published[0].outcome == expected
            assert publisher.published[0].to_payload()["outcome"] == expected

    async def test_a_dismissal_never_puts_the_reason_on_the_bus(self) -> None:
        """**An event carries an identity, not a body** — the rule
        `provider.record.received` already follows. A dismissal reason is a
        sentence a customer typed about why Signora was wrong; putting it on
        the bus copies it into every subscriber's storage, and a bus cannot
        take it back."""
        signals, resolutions = FakeSignalRepository(), FakeResolutions()
        signal = _stored(signals)
        publisher = FakePublisher()

        await _resolver(signals, resolutions, publisher).execute(
            signal.workspace_id,
            signal.id,
            outcome=Dismissed(reason=DismissalReason("They already bought from us.")),
            actor_id=ACTOR,
            correlation_id=CORRELATION,
        )

        payload = publisher.published[0].to_payload()
        assert "They already bought from us." not in str(payload)
        assert payload["outcome"] == DISMISSED

    async def test_changing_your_mind_announces_what_it_replaced(self) -> None:
        """**The chain travels.** A consumer that acted on the first decision
        has to know which one it is superseding, or it counts two."""
        signals, resolutions = FakeSignalRepository(), FakeResolutions()
        signal = _stored(signals)
        publisher = FakePublisher()
        resolver = _resolver(signals, resolutions, publisher)

        first = await resolver.execute(
            signal.workspace_id,
            signal.id,
            outcome=Dismissed(reason=DismissalReason("Not relevant.")),
            actor_id=ACTOR,
            correlation_id=CORRELATION,
        )
        await resolver.execute(
            signal.workspace_id,
            signal.id,
            outcome=Actioned(),
            actor_id=ACTOR,
            correlation_id=CORRELATION,
        )

        assert publisher.published[0].supersedes is None
        assert publisher.published[1].supersedes == first.id

    async def test_it_names_the_person_rather_than_the_platform(self) -> None:
        """*Intelligence suggests; humans commit.* Every outcome is a human
        judgement, so an event without an actor could not have happened."""
        signals, resolutions = FakeSignalRepository(), FakeResolutions()
        signal = _stored(signals)
        publisher = FakePublisher()

        await _resolver(signals, resolutions, publisher).execute(
            signal.workspace_id,
            signal.id,
            outcome=Actioned(),
            actor_id=ACTOR,
            correlation_id=CORRELATION,
        )

        assert publisher.published[0].actor_id == ACTOR

    async def test_it_carries_the_callers_correlation_id(self) -> None:
        """**The caller's, never a fresh one.** A decision that could not be
        traced back to the request that made it is exactly the untraceable
        async flow §16 forbids."""
        signals, resolutions = FakeSignalRepository(), FakeResolutions()
        signal = _stored(signals)
        publisher = FakePublisher()

        await _resolver(signals, resolutions, publisher).execute(
            signal.workspace_id,
            signal.id,
            outcome=Actioned(),
            actor_id=ACTOR,
            correlation_id=CORRELATION,
        )

        assert publisher.correlations == [CORRELATION]
        assert publisher.producer_module == PRODUCER_MODULE

    async def test_it_publishes_on_the_callers_own_session(self) -> None:
        """**So the outbox row commits with the resolution or neither does.**
        Two sessions could not promise that, and a consumer hearing about a
        decision that was rolled back is the failure the outbox exists to
        prevent (§9)."""
        signals, resolutions = FakeSignalRepository(), FakeResolutions()
        signal = _stored(signals)
        publisher, session = FakePublisher(), NullSession()

        await ResolveSignal(
            signals=signals,
            resolutions=resolutions,
            publisher=publisher,  # type: ignore[arg-type]
            session=session,  # type: ignore[arg-type]
            clock=lambda: NOW,
        ).execute(
            signal.workspace_id,
            signal.id,
            outcome=Actioned(),
            actor_id=ACTOR,
            correlation_id=CORRELATION,
        )

        assert publisher.sessions == [session]

    async def test_a_signal_that_does_not_exist_announces_nothing(self) -> None:
        """**The refusal is silent on the bus.** An event for a decision that
        was never recorded would tell the pipeline something untrue, and it is
        the case a publish placed before the write would get wrong."""
        signals, resolutions = FakeSignalRepository(), FakeResolutions()
        publisher = FakePublisher()

        with pytest.raises(SignalNotFoundError):
            await _resolver(signals, resolutions, publisher).execute(
                uuid4(),
                uuid4(),
                outcome=Actioned(),
                actor_id=ACTOR,
                correlation_id=CORRELATION,
            )

        assert publisher.published == []


class TestPrecisionCountsJudgementsAndNothingElse:
    """**TASK-444.** Precision over all four outcomes would look correct,
    produce a figure for every type, and be wrong invisibly. These are the
    exclusions."""

    @staticmethod
    def _judged(fake: FakeResolutions, signal_type: str, outcome: object) -> None:
        row = _resolution(outcome)
        fake.rows.append(row)
        fake.types[row.signal_id] = signal_type

    async def test_actioned_counts_as_right_and_dismissed_as_wrong(self) -> None:
        fake = FakeResolutions()
        self._judged(fake, "hiring_surge", Actioned())
        self._judged(fake, "hiring_surge", Actioned())
        self._judged(fake, "hiring_surge", Dismissed(DismissalReason("not a real hire")))

        (rule,) = await fake.judgements_by_type(uuid4())

        assert rule.signal_type == "hiring_surge"
        assert (rule.actioned, rule.dismissed) == (2, 1)
        assert rule.ratio == pytest.approx(2 / 3)

    async def test_assigning_is_routing_and_counts_as_neither(self) -> None:
        """⛔ *"Still open. Assigning is routing, not resolving"* — the domain's
        own words. As a success it flatters every rule whose signals get passed
        around; as a failure it punishes the busiest queue."""
        fake = FakeResolutions()
        self._judged(fake, "hiring_surge", Assigned(uuid4()))

        assert await fake.judgements_by_type(uuid4()) == ()

    async def test_snoozing_is_deferral_and_counts_as_neither(self) -> None:
        """*Later* is not *wrong*. A snooze counted against a rule would punish
        it for arriving at a bad moment."""
        fake = FakeResolutions()
        self._judged(fake, "hiring_surge", Snoozed(NOW + timedelta(days=1)))

        assert await fake.judgements_by_type(uuid4()) == ()

    async def test_a_withdrawn_judgement_is_not_held_against_the_rule(self) -> None:
        """**Superseded resolutions are excluded**, the same currency rule the
        queue uses. Somebody who dismissed a signal and then changed their mind
        has withdrawn the judgement, and counting it would make this figure
        disagree with the queue a seller is looking at."""
        fake = FakeResolutions()
        first = _resolution(Dismissed(DismissalReason("wrong, I think")))
        fake.rows.append(first)
        fake.types[first.signal_id] = "hiring_surge"
        correction = Resolution(
            id=uuid4(),
            workspace_id=first.workspace_id,
            signal_id=first.signal_id,
            outcome=Actioned(),
            actor_id=ACTOR,
            recorded_at=NOW,
            supersedes=first.id,
        )
        fake.rows.append(correction)

        (rule,) = await fake.judgements_by_type(uuid4())

        assert (rule.actioned, rule.dismissed) == (1, 0)

    async def test_a_type_nobody_has_judged_is_absent_rather_than_zero(self) -> None:
        """⛔ **P-A survives as far as the caller.** A row of zeroes would let a
        screen render *0%* for a rule nobody has ruled on."""
        fake = FakeResolutions()
        self._judged(fake, "hiring_surge", Actioned())
        self._judged(fake, "funding_round", Assigned(uuid4()))

        names = [rule.signal_type for rule in await fake.judgements_by_type(uuid4())]

        assert names == ["hiring_surge"]

    async def test_each_type_is_counted_separately(self) -> None:
        fake = FakeResolutions()
        self._judged(fake, "funding_round", Actioned())
        self._judged(fake, "hiring_surge", Dismissed(DismissalReason("noise")))

        rules = {rule.signal_type: rule for rule in await fake.judgements_by_type(uuid4())}

        assert rules["funding_round"].ratio == 1.0
        assert rules["hiring_surge"].ratio == 0.0

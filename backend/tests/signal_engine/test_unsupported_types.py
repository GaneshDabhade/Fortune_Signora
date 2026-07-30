"""Hypotheses the evidence was tested against and did not support.

**Derived, never stored** (ADR-0030 Decision 7, ruled 2026-07-30). Recording
every non-result would write a row per (entity, type) on every run — a large
table describing mostly nothing — so the question is answered on demand from
evidence this module already holds, using the rules it already owns.

The correction behind this file is worth remembering. The ADR originally
claimed the Signal Engine *already recorded* rejected hypotheses. It did not:
`ground()` returned an empty tuple and the fact was discarded. T122 found
that, and this is the capability being built rather than assumed.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

from modules.business_event_engine.public import BusinessEvent, BusinessEventType
from modules.signal_engine.application.queries import SignalQueries, UnsupportedReading
from modules.signal_engine.domain.catalog import Relevance, SignalType
from modules.signal_engine.domain.profile import ProfileEntry, SignalProfile
from modules.signal_engine.domain.signal import Signal
from modules.signal_engine.infrastructure.catalog_loader import load_catalog
from tests.signal_engine.test_generate import (
    FakeBusinessEvents,
    FakeProfileRepository,
    FakeSignalRepository,
)

WORKSPACE = UUID(int=42)
ENTITY = UUID(int=7)
NOW = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)

QUERIES_SOURCE = (
    Path(__file__).resolve().parents[2]
    / "modules"
    / "signal_engine"
    / "application"
    / "queries.py"
)


async def _readings(
    *events: BusinessEvent, profile: SignalProfile | None = None
) -> tuple[UnsupportedReading, ...]:
    queries = SignalQueries(
        repository=FakeSignalRepository(),
        profiles=FakeProfileRepository(profile),
        business_events=FakeBusinessEvents(events),  # type: ignore[arg-type]
        catalog=load_catalog(),
    )
    return await queries.unsupported_types(WORKSPACE, ENTITY, now=NOW)


class TestNothingRelevantHappened:
    async def test_a_type_with_no_contributing_evidence_is_reported(self) -> None:
        found = {r.signal_type for r in await _readings()}

        assert SignalType.DISPLACEMENT_OPPORTUNITY in found

    async def test_the_reason_names_the_evidence_that_would_have_counted(self) -> None:
        """A customer asking *"why didn't you consider X?"* is entitled to
        know what X needs, not merely that it was declined."""
        displacement = next(
            r
            for r in await _readings()
            if r.signal_type is SignalType.DISPLACEMENT_OPPORTUNITY
        )

        assert "nothing of the kind" in displacement.reason
        assert BusinessEventType.TECHNOLOGY_RETIRED.value in displacement.reason


class TestNotEnoughDistinctEvidence:
    async def test_a_composite_short_of_its_minimum_reports_the_counts(self) -> None:
        """Three hiring surges are one phenomenon reported repeatedly, not
        three grounds — so a composite type sees one distinct kind, and the
        reason must say so rather than implying nothing happened."""
        expansion = next(
            r
            for r in await _readings(
                _event(BusinessEventType.HIRING_SURGE, days_ago=5),
                _event(BusinessEventType.HIRING_SURGE, days_ago=4),
                _event(BusinessEventType.HIRING_SURGE, days_ago=3),
            )
            if r.signal_type is SignalType.EXPANSION_OPPORTUNITY
        )

        assert "only 1 of the 2 distinct kinds" in expansion.reason
        assert "days of each other" in expansion.reason


class TestWhatIsDeliberatelyNotReported:
    async def test_a_supported_type_is_not_listed_as_unsupported(self) -> None:
        """The positive control. A query returning every type would satisfy
        every other test here while saying nothing."""
        found = {
            r.signal_type
            for r in await _readings(
                _event(BusinessEventType.TECHNOLOGY_RETIRED, days_ago=3)
            )
        }

        assert SignalType.DISPLACEMENT_OPPORTUNITY not in found

    async def test_a_live_signal_is_not_reported_even_once_its_grounds_have_aged(self) -> None:
        """**The case the `produced` check exists for**, and the only one that
        distinguishes it from `ground()`.

        A signal generated earlier stays live for its relevance window even
        after the events behind it fall outside the *grounding* window. Asked
        again today, `ground()` declines — but the hypothesis is still held,
        and reporting it as "considered and rejected" would contradict the
        signal the customer can see on the same screen.

        Added after a mutation survived: removing the check changed nothing,
        because every earlier test ran against an empty signal repository.
        """
        repository = FakeSignalRepository()
        repository.rows.append(_live_signal(SignalType.DISPLACEMENT_OPPORTUNITY))
        queries = SignalQueries(
            repository=repository,
            profiles=FakeProfileRepository(None),
            # No events at all, so ground() declines every type.
            business_events=FakeBusinessEvents(()),  # type: ignore[arg-type]
            catalog=load_catalog(),
        )

        readings = await queries.unsupported_types(WORKSPACE, ENTITY, now=NOW)

        assert SignalType.DISPLACEMENT_OPPORTUNITY not in {r.signal_type for r in readings}
        assert readings, "the other types should still be reported"

    async def test_a_type_the_workspace_switched_off_is_not_reported(self) -> None:
        """*"Your workspace does not track this"* and *"the evidence does not
        support this"* are different statements. Conflating them would tell a
        customer their own configuration was a finding about their account."""
        silenced = SignalProfile(
            id=uuid4(),
            workspace_id=WORKSPACE,
            version=2,
            entries=(
                ProfileEntry(signal_type=SignalType.CONTRACTION_RISK, relevance=Relevance.IGNORED),
            ),
            created_at=NOW,
            created_by=uuid4(),
        )
        found = {r.signal_type for r in await _readings(profile=silenced)}

        assert SignalType.CONTRACTION_RISK not in found


class TestTheAnswerIsStableAndReusesTheRules:
    async def test_readings_are_returned_in_a_stable_order(self) -> None:
        """An artifact recording alternatives must not reorder them between
        two runs over identical evidence, or two Decision Packages would
        differ for a reason nobody can explain."""
        first = [r.signal_type for r in await _readings()]
        second = [r.signal_type for r in await _readings()]

        assert first == second
        assert first == sorted(first, key=lambda t: t.value)

    def test_no_grounding_rule_is_re_implemented(self) -> None:
        """Driven by `ground()`, the same function that decides whether a
        signal is generated at all. A second copy of that logic would diverge
        from the first, and the two would disagree about one set of
        evidence."""
        source = QUERIES_SOURCE.read_text()

        assert "if ground(events, definition, entry):" in source
        assert "detection_strategy" not in source, (
            "queries.py branches on detection strategy, which means it has begun "
            "re-implementing the grounding rules rather than calling them"
        )


def _event(type_key: BusinessEventType, *, days_ago: int) -> BusinessEvent:
    from modules.business_event_engine.public import BusinessDomain

    when = NOW - timedelta(days=days_ago)
    return BusinessEvent(
        id=uuid4(),
        workspace_id=WORKSPACE,
        entity_id=ENTITY,
        type_key=type_key,
        domain=BusinessDomain.WORKFORCE,
        occurred_at=when,
        window_start=when,
        window_end=when,
        detected_at=when,
        summary="Something happened",
        facts={},
        evidence_observation_ids=(uuid4(),),
        corroborating_providers=("coresignal",),
        taxonomy_version=1,
    )


def _live_signal(signal_type: SignalType) -> Signal:
    """A hypothesis still within its relevance window."""
    return Signal(
        id=uuid4(),
        workspace_id=WORKSPACE,
        entity_id=ENTITY,
        signal_type=signal_type,
        relevance=Relevance.PRIMARY,
        occurred_at=NOW - timedelta(days=300),
        window_start=NOW - timedelta(days=300),
        window_end=NOW - timedelta(days=300),
        generated_at=NOW - timedelta(days=300),
        relevant_until=NOW + timedelta(days=30),
        rationale="Generated when the evidence was still within its window.",
        contributing_event_ids=(uuid4(),),
        contributing_event_types=(BusinessEventType.TECHNOLOGY_RETIRED,),
    )

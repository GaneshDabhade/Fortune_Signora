"""The `DetectBusinessEvents` use case, tested against fakes.

The properties under test are the ones that are not any single rule's job:
provider agreement is counted rather than combined, one business fact is
one event, and a phenomenon that extends supersedes rather than
duplicates.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest

from modules.business_event_engine.application.detect import (
    DetectBusinessEvents,
    DetectBusinessEventsInput,
)
from modules.business_event_engine.domain.business_event import BusinessEvent
from modules.business_event_engine.domain.taxonomy import BusinessEventType, TaxonomyError
from modules.business_event_engine.infrastructure.taxonomy_loader import load_taxonomy
from modules.observation_engine.public import (
    Observation,
    ObservationDirection,
    ObservationKind,
)
from modules.provider_normalization.public import ClaimAttribute
from tests.knowledge_graph.fakes import RecordingPublisher

WORKSPACE = uuid4()
ENTITY = uuid4()
START = datetime(2026, 1, 1, tzinfo=UTC)
NOW = datetime(2026, 6, 1, tzinfo=UTC)


class FakeBusinessEventRepository:
    def __init__(self) -> None:
        self.rows: list[BusinessEvent] = []

    def _replaced(self) -> set[UUID]:
        return {e.supersedes for e in self.rows if e.supersedes is not None}

    async def current_for_entity(
        self, workspace_id: UUID, entity_id: UUID, *, type_key: BusinessEventType
    ) -> tuple[BusinessEvent, ...]:
        replaced = self._replaced()
        return tuple(
            e
            for e in self.rows
            if e.entity_id == entity_id and e.type_key is type_key and e.id not in replaced
        )

    async def record(self, events: tuple[BusinessEvent, ...]) -> int:
        known = {e.id for e in self.rows}
        fresh = [e for e in events if e.id not in known]
        self.rows.extend(fresh)
        return len(fresh)

    async def for_entity(
        self,
        workspace_id: UUID,
        entity_id: UUID,
        *,
        type_key: BusinessEventType | None = None,
        since: datetime | None = None,
    ) -> tuple[BusinessEvent, ...]:
        return tuple(e for e in self.rows if e.entity_id == entity_id)

    async def by_id(self, workspace_id: UUID, event_id: UUID) -> BusinessEvent | None:
        return next((e for e in self.rows if e.id == event_id), None)

    async def citing_observations(
        self, workspace_id: UUID, observation_ids: Sequence[UUID]
    ) -> tuple[BusinessEvent, ...]:
        wanted = set(observation_ids)
        return tuple(e for e in self.rows if wanted & set(e.evidence_observation_ids))


class FakeObservations:
    def __init__(self, observations: Sequence[Observation]) -> None:
        self._observations = tuple(observations)

    async def observations(
        self,
        workspace_id: UUID,
        entity_id: UUID,
        *,
        attribute: ClaimAttribute | None = None,
        since: datetime | None = None,
    ) -> tuple[Observation, ...]:
        return self._observations


def _headcount(
    previous: int, current: int, from_day: int, to_day: int, *, provider: str
) -> Observation:
    return Observation(
        id=uuid4(),
        workspace_id=WORKSPACE,
        entity_id=ENTITY,
        provider=provider,
        attribute=ClaimAttribute.EMPLOYEE_COUNT,
        kind=ObservationKind.VALUE_CHANGED,
        previous_value=previous,
        current_value=current,
        direction=ObservationDirection.INCREASED,
        magnitude=float(current - previous),
        observed_at=START + timedelta(days=to_day),
        previous_observed_at=START + timedelta(days=from_day),
        recorded_at=START,
        evidence_claim_ids=(uuid4(),),
    )


def _use_case(
    repository: FakeBusinessEventRepository, observations: Sequence[Observation]
) -> tuple[DetectBusinessEvents, RecordingPublisher]:
    publisher = RecordingPublisher()
    return (
        DetectBusinessEvents(
            repository=repository,
            observations=FakeObservations(observations),  # type: ignore[arg-type]
            taxonomy=load_taxonomy(),
            publisher=publisher,
            session=None,  # type: ignore[arg-type]
            clock=lambda: NOW,
        ),
        publisher,
    )


async def _run(
    repository: FakeBusinessEventRepository, observations: Sequence[Observation]
) -> RecordingPublisher:
    use_case, publisher = _use_case(repository, observations)
    await use_case.execute(
        DetectBusinessEventsInput(workspace_id=WORKSPACE, entity_id=ENTITY),
        correlation_id=uuid4(),
    )
    return publisher


class TestDetection:
    async def test_a_surge_is_detected_and_announced(self) -> None:
        repository = FakeBusinessEventRepository()

        publisher = await _run(repository, [_headcount(100, 140, 0, 30, provider="coresignal")])

        assert len(repository.rows) == 1
        assert repository.rows[0].type_key is BusinessEventType.HIRING_SURGE
        assert publisher.types() == ["business_event.detected"]

    async def test_re_running_over_the_same_evidence_detects_nothing(self) -> None:
        """Identity is derived from the evidence, so a redelivered event is a
        no-op without any handler-level guard."""
        repository = FakeBusinessEventRepository()
        observations = [_headcount(100, 140, 0, 30, provider="coresignal")]

        await _run(repository, observations)
        publisher = await _run(repository, observations)

        assert len(repository.rows) == 1
        assert publisher.events == []

    async def test_an_entity_with_no_observations_detects_nothing(self) -> None:
        repository = FakeBusinessEventRepository()

        publisher = await _run(repository, [])

        assert repository.rows == []
        assert publisher.events == []

    async def test_every_event_records_the_taxonomy_that_detected_it(self) -> None:
        """Without it a replay under a later version is indistinguishable
        from what came before rather than comparable to it."""
        repository = FakeBusinessEventRepository()

        await _run(repository, [_headcount(100, 140, 0, 30, provider="coresignal")])

        assert repository.rows[0].taxonomy_version == load_taxonomy().version


class TestProviderAgreement:
    async def test_two_providers_seeing_one_surge_produce_one_event(self) -> None:
        """One business fact is one event. Timeline shows what happened to
        the company, not what each vendor reported."""
        repository = FakeBusinessEventRepository()

        await _run(
            repository,
            [
                _headcount(100, 140, 0, 30, provider="coresignal"),
                _headcount(100, 140, 0, 30, provider="apollo"),
            ],
        )

        assert len(repository.rows) == 1

    async def test_agreement_is_recorded_as_evidence_not_as_a_weight(self) -> None:
        repository = FakeBusinessEventRepository()

        await _run(
            repository,
            [
                _headcount(100, 140, 0, 30, provider="coresignal"),
                _headcount(100, 140, 0, 30, provider="apollo"),
            ],
        )

        event = repository.rows[0]
        assert event.corroborating_providers == ("apollo", "coresignal")
        assert event.is_corroborated is True
        assert "confidence" not in event.facts
        assert "score" not in event.facts

    async def test_providers_disagreeing_produce_separate_conclusions(self) -> None:
        """Values are never combined. One provider seeing growth and another
        seeing a different magnitude are two conclusions, and neither is
        averaged into a synthetic truth."""
        repository = FakeBusinessEventRepository()

        await _run(
            repository,
            [
                _headcount(100, 140, 0, 30, provider="coresignal"),
                _headcount(200, 260, 0, 30, provider="apollo"),
            ],
        )

        assert len(repository.rows) == 2
        assert all(len(e.corroborating_providers) == 1 for e in repository.rows)

    async def test_one_provider_below_the_threshold_does_not_drag_another_over_it(self) -> None:
        """The rule sees one provider's series at a time, so a quiet provider
        cannot dilute or amplify a loud one."""
        repository = FakeBusinessEventRepository()

        await _run(
            repository,
            [
                _headcount(100, 140, 0, 30, provider="coresignal"),
                _headcount(1000, 1005, 0, 30, provider="apollo"),
            ],
        )

        assert len(repository.rows) == 1
        assert repository.rows[0].corroborating_providers == ("coresignal",)


class TestDurableHistory:
    async def test_an_extended_phenomenon_supersedes_rather_than_duplicates(self) -> None:
        repository = FakeBusinessEventRepository()
        first = _headcount(100, 140, 0, 30, provider="coresignal")

        await _run(repository, [first])
        earlier = repository.rows[0]

        second = _headcount(140, 200, 30, 60, provider="coresignal")
        publisher = await _run(repository, [first, second])

        assert len(repository.rows) == 2
        latest = repository.rows[-1]
        assert latest.supersedes == earlier.id
        assert "business_event.superseded" in publisher.types()

    async def test_the_earlier_event_stays_readable(self) -> None:
        """*"What did we believe about this surge, and when?"* — the question
        durable business history exists to answer."""
        repository = FakeBusinessEventRepository()
        first = _headcount(100, 140, 0, 30, provider="coresignal")
        await _run(repository, [first])
        earlier = repository.rows[0]

        await _run(repository, [first, _headcount(140, 200, 30, 60, provider="coresignal")])

        assert earlier in repository.rows

    async def test_a_superseded_event_is_no_longer_current(self) -> None:
        """Otherwise the next detection would supersede it again and the
        chain would grow without end."""
        repository = FakeBusinessEventRepository()
        first = _headcount(100, 140, 0, 30, provider="coresignal")
        second = _headcount(140, 200, 30, 60, provider="coresignal")

        await _run(repository, [first])
        await _run(repository, [first, second])

        current = await repository.current_for_entity(
            WORKSPACE, ENTITY, type_key=BusinessEventType.HIRING_SURGE
        )

        assert len(current) == 1
        assert current[0].supersedes is not None


class TestTaxonomyAndRulesMustAgree:
    async def test_a_rule_detecting_an_undeclared_type_fails_at_construction(self) -> None:
        """A rule nobody declared is a business threshold nobody reviewed —
        and it fails when the engine is built, not on the first detection."""

        class Rogue:
            detects = BusinessEventType.HIRING_SURGE

            def evaluate(self, series: Any, parameters: Any) -> tuple[Any, ...]:
                return ()

        with pytest.raises(TaxonomyError, match="no rule to detect them"):
            DetectBusinessEvents(
                repository=FakeBusinessEventRepository(),
                observations=FakeObservations([]),  # type: ignore[arg-type]
                taxonomy=load_taxonomy(),
                publisher=RecordingPublisher(),
                session=None,  # type: ignore[arg-type]
                rules=(Rogue(),),
            )

    def test_reading_an_undeclared_parameter_fails_loudly(self) -> None:
        parameters = load_taxonomy().parameters(BusinessEventType.HIRING_SURGE)

        with pytest.raises(TaxonomyError, match="undeclared parameter"):
            parameters.number("minimum_vibes")

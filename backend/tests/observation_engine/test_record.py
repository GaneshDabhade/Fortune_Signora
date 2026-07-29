"""The `RecordObservations` use case, tested against fakes.

No database, no event bus, no graph. If any of these needed one, the Clean
Architecture boundary would have leaked — so the absence of infrastructure
here is itself part of what is being asserted.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from modules.knowledge_graph.public import ClaimSet, Entity, EntityEvidence, EntityKind
from modules.observation_engine.application.record import (
    RecordObservations,
    RecordObservationsInput,
)
from modules.observation_engine.domain.observation import Observation, ObservationDirection
from modules.provider_normalization.public import ClaimAttribute, ClaimView
from tests.knowledge_graph.fakes import RecordingPublisher

WORKSPACE = uuid4()
NOW = datetime(2026, 4, 1, tzinfo=UTC)


class FakeObservationRepository:
    def __init__(self) -> None:
        self.rows: list[Observation] = []

    def _refined_ids(self) -> set[UUID]:
        return {o.supersedes for o in self.rows if o.supersedes is not None}

    async def current_for_series(
        self, workspace_id: UUID, *, entity_id: UUID, provider: str, attribute: ClaimAttribute
    ) -> tuple[Observation, ...]:
        refined = self._refined_ids()
        return tuple(
            o
            for o in self.rows
            if o.entity_id == entity_id
            and o.provider == provider
            and o.attribute is attribute
            and o.id not in refined
        )

    async def record(self, observations: tuple[Observation, ...]) -> int:
        known = {o.id for o in self.rows}
        fresh = [o for o in observations if o.id not in known]
        self.rows.extend(fresh)
        return len(fresh)

    async def for_entity(
        self,
        workspace_id: UUID,
        entity_id: UUID,
        *,
        attribute: ClaimAttribute | None = None,
        since: datetime | None = None,
    ) -> tuple[Observation, ...]:
        return tuple(
            o
            for o in self.rows
            if o.entity_id == entity_id and (attribute is None or o.attribute is attribute)
        )

    async def by_id(self, workspace_id: UUID, observation_id: UUID) -> Observation | None:
        return next((o for o in self.rows if o.id == observation_id), None)


class FakeGraph:
    """Stands in for the Knowledge Graph's public query surface."""

    def __init__(self, entity_id: UUID, claims: Sequence[ClaimView]) -> None:
        self.entity_id = entity_id
        self.claims = list(claims)

    async def entity_evidence(self, workspace_id: UUID, entity_id: UUID) -> EntityEvidence | None:
        if entity_id != self.entity_id:
            return None
        return EntityEvidence(
            entity=Entity.create(workspace_id=workspace_id, kind=EntityKind.COMPANY, now=NOW),
            bindings=(),
            claims=tuple(self.claims),
        )

    async def claim_set(
        self, workspace_id: UUID, entity_id: UUID, attribute: ClaimAttribute
    ) -> ClaimSet:
        return ClaimSet(
            entity_id=entity_id,
            attribute=attribute,
            claims=tuple(c for c in self.claims if c.attribute is attribute),
        )


def _claim(
    value: Any,
    day: int,
    *,
    provider: str = "coresignal",
    attribute: ClaimAttribute = ClaimAttribute.EMPLOYEE_COUNT,
) -> ClaimView:
    return ClaimView(
        id=uuid4(),
        provider=provider,
        attribute=attribute,
        value=value,
        observed_at=datetime(2026, 1, day, tzinfo=UTC),
        subject_external_id="acme-corp",
        subject_domain="acme.example",
        subject_legal_name="Acme Corp",
        payload_provenance="DEVELOPMENT_FIXTURE",
    )


def _use_case(
    repository: FakeObservationRepository, graph: FakeGraph
) -> tuple[RecordObservations, RecordingPublisher]:
    publisher = RecordingPublisher()
    return (
        RecordObservations(
            repository=repository,
            graph=graph,  # type: ignore[arg-type]
            publisher=publisher,
            session=None,  # type: ignore[arg-type]
            clock=lambda: NOW,
        ),
        publisher,
    )


async def _run(
    repository: FakeObservationRepository, entity_id: UUID, claims: Sequence[ClaimView]
) -> RecordingPublisher:
    use_case, publisher = _use_case(repository, FakeGraph(entity_id, claims))
    await use_case.execute(
        RecordObservationsInput(
            workspace_id=WORKSPACE,
            entity_id=entity_id,
            new_claim_ids=frozenset(c.id for c in claims),
        ),
        correlation_id=uuid4(),
    )
    return publisher


class TestRecording:
    async def test_a_change_is_recorded_and_announced(self) -> None:
        repository = FakeObservationRepository()
        entity = uuid4()

        publisher = await _run(repository, entity, [_claim(120, 1), _claim(145, 15)])

        assert len(repository.rows) == 1
        assert publisher.types() == ["observation.recorded"]

    async def test_re_running_over_the_same_evidence_records_nothing(self) -> None:
        """Deduplication is a property of the derived identity, so a
        redelivered event is a no-op without any handler-level guard."""
        repository = FakeObservationRepository()
        entity = uuid4()
        claims = [_claim(120, 1), _claim(145, 15)]

        await _run(repository, entity, claims)
        publisher = await _run(repository, entity, claims)

        assert len(repository.rows) == 1
        assert publisher.events == []

    async def test_an_unknown_entity_records_nothing(self) -> None:
        """A record from another workspace is invisible under RLS, and
        retrying will not make it appear."""
        repository = FakeObservationRepository()

        publisher = await _run(repository, uuid4(), [])

        assert repository.rows == []
        assert publisher.events == []


class TestDisagreementIsNotChange:
    async def test_two_providers_disagreeing_produce_no_observation(self) -> None:
        """The central rejection. Merging the two series would say Acme grew
        25 in a day; nothing grew, the sources disagree."""
        repository = FakeObservationRepository()
        entity = uuid4()

        await _run(
            repository,
            entity,
            [_claim(120, 1, provider="apollo"), _claim(145, 2, provider="coresignal")],
        )

        assert repository.rows == [], (
            "a difference between two providers is evidence about the providers, "
            "not movement in the world"
        )

    async def test_each_provider_keeps_its_own_series(self) -> None:
        repository = FakeObservationRepository()
        entity = uuid4()

        await _run(
            repository,
            entity,
            [
                _claim(120, 1, provider="apollo"),
                _claim(130, 15, provider="apollo"),
                _claim(145, 2, provider="coresignal"),
                _claim(160, 16, provider="coresignal"),
            ],
        )

        assert sorted(o.provider for o in repository.rows) == ["apollo", "coresignal"]
        assert all(o.direction is ObservationDirection.INCREASED for o in repository.rows)


class TestRefinement:
    async def test_a_late_claim_refines_rather_than_rewrites(self) -> None:
        repository = FakeObservationRepository()
        entity = uuid4()
        first, last = _claim(120, 1), _claim(145, 15)

        await _run(repository, entity, [first, last])
        coarse = repository.rows[0]

        middle = _claim(130, 8)
        publisher = await _run(repository, entity, [first, middle, last])

        assert coarse in repository.rows, "the coarser observation must stay readable"
        refined = [o for o in repository.rows if o.supersedes == coarse.id]
        assert len(refined) == 2, "both finer observations name the one they replace"
        assert "observation.superseded" in publisher.types()

    async def test_the_refined_observation_is_no_longer_current(self) -> None:
        """Otherwise the next derivation would see it as stale again and the
        growth would be counted three times."""
        repository = FakeObservationRepository()
        entity = uuid4()
        first, middle, last = _claim(120, 1), _claim(130, 8), _claim(145, 15)

        await _run(repository, entity, [first, last])
        await _run(repository, entity, [first, middle, last])

        current = await repository.current_for_series(
            WORKSPACE,
            entity_id=entity,
            provider="coresignal",
            attribute=ClaimAttribute.EMPLOYEE_COUNT,
        )

        assert len(current) == 2
        assert all(o.supersedes is not None for o in current)


class TestSeriesSelection:
    async def test_only_series_touched_by_new_evidence_are_examined(self) -> None:
        """Every other series is unchanged by construction. Re-deriving them
        would be work with a known-empty result — the difference between an
        engine that scales with new evidence and one that scales with total
        evidence."""
        repository = FakeObservationRepository()
        entity = uuid4()
        untouched = [
            _claim("software", 1, attribute=ClaimAttribute.INDUSTRY),
            _claim("fintech", 15, attribute=ClaimAttribute.INDUSTRY),
        ]
        touched = [_claim(120, 1), _claim(145, 15)]

        use_case, _ = _use_case(repository, FakeGraph(entity, untouched + touched))
        result = await use_case.execute(
            RecordObservationsInput(
                workspace_id=WORKSPACE,
                entity_id=entity,
                new_claim_ids=frozenset(c.id for c in touched),
            ),
            correlation_id=uuid4(),
        )

        assert result.series_examined == 1
        assert [o.attribute for o in repository.rows] == [ClaimAttribute.EMPLOYEE_COUNT]

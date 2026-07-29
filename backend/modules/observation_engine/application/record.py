"""Record the observations a batch of new evidence implies.

**The Observation Engine detects change. It does not determine
significance.** (Permanent invariant, ratified 2026-07-29.) There is no
threshold in this module, and a constant appearing in it is a review
failure: whether a move matters is a question about commercial context, and
the Business Event Engine owns the curated taxonomy where such a rule can be
stated and argued about.

The unit of work is one `(entity, provider, attribute)` **series**, always
re-derived in full. Deriving only the tail would be faster and wrong: a
claim arriving out of order changes what the earlier claims imply, and
partial derivation would leave the coarser observation standing alongside
the finer ones, double-counting the change.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from modules.knowledge_graph.public import GraphQueries
from modules.observation_engine.application.ports import ObservationRepository
from modules.observation_engine.domain.derivation import derive, refinements
from modules.observation_engine.domain.events import ObservationRecorded, ObservationSuperseded
from modules.observation_engine.domain.observation import Observation
from modules.provider_normalization.public import ClaimAttribute, ClaimView
from signora_platform.event_bus import EventPublisher
from signora_platform.observability import get_logger

logger = get_logger(__name__)

PRODUCER_MODULE = "observation_engine"


@dataclass(frozen=True, slots=True)
class RecordObservationsInput:
    workspace_id: UUID
    entity_id: UUID
    #: The claims just attached to this entity. Only the series they touch
    #: are re-derived — every other series is unchanged by construction, and
    #: re-deriving it would be work with a known-empty result.
    new_claim_ids: frozenset[UUID]


@dataclass(frozen=True, slots=True)
class RecordObservationsResult:
    recorded: int
    refined: int
    series_examined: int


class RecordObservations:
    def __init__(
        self,
        *,
        repository: ObservationRepository,
        graph: GraphQueries,
        publisher: EventPublisher,
        session: AsyncSession,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._repository = repository
        # Claims are read through the Knowledge Graph's public surface, not
        # Provider Normalization's: this module reasons over evidence that
        # has already been attached to an identity, and cannot observe
        # something it cannot attribute.
        self._graph = graph
        self._publisher = publisher
        self._session = session
        self._clock = clock

    async def execute(
        self,
        request: RecordObservationsInput,
        *,
        correlation_id: UUID,
        causation_id: UUID | None = None,
    ) -> RecordObservationsResult:
        evidence = await self._graph.entity_evidence(request.workspace_id, request.entity_id)
        if evidence is None:
            # The entity is not visible in this tenant scope. Logged rather
            # than raised — retrying will not make another workspace's row
            # appear.
            logger.warning(
                "entity not visible for observation",
                extra={"entity_id": str(request.entity_id)},
            )
            return RecordObservationsResult(recorded=0, refined=0, series_examined=0)

        now = self._clock()
        events: list[ObservationRecorded | ObservationSuperseded] = []
        recorded = refined = 0

        touched = _touched_series(evidence.claims, request.new_claim_ids)
        for provider, attribute in touched:
            series = [
                claim
                for claim in evidence.claims
                if claim.provider == provider and claim.attribute is attribute
            ]
            outcome = await self._record_series(
                request.workspace_id,
                request.entity_id,
                provider=provider,
                attribute=attribute,
                series=series,
                now=now,
                causation_id=causation_id,
                events=events,
            )
            recorded += outcome[0]
            refined += outcome[1]

        if events:
            # See the note in provider_normalization's handler: the platform's
            # PublishableEvent Protocol declares settable members, which frozen
            # domain events cannot satisfy. Raised as a finding, not fixed here.
            await self._publisher.publish(
                events,  # type: ignore[arg-type]
                session=self._session,
                producer_module=PRODUCER_MODULE,
                correlation_id=correlation_id,
            )

        logger.info(
            "observations recorded",
            extra={
                "entity_id": str(request.entity_id),
                "recorded": recorded,
                "refined": refined,
            },
        )
        return RecordObservationsResult(
            recorded=recorded, refined=refined, series_examined=len(touched)
        )

    async def _record_series(
        self,
        workspace_id: UUID,
        entity_id: UUID,
        *,
        provider: str,
        attribute: ClaimAttribute,
        series: list[ClaimView],
        now: datetime,
        causation_id: UUID | None,
        events: list[ObservationRecorded | ObservationSuperseded],
    ) -> tuple[int, int]:
        derived = derive(
            series,
            workspace_id=workspace_id,
            entity_id=entity_id,
            provider=provider,
            attribute=attribute,
            recorded_at=now,
        )
        existing = await self._repository.current_for_series(
            workspace_id, entity_id=entity_id, provider=provider, attribute=attribute
        )

        known = {observation.id for observation in existing}
        fresh = tuple(o for o in derived if o.id not in known)
        if not fresh:
            return 0, 0

        derived_ids = {observation.id for observation in derived}
        stale = tuple(o for o in existing if o.id not in derived_ids)

        # A stale observation is not wrong — it is coarser than the evidence
        # now supports. The finer observations name it, and it stays readable
        # as what was believed then.
        replaces = refinements(fresh, stale)
        to_write = tuple(
            observation.refining(replaces[observation.id])
            if observation.id in replaces
            else observation
            for observation in fresh
        )

        written = await self._repository.record(to_write)

        for observation in to_write:
            events.append(_recorded_event(observation, causation_id))
            if observation.supersedes is not None:
                events.append(_superseded_event(observation, observation.supersedes, causation_id))

        orphaned = [o.id for o in stale if o.id not in set(replaces.values())]
        if orphaned:
            # Only reachable if claims were removed, which happens on a
            # deliberate regeneration. Logged rather than deleted: an
            # observation nobody refines is still a record of what was
            # believed, and silently dropping it would break the chain.
            logger.warning(
                "observations no longer implied by the claim series",
                extra={
                    "entity_id": str(entity_id),
                    "provider": provider,
                    "attribute": attribute.value,
                    "observation_ids": [str(i) for i in orphaned],
                },
            )

        return written, len(replaces)


def _touched_series(
    claims: Sequence[ClaimView], new_claim_ids: frozenset[UUID]
) -> list[tuple[str, ClaimAttribute]]:
    """The series the new evidence could have changed.

    Every other series is unchanged by construction — re-deriving them would
    be work with a known-empty result, which is the difference between an
    engine that scales with new evidence and one that scales with total
    evidence.
    """
    touched = {(claim.provider, claim.attribute) for claim in claims if claim.id in new_claim_ids}
    return sorted(touched, key=lambda pair: (pair[0], pair[1].value))


def _recorded_event(observation: Observation, causation_id: UUID | None) -> ObservationRecorded:
    return ObservationRecorded(
        event_id=uuid4(),
        workspace_id=observation.workspace_id,
        occurred_at=observation.recorded_at,
        observation_id=observation.id,
        entity_id=observation.entity_id,
        provider=observation.provider,
        attribute=observation.attribute.value,
        kind=observation.kind.value,
        direction=observation.direction.value,
        observed_at=observation.observed_at,
        causation_id=causation_id,
    )


def _superseded_event(
    observation: Observation, supersedes: UUID, causation_id: UUID | None
) -> ObservationSuperseded:
    return ObservationSuperseded(
        event_id=uuid4(),
        workspace_id=observation.workspace_id,
        occurred_at=observation.recorded_at,
        observation_id=observation.id,
        supersedes=supersedes,
        entity_id=observation.entity_id,
        attribute=observation.attribute.value,
        causation_id=causation_id,
    )

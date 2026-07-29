"""Derive edges from technographic claims.

`TECHNOLOGY_DETECTED` opens a `USES_TECHNOLOGY` edge; `TECHNOLOGY_REMOVED`
closes one. **Closing sets `valid_to`; it never deletes the row.** The
history of what a company used and stopped using is exactly what a
competitive-displacement signal reads, and a deleted edge is a signal that
can never be generated.

Nothing else in the current claim vocabulary yields an edge without
inventing meaning, so nothing else is derived here.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Final
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from modules.knowledge_graph.application.ports import GraphRepository
from modules.knowledge_graph.domain.events import RelationshipEnded, RelationshipEstablished
from modules.knowledge_graph.domain.identity import (
    USES_TECHNOLOGY,
    EntityKind,
    Relationship,
)
from modules.provider_normalization.public import ClaimAttribute, ClaimView
from signora_platform.event_bus import EventPublisher
from signora_platform.observability import get_logger

logger = get_logger(__name__)

PRODUCER_MODULE = "knowledge_graph"

TECHNOLOGY_NAMESPACE: Final = "canonical:technology"
"""Technology has no provider identity to resolve.

Providers report a *name*, not an identifier, so the graph assigns
technologies a canonical namespace keyed on the normalized name. Two
providers reporting "SAP ERP" therefore reach one entity.

The honest limitation: "SAP" and "SAP ERP" become two entities. That is
deterministic and it *under*-merges, which is the direction this module is
deliberately biased in — a technology catalog that reconciles vendor naming
is a real piece of work, and guessing at it here would silently merge two
different products.
"""


def canonical_technology_key(name: str) -> str:
    return " ".join(name.strip().lower().split())


def _as_datetime(value: date | None) -> datetime | None:
    """A detection date becomes an instant at UTC midnight.

    Providers report detection by day; the edge is stored with a timezone
    so that `as_of` queries compare like with like. Midnight UTC is a
    stated convention, not an inferred one — and it is the same convention
    every provider's dates are read under.
    """
    if value is None:
        return None
    return datetime(value.year, value.month, value.day, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class DeriveRelationshipsInput:
    workspace_id: UUID
    entity_id: UUID
    claims: tuple[ClaimView, ...]


@dataclass(frozen=True, slots=True)
class DeriveRelationshipsResult:
    established: int
    ended: int


class DeriveRelationships:
    def __init__(
        self,
        *,
        repository: GraphRepository,
        publisher: EventPublisher,
        session: AsyncSession,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._repository = repository
        self._publisher = publisher
        self._session = session
        self._clock = clock

    async def execute(
        self,
        request: DeriveRelationshipsInput,
        *,
        correlation_id: UUID,
        causation_id: UUID | None = None,
    ) -> DeriveRelationshipsResult:
        now = self._clock()
        events: list[RelationshipEstablished | RelationshipEnded] = []

        current = await self._repository.relationships_for_entity(
            request.workspace_id, request.entity_id, kind=USES_TECHNOLOGY
        )
        live_by_target = {r.target_entity_id: r for r in current if r.is_current}
        # Closed edges are tracked too, so a re-delivered removal claim
        # recognises the edge it already wrote instead of adding another.
        closed_by_target: dict[UUID, set[datetime]] = {}
        for relationship in current:
            if relationship.valid_to is not None:
                closed_by_target.setdefault(relationship.target_entity_id, set()).add(
                    relationship.valid_to
                )

        established = ended = 0

        # Claims are processed oldest-first so that a technology detected
        # and later removed within one batch ends up closed, rather than
        # reopened by whichever claim the planner returned last.
        for claim in sorted(request.claims, key=lambda c: (c.observed_at, str(c.id))):
            technology = claim.as_technology()
            if technology is None:
                continue

            entity, _ = await self._repository.find_or_create_canonical_entity(
                request.workspace_id,
                kind=EntityKind.TECHNOLOGY,
                canonical_key=f"{TECHNOLOGY_NAMESPACE}:{canonical_technology_key(technology.name)}",
                now=now,
            )

            if claim.attribute is ClaimAttribute.TECHNOLOGY_DETECTED:
                if entity.id in live_by_target:
                    continue
                relationship = Relationship(
                    id=uuid4(),
                    workspace_id=request.workspace_id,
                    kind=USES_TECHNOLOGY,
                    source_entity_id=request.entity_id,
                    target_entity_id=entity.id,
                    valid_from=claim.observed_at,
                    evidence_claim_ids=(claim.id,),
                )
                await self._repository.add_relationship(relationship)
                live_by_target[entity.id] = relationship
                established += 1
                events.append(
                    RelationshipEstablished(
                        event_id=uuid4(),
                        workspace_id=request.workspace_id,
                        occurred_at=now,
                        relationship_id=relationship.id,
                        kind=USES_TECHNOLOGY,
                        source_entity_id=request.entity_id,
                        target_entity_id=entity.id,
                        valid_from=relationship.valid_from,
                        causation_id=causation_id,
                    )
                )
                continue

            ended_at = _as_datetime(technology.last_seen) or claim.observed_at
            existing = live_by_target.pop(entity.id, None)

            if existing is None:
                # A removal for a technology never seen live. Common with a
                # vendor that reports current state only: Signora learns
                # that LegacyERP was retired without ever having been told
                # it was running.
                #
                # The claim still carries the interval, so the edge is
                # written *already closed* rather than dropped. Discarding
                # it would lose exactly the history a competitive-
                # displacement signal reads — the information is there, and
                # throwing it away is a choice, not a default.
                if ended_at in closed_by_target.get(entity.id, set()):
                    continue

                retired = Relationship(
                    id=uuid4(),
                    workspace_id=request.workspace_id,
                    kind=USES_TECHNOLOGY,
                    source_entity_id=request.entity_id,
                    target_entity_id=entity.id,
                    valid_from=_as_datetime(technology.first_seen) or claim.observed_at,
                    evidence_claim_ids=(claim.id,),
                    valid_to=ended_at,
                )
                await self._repository.add_relationship(retired)
                closed_by_target.setdefault(entity.id, set()).add(ended_at)
                ended += 1
                logger.info(
                    "technology recorded as already retired",
                    extra={
                        "entity_id": str(request.entity_id),
                        "technology": technology.name,
                        "claim_id": str(claim.id),
                        "valid_to": ended_at.isoformat(),
                    },
                )
                events.append(
                    RelationshipEnded(
                        event_id=uuid4(),
                        workspace_id=request.workspace_id,
                        occurred_at=now,
                        relationship_id=retired.id,
                        kind=USES_TECHNOLOGY,
                        source_entity_id=request.entity_id,
                        target_entity_id=entity.id,
                        valid_to=ended_at,
                        causation_id=causation_id,
                    )
                )
                continue

            await self._repository.end_relationship(existing.id, at=ended_at)
            closed_by_target.setdefault(entity.id, set()).add(ended_at)
            ended += 1
            events.append(
                RelationshipEnded(
                    event_id=uuid4(),
                    workspace_id=request.workspace_id,
                    occurred_at=now,
                    relationship_id=existing.id,
                    kind=USES_TECHNOLOGY,
                    source_entity_id=request.entity_id,
                    target_entity_id=entity.id,
                    valid_to=ended_at,
                    causation_id=causation_id,
                )
            )

        if events:
            await self._publisher.publish(
                events,  # type: ignore[arg-type]
                session=self._session,
                producer_module=PRODUCER_MODULE,
                correlation_id=correlation_id,
            )

        return DeriveRelationshipsResult(established=established, ended=ended)

"""Persistence for business events.

**There is no update method, deliberately.** Durable history is enforced at
the database by the absent UPDATE grant (migration 0011); not offering the
method here means nobody writes code that would fail at runtime.

Every query filters `workspace_id` explicitly even though RLS already
scopes the session — RLS is the authoritative control, not the only one
(CLAUDE.md §8).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from modules.business_event_engine.domain.business_event import BusinessEvent
from modules.business_event_engine.domain.taxonomy import BusinessDomain, BusinessEventType
from modules.business_event_engine.infrastructure.models import BusinessEventModel

SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _to_domain(row: BusinessEventModel) -> BusinessEvent:
    return BusinessEvent(
        id=row.id,
        workspace_id=row.workspace_id,
        entity_id=row.entity_id,
        type_key=BusinessEventType(row.type_key),
        domain=BusinessDomain(row.domain),
        occurred_at=row.occurred_at,
        window_start=row.window_start,
        window_end=row.window_end,
        detected_at=row.detected_at,
        summary=row.summary,
        facts=dict(row.facts),
        evidence_observation_ids=tuple(row.evidence_observation_ids),
        corroborating_providers=tuple(row.corroborating_providers),
        taxonomy_version=row.taxonomy_version,
        payload_version=row.payload_version,
        supersedes=row.supersedes,
    )


class SqlBusinessEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def current_for_entity(
        self, workspace_id: UUID, entity_id: UUID, *, type_key: BusinessEventType
    ) -> tuple[BusinessEvent, ...]:
        replaced = select(BusinessEventModel.supersedes).where(
            BusinessEventModel.workspace_id == workspace_id,
            BusinessEventModel.supersedes.is_not(None),
        )
        rows = await self._session.execute(
            select(BusinessEventModel)
            .where(
                BusinessEventModel.workspace_id == workspace_id,
                BusinessEventModel.entity_id == entity_id,
                BusinessEventModel.type_key == type_key.value,
                # A replaced event is history — what was believed before the
                # phenomenon extended — so it is excluded here rather than
                # filtered by every caller.
                BusinessEventModel.id.not_in(replaced),
            )
            .order_by(BusinessEventModel.occurred_at, BusinessEventModel.id)
        )
        return tuple(_to_domain(row) for row in rows.scalars())

    async def record(self, events: tuple[BusinessEvent, ...]) -> int:
        if not events:
            return 0

        statement = (
            insert(BusinessEventModel)
            .values(
                [
                    {
                        "id": event.id,
                        "workspace_id": event.workspace_id,
                        "entity_id": event.entity_id,
                        "type_key": event.type_key.value,
                        "domain": event.domain.value,
                        "occurred_at": event.occurred_at,
                        "window_start": event.window_start,
                        "window_end": event.window_end,
                        "detected_at": event.detected_at,
                        "summary": event.summary,
                        "facts": event.facts,
                        "evidence_observation_ids": list(event.evidence_observation_ids),
                        "corroborating_providers": list(event.corroborating_providers),
                        "taxonomy_version": event.taxonomy_version,
                        "payload_version": event.payload_version,
                        "supersedes": event.supersedes,
                        "created_by": SYSTEM_USER_ID,
                        "updated_by": SYSTEM_USER_ID,
                    }
                    for event in events
                ]
            )
            # Deduplication is a primary-key conflict, not a code path. Ids
            # are derived from the evidence, so re-detecting over the same
            # observations inserts nothing.
            .on_conflict_do_nothing(index_elements=["id"])
            .returning(BusinessEventModel.id)
        )
        result = await self._session.execute(statement)
        return len(result.scalars().all())

    async def for_entity(
        self,
        workspace_id: UUID,
        entity_id: UUID,
        *,
        type_key: BusinessEventType | None = None,
        since: datetime | None = None,
    ) -> tuple[BusinessEvent, ...]:
        statement = select(BusinessEventModel).where(
            BusinessEventModel.workspace_id == workspace_id,
            BusinessEventModel.entity_id == entity_id,
        )
        if type_key is not None:
            statement = statement.where(BusinessEventModel.type_key == type_key.value)
        if since is not None:
            statement = statement.where(BusinessEventModel.occurred_at >= since)

        rows = await self._session.execute(
            statement.order_by(BusinessEventModel.occurred_at, BusinessEventModel.id)
        )
        return tuple(_to_domain(row) for row in rows.scalars())

    async def by_id(self, workspace_id: UUID, event_id: UUID) -> BusinessEvent | None:
        row = (
            await self._session.execute(
                select(BusinessEventModel).where(
                    BusinessEventModel.workspace_id == workspace_id,
                    BusinessEventModel.id == event_id,
                )
            )
        ).scalar_one_or_none()
        return _to_domain(row) if row is not None else None

    async def citing_observations(
        self, workspace_id: UUID, observation_ids: Sequence[UUID]
    ) -> tuple[BusinessEvent, ...]:
        if not observation_ids:
            return ()
        rows = await self._session.execute(
            select(BusinessEventModel)
            .where(
                BusinessEventModel.workspace_id == workspace_id,
                BusinessEventModel.evidence_observation_ids.overlap(list(observation_ids)),
            )
            .order_by(BusinessEventModel.occurred_at, BusinessEventModel.id)
        )
        return tuple(_to_domain(row) for row in rows.scalars())

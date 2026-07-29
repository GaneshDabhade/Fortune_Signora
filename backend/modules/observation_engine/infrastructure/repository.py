"""Persistence for observations.

**There is no update method, deliberately.** Immutability is enforced at the
database by the absent UPDATE grant (migration 0010); not offering the
method here means nobody writes code that would fail at runtime.

Every query filters `workspace_id` explicitly even though RLS already
scopes the session — RLS is the authoritative control, not the only one
(CLAUDE.md §8).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from modules.observation_engine.domain.observation import (
    Observation,
    ObservationDirection,
    ObservationKind,
)
from modules.observation_engine.infrastructure.models import ObservationModel
from modules.provider_normalization.public import ClaimAttribute

SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _to_domain(row: ObservationModel) -> Observation:
    return Observation(
        id=row.id,
        workspace_id=row.workspace_id,
        entity_id=row.entity_id,
        provider=row.provider,
        attribute=ClaimAttribute(row.attribute),
        kind=ObservationKind(row.kind),
        previous_value=_unwrap(row.previous_value),
        current_value=_unwrap(row.current_value),
        direction=ObservationDirection(row.direction),
        magnitude=float(row.magnitude) if row.magnitude is not None else None,
        observed_at=row.observed_at,
        previous_observed_at=row.previous_observed_at,
        recorded_at=row.recorded_at,
        evidence_claim_ids=tuple(row.evidence_claim_ids),
        supersedes=row.supersedes,
    )


def _wrap(value: Any) -> dict[str, Any] | None:
    """Claim values are not always objects — an employee count is an int.

    Wrapping keeps the column a well-typed JSONB object rather than a mix of
    scalars and objects, which would make querying it in an incident
    unpleasant for no benefit.
    """
    return None if value is None else {"v": value}


def _unwrap(stored: dict[str, Any] | None) -> Any:
    return None if stored is None else stored.get("v")


class SqlObservationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def current_for_series(
        self, workspace_id: UUID, *, entity_id: UUID, provider: str, attribute: ClaimAttribute
    ) -> tuple[Observation, ...]:
        refined = select(ObservationModel.supersedes).where(
            ObservationModel.workspace_id == workspace_id,
            ObservationModel.supersedes.is_not(None),
        )
        rows = await self._session.execute(
            select(ObservationModel)
            .where(
                ObservationModel.workspace_id == workspace_id,
                ObservationModel.entity_id == entity_id,
                ObservationModel.provider == provider,
                ObservationModel.attribute == attribute.value,
                # A refined observation is history — what was believed before
                # a late claim sharpened the picture. Excluded here rather
                # than filtered by every caller.
                ObservationModel.id.not_in(refined),
            )
            .order_by(ObservationModel.observed_at, ObservationModel.id)
        )
        return tuple(_to_domain(row) for row in rows.scalars())

    async def record(self, observations: tuple[Observation, ...]) -> int:
        if not observations:
            return 0

        statement = (
            insert(ObservationModel)
            .values(
                [
                    {
                        "id": observation.id,
                        "workspace_id": observation.workspace_id,
                        "entity_id": observation.entity_id,
                        "provider": observation.provider,
                        "attribute": observation.attribute.value,
                        "kind": observation.kind.value,
                        "previous_value": _wrap(observation.previous_value),
                        "current_value": _wrap(observation.current_value),
                        "direction": observation.direction.value,
                        "magnitude": (
                            Decimal(str(observation.magnitude))
                            if observation.magnitude is not None
                            else None
                        ),
                        "observed_at": observation.observed_at,
                        "previous_observed_at": observation.previous_observed_at,
                        "recorded_at": observation.recorded_at,
                        "evidence_claim_ids": list(observation.evidence_claim_ids),
                        "supersedes": observation.supersedes,
                        "created_by": SYSTEM_USER_ID,
                        "updated_by": SYSTEM_USER_ID,
                    }
                    for observation in observations
                ]
            )
            # Deduplication is a primary-key conflict, not a code path.
            # Observation ids are derived from what they observe, so a
            # redelivered event or a re-derived series inserts nothing.
            .on_conflict_do_nothing(index_elements=["id"])
            .returning(ObservationModel.id)
        )
        result = await self._session.execute(statement)
        return len(result.scalars().all())

    async def for_entity(
        self,
        workspace_id: UUID,
        entity_id: UUID,
        *,
        attribute: ClaimAttribute | None = None,
        since: datetime | None = None,
    ) -> tuple[Observation, ...]:
        statement = select(ObservationModel).where(
            ObservationModel.workspace_id == workspace_id,
            ObservationModel.entity_id == entity_id,
        )
        if attribute is not None:
            statement = statement.where(ObservationModel.attribute == attribute.value)
        if since is not None:
            statement = statement.where(ObservationModel.observed_at >= since)

        rows = await self._session.execute(
            statement.order_by(ObservationModel.observed_at, ObservationModel.id)
        )
        return tuple(_to_domain(row) for row in rows.scalars())

    async def by_id(self, workspace_id: UUID, observation_id: UUID) -> Observation | None:
        row = (
            await self._session.execute(
                select(ObservationModel).where(
                    ObservationModel.workspace_id == workspace_id,
                    ObservationModel.id == observation_id,
                )
            )
        ).scalar_one_or_none()
        return _to_domain(row) if row is not None else None

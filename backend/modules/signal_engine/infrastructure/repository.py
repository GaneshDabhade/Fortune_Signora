"""Persistence for signals and profiles.

**Two repositories, deliberately.** Signals are derived and rebuildable;
profiles are customer-authored and cannot be regenerated from anything.
Keeping them apart makes it impossible to write a rebuild that quietly
discards a customer's configuration.

Neither offers an update method. Immutability is enforced at the database
by the absent UPDATE grant (migration 0012); not offering the method here
means nobody writes code that would fail at runtime.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from modules.business_event_engine.public import BusinessEventType
from modules.signal_engine.domain.catalog import Relevance, SignalType
from modules.signal_engine.domain.profile import ProfileEntry, SignalProfile
from modules.signal_engine.domain.signal import Signal
from modules.signal_engine.infrastructure.models import SignalModel, SignalProfileModel

SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _to_signal(row: SignalModel) -> Signal:
    return Signal(
        id=row.id,
        workspace_id=row.workspace_id,
        entity_id=row.entity_id,
        signal_type=SignalType(row.signal_type),
        relevance=Relevance(row.relevance),
        occurred_at=row.occurred_at,
        window_start=row.window_start,
        window_end=row.window_end,
        generated_at=row.generated_at,
        relevant_until=row.relevant_until,
        rationale=row.rationale,
        contributing_event_ids=tuple(row.contributing_event_ids),
        contributing_event_types=tuple(
            BusinessEventType(value) for value in row.contributing_event_types
        ),
        constituent_signal_ids=tuple(row.constituent_signal_ids),
        catalog_version=row.catalog_version,
        profile_version=row.profile_version,
        payload_version=row.payload_version,
        supersedes=row.supersedes,
    )


def _to_profile(row: SignalProfileModel) -> SignalProfile:
    return SignalProfile(
        id=row.id,
        workspace_id=row.workspace_id,
        version=row.version,
        entries=tuple(_to_entry(entry) for entry in row.entries),
        created_at=row.created_at,
        created_by=row.created_by,
        supersedes=row.supersedes,
    )


def _to_entry(raw: dict[str, Any]) -> ProfileEntry:
    return ProfileEntry(
        signal_type=SignalType(raw["signal_type"]),
        relevance=Relevance(raw["relevance"]),
        window_days=raw.get("window_days"),
        minimum_contributors=raw.get("minimum_contributors"),
    )


class SqlSignalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def current_for_entity(
        self, workspace_id: UUID, entity_id: UUID, *, signal_type: SignalType
    ) -> tuple[Signal, ...]:
        replaced = select(SignalModel.supersedes).where(
            SignalModel.workspace_id == workspace_id, SignalModel.supersedes.is_not(None)
        )
        rows = await self._session.execute(
            select(SignalModel)
            .where(
                SignalModel.workspace_id == workspace_id,
                SignalModel.entity_id == entity_id,
                SignalModel.signal_type == signal_type.value,
                SignalModel.id.not_in(replaced),
            )
            .order_by(SignalModel.occurred_at, SignalModel.id)
        )
        return tuple(_to_signal(row) for row in rows.scalars())

    async def record(self, signals: tuple[Signal, ...]) -> int:
        if not signals:
            return 0

        statement = (
            insert(SignalModel)
            .values(
                [
                    {
                        "id": signal.id,
                        "workspace_id": signal.workspace_id,
                        "entity_id": signal.entity_id,
                        "signal_type": signal.signal_type.value,
                        "relevance": signal.relevance.value,
                        "occurred_at": signal.occurred_at,
                        "window_start": signal.window_start,
                        "window_end": signal.window_end,
                        "generated_at": signal.generated_at,
                        "relevant_until": signal.relevant_until,
                        "rationale": signal.rationale,
                        "contributing_event_ids": list(signal.contributing_event_ids),
                        "contributing_event_types": [
                            t.value for t in signal.contributing_event_types
                        ],
                        "constituent_signal_ids": list(signal.constituent_signal_ids),
                        "catalog_version": signal.catalog_version,
                        "profile_version": signal.profile_version,
                        "payload_version": signal.payload_version,
                        "supersedes": signal.supersedes,
                        "created_by": SYSTEM_USER_ID,
                        "updated_by": SYSTEM_USER_ID,
                    }
                    for signal in signals
                ]
            )
            .on_conflict_do_nothing(index_elements=["id"])
            .returning(SignalModel.id)
        )
        result = await self._session.execute(statement)
        return len(result.scalars().all())

    async def for_entity(
        self,
        workspace_id: UUID,
        entity_id: UUID,
        *,
        signal_type: SignalType | None = None,
        live_at: datetime | None = None,
    ) -> tuple[Signal, ...]:
        statement = select(SignalModel).where(
            SignalModel.workspace_id == workspace_id, SignalModel.entity_id == entity_id
        )
        if signal_type is not None:
            statement = statement.where(SignalModel.signal_type == signal_type.value)
        if live_at is not None:
            # A hypothesis stops being current in three ways; two of them
            # are here. The third — the workspace no longer holding the
            # type — is a profile question the query layer resolves.
            replaced = select(SignalModel.supersedes).where(
                SignalModel.workspace_id == workspace_id, SignalModel.supersedes.is_not(None)
            )
            statement = statement.where(
                SignalModel.relevant_until >= live_at, SignalModel.id.not_in(replaced)
            )

        rows = await self._session.execute(
            statement.order_by(SignalModel.occurred_at, SignalModel.id)
        )
        return tuple(_to_signal(row) for row in rows.scalars())

    async def by_id(self, workspace_id: UUID, signal_id: UUID) -> Signal | None:
        row = (
            await self._session.execute(
                select(SignalModel).where(
                    SignalModel.workspace_id == workspace_id, SignalModel.id == signal_id
                )
            )
        ).scalar_one_or_none()
        return _to_signal(row) if row is not None else None

    async def citing_events(
        self, workspace_id: UUID, business_event_ids: Sequence[UUID]
    ) -> tuple[Signal, ...]:
        if not business_event_ids:
            return ()
        rows = await self._session.execute(
            select(SignalModel)
            .where(
                SignalModel.workspace_id == workspace_id,
                SignalModel.contributing_event_ids.overlap(list(business_event_ids)),
            )
            .order_by(SignalModel.occurred_at, SignalModel.id)
        )
        return tuple(_to_signal(row) for row in rows.scalars())


class SqlProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def current(self, workspace_id: UUID) -> SignalProfile | None:
        """The profile in force: **the highest version.**

        **Not `WHERE supersedes IS NULL`** (`B-001`). On an immutable table the
        row with a null `supersedes` is the *first* version — the new row is
        the one that names its predecessor — so that predicate returned
        version 1 forever and silently ignored every revision a customer made.
        It never bit because nothing has ever written a second version, which
        is exactly the shape of defect that waits for a feature.

        A maximum cannot invert. `product_catalog` (migration `0019`) and
        `research_request` (`0021`) both read currency this way, for this
        reason.
        """
        row = (
            await self._session.execute(
                select(SignalProfileModel)
                .where(SignalProfileModel.workspace_id == workspace_id)
                .order_by(SignalProfileModel.version.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        return _to_profile(row) if row is not None else None

    async def by_version(self, workspace_id: UUID, version: int) -> SignalProfile | None:
        row = (
            await self._session.execute(
                select(SignalProfileModel).where(
                    SignalProfileModel.workspace_id == workspace_id,
                    SignalProfileModel.version == version,
                )
            )
        ).scalar_one_or_none()
        return _to_profile(row) if row is not None else None

    async def save(self, profile: SignalProfile) -> None:
        self._session.add(
            SignalProfileModel(
                id=profile.id,
                workspace_id=profile.workspace_id,
                version=profile.version,
                entries=[
                    {
                        "signal_type": entry.signal_type.value,
                        "relevance": entry.relevance.value,
                        "window_days": entry.window_days,
                        "minimum_contributors": entry.minimum_contributors,
                    }
                    for entry in profile.entries
                ],
                supersedes=profile.supersedes,
                created_by=profile.created_by,
                updated_by=profile.created_by,
            )
        )
        await self._session.flush()

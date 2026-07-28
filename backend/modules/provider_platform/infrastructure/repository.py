"""Persistence for provider syncs, watermarks, and raw records."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from modules.provider_platform.domain.provider import ProviderCapability, ProviderName
from modules.provider_platform.domain.sync import (
    ProviderSync,
    RawProviderRecord,
    SyncWatermark,
)
from modules.provider_platform.infrastructure.models import (
    ProviderSyncModel,
    ProviderWatermarkModel,
    RawProviderRecordModel,
)

#: Records are written by a background worker with no acting user. A fixed
#: system identity keeps `created_by` non-nullable and honest, rather than
#: attributing machine writes to whichever human triggered the schedule.
SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


class ProviderSyncRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, sync: ProviderSync) -> None:
        model = await self._session.get(ProviderSyncModel, sync.id)
        if model is None:
            model = ProviderSyncModel(
                id=sync.id,
                workspace_id=sync.workspace_id,
                created_by=SYSTEM_USER_ID,
                updated_by=SYSTEM_USER_ID,
            )
            self._session.add(model)

        model.provider = sync.provider.value
        model.capability = sync.capability.value
        model.status = sync.status.value
        model.started_at = sync.started_at
        model.finished_at = sync.finished_at
        model.records_received = sync.records_received
        model.pages_fetched = sync.pages_fetched
        model.failure_kind = sync.failure.kind.value if sync.failure else None
        model.failure_message = sync.failure.message if sync.failure else None

    async def get_watermark(
        self, workspace_id: UUID, provider: ProviderName, capability: ProviderCapability
    ) -> SyncWatermark:
        statement = select(ProviderWatermarkModel).where(
            ProviderWatermarkModel.workspace_id == workspace_id,
            ProviderWatermarkModel.provider == provider.value,
            ProviderWatermarkModel.capability == capability.value,
        )
        model = (await self._session.execute(statement)).scalar_one_or_none()

        # An absent watermark means "never synced", which requests a full
        # snapshot — the correct first behaviour, and distinct from a
        # watermark of zero.
        return SyncWatermark(
            workspace_id=workspace_id,
            provider=provider,
            capability=capability,
            position=model.position if model else None,
        )

    async def save_watermark(self, watermark: SyncWatermark) -> None:
        statement = (
            insert(ProviderWatermarkModel)
            .values(
                id=uuid4(),
                workspace_id=watermark.workspace_id,
                provider=watermark.provider.value,
                capability=watermark.capability.value,
                position=watermark.position,
                created_by=SYSTEM_USER_ID,
                updated_by=SYSTEM_USER_ID,
            )
            .on_conflict_do_update(
                constraint="uq_provider_watermark_scope",
                set_={"position": watermark.position},
            )
        )
        await self._session.execute(statement)

    async def store_records(self, records: list[RawProviderRecord]) -> int:
        """Insert raw records, ignoring ones already stored.

        `ON CONFLICT DO NOTHING` rather than an existence check: a snapshot
        re-sync legitimately re-delivers everything, and the duplicate must
        be absorbed at the storage layer without a round trip per record.
        Returns the number actually inserted, so the sync's count reflects
        new data rather than delivered volume.
        """
        if not records:
            return 0

        statement = (
            insert(RawProviderRecordModel)
            .values(
                [
                    {
                        "id": record.id,
                        "workspace_id": record.workspace_id,
                        "sync_id": record.sync_id,
                        "provider": record.provider.value,
                        "capability": record.capability.value,
                        "external_id": record.external_id,
                        "occurred_at": record.occurred_at,
                        "payload": record.payload,
                        "created_by": SYSTEM_USER_ID,
                        "updated_by": SYSTEM_USER_ID,
                    }
                    for record in records
                ]
            )
            .on_conflict_do_nothing(constraint="uq_raw_provider_record_identity")
        )
        result: CursorResult[object] = await self._session.execute(statement)  # type: ignore[assignment]
        return int(result.rowcount or 0)

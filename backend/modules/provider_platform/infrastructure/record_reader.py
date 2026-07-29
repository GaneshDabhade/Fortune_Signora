"""The one implementation of the raw-record read port."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from modules.provider_platform.infrastructure.models import RawProviderRecordModel
from modules.provider_platform.public.records import RawRecordView


class SqlRawRecordReader:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def by_id(self, raw_record_id: UUID) -> RawRecordView | None:
        record = await self._session.get(RawProviderRecordModel, raw_record_id)
        if record is None:
            return None
        return RawRecordView(
            id=record.id,
            workspace_id=record.workspace_id,
            provider=record.provider,
            capability=record.capability,
            external_id=record.external_id,
            occurred_at=record.occurred_at,
            payload=dict(record.payload),
        )

"""Event handler: normalize a raw record when one arrives.

Subscribes to `provider.record.received` from Provider Platform. The
modules communicate only through the event bus — normalization never calls
into the provider module, and vice versa (CLAUDE.md §5).

The handler is idempotent by the platform's ledger, but persistence is
idempotent independently too: re-running the same mapper over the same
record upserts one outcome and re-inserts no claims, because a duplicate
delivery must not double the evidence.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.provider_normalization.application.normalize import (
    NormalizeRawRecord,
    RawRecordInput,
)
from modules.provider_normalization.infrastructure.mappers import MAPPERS
from modules.provider_normalization.infrastructure.models import ClaimModel
from modules.provider_normalization.infrastructure.repository import ClaimRepository
from modules.provider_platform.infrastructure.models import RawProviderRecordModel
from signora_platform.event_bus import EventEnvelope
from signora_platform.observability import get_logger

logger = get_logger(__name__)

#: Fixture-derived payloads carry their provenance through to every claim.
#: Read from the record rather than assumed, so the designation survives
#: the transition to authentic payloads without a code change.
_FIXTURE_MARKER = "_fixture"


def payload_provenance(payload: dict[str, Any]) -> str:
    return "DEVELOPMENT_FIXTURE" if _FIXTURE_MARKER in payload else "AUTHENTIC"


async def normalize_received_record(envelope: EventEnvelope, *, session: AsyncSession) -> None:
    record_id = UUID(str(envelope.payload["record_id"]))

    record = await session.get(RawProviderRecordModel, record_id)
    if record is None:
        # RLS-scoped: a record from another workspace is invisible here,
        # which is correct. Logged rather than raised — retrying will not
        # make another tenant's row appear.
        logger.warning(
            "raw record not visible for normalization",
            extra={"raw_record_id": str(record_id)},
        )
        return

    already = await session.execute(
        select(ClaimModel.id).where(ClaimModel.raw_record_id == record_id).limit(1)
    )
    if already.scalar_one_or_none() is not None:
        # Claims are immutable, so a redelivery must not append a second
        # set. The platform ledger already guarantees this per consumer;
        # this makes the guarantee hold even across a consumer rename.
        return

    outcome = NormalizeRawRecord(mappers=MAPPERS).execute(
        RawRecordInput(
            raw_record_id=record.id,
            workspace_id=record.workspace_id,
            provider=record.provider,
            payload=dict(record.payload),
            occurred_at=record.occurred_at,
            payload_provenance=payload_provenance(dict(record.payload)),
        )
    )

    repository = ClaimRepository(session)
    await repository.store(outcome.claims)
    await repository.record_outcome(record.workspace_id, outcome)

    logger.info(
        "raw record normalized",
        extra={
            "raw_record_id": str(record.id),
            "provider": record.provider,
            "claims": len(outcome.claims),
            "rejections": len(outcome.rejections),
            "mapper_version": outcome.mapper_version,
        },
    )

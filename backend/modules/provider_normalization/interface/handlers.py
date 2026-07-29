"""Event handler: normalize a raw record when one arrives.

Subscribes to `provider.record.received` from Provider Platform, and
publishes `claim.recorded` for the Knowledge Graph. The modules communicate
only through the event bus and each other's public contracts —
normalization never calls into the provider module's internals, and vice
versa (CLAUDE.md §5).

The raw record is read through Provider Platform's `RawRecordReader` port
rather than its SQLAlchemy model. The earlier implementation imported the
model directly, which worked and was a boundary violation; the port is
what makes the boundary real rather than conventional.

The handler is idempotent by the platform's ledger, but persistence is
idempotent independently too: re-running the same mapper over the same
record upserts one outcome and re-inserts no claims, because a duplicate
delivery must not double the evidence.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.provider_normalization.application.normalize import (
    NormalizeRawRecord,
    RawRecordInput,
)
from modules.provider_normalization.domain.events import ClaimRecorded
from modules.provider_normalization.infrastructure.mappers import MAPPERS
from modules.provider_normalization.infrastructure.models import ClaimModel
from modules.provider_normalization.infrastructure.repository import ClaimRepository
from modules.provider_platform.public import RawRecordReader
from signora_platform.event_bus import EventEnvelope, EventPublisher
from signora_platform.observability import get_logger

logger = get_logger(__name__)

PRODUCER_MODULE = "provider_normalization"

#: Fixture-derived payloads carry their provenance through to every claim.
#: Read from the record rather than assumed, so the designation survives
#: the transition to authentic payloads without a code change.
_FIXTURE_MARKER = "_fixture"


def payload_provenance(payload: dict[str, Any]) -> str:
    return "DEVELOPMENT_FIXTURE" if _FIXTURE_MARKER in payload else "AUTHENTIC"


async def normalize_received_record(
    envelope: EventEnvelope,
    *,
    session: AsyncSession,
    records: RawRecordReader,
    publisher: EventPublisher,
) -> None:
    record_id = UUID(str(envelope.payload["record_id"]))

    record = await records.by_id(record_id)
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
            payload=record.payload,
            occurred_at=record.occurred_at,
            payload_provenance=payload_provenance(record.payload),
        )
    )

    repository = ClaimRepository(session)
    await repository.store(outcome.claims)
    await repository.record_outcome(record.workspace_id, outcome)

    if outcome.claims:
        # The *claims'* subject, not the raw record's external id. A mapper
        # legitimately identifies a subject differently from the way the
        # provider's sync addressed it — BuiltWith keys on the domain while
        # the record was fetched by name — and the consumer must resolve
        # the identity the evidence is filed under, or it will find none.
        subject_external_id = outcome.claims[0].subject.provider_external_id

        # Published only when evidence was actually produced. An event
        # announcing zero claims would give the Knowledge Graph nothing to
        # resolve while still costing it a dispatch and a ledger row.
        # The platform's `PublishableEvent` Protocol declares its members as
        # settable attributes, which a frozen dataclass cannot satisfy —
        # every module publishing an immutable event needs this suppression
        # (see `run_sync._publish`). Raised as a platform finding rather
        # than fixed here: `signora_platform/` is frozen (CLAUDE.md §20a).
        await publisher.publish(
            [
                ClaimRecorded(  # type: ignore[list-item]
                    event_id=uuid4(),
                    workspace_id=record.workspace_id,
                    occurred_at=datetime.now(UTC),
                    raw_record_id=record.id,
                    provider=record.provider,
                    subject_external_id=subject_external_id,
                    claim_count=len(outcome.claims),
                    mapper_version=outcome.mapper_version,
                    causation_id=envelope.event_id,
                )
            ],
            session=session,
            producer_module=PRODUCER_MODULE,
            correlation_id=envelope.correlation_id,
        )

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

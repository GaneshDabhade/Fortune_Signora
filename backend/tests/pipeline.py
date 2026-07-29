"""The process composition root the pipeline demonstrations run through.

This is where concrete adapters are wired to ports — the one place allowed
to know that Provider Normalization's claim reader is backed by SQL, or
that the Knowledge Graph's resolver needs one. Modules never wire each
other; that is what keeps the boundary in
docs/architecture/05-module-dependencies.md real rather than aspirational.

Each stage is driven by the **events actually published to the outbox**,
read back the way the relay reads them. Calling handlers with hand-built
envelopes would prove the handlers work while proving nothing about the
contract between the modules.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.knowledge_graph.application.queries import GraphQueries
from modules.knowledge_graph.infrastructure.composition import (
    build_derive_relationships,
    build_queries,
    build_resolve_entity,
)
from modules.knowledge_graph.interface.handlers import resolve_recorded_claims
from modules.provider_normalization.infrastructure.claim_reader import SqlClaimReader
from modules.provider_normalization.interface.handlers import normalize_received_record
from modules.provider_platform.infrastructure.models import RawProviderRecordModel
from modules.provider_platform.infrastructure.record_reader import SqlRawRecordReader
from signora_platform.db import tenant_scoped_session
from signora_platform.event_bus import (
    EventEnvelope,
    OutboxEventModel,
    PostgresOutboxEventPublisher,
)


async def _published(
    admin_factory: async_sessionmaker[AsyncSession], event_type: str
) -> list[EventEnvelope]:
    """Read the outbox the way the relay does — under the relay's own
    identity, never the application's.

    `signora_app` holds no SELECT grant on `outbox_event` (migration 0006),
    and that is the Platform Infrastructure Policy working: a business
    module must never read an infrastructure table. The test therefore uses
    the privileged connection rather than quietly restoring the grant.
    """
    async with admin_factory() as session:
        rows = await session.execute(
            select(OutboxEventModel)
            .where(OutboxEventModel.event_type == event_type)
            .order_by(OutboxEventModel.created_at, OutboxEventModel.event_id)
        )
        return [
            EventEnvelope(
                event_id=row.event_id,
                event_type=row.event_type,
                event_version=row.event_version,
                workspace_id=row.workspace_id,
                occurred_at=row.occurred_at,
                producer_module=row.producer_module,
                correlation_id=row.correlation_id,
                causation_id=row.causation_id,
                payload=row.payload,
            )
            for row in rows.scalars()
        ]


async def normalize_all(
    factory: async_sessionmaker[AsyncSession], workspace_id: UUID, user_id: UUID
) -> int:
    """Translate every ingested raw record into claims."""
    async with tenant_scoped_session(
        factory, workspace_id=workspace_id, user_id=user_id
    ) as session:
        record_ids = list(
            (
                await session.execute(
                    select(RawProviderRecordModel.id).order_by(RawProviderRecordModel.occurred_at)
                )
            ).scalars()
        )
        for record_id in record_ids:
            await normalize_received_record(
                EventEnvelope(
                    event_id=uuid4(),
                    event_type="provider.record.received",
                    event_version=1,
                    workspace_id=workspace_id,
                    occurred_at=datetime.now(UTC),
                    producer_module="provider_platform",
                    correlation_id=uuid4(),
                    causation_id=None,
                    payload={"record_id": str(record_id)},
                ),
                session=session,
                records=SqlRawRecordReader(session),
                publisher=PostgresOutboxEventPublisher(),
            )
    return len(record_ids)


async def resolve_all(
    factory: async_sessionmaker[AsyncSession],
    admin_factory: async_sessionmaker[AsyncSession],
    workspace_id: UUID,
    user_id: UUID,
    *,
    shuffled_by: int | None = None,
) -> int:
    """Resolve identity for every `claim.recorded` event on the outbox.

    `shuffled_by` rotates the processing order. Resolution must reach the
    same graph regardless, which is the whole of AC-27 — so the knob exists
    to be turned by the test rather than described in a comment.
    """
    envelopes = [
        envelope
        for envelope in await _published(admin_factory, "claim.recorded")
        if envelope.workspace_id == workspace_id
    ]

    async with tenant_scoped_session(
        factory, workspace_id=workspace_id, user_id=user_id
    ) as session:
        if shuffled_by:
            offset = shuffled_by % len(envelopes) if envelopes else 0
            envelopes = envelopes[offset:] + envelopes[:offset]

        publisher = PostgresOutboxEventPublisher()
        claims = SqlClaimReader(session, workspace_id=workspace_id)
        for envelope in envelopes:
            await resolve_recorded_claims(
                envelope,
                resolve=build_resolve_entity(session, claims=claims, publisher=publisher),
                relationships=build_derive_relationships(session, publisher=publisher),
            )
    return len(envelopes)


def queries(session: AsyncSession, workspace_id: UUID) -> GraphQueries:
    return build_queries(session, claims=SqlClaimReader(session, workspace_id=workspace_id))

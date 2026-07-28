"""The ``EventPublisher`` port and its transactional-outbox implementation.

Modules depend on the ``EventPublisher`` Protocol (an application-layer
port, per Clean Architecture); ``PostgresOutboxEventPublisher`` is the one
infrastructure implementation, wired in at each module's composition root.
"""

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from signora_platform.event_bus.outbox_model import OutboxEventModel


@runtime_checkable
class PublishableEvent(Protocol):
    """Structural contract a module's domain event must satisfy to be
    published. Defined here, not imported from any module, so that
    ``signora_platform/`` never depends on ``modules/`` — dependencies only ever
    point the other way (docs/architecture/15-project-structure.md).
    """

    event_type: str
    event_version: int
    event_id: UUID
    occurred_at: datetime
    workspace_id: UUID
    causation_id: UUID | None

    def to_payload(self) -> dict[str, Any]: ...


class EventPublisher(Protocol):
    """Application-layer port every module depends on to publish domain
    events. Never called outside the same database transaction as the
    domain state change that produced the events — that atomicity is the
    entire point of the outbox pattern (docs/architecture/06-events.md).
    """

    async def publish(
        self,
        events: Sequence[PublishableEvent],
        *,
        session: AsyncSession,
        producer_module: str,
        correlation_id: UUID,
    ) -> None: ...


class PostgresOutboxEventPublisher:
    """Writes each event as a row in the ``outbox_event`` table, using the
    caller's already-open session so the insert commits atomically with the
    domain write that caused it.
    """

    async def publish(
        self,
        events: Sequence[PublishableEvent],
        *,
        session: AsyncSession,
        producer_module: str,
        correlation_id: UUID,
    ) -> None:
        now = datetime.now(UTC)
        for event in events:
            session.add(
                OutboxEventModel(
                    event_id=event.event_id,
                    event_type=event.event_type,
                    event_version=event.event_version,
                    workspace_id=event.workspace_id,
                    occurred_at=event.occurred_at,
                    producer_module=producer_module,
                    correlation_id=correlation_id,
                    causation_id=event.causation_id,
                    payload=event.to_payload(),
                    created_at=now,
                )
            )

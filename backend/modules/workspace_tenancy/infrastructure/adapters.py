"""Infrastructure adapters implementing this module's remaining ports:
``TenantContext`` (RLS activation) and ``EventPublisher`` (outbox writes).
"""

from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from signora_platform.db import set_workspace_context
from signora_platform.event_bus import PostgresOutboxEventPublisher

PRODUCER_MODULE = "workspace_tenancy"


class SessionTenantContext:
    """Implements ``TenantContext`` by delegating to
    ``signora_platform.db.set_workspace_context`` against the module's session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def activate_workspace(self, workspace_id: UUID) -> None:
        await set_workspace_context(self._session, workspace_id)


class OutboxEventPublisherAdapter:
    """Implements this module's ``EventPublisher`` port by delegating to the
    shared ``PostgresOutboxEventPublisher``, with the session and producer
    module name bound at construction so use cases never see either.
    """

    def __init__(self, session: AsyncSession, *, delegate: PostgresOutboxEventPublisher) -> None:
        self._session = session
        self._delegate = delegate

    async def publish(self, events: Sequence[Any], *, correlation_id: UUID) -> None:
        await self._delegate.publish(
            events,
            session=self._session,
            producer_module=PRODUCER_MODULE,
            correlation_id=correlation_id,
        )

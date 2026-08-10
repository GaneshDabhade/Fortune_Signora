"""Wiring for the Action Batch's use cases.

**One function, and it exists so two composition roots do not build the same
object differently.** The worker needs `ActionBatches` and so will the API; a
handler assembling its own repository and publisher would be a second
composition root nobody reviewed (§6).

**It takes a session and nothing else.** Everything this module depends on is
either derived from that session or is a platform component with no
configuration of its own — so there is no `Settings` object here, and inventing
one for symmetry would be the speculative generalisation §6 forbids.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from modules.action_batch.application.batches import ActionBatches
from modules.action_batch.infrastructure.repository import SqlActionBatchRepository
from signora_platform.event_bus import PostgresOutboxEventPublisher


def build_action_batches(session: AsyncSession) -> ActionBatches:
    """The four use cases, wired to the outbox.

    **The publisher writes its row inside the caller's transaction**, which is
    what makes `request_application` durable: the acceptance and the event that
    carries it commit together, or neither does (§9, the transactional outbox).
    """
    return ActionBatches(
        repository=SqlActionBatchRepository(session),
        publisher=PostgresOutboxEventPublisher(),
        session=session,
    )

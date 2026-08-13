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

from datetime import timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from modules.action_batch.application.batches import ActionBatches, ProposeBatch
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


class SqlActionBatchProposer:
    """The `ActionBatchProposer` port — [D-235](../../../../docs/DECISION_REGISTER.md) ①.

    ⚡ **It writes on the session the caller is already in**, which is what
    makes the batch and the consumer's payload atomic. 📁 ADR-0405's
    *no partial state*: **a batch that exists with no payload is an approved
    action that applies nothing**, and two endpoints called in sequence would
    make it representable.

    ⛔ **`propose` and nothing else, and the absence is the contract.** The
    aggregate's `approve`, `apply` and `reverse` remain reachable only through
    this module's own application layer and its endpoints — **approval is a
    human decision on a screen, not a call in a consumer's stack.**
    """

    def __init__(self, batches: ActionBatches) -> None:
        self._batches = batches

    async def propose(
        self,
        *,
        workspace_id: UUID,
        name: str,
        item_count: int,
        proposed_by: UUID,
        reversible_for: timedelta | None = None,
    ) -> UUID:
        batch = await self._batches.propose(
            ProposeBatch(
                workspace_id=workspace_id,
                name=name,
                item_count=item_count,
                proposed_by=proposed_by,
                reversible_for=reversible_for,
            )
        )
        return batch.id


def build_action_batch_proposer(session: AsyncSession) -> SqlActionBatchProposer:
    """⚡ **Built from the same use cases the module's own endpoints use**, so a
    proposal from a consumer and one from a screen are the same operation —
    ⛔ never a second path with its own rules (§2, *behaviour exists exactly
    once*)."""
    return SqlActionBatchProposer(build_action_batches(session))

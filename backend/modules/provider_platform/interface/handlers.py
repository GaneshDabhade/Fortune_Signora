"""Event handler: a customer changed which companies they want watched.

Subscribes to `commercial_profile.target_accounts_changed` — **the first time
anything downstream consumes a customer's declaration**, and the moment
`ProviderRequest.subject` stops being a parameter nothing supplies.

**The envelope carries identity; the declaration is read.** `workspace_id` and
`declaration_version` arrive on the event and **nothing about accounts does**
([ADR-0036](../../../../docs/architecture/adr/0036-target-account-contract.md)
§3). The list is fetched through `TargetAccountReader`, so a replayed event
cannot act on a declaration the customer has since replaced, and adding a field
to a declaration is never an event-contract change.

**This handler opens its own session**, for the reason
`ai_research_engine/interface/handlers.py` records at length: `EventHandler` is
`Callable[[EventEnvelope], Awaitable[None]]` and the dispatcher does not pass
on the session it opened to claim idempotency. Widening that signature is a
`signora_platform/` change and this module does not get to make one (§20a).
"""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.provider_platform.application.sync_targets import (
    SyncDeclaredTargets,
    SyncDeclaredTargetsInput,
)
from signora_platform.db import tenant_scoped_session
from signora_platform.event_bus import EventEnvelope
from signora_platform.observability import get_logger

logger = get_logger(__name__)

CONSUMER_NAME = "provider_platform.sync_declared_targets"
"""A permanent contract. Renaming it resets the idempotency ledger, and every
historical declaration change would be re-handled on replay — which here means
re-deriving deltas against watermarks that have since advanced, so the second
run would correctly find nothing. Harmless, and still not worth doing by
accident."""

#: The identity rows are attributed to when the platform acts without a user.
SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

SyncFactory = Callable[[AsyncSession], SyncDeclaredTargets]


async def sync_declared_targets(
    envelope: EventEnvelope,
    *,
    session_factory: async_sessionmaker[AsyncSession],
    build: SyncFactory,
) -> None:
    """Read the declaration this event announces, and start what has never
    been read.

    **Both payload fields are read from the envelope and neither is trusted as
    the current state.** `declaration_version` decides only whether this event
    has already been overtaken; the list itself comes from the port.
    """
    version = int(envelope.payload["declaration_version"])

    async with tenant_scoped_session(
        session_factory, workspace_id=envelope.workspace_id, user_id=SYSTEM_USER_ID
    ) as session:
        result = await build(session).execute(
            SyncDeclaredTargetsInput(
                workspace_id=envelope.workspace_id, declaration_version=version
            ),
            correlation_id=envelope.correlation_id,
        )

    logger.info(
        "target accounts changed: handled",
        extra={
            "workspace_id": str(envelope.workspace_id),
            "correlation_id": str(envelope.correlation_id),
            "announced_version": version,
            "acted_on": result.acted_on,
            "dispatched": len(result.dispatched),
            "skipped": result.skipped,
        },
    )


__all__ = ["CONSUMER_NAME", "sync_declared_targets"]

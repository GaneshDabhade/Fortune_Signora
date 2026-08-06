"""Starting one company's first read — the port's only implementation.

**`SyncDispatcher` had none until TASK-901**, which is why a customer's
declaration reached this module's handler and stopped there. The handler was
complete, its use case was complete, and nothing carried a subject to a
provider.

### Why an event rather than a queue call

**`ai_research_engine` is the repository's one precedent for a module asking
for its own long work, and it publishes an event**: `ai_research.requested`,
subscribed by the worker, run by a handler. This follows it exactly.

⛔ **The alternative — reaching for ARQ directly — is refused by the platform
in its own first line**: *"Modules never touch this directly — the relay
publishes, the worker consumes"*
(`signora_platform/event_bus/queue.py`). **A module that enqueued its own jobs
would also lose the outbox's guarantee**: the request would exist in Redis
while the watermark write that justified it could still roll back.

### The provider is chosen here, and the rule is one line

**The first provider that declares the capability, in name order.**
`ProviderRegistry.supporting()` sorts, so the choice is deterministic and not
a function of registration order — *hidden inputs are architecture defects*
(§2), and insertion order is one this repository has already eliminated once.

⚠️ **A workspace with no provider for the capability raises rather than
returning quietly.** Silence would leave a customer's declared companies
unread with nothing to see; the raise dead-letters through the platform's
existing escape hatch, which is what it is for. **It is the same answer for
every subject in the workspace, so failing on the first is not a partial
outcome.**
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from modules.provider_platform.domain.events import (
    ProviderSyncRequested,
    new_event_id,
)
from modules.provider_platform.domain.provider import (
    ProviderCapability,
    ProviderRegistry,
)
from signora_platform.event_bus import EventPublisher

PRODUCER_MODULE = "provider_platform"

#: What a newly declared company is read for first.
#:
#: **Company enrichment, because it is the one capability every later stage
#: depends on**: an account has to exist and be described before technographics
#: or capital events mean anything about it. The other four capabilities are
#: not refused here — they are simply not what a *first* read is.
FIRST_READ: ProviderCapability = ProviderCapability.COMPANY_ENRICHMENT


class NoProviderSupportsCapabilityError(Exception):
    """Nothing in this deployment can supply what a first read needs.

    ⚠️ **Deliberately not a `ProviderError`, and §10 is why**: *"an error must
    never name a component that was not involved… an incorrect attribution is
    worse than none, because it misdirects the investigation."* **No provider
    was reached here — none exists to reach**, and `ProviderError` requires a
    `ProviderName` precisely because everything under it happened *to* a
    vendor. This is a deployment's configuration, and it says so.
    """

    def __init__(self, capability: ProviderCapability) -> None:
        self.capability = capability
        super().__init__(f"no registered provider supports {capability.value}")


class OutboxSyncDispatcher:
    """Publishes one `provider.sync.requested` per company, on the caller's
    session so the request and the watermark it justifies commit together."""

    def __init__(
        self,
        *,
        session: AsyncSession,
        publisher: EventPublisher,
        registry: ProviderRegistry,
        capability: ProviderCapability = FIRST_READ,
    ) -> None:
        self._session = session
        self._publisher = publisher
        self._registry = registry
        self._capability = capability

    async def sync(self, *, workspace_id: UUID, subject: str, correlation_id: UUID) -> None:
        supporting = self._registry.supporting(self._capability)
        if not supporting:
            raise NoProviderSupportsCapabilityError(self._capability)

        await self._publisher.publish(
            # **The ignore this module already carries at its other publish
            # site**, and for the same reason: `PublishableEvent` asks for
            # settable attributes and every domain event here is a frozen
            # dataclass. ⚡ **It is one of the five [C-417] measured**, and
            # [TASK-418] ① is what deletes them — a platform change, and not
            # this lane's to make (§20a).
            [
                ProviderSyncRequested(  # type: ignore[list-item]
                    event_id=new_event_id(),
                    workspace_id=workspace_id,
                    occurred_at=datetime.now(UTC),
                    subject=subject,
                    provider=supporting[0],
                    capability=self._capability,
                )
            ],
            session=self._session,
            producer_module=PRODUCER_MODULE,
            correlation_id=correlation_id,
        )


__all__ = ["FIRST_READ", "NoProviderSupportsCapabilityError", "OutboxSyncDispatcher"]

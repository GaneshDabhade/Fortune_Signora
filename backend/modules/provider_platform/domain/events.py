"""Domain events published by the Provider Platform.

Cataloged in docs/architecture/06-events.md. Every event carries
``workspace_id`` and participates in the standard envelope; publication is
through the transactional outbox, in the same transaction as the state
change that caused it.

**No event carries provider payload shape or simulation state.** A consumer
that could tell a simulated record from a real one would be a consumer with
a reason to behave differently, which is the coupling AC-21 forbids.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Final
from uuid import UUID, uuid4

from modules.provider_platform.domain.provider import ProviderCapability, ProviderName

EVENT_VERSION: Final = 1

#: The wire name as a constant rather than only a dataclass default.
#: `slots=True` makes the class attribute a descriptor, so `Event.event_type`
#: reads as a repr rather than the string — `ai_research_engine` found that
#: the hard way and records it.
PROVIDER_SYNC_REQUESTED: Final = "provider.sync.requested"


@dataclass(frozen=True, slots=True)
class ProviderSyncStarted:
    event_id: UUID
    workspace_id: UUID
    occurred_at: datetime
    sync_id: UUID
    provider: ProviderName
    capability: ProviderCapability
    causation_id: UUID | None = None
    event_type: str = "provider.sync.started"
    event_version: int = EVENT_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {
            "sync_id": str(self.sync_id),
            "provider": self.provider.value,
            "capability": self.capability.value,
        }


@dataclass(frozen=True, slots=True)
class ProviderRecordReceived:
    """One raw record landed.

    Carries the record's identity, not its payload. A consumer needing the
    body reads it from the owning module's public contract — putting a
    provider payload in an event envelope would make every future vendor
    shape change an event contract change.
    """

    event_id: UUID
    workspace_id: UUID
    occurred_at: datetime
    record_id: UUID
    sync_id: UUID
    provider: ProviderName
    capability: ProviderCapability
    external_id: str
    causation_id: UUID | None = None
    event_type: str = "provider.record.received"
    event_version: int = EVENT_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {
            "record_id": str(self.record_id),
            "sync_id": str(self.sync_id),
            "provider": self.provider.value,
            "capability": self.capability.value,
            "external_id": self.external_id,
        }


@dataclass(frozen=True, slots=True)
class ProviderSyncCompleted:
    event_id: UUID
    workspace_id: UUID
    occurred_at: datetime
    sync_id: UUID
    provider: ProviderName
    capability: ProviderCapability
    records_received: int
    pages_fetched: int
    causation_id: UUID | None = None
    event_type: str = "provider.sync.completed"
    event_version: int = EVENT_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {
            "sync_id": str(self.sync_id),
            "provider": self.provider.value,
            "capability": self.capability.value,
            "records_received": self.records_received,
            "pages_fetched": self.pages_fetched,
        }


@dataclass(frozen=True, slots=True)
class ProviderSyncFailed:
    event_id: UUID
    workspace_id: UUID
    occurred_at: datetime
    sync_id: UUID
    provider: ProviderName
    capability: ProviderCapability
    failure_kind: str
    #: Coarse. A message naming exactly which credential was rejected would
    #: end up in a log aggregator with retention.
    failure_message: str
    causation_id: UUID | None = None
    event_type: str = "provider.sync.failed"
    event_version: int = EVENT_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {
            "sync_id": str(self.sync_id),
            "provider": self.provider.value,
            "capability": self.capability.value,
            "failure_kind": self.failure_kind,
            "failure_message": self.failure_message,
        }


@dataclass(frozen=True, slots=True)
class ProviderSyncRequested:
    """One declared company needs reading, and nothing has read it yet.

    ⚡ **The event that makes a customer's declaration reach a provider**
    (TASK-901). `SyncDeclaredTargets` decides *which* subjects are new; this
    announces one of them, and the worker runs it. **A declaration of fifty
    companies must not become fifty paged HTTP conversations inside one event
    handler** — which is `SyncDispatcher`'s whole reason for being a port, and
    this is the shape that satisfies it.

    **Modelled on `ai_research.requested` because that is the repository's one
    precedent for a module asking for its own long work**: publish, subscribe,
    run. ⛔ **The alternative was a module enqueueing onto ARQ directly**, and
    `signora_platform/event_bus/queue.py` refuses it in its first line —
    *"modules never touch this directly."*

    **`provider` and `capability` travel on the event**, resolved when the
    request is made rather than when it runs. A consumer that re-resolved them
    could act on a registry that has since changed, which would make a replay
    do something the original run did not — the same reasoning that keeps
    `declaration_version` on the event it answers.
    """

    event_id: UUID
    workspace_id: UUID
    occurred_at: datetime
    #: The company, as the customer typed it. **Never resolved here** — this
    #: module reads what it is given and Knowledge Graph decides identity.
    subject: str
    provider: ProviderName
    capability: ProviderCapability
    causation_id: UUID | None = None
    event_type: str = PROVIDER_SYNC_REQUESTED
    event_version: int = EVENT_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "provider": self.provider.value,
            "capability": self.capability.value,
        }


def new_event_id() -> UUID:
    return uuid4()

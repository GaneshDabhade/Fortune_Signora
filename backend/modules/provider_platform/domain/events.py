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


def new_event_id() -> UUID:
    return uuid4()

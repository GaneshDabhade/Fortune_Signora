"""Provider sync — the aggregate governing one run against one provider.

The Provider Platform's whole job is: ask a Provider Port for records,
store them, remember where it got to, and announce what arrived. This
module holds the rules for that, expressed in domain vocabulary rather
than in HTTP or SQL.

**Provider-neutral by construction.** Nothing here names Apollo,
BuiltWith, Bombora, or the simulator. The platform knows only that it holds
a Provider Port implementation; provider identity lives in adapters, and
simulation identity lives in configuration (AC-21).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from modules.provider_platform.domain.provider import ProviderCapability, ProviderName


class SyncStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SyncFailureKind(StrEnum):
    """Why a sync stopped, in terms the platform acts on.

    Deliberately coarser than the Provider Port's error hierarchy: the
    platform's decision is only *resume later* or *stop and alert*, and a
    finer taxonomy here would be a vocabulary nobody consults.
    """

    TRANSIENT = "transient"
    """Retryable. The watermark is untouched, so a later run resumes from
    the same place rather than re-reading from the beginning."""

    PERMANENT = "permanent"
    """Not retryable — a rejected credential, an unknown subject. Needs a
    human, and retrying burns quota to no purpose."""

    CONTRACT = "contract"
    """The provider responded with something unusable. Distinct because it
    means the *integration* is wrong rather than one request: a vendor
    changed a shape, and every subject will fail the same way."""


class SyncStateError(RuntimeError):
    """An operation was attempted that the sync's state does not permit."""


@dataclass(frozen=True, slots=True)
class RawProviderRecord:
    """One record as the provider returned it, before any interpretation.

    ``payload`` stays untyped and unvalidated here on purpose. Provider
    Normalization owns interpretation (M2.2); a platform that understood
    payload shapes would have to change every time a vendor did.
    """

    id: UUID
    workspace_id: UUID
    provider: ProviderName
    capability: ProviderCapability
    external_id: str
    occurred_at: datetime
    payload: dict[str, Any]
    sync_id: UUID


@dataclass(frozen=True, slots=True)
class SyncWatermark:
    """How far a (workspace, provider, capability) has been read.

    Its own value object rather than a column on the sync, so that
    resetting it — the standard recovery from a bad run — does not require
    editing or deleting sync history. Recovery should not destroy the
    record of what went wrong.
    """

    workspace_id: UUID
    provider: ProviderName
    capability: ProviderCapability
    position: datetime | None = None

    def advanced_to(self, position: datetime) -> SyncWatermark:
        """Move forward, never backwards.

        A provider returning an out-of-order record must not rewind the
        watermark — that would re-deliver everything between, and the
        duplicates would be absorbed silently by idempotency while the
        real bug stayed hidden.
        """
        if self.position is not None and position <= self.position:
            return self
        return replace(self, position=position)


@dataclass(frozen=True, slots=True)
class SyncFailure:
    kind: SyncFailureKind
    message: str


@dataclass(slots=True)
class ProviderSync:
    """One run against one provider capability, for one workspace."""

    id: UUID
    workspace_id: UUID
    provider: ProviderName
    capability: ProviderCapability
    started_at: datetime
    status: SyncStatus = SyncStatus.RUNNING
    records_received: int = 0
    pages_fetched: int = 0
    finished_at: datetime | None = None
    failure: SyncFailure | None = None
    #: Highest `occurred_at` seen this run. The watermark advances to this
    #: only on success — a partial run must not claim ground it did not
    #: fully cover, or the records after the failure point are skipped
    #: forever.
    high_water: datetime | None = field(default=None)

    @classmethod
    def start(
        cls,
        *,
        workspace_id: UUID,
        provider: ProviderName,
        capability: ProviderCapability,
        now: datetime,
    ) -> ProviderSync:
        return cls(
            id=uuid4(),
            workspace_id=workspace_id,
            provider=provider,
            capability=capability,
            started_at=now,
        )

    def record_page(self, *, records: int, high_water: datetime | None) -> None:
        if self.status is not SyncStatus.RUNNING:
            raise SyncStateError(f"cannot record a page on a {self.status} sync")

        self.pages_fetched += 1
        self.records_received += records
        if high_water is not None and (self.high_water is None or high_water > self.high_water):
            self.high_water = high_water

    def complete(self, *, now: datetime) -> None:
        if self.status is not SyncStatus.RUNNING:
            raise SyncStateError(f"cannot complete a {self.status} sync")
        self.status = SyncStatus.COMPLETED
        self.finished_at = now

    def fail(self, *, kind: SyncFailureKind, message: str, now: datetime) -> None:
        if self.status is not SyncStatus.RUNNING:
            raise SyncStateError(f"cannot fail a {self.status} sync")
        self.status = SyncStatus.FAILED
        self.finished_at = now
        self.failure = SyncFailure(kind=kind, message=message)

    @property
    def may_advance_watermark(self) -> bool:
        """Only a completed sync advances the watermark.

        A failed sync that advanced it would skip every record after its
        failure point permanently — data loss that looks like a
        successfully idle integration.
        """
        return self.status is SyncStatus.COMPLETED and self.high_water is not None

    @property
    def is_retryable(self) -> bool:
        return (
            self.status is SyncStatus.FAILED
            and self.failure is not None
            and (self.failure.kind is SyncFailureKind.TRANSIENT)
        )

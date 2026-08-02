"""Ports the Provider Platform's use cases depend on.

The sync repository is stated here as a Protocol so that `RunProviderSync`
depends on the *contract* rather than on the SQLAlchemy implementation.
Application code importing infrastructure directly compiles and runs, and
is still a Clean Architecture violation (CLAUDE.md §6): it makes the use
case untestable without a database and pins the module to one storage
technology it is supposed to be independent of.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from modules.provider_platform.domain.provider import ProviderCapability, ProviderName
from modules.provider_platform.domain.sync import (
    ProviderSync,
    RawProviderRecord,
    SyncWatermark,
)
from modules.provider_platform.domain.sync import SyncFailureKind
from modules.provider_platform.domain.targets import TargetSyncState


class SyncRepository(Protocol):
    async def save(self, sync: ProviderSync) -> None: ...

    async def get_watermark(
        self,
        workspace_id: UUID,
        provider: ProviderName,
        capability: ProviderCapability,
        subject: str,
    ) -> SyncWatermark:
        """The current position **for this subject**, or a watermark with
        `position=None` when it has never been synced — which requests a full
        snapshot and is distinct from a position of zero.

        `subject` is required rather than optional (B-004): a caller that
        could omit it would get another account's position, which is the
        defect, and it would get it silently."""
        ...

    async def save_watermark(self, watermark: SyncWatermark) -> None: ...

    async def store_records(self, records: list[RawProviderRecord]) -> int:
        """Returns the number actually inserted; a re-sync legitimately
        delivers records already stored."""
        ...


class TargetSyncStateRepository(Protocol):
    """Where *"which declaration have we acted on"* is kept.

    Its own port rather than a method on `SyncRepository`, because the two
    answer different questions and are read at different moments: one is per
    `(provider, capability, subject)` and is touched by every sync, this is
    per workspace and is touched once per declaration.
    """

    async def get(self, workspace_id: UUID) -> TargetSyncState:
        """The state, or one with `declaration_version=None` when this
        workspace has never been synchronised against a declaration."""
        ...

    async def save(self, state: TargetSyncState) -> None: ...

    async def subjects_with_a_position(self, workspace_id: UUID) -> frozenset[str]:
        """Every subject this workspace has successfully read at least once.

        **A position, not a row.** A watermark with no position records an
        attempt that stored nothing, and treating that as read is precisely
        the mistake ADR-0036 §4 warns about — an account declared, never
        fetched, and re-declared would look like *"no change"*.
        """
        ...


class SyncReporter(Protocol):
    """What `RunProviderSync` tells monitoring, and nothing more.

    **A port, not an infrastructure type.** The use case states what happened;
    whether that becomes an OpenTelemetry histogram, a log line or nothing at
    all belongs to the composition root. Its signature therefore never names a
    vendor library.

    **Why metrics at all, when every sync is already a row.** `provider_sync`
    is workspace-owned with forced RLS, so *"what is the failure rate across
    the platform right now"* cannot be answered from it without reading across
    every tenant — which the tenancy model exists to prevent. The row is what
    happened to one workspace; these are how the platform is behaving.
    """

    def sync_completed(
        self, *, provider: ProviderName, duration_ms: int, records: int
    ) -> None: ...

    def sync_failed(
        self, *, provider: ProviderName, kind: SyncFailureKind, duration_ms: int
    ) -> None: ...


class NoSyncReporter:
    """Records nothing, and is the default.

    **So the use case never carries an optional reporter.** A `None` check at
    every call site is one behaviour duplicated at each of them, and the branch
    that skips recording is a branch nothing exercises — which is how a metric
    quietly stops being emitted without any test noticing.
    """

    def sync_completed(self, *, provider: ProviderName, duration_ms: int, records: int) -> None:
        return None

    def sync_failed(
        self, *, provider: ProviderName, kind: SyncFailureKind, duration_ms: int
    ) -> None:
        return None


class Pacer(Protocol):
    """Waits. Nothing else.

    **A port so the waiting is injectable and the arithmetic is not.** How long
    to wait is a domain question (`RequestPace`); *actually* waiting is the one
    part that must not happen in a test, and separating them is what lets the
    pacing be asserted rather than timed.
    """

    async def wait(self, seconds: float) -> None: ...


class NoPacer:
    """Waits for nothing.

    **Not the production default.** Injected by tests, so a suite asserts the
    intervals that were *requested* instead of spending them — a test that
    slept for real would be measuring `asyncio`, and slowly.
    """

    async def wait(self, seconds: float) -> None:
        return None

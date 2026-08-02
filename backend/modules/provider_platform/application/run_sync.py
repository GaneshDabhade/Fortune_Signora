"""Run one provider sync — the Provider Platform's core use case.

**Provider-neutral.** This orchestrates a Provider Port implementation and
has no idea which provider is behind it, or whether it is simulated. That
neutrality is the milestone's central claim (AC-21): selection happens in
configuration, at the composition root, and nothing below it knows.

The loop is deliberately plain — fetch a page, store its records, publish,
advance, repeat. Retry lives above (ARQ), idempotency lives below (the
platform's ledger), and neither is reimplemented here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter_ns
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from modules.provider_platform.application.ports import (
    NoSyncReporter,
    SyncReporter,
    SyncRepository,
)
from modules.provider_platform.domain.events import (
    ProviderRecordReceived,
    ProviderSyncCompleted,
    ProviderSyncFailed,
    ProviderSyncStarted,
    new_event_id,
)
from modules.provider_platform.domain.provider import (
    ProviderAdapter,
    ProviderCapability,
    ProviderPayloadInvalidError,
    ProviderPermanentError,
    ProviderRequest,
    ProviderTransientError,
)
from modules.provider_platform.domain.sync import (
    ProviderSync,
    RawProviderRecord,
    SyncFailureKind,
)
from signora_platform.event_bus import EventPublisher
from signora_platform.observability import get_logger

logger = get_logger(__name__)

#: A sync that has not terminated in this many pages is looping. Without a
#: bound, a provider returning a non-advancing cursor produces an infinite
#: sync that looks like a working integration because records keep arriving.
MAX_PAGES = 500


@dataclass(frozen=True, slots=True)
class RunProviderSyncInput:
    workspace_id: UUID
    capability: ProviderCapability
    subject: str
    #: Ignored when no watermark exists, which requests a full snapshot.
    incremental: bool = True
    page_size: int = 100


@dataclass(frozen=True, slots=True)
class RunProviderSyncResult:
    sync: ProviderSync
    records_stored: int


class RunProviderSync:
    def __init__(
        self,
        *,
        adapter: ProviderAdapter,
        repository: SyncRepository,
        publisher: EventPublisher,
        session: AsyncSession,
        reporter: SyncReporter | None = None,
    ) -> None:
        self._adapter = adapter
        self._repository = repository
        self._publisher = publisher
        # **A null reporter rather than an optional one.** Every call site
        # would otherwise carry the same `if self._reporter is not None`, and
        # the branch that skips recording is the branch nothing exercises.
        self._reporter = reporter or NoSyncReporter()
        # The session is injected rather than reached for through the
        # repository: publication must happen in the *same* transaction as
        # the state change that caused it, and that is a property of this
        # use case rather than a detail the repository should expose.
        self._session = session

    async def execute(
        self, request: RunProviderSyncInput, *, correlation_id: UUID
    ) -> RunProviderSyncResult:
        descriptor = self._adapter.describe()
        now = datetime.now(UTC)
        # **Monotonic, not wall clock.** A duration read from `datetime` goes
        # negative across an NTP step, and a negative latency in a histogram
        # is worse than a missing one — it is believed.
        started = perf_counter_ns()

        sync = ProviderSync.start(
            workspace_id=request.workspace_id,
            provider=descriptor.provider,
            capability=request.capability,
            now=now,
        )
        await self._repository.save(sync)
        await self._publish(
            ProviderSyncStarted(
                event_id=new_event_id(),
                workspace_id=sync.workspace_id,
                occurred_at=now,
                sync_id=sync.id,
                provider=sync.provider,
                capability=sync.capability,
            ),
            correlation_id=correlation_id,
        )

        watermark = await self._repository.get_watermark(
            request.workspace_id, descriptor.provider, request.capability, request.subject
        )
        since = watermark.position if request.incremental else None

        stored = 0
        try:
            stored = await self._drain(sync, request, since=since, correlation_id=correlation_id)
        except ProviderTransientError as exc:
            # The watermark is deliberately untouched, so a later run
            # resumes from the same place rather than re-reading from the
            # beginning or — worse — skipping what this run did not reach.
            return await self._fail(
                sync, SyncFailureKind.TRANSIENT, str(exc), correlation_id, started=started
            )
        except ProviderPayloadInvalidError as exc:
            return await self._fail(
                sync, SyncFailureKind.CONTRACT, str(exc), correlation_id, started=started
            )
        except ProviderPermanentError as exc:
            return await self._fail(
                sync, SyncFailureKind.PERMANENT, str(exc), correlation_id, started=started
            )

        sync.complete(now=datetime.now(UTC))
        await self._repository.save(sync)

        if sync.may_advance_watermark and sync.high_water is not None:
            await self._repository.save_watermark(watermark.advanced_to(sync.high_water))

        await self._publish(
            ProviderSyncCompleted(
                event_id=new_event_id(),
                workspace_id=sync.workspace_id,
                occurred_at=datetime.now(UTC),
                sync_id=sync.id,
                provider=sync.provider,
                capability=sync.capability,
                records_received=sync.records_received,
                pages_fetched=sync.pages_fetched,
            ),
            correlation_id=correlation_id,
        )

        self._reporter.sync_completed(
            provider=sync.provider,
            duration_ms=_elapsed_ms(started),
            # **Received, not stored.** Storage deduplicates, so `stored` is a
            # measure of novelty and this is a measure of volume — and the
            # scaling trigger this feeds is about how much a provider is being
            # asked for, not how much of it turned out to be new.
            records=sync.records_received,
        )
        return RunProviderSyncResult(sync=sync, records_stored=stored)

    async def _drain(
        self,
        sync: ProviderSync,
        request: RunProviderSyncInput,
        *,
        since: datetime | None,
        correlation_id: UUID,
    ) -> int:
        cursor: str | None = None
        stored = 0

        for _ in range(MAX_PAGES):
            response = await self._adapter.fetch(
                ProviderRequest(
                    capability=request.capability,
                    workspace_id=request.workspace_id,
                    correlation_id=correlation_id,
                    subject=request.subject,
                    since=since,
                    cursor=cursor,
                    limit=request.page_size,
                )
            )

            records = [
                RawProviderRecord(
                    id=uuid4(),
                    workspace_id=request.workspace_id,
                    provider=record.provider,
                    capability=record.capability,
                    external_id=record.external_id,
                    occurred_at=record.occurred_at,
                    payload=record.payload,
                    sync_id=sync.id,
                )
                for record in response.records
            ]

            inserted = await self._repository.store_records(records)
            stored += inserted

            high_water = max((r.occurred_at for r in records), default=None)
            sync.record_page(records=inserted, high_water=high_water)

            for record in records:
                await self._publish(
                    ProviderRecordReceived(
                        event_id=new_event_id(),
                        workspace_id=record.workspace_id,
                        occurred_at=record.occurred_at,
                        record_id=record.id,
                        sync_id=sync.id,
                        provider=record.provider,
                        capability=record.capability,
                        external_id=record.external_id,
                    ),
                    correlation_id=correlation_id,
                )

            if not response.has_more:
                return stored

            if response.next_cursor is None or response.next_cursor == cursor:
                # A provider claiming more while not advancing its cursor
                # would loop forever. Treated as a contract failure because
                # it means the integration is wrong, not the request.
                raise ProviderPayloadInvalidError(
                    sync.provider, "pagination cursor did not advance"
                )
            cursor = response.next_cursor

        raise ProviderPayloadInvalidError(
            sync.provider, f"sync exceeded {MAX_PAGES} pages without terminating"
        )

    async def _fail(
        self,
        sync: ProviderSync,
        kind: SyncFailureKind,
        message: str,
        correlation_id: UUID,
        *,
        started: int,
    ) -> RunProviderSyncResult:
        sync.fail(kind=kind, message=message, now=datetime.now(UTC))
        await self._repository.save(sync)
        await self._publish(
            ProviderSyncFailed(
                event_id=new_event_id(),
                workspace_id=sync.workspace_id,
                occurred_at=datetime.now(UTC),
                sync_id=sync.id,
                provider=sync.provider,
                capability=sync.capability,
                failure_kind=kind.value,
                failure_message=message,
            ),
            correlation_id=correlation_id,
        )
        logger.warning(
            "provider sync failed",
            extra={"sync_id": str(sync.id), "provider": sync.provider.value, "kind": kind.value},
        )
        # **Reported after the state is durable.** A metric emitted before the
        # row was saved would describe a failure the database never recorded,
        # and the two would disagree in the one direction nobody checks.
        self._reporter.sync_failed(
            provider=sync.provider, kind=kind, duration_ms=_elapsed_ms(started)
        )
        return RunProviderSyncResult(sync=sync, records_stored=sync.records_received)

    async def _publish(self, event: object, *, correlation_id: UUID) -> None:
        await self._publisher.publish(
            [event],  # type: ignore[list-item]
            session=self._session,
            producer_module="provider_platform",
            correlation_id=correlation_id,
        )


def _elapsed_ms(started: int) -> int:
    return (perf_counter_ns() - started) // 1_000_000

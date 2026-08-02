"""What the Provider Platform records about itself.

**Observability is a product capability, not an operational afterthought**
(`CLAUDE.md` §2). A system cannot be improved using information it never
recorded, and the record cannot be added retroactively — the runs that would
have explained the problem are gone.

**These assert the property that is otherwise invisible.** An instrument that
silently stops firing breaks nothing: no test goes red, no request fails, and
the first sign is an incident nobody can reconstruct. So the measurement is
asserted the way behaviour is.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from modules.provider_platform.application.ports import NoPacer, NoSyncReporter
from modules.provider_platform.application.run_sync import (
    RunProviderSync,
    RunProviderSyncInput,
)
from modules.provider_platform.domain.provider import (
    ProviderCapability,
    ProviderDescriptor,
    ProviderName,
    ProviderPayloadInvalidError,
    ProviderPermanentError,
    ProviderRecord,
    ProviderRequest,
    ProviderResponse,
    ProviderTransientError,
)
from modules.provider_platform.domain.sync import SyncFailureKind

WORKSPACE = UUID("11111111-1111-4111-8111-111111111111")


@dataclass
class Recorded:
    completed: list[dict[str, object]] = field(default_factory=list)
    failed: list[dict[str, object]] = field(default_factory=list)

    def sync_completed(self, *, provider: ProviderName, duration_ms: int, records: int) -> None:
        self.completed.append(
            {"provider": provider, "duration_ms": duration_ms, "records": records}
        )

    def sync_failed(
        self, *, provider: ProviderName, kind: SyncFailureKind, duration_ms: int
    ) -> None:
        self.failed.append({"provider": provider, "kind": kind, "duration_ms": duration_ms})


class StubAdapter:
    """One page, or one failure. Enough to reach both terminal states."""

    def __init__(self, *, error: Exception | None = None, records: int = 3) -> None:
        self._error = error
        self._records = records

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            provider=ProviderName.APOLLO,
            capabilities=frozenset({ProviderCapability.COMPANY_ENRICHMENT}),
            simulated=False,
        )

    async def fetch(self, request: ProviderRequest) -> ProviderResponse:
        if self._error is not None:
            raise self._error
        return ProviderResponse(
            provider=ProviderName.APOLLO,
            records=tuple(
                ProviderRecord(
                    provider=ProviderName.APOLLO,
                    capability=ProviderCapability.COMPANY_ENRICHMENT,
                    external_id=str(index),
                    occurred_at=datetime.now(UTC),
                    payload={"id": str(index)},
                )
                for index in range(self._records)
            ),
        )


class FakeRepository:
    def __init__(self) -> None:
        self.stored = 0

    async def save(self, sync: object) -> None:
        return None

    async def get_watermark(
        self,
        workspace_id: UUID,
        provider: ProviderName,
        capability: ProviderCapability,
        subject: str,
    ) -> object:
        from modules.provider_platform.domain.sync import SyncWatermark

        return SyncWatermark(
            workspace_id=workspace_id, provider=provider, capability=capability, subject=subject
        )

    async def save_watermark(self, watermark: object) -> None:
        return None

    async def store_records(self, records: list[object]) -> int:
        self.stored = len(records)
        return self.stored


class NullPublisher:
    async def publish(
        self,
        events: list[object],
        *,
        session: object,
        producer_module: str,
        correlation_id: UUID,
    ) -> None:
        return None


class NullSession:
    async def flush(self) -> None:
        return None


def _use_case(adapter: StubAdapter, reporter: object) -> RunProviderSync:
    return RunProviderSync(
        # No ignore needed: `StubAdapter` structurally satisfies `ProviderAdapter`,
        # which is the point of a Protocol port and worth leaving visible.
        adapter=adapter,
        repository=FakeRepository(),  # type: ignore[arg-type]
        publisher=NullPublisher(),  # type: ignore[arg-type]
        session=NullSession(),  # type: ignore[arg-type]
        reporter=reporter,  # type: ignore[arg-type]
        # These assert what was measured, not how long it took.
        pacer=NoPacer(),
    )


async def _run(adapter: StubAdapter, reporter: object) -> None:
    await _use_case(adapter, reporter).execute(
        RunProviderSyncInput(
            workspace_id=WORKSPACE,
            capability=ProviderCapability.COMPANY_ENRICHMENT,
            subject="acme-corp",
        ),
        correlation_id=uuid4(),
    )


class TestASuccessfulSyncIsMeasured:
    async def test_it_reports_once(self) -> None:
        recorded = Recorded()

        await _run(StubAdapter(), recorded)

        assert len(recorded.completed) == 1
        assert recorded.failed == []

    async def test_it_names_the_provider(self) -> None:
        # An attribute rather than a metric name, so "is polling volume
        # growing" is answerable without knowing the vendor list.
        recorded = Recorded()

        await _run(StubAdapter(), recorded)

        assert recorded.completed[0]["provider"] is ProviderName.APOLLO

    async def test_it_counts_records_received_rather_than_stored(self) -> None:
        """**Received, not stored.** Storage deduplicates, so stored measures
        novelty; the scaling trigger this feeds is about how much a provider is
        being *asked* for."""
        recorded = Recorded()

        await _run(StubAdapter(records=3), recorded)

        assert recorded.completed[0]["records"] == 3

    async def test_the_duration_is_never_negative(self) -> None:
        # Read from a monotonic clock, not from `datetime` — a wall-clock
        # duration goes negative across an NTP step, and a negative latency in
        # a histogram is worse than a missing one, because it is believed.
        recorded = Recorded()

        await _run(StubAdapter(), recorded)

        assert isinstance(recorded.completed[0]["duration_ms"], int)
        assert int(str(recorded.completed[0]["duration_ms"])) >= 0


class TestAFailedSyncIsMeasuredToo:
    """**A failed sync must never be less observable than a successful one**
    (§2). The whole point of the failure counter is the case nobody was
    watching for."""

    @pytest.mark.parametrize(
        ("error", "kind"),
        [
            (ProviderTransientError(ProviderName.APOLLO, "timeout"), SyncFailureKind.TRANSIENT),
            (
                ProviderPayloadInvalidError(ProviderName.APOLLO, "shape changed"),
                SyncFailureKind.CONTRACT,
            ),
            (ProviderPermanentError(ProviderName.APOLLO, "revoked"), SyncFailureKind.PERMANENT),
        ],
    )
    async def test_each_kind_is_reported_as_itself(
        self, error: Exception, kind: SyncFailureKind
    ) -> None:
        """**Collapsing these would defeat the reason for having them.** A
        provider that changed its payload shape and one that is briefly down
        need different people woken at different times."""
        recorded = Recorded()

        await _run(StubAdapter(error=error), recorded)

        assert len(recorded.failed) == 1
        assert recorded.failed[0]["kind"] is kind
        assert recorded.completed == []

    async def test_a_failure_still_records_how_long_it_took(self) -> None:
        """A sync that failed after four minutes and one that failed instantly
        are different incidents. A latency series that excluded failures would
        look healthiest exactly when a provider started timing out."""
        recorded = Recorded()

        await _run(StubAdapter(error=ProviderTransientError(ProviderName.APOLLO, "timeout")), recorded)

        assert int(str(recorded.failed[0]["duration_ms"])) >= 0


class TestTheDefaultIsSilenceOnlyWhenAskedFor:
    async def test_the_null_reporter_records_nothing_and_raises_nothing(self) -> None:
        # A null object rather than an optional reporter: a `None` check at
        # every call site is one behaviour duplicated at each of them, and the
        # skip branch is the one nothing exercises.
        await _run(StubAdapter(), NoSyncReporter())

    async def test_a_sync_runs_identically_whether_or_not_anything_is_watching(self) -> None:
        """**Measurement must not change behaviour.** If it could, the
        instrumented path would be a different program from the one running in
        production, and every number read from it would describe the wrong
        thing."""
        watched, unwatched = Recorded(), NoSyncReporter()

        watched_case = _use_case(StubAdapter(records=5), watched)
        unwatched_case = _use_case(StubAdapter(records=5), unwatched)
        request = RunProviderSyncInput(
            workspace_id=WORKSPACE,
            capability=ProviderCapability.COMPANY_ENRICHMENT,
            subject="acme-corp",
        )

        a = await watched_case.execute(request, correlation_id=uuid4())
        b = await unwatched_case.execute(request, correlation_id=uuid4())

        assert a.sync.status is b.sync.status
        assert a.records_stored == b.records_stored

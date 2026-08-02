"""Whether the platform paces itself, or discovers the limit by being throttled.

**`rate_limit_per_minute` was declared in M2.0 and read by nobody.** The
contract suite asserts every adapter declares one; the field's own docstring
says why — *"so the platform can pace itself rather than discovering the limit
by being throttled"* — and `_drain` fetched up to five hundred pages back to
back regardless.

**The intervals are asserted, never spent.** A test that slept for real would
be measuring `asyncio`, slowly, and would still not prove the arithmetic. The
waiting is a port precisely so this suite can read what was *asked for*.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from modules.provider_platform.application.ports import NoSyncReporter
from modules.provider_platform.application.run_sync import (
    RunProviderSync,
    RunProviderSyncInput,
)
from modules.provider_platform.domain.pacing import RequestPace
from modules.provider_platform.domain.provider import (
    ProviderCapability,
    ProviderDescriptor,
    ProviderName,
    ProviderRecord,
    ProviderRequest,
    ProviderResponse,
)

WORKSPACE = UUID("11111111-1111-4111-8111-111111111111")


class TestTheArithmetic:
    def test_a_declared_limit_becomes_an_interval(self) -> None:
        assert RequestPace(60).interval_seconds == pytest.approx(1.0)
        assert RequestPace(30).interval_seconds == pytest.approx(2.0)

    def test_no_declared_limit_means_no_waiting(self) -> None:
        """**Never a default rate.** Inventing one for a provider that stated
        none would slow every sync to a speed nobody asked for, and the
        contract suite explicitly permits declaring none."""
        pace = RequestPace(None)

        assert pace.interval_seconds == 0.0
        assert pace.delay_after(0.0) == 0.0

    def test_time_already_spent_counts_against_the_interval(self) -> None:
        """A provider that took two seconds to answer has already spent two
        seconds of its own spacing. Waiting the full interval on top would
        punish a slow provider twice."""
        assert RequestPace(30).delay_after(0.5) == pytest.approx(1.5)

    def test_a_request_slower_than_the_interval_waits_for_nothing(self) -> None:
        # Never negative: the limit has already been respected by the
        # provider's own latency.
        assert RequestPace(60).delay_after(5.0) == 0.0

    def test_a_zero_or_negative_limit_is_refused(self) -> None:
        """*"Never ask"* is not a rate limit — it is a disabled provider, and
        that is a different decision made somewhere else."""
        with pytest.raises(ValueError):
            RequestPace(0)
        with pytest.raises(ValueError):
            RequestPace(-1)


@dataclass
class RecordingPacer:
    waited: list[float] = field(default_factory=list)

    async def wait(self, seconds: float) -> None:
        self.waited.append(seconds)


class PagedAdapter:
    """Returns `pages` pages, then stops."""

    def __init__(self, *, pages: int, limit: int | None) -> None:
        self._pages = pages
        self._limit = limit
        self.calls = 0

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            provider=ProviderName.APOLLO,
            capabilities=frozenset({ProviderCapability.COMPANY_ENRICHMENT}),
            simulated=False,
            rate_limit_per_minute=self._limit,
        )

    async def fetch(self, request: ProviderRequest) -> ProviderResponse:
        self.calls += 1
        more = self.calls < self._pages
        return ProviderResponse(
            provider=ProviderName.APOLLO,
            records=(
                ProviderRecord(
                    provider=ProviderName.APOLLO,
                    capability=ProviderCapability.COMPANY_ENRICHMENT,
                    external_id=f"{self.calls}",
                    occurred_at=datetime.now(UTC),
                    payload={},
                ),
            ),
            # **Advancing**, because a repeated cursor is a contract failure the
            # loop correctly refuses — found by writing this stub wrong first.
            next_cursor=f"page-{self.calls}" if more else None,
            has_more=more,
        )


class FakeRepository:
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
        return len(records)


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


async def _run(adapter: PagedAdapter, pacer: RecordingPacer) -> None:
    await RunProviderSync(
        adapter=adapter,
        repository=FakeRepository(),  # type: ignore[arg-type]
        publisher=NullPublisher(),  # type: ignore[arg-type]
        session=NullSession(),  # type: ignore[arg-type]
        pacer=pacer,
        reporter=NoSyncReporter(),
    ).execute(
        RunProviderSyncInput(
            workspace_id=WORKSPACE,
            capability=ProviderCapability.COMPANY_ENRICHMENT,
            subject="acme-corp",
        ),
        correlation_id=uuid4(),
    )


class TestTheLoopHonoursIt:
    async def test_a_declared_limit_paces_every_page_after_the_first(self) -> None:
        """**Three pages, two intervals.** The first page of a sync follows
        nothing this loop issued; delaying it would add latency to every sync
        in exchange for spacing that is already there."""
        pacer = RecordingPacer()

        await _run(PagedAdapter(pages=3, limit=60), pacer)

        assert len(pacer.waited) == 2
        assert all(w == pytest.approx(1.0, abs=0.05) for w in pacer.waited)

    async def test_a_provider_declaring_no_limit_is_never_delayed(self) -> None:
        # The regression that matters most: pacing must not appear where
        # nobody asked for it.
        pacer = RecordingPacer()

        await _run(PagedAdapter(pages=4, limit=None), pacer)

        assert pacer.waited == [0.0, 0.0, 0.0]

    async def test_a_single_page_sync_never_waits(self) -> None:
        pacer = RecordingPacer()

        await _run(PagedAdapter(pages=1, limit=60), pacer)

        assert pacer.waited == []

    async def test_pacing_does_not_change_what_is_fetched(self) -> None:
        """**Measurement and pacing must not change the program.** A paced sync
        must return the same pages as an unpaced one, or every number read from
        the paced path describes a different system."""
        paced, unpaced = RecordingPacer(), RecordingPacer()
        fast, slow = PagedAdapter(pages=3, limit=None), PagedAdapter(pages=3, limit=60)

        await _run(fast, paced)
        await _run(slow, unpaced)

        assert fast.calls == slow.calls == 3

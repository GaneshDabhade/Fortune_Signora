"""When a provider last *looked*, as distinct from what it found. **A7.**

**The two facts diverge exactly where a seller needs them to.** `position`
records how far a subject has been read and advances only when records arrive,
so before this slice **an account nobody has found anything about was
indistinguishable from one nobody had checked.** A brief saying *"Latest
evidence · 5 weeks ago"* could not tell a seller whether the account went quiet
or the pipeline did.

**The risk this slice carries is the opposite of the gap it closes.** Saying
*checked* about a read that never happened would relocate the false certainty
rather than remove it — so a failed run is asserted to write nothing here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from modules.provider_platform.application.ports import NoPacer, NoSyncReporter
from modules.provider_platform.application.run_sync import (
    RunProviderSync,
    RunProviderSyncInput,
)
from modules.provider_platform.domain.provider import (
    ProviderCapability,
    ProviderDescriptor,
    ProviderName,
    ProviderRecord,
    ProviderRequest,
    ProviderResponse,
    ProviderTransientError,
)
from modules.provider_platform.domain.sync import SyncWatermark

WORKSPACE = UUID("11111111-1111-4111-8111-111111111111")
SUBJECT = "acme-corp"


class StubAdapter:
    """One page, empty or not — or one failure."""

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


@dataclass
class FakeRepository:
    """Holds the watermark, so a second run reads what the first wrote."""

    watermark: SyncWatermark | None = None
    saved: list[SyncWatermark] = field(default_factory=list)

    async def save(self, sync: object) -> None:
        return None

    async def get_watermark(
        self,
        workspace_id: UUID,
        provider: ProviderName,
        capability: ProviderCapability,
        subject: str,
    ) -> SyncWatermark:
        if self.watermark is not None:
            return self.watermark
        return SyncWatermark(
            workspace_id=workspace_id,
            provider=provider,
            capability=capability,
            subject=subject,
        )

    async def save_watermark(self, watermark: SyncWatermark) -> None:
        self.watermark = watermark
        self.saved.append(watermark)

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


async def _run(adapter: StubAdapter, repository: FakeRepository) -> None:
    use_case = RunProviderSync(
        adapter=adapter,
        repository=repository,  # type: ignore[arg-type]
        publisher=NullPublisher(),  # type: ignore[arg-type]
        session=NullSession(),  # type: ignore[arg-type]
        reporter=NoSyncReporter(),
        pacer=NoPacer(),
    )
    await use_case.execute(
        RunProviderSyncInput(
            workspace_id=WORKSPACE,
            capability=ProviderCapability.COMPANY_ENRICHMENT,
            subject=SUBJECT,
        ),
        correlation_id=uuid4(),
    )



class TestASuccessfulReadRecordsThatItHappened:
    async def test_a_run_that_found_something_says_when_it_looked(self) -> None:
        repository = FakeRepository()

        await _run(StubAdapter(records=3), repository)

        assert repository.watermark is not None
        assert repository.watermark.attempted_at is not None

    async def test_a_run_that_found_nothing_says_when_it_looked(self) -> None:
        # **The case the whole slice exists for.** Before A7 this run wrote
        # no watermark at all, because `position` only advances when records
        # arrive — so a checked-and-empty account was indistinguishable from
        # an unchecked one.
        repository = FakeRepository()

        await _run(StubAdapter(records=0), repository)

        assert repository.watermark is not None
        assert repository.watermark.attempted_at is not None

    async def test_an_account_never_checked_is_distinguishable_from_one_checked_and_empty(
        self,
    ) -> None:
        # Acceptance ②, asserted as the contrast rather than as one half.
        never = SyncWatermark(
            workspace_id=WORKSPACE,
            provider=ProviderName.APOLLO,
            capability=ProviderCapability.COMPANY_ENRICHMENT,
            subject=SUBJECT,
        )
        repository = FakeRepository()

        await _run(StubAdapter(records=0), repository)
        checked = repository.watermark

        assert never.attempted_at is None
        assert checked is not None and checked.attempted_at is not None

    async def test_a_later_run_moves_it_forward(self) -> None:
        repository = FakeRepository()

        await _run(StubAdapter(records=0), repository)
        first = repository.watermark
        await _run(StubAdapter(records=0), repository)
        second = repository.watermark

        assert first is not None and first.attempted_at is not None
        assert second is not None and second.attempted_at is not None
        assert second.attempted_at >= first.attempted_at


class TestAFailedRunSaysNothingAboutLooking:
    async def test_it_writes_no_watermark(self) -> None:
        # **The word *checked* ships only once it is true.** A run that raised
        # did not successfully read anything, and recording it here would
        # relocate the false certainty this field exists to remove. What
        # happened is on `provider_sync`, which is the record for it.
        repository = FakeRepository()

        await _run(
            StubAdapter(error=ProviderTransientError(ProviderName.APOLLO, "upstream unavailable")),
            repository,
        )

        assert repository.saved == []

    async def test_it_does_not_overwrite_an_earlier_successful_read(self) -> None:
        repository = FakeRepository()
        await _run(StubAdapter(records=0), repository)
        succeeded_at = repository.watermark.attempted_at if repository.watermark else None

        await _run(
            StubAdapter(error=ProviderTransientError(ProviderName.APOLLO, "upstream unavailable")),
            repository,
        )

        assert repository.watermark is not None
        assert repository.watermark.attempted_at == succeeded_at


class TestThePositionRuleIsUntouched:
    """A7 adds a fact; it must not quietly change the one already there."""

    async def test_an_empty_read_still_leaves_the_position_alone(self) -> None:
        # `subjects_with_a_position` reads *position*, not the row — so a
        # watermark created purely to record an attempt must not make an
        # unread subject look read (ADR-0036 §4).
        repository = FakeRepository()

        await _run(StubAdapter(records=0), repository)

        assert repository.watermark is not None
        assert repository.watermark.position is None

    async def test_a_read_that_found_something_still_advances_the_position(self) -> None:
        repository = FakeRepository()

        await _run(StubAdapter(records=3), repository)

        assert repository.watermark is not None
        assert repository.watermark.position is not None

    def test_a_position_still_refuses_to_go_backwards(self) -> None:
        later = datetime.now(UTC)
        watermark = SyncWatermark(
            workspace_id=WORKSPACE,
            provider=ProviderName.APOLLO,
            capability=ProviderCapability.COMPANY_ENRICHMENT,
            subject=SUBJECT,
            position=later,
        )

        assert watermark.advanced_to(later - timedelta(days=1)).position == later

    def test_an_attempt_always_moves_because_a_later_run_did_happen(self) -> None:
        # **Deliberately unlike `advanced_to`.** A position going backwards
        # would re-deliver evidence. An attempt time is a statement about
        # when a run finished, and the run that is writing it finished last.
        earlier = datetime.now(UTC) - timedelta(days=1)
        watermark = SyncWatermark(
            workspace_id=WORKSPACE,
            provider=ProviderName.APOLLO,
            capability=ProviderCapability.COMPANY_ENRICHMENT,
            subject=SUBJECT,
            attempted_at=datetime.now(UTC),
        )

        assert watermark.attempted(earlier).attempted_at == earlier

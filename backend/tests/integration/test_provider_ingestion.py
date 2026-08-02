"""M2.1 demonstration: the Provider Platform ingests through the real path.

**The most important test in this milestone.** It proves the Provider
Platform consumes a Provider Port implementation *without knowing whether
the source is simulated or production* — validating the architecture
M2.0 was built on. If this needed a single simulation-specific branch, the
Port's design would be wrong and every downstream module would inherit the
flaw.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.provider_platform.application.run_sync import RunProviderSyncInput
from modules.provider_platform.domain.provider import ProviderCapability, ProviderName
from modules.provider_platform.domain.sync import SyncFailureKind, SyncStatus
from modules.provider_platform.infrastructure.adapters.simulated.adapter import (
    SimulatedProviderAdapter,
)
from modules.provider_platform.infrastructure.composition import build_run_sync
from modules.workspace_tenancy.application.use_cases import CreateWorkspaceInput
from modules.workspace_tenancy.infrastructure.composition import build_use_cases
from signora_platform.db import tenant_scoped_session, user_scoped_session
from signora_platform.event_bus import PostgresOutboxEventPublisher
from signora_platform.simulation import (
    ClockMode,
    DeliveryPlan,
    FaultInjector,
    FaultKind,
    FaultProfile,
    FaultRule,
    ReplayRecord,
    VirtualClock,
    build_timeline,
    load,
    load_scenario,
)
from signora_platform.simulation.generators import ApolloFixtureGenerator

pytestmark = pytest.mark.integration

REPLAY = ReplayRecord("baseline", 1, "1", "0.1.0-fixture", "instant", "baseline@1")


def _adapter(
    *, page_size: int = 100, faults: FaultProfile | None = None
) -> SimulatedProviderAdapter:
    timeline = build_timeline(
        load_scenario("baseline", 1),
        load("baseline", 1),
        VirtualClock(mode=ClockMode.INSTANT),
        seed=1,
        providers=["apollo"],
    )
    return SimulatedProviderAdapter(
        provider=ProviderName.APOLLO,
        capabilities=frozenset({ProviderCapability.COMPANY_ENRICHMENT}),
        generator=ApolloFixtureGenerator(),
        plan=DeliveryPlan(
            timeline,
            page_size=page_size,
            injector=FaultInjector(faults, seed=1) if faults else None,
        ),
        replay=REPLAY,
    )


async def _workspace(factory: async_sessionmaker[AsyncSession]) -> tuple[UUID, UUID]:
    user_id = uuid4()
    async with user_scoped_session(factory, user_id=user_id) as session:
        result = await build_use_cases(session).create_workspace.execute(
            CreateWorkspaceInput(name="Ingestion", created_by=user_id), correlation_id=uuid4()
        )
        return result.workspace.id, user_id


class TestIngestion:
    async def test_a_sync_stores_records_and_completes(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """The demonstration. A Provider Port implementation is consumed by
        the real platform, through the real pipeline, and the records land
        in the real table."""
        workspace_id, user_id = await _workspace(session_factory)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            use_case = build_run_sync(
                session, adapter=_adapter(), publisher=PostgresOutboxEventPublisher()
            )
            result = await use_case.execute(
                RunProviderSyncInput(
                    workspace_id=workspace_id,
                    capability=ProviderCapability.COMPANY_ENRICHMENT,
                    subject="acme-corp",
                ),
                correlation_id=uuid4(),
            )

        assert result.sync.status is SyncStatus.COMPLETED
        assert result.records_stored >= 1
        assert result.sync.pages_fetched >= 1

    async def test_records_are_workspace_scoped(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Ingested data is tenant data. RLS applies to it exactly as to
        anything else — asserted with an unfiltered query."""
        workspace_id, user_id = await _workspace(session_factory)
        other_id, other_user = await _workspace(session_factory)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            await build_run_sync(
                session, adapter=_adapter(), publisher=PostgresOutboxEventPublisher()
            ).execute(
                RunProviderSyncInput(
                    workspace_id=workspace_id,
                    capability=ProviderCapability.COMPANY_ENRICHMENT,
                    subject="acme-corp",
                ),
                correlation_id=uuid4(),
            )

        async with tenant_scoped_session(
            session_factory, workspace_id=other_id, user_id=other_user
        ) as session:
            visible = (
                await session.execute(text("SELECT count(*) FROM raw_provider_record"))
            ).scalar_one()

        assert visible == 0, "another workspace saw ingested records"

    async def test_a_resync_stores_no_duplicates(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """A snapshot re-sync legitimately re-delivers everything. Storage
        must absorb it — that is what makes a full re-sync a safe recovery
        action rather than a data-doubling one."""
        workspace_id, user_id = await _workspace(session_factory)

        async def run() -> int:
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=user_id
            ) as session:
                result = await build_run_sync(
                    session, adapter=_adapter(), publisher=PostgresOutboxEventPublisher()
                ).execute(
                    RunProviderSyncInput(
                        workspace_id=workspace_id,
                        capability=ProviderCapability.COMPANY_ENRICHMENT,
                        subject="acme-corp",
                        incremental=False,
                    ),
                    correlation_id=uuid4(),
                )
                return result.records_stored

        first = await run()
        second = await run()

        assert first >= 1
        assert second == 0, "a re-sync duplicated records"

    async def test_pagination_drains_every_page(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        workspace_id, user_id = await _workspace(session_factory)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            result = await build_run_sync(
                session, adapter=_adapter(page_size=1), publisher=PostgresOutboxEventPublisher()
            ).execute(
                RunProviderSyncInput(
                    workspace_id=workspace_id,
                    capability=ProviderCapability.COMPANY_ENRICHMENT,
                    subject="acme-corp",
                    page_size=1,
                ),
                correlation_id=uuid4(),
            )

        assert result.sync.pages_fetched >= 2

    async def test_events_are_published_in_the_causing_transaction(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Sync events reach the outbox alongside the records that caused
        them, so a consumer cannot be told about a record that was rolled
        back."""
        workspace_id, user_id = await _workspace(session_factory)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            await build_run_sync(
                session, adapter=_adapter(), publisher=PostgresOutboxEventPublisher()
            ).execute(
                RunProviderSyncInput(
                    workspace_id=workspace_id,
                    capability=ProviderCapability.COMPANY_ENRICHMENT,
                    subject="acme-corp",
                ),
                correlation_id=uuid4(),
            )

        async with admin_session_factory() as session, session.begin():
            types = (
                (
                    await session.execute(
                        text(
                            "SELECT DISTINCT event_type FROM outbox_event "
                            "WHERE event_type LIKE 'provider.%' ORDER BY event_type"
                        )
                    )
                )
                .scalars()
                .all()
            )

        assert "provider.sync.started" in types
        assert "provider.sync.completed" in types
        assert "provider.record.received" in types


class TestFailureHandling:
    async def test_a_transient_failure_leaves_the_watermark_untouched(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """So a later run resumes from the same place rather than skipping
        what this run never reached — which would be silent data loss that
        looks like a healthy idle integration."""
        workspace_id, user_id = await _workspace(session_factory)
        faults = FaultProfile(rules=(FaultRule(kind=FaultKind.TIMEOUT),))

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            result = await build_run_sync(
                session,
                adapter=_adapter(faults=faults),
                publisher=PostgresOutboxEventPublisher(),
            ).execute(
                RunProviderSyncInput(
                    workspace_id=workspace_id,
                    capability=ProviderCapability.COMPANY_ENRICHMENT,
                    subject="acme-corp",
                ),
                correlation_id=uuid4(),
            )

            watermark = await session.execute(
                text("SELECT count(*) FROM provider_watermark WHERE position IS NOT NULL")
            )

        assert result.sync.status is SyncStatus.FAILED
        assert result.sync.failure is not None
        assert result.sync.failure.kind is SyncFailureKind.TRANSIENT
        assert result.sync.is_retryable is True
        assert watermark.scalar_one() == 0

    async def test_a_rate_limit_is_transient_not_permanent(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Retrying a permanent failure burns quota; giving up on a rate
        limit loses data that was merely delayed."""
        workspace_id, user_id = await _workspace(session_factory)
        faults = FaultProfile(rules=(FaultRule(kind=FaultKind.RATE_LIMITED),))

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            result = await build_run_sync(
                session,
                adapter=_adapter(faults=faults),
                publisher=PostgresOutboxEventPublisher(),
            ).execute(
                RunProviderSyncInput(
                    workspace_id=workspace_id,
                    capability=ProviderCapability.COMPANY_ENRICHMENT,
                    subject="acme-corp",
                ),
                correlation_id=uuid4(),
            )

        assert result.sync.failure is not None
        assert result.sync.failure.kind is SyncFailureKind.TRANSIENT

    async def test_a_malformed_payload_is_a_contract_failure(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Distinct from a permanent error: it means the integration is
        wrong rather than one request, and every subject will fail the same
        way."""
        workspace_id, user_id = await _workspace(session_factory)
        faults = FaultProfile(rules=(FaultRule(kind=FaultKind.MALFORMED_PAYLOAD),))

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            result = await build_run_sync(
                session,
                adapter=_adapter(faults=faults),
                publisher=PostgresOutboxEventPublisher(),
            ).execute(
                RunProviderSyncInput(
                    workspace_id=workspace_id,
                    capability=ProviderCapability.COMPANY_ENRICHMENT,
                    subject="acme-corp",
                ),
                correlation_id=uuid4(),
            )

        assert result.sync.failure is not None
        assert result.sync.failure.kind is SyncFailureKind.CONTRACT
        assert result.sync.is_retryable is False


class TestAWatermarkBelongsToOneSubject:
    """**B-004.** `provider_watermark` was keyed `(workspace, provider,
    capability)` and carried no subject, so a workspace watching two accounts
    shared one position between them.

    **The failure is silent, which is what makes it worth a suite of its
    own.** Sync Acme to Tuesday, then sync Initech: Initech's run reads
    Acme's position, asks the provider for everything *since* it, and every
    Initech record older than Tuesday is never requested. No error, no log,
    no failed sync — just evidence that never becomes a signal, on an
    integration that looks healthy.

    Latent until PP-02, because nothing outside the simulation framework has
    ever supplied a `subject` and no workspace has yet had two.
    """

    async def _sync(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        workspace_id: UUID,
        user_id: UUID,
        subject: str,
    ) -> None:
        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            await build_run_sync(
                session, adapter=_adapter(), publisher=PostgresOutboxEventPublisher()
            ).execute(
                RunProviderSyncInput(
                    workspace_id=workspace_id,
                    capability=ProviderCapability.COMPANY_ENRICHMENT,
                    subject=subject,
                ),
                correlation_id=uuid4(),
            )

    async def test_two_watched_accounts_keep_separate_positions(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """The regression. One row per subject, not one row shared."""
        workspace_id, user_id = await _workspace(session_factory)

        await self._sync(session_factory, workspace_id, user_id, "acme-corp")
        await self._sync(session_factory, workspace_id, user_id, "initech")

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            subjects = (
                (
                    await session.execute(
                        text(
                            "SELECT subject FROM provider_watermark "
                            "WHERE workspace_id = :w ORDER BY subject"
                        ),
                        {"w": workspace_id},
                    )
                )
                .scalars()
                .all()
            )

        assert list(subjects) == ["acme-corp", "initech"]

    async def test_the_second_account_is_not_read_from_the_first_s_position(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """**The defect stated as behaviour rather than as schema.**

        A row count proves the constraint changed; this proves what the
        constraint was protecting. The second subject must be read from the
        beginning, because *it* has never been synced — which is exactly
        what an absent watermark already means.
        """
        workspace_id, user_id = await _workspace(session_factory)

        await self._sync(session_factory, workspace_id, user_id, "acme-corp")

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            before = await build_run_sync(
                session, adapter=_adapter(), publisher=PostgresOutboxEventPublisher()
            )._repository.get_watermark(
                workspace_id,
                ProviderName.APOLLO,
                ProviderCapability.COMPANY_ENRICHMENT,
                "initech",
            )

        assert before.position is None, (
            "a subject that has never been synced must have no position — "
            "reading another account's is B-004"
        )
        assert before.subject == "initech"

    async def test_one_account_advancing_does_not_move_the_other(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Re-syncing Acme must leave Initech exactly where it was. Under
        the old key it would have moved both, and the movement would have
        been invisible."""
        workspace_id, user_id = await _workspace(session_factory)

        await self._sync(session_factory, workspace_id, user_id, "acme-corp")
        await self._sync(session_factory, workspace_id, user_id, "initech")

        async def position(subject: str) -> object:
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=user_id
            ) as session:
                return (
                    await session.execute(
                        text(
                            "SELECT position FROM provider_watermark "
                            "WHERE workspace_id = :w AND subject = :s"
                        ),
                        {"w": workspace_id, "s": subject},
                    )
                ).scalar_one()

        initech_before = await position("initech")
        await self._sync(session_factory, workspace_id, user_id, "acme-corp")

        assert await position("initech") == initech_before

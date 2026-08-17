"""M2.2 demonstration: raw records become claims through the real path.

Proves the second link of the pipeline. A provider payload ingested by
Provider Platform is translated into canonical claims by Provider
Normalization — module to module, over the event bus, with the evidence
chain intact from raw record to claim.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.provider_platform.application.run_sync import RunProviderSyncInput
from modules.provider_platform.domain.provider import ProviderCapability
from modules.provider_platform.infrastructure.composition import build_run_sync
from modules.workspace_tenancy.application.use_cases import CreateWorkspaceInput
from modules.workspace_tenancy.infrastructure.composition import build_use_cases
from signora_platform.db import tenant_scoped_session, user_scoped_session
from signora_platform.event_bus import PostgresOutboxEventPublisher
from tests.integration.test_provider_ingestion import _adapter
from tests.pipeline import normalize_all
from tests.slugs import test_slug as _test_slug

pytestmark = pytest.mark.integration


async def _ingest(factory: async_sessionmaker[AsyncSession]) -> tuple[UUID, UUID]:
    """Run a real sync, then return the workspace and its raw records."""
    user_id = uuid4()
    async with user_scoped_session(factory, user_id=user_id) as session:
        workspace_id = (
            await build_use_cases(session).create_workspace.execute(
                CreateWorkspaceInput(name="Normalization", slug=_test_slug("Normalization"), created_by=user_id),
                correlation_id=uuid4(),
            )
        ).workspace.id

    async with tenant_scoped_session(
        factory, workspace_id=workspace_id, user_id=user_id
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

    return workspace_id, user_id


async def _normalize_all(
    factory: async_sessionmaker[AsyncSession], workspace_id: UUID, user_id: UUID
) -> int:
    return await normalize_all(factory, workspace_id, user_id)


class TestPipelineDemonstration:
    async def test_raw_records_become_claims(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        workspace_id, user_id = await _ingest(session_factory)

        records = await _normalize_all(session_factory, workspace_id, user_id)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            claims = (await session.execute(text("SELECT count(*) FROM claim"))).scalar_one()
            outcomes = (
                await session.execute(text("SELECT count(*) FROM normalization_outcome"))
            ).scalar_one()

        assert records >= 1
        assert claims >= 1, "no evidence was produced from ingested records"
        assert outcomes == records, "every record must produce an outcome, even an empty one"

    async def test_every_claim_traces_to_its_raw_record(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """The evidence chain. A claim that cannot be traced looks like
        knowledge without being it."""
        workspace_id, user_id = await _ingest(session_factory)
        await _normalize_all(session_factory, workspace_id, user_id)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            orphans = (
                await session.execute(
                    text(
                        "SELECT count(*) FROM claim c "
                        "LEFT JOIN raw_provider_record r ON r.id = c.raw_record_id "
                        "WHERE r.id IS NULL"
                    )
                )
            ).scalar_one()
            provenance = (
                (await session.execute(text("SELECT DISTINCT payload_provenance FROM claim")))
                .scalars()
                .all()
            )

        assert orphans == 0
        assert set(provenance) == {"DEVELOPMENT_FIXTURE"}, (
            "fixture provenance must travel with the claim, so conclusions built on a "
            "fixture can be found when authentic payloads arrive"
        )

    async def test_claims_are_workspace_scoped(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        workspace_id, user_id = await _ingest(session_factory)
        await _normalize_all(session_factory, workspace_id, user_id)
        other_id, other_user = await _ingest(session_factory)

        async with tenant_scoped_session(
            session_factory, workspace_id=other_id, user_id=other_user
        ) as session:
            visible = (await session.execute(text("SELECT count(*) FROM claim"))).scalar_one()

        assert visible == 0, "another workspace saw claims"

    async def test_redelivery_does_not_duplicate_evidence(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Claims are immutable, so a duplicate delivery must not append a
        second set — that would silently double the evidence a buying score
        is computed from."""
        workspace_id, user_id = await _ingest(session_factory)

        await _normalize_all(session_factory, workspace_id, user_id)
        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            first = (await session.execute(text("SELECT count(*) FROM claim"))).scalar_one()

        await _normalize_all(session_factory, workspace_id, user_id)
        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            second = (await session.execute(text("SELECT count(*) FROM claim"))).scalar_one()

        assert first == second

    async def test_a_claim_cannot_be_updated(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Immutability enforced by the database, not by convention."""
        workspace_id, user_id = await _ingest(session_factory)
        await _normalize_all(session_factory, workspace_id, user_id)

        with pytest.raises(Exception) as exc_info:
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=user_id
            ) as session:
                await session.execute(text("UPDATE claim SET provider = 'tampered'"))

        assert "permission denied" in str(exc_info.value).lower()

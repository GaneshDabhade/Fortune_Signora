"""The provider sync background task.

A sync makes paged network calls to a third party and can take minutes, so
it runs in a worker rather than a request (Principle 13). This asserts the
boundary behaves: it reconstructs domain types from primitives, scopes the
session, and reports an outcome the caller can act on.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.provider_platform.domain.provider import (
    ProviderCapability,
    ProviderName,
    ProviderRegistry,
)
from modules.provider_platform.interface.tasks import run_provider_sync
from modules.workspace_tenancy.application.use_cases import CreateWorkspaceInput
from modules.workspace_tenancy.infrastructure.composition import build_use_cases
from signora_platform.db import user_scoped_session
from tests.integration.test_provider_ingestion import _adapter
from tests.slugs import test_slug as _test_slug

pytestmark = pytest.mark.integration


async def _workspace(factory: async_sessionmaker[AsyncSession]) -> str:
    user_id = uuid4()
    async with user_scoped_session(factory, user_id=user_id) as session:
        result = await build_use_cases(session).create_workspace.execute(
            CreateWorkspaceInput(name="Task", slug=_test_slug("Task"), created_by=user_id), correlation_id=uuid4()
        )
        return str(result.workspace.id)


def _ctx(session_factory: async_sessionmaker[AsyncSession]) -> dict[str, object]:
    registry = ProviderRegistry()
    registry.register(_adapter())
    return {"session_factory": session_factory, "provider_registry": registry}


class TestProviderSyncTask:
    async def test_runs_a_sync_and_reports_its_outcome(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        workspace_id = await _workspace(session_factory)

        result = await run_provider_sync(
            _ctx(session_factory),
            workspace_id=workspace_id,
            provider=ProviderName.APOLLO.value,
            capability=ProviderCapability.COMPANY_ENRICHMENT.value,
            subject="acme-corp",
            correlation_id=str(uuid4()),
        )

        assert result["status"] == "completed"
        assert result["records_stored"] >= 1
        assert result["retryable"] is False

    async def test_a_failure_is_reported_rather_than_raised(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """The sync recorded its own outcome and published an event.
        Raising would additionally trigger ARQ's retry, which is correct
        only for transient failures — a decision belonging to whoever knows
        the failure kind, not to this boundary."""
        from signora_platform.simulation import FaultKind, FaultProfile, FaultRule

        workspace_id = await _workspace(session_factory)
        registry = ProviderRegistry()
        registry.register(_adapter(faults=FaultProfile(rules=(FaultRule(kind=FaultKind.TIMEOUT),))))
        ctx = {"session_factory": session_factory, "provider_registry": registry}

        result = await run_provider_sync(
            ctx,
            workspace_id=workspace_id,
            provider=ProviderName.APOLLO.value,
            capability=ProviderCapability.COMPANY_ENRICHMENT.value,
            subject="acme-corp",
            correlation_id=str(uuid4()),
        )

        assert result["status"] == "failed"
        assert result["retryable"] is True, "a transient failure must be retryable"

    async def test_an_unregistered_provider_fails_loudly(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        from modules.provider_platform.domain.provider import ProviderPermanentError

        workspace_id = await _workspace(session_factory)

        with pytest.raises(ProviderPermanentError, match="no adapter registered"):
            await run_provider_sync(
                _ctx(session_factory),
                workspace_id=workspace_id,
                provider=ProviderName.BOMBORA.value,
                capability=ProviderCapability.BEHAVIOURAL_INTENT.value,
                subject="acme-corp",
                correlation_id=str(uuid4()),
            )

"""Background task entry point for provider syncs.

A sync is dispatched to a worker, never run inside a request: it makes
paged network calls to a third party and can take minutes (CLAUDE.md §7,
Principle 13).

This is the composition boundary — the only place that decides *which*
adapter runs. Everything below receives a `ProviderAdapter` and cannot
tell what is behind it.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from modules.provider_platform.application.run_sync import (
    RunProviderSync,
    RunProviderSyncInput,
)
from modules.provider_platform.domain.provider import (
    ProviderCapability,
    ProviderName,
    ProviderRegistry,
)
from modules.provider_platform.infrastructure.composition import build_run_sync
from signora_platform.db import tenant_scoped_session
from signora_platform.event_bus import PostgresOutboxEventPublisher
from signora_platform.observability import get_logger, logging_context

logger = get_logger(__name__)

#: Syncs run without an acting user. Matches the repository's system
#: identity so machine writes are attributable to a machine.
SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


async def run_provider_sync(
    ctx: dict[str, Any],
    *,
    workspace_id: str,
    provider: str,
    capability: str,
    subject: str,
    correlation_id: str,
) -> dict[str, Any]:
    """ARQ task: run one sync for one workspace.

    Arguments are primitives because ARQ serialises them through Redis. The
    task reconstructs domain types at the boundary rather than pushing
    that on every caller.
    """
    registry: ProviderRegistry = ctx["provider_registry"]
    workspace = UUID(workspace_id)
    correlation = UUID(correlation_id)
    adapter = registry.get(ProviderName(provider))

    with logging_context(correlation_id=correlation, workspace_id=workspace):
        async with tenant_scoped_session(
            ctx["session_factory"], workspace_id=workspace, user_id=SYSTEM_USER_ID
        ) as session:
            use_case: RunProviderSync = build_run_sync(
                session, adapter=adapter, publisher=PostgresOutboxEventPublisher()
            )
            result = await use_case.execute(
                RunProviderSyncInput(
                    workspace_id=workspace,
                    capability=ProviderCapability(capability),
                    subject=subject,
                ),
                correlation_id=correlation,
            )

        logger.info(
            "provider sync finished",
            extra={
                "sync_id": str(result.sync.id),
                "provider": provider,
                "status": result.sync.status.value,
                "records_stored": result.records_stored,
                "pages_fetched": result.sync.pages_fetched,
            },
        )

        # Returned rather than raised on failure: the sync recorded its own
        # outcome and published an event. Raising would additionally
        # trigger ARQ's retry, which is correct only for transient
        # failures — and that decision belongs to the caller that knows
        # the failure kind, not to this boundary.
        return {
            "sync_id": str(result.sync.id),
            "status": result.sync.status.value,
            "records_stored": result.records_stored,
            "retryable": result.sync.is_retryable,
        }

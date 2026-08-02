"""Composition root for the Provider Platform.

**The only place that knows a simulator exists.** Selection is by
configuration; every layer below receives a `ProviderAdapter` and cannot
tell what is behind it (AC-21).
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from modules.provider_platform.application.run_sync import RunProviderSync
from modules.provider_platform.domain.provider import ProviderAdapter
from modules.provider_platform.application.ports import SyncReporter
from modules.provider_platform.infrastructure.metrics import build_sync_metrics
from modules.provider_platform.infrastructure.repository import ProviderSyncRepository
from signora_platform.event_bus import EventPublisher


def build_run_sync(
    session: AsyncSession,
    *,
    adapter: ProviderAdapter,
    publisher: EventPublisher,
    reporter: SyncReporter | None = None,
) -> RunProviderSync:
    """**The reporter defaults to the real one.** An observability gap is
    invisible by construction — nothing fails, no test goes red, and the first
    sign is an incident nobody can reconstruct. Making silence the thing you
    have to ask for is the only version that stays true."""
    return RunProviderSync(
        adapter=adapter,
        repository=ProviderSyncRepository(session),
        publisher=publisher,
        session=session,
        reporter=reporter or build_sync_metrics(),
    )

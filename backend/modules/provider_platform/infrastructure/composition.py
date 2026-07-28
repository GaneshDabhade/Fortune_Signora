"""Composition root for the Provider Platform.

**The only place that knows a simulator exists.** Selection is by
configuration; every layer below receives a `ProviderAdapter` and cannot
tell what is behind it (AC-21).
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from modules.provider_platform.application.run_sync import RunProviderSync
from modules.provider_platform.domain.provider import ProviderAdapter
from modules.provider_platform.infrastructure.repository import ProviderSyncRepository
from signora_platform.event_bus import EventPublisher


def build_run_sync(
    session: AsyncSession, *, adapter: ProviderAdapter, publisher: EventPublisher
) -> RunProviderSync:
    return RunProviderSync(
        adapter=adapter,
        repository=ProviderSyncRepository(session),
        publisher=publisher,
        session=session,
    )

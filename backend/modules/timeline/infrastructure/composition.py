"""Wiring for Timeline. The one place that knows the store is SQL-backed."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from modules.timeline.application.ports import EntryStore
from modules.timeline.infrastructure.repository import SqlEntryStore


def build_entry_store(session: AsyncSession) -> EntryStore:
    return SqlEntryStore(session)

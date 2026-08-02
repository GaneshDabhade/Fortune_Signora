"""Wiring for Timeline. The one place that knows the store is SQL-backed."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from modules.timeline.application.ports import EntryStore, FeedReader
from modules.timeline.application.project import ProjectEvent
from modules.timeline.application.queries import TimelineQueries
from modules.timeline.infrastructure.repository import SqlEntryStore


def build_entry_store(session: AsyncSession) -> EntryStore:
    return SqlEntryStore(session)


def build_feed_reader(session: AsyncSession) -> FeedReader:
    return SqlEntryStore(session)


def build_project_event(session: AsyncSession) -> ProjectEvent:
    return ProjectEvent(build_entry_store(session))


def build_timeline_queries(session: AsyncSession) -> TimelineQueries:
    return TimelineQueries(build_feed_reader(session))

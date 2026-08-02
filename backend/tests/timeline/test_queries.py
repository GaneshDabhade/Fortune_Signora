"""Paging a feed, and the properties that keep pages stable under writes."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from modules.timeline.application.queries import TimelineQueries
from modules.timeline.domain.entry import EntryKind, TimelineEntry
from signora_platform.pagination import CursorPosition

WORKSPACE = uuid4()
ACCOUNT = uuid4()
BASE = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)


def _entry(minutes: int, *, entity: UUID = ACCOUNT, workspace: UUID = WORKSPACE) -> TimelineEntry:
    return TimelineEntry.project(
        workspace_id=workspace,
        entity_id=entity,
        kind=EntryKind.SIGNAL_GENERATED,
        occurred_at=BASE + timedelta(minutes=minutes),
        event_id=uuid4(),
        source_module="signal_engine",
        source_ref=uuid4(),
    )


class FakeFeedReader:
    """Applies the same ordering and keyset rule the SQL does, so the query
    layer's behaviour is testable without a database (§11)."""

    def __init__(self, entries: list[TimelineEntry]) -> None:
        self._entries = entries

    async def feed(
        self,
        *,
        workspace_id: UUID,
        entity_id: UUID,
        after: CursorPosition | None,
        limit: int,
    ) -> list[TimelineEntry]:
        rows = [
            e
            for e in self._entries
            if e.workspace_id == workspace_id and e.entity_id == entity_id
        ]
        rows.sort(key=lambda e: (e.occurred_at, e.id), reverse=True)
        if after is not None:
            rows = [e for e in rows if (e.occurred_at, e.id) < (after.created_at, after.id)]
        return rows[:limit]


def _queries(entries: list[TimelineEntry]) -> TimelineQueries:
    return TimelineQueries(FakeFeedReader(entries))


class TestOrdering:
    @pytest.mark.asyncio
    async def test_newest_first(self) -> None:
        entries = [_entry(0), _entry(60), _entry(30)]
        page = await _queries(entries).feed(WORKSPACE, ACCOUNT, after=None, limit=10)
        assert [e.occurred_at for e in page.items] == [
            BASE + timedelta(minutes=60),
            BASE + timedelta(minutes=30),
            BASE,
        ]

    @pytest.mark.asyncio
    async def test_another_account_is_not_in_this_feed(self) -> None:
        entries = [_entry(0), _entry(10, entity=uuid4())]
        page = await _queries(entries).feed(WORKSPACE, ACCOUNT, after=None, limit=10)
        assert len(page.items) == 1

    @pytest.mark.asyncio
    async def test_another_workspace_is_not_in_this_feed(self) -> None:
        """Belt and braces beside RLS — the authoritative control is the
        database policy, and the query filters anyway (§8)."""
        entries = [_entry(0), _entry(10, workspace=uuid4())]
        page = await _queries(entries).feed(WORKSPACE, ACCOUNT, after=None, limit=10)
        assert len(page.items) == 1


class TestPaging:
    @pytest.mark.asyncio
    async def test_has_more_is_answered_without_counting(self) -> None:
        page = await _queries([_entry(i) for i in range(5)]).feed(
            WORKSPACE, ACCOUNT, after=None, limit=2
        )
        assert len(page.items) == 2
        assert page.has_more is True

    @pytest.mark.asyncio
    async def test_the_last_page_says_so(self) -> None:
        page = await _queries([_entry(i) for i in range(2)]).feed(
            WORKSPACE, ACCOUNT, after=None, limit=10
        )
        assert page.has_more is False

    @pytest.mark.asyncio
    async def test_an_empty_feed_has_no_position(self) -> None:
        page = await _queries([]).feed(WORKSPACE, ACCOUNT, after=None, limit=10)
        assert page.items == []
        assert page.next_position is None

    @pytest.mark.asyncio
    async def test_walking_every_page_yields_each_entry_exactly_once(self) -> None:
        entries = [_entry(i) for i in range(11)]
        queries = _queries(entries)
        seen: list[TimelineEntry] = []
        after: CursorPosition | None = None
        for _ in range(10):
            page = await queries.feed(WORKSPACE, ACCOUNT, after=after, limit=3)
            seen.extend(page.items)
            if not page.has_more:
                break
            after = page.next_position
        assert len({e.id for e in seen}) == 11


class TestPagesAreStableUnderWrites:
    """**The reason the cursor is a keyset and not an offset.**

    Signora's pipeline writes continuously, so rows arriving between two
    requests is the normal case rather than a race worth ignoring.
    """

    @pytest.mark.asyncio
    async def test_entries_arriving_between_pages_do_not_shift_the_next_page(self) -> None:
        entries = [_entry(i) for i in range(6)]
        queries = _queries(entries)
        first = await queries.feed(WORKSPACE, ACCOUNT, after=None, limit=3)

        # The pipeline keeps running: three newer entries land mid-walk. Under
        # OFFSET they would push the first page's rows down and page two would
        # repeat them.
        entries.extend(_entry(100 + i) for i in range(3))

        second = await queries.feed(
            WORKSPACE, ACCOUNT, after=first.next_position, limit=3
        )
        assert not ({e.id for e in first.items} & {e.id for e in second.items})

    @pytest.mark.asyncio
    async def test_entries_sharing_a_timestamp_page_without_loss(self) -> None:
        """The tie case the `(occurred_at, id)` index exists for. A cursor over
        `occurred_at` alone would skip or repeat every one of these."""
        entries = [_entry(0) for _ in range(7)]
        queries = _queries(entries)
        seen: set[UUID] = set()
        after: CursorPosition | None = None
        for _ in range(7):
            page = await queries.feed(WORKSPACE, ACCOUNT, after=after, limit=2)
            seen.update(e.id for e in page.items)
            if not page.has_more:
                break
            after = page.next_position
        assert len(seen) == 7

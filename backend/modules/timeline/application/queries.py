"""Reading an account's feed."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from modules.timeline.application.ports import FeedReader
from modules.timeline.domain.entry import TimelineEntry
from signora_platform.pagination import CursorPosition, split_overfetched


@dataclass(frozen=True, slots=True)
class FeedPage:
    items: list[TimelineEntry]
    has_more: bool

    @property
    def next_position(self) -> CursorPosition | None:
        """The keyset position a caller echoes back for the next page.

        **Positions on `(occurred_at, id)`, which is the order the feed is
        stored in and an index enforces.** `CursorPosition` names its first
        field `created_at` because it is the platform's generic sort key, not a
        claim about a column — and paging by anything the pipeline can move
        would let a projection between two requests skip an entry or repeat it.
        Nothing moves `occurred_at`: entries are immutable.
        """
        if not self.items:
            return None
        last = self.items[-1]
        return CursorPosition(created_at=last.occurred_at, id=last.id)


class TimelineQueries:
    """The one question this module exists to answer."""

    def __init__(self, entries: FeedReader) -> None:
        self._entries = entries

    async def feed(
        self,
        workspace_id: UUID,
        entity_id: UUID,
        *,
        after: CursorPosition | None,
        limit: int,
    ) -> FeedPage:
        """*"What has actually happened with this account?"* — newest first.

        **Over-fetches one row to answer `has_more` without a second query.**
        A `COUNT` over a table that grows with every pipeline event is the kind
        of query that is free in a demo and ruinous at ten million rows.
        """
        rows = await self._entries.feed(
            workspace_id=workspace_id, entity_id=entity_id, after=after, limit=limit + 1
        )
        items, has_more = split_overfetched(rows, limit=limit)
        return FeedPage(items=items, has_more=has_more)

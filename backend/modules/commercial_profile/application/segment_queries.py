"""Reading a workspace's segments — the screen that does not exist today.

**The read model was challenged before it was written**, because the first one
is rarely the right one.

### What is in a row, and what is not

A row carries what a customer scans for: **name, state, which products, when it
last changed, and which version it is on.** The criteria are not there. Nobody
reads *"Fintech · US, UK · 100–1000 · only where they already run Salesforce"*
across forty rows — they read names, find the one they meant, and open it. The
criteria travel on the detail read.

### Counts are not precomputed, and that is a decision

*"How many opportunities did this segment produce?"* is the count worth having
and **no module can answer it yet** — nothing consumes an ICP. Precomputing a
count of products would be a stored copy of a joined fact, stale the moment a
version is published, to save a join that costs nothing at this size.

### Paging is on `(created_at, id)`; display order is the client's

**The first draft paged on `(name, id)` and it was wrong** — the platform's
`CursorPosition` is `(datetime, UUID)`, and forcing a name into it would have
been a type lie in a frozen primitive to save the client a `sort()`.

So the keyset is **when the segment was created**, which never changes and is
therefore a stable total order with `id` breaking ties. **Alphabetical is a
display concern** while a workspace has tens of segments, and the client does
it. When lists are long enough that display order and page order must agree,
that is a server-side sort with its own cursor — recorded as a pressure point
rather than built for a load nobody has.

### Archived segments are excluded by default, and never hidden

An archived segment is not deleted and must remain reachable; it is simply not
what somebody means by *"who do we sell to?"*. The filter is a parameter, not a
policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from modules.commercial_profile.domain.segment import SegmentState
from signora_platform.pagination import CursorPosition


@dataclass(frozen=True, slots=True)
class SegmentSummary:
    """One segment, as a list reads it."""

    id: UUID
    name: str
    state: SegmentState
    version: int
    #: **Ids, not names.** Resolving a product to a name is the catalog's, and
    #: a product removed from it must still leave this row readable — the
    #: client resolves and says what is missing, exactly as the ICP editor
    #: already does.
    product_ids: tuple[UUID, ...]
    #: When the segment last changed — a publication or a lifecycle move,
    #: whichever is later. **Derived at read time**; a stored column would be
    #: a second copy of a fact two tables already hold.
    last_changed_at: datetime
    last_changed_by: UUID
    #: The paging key. Never changes, which is what makes a page boundary
    #: stable while somebody else is publishing.
    created_at: datetime


@dataclass(frozen=True, slots=True)
class SegmentPage:
    items: list[SegmentSummary]
    has_more: bool

    @property
    def next_position(self) -> CursorPosition | None:
        """The keyset position a caller echoes back.

        On `created_at`, which nothing moves: a segment's creation is a fact
        about a moment, so a page boundary cannot shift under a publication
        happening between two requests.
        """
        if not self.items:
            return None
        last = self.items[-1]
        return CursorPosition(created_at=last.created_at, id=last.id)


class SegmentReader(Protocol):
    """What the query layer needs from storage, and nothing more."""

    async def page(
        self,
        *,
        workspace_id: UUID,
        include_archived: bool,
        after: CursorPosition | None,
        limit: int,
    ) -> list[SegmentSummary]: ...


class SegmentQueries:
    """*"Who do we sell to?"* — the one question this read model answers."""

    def __init__(self, segments: SegmentReader) -> None:
        self._segments = segments

    async def page(
        self,
        *,
        workspace_id: UUID,
        include_archived: bool = False,
        after: CursorPosition | None = None,
        limit: int = 50,
    ) -> SegmentPage:
        """One page, with `has_more` answered without counting.

        **Reads `limit + 1` and discards the extra.** A `COUNT` over a
        customer's segments is a scan nobody asked for, and *"is there another
        page?"* is the only question the screen actually has.
        """
        rows = await self._segments.page(
            workspace_id=workspace_id,
            include_archived=include_archived,
            after=after,
            limit=limit + 1,
        )
        return SegmentPage(items=rows[:limit], has_more=len(rows) > limit)

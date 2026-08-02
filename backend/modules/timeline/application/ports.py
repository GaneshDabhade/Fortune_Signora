"""The ports Timeline depends on.

**A port belongs to the module that owns the language it represents**
(`CLAUDE.md` §6), so these live in Timeline's own layers and are implemented in
its infrastructure. Nothing here names SQL, a session, or a table.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from modules.timeline.domain.entry import TimelineEntry


class EntryStore(Protocol):
    """Where projected entries are kept.

    **`append` is the only write.** There is no `update` and no `delete`, and
    the absence is the point: a projection that can edit its past is a feed
    nobody can cite, and the entries most worth editing are always the
    inconvenient ones. The grant enforces the same rule at the database
    (migration `0026`), so this is not the only thing standing between an
    engineer and an edited timeline — it is the shape that stops one being
    written by accident.
    """

    async def append(self, entry: TimelineEntry) -> bool:
        """Record `entry`, returning whether it was new.

        **Idempotent by contract, not by hope.** A redelivered event derives an
        entry that already exists; this returns `False` and writes nothing.
        Callers use the answer for observability — *"how much of this replay was
        genuinely new"* — and never to decide correctness.
        """
        ...

    async def feed(
        self, *, workspace_id: UUID, entity_id: UUID, limit: int
    ) -> list[TimelineEntry]:
        """The account's entries, newest first.

        Ordered by `occurred_at` descending with `id` breaking ties, which is
        the total order the feed index exists for.
        """
        ...

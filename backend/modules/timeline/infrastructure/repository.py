"""SQL-backed `EntryStore`."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import desc, select, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from modules.timeline.domain.entry import EntryKind, TimelineEntry
from modules.timeline.infrastructure.models import TimelineEntryModel
from signora_platform.pagination import CursorPosition


class SqlEntryStore:
    """Append-only, and idempotent on the derived entry id."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, entry: TimelineEntry) -> bool:
        # `ON CONFLICT DO NOTHING` rather than a read-then-write: two workers
        # handling the same redelivered event would both find nothing and both
        # insert, and the race is only visible under the load that makes it
        # matter. The database already refuses the duplicate — asking it to say
        # so is cheaper and correct under concurrency.
        #
        # **No arbiter index, and that is the fix rather than an omission.**
        # This named `index_elements=["id"]`, which arbitrates on the primary
        # key alone — and `timeline_entry` carries TWO unique indexes, the
        # second on `event_id`. `id` is `uuid5(NAMESPACE, event_id)`, so the
        # two agree on every row and the narrower arbiter looked equivalent.
        #
        # It is not equivalent under the concurrency this comment was written
        # for. Speculative insertion arbitrates only on the index it was given:
        # a concurrent writer's row can be invisible to the `id` check and then
        # present when the `event_id` index is written, and PostgreSQL raises
        # for the index it was not told to arbitrate on. The comment above
        # claimed correctness under concurrency while guarding one of the two
        # ways this row can already exist.
        #
        # Bare `DO NOTHING` ignores *any* unique violation, which is what
        # "append this unless it is already here" actually means — and it is
        # what CLAUDE.md §9 requires: consumers are idempotent on `event_id`,
        # not on a key derived from it. Measured 2026-08-20 (B-294): the
        # Playground seeder's in-process pipeline and a live `timeline.project`
        # worker wrote the same event 1.07s apart, and the seed aborted.
        statement = (
            insert(TimelineEntryModel)
            .values(
                id=entry.id,
                workspace_id=entry.workspace_id,
                entity_id=entry.entity_id,
                kind=entry.kind.value,
                occurred_at=entry.occurred_at,
                event_id=entry.event_id,
                source_module=entry.source_module,
                source_ref=entry.source_ref,
                detail=dict(entry.detail),
            )
            .on_conflict_do_nothing()
            .returning(TimelineEntryModel.id)
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none() is not None

    async def feed(
        self,
        *,
        workspace_id: UUID,
        entity_id: UUID,
        after: CursorPosition | None,
        limit: int,
    ) -> list[TimelineEntry]:
        # `workspace_id` is filtered explicitly even though RLS is the
        # authoritative control — defence in depth, per §8.
        statement = (
            select(TimelineEntryModel)
            .where(
                TimelineEntryModel.workspace_id == workspace_id,
                TimelineEntryModel.entity_id == entity_id,
            )
            .order_by(desc(TimelineEntryModel.occurred_at), desc(TimelineEntryModel.id))
            .limit(limit)
        )
        if after is not None:
            # Row-wise comparison rather than `occurred_at < x OR (= x AND
            # id < y)`: one tuple predicate the planner can drive straight off
            # the `(workspace, entity, occurred_at, id)` index, and one
            # expression that cannot be got subtly wrong at a tie.
            statement = statement.where(
                tuple_(TimelineEntryModel.occurred_at, TimelineEntryModel.id)
                < (after.created_at, after.id)
            )
        rows = (await self._session.execute(statement)).scalars().all()
        return [
            TimelineEntry(
                id=row.id,
                workspace_id=row.workspace_id,
                entity_id=row.entity_id,
                kind=EntryKind(row.kind),
                occurred_at=row.occurred_at,
                event_id=row.event_id,
                source_module=row.source_module,
                source_ref=row.source_ref,
                detail=dict(row.detail),
            )
            for row in rows
        ]

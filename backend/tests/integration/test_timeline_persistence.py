"""Timeline against a real PostgreSQL 17, as the least-privilege role.

**Two paths that had no test between them, and both are load-bearing.**

`interface/handlers.py` is how every entry a customer will ever read gets into
the feed; it was at 0%. `infrastructure/repository.py` holds the keyset
predicate, and the unit suite exercised paging against a fake that
*reimplements the same rule in Python* — so if the SQL and the fake ever
disagreed, the fake is the one that would pass. That is the failure mode a
double cannot see, and it is why [B-024](../../../docs/BUGS.md) named these
files rather than a percentage.

What is asserted here is behaviour the fake cannot produce: redelivery losing
the race against a unique index, ties broken identically by PostgreSQL's
collation and by the cursor, and RLS refusing another organization's feed.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.timeline.application.queries import TimelineQueries
from modules.timeline.domain.entry import EntryKind, TimelineEntry
from modules.timeline.infrastructure.composition import (
    build_entry_store,
    build_project_event,
    build_timeline_queries,
)
from modules.timeline.interface.handlers import CONSUMER_NAME, project_to_timeline
from signora_platform.db import tenant_scoped_session
from signora_platform.event_bus import EventEnvelope

pytestmark = pytest.mark.integration

BASE = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)
ACTOR = UUID("22222222-2222-4222-8222-222222222222")


async def _entity(
    session_factory: async_sessionmaker[AsyncSession], workspace_id: UUID
) -> UUID:
    """A real `entity` row, because `timeline_entry.entity_id` references one.

    Written with raw SQL rather than through Knowledge Graph's repository: this
    is Timeline's suite, and importing another module's infrastructure to build
    a fixture is exactly the reach across a boundary the architecture forbids.
    """
    entity_id = uuid4()
    async with tenant_scoped_session(
        session_factory, workspace_id=workspace_id, user_id=ACTOR
    ) as session:
        await session.execute(
            text(
                "INSERT INTO entity (id, workspace_id, kind, created_by, updated_by) "
                "VALUES (:id, :ws, 'company', :actor, :actor)"
            ),
            {"id": entity_id, "ws": workspace_id, "actor": ACTOR},
        )
        await session.commit()
    return entity_id


def _entry(
    workspace_id: UUID,
    entity_id: UUID,
    *,
    minutes: int = 0,
    occurred_at: datetime | None = None,
    event_id: UUID | None = None,
) -> TimelineEntry:
    return TimelineEntry.project(
        workspace_id=workspace_id,
        entity_id=entity_id,
        kind=EntryKind.SIGNAL_GENERATED,
        occurred_at=occurred_at or BASE + timedelta(minutes=minutes),
        event_id=event_id or uuid4(),
        source_module="signal_engine",
        source_ref=uuid4(),
        detail={"signal_type": "hiring_surge", "relevance": "high"},
    )


def _envelope(workspace_id: UUID, entity_id: UUID, **payload: Any) -> EventEnvelope:
    return EventEnvelope(
        event_id=uuid4(),
        event_type="signal.generated",
        event_version=1,
        workspace_id=workspace_id,
        correlation_id=uuid4(),
        causation_id=uuid4(),
        occurred_at=BASE,
        producer_module="signal_engine",
        payload={
            "entity_id": str(entity_id),
            "signal_id": str(uuid4()),
            "signal_type": "hiring_surge",
            "relevance": "high",
            **payload,
        },
    )


class TestTheProjectionActuallyLands:
    """The consumption path — how everything a customer reads gets there."""

    async def test_an_event_becomes_a_row_a_customer_can_read(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        workspace = uuid4()
        entity_id = await _entity(session_factory, workspace)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            await project_to_timeline(
                _envelope(workspace, entity_id), project=build_project_event(session)
            )
            await session.commit()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            page = await build_timeline_queries(session).feed(
                workspace_id=workspace, entity_id=entity_id, after=None, limit=10
            )

        assert len(page.items) == 1
        assert page.items[0].kind is EntryKind.SIGNAL_GENERATED
        assert page.items[0].detail["signal_type"] == "hiring_surge"

    async def test_an_event_timeline_does_not_project_writes_nothing(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Most of the bus is not this module's business, and silence is the
        correct response rather than an error."""
        workspace = uuid4()
        entity_id = await _entity(session_factory, workspace)
        envelope = _envelope(workspace, entity_id)
        unmapped = EventEnvelope(
            event_id=envelope.event_id,
            event_type="provider.sync_completed",
            event_version=1,
            workspace_id=workspace,
            correlation_id=envelope.correlation_id,
            causation_id=envelope.causation_id,
            occurred_at=BASE,
            producer_module="provider_platform",
            payload=envelope.payload,
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            await project_to_timeline(unmapped, project=build_project_event(session))
            await session.commit()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            page = await build_timeline_queries(session).feed(
                workspace_id=workspace, entity_id=entity_id, after=None, limit=10
            )

        assert page.items == []

    async def test_a_second_writer_of_one_event_is_absorbed_not_refused(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """**`timeline_entry` has TWO unique indexes and `append` arbitrated on
        one** — [B-294](../../../docs/BUGS.md).

        The primary key is `uuid5(NAMESPACE, event_id)`, so `id` and `event_id`
        agree on every row this module writes and `ON CONFLICT (id)` looked
        equivalent to guarding both. It is not: speculative insertion
        arbitrates only on the index it is given, so a row that is invisible to
        the `id` check and present when the `event_id` index is written raises
        `timeline_entry_event_id_key` instead of doing nothing.

        **The test forces the state that concurrency produces**, because the
        race itself is not reproducible on demand: a row already holding this
        `event_id` under a different `id`. With an `id` arbiter this raises;
        with none it is absorbed and reported as `False`, which is what
        `CLAUDE.md` §9 means by *idempotent on `event_id`*.

        Measured in the wild: the Playground seeder's in-process pipeline and a
        live `timeline.project` worker wrote one event 1.07s apart, and the
        seed aborted mid-way.
        """
        workspace = uuid4()
        entity_id = await _entity(session_factory, workspace)
        entry = _entry(workspace, entity_id)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            # The other writer, landing first under an id this module would
            # not derive — standing in for a row the arbiter cannot see yet.
            await session.execute(
                text(
                    "INSERT INTO timeline_entry (id, workspace_id, entity_id, kind,"
                    " occurred_at, event_id, source_module, source_ref, detail)"
                    " VALUES (:id, :w, :e, :k, :at, :ev, :m, :ref, '{}'::jsonb)"
                ),
                {
                    "id": uuid4(),
                    "w": workspace,
                    "e": entity_id,
                    "k": entry.kind.value,
                    "at": entry.occurred_at,
                    "ev": entry.event_id,
                    "m": entry.source_module,
                    "ref": entry.source_ref,
                },
            )
            await session.commit()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            wrote = await build_entry_store(session).append(entry)
            await session.commit()

        # Absorbed, and honest about not having written.
        assert wrote is False

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            page = await build_timeline_queries(session).feed(
                workspace_id=workspace, entity_id=entity_id, after=None, limit=10
            )

        # One event, one entry — never two.
        assert len(page.items) == 1

    async def test_redelivery_writes_once_and_the_second_says_so(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """**The property a fake cannot produce.** `ON CONFLICT DO NOTHING`
        rather than read-then-write, because two workers handling one redelivery
        would both find nothing and both insert — a race visible only under the
        load that makes it matter."""
        workspace = uuid4()
        entity_id = await _entity(session_factory, workspace)
        envelope = _envelope(workspace, entity_id)

        writes: list[bool] = []
        for _ in range(2):
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace, user_id=ACTOR
            ) as session:
                entry = _entry(workspace, entity_id, event_id=envelope.event_id)
                writes.append(await build_entry_store(session).append(entry))
                await session.commit()

        assert writes == [True, False]

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            page = await build_timeline_queries(session).feed(
                workspace_id=workspace, entity_id=entity_id, after=None, limit=10
            )

        assert len(page.items) == 1

    async def test_the_consumer_name_is_the_idempotency_ledger_key(self) -> None:
        """Renaming it would re-project every historical event on the next
        replay. Asserted so a rename is a failing test rather than a surprise."""
        assert CONSUMER_NAME == "timeline.project"


class TestPagingIsTheDatabasesNotThePythons:
    """The unit suite pages against a fake that reimplements this rule. These
    run the rule that actually ships."""

    async def test_newest_first_across_a_real_index(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        workspace = uuid4()
        entity_id = await _entity(session_factory, workspace)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            store = build_entry_store(session)
            for minutes in (0, 20, 10):
                await store.append(_entry(workspace, entity_id, minutes=minutes))
            await session.commit()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            page = await build_timeline_queries(session).feed(
                workspace_id=workspace, entity_id=entity_id, after=None, limit=10
            )

        assert [e.occurred_at for e in page.items] == [
            BASE + timedelta(minutes=20),
            BASE + timedelta(minutes=10),
            BASE,
        ]

    async def test_walking_every_page_yields_each_entry_exactly_once(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        workspace = uuid4()
        entity_id = await _entity(session_factory, workspace)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            store = build_entry_store(session)
            for minutes in range(7):
                await store.append(_entry(workspace, entity_id, minutes=minutes))
            await session.commit()

        seen: list[UUID] = []
        cursor = None
        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            queries: TimelineQueries = build_timeline_queries(session)
            while True:
                page = await queries.feed(
                    workspace_id=workspace, entity_id=entity_id, after=cursor, limit=3
                )
                seen.extend(e.id for e in page.items)
                if not page.has_more:
                    break
                cursor = page.next_position

        assert len(seen) == 7
        assert len(set(seen)) == 7

    async def test_entries_sharing_a_timestamp_page_without_loss(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """**Where a non-total order silently drops rows.** Three entries at one
        instant, read two at a time: the tuple comparison must break the tie the
        same way the `ORDER BY` does, and only PostgreSQL can prove it does."""
        workspace = uuid4()
        entity_id = await _entity(session_factory, workspace)
        same_moment = BASE + timedelta(minutes=5)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            store = build_entry_store(session)
            for _ in range(3):
                await store.append(_entry(workspace, entity_id, occurred_at=same_moment))
            await session.commit()

        seen: list[UUID] = []
        cursor = None
        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            queries = build_timeline_queries(session)
            while True:
                page = await queries.feed(
                    workspace_id=workspace, entity_id=entity_id, after=cursor, limit=2
                )
                seen.extend(e.id for e in page.items)
                if not page.has_more:
                    break
                cursor = page.next_position

        assert len(set(seen)) == 3

    async def test_has_more_is_answered_without_counting(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        workspace = uuid4()
        entity_id = await _entity(session_factory, workspace)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            store = build_entry_store(session)
            for minutes in range(4):
                await store.append(_entry(workspace, entity_id, minutes=minutes))
            await session.commit()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=ACTOR
        ) as session:
            queries = build_timeline_queries(session)
            first = await queries.feed(
                workspace_id=workspace, entity_id=entity_id, after=None, limit=2
            )
            last = await queries.feed(
                workspace_id=workspace,
                entity_id=entity_id,
                after=first.next_position,
                limit=5,
            )

        assert first.has_more is True
        assert last.has_more is False


class TestAnotherOrganizationsFeedIsNotReachable:
    async def test_rls_refuses_a_feed_read_under_the_wrong_workspace(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """The entity id is not a secret — a caller who guessed one must still
        get nothing, and RLS is what guarantees that rather than the filter."""
        owner, intruder = uuid4(), uuid4()
        entity_id = await _entity(session_factory, owner)

        async with tenant_scoped_session(
            session_factory, workspace_id=owner, user_id=ACTOR
        ) as session:
            await build_entry_store(session).append(_entry(owner, entity_id))
            await session.commit()

        async with tenant_scoped_session(
            session_factory, workspace_id=intruder, user_id=ACTOR
        ) as session:
            page = await build_timeline_queries(session).feed(
                workspace_id=intruder, entity_id=entity_id, after=None, limit=10
            )

        assert page.items == []

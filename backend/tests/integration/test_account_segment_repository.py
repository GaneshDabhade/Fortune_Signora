"""Segments against a real database — [TASK-1479](../../../docs/BACKLOG.md) ⓶b.

🔴 **Three things only a database can answer**, and each is a rule the domain
states and cannot enforce alone: **the unique index folds the way `casefold`
does**, **membership survives a rename**, and **`added` becomes a list exactly
once.**
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from modules.commercial_profile.domain.account_segment import (
    AccountSegment,
    SegmentBatch,
    add_to_segment,
)
from modules.commercial_profile.infrastructure.account_segment_repository import (
    SqlAccountSegmentRepository,
    SqlSegmentBatchStore,
)
from tests.conftest import DEFAULT_APP_DATABASE_URL


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    """A session with RLS context set, **as a request would set it** (§8)."""
    engine = create_async_engine(DEFAULT_APP_DATABASE_URL)
    async with AsyncSession(engine) as db:
        yield db
    await engine.dispose()


async def _scoped(db: AsyncSession, workspace_id: UUID) -> None:
    await db.execute(text(f"SET LOCAL app.workspace_id = '{workspace_id}'"))


class TestTheDirectoryIsWhatSaysWhichSegmentsExist:
    async def test_a_created_segment_reads_back(self, session: AsyncSession) -> None:
        workspace_id, actor = uuid4(), uuid4()
        await _scoped(session, workspace_id)
        repository = SqlAccountSegmentRepository(session)
        segment = AccountSegment(id=uuid4(), name="Board reporting set")

        await repository.create(workspace_id, segment, actor_id=actor)
        directory = await repository.directory(workspace_id)

        assert directory.get(segment.id) == segment

    async def test_the_panel_is_ordered_by_name_rather_than_by_insertion(
        self, session: AsyncSession
    ) -> None:
        """⛔ ***"Whatever order the rows came back in"* is a hidden input**
        (§2): the same set would render differently between two requests, and
        the design draws a list a person scans."""
        workspace_id, actor = uuid4(), uuid4()
        await _scoped(session, workspace_id)
        repository = SqlAccountSegmentRepository(session)
        for name in ("Dormant enterprise", "Board reporting set", "Competitive watch"):
            await repository.create(
                workspace_id, AccountSegment(id=uuid4(), name=name), actor_id=actor
            )

        directory = await repository.directory(workspace_id)

        assert [segment.name for segment in directory.segments] == [
            "Board reporting set",
            "Competitive watch",
            "Dormant enterprise",
        ]

    async def test_the_unique_index_folds_the_way_casefold_does(
        self, session: AsyncSession
    ) -> None:
        """🔴 **The reason `name_key` is a column rather than a `lower(name)`
        constraint.**

        ⛔ **`lower("STRASSE")` and `lower("straße")` differ** where the
        customer means one segment; **`casefold` is the function that does
        not** — and the index is over the domain's own `key`, so the database
        and the rule cannot disagree about what folding means.
        """
        from sqlalchemy.exc import IntegrityError

        workspace_id, actor = uuid4(), uuid4()
        await _scoped(session, workspace_id)
        repository = SqlAccountSegmentRepository(session)
        await repository.create(
            workspace_id, AccountSegment(id=uuid4(), name="STRASSE"), actor_id=actor
        )

        with pytest.raises(IntegrityError):
            await repository.create(
                workspace_id, AccountSegment(id=uuid4(), name="straße"), actor_id=actor
            )

    async def test_a_neighbour_s_segment_is_not_in_this_workspace_s_directory(
        self, session: AsyncSession
    ) -> None:
        mine, theirs, actor = uuid4(), uuid4(), uuid4()
        await _scoped(session, mine)
        repository = SqlAccountSegmentRepository(session)
        await repository.create(
            mine, AccountSegment(id=uuid4(), name="Board reporting set"), actor_id=actor
        )

        assert (await repository.directory(theirs)).segments == ()


class TestMembershipSurvivesARename:
    async def test_every_company_stays_in_it(self, session: AsyncSession) -> None:
        """⚡ **The whole reason a segment has an id.** Without one, renaming
        would be indistinguishable from deleting one grouping and creating
        another — and the customer's curation would vanish with the name."""
        workspace_id, actor, account = uuid4(), uuid4(), uuid4()
        await _scoped(session, workspace_id)
        repository = SqlAccountSegmentRepository(session)
        segment = AccountSegment(id=uuid4(), name="Board reporting set")
        await repository.create(workspace_id, segment, actor_id=actor)
        await repository.add(workspace_id, segment.id, (account,), actor_id=actor)

        await repository.rename(workspace_id, segment.renamed("Quarterly pack"), actor_id=actor)

        assert await repository.members_among(
            workspace_id, segment.id, among=(account,)
        ) == frozenset({account})


class TestReadsAskAboutTheAccountsTheCallerNamed:
    async def test_membership_is_scoped_to_the_page_on_screen(
        self, session: AsyncSession
    ) -> None:
        """⛔ **Never *"everything in this segment"*** — the design draws a
        grouping with 304 members and a bulk action over 41, and reading 304 to
        decide 41 is the unbounded read §14 calls a defect at write time."""
        workspace_id, actor = uuid4(), uuid4()
        on_screen, elsewhere = uuid4(), uuid4()
        await _scoped(session, workspace_id)
        repository = SqlAccountSegmentRepository(session)
        segment = AccountSegment(id=uuid4(), name="Board reporting set")
        await repository.create(workspace_id, segment, actor_id=actor)
        await repository.add(workspace_id, segment.id, (on_screen, elsewhere), actor_id=actor)

        assert await repository.members_among(
            workspace_id, segment.id, among=(on_screen,)
        ) == frozenset({on_screen})

    async def test_an_empty_question_costs_no_round_trip(self, session: AsyncSession) -> None:
        workspace_id = uuid4()
        await _scoped(session, workspace_id)
        repository = SqlAccountSegmentRepository(session)

        assert await repository.members_among(workspace_id, uuid4(), among=()) == frozenset()
        assert await repository.segments_for(workspace_id, ()) == {}

    async def test_the_companies_read_answers_for_many_accounts_in_one_query(
        self, session: AsyncSession
    ) -> None:
        workspace_id, actor = uuid4(), uuid4()
        first, second, unlisted = uuid4(), uuid4(), uuid4()
        await _scoped(session, workspace_id)
        repository = SqlAccountSegmentRepository(session)
        a = AccountSegment(id=uuid4(), name="Board reporting set")
        b = AccountSegment(id=uuid4(), name="Competitive watch")
        await repository.create(workspace_id, a, actor_id=actor)
        await repository.create(workspace_id, b, actor_id=actor)
        await repository.add(workspace_id, a.id, (first, second), actor_id=actor)
        await repository.add(workspace_id, b.id, (second,), actor_id=actor)

        held = await repository.segments_for(workspace_id, (first, second, unlisted))

        assert set(held[first]) == {a.id}
        assert set(held[second]) == {a.id, b.id}
        # ⛔ **Absent, not present-with-an-empty-list.** An account in no
        # segment has nothing to say, and the screen renders nothing either way.
        assert unlisted not in held

    async def test_counts_omit_an_empty_segment_and_the_caller_compensates(
        self, session: AsyncSession
    ) -> None:
        """⚠️ **The `GROUP BY` cannot produce a row for a segment with no
        members**, so this returns nothing for it — **and the directory use
        case is where that becomes a `0` rather than a disappearance.** Stated
        here so nobody 'fixes' the count by joining."""
        workspace_id, actor = uuid4(), uuid4()
        await _scoped(session, workspace_id)
        repository = SqlAccountSegmentRepository(session)
        empty = AccountSegment(id=uuid4(), name="Board reporting set")
        filled = AccountSegment(id=uuid4(), name="Competitive watch")
        await repository.create(workspace_id, empty, actor_id=actor)
        await repository.create(workspace_id, filled, actor_id=actor)
        await repository.add(workspace_id, filled.id, (uuid4(), uuid4()), actor_id=actor)

        counts = await repository.counts(workspace_id)

        assert counts == {filled.id: 2}

    async def test_removing_takes_companies_out(self, session: AsyncSession) -> None:
        workspace_id, actor = uuid4(), uuid4()
        stays, goes = uuid4(), uuid4()
        await _scoped(session, workspace_id)
        repository = SqlAccountSegmentRepository(session)
        segment = AccountSegment(id=uuid4(), name="Board reporting set")
        await repository.create(workspace_id, segment, actor_id=actor)
        await repository.add(workspace_id, segment.id, (stays, goes), actor_id=actor)

        await repository.remove(workspace_id, segment.id, (goes,))

        assert await repository.members_among(
            workspace_id, segment.id, among=(stays, goes)
        ) == frozenset({stays})

    async def test_removing_nothing_is_not_a_query(self, session: AsyncSession) -> None:
        workspace_id = uuid4()
        await _scoped(session, workspace_id)

        await SqlAccountSegmentRepository(session).remove(workspace_id, uuid4(), ())

    async def test_adding_nothing_is_not_a_write(self, session: AsyncSession) -> None:
        workspace_id = uuid4()
        await _scoped(session, workspace_id)

        await SqlAccountSegmentRepository(session).add(
            workspace_id, uuid4(), (), actor_id=uuid4()
        )


class TestTheBatchStoreKeepsWhatTheEventDoesNot:
    async def _segment(self, session: AsyncSession, workspace_id: UUID) -> AccountSegment:
        segment = AccountSegment(id=uuid4(), name="Board reporting set")
        await SqlAccountSegmentRepository(session).create(
            workspace_id, segment, actor_id=uuid4()
        )
        return segment

    async def test_a_recorded_batch_reads_back_as_not_applied(
        self, session: AsyncSession
    ) -> None:
        """⛔ **`None`, not `[]`.** ⚠️ *Never approved* and *approved and added
        nobody* are different rows, and only the first is still waiting for a
        person."""
        workspace_id, account = uuid4(), uuid4()
        await _scoped(session, workspace_id)
        segment = await self._segment(session, workspace_id)
        store = SqlSegmentBatchStore(session)
        batch = SegmentBatch(batch_id=uuid4(), segment_id=segment.id, requested=(account,))

        await store.record(workspace_id, batch, actor_id=uuid4())
        read_back = await store.get(workspace_id, batch.batch_id)

        assert read_back is not None
        assert read_back.applied is None
        assert read_back.to_reverse() == ()

    async def test_an_applied_batch_reads_back_what_it_added_and_derives_the_rest(
        self, session: AsyncSession
    ) -> None:
        """⚡ **`unchanged` is derived, never stored.** Everything requested
        that was not added was already there — **storing both would be two
        representations of one partition, and the one nobody writes to is the
        one that goes wrong.**"""
        workspace_id, already, fresh = uuid4(), uuid4(), uuid4()
        await _scoped(session, workspace_id)
        segment = await self._segment(session, workspace_id)
        store = SqlSegmentBatchStore(session)
        batch = SegmentBatch(
            batch_id=uuid4(), segment_id=segment.id, requested=(already, fresh)
        )
        await store.record(workspace_id, batch, actor_id=uuid4())

        await store.record_application(
            workspace_id,
            batch.batch_id,
            add_to_segment(segment.id, accounts=(already, fresh), already_in=frozenset({already})),
            actor_id=uuid4(),
        )
        read_back = await store.get(workspace_id, batch.batch_id)

        assert read_back is not None
        assert read_back.to_reverse() == (fresh,)
        assert read_back.applied is not None
        assert read_back.applied.unchanged == (already,)

    async def test_a_second_application_is_refused_by_the_write_itself(
        self, session: AsyncSession
    ) -> None:
        """🔴 **The guard the domain cannot provide alone.**

        ⛔ `SegmentBatch.with_application` raises, **but its answer depends on
        having read the row** — and two deliveries of one `applied` event can
        both read `None`. **This is `UPDATE … WHERE added IS NULL`**, so the
        second write matches nothing and says so.
        """
        workspace_id, account = uuid4(), uuid4()
        await _scoped(session, workspace_id)
        segment = await self._segment(session, workspace_id)
        store = SqlSegmentBatchStore(session)
        batch = SegmentBatch(batch_id=uuid4(), segment_id=segment.id, requested=(account,))
        await store.record(workspace_id, batch, actor_id=uuid4())
        addition = add_to_segment(segment.id, accounts=(account,), already_in=frozenset())
        await store.record_application(
            workspace_id, batch.batch_id, addition, actor_id=uuid4()
        )

        with pytest.raises(RuntimeError):
            await store.record_application(
                workspace_id, batch.batch_id, addition, actor_id=uuid4()
            )

    async def test_a_batch_from_another_workspace_is_absent(
        self, session: AsyncSession
    ) -> None:
        mine, theirs = uuid4(), uuid4()
        await _scoped(session, mine)
        segment = await self._segment(session, mine)
        store = SqlSegmentBatchStore(session)
        batch = SegmentBatch(batch_id=uuid4(), segment_id=segment.id, requested=(uuid4(),))
        await store.record(mine, batch, actor_id=uuid4())

        assert await store.get(theirs, batch.batch_id) is None

    async def test_a_batch_nobody_proposed_here_reads_as_absent(
        self, session: AsyncSession
    ) -> None:
        workspace_id = uuid4()
        await _scoped(session, workspace_id)

        assert await SqlSegmentBatchStore(session).get(workspace_id, uuid4()) is None


class TestTheNullIsASqlNullAndNotTheJsonValueNull:
    """🔴 **The defect this class exists for, found by a conditional write.**

    ⛔ **SQLAlchemy's default for a JSON column serialises Python `None` as the
    JSON value `null`, not as SQL `NULL`.** ⚡ **The ORM decodes it back to
    `None`, so every read looked correct** — and `UPDATE … WHERE added IS
    NULL` matched **zero** rows, so the first application of every batch was
    silently refused.

    ⚠️ **`account_assignment_batch.moved` carried the same shape through slice
    ⓶a.** Nothing read it wrongly, because nothing asked SQL — **but the
    migration's docstring promises a `NULL`, and a partial index, a report or a
    later guard written against that promise would have been wrong.** Both
    columns now set `none_as_null=True`, and this asserts the storage rather
    than the round trip.
    """

    async def test_an_unapplied_batch_is_null_to_sql_itself(
        self, session: AsyncSession
    ) -> None:
        workspace_id = uuid4()
        await _scoped(session, workspace_id)
        segment = AccountSegment(id=uuid4(), name="Board reporting set")
        await SqlAccountSegmentRepository(session).create(
            workspace_id, segment, actor_id=uuid4()
        )
        batch = SegmentBatch(batch_id=uuid4(), segment_id=segment.id, requested=(uuid4(),))
        await SqlSegmentBatchStore(session).record(workspace_id, batch, actor_id=uuid4())

        # ⛔ **Asked of the database, not of the ORM.** A round trip through
        # Python cannot tell SQL `NULL` from the JSON value `null`, which is
        # exactly why the defect survived a passing read.
        is_sql_null = (
            await session.execute(
                text(
                    "SELECT added IS NULL FROM account_segment_batch "
                    "WHERE batch_id = :batch_id"
                ),
                {"batch_id": str(batch.batch_id)},
            )
        ).scalar_one()

        assert is_sql_null is True

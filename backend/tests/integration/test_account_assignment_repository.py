"""Owner and CSM against a real database — [TASK-1479](../../../docs/BACKLOG.md) slice ⓶.

🔴 **The reversal is the subject**, and specifically the case that is normally
missed: **an account that had no owner before must end with no owner.**
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from modules.commercial_profile.domain.account_assignment import (
    AccountRole,
    AssignmentBatch,
    Reassignment,
)
from modules.commercial_profile.infrastructure.assignment_repository import (
    SqlAccountAssignmentRepository,
    SqlAssignmentBatchStore,
)
from tests.conftest import DEFAULT_APP_DATABASE_URL


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    """A session with RLS context set, **as a request would set it** — the same
    fixture the tag repository's tests use, for the same reason (§8)."""
    engine = create_async_engine(DEFAULT_APP_DATABASE_URL)
    async with AsyncSession(engine) as db:
        yield db
    await engine.dispose()


async def _scoped(db: AsyncSession, workspace_id: UUID) -> None:
    await db.execute(text(f"SET LOCAL app.workspace_id = '{workspace_id}'"))


async def _held(
    session: AsyncSession, workspace_id: UUID, account_id: UUID, role: AccountRole
) -> UUID | None:
    repository = SqlAccountAssignmentRepository(session)
    for assignment in await repository.for_accounts(workspace_id, (account_id,)):
        if assignment.role is role:
            return assignment.member_user_id
    return None


class TestAssigningReportsWhatMovedRatherThanWhatWasAsked:
    async def test_an_account_already_held_by_that_member_is_unchanged(
        self, session: AsyncSession
    ) -> None:
        """⛔ **Re-applying is not a change**, and saying so is what stops the
        reversal touching it."""
        account, member = uuid4(), uuid4()
        workspace, actor = uuid4(), uuid4()
        await _scoped(session, workspace)
        repository = SqlAccountAssignmentRepository(session)

        await repository.assign(
            workspace, (account,), role=AccountRole.OWNER,
            member_user_id=member, actor_id=actor,
        )
        second = await repository.assign(
            workspace, (account,), role=AccountRole.OWNER,
            member_user_id=member, actor_id=actor,
        )

        assert second.previous == ()
        assert second.unchanged == (account,)

    async def test_a_previously_unowned_account_records_none(
        self, session: AsyncSession
    ) -> None:
        """⚡ **`None` is a value here, not an absence of one.** It is what
        tells the reversal to clear the field rather than skip the row."""
        account, member = uuid4(), uuid4()
        workspace, actor = uuid4(), uuid4()
        await _scoped(session, workspace)

        outcome = await SqlAccountAssignmentRepository(session).assign(
            workspace, (account,), role=AccountRole.OWNER,
            member_user_id=member, actor_id=actor,
        )

        assert outcome.previous == ((account, None),)

    async def test_a_reassignment_records_who_held_it(
        self, session: AsyncSession
    ) -> None:
        account, first, second = uuid4(), uuid4(), uuid4()
        workspace, actor = uuid4(), uuid4()
        await _scoped(session, workspace)
        repository = SqlAccountAssignmentRepository(session)

        await repository.assign(
            workspace, (account,), role=AccountRole.OWNER,
            member_user_id=first, actor_id=actor,
        )
        outcome = await repository.assign(
            workspace, (account,), role=AccountRole.OWNER,
            member_user_id=second, actor_id=actor,
        )

        assert outcome.previous == ((account, first),)
        assert await _held(session, workspace, account, AccountRole.OWNER) == second

    async def test_owner_and_csm_are_independent(
        self, session: AsyncSession
    ) -> None:
        """⛔ **The primary key includes the role.** Setting a CSM must not
        disturb the owner — they are frequently different people, which is the
        whole reason the ruling names two."""
        account, owner, csm = uuid4(), uuid4(), uuid4()
        workspace, actor = uuid4(), uuid4()
        await _scoped(session, workspace)
        repository = SqlAccountAssignmentRepository(session)

        await repository.assign(
            workspace, (account,), role=AccountRole.OWNER,
            member_user_id=owner, actor_id=actor,
        )
        await repository.assign(
            workspace, (account,), role=AccountRole.CSM,
            member_user_id=csm, actor_id=actor,
        )

        assert await _held(session, workspace, account, AccountRole.OWNER) == owner
        assert await _held(session, workspace, account, AccountRole.CSM) == csm


class TestRestoringPutsBackTheAbsencesToo:
    async def test_an_account_that_had_nobody_ends_with_nobody(
        self, session: AsyncSession
    ) -> None:
        """🔴 **The half that is normally missed.**

        ⛔ **Writing nothing for a `None` would leave the new owner in place**,
        so the reversal would report success while half of it did not happen —
        and the customer would find an owner they had explicitly undone.
        """
        account, member = uuid4(), uuid4()
        workspace, actor = uuid4(), uuid4()
        await _scoped(session, workspace)
        repository = SqlAccountAssignmentRepository(session)

        outcome = await repository.assign(
            workspace, (account,), role=AccountRole.OWNER,
            member_user_id=member, actor_id=actor,
        )
        await repository.restore(
            workspace, outcome.inverse(), role=AccountRole.OWNER,
            assigned_to=outcome.assigned_to, actor_id=actor,
        )

        assert await _held(session, workspace, account, AccountRole.OWNER) is None

    async def test_an_account_that_had_somebody_gets_them_back(
        self, session: AsyncSession
    ) -> None:
        account, first, second = uuid4(), uuid4(), uuid4()
        workspace, actor = uuid4(), uuid4()
        await _scoped(session, workspace)
        repository = SqlAccountAssignmentRepository(session)

        await repository.assign(
            workspace, (account,), role=AccountRole.OWNER,
            member_user_id=first, actor_id=actor,
        )
        outcome = await repository.assign(
            workspace, (account,), role=AccountRole.OWNER,
            member_user_id=second, actor_id=actor,
        )
        await repository.restore(
            workspace, outcome.inverse(), role=AccountRole.OWNER,
            assigned_to=outcome.assigned_to, actor_id=actor,
        )

        assert await _held(session, workspace, account, AccountRole.OWNER) == first

    async def test_a_mixed_batch_restores_each_account_to_its_own_prior_state(
        self, session: AsyncSession
    ) -> None:
        """⚡ **The realistic case**, and the one a nullable column could not
        serve: some of the selection had an owner and some did not."""
        had, had_not, first, new = uuid4(), uuid4(), uuid4(), uuid4()
        workspace, actor = uuid4(), uuid4()
        await _scoped(session, workspace)
        repository = SqlAccountAssignmentRepository(session)

        await repository.assign(
            workspace, (had,), role=AccountRole.OWNER,
            member_user_id=first, actor_id=actor,
        )
        outcome = await repository.assign(
            workspace, (had, had_not), role=AccountRole.OWNER,
            member_user_id=new, actor_id=actor,
        )
        await repository.restore(
            workspace, outcome.inverse(), role=AccountRole.OWNER,
            assigned_to=outcome.assigned_to, actor_id=actor,
        )

        assert await _held(session, workspace, had, AccountRole.OWNER) == first
        assert await _held(session, workspace, had_not, AccountRole.OWNER) is None


class TestReadsAskAboutAccountsTheCallerAlreadyNamed:
    async def test_an_empty_selection_asks_the_database_nothing(
        self, session: AsyncSession
    ) -> None:
        workspace, actor = uuid4(), uuid4()
        await _scoped(session, workspace)

        assert await SqlAccountAssignmentRepository(session).for_accounts(workspace, ()) == ()

    async def test_another_workspaces_assignment_is_not_returned(
        self, session: AsyncSession
    ) -> None:
        """⛔ **RLS is the authoritative control and the query filters anyway**
        (§8, defense in depth). This proves the pair, not either alone."""
        account, member = uuid4(), uuid4()
        workspace, actor = uuid4(), uuid4()
        await _scoped(session, workspace)
        await SqlAccountAssignmentRepository(session).assign(
            workspace, (account,), role=AccountRole.OWNER,
            member_user_id=member, actor_id=actor,
        )

        other = uuid4()
        await _scoped(session, other)

        assert await SqlAccountAssignmentRepository(session).for_accounts(
            other, (account,)
        ) == ()


class TestTheReversalAgainstAWorldThatMoved:
    """**QE's three hypotheses, tested rather than reasoned about.**

    🔴 The two known failures are about the *shape* of the prior state — an
    absence must be restored as an absence. **These are about its validity: is
    the state the reversal is undoing still the state it left?**
    """

    async def test_a_reversal_does_not_overwrite_an_assignment_made_since(
        self, session: AsyncSession
    ) -> None:
        """🔴 **A lost update wearing an undo's clothes.**

        The batch set the owner to `new`. Somebody then legitimately set it to
        `later`. ⛔ **Taking the batch back must not silently discard `later`**
        — the customer undid a batch, not a colleague's decision, and nothing
        on the screen would say the second change had gone.
        """
        account, first, new, later = uuid4(), uuid4(), uuid4(), uuid4()
        workspace, actor = uuid4(), uuid4()
        await _scoped(session, workspace)
        repository = SqlAccountAssignmentRepository(session)

        await repository.assign(
            workspace, (account,), role=AccountRole.OWNER,
            member_user_id=first, actor_id=actor,
        )
        outcome = await repository.assign(
            workspace, (account,), role=AccountRole.OWNER,
            member_user_id=new, actor_id=actor,
        )
        # Somebody else, afterwards and legitimately.
        await repository.assign(
            workspace, (account,), role=AccountRole.OWNER,
            member_user_id=later, actor_id=actor,
        )

        await repository.restore(
            workspace, outcome.inverse(), role=AccountRole.OWNER,
            assigned_to=outcome.assigned_to, actor_id=actor,
        )

        assert await _held(session, workspace, account, AccountRole.OWNER) == later

    async def test_reversing_twice_does_not_re_assert_a_stale_holder(
        self, session: AsyncSession
    ) -> None:
        """⚠️ **The second reversal must be a no-op, not a second write.**

        After the first `restore`, the account is back with `first`. If a
        colleague then assigns `later`, **a repeated reversal must not reach
        back and undo them** — an undo pressed twice is still one undo.
        """
        account, first, new, later = uuid4(), uuid4(), uuid4(), uuid4()
        workspace, actor = uuid4(), uuid4()
        await _scoped(session, workspace)
        repository = SqlAccountAssignmentRepository(session)

        await repository.assign(
            workspace, (account,), role=AccountRole.OWNER,
            member_user_id=first, actor_id=actor,
        )
        outcome = await repository.assign(
            workspace, (account,), role=AccountRole.OWNER,
            member_user_id=new, actor_id=actor,
        )
        await repository.restore(
            workspace, outcome.inverse(), role=AccountRole.OWNER,
            assigned_to=outcome.assigned_to, actor_id=actor,
        )
        await repository.assign(
            workspace, (account,), role=AccountRole.OWNER,
            member_user_id=later, actor_id=actor,
        )

        await repository.restore(
            workspace, outcome.inverse(), role=AccountRole.OWNER,
            assigned_to=outcome.assigned_to, actor_id=actor,
        )

        assert await _held(session, workspace, account, AccountRole.OWNER) == later

    async def test_an_absence_is_only_restored_if_the_batch_still_holds_it(
        self, session: AsyncSession
    ) -> None:
        """⛔ **The same rule for the clearing half.**

        The batch gave an unowned account an owner. Somebody then chose a
        different one. **Taking the batch back must not clear their choice** —
        the account was never the batch's to empty once it had moved on.
        """
        account, new, later = uuid4(), uuid4(), uuid4()
        workspace, actor = uuid4(), uuid4()
        await _scoped(session, workspace)
        repository = SqlAccountAssignmentRepository(session)

        outcome = await repository.assign(
            workspace, (account,), role=AccountRole.OWNER,
            member_user_id=new, actor_id=actor,
        )
        await repository.assign(
            workspace, (account,), role=AccountRole.OWNER,
            member_user_id=later, actor_id=actor,
        )

        await repository.restore(
            workspace, outcome.inverse(), role=AccountRole.OWNER,
            assigned_to=outcome.assigned_to, actor_id=actor,
        )

        assert await _held(session, workspace, account, AccountRole.OWNER) == later


class TestTheBatchStoreKeepsWhatTheEventDoesNot:
    """🔴 **`SqlAssignmentBatchStore` against a real database** — found untested
    by [B-201](../../../docs/BUGS.md)'s repository-wide coverage number.

    📁 *Events carry identity; ports carry payload.* The `applied` event names
    a `batch_id` and nothing else, **so everything the reversal needs has to
    survive in this table** — and these are the assertions that say it does.
    """

    async def test_a_recorded_batch_reads_back_as_not_applied(
        self, session: AsyncSession
    ) -> None:
        """⛔ **`None`, not `()`.** ⚠️ **The distinction is the whole reason the
        column is nullable**: *never approved* and *approved and moved nobody*
        are different rows, and only the first is still waiting for a person.
        """
        workspace_id, member, account = uuid4(), uuid4(), uuid4()
        await _scoped(session, workspace_id)
        store = SqlAssignmentBatchStore(session)
        batch = AssignmentBatch(
            batch_id=uuid4(),
            role=AccountRole.OWNER,
            member_user_id=member,
            requested=(account,),
        )

        await store.record(workspace_id, batch, actor_id=member)
        read_back = await store.by_id(workspace_id, batch.batch_id)

        assert read_back is not None
        assert read_back.moved is None
        assert read_back.requested == (account,)
        assert read_back.to_reverse() == ()

    async def test_an_applied_batch_carries_the_prior_holders_and_the_absences(
        self, session: AsyncSession
    ) -> None:
        """🔴 **A `None` prior has to survive the round trip through JSON.**

        ⛔ **This is where the reversal's hardest case lives**: an account that
        had *no* owner before must come back as `(account, None)` rather than
        being dropped — **a reversal that skipped it would leave the new owner
        in place while reporting success.**
        """
        workspace_id, member, prior = uuid4(), uuid4(), uuid4()
        had_owner, had_none = uuid4(), uuid4()
        await _scoped(session, workspace_id)
        store = SqlAssignmentBatchStore(session)
        batch = AssignmentBatch(
            batch_id=uuid4(),
            role=AccountRole.OWNER,
            member_user_id=member,
            requested=(had_owner, had_none),
        )
        await store.record(workspace_id, batch, actor_id=member)

        await store.record_applied(
            workspace_id,
            batch.batch_id,
            Reassignment(
                role=AccountRole.OWNER,
                assigned_to=member,
                previous=((had_owner, prior), (had_none, None)),
            ),
            actor_id=member,
        )
        read_back = await store.by_id(workspace_id, batch.batch_id)

        assert read_back is not None
        assert read_back.moved is not None
        assert read_back.to_reverse() == ((had_owner, prior), (had_none, None))
        # ⚡ **What the batch PUT there**, which is what makes `restore`
        # conditional rather than a lost update wearing an undo's clothes.
        assert read_back.moved.assigned_to == member

    async def test_a_batch_from_another_workspace_is_absent_rather_than_visible(
        self, session: AsyncSession
    ) -> None:
        """🔴 **Tenancy, asserted rather than assumed.** ⛔ The predicate and
        the RLS policy both scope this, and a store that returned a neighbour's
        batch would let one workspace's reversal rewrite another's accounts.
        """
        mine, theirs, member = uuid4(), uuid4(), uuid4()
        await _scoped(session, mine)
        store = SqlAssignmentBatchStore(session)
        batch = AssignmentBatch(
            batch_id=uuid4(),
            role=AccountRole.CSM,
            member_user_id=member,
            requested=(uuid4(),),
        )
        await store.record(mine, batch, actor_id=member)

        assert await store.by_id(theirs, batch.batch_id) is None

    async def test_a_batch_nobody_proposed_here_reads_as_absent(
        self, session: AsyncSession
    ) -> None:
        """⛔ **`None`, and the handler does nothing with it.** A tag batch's
        `applied` event reaches this consumer too, and raising would
        dead-letter somebody else's action on this module's queue."""
        workspace_id = uuid4()
        await _scoped(session, workspace_id)

        assert await SqlAssignmentBatchStore(session).by_id(workspace_id, uuid4()) is None


class TestARestoreWithNothingToConditionOnWritesNothing:
    async def test_a_reversal_with_no_assigned_to_is_refused_silently(
        self, session: AsyncSession
    ) -> None:
        """🔴 **The guard at the top of `restore`, and it is the safe default.**

        ⛔ **Every write in `restore` is conditional on the batch's own value
        still being in place.** With no `assigned_to` there is nothing to
        condition on — **the reversal could not tell its own change from
        anybody else's** — and guessing would be exactly the destructive write
        the compare-and-set exists to prevent.

        ⚠️ **Silently rather than by raising**, because this is reachable only
        from a batch that recorded no assignment, and dead-lettering a
        reversal on the worker's queue would be worse than doing nothing.
        """
        workspace_id, account, holder = uuid4(), uuid4(), uuid4()
        await _scoped(session, workspace_id)
        repository = SqlAccountAssignmentRepository(session)
        await repository.assign(
            workspace_id,
            (account,),
            role=AccountRole.OWNER,
            member_user_id=holder,
            actor_id=holder,
        )

        await repository.restore(
            workspace_id,
            ((account, None),),
            role=AccountRole.OWNER,
            assigned_to=None,
            actor_id=holder,
        )

        # **Untouched.** The account is still held by whoever held it.
        assert await _held(session, workspace_id, account, AccountRole.OWNER) == holder

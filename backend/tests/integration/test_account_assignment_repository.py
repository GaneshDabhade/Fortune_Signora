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

from modules.commercial_profile.domain.account_assignment import AccountRole
from modules.commercial_profile.infrastructure.assignment_repository import (
    SqlAccountAssignmentRepository,
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
            workspace, outcome.inverse(), role=AccountRole.OWNER, actor_id=actor
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
            workspace, outcome.inverse(), role=AccountRole.OWNER, actor_id=actor
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
            workspace, outcome.inverse(), role=AccountRole.OWNER, actor_id=actor
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

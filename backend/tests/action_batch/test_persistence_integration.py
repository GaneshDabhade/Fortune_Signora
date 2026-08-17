"""What the database refuses about a batch, and what it keeps.

**[TASK-463](../../../docs/BACKLOG.md), slice 3 of six.**

**Against a real database, not a double.** Every refusal below is a `CHECK`
constraint, a unique index or a missing grant — **a repository fake would
reproduce whatever its author believed those meant**, which is the thing under
test. `test_persistence.py` covers the mapping; this covers the store.

⚡ **And it is what proves the round trip actually round-trips.** A slice whose
persistence is only exercised through fakes has a schema nobody has written to,
which is precisely how `people/public/` reached `main` empty
([C-235](../../../docs/LANE_COORDINATION.md)).

**The workspace is created through the real use case**, never inserted — test
data enters the way a customer's data enters (§20e).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.action_batch.domain.batch import ActionBatch, ApprovalState, Decision, Transition
from modules.action_batch.infrastructure.models import ActionBatchTransitionModel
from modules.action_batch.infrastructure.repository import SqlActionBatchRepository
from modules.workspace_tenancy.application.use_cases import CreateWorkspaceInput
from modules.workspace_tenancy.infrastructure.composition import build_use_cases
from signora_platform.db import tenant_scoped_session, user_scoped_session
from tests.slugs import test_slug as _test_slug

pytestmark = pytest.mark.integration

PROPOSED = datetime(2026, 8, 7, 9, 0, tzinfo=UTC)
DECIDED = PROPOSED + timedelta(minutes=5)
APPLIED = PROPOSED + timedelta(minutes=10)
WINDOW = timedelta(hours=1)


async def _workspace(factory: async_sessionmaker[AsyncSession]) -> tuple[UUID, UUID]:
    user_id = uuid4()
    async with user_scoped_session(factory, user_id=user_id) as session:
        result = await build_use_cases(session).create_workspace.execute(
            CreateWorkspaceInput(name="Action Batch", slug=_test_slug("Action Batch"), created_by=user_id),
            correlation_id=uuid4(),
        )
        return result.workspace.id, user_id


def _batch(workspace_id: UUID, proposer: UUID, *, window: timedelta | None = WINDOW) -> ActionBatch:
    return ActionBatch(
        id=uuid4(),
        workspace_id=workspace_id,
        name="Move 12 accounts to Engaged",
        item_count=12,
        proposed=Decision(actor_id=proposer, at=PROPOSED),
        reversible_for=window,
    )


class TestABatchSurvivesTheDatabase:
    @pytest.mark.asyncio
    async def test_a_proposal_comes_back_as_it_went_in(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id = await _workspace(admin_session_factory)
        batch = _batch(workspace_id, user_id)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            await SqlActionBatchRepository(session).add(batch, actor_id=user_id)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            stored = await SqlActionBatchRepository(session).get(workspace_id, batch.id)

        assert stored == batch

    @pytest.mark.asyncio
    async def test_the_whole_lifecycle_replays_from_the_log(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """⚡ **The slice's central claim, proven end to end.** Approval,
        application and reversal are three appended rows and no `UPDATE`, and
        the aggregate that comes back is the one that went in."""
        workspace_id, user_id = await _workspace(admin_session_factory)
        batch = _batch(workspace_id, user_id)
        approved = batch.approved_by(user_id, at=DECIDED)
        applied = approved.applied_on(APPLIED)
        reversed_ = applied.reversed_by(user_id, at=APPLIED + timedelta(minutes=30))

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            repository = SqlActionBatchRepository(session)
            await repository.add(batch, actor_id=user_id)
            for state in (approved, applied, reversed_):
                await repository.record(state, actor_id=user_id)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            stored = await SqlActionBatchRepository(session).get(workspace_id, batch.id)

        assert stored == reversed_
        assert stored is not None
        assert stored.state is ApprovalState.REVERSED
        assert stored.applied_at == APPLIED
        assert stored.decided is not None and stored.decided.at == DECIDED

    @pytest.mark.asyncio
    async def test_a_window_that_was_never_offered_stays_absent(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """`NULL` means reversal was never offered, and a store that turned it
        into a zero-length window would say *expired* instead."""
        workspace_id, user_id = await _workspace(admin_session_factory)
        batch = _batch(workspace_id, user_id, window=None)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            await SqlActionBatchRepository(session).add(batch, actor_id=user_id)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            stored = await SqlActionBatchRepository(session).get(workspace_id, batch.id)

        assert stored is not None
        assert stored.reversible_for is None

    @pytest.mark.asyncio
    async def test_a_batch_that_does_not_exist_is_none_rather_than_an_error(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id = await _workspace(admin_session_factory)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            assert await SqlActionBatchRepository(session).get(workspace_id, uuid4()) is None


class TestTheDatabaseRefusesWhatTheDomainRefuses:
    """**The type protects the code written today; the constraint protects the
    row written by whatever writes it next** — a backfill, a repair script, a
    second service. A rule that lives only in the caller is a rule the next
    caller does not have."""

    @pytest.mark.asyncio
    async def test_recording_the_same_transition_twice_collides(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """⚡ **This is what makes `record` idempotent rather than merely
        careful.** The position comes from the aggregate, so a repeat writes
        the same `sequence` and the unique index refuses it — where a
        `max(sequence) + 1` would have stored the approval twice."""
        workspace_id, user_id = await _workspace(admin_session_factory)
        batch = _batch(workspace_id, user_id)
        approved = batch.approved_by(user_id, at=DECIDED)

        with pytest.raises(IntegrityError):
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=user_id
            ) as session:
                repository = SqlActionBatchRepository(session)
                await repository.add(batch, actor_id=user_id)
                await repository.record(approved, actor_id=user_id)
                await repository.record(approved, actor_id=user_id)

    @pytest.mark.asyncio
    async def test_an_unattributed_approval_is_refused_by_the_database(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Application is the only transition without an actor.** Written
        directly, because no repository method can produce this — which is
        exactly why the constraint has to exist rather than the guard alone."""
        workspace_id, user_id = await _workspace(admin_session_factory)
        batch = _batch(workspace_id, user_id)

        with pytest.raises((IntegrityError, DBAPIError)):
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=user_id
            ) as session:
                await SqlActionBatchRepository(session).add(batch, actor_id=user_id)
                session.add(
                    ActionBatchTransitionModel(
                        id=uuid4(),
                        workspace_id=workspace_id,
                        batch_id=batch.id,
                        sequence=0,
                        transition=Transition.APPROVED.value,
                        actor_id=None,
                        occurred_at=DECIDED,
                        created_by=user_id,
                        updated_by=user_id,
                    )
                )
                await session.flush()

    @pytest.mark.asyncio
    async def test_a_transition_the_domain_has_no_name_for_is_refused(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id = await _workspace(admin_session_factory)
        batch = _batch(workspace_id, user_id)

        with pytest.raises((IntegrityError, DBAPIError)):
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=user_id
            ) as session:
                await SqlActionBatchRepository(session).add(batch, actor_id=user_id)
                session.add(
                    ActionBatchTransitionModel(
                        id=uuid4(),
                        workspace_id=workspace_id,
                        batch_id=batch.id,
                        sequence=0,
                        transition="unapproved",
                        actor_id=user_id,
                        occurred_at=DECIDED,
                        created_by=user_id,
                        updated_by=user_id,
                    )
                )
                await session.flush()

    @pytest.mark.asyncio
    async def test_an_empty_batch_is_refused_by_the_database_too(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The domain refuses it in `__post_init__`; this proves the row is
        refused as well, for whatever writes one without going through it."""
        workspace_id, user_id = await _workspace(admin_session_factory)
        batch = _batch(workspace_id, user_id)
        object.__setattr__(batch, "item_count", 0)

        with pytest.raises((IntegrityError, DBAPIError)):
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=user_id
            ) as session:
                await SqlActionBatchRepository(session).add(batch, actor_id=user_id)


class TestOneWorkspacesApprovalsAreNeverAnothers:
    @pytest.mark.asyncio
    async def test_a_batch_in_another_workspace_is_not_found(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Not forbidden — not found.** The same rule §7 applies to
        workspaces, and it is what stops a caller enumerating them."""
        mine, my_user = await _workspace(admin_session_factory)
        theirs, their_user = await _workspace(admin_session_factory)
        batch = _batch(mine, my_user)

        async with tenant_scoped_session(
            session_factory, workspace_id=mine, user_id=my_user
        ) as session:
            await SqlActionBatchRepository(session).add(batch, actor_id=my_user)

        async with tenant_scoped_session(
            session_factory, workspace_id=theirs, user_id=their_user
        ) as session:
            assert await SqlActionBatchRepository(session).get(theirs, batch.id) is None

    @pytest.mark.asyncio
    async def test_the_transition_log_is_scoped_the_same_way(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """⚠️ **The log is where an approval actually lives**, so a leak here
        would expose who approved what in another tenant even if the batch row
        itself were hidden."""
        mine, my_user = await _workspace(admin_session_factory)
        theirs, their_user = await _workspace(admin_session_factory)
        batch = _batch(mine, my_user)
        approved = batch.approved_by(my_user, at=DECIDED)

        async with tenant_scoped_session(
            session_factory, workspace_id=mine, user_id=my_user
        ) as session:
            repository = SqlActionBatchRepository(session)
            await repository.add(batch, actor_id=my_user)
            await repository.record(approved, actor_id=my_user)

        async with tenant_scoped_session(
            session_factory, workspace_id=theirs, user_id=their_user
        ) as session:
            rows = await session.execute(
                ActionBatchTransitionModel.__table__.select().where(
                    ActionBatchTransitionModel.batch_id == batch.id
                )
            )
            assert rows.all() == []

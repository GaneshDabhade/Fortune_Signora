"""**Two people in ONE workspace cannot see each other's read state.**

📁 **[TASK-480](../../../docs/BACKLOG.md), [D-239](../../../docs/DECISION_REGISTER.md).**

## 🔴 The case tenant isolation cannot cover, which is why this file exists

⛔ **Every other tenancy test proves that one workspace cannot see another's
rows.** ⚡ **That proof passes for a table that leaks every row between
COLLEAGUES** — **two people in the same workspace are legitimately in the same
tenant, and only the person predicate separates them.**

⚠️ **QE named this exactly**: *"the test I will not accept as sufficient is the
one that proves workspace isolation and calls it done."* ✅ **So this asserts
the narrowing itself** — 📁 492 §0, *"one predicate is added"* — **through the
POLICY, by reading as each person under their own session context.**

⛔ **It reads through `signora_app` rather than the owner**, which is the whole
point: **the owner bypasses RLS, so a test run as one would pass against a
table with no policies at all.**
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.workspace_tenancy.infrastructure.repositories import (
    SqlAlchemyNotificationReadRepository,
)
from signora_platform.db.session import tenant_scoped_session

pytestmark = pytest.mark.asyncio


async def _a_workspace(session: AsyncSession, workspace_id: UUID, founder: UUID) -> None:
    """⚡ **`created_by` is NOT NULL** — every workspace has a founder, which is
    the constraint saying so."""
    await session.execute(
        text(
            "INSERT INTO workspace (id, name, slug, created_by, updated_by) "
            "VALUES (:id, :name, :slug, :by, :by)"
        ),
        {
            "id": str(workspace_id),
            "name": "Northwind",
            # ⚡ Unique per row; the column carries a unique constraint.
            "slug": f"nw-{str(workspace_id)[:8]}",
            "by": str(founder),
        },
    )


class TestOnePersonsReadStateIsNotAnothers:
    async def test_a_colleague_cannot_see_what_this_person_has_read(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """🔴 **The invariant, in the one shape tenant isolation cannot catch.**"""
        workspace_id, alice, bob = uuid4(), uuid4(), uuid4()
        notification_id = uuid4()

        async with admin_session_factory() as owner, owner.begin():
            await _a_workspace(owner, workspace_id, alice)

        # ⚡ **Alice reads it, through the policy rather than around it.**
        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=alice
        ) as session:
            await SqlAlchemyNotificationReadRepository(session).mark_read(
                workspace_id, alice, [notification_id]
            )

        # ✅ **Alice sees her own read: nothing unread.**
        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=alice
        ) as session:
            hers = await SqlAlchemyNotificationReadRepository(session).unread(
                workspace_id, alice, [notification_id]
            )

        # 🔴 **Bob, in the SAME workspace, must still see it as unread.**
        # ⛔ **If the person predicate were missing, Alice's row would satisfy
        # Bob's query and he would be told he had read something he has not.**
        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=bob
        ) as session:
            his = await SqlAlchemyNotificationReadRepository(session).unread(
                workspace_id, bob, [notification_id]
            )

        assert hers.value == 0, "Alice read it, so nothing is unread for her"
        assert his.value == 1, (
            "Bob has not read it. A zero here means one colleague's read state "
            "satisfied another's query — which tenant isolation cannot catch, "
            "because they are legitimately in the same tenant."
        )

    async def test_the_policy_hides_the_row_itself_not_only_the_count(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """⚡ **Through the POLICY, asserted on the row rather than the answer.**

        ⛔ **A repository that filtered correctly over a table with no policy
        would pass the test above.** ✅ **This one reads the table directly as
        Bob and asserts the row is not merely excluded by the query — it is
        invisible.**
        """
        workspace_id, alice, bob = uuid4(), uuid4(), uuid4()
        notification_id = uuid4()

        async with admin_session_factory() as owner, owner.begin():
            await _a_workspace(owner, workspace_id, alice)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=alice
        ) as session:
            await SqlAlchemyNotificationReadRepository(session).mark_read(
                workspace_id, alice, [notification_id]
            )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=bob
        ) as session:
            # ⛔ **No `user_id` predicate in this SQL, deliberately.** ⚡ **The
            # POLICY is what must exclude it** — a query that filtered here
            # would be testing the query rather than the policy.
            visible = await session.scalar(
                text("SELECT count(*) FROM notification_read WHERE workspace_id = :w"),
                {"w": str(workspace_id)},
            )

        assert visible == 0, (
            "Bob's session can see a row belonging to Alice. The RLS policy on "
            "notification_read is missing its person predicate, and every "
            "workspace-level guarantee is intact while this leaks."
        )

    async def test_alice_sees_her_own_row_so_the_policy_is_not_simply_denying_everything(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """⚠️ **The half that stops the test above passing vacuously.**

        ⛔ **A policy denying every row would satisfy *Bob sees nothing*** — and
        the feature would be broken while the invariant read green.
        """
        workspace_id, alice = uuid4(), uuid4()
        notification_id = uuid4()

        async with admin_session_factory() as owner, owner.begin():
            await _a_workspace(owner, workspace_id, alice)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=alice
        ) as session:
            await SqlAlchemyNotificationReadRepository(session).mark_read(
                workspace_id, alice, [notification_id]
            )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=alice
        ) as session:
            visible = await session.scalar(
                text("SELECT count(*) FROM notification_read WHERE workspace_id = :w"),
                {"w": str(workspace_id)},
            )

        assert visible == 1, "Alice cannot see her own read — the policy denies everything"

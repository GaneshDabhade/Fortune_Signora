"""**One person's reading history is not a colleague's.**

📁 **Session Continuity tier 4**, migration `0064`, read by 📁 Home's
`card.recents`.

## 🔴 Why this needs its own invariant rather than inheriting tenant isolation

⛔ **Every tenancy test proves one workspace cannot see another's rows, and
every one of them passes for a table that leaks every row between COLLEAGUES.**
⚡ **Two people in one workspace are legitimately the same tenant** — only the
person predicate separates them, and 492 §0 puts it in the policy precisely so
that a query which forgets it still cannot reach across.

## ⚠️ What a defect here would actually disclose

⛔ **Not a wrong number — a reading history.** Which accounts a colleague opened,
and when, is a fact about how they spend their time and which deals they are
working. **That is the disclosure this file exists to prevent**, and it is
invisible to every test that only asks whether workspaces are separated.

⛔ **Read through `signora_app`, never the owner** — the owner bypasses RLS, so
these would pass against a table carrying no policies at all.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.workspace_tenancy.domain.recently_viewed import ViewedKind
from modules.workspace_tenancy.infrastructure.repositories import (
    SqlAlchemyRecentlyViewedRepository,
)
from signora_platform.db.session import tenant_scoped_session

pytestmark = pytest.mark.asyncio


async def _a_workspace(session: AsyncSession, workspace_id: UUID, founder: UUID) -> None:
    await session.execute(
        text(
            "INSERT INTO workspace (id, name, slug, created_by, updated_by) "
            "VALUES (:id, :name, :slug, :by, :by)"
        ),
        {
            "id": str(workspace_id),
            "name": "Northwind",
            "slug": f"nw-{str(workspace_id)[:8]}",
            "by": str(founder),
        },
    )


class TestOnePersonsRecentsAreNotAnothers:
    async def test_a_colleague_does_not_see_what_this_person_opened(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """🔴 **The disclosure tenant isolation cannot catch.**"""
        workspace_id, alice, bob, account = uuid4(), uuid4(), uuid4(), uuid4()

        async with admin_session_factory() as owner, owner.begin():
            await _a_workspace(owner, workspace_id, alice)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=alice
        ) as session:
            await SqlAlchemyRecentlyViewedRepository(session).record(
                workspace_id, alice, account, ViewedKind.ACCOUNT
            )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=alice
        ) as session:
            hers = await SqlAlchemyRecentlyViewedRepository(session).recent(
                workspace_id, alice, limit=5, within_days=30
            )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=bob
        ) as session:
            his = await SqlAlchemyRecentlyViewedRepository(session).recent(
                workspace_id, bob, limit=5, within_days=30
            )

        assert [record.entity_id for record in hers] == [account]
        # ⛔ **Bob is a legitimate member of the same workspace.** The tenant
        # predicate admits him; only the person predicate keeps him out.
        assert his == ()

    async def test_a_colleague_cannot_write_into_this_persons_history(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """⛔ **The INSERT policy carries the person predicate too.**

        ⚡ **Writing is the other half.** A history somebody else can append to
        is a history that can be used to plant a record — and the `WITH CHECK`
        half of the policy is what refuses it, not the endpoint's signature.
        """
        workspace_id, alice, bob, account = uuid4(), uuid4(), uuid4(), uuid4()

        async with admin_session_factory() as owner, owner.begin():
            await _a_workspace(owner, workspace_id, alice)

        # Bob's session, writing a row that claims to be Alice's.
        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=bob
        ) as session:
            with pytest.raises(Exception):
                await session.execute(
                    text(
                        "INSERT INTO recently_viewed "
                        "(workspace_id, user_id, entity_id, entity_kind, viewed_at, "
                        " created_by, updated_by) "
                        "VALUES (:ws, :alice, :entity, 'account', now(), :bob, :bob)"
                    ),
                    {
                        "ws": str(workspace_id),
                        "alice": str(alice),
                        "entity": str(account),
                        "bob": str(bob),
                    },
                )
                await session.flush()

"""**What a person opened, offered back** — 📁 Session Continuity tier 4.

📁 Read by `Fortune Signora Home.dc.html` §04 — *"Pick up where you left off ·
last five records touched · context, never urgent."*
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.workspace_tenancy.application.use_cases.recently_viewed import (
    HOME_RECENTS,
    RecentRecordsUseCase,
    RecordViewUseCase,
)
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


class TestAViewIsIdempotentPerRecord:
    async def test_opening_the_same_record_twice_is_one_entry(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """🔴 **The single way this card can be useless.**

        📁 The design asks for *"the last five **records**"*. ⛔ **An
        append-only view log answers with one account five times** for somebody
        who refreshed, and the card then tells them to pick up where they left
        off — five times, on the same account.
        """
        workspace_id, person, account = uuid4(), uuid4(), uuid4()

        async with admin_session_factory() as owner, owner.begin():
            await _a_workspace(owner, workspace_id, person)

        for _ in range(3):
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=person
            ) as session:
                await RecordViewUseCase(
                    recently_viewed=SqlAlchemyRecentlyViewedRepository(session)
                ).execute(workspace_id, person, account, ViewedKind.ACCOUNT)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=person
        ) as session:
            records = await RecentRecordsUseCase(
                recently_viewed=SqlAlchemyRecentlyViewedRepository(session),
                retention_days=30,
            ).execute(workspace_id, person)

        assert [record.entity_id for record in records] == [account]


class TestTheListIsTheDesigns:
    async def test_newest_first_and_never_more_than_five(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """📁 *"Last five records touched"* — five, newest first."""
        workspace_id, person = uuid4(), uuid4()
        accounts = [uuid4() for _ in range(8)]

        async with admin_session_factory() as owner, owner.begin():
            await _a_workspace(owner, workspace_id, person)

        for account in accounts:
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=person
            ) as session:
                await RecordViewUseCase(
                    recently_viewed=SqlAlchemyRecentlyViewedRepository(session)
                ).execute(workspace_id, person, account, ViewedKind.ACCOUNT)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=person
        ) as session:
            records = await RecentRecordsUseCase(
                recently_viewed=SqlAlchemyRecentlyViewedRepository(session),
                retention_days=30,
            ).execute(workspace_id, person)

        assert len(records) == HOME_RECENTS
        # ⚡ **The five most recently opened, newest first** — the last five
        # written, reversed.
        assert [r.entity_id for r in records] == list(reversed(accounts[-HOME_RECENTS:]))


class TestRetentionIsConfiguration:
    async def test_a_record_older_than_the_window_is_not_offered_back(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """📁 **Session Continuity state 14** — *"tier 4 kept 30 days"*, and its
        `U-01` requires that be *"configuration, not a constant"* because
        retention may be constrained by the DPA.

        ⛔ **The row is not deleted on read.** A GET that pruned would be a
        destructive read; the window is a filter, and pruning is operational.
        """
        workspace_id, person, old, fresh = uuid4(), uuid4(), uuid4(), uuid4()

        async with admin_session_factory() as owner, owner.begin():
            await _a_workspace(owner, workspace_id, person)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=person
        ) as session:
            repository = SqlAlchemyRecentlyViewedRepository(session)
            await repository.record(workspace_id, person, old, ViewedKind.ACCOUNT)
            await repository.record(workspace_id, person, fresh, ViewedKind.ACCOUNT)
            await session.flush()
            # Age one row past the window.
            await session.execute(
                text(
                    "UPDATE recently_viewed SET viewed_at = :then "
                    "WHERE entity_id = :entity"
                ),
                {"then": datetime.now(UTC) - timedelta(days=45), "entity": str(old)},
            )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=person
        ) as session:
            records = await RecentRecordsUseCase(
                recently_viewed=SqlAlchemyRecentlyViewedRepository(session),
                retention_days=30,
            ).execute(workspace_id, person)

        assert [r.entity_id for r in records] == [fresh]

        # ⚡ **A wider window offers it again**, which is what makes this
        # configuration rather than a deletion.
        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=person
        ) as session:
            wider = await RecentRecordsUseCase(
                recently_viewed=SqlAlchemyRecentlyViewedRepository(session),
                retention_days=60,
            ).execute(workspace_id, person)

        assert {r.entity_id for r in wider} == {old, fresh}

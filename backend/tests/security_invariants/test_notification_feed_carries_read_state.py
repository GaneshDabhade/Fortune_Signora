"""**The feed says which items this person has read, and only this person.**

📁 **[TASK-495](../../../docs/BACKLOG.md) slice ⓑ** — 📁 the App Shell's §10:
*"Unread is a 6px dot on the right, never a coloured row"* and *"opening the
panel does not mark items read; opening an item does."*

## ⚠️ What each assertion here actually guards — measured, not assumed

**Both mutations below were applied to the real query and the suite re-run.**
⛔ **The first draft of this docstring claimed the person predicate was what
separated two colleagues, and that claim was false.**

| Mutation | Result |
|---|---|
| **`.outerjoin` → `.join`** | 🔴 **2 of 3 fail.** *"the left join dropped an unread row"* — ✅ **this is load-bearing** |
| **remove `NotificationReadRow.user_id == person_id`** | ✅ **3 pass.** ⛔ **The predicate is DEFENCE IN DEPTH, not the guard** |

⚡ **The person separation is enforced by the RLS policy on
`notification_read`**, which carries the same predicate one layer down — 📁 492
§0's narrowing, and `test_notification_read_isolates_colleagues` is the test
that proves the policy. **A session opened for Alice cannot see Bob's read row
at all, so the join has nothing wrong to find.**

⛔ **The predicate stays** — 📁 [§8](../../../CLAUDE.md) requires explicit
filtering *"as defence-in-depth — RLS is the authoritative control, not the only
one"* — **but this file does not claim to be what makes it hold**, because a
test that cannot fail in the case it names is documentation pretending to be
code ([§2](../../../CLAUDE.md)).

⚡ **The third test is still worth its place**: it asserts the OUTCOME a
customer would notice — one colleague's reading does not mark another's panel —
**whichever layer delivers it.** ⛔ It would catch a policy regression, which is
the failure that actually discloses something.

## 🔴 Why the left join is the one to protect

⛔ **An inner join returns only what has already been read** — the exact inverse
of the panel's purpose, and a mistake that **reads as an empty feed rather than
as a wrong one**, so nobody would look for a join bug.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.workspace_tenancy.domain.notification import (
    Actor,
    ActorKind,
    Category,
    Notification,
    Subject,
)
from modules.workspace_tenancy.infrastructure.repositories import (
    SqlAlchemyNotificationReadRepository,
    SqlAlchemyNotificationRepository,
)
from signora_platform.db.session import tenant_scoped_session

NOW = datetime(2026, 8, 19, 9, 12, tzinfo=UTC)


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


def _a_notification(workspace_id: UUID, recipient: UUID, *, at: datetime) -> Notification:
    return Notification(
        id=uuid4(),
        workspace_id=workspace_id,
        recipient_id=recipient,
        category=Category.NEEDS_YOU,
        actor=Actor(kind=ActorKind.AGENT, agent_name="Renewal risk sweep"),
        subject=Subject(kind="account", id=uuid4()),
        summary="finished researching Vantage Logistics",
        expectation="Review what it found",
        occurred_at=at,
    )


class TestTheFeedCarriesThisPersonsReadState:
    async def test_an_unread_item_comes_back_with_no_read_time(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """⛔ **`None` is the panel's dot.** A blanket time would hide every one."""
        workspace_id, alice = uuid4(), uuid4()
        async with admin_session_factory() as owner, owner.begin():
            await _a_workspace(owner, workspace_id, alice)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=alice
        ) as session:
            await SqlAlchemyNotificationRepository(session).record(
                _a_notification(workspace_id, alice, at=NOW)
            )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=alice
        ) as session:
            feed = await SqlAlchemyNotificationRepository(session).feed(
                workspace_id, alice, limit=20
            )

        assert len(feed) == 1, "the left join dropped an unread row — it is not a left join"
        assert feed[0].read_at is None

    async def test_reading_it_puts_a_time_on_that_item(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, alice = uuid4(), uuid4()
        async with admin_session_factory() as owner, owner.begin():
            await _a_workspace(owner, workspace_id, alice)

        notification = _a_notification(workspace_id, alice, at=NOW)
        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=alice
        ) as session:
            await SqlAlchemyNotificationRepository(session).record(notification)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=alice
        ) as session:
            await SqlAlchemyNotificationReadRepository(session).mark_read(
                workspace_id, alice, [notification.id]
            )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=alice
        ) as session:
            feed = await SqlAlchemyNotificationRepository(session).feed(
                workspace_id, alice, limit=20
            )

        assert len(feed) == 1
        assert feed[0].read_at is not None, "the item was read and the feed does not say so"

    async def test_a_colleagues_read_does_not_mark_this_persons_item(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """🔴 **The outcome a customer would notice, whichever layer delivers it.**

        ⚠️ **Measured: removing the join's person predicate does NOT fail this**
        — the RLS policy on `notification_read` already hides Bob's row from a
        session opened for Alice. ⛔ **So this does not prove the predicate**,
        and the file header says so rather than implying otherwise.

        ✅ **It proves the policy still holds through the query the screen
        actually uses**, which is the regression that would disclose one
        colleague's reading habits to another.
        """
        workspace_id, alice, bob = uuid4(), uuid4(), uuid4()
        async with admin_session_factory() as owner, owner.begin():
            await _a_workspace(owner, workspace_id, alice)

        # ⚡ **One notification each**, because the feed is filtered by
        # recipient — ⛔ a shared row would be caught by the recipient
        # predicate rather than by the one under test.
        hers = _a_notification(workspace_id, alice, at=NOW)
        his = _a_notification(workspace_id, bob, at=NOW)
        for person, notification in ((alice, hers), (bob, his)):
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=person
            ) as session:
                await SqlAlchemyNotificationRepository(session).record(notification)

        # 🔴 **Bob reads HIS, and also claims to have read HERS.** The second
        # is what a defect elsewhere could write, and the join must ignore it
        # for Alice regardless.
        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=bob
        ) as session:
            await SqlAlchemyNotificationReadRepository(session).mark_read(
                workspace_id, bob, [his.id, hers.id]
            )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=alice
        ) as session:
            feed = await SqlAlchemyNotificationRepository(session).feed(
                workspace_id, alice, limit=20
            )

        assert [item.notification.id for item in feed] == [hers.id]
        assert feed[0].read_at is None, (
            "Alice's item reads as read because a colleague read it. Both the "
            "RLS policy on notification_read and the join's own person "
            "predicate would have to be wrong for this to happen — and tenant "
            "isolation cannot catch it, because they are legitimately in the "
            "same workspace."
        )

"""**One person's notifications are not another's, and a colleague may still write one.**

📁 **[TASK-495](../../../docs/BACKLOG.md)**, migration `0059`, on
[ADR-0017](../../../docs/architecture/adr/0017-notifications.md) and
[D-239](../../../docs/DECISION_REGISTER.md).

## 🔴 Why this table needs its own invariant rather than inheriting `0058`'s

⚡ **`notification_read` (`0058`) carries `workspace AND user` on every policy**,
because a person marks their OWN read. ⛔ **This table cannot**: a notification
is written FOR somebody else — a mention is one colleague addressing another,
and the research agent addresses whoever asked.

✅ **So the policies are ASYMMETRIC**: **INSERT is workspace-scoped, SELECT is
workspace AND recipient.** 🔴 **The guarantee lives entirely on the read side**,
and this file is what proves the asymmetry was deliberate rather than a
predicate somebody forgot.

## ⚠️ The failure this exists to catch is the one tenant isolation cannot

⛔ **Every other tenancy test proves one workspace cannot see another's rows,
and every one of them passes for a table that leaks every row between
COLLEAGUES.** ⚡ **Two people in one workspace are legitimately in the same
tenant; only the recipient predicate separates them** — and here a defect does
not render a wrong number, **it shows one person what another was told about
their own accounts.**

⛔ **Read through `signora_app`, never the owner** — the owner bypasses RLS, so
these would pass against a table with no policies at all.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
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
    SqlAlchemyNotificationRepository,
)
from signora_platform.db.session import tenant_scoped_session

pytestmark = pytest.mark.asyncio

NOW = datetime(2026, 8, 16, 9, 30, tzinfo=UTC)


async def _a_workspace(session: AsyncSession, workspace_id: UUID, founder: UUID) -> None:
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


def _for(workspace_id: UUID, recipient: UUID) -> Notification:
    return Notification(
        id=uuid4(),
        workspace_id=workspace_id,
        recipient_id=recipient,
        category=Category.NEEDS_YOU,
        actor=Actor(kind=ActorKind.AGENT, agent_name="Research"),
        subject=Subject(kind="opportunity", id=uuid4()),
        summary="Signora finished researching this account.",
        expectation="Open the account to read what Signora found.",
        occurred_at=NOW,
    )


class TestOnePersonsNotificationsAreNotAnothers:
    async def test_a_colleague_does_not_receive_this_persons_feed(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """🔴 **The invariant, in the one shape tenant isolation cannot catch.**"""
        workspace_id, alice, bob = uuid4(), uuid4(), uuid4()

        async with admin_session_factory() as owner, owner.begin():
            await _a_workspace(owner, workspace_id, alice)

        # ⚡ **Written by the platform acting for nobody in particular**, which
        # is the case the workspace-scoped INSERT policy exists to permit.
        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=alice
        ) as session:
            await SqlAlchemyNotificationRepository(session).record(_for(workspace_id, alice))

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=alice
        ) as session:
            hers = await SqlAlchemyNotificationRepository(session).feed(
                workspace_id, alice, limit=10
            )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=bob
        ) as session:
            his = await SqlAlchemyNotificationRepository(session).feed(
                workspace_id, bob, limit=10
            )

        assert len(hers) == 1, "Alice cannot read the notification addressed to her"
        assert his == [], (
            "Bob received a notification addressed to Alice. Tenant isolation "
            "cannot catch this — they are legitimately in the same workspace, "
            "and only the recipient predicate separates them."
        )

    async def test_the_policy_hides_the_row_itself_not_only_the_query(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """⚡ **Through the POLICY, asserted on the row rather than the answer.**

        ⛔ **A repository that filtered correctly over a table with no policy
        would pass the test above.**
        """
        workspace_id, alice, bob = uuid4(), uuid4(), uuid4()

        async with admin_session_factory() as owner, owner.begin():
            await _a_workspace(owner, workspace_id, alice)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=alice
        ) as session:
            await SqlAlchemyNotificationRepository(session).record(_for(workspace_id, alice))

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=bob
        ) as session:
            # ⛔ **No `recipient_id` predicate in this SQL, deliberately.**
            visible = await session.scalar(
                text("SELECT count(*) FROM notification WHERE workspace_id = :w"),
                {"w": str(workspace_id)},
            )

        assert visible == 0, (
            "Bob's session can see a notification addressed to Alice. The RLS "
            "policy on notification is missing its recipient predicate, and "
            "every workspace-level guarantee is intact while this leaks."
        )

    async def test_alice_sees_her_own_row_so_the_policy_is_not_denying_everything(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """⚠️ **The half that stops the test above passing vacuously.**

        ⛔ **A policy denying every row would satisfy *Bob sees nothing*** — and
        the bell would be permanently empty while the invariant read green.
        """
        workspace_id, alice = uuid4(), uuid4()

        async with admin_session_factory() as owner, owner.begin():
            await _a_workspace(owner, workspace_id, alice)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=alice
        ) as session:
            await SqlAlchemyNotificationRepository(session).record(_for(workspace_id, alice))

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=alice
        ) as session:
            visible = await session.scalar(
                text("SELECT count(*) FROM notification WHERE workspace_id = :w"),
                {"w": str(workspace_id)},
            )

        assert visible == 1, "Alice cannot see her own notification — the policy denies everything"


class TestAColleagueMayWriteOneAndThatIsTheAsymmetry:
    async def test_one_person_can_create_a_notification_addressed_to_another(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """🔴 **The half a symmetric policy would have broken silently.**

        ⚠️ **An INSERT policy requiring `recipient_id = current_setting('app.user_id')`
        would make it impossible to notify anybody but yourself** — ⛔ **which is
        every case a notification exists for**, and the failure would look like
        *nothing is ever delivered* rather than like a policy mistake.

        ⚡ **This is the mention: Alice writes, Bob reads.**
        """
        workspace_id, alice, bob = uuid4(), uuid4(), uuid4()

        async with admin_session_factory() as owner, owner.begin():
            await _a_workspace(owner, workspace_id, alice)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=alice
        ) as session:
            await SqlAlchemyNotificationRepository(session).record(_for(workspace_id, bob))

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=bob
        ) as session:
            his = await SqlAlchemyNotificationRepository(session).feed(
                workspace_id, bob, limit=10
            )

        assert len(his) == 1, (
            "Alice could not notify Bob. The INSERT policy is narrowed by "
            "recipient, which permits notifying nobody but yourself."
        )

    async def test_a_notification_cannot_be_written_into_another_workspace(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """⛔ **The INSERT policy is workspace-scoped, not absent.**

        ⚠️ **Relaxing the recipient predicate on the write is exactly where a
        tenant predicate gets dropped by accident**, so it is asserted rather
        than assumed.
        """
        theirs, ours, alice = uuid4(), uuid4(), uuid4()

        async with admin_session_factory() as owner, owner.begin():
            await _a_workspace(owner, theirs, alice)
            await _a_workspace(owner, ours, alice)

        async with tenant_scoped_session(
            session_factory, workspace_id=ours, user_id=alice
        ) as session:
            with pytest.raises(Exception, match="row-level security|violates"):
                await SqlAlchemyNotificationRepository(session).record(_for(theirs, alice))


class TestANotificationIsAFactAndTheTableSaysSo:
    async def test_the_application_role_cannot_update_one(
        self,
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """📁 [§2](../../../CLAUDE.md), *immutability is the default for anything
        that records a fact*.

        ⛔ **No `UPDATE` grant** — ⚡ **correcting the summary of a nudge somebody
        already read would change what they were told after they were told
        it**, and *dismissing* one is a READ recorded next door in
        `notification_read`.

        ⚠️ **`DELETE` is present and is a DIFFERENT question, which this table
        first got wrong.** 📁 `test_tenancy_policy.py`: *"Erasability is a
        property of the TENANCY model, not of what a row means: a workspace that
        cannot be deleted is a retention problem on every table it owns,
        immutable or not."* ⛔ **The absent grant is the claim; the present one
        is asserted so removing it later fails here rather than in a suite
        nobody connects to this table.**
        """
        async with admin_session_factory() as owner:
            granted = set(
                (
                    await owner.execute(
                        text(
                            "SELECT privilege_type FROM information_schema.role_table_grants "
                            "WHERE table_name = 'notification' AND grantee = 'signora_app'"
                        )
                    )
                )
                .scalars()
                .all()
            )

        assert granted == {"SELECT", "INSERT", "DELETE"}, (
            f"the notification table's grants are {sorted(granted)}. UPDATE is "
            "withheld because a notification records that something happened "
            "and there is nothing about one to amend; DELETE is required "
            "because erasing a workspace is a tenancy obligation every "
            "tenant-owned table owes."
        )

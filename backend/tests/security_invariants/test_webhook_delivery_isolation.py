"""One workspace's deliveries are not another's — TASK-1481, migration ``0060``.

**This table is the odd one in its own package.** ``outbox_event``,
``processed_event`` and ``dead_letter_event`` sit beside it and are platform
infrastructure: ``signora_app`` inserts and cannot read, so the grant is the
only thing separating tenants there. ``webhook_delivery`` is tenant-owned
because its state reaches a customer's screen — **which means RLS is what
separates tenants here, and RLS is what this asserts.**

⛔ **The lifecycle test is deliberately in the same file.** The isolation
guarantee and the twenty-four hour guarantee are both properties of these rows,
and a suite that proves one where the other lives is a suite somebody splits.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.webhook_delivery.infrastructure.models import WebhookDeliveryModel
from modules.webhook_delivery.domain.delivery import (
    DELIVERY_WINDOW,
    DeliveryState,
    utcnow,
)
from modules.webhook_delivery.infrastructure.repository import (
    claim_due,
    enqueue,
    record_failure,
    record_success,
)
from signora_platform.db.session import tenant_scoped_session

NOW = utcnow()

pytestmark = pytest.mark.asyncio


async def _a_workspace(session: AsyncSession, workspace_id: UUID, founder: UUID) -> None:
    await session.execute(
        text(
            "INSERT INTO workspace (id, name, created_by, updated_by) "
            "VALUES (:id, :name, :by, :by)"
        ),
        {"id": str(workspace_id), "name": "Northwind", "by": str(founder)},
    )


class TestOneWorkspacesDeliveriesAreNotAnothers:
    async def test_rls_hides_another_workspaces_delivery(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """🔴 **The guarantee, proven by attempting the crossing.**"""
        theirs, ours, founder = uuid4(), uuid4(), uuid4()

        async with admin_session_factory() as owner, owner.begin():
            await _a_workspace(owner, theirs, founder)
            await _a_workspace(owner, ours, founder)

        async with tenant_scoped_session(
            session_factory, workspace_id=theirs, user_id=founder
        ) as session:
            await enqueue(
                session,
                workspace_id=theirs,
                endpoint_id=uuid4(),
                event_type="opportunity.opened",
                payload={"secret": "another customer's data"},
                now=NOW,
            )
            await session.flush()

        async with tenant_scoped_session(
            session_factory, workspace_id=ours, user_id=founder
        ) as session:
            rows = (await session.execute(select(WebhookDeliveryModel))).scalars().all()

        assert rows == []

    async def test_the_worker_only_claims_deliveries_in_its_own_scope(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """⛔ **`claim_due` carries no `workspace_id` filter, and must not need one.**

        RLS is the authoritative control (§13). A claim that is correct only
        because it remembered to filter is one the next caller writes without
        the filter — so the read is written the way a worker would write it, and
        the isolation still has to hold.
        """
        theirs, ours, founder = uuid4(), uuid4(), uuid4()

        async with admin_session_factory() as owner, owner.begin():
            await _a_workspace(owner, theirs, founder)
            await _a_workspace(owner, ours, founder)

        for workspace in (theirs, ours):
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace, user_id=founder
            ) as session:
                await enqueue(
                    session,
                    workspace_id=workspace,
                    endpoint_id=uuid4(),
                    event_type="opportunity.opened",
                    payload={"workspace": str(workspace)},
                    now=NOW,
                )
                await session.flush()

        async with tenant_scoped_session(
            session_factory, workspace_id=ours, user_id=founder
        ) as session:
            claimed = await claim_due(session, now=NOW)

        assert [d.workspace_id for d in claimed] == [ours]


class TestTheTwentyFourHourGuarantee:
    async def test_a_failure_reschedules_and_a_success_is_terminal(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, founder = uuid4(), uuid4()

        async with admin_session_factory() as owner, owner.begin():
            await _a_workspace(owner, workspace_id, founder)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=founder
        ) as session:
            await enqueue(
                session,
                workspace_id=workspace_id,
                endpoint_id=uuid4(),
                event_type="opportunity.opened",
                payload={"id": 1},
                now=NOW,
            )
            await session.flush()

            [delivery] = await claim_due(session, now=NOW)
            record_failure(delivery, now=NOW, reason="connection refused")
            await session.flush()

            assert delivery.state == DeliveryState.PENDING.value
            assert delivery.next_attempt_at is not None
            assert delivery.last_failure_reason == "connection refused"
            assert delivery.attempts == 1

            record_success(delivery, now=NOW + timedelta(seconds=5))
            await session.flush()

            assert delivery.state == DeliveryState.DELIVERED.value
            assert delivery.next_attempt_at is None

    async def test_the_window_expires_and_the_payload_survives_it(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """🔴 **The design's sentence, end to end.**

        ⛔ *"…then park with the payload retained."* **The retention is asserted
        by reading the payload back AFTER parking** — a parked delivery a
        customer cannot inspect is indistinguishable from one that was dropped.
        """
        workspace_id, founder = uuid4(), uuid4()
        payload = {"account": "Vantage Logistics", "amount": 1_240_000}

        async with admin_session_factory() as owner, owner.begin():
            await _a_workspace(owner, workspace_id, founder)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=founder
        ) as session:
            await enqueue(
                session,
                workspace_id=workspace_id,
                endpoint_id=uuid4(),
                event_type="opportunity.opened",
                payload=payload,
                now=NOW,
            )
            await session.flush()

            [delivery] = await claim_due(session, now=NOW)
            record_failure(
                delivery,
                now=NOW + DELIVERY_WINDOW,
                reason="endpoint unreachable for 24 hours",
            )
            await session.flush()

            assert delivery.state == DeliveryState.PARKED.value
            assert delivery.next_attempt_at is None
            assert delivery.payload == payload

        # ⚡ **Read back in a NEW session**, so the assertion is about the row
        # rather than about the object still in the identity map.
        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=founder
        ) as session:
            [row] = (await session.execute(select(WebhookDeliveryModel))).scalars().all()
            assert row.state == DeliveryState.PARKED.value
            assert row.payload == payload

    async def test_a_parked_delivery_is_never_claimed_again(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """⛔ **The window is a promise in both directions.**

        A parked delivery that a later poll picks up would keep calling a
        customer's endpoint after we told them we had stopped.
        """
        workspace_id, founder = uuid4(), uuid4()

        async with admin_session_factory() as owner, owner.begin():
            await _a_workspace(owner, workspace_id, founder)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=founder
        ) as session:
            await enqueue(
                session,
                workspace_id=workspace_id,
                endpoint_id=uuid4(),
                event_type="opportunity.opened",
                payload={},
                now=NOW,
            )
            await session.flush()

            [delivery] = await claim_due(session, now=NOW)
            record_failure(delivery, now=NOW + DELIVERY_WINDOW, reason="gone")
            await session.flush()

            assert await claim_due(session, now=NOW + DELIVERY_WINDOW * 2) == []

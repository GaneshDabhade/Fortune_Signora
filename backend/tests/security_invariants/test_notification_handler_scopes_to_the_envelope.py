"""**A notification lands in the workspace the ENVELOPE names, and nowhere else.**

📁 **[TASK-495](../../../docs/BACKLOG.md)**, the `notification.requested`
consumer.

## 🔴 Why this is a Security Invariant rather than a handler unit test

⚡ **Every event is workspace-scoped** ([§9](../../../CLAUDE.md)) **and the
envelope is the only trustworthy statement of which workspace.** ⛔ **A payload
that could name its own tenant would be a cross-workspace write one typo
away** — and the write here is a row a person then reads on every screen.

⚠️ **The defect this catches is one line long**: taking `workspace_id` from
`envelope.payload` instead of `envelope.workspace_id`. **It would pass every
behavioural test**, because in every ordinary run the two agree.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.workspace_tenancy.application.notify import Notify
from modules.workspace_tenancy.domain.notification import (
    NOTIFICATION_REQUESTED,
    Actor,
    ActorKind,
    Category,
    Channel,
    ChannelNotRegisteredError,
    NotificationChannelRegistry,
    NotificationRequested,
    Subject,
)
from modules.workspace_tenancy.infrastructure.composition import build_notifier
from modules.workspace_tenancy.infrastructure.repositories import (
    SqlAlchemyNotificationRepository,
)
from modules.workspace_tenancy.interface.handlers import deliver_requested_notification
from signora_platform.event_bus import EventEnvelope

pytestmark = pytest.mark.asyncio

NOW = datetime(2026, 8, 16, 9, 30, tzinfo=UTC)


def _an_envelope(*, workspace_id: UUID, recipient: UUID, claims: UUID | None = None) -> EventEnvelope:
    """⚡ **Built from the real event**, so the payload is the shape the producer
    emits rather than the shape this file imagines."""
    event = NotificationRequested(
        event_id=uuid4(),
        workspace_id=workspace_id,
        occurred_at=NOW,
        recipient_id=recipient,
        category=Category.NEEDS_YOU,
        actor=Actor(kind=ActorKind.AGENT, agent_name="Research"),
        subject=Subject(kind="opportunity", id=uuid4()),
        summary="Signora finished researching this account.",
        expectation="Open the account to read what Signora found.",
        channels=frozenset({Channel.IN_APP}),
    )
    payload = dict(event.to_payload())
    if claims is not None:
        # ⛔ **The forgery**: a payload asserting a workspace of its own.
        payload["workspace_id"] = str(claims)
    return EventEnvelope(
        event_id=event.event_id,
        event_type=NOTIFICATION_REQUESTED,
        event_version=1,
        workspace_id=workspace_id,
        occurred_at=NOW,
        producer_module="ai_research_engine",
        correlation_id=uuid4(),
        causation_id=None,
        payload=payload,
    )


class TestTheEnvelopeDecidesTheWorkspace:
    async def test_a_payload_claiming_another_workspace_is_ignored(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """🔴 **The envelope wins, and the forged field changes nothing.**"""
        from sqlalchemy import text

        ours, theirs, alice = uuid4(), uuid4(), uuid4()
        async with admin_session_factory() as owner, owner.begin():
            for workspace_id in (ours, theirs):
                await owner.execute(
                    text(
                        "INSERT INTO workspace (id, name, created_by, updated_by) "
                        "VALUES (:id, :name, :by, :by)"
                    ),
                    {"id": str(workspace_id), "name": "Northwind", "by": str(alice)},
                )

        await deliver_requested_notification(
            _an_envelope(workspace_id=ours, recipient=alice, claims=theirs),
            session_factory=session_factory,
            notify=build_notifier,
        )

        from signora_platform.db.session import tenant_scoped_session

        async with tenant_scoped_session(
            session_factory, workspace_id=theirs, user_id=alice
        ) as session:
            leaked = await SqlAlchemyNotificationRepository(session).feed(
                theirs, alice, limit=10
            )
        async with tenant_scoped_session(
            session_factory, workspace_id=ours, user_id=alice
        ) as session:
            landed = await SqlAlchemyNotificationRepository(session).feed(ours, alice, limit=10)

        assert leaked == [], (
            "the payload named a workspace and the handler believed it. Every "
            "event is workspace-scoped and the envelope is the only trustworthy "
            "statement of which one."
        )
        assert len(landed) == 1, "the notification did not land in the envelope's workspace"


class TestAnUnreachableChannelFailsLoudly:
    async def test_the_handler_does_not_swallow_an_unregistered_channel(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """⛔ **The event dead-letters rather than silently delivering nothing.**

        📁 [§10](../../../CLAUDE.md) — ⚡ **a channel that failed quietly makes a
        customer who was never told indistinguishable from one who was.**
        """

        def a_registry_serving_nothing(session: AsyncSession) -> Notify:
            return Notify(channels=NotificationChannelRegistry())

        with pytest.raises(ChannelNotRegisteredError):
            await deliver_requested_notification(
                _an_envelope(workspace_id=uuid4(), recipient=uuid4()),
                session_factory=session_factory,
                notify=a_registry_serving_nothing,
            )

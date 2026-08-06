"""A decision reaches the outbox, in the same transaction as the row — **TASK-432**.

**The one transition in this pipeline that produced no event.** Every other
stage announces what it concluded; a *human* decision was recorded in a row and
nowhere else, so `timeline` could not project it and nothing measuring whether
Signora's judgement was any good had a transition to read. **The row recorded
the state and nothing recorded the change**, which is evidence that cannot be
recovered afterwards.

**Against a real database and the real publisher.** `test_triage.py` proves the
use case *asks* for the announcement; that is a statement about the code. This
proves the row actually lands in `outbox_event` and that it lands **atomically
with the resolution** — a fact about PostgreSQL, and the one a fake cannot
establish. It is the same reason `test_resolution_persistence.py` exists beside
the domain tests.

**Read back under the privileged identity, never the application's.**
`signora_app` publishes events and is forbidden from reading them (migration
`0006`), so a test reading them as the application role would be asserting a
capability the architecture deliberately removed.
"""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.signal_engine.application.resolve import SignalNotFoundError
from modules.signal_engine.domain.resolution import (
    ACTIONED,
    DISMISSED,
    Actioned,
    DismissalReason,
    Dismissed,
)
from modules.signal_engine.infrastructure.composition import build_resolve_signal
from signora_platform.db import tenant_scoped_session
from signora_platform.event_bus import PostgresOutboxEventPublisher
from tests.signal_engine.test_resolution_persistence import _a_signal
from tests.signal_engine.test_signal_pipeline import _pipeline

pytestmark = pytest.mark.integration


async def _resolve(
    factory: async_sessionmaker[AsyncSession],
    workspace_id: UUID,
    user_id: UUID,
    signal_id: UUID,
    outcome: Actioned | Dismissed,
    *,
    correlation_id: UUID,
) -> None:
    """Through the production composition, on a tenant-scoped session.

    **`build_resolve_signal` with the real outbox publisher**, exactly as
    `apps/api/composition/triage.py` wires it. A test that assembled the use
    case differently would prove something about its own wiring.
    """
    async with tenant_scoped_session(
        factory, workspace_id=workspace_id, user_id=user_id
    ) as session:
        await build_resolve_signal(session, publisher=PostgresOutboxEventPublisher()).execute(
            workspace_id,
            signal_id,
            outcome=outcome,
            actor_id=user_id,
            correlation_id=correlation_id,
        )


async def _announcements(
    admin_session_factory: async_sessionmaker[AsyncSession],
) -> list[Any]:
    async with admin_session_factory() as session:
        return list(
            (
                await session.execute(
                    text(
                        "SELECT event_type, event_version, workspace_id, payload, "
                        "producer_module, correlation_id "
                        "FROM outbox_event WHERE event_type = 'signal.resolved' "
                        "ORDER BY created_at"
                    )
                )
            ).all()
        )


def _payload(row: Any) -> dict[str, Any]:
    return row.payload if isinstance(row.payload, dict) else json.loads(row.payload)


class TestADecisionIsAnnounced:
    async def test_it_reaches_the_outbox(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Acme")
        signal_id = await _a_signal(session_factory, workspace_id, user_id)
        correlation = uuid4()

        await _resolve(
            session_factory,
            workspace_id,
            user_id,
            signal_id,
            Actioned(),
            correlation_id=correlation,
        )

        rows = await _announcements(admin_session_factory)
        assert len(rows) == 1
        assert rows[0].producer_module == "signal_engine"
        assert rows[0].workspace_id == workspace_id
        assert rows[0].correlation_id == correlation

    async def test_the_payload_names_the_signal_the_account_and_the_person(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Enough for a consumer to place it without asking.** `timeline`
        projects per account and does not depend on this module's read
        surface, so an event it could not place would be one it must ignore."""
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Acme")
        signal_id = await _a_signal(session_factory, workspace_id, user_id)

        await _resolve(
            session_factory,
            workspace_id,
            user_id,
            signal_id,
            Actioned(),
            correlation_id=uuid4(),
        )

        payload = _payload((await _announcements(admin_session_factory))[0])
        assert payload["signal_id"] == str(signal_id)
        assert payload["actor_id"] == str(user_id)
        assert payload["outcome"] == ACTIONED
        assert UUID(payload["entity_id"])
        assert payload["supersedes"] is None

    async def test_a_dismissals_reason_never_reaches_the_bus(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**An event carries an identity, not a body.** A dismissal reason is
        a sentence a customer typed about why Signora was wrong; publishing it
        copies it into every subscriber's storage, and a bus cannot take it
        back. Asserted against the stored row rather than the object, because
        the row is what a subscriber will actually read."""
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Acme")
        signal_id = await _a_signal(session_factory, workspace_id, user_id)

        await _resolve(
            session_factory,
            workspace_id,
            user_id,
            signal_id,
            Dismissed(reason=DismissalReason("They already bought from us.")),
            correlation_id=uuid4(),
        )

        row = (await _announcements(admin_session_factory))[0]
        assert "already bought" not in json.dumps(_payload(row))
        assert _payload(row)["outcome"] == DISMISSED

    async def test_changing_your_mind_announces_what_it_replaced(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Two announcements, and the second names the first.** A consumer
        that acted on the earlier decision would otherwise count both."""
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Acme")
        signal_id = await _a_signal(session_factory, workspace_id, user_id)

        await _resolve(
            session_factory,
            workspace_id,
            user_id,
            signal_id,
            Dismissed(reason=DismissalReason("Not relevant.")),
            correlation_id=uuid4(),
        )
        await _resolve(
            session_factory,
            workspace_id,
            user_id,
            signal_id,
            Actioned(),
            correlation_id=uuid4(),
        )

        first, second = (_payload(row) for row in await _announcements(admin_session_factory))
        assert first["supersedes"] is None
        assert second["supersedes"] == first["resolution_id"]


class TestNothingIsAnnouncedThatDidNotHappen:
    async def test_a_signal_this_workspace_cannot_see_leaves_no_event(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The refusal is silent on the bus.** An event for a decision that
        was never recorded would tell the pipeline something untrue — and the
        transaction is what guarantees it, not the ordering of two statements.
        """
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Acme")

        with pytest.raises(SignalNotFoundError):
            await _resolve(
                session_factory,
                workspace_id,
                user_id,
                uuid4(),
                Actioned(),
                correlation_id=uuid4(),
            )

        assert await _announcements(admin_session_factory) == []

    async def test_the_resolution_and_its_announcement_commit_together(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Neither survives alone.** The outbox exists so a consumer can
        never hear about something that did not happen; a session that failed
        after the row and before the event would break that in the direction
        nobody notices — silently, and only under load.
        """
        workspace_id, user_id = await _pipeline(session_factory, admin_session_factory, "Acme")
        signal_id = await _a_signal(session_factory, workspace_id, user_id)

        with pytest.raises(RuntimeError):
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=user_id
            ) as session:
                await build_resolve_signal(
                    session, publisher=PostgresOutboxEventPublisher()
                ).execute(
                    workspace_id,
                    signal_id,
                    outcome=Actioned(),
                    actor_id=user_id,
                    correlation_id=uuid4(),
                )
                raise RuntimeError("something after the write fails")

        assert await _announcements(admin_session_factory) == []
        async with admin_session_factory() as session:
            stored = await session.execute(
                text("SELECT count(*) FROM signal_resolution WHERE signal_id = :s"),
                {"s": signal_id},
            )
            assert stored.scalar_one() == 0

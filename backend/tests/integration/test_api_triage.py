"""*"Have I dealt with it?"* — the queue over HTTP.

**The read half of TASK-405.** Recording a decision has no route yet: every
write surface in the repository carries its own authorization `Resource`, there
is no `signal` one, and adding it touches `signora_platform/` — 🔴 on the
Change Budget. [C-224](../../../docs/LANE_COORDINATION.md) carries the request.

So these tests assert what a customer can actually reach today: **every live
hypothesis about an account, with the decision in force about it, filtered by
state.** The decisions themselves are written through the use case, which is
where they will come from once the route exists — so the read is exercised
against real rows rather than against an empty table.
"""

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.api.main import create_app
from modules.signal_engine.domain.resolution import (
    Actioned,
    DismissalReason,
    Dismissed,
    Outcome,
    Snoozed,
)
from modules.signal_engine.infrastructure.composition import build_resolve_signal
from signora_platform.db import tenant_scoped_session
from signora_platform.event_bus import PostgresOutboxEventPublisher
from signora_platform.settings import Settings
from signora_platform.tests.keys import (
    TEST_AUDIENCE,
    TEST_ISSUER,
    KeyPair,
    generate_key_pair,
    mint_token,
)
from tests.conftest import DEFAULT_APP_DATABASE_URL
from tests.opportunity_engine.test_opportunity_pipeline import _tracked

pytestmark = pytest.mark.integration

#: The baseline scenario's evidence is months old, so every hypothesis it forms
#: is past its shelf life and a *live* read correctly returns nothing. These
#: tests need the other case, so they ingest at a recent epoch the way the
#: Playground does — the same code path and the same scenario file.
_EPOCH = timedelta(days=150)
_ASKED = timedelta(days=35)


def _recent() -> dict[str, Any]:
    midnight = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    return {"epoch": midnight - _EPOCH, "moment": midnight - _ASKED}


@pytest.fixture(scope="session")
def key_pair() -> KeyPair:
    return generate_key_pair()


@pytest.fixture
async def client(key_pair: KeyPair) -> AsyncIterator[AsyncClient]:
    settings = Settings(
        environment="test",
        database_url=DEFAULT_APP_DATABASE_URL,
        jwt_public_key=key_pair.public_pem,
        jwt_issuer=TEST_ISSUER,
        jwt_audience=TEST_AUDIENCE,
    )
    app = create_app(settings)
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http,
    ):
        yield http


def _auth(key_pair: KeyPair, user_id: UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {mint_token(key_pair, user_id=user_id)}"}


async def _triage(
    client: AsyncClient,
    key_pair: KeyPair,
    user_id: UUID,
    workspace_id: UUID,
    account_id: UUID,
    *,
    state: str | None = None,
) -> Any:
    query = f"?state={state}" if state else ""
    return await client.get(
        f"/workspaces/{workspace_id}/accounts/{account_id}/triage{query}",
        headers=_auth(key_pair, user_id),
    )


async def _decide(
    factory: async_sessionmaker[AsyncSession],
    workspace_id: UUID,
    user_id: UUID,
    signal_id: UUID,
    outcome: Outcome,
) -> None:
    """Through the use case, which is where the route will call once it
    exists. **Not raw SQL** — a fixture that bypassed the write would test the
    read against rows the product cannot actually produce.

    **The real outbox publisher, as the composition root wires it** (TASK-432).
    Recording a decision now also announces it, and a fixture publishing to a
    double would leave this read tested against a write the product does not
    perform — the same reason it does not use raw SQL."""
    async with tenant_scoped_session(
        factory, workspace_id=workspace_id, user_id=user_id
    ) as session:
        await build_resolve_signal(session, publisher=PostgresOutboxEventPublisher()).execute(
            workspace_id,
            signal_id,
            outcome=outcome,
            actor_id=user_id,
            correlation_id=uuid4(),
        )


class TestTheQueueShowsWhatIsStillYours:
    async def test_a_signal_nobody_has_decided_about_is_open(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**No decision is `open`, and carries no resolution.** Absent is not
        a decision to do nothing — that is what `actioned` is for."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind", **_recent()
        )

        response = await _triage(client, key_pair, user_id, workspace_id, entity_id)

        assert response.status_code == 200, response.text
        entries = response.json()["entries"]
        assert entries, "the recent-epoch scenario is expected to hold live hypotheses"
        assert all(entry["state"] == "open" for entry in entries)
        assert all(entry["resolution"] is None for entry in entries)

    async def test_dismissing_one_closes_it_and_records_the_reason(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind", **_recent()
        )
        first = (await _triage(client, key_pair, user_id, workspace_id, entity_id)).json()
        signal_id = UUID(first["entries"][0]["signal_id"])

        await _decide(
            session_factory,
            workspace_id,
            user_id,
            signal_id,
            Dismissed(reason=DismissalReason("They hired for the role internally.")),
        )

        after = (await _triage(client, key_pair, user_id, workspace_id, entity_id)).json()
        decided = next(e for e in after["entries"] if e["signal_id"] == str(signal_id))
        assert decided["state"] == "closed"
        assert decided["resolution"]["reason"] == "They hired for the role internally."
        assert decided["resolution"]["actor_id"] == str(user_id)

    async def test_filtering_by_state_leaves_the_closed_one_out(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The queue, as opposed to the list.** `?state=open` is what a
        seller sees; omitting it returns closed rows too, because nothing is
        deleted and an audit needs to see what left."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind", **_recent()
        )
        first = (await _triage(client, key_pair, user_id, workspace_id, entity_id)).json()
        signal_id = UUID(first["entries"][0]["signal_id"])
        total = len(first["entries"])

        await _decide(session_factory, workspace_id, user_id, signal_id, Actioned())

        open_only = (
            await _triage(client, key_pair, user_id, workspace_id, entity_id, state="open")
        ).json()
        everything = (await _triage(client, key_pair, user_id, workspace_id, entity_id)).json()

        assert len(open_only["entries"]) == total - 1
        assert str(signal_id) not in {e["signal_id"] for e in open_only["entries"]}
        assert len(everything["entries"]) == total

    async def test_a_snoozed_signal_leaves_the_open_queue_without_being_closed(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """*"Not now"* is not *"no"*. It is absent from `open`, present in
        `snoozed`, and **the signal is untouched** — which is what makes its
        evidence intact when it returns."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind", **_recent()
        )
        first = (await _triage(client, key_pair, user_id, workspace_id, entity_id)).json()
        signal_id = UUID(first["entries"][0]["signal_id"])

        await _decide(
            session_factory,
            workspace_id,
            user_id,
            signal_id,
            Snoozed(until=datetime.now(UTC) + timedelta(days=7)),
        )

        snoozed = (
            await _triage(client, key_pair, user_id, workspace_id, entity_id, state="snoozed")
        ).json()
        open_only = (
            await _triage(client, key_pair, user_id, workspace_id, entity_id, state="open")
        ).json()

        assert {e["signal_id"] for e in snoozed["entries"]} == {str(signal_id)}
        assert str(signal_id) not in {e["signal_id"] for e in open_only["entries"]}

    async def test_an_account_with_nothing_live_answers_rather_than_erroring(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """An empty queue is an answer. **Never a 404** — the account exists
        and there is simply nothing to triage."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        response = await _triage(client, key_pair, user_id, workspace_id, entity_id)

        assert response.status_code == 200, response.text
        assert response.json()["entries"] == []


class TestNothingIsDeleted:
    async def test_a_regretted_dismissal_is_still_readable(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """*"Every resolution is auditable."* The queue shows what is true now;
        this shows how it got there, **including the reason somebody gave for a
        dismissal they later took back.**"""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind", **_recent()
        )
        first = (await _triage(client, key_pair, user_id, workspace_id, entity_id)).json()
        signal_id = UUID(first["entries"][0]["signal_id"])

        await _decide(
            session_factory,
            workspace_id,
            user_id,
            signal_id,
            Dismissed(reason=DismissalReason("Not a competitor.")),
        )
        await _decide(session_factory, workspace_id, user_id, signal_id, Actioned())

        response = await client.get(
            f"/workspaces/{workspace_id}/signals/{signal_id}/decisions",
            headers=_auth(key_pair, user_id),
        )

        assert response.status_code == 200, response.text
        decisions = response.json()["decisions"]
        assert [d["outcome"] for d in decisions] == ["dismissed", "actioned"]
        assert decisions[0]["reason"] == "Not a competitor."
        assert decisions[1]["supersedes"] == decisions[0]["id"]

    async def test_a_signal_nobody_decided_about_has_an_empty_history(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Not a 404.** *"Nobody has decided yet"* is an answer, and it is
        not the same fact as *"no such signal"*."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind", **_recent()
        )
        first = (await _triage(client, key_pair, user_id, workspace_id, entity_id)).json()
        signal_id = first["entries"][0]["signal_id"]

        response = await client.get(
            f"/workspaces/{workspace_id}/signals/{signal_id}/decisions",
            headers=_auth(key_pair, user_id),
        )

        assert response.status_code == 200, response.text
        assert response.json()["decisions"] == []

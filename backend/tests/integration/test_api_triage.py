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


async def _queue(
    client: AsyncClient,
    key_pair: KeyPair,
    user_id: UUID,
    workspace_id: UUID,
    *,
    state: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> Any:
    params: list[str] = []
    if state:
        params.append(f"state={state}")
    if limit is not None:
        params.append(f"limit={limit}")
    if cursor:
        params.append(f"cursor={cursor}")
    query = f"?{'&'.join(params)}" if params else ""
    return await client.get(
        f"/workspaces/{workspace_id}/triage{query}", headers=_auth(key_pair, user_id)
    )


async def _resolve(
    client: AsyncClient,
    key_pair: KeyPair,
    user_id: UUID,
    workspace_id: UUID,
    signal_id: UUID,
    outcome: dict[str, Any],
) -> Any:
    return await client.post(
        f"/workspaces/{workspace_id}/signals/{signal_id}/resolution",
        json={"outcome": outcome},
        headers=_auth(key_pair, user_id),
    )


class TestTheWorkspaceQueue:
    """**The read [C-228](../../../docs/LANE_COORDINATION.md) found missing.**

    The per-account triage answers *"what is outstanding here"*. The approved
    Signal Center is *"a triage queue, not a notification list"* and asks the
    question across the workspace — and until this endpoint there was no way
    to ask it at any layer.
    """

    async def test_it_returns_what_is_waiting_across_the_workspace(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind", **_recent()
        )

        response = await _queue(client, key_pair, user_id, workspace_id)

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["items"], "the recent-epoch scenario is expected to hold live hypotheses"
        assert all(entry["state"] == "open" for entry in body["items"])
        # **Contains, not equals** — and the difference is the whole point of
        # this endpoint. The scenario seeds several accounts in one workspace,
        # and a queue that returned only the one the test happened to name
        # would be the per-account read wearing a new path.
        assert str(entity_id) in {entry["entity_id"] for entry in body["items"]}
        assert all(entry["entity_id"] for entry in body["items"])

    async def test_a_workspace_with_nothing_outstanding_gets_an_empty_page(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**An empty queue is an answer, not an error.** A product that 404'd
        on *"you are finished"* would be treating success as a fault."""
        user_id = uuid4()
        created = await client.post(
            "/workspaces", json={"name": "Acme"}, headers=_auth(key_pair, user_id)
        )
        workspace_id = UUID(created.json()["id"])

        response = await _queue(client, key_pair, user_id, workspace_id)

        assert response.status_code == 200, response.text
        assert response.json() == {"items": [], "next_cursor": None, "has_more": False}

    async def test_a_decision_takes_a_signal_out_of_the_open_queue(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Every item leaves the list by a decision** — the screen's whole
        promise, asserted end to end through the two new routes together."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind", **_recent()
        )
        first = (await _queue(client, key_pair, user_id, workspace_id)).json()["items"][0]
        signal_id = UUID(first["signal_id"])

        recorded = await _resolve(
            client, key_pair, user_id, workspace_id, signal_id, {"kind": "actioned"}
        )

        assert recorded.status_code == 201, recorded.text
        still_open = (await _queue(client, key_pair, user_id, workspace_id, state="open")).json()[
            "items"
        ]
        assert str(signal_id) not in {e["signal_id"] for e in still_open}

    async def test_it_is_paged_and_the_page_is_bounded(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**A queue is unbounded by nature**, so the read is paged — an
        endpoint that returned every live signal would be the unbounded fetch
        §14 forbids, on the screen most likely to have thousands."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind", **_recent()
        )

        first = (await _queue(client, key_pair, user_id, workspace_id, limit=1)).json()

        assert len(first["items"]) <= 1
        if first["has_more"]:
            assert first["next_cursor"]
            second = await _queue(
                client, key_pair, user_id, workspace_id, limit=1, cursor=first["next_cursor"]
            )
            assert second.status_code == 200, second.text
            assert second.json()["items"][0]["signal_id"] != first["items"][0]["signal_id"]

    async def test_another_workspace_sees_none_of_it(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, _, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind", **_recent()
        )
        stranger = uuid4()

        response = await _queue(client, key_pair, stranger, workspace_id)

        assert response.status_code == 404, response.text


class TestRecordingADecisionOverHttp:
    """**The route [TASK-405](../../../docs/BACKLOG.md) built everything for
    and withheld**, because a write surface needs an authorization `Resource`
    and there was none. `signal:resolve` exists now.
    """

    async def test_a_dismissal_requires_a_reason(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Refused at the edge, not behind it.** The discriminated union
        makes a reasonless dismissal unconstructable, so it is a `422` rather
        than a domain exception mapped to one."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind", **_recent()
        )
        signal_id = UUID(
            (await _queue(client, key_pair, user_id, workspace_id)).json()["items"][0]["signal_id"]
        )

        response = await _resolve(
            client, key_pair, user_id, workspace_id, signal_id, {"kind": "dismissed"}
        )

        assert response.status_code == 422, response.text

    async def test_a_snooze_that_has_already_elapsed_is_refused(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The signal would come straight back, so the product says so rather
        than accepting an instruction it cannot honour."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind", **_recent()
        )
        signal_id = UUID(
            (await _queue(client, key_pair, user_id, workspace_id)).json()["items"][0]["signal_id"]
        )
        past = (datetime.now(UTC) - timedelta(days=1)).isoformat()

        response = await _resolve(
            client,
            key_pair,
            user_id,
            workspace_id,
            signal_id,
            {"kind": "snoozed", "until": past},
        )

        assert response.status_code == 422, response.text

    async def test_the_decision_is_attributed_to_the_caller(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The verified principal, never the body.** A request able to name
        its own actor could sign somebody else's name to a decision that
        outlives them."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind", **_recent()
        )
        signal_id = UUID(
            (await _queue(client, key_pair, user_id, workspace_id)).json()["items"][0]["signal_id"]
        )

        recorded = await _resolve(
            client,
            key_pair,
            user_id,
            workspace_id,
            signal_id,
            {"kind": "dismissed", "reason": "Already a customer."},
        )

        assert recorded.status_code == 201, recorded.text
        assert recorded.json()["actor_id"] == str(user_id)

    async def test_a_signal_in_another_workspace_is_a_404(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Never distinguished from *no such signal*.** Telling the two apart
        answers *"does workspace X hold this?"* to somebody who cannot see it."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind", **_recent()
        )

        response = await _resolve(
            client, key_pair, user_id, workspace_id, uuid4(), {"kind": "actioned"}
        )

        assert response.status_code == 404, response.text

    async def test_changing_your_mind_supersedes_rather_than_edits(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """*"Nothing is deleted; every resolution is auditable."* The second
        decision names the first rather than replacing it."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind", **_recent()
        )
        signal_id = UUID(
            (await _queue(client, key_pair, user_id, workspace_id)).json()["items"][0]["signal_id"]
        )

        first = await _resolve(
            client,
            key_pair,
            user_id,
            workspace_id,
            signal_id,
            {"kind": "dismissed", "reason": "Wrong account."},
        )
        second = await _resolve(
            client, key_pair, user_id, workspace_id, signal_id, {"kind": "actioned"}
        )

        assert second.status_code == 201, second.text
        assert second.json()["supersedes"] == first.json()["id"]

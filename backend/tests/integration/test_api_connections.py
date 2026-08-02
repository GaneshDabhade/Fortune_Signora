"""The connections surface over the full stack.

The three routes a customer's Connection Center actually calls, exercised
through JWT verification, membership verification, RLS context, Casbin, and
PostgreSQL as the least-privileged role.

**What these are for.** `interface/router.py` was the module's least-covered
file, and a route is the one layer no unit test reaches: authorization, the
response shape, and the *"who is disconnecting this"* attribution all live
between the HTTP boundary and the application layer. Two of the assertions
below — that a member may read and may **not** disconnect, and that the
disconnect names the caller — exist nowhere else.
"""

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.api.main import create_app
from modules.integrations.application.connect import ConnectInput, ConnectSystem
from modules.integrations.domain.grant import Credential
from modules.integrations.infrastructure.repository import (
    SqlConnectedAccountRepository,
    SqlGrantStore,
)
from modules.integrations.infrastructure.secrets import EncryptedSecretStore
from signora_platform.db import tenant_scoped_session
from signora_platform.settings import Settings
from signora_platform.tests.keys import (
    TEST_AUDIENCE,
    TEST_ISSUER,
    KeyPair,
    generate_key_pair,
    mint_token,
)
from tests.conftest import DEFAULT_APP_DATABASE_URL

pytestmark = pytest.mark.integration

KEY = Fernet.generate_key().decode()


@pytest.fixture(scope="session")
def key_pair() -> KeyPair:
    return generate_key_pair()


@pytest.fixture(autouse=True)
def integration_secret_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """The module's own `Settings`, injected the way the composition root does.

    It has **no default** — a defaulted Fernet key would ship a known one,
    which reads as protection and is not. So a test that exercises the
    disconnect route has to supply one, exactly as a deployment does.
    """
    from apps.api.composition import integrations as composition

    monkeypatch.setenv("SIGNORA_INTEGRATIONS_SECRET_KEY", KEY)
    composition._settings.cache_clear()


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


async def _workspace(client: AsyncClient, key_pair: KeyPair, user_id: UUID) -> UUID:
    response = await client.post(
        "/workspaces", json={"name": "Acme"}, headers=_auth(key_pair, user_id)
    )
    assert response.status_code == 201, response.text
    return UUID(response.json()["id"])


async def _add_member(
    client: AsyncClient, key_pair: KeyPair, owner: UUID, workspace: UUID, member: UUID
) -> None:
    response = await client.post(
        f"/workspaces/{workspace}/members",
        json={"user_id": str(member), "role": "member"},
        headers=_auth(key_pair, owner),
    )
    assert response.status_code in (200, 201), response.text


async def _connect(
    session_factory: async_sessionmaker[AsyncSession],
    workspace: UUID,
    actor: UUID,
    *,
    integration: str = "hubspot",
    label: str = "Acme production",
) -> UUID:
    """Data enters the way it will in production — through the use case, never
    by inserting rows (`CLAUDE.md` §20e, *test data*)."""
    async with tenant_scoped_session(
        session_factory, workspace_id=workspace, user_id=actor
    ) as session:
        account = await ConnectSystem(
            SqlConnectedAccountRepository(session),
            SqlGrantStore(session),
            EncryptedSecretStore(session, KEY),
        ).execute(
            ConnectInput(
                workspace_id=workspace,
                actor_id=actor,
                integration=integration,
                external_account_id=str(uuid4()),
                label=label,
                endpoint=None,
                credential=Credential(kind="bearer", material=b"token"),
                scopes=("crm.objects.contacts.read",),
                expires_at=None,
                refreshable=True,
            ),
            at=datetime.now(UTC),
        )
        await session.commit()
    return account.id


class TestAnOrganizationThatHasConnectedNothing:
    async def test_the_connections_list_is_empty_rather_than_a_404(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await client.get(
            f"/workspaces/{workspace}/connections", headers=_auth(key_pair, user)
        )

        assert response.status_code == 200, response.text
        assert response.json() == []

    async def test_the_systems_list_still_says_what_could_be_connected(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**The reason this route exists separately.** A screen built only from
        what somebody already did cannot answer *"what are we missing?"*"""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        body = (
            await client.get(
                f"/workspaces/{workspace}/integrations", headers=_auth(key_pair, user)
            )
        ).json()

        assert {row["integration"] for row in body} >= {"hubspot", "google_calendar"}
        assert all(row["connections"] == [] for row in body)
        assert all(row["working"] is False for row in body)

    async def test_nothing_is_advertised_as_connectable_before_it_is(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """The product does not offer a button that cannot work. Until real
        credentials exist, every system reads as not yet available — asserted
        here so it cannot become true by accident."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        body = (
            await client.get(
                f"/workspaces/{workspace}/integrations", headers=_auth(key_pair, user)
            )
        ).json()

        assert all(row["connectable"] is False for row in body)


class TestAConnectedOrganization:
    async def test_the_connection_is_listed_with_nothing_needing_attention(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        await _connect(session_factory, workspace, user)

        body = (
            await client.get(
                f"/workspaces/{workspace}/connections", headers=_auth(key_pair, user)
            )
        ).json()

        assert len(body) == 1
        assert body[0]["label"] == "Acme production"
        assert body[0]["state"] == "connected"
        assert body[0]["attention"] == "none"

    async def test_no_bookkeeping_reaches_the_response(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """A screen showing a secret reference or a vendor's org id is showing
        the customer Signora's internals."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        await _connect(session_factory, workspace, user)

        body = (
            await client.get(
                f"/workspaces/{workspace}/connections", headers=_auth(key_pair, user)
            )
        ).json()

        assert not set(body[0]) & {
            "secret_ref",
            "external_account_id",
            "endpoint",
            "grant_id",
            "actor_id",
        }

    async def test_the_system_reads_as_working(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        await _connect(session_factory, workspace, user)

        body = (
            await client.get(
                f"/workspaces/{workspace}/integrations", headers=_auth(key_pair, user)
            )
        ).json()
        hubspot = next(row for row in body if row["integration"] == "hubspot")

        assert hubspot["working"] is True
        assert hubspot["needs_attention"] is False
        assert len(hubspot["connections"]) == 1


class TestDisconnecting:
    async def test_it_stops_the_connection_and_says_the_vendor_was_not_told(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """No adapter calls a vendor's revocation endpoint yet, so the response
        says so — and the screen passes that on rather than implying otherwise."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        connection = await _connect(session_factory, workspace, user)

        response = await client.post(
            f"/workspaces/{workspace}/connections/{connection}/disconnect",
            headers=_auth(key_pair, user),
        )

        assert response.status_code == 200, response.text
        assert response.json() == {
            "state": "disconnected",
            "revoked_at_provider": False,
            "already_disconnected": False,
        }

    async def test_a_second_press_is_not_an_error(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        connection = await _connect(session_factory, workspace, user)
        url = f"/workspaces/{workspace}/connections/{connection}/disconnect"

        await client.post(url, headers=_auth(key_pair, user))
        second = await client.post(url, headers=_auth(key_pair, user))

        assert second.status_code == 200, second.text
        assert second.json()["already_disconnected"] is True

    async def test_it_records_who_disconnected_it_without_losing_who_connected_it(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The attribution only the route can supply.** *"Who disconnected our
        CRM?"* is asked during an incident, and the answer exists at exactly one
        moment — this request."""
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)
        connection = await _connect(session_factory, workspace, owner)

        await client.post(
            f"/workspaces/{workspace}/connections/{connection}/disconnect",
            headers=_auth(key_pair, owner),
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace, user_id=owner
        ) as session:
            row = (
                await session.execute(
                    text(
                        "SELECT created_by, updated_by FROM connected_account WHERE id = :id"
                    ),
                    {"id": connection},
                )
            ).one()

        assert row.created_by == owner
        assert row.updated_by == owner

    async def test_a_connection_in_another_organization_is_not_found(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """404, never 403 — a caller who names a connection they cannot see
        learns nothing about whether it exists."""
        owner, outsider = uuid4(), uuid4()
        theirs = await _workspace(client, key_pair, owner)
        mine = await _workspace(client, key_pair, outsider)
        connection = await _connect(session_factory, theirs, owner)

        response = await client.post(
            f"/workspaces/{mine}/connections/{connection}/disconnect",
            headers=_auth(key_pair, outsider),
        )

        assert response.status_code == 404, response.text


class TestAuthorization:
    async def test_a_member_may_read_the_connections(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner, member = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)
        await _add_member(client, key_pair, owner, workspace, member)

        response = await client.get(
            f"/workspaces/{workspace}/connections", headers=_auth(key_pair, member)
        )

        assert response.status_code == 200, response.text

    async def test_a_member_may_not_disconnect_one(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Withdrawing an organization's access to its own CRM is an owner's
        decision.** The client hides the control as a courtesy; this is the
        check that actually decides."""
        owner, member = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)
        await _add_member(client, key_pair, owner, workspace, member)
        connection = await _connect(session_factory, workspace, owner)

        response = await client.post(
            f"/workspaces/{workspace}/connections/{connection}/disconnect",
            headers=_auth(key_pair, member),
        )

        assert response.status_code == 403, response.text

    async def test_a_stranger_sees_nothing_at_all(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner, stranger = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)

        response = await client.get(
            f"/workspaces/{workspace}/connections", headers=_auth(key_pair, stranger)
        )

        assert response.status_code == 404, response.text

    async def test_an_unauthenticated_caller_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        workspace = await _workspace(client, key_pair, uuid4())

        response = await client.get(f"/workspaces/{workspace}/connections")

        assert response.status_code == 401, response.text


class TestTheResponseShapeIsPurposeBuilt:
    async def test_every_field_a_client_relies_on_is_present(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        await _connect(session_factory, workspace, user)

        body: list[dict[str, Any]] = (
            await client.get(
                f"/workspaces/{workspace}/connections", headers=_auth(key_pair, user)
            )
        ).json()

        assert set(body[0]) == {
            "id",
            "integration",
            "label",
            "state",
            "connected_at",
            "attention",
            "reason",
        }

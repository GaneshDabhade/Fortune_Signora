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
from datetime import UTC, datetime, timedelta
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


def _connect_body(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "integration": "hubspot",
        "external_account_id": "24601",
        "label": "Acme production",
        "credential": {"kind": "bearer", "material": "a-real-looking-access-token"},
        "scopes": ["crm.objects.companies.read"],
        "refreshable": True,
    }
    body.update(overrides)
    return body


class TestConnectingOneOfYourOwnSystems:
    """**The use case existed and nothing exposed it.**

    `ConnectSystem` has been complete and tested since M13 S01, reachable only
    from a test helper — so a customer who finished a consent flow had nowhere
    to land. These exercise the route, which is the part that was missing.
    """

    async def test_a_connection_is_recorded_and_readable(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        created = await client.post(
            f"/workspaces/{workspace}/connections",
            json=_connect_body(),
            headers=_auth(key_pair, owner),
        )

        assert created.status_code == 201, created.text
        assert created.json()["integration"] == "hubspot"
        assert created.json()["label"] == "Acme production"
        assert created.json()["state"] == "connected"

        listed = await client.get(
            f"/workspaces/{workspace}/connections", headers=_auth(key_pair, owner)
        )
        assert [row["id"] for row in listed.json()] == [created.json()["id"]]

    async def test_the_system_stops_reading_as_missing(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """The customer's actual question — *is my CRM connected?* — changes."""
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        def hubspot(payload: list[dict[str, Any]]) -> dict[str, Any]:
            return next(row for row in payload if row["integration"] == "hubspot")

        before = await client.get(
            f"/workspaces/{workspace}/integrations", headers=_auth(key_pair, owner)
        )
        assert hubspot(before.json())["working"] is False

        await client.post(
            f"/workspaces/{workspace}/connections",
            json=_connect_body(),
            headers=_auth(key_pair, owner),
        )

        after = await client.get(
            f"/workspaces/{workspace}/integrations", headers=_auth(key_pair, owner)
        )
        assert hubspot(after.json())["working"] is True

    async def test_a_system_signora_does_not_understand_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**422 rather than 404**: the route exists and the request is
        well-formed; what does not exist is a system Signora understands. A
        caller fixes this by naming a different one, which is a different
        action from retrying."""
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        response = await client.post(
            f"/workspaces/{workspace}/connections",
            json=_connect_body(integration="pipedrive"),
            headers=_auth(key_pair, owner),
        )

        assert response.status_code == 422, response.text
        assert response.json()["error"]["code"] == "unknown_integration"

        listed = await client.get(
            f"/workspaces/{workspace}/connections", headers=_auth(key_pair, owner)
        )
        assert listed.json() == []

    async def test_an_expiring_credential_says_so_immediately(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**Attention is derived, and the connect path must derive it the same
        way the list does.** A grant that expires within the warning window is
        `soon` on the response that creates it, not only on the next read."""
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)
        soon = datetime.now(UTC).replace(microsecond=0) + timedelta(days=2)

        response = await client.post(
            f"/workspaces/{workspace}/connections",
            json=_connect_body(refreshable=False, expires_at=soon.isoformat()),
            headers=_auth(key_pair, owner),
        )

        assert response.status_code == 201, response.text
        assert response.json()["attention"] == "soon"
        assert response.json()["reason"] == "credential_expiring"

    async def test_connecting_the_same_account_twice_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**The database decided this, and it decided it before I did.**

        This test was written asserting a second connection would be created,
        on a docstring I had just written saying so. PostgreSQL refused it:
        `connected_account` is unique on `(workspace, integration, external
        account)`, because one HubSpot portal is one relationship however many
        times somebody consents to it — and the grant table's own comment had
        anticipated the sequel all along, *"a connection may accumulate revoked
        grants across reconnections."*

        The B-024 lesson again, one layer out: **a fake would have accepted
        this, and every caller of a route that did not yet exist would have got
        a `500` the first time a customer re-consented.**
        """
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        first = await client.post(
            f"/workspaces/{workspace}/connections",
            json=_connect_body(),
            headers=_auth(key_pair, owner),
        )
        assert first.status_code == 201, first.text

        second = await client.post(
            f"/workspaces/{workspace}/connections",
            json=_connect_body(label="Acme sandbox"),
            headers=_auth(key_pair, owner),
        )

        assert second.status_code == 409, second.text
        assert second.json()["error"]["code"] == "integration_already_connected"

    async def test_a_second_portal_of_the_same_system_is_allowed(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**The constraint is about the account, never the system.**

        An organization with two HubSpot portals has two connections, and a
        rule keyed on `integration` alone would have refused the second — which
        is why the unique index names the external account too.
        """
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        await client.post(
            f"/workspaces/{workspace}/connections",
            json=_connect_body(),
            headers=_auth(key_pair, owner),
        )
        second = await client.post(
            f"/workspaces/{workspace}/connections",
            json=_connect_body(external_account_id="24602", label="Acme EMEA"),
            headers=_auth(key_pair, owner),
        )

        assert second.status_code == 201, second.text
        listed = await client.get(
            f"/workspaces/{workspace}/connections", headers=_auth(key_pair, owner)
        )
        assert len(listed.json()) == 2

    async def test_disconnecting_then_connecting_again_works(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**Disconnect was irreversible, and building this route is what made
        it reachable enough to notice.**

        The unique index spans every state, so a disconnected connection kept
        the identity forever and the same portal could never be connected
        again. The transition table had allowed `DISCONNECTED → AUTHORIZING`
        and `REVOKED → AUTHORIZING` since it was written — *"the route back is
        re-authorization"* — and nothing had ever used either edge, because the
        use case always minted a new id.

        **The fix was to use the lifecycle that was already there**, which is
        why this asserts the same connection comes back rather than a second
        one appearing beside it.
        """
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        first = await client.post(
            f"/workspaces/{workspace}/connections",
            json=_connect_body(),
            headers=_auth(key_pair, owner),
        )
        await client.post(
            f"/workspaces/{workspace}/connections/{first.json()['id']}/disconnect",
            headers=_auth(key_pair, owner),
        )

        again = await client.post(
            f"/workspaces/{workspace}/connections",
            json=_connect_body(),
            headers=_auth(key_pair, owner),
        )

        assert again.status_code == 201, again.text
        assert again.json()["id"] == first.json()["id"]
        assert again.json()["state"] == "connected"

        listed = await client.get(
            f"/workspaces/{workspace}/connections", headers=_auth(key_pair, owner)
        )
        assert len(listed.json()) == 1


class TestTheCredentialNeverComesBack:
    async def test_no_response_field_carries_the_material(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**The one thing this endpoint must never do.**

        A screen renders what the API returns, a browser caches it, and a proxy
        logs it. The material goes in and nothing about it comes out.
        """
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        created = await client.post(
            f"/workspaces/{workspace}/connections",
            json=_connect_body(),
            headers=_auth(key_pair, owner),
        )

        assert "a-real-looking-access-token" not in created.text
        assert set(created.json()) == {
            "id",
            "integration",
            "label",
            "state",
            "connected_at",
            "attention",
            "reason",
        }

    async def test_a_rejected_request_does_not_echo_it_either(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**The property that lets this endpoint take a credential at all.**

        The platform's validation handler reports a field path and a message
        and never the input that failed. If that ever changes, a malformed
        connect request starts returning material to whoever sent it — so the
        guarantee is asserted here rather than assumed from
        `signora_platform/api/errors.py`.
        """
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        response = await client.post(
            f"/workspaces/{workspace}/connections",
            json=_connect_body(label=""),
            headers=_auth(key_pair, owner),
        )

        assert response.status_code == 422, response.text
        assert "a-real-looking-access-token" not in response.text


class TestConnectingIsAnOwnersDecision:
    async def test_a_member_may_not_connect_a_system(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**Symmetric with disconnecting**, and for the same reason: handing
        an organization's CRM to a third party is not something one member of
        the team decides for everybody."""
        owner, member = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)
        await _add_member(client, key_pair, owner, workspace, member)

        response = await client.post(
            f"/workspaces/{workspace}/connections",
            json=_connect_body(),
            headers=_auth(key_pair, member),
        )

        assert response.status_code == 403, response.text

    async def test_a_stranger_cannot_connect_into_a_workspace_they_named(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**404, never 403.** A caller who is not a member must not learn
        whether the organization exists."""
        owner, stranger = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)

        response = await client.post(
            f"/workspaces/{workspace}/connections",
            json=_connect_body(),
            headers=_auth(key_pair, stranger),
        )

        assert response.status_code == 404, response.text

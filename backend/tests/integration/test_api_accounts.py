"""The first customer-facing endpoint, over the full stack.

`GET /workspaces/{id}/accounts` answers *"which accounts should I work on
today?"* — and until M12.1 nothing the pipeline computed had an HTTP path at
all. These exercise the whole chain a real request traverses: JWT verification,
server-side membership verification, RLS context, Casbin authorization, the
six-deep read composition, and PostgreSQL as the least-privileged role.

**Behaviour, not implementation.** Nothing here asserts a SQL shape or a call
count; each test states something a customer would notice.
"""

from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.api.main import create_app
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
    async with app.router.lifespan_context(app), AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as http:
        yield http


def _auth(key_pair: KeyPair, user_id: UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {mint_token(key_pair, user_id=user_id)}"}


async def _workspace(client: AsyncClient, key_pair: KeyPair, user_id: UUID) -> UUID:
    response = await client.post(
        "/workspaces", json={"name": "Acme"}, headers=_auth(key_pair, user_id)
    )
    assert response.status_code == 201, response.text
    return UUID(response.json()["id"])


async def _accounts(
    client: AsyncClient, key_pair: KeyPair, user_id: UUID, workspace_id: UUID, **params: Any
) -> Any:
    return await client.get(
        f"/workspaces/{workspace_id}/accounts",
        params=params,
        headers=_auth(key_pair, user_id),
    )


class TestTheEndpointIsReachableAndScoped:
    async def test_a_member_sees_their_workspace(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await _accounts(client, key_pair, user, workspace)

        assert response.status_code == 200, response.text
        assert response.json() == {"items": [], "next_cursor": None, "has_more": False}

    async def test_a_workspace_with_no_accounts_is_an_empty_page_not_an_error(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """A new customer's first day. An empty list is the answer, and the
        frontend renders a designed empty state from it."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        body = (await _accounts(client, key_pair, user, workspace)).json()

        assert body["items"] == []
        assert body["has_more"] is False

    async def test_a_non_member_gets_404_never_403(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**A security property, not an inconsistency.** 403 would confirm the
        workspace exists, which is workspace enumeration (§7)."""
        owner, outsider = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)

        response = await _accounts(client, key_pair, outsider, workspace)

        assert response.status_code == 404

    async def test_a_workspace_that_does_not_exist_is_also_404(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """Indistinguishable from the case above, deliberately — a caller must
        not be able to tell a workspace they cannot see from one that is not
        there."""
        response = await _accounts(client, key_pair, uuid4(), uuid4())

        assert response.status_code == 404

    async def test_an_unauthenticated_request_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        workspace = await _workspace(client, key_pair, uuid4())

        response = await client.get(f"/workspaces/{workspace}/accounts")

        assert response.status_code == 401

    async def test_a_token_from_a_foreign_key_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        workspace = await _workspace(client, key_pair, uuid4())
        forged = generate_key_pair()

        response = await client.get(
            f"/workspaces/{workspace}/accounts", headers=_auth(forged, uuid4())
        )

        assert response.status_code == 401


class TestTheRequestIsValidatedBeforeItReachesTheDatabase:
    @pytest.mark.parametrize("limit", [0, -1, 201])
    async def test_a_limit_outside_the_permitted_range_is_refused(
        self, client: AsyncClient, key_pair: KeyPair, limit: int
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await _accounts(client, key_pair, user, workspace, limit=limit)

        assert response.status_code == 422

    async def test_a_cursor_this_api_did_not_issue_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """Cursors are opaque by contract: clients echo them back and never
        construct one. A fabricated cursor is a bad request, not an empty page
        — an empty page would look like *"you have no accounts"*."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await _accounts(
            client, key_pair, user, workspace, cursor="not-a-cursor-we-issued"
        )

        assert response.status_code == 400

    async def test_a_malformed_workspace_identifier_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        response = await client.get(
            "/workspaces/not-a-uuid/accounts", headers=_auth(key_pair, uuid4())
        )

        assert response.status_code == 422


class TestTheResponseShapeIsTheOneDocumented:
    async def test_the_envelope_is_the_repository_wide_cursor_page(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """One envelope across every collection in the API — a second shape
        per module is the anti-pattern §7 names."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        body = (await _accounts(client, key_pair, user, workspace)).json()

        assert set(body) == {"items", "next_cursor", "has_more"}

    async def test_the_row_exposes_no_internal_bookkeeping(self) -> None:
        """**Every field answers a question a salesperson would ask.**

        `generation`, `policy_version`, `originating_buying_score_id` and
        `contested_at_creation` are all real, all stored, and none of them is
        something a seller decides from — a row carrying them teaches a reader
        that the fields on it are not worth reading.
        """
        from modules.opportunity_engine.interface.schemas import AccountAttentionResponse

        fields = set(AccountAttentionResponse.model_fields)

        assert fields == {
            "id",
            "account_id",
            "score",
            "trend",
            "score_change",
            "trigger",
            "contested",
            "evidence",
            "stage",
            "owner_id",
            "opened_at",
        }
        for internal in (
            "generation",
            "policy_version",
            "originating_buying_score_id",
            "contested_at_creation",
            "workspace_id",
        ):
            assert internal not in fields

    async def test_the_schema_is_not_a_domain_entity(self) -> None:
        """Coupling the wire contract to the domain model makes a domain
        refactor a client-breaking change (19-api-conventions.md)."""
        from modules.opportunity_engine.domain.opportunity import Opportunity
        from modules.opportunity_engine.interface.schemas import AccountAttentionResponse

        assert not issubclass(AccountAttentionResponse, Opportunity)


class TestTheEndpointIsRegisteredAndDocumented:
    async def test_it_appears_in_the_generated_openapi(
        self, client: AsyncClient
    ) -> None:
        """The API is documented by generation, never by hand (§7)."""
        schema = (await client.get("/openapi.json")).json()
        path = schema["paths"]["/workspaces/{workspace_id}/accounts"]["get"]

        assert path["summary"] == "Accounts worth attention, most pressing first"
        assert "which accounts should i work on today" in path["description"].lower()

    async def test_every_response_field_is_documented(
        self, client: AsyncClient
    ) -> None:
        """A field a customer cannot interpret is a field that should not be on
        the row. Asserted against the generated schema, so a new field without
        a description fails here rather than reaching a client."""
        schema = (await client.get("/openapi.json")).json()
        row = schema["components"]["schemas"]["AccountAttentionResponse"]["properties"]

        undocumented = sorted(name for name, spec in row.items() if not spec.get("description"))

        assert undocumented == [], f"{undocumented} reach the wire with no description"


class TestARealAccountReachesTheWire:
    """**The M12.1 demonstration.** A simulated provider payload traverses the
    whole pipeline and comes back as a row a salesperson can act on.

    Seeded through the same helper M8, M9 and M10 use, so the list is asserted
    against what the pipeline actually produces rather than against a fixture
    written to match it.
    """

    async def test_the_list_is_ordered_by_attention(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Scores descending, and accounts with no live score last — the order
        a seller reads top-down."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        rows = (await _accounts(client, key_pair, user_id, workspace_id)).json()["items"]

        ranked = [(r["score"] if r["score"] is not None else -1) for r in rows]
        assert ranked == sorted(ranked, reverse=True)

    async def test_a_qualified_account_appears_with_its_reason_to_exist(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        response = await _accounts(client, key_pair, user_id, workspace_id)

        assert response.status_code == 200, response.text
        rows = response.json()["items"]
        (row,) = [r for r in rows if UUID(r["account_id"]) == entity_id]
        assert 0 <= row["score"] <= 100
        assert row["trigger"], "a row with no reason to exist is a row nobody can act on"
        assert row["evidence"] in {"current", "cooling", "stale"}
        assert row["stage"]

    async def test_two_workspaces_never_see_each_other(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Tenant isolation over the real request path**, not asserted at the
        repository. RLS is the authoritative control and this is what proves it
        reaches the customer."""
        first_workspace, first_user, first_entity, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        second_workspace, second_user, second_entity, _ = await _tracked(
            session_factory, admin_session_factory, "contoso"
        )

        mine = (await _accounts(client, key_pair, first_user, first_workspace)).json()
        theirs = (await _accounts(client, key_pair, second_user, second_workspace)).json()

        ours = {UUID(r["account_id"]) for r in mine["items"]}
        others = {UUID(r["account_id"]) for r in theirs["items"]}

        assert first_entity in ours
        assert second_entity in others
        assert ours.isdisjoint(others), "one workspace's accounts appeared in another's list"

    async def test_a_member_of_one_workspace_cannot_read_the_other(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        first_workspace, first_user, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        second_workspace, _, _, _ = await _tracked(
            session_factory, admin_session_factory, "contoso"
        )

        response = await _accounts(client, key_pair, first_user, second_workspace)

        assert response.status_code == 404

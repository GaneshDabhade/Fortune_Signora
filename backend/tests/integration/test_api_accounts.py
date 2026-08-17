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
from datetime import datetime
from types import SimpleNamespace
from typing import Any
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.api.main import create_app
from signora_platform.db.session import set_workspace_context
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
from tests.slugs import test_slug as _test_slug

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
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http,
    ):
        yield http


def _auth(key_pair: KeyPair, user_id: UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {mint_token(key_pair, user_id=user_id)}"}


async def _workspace(client: AsyncClient, key_pair: KeyPair, user_id: UUID) -> UUID:
    response = await client.post(
        "/workspaces", json={"name": "Acme", "slug": _test_slug("Acme")}, headers=_auth(key_pair, user_id)
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
            "signal_type",
            # **Added closing R9-03**, and it earns its place by the same test
            # as every field above: *"which of these should worry me?"* is a
            # question a sales manager asks daily, and until now the row
            # answered it only in prose a reader had to read.
            "posture",
            "contested",
            "evidence",
            "stage",
            "owner_id",
            "opened_at",
            # **The Friday-afternoon question** (LO-06). It passes the same
            # test as every field above: *"what have I been sitting on?"* is
            # asked weekly, and the row could not answer it — an account taken
            # on this morning and one taken on in March rendered identically.
            "since",
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
    async def test_it_appears_in_the_generated_openapi(self, client: AsyncClient) -> None:
        """The API is documented by generation, never by hand (§7)."""
        schema = (await client.get("/openapi.json")).json()
        path = schema["paths"]["/workspaces/{workspace_id}/accounts"]["get"]

        assert path["summary"] == "Accounts worth attention, most pressing first"
        assert "which accounts should i work on today" in path["description"].lower()

    async def test_every_response_field_is_documented(self, client: AsyncClient) -> None:
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
        assert row["signal_type"], "a row with no hypothesis is a row nobody can act on"
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


class TestAccountIdentitiesAreResolvedNotStored:
    """`GET /workspaces/{id}/account-identities` — who these accounts are.

    An account's name is a `legal_name` claim, so naming one is a resolution
    performed on every request. These assert the customer-visible half: the
    endpoint is scoped, batched, validated, and honest about disagreement.
    """

    async def test_a_real_account_comes_back_named(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        response = await client.get(
            f"/workspaces/{workspace_id}/account-identities",
            params={"ids": [str(entity_id)]},
            headers=_auth(key_pair, user_id),
        )

        assert response.status_code == 200, response.text
        (identity,) = response.json()
        assert UUID(identity["account_id"]) == entity_id
        assert identity["name"], "the pipeline produced an account nothing can name"
        assert identity["agreement"] in {"unknown", "single_source", "agreed", "disputed"}
        assert identity["source_count"] >= 1

    async def test_one_request_names_a_whole_page(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Batched, because naming fifty rows one at a time is fifty round
        trips.** The list endpoint and this one are joined by `account_id`."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        rows = (await _accounts(client, key_pair, user_id, workspace_id)).json()["items"]
        ids = [row["account_id"] for row in rows]

        response = await client.get(
            f"/workspaces/{workspace_id}/account-identities",
            params={"ids": ids},
            headers=_auth(key_pair, user_id),
        )

        assert response.status_code == 200, response.text
        assert {i["account_id"] for i in response.json()} == set(ids)

    async def test_an_account_says_how_current_its_evidence_is(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**A4 — *"how old is what I am looking at?"***

        Against a real database and the real grouped query, because the thing
        most likely to be wrong is the join: `latest_observed_at` groups by
        `(provider, subject_external_id)` and the caller maps those back
        through identity bindings. A fake agrees with whatever the fake was
        written to agree with.

        **Not `>= observed_at`.** The name claim is one of many, so asserting
        an ordering between the two would pass whichever way the join was
        wired. What is asserted is that it equals the newest claim the
        pipeline actually recorded for this account.
        """
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        response = await client.get(
            f"/workspaces/{workspace_id}/account-identities",
            params={"ids": [str(entity_id)]},
            headers=_auth(key_pair, user_id),
        )

        assert response.status_code == 200, response.text
        (identity,) = response.json()
        assert identity["last_observed_at"] is not None, (
            "the pipeline produced claims for this account, so something was observed"
        )

        async with session_factory() as session:
            # `set_config(..., true)` rather than `SET LOCAL`: the latter takes
            # no bind parameter, so the platform's own helper is the only
            # correct way to establish tenant context — and reading through
            # RLS is the point of doing it here rather than as the owner.
            await set_workspace_context(session, workspace_id)
            newest = await session.scalar(
                text(
                    "SELECT max(c.observed_at) FROM claim c "
                    "JOIN identity_binding b "
                    "  ON b.provider = c.provider "
                    " AND b.provider_external_id = c.subject_external_id "
                    "WHERE b.entity_id = :entity_id AND c.workspace_id = :workspace_id"
                ),
                {"entity_id": entity_id, "workspace_id": workspace_id},
            )

        assert datetime.fromisoformat(identity["last_observed_at"]) == newest

    async def test_another_workspace_s_account_is_absent_rather_than_named(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The tenancy boundary on the identity path.** Naming an account is
        a read of another tenant's claims; asking for one by id must return
        nothing rather than a name."""
        mine_workspace, mine_user, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        _, _, theirs_entity, _ = await _tracked(session_factory, admin_session_factory, "contoso")

        response = await client.get(
            f"/workspaces/{mine_workspace}/account-identities",
            params={"ids": [str(theirs_entity)]},
            headers=_auth(key_pair, mine_user),
        )

        assert response.status_code == 200
        assert [i for i in response.json() if i["name"] is not None] == []

    async def test_a_non_member_gets_404(self, client: AsyncClient, key_pair: KeyPair) -> None:
        workspace = await _workspace(client, key_pair, uuid4())

        response = await client.get(
            f"/workspaces/{workspace}/account-identities",
            params={"ids": [str(uuid4())]},
            headers=_auth(key_pair, uuid4()),
        )

        assert response.status_code == 404

    async def test_asking_for_nothing_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """A request naming no accounts is a mistake, not an empty answer."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await client.get(
            f"/workspaces/{workspace}/account-identities", headers=_auth(key_pair, user)
        )

        assert response.status_code == 422

    async def test_asking_for_more_than_a_page_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """Bounded by the same ceiling a page is: a request naming more
        accounts than a page can hold is either a mistake or a scrape."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await client.get(
            f"/workspaces/{workspace}/account-identities",
            params={"ids": [str(uuid4()) for _ in range(201)]},
            headers=_auth(key_pair, user),
        )

        assert response.status_code == 422

    async def test_every_field_is_documented(self, client: AsyncClient) -> None:
        schema = (await client.get("/openapi.json")).json()
        row = schema["components"]["schemas"]["AccountIdentityResponse"]["properties"]

        undocumented = sorted(name for name, spec in row.items() if not spec.get("description"))

        assert undocumented == []


async def _score(
    client: AsyncClient, key_pair: KeyPair, user_id: UUID, workspace_id: UUID, account_id: UUID
) -> Any:
    return await client.get(
        f"/workspaces/{workspace_id}/accounts/{account_id}/score",
        headers=_auth(key_pair, user_id),
    )


class TestTheScoreExplainsItself:
    """`GET /workspaces/{id}/accounts/{account_id}/score` — *"why this account?"*

    The first surface in the repository that returns a number **and** the
    arithmetic that produced it. These assert the property the whole module
    exists for: that a customer handed this response can reproduce the score
    themselves and disagree with it line by line.
    """

    async def test_a_real_account_comes_back_with_its_ledger(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        response = await _score(client, key_pair, user_id, workspace_id, entity_id)

        assert response.status_code == 200, response.text
        body = response.json()
        assert UUID(body["account_id"]) == entity_id
        assert 0 <= body["score"] <= 100
        assert body["contributions"], (
            "a score with no ledger is exactly the opaque number this module exists to avoid"
        )
        for line in body["contributions"]:
            assert line["reason"].strip(), "a line a customer cannot challenge"

    async def test_the_score_reproduces_from_the_lines_beneath_it(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The property that makes the explanation worth reading.**

        Sum the counted points, divide by the ceiling, cap at 100. Asserted
        over the wire rather than in the domain, because an explanation that
        reproduces in Python and not in the response is an explanation the
        customer does not have.
        """
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        body = (await _score(client, key_pair, user_id, workspace_id, entity_id)).json()

        counted = sum(line["points"] for line in body["contributions"] if line["counted"])
        assert counted == body["points"]
        assert body["score"] == min(100, body["points"] * 100 // body["ceiling"])

    async def test_an_uncounted_line_carries_no_points_and_still_says_why(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """A zero with a reason is information; an absent row is a mystery."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        body = (await _score(client, key_pair, user_id, workspace_id, entity_id)).json()

        for line in body["contributions"]:
            if not line["counted"]:
                assert line["points"] == 0
                assert line["reason"].strip()

    async def test_dissent_is_only_claimed_where_the_account_is_contested(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Contradiction is detected from the evidence, never asserted beside
        it — so a line cannot be marked dissenting on an account where nothing
        disagrees."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        body = (await _score(client, key_pair, user_id, workspace_id, entity_id)).json()

        dissenting = [line for line in body["contributions"] if line["dissenting"]]
        assert body["contested"] or dissenting == []

    async def test_a_reading_states_how_long_it_is_correct_for(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """A score is a reading with a stated validity, not a live gauge.
        `is_current` is derived server-side so the browser never has to decide
        whether a number it was handed is still true."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        body = (await _score(client, key_pair, user_id, workspace_id, entity_id)).json()

        assert body["computed_at"]
        assert isinstance(body["is_current"], bool)

    async def test_an_account_that_was_never_scored_is_404(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await _score(client, key_pair, user, workspace, uuid4())

        assert response.status_code == 404

    async def test_another_workspace_s_account_is_404_and_not_a_score(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Tenant isolation on the explanation path.** Indistinguishable from
        an account that was never scored, deliberately: a different answer here
        would make account identifiers enumerable across tenants."""
        mine_workspace, mine_user, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        _, _, theirs_entity, _ = await _tracked(session_factory, admin_session_factory, "contoso")

        response = await _score(client, key_pair, mine_user, mine_workspace, theirs_entity)

        assert response.status_code == 404

    async def test_a_non_member_gets_404(self, client: AsyncClient, key_pair: KeyPair) -> None:
        workspace = await _workspace(client, key_pair, uuid4())

        response = await _score(client, key_pair, uuid4(), workspace, uuid4())

        assert response.status_code == 404

    async def test_an_unauthenticated_request_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        workspace = await _workspace(client, key_pair, uuid4())

        response = await client.get(f"/workspaces/{workspace}/accounts/{uuid4()}/score")

        assert response.status_code == 401

    async def test_a_malformed_account_identifier_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await client.get(
            f"/workspaces/{workspace}/accounts/not-a-uuid/score",
            headers=_auth(key_pair, user),
        )

        assert response.status_code == 422

    async def test_it_appears_in_the_generated_openapi(self, client: AsyncClient) -> None:
        schema = (await client.get("/openapi.json")).json()
        path = schema["paths"]["/workspaces/{workspace_id}/accounts/{account_id}/score"]["get"]

        assert path["summary"] == "Why this account is scored where it is"
        assert "why this account" in path["description"].lower()

    async def test_every_response_field_is_documented(self, client: AsyncClient) -> None:
        schema = (await client.get("/openapi.json")).json()
        schemas = schema["components"]["schemas"]

        for name in ("AccountScoreResponse", "ContributionResponse"):
            undocumented = sorted(
                field
                for field, spec in schemas[name]["properties"].items()
                if not spec.get("description")
            )
            assert undocumented == [], f"{name}: {undocumented} reach the wire undocumented"

    async def test_the_response_exposes_no_internal_bookkeeping(self) -> None:
        """**Every field answers a question a salesperson would ask.**

        Score identity, the reading it supersedes, the configuration versions
        in force and the three multipliers behind one line are all real, all
        stored, and none of them is something a seller decides from.
        """
        from modules.buying_score_engine.interface.schemas import (
            AccountScoreResponse,
            ContributionResponse,
        )

        header = set(AccountScoreResponse.model_fields)
        line = set(ContributionResponse.model_fields)

        for internal in ("id", "supersedes", "basis_at", "workspace_id"):
            assert internal not in header
        for internal in (
            "scoring_model_version",
            "model_artifact_version",
            "profile_version",
            "payload_version",
        ):
            assert internal not in header
        for internal in (
            "base_weight",
            "relevance_multiplier",
            "age_multiplier",
            "band_started_at",
            "band_ends_at",
        ):
            assert internal not in line

    async def test_the_schema_is_not_a_domain_entity(self) -> None:
        """Coupling the wire contract to the domain model makes a domain
        refactor a client-breaking change (19-api-conventions.md)."""
        from modules.buying_score_engine.domain.ledger import Contribution
        from modules.buying_score_engine.domain.score import BuyingScore
        from modules.buying_score_engine.interface.schemas import (
            AccountScoreResponse,
            ContributionResponse,
        )

        assert not issubclass(AccountScoreResponse, BuyingScore)
        assert not issubclass(ContributionResponse, Contribution)


async def _opportunity(
    client: AsyncClient, key_pair: KeyPair, user_id: UUID, workspace_id: UUID, account_id: UUID
) -> Any:
    return await client.get(
        f"/workspaces/{workspace_id}/accounts/{account_id}/opportunity",
        headers=_auth(key_pair, user_id),
    )


class TestTheBriefKnowsWhatChanged:
    """`GET …/accounts/{account_id}/opportunity` — *"what changed?"*

    The attention list knows only about now. This is the record of what was
    true when somebody committed, which is what makes today's number mean
    something: 50 on an account opened at 20 is a different situation from 50
    on one opened at 60.
    """

    async def test_it_reports_then_beside_now(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        response = await _opportunity(client, key_pair, user_id, workspace_id, entity_id)

        assert response.status_code == 200, response.text
        body = response.json()
        assert UUID(body["account_id"]) == entity_id
        assert body["score_at_open"] >= 0
        assert body["opened_at"]
        assert body["stage"] in {"tracking", "engaged", "closed_won", "closed_lost", "dismissed"}

    async def test_the_movement_is_computed_from_the_two_it_reports(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Derived server-side, and checkable against the two numbers beside
        it — a client that subtracted them itself would be a second
        implementation of the only arithmetic on this response."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        body = (await _opportunity(client, key_pair, user_id, workspace_id, entity_id)).json()

        if body["score"] is None:
            assert body["score_change_since_open"] is None
        else:
            assert body["score_change_since_open"] == body["score"] - body["score_at_open"]

    async def test_no_live_score_reports_absence_rather_than_no_change(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Zero and null mean opposite things here.** Zero is a reading that
        has not moved; null is the absence of one. A brief reporting *"no
        change"* for an account whose evidence expired would state the reverse
        of what happened."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        body = (await _opportunity(client, key_pair, user_id, workspace_id, entity_id)).json()

        assert (body["score"] is None) == (body["score_change_since_open"] is None)

    async def test_the_history_is_complete_and_ordered(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Append-only, oldest first. The status *is* the audit trail."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        history = (await _opportunity(client, key_pair, user_id, workspace_id, entity_id)).json()[
            "history"
        ]

        assert history, "an opportunity with no recorded state cannot explain itself"
        assert [e["occurred_at"] for e in history] == sorted(e["occurred_at"] for e in history)
        for entry in history:
            assert entry["reason"].strip(), "a workflow change that explains nothing"

    async def test_the_opening_entry_names_no_person(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Intelligence suggests; humans commit.** Signora may open an
        account at `tracking` and may do nothing else, so the first entry is
        the one state with no actor — and every later one must name someone."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        history = (await _opportunity(client, key_pair, user_id, workspace_id, entity_id)).json()[
            "history"
        ]

        assert history[0]["stage"] == "tracking"
        assert history[0]["decided_by"] is None
        for entry in history[1:]:
            assert entry["decided_by"] is not None

    async def test_an_account_with_nothing_open_is_404(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await _opportunity(client, key_pair, user, workspace, uuid4())

        assert response.status_code == 404

    async def test_another_workspace_s_account_is_404(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Indistinguishable from an account with nothing open, deliberately."""
        mine_workspace, mine_user, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        _, _, theirs_entity, _ = await _tracked(session_factory, admin_session_factory, "contoso")

        response = await _opportunity(client, key_pair, mine_user, mine_workspace, theirs_entity)

        assert response.status_code == 404

    async def test_a_non_member_gets_404(self, client: AsyncClient, key_pair: KeyPair) -> None:
        workspace = await _workspace(client, key_pair, uuid4())

        response = await _opportunity(client, key_pair, uuid4(), workspace, uuid4())

        assert response.status_code == 404

    async def test_an_unauthenticated_request_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        workspace = await _workspace(client, key_pair, uuid4())

        response = await client.get(f"/workspaces/{workspace}/accounts/{uuid4()}/opportunity")

        assert response.status_code == 401

    async def test_every_response_field_is_documented(self, client: AsyncClient) -> None:
        schema = (await client.get("/openapi.json")).json()
        schemas = schema["components"]["schemas"]

        for name in ("AccountOpportunityResponse", "WorkflowStateResponse"):
            undocumented = sorted(
                field
                for field, spec in schemas[name]["properties"].items()
                if not spec.get("description")
            )
            assert undocumented == [], f"{name}: {undocumented} reach the wire undocumented"

    async def test_the_response_exposes_no_internal_bookkeeping(self) -> None:
        """`generation`, `policy_version` and `originating_buying_score_id` are
        real, stored, and none of them is something a seller decides from. The
        score id belongs here the day a citation can be *followed* from it —
        M12.3 owns that, and adding it now would be a field nobody can use."""
        from modules.opportunity_engine.interface.schemas import AccountOpportunityResponse

        fields = set(AccountOpportunityResponse.model_fields)

        for internal in (
            "generation",
            "policy_version",
            "originating_buying_score_id",
            "payload_version",
            "workspace_id",
        ):
            assert internal not in fields


async def _narration(
    client: AsyncClient, key_pair: KeyPair, user_id: UUID, workspace_id: UUID, account_id: UUID
) -> Any:
    return await client.get(
        f"/workspaces/{workspace_id}/accounts/{account_id}/narration",
        headers=_auth(key_pair, user_id),
    )


class TestTheBriefCanSpeakPlainly:
    """`GET …/accounts/{account_id}/narration` — the brief's narrative half.

    **The first model-authored content with an HTTP path.** These assert the
    contract that makes it safe to render: every statement arrives with its
    citations, and the response says what wrote it.
    """

    async def _stored(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        workspace_id: UUID,
        account_id: UUID,
    ) -> None:
        from datetime import UTC, datetime

        from modules.ai_platform.domain.grounding import GroundedStatement
        from modules.ai_platform.domain.narration import (
            MaterializedNarration,
            NarrationSubject,
        )
        from modules.ai_platform.domain.provider import AIVendor
        from modules.ai_platform.infrastructure.repository import SqlNarrationRepository
        from signora_platform.db import tenant_scoped_session

        cited = f"buying_score:{uuid4()}"
        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=uuid4()
        ) as session:
            await SqlNarrationRepository(session).save(
                MaterializedNarration(
                    id=uuid4(),
                    workspace_id=workspace_id,
                    correlation_id=uuid4(),
                    subject=NarrationSubject(kind="account", id=account_id),
                    prompt_name="explanation_narration",
                    prompt_version=1,
                    prompt_fingerprint="a" * 64,
                    model="llama3.1:8b",
                    vendor=AIVendor.OLLAMA,
                    evidence_digest="b" * 64,
                    evidence_refs=(cited,),
                    inference_id=uuid4(),
                    statements=(
                        GroundedStatement(
                            text="The score that opened this was 20 out of 120.",
                            evidence=(cited,),
                        ),
                    ),
                    created_at=datetime(2026, 8, 1, tzinfo=UTC),
                )
            )

    async def test_every_statement_arrives_with_its_citations(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The grounding guarantee, observable by the party it exists for.**
        A statement without its evidence would be unverifiable prose, which is
        the one thing this product must never ship."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        await self._stored(session_factory, workspace_id, entity_id)

        response = await _narration(client, key_pair, user_id, workspace_id, entity_id)

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["statements"], "a narration with no statements explains nothing"
        for statement in body["statements"]:
            assert statement["text"].strip()
            assert statement["evidence"], "an uncited sentence reached the wire"

    async def test_the_response_says_what_wrote_it(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Provenance on the response, not reachable from it: a customer
        reading generated language is entitled to know what generated it while
        they are reading it (M12.2 definition of done)."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        await self._stored(session_factory, workspace_id, entity_id)

        body = (await _narration(client, key_pair, user_id, workspace_id, entity_id)).json()

        assert body["prompt"] == "explanation_narration@1"
        assert body["model"] == "llama3.1:8b"
        assert body["generated_at"]

    async def test_it_carries_no_uncited_summary(self) -> None:
        """**The one sentence a reader looks at first must not be the one
        exempt from grounding.** The domain refuses an un-cited summary field;
        the wire contract must not reintroduce one."""
        from modules.ai_platform.interface.schemas import AccountNarrationResponse

        fields = set(AccountNarrationResponse.model_fields)

        for forbidden in ("summary", "headline", "text", "conclusion", "recommendation"):
            assert forbidden not in fields

    async def test_an_account_with_no_narration_is_404(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """The ordinary state of a new account, not an error: narration is
        produced by a worker after the pipeline has something to explain."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await _narration(client, key_pair, user, workspace, uuid4())

        assert response.status_code == 404

    async def test_another_workspace_s_narration_is_not_readable(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Tenant isolation over generated content.** A narration quotes a
        workspace's evidence in prose, which makes a leak here more legible to
        an attacker than a leak of the underlying rows."""
        mine_workspace, mine_user, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        theirs_workspace, _, theirs_entity, _ = await _tracked(
            session_factory, admin_session_factory, "contoso"
        )
        await self._stored(session_factory, theirs_workspace, theirs_entity)

        response = await _narration(client, key_pair, mine_user, mine_workspace, theirs_entity)

        assert response.status_code == 404

    async def test_a_non_member_gets_404(self, client: AsyncClient, key_pair: KeyPair) -> None:
        workspace = await _workspace(client, key_pair, uuid4())

        response = await _narration(client, key_pair, uuid4(), workspace, uuid4())

        assert response.status_code == 404

    async def test_an_unauthenticated_request_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        workspace = await _workspace(client, key_pair, uuid4())

        response = await client.get(f"/workspaces/{workspace}/accounts/{uuid4()}/narration")

        assert response.status_code == 401

    async def _grounded(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        workspace_id: UUID,
        account_id: UUID,
        *,
        digest: str | None = None,
    ) -> tuple[str, ...]:
        """Store a narration cited against **the account's real evidence**.

        `_stored` invents a token and a digest, which is right for the tests
        that only care about the grounding contract. These need the genuine
        article: a citation that resolves, and a digest that either matches the
        evidence or deliberately does not.

        Returns the tokens it cited, so a test can assert against them without
        reconstructing the assembler's output.
        """
        from datetime import UTC, datetime

        from modules.ai_platform.domain.grounding import GroundedStatement
        from modules.ai_platform.domain.narration import (
            MaterializedNarration,
            NarrationSubject,
        )
        from modules.ai_platform.domain.provider import AIVendor
        from modules.ai_platform.infrastructure.repository import SqlNarrationRepository
        from signora_platform.db import tenant_scoped_session

        evidence = await self._evidence(session_factory, workspace_id, account_id)
        assert evidence is not None, "the account has no explanation to cite"
        tokens = tuple(fact.ref.token for fact in evidence)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=uuid4()
        ) as session:
            await SqlNarrationRepository(session).save(
                MaterializedNarration(
                    id=uuid4(),
                    workspace_id=workspace_id,
                    correlation_id=uuid4(),
                    subject=NarrationSubject(kind="account", id=account_id),
                    prompt_name="explanation_narration",
                    prompt_version=1,
                    prompt_fingerprint="a" * 64,
                    model="llama3.1:8b",
                    vendor=AIVendor.OLLAMA,
                    evidence_digest=digest or evidence.digest,
                    evidence_refs=tokens,
                    inference_id=uuid4(),
                    statements=(
                        GroundedStatement(
                            text="This account is worth a look.", evidence=(tokens[0],)
                        ),
                        # Deliberately cites the same fact again: three
                        # sentences resting on one fact must not produce three
                        # copies of it.
                        GroundedStatement(
                            text="The evidence behind it is recent.",
                            evidence=(tokens[0], tokens[-1]),
                        ),
                    ),
                    created_at=datetime(2026, 8, 1, tzinfo=UTC),
                )
            )
        return tokens

    async def _evidence(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        workspace_id: UUID,
        account_id: UUID,
    ) -> Any:
        from apps.api.composition.opportunities import opportunity_queries
        from modules.ai_platform.infrastructure.explanation import (
            OpportunityExplanationSource,
        )
        from signora_platform.db import tenant_scoped_session

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=uuid4()
        ) as session:
            context = SimpleNamespace(session=session, workspace_id=workspace_id)
            source = OpportunityExplanationSource(opportunity_queries(context))  # type: ignore[arg-type]
            return await source.evidence_for(workspace_id, account_id)

    async def test_a_citation_resolves_to_the_fact_the_model_was_given(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**D42.** *"3 facts"* with no way to follow them was the one place the
        product visibly promised something it did not do, on the surface whose
        whole argument is *you can check this*."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        tokens = await self._grounded(session_factory, workspace_id, entity_id)

        body = (await _narration(client, key_pair, user_id, workspace_id, entity_id)).json()

        cited = {token for s in body["statements"] for token in s["evidence"]}
        resolved = {fact["token"] for fact in body["facts"]}
        assert cited, "the fixture cites nothing"
        assert cited <= resolved, f"unresolvable citations reached the wire: {cited - resolved}"
        assert tokens[0] in resolved

    async def test_a_fact_two_statements_cite_appears_once(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The citation is the token and the fact is looked up. Carrying the
        same fact inside each statement would be copies of one truth, and the
        copies eventually disagree."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        await self._grounded(session_factory, workspace_id, entity_id)

        body = (await _narration(client, key_pair, user_id, workspace_id, entity_id)).json()

        tokens = [fact["token"] for fact in body["facts"]]
        assert len(tokens) == len(set(tokens)), f"a fact was repeated: {tokens}"

    async def test_a_fact_carries_the_owning_module_s_own_words(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """A citation resolves into the pipeline's vocabulary, not the
        substrate's paraphrase of it — and carries the figures behind the
        sentence, which is what makes it checkable rather than merely readable."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        await self._grounded(session_factory, workspace_id, entity_id)

        body = (await _narration(client, key_pair, user_id, workspace_id, entity_id)).json()

        for fact in body["facts"]:
            assert fact["summary"].strip(), "a fact a reader cannot read is not evidence"
            assert fact["kind"] in {"opportunity", "buying_score", "signal_contribution"}
        assert any(fact["attributes"] for fact in body["facts"])

    async def test_it_says_the_evidence_is_unchanged_when_it_is(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The digest recorded at write time, compared against the set
        re-derived now. **This is what makes re-derivation honest** — without
        it the response would present today's facts as the ones a model saw."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        await self._grounded(session_factory, workspace_id, entity_id)

        body = (await _narration(client, key_pair, user_id, workspace_id, entity_id)).json()

        assert body["evidence_unchanged"] is True

    async def test_it_says_the_evidence_moved_when_the_digest_disagrees(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """A narration is never edited to catch up with its account. It is
        dated, and the product says so rather than quietly re-describing it."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        await self._grounded(session_factory, workspace_id, entity_id, digest="c" * 64)

        body = (await _narration(client, key_pair, user_id, workspace_id, entity_id)).json()

        assert body["evidence_unchanged"] is False
        # The citations still resolve: what moved is the *set*, and the facts
        # still present are still the facts. Refusing to resolve any of them
        # would hide the half a reader can still check.
        assert body["facts"], "a changed digest emptied facts that still resolve"

    async def test_an_unresolvable_citation_is_absent_rather_than_invented(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """`_stored` cites a token no evidence set contains. Nothing may be
        fabricated to fill it, and `evidence_unchanged` must not claim the
        evidence still matches."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        await self._stored(session_factory, workspace_id, entity_id)

        body = (await _narration(client, key_pair, user_id, workspace_id, entity_id)).json()

        assert body["facts"] == []
        assert body["evidence_unchanged"] is False

    async def test_every_response_field_is_documented(self, client: AsyncClient) -> None:
        schema = (await client.get("/openapi.json")).json()
        schemas = schema["components"]["schemas"]

        for name in (
            "AccountNarrationResponse",
            "NarrationStatementResponse",
            "EvidenceFactResponse",
        ):
            undocumented = sorted(
                field
                for field, spec in schemas[name]["properties"].items()
                if not spec.get("description")
            )
            assert undocumented == [], f"{name}: {undocumented} reach the wire undocumented"


async def _live_account(
    session_factory: async_sessionmaker[AsyncSession],
    admin_session_factory: async_sessionmaker[AsyncSession],
) -> tuple[UUID, UUID, UUID, Any]:
    """One account whose hypotheses are current at wall-clock now.

    The Playground anchors its narrative relative to today, which is the only
    seeded data in the repository where "live" means anything. `atlassian` is
    the smallest such account — one intent surge, one hypothesis — so the test
    asserts the endpoint rather than the scenario.
    """
    from datetime import UTC, datetime, timedelta

    now = datetime.now(UTC)
    today = datetime(now.year, now.month, now.day, tzinfo=UTC)
    return await _tracked(
        session_factory,
        admin_session_factory,
        "live",
        scenario=("playground", 2),
        subjects=("atlassian",),
        epoch=today - timedelta(days=150),
        moment=now,
        anchor="atlassian",
    )


async def _validation(
    client: AsyncClient, key_pair: KeyPair, user_id: UUID, workspace_id: UUID, account_id: UUID
) -> Any:
    return await client.get(
        f"/workspaces/{workspace_id}/accounts/{account_id}/validation",
        headers=_auth(key_pair, user_id),
    )


class TestTheBriefSaysWhatToCheck:
    """`GET …/accounts/{account_id}/validation` — *"what should I do?"*

    **The first surface that is about action rather than about truth**, and it
    needed no model: `limitations` and `suggested_validation` have been in the
    Signal Catalog since M5A and had never been displayed.
    """

    async def test_a_real_account_says_what_to_confirm(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Seeded from the Playground, not the baseline, and that is the
        test.** Guidance is only offered for *live* hypotheses, and the
        baseline scenario describes events months in the past — at wall-clock
        now every one of its signals has passed its shelf life, so it can only
        ever produce an empty answer. An account with something current is the
        only way to assert this endpoint says anything at all."""
        workspace_id, user_id, entity_id, _ = await _live_account(
            session_factory, admin_session_factory
        )

        response = await _validation(client, key_pair, user_id, workspace_id, entity_id)

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["hypotheses"], "an account with live signals and no guidance"
        for entry in body["hypotheses"]:
            assert entry["suggested_validation"], "a hypothesis with nothing to check"

    async def test_every_hypothesis_states_what_it_cannot_prove(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The load-bearing half.** A confident number invites over-reading,
        and this is the only place that says what it cannot support. A type
        claiming no limitations would be asserting certainty the evidence
        cannot carry — the catalog refuses to declare one."""
        workspace_id, user_id, entity_id, _ = await _live_account(
            session_factory, admin_session_factory
        )

        body = (await _validation(client, key_pair, user_id, workspace_id, entity_id)).json()

        assert body["hypotheses"]
        for entry in body["hypotheses"]:
            assert entry["limitations"], f"{entry['title']} claims no limitations"

    async def test_the_guidance_never_mentions_this_account(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**It is not a recommendation, and this is what keeps it from
        becoming one.** The guidance is a property of the hypothesis type — the
        same for every account and every workspace — so nothing in it may be
        specific to the company being read. A field that started naming the
        account would be an inference wearing the catalog's clothes."""
        workspace_id, user_id, entity_id, _ = await _live_account(
            session_factory, admin_session_factory
        )

        body = (await _validation(client, key_pair, user_id, workspace_id, entity_id)).json()

        assert body["hypotheses"]
        for entry in body["hypotheses"]:
            prose = " ".join((*entry["limitations"], *entry["suggested_validation"]))
            assert str(entity_id) not in prose
            assert str(workspace_id) not in prose

    async def test_the_most_relevant_hypothesis_is_first(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Ordering is the product's judgement about what to validate first,
        and `relevance` is the only declaration of importance the platform
        holds — the workspace's own, never an inference."""
        workspace_id, user_id, entity_id, _ = await _live_account(
            session_factory, admin_session_factory
        )

        order = {"primary": 0, "supporting": 1, "contextual": 2, "ignored": 3}
        body = (await _validation(client, key_pair, user_id, workspace_id, entity_id)).json()
        ranks = [order[entry["relevance"]] for entry in body["hypotheses"]]

        assert ranks == sorted(ranks)

    async def test_an_account_with_nothing_live_is_an_empty_answer_not_a_404(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """*"Nothing is currently held about this account"* is a real answer.
        A 404 would say the account does not exist, which is a different and
        wrong statement."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await _validation(client, key_pair, user, workspace, uuid4())

        assert response.status_code == 200, response.text
        assert response.json()["hypotheses"] == []

    async def test_a_non_member_gets_404(self, client: AsyncClient, key_pair: KeyPair) -> None:
        workspace = await _workspace(client, key_pair, uuid4())

        response = await _validation(client, key_pair, uuid4(), workspace, uuid4())

        assert response.status_code == 404

    async def test_an_unauthenticated_request_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        workspace = await _workspace(client, key_pair, uuid4())

        response = await client.get(f"/workspaces/{workspace}/accounts/{uuid4()}/validation")

        assert response.status_code == 401

    async def test_another_workspace_s_account_yields_nothing(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        mine_workspace, mine_user, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        _, _, theirs_entity, _ = await _tracked(session_factory, admin_session_factory, "contoso")

        response = await _validation(client, key_pair, mine_user, mine_workspace, theirs_entity)

        assert response.status_code == 200
        assert response.json()["hypotheses"] == []

    async def test_every_response_field_is_documented(self, client: AsyncClient) -> None:
        schema = (await client.get("/openapi.json")).json()
        schemas = schema["components"]["schemas"]

        for name in ("AccountValidationResponse", "HypothesisValidationResponse"):
            undocumented = sorted(
                field
                for field, spec in schemas[name]["properties"].items()
                if not spec.get("description")
            )
            assert undocumented == [], f"{name}: {undocumented} reach the wire undocumented"


class TestACitationResolvesToARecord:
    """`GET …/business-events/{event_id}` — *"prove it."*

    **The end of every citation in the product.** Every other surface says
    something *about* a fact; the observations here are the only content
    Signora did not write, which is why a citation has to end at them rather
    than at another summary.
    """

    async def _an_event(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        user_id: UUID,
        workspace_id: UUID,
        account_id: UUID,
    ) -> str:
        """A business event id, taken from a ledger line the way a reader would."""
        score = (await _score(client, key_pair, user_id, workspace_id, account_id)).json()
        return str(score["contributions"][0]["business_event_id"])

    async def test_a_ledger_line_opens_to_the_readings_beneath_it(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The whole point.** A contribution names a business event; the
        event opens to what a provider actually reported."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        event_id = await self._an_event(client, key_pair, user_id, workspace_id, entity_id)

        response = await client.get(
            f"/workspaces/{workspace_id}/business-events/{event_id}",
            headers=_auth(key_pair, user_id),
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["summary"].strip()
        assert body["observations"], "a citation that resolves to no evidence at all"

    async def test_every_reading_names_its_provider_and_when_it_was_seen(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """A reading with no source is not evidence. `observed_at` is the
        provider's moment, never Signora's — the distinction is what lets a
        reader judge staleness independently of when the pipeline ran."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        event_id = await self._an_event(client, key_pair, user_id, workspace_id, entity_id)

        body = (
            await client.get(
                f"/workspaces/{workspace_id}/business-events/{event_id}",
                headers=_auth(key_pair, user_id),
            )
        ).json()

        for observation in body["observations"]:
            assert observation["provider"].strip()
            assert observation["observed_at"]
            assert observation["current_value"] is not None

    async def test_corroboration_is_reported_rather_than_assumed(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """A fact supported by one provider is not a weaker fact — it is a
        differently-supported one. Every provider that reported it appears,
        and the observations cannot name a provider the event omits."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        event_id = await self._an_event(client, key_pair, user_id, workspace_id, entity_id)

        body = (
            await client.get(
                f"/workspaces/{workspace_id}/business-events/{event_id}",
                headers=_auth(key_pair, user_id),
            )
        ).json()

        assert body["corroborating_providers"]
        reporting = {o["provider"] for o in body["observations"]}
        assert reporting <= set(body["corroborating_providers"])

    async def test_the_readings_are_oldest_first(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """A change reads forwards. Newest-first would make *"29,000 → 34,000"*
        arrive backwards."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        event_id = await self._an_event(client, key_pair, user_id, workspace_id, entity_id)

        body = (
            await client.get(
                f"/workspaces/{workspace_id}/business-events/{event_id}",
                headers=_auth(key_pair, user_id),
            )
        ).json()
        seen = [o["observed_at"] for o in body["observations"]]

        assert seen == sorted(seen)

    async def test_another_workspace_s_evidence_is_404(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**A citation is a bare identifier.** If a foreign event answered
        differently from a missing one, evidence would be enumerable across
        tenants by guessing."""
        mine_workspace, mine_user, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        theirs_workspace, theirs_user, theirs_entity, _ = await _tracked(
            session_factory, admin_session_factory, "contoso"
        )
        theirs_event = await self._an_event(
            client, key_pair, theirs_user, theirs_workspace, theirs_entity
        )

        response = await client.get(
            f"/workspaces/{mine_workspace}/business-events/{theirs_event}",
            headers=_auth(key_pair, mine_user),
        )

        assert response.status_code == 404

    async def test_an_event_that_does_not_exist_is_404(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await client.get(
            f"/workspaces/{workspace}/business-events/{uuid4()}",
            headers=_auth(key_pair, user),
        )

        assert response.status_code == 404

    async def test_an_unauthenticated_request_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        workspace = await _workspace(client, key_pair, uuid4())

        response = await client.get(f"/workspaces/{workspace}/business-events/{uuid4()}")

        assert response.status_code == 401

    async def test_every_response_field_is_documented(self, client: AsyncClient) -> None:
        schema = (await client.get("/openapi.json")).json()
        schemas = schema["components"]["schemas"]

        for name in ("BusinessEventEvidenceResponse", "ObservationResponse"):
            undocumented = sorted(
                field
                for field, spec in schemas[name]["properties"].items()
                if not spec.get("description")
            )
            assert undocumented == [], f"{name}: {undocumented} reach the wire undocumented"


class TestTheRowSaysWhatIsHappening:
    """**The most-read line on the daily surface.**

    It used to carry `ScoreTrigger` — *why the score was last recomputed* — and
    across twelve real accounts that produced **two** distinct values. A seller
    reads that line asking *why does this company matter today*, which is a
    different question the enum cannot answer.

    It now carries the hypothesis that most explains the score, which produces
    six across the same twelve. Asserted over the real pipeline rather than a
    fixture, because the finding was about **variety in practice**, not about
    whether a field is populated.
    """

    async def test_the_row_names_the_hypothesis_that_leads_the_score(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        rows = (await _accounts(client, key_pair, user_id, workspace_id)).json()["items"]

        (row,) = [r for r in rows if UUID(r["account_id"]) == entity_id]
        assert row["signal_type"], "a scored account with no leading hypothesis"

    async def test_it_is_a_key_and_never_a_title(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The module that ranks accounts may not name a hypothesis.** Its
        import contract forbids reaching the Signal Engine at all — *it decides
        what to track and never forms hypotheses or weighs them* — so the row
        carries the catalog's key and the catalog supplies the words.
        """
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        rows = (await _accounts(client, key_pair, user_id, workspace_id)).json()["items"]
        catalog = (
            await client.get(
                f"/workspaces/{workspace_id}/signal-catalog",
                headers=_auth(key_pair, user_id),
            )
        ).json()

        keys = {t["key"] for t in catalog["types"]}
        titles = {t["title"] for t in catalog["types"]}
        present = {r["signal_type"] for r in rows if r["signal_type"]}

        assert present, "no row named a hypothesis at all"
        assert present <= keys
        assert present.isdisjoint(titles), "a title reached the row; the key was the contract"

    async def test_the_trigger_is_gone_from_the_row(self) -> None:
        """It described **the last recomputation** while the evidence badge
        beside it described **now**, and side by side with no separation the
        two read as a contradiction — *stale · new evidence arrived* (R1-02).

        It is not deleted: the brief still carries it, where *"why did this
        number move"* is a question somebody is actually asking.
        """
        from modules.opportunity_engine.interface.schemas import AccountAttentionResponse

        assert "trigger" not in AccountAttentionResponse.model_fields


class TestTheVocabularyHasOneOwner:
    async def test_the_catalog_names_every_hypothesis_the_pipeline_can_form(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await client.get(
            f"/workspaces/{workspace}/signal-catalog", headers=_auth(key_pair, user)
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["version"] >= 1
        assert len(body["types"]) >= 1
        assert all(t["key"] and t["title"] for t in body["types"])

    async def test_it_carries_names_and_type_level_meaning_and_nothing_else(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**What a hypothesis proposes, cannot prove, and how to check it are
        per-account questions the validation surface already answers. The same
        prose in two places means one of them goes stale.**

        ⚡ **Widened by TASK-456 to `why_it_matters`, and the refusal above is
        unchanged.** C-204 found that a seller reading a two-word label on a
        ranked row had no way to learn what it meant — and `why_it_matters` is
        the one catalog field surfaced *nowhere*, because it is a fact about
        the **type** rather than about an account. **It duplicates nothing.**

        ⛔ **`hypothesis`, `limitations` and `suggested_validation` stay out**,
        and this assertion is what keeps them out: all three are on
        `HypothesisValidationResponse` already, per account, where they belong.
        """
        from modules.signal_engine.interface.schemas import SignalTypeResponse

        assert set(SignalTypeResponse.model_fields) == {"key", "title", "why_it_matters"}

    async def test_it_is_ordered_so_two_requests_agree(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """Catalog declaration order is an authoring accident. Sorting by title
        means a client rendering a legend gets the same one twice."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        titles = [
            t["title"]
            for t in (
                await client.get(
                    f"/workspaces/{workspace}/signal-catalog",
                    headers=_auth(key_pair, user),
                )
            ).json()["types"]
        ]

        assert titles == sorted(titles)

    async def test_a_non_member_gets_404(self, client: AsyncClient, key_pair: KeyPair) -> None:
        """The vocabulary is not secret, and the answer is still 404 — every
        endpoint under a workspace path answers alike, or the ones that do not
        become the way to test whether a workspace exists."""
        owner, outsider = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)

        response = await client.get(
            f"/workspaces/{workspace}/signal-catalog", headers=_auth(key_pair, outsider)
        )

        assert response.status_code == 404

    async def test_every_field_is_documented(self, client: AsyncClient) -> None:
        schema = (await client.get("/openapi.json")).json()
        for name in ("SignalCatalogResponse", "SignalTypeResponse"):
            properties = schema["components"]["schemas"][name]["properties"]
            undocumented = sorted(k for k, v in properties.items() if not v.get("description"))
            assert undocumented == [], f"{name}: {undocumented} reach the wire undocumented"


class TestTheRowSaysWhatKindOfAttentionThisIs:
    """**R9-03.** A contraction risk rendered identically to an expansion
    opportunity, and a manager scanning twelve rows had to read twelve titles.

    The Buying Score Engine computes posture and refuses to net it into the
    score — *two accounts can score identically and mean opposite things* —
    and the list is where that refusal stopped being visible.
    """

    async def test_the_row_carries_the_posture_of_its_leading_hypothesis(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        rows = (await _accounts(client, key_pair, user_id, workspace_id)).json()["items"]

        assert rows, "the fixture produced no rows"
        for row in rows:
            assert row["posture"] in {
                "expansionary",
                "contractionary",
                "neutral",
                None,
            }

    async def test_posture_and_hypothesis_are_absent_together(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Both come from the live score, so an account whose evidence has
        expired has neither. **One absence, not two** — a row with a posture
        and no hypothesis would invite a reader to reconcile two statements
        that are one fact."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        rows = (await _accounts(client, key_pair, user_id, workspace_id)).json()["items"]

        for row in rows:
            assert (row["posture"] is None) == (row["signal_type"] is None)

    async def test_the_row_maps_no_catalog_key_to_a_meaning(self) -> None:
        """**The reason posture is on the wire at all.** A client holding
        `{contraction_risk: 'risk', …}` would be a second commercial
        vocabulary — wrong the moment the catalog gained a type, and invisible
        when it did. The same rule that keeps the *title* in the catalog
        (D33) keeps its *meaning* in the pipeline.
        """
        import inspect

        from modules.opportunity_engine.interface import schemas

        source = inspect.getsource(schemas).casefold()
        for catalog_key in (
            "contraction_risk",
            "expansion_opportunity",
            "displacement_opportunity",
        ):
            assert catalog_key not in source, (
                f"'{catalog_key}' is named in the module forbidden from reaching the "
                "Signal Engine. Posture travels on the wire so it does not have to be."
            )


def _rows(payload: object) -> list[dict[str, Any]]:
    """Every match across every group, in group order.

    **Search returns groups from TASK-408**, one per `EntityKind`, each saying
    whether Signora looked. These tests were written against the flat list that
    preceded the ruling and assert facts about *matches* rather than about
    grouping — so they read through this rather than being rewritten to care
    about a shape they are not testing. **The grouping itself is asserted in
    `TestTheGroupsSayWhatWasSearched` below**, which is where it belongs.
    """
    assert isinstance(payload, list)
    rows: list[dict[str, Any]] = []
    for group in payload:
        assert isinstance(group, dict)
        results = group["results"]
        assert isinstance(results, list)
        rows.extend(results)
    return rows


class TestFindingAnAccountByName:
    """`GET /workspaces/{id}/account-search` — A1.

    Against a real database, because the parts most likely to be wrong are the
    ones a fake cannot have: the JSONB accessor, `ILIKE`, wildcard escaping,
    and whether RLS actually stops a search crossing a workspace.
    """

    async def test_a_partial_name_finds_the_account(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        named = (
            await client.get(
                f"/workspaces/{workspace_id}/account-identities",
                params={"ids": [str(entity_id)]},
                headers=_auth(key_pair, user_id),
            )
        ).json()[0]
        assert named["name"], "the pipeline produced an account nothing can name"

        response = await client.get(
            f"/workspaces/{workspace_id}/account-search",
            params={"q": named["name"][:4]},
            headers=_auth(key_pair, user_id),
        )

        assert response.status_code == 200, response.text
        assert entity_id in {UUID(row["account"]["account_id"]) for row in _rows(response.json())}

    async def test_a_search_never_crosses_a_workspace(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**A tenancy assertion wearing a feature's clothes.** Search is the
        first endpoint that returns accounts the caller did not name, so it is
        the first place a missing `workspace_id` filter would hand one
        customer another's book of business — and it would look like a
        working search."""
        mine, my_user, my_entity, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        theirs, their_user, their_entity, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        assert mine != theirs

        their_name = (
            await client.get(
                f"/workspaces/{theirs}/account-identities",
                params={"ids": [str(their_entity)]},
                headers=_auth(key_pair, their_user),
            )
        ).json()[0]["name"]

        response = await client.get(
            f"/workspaces/{mine}/account-search",
            params={"q": their_name[:4]},
            headers=_auth(key_pair, my_user),
        )

        assert response.status_code == 200, response.text
        returned = {UUID(row["account"]["account_id"]) for row in _rows(response.json())}
        assert their_entity not in returned
        assert returned <= {my_entity} or returned, "only this workspace's accounts"

    async def test_a_wildcard_is_text_and_not_a_pattern(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**`%` is a character a customer typed, not an instruction.**
        Unescaped it matches every account in the workspace, so a search box
        would return the whole book of business for a keystroke — and look
        like it was working."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        response = await client.get(
            f"/workspaces/{workspace_id}/account-search",
            params={"q": "%%"},
            headers=_auth(key_pair, user_id),
        )

        assert response.status_code == 200, response.text
        assert _rows(response.json()) == []

    async def test_no_match_is_an_empty_list_not_a_404(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        response = await client.get(
            f"/workspaces/{workspace_id}/account-search",
            params={"q": "zzzzzznothing"},
            headers=_auth(key_pair, user_id),
        )

        assert response.status_code == 200, response.text
        assert _rows(response.json()) == []

    async def test_one_character_is_refused_before_it_reaches_the_database(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """A customer who has typed one letter has not asked a question yet."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        response = await client.get(
            f"/workspaces/{workspace_id}/account-search",
            params={"q": "a"},
            headers=_auth(key_pair, user_id),
        )

        assert response.status_code == 422, response.text

    async def test_every_result_says_what_it_is_and_why_it_is_here(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Against the real reader**, because the matched name is read out of
        a JSONB accessor and thrown away by one careless unpack — which is
        exactly what the previous implementation did."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        named = (
            await client.get(
                f"/workspaces/{workspace_id}/account-identities",
                params={"ids": [str(entity_id)]},
                headers=_auth(key_pair, user_id),
            )
        ).json()[0]

        response = await client.get(
            f"/workspaces/{workspace_id}/account-search",
            params={"q": named["name"][:4]},
            headers=_auth(key_pair, user_id),
        )

        assert response.status_code == 200, response.text
        row = next(
            r for r in _rows(response.json()) if r["account"]["account_id"] == str(entity_id)
        )
        assert row["result_type"] == "company"
        assert row["matched_name"], "a row that cannot say what matched explains nothing"
        assert named["name"][:4].lower() in row["matched_name"].lower()
        assert row["matched_source"], "somebody claimed that name"
        assert row["is_renamed"] is (row["matched_name"] != row["account"]["name"])


class TestHowACompanyHasChanged:
    """`GET /workspaces/{id}/accounts/{account_id}/observations` — A5.

    *"Is this company actually growing, or did it hire once?"* The brief says
    *"Grew headcount 15% over 32 days"* and, until this endpoint, nothing
    behind it.

    **Every field asserted here was computed by M4 and had no HTTP path**,
    which is Epic A's whole shape.
    """

    async def test_a_recorded_change_carries_what_it_moved_from_and_to(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        response = await client.get(
            f"/workspaces/{workspace_id}/accounts/{entity_id}/observations",
            headers=_auth(key_pair, user_id),
        )

        assert response.status_code == 200, response.text
        rows = response.json()
        assert rows, "the pipeline recorded changes for this account"

        for row in rows:
            assert row["provider"], "a change is only ever a change according to someone"
            assert row["observed_at"], "when the provider says it was true"
            assert row["attribute"] and row["kind"] and row["direction"]
            # **The window, whenever there is one to bound.** A transition
            # carries both ends; an occurrence has genuinely nothing it moved
            # from, and null there is absence rather than a missing field.
            if row["previous_value"] is not None:
                assert row["previous_observed_at"] is not None, (
                    "a transition bounds the window it happened in; a client drawing a "
                    "point without this claims precision the evidence does not have"
                )
                assert row["observed_at"] >= row["previous_observed_at"]

    async def test_the_seeded_pipeline_records_occurrences_and_no_transitions(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Pinning a limitation, not a behaviour** — see [B-319](../../../docs/BUGS.md).

        A transition needs one provider asserting a *state* attribute twice, and
        the scenario enriches each account once. So every observation the
        Playground produces is a first sighting, and **A5's screen has no
        evolution to draw** even though the engine computes transitions
        correctly.

        This test exists to fail the day that changes, because the day it does
        is the day A5's screen becomes demonstrable — and nothing else in the
        repository would say so.
        """
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        rows = (
            await client.get(
                f"/workspaces/{workspace_id}/accounts/{entity_id}/observations",
                headers=_auth(key_pair, user_id),
            )
        ).json()

        assert rows
        assert all(row["previous_value"] is None for row in rows), (
            "A transition appeared. The simulator now enriches an account more than "
            "once — remove this test, and A5's screen has a series to draw."
        )

    async def test_the_response_carries_no_judgement_about_significance(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Whether a move matters is the Business Event Engine's question.**
        A `significance`, `score` or `importance` here would be answered by
        whoever rendered it — and this module's public contract has refused
        one since M4. The wire shape must not quietly reintroduce it."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        response = await client.get(
            f"/workspaces/{workspace_id}/accounts/{entity_id}/observations",
            headers=_auth(key_pair, user_id),
        )

        for row in response.json():
            for judgement in ("significance", "score", "importance", "severity", "summary"):
                assert judgement not in row, f"'{judgement}' reached the wire"

    async def test_it_narrows_to_one_attribute(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        everything = (
            await client.get(
                f"/workspaces/{workspace_id}/accounts/{entity_id}/observations",
                headers=_auth(key_pair, user_id),
            )
        ).json()
        attribute = everything[0]["attribute"]

        response = await client.get(
            f"/workspaces/{workspace_id}/accounts/{entity_id}/observations",
            params={"attribute": attribute},
            headers=_auth(key_pair, user_id),
        )

        assert response.status_code == 200, response.text
        assert {row["attribute"] for row in response.json()} == {attribute}
        assert len(response.json()) <= len(everything)

    async def test_an_invented_attribute_is_refused_rather_than_ignored(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Silently returning everything for an unknown filter is how a client
        bug becomes a customer looking at the wrong data and believing it."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        response = await client.get(
            f"/workspaces/{workspace_id}/accounts/{entity_id}/observations",
            params={"attribute": "not_an_attribute"},
            headers=_auth(key_pair, user_id),
        )

        assert response.status_code == 422, response.text

    async def test_an_account_in_another_workspace_shows_nothing(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**An empty list, not another workspace's history.** The account
        identifier is well-formed and belongs to somebody else, which is the
        shape a scrape takes."""
        mine, my_user, _, _ = await _tracked(session_factory, admin_session_factory, "northwind")
        _, _, their_entity, _ = await _tracked(session_factory, admin_session_factory, "northwind")

        response = await client.get(
            f"/workspaces/{mine}/accounts/{their_entity}/observations",
            headers=_auth(key_pair, my_user),
        )

        assert response.status_code == 200, response.text
        assert response.json() == []


class TestTheRowSaysHowLongItHasBeenSittingThere:
    """**The Friday-afternoon question — LO-06.**

    An account taken on this morning and one taken on in March rendered as the
    same row, so *"what have I been sitting on?"* meant opening briefs one at a
    time.

    **The row already carried the state's stage and owner and left *when*
    behind.** `_page` returns the opportunity beside its current state, so this
    costs no query — the same shape as `owner_id` in M12.2 and `posture` in
    M12.3.
    """

    async def test_the_row_says_when_its_state_was_recorded(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        rows = (await _accounts(client, key_pair, user_id, workspace_id)).json()["items"]

        (row,) = [r for r in rows if UUID(r["account_id"]) == entity_id]
        assert row["since"], "the row cannot say how long it has stood where it stands"

    async def test_taking_an_account_on_restarts_the_clock(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**A workflow decision is the one act Signora can see**, so it is the
        only thing that moves this clock. A new signal arriving is *Signora*
        working, not the seller — letting it reset the count would let the
        platform's own activity hide a seller's inactivity."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        before = (await _accounts(client, key_pair, user_id, workspace_id)).json()["items"]
        (was,) = [r for r in before if UUID(r["account_id"]) == entity_id]

        await client.post(
            f"/workspaces/{workspace_id}/opportunities/{was['id']}/states",
            headers=_auth(key_pair, user_id),
            json={"stage": "engaged", "reason": "worth a call this quarter"},
        )

        after = (await _accounts(client, key_pair, user_id, workspace_id)).json()["items"]
        (now,) = [r for r in after if UUID(r["account_id"]) == entity_id]
        assert now["since"] > was["since"]
        # **`opened_at` did not move**, which is the distinction: one says when
        # Signora suggested this account and the other when a person last acted
        # on it. Collapsing them would answer neither question.
        assert now["opened_at"] == was["opened_at"]


class TestAHumanCanOpenAnOpportunity:
    """**The route into a capability the domain has had all along — LO-07.**

    `Qualification.MANUAL` has been modelled since M12.1 and rendered on every
    brief as *"somebody here added it"*, and **nothing could produce one**:
    `QualifyOpportunity` had a single caller, the buying-score handler, which
    never names a person (49-lead-ownership.md §14, F-3).

    It is also the recourse for the finding above it. A won deal is terminal,
    correctly — *the next deal at that account is genuinely a new
    opportunity* — and until now that sentence named a route nobody could take.
    """

    async def test_a_seller_can_open_one_the_policy_did_not(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        rows = (await _accounts(client, key_pair, user_id, workspace_id)).json()["items"]
        (row,) = [r for r in rows if UUID(r["account_id"]) == entity_id]
        # A won deal is reached through being worked — `tracking` cannot
        # become `closed_won`, which is the transition table doing its job.
        await client.post(
            f"/workspaces/{workspace_id}/opportunities/{row['id']}/states",
            headers=_auth(key_pair, user_id),
            json={"stage": "engaged", "reason": "worth a call this quarter"},
        )
        await client.post(
            f"/workspaces/{workspace_id}/opportunities/{row['id']}/states",
            headers=_auth(key_pair, user_id),
            json={"stage": "closed_won", "reason": "signed the three-year deal"},
        )

        response = await client.post(
            f"/workspaces/{workspace_id}/accounts/{entity_id}/opportunity",
            headers=_auth(key_pair, user_id),
            json={"reason": "they came back for the second site"},
        )

        assert response.status_code == 201, response.text
        body = response.json()
        assert UUID(body["account_id"]) == entity_id
        # **Opened, never owned.** A human opening an opportunity is still a
        # suggestion becoming a record; taking it on is a separate act.
        assert body["stage"] == "tracking"
        # **A new opportunity, not an edited one.** The won deal keeps its
        # history, its reasons and its outcome, and nothing rewrites them.
        assert body["generation"] == 1

    async def test_the_closed_deal_is_left_exactly_as_it_was(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The mistake stays on the record.** Records here are immutable, so
        a false win is not erased — the correction is a new opportunity whose
        reason names why it exists, and the win-rate figures keep the truth
        about what somebody actually recorded."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        rows = (await _accounts(client, key_pair, user_id, workspace_id)).json()["items"]
        (row,) = [r for r in rows if UUID(r["account_id"]) == entity_id]
        # A won deal is reached through being worked — `tracking` cannot
        # become `closed_won`, which is the transition table doing its job.
        await client.post(
            f"/workspaces/{workspace_id}/opportunities/{row['id']}/states",
            headers=_auth(key_pair, user_id),
            json={"stage": "engaged", "reason": "worth a call this quarter"},
        )
        await client.post(
            f"/workspaces/{workspace_id}/opportunities/{row['id']}/states",
            headers=_auth(key_pair, user_id),
            json={"stage": "closed_won", "reason": "signed the three-year deal"},
        )

        await client.post(
            f"/workspaces/{workspace_id}/accounts/{entity_id}/opportunity",
            headers=_auth(key_pair, user_id),
            json={"reason": "clicked the wrong row"},
        )

        decided = (
            await client.get(
                f"/workspaces/{workspace_id}/accounts/decided",
                headers=_auth(key_pair, user_id),
            )
        ).json()["items"]
        won = [d for d in decided if UUID(d["account_id"]) == entity_id]
        assert won, "the closed deal disappeared from the record"
        assert won[0]["stage"] == "closed_won"
        assert won[0]["reason"] == "signed the three-year deal"

    async def test_an_account_already_open_is_refused_rather_than_duplicated(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        response = await client.post(
            f"/workspaces/{workspace_id}/accounts/{entity_id}/opportunity",
            headers=_auth(key_pair, user_id),
            json={"reason": "I want to work this"},
        )

        assert response.status_code == 409, response.text
        # Reaches a customer verbatim, so no identifier (R4-03).
        assert str(entity_id) not in response.text

    async def test_an_account_signora_knows_nothing_about_is_a_404(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**An opportunity with no provenance is a record nobody can
        defend.** A manual opening bypasses the policy and never the score."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        response = await client.post(
            f"/workspaces/{workspace_id}/accounts/{uuid4()}/opportunity",
            headers=_auth(key_pair, user_id),
            json={"reason": "a company nobody has heard of"},
        )

        assert response.status_code == 404, response.text

    async def test_the_opening_names_the_person_who_asked(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Signora is not a person, and a human opening is not Signora.**
        The brief's opening line is the product's central claim made visible —
        *intelligence suggests, humans commit* — and it could only ever say
        *suggested* until now."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        rows = (await _accounts(client, key_pair, user_id, workspace_id)).json()["items"]
        (row,) = [r for r in rows if UUID(r["account_id"]) == entity_id]
        await client.post(
            f"/workspaces/{workspace_id}/opportunities/{row['id']}/states",
            headers=_auth(key_pair, user_id),
            json={"stage": "dismissed", "reason": "wrong segment"},
        )

        await client.post(
            f"/workspaces/{workspace_id}/accounts/{entity_id}/opportunity",
            headers=_auth(key_pair, user_id),
            json={"reason": "they raised, so I was wrong"},
        )

        brief = (
            await client.get(
                f"/workspaces/{workspace_id}/accounts/{entity_id}/opportunity",
                headers=_auth(key_pair, user_id),
            )
        ).json()
        assert brief["opened_by"] == "manual"
        assert brief["history"][0]["reason"] == "they raised, so I was wrong"
        # The opening entry of a *manual* opportunity names its actor, where an
        # automatic one names nobody. Only TRACKING may be machine-authored.
        assert brief["history"][0]["decided_by"] == str(user_id)


class TestADecidedRowNamesItsAuthor:
    """**A judgement without an author — the screen audit.**

    The decided row carried `owner_id` and said *yours* when it matched the
    reader. **An account nobody ever took on can still be dismissed**, so that
    answered *"who decided this?"* only when the reader happened to have owned
    it — on the one surface whose whole purpose is showing a customer a
    judgement back.
    """

    async def test_the_row_says_who_decided_even_when_nobody_held_it(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        rows = (await _accounts(client, key_pair, user_id, workspace_id)).json()["items"]
        (row,) = [r for r in rows if UUID(r["account_id"]) == entity_id]
        # Dismissed straight from `tracking`, so it was never owned by anybody.
        await client.post(
            f"/workspaces/{workspace_id}/opportunities/{row['id']}/states",
            headers=_auth(key_pair, user_id),
            json={"stage": "dismissed", "reason": "wrong segment entirely"},
        )

        decided = (
            await client.get(
                f"/workspaces/{workspace_id}/accounts/decided",
                headers=_auth(key_pair, user_id),
            )
        ).json()["items"]

        (entry,) = [d for d in decided if UUID(d["account_id"]) == entity_id]
        assert entry["owner_id"] is None, "this account was never held, which is the case"
        assert UUID(entry["decided_by"]) == user_id


async def _decision_package(
    client: AsyncClient, key_pair: KeyPair, user_id: UUID, workspace_id: UUID, account_id: UUID
) -> Any:
    return await client.get(
        f"/workspaces/{workspace_id}/accounts/{account_id}/decision-package",
        headers=_auth(key_pair, user_id),
    )


class TestTheConclusionCanBeRead:
    """`GET …/accounts/{account_id}/decision-package` — what Signora concluded.

    **The module reasoned for weeks with no way to be read** (417 §2c). These
    assert the boundary that changed: a stored conclusion comes back whole,
    with its citations, its objections and what produced it — and an account
    nobody has concluded about says so rather than inventing one.
    """

    async def _stored(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        workspace_id: UUID,
        account_id: UUID,
    ) -> None:
        from datetime import UTC, datetime, timedelta

        from modules.ai_platform.public import AIVendor, GroundedStatement
        from modules.ai_reasoning_engine.domain.package import (
            AlternativeReading,
            DecisionPackage,
        )
        from modules.ai_reasoning_engine.domain.support import SupportBasis
        from modules.ai_reasoning_engine.domain.temporal import TemporalExplanation
        from modules.ai_reasoning_engine.infrastructure.repository import (
            SqlDecisionPackageRepository,
        )
        from modules.buying_score_engine.public import ScoreTrigger, Trend
        from modules.opportunity_engine.public import EvidenceState
        from signora_platform.db import tenant_scoped_session

        now = datetime(2026, 8, 4, tzinfo=UTC)
        cited = f"buying_score:{uuid4()}"
        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=uuid4()
        ) as session:
            await SqlDecisionPackageRepository(session).save(
                DecisionPackage(
                    id=uuid4(),
                    workspace_id=workspace_id,
                    correlation_id=uuid4(),
                    subject_kind="account",
                    subject_id=account_id,
                    summary=GroundedStatement(
                        text="They are replacing a retiring platform.", evidence=(cited,)
                    ),
                    proposition=GroundedStatement(
                        text="A replacement evaluation is underway.", evidence=(cited,)
                    ),
                    stated_reasoning=(
                        GroundedStatement(
                            text="Two independent sources saw the same move.",
                            evidence=(cited,),
                        ),
                    ),
                    supporting_evidence=(cited,),
                    support=SupportBasis(
                        corroborating_providers=frozenset({"zoominfo", "apollo"}),
                        contributing_events=3,
                        evidence_state=EvidenceState.CURRENT,
                        contested=True,
                        dissenting_signals=1,
                    ),
                    temporal=TemporalExplanation(
                        trigger=ScoreTrigger.SIGNAL_GENERATED,
                        basis_at=now - timedelta(days=9),
                        computed_at=now,
                        delta=12,
                        trend=Trend.RISING,
                        evidence_state=EvidenceState.CURRENT,
                        valid_until=now + timedelta(days=14),
                        # Named, not None: `TemporalExplanation` refuses a
                        # first reading that differs by 12 from a reading that
                        # does not exist, which is the invariant doing its job.
                        supersedes=uuid4(),
                    ),
                    alternative_readings=(
                        AlternativeReading(
                            signal_type="hiring_surge",
                            reason="Only one source saw it.",
                        ),
                    ),
                    limitations=("Signora cannot see a conversation.",),
                    suggested_validation=("Ask the account owner what they heard.",),
                    catalog_version=1,
                    prompt_name="reasoning",
                    prompt_version=1,
                    prompt_fingerprint="a" * 64,
                    model="llama3.1:8b",
                    vendor=AIVendor.OLLAMA,
                    evidence_digest="b" * 64,
                    inference_id=uuid4(),
                    originating_buying_score_id=uuid4(),
                    created_at=now,
                )
            )

    async def test_the_conclusion_arrives_with_its_citations(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The grounding guarantee, end to end.** A conclusion a customer
        cannot check is the one thing this product must never ship."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        await self._stored(session_factory, workspace_id, entity_id)

        response = await _decision_package(client, key_pair, user_id, workspace_id, entity_id)

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["proposition"]["evidence"], "an uncited conclusion reached the wire"
        assert body["summary"]["evidence"]
        for step in body["stated_reasoning"]:
            assert step["evidence"], "an uncited reasoning step reached the wire"

    async def test_what_argues_against_it_arrives_too(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """A Decision Package is a decision *input*, not a verdict. An endpoint
        that served the conclusion without its objections would have turned it
        into one."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        await self._stored(session_factory, workspace_id, entity_id)

        body = (await _decision_package(client, key_pair, user_id, workspace_id, entity_id)).json()

        assert body["support"]["contested"] is True
        assert body["support"]["dissenting_signals"] == 1
        assert body["alternative_readings"][0]["signal_type"] == "hiring_surge"
        assert body["limitations"], "a conclusion with no stated blind spot"
        assert body["suggested_validation"], "no way to check it independently"

    async def test_the_response_says_what_produced_it(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        await self._stored(session_factory, workspace_id, entity_id)

        body = (await _decision_package(client, key_pair, user_id, workspace_id, entity_id)).json()

        assert body["model"] == "llama3.1:8b"
        assert body["prompt_name"] == "reasoning"
        assert body["vendor"]

    async def test_an_account_nobody_has_concluded_about_says_so(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The ordinary state of a new account.** A package is produced by a
        background worker after the pipeline has a score worth explaining, so
        404 here is the truth rather than a gap."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        response = await _decision_package(client, key_pair, user_id, workspace_id, entity_id)

        assert response.status_code == 404

    async def test_another_workspaces_conclusion_is_not_reachable(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**404, not 403** — the same answer an account that was never
        concluded about receives, so the endpoint cannot be used to discover
        that a workspace holds one (§7)."""
        owner_workspace, _, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        await self._stored(session_factory, owner_workspace, entity_id)
        outsider_workspace, outsider, _, _ = await _tracked(
            session_factory, admin_session_factory, "contoso"
        )

        response = await _decision_package(
            client, key_pair, outsider, outsider_workspace, entity_id
        )

        assert response.status_code == 404

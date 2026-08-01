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
        _, _, theirs_entity, _ = await _tracked(
            session_factory, admin_session_factory, "contoso"
        )

        response = await client.get(
            f"/workspaces/{mine_workspace}/account-identities",
            params={"ids": [str(theirs_entity)]},
            headers=_auth(key_pair, mine_user),
        )

        assert response.status_code == 200
        assert [i for i in response.json() if i["name"] is not None] == []

    async def test_a_non_member_gets_404(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
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
        _, _, theirs_entity, _ = await _tracked(
            session_factory, admin_session_factory, "contoso"
        )

        response = await _score(
            client, key_pair, mine_user, mine_workspace, theirs_entity
        )

        assert response.status_code == 404

    async def test_a_non_member_gets_404(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
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

        body = (
            await _opportunity(client, key_pair, user_id, workspace_id, entity_id)
        ).json()

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

        body = (
            await _opportunity(client, key_pair, user_id, workspace_id, entity_id)
        ).json()

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

        history = (
            await _opportunity(client, key_pair, user_id, workspace_id, entity_id)
        ).json()["history"]

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

        history = (
            await _opportunity(client, key_pair, user_id, workspace_id, entity_id)
        ).json()["history"]

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
        _, _, theirs_entity, _ = await _tracked(
            session_factory, admin_session_factory, "contoso"
        )

        response = await _opportunity(
            client, key_pair, mine_user, mine_workspace, theirs_entity
        )

        assert response.status_code == 404

    async def test_a_non_member_gets_404(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        workspace = await _workspace(client, key_pair, uuid4())

        response = await _opportunity(client, key_pair, uuid4(), workspace, uuid4())

        assert response.status_code == 404

    async def test_an_unauthenticated_request_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        workspace = await _workspace(client, key_pair, uuid4())

        response = await client.get(
            f"/workspaces/{workspace}/accounts/{uuid4()}/opportunity"
        )

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

        body = (
            await _narration(client, key_pair, user_id, workspace_id, entity_id)
        ).json()

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

        response = await _narration(
            client, key_pair, mine_user, mine_workspace, theirs_entity
        )

        assert response.status_code == 404

    async def test_a_non_member_gets_404(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        workspace = await _workspace(client, key_pair, uuid4())

        response = await _narration(client, key_pair, uuid4(), workspace, uuid4())

        assert response.status_code == 404

    async def test_an_unauthenticated_request_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        workspace = await _workspace(client, key_pair, uuid4())

        response = await client.get(
            f"/workspaces/{workspace}/accounts/{uuid4()}/narration"
        )

        assert response.status_code == 401

    async def test_every_response_field_is_documented(self, client: AsyncClient) -> None:
        schema = (await client.get("/openapi.json")).json()
        schemas = schema["components"]["schemas"]

        for name in ("AccountNarrationResponse", "NarrationStatementResponse"):
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

        body = (
            await _validation(client, key_pair, user_id, workspace_id, entity_id)
        ).json()

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

        body = (
            await _validation(client, key_pair, user_id, workspace_id, entity_id)
        ).json()

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
        body = (
            await _validation(client, key_pair, user_id, workspace_id, entity_id)
        ).json()
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

    async def test_a_non_member_gets_404(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        workspace = await _workspace(client, key_pair, uuid4())

        response = await _validation(client, key_pair, uuid4(), workspace, uuid4())

        assert response.status_code == 404

    async def test_an_unauthenticated_request_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        workspace = await _workspace(client, key_pair, uuid4())

        response = await client.get(
            f"/workspaces/{workspace}/accounts/{uuid4()}/validation"
        )

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
        _, _, theirs_entity, _ = await _tracked(
            session_factory, admin_session_factory, "contoso"
        )

        response = await _validation(
            client, key_pair, mine_user, mine_workspace, theirs_entity
        )

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

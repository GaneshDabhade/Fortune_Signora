"""The approach read path over the full stack.

**Sales Engagement's first reachable surface.** Its `public/` has published 39
names since SE-01 and nothing could get at any of them, because the three ports
`AssembleApproach` declares had no implementations. A-ii builds them, and this
exercises the whole chain a real request traverses: JWT verification,
server-side membership verification, RLS context, Casbin authorization, and the
two published contracts it reads through.

**Every declaration arrives through the product's own API.** No row is
inserted: a view assembled from data that came in by a private door proves the
door rather than the product.
"""

from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

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
        "/workspaces", json={"name": "Northwind"}, headers=_auth(key_pair, user_id)
    )
    assert response.status_code == 201, response.text
    return UUID(response.json()["id"])


async def _sell(
    client: AsyncClient, key_pair: KeyPair, user: UUID, workspace: UUID, *names: str
) -> list[UUID]:
    ids = [uuid4() for _ in names]
    response = await client.put(
        f"/workspaces/{workspace}/products",
        json={
            "expected_version": 0,
            "products": [
                {"id": str(pid), "name": name, "description": ""}
                for pid, name in zip(ids, names, strict=True)
            ],
        },
        headers=_auth(key_pair, user),
    )
    assert response.status_code == 200, response.text
    return ids


async def _declare_committee(
    client: AsyncClient,
    key_pair: KeyPair,
    user: UUID,
    workspace: UUID,
    committees: list[dict[str, Any]],
) -> None:
    response = await client.put(
        f"/workspaces/{workspace}/buying-committee",
        json={"expected_version": 0, "committees": committees},
        headers=_auth(key_pair, user),
    )
    assert response.status_code == 200, response.text


async def _approach(
    client: AsyncClient,
    key_pair: KeyPair,
    user: UUID,
    workspace: UUID,
    account: UUID,
    *,
    product_id: UUID | None = None,
) -> Any:
    query = "" if product_id is None else f"?product_id={product_id}"
    return await client.get(
        f"/workspaces/{workspace}/accounts/{account}/approach{query}",
        headers=_auth(key_pair, user),
    )


class TestItAlwaysAnswers:
    """**There is no 404 here, deliberately.**

    An account with nothing declared and nothing recorded still receives the
    roles that did not rank and the reasons they did not — which is the only
    shape that tells a seller what to fix, and the sentence a ranked list
    structurally cannot carry.
    """

    async def test_a_workspace_that_has_declared_nothing_still_gets_an_answer(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await _approach(client, key_pair, user, workspace, uuid4())

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["roles"] == []
        assert body["recommendation"]["action"] in {"approach", "verify", "wait"}
        assert body["recommendation"]["reason"]

    async def test_a_declared_committee_reaches_the_answer(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**The whole point of A-ii.** The committee is declared in one module
        and read in another, through `public/` and nothing else."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        (product,) = await _sell(client, key_pair, user, workspace, "Revenue Cloud")
        await _declare_committee(
            client,
            key_pair,
            user,
            workspace,
            [
                {
                    "product_id": str(product),
                    "roles": [
                        {"title": "VP of Revenue Operations", "part": "economic_buyer"},
                        {"title": "Head of Security", "part": "gatekeeper"},
                    ],
                }
            ],
        )

        response = await _approach(
            client, key_pair, user, workspace, uuid4(), product_id=product
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert [role["title"] for role in body["roles"]] == [
            "VP of Revenue Operations",
            "Head of Security",
        ]

    async def test_an_unranked_role_says_why_not(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**`why_not` is the value of an unranked role, not an error.** With no
        evidence recorded, every role is unranked and each one says so."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        (product,) = await _sell(client, key_pair, user, workspace, "Revenue Cloud")
        await _declare_committee(
            client,
            key_pair,
            user,
            workspace,
            [{"product_id": str(product), "roles": [{"title": "CFO", "part": "economic_buyer"}]}],
        )

        response = await _approach(
            client, key_pair, user, workspace, uuid4(), product_id=product
        )

        role = response.json()["roles"][0]
        assert role["strength"] is None
        assert role["support"] == []
        assert role["why_not"]


class TestTheSellersOverride:
    """**An override is an answer, not a hint to be re-checked.**"""

    async def test_naming_a_product_leaves_the_ranking_out(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """`fits` is empty when the seller said which product. Showing a
        ranking beside their own answer invites them to re-litigate it."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        first, second = await _sell(client, key_pair, user, workspace, "Revenue Cloud", "Service")
        await _declare_committee(
            client,
            key_pair,
            user,
            workspace,
            [
                {"product_id": str(first), "roles": [{"title": "CFO", "part": "economic_buyer"}]},
                {"product_id": str(second), "roles": [{"title": "CTO", "part": "evaluator"}]},
            ],
        )

        response = await _approach(client, key_pair, user, workspace, uuid4(), product_id=second)

        body = response.json()
        assert body["fits"] == []
        assert body["product_id"] is None
        assert [role["title"] for role in body["roles"]] == ["CTO"]

    async def test_omitting_it_with_no_evidence_shows_no_roles(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**Asserts what the platform does, and it is asymmetric.**

        With an override and no evidence, every role comes back unranked with
        its `why_not`. Without one, `fit()` produces nothing, `_widest` returns
        `()` by its own last line, and the seller sees no roles at all — so the
        same account answers two different ways depending on whether they
        happened to name a product.

        The domain's reasoning covers a **tie** — *"a seller looking at a tie
        should still see which roles the evidence names"* — and this is the
        case below a tie, where there is nothing to rank. **Recorded rather
        than changed**: A-ii is an interface layer over an existing contract,
        and altering `_widest` is a domain decision outside this slice.
        """
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        first, second = await _sell(client, key_pair, user, workspace, "Revenue Cloud", "Service")
        await _declare_committee(
            client,
            key_pair,
            user,
            workspace,
            [
                {"product_id": str(first), "roles": [{"title": "CFO", "part": "economic_buyer"}]},
                {"product_id": str(second), "roles": [{"title": "CTO", "part": "evaluator"}]},
            ],
        )

        account = uuid4()

        response = await _approach(client, key_pair, user, workspace, account)

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["account_id"] == str(account)
        # **Nothing was chosen, and the seller still sees a committee.** With no
        # evidence recorded nothing distinguishes the two products, so the
        # reasoning runs against the widest one rather than returning an empty
        # screen while the question is answered.
        assert body["product_id"] is None
        assert body["roles"] == []
        assert body["fits"] == []


class TestTenancyAndAuthorization:
    async def test_a_stranger_gets_404_not_403(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**A security property, not an inconsistency** (§7): `403` would
        confirm the workspace exists to somebody who is not in it."""
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        response = await _approach(client, key_pair, uuid4(), workspace, uuid4())

        assert response.status_code == 404, response.text

    async def test_it_refuses_an_unauthenticated_caller(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        workspace = await _workspace(client, key_pair, uuid4())

        response = await client.get(f"/workspaces/{workspace}/accounts/{uuid4()}/approach")

        assert response.status_code == 401


class TestTheWireContract:
    async def test_it_names_no_person_anywhere(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**Roles, never people.** No person's name enters the platform at any
        point, and this surface has no field one could arrive in."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        (product,) = await _sell(client, key_pair, user, workspace, "Revenue Cloud")
        await _declare_committee(
            client,
            key_pair,
            user,
            workspace,
            [{"product_id": str(product), "roles": [{"title": "CFO", "part": "economic_buyer"}]}],
        )

        body = (
            await _approach(client, key_pair, user, workspace, uuid4(), product_id=product)
        ).json()

        fields = {key for role in body["roles"] for key in role}
        assert not {
            field
            for field in fields
            for term in ("person", "name", "email", "contact")
            if term in field.casefold() and field != "why_not"
        }

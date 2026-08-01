"""The commercial focus over the full stack.

The fourth customer-authored write in Signora, exercising the whole chain a
real request traverses: JWT verification, server-side membership verification,
RLS context, Casbin authorization, and PostgreSQL as the least-privileged role
— the one that holds no `UPDATE` grant on this table.
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
        "/workspaces", json={"name": "Acme"}, headers=_auth(key_pair, user_id)
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
                {"id": str(product_id), "name": name, "description": ""}
                for product_id, name in zip(ids, names, strict=True)
            ],
        },
        headers=_auth(key_pair, user),
    )
    assert response.status_code == 200, response.text
    return ids


async def _read(client: AsyncClient, key_pair: KeyPair, user: UUID, workspace: UUID) -> Any:
    return await client.get(f"/workspaces/{workspace}/focus", headers=_auth(key_pair, user))


async def _declare(
    client: AsyncClient,
    key_pair: KeyPair,
    user: UUID,
    workspace: UUID,
    *,
    products: list[UUID],
    objective: str = "",
    expected_version: int,
) -> Any:
    return await client.put(
        f"/workspaces/{workspace}/focus",
        json={
            "expected_version": expected_version,
            "products": [str(product_id) for product_id in products],
            "objective": objective,
        },
        headers=_auth(key_pair, user),
    )


class TestAWorkspaceWithNoFocus:
    async def test_it_reads_an_empty_focus_rather_than_a_404(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await _read(client, key_pair, user, workspace)

        assert response.status_code == 200, response.text
        assert response.json() == {
            "version": 0,
            "products": [],
            "objective": "",
            "updated_at": None,
            "updated_by": None,
        }


class TestDeclaringAFocus:
    async def test_it_is_stored_and_read_back_as_stated(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        core, enterprise = await _sell(
            client, key_pair, user, workspace, "Revenue Cloud", "Enterprise"
        )

        declared = await _declare(
            client,
            key_pair,
            user,
            workspace,
            products=[core, enterprise],
            objective="Land three health systems before December.",
            expected_version=0,
        )

        assert declared.status_code == 200, declared.text
        body = (await _read(client, key_pair, user, workspace)).json()
        assert body["version"] == 1
        assert body["products"] == [str(core), str(enterprise)]
        assert body["objective"] == "Land three health systems before December."

    async def test_it_records_who_declared_it_and_when(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**The date is the answer to whether the focus is current.** There
        is no period field precisely so there is nothing to disagree with
        it."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        (core,) = await _sell(client, key_pair, user, workspace, "Revenue Cloud")

        await _declare(client, key_pair, user, workspace, products=[core], expected_version=0)

        body = (await _read(client, key_pair, user, workspace)).json()
        assert body["updated_by"] == str(user)
        assert body["updated_at"] is not None

    async def test_a_revision_supersedes_rather_than_edits(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        core, enterprise = await _sell(
            client, key_pair, user, workspace, "Revenue Cloud", "Enterprise"
        )

        await _declare(client, key_pair, user, workspace, products=[core], expected_version=0)
        revised = await _declare(
            client,
            key_pair,
            user,
            workspace,
            products=[enterprise],
            expected_version=1,
        )

        assert revised.status_code == 200, revised.text
        assert revised.json()["version"] == 2
        assert revised.json()["products"] == [str(enterprise)]

    async def test_retracting_the_focus_is_a_new_version(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """*"We are not pushing anything in particular"* is a statement with
        an author and a moment — which is what makes it different from never
        having said anything."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        (core,) = await _sell(client, key_pair, user, workspace, "Revenue Cloud")

        await _declare(client, key_pair, user, workspace, products=[core], expected_version=0)
        retracted = await _declare(
            client, key_pair, user, workspace, products=[], expected_version=1
        )

        assert retracted.status_code == 200, retracted.text
        body = (await _read(client, key_pair, user, workspace)).json()
        assert (body["version"], body["products"]) == (2, [])
        assert body["updated_by"] == str(user), "a retraction still names its author"


class TestItNamesProductsTheWorkspaceSells:
    async def test_an_undeclared_product_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        await _sell(client, key_pair, user, workspace, "Revenue Cloud")

        response = await _declare(
            client, key_pair, user, workspace, products=[uuid4()], expected_version=0
        )

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "focus_unknown_product"
        assert "focus on" in response.json()["error"]["message"]


class TestTheFourDeclarationsVersionIndependently:
    async def test_declaring_a_focus_touches_none_of_the_other_three(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**Four aggregates, deliberately.** A focus changes every planning
        cycle and a catalog quarterly; one shared version would fill three
        audit histories with a fourth thing's changes."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        (core,) = await _sell(client, key_pair, user, workspace, "Revenue Cloud")
        icp = await client.put(
            f"/workspaces/{workspace}/icp",
            json={
                "expected_version": 0,
                "profiles": [{"product_id": str(core), "industries": ["Healthcare"]}],
            },
            headers=_auth(key_pair, user),
        )
        assert icp.status_code == 200, icp.text
        committee = await client.put(
            f"/workspaces/{workspace}/buying-committee",
            json={
                "expected_version": 0,
                "committees": [
                    {
                        "product_id": str(core),
                        "roles": [{"title": "CFO", "part": "economic_buyer"}],
                    }
                ],
            },
            headers=_auth(key_pair, user),
        )
        assert committee.status_code == 200, committee.text

        await _declare(client, key_pair, user, workspace, products=[core], expected_version=0)

        for path in ("products", "icp", "buying-committee"):
            other = await client.get(
                f"/workspaces/{workspace}/{path}", headers=_auth(key_pair, user)
            )
            assert other.json()["version"] == 1, path


class TestConcurrentEdits:
    async def test_a_stale_version_is_refused_with_the_one_in_force(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        core, enterprise = await _sell(
            client, key_pair, user, workspace, "Revenue Cloud", "Enterprise"
        )

        await _declare(client, key_pair, user, workspace, products=[core], expected_version=0)
        stale = await _declare(
            client, key_pair, user, workspace, products=[enterprise], expected_version=0
        )

        assert stale.status_code == 409
        assert stale.json()["error"]["code"] == "focus_version_conflict"
        assert "version 1" in stale.json()["error"]["message"]

    async def test_a_refused_declaration_writes_nothing(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        core, enterprise = await _sell(
            client, key_pair, user, workspace, "Revenue Cloud", "Enterprise"
        )

        await _declare(
            client,
            key_pair,
            user,
            workspace,
            products=[core],
            objective="Kept",
            expected_version=0,
        )
        await _declare(
            client,
            key_pair,
            user,
            workspace,
            products=[enterprise],
            objective="Lost",
            expected_version=0,
        )

        assert (await _read(client, key_pair, user, workspace)).json()["objective"] == ("Kept")


class TestWhatTheDomainRefuses:
    async def test_the_same_product_twice_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        (core,) = await _sell(client, key_pair, user, workspace, "Revenue Cloud")

        response = await _declare(
            client, key_pair, user, workspace, products=[core, core], expected_version=0
        )

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "focus_refused"

    async def test_an_unknown_field_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """`extra="forbid"`. The field this exists to catch is a rank or a
        weight added client-side — silently ignoring it would let a customer
        believe Signora had been told something it had not."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        (core,) = await _sell(client, key_pair, user, workspace, "Revenue Cloud")

        response = await client.put(
            f"/workspaces/{workspace}/focus",
            json={
                "expected_version": 0,
                "products": [str(core)],
                "objective": "",
                "rank": 1,
            },
            headers=_auth(key_pair, user),
        )

        assert response.status_code == 422


class TestTenancyAndAuthorization:
    async def test_another_workspace_s_focus_is_not_readable(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """A leaked focus tells a competitor what a company is pushing this
        quarter and what it is trying to land."""
        theirs_user = uuid4()
        theirs = await _workspace(client, key_pair, theirs_user)
        (core,) = await _sell(client, key_pair, theirs_user, theirs, "Revenue Cloud")
        await _declare(
            client,
            key_pair,
            theirs_user,
            theirs,
            products=[core],
            objective="Their plan for the quarter",
            expected_version=0,
        )

        response = await _read(client, key_pair, uuid4(), theirs)

        assert response.status_code == 404, "a non-member gets 404, never 403"

    async def test_a_member_may_read_but_not_declare(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner = uuid4()
        member = uuid4()
        workspace = await _workspace(client, key_pair, owner)
        (core,) = await _sell(client, key_pair, owner, workspace, "Revenue Cloud")
        added = await client.post(
            f"/workspaces/{workspace}/members",
            json={"user_id": str(member), "role": "member"},
            headers=_auth(key_pair, owner),
        )
        assert added.status_code == 201, added.text

        assert (await _read(client, key_pair, member, workspace)).status_code == 200
        refused = await _declare(
            client, key_pair, member, workspace, products=[core], expected_version=0
        )
        assert refused.status_code == 403

    async def test_an_unauthenticated_request_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        workspace = await _workspace(client, key_pair, uuid4())

        assert (await client.get(f"/workspaces/{workspace}/focus")).status_code == 401


class TestTheWireContract:
    async def test_every_response_field_is_documented(self, client: AsyncClient) -> None:
        schema = (await client.get("/openapi.json")).json()["components"]["schemas"]

        undocumented = sorted(
            field
            for field, spec in schema["CommercialFocusResponse"]["properties"].items()
            if not spec.get("description")
        )
        assert undocumented == [], f"{undocumented} reach the wire undocumented"

    async def test_it_reports_no_rank_weight_or_score(self, client: AsyncClient) -> None:
        """**The boundary, asserted on the wire.** The roadmap's word for this
        capability is *business priorities*, and an ordinal is exactly what
        that word invites."""
        schema = (await client.get("/openapi.json")).json()["components"]["schemas"]

        fields = set(schema["CommercialFocusResponse"]["properties"])

        assert not {
            field
            for field in fields
            for term in ("rank", "weight", "score", "priority", "position", "order")
            if term in field.casefold()
        }

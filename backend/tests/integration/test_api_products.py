"""The product catalog over the full stack.

**The first endpoint that stores something a customer wrote.** Every other
write in Signora records a decision *about* the pipeline's output; this one
records the input the pipeline has never had.

These exercise the whole chain a real request traverses: JWT verification,
server-side membership verification, RLS context, Casbin authorization, and
PostgreSQL as the least-privileged role — the one that holds no `UPDATE`
grant on this table.
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
    async with app.router.lifespan_context(app), AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as http:
        yield http


def _auth(key_pair: KeyPair, user_id: UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {mint_token(key_pair, user_id=user_id)}"}


async def _workspace(client: AsyncClient, key_pair: KeyPair, user_id: UUID) -> UUID:
    response = await client.post(
        "/workspaces", json={"name": "Acme", "slug": _test_slug("Acme")}, headers=_auth(key_pair, user_id)
    )
    assert response.status_code == 201, response.text
    return UUID(response.json()["id"])


async def _read(
    client: AsyncClient, key_pair: KeyPair, user: UUID, workspace: UUID
) -> Any:
    return await client.get(
        f"/workspaces/{workspace}/products", headers=_auth(key_pair, user)
    )


async def _publish(
    client: AsyncClient,
    key_pair: KeyPair,
    user: UUID,
    workspace: UUID,
    *,
    products: list[dict[str, str]],
    expected_version: int,
) -> Any:
    return await client.put(
        f"/workspaces/{workspace}/products",
        json={"expected_version": expected_version, "products": products},
        headers=_auth(key_pair, user),
    )


def _product(name: str = "Signora Core", description: str = "") -> dict[str, str]:
    return {"id": str(uuid4()), "name": name, "description": description}


class TestAWorkspaceThatHasDeclaredNothing:
    async def test_it_reads_an_empty_catalog_rather_than_a_404(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """The ordinary state of every new workspace. Answering with an
        absence would make the starting state look like a fault and force a
        branch on every caller."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await _read(client, key_pair, user, workspace)

        assert response.status_code == 200, response.text
        assert response.json() == {
            "version": 0,
            "products": [],
            "updated_at": None,
            "updated_by": None,
        }


class TestDeclaringACatalog:
    async def test_the_first_catalog_is_stored_and_read_back(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        product = _product("Revenue Cloud", "Pipeline generation for mid-market teams")

        published = await _publish(
            client, key_pair, user, workspace, products=[product], expected_version=0
        )

        assert published.status_code == 200, published.text
        assert published.json()["version"] == 1
        read_back = (await _read(client, key_pair, user, workspace)).json()
        assert read_back["products"] == [
            {
                "id": product["id"],
                "name": "Revenue Cloud",
                "description": "Pipeline generation for mid-market teams",
            }
        ]

    async def test_it_records_who_declared_it_and_when(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """A commercial declaration is a decision. The row is never edited,
        so this attribution cannot later be changed."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        await _publish(
            client, key_pair, user, workspace, products=[_product()], expected_version=0
        )

        body = (await _read(client, key_pair, user, workspace)).json()
        assert body["updated_by"] == str(user)
        assert body["updated_at"] is not None

    async def test_a_revision_supersedes_rather_than_edits(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**The immutability guarantee, over the real database.** The app
        role holds no `UPDATE` grant on this table, so a revision that tried
        to edit would fail here rather than in a unit test's fake."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        first = _product("Core")

        await _publish(
            client, key_pair, user, workspace, products=[first], expected_version=0
        )
        second = await _publish(
            client,
            key_pair,
            user,
            workspace,
            products=[first, _product("Enterprise")],
            expected_version=1,
        )

        assert second.status_code == 200, second.text
        assert second.json()["version"] == 2
        assert len(second.json()["products"]) == 2

    async def test_a_product_keeps_its_identity_across_revisions(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """What everything declared later depends on: an ICP or a priority
        cites a product id, and it must still resolve twelve revisions on."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        product = _product("Core")

        await _publish(
            client, key_pair, user, workspace, products=[product], expected_version=0
        )
        renamed = {**product, "name": "Core Platform"}
        await _publish(
            client, key_pair, user, workspace, products=[renamed], expected_version=1
        )

        body = (await _read(client, key_pair, user, workspace)).json()
        assert body["products"][0]["id"] == product["id"]
        assert body["products"][0]["name"] == "Core Platform"

    async def test_removing_a_product_is_a_new_version_not_a_deletion(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        await _publish(
            client,
            key_pair,
            user,
            workspace,
            products=[_product("A"), _product("B")],
            expected_version=0,
        )
        await _publish(
            client, key_pair, user, workspace, products=[], expected_version=1
        )

        body = (await _read(client, key_pair, user, workspace)).json()
        assert (body["version"], body["products"]) == (2, [])

    async def test_sending_the_same_catalog_twice_is_idempotent(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """The client chooses product ids precisely so a retried save cannot
        duplicate every product. The second attempt is refused on version,
        and the stored catalog is unchanged."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        body = [_product("Core")]

        await _publish(
            client, key_pair, user, workspace, products=body, expected_version=0
        )
        retried = await _publish(
            client, key_pair, user, workspace, products=body, expected_version=0
        )

        assert retried.status_code == 409
        stored = (await _read(client, key_pair, user, workspace)).json()
        assert (stored["version"], len(stored["products"])) == (1, 1)


class TestConcurrentEdits:
    async def test_a_stale_version_is_refused_with_the_one_in_force(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**The failure this exists to prevent**: two colleagues open the
        page, both save, and the second silently erases the first's work
        while both are told it worked."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        await _publish(
            client, key_pair, user, workspace, products=[_product("A")], expected_version=0
        )
        stale = await _publish(
            client, key_pair, user, workspace, products=[_product("B")], expected_version=0
        )

        assert stale.status_code == 409
        assert stale.json()["error"]["code"] == "catalog_version_conflict"
        assert "version 1" in stale.json()["error"]["message"]

    async def test_a_refused_publish_writes_nothing(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        kept = _product("Kept")

        await _publish(
            client, key_pair, user, workspace, products=[kept], expected_version=0
        )
        await _publish(
            client, key_pair, user, workspace, products=[_product("Lost")], expected_version=0
        )

        body = (await _read(client, key_pair, user, workspace)).json()
        assert body["products"][0]["id"] == kept["id"]


class TestWhatTheDomainRefuses:
    async def test_two_products_sharing_a_name_are_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await _publish(
            client,
            key_pair,
            user,
            workspace,
            products=[_product("Core"), _product("core")],
            expected_version=0,
        )

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "catalog_refused"
        assert "share a name" in response.json()["error"]["message"]

    async def test_an_unnamed_product_is_refused_before_the_domain(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """Schema validation catches it first, which is correct — the domain
        rule still holds and is asserted in the unit suite."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await _publish(
            client,
            key_pair,
            user,
            workspace,
            products=[{"id": str(uuid4()), "name": "", "description": ""}],
            expected_version=0,
        )

        assert response.status_code == 422

    async def test_an_unknown_field_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """`extra="forbid"`. A misspelled field silently ignored would let a
        customer believe they had declared something they had not."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await client.put(
            f"/workspaces/{workspace}/products",
            json={
                "expected_version": 0,
                "products": [{"id": str(uuid4()), "name": "Core", "prise": "100"}],
            },
            headers=_auth(key_pair, user),
        )

        assert response.status_code == 422


class TestTenancyAndAuthorization:
    async def test_another_workspace_s_catalog_is_not_readable(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**Tenant isolation over customer-authored data.** A product
        catalog states what a company sells — a leak here is competitive
        intelligence, not a row of derived numbers."""
        theirs_user = uuid4()
        theirs = await _workspace(client, key_pair, theirs_user)
        await _publish(
            client,
            key_pair,
            theirs_user,
            theirs,
            products=[_product("Their Secret Product")],
            expected_version=0,
        )

        response = await _read(client, key_pair, uuid4(), theirs)

        assert response.status_code == 404, "a non-member gets 404, never 403"

    async def test_a_member_may_read_but_not_declare(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
    ) -> None:
        """**Declaring what the company sells is an administrative act.**
        Every seller needs to see the catalog; changing it is the owner's,
        and this is the first place Signora's two roles differ on a business
        capability rather than on settings."""
        owner = uuid4()
        member = uuid4()
        workspace = await _workspace(client, key_pair, owner)
        added = await client.post(
            f"/workspaces/{workspace}/members",
            json={"user_id": str(member), "role": "member"},
            headers=_auth(key_pair, owner),
        )
        assert added.status_code == 201, added.text

        assert (await _read(client, key_pair, member, workspace)).status_code == 200
        refused = await _publish(
            client, key_pair, member, workspace, products=[_product()], expected_version=0
        )
        assert refused.status_code == 403

    async def test_an_unauthenticated_request_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        workspace = await _workspace(client, key_pair, uuid4())

        assert (await client.get(f"/workspaces/{workspace}/products")).status_code == 401


class TestTheWireContract:
    async def test_every_response_field_is_documented(self, client: AsyncClient) -> None:
        schema = (await client.get("/openapi.json")).json()["components"]["schemas"]

        for name in ("ProductCatalogResponse", "ProductResponse"):
            undocumented = sorted(
                field
                for field, spec in schema[name]["properties"].items()
                if not spec.get("description")
            )
            assert undocumented == [], f"{name}: {undocumented} reach the wire undocumented"

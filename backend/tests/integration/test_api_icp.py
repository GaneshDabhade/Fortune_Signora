"""The ideal customer over the full stack.

The second customer-authored write in Signora, and these exercise the whole
chain a real request traverses: JWT verification, server-side membership
verification, RLS context, Casbin authorization, and PostgreSQL as the
least-privileged role — the one that holds no `UPDATE` grant on this table.

**The most commercially sensitive rows in the platform.** A product catalog
says what a company sells; this says who they sell it to, in their own words.
The isolation test here is the one that matters most in the module.
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


async def _sell(client: AsyncClient, key_pair: KeyPair, user: UUID, workspace: UUID) -> UUID:
    """Declare one product, because an ideal customer must name one."""
    product_id = uuid4()
    response = await client.put(
        f"/workspaces/{workspace}/products",
        json={
            "expected_version": 0,
            "products": [{"id": str(product_id), "name": "Revenue Cloud", "description": ""}],
        },
        headers=_auth(key_pair, user),
    )
    assert response.status_code == 200, response.text
    return product_id


async def _read(client: AsyncClient, key_pair: KeyPair, user: UUID, workspace: UUID) -> Any:
    return await client.get(f"/workspaces/{workspace}/icp", headers=_auth(key_pair, user))


async def _declare(
    client: AsyncClient,
    key_pair: KeyPair,
    user: UUID,
    workspace: UUID,
    *,
    profiles: list[dict[str, Any]],
    expected_version: int,
) -> Any:
    return await client.put(
        f"/workspaces/{workspace}/icp",
        json={"expected_version": expected_version, "profiles": profiles},
        headers=_auth(key_pair, user),
    )


def _profile(product_id: UUID, **overrides: Any) -> dict[str, Any]:
    return {
        "product_id": str(product_id),
        "industries": ["Financial services"],
        **overrides,
    }


class TestAWorkspaceThatHasDescribedNobody:
    async def test_it_reads_an_empty_declaration_rather_than_a_404(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await _read(client, key_pair, user, workspace)

        assert response.status_code == 200, response.text
        assert response.json() == {
            "version": 0,
            "profiles": [],
            "updated_at": None,
            "updated_by": None,
        }


class TestDescribingTheIdealCustomer:
    async def test_it_is_stored_and_read_back_as_stated(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**Word for word.** The customer's capitalisation is part of what
        they said, and a module that records does not tidy it."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        product = await _sell(client, key_pair, user, workspace)

        declared = await _declare(
            client,
            key_pair,
            user,
            workspace,
            profiles=[
                _profile(
                    product,
                    industries=["Financial Services", "SaaS"],
                    countries=["United States", "United Kingdom"],
                    employees={"minimum": 200, "maximum": 2000},
                    notes="Only where they already run Salesforce.",
                )
            ],
            expected_version=0,
        )

        assert declared.status_code == 200, declared.text
        body = (await _read(client, key_pair, user, workspace)).json()
        assert body["version"] == 1
        assert body["profiles"] == [
            {
                "product_id": str(product),
                "industries": ["Financial Services", "SaaS"],
                "countries": ["United States", "United Kingdom"],
                "employees": {"minimum": 200, "maximum": 2000},
                "notes": "Only where they already run Salesforce.",
            }
        ]

    async def test_it_records_who_described_them_and_when(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        product = await _sell(client, key_pair, user, workspace)

        await _declare(
            client,
            key_pair,
            user,
            workspace,
            profiles=[_profile(product)],
            expected_version=0,
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
        product = await _sell(client, key_pair, user, workspace)

        await _declare(
            client,
            key_pair,
            user,
            workspace,
            profiles=[_profile(product)],
            expected_version=0,
        )
        revised = await _declare(
            client,
            key_pair,
            user,
            workspace,
            profiles=[_profile(product, industries=["Insurance"])],
            expected_version=1,
        )

        assert revised.status_code == 200, revised.text
        assert revised.json()["version"] == 2
        assert revised.json()["profiles"][0]["industries"] == ["Insurance"]

    async def test_size_may_be_stated_with_one_bound(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        product = await _sell(client, key_pair, user, workspace)

        response = await _declare(
            client,
            key_pair,
            user,
            workspace,
            profiles=[_profile(product, industries=[], employees={"minimum": 500})],
            expected_version=0,
        )

        assert response.status_code == 200, response.text
        assert response.json()["profiles"][0]["employees"] == {
            "minimum": 500,
            "maximum": None,
        }

    async def test_removing_a_description_is_a_new_version_not_a_deletion(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        product = await _sell(client, key_pair, user, workspace)

        await _declare(
            client,
            key_pair,
            user,
            workspace,
            profiles=[_profile(product)],
            expected_version=0,
        )
        await _declare(client, key_pair, user, workspace, profiles=[], expected_version=1)

        body = (await _read(client, key_pair, user, workspace)).json()
        assert (body["version"], body["profiles"]) == (2, [])


class TestItNamesAProductTheWorkspaceSells:
    async def test_an_undeclared_product_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """The reference would resolve to nothing, in the module whose whole
        job is being citable later."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        await _sell(client, key_pair, user, workspace)

        response = await _declare(
            client,
            key_pair,
            user,
            workspace,
            profiles=[_profile(uuid4())],
            expected_version=0,
        )

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "icp_unknown_product"
        assert "Add it under Products first" in response.json()["error"]["message"]

    async def test_the_description_survives_the_product_being_renamed(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**What the stable product id is for.** A catalog revision does not
        mint new products, so a description keeps pointing at the same one."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        product = await _sell(client, key_pair, user, workspace)
        await _declare(
            client,
            key_pair,
            user,
            workspace,
            profiles=[_profile(product)],
            expected_version=0,
        )

        renamed = await client.put(
            f"/workspaces/{workspace}/products",
            json={
                "expected_version": 1,
                "products": [{"id": str(product), "name": "Revenue Cloud EU", "description": ""}],
            },
            headers=_auth(key_pair, user),
        )
        assert renamed.status_code == 200, renamed.text

        body = (await _read(client, key_pair, user, workspace)).json()
        assert body["profiles"][0]["product_id"] == str(product)


class TestConcurrentEdits:
    async def test_a_stale_version_is_refused_with_the_one_in_force(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        product = await _sell(client, key_pair, user, workspace)

        await _declare(
            client,
            key_pair,
            user,
            workspace,
            profiles=[_profile(product)],
            expected_version=0,
        )
        stale = await _declare(
            client,
            key_pair,
            user,
            workspace,
            profiles=[_profile(product, industries=["Insurance"])],
            expected_version=0,
        )

        assert stale.status_code == 409
        assert stale.json()["error"]["code"] == "icp_version_conflict"
        assert "version 1" in stale.json()["error"]["message"]

    async def test_a_refused_declaration_writes_nothing(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        product = await _sell(client, key_pair, user, workspace)

        await _declare(
            client,
            key_pair,
            user,
            workspace,
            profiles=[_profile(product, industries=["Kept"])],
            expected_version=0,
        )
        await _declare(
            client,
            key_pair,
            user,
            workspace,
            profiles=[_profile(product, industries=["Lost"])],
            expected_version=0,
        )

        body = (await _read(client, key_pair, user, workspace)).json()
        assert body["profiles"][0]["industries"] == ["Kept"]

    async def test_the_catalog_and_the_description_version_independently(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**Two aggregates, deliberately.** Renaming a product must not mint
        a description version, or the audit history becomes unreadable."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        product = await _sell(client, key_pair, user, workspace)
        await _declare(
            client,
            key_pair,
            user,
            workspace,
            profiles=[_profile(product)],
            expected_version=0,
        )

        await client.put(
            f"/workspaces/{workspace}/products",
            json={
                "expected_version": 1,
                "products": [{"id": str(product), "name": "Revenue Cloud EU", "description": ""}],
            },
            headers=_auth(key_pair, user),
        )

        assert (await _read(client, key_pair, user, workspace)).json()["version"] == 1


class TestWhatTheDomainRefuses:
    async def test_a_description_with_no_criteria_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        product = await _sell(client, key_pair, user, workspace)

        response = await _declare(
            client,
            key_pair,
            user,
            workspace,
            profiles=[{"product_id": str(product), "notes": "the usual suspects"}],
            expected_version=0,
        )

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "icp_refused"
        assert "at least one thing" in response.json()["error"]["message"]

    async def test_an_inverted_size_range_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        product = await _sell(client, key_pair, user, workspace)

        response = await _declare(
            client,
            key_pair,
            user,
            workspace,
            profiles=[_profile(product, employees={"minimum": 5000, "maximum": 50})],
            expected_version=0,
        )

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "icp_refused"

    async def test_an_unknown_field_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """`extra="forbid"`. A misspelled field silently ignored would let a
        customer believe they had declared something they had not."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        product = await _sell(client, key_pair, user, workspace)

        response = await _declare(
            client,
            key_pair,
            user,
            workspace,
            profiles=[_profile(product, revenue_band="over_1b")],
            expected_version=0,
        )

        assert response.status_code == 422


class TestTenancyAndAuthorization:
    async def test_another_workspace_s_description_is_not_readable(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**The most sensitive rows in the platform.** A leaked ideal
        customer is a competitor's go-to-market strategy, stated by the
        company that owns it."""
        theirs_user = uuid4()
        theirs = await _workspace(client, key_pair, theirs_user)
        product = await _sell(client, key_pair, theirs_user, theirs)
        await _declare(
            client,
            key_pair,
            theirs_user,
            theirs,
            profiles=[_profile(product, industries=["Their target market"])],
            expected_version=0,
        )

        response = await _read(client, key_pair, uuid4(), theirs)

        assert response.status_code == 404, "a non-member gets 404, never 403"

    async def test_a_member_may_read_but_not_describe(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """Deciding who the company sells to is an administrative act, like
        deciding what it sells."""
        owner = uuid4()
        member = uuid4()
        workspace = await _workspace(client, key_pair, owner)
        product = await _sell(client, key_pair, owner, workspace)
        added = await client.post(
            f"/workspaces/{workspace}/members",
            json={"user_id": str(member), "role": "member"},
            headers=_auth(key_pair, owner),
        )
        assert added.status_code == 201, added.text

        assert (await _read(client, key_pair, member, workspace)).status_code == 200
        refused = await _declare(
            client,
            key_pair,
            member,
            workspace,
            profiles=[_profile(product)],
            expected_version=0,
        )
        assert refused.status_code == 403

    async def test_an_unauthenticated_request_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        workspace = await _workspace(client, key_pair, uuid4())

        assert (await client.get(f"/workspaces/{workspace}/icp")).status_code == 401


class TestTheWireContract:
    async def test_every_response_field_is_documented(self, client: AsyncClient) -> None:
        schema = (await client.get("/openapi.json")).json()["components"]["schemas"]

        for name in (
            "IcpDeclarationResponse",
            "ProductIcpResponse",
            "EmployeeRangeResponse",
        ):
            undocumented = sorted(
                field
                for field, spec in schema[name]["properties"].items()
                if not spec.get("description")
            )
            assert undocumented == [], f"{name}: {undocumented} reach the wire undocumented"

    async def test_it_reports_no_match_score_or_rank(self, client: AsyncClient) -> None:
        """**The boundary, asserted on the wire.** The module records a
        description; a conclusion about a company is not its to report, and a
        field here would be the first place one leaked."""
        schema = (await client.get("/openapi.json")).json()["components"]["schemas"]

        fields = {
            field
            for name in ("IcpDeclarationResponse", "ProductIcpResponse")
            for field in schema[name]["properties"]
        }

        assert not {
            field
            for field in fields
            for term in ("score", "match", "rank", "fit", "priority")
            if term in field.casefold()
        }

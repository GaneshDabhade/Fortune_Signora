"""The buying committee over the full stack.

The third customer-authored write in Signora, exercising the whole chain a
real request traverses: JWT verification, server-side membership verification,
RLS context, Casbin authorization, and PostgreSQL as the least-privileged role
— the one that holds no `UPDATE` grant on this table.

**The isolation test matters as much as the ideal customer's.** A leaked
committee tells a competitor exactly who to call inside their prospects'
organizations.
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


async def _sell(client: AsyncClient, key_pair: KeyPair, user: UUID, workspace: UUID) -> UUID:
    """Declare one product, because a committee must name one."""
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
    return await client.get(
        f"/workspaces/{workspace}/buying-committee", headers=_auth(key_pair, user)
    )


async def _declare(
    client: AsyncClient,
    key_pair: KeyPair,
    user: UUID,
    workspace: UUID,
    *,
    committees: list[dict[str, Any]],
    expected_version: int,
) -> Any:
    return await client.put(
        f"/workspaces/{workspace}/buying-committee",
        json={"expected_version": expected_version, "committees": committees},
        headers=_auth(key_pair, user),
    )


def _committee(product_id: UUID, *roles: dict[str, str]) -> dict[str, Any]:
    return {
        "product_id": str(product_id),
        "roles": list(roles) or [{"title": "VP of Revenue Operations", "part": "economic_buyer"}],
    }


class TestAWorkspaceWithNoCommittee:
    async def test_it_reads_an_empty_declaration_rather_than_a_404(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await _read(client, key_pair, user, workspace)

        assert response.status_code == 200, response.text
        assert response.json() == {
            "version": 0,
            "committees": [],
            "updated_at": None,
            "updated_by": None,
        }


class TestDeclaringACommittee:
    async def test_it_is_stored_and_read_back_as_stated(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**Word for word**, including the customer's own job titles."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        product = await _sell(client, key_pair, user, workspace)

        declared = await _declare(
            client,
            key_pair,
            user,
            workspace,
            committees=[
                _committee(
                    product,
                    {"title": "Chief Financial Officer", "part": "economic_buyer"},
                    {"title": "Head of Clinical Informatics", "part": "champion"},
                    {"title": "Head of Security", "part": "gatekeeper"},
                )
            ],
            expected_version=0,
        )

        assert declared.status_code == 200, declared.text
        body = (await _read(client, key_pair, user, workspace)).json()
        assert body["version"] == 1
        assert body["committees"][0]["roles"] == [
            {"title": "Chief Financial Officer", "part": "economic_buyer"},
            {"title": "Head of Clinical Informatics", "part": "champion"},
            {"title": "Head of Security", "part": "gatekeeper"},
        ]

    async def test_it_records_who_declared_it_and_when(
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
            committees=[_committee(product)],
            expected_version=0,
        )

        body = (await _read(client, key_pair, user, workspace)).json()
        assert body["updated_by"] == str(user)
        assert body["updated_at"] is not None

    async def test_a_revision_supersedes_rather_than_edits(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**The immutability guarantee, over the real database.** The app
        role holds no `UPDATE` grant, so a revision that tried to edit would
        fail here rather than in a unit test's fake."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        product = await _sell(client, key_pair, user, workspace)

        await _declare(
            client,
            key_pair,
            user,
            workspace,
            committees=[_committee(product)],
            expected_version=0,
        )
        revised = await _declare(
            client,
            key_pair,
            user,
            workspace,
            committees=[
                _committee(
                    product,
                    {"title": "VP of Revenue Operations", "part": "economic_buyer"},
                    {"title": "General Counsel", "part": "gatekeeper"},
                )
            ],
            expected_version=1,
        )

        assert revised.status_code == 200, revised.text
        assert revised.json()["version"] == 2
        assert len(revised.json()["committees"][0]["roles"]) == 2

    async def test_two_gatekeepers_are_the_ordinary_case(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """Security and legal are both gatekeepers. Only the title has to be
        distinguishable — the part is not a unique seat."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        product = await _sell(client, key_pair, user, workspace)

        response = await _declare(
            client,
            key_pair,
            user,
            workspace,
            committees=[
                _committee(
                    product,
                    {"title": "Head of Security", "part": "gatekeeper"},
                    {"title": "General Counsel", "part": "gatekeeper"},
                )
            ],
            expected_version=0,
        )

        assert response.status_code == 200, response.text

    async def test_removing_a_committee_is_a_new_version_not_a_deletion(
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
            committees=[_committee(product)],
            expected_version=0,
        )
        await _declare(client, key_pair, user, workspace, committees=[], expected_version=1)

        body = (await _read(client, key_pair, user, workspace)).json()
        assert (body["version"], body["committees"]) == (2, [])


class TestItNamesAProductTheWorkspaceSells:
    async def test_an_undeclared_product_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        await _sell(client, key_pair, user, workspace)

        response = await _declare(
            client,
            key_pair,
            user,
            workspace,
            committees=[_committee(uuid4())],
            expected_version=0,
        )

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "committee_unknown_product"
        assert "who decides about" in response.json()["error"]["message"]


class TestTheThreeDeclarationsVersionIndependently:
    async def test_declaring_a_committee_does_not_touch_the_catalog_or_the_icp(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**Three aggregates, deliberately.** Adding a security reviewer must
        not mint a version of what the company sells or who it sells to, or
        no audit history can answer *what changed*."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        product = await _sell(client, key_pair, user, workspace)
        icp = await client.put(
            f"/workspaces/{workspace}/icp",
            json={
                "expected_version": 0,
                "profiles": [{"product_id": str(product), "industries": ["Healthcare"]}],
            },
            headers=_auth(key_pair, user),
        )
        assert icp.status_code == 200, icp.text

        await _declare(
            client,
            key_pair,
            user,
            workspace,
            committees=[_committee(product)],
            expected_version=0,
        )

        catalog = await client.get(
            f"/workspaces/{workspace}/products", headers=_auth(key_pair, user)
        )
        described = await client.get(f"/workspaces/{workspace}/icp", headers=_auth(key_pair, user))
        assert catalog.json()["version"] == 1
        assert described.json()["version"] == 1
        assert (await _read(client, key_pair, user, workspace)).json()["version"] == 1


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
            committees=[_committee(product)],
            expected_version=0,
        )
        stale = await _declare(
            client,
            key_pair,
            user,
            workspace,
            committees=[_committee(product, {"title": "CFO", "part": "economic_buyer"})],
            expected_version=0,
        )

        assert stale.status_code == 409
        assert stale.json()["error"]["code"] == "committee_version_conflict"
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
            committees=[_committee(product, {"title": "Kept", "part": "champion"})],
            expected_version=0,
        )
        await _declare(
            client,
            key_pair,
            user,
            workspace,
            committees=[_committee(product, {"title": "Lost", "part": "champion"})],
            expected_version=0,
        )

        body = (await _read(client, key_pair, user, workspace)).json()
        assert body["committees"][0]["roles"][0]["title"] == "Kept"


class TestWhatTheDomainRefuses:
    async def test_a_committee_with_no_roles_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """Schema validation catches it first (`min_length=1`), which is
        correct — the domain rule still holds and is asserted in the unit
        suite."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        product = await _sell(client, key_pair, user, workspace)

        response = await _declare(
            client,
            key_pair,
            user,
            workspace,
            committees=[{"product_id": str(product), "roles": []}],
            expected_version=0,
        )

        assert response.status_code == 422

    async def test_two_roles_sharing_a_title_are_refused(
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
            committees=[
                _committee(
                    product,
                    {"title": "CFO", "part": "economic_buyer"},
                    {"title": "cfo", "part": "gatekeeper"},
                )
            ],
            expected_version=0,
        )

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "committee_refused"
        assert "share a title" in response.json()["error"]["message"]

    async def test_a_part_outside_the_vocabulary_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**The vocabulary is closed, and it is this module's own.** An
        invented part would be a value nothing could ever mean."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        product = await _sell(client, key_pair, user, workspace)

        response = await _declare(
            client,
            key_pair,
            user,
            workspace,
            committees=[_committee(product, {"title": "Analyst", "part": "influencer"})],
            expected_version=0,
        )

        assert response.status_code == 422

    async def test_an_unknown_field_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """`extra="forbid"`. The field this is most likely to catch is an
        influence weight somebody added client-side — and it must not be
        silently ignored, because a customer would believe it had been saved.
        """
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        product = await _sell(client, key_pair, user, workspace)

        response = await _declare(
            client,
            key_pair,
            user,
            workspace,
            committees=[
                _committee(
                    product,
                    {"title": "CFO", "part": "economic_buyer", "influence": "high"},
                )
            ],
            expected_version=0,
        )

        assert response.status_code == 422


class TestTenancyAndAuthorization:
    async def test_another_workspace_s_committee_is_not_readable(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """A leaked committee tells a competitor exactly who to call inside
        their prospects' organizations."""
        theirs_user = uuid4()
        theirs = await _workspace(client, key_pair, theirs_user)
        product = await _sell(client, key_pair, theirs_user, theirs)
        await _declare(
            client,
            key_pair,
            theirs_user,
            theirs,
            committees=[_committee(product, {"title": "Their champion", "part": "champion"})],
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
            committees=[_committee(product)],
            expected_version=0,
        )
        assert refused.status_code == 403

    async def test_an_unauthenticated_request_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        workspace = await _workspace(client, key_pair, uuid4())

        response = await client.get(f"/workspaces/{workspace}/buying-committee")

        assert response.status_code == 401


class TestTheWireContract:
    async def test_every_response_field_is_documented(self, client: AsyncClient) -> None:
        schema = (await client.get("/openapi.json")).json()["components"]["schemas"]

        for name in (
            "BuyingCommitteeResponse",
            "ProductCommitteeResponse",
            "CommitteeRoleResponse",
        ):
            undocumented = sorted(
                field
                for field, spec in schema[name]["properties"].items()
                if not spec.get("description")
            )
            assert undocumented == [], f"{name}: {undocumented} reach the wire undocumented"

    async def test_it_reports_no_influence_score_or_rank(self, client: AsyncClient) -> None:
        """**The boundary, asserted on the wire.** A committee is one
        plausible field away from an influence model, and that field would
        arrive here first."""
        schema = (await client.get("/openapi.json")).json()["components"]["schemas"]

        fields = {
            field
            for name in (
                "BuyingCommitteeResponse",
                "ProductCommitteeResponse",
                "CommitteeRoleResponse",
            )
            for field in schema[name]["properties"]
        }

        assert not {
            field
            for field in fields
            for term in ("score", "rank", "weight", "influence", "priority", "seniority")
            if term in field.casefold()
        }

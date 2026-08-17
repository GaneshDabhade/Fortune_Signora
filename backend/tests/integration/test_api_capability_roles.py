"""The capability layer through the API — [TASK-1479](../../../docs/BACKLOG.md) ⓸.

🔴 **Two things are the subject and neither is reachable from a unit test:**
**a member may read roles and may not change them**, and **the layer actually
narrows a real request** — 📁 which is the only assertion that proves it is
wired rather than merely built.
"""

from __future__ import annotations

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


async def _add_member(
    client: AsyncClient, key_pair: KeyPair, owner: UUID, workspace: UUID, person: UUID
) -> None:
    response = await client.post(
        f"/workspaces/{workspace}/members",
        json={"user_id": str(person), "role": "member"},
        headers=_auth(key_pair, owner),
    )
    assert response.status_code in (200, 201), response.text


async def _create_role(
    client: AsyncClient, key_pair: KeyPair, owner: UUID, workspace: UUID, name: str
) -> Any:
    return await client.post(
        f"/workspaces/{workspace}/capability-roles",
        json={"name": name},
        headers=_auth(key_pair, owner),
    )


class TestNamingARole:
    async def test_a_new_role_is_created_and_holds_nobody(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⚠️ **`holders: 0` is the only honest thing the response can say**, and
        the role grants nothing until `policy.csv` says otherwise."""
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        response = await _create_role(client, key_pair, owner, workspace, "Analyst")

        assert response.status_code == 201, response.text
        assert response.json()["name"] == "Analyst"
        assert response.json()["holders"] == 0

    async def test_a_membership_role_name_is_refused_with_its_own_code(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """🔴 **ADR-0410 §5's invariant, at the boundary.**

        ⛔ **The code is pinned, not just the status** — without its own row in
        the error map this reports the module's base code, which names
        something the customer was not doing.
        """
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        response = await _create_role(client, key_pair, owner, workspace, "owner")

        assert response.status_code == 422, response.text
        assert response.json()["error"]["code"] == "capability_refused"

    async def test_a_duplicate_name_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)
        await _create_role(client, key_pair, owner, workspace, "Analyst")

        response = await _create_role(client, key_pair, owner, workspace, "  ANALYST ")

        assert response.status_code == 422, response.text


class TestAMemberMayReadRolesAndMayNotChangeThem:
    """📁 `policy.csv` grants `member, capability_role, read` and withholds
    `update`. ⚡ **Team Management shows a colleague's role to everyone;
    defining roles is administration**, the same class as adding a member."""

    async def test_a_member_can_read_the_roles(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner, person = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)
        await _add_member(client, key_pair, owner, workspace, person)
        await _create_role(client, key_pair, owner, workspace, "Analyst")

        response = await client.get(
            f"/workspaces/{workspace}/capability-roles", headers=_auth(key_pair, person)
        )

        assert response.status_code == 200, response.text
        assert [role["name"] for role in response.json()["roles"]] == ["Analyst"]

    async def test_a_member_cannot_create_one(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⛔ **403 rather than 404** — the caller has demonstrably reached the
        workspace, so a `403` leaks nothing (18-authentication.md)."""
        owner, person = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)
        await _add_member(client, key_pair, owner, workspace, person)

        response = await _create_role(client, key_pair, person, workspace, "Analyst")

        assert response.status_code == 403, response.text

    async def test_a_member_cannot_change_somebody_s_role(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner, person = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)
        await _add_member(client, key_pair, owner, workspace, person)
        role_id = (
            await _create_role(client, key_pair, owner, workspace, "Analyst")
        ).json()["role_id"]

        response = await client.put(
            f"/workspaces/{workspace}/members/{person}/capability-role",
            json={"role_id": role_id},
            headers=_auth(key_pair, person),
        )

        assert response.status_code == 403, response.text


class TestTheLayerActuallyNarrowsARealRequest:
    """🔴 **The assertion that proves the slice is wired rather than built.**

    ⛔ Every other test here would pass against a capability layer that was
    stored, read back and never consulted by the enforcement point.
    """

    async def test_a_member_on_an_ungranted_role_loses_access_to_the_workspace(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⚡ **A member may read the roles list.** ⛔ **Change them to a role
        with no `policy.csv` rows and the same request is refused**, because the
        subject Casbin is asked about is no longer `member`.

        📁 **This is ADR-0410 §5's safe direction, observed end to end**: *"a
        capability that is not yet granted denies."*
        """
        owner, person = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)
        await _add_member(client, key_pair, owner, workspace, person)
        role_id = (
            await _create_role(client, key_pair, owner, workspace, "Analyst")
        ).json()["role_id"]

        before = await client.get(
            f"/workspaces/{workspace}/capability-roles", headers=_auth(key_pair, person)
        )
        assert before.status_code == 200, before.text

        assigned = await client.put(
            f"/workspaces/{workspace}/members/{person}/capability-role",
            json={"role_id": role_id},
            headers=_auth(key_pair, owner),
        )
        assert assigned.status_code == 204, assigned.text

        after = await client.get(
            f"/workspaces/{workspace}/capability-roles", headers=_auth(key_pair, person)
        )

        assert after.status_code == 403, (
            "the capability layer did not reach the enforcement point"
        )

    async def test_changing_back_restores_exactly_what_they_had(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⚡ ***Change back* is a real act**, and it must restore what the
        person had rather than something equivalent-looking."""
        owner, person = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)
        await _add_member(client, key_pair, owner, workspace, person)
        role_id = (
            await _create_role(client, key_pair, owner, workspace, "Analyst")
        ).json()["role_id"]
        await client.put(
            f"/workspaces/{workspace}/members/{person}/capability-role",
            json={"role_id": role_id},
            headers=_auth(key_pair, owner),
        )

        await client.put(
            f"/workspaces/{workspace}/members/{person}/capability-role",
            json={"role_id": None},
            headers=_auth(key_pair, owner),
        )

        restored = await client.get(
            f"/workspaces/{workspace}/capability-roles", headers=_auth(key_pair, person)
        )
        assert restored.status_code == 200, restored.text


class TestEffectivePermissions:
    async def test_it_reports_what_a_member_can_actually_do(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """📁 **Computed, never stored** — and every entry came from the same
        enforcer that decided the request that asked for it."""
        owner, person = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)
        await _add_member(client, key_pair, owner, workspace, person)

        response = await client.get(
            f"/workspaces/{workspace}/members/{person}/effective-permissions",
            headers=_auth(key_pair, owner),
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["role_name"] is None
        assert {"resource": "workspace", "action": "read"} in body["permissions"]

    async def test_a_narrowed_person_reports_their_role_and_fewer_permissions(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner, person = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)
        await _add_member(client, key_pair, owner, workspace, person)
        role_id = (
            await _create_role(client, key_pair, owner, workspace, "Analyst")
        ).json()["role_id"]
        await client.put(
            f"/workspaces/{workspace}/members/{person}/capability-role",
            json={"role_id": role_id},
            headers=_auth(key_pair, owner),
        )

        response = await client.get(
            f"/workspaces/{workspace}/members/{person}/effective-permissions",
            headers=_auth(key_pair, owner),
        )

        assert response.status_code == 200, response.text
        assert response.json()["role_name"] == "Analyst"
        assert response.json()["permissions"] == []

    async def test_somebody_who_is_not_a_member_is_a_404_with_its_own_code(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⛔ **Not an empty permission list.** 📁 An absence and *"a member who
        may do nothing"* are different facts, and the second is a sentence
        about somebody who is not there."""
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        response = await client.get(
            f"/workspaces/{workspace}/members/{uuid4()}/effective-permissions",
            headers=_auth(key_pair, owner),
        )

        assert response.status_code == 404, response.text
        assert response.json()["error"]["code"] == "member_not_found"


class TestAnotherWorkspaceCannotBeReached:
    async def test_a_non_member_gets_404_and_never_403(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner, stranger = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)

        response = await client.get(
            f"/workspaces/{workspace}/capability-roles", headers=_auth(key_pair, stranger)
        )

        assert response.status_code == 404, response.text


class TestPreviewingARoleChange:
    """📁 **The design's *Change role — Member → Analyst* dialog**, which shows
    *Gains* and *Loses* — *"both directions… because a role change is a trade
    rather than a promotion."*"""

    async def test_it_names_what_the_change_would_cost(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⚡ **The sentence the customer needs before clicking.** ⛔ Today a
        capability role grants nothing, so this is *"loses everything"* — 📁
        ADR-0410 §5's safe direction, **shown rather than discovered.**"""
        owner, person = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)
        await _add_member(client, key_pair, owner, workspace, person)
        role_id = (
            await _create_role(client, key_pair, owner, workspace, "Analyst")
        ).json()["role_id"]

        response = await client.get(
            f"/workspaces/{workspace}/members/{person}/capability-role/preview",
            params={"role_id": role_id},
            headers=_auth(key_pair, owner),
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["current"]["role_name"] is None
        assert {"resource": "workspace", "action": "read"} in body["current"]["permissions"]
        assert body["proposed"]["role_name"] == "Analyst"
        assert body["proposed"]["permissions"] == []

    async def test_changing_back_is_previewable_and_is_the_direction_that_gains(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner, person = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)
        await _add_member(client, key_pair, owner, workspace, person)
        role_id = (
            await _create_role(client, key_pair, owner, workspace, "Analyst")
        ).json()["role_id"]
        await client.put(
            f"/workspaces/{workspace}/members/{person}/capability-role",
            json={"role_id": role_id},
            headers=_auth(key_pair, owner),
        )

        response = await client.get(
            f"/workspaces/{workspace}/members/{person}/capability-role/preview",
            headers=_auth(key_pair, owner),
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["current"]["permissions"] == []
        assert body["proposed"]["role_name"] is None
        assert {"resource": "workspace", "action": "read"} in body["proposed"]["permissions"]

    async def test_a_role_that_is_not_here_is_refused_rather_than_shown_as_no_change(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⛔ **A dialog rendering *nothing changes* for a change the `PUT`
        would refuse is worse than an error** — it would say the act was safe."""
        owner, person = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)
        await _add_member(client, key_pair, owner, workspace, person)

        response = await client.get(
            f"/workspaces/{workspace}/members/{person}/capability-role/preview",
            params={"role_id": str(uuid4())},
            headers=_auth(key_pair, owner),
        )

        assert response.status_code == 422, response.text
        assert response.json()["error"]["code"] == "capability_refused"

    async def test_somebody_who_is_not_a_member_is_a_404_with_its_own_code(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        response = await client.get(
            f"/workspaces/{workspace}/members/{uuid4()}/capability-role/preview",
            headers=_auth(key_pair, owner),
        )

        assert response.status_code == 404, response.text
        assert response.json()["error"]["code"] == "member_not_found"

    async def test_a_member_may_read_a_preview(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⚠️ **`READ`, not `UPDATE`.** ⛔ Requiring the authority to perform the
        change would stop a member ever seeing why a control is not theirs —
        📁 the `onlyOwnersCan` shape the product already uses, one tier up."""
        owner, person = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)
        await _add_member(client, key_pair, owner, workspace, person)

        response = await client.get(
            f"/workspaces/{workspace}/members/{person}/capability-role/preview",
            headers=_auth(key_pair, person),
        )

        assert response.status_code == 200, response.text


class TestWhoHoldsWhat:
    async def test_the_roster_learns_every_held_role_in_one_request(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """🔴 **Team Management's role chip.** ⛔ Asking per person would be an
        N+1 on a screen that renders every colleague."""
        owner, holder, plain = uuid4(), uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)
        await _add_member(client, key_pair, owner, workspace, holder)
        await _add_member(client, key_pair, owner, workspace, plain)
        role_id = (
            await _create_role(client, key_pair, owner, workspace, "Analyst")
        ).json()["role_id"]
        await client.put(
            f"/workspaces/{workspace}/members/{holder}/capability-role",
            json={"role_id": role_id},
            headers=_auth(key_pair, owner),
        )

        response = await client.get(
            f"/workspaces/{workspace}/capability-assignments",
            headers=_auth(key_pair, owner),
        )

        assert response.status_code == 200, response.text
        assert response.json()["assignments"] == {str(holder): "Analyst"}

    async def test_changing_back_removes_them_from_the_answer(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⛔ **Absent, not `null`.** ⚡ A key with a null value would be a third
        way of saying *"holds nothing"*, and the screen would have to know all
        three."""
        owner, person = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)
        await _add_member(client, key_pair, owner, workspace, person)
        role_id = (
            await _create_role(client, key_pair, owner, workspace, "Analyst")
        ).json()["role_id"]
        for role in (role_id, None):
            await client.put(
                f"/workspaces/{workspace}/members/{person}/capability-role",
                json={"role_id": role},
                headers=_auth(key_pair, owner),
            )

        response = await client.get(
            f"/workspaces/{workspace}/capability-assignments",
            headers=_auth(key_pair, owner),
        )

        assert response.status_code == 200, response.text
        assert response.json()["assignments"] == {}

    async def test_a_member_may_read_it(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner, person = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)
        await _add_member(client, key_pair, owner, workspace, person)

        response = await client.get(
            f"/workspaces/{workspace}/capability-assignments",
            headers=_auth(key_pair, person),
        )

        assert response.status_code == 200, response.text

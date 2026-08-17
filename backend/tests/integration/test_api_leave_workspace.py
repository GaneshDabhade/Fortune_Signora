"""Leaving an organization, over HTTP and against real authorization.

**The unit tests cover the rules; this covers what a double cannot.** That
`Action.LEAVE`'s two policy grants actually admit a member and an owner, that
the domain's refusal reaches a customer as something they can act on rather
than as a fault, and that a departure genuinely removes access rather than only
recording that it should have.
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


def _auth(
    key_pair: KeyPair, user_id: UUID, *, email: str = "person@customer.test"
) -> dict[str, str]:
    token = mint_token(key_pair, user_id=user_id, email=email, email_verified=True)
    return {"Authorization": f"Bearer {token}"}


async def _workspace(client: AsyncClient, key_pair: KeyPair, owner: UUID) -> UUID:
    created = await client.post(
        "/workspaces", json={"name": "Acme", "slug": _test_slug("Acme")}, headers=_auth(key_pair, owner)
    )
    assert created.status_code == 201, created.text
    return UUID(created.json()["id"])


async def _joins(
    client: AsyncClient, key_pair: KeyPair, workspace_id: UUID, owner: UUID, *, role: str
) -> UUID:
    """A second person, by the door a customer actually uses: an invitation the
    owner sends and the joiner accepts with their own verified address."""
    email = f"{uuid4().hex[:8]}@customer.test"
    invited = await client.post(
        f"/workspaces/{workspace_id}/invitations",
        json={"email": email, "role": role},
        headers=_auth(key_pair, owner),
    )
    assert invited.status_code in (200, 201), invited.text

    joiner = uuid4()
    accepted = await client.post(
        f"/workspaces/{workspace_id}/invitations/accept",
        headers=_auth(key_pair, joiner, email=email),
    )
    assert accepted.status_code == 200, accepted.text
    return joiner


async def _leave(client: AsyncClient, key_pair: KeyPair, workspace_id: UUID, user: UUID) -> Any:
    return await client.post(
        f"/workspaces/{workspace_id}/membership/leave", headers=_auth(key_pair, user)
    )


class TestAPersonCanLeave:
    async def test_a_member_can_leave(self, client: AsyncClient, key_pair: KeyPair) -> None:
        """**`p, member, *, member, leave` admits them.** Before capability ④
        the grant did not exist; before this endpoint it authorised nothing."""
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)
        member = await _joins(client, key_pair, workspace_id, owner, role="member")

        response = await _leave(client, key_pair, workspace_id, member)

        assert response.status_code == 200, response.text
        assert response.json()["ended_at"] is not None

    async def test_they_can_no_longer_read_the_organization(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**The property that makes the rest worth having.** A membership that
        ended on paper and still granted access would be a departure that did
        nothing — and 404 rather than 403, because a workspace the caller
        cannot see must be indistinguishable from one that does not exist."""
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)
        member = await _joins(client, key_pair, workspace_id, owner, role="member")

        await _leave(client, key_pair, workspace_id, member)
        after = await client.get(
            f"/workspaces/{workspace_id}/members", headers=_auth(key_pair, member)
        )

        assert after.status_code == 404, after.text

    async def test_an_owner_can_leave_when_another_owner_remains(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**`p, owner, *, member, leave`**, and the case the invariant must not
        over-refuse: an administrator handing over and stepping back."""
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)
        second = await _joins(client, key_pair, workspace_id, owner, role="owner")

        response = await _leave(client, key_pair, workspace_id, second)

        assert response.status_code == 200, response.text

    async def test_the_organization_survives_the_departure(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """Everybody else is unaffected. Leaving is not a deletion of anything
        but one person's own involvement."""
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)
        member = await _joins(client, key_pair, workspace_id, owner, role="member")

        await _leave(client, key_pair, workspace_id, member)
        still_there = await client.get(
            f"/workspaces/{workspace_id}/members", headers=_auth(key_pair, owner)
        )

        assert still_there.status_code == 200, still_there.text


class TestTheLastOwnerCannotLeave:
    async def test_the_sole_owner_is_refused(self, client: AsyncClient, key_pair: KeyPair) -> None:
        """**409, not 500.** The domain has raised this since M1 and it was
        mapped nowhere, so the platform's fail-closed handler turned a refusal a
        customer can act on into *"An unexpected error occurred."*"""
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)

        response = await _leave(client, key_pair, workspace_id, owner)

        assert response.status_code == 409, response.text
        assert response.json()["error"]["code"] == "last_owner_cannot_leave"

    async def test_the_refusal_tells_them_what_to_do(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """The domain's sentence reaches the customer verbatim. That is the
        whole reason the mapping exists."""
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)

        response = await _leave(client, key_pair, workspace_id, owner)

        assert "Make somebody else an owner first" in response.json()["error"]["message"]

    async def test_a_refused_departure_leaves_them_a_member(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**The refusal must not half-apply.** A rolled-back departure that
        still ended the membership would be the worst outcome available: an
        organization with nobody who can administer it."""
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)

        await _leave(client, key_pair, workspace_id, owner)
        after = await client.get(
            f"/workspaces/{workspace_id}/members", headers=_auth(key_pair, owner)
        )

        assert after.status_code == 200, after.text

    async def test_the_last_owner_may_leave_once_somebody_else_can_administer(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """The refusal is a state, not a sentence about this person — which is
        why it is a conflict. Promote a colleague and the same request works."""
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)
        second = await _joins(client, key_pair, workspace_id, owner, role="owner")
        assert (await _leave(client, key_pair, workspace_id, owner)).status_code == 200

        response = await _leave(client, key_pair, workspace_id, second)

        assert response.status_code == 409, response.text


class TestLeavingIsSelfScoped:
    async def test_an_anonymous_caller_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)

        response = await client.post(f"/workspaces/{workspace_id}/membership/leave")

        assert response.status_code == 401, response.text

    async def test_somebody_who_is_not_a_member_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**404, and it never reaches the use case.** `CurrentWorkspace`
        verifies membership first, so a stranger cannot learn whether the
        workspace exists."""
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)

        response = await _leave(client, key_pair, workspace_id, uuid4())

        assert response.status_code == 404, response.text

    async def test_leaving_twice_is_refused(self, client: AsyncClient, key_pair: KeyPair) -> None:
        """The second tab. Accepting it would overwrite the moment the
        departure actually happened."""
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)
        member = await _joins(client, key_pair, workspace_id, owner, role="member")

        first = await _leave(client, key_pair, workspace_id, member)
        second = await _leave(client, key_pair, workspace_id, member)

        assert first.status_code == 200, first.text
        assert second.status_code == 404, second.text

    async def test_the_request_carries_no_target_to_substitute(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**The safest parameter is the one that does not exist.** There is no
        membership id in the path and no body, so there is nothing a caller
        could point at somebody else — and therefore no ownership check that
        could be written wrongly."""
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)
        member = await _joins(client, key_pair, workspace_id, owner, role="member")

        response = await client.post(
            f"/workspaces/{workspace_id}/membership/leave",
            json={"membership_id": str(uuid4()), "user_id": str(owner)},
            headers=_auth(key_pair, member),
        )

        # The body is ignored entirely: the member leaves, and the owner does not.
        assert response.status_code == 200, response.text
        assert (
            await client.get(f"/workspaces/{workspace_id}/members", headers=_auth(key_pair, owner))
        ).status_code == 200


class TestAnEndedMembershipGrantsNothing:
    """**The guarantee underneath this whole slice, and it was not holding.**

    `resolve_role` is the authoritative answer to *"is this person in this
    workspace"* on every authenticated request — `active_workspace_id` in the
    token is only a hint (18-authentication.md). It read
    `WorkspaceQueryService.get_membership`, which selected on
    `(workspace_id, user_id)` and **nothing else**, so an ended membership still
    resolved and **removal was a record rather than a revocation**
    ([B-206](../../../docs/BUGS.md)).

    `SqlMembershipRepository.get` had the filter and documented this exact
    outcome as the reason for it. **Two reads of one fact, and only one was
    filtered.**

    **Asserted through the customer's door rather than by seeding a row.** The
    first attempt inserted a membership directly and PostgreSQL refused it —
    row-level security doing its job — which is §20e's rule arriving as an
    error: *"test data enters the way a customer's data enters."* The end-to-end
    version is the stronger assertion anyway, because it exercises the
    dependency chain a request actually travels.
    """

    async def test_a_removed_member_loses_access(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**The pre-existing half, and the more serious one.** `member:remove`
        has existed since M1: an administrator removing somebody did not stop
        them reading the organization."""
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)
        member = await _joins(client, key_pair, workspace_id, owner, role="member")
        members = await client.get(
            f"/workspaces/{workspace_id}/members", headers=_auth(key_pair, owner)
        )
        membership_id = next(
            row["id"] for row in members.json()["items"] if row["user_id"] == str(member)
        )

        removed = await client.post(
            f"/workspaces/{workspace_id}/members/{membership_id}/remove",
            json={"reason": "left the company"},
            headers=_auth(key_pair, owner),
        )
        after = await client.get(
            f"/workspaces/{workspace_id}/members", headers=_auth(key_pair, member)
        )

        assert removed.status_code == 200, removed.text
        assert after.status_code == 404, after.text

    async def test_a_removed_member_cannot_reach_any_workspace_surface(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """Not only the members list. The check is in the dependency chain every
        workspace-scoped route shares, so proving one route would prove the
        weakest possible version of the guarantee."""
        owner = uuid4()
        workspace_id = await _workspace(client, key_pair, owner)
        member = await _joins(client, key_pair, workspace_id, owner, role="member")

        await _leave(client, key_pair, workspace_id, member)
        workspace = await client.get(f"/workspaces/{workspace_id}", headers=_auth(key_pair, member))

        assert workspace.status_code == 404, workspace.text

"""Joining an organization you were invited to, over HTTP and against real RLS.

**The one endpoint in Signora served to somebody outside the workspace.** The
unit tests in `modules/workspace_tenancy/tests/` cover the rules; this covers
the thing a double cannot: that the named single-purpose path
([C-208](../../../docs/LANE_COORDINATION.md)) reaches the invitation at all,
and that nothing else about tenancy moved to let it.

**A green suite here with a fake would have proved nothing.** The whole
difficulty is a row-level security policy, and a repository double reproduces
whatever its author believed the policy meant.
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

INVITED = "ada@example.com"


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
    key_pair: KeyPair,
    user_id: UUID,
    *,
    email: str = "founder@customer.test",
    email_verified: bool = True,
) -> dict[str, str]:
    token = mint_token(
        key_pair, user_id=user_id, email=email, email_verified=email_verified
    )
    return {"Authorization": f"Bearer {token}"}


async def _workspace_with_invitation(
    client: AsyncClient, key_pair: KeyPair, *, invited: str = INVITED
) -> tuple[UUID, UUID]:
    """A workspace whose owner has invited one address. Returns both ids —
    which is exactly what the invitation link carries."""
    owner = uuid4()
    created = await client.post(
        "/workspaces", json={"name": "Acme"}, headers=_auth(key_pair, owner)
    )
    assert created.status_code == 201, created.text
    workspace_id = UUID(created.json()["id"])

    invited_response = await client.post(
        f"/workspaces/{workspace_id}/invitations",
        json={"email": invited, "role": "member"},
        headers=_auth(key_pair, owner),
    )
    assert invited_response.status_code in (200, 201), invited_response.text
    return workspace_id, UUID(invited_response.json()["id"])


async def _accept(
    client: AsyncClient,
    key_pair: KeyPair,
    workspace_id: UUID,
    invitation_id: UUID,
    *,
    user_id: UUID | None = None,
    email: str = INVITED,
    email_verified: bool = True,
) -> Any:
    return await client.post(
        f"/workspaces/{workspace_id}/invitations/{invitation_id}/accept",
        headers=_auth(
            key_pair, user_id or uuid4(), email=email, email_verified=email_verified
        ),
    )


class TestTheInvitedPersonCanJoin:
    async def test_acceptance_creates_the_membership(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**The read that RLS makes hard.** The accepter is not a member, so
        no membership grants them `app.workspace_id` — and without the named
        path this request cannot see the row addressed to it."""
        workspace_id, invitation_id = await _workspace_with_invitation(client, key_pair)

        response = await _accept(client, key_pair, workspace_id, invitation_id)

        assert response.status_code == 200, response.text
        assert response.json()["workspace_id"] == str(workspace_id)
        assert response.json()["role"] == "member"

    async def test_they_can_then_read_the_workspace_they_joined(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**The membership is real, not just recorded.** A row that did not
        grant access would be a join that succeeded on paper."""
        workspace_id, invitation_id = await _workspace_with_invitation(client, key_pair)
        joining = uuid4()

        await _accept(client, key_pair, workspace_id, invitation_id, user_id=joining)
        members = await client.get(
            f"/workspaces/{workspace_id}/members",
            headers=_auth(key_pair, joining, email=INVITED),
        )

        assert members.status_code == 200, members.text

    async def test_following_the_link_twice_still_succeeds(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """The second click is the ordinary one. An error here would report a
        failure for the state the person asked for and already has."""
        workspace_id, invitation_id = await _workspace_with_invitation(client, key_pair)
        joining = uuid4()

        first = await _accept(
            client, key_pair, workspace_id, invitation_id, user_id=joining
        )
        second = await _accept(
            client, key_pair, workspace_id, invitation_id, user_id=joining
        )

        assert first.status_code == 200, first.text
        assert second.status_code == 200, second.text
        assert first.json()["id"] == second.json()["id"]


class TestHoldingTheLinkIsNotBeingTheAddressee:
    async def test_somebody_else_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**The test this endpoint exists to survive.** Both identifiers
        travel in a URL and neither is a secret."""
        workspace_id, invitation_id = await _workspace_with_invitation(client, key_pair)

        response = await _accept(
            client, key_pair, workspace_id, invitation_id, email="mallory@elsewhere.com"
        )

        assert response.status_code == 404, response.text

    async def test_an_unverified_address_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """An unverified address is the caller's own assertion. Accepting on
        one would let anybody type their way into a customer's data."""
        workspace_id, invitation_id = await _workspace_with_invitation(client, key_pair)

        response = await _accept(
            client, key_pair, workspace_id, invitation_id, email_verified=False
        )

        assert response.status_code == 403, response.text

    async def test_a_refused_attempt_grants_nothing(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**The property that matters most.** The named path sets workspace
        context before the address is checked, so a refusal must leave the
        caller with no access at all — otherwise the transaction that failed
        would still have been a way in."""
        workspace_id, invitation_id = await _workspace_with_invitation(client, key_pair)
        stranger = uuid4()

        await _accept(
            client,
            key_pair,
            workspace_id,
            invitation_id,
            user_id=stranger,
            email="mallory@elsewhere.com",
        )
        members = await client.get(
            f"/workspaces/{workspace_id}/members",
            headers=_auth(key_pair, stranger, email="mallory@elsewhere.com"),
        )

        assert members.status_code == 404, members.text

    async def test_an_invitation_from_another_workspace_is_not_reachable(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**Acceptance never reads across tenants.** Naming one workspace
        while holding another's invitation must find nothing."""
        _, invitation_id = await _workspace_with_invitation(client, key_pair)
        other_workspace, _ = await _workspace_with_invitation(client, key_pair)

        response = await _accept(client, key_pair, other_workspace, invitation_id)

        assert response.status_code == 404, response.text

    async def test_an_invented_invitation_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        workspace_id, _ = await _workspace_with_invitation(client, key_pair)

        response = await _accept(client, key_pair, workspace_id, uuid4())

        assert response.status_code == 404, response.text

    async def test_a_missing_invitation_and_somebody_elses_are_one_answer(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """Distinguishing them would answer *"has this workspace invited this
        person?"* to somebody who cannot see the workspace."""
        workspace_id, invitation_id = await _workspace_with_invitation(client, key_pair)

        missing = await _accept(client, key_pair, workspace_id, uuid4())
        theirs = await _accept(
            client, key_pair, workspace_id, invitation_id, email="mallory@elsewhere.com"
        )

        assert missing.status_code == theirs.status_code
        assert missing.json()["error"]["code"] == theirs.json()["error"]["code"]
        assert missing.json()["error"]["message"] == theirs.json()["error"]["message"]


class TestTheEndpointRequiresAuthentication:
    async def test_an_anonymous_caller_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """`CurrentUser` still authenticates. What it does not do is verify
        membership — which is the whole and only difference."""
        workspace_id, invitation_id = await _workspace_with_invitation(client, key_pair)

        response = await client.post(
            f"/workspaces/{workspace_id}/invitations/{invitation_id}/accept"
        )

        assert response.status_code == 401, response.text

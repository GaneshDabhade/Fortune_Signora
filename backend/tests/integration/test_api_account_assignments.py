"""Owner and CSM through the API — [TASK-1479](../../../docs/BACKLOG.md) slice ⓶.

🔴 **The refusal is the subject.** [ADR-0411](../../../docs/architecture/adr/0411-customer-organized-account-metadata.md)
says an owner is *"a reference to a workspace member, not free text"*, and
**the only thing that makes that true rather than aspirational is a request
that names a stranger and is turned down.**
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


async def _assign(
    client: AsyncClient,
    key_pair: KeyPair,
    user: UUID,
    workspace: UUID,
    *,
    accounts: list[UUID],
    member: UUID,
    role: str = "owner",
) -> Any:
    return await client.post(
        f"/workspaces/{workspace}/account-assignments",
        json={
            "account_ids": [str(account) for account in accounts],
            "role": role,
            "member_user_id": str(member),
        },
        headers=_auth(key_pair, user),
    )


class TestAnOwnerIsAReferenceToAMember:
    async def test_a_member_can_be_named(self, client: AsyncClient, key_pair: KeyPair) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await _assign(
            client, key_pair, user, workspace, accounts=[uuid4()], member=user
        )

        assert response.status_code == 200, response.text
        assert response.json()["changed"] == 1

    async def test_a_stranger_is_refused(self, client: AsyncClient, key_pair: KeyPair) -> None:
        """🔴 **The assertion the whole design exists for.**

        ⛔ **A reference that is never checked is free text with a `UUID`
        type**, and the dangling-name problem the ruling describes would arrive
        the first time somebody typed an id.
        """
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await _assign(
            client, key_pair, user, workspace, accounts=[uuid4()], member=uuid4()
        )

        assert response.status_code == 422, response.text

    async def test_the_refusal_says_which_person_and_not_just_that_it_failed(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⚠️ *"This person is not on your team"* is something a customer can
        act on; a bare *invalid request* is not."""
        user, stranger = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await _assign(
            client, key_pair, user, workspace, accounts=[uuid4()], member=stranger
        )

        assert str(stranger) in response.text
        assert response.json()["error"]["code"] == "not_a_workspace_member"


class TestTheResponseCountsWhatMovedRatherThanWhatWasSent:
    async def test_reassigning_the_same_member_changes_nothing(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⚡ **The confirmation a seller reads is the truth, not the size of
        their selection** — the same distinction the tag batch draws."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        account = uuid4()

        await _assign(client, key_pair, user, workspace, accounts=[account], member=user)
        second = await _assign(
            client, key_pair, user, workspace, accounts=[account], member=user
        )

        assert second.json() == {"role": "owner", "changed": 0, "unchanged": 1}

    async def test_an_empty_selection_is_refused_before_anything_is_created(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⛔ **A successful no-op would tell somebody their accounts were
        assigned.** P-A's shape, one layer up."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await _assign(
            client, key_pair, user, workspace, accounts=[], member=user
        )

        assert response.status_code == 422, response.text


class TestReadingBackWhatWasAssigned:
    async def test_it_answers_for_the_accounts_the_caller_named(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        held, unheld = uuid4(), uuid4()
        await _assign(client, key_pair, user, workspace, accounts=[held], member=user)

        response = await client.get(
            f"/workspaces/{workspace}/account-assignments",
            params={"account_ids": [str(held), str(unheld)]},
            headers=_auth(key_pair, user),
        )

        assert response.status_code == 200, response.text
        assignments = response.json()["assignments"]
        assert [a["account_id"] for a in assignments] == [str(held)]

    async def test_an_account_nobody_owns_is_absent_rather_than_an_error(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**Never a 404 and never empty-as-an-error** (P-A). The screen
        renders *Unassigned* either way."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await client.get(
            f"/workspaces/{workspace}/account-assignments",
            params={"account_ids": [str(uuid4())]},
            headers=_auth(key_pair, user),
        )

        assert response.status_code == 200
        assert response.json()["assignments"] == []

    async def test_owner_and_csm_come_back_separately(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⛔ Setting a CSM must not disturb the owner — they are frequently
        different people, which is why the ruling names two."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        account = uuid4()

        await _assign(
            client, key_pair, user, workspace, accounts=[account], member=user, role="owner"
        )
        await _assign(
            client, key_pair, user, workspace, accounts=[account], member=user, role="csm"
        )

        response = await client.get(
            f"/workspaces/{workspace}/account-assignments",
            params={"account_ids": [str(account)]},
            headers=_auth(key_pair, user),
        )

        assert {a["role"] for a in response.json()["assignments"]} == {"owner", "csm"}


class TestAnotherWorkspaceCannotBeReached:
    async def test_a_non_member_gets_404_and_never_403(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """📁 [§7](../../../CLAUDE.md): a caller who is not a member gets `404`,
        **never `403`** — a security property that prevents workspace
        enumeration, not an inconsistency to tidy up."""
        owner, outsider = uuid4(), uuid4()
        workspace = await _workspace(client, key_pair, owner)

        response = await client.get(
            f"/workspaces/{workspace}/account-assignments",
            params={"account_ids": [str(uuid4())]},
            headers=_auth(key_pair, outsider),
        )

        assert response.status_code == 404, response.text

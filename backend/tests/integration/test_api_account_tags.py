"""A customer's own labels over the full stack — [TASK-466](../../../docs/BACKLOG.md).

**The layer the unit tests cannot reach.** JWT verification · membership
verification · RLS context · Casbin · PostgreSQL as the least-privileged role
— and the two things this slice adds that only a real request exercises:

- 🔴 **the unique index on `(workspace_id, lower(name))` is what actually
  arbitrates two labels a customer cannot tell apart**, and the domain's
  `casefold` is a different function from Postgres's `lower`; and
- 🔴 **the reversal, against a real `account_tag_assignment` table** — where
  *"take the batch back"* meets rows that were already there.
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


async def _create_tag(
    client: AsyncClient,
    key_pair: KeyPair,
    user: UUID,
    workspace: UUID,
    *,
    name: str,
    tone: str = "risk",
) -> Any:
    return await client.post(
        f"/workspaces/{workspace}/account-tags",
        json={"name": name, "tone": tone},
        headers=_auth(key_pair, user),
    )


async def _apply(
    client: AsyncClient,
    key_pair: KeyPair,
    user: UUID,
    workspace: UUID,
    tag_id: str,
    accounts: list[UUID],
) -> Any:
    return await client.post(
        f"/workspaces/{workspace}/account-tags/{tag_id}/accounts",
        json={"accounts": [str(a) for a in accounts]},
        headers=_auth(key_pair, user),
    )


async def _assignments(
    client: AsyncClient,
    key_pair: KeyPair,
    user: UUID,
    workspace: UUID,
    accounts: list[UUID],
) -> Any:
    return await client.post(
        f"/workspaces/{workspace}/account-tags/assignments",
        json={"accounts": [str(a) for a in accounts]},
        headers=_auth(key_pair, user),
    )


class TestAWorkspaceThatHasNamedNoLabels:
    async def test_it_reads_an_empty_vocabulary_rather_than_a_404(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⛔ **An absent row is not an absent answer.** The screen renders
        *Add tag* either way, and a 404 would give every caller a branch to
        forget."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await client.get(
            f"/workspaces/{workspace}/account-tags", headers=_auth(key_pair, user)
        )

        assert response.status_code == 200, response.text
        assert response.json() == {"tags": []}


class TestTheUniqueIndexIsWhatArbitrates:
    async def test_two_labels_a_customer_cannot_tell_apart_are_one_tag(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """🔴 **The rule the domain states and the database enforces.**

        ⚡ The unit tests prove `TagVocabulary` refuses the pair. **This proves
        the whole request does** — and that a customer typing the second one
        gets the first tag back rather than an error, which is what makes *Add
        tag* safe to press twice.
        """
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        first = await _create_tag(client, key_pair, user, workspace, name="At risk")
        assert first.status_code == 200, first.text

        again = await _create_tag(client, key_pair, user, workspace, name="  at RISK ")

        assert again.status_code == 200, again.text
        assert again.json()["id"] == first.json()["id"]
        # ⛔ **And the tone is NOT restyled** by the second caller.
        assert again.json()["tone"] == "risk"

    async def test_one_workspace_s_labels_are_not_another_s(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """🔴 **The Security Invariant at the layer above the policy.**

        Two workspaces may both have *At risk* — the index is scoped to
        `workspace_id` — **and neither can see the other's.**
        """
        me, colleague = uuid4(), uuid4()
        mine = await _workspace(client, key_pair, me)
        theirs = await _workspace(client, key_pair, colleague)
        await _create_tag(client, key_pair, me, mine, name="At risk")

        response = await client.get(
            f"/workspaces/{theirs}/account-tags", headers=_auth(key_pair, colleague)
        )

        assert response.status_code == 200, response.text
        assert response.json() == {"tags": []}

    async def test_a_non_member_gets_404_rather_than_403(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """📁 [§7](../../../CLAUDE.md): *"a caller who is not a member of the
        workspace they name gets `404`, never `403`"* — it prevents workspace
        enumeration and is a security property rather than an inconsistency."""
        me, stranger = uuid4(), uuid4()
        mine = await _workspace(client, key_pair, me)

        response = await client.get(
            f"/workspaces/{mine}/account-tags", headers=_auth(key_pair, stranger)
        )

        assert response.status_code == 404, response.text


class TestARefusalSaysWhatWasRefused:
    async def test_a_blank_name_is_a_validation_error_and_never_a_500(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await _create_tag(client, key_pair, user, workspace, name="   ")

        assert response.status_code == 422, response.text

    async def test_a_tone_the_design_reserves_for_signora_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⛔ **`ai` is not a tone a customer may choose.** The design reserves
        it for what Signora inferred, and a human opinion wearing it is the one
        confusion the evidence model exists to prevent."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await _create_tag(
            client, key_pair, user, workspace, name="Looks good", tone="ai"
        )

        assert response.status_code == 422, response.text

    async def test_applying_a_tag_from_another_workspace_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        me, colleague = uuid4(), uuid4()
        mine = await _workspace(client, key_pair, me)
        theirs = await _workspace(client, key_pair, colleague)
        theirs_tag = await _create_tag(client, key_pair, colleague, theirs, name="At risk")

        response = await _apply(
            client, key_pair, me, mine, theirs_tag.json()["id"], [uuid4()]
        )

        assert response.status_code == 422, response.text
        # ⚡ **The code names the thing that was refused.** `AccountTagError`
        # inherits `CommercialProfileError`, and without its own row in the
        # mapping this would read `catalog_refused` — a document the caller was
        # not editing.
        assert response.json()["error"]["code"] == "account_tag_refused"


class TestPuttingALabelOnSeveralAccountsAtOnce:
    async def test_the_response_counts_what_changed_rather_than_what_was_asked(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        tag = (await _create_tag(client, key_pair, user, workspace, name="At risk")).json()
        june = [uuid4() for _ in range(3)]
        await _apply(client, key_pair, user, workspace, tag["id"], june)
        now = [uuid4() for _ in range(5)]

        response = await _apply(client, key_pair, user, workspace, tag["id"], june + now)

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["applied_count"] == 5
        assert body["total_count"] == 8
        assert sorted(body["changed"]) == sorted(str(a) for a in now)
        assert sorted(body["unchanged"]) == sorted(str(a) for a in june)

    async def test_selecting_one_row_twice_does_not_break_the_primary_key(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """🔴 **The half a fake could not prove.**

        ⛔ `(tag_id, account_id)` is a primary key, so a duplicate `INSERT`
        raises in Postgres. **The domain de-duplicates the selection**, and
        this is where that stops being a unit test — a table offering *Select
        all* on top of an existing selection is exactly how a row arrives
        twice.
        """
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        tag = (await _create_tag(client, key_pair, user, workspace, name="At risk")).json()
        account = uuid4()

        response = await _apply(
            client, key_pair, user, workspace, tag["id"], [account, account]
        )

        assert response.status_code == 200, response.text
        assert response.json()["applied_count"] == 1

    async def test_re_applying_to_an_account_that_has_it_writes_nothing(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⛔ **Against a real primary key, *"upsert and let it sort itself
        out"* is a 500 on a bulk action** rather than a tidier alternative."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        tag = (await _create_tag(client, key_pair, user, workspace, name="At risk")).json()
        account = uuid4()
        await _apply(client, key_pair, user, workspace, tag["id"], [account])

        response = await _apply(client, key_pair, user, workspace, tag["id"], [account])

        assert response.status_code == 200, response.text
        assert response.json()["applied_count"] == 0


class TestTheTagsOnAPageOfRows:
    async def test_it_answers_for_the_accounts_that_have_tags(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        risk = (await _create_tag(client, key_pair, user, workspace, name="At risk")).json()
        strategic = (
            await _create_tag(
                client, key_pair, user, workspace, name="Strategic", tone="neutral"
            )
        ).json()
        tagged, untagged = uuid4(), uuid4()
        await _apply(client, key_pair, user, workspace, risk["id"], [tagged])
        await _apply(client, key_pair, user, workspace, strategic["id"], [tagged])

        response = await _assignments(client, key_pair, user, workspace, [tagged, untagged])

        assert response.status_code == 200, response.text
        held = response.json()["assignments"]
        assert sorted(held[str(tagged)]) == sorted([risk["id"], strategic["id"]])
        # ⚡ **An account with no tags is absent**, and the request named it —
        # so *"we looked and found none"* is unambiguous.
        assert str(untagged) not in held


class TestARenameKeepsTheTagOnEveryAccount:
    async def test_the_id_does_not_move(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """🔴 **The whole reason a tag has an identity.** Without it, renaming
        is indistinguishable from deleting one label and creating another —
        and every account would silently lose it."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        tag = (await _create_tag(client, key_pair, user, workspace, name="At risk")).json()
        account = uuid4()
        await _apply(client, key_pair, user, workspace, tag["id"], [account])

        renamed = await client.patch(
            f"/workspaces/{workspace}/account-tags/{tag['id']}",
            json={"name": "Churn risk", "tone": "risk"},
            headers=_auth(key_pair, user),
        )

        assert renamed.status_code == 200, renamed.text
        assert renamed.json()["id"] == tag["id"]
        assert renamed.json()["name"] == "Churn risk"
        held = (await _assignments(client, key_pair, user, workspace, [account])).json()
        assert held["assignments"][str(account)] == [tag["id"]]

    async def test_renaming_onto_a_name_already_in_use_is_refused_with_a_sentence(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⛔ **Refused by the application, not by the index.** The index is
        what arbitrates two *concurrent* renames; a customer typing a name that
        is plainly taken should get a reason rather than a constraint
        violation."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        first = (await _create_tag(client, key_pair, user, workspace, name="At risk")).json()
        await _create_tag(client, key_pair, user, workspace, name="Churn risk")

        response = await client.patch(
            f"/workspaces/{workspace}/account-tags/{first['id']}",
            json={"name": "churn RISK", "tone": "risk"},
            headers=_auth(key_pair, user),
        )

        assert response.status_code == 422, response.text
        assert response.json()["error"]["code"] == "account_tag_refused"


class TestProposingABulkAddTag:
    """🔴 **The customer journey's first half, over the full stack.**

    ⛔ **Nothing is tagged by this request** — it creates something somebody is
    asked to approve, and 📁 ADR-0405 is why: *an action is approved before it
    is effective.*
    """

    async def test_it_answers_201_with_the_id_of_what_it_made(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        tag = (await _create_tag(client, key_pair, user, workspace, name="At risk")).json()
        accounts = [uuid4() for _ in range(3)]

        response = await client.post(
            f"/workspaces/{workspace}/account-tags/{tag['id']}/batches",
            json={"accounts": [str(a) for a in accounts]},
            headers=_auth(key_pair, user),
        )

        assert response.status_code == 201, response.text
        assert response.json()["item_count"] == 3
        UUID(response.json()["batch_id"])

    async def test_the_count_is_companies_and_not_clicks(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """⛔ **A customer approving *"Tag 3 companies"* when two are the same
        row has approved a sentence that is false**, and `item_count` is what
        the Action Batch reports for the rest of its life."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        tag = (await _create_tag(client, key_pair, user, workspace, name="At risk")).json()
        twice = uuid4()

        response = await client.post(
            f"/workspaces/{workspace}/account-tags/{tag['id']}/batches",
            json={"accounts": [str(twice), str(uuid4()), str(twice)]},
            headers=_auth(key_pair, user),
        )

        assert response.json()["item_count"] == 2

    async def test_nothing_is_tagged_until_somebody_approves_it(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """🔴 **The assertion that separates propose from apply.**

        ⚡ **Proposing is a question**, and a screen that showed the chips
        immediately would have told the customer the work was done before
        anybody accepted it.
        """
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        tag = (await _create_tag(client, key_pair, user, workspace, name="At risk")).json()
        account = uuid4()

        await client.post(
            f"/workspaces/{workspace}/account-tags/{tag['id']}/batches",
            json={"accounts": [str(account)]},
            headers=_auth(key_pair, user),
        )

        held = (await _assignments(client, key_pair, user, workspace, [account])).json()
        assert held["assignments"] == {}

    async def test_a_tag_from_another_workspace_proposes_nothing(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        me, colleague = uuid4(), uuid4()
        mine = await _workspace(client, key_pair, me)
        theirs = await _workspace(client, key_pair, colleague)
        theirs_tag = await _create_tag(client, key_pair, colleague, theirs, name="At risk")

        response = await client.post(
            f"/workspaces/{mine}/account-tags/{theirs_tag.json()['id']}/batches",
            json={"accounts": [str(uuid4())]},
            headers=_auth(key_pair, me),
        )

        assert response.status_code == 422, response.text
        assert response.json()["error"]["code"] == "account_tag_refused"

    async def test_an_empty_selection_is_refused_before_anything_is_created(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        # ⛔ **An approvable action over nothing** is a question with no answer,
        # and the schema refuses it before the use case is reached.
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        tag = (await _create_tag(client, key_pair, user, workspace, name="At risk")).json()

        response = await client.post(
            f"/workspaces/{workspace}/account-tags/{tag['id']}/batches",
            json={"accounts": []},
            headers=_auth(key_pair, user),
        )

        assert response.status_code == 422, response.text

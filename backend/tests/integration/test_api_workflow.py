"""The first write a customer can perform.

`POST /workspaces/{id}/opportunities/{id}/states` is where Signora stops being
something you read and becomes something you use. Every other endpoint reports
what the pipeline computed; this records what a person decided — and the two
are different kinds of fact. Delete every derived table and the pipeline
rebuilds it byte for byte. **Nothing anywhere reproduces a decision somebody
made**, which is why the guarantees asserted here are about *attribution* and
*refusal* rather than about correctness of a number.

Over the full stack, deliberately: JWT verification, server-side membership
verification, RLS context, Casbin authorization, the domain's transition rules,
the outbox, and PostgreSQL as the least-privileged role.
"""

from typing import Any
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from signora_platform.event_bus import OutboxEventModel
from signora_platform.tests.keys import KeyPair
from tests.integration.test_api_accounts import _auth, client, key_pair  # noqa: F401
from tests.opportunity_engine.test_opportunity_pipeline import _tracked

pytestmark = pytest.mark.integration


async def _open_opportunity(
    client: AsyncClient, key_pair: KeyPair, user_id: UUID, workspace_id: UUID
) -> UUID:
    """The opportunity the pipeline actually opened, read the way a client
    reads it — from the attention list, never constructed here."""
    response = await client.get(
        f"/workspaces/{workspace_id}/accounts", headers=_auth(key_pair, user_id)
    )
    assert response.status_code == 200, response.text
    rows = response.json()["items"]
    assert rows, "the pipeline opened no opportunity, so there is nothing to decide about"
    return UUID(rows[0]["id"])


async def _decide(
    client: AsyncClient,
    key_pair: KeyPair,
    user_id: UUID,
    workspace_id: UUID,
    opportunity_id: UUID,
    **body: Any,
) -> Any:
    return await client.post(
        f"/workspaces/{workspace_id}/opportunities/{opportunity_id}/states",
        json=body,
        headers=_auth(key_pair, user_id),
    )


async def _add_member(
    client: AsyncClient,
    key_pair: KeyPair,
    owner_id: UUID,
    workspace_id: UUID,
    new_member: UUID,
) -> None:
    response = await client.post(
        f"/workspaces/{workspace_id}/members",
        json={"user_id": str(new_member), "role": "member"},
        headers=_auth(key_pair, owner_id),
    )
    assert response.status_code in (200, 201), response.text


class TestAHumanCanCommitToAnAccount:
    """*"I'm working this one."* — the journey the whole slice exists for."""

    async def test_taking_an_account_on_is_recorded_with_who_and_why(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        opportunity_id = await _open_opportunity(client, key_pair, user_id, workspace_id)

        response = await _decide(
            client,
            key_pair,
            user_id,
            workspace_id,
            opportunity_id,
            stage="engaged",
            reason="Met their VP of Data at the conference last week.",
            owner_id=str(user_id),
        )

        assert response.status_code == 201, response.text
        state = response.json()
        assert state["stage"] == "engaged"
        assert UUID(state["owner_id"]) == user_id
        assert UUID(state["decided_by"]) == user_id
        assert state["reason"] == "Met their VP of Data at the conference last week."

    async def test_the_decision_is_there_on_the_next_load(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The brief and the list reflect it**, which is the difference
        between a control that works and one that appears to."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        opportunity_id = await _open_opportunity(client, key_pair, user_id, workspace_id)
        await _decide(
            client,
            key_pair,
            user_id,
            workspace_id,
            opportunity_id,
            stage="engaged",
            reason="Taking this on.",
            owner_id=str(user_id),
        )

        brief = (
            await client.get(
                f"/workspaces/{workspace_id}/accounts/{entity_id}/opportunity",
                headers=_auth(key_pair, user_id),
            )
        ).json()

        assert brief["stage"] == "engaged"
        assert UUID(brief["owner_id"]) == user_id
        assert [s["stage"] for s in brief["history"]] == ["tracking", "engaged"]
        # The opening entry names nobody: Signora may suggest tracking an
        # account and may do nothing else.
        assert brief["history"][0]["decided_by"] is None
        assert UUID(brief["history"][1]["decided_by"]) == user_id

    async def test_the_history_only_ever_grows(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Append-only over HTTP, not merely in the repository. A seller who
        engaged and then lost can still see that they engaged."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        opportunity_id = await _open_opportunity(client, key_pair, user_id, workspace_id)

        for stage, reason in (
            ("engaged", "Warm intro from a customer."),
            ("closed_lost", "They renewed with the incumbent for another year."),
        ):
            response = await _decide(
                client,
                key_pair,
                user_id,
                workspace_id,
                opportunity_id,
                stage=stage,
                reason=reason,
            )
            assert response.status_code == 201, response.text

        brief = (
            await client.get(
                f"/workspaces/{workspace_id}/accounts/{entity_id}/opportunity",
                headers=_auth(key_pair, user_id),
            )
        ).json()

        assert [s["stage"] for s in brief["history"]] == [
            "tracking",
            "engaged",
            "closed_lost",
        ]
        assert brief["history"][2]["reason"].startswith("They renewed")

    async def test_a_dismissal_keeps_the_sellers_words(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The only feedback Signora ever gets about its own qualification
        quality.** Dismissal is deliberately not a sales outcome, and the
        sentence explaining it is the whole value of the distinction."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        opportunity_id = await _open_opportunity(client, key_pair, user_id, workspace_id)

        response = await _decide(
            client,
            key_pair,
            user_id,
            workspace_id,
            opportunity_id,
            stage="dismissed",
            reason="They are a reseller, not an end customer. Wrong profile entirely.",
        )

        assert response.status_code == 201, response.text
        brief = (
            await client.get(
                f"/workspaces/{workspace_id}/accounts/{entity_id}/opportunity",
                headers=_auth(key_pair, user_id),
            )
        ).json()
        assert brief["stage"] == "dismissed"
        assert "reseller" in brief["history"][-1]["reason"]


class TestWhoDecidedIsNeverTakenFromTheRequest:
    async def test_the_actor_is_the_verified_caller(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**A member must not be able to sign another member's name to a
        decision.** The body below names somebody else as the actor; the
        recorded decision names the caller, because `actor_id` is not on the
        request contract at all.
        """
        workspace_id, owner_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        colleague = uuid4()
        await _add_member(client, key_pair, owner_id, workspace_id, colleague)
        opportunity_id = await _open_opportunity(client, key_pair, owner_id, workspace_id)

        response = await _decide(
            client,
            key_pair,
            colleague,
            workspace_id,
            opportunity_id,
            stage="engaged",
            reason="I am taking this.",
            actor_id=str(owner_id),
            decided_by=str(owner_id),
        )

        assert response.status_code == 201, response.text
        assert UUID(response.json()["decided_by"]) == colleague

    async def test_an_account_can_be_handed_to_a_colleague(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Who *decided* and who *holds it* are separate facts, and a manager
        assigning work depends on them staying separate."""
        workspace_id, owner_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        colleague = uuid4()
        await _add_member(client, key_pair, owner_id, workspace_id, colleague)
        opportunity_id = await _open_opportunity(client, key_pair, owner_id, workspace_id)

        response = await _decide(
            client,
            key_pair,
            owner_id,
            workspace_id,
            opportunity_id,
            stage="engaged",
            reason="Handing this to the named account rep.",
            owner_id=str(colleague),
        )

        assert response.status_code == 201, response.text
        state = response.json()
        assert UUID(state["owner_id"]) == colleague
        assert UUID(state["decided_by"]) == owner_id

    async def test_an_account_cannot_be_handed_outside_the_workspace(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Membership is verified server-side on every assignment. A `user_id`
        in a request is a *claim* about who should hold the work."""
        workspace_id, owner_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        opportunity_id = await _open_opportunity(client, key_pair, owner_id, workspace_id)

        response = await _decide(
            client,
            key_pair,
            owner_id,
            workspace_id,
            opportunity_id,
            stage="engaged",
            reason="Assigning to somebody who does not work here.",
            owner_id=str(uuid4()),
        )

        assert response.status_code == 422, response.text
        assert response.json()["error"]["code"] == "owner_not_a_member"


class TestTheServerRefusesWhatTheClientWouldNeverOffer:
    """**The client-side hide is a courtesy; this is the enforcement.**

    The brief only draws the transitions that are legal from where an account
    stands. Every one of these bypasses that entirely.
    """

    async def test_a_won_deal_does_not_reopen(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The next deal at that account is genuinely a new opportunity, and
        conflating them distorts every win-rate figure computed later."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        opportunity_id = await _open_opportunity(client, key_pair, user_id, workspace_id)
        for stage in ("engaged", "closed_won"):
            assert (
                await _decide(
                    client,
                    key_pair,
                    user_id,
                    workspace_id,
                    opportunity_id,
                    stage=stage,
                    reason="Progressing.",
                )
            ).status_code == 201

        response = await _decide(
            client,
            key_pair,
            user_id,
            workspace_id,
            opportunity_id,
            stage="engaged",
            reason="Actually, let us keep working it.",
        )

        assert response.status_code == 422, response.text
        assert response.json()["error"]["code"] == "transition_refused"
        assert "does not reopen" in response.json()["error"]["message"]

    async def test_skipping_straight_to_won_is_refused(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """A deal nobody ever engaged with was not won. The refusal names what
        *is* allowed, so a client author is not left guessing."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        opportunity_id = await _open_opportunity(client, key_pair, user_id, workspace_id)

        response = await _decide(
            client,
            key_pair,
            user_id,
            workspace_id,
            opportunity_id,
            stage="closed_won",
            reason="Signed.",
        )

        assert response.status_code == 422, response.text
        assert "engaged" in response.json()["error"]["message"]

    async def test_a_change_that_changes_nothing_is_refused(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """A state row recording no change is noise in an audit trail whose
        only job is to be readable."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        opportunity_id = await _open_opportunity(client, key_pair, user_id, workspace_id)

        response = await _decide(
            client,
            key_pair,
            user_id,
            workspace_id,
            opportunity_id,
            stage="tracking",
            reason="Confirming it is still tracked.",
        )

        assert response.status_code == 422, response.text
        assert response.json()["error"]["code"] == "transition_refused"

    async def test_a_decision_with_no_reason_is_refused(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Workflow has to explain itself as thoroughly as the intelligence
        does. Whitespace is not an explanation."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        opportunity_id = await _open_opportunity(client, key_pair, user_id, workspace_id)

        response = await _decide(
            client,
            key_pair,
            user_id,
            workspace_id,
            opportunity_id,
            stage="engaged",
            reason="   ",
        )

        assert response.status_code == 422, response.text

    async def test_a_stage_this_product_does_not_have_is_refused(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Rejected by the schema before a handler runs — the stage is an enum
        on the wire, not a free string."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        opportunity_id = await _open_opportunity(client, key_pair, user_id, workspace_id)

        response = await _decide(
            client,
            key_pair,
            user_id,
            workspace_id,
            opportunity_id,
            stage="qualified",
            reason="Inventing a stage.",
        )

        assert response.status_code == 422, response.text
        assert response.json()["error"]["code"] == "validation_error"


class TestOneWorkspaceCannotDecideForAnother:
    async def test_an_opportunity_that_does_not_exist_is_404(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        response = await _decide(
            client,
            key_pair,
            user_id,
            workspace_id,
            uuid4(),
            stage="engaged",
            reason="Deciding about nothing.",
        )

        assert response.status_code == 404, response.text
        assert response.json()["error"]["code"] == "opportunity_not_found"

    async def test_another_workspaces_opportunity_is_also_404(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Deliberately indistinguishable from the case above.** A 422
        saying *"that transition is illegal"* would confirm the opportunity
        exists, and identifiers would become enumerable one status code at a
        time.
        """
        mine, my_user, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        theirs, their_user, _, _ = await _tracked(
            session_factory, admin_session_factory, "contoso"
        )
        theirs_opportunity = await _open_opportunity(client, key_pair, their_user, theirs)

        response = await _decide(
            client,
            key_pair,
            my_user,
            mine,
            theirs_opportunity,
            stage="engaged",
            reason="Reaching into another tenant.",
        )

        assert response.status_code == 404, response.text

    async def test_a_non_member_gets_404_never_403(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        opportunity_id = await _open_opportunity(client, key_pair, user_id, workspace_id)

        response = await _decide(
            client,
            key_pair,
            uuid4(),
            workspace_id,
            opportunity_id,
            stage="engaged",
            reason="Not my workspace.",
        )

        assert response.status_code == 404, response.text

    async def test_an_unauthenticated_write_is_refused(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        opportunity_id = await _open_opportunity(client, key_pair, user_id, workspace_id)

        response = await client.post(
            f"/workspaces/{workspace_id}/opportunities/{opportunity_id}/states",
            json={"stage": "engaged", "reason": "No token at all."},
        )

        assert response.status_code == 401, response.text


class TestTheDecisionIsAnnouncedDurably:
    async def test_the_state_row_and_its_event_commit_together(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The transactional outbox, over a real request.

        An event published before its cause committed is the failure the
        outbox exists to prevent. Read here through the **admin** session
        because `signora_app` deliberately holds no read grant on
        `outbox_event` — the absence of that grant is itself a tenancy control
        (§8), and a test that needed it revoked would be testing the wrong
        thing.
        """
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        opportunity_id = await _open_opportunity(client, key_pair, user_id, workspace_id)

        assert (
            await _decide(
                client,
                key_pair,
                user_id,
                workspace_id,
                opportunity_id,
                stage="engaged",
                reason="Working it.",
            )
        ).status_code == 201

        async with admin_session_factory() as session:
            rows = (
                await session.execute(
                    select(OutboxEventModel).where(
                        OutboxEventModel.workspace_id == workspace_id,
                        OutboxEventModel.event_type == "opportunity.stage_changed",
                    )
                )
            ).scalars().all()

        assert len(rows) == 1, "the decision was recorded and never announced"
        assert rows[0].producer_module == "opportunity_engine"


class TestTheEndpointIsRegisteredAndDocumented:
    async def test_it_appears_in_the_generated_openapi(self, client: AsyncClient) -> None:
        schema = (await client.get("/openapi.json")).json()
        path = schema["paths"][
            "/workspaces/{workspace_id}/opportunities/{opportunity_id}/states"
        ]["post"]

        assert path["summary"] == "Record what you decided about this account"
        assert "i'm working this one" in path["description"].lower()

    async def test_every_request_field_is_documented(self, client: AsyncClient) -> None:
        schema = (await client.get("/openapi.json")).json()
        body = schema["components"]["schemas"]["RecordDecisionRequest"]["properties"]

        undocumented = sorted(
            name for name, spec in body.items() if not spec.get("description")
        )

        assert undocumented == [], f"{undocumented} reach the wire with no description"

    async def test_the_request_cannot_name_its_own_actor(self) -> None:
        """**Asserted on the contract, not only on behaviour.** A future
        author adding `actor_id` "for the CRM sync" would make impersonation
        possible with no other test failing."""
        from modules.opportunity_engine.interface.schemas import RecordDecisionRequest

        assert set(RecordDecisionRequest.model_fields) == {"stage", "reason", "owner_id"}


class TestTheLegalMovesComeFromTheDomain:
    """**One authoritative representation of the transition rules.**

    A client that reimplemented `allowed_from` would be a second copy of it,
    wrong the moment either changed — so the brief carries the moves and the
    client renders whatever it is told.
    """

    async def test_the_moves_arrive_in_the_order_work_moves_in(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        brief = (
            await client.get(
                f"/workspaces/{workspace_id}/accounts/{entity_id}/opportunity",
                headers=_auth(key_pair, user_id),
            )
        ).json()

        # **Not alphabetical.** Ordered by the `Stage` enum's own declaration,
        # so a client rendering them in order leads with the move a seller
        # usually wants. Sorted by value this read *"Lost"* first and *"I'm
        # working this"* last, which is the opposite of the product's opinion.
        assert brief["allowed_next"] == ["engaged", "closed_lost", "dismissed"]

    async def test_a_won_deal_offers_nothing(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Terminal, and the screen has nothing to draw. The empty list is the
        product's answer rather than a client-side special case."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        opportunity_id = await _open_opportunity(client, key_pair, user_id, workspace_id)
        for stage in ("engaged", "closed_won"):
            await _decide(
                client,
                key_pair,
                user_id,
                workspace_id,
                opportunity_id,
                stage=stage,
                reason="Progressing.",
            )

        brief = (
            await client.get(
                f"/workspaces/{workspace_id}/accounts/{entity_id}/opportunity",
                headers=_auth(key_pair, user_id),
            )
        ).json()

        assert brief["allowed_next"] == []

    async def test_a_dismissed_account_can_still_be_read_and_reopened(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Settled by M12.3.** A brief that vanished on dismissal would take
        the seller's own words with it and leave a legal reopening
        unreachable — which reads as the product deleting the account they
        just judged."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        opportunity_id = await _open_opportunity(client, key_pair, user_id, workspace_id)
        await _decide(
            client,
            key_pair,
            user_id,
            workspace_id,
            opportunity_id,
            stage="dismissed",
            reason="Wrong profile — they are a reseller.",
        )

        brief = (
            await client.get(
                f"/workspaces/{workspace_id}/accounts/{entity_id}/opportunity",
                headers=_auth(key_pair, user_id),
            )
        ).json()

        assert brief["stage"] == "dismissed"
        assert brief["allowed_next"] == ["tracking", "engaged"]

        reopened = await _decide(
            client,
            key_pair,
            user_id,
            workspace_id,
            opportunity_id,
            stage="tracking",
            reason="They acquired an end-customer business; worth watching again.",
        )
        assert reopened.status_code == 201, reopened.text

    async def test_a_closed_account_leaves_the_attention_list(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The list is open work. Dismissing something is how a seller makes
        their morning shorter, and a list that kept showing it would make the
        decision pointless."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        opportunity_id = await _open_opportunity(client, key_pair, user_id, workspace_id)
        before = (
            await client.get(
                f"/workspaces/{workspace_id}/accounts", headers=_auth(key_pair, user_id)
            )
        ).json()["items"]

        await _decide(
            client,
            key_pair,
            user_id,
            workspace_id,
            opportunity_id,
            stage="dismissed",
            reason="Not our market.",
        )

        after = (
            await client.get(
                f"/workspaces/{workspace_id}/accounts", headers=_auth(key_pair, user_id)
            )
        ).json()["items"]

        assert len(after) == len(before) - 1
        assert str(opportunity_id) not in {row["id"] for row in after}

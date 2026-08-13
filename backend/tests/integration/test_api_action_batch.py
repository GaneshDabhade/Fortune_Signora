"""Applying an action batch, over the full stack —
[TASK-465](../../../docs/BACKLOG.md), slice 5.

🔴 **`POST …/apply` is the row's whole subject, and its STATUS CODE is the
argument.** 📁 [§14](../../../CLAUDE.md): *a handler responds once the request
has been durably accepted, never after the work.* ⛔ **`200` would say the work
is done**, which is the risk the row names: *a customer told **applied** before
the work finishes.*

**These exercise the chain a real request traverses**: JWT verification,
server-side membership verification, RLS context, Casbin authorization, the
append-only write, the outbox row that will start the work, and PostgreSQL as
the least-privileged role.

⛔ **No worker runs anywhere in this file, and that is the point.** What is
asserted here is that the API *accepts* and *dispatches*; the applying is
verified against fakes in `tests/action_batch/test_handler.py`.
"""

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.api.main import create_app
from modules.action_batch.application.batches import ActionBatches, ProposeBatch
from modules.action_batch.infrastructure.composition import (
    build_action_batch_proposer,
    build_action_batches,
)
from modules.workspace_tenancy.application.use_cases import CreateWorkspaceInput
from modules.workspace_tenancy.infrastructure.composition import build_use_cases
from signora_platform.db import tenant_scoped_session, user_scoped_session
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

NOW = datetime(2026, 8, 10, 9, 0, tzinfo=UTC)


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


async def _workspace(factory: async_sessionmaker[AsyncSession]) -> tuple[UUID, UUID]:
    user_id = uuid4()
    async with user_scoped_session(factory, user_id=user_id) as session:
        result = await build_use_cases(session).create_workspace.execute(
            CreateWorkspaceInput(name="Action Batch", created_by=user_id),
            correlation_id=uuid4(),
        )
        return result.workspace.id, user_id


async def _approved_batch(
    factory: async_sessionmaker[AsyncSession], workspace_id: UUID, user_id: UUID
) -> UUID:
    """A batch somebody proposed and approved.

    ⚡ **Through the module's own use cases** — ⛔ **not by inserting rows.**
    📁 [§20e](../../../CLAUDE.md): *test data enters the way a customer's data
    enters.* **There is no propose/approve endpoint yet** (slice 6 brings the
    consumer that needs one), so the application layer is the door that exists.
    """
    async with tenant_scoped_session(factory, workspace_id=workspace_id, user_id=user_id) as s:
        batches: ActionBatches = build_action_batches(s)
        batch = await batches.propose(
            ProposeBatch(
                workspace_id=workspace_id,
                name="Archive 12 stale accounts",
                item_count=12,
                proposed_by=user_id,
                reversible_for=timedelta(hours=1),
            ),
            now=NOW,
        )
        await batches.approve(workspace_id, batch.id, actor_id=user_id, now=NOW)
        return batch.id


async def _outbox(admin_factory: async_sessionmaker[AsyncSession]) -> list[str]:
    async with admin_factory() as session:
        rows = await session.execute(text("SELECT event_type FROM outbox_event"))
        return [row[0] for row in rows]


class TestApplyingIsAcceptedAndDispatched:
    async def test_it_answers_202_ACCEPTED_and_never_200(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """🔴 **The row, in one assertion.**

        ⛔ **`200` would mean the work is done.** 📁 §14: the handler answers
        once the request is durably accepted, never after the work.
        """
        workspace_id, user_id = await _workspace(session_factory)
        batch_id = await _approved_batch(session_factory, workspace_id, user_id)

        response = await client.post(
            f"/workspaces/{workspace_id}/action-batches/{batch_id}/apply",
            headers=_auth(key_pair, user_id),
        )

        assert response.status_code == 202, response.text
        body = response.json()
        # ⚡ **What the screen may say**: accepted, and NOT applied.
        assert body["progress"] == "accepted"
        assert body["applied_at"] is None
        assert body["accepted_at"] is not None

    async def test_the_acceptance_publishes_the_event_that_will_start_the_work(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Through the outbox, in the request's own transaction** (§9).

        ⛔ **An event published before its cause committed would be a worker
        applying a change nobody successfully asked for.**
        """
        workspace_id, user_id = await _workspace(session_factory)
        batch_id = await _approved_batch(session_factory, workspace_id, user_id)

        await client.post(
            f"/workspaces/{workspace_id}/action-batches/{batch_id}/apply",
            headers=_auth(key_pair, user_id),
        )

        published = await _outbox(admin_session_factory)
        assert published.count("action_batch.application_requested") == 1
        # ⛔ **`applied` is the WORKER's to publish**, and it has not run.
        assert "action_batch.applied" not in published

    async def test_asking_twice_is_refused_rather_than_queued(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """⚠️ **Two dispatches of one approval means the change runs twice.**

        ⛔ **A defect to surface rather than a job to enqueue**, so the domain
        refuses it and the API answers `409` with the domain's own sentence.
        """
        workspace_id, user_id = await _workspace(session_factory)
        batch_id = await _approved_batch(session_factory, workspace_id, user_id)
        url = f"/workspaces/{workspace_id}/action-batches/{batch_id}/apply"

        first = await client.post(url, headers=_auth(key_pair, user_id))
        second = await client.post(url, headers=_auth(key_pair, user_id))

        assert first.status_code == 202
        assert second.status_code == 409, second.text
        assert "already dispatched" in second.text


class TestTheProgressRead:
    async def test_it_distinguishes_not_started_from_accepted(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """🔴 **[P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md)**, which
        [455](../../../docs/architecture/455-context-definitions-r02-r03.md)
        applies to this slice by name: **a batch still running and one that
        failed to start must never render alike** — ⛔ **and neither must
        *not started* and *running*.**
        """
        workspace_id, user_id = await _workspace(session_factory)
        batch_id = await _approved_batch(session_factory, workspace_id, user_id)
        url = f"/workspaces/{workspace_id}/action-batches/{batch_id}"

        before = await client.get(url, headers=_auth(key_pair, user_id))
        await client.post(f"{url}/apply", headers=_auth(key_pair, user_id))
        after = await client.get(url, headers=_auth(key_pair, user_id))

        assert before.json()["progress"] == "not_started"
        assert after.json()["progress"] == "accepted"
        assert before.json()["failure_reason"] is None

    async def test_a_batch_in_another_workspace_is_not_found_rather_than_forbidden(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """⛔ **`404`, never `403`** — 📁 §7. **`Forbidden` confirms the id
        exists**, which is a workspace-enumeration oracle.
        """
        workspace_id, user_id = await _workspace(session_factory)
        other_workspace, other_user = await _workspace(session_factory)
        batch_id = await _approved_batch(session_factory, workspace_id, user_id)

        response = await client.get(
            f"/workspaces/{other_workspace}/action-batches/{batch_id}",
            headers=_auth(key_pair, other_user),
        )

        assert response.status_code == 404, response.text

    async def test_a_stranger_is_refused_before_the_batch_is_looked_for(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """⚡ **Membership is verified server-side**, never taken from the path."""
        workspace_id, user_id = await _workspace(session_factory)
        batch_id = await _approved_batch(session_factory, workspace_id, user_id)

        response = await client.get(
            f"/workspaces/{workspace_id}/action-batches/{batch_id}",
            headers=_auth(key_pair, uuid4()),
        )

        assert response.status_code == 404, response.text


class TestTheProposerPortAConsumingDomainUses:
    """🔴 **[D-235](../../../docs/DECISION_REGISTER.md) ① made executable.**

    ⚡ **The helper above says *"there is no propose/approve endpoint yet
    (slice 6 brings the consumer that needs one)"*.** ✅ **Slice 6 is
    [TASK-466](../../../docs/BACKLOG.md) and this is that consumer's door** —
    `propose`, and nothing else.
    """

    async def test_a_consumer_can_propose_and_gets_the_id_back(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """⚡ **The id is why an event-based propose was refused** — 📁
        [C-1504](../../../docs/LANE_COORDINATION.md): *"the caller gets no
        `batch_id` back, so the confirmation cannot name what it created."*"""
        workspace_id, user_id = await _workspace(session_factory)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            batch_id = await build_action_batch_proposer(session).propose(
                workspace_id=workspace_id,
                name="Tag 8 companies",
                item_count=8,
                proposed_by=user_id,
                reversible_for=timedelta(hours=1),
            )

            view = await build_action_batches(session).current(workspace_id, batch_id)

        assert view is not None
        assert view.name == "Tag 8 companies"
        assert view.item_count == 8

    async def test_it_writes_on_the_caller_s_transaction(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """🔴 **Atomicity is the whole reason option ① was chosen over two
        endpoints.**

        ⛔ **A batch that exists with no payload is an approved action that
        applies nothing** — 📁 ADR-0405's *no partial state*.
        ⚡ **This proves the proposer joins the caller's
        transaction rather than opening its own**: rolling back leaves no
        batch, so a consumer whose payload write fails cannot strand one.
        """
        workspace_id, user_id = await _workspace(session_factory)

        async with session_factory() as session:
            await session.execute(text(f"SET LOCAL app.workspace_id = '{workspace_id}'"))
            batch_id = await build_action_batch_proposer(session).propose(
                workspace_id=workspace_id,
                name="Tag 8 companies",
                item_count=8,
                proposed_by=user_id,
            )
            await session.rollback()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            assert await build_action_batches(session).current(workspace_id, batch_id) is None

    async def test_proposing_publishes_nothing(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """⛔ **A proposal is a question, and no domain outside this one acts on
        a question** — the module's own words. ⚡ **So a consumer proposing does
        not wake a worker**, and nothing downstream can mistake an unapproved
        batch for work to do."""
        workspace_id, user_id = await _workspace(session_factory)
        before = len(await _outbox(admin_session_factory))

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            await build_action_batch_proposer(session).propose(
                workspace_id=workspace_id,
                name="Tag 8 companies",
                item_count=8,
                proposed_by=user_id,
            )

        assert len(await _outbox(admin_session_factory)) == before


class TestTheLifecycleAScreenCanDrive:
    """🔴 **The three routes a customer journey needs, and two were missing.**

    📁 [TASK-466](../../../docs/BACKLOG.md)'s own cell named it a cycle before
    it was closed: ⛔ *"there is no `propose`, `approve` or `reverse` route, so
    a screen cannot create a batch or take one back."*

    ⚡ **Building the first consumer proved it**: a proposed batch could not be
    approved, so it could never apply, so nothing could be reversed.
    """

    async def test_a_proposed_batch_can_be_approved(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id = await _workspace(session_factory)
        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            batch_id = await build_action_batch_proposer(session).propose(
                workspace_id=workspace_id,
                name="Tag 3 companies",
                item_count=3,
                proposed_by=user_id,
                reversible_for=timedelta(hours=24),
            )

        response = await client.post(
            f"/workspaces/{workspace_id}/action-batches/{batch_id}/approve",
            headers=_auth(key_pair, user_id),
        )

        assert response.status_code == 200, response.text
        assert response.json()["state"] == "approved"
        # ⛔ **Approved is not applied.** Two moments, and a screen that
        # rendered them alike would tell somebody the work had started.
        assert response.json()["applied_at"] is None

    async def test_approving_twice_is_refused_rather_than_repeated(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id = await _workspace(session_factory)
        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            batch_id = await build_action_batch_proposer(session).propose(
                workspace_id=workspace_id,
                name="Tag 3 companies",
                item_count=3,
                proposed_by=user_id,
            )
        await client.post(
            f"/workspaces/{workspace_id}/action-batches/{batch_id}/approve",
            headers=_auth(key_pair, user_id),
        )

        again = await client.post(
            f"/workspaces/{workspace_id}/action-batches/{batch_id}/approve",
            headers=_auth(key_pair, user_id),
        )

        assert again.status_code == 409, again.text

    async def test_a_batch_that_never_applied_cannot_be_reversed(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """⛔ **Nothing to take back.** ⚠️ *"Reversal was never offered"* and
        *"the window has closed"* are different refusals, and the domain
        answers rather than this handler."""
        workspace_id, user_id = await _workspace(session_factory)
        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            batch_id = await build_action_batch_proposer(session).propose(
                workspace_id=workspace_id,
                name="Tag 3 companies",
                item_count=3,
                proposed_by=user_id,
                reversible_for=timedelta(hours=24),
            )

        response = await client.post(
            f"/workspaces/{workspace_id}/action-batches/{batch_id}/reverse",
            headers=_auth(key_pair, user_id),
        )

        assert response.status_code == 409, response.text

    async def test_a_batch_in_another_workspace_is_not_found_rather_than_forbidden(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        # 📁 §7: *forbidden* confirms the id exists, which is a
        # workspace-enumeration oracle.
        workspace_id, user_id = await _workspace(session_factory)

        response = await client.post(
            f"/workspaces/{workspace_id}/action-batches/{uuid4()}/approve",
            headers=_auth(key_pair, user_id),
        )

        assert response.status_code == 404, response.text

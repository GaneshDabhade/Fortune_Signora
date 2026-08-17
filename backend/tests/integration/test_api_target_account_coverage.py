"""*"Is Signora still watching this company?"*, over the full stack — **A7**.

**The render slice for the column [`0035`](../../migrations/versions/0035_watermark_attempted_at.py)
added and nothing read.** Its own handoff said so: *"visual/UI regression: none
— nothing renders this."* This is the surface that does.

**Why this endpoint is Provider Platform's rather than a field on the target
account list.** The list belongs to Commercial Profile, and the dependency
matrix runs **Commercial Profile → Provider Platform** — so the module holding
the list may not read the module holding the attempts, and reversing the edge
would make the graph cyclic. **The frontend composes the two**, which is
[C-219](../../../docs/LANE_COORDINATION.md) option ③ as Lane C ratified it, and
the same arrangement `account-identities` already uses for names.

**The watermarks here are written by `RunProviderSync`, against the real
database, as a real sync.** No row is inserted directly: a watermark comes into
existence exactly one way, and a test that manufactured one would be asserting
against a state the product cannot reach (`CLAUDE.md` §20e).
"""

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.api.main import create_app
from modules.provider_platform.application.ports import NoPacer, NoSyncReporter
from modules.provider_platform.application.run_sync import RunProviderSyncInput
from modules.provider_platform.domain.provider import (
    ProviderCapability,
    ProviderDescriptor,
    ProviderName,
    ProviderRecord,
    ProviderRequest,
    ProviderResponse,
)
from modules.provider_platform.infrastructure.composition import build_run_sync
from modules.provider_platform.interface.tasks import SYSTEM_USER_ID
from signora_platform.db import tenant_scoped_session
from signora_platform.event_bus import PostgresOutboxEventPublisher
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


async def _coverage(
    client: AsyncClient,
    key_pair: KeyPair,
    user: UUID,
    workspace: UUID,
    *subjects: str,
) -> Any:
    return await client.get(
        f"/workspaces/{workspace}/target-account-coverage",
        params=[("subjects", subject) for subject in subjects],
        headers=_auth(key_pair, user),
    )


class StubAdapter:
    """One provider, one page — empty or not.

    Deliberately not the simulated adapter: this asserts what a *completed*
    read records, and the simulator's own scenario data would decide how many
    records that is.
    """

    def __init__(self, *, records: int, provider: ProviderName = ProviderName.APOLLO) -> None:
        self._records = records
        self._provider = provider

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            provider=self._provider,
            capabilities=frozenset({ProviderCapability.COMPANY_ENRICHMENT}),
            simulated=False,
        )

    async def fetch(self, request: ProviderRequest) -> ProviderResponse:
        return ProviderResponse(
            provider=self._provider,
            records=tuple(
                ProviderRecord(
                    provider=self._provider,
                    capability=ProviderCapability.COMPANY_ENRICHMENT,
                    external_id=f"{request.subject}-{index}",
                    occurred_at=datetime.now(UTC),
                    payload={"id": str(index)},
                )
                for index in range(self._records)
            ),
        )


async def _sync(
    sessions: async_sessionmaker[AsyncSession],
    workspace: UUID,
    subject: str,
    *,
    records: int,
    provider: ProviderName = ProviderName.APOLLO,
) -> None:
    """Run a real sync through the production composition.

    **`build_run_sync` and `tenant_scoped_session`, exactly as the ARQ task
    does it** — the real repository, the real outbox publisher, the real RLS
    scoping. A watermark comes into existence one way, and a test that
    inserted one directly would assert against a state the product cannot
    reach (§20e).

    The pacer is the one deliberate substitution: the real one waits out a
    provider's declared rate limit, and a test is the only caller that may ask
    it not to — which `build_run_sync`'s own signature already anticipates.
    """
    async with tenant_scoped_session(
        sessions, workspace_id=workspace, user_id=SYSTEM_USER_ID
    ) as session:
        await build_run_sync(
            session,
            adapter=StubAdapter(records=records, provider=provider),
            publisher=PostgresOutboxEventPublisher(),
            reporter=NoSyncReporter(),
            pacer=NoPacer(),
        ).execute(
            RunProviderSyncInput(
                workspace_id=workspace,
                capability=ProviderCapability.COMPANY_ENRICHMENT,
                subject=subject,
            ),
            correlation_id=uuid4(),
        )


class TestTheQuestionA4CouldNotAnswer:
    async def test_a_company_nobody_has_checked_says_so(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**Absence stated, never omitted.** The entry comes back with both
        fields empty rather than the subject vanishing from the response — a
        caller reading a missing key renders a blank, and a blank reads as a
        screen that forgot something rather than as an answer."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await _coverage(client, key_pair, user, workspace, "Northwind Health")

        assert response.status_code == 200, response.text
        assert response.json() == [
            {
                "subject": "Northwind Health",
                "last_attempt": None,
                "stored_anything": False,
            }
        ]

    async def test_a_company_checked_with_nothing_found_says_when(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Acceptance ①, and the whole reason the slice exists.** Before
        `attempted_at`, a completed read that stored nothing left no trace at
        all — the watermark's position only advances when records arrive."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        await _sync(session_factory, workspace, "Northwind Health", records=0)

        body = (await _coverage(client, key_pair, user, workspace, "Northwind Health")).json()

        assert body[0]["last_attempt"] is not None
        assert body[0]["stored_anything"] is False

    async def test_never_checked_is_distinguishable_from_checked_and_empty(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Acceptance ②, and it is asserted as the comparison.** These two
        were one state before this slice, and a seller reading the older
        screen could not tell *the account went quiet* from *the pipeline
        did* — which demand opposite actions."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        await _sync(session_factory, workspace, "Checked", records=0)

        never, checked = (
            await _coverage(client, key_pair, user, workspace, "Never", "Checked")
        ).json()

        assert never["last_attempt"] is None
        assert checked["last_attempt"] is not None
        assert never["stored_anything"] == checked["stored_anything"] is False

    async def test_a_company_checked_and_found_reports_both(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        await _sync(session_factory, workspace, "Northwind Health", records=3)

        body = (await _coverage(client, key_pair, user, workspace, "Northwind Health")).json()

        assert body[0]["last_attempt"] is not None
        assert body[0]["stored_anything"] is True


class TestOneAnswerAcrossEveryProvider:
    async def test_evidence_from_any_provider_counts(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """A subject carries one watermark per `(provider, capability)`, and
        the question a seller asks is *has anybody found anything* — not
        *did Apollo*."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        await _sync(session_factory, workspace, "Northwind Health", records=0)
        await _sync(
            session_factory,
            workspace,
            "Northwind Health",
            records=2,
            provider=ProviderName.BOMBORA,
        )

        body = (await _coverage(client, key_pair, user, workspace, "Northwind Health")).json()

        assert len(body) == 1
        assert body[0]["stored_anything"] is True


class TestTheRequestIsBounded:
    async def test_the_customers_own_order_is_returned(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        body = (await _coverage(client, key_pair, user, workspace, "Zeta", "Alpha", "Mu")).json()

        assert [entry["subject"] for entry in body] == ["Zeta", "Alpha", "Mu"]

    async def test_asking_about_nothing_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """A request naming no company is a caller mistake, not an empty
        answer — and refusing it is what stops the query being reached with a
        set that could only return nothing."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)

        response = await client.get(
            f"/workspaces/{workspace}/target-account-coverage",
            headers=_auth(key_pair, user),
        )

        assert response.status_code == 422, response.text


class TestItIsNotAWayToReadAnotherWorkspace:
    async def test_a_non_member_gets_404_rather_than_403(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """**404, never 403** (§7). A 403 would confirm the workspace exists,
        which is workspace enumeration — a security property rather than an
        inconsistency to tidy up."""
        owner = uuid4()
        workspace = await _workspace(client, key_pair, owner)

        response = await _coverage(client, key_pair, uuid4(), workspace, "Northwind Health")

        assert response.status_code == 404, response.text

    async def test_one_workspaces_attempts_never_appear_in_anothers(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The same company name in two workspaces is two companies.**
        `subject` is an unresolved string a customer typed, so two tenants
        naming the same firm is the ordinary case rather than the odd one —
        and it is exactly the case a missing `workspace_id` filter would leak.
        """
        watcher = uuid4()
        watched = await _workspace(client, key_pair, watcher)
        await _sync(session_factory, watched, "Northwind Health", records=3)

        stranger = uuid4()
        elsewhere = await _workspace(client, key_pair, stranger)
        body = (await _coverage(client, key_pair, stranger, elsewhere, "Northwind Health")).json()

        assert body == [
            {
                "subject": "Northwind Health",
                "last_attempt": None,
                "stored_anything": False,
            }
        ]

    async def test_an_unauthenticated_caller_is_refused(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        workspace = await _workspace(client, key_pair, uuid4())

        response = await client.get(
            f"/workspaces/{workspace}/target-account-coverage",
            params={"subjects": "Northwind Health"},
        )

        assert response.status_code == 401, response.text

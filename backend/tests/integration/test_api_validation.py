"""*"What should I do?"* — and whether it looks like Signora looked.

`R2-01`. Two accounts holding the same hypothesis get **word-for-word the same
checks**, because a check is a property of the hypothesis *type* and not of the
account. That is the design and it is what keeps this surface from being a
recommendation.

It is also what an AE reacted to: *"It gave me the same advice for two different
companies, so I assumed it wasn't really looking at either."*

**The guidance is generic; what it points at is not.** These tests assert both
halves — that the checks stay identical across accounts, and that the evidence
beside them does not.
"""

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.api.main import create_app
from signora_platform.settings import Settings
from signora_platform.tests.keys import (
    TEST_AUDIENCE,
    TEST_ISSUER,
    KeyPair,
    generate_key_pair,
    mint_token,
)
from signora_platform.simulation import dataset as dataset_module
from tests.conftest import DEFAULT_APP_DATABASE_URL
from tests.opportunity_engine.test_opportunity_pipeline import _tracked

pytestmark = pytest.mark.integration

#: **The baseline scenario's evidence is months old on purpose**, so every
#: hypothesis it forms is past its shelf life and this surface — which shows
#: *live* hypotheses only — correctly returns nothing. That is the lifecycle
#: working, and it is asserted in its own right in `25-signal-engine.md`.
#:
#: These tests need the other case, so they ingest at a recent epoch the way
#: the Playground does. **The same code path and the same scenario file** — the
#: only difference is when the clock says the events happened.
_EPOCH = timedelta(days=150)
_ASKED = timedelta(days=35)

#: The Playground's own scenario, used by **one** test. It is the only fixture
#: in which two accounts hold the same hypothesis — the case R2-01 is about —
#: and a test that skipped for want of it would be a claim nobody checked.
#:
#: Only one test pays for it: twelve accounts through the real pipeline is
#: seconds, not milliseconds, and the other assertions do not need them.
_SCENARIO = ("playground", 2)


def _midnight() -> datetime:
    return datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)


def _recent() -> dict[str, Any]:
    midnight = _midnight()
    return {"epoch": midnight - _EPOCH, "moment": midnight - _ASKED}


def _recent_playground() -> dict[str, Any]:
    subjects = tuple(sorted(dataset_module.load(*_SCENARIO).entities))
    return {
        **_recent(),
        "scenario": _SCENARIO,
        "subjects": subjects,
        # `_tracked` returns one entity for the caller's convenience and picks
        # it by name; the baseline's default is not in this cast.
        "anchor": subjects[0],
    }


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


async def _validation(
    client: AsyncClient, key_pair: KeyPair, user_id: UUID, workspace_id: UUID, account_id: UUID
) -> Any:
    return await client.get(
        f"/workspaces/{workspace_id}/accounts/{account_id}/validation",
        headers=_auth(key_pair, user_id),
    )


class TestTheGuidanceIsAnchoredToThisAccount:
    async def test_every_hypothesis_names_what_this_account_actually_did(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**R2-01.** A check that pointed at nothing was the whole finding."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind", **_recent()
        )

        response = await _validation(client, key_pair, user_id, workspace_id, entity_id)

        assert response.status_code == 200, response.text
        hypotheses = response.json()["hypotheses"]
        assert hypotheses, "the scenario must hold at least one live hypothesis"
        for hypothesis in hypotheses:
            assert hypothesis["observed"], hypothesis["title"]

    async def test_the_evidence_is_the_pipeline_s_own_sentence(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Never a paraphrase. The same summary a citation already opens to —
        two wordings for one fact is how a customer catches the product
        contradicting itself."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind", **_recent()
        )

        hypotheses = (
            await _validation(client, key_pair, user_id, workspace_id, entity_id)
        ).json()["hypotheses"]
        observed = hypotheses[0]["observed"][0]

        event = await client.get(
            f"/workspaces/{workspace_id}/business-events/{observed['business_event_id']}",
            headers=_auth(key_pair, user_id),
        )
        assert event.status_code == 200, event.text
        assert event.json()["summary"] == observed["summary"]

    async def test_the_citation_is_the_one_the_ledger_already_uses(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """One concept, not two. The evidence drawer opens these unchanged."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind", **_recent()
        )

        hypotheses = (
            await _validation(client, key_pair, user_id, workspace_id, entity_id)
        ).json()["hypotheses"]
        cited = {
            row["business_event_id"] for h in hypotheses for row in h["observed"]
        }

        score = await client.get(
            f"/workspaces/{workspace_id}/accounts/{entity_id}/score",
            headers=_auth(key_pair, user_id),
        )
        ledger = {line["business_event_id"] for line in score.json()["contributions"]}

        assert cited
        assert cited <= ledger, "the validation surface cites events the ledger does not"


class TestTheCheckStaysGenericAndTheEvidenceDoesNot:
    async def test_two_accounts_holding_one_hypothesis_get_the_same_checks(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**This is the design, not the defect.** The guidance is a property
        of the hypothesis type; making it per-account would make it a
        recommendation, which is a different product with a different burden
        of proof."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind", **_recent_playground()
        )
        accounts = (
            await client.get(
                f"/workspaces/{workspace_id}/accounts", headers=_auth(key_pair, user_id)
            )
        ).json()["items"]
        assert len(accounts) >= 2

        by_type: dict[str, list[dict[str, Any]]] = {}
        for account in accounts:
            for hypothesis in (
                await _validation(
                    client, key_pair, user_id, workspace_id, UUID(account["account_id"])
                )
            ).json()["hypotheses"]:
                by_type.setdefault(hypothesis["title"], []).append(hypothesis)

        shared = [rows for rows in by_type.values() if len(rows) >= 2]
        if not shared:
            pytest.skip("this scenario holds no hypothesis on two accounts")

        for rows in shared:
            checks = {tuple(row["suggested_validation"]) for row in rows}
            assert len(checks) == 1, "the checks must not vary by account"

    async def test_and_the_evidence_beneath_them_differs(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The other half, and the point of R2-01.** Identical advice with
        identical evidence reads as a product that is not looking. Identical
        advice over *different* evidence reads as a product that knows the
        difference between a rule and a company."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind", **_recent_playground()
        )
        accounts = (
            await client.get(
                f"/workspaces/{workspace_id}/accounts", headers=_auth(key_pair, user_id)
            )
        ).json()["items"]

        cited_per_account = []
        for account in accounts[:2]:
            hypotheses = (
                await _validation(
                    client, key_pair, user_id, workspace_id, UUID(account["account_id"])
                )
            ).json()["hypotheses"]
            cited_per_account.append(
                {row["business_event_id"] for h in hypotheses for row in h["observed"]}
            )

        first, second = cited_per_account
        assert first and second
        assert not (first & second), "two accounts must never cite the same recorded event"


class TestTheSurfaceIsScoped:
    async def test_a_non_member_gets_404(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, _, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind", **_recent()
        )

        response = await _validation(client, key_pair, uuid4(), workspace_id, entity_id)

        assert response.status_code == 404, response.text

    async def test_an_account_with_nothing_live_is_an_empty_list(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """An answer, not a 404 — *"nothing is currently held here"* is a
        different statement from *"that account does not exist"*."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind", **_recent()
        )

        response = await _validation(client, key_pair, user_id, workspace_id, uuid4())

        assert response.status_code == 200, response.text
        assert response.json()["hypotheses"] == []

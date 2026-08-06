"""*"Is our ideal customer description any good?"* — over the full stack.

**Every figure comes from accounts moved through the product's own endpoints**,
and the ICP from the customer's own `PUT /icp`. Nothing is seeded by a private
door, which is what makes the measurement a statement about the product rather
than about a fixture.
"""

from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID

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
from tests.conftest import DEFAULT_APP_DATABASE_URL
from tests.opportunity_engine.test_opportunity_pipeline import _tracked

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
    async with app.router.lifespan_context(app), AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as http:
        yield http


def _auth(key_pair: KeyPair, user_id: UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {mint_token(key_pair, user_id=user_id)}"}


async def _performance(
    client: AsyncClient, key_pair: KeyPair, user_id: UUID, workspace_id: UUID
) -> Any:
    return await client.get(
        f"/workspaces/{workspace_id}/icp-performance", headers=_auth(key_pair, user_id)
    )


class TestAWorkspaceWithNoDeclarationIsNotAnError:
    async def test_no_icp_returns_an_empty_list(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**A state to wait in, not zeroes and not a 404.** A customer who has
        not described who buys from them has nothing to be measured against."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        response = await _performance(client, key_pair, user_id, workspace_id)

        assert response.status_code == 200, response.text
        assert response.json() == []


class TestOneWorkspaceNeverMeasuresAnother:
    async def test_a_non_member_is_told_it_does_not_exist(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**404, never 403** — a 403 confirms the workspace exists."""
        workspace_id, _, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        _, stranger, _, _ = await _tracked(
            session_factory, admin_session_factory, "contoso"
        )

        response = await _performance(client, key_pair, stranger, workspace_id)

        assert response.status_code == 404, response.text

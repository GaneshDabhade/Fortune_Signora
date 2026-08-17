"""The published ICP read, exercised through the door a customer uses.

[TASK-434](../../../docs/BACKLOG.md) slice ①. **Thirteen views were published
before this one and not one was the ICP**, so no module could read the
criteria at all — which is how sixteen consumers came to be waiting on a
capability nobody could build.

**Declared through `PUT /icp` and read back through the port**, never by
inserting a row: data that arrives by a private door proves the door
(`CLAUDE.md` §20e).
"""

from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.api.main import create_app
from modules.commercial_profile.infrastructure.icp_reader import SqlIcpReader
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


@pytest.fixture
async def sessions() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(DEFAULT_APP_DATABASE_URL)
    try:
        yield async_sessionmaker(engine, expire_on_commit=False)
    finally:
        await engine.dispose()


def _auth(key_pair: KeyPair, user_id: UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {mint_token(key_pair, user_id=user_id)}"}


async def _workspace(client: AsyncClient, key_pair: KeyPair, user_id: UUID) -> UUID:
    response = await client.post(
        "/workspaces", json={"name": "Acme", "slug": _test_slug("Acme")}, headers=_auth(key_pair, user_id)
    )
    assert response.status_code == 201, response.text
    return UUID(response.json()["id"])


async def _sell(client: AsyncClient, key_pair: KeyPair, user: UUID, workspace: UUID) -> UUID:
    product_id = uuid4()
    response = await client.put(
        f"/workspaces/{workspace}/products",
        json={
            "expected_version": 0,
            "products": [{"id": str(product_id), "name": "Revenue Cloud", "description": ""}],
        },
        headers=_auth(key_pair, user),
    )
    assert response.status_code == 200, response.text
    return product_id


async def _read_icp(
    sessions: async_sessionmaker[AsyncSession], workspace: UUID
) -> object:
    """Read through the port, under the workspace's own RLS context.

    **`SET LOCAL`, never `SET`** — the scope is the transaction, which is what
    stops a pooled connection carrying one workspace's context into the next
    request (`CLAUDE.md` §8).
    """
    async with sessions() as session:
        await session.execute(text(f"SET LOCAL app.workspace_id = '{workspace}'"))
        return await SqlIcpReader(session).current(workspace)


class TestTheIcpIsReadableByAnotherModule:
    async def test_a_workspace_that_has_never_declared_one_reads_none(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        sessions: async_sessionmaker[AsyncSession],
    ) -> None:
        """**`None`, not an empty view.** *"They have not told us"* is a state
        to wait in; an account evaluated against no criteria would come back
        `UNMEASURED` three times, which is true and useless."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        assert await _read_icp(sessions, workspace) is None

    async def test_what_the_customer_typed_is_what_another_module_reads(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        sessions: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Free text crosses the boundary unchanged.** Normalising here
        would put a second vocabulary in the module whose job is recording the
        first."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        product = await _sell(client, key_pair, user, workspace)

        response = await client.put(
            f"/workspaces/{workspace}/icp",
            json={
                "expected_version": 0,
                "profiles": [
                    {
                        "product_id": str(product),
                        "industries": ["Mid-market Fintech"],
                        "countries": ["United Kingdom"],
                        "employees": {"minimum": 100, "maximum": 1000},
                    }
                ],
            },
            headers=_auth(key_pair, user),
        )
        assert response.status_code == 200, response.text

        view = await _read_icp(sessions, workspace)
        assert view is not None
        assert view.version == 1  # type: ignore[attr-defined]
        criteria = view.criteria[0]  # type: ignore[attr-defined]
        assert criteria.industries == ("Mid-market Fintech",)
        assert criteria.countries == ("United Kingdom",)
        assert criteria.employees_minimum == 100
        assert criteria.employees_maximum == 1000

    async def test_an_unstated_bound_reads_as_absent_rather_than_zero(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        sessions: async_sessionmaker[AsyncSession],
    ) -> None:
        """**`None` is not `0`.** *"Anything over 500"* has no upper bound;
        reading one as zero would match nothing and look deliberate."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        product = await _sell(client, key_pair, user, workspace)

        await client.put(
            f"/workspaces/{workspace}/icp",
            json={
                "expected_version": 0,
                "profiles": [
                    {"product_id": str(product), "employees": {"minimum": 500}}
                ],
            },
            headers=_auth(key_pair, user),
        )

        view = await _read_icp(sessions, workspace)
        assert view is not None
        criteria = view.criteria[0]  # type: ignore[attr-defined]
        assert criteria.employees_minimum == 500
        assert criteria.employees_maximum is None

    async def test_a_criterion_the_customer_left_out_reads_as_empty(
        self,
        client: AsyncClient,
        key_pair: KeyPair,
        sessions: async_sessionmaker[AsyncSession],
    ) -> None:
        """An undeclared criterion is an empty tuple here and becomes
        `UNMEASURED` in `evaluate` — never a criterion everything passes."""
        user = uuid4()
        workspace = await _workspace(client, key_pair, user)
        product = await _sell(client, key_pair, user, workspace)

        await client.put(
            f"/workspaces/{workspace}/icp",
            json={
                "expected_version": 0,
                "profiles": [{"product_id": str(product), "industries": ["Fintech"]}],
            },
            headers=_auth(key_pair, user),
        )

        view = await _read_icp(sessions, workspace)
        assert view is not None
        criteria = view.criteria[0]  # type: ignore[attr-defined]
        assert criteria.countries == ()
        assert criteria.employees_minimum is None

"""Integration tests for the API's operational endpoints."""

import os

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import create_app
from signora_platform.settings import Settings
from signora_platform.tests.keys import TEST_AUDIENCE, TEST_ISSUER, generate_key_pair

pytestmark = pytest.mark.integration

ADMIN_URL = os.environ.get(
    "SIGNORA_TEST_ADMIN_DATABASE_URL",
    "postgresql+asyncpg://signora:signora@localhost:5432/signora",
)


# Operational probes are unauthenticated, but Settings still requires JWT
# configuration — the app must not be constructible without it.
_KEY_PAIR = generate_key_pair()


def _settings(database_url: str) -> Settings:
    return Settings(
        environment="test",
        database_url=database_url,
        jwt_public_key=_KEY_PAIR.public_pem,
        jwt_issuer=TEST_ISSUER,
        jwt_audience=TEST_AUDIENCE,
    )


async def test_health_reports_ok_without_touching_the_database() -> None:
    """Liveness must not depend on the database — pointed at an
    unreachable database it should still report ok."""
    app = create_app(_settings("postgresql+asyncpg://nobody@127.0.0.1:1/nonexistent"))

    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "environment": "test"}


async def test_ready_reports_ready_when_database_is_reachable() -> None:
    app = create_app(_settings(ADMIN_URL))

    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/ready")

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "ready"
    assert body["database"] == "ok"
    assert body["authentication"] == "ok"


async def test_ready_reports_degraded_when_database_is_unreachable() -> None:
    app = create_app(_settings("postgresql+asyncpg://nobody@127.0.0.1:1/nonexistent"))

    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/ready")

    body = response.json()
    # 503, not 200. Orchestrators route on the status code and never read
    # the body, so a degraded API answering 200 keeps receiving traffic it
    # cannot serve.
    assert response.status_code == 503
    assert body["status"] == "degraded"
    assert body["database"] == "unavailable"


async def test_openapi_schema_is_generated() -> None:
    app = create_app(_settings(ADMIN_URL))

    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/openapi.json")

    schema = response.json()
    assert response.status_code == 200
    assert schema["info"]["title"] == "Signora API"
    assert "/health" in schema["paths"]


class TestAuthenticationReadiness:
    """Readiness must cover the authentication subsystem, not only the
    database. An API that cannot verify a token is not ready — every
    authenticated request would 401, which a user cannot distinguish from
    an outage."""

    async def test_reports_authentication_ok_with_valid_configuration(self) -> None:
        app = create_app(_settings(ADMIN_URL))

        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                body = (await client.get("/ready")).json()

        assert body["authentication"] == "ok"
        assert body["authentication_detail"] is None

    async def test_private_key_in_api_configuration_makes_it_not_ready(self) -> None:
        """The most serious misconfiguration this tier can have: a private
        key here would make the API able to mint tokens it accepts, which is
        exactly what asymmetric signing was chosen to prevent (ADR-0026)."""
        private_pem = "-----BEGIN PRIVATE KEY-----\nMIIBVAIBADANBg\n-----END PRIVATE KEY-----\n"
        settings = Settings(
            environment="test",
            database_url=ADMIN_URL,
            jwt_public_key=private_pem,
            jwt_issuer=TEST_ISSUER,
            jwt_audience=TEST_AUDIENCE,
        )
        app = create_app(settings)

        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/ready")

        body = response.json()
        assert body["status"] == "degraded"
        assert body["authentication"] == "unavailable"
        assert "PRIVATE key" in body["authentication_detail"]

    async def test_malformed_public_key_makes_it_not_ready(self) -> None:
        settings = Settings(
            environment="test",
            database_url=ADMIN_URL,
            jwt_public_key="not-a-pem",
            jwt_issuer=TEST_ISSUER,
            jwt_audience=TEST_AUDIENCE,
        )
        app = create_app(settings)

        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                body = (await client.get("/ready")).json()

        assert body["authentication"] == "unavailable"

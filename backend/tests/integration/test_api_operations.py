"""Integration tests for the API's operational endpoints."""

import os

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import create_app
from signora_platform.settings import Settings

pytestmark = pytest.mark.integration

ADMIN_URL = os.environ.get(
    "SIGNORA_TEST_ADMIN_DATABASE_URL",
    "postgresql+asyncpg://signora:signora@localhost:5432/signora",
)


def _settings(database_url: str) -> Settings:
    return Settings(environment="test", database_url=database_url)


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

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "ok"}


async def test_ready_reports_degraded_when_database_is_unreachable() -> None:
    app = create_app(_settings("postgresql+asyncpg://nobody@127.0.0.1:1/nonexistent"))

    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "degraded", "database": "unavailable"}


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

"""FastAPI application entry point.

Currently exposes only operational endpoints. Business routes are added per
module as each module's interface layer is built; the workspace_tenancy
routes specifically are blocked on resolving how Better Auth (a TypeScript
library, ADR-0010) issues sessions this Python API can verify — see
docs/architecture/16-architecture-risks.md.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from signora_platform.db import create_engine
from signora_platform.settings import Settings, get_settings


class HealthResponse(BaseModel):
    status: Literal["ok"]
    environment: str


class ReadinessResponse(BaseModel):
    status: Literal["ready", "degraded"]
    database: Literal["ok", "unavailable"]


def create_app(settings: Settings | None = None) -> FastAPI:
    """Application factory. Takes settings explicitly so tests can build an
    app without depending on process environment.
    """
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_engine(resolved_settings)
        app.state.engine = engine
        try:
            yield
        finally:
            await engine.dispose()

    app = FastAPI(
        title="Signora API",
        version="0.1.0",
        summary="AI Revenue Intelligence Platform",
        lifespan=lifespan,
    )

    @app.get("/health", response_model=HealthResponse, tags=["operations"])
    async def health() -> HealthResponse:
        """Liveness probe: the process is running. Deliberately does not
        touch the database — a liveness check that fails on a transient
        database blip causes orchestrators to restart healthy processes."""
        return HealthResponse(status="ok", environment=resolved_settings.environment)

    @app.get("/ready", response_model=ReadinessResponse, tags=["operations"])
    async def ready() -> ReadinessResponse:
        """Readiness probe: the process can serve traffic, which requires a
        reachable database."""
        engine: AsyncEngine = app.state.engine
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception:
            return ReadinessResponse(status="degraded", database="unavailable")
        return ReadinessResponse(status="ready", database="ok")

    return app

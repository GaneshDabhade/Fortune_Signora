"""FastAPI application entry point and composition root.

This is the only place permitted to know about both ``signora_platform`` and
``modules``. Dependency inversion happens here: the platform layer declares
the ports it needs (notably ``MembershipVerifier``) and this module supplies
Workspace & Tenancy's concrete implementation, so the platform never imports
a module (15-project-structure.md).
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, Response, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from modules.opportunity_engine.interface.router import router as opportunity_router
from modules.workspace_tenancy.infrastructure.composition import build_query_service
from modules.workspace_tenancy.interface.errors import (
    ERROR_MAPPING as WORKSPACE_TENANCY_ERRORS,
)
from modules.workspace_tenancy.interface.router import router as workspace_tenancy_router
from signora_platform.api import (
    ApiDependencies,
    ErrorMapping,
    MembershipVerifier,
    WorkspaceAccessDeniedError,
    register_exception_handlers,
)
from signora_platform.auth import JwtVerifier, check_auth_health
from signora_platform.authorization import CasbinAuthorizer
from signora_platform.db import create_engine, create_session_factory
from signora_platform.observability import (
    configure_error_tracking,
    configure_logging,
    configure_tracing,
    instrument_fastapi,
    instrument_sqlalchemy,
)
from signora_platform.pagination import InvalidCursorError
from signora_platform.settings import Settings, get_settings


class HealthResponse(BaseModel):
    status: Literal["ok"]
    environment: str


class ReadinessResponse(BaseModel):
    status: Literal["ready", "degraded"]
    database: Literal["ok", "unavailable"]
    authentication: Literal["ok", "degraded", "unavailable"]
    authentication_detail: str | None = None


def _membership_verifier(session: AsyncSession) -> MembershipVerifier:
    """Adapts Workspace & Tenancy's query service to the platform's port."""
    return build_query_service(session)


def _error_mappings() -> ErrorMapping:
    """Domain-error-to-HTTP mappings from the platform and every module.

    Platform-level errors are listed first; each module contributes its own.
    Adding a module means adding one entry here, not editing the handler.
    """
    mappings: dict[type[Exception], tuple[int, str]] = {
        # A caller who is not a member gets 404, deliberately identical to
        # "no such workspace" (18-authentication.md).
        WorkspaceAccessDeniedError: (404, "workspace_not_found"),
        InvalidCursorError: (400, "invalid_cursor"),
    }
    mappings.update(WORKSPACE_TENANCY_ERRORS)
    return mappings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Application factory. Takes settings explicitly so tests can build an
    app without depending on process environment."""
    resolved_settings = settings or get_settings()

    # Observability is configured before anything else so that failures
    # during the rest of startup are themselves logged and reported.
    configure_logging(level=resolved_settings.log_level)
    configure_tracing(resolved_settings)
    configure_error_tracking(resolved_settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_engine(resolved_settings)
        instrument_sqlalchemy(engine)
        app.state.engine = engine
        app.state.api_dependencies = ApiDependencies(
            jwt_verifier=JwtVerifier(
                public_key=resolved_settings.jwt_public_key,
                issuer=resolved_settings.jwt_issuer,
                audience=resolved_settings.jwt_audience,
            ),
            session_factory=create_session_factory(engine),
            # Constructed once: policy is read-only at runtime, so the
            # enforcer is safe to share across requests.
            authorizer=CasbinAuthorizer(),
            membership_verifier_factory=_membership_verifier,
        )
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

    instrument_fastapi(app)
    register_exception_handlers(app, domain_errors=_error_mappings())
    app.include_router(workspace_tenancy_router)
    app.include_router(opportunity_router)

    @app.get("/health", response_model=HealthResponse, tags=["operations"])
    async def health() -> HealthResponse:
        """Liveness probe: the process is running. Deliberately does not
        touch the database — a liveness check that fails on a transient
        database blip causes orchestrators to restart healthy processes."""
        return HealthResponse(status="ok", environment=resolved_settings.environment)

    @app.get(
        "/ready",
        response_model=ReadinessResponse,
        tags=["operations"],
        responses={503: {"model": ReadinessResponse, "description": "Not ready to serve"}},
    )
    async def ready(response: Response) -> ReadinessResponse:
        """Readiness probe: the process can serve traffic.

        Covers both the database and the authentication subsystem. An API
        that cannot verify a token is not ready, even with a healthy
        database — every authenticated request would 401, which is
        indistinguishable from an outage to a user.

        **Not ready is a 503, not a 200 with bad news in the body.** Every
        orchestrator that will run this — Docker healthchecks, ECS target
        groups, Kubernetes readiness probes — routes on the status code and
        never reads the body. A degraded API returning 200 keeps receiving
        traffic it cannot serve. The body remains for humans and for
        debugging; the status code is what the infrastructure acts on.
        """
        engine: AsyncEngine = app.state.engine
        database: Literal["ok", "unavailable"] = "ok"
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception:
            database = "unavailable"

        auth_health = check_auth_health(resolved_settings)
        ready_to_serve = database == "ok" and auth_health.status != "unavailable"
        if not ready_to_serve:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        return ReadinessResponse(
            status="ready" if ready_to_serve else "degraded",
            database=database,
            authentication=auth_health.status,
            authentication_detail=auth_health.detail,
        )

    return app

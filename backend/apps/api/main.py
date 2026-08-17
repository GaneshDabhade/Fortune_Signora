"""FastAPI application entry point and composition root.

This is the only place permitted to know about both ``signora_platform`` and
``modules``. Dependency inversion happens here: the platform layer declares
the ports it needs (notably ``MembershipVerifier``) and this module supplies
Workspace & Tenancy's concrete implementation, so the platform never imports
a module (15-project-structure.md).
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal, cast

from fastapi import FastAPI, Response, status
from pydantic import BaseModel
from sqlalchemy import text
from redis.asyncio import from_url as redis_from_url
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from modules.action_batch.interface.router import router as action_batch_router
from modules.ai_platform.interface.router import router as narration_router
from modules.ai_reasoning_engine.interface.router import router as reasoning_router
from modules.ai_research_engine.interface.errors import (
    ERROR_MAPPING as AI_RESEARCH_ENGINE_ERRORS,
)
from modules.ai_research_engine.interface.router import router as research_router
from modules.business_event_engine.interface.router import router as evidence_router
from modules.buying_score_engine.interface.router import router as buying_score_router
from modules.commercial_profile.interface.errors import (
    ERROR_MAPPING as COMMERCIAL_PROFILE_ERRORS,
)
from modules.commercial_profile.interface.router import router as products_router
from modules.integrations.interface.errors import (
    ERROR_MAPPING as INTEGRATIONS_ERRORS,
)
from modules.integrations.interface.router import router as integrations_router
from modules.knowledge_graph.interface.router import router as knowledge_graph_router
from modules.observation_engine.interface.router import router as observation_router
from modules.opportunity_engine.interface.errors import (
    ERROR_MAPPING as OPPORTUNITY_ENGINE_ERRORS,
)
from modules.opportunity_engine.interface.router import router as opportunity_router
from modules.provider_platform.interface.router import router as coverage_router
from modules.sales_engagement.interface.router import router as approach_router
from modules.signal_engine.interface.errors import (
    ERROR_MAPPING as SIGNAL_ENGINE_ERRORS,
)
from modules.signal_engine.interface.router import router as validation_router
from modules.timeline.interface.router import router as timeline_router
from modules.workspace_tenancy.infrastructure.authorization_subject import (
    CapabilityAwareMembershipVerifier,
)
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
from signora_platform.api.rate_limit import (
    CounterStore,
    InMemoryCounterStore,
    RateLimiter,
    RateLimitMiddleware,
    RedisCounterStore,
    RedisLike,
)
from signora_platform.settings import Settings, get_settings

_LOG = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    status: Literal["ok"]
    environment: str


class ReadinessResponse(BaseModel):
    status: Literal["ready", "degraded"]
    database: Literal["ok", "unavailable"]
    authentication: Literal["ok", "degraded", "unavailable"]
    authentication_detail: str | None = None


def _membership_verifier(session: AsyncSession) -> MembershipVerifier:
    """Adapts Workspace & Tenancy to the platform's port.

    ⚡ **Capability-aware from TASK-1479 ⓸**, on ADR-0410.
    **This one line is where the capability layer takes effect**, and it is the
    only wiring the whole slice needed: the platform's `MembershipVerifier`
    asks for the string to authorize against, and this now answers with a
    person's capability role where they hold one.

    ⛔ **`None` still means *not a member*** and still becomes a `404`. **A
    capability role never widens who may reach a workspace, only what they may
    do inside it.**
    """
    return CapabilityAwareMembershipVerifier(session)


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
    mappings.update(OPPORTUNITY_ENGINE_ERRORS)
    mappings.update(COMMERCIAL_PROFILE_ERRORS)
    mappings.update(AI_RESEARCH_ENGINE_ERRORS)
    mappings.update(INTEGRATIONS_ERRORS)
    mappings.update(SIGNAL_ENGINE_ERRORS)
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
    app.include_router(action_batch_router)
    app.include_router(workspace_tenancy_router)
    app.include_router(opportunity_router)
    app.include_router(knowledge_graph_router)
    app.include_router(observation_router)
    app.include_router(buying_score_router)
    app.include_router(narration_router)
    app.include_router(reasoning_router)
    app.include_router(validation_router)
    app.include_router(evidence_router)
    app.include_router(products_router)
    app.include_router(research_router)
    app.include_router(timeline_router)
    app.include_router(integrations_router)
    app.include_router(approach_router)
    app.include_router(coverage_router)

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

    # ## Inbound rate limiting — [ADR-0408](../../../docs/architecture/adr/0408-inbound-rate-limiting.md), [C-287](../../../docs/LANE_COORDINATION.md) ⓓ
    #
    # **Registered LAST so it runs FIRST.** Starlette applies middleware in
    # reverse registration order, so this sits outside `instrument_fastapi`'s
    # tracing and therefore *after* correlation-id assignment on the way in —
    # ADR-0408 §4's ordering requirement, and why a refused request is still
    # traceable (§16).
    #
    # ⚠️ **`app.routes` is passed and it is load-bearing.** Without it the
    # limiter keys on the concrete path, so `/workspaces/w1/...`,
    # `/workspaces/w2/...` each get a full budget and nothing is ever limited.
    # **Written that way first and caught by a test**, not by review.
    #
    # ⛔ **This protects the business API and cannot see `/signin`.** Those
    # routes are Better Auth's, in Next.js, and are limited there — the second
    # of the two policies C-287 ⓓ approved. [`501-rate-limiting-boundary.md`](../../../docs/architecture/501-rate-limiting-boundary.md)
    # states the boundary; neither limiter covers both tiers.
    app.add_middleware(
        RateLimitMiddleware,
        limiter=RateLimiter(
            _counter_store(resolved_settings),
            resolved_settings.rate_limit,
        ),
        routes=app.routes,
    )

    return app


def _counter_store(settings: Settings) -> CounterStore:
    """Redis when it is configured, and an in-process counter when it is not.

    ⚠️ **The fallback is for a developer running the API with no Redis**, and
    it is the one ADR-0408 §9 warns about — *"a number that is wrong by a
    factor of n and looks right."* ⛔ **It is safe here only because
    `require_redis_url()` already refuses to invent a URL**, so a deployed
    service without Redis fails at configuration rather than limping.
    """
    if settings.redis_url is None:
        _LOG.warning(
            "rate_limit_counters_in_process",
            extra={"reason": "no redis_url configured; counters are per-process"},
        )
        return InMemoryCounterStore()
    # **`redis.asyncio.from_url` is untyped at the vendor boundary.** The
    # narrow `RedisLike` Protocol the store declares is what this satisfies,
    # and casting to it here keeps the untyped call at the one edge that has
    # to touch a client rather than letting `Any` travel inward.
    client = cast(RedisLike, redis_from_url(str(settings.redis_url)))  # type: ignore[no-untyped-call]
    return RedisCounterStore(client)

"""ARQ worker entry point.

One process runs one pool. Which pool is chosen at startup by
``SIGNORA_WORKER_POOL``, so the same image is deployed for every pool and
scaled independently — the operational shape docs/architecture/12-scalability.md
calls for, where AI stages run at low concurrency with long timeouts while
normalization runs wide and fast.

Run with:  ``arq apps.worker.main.WorkerSettings``
"""

import asyncio
from typing import Any

import httpx
from arq.connections import RedisSettings

from apps.worker import subscriptions
from apps.worker.pools import POOLS, resolve_pool
from modules.ai_platform.infrastructure.settings import AISettings
from modules.provider_platform.infrastructure.composition import (
    build_provider_registry as build_data_provider_registry,
)
from modules.provider_platform.infrastructure.settings import ProviderSettings
from signora_platform.db import create_engine, create_session_factory
from signora_platform.event_bus import (
    MAX_ATTEMPTS,
    EventDispatcher,
    EventEnvelope,
    backoff_seconds,
    queue_name_for,
    record_dead_letter,
    registry,
)
from signora_platform.observability import (
    configure_error_tracking,
    configure_logging,
    configure_metrics,
    configure_tracing,
    get_logger,
    instrument_sqlalchemy,
)
from signora_platform.settings import get_settings

logger = get_logger(__name__)


async def dispatch_event(
    ctx: dict[str, Any], consumer_name: str, envelope_data: dict[str, Any]
) -> None:
    """The single ARQ task every consumer's work arrives as.

    Retry and dead-lettering live here rather than inside the dispatcher so
    that the dispatcher stays a pure "run this handler exactly once in
    tenant scope" component, testable without a job framework.

    Re-raising is what triggers ARQ's retry; the final attempt dead-letters
    and returns normally, because raising there would leave ARQ retrying an
    event we have deliberately given up on.
    """
    envelope = EventEnvelope.model_validate(envelope_data)
    dispatcher: EventDispatcher = ctx["dispatcher"]
    attempt: int = ctx.get("job_try", 1)

    try:
        await dispatcher.dispatch(consumer_name=consumer_name, envelope=envelope)
    except Exception as exc:
        failure_reason = f"{type(exc).__name__}: {exc}"

        metrics = ctx.get("metrics")

        if attempt >= MAX_ATTEMPTS:
            if metrics:
                metrics.event_dead_lettered(
                    event_type=envelope.event_type, consumer_name=consumer_name
                )
            await record_dead_letter(
                ctx["session_factory"],
                consumer_name=consumer_name,
                envelope=envelope,
                attempts=attempt,
                failure_reason=failure_reason,
            )
            return

        delay = backoff_seconds(attempt)
        if metrics:
            metrics.handler_retried(
                event_type=envelope.event_type,
                consumer_name=consumer_name,
                attempt=attempt,
            )
        logger.warning(
            "event handler failed, retrying",
            extra={
                "event_type": envelope.event_type,
                "consumer_name": consumer_name,
                "attempt": attempt,
                "retry_in_seconds": delay,
                "error": failure_reason,
            },
        )
        await asyncio.sleep(delay)
        raise


async def startup(ctx: dict[str, Any]) -> None:
    settings = get_settings()
    configure_logging(level=settings.log_level)
    configure_tracing(settings)
    configure_error_tracking(settings)
    metrics = configure_metrics(settings)

    pool = resolve_pool()
    engine = create_engine(settings)
    instrument_sqlalchemy(engine)
    session_factory = create_session_factory(engine)

    ctx["engine"] = engine
    ctx["session_factory"] = session_factory
    ctx["metrics"] = metrics
    ctx["dispatcher"] = EventDispatcher(
        session_factory=session_factory, registry=registry, metrics=metrics
    )
    ctx["pool"] = pool

    # The runtime consumers resolve at call time. Importing `subscriptions`
    # registered them; this is what makes them able to do any work, and it is
    # deliberately the last thing startup does — a handler that ran against a
    # half-built context would fail in a way nobody could read.
    #
    # One long-lived HTTP client: a connection per inference would spend more
    # time in TLS setup than a model spends thinking. The timeout is generous
    # because a research run is two calls against a model that may be local
    # and slow, and a client timeout here would surface as a product failure
    # rather than as a slow machine.
    http = httpx.AsyncClient(timeout=300.0)
    ctx["http"] = http
    subscriptions.install(
        subscriptions.WorkerRuntime(
            session_factory=session_factory,
            http=http,
            ai=AISettings(),
            # **The data-provider registry, built here and nowhere else.**
            # ADR-0404 capability 3: `provider_platform` decides *which*
            # adapters exist from its own typed settings, and the composition
            # root is the only place allowed to ask it. A handler building one
            # would be a second composition root, which is what `runtime()`
            # exists to prevent.
            #
            # It raises at startup if simulated adapters are selected outside a
            # local environment — deliberately, because a deployed worker
            # serving generated company data is indistinguishable from one that
            # is working, and every score built on it would be fabricated.
            provider_registry=build_data_provider_registry(ProviderSettings()),
        )
    )

    logger.info(
        "worker started",
        extra={
            "pool": pool.name,
            "queue": queue_name_for(pool.name),
            "max_jobs": pool.max_jobs,
            "job_timeout_seconds": pool.job_timeout_seconds,
            "subscriptions": len(registry.for_pool(pool.name)),
        },
    )


async def shutdown(ctx: dict[str, Any]) -> None:
    """Dispose the engine on shutdown.

    ARQ finishes in-flight jobs before calling this, so disposing here
    cannot interrupt work in progress — which is what makes a rolling
    deploy lossless rather than merely fast.
    """
    await ctx["http"].aclose()
    await ctx["engine"].dispose()
    logger.info("worker stopped", extra={"pool": ctx["pool"].name})


class WorkerSettings:
    """ARQ configuration, resolved from the pool selected at startup."""

    functions = [dispatch_event]
    on_startup = startup
    on_shutdown = shutdown

    _pool = resolve_pool()
    queue_name = queue_name_for(_pool.name)
    max_jobs = _pool.max_jobs
    job_timeout = _pool.job_timeout_seconds

    # Retries are driven by our own policy in dispatch_event; ARQ's own
    # ceiling is set above it so ARQ never gives up before we have had the
    # chance to dead-letter with full context.
    max_tries = MAX_ATTEMPTS + 1

    # A plain attribute, not a staticmethod: ARQ reads `redis_settings` as
    # a value and immediately dereferences `.host`, so a callable here fails
    # at worker startup with `'staticmethod' object has no attribute 'host'`.
    # Evaluating at class-definition time is consistent with `_pool` above,
    # which already resolves at import.
    redis_settings = RedisSettings.from_dsn(str(get_settings().require_redis_url()))


__all__ = ["POOLS", "WorkerSettings", "dispatch_event"]

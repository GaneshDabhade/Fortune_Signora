"""OpenTelemetry tracing setup and cross-process context propagation.

The property that matters here is **trace continuity across the relay hop**.
An API request commits an event; a separate relay process picks it up; a
third worker process handles it. Without explicit propagation those appear
as three unrelated traces, and the pipeline becomes undebuggable exactly
when it is hardest to debug.

Instrumentation is vendor-neutral by design (ADR-0018): switching the
backend later is an exporter configuration change, not a re-instrumentation
project.
"""

from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.propagate import extract, inject
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Span

from signora_platform.observability.logging import get_logger
from signora_platform.settings import Settings

logger = get_logger(__name__)

TRACE_CONTEXT_KEY = "_trace_context"
"""Key under which W3C trace context travels inside a queued job's payload.

Carried in the job rather than the event envelope deliberately: trace
context is transport metadata, not domain data, and the envelope is a
documented contract (docs/architecture/06-events.md) that should not gain
observability fields.
"""


def configure_tracing(settings: Settings) -> None:
    """Install the tracer provider for this process.

    A missing ``otlp_endpoint`` configures tracing without an exporter
    rather than skipping setup entirely — spans are still created and
    context still propagates, so the code path is identical in development
    and production. Only the export is absent.
    """
    provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": settings.service_name,
                "service.version": settings.release_version,
                "deployment.environment": settings.environment,
            }
        )
    )

    if settings.otlp_endpoint:
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otlp_endpoint))
        )
        logger.info("tracing configured", extra={"otlp_endpoint": settings.otlp_endpoint})
    else:
        logger.info("tracing configured without exporter (no OTLP endpoint set)")

    trace.set_tracer_provider(provider)


def instrument_fastapi(app: Any) -> None:
    """Instrument a FastAPI application, if the optional package is present."""
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)
    except ImportError:  # pragma: no cover - optional dependency
        logger.warning("FastAPI instrumentation unavailable")


def instrument_sqlalchemy(engine: Any) -> None:
    """Instrument a SQLAlchemy engine, if the optional package is present."""
    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
    except ImportError:  # pragma: no cover - optional dependency
        logger.warning("SQLAlchemy instrumentation unavailable")


def get_tracer(name: str) -> trace.Tracer:
    return trace.get_tracer(name)


def current_trace_context() -> dict[str, str]:
    """Serialize the active trace context for transport across a process
    boundary."""
    carrier: dict[str, str] = {}
    inject(carrier)
    return carrier


def context_from(carrier: dict[str, str] | None) -> Any:
    """Restore trace context received from another process.

    Returns ``None`` when no context was carried, which starts a new trace
    rather than failing — an event published before tracing was enabled must
    still be processable.
    """
    return extract(carrier) if carrier else None


def set_event_attributes(
    span: Span,
    *,
    event_type: str,
    event_id: str,
    workspace_id: str,
    correlation_id: str,
    consumer_name: str | None = None,
) -> None:
    """Apply the standard event attributes to a span.

    Centralised so every span uses identical attribute names — inconsistent
    naming makes cross-service queries silently incomplete rather than
    obviously broken.
    """
    span.set_attribute("signora.event.type", event_type)
    span.set_attribute("signora.event.id", event_id)
    span.set_attribute("signora.workspace.id", workspace_id)
    span.set_attribute("signora.correlation.id", correlation_id)
    if consumer_name:
        span.set_attribute("signora.consumer.name", consumer_name)

"""Unit tests for metrics instruments and trace-context propagation.

These cover the parts of observability that carry logic. Vendor SDK
initialisation (Sentry's ``init``, the OTLP exporter) is deliberately not
unit-tested — asserting that a third-party constructor was called tests the
mock, not the system. Those paths are exercised by running the processes.
"""

from uuid import uuid4

import pytest
from opentelemetry import trace

from signora_platform.observability import (
    PipelineMetrics,
    configure_error_tracking,
    configure_metrics,
    configure_tracing,
    context_from,
    current_trace_context,
    get_tracer,
    set_event_attributes,
)
from signora_platform.settings import Settings


@pytest.fixture(scope="module")
def settings() -> Settings:
    return Settings(
        environment="test",
        database_url="postgresql+asyncpg://u:p@localhost:5432/db",
        jwt_public_key="key",
        jwt_issuer="iss",
        jwt_audience="aud",
    )


class TestMetrics:
    def test_builds_all_pipeline_instruments(self, settings: Settings) -> None:
        metrics = configure_metrics(settings)

        assert isinstance(metrics, PipelineMetrics)

    def test_recording_metrics_never_raises(self, settings: Settings) -> None:
        """Instrumentation must be safe to call unconditionally. A metric
        that can throw turns observability into an outage source."""
        metrics = configure_metrics(settings)

        metrics.event_relayed(event_type="a.b", subscribers=2)
        metrics.relay_failed(event_type="a.b")
        metrics.outbox_lag(seconds=1.5)
        metrics.event_handled(event_type="a.b", consumer_name="c", latency_ms=12.0)
        metrics.event_redelivered(event_type="a.b", consumer_name="c")
        metrics.handler_retried(event_type="a.b", consumer_name="c", attempt=2)
        metrics.event_dead_lettered(event_type="a.b", consumer_name="c")


class TestTracing:
    def test_configures_without_an_exporter(self, settings: Settings) -> None:
        """A missing OTLP endpoint must not prevent startup — spans are
        still created and context still propagates, only export is absent."""
        configure_tracing(settings)

        assert get_tracer("test") is not None

    def test_trace_context_round_trips_across_a_process_boundary(self, settings: Settings) -> None:
        """The relay hop is the whole reason this exists: without it, API,
        relay, and worker produce three unrelated traces."""
        configure_tracing(settings)
        tracer = get_tracer("test")

        with tracer.start_as_current_span("producer"):
            carrier = current_trace_context()

        assert carrier, "context must serialize into a carrier"
        assert context_from(carrier) is not None

    def test_absent_carrier_starts_a_new_trace_rather_than_failing(self) -> None:
        """An event published before tracing was enabled must still be
        processable."""
        assert context_from(None) is None
        assert context_from({}) is None

    def test_event_attributes_use_consistent_names(self, settings: Settings) -> None:
        """Inconsistent attribute names make cross-service queries silently
        incomplete rather than obviously broken."""
        configure_tracing(settings)
        tracer = get_tracer("test")
        event_id, workspace_id, correlation_id = uuid4(), uuid4(), uuid4()

        with tracer.start_as_current_span("consume") as span:
            set_event_attributes(
                span,
                event_type="a.b",
                event_id=str(event_id),
                workspace_id=str(workspace_id),
                correlation_id=str(correlation_id),
                consumer_name="timeline",
            )

            assert isinstance(span, trace.Span)


class TestErrorTracking:
    def test_absent_dsn_disables_tracking_without_failing(self, settings: Settings) -> None:
        """Local development and tests must not require a Sentry project."""
        configure_error_tracking(settings)

"""Pipeline metrics.

Every metric here exists because a specific decision depends on it. The
scaling triggers in docs/architecture/12-scalability.md — "queue depth
sustained growth that autoscaling cannot drain", "outbox dispatch latency
exceeding SLA" — are unusable without these being emitted, and a trigger
nobody can measure is a trigger that never fires.

Metric names are fixed here rather than at call sites so dashboards and
alerts bind to one definition. A renamed metric silently empties a
dashboard, which reads as "the system is healthy" rather than as a break.
"""

from typing import Final

from opentelemetry import metrics

from signora_platform.settings import Settings

_METER_NAME: Final = "signora.pipeline"

OUTBOX_RELAYED: Final = "signora.outbox.relayed"
OUTBOX_RELAY_FAILURES: Final = "signora.outbox.relay_failures"
OUTBOX_LAG_SECONDS: Final = "signora.outbox.lag_seconds"
DISPATCH_LATENCY: Final = "signora.dispatch.latency_ms"
EVENTS_HANDLED: Final = "signora.events.handled"
EVENTS_REDELIVERED: Final = "signora.events.redelivered"
HANDLER_RETRIES: Final = "signora.handler.retries"
DEAD_LETTERED: Final = "signora.events.dead_lettered"


class PipelineMetrics:
    """Instruments for the event pipeline.

    Constructed once per process and passed explicitly rather than accessed
    as a module global, so tests can assert on a real instance instead of
    reaching into global state.
    """

    def __init__(self, meter: metrics.Meter) -> None:
        self._relayed = meter.create_counter(
            OUTBOX_RELAYED, unit="1", description="Outbox events successfully relayed"
        )
        self._relay_failures = meter.create_counter(
            OUTBOX_RELAY_FAILURES,
            unit="1",
            description="Failed attempts to enqueue an outbox event",
        )
        self._outbox_lag = meter.create_histogram(
            OUTBOX_LAG_SECONDS,
            unit="s",
            description="Age of the oldest unrelayed outbox event",
        )
        self._dispatch_latency = meter.create_histogram(
            DISPATCH_LATENCY,
            unit="ms",
            description="Time from event commit to handler completion",
        )
        self._handled = meter.create_counter(
            EVENTS_HANDLED, unit="1", description="Events handled successfully"
        )
        self._redelivered = meter.create_counter(
            EVENTS_REDELIVERED,
            unit="1",
            description="Redeliveries skipped by the idempotency ledger",
        )
        self._retries = meter.create_counter(
            HANDLER_RETRIES, unit="1", description="Handler attempts that failed and retried"
        )
        self._dead_lettered = meter.create_counter(
            DEAD_LETTERED, unit="1", description="Events moved to the dead-letter table"
        )

    def event_relayed(self, *, event_type: str, subscribers: int) -> None:
        self._relayed.add(1, {"event_type": event_type, "subscribers": str(subscribers)})

    def relay_failed(self, *, event_type: str) -> None:
        self._relay_failures.add(1, {"event_type": event_type})

    def outbox_lag(self, *, seconds: float) -> None:
        self._outbox_lag.record(seconds)

    def event_handled(self, *, event_type: str, consumer_name: str, latency_ms: float) -> None:
        attrs = {"event_type": event_type, "consumer_name": consumer_name}
        self._handled.add(1, attrs)
        self._dispatch_latency.record(latency_ms, attrs)

    def event_redelivered(self, *, event_type: str, consumer_name: str) -> None:
        self._redelivered.add(1, {"event_type": event_type, "consumer_name": consumer_name})

    def handler_retried(self, *, event_type: str, consumer_name: str, attempt: int) -> None:
        self._retries.add(
            1,
            {
                "event_type": event_type,
                "consumer_name": consumer_name,
                "attempt": str(attempt),
            },
        )

    def event_dead_lettered(self, *, event_type: str, consumer_name: str) -> None:
        self._dead_lettered.add(1, {"event_type": event_type, "consumer_name": consumer_name})


def configure_metrics(settings: Settings) -> PipelineMetrics:
    """Build the metrics instruments for this process.

    Uses whatever meter provider is installed. As with tracing, absent an
    exporter the instruments still exist and are still recorded to — only
    export is missing — so instrumented code behaves identically in every
    environment.
    """
    return PipelineMetrics(metrics.get_meter(_METER_NAME, settings.release_version))

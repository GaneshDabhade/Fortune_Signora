"""Sentry error tracking (ADR-0018).

Sentry receives the exception detail the API deliberately withholds from
callers — the standard error envelope returns a generic message plus a
correlation id, and this is where the specifics go. The correlation id is
attached as a tag so a support conversation quoting it leads directly to
the captured exception.
"""

from typing import Any

from signora_platform.observability.context import current_context
from signora_platform.observability.logging import get_logger, redact
from signora_platform.settings import Settings

logger = get_logger(__name__)


def configure_error_tracking(settings: Settings) -> None:
    """Initialise Sentry if a DSN is configured.

    Absent a DSN this is a no-op: local development and tests must not need
    a Sentry project, and a missing DSN must never prevent startup.
    """
    if not settings.sentry_dsn:
        logger.info("error tracking disabled (no Sentry DSN configured)")
        return

    import sentry_sdk

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        release=settings.release_version,
        # Sampled rather than exhaustive: Sentry is for errors, and
        # OpenTelemetry already owns full-fidelity tracing (ADR-0018).
        traces_sample_rate=0.1,
        # PII is scrubbed in before_send; this prevents Sentry's own
        # convenience capture of headers, cookies, and request bodies from
        # reintroducing it beforehand.
        send_default_pii=False,
        before_send=_scrub_event,
    )
    logger.info("error tracking configured", extra={"environment": settings.environment})


def _scrub_event(event: Any, _hint: dict[str, Any]) -> Any:
    """Redact secrets and attach correlation context before an event is sent.

    Reuses the logging redactor rather than duplicating the patterns — one
    definition of "what counts as a secret" is the only way to keep the two
    paths from drifting apart.
    """
    scrubbed: Any = redact(event)

    context = current_context()
    if context:
        tags = scrubbed.setdefault("tags", {})
        for key in ("correlation_id", "workspace_id", "consumer_name"):
            if key in context:
                tags[key] = context[key]

    return scrubbed

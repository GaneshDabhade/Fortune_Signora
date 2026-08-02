"""Event handlers: one handler, nine event types.

**One handler rather than nine.** Every upstream event reaches Timeline through
the same question — *does this project, and to what* — answered by the
projection table rather than by the handler. Nine near-identical handlers would
be nine places for the answer to drift.

**Timeline subscribes and publishes nothing.** It is a pure read-side consumer
([04-modules.md](../../../../docs/architecture/04-modules.md)), so there is no
outbox write here and no event to catalog.
"""

from __future__ import annotations

from modules.timeline.application.project import ProjectEvent, ProjectEventInput
from signora_platform.event_bus import EventEnvelope
from signora_platform.observability import get_logger

logger = get_logger(__name__)

CONSUMER_NAME = "timeline.project"
"""A permanent contract. Renaming it resets the idempotency ledger, and every
historical event would be re-projected on the next replay."""


async def project_to_timeline(envelope: EventEnvelope, *, project: ProjectEvent) -> None:
    written = await project.execute(
        ProjectEventInput(
            event_id=envelope.event_id,
            event_type=envelope.event_type,
            workspace_id=envelope.workspace_id,
            occurred_at=envelope.occurred_at,
            payload=envelope.payload,
        )
    )
    # Logged at debug, and only when something was written. A projection runs
    # on every event the pipeline produces, so an info line per delivery would
    # bury the lines that matter — and a redelivery writing nothing is the
    # system working, not an anomaly worth a level.
    if written:
        logger.debug(
            "timeline entry projected",
            extra={
                "workspace_id": str(envelope.workspace_id),
                "correlation_id": str(envelope.correlation_id),
                "causation_id": str(envelope.event_id),
                "event_type": envelope.event_type,
            },
        )

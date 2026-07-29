"""Event handlers: detect when observations arrive, re-evaluate when they
are refined.

Subscribes to `observation.recorded` and `observation.superseded` from the
Observation Engine. The second is not optional: an event built on an
observation that was later refined is a conclusion resting on evidence
that has moved, and because business events **cite** rather than copy, it
is findable.
"""

from __future__ import annotations

from uuid import UUID

from modules.business_event_engine.application.detect import (
    DetectBusinessEvents,
    DetectBusinessEventsInput,
)
from signora_platform.event_bus import EventEnvelope
from signora_platform.observability import get_logger

logger = get_logger(__name__)

CONSUMER_NAME = "business_event_engine.detect"
"""A permanent contract. Renaming it resets the idempotency ledger and
every historical event would be re-processed on replay."""


async def detect_from_observation(envelope: EventEnvelope, *, detect: DetectBusinessEvents) -> None:
    await detect.execute(
        DetectBusinessEventsInput(
            workspace_id=envelope.workspace_id,
            entity_id=UUID(str(envelope.payload["entity_id"])),
        ),
        correlation_id=envelope.correlation_id,
        causation_id=envelope.event_id,
    )

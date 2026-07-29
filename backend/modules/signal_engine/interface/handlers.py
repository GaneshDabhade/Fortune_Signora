"""Event handler: form hypotheses when business events are detected.

Subscribes to `business_event.detected` and `business_event.superseded`
from the Business Event Engine. Signals reference **business event types
directly** — never re-derived meaning from observations, which would fork
the vocabulary and diverge within a year.
"""

from __future__ import annotations

from uuid import UUID

from modules.signal_engine.application.generate import (
    GenerateSignals,
    GenerateSignalsInput,
)
from signora_platform.event_bus import EventEnvelope
from signora_platform.observability import get_logger

logger = get_logger(__name__)

CONSUMER_NAME = "signal_engine.generate"
"""A permanent contract. Renaming it resets the idempotency ledger and
every historical event would be re-processed on replay."""


async def generate_from_business_event(
    envelope: EventEnvelope, *, generate: GenerateSignals
) -> None:
    await generate.execute(
        GenerateSignalsInput(
            workspace_id=envelope.workspace_id,
            entity_id=UUID(str(envelope.payload["entity_id"])),
        ),
        correlation_id=envelope.correlation_id,
        causation_id=envelope.event_id,
    )

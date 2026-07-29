"""Event handler: consider an account for tracking when its score moves.

Subscribes to `buying_score.updated`. **This is the only automatic path
into workflow, and it can do exactly one thing:** open an opportunity at
`TRACKING`, which commits nobody.

There is deliberately **no handler that closes, progresses, or reassigns
anything.** A falling score, an expiring score, or an account going quiet
arrives here as an event and changes no stage. That is not an oversight to
fill in later — it is the principle, and the absence of the code is what
enforces it.
"""

from __future__ import annotations

from uuid import UUID

from modules.opportunity_engine.application.qualify import (
    QualifyOpportunity,
    QualifyOpportunityInput,
)
from signora_platform.event_bus import EventEnvelope
from signora_platform.observability import get_logger

logger = get_logger(__name__)

CONSUMER_NAME = "opportunity_engine.qualify"
"""A permanent contract. Renaming it resets the idempotency ledger and
every historical event would be re-processed on replay."""


async def qualify_from_buying_score(
    envelope: EventEnvelope, *, qualify: QualifyOpportunity
) -> None:
    await qualify.execute(
        QualifyOpportunityInput(
            workspace_id=envelope.workspace_id,
            entity_id=UUID(str(envelope.payload["entity_id"])),
        ),
        correlation_id=envelope.correlation_id,
        causation_id=envelope.event_id,
    )

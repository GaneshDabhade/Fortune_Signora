"""Event handler: observe what changed when evidence lands.

Subscribes to `entity.evidence_attached` from the Knowledge Graph — never
to `claim.recorded` directly. **The Observation Engine reasons over
evidence that has already been attached to an identity**, so it can never
observe something it cannot attribute to an entity, and the ratified
dependency graph (Knowledge Graph → Observation Engine) stays intact.
"""

from __future__ import annotations

from uuid import UUID

from modules.observation_engine.application.record import (
    RecordObservations,
    RecordObservationsInput,
)
from signora_platform.event_bus import EventEnvelope
from signora_platform.observability import get_logger

logger = get_logger(__name__)

CONSUMER_NAME = "observation_engine.observe_changes"
"""A permanent contract. Renaming it resets the idempotency ledger and
every historical event would be re-processed on replay."""


async def observe_attached_evidence(envelope: EventEnvelope, *, record: RecordObservations) -> None:
    claim_ids = frozenset(UUID(str(raw)) for raw in envelope.payload["claim_ids"])
    if not claim_ids:
        return

    await record.execute(
        RecordObservationsInput(
            workspace_id=envelope.workspace_id,
            entity_id=UUID(str(envelope.payload["entity_id"])),
            new_claim_ids=claim_ids,
        ),
        correlation_id=envelope.correlation_id,
        causation_id=envelope.event_id,
    )

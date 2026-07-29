"""Event handlers: re-read an account's attention when its hypotheses move.

Subscribes to `signal.generated` and `signal.superseded` from the Signal
Engine. **Both matter.** A strengthened hypothesis arrives as a new signal
plus a supersession, and a consumer that handled only the first would keep
weighing the replaced reading alongside the one that replaced it — counting
the same grounds twice.

Signals are read back through the Signal Engine's published port rather
than reconstructed from the envelope. Events carry identity; ports carry
payload, and a score built from an event body would be a score built from
whatever the envelope happened to include.
"""

from __future__ import annotations

from uuid import UUID

from modules.buying_score_engine.application.compute import (
    ComputeBuyingScore,
    ComputeBuyingScoreInput,
)
from modules.buying_score_engine.domain.score import ScoreTrigger
from signora_platform.event_bus import EventEnvelope
from signora_platform.observability import get_logger

logger = get_logger(__name__)

CONSUMER_NAME = "buying_score_engine.compute"
"""A permanent contract. Renaming it resets the idempotency ledger and
every historical event would be re-processed on replay."""

_TRIGGERS = {
    "signal.generated": ScoreTrigger.SIGNAL_GENERATED,
    "signal.superseded": ScoreTrigger.SIGNAL_SUPERSEDED,
}


async def compute_from_signal(
    envelope: EventEnvelope, *, compute: ComputeBuyingScore
) -> None:
    await compute.execute(
        ComputeBuyingScoreInput(
            workspace_id=envelope.workspace_id,
            entity_id=UUID(str(envelope.payload["entity_id"])),
            trigger=_TRIGGERS.get(envelope.event_type, ScoreTrigger.SIGNAL_GENERATED),
        ),
        correlation_id=envelope.correlation_id,
        causation_id=envelope.event_id,
    )

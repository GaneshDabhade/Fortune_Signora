"""Domain events published by the Buying Score Engine.

Cataloged in docs/architecture/06-events.md.

The payload carries `contested` alongside the number. A consumer that
cannot tell a fought-over account from a quiet one will reconstruct the
distinction by querying signals itself, which puts scoring logic in
Opportunity Engine — the fact travels with the score precisely so it does
not have to be rebuilt downstream.

**No probability, no likelihood, no prediction.** A buying score
prioritizes commercial attention; it does not forecast a purchase, and a
field here implying otherwise would be believed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Final
from uuid import UUID

EVENT_VERSION: Final = 1


@dataclass(frozen=True, slots=True)
class BuyingScoreUpdated:
    """An account's commercial attention has been re-read."""

    event_id: UUID
    workspace_id: UUID
    occurred_at: datetime
    score_id: UUID
    entity_id: UUID
    score: int
    trend: str
    delta: int
    contested: bool
    #: The hypotheses the number rests on. Identity only — the ledger
    #: carries the arithmetic, and embedding it here would make every
    #: weighting change an event-contract change.
    source_signal_ids: tuple[UUID, ...]
    dissenting_signal_ids: tuple[UUID, ...]
    trigger: str
    #: Until when the published number is exactly correct. A consumer
    #: holding it past this moment knows it is reading a stale reading.
    valid_until: datetime | None
    model_version: int
    payload_version: int
    causation_id: UUID | None = None
    event_type: str = "buying_score.updated"
    event_version: int = EVENT_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {
            "score_id": str(self.score_id),
            "entity_id": str(self.entity_id),
            "score": self.score,
            "trend": self.trend,
            "delta": self.delta,
            "contested": self.contested,
            "source_signal_ids": [str(signal_id) for signal_id in self.source_signal_ids],
            "dissenting_signal_ids": [str(signal_id) for signal_id in self.dissenting_signal_ids],
            "trigger": self.trigger,
            "valid_until": None if self.valid_until is None else self.valid_until.isoformat(),
            "model_version": self.model_version,
            "payload_version": self.payload_version,
        }

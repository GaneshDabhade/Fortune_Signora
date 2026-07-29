"""Domain events published by the Observation Engine.

Cataloged in docs/architecture/06-events.md.

Following the established rule — **events carry identity, ports carry
payload** — neither event carries the observed values. A consumer reads
them through the module's read port, so adding a canonical attribute is
never an event-contract change.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Final
from uuid import UUID

EVENT_VERSION: Final = 1


@dataclass(frozen=True, slots=True)
class ObservationRecorded:
    """Something changed, according to one provider.

    **Not a claim that it matters.** `direction` and `kind` are structural
    readings; the Business Event Engine applies its taxonomy to decide
    whether this is a hiring surge or a rounding error.
    """

    event_id: UUID
    workspace_id: UUID
    occurred_at: datetime
    observation_id: UUID
    entity_id: UUID
    provider: str
    attribute: str
    kind: str
    direction: str
    #: When the provider says it was true — distinct from `occurred_at`,
    #: which is when Signora learned it. Timeline orders on this one, or a
    #: backfill would render as a wall of activity on its ingestion day.
    observed_at: datetime
    causation_id: UUID | None = None
    event_type: str = "observation.recorded"
    event_version: int = EVENT_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {
            "observation_id": str(self.observation_id),
            "entity_id": str(self.entity_id),
            "provider": self.provider,
            "attribute": self.attribute,
            "kind": self.kind,
            "direction": self.direction,
            "observed_at": self.observed_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class ObservationSuperseded:
    """A late-arriving claim refined an earlier observation.

    A first-class event rather than a log line: a consumer that already
    acted on the coarser observation needs to know it was refined, or it
    will double-count the change.
    """

    event_id: UUID
    workspace_id: UUID
    occurred_at: datetime
    observation_id: UUID
    supersedes: UUID
    entity_id: UUID
    attribute: str
    causation_id: UUID | None = None
    event_type: str = "observation.superseded"
    event_version: int = EVENT_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {
            "observation_id": str(self.observation_id),
            "supersedes": str(self.supersedes),
            "entity_id": str(self.entity_id),
            "attribute": self.attribute,
        }

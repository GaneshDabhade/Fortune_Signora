"""Domain events published by the Business Event Engine.

Cataloged in docs/architecture/06-events.md.

Following the established rule — **events carry identity, ports carry
payload** — neither event carries `facts` or the evidence list. A consumer
reads them through the module's read port, so adding a fact to a type is
never an event-contract change.

**Two version numbers travel together, deliberately.** `taxonomy_version`
is the meaning; `payload_version` is the wire shape. Conflating them means
tuning a threshold breaks a consumer contract, so nobody ever tunes a
threshold.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Final
from uuid import UUID

EVENT_VERSION: Final = 1


@dataclass(frozen=True, slots=True)
class BusinessEventDetected:
    """Something business-relevant happened.

    **Not a claim that anyone should act on it.** Priority, urgency, and
    likelihood belong to the Signal Engine and everything after it.
    """

    event_id: UUID
    workspace_id: UUID
    occurred_at: datetime
    business_event_id: UUID
    entity_id: UUID
    type_key: str
    domain: str
    #: When it happened in the customer's business — distinct from
    #: `occurred_at`, which is when Signora concluded it. Timeline orders on
    #: this one, or a backfill renders as a wall of activity.
    business_occurred_at: datetime
    window_start: datetime
    window_end: datetime
    taxonomy_version: int
    payload_version: int
    causation_id: UUID | None = None
    event_type: str = "business_event.detected"
    event_version: int = EVENT_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {
            "business_event_id": str(self.business_event_id),
            "entity_id": str(self.entity_id),
            "type_key": self.type_key,
            "domain": self.domain,
            "occurred_at": self.business_occurred_at.isoformat(),
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "taxonomy_version": self.taxonomy_version,
            "payload_version": self.payload_version,
        }


@dataclass(frozen=True, slots=True)
class BusinessEventSuperseded:
    """A phenomenon extended, or a conclusion was corrected.

    A first-class event rather than a log line: a consumer that already
    acted on the earlier, smaller view needs to know, or it will count the
    same phenomenon twice.
    """

    event_id: UUID
    workspace_id: UUID
    occurred_at: datetime
    business_event_id: UUID
    supersedes: UUID
    entity_id: UUID
    type_key: str
    causation_id: UUID | None = None
    event_type: str = "business_event.superseded"
    event_version: int = EVENT_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {
            "business_event_id": str(self.business_event_id),
            "supersedes": str(self.supersedes),
            "entity_id": str(self.entity_id),
            "type_key": self.type_key,
        }

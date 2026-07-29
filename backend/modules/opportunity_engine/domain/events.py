"""Domain events published by the Opportunity Engine.

Cataloged in docs/architecture/06-events.md.

**The first events in the pipeline that announce a decision rather than a
derivation.** Everything upstream announces what Signora concluded from
evidence; `opportunity.stage_changed` announces what a person did.

`opportunity.closed` is deliberately absent: `stage_changed` already
carries it, and an event whose information is fully contained in another is
a contract nobody keeps — the same reasoning that removed `signal.scored`
and `business_event_type.published`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Final
from uuid import UUID

EVENT_VERSION: Final = 1


@dataclass(frozen=True, slots=True)
class OpportunityCreated:
    """An account crossed the threshold for tracking.

    **A suggestion, not a commitment.** The opportunity opens at `TRACKING`,
    which commits nobody: *intelligence suggests; humans commit*.
    """

    event_id: UUID
    workspace_id: UUID
    occurred_at: datetime
    opportunity_id: UUID
    entity_id: UUID
    #: The score that caused this to exist — the first link of the chain
    #: outward to the raw provider payload.
    originating_buying_score_id: UUID
    score_at_creation: int
    #: Carried so no consumer has to rediscover it by querying signals,
    #: which would put scoring logic in the wrong module.
    contested_at_creation: bool
    qualification: str
    stage: str
    policy_version: int
    payload_version: int
    causation_id: UUID | None = None
    event_type: str = "opportunity.created"
    event_version: int = EVENT_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {
            "opportunity_id": str(self.opportunity_id),
            "entity_id": str(self.entity_id),
            "originating_buying_score_id": str(self.originating_buying_score_id),
            "score_at_creation": self.score_at_creation,
            "contested_at_creation": self.contested_at_creation,
            "qualification": self.qualification,
            "stage": self.stage,
            "policy_version": self.policy_version,
            "payload_version": self.payload_version,
        }


@dataclass(frozen=True, slots=True)
class OpportunityStageChanged:
    """A human moved an opportunity.

    `actor_id` is never absent here: only `TRACKING` may be machine-authored,
    and `TRACKING` is only ever an opening state.
    """

    event_id: UUID
    workspace_id: UUID
    occurred_at: datetime
    opportunity_id: UUID
    entity_id: UUID
    previous_stage: str
    new_stage: str
    owner_id: UUID | None
    actor_id: UUID
    reason: str
    sequence: int
    payload_version: int
    causation_id: UUID | None = None
    event_type: str = "opportunity.stage_changed"
    event_version: int = EVENT_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {
            "opportunity_id": str(self.opportunity_id),
            "entity_id": str(self.entity_id),
            "previous_stage": self.previous_stage,
            "new_stage": self.new_stage,
            "owner_id": None if self.owner_id is None else str(self.owner_id),
            "actor_id": str(self.actor_id),
            "reason": self.reason,
            "sequence": self.sequence,
            "payload_version": self.payload_version,
        }

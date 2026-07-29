"""Domain events published by the Signal Engine.

Cataloged in docs/architecture/06-events.md.

**Neither event carries a score**, because the Signal Engine produces none.
That is a change from the v2 catalog, which gave `signal.generated` a
`score` and added a `signal.scored` event: propensity belongs to the Buying
Score Engine, and an event whose only possible producer lives in another
module is a contract nobody is keeping.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Final
from uuid import UUID

EVENT_VERSION: Final = 1


@dataclass(frozen=True, slots=True)
class SignalGenerated:
    """A commercial hypothesis is supported for this workspace.

    **Not a claim that anyone should act.** How likely a purchase is, which
    account to prioritise, and what to recommend belong downstream.
    """

    event_id: UUID
    workspace_id: UUID
    occurred_at: datetime
    signal_id: UUID
    entity_id: UUID
    signal_type: str
    relevance: str
    #: When the underlying business events happened — distinct from
    #: `occurred_at`, which is when Signora formed the hypothesis.
    business_occurred_at: datetime
    relevant_until: datetime
    #: The two halves of *why this exists*. A historical signal without both
    #: is unexplainable.
    catalog_version: int
    profile_version: int
    payload_version: int
    causation_id: UUID | None = None
    event_type: str = "signal.generated"
    event_version: int = EVENT_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {
            "signal_id": str(self.signal_id),
            "entity_id": str(self.entity_id),
            "signal_type": self.signal_type,
            # A category, never a number — see Relevance. It travels as the
            # string it is so no consumer can read it as a weight.
            "relevance": self.relevance,
            "occurred_at": self.business_occurred_at.isoformat(),
            "relevant_until": self.relevant_until.isoformat(),
            "catalog_version": self.catalog_version,
            "profile_version": self.profile_version,
            "payload_version": self.payload_version,
        }


@dataclass(frozen=True, slots=True)
class SignalSuperseded:
    """A hypothesis gained evidence, or a conclusion was corrected.

    First-class rather than a log line: a consumer that already acted on the
    smaller view needs to know, or it will count the same grounds twice.
    """

    event_id: UUID
    workspace_id: UUID
    occurred_at: datetime
    signal_id: UUID
    supersedes: UUID
    entity_id: UUID
    signal_type: str
    causation_id: UUID | None = None
    event_type: str = "signal.superseded"
    event_version: int = EVENT_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {
            "signal_id": str(self.signal_id),
            "supersedes": str(self.supersedes),
            "entity_id": str(self.entity_id),
            "signal_type": self.signal_type,
        }

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


@dataclass(frozen=True, slots=True)
class SignalResolved:
    """A person decided what to do about a signal, and the pipeline hears it.

    **The one thing in this pipeline that produced no event.** Every other
    stage announces what it concluded; a *human* decision was recorded in a row
    and nowhere else — so `timeline` could not project it, and a measure of
    whether Signora's judgement was any good had nothing to read. **The row
    records the state; nothing recorded the transition**, and a transition
    nobody published is evidence that cannot be recovered afterwards.

    ### It carries the outcome's name, never the reason's words

    `Dismissed` holds a person's own sentence about why Signora was wrong.
    **That sentence stays in the row it was written into.** An event carries an
    identity, not a body — the rule `provider.record.received` already follows,
    *"the record's identity, not its body: a consumer that needs the payload
    reads it through a port"* — and a free-text field a customer typed would
    otherwise be copied into every subscriber's storage by a bus that cannot
    take it back.

    ### And it carries no `closes_the_signal`

    **Derivable from `outcome`, and therefore a second representation of one
    fact** (§2). Which outcomes end a signal is this module's judgement and it
    is published in `CLOSING`; a consumer that needs the answer asks rather
    than being handed a boolean that can disagree with the discriminator
    beside it.
    """

    event_id: UUID
    workspace_id: UUID
    occurred_at: datetime
    resolution_id: UUID
    signal_id: UUID
    #: **The account the decision was about**, carried because a consumer that
    #: projects per account cannot reach a signal to look it up — `timeline`
    #: does not depend on this module's read surface.
    entity_id: UUID
    #: The outcome's discriminator — `actioned`, `assigned`, `snoozed` or
    #: `dismissed`. **A closed vocabulary this module owns**, and deliberately
    #: not a `Relevance` value: `IGNORED` there is prospective configuration
    #: about a signal *type*, and this is a retrospective judgement about one
    #: signal. Collapsing them would turn feedback into configuration.
    outcome: str
    #: **Never absent, and never the platform.** Every outcome is a human
    #: judgement, so an event without an actor could not have happened.
    actor_id: UUID
    #: The resolution this replaces. `None` on the first decision about a
    #: signal, and set when somebody changed their mind — which is a new record
    #: naming the old one, never an edit.
    supersedes: UUID | None
    payload_version: int
    causation_id: UUID | None = None
    event_type: str = "signal.resolved"
    event_version: int = EVENT_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {
            "resolution_id": str(self.resolution_id),
            "signal_id": str(self.signal_id),
            "entity_id": str(self.entity_id),
            "outcome": self.outcome,
            "actor_id": str(self.actor_id),
            "supersedes": str(self.supersedes) if self.supersedes else None,
            "payload_version": self.payload_version,
        }

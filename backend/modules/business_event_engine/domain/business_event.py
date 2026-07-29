"""The Business Event — what happened in the customer's business.

**This module answers "why is this business-relevant?" and nothing more.**
It does not answer how important the account is, whether Sales should
engage, what priority this deserves, how likely a purchase is, or what to
recommend. Those belong to the Signal Engine and everything after it, and
a business event therefore carries **no priority, score, urgency, or
rank** — asserted structurally, not by convention.

The test every field has to pass is the same one the taxonomy passes: a
CRO reading this should understand what happened without knowing which
vendor reported it or how Signora derived it.

Three properties carry the design:

**Durable history.** Events are immutable. A phenomenon that extends or a
conclusion that is corrected produces a *new* event naming the one it
replaces, so the full sequence of what Signora believed survives — which
is what lets a later module reason over history rather than over a
snapshot.

**Citation, never subsumption.** An event references its observations
rather than copying their values, so the chain stays walkable in both
directions and a corrected mapper's blast radius stays knowable.

**Agreement is evidence, not truth.** `corroborating_providers` records
which providers' series independently satisfied the rule. It is a set,
never a coefficient — combining provider values into a synthetic truth is
exactly what the pipeline refuses.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any, Final
from uuid import UUID, uuid5

from modules.business_event_engine.domain.taxonomy import BusinessDomain, BusinessEventType

BUSINESS_EVENT_NAMESPACE: Final = UUID("2f7c9a10-4b6d-5e81-b3c2-7d95a1e04f68")
"""Fixed namespace for deterministic identity. **Never change it** — every
business event in every workspace would acquire a new identity, and the
next detection would insert a duplicate of the entire table."""

PAYLOAD_VERSION: Final = 1
"""The wire shape of `facts` and of the published envelope.

**Deliberately separate from the taxonomy version.** Conflating them means
tuning a threshold breaks a consumer contract, so nobody ever tunes a
threshold. Kept apart, the taxonomy can evolve while the contract stays
stable.
"""


class BusinessEventError(ValueError):
    """A business event was constructed that violates an invariant."""


@dataclass(frozen=True, slots=True)
class BusinessEvent:
    id: UUID
    workspace_id: UUID
    entity_id: UUID
    type_key: BusinessEventType
    domain: BusinessDomain

    #: When it happened in the customer's business — never when Signora
    #: noticed. Timeline orders on this, or a backfill renders as a wall of
    #: activity on its ingestion day.
    occurred_at: datetime
    #: The interval the evidence supports. Collapsed to one instant for an
    #: event derived from a single observation; never narrower than the
    #: evidence for a correlated one.
    window_start: datetime
    window_end: datetime
    #: When Signora concluded it. The gap from `occurred_at` is detection
    #: lag, which is an operational metric rather than a business fact.
    detected_at: datetime

    #: A sentence a customer reads, rendered by the rule from `facts` — so
    #: the words a CRO sees and the numbers an auditor checks cannot
    #: diverge.
    summary: str
    #: What the rule computed. Business quantities only: a growth ratio, a
    #: round amount, a technology name. **Never a score.**
    facts: dict[str, Any]

    evidence_observation_ids: tuple[UUID, ...]
    #: Which providers' series independently satisfied the rule. A count of
    #: agreement, never a weight.
    corroborating_providers: tuple[str, ...]

    taxonomy_version: int
    payload_version: int = PAYLOAD_VERSION
    #: The event this one replaces — a phenomenon that extended, or a
    #: conclusion corrected after evidence was refined. Points **backwards**,
    #: forced by immutability: a forward pointer would have to be written
    #: onto the older row, which needs the UPDATE grant this table
    #: deliberately withholds.
    supersedes: UUID | None = None

    def __post_init__(self) -> None:
        if not self.evidence_observation_ids:
            raise BusinessEventError(
                f"business event {self.id} cites no observations. An event that cannot be traced "
                "back to the evidence that produced it is an assertion, not intelligence."
            )
        if not self.corroborating_providers:
            raise BusinessEventError(
                f"business event {self.id} names no provider. Every conclusion in Signora is "
                "*according to* someone, and dropping that is how evidence becomes assertion."
            )
        if self.window_end < self.window_start:
            raise BusinessEventError("a business event's window cannot end before it begins.")
        if not self.summary.strip():
            raise BusinessEventError(
                "a business event without a summary is one no customer can read."
            )

    @property
    def is_corroborated(self) -> bool:
        """Whether more than one provider independently supports this.

        A **fact about the evidence**, deliberately not a confidence.
        Turning agreement into a weight is the Signal Engine's decision to
        make, with its own reviewable rule.
        """
        return len(self.corroborating_providers) > 1

    def replacing(self, earlier: UUID) -> BusinessEvent:
        return replace(self, supersedes=earlier)


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def business_event_id(
    *,
    workspace_id: UUID,
    entity_id: UUID,
    type_key: BusinessEventType,
    evidence_observation_ids: tuple[UUID, ...],
) -> UUID:
    """Derived from the evidence, never allocated.

    **Deliberately not keyed on the taxonomy version.** The identity is the
    business fact, not the rule that found it: a version bump that
    re-detects the same surge over the same evidence produces the same id
    and inserts nothing, which is what should happen. A version that finds
    a *different* extent produces a different evidence set, and therefore a
    new event superseding the old.

    Observation ids are themselves derived from observed facts and survive
    claim regeneration, so a business event survives a full pipeline
    rebuild.
    """
    evidence = "|".join(sorted(str(observation_id) for observation_id in evidence_observation_ids))
    return uuid5(
        BUSINESS_EVENT_NAMESPACE, f"{workspace_id}|{entity_id}|{type_key.value}|{evidence}"
    )

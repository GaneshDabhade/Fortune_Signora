"""The Signal — a commercial hypothesis, held for one customer.

**A signal proposes; it does not assert.** Business events describe
objective business phenomena. A signal describes what those phenomena
*might* mean commercially, to *this* workspace — a reading that is false
for a company selling something else and unknowable from the evidence
alone.

Four properties keep that honest:

**It asserts nothing of its own.** Every fact in a signal is a citation.
The module holds no measurements, no scores, and no claims about the
world; it holds a reference to the business events that carry them and an
interpretation drawn from the workspace's profile.

**Contradiction is preserved, never resolved.** A `CONTRACTION_RISK` and
an `EXPANSION_OPPORTUNITY` may be live for one account at once. The Signal
Engine must not pick — that is the claim-disagreement principle one layer
up, and collapsing the two would destroy exactly what a seller needs to
see.

**A hypothesis has a shelf life.** `relevant_until` is a derived date, not
a weight: how long this interpretation stays current, declared per type in
the catalog.

**It explains itself in two halves** — the interpretation and the
evidence — because a customer must be able to challenge either one
independently.

There is **no score, no priority, no likelihood, and no rank**. How much
this matters is the Buying Score Engine's question.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Final
from uuid import UUID, uuid5

from modules.business_event_engine.public import BusinessEventType
from modules.signal_engine.domain.catalog import Relevance, SignalType

SIGNAL_NAMESPACE: Final = UUID("8c41e6b2-73da-5f19-a4d7-2e0b95f31c68")
"""Fixed namespace for deterministic identity. **Never change it** — every
signal in every workspace would acquire a new identity, and the next
generation would insert a duplicate of the entire table."""

PAYLOAD_VERSION: Final = 1


class SignalError(ValueError):
    """A signal was constructed that violates an invariant."""


@dataclass(frozen=True, slots=True)
class Signal:
    id: UUID
    workspace_id: UUID
    entity_id: UUID
    signal_type: SignalType
    #: The workspace's reading **at generation time**, denormalized so the
    #: signal stays self-describing after the profile changes.
    relevance: Relevance

    #: When the underlying business events happened — never generation
    #: time. Timeline orders on this.
    occurred_at: datetime
    window_start: datetime
    window_end: datetime
    #: When Signora formed the hypothesis. The gap from `occurred_at` is
    #: interpretation lag.
    generated_at: datetime
    #: How long this reading stays current. A **date**, derived from the
    #: catalog's declared relevance window — never a weight.
    relevant_until: datetime

    #: Two halves: why this matters *here*, and what it rests on. Rendered
    #: together so the interpretation a customer reads and the evidence an
    #: auditor checks cannot diverge.
    rationale: str

    contributing_event_ids: tuple[UUID, ...]
    #: Carried alongside the ids so a consumer can reason about the *shape*
    #: of the evidence — "this rests on hiring and funding" — without a join.
    contributing_event_types: tuple[BusinessEventType, ...]
    #: Signals this one builds on. **A composite enriches; it never
    #: replaces.** Every constituent remains independently visible and
    #: independently explainable — the composite adds context on top of
    #: them, and collapses no history.
    constituent_signal_ids: tuple[UUID, ...] = ()

    catalog_version: int = 0
    profile_version: int = 0
    payload_version: int = PAYLOAD_VERSION
    supersedes: UUID | None = None

    def __post_init__(self) -> None:
        if not self.contributing_event_ids:
            raise SignalError(
                f"signal {self.id} cites no business events. A hypothesis with no evidence is an "
                "opinion, and the chain back to raw provider payloads is what makes it otherwise."
            )
        if not self.contributing_event_types:
            raise SignalError(
                f"signal {self.id} names no contributing event types; downstream would have to "
                "join to learn the shape of its own evidence."
            )
        if self.relevance is Relevance.IGNORED:
            raise SignalError(
                "a signal was generated for a type this workspace ignores. `IGNORED` means the "
                "hypothesis is not held here at all, not that it is held weakly."
            )
        if self.window_end < self.window_start:
            raise SignalError("a signal's window cannot end before it begins.")
        if self.relevant_until < self.occurred_at:
            raise SignalError("a signal cannot stop being relevant before it occurred.")
        if not self.rationale.strip():
            raise SignalError(
                "a signal without a rationale is one a customer can neither understand nor "
                "challenge — and being challengeable is what makes it trustworthy."
            )

    @property
    def is_composite(self) -> bool:
        return len(self.contributing_event_types) > 1 or bool(self.constituent_signal_ids)

    def is_live_at(self, moment: datetime) -> bool:
        """Whether this reading is still current.

        A hypothesis stops being current in three ways: it is superseded by
        a better-evidenced one, its shelf life expires, or the workspace
        stops holding it. This covers the first two; the third is a profile
        question the query layer resolves.
        """
        return self.supersedes is None or moment <= self.relevant_until

    def enriched_by(self, constituents: tuple[UUID, ...]) -> Signal:
        return replace(self, constituent_signal_ids=constituents)

    def replacing(self, earlier: UUID) -> Signal:
        return replace(self, supersedes=earlier)


def signal_id(
    *,
    workspace_id: UUID,
    entity_id: UUID,
    signal_type: SignalType,
    contributing_event_ids: tuple[UUID, ...],
) -> UUID:
    """Derived from the hypothesis and its evidence, never allocated.

    **Deliberately not keyed on the profile version.** The identity is
    *this hypothesis over this evidence*: a profile change that keeps the
    type produces the same signal and inserts nothing, which is what should
    happen. A change that removes the type simply stops producing it, and
    historical signals stay interpretable through their recorded version.

    Business event ids are themselves derived from their evidence, so a
    signal survives a full pipeline rebuild.
    """
    evidence = "|".join(sorted(str(event_id) for event_id in contributing_event_ids))
    return uuid5(SIGNAL_NAMESPACE, f"{workspace_id}|{entity_id}|{signal_type.value}|{evidence}")


def relevant_until(occurred_at: datetime, relevance_window_days: int) -> datetime:
    return occurred_at + timedelta(days=relevance_window_days)

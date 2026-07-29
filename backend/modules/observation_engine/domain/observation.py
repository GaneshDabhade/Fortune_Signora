"""The Observation — Signora's unit of change.

**The Observation Engine detects change. It does not determine
significance.** (Permanent invariant, ratified 2026-07-29.) Whether a
headcount move of five matters is a question about commercial context; the
Business Event Engine owns a curated, versioned taxonomy where such a rule
can be stated and argued about. A threshold here would be a constant nobody
can justify that four modules trust within a year.

An observation says: *according to this provider, this attribute of this
entity moved from here to there, between these times.* Nothing more.

Three properties carry the design:

**Always per-provider.** An observation names who asserted it, and change is
only ever computed within one provider's series. Apollo reporting 120 on
Monday and CoreSignal 145 on Tuesday is *disagreement* — merging them would
manufacture growth that never happened, and correcting for it would mean
deciding which provider is authoritative, which is truth resolution.

**Identity is derived, not allocated.** Two runs over the same evidence
produce the same observation id, so deduplication is a primary-key
conflict rather than a code path.

**Immutable, refined by supersession.** A late-arriving claim makes an
earlier observation *less precise*, not false. The finer observations name
the one they replace, and it stays readable as what was believed then.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from typing import Any, Final
from uuid import UUID, uuid5

from modules.observation_engine.domain.semantics import (
    NUMERIC_ATTRIBUTES,
    ORDERED_ATTRIBUTES,
    AttributeKind,
    attribute_kind,
)
from modules.provider_normalization.public import ClaimAttribute

OBSERVATION_NAMESPACE: Final = UUID("0b5e7a4c-9d21-5f38-9a6e-1c7b2d4e8f30")
"""Fixed namespace for deterministic observation ids. **Never change it** —
every observation in every workspace would acquire a new identity, and the
next derivation would insert a duplicate of the entire table."""


class ObservationKind(StrEnum):
    VALUE_CHANGED = "value_changed"
    """A state attribute moved between two consecutive assertions."""

    OCCURRENCE_OBSERVED = "occurrence_observed"
    """Something the provider says happened, seen for the first time."""


class ObservationDirection(StrEnum):
    """Which way it went — structural, never a judgement of whether that is
    good. `INCREASED` on `OPEN_ROLES` is hiring; on churn it would be the
    opposite. Interpreting it is the Business Event Engine's job."""

    INCREASED = "increased"
    DECREASED = "decreased"
    CHANGED = "changed"
    """The value moved, but the vocabulary defines no order for it —
    an industry or a country reclassification."""

    OCCURRED = "occurred"
    """An occurrence. There is no previous value to have moved from."""


class ObservationError(ValueError):
    """An observation was constructed that violates an invariant."""


@dataclass(frozen=True, slots=True)
class Observation:
    """One change, with everything needed to reason about it directly.

    Downstream modules must never have to reconstruct a transition by
    re-reading the claim history: the previous value, the current value,
    the direction, the magnitude, the provider, the timing, and the entity
    are all carried here. Reconstruction would mean every consumer
    reimplementing this module's logic, and diverging from it.
    """

    id: UUID
    workspace_id: UUID
    entity_id: UUID
    provider: str
    attribute: ClaimAttribute
    kind: ObservationKind

    #: None for an occurrence, and that absence is meaningful rather than
    #: missing — there is genuinely nothing it moved from.
    previous_value: Any | None
    current_value: Any
    direction: ObservationDirection
    #: The arithmetic delta, for counts only. **Never a score**, never
    #: normalized, never comparable across attributes.
    magnitude: float | None

    #: When the provider says this was true.
    observed_at: datetime
    #: When the previous value was asserted. With `observed_at` it bounds
    #: the window the change occurred within — never narrower than the
    #: evidence supports.
    previous_observed_at: datetime | None
    #: When Signora learned it. Deliberately distinct from the row's audit
    #: timestamp: the gap from `observed_at` is **reporting lag**, which is
    #: real (intent data is reported weeks late) and which downstream
    #: reasons about. Collapsing the two makes a backfill indistinguishable
    #: from a burst of real activity.
    recorded_at: datetime

    evidence_claim_ids: tuple[UUID, ...]

    #: The coarser observation this one refines. Points **backwards**,
    #: forced by immutability: a forward pointer would have to be written
    #: onto the older row, which needs the UPDATE grant this table
    #: deliberately withholds.
    supersedes: UUID | None = None

    def __post_init__(self) -> None:
        if not self.evidence_claim_ids:
            raise ObservationError(
                f"observation {self.id} cites no claims. An observation that cannot be traced "
                "back to the evidence that produced it looks like knowledge without being it."
            )

        if self.kind is ObservationKind.VALUE_CHANGED:
            if self.previous_observed_at is None:
                raise ObservationError(
                    "a value change must name when the previous value was asserted; without it "
                    "the window the change occurred within is unbounded."
                )
            if self.direction is ObservationDirection.OCCURRED:
                raise ObservationError("OCCURRED is the direction of an occurrence, not a change.")
        elif self.previous_value is not None:
            raise ObservationError(
                "an occurrence has nothing to have moved from; a previous value here would be "
                "invented rather than observed."
            )

    def refining(self, coarser_id: UUID) -> Observation:
        return replace(self, supersedes=coarser_id)

    def describe(self) -> str:
        """Human-readable, for audit output and Timeline diagnosis."""
        if self.kind is ObservationKind.OCCURRENCE_OBSERVED:
            return f"{self.provider} reported {self.attribute} at {self.observed_at.date()}"
        return (
            f"{self.provider} reported {self.attribute} {self.direction} from "
            f"{self.previous_value!r} to {self.current_value!r} between "
            f"{self.previous_observed_at.date() if self.previous_observed_at else '?'} "
            f"and {self.observed_at.date()}"
        )


def canonical(value: Any) -> str:
    """A stable textual form of a claim value.

    Sorted keys, because two providers can report the same object with keys
    in a different order and that is the same value. Used only for identity;
    the stored value keeps its original shape.
    """
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def observation_id(
    *,
    workspace_id: UUID,
    entity_id: UUID,
    provider: str,
    attribute: ClaimAttribute,
    kind: ObservationKind,
    key: str,
) -> UUID:
    """Derived from what is observed, never allocated.

    **Deliberately keyed on values and times rather than on claim ids.**
    Claim ids are allocated when a mapper runs, so regenerating claims after
    a mapper fix would mint new ones — and a claim-keyed observation id would
    duplicate every observation in the workspace. Keying on the observed
    facts survives regeneration, which is the rollback path the whole
    pipeline depends on.
    """
    return uuid5(
        OBSERVATION_NAMESPACE,
        f"{workspace_id}|{entity_id}|{provider}|{attribute.value}|{kind.value}|{key}",
    )


def transition_key(
    *,
    previous_value: Any,
    previous_observed_at: datetime,
    current_value: Any,
    observed_at: datetime,
) -> str:
    return (
        f"{canonical(previous_value)}@{previous_observed_at.isoformat()}"
        f"->{canonical(current_value)}@{observed_at.isoformat()}"
    )


def direction_and_magnitude(
    attribute: ClaimAttribute, previous_value: Any, current_value: Any
) -> tuple[ObservationDirection, float | None]:
    """Both are structural readings of the vocabulary, never estimates.

    Magnitude exists only for counts, because subtracting two industries is
    meaningless and inventing a distance between them would be exactly the
    kind of manufactured number this platform refuses.
    """
    if attribute in NUMERIC_ATTRIBUTES:
        delta = float(current_value) - float(previous_value)
        return (
            ObservationDirection.INCREASED if delta > 0 else ObservationDirection.DECREASED,
            abs(delta),
        )

    order = ORDERED_ATTRIBUTES.get(attribute)
    if order is not None and str(previous_value) in order and str(current_value) in order:
        # A fact about the vocabulary, not a heuristic: revenue bands run
        # from `under_1m` to `over_1b` by definition.
        moved = order.index(str(current_value)) - order.index(str(previous_value))
        return (
            ObservationDirection.INCREASED if moved > 0 else ObservationDirection.DECREASED,
            None,
        )

    return ObservationDirection.CHANGED, None


def observation_kind_for(attribute: ClaimAttribute) -> ObservationKind:
    return (
        ObservationKind.VALUE_CHANGED
        if attribute_kind(attribute) is AttributeKind.STATE
        else ObservationKind.OCCURRENCE_OBSERVED
    )

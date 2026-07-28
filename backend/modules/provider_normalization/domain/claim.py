"""The Claim — Signora's unit of evidence.

**Normalization does not determine truth. Normalization preserves
evidence.** A claim says *this provider asserted this attribute had this
value, as of this time, and here is the raw record it came from.* Nothing
more. It does not rank, reconcile, resolve, or estimate.

Three invariants, all structural:

**Claims are immutable.** Never updated, never overwritten. New information
is a new claim. Historical evidence is an asset — Timeline, the Observation
Engine, and AI Reasoning all depend on being able to see what was believed
*when*. Enforced at three levels: frozen dataclasses, no update method on
the repository, and no `UPDATE` grant on the table.

**No claim exists without provenance.** Provider, raw record, observed_at,
mapper version, and payload provenance are all required. The evidence chain
begins here, and a claim that cannot be traced is worse than no claim — it
looks like knowledge.

**No confidence field.** Normalization has no authority to estimate it. A
number invented here with no evidence behind it would propagate into buying
scores as though it meant something. Confidence belongs to modules with
enough context to justify it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from modules.provider_normalization.domain.vocabulary import (
    ATTRIBUTE_VALUE_TYPES,
    ClaimAttribute,
    ClaimValue,
    observed_at_is_sane,
)


class ClaimError(ValueError):
    """A claim was constructed that violates an invariant."""


@dataclass(frozen=True, slots=True)
class SubjectHint:
    """Identity *hints*, never a resolved identity.

    Knowledge Graph owns entity resolution (M3A). Normalization only
    preserves what the provider supplied — deciding here that two hints are
    the same company would bury a resolution decision in a translation
    layer, where nothing can explain or revise it.
    """

    provider_external_id: str
    domain: str | None = None
    legal_name: str | None = None

    def __post_init__(self) -> None:
        if not self.provider_external_id.strip():
            raise ClaimError(
                "a subject hint needs at least the provider's own identifier; "
                "an unattributable claim is noise, not evidence"
            )

    @property
    def is_resolvable(self) -> bool:
        """Whether Knowledge Graph has anything to match on beyond the
        provider's private id — which is only useful within that provider."""
        return bool(self.domain or self.legal_name)


@dataclass(frozen=True, slots=True)
class ClaimSource:
    """Where a claim came from. Every field is required.

    ``payload_provenance`` carries the M2.0 designation through, so a claim
    derived from a development fixture stays identifiable for as long as
    fixtures exist — and a downstream conclusion built on one can be found
    when authentic payloads arrive.
    """

    provider: str
    raw_record_id: UUID
    mapper_version: str
    payload_provenance: str

    def __post_init__(self) -> None:
        missing = [
            name
            for name, value in (
                ("provider", self.provider),
                ("mapper_version", self.mapper_version),
                ("payload_provenance", self.payload_provenance),
            )
            if not str(value).strip()
        ]
        if missing:
            raise ClaimError(
                f"claim source is missing {missing}. The evidence chain begins here; "
                "a claim that cannot be traced looks like knowledge without being it."
            )


@dataclass(frozen=True, slots=True)
class Claim:
    """One piece of evidence. Immutable."""

    id: UUID
    workspace_id: UUID
    subject: SubjectHint
    attribute: ClaimAttribute
    value: ClaimValue
    #: When the provider says this was true — **not** when it was fetched.
    #: The gap between them is what a backfill looks like.
    observed_at: datetime
    source: ClaimSource

    def __post_init__(self) -> None:
        if not observed_at_is_sane(self.observed_at):
            raise ClaimError(
                f"observed_at for {self.attribute} is timezone-naive. Assuming UTC for a "
                "provider that meant local time silently shifts a trajectory by hours."
            )

        permitted = ATTRIBUTE_VALUE_TYPES[self.attribute]
        if not isinstance(self.value, permitted):
            raise ClaimError(
                f"{self.attribute} requires {[t.__name__ for t in permitted]}, "
                f"got {type(self.value).__name__}. Typed at construction so a bad mapping "
                "fails here rather than three modules downstream."
            )


def new_claim(
    *,
    workspace_id: UUID,
    subject: SubjectHint,
    attribute: ClaimAttribute,
    value: ClaimValue,
    observed_at: datetime,
    source: ClaimSource,
) -> Claim:
    return Claim(
        id=uuid4(),
        workspace_id=workspace_id,
        subject=subject,
        attribute=attribute,
        value=value,
        observed_at=observed_at,
        source=source,
    )

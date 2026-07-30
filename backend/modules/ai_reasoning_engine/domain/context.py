"""Everything deterministic a Decision Package needs, gathered in one place.

The **twelve of fifteen parts a model has nothing to do with**, plus the
evidence set the model will be shown. Assembled by an adapter that speaks the
pipeline's vocabulary, consumed by a use case that does not.

Its existence is what keeps `reason.py` thin. Without it the use case would
be reaching into a buying score to count providers, into a catalog to compose
limitations, and into a signal query for rejected readings — which is three
modules' vocabulary in a layer that should coordinate and decide nothing.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from modules.ai_platform.public import EvidenceSet
from modules.ai_reasoning_engine.domain.package import AlternativeReading
from modules.ai_reasoning_engine.domain.support import SupportBasis
from modules.ai_reasoning_engine.domain.temporal import TemporalExplanation


class ContextError(ValueError):
    """A context was assembled that could not support a conclusion."""


@dataclass(frozen=True, slots=True)
class ReasoningContext:
    """The deterministic half of a Decision Package, ready to compose."""

    #: The closed universe the model may reference. Workspace-stamped, and
    #: refused by the builder if it were ever mixed.
    evidence: EvidenceSet
    subject_id: UUID
    #: The immutable reading everything temporal is recoverable from.
    originating_buying_score_id: UUID

    support: SupportBasis
    temporal: TemporalExplanation
    alternative_readings: tuple[AlternativeReading, ...]

    #: Composed from the signal catalog for the types actually present, and
    #: snapshotted onto the package — a reviewed artifact changes by version.
    limitations: tuple[str, ...]
    suggested_validation: tuple[str, ...]
    catalog_version: int

    def __post_init__(self) -> None:
        # **No empty-evidence check here.** `EvidenceSet` already refuses to
        # be built with no facts — *"a model given nothing to reference can
        # only produce something ungrounded"* — so a repeat of that check
        # could never fire. Found at T127 by a test that could not reach it.
        if not self.limitations or not self.suggested_validation:
            raise ContextError(
                "the signal catalog supplied no limitations or no validation steps. Both are "
                "required there, so an empty one here means the catalog was not consulted."
            )

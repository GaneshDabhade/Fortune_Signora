"""The signal catalog — Signora's vocabulary of commercial hypotheses.

**Business events describe objective business phenomena. Signals describe
customer-specific commercial hypotheses.** (Permanent principle, ratified
2026-07-29.) Signals are therefore the **first subjective layer** in the
pipeline — and that subjectivity has to stay explicit, explainable, and
constrained. Everything above the Signal Engine is globally true;
everything below must remain traceable back to globally true information.

**The catalog belongs to Signora; profiles belong to customers.** That
split is decided by *ownership*, not by technology: our language ships
with a release and is reviewed in a pull request, while a customer's
commercial position cannot be made to wait for one.

**A workspace can never invent a signal type.** It configures relevance
over this catalog. The constraint is not a limitation to relax later — a
per-workspace vocabulary would mean AI Reasoning could not be prompted
about `EXPANSION_OPPORTUNITY`, benchmarks could not compare customers, and
support could not answer a question about a signal without first learning
that customer's private dialect.

Every entry declares a **detection strategy** rather than a detection
procedure. The catalog states domain semantics — *what kind of evidence
supports this hypothesis* — and leaves the mechanics to `domain/rules/`,
so an improved implementation never changes what a signal *means*.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final

from pydantic import BaseModel, ConfigDict, Field

from modules.business_event_engine.public import BusinessEventType


class DetectionStrategy(StrEnum):
    """What kind of evidence supports a hypothesis — not how it is found."""

    SINGLE_EVENT = "single_event"
    """One contributing business event is grounds enough."""

    COMPOSITE = "composite"
    """Several **distinct** contributing event types within a window. Three
    hiring surges are one phenomenon reported repeatedly, not three
    independent grounds for believing a company is expanding."""


class SignalType(StrEnum):
    """The global vocabulary. **Adding one is a product decision.**"""

    EXPANSION_OPPORTUNITY = "expansion_opportunity"
    BUDGET_UNLOCKED = "budget_unlocked"
    DISPLACEMENT_OPPORTUNITY = "displacement_opportunity"
    MODERNIZATION_UNDERWAY = "modernization_underway"
    NEW_DECISION_MAKER = "new_decision_maker"
    DECISION_MAKER_DEPARTED = "decision_maker_departed"
    ACTIVE_EVALUATION = "active_evaluation"
    CONSOLIDATION_UNDERWAY = "consolidation_underway"
    CONTRACTION_RISK = "contraction_risk"


class Relevance(StrEnum):
    """How central a hypothesis is to **this** workspace's commercial
    interest.

    A category, declared per workspace and never computed — the same
    discipline as `MatchStrength`, and for the same reason: a number
    invites weighting, weighting invites thresholds, and a threshold here
    would be a propensity judgement in the wrong module.

    The Buying Score Engine maps these to weights in *its* configuration,
    which is where "how much does this matter" belongs.
    """

    PRIMARY = "primary"
    SUPPORTING = "supporting"
    CONTEXTUAL = "contextual"
    IGNORED = "ignored"
    """Explicitly not relevant here. Distinct from absence: "we decided we
    do not care" and "nobody has configured this" are different facts, and
    only one of them should ever be revisited."""


class CatalogError(Exception):
    """The catalog artifact is malformed, or a type is missing from it.

    Raised at load time rather than at first generation: a catalog that is
    wrong should stop a deployment, not silently stop producing one type.
    """


class SignalTypeDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    key: SignalType
    title: str
    hypothesis: str
    """What this type *proposes*, written for a customer and phrased as a
    possibility. A signal does not assert; it suggests. If this sentence
    reads as a fact, the type has drifted into the Business Event
    Engine's territory."""

    why_it_matters: str
    detection_strategy: DetectionStrategy
    contributing_event_types: tuple[BusinessEventType, ...] = Field(min_length=1)
    """Business event types — **referenced directly**, never re-derived
    from observations. Two definitions of one concept diverge within a
    year."""

    minimum_contributors: int = Field(ge=1)
    window_days: int = Field(gt=0)
    relevance_window_days: int = Field(gt=0)
    """How long this interpretation stays current. A hypothesis has a shelf
    life: a hiring surge from eight months ago is weaker grounds than last
    week's, and capturing that here keeps temporal interpretation out of
    downstream modules."""

    default_relevance: Relevance

    @property
    def is_composite(self) -> bool:
        return self.detection_strategy is DetectionStrategy.COMPOSITE


class SignalCatalog(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    version: int
    types: tuple[SignalTypeDefinition, ...]
    note: str = Field(default="", alias="_comment")

    def definition(self, key: SignalType) -> SignalTypeDefinition:
        for definition in self.types:
            if definition.key is key:
                return definition
        raise CatalogError(
            f"'{key}' is not declared in signal catalog v{self.version}. A rule producing a type "
            "the catalog does not define is a hypothesis nobody can explain."
        )

    def validate_complete(self, produced: frozenset[SignalType]) -> None:
        declared = {definition.key for definition in self.types}

        if orphan_types := declared - produced:
            raise CatalogError(
                f"declared with no rule to produce them: {sorted(t.value for t in orphan_types)}. "
                "A type nobody produces is a promise the product cannot keep."
            )
        if orphan_rules := produced - declared:
            raise CatalogError(
                f"produced but not declared: {sorted(t.value for t in orphan_rules)}. "
                "A rule with no declaration is a hypothesis nobody reviewed."
            )


CURRENT_CATALOG_VERSION: Final = 1
"""The version this build ships. Recorded on every signal, because *why
does this exist* has two halves and this is one of them."""

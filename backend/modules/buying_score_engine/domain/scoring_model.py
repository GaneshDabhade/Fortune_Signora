"""The scoring model — how much attention each hypothesis earns.

**The third layer of the platform's configuration ownership split.** The
signal catalog is Signora's (what hypotheses exist and what they mean); the
signal profile is the customer's (which ones they care about); the scoring
model is the customer's too (how much attention caring earns).

It is deliberately **not** folded into the signal profile. They answer
different questions at different cadences — relevance is *"do we care about
this hypothesis?"*, weight is *"how much attention does caring earn?"* —
and, decisively, every signal records the profile version that produced it.
Folding weights in would mean tuning a score mints a new *profile* version
and churns the explanation of every historical signal. **A tuning knob must
not rewrite the audit trail of a neighbouring module.**

Two rules the model obeys, both structural rather than advisory:

**Every number is an integer, and every product is integer arithmetic.** A
buying score must reproduce from its own ledger *exactly* (AC-51), and
floating point cannot promise that. Weights are points; multipliers are
percentages; the single division happens once, at normalization.

**Posture is Signora's, never the customer's.** A workspace tunes weights,
multipliers, and band boundaries. It may never invert what a signal type
means commercially — whether `CONTRACTION_RISK` reads as contractionary is
a fact about the language, not a commercial preference, and letting a
workspace flip it would make `contested` incomparable across the platform.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import StrEnum
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, model_validator

from modules.signal_engine.public import Relevance, SignalType

CURRENT_MODEL_VERSION: Final = 1
"""The artifact version this build ships. Recorded on every score, because
*why is this number what it is* has two halves and this is one of them."""

PERCENT: Final = 100
"""The scale multipliers are expressed in. Named because it appears in the
arithmetic, and an unexplained `100` there would read as a threshold."""


class Posture(StrEnum):
    """What a hypothesis implies commercially.

    **Never summed into the score.** Posture is what makes contradiction
    *visible*; folding it into the arithmetic as a sign is exactly the
    netting this module refuses.
    """

    EXPANSIONARY = "expansionary"
    CONTRACTIONARY = "contractionary"
    NEUTRAL = "neutral"


class ScoringModelError(Exception):
    """The scoring model artifact is malformed, or a type is missing from it.

    Raised at load time rather than at first scoring: a model that is wrong
    should stop a deployment, not silently stop weighting one type.
    """


class AgeBand(BaseModel):
    """One step of the decay curve.

    **Step decay, not linear.** A stored score is a snapshot with a stated
    validity period, and that contract only holds if the value is *constant*
    across the interval. Any decay changing continuously with wall-clock
    time makes the stored number wrong the instant after it is written —
    unless scores are recomputed continuously, which the platform has
    deliberately rejected. A discrete curve is the only kind that lets
    `valid_until` state something true.

    It is also the only kind a customer can argue with: *"we count evidence
    past a month at 60%"* is a rule; `×0.7213` is a slope.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    through_percent: int = Field(gt=0, le=PERCENT)
    """Where this band ends, as a percentage of **the signal type's own
    relevance window**. A fraction rather than a fixed number of days, so
    the catalog's existing per-type judgement about how long a hypothesis
    stays current is reused instead of duplicated beside it."""

    multiplier_percent: int = Field(ge=0, le=PERCENT)
    label: str
    """The word that appears in the ledger and in front of a customer."""


class TypeWeight(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    key: SignalType
    posture: Posture
    base_weight: int = Field(ge=0)
    """Attention in points, before relevance and age. **Unsigned, for every
    posture.** A contraction risk earns attention just as an expansion
    opportunity does; the difference is recorded as posture and surfaced as
    `contested`, never as a minus sign."""


class ScoringModel(BaseModel):
    """A complete, versioned statement of how attention is computed."""

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    version: int
    ceiling: int = Field(gt=0)
    """The point total that reads as 100. A declared, reviewable constant in
    data — the same discipline that put every materiality threshold in the
    taxonomy's parameters — never a literal in scoring code."""

    steady_delta: int = Field(ge=0)
    """How far a score may move and still read as `STEADY`."""

    age_bands: tuple[AgeBand, ...] = Field(min_length=1)
    relevance_multipliers: dict[Relevance, int]
    types: tuple[TypeWeight, ...] = Field(min_length=1)
    note: str = Field(default="", alias="_comment")

    @model_validator(mode="after")
    def _check(self) -> ScoringModel:
        thresholds = [band.through_percent for band in self.age_bands]
        if thresholds != sorted(set(thresholds)):
            raise ValueError(
                "age bands must be ordered and distinct by `through_percent`; overlapping or "
                "unordered bands make the band a signal falls into ambiguous."
            )
        if thresholds[-1] != PERCENT:
            raise ValueError(
                "the last age band must end at 100% of the relevance window. A curve stopping "
                "short leaves live signals with no band, and they would silently score nothing."
            )
        if Relevance.IGNORED in self.relevance_multipliers:
            raise ValueError(
                "`ignored` has no multiplier: it means the hypothesis is not held here at all, "
                "so no signal of that type exists to weigh."
            )
        missing = {r for r in Relevance if r is not Relevance.IGNORED} - set(
            self.relevance_multipliers
        )
        if missing:
            raise ValueError(
                f"no multiplier declared for {sorted(r.value for r in missing)}. A held relevance "
                "with no weight would score zero, which is indistinguishable from ignoring it."
            )
        return self

    def weight_for(self, signal_type: SignalType) -> TypeWeight:
        for weight in self.types:
            if weight.key is signal_type:
                return weight
        raise ScoringModelError(
            f"'{signal_type}' has no weight in scoring model v{self.version}. A signal the model "
            "cannot weigh would silently contribute nothing, which looks exactly like an account "
            "with no evidence."
        )

    def relevance_multiplier(self, relevance: Relevance) -> int:
        try:
            return self.relevance_multipliers[relevance]
        except KeyError as exc:
            raise ScoringModelError(
                f"'{relevance}' has no multiplier in scoring model v{self.version}."
            ) from exc

    def validate_covers(self, catalog_types: frozenset[SignalType]) -> None:
        """Every type the catalog declares must be weighable, and no more.

        Checked at startup: a catalog type with no weight scores nothing,
        and an account with a strong hypothesis nobody weighted looks
        identical to an account where nothing happened.
        """
        declared = {weight.key for weight in self.types}
        if unweighted := catalog_types - declared:
            raise ScoringModelError(
                f"declared in the signal catalog but unweighted: "
                f"{sorted(t.value for t in unweighted)}. A hypothesis nobody weighted contributes "
                "nothing, and reads as an account where nothing happened."
            )
        if unknown := declared - catalog_types:
            raise ScoringModelError(
                f"weighted but not in the signal catalog: {sorted(t.value for t in unknown)}. "
                "A weight for a type that cannot be produced is a rule nobody reviewed."
            )

    def band_boundaries(self, occurred_at: datetime, relevant_until: datetime) -> list[datetime]:
        """The moments at which this signal's contribution changes.

        Every boundary is a fraction of the signal's own window, and the
        final one **is** its expiry — so expiry is simply the last band
        transition rather than a second mechanism beside them. That is what
        lets a score state one honest `valid_until`.
        """
        window = relevant_until - occurred_at
        return [
            occurred_at + timedelta(seconds=window.total_seconds() * band.through_percent / PERCENT)
            for band in self.age_bands
        ]

    def band_at(self, occurred_at: datetime, relevant_until: datetime, moment: datetime) -> AgeBand:
        """Which band a signal falls in. Never extrapolates past expiry —
        a caller asking about an expired signal has already made a mistake
        the arithmetic should not paper over."""
        boundaries = self.band_boundaries(occurred_at, relevant_until)
        for band, boundary in zip(self.age_bands, boundaries, strict=True):
            if moment <= boundary:
                return band
        raise ScoringModelError(
            "a signal past its relevance window has no age band. An expired hypothesis is not "
            "worth a little — it is not held at all, and must be excluded before scoring."
        )

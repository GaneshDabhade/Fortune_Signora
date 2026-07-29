"""The Buying Score — how much commercial attention an account deserves.

**Permanent architectural principle, ratified 2026-07-29:**

> Buying scores **prioritize commercial attention**. They do not predict
> purchasing behaviour. They do not estimate probability. They do not
> resolve contradiction. They summarize *explainable* commercial attention.

This is the pipeline's **first intentional reduction**. Every stage before
it adds information and destroys none; this one turns many live hypotheses
into a single number, which is both its product value and the first real
opportunity the architecture has had to lose something it cannot recover.

Four properties keep that safe:

**The score is projected from its ledger, never assembled beside it.** Read
the dependency as ledger → score. A score is constructed only through
`projected_from`, and its value is whatever the ledger says it is — there
is no path that lets a number and its explanation disagree.

**It is a reading with a stated validity, not a live gauge.** Between
`computed_at` and `valid_until` the stored value is *exactly correct*, not
merely recent. That contract is what forced step decay: any curve changing
continuously with the clock would make the stored number wrong the instant
after it was written.

**It is immutable.** A recomputation is a new score naming the one it
replaces, so what a customer was told in March survives being told
something different in April. Trend is a fact about that history.

**It is never the canonical representation of an account.** There are no
account attributes here — no name, no domain, no industry. A score row that
grew them would become a de facto account record within a year, and
consumers would read it instead of the intelligence it summarizes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Final
from uuid import UUID, uuid5

from modules.buying_score_engine.domain.ledger import ContributionLedger

BUYING_SCORE_NAMESPACE: Final = UUID("6d3f0a94-51c7-5b28-9e14-0a7b62d38f5c")
"""Fixed namespace for deterministic identity. **Never change it** — every
score in every workspace would acquire a new identity, and the next
computation would insert a duplicate of the entire table."""

PAYLOAD_VERSION: Final = 1


class Trend(StrEnum):
    """Direction against the immediately previous reading.

    A company at 71 on the way up and one at 71 on the way down warrant
    opposite actions, and a consumer given only today's number cannot tell
    them apart.
    """

    RISING = "rising"
    STEADY = "steady"
    FALLING = "falling"


class ScoreTrigger(StrEnum):
    """Why this score exists. Recorded because a number that moved for an
    unexplainable reason is a number nobody trusts — and *"nothing has
    happened here for six weeks"* is real commercial information."""

    SIGNAL_GENERATED = "signal_generated"
    SIGNAL_SUPERSEDED = "signal_superseded"
    MODEL_CHANGED = "model_changed"
    PROFILE_CHANGED = "profile_changed"
    EVIDENCE_AGED = "evidence_aged"


class BuyingScoreError(ValueError):
    """A score was constructed that violates an invariant."""


@dataclass(frozen=True, slots=True)
class BuyingScore:
    id: UUID
    workspace_id: UUID
    entity_id: UUID

    #: 0–100. **Not a probability and not a prediction** — an ordering of
    #: commercial attention, normalized against a ceiling the scoring model
    #: declares.
    value: int
    trend: Trend
    #: Signed movement against the previous reading; 0 for a first score.
    delta: int

    #: The authoritative explanation. Every field above is derived from it.
    ledger: ContributionLedger

    #: Opposing readings are both live. **Never reduces the score** — a
    #: fought-over account warrants more attention, not average attention.
    contested: bool
    #: The outweighed reading's signals, named rather than counted.
    dissenting_signal_ids: tuple[UUID, ...]

    computed_at: datetime
    #: The next moment the arithmetic provably changes. The stored value is
    #: exactly correct until here.
    valid_until: datetime | None
    #: The evidence-derived moment the ledger's composition last changed.
    basis_at: datetime
    trigger: ScoreTrigger

    #: The workspace's own weighting version; `0` when it has authored none
    #: and the shipped artifact applies.
    scoring_model_version: int
    #: Signora's shipped artifact version. Both halves are needed: *"our
    #: weights v1, their tuning v3"* explains a number that neither does
    #: alone.
    model_artifact_version: int
    profile_version: int
    payload_version: int = PAYLOAD_VERSION
    #: The score this one replaces. Points **backwards**, forced by
    #: immutability — a forward pointer would have to be written onto the
    #: older row, which needs the UPDATE grant this table withholds.
    supersedes: UUID | None = None

    def __post_init__(self) -> None:
        if self.value != self.ledger.value():
            raise BuyingScoreError(
                f"score {self.id} reads {self.value} but its ledger reproduces "
                f"{self.ledger.value()}. A ledger that does not reproduce its own score is a "
                "corrupt explanation, not a discrepancy to reconcile later."
            )
        if self.contested != self.ledger.is_contested:
            raise BuyingScoreError(
                f"score {self.id} disagrees with its ledger about whether it is contested. "
                "Contradiction is detected from the evidence, never asserted alongside it."
            )
        if self.valid_until is not None and self.valid_until < self.computed_at:
            raise BuyingScoreError(
                f"score {self.id} expires before it was computed; its stated validity period "
                "would never have held."
            )

    @classmethod
    def projected_from(
        cls,
        ledger: ContributionLedger,
        *,
        workspace_id: UUID,
        entity_id: UUID,
        computed_at: datetime,
        basis_at: datetime,
        trigger: ScoreTrigger,
        scoring_model_version: int,
        model_artifact_version: int,
        profile_version: int,
        steady_delta: int,
        previous: BuyingScore | None = None,
    ) -> BuyingScore:
        """Project a score from its ledger. **The only way to build one.**

        `basis_at` is supplied rather than read from the ledger because an
        empty ledger has none of its own: when the last contribution
        expires, the moment the composition changed is the previous score's
        `valid_until` — still evidence-derived, just derived from the
        reading being replaced.
        """
        value = ledger.value()
        delta = 0 if previous is None else value - previous.value
        return cls(
            id=score_id(
                workspace_id=workspace_id,
                entity_id=entity_id,
                scoring_model_version=scoring_model_version,
                model_artifact_version=model_artifact_version,
                profile_version=profile_version,
                contributing_signal_ids=ledger.contributing_signals(),
                basis_at=basis_at,
            ),
            workspace_id=workspace_id,
            entity_id=entity_id,
            value=value,
            trend=_trend(delta, steady_delta, first=previous is None),
            delta=delta,
            ledger=ledger,
            contested=ledger.is_contested,
            dissenting_signal_ids=ledger.dissent(),
            computed_at=computed_at,
            valid_until=ledger.valid_until(),
            basis_at=basis_at,
            trigger=trigger,
            scoring_model_version=scoring_model_version,
            model_artifact_version=model_artifact_version,
            profile_version=profile_version,
            supersedes=None if previous is None else previous.id,
        )

    def is_valid_at(self, moment: datetime) -> bool:
        """Whether the stored value is still exactly correct.

        The one question a score can answer about itself. Whether a *later*
        score has replaced it is a fact about other rows — `supersedes`
        points backwards — and a method here that appeared to answer it
        would be believed, and would be wrong.
        """
        return self.valid_until is None or moment <= self.valid_until


def _trend(delta: int, steady_delta: int, *, first: bool) -> Trend:
    """A first reading is `STEADY`: there is nothing to have moved from, and
    calling it `RISING` would invent a history the account does not have."""
    if first or abs(delta) <= steady_delta:
        return Trend.STEADY
    return Trend.RISING if delta > 0 else Trend.FALLING


def score_id(
    *,
    workspace_id: UUID,
    entity_id: UUID,
    scoring_model_version: int,
    model_artifact_version: int,
    profile_version: int,
    contributing_signal_ids: tuple[UUID, ...],
    basis_at: datetime,
) -> UUID:
    """Derived from what produced the score, never allocated.

    Keyed on the configuration in force, the signals contributing, and the
    evidence-derived moment their composition last changed — so an identical
    situation computes an identical id and inserts nothing, while a band
    rolling over or a signal arriving produces a genuinely new reading.

    Signal ids are themselves derived from their evidence, which are derived
    from theirs, so a score survives a full pipeline rebuild.
    """
    signals = "|".join(sorted(str(signal_id) for signal_id in contributing_signal_ids))
    return uuid5(
        BUYING_SCORE_NAMESPACE,
        f"{workspace_id}|{entity_id}|{model_artifact_version}|{scoring_model_version}|"
        f"{profile_version}|{signals}|{basis_at.isoformat()}",
    )

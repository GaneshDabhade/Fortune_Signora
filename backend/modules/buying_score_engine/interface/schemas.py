"""HTTP response schemas for the Buying Score Engine.

**The answer to *"why this account?"*** — the second customer journey, and the
first surface in the repository that shows a number *and* the arithmetic that
produced it. The attention list answers *which* accounts; this answers *why*,
which is the question a seller has to be able to defend in front of somebody
else.

Deliberately separate from the domain entities, even where field-identical:
coupling the wire contract to the domain model makes a domain refactor a
client-breaking change (19-api-conventions.md).

**Every number here is computed by the server, never by the browser.** The raw
point total, the ceiling, the per-posture split and which entries dissent are
all derived here, because a figure assembled in a client is a second
implementation of the arithmetic — and the ledger exists precisely so there is
exactly one. A customer can check the score with two integers and a division;
they should never have to reproduce it to see it.

**What did not survive the *"would someone selling understand why this is
present?"* test**, applied here as it was to the attention row:

- `id` and `supersedes` — a score's identity and the reading it replaced. Real
  and immutable, and there is nothing yet that can be opened by following one.
- `basis_at` — the evidence-derived moment the ledger last changed. It exists
  so replay reproduces byte-identical score ids; it answers no commercial
  question.
- `scoring_model_version`, `model_artifact_version`, `profile_version` — the
  configuration in force. A support question, the same category as the
  attention row's `policy_version`.
- `base_weight`, `relevance_multiplier`, `age_multiplier` — the three factors
  behind one entry's points. **Already in `reason`**, rendered as the words a
  customer can argue with rather than the integers they would have to multiply.
- `band_started_at` / `band_ends_at` — each entry's decay schedule. The
  earliest of them across the whole ledger is `valid_until`, which is the form
  of that fact anybody asks for.
- `signal_type` — the hypothesis key. Left off for a different reason from the
  rest, and the reason is worth stating: **the Signal Catalog owns what a
  signal type is called**, and `reason` already carries that title, rendered
  server-side. Putting the raw key on the wire beside it invites a client to
  build its own titles, and then two places would define what
  `displacement_opportunity` means to a customer. `posture`, `relevance` and
  `evidence_age` are kept because each is a short, closed vocabulary the screen
  renders as its own affordance rather than as a phrase.

None of them are secret. They are simply not part of *this* answer.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from modules.buying_score_engine.domain.ledger import Contribution
from modules.buying_score_engine.domain.score import BuyingScore, ScoreTrigger, Trend
from modules.buying_score_engine.domain.scoring_model import Posture, ScoringModel
from modules.signal_engine.public import Relevance, SignalType


class ContributionResponse(BaseModel):
    """One line of the explanation — a single business event's contribution."""

    model_config = ConfigDict(frozen=True)

    business_event_id: UUID = Field(
        description=(
            "The thing that happened. The unit of contribution is the event rather than "
            "the hypothesis reading it, so the same grounds understood two ways cannot "
            "count twice."
        )
    )
    signal_id: UUID = Field(
        description=(
            "The hypothesis this event was read through. Both identifiers are here "
            "because they are what a citation resolves to — the point at which a claim "
            "becomes a record you can read."
        )
    )
    posture: Posture = Field(
        description=(
            "What this reading implies commercially — expansionary, contractionary or "
            "neutral. Never folded into the score as a sign: two accounts can score the "
            "same and mean opposite things, and this is where that survives."
        )
    )
    relevance: Relevance = Field(
        description=(
            "How central this hypothesis is to your ideal customer profile. Your "
            "declaration, not a measurement."
        )
    )
    evidence_age: str = Field(
        description=(
            "How far through its useful life this evidence is: fresh, recent or ageing. "
            "Attention decays in steps rather than continuously, so a score stays exactly "
            "correct for a stated period instead of drifting the moment it is written."
        )
    )

    points: int = Field(
        description=(
            "What this line added, after relevance and age. Zero when the line is not "
            "counted."
        )
    )
    counted: bool = Field(
        description=(
            "Whether these points are in the total. False means the same business event "
            "was already counted through a higher-weighted hypothesis — kept in the list "
            "with its reason, because a zero you can read beats a row that vanished."
        )
    )
    dissenting: bool = Field(
        description=(
            "Whether this line belongs to the outweighed reading of a contested account. "
            "Named rather than netted away: being told which evidence disagrees is what "
            "lets you go and read it."
        )
    )
    reason: str = Field(
        description=(
            "The line in plain language, rendered from the same fields an auditor checks "
            "— so the sentence and the arithmetic cannot drift apart."
        )
    )

    @classmethod
    def from_domain(
        cls, entry: Contribution, *, dissenting: bool
    ) -> "ContributionResponse":
        return cls(
            business_event_id=entry.business_event_id,
            signal_id=entry.signal_id,
            posture=entry.posture,
            relevance=entry.relevance,
            evidence_age=entry.age_band,
            points=entry.contribution,
            counted=entry.counted,
            dissenting=dissenting,
            reason=entry.reason,
        )


class AccountScoreResponse(BaseModel):
    """One account's score, with everything needed to challenge it."""

    model_config = ConfigDict(frozen=True)

    account_id: UUID = Field(
        description="The company this reading is about. Resolve its name from the "
        "account-identities endpoint, as the attention list does."
    )

    score: int = Field(
        description=(
            "Commercial attention, 0–100. An ordering, not a probability and not a "
            "prediction — 80 means this deserves your time before a 60 does, never that "
            "it is 80% likely to buy."
        )
    )
    trend: Trend = Field(
        description=(
            "Which way it last moved. An account at 71 on the way up and one at 71 on "
            "the way down warrant opposite actions."
        )
    )
    score_change: int = Field(
        description="Signed movement against the previous reading; 0 for a first score."
    )
    trigger: ScoreTrigger = Field(
        description=(
            "Why this reading exists — new evidence, evidence replaced, evidence ageing "
            "out, or a change you made to your scoring model or profile."
        )
    )
    contested: bool = Field(
        description=(
            "Whether opposing readings are both live. This never reduces the score: a "
            "fought-over account warrants more attention, not average attention."
        )
    )

    computed_at: datetime = Field(
        description="When this reading was taken. It has not changed since — a "
        "recomputation produces a new reading rather than editing this one."
    )
    valid_until: datetime | None = Field(
        description=(
            "The next moment the arithmetic provably changes. Until then the score is "
            "exactly correct rather than merely recent. Null when nothing is "
            "contributing, so nothing can change without new evidence arriving."
        )
    )
    is_current: bool = Field(
        description=(
            "Whether that validity period still holds. An expired reading is shown "
            "rather than hidden — that the evidence went cold is information, and "
            "concealing it would be worse than showing a number that admits it is old."
        )
    )

    points: int = Field(
        description=(
            "The raw point total of the counted lines below, before normalising. With "
            "`ceiling`, this is the whole of the arithmetic: score = points ÷ ceiling, "
            "capped at 100."
        )
    )
    ceiling: int = Field(
        description=(
            "The point total that reads as 100, taken from the scoring model that was in "
            "force when this was computed — never today's, or a historical score would be "
            "re-explained through weights it never used."
        )
    )
    attention_by_posture: dict[Posture, int] = Field(
        description=(
            "Counted points split by what they imply commercially. Deliberately not "
            "summed into the score: this is the only place where the difference between "
            "a quiet account and a contested one survives."
        )
    )

    contributions: tuple[ContributionResponse, ...] = Field(
        description=(
            "Every line that produced the score, largest contribution first — including "
            "the ones that counted nothing, with the reason they did not."
        )
    )

    @classmethod
    def from_domain(cls, score: BuyingScore, *, now: datetime) -> "AccountScoreResponse":
        dissent = frozenset(score.dissenting_signal_ids)
        return cls(
            account_id=score.entity_id,
            score=score.value,
            trend=score.trend,
            score_change=score.delta,
            trigger=score.trigger,
            contested=score.contested,
            computed_at=score.computed_at,
            valid_until=score.valid_until,
            is_current=score.is_valid_at(now),
            points=score.ledger.total(),
            ceiling=score.ledger.ceiling,
            attention_by_posture=score.ledger.posture_summary(),
            contributions=tuple(
                ContributionResponse.from_domain(
                    entry, dissenting=entry.signal_id in dissent
                )
                for entry in score.ledger.entries
            ),
        )


class TypePostureResponse(BaseModel):
    """What one kind of hypothesis implies commercially.

    **The weighting is deliberately not here.** How many points a type earns is
    an input to the score, and a client that could read it could rank accounts
    itself — a second ranking, disagreeing with the one this module computes.
    Posture is different: it is a closed vocabulary a screen renders as an
    affordance, exactly as the ledger's own `posture` field already is.
    """

    model_config = ConfigDict(frozen=True)

    key: SignalType = Field(
        description=(
            "The hypothesis type. **A key, not a name** — the Signal Engine's catalog is "
            "the one place a type is named, and a second title here would be a second "
            "vocabulary."
        )
    )
    posture: Posture = Field(
        description=(
            "expansionary, contractionary or neutral. **Signora's, never the customer's** "
            "— a workspace tunes weights and cannot redefine what a contraction means."
        )
    )


class ScoringModelResponse(BaseModel):
    """What each kind of hypothesis implies, in the version actually in force.

    **A property of the model, not of any account.** The per-account read above
    answers *why is this one scored where it is*; this answers *what does this
    kind of finding mean*, which a surface needs before it has an account in
    hand — the Home attention card renders severity from it, and severity has to
    be right on the first paint.

    **Resolved rather than shipped.** The response is the workspace's values
    over Signora's artifact, so a workspace that has tuned nothing still gets a
    complete answer and one that has cannot see a weight it did not set.
    """

    model_config = ConfigDict(frozen=True)

    version: int = Field(
        description=(
            "The model version in force. Present so a client can tell a changed meaning "
            "from a changed account — a posture that moved between two reads is a model "
            "change, not news about a company."
        )
    )
    types: tuple[TypePostureResponse, ...] = Field(
        description="Every type the model weights, in the artifact's own order."
    )

    @classmethod
    def from_domain(cls, model: ScoringModel) -> "ScoringModelResponse":
        return cls(
            version=model.version,
            types=tuple(
                TypePostureResponse(key=weight.key, posture=weight.posture)
                for weight in model.types
            ),
        )


__all__ = [
    "AccountScoreResponse",
    "ContributionResponse",
    "ScoringModelResponse",
    "TypePostureResponse",
]

"""Why now · why not earlier · what changed · how fresh.

**Nothing here is inferred, and nothing here is new.** Every one of these
answers already exists in the repository, computed deterministically by the
module that owns it, and this file composes them into sentences a customer
can read. Asking a model to narrate history the platform already records
would replace a fact with a guess — and a guess about *causality*, which is
the least checkable kind there is.

Where each answer comes from, and who owns it:

| Question | Fact | Owner |
|---|---|---|
| Why now? | `BuyingScore.trigger` | Buying Score Engine |
| Why not earlier? | `basis_at`, `supersedes` | Buying Score Engine |
| What changed? | `delta`, `trend` | Buying Score Engine |
| How fresh? | `EvidenceState`, `valid_until` | Opportunity Engine |

**Not one of these is redefined here.** `ScoreTrigger` exists precisely
because *"a number that moved for an unexplainable reason is a number nobody
trusts"*; re-deriving why a reading exists would be a second answer to a
question already answered, and the two would disagree within a year.

**This holds no state of its own and needs no snapshot.** A materialized
Decision Package normally has to record what a customer was shown, because
the source may change underneath it — but `buying_score` is immutable, so a
superseded reading stays readable forever and these answers are recoverable
from `originating_buying_score_id` alone. Only the *catalog*-sourced parts of
the package need snapshotting, because a reviewed artifact changes by
version while a score never changes at all.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from modules.buying_score_engine.public import ScoreTrigger, Trend
from modules.opportunity_engine.public import EvidenceState

#: What each trigger means to someone who does not work here. The phrasing is
#: M9's — turning a recorded fact into a readable sentence is presentation,
#: and presentation is this module's job. The *fact* remains the Buying Score
#: Engine's, and is never re-derived.
_WHY: dict[ScoreTrigger, str] = {
    ScoreTrigger.SIGNAL_GENERATED: "a new signal was found in this account's evidence",
    ScoreTrigger.SIGNAL_SUPERSEDED: "an existing signal was replaced by a better-supported one",
    ScoreTrigger.MODEL_CHANGED: "your workspace changed how much weight each signal carries",
    ScoreTrigger.PROFILE_CHANGED: "your workspace changed which signals matter here",
    ScoreTrigger.EVIDENCE_AGED: "existing evidence passed the point where it still counts fully",
}


class TemporalError(ValueError):
    """A temporal explanation was constructed that cannot describe a history."""


@dataclass(frozen=True, slots=True)
class TemporalExplanation:
    """The four temporal questions, answered from recorded facts alone.

    Every field is copied from one immutable buying score. Nothing is
    computed here that was not computed upstream — this type exists to make
    the answers *presentable*, not to produce them.
    """

    trigger: ScoreTrigger
    #: The evidence-derived moment the ledger's composition last changed.
    #: **This is what makes "why not earlier" answerable**: before it, the
    #: previous reading was still the correct one.
    basis_at: datetime
    computed_at: datetime
    #: Change against the immediately previous reading. Zero on a first
    #: reading, where there is nothing to differ from.
    delta: int
    trend: Trend
    evidence_state: EvidenceState
    #: `None` when nothing is contributing, which means nothing changes
    #: without a new signal — and a new signal publishes an event.
    valid_until: datetime | None
    #: The reading this one replaced. `None` means this account has never
    #: been read before, which is a different answer to *"why not earlier"*
    #: rather than a missing one.
    supersedes: UUID | None

    def __post_init__(self) -> None:
        if self.supersedes is None and self.delta != 0:
            raise TemporalError(
                f"a first reading cannot differ by {self.delta} from a reading that does not "
                "exist. Either this supersedes something, or its delta is zero."
            )
        if self.valid_until is not None and self.valid_until < self.computed_at:
            raise TemporalError("a reading cannot expire before it was computed.")
        if self.basis_at > self.computed_at:
            raise TemporalError(
                "the evidence behind a reading cannot have changed after the reading was "
                "computed — a score is a projection over evidence that already existed."
            )

    @property
    def is_first_reading(self) -> bool:
        return self.supersedes is None

    def why_now(self) -> str:
        """Recorded, never guessed. `ScoreTrigger` exists for this question."""
        return f"This reading exists because {_WHY[self.trigger]}."

    def why_not_earlier(self) -> str:
        """`basis_at` is the answer: the previous reading was correct until
        the evidence beneath it changed."""
        if self.is_first_reading:
            return "This is the first reading for this account — there was nothing earlier to see."
        return (
            f"The previous reading was the correct one until {self.basis_at.date().isoformat()}, "
            "when the evidence beneath it changed."
        )

    def what_changed(self) -> str:
        """From `delta` and `trend`, both already computed against the
        immediately previous reading."""
        if self.is_first_reading:
            return "Nothing changed — this account had not been read before."
        if self.delta == 0:
            return (
                f"The score held steady; the evidence behind it changed without moving the "
                f"number ({self.trend.value})."
            )
        direction = "rose" if self.delta > 0 else "fell"
        return f"The score {direction} by {abs(self.delta)} point(s) ({self.trend.value})."

    def freshness(self) -> str:
        """How far the intelligence can still be relied on.

        `valid_until` states how long the stored value is **exactly correct**,
        not merely recent — which is what makes step decay a contract rather
        than an implementation detail.
        """
        if self.valid_until is None:
            return (
                f"The intelligence behind this is {self.evidence_state.value}, and nothing is "
                "currently due to age out of it."
            )
        return (
            f"The intelligence behind this is {self.evidence_state.value}, and is exactly "
            f"correct until {self.valid_until.date().isoformat()}."
        )

    def explain(self) -> tuple[str, ...]:
        """All four, in the order a customer asks them.

        Derived from the same fields every time, so the explanation cannot
        drift from the facts it explains — the alternative, a stored
        paragraph, would be a second representation of one history.
        """
        return (self.why_now(), self.why_not_earlier(), self.what_changed(), self.freshness())

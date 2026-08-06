"""Does a declared criterion predict anything? — measured, never asserted.

**The row three coordination items were about.** This lane claimed
[TASK-406](../../../../docs/BACKLOG.md), found nothing could say whether an
account matches a criterion, and **refused to invent it inside a slice**
([C-330](../../../../docs/LANE_COORDINATION.md)). The product owner made it a
foundational capability; [TASK-434](../../../../docs/BACKLOG.md) built the
predicate; [C-332](../../../../docs/LANE_COORDINATION.md) found nothing could
construct its input; [TASK-446](../../../../docs/BACKLOG.md) built the reader.
**This is what all of that was for.**

### Why the measurement lives here

**[C-328](../../../../docs/LANE_COORDINATION.md), ruled by the product owner:**
*"Do not introduce the forbidden dependency. `commercial_profile` declares.
`opportunity_engine` measures. Maintain the existing dependency direction."*

**The module that owns outcomes measures against them.** The module that
records a declaration goes on only recording it — and the trade-off was stated
rather than buried: the customer-facing surface is the **ICP Builder**, which
is `commercial_profile`'s screen, so the value a seller reads is computed by a
module they never see named. **That is already true of every derived fact in
the product**, and the alternative is a declaring module grading its own input.

### The arithmetic, and the one honest thing about it

> **Lift is `P(won | criterion satisfied) ÷ P(won overall)`.**

**Above 1.0 the criterion is predictive; at 1.0 it tells you nothing; below it
the criterion is selecting against you** — which is the most useful thing this
measurement can say and the one nobody expects to see.

**Every figure carries its sample size**, because a lift computed over eleven
deals is not the same claim as one computed over four hundred and **a screen
showing only the multiple invites the reader to forget that.** The ICP
Builder's own discipline says it in the product's words: *"2.2× lift on only 22
deals; treat as directional, not settled."*

### `UNMEASURED` accounts are excluded, and that is the decision

**TASK-434 deliberately left this policy open** — *"that rule belongs to
whichever consumer has a reason for it, stated where a customer can see it."*
**This is that consumer, and the reason is stated here.**

> **An account whose industry nobody has reported is not evidence about
> whether the industry criterion predicts anything.**

Counting it as *not satisfying* would make every unreported account argue
against the criterion, so **a criterion would look worse the less Signora knew
— which is the opposite of the truth.** Counting it as *satisfying* is the same
error in the flattering direction. **So it leaves the denominator**, and
`measured` reports how many remained, because a lift over the eleven accounts
anybody knew anything about must not be read as a lift over four hundred.

⚠️ **A `DISPUTED` attribute is still measured.** `AccountAttributesReader`
returns the most recent value with the disagreement named; treating a contested
observation as unknown would discard evidence the platform genuinely has.
**The consumer surface should show the dispute; the measurement uses the
value.**
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from modules.commercial_profile.public import CriterionKind, Verdict
from modules.opportunity_engine.domain.opportunity import Stage


@dataclass(frozen=True, slots=True)
class Outcome:
    """One decided account, and whether the criterion held for it.

    **The input the measurement takes**, so the assembly — reading decided
    opportunities, resolving attributes, calling the predicate — happens in the
    application layer and the rule below stays pure.
    """

    stage: Stage
    verdict: Verdict

    @property
    def is_won(self) -> bool:
        return self.stage is Stage.CLOSED_WON

    @property
    def is_measured(self) -> bool:
        """**`DISMISSED` is not an outcome about the criterion.**

        It is feedback about Signora's own qualification — *"we should not have
        been shown this"* — and folding it into losses would make a criterion
        look unpredictive because the platform surfaced the wrong accounts,
        which is a different failure with a different owner.
        """
        return self.stage in {Stage.CLOSED_WON, Stage.CLOSED_LOST}


@dataclass(frozen=True, slots=True)
class CriterionLift:
    """What one criterion predicted, and how much evidence there is for it."""

    kind: CriterionKind
    #: Decided accounts where the criterion was **satisfied**.
    satisfied: int
    #: Of those, how many were won.
    satisfied_won: int
    #: Every decided account the criterion could be measured on — satisfied or
    #: not. **The denominator of the baseline**, and the number that says how
    #: much this figure is worth.
    measured: int
    measured_won: int
    #: Decided accounts dropped because nothing was observed to compare
    #: against. **Reported, never silently absorbed.**
    unmeasured: int

    def __post_init__(self) -> None:
        if self.satisfied > self.measured:
            raise ValueError(
                f"{self.satisfied} accounts satisfied '{self.kind}' out of {self.measured} "
                "measured. The satisfied set is a subset of the measured set, so this is a "
                "query that stopped scoping one of its two counts."
            )
        if self.satisfied_won > self.satisfied or self.measured_won > self.measured:
            raise ValueError("more accounts were won than existed to win.")

    @property
    def lift(self) -> float | None:
        """`P(won | satisfied) ÷ P(won overall)`, or **`None` when it cannot be
        measured.**

        **`None` in three cases, and never `1.0`:** nothing satisfied the
        criterion, nothing was measured at all, or **nobody has won anything
        yet** — the last being the one a young workspace hits, where a `1.0`
        would read as *"this criterion is neutral"* when the truth is *"there
        are no wins to compare against."*

        **A criterion no outcome data supports says so**, which is the row's
        own acceptance criterion.
        """
        if self.satisfied == 0 or self.measured == 0 or self.measured_won == 0:
            return None
        return (self.satisfied_won / self.satisfied) / (self.measured_won / self.measured)

    @property
    def is_directional(self) -> bool:
        """**Whether the sample is too small to settle anything.**

        The threshold is the ICP Builder's own words — *"2.2× lift on only 22
        deals; treat as directional, not settled"* — so **the screen and the
        measurement agree about what small means** rather than each carrying
        its own number.
        """
        return self.satisfied < DIRECTIONAL_BELOW


#: Below this many satisfying accounts, a lift is directional rather than
#: settled. **Taken from the approved screen's own sentence**, not chosen here:
#: a threshold invented in the domain would eventually disagree with the one a
#: customer was told.
DIRECTIONAL_BELOW = 22


def lift_for(kind: CriterionKind, outcomes: Sequence[Outcome]) -> CriterionLift:
    """Measure one criterion against decided accounts.

    **Pure.** No repository, no session, no clock — the caller supplies the
    outcomes it already assembled, so the arithmetic can be replayed and put in
    front of a customer as an explanation.
    """
    decided = [o for o in outcomes if o.is_measured]
    measured = [o for o in decided if o.verdict is not Verdict.UNMEASURED]
    satisfied = [o for o in measured if o.verdict is Verdict.YES]

    return CriterionLift(
        kind=kind,
        satisfied=len(satisfied),
        satisfied_won=sum(1 for o in satisfied if o.is_won),
        measured=len(measured),
        measured_won=sum(1 for o in measured if o.is_won),
        unmeasured=len(decided) - len(measured),
    )


__all__ = ["DIRECTIONAL_BELOW", "CriterionLift", "Outcome", "lift_for"]

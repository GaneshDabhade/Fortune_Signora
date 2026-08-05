"""Whether an account matches an ideal customer — asked once, answered here.

**The capability [C-330](../../../../docs/LANE_COORDINATION.md) asked for.**
Lane B refused to invent it inside TASK-406; the product owner ruled it
foundational rather than one row's dependency — *"multiple future product
areas will depend upon it"* — and [443](../../../../docs/architecture/443-account-matching-capability.md)
counted **sixteen** consumers. This is the one place that answers.

### Why it lives in the module that records the declaration

**The criterion vocabulary is defined here** — `industries`, `countries`,
`EmployeeRange`, `validate_criterion_list` — and a matcher built anywhere else
would need a second copy of it. Two copies of a vocabulary is the duplicated
truth §2 forbids, and the copy nobody is maintaining is the one that decides
whether an account is in its own ICP.

### And why that does not breach the contract this module lives under

`pyproject.toml` forbids `commercial_profile` from importing the pipeline:
*"commercial_profile declares; it never reads the pipeline."* **This file
reads nothing.** `evaluate` imports no module, queries no repository, opens no
session and knows no caller — **the facts are handed to it**. The prohibition
is on *reaching for* the pipeline, and being given a value is not reaching.

That distinction is what makes the ruled dependency direction hold: the caller
that has the observed attributes — and only it — decides when to ask.

### Two invariants, and both are in the type rather than in prose

**A verdict is a category with reasons and is never a number.** `MatchStrength`
established this in resolution — *"a semantic category, never a number"* — and
the same door would open here: a number invites a weight, a weight invites a
threshold, and a threshold is a propensity judgement this module has no
standing to make. **There is no score on anything in this file.**

**`UNMEASURED` is not `NO`.** The customer declares free text and the pipeline
observes canonical values, so `SaaS` and `Computer Software` are the same
industry written twice. Under string equality that returns *no match* and the
account **silently drops out of its own ICP** — a wrong answer that looks like
a confident one. Absence of an observation and absence of a match are
different facts, and collapsing them is the same defect the search ruling
closed for groups (TASK-408).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from modules.commercial_profile.domain.icp import EmployeeRange, ProductIcp


class CriterionKind(StrEnum):
    """Which part of a declaration a verdict is about.

    **Named rather than positional**, so a consumer rendering *"industry:
    matched"* reads a field instead of counting a tuple — and so adding a
    criterion later is a new member rather than a shifted index.
    """

    INDUSTRY = "industry"
    COUNTRY = "country"
    EMPLOYEES = "employees"


class Verdict(StrEnum):
    """Whether a criterion is satisfied — **a category, never a number.**

    Three states, and the third is the one that matters. A consumer that
    treats `UNMEASURED` as `NO` reports an account as outside an ICP nobody
    checked it against, which is worse than reporting nothing: it is wrong
    and it looks decided.
    """

    YES = "yes"
    """The observed value satisfies the declared criterion."""

    NO = "no"
    """The observed value was read and does not satisfy it."""

    UNMEASURED = "unmeasured"
    """**Nothing was observed to compare against — not a failure.**

    Either no provider has reported this attribute, or the declaration says
    nothing about it. A consumer must render this as *unknown* and must never
    fold it into `NO`.
    """


@dataclass(frozen=True, slots=True)
class CriterionVerdict:
    """One criterion, its answer, and why.

    `reason` is the whole of the disclosure: a verdict a seller cannot
    interrogate is a verdict they have to take on trust, and this module's
    entire discipline is that nothing is taken on trust.
    """

    kind: CriterionKind
    verdict: Verdict
    #: What was compared, in the customer's words and the provider's.
    #: **Never a score.** Empty when nothing was observed.
    reason: str

    @property
    def is_decided(self) -> bool:
        return self.verdict is not Verdict.UNMEASURED


@dataclass(frozen=True, slots=True)
class ObservedAttributes:
    """What the pipeline observed about one account, handed in by the caller.

    **This module never fetches these**, and the type exists so that it is
    obvious it does not: every field is optional because a real account is
    usually missing some, and a missing field produces `UNMEASURED` rather
    than a failed match.
    """

    #: The industry as some provider reported it, canonical or not. This
    #: module compares text and does not normalise: **normalising here would
    #: be a second vocabulary**, and the reviewed synonym catalog that will
    #: eventually do it properly is deliberately out of scope (443 M1).
    industry: str | None = None
    country: str | None = None
    employees: int | None = None


def _normalise(value: str) -> str:
    """Case and surrounding space only.

    **Deliberately not a synonym map, a stemmer or a fuzzy ratio.** Folding
    case is not interpretation — `SaaS` and `saas` are the same string typed
    twice. Anything cleverer is a judgement about what two different words
    mean, and 443 records that as a **reviewed catalog** rather than code:
    *"build it when `UNMEASURED` shows it is losing accounts."*
    """
    return " ".join(value.split()).casefold()


def _text_verdict(
    kind: CriterionKind, declared: tuple[str, ...], observed: str | None
) -> CriterionVerdict:
    if not declared:
        return CriterionVerdict(
            kind=kind, verdict=Verdict.UNMEASURED, reason="not declared"
        )
    if observed is None or not observed.strip():
        return CriterionVerdict(
            kind=kind, verdict=Verdict.UNMEASURED, reason="nothing observed"
        )
    wanted = {_normalise(d) for d in declared}
    if _normalise(observed) in wanted:
        return CriterionVerdict(
            kind=kind, verdict=Verdict.YES, reason=f"observed «{observed}» is declared"
        )
    return CriterionVerdict(
        kind=kind,
        verdict=Verdict.NO,
        # The declared list travels with the refusal, because *"not a match"*
        # without saying what was wanted sends the reader to another screen.
        reason=f"observed «{observed}»; declared {', '.join(f'«{d}»' for d in declared)}",
    )


def _employee_verdict(
    declared: EmployeeRange | None, observed: int | None
) -> CriterionVerdict:
    kind = CriterionKind.EMPLOYEES
    if declared is None:
        return CriterionVerdict(
            kind=kind, verdict=Verdict.UNMEASURED, reason="not declared"
        )
    if observed is None:
        return CriterionVerdict(
            kind=kind, verdict=Verdict.UNMEASURED, reason="nothing observed"
        )
    low = declared.minimum
    high = declared.maximum
    # **Both bounds inclusive.** A customer saying "100–1000" means a company
    # of exactly 1000, and a half-open range would exclude it for a reason
    # nobody could explain from the screen they typed it on.
    if (low is None or observed >= low) and (high is None or observed <= high):
        return CriterionVerdict(
            kind=kind, verdict=Verdict.YES, reason=f"{observed} is within {_span(declared)}"
        )
    return CriterionVerdict(
        kind=kind, verdict=Verdict.NO, reason=f"{observed} is outside {_span(declared)}"
    )


def _span(declared: EmployeeRange) -> str:
    if declared.minimum is None:
        return f"up to {declared.maximum}"
    if declared.maximum is None:
        return f"{declared.minimum} or more"
    return f"{declared.minimum}–{declared.maximum}"


def evaluate(
    icp: ProductIcp, observed: ObservedAttributes
) -> tuple[CriterionVerdict, ...]:
    """Whether an account satisfies each declared criterion.

    **Pure.** No I/O, no clock, no randomness, no module import beyond this
    one's own vocabulary — the same input returns the same verdicts forever,
    which is what lets a consumer cache it, replay it, or put it in front of a
    customer as an explanation.

    **Always three verdicts, one per criterion kind**, whether or not the
    declaration mentions them. A criterion the customer did not declare
    returns `UNMEASURED` rather than being omitted — the same reasoning the
    product owner applied to search groups: *"the absence of results and the
    absence of the group represent different business meanings."*

    **No overall answer, and that is deliberate.** Rolling three verdicts into
    *"matches"* needs a rule for what to do about `UNMEASURED`, and every
    available rule is a judgement — treat it as a pass and an unmeasured
    account looks qualified, treat it as a fail and it looks disqualified.
    **That rule belongs to whichever consumer has a reason for it**, stated
    where a customer can see it, not hidden in a helper here.
    """
    return (
        _text_verdict(CriterionKind.INDUSTRY, icp.industries, observed.industry),
        _text_verdict(CriterionKind.COUNTRY, icp.countries, observed.country),
        _employee_verdict(icp.employees, observed.employees),
    )

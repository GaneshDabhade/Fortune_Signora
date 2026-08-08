"""The Onboarding Run — **what a person confirmed on their way in**.

**[TASK-469](../../../../docs/BACKLOG.md) · Workflow 8**, against
`docs/design-snapshot/screens/Fortune Signora Onboarding.dc.html`
([D-138](../../../../docs/DECISION_REGISTER.md): the snapshot is the
implementation authority).

### ⚡ The design's own sentence is the aggregate's shape

> ***"Confirm, don't collect. Eleven of the fifteen values are inferred from
> the domain, its public record and the browser."***

⛔ **So a value here is never a bare value.** It is a value **and where it came
from**, because the design requires *"every inferred value marked as inferred
and correctable"* and a screen cannot mark what the record did not keep.
`Answer` is that pair, and it is why `provenance` has no default: **a caller
that could omit it would be able to store a guess indistinguishable from a
person's answer**, which is the one thing this record exists to prevent.

### 🔴 Skipping is safe, and the aggregate is what makes that true

> ***"The workspace exists at step 2. Everything after it is refinement of
> something the user already owns… an abandoned onboarding still produces a
> customer."***

**Every step except the workspace is skippable**, so **no field here is
required and none is validated into existence.** ⛔ **A `NOT NULL` industry
would turn an abandoned run into a broken row**, and the customer the design
promises would not exist. **`skip()` is a first-class transition rather than an
absence** — a run that was left is a different fact from a run that was never
started, and only one of them should raise a resume banner.

### ⛔ What this aggregate refuses to know

**What a goal *does*.** `features_for()` maps goals onto capability names and
stops there — it does not enable anything, does not read a module, and does not
learn what a feature is. **The design says the mapping is deterministic**
(*"Three outcomes map deterministically onto modules, so the feature-
preferences step disappears"*), and [§2](../../../../CLAUDE.md)'s
least-powerful-author rule puts a deterministic mapping in code rather than in
a stored column that could disagree with it.

⚠️ **Company size is banded and free integers are unrepresentable.** The design
gives the reason rather than the rule: *"Free numbers are not accepted; bands
are what benchmarks are computed against."* **An `int` here would be a number
nothing can benchmark**, and it would be accepted silently.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from modules.workspace_tenancy.domain.exceptions import (
    OnboardingRunAlreadyFinishedError,
    TeamSizeOutOfRangeError,
    TooManyGoalsError,
)

#: The design's rule, verbatim: *"Integer ≥ 1, ≤ 10,000. Zero explains that
#: they count."* ⚡ **Zero is refused rather than corrected** — a person who
#: types it is telling the product something, and silently storing `1` would
#: answer them by overwriting the question.
MIN_TEAM_SIZE = 1
MAX_TEAM_SIZE = 10_000

#: *"Up to three outcomes."* ⛔ **The fourth selection is disabled, not
#: silently ignored** — the screen states the limit and the aggregate refuses
#: it, so the two cannot drift into disagreeing about what happened.
MAX_GOALS = 3


class Provenance(StrEnum):
    """Where a value came from, and it travels with the value.

    ⚠️ **`INFERRED` is not a lesser kind of truth — it is an unconfirmed one.**
    The design shows it as a badge beside the field with the value editable,
    never as a warning, because *"confirming four pre-filled fields is a
    fundamentally different task from filling a form."*
    """

    #: Derived from the email domain, its public record, or the browser.
    INFERRED = "inferred"
    #: A person was shown an inferred value and agreed with it.
    CONFIRMED = "confirmed"
    #: A person typed or chose it themselves, with nothing pre-filled.
    ENTERED = "entered"


class OnboardingStep(StrEnum):
    """The six steps the design names, in the order it names them.

    ⛔ **`WORKSPACE` is the only one that is not skippable**, and that is a
    fact about the flow rather than about this enum — the aggregate never
    holds workspace creation, because by the time a run exists the workspace
    does (it is what `workspace_id` points at).
    """

    WELCOME = "welcome"
    WORKSPACE = "workspace"
    COMPANY = "company"
    YOU = "you"
    GOALS = "goals"
    CONNECT = "connect"


class CompanySizeBand(StrEnum):
    """Bands, because *"bands are what benchmarks are computed against."*"""

    MICRO = "1-10"
    SMALL = "11-50"
    MEDIUM = "51-200"
    LARGE = "201-1000"
    ENTERPRISE = "1001-5000"
    GLOBAL = "5000+"


class Role(StrEnum):
    """The six roles on screen `05`. *"Role sets the home page and the alert
    routing"* — which is why it is closed rather than free text."""

    REVENUE_LEADER = "revenue_leader"
    ACCOUNT_EXECUTIVE = "account_executive"
    SALES_OPERATIONS = "sales_operations"
    CUSTOMER_SUCCESS = "customer_success"
    MARKETING = "marketing"
    EXECUTIVE = "executive"


class Goal(StrEnum):
    """The six outcomes on screen `06`.

    ⚡ **Closed on purpose.** *"Users can't rank features they haven't used,
    but they know what is going wrong"* — the value of this step is that the
    six are a vocabulary the product understands, and a seventh arriving from
    a request body would map onto nothing.
    """

    FORECAST_ACCURATELY = "forecast_accurately"
    STOP_DEALS_SLIPPING = "stop_deals_slipping"
    PROTECT_RENEWALS = "protect_renewals"
    COACH_THE_TEAM = "coach_the_team"
    FIND_NEW_PIPELINE = "find_new_pipeline"
    PROVE_MARKETING_IMPACT = "prove_marketing_impact"


#: **The feature-preferences step, replaced.** Deterministic, so it is derived
#: on every read rather than written down — [§2](../../../../CLAUDE.md), *truth
#: has exactly one authoritative representation*. **A stored copy would be the
#: version that disagrees the first time this table changes.**
_FEATURES_BY_GOAL: dict[Goal, tuple[str, ...]] = {
    Goal.FORECAST_ACCURATELY: ("forecast", "executive_dashboard"),
    Goal.STOP_DEALS_SLIPPING: ("signals", "opportunity_intelligence"),
    Goal.PROTECT_RENEWALS: ("signals", "account_360"),
    Goal.COACH_THE_TEAM: ("team_management", "ai_copilot"),
    Goal.FIND_NEW_PIPELINE: ("companies", "ai_research"),
    Goal.PROVE_MARKETING_IMPACT: ("reports", "executive_dashboard"),
}


@dataclass(frozen=True, slots=True)
class Answer[T]:
    """A value and where it came from, which the design requires together.

    ⛔ **Neither field has a default.** A value with an assumed provenance is
    exactly the *hidden input* [§2](../../../../CLAUDE.md) calls an
    architecture defect: the same stored row would mean two different things
    to the screen depending on which caller wrote it.
    """

    value: T
    provenance: Provenance

    def confirmed(self) -> Answer[T]:
        """The person agreed with what they were shown.

        ⚡ **The value does not change and the provenance does.** That is the
        whole of screen `04`: four confirmations and no typing.
        """
        return replace(self, provenance=Provenance.CONFIRMED)

    def corrected(self, value: T) -> Answer[T]:
        """They changed it, so it is theirs now — *inferred and correctable*."""
        return Answer(value=value, provenance=Provenance.ENTERED)


@dataclass(frozen=True, slots=True)
class OnboardingRun:
    """One person's run through onboarding, in one workspace.

    **Frozen**, like every other aggregate in this module: a caller cannot
    reach through it and set a goal without going past the limit that refuses
    a fourth.

    ⚠️ **Keyed by workspace *and* person.** A workspace has many members and
    each arrives once; a single row per workspace would let the second member
    resume the first member's run, which the resume banner would then offer to
    the wrong person.
    """

    workspace_id: UUID
    person_id: UUID
    started_at: datetime
    #: The step the person is on. **Not a percentage** — the design's rail
    #: shows named steps with done/active/idle, and a number would have to be
    #: re-interpreted into names by whoever rendered it.
    current_step: OnboardingStep = OnboardingStep.WELCOME
    completed_steps: frozenset[OnboardingStep] = frozenset()
    industry: Answer[str] | None = None
    company_size: Answer[CompanySizeBand] | None = None
    region: Answer[str] | None = None
    timezone: Answer[str] | None = None
    role: Answer[Role] | None = None
    team_size: Answer[int] | None = None
    goals: tuple[Goal, ...] = ()
    finished_at: datetime | None = None
    #: ⚡ **Distinguishes *left* from *never started*.** Both have an unfinished
    #: run; only the first should raise a resume banner, and only the first was
    #: a decision the person made.
    skipped_at: datetime | None = None
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def is_finished(self) -> bool:
        return self.finished_at is not None

    @property
    def features(self) -> tuple[str, ...]:
        """The capability names the chosen goals imply, deduplicated, in order.

        ⛔ **Derived on every read.** See `_FEATURES_BY_GOAL` — this is the
        feature-preferences step the design deletes, and storing its output
        would be the second representation that eventually disagrees.
        """
        seen: dict[str, None] = {}
        for goal in self.goals:
            for feature in _FEATURES_BY_GOAL[goal]:
                seen.setdefault(feature, None)
        return tuple(seen)

    def _open(self) -> None:
        """A finished run is history and history is not edited ([§2](../../../../CLAUDE.md))."""
        if self.is_finished:
            raise OnboardingRunAlreadyFinishedError(
                "This onboarding run has finished; a change after it is a settings change."
            )

    def _touch(self, **changes: object) -> OnboardingRun:
        return replace(self, updated_at=datetime.now(UTC), **changes)  # type: ignore[arg-type]

    def advance_to(self, step: OnboardingStep) -> OnboardingRun:
        """Move to a step, marking the one being left as complete.

        ⚡ **Autosave is *this*.** The design says *"every step saves on advance
        and on blur"*, so advancing is a persisted transition rather than a
        client-side cursor — which is what makes *"you can leave at any point"*
        true rather than aspirational.

        ⛔ **Going back is not destructive** (*"Returning to a step shows what
        was chosen, not an empty form"*), so a completed step stays completed
        when the person navigates back through it.
        """
        self._open()
        return self._touch(
            current_step=step,
            completed_steps=self.completed_steps | {self.current_step},
        )

    def confirm_company(
        self,
        *,
        industry: Answer[str] | None = None,
        company_size: Answer[CompanySizeBand] | None = None,
        region: Answer[str] | None = None,
        timezone: Answer[str] | None = None,
    ) -> OnboardingRun:
        """Screen `04` — four facts, each confirmed or corrected.

        ⛔ **Every argument is optional and omitting one leaves it alone.**
        The step is skippable and partially answerable, and a call that reset
        three fields because it only meant to change the fourth would lose
        answers the person had already given.
        """
        self._open()
        return self._touch(
            industry=industry if industry is not None else self.industry,
            company_size=company_size if company_size is not None else self.company_size,
            region=region if region is not None else self.region,
            timezone=timezone if timezone is not None else self.timezone,
        )

    def describe_person(
        self,
        *,
        role: Answer[Role] | None = None,
        team_size: Answer[int] | None = None,
    ) -> OnboardingRun:
        """Screen `05` — role and team size.

        **The range is refused rather than clamped.** *"Zero explains that they
        count"* is copy on a screen; storing `1` for a typed `0` would answer
        the person by overwriting them.
        """
        self._open()
        if team_size is not None and not (MIN_TEAM_SIZE <= team_size.value <= MAX_TEAM_SIZE):
            raise TeamSizeOutOfRangeError(
                f"A team is between {MIN_TEAM_SIZE} and {MAX_TEAM_SIZE:,} people."
            )
        return self._touch(
            role=role if role is not None else self.role,
            team_size=team_size if team_size is not None else self.team_size,
        )

    def choose_goals(self, goals: tuple[Goal, ...]) -> OnboardingRun:
        """Screen `06` — up to three, and the fourth is refused.

        ⚡ **Selection order is kept**, because the design says the goals
        *"order the home page"*. A set would lose that and the home page would
        have to invent an order of its own.

        ⛔ **An empty tuple is valid**: *"skipping entirely is permitted."*
        """
        self._open()
        if len(goals) > MAX_GOALS:
            raise TooManyGoalsError(f"Choose up to {MAX_GOALS} goals.")
        deduplicated = tuple(dict.fromkeys(goals))
        return self._touch(goals=deduplicated)

    def finish(self) -> OnboardingRun:
        """The run completed. **Finishing twice is a caller error**, not a
        silent overwrite — the first timestamp is the one that happened."""
        self._open()
        now = datetime.now(UTC)
        return replace(
            self,
            current_step=OnboardingStep.CONNECT,
            completed_steps=self.completed_steps | {self.current_step},
            finished_at=now,
            updated_at=now,
        )

    def skip(self) -> OnboardingRun:
        """They chose to leave. ⛔ **Not a failure and not a finish.**

        *"The dialog says what gets worse in product terms and lets them go.
        No second ask, no guilt copy — the resume banner does the remaining
        work quietly."* **This is the record that banner reads.**
        """
        self._open()
        return self._touch(skipped_at=datetime.now(UTC))


def features_for(goals: tuple[Goal, ...]) -> tuple[str, ...]:
    """The mapping as a function, for callers holding goals without a run."""
    return OnboardingRun(
        workspace_id=UUID(int=0),
        person_id=UUID(int=0),
        started_at=datetime.now(UTC),
        goals=goals,
    ).features

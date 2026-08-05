"""What the pipeline is doing, computed from the states somebody actually recorded.

**Four questions a CRO asks, and every one of them is arithmetic over
`opportunity_state`** — which is append-only and carries `sequence`, `stage`,
`owner_id`, `actor_id`, `reason` and `occurred_at`. **Nothing here is stored**:
a dashboard figure is derived on every request, because a cached one is a
second representation of a fact the state table already holds (§2).

### Why the rules are here and the aggregation is not

**A workspace's history is unbounded, so the counting happens in SQL** — an
`GROUP BY` over a few thousand rows rather than a few thousand rows crossing a
boundary to be counted in Python (§14). **What crosses is already aggregated,
and what lives here is every rule that could be argued with**: which stages
form the funnel, what a conversion is when nothing entered, how a median
breaks on an even count, and whether an unassigned account is an owner.

That split is deliberate. **A number a customer disputes must be defensible
from a function somebody can read**, and none of these functions touches a
session, a clock or a network.

### The one discipline every figure here inherits

> **A denominator of zero is `None`, never `1.0` and never `0.0`.**

[TASK-406](../../../../docs/BACKLOG.md) states it for lift — *"a criterion no
outcome data supports says so rather than reporting `1.0×`"* — and it is the
same defect either way: **a rate invented from no evidence looks exactly like
a rate measured from plenty.** A new workspace's dashboard must read *"nothing
has reached this stage yet"*, not *"0% conversion"*, which a CRO would act on.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Final, Sequence
from uuid import UUID

from modules.opportunity_engine.domain.opportunity import OPEN_STAGES, Stage

#: The funnel, in order, and **it is not every stage.**
#:
#: `CLOSED_LOST` and `DISMISSED` are *exits*, not steps — an opportunity that
#: reaches one has left the funnel rather than progressed through it, and
#: including them would make "conversion" mean two different things in one
#: table. They are still counted, as the exits they are.
#:
#: **Reopening is why each step is measured independently.** `CLOSED_LOST` may
#: return to `TRACKING`, so an opportunity can enter a stage more than once and
#: can reach a later stage before an earlier one in wall-clock order. Every
#: figure below therefore asks *"did this opportunity ever reach X?"* rather
#: than walking a sequence, which is the only reading that survives a reopen.
FUNNEL: Final = (Stage.TRACKING, Stage.ENGAGED, Stage.CLOSED_WON)


@dataclass(frozen=True, slots=True)
class StageConversion:
    """One step of the funnel: how many arrived, and how many went on.

    **Both counts are distinct opportunities, never state rows.** An account
    that was closed lost and reopened has two `TRACKING` rows and is one
    opportunity, and counting rows would inflate the top of the funnel by
    exactly the accounts a seller worked hardest.
    """

    from_stage: Stage
    to_stage: Stage
    #: Distinct opportunities that ever reached `from_stage`.
    entered: int
    #: Of those, distinct opportunities that ever reached `to_stage`.
    advanced: int

    def __post_init__(self) -> None:
        if self.advanced > self.entered:
            raise ValueError(
                f"{self.advanced} opportunities advanced from '{self.from_stage}' to "
                f"'{self.to_stage}' but only {self.entered} ever entered it. `advanced` is "
                "measured over the accounts that entered, so it can never exceed them — this "
                "is a query that stopped scoping one of its two counts."
            )

    @property
    def rate(self) -> float | None:
        """The proportion that advanced, or **`None` when nobody entered.**

        Not `0.0`. A stage nothing has reached has no conversion rate, and
        reporting one invites a reader to compare it against a stage that has.
        """
        if self.entered == 0:
            return None
        return self.advanced / self.entered


@dataclass(frozen=True, slots=True)
class StageAgeing:
    """How long the work currently sitting in a stage has been sitting there.

    **Open opportunities only, and that is the question being asked.** A CRO
    looking at ageing wants to know what is going stale *now*; folding in how
    long closed deals once took would mix a live problem with a historical
    average and move the number in the wrong direction whenever somebody
    finally closed something old.
    """

    stage: Stage
    open_count: int
    #: Days in this stage, median across the open opportunities.
    median_days: float | None
    #: The single oldest, because a median hides the account somebody forgot.
    oldest_days: float | None

    def __post_init__(self) -> None:
        if self.stage not in OPEN_STAGES:
            raise ValueError(
                f"'{self.stage}' is terminal and cannot age. Ageing measures work in progress; "
                "a closed opportunity has a duration, not an age."
            )
        if (self.open_count == 0) != (self.median_days is None):
            raise ValueError(
                "ageing must report a median exactly when it has open opportunities to measure "
                "— an empty stage has no median, and a populated one always has."
            )


@dataclass(frozen=True, slots=True)
class OwnerLoad:
    """One person's share of the pipeline.

    **`owner_id` is `None` for unassigned work, and that is a row rather than
    an omission.** Unassigned accounts are the ones most likely to be missed,
    so a roll-up that silently dropped them would hide exactly the column a
    manager is looking for.

    **No names here.** This module knows an id; who that is belongs to the
    surface that can ask Workspace & Tenancy.
    """

    owner_id: UUID | None
    open_count: int
    won: int
    lost: int

    def __post_init__(self) -> None:
        for label, value in (("open", self.open_count), ("won", self.won), ("lost", self.lost)):
            if value < 0:
                raise ValueError(f"an owner cannot hold {value} {label} opportunities.")


@dataclass(frozen=True, slots=True)
class Movement:
    """One thing that changed, and why somebody changed it.

    **The `reason` travels with it.** `OpportunityState` refuses to exist
    without one — *"workflow that cannot explain itself is worse than
    intelligence that cannot"* — so a movement feed that omitted it would
    discard the field the record was designed around.
    """

    opportunity_id: UUID
    entity_id: UUID
    stage: Stage
    #: What it was before. `None` for the opening state, which came from nothing.
    previous_stage: Stage | None
    owner_id: UUID | None
    #: `None` only on the opening `TRACKING` row — the one state Signora authors.
    actor_id: UUID | None
    reason: str
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class PipelineHealth:
    """The four sections, together, describing one workspace at one moment.

    ⚠️ **Four, not five.** The Executive Dashboard's fifth section is *ICP
    coverage, in versus outside*, and it is **not here**: the predicate that
    would decide which cohort an account is in takes observed attributes that
    nothing in the repository constructs, and this module is forbidden every
    module that could construct them ([C-332](../../../../docs/LANE_COORDINATION.md)).
    **Its absence is stated rather than filled with a zero**, which would have
    read as *"no accounts match your ICP"*.
    """

    conversions: tuple[StageConversion, ...]
    ageing: tuple[StageAgeing, ...]
    owners: tuple[OwnerLoad, ...]
    movements: tuple[Movement, ...]
    #: The boundary `movements` was asked for, echoed back so a caller renders
    #: *"since 1 August"* without having to remember what it requested.
    movements_since: datetime


def median(values: Sequence[float]) -> float | None:
    """The middle value, **averaging the two middle ones on an even count.**

    **`None` on an empty sequence rather than `0.0`** — the discipline this
    module inherits everywhere. Zero days in stage is a real and different
    answer, describing work that arrived this morning.
    """
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def _days(span: timedelta) -> float:
    return span.total_seconds() / 86400.0


def stage_ageing(stage: Stage, entered_at: Sequence[datetime], *, now: datetime) -> StageAgeing:
    """Age the open opportunities sitting in one stage.

    **`now` is a parameter and has no default.** A function that read the clock
    itself would be untestable and would make two sections of one dashboard
    disagree by however long the request took — a hidden input, which §2 calls
    an architecture defect rather than an implementation detail.
    """
    ages = [_days(now - moment) for moment in entered_at]
    return StageAgeing(
        stage=stage,
        open_count=len(ages),
        median_days=median(ages),
        oldest_days=max(ages) if ages else None,
    )


def funnel(reach: dict[Stage, int], advanced: dict[tuple[Stage, Stage], int]) -> tuple[StageConversion, ...]:
    """The funnel as ordered steps, from counts the repository aggregated.

    **A step with no arrivals is still a step.** Returning it with `entered=0`
    and a `None` rate keeps the funnel's shape stable between an empty
    workspace and a busy one, so a surface renders the same three rows on the
    first day as on the hundredth — the same reasoning the product owner
    applied to search groups at TASK-408, where *"the absence of results and
    the absence of the group represent different business meanings."*
    """
    return tuple(
        StageConversion(
            from_stage=lower,
            to_stage=upper,
            entered=reach.get(lower, 0),
            advanced=advanced.get((lower, upper), 0),
        )
        for lower, upper in zip(FUNNEL, FUNNEL[1:])
    )


__all__ = [
    "FUNNEL",
    "Movement",
    "OwnerLoad",
    "PipelineHealth",
    "StageAgeing",
    "StageConversion",
    "funnel",
    "median",
    "stage_ageing",
]

"""The Opportunity — what Sales should actively track.

**Signora's first workflow module.** Every module before it derives
information from evidence: delete any derived table, re-run the pipeline,
and the same rows come back byte for byte, because every identity is
derived from the evidence beneath it. An opportunity records that **a human
committed to something**, and nothing reproduces that.

*Permanent architectural principle, ratified 2026-07-29:*

> **Intelligence suggests. Humans commit.**
>
> A buying score may **create** an opportunity. **Only a human may progress
> one beyond the machine-authored boundary.** Commercial intelligence
> informs workflow; it never owns it.

Four properties carry the design:

**It holds no derived intelligence of its own.** No current score, no
signals, no recomputed judgement. It cites the score that *caused it to
exist* and reads everything else live. A workflow row caching a score would
be a second, stale copy of the pipeline's output — and within a year
something would read it in preference to the real thing.

**It outlives the score that created it.** A score is a reading with a
stated expiry; an opportunity is a commitment. The score is the reason it
was *opened*, never the reason it stays open — a seller mid-deal must not
watch it vanish because no provider payload arrived for six weeks.

**Its identity is stable and its history is append-only.** The aggregate is
written once and never updated; every state change is a new row recording
the *complete* workflow state. The status **is** the audit log rather than
something kept beside it, so the two cannot disagree.

**Its id is allocated, not derived** — the first in the pipeline. Derived
identity is what makes rebuildable things deduplicate, and an opportunity
is not rebuildable: a derived id would collide a human-managed object with
a re-run.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Final
from uuid import UUID

PAYLOAD_VERSION: Final = 1


class OwnerScope(StrEnum):
    """Whose work a seller is asking to see.

    **Applied in the page query, never over the page.** The attention list is
    cursor-paginated, so filtering returned rows would mean *"mine on this
    page"* — which reads correctly at twelve accounts and silently becomes a
    lie at two hundred. **Correct semantics beat convenience**, and the cost is
    one predicate.
    """

    ALL = "all"
    MINE = "mine"
    UNASSIGNED = "unassigned"


class Stage(StrEnum):
    """Where an opportunity stands.

    **`TRACKING` is the only machine-authored stage.** Everything after it
    requires a human, which puts the intelligence/workflow boundary in the
    data itself rather than only in prose.
    """

    TRACKING = "tracking"
    """Signora suggests tracking this account. Nobody has committed."""

    ENGAGED = "engaged"
    """A human has taken it up."""

    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    """Pursued and lost — a sales outcome."""

    DISMISSED = "dismissed"
    """Not a real opportunity: *we should not have been shown this.*

    **Deliberately distinct from `CLOSED_LOST`.** One is feedback about
    Signora's judgement, the other is a sales outcome, and collapsing them
    would destroy the only signal the platform gets about its own
    qualification quality — the same discipline that made `IGNORED` distinct
    from absence in the Signal Engine.
    """


#: The one stage Signora may author. Everything else needs a person.
MACHINE_AUTHORED: Final = frozenset({Stage.TRACKING})

#: Stages in which an opportunity is still live work.
OPEN_STAGES: Final = frozenset({Stage.TRACKING, Stage.ENGAGED})

#: Reached and finished. `CLOSED_WON` is *terminal*; the others may reopen.
TERMINAL_STAGES: Final = frozenset({Stage.CLOSED_WON, Stage.CLOSED_LOST, Stage.DISMISSED})

_ALLOWED: Final[dict[Stage, frozenset[Stage]]] = {
    Stage.TRACKING: frozenset({Stage.ENGAGED, Stage.CLOSED_LOST, Stage.DISMISSED}),
    Stage.ENGAGED: frozenset({Stage.CLOSED_WON, Stage.CLOSED_LOST, Stage.DISMISSED}),
    # Reopening is a transition, not a new opportunity: one history in one
    # place, and one stable id for the human — and for the CRM that will
    # hold a reference to it.
    Stage.CLOSED_LOST: frozenset({Stage.TRACKING, Stage.ENGAGED}),
    Stage.DISMISSED: frozenset({Stage.TRACKING, Stage.ENGAGED}),
    # A won deal does not reopen. The next deal at that account is genuinely
    # a new opportunity, and conflating them would distort every win-rate
    # figure computed later.
    Stage.CLOSED_WON: frozenset(),
}


class EvidenceState(StrEnum):
    """How the intelligence behind an opportunity is holding up.

    **Derived at read time from the current score, never stored and never a
    transition.** Storing it would cache derived intelligence in a workflow
    row, which is the one thing this module exists not to do — and making it
    a transition would let a data refresh silently revoke a human decision.
    """

    CURRENT = "current"
    """A live score exists and is within its stated validity."""

    COOLING = "cooling"
    """The current score has fallen materially since the opportunity opened."""

    STALE = "stale"
    """The score is past its validity, or no live score exists at all."""


class Qualification(StrEnum):
    """Who decided this was worth tracking."""

    AUTOMATIC = "automatic"
    """Signora suggested it. Still only a suggestion — the opportunity opens
    at `TRACKING`, which commits nobody."""

    MANUAL = "manual"
    """A human opened it directly, whatever the score said."""


class OpportunityError(ValueError):
    """An opportunity or transition was constructed that violates an
    invariant."""


@dataclass(frozen=True, slots=True)
class Opportunity:
    """Created once, never updated. Its state lives in `OpportunityState`."""

    id: UUID
    workspace_id: UUID
    entity_id: UUID
    #: How many opportunities this entity has had before. Part of a unique
    #: key, so two concurrent qualifications conflict rather than both
    #: opening one — the same technique derived identity uses upstream.
    generation: int

    #: The score that **caused this to exist**. Immutable, and readable
    #: forever because scores are immutable: the explanation chain does not
    #: break when the score is later superseded.
    originating_buying_score_id: UUID
    #: The number at the moment of qualification. A **historical fact**, not
    #: a cache of a current value — the same reasoning as `signal.relevance`,
    #: and it keeps the opportunity self-describing without a join.
    score_at_creation: int
    contested_at_creation: bool

    qualification: Qualification
    policy_version: int
    created_at: datetime
    created_by: UUID
    payload_version: int = PAYLOAD_VERSION

    def __post_init__(self) -> None:
        if self.generation < 0:
            raise OpportunityError("an opportunity's generation cannot be negative.")
        if self.score_at_creation < 0:
            raise OpportunityError("An opportunity cannot record a negative score at creation.")


@dataclass(frozen=True, slots=True)
class OpportunityState:
    """One complete statement of workflow state, appended and never edited.

    Records **state, not a delta**. Reading the current state is one row; a
    future workflow field needs no discriminator; and no row can describe a
    transition whose starting point disagrees with the row before it.
    """

    id: UUID
    opportunity_id: UUID
    workspace_id: UUID
    #: Monotonic from 0. Ordering that does not depend on clock resolution.
    sequence: int
    stage: Stage
    #: Who holds it now. `None` until a human takes it up.
    owner_id: UUID | None
    #: Who caused this state. `None` only for the opening `TRACKING` row,
    #: which is the one state Signora may author.
    actor_id: UUID | None
    #: Why. *"Someone changed it"* is not an explanation, and workflow has
    #: to explain itself as thoroughly as intelligence does.
    reason: str
    occurred_at: datetime

    def __post_init__(self) -> None:
        if self.sequence < 0:
            raise OpportunityError("a state sequence cannot be negative.")
        if self.actor_id is None and self.stage not in MACHINE_AUTHORED:
            raise OpportunityError(
                f"stage '{self.stage}' has no actor. **Intelligence suggests; humans commit** — "
                "only TRACKING may be machine-authored, and every stage beyond it names the "
                "person who decided it."
            )
        if not self.reason.strip():
            raise OpportunityError(
                f"State {self.sequence} of this opportunity has no reason. "
                "Workflow that cannot explain itself is worse than intelligence that cannot: a "
                "human chose it, and the choice is the record."
            )

    @property
    def is_open(self) -> bool:
        return self.stage in OPEN_STAGES

    @property
    def is_machine_authored(self) -> bool:
        return self.actor_id is None


def opening_state(
    *,
    state_id: UUID,
    opportunity: Opportunity,
    reason: str,
    actor_id: UUID | None,
    occurred_at: datetime,
) -> OpportunityState:
    """The first state row, written in the same transaction as the aggregate.

    Always `TRACKING`, and owned by nobody: qualification is a suggestion.
    A manually opened opportunity carries its actor; an automatically
    qualified one carries none, because Signora is not a person.
    """
    return OpportunityState(
        id=state_id,
        opportunity_id=opportunity.id,
        workspace_id=opportunity.workspace_id,
        sequence=0,
        stage=Stage.TRACKING,
        owner_id=None,
        actor_id=actor_id,
        reason=reason,
        occurred_at=occurred_at,
    )


def next_state(
    current: OpportunityState,
    *,
    state_id: UUID,
    stage: Stage,
    owner_id: UUID | None,
    actor_id: UUID,
    reason: str,
    occurred_at: datetime,
) -> OpportunityState:
    """Advance workflow. **Always requires a human actor.**

    There is no machine path to this function, and that is the structural
    form of the principle: the type system requires an `actor_id`, so code
    that progresses an opportunity without a person does not compile.
    """
    if stage is current.stage and owner_id == current.owner_id:
        # **No identifier in the message** (R4-03). This reaches a customer
        # verbatim, and the opportunity id is already on the row they are
        # looking at, in the log line and on the correlation id. It was here
        # because the sentence was written for a log and became customer copy
        # at M12.3 without anybody re-reading it as one.
        raise OpportunityError(
            f"This account is already {stage} with the same owner. "
            "A state row that changes nothing is noise in the audit trail."
        )
    if stage is not current.stage and stage not in _ALLOWED[current.stage]:
        raise OpportunityError(
            f"'{current.stage}' cannot become '{stage}'. "
            + (
                "A won deal does not reopen — the next deal at that account is genuinely a new "
                "opportunity, and conflating them distorts every win-rate figure computed later."
                if current.stage is Stage.CLOSED_WON
                # Joined, not repr'd. `sorted(...)` of a generator rendered a
                # **Python list literal** into a sentence a salesperson reads —
                # brackets, quotes and all (R4-03, found while fixing it).
                else "Allowed from here: "
                + ", ".join(sorted(s.value for s in _ALLOWED[current.stage]))
                + "."
            )
        )
    return OpportunityState(
        id=state_id,
        opportunity_id=current.opportunity_id,
        workspace_id=current.workspace_id,
        sequence=current.sequence + 1,
        stage=stage,
        owner_id=owner_id,
        actor_id=actor_id,
        reason=reason,
        occurred_at=occurred_at,
    )


def allowed_from(stage: Stage) -> frozenset[Stage]:
    return _ALLOWED[stage]

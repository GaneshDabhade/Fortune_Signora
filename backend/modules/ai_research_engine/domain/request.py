"""Somebody asked for research. **The act, not the answer.**

Every other object in this module records what research *found*. This one
records that a person wanted it — and the two are different kinds of fact,
which is why they are different tables rather than a status column on
`research_task`.

    ResearchRequest        a human asked          workflow state
    ResearchTask           a run happened         operational history
    ResearchFinding        a comparison           DERIVED knowledge
    ResearchSynthesis      a model wrote          INFERRED knowledge

**`research_task` deliberately holds no status**, and adding one was the first
design considered and rejected. `Research.run()` writes nothing until every
step has succeeded, precisely so that *"a run that stored its findings and then
failed cannot look, to a later reader, like a completed run that found things
and said nothing."* A status column would put mutable workflow state on the row
that gives findings their `task_id`, mixing two of the four data categories
CLAUDE.md §2 keeps apart.

---

**History is append-only, exactly as an opportunity's is.** No table in this
repository has carried an `UPDATE` grant since migration `0008`, and this one
does not either. A request is written once; every change of status is a new
`ResearchRequestState` row stating the status *completely*, and the current
status is the highest sequence. The status therefore **is** the audit trail
rather than something kept beside it, so the two cannot disagree — the same
shape, and the same reason, as `opportunity_state`.

**A request's id is minted, not derived.** Asking twice is asking twice, even
about the same account over the same evidence. That is Rule 1 of the Knowledge
Contract applied to an act rather than to a computation, and it is why a
re-request produces a second request while the findings underneath it collide
on their derived ids and insert nothing.

**`generation` is the only field here nobody asked for.** It is a uniqueness
device, borrowed unchanged from `Opportunity`, and it is what makes two
simultaneous clicks resolve to one run: both compute the same number and one
loses on the unique constraint. It is deliberately not shown to anybody.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Final
from uuid import UUID

PAYLOAD_VERSION: Final = 1


class ResearchStatus(StrEnum):
    """Where a request stands.

    **Five statuses, and the two that look redundant are the two that matter
    most.** A customer waiting on a minute-long task needs to know whether the
    work has started, and a run that legitimately found nothing must not be
    reported as a failure — the product would be blaming itself for an account
    that simply has little evidence.
    """

    REQUESTED = "requested"
    """Accepted and durably recorded. Nothing has run yet."""

    RUNNING = "running"
    """A worker picked it up. The model is being called."""

    COMPLETED = "completed"
    """A research artifact exists and can be read."""

    NOTHING_TO_RESEARCH = "nothing_to_research"
    """The run finished and there was nothing worth comparing.

    **Not a failure, and never reported as one.** `Research.run()` returns
    `None` for an account whose evidence a plan finds nothing in, and an
    account with two business events from one provider is a legitimate case of
    that. Collapsing it into `FAILED` would teach a seller to distrust the
    product on exactly the accounts where it is behaving correctly.
    """

    FAILED = "failed"
    """The run raised. The reason is recorded verbatim."""


#: A request that has not finished. **The in-flight guard reads this set**, so
#: adding a status without deciding which side it falls on is a type error at
#: the point that matters rather than a silent second run.
IN_FLIGHT: Final = frozenset({ResearchStatus.REQUESTED, ResearchStatus.RUNNING})

#: Reached an end. A request in one of these may be asked again.
SETTLED: Final = frozenset(
    {ResearchStatus.COMPLETED, ResearchStatus.NOTHING_TO_RESEARCH, ResearchStatus.FAILED}
)

_ALLOWED: Final[dict[ResearchStatus, frozenset[ResearchStatus]]] = {
    ResearchStatus.REQUESTED: frozenset({ResearchStatus.RUNNING, ResearchStatus.FAILED}),
    ResearchStatus.RUNNING: frozenset(
        {ResearchStatus.COMPLETED, ResearchStatus.NOTHING_TO_RESEARCH, ResearchStatus.FAILED}
    ),
    # Settled is settled. A second run is a second *request*, which keeps one
    # request's history readable as one attempt — and stops a retry silently
    # overwriting the reason the first one failed.
    ResearchStatus.COMPLETED: frozenset(),
    ResearchStatus.NOTHING_TO_RESEARCH: frozenset(),
    ResearchStatus.FAILED: frozenset(),
}


class ResearchRequestError(ValueError):
    """A request was asked to do something its history does not permit."""


@dataclass(frozen=True, slots=True)
class ResearchRequest:
    """One person's ask, about one account.

    Holds no status of its own — see the module docstring. It names *what* was
    asked about and *who* asked; where it has got to is the state history.
    """

    id: UUID
    workspace_id: UUID
    entity_id: UUID
    opportunity_id: UUID
    #: **The verified principal, never a value from a request body.** Research
    #: costs a model call and a minute of a worker; who spent it is the kind
    #: of fact nothing can reconstruct if it is wrong.
    requested_by: UUID
    requested_at: datetime
    #: How many times this account has been researched, counting from 0. **A
    #: uniqueness device, not a fact a customer wants** — `Opportunity` carries
    #: one for the same reason and it reaches no screen there either.
    generation: int = 0


@dataclass(frozen=True, slots=True)
class ResearchRequestState:
    """A complete statement of where a request stands, at one moment.

    Not a delta. Two rows can never describe a change whose starting point
    disagrees with the row before it, because neither row mentions a starting
    point.
    """

    request_id: UUID
    workspace_id: UUID
    sequence: int
    status: ResearchStatus
    occurred_at: datetime
    #: The artifact this run produced. Set on `COMPLETED` and on nothing else —
    #: which is what makes *"is there something to read?"* one field rather
    #: than a join that might return nothing.
    task_id: UUID | None = None
    #: Why it failed, verbatim. Set on `FAILED` and on nothing else.
    detail: str | None = None

    def __post_init__(self) -> None:
        if self.sequence < 0:
            raise ResearchRequestError("a state's sequence cannot be negative.")
        if (self.status is ResearchStatus.COMPLETED) != (self.task_id is not None):
            raise ResearchRequestError(
                "a completed request names its artifact and no other status has one. "
                f"Status {self.status.value!r} with an artifact named would make "
                "'is there something to read?' answerable two different ways."
            )
        # `.strip()`, not truthiness. A reason of `"   "` is no reason, and
        # the database's own CHECK is `length(trim(detail)) > 0` — a domain
        # that accepted what the table refuses would fail at the last
        # possible moment, in a worker, with a constraint name for a message.
        if (self.status is ResearchStatus.FAILED) != bool((self.detail or "").strip()):
            raise ResearchRequestError(
                "a failed request states why, and only a failed request does. "
                f"Status {self.status.value!r} with detail {self.detail!r} would either "
                "hide a reason or invent one."
            )


def opening_state(request: ResearchRequest) -> ResearchRequestState:
    """The first row of a request's history. Always `REQUESTED`, always `0`."""
    return ResearchRequestState(
        request_id=request.id,
        workspace_id=request.workspace_id,
        sequence=0,
        status=ResearchStatus.REQUESTED,
        occurred_at=request.requested_at,
    )


def next_state(
    current: ResearchRequestState,
    status: ResearchStatus,
    *,
    occurred_at: datetime,
    task_id: UUID | None = None,
    detail: str | None = None,
) -> ResearchRequestState:
    """The next row, or a refusal explaining itself.

    The only way to build a state after the first, so an illegal history
    cannot be constructed — not by a handler, not by a repository, and not by
    a test that would then be asserting something the product cannot do.
    """
    if status not in _ALLOWED[current.status]:
        allowed = ", ".join(sorted(s.value for s in _ALLOWED[current.status])) or "nothing"
        raise ResearchRequestError(
            f"a {current.status.value!r} research request cannot become {status.value!r}. "
            f"It may become: {allowed}."
        )
    return ResearchRequestState(
        request_id=current.request_id,
        workspace_id=current.workspace_id,
        sequence=current.sequence + 1,
        status=status,
        occurred_at=occurred_at,
        task_id=task_id,
        detail=detail,
    )

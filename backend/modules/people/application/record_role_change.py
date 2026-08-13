"""A role change becomes an affiliation — an arrival opens one, a departure
closes the one it can identify.

**[TASK-428](../../../../docs/BACKLOG.md), M-I stage S3, narrowed to this
lane's modules** ([C-336](../../../../docs/LANE_COORDINATION.md)).

> **This is what stops `people` being a schema nothing writes to.**
> [52](../../../../docs/architecture/52-people.md) recorded the gap in its own
> words — *"nothing populates these tables. No event handler, no use case, no
> endpoint"* — and this is the use case half of that sentence.

### The rule was written first, and this obeys it rather than restating it

`domain/matching_rule.py` decides **which** affiliation a departure closes, and
[52](../../../../docs/architecture/52-people.md) already told whoever arrived
here what to do with it:

> **Read `match_departure` before writing a handler.** The handler's job is to
> supply the open affiliations and act on the outcome — **including doing
> nothing on `AMBIGUOUS`**, which is the case a handler is most likely to get
> wrong by picking one.

⛔ **So this module never inspects `candidates` to choose.** On `AMBIGUOUS` the
departure is real, its subject is unknowable from the event, and **nothing is
closed** — a caller that picked would be making the judgement the domain
declined to make, in the module least equipped to review it.

### What it is not

⛔ **It does not decide what a role change *means*.** No score, no seniority
ranking, no *"this is a key contact"* — `test_boundary.py` reads this package
as a syntax tree and refuses those words. **Influence is
`buying_score_engine`'s.**

⛔ **It mints no name.** [C-221](../../../../docs/LANE_COORDINATION.md): a
`Person` is anonymous, and an arrival creates an identity to hang an interval
on rather than a profile.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID, uuid4

from modules.people.application.ports import PeopleRepository
from modules.people.domain.affiliation import Affiliation, RoleInterval
from modules.people.domain.matching_rule import MatchOutcome, match_departure
from modules.people.domain.person import Person


@dataclass(frozen=True, slots=True)
class RoleChange:
    """One reported movement in or out of a role.

    **The vocabulary is the provider's, carried rather than re-derived** —
    `title` and `seniority` are what `RoleChangeValue` already supplies and
    what `business_event_engine`'s rules already filter on. Re-deriving either
    here would put a second vocabulary in the module that owns none.
    """

    workspace_id: UUID
    #: The company as the Knowledge Graph knows it.
    company_id: UUID
    title: str
    seniority: str
    #: When it happened in the customer's business — **never when Signora
    #: concluded it.** An affiliation dated by detection would put an arrival
    #: after the departure that followed it.
    occurred_on: date


@dataclass(frozen=True, slots=True)
class Arrival:
    """What an appointment did. **Always exactly one new affiliation.**"""

    person_id: UUID
    affiliation_id: UUID


@dataclass(frozen=True, slots=True)
class Departure:
    """What a departure did, **including when it deliberately did nothing.**

    ⚠️ **`outcome` is reported rather than swallowed.** A departure that closed
    nothing is not a no-op: on `NONE_OPEN` the person was in post before
    Signora started watching, and on `AMBIGUOUS` two people hold the title and
    the subject is unknowable. **Both are facts a caller may want to surface**,
    and collapsing them into *"nothing happened"* discards a real departure —
    [P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md)'s shape, one module
    over: absence must never be indistinguishable from failure.
    """

    outcome: MatchOutcome
    #: The affiliation actually closed, or `None` when the rule refused.
    closed: UUID | None
    #: How many open affiliations carried that title. **`2` on `AMBIGUOUS` is
    #: what lets a consumer say *"one of these two left"*** rather than nothing.
    candidate_count: int


class RecordRoleChange:
    """Turns reported role changes into the interval history."""

    def __init__(self, repository: PeopleRepository) -> None:
        self._repository = repository

    async def arrived(self, change: RoleChange, *, actor_id: UUID) -> Arrival:
        """Somebody took a role. **A new person and a new open interval.**

        ⚠️ **Every arrival mints a new `Person`, and that is still true here
        even though it will sometimes be the same human twice.** This use case
        is fed by `ROLE_CHANGE`, which carries
        `RoleChangeValue(title, seniority, direction)` and **no identifier** —
        so there is nothing to match an arrival against, and inventing a
        heuristic on title alone would merge two strangers who share a job
        title.

        ✅ **The identifier now exists, and it arrives by a different door.**
        ❓1 of [ADR-0400](../../../../docs/architecture/adr/0400-person-as-an-entity.md)
        asked whether a provider could supply one; **[TASK-429](../../../../docs/BACKLOG.md)
        answered it** — `ClaimAttribute.PERSON_IDENTITY` carries a
        provider-stable `person_ref` alongside the title, and Apollo emits one
        per roster member. ⛔ **Nothing consumes it into this module yet**, and
        that is [TASK-428](../../../../docs/BACKLOG.md)'s stage S5, which named
        this row as its gate. **Until then a duplicate `Person` is a known
        limitation with an owner, rather than a defect nobody has noticed.**
        """
        person = Person(id=uuid4(), workspace_id=change.workspace_id)
        await self._repository.add_person(person, actor_id=actor_id)

        affiliation = Affiliation(
            id=uuid4(),
            workspace_id=change.workspace_id,
            person_id=person.id,
            company_id=change.company_id,
            title=change.title,
            seniority=change.seniority,
            interval=RoleInterval(started_on=change.occurred_on),
        )
        await self._repository.add_affiliation(affiliation, actor_id=actor_id)

        return Arrival(person_id=person.id, affiliation_id=affiliation.id)

    async def departed(self, change: RoleChange, *, actor_id: UUID) -> Departure:
        """Somebody left a role, **if the rule can say which one.**

        ⛔ **`AMBIGUOUS` closes nothing and is not an error.** The rule declined
        to guess; this reports the refusal upward with its candidate count
        instead of resolving it, because resolving it would be exactly the
        judgement `match_departure` exists to refuse.
        """
        open_affiliations = await self._repository.open_at_company(
            change.workspace_id, change.company_id
        )
        match = match_departure(
            open_affiliations, company_id=change.company_id, title=change.title
        )

        closes = match.closes
        if closes is None:
            return Departure(
                outcome=match.outcome,
                closed=None,
                candidate_count=len(match.candidates),
            )

        ended = Affiliation(
            id=closes.id,
            workspace_id=closes.workspace_id,
            person_id=closes.person_id,
            company_id=closes.company_id,
            title=closes.title,
            seniority=closes.seniority,
            interval=closes.interval.closed_on(change.occurred_on),
        )
        await self._repository.close_affiliation(ended, actor_id=actor_id)

        return Departure(
            outcome=match.outcome,
            closed=ended.id,
            candidate_count=len(match.candidates),
        )


__all__ = ["Arrival", "Departure", "RecordRoleChange", "RoleChange"]

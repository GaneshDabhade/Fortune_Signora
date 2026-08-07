"""A role change becomes an affiliation — and a departure that cannot be
identified closes nothing.

**[TASK-428](../../../docs/BACKLOG.md), M-I stage S3.** The use case that
makes `people` populated for the first time.

**The refusals are the substance.** An arrival is four lines. What this file
mostly asserts is that a departure the rule cannot attribute leaves the
history alone and says so — because a handler picking from `candidates` is the
single most likely way this module starts making judgements it is forbidden to
make, and [52](../../../docs/architecture/52-people.md) named that risk before
the handler existed.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pytest

from modules.people.application.record_role_change import (
    RecordRoleChange,
    RoleChange,
)
from modules.people.domain.affiliation import Affiliation, RoleInterval
from modules.people.domain.matching_rule import MatchOutcome
from modules.people.domain.person import Person

ARRIVED = date(2026, 3, 1)
LEFT = date(2026, 9, 30)


class FakeRepository:
    """In memory, and honest about ordering — `open_at_company` returns only
    what is genuinely open, exactly as the real one must."""

    def __init__(self, *, existing: tuple[Affiliation, ...] = ()) -> None:
        self.people: list[Person] = []
        self.affiliations: list[Affiliation] = list(existing)
        self.closed: list[Affiliation] = []
        self.actors: list[UUID] = []

    async def add_person(self, person: Person, *, actor_id: UUID) -> None:
        self.people.append(person)
        self.actors.append(actor_id)

    async def add_affiliation(self, affiliation: Affiliation, *, actor_id: UUID) -> None:
        self.affiliations.append(affiliation)
        self.actors.append(actor_id)

    async def open_at_company(
        self, workspace_id: UUID, company_id: UUID
    ) -> tuple[Affiliation, ...]:
        return tuple(
            a
            for a in self.affiliations
            if a.workspace_id == workspace_id
            and a.company_id == company_id
            and a.interval.is_open
        )

    async def close_affiliation(self, affiliation: Affiliation, *, actor_id: UUID) -> None:
        self.closed.append(affiliation)
        self.affiliations = [a for a in self.affiliations if a.id != affiliation.id]
        self.affiliations.append(affiliation)
        self.actors.append(actor_id)

    async def affiliations_for(
        self, workspace_id: UUID, person_id: UUID
    ) -> tuple[Affiliation, ...]:
        return tuple(a for a in self.affiliations if a.person_id == person_id)


WORKSPACE = uuid4()
COMPANY = uuid4()


def _change(*, title: str = "VP of Engineering", on: date = ARRIVED) -> RoleChange:
    return RoleChange(
        workspace_id=WORKSPACE,
        company_id=COMPANY,
        title=title,
        seniority="vp",
        occurred_on=on,
    )


def _open_affiliation(
    *, title: str = "VP of Engineering", company: UUID = COMPANY
) -> Affiliation:
    return Affiliation(
        id=uuid4(),
        workspace_id=WORKSPACE,
        person_id=uuid4(),
        company_id=company,
        title=title,
        seniority="vp",
        interval=RoleInterval(started_on=ARRIVED),
    )


class TestAnArrivalOpensAnInterval:
    @pytest.mark.asyncio
    async def test_it_creates_a_person_and_an_open_affiliation(self) -> None:
        repo = FakeRepository()
        actor = uuid4()

        arrival = await RecordRoleChange(repo).arrived(_change(), actor_id=actor)

        assert len(repo.people) == 1
        assert repo.people[0].id == arrival.person_id
        assert len(repo.affiliations) == 1

        opened = repo.affiliations[0]
        assert opened.id == arrival.affiliation_id
        assert opened.person_id == arrival.person_id
        assert opened.interval.is_open
        assert opened.interval.started_on == ARRIVED
        assert opened.title == "VP of Engineering"

    @pytest.mark.asyncio
    async def test_every_write_is_attributed(self) -> None:
        """`actor_id` has no default anywhere in this module, and the use case
        must not invent one."""
        repo = FakeRepository()
        actor = uuid4()

        await RecordRoleChange(repo).arrived(_change(), actor_id=actor)

        assert repo.actors == [actor, actor]

    @pytest.mark.asyncio
    async def test_the_person_carries_no_identity(self) -> None:
        """C-221: an arrival mints a subject, never a profile."""
        repo = FakeRepository()

        await RecordRoleChange(repo).arrived(_change(), actor_id=uuid4())

        assert {f for f in Person.__slots__} == {"id", "workspace_id"}


class TestADepartureClosesOnlyWhatItCanIdentify:
    @pytest.mark.asyncio
    async def test_one_open_holder_is_closed(self) -> None:
        existing = _open_affiliation()
        repo = FakeRepository(existing=(existing,))

        departure = await RecordRoleChange(repo).departed(
            _change(on=LEFT), actor_id=uuid4()
        )

        assert departure.outcome is MatchOutcome.MATCHED
        assert departure.closed == existing.id
        assert repo.closed[0].interval.ended_on == LEFT

    @pytest.mark.asyncio
    async def test_two_holders_close_nothing_and_say_so(self) -> None:
        """⛔ **The case the module doc named as most likely to be got wrong.**
        Picking one would be the judgement `match_departure` exists to refuse.
        """
        repo = FakeRepository(existing=(_open_affiliation(), _open_affiliation()))

        departure = await RecordRoleChange(repo).departed(
            _change(on=LEFT), actor_id=uuid4()
        )

        assert departure.outcome is MatchOutcome.AMBIGUOUS
        assert departure.closed is None
        assert departure.candidate_count == 2
        assert repo.closed == []

    @pytest.mark.asyncio
    async def test_nobody_recorded_in_the_role_closes_nothing(self) -> None:
        """Not an error. Signora never saw the arrival — the person was in post
        before it started watching."""
        repo = FakeRepository()

        departure = await RecordRoleChange(repo).departed(
            _change(on=LEFT), actor_id=uuid4()
        )

        assert departure.outcome is MatchOutcome.NONE_OPEN
        assert departure.closed is None
        assert departure.candidate_count == 0
        assert repo.closed == []

    @pytest.mark.asyncio
    async def test_a_departure_at_another_company_is_not_this_one(self) -> None:
        """The same title is held at every company in the workspace."""
        repo = FakeRepository(existing=(_open_affiliation(company=uuid4()),))

        departure = await RecordRoleChange(repo).departed(
            _change(on=LEFT), actor_id=uuid4()
        )

        assert departure.outcome is MatchOutcome.NONE_OPEN
        assert repo.closed == []

    @pytest.mark.asyncio
    async def test_an_already_closed_interval_is_not_reopened_or_reclosed(self) -> None:
        """The domain refuses a second close; the use case must not route
        around it by matching a closed interval."""
        closed = Affiliation(
            id=uuid4(),
            workspace_id=WORKSPACE,
            person_id=uuid4(),
            company_id=COMPANY,
            title="VP of Engineering",
            seniority="vp",
            interval=RoleInterval(started_on=ARRIVED, ended_on=LEFT),
        )
        repo = FakeRepository(existing=(closed,))

        departure = await RecordRoleChange(repo).departed(
            _change(on=date(2026, 11, 1)), actor_id=uuid4()
        )

        assert departure.outcome is MatchOutcome.NONE_OPEN
        assert repo.closed == []


class TestTheHistorySurvivesTheDeparture:
    @pytest.mark.asyncio
    async def test_the_closed_interval_keeps_its_start_and_its_person(self) -> None:
        """*"Priya left Acme" is not a mutation of Priya — it is an interval
        closing* (ADR-0400). Closing must not lose who or when."""
        existing = _open_affiliation()
        repo = FakeRepository(existing=(existing,))

        await RecordRoleChange(repo).departed(_change(on=LEFT), actor_id=uuid4())

        ended = repo.closed[0]
        assert ended.person_id == existing.person_id
        assert ended.company_id == existing.company_id
        assert ended.title == existing.title
        assert ended.seniority == existing.seniority
        assert ended.interval.started_on == ARRIVED
        assert ended.interval.ended_on == LEFT

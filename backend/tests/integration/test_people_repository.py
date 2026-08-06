"""The People tables, under real Row-Level Security.

**No API drives this**, and that is stated rather than worked around: TASK-427
delivers a domain and its persistence, [441 §4](../../../docs/architecture/441-people-roadmap.md)
records that it has *"(none — no screen)"*, and the consumers that populate it
are S3. Testing through a door a customer does not have would be wrong; there
is no door yet, so these exercise the repository against a real database with
the same tenant context every request establishes.
"""

from datetime import date
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.people.domain.affiliation import Affiliation, RoleInterval
from modules.people.domain.matching_rule import MatchOutcome, match_departure
from modules.people.domain.person import Person
from modules.people.infrastructure.repository import SqlPeopleRepository
from signora_platform.db.session import set_workspace_context

pytestmark = pytest.mark.integration

MARCH = date(2026, 3, 1)
SEPTEMBER = date(2026, 9, 1)


def _affiliation(workspace: UUID, person: UUID, company: UUID, *, title: str) -> Affiliation:
    return Affiliation(
        id=uuid4(),
        workspace_id=workspace,
        person_id=person,
        company_id=company,
        title=title,
        seniority="vp",
        interval=RoleInterval(started_on=MARCH),
    )


async def _seed(
    session: AsyncSession, workspace: UUID, company: UUID, *, title: str, actor: UUID
) -> Affiliation:
    repository = SqlPeopleRepository(session)
    person = Person(id=uuid4(), workspace_id=workspace)
    await repository.add_person(person, actor_id=actor)
    affiliation = _affiliation(workspace, person.id, company, title=title)
    await repository.add_affiliation(affiliation, actor_id=actor)
    return affiliation


class TestAnIntervalSurvivesTheRoundTrip:
    async def test_an_open_affiliation_comes_back_open(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        workspace, company, actor = uuid4(), uuid4(), uuid4()

        async with session_factory() as session, session.begin():
            await set_workspace_context(session, workspace)
            seeded = await _seed(session, workspace, company, title="VP of Engineering", actor=actor)

            found = await SqlPeopleRepository(session).open_at_company(workspace, company)

        assert [a.id for a in found] == [seeded.id]
        assert found[0].is_current
        assert found[0].title == "VP of Engineering"

    async def test_closing_it_leaves_the_start_untouched(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """**A departure closes an interval; it does not edit a person.**"""
        workspace, company, actor = uuid4(), uuid4(), uuid4()

        async with session_factory() as session, session.begin():
            await set_workspace_context(session, workspace)
            seeded = await _seed(session, workspace, company, title="CFO", actor=actor)
            repository = SqlPeopleRepository(session)

            await repository.close_affiliation(seeded.ended(on=SEPTEMBER), actor_id=actor)

            still_open = await repository.open_at_company(workspace, company)
            history = await repository.affiliations_for(workspace, seeded.person_id)

        assert still_open == ()
        assert history[0].interval.started_on == MARCH
        assert history[0].interval.ended_on == SEPTEMBER

    async def test_a_second_close_changes_nothing(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """**The database refuses what the domain refuses.**

        The domain raises on a second close; this proves the `ended_on IS NULL`
        predicate also holds when two processes cannot see each other — the
        case the domain structurally cannot cover.
        """
        workspace, company, actor = uuid4(), uuid4(), uuid4()

        async with session_factory() as session, session.begin():
            await set_workspace_context(session, workspace)
            seeded = await _seed(session, workspace, company, title="CTO", actor=actor)
            repository = SqlPeopleRepository(session)
            await repository.close_affiliation(seeded.ended(on=SEPTEMBER), actor_id=actor)

            # A racing process that read the row before the first close.
            stale = seeded.ended(on=date(2026, 12, 1))
            await repository.close_affiliation(stale, actor_id=actor)

            history = await repository.affiliations_for(workspace, seeded.person_id)

        assert history[0].interval.ended_on == SEPTEMBER


class TestTheRuleReadsWhatTheDatabaseHolds:
    async def test_two_open_roles_with_one_title_refuse_to_match(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        workspace, company, actor = uuid4(), uuid4(), uuid4()

        async with session_factory() as session, session.begin():
            await set_workspace_context(session, workspace)
            await _seed(session, workspace, company, title="VP of Engineering", actor=actor)
            await _seed(session, workspace, company, title="VP of Engineering", actor=actor)

            open_now = await SqlPeopleRepository(session).open_at_company(workspace, company)

        found = match_departure(open_now, company_id=company, title="VP of Engineering")
        assert found.outcome is MatchOutcome.AMBIGUOUS
        assert found.closes is None


class TestOneWorkspaceNeverSeesAnothersPeople:
    async def test_a_second_tenants_affiliations_are_invisible(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Two customers tracking the same real human hold two unrelated rows,
        and neither may read the other's."""
        mine, theirs, company, actor = uuid4(), uuid4(), uuid4(), uuid4()

        async with session_factory() as session, session.begin():
            await set_workspace_context(session, theirs)
            await _seed(session, theirs, company, title="VP of Engineering", actor=actor)

        async with session_factory() as session, session.begin():
            await set_workspace_context(session, mine)
            found = await SqlPeopleRepository(session).open_at_company(mine, company)

        assert found == ()

    async def test_the_same_company_is_read_independently_by_each(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        mine, theirs, company, actor = uuid4(), uuid4(), uuid4(), uuid4()

        async with session_factory() as session, session.begin():
            await set_workspace_context(session, theirs)
            await _seed(session, theirs, company, title="CFO", actor=actor)
        async with session_factory() as session, session.begin():
            await set_workspace_context(session, mine)
            await _seed(session, mine, company, title="CFO", actor=actor)

        async with session_factory() as session, session.begin():
            await set_workspace_context(session, mine)
            found = await SqlPeopleRepository(session).open_at_company(mine, company)

        assert len(found) == 1
        assert found[0].workspace_id == mine

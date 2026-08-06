"""The repository port, and the property that makes it a boundary.

⚠️ **Written 2026-08-06 after `make coverage-debt` reported
`application/ports.py` at 0%** — a file [TASK-427](../../../docs/BACKLOG.md)
introduced, which the Definition of Done forbids. **The gate found it; this
lane had not run the gate before handing the slice to QE.**

**Not coverage theatre.** The M5B finding this repository already records —
*"if a fake cannot stand in for a dependency, the dependency was never really a
boundary"* — is the assertion, and a Protocol nobody has ever substituted is a
Protocol nobody has checked is substitutable.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

from modules.people.application.ports import PeopleRepository
from modules.people.domain.affiliation import Affiliation, RoleInterval
from modules.people.domain.person import Person


class InMemoryPeople:
    """A fake that stands in for the real repository, and does so completely."""

    def __init__(self) -> None:
        self.people: list[Person] = []
        self.affiliations: list[Affiliation] = []

    async def add_person(self, person: Person, *, actor_id: UUID) -> None:
        self.people.append(person)

    async def add_affiliation(self, affiliation: Affiliation, *, actor_id: UUID) -> None:
        self.affiliations.append(affiliation)

    async def open_at_company(
        self, workspace_id: UUID, company_id: UUID
    ) -> tuple[Affiliation, ...]:
        return tuple(
            a
            for a in self.affiliations
            if a.workspace_id == workspace_id and a.company_id == company_id and a.is_current
        )

    async def close_affiliation(self, affiliation: Affiliation, *, actor_id: UUID) -> None:
        self.affiliations = [
            affiliation if existing.id == affiliation.id else existing
            for existing in self.affiliations
        ]

    async def affiliations_for(
        self, workspace_id: UUID, person_id: UUID
    ) -> tuple[Affiliation, ...]:
        return tuple(
            a
            for a in self.affiliations
            if a.workspace_id == workspace_id and a.person_id == person_id
        )


class TestTheRepositoryIsGenuinelyAPort:
    def test_a_fake_satisfies_it(self) -> None:
        """**`mypy --strict` accepting this line is the assertion.** If a fake
        cannot stand in, the dependency was never really a boundary."""
        repository: PeopleRepository = InMemoryPeople()
        assert repository is not None

    def test_it_offers_no_way_to_edit_a_person(self) -> None:
        """⛔ **There is no `update_person`, and that is the design.** A person
        holds nothing to update; the one in-place change in this module is
        closing an interval, which is argued in migration 0040."""
        published = {name for name in dir(PeopleRepository) if not name.startswith("_")}

        assert published == {
            "add_person",
            "add_affiliation",
            "open_at_company",
            "close_affiliation",
            "affiliations_for",
        }

    async def test_the_fake_behaves_like_the_contract_describes(self) -> None:
        """Exercises every method, so the port's shape is checked rather than
        merely declared."""
        workspace, company, actor = uuid4(), uuid4(), uuid4()
        repository: PeopleRepository = InMemoryPeople()
        person = Person(id=uuid4(), workspace_id=workspace)
        await repository.add_person(person, actor_id=actor)

        affiliation = Affiliation(
            id=uuid4(),
            workspace_id=workspace,
            person_id=person.id,
            company_id=company,
            title="CFO",
            seniority="c_level",
            interval=RoleInterval(started_on=date(2026, 3, 1)),
        )
        await repository.add_affiliation(affiliation, actor_id=actor)

        assert len(await repository.open_at_company(workspace, company)) == 1

        await repository.close_affiliation(
            affiliation.ended(on=date(2026, 9, 1)), actor_id=actor
        )

        assert await repository.open_at_company(workspace, company) == ()
        history = await repository.affiliations_for(workspace, person.id)
        assert history[0].interval.ended_on == date(2026, 9, 1)

"""The SQL implementation of `PeopleRepository`."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from modules.people.domain.affiliation import Affiliation, RoleInterval
from modules.people.domain.person import Person
from modules.people.infrastructure.models import AffiliationModel, PersonModel


def _to_affiliation(row: AffiliationModel) -> Affiliation:
    return Affiliation(
        id=row.id,
        workspace_id=row.workspace_id,
        person_id=row.person_id,
        company_id=row.company_id,
        title=row.title,
        seniority=row.seniority,
        interval=RoleInterval(started_on=row.started_on, ended_on=row.ended_on),
    )


class SqlPeopleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_person(self, person: Person, *, actor_id: UUID) -> None:
        self._session.add(
            PersonModel(
                id=person.id,
                workspace_id=person.workspace_id,
                created_by=actor_id,
                updated_by=actor_id,
            )
        )
        await self._session.flush()

    async def add_affiliation(self, affiliation: Affiliation, *, actor_id: UUID) -> None:
        self._session.add(
            AffiliationModel(
                id=affiliation.id,
                workspace_id=affiliation.workspace_id,
                person_id=affiliation.person_id,
                company_id=affiliation.company_id,
                title=affiliation.title,
                seniority=affiliation.seniority,
                started_on=affiliation.interval.started_on,
                ended_on=affiliation.interval.ended_on,
                created_by=actor_id,
                updated_by=actor_id,
            )
        )
        await self._session.flush()

    async def open_at_company(
        self, workspace_id: UUID, company_id: UUID
    ) -> tuple[Affiliation, ...]:
        rows = await self._session.execute(
            select(AffiliationModel)
            .where(
                # **Both, always.** RLS is the authoritative control and the
                # explicit predicate is defence in depth (§8) — and it is what
                # keeps the partial index on `(workspace_id, company_id)`
                # usable.
                AffiliationModel.workspace_id == workspace_id,
                AffiliationModel.company_id == company_id,
                AffiliationModel.ended_on.is_(None),
            )
            .order_by(AffiliationModel.started_on, AffiliationModel.id)
        )
        return tuple(_to_affiliation(row) for row in rows.scalars())

    async def close_affiliation(self, affiliation: Affiliation, *, actor_id: UUID) -> None:
        """**Only `ended_on` moves**, and only from `NULL`.

        The `ended_on IS NULL` predicate is the concurrency control: two
        departures racing to close one affiliation means the second updates no
        rows rather than overwriting the first's date. The domain already
        refuses a second close; this refuses it again where two processes can
        see each other, which the domain cannot.
        """
        await self._session.execute(
            update(AffiliationModel)
            .where(
                AffiliationModel.id == affiliation.id,
                AffiliationModel.workspace_id == affiliation.workspace_id,
                AffiliationModel.ended_on.is_(None),
            )
            .values(ended_on=affiliation.interval.ended_on, updated_by=actor_id)
        )
        await self._session.flush()

    async def affiliations_for(
        self, workspace_id: UUID, person_id: UUID
    ) -> tuple[Affiliation, ...]:
        rows = await self._session.execute(
            select(AffiliationModel)
            .where(
                AffiliationModel.workspace_id == workspace_id,
                AffiliationModel.person_id == person_id,
            )
            .order_by(AffiliationModel.started_on, AffiliationModel.id)
        )
        return tuple(_to_affiliation(row) for row in rows.scalars())

"""The published read side of the affiliation history.

**[C-238](../../../../docs/LANE_COORDINATION.md).** `people/public/` published
`AffiliationReader` as a `Protocol` and **nothing implemented it**, so
[TASK-458](../../../../docs/BACKLOG.md) could consume the type and could not be
wired — *"a use case its own composition root cannot construct"*.

> ⚠️ **The port was verified consumable and not verified injectable.** Lane A
> measured it across four refs before raising it, and they were right. **The
> lesson is the shape of the check, not the omission**: publishing a `Protocol`
> is half a contract until something satisfies it.

**Separated from `repository.py` on the same terms as
`commercial_profile`'s `SqlDeclaredCompetitorReader`**, which is the pattern
this copies rather than inventing a second one: everything in `repository.py`
serves this module's own use cases and may change freely; **everything here is
a contract with somebody else and may not.**

**The mapping is the boundary.** A consumer receives `AffiliationView`, never
the domain `Affiliation`, so this module's `RoleInterval`, its constructors and
its future refactors stay entirely its own.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.people.infrastructure.models import AffiliationModel
from modules.people.public import AffiliationView


def _to_view(row: AffiliationModel) -> AffiliationView:
    return AffiliationView(
        id=row.id,
        workspace_id=row.workspace_id,
        person_id=row.person_id,
        company_id=row.company_id,
        title=row.title,
        seniority=row.seniority,
        started_on=row.started_on,
        ended_on=row.ended_on,
    )


class SqlAffiliationReader:
    """Implements `AffiliationReader` for the composition root to inject."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def at_company(
        self, workspace_id: UUID, company_id: UUID
    ) -> tuple[AffiliationView, ...]:
        """Everyone recorded in a role at this company, **open and closed.**

        ⛔ **This is deliberately not `SqlPeopleRepository.open_at_company`**,
        and the difference is the whole reason the port exists. That method
        filters `ended_on IS NULL` because the matching rule only ever
        considers open intervals; **this one must include closed ones, because
        *"who left, and when"* is the question `decision_maker_departed` exists
        to answer and a read that returned only current holders could not
        answer it at all.**

        **Ordered oldest first and made total by `id`** — two affiliations can
        share a start date, and an unstable order gives two consumers different
        answers to the same question.
        """
        rows = await self._session.execute(
            select(AffiliationModel)
            .where(
                # **Both, always.** RLS is the authoritative control and the
                # explicit predicate is defence in depth (§8).
                AffiliationModel.workspace_id == workspace_id,
                AffiliationModel.company_id == company_id,
            )
            .order_by(AffiliationModel.started_on, AffiliationModel.id)
        )
        return tuple(_to_view(row) for row in rows.scalars())

    async def for_person(
        self, workspace_id: UUID, person_id: UUID
    ) -> tuple[AffiliationView, ...]:
        """Everywhere this person has been recorded, **oldest first.**

        ⚠️ **Today this returns one affiliation in almost every case**, and the
        contract says why: `people` mints a new subject per arrival because it
        holds no identifier to match one against
        ([C-221](../../../../docs/LANE_COORDINATION.md)). **Stated on the port
        so a consumer does not read a single-element result as a data gap.**
        """
        rows = await self._session.execute(
            select(AffiliationModel)
            .where(
                AffiliationModel.workspace_id == workspace_id,
                AffiliationModel.person_id == person_id,
            )
            .order_by(AffiliationModel.started_on, AffiliationModel.id)
        )
        return tuple(_to_view(row) for row in rows.scalars())

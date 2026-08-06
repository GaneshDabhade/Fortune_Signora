"""The ports the People use cases depend on."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from modules.people.domain.affiliation import Affiliation
from modules.people.domain.person import Person


class PeopleRepository(Protocol):
    """Persistence for identities and the intervals attached to them.

    **No `update_person`**, because a person holds nothing to update. The one
    write that changes an existing row is `close_affiliation`, and it moves
    `ended_on` from `NULL` to a date and touches nothing else — which is the
    only in-place change this module makes and is argued in migration 0040.
    """

    async def add_person(self, person: Person, *, actor_id: UUID) -> None: ...

    async def add_affiliation(self, affiliation: Affiliation, *, actor_id: UUID) -> None: ...

    async def open_at_company(
        self, workspace_id: UUID, company_id: UUID
    ) -> tuple[Affiliation, ...]:
        """Every affiliation at this company with no departure observed.

        **The one read the matching rule needs**, and scoped to a company
        because a rule matching on title alone would close the wrong account's
        VP of Engineering.
        """
        ...

    async def close_affiliation(self, affiliation: Affiliation, *, actor_id: UUID) -> None:
        """Record the departure the domain already decided on.

        Takes the **closed** affiliation rather than an id and a date, so the
        domain's refusal to close twice happens before anything reaches the
        database rather than being re-implemented in SQL.
        """
        ...

    async def affiliations_for(
        self, workspace_id: UUID, person_id: UUID
    ) -> tuple[Affiliation, ...]:
        """Everywhere this person has worked, oldest first. **Closed intervals
        included** — the history is the reason the interval model exists."""
        ...

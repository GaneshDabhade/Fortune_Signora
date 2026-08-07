"""How `people`'s infrastructure is constructed.

**Built here rather than at the caller** for the reason
`commercial_profile`'s composition gives: a consumer depends on the
`AffiliationReader` Protocol in `public/`, its composition root calls this, and
**the consumer never learns that any of it is backed by SQL.**
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from modules.people.application.record_role_change import RecordRoleChange
from modules.people.infrastructure.affiliation_reader import SqlAffiliationReader
from modules.people.infrastructure.repository import SqlPeopleRepository


def build_people_repository(session: AsyncSession) -> SqlPeopleRepository:
    return SqlPeopleRepository(session)


def build_record_role_change(session: AsyncSession) -> RecordRoleChange:
    return RecordRoleChange(build_people_repository(session))


def build_affiliation_reader(session: AsyncSession) -> SqlAffiliationReader:
    """The module's published read side, for another module's composition root.

    ⛔ **Returns the reader and never the repository.** `SqlPeopleRepository`
    can write; this cannot, and a consumer that could reach the first would be
    able to author the history it is meant to read.
    """
    return SqlAffiliationReader(session)

"""The published port has an implementation, and it returns closed intervals.

**[C-238](../../../docs/LANE_COORDINATION.md), raised by Lane A and measured
across four refs before it was raised.** `AffiliationReader` was a `Protocol`
that nothing satisfied, so [TASK-458](../../../docs/BACKLOG.md) could consume
the type and its composition root had nothing to pass.

> ⚠️ **The type was verified consumable and not verified injectable**, which is
> one step deeper than [C-237](../../../docs/LANE_COORDINATION.md) and the
> fourth instance of one class in three days.

**So the first test here is the one that was missing**: something satisfies the
port. The rest assert the half that made the port worth shaping this way —
**`at_company` returns closed intervals**, and `SqlPeopleRepository.open_at_company`
does not, which is why the two are different methods rather than one reused.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.people.application.record_role_change import RoleChange
from modules.people.infrastructure.composition import (
    build_affiliation_reader,
    build_record_role_change,
)
from modules.people.public import AffiliationReader, AffiliationView
from modules.workspace_tenancy.application.use_cases import CreateWorkspaceInput
from modules.workspace_tenancy.infrastructure.composition import build_use_cases
from signora_platform.db import tenant_scoped_session, user_scoped_session
from tests.slugs import test_slug as _test_slug

pytestmark = pytest.mark.integration

ARRIVED = date(2026, 3, 1)
LEFT = date(2026, 9, 30)


async def _workspace(factory: async_sessionmaker[AsyncSession]) -> tuple[UUID, UUID]:
    user_id = uuid4()
    async with user_scoped_session(factory, user_id=user_id) as session:
        result = await build_use_cases(session).create_workspace.execute(
            CreateWorkspaceInput(name="People", slug=_test_slug("People"), created_by=user_id), correlation_id=uuid4()
        )
        return result.workspace.id, user_id


def _change(workspace_id: UUID, company_id: UUID, *, title: str, on: date) -> RoleChange:
    return RoleChange(
        workspace_id=workspace_id,
        company_id=company_id,
        title=title,
        seniority="vp",
        occurred_on=on,
    )


class TestThePortIsSatisfied:
    """**The test C-238 asked for, and it needs no database.**"""

    def test_something_in_this_repository_implements_the_reader(self) -> None:
        """⛔ **A `Protocol` nothing satisfies is half a contract.** Asserted
        structurally so it holds whether or not an integration run happens —
        the omission it catches was invisible for a day precisely because
        every check that ran was about the *type*."""
        from modules.people.infrastructure.affiliation_reader import SqlAffiliationReader

        reader: AffiliationReader = SqlAffiliationReader(session=None)  # type: ignore[arg-type]

        assert reader is not None

    def test_the_composition_root_has_something_to_call(self) -> None:
        """**The other half of C-238**: `GenerateSignals` takes the port by
        injection, so a builder has to exist for a composition root to reach."""
        assert callable(build_affiliation_reader)

    def test_the_builder_hands_out_a_reader_and_never_the_repository(self) -> None:
        """⛔ **The repository can write; the reader cannot.** A consumer able
        to reach the first could author the history it is meant to read."""
        from modules.people.infrastructure.affiliation_reader import SqlAffiliationReader

        built = build_affiliation_reader(session=None)  # type: ignore[arg-type]

        assert isinstance(built, SqlAffiliationReader)
        assert not [m for m in dir(built) if m.startswith(("add", "close", "save"))]


class TestAtCompanyReturnsWhatTheSignalNeeds:
    @pytest.mark.asyncio
    async def test_a_departed_holder_is_still_returned(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """⚡ **The load-bearing half, and the reason `open_at_company` could
        not be reused.** *"Who left, and when"* is what
        `decision_maker_departed` exists to answer.
        """
        workspace_id, user_id = await _workspace(admin_session_factory)
        company = uuid4()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            use_case = build_record_role_change(session)
            await use_case.arrived(
                _change(workspace_id, company, title="VP of Engineering", on=ARRIVED),
                actor_id=user_id,
            )
            await use_case.departed(
                _change(workspace_id, company, title="VP of Engineering", on=LEFT),
                actor_id=user_id,
            )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            found = await build_affiliation_reader(session).at_company(workspace_id, company)

        assert len(found) == 1
        assert found[0].ended_on == LEFT
        assert not found[0].is_open

    @pytest.mark.asyncio
    async def test_open_and_closed_come_back_together(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id = await _workspace(admin_session_factory)
        company = uuid4()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            use_case = build_record_role_change(session)
            await use_case.arrived(
                _change(workspace_id, company, title="VP of Engineering", on=ARRIVED),
                actor_id=user_id,
            )
            await use_case.departed(
                _change(workspace_id, company, title="VP of Engineering", on=LEFT),
                actor_id=user_id,
            )
            await use_case.arrived(
                _change(workspace_id, company, title="Head of Data", on=ARRIVED),
                actor_id=user_id,
            )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            found = await build_affiliation_reader(session).at_company(workspace_id, company)

        assert len(found) == 2
        assert {view.is_open for view in found} == {True, False}

    @pytest.mark.asyncio
    async def test_it_publishes_the_view_and_never_the_domain_object(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The mapping is the boundary.** A consumer receiving `Affiliation`
        would inherit this module's constructors and every future refactor of
        them."""
        workspace_id, user_id = await _workspace(admin_session_factory)
        company = uuid4()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            await build_record_role_change(session).arrived(
                _change(workspace_id, company, title="VP of Engineering", on=ARRIVED),
                actor_id=user_id,
            )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            found = await build_affiliation_reader(session).at_company(workspace_id, company)

        assert all(isinstance(view, AffiliationView) for view in found)

    @pytest.mark.asyncio
    async def test_another_company_is_not_this_one(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The same title is held at every company in a workspace — scoping is
        what stops a consumer matching on title alone."""
        workspace_id, user_id = await _workspace(admin_session_factory)
        mine, theirs = uuid4(), uuid4()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            await build_record_role_change(session).arrived(
                _change(workspace_id, theirs, title="VP of Engineering", on=ARRIVED),
                actor_id=user_id,
            )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            assert await build_affiliation_reader(session).at_company(workspace_id, mine) == ()


class TestForPerson:
    @pytest.mark.asyncio
    async def test_it_returns_that_persons_affiliations(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id = await _workspace(admin_session_factory)
        company = uuid4()

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            arrival = await build_record_role_change(session).arrived(
                _change(workspace_id, company, title="VP of Engineering", on=ARRIVED),
                actor_id=user_id,
            )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            found = await build_affiliation_reader(session).for_person(
                workspace_id, arrival.person_id
            )

        assert len(found) == 1
        assert found[0].person_id == arrival.person_id

    @pytest.mark.asyncio
    async def test_an_unknown_person_is_empty_rather_than_an_error(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id = await _workspace(admin_session_factory)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            assert await build_affiliation_reader(session).for_person(workspace_id, uuid4()) == ()


class TestOneWorkspacesPeopleAreNeverAnothers:
    @pytest.mark.asyncio
    async def test_a_company_in_another_workspace_reads_empty(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        mine, my_user = await _workspace(admin_session_factory)
        theirs, their_user = await _workspace(admin_session_factory)
        company = uuid4()

        async with tenant_scoped_session(
            session_factory, workspace_id=mine, user_id=my_user
        ) as session:
            await build_record_role_change(session).arrived(
                _change(mine, company, title="VP of Engineering", on=ARRIVED), actor_id=my_user
            )

        async with tenant_scoped_session(
            session_factory, workspace_id=theirs, user_id=their_user
        ) as session:
            assert await build_affiliation_reader(session).at_company(theirs, company) == ()

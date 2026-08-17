"""Integration tests: workspace_tenancy against a real PostgreSQL 17.

These exercise the full infrastructure stack — SQLAlchemy repositories, the
RLS session-context helpers, and the transactional outbox — as the
least-privilege application role.
"""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.workspace_tenancy.application.use_cases import (
    AddMemberInput,
    CreateWorkspaceInput,
    GetWorkspaceInput,
    ListWorkspaceMembersInput,
)
from modules.workspace_tenancy.domain.entities import WorkspaceRole
from modules.workspace_tenancy.domain.exceptions import DuplicateMembershipError
from modules.workspace_tenancy.infrastructure.composition import build_use_cases
from signora_platform.db import tenant_scoped_session, user_scoped_session
from tests.slugs import test_slug as _test_slug

pytestmark = pytest.mark.integration


async def _create_workspace(
    session_factory: async_sessionmaker[AsyncSession], *, name: str, user_id: UUID
) -> UUID:
    async with user_scoped_session(session_factory, user_id=user_id) as session:
        use_cases = build_use_cases(session)
        result = await use_cases.create_workspace.execute(
            CreateWorkspaceInput(name=name, slug=_test_slug(name), created_by=user_id), correlation_id=uuid4()
        )
        return result.workspace.id


class TestCreateWorkspace:
    async def test_persists_workspace_and_founding_membership(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        user_id = uuid4()

        workspace_id = await _create_workspace(
            session_factory, name="Acme Revenue", user_id=user_id
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            use_cases = build_use_cases(session)
            workspace = await use_cases.get_workspace.execute(
                GetWorkspaceInput(workspace_id=workspace_id)
            )
            members = (
                await use_cases.list_workspace_members.execute(
                    ListWorkspaceMembersInput(workspace_id=workspace_id, limit=50, after=None)
                )
            ).members

        assert workspace.name == "Acme Revenue"
        assert len(members) == 1
        assert members[0].user_id == user_id
        assert members[0].role is WorkspaceRole.OWNER

    async def test_writes_both_events_to_the_outbox(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The outbox is read under the privileged identity, never the
        application's: the application publishes events and is forbidden from
        reading them back (migration 0006). A test that read them as
        ``signora_app`` would be asserting a capability the architecture
        deliberately removed."""
        user_id = uuid4()
        workspace_id = await _create_workspace(session_factory, name="Acme", user_id=user_id)

        async with admin_session_factory() as session:
            rows = (
                await session.execute(
                    text(
                        "SELECT event_type, workspace_id, correlation_id, causation_id, "
                        "producer_module, relayed_at FROM outbox_event ORDER BY event_type"
                    )
                )
            ).all()

        assert [row.event_type for row in rows] == ["workspace.created", "workspace.member_added"]
        assert all(row.workspace_id == workspace_id for row in rows)
        assert all(row.producer_module == "workspace_tenancy" for row in rows)
        # Nothing has been relayed yet — the relay process does not exist.
        assert all(row.relayed_at is None for row in rows)

    async def test_all_events_from_one_operation_share_a_correlation_id(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        await _create_workspace(session_factory, name="Acme", user_id=uuid4())

        async with admin_session_factory() as session:
            correlation_ids = (
                (await session.execute(text("SELECT DISTINCT correlation_id FROM outbox_event")))
                .scalars()
                .all()
            )

        assert len(correlation_ids) == 1

    async def test_member_added_is_caused_by_workspace_created(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        await _create_workspace(session_factory, name="Acme", user_id=uuid4())

        async with admin_session_factory() as session:
            created_id = (
                await session.execute(
                    text("SELECT event_id FROM outbox_event WHERE event_type='workspace.created'")
                )
            ).scalar_one()
            member_causation = (
                await session.execute(
                    text(
                        "SELECT causation_id FROM outbox_event "
                        "WHERE event_type='workspace.member_added'"
                    )
                )
            ).scalar_one()

        assert member_causation == created_id

    async def test_failed_operation_writes_neither_state_nor_events(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """The outbox insert and the domain write share one transaction, so a
        failure after publishing must roll back both — this is the guarantee
        the transactional outbox exists to provide (06-events.md)."""
        user_id = uuid4()
        workspace_id = await _create_workspace(session_factory, name="Acme", user_id=user_id)

        with pytest.raises(DuplicateMembershipError):
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=user_id
            ) as session:
                use_cases = build_use_cases(session)
                # Succeeds and publishes an event...
                await use_cases.add_member.execute(
                    AddMemberInput(
                        workspace_id=workspace_id,
                        user_id=uuid4(),
                        role=WorkspaceRole.MEMBER,
                        added_by=user_id,
                    ),
                    correlation_id=uuid4(),
                )
                # ...then this fails, rolling the whole transaction back.
                await use_cases.add_member.execute(
                    AddMemberInput(
                        workspace_id=workspace_id,
                        user_id=user_id,
                        role=WorkspaceRole.MEMBER,
                        added_by=user_id,
                    ),
                    correlation_id=uuid4(),
                )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            members = (
                await build_use_cases(session).list_workspace_members.execute(
                    ListWorkspaceMembersInput(workspace_id=workspace_id, limit=50, after=None)
                )
            ).members

        async with admin_session_factory() as session:
            outbox_count = (
                await session.execute(text("SELECT count(*) FROM outbox_event"))
            ).scalar_one()

        # Only the founding owner remains; the rolled-back member is absent.
        assert len(members) == 1
        # Only the two events from workspace creation remain.
        assert outbox_count == 2


class TestAddMember:
    async def test_adds_a_second_member(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        owner = uuid4()
        new_member = uuid4()
        workspace_id = await _create_workspace(session_factory, name="Acme", user_id=owner)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=owner
        ) as session:
            await build_use_cases(session).add_member.execute(
                AddMemberInput(
                    workspace_id=workspace_id,
                    user_id=new_member,
                    role=WorkspaceRole.MEMBER,
                    added_by=owner,
                ),
                correlation_id=uuid4(),
            )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=owner
        ) as session:
            members = (
                await build_use_cases(session).list_workspace_members.execute(
                    ListWorkspaceMembersInput(workspace_id=workspace_id, limit=50, after=None)
                )
            ).members

        assert {m.user_id for m in members} == {owner, new_member}

    async def test_database_rejects_duplicate_membership(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Defense in depth: the use case checks for duplicates, and the
        unique constraint enforces it at the database level regardless."""
        owner = uuid4()
        workspace_id = await _create_workspace(session_factory, name="Acme", user_id=owner)

        with pytest.raises(DuplicateMembershipError):
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_id, user_id=owner
            ) as session:
                await build_use_cases(session).add_member.execute(
                    AddMemberInput(
                        workspace_id=workspace_id,
                        user_id=owner,
                        role=WorkspaceRole.MEMBER,
                        added_by=owner,
                    ),
                    correlation_id=uuid4(),
                )

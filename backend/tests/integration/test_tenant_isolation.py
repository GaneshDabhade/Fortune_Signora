"""Integration tests: Row-Level Security tenant isolation.

This is the most security-critical test module in the codebase. It asserts
that workspace data cannot leak across tenant boundaries even when the
application layer asks for it directly — i.e. that isolation is enforced by
PostgreSQL itself, not merely by well-behaved application code
(docs/architecture/11-tenancy.md, docs/architecture/10-security.md).

Every test here runs as ``signora_app``, the non-superuser role without
BYPASSRLS. The session-scoped ``verify_app_role_is_rls_bound`` fixture in
conftest.py fails the suite if that ever stops being true.
"""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.workspace_tenancy.application.use_cases import (
    CreateWorkspaceInput,
    ListWorkspaceMembersInput,
)
from modules.workspace_tenancy.domain.exceptions import WorkspaceNotFoundError
from modules.workspace_tenancy.infrastructure.composition import (
    build_query_service,
    build_use_cases,
)
from signora_platform.db import tenant_scoped_session, user_scoped_session

pytestmark = pytest.mark.integration


async def _create_workspace(
    session_factory: async_sessionmaker[AsyncSession], *, name: str, user_id: UUID
) -> UUID:
    async with user_scoped_session(session_factory, user_id=user_id) as session:
        result = await build_use_cases(session).create_workspace.execute(
            CreateWorkspaceInput(name=name, created_by=user_id), correlation_id=uuid4()
        )
        return result.workspace.id


class TestMembershipIsolation:
    async def test_reading_another_workspace_is_indistinguishable_from_it_not_existing(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Asking, from workspace B's context, for workspace A's members
        must raise "not found" rather than "forbidden" or an empty list.

        Returning a distinct "forbidden" error would let a caller enumerate
        which workspace ids exist; returning an empty list would imply the
        workspace exists but is empty. "Not found" leaks nothing.
        """
        user_a, user_b = uuid4(), uuid4()
        workspace_a = await _create_workspace(session_factory, name="Tenant A", user_id=user_a)
        workspace_b = await _create_workspace(session_factory, name="Tenant B", user_id=user_b)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_b, user_id=user_b
        ) as session:
            with pytest.raises(WorkspaceNotFoundError):
                await build_use_cases(session).list_workspace_members.execute(
                    ListWorkspaceMembersInput(workspace_id=workspace_a)
                )

    async def test_raw_unfiltered_query_still_returns_only_current_workspace(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """The decisive test: a query with no WHERE clause at all must still
        be constrained by RLS. If this fails, application-level filtering is
        the only thing protecting tenants — exactly what RLS exists to
        prevent."""
        user_a, user_b = uuid4(), uuid4()
        workspace_a = await _create_workspace(session_factory, name="Tenant A", user_id=user_a)
        await _create_workspace(session_factory, name="Tenant B", user_id=user_b)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_a, user_id=user_a
        ) as session:
            rows = (
                (await session.execute(text("SELECT workspace_id FROM membership"))).scalars().all()
            )

        assert rows == [workspace_a]

    async def test_membership_cannot_be_inserted_into_another_workspace(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """The RLS policy's WITH CHECK clause must block writes that would
        place a row outside the active workspace context."""
        user_a, user_b = uuid4(), uuid4()
        workspace_a = await _create_workspace(session_factory, name="Tenant A", user_id=user_a)
        workspace_b = await _create_workspace(session_factory, name="Tenant B", user_id=user_b)

        with pytest.raises(Exception) as exc_info:
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_b, user_id=user_b
            ) as session:
                await session.execute(
                    text(
                        "INSERT INTO membership "
                        "(id, workspace_id, user_id, role, created_at, updated_at, "
                        " created_by, updated_by) "
                        "VALUES (:id, :ws, :uid, 'member', now(), now(), :uid, :uid)"
                    ),
                    {"id": uuid4(), "ws": workspace_a, "uid": user_b},
                )

        assert "row-level security" in str(exc_info.value).lower()


class TestWorkspaceVisibility:
    async def test_user_sees_only_workspaces_they_belong_to(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        user_a, user_b = uuid4(), uuid4()
        workspace_a = await _create_workspace(session_factory, name="Tenant A", user_id=user_a)
        await _create_workspace(session_factory, name="Tenant B", user_id=user_b)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_a, user_id=user_a
        ) as session:
            visible = (await session.execute(text("SELECT id FROM workspace"))).scalars().all()

        assert visible == [workspace_a]

    async def test_non_member_cannot_read_a_workspace(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Even with the correct workspace_id in hand, a user with no
        membership must not be able to read the workspace record."""
        owner = uuid4()
        outsider = uuid4()
        workspace_id = await _create_workspace(session_factory, name="Private", user_id=owner)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=outsider
        ) as session:
            query_service = build_query_service(session)
            exists = await query_service.workspace_exists(workspace_id)
            membership = await query_service.get_membership(workspace_id, outsider)

        assert exists is False
        assert membership is None

    async def test_member_can_read_their_own_workspace(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """The positive counterpart to the test above — isolation must not
        be so aggressive that legitimate access breaks."""
        owner = uuid4()
        workspace_id = await _create_workspace(session_factory, name="Mine", user_id=owner)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=owner
        ) as session:
            query_service = build_query_service(session)
            exists = await query_service.workspace_exists(workspace_id)
            membership = await query_service.get_membership(workspace_id, owner)

        assert exists is True
        assert membership is not None
        assert membership.role == "owner"


class TestSessionContextHygiene:
    async def test_workspace_context_does_not_leak_across_pooled_connections(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """``SET LOCAL`` scopes the setting to its transaction. If ``SET``
        were used instead, the pooled connection would carry one tenant's
        context into the next request — the single most dangerous bug this
        architecture can have (11-tenancy.md)."""
        user_a = uuid4()
        workspace_a = await _create_workspace(session_factory, name="Tenant A", user_id=user_a)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_a, user_id=user_a
        ) as session:
            await session.execute(text("SELECT 1"))

        # A fresh session with no context set must see no tenant rows,
        # even though it may reuse the same underlying connection.
        async with session_factory() as session, session.begin():
            leaked = (await session.execute(text("SELECT count(*) FROM membership"))).scalar_one()

        assert leaked == 0

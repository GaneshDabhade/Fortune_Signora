"""Invariants: Casbin decides access, and PostgreSQL — not application code
— enforces workspace isolation.

The layering matters. Casbin answers "may this user do this?"; RLS answers
"which rows exist for this session?". Either alone leaves a hole: a policy
bug without RLS leaks data, and RLS without policy lets any member do
anything. Both are asserted here (docs/architecture/10-security.md,
docs/architecture/11-tenancy.md).
"""

import inspect
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.workspace_tenancy.application.use_cases import CreateWorkspaceInput
from modules.workspace_tenancy.infrastructure.composition import (
    build_query_service,
    build_use_cases,
)
from signora_platform.authorization import (
    Action,
    AuthorizationDeniedError,
    CasbinAuthorizer,
    Resource,
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


class TestCasbinEnforcement:
    """Authorization decisions come from policy, never from a claim in the
    token and never from an ad-hoc check in a handler."""

    @pytest.fixture
    def authorizer(self) -> CasbinAuthorizer:
        return CasbinAuthorizer()

    def test_an_owner_may_mutate(self, authorizer: CasbinAuthorizer) -> None:
        assert authorizer.is_allowed(
            role="owner", workspace_id=uuid4(), resource=Resource.WORKSPACE, action=Action.UPDATE
        )

    def test_a_member_may_read_but_not_mutate(self, authorizer: CasbinAuthorizer) -> None:
        workspace_id = uuid4()

        assert authorizer.is_allowed(
            role="member",
            workspace_id=workspace_id,
            resource=Resource.WORKSPACE,
            action=Action.READ,
        )
        assert not authorizer.is_allowed(
            role="member",
            workspace_id=workspace_id,
            resource=Resource.WORKSPACE,
            action=Action.UPDATE,
        )

    def test_an_unrecognised_role_is_denied_everything(self, authorizer: CasbinAuthorizer) -> None:
        """Policy must fail closed. A role added to the domain model but not
        to the policy gets nothing, rather than inheriting a permissive
        default."""
        for resource in Resource:
            for action in Action:
                assert not authorizer.is_allowed(
                    role="not_a_real_role",
                    workspace_id=uuid4(),
                    resource=resource,
                    action=action,
                ), f"unknown role was permitted to {action} {resource}"

    def test_every_decision_is_scoped_to_a_workspace(self, authorizer: CasbinAuthorizer) -> None:
        """``workspace_id`` is a required keyword argument, so no call site
        can accidentally ask a global question. A permission granted in one
        workspace must never be a permission everywhere."""
        parameter = inspect.signature(authorizer.is_allowed).parameters.get("workspace_id")

        assert parameter is not None
        assert parameter.default is inspect.Parameter.empty

    def test_denial_is_expressed_as_a_domain_error_carrying_context(self) -> None:
        """The error must name role, resource, and action: an authorization
        failure with no context is close to undebuggable in production, and
        the alternative is logging the whole request."""
        error = AuthorizationDeniedError(
            role="member", resource=Resource.WORKSPACE, action=Action.UPDATE
        )

        assert error.role == "member"
        assert error.resource is Resource.WORKSPACE
        assert error.action is Action.UPDATE


class TestWorkspaceIsolation:
    async def test_a_non_member_cannot_observe_that_a_workspace_exists(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Not-found rather than forbidden. A distinct "forbidden" response
        confirms the id is real, which is enough to enumerate customers."""
        owner, outsider = uuid4(), uuid4()
        workspace_id = await _create_workspace(session_factory, name="Private", user_id=owner)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=outsider
        ) as session:
            query_service = build_query_service(session)

            assert await query_service.workspace_exists(workspace_id) is False
            assert await query_service.get_membership(workspace_id, outsider) is None

    async def test_a_member_can_reach_their_own_workspace(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """The positive control: isolation that also blocks legitimate access
        would satisfy every negative test in this file."""
        owner = uuid4()
        workspace_id = await _create_workspace(session_factory, name="Mine", user_id=owner)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=owner
        ) as session:
            assert await build_query_service(session).workspace_exists(workspace_id) is True


class TestRowLevelSecurity:
    async def test_a_query_with_no_where_clause_still_returns_one_workspace(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """The decisive invariant. If this fails, application-level filtering
        is the only thing separating tenants, and a single forgotten WHERE
        becomes a data breach."""
        user_a, user_b = uuid4(), uuid4()
        workspace_a = await _create_workspace(session_factory, name="A", user_id=user_a)
        await _create_workspace(session_factory, name="B", user_id=user_b)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_a, user_id=user_a
        ) as session:
            rows = (
                (await session.execute(text("SELECT workspace_id FROM membership"))).scalars().all()
            )

        assert rows == [workspace_a]

    async def test_a_write_outside_the_active_workspace_is_blocked(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Read isolation without write isolation would let one tenant insert
        rows into another's data."""
        user_a, user_b = uuid4(), uuid4()
        workspace_a = await _create_workspace(session_factory, name="A", user_id=user_a)
        workspace_b = await _create_workspace(session_factory, name="B", user_id=user_b)

        with pytest.raises(Exception) as exc_info:
            async with tenant_scoped_session(
                session_factory, workspace_id=workspace_b, user_id=user_b
            ) as session:
                await session.execute(
                    text(
                        "INSERT INTO membership (id, workspace_id, user_id, role, created_at, "
                        "updated_at, created_by, updated_by) "
                        "VALUES (:id, :ws, :uid, 'member', now(), now(), :uid, :uid)"
                    ),
                    {"id": uuid4(), "ws": workspace_a, "uid": user_b},
                )

        assert "row-level security" in str(exc_info.value).lower()

    async def test_a_session_with_no_workspace_context_sees_nothing(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Fail closed. Missing context must yield no rows rather than all
        rows — and because context is set with ``SET LOCAL``, it cannot leak
        from the previous transaction on a pooled connection."""
        user_a = uuid4()
        await _create_workspace(session_factory, name="A", user_id=user_a)

        async with session_factory() as session, session.begin():
            visible = (await session.execute(text("SELECT count(*) FROM membership"))).scalar_one()

        assert visible == 0

    async def test_every_workspace_owned_table_has_rls_enabled_and_forced(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Catches the realistic future regression: a module adds a table
        with a ``workspace_id`` column and forgets its policy. Nothing else
        in the suite would notice until that module's data leaked.

        ``FORCE`` matters separately from ``ENABLE``: without it, the table's
        owner is exempt from its own policies.
        """
        async with admin_session_factory() as session, session.begin():
            rows = (
                await session.execute(
                    text(
                        """
                        SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity
                        FROM pg_class c
                        JOIN pg_namespace n ON n.oid = c.relnamespace
                        JOIN information_schema.columns col
                          ON col.table_schema = n.nspname
                         AND col.table_name = c.relname
                         AND col.column_name = 'workspace_id'
                        WHERE n.nspname = 'public' AND c.relkind = 'r'
                        ORDER BY c.relname
                        """
                    )
                )
            ).all()

        unprotected = [name for name, enabled, forced in rows if not (enabled and forced)]

        assert unprotected == PLATFORM_TABLES_WITHOUT_RLS, (
            f"table(s) with workspace_id but no forced RLS: {unprotected}. "
            "Add the policy in the same migration that creates the table "
            "(docs/architecture/11-tenancy.md), or extend the documented "
            "exception list if this is deliberate."
        )


# The outbox relay and dead-letter handling must sweep every workspace's
# rows in one pass, which tenant-scoped RLS would prevent by construction.
# These are platform-owned tables, not module-owned data
# (docs/architecture/11-tenancy.md, "Platform Tables Are Not Workspace-Owned").
#
# The exception is narrow and deliberately spelled out here rather than
# inferred: any *other* table reaching this list is a bug, and the test above
# fails until it is either given a policy or added with a stated reason.
PLATFORM_TABLES_WITHOUT_RLS = ["dead_letter_event", "outbox_event"]

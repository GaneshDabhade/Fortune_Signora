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

    def test_a_member_may_work_accounts_and_still_not_run_the_workspace(
        self, authorizer: CasbinAuthorizer
    ) -> None:
        """**The grant M12.3 added, and its boundary.**

        A member *is* the seller — an SDR who could not take an account on or
        dismiss one would find the product unusable, so `opportunity:update`
        is theirs by design. It buys nothing else: they still cannot rename
        the workspace or add a colleague, which are the two ways a workflow
        permission would otherwise become an administrative one.

        Stated here rather than only in the opportunity tests because a
        rewrite of that feature must not be able to take the boundary with
        it.
        """
        workspace_id = uuid4()

        assert authorizer.is_allowed(
            role="member",
            workspace_id=workspace_id,
            resource=Resource.OPPORTUNITY,
            action=Action.UPDATE,
        )
        for resource, action in (
            (Resource.WORKSPACE, Action.UPDATE),
            (Resource.MEMBER, Action.ADD),
            (Resource.MEMBER, Action.REMOVE),
        ):
            assert not authorizer.is_allowed(
                role="member", workspace_id=workspace_id, resource=resource, action=action
            ), f"a member was permitted to {action} {resource}"

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

    # The structural "does every tenant table have forced RLS" check moved
    # to test_tenancy_policy.py, where it is one clause of the full Tenant
    # Isolation Policy rather than a lone assertion. This file keeps the
    # behavioural proof that isolation actually holds; that file proves the
    # configuration is present on every table it should be.

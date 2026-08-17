"""Unit tests for the read-side use cases."""

from uuid import uuid4

import pytest

from modules.workspace_tenancy.application.use_cases import (
    GetWorkspaceInput,
    GetWorkspaceUseCase,
    ListWorkspaceMembersInput,
    ListWorkspaceMembersUseCase,
)
from modules.workspace_tenancy.domain.entities import Membership, Workspace, WorkspaceRole
from modules.workspace_tenancy.domain.exceptions import WorkspaceNotFoundError
from modules.workspace_tenancy.tests.fakes import FakeMembershipRepository, FakeWorkspaceRepository


@pytest.fixture
def workspaces() -> FakeWorkspaceRepository:
    return FakeWorkspaceRepository()


@pytest.fixture
def memberships() -> FakeMembershipRepository:
    return FakeMembershipRepository()


class TestGetWorkspace:
    async def test_returns_existing_workspace(self, workspaces: FakeWorkspaceRepository) -> None:
        workspace, _ = Workspace.create(name="Acme", slug="a-workspace", created_by=uuid4())
        await workspaces.add(workspace)
        use_case = GetWorkspaceUseCase(workspace_repository=workspaces)

        result = await use_case.execute(GetWorkspaceInput(workspace_id=workspace.id))

        assert result.id == workspace.id
        assert result.name == "Acme"

    async def test_raises_for_unknown_workspace(self, workspaces: FakeWorkspaceRepository) -> None:
        use_case = GetWorkspaceUseCase(workspace_repository=workspaces)

        with pytest.raises(WorkspaceNotFoundError):
            await use_case.execute(GetWorkspaceInput(workspace_id=uuid4()))


class TestListWorkspaceMembers:
    async def test_lists_only_members_of_the_requested_workspace(
        self, workspaces: FakeWorkspaceRepository, memberships: FakeMembershipRepository
    ) -> None:
        target, _ = Workspace.create(name="Target", slug="a-workspace", created_by=uuid4())
        other, _ = Workspace.create(name="Other", slug="a-workspace", created_by=uuid4())
        await workspaces.add(target)
        await workspaces.add(other)

        for workspace in (target, target, other):
            membership, _ = Membership.create(
                workspace_id=workspace.id,
                user_id=uuid4(),
                role=WorkspaceRole.MEMBER,
                created_by=uuid4(),
            )
            await memberships.add(membership)

        use_case = ListWorkspaceMembersUseCase(
            workspace_repository=workspaces, membership_repository=memberships
        )

        result = await use_case.execute(
            ListWorkspaceMembersInput(workspace_id=target.id, limit=50, after=None)
        )

        assert len(result.members) == 2
        assert all(m.workspace_id == target.id for m in result.members)
        assert result.has_more is False

    async def test_returns_empty_list_for_workspace_without_members(
        self, workspaces: FakeWorkspaceRepository, memberships: FakeMembershipRepository
    ) -> None:
        workspace, _ = Workspace.create(name="Empty", slug="a-workspace", created_by=uuid4())
        await workspaces.add(workspace)
        use_case = ListWorkspaceMembersUseCase(
            workspace_repository=workspaces, membership_repository=memberships
        )

        result = await use_case.execute(
            ListWorkspaceMembersInput(workspace_id=workspace.id, limit=50, after=None)
        )

        assert result.members == []
        assert result.has_more is False

    async def test_raises_for_unknown_workspace(
        self, workspaces: FakeWorkspaceRepository, memberships: FakeMembershipRepository
    ) -> None:
        use_case = ListWorkspaceMembersUseCase(
            workspace_repository=workspaces, membership_repository=memberships
        )

        with pytest.raises(WorkspaceNotFoundError):
            await use_case.execute(
                ListWorkspaceMembersInput(workspace_id=uuid4(), limit=50, after=None)
            )

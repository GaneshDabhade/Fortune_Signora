"""Unit tests for AddMemberUseCase."""

from uuid import uuid4

import pytest

from modules.workspace_tenancy.application.use_cases import AddMemberInput, AddMemberUseCase
from modules.workspace_tenancy.domain.entities import Workspace, WorkspaceRole
from modules.workspace_tenancy.domain.exceptions import (
    DuplicateMembershipError,
    WorkspaceNotFoundError,
)
from modules.workspace_tenancy.tests.fakes import (
    FakeEventPublisher,
    FakeMembershipRepository,
    FakeWorkspaceRepository,
)


@pytest.fixture
def workspaces() -> FakeWorkspaceRepository:
    return FakeWorkspaceRepository()


@pytest.fixture
def memberships() -> FakeMembershipRepository:
    return FakeMembershipRepository()


@pytest.fixture
def publisher() -> FakeEventPublisher:
    return FakeEventPublisher()


@pytest.fixture
def use_case(
    workspaces: FakeWorkspaceRepository,
    memberships: FakeMembershipRepository,
    publisher: FakeEventPublisher,
) -> AddMemberUseCase:
    return AddMemberUseCase(
        workspace_repository=workspaces,
        membership_repository=memberships,
        event_publisher=publisher,
    )


@pytest.fixture
async def existing_workspace(workspaces: FakeWorkspaceRepository) -> Workspace:
    workspace, _ = Workspace.create(name="Acme", created_by=uuid4())
    await workspaces.add(workspace)
    return workspace


async def test_adds_member_to_existing_workspace(
    use_case: AddMemberUseCase,
    existing_workspace: Workspace,
    memberships: FakeMembershipRepository,
) -> None:
    new_user = uuid4()

    membership = await use_case.execute(
        AddMemberInput(
            workspace_id=existing_workspace.id,
            user_id=new_user,
            role=WorkspaceRole.MEMBER,
            added_by=uuid4(),
        ),
        correlation_id=uuid4(),
    )

    assert membership.user_id == new_user
    assert membership.role is WorkspaceRole.MEMBER
    assert len(memberships.memberships) == 1


async def test_publishes_member_added_event(
    use_case: AddMemberUseCase, existing_workspace: Workspace, publisher: FakeEventPublisher
) -> None:
    await use_case.execute(
        AddMemberInput(
            workspace_id=existing_workspace.id,
            user_id=uuid4(),
            role=WorkspaceRole.MEMBER,
            added_by=uuid4(),
        ),
        correlation_id=uuid4(),
    )

    assert [event.event_type for event in publisher.published] == ["workspace.member_added"]


async def test_rejects_unknown_workspace(
    use_case: AddMemberUseCase, publisher: FakeEventPublisher
) -> None:
    unknown_workspace = uuid4()

    with pytest.raises(WorkspaceNotFoundError):
        await use_case.execute(
            AddMemberInput(
                workspace_id=unknown_workspace,
                user_id=uuid4(),
                role=WorkspaceRole.MEMBER,
                added_by=uuid4(),
            ),
            correlation_id=uuid4(),
        )

    assert publisher.published == []


async def test_rejects_duplicate_membership(
    use_case: AddMemberUseCase,
    existing_workspace: Workspace,
    publisher: FakeEventPublisher,
    memberships: FakeMembershipRepository,
) -> None:
    user_id = uuid4()
    input_ = AddMemberInput(
        workspace_id=existing_workspace.id,
        user_id=user_id,
        role=WorkspaceRole.MEMBER,
        added_by=uuid4(),
    )
    await use_case.execute(input_, correlation_id=uuid4())

    with pytest.raises(DuplicateMembershipError):
        await use_case.execute(input_, correlation_id=uuid4())

    assert len(memberships.memberships) == 1
    assert len(publisher.published) == 1


async def test_same_user_may_belong_to_multiple_workspaces(
    use_case: AddMemberUseCase,
    workspaces: FakeWorkspaceRepository,
    memberships: FakeMembershipRepository,
) -> None:
    """Duplicate detection is scoped per workspace, not global — a user
    legitimately belongs to many workspaces."""
    user_id = uuid4()
    first, _ = Workspace.create(name="First", created_by=uuid4())
    second, _ = Workspace.create(name="Second", created_by=uuid4())
    await workspaces.add(first)
    await workspaces.add(second)

    for workspace in (first, second):
        await use_case.execute(
            AddMemberInput(
                workspace_id=workspace.id,
                user_id=user_id,
                role=WorkspaceRole.MEMBER,
                added_by=uuid4(),
            ),
            correlation_id=uuid4(),
        )

    for workspace in (first, second):
        members = await memberships.list_page_for_workspace(workspace.id, limit=10, after=None)
        assert [m.user_id for m in members] == [user_id]

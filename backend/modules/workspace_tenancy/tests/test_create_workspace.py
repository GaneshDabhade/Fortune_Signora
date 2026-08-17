"""Unit tests for CreateWorkspaceUseCase."""

from uuid import uuid4

import pytest

from modules.workspace_tenancy.application.use_cases import (
    CreateWorkspaceInput,
    CreateWorkspaceUseCase,
)
from modules.workspace_tenancy.domain.entities import WorkspaceRole
from modules.workspace_tenancy.domain.exceptions import InvalidWorkspaceNameError
from modules.workspace_tenancy.tests.fakes import (
    FakeEventPublisher,
    FakeMembershipRepository,
    FakeTenantContext,
    FakeWorkspaceRepository,
)


@pytest.fixture
def workspaces() -> FakeWorkspaceRepository:
    return FakeWorkspaceRepository()


@pytest.fixture
def memberships() -> FakeMembershipRepository:
    return FakeMembershipRepository()


@pytest.fixture
def tenant_context() -> FakeTenantContext:
    return FakeTenantContext()


@pytest.fixture
def publisher() -> FakeEventPublisher:
    return FakeEventPublisher()


@pytest.fixture
def use_case(
    workspaces: FakeWorkspaceRepository,
    memberships: FakeMembershipRepository,
    tenant_context: FakeTenantContext,
    publisher: FakeEventPublisher,
) -> CreateWorkspaceUseCase:
    return CreateWorkspaceUseCase(
        workspace_repository=workspaces,
        membership_repository=memberships,
        tenant_context=tenant_context,
        event_publisher=publisher,
    )


async def test_persists_workspace_and_founding_membership(
    use_case: CreateWorkspaceUseCase,
    workspaces: FakeWorkspaceRepository,
    memberships: FakeMembershipRepository,
) -> None:
    creator = uuid4()

    result = await use_case.execute(
        CreateWorkspaceInput(name="Acme Revenue", slug="acme-revenue", created_by=creator),
        correlation_id=uuid4(),
    )

    assert workspaces.workspaces[result.workspace.id].name == "Acme Revenue"
    assert len(memberships.memberships) == 1
    assert memberships.memberships[0].workspace_id == result.workspace.id


async def test_creator_becomes_workspace_owner(use_case: CreateWorkspaceUseCase) -> None:
    creator = uuid4()

    result = await use_case.execute(
        CreateWorkspaceInput(name="Acme", slug="acme-revenue", created_by=creator), correlation_id=uuid4()
    )

    assert result.founding_membership.user_id == creator
    assert result.founding_membership.role is WorkspaceRole.OWNER


async def test_activates_rls_workspace_context_before_inserting_membership(
    use_case: CreateWorkspaceUseCase, tenant_context: FakeTenantContext
) -> None:
    """The membership insert must run under the new workspace's RLS context —
    see the workspace-creation bootstrap pattern in
    docs/architecture/11-tenancy.md."""
    result = await use_case.execute(
        CreateWorkspaceInput(name="Acme", slug="acme-revenue", created_by=uuid4()), correlation_id=uuid4()
    )

    assert tenant_context.activated == [result.workspace.id]


async def test_publishes_both_events_in_causal_order(
    use_case: CreateWorkspaceUseCase, publisher: FakeEventPublisher
) -> None:
    await use_case.execute(
        CreateWorkspaceInput(name="Acme", slug="acme-revenue", created_by=uuid4()), correlation_id=uuid4()
    )

    assert [event.event_type for event in publisher.published] == [
        "workspace.created",
        "workspace.member_added",
    ]


async def test_member_added_event_is_caused_by_workspace_created_event(
    use_case: CreateWorkspaceUseCase, publisher: FakeEventPublisher
) -> None:
    await use_case.execute(
        CreateWorkspaceInput(name="Acme", slug="acme-revenue", created_by=uuid4()), correlation_id=uuid4()
    )

    workspace_created, member_added = publisher.published
    assert member_added.causation_id == workspace_created.event_id


async def test_propagates_supplied_correlation_id(
    use_case: CreateWorkspaceUseCase, publisher: FakeEventPublisher
) -> None:
    correlation_id = uuid4()

    await use_case.execute(
        CreateWorkspaceInput(name="Acme", slug="acme-revenue", created_by=uuid4()), correlation_id=correlation_id
    )

    assert publisher.correlation_ids == [correlation_id]


async def test_invalid_name_publishes_nothing_and_persists_nothing(
    use_case: CreateWorkspaceUseCase,
    workspaces: FakeWorkspaceRepository,
    memberships: FakeMembershipRepository,
    publisher: FakeEventPublisher,
) -> None:
    with pytest.raises(InvalidWorkspaceNameError):
        await use_case.execute(
            CreateWorkspaceInput(name="   ", slug="acme-revenue", created_by=uuid4()), correlation_id=uuid4()
        )

    assert workspaces.workspaces == {}
    assert memberships.memberships == []
    assert publisher.published == []

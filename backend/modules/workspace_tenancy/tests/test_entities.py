"""Unit tests for the Workspace & Tenancy domain layer."""

from uuid import uuid4

import pytest

from modules.workspace_tenancy.domain.entities import (
    MAX_WORKSPACE_NAME_LENGTH,
    Membership,
    Workspace,
    WorkspaceRole,
)
from modules.workspace_tenancy.domain.exceptions import InvalidWorkspaceNameError


class TestWorkspaceCreate:
    def test_creates_workspace_with_normalized_name(self) -> None:
        user_id = uuid4()

        workspace, event = Workspace.create(name="  Acme Revenue  ", created_by=user_id)

        assert workspace.name == "Acme Revenue"
        assert workspace.created_by == user_id
        assert workspace.updated_by == user_id
        assert event.event_type == "workspace.created"
        assert event.workspace_id == workspace.id
        assert event.name == "Acme Revenue"

    def test_created_and_updated_timestamps_are_identical_on_creation(self) -> None:
        workspace, _ = Workspace.create(name="Acme", created_by=uuid4())

        assert workspace.created_at == workspace.updated_at

    def test_event_payload_serializes_uuids_as_strings(self) -> None:
        user_id = uuid4()

        workspace, event = Workspace.create(name="Acme", created_by=user_id)
        payload = event.to_payload()

        assert payload == {
            "workspace_id": str(workspace.id),
            "name": "Acme",
            "created_by": str(user_id),
        }

    @pytest.mark.parametrize("invalid_name", ["", "   ", "\t\n"])
    def test_rejects_blank_names(self, invalid_name: str) -> None:
        with pytest.raises(InvalidWorkspaceNameError):
            Workspace.create(name=invalid_name, created_by=uuid4())

    def test_rejects_names_over_max_length(self) -> None:
        too_long = "a" * (MAX_WORKSPACE_NAME_LENGTH + 1)

        with pytest.raises(InvalidWorkspaceNameError):
            Workspace.create(name=too_long, created_by=uuid4())

    def test_accepts_name_at_exactly_max_length(self) -> None:
        at_limit = "a" * MAX_WORKSPACE_NAME_LENGTH

        workspace, _ = Workspace.create(name=at_limit, created_by=uuid4())

        assert workspace.name == at_limit

    def test_name_is_validated_after_trimming_not_before(self) -> None:
        """A name that only exceeds the limit because of surrounding
        whitespace is valid — trimming happens first."""
        padded = "  " + "a" * MAX_WORKSPACE_NAME_LENGTH + "  "

        workspace, _ = Workspace.create(name=padded, created_by=uuid4())

        assert len(workspace.name) == MAX_WORKSPACE_NAME_LENGTH

    def test_each_workspace_gets_a_unique_id(self) -> None:
        first, _ = Workspace.create(name="Acme", created_by=uuid4())
        second, _ = Workspace.create(name="Acme", created_by=uuid4())

        assert first.id != second.id


class TestMembershipCreate:
    def test_creates_membership_with_role(self) -> None:
        workspace_id, user_id, actor_id = uuid4(), uuid4(), uuid4()

        membership, event = Membership.create(
            workspace_id=workspace_id,
            user_id=user_id,
            role=WorkspaceRole.MEMBER,
            created_by=actor_id,
        )

        assert membership.workspace_id == workspace_id
        assert membership.user_id == user_id
        assert membership.role is WorkspaceRole.MEMBER
        assert membership.created_by == actor_id
        assert event.event_type == "workspace.member_added"
        assert event.role == "member"

    def test_records_causation_id_when_provided(self) -> None:
        causing_event_id = uuid4()

        _, event = Membership.create(
            workspace_id=uuid4(),
            user_id=uuid4(),
            role=WorkspaceRole.OWNER,
            created_by=uuid4(),
            causation_id=causing_event_id,
        )

        assert event.causation_id == causing_event_id

    def test_causation_id_defaults_to_none(self) -> None:
        _, event = Membership.create(
            workspace_id=uuid4(),
            user_id=uuid4(),
            role=WorkspaceRole.OWNER,
            created_by=uuid4(),
        )

        assert event.causation_id is None

    def test_role_serializes_to_its_string_value_in_payload(self) -> None:
        _, event = Membership.create(
            workspace_id=uuid4(),
            user_id=uuid4(),
            role=WorkspaceRole.OWNER,
            created_by=uuid4(),
        )

        assert event.to_payload()["role"] == "owner"

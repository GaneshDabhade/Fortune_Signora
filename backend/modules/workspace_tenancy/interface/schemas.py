"""HTTP request/response schemas for Workspace & Tenancy.

Deliberately separate from the domain entities in ``domain/entities.py``,
even where currently field-identical. Coupling the wire contract to the
domain model means a domain refactor becomes a client-breaking change
(19-api-conventions.md).
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from modules.workspace_tenancy.domain.entities import (
    MAX_WORKSPACE_NAME_LENGTH,
    Membership,
    Workspace,
    WorkspaceRole,
)
from modules.workspace_tenancy.domain.invitation import Invitation, InvitationState


class CreateWorkspaceRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1, max_length=MAX_WORKSPACE_NAME_LENGTH)


class AddMemberRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: UUID
    role: WorkspaceRole


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, workspace: Workspace) -> "WorkspaceResponse":
        return cls(
            id=workspace.id,
            name=workspace.name,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
        )


class MembershipResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    workspace_id: UUID
    user_id: UUID
    role: WorkspaceRole
    created_at: datetime

    @classmethod
    def from_domain(cls, membership: Membership) -> "MembershipResponse":
        return cls(
            id=membership.id,
            workspace_id=membership.workspace_id,
            user_id=membership.user_id,
            role=membership.role,
            created_at=membership.created_at,
        )


class InviteMemberRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    #: As the customer typed it. Normalized by the domain — the one place an
    #: address is put into the form the unique index and acceptance compare.
    email: str
    role: WorkspaceRole


class InvitationResponse(BaseModel):
    """An offer, as an administrator reads it.

    **`state` is computed and sent, not stored.** The browser must not derive it
    from `expires_at`, because two clocks would disagree and the one that
    matters is the server's — the same reason `evidence_state` travels on the
    wire rather than being recomputed on the client.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID
    workspace_id: UUID
    invited_email: str
    role: WorkspaceRole
    state: InvitationState
    expires_at: datetime
    created_at: datetime
    #: Who offered it. An identifier rather than a name, for the reason the
    #: members list has the same shape (C-203) — and it never changes, because
    #: the inviter is provenance rather than an owner.
    invited_by: UUID

    @classmethod
    def from_domain(cls, invitation: Invitation, *, at: datetime) -> "InvitationResponse":
        return cls(
            id=invitation.id,
            workspace_id=invitation.workspace_id,
            invited_email=invitation.invited_email,
            role=invitation.role,
            state=invitation.state(at=at),
            expires_at=invitation.expires_at,
            created_at=invitation.created_at,
            invited_by=invitation.invited_by,
        )

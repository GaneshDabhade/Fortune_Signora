"""This module's published event payload contracts, per
docs/architecture/06-events.md. Other modules that consume ``workspace.*``
events depend on these Pydantic models, never on this module's internal
domain event dataclasses.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class WorkspaceCreatedPayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    workspace_id: UUID
    name: str
    created_by: UUID


class MemberAddedPayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    workspace_id: UUID
    user_id: UUID
    role: str

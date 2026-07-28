"""The one approved synchronous, read-only query interface other modules
may depend on directly, per docs/architecture/05-module-dependencies.md
("Any module -> Workspace & Tenancy: resolve/validate workspace context,
read-only"). Every other cross-module interaction goes through published
events, never this port.
"""

from typing import Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MembershipView(BaseModel):
    model_config = ConfigDict(frozen=True)

    workspace_id: UUID
    user_id: UUID
    role: str


class WorkspaceQueryPort(Protocol):
    async def workspace_exists(self, workspace_id: UUID) -> bool: ...
    async def get_membership(self, workspace_id: UUID, user_id: UUID) -> MembershipView | None: ...

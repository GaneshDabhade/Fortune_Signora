"""Application-layer ports (Python Protocols) that this module's use cases
depend on. Infrastructure implements these; domain and application code
never import SQLAlchemy, FastAPI, or any other infrastructure type directly
— that is what keeps this module's business logic testable with fakes and
free of framework coupling (docs/architecture/15-project-structure.md).
"""

from collections.abc import Sequence
from typing import Any, Protocol
from uuid import UUID

from modules.workspace_tenancy.domain.entities import Membership, Workspace


class WorkspaceRepository(Protocol):
    async def add(self, workspace: Workspace) -> None: ...
    async def get(self, workspace_id: UUID) -> Workspace | None: ...


class MembershipRepository(Protocol):
    async def add(self, membership: Membership) -> None: ...
    async def get(self, workspace_id: UUID, user_id: UUID) -> Membership | None: ...
    async def list_for_workspace(self, workspace_id: UUID) -> list[Membership]: ...
    async def list_for_user(self, user_id: UUID) -> list[Membership]: ...


class TenantContext(Protocol):
    """Activates RLS workspace scope mid-transaction. Abstracts over the
    concrete ``SET LOCAL``/``set_config`` mechanism in ``signora_platform/db`` so
    the application layer never imports SQLAlchemy directly. Needed because
    workspace creation runs before a workspace_id exists to scope to — see
    the bootstrap pattern in docs/architecture/11-tenancy.md.
    """

    async def activate_workspace(self, workspace_id: UUID) -> None: ...


class EventPublisher(Protocol):
    """Module-local publishing port. The session and producer-module name
    are bound into the infrastructure adapter at construction time, so use
    cases only ever deal in domain events and a correlation id — never a
    database session.
    """

    async def publish(self, events: Sequence[Any], *, correlation_id: UUID) -> None: ...

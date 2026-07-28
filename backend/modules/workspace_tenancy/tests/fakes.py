"""In-memory fakes implementing this module's application-layer ports.

Used by unit tests so domain and application logic is exercised without a
database — if a unit test ever needs a real database, that is a signal the
Clean Architecture boundary has leaked (CLAUDE.md §11).
"""

from collections.abc import Sequence
from typing import Any
from uuid import UUID

from modules.workspace_tenancy.domain.entities import Membership, Workspace
from signora_platform.pagination import CursorPosition


class FakeWorkspaceRepository:
    def __init__(self) -> None:
        self.workspaces: dict[UUID, Workspace] = {}

    async def add(self, workspace: Workspace) -> None:
        self.workspaces[workspace.id] = workspace

    async def get(self, workspace_id: UUID) -> Workspace | None:
        return self.workspaces.get(workspace_id)

    async def list_visible(self, *, limit: int, after: CursorPosition | None) -> list[Workspace]:
        """Mirrors the newest-first keyset ordering the real repository gets
        from SQL, so pagination behaviour is exercised without a database."""
        ordered = sorted(self.workspaces.values(), key=lambda w: (w.created_at, w.id), reverse=True)
        if after is not None:
            ordered = [w for w in ordered if (w.created_at, w.id) < (after.created_at, after.id)]
        return ordered[:limit]


class FakeMembershipRepository:
    def __init__(self) -> None:
        self.memberships: list[Membership] = []

    async def add(self, membership: Membership) -> None:
        self.memberships.append(membership)

    async def get(self, workspace_id: UUID, user_id: UUID) -> Membership | None:
        return next(
            (
                m
                for m in self.memberships
                if m.workspace_id == workspace_id and m.user_id == user_id
            ),
            None,
        )

    async def list_for_workspace(self, workspace_id: UUID) -> list[Membership]:
        return [m for m in self.memberships if m.workspace_id == workspace_id]

    async def list_for_user(self, user_id: UUID) -> list[Membership]:
        return [m for m in self.memberships if m.user_id == user_id]

    async def list_page_for_workspace(
        self, workspace_id: UUID, *, limit: int, after: CursorPosition | None
    ) -> list[Membership]:
        ordered = sorted(
            (m for m in self.memberships if m.workspace_id == workspace_id),
            key=lambda m: (m.created_at, m.id),
            reverse=True,
        )
        if after is not None:
            ordered = [m for m in ordered if (m.created_at, m.id) < (after.created_at, after.id)]
        return ordered[:limit]


class FakeTenantContext:
    """Records workspace activations so tests can assert RLS context was
    established at the right point in a use case's flow."""

    def __init__(self) -> None:
        self.activated: list[UUID] = []

    async def activate_workspace(self, workspace_id: UUID) -> None:
        self.activated.append(workspace_id)


class FakeEventPublisher:
    def __init__(self) -> None:
        self.published: list[Any] = []
        self.correlation_ids: list[UUID] = []

    async def publish(self, events: Sequence[Any], *, correlation_id: UUID) -> None:
        self.published.extend(events)
        self.correlation_ids.append(correlation_id)

"""SQLAlchemy implementations of this module's repository ports.

Each repository is constructed with the request/job-scoped ``AsyncSession``
(bound by the composition root — see ``composition.py``) and maps explicitly
between domain entities and ORM models in both directions.
"""

from uuid import UUID

from sqlalchemy import Select, literal, select, tuple_

from modules.workspace_tenancy.domain.entities import Membership, Workspace
from modules.workspace_tenancy.infrastructure.models import MembershipModel, WorkspaceModel
from signora_platform.db import SqlAlchemyRepository
from signora_platform.pagination import CursorPosition


def _workspace_to_domain(model: WorkspaceModel) -> Workspace:
    return Workspace(
        id=model.id,
        name=model.name,
        created_at=model.created_at,
        updated_at=model.updated_at,
        created_by=model.created_by,
        updated_by=model.updated_by,
    )


def _membership_to_domain(model: MembershipModel) -> Membership:
    return Membership(
        id=model.id,
        workspace_id=model.workspace_id,
        user_id=model.user_id,
        role=model.role,
        created_at=model.created_at,
        updated_at=model.updated_at,
        created_by=model.created_by,
        updated_by=model.updated_by,
    )


def _apply_keyset[M: MembershipModel | WorkspaceModel](
    statement: Select[tuple[M]],
    model: type[M],
    after: CursorPosition | None,
) -> Select[tuple[M]]:
    """Apply newest-first keyset ordering and a strict "after" bound.

    The bound is a SQL row-value comparison — ``(created_at, id) < (…)`` —
    rather than two chained column comparisons. That is what makes the page
    boundary exact when rows share a timestamp: comparing on ``created_at``
    alone would drop or repeat rows at the seam, and an ``OR``-based
    rewrite is both harder to read and worse for the planner.

    ``tuple_()`` is required here; a plain Python tuple comparison would
    compare the column objects themselves, not emit SQL.
    """
    statement = statement.order_by(model.created_at.desc(), model.id.desc())
    if after is not None:
        # literal() binds the cursor values as parameters rather than
        # inlining them, so the comparison is both typed and injection-safe.
        statement = statement.where(
            tuple_(model.created_at, model.id)
            < tuple_(literal(after.created_at), literal(after.id))
        )
    return statement


class SqlAlchemyWorkspaceRepository(SqlAlchemyRepository):
    async def add(self, workspace: Workspace) -> None:
        await self._add(
            WorkspaceModel(
                id=workspace.id,
                name=workspace.name,
                created_at=workspace.created_at,
                updated_at=workspace.updated_at,
                created_by=workspace.created_by,
                updated_by=workspace.updated_by,
            )
        )

    async def get(self, workspace_id: UUID) -> Workspace | None:
        model = await self._session.get(WorkspaceModel, workspace_id)
        return _workspace_to_domain(model) if model is not None else None

    async def list_visible(self, *, limit: int, after: CursorPosition | None) -> list[Workspace]:
        """No user filter appears here by design: the workspace table's RLS
        policy already restricts rows to workspaces the session's
        ``app.user_id`` is a member of (11-tenancy.md)."""
        statement = _apply_keyset(select(WorkspaceModel), WorkspaceModel, after).limit(limit)
        models = (await self._session.execute(statement)).scalars().all()
        return [_workspace_to_domain(model) for model in models]


class SqlAlchemyMembershipRepository(SqlAlchemyRepository):
    async def add(self, membership: Membership) -> None:
        await self._add(
            MembershipModel(
                id=membership.id,
                workspace_id=membership.workspace_id,
                user_id=membership.user_id,
                role=membership.role,
                created_at=membership.created_at,
                updated_at=membership.updated_at,
                created_by=membership.created_by,
                updated_by=membership.updated_by,
            )
        )

    async def get(self, workspace_id: UUID, user_id: UUID) -> Membership | None:
        stmt = select(MembershipModel).where(
            MembershipModel.workspace_id == workspace_id,
            MembershipModel.user_id == user_id,
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _membership_to_domain(model) if model is not None else None

    async def list_page_for_workspace(
        self, workspace_id: UUID, *, limit: int, after: CursorPosition | None
    ) -> list[Membership]:
        statement = _apply_keyset(
            select(MembershipModel).where(MembershipModel.workspace_id == workspace_id),
            MembershipModel,
            after,
        ).limit(limit)
        models = (await self._session.execute(statement)).scalars().all()
        return [_membership_to_domain(model) for model in models]


__all__ = ["SqlAlchemyMembershipRepository", "SqlAlchemyWorkspaceRepository"]

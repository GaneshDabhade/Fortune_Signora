"""SQLAlchemy implementations of this module's repository ports.

Each repository is constructed with the request/job-scoped ``AsyncSession``
(bound by the composition root — see ``composition.py``) and maps explicitly
between domain entities and ORM models in both directions.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.workspace_tenancy.domain.entities import Membership, Workspace
from modules.workspace_tenancy.infrastructure.models import MembershipModel, WorkspaceModel


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


class SqlAlchemyWorkspaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, workspace: Workspace) -> None:
        self._session.add(
            WorkspaceModel(
                id=workspace.id,
                name=workspace.name,
                created_at=workspace.created_at,
                updated_at=workspace.updated_at,
                created_by=workspace.created_by,
                updated_by=workspace.updated_by,
            )
        )
        # Flush (not commit) so a subsequent query in the same transaction —
        # e.g. the membership FK check — sees this row; the transaction as a
        # whole is committed by whoever opened the session (composition
        # root), never by the repository.
        await self._session.flush()

    async def get(self, workspace_id: UUID) -> Workspace | None:
        model = await self._session.get(WorkspaceModel, workspace_id)
        return _workspace_to_domain(model) if model is not None else None


class SqlAlchemyMembershipRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, membership: Membership) -> None:
        self._session.add(
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
        await self._session.flush()

    async def get(self, workspace_id: UUID, user_id: UUID) -> Membership | None:
        stmt = select(MembershipModel).where(
            MembershipModel.workspace_id == workspace_id,
            MembershipModel.user_id == user_id,
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _membership_to_domain(model) if model is not None else None

    async def list_for_workspace(self, workspace_id: UUID) -> list[Membership]:
        stmt = select(MembershipModel).where(MembershipModel.workspace_id == workspace_id)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_membership_to_domain(model) for model in models]

    async def list_for_user(self, user_id: UUID) -> list[Membership]:
        stmt = select(MembershipModel).where(MembershipModel.user_id == user_id)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_membership_to_domain(model) for model in models]


__all__ = ["SqlAlchemyMembershipRepository", "SqlAlchemyWorkspaceRepository"]

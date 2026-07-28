"""Implements ``public.query_port.WorkspaceQueryPort`` — the one interface
other modules are allowed to call synchronously. Kept intentionally thin and
read-only; it must never grow write operations or module-internal logic.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.workspace_tenancy.infrastructure.models import MembershipModel, WorkspaceModel
from modules.workspace_tenancy.public.query_port import MembershipView


class WorkspaceQueryService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def workspace_exists(self, workspace_id: UUID) -> bool:
        return await self._session.get(WorkspaceModel, workspace_id) is not None

    async def get_membership(self, workspace_id: UUID, user_id: UUID) -> MembershipView | None:
        stmt = select(MembershipModel).where(
            MembershipModel.workspace_id == workspace_id,
            MembershipModel.user_id == user_id,
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        if model is None:
            return None
        return MembershipView(
            workspace_id=model.workspace_id,
            user_id=model.user_id,
            role=model.role.value,
        )

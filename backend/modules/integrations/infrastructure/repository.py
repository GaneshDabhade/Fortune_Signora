"""SQL-backed repositories for Integrations."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.integrations.domain.connection import ConnectedAccount, ConnectionState
from modules.integrations.domain.grant import IntegrationGrant
from modules.integrations.infrastructure.models import (
    ConnectedAccountModel,
    IntegrationGrantModel,
)


def _to_account(row: ConnectedAccountModel) -> ConnectedAccount:
    return ConnectedAccount(
        id=row.id,
        workspace_id=row.workspace_id,
        integration=row.integration,
        external_account_id=row.external_account_id,
        endpoint=row.endpoint,
        label=row.label,
        state=ConnectionState(row.state),
        connected_at=row.connected_at,
    )


class SqlConnectedAccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, workspace_id: UUID, account_id: UUID) -> ConnectedAccount | None:
        # `workspace_id` filtered explicitly beside RLS — defence in depth (§8).
        row = (
            await self._session.execute(
                select(ConnectedAccountModel).where(
                    ConnectedAccountModel.workspace_id == workspace_id,
                    ConnectedAccountModel.id == account_id,
                )
            )
        ).scalar_one_or_none()
        return _to_account(row) if row is not None else None

    async def list_for_workspace(self, workspace_id: UUID) -> list[ConnectedAccount]:
        # Ordered so a screen is stable between reloads. By integration first
        # because that is how a customer groups them — every Google Calendar
        # together — and by label within, which is the name they chose.
        rows = (
            (
                await self._session.execute(
                    select(ConnectedAccountModel)
                    .where(ConnectedAccountModel.workspace_id == workspace_id)
                    .order_by(ConnectedAccountModel.integration, ConnectedAccountModel.label)
                )
            )
            .scalars()
            .all()
        )
        return [_to_account(row) for row in rows]

    async def save(self, account: ConnectedAccount) -> None:
        row = await self._session.get(ConnectedAccountModel, account.id)
        if row is None:
            self._session.add(
                ConnectedAccountModel(
                    id=account.id,
                    workspace_id=account.workspace_id,
                    integration=account.integration,
                    external_account_id=account.external_account_id,
                    endpoint=account.endpoint,
                    label=account.label,
                    state=account.state.value,
                    connected_at=account.connected_at,
                )
            )
            return
        # A connection is a live relationship, so this is one of the few places
        # in the repository that updates rather than supersedes (migration 0027).
        row.endpoint = account.endpoint
        row.label = account.label
        row.state = account.state.value
        row.connected_at = account.connected_at


class SqlGrantStore:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def current_for(
        self, workspace_id: UUID, connected_account_id: UUID
    ) -> IntegrationGrant | None:
        # The live grant is the one not revoked. A connection may accumulate
        # revoked grants across reconnections, and they are history rather than
        # candidates.
        row = (
            await self._session.execute(
                select(IntegrationGrantModel)
                .where(
                    IntegrationGrantModel.workspace_id == workspace_id,
                    IntegrationGrantModel.connected_account_id == connected_account_id,
                    IntegrationGrantModel.revoked_at.is_(None),
                )
                .order_by(IntegrationGrantModel.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if row is None:
            return None
        return IntegrationGrant(
            id=row.id,
            workspace_id=row.workspace_id,
            connected_account_id=row.connected_account_id,
            secret_ref=row.secret_ref,
            scopes=tuple(row.scopes),
            expires_at=row.expires_at,
            refreshable=row.refreshable,
            revoked_at=row.revoked_at,
        )

    async def save(self, grant: IntegrationGrant) -> None:
        row = await self._session.get(IntegrationGrantModel, grant.id)
        if row is None:
            self._session.add(
                IntegrationGrantModel(
                    id=grant.id,
                    workspace_id=grant.workspace_id,
                    connected_account_id=grant.connected_account_id,
                    secret_ref=grant.secret_ref,
                    scopes=list(grant.scopes),
                    expires_at=grant.expires_at,
                    refreshable=grant.refreshable,
                    revoked_at=grant.revoked_at,
                )
            )
            return
        row.expires_at = grant.expires_at
        row.revoked_at = grant.revoked_at
        row.secret_ref = grant.secret_ref

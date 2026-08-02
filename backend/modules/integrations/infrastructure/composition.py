"""Wiring for Integrations. The one place that knows the stores are SQL-backed."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from modules.integrations.application.ports import ConnectedAccountRepository, GrantStore
from modules.integrations.application.queries import IntegrationQueries
from modules.integrations.infrastructure.repository import (
    SqlConnectedAccountRepository,
    SqlGrantStore,
)


def build_connected_accounts(session: AsyncSession) -> ConnectedAccountRepository:
    return SqlConnectedAccountRepository(session)


def build_grants(session: AsyncSession) -> GrantStore:
    return SqlGrantStore(session)


def build_integration_queries(session: AsyncSession) -> IntegrationQueries:
    return IntegrationQueries(build_connected_accounts(session), build_grants(session))


# `ResolveExecutionContext` is deliberately not wired here. Its `SecretStore`
# has no production implementation until the vault arrives, and a factory that
# could only raise would be a wiring that lies about what exists.

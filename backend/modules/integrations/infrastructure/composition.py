"""Wiring for Integrations. The one place that knows the stores are SQL-backed."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from modules.integrations.application.ports import ConnectedAccountRepository, GrantStore
from modules.integrations.application.disconnect import DisconnectSystem
from modules.integrations.application.queries import IntegrationQueries
from modules.integrations.infrastructure.repository import (
    SqlConnectedAccountRepository,
    SqlGrantStore,
)
from modules.integrations.infrastructure.secrets import EncryptedSecretStore
from modules.integrations.infrastructure.settings import IntegrationSettings


def build_connected_accounts(session: AsyncSession) -> ConnectedAccountRepository:
    return SqlConnectedAccountRepository(session)


def build_grants(session: AsyncSession) -> GrantStore:
    return SqlGrantStore(session)


def build_integration_queries(session: AsyncSession) -> IntegrationQueries:
    return IntegrationQueries(build_connected_accounts(session), build_grants(session))


# `ResolveExecutionContext` is deliberately not wired here. Its `SecretStore`
# has no production implementation until the vault arrives, and a factory that
# could only raise would be a wiring that lies about what exists.


def build_disconnect_system(session: AsyncSession, settings: IntegrationSettings) -> DisconnectSystem:
    """**No revoker, and that is honest rather than incomplete.** No adapter
    exists to call a vendor's revocation endpoint, and `NoRevoker` reports
    failure — so a customer is told their access was removed here and may still
    need removing at the vendor, which is true."""
    return DisconnectSystem(
        SqlConnectedAccountRepository(session),
        SqlGrantStore(session),
        EncryptedSecretStore(session, settings.secret_key),
    )

"""Wiring for Integrations. The one place that knows the stores are SQL-backed."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from modules.integrations.application.ports import ConnectedAccountRepository, GrantStore
from modules.integrations.application.connect import ConnectSystem
from modules.integrations.application.disconnect import DisconnectSystem
from modules.integrations.application.refresh import RefreshGrant
from modules.integrations.application.resolve import ResolveExecutionContext
from modules.integrations.application.queries import IntegrationQueries
from modules.integrations.infrastructure.repository import (
    SqlConnectedAccountRepository,
    SqlGrantStore,
)
from modules.integrations.infrastructure.refreshing import (
    HttpTokenRefresher,
    SettingsClientCredentials,
)
from modules.integrations.infrastructure.revocation import HttpProviderRevoker
from modules.integrations.infrastructure.secrets import EncryptedSecretStore
from modules.integrations.infrastructure.settings import IntegrationSettings


def build_connected_accounts(session: AsyncSession) -> ConnectedAccountRepository:
    return SqlConnectedAccountRepository(session)


def build_grants(session: AsyncSession) -> GrantStore:
    return SqlGrantStore(session)


def build_integration_queries(session: AsyncSession) -> IntegrationQueries:
    return IntegrationQueries(build_connected_accounts(session), build_grants(session))


# `ResolveExecutionContext` is wired at the end of this file, now that it can
# do its whole job — see `build_resolve_execution_context`.


def build_disconnect_system(
    session: AsyncSession, settings: IntegrationSettings, workspace_id: UUID
) -> DisconnectSystem:
    """**With a revoker, since 2026-08-04.** Until then `NoRevoker` reported
    failure and the product said so honestly — a customer was told their access
    was removed here and may still need removing at the vendor, which was true
    and left them holding a live credential.

    **The revoker takes the workspace** because the port is
    `revoke(connected_account_id)` and an adapter that read a connection
    without scoping it would be reaching across a tenant boundary to do it.
    RLS would refuse, and depending on that refusal rather than passing the
    scope is exactly the defence-in-depth §8 declines to skip.
    """
    accounts = SqlConnectedAccountRepository(session)
    grants = SqlGrantStore(session)
    secrets = EncryptedSecretStore(session, settings.secret_key)
    return DisconnectSystem(
        accounts,
        grants,
        secrets,
        revoker=HttpProviderRevoker(accounts, grants, secrets, workspace_id),
    )


def build_connect_system(session: AsyncSession, settings: IntegrationSettings) -> ConnectSystem:
    """The same encrypted store the disconnect path purges from.

    One `SecretStore` implementation behind three ports — write here, read for
    execution, destroy on disconnect — so material written by this path is
    material `purge_for` can find. Two implementations would eventually be two
    key configurations, and the failure would surface as a credential nobody
    could decrypt on the day somebody needed to revoke it.
    """
    return ConnectSystem(
        SqlConnectedAccountRepository(session),
        SqlGrantStore(session),
        EncryptedSecretStore(session, settings.secret_key),
    )


def build_refresh_grant(
    session: AsyncSession, settings: IntegrationSettings
) -> RefreshGrant:
    """**With a real refresher only when one can work.**

    A deployment that has configured no client credentials gets
    `NoTokenRefresher`, which reports it could not renew — the same shape
    `credentialsFor()` produces at the other tier when its environment holds no
    client id, and the same honesty `NoRevoker` had. **A factory that returned
    a refresher which could only fail per connection would be a wiring that
    lies about what exists**, which is the reasoning that keeps
    `ResolveExecutionContext` unwired above.
    """
    secrets = EncryptedSecretStore(session, settings.secret_key)
    credentials = SettingsClientCredentials(settings)
    return RefreshGrant(
        SqlConnectedAccountRepository(session),
        SqlGrantStore(session),
        secrets,
        secrets,
        HttpTokenRefresher(credentials) if credentials.any_configured() else None,
    )


def build_resolve_execution_context(
    session: AsyncSession, settings: IntegrationSettings
) -> ResolveExecutionContext:
    """Resolution, with a renewal attached to it.

    **Refresh-on-use, because that is the only moment a renewal is needed.** A
    credential is renewed when something is about to use it, and this is that
    moment — so the capability needs no scheduler, which the repository does
    not have and which would not be this module's to add.

    **Still called by nothing.** Its consumer is whatever synchronizes through
    a connection, which is
    [ADR-0300](../../../../docs/architecture/adr/0300-inbound-customer-systems.md)'s
    to decide. The factory exists because it can now do its whole job — which
    is exactly the condition the note it replaced was waiting for, and the
    reason that note was not simply a deferral.
    """
    return ResolveExecutionContext(
        SqlConnectedAccountRepository(session),
        SqlGrantStore(session),
        EncryptedSecretStore(session, settings.secret_key),
        build_refresh_grant(session, settings),
    )

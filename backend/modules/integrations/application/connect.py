"""Recording that a customer connected one of their own systems."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID, uuid4

from modules.integrations.application.ports import ConnectedAccountRepository, GrantStore
from modules.integrations.domain.catalog import entry_for
from modules.integrations.domain.connection import ConnectedAccount, ConnectionState
from modules.integrations.domain.grant import Credential, IntegrationGrant


class SecretWriter(Protocol):
    """Writing material, which the read-side `SecretStore` deliberately cannot.

    **Split from `SecretStore` for the same reason `EntryStore` and `FeedReader`
    were split in Timeline**: a component that only ever needs to read a
    credential must not be handed the ability to write one.
    """

    async def store(
        self,
        *,
        secret_ref: str,
        workspace_id: str,
        connected_account_id: str,
        credential: Credential,
    ) -> None: ...


class UnknownIntegration(Exception):
    """A slug the catalog does not contain.

    **Refused rather than accepted.** Storing a connection to a system Signora
    does not understand would put a row on a customer's screen that nothing can
    ever act on, and no adapter could resolve.
    """


@dataclass(frozen=True, slots=True)
class ConnectInput:
    """What the acquisition flow hands over once the customer has consented.

    **Assembled at the frontend edge and never here.** The redirect, the
    consent screen and the authorization-code exchange happen in Next.js
    ([18-authentication.md](../../../../docs/architecture/18-authentication.md)),
    and this module receives the result. Nothing in this type names OAuth,
    because an API key or a certificate arrives through the same door.
    """

    workspace_id: UUID
    actor_id: UUID
    integration: str
    external_account_id: str
    label: str
    endpoint: str | None
    credential: Credential
    scopes: tuple[str, ...]
    expires_at: datetime | None
    refreshable: bool


class ConnectSystem:
    """Records a connection and the grant that authorises it."""

    def __init__(
        self,
        accounts: ConnectedAccountRepository,
        grants: GrantStore,
        secrets: SecretWriter,
    ) -> None:
        self._accounts = accounts
        self._grants = grants
        self._secrets = secrets

    async def execute(self, request: ConnectInput, *, at: datetime) -> ConnectedAccount:
        if entry_for(request.integration) is None:
            raise UnknownIntegration(request.integration)

        account = ConnectedAccount(
            id=uuid4(),
            workspace_id=request.workspace_id,
            integration=request.integration,
            external_account_id=request.external_account_id,
            endpoint=request.endpoint,
            label=request.label,
            # Through `AUTHORIZING` rather than straight to `CONNECTED`: the
            # lifecycle says a connection is authorized before it exists, and a
            # use case that skipped its own state machine would make the machine
            # decorative.
            state=ConnectionState.NOT_CONNECTED,
            connected_at=None,
        ).transition(ConnectionState.AUTHORIZING, at=at).transition(
            ConnectionState.CONNECTED, at=at
        )

        secret_ref = f"integration/{account.id}"
        # Material first. If the grant were written first and this failed, a
        # connection would read as working with nothing behind it — and the
        # screen would say "Ready to use" about a credential that does not
        # exist.
        await self._secrets.store(
            secret_ref=secret_ref,
            workspace_id=str(request.workspace_id),
            connected_account_id=str(account.id),
            credential=request.credential,
        )
        await self._accounts.save(account)
        await self._grants.save(
            IntegrationGrant(
                id=uuid4(),
                workspace_id=request.workspace_id,
                connected_account_id=account.id,
                secret_ref=secret_ref,
                scopes=request.scopes,
                expires_at=request.expires_at,
                refreshable=request.refreshable,
                revoked_at=None,
            )
        )
        return account

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

        # Through `AUTHORIZING` rather than straight to `CONNECTED`: the
        # lifecycle says a connection is authorized before it exists, and a use
        # case that skipped its own state machine would make the machine
        # decorative.
        authorizing = ConnectedAccount(
            id=uuid4(),
            workspace_id=request.workspace_id,
            integration=request.integration,
            external_account_id=request.external_account_id,
            endpoint=request.endpoint,
            label=request.label,
            state=ConnectionState.NOT_CONNECTED,
            connected_at=None,
            actor_id=request.actor_id,
        ).transition(ConnectionState.AUTHORIZING, at=at, by=request.actor_id)

        # **The connection is written first, and the order is not stylistic.**
        # Material and grants are children of a connection — `integration_secret`
        # and `integration_grant` both carry a foreign key to it — so writing
        # either first is refused by the database. Found by the first test to
        # run this against PostgreSQL rather than a fake, which accepted any
        # order; see B-024.
        #
        # It costs nothing, because the row lands in `AUTHORIZING`. A failure
        # anywhere below therefore leaves a connection that reads as *"you
        # started connecting this and did not finish"* — which is true, is
        # already what the Connection Center says, and is already something a
        # customer can disconnect. The state it must never be left in is
        # `CONNECTED` with nothing behind it, and that only happens on the last
        # line.
        await self._accounts.save(authorizing)

        secret_ref = f"integration/{authorizing.id}"
        # Material before the grant. A grant naming a credential that was never
        # stored would read as usable and fail at the vendor.
        await self._secrets.store(
            secret_ref=secret_ref,
            workspace_id=str(request.workspace_id),
            connected_account_id=str(authorizing.id),
            credential=request.credential,
        )
        await self._grants.save(
            IntegrationGrant(
                id=uuid4(),
                workspace_id=request.workspace_id,
                connected_account_id=authorizing.id,
                secret_ref=secret_ref,
                scopes=request.scopes,
                expires_at=request.expires_at,
                refreshable=request.refreshable,
                revoked_at=None,
                actor_id=request.actor_id,
            )
        )

        connected = authorizing.transition(
            ConnectionState.CONNECTED, at=at, by=request.actor_id
        )
        await self._accounts.save(connected)
        return connected

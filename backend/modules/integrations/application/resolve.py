"""Resolving a connection into something an adapter can execute against."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from modules.integrations.application.ports import (
    ConnectedAccountRepository,
    GrantStore,
    SecretStore,
)
from modules.integrations.domain.connection import ConnectedAccount, ConnectionState
from modules.integrations.domain.grant import Credential


class ConnectionUnusable(Exception):
    """The connection cannot be executed against, and the message says why.

    One exception carrying the state rather than one per state: a caller does
    the same thing with all of them — stop, and tell somebody — and the state is
    what it reports.
    """

    def __init__(self, state: ConnectionState, detail: str) -> None:
        self.state = state
        super().__init__(detail)


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    """Everything an adapter needs to act, and nothing about how it was
    obtained.

    **The unit of resolution, deliberately larger than a credential.** Resolving
    only a credential would couple every future concern — region, throttling,
    retry policy, audit context — to the one that happened to be first. An
    adapter receives a context and reads what it needs from it, so adding a
    field later changes no signature.

    **It carries no vendor identity a caller can branch on.** `integration` is
    the catalog slug an adapter was chosen *by*; nothing above the adapter is
    expected to read it, and business behaviour that varied on it would be the
    vendor leaking upward — the rule the AI Platform already holds.
    """

    workspace_id: UUID
    connected_account_id: UUID
    integration: str
    #: Where to reach this account, when the vendor is not one fixed host.
    endpoint: str | None
    #: What the customer permitted, so a missing scope is a readable refusal.
    scopes: tuple[str, ...]
    credential: Credential

    def __repr__(self) -> str:
        # The credential redacts itself; this stops a careless container from
        # rendering it by rendering the whole context.
        return (
            f"ExecutionContext(workspace_id={self.workspace_id!r}, "
            f"connected_account_id={self.connected_account_id!r}, "
            f"integration={self.integration!r}, credential=<redacted>)"
        )

    __str__ = __repr__


class ResolveExecutionContext:
    """Turns a connection into an execution context, or refuses.

    **The one place the three separated capabilities meet**, and it is a
    read: acquisition happened elsewhere and earlier, management owns the
    lifecycle checks below, and synchronization receives the result knowing
    none of it.
    """

    def __init__(
        self,
        accounts: ConnectedAccountRepository,
        grants: GrantStore,
        secrets: SecretStore,
    ) -> None:
        self._accounts = accounts
        self._grants = grants
        self._secrets = secrets

    async def execute(
        self, workspace_id: UUID, connected_account_id: UUID, *, at: datetime
    ) -> ExecutionContext:
        account = await self._accounts.get(workspace_id, connected_account_id)
        if account is None:
            # Same reasoning as the 404-not-403 rule: a caller who names a
            # connection in a workspace they cannot see learns nothing.
            raise ConnectionUnusable(
                ConnectionState.NOT_CONNECTED, "no such connection in this workspace"
            )
        self._refuse_if_unusable(account)

        grant = await self._grants.current_for(workspace_id, connected_account_id)
        if grant is None:
            raise ConnectionUnusable(
                account.state, "the connection has no grant to act with"
            )
        # Raises `GrantExpired` or `GrantRevoked` — distinct on purpose, because
        # one is refreshed and the other needs the customer back.
        grant.check_usable(at=at)

        return ExecutionContext(
            workspace_id=workspace_id,
            connected_account_id=connected_account_id,
            integration=account.integration,
            endpoint=account.endpoint,
            scopes=grant.scopes,
            credential=await self._secrets.resolve(grant.secret_ref),
        )

    @staticmethod
    def _refuse_if_unusable(account: ConnectedAccount) -> None:
        if account.is_usable:
            return
        raise ConnectionUnusable(
            account.state,
            f"the connection is {account.state.value.replace('_', ' ')}",
        )

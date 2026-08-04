"""Resolving a connection into something an adapter can execute against."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Final
from uuid import UUID

from modules.integrations.application.ports import (
    ConnectedAccountRepository,
    GrantStore,
    SecretNotFound,
    SecretStore,
)
from modules.integrations.application.refresh import RefreshGrant, RefreshOutcome
from modules.integrations.domain.connection import ConnectedAccount, ConnectionState
from modules.integrations.domain.grant import Credential, GrantExpired, IntegrationGrant

#: Who a renewal is attributed to when nobody asked for it.
#:
#: **A renewal is not a person's action.** `transition()` and every audit column
#: demand an actor with no default, deliberately — *"who disconnected our CRM?"*
#: is asked during an incident — and the honest answer here is *the platform*,
#: not the customer who happened to consent months earlier.
#:
#: The same constant and the same value `provider_platform` already uses for
#: its own unattended writes. **Declared here rather than imported**: a module
#: does not reach into another's internals, and the convention is the shared
#: thing, not the symbol.
SYSTEM_ACTOR_ID: Final = UUID("00000000-0000-0000-0000-000000000001")


class CredentialUnreadable(Exception):
    """The credential exists and cannot be read.

    **An operational state, not a crash.** A rotated or wrong encryption key,
    or material purged while a grant survived, are indistinguishable here and
    mean the same thing to a customer: this connection has to be made again. A
    stack trace tells them nothing they can act on; *"reconnect"* tells them
    everything.

    Distinct from `ConnectionUnusable` because the connection's *state* is
    fine — it is the material behind it that is not, and reporting it as a
    revoked or expired connection would be describing the wrong thing.
    """


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
        refresher: RefreshGrant | None = None,
    ) -> None:
        self._accounts = accounts
        self._grants = grants
        self._secrets = secrets
        self._refresher = refresher

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
        # one is refreshed and the other needs the customer back. **This is
        # where that distinction stops being commentary**: an expired grant is
        # renewed here and the caller never learns it lapsed, which is the
        # entire reason `refreshable` is recorded.
        #
        # **Revocation is untouched.** `check_usable` raises revoked before
        # expired, so a customer who withdrew Signora at the vendor is never
        # quietly reconnected — the same refusal `RefreshGrant` applies again
        # one layer down.
        try:
            grant.check_usable(at=at)
        except GrantExpired:
            grant = await self._renewed(workspace_id, connected_account_id, at=at)

        try:
            credential = await self._secrets.resolve(grant.secret_ref)
        except SecretNotFound as exc:
            # A grant outliving its material. Reported as unreadable rather
            # than propagated, so it reaches a customer as *reconnect* instead
            # of as an unhandled exception in a worker log.
            raise CredentialUnreadable(str(exc)) from exc

        return ExecutionContext(
            workspace_id=workspace_id,
            connected_account_id=connected_account_id,
            integration=account.integration,
            endpoint=account.endpoint,
            scopes=grant.scopes,
            credential=credential,
        )

    async def _renewed(
        self, workspace_id: UUID, connected_account_id: UUID, *, at: datetime
    ) -> IntegrationGrant:
        """Renew in place, or let the expiry stand.

        **Refresh-on-use rather than a scheduled sweep.** A renewal is only
        ever needed at the moment a credential is about to be used, and this is
        that moment — so the capability needs no scheduler, which the
        repository does not have and which would not be this module's to add.

        Every failure re-raises the original `GrantExpired`: the caller's
        situation is unchanged, and a new exception type would make *we tried
        and could not* look different from *we never could*, when the customer
        does the same thing about both.
        """
        if self._refresher is None:
            raise
        result = await self._refresher.execute(
            workspace_id, connected_account_id, at=at, actor_id=SYSTEM_ACTOR_ID
        )
        if result.outcome is not RefreshOutcome.RENEWED:
            raise
        renewed = await self._grants.current_for(workspace_id, connected_account_id)
        if renewed is None:
            raise
        # Checked again rather than assumed. A vendor that returned material
        # already past its expiry would otherwise be handed to an adapter as
        # though it worked.
        renewed.check_usable(at=at)
        return renewed

    @staticmethod
    def _refuse_if_unusable(account: ConnectedAccount) -> None:
        if account.is_usable:
            return
        raise ConnectionUnusable(
            account.state,
            f"the connection is {account.state.value.replace('_', ' ')}",
        )

"""Renewing a grant before a customer has to notice it expired.

**Everything here is built and one thing is deliberately not decided.** A
refresh needs the OAuth *client* credentials — the application's own id and
secret, not the customer's — and **where those live is an architectural
boundary, not this module's to choose**: they are frontend environment values
today, and moving them is a change to credential ownership and to the trust
boundary between the two tiers.

So the dependency is isolated to **one port**, `TokenRefresher`, and everything
on either side of it is complete and tested. `NoTokenRefresher` is the default
and reports that it could not act — the same honest shape `NoRevoker` held
until an adapter existed. **The unresolved boundary is one wiring line, and
nothing else waits on it.** Recorded as
[C-327](../../../../docs/LANE_COORDINATION.md).

### Why a refresh is a new grant rather than an edit

**Material is never edited in place** (§3): a rotation writes a new
`secret_ref` and leaves the old one to be purged. The old grant is revoked and
a new one takes its place, so `current_for` keeps meaning *the live grant* and
the history of what was live when survives — which is the only thing that makes
a rotation diagnosable while it is happening.

### Why it can revive an expired connection

`EXPIRED → CONNECTED` is already in the transition table. A grant that renews
brings the connection back with it, and the customer never learns that anything
lapsed — which is the entire point of storing `refreshable` in the first place.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID, uuid4

from modules.integrations.application.connect import SecretWriter
from modules.integrations.application.ports import (
    ConnectedAccountRepository,
    GrantStore,
    SecretNotFound,
    SecretStore,
)
from modules.integrations.domain.connection import ConnectedAccount, ConnectionState
from modules.integrations.domain.grant import IntegrationGrant, OAuth2Material


@dataclass(frozen=True, slots=True)
class RenewedMaterial:
    """What a provider returns when a grant is renewed — RFC 6749 §6.

    **A new refresh token is optional and must not be assumed.** Google returns
    none and the old one stays valid; HubSpot issues a fresh one each time.
    Overwriting with `None` in the first case would destroy the only thing that
    could ever renew the grant again.
    """

    access_token: str
    refresh_token: str | None
    expires_at: datetime | None


class TokenRefresher(Protocol):
    """Exchanges a refresh token for new material.

    **The one seam that needs the OAuth client credentials**, and therefore the
    one place the unresolved boundary touches. An implementation needs the
    application's own client id and secret; nothing above this line does.
    """

    async def renew(self, integration: str, refresh_token: str) -> RenewedMaterial | None:
        """New material, or `None` when the provider would not renew."""
        ...


class NoTokenRefresher:
    """The default, and it reports that it could not renew.

    **Honest rather than incomplete**, exactly as `NoRevoker` was: no adapter
    can run until the client credentials have somewhere to live, and a refresher
    that claimed success would leave a connection reading healthy with material
    that stopped working.
    """

    async def renew(self, integration: str, refresh_token: str) -> RenewedMaterial | None:
        return None


class RefreshOutcome(StrEnum):
    """Why a refresh did or did not happen.

    **Five outcomes rather than a boolean**, because a caller does something
    different with each: renewed is silent, `NOT_REFRESHABLE` means the
    customer must reconnect, `REFUSED` may mean they revoked Signora at the
    vendor, and `UNREADABLE` is an operational fault on Signora's side.
    """

    RENEWED = "renewed"
    #: No live grant, or one the provider said cannot be renewed.
    NOT_REFRESHABLE = "not_refreshable"
    #: The provider declined. Commonly a customer withdrawing access there.
    REFUSED = "refused"
    #: Material Signora cannot read — a rotated key, or a purged secret.
    UNREADABLE = "unreadable"
    #: The connection is gone, or is in a state that cannot hold a grant.
    UNUSABLE = "unusable"


@dataclass(frozen=True, slots=True)
class RefreshResult:
    outcome: RefreshOutcome
    account: ConnectedAccount | None = None


class RefreshGrant:
    """Renews the live grant on a connection, or says why it did not."""

    def __init__(
        self,
        accounts: ConnectedAccountRepository,
        grants: GrantStore,
        secrets: SecretStore,
        writer: SecretWriter,
        refresher: TokenRefresher | None = None,
    ) -> None:
        self._accounts = accounts
        self._grants = grants
        self._secrets = secrets
        self._writer = writer
        self._refresher = refresher or NoTokenRefresher()

    async def execute(
        self,
        workspace_id: UUID,
        connected_account_id: UUID,
        *,
        at: datetime,
        actor_id: UUID,
    ) -> RefreshResult:
        account = await self._accounts.get(workspace_id, connected_account_id)
        if account is None or account.state in _CANNOT_HOLD_A_GRANT:
            # A disconnected or revoked connection has nothing to renew, and
            # renewing one would resurrect access the customer withdrew.
            return RefreshResult(RefreshOutcome.UNUSABLE)

        grant = await self._grants.current_for(workspace_id, connected_account_id)
        if grant is None or not grant.refreshable:
            return RefreshResult(RefreshOutcome.NOT_REFRESHABLE, account)

        current = await self._material(grant.secret_ref)
        if current is None:
            return RefreshResult(RefreshOutcome.UNREADABLE, account)
        if current.refresh_token is None:
            # `refreshable` said yes and the material carries nothing to renew
            # with. Reported rather than attempted: the two disagreeing is a
            # defect, and sending `None` to a vendor would hide it behind a
            # provider refusal.
            return RefreshResult(RefreshOutcome.NOT_REFRESHABLE, account)

        renewed = await self._refresher.renew(account.integration, current.refresh_token)
        if renewed is None:
            return RefreshResult(RefreshOutcome.REFUSED, account)

        await self._replace(workspace_id, account, grant, renewed, current, at=at, actor=actor_id)
        return RefreshResult(RefreshOutcome.RENEWED, await self._revive(account, at, actor_id))

    async def _replace(
        self,
        workspace_id: UUID,
        account: ConnectedAccount,
        previous: IntegrationGrant,
        renewed: RenewedMaterial,
        current: OAuth2Material,
        *,
        at: datetime,
        actor: UUID,
    ) -> None:
        grant_id = uuid4()
        secret_ref = f"integration/{account.id}/{grant_id}"
        await self._writer.store(
            secret_ref=secret_ref,
            workspace_id=str(workspace_id),
            connected_account_id=str(account.id),
            credential=OAuth2Material(
                access_token=renewed.access_token,
                # **The old one is kept when the provider issued no new one.**
                # Google does exactly that, and overwriting with `None` would
                # destroy the only thing that could renew this grant again.
                refresh_token=renewed.refresh_token or current.refresh_token,
            ).as_credential(),
        )
        # The new grant before the old is revoked, so `current_for` never
        # returns nothing — a reader between the two writes sees the grant that
        # is about to be replaced rather than no grant at all.
        await self._grants.save(
            IntegrationGrant(
                id=grant_id,
                workspace_id=workspace_id,
                connected_account_id=account.id,
                secret_ref=secret_ref,
                # **Carried forward, never re-derived.** A refresh does not ask
                # the customer for anything, so it cannot widen or narrow what
                # they permitted, and a provider that echoes a shorter list is
                # describing this call rather than the grant.
                scopes=previous.scopes,
                expires_at=renewed.expires_at,
                refreshable=True,
                revoked_at=None,
                actor_id=actor,
            )
        )
        await self._grants.save(previous.revoke(at=at, by=actor))

    async def _revive(
        self, account: ConnectedAccount, at: datetime, actor: UUID
    ) -> ConnectedAccount:
        """A renewed grant brings an expired connection back with it.

        `EXPIRED → CONNECTED` is already in the transition table, and using it
        is what makes a refresh invisible to the customer — which is the entire
        reason `refreshable` is recorded.
        """
        if account.state is not ConnectionState.EXPIRED:
            return account
        revived = account.transition(ConnectionState.CONNECTED, at=at, by=actor)
        await self._accounts.save(revived)
        return revived

    async def _material(self, secret_ref: str) -> OAuth2Material | None:
        try:
            credential = await self._secrets.resolve(secret_ref)
        except SecretNotFound:
            return None
        return OAuth2Material.read(credential)


#: States in which a connection cannot hold a live grant. **`DISCONNECTED` and
#: `REVOKED` are deliberate**: renewing either would restore access a customer
#: or a vendor deliberately withdrew.
_CANNOT_HOLD_A_GRANT = frozenset(
    {
        ConnectionState.NOT_CONNECTED,
        ConnectionState.DISCONNECTED,
        ConnectionState.REVOKED,
    }
)



__all__ = [
    "NoTokenRefresher",
    "RefreshGrant",
    "RefreshOutcome",
    "RefreshResult",
    "RenewedMaterial",
    "TokenRefresher",
]

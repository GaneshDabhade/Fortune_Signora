"""Ending a customer's relationship with one of their own systems.

**A lifecycle, not a state change.** Disconnecting is the moment a customer
withdraws trust, and it has to work when they most want it to — including when
the vendor is unreachable, which is exactly when somebody is most likely to be
disconnecting in a hurry.

Three rules shape it, and each exists because the obvious implementation gets
it wrong:

**Local disconnection always succeeds.** Provider-side revocation is attempted
and its failure is recorded, never propagated. A disconnect that fails because
HubSpot is down would leave a customer unable to revoke access at the one
moment they are trying to — a security action held hostage by the system it is
protecting them from.

**Material is destroyed, not orphaned.** Deleting a grant row leaves the
credential in storage. Purging is what makes *"Signora can no longer read from
this"* true rather than merely believed.

**It is idempotent.** A second disconnect is a customer clicking twice, not an
error, and it must not overwrite when the first one happened.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from modules.integrations.application.ports import ConnectedAccountRepository, GrantStore
from modules.integrations.domain.connection import ConnectedAccount, ConnectionState


class SecretPurger(Protocol):
    """Destroying material for a connection.

    Separate from reading and from writing, on the same rule the other two
    follow: a component that only needs to destroy must not also be able to
    read.
    """

    async def purge_for(self, connected_account_id: str) -> None: ...


class ProviderRevoker(Protocol):
    """Telling the vendor Signora is done, where the vendor supports it.

    **Best-effort by contract.** The return value says whether it worked so the
    outcome can be recorded; a raise is caught by the use case rather than
    surfacing, because no vendor failure may block a customer from disconnecting.
    """

    async def revoke(self, connected_account_id: UUID) -> bool: ...


class NoRevoker:
    """The default until an adapter exists.

    **Reports failure rather than success.** Claiming a revocation that never
    happened would tell a customer their access was withdrawn at the vendor when
    the credential is still live there — the more dangerous of the two lies.
    """

    async def revoke(self, connected_account_id: UUID) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class DisconnectResult:
    account: ConnectedAccount
    #: Whether the vendor was told. `False` means the customer should also
    #: remove Signora on the vendor's side, and the screen says so.
    revoked_at_provider: bool
    #: `True` when the connection was already disconnected. Not an error.
    already_disconnected: bool


class DisconnectSystem:
    """Ends a connection, destroys its credential, and tells the vendor if it can."""

    def __init__(
        self,
        accounts: ConnectedAccountRepository,
        grants: GrantStore,
        secrets: SecretPurger,
        revoker: ProviderRevoker | None = None,
    ) -> None:
        self._accounts = accounts
        self._grants = grants
        self._secrets = secrets
        self._revoker = revoker or NoRevoker()

    async def execute(
        self, workspace_id: UUID, connected_account_id: UUID, *, at: datetime
    ) -> DisconnectResult:
        account = await self._accounts.get(workspace_id, connected_account_id)
        if account is None:
            raise ConnectionNotFound(connected_account_id)

        if account.state is ConnectionState.DISCONNECTED:
            # Idempotent: a customer clicking twice, or a retry after a timeout.
            # Returning success without touching anything is what stops the
            # second call moving the timestamp of the first.
            return DisconnectResult(account, revoked_at_provider=False, already_disconnected=True)

        # The vendor first, because if it succeeds the customer's access is
        # already gone even should everything below fail. Its failure is
        # recorded and never raised.
        revoked = await self._try_revoke(connected_account_id)

        grant = await self._grants.current_for(workspace_id, connected_account_id)
        if grant is not None:
            await self._grants.save(grant.revoke(at=at))

        # Material last, and unconditionally. A grant marked revoked with its
        # credential still in storage is the gap this whole capability exists
        # to close.
        await self._secrets.purge_for(str(connected_account_id))

        disconnected = account.transition(ConnectionState.DISCONNECTED, at=at)
        await self._accounts.save(disconnected)
        return DisconnectResult(
            disconnected, revoked_at_provider=revoked, already_disconnected=False
        )

    async def _try_revoke(self, connected_account_id: UUID) -> bool:
        try:
            return await self._revoker.revoke(connected_account_id)
        except Exception:
            # Deliberately broad, and deliberately silent to the caller. Any
            # vendor failure — timeout, 500, DNS — must not stop a customer
            # withdrawing access. The result records that it did not happen.
            return False


class ConnectionNotFound(Exception):
    """No such connection in this workspace.

    The 404-not-403 rule: a caller who names a connection they cannot see
    learns nothing about whether it exists.
    """

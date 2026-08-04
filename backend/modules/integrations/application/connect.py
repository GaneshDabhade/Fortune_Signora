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


class AlreadyConnected(Exception):
    """This workspace has already connected this account of this system.

    **The schema decided this, not a rule written here.** `connected_account`
    is unique on `(workspace_id, integration, external_account_id)` because one
    HubSpot portal is one relationship, however many times somebody consents to
    it — and the grant table's own comment has always anticipated the sequel:
    *"a connection may accumulate revoked grants across reconnections."*

    **Raised only while the existing connection is still usable.** A
    disconnected or revoked one is *reconnected* rather than refused — that is
    the sequel the comment anticipated, and the transition table has allowed it
    all along. What this refuses is replacing a **working** grant, because a
    customer re-consenting with wider scopes would otherwise lose the one that
    currently works in order to find out whether the new one does.

    **The way out is the same either way**: disconnect, then connect.
    """


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

        # **A returning customer reconnects the relationship they already
        # had.** `connected_account` is unique on the identity below, and the
        # transition table has allowed `DISCONNECTED → AUTHORIZING` and
        # `REVOKED → AUTHORIZING` since it was written — *"the route back is
        # re-authorization"*. Nothing used either edge, because this use case
        # always minted a new id, so a customer who disconnected HubSpot could
        # never connect it again. Found by building the route that made it
        # reachable, and fixed by using the lifecycle that was already there.
        existing = await self._accounts.find_identity(
            request.workspace_id, request.integration, request.external_account_id
        )
        if existing is not None and existing.is_usable:
            # A live connection is not something to silently replace: the
            # customer may be re-consenting with wider scopes, and discarding
            # the working grant to find out would be the expensive way to
            # learn. Refused, and they disconnect first if they meant to.
            # **No identifier in the message.** It reaches a customer verbatim
            # through `ERROR_MAPPING`, and a vendor's account id is Signora's
            # bookkeeping rather than anything they asked to see — the same
            # rule that keeps `external_account_id` off `ConnectionView`.
            # Asserted by a Security Invariant, which is how this was caught.
            raise AlreadyConnected("this system is already connected to this workspace")

        # Through `AUTHORIZING` rather than straight to `CONNECTED`: the
        # lifecycle says a connection is authorized before it exists, and a use
        # case that skipped its own state machine would make the machine
        # decorative.
        authorizing = (
            existing
            if existing is not None
            else ConnectedAccount(
                id=uuid4(),
                workspace_id=request.workspace_id,
                integration=request.integration,
                external_account_id=request.external_account_id,
                endpoint=request.endpoint,
                label=request.label,
                state=ConnectionState.NOT_CONNECTED,
                connected_at=None,
                actor_id=request.actor_id,
            )
        ).transition(ConnectionState.AUTHORIZING, at=at, by=request.actor_id)
        # **A reconnection keeps the customer's own name for the relationship**
        # and its recorded `connected_at`. Both are facts about a relationship
        # that persisted through a gap, and the acquisition flow does not ask
        # for a label a second time. **Its `endpoint` is also kept**, which is
        # correct for every shipped system and would not be for one whose host
        # can move between authorizations — Salesforce is the case, and it is
        # not shipped. Noted in 44-integrations.md rather than guessed at here.

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

        # **A ref per grant, never per connection.** A reconnection stores new
        # material for a connection that may still hold the old, and §3's rule
        # is that a rotation *writes a new ref and leaves the old to be purged*
        # rather than editing material in place — which is exactly what makes a
        # rotation diagnosable while it is happening.
        grant_id = uuid4()
        secret_ref = f"integration/{authorizing.id}/{grant_id}"
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
                id=grant_id,
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

"""What a customer needs to know about their connections."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from modules.integrations.application.ports import ConnectedAccountRepository, GrantStore
from modules.integrations.domain.connection import ConnectedAccount, ConnectionState


class Attention(StrEnum):
    """Whether a customer must do something, and how urgently.

    **Derived, never stored** (§2). It is a reading of the connection's state
    and its grant's expiry at the moment of the question; a column would be a
    second representation of a fact that already exists, and it would be wrong
    the minute a grant expired without anybody writing a row.
    """

    #: Working. Nothing to do.
    NONE = "none"
    #: Working, but it will stop without action — a grant expiring soon that
    #: cannot refresh itself.
    SOON = "soon"
    #: Not working. Data is not flowing and only the customer can fix it.
    NOW = "now"


@dataclass(frozen=True, slots=True)
class ConnectionView:
    """One connection, as a customer reads it.

    **Deliberately smaller than the aggregate.** No `secret_ref`, no grant id,
    no `external_account_id` — a screen that showed a Salesforce org id would be
    showing the customer Signora's bookkeeping.
    """

    id: UUID
    integration: str
    label: str
    state: ConnectionState
    connected_at: datetime | None
    attention: Attention
    #: Why action is needed, in a form the edge turns into a sentence. `None`
    #: when nothing is needed. **Not a rendered sentence** — the wording is the
    #: presentation layer's, on the same rule Timeline established.
    reason: str | None


#: How long before an expiry is worth warning about. **A product decision with
#: a number attached**: soon enough that a customer can act, far enough that the
#: warning is not permanent. Deliberately not configurable — a per-workspace
#: knob here would be a setting nobody knows how to answer.
EXPIRY_WARNING = 60 * 60 * 24 * 3


class IntegrationQueries:
    def __init__(self, accounts: ConnectedAccountRepository, grants: GrantStore) -> None:
        self._accounts = accounts
        self._grants = grants

    async def connections(self, workspace_id: UUID, *, at: datetime) -> list[ConnectionView]:
        """Every connection this workspace has, in any state.

        **Including the broken ones, which is the point.** A revoked Salesforce
        is the most important row on this screen, and a list that quietly
        omitted it would leave a customer believing their data was flowing.
        """
        views: list[ConnectionView] = []
        for account in await self._accounts.list_for_workspace(workspace_id):
            grant = await self._grants.current_for(workspace_id, account.id)
            expires_at = grant.expires_at if grant else None
            refreshable = grant.refreshable if grant else False
            views.append(
                ConnectionView(
                    id=account.id,
                    integration=account.integration,
                    label=account.label,
                    state=account.state,
                    connected_at=account.connected_at,
                    attention=_attention(account, expires_at, refreshable, at),
                    reason=_reason(account, expires_at, refreshable, at),
                )
            )
        return views


def _attention(
    account: ConnectedAccount,
    expires_at: datetime | None,
    refreshable: bool,
    at: datetime,
) -> Attention:
    if account.state in {ConnectionState.REVOKED, ConnectionState.EXPIRED}:
        return Attention.NOW
    if account.state is ConnectionState.AUTHORIZING:
        return Attention.NOW
    if not account.is_usable:
        # Not connected or deliberately disconnected: nothing is broken, and
        # nagging about a system the customer chose not to connect is noise.
        return Attention.NONE
    if expires_at is not None and not refreshable:
        if (expires_at - at).total_seconds() <= EXPIRY_WARNING:
            return Attention.SOON
    return Attention.NONE


def _reason(
    account: ConnectedAccount,
    expires_at: datetime | None,
    refreshable: bool,
    at: datetime,
) -> str | None:
    if account.state is ConnectionState.REVOKED:
        return "permission_withdrawn"
    if account.state is ConnectionState.EXPIRED:
        return "credential_expired"
    if account.state is ConnectionState.AUTHORIZING:
        return "authorization_unfinished"
    if (
        account.is_usable
        and expires_at is not None
        and not refreshable
        and (expires_at - at).total_seconds() <= EXPIRY_WARNING
    ):
        return "credential_expiring"
    return None

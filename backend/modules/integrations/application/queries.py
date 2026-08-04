"""What a customer needs to know about their connections."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from modules.integrations.application.ports import ConnectedAccountRepository, GrantStore
from modules.integrations.domain.catalog import CATALOG, Capability, entry_for
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

    @classmethod
    def of(
        cls,
        account: ConnectedAccount,
        *,
        expires_at: datetime | None,
        refreshable: bool,
        at: datetime,
    ) -> ConnectionView:
        """**The one place attention is derived**, and it has two callers.

        Extracted when the connect route needed to answer *did it work?* for a
        connection it had just written. The alternative was deriving attention
        a second time from the same three inputs — and two derivations of one
        fact are two derivations that eventually disagree, which is the defect
        §2 names rather than a style preference.
        """
        return cls(
            id=account.id,
            integration=account.integration,
            label=account.label,
            state=account.state,
            connected_at=account.connected_at,
            attention=_attention(account, expires_at, refreshable, at),
            reason=_reason(account, expires_at, refreshable, at),
        )


@dataclass(frozen=True, slots=True)
class SystemView:
    """One system Signora understands, and what this organization has of it.

    **The Connection Center's unit, and deliberately not "a connection".** The
    question a customer opens this screen with is *"is my CRM connected?"*, not
    *"list my connections"* — and a system with none is the row that most needs
    to appear.
    """

    integration: str
    #: What this system gives Signora **that the platform can act on today**.
    #: A capability waiting on an unbuilt module is absent rather than greyed:
    #: a promise the product cannot keep is worse than a shorter list.
    capabilities: tuple[Capability, ...]
    connectable: bool
    connections: tuple[ConnectionView, ...]

    @property
    def needs_attention(self) -> bool:
        return any(c.attention is not Attention.NONE for c in self.connections)

    @property
    def is_working(self) -> bool:
        """At least one connection Signora can currently use.

        **Not "has a connection"** — a revoked Salesforce is a connection, and
        answering *"is my CRM connected?"* with *yes* would be the screen's
        worst possible lie.
        """
        return any(
            c.state in {ConnectionState.CONNECTED, ConnectionState.VALIDATED}
            for c in self.connections
        )


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
                ConnectionView.of(
                    account, expires_at=expires_at, refreshable=refreshable, at=at
                )
            )
        return views

    async def systems(self, workspace_id: UUID, *, at: datetime) -> list[SystemView]:
        """Every system Signora understands, with what this organization has.

        **Catalog-first rather than connection-first.** A screen built from
        connections can only show what somebody already did; this one also
        answers *"what could we connect, and what would it give us?"* — and it
        keeps a system a customer has never touched visible instead of absent.
        """
        by_integration: dict[str, list[ConnectionView]] = {}
        for view in await self.connections(workspace_id, at=at):
            by_integration.setdefault(view.integration, []).append(view)

        systems = [
            SystemView(
                integration=entry.slug,
                capabilities=entry.live_capabilities,
                connectable=entry.connectable,
                connections=tuple(by_integration.pop(entry.slug, [])),
            )
            for entry in CATALOG.values()
        ]
        # A connection whose catalog entry was withdrawn still belongs to the
        # customer and must not vanish from their screen.
        systems.extend(
            SystemView(
                integration=slug, capabilities=(), connectable=False, connections=tuple(views)
            )
            for slug, views in by_integration.items()
        )
        return systems


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

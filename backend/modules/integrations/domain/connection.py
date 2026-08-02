"""A customer's connection to one of their own systems.

**The distinction this module exists to hold** ([04-modules.md](../../../../docs/architecture/04-modules.md)):
a *provider* is Signora's supplier and Signora holds the credential; an
*integration* is the **customer's own system** and the customer holds it. That
is a business relationship, not a synchronization mechanism, which is why it
lives here and not in Provider Platform.

A Connected Account exists **before** any synchronization, **while** paused,
**after** a grant is revoked, and **even if synchronization never happens at
all.** Nothing about it is a fact about a sync run.

Three properties carry the design:

**A Connected Account is an account, never a person.** Google domain-wide
delegation and Microsoft Graph app-only permissions bind one grant to an entire
organisation; a model that assumed one human would have broken on the second
integration.

**The endpoint is not the credential.** Salesforce returns a per-org
`instance_url` alongside its token. Storing it on the grant would mean rotating
a credential to correct an address.

**Connection state and run state are different lifecycles.** A healthy
connection can have a failed sync, and a revoked grant can have a completed one.
Only the first is something a customer can act on.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ConnectionState(StrEnum):
    """Where a connection is, independently of any synchronization.

    Deliberately **not** modelled with the sync lifecycle
    (`RUNNING`/`COMPLETED`/`FAILED`, owned by Provider Platform). Merging them
    would make *"the customer revoked us in Salesforce"* indistinguishable from
    *"last night's sync timed out"*, and only one of those is a customer's to
    fix.
    """

    #: A catalog entry the customer has not connected. Represented rather than
    #: implied by absence, so a screen can list what *could* be connected.
    NOT_CONNECTED = "not_connected"
    #: Permission has been requested and not yet granted. **Persisted, not
    #: transient** — OAuth device flow leaves a connection here for minutes
    #: while the customer types a code on another device.
    AUTHORIZING = "authorizing"
    #: A grant exists. It has not yet been proven to work.
    CONNECTED = "connected"
    #: A real call succeeded with it. **The state that earns its place**: a
    #: grant that authenticates but lacks a scope is the commonest integration
    #: failure and is indistinguishable from healthy until the first sync.
    VALIDATED = "validated"
    #: The grant's own lifetime ran out. Recoverable by refresh.
    EXPIRED = "expired"
    #: The customer withdrew permission **at the vendor**. Not recoverable by
    #: retry, and retrying is a system doing nothing while a dashboard says it
    #: is fine.
    REVOKED = "revoked"
    #: The customer disconnected it here. Deliberate, and reversible.
    DISCONNECTED = "disconnected"


#: States in which asking the vendor for anything is pointless. Named once so a
#: caller cannot assemble its own list and quietly disagree with this one.
UNUSABLE_STATES: frozenset[ConnectionState] = frozenset(
    {
        ConnectionState.NOT_CONNECTED,
        ConnectionState.AUTHORIZING,
        ConnectionState.EXPIRED,
        ConnectionState.REVOKED,
        ConnectionState.DISCONNECTED,
    }
)


class ConnectionTransitionError(RuntimeError):
    """A transition the connection's state does not permit."""


#: The transitions a connection may make. A table rather than a chain of `if`s:
#: adding a state is a row, and an illegal transition is refused by construction
#: rather than by whichever branch happened to be written.
_ALLOWED: dict[ConnectionState, frozenset[ConnectionState]] = {
    ConnectionState.NOT_CONNECTED: frozenset({ConnectionState.AUTHORIZING}),
    # `DISCONNECTED` included because a customer who abandoned a half-finished
    # connection must be able to remove it. Without it the Connection Center
    # shows a row reading *Not finished* that nothing can clear — found by a
    # disconnect test rather than by reading this table.
    ConnectionState.AUTHORIZING: frozenset(
        {
            ConnectionState.CONNECTED,
            ConnectionState.NOT_CONNECTED,
            ConnectionState.DISCONNECTED,
        }
    ),
    ConnectionState.CONNECTED: frozenset(
        {
            ConnectionState.VALIDATED,
            ConnectionState.EXPIRED,
            ConnectionState.REVOKED,
            ConnectionState.DISCONNECTED,
        }
    ),
    ConnectionState.VALIDATED: frozenset(
        {ConnectionState.EXPIRED, ConnectionState.REVOKED, ConnectionState.DISCONNECTED}
    ),
    # A refresh recovers an expired connection; a revocation can be discovered
    # while it is expired, and the customer can give up on it.
    ConnectionState.EXPIRED: frozenset(
        {
            ConnectionState.CONNECTED,
            ConnectionState.REVOKED,
            ConnectionState.DISCONNECTED,
        }
    ),
    # Terminal until the customer authorizes again, which starts at the top.
    ConnectionState.REVOKED: frozenset({ConnectionState.AUTHORIZING}),
    ConnectionState.DISCONNECTED: frozenset({ConnectionState.AUTHORIZING}),
}


@dataclass(frozen=True, slots=True)
class ConnectedAccount:
    """One customer's account in one external system.

    An org, a domain, a mailbox, a calendar — **whatever identity the vendor
    lets Signora synchronize against.** The vendor decides how many humans that
    covers, and this model deliberately does not ask.
    """

    id: UUID
    workspace_id: UUID
    #: The catalog entry this connects to. **An opaque slug, never an enum** —
    #: a closed enum cannot admit a partner-published or customer-written
    #: connector, and that is the assumption a marketplace would break first.
    integration: str
    #: The vendor's own identifier for the account: an org id, a domain, an
    #: address. Opaque here; only the adapter interprets it.
    external_account_id: str
    #: Where to reach this account, when the vendor is not one fixed host —
    #: Salesforce's per-org `instance_url`, a self-hosted base URL.
    #: **Address, never secret.**
    endpoint: str | None
    #: What the customer calls it. Shown back to them so *"which Salesforce?"*
    #: has an answer when a workspace connects two.
    label: str
    state: ConnectionState
    connected_at: datetime | None

    def __post_init__(self) -> None:
        if not self.integration:
            raise ValueError("integration must name a catalog entry")
        if not self.external_account_id:
            raise ValueError("external_account_id must identify the account")

    @property
    def is_usable(self) -> bool:
        """Whether asking the vendor for anything could succeed."""
        return self.state not in UNUSABLE_STATES

    def transition(self, to: ConnectionState, *, at: datetime) -> ConnectedAccount:
        """Move to `to`, refusing a transition the lifecycle does not allow.

        **Returns a new account rather than mutating.** The state of a
        connection is a fact about a moment, and a caller holding the previous
        value should keep holding what it read.
        """
        if to not in _ALLOWED[self.state]:
            raise ConnectionTransitionError(
                f"a connection cannot move from {self.state.value} to {to.value}"
            )
        connected_at = self.connected_at
        if to is ConnectionState.CONNECTED and connected_at is None:
            connected_at = at
        return ConnectedAccount(
            id=self.id,
            workspace_id=self.workspace_id,
            integration=self.integration,
            external_account_id=self.external_account_id,
            endpoint=self.endpoint,
            label=self.label,
            state=to,
            connected_at=connected_at,
        )

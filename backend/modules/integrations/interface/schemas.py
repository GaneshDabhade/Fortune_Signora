"""Response shapes for the connections surface.

Purpose-built, never a domain entity (§7). Nothing here exposes a
`secret_ref`, a grant id or a vendor's internal account id — a screen showing a
Salesforce org id is showing the customer Signora's bookkeeping.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SecretStr

from modules.integrations.application.connect import ConnectInput
from modules.integrations.application.disconnect import DisconnectResult
from modules.integrations.application.queries import ConnectionView, SystemView
from modules.integrations.domain.grant import Credential


class ConnectionResponse(BaseModel):
    """One connection, as a customer reads it."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    integration: str = Field(
        description=(
            "Which system this connects to, as a stable slug. Clients map it to "
            "a name and an icon; the API deliberately sends neither."
        )
    )
    label: str = Field(description="What the customer called this connection.")
    state: str = Field(
        description=(
            "Where the connection is, independently of any synchronization. A "
            "sync can fail while this is healthy, and vice versa."
        )
    )
    connected_at: datetime | None = Field(
        description="When it was first connected, never when it last refreshed."
    )
    attention: str = Field(
        description=(
            "Whether the customer must act: none, soon, or now. Derived at read "
            "time from the connection and its grant — never stored."
        )
    )
    reason: str | None = Field(
        default=None,
        description=(
            "Why action is needed, as a stable code. Clients turn it into a "
            "sentence; the API sends no prose."
        ),
    )
    health: str = Field(
        description=(
            "What happened when Signora last actually tried to use this "
            "connection: healthy, degraded, or unknown. Distinct from `state`, "
            "and the distinction is the point — `state` says what the records "
            "imply, and a credential that lost a permission is in a perfect "
            "state and does not work. `unknown` means nothing has been tried "
            "yet; it does not mean working."
        )
    )

    @classmethod
    def from_domain(cls, view: ConnectionView) -> ConnectionResponse:
        return cls(
            id=view.id,
            integration=view.integration,
            label=view.label,
            state=view.state.value,
            connected_at=view.connected_at,
            attention=view.attention.value,
            reason=view.reason,
            health=view.health.value,
        )


class SystemResponse(BaseModel):
    """One system, and what this organization has of it."""

    model_config = ConfigDict(frozen=True)

    integration: str = Field(
        description="Stable slug. Clients supply the name and the icon."
    )
    capabilities: list[str] = Field(
        description=(
            "What connecting this gives Signora, limited to what the platform "
            "can act on today. A capability waiting on unbuilt work is absent "
            "rather than listed as unavailable — the product does not advertise "
            "what it cannot do."
        )
    )
    connectable: bool = Field(
        description="Whether it can be connected right now."
    )
    working: bool = Field(
        description=(
            "Whether at least one connection is usable. Not the same as having "
            "a connection: a revoked one is a connection."
        )
    )
    needs_attention: bool = Field(
        description="Whether any connection needs the customer to act."
    )
    connections: list[ConnectionResponse]

    @classmethod
    def from_domain(cls, view: SystemView) -> SystemResponse:
        return cls(
            integration=view.integration,
            capabilities=[c.value for c in view.capabilities],
            connectable=view.connectable,
            working=view.is_working,
            needs_attention=view.needs_attention,
            connections=[ConnectionResponse.from_domain(c) for c in view.connections],
        )


class DisconnectResponse(BaseModel):
    """What happened when a customer disconnected a system."""

    model_config = ConfigDict(frozen=True)

    state: str = Field(description="Where the connection is now.")
    revoked_at_provider: bool = Field(
        description=(
            "Whether the other system was told. When false, Signora has stopped "
            "reading and the customer may still want to remove Signora on that "
            "system's side — which the screen says rather than implying."
        )
    )
    already_disconnected: bool = Field(
        description="Whether it was already disconnected. Not an error."
    )

    @classmethod
    def from_domain(cls, result: DisconnectResult) -> DisconnectResponse:
        return cls(
            state=result.account.state.value,
            revoked_at_provider=result.revoked_at_provider,
            already_disconnected=result.already_disconnected,
        )


class CredentialRequest(BaseModel):
    """Secret material arriving from the acquisition edge.

    **`SecretStr`, so nothing renders it by accident.** A request model ends up
    in a traceback, a debugger, a structured log line and a pytest diff, and a
    bearer token in any of those is a bearer token in a log aggregator — the
    same reasoning that makes the domain's `Credential` refuse its own `repr`.

    **The platform's validation handler never echoes input** — it reports the
    field path and the message and nothing else — so a malformed request cannot
    return material to its sender either. That property is load-bearing here
    and is the reason this endpoint can take a credential in a body at all.

    **Text material only, and stated rather than assumed.** A bearer token and
    a refresh token are text; a client certificate is not, and expressing one
    would need an encoding this model deliberately does not invent (§6). The
    day mTLS arrives, that is the field to add.
    """

    model_config = ConfigDict(frozen=True)

    kind: str = Field(
        min_length=1,
        max_length=64,
        description=(
            "What kind of material this is, so a client factory knows what to "
            "build. Nothing branches on it above the factory."
        ),
    )
    material: SecretStr = Field(description="The material itself. Never returned, never logged.")


class ConnectRequest(BaseModel):
    """What the acquisition edge hands over once a customer has consented.

    **Nothing here names OAuth.** An API key, a service account or a
    certificate arrives through the same door — the property `ConnectInput`
    was designed for, preserved at the wire.

    **The workspace is not in the body.** It is in the path and re-verified
    against membership before this is read, so a caller cannot connect a system
    into an organization they merely named (§7).
    """

    model_config = ConfigDict(frozen=True)

    integration: str = Field(
        min_length=1,
        max_length=64,
        description=(
            "The catalog slug. A slug Signora does not understand is refused — "
            "storing a connection nothing can act on would put a permanent row "
            "on a customer's screen."
        ),
    )
    external_account_id: str = Field(
        min_length=1,
        max_length=255,
        description="The vendor's identifier for the account that granted access.",
    )
    label: str = Field(
        min_length=1,
        max_length=255,
        description="What the customer will see. Their words, not the vendor's identifier.",
    )
    endpoint: str | None = Field(
        default=None,
        max_length=512,
        description=(
            "Where to reach this account, when the vendor is not one fixed host. "
            "Salesforce returns one; HubSpot does not. **On the connection and "
            "never on the grant** — an address that lived on the credential "
            "would make correcting it a rotation."
        ),
    )
    credential: CredentialRequest
    scopes: tuple[str, ...] = Field(
        default=(),
        description=(
            "What the customer actually permitted, so a later refusal can say "
            "*which permission is missing* rather than *something went wrong*."
        ),
    )
    expires_at: datetime | None = Field(
        default=None,
        description="When the grant stops working. Absent for material that does not expire.",
    )
    refreshable: bool = Field(
        default=False,
        description=(
            "Whether this can be renewed without the customer. **A property, not "
            "a special case** — an API key is simply a grant that is neither."
        ),
    )

    def to_input(self, *, workspace_id: UUID, actor_id: UUID) -> ConnectInput:
        return ConnectInput(
            workspace_id=workspace_id,
            actor_id=actor_id,
            integration=self.integration,
            external_account_id=self.external_account_id,
            label=self.label,
            endpoint=self.endpoint,
            credential=Credential(
                kind=self.credential.kind,
                material=self.credential.material.get_secret_value().encode("utf-8"),
            ),
            scopes=self.scopes,
            expires_at=self.expires_at,
            refreshable=self.refreshable,
        )

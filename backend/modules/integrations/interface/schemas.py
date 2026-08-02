"""Response shapes for the connections surface.

Purpose-built, never a domain entity (§7). Nothing here exposes a
`secret_ref`, a grant id or a vendor's internal account id — a screen showing a
Salesforce org id is showing the customer Signora's bookkeeping.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from modules.integrations.application.queries import ConnectionView, SystemView


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

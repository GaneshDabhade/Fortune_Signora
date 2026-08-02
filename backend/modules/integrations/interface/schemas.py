"""Response shapes for the connections surface.

Purpose-built, never a domain entity (§7). Nothing here exposes a
`secret_ref`, a grant id or a vendor's internal account id — a screen showing a
Salesforce org id is showing the customer Signora's bookkeeping.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from modules.integrations.application.queries import ConnectionView


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

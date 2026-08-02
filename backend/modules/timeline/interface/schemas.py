"""Response shapes for the timeline feed.

**Purpose-built, never a domain entity or a SQLAlchemy model** (§7). The wire
shape is a contract with the frontend and the domain is free to change without
breaking it.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from modules.timeline.domain.entry import TimelineEntry


class TimelineEntryResponse(BaseModel):
    """One thing that happened, with no opinion about what it means.

    **No rendered sentence, deliberately.** The entry carries structured facts
    and the frontend edge says them in the customer's words — which is where
    [ADR-0034](../../../../docs/architecture/adr/0034-ubiquitous-language.md)
    puts the translation, and it never travels inward. A `summary` field here
    would freeze one phrasing into an immutable record and into every client
    that reads it.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID
    kind: str = Field(
        description=(
            "What happened, as the owning module named it. Clients map this to "
            "customer-facing wording; the API deliberately does not."
        )
    )
    occurred_at: datetime = Field(
        description=(
            "When the thing happened in the domain — never when Signora "
            "processed it. Detection can lag occurrence by days."
        )
    )
    source_module: str = Field(
        description="Which module owns the fact, and therefore its meaning."
    )
    source_ref: UUID = Field(
        description=(
            "The row upstream this entry points back to. Timeline holds no "
            "interpretation; this is where the explanation lives."
        )
    )
    detail: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "The few fields needed to read the row without a second request. "
            "A bounded allow-list per kind, not the upstream payload."
        ),
    )

    @classmethod
    def from_domain(cls, entry: TimelineEntry) -> TimelineEntryResponse:
        return cls(
            id=entry.id,
            kind=entry.kind.value,
            occurred_at=entry.occurred_at,
            source_module=entry.source_module,
            source_ref=entry.source_ref,
            detail=dict(entry.detail),
        )

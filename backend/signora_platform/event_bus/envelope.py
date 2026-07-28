"""The standard event envelope every domain event is serialized into.

Mirrors the envelope contract in docs/architecture/06-events.md exactly.
This is the wire/storage format; module-internal domain events (e.g.
``modules.workspace_tenancy.domain.events.WorkspaceCreated``) are a distinct,
richer, module-owned representation that gets *converted* to this envelope
by the module's ``EventPublisher`` call — the envelope never leaks back into
domain code.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EventEnvelope(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: UUID
    event_type: str
    event_version: int
    workspace_id: UUID
    occurred_at: datetime
    producer_module: str
    correlation_id: UUID
    causation_id: UUID | None
    payload: dict[str, Any]

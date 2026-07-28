"""Domain events raised by this module's aggregates.

``DomainEvent`` is intentionally module-local rather than a shared base
imported from ``signora_platform/`` — with only one module in existence, promoting
it to a shared kernel now would be a speculative abstraction for a single
consumer (CLAUDE.md's anti-pattern list). Promote it the moment a second
module needs an identical base, not before.

These are plain dataclasses, not Pydantic models: they are internal domain
objects with behavior-free data and no serialization concerns of their own.
Serialization into the wire-format ``EventEnvelope`` happens at the
publisher boundary (signora_platform/event_bus), never here.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, ClassVar
from uuid import UUID, uuid4


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    event_type: ClassVar[str]
    event_version: ClassVar[int] = 1

    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    workspace_id: UUID
    causation_id: UUID | None = None

    def to_payload(self) -> dict[str, Any]:
        raise NotImplementedError


@dataclass(frozen=True, kw_only=True)
class WorkspaceCreated(DomainEvent):
    event_type: ClassVar[str] = "workspace.created"

    name: str
    created_by: UUID

    def to_payload(self) -> dict[str, Any]:
        return {
            "workspace_id": str(self.workspace_id),
            "name": self.name,
            "created_by": str(self.created_by),
        }


@dataclass(frozen=True, kw_only=True)
class MemberAdded(DomainEvent):
    event_type: ClassVar[str] = "workspace.member_added"

    user_id: UUID
    role: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "workspace_id": str(self.workspace_id),
            "user_id": str(self.user_id),
            "role": self.role,
        }

"""The raw-record read contract.

`provider.record.received` carries the record's *identity*, not its body —
a consumer that needs the payload reads it through this port rather than
through Provider Platform's tables or SQLAlchemy models. That is the
difference between a module boundary and a naming convention.

The port is a Protocol; its one implementation lives in this module's
`infrastructure/`, and the composition root injects it. A consumer never
imports the implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RawRecordView:
    """One raw provider record, as other modules may see it.

    A frozen view rather than the ORM model: an ORM instance carries a
    session, lazy loaders, and a write path, all of which would let a
    consumer mutate another module's table by accident.
    """

    id: UUID
    workspace_id: UUID
    provider: str
    capability: str
    external_id: str
    occurred_at: datetime
    payload: dict[str, Any]


class RawRecordReader(Protocol):
    async def by_id(self, raw_record_id: UUID) -> RawRecordView | None:
        """The record, or None when it is not visible in the current tenant
        scope. Absence is a legitimate answer, not an error: a record from
        another workspace is invisible under RLS, and retrying will not
        make it appear."""
        ...

"""What the Action Batch's endpoints put on the wire.

**Purpose-built response shapes, never the aggregate** (§7, 19-api-conventions).
The domain object carries transitions, a reversible window and guards a caller
has no business seeing; what a screen needs is *what is this, and how far has it
got*.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from modules.action_batch.domain.batch import ActionBatch, ApplicationProgress


class ActionBatchProgressResponse(BaseModel):
    """A batch, and how far the work has got.

    🔴 **`progress` is the field this row exists for** —
    [TASK-465](../../../../docs/BACKLOG.md). ⛔ **`accepted` is not `applied`**,
    and a screen that renders them alike is the row's own named risk: *a
    customer told applied before the work finishes.*
    """

    model_config = ConfigDict(frozen=True)

    id: UUID
    name: str
    item_count: int
    #: 📁 The customer-facing lifecycle — proposed · approved · withdrawn ·
    #: reversed · rejected.
    state: str
    #: ⚡ **How far the WORK has got**, which is a different question from the
    #: decision above.
    progress: ApplicationProgress
    #: ⛔ **When the application was ACCEPTED**, not when it ran. `null` until
    #: somebody asks for it.
    accepted_at: datetime | None
    #: When it took effect. `null` while it has not.
    applied_at: datetime | None
    #: ⛔ **Why it did not run.** 📁 **Present exactly when `progress` is
    #: `failed`** — [P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md): a
    #: failure a customer can see and nobody can act on is worse than a spinner.
    failure_reason: str | None

    @classmethod
    def from_domain(cls, batch: ActionBatch) -> ActionBatchProgressResponse:
        return cls(
            id=batch.id,
            name=batch.name,
            item_count=batch.item_count,
            state=batch.state.value,
            progress=batch.progress,
            accepted_at=batch.dispatched_at,
            applied_at=batch.applied_at,
            failure_reason=batch.failure.reason if batch.failure is not None else None,
        )

"""What the Action Batch tells the rest of Signora.

**Two events, and the pair is deliberate.** A batch has many transitions —
proposed, approved, rejected, withdrawn, applied, reversed — and only two of
them change anything outside this module: **the moment it took effect, and the
moment it was taken back.** The rest are decisions about whether it will, and a
decision nobody downstream acts on is not an integration event (§9).

⛔ **No `action_batch.approved`.** Approval is permission to apply, not the
application: a subscriber acting on it would act before the work happened, and
the gap between the two moments is real — `APPROVED` with no `applied_at` is a
state this domain models on purpose.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Final
from uuid import UUID

EVENT_VERSION: Final = 1


@dataclass(frozen=True, slots=True)
class ActionBatchApplied:
    """A named unit of work took effect.

    **The first moment anything outside this module should react to.** The
    timeline records it, and whoever proposed the items can consider them done.
    """

    event_id: UUID
    workspace_id: UUID
    occurred_at: datetime
    batch_id: UUID
    #: What the customer called it. **Their words**, so a history reads as a
    #: record of decisions rather than a list of identifiers.
    name: str
    #: How many things it covered. **A count, never the payload** — what each
    #: item means belongs to the domain that proposed it.
    item_count: int
    #: Who approved it. ⛔ **Never optional**: *intelligence suggests; humans
    #: commit*, and an application whose approver is unattributed is one nobody
    #: can cite.
    approved_by: UUID
    #: Until when it can be taken back. `None` means **reversal was never
    #: offered**, which is not the same as a window that has closed — and a
    #: subscriber is told the two differently.
    reversible_until: datetime | None


@dataclass(frozen=True, slots=True)
class ActionBatchReversed:
    """A named unit of work was taken back.

    ⚠️ **Not a correction of the applied event, and never its retraction.**
    Both happened, in that order, and a subscriber that dropped the first on
    seeing the second would lose the fact that the work was live in between —
    which is exactly the interval a customer asks about.
    """

    event_id: UUID
    workspace_id: UUID
    occurred_at: datetime
    batch_id: UUID
    #: The application this reverses. **Stated rather than inferred** from
    #: ordering, because a subscriber may see them out of order.
    applied_at: datetime
    reversed_by: UUID

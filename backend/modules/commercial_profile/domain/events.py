"""Domain events published by the Commercial Profile.

**The module's first, and for a long time its only.** Four declarations
shipped without one, because nothing downstream consumed them; this one exists
because Provider Platform has waited since M2.1 for a subject to synchronize.

Cataloged in `docs/architecture/06-events.md` — see the note in
[40-commercial-profile.md](../../../../docs/architecture/40-commercial-profile.md)
about who may write that file.

### The payload is one integer, and that is the contract

[ADR-0036](../../../../docs/architecture/adr/0036-target-account-contract.md)
§3: **`workspace_id` on the envelope, `declaration_version` in the payload,
nothing about accounts.** The list itself is read through
`TargetAccountReader`, and the reasons are worth knowing rather than
rediscovering:

- **Embedding names would put a copy of an aggregate's truth on a bus**, where
  it can be stale, replayed and contradicted by the aggregate it copies.
- **Every future field would become an event-contract change.** A port can
  grow a field; a published event cannot, cheaply.
- **The version is here for ordering, not replay.** Idempotency on `event_id`
  handles redelivery; it does not order two workspace-level events against
  each other, and a consumer acting on v5 after v6 would sync a list one
  revision stale. A consumer compares this integer with what it last acted on
  and ignores the older — a decision it can make locally, with no coordination.

**What must never appear here:** a resolved company, a provider name, a
synchronization decision, a schedule, a delta, or anything canonical. Each
belongs to a module downstream of this one, and an event is the easiest place
in a system to smuggle one.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Final
from uuid import UUID

EVENT_VERSION: Final = 1

EVENT_TYPE: Final = "commercial_profile.target_accounts_changed"


@dataclass(frozen=True, slots=True)
class TargetAccountsChanged:
    """A workspace has restated which companies it wants watched.

    **Announced on every accepted declaration**, including one that removes
    the last account and one whose content happens to match the previous
    version. This module records that the customer said something; deciding
    that a restatement changes nothing worth acting on requires knowing what
    has already been synchronized, which is a fact Provider Platform holds and
    this module does not.
    """

    event_id: UUID
    workspace_id: UUID
    occurred_at: datetime
    #: The version now in force. The whole payload, and the reason is ordering
    #: rather than replay — see the module docstring.
    declaration_version: int
    causation_id: UUID | None = None
    event_type: str = EVENT_TYPE
    event_version: int = EVENT_VERSION

    def to_payload(self) -> dict[str, Any]:
        return {"declaration_version": self.declaration_version}

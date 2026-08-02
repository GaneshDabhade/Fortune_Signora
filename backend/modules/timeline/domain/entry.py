"""The Timeline Entry — one thing that happened, in time order.

**Timeline records that something happened, in the words the module that owned
it used, and never decides what any of it means** ([ADR-0038](../../../../docs/architecture/adr/0038-timeline.md)).
Every module upstream has already made its judgement — an observation was
recorded, a signal was found relevant, a score moved, an opportunity opened.
This restates those facts chronologically and adds no opinion.

Four properties carry the design:

**Identity is derived from the event, not allocated.** Two deliveries of one
event produce the same entry id, so redelivery is a primary-key conflict rather
than a code path. At-least-once delivery makes that the difference between a
feed and a feed with duplicates in it.

**Ordering is by the domain's `occurred_at`, never by arrival.** Arrival order
is a fact about the bus, not about the account, and a feed ordered by it tells a
seller that something from March happened after something from June.

**The entry holds no fact whose source of truth is not upstream.** It stores the
kind, when it happened, and a reference back to the row that owns it. Anything
richer would be a copy that can go stale and can never be corrected, because
entries are immutable.

**No rendered prose is stored.** See `EntryDetail` below — this is a deliberate
departure from ADR-0038's draft, recorded there.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, Final
from uuid import UUID, uuid5

TIMELINE_NAMESPACE: Final = UUID("7f3c1d92-4b8e-5a06-9c17-2e5d8a4b6f31")
"""Fixed namespace for deterministic entry ids. **Never change it** — every
entry in every workspace would acquire a new identity, and the next projection
run would insert a duplicate of the entire table."""


class EntryKind(StrEnum):
    """What kind of thing happened, named as the owning module named it.

    **These are engineering's words on purpose.** [ADR-0034](../../../../docs/architecture/adr/0034-ubiquitous-language.md)
    puts the customer's vocabulary at the frontend edge and keeps it from
    travelling inward, so the column stays precise and the screen says what a
    salesperson would say. This module is where that rule is easiest to break,
    because its content is literally a list of other modules' internal
    milestones — a feed reading *"observation.recorded — employee_count"* is the
    pipeline talking to itself in front of a customer.
    """

    OBSERVATION_RECORDED = "observation_recorded"
    OBSERVATION_SUPERSEDED = "observation_superseded"
    BUSINESS_EVENT_DETECTED = "business_event_detected"
    BUSINESS_EVENT_SUPERSEDED = "business_event_superseded"
    SIGNAL_GENERATED = "signal_generated"
    SIGNAL_SUPERSEDED = "signal_superseded"
    BUYING_SCORE_UPDATED = "buying_score_updated"
    OPPORTUNITY_CREATED = "opportunity_created"
    OPPORTUNITY_STAGE_CHANGED = "opportunity_stage_changed"


EntryDetail = Mapping[str, Any]
"""The structured facts an entry carries, and **never a rendered sentence.**

ADR-0038's draft said the entry carries *"a short customer-facing summary
line"*. Implementation says it must not, for two reasons that only became
obvious with the immutability rule in front of it:

**A stored sentence is a copy of the phrasing catalog that can never be
corrected.** Entries are immutable, so improving one word of customer-facing
copy would mean a new row for every entry ever written, or an edit the grant
does not permit. The phrasing is *static knowledge a domain expert owns* — the
least-powerful-author rule (`CLAUDE.md` §2) — and it belongs in a reviewed
catalog read at render time, exactly like the Signal Catalog's titles.

**It would put the customer's vocabulary inside the database**, which ADR-0034
forbids in the same sentence that says the translation lives at the frontend
edge and never travels inward.

So an entry stores what happened in structured form and the edge decides how to
say it. Recorded as an amendment on ADR-0038 rather than applied quietly.
"""


@dataclass(frozen=True, slots=True)
class TimelineEntry:
    """One entry in one workspace's feed. Immutable, like the facts it cites."""

    id: UUID
    workspace_id: UUID
    entity_id: UUID
    kind: EntryKind
    occurred_at: datetime
    event_id: UUID
    source_module: str
    source_ref: UUID
    detail: EntryDetail

    def __post_init__(self) -> None:
        # A naive datetime here would order a feed wrongly and silently: two
        # entries an hour apart in different zones compare as though they were
        # not. Every event envelope carries an aware `occurred_at`, so a naive
        # one means something has already been lost.
        if self.occurred_at.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware")
        if not self.source_module:
            raise ValueError("source_module must name the module that owns the fact")

    @classmethod
    def project(
        cls,
        *,
        workspace_id: UUID,
        entity_id: UUID,
        kind: EntryKind,
        occurred_at: datetime,
        event_id: UUID,
        source_module: str,
        source_ref: UUID,
        detail: EntryDetail | None = None,
    ) -> TimelineEntry:
        """Build the entry one event projects to.

        **The only constructor.** `id` is derived rather than accepted, so no
        caller can allocate one — which is what makes redelivery a primary-key
        conflict rather than a duplicate row somebody has to notice.
        """
        return cls(
            id=uuid5(TIMELINE_NAMESPACE, str(event_id)),
            workspace_id=workspace_id,
            entity_id=entity_id,
            kind=kind,
            occurred_at=occurred_at,
            event_id=event_id,
            source_module=source_module,
            source_ref=source_ref,
            detail=dict(detail or {}),
        )

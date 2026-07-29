"""Detection strategies — how a hypothesis is grounded in evidence.

The catalog declares *what kind* of evidence supports a type; this module
implements the two strategies that describes. Keeping them apart means an
improved implementation never changes what a signal **means**, which is the
same separation the business event taxonomy makes and for the same reason.

**No threshold lives here.** Windows, minimum contributor counts, and
relevance all come from the catalog or the workspace profile. A Security
Invariant parses this module as a syntax tree and fails on any numeric
literal in a comparison other than `0` or `1` — those two are structural
(*nothing* and *something*); anything else is a claim about the world
somebody must be able to argue with.

Strategies are pure: business events and configuration in, groundings out.
No I/O, no clock, so the same evidence yields the same hypothesis on every
machine and in any processing order.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from modules.business_event_engine.public import BusinessEvent, BusinessEventType
from modules.signal_engine.domain.catalog import DetectionStrategy, SignalTypeDefinition
from modules.signal_engine.domain.profile import ProfileEntry


@dataclass(frozen=True, slots=True)
class Grounding:
    """Evidence that supports a hypothesis, before it becomes a stored signal.

    Deliberately not a `Signal`: the strategy decides *what the evidence
    supports*, while identity, versioning, relevance, and supersession are
    the use case's concern. Keeping them apart is what lets a strategy be
    tested with no database and no clock.
    """

    events: tuple[BusinessEvent, ...]

    @property
    def occurred_at(self) -> datetime:
        return max(event.occurred_at for event in self.events)

    @property
    def window_start(self) -> datetime:
        return min(event.window_start for event in self.events)

    @property
    def window_end(self) -> datetime:
        return max(event.window_end for event in self.events)

    @property
    def event_types(self) -> tuple[BusinessEventType, ...]:
        return tuple(sorted({event.type_key for event in self.events}, key=lambda t: t.value))


def ground(
    events: Sequence[BusinessEvent],
    definition: SignalTypeDefinition,
    entry: ProfileEntry,
) -> tuple[Grounding, ...]:
    """Everything in this evidence that supports this hypothesis."""
    relevant = tuple(
        event for event in events if event.type_key in definition.contributing_event_types
    )
    if not relevant:
        return ()

    if definition.detection_strategy is DetectionStrategy.SINGLE_EVENT:
        return _single(relevant)
    return _composite(relevant, definition, entry)


def _single(events: tuple[BusinessEvent, ...]) -> tuple[Grounding, ...]:
    """One contributing event is grounds enough, and each stands alone.

    A company that retired two systems has two displacement openings, not
    one — merging them would hide the second.
    """
    return tuple(
        Grounding(events=(event,))
        for event in sorted(events, key=lambda e: (e.occurred_at, str(e.id)))
    )


def _composite(
    events: tuple[BusinessEvent, ...],
    definition: SignalTypeDefinition,
    entry: ProfileEntry,
) -> tuple[Grounding, ...]:
    """Several **distinct** contributing types within a window.

    Distinct *types*, deliberately: three hiring surges are one phenomenon
    reported repeatedly, not three independent grounds for believing a
    company is expanding.

    The window is anchored on the most recent contributing event rather
    than on wall-clock now, so a replay of historical evidence reaches the
    conclusion it would have reached at the time. A window measured against
    *now* would make every rebuild produce different signals as time
    passed.
    """
    window_days = entry.window_days if entry.window_days is not None else definition.window_days
    minimum = (
        entry.minimum_contributors
        if entry.minimum_contributors is not None
        else definition.minimum_contributors
    )

    ordered = sorted(events, key=lambda e: (e.occurred_at, str(e.id)))
    cutoff = ordered[-1].occurred_at - timedelta(days=window_days)
    within = tuple(event for event in ordered if event.occurred_at >= cutoff)

    distinct_types = {event.type_key for event in within}
    if len(distinct_types) < minimum:
        return ()

    # One grounding covering the whole window: a composite hypothesis is
    # about the *pattern*, and splitting it per event would restate the
    # constituent signals that already exist independently.
    return (Grounding(events=within),)

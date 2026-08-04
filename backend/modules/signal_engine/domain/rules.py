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
from typing import Final

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
    *,
    declared: frozenset[str] = frozenset(),
) -> tuple[Grounding, ...]:
    """Everything in this evidence that supports this hypothesis.

    `declared` is what the customer said, folded to compare — the competitor
    names for a `DECLARED_MATCH` type, and empty for every other strategy,
    which ignores it. **Passed in rather than read**, on the same terms as the
    profile: this module performs no I/O, so the same evidence and the same
    declaration yield the same hypothesis on every machine.
    """
    relevant = tuple(
        event for event in events if event.type_key in definition.contributing_event_types
    )
    if not relevant:
        return ()

    if definition.detection_strategy is DetectionStrategy.SINGLE_EVENT:
        return _single(relevant)
    if definition.detection_strategy is DetectionStrategy.DECLARED_MATCH:
        return _declared_match(relevant, declared)
    return _composite(relevant, definition, entry)


#: Where a point rule records the thing it saw. `TechnologyAdopted` writes
#: `{"technology": …, "category": …}`, and the name is the only part a
#: declaration can be compared against.
_SUBJECT: Final = "technology"


def fold(name: str) -> str:
    """How a declared name and an observed one are compared.

    **Case and surrounding space only.** Nothing here resolves *Salesforce*,
    *salesforce.com* and *SFDC* to one thing — that is the Knowledge Graph's
    work, and a cleverer comparison in this module would be a second resolver
    quietly disagreeing with the first. A customer who types a name the
    provider does not report gets no signal, and the catalog says so out loud
    in its limitations.

    Exported because the boundary is only kept if both sides fold identically.
    """
    return name.strip().casefold()


def _declared_match(
    events: tuple[BusinessEvent, ...], declared: frozenset[str]
) -> tuple[Grounding, ...]:
    """One contributing event naming something the customer declared.

    **An empty declaration grounds nothing, and that is the correct answer
    rather than a missing one.** A customer who has named no rivals has said
    that adopting anything is not a competitive event for them; a customer who
    has never been asked has said nothing at all. Both reach here as an empty
    set, and both mean *no grounds* — the difference between them matters to
    the surface that asks, not to the rule that grounds.

    Each match stands alone, as in `_single`: two rivals arriving in one
    account are two events worth reading, and merging them would hide the
    second.
    """
    if not declared:
        return ()
    return tuple(
        Grounding(events=(event,))
        for event in sorted(events, key=lambda e: (e.occurred_at, str(e.id)))
        if fold(str(event.facts.get(_SUBJECT, ""))) in declared
    )


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

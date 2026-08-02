"""The Signal Engine's read surface.

Built around the four questions every signal must be able to answer:

1. **Why does this hypothesis exist?** — the rationale, in two halves
2. **Which business events produced it?** — cited, with their summaries
3. **Which workspace profile interpreted it?** — the version, and the entry
4. **How long should this interpretation remain relevant?** — a date

**Deliberately absent: any ranked list, top-N, or score.** All three are
the Buying Score Engine's question. A convenience method here would put
propensity behind an innocuous call, and within a year every consumer would
use it instead of forming its own view.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from modules.business_event_engine.public import BusinessEvent, BusinessEventQueries
from modules.signal_engine.application.ports import ProfileRepository, SignalRepository
from modules.signal_engine.domain.catalog import SignalCatalog, SignalType, SignalTypeDefinition
from modules.signal_engine.domain.profile import (
    ProfileEntry,
    SignalProfile,
    default_profile,
    resolve_entry,
)
from modules.signal_engine.domain.rules import ground
from modules.signal_engine.domain.signal import Signal


@dataclass(frozen=True, slots=True)
class SignalExplanation:
    """Everything needed to understand — or challenge — one hypothesis.

    Both halves are separately challengeable, and that is the point: *"we
    don't actually care about that"* is a different objection from *"that
    didn't happen"*, and only one of them is Signora's mistake.
    """

    signal: Signal
    definition: SignalTypeDefinition
    #: Why it matters *here* — the workspace's own reading.
    profile_entry: ProfileEntry
    profile_version: int
    #: What it rests on, with the sentences a customer already reads
    #: elsewhere in the product.
    business_events: tuple[BusinessEvent, ...]
    #: Signals this one enriches. Never replaced, always independently
    #: readable.
    constituents: tuple[Signal, ...]


@dataclass(frozen=True, slots=True)
class UnsupportedReading:
    """A hypothesis this evidence was tested against and did not support.

    **Rejected readings are derived, never stored** (ADR-0030, Decision 7,
    ruled 2026-07-30). Recording every non-result would write a row per
    (entity, type) on every run — a large table describing mostly nothing —
    so the question is answered on demand from evidence this module already
    holds, using the rules it already owns.

    Its value is honesty about what was *considered*. A conclusion is easier
    to trust when a reader can see the alternatives the system tested and set
    aside, and easier to debug when they can see the one it never tested.
    """

    signal_type: SignalType
    #: Why the rules declined it, in the rules' own terms — never a model's
    #: account of why it "rejected" anything. A model asked to list
    #: alternatives it discarded is confabulating: it did not enumerate and
    #: reject them, it generated plausible ones after the fact.
    reason: str


class SignalQueries:
    """Read-only. Every method is scoped to one workspace, explicitly."""

    def __init__(
        self,
        *,
        repository: SignalRepository,
        profiles: ProfileRepository,
        business_events: BusinessEventQueries,
        catalog: SignalCatalog,
    ) -> None:
        self._repository = repository
        self._profiles = profiles
        self._business_events = business_events
        self._catalog = catalog

    async def signals(
        self,
        workspace_id: UUID,
        entity_id: UUID,
        *,
        signal_type: SignalType | None = None,
        live_only: bool = True,
        now: datetime | None = None,
    ) -> tuple[Signal, ...]:
        """Hypotheses held for this entity.

        `live_only` applies all three ways a hypothesis stops being current:
        superseded by better-evidenced grounds, past its shelf life, or of a
        type the workspace no longer holds.
        """
        moment = now or datetime.now(UTC)
        found = await self._repository.for_entity(
            workspace_id,
            entity_id,
            signal_type=signal_type,
            live_at=moment if live_only else None,
        )
        if not live_only:
            return found

        profile = await self._profiles.current(workspace_id)
        return tuple(
            signal
            for signal in found
            if resolve_entry(self._catalog, profile, signal.signal_type).is_active
        )

    async def explanation(self, workspace_id: UUID, signal_id: UUID) -> SignalExplanation | None:
        signal = await self._repository.by_id(workspace_id, signal_id)
        if signal is None:
            return None

        profile = await self._profiles.by_version(workspace_id, signal.profile_version)
        cited = set(signal.contributing_event_ids)
        events = await self._business_events.business_events(workspace_id, signal.entity_id)
        constituents = [
            await self._repository.by_id(workspace_id, constituent_id)
            for constituent_id in signal.constituent_signal_ids
        ]

        return SignalExplanation(
            signal=signal,
            definition=self._catalog.definition(signal.signal_type),
            # The entry as recorded on the signal, resolved through the
            # profile version that produced it — not today's. A historical
            # signal explained through a current profile would be a lie.
            profile_entry=resolve_entry(self._catalog, profile, signal.signal_type),
            profile_version=signal.profile_version,
            business_events=tuple(event for event in events if event.id in cited),
            constituents=tuple(c for c in constituents if c is not None),
        )

    async def history(self, workspace_id: UUID, signal_id: UUID) -> tuple[Signal, ...]:
        """The supersession chain, oldest first — what was believed, and
        when."""
        chain: list[Signal] = []
        current = await self._repository.by_id(workspace_id, signal_id)
        while current is not None:
            chain.append(current)
            if current.supersedes is None:
                break
            current = await self._repository.by_id(workspace_id, current.supersedes)
        return tuple(reversed(chain))

    async def profile(self, workspace_id: UUID) -> tuple[ProfileEntry, ...]:
        """This workspace's reading of the catalog, falling back to the
        declared defaults where it has said nothing."""
        stored = await self._profiles.current(workspace_id)
        if stored is None:
            return default_profile(self._catalog)
        return tuple(
            resolve_entry(self._catalog, stored, definition.key)
            for definition in self._catalog.types
        )

    async def stored_profile(self, workspace_id: UUID) -> SignalProfile | None:
        return await self._profiles.current(workspace_id)

    async def unsupported_types(
        self, workspace_id: UUID, entity_id: UUID, *, now: datetime | None = None
    ) -> tuple[UnsupportedReading, ...]:
        """Hypotheses this entity's evidence was tested against and did not
        support — the *competing readings* a Decision Package reports.

        Driven by `ground()`, the same function that decides whether a signal
        is generated at all. **No rule is re-implemented here**, and none may
        be: a second copy of the grounding logic would diverge from the first
        and the two answers would disagree about the same evidence.

        Types the workspace has switched off are excluded rather than
        reported as unsupported. *"Your workspace does not track this"* and
        *"the evidence does not support this"* are different statements, and
        conflating them would tell a customer their configuration was a
        finding about their account.
        """
        events = await self._business_events.business_events(workspace_id, entity_id)
        profile = await self._profiles.current(workspace_id)
        produced = {
            signal.signal_type
            for signal in await self.signals(workspace_id, entity_id, live_only=True, now=now)
        }

        readings: list[UnsupportedReading] = []
        for definition in self._catalog.types:
            if definition.key in produced:
                continue
            entry = resolve_entry(self._catalog, profile, definition.key)
            if not entry.is_active:
                continue
            if ground(events, definition, entry):
                continue
            readings.append(
                UnsupportedReading(
                    signal_type=definition.key,
                    reason=_why_not(events, definition, entry),
                )
            )
        return tuple(sorted(readings, key=lambda r: r.signal_type.value))

    async def live_with_evidence(
        self, workspace_id: UUID, entity_id: UUID, *, now: datetime | None = None
    ) -> tuple[tuple[Signal, tuple[BusinessEvent, ...]], ...]:
        """Every live hypothesis, with the recorded events it rests on (**R2-01**).

        **Two reads, not one per hypothesis.** Every signal about an account
        cites events belonging to that account, so the events are fetched once
        and paired in memory — a per-signal join would make a page of four
        hypotheses cost five queries to answer one question.

        The pairing preserves `contributing_event_ids` order, which is the
        order the pipeline recorded, so the same account renders the same way
        twice. Insertion order is not a fact about a company.
        """
        signals = await self.signals(workspace_id, entity_id, live_only=True, now=now)
        if not signals:
            return ()
        events = {
            event.id: event
            for event in await self._business_events.business_events(workspace_id, entity_id)
        }
        return tuple(
            (
                signal,
                # A cited event that no longer resolves is skipped rather than
                # faked. A signal cannot be constructed citing nothing, so an
                # empty tuple here means the events were deleted underneath it
                # — which the surface renders as absence, never as a guess.
                tuple(
                    events[event_id]
                    for event_id in signal.contributing_event_ids
                    if event_id in events
                ),
            )
            for signal in signals
        )

    def catalog(self) -> SignalCatalog:
        """The global vocabulary. Exposed so the product, analytics,
        documentation, and support all read the same definitions rather than
        re-describing them."""
        return self._catalog


def _why_not(
    events: tuple[BusinessEvent, ...],
    definition: SignalTypeDefinition,
    entry: ProfileEntry,
) -> str:
    """The rules' own reason, phrased for a reader.

    Two reasons and no others, because `ground()` has exactly two ways to
    decline: nothing relevant happened, or not enough distinct things
    happened close enough together. Anything else here would be a third
    explanation for behaviour that has two.
    """
    relevant = [event for event in events if event.type_key in definition.contributing_event_types]
    if not relevant:
        kinds = ", ".join(sorted(t.value for t in definition.contributing_event_types))
        return f"nothing of the kind this reading needs has happened here ({kinds})"

    minimum = (
        entry.minimum_contributors
        if entry.minimum_contributors is not None
        else definition.minimum_contributors
    )
    window = entry.window_days if entry.window_days is not None else definition.window_days
    found = len({event.type_key for event in relevant})
    return (
        f"only {found} of the {minimum} distinct kinds of evidence this reading needs occurred "
        f"within {window} days of each other"
    )

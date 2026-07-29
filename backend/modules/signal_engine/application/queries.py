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

    def catalog(self) -> SignalCatalog:
        """The global vocabulary. Exposed so the product, analytics,
        documentation, and support all read the same definitions rather than
        re-describing them."""
        return self._catalog

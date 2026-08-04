"""Generate the commercial hypotheses an entity's business events support.

**This use case answers "why might this matter to this customer?" and
stops.** It does not rank, prioritise, score, or estimate likelihood. There
is no number in it beyond windows and counts.

Three properties shape the flow:

**Interpretation is workspace-specific; evidence is not.** The same
business events produce different signals in two workspaces with different
profiles, and identical signals in two workspaces with identical ones.
Nothing about the evidence changes.

**Contradiction is preserved.** Opposing hypotheses are generated
independently and both stored. The Signal Engine never picks.

**A composite enriches; it never replaces.** Constituent signals are
generated and stored in their own right, and the composite names them. It
adds context on top of history rather than collapsing it.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from modules.business_event_engine.public import BusinessEventQueries
from modules.commercial_profile.public import DeclaredCompetitorReader
from modules.signal_engine.application.ports import ProfileRepository, SignalRepository
from modules.signal_engine.domain.catalog import (
    SignalCatalog,
    SignalType,
    SignalTypeDefinition,
)
from modules.signal_engine.domain.events import SignalGenerated, SignalSuperseded
from modules.signal_engine.domain.profile import (
    DEFAULT_PROFILE_VERSION,
    ProfileEntry,
    SignalProfile,
    resolve_entry,
)
from modules.signal_engine.domain.rules import Grounding, fold, ground
from modules.signal_engine.domain.signal import Signal, relevant_until, signal_id
from signora_platform.event_bus import EventPublisher
from signora_platform.observability import get_logger

logger = get_logger(__name__)

PRODUCER_MODULE = "signal_engine"


@dataclass(frozen=True, slots=True)
class GenerateSignalsInput:
    workspace_id: UUID
    entity_id: UUID
    #: Which profile version to interpret through. `None` means the current
    #: one — **current replay**, answering *"what would we say now?"*.
    #: A specific version is **historical replay**, reproducing what the
    #: customer was originally told. The two answer different business
    #: questions and are never conflated.
    profile_version: int | None = None


@dataclass(frozen=True, slots=True)
class GenerateSignalsResult:
    generated: int
    superseded: int
    profile_version: int


class GenerateSignals:
    def __init__(
        self,
        *,
        repository: SignalRepository,
        profiles: ProfileRepository,
        competitors: DeclaredCompetitorReader,
        business_events: BusinessEventQueries,
        catalog: SignalCatalog,
        publisher: EventPublisher,
        session: AsyncSession,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._repository = repository
        self._profiles = profiles
        # **The one declaration this module reads that it does not own.**
        # Resolved through `commercial_profile.public`, injected by the
        # composition root, and consulted at the same moment as the profile —
        # ADR-0403. Nothing here learns that it is backed by SQL.
        self._competitors = competitors
        # Business events are referenced directly through their public
        # contract, never re-derived from observations: two definitions of
        # one concept diverge within a year.
        self._business_events = business_events
        self._catalog = catalog
        self._publisher = publisher
        self._session = session
        self._clock = clock

    async def execute(
        self,
        request: GenerateSignalsInput,
        *,
        correlation_id: UUID,
        causation_id: UUID | None = None,
    ) -> GenerateSignalsResult:
        events = await self._business_events.business_events(
            request.workspace_id, request.entity_id
        )
        profile = await self._resolve_profile(request)
        version = profile.version if profile is not None else DEFAULT_PROFILE_VERSION
        declared = await self._resolve_competitors(request.workspace_id)

        if not events:
            return GenerateSignalsResult(generated=0, superseded=0, profile_version=version)

        now = self._clock()
        published: list[SignalGenerated | SignalSuperseded] = []
        generated = superseded = 0

        # Single-event strategies first, so a composite can name the
        # constituents it enriches rather than inventing them.
        singles: list[Signal] = []
        composites: list[tuple[Signal, Grounding]] = []

        for definition in self._ordered_types():
            entry = resolve_entry(self._catalog, profile, definition.key)
            if not entry.is_active:
                # IGNORED means the hypothesis is not held here at all.
                continue

            for grounding in ground(events, definition, entry, declared=declared):
                signal = self._build(request, definition, entry, grounding, now, version)
                if definition.is_composite:
                    composites.append((signal, grounding))
                else:
                    singles.append(signal)

        enriched = [
            signal.enriched_by(_constituents_of(grounding, singles))
            for signal, grounding in composites
        ]

        for signal_type, batch in _by_type(singles + enriched).items():
            outcome = await self._record(request, signal_type, batch, causation_id, published)
            generated += outcome[0]
            superseded += outcome[1]

        if published:
            # See the note in provider_normalization's handler: the platform's
            # PublishableEvent Protocol declares settable members, which frozen
            # domain events cannot satisfy. Raised as a finding, not fixed here.
            await self._publisher.publish(
                published,  # type: ignore[arg-type]
                session=self._session,
                producer_module=PRODUCER_MODULE,
                correlation_id=correlation_id,
            )

        logger.info(
            "signals generated",
            extra={
                "entity_id": str(request.entity_id),
                "generated": generated,
                "superseded": superseded,
                "catalog_version": self._catalog.version,
                "profile_version": version,
            },
        )
        return GenerateSignalsResult(
            generated=generated, superseded=superseded, profile_version=version
        )

    async def _resolve_competitors(self, workspace_id: UUID) -> frozenset[str]:
        """The declared rivals, folded for comparison.

        **`None` and an empty list collapse here, deliberately.** *"Nobody has
        told us"* and *"we compete with nobody"* are different facts and the
        surface that asks must tell them apart — but to a rule deciding
        whether an adoption is grounds, both mean **no declared rival**, and
        branching on the difference would invent a behaviour neither state
        asks for.

        **Not versioned into the signal.** A profile version is recorded
        because it changes what a signal *means*; a competitor list changes
        only whether one exists at all, and the signal's own evidence already
        names the technology that matched.
        """
        declaration = await self._competitors.current(workspace_id)
        if declaration is None:
            return frozenset()
        return frozenset(fold(competitor.name) for competitor in declaration.competitors)

    async def _resolve_profile(self, request: GenerateSignalsInput) -> SignalProfile | None:
        if request.profile_version is None:
            return await self._profiles.current(request.workspace_id)
        if request.profile_version == DEFAULT_PROFILE_VERSION:
            return None
        return await self._profiles.by_version(request.workspace_id, request.profile_version)

    def _ordered_types(self) -> list[SignalTypeDefinition]:
        return sorted(self._catalog.types, key=lambda d: (d.is_composite, d.key.value))

    def _build(
        self,
        request: GenerateSignalsInput,
        definition: SignalTypeDefinition,
        entry: ProfileEntry,
        grounding: Grounding,
        now: datetime,
        profile_version: int,
    ) -> Signal:
        event_ids = tuple(event.id for event in grounding.events)
        return Signal(
            id=signal_id(
                workspace_id=request.workspace_id,
                entity_id=request.entity_id,
                signal_type=definition.key,
                contributing_event_ids=event_ids,
            ),
            workspace_id=request.workspace_id,
            entity_id=request.entity_id,
            signal_type=definition.key,
            relevance=entry.relevance,
            occurred_at=grounding.occurred_at,
            window_start=grounding.window_start,
            window_end=grounding.window_end,
            generated_at=now,
            relevant_until=relevant_until(grounding.occurred_at, definition.relevance_window_days),
            rationale=_rationale(definition, entry, grounding),
            contributing_event_ids=event_ids,
            contributing_event_types=grounding.event_types,
            catalog_version=self._catalog.version,
            profile_version=profile_version,
        )

    async def _record(
        self,
        request: GenerateSignalsInput,
        signal_type: SignalType,
        fresh_batch: list[Signal],
        causation_id: UUID | None,
        published: list[SignalGenerated | SignalSuperseded],
    ) -> tuple[int, int]:
        existing = await self._repository.current_for_entity(
            request.workspace_id, request.entity_id, signal_type=signal_type
        )
        known = {signal.id for signal in existing}
        fresh = [signal for signal in fresh_batch if signal.id not in known]
        if not fresh:
            return 0, 0

        # A hypothesis whose grounds a fresh one now subsumes was not wrong —
        # it rested on less. The newer signal names it, and it stays readable
        # as what was believed then.
        replacements = _replacements(fresh, existing)
        to_write = tuple(
            signal.replacing(replacements[signal.id]) if signal.id in replacements else signal
            for signal in fresh
        )

        written = await self._repository.record(to_write)
        for signal in to_write:
            published.append(_generated_event(signal, causation_id))
            if signal.supersedes is not None:
                published.append(_superseded_event(signal, signal.supersedes, causation_id))

        return written, len(replacements)


def _rationale(definition: SignalTypeDefinition, entry: ProfileEntry, grounding: Grounding) -> str:
    """Two halves, deliberately: the interpretation and the evidence.

    A customer must be able to challenge either independently — *"we don't
    actually care about that"* is a different objection from *"that didn't
    happen"*, and only one of them is Signora's mistake.
    """
    basis = "; ".join(event.summary for event in grounding.events)
    return (
        f"{definition.hypothesis} Your profile treats this as a "
        f"{entry.relevance.value} indicator. Based on: {basis}."
    )


def _constituents_of(grounding: Grounding, singles: Sequence[Signal]) -> tuple[UUID, ...]:
    """Which independently-generated signals this composite builds on.

    **Enrichment, never replacement.** The constituents were generated and
    stored in their own right; naming them here adds navigable context
    without collapsing any of them.
    """
    covered = set(event.id for event in grounding.events)
    return tuple(
        sorted(
            (signal.id for signal in singles if set(signal.contributing_event_ids) <= covered),
            key=str,
        )
    )


def _by_type(signals: Sequence[Signal]) -> dict[SignalType, list[Signal]]:
    grouped: dict[SignalType, list[Signal]] = {}
    for signal in signals:
        grouped.setdefault(signal.signal_type, []).append(signal)
    return dict(sorted(grouped.items(), key=lambda item: item[0].value))


def _replacements(fresh: Sequence[Signal], existing: Sequence[Signal]) -> dict[UUID, UUID]:
    """Which fresh signal replaces which earlier one.

    An earlier signal is replaced when a fresh one of the same type rests on
    a strict superset of its evidence — the hypothesis gained grounds.
    Anything else is a genuinely different hypothesis and replaces nothing.
    """
    replacements: dict[UUID, UUID] = {}
    for earlier in existing:
        earlier_evidence = set(earlier.contributing_event_ids)
        for signal in fresh:
            if earlier_evidence < set(signal.contributing_event_ids):
                replacements[signal.id] = earlier.id
    return replacements


def _generated_event(signal: Signal, causation_id: UUID | None) -> SignalGenerated:
    return SignalGenerated(
        event_id=uuid4(),
        workspace_id=signal.workspace_id,
        occurred_at=signal.generated_at,
        signal_id=signal.id,
        entity_id=signal.entity_id,
        signal_type=signal.signal_type.value,
        relevance=signal.relevance.value,
        business_occurred_at=signal.occurred_at,
        relevant_until=signal.relevant_until,
        catalog_version=signal.catalog_version,
        profile_version=signal.profile_version,
        payload_version=signal.payload_version,
        causation_id=causation_id,
    )


def _superseded_event(
    signal: Signal, supersedes: UUID, causation_id: UUID | None
) -> SignalSuperseded:
    return SignalSuperseded(
        event_id=uuid4(),
        workspace_id=signal.workspace_id,
        occurred_at=signal.generated_at,
        signal_id=signal.id,
        supersedes=supersedes,
        entity_id=signal.entity_id,
        signal_type=signal.signal_type.value,
        causation_id=causation_id,
    )

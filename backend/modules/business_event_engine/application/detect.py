"""Detect the business events an entity's observations support.

**This use case answers "why is this business-relevant?" and stops.** It
does not rank, prioritise, or score. Every threshold it applies comes from
the taxonomy; a numeric constant appearing in a rule is a review failure,
asserted by a syntax-tree invariant.

Two properties shape the flow:

**Rules see one provider's series at a time.** Provider values are never
combined into a synthetic truth. Agreement is counted *after* each series
has independently reached a conclusion — evidence about the evidence,
never a resolved value.

**One business fact is one event.** Two providers both showing a hiring
surge is one surge with two providers behind it, not two surges. Timeline
shows what happened to the company, not what each vendor reported.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from modules.business_event_engine.application.ports import BusinessEventRepository
from modules.business_event_engine.domain.business_event import (
    BusinessEvent,
    business_event_id,
)
from modules.business_event_engine.domain.events import (
    BusinessEventDetected,
    BusinessEventSuperseded,
)
from modules.business_event_engine.domain.rules import RULES, Detection, DetectionRule
from modules.business_event_engine.domain.taxonomy import BusinessEventType, Taxonomy
from modules.observation_engine.public import Observation, ObservationQueries
from signora_platform.event_bus import EventPublisher
from signora_platform.observability import get_logger

logger = get_logger(__name__)

PRODUCER_MODULE = "business_event_engine"


@dataclass(frozen=True, slots=True)
class DetectBusinessEventsInput:
    workspace_id: UUID
    entity_id: UUID


@dataclass(frozen=True, slots=True)
class DetectBusinessEventsResult:
    detected: int
    superseded: int


class DetectBusinessEvents:
    def __init__(
        self,
        *,
        repository: BusinessEventRepository,
        observations: ObservationQueries,
        taxonomy: Taxonomy,
        publisher: EventPublisher,
        session: AsyncSession,
        rules: Sequence[DetectionRule] = RULES,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._repository = repository
        self._observations = observations
        self._taxonomy = taxonomy
        self._publisher = publisher
        self._session = session
        self._rules = tuple(rules)
        self._clock = clock

        # Fails at construction rather than at the first detection: a type
        # nobody detects is a promise the product cannot keep, and a rule
        # nobody declared is a threshold nobody reviewed.
        taxonomy.validate_complete(frozenset(rule.detects for rule in self._rules))

    async def execute(
        self,
        request: DetectBusinessEventsInput,
        *,
        correlation_id: UUID,
        causation_id: UUID | None = None,
    ) -> DetectBusinessEventsResult:
        observations = await self._observations.observations(
            request.workspace_id, request.entity_id
        )
        if not observations:
            return DetectBusinessEventsResult(detected=0, superseded=0)

        now = self._clock()
        events: list[BusinessEventDetected | BusinessEventSuperseded] = []
        detected = superseded = 0

        by_provider = _grouped_by_provider(observations)

        for rule in self._rules:
            parameters = self._taxonomy.parameters(rule.detects)
            # Each provider's series is evaluated alone. This is the line
            # that keeps a phantom conclusion out: no rule ever sees two
            # providers' values in one computation.
            detections = [
                detection
                for series in by_provider.values()
                for detection in rule.evaluate(series, parameters)
            ]
            if not detections:
                continue

            outcome = await self._record(
                request, rule.detects, detections, now, causation_id, events
            )
            detected += outcome[0]
            superseded += outcome[1]

        if events:
            # See the note in provider_normalization's handler: the platform's
            # PublishableEvent Protocol declares settable members, which frozen
            # domain events cannot satisfy. Raised as a finding, not fixed here.
            await self._publisher.publish(
                events,  # type: ignore[arg-type]
                session=self._session,
                producer_module=PRODUCER_MODULE,
                correlation_id=correlation_id,
            )

        logger.info(
            "business events detected",
            extra={
                "entity_id": str(request.entity_id),
                "detected": detected,
                "superseded": superseded,
                "taxonomy_version": self._taxonomy.version,
            },
        )
        return DetectBusinessEventsResult(detected=detected, superseded=superseded)

    async def _record(
        self,
        request: DetectBusinessEventsInput,
        type_key: BusinessEventType,
        detections: list[Detection],
        now: datetime,
        causation_id: UUID | None,
        events: list[BusinessEventDetected | BusinessEventSuperseded],
    ) -> tuple[int, int]:
        definition = self._taxonomy.definition(type_key)
        merged = _merge_agreeing(detections)

        existing = await self._repository.current_for_entity(
            request.workspace_id, request.entity_id, type_key=type_key
        )
        known = {event.id for event in existing}

        fresh: list[BusinessEvent] = []
        for detection in merged:
            evidence_ids = tuple(observation.id for observation in detection.evidence)
            event_id = business_event_id(
                workspace_id=request.workspace_id,
                entity_id=request.entity_id,
                type_key=type_key,
                evidence_observation_ids=evidence_ids,
            )
            if event_id in known:
                continue

            fresh.append(
                BusinessEvent(
                    id=event_id,
                    workspace_id=request.workspace_id,
                    entity_id=request.entity_id,
                    type_key=type_key,
                    domain=definition.domain,
                    occurred_at=detection.occurred_at,
                    window_start=detection.window_start,
                    window_end=detection.window_end,
                    detected_at=now,
                    summary=detection.summary,
                    facts=detection.facts,
                    evidence_observation_ids=evidence_ids,
                    corroborating_providers=detection.providers,
                    taxonomy_version=self._taxonomy.version,
                )
            )

        if not fresh:
            return 0, 0

        # An event whose evidence a fresh one now subsumes was not wrong —
        # it was a smaller view of the same phenomenon. The newer event names
        # it, and it stays readable as what was believed then.
        replacements = _replacements(fresh, existing)
        to_write = tuple(
            event.replacing(replacements[event.id]) if event.id in replacements else event
            for event in fresh
        )

        written = await self._repository.record(to_write)
        for event in to_write:
            events.append(_detected_event(event, causation_id))
            if event.supersedes is not None:
                events.append(_superseded_event(event, event.supersedes, causation_id))

        return written, len(replacements)


def _grouped_by_provider(
    observations: tuple[Observation, ...],
) -> dict[str, tuple[Observation, ...]]:
    grouped: dict[str, list[Observation]] = {}
    for observation in observations:
        grouped.setdefault(observation.provider, []).append(observation)
    return {
        provider: tuple(sorted(items, key=lambda o: (o.observed_at, str(o.id))))
        for provider, items in sorted(grouped.items())
    }


def _merge_agreeing(detections: list[Detection]) -> list[Detection]:
    """One business fact is one event, however many providers saw it.

    Detections are grouped by what they concluded — the summary and the
    facts — and their evidence is unioned. **No values are combined**: each
    detection was reached from one provider's series alone, and merging
    only records that more than one series reached it.
    """
    grouped: dict[tuple[str, str], list[Detection]] = {}
    for detection in detections:
        key = (detection.summary, _facts_key(detection))
        grouped.setdefault(key, []).append(detection)

    merged: list[Detection] = []
    for group in grouped.values():
        # Deduplicated by id rather than by object: an observation's value
        # may be a mapping, so the observations themselves are not hashable.
        by_id = {
            observation.id: observation for detection in group for observation in detection.evidence
        }
        evidence = tuple(sorted(by_id.values(), key=lambda o: (o.observed_at, str(o.id))))
        first = group[0]
        merged.append(
            Detection(
                summary=first.summary,
                facts=first.facts,
                occurred_at=min(detection.occurred_at for detection in group),
                window_start=min(detection.window_start for detection in group),
                window_end=max(detection.window_end for detection in group),
                evidence=evidence,
            )
        )
    return merged


def _facts_key(detection: Detection) -> str:
    import json

    return json.dumps(detection.facts, sort_keys=True, default=str, separators=(",", ":"))


def _replacements(
    fresh: Sequence[BusinessEvent], existing: Sequence[BusinessEvent]
) -> dict[UUID, UUID]:
    """Which fresh event replaces which earlier one.

    An earlier event is replaced when a fresh event of the same type is
    built on a superset of its evidence — the phenomenon extended. Anything
    else is a genuinely different event and replaces nothing.
    """
    replacements: dict[UUID, UUID] = {}
    for earlier in existing:
        earlier_evidence = set(earlier.evidence_observation_ids)
        for event in fresh:
            if earlier_evidence < set(event.evidence_observation_ids):
                replacements[event.id] = earlier.id
    return replacements


def _detected_event(event: BusinessEvent, causation_id: UUID | None) -> BusinessEventDetected:
    return BusinessEventDetected(
        event_id=uuid4(),
        workspace_id=event.workspace_id,
        occurred_at=event.detected_at,
        business_event_id=event.id,
        entity_id=event.entity_id,
        type_key=event.type_key.value,
        domain=event.domain.value,
        business_occurred_at=event.occurred_at,
        window_start=event.window_start,
        window_end=event.window_end,
        taxonomy_version=event.taxonomy_version,
        payload_version=event.payload_version,
        causation_id=causation_id,
    )


def _superseded_event(
    event: BusinessEvent, supersedes: UUID, causation_id: UUID | None
) -> BusinessEventSuperseded:
    return BusinessEventSuperseded(
        event_id=uuid4(),
        workspace_id=event.workspace_id,
        occurred_at=event.detected_at,
        business_event_id=event.id,
        supersedes=supersedes,
        entity_id=event.entity_id,
        type_key=event.type_key.value,
        causation_id=causation_id,
    )

"""Derive observations from one provider's claim series.

Pure and total: given the same claims it produces the same observations on
every machine, in any processing order. That is what makes the whole table
rebuildable from claims — the rollback for a bad derivation rule.

**The series is always one `(entity, provider, attribute)`.** Change is
never computed across providers. Apollo reporting 120 on Monday and
CoreSignal 145 on Tuesday is disagreement, and merging the two series would
say "grew 25 in a day" about a company where nothing happened. Correcting
for that would mean deciding which provider is authoritative — truth
resolution, which no module at this depth has the context to justify.

**Most claims produce nothing, and that is the point.** A nightly sync
re-asserts the same headcount for weeks. Filtering re-assertion is the
module's main job, not an optimisation.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from modules.observation_engine.domain.observation import (
    Observation,
    ObservationDirection,
    ObservationKind,
    canonical,
    direction_and_magnitude,
    observation_id,
    observation_kind_for,
    transition_key,
)
from modules.observation_engine.domain.semantics import occurrence_key
from modules.provider_normalization.public import ClaimAttribute, ClaimView


def _ordered(claims: Sequence[ClaimView]) -> list[ClaimView]:
    """Oldest first, with the claim id as a tiebreak.

    The tiebreak matters: two claims can legitimately share an
    `observed_at`, and without a total order the derived observations would
    depend on the order the database happened to return rows — which would
    quietly break determinism and replay.
    """
    return sorted(claims, key=lambda c: (c.observed_at, str(c.id)))


def derive(
    claims: Sequence[ClaimView],
    *,
    workspace_id: UUID,
    entity_id: UUID,
    provider: str,
    attribute: ClaimAttribute,
    recorded_at: datetime,
) -> tuple[Observation, ...]:
    """Every observation this series implies, in `observed_at` order."""
    if not claims:
        return ()

    kind = observation_kind_for(attribute)
    series = _ordered(claims)

    if kind is ObservationKind.OCCURRENCE_OBSERVED:
        return _occurrences(
            series,
            workspace_id=workspace_id,
            entity_id=entity_id,
            provider=provider,
            attribute=attribute,
            recorded_at=recorded_at,
        )

    return _transitions(
        series,
        workspace_id=workspace_id,
        entity_id=entity_id,
        provider=provider,
        attribute=attribute,
        recorded_at=recorded_at,
    )


def _transitions(
    series: list[ClaimView],
    *,
    workspace_id: UUID,
    entity_id: UUID,
    provider: str,
    attribute: ClaimAttribute,
    recorded_at: datetime,
) -> tuple[Observation, ...]:
    """Consecutive assertions that differ.

    **The first claim establishes a baseline and produces no observation.**
    Nothing changed — Signora merely learned. Emitting one would mean an
    onboarding sync of five thousand companies producing tens of thousands
    of observations that all say "we have started tracking this", drowning
    every consumer's signal for the life of the workspace. Entity creation
    already announces that, once, per company. (Ratified 2026-07-29: if
    "knowledge established" is ever needed, it is a separate domain concept,
    not an expansion of this one.)
    """
    observations: list[Observation] = []
    previous = series[0]

    for claim in series[1:]:
        if canonical(claim.value) == canonical(previous.value):
            # Re-assertion. The dominant case in a polling pipeline, and
            # never an observation.
            previous = claim
            continue

        direction, magnitude = direction_and_magnitude(attribute, previous.value, claim.value)
        observations.append(
            Observation(
                id=observation_id(
                    workspace_id=workspace_id,
                    entity_id=entity_id,
                    provider=provider,
                    attribute=attribute,
                    kind=ObservationKind.VALUE_CHANGED,
                    key=transition_key(
                        previous_value=previous.value,
                        previous_observed_at=previous.observed_at,
                        current_value=claim.value,
                        observed_at=claim.observed_at,
                    ),
                ),
                workspace_id=workspace_id,
                entity_id=entity_id,
                provider=provider,
                attribute=attribute,
                kind=ObservationKind.VALUE_CHANGED,
                previous_value=previous.value,
                current_value=claim.value,
                direction=direction,
                magnitude=magnitude,
                observed_at=claim.observed_at,
                previous_observed_at=previous.observed_at,
                recorded_at=recorded_at,
                evidence_claim_ids=(previous.id, claim.id),
            )
        )
        previous = claim

    return tuple(observations)


def _occurrences(
    series: list[ClaimView],
    *,
    workspace_id: UUID,
    entity_id: UUID,
    provider: str,
    attribute: ClaimAttribute,
    recorded_at: datetime,
) -> tuple[Observation, ...]:
    """One observation per distinct occurrence, at its earliest sighting.

    A provider re-reporting the same funding round on twenty consecutive
    nightly syncs asserts one thing twenty times. The earliest sighting is
    kept because it is the one the evidence actually supports — a later
    `observed_at` for the same round would misdate it.
    """
    observations: list[Observation] = []
    seen: set[str] = set()

    for claim in series:
        key = occurrence_key(attribute, claim.value, claim.observed_at)
        if key in seen:
            continue
        seen.add(key)

        observations.append(
            Observation(
                id=observation_id(
                    workspace_id=workspace_id,
                    entity_id=entity_id,
                    provider=provider,
                    attribute=attribute,
                    kind=ObservationKind.OCCURRENCE_OBSERVED,
                    key=key,
                ),
                workspace_id=workspace_id,
                entity_id=entity_id,
                provider=provider,
                attribute=attribute,
                kind=ObservationKind.OCCURRENCE_OBSERVED,
                previous_value=None,
                current_value=claim.value,
                direction=ObservationDirection.OCCURRED,
                magnitude=None,
                observed_at=claim.observed_at,
                previous_observed_at=None,
                recorded_at=recorded_at,
                evidence_claim_ids=(claim.id,),
            )
        )

    return tuple(observations)


def refinements(derived: Sequence[Observation], stale: Sequence[Observation]) -> dict[UUID, UUID]:
    """Which derived observation refines which superseded one.

    A late-arriving claim does not make an earlier observation *false* —
    headcount really did go 120 → 145 across that window. It makes it **less
    precise**, and leaving it alongside the two finer observations would
    double-count the growth.

    A finer observation is one whose window falls inside the coarser one's.
    Windows within a series never overlap, so the mapping is unambiguous.
    """
    mapping: dict[UUID, UUID] = {}

    for coarse in stale:
        if coarse.previous_observed_at is None:
            continue
        for fine in derived:
            if fine.previous_observed_at is None:
                continue
            if (
                fine.previous_observed_at >= coarse.previous_observed_at
                and fine.observed_at <= coarse.observed_at
            ):
                mapping[fine.id] = coarse.id

    return mapping

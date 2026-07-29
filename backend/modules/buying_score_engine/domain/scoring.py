"""Building a ledger from live hypotheses — the whole of the reduction.

**The unit of contribution is the business event, not the signal.** That is
not a deduplication pass bolted on afterwards; it is the shape of the
algorithm, which makes double counting structurally impossible rather than
merely avoided. A composite hypothesis and the constituent it enriches rest
on the same grounds read two ways, and grounds are counted once.

Where several signals cite one business event, it is attributed to the
**highest-weighted** of them. The others stay in the ledger with a zero
contribution and a stated reason — a zero with a reason is information; an
absent row is a mystery.

**Nothing here nets.** Attention is unsigned for every posture. Posture is
carried through to the ledger so contradiction stays visible, and is never
folded into the arithmetic as a sign.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from modules.buying_score_engine.domain.ledger import (
    Contribution,
    ContributionLedger,
    weigh,
)
from modules.buying_score_engine.domain.scoring_model import AgeBand, ScoringModel
from modules.signal_engine.public import Signal, SignalCatalog


@dataclass(frozen=True, slots=True)
class _Candidate:
    """One signal's claim on one business event, before attribution."""

    business_event_id: UUID
    signal: Signal
    band: AgeBand
    band_started_at: datetime
    band_ends_at: datetime
    points: int


def build_ledger(
    signals: Sequence[Signal],
    *,
    model: ScoringModel,
    catalog: SignalCatalog,
    moment: datetime,
) -> ContributionLedger:
    """Reduce live hypotheses to a ledger. The score follows from it."""
    candidates = [
        candidate
        for signal in signals
        for candidate in _candidates_for(signal, model=model, moment=moment)
    ]
    winners = _attribute(candidates)

    entries = tuple(
        _entry(candidate, model=model, catalog=catalog, winner=winners[candidate.business_event_id])
        for candidate in candidates
    )
    return ContributionLedger(entries=_ordered(entries), ceiling=model.ceiling)


def _candidates_for(
    signal: Signal, *, model: ScoringModel, moment: datetime
) -> list[_Candidate]:
    """One candidate per business event the signal cites.

    An account with more distinct material business events deserves more
    attention than one with a single event read the same way — so weight
    accrues per event rather than per hypothesis.
    """
    weight = model.weight_for(signal.signal_type)
    band = model.band_at(signal.occurred_at, signal.relevant_until, moment)
    started, ends = _band_span(signal, model=model, band=band)
    points = weigh(
        weight.base_weight,
        model.relevance_multiplier(signal.relevance),
        band.multiplier_percent,
    )
    return [
        _Candidate(
            business_event_id=event_id,
            signal=signal,
            band=band,
            band_started_at=started,
            band_ends_at=ends,
            points=points,
        )
        for event_id in signal.contributing_event_ids
    ]


def _band_span(
    signal: Signal, *, model: ScoringModel, band: AgeBand
) -> tuple[datetime, datetime]:
    """When the signal entered its current band, and when it leaves.

    The first band begins at `occurred_at`; every later one begins where its
    predecessor ended. The final boundary **is** the signal's expiry, so
    ageing out is the last band transition rather than a second mechanism
    beside them — which is what lets a score state one honest `valid_until`.
    """
    boundaries = model.band_boundaries(signal.occurred_at, signal.relevant_until)
    index = model.age_bands.index(band)
    started = signal.occurred_at if index == 0 else boundaries[index - 1]
    return started, boundaries[index]


def _attribute(candidates: Sequence[_Candidate]) -> dict[UUID, UUID]:
    """Which signal each business event's points belong to.

    The highest-weighted claim wins, ties broken by signal id so the result
    is reproducible rather than dependent on iteration order. A composite
    usually outweighs the constituents it enriches, so it tends to win
    naturally — and where a constituent's type is weighted higher, it wins
    instead, which is the correct answer for the same reason.
    """
    winners: dict[UUID, _Candidate] = {}
    for candidate in candidates:
        best = winners.get(candidate.business_event_id)
        if best is None or (candidate.points, str(candidate.signal.id)) > (
            best.points,
            str(best.signal.id),
        ):
            winners[candidate.business_event_id] = candidate
    return {event_id: winner.signal.id for event_id, winner in winners.items()}


def _entry(
    candidate: _Candidate, *, model: ScoringModel, catalog: SignalCatalog, winner: UUID
) -> Contribution:
    counted = candidate.signal.id == winner
    weight = model.weight_for(candidate.signal.signal_type)
    return Contribution(
        business_event_id=candidate.business_event_id,
        signal_id=candidate.signal.id,
        signal_type=candidate.signal.signal_type,
        posture=weight.posture,
        relevance=candidate.signal.relevance,
        base_weight=weight.base_weight,
        relevance_multiplier=model.relevance_multiplier(candidate.signal.relevance),
        age_band=candidate.band.key,
        age_multiplier=candidate.band.multiplier_percent,
        contribution=candidate.points if counted else 0,
        counted=counted,
        reason=_reason(candidate, catalog=catalog, counted=counted),
        band_started_at=candidate.band_started_at,
        band_ends_at=candidate.band_ends_at,
    )


def _reason(candidate: _Candidate, *, catalog: SignalCatalog, counted: bool) -> str:
    """The sentence a customer reads, from the fields an auditor checks.

    The band's **word** appears beside its percentage deliberately: a
    customer can argue with *"we count ageing evidence at 30%"*, and cannot
    argue with a decimal.
    """
    title = catalog.definition(candidate.signal.signal_type).title
    if not counted:
        return (
            f"{title} rests on this business event too, already counted through a "
            "higher-weighted hypothesis. Counted once, so the same grounds read two ways "
            "cannot inflate the score."
        )
    return (
        f"{title} · {candidate.signal.relevance.value} relevance · "
        f"{candidate.band.label} evidence ({candidate.band.multiplier_percent}%) "
        f"— {candidate.points} points"
    )


def _ordered(entries: tuple[Contribution, ...]) -> tuple[Contribution, ...]:
    """Largest contribution first, then stably by identity.

    Storage order is what a customer reads first, so it answers *"why is
    this account scored where it is?"* in the order that actually explains it.
    """
    return tuple(
        sorted(
            entries,
            key=lambda entry: (
                -entry.contribution,
                str(entry.business_event_id),
                str(entry.signal_id),
            ),
        )
    )

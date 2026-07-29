"""Rules that read a single observation.

Most business events need no correlation at all: a funding round happened,
a technology was retired, a leader joined. Noticing that avoids building a
correlation engine for cases that do not need one.

Every summary here is written for a CRO. No provider names, no attribute
identifiers, no implementation vocabulary — *"Acme raised a $24M Series
B"*, not *"crunchbase funding_round occurrence observed"*.
"""

from __future__ import annotations

from typing import Any

from modules.business_event_engine.domain.rules.base import Detection, window_of
from modules.business_event_engine.domain.taxonomy import BusinessEventType, Parameters
from modules.observation_engine.public import Observation, ObservationDirection
from modules.provider_normalization.public import ClaimAttribute


def _field(value: Any, name: str) -> Any:
    return value.get(name) if isinstance(value, dict) else None


def _one(observation: Observation, summary: str, facts: dict[str, Any]) -> Detection:
    start, end = window_of((observation,))
    return Detection(
        summary=summary,
        facts=facts,
        occurred_at=observation.observed_at,
        window_start=start,
        window_end=end,
        evidence=(observation,),
    )


def _money(amount: Any, currency: Any) -> str:
    if not isinstance(amount, (int, float)):
        return "an undisclosed amount"
    unit = str(currency) if currency else "USD"
    millions = amount / 1_000_000
    return f"{millions:,.0f}M {unit}" if millions >= 1 else f"{amount:,.0f} {unit}"


class FundingRoundClosed:
    detects = BusinessEventType.FUNDING_ROUND_CLOSED

    def evaluate(
        self, series: tuple[Observation, ...], parameters: Parameters
    ) -> tuple[Detection, ...]:
        minimum = parameters.number("minimum_amount")
        detections: list[Detection] = []

        for observation in series:
            if observation.attribute is not ClaimAttribute.FUNDING_ROUND:
                continue
            amount = _field(observation.current_value, "amount")
            if not isinstance(amount, (int, float)) or amount < minimum:
                # A small round is real but not the news this type exists to
                # carry. The floor is a business judgement, so it lives in
                # the taxonomy where it can be argued with.
                continue

            round_type = str(_field(observation.current_value, "round_type") or "round")
            detections.append(
                _one(
                    observation,
                    f"Raised {_money(amount, _field(observation.current_value, 'currency'))} "
                    f"in a {round_type.replace('_', ' ')} round",
                    {
                        "round_type": round_type,
                        "amount": amount,
                        "currency": _field(observation.current_value, "currency"),
                        "investors": _field(observation.current_value, "investors") or [],
                    },
                )
            )

        return tuple(detections)


class AcquisitionAnnounced:
    detects = BusinessEventType.ACQUISITION_ANNOUNCED

    def evaluate(
        self, series: tuple[Observation, ...], parameters: Parameters
    ) -> tuple[Detection, ...]:
        return tuple(
            _one(
                observation,
                f"Announced the acquisition of "
                f"{_field(observation.current_value, 'counterparty') or 'another company'}",
                {
                    "counterparty": _field(observation.current_value, "counterparty"),
                    "announced_on": _field(observation.current_value, "announced_on"),
                },
            )
            for observation in series
            if observation.attribute is ClaimAttribute.ACQUISITION
        )


class TechnologyAdopted:
    detects = BusinessEventType.TECHNOLOGY_ADOPTED

    def evaluate(
        self, series: tuple[Observation, ...], parameters: Parameters
    ) -> tuple[Detection, ...]:
        return tuple(
            _one(
                observation,
                f"Started using {_field(observation.current_value, 'name')}",
                {
                    "technology": _field(observation.current_value, "name"),
                    "category": _field(observation.current_value, "category"),
                },
            )
            for observation in series
            if observation.attribute is ClaimAttribute.TECHNOLOGY_DETECTED
        )


class TechnologyRetired:
    detects = BusinessEventType.TECHNOLOGY_RETIRED

    def evaluate(
        self, series: tuple[Observation, ...], parameters: Parameters
    ) -> tuple[Detection, ...]:
        return tuple(
            _one(
                observation,
                f"Stopped using {_field(observation.current_value, 'name')}",
                {
                    "technology": _field(observation.current_value, "name"),
                    "category": _field(observation.current_value, "category"),
                },
            )
            for observation in series
            if observation.attribute is ClaimAttribute.TECHNOLOGY_REMOVED
        )


class _LeadershipRule:
    """Shared shape for appointments and departures.

    Split into two types rather than one with a direction field, because a
    leader joining and a leader leaving mean opposite things commercially.
    A consumer that has to read a field to know whether the news is good
    has been handed the wrong vocabulary.
    """

    directions: frozenset[str]
    phrasing: str

    def evaluate(
        self, series: tuple[Observation, ...], parameters: Parameters
    ) -> tuple[Detection, ...]:
        qualifying = parameters.strings("qualifying_seniorities")
        detections: list[Detection] = []

        for observation in series:
            if observation.attribute is not ClaimAttribute.ROLE_CHANGE:
                continue
            direction = str(_field(observation.current_value, "direction") or "")
            seniority = str(_field(observation.current_value, "seniority") or "")
            if direction not in self.directions or seniority not in qualifying:
                # Which seniorities count is a business judgement — a
                # manager moving is not leadership news — so the list is
                # declared in the taxonomy.
                continue

            title = str(_field(observation.current_value, "title") or "A senior leader")
            detections.append(
                _one(
                    observation,
                    self.phrasing.format(title=title),
                    {"title": title, "seniority": seniority, "direction": direction},
                )
            )

        return tuple(detections)


class LeadershipAppointed(_LeadershipRule):
    detects = BusinessEventType.LEADERSHIP_APPOINTED
    directions = frozenset({"joined", "promoted"})
    phrasing = "Appointed a new {title}"


class LeadershipDeparted(_LeadershipRule):
    detects = BusinessEventType.LEADERSHIP_DEPARTED
    directions = frozenset({"left"})
    phrasing = "Their {title} departed"


class _RevenueRule:
    """Revenue movement, split by direction for the same reason leadership
    is: moving up market and moving down market are opposite news."""

    direction: ObservationDirection
    phrasing: str

    def evaluate(
        self, series: tuple[Observation, ...], parameters: Parameters
    ) -> tuple[Detection, ...]:
        minimum = parameters.count("minimum_ranges_moved")
        detections: list[Detection] = []

        for observation in series:
            if observation.attribute is not ClaimAttribute.REVENUE_BAND:
                continue
            if observation.direction is not self.direction:
                continue
            moved = _ranges_moved(observation)
            if moved < minimum:
                continue

            detections.append(
                _one(
                    observation,
                    self.phrasing.format(
                        previous=_readable_range(observation.previous_value),
                        current=_readable_range(observation.current_value),
                    ),
                    {
                        "previous_range": observation.previous_value,
                        "current_range": observation.current_value,
                        "ranges_moved": moved,
                    },
                )
            )

        return tuple(detections)


class RevenueGrowth(_RevenueRule):
    detects = BusinessEventType.REVENUE_GROWTH
    direction = ObservationDirection.INCREASED
    phrasing = "Revenue grew from {previous} to {current}"


class RevenueContraction(_RevenueRule):
    detects = BusinessEventType.REVENUE_CONTRACTION
    direction = ObservationDirection.DECREASED
    phrasing = "Revenue fell from {previous} to {current}"


#: Revenue ranges in ascending order, as the vocabulary defines them. Read
#: rather than re-declared, so the two cannot drift apart.
_RANGE_ORDER: tuple[str, ...] = (
    "under_1m",
    "1m_10m",
    "10m_50m",
    "50m_250m",
    "250m_1b",
    "over_1b",
)

_RANGE_LABELS: dict[str, str] = {
    "under_1m": "under $1M",
    "1m_10m": "$1M–$10M",
    "10m_50m": "$10M–$50M",
    "50m_250m": "$50M–$250M",
    "250m_1b": "$250M–$1B",
    "over_1b": "over $1B",
}


def _ranges_moved(observation: Observation) -> int:
    previous, current = str(observation.previous_value), str(observation.current_value)
    if previous not in _RANGE_ORDER or current not in _RANGE_ORDER:
        return 0
    return abs(_RANGE_ORDER.index(current) - _RANGE_ORDER.index(previous))


def _readable_range(value: Any) -> str:
    """A range a customer recognises, not the identifier we store it under."""
    return _RANGE_LABELS.get(str(value), str(value))


POINT_RULES: tuple[Any, ...] = (
    FundingRoundClosed(),
    AcquisitionAnnounced(),
    TechnologyAdopted(),
    TechnologyRetired(),
    LeadershipAppointed(),
    LeadershipDeparted(),
    RevenueGrowth(),
    RevenueContraction(),
)

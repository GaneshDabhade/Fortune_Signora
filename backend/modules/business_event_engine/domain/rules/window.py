"""Rules that correlate a series of observations over a window.

These are the cases a single observation genuinely cannot answer. A
company that grows 120 → 130 → 145 may pass no individual step's
threshold while the trajectory obviously does, and a buying-intent surge
is a shape across weeks rather than a moment.

**The series is always one provider's.** No rule here sees two providers'
values together, so nothing can combine them into a synthetic truth.
Agreement between providers is counted afterwards, from conclusions each
series reached independently.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from modules.business_event_engine.domain.rules.base import Detection, window_of
from modules.business_event_engine.domain.taxonomy import BusinessEventType, Parameters
from modules.observation_engine.public import Observation
from modules.provider_normalization.public import ClaimAttribute


def _within_window(series: tuple[Observation, ...], days: float) -> tuple[Observation, ...]:
    """The most recent stretch of the series.

    Anchored on the latest observation rather than on wall-clock now, so a
    replay of historical evidence reaches the same conclusion it would have
    reached at the time. A window measured against *now* would make every
    rebuild produce different events as time passed.
    """
    if not series:
        return ()
    ordered = sorted(series, key=lambda o: (o.observed_at, str(o.id)))
    cutoff = ordered[-1].observed_at - timedelta(days=days)
    return tuple(o for o in ordered if o.observed_at >= cutoff)


class _HeadcountRule:
    """Shared shape for growth and decline.

    Two types rather than one with a sign, because hiring and shrinking
    mean opposite things to a revenue team.
    """

    detects: BusinessEventType
    attributes: frozenset[ClaimAttribute]
    ratio_parameter: str
    absolute_parameter: str
    phrasing: str

    def evaluate(
        self, series: tuple[Observation, ...], parameters: Parameters
    ) -> tuple[Detection, ...]:
        relevant = tuple(o for o in series if o.attribute in self.attributes)
        window = _within_window(relevant, parameters.number("window_days"))
        if not window:
            return ()

        first, last = window[0], window[-1]
        start_value, end_value = first.previous_value, last.current_value
        if not isinstance(start_value, (int, float)) or not isinstance(end_value, (int, float)):
            return ()
        if start_value <= 0:
            # A ratio against a zero or missing baseline is not a growth
            # rate, it is a division. Nothing is concluded.
            return ()

        change = self._change(float(start_value), float(end_value))
        if change <= 0:
            return ()

        ratio = change / float(start_value)
        if ratio < parameters.number(self.ratio_parameter):
            return ()
        if change < parameters.number(self.absolute_parameter):
            # Both a proportional and an absolute floor: 15% of eight people
            # is not a hiring surge, and 400 hires at a company of 40,000 is.
            return ()

        window_start, window_end = window_of(window)
        return (
            Detection(
                summary=self.phrasing.format(
                    percent=round(ratio * 100),
                    days=max((window_end - window_start).days, 1),
                ),
                facts={
                    "starting_value": start_value,
                    "ending_value": end_value,
                    "change": change,
                    "ratio": round(ratio, 4),
                    "attribute": last.attribute.value,
                },
                occurred_at=window_end,
                window_start=window_start,
                window_end=window_end,
                evidence=window,
            ),
        )

    @staticmethod
    def _change(start: float, end: float) -> float:
        raise NotImplementedError


class HiringSurge(_HeadcountRule):
    detects = BusinessEventType.HIRING_SURGE
    attributes = frozenset({ClaimAttribute.EMPLOYEE_COUNT, ClaimAttribute.OPEN_ROLES})
    ratio_parameter = "minimum_growth_ratio"
    absolute_parameter = "minimum_absolute_growth"
    phrasing = "Grew headcount {percent}% over {days} days"

    @staticmethod
    def _change(start: float, end: float) -> float:
        return end - start


class HeadcountDecline(_HeadcountRule):
    detects = BusinessEventType.HEADCOUNT_DECLINE
    attributes = frozenset({ClaimAttribute.EMPLOYEE_COUNT})
    ratio_parameter = "minimum_decline_ratio"
    absolute_parameter = "minimum_absolute_decline"
    phrasing = "Reduced headcount {percent}% over {days} days"

    @staticmethod
    def _change(start: float, end: float) -> float:
        return start - end


class BuyingIntentSurge:
    """Sustained research on one topic.

    Grouped by topic, because a company researching two unrelated topics is
    two pieces of news. A rollup across topics would produce a number that
    means nothing to anybody.
    """

    detects = BusinessEventType.BUYING_INTENT_SURGE

    def evaluate(
        self, series: tuple[Observation, ...], parameters: Parameters
    ) -> tuple[Detection, ...]:
        relevant = tuple(o for o in series if o.attribute is ClaimAttribute.INTENT_TOPIC_SURGE)
        window = _within_window(relevant, parameters.number("window_days"))
        minimum_score = parameters.number("minimum_score")
        minimum_weeks = parameters.count("minimum_weeks")

        by_topic: dict[str, list[Observation]] = {}
        for observation in window:
            topic = _topic(observation)
            if topic:
                by_topic.setdefault(topic, []).append(observation)

        detections: list[Detection] = []
        for topic in sorted(by_topic):
            weeks = [o for o in by_topic[topic] if _score(o) >= minimum_score]
            if len(weeks) < minimum_weeks:
                # One loud week is noise. Sustained attention is the news,
                # and how many weeks count is a business judgement.
                continue

            window_start, window_end = window_of(tuple(weeks))
            peak = max(_score(o) for o in weeks)
            detections.append(
                Detection(
                    summary=(
                        f"Researching {topic} — {len(weeks)} weeks of elevated activity, "
                        f"peaking at {peak:.0f}"
                    ),
                    facts={
                        "topic": topic,
                        "weeks_elevated": len(weeks),
                        "peak_score": peak,
                    },
                    occurred_at=window_end,
                    window_start=window_start,
                    window_end=window_end,
                    evidence=tuple(weeks),
                )
            )

        return tuple(detections)


def _topic(observation: Observation) -> str | None:
    value = observation.current_value
    topic = value.get("topic") if isinstance(value, dict) else None
    return str(topic) if topic else None


def _score(observation: Observation) -> float:
    value = observation.current_value
    score = value.get("score") if isinstance(value, dict) else None
    return float(score) if isinstance(score, (int, float)) else 0.0


WINDOW_RULES: tuple[Any, ...] = (HiringSurge(), HeadcountDecline(), BuyingIntentSurge())

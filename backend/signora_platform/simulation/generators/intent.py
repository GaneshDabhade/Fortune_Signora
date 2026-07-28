"""DEVELOPMENT FIXTURE generator for behavioural intent.

**Not an authentic Bombora payload.** The structure is representative of
what a behavioural-intent provider is expected to expose; it must be
replaced when a legitimate artifact arrives.

Categorically different from the other four generators. They describe *what
a company is and what changed*; this describes *how a company is behaving
over time*. A single intent score is not a simulation of intent — it is a
number. The trajectory is the entire signal:

    Week 1: 18   baseline noise
    Week 2: 42
    Week 3: 71
    Week 4: 88   sustained rise → business event → signal → opportunity

The pipeline must be able to tell a rise from a decay from a reactivation.
A company whose intent is *falling* has usually already bought elsewhere,
and recommending outreach to them is the specific failure this generator
exists to let us test for.
"""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Final

from signora_platform.simulation.generators.base import PayloadGenerator, _fixture_notice
from signora_platform.simulation.scenario import ScenarioEvent

#: Below this, a score is indistinguishable from background noise. Emitting
#: a flat zero baseline would make every rise look cleaner than real intent
#: data ever is, and a pipeline tuned against clean data is tuned wrong.
NOISE_FLOOR: Final = 20
SURGE_CEILING: Final = 100


class TrendDirection(StrEnum):
    """Reported alongside the history so the shape is legible without
    recomputing it — and so a pipeline bug that misreads the trajectory is
    distinguishable from a provider that reported it differently."""

    EMERGING = "emerging"
    SUSTAINED = "sustained"
    DECAYING = "decaying"
    REACTIVATED = "reactivated"
    NOISE = "noise"


@dataclass(frozen=True, slots=True)
class TopicTrajectory:
    """One topic's weekly surge history."""

    topic: str
    weekly_scores: tuple[int, ...]
    direction: TrendDirection

    @property
    def current(self) -> int:
        return self.weekly_scores[-1] if self.weekly_scores else 0


def build_trajectory(
    topic: str,
    *,
    direction: TrendDirection,
    weeks: int,
    peak: int,
    rng: random.Random,
    noise: int = 6,
) -> TopicTrajectory:
    """Produce a weekly score series with the requested shape.

    Noise is applied to every point, including the baseline. Real intent
    data is jittery, and a perfectly monotonic rise is the easiest possible
    thing for a downstream detector to find — which would make the detector
    look better than it is.
    """
    if weeks < 1:
        raise ValueError("a trajectory needs at least one week")

    base: list[float]
    if direction is TrendDirection.EMERGING:
        base = [
            NOISE_FLOOR + (peak - NOISE_FLOOR) * (week / (weeks - 1 or 1)) for week in range(weeks)
        ]
    elif direction is TrendDirection.SUSTAINED:
        # Rises over the first third, then holds. Distinguishable from a
        # single spike, which is the point — a spike is a press mention, a
        # plateau is an evaluation.
        ramp = max(1, weeks // 3)
        base = [NOISE_FLOOR + (peak - NOISE_FLOOR) * min(1.0, week / ramp) for week in range(weeks)]
    elif direction is TrendDirection.DECAYING:
        base = [peak - (peak - NOISE_FLOOR) * (week / (weeks - 1 or 1)) for week in range(weeks)]
    elif direction is TrendDirection.REACTIVATED:
        # Rise, fall to baseline, rise again. The graph must recognise the
        # second rise as the same company returning, not a new prospect.
        third = max(1, weeks // 3)
        base = []
        for week in range(weeks):
            if week < third:
                base.append(NOISE_FLOOR + (peak - NOISE_FLOOR) * (week / third))
            elif week < 2 * third:
                base.append(peak - (peak - NOISE_FLOOR) * ((week - third) / third))
            else:
                base.append(NOISE_FLOOR + (peak - NOISE_FLOOR) * ((week - 2 * third) / third))
    else:
        base = [float(NOISE_FLOOR) for _ in range(weeks)]

    scores = tuple(
        max(0, min(SURGE_CEILING, round(value + rng.uniform(-noise, noise)))) for value in base
    )
    return TopicTrajectory(topic=topic, weekly_scores=scores, direction=direction)


class BomboraFixtureGenerator(PayloadGenerator):
    """Intent topics with weekly surge history and trend direction.

    Emits the **whole history**, not just the current week. A consumer
    given only today's score cannot distinguish a company at 71 on the way
    up from one at 71 on the way down — and those warrant opposite actions.
    """

    provider = "bombora"

    def render(self, event: ScenarioEvent) -> Mapping[str, Any]:
        facts = event.facts
        # Seeded from the event so the same event always yields the same
        # trajectory, and two events never share a generator's state.
        rng = random.Random(f"{event.event_ref}:{facts.get('_jitter', 0)}")  # noqa: S311

        declared: Sequence[Mapping[str, Any]] = facts.get("intent_topics", [])
        trajectories = [
            build_trajectory(
                topic=str(topic.get("topic", "unknown")),
                direction=TrendDirection(topic.get("direction", TrendDirection.EMERGING.value)),
                weeks=int(topic.get("weeks", 4)),
                peak=int(topic.get("peak", 80)),
                rng=rng,
            )
            for topic in declared
        ]

        return {
            "_fixture": _fixture_notice("Bombora"),
            "company_id": event.subject,
            "domain": facts.get("domain", "example.com"),
            "report_week": facts.get("report_week"),
            # Late reporting is normal for intent data and is expressed
            # here rather than by delaying delivery: the consumer must
            # handle a report describing weeks that have already passed.
            "reporting_lag_days": facts.get("reporting_lag_days", 0),
            "topics": [
                {
                    "topic": trajectory.topic,
                    "surge_score": trajectory.current,
                    "trend": trajectory.direction.value,
                    "weekly_history": list(trajectory.weekly_scores),
                    "above_noise_floor": trajectory.current > NOISE_FLOOR,
                }
                for trajectory in trajectories
            ],
        }

"""The detection rule contract.

**Taxonomy defines language; rules define derivation.** A rule may change
whenever a better derivation is found; what a hiring surge *means* must
not change with it. That is why parameters live in the taxonomy and only
the logic lives here.

**No rule may contain a business threshold.** Every number that decides
what counts is read from `Parameters`. A Security Invariant parses each
rule module as a syntax tree and fails on any numeric literal in a
comparison other than `0` or `1` — those two are structural (*nothing* and
*something*), while any other number is a claim about the world that
somebody must be able to argue with.

Rules are pure. They receive observations and parameters and return
detections; they perform no I/O, so the same evidence produces the same
conclusion on every machine and in any processing order.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol

from modules.business_event_engine.domain.taxonomy import BusinessEventType, Parameters
from modules.observation_engine.public import Observation


@dataclass(frozen=True, slots=True)
class Detection:
    """What a rule concluded, before it becomes a stored event.

    Deliberately not a `BusinessEvent`: the rule decides *what happened*,
    while identity, versioning, and supersession are the use case's
    concern. Keeping them apart is what lets a rule be tested with no
    database and no clock.
    """

    summary: str
    facts: dict[str, Any]
    occurred_at: datetime
    window_start: datetime
    window_end: datetime
    evidence: tuple[Observation, ...]

    @property
    def providers(self) -> tuple[str, ...]:
        return tuple(sorted({observation.provider for observation in self.evidence}))


class DetectionRule(Protocol):
    """One rule per type, and one type per rule.

    The pairing is asserted at load time: a declared type with no rule is a
    promise the product cannot keep, and a rule with no declaration is a
    threshold nobody reviewed.
    """

    detects: BusinessEventType

    def evaluate(
        self, series: tuple[Observation, ...], parameters: Parameters
    ) -> tuple[Detection, ...]:
        """Conclusions supported by **one provider's** observations.

        The series is always a single provider's, so no rule can combine
        two providers' values into a synthetic truth. Agreement between
        providers is counted afterwards, by the use case, from the
        detections each series produced independently.
        """
        ...


def window_of(observations: tuple[Observation, ...]) -> tuple[datetime, datetime]:
    """The interval the evidence actually supports.

    Starts at the earliest moment any evidence speaks to — the *previous*
    observed time where there is one — so a window is never narrower than
    the evidence behind it.
    """
    starts = [
        observation.previous_observed_at or observation.observed_at for observation in observations
    ]
    ends = [observation.observed_at for observation in observations]
    return min(starts), max(ends)

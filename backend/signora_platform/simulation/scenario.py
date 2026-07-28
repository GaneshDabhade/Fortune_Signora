"""The Scenario Engine — turns a dataset and a narrative into an ordered
sequence of provider events.

A dataset is the *cast*; a scenario is the *narrative*. Separating them
means the same companies can play different stories, and a corrected
dataset can be re-run against an unchanged story.

**Provider-agnostic by construction.** The engine names no provider and
knows nothing about payload shapes — a scenario step declares *which*
provider should emit and *what dataset fact* it concerns; rendering that
into a vendor shape belongs to a generator. This is what lets generators
land incrementally as providers qualify, with no change here (AC-20).

Deliberately small. The simulator is infrastructure, not product: this does
what is needed to produce deterministic, ordered, replayable event
sequences and nothing beyond it.
"""

from __future__ import annotations

import json
import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Final

from signora_platform.simulation.clock import VirtualClock
from signora_platform.simulation.dataset import Dataset

SCENARIO_ROOT: Final = Path(__file__).parent / "scenarios"


class ScenarioError(RuntimeError):
    """A scenario could not be loaded or is inconsistent with its dataset."""


@dataclass(frozen=True, slots=True)
class ScenarioEvent:
    """One provider event on the timeline.

    Not yet a payload — a generator renders this into a vendor shape. The
    separation is what keeps the engine provider-agnostic.

    ``sequence`` is the event's position in the scenario, stable across
    runs. It is what a downstream anomaly traces back to, and what seeds
    per-event randomness so a fault lands on the same event every run.
    """

    sequence: int
    provider: str
    subject: str
    occurred_at: datetime
    facts: Mapping[str, Any]

    @property
    def event_ref(self) -> str:
        """Stable identifier: `erp-replacement#3`. Recorded on every
        payload so an anomaly names the event that produced it."""
        return f"{self.provider}#{self.sequence}"


@dataclass(frozen=True, slots=True)
class ScenarioStep:
    """One declared step of a scenario definition."""

    provider: str
    subject: str
    #: Offset from the clock's epoch. Declaring an offset rather than
    #: advancing the clock is how a late or out-of-order event is
    #: expressed: its offset precedes events already emitted.
    offset: timedelta
    facts: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class Scenario:
    """A versioned narrative over a dataset."""

    name: str
    version: int
    dataset: str
    dataset_version: int
    steps: tuple[ScenarioStep, ...]

    @property
    def reference(self) -> str:
        return f"{self.name}@{self.version}"

    @property
    def providers(self) -> tuple[str, ...]:
        """Providers this scenario needs.

        A scenario runs with whichever of these are available; the rest are
        skipped. That is what stops one unqualified provider — Bombora in
        particular — blocking every scenario it appears in.
        """
        return tuple(sorted({step.provider for step in self.steps}))


def load(name: str, version: int, *, root: Path | None = None) -> Scenario:
    directory = root if root is not None else SCENARIO_ROOT
    path = directory / f"{name}@{version}.json"

    if not path.exists():
        available = sorted(p.stem for p in directory.glob(f"{name}@*.json"))
        raise ScenarioError(
            f"scenario '{name}@{version}' not found at {path}. Available: {available or 'none'}."
        )

    try:
        raw: Any = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ScenarioError(f"scenario '{name}@{version}' is not valid JSON: {exc}") from exc

    if not isinstance(raw, dict):
        raise ScenarioError(f"scenario '{name}@{version}' must be a JSON object")

    steps_raw = raw.get("steps")
    if not isinstance(steps_raw, list) or not steps_raw:
        # A scenario producing no events fails loudly. Silently emitting
        # nothing is indistinguishable from a pipeline that consumed
        # everything and produced nothing — an expensive ambiguity in
        # front of a customer.
        raise ScenarioError(f"scenario '{name}@{version}' declares no steps")

    steps = tuple(
        ScenarioStep(
            provider=str(step["provider"]),
            subject=str(step["subject"]),
            offset=timedelta(days=float(step.get("offset_days", 0))),
            facts=dict(step.get("facts", {})),
        )
        for step in steps_raw
    )

    return Scenario(
        name=name,
        version=version,
        dataset=str(raw["dataset"]),
        dataset_version=int(raw["dataset_version"]),
        steps=steps,
    )


def build_timeline(
    scenario: Scenario,
    dataset: Dataset,
    clock: VirtualClock,
    *,
    seed: int,
    providers: Sequence[str] | None = None,
) -> tuple[ScenarioEvent, ...]:
    """Render a scenario into an ordered event sequence.

    ``providers`` restricts the run to those available. Steps for absent
    providers are **skipped, not failed** — a scenario is a composition of
    providers, and one unqualified provider must not invalidate the rest
    of the narrative (principle 9).

    Determinism: given the same scenario, dataset, and seed, the sequence
    is identical. The seeded generator is created here and never at module
    scope, so two concurrent runs cannot consume each other's randomness.
    """
    if dataset.name != scenario.dataset or dataset.version != scenario.dataset_version:
        raise ScenarioError(
            f"scenario {scenario.reference} expects dataset "
            f"{scenario.dataset}@{scenario.dataset_version}, got {dataset.reference}"
        )

    available = None if providers is None else set(providers)
    rng = random.Random(seed)  # noqa: S311 - simulation, not cryptography
    events: list[ScenarioEvent] = []

    for step in scenario.steps:
        if available is not None and step.provider not in available:
            continue

        # Fails here rather than mid-run: a dangling entity reference is
        # otherwise discovered only when that scenario happens to execute.
        entity = dataset.entity(step.subject)

        events.append(
            ScenarioEvent(
                sequence=len(events),
                provider=step.provider,
                subject=step.subject,
                occurred_at=clock.at(step.offset),
                facts={**entity, **step.facts, "_jitter": rng.random()},
            )
        )

    if not events:
        raise ScenarioError(
            f"scenario {scenario.reference} produced no events for providers "
            f"{sorted(available) if available else 'all'}. Every declared provider is "
            "unavailable — check the qualification register."
        )

    # Sorted by logical time, not declaration order: a step declared later
    # may legitimately occur earlier, which is how late arrival is
    # expressed. The pipeline must tolerate receiving it out of order.
    return tuple(sorted(events, key=lambda event: (event.occurred_at, event.sequence)))

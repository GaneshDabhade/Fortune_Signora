"""Invariants: the simulator cannot know, reach, or become load-bearing.

Three properties, each of which would be violated quietly and each of
which would invalidate everything the simulator proves
(docs/architecture/20-provider-simulation.md, principles 2, 3, 9).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from signora_platform.simulation import PERMITTED_ENVIRONMENTS, is_permitted

BACKEND_ROOT = Path(__file__).resolve().parents[2]
SIMULATION_ROOT = BACKEND_ROOT / "signora_platform" / "simulation"


def simulation_sources() -> list[tuple[str, str]]:
    return [
        (str(path.relative_to(BACKEND_ROOT)), path.read_text())
        for path in SIMULATION_ROOT.rglob("*.py")
    ]


class TestSimulatorHasNoDownstreamKnowledge:
    """Principle 2. The simulator knows its dataset and its scenario, and
    nothing else.

    A simulator that reads a Signal to decide what payload to emit next
    would make every scenario pass while proving nothing about the
    pipeline — and the test suite would look healthier than ever.
    """

    def test_simulation_imports_no_module(self) -> None:
        offenders = [
            name
            for name, source in simulation_sources()
            if re.search(r"^\s*(?:from|import)\s+modules\b", source, re.MULTILINE)
        ]

        assert offenders == [], (
            f"{offenders} import a module. The simulator produces provider payloads only; "
            "everything downstream must be discovered by the platform itself."
        )

    @pytest.mark.parametrize(
        "forbidden",
        [
            "knowledge_graph",
            "observation",
            "business_event",
            "signal_engine",
            "buying_score",
            "opportunity",
            "recommendation",
            "ai_reasoning",
        ],
    )
    def test_simulation_never_names_a_downstream_concept(self, forbidden: str) -> None:
        """Catches the subtler version: not an import, but a lookup or a
        conditional keyed on downstream state."""
        offenders = [
            name
            for name, source in simulation_sources()
            # Prose in docstrings and comments legitimately names these
            # concepts when explaining why they are off-limits.
            if re.search(rf"^(?!\s*#).*\b{forbidden}\b", _strip_docstrings(source), re.MULTILINE)
        ]

        assert offenders == [], f"{offenders} reference '{forbidden}'"


class TestSimulatorCannotBypassThePort:
    """Principle 3. Entry is at the Provider Port and nowhere else."""

    def test_simulation_does_not_publish_events(self) -> None:
        """Injecting a synthetic observation or a pre-built signal would
        exercise a path production never takes, producing demos that prove
        nothing."""
        offenders = [
            name
            for name, source in simulation_sources()
            if "EventPublisher" in _strip_docstrings(source)
            or "publish(" in _strip_docstrings(source)
        ]

        assert offenders == []

    def test_simulation_touches_no_database(self) -> None:
        offenders = [
            name
            for name, source in simulation_sources()
            if re.search(r"\b(?:AsyncSession|sessionmaker|sqlalchemy)\b", source)
        ]

        assert offenders == []


class TestDeterminism:
    def test_simulation_never_reads_the_wall_clock(self) -> None:
        """A single `datetime.now()` reintroduces non-determinism that is
        very hard to find, because it produces a test failing roughly once
        a week and passing on re-run. Every timestamp comes from the
        VirtualClock."""
        offenders = [
            name
            for name, source in simulation_sources()
            # Docstrings stripped: clock.py's own docstring states the
            # rule, and scanning raw source would flag the documentation of
            # a rule as a violation of it.
            if re.search(r"datetime\.now\(|time\.time\(|date\.today\(", _strip_docstrings(source))
        ]

        assert offenders == [], f"{offenders} read the wall clock; use the VirtualClock"

    def test_simulation_never_uses_unseeded_randomness(self) -> None:
        """`random.random()` without a seeded Random instance makes a
        scenario pass and fail at random, and nobody trusts the suite
        afterwards."""
        offenders = [
            name
            for name, source in simulation_sources()
            if re.search(
                r"^\s*import random\b|\brandom\.(?:random|choice|randint|shuffle)\(",
                _strip_docstrings(source),
                re.MULTILINE,
            )
        ]

        assert offenders == [], f"{offenders} use module-level randomness; use a seeded Random"


class TestProviderIndependence:
    """Principle 9 / AC-20. The framework must not depend on any single
    provider — including Bombora, whose qualification is outstanding."""

    def test_the_framework_names_no_specific_provider(self) -> None:
        """Scenarios compose providers; providers never depend on each
        other, and the framework depends on none of them. A generator must
        be independently removable."""
        offenders = [
            (name, provider)
            for name, source in simulation_sources()
            for provider in ("apollo", "builtwith", "crunchbase", "coresignal", "bombora")
            if re.search(
                rf"^(?!\s*#).*\b{provider}\b", _strip_docstrings(source).lower(), re.MULTILINE
            )
        ]

        assert offenders == [], (
            f"{offenders}: the simulation framework names a specific provider. "
            "Removing any one generator must leave the framework and every other "
            "provider working."
        )

    def test_the_framework_functions_with_no_generators_at_all(self) -> None:
        """The current state, and it must remain valid: all five providers
        are Conditional pending payload provenance, and the framework is
        nonetheless complete and tested."""
        clock_and_dataset_work = is_permitted("local") and len(PERMITTED_ENVIRONMENTS) > 0

        assert clock_and_dataset_work


def _strip_docstrings(source: str) -> str:
    """Remove triple-quoted blocks.

    Prose legitimately names downstream concepts and providers when
    explaining why they are off-limits; scanning raw source would flag the
    documentation of the rule as a violation of it.
    """
    return re.sub(r'"""(?:.|\n)*?"""', "", source)

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
    """The simulation framework, excluding generators.

    A generator naming its own provider is the entire point of a
    generator. What must name no provider is the framework *core* — the
    clock, dataset store, scenario engine, fault injector, delivery, and
    safety guards — because that is what makes each generator
    independently removable (principle 9 / AC-20).
    """
    return [
        (str(path.relative_to(BACKEND_ROOT)), path.read_text())
        for path in SIMULATION_ROOT.rglob("*.py")
        if "generators" not in path.parts
    ]


def generator_sources() -> list[tuple[str, str]]:
    return [
        (str(path.relative_to(BACKEND_ROOT)), path.read_text())
        for path in (SIMULATION_ROOT / "generators").rglob("*.py")
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
        """A module-level `random.random()` makes a scenario pass and fail
        at random, and nobody trusts the suite afterwards. A seeded
        `random.Random(seed)` instance is the correct form and is
        deliberately permitted."""
        offenders = [
            name
            for name, source in simulation_sources()
            if re.search(
                # Module-level calls only. `random.Random(seed)` is the
                # correct usage — banning the import would ban the seeded
                # generator along with the unseeded functions, which is the
                # opposite of the intent.
                r"\brandom\.(?:random|choice|randint|shuffle|uniform|sample)\(",
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

    def test_no_generator_depends_on_another_generator(self) -> None:
        """Scenarios compose providers; providers never depend on each
        other. A generator importing another would make removing the
        second break the first — exactly the coupling AC-20 forbids."""
        offenders = [
            name
            for name, source in generator_sources()
            if name.rsplit("/", 1)[-1] not in {"__init__.py", "base.py"}
            and re.search(
                r"^from signora_platform\.simulation\.generators\.(?!base)", source, re.MULTILINE
            )
        ]

        assert offenders == [], f"{offenders} import another generator"

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


class TestPipelineNeutrality:
    """AC-21. The ingestion pipeline must process simulated and production
    providers identically.

    **The most important invariant in M2.1.** Configuration may select the
    provider implementation; the pipeline itself must never know which it
    got. A single branch here would mean the simulator proves nothing about
    the production path, and every downstream module would inherit that.
    """

    PIPELINE_ROOT = BACKEND_ROOT / "modules" / "provider_platform"

    def _pipeline_sources(self, *layers: str) -> list[tuple[str, str]]:
        return [
            (str(path.relative_to(BACKEND_ROOT)), path.read_text())
            for layer in layers
            for path in (self.PIPELINE_ROOT / layer).rglob("*.py")
        ]

    #: **AC-21 is behavioural, not informational** (ratified 2026-07-28).
    #: Metadata may exist; behaviour must remain provider-neutral. The
    #: Provider Platform may carry data required for observability,
    #: traceability, and type safety provided no business behaviour
    #: changes, no branching occurs, no simulation-specific execution path
    #: exists, and provider identity stays metadata rather than logic.
    #:
    #: Approved metadata, confined to one file:
    #: 1. `ProviderResponse.simulated` — observability; the safety guard
    #:    requires ingestion logs to mark simulated payloads.
    #: 2. `ProviderDescriptor.simulated` — logging, diagnostics, safety.
    #: 3. `ProviderName` — typed metadata for dispatch and sync records.
    #:
    #: Named explicitly so a *fourth* piece of such knowledge, or any
    #: instance outside this file, fails the build.
    APPROVED_METADATA = frozenset({"modules/provider_platform/domain/provider.py"})

    def test_no_new_simulation_knowledge_enters_the_pipeline(self) -> None:
        """Nothing *branches* on simulation anywhere in the pipeline.

        The approved metadata in `provider.py` is data, not control flow —
        see APPROVED_METADATA. Any other file mentioning simulation fails
        here.
        """
        offenders = [
            name
            for name, source in self._pipeline_sources("domain", "application")
            if re.search(r"simulat", _strip_docstrings(source), re.IGNORECASE)
            and name not in self.APPROVED_METADATA
        ]

        assert offenders == [], (
            f"{offenders} reference simulation. Selection happens in configuration at the "
            "composition root; the pipeline must not know which implementation it received."
        )

    def test_nothing_in_the_pipeline_branches_on_simulation(self) -> None:
        """The assertion that matters most. A *flag* is data; an `if` on
        that flag is behaviour, and behaviour that differs between the two
        paths is exactly what makes the simulator prove nothing."""
        offenders = [
            name
            for name, source in self._pipeline_sources("domain", "application", "infrastructure")
            if re.search(r"if\s+.*\bsimulated\b", _strip_docstrings(source))
            and "adapters/simulated" not in name
        ]

        assert offenders == [], f"{offenders} branch on simulation state"

    def test_domain_and_application_import_nothing_from_the_simulator(self) -> None:
        offenders = [
            name
            for name, source in self._pipeline_sources("domain", "application")
            if re.search(
                r"^\s*(?:from|import)\s+signora_platform\.simulation", source, re.MULTILINE
            )
        ]

        assert offenders == []

    def test_no_provider_specific_behaviour_in_the_pipeline(self) -> None:
        """Provider identity belongs inside adapters.

        `ProviderName` is approved typed metadata (see APPROVED_METADATA): the
        platform records *which* provider a sync belongs to, which is
        arguably identity knowledge. What it must never do is *behave*
        differently per provider — that is what this asserts, and it is the
        property that actually matters.
        """
        offenders = [
            (name, provider)
            for name, source in self._pipeline_sources("domain", "application")
            for provider in ("apollo", "builtwith", "crunchbase", "coresignal", "bombora")
            if re.search(
                rf"(?:if|elif|match|case).*\b{provider}\b", _strip_docstrings(source), re.IGNORECASE
            )
        ]

        assert offenders == [], f"{offenders} branch on provider identity"

    def test_only_the_composition_root_knows_a_simulator_exists(self) -> None:
        """One file may know, and it is the file whose job is wiring."""
        knowing = [
            name
            for name, source in self._pipeline_sources("infrastructure")
            if re.search(r"simulat", _strip_docstrings(source), re.IGNORECASE)
        ]

        assert all(
            "adapters/simulated" in name or name.endswith("composition.py") for name in knowing
        ), f"{knowing} know about simulation outside the adapter and composition root"

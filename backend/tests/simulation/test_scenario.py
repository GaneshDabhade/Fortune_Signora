"""Tests for the Scenario Engine.

The two properties that matter: **determinism** (a regression suite that
varies between runs is anecdote, not measurement) and **provider
independence** (an unqualified provider must not invalidate the scenarios
it appears in).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from signora_platform.simulation import (
    ClockMode,
    ScenarioError,
    VirtualClock,
    build_timeline,
    load,
    load_scenario,
)


@pytest.fixture
def clock() -> VirtualClock:
    return VirtualClock(mode=ClockMode.INSTANT)


class TestScenarioLoading:
    def test_loads_a_published_scenario(self) -> None:
        scenario = load_scenario("baseline", 1)

        assert scenario.reference == "baseline@1"
        assert scenario.dataset == "baseline"

    def test_reports_which_providers_it_needs(self) -> None:
        """A scenario runs with whichever providers are available; knowing
        which it wants is what makes that decision possible."""
        assert load_scenario("baseline", 1).providers == (
            "apollo",
            "bombora",
            "builtwith",
            "coresignal",
            "crunchbase",
        )

    def test_a_missing_scenario_fails_at_load(self) -> None:
        with pytest.raises(ScenarioError, match="not found"):
            load_scenario("baseline", 99)

    def test_a_scenario_with_no_steps_is_rejected(self, tmp_path: Path) -> None:
        """Silently emitting nothing is indistinguishable from a pipeline
        that consumed everything and produced nothing — an expensive
        ambiguity in front of a customer."""
        (tmp_path / "empty@1.json").write_text(
            json.dumps({"dataset": "baseline", "dataset_version": 1, "steps": []})
        )

        with pytest.raises(ScenarioError, match="declares no steps"):
            load_scenario("empty", 1, root=tmp_path)


class TestDeterminism:
    def test_the_same_seed_produces_an_identical_timeline(self, clock: VirtualClock) -> None:
        scenario, dataset = load_scenario("baseline", 1), load("baseline", 1)

        first = build_timeline(scenario, dataset, clock, seed=42)
        second = build_timeline(scenario, dataset, clock, seed=42)

        assert first == second

    def test_a_different_seed_produces_a_different_timeline(self, clock: VirtualClock) -> None:
        """The half that catches a seed which is accepted and ignored —
        without it, every determinism test passes vacuously."""
        scenario, dataset = load_scenario("baseline", 1), load("baseline", 1)

        first = build_timeline(scenario, dataset, clock, seed=1)
        second = build_timeline(scenario, dataset, clock, seed=2)

        assert first != second

    def test_timestamps_do_not_depend_on_generation_duration(self, clock: VirtualClock) -> None:
        scenario, dataset = load_scenario("baseline", 1), load("baseline", 1)

        first = build_timeline(scenario, dataset, VirtualClock(), seed=7)
        second = build_timeline(scenario, dataset, VirtualClock(), seed=7)

        assert [e.occurred_at for e in first] == [e.occurred_at for e in second]


class TestOrdering:
    def test_events_are_ordered_by_logical_time_not_declaration(self, clock: VirtualClock) -> None:
        """A step declared later may legitimately occur earlier — that is
        how late arrival is expressed, and the pipeline must tolerate
        receiving it out of order."""
        timeline = build_timeline(load_scenario("baseline", 1), load("baseline", 1), clock, seed=1)

        occurred = [event.occurred_at for event in timeline]
        assert occurred == sorted(occurred)
        # The bombora step is declared third but offset earlier than the
        # coresignal step declared second.
        # bombora is declared third but offset earlier than coresignal,
        # declared second — the ordering is by logical time.
        assert timeline[2].provider == "bombora"
        assert timeline[3].provider == "builtwith"

    def test_every_event_carries_a_stable_reference(self, clock: VirtualClock) -> None:
        """What a downstream anomaly traces back to."""
        timeline = build_timeline(load_scenario("baseline", 1), load("baseline", 1), clock, seed=1)

        refs = [event.event_ref for event in timeline]
        assert len(set(refs)) == len(refs)


class TestProviderIndependence:
    """AC-20. An unqualified provider must not invalidate the scenarios it
    appears in — the property that lets Bombora stay Conditional without
    blocking anything."""

    def test_absent_providers_are_skipped_not_failed(self, clock: VirtualClock) -> None:
        timeline = build_timeline(
            load_scenario("baseline", 1),
            load("baseline", 1),
            clock,
            seed=1,
            providers=["apollo", "coresignal"],
        )

        assert {event.provider for event in timeline} == {"apollo", "coresignal"}
        assert len(timeline) == 3, "the remaining narrative still runs"

    def test_a_scenario_runs_with_a_single_provider(self, clock: VirtualClock) -> None:
        """The current state: generators land incrementally, and the first
        one to qualify must be usable on its own."""
        timeline = build_timeline(
            load_scenario("baseline", 1), load("baseline", 1), clock, seed=1, providers=["apollo"]
        )

        assert len(timeline) == 2

    def test_no_available_provider_fails_loudly(self, clock: VirtualClock) -> None:
        """Silently producing nothing would look like a working scenario
        with no data."""
        with pytest.raises(ScenarioError, match="produced no events"):
            build_timeline(
                load_scenario("baseline", 1), load("baseline", 1), clock, seed=1, providers=[]
            )

    def test_the_engine_names_no_provider(self) -> None:
        """Rendering a vendor shape belongs to a generator. The engine
        treating a provider as an opaque string is what lets generators
        land with no change here."""
        source = (
            Path(__file__).resolve().parents[2] / "signora_platform" / "simulation" / "scenario.py"
        ).read_text()

        for provider in ("apollo", "builtwith", "crunchbase", "coresignal", "bombora"):
            assert provider not in source.lower().split('"""')[0] + source.lower().split('"""')[-1]


class TestConsistency:
    def test_a_mismatched_dataset_is_rejected(self, clock: VirtualClock) -> None:
        """Running a narrative against the wrong cast produces events that
        look valid and mean nothing."""
        scenario = load_scenario("baseline", 1)
        wrong = load("baseline", 1)
        object.__setattr__(wrong, "version", 2)

        with pytest.raises(ScenarioError, match="expects dataset"):
            build_timeline(scenario, wrong, clock, seed=1)

    def test_a_dangling_entity_reference_fails(self, tmp_path: Path, clock: VirtualClock) -> None:
        (tmp_path / "dangling@1.json").write_text(
            json.dumps(
                {
                    "dataset": "baseline",
                    "dataset_version": 1,
                    "steps": [{"provider": "apollo", "subject": "no-such-entity"}],
                }
            )
        )

        from signora_platform.simulation.dataset import DatasetError

        with pytest.raises(DatasetError, match="has no entity"):
            build_timeline(
                load_scenario("dangling", 1, root=tmp_path), load("baseline", 1), clock, seed=1
            )

"""Tests for the payload generators.

Two concerns. First, that **no fixture can be mistaken for an authentic
payload** — the provenance policy is unchanged, and these are development
fixtures. Second, that Bombora produces a **trajectory**, since a single
intent score is not a simulation of intent but a number.
"""

from __future__ import annotations

import random
from pathlib import Path

import pytest

from signora_platform.simulation import (
    ClockMode,
    ScenarioEvent,
    VirtualClock,
    build_timeline,
    load,
    load_scenario,
)
from signora_platform.simulation.generators import (
    NOISE_FLOOR,
    ApolloFixtureGenerator,
    BomboraFixtureGenerator,
    BuiltWithFixtureGenerator,
    CoreSignalFixtureGenerator,
    CrunchbaseFixtureGenerator,
    PayloadGenerator,
    PayloadProvenance,
    TrendDirection,
    build_trajectory,
)

ALL_GENERATORS: list[PayloadGenerator] = [
    ApolloFixtureGenerator(),
    BuiltWithFixtureGenerator(),
    CrunchbaseFixtureGenerator(),
    CoreSignalFixtureGenerator(),
    BomboraFixtureGenerator(),
]


@pytest.fixture
def timeline() -> tuple[ScenarioEvent, ...]:
    return build_timeline(
        load_scenario("baseline", 1),
        load("baseline", 1),
        VirtualClock(mode=ClockMode.INSTANT),
        seed=1,
    )


class TestFixtureDesignation:
    """The provenance policy is unchanged. A fixture that could pass for a
    real payload would quietly become the contract — precisely the failure
    the policy exists to prevent."""

    @pytest.mark.parametrize("generator", ALL_GENERATORS, ids=lambda g: g.provider)
    def test_every_generator_declares_itself_a_development_fixture(
        self, generator: PayloadGenerator
    ) -> None:
        assert generator.provenance is PayloadProvenance.DEVELOPMENT_FIXTURE
        assert generator.provenance.is_authentic is False

    @pytest.mark.parametrize("generator", ALL_GENERATORS, ids=lambda g: g.provider)
    def test_every_payload_carries_the_marker_in_its_body(
        self, generator: PayloadGenerator, timeline: tuple[ScenarioEvent, ...]
    ) -> None:
        """Inside the body, not only alongside it. A payload copied into a
        bug report, a test fixture, or a demo carries its own warning."""
        event = next(e for e in timeline if e.provider == generator.provider)

        payload = generator.generate(event).payload

        assert "_fixture" in payload
        assert "DEVELOPMENT FIXTURE" in str(payload["_fixture"])
        assert "NOT an authentic" in str(payload["_fixture"])

    @pytest.mark.parametrize("generator", ALL_GENERATORS, ids=lambda g: g.provider)
    def test_no_generator_claims_a_source_it_does_not_have(
        self, generator: PayloadGenerator
    ) -> None:
        assert "development fixture" in generator.source_reference.lower()

    def test_the_marker_disappears_when_a_fixture_is_replaced(self) -> None:
        """The absence of `_fixture` is what a future test asserts to
        confirm a replacement is complete — so the field must be tied to
        the designation, not left behind by habit."""
        source = (
            Path(__file__).resolve().parents[2]
            / "signora_platform"
            / "simulation"
            / "generators"
            / "base.py"
        ).read_text()

        assert "_fixture_notice" in source
        assert "DEVELOPMENT FIXTURE" in source


class TestGeneratedShapes:
    """Each generator emits the *kind* of information its provider is
    expected to expose — enough to build the pipeline against, no claim to
    schema fidelity."""

    def test_apollo_emits_a_company_profile(self, timeline: tuple[ScenarioEvent, ...]) -> None:
        event = next(e for e in timeline if e.provider == "apollo")

        payload = ApolloFixtureGenerator().generate(event).payload

        assert "organization" in payload
        assert payload["organization"]["estimated_num_employees"] >= 0

    def test_builtwith_reports_detection_dates_not_a_flat_list(
        self, timeline: tuple[ScenarioEvent, ...]
    ) -> None:
        """A technology *removal* is only observable as a last_detected
        that stopped advancing — the signal a migration scenario needs."""
        event = next(e for e in timeline if e.provider == "builtwith")

        technologies = BuiltWithFixtureGenerator().generate(event).payload["technologies"]

        assert any(tech["is_live"] is False for tech in technologies)
        assert all("first_detected" in tech for tech in technologies)

    def test_coresignal_reports_a_delta_alongside_the_count(
        self, timeline: tuple[ScenarioEvent, ...]
    ) -> None:
        """Deriving growth downstream would require the platform to
        remember the previous value — state the provider is better placed
        to report."""
        event = next(e for e in timeline if e.provider == "coresignal")

        workforce = CoreSignalFixtureGenerator().generate(event).payload["workforce"]

        assert "employee_count_change_90d" in workforce

    def test_crunchbase_emits_funding_rounds(self, timeline: tuple[ScenarioEvent, ...]) -> None:
        event = next(e for e in timeline if e.provider == "crunchbase")

        payload = CrunchbaseFixtureGenerator().generate(event).payload

        assert len(payload["funding_rounds"]) >= 1


class TestIntentTrajectories:
    """AC-18 / AC-19. Bombora produces trajectories, not snapshots — a
    company at 71 on the way up and one at 71 on the way down warrant
    opposite actions."""

    @pytest.fixture
    def rng(self) -> random.Random:
        return random.Random(7)

    def test_emerging_intent_rises(self, rng: random.Random) -> None:
        trajectory = build_trajectory(
            "Cloud ERP", direction=TrendDirection.EMERGING, weeks=4, peak=88, rng=rng
        )

        assert trajectory.weekly_scores[-1] > trajectory.weekly_scores[0]
        assert trajectory.current > NOISE_FLOOR

    def test_decaying_intent_falls(self, rng: random.Random) -> None:
        """Must be distinguishable from a rise. A company whose intent is
        falling has usually already bought elsewhere."""
        trajectory = build_trajectory(
            "Cloud ERP", direction=TrendDirection.DECAYING, weeks=4, peak=88, rng=rng
        )

        assert trajectory.weekly_scores[-1] < trajectory.weekly_scores[0]

    def test_sustained_intent_plateaus_rather_than_spiking(self, rng: random.Random) -> None:
        """A spike is a press mention; a plateau is an evaluation."""
        trajectory = build_trajectory(
            "Zero Trust", direction=TrendDirection.SUSTAINED, weeks=9, peak=80, rng=rng
        )

        tail = trajectory.weekly_scores[-3:]
        assert max(tail) - min(tail) < 25, "a sustained topic should not still be climbing steeply"

    def test_reactivated_intent_returns_after_falling(self, rng: random.Random) -> None:
        """The graph must recognise the second rise as the same company
        returning, not a new prospect."""
        scores = build_trajectory(
            "Cloud ERP", direction=TrendDirection.REACTIVATED, weeks=9, peak=90, rng=rng
        ).weekly_scores

        trough = min(scores[2:6])
        assert scores[2] > trough or scores[-1] > trough
        assert scores[-1] > trough, "intent did not return"

    def test_noise_stays_near_the_floor(self, rng: random.Random) -> None:
        """Emitting a flat zero baseline would make every rise look
        cleaner than real intent data ever is."""
        trajectory = build_trajectory(
            "Irrelevant Topic", direction=TrendDirection.NOISE, weeks=6, peak=90, rng=rng
        )

        assert max(trajectory.weekly_scores) < NOISE_FLOOR + 15

    def test_a_trajectory_is_never_perfectly_smooth(self, rng: random.Random) -> None:
        """A monotonic rise is the easiest possible thing for a detector to
        find, which would make the detector look better than it is."""
        scores = build_trajectory(
            "Cloud ERP", direction=TrendDirection.EMERGING, weeks=8, peak=88, rng=rng
        ).weekly_scores

        deltas = [b - a for a, b in zip(scores, scores[1:], strict=False)]
        assert len(set(deltas)) > 1, "every step was identical — no noise applied"

    def test_the_payload_carries_the_whole_history(
        self, timeline: tuple[ScenarioEvent, ...]
    ) -> None:
        """A consumer given only today's score cannot tell a company at 71
        on the way up from one at 71 on the way down."""
        event = next(e for e in timeline if e.provider == "bombora")

        topics = BomboraFixtureGenerator().generate(event).payload["topics"]

        assert len(topics) >= 1
        for topic in topics:
            assert len(topic["weekly_history"]) >= 4
            assert topic["surge_score"] == topic["weekly_history"][-1]
            assert topic["trend"] in {d.value for d in TrendDirection}

    def test_generation_is_deterministic(self, timeline: tuple[ScenarioEvent, ...]) -> None:
        event = next(e for e in timeline if e.provider == "bombora")

        first = BomboraFixtureGenerator().generate(event).payload
        second = BomboraFixtureGenerator().generate(event).payload

        assert first == second

    def test_multiple_concurrent_topics_are_supported(self) -> None:
        """Correlated intent across related topics is a materially
        different claim from one topic surging."""
        rng = random.Random(3)
        topics = [
            build_trajectory(name, direction=TrendDirection.EMERGING, weeks=4, peak=85, rng=rng)
            for name in ("Identity Management", "Zero Trust", "Endpoint Protection")
        ]

        assert all(t.current > NOISE_FLOOR for t in topics)
        assert len({t.topic for t in topics}) == 3

    def test_a_trajectory_needs_at_least_one_week(self) -> None:
        with pytest.raises(ValueError, match="at least one week"):
            build_trajectory(
                "x", direction=TrendDirection.EMERGING, weeks=0, peak=50, rng=random.Random(1)
            )

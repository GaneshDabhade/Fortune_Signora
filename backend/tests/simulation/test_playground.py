"""The Product Playground — twelve shapes, not twelve rows.

**Design decisions made against two accounts are unfalsifiable.** Until this
existed, every hierarchy, density and grouping judgement in the product was made
against a list that could not exercise any of them, and the standing caveat on
every prompt evaluation in the repository was *"two cases, one shape"*.

These tests keep the Playground worth trusting: that it is genuinely varied,
that nothing in it can be mistaken for a real company, and that it stays the
*one* source of truth rather than drifting into a second fixture set.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from signora_platform.simulation import dataset as dataset_module
from signora_platform.simulation import scenario as scenario_module

SCENARIO = "playground"
VERSION = 1

#: The stories the Playground exists to tell. Named here rather than counted,
#: because "twelve accounts" is a number and "twelve *shapes*" is the point —
#: a scenario that grew four more copies of the same story would still pass a
#: count and would answer no new design question.
SHAPES = {
    "northwind-logistics": "technology migration — the textbook displacement",
    "contoso-health": "executive hiring surge",
    "fabrikam-industrial": "provider disagreement — two sources, two legal names",
    "tailwind-freight": "acquisition",
    "proseware-analytics": "rapid growth — every indicator moving together",
    "adventure-outdoor": "stale evidence",
    "litware-payments": "false positive — loud intent, nothing beneath it",
    "wingtip-media": "the silent account",
    "coho-vineyards": "rebranding mid-cycle",
    "relecloud-infra": "contested — opposing readings, both live",
    "vanarsdel-retail": "the slow burn",
    "lamna-legal": "cooling",
}


@pytest.fixture(scope="module")
def scenario() -> scenario_module.Scenario:
    return scenario_module.load(SCENARIO, VERSION)


@pytest.fixture(scope="module")
def cast() -> dataset_module.Dataset:
    return dataset_module.load(SCENARIO, VERSION)


class TestThePlaygroundIsVariedEnoughToDesignAgainst:
    def test_it_holds_every_shape_it_claims(
        self, scenario: scenario_module.Scenario
    ) -> None:
        assert {step.subject for step in scenario.steps} == set(SHAPES)

    def test_it_is_large_enough_that_a_list_must_be_scanned(
        self, scenario: scenario_module.Scenario
    ) -> None:
        """**Never design for two rows.** Twelve is the smallest number at
        which ranking and grouping give visibly different answers, and at which
        a row that reads well alone can still read badly in a column."""
        assert len({step.subject for step in scenario.steps}) >= 12

    def test_no_two_accounts_are_told_by_the_same_providers(
        self, scenario: scenario_module.Scenario
    ) -> None:
        """Variety means *different evidence*, not different names. Twelve
        accounts each described by the same three providers would be one shape
        twelve times, and would answer nothing the baseline scenario does not."""
        by_account: dict[str, set[str]] = {}
        for step in scenario.steps:
            by_account.setdefault(step.subject, set()).add(step.provider)

        distinct = {frozenset(providers) for providers in by_account.values()}
        assert len(distinct) >= 5, "the accounts differ in name and not in evidence"

    def test_every_provider_with_a_generator_is_exercised(
        self, scenario: scenario_module.Scenario
    ) -> None:
        """A demo that never emits a provider leaves that path unreviewed."""
        assert set(scenario.providers) == {
            "apollo",
            "bombora",
            "builtwith",
            "coresignal",
            "crunchbase",
        }

    def test_the_evidence_spans_a_period_rather_than_one_instant(
        self, scenario: scenario_module.Scenario
    ) -> None:
        """Freshness, cooling and staleness are all *temporal*. A scenario
        emitting everything on day zero cannot produce any of them, and the
        interface has three states that would never be seen."""
        offsets = {step.offset.days for step in scenario.steps}

        assert max(offsets) - min(offsets) >= 21


class TestNothingHereCanBeMistakenForARealCompany:
    def test_every_domain_is_reserved_and_cannot_resolve(
        self, cast: dataset_module.Dataset
    ) -> None:
        """RFC 2606 reserves `.example` precisely so it never resolves.

        **Fabricated buying signals attached to a real company are
        indistinguishable from real ones in a screenshot**, and a demo that
        could be read as a claim about somebody's business is a liability
        rather than an asset.
        """
        for key in SHAPES:
            assert cast.entity(key)["domain"].endswith(".example")

    def test_the_dataset_says_plainly_that_it_is_fictional(self) -> None:
        raw = json.loads(
            (
                Path(dataset_module.DATASET_ROOT) / f"{SCENARIO}@{VERSION}.json"
            ).read_text()
        )

        assert "FICTIONAL" in raw["_comment"]

    def test_it_names_no_real_company(self, cast: dataset_module.Dataset) -> None:
        """A guard rather than a habit. The convention is deliberate — these
        are the placeholder names Microsoft ships in its own sample data — and
        a future contributor reaching for a recognisable brand fails here."""
        real = {
            "microsoft",
            "salesforce",
            "stripe",
            "nvidia",
            "snowflake",
            "databricks",
            "atlassian",
            "hubspot",
            "google",
            "amazon",
            "oracle",
            "sap",
        }
        named = " ".join(cast.entity(key)["name"].lower() for key in SHAPES)

        assert not any(brand in named for brand in real)


class TestItStaysOneSourceOfTruth:
    def test_it_lives_in_the_framework_that_already_owns_scenarios(self) -> None:
        """**Not a parallel seeder.** The Provider Simulation Framework owns
        scenarios, the seeded determinism, the fault injector and the
        provenance fields; a second seeding system beside it would split all
        four across two owners."""
        assert (Path(scenario_module.SCENARIO_ROOT) / f"{SCENARIO}@{VERSION}.json").exists()
        assert (Path(dataset_module.DATASET_ROOT) / f"{SCENARIO}@{VERSION}.json").exists()

    def test_the_cast_is_immutable_once_published(
        self, cast: dataset_module.Dataset, tmp_path: Path
    ) -> None:
        """Editing a published dataset invalidates every result recorded
        against it. A correction is a new version."""
        raw = json.loads(
            (Path(dataset_module.DATASET_ROOT) / f"{SCENARIO}@{VERSION}.json").read_text()
        )
        raw["entities"]["lamna-legal"]["name"] = "Edited After Publication"
        (tmp_path / f"{SCENARIO}@{VERSION}.json").write_text(json.dumps(raw))

        with pytest.raises(dataset_module.DatasetError, match="content hash mismatch"):
            dataset_module.load(SCENARIO, VERSION, root=tmp_path)

    def test_running_it_twice_produces_the_same_timeline(
        self, scenario: scenario_module.Scenario, cast: dataset_module.Dataset
    ) -> None:
        """Determinism is what lets a design review, an AI evaluation and a
        demo all cite the same run. Asserted by comparing timelines rather than
        by inspection."""
        from signora_platform.simulation.clock import VirtualClock

        def timeline() -> list[str]:
            return [
                event.event_ref
                for event in scenario_module.build_timeline(
                    scenario, cast, VirtualClock(), seed=1701
                )
            ]

        assert timeline() == timeline()

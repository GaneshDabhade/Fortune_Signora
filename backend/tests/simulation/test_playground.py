"""The Product Playground — twelve business stories, not twelve rows.

**Design decisions made against two accounts are unfalsifiable.** Until this
existed, every hierarchy, density and grouping judgement in the product was made
against a list that could not exercise any of them, and the standing caveat on
every prompt evaluation in the repository was *"two cases, one shape"*.

These tests keep the Playground worth trusting: that it is genuinely varied,
that it declares what is invented, that it exercises the identity states the
product can render, and that it stays the *one* source of truth rather than
drifting into a second fixture set.

**`playground@1` is not deleted and not edited.** It remains in the repository
as the version earlier runs cite. It is superseded rather than corrected,
because a published dataset is immutable and every result recorded against it
would otherwise become meaningless (D17).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from signora_platform.simulation import dataset as dataset_module
from signora_platform.simulation import scenario as scenario_module

SCENARIO = "playground"
VERSION = 2

#: The business stories the Playground exists to tell. Named here rather than
#: counted, because "twelve accounts" is a number and "twelve *stories*" is the
#: point — a scenario that grew four more copies of one story would still pass a
#: count and would answer no new design question.
STORIES = {
    "snowflake": "acquisition, and a live evaluation beside it",
    "databricks": "funding closed, and the hiring that follows one",
    "nvidia": "expansion on two independent fronts",
    "hubspot": "marketing stack replaced — evidence now recent, not fresh",
    "atlassian": "a security initiative, named by a single source",
    "salesforce": "a new revenue leader",
    "stripe": "cutting headcount while evaluating — contested",
    "adobe": "ERP replacement whose evidence has aged, under a disputed name",
    "mongodb": "an evaluation that has just passed its shelf life",
    "twilio": "the CFO departed",
    "datadog": "a reduction, with nothing pulling the other way",
    "figma": "behavioural intent and nothing else — nobody names it",
}


@pytest.fixture(scope="module")
def scenario() -> scenario_module.Scenario:
    return scenario_module.load(SCENARIO, VERSION)


@pytest.fixture(scope="module")
def cast() -> dataset_module.Dataset:
    return dataset_module.load(SCENARIO, VERSION)


def _raw(kind: str) -> dict[str, Any]:
    """The file as written, before the loaders interpret it.

    Some of what these tests assert — the fictional-stories notice, the absence
    of a date — is about the *artifact*, not about the object it produces, and
    reading the loaded form would not see it.
    """
    root = dataset_module.DATASET_ROOT if kind == "dataset" else scenario_module.SCENARIO_ROOT
    loaded: dict[str, Any] = json.loads(
        (Path(root) / f"{SCENARIO}@{VERSION}.json").read_text()
    )
    return loaded


class TestItIsVariedEnoughToDesignAgainst:
    def test_it_holds_every_story_it_claims(
        self, scenario: scenario_module.Scenario
    ) -> None:
        assert {step.subject for step in scenario.steps} == set(STORIES)

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
        accounts each described by the same three providers would be one story
        twelve times."""
        by_account: dict[str, set[str]] = {}
        for step in scenario.steps:
            by_account.setdefault(step.subject, set()).add(step.provider)

        assert len({frozenset(p) for p in by_account.values()}) >= 6, (
            "the accounts differ in name and not in evidence"
        )

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

    def test_the_evidence_spans_months_rather_than_one_instant(
        self, scenario: scenario_module.Scenario
    ) -> None:
        """**Freshness must vary on its own.**

        Every temporal state the product can render — current, ageing, cooling,
        stale — is the band arithmetic applied to *when the evidence happened*.
        A scenario emitting everything at once cannot produce any of them, and
        four interface states would never be seen. The shortest relevance
        window in the catalog is 90 days, so the span has to exceed it or
        nothing can ever expire (D17).
        """
        offsets = {step.offset.days for step in scenario.steps}

        assert max(offsets) - min(offsets) > 90

    def test_the_narrative_declares_no_date_of_its_own(self) -> None:
        """**A scenario says when things happened relative to each other, never
        when it is being told.** Anchoring belongs to whoever runs it — the same
        story is today's book or a historical replay depending only on the
        epoch, and a date baked in here is what made `playground@1` demonstrate
        seven-month-old evidence (D17)."""
        raw = _raw("scenario")

        assert "epoch" not in raw
        assert "horizon_days" not in raw


class TestNothingHereIsPresentedAsFact:
    """**The companies are real; every business event about them is invented.**

    Real names are used because a revenue-intelligence demo is illegible
    without companies a reviewer recognises. That makes the declaration load
    bearing rather than decorative: fabricated buying signals attached to a
    real company are indistinguishable from real ones in a screenshot.
    """

    def test_the_dataset_says_plainly_that_the_stories_are_invented(self) -> None:
        comment = _raw("dataset")["_comment"].upper()

        assert "FICTIONAL" in comment
        assert "SCREENSHOT" in comment, (
            "the notice must travel with an image, which is how this data leaves its context"
        )

    def test_no_entity_carries_a_figure_presented_as_reported(
        self, cast: dataset_module.Dataset
    ) -> None:
        """Firmographics are approximate by construction. Nothing in the cast
        may claim a source, a date of observation, or a provider — those are
        the fields that would make an invented figure read as a measurement."""
        for key in STORIES:
            entity = cast.entity(key)
            assert not {"source", "observed_at", "provider", "as_of"} & set(entity)


class TestTheIdentityStatesTheProductRendersAreAllReachable:
    """Each of these was **unreachable through the pipeline** before M12.1.5.

    Only one mapper claimed a legal name, and neither the registry nor the
    workforce provider offered a domain — so a second source could agree only
    by naming a company identically, and disagreeing split it into two
    companies instead. The product could render `AGREED` and `DISPUTED` and
    could never be given either.
    """

    def _namers(self, scenario: scenario_module.Scenario) -> dict[str, set[str]]:
        #: The providers that claim a legal name. Kept in step with the
        #: mappers rather than inferred, so adding a third namer fails here
        #: and is reviewed rather than absorbed.
        naming = {"apollo", "crunchbase"}
        by_account: dict[str, set[str]] = {key: set() for key in STORIES}
        for step in scenario.steps:
            if step.provider in naming:
                by_account[step.subject].add(step.provider)
        return by_account

    def test_some_account_is_named_by_two_sources(
        self, scenario: scenario_module.Scenario
    ) -> None:
        assert any(len(p) >= 2 for p in self._namers(scenario).values())

    def test_some_account_is_named_by_exactly_one(
        self, scenario: scenario_module.Scenario
    ) -> None:
        """`SINGLE_SOURCE` is *uncorroborated*, not agreement, and the product
        says so — which it can only be seen to do if the state occurs."""
        assert any(len(p) == 1 for p in self._namers(scenario).values())

    def test_some_account_is_named_by_nobody(
        self, scenario: scenario_module.Scenario
    ) -> None:
        """The fallback shows the real identifier rather than a fabricated
        name. **The account with the worst label is the one worth opening**, so
        the demo must contain one."""
        assert any(len(p) == 0 for p in self._namers(scenario).values())

    def test_two_sources_disagree_about_exactly_one_account(
        self, scenario: scenario_module.Scenario
    ) -> None:
        """A registry name beside a trading name — the realistic form of the
        disagreement. Exactly one, because the marker is meant to be rare: on
        every row it would be noise, and noise trains people to stop reading."""
        overridden = [
            step.subject for step in scenario.steps if "name" in step.facts
        ]

        assert len(overridden) == 1


class TestItStaysOneSourceOfTruth:
    def test_it_lives_in_the_framework_that_already_owns_scenarios(self) -> None:
        """**Not a parallel seeder.** The Provider Simulation Framework owns
        scenarios, the seeded determinism, the fault injector and the
        provenance fields; a second seeding system beside it would split all
        four across two owners."""
        assert (Path(scenario_module.SCENARIO_ROOT) / f"{SCENARIO}@{VERSION}.json").exists()
        assert (Path(dataset_module.DATASET_ROOT) / f"{SCENARIO}@{VERSION}.json").exists()

    def test_the_superseded_version_is_still_loadable(self) -> None:
        """Kept, not deleted. Every run recorded against `playground@1` cites
        it, and a correction that removed it would make those records
        uncheckable."""
        assert dataset_module.load(SCENARIO, 1).version == 1

    def test_the_cast_is_immutable_once_published(
        self, cast: dataset_module.Dataset, tmp_path: Path
    ) -> None:
        """Editing a published dataset invalidates every result recorded
        against it. A correction is a new version."""
        raw = _raw("dataset")
        raw["entities"]["figma"]["name"] = "Edited After Publication"
        (tmp_path / f"{SCENARIO}@{VERSION}.json").write_text(json.dumps(raw))

        with pytest.raises(dataset_module.DatasetError, match="content hash mismatch"):
            dataset_module.load(SCENARIO, VERSION, root=tmp_path)

    def test_running_it_twice_produces_the_same_timeline(
        self, scenario: scenario_module.Scenario, cast: dataset_module.Dataset
    ) -> None:
        """Determinism is what lets a design review, an AI evaluation and a
        demo all cite the same run. **Anchoring the epoch to today does not
        weaken it**: the epoch is an explicit input, and determinism means the
        same inputs produce the same outputs — not that the inputs may never
        include a date."""
        from signora_platform.simulation.clock import VirtualClock

        def timeline() -> list[str]:
            return [
                event.event_ref
                for event in scenario_module.build_timeline(
                    scenario, cast, VirtualClock(), seed=1701
                )
            ]

        assert timeline() == timeline()

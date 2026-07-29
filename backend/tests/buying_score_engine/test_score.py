"""The score itself: projection from the ledger, identity, trend, validity.

A score is constructed only through `projected_from`, so there is no path
by which a number and its explanation can disagree — and the tests that
matter most here are the ones proving the disagreement is refused.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from modules.buying_score_engine.domain.ledger import ContributionLedger
from modules.buying_score_engine.domain.score import (
    BuyingScore,
    BuyingScoreError,
    ScoreTrigger,
    Trend,
)
from modules.buying_score_engine.domain.scoring import build_ledger
from modules.buying_score_engine.domain.scoring_model import Posture
from modules.buying_score_engine.infrastructure.model_loader import load_scoring_model
from modules.signal_engine.infrastructure.catalog_loader import load_catalog
from modules.signal_engine.public import Relevance, Signal, SignalType
from tests.buying_score_engine.fakes import ENTITY, WORKSPACE, make_signal

NOW = datetime(2026, 3, 1, tzinfo=UTC)
MODEL = load_scoring_model()
CATALOG = load_catalog()


def project(
    signals: Sequence[Signal],
    *,
    moment: datetime = NOW,
    previous: BuyingScore | None = None,
    trigger: ScoreTrigger = ScoreTrigger.SIGNAL_GENERATED,
    scoring_model_version: int = 0,
) -> BuyingScore:
    ledger = build_ledger(signals, model=MODEL, catalog=CATALOG, moment=moment)
    basis = ledger.basis_at()
    assert basis is not None
    return BuyingScore.projected_from(
        ledger,
        workspace_id=WORKSPACE,
        entity_id=ENTITY,
        computed_at=moment,
        basis_at=basis,
        trigger=trigger,
        scoring_model_version=scoring_model_version,
        model_artifact_version=MODEL.version,
        profile_version=0,
        steady_delta=MODEL.steady_delta,
        previous=previous,
    )


class TestTheScoreIsProjectedFromItsLedger:
    def test_the_value_is_whatever_the_ledger_says(self) -> None:
        signal = make_signal(signal_type=SignalType.ACTIVE_EVALUATION, events=(uuid4(),))

        score = project((signal,))

        assert score.value == score.ledger.value()
        assert score.contested == score.ledger.is_contested

    def test_a_ledger_that_does_not_reproduce_its_score_is_refused(self) -> None:
        """**A corrupt explanation, not a discrepancy to reconcile later.**"""
        score = project((make_signal(signal_type=SignalType.ACTIVE_EVALUATION, events=(uuid4(),)),))

        with pytest.raises(BuyingScoreError, match="corrupt explanation"):
            replace(score, value=score.value + 1)

    def test_a_score_cannot_disagree_with_its_ledger_about_contradiction(self) -> None:
        score = project((make_signal(signal_type=SignalType.ACTIVE_EVALUATION, events=(uuid4(),)),))

        with pytest.raises(BuyingScoreError, match="disagrees with its ledger"):
            replace(score, contested=True)

    def test_a_score_cannot_expire_before_it_was_computed(self) -> None:
        score = project((make_signal(signal_type=SignalType.ACTIVE_EVALUATION, events=(uuid4(),)),))

        with pytest.raises(BuyingScoreError, match="expires before it was computed"):
            replace(score, valid_until=score.computed_at - timedelta(days=1))


class TestIdentityIsDerived:
    def test_the_same_situation_computes_the_same_id(self) -> None:
        """Recomputing an unchanged account inserts nothing, which is what
        makes replay safe to run repeatedly."""
        signal = make_signal(
            signal_type=SignalType.ACTIVE_EVALUATION, events=(uuid4(),), signal_id=uuid4()
        )

        assert project((signal,)).id == project((signal,)).id

    def test_a_clock_reading_does_not_change_identity_within_a_band(self) -> None:
        signal = make_signal(
            signal_type=SignalType.ACTIVE_EVALUATION,
            events=(uuid4(),),
            occurred_at=NOW,
            window_days=90,
        )

        early = project((signal,), moment=NOW + timedelta(days=1))
        later = project((signal,), moment=NOW + timedelta(days=20))

        assert early.id == later.id

    def test_a_band_transition_produces_a_genuinely_new_reading(self) -> None:
        signal = make_signal(
            signal_type=SignalType.ACTIVE_EVALUATION,
            events=(uuid4(),),
            occurred_at=NOW,
            window_days=90,
        )
        first = project((signal,), moment=NOW + timedelta(days=1))
        assert first.valid_until is not None

        after = project((signal,), moment=first.valid_until + timedelta(seconds=1))

        assert after.id != first.id
        assert after.value < first.value

    def test_a_different_weighting_produces_a_different_reading(self) -> None:
        signal = make_signal(
            signal_type=SignalType.ACTIVE_EVALUATION, events=(uuid4(),), signal_id=uuid4()
        )

        assert project((signal,), scoring_model_version=0).id != project(
            (signal,), scoring_model_version=2
        ).id


class TestTrend:
    def test_a_first_reading_is_steady_because_there_is_nothing_to_have_moved_from(
        self,
    ) -> None:
        score = project((make_signal(signal_type=SignalType.ACTIVE_EVALUATION, events=(uuid4(),)),))

        assert score.trend is Trend.STEADY
        assert score.delta == 0
        assert score.supersedes is None

    def test_more_evidence_reads_as_rising_and_names_what_it_replaces(self) -> None:
        first_signal = make_signal(
            signal_type=SignalType.ACTIVE_EVALUATION, events=(uuid4(),)
        )
        first = project((first_signal,))
        second = project(
            (first_signal, make_signal(signal_type=SignalType.BUDGET_UNLOCKED, events=(uuid4(),))),
            previous=first,
        )

        assert second.trend is Trend.RISING
        assert second.delta > 0
        assert second.supersedes == first.id

    def test_ageing_evidence_reads_as_falling(self) -> None:
        """*"Nothing has happened here for six weeks"* is real commercial
        information, and a trend that hid it would be less honest."""
        signal = make_signal(
            signal_type=SignalType.ACTIVE_EVALUATION,
            events=(uuid4(),),
            occurred_at=NOW,
            window_days=90,
        )
        first = project((signal,), moment=NOW + timedelta(days=1))
        assert first.valid_until is not None

        aged = project(
            (signal,),
            moment=first.valid_until + timedelta(seconds=1),
            previous=first,
            trigger=ScoreTrigger.EVIDENCE_AGED,
        )

        assert aged.trend is Trend.FALLING
        assert aged.trigger is ScoreTrigger.EVIDENCE_AGED

    def test_a_movement_inside_the_declared_band_reads_as_steady(self) -> None:
        """The steady band is declared in the model artifact, so a customer
        can widen it rather than live with a jittery direction."""
        first_signal = make_signal(signal_type=SignalType.ACTIVE_EVALUATION, events=(uuid4(),))
        first = project((first_signal,))
        # Low-weighted, contextual, and old enough to be in its last band —
        # the smallest real contribution the catalog can produce.
        faint = make_signal(
            signal_type=SignalType.DECISION_MAKER_DEPARTED,
            events=(uuid4(),),
            relevance=Relevance.CONTEXTUAL,
            occurred_at=NOW - timedelta(days=80),
            window_days=90,
        )

        nudged = project((first_signal, faint), previous=first)

        assert 0 < abs(nudged.delta) <= MODEL.steady_delta
        assert nudged.trend is Trend.STEADY


class TestValidity:
    def test_a_score_knows_only_whether_it_is_still_correct(self) -> None:
        """Whether a *later* score replaced it is a fact about other rows —
        `supersedes` points backwards — so a lone score cannot report it."""
        score = project((make_signal(signal_type=SignalType.ACTIVE_EVALUATION, events=(uuid4(),)),))
        assert score.valid_until is not None

        assert score.is_valid_at(score.valid_until)
        assert not score.is_valid_at(score.valid_until + timedelta(seconds=1))

    def test_a_score_with_nothing_contributing_never_expires(self) -> None:
        empty = ContributionLedger(entries=(), ceiling=MODEL.ceiling)
        score = BuyingScore.projected_from(
            empty,
            workspace_id=WORKSPACE,
            entity_id=ENTITY,
            computed_at=NOW,
            basis_at=NOW,
            trigger=ScoreTrigger.EVIDENCE_AGED,
            scoring_model_version=0,
            model_artifact_version=MODEL.version,
            profile_version=0,
            steady_delta=MODEL.steady_delta,
        )

        assert score.value == 0
        assert score.valid_until is None
        assert score.is_valid_at(NOW + timedelta(days=3650))


class TestContestedIsNeverAveraged:
    def test_a_contested_account_scores_above_a_one_sided_one(self) -> None:
        expansion = make_signal(
            signal_type=SignalType.EXPANSION_OPPORTUNITY, events=(uuid4(),)
        )
        contraction = make_signal(signal_type=SignalType.CONTRACTION_RISK, events=(uuid4(),))

        contested = project((expansion, contraction))
        one_sided = project((expansion,))

        assert contested.contested
        assert contested.value > one_sided.value
        assert contested.dissenting_signal_ids == (contraction.id,)
        assert contested.ledger.posture_summary()[Posture.CONTRACTIONARY] > 0

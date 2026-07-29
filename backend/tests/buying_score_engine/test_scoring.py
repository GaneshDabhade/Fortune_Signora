"""Attribution and step decay — how a ledger is built from hypotheses.

Step decay is the decision this module reversed during design, and the
reason is here rather than in a comment: a stored score is a snapshot with
a stated validity period, and only a discrete curve keeps that promise.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from modules.buying_score_engine.domain.ledger import ContributionLedger
from modules.buying_score_engine.domain.scoring import build_ledger
from modules.buying_score_engine.domain.scoring_model import (
    Posture,
    ScoringModelError,
)
from modules.buying_score_engine.infrastructure.model_loader import load_scoring_model
from modules.signal_engine.infrastructure.catalog_loader import load_catalog
from modules.signal_engine.public import Relevance, Signal, SignalType
from tests.buying_score_engine.fakes import make_signal

NOW = datetime(2026, 3, 1, tzinfo=UTC)
MODEL = load_scoring_model()
CATALOG = load_catalog()


def ledger_for(
    signals: Sequence[Signal], moment: datetime = NOW
) -> ContributionLedger:
    return build_ledger(signals, model=MODEL, catalog=CATALOG, moment=moment)


class TestEventUnitAttribution:
    """Double counting is impossible by construction, not avoided by a pass."""

    def test_a_shared_business_event_is_counted_once_for_the_stronger_signal(self) -> None:
        shared = uuid4()
        weak = make_signal(signal_type=SignalType.MODERNIZATION_UNDERWAY, events=(shared,))
        strong = make_signal(signal_type=SignalType.ACTIVE_EVALUATION, events=(shared,))

        ledger = ledger_for((weak, strong))

        assert len(ledger.entries) == 2
        assert ledger.counted_events() == frozenset({shared})
        counted = [e for e in ledger.entries if e.counted]
        assert len(counted) == 1
        assert counted[0].signal_id == strong.id
        assert counted[0].contribution == 40

    def test_the_outcompeted_signal_stays_visible_with_a_stated_reason(self) -> None:
        shared = uuid4()
        weak = make_signal(signal_type=SignalType.MODERNIZATION_UNDERWAY, events=(shared,))
        strong = make_signal(signal_type=SignalType.ACTIVE_EVALUATION, events=(shared,))

        ledger = ledger_for((weak, strong))

        loser = next(e for e in ledger.entries if not e.counted)
        assert loser.signal_id == weak.id
        assert loser.contribution == 0
        assert "already counted" in loser.reason

    def test_a_composite_and_its_constituent_do_not_inflate_the_score(self) -> None:
        """The requirement recorded during M5A: deduplicate on business
        events, not on signals. The same grounds read two ways are one set
        of grounds."""
        funding, hiring = uuid4(), uuid4()
        constituent = make_signal(
            signal_type=SignalType.BUDGET_UNLOCKED, events=(funding,)
        )
        composite = make_signal(
            signal_type=SignalType.EXPANSION_OPPORTUNITY,
            events=(funding, hiring),
            constituents=(constituent.id,),
        )

        ledger = ledger_for((constituent, composite))

        # Two distinct business events, so two counted contributions —
        # never three, which is what counting per signal would give.
        assert len(ledger.counted_events()) == 2
        assert ledger.total() == 35 + 30

    def test_attribution_is_reproducible_regardless_of_input_order(self) -> None:
        shared = uuid4()
        a = make_signal(signal_type=SignalType.BUDGET_UNLOCKED, events=(shared,))
        b = make_signal(signal_type=SignalType.DISPLACEMENT_OPPORTUNITY, events=(shared,))

        forwards = ledger_for((a, b))
        backwards = ledger_for((b, a))

        assert forwards.total() == backwards.total()
        assert [e.signal_id for e in forwards.entries] == [
            e.signal_id for e in backwards.entries
        ]

    def test_distinct_evidence_accrues_attention(self) -> None:
        one = make_signal(signal_type=SignalType.EXPANSION_OPPORTUNITY, events=(uuid4(),))
        two = make_signal(
            signal_type=SignalType.EXPANSION_OPPORTUNITY, events=(uuid4(), uuid4())
        )

        assert ledger_for((two,)).total() > ledger_for((one,)).total()


class TestStepDecay:
    """Gradation, without making the stored score continuously wrong."""

    def test_evidence_is_worth_less_as_it_ages(self) -> None:
        signal = make_signal(
            signal_type=SignalType.EXPANSION_OPPORTUNITY,
            events=(uuid4(),),
            occurred_at=NOW,
            window_days=90,
        )

        fresh = ledger_for((signal,), NOW + timedelta(days=1)).total()
        recent = ledger_for((signal,), NOW + timedelta(days=45)).total()
        ageing = ledger_for((signal,), NOW + timedelta(days=85)).total()

        assert fresh > recent > ageing > 0

    def test_the_score_is_constant_within_a_band(self) -> None:
        """**The property that forced step decay.** A stored score promises
        to be exactly correct until `valid_until`; a continuous curve would
        break that promise at every instant."""
        signal = make_signal(
            signal_type=SignalType.EXPANSION_OPPORTUNITY,
            events=(uuid4(),),
            occurred_at=NOW,
            window_days=90,
        )
        first = ledger_for((signal,), NOW + timedelta(days=1))
        boundary = first.valid_until()
        assert boundary is not None

        assert ledger_for((signal,), boundary - timedelta(seconds=1)).total() == first.total()

    def test_the_band_changes_exactly_at_the_stated_validity(self) -> None:
        signal = make_signal(
            signal_type=SignalType.EXPANSION_OPPORTUNITY,
            events=(uuid4(),),
            occurred_at=NOW,
            window_days=90,
        )
        first = ledger_for((signal,), NOW + timedelta(days=1))
        boundary = first.valid_until()
        assert boundary is not None

        assert ledger_for((signal,), boundary + timedelta(seconds=1)).total() < first.total()

    def test_bands_scale_with_the_types_own_relevance_window(self) -> None:
        """Boundaries are fractions of the catalog's per-type judgement, so
        a short-lived hypothesis ages faster in wall-clock terms without any
        per-type constant in the model."""
        short = make_signal(
            signal_type=SignalType.EXPANSION_OPPORTUNITY,
            events=(uuid4(),),
            occurred_at=NOW,
            window_days=30,
        )
        long = make_signal(
            signal_type=SignalType.EXPANSION_OPPORTUNITY,
            events=(uuid4(),),
            occurred_at=NOW,
            window_days=360,
        )
        at = NOW + timedelta(days=20)

        assert ledger_for((short,), at).total() < ledger_for((long,), at).total()

    def test_the_band_carries_a_word_a_customer_can_argue_with(self) -> None:
        signal = make_signal(signal_type=SignalType.EXPANSION_OPPORTUNITY, events=(uuid4(),))

        entry = ledger_for((signal,)).entries[0]

        assert entry.age_band == "fresh"
        assert "fresh" in entry.reason
        assert "100%" in entry.reason

    def test_an_expired_hypothesis_has_no_band_and_must_not_be_scored(self) -> None:
        signal = make_signal(
            signal_type=SignalType.EXPANSION_OPPORTUNITY,
            events=(uuid4(),),
            occurred_at=NOW,
            window_days=30,
        )

        with pytest.raises(ScoringModelError, match="not worth a little"):
            ledger_for((signal,), NOW + timedelta(days=31))


class TestRelevanceBecomesWeight:
    """M5A refused to turn its category into a number. M5B is where that
    mapping lives — declared, versioned, and the customer's."""

    def test_a_primary_hypothesis_outweighs_a_contextual_one(self) -> None:
        primary = make_signal(
            signal_type=SignalType.EXPANSION_OPPORTUNITY,
            events=(uuid4(),),
            relevance=Relevance.PRIMARY,
        )
        contextual = make_signal(
            signal_type=SignalType.EXPANSION_OPPORTUNITY,
            events=(uuid4(),),
            relevance=Relevance.CONTEXTUAL,
        )

        assert ledger_for((primary,)).total() > ledger_for((contextual,)).total()


class TestPostureIsCarriedNotSummed:
    def test_a_contraction_risk_adds_attention_and_records_its_posture(self) -> None:
        risk = make_signal(signal_type=SignalType.CONTRACTION_RISK, events=(uuid4(),))

        entry = ledger_for((risk,)).entries[0]

        assert entry.posture is Posture.CONTRACTIONARY
        assert entry.contribution > 0

    def test_an_account_in_tension_outscores_a_quiet_one(self) -> None:
        expansion = make_signal(
            signal_type=SignalType.EXPANSION_OPPORTUNITY, events=(uuid4(),)
        )
        contraction = make_signal(signal_type=SignalType.CONTRACTION_RISK, events=(uuid4(),))

        contested = ledger_for((expansion, contraction))
        one_sided = ledger_for((expansion,))

        assert contested.value() > one_sided.value()
        assert contested.is_contested
        assert contested.dissent() == (contraction.id,)

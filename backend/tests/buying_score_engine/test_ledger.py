"""The Contribution Ledger — the authoritative explanation of a score.

The properties under test are the ones that make the pipeline's first
intentional reduction safe: the score reproduces from the ledger exactly,
opposing readings never cancel, a business event is counted once, and
nothing is silently dropped.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from modules.buying_score_engine.domain.ledger import (
    Contribution,
    ContributionLedger,
    LedgerError,
    weigh,
)
from modules.buying_score_engine.domain.scoring_model import PERCENT, Posture
from modules.signal_engine.public import Relevance, SignalType

NOW = datetime(2026, 3, 1, tzinfo=UTC)


def entry(
    *,
    points: int,
    posture: Posture = Posture.EXPANSIONARY,
    counted: bool = True,
    event_id: UUID | None = None,
    signal_id: UUID | None = None,
    band_ends_at: datetime | None = None,
) -> Contribution:
    return Contribution(
        business_event_id=event_id or uuid4(),
        signal_id=signal_id or uuid4(),
        signal_type=SignalType.EXPANSION_OPPORTUNITY,
        posture=posture,
        relevance=Relevance.PRIMARY,
        base_weight=points,
        relevance_multiplier=PERCENT,
        age_band="fresh",
        age_multiplier=PERCENT,
        contribution=points if counted else 0,
        counted=counted,
        reason="because the evidence says so",
        band_started_at=NOW,
        band_ends_at=band_ends_at or NOW + timedelta(days=60),
    )


class TestReproduction:
    """A score that cannot be recomputed from its ledger is not explained."""

    def test_the_score_is_the_ledger_arithmetic_with_no_clock_and_no_configuration(self) -> None:
        ledger = ContributionLedger(
            entries=(entry(points=30), entry(points=25), entry(points=5)), ceiling=120
        )

        assert ledger.total() == 60
        assert ledger.value() == 60 * 100 // 120

    def test_saturation_is_honest_rather_than_overflowing(self) -> None:
        ledger = ContributionLedger(entries=(entry(points=500),), ceiling=120)

        assert ledger.value() == 100

    def test_an_empty_ledger_projects_zero_and_expires_never(self) -> None:
        ledger = ContributionLedger(entries=(), ceiling=120)

        assert ledger.value() == 0
        assert ledger.valid_until() is None
        assert ledger.basis_at() is None

    def test_arithmetic_is_integral_end_to_end(self) -> None:
        """Float accumulation would make the one artifact whose job is to be
        checkable only approximately checkable."""
        assert weigh(35, 60, 30) == 6
        assert isinstance(weigh(35, 60, 30), int)

    def test_a_ledger_needs_a_ceiling_to_normalize_against(self) -> None:
        with pytest.raises(LedgerError, match="positive ceiling"):
            ContributionLedger(entries=(), ceiling=0)


class TestNoDoubleCounting:
    """The unit of contribution is the business event, structurally."""

    def test_one_business_event_cannot_be_counted_twice(self) -> None:
        shared = uuid4()

        with pytest.raises(LedgerError, match="counted twice"):
            ContributionLedger(
                entries=(entry(points=30, event_id=shared), entry(points=25, event_id=shared)),
                ceiling=120,
            )

    def test_the_same_event_may_appear_again_uncounted(self) -> None:
        """Nothing is silently dropped: a zero with a reason is information,
        an absent row is a mystery."""
        shared = uuid4()
        ledger = ContributionLedger(
            entries=(
                entry(points=30, event_id=shared),
                entry(points=25, event_id=shared, counted=False),
            ),
            ceiling=120,
        )

        assert ledger.total() == 30
        assert len(ledger.entries) == 2
        assert ledger.counted_events() == frozenset({shared})

    def test_an_uncounted_entry_carrying_points_is_a_self_contradiction(self) -> None:
        with pytest.raises(LedgerError, match="not counted but carries"):
            Contribution(
                business_event_id=uuid4(),
                signal_id=uuid4(),
                signal_type=SignalType.EXPANSION_OPPORTUNITY,
                posture=Posture.EXPANSIONARY,
                relevance=Relevance.PRIMARY,
                base_weight=30,
                relevance_multiplier=PERCENT,
                age_band="fresh",
                age_multiplier=PERCENT,
                contribution=30,
                counted=False,
                reason="whatever",
                band_started_at=NOW,
                band_ends_at=NOW,
            )


class TestContradictionIsPreservedNotNetted:
    """The decision the whole module turns on."""

    def test_opposing_readings_both_add_attention(self) -> None:
        """A fought-over account warrants **more** attention, not average
        attention. Netting would score it like an inert one, and those are
        the two most different accounts in the book."""
        contested = ContributionLedger(
            entries=(
                entry(points=30, posture=Posture.EXPANSIONARY),
                entry(points=25, posture=Posture.CONTRACTIONARY),
            ),
            ceiling=120,
        )
        inert = ContributionLedger(entries=(), ceiling=120)

        assert contested.total() == 55
        assert contested.value() > inert.value()
        assert contested.is_contested

    def test_attention_is_unsigned_for_every_posture(self) -> None:
        with pytest.raises(LedgerError, match="Attention is unsigned"):
            Contribution(
                business_event_id=uuid4(),
                signal_id=uuid4(),
                signal_type=SignalType.CONTRACTION_RISK,
                posture=Posture.CONTRACTIONARY,
                relevance=Relevance.PRIMARY,
                base_weight=25,
                relevance_multiplier=PERCENT,
                age_band="fresh",
                age_multiplier=PERCENT,
                contribution=-25,
                counted=True,
                reason="a minus sign is the netting this module refuses",
                band_started_at=NOW,
                band_ends_at=NOW,
            )

    def test_one_sided_evidence_is_not_contested(self) -> None:
        ledger = ContributionLedger(
            entries=(
                entry(points=30, posture=Posture.EXPANSIONARY),
                entry(points=20, posture=Posture.NEUTRAL),
            ),
            ceiling=120,
        )

        assert not ledger.is_contested
        assert ledger.dissent() == ()

    def test_dissent_names_the_outweighed_reading(self) -> None:
        losing = uuid4()
        ledger = ContributionLedger(
            entries=(
                entry(points=40, posture=Posture.EXPANSIONARY),
                entry(points=15, posture=Posture.CONTRACTIONARY, signal_id=losing),
            ),
            ceiling=120,
        )

        assert ledger.dissent() == (losing,)

    def test_posture_never_reaches_the_scalar(self) -> None:
        summary = ContributionLedger(
            entries=(
                entry(points=30, posture=Posture.EXPANSIONARY),
                entry(points=25, posture=Posture.CONTRACTIONARY),
            ),
            ceiling=120,
        ).posture_summary()

        assert summary[Posture.EXPANSIONARY] == 30
        assert summary[Posture.CONTRACTIONARY] == 25


class TestValidity:
    """When the arithmetic next changes, from the evidence's own boundaries."""

    def test_validity_is_the_earliest_band_transition(self) -> None:
        soon = NOW + timedelta(days=10)
        ledger = ContributionLedger(
            entries=(
                entry(points=30, band_ends_at=NOW + timedelta(days=60)),
                entry(points=25, band_ends_at=soon),
            ),
            ceiling=120,
        )

        assert ledger.valid_until() == soon

    def test_an_uncounted_entry_still_bounds_validity(self) -> None:
        """When the signal currently holding a business event expires, an
        uncounted claim on it becomes the counted one — so it changes the
        arithmetic even while contributing nothing."""
        shared = uuid4()
        soon = NOW + timedelta(days=5)
        ledger = ContributionLedger(
            entries=(
                entry(points=30, event_id=shared, band_ends_at=NOW + timedelta(days=90)),
                entry(points=25, event_id=shared, counted=False, band_ends_at=soon),
            ),
            ceiling=120,
        )

        assert ledger.valid_until() == soon

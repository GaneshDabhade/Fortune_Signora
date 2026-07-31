"""The four temporal questions, answered from recorded facts.

No model appears here or in the code under test. Every answer already existed
in the repository before M9 was written — this proves M9 *composes* them
rather than re-deriving them, which is the difference between a fact and a
guess about causality.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest

from modules.ai_reasoning_engine.domain.temporal import (
    TemporalError,
    TemporalExplanation,
)
from modules.buying_score_engine.public import ScoreTrigger, Trend
from modules.opportunity_engine.public import EvidenceState

NOW = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)
EARLIER = datetime(2026, 7, 11, 9, 0, tzinfo=UTC)
LATER = datetime(2026, 8, 13, 9, 0, tzinfo=UTC)


class TestWhyNowIsRecordedNeverGuessed:
    """`ScoreTrigger` exists precisely because *"a number that moved for an
    unexplainable reason is a number nobody trusts"*. M9 presents it."""

    @pytest.mark.parametrize("trigger", list(ScoreTrigger))
    def test_every_trigger_has_a_customer_readable_answer(self, trigger: ScoreTrigger) -> None:
        """A trigger with no phrasing would render as a crash or a raw enum
        value in front of a customer. Parametrised over the enum, so adding a
        trigger upstream fails here rather than in production."""
        rendered = _temporal(trigger=trigger).why_now()

        assert rendered.startswith("This reading exists because ")
        assert trigger.value not in rendered, "the raw enum value reached the customer"

    def test_configuration_changes_are_distinguished_from_evidence_changes(self) -> None:
        """*Your workspace changed the weighting* and *a new signal was found*
        are different answers, and a customer who cannot tell them apart will
        think the account moved when their own settings did."""
        by_evidence = _temporal(trigger=ScoreTrigger.SIGNAL_GENERATED).why_now()
        by_config = _temporal(trigger=ScoreTrigger.MODEL_CHANGED).why_now()

        assert "new signal" in by_evidence
        assert "your workspace" in by_config.lower()

    def test_evidence_ageing_is_stated_as_a_reason_in_its_own_right(self) -> None:
        """The reason the Buying Score Engine has a sweep at all: *"nothing
        has happened here for six weeks"* is real commercial information."""
        assert "passed the point" in _temporal(trigger=ScoreTrigger.EVIDENCE_AGED).why_now()


class TestWhyNotEarlier:
    def test_a_first_reading_says_there_was_nothing_earlier(self) -> None:
        """A different answer, not a missing one."""
        assert "first reading" in _temporal(supersedes=None, delta=0).why_not_earlier()

    def test_a_later_reading_names_when_the_evidence_beneath_it_changed(self) -> None:
        """`basis_at` is what makes this answerable: before it, the previous
        reading was the correct one."""
        rendered = _temporal(basis_at=EARLIER).why_not_earlier()

        assert "2026-07-11" in rendered
        assert "previous reading was the correct one" in rendered


class TestWhatChanged:
    @pytest.mark.parametrize(("delta", "expected"), [(12, "rose by 12"), (-7, "fell by 7")])
    def test_it_reports_direction_and_magnitude(self, delta: int, expected: str) -> None:
        assert expected in _temporal(delta=delta).what_changed()

    def test_a_steady_score_still_reports_that_evidence_moved(self) -> None:
        """The evidence behind a number can change without moving it, and a
        customer told only "no change" would think nothing happened."""
        rendered = _temporal(delta=0, trend=Trend.STEADY).what_changed()

        assert "held steady" in rendered
        assert "changed without moving the number" in rendered

    def test_a_first_reading_changed_nothing(self) -> None:
        assert "had not been read before" in _temporal(supersedes=None, delta=0).what_changed()


class TestFreshness:
    def test_it_states_how_long_the_value_is_exactly_correct(self) -> None:
        """`valid_until` is *exactly correct until*, not *recent as of* —
        which is what makes step decay a contract rather than an
        implementation detail."""
        rendered = _temporal(valid_until=LATER).freshness()

        assert "exactly correct until 2026-08-13" in rendered

    def test_no_expiry_means_nothing_is_due_to_age_out(self) -> None:
        """`None` means nothing is contributing, so nothing changes without a
        new signal — and a new signal publishes an event."""
        assert "nothing is currently due to age out" in _temporal(valid_until=None).freshness()

    def test_it_reuses_the_opportunity_engines_own_derivation(self) -> None:
        """A second definition of "is this still current" would disagree with
        the first within a year."""
        assert "cooling" in _temporal(evidence_state=EvidenceState.COOLING).freshness()


class TestAHistoryMustBeCoherent:
    """Invalid states refused at construction rather than measured later."""

    def test_a_first_reading_cannot_have_moved(self) -> None:
        """`delta` is measured against the immediately previous reading. With
        no predecessor there is nothing to differ from — the Buying Score
        Engine sets zero, and a non-zero value here means the two disagree."""
        with pytest.raises(TemporalError, match="does not exist"):
            _temporal(supersedes=None, delta=5)

    def test_a_reading_cannot_expire_before_it_was_computed(self) -> None:
        with pytest.raises(TemporalError, match="expire before"):
            _temporal(computed_at=NOW, valid_until=EARLIER)

    def test_evidence_cannot_change_after_the_reading_it_produced(self) -> None:
        """A score is a projection over evidence that already existed."""
        with pytest.raises(TemporalError, match="cannot have changed after"):
            _temporal(basis_at=LATER, computed_at=NOW)

    def test_a_coherent_history_is_accepted(self) -> None:
        """The positive control. Validators that rejected everything would
        satisfy all three tests above."""
        assert _temporal().explain()


class TestTheFourAnswersTravelTogether:
    def test_explain_returns_all_four_in_the_order_a_customer_asks_them(self) -> None:
        explanation = _temporal()

        assert explanation.explain() == (
            explanation.why_now(),
            explanation.why_not_earlier(),
            explanation.what_changed(),
            explanation.freshness(),
        )

    def test_the_answers_are_derived_rather_than_stored(self) -> None:
        """Rendered from the same fields every time, so an explanation cannot
        drift from the history it explains. A stored paragraph would be a
        second representation of one history."""
        first = _temporal(trigger=ScoreTrigger.EVIDENCE_AGED)
        second = _temporal(trigger=ScoreTrigger.SIGNAL_GENERATED)

        assert first.explain() != second.explain()


def _temporal(**overrides: object) -> TemporalExplanation:
    defaults: dict[str, object] = {
        "trigger": ScoreTrigger.SIGNAL_GENERATED,
        "basis_at": EARLIER,
        "computed_at": NOW,
        "delta": 12,
        "trend": Trend.RISING,
        "evidence_state": EvidenceState.CURRENT,
        "valid_until": LATER,
        "supersedes": UUID(int=9),
    }
    return TemporalExplanation(**{**defaults, **overrides})  # type: ignore[arg-type]

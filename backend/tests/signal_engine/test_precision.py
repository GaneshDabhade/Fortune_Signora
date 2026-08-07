"""**TASK-444 — the catalog learns which rules misfire.**

[447](../../../docs/architecture/447-signal-center-traceability-audit.md):
*"dismissal reasons feed rule precision."* A signal type that keeps being
dismissed is a rule that keeps being wrong, and until this nothing noticed.

**The tests that matter are about what is *not* counted.** Precision computed
over all four outcomes would look correct, produce a number for every type,
and be wrong in a direction nobody could see.
"""

from __future__ import annotations

import pytest

from modules.signal_engine.domain.precision import RulePrecision


class TestARuleNobodyHasJudged:
    def test_has_no_precision_rather_than_zero(self) -> None:
        """⛔ **P-A.** A new rule and a rule that is always wrong are opposite
        facts, and `0.0` renders them identically — the reading a person takes
        from *0%* being the second one."""
        assert RulePrecision(signal_type="hiring_surge", actioned=0, dismissed=0).ratio is None

    def test_and_says_nobody_has(self) -> None:
        assert RulePrecision(signal_type="hiring_surge", actioned=0, dismissed=0).judged == 0


class TestTheArithmetic:
    @pytest.mark.parametrize(
        ("actioned", "dismissed", "expected"),
        [(3, 1, 0.75), (1, 1, 0.5), (0, 4, 0.0), (4, 0, 1.0)],
    )
    def test_precision_is_the_share_that_were_right(
        self, actioned: int, dismissed: int, expected: float
    ) -> None:
        assert RulePrecision("t", actioned=actioned, dismissed=dismissed).ratio == expected

    def test_a_rule_always_dismissed_is_zero_and_that_is_a_real_answer(self) -> None:
        """**Distinct from `None` above.** Four people judged it and all four
        said it should not have been raised — that is a measurement, not an
        absence, and the two must not render the same way."""
        rule = RulePrecision("t", actioned=0, dismissed=4)
        assert rule.ratio == 0.0
        assert rule.judged == 4

    def test_the_denominator_is_judgements_and_not_signals_raised(self) -> None:
        assert RulePrecision("t", actioned=2, dismissed=3).judged == 5

    def test_a_negative_count_is_refused(self) -> None:
        with pytest.raises(ValueError):
            RulePrecision("t", actioned=-1, dismissed=0)

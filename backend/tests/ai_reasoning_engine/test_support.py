"""Support is computed from facts the platform already owns.

No model appears anywhere in this file, and none appears in the code it
tests. That is the guarantee: a customer asking *"how strong is this?"* gets
an answer they can recompute from evidence in front of them, not a number
they are asked to believe.
"""

from __future__ import annotations

import pytest

from modules.ai_reasoning_engine.domain.support import (
    MINIMUM_CORROBORATING_PROVIDERS,
    SupportBasis,
    SupportLevel,
)
from modules.opportunity_engine.public import EvidenceState


class TestSupportIsNeverANumber:
    """`SupportLevel` refuses arithmetic, exactly as `MatchStrength` does.

    A category that can become a number gets averaged across accounts within
    a year, by someone who never read the docstring forbidding it.
    """

    @pytest.mark.parametrize("convert", [int, float])
    def test_it_refuses_numeric_conversion(self, convert: object) -> None:
        assert callable(convert)
        with pytest.raises(TypeError, match="not a score"):
            convert(SupportLevel.CORROBORATED)

    @pytest.mark.parametrize("op", ["__lt__", "__le__", "__gt__", "__ge__"])
    def test_it_refuses_ordering(self, op: str) -> None:
        """Two levels differ in *why* the evidence is weaker. Ranking them
        hides which problem a reader is looking at."""
        with pytest.raises(TypeError, match="does not order"):
            getattr(SupportLevel.CORROBORATED, op)(SupportLevel.LIMITED)


class TestTheLevelIsTwoYesNoQuestions:
    """Both inputs were already derived elsewhere, so Support introduces no
    new threshold — which is what makes it explainable rather than tuned."""

    def test_corroborated_and_current_is_the_strongest_reading(self) -> None:
        assert _basis().level is SupportLevel.CORROBORATED

    @pytest.mark.parametrize(
        ("kwargs", "why"),
        [
            ({"corroborating_providers": frozenset({"apollo"})}, "single source"),
            ({"evidence_state": EvidenceState.COOLING}, "aging evidence"),
        ],
    )
    def test_either_half_missing_qualifies_it(self, kwargs: dict[str, object], why: str) -> None:
        assert _basis(**kwargs).level is SupportLevel.QUALIFIED, why

    def test_neither_half_leaves_it_limited(self) -> None:
        basis = _basis(
            corroborating_providers=frozenset({"apollo"}), evidence_state=EvidenceState.STALE
        )
        assert basis.level is SupportLevel.LIMITED

    def test_corroboration_counts_distinct_providers_not_events(self) -> None:
        """One provider repeating itself across ten events is one source.
        The same distinction `ReasonedOutput.premises` draws for citations."""
        loud = _basis(corroborating_providers=frozenset({"apollo"}), contributing_events=10)

        assert not loud.is_corroborated
        assert loud.level is SupportLevel.QUALIFIED

    def test_the_corroboration_rule_is_stated_once(self) -> None:
        assert MINIMUM_CORROBORATING_PROVIDERS == 2


class TestWhatDeliberatelyDoesNotAffectTheLevel:
    def test_contention_never_lowers_support(self) -> None:
        """*The Buying Score Engine prioritizes; it never resolves.* A
        fought-over account warrants more attention, not average attention —
        so netting a contradiction into weaker support would resolve, one
        stage later, exactly what six stages preserved."""
        quiet = _basis()
        contested = _basis(contested=True, dissenting_signals=2)

        assert contested.level is quiet.level is SupportLevel.CORROBORATED

    def test_event_count_never_changes_the_level(self) -> None:
        """*How many events is enough* is a threshold nobody can justify.
        Corroboration is used instead, because "two independent providers say
        this" is a definition rather than a tuned value."""
        levels = {_basis(contributing_events=n).level for n in (1, 3, 40)}

        assert levels == {SupportLevel.CORROBORATED}

    def test_the_count_is_still_shown(self) -> None:
        """Excluded from the decision, not from the customer."""
        assert "40 contributing business event(s)" in _basis(contributing_events=40).explain()[0]


class TestABasisMustDescribeSomethingReal:
    def test_contested_without_a_named_dissenter_is_refused(self) -> None:
        """Contradiction is named, never merely counted — a consumer told only
        "contested" learns something disagrees while being denied the means to
        look. The buying score ledger enforces the same rule."""
        with pytest.raises(ValueError, match="names no dissenting signal"):
            _basis(contested=True, dissenting_signals=0)

    def test_providers_corroborating_nothing_are_refused(self) -> None:
        with pytest.raises(ValueError, match="corroborate no events"):
            _basis(contributing_events=0)

    @pytest.mark.parametrize("kwargs", [{"contributing_events": -1}, {"dissenting_signals": -1}])
    def test_negative_quantities_are_refused(self, kwargs: dict[str, object]) -> None:
        with pytest.raises(ValueError, match="negative"):
            _basis(**kwargs)


class TestTheLevelExplainsItself:
    """A customer must always be able to see *why* Support reads as it does,
    so the level never travels alone."""

    def test_it_names_the_providers_that_agree(self) -> None:
        rendered = " | ".join(_basis().explain())

        assert "apollo" in rendered and "coresignal" in rendered
        assert "2 independent providers" in rendered

    def test_it_says_which_half_is_missing(self) -> None:
        single = " | ".join(_basis(corroborating_providers=frozenset({"apollo"})).explain())
        aging = " | ".join(_basis(evidence_state=EvidenceState.STALE).explain())

        assert "a single source (apollo)" in single
        assert "the intelligence behind it is stale" in aging

    def test_it_states_that_contention_is_not_a_weakness(self) -> None:
        rendered = " | ".join(_basis(contested=True, dissenting_signals=1).explain())

        assert "does not weaken the support" in rendered

    def test_a_quiet_basis_mentions_no_dissent(self) -> None:
        """The positive control: an explanation that always mentioned dissent
        would satisfy the test above while saying nothing."""
        assert not any("differently" in reason for reason in _basis().explain())

    def test_the_explanation_is_derived_rather_than_stored(self) -> None:
        """Rendered from the same fields the level reads, so the two cannot
        drift. A stored sentence would be a second representation of one
        fact."""
        basis = _basis(evidence_state=EvidenceState.COOLING)

        assert basis.level is SupportLevel.QUALIFIED
        assert "cooling" in " | ".join(basis.explain())


def _basis(**overrides: object) -> SupportBasis:
    defaults: dict[str, object] = {
        "corroborating_providers": frozenset({"apollo", "coresignal"}),
        "contributing_events": 3,
        "evidence_state": EvidenceState.CURRENT,
        "contested": False,
        "dissenting_signals": 0,
    }
    return SupportBasis(**{**defaults, **overrides})  # type: ignore[arg-type]

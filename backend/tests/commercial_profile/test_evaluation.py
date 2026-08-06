"""Whether an account matches a criterion — the predicate sixteen consumers wait on.

[TASK-434](../../../docs/BACKLOG.md), which exists because this lane refused to
invent it inside TASK-406 and the product owner ruled it foundational
([C-330](../../../docs/LANE_COORDINATION.md)).

**Two invariants carry the weight**, and both are asserted rather than
described: a verdict is a category with a reason and never a number, and
`UNMEASURED` is never folded into `NO`.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from modules.commercial_profile.domain.icp import EmployeeRange, ProductIcp
from modules.commercial_profile.public import IcpCriteriaView, evaluate_criteria
from modules.commercial_profile.domain.evaluation import (
    CriterionKind,
    CriterionVerdict,
    ObservedAttributes,
    Verdict,
    evaluate,
)


def an_icp(**overrides: object) -> ProductIcp:
    kwargs: dict[str, object] = {"product_id": uuid4(), "industries": ("Fintech",)}
    kwargs.update(overrides)
    return ProductIcp(**kwargs)  # type: ignore[arg-type]


def _for(kind: CriterionKind, verdicts: tuple[CriterionVerdict, ...]) -> CriterionVerdict:
    return next(v for v in verdicts if v.kind is kind)


class TestUnmeasuredIsNotNo:
    """**The invariant that stops an account silently leaving its own ICP.**

    The customer declares free text and the pipeline observes canonical
    values. A matcher that returned `NO` when it had nothing to compare would
    be wrong in a way that looks decided, which is worse than saying nothing.
    """

    def test_nothing_observed_is_unmeasured_rather_than_no(self) -> None:
        verdicts = evaluate(an_icp(), ObservedAttributes())
        assert _for(CriterionKind.INDUSTRY, verdicts).verdict is Verdict.UNMEASURED

    def test_a_criterion_nobody_declared_is_unmeasured_rather_than_yes(self) -> None:
        """The other direction, and it matters as much: an undeclared
        criterion is not a criterion everything passes."""
        verdicts = evaluate(an_icp(countries=()), ObservedAttributes(country="US"))
        assert _for(CriterionKind.COUNTRY, verdicts).verdict is Verdict.UNMEASURED

    def test_an_observed_value_that_does_not_match_is_no_and_not_unmeasured(self) -> None:
        """The negative control. `UNMEASURED` must not become a way to avoid
        ever saying no."""
        verdicts = evaluate(an_icp(), ObservedAttributes(industry="Mining"))
        assert _for(CriterionKind.INDUSTRY, verdicts).verdict is Verdict.NO

    def test_a_blank_observation_is_unmeasured(self) -> None:
        """Whitespace is not an observation, and treating it as one would
        report `NO` against a value nobody supplied."""
        verdicts = evaluate(an_icp(), ObservedAttributes(industry="   "))
        assert _for(CriterionKind.INDUSTRY, verdicts).verdict is Verdict.UNMEASURED


class TestAVerdictIsACategoryWithReasons:
    """`MatchStrength`'s rule, applied where the same door would open."""

    def test_no_verdict_carries_a_number(self) -> None:
        verdicts = evaluate(an_icp(), ObservedAttributes(industry="Fintech"))
        for verdict in verdicts:
            assert not hasattr(verdict, "score")
            assert not hasattr(verdict, "confidence")
            assert not hasattr(verdict, "weight")

    def test_a_refusal_says_what_was_wanted(self) -> None:
        """*"Not a match"* without saying what was declared sends the reader
        to another screen to find out."""
        verdicts = evaluate(
            an_icp(industries=("Fintech", "Insurance")), ObservedAttributes(industry="Mining")
        )
        reason = _for(CriterionKind.INDUSTRY, verdicts).reason
        assert "Mining" in reason and "Fintech" in reason and "Insurance" in reason

    def test_a_match_says_what_matched(self) -> None:
        verdicts = evaluate(an_icp(), ObservedAttributes(industry="Fintech"))
        assert "Fintech" in _for(CriterionKind.INDUSTRY, verdicts).reason

    def test_is_decided_separates_the_two_answers_from_the_absence(self) -> None:
        decided = evaluate(an_icp(), ObservedAttributes(industry="Fintech"))
        assert _for(CriterionKind.INDUSTRY, decided).is_decided is True
        undecided = evaluate(an_icp(), ObservedAttributes())
        assert _for(CriterionKind.INDUSTRY, undecided).is_decided is False


class TestItComparesTextWithoutInterpretingIt:
    def test_case_and_spacing_are_folded(self) -> None:
        """Not interpretation — the same string typed twice."""
        verdicts = evaluate(
            an_icp(industries=("Financial Services",)),
            ObservedAttributes(industry="  financial   services "),
        )
        assert _for(CriterionKind.INDUSTRY, verdicts).verdict is Verdict.YES

    def test_a_synonym_is_not_matched_and_that_is_the_known_limitation(self) -> None:
        """**`SaaS` against `Computer Software` returns `NO`, deliberately.**

        A synonym catalog is a reviewed artifact rather than code (443 M1),
        and inventing one here would be this module deciding what two
        different words mean. **The limitation is asserted so it is visible**
        rather than discovered by a customer whose account left their ICP.
        """
        verdicts = evaluate(
            an_icp(industries=("SaaS",)), ObservedAttributes(industry="Computer Software")
        )
        assert _for(CriterionKind.INDUSTRY, verdicts).verdict is Verdict.NO


class TestTheSizeRange:
    @pytest.mark.parametrize(
        ("observed", "expected"),
        [(100, Verdict.YES), (1000, Verdict.YES), (99, Verdict.NO), (1001, Verdict.NO)],
    )
    def test_both_bounds_are_inclusive(self, observed: int, expected: Verdict) -> None:
        """A customer typing 100–1000 means a company of exactly 1000."""
        icp = an_icp(employees=EmployeeRange(minimum=100, maximum=1000))
        verdicts = evaluate(icp, ObservedAttributes(employees=observed))
        assert _for(CriterionKind.EMPLOYEES, verdicts).verdict is expected

    def test_an_open_upper_bound_admits_anything_above(self) -> None:
        icp = an_icp(employees=EmployeeRange(minimum=500))
        verdicts = evaluate(icp, ObservedAttributes(employees=50_000))
        assert _for(CriterionKind.EMPLOYEES, verdicts).verdict is Verdict.YES

    def test_zero_employees_is_measured_rather_than_missing(self) -> None:
        """**`0` is an observation and `None` is not**, and collapsing them
        would report an unmeasured account as one with no staff."""
        icp = an_icp(employees=EmployeeRange(minimum=1))
        verdicts = evaluate(icp, ObservedAttributes(employees=0))
        assert _for(CriterionKind.EMPLOYEES, verdicts).verdict is Verdict.NO


class TestItIsPure:
    def test_the_same_input_returns_the_same_verdicts(self) -> None:
        icp = an_icp(industries=("Fintech",), employees=EmployeeRange(minimum=10))
        observed = ObservedAttributes(industry="Fintech", employees=20)
        assert evaluate(icp, observed) == evaluate(icp, observed)

    def test_it_answers_for_every_criterion_kind_every_time(self) -> None:
        """**A criterion the customer did not declare is present and
        `UNMEASURED`, never omitted** — the same reasoning the product owner
        applied to search groups at TASK-408."""
        verdicts = evaluate(an_icp(), ObservedAttributes())
        assert {v.kind for v in verdicts} == set(CriterionKind)

    def test_it_offers_no_overall_answer(self) -> None:
        """Rolling three verdicts into one needs a rule for `UNMEASURED`, and
        every available rule is a judgement that belongs to the consumer with
        a reason for it."""
        verdicts = evaluate(an_icp(), ObservedAttributes())
        assert isinstance(verdicts, tuple)
        assert not hasattr(verdicts, "matches")


class TestThePredicateIsReachableFromOutsideTheModule:
    """⚡ **`evaluate` shipped at TASK-434 and no consumer could call it.**

    It takes `ProductIcp` — this module's aggregate — so a module holding
    `IcpCriteriaView` had the criteria and no way to ask the question about
    them. **A foundation sixteen consumers were counted waiting on, that none
    of them could reach.** Published on the trigger this module already uses:
    the first consumer that needs it ([TASK-406](../../../docs/BACKLOG.md)).
    """

    @staticmethod
    def _criteria(**overrides: object) -> IcpCriteriaView:
        defaults: dict[str, object] = {
            "product_id": uuid4(),
            "industries": ("Fintech",),
            "countries": ("United Kingdom",),
            "employees_minimum": 100,
            "employees_maximum": 1000,
        }
        return IcpCriteriaView(**{**defaults, **overrides})  # type: ignore[arg-type]

    def test_a_consumer_can_ask_the_question_holding_only_the_view(self) -> None:
        found = evaluate_criteria(
            self._criteria(), industry="Fintech", country="United Kingdom", employees=500
        )

        assert {v.kind: v.verdict for v in found} == {
            CriterionKind.INDUSTRY: Verdict.YES,
            CriterionKind.COUNTRY: Verdict.YES,
            CriterionKind.EMPLOYEES: Verdict.YES,
        }

    def test_nothing_observed_is_unmeasured_and_never_no(self) -> None:
        """**The same fact `AccountAttributesReader` calls `unknown`**, arriving
        from the other end of the same call."""
        found = evaluate_criteria(self._criteria())

        assert {v.verdict for v in found} == {Verdict.UNMEASURED}

    def test_an_undeclared_criterion_is_still_returned(self) -> None:
        """A criterion the customer did not declare comes back `UNMEASURED`
        rather than being omitted — *the absence of results and the absence of
        the group represent different business meanings.*"""
        found = evaluate_criteria(
            self._criteria(industries=(), employees_minimum=None, employees_maximum=None),
            industry="Fintech",
            employees=500,
        )

        by_kind = {v.kind: v.verdict for v in found}
        assert len(found) == 3
        assert by_kind[CriterionKind.INDUSTRY] is Verdict.UNMEASURED
        assert by_kind[CriterionKind.EMPLOYEES] is Verdict.UNMEASURED

    def test_a_size_only_declaration_still_builds_its_range(self) -> None:
        """An open-ended range is declared, not absent — the view carries one
        bound and the predicate must see it."""
        found = evaluate_criteria(
            self._criteria(industries=(), countries=(), employees_maximum=None),
            employees=50,
        )

        assert {v.kind: v.verdict for v in found}[CriterionKind.EMPLOYEES] is Verdict.NO

    def test_it_returns_no_overall_answer(self) -> None:
        """⛔ **Deliberate.** Rolling three verdicts into *"matches"* needs a
        rule for `UNMEASURED`, and every available rule is a judgement that
        belongs to the consumer with a reason for it."""
        found = evaluate_criteria(self._criteria(), industry="Fintech")

        assert isinstance(found, tuple)
        assert not hasattr(found, "matches")

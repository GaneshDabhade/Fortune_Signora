"""The synthesis contract — what AI may return, and what it may not.

**Built before there is any prose to be tempted by.** The specification is one
sentence: *a synthesis must be incapable of increasing the repository's
knowledge; it may only reorganize it.* These assert that it cannot.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from modules.sales_engagement.domain.synthesis import (
    Passage,
    SynthesisRefusedError,
    SynthesisSource,
    validate,
)
from modules.sales_engagement.public import CommitteeRoleRef, Evidence, reason

NOW = datetime(2026, 8, 3, tzinfo=UTC)
ACCOUNT = UUID("22222222-2222-4222-8222-222222222222")
CHAMPION = CommitteeRoleRef(title="VP Engineering", part="champion")
BUYER = CommitteeRoleRef(title="CFO", part="economic_buyer")

APPOINTMENT = Evidence(
    event_id=uuid4(),
    type_key="leadership_appointed",
    summary="Appointed a new VP of Engineering",
    occurred_at=NOW - timedelta(days=20),
    corroborating_providers=2,
    names_title="VP of Engineering",
)


def source() -> SynthesisSource:
    return SynthesisSource(
        reasoning=reason(
            account_id=ACCOUNT,
            committee=(CHAMPION, BUYER),
            evidence=(APPOINTMENT,),
            now=NOW,
        ),
        fits=(),
        product=None,
    )


def ok(text: str, *cites: str) -> tuple[Passage, ...]:
    return (Passage(text=text, cites=cites or ("recommendation",)),)


class TestASynthesisMayOnlyReorganize:
    def test_a_passage_grounded_in_the_reasoning_is_accepted(self) -> None:
        result = validate(
            ok("They appointed a new VP of Engineering.", "VP Engineering"),
            source(),
            inference_id=uuid4(),
        )

        assert len(result.passages) == 1

    def test_it_may_cite_the_recommendation_itself(self) -> None:
        result = validate(ok("Approach them now."), source(), inference_id=uuid4())

        assert result.passages[0].cites == ("recommendation",)

    def test_a_synthesis_is_constructible_only_through_validation(self) -> None:
        """`Synthesis` carries the inference that produced it, so a refusal and
        a success are distinguishable in the operational record."""
        result = validate(ok("Approach them now."), source(), inference_id=uuid4())

        assert result.inference_id is not None


class TestFreeFloatingProseIsRefused:
    def test_a_passage_citing_nothing_is_refused(self) -> None:
        with pytest.raises(SynthesisRefusedError, match="cites nothing"):
            validate((Passage(text="They seem ready.", cites=()),), source(), inference_id=uuid4())

    def test_a_citation_that_does_not_resolve_is_refused(self) -> None:
        with pytest.raises(SynthesisRefusedError, match="did not produce"):
            validate(ok("Talk to them.", "Chief Revenue Officer"), source(), inference_id=uuid4())

    def test_an_empty_synthesis_explains_nothing(self) -> None:
        with pytest.raises(SynthesisRefusedError, match="explains nothing"):
            validate((), source(), inference_id=uuid4())


class TestInventedConfidenceChronologyAndUrgency:
    """**All three arrive as numbers**, and none of them is detectable by
    asking a model to behave."""

    def test_an_invented_percentage_is_refused(self) -> None:
        with pytest.raises(SynthesisRefusedError, match="'73'"):
            validate(
                ok("There is a 73% chance they buy.", "recommendation"),
                source(),
                inference_id=uuid4(),
            )

    def test_an_invented_chronology_is_refused(self) -> None:
        with pytest.raises(SynthesisRefusedError, match="nothing in the reasoning derived"):
            validate(
                ok("They have been evaluating for 9 months.", "recommendation"),
                source(),
                inference_id=uuid4(),
            )

    def test_a_number_the_reasoning_did_state_is_allowed(self) -> None:
        """The recommendation says *20 days ago*. Repeating it is
        reorganization; inventing another figure is not."""
        result = validate(
            ok("It happened 20 days ago.", "recommendation"), source(), inference_id=uuid4()
        )

        assert result.passages


class TestInventedNames:
    """**A competitor, initiative, department, technology, product or person
    the graph never mentioned is an invention whatever it is called.** One
    rule, because all six are names."""

    @pytest.mark.parametrize(
        "claim",
        [
            "They are moving off Databricks.",
            "Their Platform Modernisation programme is underway.",
            "Speak to Sarah about it.",
            "They adopted Kubernetes last quarter.",
            "This suits Secure Edge best.",
        ],
    )
    def test_a_name_the_reasoning_never_used_is_refused(self, claim: str) -> None:
        with pytest.raises(SynthesisRefusedError, match="appears nowhere in the reasoning"):
            validate(ok(claim, "recommendation"), source(), inference_id=uuid4())

    def test_a_name_the_reasoning_did_use_is_allowed(self) -> None:
        result = validate(
            ok("Their VP of Engineering is the place to start.", "VP Engineering"),
            source(),
            inference_id=uuid4(),
        )

        assert result.passages

    def test_ordinary_sentence_capitals_are_not_treated_as_names(self) -> None:
        """Erring toward refusal is correct, but a synthesis that could not
        start a sentence would be refused every time."""
        result = validate(
            ok("The evidence is recent.", "recommendation"), source(), inference_id=uuid4()
        )

        assert result.passages


class TestTheRefusalNamesTheClaim:
    def test_it_says_which_figure_was_invented(self) -> None:
        """*"The synthesis was refused"* is not something an engineer can act
        on. *"It said 73% and nothing derived 73%"* is."""
        with pytest.raises(SynthesisRefusedError) as refused:
            validate(ok("A 73% chance.", "recommendation"), source(), inference_id=uuid4())

        assert "73" in str(refused.value)

    def test_it_says_which_name_was_invented(self) -> None:
        with pytest.raises(SynthesisRefusedError) as refused:
            validate(ok("Talk to Databricks.", "recommendation"), source(), inference_id=uuid4())

        assert "databricks" in str(refused.value).casefold()

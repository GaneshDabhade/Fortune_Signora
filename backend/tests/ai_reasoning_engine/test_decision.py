"""What the model may produce, and what it structurally cannot.

Nothing here calls a model. The shape of a reasoning result is deterministic
engineering behaviour; whether a model reasons *well* is the harness's
question (`make eval`), and conflating the two is what the two-tier split
exists to prevent.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from modules.ai_platform.public import GroundedStatement, output_schema
from modules.ai_reasoning_engine.domain.decision import (
    MINIMUM_PREMISES,
    ReasonedOutput,
)

FUNDING = "business_event:00000000-0000-0000-0000-000000000001"
HIRING = "business_event:00000000-0000-0000-0000-000000000002"
RETIREMENT = "business_event:00000000-0000-0000-0000-000000000003"


class TestEveryModelAuthoredSentenceIsChecked:
    def test_all_three_fields_are_offered_for_grounding(self) -> None:
        """Omitting any part from ``statements()`` would exempt it from
        grounding while leaving the output looking verified — the failure M8
        removed by deleting its un-cited summary, and reachable again through
        this method alone."""
        output = _reasoned()

        assert set(output.statements()) == {
            output.summary,
            output.proposition,
            *output.stated_reasoning,
        }

    def test_the_summary_is_grounded_like_everything_else(self) -> None:
        """The sentence a reader looks at first carries the most rhetorical
        weight and therefore the least entitlement to an exemption."""
        assert _reasoned().summary in _reasoned().statements()

    def test_a_summary_without_citations_cannot_be_constructed_uncited(self) -> None:
        """`GroundedStatement` requires an `evidence` tuple, so a bare string
        summary is not merely discouraged — it does not typecheck."""
        with pytest.raises(ValidationError):
            GroundedStatement(text="They are modernizing.")  # type: ignore[call-arg]


class TestTheShapeIsTheStopCondition:
    """M9 may conclude. It may not recommend, message, or rank.

    Those are unrepresentable rather than forbidden by convention: there is no
    field for them, so a model attempting one has nowhere to put it and the
    schema refuses the output.
    """

    @pytest.mark.parametrize(
        "field", ["next_action", "recommendation", "message", "priority", "rank", "confidence"]
    )
    def test_no_field_exists_for_an_action_a_message_or_a_ranking(self, field: str) -> None:
        assert field not in ReasonedOutput.model_fields, (
            f"`{field}` would move M9 into a later milestone's territory. Recommending and "
            "messaging are M11's; ranking accounts against each other is the Revenue "
            "Intelligence Platform's; confidence is derived rather than emitted (ADR-0030)."
        )

    def test_extra_fields_are_refused_outright(self) -> None:
        """`extra="forbid"` is inherited from `GroundedOutput`. Without it a
        model could return `next_action` and the field would simply be
        ignored — present in the response, absent from the type, and invisible
        to every test above."""
        with pytest.raises(ValidationError):
            ReasonedOutput(**{**_payload(), "next_action": "call the CFO"})

    def test_the_schema_sent_to_the_model_advertises_no_action_field(self) -> None:
        """The schema is derived from the type, so the model is never even
        *offered* somewhere to put an instruction."""
        properties = output_schema(ReasonedOutput)["properties"]
        assert isinstance(properties, dict)
        assert set(properties) == {"proposition", "summary", "stated_reasoning"}


class TestAConclusionMustRestOnMoreThanOneFact:
    def test_a_single_premise_is_refused(self) -> None:
        """Refused, not scored low. Reasoning means relating things that were
        not previously related; one premise cannot be related to anything, so
        the output is an observation with a conclusion's grammar — and M8
        already ships a capability for restating single facts."""
        with pytest.raises(ValidationError, match="narration rather than reasoning"):
            ReasonedOutput(
                proposition=GroundedStatement(text="They are modernizing.", evidence=(FUNDING,)),
                summary=GroundedStatement(text="Modernizing.", evidence=(FUNDING,)),
                stated_reasoning=(
                    GroundedStatement(text="They raised money.", evidence=(FUNDING,)),
                ),
            )

    def test_premises_are_counted_across_every_statement_not_per_sentence(self) -> None:
        """Two sentences each citing one *different* fact is a real inference
        relating two things. Counting per sentence would reject it."""
        output = ReasonedOutput(
            proposition=GroundedStatement(text="A replacement is underway.", evidence=(FUNDING,)),
            summary=GroundedStatement(text="Replacement underway.", evidence=(RETIREMENT,)),
            stated_reasoning=(),
        )

        assert output.premises == {FUNDING, RETIREMENT}

    def test_premises_are_distinct_facts_not_citation_count(self) -> None:
        """Three sentences all citing the same fact is one premise repeated,
        which is exactly the case the rule exists to catch."""
        with pytest.raises(ValidationError, match="1 distinct fact"):
            ReasonedOutput(
                proposition=GroundedStatement(text="Modernizing.", evidence=(FUNDING,)),
                summary=GroundedStatement(text="Modernizing.", evidence=(FUNDING,)),
                stated_reasoning=(
                    GroundedStatement(text="They raised money.", evidence=(FUNDING,)),
                    GroundedStatement(text="Money was raised.", evidence=(FUNDING,)),
                ),
            )

    def test_the_threshold_is_stated_once_and_read_from_the_domain(self) -> None:
        """If this test hard-coded 2, the rule would have two representations
        and the message would eventually disagree with the check."""
        assert MINIMUM_PREMISES == 2

    def test_a_well_supported_conclusion_is_accepted(self) -> None:
        """The positive control. A validator that rejected everything would
        satisfy every test above."""
        assert len(_reasoned().premises) >= MINIMUM_PREMISES


class TestStatedReasoningIsNamedForWhatItIs:
    def test_the_field_is_not_called_chain_of_thought(self) -> None:
        """A model has no introspective access to its own computation. Since
        this field exists for audit and governance, a record misdescribing its
        own nature would be worse than none (ADR-0030, Decision 2)."""
        assert "stated_reasoning" in ReasonedOutput.model_fields
        for misleading in ("chain_of_thought", "reasoning_chain", "thoughts", "logic"):
            assert misleading not in ReasonedOutput.model_fields

    def test_every_step_carries_its_own_evidence(self) -> None:
        """The ordering is narrative rather than causal — but each step's
        *evidence* is real, which is what makes the field auditable at all."""
        for step in _reasoned().stated_reasoning:
            assert step.evidence


def _payload() -> dict[str, object]:
    return {
        "proposition": GroundedStatement(
            text="An ERP replacement programme is underway.", evidence=(RETIREMENT, HIRING)
        ),
        "summary": GroundedStatement(text="They are replacing their ERP.", evidence=(RETIREMENT,)),
        "stated_reasoning": (
            GroundedStatement(text="A system was retired.", evidence=(RETIREMENT,)),
            GroundedStatement(text="Implementation staff were hired.", evidence=(HIRING,)),
        ),
    }


def _reasoned() -> ReasonedOutput:
    return ReasonedOutput(**_payload())

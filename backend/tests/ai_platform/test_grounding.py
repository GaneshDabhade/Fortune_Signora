"""Grounding: does the output correspond to the evidence, or not.

Built around a **deliberately corrupt corpus** — recorded outputs that
fabricate a citation, invent a figure, cite nothing, or reach into another
workspace. Those are the failures the platform exists to catch, and the only
honest way to test a catcher is to hand it the thing it must catch.

Nothing here calls a model. These are deterministic guarantees verified
against fixtures, per the two-tier split (CLAUDE.md §10): a guarantee that
needs a GPU to verify is not a guarantee.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from modules.ai_platform.domain.errors import AIPlatformError
from modules.ai_platform.domain.evidence import (
    EvidenceFact,
    EvidenceRef,
    EvidenceSet,
    EvidenceSetBuilder,
)
from modules.ai_platform.domain.grounding import (
    GroundedOutput,
    GroundedStatement,
    SchemaViolationError,
    UngroundedOutputError,
    ViolationKind,
    check,
    output_schema,
    parse,
    verify,
)

ASSEMBLED = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)
WORKSPACE = UUID(int=42)

FUNDING = EvidenceRef(kind="business_event", id=UUID(int=1))
HIRING = EvidenceRef(kind="business_event", id=UUID(int=2))
SCORE = EvidenceRef(kind="buying_score", id=UUID(int=3))


class Narration(GroundedOutput):
    """A minimal grounded output, standing in for T121's narration."""

    points: tuple[GroundedStatement, ...]

    def statements(self) -> tuple[GroundedStatement, ...]:
        return self.points


def evidence() -> EvidenceSet:
    builder = EvidenceSetBuilder(WORKSPACE)
    builder.include(
        EvidenceFact(
            ref=FUNDING,
            workspace_id=WORKSPACE,
            summary="Raised 24M USD in a Series B round",
            attributes=(("amount", Decimal("24000000")),),
        )
    )
    builder.include(
        EvidenceFact(
            ref=HIRING,
            workspace_id=WORKSPACE,
            summary="Engineering headcount grew from 180 to 240",
            attributes=(("headcount", 240), ("previous_headcount", 180)),
        )
    )
    builder.include(
        EvidenceFact(
            ref=SCORE,
            workspace_id=WORKSPACE,
            summary="Commercial attention reached 62",
            attributes=(("value", 62), ("contested", False)),
        )
    )
    return builder.build(assembled_at=ASSEMBLED)


def said(text: str, *refs: EvidenceRef | str) -> GroundedStatement:
    tokens = tuple(r if isinstance(r, str) else r.token for r in refs)
    return GroundedStatement(text=text, evidence=tokens)


class TestGroundedOutputPasses:
    def test_a_statement_supported_by_its_citation_is_grounded(self) -> None:
        output = Narration(points=(said("This account raised a Series B.", FUNDING),))
        assert check(output, evidence()).is_grounded

    def test_a_figure_present_in_a_cited_fact_is_grounded(self) -> None:
        output = Narration(points=(said("They raised 24M USD.", FUNDING),))
        assert check(output, evidence()).is_grounded

    def test_a_grouped_figure_matches_its_plain_form(self) -> None:
        """24,000,000 and 24000000 are one figure written two ways."""
        output = Narration(points=(said("They raised 24,000,000 USD.", FUNDING),))
        assert check(output, evidence()).is_grounded

    def test_awkward_prose_fully_supported_still_passes(self) -> None:
        """Grounding validates truth, not language. This module has no
        opinion about how well anything reads."""
        output = Narration(points=(said("headcount. 240. grew. from 180", HIRING),))
        assert check(output, evidence()).is_grounded

    def test_a_statement_may_rest_on_several_facts(self) -> None:
        output = Narration(
            points=(said("Headcount reached 240 and attention reached 62.", HIRING, SCORE),)
        )
        assert check(output, evidence()).is_grounded

    def test_verify_returns_quietly_when_grounded(self) -> None:
        verify(Narration(points=(said("A Series B round.", FUNDING),)), evidence())


class TestFabricatedFactsFail:
    def test_a_citation_addressing_nothing_is_unresolved(self) -> None:
        """The signature of a fabricated fact — fluent prose, real-looking
        reference, nothing behind it."""
        invented = EvidenceRef(kind="business_event", id=uuid4())
        report = check(
            Narration(points=(said("They opened a Berlin office.", invented),)), evidence()
        )
        assert report.kinds() == {ViolationKind.UNRESOLVED_CITATION}

    @pytest.mark.parametrize(
        "token", ["not-a-reference", "business_event:not-a-uuid", "", ":" + str(UUID(int=1))]
    )
    def test_a_citation_that_does_not_parse_is_malformed(self, token: str) -> None:
        """Distinct from unresolved: one is a broken reference, the other a
        well-formed reference to nothing, and they have different causes."""
        report = check(Narration(points=(said("Something happened.", token),)), evidence())
        assert report.kinds() == {ViolationKind.MALFORMED_CITATION}

    def test_a_statement_citing_nothing_is_unsupportable(self) -> None:
        report = check(
            Narration(points=(GroundedStatement(text="They are ready to buy.", evidence=()),)),
            evidence(),
        )
        assert report.kinds() == {ViolationKind.UNCITED_STATEMENT}

    def test_an_uncited_statement_is_reported_once_not_per_figure(self) -> None:
        report = check(
            Narration(points=(GroundedStatement(text="They grew 40% to 900.", evidence=()),)),
            evidence(),
        )
        assert len(report.violations) == 1


class TestInventedQuantitiesFail:
    """The characteristic failure of this product: not an invented company,
    an invented figure."""

    def test_a_figure_in_no_cited_fact_is_ungrounded(self) -> None:
        report = check(Narration(points=(said("Headcount grew 40%.", HIRING),)), evidence())
        assert report.kinds() == {ViolationKind.UNGROUNDED_QUANTITY}
        assert "40" in report.violations[0].detail

    def test_a_figure_from_an_uncited_fact_is_ungrounded(self) -> None:
        """A statement citing the hiring event may not borrow the funding
        amount. Quantities are checked against what *this* statement cited."""
        report = check(Narration(points=(said("They raised 24M.", HIRING),)), evidence())
        assert report.kinds() == {ViolationKind.UNGROUNDED_QUANTITY}

    def test_the_same_figure_borrowed_with_the_right_citation_passes(self) -> None:
        assert check(Narration(points=(said("They raised 24M.", FUNDING),)), evidence()).is_grounded

    def test_a_figure_that_merely_contains_a_real_one_is_ungrounded(self) -> None:
        """2400 is not 240. Tokenised comparison, never substring."""
        report = check(Narration(points=(said("Headcount reached 2400.", HIRING),)), evidence())
        assert report.kinds() == {ViolationKind.UNGROUNDED_QUANTITY}

    def test_a_trailing_zero_decimal_matches_its_shorter_form(self) -> None:
        """Evidence holding 1.50 and prose writing 1.5 are one figure. Left
        unnormalised, a legitimate response would be rejected — a false
        negative, which is the direction that quietly erodes trust in the
        check itself."""
        ratio = EvidenceRef(kind="signal", id=UUID(int=4))
        builder = EvidenceSetBuilder(WORKSPACE)
        builder.include(
            EvidenceFact(
                ref=ratio,
                workspace_id=WORKSPACE,
                summary="Expansion ratio recorded",
                attributes=(("ratio", Decimal("1.50")),),
            )
        )
        evidence_set = builder.build(assembled_at=ASSEMBLED)

        assert check(
            Narration(points=(said("The ratio is 1.5.", ratio),)), evidence_set
        ).is_grounded

    def test_a_typed_attribute_licenses_its_own_figure(self) -> None:
        """62 appears in the score's summary and as a typed value. The typed
        half is why this is arithmetic rather than a guess."""
        assert check(
            Narration(points=(said("Attention stands at 62.", SCORE),)), evidence()
        ).is_grounded

    def test_a_boolean_attribute_licenses_no_figure(self) -> None:
        """`contested` is False, which reads as "False" and contains no
        digits — so it permits neither 0 nor 1. Asserted because the
        property matters, not because any code defends it: a guard would be
        dead code, and mutation testing showed exactly that."""
        report = check(Narration(points=(said("There were 0 objections.", SCORE),)), evidence())
        assert report.kinds() == {ViolationKind.UNGROUNDED_QUANTITY}

    def test_every_invented_figure_is_reported(self) -> None:
        report = check(Narration(points=(said("Grew 40% across 7 regions.", HIRING),)), evidence())
        assert len(report.violations) == 2


class TestWorkspaceEscapeFails:
    def test_a_fact_from_another_workspace_is_reported(self) -> None:
        """Unreachable through the builder, and asserted anyway — the same
        defence-in-depth as RLS plus an explicit workspace filter."""
        intruder = EvidenceFact(
            ref=EvidenceRef(kind="signal", id=UUID(int=9)),
            workspace_id=uuid4(),
            summary="Another tenant's signal",
        )
        # Constructed around the builder deliberately: this is the state the
        # check exists to catch, and it cannot be reached the normal way.
        smuggled = EvidenceSet.__new__(EvidenceSet)
        object.__setattr__(smuggled, "workspace_id", WORKSPACE)
        object.__setattr__(smuggled, "facts", (intruder,))
        object.__setattr__(smuggled, "assembled_at", ASSEMBLED)

        report = check(Narration(points=(said("Something.", intruder.ref),)), smuggled)
        assert report.kinds() == {ViolationKind.WORKSPACE_ESCAPE}


class TestSchemaViolationsAreDistinct:
    def test_output_that_is_not_json_fails_to_parse(self) -> None:
        with pytest.raises(SchemaViolationError):
            parse(Narration, "I'm afraid I can't help with that.")

    def test_output_missing_a_required_field_fails_to_parse(self) -> None:
        with pytest.raises(SchemaViolationError):
            parse(Narration, '{"points": [{"text": "hello"}]}')

    def test_an_invented_field_fails_to_parse(self) -> None:
        """`extra="forbid"`: a model that invents a *field* fails here, just
        as one inventing a *fact* fails in check."""
        with pytest.raises(SchemaViolationError):
            parse(
                Narration,
                '{"points": [{"text": "hi", "evidence": [], "confidence": 0.9}]}',
            )

    def test_valid_output_parses_into_the_declared_type(self) -> None:
        parsed = parse(
            Narration,
            '{"points": [{"text": "A Series B round.", "evidence": ["' + FUNDING.token + '"]}]}',
        )
        assert parsed.statements()[0].text == "A Series B round."

    def test_a_schema_violation_is_not_a_grounding_failure(self) -> None:
        """Three different things break for three different reasons, and one
        metric covering all of them would say nothing useful about any."""
        assert not issubclass(SchemaViolationError, UngroundedOutputError)
        assert issubclass(SchemaViolationError, AIPlatformError)


class TestTheSchemaCannotDriftFromTheValidator:
    def test_the_requested_schema_is_derived_from_the_validating_type(self) -> None:
        schema = output_schema(Narration)
        assert schema["title"] == "Narration"
        assert "points" in schema["properties"]

    def test_the_schema_forbids_additional_properties(self) -> None:
        assert output_schema(Narration)["additionalProperties"] is False

    def test_a_base_output_that_names_no_statements_refuses(self) -> None:
        with pytest.raises(NotImplementedError, match="which of its parts are statements"):
            GroundedOutput().statements()


class TestGroundingIsDeterministicAndPure:
    def test_the_same_inputs_always_produce_the_same_report(self) -> None:
        output = Narration(
            points=(
                said("Grew 40%.", HIRING),
                said("Raised 24M.", FUNDING),
                GroundedStatement(text="Ready to buy.", evidence=()),
            )
        )
        reports = {check(output, evidence()) for _ in range(5)}
        assert len(reports) == 1

    def test_violations_are_ordered_by_statement(self) -> None:
        output = Narration(
            points=(
                said("Raised 24M.", FUNDING),
                GroundedStatement(text="Ready to buy.", evidence=()),
                said("Grew 40%.", HIRING),
            )
        )
        indexes = [v.statement for v in check(output, evidence()).violations]
        assert indexes == sorted(indexes) == [1, 2]

    def test_checking_does_not_alter_the_evidence(self) -> None:
        """It validates; it never repairs. A validator that quietly fixed
        its input would make the failure rate unmeasurable."""
        original = evidence()
        before = original.digest
        check(Narration(points=(said("Grew 40%.", HIRING),)), original)
        assert original.digest == before
        assert len(original) == 3

    def test_verify_raises_carrying_the_whole_report(self) -> None:
        output = Narration(
            points=(said("Grew 40%.", HIRING), GroundedStatement(text="Ready.", evidence=()))
        )
        with pytest.raises(UngroundedOutputError) as caught:
            verify(output, evidence())
        assert caught.value.report.kinds() == {
            ViolationKind.UNGROUNDED_QUANTITY,
            ViolationKind.UNCITED_STATEMENT,
        }

    def test_an_unresolved_citation_suppresses_the_quantity_check(self) -> None:
        """The permitted figures are unknown when a citation does not
        resolve, so reporting every number would bury the real problem."""
        report = check(
            Narration(points=(said("Grew 40% to 900.", EvidenceRef("signal", uuid4())),)),
            evidence(),
        )
        assert report.kinds() == {ViolationKind.UNRESOLVED_CITATION}

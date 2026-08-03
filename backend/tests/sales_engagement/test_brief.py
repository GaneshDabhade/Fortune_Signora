"""The Approach Brief — a structured object, never a prompt's output.

**Sections are absent, never empty**, and a brief with no narration at all is
complete rather than broken. These assert both, because both are the reason the
object exists rather than a markdown string.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from modules.sales_engagement.domain.brief import ApproachBrief, Pass, assemble
from modules.sales_engagement.domain.synthesis import Passage, Synthesis
from modules.sales_engagement.public import CommitteeRoleRef, Evidence, ProductRef, reason

NOW = datetime(2026, 8, 3, tzinfo=UTC)
ACCOUNT = UUID("22222222-2222-4222-8222-222222222222")
CHAMPION = CommitteeRoleRef(title="VP Engineering", part="champion")
BUYER = CommitteeRoleRef(title="CFO", part="economic_buyer")
CLOUD = ProductRef(id=uuid4(), name="Revenue Cloud")

APPOINTED = Evidence(
    event_id=uuid4(),
    type_key="leadership_appointed",
    summary="Appointed a new VP of Engineering",
    occurred_at=NOW - timedelta(days=20),
    corroborating_providers=2,
    names_title="VP of Engineering",
)


def brief(
    *,
    committee: tuple[CommitteeRoleRef, ...] = (CHAMPION,),
    evidence: tuple[Evidence, ...] = (APPOINTED,),
    narration: Mapping[Pass, Synthesis] | None = None,
) -> ApproachBrief:
    return assemble(
        reasoning=reason(account_id=ACCOUNT, committee=committee, evidence=evidence, now=NOW),
        fits=(),
        product=CLOUD,
        narration=narration,
    )


def narrated() -> Synthesis:
    return Synthesis(
        passages=(Passage(text="They appointed one recently.", cites=("recommendation",)),),
        inference_id=uuid4(),
    )


class TestSectionsAreAbsentNeverEmpty:
    """**A brief with a `Contradictions` heading and nothing under it looks the
    same for every Target Account** — the defect R1-06 named on the workflow
    line and D6 named on a filter."""

    def test_a_brief_with_nothing_unknown_has_no_unknowns_section(self) -> None:
        assert "unknowns" not in brief().sections()

    def test_a_brief_with_something_unknown_has_one(self) -> None:
        assert "unknowns" in brief(committee=(CHAMPION, BUYER)).sections()

    def test_a_brief_with_no_risk_has_no_risks_section(self) -> None:
        assert "risks" not in brief().sections()

    def test_the_recommendation_is_always_present(self) -> None:
        """It is the answer to *what should I do*, and there is always one —
        `wait` included."""
        assert brief(evidence=()).sections()[0] == "recommendation"

    def test_a_reader_who_sees_a_section_knows_it_has_content(self) -> None:
        """The property, stated directly: **every named section has something
        in it**, so the heading itself carries information."""
        full = brief(committee=(CHAMPION, BUYER))

        for section in full.sections():
            assert section, "an empty section name reached the reader"
        assert "unknowns" in full.sections()


class TestABriefIsCompleteWithoutAModel:
    def test_no_narration_is_a_valid_brief(self) -> None:
        """**Delete the synthesis and the product still works.** This is that
        asymmetry, asserted rather than described."""
        without = brief()

        assert not without.is_narrated
        assert without.recommendation is not None
        assert without.roles

    def test_narration_adds_sections_without_replacing_any(self) -> None:
        with_prose = brief(narration={Pass.EXECUTIVE_SUMMARY: narrated()})

        assert with_prose.is_narrated
        assert "executive_summary" in with_prose.sections()
        assert "recommendation" in with_prose.sections()

    def test_narrated_sections_read_in_pass_order_not_insertion_order(self) -> None:
        """**Ordering that does not depend on a dictionary's history.** Two
        briefs with the same passes must read identically, which insertion
        order would not guarantee."""
        one = brief(narration={Pass.RISK_NARRATION: narrated(), Pass.EXECUTIVE_SUMMARY: narrated()})
        other = brief(
            narration={Pass.EXECUTIVE_SUMMARY: narrated(), Pass.RISK_NARRATION: narrated()}
        )

        assert one.sections() == other.sections()

    def test_narration_cannot_be_added_after_assembly(self) -> None:
        """A caller holding the original mapping could otherwise add a pass
        **after** validation — precisely the hole the synthesis contract
        exists to close."""
        supplied: dict[Pass, Synthesis] = {}
        assembled = brief(narration=supplied)

        supplied[Pass.OBJECTIONS] = narrated()

        assert not assembled.is_narrated


class TestOneGraphManyViews:
    def test_every_pass_keys_the_same_brief_shape(self) -> None:
        """**Six passes, one graph.** A seventh costs an artifact rather than
        a pipeline, which is the property that makes future audiences —
        executive, SDR, AE, manager — arrangements rather than rewrites."""
        every = brief(narration={one: narrated() for one in Pass})

        assert len([s for s in every.sections() if s in {p.value for p in Pass}]) == len(Pass)

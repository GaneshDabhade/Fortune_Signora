"""The ICP as an addressable thing, and the rules that keep it honest.

**These assert the decisions in [ADR-0041](../../../docs/architecture/adr/0041-icp-aggregate.md)**,
not the shape of the code — each one would fail if the decision were reversed,
and several exist because the reasoning changed during discovery and the
earlier version would have passed a weaker test.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from modules.commercial_profile.domain.icp import EmployeeRange, IcpError
from modules.commercial_profile.domain.segment import (
    MAX_NAME,
    MAX_PRODUCTS,
    Segment,
    SegmentCriteria,
    SegmentState,
    SegmentTransition,
    SegmentTransitionError,
    SegmentVersion,
    next_state,
)

NOW = datetime(2026, 8, 2, 12, 0, tzinfo=UTC)
WORKSPACE = UUID("11111111-1111-4111-8111-111111111111")
ACTOR = UUID("22222222-2222-4222-8222-222222222222")
OTHER = UUID("33333333-3333-4333-8333-333333333333")


def _criteria(**kw: object) -> SegmentCriteria:
    defaults: dict[str, object] = {"industries": ("Fintech",)}
    defaults.update(kw)
    return SegmentCriteria(**defaults)  # type: ignore[arg-type]


def _version(**kw: object) -> SegmentVersion:
    defaults: dict[str, object] = {
        "id": uuid4(),
        "segment_id": uuid4(),
        "workspace_id": WORKSPACE,
        "version": 1,
        "name": "Mid-market Fintech",
        "criteria": _criteria(),
        "product_ids": (uuid4(),),
        "created_at": NOW,
        "created_by": ACTOR,
    }
    defaults.update(kw)
    return SegmentVersion(**defaults)  # type: ignore[arg-type]


class TestTheSentenceThatBrokeTheOldModel:
    def test_one_segment_may_buy_several_products(self) -> None:
        """**The whole reason the aggregate changed.** *"Revenue Cloud + CPQ +
        Billing, sold together to mid-market fintech"* is one statement, and
        the previous model could only record it as three that drift."""
        products = (uuid4(), uuid4(), uuid4())
        assert _version(product_ids=products).product_ids == products

    def test_two_segments_may_buy_the_same_product(self) -> None:
        """*"We sell Revenue Cloud to fintech, and separately to insurers."*
        The old model refused this outright — one profile per product."""
        product = uuid4()
        first = _version(name="Mid-market Fintech", product_ids=(product,))
        second = _version(name="Enterprise Insurance", product_ids=(product,))
        assert first.product_ids == second.product_ids
        assert first.segment_id != second.segment_id

    def test_the_same_product_twice_in_one_segment_is_refused(self) -> None:
        product = uuid4()
        with pytest.raises(IcpError, match="listed twice"):
            _version(product_ids=(product, product))


class TestPublicationIsWhereExecutionInvariantsBind:
    """A draft exists for a human; a published segment exists for Signora."""

    def test_a_published_segment_must_name_a_product(self) -> None:
        """**Actionability, not identity.** Signora looks for companies that
        will buy *something the customer sells*; a segment naming nothing
        cannot be acted on by discovery, scoring or analytics."""
        with pytest.raises(IcpError, match="cannot be acted on"):
            _version(product_ids=())

    def test_criteria_alone_are_a_complete_description(self) -> None:
        """**The identity test, asserted.** If products vanished tomorrow,
        *"mid-market fintech, 100–1000 employees"* would still describe a
        segment — which is why products are a relationship rather than
        identity, and why the rule above is about usefulness."""
        criteria = SegmentCriteria(
            industries=("Fintech",), employees=EmployeeRange(minimum=100, maximum=1000)
        )
        assert criteria.describes_nobody_in_particular is False

    def test_empty_criteria_are_allowed_to_exist_and_refused_at_publication(self) -> None:
        """Constructing them is legal — a draft is incomplete by definition.
        Publishing them is not."""
        empty = SegmentCriteria()
        assert empty.describes_nobody_in_particular is True
        with pytest.raises(IcpError, match="every company on earth"):
            _version(criteria=empty)

    def test_a_broad_segment_is_never_refused(self) -> None:
        """**The gate asks whether Signora can act, never whether the segment
        is good.** A customer describing a wide market is describing a real
        strategy, and refusing it would be this module judging their business."""
        wide = _version(
            criteria=SegmentCriteria(industries=("Software", "Finance", "Retail")),
            product_ids=tuple(uuid4() for _ in range(5)),
        )
        assert len(wide.product_ids) == 5


class TestNaming:
    def test_a_segment_is_named_in_the_customers_words(self) -> None:
        assert _version(name="UK Insurance").name == "UK Insurance"

    def test_a_blank_name_is_refused(self) -> None:
        with pytest.raises(IcpError, match="recognise in a list"):
            _version(name="   ")

    def test_a_paragraph_is_not_a_name(self) -> None:
        with pytest.raises(IcpError, match=str(MAX_NAME)):
            _version(name="x" * (MAX_NAME + 1))

    def test_capitalisation_is_recorded_as_typed(self) -> None:
        """The customer's own words, unnormalised — the rule the criteria
        already follow."""
        assert _criteria(industries=("FinTech",)).industries == ("FinTech",)


class TestTheLifecycleIsATable:
    def _transition(self, current: SegmentState, to: SegmentState) -> SegmentTransition:
        return next_state(
            current,
            to,
            at=NOW,
            by=ACTOR,
            segment_id=uuid4(),
            workspace_id=WORKSPACE,
            sequence=1,
            id=uuid4(),
        )

    @pytest.mark.parametrize(
        ("current", "to"),
        [
            (SegmentState.DRAFT, SegmentState.PUBLISHED),
            (SegmentState.PUBLISHED, SegmentState.ARCHIVED),
            (SegmentState.ARCHIVED, SegmentState.PUBLISHED),
        ],
    )
    def test_the_permitted_moves(self, current: SegmentState, to: SegmentState) -> None:
        assert self._transition(current, to).state is to

    @pytest.mark.parametrize(
        ("current", "to"),
        [
            (SegmentState.DRAFT, SegmentState.ARCHIVED),
            (SegmentState.PUBLISHED, SegmentState.DRAFT),
            (SegmentState.ARCHIVED, SegmentState.DRAFT),
            (SegmentState.PUBLISHED, SegmentState.PUBLISHED),
        ],
    )
    def test_the_refused_moves(self, current: SegmentState, to: SegmentState) -> None:
        with pytest.raises(SegmentTransitionError):
            self._transition(current, to)

    def test_archiving_is_reversible(self) -> None:
        """**Archive is not deletion with a nicer word.** Everything Signora
        found under a segment was found because of it, so retiring one must be
        undoable."""
        assert self._transition(SegmentState.ARCHIVED, SegmentState.PUBLISHED).state is (
            SegmentState.PUBLISHED
        )

    def test_publishing_again_is_not_a_transition(self) -> None:
        """**Republishing mints a version; the state does not move.** Treating
        it as a transition would fill the lifecycle log with rows that record
        no change of state."""
        with pytest.raises(SegmentTransitionError):
            self._transition(SegmentState.PUBLISHED, SegmentState.PUBLISHED)

    def test_a_transition_names_its_actor(self) -> None:
        """*"Who archived our EMEA segment?"* is asked during an incident, and
        this is the only moment the answer exists."""
        assert self._transition(SegmentState.DRAFT, SegmentState.PUBLISHED).actor_id == ACTOR

    def test_an_actor_cannot_be_omitted(self) -> None:
        """`by` is keyword-only with no default, on the rule `next_state`
        already follows in the Opportunity Engine."""
        with pytest.raises(TypeError):
            next_state(  # type: ignore[call-arg]
                SegmentState.DRAFT,
                SegmentState.PUBLISHED,
                at=NOW,
                segment_id=uuid4(),
                workspace_id=WORKSPACE,
                sequence=1,
                id=uuid4(),
            )


class TestIdentityOutlivesContent:
    def test_a_segment_carries_no_content_at_all(self) -> None:
        """**What makes a citation resolvable forever.** If the versioned row
        were the segment, every revision would mint a new id and every
        citation an opportunity ever made would become unresolvable."""
        fields = set(Segment.__dataclass_fields__)
        assert fields == {"id", "workspace_id", "created_at", "created_by"}

    def test_a_version_names_the_segment_it_belongs_to(self) -> None:
        segment_id = uuid4()
        assert _version(segment_id=segment_id).segment_id == segment_id

    def test_a_revision_names_its_predecessor(self) -> None:
        first = _version(version=1)
        second = _version(version=2, segment_id=first.segment_id, supersedes=first.id)
        assert second.supersedes == first.id
        assert second.version == first.version + 1

    def test_the_first_version_supersedes_nothing(self) -> None:
        assert _version(version=1).supersedes is None

    def test_a_version_below_one_is_refused(self) -> None:
        with pytest.raises(IcpError, match="version 1 or above"):
            _version(version=0)

    def test_a_segment_carries_no_state(self) -> None:
        """**State is derived from the latest transition, never stored.** A
        column here would answer *"is it archived?"* and lose *"who archived
        it, and when?"*"""
        assert "state" not in Segment.__dataclass_fields__


class TestTheModuleStillHoldsNoJudgement:
    """The invariant `test_boundary.py` guards, asserted directly for the new
    aggregate: this module records, and never rates."""

    def test_no_type_here_carries_a_verdict(self) -> None:
        forbidden = {"score", "rank", "priority", "fit", "weight", "propensity", "quality"}
        for kind in (Segment, SegmentVersion, SegmentCriteria, SegmentTransition):
            names = {name.casefold() for name in kind.__dataclass_fields__}
            assert not names & forbidden, f"{kind.__name__} names a judgement"

    def test_products_are_limited_only_by_a_typo_guard(self) -> None:
        """The real bound is the catalog. This refuses a stray paste, not a
        strategy."""
        with pytest.raises(IcpError, match=str(MAX_PRODUCTS)):
            _version(product_ids=tuple(uuid4() for _ in range(MAX_PRODUCTS + 1)))


class TestAnotherOrganizationIsNeverImplied:
    def test_every_row_carries_its_workspace(self) -> None:
        """Each of the three tables is workspace-owned in its own right —
        deriving a version's workspace through its segment would make an
        RLS policy depend on a join."""
        for kind in (Segment, SegmentVersion, SegmentTransition):
            assert "workspace_id" in kind.__dataclass_fields__

    def test_a_transition_sequence_starts_at_zero(self) -> None:
        with pytest.raises(IcpError, match="starts at 0"):
            SegmentTransition(
                id=uuid4(),
                segment_id=uuid4(),
                workspace_id=WORKSPACE,
                sequence=-1,
                state=SegmentState.DRAFT,
                occurred_at=NOW,
                actor_id=OTHER,
            )

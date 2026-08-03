"""Commercial Fit Reasoning — which of the Signora Customer's products fits.

**Likely, never certain.** A Buying Committee is declared per product and an
Opportunity has no product, so something must infer one — and the properties
under test are what keep that inference honest: it explains itself, it refuses
to break a tie, and it consults nothing when the seller has already answered.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from modules.sales_engagement.application.approach import (
    Approach,
    ApproachInput,
    AssembleApproach,
)
from modules.sales_engagement.public import (
    CommitteeRoleRef,
    Evidence,
    FitDimension,
    ProductFit,
    ProductRef,
    ReasoningError,
    Strength,
    fit,
    likely,
)

NOW = datetime(2026, 8, 3, tzinfo=UTC)
WORKSPACE = UUID("11111111-1111-4111-8111-111111111111")
ACCOUNT = UUID("22222222-2222-4222-8222-222222222222")

CLOUD = ProductRef(id=UUID("aaaaaaaa-0000-4000-8000-000000000001"), name="Revenue Cloud")
SECURE = ProductRef(id=UUID("aaaaaaaa-0000-4000-8000-000000000002"), name="Secure Edge")

ENGINEERING = CommitteeRoleRef(title="VP Engineering", part="champion")
SECURITY = CommitteeRoleRef(title="Head of Security", part="gatekeeper")


def names(title: str, *, providers: int = 2, days_ago: int = 10) -> Evidence:
    return Evidence(
        event_id=uuid4(),
        type_key="leadership_appointed",
        summary=f"Appointed a new {title}",
        occurred_at=NOW - timedelta(days=days_ago),
        corroborating_providers=providers,
        names_title=title,
    )


class TestWhichProductAndWhy:
    def test_the_product_whose_committee_the_evidence_names(self) -> None:
        committees = {CLOUD: (ENGINEERING,), SECURE: (SECURITY,)}

        (best,) = fit(committees, (names("VP of Engineering"),), now=NOW)

        assert best.product is CLOUD

    def test_which_product_and_why_are_the_same_answer(self) -> None:
        """**Structural rather than prose.** A seller can disagree with a
        specific reason; a paragraph they can only accept or reject whole is a
        verdict, not an argument."""
        committees = {CLOUD: (ENGINEERING,)}

        (best,) = fit(committees, (names("VP of Engineering"),), now=NOW)

        (why,) = best.reasons
        assert why.dimension is FitDimension.COMMITTEE_OVERLAP
        assert "VP Engineering" in why.detail
        assert "appointed a new" in why.detail.lower()

    def test_a_fit_with_no_reason_cannot_exist(self) -> None:
        with pytest.raises(ReasoningError, match="states no reason"):
            ProductFit(product=CLOUD, strength=Strength.STRONG, reasons=())

    def test_a_product_the_evidence_says_nothing_about_is_absent(self) -> None:
        """A portfolio of nine with one fit should read as one fit, not as
        nine rows of which eight say nothing."""
        committees = {CLOUD: (ENGINEERING,), SECURE: (SECURITY,)}

        fits = fit(committees, (names("VP of Engineering"),), now=NOW)

        assert [one.product for one in fits] == [CLOUD]

    def test_more_named_roles_ranks_above_fewer_at_the_same_strength(self) -> None:
        committees = {CLOUD: (ENGINEERING, SECURITY), SECURE: (SECURITY,)}
        evidence = (names("VP of Engineering"), names("Head of Security"))

        fits = fit(committees, evidence, now=NOW)

        assert fits[0].product is CLOUD


class TestATieIsAQuestionNotACoinToss:
    def test_two_products_fitting_equally_produce_no_answer(self) -> None:
        """**Guessing between them would be the platform inventing a
        commercial decision it has no evidence for** — the same refusal that
        stops it resolving a disagreement between two providers."""
        committees = {CLOUD: (ENGINEERING,), SECURE: (ENGINEERING,)}

        fits = fit(committees, (names("VP of Engineering"),), now=NOW)

        assert len(fits) == 2
        assert likely(fits) is None

    def test_nothing_fitting_produces_no_answer_either(self) -> None:
        """*Signora cannot tell*, said out loud rather than by omission."""
        assert likely(()) is None

    def test_a_clear_winner_is_answered(self) -> None:
        committees = {CLOUD: (ENGINEERING,), SECURE: (SECURITY,)}

        fits = fit(committees, (names("VP of Engineering"),), now=NOW)

        assert likely(fits) is CLOUD


class FakeCommittees:
    def __init__(self, by_product: dict[UUID, tuple[CommitteeRoleRef, ...]]) -> None:
        self._by_product = by_product

    async def committee(
        self, workspace_id: UUID, *, product_id: UUID
    ) -> tuple[CommitteeRoleRef, ...]:
        return self._by_product.get(product_id, ())


class FakeEvidence:
    def __init__(self, evidence: tuple[Evidence, ...]) -> None:
        self._evidence = evidence

    async def evidence(self, workspace_id: UUID, *, account_id: UUID) -> tuple[Evidence, ...]:
        return self._evidence


class FakePortfolio:
    def __init__(self, products: tuple[ProductRef, ...]) -> None:
        self._products = products

    async def portfolio(self, workspace_id: UUID) -> tuple[ProductRef, ...]:
        return self._products


def assemble(
    *,
    committees: dict[UUID, tuple[CommitteeRoleRef, ...]],
    evidence: tuple[Evidence, ...],
    portfolio: tuple[ProductRef, ...],
) -> AssembleApproach:
    return AssembleApproach(
        committees=FakeCommittees(committees),
        evidence=FakeEvidence(evidence),
        portfolio=FakePortfolio(portfolio),
        clock=lambda: NOW,
    )


class TestInferringWithoutAnOverride:
    async def test_it_infers_the_product_and_reasons_against_its_committee(self) -> None:
        approach = assemble(
            committees={CLOUD.id: (ENGINEERING,), SECURE.id: (SECURITY,)},
            evidence=(names("VP of Engineering"),),
            portfolio=(CLOUD, SECURE),
        )

        result: Approach = await approach.execute(
            ApproachInput(workspace_id=WORKSPACE, account_id=ACCOUNT)
        )

        assert result.product is CLOUD
        assert result.reasoning.roles[0].role is ENGINEERING

    async def test_a_tie_becomes_an_unknown_the_seller_can_answer(self) -> None:
        """**The open question is *which product*, not *whether anything is
        happening*** — so the roles and their evidence are still shown while
        the seller answers it."""
        approach = assemble(
            committees={CLOUD.id: (ENGINEERING,), SECURE.id: (ENGINEERING,)},
            evidence=(names("VP of Engineering"),),
            portfolio=(CLOUD, SECURE),
        )

        result = await approach.execute(ApproachInput(workspace_id=WORKSPACE, account_id=ACCOUNT))

        assert result.product is None
        assert any("Revenue Cloud" in one.question for one in result.reasoning.unknowns)
        assert result.reasoning.roles, "a tie left the seller with nothing to read"

    async def test_an_empty_portfolio_says_nothing_rather_than_guessing(self) -> None:
        approach = assemble(committees={}, evidence=(names("VP of Engineering"),), portfolio=())

        result = await approach.execute(ApproachInput(workspace_id=WORKSPACE, account_id=ACCOUNT))

        assert result.product is None
        assert result.fits == ()

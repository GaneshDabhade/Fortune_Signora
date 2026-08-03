"""The commercial reasoning graph, against fakes.

**No model is called here, and none may be.** The properties under test are
what make the conclusion defensible to a Signora Customer who asks why they
were shown this: it is derived from evidence, it says what it does not know,
it says what could be wrong, and it never picks a winner between two providers
that disagree.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from modules.sales_engagement.public import (
    STALE_AFTER_DAYS,
    ApproachInput,
    AssembleApproach,
    CommitteeRoleRef,
    Evidence,
    NextAction,
    RankedRole,
    ReasoningError,
    Recommendation,
    RiskKind,
    Strength,
    contradictions,
    rank_roles,
    reason,
    risks,
    unknowns,
)

NOW = datetime(2026, 8, 3, tzinfo=UTC)
WORKSPACE = UUID("11111111-1111-4111-8111-111111111111")
ACCOUNT = UUID("22222222-2222-4222-8222-222222222222")
PRODUCT = UUID("33333333-3333-4333-8333-333333333333")

CHAMPION = CommitteeRoleRef(title="VP Engineering", part="champion")
BUYER = CommitteeRoleRef(title="CFO", part="economic_buyer")
GATEKEEPER = CommitteeRoleRef(title="Head of Security", part="gatekeeper")


def appointed(
    *,
    title: str | None = "VP of Engineering",
    providers: int = 2,
    days_ago: int = 20,
    type_key: str = "leadership_appointed",
) -> Evidence:
    return Evidence(
        event_id=uuid4(),
        type_key=type_key,
        summary=f"Appointed a new {title}",
        occurred_at=NOW - timedelta(days=days_ago),
        corroborating_providers=providers,
        names_title=title,
    )


class TestTheJoinNothingPerformed:
    """**The capability, in one comparison.** The Signora Customer declared
    that their champion is the VP of Engineering. The pipeline detected that a
    VP of Engineering was appointed at this Target Account. Nothing in Signora
    joined those two facts before this module."""

    def test_a_declared_role_ranks_when_the_evidence_names_it(self) -> None:
        (ranked, *rest) = rank_roles((CHAMPION,), (appointed(),), now=NOW)

        assert ranked.role is CHAMPION
        assert ranked.strength is Strength.STRONG
        assert ranked.support and ranked.why_not is None
        assert rest == []

    def test_the_titles_need_not_match_exactly(self) -> None:
        """A Signora Customer declares *VP Engineering*; a provider reports
        *VP of Engineering*. **Neither is wrong**, and a strict comparison
        would rank nothing at all in practice."""
        (ranked,) = rank_roles((CHAMPION,), (appointed(title="VP of Engineering"),), now=NOW)

        assert ranked.strength is not None

    def test_no_model_is_involved_in_the_join(self) -> None:
        """A string comparison against a declared title. **If the system
        already knows something deterministically, never ask a model to invent
        it again** — and this test exists so that a future refactor toward one
        has to delete it deliberately."""
        first = reason(account_id=ACCOUNT, committee=(CHAMPION,), evidence=(appointed(),), now=NOW)
        second = reason(account_id=ACCOUNT, committee=(CHAMPION,), evidence=(appointed(),), now=NOW)

        assert first.roles[0].strength == second.roles[0].strength
        assert first.unknowns == second.unknowns


class TestTheDeclarationIsAPreferenceAndTheEvidenceIsAFact:
    def test_the_customer_s_ordering_is_not_the_ranking(self) -> None:
        """**Commercial Profile refuses to hold an influence model** and a
        structural test enforces it. Reading its declared order as a ranking
        here would import the model it refused to keep."""
        committee = (BUYER, CHAMPION)

        (first, *rest) = rank_roles(committee, (appointed(),), now=NOW)

        assert first.role is CHAMPION, "the declared order decided the ranking"
        assert rest[0].role is BUYER

    def test_strongest_first_among_the_ranked(self) -> None:
        weakly = appointed(title="Head of Security", providers=1)
        strongly = appointed()

        ranked = rank_roles((GATEKEEPER, CHAMPION), (weakly, strongly), now=NOW)

        assert [one.strength for one in ranked[:2]] == [Strength.STRONG, Strength.REASONABLE]


class TestItSaysWhyNot:
    def test_an_unranked_role_carries_its_reason(self) -> None:
        """*"No evidence names your CFO"* is more useful to a seller than the
        CFO's silent absence from a list — and it is the sentence a ranked
        list structurally cannot carry."""
        ranked = rank_roles((CHAMPION, BUYER), (appointed(),), now=NOW)

        (unranked,) = [one for one in ranked if one.strength is None]
        assert unranked.role is BUYER
        assert unranked.why_not is not None

    def test_a_role_can_never_be_silently_absent(self) -> None:
        """**The type refuses it.** A role that is neither ranked with
        evidence nor unranked with a reason is a gap the reader has to explain
        to themselves, which is the failure this module exists to remove."""
        with pytest.raises(ReasoningError, match="either ranked"):
            RankedRole(role=CHAMPION, strength=None, support=(), why_not=None)

    def test_a_ranked_role_must_cite_something(self) -> None:
        with pytest.raises(ReasoningError, match="cites no evidence"):
            RankedRole(role=CHAMPION, strength=Strength.STRONG, support=())

    def test_every_declared_role_appears_somewhere(self) -> None:
        ranked = rank_roles((CHAMPION, BUYER, GATEKEEPER), (appointed(),), now=NOW)

        assert {one.role for one in ranked} == {CHAMPION, BUYER, GATEKEEPER}


class TestUnknownsAreComputedNotGuessed:
    """**An absence is a set difference**, which is why this is the cheapest
    section in the module and possibly the most valuable. Most platforms tell a
    seller what they know."""

    def test_a_role_nothing_names_becomes_an_unknown(self) -> None:
        ranked = rank_roles((CHAMPION, BUYER), (appointed(),), now=NOW)

        (gap,) = unknowns(ranked)
        assert gap.subject == "CFO"

    def test_it_carries_the_question_that_would_close_it(self) -> None:
        """Knowing the next question to ask is often worth more than another
        signal. A question a seller cannot say out loud is an admission rather
        than a lead."""
        ranked = rank_roles((BUYER,), (), now=NOW)

        (gap,) = unknowns(ranked)
        assert gap.question.endswith("?")
        assert "CFO" in gap.question

    def test_nothing_is_unknown_when_everything_ranked(self) -> None:
        ranked = rank_roles((CHAMPION,), (appointed(),), now=NOW)

        assert unknowns(ranked) == ()


class TestRisksAreNamedNeverResolved:
    def test_a_single_provider_is_reported_as_thin_support(self) -> None:
        ranked = rank_roles((CHAMPION,), (appointed(providers=1),), now=NOW)

        assert RiskKind.SINGLE_SOURCE in {one.kind for one in risks(ranked, now=NOW)}

    def test_ageing_evidence_is_reported_rather_than_trusted(self) -> None:
        old = appointed(days_ago=STALE_AFTER_DAYS + 1)

        ranked = rank_roles((CHAMPION,), (old,), now=NOW)

        assert ranked[0].strength is Strength.THIN
        assert RiskKind.STALE in {one.kind for one in risks(ranked, now=NOW)}

    def test_an_indirect_link_is_stated_rather_than_hidden(self) -> None:
        """A hiring surge bears on a champion without naming one. **Ranking on
        it is defensible; ranking on it silently is not.**"""
        surge = Evidence(
            event_id=uuid4(),
            type_key="workforce_surge",
            summary="Engineering headcount grew 42%",
            occurred_at=NOW - timedelta(days=10),
            corroborating_providers=2,
            names_title=None,
        )

        ranked = rank_roles((CHAMPION,), (surge,), now=NOW)

        assert ranked[0].strength is Strength.THIN
        assert RiskKind.INFERRED in {one.kind for one in risks(ranked, now=NOW)}

    def test_a_strong_role_carries_no_risk_of_its_own(self) -> None:
        ranked = rank_roles((CHAMPION,), (appointed(),), now=NOW)

        assert risks(ranked, now=NOW) == ()


class TestConfidenceIsNeverANumber:
    def test_strength_refuses_arithmetic(self) -> None:
        """**Three refusals in this platform, all the same one**: revenue is a
        band, `MatchStrength` refuses numeric conversion, and this refuses a
        percentage. A figure would imply an arithmetic nobody performed."""
        with pytest.raises(ValueError, match="invalid literal"):
            int(Strength.STRONG)
        with pytest.raises(TypeError):
            Strength.STRONG + 1  # type: ignore[operator]

    def test_the_reading_order_is_not_reachable_as_a_weight(self) -> None:
        """The ranking order lives in a private table, not on the enum. **A
        number on the enum is a number somebody will eventually average.**"""
        assert not any(hasattr(one, "weight") or hasattr(one, "score") for one in Strength)

    def test_the_bands_are_words_a_seller_would_use(self) -> None:
        assert {one.value for one in Strength} == {"strong", "reasonable", "thin"}


class TestNothingIsInvented:
    def test_an_empty_committee_produces_no_recommendation(self) -> None:
        """**A recommendation with no declared committee would be Signora
        inventing the Signora Customer's sales process.** The screen says so
        and offers the declaration; it ranks nothing."""
        result = reason(account_id=ACCOUNT, committee=(), evidence=(appointed(),), now=NOW)

        assert result.roles == ()
        assert result.unknowns == ()

    def test_no_evidence_means_every_role_is_an_unknown(self) -> None:
        """Silence with a reason, which is the rule the attention list and the
        decided section both already follow."""
        result = reason(account_id=ACCOUNT, committee=(CHAMPION, BUYER), evidence=(), now=NOW)

        assert all(one.strength is None for one in result.roles)
        assert len(result.unknowns) == 2

    def test_every_ranked_role_can_be_opened(self) -> None:
        """A conclusion that cannot be traced back to a recorded fact is an
        assertion, and this module publishes none."""
        result = reason(account_id=ACCOUNT, committee=(CHAMPION,), evidence=(appointed(),), now=NOW)

        for one in result.roles:
            if one.strength is not None:
                assert all(cited.event_id is not None for cited in one.support)


class FakeCommittees:
    def __init__(self, roles: tuple[CommitteeRoleRef, ...]) -> None:
        self._roles = roles

    async def committee(
        self, workspace_id: UUID, *, product_id: UUID
    ) -> tuple[CommitteeRoleRef, ...]:
        return self._roles


class FakeEvidence:
    def __init__(self, evidence: tuple[Evidence, ...]) -> None:
        self._evidence = evidence

    async def evidence(self, workspace_id: UUID, *, account_id: UUID) -> tuple[Evidence, ...]:
        return self._evidence


class TestAssembly:
    async def test_it_composes_and_decides_nothing(self) -> None:
        """The judgement is entirely in the pure domain; this reads two ports
        and hands their output to it."""
        assemble = AssembleApproach(
            committees=FakeCommittees((CHAMPION, BUYER)),
            evidence=FakeEvidence((appointed(),)),
            clock=lambda: NOW,
        )

        result = await assemble.execute(
            ApproachInput(workspace_id=WORKSPACE, account_id=ACCOUNT, product_id=PRODUCT)
        )

        assert result.account_id == ACCOUNT
        assert result.roles[0].role is CHAMPION
        assert [one.subject for one in result.unknowns] == ["CFO"]


class TestTitleMatchingIsTheJoinAndMustNotBeLoose:
    """**A false match puts a seller in front of the wrong person with
    Signora's confidence behind it**, which is worse than no recommendation.

    The first implementation compared substrings and ranked nothing at all: a
    Signora Customer declares *VP Engineering*, a provider reports *VP of
    Engineering*, and neither contains the other. Found by a test, not by
    review.
    """

    @pytest.mark.parametrize(
        ("declared", "observed"),
        [
            ("VP Engineering", "VP of Engineering"),
            ("Head of Security", "Head of Security"),
            ("Chief Financial Officer", "Chief Financial Officer"),
            ("VP, Engineering", "VP of Engineering"),
        ],
    )
    def test_the_same_job_written_differently_still_matches(
        self, declared: str, observed: str
    ) -> None:
        role = CommitteeRoleRef(title=declared, part="champion")

        (ranked,) = rank_roles((role,), (appointed(title=observed),), now=NOW)

        assert ranked.strength is not None, f"{declared!r} did not match {observed!r}"

    @pytest.mark.parametrize(
        ("declared", "observed"),
        [
            ("VP Engineering", "VP of Sales"),
            ("CFO", "CTO"),
            ("Head of Security", "Head of Marketing"),
        ],
    )
    def test_a_different_job_does_not_match(self, declared: str, observed: str) -> None:
        role = CommitteeRoleRef(title=declared, part="economic_buyer")

        (ranked,) = rank_roles((role,), (appointed(title=observed),), now=NOW)

        assert ranked.strength is None, f"{declared!r} wrongly matched {observed!r}"


def departed(*, title: str = "VP of Engineering", days_ago: int = 5) -> Evidence:
    return Evidence(
        event_id=uuid4(),
        type_key="leadership_departed",
        summary=f"Their {title} departed",
        occurred_at=NOW - timedelta(days=days_ago),
        corroborating_providers=2,
        names_title=title,
    )


class TestWhatToDoWithTheNextFifteenMinutes:
    """**The question the Signora Customer is actually paying for**, and it is
    larger than *who do I contact*. A module that can only say *approach* is
    one whose recommendation carries no information."""

    def test_strong_recent_corroborated_evidence_says_approach(self) -> None:
        result = reason(account_id=ACCOUNT, committee=(CHAMPION,), evidence=(appointed(),), now=NOW)

        assert result.recommendation.action is NextAction.APPROACH
        assert result.recommendation.role is CHAMPION

    def test_the_reason_is_the_why_now(self) -> None:
        """A recommendation a seller cannot repeat to their manager is not one
        this module will make."""
        result = reason(account_id=ACCOUNT, committee=(CHAMPION,), evidence=(appointed(),), now=NOW)

        assert "Appointed a new" in result.recommendation.reason
        assert "20 days ago" in result.recommendation.reason

    def test_one_source_says_verify_rather_than_approach(self) -> None:
        """**One missing fact stands between here and an approach**, and it is
        named so it can be closed in a single call."""
        result = reason(
            account_id=ACCOUNT,
            committee=(CHAMPION,),
            evidence=(appointed(providers=1),),
            now=NOW,
        )

        assert result.recommendation.action is NextAction.VERIFY
        assert "only one source" in result.recommendation.reason

    def test_nothing_observed_says_wait(self) -> None:
        result = reason(account_id=ACCOUNT, committee=(CHAMPION, BUYER), evidence=(), now=NOW)

        assert result.recommendation.action is NextAction.WAIT
        assert result.recommendation.role is None

    def test_everything_old_says_wait(self) -> None:
        """A six-month-old reason to call is a reason not to."""
        result = reason(
            account_id=ACCOUNT,
            committee=(CHAMPION,),
            evidence=(appointed(days_ago=STALE_AFTER_DAYS + 30),),
            now=NOW,
        )

        assert result.recommendation.action is NextAction.WAIT
        assert str(STALE_AFTER_DAYS) in result.recommendation.reason

    def test_waiting_never_names_somebody(self) -> None:
        """**Naming somebody while advising against contact is an invitation
        dressed as caution**, and a seller will read the name and ignore the
        advice. The type refuses it."""
        with pytest.raises(ReasoningError, match="invitation dressed as caution"):
            Recommendation(action=NextAction.WAIT, reason="not yet", role=CHAMPION)

    def test_acting_always_names_somebody(self) -> None:
        with pytest.raises(ReasoningError, match="names nobody"):
            Recommendation(action=NextAction.APPROACH, reason="go")


class TestTheChampionWhoDisappeared:
    """**The same evidence that would rank a role highest is the evidence that
    means nobody is there.** Approaching a departed executive is the single
    most embarrassing thing this module could cause."""

    def test_a_departure_makes_the_seat_a_question_rather_than_a_target(self) -> None:
        result = reason(
            account_id=ACCOUNT, committee=(CHAMPION,), evidence=(departed(),), now=NOW
        )

        assert result.recommendation.action is NextAction.VERIFY
        assert "departure" in result.recommendation.reason

    def test_the_most_recent_event_decides_not_the_set(self) -> None:
        """A VP who joined in March and left in July is a vacancy. One who
        left in March and was replaced in July is not. **Reading the set rather
        than the sequence would get both wrong.**"""
        left_then_replaced = (departed(days_ago=90), appointed(days_ago=10))

        result = reason(
            account_id=ACCOUNT, committee=(CHAMPION,), evidence=left_then_replaced, now=NOW
        )

        assert result.recommendation.action is NextAction.APPROACH

    def test_an_empty_seat_becomes_an_unknown(self) -> None:
        result = reason(
            account_id=ACCOUNT, committee=(CHAMPION,), evidence=(departed(),), now=NOW
        )

        assert any("since the last one left" in one.question for one in result.unknowns)

    def test_both_directions_at_once_is_a_contradiction(self) -> None:
        """**Reported, never resolved.** Two providers describing different
        worlds, and picking one would be this module settling a question the
        evidence did not."""
        both = (appointed(days_ago=30), departed(days_ago=20))

        result = reason(account_id=ACCOUNT, committee=(CHAMPION,), evidence=both, now=NOW)

        assert RiskKind.CONTRADICTION in {one.kind for one in result.risks}

    def test_the_contradiction_kind_is_reachable(self) -> None:
        """**Every `RiskKind` must be producible.** A kind nothing can emit is
        Decorative Logic — it reads as protection and enforces nothing, and
        `CONTRADICTION` was exactly that until this rule existed."""
        produced = set()
        for evidence in [
            (appointed(providers=1),),
            (appointed(days_ago=STALE_AFTER_DAYS + 1),),
            (appointed(days_ago=30), departed(days_ago=20)),
        ]:
            ranked = rank_roles((CHAMPION,), evidence, now=NOW)
            produced |= {one.kind for one in risks(ranked, now=NOW)}
            produced |= {one.kind for one in contradictions(ranked)}

        surge = Evidence(
            event_id=uuid4(),
            type_key="workforce_surge",
            summary="Engineering headcount grew 42%",
            occurred_at=NOW - timedelta(days=10),
            corroborating_providers=2,
        )
        produced |= {
            one.kind for one in risks(rank_roles((CHAMPION,), (surge,), now=NOW), now=NOW)
        }

        assert produced == set(RiskKind)

"""Tests for the detection rules — where observations become business news.

Every rule is pure: observations and parameters in, detections out. No
database, no clock, no event bus. If one needed any of those, the Clean
Architecture boundary would have leaked.

Two properties are asserted throughout: **every threshold comes from the
taxonomy**, and **every summary is a sentence a CRO would understand**.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest

from modules.business_event_engine.domain.rules.base import Detection
from modules.business_event_engine.domain.rules.point import (
    AcquisitionAnnounced,
    FundingRoundClosed,
    LeadershipAppointed,
    LeadershipDeparted,
    RevenueContraction,
    RevenueGrowth,
    TechnologyAdopted,
    TechnologyRetired,
)
from modules.business_event_engine.domain.rules.window import (
    BuyingIntentSurge,
    HeadcountDecline,
    HiringSurge,
)
from modules.business_event_engine.domain.taxonomy import BusinessEventType, Parameters
from modules.business_event_engine.infrastructure.taxonomy_loader import load_taxonomy
from modules.observation_engine.public import (
    Observation,
    ObservationDirection,
    ObservationKind,
)
from modules.provider_normalization.public import ClaimAttribute

WORKSPACE = uuid4()
ENTITY = uuid4()
START = datetime(2026, 1, 1, tzinfo=UTC)


def _params(type_key: BusinessEventType) -> Parameters:
    """Always the real taxonomy. A test with hand-written parameters proves
    the rule works against numbers nobody shipped."""
    return load_taxonomy().parameters(type_key)


def _occurrence(
    attribute: ClaimAttribute, value: Any, day: int, *, provider: str = "apollo"
) -> Observation:
    return Observation(
        id=uuid4(),
        workspace_id=WORKSPACE,
        entity_id=ENTITY,
        provider=provider,
        attribute=attribute,
        kind=ObservationKind.OCCURRENCE_OBSERVED,
        previous_value=None,
        current_value=value,
        direction=ObservationDirection.OCCURRED,
        magnitude=None,
        observed_at=START + timedelta(days=day),
        previous_observed_at=None,
        recorded_at=START,
        evidence_claim_ids=(uuid4(),),
    )


def _change(
    attribute: ClaimAttribute,
    previous: Any,
    current: Any,
    from_day: int,
    to_day: int,
    *,
    direction: ObservationDirection = ObservationDirection.INCREASED,
    provider: str = "coresignal",
) -> Observation:
    return Observation(
        id=uuid4(),
        workspace_id=WORKSPACE,
        entity_id=ENTITY,
        provider=provider,
        attribute=attribute,
        kind=ObservationKind.VALUE_CHANGED,
        previous_value=previous,
        current_value=current,
        direction=direction,
        magnitude=abs(float(current) - float(previous))
        if isinstance(current, (int, float))
        else None,
        observed_at=START + timedelta(days=to_day),
        previous_observed_at=START + timedelta(days=from_day),
        recorded_at=START,
        evidence_claim_ids=(uuid4(),),
    )


class TestCapitalEvents:
    def test_a_material_round_is_news(self) -> None:
        observation = _occurrence(
            ClaimAttribute.FUNDING_ROUND,
            {"round_type": "series_b", "amount": 24_000_000, "currency": "USD", "investors": ["X"]},
            20,
        )

        (detection,) = FundingRoundClosed().evaluate(
            (observation,), _params(BusinessEventType.FUNDING_ROUND_CLOSED)
        )

        assert detection.summary == "Raised 24M USD in a series b round"
        assert detection.facts["amount"] == 24_000_000

    def test_a_round_below_the_declared_floor_is_not(self) -> None:
        """The floor is a business judgement, so it lives in the taxonomy —
        this test reads the shipped value rather than inventing one."""
        tiny = _occurrence(
            ClaimAttribute.FUNDING_ROUND,
            {"round_type": "pre_seed", "amount": 50_000, "currency": "USD"},
            20,
        )

        assert (
            FundingRoundClosed().evaluate((tiny,), _params(BusinessEventType.FUNDING_ROUND_CLOSED))
            == ()
        )

    def test_an_undisclosed_amount_is_not_treated_as_zero(self) -> None:
        """Missing is not small. Treating it as zero would silently drop
        every round a vendor did not price."""
        undisclosed = _occurrence(
            ClaimAttribute.FUNDING_ROUND, {"round_type": "series_a", "amount": None}, 20
        )

        assert (
            FundingRoundClosed().evaluate(
                (undisclosed,), _params(BusinessEventType.FUNDING_ROUND_CLOSED)
            )
            == ()
        )

    def test_an_acquisition_names_the_counterparty(self) -> None:
        observation = _occurrence(
            ClaimAttribute.ACQUISITION,
            {"counterparty": "Initech", "announced_on": "2026-02-01"},
            30,
        )

        (detection,) = AcquisitionAnnounced().evaluate(
            (observation,), _params(BusinessEventType.ACQUISITION_ANNOUNCED)
        )

        assert detection.summary == "Announced the acquisition of Initech"


class TestTechnologyEvents:
    def test_adoption_and_retirement_are_separate_news(self) -> None:
        adopted = _occurrence(
            ClaimAttribute.TECHNOLOGY_DETECTED, {"name": "CloudERP", "category": "erp"}, 10
        )
        retired = _occurrence(
            ClaimAttribute.TECHNOLOGY_REMOVED, {"name": "LegacyERP", "category": "erp"}, 10
        )

        (adoption,) = TechnologyAdopted().evaluate(
            (adopted, retired), _params(BusinessEventType.TECHNOLOGY_ADOPTED)
        )
        (retirement,) = TechnologyRetired().evaluate(
            (adopted, retired), _params(BusinessEventType.TECHNOLOGY_RETIRED)
        )

        assert adoption.summary == "Started using CloudERP"
        assert retirement.summary == "Stopped using LegacyERP"


class TestLeadershipEvents:
    def _role(self, direction: str, seniority: str, title: str = "CRO") -> Observation:
        return _occurrence(
            ClaimAttribute.ROLE_CHANGE,
            {"title": title, "seniority": seniority, "direction": direction},
            15,
        )

    def test_an_executive_joining_is_an_appointment(self) -> None:
        (detection,) = LeadershipAppointed().evaluate(
            (self._role("joined", "executive"),),
            _params(BusinessEventType.LEADERSHIP_APPOINTED),
        )

        assert detection.summary == "Appointed a new CRO"

    def test_an_executive_leaving_is_a_departure(self) -> None:
        (detection,) = LeadershipDeparted().evaluate(
            (self._role("left", "executive", "CTO"),),
            _params(BusinessEventType.LEADERSHIP_DEPARTED),
        )

        assert detection.summary == "Their CTO departed"

    def test_the_two_directions_never_produce_each_other(self) -> None:
        """Split into two types precisely because they mean opposite things.
        A consumer that had to read a field to know whether the news was good
        would have been handed the wrong vocabulary."""
        joined = (self._role("joined", "executive"),)

        assert (
            LeadershipDeparted().evaluate(joined, _params(BusinessEventType.LEADERSHIP_DEPARTED))
            == ()
        )

    def test_a_manager_moving_is_not_leadership_news(self) -> None:
        """Which seniorities count is declared in the taxonomy, not decided
        in the rule."""
        assert (
            LeadershipAppointed().evaluate(
                (self._role("joined", "manager"),),
                _params(BusinessEventType.LEADERSHIP_APPOINTED),
            )
            == ()
        )


class TestRevenueEvents:
    def test_moving_up_a_range_is_growth_in_customer_language(self) -> None:
        observation = _change(ClaimAttribute.REVENUE_BAND, "10m_50m", "50m_250m", 0, 60)

        (detection,) = RevenueGrowth().evaluate(
            (observation,), _params(BusinessEventType.REVENUE_GROWTH)
        )

        assert detection.summary == "Revenue grew from $10M–$50M to $50M–$250M"
        assert "10m_50m" not in detection.summary, "storage identifiers must not reach a customer"

    def test_moving_down_a_range_is_contraction(self) -> None:
        observation = _change(
            ClaimAttribute.REVENUE_BAND,
            "50m_250m",
            "10m_50m",
            0,
            60,
            direction=ObservationDirection.DECREASED,
        )

        (detection,) = RevenueContraction().evaluate(
            (observation,), _params(BusinessEventType.REVENUE_CONTRACTION)
        )

        assert detection.summary == "Revenue fell from $50M–$250M to $10M–$50M"

    def test_growth_and_contraction_never_produce_each_other(self) -> None:
        up = (_change(ClaimAttribute.REVENUE_BAND, "10m_50m", "50m_250m", 0, 60),)

        assert (
            RevenueContraction().evaluate(up, _params(BusinessEventType.REVENUE_CONTRACTION)) == ()
        )


class TestHiringSurge:
    def test_sustained_growth_across_several_steps_is_one_surge(self) -> None:
        """The case a single observation cannot answer: no individual step
        need pass the threshold for the trajectory to."""
        series = (
            _change(ClaimAttribute.EMPLOYEE_COUNT, 100, 110, 0, 30),
            _change(ClaimAttribute.EMPLOYEE_COUNT, 110, 125, 30, 60),
            _change(ClaimAttribute.EMPLOYEE_COUNT, 125, 140, 60, 90),
        )

        (detection,) = HiringSurge().evaluate(series, _params(BusinessEventType.HIRING_SURGE))

        assert detection.facts["starting_value"] == 100
        assert detection.facts["ending_value"] == 140
        assert "40%" in detection.summary
        assert len(detection.evidence) == 3

    def test_growth_below_the_declared_ratio_is_not_a_surge(self) -> None:
        modest = (_change(ClaimAttribute.EMPLOYEE_COUNT, 1000, 1050, 0, 30),)

        assert HiringSurge().evaluate(modest, _params(BusinessEventType.HIRING_SURGE)) == ()

    def test_a_large_ratio_on_a_tiny_base_is_not_a_surge(self) -> None:
        """Both floors matter: 50% of four people is two people. The absolute
        floor is what stops a startup's every hire becoming news."""
        tiny = (_change(ClaimAttribute.EMPLOYEE_COUNT, 4, 6, 0, 30),)

        assert HiringSurge().evaluate(tiny, _params(BusinessEventType.HIRING_SURGE)) == ()

    def test_a_zero_baseline_concludes_nothing(self) -> None:
        """A ratio against zero is a division, not a growth rate."""
        from_nothing = (_change(ClaimAttribute.EMPLOYEE_COUNT, 0, 40, 0, 30),)

        assert HiringSurge().evaluate(from_nothing, _params(BusinessEventType.HIRING_SURGE)) == ()

    def test_evidence_older_than_the_window_is_excluded(self) -> None:
        """The window is anchored on the latest observation, not on wall
        clock, so a replay of historical evidence reaches the conclusion it
        would have reached at the time."""
        series = (
            _change(ClaimAttribute.EMPLOYEE_COUNT, 100, 105, 0, 5),
            _change(ClaimAttribute.EMPLOYEE_COUNT, 105, 140, 400, 430),
        )

        (detection,) = HiringSurge().evaluate(series, _params(BusinessEventType.HIRING_SURGE))

        assert len(detection.evidence) == 1
        assert detection.facts["starting_value"] == 105

    def test_a_decline_is_never_a_surge(self) -> None:
        shrinking = (
            _change(
                ClaimAttribute.EMPLOYEE_COUNT,
                200,
                150,
                0,
                30,
                direction=ObservationDirection.DECREASED,
            ),
        )

        assert HiringSurge().evaluate(shrinking, _params(BusinessEventType.HIRING_SURGE)) == ()


class TestHeadcountDecline:
    def test_a_material_reduction_is_news(self) -> None:
        shrinking = (
            _change(
                ClaimAttribute.EMPLOYEE_COUNT,
                200,
                150,
                0,
                30,
                direction=ObservationDirection.DECREASED,
            ),
        )

        (detection,) = HeadcountDecline().evaluate(
            shrinking, _params(BusinessEventType.HEADCOUNT_DECLINE)
        )

        assert "25%" in detection.summary
        assert detection.facts["change"] == 50

    def test_growth_is_never_a_decline(self) -> None:
        growing = (_change(ClaimAttribute.EMPLOYEE_COUNT, 100, 140, 0, 30),)

        assert (
            HeadcountDecline().evaluate(growing, _params(BusinessEventType.HEADCOUNT_DECLINE)) == ()
        )


class TestBuyingIntentSurge:
    def _week(self, topic: str, score: int, day: int) -> Observation:
        return _occurrence(
            ClaimAttribute.INTENT_TOPIC_SURGE,
            {"topic": topic, "score": score, "observed_week": f"2026-01-{day:02d}"},
            day,
            provider="bombora",
        )

    def test_sustained_elevated_weeks_are_a_surge(self) -> None:
        weeks = (
            self._week("Cloud ERP", 72, 1),
            self._week("Cloud ERP", 81, 8),
            self._week("Cloud ERP", 88, 15),
        )

        (detection,) = BuyingIntentSurge().evaluate(
            weeks, _params(BusinessEventType.BUYING_INTENT_SURGE)
        )

        assert detection.facts["topic"] == "Cloud ERP"
        assert detection.facts["weeks_elevated"] == 3
        assert detection.facts["peak_score"] == 88
        assert "Researching Cloud ERP" in detection.summary

    def test_one_loud_week_is_not_a_surge(self) -> None:
        assert (
            BuyingIntentSurge().evaluate(
                (self._week("Cloud ERP", 95, 1),),
                _params(BusinessEventType.BUYING_INTENT_SURGE),
            )
            == ()
        )

    def test_quiet_weeks_do_not_accumulate_into_one(self) -> None:
        quiet = tuple(self._week("Cloud ERP", 20, day) for day in (1, 8, 15, 22))

        assert (
            BuyingIntentSurge().evaluate(quiet, _params(BusinessEventType.BUYING_INTENT_SURGE))
            == ()
        )

    def test_two_topics_are_two_pieces_of_news(self) -> None:
        """A rollup across topics would produce a number that means nothing
        to anybody."""
        weeks = tuple(
            self._week(topic, 80, day)
            for topic in ("Cloud ERP", "Data Warehousing")
            for day in (1, 8, 15)
        )

        detections = BuyingIntentSurge().evaluate(
            weeks, _params(BusinessEventType.BUYING_INTENT_SURGE)
        )

        assert {d.facts["topic"] for d in detections} == {"Cloud ERP", "Data Warehousing"}


class TestSummariesAreWrittenForCustomers:
    """*If a CRO opened Signora today, would they immediately understand
    what this event means?*"""

    @pytest.mark.parametrize(
        "detection",
        [
            FundingRoundClosed().evaluate(
                (
                    _occurrence(
                        ClaimAttribute.FUNDING_ROUND,
                        {"round_type": "series_b", "amount": 24_000_000, "currency": "USD"},
                        1,
                    ),
                ),
                load_taxonomy().parameters(BusinessEventType.FUNDING_ROUND_CLOSED),
            )[0],
            HiringSurge().evaluate(
                (_change(ClaimAttribute.EMPLOYEE_COUNT, 100, 140, 0, 30),),
                load_taxonomy().parameters(BusinessEventType.HIRING_SURGE),
            )[0],
        ],
        ids=["funding", "hiring"],
    )
    def test_no_provider_or_implementation_vocabulary_reaches_the_summary(
        self, detection: Detection
    ) -> None:
        forbidden = (
            "apollo",
            "coresignal",
            "bombora",
            "builtwith",
            "crunchbase",
            "observation",
            "claim",
            "attribute",
            "entity",
            "workspace",
            "provider",
        )
        lowered = detection.summary.lower()

        assert not any(word in lowered for word in forbidden), (
            f"'{detection.summary}' leaks vocabulary a customer should never need to know"
        )

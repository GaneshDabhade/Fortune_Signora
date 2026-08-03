"""What a customer's browser receives about a company's changes — A5.

**A separate file because the transition path is unreachable from the seeded
pipeline.** A transition needs one provider asserting a *state* attribute
twice, and the Playground scenario enriches each account once, so every
observation it produces is a first sighting ([B-319](../../../docs/BUGS.md)).
The endpoint's integration tests therefore exercise occurrences only, and the
half of the response a chart actually needs would go unasserted.

Here the two readings are constructed directly, which is the level where that
is honest: no database, no pipeline, and the mapping under test is pure.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from modules.observation_engine.domain.observation import (
    Observation,
    ObservationDirection,
    ObservationKind,
)
from modules.observation_engine.interface.schemas import AccountObservationResponse
from modules.provider_normalization.public import ClaimAttribute

NOW = datetime(2026, 7, 1, tzinfo=UTC)


def _transition() -> Observation:
    return Observation(
        id=uuid4(),
        workspace_id=uuid4(),
        entity_id=uuid4(),
        provider="coresignal",
        attribute=ClaimAttribute.EMPLOYEE_COUNT,
        kind=ObservationKind.VALUE_CHANGED,
        previous_value=120,
        current_value=145,
        direction=ObservationDirection.INCREASED,
        magnitude=25.0,
        observed_at=NOW,
        previous_observed_at=NOW - timedelta(days=32),
        recorded_at=NOW + timedelta(days=1),
        evidence_claim_ids=(uuid4(),),
    )


class TestATransitionCarriesEnoughToDrawIt:
    def test_both_ends_and_the_window_reach_the_wire(self) -> None:
        """**The brief says *"Grew headcount 15% over 32 days"* and nothing
        behind it.** This is what has to be behind it: what it was, what it
        became, how far, and between which two dates."""
        response = AccountObservationResponse.from_domain(_transition())

        assert response.previous_value == 120
        assert response.current_value == 145
        assert response.magnitude == 25.0
        assert response.direction == "increased"
        assert response.previous_observed_at == NOW - timedelta(days=32)
        assert response.observed_at == NOW

    def test_the_provider_travels_with_the_change(self) -> None:
        """**A correctness constraint on every chart drawn from this.** A
        reading is only ever a change according to one source: Apollo saying
        120 on Monday and CoreSignal saying 145 on Tuesday is disagreement,
        not growth of 25. Without `provider` on each row a client cannot
        group before plotting, and the phantom is unavoidable rather than
        merely likely."""
        assert AccountObservationResponse.from_domain(_transition()).provider == "coresignal"

    def test_reporting_lag_survives_as_two_distinct_times(self) -> None:
        """`observed_at` is when the provider says it was true; `recorded_at`
        is when Signora learned it. Collapsing them makes a backfill look like
        a burst of activity on its ingestion day."""
        response = AccountObservationResponse.from_domain(_transition())

        assert response.recorded_at > response.observed_at

    def test_a_first_sighting_says_absent_rather_than_zero(self) -> None:
        """An occurrence has genuinely nothing it moved from. Zero would be a
        reading, and a chart would draw a rise from nothing that never
        happened."""
        occurrence = Observation(
            id=uuid4(),
            workspace_id=uuid4(),
            entity_id=uuid4(),
            provider="builtwith",
            attribute=ClaimAttribute.TECHNOLOGY_DETECTED,
            kind=ObservationKind.OCCURRENCE_OBSERVED,
            previous_value=None,
            current_value={"name": "CloudERP", "category": "erp"},
            direction=ObservationDirection.OCCURRED,
            magnitude=None,
            observed_at=NOW,
            previous_observed_at=None,
            recorded_at=NOW,
            evidence_claim_ids=(uuid4(),),
        )

        response = AccountObservationResponse.from_domain(occurrence)

        assert response.previous_value is None
        assert response.previous_observed_at is None
        assert response.magnitude is None

    def test_no_judgement_about_significance_can_be_expressed(self) -> None:
        """Whether a move *matters* is the Business Event Engine's question,
        and this module's public contract has refused to answer it since M4.
        A field here would be filled in by whoever rendered it."""
        fields = set(AccountObservationResponse.model_fields)

        for judgement in ("significance", "score", "importance", "severity", "summary"):
            assert judgement not in fields

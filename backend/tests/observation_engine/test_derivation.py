"""Tests for change detection — the module's whole job.

Two properties carry the design, and both are about **restraint**:

* **Re-assertion is not change.** A nightly sync repeating the same
  headcount for six weeks produces nothing. This is the dominant case in a
  polling pipeline, and an engine that fires on it is worse than no engine.
* **Disagreement is not change.** Two providers reporting different values
  is evidence about the providers, not movement in the world. Change is only
  ever computed *within* one provider's series.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from modules.observation_engine.domain.derivation import derive, refinements
from modules.observation_engine.domain.observation import (
    ObservationDirection,
    ObservationKind,
    observation_id,
)
from modules.observation_engine.domain.semantics import (
    ATTRIBUTE_KINDS,
    ORDERED_ATTRIBUTES,
    AttributeKind,
    UnclassifiedAttributeError,
    attribute_kind,
    occurrence_key,
)
from modules.provider_normalization.public import ClaimAttribute, ClaimView, RevenueBand

WORKSPACE = uuid4()
ENTITY = uuid4()
NOW = datetime(2026, 4, 1, tzinfo=UTC)


def _claim(
    value: Any,
    day: int,
    *,
    attribute: ClaimAttribute = ClaimAttribute.EMPLOYEE_COUNT,
    provider: str = "coresignal",
    claim_id: UUID | None = None,
) -> ClaimView:
    return ClaimView(
        id=claim_id or uuid4(),
        provider=provider,
        attribute=attribute,
        value=value,
        observed_at=datetime(2026, 1, day, tzinfo=UTC),
        subject_external_id="acme-corp",
        subject_domain="acme.example",
        subject_legal_name="Acme Corp",
        payload_provenance="DEVELOPMENT_FIXTURE",
    )


def _derive(
    *claims: ClaimView, attribute: ClaimAttribute = ClaimAttribute.EMPLOYEE_COUNT
) -> tuple[Any, ...]:
    return derive(
        claims,
        workspace_id=WORKSPACE,
        entity_id=ENTITY,
        provider="coresignal",
        attribute=attribute,
        recorded_at=NOW,
    )


class TestRestraint:
    """What the engine refuses to call a change."""

    def test_the_first_value_establishes_a_baseline_and_observes_nothing(self) -> None:
        """Nothing changed — Signora merely learned. Emitting one here would
        mean an onboarding sync of five thousand companies producing tens of
        thousands of observations that all say the same empty thing."""
        assert _derive(_claim(120, 1)) == ()

    def test_re_assertion_is_never_an_observation(self) -> None:
        """The dominant case in a polling pipeline."""
        assert _derive(_claim(120, 1), _claim(120, 8), _claim(120, 15)) == ()

    def test_a_value_that_returns_to_a_previous_one_is_two_changes(self) -> None:
        """120 → 145 → 120 is two movements, not zero. Comparing against the
        first value rather than the previous one would erase the excursion."""
        observations = _derive(_claim(120, 1), _claim(145, 8), _claim(120, 15))

        assert len(observations) == 2
        assert [o.direction for o in observations] == [
            ObservationDirection.INCREASED,
            ObservationDirection.DECREASED,
        ]

    def test_an_empty_series_observes_nothing(self) -> None:
        assert _derive() == ()


class TestTransitions:
    def test_a_change_carries_everything_needed_to_reason_about_it(self) -> None:
        """Downstream must never have to reconstruct a transition from the
        claim history — that would mean every consumer reimplementing this
        module, and diverging from it."""
        (observation,) = _derive(_claim(120, 1), _claim(145, 15))

        assert observation.kind is ObservationKind.VALUE_CHANGED
        assert observation.previous_value == 120
        assert observation.current_value == 145
        assert observation.direction is ObservationDirection.INCREASED
        assert observation.magnitude == 25
        assert observation.provider == "coresignal"
        assert observation.entity_id == ENTITY
        assert observation.observed_at == datetime(2026, 1, 15, tzinfo=UTC)
        assert observation.previous_observed_at == datetime(2026, 1, 1, tzinfo=UTC)

    def test_the_window_is_never_narrower_than_the_evidence(self) -> None:
        """Six weeks between assertions means the change happened *somewhere*
        in six weeks. Claiming the later date as the moment would invent a
        precision no provider supplied."""
        (observation,) = _derive(_claim(120, 1), _claim(145, 15))

        assert observation.previous_observed_at < observation.observed_at

    def test_a_change_cites_both_claims(self) -> None:
        before, after = _claim(120, 1), _claim(145, 15)

        (observation,) = _derive(before, after)

        assert set(observation.evidence_claim_ids) == {before.id, after.id}

    def test_an_unordered_attribute_changes_without_a_direction_or_magnitude(self) -> None:
        """Subtracting two industries is meaningless, and inventing a
        distance between them would be a manufactured number."""
        (observation,) = _derive(
            _claim("software", 1, attribute=ClaimAttribute.INDUSTRY),
            _claim("fintech", 15, attribute=ClaimAttribute.INDUSTRY),
            attribute=ClaimAttribute.INDUSTRY,
        )

        assert observation.direction is ObservationDirection.CHANGED
        assert observation.magnitude is None

    def test_revenue_bands_have_a_direction_because_the_vocabulary_orders_them(self) -> None:
        """A fact about the vocabulary, not a heuristic: bands run from
        `under_1m` to `over_1b` by definition."""
        (observation,) = _derive(
            _claim(RevenueBand.FROM_1M_TO_10M.value, 1, attribute=ClaimAttribute.REVENUE_BAND),
            _claim(RevenueBand.FROM_50M_TO_250M.value, 15, attribute=ClaimAttribute.REVENUE_BAND),
            attribute=ClaimAttribute.REVENUE_BAND,
        )

        assert observation.direction is ObservationDirection.INCREASED
        assert observation.magnitude is None, "band distance is not a quantity"


class TestOccurrences:
    def _funding(self, day: int, announced: str = "2026-01-22") -> ClaimView:
        return _claim(
            {"round_type": "series_b", "amount": 24_000_000, "announced_on": announced},
            day,
            attribute=ClaimAttribute.FUNDING_ROUND,
        )

    def test_an_occurrence_is_observed_once_however_often_it_is_reported(self) -> None:
        """A provider re-reporting the same Series B on twenty nightly syncs
        asserts one thing twenty times."""
        observations = _derive(
            self._funding(23),
            self._funding(24),
            self._funding(25),
            attribute=ClaimAttribute.FUNDING_ROUND,
        )

        assert len(observations) == 1
        assert observations[0].kind is ObservationKind.OCCURRENCE_OBSERVED

    def test_the_earliest_sighting_is_the_one_kept(self) -> None:
        """A later `observed_at` for the same round would misdate it."""
        observations = _derive(
            self._funding(25), self._funding(23), attribute=ClaimAttribute.FUNDING_ROUND
        )

        assert observations[0].observed_at == datetime(2026, 1, 23, tzinfo=UTC)

    def test_a_different_occurrence_is_a_different_observation(self) -> None:
        observations = _derive(
            self._funding(23, "2026-01-22"),
            self._funding(30, "2026-03-14"),
            attribute=ClaimAttribute.FUNDING_ROUND,
        )

        assert len(observations) == 2

    def test_an_occurrence_has_nothing_to_have_moved_from(self) -> None:
        (observation,) = _derive(self._funding(23), attribute=ClaimAttribute.FUNDING_ROUND)

        assert observation.previous_value is None
        assert observation.previous_observed_at is None
        assert observation.direction is ObservationDirection.OCCURRED

    def test_each_intent_week_is_its_own_observation(self) -> None:
        """The trajectory is product value. A consumer given only the latest
        week cannot tell a company at 71 on the way up from one on the way
        down."""
        weeks = [
            _claim(
                {"topic": "Cloud ERP", "score": score, "observed_week": week, "trend": "emerging"},
                20,
                attribute=ClaimAttribute.INTENT_TOPIC_SURGE,
            )
            for score, week in ((41, "2026-01-05"), (62, "2026-01-12"), (88, "2026-01-19"))
        ]

        observations = _derive(*weeks, attribute=ClaimAttribute.INTENT_TOPIC_SURGE)

        assert len(observations) == 3

    def test_a_week_re_reported_late_deduplicates(self) -> None:
        """Intent is reported late by design; keying on arrival would make
        one week's measurement look like several."""
        week = {
            "topic": "Cloud ERP",
            "score": 88,
            "observed_week": "2026-01-19",
            "trend": "emerging",
        }
        observations = _derive(
            _claim(week, 20, attribute=ClaimAttribute.INTENT_TOPIC_SURGE),
            _claim(week, 27, attribute=ClaimAttribute.INTENT_TOPIC_SURGE),
            attribute=ClaimAttribute.INTENT_TOPIC_SURGE,
        )

        assert len(observations) == 1


class TestDeterminism:
    def test_processing_order_does_not_change_the_result(self) -> None:
        a, b, c = _claim(120, 1), _claim(145, 8), _claim(160, 15)

        forward = _derive(a, b, c)
        shuffled = _derive(c, a, b)

        assert [o.id for o in forward] == [o.id for o in shuffled]

    def test_identity_survives_claim_regeneration(self) -> None:
        """Claim ids are allocated when a mapper runs. Keying an observation
        on them would duplicate the entire table after a mapper fix."""
        first = _derive(_claim(120, 1, claim_id=uuid4()), _claim(145, 15, claim_id=uuid4()))
        regenerated = _derive(_claim(120, 1, claim_id=uuid4()), _claim(145, 15, claim_id=uuid4()))

        assert [o.id for o in first] == [o.id for o in regenerated]

    def test_a_different_workspace_produces_a_different_identity(self) -> None:
        """Otherwise one tenant's observation would collide with another's."""
        assert observation_id(
            workspace_id=uuid4(),
            entity_id=ENTITY,
            provider="apollo",
            attribute=ClaimAttribute.EMPLOYEE_COUNT,
            kind=ObservationKind.VALUE_CHANGED,
            key="k",
        ) != observation_id(
            workspace_id=uuid4(),
            entity_id=ENTITY,
            provider="apollo",
            attribute=ClaimAttribute.EMPLOYEE_COUNT,
            kind=ObservationKind.VALUE_CHANGED,
            key="k",
        )

    def test_claims_sharing_a_timestamp_still_order_totally(self) -> None:
        """Without a tiebreak the result would depend on the order the
        database happened to return rows."""
        same_day = [_claim(120, 1), _claim(145, 1), _claim(160, 1)]

        assert [o.id for o in _derive(*same_day)] == [o.id for o in _derive(*reversed(same_day))]


class TestRefinement:
    def test_a_late_claim_refines_the_observation_that_contained_it(self) -> None:
        """The coarse observation is not false — headcount really did go
        120 → 145 across that window. It is less precise, and leaving it
        alongside the finer pair would double-count the growth."""
        (coarse,) = _derive(_claim(120, 1), _claim(145, 15))
        fine = _derive(_claim(120, 1), _claim(130, 8), _claim(145, 15))

        mapping = refinements(fine, (coarse,))

        assert set(mapping) == {o.id for o in fine}
        assert set(mapping.values()) == {coarse.id}

    def test_an_unrelated_observation_refines_nothing(self) -> None:
        (early,) = _derive(_claim(120, 1), _claim(145, 8))
        later = _derive(_claim(200, 20), _claim(240, 28))

        assert refinements(later, (early,)) == {}


class TestAttributeSemantics:
    def test_every_canonical_attribute_is_classified(self) -> None:
        """A silent default is how a new attribute acquires a behaviour
        nobody chose. Adding one to the vocabulary requires an RFC;
        classifying it is part of that RFC."""
        for attribute in ClaimAttribute:
            assert attribute in ATTRIBUTE_KINDS

    def test_an_unclassified_attribute_fails_loudly(self) -> None:
        class Invented(str):
            value = "invented"

        with pytest.raises(UnclassifiedAttributeError, match="no declared observation semantics"):
            attribute_kind(Invented())  # type: ignore[arg-type]

    def test_headcount_change_is_an_occurrence_not_a_state(self) -> None:
        """CoreSignal reports a delta directly. Deriving a transition from it
        would double-count against EMPLOYEE_COUNT."""
        assert attribute_kind(ClaimAttribute.HEADCOUNT_CHANGE) is AttributeKind.OCCURRENCE

    def test_revenue_band_order_is_ascending_as_the_direction_logic_assumes(self) -> None:
        """Reordering the enum would silently invert every revenue direction
        in the platform. This is the guard against that."""
        assert ORDERED_ATTRIBUTES[ClaimAttribute.REVENUE_BAND] == (
            "under_1m",
            "1m_10m",
            "10m_50m",
            "50m_250m",
            "250m_1b",
            "over_1b",
        )

    def test_a_technology_is_keyed_on_its_name_alone(self) -> None:
        """A vendor re-reporting the same technology with a later
        `last_detected` is the same detection, not a new one."""
        early = occurrence_key(
            ClaimAttribute.TECHNOLOGY_DETECTED,
            {"name": "CloudERP", "category": "erp", "last_seen": "2026-01-19"},
            datetime(2026, 1, 20, tzinfo=UTC),
        )
        later = occurrence_key(
            ClaimAttribute.TECHNOLOGY_DETECTED,
            {"name": "  cloud erp ", "category": "erp", "last_seen": "2026-03-01"},
            datetime(2026, 3, 2, tzinfo=UTC),
        )

        assert early != later, "'CloudERP' and 'cloud erp' are different names to a provider"
        assert (
            occurrence_key(
                ClaimAttribute.TECHNOLOGY_DETECTED,
                {"name": "CloudERP", "category": "erp", "last_seen": "2026-03-01"},
                datetime(2026, 3, 2, tzinfo=UTC),
            )
            == early
        )

    def test_an_intent_week_is_keyed_on_the_observed_week(self) -> None:
        value = {"topic": "Cloud ERP", "observed_week": "2026-01-19", "score": 88}

        assert occurrence_key(
            ClaimAttribute.INTENT_TOPIC_SURGE, value, datetime(2026, 1, 20, tzinfo=UTC)
        ) == occurrence_key(
            ClaimAttribute.INTENT_TOPIC_SURGE, value, datetime(2026, 2, 4, tzinfo=UTC)
        )

    @pytest.mark.parametrize(
        "attribute",
        [a for a, kind in ATTRIBUTE_KINDS.items() if kind is AttributeKind.STATE],
    )
    def test_state_attributes_have_no_occurrence_key(self, attribute: ClaimAttribute) -> None:
        """Asking for one would mean the classification had been ignored."""
        with pytest.raises(UnclassifiedAttributeError):
            occurrence_key(attribute, 1, datetime(2026, 1, 1, tzinfo=UTC))


@pytest.mark.parametrize("date_value", [date(2026, 1, 19), "2026-01-19"], ids=["date", "string"])
def test_occurrence_keys_are_stable_across_value_encodings(date_value: object) -> None:
    """Values arrive as JSON from storage and as objects in memory. A key
    that differed between them would duplicate every observation on the
    first rebuild."""
    key = occurrence_key(
        ClaimAttribute.INTENT_TOPIC_SURGE,
        {"topic": "Cloud ERP", "observed_week": date_value},
        datetime(2026, 1, 20, tzinfo=UTC),
    )

    assert key == "cloud erp|2026-01-19"

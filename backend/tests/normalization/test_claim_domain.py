"""Tests for the Claim domain — Signora's unit of evidence.

The invariants here are the ones every downstream intelligence module
inherits: evidence is immutable, always attributable, never
self-interpreting.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

import pytest

from modules.provider_normalization.domain.claim import (
    Claim,
    ClaimError,
    ClaimSource,
    SubjectHint,
    new_claim,
)
from modules.provider_normalization.domain.outcome import (
    NormalizationOutcome,
    Rejection,
    RejectionReason,
)
from modules.provider_normalization.domain.vocabulary import (
    ATTRIBUTE_VALUE_TYPES,
    ClaimAttribute,
    ClaimDomain,
    IntentSurgeValue,
    RevenueBand,
    TechnologyValue,
    TrendDirection,
    observed_at_is_sane,
)

WORKSPACE = uuid4()


def _source(**overrides: object) -> ClaimSource:
    defaults = {
        "provider": "apollo",
        "raw_record_id": uuid4(),
        "mapper_version": "1",
        "payload_provenance": "DEVELOPMENT_FIXTURE",
    }
    return ClaimSource(**{**defaults, **overrides})  # type: ignore[arg-type]


def _hint() -> SubjectHint:
    return SubjectHint(provider_external_id="acme-corp", domain="acme.example")


class TestVocabulary:
    def test_every_attribute_belongs_to_a_domain(self) -> None:
        """A completeness check: an attribute added without a domain would
        be invisible to any consumer filtering by domain."""
        for attribute in ClaimAttribute:
            assert isinstance(attribute.domain, ClaimDomain)

    def test_every_attribute_declares_its_value_type(self) -> None:
        """A generic value would push type-checking into every consumer,
        and by the Signal Engine nobody would remember what an
        employee_count is."""
        for attribute in ClaimAttribute:
            assert attribute in ATTRIBUTE_VALUE_TYPES

    def test_intent_surge_carries_its_week_separately(self) -> None:
        """Intent is *reported* late: a provider may deliver week 3's score
        in week 5, and conflating the two makes the trajectory unreadable."""
        value = IntentSurgeValue(
            topic="Cloud ERP",
            score=71,
            observed_week=date(2026, 2, 2),
            trend=TrendDirection.EMERGING,
        )

        assert value.observed_week == date(2026, 2, 2)

    def test_revenue_is_a_band_not_a_figure(self) -> None:
        """Inventing a point estimate from a range is exactly the quiet
        interpretation this layer must not do."""
        assert ATTRIBUTE_VALUE_TYPES[ClaimAttribute.REVENUE_BAND] == (RevenueBand,)

    def test_a_naive_timestamp_is_not_sane(self) -> None:
        assert observed_at_is_sane(datetime(2026, 1, 1)) is False  # noqa: DTZ001
        assert observed_at_is_sane(datetime(2026, 1, 1, tzinfo=UTC)) is True


class TestProvenance:
    """No claim exists without provenance. The evidence chain begins here,
    and a claim that cannot be traced looks like knowledge without being
    it."""

    def test_a_claim_carries_its_raw_record(self) -> None:
        record_id = uuid4()

        claim = new_claim(
            workspace_id=WORKSPACE,
            subject=_hint(),
            attribute=ClaimAttribute.EMPLOYEE_COUNT,
            value=120,
            observed_at=datetime.now(UTC),
            source=_source(raw_record_id=record_id),
        )

        assert claim.source.raw_record_id == record_id

    @pytest.mark.parametrize("field", ["provider", "mapper_version", "payload_provenance"])
    def test_a_source_missing_any_field_is_rejected(self, field: str) -> None:
        with pytest.raises(ClaimError, match="evidence chain"):
            _source(**{field: "  "})

    def test_payload_provenance_travels_with_the_claim(self) -> None:
        """So a claim derived from a development fixture stays identifiable
        for as long as fixtures exist — and a downstream conclusion built
        on one can be found when authentic payloads arrive."""
        claim = new_claim(
            workspace_id=WORKSPACE,
            subject=_hint(),
            attribute=ClaimAttribute.EMPLOYEE_COUNT,
            value=120,
            observed_at=datetime.now(UTC),
            source=_source(),
        )

        assert claim.source.payload_provenance == "DEVELOPMENT_FIXTURE"


class TestSubjectHints:
    """Normalization never resolves identity. Knowledge Graph owns entity
    resolution; deciding here that two hints are the same company would
    bury a resolution decision in a translation layer."""

    def test_a_hint_needs_at_least_the_providers_own_identifier(self) -> None:
        with pytest.raises(ClaimError, match="unattributable"):
            SubjectHint(provider_external_id="   ")

    def test_a_hint_with_only_a_provider_id_is_not_resolvable(self) -> None:
        """A provider's private id is only useful within that provider —
        Knowledge Graph has nothing to match on across sources."""
        assert SubjectHint(provider_external_id="apollo-123").is_resolvable is False

    def test_a_domain_or_name_makes_it_resolvable(self) -> None:
        assert SubjectHint(provider_external_id="x", domain="acme.example").is_resolvable
        assert SubjectHint(provider_external_id="x", legal_name="Acme Corp").is_resolvable


class TestClaimInvariants:
    def test_a_claim_is_immutable(self) -> None:
        """New information is a new claim, never an overwrite. Enforced
        again at the database, which grants no UPDATE on the table."""
        claim = new_claim(
            workspace_id=WORKSPACE,
            subject=_hint(),
            attribute=ClaimAttribute.EMPLOYEE_COUNT,
            value=120,
            observed_at=datetime.now(UTC),
            source=_source(),
        )

        with pytest.raises((AttributeError, TypeError)):
            claim.value = 145  # type: ignore[misc]

    def test_a_mistyped_value_is_rejected_at_construction(self) -> None:
        """So a bad mapping fails here rather than three modules
        downstream, where the cause is no longer visible."""
        with pytest.raises(ClaimError, match="requires"):
            new_claim(
                workspace_id=WORKSPACE,
                subject=_hint(),
                attribute=ClaimAttribute.EMPLOYEE_COUNT,
                value="one hundred and twenty",
                observed_at=datetime.now(UTC),
                source=_source(),
            )

    def test_a_naive_observed_at_is_rejected(self) -> None:
        """Assuming UTC for a provider that meant local time silently
        shifts a trajectory by hours, and nobody would find it."""
        with pytest.raises(ClaimError, match="timezone-naive"):
            new_claim(
                workspace_id=WORKSPACE,
                subject=_hint(),
                attribute=ClaimAttribute.EMPLOYEE_COUNT,
                value=120,
                observed_at=datetime(2026, 1, 1),  # noqa: DTZ001
                source=_source(),
            )

    def test_a_structured_value_is_accepted(self) -> None:
        claim = new_claim(
            workspace_id=WORKSPACE,
            subject=_hint(),
            attribute=ClaimAttribute.TECHNOLOGY_DETECTED,
            value=TechnologyValue(name="CloudERP", category="erp"),
            observed_at=datetime.now(UTC),
            source=_source(provider="builtwith"),
        )

        assert isinstance(claim.value, TechnologyValue)

    def test_a_claim_has_no_confidence_field(self) -> None:
        """Normalization has no authority to estimate confidence. A number
        invented here would propagate into buying scores as though it meant
        something."""
        assert not hasattr(Claim, "confidence")
        assert "confidence" not in Claim.__dataclass_fields__


class TestNormalizationOutcome:
    """A record yielding zero claims must be distinguishable from one never
    processed, and an unmappable field must be diagnosable rather than a
    silent null."""

    def test_a_total_failure_is_distinguishable_from_an_empty_record(self) -> None:
        record_id = uuid4()

        failed = NormalizationOutcome(
            raw_record_id=record_id,
            provider="apollo",
            mapper_version="1",
            rejections=(Rejection(RejectionReason.MISSING_REQUIRED_FIELD, "employee_count"),),
        )
        empty = NormalizationOutcome(raw_record_id=record_id, provider="apollo", mapper_version="1")

        assert failed.is_total_failure is True
        assert empty.is_total_failure is False

    def test_a_missing_field_is_flagged_as_the_shape_change_signal(self) -> None:
        """A vendor renaming a field is more urgent than adding one: the
        rename breaks existing mappings, the addition does not."""
        outcome = NormalizationOutcome(
            raw_record_id=uuid4(),
            provider="apollo",
            mapper_version="1",
            rejections=(Rejection(RejectionReason.MISSING_REQUIRED_FIELD, "organization.name"),),
        )

        assert outcome.has_missing_fields is True

    def test_an_ignored_field_is_not_a_rejection(self) -> None:
        """ "We chose not to map this" and "we could not map this" must
        never look the same in a diagnosis."""
        outcome = NormalizationOutcome(
            raw_record_id=uuid4(),
            provider="apollo",
            mapper_version="1",
            ignored_fields=("_fixture",),
        )

        assert outcome.rejections == ()
        assert outcome.has_missing_fields is False
        assert outcome.ignored_fields == ("_fixture",)

    def test_a_rejection_names_the_field_that_failed(self) -> None:
        """ "Mapping failed" costs an engineer an hour that
        "employee_count absent" does not."""
        rejection = Rejection(RejectionReason.UNPARSEABLE_VALUE, "funding_rounds[0].amount_usd")

        assert "funding_rounds[0].amount_usd" in rejection.detail


class TestValueEncoding:
    """A stored claim must be readable in a psql session during an
    incident. An opaque encoding would make the evidence chain unreadable
    exactly when someone needs to follow it."""

    def test_a_structured_value_encodes_to_readable_json(self) -> None:
        from modules.provider_normalization.infrastructure.repository import encode_value

        encoded = encode_value(
            IntentSurgeValue(
                topic="Cloud ERP",
                score=71,
                observed_week=date(2026, 2, 2),
                trend=TrendDirection.EMERGING,
            )
        )

        assert encoded == {
            "topic": "Cloud ERP",
            "score": 71,
            "observed_week": "2026-02-02",
            "trend": "emerging",
        }

    def test_enums_encode_to_their_values(self) -> None:
        from modules.provider_normalization.infrastructure.repository import encode_value

        assert encode_value(RevenueBand.FROM_10M_TO_50M) == "10m_50m"

    def test_scalars_pass_through(self) -> None:
        from modules.provider_normalization.infrastructure.repository import encode_value

        assert encode_value(120) == 120
        assert encode_value("software") == "software"

    def test_sequences_encode_elementwise(self) -> None:
        from modules.provider_normalization.infrastructure.repository import encode_value

        assert encode_value((RevenueBand.OVER_1B, date(2026, 1, 1))) == ["over_1b", "2026-01-01"]

    def test_a_technology_value_encodes_its_dates(self) -> None:
        from modules.provider_normalization.infrastructure.repository import encode_value

        encoded = encode_value(
            TechnologyValue(name="CloudERP", category="erp", first_seen=date(2026, 1, 12))
        )

        assert encoded["first_seen"] == "2026-01-12"
        assert encoded["last_seen"] is None

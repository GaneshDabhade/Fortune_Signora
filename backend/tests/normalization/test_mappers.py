"""Tests for the mapper layer — the border between vendor languages and
Signora's.

Two concerns dominate. **Information must not be lost**: a mapper that
silently drops a field discards evidence that can never be recovered.
And **unknown fields must fail loudly**: a vendor shape change is an
operational event, diagnosable without reading source code.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

from modules.provider_normalization.application.normalize import (
    NormalizeRawRecord,
    RawRecordInput,
)
from modules.provider_normalization.domain.outcome import NormalizationOutcome, RejectionReason
from modules.provider_normalization.domain.vocabulary import (
    ClaimAttribute,
    FundingValue,
    IntentSurgeValue,
    TechnologyValue,
)
from modules.provider_normalization.infrastructure.mappers import MAPPERS
from modules.provider_platform.public import ProviderName

WORKSPACE = uuid4()
OBSERVED = datetime(2026, 2, 23, tzinfo=UTC)


def _normalize(provider: str, payload: dict[str, object]) -> NormalizationOutcome:
    return NormalizeRawRecord(mappers=MAPPERS).execute(
        RawRecordInput(
            raw_record_id=uuid4(),
            workspace_id=WORKSPACE,
            provider=provider,
            payload=payload,
            occurred_at=OBSERVED,
            payload_provenance="DEVELOPMENT_FIXTURE",
        )
    )


class TestFailLoudly:
    def test_an_unknown_field_is_rejected_not_ignored(self) -> None:
        """The signature of a vendor *adding* a field. Silent degradation
        is unacceptable — the field would simply never appear downstream
        and nobody would know to look for it."""
        outcome = _normalize(
            "apollo",
            {"organization": {"id": "a", "name": "Acme"}, "brand_new_field": 1},
        )

        reasons = {r.reason for r in outcome.rejections}
        assert RejectionReason.UNKNOWN_FIELD in reasons

    def test_a_rejection_names_the_field_and_the_mapper_version(self) -> None:
        """Diagnosable without inspecting source code."""
        outcome = _normalize("apollo", {"organization": {"id": "a"}, "surprise": 1})

        detail = next(
            r.detail for r in outcome.rejections if r.reason is RejectionReason.UNKNOWN_FIELD
        )
        assert "surprise" in detail
        assert "apollo" in detail
        assert "v1" in detail

    def test_a_missing_required_field_is_distinguished_from_an_unknown_one(self) -> None:
        """Opposite meanings: a rename breaks existing mappings and is
        urgent; an addition does not."""
        outcome = _normalize("coresignal", {"company_id": "c"})

        assert outcome.has_missing_fields is True

    def test_an_unmapped_provider_is_a_typed_failure(self) -> None:
        """Not an empty result — an unmapped provider must never look like
        a provider with nothing to say."""
        outcome = _normalize("unknown_vendor", {"anything": 1})

        assert outcome.is_total_failure is True
        assert outcome.rejections[0].reason is RejectionReason.UNSUPPORTED_CAPABILITY

    def test_the_fixture_marker_is_ignored_not_rejected(self) -> None:
        """ "We chose not to map this" must not look like "we could not"."""
        outcome = _normalize(
            "apollo", {"_fixture": "DEVELOPMENT FIXTURE", "organization": {"id": "a"}}
        )

        assert "_fixture" in outcome.ignored_fields
        assert not any(r.reason is RejectionReason.UNKNOWN_FIELD for r in outcome.rejections)


class TestPreserveInformation:
    def test_apollo_preserves_every_firmographic_it_carries(self) -> None:
        outcome = _normalize(
            "apollo",
            {
                "_fixture": "x",
                "organization": {
                    "id": "acme",
                    "name": "Acme Corp",
                    "website_url": "https://acme.example",
                    "industry": "software",
                    "estimated_num_employees": 120,
                    "annual_revenue_printed": "$10M-$50M",
                    "founded_year": 2018,
                    "country": "US",
                },
            },
        )

        attributes = {c.attribute for c in outcome.claims}
        assert attributes == {
            ClaimAttribute.EMPLOYEE_COUNT,
            ClaimAttribute.FOUNDED_YEAR,
            ClaimAttribute.INDUSTRY,
            ClaimAttribute.COUNTRY,
            ClaimAttribute.LEGAL_NAME,
            ClaimAttribute.REVENUE_BAND,
        }

    def test_an_unrecognised_revenue_band_is_rejected_not_bucketed(self) -> None:
        """Silently widening an estimate into the nearest band is
        interpretation, and this layer does not interpret."""
        outcome = _normalize(
            "apollo", {"organization": {"id": "a", "annual_revenue_printed": "$7M-$9M"}}
        )

        assert any(r.reason is RejectionReason.UNPARSEABLE_VALUE for r in outcome.rejections)

    def test_builtwith_distinguishes_a_removal_from_a_detection(self) -> None:
        """A technology removal is the signal a migration scenario depends
        on, and it is only observable as is_live going false."""
        outcome = _normalize(
            "builtwith",
            {
                "domain": "acme.example",
                "technologies": [
                    {"name": "LegacyERP", "category": "erp", "is_live": False},
                    {"name": "CloudERP", "category": "erp", "is_live": True},
                ],
            },
        )

        attributes = {c.attribute for c in outcome.claims}
        assert attributes == {
            ClaimAttribute.TECHNOLOGY_REMOVED,
            ClaimAttribute.TECHNOLOGY_DETECTED,
        }

    def test_builtwith_preserves_detection_dates(self) -> None:
        outcome = _normalize(
            "builtwith",
            {
                "domain": "acme.example",
                "technologies": [
                    {
                        "name": "CloudERP",
                        "category": "erp",
                        "first_detected": "2026-01-12",
                        "last_detected": "2026-01-19",
                    }
                ],
            },
        )

        value = outcome.claims[0].value
        assert isinstance(value, TechnologyValue)
        assert value.first_seen == date(2026, 1, 12)

    def test_crunchbase_preserves_the_currency_with_the_amount(self) -> None:
        """An amount without its unit is a number that will eventually be
        wrong."""
        outcome = _normalize(
            "crunchbase",
            {
                "organization": {"uuid": "globex", "name": "Globex"},
                "funding_rounds": [{"investment_type": "series_b", "money_raised_usd": 24_000_000}],
            },
        )

        # Selected by type rather than by position. The mapper now also claims
        # the organisation's name, and a test that indexed into the list was
        # asserting an ordering it never meant to pin.
        (value,) = [c.value for c in outcome.claims if isinstance(c.value, FundingValue)]
        assert value.amount == 24_000_000
        assert value.currency == "USD"

    def test_partial_translation_still_yields_what_succeeded(self) -> None:
        """Discarding partial evidence because part of a payload was bad
        loses information that can never be recovered."""
        outcome = _normalize(
            "builtwith",
            {
                "domain": "acme.example",
                "technologies": [
                    {"category": "erp"},  # no name — rejected
                    {"name": "CloudERP", "category": "erp"},  # fine
                ],
            },
        )

        assert len(outcome.claims) == 1
        assert len(outcome.rejections) == 1


class TestIntentTrajectory:
    def test_each_week_becomes_its_own_claim(self) -> None:
        """Flattening to a current score would destroy the trajectory and
        force the Observation Engine to reconstruct it from nothing."""
        outcome = _normalize(
            "bombora",
            {
                "company_id": "acme",
                "domain": "acme.example",
                "report_week": "2026-02-23",
                "topics": [
                    {
                        "topic": "Cloud ERP",
                        "surge_score": 88,
                        "trend": "emerging",
                        "weekly_history": [18, 42, 71, 88],
                    }
                ],
            },
        )

        assert len(outcome.claims) == 4
        scores = [c.value.score for c in outcome.claims if isinstance(c.value, IntentSurgeValue)]
        assert scores == [18, 42, 71, 88]

    def test_each_week_carries_its_own_date(self) -> None:
        """The history runs backwards from the report week — without
        per-week dates the series has no time axis."""
        outcome = _normalize(
            "bombora",
            {
                "company_id": "acme",
                "report_week": "2026-02-23",
                "topics": [
                    {"topic": "Cloud ERP", "trend": "emerging", "weekly_history": [18, 42, 71, 88]}
                ],
            },
        )

        weeks = [
            c.value.observed_week for c in outcome.claims if isinstance(c.value, IntentSurgeValue)
        ]
        assert weeks == [date(2026, 2, 2), date(2026, 2, 9), date(2026, 2, 16), date(2026, 2, 23)]
        assert weeks == sorted(weeks)

    def test_intent_without_a_trajectory_is_rejected(self) -> None:
        """Falling back to the current score would silently replace a
        trajectory with a point — invisible downstream, and exactly the
        information loss this mapper exists to prevent."""
        outcome = _normalize(
            "bombora",
            {
                "company_id": "acme",
                "topics": [{"topic": "Cloud ERP", "surge_score": 88, "trend": "emerging"}],
            },
        )

        assert outcome.claims == ()
        assert outcome.has_missing_fields is True

    def test_the_reported_trend_is_preserved_not_recomputed(self) -> None:
        """Deriving it here would be interpretation, and downstream has the
        whole series to derive it from anyway."""
        outcome = _normalize(
            "bombora",
            {
                "company_id": "acme",
                "report_week": "2026-02-23",
                "topics": [
                    {"topic": "Cloud ERP", "trend": "decaying", "weekly_history": [88, 71, 42, 18]}
                ],
            },
        )

        value = outcome.claims[0].value
        assert isinstance(value, IntentSurgeValue)
        assert value.trend.value == "decaying"


class TestTranslationOnly:
    """A mapper translates faithfully and never interprets."""

    def test_no_mapper_resolves_identity(self) -> None:
        """Two payloads naming the same company produce two independent
        subjects. Knowledge Graph resolves; normalization does not."""
        apollo = _normalize(
            "apollo",
            {"organization": {"id": "a", "name": "Acme", "website_url": "https://acme.example"}},
        )
        builtwith = _normalize(
            "builtwith",
            {"domain": "acme.example", "technologies": [{"name": "CloudERP", "category": "erp"}]},
        )

        assert apollo.claims[0].subject.provider_external_id == "a"
        assert all(c.subject.provider_external_id == "acme.example" for c in builtwith.claims)

    def test_every_claim_carries_its_mapper_version_and_provenance(self) -> None:
        outcome = _normalize("apollo", {"organization": {"id": "a", "name": "Acme"}})

        source = outcome.claims[0].source
        assert source.mapper_version == "1"
        assert source.payload_provenance == "DEVELOPMENT_FIXTURE"
        assert source.provider == "apollo"

    def test_no_claim_carries_a_confidence(self) -> None:
        outcome = _normalize("apollo", {"organization": {"id": "a", "name": "Acme"}})

        assert not hasattr(outcome.claims[0], "confidence")

    def test_every_ratified_provider_has_a_mapper(self) -> None:
        """**Asserted against `ProviderName` rather than a literal set.**

        This read `== {"apollo", …}` and was correct until the registry
        acquired something that is not a provider. `hubspot` is a *customer's*
        system, keyed by a catalog slug rather than a ratified qualification
        record ([ADR-0300](../../../docs/architecture/adr/0300-inbound-customer-systems.md)),
        so a literal set could only be widened — and widening it would have
        left the test asserting *the registry contains these six strings*,
        which is a restatement of the registry rather than a property of it.

        **What it was actually protecting is that no ratified provider can
        reach normalization with nothing to translate it**, and that is now
        what it says. It also gets stronger for free: adding a `ProviderName`
        member without a mapper fails here, which the literal set could never
        have caught.
        """
        assert {provider.value for provider in ProviderName} <= set(MAPPERS)

    def test_the_registry_also_carries_sources_that_are_not_providers(self) -> None:
        """**The distinction the test above stopped hard-coding.**

        Signora holds a provider's credential; a customer holds their own
        system's. Normalization cannot tell the two apart and must not learn
        to — a claim carries where it came from, and nothing downstream
        branches on it.
        """
        assert "hubspot" in set(MAPPERS) - {provider.value for provider in ProviderName}


class TestOutcomeAlwaysProduced:
    """Every record produces an outcome, including one that yielded
    nothing. A missing outcome and an empty one mean different things, and
    only one of them is a bug."""

    def test_an_unattributable_payload_still_reports_its_shape_problems(self) -> None:
        """Translation stops without a subject — there is nothing to attach
        evidence to — but unknown-field rejections are still reported,
        because they diagnose the same shape change."""
        outcome = _normalize("apollo", {"organization": {}, "mystery": 1})

        reasons = {r.reason for r in outcome.rejections}
        assert RejectionReason.UNRESOLVABLE_SUBJECT in reasons
        assert RejectionReason.UNKNOWN_FIELD in reasons

    def test_an_empty_but_valid_payload_is_not_a_failure(self) -> None:
        outcome = _normalize("builtwith", {"domain": "acme.example", "technologies": []})

        assert outcome.claims == ()
        assert outcome.is_total_failure is False


class TestARegistryCanNameACompany:
    """**Added at M12.1.5**, and each of these was unreachable before it.

    Until this change exactly one mapper claimed `LEGAL_NAME`, and the
    Crunchbase hint carried no domain. Between them those two facts made the
    naming resolver's `AGREED` and `DISPUTED` states **impossible to reach
    through the pipeline** — the product could render a disagreement it could
    never be given. That is not a demo gap; it is a shipped capability with no
    possible input.
    """

    def test_crunchbase_claims_the_name_it_reports(self) -> None:
        outcome = _normalize(
            "crunchbase",
            {"organization": {"uuid": "globex", "name": "Globex Corporation"}},
        )

        names = [
            claim.value
            for claim in outcome.claims
            if claim.attribute is ClaimAttribute.LEGAL_NAME
        ]
        assert names == ["Globex Corporation"]

    def test_crunchbase_offers_a_domain_so_a_differing_name_is_still_one_company(
        self,
    ) -> None:
        """**The half that makes disagreement possible.**

        Identity resolves on provider id, exact domain, or legal name *plus*
        country. With no domain, a registry could only reach an existing
        company by naming it identically — so asserting a different name
        produced a *second company* rather than a disagreement about one, and
        the state the product exists to surface could never occur.
        """
        hint = MAPPERS["crunchbase"].subject(
            {
                "organization": {
                    "uuid": "globex",
                    "name": "Globex Corporation Ltd",
                    "website_url": "https://globex.example",
                }
            }
        )

        assert hint.domain == "globex.example"
        assert hint.legal_name == "Globex Corporation Ltd"

    def test_a_registry_with_no_website_still_maps(self) -> None:
        """Absent rather than empty. A `""` domain would match another
        company that also failed to report one."""
        hint = MAPPERS["crunchbase"].subject({"organization": {"uuid": "globex"}})

        assert hint.domain is None

"""Tests for the CRM mapper — a customer's own system as an evidence source.

The concerns are the package's usual two — **information must not be lost**,
**unknown fields must fail loudly** — plus one this vendor introduces on its
own: **every value arrives as a string**, so parsing is where evidence gets
silently thinner if nobody is watching.

Exercised through `NormalizeRawRecord` rather than the mapper directly, so
registration is part of what is proven. A mapper that translates perfectly
and is not in `MAPPERS` produces `no mapper registered`, which is a passing
unit test and a broken pipeline.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from modules.provider_normalization.application.normalize import (
    NormalizeRawRecord,
    RawRecordInput,
)
from modules.provider_normalization.domain.outcome import NormalizationOutcome, RejectionReason
from modules.provider_normalization.domain.vocabulary import ClaimAttribute, RevenueBand
from modules.provider_normalization.infrastructure.mappers import MAPPERS

WORKSPACE = uuid4()
OBSERVED = datetime(2026, 2, 23, tzinfo=UTC)


def _company(**properties: Any) -> dict[str, Any]:
    """A HubSpot company record, with only the properties a test cares about."""
    return {
        "id": "512",
        "properties": {"domain": "acme.example", "name": "Acme Corp", **properties},
        "createdAt": "2024-01-05T09:00:00Z",
        "updatedAt": "2026-02-23T11:30:00Z",
        "archived": False,
        "_fixture": True,
    }


def _normalize(payload: dict[str, Any]) -> NormalizationOutcome:
    return NormalizeRawRecord(mappers=MAPPERS).execute(
        RawRecordInput(
            raw_record_id=uuid4(),
            workspace_id=WORKSPACE,
            provider="hubspot",
            payload=payload,
            occurred_at=OBSERVED,
            payload_provenance="DEVELOPMENT_FIXTURE",
        )
    )


def _values(outcome: NormalizationOutcome) -> dict[ClaimAttribute, object]:
    return {claim.attribute: claim.value for claim in outcome.claims}


class TestACustomersCrmBecomesEvidence:
    def test_it_is_registered_under_the_catalog_slug(self) -> None:
        """**The registry key and the catalog slug are the same string.**

        `integrations`' catalog knows this system as `hubspot`, and a record
        it produced will carry that as its provider. A mapper registered
        under anything else would translate nothing while looking present.
        """
        assert "hubspot" in MAPPERS
        assert MAPPERS["hubspot"].provider == "hubspot"

    def test_a_company_record_becomes_firmographic_claims(self) -> None:
        outcome = _normalize(
            _company(
                numberofemployees="350",
                annualrevenue="45000000",
                industry="COMPUTER_SOFTWARE",
                country="United States",
                founded_year="2011",
            )
        )

        assert _values(outcome) == {
            ClaimAttribute.LEGAL_NAME: "Acme Corp",
            ClaimAttribute.INDUSTRY: "COMPUTER_SOFTWARE",
            ClaimAttribute.COUNTRY: "United States",
            ClaimAttribute.EMPLOYEE_COUNT: 350,
            ClaimAttribute.FOUNDED_YEAR: 2011,
            ClaimAttribute.REVENUE_BAND: RevenueBand.FROM_10M_TO_50M,
        }
        assert outcome.rejections == ()

    def test_the_industry_is_carried_in_the_vendors_words(self) -> None:
        """**`COMPUTER_SOFTWARE`, not *Computer Software*.**

        A claim preserves what a source said. Every other mapper does the
        same with its vendor's industry vocabulary, and reconciling them is
        a question for a layer with enough context to justify an answer —
        never a translation file quietly improving a string.
        """
        outcome = _normalize(_company(industry="COMPUTER_SOFTWARE"))
        assert _values(outcome)[ClaimAttribute.INDUSTRY] == "COMPUTER_SOFTWARE"

    def test_the_domain_is_a_hint_and_never_a_claim(self) -> None:
        """A domain is how identity resolves, not something a company asserts."""
        outcome = _normalize(_company())
        assert all(claim.subject.domain == "acme.example" for claim in outcome.claims)
        assert ClaimAttribute.INDUSTRY not in _values(outcome)

    def test_the_subject_carries_what_makes_it_merge(self) -> None:
        """**The CRM id alone would give every customer a private company.**

        Identity resolves on provider id, exact domain, or legal name plus
        country. A CRM's record id is shared with nobody, so without the
        domain and the name a connected customer's accounts would sit beside
        the companies Signora already knows rather than joining them — and
        the duplicate would be the account they actually sell to.
        """
        subject = _normalize(_company()).claims[0].subject
        assert subject.provider_external_id == "512"
        assert subject.domain == "acme.example"
        assert subject.legal_name == "Acme Corp"


class TestEveryValueArrivesAsAString:
    def test_a_numeric_string_becomes_a_number(self) -> None:
        outcome = _normalize(_company(numberofemployees="350"))
        assert _values(outcome)[ClaimAttribute.EMPLOYEE_COUNT] == 350

    def test_surrounding_whitespace_is_not_a_shape_change(self) -> None:
        outcome = _normalize(_company(numberofemployees="  350 "))
        assert _values(outcome)[ClaimAttribute.EMPLOYEE_COUNT] == 350
        assert outcome.rejections == ()

    def test_an_unset_property_is_absence_rather_than_a_defect(self) -> None:
        """**The commonest state of any CRM field, and it is not news.**

        A rejection per empty property would bury the shape changes that
        matter under the ordinary condition of every CRM ever populated by
        hand.
        """
        outcome = _normalize(_company(numberofemployees="", annualrevenue=None))
        assert ClaimAttribute.EMPLOYEE_COUNT not in _values(outcome)
        assert outcome.rejections == ()

    def test_an_unreadable_number_is_reported_rather_than_dropped(self) -> None:
        """A value that was present and would not parse is a diagnosis."""
        outcome = _normalize(_company(numberofemployees="about 350"))

        assert ClaimAttribute.EMPLOYEE_COUNT not in _values(outcome)
        assert [r.reason for r in outcome.rejections] == [RejectionReason.UNPARSEABLE_VALUE]
        assert "'numberofemployees' is not a whole number" in outcome.rejections[0].detail

    def test_one_bad_property_does_not_cost_the_others(self) -> None:
        """Partial evidence survives. Discarding it loses what did translate."""
        outcome = _normalize(_company(numberofemployees="unknown", founded_year="2011"))

        assert _values(outcome)[ClaimAttribute.FOUNDED_YEAR] == 2011
        assert _values(outcome)[ClaimAttribute.LEGAL_NAME] == "Acme Corp"
        assert len(outcome.rejections) == 1


class TestRevenueBecomesABand:
    def test_a_figure_lands_in_the_band_that_contains_it(self) -> None:
        outcome = _normalize(_company(annualrevenue="45000000"))
        assert _values(outcome)[ClaimAttribute.REVENUE_BAND] == RevenueBand.FROM_10M_TO_50M

    def test_a_boundary_belongs_to_the_band_above_it(self) -> None:
        """**Lower bound inclusive**, asserted rather than left to a reader.

        Exactly 1,000,000 is `1m_10m`. A boundary convention that lives only
        in somebody's head is one two readers will disagree about, and the
        disagreement surfaces as a company changing band for no reason.
        """
        assert (
            _values(_normalize(_company(annualrevenue="1000000")))[ClaimAttribute.REVENUE_BAND]
            == RevenueBand.FROM_1M_TO_10M
        )
        assert (
            _values(_normalize(_company(annualrevenue="999999")))[ClaimAttribute.REVENUE_BAND]
            == RevenueBand.UNDER_1M
        )

    def test_the_top_band_is_open_ended(self) -> None:
        outcome = _normalize(_company(annualrevenue="7400000000"))
        assert _values(outcome)[ClaimAttribute.REVENUE_BAND] == RevenueBand.OVER_1B

    def test_zero_is_a_figure_and_not_an_absence(self) -> None:
        """A company reporting no revenue said something. `""` said nothing."""
        outcome = _normalize(_company(annualrevenue="0"))
        assert _values(outcome)[ClaimAttribute.REVENUE_BAND] == RevenueBand.UNDER_1M

    def test_a_revenue_that_will_not_parse_is_reported(self) -> None:
        """**`"45M"` is what somebody types into a CRM**, and it is not a number.

        Distinct from the negative case below: this one never became a
        figure at all, so no band could be considered. Reported rather than
        dropped, because a revenue that was present and unreadable is the
        difference between *the customer left it blank* and *we could not
        read what they wrote*.
        """
        outcome = _normalize(_company(annualrevenue="45M"))

        assert ClaimAttribute.REVENUE_BAND not in _values(outcome)
        assert [r.reason for r in outcome.rejections] == [RejectionReason.UNPARSEABLE_VALUE]
        assert "'annualrevenue' is not a whole number" in outcome.rejections[0].detail

    def test_a_negative_figure_is_refused(self) -> None:
        """No band describes it, and the nearest one would be a fiction."""
        outcome = _normalize(_company(annualrevenue="-5000"))

        assert ClaimAttribute.REVENUE_BAND not in _values(outcome)
        assert [r.reason for r in outcome.rejections] == [RejectionReason.UNPARSEABLE_VALUE]


class TestTheShapeChangeSignalReachesTheBagItLivesIn:
    def test_an_unrecognised_property_is_reported(self) -> None:
        """**HubSpot's top level never changes; its properties bag does.**

        `unexpected_fields` checks top-level keys, which is right for every
        other mapper in this package and would be decorative here: `id`,
        `properties`, `createdAt`, `updatedAt` and `archived` are fixed, so
        a mapper declaring only those would report *no unknown fields* on
        the day a property appeared.
        """
        outcome = _normalize(_company(hs_annual_recurring_revenue="120000"))

        assert [r.reason for r in outcome.rejections] == [RejectionReason.UNKNOWN_FIELD]
        assert "hs_annual_recurring_revenue" in outcome.rejections[0].detail

    def test_the_rejection_says_what_a_reader_should_do(self) -> None:
        detail = _normalize(_company(custom_field="x")).rejections[0].detail
        assert "hubspot" in detail
        assert "custom property" in detail

    def test_housekeeping_properties_are_ignored_rather_than_unknown(self) -> None:
        """*Chose not to map* and *could not map* must not look the same."""
        outcome = _normalize(
            _company(
                hs_object_id="512",
                createdate="2024-01-05T09:00:00Z",
                hs_lastmodifieddate="2026-02-23T11:30:00Z",
            )
        )
        assert outcome.rejections == ()

    def test_a_top_level_addition_is_still_caught(self) -> None:
        """The inherited check is not replaced, only joined."""
        payload = _company()
        payload["associations"] = {"contacts": []}
        outcome = _normalize(payload)

        assert [r.reason for r in outcome.rejections] == [RejectionReason.UNKNOWN_FIELD]
        assert "associations" in outcome.rejections[0].detail


class TestWhatItRefusesToTranslate:
    def test_no_claim_is_produced_for_a_commercial_property(self) -> None:
        """**The reason Epic E1 needs a second ruling, asserted here.**

        *Is this already a customer*, *contract value*, *renewal date* and
        *opportunity stage* are what make a CRM worth connecting for Epic D,
        and `ClaimAttribute` has no member for any of them. This test fails
        the day somebody adds one here instead of through the RFC the
        vocabulary requires — which is the quietest place in the codebase to
        make a language decision.
        """
        outcome = _normalize(_company(lifecyclestage="customer", hs_lead_status="OPEN_DEAL"))

        assert {r.reason for r in outcome.rejections} == {RejectionReason.UNKNOWN_FIELD}
        assert all(
            claim.attribute.domain.value == "firmographic" for claim in outcome.claims
        )


class TestAMalformedRecord:
    def test_a_record_with_no_properties_bag_is_reported(self) -> None:
        outcome = _normalize({"id": "512", "archived": False, "_fixture": True})

        assert outcome.claims == ()
        assert [r.reason for r in outcome.rejections] == [
            RejectionReason.MISSING_REQUIRED_FIELD
        ]

    def test_a_record_with_no_id_cannot_be_attributed(self) -> None:
        """**Without a subject there is nothing to attach evidence to.**

        Reported as an unresolvable subject rather than translated into
        claims nothing can file — an unattributable claim is noise that
        looks like knowledge.
        """
        outcome = _normalize({"properties": {"name": "Acme Corp"}, "_fixture": True})

        assert outcome.claims == ()
        assert [r.reason for r in outcome.rejections] == [
            RejectionReason.UNRESOLVABLE_SUBJECT
        ]

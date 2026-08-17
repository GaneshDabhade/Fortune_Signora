"""**The typed accessors on `ClaimView`, exercised through a claim.**

🔴 **These existed and only their module-level decoders were tested.**
`money_from`, `day_from` and `stage_from` had direct coverage because
`knowledge_graph` calls them with a raw value; **the accessors that delegate to
them had none**, and the attribute guard each one opens with — *"return None
when this claim is not that attribute"* — was never executed either way.

⚠️ **That guard is the whole safety of the pair.** Without it `as_money()` on a
`RENEWAL_DATE` claim would reach `money_from` and answer `None` for the right
reason by accident; with it, asking a claim for the wrong shape is refused
before the decode. **A test that never asks the wrong question cannot tell the
two apart.**

📁 [B-1011](../../../docs/BUGS.md) is why they are covered now rather than
later: the repository crossed the coverage floor on a slice this file's subject
was part of.
"""

from __future__ import annotations

from datetime import date

from modules.provider_normalization.domain.vocabulary import (
    ClaimAttribute,
    CommercialStage,
)
from modules.provider_normalization.public import ClaimView, SubjectRef

from tests.knowledge_graph.fakes import claim


def _claim(attribute: ClaimAttribute, value: object) -> ClaimView:
    return claim(attribute=attribute, value=value)


class TestAskingAClaimForTheShapeItCarries:
    def test_open_acv_decodes_to_money(self) -> None:
        view = _claim(ClaimAttribute.OPEN_ACV, {"amount": 1_240_000, "currency": "DKK"})

        money = view.as_money()

        assert money is not None
        assert (money.amount, money.currency) == (1_240_000, "DKK")

    def test_renewal_date_decodes_to_a_day(self) -> None:
        assert _claim(ClaimAttribute.RENEWAL_DATE, "2026-10-12").as_day() == date(2026, 10, 12)

    def test_commercial_stage_keeps_the_tenants_word(self) -> None:
        stage = _claim(
            ClaimAttribute.COMMERCIAL_STAGE,
            {"position": "negotiating", "label": "Negotiation"},
        ).as_stage()

        assert stage is not None
        assert stage.position is CommercialStage.NEGOTIATING
        assert stage.label == "Negotiation"

    def test_an_unmapped_position_keeps_the_label_and_drops_the_position(self) -> None:
        """📁 *"214 opportunities now sit in stages Signora treats as unmapped."*

        ⛔ **The state the CRM Integrations design counts and acts on** — so an
        unrecognised position must not collapse the whole value to `None`.
        """
        stage = _claim(
            ClaimAttribute.COMMERCIAL_STAGE,
            {"position": "legal-review", "label": "Legal review"},
        ).as_stage()

        assert stage is not None
        assert stage.position is None
        assert stage.label == "Legal review"

    def test_a_blank_label_is_refused_rather_than_raising(self) -> None:
        """⛔ **A stored claim is untrusted input and a read surface must not
        raise on one**, which is why the guard is here rather than in the
        constructor."""
        assert _claim(ClaimAttribute.COMMERCIAL_STAGE, {"label": "   "}).as_stage() is None

    def test_a_currency_that_is_not_a_string_is_not_a_figure(self) -> None:
        """📁 [ADR-0409](../../../docs/architecture/adr/0409-commercial-account-facts.md)
        §3: *"a figure without its currency is not a fact."*"""
        assert _claim(ClaimAttribute.OPEN_ACV, {"amount": 10, "currency": 978}).as_money() is None


class TestAskingAClaimForAShapeItDoesNotCarry:
    """🔴 **The attribute guard, which is the half that was never executed.**"""

    def test_a_date_claim_is_not_money(self) -> None:
        assert _claim(ClaimAttribute.RENEWAL_DATE, "2026-10-12").as_money() is None

    def test_a_money_claim_is_not_a_day(self) -> None:
        assert _claim(ClaimAttribute.OPEN_ACV, {"amount": 1, "currency": "EUR"}).as_day() is None

    def test_a_money_claim_is_not_a_stage(self) -> None:
        assert _claim(ClaimAttribute.OPEN_ACV, {"amount": 1, "currency": "EUR"}).as_stage() is None

    def test_a_commercial_claim_is_not_a_technology(self) -> None:
        assert _claim(ClaimAttribute.OPEN_ACV, {"amount": 1, "currency": "EUR"}).as_technology() is None


class TestTheShapesThatDoNotSurviveStorage:
    def test_a_malformed_day_yields_none_rather_than_raising(self) -> None:
        """📁 *"the claim itself is still evidence, and losing all of it because
        one optional field is unparseable would be a worse failure."*"""
        assert _claim(ClaimAttribute.RENEWAL_DATE, "12 October").as_day() is None

    def test_a_technographic_claim_that_is_not_an_object_is_refused(self) -> None:
        assert _claim(ClaimAttribute.TECHNOLOGY_DETECTED, "Salesforce").as_technology() is None

    def test_a_technology_without_a_category_is_refused(self) -> None:
        """⚠️ **Both halves or nothing.** A technology with no category cannot be
        acted on, and half a `TechnologyRef` would be rendered as if it could."""
        assert (
            _claim(ClaimAttribute.TECHNOLOGY_DETECTED, {"name": "Salesforce"}).as_technology()
            is None
        )

    def test_a_technology_carries_its_detection_window(self) -> None:
        """📁 *"that interval is the whole of what makes a displacement
        observable."*"""
        technology = _claim(
            ClaimAttribute.TECHNOLOGY_REMOVED,
            {
                "name": "Cadenza",
                "category": "freight",
                "first_seen": "2024-01-05",
                "last_seen": "2026-02-01",
            },
        ).as_technology()

        assert technology is not None
        assert technology.first_seen == date(2024, 1, 5)
        assert technology.last_seen == date(2026, 2, 1)


class TestTheIdentityAClaimIsAbout:
    def test_the_subject_is_the_provider_and_the_id_it_stated(self) -> None:
        """⛔ **A provider identity, never a resolved one** — resolving these is
        the Knowledge Graph's job and this module has no idea entities exist."""
        view = claim(provider="hubspot", external_id="0011t000")

        assert view.subject == SubjectRef(provider="hubspot", provider_external_id="0011t000")

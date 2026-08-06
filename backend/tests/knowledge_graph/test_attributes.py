"""Resolving an attribute's value, and refusing to do anything more.

**The rule is the deliverable.** [462 §3](../../../docs/architecture/462-observed-attributes-proposal.md)
required it to be *stated in the contract rather than buried in a query*, and
these are the statements made executable.
"""

from datetime import UTC, datetime
from uuid import uuid4

from modules.knowledge_graph.domain.attributes import (
    ResolvedAttribute,
    ValueAgreement,
    resolve_value,
)
from modules.provider_normalization.public import ClaimAttribute, ClaimView

EARLY = datetime(2026, 3, 1, tzinfo=UTC)
LATE = datetime(2026, 9, 1, tzinfo=UTC)


def _claim(provider: str, value: object, when: datetime = EARLY) -> ClaimView:
    return ClaimView(
        id=uuid4(),
        provider=provider,
        attribute=ClaimAttribute.INDUSTRY,
        value=value,
        observed_at=when,
        subject_external_id=f"{provider}-1",
        subject_domain=None,
        subject_legal_name=None,
        payload_provenance="test",
    )


class TestNothingObservedIsAnAnswer:
    def test_no_claims_resolve_to_unknown(self) -> None:
        found = resolve_value(())

        assert found.agreement is ValueAgreement.UNKNOWN
        assert found.value is None
        assert found.providers == ()
        assert not found.is_known

    def test_unknown_is_not_an_error_and_carries_no_provenance(self) -> None:
        """It is the same *unmeasured* TASK-434's predicate already carries,
        arriving from the other end of the same call."""
        assert resolve_value(()).observed_at is None


class TestTheMostRecentClaimWins:
    def test_a_later_observation_replaces_an_earlier_one(self) -> None:
        found = resolve_value((_claim("apollo", "SaaS", EARLY), _claim("apollo", "Fintech", LATE)))

        assert found.value == "Fintech"
        assert found.agreement is ValueAgreement.SINGLE_SOURCE

    def test_one_provider_is_uncorroborated_rather_than_agreed(self) -> None:
        """A lone claim is not consensus — the same distinction `NameAgreement`
        draws, and for the same reason."""
        assert resolve_value((_claim("apollo", "SaaS"),)).agreement is ValueAgreement.SINGLE_SOURCE

    def test_providers_saying_the_same_thing_agree(self) -> None:
        found = resolve_value((_claim("apollo", "SaaS"), _claim("clearbit", "SaaS")))

        assert found.agreement is ValueAgreement.AGREED
        assert found.providers == ("apollo", "clearbit")

    def test_disagreement_is_reported_and_never_silently_settled(self) -> None:
        """**The value is the most recent and the field says it is contested.**
        A consumer showing the value without the agreement is showing a
        disputed fact as a settled one."""
        found = resolve_value(
            (_claim("apollo", "SaaS", EARLY), _claim("clearbit", "Fintech", LATE))
        )

        assert found.value == "Fintech"
        assert found.agreement is ValueAgreement.DISPUTED

    def test_only_the_agreeing_providers_are_named(self) -> None:
        """Listing every provider that reported *something* would make a
        disputed attribute look corroborated by the sources contradicting it."""
        found = resolve_value(
            (
                _claim("apollo", "Fintech", LATE),
                _claim("clearbit", "SaaS", EARLY),
                _claim("zoominfo", "Fintech", EARLY),
            )
        )

        assert found.value == "Fintech"
        assert found.providers == ("apollo", "zoominfo")

    def test_a_tie_breaks_on_provider_name_so_two_runs_agree(self) -> None:
        """A value that depended on row order would make one account answer
        differently to two callers asking at once."""
        first = resolve_value((_claim("apollo", "SaaS", LATE), _claim("clearbit", "Fintech", LATE)))
        second = resolve_value(
            (_claim("clearbit", "Fintech", LATE), _claim("apollo", "SaaS", LATE))
        )

        assert first.value == second.value == "Fintech"

    def test_case_and_spacing_do_not_create_a_dispute(self) -> None:
        found = resolve_value((_claim("apollo", "SaaS"), _claim("clearbit", "  saas ")))

        assert found.agreement is ValueAgreement.AGREED

    def test_a_genuine_synonym_is_still_a_dispute(self) -> None:
        """**The limitation, asserted.** Deciding `SaaS` and `Computer
        Software` mean one thing is a reviewed catalog, not code — the same
        limitation `commercial_profile.evaluation` carries."""
        found = resolve_value((_claim("apollo", "SaaS"), _claim("clearbit", "Computer Software")))

        assert found.agreement is ValueAgreement.DISPUTED

    def test_a_non_text_value_resolves_too(self) -> None:
        """`EMPLOYEE_COUNT` is an `int`, and the rule is the same one."""
        found = resolve_value((_claim("apollo", 500, EARLY), _claim("apollo", 900, LATE)))

        assert found.value == 900


class TestTheContractExposesNoSubject:
    def test_a_resolved_attribute_carries_provider_names_and_no_subject(self) -> None:
        """⛔ **The omission is load-bearing.** A provider identity crossing
        this boundary would let a consumer walk back to the claims and resolve
        them itself, which is the defect the contract closes."""
        found = resolve_value((_claim("apollo", "SaaS"),))

        assert found.providers == ("apollo",)
        assert not hasattr(found, "subject")
        assert not hasattr(found, "subject_external_id")

    def test_no_field_on_the_type_names_a_subject(self) -> None:
        assert set(ResolvedAttribute.__dataclass_fields__) == {
            "value",
            "agreement",
            "providers",
            "observed_at",
        }

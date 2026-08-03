"""Who an account is, and how sure Signora is about it.

**An `Entity` has no name.** Naming one is the truth-resolution the graph
declined to store, and these assert the rule that makes it: most recent claim
wins, ties break deterministically, disagreement is reported rather than
resolved away, and a claim that is not usable as a name is treated as absent.

Every test states something a customer would notice on a screen.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from modules.knowledge_graph.domain.naming import NameAgreement, select_name
from modules.provider_normalization.public import ClaimAttribute, ClaimView

NOW = datetime(2026, 7, 31, 12, 0, tzinfo=UTC)


def _claim(
    provider: str, value: object, *, at: datetime | None = None, subject: str = "acme-1"
) -> ClaimView:
    return ClaimView(
        id=uuid4(),
        provider=provider,
        attribute=ClaimAttribute.LEGAL_NAME,
        value=value,
        observed_at=at or NOW,
        subject_external_id=subject,
        subject_domain=None,
        subject_legal_name=None,
        payload_provenance="raw",
    )


class TestTheMostRecentClaimWins:
    def test_a_renamed_company_shows_its_new_name(self) -> None:
        """**The reason recency is the rule.** A company that renamed should
        display what it is called now, not what the first provider to see it
        called it."""
        selected, _ = select_name(
            (
                _claim("apollo", "Northwind Traders", at=NOW - timedelta(days=90)),
                _claim("apollo", "Northwind Group", at=NOW),
            )
        )

        assert selected is not None
        assert selected.value == "Northwind Group"

    def test_the_selection_names_who_supplied_it_and_when(self) -> None:
        """A name a seller cannot attribute is a name they have to take on
        trust — and `observed_at` is when the *provider* saw it, not when
        Signora stored it."""
        selected, _ = select_name((_claim("builtwith", "Contoso Ltd", at=NOW),))

        assert selected is not None
        assert selected.provider == "builtwith"
        assert selected.observed_at == NOW

    def test_two_providers_observing_at_the_same_instant_resolve_identically(self) -> None:
        """**A display name that depended on row order would render this
        account differently to two people looking at once.**"""
        forward = select_name((_claim("apollo", "A Ltd"), _claim("builtwith", "B Ltd")))
        reverse = select_name((_claim("builtwith", "B Ltd"), _claim("apollo", "A Ltd")))

        assert forward == reverse


class TestAgreementIsReportedRatherThanResolvedAway:
    def test_one_source_is_uncorroborated_not_agreement(self) -> None:
        """A lone claim is not consensus. Calling it agreement would overstate
        what a single source can establish."""
        _, agreement = select_name((_claim("apollo", "Acme Inc"),))

        assert agreement is NameAgreement.SINGLE_SOURCE

    def test_providers_saying_the_same_thing_agree(self) -> None:
        _, agreement = select_name((_claim("apollo", "Acme Inc"), _claim("builtwith", "Acme Inc")))

        assert agreement is NameAgreement.AGREED

    def test_providers_saying_different_things_are_disputed(self) -> None:
        """**The one state worth interrupting a seller for.** A product that
        silently picks one of two names asserts a fact it cannot defend."""
        selected, agreement = select_name(
            (
                _claim("apollo", "Acme Inc", at=NOW - timedelta(days=1)),
                _claim("builtwith", "Acme Incorporated", at=NOW),
            )
        )

        assert agreement is NameAgreement.DISPUTED
        assert selected is not None
        assert selected.value == "Acme Incorporated", "recency still decides what is shown"

    def test_a_provider_correcting_itself_is_not_a_dispute(self) -> None:
        """Agreement compares each provider's **most recent** observation. A
        value that legitimately changed over time is a different fact, and
        reporting it as disagreement would make every renamed company look
        contested."""
        _, agreement = select_name(
            (
                _claim("apollo", "Old Name", at=NOW - timedelta(days=30)),
                _claim("apollo", "New Name", at=NOW),
                _claim("builtwith", "New Name", at=NOW),
            )
        )

        assert agreement is NameAgreement.AGREED

    def test_nobody_naming_it_is_unknown_rather_than_disputed(self) -> None:
        selected, agreement = select_name(())

        assert selected is None
        assert agreement is NameAgreement.UNKNOWN


class TestAnUnusableClaimIsAbsentRatherThanRendered:
    @pytest.mark.parametrize("value", [None, "", "   ", 42, {"name": "Acme"}, []])
    def test_a_value_that_is_not_a_name_is_ignored(self, value: object) -> None:
        """`value` is stored JSON and a provider can put anything in it. A
        `null` or an empty string reaching a row **as a company name** would
        look like a product defect rather than missing data."""
        selected, agreement = select_name((_claim("apollo", value),))

        assert selected is None
        assert agreement is NameAgreement.UNKNOWN

    def test_a_usable_claim_still_wins_beside_an_unusable_one(self) -> None:
        selected, agreement = select_name(
            (
                _claim("apollo", "", at=NOW),
                _claim("builtwith", "Contoso Ltd", at=NOW - timedelta(days=1)),
            )
        )

        assert selected is not None
        assert selected.value == "Contoso Ltd"
        assert agreement is NameAgreement.SINGLE_SOURCE, "an unusable claim is not a source"

    def test_a_name_is_trimmed_rather_than_rendered_with_its_whitespace(self) -> None:
        selected, _ = select_name((_claim("apollo", "  Acme Inc  "),))

        assert selected is not None
        assert selected.value == "Acme Inc"


class TestTheRuleIsIsolatedWhereAPolicyChangeWouldLand:
    def test_selection_depends_on_nothing_but_the_claims(self) -> None:
        """**Pure, so a future precedence policy is a change to one function.**
        No session, no clock, no configuration — a resolver that read any of
        those would spread the decision across the layers that call it."""
        import inspect

        parameters = list(inspect.signature(select_name).parameters)

        assert parameters == ["claims"]

    def test_no_provider_is_ranked_above_another(self) -> None:
        """Provider precedence is a **customer policy** (D7), the same category
        as the scoring model. Encoding a trust order here would put an
        unreviewed judgement in the substrate — so provider name affects only
        tie-breaking, never which claim is preferred."""
        source = inspect_source()

        for ranked in ("apollo", "builtwith", "clearbit", "zoominfo", "salesforce"):
            assert ranked not in source, f"'{ranked}' is named in the selection rule"


def inspect_source() -> str:
    from pathlib import Path

    return (
        Path(__file__).resolve().parents[2]
        / "modules/knowledge_graph/domain/naming.py"
    ).read_text()


class TestTheReadModelExposesOnlyWhatCanBeActedOn:
    def test_it_carries_no_address_nothing_can_resolve(self) -> None:
        """The winning claim's id is deliberately absent: no claims endpoint
        exists, so it would be an address nobody can follow — the defect M12.1
        removed from the attention row. It arrives with evidence resolution."""
        from modules.knowledge_graph.public import AccountIdentity

        fields = set(AccountIdentity.__dataclass_fields__)

        assert fields == {
            "entity_id",
            "name",
            "agreement",
            "source_count",
            "source",
            "observed_at",
            # **Added by A4, and this assertion is why it was argued for
            # rather than appended.** The read model is deliberately narrow;
            # a field set nobody has to justify grows until it is the entity
            # record `Entity` refuses to be. `last_observed_at` says nothing
            # about the company — it says how current Signora's knowledge of
            # it is, which is this module's own work and is acted on the
            # moment it is read.
            "last_observed_at",
        }
        for absent in ("claim_id", "claims", "industry", "employee_count", "domain"):
            assert absent not in fields

    def test_an_unnamed_account_reports_absence_rather_than_a_placeholder(self) -> None:
        from modules.knowledge_graph.application.queries import _identity

        identity = _identity(UUID(int=1), (), None)

        assert identity.name is None
        assert identity.source is None
        assert identity.observed_at is None
        assert identity.last_observed_at is None
        assert identity.source_count == 0
        assert not identity.is_disputed

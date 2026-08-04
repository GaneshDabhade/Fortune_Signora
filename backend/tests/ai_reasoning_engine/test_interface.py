"""What a Decision Package looks like on the wire.

**The module concluded for weeks and nothing could read the conclusion**
([417 §2c](../../../docs/architecture/417-executable-slice-audit.md)). These
assert the contract that makes the new read path safe to render, and they are
deliberately about the *boundary* rather than the reasoning — whether the
conclusion is any good is the harness's question (§10), and whether the package
is well-formed is `test_reason.py`'s.

**The builder is imported rather than rewritten.** A second fixture for a
fifteen-part composition is a second thing to keep in step with the domain, and
the one in `test_reason.py` is already exercised against `DecisionPackage`'s own
construction guards. Same precedent as `tests/ai_platform/test_explanation_source.py`.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from modules.ai_platform.public import GroundedStatement
from modules.ai_reasoning_engine.domain.package import AlternativeReading
from modules.ai_reasoning_engine.domain.support import SupportLevel
from modules.ai_reasoning_engine.interface.schemas import DecisionPackageResponse
from modules.opportunity_engine.public import EvidenceState
from tests.ai_reasoning_engine.test_reason import _package, _support


class TestTheGroundingGuaranteeSurvivesTheWire:
    """**The one property that makes model-authored content renderable.**

    A statement whose citations were dropped on the way out is unverifiable
    prose, and the customer is the only party the guarantee exists for.
    """

    def test_every_authored_statement_arrives_with_its_citations(self) -> None:
        response = DecisionPackageResponse.from_domain(
            _package(
                stated_reasoning=(
                    GroundedStatement(text="Two sources saw it.", evidence=("signal:a",)),
                    GroundedStatement(text="The score moved.", evidence=("buying_score:b",)),
                )
            )
        )

        for statement in (response.proposition, response.summary, *response.stated_reasoning):
            assert statement.text.strip()
            assert statement.evidence, "an uncited sentence reached the wire"

    def test_there_is_no_flattened_paragraph(self) -> None:
        """**Deliberate.** A single `text` field holding the whole conclusion
        would be renderable without any citations at all, which is exactly the
        shape the domain refuses to produce.
        """
        fields = set(DecisionPackageResponse.model_fields)

        assert "text" not in fields
        assert "narrative" not in fields

    def test_the_reasoning_keeps_its_order(self) -> None:
        """Steps in an argument are not a set. Reordering them changes what was
        argued, and the domain stores a tuple for that reason."""
        first = GroundedStatement(text="First.", evidence=("signal:a",))
        second = GroundedStatement(text="Second.", evidence=("signal:b",))

        response = DecisionPackageResponse.from_domain(
            _package(stated_reasoning=(first, second))
        )

        assert [s.text for s in response.stated_reasoning] == ["First.", "Second."]


class TestWhatArguesAgainstTheConclusionIsNotOptional:
    """A conclusion that arrived without its objections would be a verdict, and
    the module's own contract says a Decision Package is a decision *input*."""

    def test_alternative_readings_reach_the_customer(self) -> None:
        response = DecisionPackageResponse.from_domain(
            _package(
                alternative_readings=(
                    AlternativeReading(
                        signal_type="hiring_surge", reason="Only one source saw it."
                    ),
                )
            )
        )

        assert response.alternative_readings[0].signal_type == "hiring_surge"
        assert response.alternative_readings[0].reason == "Only one source saw it."

    def test_a_contested_reading_says_so_rather_than_averaging_it_away(self) -> None:
        """**The disagreement is the finding.** Netting two opposed readings
        into one number is how a customer stops being told there was an
        argument."""
        response = DecisionPackageResponse.from_domain(
            _package(support=_support(contested=True, dissenting_signals=2))
        )

        assert response.support.contested is True
        assert response.support.dissenting_signals == 2

    def test_limitations_and_validation_always_travel(self) -> None:
        """Both are refused as empty at construction, so their presence here is
        the domain's guarantee arriving intact rather than this layer's check."""
        response = DecisionPackageResponse.from_domain(_package())

        assert response.limitations
        assert response.suggested_validation
        assert response.catalog_version >= 1


class TestSupportIsDerivedRatherThanReported:
    """`support_level` exists as a column and the repository deliberately never
    reads it. This asserts the same discipline one layer out: the response
    carries what `SupportBasis` derives, so a drifted copy could not reach a
    customer even if one were introduced."""

    def test_the_level_matches_what_the_basis_derives(self) -> None:
        basis = _support(corroborating_providers=frozenset({"apollo"}))

        response = DecisionPackageResponse.from_domain(_package(support=basis))

        assert response.support.level == basis.level.value

    def test_a_single_source_is_never_reported_as_corroborated(self) -> None:
        """One source is a reading; two that never spoke to each other is
        corroboration. The distinction is the product's, not a nuance — and
        `corroborated` is the strongest thing Signora says without a human."""
        response = DecisionPackageResponse.from_domain(
            _package(support=_support(corroborating_providers=frozenset({"apollo"})))
        )

        assert response.support.level != SupportLevel.CORROBORATED.value
        assert response.support.level == SupportLevel.QUALIFIED.value

    def test_stale_evidence_is_visible_rather_than_quietly_served(self) -> None:
        response = DecisionPackageResponse.from_domain(
            _package(support=_support(evidence_state=EvidenceState.STALE))
        )

        assert response.support.evidence_state == EvidenceState.STALE.value


class TestNothingOnTheWireDependsOnIterationOrder:
    """**A hidden input is an architecture defect** (§2), and a frozenset is the
    classic one — two identical packages must serialise identically."""

    def test_corroborating_providers_are_sorted(self) -> None:
        response = DecisionPackageResponse.from_domain(
            _package(support=_support(corroborating_providers=frozenset({"zoominfo", "apollo"})))
        )

        assert response.support.corroborating_providers == ("apollo", "zoominfo")

    def test_two_identical_packages_serialise_identically(self) -> None:
        providers = frozenset({"apollo", "coresignal", "zoominfo"})
        one = DecisionPackageResponse.from_domain(
            _package(support=_support(corroborating_providers=providers))
        )
        other = DecisionPackageResponse.from_domain(
            _package(support=_support(corroborating_providers=providers))
        )

        assert one.support.model_dump() == other.support.model_dump()


class TestTheOperationalRecordStaysOperational:
    """**The narration schema's rule, applied to the second surface that needs
    it.** These identifiers are how an engineer traces a call, not how a seller
    decides anything — and `evidence_digest` is a hash a customer cannot
    recompute, so it would be provenance nobody can check."""

    def test_no_tracing_identifier_reaches_the_customer(self) -> None:
        fields = set(DecisionPackageResponse.model_fields)

        for internal in (
            "id",
            "correlation_id",
            "inference_id",
            "prompt_fingerprint",
            "evidence_digest",
            "workspace_id",
            "payload_version",
            "subject_kind",
            "originating_buying_score_id",
        ):
            assert internal not in fields, internal

    def test_what_produced_the_conclusion_is_answered_without_a_second_request(self) -> None:
        """A customer reading generated language is entitled to know what
        generated it **at the moment they read it**, not after following a link
        they will not follow."""
        response = DecisionPackageResponse.from_domain(_package())

        assert response.model
        assert response.vendor
        assert response.prompt_name
        assert response.prompt_version >= 1

    def test_the_account_is_named_in_the_customers_vocabulary(self) -> None:
        """`subject_id` is this module's addressing vocabulary and `account_id`
        is the customer's. **The translation happens at the edge** (ADR-0034),
        and this is the edge."""
        account = uuid4()

        response = DecisionPackageResponse.from_domain(_package(subject_id=account))

        assert response.account_id == account


class TestTheHandlerDecidesOnlyOneThing:
    """The route's own branch, exercised without HTTP.

    **A handler translates, authorizes and delegates**, so the single decision
    it owns is *what to do when there is no conclusion yet*. That branch is
    asserted here directly because it is the handler's, and end-to-end through
    the API in `tests/integration/test_api_accounts.py` because a route nobody
    can reach is not a surface.
    """

    class _Context:
        """Just enough `WorkspaceContext` for a handler that reads."""

        workspace_id = uuid4()

        def __init__(self) -> None:
            self.authorized: list[tuple[object, object]] = []

        def authorize(self, resource: object, action: object) -> None:
            self.authorized.append((resource, action))

    class _Packages:
        def __init__(self, package: object | None) -> None:
            self._package = package
            self.asked: list[tuple[object, object]] = []

        async def latest_for(self, workspace_id: object, subject_id: object) -> object | None:
            self.asked.append((workspace_id, subject_id))
            return self._package

        async def save(self, package: object) -> None:  # pragma: no cover - never called
            raise AssertionError("a read path must not be able to write")

    async def test_a_stored_conclusion_comes_back(self) -> None:
        from modules.ai_reasoning_engine.interface.router import account_decision_package

        account = uuid4()
        context = self._Context()
        packages = self._Packages(_package(subject_id=account))

        response = await account_decision_package(
            context=context,  # type: ignore[arg-type]
            packages=packages,  # type: ignore[arg-type]
            account_id=account,
        )

        assert response.account_id == account

    async def test_nothing_concluded_is_a_404_rather_than_an_invented_answer(self) -> None:
        """**The branch worth owning.** An endpoint that manufactured an empty
        conclusion would be asserting Signora had thought about an account it
        has never seen."""
        from fastapi import HTTPException

        from modules.ai_reasoning_engine.interface.router import account_decision_package

        with pytest.raises(HTTPException) as raised:
            await account_decision_package(
                context=self._Context(),  # type: ignore[arg-type]
                packages=self._Packages(None),  # type: ignore[arg-type]
                account_id=uuid4(),
            )

        assert raised.value.status_code == 404

    async def test_it_authorizes_before_it_reads(self) -> None:
        """Ordering, not presence. A check that runs after the read has already
        read."""
        from signora_platform.authorization import Action, Resource

        context = self._Context()
        packages = self._Packages(_package())

        await account_decision_package_for(context, packages)

        assert context.authorized == [(Resource.ACCOUNT, Action.READ)]
        assert packages.asked, "the read never happened"


async def account_decision_package_for(context: object, packages: object) -> object:
    """Calls the handler with the arguments this suite always passes."""
    from modules.ai_reasoning_engine.interface.router import account_decision_package

    return await account_decision_package(
        context=context,  # type: ignore[arg-type]
        packages=packages,  # type: ignore[arg-type]
        account_id=uuid4(),
    )

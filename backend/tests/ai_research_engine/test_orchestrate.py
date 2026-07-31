"""Executing a plan: three derivations, and an orchestrator that decides nothing.

Two things are being protected here. That each comparison is **reproducible from
identical inputs**, which is what makes a `ResearchFinding` DERIVED rather than
labelled so. And that the orchestrator adds **no authority** — it resolves,
delegates and assembles, and every number in a finding came from a rule.

Nothing here calls a model, and nothing reaches a network.
"""

from __future__ import annotations

import ast
import time
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from modules.ai_platform.public import (
    EvidenceFact,
    EvidenceRef,
    EvidenceSet,
    GroundedStatement,
    UngroundedOutputError,
)
from modules.ai_research_engine.application.orchestrate import execute
from modules.ai_research_engine.domain import derivations
from modules.ai_research_engine.domain.derivations import (
    DERIVATIONS,
    Corroboration,
    DerivationError,
    Dissent,
    Recency,
    for_type,
    validate_complete,
)
from modules.ai_research_engine.domain.plan import CATALOG, DerivationType, PlannedStep, ResearchPlan
from modules.ai_research_engine.domain.research import ResearchError, ResearchTask
from modules.ai_research_engine.domain.retrieval import (
    BUSINESS_EVENT,
    CORROBORATED,
    DISSENTING_SIGNAL,
    EVENT_TYPE,
    OBSERVED_ON,
    OCCURRED_ON,
    PROVIDER_COUNT,
    PROVIDERS,
    RELEVANCE,
    SIGNAL_TYPE,
)

WORKSPACE = uuid4()
SUBJECT = EvidenceRef(kind="entity", id=uuid4())
NOW = datetime(2026, 7, 31, 12, 0, tzinfo=UTC)


def _event(*, providers: tuple[str, ...], occurred: date, event_type: str = "hiring_surge") -> EvidenceFact:
    return EvidenceFact(
        ref=EvidenceRef(kind=BUSINESS_EVENT, id=uuid4()),
        workspace_id=WORKSPACE,
        summary="Headcount grew sharply.",
        attributes=(
            (EVENT_TYPE, event_type),
            (OCCURRED_ON, occurred),
            (PROVIDER_COUNT, len(providers)),
            (PROVIDERS, ",".join(sorted(providers))),
            (CORROBORATED, len(providers) > 1),
        ),
    )


def _dissent(*, signal_type: str, relevance: str) -> EvidenceFact:
    return EvidenceFact(
        ref=EvidenceRef(kind=DISSENTING_SIGNAL, id=uuid4()),
        workspace_id=WORKSPACE,
        summary="An outweighed reading.",
        attributes=(
            (SIGNAL_TYPE, signal_type),
            (RELEVANCE, relevance),
            (OBSERVED_ON, date(2026, 5, 1)),
        ),
    )


def _set(*facts: EvidenceFact) -> EvidenceSet:
    return EvidenceSet(workspace_id=WORKSPACE, facts=facts, assembled_at=NOW)


def _plan(derivation: DerivationType, *facts: EvidenceFact) -> ResearchPlan:
    return ResearchPlan(
        steps=(
            PlannedStep(
                derivation=derivation,
                reason=GroundedStatement(
                    text="Worth checking.", evidence=tuple(f.ref.token for f in facts)
                ),
            ),
        )
    )


def _task() -> ResearchTask:
    return ResearchTask(
        id=uuid4(),
        workspace_id=WORKSPACE,
        correlation_id=uuid4(),
        subject=SUBJECT,
        opportunity_id=uuid4(),
        requested_at=NOW,
    )


class TestEveryDeclaredDerivationHasExactlyOneRule:
    def test_the_registry_pairs_with_the_catalog(self) -> None:
        validate_complete()
        assert {rule.derives for rule in DERIVATIONS} == set(CATALOG)

    @pytest.mark.parametrize("derivation", list(DerivationType))
    def test_each_type_resolves_to_its_own_rule(self, derivation: DerivationType) -> None:
        assert for_type(derivation).derives is derivation

    def test_a_declared_type_with_no_rule_is_refused(self) -> None:
        """A promise the planner can make and nothing can keep."""
        with pytest.raises(DerivationError, match="no derivation to compute"):
            validate_complete((Corroboration(), Dissent()))

    def test_a_rule_with_no_declaration_is_refused(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A comparison with no stated question and no checked input contract.

        The catalog is narrowed rather than the registry widened, because
        `derives` is typed as a `DerivationType` — an invented name is already
        unconstructable, and the reachable version of this failure is a
        catalog entry being deleted while its rule stays registered.
        """
        narrowed = {
            key: value for key, value in CATALOG.items() if key is not DerivationType.RECENCY
        }
        monkeypatch.setattr(derivations, "CATALOG", narrowed)

        with pytest.raises(DerivationError, match="not declared"):
            validate_complete()

    def test_the_pairing_is_checked_at_import_rather_than_at_first_use(self) -> None:
        """**Found by a surviving mutation.** Calling `validate_complete()` in
        the tests proves the function works; it does not prove the module runs
        it. Commenting out the module-level call changed nothing, which meant a
        mispairing would have surfaced on the first research request rather
        than when the module loaded.
        """
        tree = ast.parse(
            (Path(derivations.__file__).read_text(encoding="utf-8")), type_comments=False
        )
        called = {
            node.value.func.id
            for node in tree.body
            if isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
        }
        assert "validate_complete" in called, (
            "derivations.py no longer validates its pairing at import time. A declared "
            "derivation with no rule would then be discovered by the first request that "
            "planned it, in production, rather than at load."
        )

    def test_two_rules_claiming_one_type_are_refused(self) -> None:
        """Which one runs would depend on registry order, and a finding's
        content would depend on where a rule was declared."""
        with pytest.raises(DerivationError, match="two derivations claim one type"):
            validate_complete((*DERIVATIONS, Corroboration()))


class TestCorroboration:
    def test_it_separates_single_source_conclusions_from_agreed_ones(self) -> None:
        """**The comparison nothing in the product performs today**, and the
        one that feeds `SupportBasis`'s "two distinct providers"."""
        facts = (
            _event(providers=("apollo",), occurred=date(2026, 6, 1)),
            _event(providers=("apollo", "coresignal"), occurred=date(2026, 6, 2)),
        )
        attributes = dict(Corroboration().run(facts))

        assert attributes["conclusions"] == 2
        assert attributes["single_source"] == 1
        assert attributes["independently_agreed"] == 1
        assert attributes["distinct_providers"] == 2
        assert attributes["providers"] == "apollo,coresignal"

    def test_a_provider_seen_twice_is_one_provider(self) -> None:
        """Rule 21 — corroboration is independent sources agreeing, and one
        source repeating itself is one source."""
        facts = (
            _event(providers=("apollo",), occurred=date(2026, 6, 1)),
            _event(providers=("apollo",), occurred=date(2026, 6, 2)),
        )
        assert dict(Corroboration().run(facts))["distinct_providers"] == 1

    def test_fact_order_does_not_change_the_result(self) -> None:
        left = _event(providers=("apollo",), occurred=date(2026, 6, 1))
        right = _event(providers=("coresignal",), occurred=date(2026, 6, 2))

        assert Corroboration().run((left, right)) == Corroboration().run((right, left))


class TestDissent:
    def test_it_reports_what_was_outweighed_without_ranking_it(self) -> None:
        """Relevance is a category with no numeric meaning. Reporting a
        *strongest* dissent would order one, which is how a category becomes a
        score."""
        facts = (
            _dissent(signal_type="budget_freeze", relevance="high"),
            _dissent(signal_type="churn_risk", relevance="moderate"),
        )
        attributes = dict(Dissent().run(facts))

        assert attributes["dissenting_signals"] == 2
        assert attributes["signal_types"] == "budget_freeze,churn_risk"
        assert attributes["relevances"] == "high,moderate"
        assert not any("strongest" in name or "max" in name for name, _ in Dissent().run(facts))

    def test_repeated_values_are_reported_once(self) -> None:
        facts = (
            _dissent(signal_type="churn_risk", relevance="high"),
            _dissent(signal_type="churn_risk", relevance="high"),
        )
        attributes = dict(Dissent().run(facts))

        assert attributes["dissenting_signals"] == 2
        assert attributes["signal_types"] == "churn_risk"


class TestRecency:
    def test_it_measures_the_span_without_judging_it(self) -> None:
        """A measurement, not a verdict. Nothing here decides that an interval
        is too long — that threshold belongs to whoever reads the finding."""
        facts = (
            _event(providers=("apollo",), occurred=date(2026, 3, 1)),
            _event(providers=("apollo",), occurred=date(2026, 6, 1)),
        )
        attributes = dict(Recency().run(facts))

        assert attributes["oldest_on"] == date(2026, 3, 1)
        assert attributes["newest_on"] == date(2026, 6, 1)
        assert attributes["span_days"] == 92
        assert not any("stale" in name for name, _ in Recency().run(facts))

    def test_fact_order_does_not_change_the_span(self) -> None:
        """**Found by a surviving mutation.** Removing the sort left
        `oldest_on` as *the first fact given* rather than the earliest — which
        every ascending fixture agrees with, and no descending one does."""
        early = _event(providers=("apollo",), occurred=date(2026, 3, 1))
        late = _event(providers=("apollo",), occurred=date(2026, 6, 1))

        assert Recency().run((late, early)) == Recency().run((early, late))
        assert dict(Recency().run((late, early)))["oldest_on"] == date(2026, 3, 1)

    def test_one_event_spans_no_days(self) -> None:
        facts = (_event(providers=("apollo",), occurred=date(2026, 6, 1)),)
        assert dict(Recency().run(facts))["span_days"] == 0

    def test_an_untyped_date_is_refused(self) -> None:
        """Retrieval writes typed attributes precisely so a comparison never
        parses one back out of text."""
        fact = EvidenceFact(
            ref=EvidenceRef(kind=BUSINESS_EVENT, id=uuid4()),
            workspace_id=WORKSPACE,
            summary="x",
            attributes=((OCCURRED_ON, "2026-06-01"),),
        )
        with pytest.raises(DerivationError, match="expected a date"):
            Recency().run((fact,))


class TestTheOrchestratorDecidesNothing:
    def test_it_produces_one_finding_per_planned_step(self) -> None:
        event = _event(providers=("apollo", "coresignal"), occurred=date(2026, 6, 1))
        dissent = _dissent(signal_type="churn_risk", relevance="high")
        plan = ResearchPlan(
            steps=(
                *_plan(DerivationType.CORROBORATION, event).steps,
                *_plan(DerivationType.DISSENT, dissent).steps,
            )
        )

        findings = execute(_task(), plan, _set(event, dissent), now=NOW)

        assert [f.derivation for f in findings] == ["corroboration", "dissent"]
        assert all(f.workspace_id == WORKSPACE for f in findings)

    def test_an_empty_plan_produces_no_findings(self) -> None:
        """Stopping is a planning answer, and executing that answer means
        deriving nothing — not deriving something empty."""
        event = _event(providers=("apollo",), occurred=date(2026, 6, 1))
        assert execute(_task(), ResearchPlan(), _set(event), now=NOW) == ()

    def test_every_finding_cites_exactly_what_its_step_targeted(self) -> None:
        event = _event(providers=("apollo",), occurred=date(2026, 6, 1))
        other = _event(providers=("coresignal",), occurred=date(2026, 6, 2))

        findings = execute(
            _task(), _plan(DerivationType.CORROBORATION, event), _set(event, other), now=NOW
        )

        assert findings[0].cited == (event.ref,)

    def test_a_step_targeting_an_invented_fact_never_reaches_a_derivation(self) -> None:
        """M8's grounding, reused. Nothing here re-checks closure."""
        event = _event(providers=("apollo",), occurred=date(2026, 6, 1))
        stranger = _event(providers=("apollo",), occurred=date(2026, 6, 1))

        with pytest.raises(UngroundedOutputError):
            execute(
                _task(), _plan(DerivationType.CORROBORATION, stranger), _set(event), now=NOW
            )

    def test_evidence_from_another_workspace_is_refused(self) -> None:
        event = _event(providers=("apollo",), occurred=date(2026, 6, 1))
        elsewhere = uuid4()
        stranger = EvidenceFact(
            ref=EvidenceRef(kind=BUSINESS_EVENT, id=uuid4()),
            workspace_id=elsewhere,
            summary="Assembled elsewhere.",
        )
        foreign = EvidenceSet(workspace_id=elsewhere, facts=(stranger,), assembled_at=NOW)

        with pytest.raises(ResearchError, match="Nothing may cross a workspace boundary"):
            execute(_task(), _plan(DerivationType.CORROBORATION, event), foreign, now=NOW)

    def test_the_orchestrator_performs_no_arithmetic_of_its_own(self) -> None:
        """**Structural, not stylistic.** Every attribute in a finding must be
        traceable to the rule that computed it, so the orchestrator's output
        must equal the rule's output exactly."""
        event = _event(providers=("apollo", "coresignal"), occurred=date(2026, 6, 1))

        findings = execute(
            _task(), _plan(DerivationType.CORROBORATION, event), _set(event), now=NOW
        )

        assert findings[0].attributes == tuple(sorted(Corroboration().run((event,))))


class TestReRunningIsSafe:
    def test_the_same_plan_over_the_same_facts_produces_the_same_findings(self) -> None:
        """**What resumability rests on.** A partially completed run resumes by
        running again: what exists collides on its primary key and inserts
        nothing, so there is no progress checkpoint to keep consistent."""
        event = _event(providers=("apollo",), occurred=date(2026, 6, 1))
        task = _task()
        plan = _plan(DerivationType.CORROBORATION, event)

        first = execute(task, plan, _set(event), now=NOW)
        second = execute(task, plan, _set(event), now=NOW)

        assert [f.id for f in first] == [f.id for f in second]
        assert first[0].attributes == second[0].attributes

    def test_a_different_task_re_deriving_the_same_comparison_finds_the_same_thing(
        self,
    ) -> None:
        """`task_id` records the run that first derived a finding and is
        deliberately absent from its identity, so a later run does not
        duplicate what an earlier one already established."""
        event = _event(providers=("apollo",), occurred=date(2026, 6, 1))
        plan = _plan(DerivationType.CORROBORATION, event)

        first = execute(_task(), plan, _set(event), now=NOW)
        later = execute(_task(), plan, _set(event), now=NOW)

        assert first[0].id == later[0].id
        assert first[0].task_id != later[0].task_id

    def test_the_rules_own_version_is_what_identifies_a_finding(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """**Found by a surviving mutation.** Every rule is at version 1 today,
        so an orchestrator that hardcoded 1 would be indistinguishable from one
        that read the rule — until the first rule was revised, at which point
        the new answer would collide with the old id and silently keep the old
        value.
        """
        event = _event(providers=("apollo",), occurred=date(2026, 6, 1))
        task = _task()
        plan = _plan(DerivationType.CORROBORATION, event)

        at_v1 = execute(task, plan, _set(event), now=NOW)

        monkeypatch.setattr(Corroboration, "version", 2)
        at_v2 = execute(task, plan, _set(event), now=NOW)

        assert at_v1[0].derivation_version == 1
        assert at_v2[0].derivation_version == 2
        assert at_v1[0].id != at_v2[0].id


class TestExecutionCost:
    def test_a_full_plan_over_a_realistic_fact_set_is_microseconds(self) -> None:
        """**The measurement R-09 asked for, and the honest scope of it.**

        Everything the orchestrator executes is a pure comparison over facts
        already in memory. The term that dominates a research task is the model
        call, and no prompt exists yet — so this measures what can be measured
        and the timeout stays open rather than being guessed.

        The bound is deliberately loose: it exists to catch an accidental
        quadratic, not to police a machine's speed.
        """
        events = tuple(
            _event(providers=("apollo", "coresignal"), occurred=date(2026, 1, 1 + n))
            for n in range(25)
        )
        dissent = tuple(
            _dissent(signal_type=f"type_{n}", relevance="high") for n in range(10)
        )
        plan = ResearchPlan(
            steps=(
                *_plan(DerivationType.CORROBORATION, *events).steps,
                *_plan(DerivationType.RECENCY, *events).steps,
                *_plan(DerivationType.DISSENT, *dissent).steps,
            )
        )
        evidence = _set(*events, *dissent)
        task = _task()

        started = time.perf_counter()
        findings = execute(task, plan, evidence, now=NOW)
        elapsed = time.perf_counter() - started

        assert len(findings) == 3
        assert elapsed < 0.1, f"a full plan took {elapsed:.4f}s"

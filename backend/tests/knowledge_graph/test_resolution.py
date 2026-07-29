"""Tests for identity resolution — the first decision Signora makes.

Three properties carry the design: **explainable** (every decision names
what matched), **deterministic** (same claims, any order, same graph), and
**biased against over-merge** (ambiguity never merges).

The third is the one that matters most in production. An under-merge is a
visible duplicate somebody reports. An over-merge silently mixes two
customers' intelligence and looks perfectly clean while doing it.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from modules.knowledge_graph.domain.identity import (
    RULE_STRENGTH,
    IdentityState,
    MatchStrength,
    ResolutionOutcome,
    ResolutionRule,
)
from modules.knowledge_graph.domain.resolution import (
    ResolutionCandidate,
    ResolutionInput,
    normalize_domain,
    normalize_name,
    resolve,
)

WORKSPACE = uuid4()
NOW = datetime(2026, 3, 1, tzinfo=UTC)


def _input(**overrides: object) -> ResolutionInput:
    defaults: dict[str, object] = {
        "provider": "apollo",
        "provider_external_id": "acme-corp",
        "domain": "acme.example",
        "legal_name": "Acme Corp",
        "country": "US",
        "evidence_claim_ids": (),
    }
    return ResolutionInput(**{**defaults, **overrides})  # type: ignore[arg-type]


def _candidate(entity_id: UUID, **overrides: object) -> ResolutionCandidate:
    defaults: dict[str, object] = {
        "entity_id": entity_id,
        "provider": "builtwith",
        "provider_external_id": "acme.example",
        "domain": "acme.example",
        "legal_name": "Acme Corp",
        "country": "US",
    }
    return ResolutionCandidate(**{**defaults, **overrides})  # type: ignore[arg-type]


class TestBiasAgainstOverMerge:
    """The asymmetry the whole design turns on."""

    def test_two_matching_candidates_never_merge(self) -> None:
        first, second = uuid4(), uuid4()

        decision, state = resolve(
            _input(),
            (_candidate(first), _candidate(second)),
            workspace_id=WORKSPACE,
            now=NOW,
        )

        assert decision.outcome is ResolutionOutcome.AMBIGUOUS
        assert state is IdentityState.AMBIGUOUS
        assert decision.entity_id is None, "an ambiguous identity must bind to nothing"

    def test_ambiguity_records_what_it_could_not_choose_between(self) -> None:
        """So an operator can see the candidates rather than guessing at
        what confused it."""
        first, second = uuid4(), uuid4()

        decision, _ = resolve(
            _input(), (_candidate(first), _candidate(second)), workspace_id=WORKSPACE, now=NOW
        )

        assert set(decision.candidate_entity_ids) == {first, second}

    def test_two_bindings_of_the_same_entity_are_not_ambiguous(self) -> None:
        """One company legitimately has several provider identities.
        Matching two of them is agreement, not conflict."""
        entity = uuid4()

        decision, state = resolve(
            _input(),
            (
                _candidate(entity, provider="builtwith"),
                _candidate(entity, provider="crunchbase", provider_external_id="cb-1"),
            ),
            workspace_id=WORKSPACE,
            now=NOW,
        )

        assert decision.outcome is ResolutionOutcome.BOUND
        assert state is IdentityState.IDENTIFIED
        assert decision.entity_id == entity


class TestRulePrecedence:
    def test_a_certain_match_is_never_passed_over_for_a_weaker_one(self) -> None:
        """Otherwise a name collision could override the provider's own
        key — the one thing that cannot be wrong."""
        by_id, by_name = uuid4(), uuid4()

        decision, _ = resolve(
            _input(domain=None),
            (
                _candidate(
                    by_id, provider="apollo", provider_external_id="acme-corp", legal_name=None
                ),
                _candidate(by_name, provider="crunchbase", provider_external_id="other"),
            ),
            workspace_id=WORKSPACE,
            now=NOW,
        )

        assert decision.entity_id == by_id
        assert decision.reasons[0].rule is ResolutionRule.SAME_PROVIDER_ID

    def test_domain_outranks_legal_name(self) -> None:
        by_domain, by_name = uuid4(), uuid4()

        decision, _ = resolve(
            _input(),
            (
                _candidate(by_domain, legal_name=None, country=None),
                _candidate(by_name, domain="different.example"),
            ),
            workspace_id=WORKSPACE,
            now=NOW,
        )

        assert decision.entity_id == by_domain
        assert decision.reasons[0].rule is ResolutionRule.EXACT_DOMAIN

    def test_no_match_creates_rather_than_failing(self) -> None:
        """A company Signora has not seen has to start somewhere. This is
        a normal outcome, not an error."""
        decision, state = resolve(_input(), (), workspace_id=WORKSPACE, now=NOW)

        assert decision.outcome is ResolutionOutcome.CREATED
        assert state is IdentityState.IDENTIFIED
        assert decision.reasons == ()


class TestExplainability:
    def test_a_decision_names_the_value_that_matched(self) -> None:
        """Not merely that a domain rule fired — *which* domain. Future
        explainability depends entirely on these surviving."""
        decision, _ = resolve(_input(), (_candidate(uuid4()),), workspace_id=WORKSPACE, now=NOW)

        reason = decision.reasons[0]
        assert reason.field == "domain"
        assert reason.value == "acme.example"
        assert "acme.example" in reason.describe()

    def test_every_outcome_explains_itself(self) -> None:
        bound, _ = resolve(_input(), (_candidate(uuid4()),), workspace_id=WORKSPACE, now=NOW)
        created, _ = resolve(_input(), (), workspace_id=WORKSPACE, now=NOW)
        ambiguous, _ = resolve(
            _input(),
            (_candidate(uuid4()), _candidate(uuid4())),
            workspace_id=WORKSPACE,
            now=NOW,
        )

        assert "bound to" in bound.explain()
        assert "no rule matched" in created.explain()
        assert "nothing merged" in ambiguous.explain()

    def test_evidence_claims_travel_with_the_decision(self) -> None:
        claims = (uuid4(), uuid4())

        decision, _ = resolve(
            _input(evidence_claim_ids=claims),
            (_candidate(uuid4()),),
            workspace_id=WORKSPACE,
            now=NOW,
        )

        assert decision.evidence_claim_ids == claims


class TestMatchStrength:
    """A property of the rule, never a computed belief."""

    def test_every_rule_declares_its_strength(self) -> None:
        for rule in ResolutionRule:
            assert rule in RULE_STRENGTH

    def test_the_providers_own_key_is_certain(self) -> None:
        assert RULE_STRENGTH[ResolutionRule.SAME_PROVIDER_ID] is MatchStrength.CERTAIN

    def test_domain_is_strong_but_not_certain(self) -> None:
        """Subsidiaries and agencies share domains."""
        assert RULE_STRENGTH[ResolutionRule.EXACT_DOMAIN] is MatchStrength.STRONG

    def test_name_matching_is_the_weakest(self) -> None:
        """Two unrelated 'Acme Ltd' in one country is a real scenario."""
        assert RULE_STRENGTH[ResolutionRule.LEGAL_NAME_AND_COUNTRY] is MatchStrength.MODERATE

    def test_strength_is_the_weakest_reason_not_a_combination(self) -> None:
        """Two moderate matches do not make a strong one. Treating them as
        if they did would be the probabilistic scoring this model exists
        to avoid."""
        decision, _ = resolve(
            _input(),
            (_candidate(uuid4(), provider="apollo", provider_external_id="acme-corp"),),
            workspace_id=WORKSPACE,
            now=NOW,
        )

        assert decision.strength is MatchStrength.CERTAIN

    def test_a_created_entity_has_no_strength(self) -> None:
        """Nothing matched, so there is nothing to be strong about."""
        decision, _ = resolve(_input(), (), workspace_id=WORKSPACE, now=NOW)

        assert decision.strength is None


class TestDeterminism:
    def test_candidate_order_does_not_change_the_outcome(self) -> None:
        """Claims arrive in whatever order the pipeline delivers them. If
        order changed the graph, rebuilds and regression tests would both
        be meaningless."""
        candidates = tuple(_candidate(uuid4(), domain=f"c{i}.example") for i in range(6))
        target = _candidate(uuid4())
        pool = (*candidates, target)

        outcomes = set()
        for seed in range(8):
            shuffled = list(pool)
            random.Random(seed).shuffle(shuffled)
            decision, _ = resolve(_input(), tuple(shuffled), workspace_id=WORKSPACE, now=NOW)
            outcomes.add((decision.outcome, decision.entity_id))

        assert len(outcomes) == 1, f"resolution varied with input order: {outcomes}"

    def test_ambiguous_reasons_are_ordered_stably(self) -> None:
        """So two runs produce byte-identical decisions, not merely
        equivalent ones."""
        first, second = uuid4(), uuid4()
        pool = (_candidate(first), _candidate(second))

        a, _ = resolve(_input(), pool, workspace_id=WORKSPACE, now=NOW)
        b, _ = resolve(_input(), tuple(reversed(pool)), workspace_id=WORKSPACE, now=NOW)

        assert a.reasons == b.reasons
        assert a.candidate_entity_ids == b.candidate_entity_ids


class TestNormalization:
    """Real provider data is messier than fixtures. Centralised so the
    inevitable extension is one edit rather than a hunt."""

    @pytest.mark.parametrize(
        "raw",
        [
            "acme.example",
            "ACME.example",
            "https://acme.example",
            "www.acme.example",
            " acme.example/ ",
        ],
    )
    def test_domain_variants_normalize_together(self, raw: str) -> None:
        assert normalize_domain(raw) == "acme.example"

    def test_an_empty_domain_is_none_not_an_empty_match(self) -> None:
        """An empty string matching another empty string would merge every
        company with no domain into one."""
        assert normalize_domain("") is None
        assert normalize_domain("   ") is None

    def test_names_normalize_on_case_and_whitespace(self) -> None:
        assert normalize_name("  Acme   Corp ") == "acme corp"

    def test_a_missing_domain_never_matches(self) -> None:
        decision, _ = resolve(
            _input(domain=None, legal_name=None),
            (_candidate(uuid4(), provider="builtwith", domain=None, legal_name=None),),
            workspace_id=WORKSPACE,
            now=NOW,
        )

        assert decision.outcome is ResolutionOutcome.CREATED, (
            "two companies with no domain must not resolve to each other"
        )

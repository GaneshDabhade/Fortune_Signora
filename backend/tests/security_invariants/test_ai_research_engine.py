"""Invariants: the AI Research Engine's boundary, installed before its code.

**Written at T131, before the module contains a single domain type.** That
ordering is deliberate and has precedent: a guard installed before the code it
guards is the right order, because the alternative is writing the code first
and discovering afterwards which boundary it already crossed.

Three guarantees, each of which would be violated quietly:

**The graph edge points one way.** `ARE -> AIR` is ratified: the AI Reasoning
Engine consumes a completed research artifact opportunistically. Research must
never reach *back* into reasoning — a cycle would make both modules
unextractable and neither testable in isolation.

**The module is under Clean Architecture enforcement.** The layering contract
does not auto-discover modules, by design, so a module absent from its
`containers` list is silently unenforced.

**No upstream module depends on it.** The pipeline flows one way, and the AI
Platform in particular must stay a substrate.

**Extended at T132, when the module acquired domain types**, with two
guarantees that could not be stated before they had something to bind:

**Research stays internal.** The Internal Research ruling of 2026-07-31 is a
product decision, and one recorded only in a document is one a future task can
contradict without noticing. ATTESTED is unconstructable and no file in the
module may import a network client.

**INFERRED knowledge is uncitable.** Enforced by absence — a synthesis has no
address — with a positive control proving the absence is not vacuous.

These tests read source, configuration and the domain's own types. They never
call a model and never touch a database.
"""

from __future__ import annotations

import ast
import tomllib
from dataclasses import fields
from pathlib import Path

import pytest

from modules.ai_platform.infrastructure.explanation import (
    BUYING_SCORE,
    CONTRIBUTION,
    OPPORTUNITY,
)
from modules.ai_research_engine.domain import research
from modules.ai_research_engine.domain.knowledge import EpistemicOrigin
from modules.ai_research_engine.domain.research import ResearchFinding
from modules.ai_research_engine.domain.retrieval import RESEARCH_FACT_KINDS

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = BACKEND_ROOT / "pyproject.toml"
MODULE_ROOT = BACKEND_ROOT / "modules" / "ai_research_engine"

pytestmark = pytest.mark.security_invariant


def _contracts() -> list[dict[str, object]]:
    with PYPROJECT.open("rb") as handle:
        return list(tomllib.load(handle)["tool"]["importlinter"]["contracts"])


def _by_name(name: str) -> dict[str, object]:
    found = next((c for c in _contracts() if c["name"] == name), None)
    assert found is not None, (
        f"import-linter contract '{name}' is missing from pyproject.toml. Deleting a "
        "contract makes the rule it expressed unenforceable while every run stays green."
    )
    return found


class TestTheModuleIsUnderEnforcement:
    def test_the_scaffold_has_every_clean_architecture_layer(self) -> None:
        """A layer added later is a layer whose contract never applied to the
        code written before it."""
        for layer in ("domain", "application", "infrastructure", "public", "evaluation"):
            assert (MODULE_ROOT / layer / "__init__.py").is_file(), f"{layer}/ is missing"

    def test_it_is_in_the_layering_contract(self) -> None:
        layering = _by_name("modules: Clean Architecture layering")
        assert "modules.ai_research_engine" in layering["containers"]  # type: ignore[operator]

    def test_its_domain_is_free_of_frameworks(self) -> None:
        contract = _by_name(
            "ai_research_engine: domain has no infrastructure/framework dependencies"
        )
        forbidden = contract["forbidden_modules"]
        assert "sqlalchemy" in forbidden  # type: ignore[operator]
        assert "httpx" in forbidden  # type: ignore[operator]

    def test_it_reaches_other_modules_only_through_public(self) -> None:
        contract = _by_name("ai_research_engine reaches other modules only through public/")
        forbidden = contract["forbidden_modules"]
        assert "modules.ai_platform.domain" in forbidden  # type: ignore[operator]
        assert "modules.opportunity_engine.application" in forbidden  # type: ignore[operator]


class TestTheResearchEdgePointsOneWay:
    """`ARE -> AIR` is ratified. The reverse is a cycle."""

    def test_research_may_not_depend_on_reasoning(self) -> None:
        contract = _by_name("the AI Research Engine does not depend on the AI Reasoning Engine")
        assert contract["source_modules"] == ["modules.ai_research_engine"]
        assert contract["forbidden_modules"] == ["modules.ai_reasoning_engine"]

    def test_reasoning_may_still_depend_on_research(self) -> None:
        """**The positive control, and the reason the test above is not simply
        "forbid everything".**

        `AIR -> ARE` is the one dependency M10 exists to serve. A contract that
        forbade it in both directions would satisfy the test above while making
        the module useless, and nothing else would catch that.
        """
        contract = _by_name("no upstream module depends on the AI Research Engine")
        sources = contract["source_modules"]
        assert "modules.ai_reasoning_engine" not in sources, (  # type: ignore[operator]
            "The AI Reasoning Engine must remain free to consume a research artifact — "
            "05-module-dependencies.md ratifies ARE -> AIR as the pipeline's one "
            "deliberate non-blocking edge."
        )
        assert "modules.ai_platform" in sources  # type: ignore[operator]
        assert "modules.opportunity_engine" in sources  # type: ignore[operator]


class TestResearchStaysInternal:
    """The **Internal Research** ruling of 2026-07-31, made mechanical.

    M10 was ruled to explore, compare and synthesise knowledge Signora already
    owns, reaching no external source. That ruling is a product decision, and a
    product decision recorded only in a document is one a future task can
    contradict without noticing. These two tests make contradicting it fail.
    """

    def test_attested_knowledge_is_unconstructable(self) -> None:
        """External findings cannot arrive by setting a field.

        `EpistemicOrigin` deliberately omits ATTESTED — the origin of *"a named
        outside source asserts X"*. Adding external retrieval must therefore add
        the member, which is a visible diff on a file that records why it was
        absent, rather than a value quietly appearing in a column.
        """
        origins = {origin.value for origin in EpistemicOrigin}
        assert "attested" not in origins, (
            "ATTESTED became constructable. M10 was ruled Internal Research: findings are "
            "DERIVED from rows Signora owns. Admitting external assertions needs a product "
            "ruling on whether they may be cited at all — 31-m10-design-review-evidence.md §7.2."
        )
        assert origins == {"derived", "inferred"}

    def test_no_network_client_exists_except_to_hand_to_the_platform(self) -> None:
        """**Wider than the layering contract, and narrowed at T137.**

        `import-linter` forbids `httpx` in `domain/` — a Clean Architecture
        rule, and it would happily allow a browser tool in `infrastructure/`.
        The ruling is about the module as a whole.

        As first written this forbade a network client *anywhere*, justified by
        *"every model call goes through the AI Platform's adapters, which own
        the transport, so nothing here needs a client of its own."* **T137
        disproved that.** `build_provider_registry(settings, client=client)`
        takes a client: the platform owns the adapters, the composition root
        owns the client's lifetime, and M9's entry point does the same.

        So the rule is narrowed to what it always meant rather than exempting a
        directory. A client may exist **only in a file that hands it to the
        platform's registry** — which permits the one legitimate use and still
        refuses a client anyone could fetch with, including inside
        `evaluation/`.
        """
        clients = {"httpx", "requests", "urllib", "urllib3", "aiohttp", "socket", "webbrowser"}
        for source in MODULE_ROOT.rglob("*.py"):
            text = source.read_text(encoding="utf-8")
            tree = ast.parse(text)
            imported: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported |= {alias.name.split(".")[0] for alias in node.names}
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported |= {node.module.split(".")[0]}

            offending = imported & clients
            if not offending:
                continue
            assert "build_provider_registry" in text, (
                f"{source.relative_to(MODULE_ROOT)} imports {sorted(offending)} without handing "
                "it to the AI Platform's provider registry. The AI Research Engine researches "
                "what Signora already owns; a client it can fetch with is external retrieval "
                "arriving without the ruling that authorises it."
            )

    def test_no_client_exists_outside_the_composition_root(self) -> None:
        """The other half, so the narrowing above cannot be widened by moving a
        fetch next to a registry call. Retrieval, derivation and orchestration
        must import no client at all."""
        clients = {"httpx", "requests", "urllib", "urllib3", "aiohttp", "socket", "webbrowser"}
        for layer in ("domain", "application", "infrastructure", "public"):
            for source in (MODULE_ROOT / layer).rglob("*.py"):
                tree = ast.parse(source.read_text(encoding="utf-8"))
                for node in ast.walk(tree):
                    imported: set[str] = set()
                    if isinstance(node, ast.Import):
                        imported = {alias.name.split(".")[0] for alias in node.names}
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        imported = {node.module.split(".")[0]}
                    offending = imported & clients
                    assert not offending, (
                        f"{source.relative_to(MODULE_ROOT)} imports {sorted(offending)}. Only "
                        "the evaluation composition root may hold a client, and only to hand "
                        "to the provider registry."
                    )


class TestOneCitationResolvesToOneSentence:
    """Two modules assemble evidence from the same `OpportunityExplanation`.
    **Their citation kinds must never intersect.**

    M8's assembler emits `opportunity`, `buying_score` and
    `signal_contribution`. The AI Research Engine emits what that omits. If a
    kind appeared in both, one citation token would resolve to two different
    facts with two different summaries depending on which module assembled the
    set — and a customer checking a premise would have no way to know which one
    they were shown.

    Asserted here as well as in the module's own tests, deliberately: rewriting
    either module's retrieval must not be able to remove the guarantee.
    """

    def test_research_never_emits_a_kind_the_platform_already_emits(self) -> None:
        platform = {OPPORTUNITY, BUYING_SCORE, CONTRIBUTION}
        collisions = RESEARCH_FACT_KINDS & platform
        assert not collisions, (
            f"{sorted(collisions)} is emitted by both the AI Platform's assembler and the AI "
            "Research Engine. One citation would resolve to two different sentences."
        )

    def test_both_sides_of_the_rule_are_non_empty(self) -> None:
        """A disjointness assertion is satisfied by either side being empty,
        which would make it pass while proving nothing."""
        assert RESEARCH_FACT_KINDS
        assert {OPPORTUNITY, BUYING_SCORE, CONTRIBUTION}


class TestInferredKnowledgeIsUncitable:
    """Knowledge Contract Rule 12, enforced by absence rather than by a check."""

    def test_no_inferred_type_exposes_an_evidence_address(self) -> None:
        """A model's output must never become another model's evidence.

        The enforcement is that an INFERRED object has **no address** — no
        `ref`, no `token`, no `EvidenceRef` field — so a consumer cannot cite it
        even deliberately. This scans every INFERRED type the module defines, so
        a *future* one cannot quietly acquire one.
        """
        inferred = [
            obj
            for obj in vars(research).values()
            if isinstance(obj, type)
            and getattr(obj, "origin", None) is EpistemicOrigin.INFERRED
        ]
        assert inferred, "no INFERRED type found — this test would pass vacuously."
        for cls in inferred:
            for name in ("ref", "token", "evidence_ref"):
                assert not hasattr(cls, name), (
                    f"{cls.__name__} exposes '{name}'. It is INFERRED, and an addressable "
                    "inference is a citable one — Rule 12 forbids it under any configuration."
                )
            addresses = [
                field.name
                for field in fields(cls)
                if field.type in {"EvidenceRef", "EvidenceRef | None"}
            ]
            assert not addresses, (
                f"{cls.__name__} carries {addresses}, which addresses evidence. An INFERRED "
                "object may reference its inputs by identity; it may not become one."
            )

    def test_the_derived_finding_is_addressable(self) -> None:
        """The positive control. A rule enforced by absence is satisfied by an
        empty module, so something must be shown to *have* the address."""
        assert ResearchFinding.origin is EpistemicOrigin.DERIVED
        assert hasattr(ResearchFinding, "ref")

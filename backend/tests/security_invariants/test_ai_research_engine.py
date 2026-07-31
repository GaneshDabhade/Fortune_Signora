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

These tests read source and configuration. They never call a model, and they
never require the module to contain anything.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

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

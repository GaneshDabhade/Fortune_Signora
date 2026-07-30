"""Invariants: the module that concludes stays inside its boundary.

M9 is the first module in the pipeline that produces propositions its input
did not contain. Everything upstream derives, projects or restates; a defect
here is therefore the first one that cannot be caught by recomputing
something. That makes its structural boundaries worth asserting from the
first line of code rather than after the module has grown into them.

Three guarantees, each of which would be violated quietly:

**It reads through published contracts and nothing deeper.** Everything M9
needs about an opportunity, its score, its ledger and its signals arrives
through ``opportunity_engine.public``, which already carries the whole chain.
A direct reach into a deeper layer is a module rebuilding a view another
module already publishes — the M3A finding, which caught two real violations
in shipped code.

**Nothing upstream reads back.** Every stage before M9 is rebuildable
precisely because nothing downstream feeds it. An upstream module that
learned what was concluded about its own output would make the derivation
circular, and the pipeline would stop being replayable.

**The contracts stay registered.** import-linter enforces the above on every
run, from a config file a future change could edit. This module asserts the
rules are still *asked for* — deliberate overlap, per CLAUDE.md §11.

Structural by design: these read source and configuration and never call a
model. A guarantee that needs a GPU to verify is not a guarantee
(28-ai-platform.md, "the two-tier guarantee").
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
MODULE_ROOT = BACKEND_ROOT / "modules" / "ai_reasoning_engine"
PYPROJECT = BACKEND_ROOT / "pyproject.toml"

pytestmark = pytest.mark.security_invariant


def _contracts() -> list[dict[str, object]]:
    with PYPROJECT.open("rb") as handle:
        return list(tomllib.load(handle)["tool"]["importlinter"]["contracts"])


def _named(name: str) -> dict[str, object]:
    return next(c for c in _contracts() if c["name"] == name)


class TestTheBoundaryContractsStayRegistered:
    """A contract deleted from ``pyproject.toml`` produces a green run,
    because a rule that is not configured cannot be broken."""

    REQUIRED = (
        "ai_reasoning_engine reaches other modules only through public/",
        "no upstream module depends on the AI Reasoning Engine",
        "ai_reasoning_engine: domain has no infrastructure/framework dependencies",
    )

    @pytest.mark.parametrize("contract", REQUIRED)
    def test_contract_is_configured(self, contract: str) -> None:
        assert contract in {c["name"] for c in _contracts()}, (
            f"import-linter contract '{contract}' is missing. Deleting a contract makes the "
            "rule it expressed unenforceable while every run stays green."
        )

    def test_the_module_is_under_clean_architecture_enforcement(self) -> None:
        """The layering contract does not auto-discover modules, by design —
        so a module absent from its container list is silently unenforced."""
        layering = _named("modules: Clean Architecture layering")
        containers = layering["containers"]
        assert isinstance(containers, list)
        assert "modules.ai_reasoning_engine" in containers

    def test_every_pipeline_stage_is_named_as_forbidden_to_read_back(self) -> None:
        """The positive control on the reverse-dependency rule.

        A contract listing only *some* upstream modules would pass the
        registration check above while leaving the others free to import M9.
        Enumerated here so adding a pipeline module without adding it there is
        a failure rather than an omission.
        """
        contract = _named("no upstream module depends on the AI Reasoning Engine")
        sources = contract["source_modules"]
        assert isinstance(sources, list)

        upstream = {
            "modules.provider_platform",
            "modules.provider_normalization",
            "modules.knowledge_graph",
            "modules.observation_engine",
            "modules.business_event_engine",
            "modules.signal_engine",
            "modules.buying_score_engine",
            "modules.opportunity_engine",
            "modules.workspace_tenancy",
            "modules.ai_platform",
        }
        missing = upstream - set(sources)
        assert not missing, (
            f"these modules could import the AI Reasoning Engine without failing a contract: "
            f"{sorted(missing)}. Every stage M9 reads from must be forbidden from reading back, "
            "or the pipeline stops being replayable."
        )


class TestTheModuleIsScaffoldedUnderCleanArchitecture:
    def test_the_expected_layers_exist(self) -> None:
        for layer in ("domain", "application", "infrastructure", "public"):
            assert (MODULE_ROOT / layer).is_dir(), f"missing layer: {layer}"

    def test_interface_is_absent_until_it_has_a_caller(self) -> None:
        """``interface/`` is optional in the layering contract and is created
        when M9 gains its event handlers (T130). A directory made for a caller
        that does not exist is the speculative structure CLAUDE.md §6
        forbids — the same call M8 made and kept."""
        assert not (MODULE_ROOT / "interface").exists()

    def test_the_public_contract_exports_nothing_yet(self) -> None:
        """Scaffolded, not started. Asserted so that the first export is a
        deliberate act rather than something that appeared while the module
        was being wired."""
        from modules.ai_reasoning_engine import public

        assert public.__all__ == []

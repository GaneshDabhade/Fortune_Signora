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
#: The composition root, read as text: whether a router is *mounted* is a
#: structural fact, and importing the app to find out would need a database.
_MAIN = BACKEND_ROOT / "apps" / "api" / "main.py"

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

    def test_the_interface_exists_and_has_a_caller(self) -> None:
        """**This guard replaced one that had done its job.**

        It read ``assert not (MODULE_ROOT / "interface").exists()``, and its
        reason was that *"a directory made for a caller that does not exist is
        the speculative structure §6 forbids."* A-i gave it a caller — the
        router is mounted at the composition root — so the original condition
        can no longer occur, and **a guard that cannot fail is documentation
        pretending to be code** (§2).

        Replaced rather than deleted, and pointed at the property that is now
        the one at risk: the layer exists *and* something reaches it. A layer
        nobody mounted is the same speculative structure wearing the opposite
        coat.
        """
        assert (MODULE_ROOT / "interface").is_dir()
        assert "ai_reasoning_engine.interface.router" in _MAIN.read_text()

    def test_the_module_publishes_no_route_that_writes(self) -> None:
        """**The invariant the slice above actually needs.**

        Reaching a conclusion is a model call. §7 forbids an API handler
        blocking on pipeline work and Principle 13 puts it in a background
        worker — so a ``POST`` here would be the most tempting shortcut in the
        product and the most expensive one. It would also make M9 the agentic
        thing the M9/M10 split exists to keep it from becoming, which no import
        contract would notice.

        Asserted over the decorators rather than the mounted app: this suite is
        structural and must not need a database to answer (*"the two-tier
        guarantee"*).
        """
        source = (MODULE_ROOT / "interface" / "router.py").read_text()

        for verb in ("post", "put", "patch", "delete"):
            assert f"@router.{verb}(" not in source, verb
        assert "@router.get(" in source, "a router that serves nothing is not a surface"

    def test_the_public_contract_publishes_language_and_never_the_conclusion(self) -> None:
        """**Replaced rather than deleted, on the same grounds as the slice
        above** — and by the test's own terms.

        It read ``public.__all__ == []`` and said why: *"asserted so that the
        first export is a **deliberate act** rather than something that
        appeared while the module was being wired."* ⚡ **That is exactly what
        happened.** The first export is [TASK-453](../../../docs/BACKLOG.md),
        ruled onto this module by
        [D-112](../../../docs/DECISION_REGISTER.md) — *"the engine owns the
        language. Screens consume that language."* **The guard fired, a human
        ruled, and the condition it protected has been discharged.**

        ⛔ **The successor is strictly stronger, because "nothing" stops being
        assertable the moment anything is published.** What is now at risk is
        not *whether* the module exports, but *what*: this module holds the
        `DecisionPackage` aggregate, its evidence set and its grounding
        report, and **publishing any of them would put the conclusion itself
        on the contract** — where a consumer would render it instead of
        inspecting it, and where §5's *only via `public/`* would start
        carrying the domain rather than the language.

        **So: the two ruled types, and nothing that concludes, writes or
        ranks.**
        """
        from modules.ai_reasoning_engine import public

        assert public.__all__ == ["ReasoningVerb", "Surface"]

        published = {name for name in public.__all__}

        # The conclusion and its machinery stay inside the module. A consumer
        # asks in this language; it never receives the aggregate.
        forbidden = {
            "DecisionPackage",
            "EvidenceSet",
            "GroundedOutput",
            "GroundingReport",
            "SupportBasis",
            "SupportLevel",
            "ReasonedOutput",
        }
        assert not published & forbidden

        # Nothing here may write, rank, or decide. Same rule as every other
        # published reader in the platform.
        for name in published:
            exported = getattr(public, name)
            surface = {a for a in dir(exported) if not a.startswith("_")}
            assert not {a for a in surface if a.startswith(("save", "write", "create", "rank"))}

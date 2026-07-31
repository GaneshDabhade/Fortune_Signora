"""M9's evaluation command refuses to invent a result.

The same guarantee M8's harness carries, asserted separately because this is a
**different composition root** — M9 owns its own, since M8's cannot import
`ReasonedOutput` without breaking the reverse-dependency contract.

Rewritten 2026-07-30 alongside M8's, when the Ollama-specific reachability
probe was removed from both. The probe made a *hosted* evaluation depend on a
*local* runtime answering, which is precisely backwards for the run that earns
a release — and it was never what prevented a fake being substituted for a
model. Composition is: this file obtains its providers from
`build_provider_registry`, so no fake is reachable from it.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from modules.ai_reasoning_engine.evaluation.__main__ import main

ENTRY_POINT = (
    Path(__file__).resolve().parents[2]
    / "modules"
    / "ai_reasoning_engine"
    / "evaluation"
    / "__main__.py"
)


class TestItRefusesToMeasureWithoutAModel:
    async def test_a_model_no_provider_serves_produces_no_verdict(self, capsys: Any) -> None:
        exit_code = await main(["--model", "a-model-nothing-serves"])

        assert exit_code == 2
        printed = capsys.readouterr().err
        assert "UNMEASURABLE" in printed
        assert "a-model-nothing-serves" in printed, "the refusal must name the model it tried"
        assert "Registered:" in printed

    async def test_the_refusal_states_that_a_fake_is_never_substituted(self, capsys: Any) -> None:
        await main(["--model", "a-model-nothing-serves"])
        assert "will not substitute a fake" in capsys.readouterr().err

    async def test_the_refusal_names_no_vendor(self, capsys: Any) -> None:
        """The positive control. A message telling the engineer to start one
        vendor's runtime would satisfy both tests above while reintroducing
        exactly what was removed."""
        await main(["--model", "a-model-nothing-serves"])
        printed = capsys.readouterr().err.lower()
        for vendor in ("ollama", "anthropic", "claude", "openai", "gemini"):
            assert vendor not in printed, f"the UNMEASURABLE message names {vendor}"


class TestTheProviderIsResolvedRatherThanNamed:
    """`--model claude-sonnet-4-5` must be *configuration*, not a code path.

    Ruled 2026-07-30: the benchmark is unchanged by which provider executes it.
    A local runtime gives a developer feedback; the release that counts is
    earned against the hosted production model. Both go through one registry,
    keyed by model, and neither is special-cased anywhere in this module.
    """

    def test_the_entry_point_constructs_no_adapter_of_its_own(self) -> None:
        """**This is what stops a fake, and it is structural.** A file that
        may not name an adapter cannot name a scripted one either."""
        constructed = {
            node.func.id
            for node in ast.walk(ast.parse(ENTRY_POINT.read_text()))
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        assert not {name for name in constructed if name.endswith("Adapter")}

    def test_it_resolves_providers_through_the_platforms_own_registry(self) -> None:
        """Reused rather than reinvented. A second registration path in M9
        would be a parallel abstraction over a capability M8 already owns —
        and the two would disagree about which models exist."""
        assert "build_provider_registry" in ENTRY_POINT.read_text()

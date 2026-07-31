"""M10's evaluation composition root, and the properties it must keep.

**Nothing here calls a model.** These assert the *composition* — that the entry
point resolves a provider through the AI Platform's registry rather than
constructing one, that it names no vendor, and that a run which cannot execute
faithfully produces no verdict rather than a verdict from the cases that
happened to survive.

The same shape as M9's, deliberately. Two evaluation entry points disagreeing
about what an unmeasurable run looks like would make the two milestones'
results incomparable.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest

from modules.ai_research_engine.evaluation.__main__ import (
    DATASET,
    DATASET_DIR,
    PROMPT,
    PROMPT_DIR,
    main,
)

ENTRY_POINT = Path(__file__).resolve().parents[2] / "modules/ai_research_engine/evaluation/__main__.py"


@pytest.mark.asyncio
class TestARunThatCannotExecuteProducesNoVerdict:
    async def test_a_model_no_provider_serves_is_unmeasurable(self, capsys: Any) -> None:
        """Not a failing score. A model nothing serves was never measured, and
        reporting zero would put a fabricated observation in the record."""
        exit_code = await main(["--model", "a-model-nothing-serves"])

        assert exit_code == 2
        assert "UNMEASURABLE" in capsys.readouterr().err

    async def test_the_refusal_names_no_vendor(self, capsys: Any) -> None:
        """Failure attribution must be truthful: a request refused before
        provider resolution has no vendor to name."""
        await main(["--model", "a-model-nothing-serves"])

        err = capsys.readouterr().err.lower()
        assert "anthropic" not in err
        assert "ollama" not in err


class TestTheCompositionRootComposesRatherThanBuilds:
    def test_it_constructs_no_adapter_of_its_own(self) -> None:
        """An entry point that instantiated an adapter would be choosing a
        vendor — the decision `for_model` exists to take."""
        source = ENTRY_POINT.read_text(encoding="utf-8")
        for adapter in ("OllamaAdapter", "AnthropicAdapter", "Adapter("):
            assert adapter not in source, f"{adapter} is constructed in the composition root"

    def test_it_resolves_providers_through_the_platforms_own_registry(self) -> None:
        assert "build_provider_registry" in ENTRY_POINT.read_text(encoding="utf-8")

    def test_it_names_no_vendor_in_executable_code(self) -> None:
        """Prose may explain vendor neutrality; code may not depend on it."""
        tree = ast.parse(ENTRY_POINT.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                lowered = node.value.lower()
                assert "anthropic" not in lowered
                assert "claude-" not in lowered


class TestItEvaluatesTheModulesOwnArtifacts:
    def test_the_prompt_and_dataset_are_this_modules(self) -> None:
        assert PROMPT == "research_planning"
        assert DATASET == "research_planning"
        assert PROMPT_DIR.name == "prompts"
        assert PROMPT_DIR.parent.name == "ai_research_engine"

    def test_the_dataset_lives_in_this_module(self) -> None:
        """**M10 owns its dataset for a mechanical reason.** The derivation
        catalog consumes `business_event` and `dissenting_signal`; M8's golden
        set holds neither, so every step a planner produced against it would be
        refused at construction and the run would measure the dataset."""
        assert DATASET_DIR.parent.parent.name == "ai_research_engine"
        assert (DATASET_DIR / f"{DATASET}@1.json").is_file()

    def test_the_prompt_file_matches_its_recorded_fingerprint(self) -> None:
        """The loader refuses a mismatch; this states the guarantee where a
        reader looks for it. A released prompt is never edited in place."""
        from modules.ai_platform.infrastructure.prompt_loader import load_prompt_registry

        registry = load_prompt_registry(PROMPT_DIR)
        assert registry.get(PROMPT, 1).version == 1


class TestTheDatasetMatchesWhatThePlannerCanUse:
    def test_every_fact_is_a_kind_a_derivation_reads(self) -> None:
        """A dataset containing a kind no derivation consumes would measure a
        planner's ability to produce steps its own schema refuses."""
        from modules.ai_platform.evaluation.dataset import load_dataset
        from modules.ai_research_engine.domain.retrieval import RESEARCH_FACT_KINDS

        dataset = load_dataset(DATASET, 1, directory=DATASET_DIR)
        for case in dataset.cases:
            kinds = {fact.ref.kind for fact in case.evidence}
            assert kinds <= RESEARCH_FACT_KINDS, f"{case.name} holds {kinds - RESEARCH_FACT_KINDS}"

    def test_every_load_bearing_fact_is_in_its_case(self) -> None:
        from modules.ai_platform.evaluation.dataset import load_dataset

        dataset = load_dataset(DATASET, 1, directory=DATASET_DIR)
        for case in dataset.cases:
            present = {fact.ref.token for fact in case.evidence}
            assert set(case.load_bearing) <= present

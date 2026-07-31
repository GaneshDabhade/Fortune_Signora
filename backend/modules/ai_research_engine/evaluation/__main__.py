"""`make eval-research` — the composition root for an M10 planning evaluation.

**M10 owns this rather than extending M8's**, for the reason M9's entry point
gives: `ai_platform/evaluation/__main__.py` would have to import
`ResearchPlan`, and *"no upstream module depends on the AI Research Engine"*
stops it. Everything reusable is reused unchanged — the harness, the dataset
loader, the rubric, the release recorder, the UNMEASURABLE renderer. Only the
three things that are M10's are named: its prompt, its output type, its
directories.

**This file is the single narrow exception to M10's through-`public` contract.**
The exemption was deliberately *not* added at T131, because nothing under
`evaluation/` imported anything yet and an exemption for an import that does not
exist is a declared hole guarding nothing. It is added now, by the task that
writes the import.

**The provider is resolved, never named.** `build_provider_registry` registers
every adapter whose credentials are present; `for_model` answers who serves the
model this run asked for. There is no vendor branch here and no way to write
one.

**The dataset is M10's own**, and that is mechanical rather than aesthetic. M8's
golden set holds `opportunity`, `buying_score` and `signal_contribution` facts;
the derivation catalog consumes `business_event` and `dissenting_signal` and
nothing else. Evaluated against M8's set, every step the planner could produce
would be refused at construction — the run would measure the dataset's shape
rather than the prompt.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

import httpx

from modules.ai_platform.evaluation.dataset import load_dataset
from modules.ai_platform.evaluation.harness import Harness
from modules.ai_platform.evaluation.release import record
from modules.ai_platform.evaluation.report import unmeasurable
from modules.ai_platform.evaluation.run_log import RunLog
from modules.ai_platform.infrastructure.composition import build_provider_registry
from modules.ai_platform.infrastructure.prompt_loader import load_prompt_registry
from modules.ai_platform.infrastructure.settings import AISettings
from modules.ai_platform.public import AIPlatformError, GroundedOutput, Infer, InferencePolicy
from modules.ai_research_engine.domain.plan import ResearchPlan
from modules.ai_research_engine.domain.synthesis import SynthesisedResearch

MODULE_ROOT = Path(__file__).resolve().parent.parent
PROMPT_DIR = MODULE_ROOT / "prompts"
DATASET_DIR = MODULE_ROOT / "evaluation" / "datasets"
#: The two prompts M10 ships. Named as a pair so `--prompt` selects one and its
#: dataset together — a prompt evaluated against the other's dataset would
#: measure the dataset's shape rather than the prompt.
PROMPTS = ("research_planning", "research_synthesis")
PROMPT = PROMPTS[0]
DATASET = PROMPTS[0]


async def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="make eval-research")
    parser.add_argument("--prompt-version", type=int, default=1)
    parser.add_argument("--dataset-version", type=int, default=1)
    parser.add_argument(
        "--model",
        default=None,
        help="the model to evaluate. Defaults to the development runtime's configured "
        "model; pass any model this environment has registered a provider for.",
    )
    parser.add_argument(
        "--prompt",
        default=PROMPTS[0],
        choices=PROMPTS,
        help="which of M10's prompts to evaluate. Each is measured against its own dataset.",
    )
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args(argv)

    settings = AISettings()
    model = args.model or settings.ollama_model
    prompt = args.prompt
    output_type: type[GroundedOutput] = (
        ResearchPlan if prompt == PROMPTS[0] else SynthesisedResearch
    )

    async with httpx.AsyncClient() as client:
        providers = build_provider_registry(settings, client=client)
        prompts = load_prompt_registry(PROMPT_DIR)
        run_log = RunLog()
        harness = Harness(
            infer=Infer(
                providers=providers, prompts=prompts, recorder=run_log, policy=InferencePolicy()
            ),
            prompts=prompts,
            run_log=run_log,
        )

        try:
            report = await harness.evaluate(
                prompt_name=prompt,
                prompt_version=args.prompt_version,
                model=model,
                dataset=load_dataset(prompt, args.dataset_version, directory=DATASET_DIR),
                output_type=output_type,
            )
        except AIPlatformError as exc:
            print(unmeasurable(model, exc), file=sys.stderr)
            return 2

    print(report.render())
    if args.record:
        record(report, manifest=PROMPT_DIR / "manifest.json")
        print("\nrecorded in the prompt manifest.")
    return 0 if report.as_evaluation().passed else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

"""`make eval-reasoning` — the composition root for an M9 evaluation run.

**M9 owns this rather than extending M8's**, because the contracts already
forbid the alternative: `ai_platform/evaluation/__main__.py` would have to
import `ReasonedOutput`, and *"no upstream module depends on the AI Reasoning
Engine"* stops it. Everything reusable is reused unchanged — the harness, the
dataset loader, the rubric, the release recorder. Only the three things that
are M9's are named here: its prompt, its output type, its registry.

**This file is the single narrow exception to M9's through-`public` contract**
(ruled 2026-07-30, recorded in `pyproject.toml`). Wiring an adapter, a
registry and a harness is what a composition root is *for*. Nothing else
under `ai_reasoning_engine` may reach past another module's `public/`.

The evidence is **M2.0's baseline pipeline output** — the same recorded golden
set M8 evaluates against, because reasoning and narration operate over the
identical closed evidence set and a second copy would be a second thing to
keep in step.
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
from modules.ai_platform.evaluation.run_log import RunLog
from modules.ai_platform.infrastructure.adapters.ollama import OllamaAdapter
from modules.ai_platform.infrastructure.prompt_loader import load_prompt_registry
from modules.ai_platform.infrastructure.settings import AISettings
from modules.ai_platform.public import AIPlatformError, AIProviderRegistry, Infer, InferencePolicy
from modules.ai_reasoning_engine.domain.decision import ReasonedOutput

PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"
PROMPT = "reasoning"
#: Named for the prompt that first seeded it. See the T128 note in
#: 29-ai-reasoning-engine.md on why it is not renamed: the name is recorded
#: in a released evaluation, and a record of what was true then is not
#: rewritten to match now.
DATASET = "explanation_narration"


async def _reachable(client: httpx.AsyncClient, base_url: str) -> bool:
    try:
        response = await client.get(f"{base_url.rstrip('/')}/api/tags", timeout=5.0)
    except httpx.HTTPError:
        return False
    return response.status_code == httpx.codes.OK


async def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="make eval-reasoning")
    parser.add_argument("--prompt-version", type=int, default=1)
    parser.add_argument("--dataset-version", type=int, default=1)
    parser.add_argument("--model", default=None)
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args(argv)

    settings = AISettings()
    model = args.model or settings.ollama_model

    async with httpx.AsyncClient() as client:
        if not await _reachable(client, settings.ollama_base_url):
            print(
                f"No model runtime at {settings.ollama_base_url}.\n\n"
                "This command measures a real model and will not substitute a fake for one.\n"
                "Start the rootless runtime with `~/.local/bin/ollama serve`, or point\n"
                "SIGNORA_OLLAMA_BASE_URL at a running one.",
                file=sys.stderr,
            )
            return 2

        providers = AIProviderRegistry()
        providers.register(
            OllamaAdapter(
                client=client, models=frozenset({model}), base_url=settings.ollama_base_url
            )
        )
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
                prompt_name=PROMPT,
                prompt_version=args.prompt_version,
                model=model,
                dataset=load_dataset(DATASET, args.dataset_version),
                output_type=ReasonedOutput,
            )
        except AIPlatformError as exc:
            # UNMEASURABLE — a third state, distinct from EARNED and REFUSED.
            # The run could not execute faithfully, so it produced no verdict
            # rather than a verdict from the cases that happened to survive.
            print(f"UNMEASURABLE — evaluation abandoned: {exc}", file=sys.stderr)
            return 2

    print(report.render())
    if args.record:
        record(report, manifest=PROMPT_DIR / "manifest.json")
        print("\nrecorded in the prompt manifest.")
    return 0 if report.as_evaluation().passed else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

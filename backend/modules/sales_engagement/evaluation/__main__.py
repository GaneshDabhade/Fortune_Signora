"""`make eval-approach` — the composition root for a Sales Engagement evaluation.

**This module owns this rather than extending the AI Platform's**, for the same
reason M9 and M10 own theirs: the platform's entry point would have to import
this module's `Pass`, its context protocol and its dataset shape, and *no
upstream module depends on a downstream one*. Everything genuinely reusable is
reused unchanged — the provider registry, the prompt loader, the settings.

**This file is the single narrow exception to this module's through-`public`
contract.** Wiring a registry and a harness is what a composition root is *for*;
nothing else under `sales_engagement` may reach past another module's `public/`.

**The provider is resolved, never named.** `build_provider_registry` registers
every adapter whose credentials are present, and `for_model` answers who serves
the model this run asked for. So `--model claude-sonnet-4-5` against a configured
key is *configuration* — there is no vendor branch here, and deliberately no way
to write one.

> **This command requires a real model and will not substitute a fake.** A
> scripted adapter never invents a competitor unless it is told to, so a run
> against one would prove the fence works and nothing about the model.
"""

from __future__ import annotations

import argparse
import asyncio
import sys

import httpx

from modules.ai_platform.infrastructure.composition import build_provider_registry
from modules.ai_platform.infrastructure.settings import AISettings
from modules.ai_platform.public import AIPlatformError
from modules.sales_engagement.application.synthesise import Synthesise
from modules.sales_engagement.domain.brief import Pass
from modules.sales_engagement.domain.release import earns_release
from modules.sales_engagement.evaluation.dataset import load_dataset
from modules.sales_engagement.evaluation.harness import Harness
from modules.sales_engagement.evaluation.release import record
from modules.sales_engagement.evaluation.report import unmeasurable
from modules.sales_engagement.infrastructure.model import ProviderSynthesisModel
from modules.sales_engagement.infrastructure.prompts import MANIFEST, prompts

DATASET = "approach"


async def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="make eval-approach")
    parser.add_argument(
        "--pass",
        dest="pass_",
        default=Pass.EXECUTIVE_SUMMARY.value,
        choices=[one.value for one in Pass],
        help="which synthesis pass to evaluate. A pass with no artifact on disk is refused "
        "by the registry rather than silently skipped.",
    )
    parser.add_argument("--prompt-version", type=int, default=1)
    parser.add_argument("--dataset-version", type=int, default=1)
    parser.add_argument(
        "--model",
        default=None,
        help="the model to evaluate. Defaults to the development runtime's configured model; "
        "pass any model this environment has registered a provider for.",
    )
    parser.add_argument(
        "--runs-per-case",
        type=int,
        default=2,
        help="attempts per case. Two by default, because stability across identical closed "
        "sets is the dimension this architecture can guarantee most cheaply.",
    )
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args(argv)

    settings = AISettings()
    model = args.model or settings.ollama_model

    async with httpx.AsyncClient() as client:
        registry = prompts()
        harness = Harness(
            synthesise=Synthesise(
                prompts=registry,
                model=ProviderSynthesisModel(build_provider_registry(settings, client=client)),
                model_name=model,
            ),
            prompts=registry,
        )

        try:
            report = await harness.evaluate(
                pass_=Pass(args.pass_),
                version=args.prompt_version,
                model=model,
                dataset=load_dataset(DATASET, args.dataset_version),
                runs_per_case=args.runs_per_case,
            )
        except AIPlatformError as exc:
            print(unmeasurable(model, exc), file=sys.stderr)
            return 2

    print(report.render())
    if args.record:
        record(report, manifest=MANIFEST)
        print("\nrecorded in the prompt manifest.")
    return 0 if earns_release(report.as_evaluation()) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

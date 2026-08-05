"""``make eval`` — the composition root for an evaluation run.

The one entry point in Signora that requires a real model, and the only place
that is true. `make test` never reaches this file, no Security Invariant does,
and nothing here is importable from a test that expects to run offline.

**It refuses to produce a result it cannot stand behind.** A run that cannot
execute faithfully reports UNMEASURABLE and no verdict — it does not skip,
does not warn-and-continue, and above all does not fall back to a fake. That
last guarantee is provided by *composition*, not by a check: the only adapters
this file can register are the real ones `build_provider_registry` knows about,
so there is no fake for it to reach.

**The provider is resolved, never named** (ruled 2026-07-30). This file passes
`AISettings` to the AI Platform's own registry builder and asks for a *model*;
which vendor serves it is that module's business. Evaluating against a local
runtime today and a hosted model tomorrow is `--model` plus the credentials in
the environment — no code change, no vendor branch, and adding OpenAI or Gemini
later is an adapter registration rather than an edit here.

**Removed 2026-07-30: an Ollama-specific reachability probe.** It hit
`/api/tags` before every run, which gated a *hosted* evaluation on a *local*
runtime being up, and put vendor-specific logic in the one framework that must
have none. It was also never the thing enforcing "no fake" — composition is —
so what it actually contributed was a nicer message for one vendor's outage.
That fact is discovered by the transport already, and reporting it twice is two
representations of one truth. A run against an unreachable provider now
abandons and reports UNMEASURABLE, which is the correct answer and was always
the correct answer.
"""

from __future__ import annotations

import argparse
import asyncio
import sys

import httpx

from modules.ai_platform.application.infer import Infer, InferencePolicy
from modules.ai_platform.domain.errors import AIPlatformError
from modules.ai_platform.domain.narration import Narration
from modules.ai_platform.evaluation.dataset import load_dataset
from modules.ai_platform.evaluation.harness import Harness
from modules.ai_platform.evaluation.release import record
from modules.ai_platform.evaluation.report import unmeasurable
from modules.ai_platform.evaluation.run_log import RunLog
from modules.ai_platform.infrastructure.composition import build_provider_registry
from modules.ai_platform.infrastructure.prompt_loader import load_prompt_registry
from modules.ai_platform.infrastructure.settings import AISettings

#: What `make eval` runs when given no arguments: the prompt M8 ships, over
#: the golden set seeded from the M2.0 baseline scenario.
DEFAULT_PROMPT = "explanation_narration"
DEFAULT_DATASET = "explanation_narration"


async def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="make eval",
        description="Evaluate a prompt against a model over a golden dataset.",
    )
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--prompt-version", type=int, default=1)
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--dataset-version", type=int, default=1)
    parser.add_argument(
        "--model",
        default=None,
        help="the model to evaluate. Defaults to the development runtime's configured "
        "model; pass any model this environment has registered a provider for.",
    )
    parser.add_argument(
        "--record",
        action="store_true",
        help="append the measurement to the prompt manifest. Without this the run reports and "
        "records nothing, which is what you want while iterating on a prompt.",
    )
    args = parser.parse_args(argv)

    settings = AISettings()
    #: Development is the local runtime (ADR-0028), so that is the default a
    #: developer gets. It is a *default*, not a coupling: the registry resolves
    #: whatever `--model` names, and release is earned against the hosted one.
    model = args.model or settings.ollama_model

    async with httpx.AsyncClient() as client:
        # One registry, built by the module that owns vendors. Nothing here
        # constructs an adapter.
        #
        # **It used to say "so nothing here can construct a fake", and that
        # stopped being true at TASK-415** (B-324): the deterministic mock is
        # now the local development default, and this registry will serve it.
        # A comment asserting a guarantee the code no longer makes is the
        # false claim §2 forbids, so the guarantee moved to where it can be
        # enforced instead — `record()` refuses a mock-served run.
        providers = build_provider_registry(settings, client=client)

        # One prompt registry in two roles, and one `RunLog` in two: the
        # `InferenceRecorder` port `Infer` writes every outcome to, and the
        # record the harness reads back so a run can report its own retries.
        prompts = load_prompt_registry()
        run_log = RunLog()
        harness = Harness(
            infer=Infer(
                providers=providers,
                prompts=prompts,
                recorder=run_log,
                policy=InferencePolicy(),
            ),
            prompts=prompts,
            run_log=run_log,
        )

        try:
            report = await harness.evaluate(
                prompt_name=args.prompt,
                prompt_version=args.prompt_version,
                model=model,
                dataset=load_dataset(args.dataset, args.dataset_version),
                output_type=Narration,
            )
        except AIPlatformError as exc:
            print(unmeasurable(model, exc), file=sys.stderr)
            return 2

    print(report.render())

    evaluation = report.as_evaluation()
    if args.record:
        record(report)
        print("\nrecorded in the prompt manifest.")

    return 0 if evaluation.passed else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

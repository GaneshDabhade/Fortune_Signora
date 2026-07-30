"""``make eval`` — the composition root for an evaluation run.

The one entry point in Signora that requires a real model, and the only place
that is true. `make test` never reaches this file, no Security Invariant does,
and nothing here is importable from a test that expects to run offline.

**It refuses to produce a result it cannot stand behind.** If no model
runtime is reachable it fails, loudly, naming what is missing — it does not
skip, does not warn-and-continue, and above all does not fall back to a fake.
A harness satisfied by a scripted adapter would measure the scripted adapter:
a fake never invents a quantity unless it is told to, so grounding against one
proves the checker works and nothing whatsoever about the model.

Composition happens here and only here (CLAUDE.md §6): `AISettings` is
constructed, the adapter is built from it, the registry is assembled, and
`Infer` is wired. Nothing below this file knows a vendor exists.
"""

from __future__ import annotations

import argparse
import asyncio
import sys

import httpx

from modules.ai_platform.application.infer import Infer, InferencePolicy
from modules.ai_platform.domain.errors import AIPlatformError
from modules.ai_platform.domain.narration import Narration
from modules.ai_platform.domain.provider import AIProviderRegistry
from modules.ai_platform.domain.record import InferenceRecord
from modules.ai_platform.evaluation.dataset import load_dataset
from modules.ai_platform.evaluation.harness import Harness
from modules.ai_platform.evaluation.release import record
from modules.ai_platform.infrastructure.adapters.ollama import OllamaAdapter
from modules.ai_platform.infrastructure.prompt_loader import load_prompt_registry
from modules.ai_platform.infrastructure.settings import AISettings

#: What `make eval` runs when given no arguments: the prompt M8 ships, over
#: the golden set seeded from the M2.0 baseline scenario.
DEFAULT_PROMPT = "explanation_narration"
DEFAULT_DATASET = "explanation_narration"


class _StdoutRecorder:
    """Satisfies ``InferenceRecorder`` without a database.

    An evaluation is not production traffic: it is a measurement of a prompt,
    run from a developer's terminal, and writing its rows into `ai_inference`
    would put synthetic calls into the same table the ungrounded *production*
    rate is read from. The two must stay distinguishable, and the cheapest way
    to guarantee that is for the harness never to reach the table at all.
    """

    def __init__(self) -> None:
        self.written: list[InferenceRecord] = []

    async def record(self, record: InferenceRecord) -> None:
        self.written.append(record)


async def _reachable(client: httpx.AsyncClient, base_url: str) -> bool:
    try:
        response = await client.get(f"{base_url.rstrip('/')}/api/tags", timeout=5.0)
    except httpx.HTTPError:
        return False
    return response.status_code == httpx.codes.OK


async def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="make eval",
        description="Evaluate a prompt against a model over a golden dataset.",
    )
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--prompt-version", type=int, default=1)
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--dataset-version", type=int, default=1)
    parser.add_argument("--model", default=None, help="defaults to the configured Ollama model")
    parser.add_argument(
        "--record",
        action="store_true",
        help="append the measurement to the prompt manifest. Without this the run reports and "
        "records nothing, which is what you want while iterating on a prompt.",
    )
    args = parser.parse_args(argv)

    settings = AISettings()
    model = args.model or settings.ollama_model

    async with httpx.AsyncClient() as client:
        if not await _reachable(client, settings.ollama_base_url):
            print(
                f"No model runtime at {settings.ollama_base_url}.\n"
                "\n"
                "`make eval` measures a real model and will not substitute a fake for one:\n"
                "a scripted adapter never invents a quantity unless it is told to, so a run\n"
                "against one would prove the grounding checker works and nothing about the\n"
                "model. Every other gate in this repository is offline by design; this one\n"
                "is the exception, deliberately (ADR-0028, 28-ai-platform.md).\n"
                "\n"
                "Install Ollama and pull the configured model:\n"
                "    curl -fsSL https://ollama.com/install.sh | sh\n"
                f"    ollama pull {model}\n"
                "\n"
                "That installer needs root. Without sudo, extract the release tarball\n"
                "into ~/.local and run the server as your own user instead — it needs no\n"
                "privileges and is removed by deleting the directory:\n"
                "    https://github.com/ollama/ollama/releases  (ollama-linux-amd64.tar.zst)\n"
                "    ~/.local/bin/ollama serve\n"
                "\n"
                "Or point SIGNORA_OLLAMA_BASE_URL at a running one.",
                file=sys.stderr,
            )
            return 2

        adapter = OllamaAdapter(
            client=client,
            models=frozenset({model}),
            base_url=settings.ollama_base_url,
        )
        providers = AIProviderRegistry()
        providers.register(adapter)

        harness = Harness(
            infer=Infer(
                providers=providers,
                prompts=load_prompt_registry(),
                recorder=_StdoutRecorder(),
                policy=InferencePolicy(),
            ),
            prompts=load_prompt_registry(),
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
            print(f"evaluation abandoned: {exc}", file=sys.stderr)
            return 2

    print(report.render())

    evaluation = report.as_evaluation()
    if args.record:
        record(report)
        print("\nrecorded in the prompt manifest.")

    return 0 if evaluation.passed else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

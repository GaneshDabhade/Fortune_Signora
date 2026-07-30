"""Run a prompt against a model over a golden dataset.

The harness composes capabilities that already exist rather than inventing
any: the prompt registry resolves the artifact, `Infer` renders and calls and
grounds and records, the rubric measures, the domain judges. It adds one
thing — **iteration over recorded expectations** — and nothing else.

Three properties it must not lose:

**It is the one place in Signora that requires a real model.** No test suite
does, no Security Invariant does, and `make test` never reaches this file. A
harness that could be satisfied by a fake would measure the fake: a scripted
adapter never invents a quantity unless it is told to, so grounding against
one proves the checker works and nothing about the model.

**It knows no vendor.** It names a *model*; who serves it is the registry's
business. Evaluating against Ollama today and Claude tomorrow changes a
composition argument and nothing here (AC-71).

**A run that did not complete produces no record.** A transport failure
invalidates a run rather than lowering its score, because a vendor being
down says nothing about a prompt — and a partial average silently reported
as a result is how a release gets granted on the cases that happened to
succeed.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from uuid import UUID

from modules.ai_platform.application.infer import Infer, InferenceInput
from modules.ai_platform.domain.errors import AIPlatformError
from modules.ai_platform.domain.grounding import (
    GroundedOutput,
    SchemaViolationError,
    UngroundedOutputError,
)
from modules.ai_platform.domain.prompt import PromptRegistry
from modules.ai_platform.domain.provider import AIProviderError, AITransientError
from modules.ai_platform.domain.record import InferenceOutcome
from modules.ai_platform.evaluation.dataset import GoldenCase, GoldenDataset
from modules.ai_platform.evaluation.report import CaseResult, EvaluationReport
from modules.ai_platform.evaluation.rubric import RUBRIC_VERSION, coverage


class EvaluationAbandonedError(AIPlatformError):
    """The run could not be completed, so it produced no measurement.

    Distinct from a failing run. A failing run is a result — the prompt is
    not releasable for this model. This is the *absence* of a result, and
    conflating the two would let an outage read as a quality regression.
    """


class Harness:
    """Evaluates one prompt against one model over one dataset."""

    def __init__(
        self,
        *,
        infer: Infer,
        prompts: PromptRegistry,
        today: Callable[[], date] = date.today,
    ) -> None:
        self._infer = infer
        self._prompts = prompts
        # Injected so a report's date is a fact about the run rather than
        # about when the test happened to execute.
        self._today = today

    async def evaluate[T: GroundedOutput](
        self,
        *,
        prompt_name: str,
        prompt_version: int,
        model: str,
        dataset: GoldenDataset,
        output_type: type[T],
    ) -> EvaluationReport:
        prompt = self._prompts.get(prompt_name, prompt_version)

        results = [
            await self._case(
                case,
                prompt_name=prompt_name,
                prompt_version=prompt_version,
                model=model,
                output_type=output_type,
            )
            for case in dataset.cases
        ]

        report = EvaluationReport(
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            prompt_fingerprint=prompt.fingerprint,
            model=model,
            dataset_name=dataset.name,
            dataset_version=dataset.version,
            dataset_fingerprint=dataset.fingerprint,
            rubric_version=RUBRIC_VERSION,
            evaluated_on=self._today(),
            results=tuple(results),
        )

        if report.transport_failures:
            raise EvaluationAbandonedError(
                f"{report.transport_failures} of {report.sample_size} cases never reached a "
                "verdict, so this run measured nothing about the prompt. Fix the provider and "
                "run again — a partial average recorded as a result would grant a release on "
                "the cases that happened to succeed."
            )
        return report

    async def _case[T: GroundedOutput](
        self,
        case: GoldenCase,
        *,
        prompt_name: str,
        prompt_version: int,
        model: str,
        output_type: type[T],
    ) -> CaseResult:
        request = InferenceInput(
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            model=model,
            evidence=case.evidence,
            # Derived from the evidence digest, so the same case in the same
            # dataset always traces under the same id and two runs can be
            # diffed row by row. An evaluation is exactly where "which of the
            # twelve calls was that?" must not be answered by reading
            # timestamps.
            correlation_id=UUID(hex=case.evidence.digest[:32]),
        )

        try:
            # `measure`, not `execute`: this run is what earns the release
            # the rule enforces. See Infer.measure — the exception is named
            # and invariant-enforced rather than a flag.
            result = await self._infer.measure(request, output_type)
        except UngroundedOutputError as exc:
            return CaseResult(case.name, InferenceOutcome.UNGROUNDED, 0.0, str(exc))
        except SchemaViolationError as exc:
            return CaseResult(case.name, InferenceOutcome.SCHEMA_INVALID, 0.0, str(exc))
        except AIProviderError as exc:
            outcome = (
                InferenceOutcome.TRANSIENT
                if isinstance(exc, AITransientError)
                else InferenceOutcome.PERMANENT
            )
            return CaseResult(case.name, outcome, 0.0, str(exc))

        return CaseResult(
            case.name,
            InferenceOutcome.OK,
            coverage(result.output, case.load_bearing),
        )

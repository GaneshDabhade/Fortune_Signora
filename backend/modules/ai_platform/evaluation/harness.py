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
from modules.ai_platform.evaluation.run_log import RunLog


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
        run_log: RunLog,
        today: Callable[[], date] = date.today,
    ) -> None:
        self._infer = infer
        self._prompts = prompts
        # The same object `infer` writes its records to. The harness reads it
        # back so a run can report its own retries without anyone consulting
        # the vendor's server log.
        self._run_log = run_log
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
            # Read back from what actually answered, never passed in: the
            # adapter that served the call is the only component that knows.
            provider=self._run_log.provider(),
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
        correlation_id = UUID(hex=case.evidence.digest[:32])
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
            correlation_id=correlation_id,
        )

        try:
            # `measure`, not `execute`: this run is what earns the release
            # the rule enforces. See Infer.measure — the exception is named
            # and invariant-enforced rather than a flag.
            result = await self._infer.measure(request, output_type)
        except UngroundedOutputError as exc:
            return self._failed(case, InferenceOutcome.UNGROUNDED, exc, correlation_id)
        except SchemaViolationError as exc:
            return self._failed(case, InferenceOutcome.SCHEMA_INVALID, exc, correlation_id)
        except AIProviderError as exc:
            outcome = (
                InferenceOutcome.TRANSIENT
                if isinstance(exc, AITransientError)
                else InferenceOutcome.PERMANENT
            )
            return self._failed(case, outcome, exc, correlation_id)

        return CaseResult(
            case=case.name,
            outcome=InferenceOutcome.OK,
            coverage=coverage(result.output, case.load_bearing),
            # From the record rather than from a counter here: `Infer` owns
            # the retry policy, so `Infer`'s record is the authority on how
            # many times it acted.
            retries=result.record.usage.retries,
        )

    def _failed(
        self,
        case: GoldenCase,
        outcome: InferenceOutcome,
        error: Exception,
        correlation_id: UUID,
    ) -> CaseResult:
        """A failed case reports its retries too.

        Especially a failed one: a case that failed after three attempts and
        one that failed on the first are different operational facts, and the
        distinction is invisible in the failure message.
        """
        return CaseResult(
            case=case.name,
            outcome=outcome,
            coverage=0.0,
            retries=self._run_log.retries_for(correlation_id),
            detail=str(error),
        )

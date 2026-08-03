"""Run one synthesis prompt against one model over one set of golden graphs.

The harness composes capabilities that already exist rather than inventing any:
the prompt registry resolves the artifact, `Synthesise` renders and calls and
parses and fences, the rubric measures, `domain/release` judges. It adds one
thing — **iteration over recorded expectations** — and nothing else.

Three properties it must not lose:

**It is the one place in this module that requires a real model.** No test suite
does, no Security Invariant does, and `make test` never reaches this file. A
harness that could be satisfied by a fake would measure the fake: a scripted
adapter never invents a competitor unless it is told to, so fencing against one
proves the fence works and nothing about the model.

**It knows no vendor.** It names a *model*; who serves it is the registry's
business. Evaluating against Ollama today and a hosted model tomorrow changes a
composition argument and nothing here.

**A run that did not complete produces no record.** A transport failure
invalidates a run rather than lowering its score, because a vendor being down
says nothing about a prompt — and a partial average silently reported as a
result is how a release gets granted on the cases that happened to succeed.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Final
from uuid import UUID, uuid5

from modules.ai_platform.public import AIPlatformError, PromptRegistry
from modules.sales_engagement.application.approach import Approach
from modules.sales_engagement.application.synthesise import PassOutcome, PassResult, Synthesise
from modules.sales_engagement.domain.brief import Pass
from modules.sales_engagement.evaluation.dataset import GoldenCase, GoldenDataset
from modules.sales_engagement.evaluation.report import CaseResult, EvaluationReport
from modules.sales_engagement.evaluation.rubric import RUBRIC_VERSION, coverage, stability

#: Namespace for deriving a case's correlation id from its name.
#:
#: **Derived rather than random**, so the same case always traces under the same
#: id and two runs can be diffed row by row. An evaluation is exactly where
#: *"which of the twelve calls was that?"* must not be answered by reading
#: timestamps.
_CORRELATION_NAMESPACE: Final = UUID("6f1d5f3a-1c2b-4b0e-9f77-3f9a0c5d8e21")

#: The workspace an evaluation runs in. A golden graph belongs to no customer,
#: and a nil workspace is the honest way to say so — it is never used to reach
#: data, only to keep the adapter's own log lines traceable.
_EVALUATION_WORKSPACE: Final = UUID(int=0)


class EvaluationAbandonedError(AIPlatformError):
    """The run could not be completed, so it produced no measurement.

    Distinct from a failing run. A failing run is a result — the prompt is not
    releasable for this model, and that is evidence. This is the *absence* of a
    result, and conflating the two would let an outage read as a quality
    regression.
    """


class Harness:
    """Evaluates one pass's prompt against one model over one dataset."""

    def __init__(
        self,
        *,
        synthesise: Synthesise,
        prompts: PromptRegistry,
        today: Callable[[], date] = date.today,
    ) -> None:
        self._synthesise = synthesise
        self._prompts = prompts
        # Injected so a report's date is a fact about the run rather than about
        # when the command happened to execute.
        self._today = today

    async def evaluate(
        self,
        *,
        pass_: Pass,
        version: int,
        model: str,
        dataset: GoldenDataset,
        runs_per_case: int = 2,
    ) -> EvaluationReport:
        """Measure a prompt, twice per case by default.

        **Twice, because stability is the dimension this architecture can
        guarantee most cheaply.** The input is a closed set, so two runs differ
        only by the model — and a pass that passes once and fabricates on the
        second attempt is a pass that is not ready, which a single run
        structurally cannot detect.
        """
        if runs_per_case < 1:
            raise EvaluationAbandonedError("a run over zero attempts measured nothing.")

        prompt = self._prompts.get(pass_.value, version)
        results = [
            await self._case(one, pass_=pass_, version=version, runs=runs_per_case)
            for one in dataset.cases
        ]

        report = EvaluationReport(
            prompt_name=pass_.value,
            prompt_version=version,
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

    async def _case(self, case: GoldenCase, *, pass_: Pass, version: int, runs: int) -> CaseResult:
        approach = Approach(
            reasoning=case.source.reasoning,
            fits=case.source.fits,
            product=case.source.product,
        )
        correlation_id = uuid5(_CORRELATION_NAMESPACE, case.name)

        attempts: list[PassResult] = []
        for _ in range(runs):
            attempts.append(
                await self._synthesise.measure(
                    approach,
                    pass_,
                    version=version,
                    workspace_id=_EVALUATION_WORKSPACE,
                    correlation_id=correlation_id,
                )
            )

        # **The first failure decides the case.** A pass that fabricated on one
        # of two attempts has fabricated; averaging the two would let a prompt
        # earn a release on the run that happened to behave, which is the same
        # defect as averaging over a partial run.
        failed = next((one for one in attempts if not one.succeeded), None)
        if failed is not None:
            return CaseResult(
                case=case.name,
                outcome=failed.outcome,
                coverage=0.0,
                detail=failed.detail,
            )

        syntheses = [one.synthesis for one in attempts]
        assert all(one is not None for one in syntheses)  # narrowing; every attempt succeeded
        first = syntheses[0]
        assert first is not None

        agreement: float | None = None
        if len(syntheses) > 1:
            pairs = []
            for other in syntheses[1:]:
                assert other is not None
                pairs.append(stability(first, other))
            agreement = sum(pairs) / len(pairs)

        return CaseResult(
            case=case.name,
            outcome=PassOutcome.OK,
            coverage=coverage(first, case.load_bearing),
            stability=agreement,
        )

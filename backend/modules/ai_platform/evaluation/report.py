"""What one evaluation run recorded.

**Signora's view of an evaluation is deterministic even though the model is
not.** The output cannot be re-derived; everything *about* the run can be —
which prompt text, which model, which expectations, which criteria, on what
day, over how many cases, with what result. A run that cannot name those is
not a measurement, it is an anecdote.

The report is the human-readable artifact. The **durable** record is the
`Evaluation` it produces, appended to the prompt manifest — one authoritative
history rather than a reports directory that can disagree with it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from modules.ai_platform.domain.prompt import Evaluation
from modules.ai_platform.domain.record import InferenceOutcome
from modules.ai_platform.domain.rendering import PROMPT_RENDERING_PROTOCOL_VERSION
from modules.ai_platform.evaluation.rubric import RUBRIC_VERSION, criteria


def unmeasurable(model: str, reason: Exception) -> str:
    """The third evaluation state, rendered once for every entry point.

    **READY, REFUSED and UNMEASURABLE are three distinct engineering states**
    (ruled 2026-07-30). A refused run is a *result* — the prompt is not
    releasable for this model, and that is evidence. This is the absence of a
    result, and the two must never be conflated: an outage read as a quality
    regression would retire a prompt that nothing was ever wrong with.

    Written here rather than in each entry point because behaviour exists
    exactly once, and a message duplicated across two commands is how the two
    eventually report the same state differently.

    **It names no vendor**, because nothing in evaluation may: the run asked
    for a *model*, and which adapter serves one is configuration this text has
    no business describing.
    """
    return (
        f"UNMEASURABLE — the run produced no verdict.\n"
        f"\n"
        f"  model   {model}\n"
        f"  reason  {reason}\n"
        f"\n"
        "A run that cannot execute faithfully reports nothing rather than a verdict from\n"
        "the cases that happened to survive — a partial average recorded as a result is\n"
        "how a release gets granted on the successes.\n"
        "\n"
        "Evaluation resolves a provider by **model**, never by vendor: the registry serves\n"
        "whichever adapters this environment configured. If the model above is not\n"
        "registered, supply its credentials and run again; if its runtime is unreachable,\n"
        "start it. Neither is a finding about the prompt.\n"
        "\n"
        "This command measures a real model and will not substitute a fake for one: a\n"
        "scripted adapter never invents a quantity unless it is told to, so a run against\n"
        "one would prove the grounding checker works and nothing about the model."
    )


@dataclass(frozen=True, slots=True)
class CaseResult:
    """One case, measured.

    ``detail`` is kept for the failures: an evaluation that reports *how
    many* failed without saying *how* leaves the engineer to reproduce the
    run to find out, and a probabilistic run may not reproduce.
    """

    case: str
    outcome: InferenceOutcome
    coverage: float
    #: How many times this case's call was retried. **Never a quality
    #: signal** — it is a cost and reliability signal, and it must not
    #: influence whether the run earns a release. Reported because a run that
    #: needed retries is operationally different from one that did not, and
    #: that difference was previously visible only in the vendor's own log.
    retries: int = 0
    detail: str | None = None

    @property
    def grounding_failed(self) -> bool:
        return self.outcome is InferenceOutcome.UNGROUNDED

    @property
    def schema_failed(self) -> bool:
        return self.outcome is InferenceOutcome.SCHEMA_INVALID


@dataclass(frozen=True, slots=True)
class EvaluationReport:
    """One run of one prompt against one model over one dataset."""

    prompt_name: str
    prompt_version: int
    #: The prompt's *content* identity, not merely its number. Two runs
    #: claiming version 1 with different fingerprints measured two different
    #: prompts.
    prompt_fingerprint: str
    model: str
    dataset_name: str
    dataset_version: int
    dataset_fingerprint: str
    rubric_version: int
    evaluated_on: date
    results: tuple[CaseResult, ...]

    @property
    def sample_size(self) -> int:
        return len(self.results)

    @property
    def grounding_failures(self) -> int:
        return sum(1 for r in self.results if r.grounding_failed)

    @property
    def schema_failures(self) -> int:
        return sum(1 for r in self.results if r.schema_failed)

    @property
    def transport_failures(self) -> int:
        """Calls that never reached a verdict.

        Reported separately and **never** counted as a quality failure: a
        vendor being down says nothing about a prompt. It does invalidate the
        run, which is why `evaluation` refuses to record a result containing
        one rather than quietly averaging over the cases that survived.
        """
        return sum(
            1
            for r in self.results
            if r.outcome in (InferenceOutcome.TRANSIENT, InferenceOutcome.PERMANENT)
        )

    @property
    def coverage(self) -> float:
        return sum(r.coverage for r in self.results) / len(self.results)

    @property
    def retries(self) -> int:
        """Total retries across the run.

        A rising value is the earliest visible sign of a rate-limit or
        timeout problem (R-01) — visible here long before it is visible on an
        invoice. It does **not** affect `Evaluation.passed`: retrying is what
        the platform is supposed to do about a transient failure, and
        penalising a prompt for its provider's bad afternoon would make the
        release criteria measure the wrong thing.
        """
        return sum(r.retries for r in self.results)

    def as_evaluation(self) -> Evaluation:
        """The durable record this run supports.

        Facts only — no verdict. Whether they earn a release is
        `Evaluation.passed`, derived from the same numbers by criteria that
        live in one place.
        """
        return Evaluation(
            model=self.model,
            dataset=self.dataset_name,
            dataset_version=self.dataset_version,
            rubric_version=self.rubric_version,
            evaluated_on=self.evaluated_on,
            sample_size=self.sample_size,
            grounding_failures=self.grounding_failures,
            schema_failures=self.schema_failures,
            coverage=self.coverage,
            # Stamped from the running protocol rather than carried in on the
            # report: the run rendered through this process's renderer, so this
            # is the one place that can state it without being told.
            rendering_protocol_version=PROMPT_RENDERING_PROTOCOL_VERSION,
            retries=self.retries,
        )

    def render(self) -> str:
        evaluation = self.as_evaluation()
        lines = [
            f"prompt   {self.prompt_name}@{self.prompt_version}  {self.prompt_fingerprint[:12]}",
            f"model    {self.model}",
            f"dataset  {self.dataset_name}@{self.dataset_version}  {self.dataset_fingerprint[:12]}",
            f"rubric   v{self.rubric_version}    run on {self.evaluated_on.isoformat()}",
            # The fourth experimental condition, printed beside the other three
            # so a reader can see all of them without opening the manifest.
            f"render   protocol v{PROMPT_RENDERING_PROTOCOL_VERSION}",
            "",
            "criteria",
        ]
        lines.extend(f"  {line}" for line in criteria())
        lines.extend(
            [
                "",
                "cases",
            ]
        )
        for result in self.results:
            mark = "ok  " if result.outcome is InferenceOutcome.OK else "FAIL"
            line = f"  {mark} {result.case:<32} coverage {result.coverage:.2f}"
            if result.retries:
                line += f"  retries {result.retries}"
            if result.detail:
                line += f"\n         {result.detail}"
            lines.append(line)
        lines.extend(
            [
                "",
                f"sample size         {self.sample_size}",
                f"grounding failures  {self.grounding_failures}",
                f"schema failures     {self.schema_failures}",
                f"transport failures  {self.transport_failures}",
                f"retries             {self.retries}",
                f"coverage            {self.coverage:.3f}",
                "",
                f"release             {'EARNED' if evaluation.passed else 'REFUSED'}",
            ]
        )
        return "\n".join(lines)


#: Re-exported so a caller building a report imports one module, not three.
__all__ = ["CaseResult", "EvaluationReport", "RUBRIC_VERSION"]

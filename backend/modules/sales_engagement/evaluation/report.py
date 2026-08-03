"""What one evaluation run recorded.

**Signora's view of an evaluation is deterministic even though the model is
not.** The prose cannot be re-derived; everything *about* the run can be — which
prompt text, which model, which expectations, which criteria, under which
context protocol, on what day, over how many cases, with what result. A run that
cannot name those is not a measurement, it is an anecdote.

The report is the human-readable artifact. The **durable** record is the
`Evaluation` it produces, appended to this module's prompt manifest — one
authoritative history rather than a reports directory that can disagree with it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from modules.ai_platform.public import Evaluation
from modules.sales_engagement.application.synthesise import PassOutcome
from modules.sales_engagement.domain.context import COMMERCIAL_CONTEXT_PROTOCOL_VERSION
from modules.sales_engagement.domain.release import earns_release
from modules.sales_engagement.evaluation.rubric import RUBRIC_VERSION, criteria


def unmeasurable(model: str, reason: Exception) -> str:
    """The third evaluation state, rendered once for every entry point.

    **READY, REFUSED and UNMEASURABLE are three distinct engineering states.** A
    refused run is a *result* — the prompt is not releasable for this model, and
    that is evidence. This is the *absence* of a result, and conflating the two
    would let an outage read as a quality regression and retire a prompt that
    nothing was ever wrong with.

    **It names no vendor**, because nothing in evaluation may: the run asked for
    a *model*, and which adapter serves one is configuration this text has no
    business describing.
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
        "Evaluation resolves a provider by **model**, never by vendor. If the model above\n"
        "is not registered, supply its credentials and run again; if its runtime is\n"
        "unreachable, start it. Neither is a finding about the prompt.\n"
        "\n"
        "This command measures a real model and will not substitute a fake for one: a\n"
        "scripted adapter never invents a competitor unless it is told to, so a run\n"
        "against one would prove the fence works and nothing about the model."
    )


@dataclass(frozen=True, slots=True)
class CaseResult:
    """One case, measured.

    `detail` is kept for the failures: an evaluation reporting *how many* were
    refused without saying *which claim* leaves the engineer to reproduce a run
    that is probabilistic and may not reproduce.
    """

    case: str
    outcome: PassOutcome
    coverage: float
    #: Agreement between two runs over the same closed set. `None` when the case
    #: was run once — **absent rather than 1.0**, because a stability figure
    #: nobody measured must not read as perfect stability.
    stability: float | None = None
    detail: str | None = None

    @property
    def refused(self) -> bool:
        return self.outcome is PassOutcome.REFUSED

    @property
    def malformed(self) -> bool:
        return self.outcome is PassOutcome.MALFORMED


@dataclass(frozen=True, slots=True)
class EvaluationReport:
    """One run of one prompt against one model over one dataset."""

    prompt_name: str
    prompt_version: int
    #: The prompt's *content* identity, not merely its number. Two runs claiming
    #: version 1 with different fingerprints measured two different prompts.
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
    def refusals(self) -> int:
        return sum(1 for one in self.results if one.refused)

    @property
    def malformed(self) -> int:
        return sum(1 for one in self.results if one.malformed)

    @property
    def transport_failures(self) -> int:
        """Calls that never reached a verdict.

        Reported separately and **never** counted as a quality failure: a vendor
        being down says nothing about a prompt. It does invalidate the run,
        which is why the harness refuses to record a result containing one
        rather than quietly averaging over the cases that survived.
        """
        return sum(1 for one in self.results if one.outcome is PassOutcome.PROVIDER_FAILED)

    @property
    def coverage(self) -> float:
        return sum(one.coverage for one in self.results) / len(self.results)

    @property
    def stability(self) -> float | None:
        """Mean agreement across the cases that were run twice.

        `None` when nothing was — the same refusal `CaseResult.stability` makes,
        for the same reason.
        """
        measured = [one.stability for one in self.results if one.stability is not None]
        return sum(measured) / len(measured) if measured else None

    def as_evaluation(self) -> Evaluation:
        """The durable record this run supports.

        **Facts only — no verdict.** Whether they earn a release is
        `domain/release.earns_release`, derived from these same numbers by
        criteria that live in one place.

        Two fields carry this module's meaning rather than the AI Platform's,
        and the manifest says so: `grounding_failures` counts **syntheses the
        fence refused**, and `rendering_protocol_version` names the **Commercial
        Context Protocol**. Both are faithful to what the field records — *what
        was not supported by the closed set*, and *what produced the text the
        model read* — which is why the record is reused rather than reinvented.
        """
        return Evaluation(
            model=self.model,
            dataset=self.dataset_name,
            dataset_version=self.dataset_version,
            rubric_version=self.rubric_version,
            evaluated_on=self.evaluated_on,
            sample_size=self.sample_size,
            grounding_failures=self.refusals,
            schema_failures=self.malformed,
            coverage=self.coverage,
            # Stamped from the running protocol rather than carried in on the
            # report: the run rendered through this process's context renderer,
            # so this is the one place that can state it without being told.
            rendering_protocol_version=COMMERCIAL_CONTEXT_PROTOCOL_VERSION,
            retries=0,
        )

    def render(self) -> str:
        evaluation = self.as_evaluation()
        lines = [
            f"prompt   {self.prompt_name}@{self.prompt_version}  {self.prompt_fingerprint[:12]}",
            f"model    {self.model}",
            f"dataset  {self.dataset_name}@{self.dataset_version}  {self.dataset_fingerprint[:12]}",
            f"rubric   v{self.rubric_version}    run on {self.evaluated_on.isoformat()}",
            f"context  Commercial Context Protocol v{COMMERCIAL_CONTEXT_PROTOCOL_VERSION}",
            "",
            "criteria",
        ]
        lines.extend(f"  {one}" for one in criteria())
        lines.extend(["", "cases"])
        for one in self.results:
            mark = "ok  " if one.outcome is PassOutcome.OK else "FAIL"
            line = f"  {mark} {one.case:<34} coverage {one.coverage:.2f}"
            if one.stability is not None:
                line += f"  stability {one.stability:.2f}"
            if one.detail:
                line += f"\n         {one.outcome.value}: {one.detail}"
            lines.append(line)

        stability = self.stability
        shown = f"{stability:.3f}" if stability is not None else "not measured"
        lines.extend(
            [
                "",
                f"sample size         {self.sample_size}",
                f"refusals            {self.refusals}",
                f"malformed drafts    {self.malformed}",
                f"transport failures  {self.transport_failures}",
                f"coverage            {self.coverage:.3f}",
                f"stability           {shown}",
                "",
                f"release             {'EARNED' if earns_release(evaluation) else 'REFUSED'}",
            ]
        )
        return "\n".join(lines)


__all__ = ["CaseResult", "EvaluationReport", "RUBRIC_VERSION", "unmeasurable"]

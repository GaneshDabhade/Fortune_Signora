"""Running one synthesis pass over one closed reasoning graph.

**Five steps, and four of them can fail without a seller losing anything.**

```
  reasoning ─▶ context ─▶ prompt ─▶ model ─▶ draft ─▶ fence ─▶ Synthesis
                                      │        │        │
                                      └────────┴────────┴──▶ no prose,
                                                             brief intact
```

Every failure below degrades to *the brief renders without prose*, because none
of the recommendation, the ranked roles, the evidence, the unknowns or the risks
was ever the model's to produce (ADR-0200). **Delete the synthesis and the
product still works; delete the graph and there is nothing to synthesise.**

### Why the outcome is a value and not an exception

A caller needs to say *why* there is no prose, and the four answers need
different work: no released prompt is a **release** question, a malformed reply
is a **schema** question, a refusal is a **quality** question, and a provider
failure is an **operational** one. Collapsing them into one exception would put
the same line in the record for all four, which is how a model that
hallucinates and a model that is switched off become indistinguishable
(`CLAUDE.md` §17 — a system cannot be improved using information it never
recorded).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from modules.ai_platform.public import (
    AIProviderError,
    PromptNotReleasableError,
    PromptRegistry,
    PromptVersion,
)
from modules.sales_engagement.application.approach import Approach
from modules.sales_engagement.application.ports import SynthesisModel
from modules.sales_engagement.domain import release
from modules.sales_engagement.domain.brief import Pass
from modules.sales_engagement.domain.context import CommercialContext
from modules.sales_engagement.domain.draft import SCHEMA, DraftMalformedError, parse
from modules.sales_engagement.domain.synthesis import (
    Synthesis,
    SynthesisRefusedError,
    SynthesisSource,
    validate,
)

#: Where the reasoning graph goes in a prompt template, and where the output
#: schema goes. Refused if absent: a prompt with no context placeholder would
#: never show the model the graph, making every statement it produced an
#: invention by construction.
CONTEXT_PLACEHOLDER = "{context}"
SCHEMA_PLACEHOLDER = "{schema}"


class PassOutcome(StrEnum):
    """Why a pass did or did not produce prose."""

    OK = "ok"
    """The draft passed the fence."""

    NO_RELEASED_PROMPT = "no_released_prompt"
    """No artifact for this pass has earned this model. **The correct state for
    a prompt nobody has evaluated**, not a fault."""

    MALFORMED = "malformed"
    """The reply was not the declared shape."""

    REFUSED = "refused"
    """The reply claimed something the graph did not produce."""

    PROVIDER_FAILED = "provider_failed"
    """The call never reached a verdict. **Says nothing about the prompt.**"""


@dataclass(frozen=True, slots=True)
class PassResult:
    """One pass, run.

    `detail` is kept for every non-`OK` outcome: a record saying prose was
    refused without saying *which claim* leaves an engineer to reproduce a run
    that is probabilistic and may not reproduce.
    """

    pass_: Pass
    outcome: PassOutcome
    synthesis: Synthesis | None = None
    detail: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.synthesis is not None


class Synthesise:
    """Turns one reasoning graph into one narrated pass.

    **It decides nothing commercial.** Every value the model is shown was
    decided by the deterministic layer; this renders, calls, parses and checks.
    """

    def __init__(
        self,
        *,
        prompts: PromptRegistry,
        model: SynthesisModel,
        model_name: str,
    ) -> None:
        self._prompts = prompts
        self._model = model
        # **A model name, never a vendor** (`CLAUDE.md` §10). Configuration
        # supplies it at the composition root and nothing here may branch on
        # who serves it.
        self._model_name = model_name

    async def execute(
        self,
        approach: Approach,
        pass_: Pass,
        *,
        workspace_id: UUID,
        correlation_id: UUID,
    ) -> PassResult:
        """Run a pass, refusing any prompt that has not earned this model.

        **The gated path, and the only one production may take.** A prompt tuned
        against a small local model has not been shown to behave on a frontier
        hosted one, and ADR-0028 makes that structural rather than remembered.
        """
        try:
            prompt = self._released(pass_)
        except PromptNotReleasableError as exc:
            return PassResult(pass_, PassOutcome.NO_RELEASED_PROMPT, detail=str(exc))
        return await self._run(
            approach,
            pass_,
            prompt_text=prompt.text,
            workspace_id=workspace_id,
            correlation_id=correlation_id,
        )

    async def measure(
        self,
        approach: Approach,
        pass_: Pass,
        *,
        version: int,
        workspace_id: UUID,
        correlation_id: UUID,
    ) -> PassResult:
        """Run a specific version **without** the release gate.

        **Named for what it is**, exactly as `Infer.measure` is: this is the run
        that *earns* the release the rule enforces, so it cannot itself require
        one — and a boolean flag on `execute` would have made the ungated path
        reachable by accident from production code.
        """
        prompt = self._prompts.get(pass_.value, version)
        return await self._run(
            approach,
            pass_,
            prompt_text=prompt.text,
            workspace_id=workspace_id,
            correlation_id=correlation_id,
        )

    def _released(self, pass_: Pass) -> PromptVersion:
        """The highest version of this pass's artifact that has earned the model.

        **Highest rather than latest-on-disk.** A version 2 that has not been
        evaluated must never displace a version 1 that has — that is how a
        release becomes a filename convention instead of a measurement.
        """
        candidates = sorted(
            (
                one
                for one in self._prompts.versions
                if one.name == pass_.value and release.released_for(one, self._model_name)
            ),
            key=lambda one: one.version,
            reverse=True,
        )
        if candidates:
            return candidates[0]

        # Nothing released. Re-ask the gate for the *specific* refusal, so the
        # record says "not evaluated for this model" or "measured under a
        # superseded protocol" rather than a shrug — those have opposite
        # remedies, and one of them is *do not re-author the prompt*.
        known = [one for one in self._prompts.versions if one.name == pass_.value]
        if not known:
            raise PromptNotReleasableError(
                f"no prompt artifact named '{pass_.value}' exists. The pass is defined and "
                "the brief renders without it — every value above narration was produced "
                "without a model."
            )
        raise release.refusal(max(known, key=lambda one: one.version), self._model_name)

    async def _run(
        self,
        approach: Approach,
        pass_: Pass,
        *,
        prompt_text: str,
        workspace_id: UUID,
        correlation_id: UUID,
    ) -> PassResult:
        context = CommercialContext(
            source=SynthesisSource(
                reasoning=approach.reasoning,
                fits=approach.fits,
                product=approach.product,
            )
        )
        text = render(prompt_text, context)

        try:
            reply = await self._model.complete(
                prompt=text,
                model=self._model_name,
                workspace_id=workspace_id,
                correlation_id=correlation_id,
            )
        except AIProviderError as exc:
            return PassResult(pass_, PassOutcome.PROVIDER_FAILED, detail=str(exc))

        try:
            draft = parse(reply.text)
        except DraftMalformedError as exc:
            return PassResult(pass_, PassOutcome.MALFORMED, detail=str(exc))

        try:
            # **The context, not the source.** The model may quote a date or a
            # corroboration count the protocol showed it, and validating against
            # the narrower set would refuse a draft for repeating what it was
            # given — the false refusal `CommercialContext` exists to remove.
            synthesis = validate(draft, context, inference_id=reply.inference_id)
        except SynthesisRefusedError as exc:
            return PassResult(pass_, PassOutcome.REFUSED, detail=str(exc))

        return PassResult(pass_, PassOutcome.OK, synthesis=synthesis)


def render(prompt_text: str, context: CommercialContext) -> str:
    """The complete prompt for one pass.

    **Replacement, not formatting.** The template carries a JSON schema full of
    braces, and `str.format` would read every one of them as a placeholder — so
    the prompt would fail to render for a reason having nothing to do with what
    it says. The AI Platform's renderer made the same choice for the same
    reason.
    """
    if CONTEXT_PLACEHOLDER not in prompt_text:
        raise PromptNotReleasableError(
            f"a synthesis prompt has no {CONTEXT_PLACEHOLDER} placeholder, so the reasoning "
            "graph would never reach the model — which would make every statement it "
            "produced an invention by construction."
        )
    return prompt_text.replace(CONTEXT_PLACEHOLDER, context.render()).replace(
        SCHEMA_PLACEHOLDER, SCHEMA
    )

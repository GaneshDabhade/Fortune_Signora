"""The only path from Signora to a model.

Every inference in the platform passes through ``Infer.execute`` — there is
no other way to obtain model output, and no way to obtain *unvalidated*
model output at all. The same property the Buying Score Engine has, where
``BuyingScore.projected_from`` is the only constructor and a score that
disagrees with its ledger cannot be built.

**The lifecycle is explicit, and nothing happens between the stages:**

    resolve prompt  →  render  →  select provider  →  execute (with retry)
                    →  parse  →  ground  →  record  →  return

**Orchestration only.** This layer decides no business question. It does not
choose what to explain, what matters, or what an account deserves. It
coordinates six collaborators and records what happened.

**Stateless.** Everything needed arrives as an argument or an injected
collaborator; nothing is retained between calls. Two invocations with
identical inputs are indistinguishable except in the wording of the output —
which is what makes grounding checkable at all, since a response can only be
validated against a *known* evidence set.

**Retry is semantic, and narrow.** Transient failures are retried; permanent
ones never are. **Schema and grounding failures are never retried either** —
they are content failures, not transport failures, and quietly re-rolling
them would burn tokens while making the one rate this platform most needs to
measure unmeasurable.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from modules.ai_platform.application.ports import InferenceRecorder
from modules.ai_platform.application.render import render
from modules.ai_platform.domain.evidence import EvidenceSet
from modules.ai_platform.domain.grounding import (
    GroundedOutput,
    GroundingError,
    SchemaViolationError,
    UngroundedOutputError,
    output_schema,
    parse,
    verify,
)
from modules.ai_platform.domain.prompt import PromptRegistry, PromptVersion
from modules.ai_platform.domain.provider import (
    AIPermanentError,
    AIProviderAdapter,
    AIProviderError,
    AIProviderRegistry,
    AIRateLimitedError,
    AITransientError,
    AIVendor,
    InferenceRequest,
    InferenceResult,
)
from modules.ai_platform.domain.record import InferenceOutcome, InferenceRecord
from modules.ai_platform.domain.usage import InferenceUsage
from signora_platform.observability import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class InferencePolicy:
    """How the platform calls a model. **The only place these are decided.**

    Central and provider-agnostic, so no adapter's own idea of a timeout can
    leak upward and no two call sites disagree about how long is too long.
    """

    max_attempts: int = 3
    timeout_seconds: float = 60.0
    max_output_tokens: int = 2048
    #: Not a determinism control — see ``InferenceRequest.temperature``.
    #: Low because restatement is the task, not invention.
    temperature: float = 0.0
    #: Base delay between attempts, doubled each time. Used only when the
    #: vendor stated no wait of its own; a stated one always wins, because
    #: guessing over a vendor's own answer is how an integration gets
    #: throttled harder.
    backoff_seconds: float = 1.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1; zero attempts calls nothing.")
        if self.timeout_seconds <= 0 or self.backoff_seconds < 0:
            raise ValueError("timeout must be positive and backoff cannot be negative.")


class _ProviderCallError(Exception):
    """Carries the attempt count across the retry boundary. Never escapes.

    The count is known inside the retry loop and needed by the recorder
    outside it. Without it, a call that failed after three attempts records
    ``retries = 0`` — so a retry storm is invisible in exactly the rows that
    prove one happened, which is the opposite of what R-01 asks this table
    for.
    """

    def __init__(self, error: AIProviderError, retries: int) -> None:
        super().__init__(str(error))
        self.error = error
        self.retries = retries


@dataclass(frozen=True, slots=True)
class InferenceInput:
    """One request for grounded output."""

    prompt_name: str
    prompt_version: int
    model: str
    evidence: EvidenceSet
    correlation_id: UUID


@dataclass(frozen=True, slots=True)
class InferenceOutput[T: GroundedOutput]:
    """The validated output, and the record of how it was obtained."""

    output: T
    record: InferenceRecord


class Infer:
    """The single path to a model."""

    def __init__(
        self,
        *,
        providers: AIProviderRegistry,
        prompts: PromptRegistry,
        recorder: InferenceRecorder,
        policy: InferencePolicy,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._providers = providers
        self._prompts = prompts
        self._recorder = recorder
        self._policy = policy
        self._clock = clock
        # Injected so a test does not wait out a real backoff, and so the
        # only wall-clock dependency in the class is declared rather than
        # reached for.
        self._sleep = sleep

    def output_is_evidence(self, model: str) -> bool:
        """Whether a measurement taken against this model would be evidence.

        **`False` when the adapter serving it returns scripted content** — the
        deterministic mock, or any future fake or replay adapter that declares
        the same. `True` when a real model would answer.

        **A capability read from the descriptor, never a vendor comparison**
        (§10). The caller names a *model*; the registry decides who serves it
        and the adapter says what it is. Evaluation can therefore refuse a
        worthless run without being able to name what it refused
        ([B-324](../../../../docs/BUGS.md)).

        **Here rather than on the harness**, because the harness has no
        registry and giving it one would change a constructor four evaluation
        entrypoints call — one of which belongs to another module. This
        object already holds the registry, and every harness already holds
        this object, so the guarantee reaches all four without any of them
        changing.

        **`True` for a model nothing serves.** An unregistered model fails at
        the call with its own diagnosis; answering *"not evidence"* here would
        replace that with a misleading one, and the run records no result to
        write in any case.
        """
        for adapter in self._providers.adapters:
            descriptor = adapter.describe()
            if descriptor.serves(model):
                return descriptor.output_is_evidence
        return True

    async def execute[T: GroundedOutput](
        self, request: InferenceInput, output_type: type[T]
    ) -> InferenceOutput[T]:
        """Obtain grounded output. **The only path a request path may take.**

        Refuses a prompt that has not earned this model, before anything is
        rendered or sent.
        """
        prompt = self._prompts.get(request.prompt_name, request.prompt_version)
        prompt.require_model(request.model)
        return await self._run(request, output_type, prompt)

    async def measure[T: GroundedOutput](
        self, request: InferenceInput, output_type: type[T]
    ) -> InferenceOutput[T]:
        """The same call, without the release rule. **Evaluation only.**

        The release rule and the act that satisfies it cannot both come first:
        a prompt is usable with a model once it has passed evaluation against
        it, and evaluating it requires calling it. So the exception is named,
        narrow, and *structural* rather than a flag — a boolean argument
        called `skip_release_check` would eventually be passed `True` by a
        request path at three in the morning.

        **Enforced, not documented:** a Security Invariant asserts this method
        is called from `evaluation/` and nowhere else. Everything else about
        the lifecycle is identical, deliberately — a harness measuring a
        different code path from the one production runs measures the wrong
        thing.
        """
        prompt = self._prompts.get(request.prompt_name, request.prompt_version)
        return await self._run(request, output_type, prompt)

    async def _run[T: GroundedOutput](
        self, request: InferenceInput, output_type: type[T], prompt: PromptVersion
    ) -> InferenceOutput[T]:
        # ---- render: evidence becomes text, deterministically
        text = render(prompt, request.evidence)

        # ---- select provider: by model. No caller names a vendor.
        adapter = self._providers.for_model(request.model)

        call = InferenceRequest(
            model=request.model,
            prompt=text,
            output_schema=output_schema(output_type),
            workspace_id=request.evidence.workspace_id,
            correlation_id=request.correlation_id,
            max_output_tokens=self._policy.max_output_tokens,
            temperature=self._policy.temperature,
            timeout_seconds=self._policy.timeout_seconds,
        )

        # ---- execute, with retry confined to transport failures
        try:
            result, retries = await self._call(adapter, call)
        except _ProviderCallError as failure:
            outcome = (
                InferenceOutcome.TRANSIENT
                if isinstance(failure.error, AITransientError)
                else InferenceOutcome.PERMANENT
            )
            await self._write(
                request,
                prompt,
                outcome,
                # The vendor *is* known here even though nothing came back:
                # every AIProviderError names the one that raised it. Losing
                # it would leave a rate-limit incident attributable to
                # nobody, which is the failure this hierarchy exists to
                # prevent in the other direction.
                vendor=failure.error.vendor,
                # But not what served it. Nothing served it.
                served_model=None,
                detail=str(failure.error),
                usage=_spent(retries=failure.retries),
            )
            raise failure.error from None

        usage = _with_retries(result.usage, retries)

        # ---- validate structure, then ground. Never retried: both are
        #      content failures, and re-rolling one hides it.
        try:
            output = parse(output_type, result.content)
            verify(output, request.evidence)
        except (SchemaViolationError, UngroundedOutputError) as exc:
            outcome = (
                InferenceOutcome.SCHEMA_INVALID
                if isinstance(exc, SchemaViolationError)
                else InferenceOutcome.UNGROUNDED
            )
            await self._write(
                request,
                prompt,
                outcome,
                vendor=result.vendor,
                served_model=result.model,
                detail=str(exc),
                usage=usage,
            )
            raise

        record = await self._write(
            request,
            prompt,
            InferenceOutcome.OK,
            vendor=result.vendor,
            served_model=result.model,
            detail=None,
            usage=usage,
        )
        return InferenceOutput(output=output, record=record)

    async def _call(
        self, adapter: AIProviderAdapter, call: InferenceRequest
    ) -> tuple[InferenceResult, int]:
        """Execute, retrying transient failures only.

        Returns the result and **how many retries it took** — a permanent
        failure raised on the second attempt is a different operational fact
        from one raised on the first, and both are lost if only the error
        travels.

        A permanent failure is never retried: retrying one burns quota to no
        purpose and turns a configuration mistake into a burst of identical
        failures at the vendor.
        """
        last: tuple[AITransientError, int] | None = None
        for attempt in range(self._policy.max_attempts):
            try:
                return await adapter.complete(call), attempt
            except AITransientError as exc:
                last = (exc, attempt)
                if attempt + 1 >= self._policy.max_attempts:
                    break
                await self._sleep(self._delay(exc, attempt))
            except AIPermanentError as exc:
                raise _ProviderCallError(exc, attempt) from exc
        assert last is not None  # only reachable after a transient failure
        raise _ProviderCallError(*last)

    def _delay(self, error: AITransientError, attempt: int) -> float:
        """The vendor's stated wait if it gave one, else exponential backoff.

        A stated wait always wins. Guessing over a vendor's own answer is
        how an integration gets throttled harder, and inventing one when it
        said nothing is the same mistake in the other direction.
        """
        if isinstance(error, AIRateLimitedError):
            stated: float | None = error.retry_after_seconds
            if stated is not None:
                return stated
        # 2.0 rather than 2: int ** int is Any in typeshed, since a
        # negative exponent yields a float.
        return self._policy.backoff_seconds * (2.0**attempt)

    async def _write(
        self,
        request: InferenceInput,
        prompt: PromptVersion,
        outcome: InferenceOutcome,
        *,
        vendor: AIVendor | None,
        served_model: str | None,
        detail: str | None,
        usage: InferenceUsage,
    ) -> InferenceRecord:
        """Record what happened. **Called on every outcome.**

        ``vendor`` and ``served_model`` are passed rather than derived from a
        result, because they are not known together: a failure that reached a
        vendor names it while nothing served the call.
        """
        record = InferenceRecord(
            id=uuid4(),
            workspace_id=request.evidence.workspace_id,
            correlation_id=request.correlation_id,
            prompt_name=prompt.name,
            prompt_version=prompt.version,
            prompt_fingerprint=prompt.fingerprint,
            requested_model=request.model,
            served_model=served_model,
            vendor=vendor,
            evidence_digest=request.evidence.digest,
            evidence_refs=tuple(sorted(f.ref.token for f in request.evidence)),
            outcome=outcome,
            usage=usage,
            detail=detail,
            created_at=self._clock(),
        )
        await self._recorder.record(record)
        logger.info(
            "inference completed",
            extra={
                "workspace_id": str(record.workspace_id),
                "correlation_id": str(record.correlation_id),
                "prompt": prompt.reference,
                "requested_model": record.requested_model,
                "vendor": record.vendor.value if record.vendor else None,
                "outcome": record.outcome.value,
                "input_tokens": record.usage.input_tokens,
                "output_tokens": record.usage.output_tokens,
                "latency_ms": record.usage.latency_ms,
                "retries": record.usage.retries,
            },
        )
        return record


def _spent(*, retries: int) -> InferenceUsage:
    """Usage for a call that never produced a response.

    Zeros for tokens and latency rather than absence: a failed call still
    happened, and a row with no usage is indistinguishable from one that was
    never attempted. ``retries`` is emphatically **not** zeroed — it is the
    only part of this record that carries information.
    """
    return InferenceUsage(input_tokens=0, output_tokens=0, latency_ms=0, retries=retries)


def _with_retries(usage: InferenceUsage, retries: int) -> InferenceUsage:
    """Adapters report one call; the retry count belongs to whoever retried."""
    return InferenceUsage(
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        latency_ms=usage.latency_ms,
        retries=retries,
    )


# Grounding failures are content failures. Re-exported here so a caller
# handling the outcome of an inference imports one module, not three.
__all__ = [
    "Infer",
    "InferenceInput",
    "InferenceOutput",
    "InferencePolicy",
    "GroundingError",
]

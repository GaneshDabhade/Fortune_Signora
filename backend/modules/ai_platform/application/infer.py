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

    async def execute[T: GroundedOutput](
        self, request: InferenceInput, output_type: type[T]
    ) -> InferenceOutput[T]:
        # ---- resolve prompt: refuses a model this prompt has not earned
        prompt = self._prompts.get(request.prompt_name, request.prompt_version)
        prompt.require_model(request.model)

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
            result, attempts = await self._call(adapter, call)
        except AIProviderError as exc:
            outcome = (
                InferenceOutcome.TRANSIENT
                if isinstance(exc, AITransientError)
                else InferenceOutcome.PERMANENT
            )
            await self._write(request, prompt, outcome, None, str(exc), _spent(attempts=0))
            raise

        usage = _with_retries(result.usage, attempts)

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
            await self._write(request, prompt, outcome, result, str(exc), usage)
            raise

        record = await self._write(request, prompt, InferenceOutcome.OK, result, None, usage)
        return InferenceOutput(output=output, record=record)

    async def _call(
        self, adapter: AIProviderAdapter, call: InferenceRequest
    ) -> tuple[InferenceResult, int]:
        """Execute, retrying transient failures only.

        A permanent failure is raised on the first attempt: retrying one
        burns quota to no purpose and turns a configuration mistake into a
        burst of identical failures at the vendor.
        """
        last: AITransientError | None = None
        for attempt in range(self._policy.max_attempts):
            try:
                return await adapter.complete(call), attempt
            except AITransientError as exc:
                last = exc
                if attempt + 1 >= self._policy.max_attempts:
                    break
                await self._sleep(self._delay(exc, attempt))
            except AIPermanentError:
                raise
        assert last is not None  # only reachable after a transient failure
        raise last

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
        result: InferenceResult | None,
        detail: str | None,
        usage: InferenceUsage,
    ) -> InferenceRecord:
        record = InferenceRecord(
            id=uuid4(),
            workspace_id=request.evidence.workspace_id,
            correlation_id=request.correlation_id,
            prompt_name=prompt.name,
            prompt_version=prompt.version,
            prompt_fingerprint=prompt.fingerprint,
            requested_model=request.model,
            served_model=result.model if result else None,
            vendor=result.vendor if result else None,
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


def _spent(*, attempts: int) -> InferenceUsage:
    """Usage for a call that never produced a response.

    Zeros rather than absence: a failed call still happened, and a row with
    no usage is indistinguishable from one that was never attempted.
    """
    return InferenceUsage(input_tokens=0, output_tokens=0, latency_ms=0, retries=attempts)


def _with_retries(usage: InferenceUsage, attempts: int) -> InferenceUsage:
    """Adapters report one call; the retry count belongs to whoever retried."""
    return InferenceUsage(
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        latency_ms=usage.latency_ms,
        retries=attempts,
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

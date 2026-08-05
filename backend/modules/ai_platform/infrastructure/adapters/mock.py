"""The deterministic provider — how development runs, and how it must never
run in production.

**A first-class development provider, not a test double.** The distinction
is the product owner's and it decides the file's shape: this is registered
by the composition root, resolved through `AIProviderRegistry.for_model`,
and reached by the same code path a customer's inference takes. Nothing
above the port can tell it apart from Ollama or Anthropic, which is the
point — a deterministic mode that skipped the port would prove the mock
works and say nothing about the product.

**Why it exists.** `CLAUDE.md` §10: *"Development must never require a
locally running LLM… A fresh clone is productive with no local model."*
Before this adapter, `build_provider_registry` registered Ollama
unconditionally, so every developer needed a 4.7GB download to exercise a
code path that never calls a model in anger.

### The mock follows the contract; the contract never follows the mock

It implements **only** `describe` and `complete`, because that is all
`AIProviderAdapter` defines. No streaming, no tool calls, no embeddings —
`domain/provider.py` is explicit that a wider port *"would force every
future vendor to implement methods most of them do not have, and the usual
outcome is adapters raising NotImplementedError, which is a contract that
lies."* When the port grows, this file grows in the same change and never
before it.

### Six knobs, and they are constructor arguments rather than settings

Configuration selects *the mock*; a caller configures *its behaviour*. Six
environment variables to make a fake return a rate-limit would be
configuration surface nobody would set, and §6 forbids flags built for
requirements that do not exist. A test that wants a 429 constructs one.

### The timeout is derived from latency, and that is one knob fewer than asked

[TASK-415](../../../../../docs/BACKLOG.md) lists **timeout** beside **latency**
as separate knobs. **They are one fact.** A configured latency and a
configured timeout are two representations of *how long this call took*, and
§2 is explicit that the second copy eventually contradicts the first — a mock
scripted to take 5s and time out at 30s would raise a timeout while reporting
that it did not.

So `latency_ms` decides both: it is what the result reports, **and** the call
raises `AITransientError` when it exceeds the request's own
`timeout_seconds`. That is also what a real adapter does — the budget lives
on `InferenceRequest`, set once by `InferencePolicy`, and an adapter carrying
its own would be the duplicated default §2 names.

**Deviation from the row's acceptance criterion, stated rather than
absorbed**, because *"each of the six knobs is independently settable"* is
satisfied by five knobs and one derivation, and hiding that in an
implementation would make the criterion look met by something it is not.

### It is deterministic, and that is a guarantee rather than a side effect

Same request in, same result out — no clock, no randomness, no counter
that changes what the second call returns. `latency_ms` is a *reported*
number, not a slept one: a fake that actually waited would make the suite
slower without making it more honest. Determinism is what lets this adapter
sit under replay, regression and the Security Invariants (`CLAUDE.md` §2,
*determinism outranks convenience*).
"""

from __future__ import annotations

from modules.ai_platform.domain.provider import (
    AIProviderDescriptor,
    AIProviderError,
    AITransientError,
    AIVendor,
    InferenceRequest,
    InferenceResult,
)
from modules.ai_platform.domain.usage import InferenceUsage

VENDOR = AIVendor.MOCK

#: What a caller gets when nothing else is scripted. A valid, empty JSON
#: object: every prompt in this platform demands a schema-constrained
#: object, so the default has to *parse* even though it asserts nothing.
DEFAULT_CONTENT = "{}"


class MockAdapter:
    """Satisfies ``AIProviderAdapter`` without reaching anything.

    Serves whichever models it is told to. The registry refuses two adapters
    claiming one model, so a process that registers this one has deliberately
    not registered a real one for those models — which is the composition
    root's decision and never this adapter's.
    """

    def __init__(
        self,
        *,
        models: frozenset[str],
        content: str = DEFAULT_CONTENT,
        error: AIProviderError | None = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        latency_ms: int = 0,
        retries: int = 0,
    ) -> None:
        self._models = models
        self._content = content
        self._error = error
        self._input_tokens = input_tokens
        self._output_tokens = output_tokens
        self._latency_ms = latency_ms
        self._retries = retries
        #: Every request that crossed the port, in order. Lets a caller
        #: assert what was *asked* without reaching inside the adapter —
        #: the property `FakeAdapter` established and the reason this file
        #: replaces it rather than sitting beside it.
        self.seen: list[InferenceRequest] = []

    def describe(self) -> AIProviderDescriptor:
        return AIProviderDescriptor(
            models=self._models,
            #: True because it is: the mock returns exactly the content it
            #: was given, which satisfies any schema the caller scripted it
            #: for. Declaring False would make the registry refuse it, and
            #: correctly — an adapter that cannot constrain output is
            #: unusable here, not degraded.
            supports_structured_output=True,
            vendor=VENDOR,
        )

    async def complete(self, request: InferenceRequest) -> InferenceResult:
        """Return what this adapter was scripted to return.

        **Raises the configured failure before recording usage**, matching a
        real adapter: a call that failed has no output tokens, and reporting
        some would make the deterministic path disagree with every other one.
        """
        self.seen.append(request)
        if self._error is not None:
            raise self._error
        if self._latency_ms / 1000 > request.timeout_seconds:
            raise AITransientError(
                VENDOR,
                f"the request allowed {request.timeout_seconds}s and this call took "
                f"{self._latency_ms / 1000}s.",
            )
        return InferenceResult(
            content=self._content,
            #: `request.model`, never a model of this adapter's own choosing.
            #: A real vendor may route an alias to a specific build and the
            #: field records what actually served the call; the mock has no
            #: such indirection, so echoing what was asked is the truthful
            #: answer rather than a convenient one.
            model=request.model,
            vendor=VENDOR,
            usage=InferenceUsage(
                input_tokens=self._input_tokens,
                output_tokens=self._output_tokens,
                latency_ms=self._latency_ms,
                retries=self._retries,
            ),
        )

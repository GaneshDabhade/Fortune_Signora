"""The AI Provider Port — the contract every model vendor satisfies.

Modelled deliberately on ``modules/provider_platform/domain/provider.py``,
which has held for four milestones. Same shape: a narrow Protocol, a
semantic failure taxonomy, a descriptor readable without calling anything,
and a registry populated from configuration at the composition root.

Four properties shape everything here.

**The port describes capability, never implementation.** A caller says what
it needs — this model, this schema, this budget — and the adapter decides
how to satisfy it. Nothing above the port knows that Ollama takes a
``format`` field and Anthropic takes a tool definition.

**Failure is part of the contract.** A port that returns data on success and
raises whatever the vendor SDK raised on failure has not abstracted the
vendor at all — every caller ends up handling ``httpx``, ``anthropic`` and
``openai`` exceptions. The failures below are the complete set a caller must
handle, and adapters translate everything into them (CLAUDE.md §15).

**Vendor identity is a label, never a decision input.** ``AIVendor`` exists
because provenance requires it: every inference records which vendor
answered (AC-69), and an unattributable result cannot be debugged. It is
recorded and never consulted — no business behaviour may differ because
Ollama rather than Claude served a call (CLAUDE.md §10, ADR-0028). The
registry below makes that structural rather than aspirational.

**The port is stateless.** ``complete`` takes everything it needs and the
adapter retains nothing between calls: no conversation handle, no server-side
session, no response cache. Vendor APIs offering stateful conversations are
used in their stateless form. This is not a scaling preference — a grounded
response is only checkable against a *known* evidence set, so a platform
carrying facts between calls would validate against a set the model never
saw (``docs/architecture/28-ai-platform.md``).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable
from uuid import UUID

from modules.ai_platform.domain.errors import AIPlatformError
from modules.ai_platform.domain.usage import InferenceUsage


class AIVendor(StrEnum):
    """Vendors with a ratified architectural record.

    Membership means the vendor is *architecturally recognised*, not that an
    adapter exists — the same framing as ``ProviderName``. M8 builds two:
    ``OLLAMA`` and ``ANTHROPIC`` (ADR-0028). ``OPENAI`` and ``GEMINI`` are
    ratified in ADR-0012 and gain adapters when a real caller needs them.

    Azure OpenAI and Bedrock are *reserved* rather than recognised, and are
    deliberately absent: a member here with no ratified status is a
    speculative extension point, and the roadmap's no-speculative-ports
    ruling applies to enums too.

    **This is a provenance label and a composition key. It is never a
    decision input.** Nothing outside an adapter may branch on it.
    """

    OLLAMA = "ollama"
    """Development only. Never a production dependency (ADR-0028)."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"


# --------------------------------------------------------------- failures
#
# Split by what was actually reached. A malformed request never touched a
# vendor, and stamping one with a vendor name would put a false lead in the
# exact place an engineer looks first. `ProviderError` takes a vendor
# unconditionally because every failure it models is a vendor's; that is not
# true here, and copying the shape without checking would have made the
# error messages lie.


class InferenceRequestError(AIPlatformError, ValueError):
    """The caller built a request that cannot be sent.

    A caller bug, caught before any vendor is chosen — hence no vendor.
    """


class AIRegistrationError(AIPlatformError):
    """An adapter was registered that cannot be used.

    Composition-time, where a human is present and a stack trace is cheap.
    """

    def __init__(self, vendor: AIVendor, message: str) -> None:
        super().__init__(f"[{vendor}] {message}")
        self.vendor = vendor


class ModelNotRegisteredError(AIPlatformError):
    """A model was requested that no registered adapter serves.

    A routing fact rather than a vendor failure — *nobody* answered, so
    there is nobody to attribute it to. Typed rather than an empty result,
    so a misconfigured model name fails loudly instead of looking like a
    model that had nothing to say.
    """


class AIProviderError(AIPlatformError):
    """Base for every failure a vendor call may surface.

    A caller catching this has caught everything an adapter can raise. No
    vendor SDK exception escapes an adapter.
    """

    def __init__(self, vendor: AIVendor, message: str) -> None:
        super().__init__(f"[{vendor}] {message}")
        self.vendor = vendor


class AITransientError(AIProviderError):
    """Retry with backoff — a timeout, a 5xx, an overloaded model.

    Separated from permanent failures because the correct response differs
    entirely: retrying a permanent failure burns quota to no purpose, and
    giving up on a transient one discards work that was merely late.
    """


class AIRateLimitedError(AITransientError):
    """Transient, but with a vendor-supplied wait.

    A subclass rather than a flag, so a caller handling transient failures
    generically still backs off correctly while one that wants to honour
    ``retry_after_seconds`` can. Guessing a backoff when the vendor stated
    one is how an integration gets throttled harder.
    """

    def __init__(
        self, vendor: AIVendor, message: str, retry_after_seconds: float | None = None
    ) -> None:
        super().__init__(vendor, message)
        self.retry_after_seconds = retry_after_seconds


class AIPermanentError(AIProviderError):
    """Do not retry — a rejected credential, a malformed request, a refusal."""


class AIOutputUnusableError(AIPermanentError):
    """The vendor responded, but not with something that can be parsed.

    Truncated output, prose where a JSON object was demanded, a response cut
    short by a token ceiling. **Distinct from a grounding failure**, which is
    a validated structure making an unsupported claim: this is the transport
    contract breaking, that is the content contract breaking, and conflating
    them would hide a systemic vendor problem inside a per-call quality
    metric.
    """


# ------------------------------------------------------------- contracts


@dataclass(frozen=True, slots=True)
class InferenceRequest:
    """One complete request to one model.

    Complete is the operative word: the adapter holds no state between
    calls, so everything the vendor needs is here. Two requests with
    identical fields are indistinguishable to the adapter.
    """

    #: The model to use. **Not** a vendor — the registry resolves who serves
    #: it, so no caller above the port names a vendor to get work done.
    model: str
    #: The fully rendered prompt. Rendering happens above the port, from a
    #: versioned template and a closed evidence set; the adapter receives
    #: text and never assembles it.
    prompt: str
    #: JSON Schema the response must satisfy. Adapters translate this into
    #: whatever their vendor calls structured output — that translation is
    #: the entire reason this port exists.
    output_schema: Mapping[str, Any]
    #: Present so the adapter's own log lines are traceable (CLAUDE.md §16).
    #: **Never sent to the vendor**; they identify a call in Signora, not to
    #: a third party.
    workspace_id: UUID
    correlation_id: UUID
    max_output_tokens: int
    #: Sampling temperature. **Not a determinism control.** Batching,
    #: hardware, and silent vendor-side model updates all move the output at
    #: any temperature; no part of this design may claim reproducibility on
    #: the strength of this field (ADR-0028, 28-ai-platform.md).
    temperature: float = 0.0
    timeout_seconds: float = 60.0

    def __post_init__(self) -> None:
        if not self.model.strip():
            raise InferenceRequestError("an inference request names no model.")
        if not self.prompt.strip():
            raise InferenceRequestError(
                "an inference request carries an empty prompt. A model asked nothing still "
                "returns something, and that something would be ungrounded by construction."
            )
        if self.max_output_tokens <= 0:
            raise InferenceRequestError(
                f"max_output_tokens must be positive (got {self.max_output_tokens})."
            )


@dataclass(frozen=True, slots=True)
class InferenceResult:
    """What one model returned, plus what it cost.

    ``content`` is **untrusted**. It is raw text that parses as the requested
    shape at best; whether it is *grounded* — every statement cited, every
    citation resolving, every number present in cited evidence — is decided
    above the port and is not this type's business (28-ai-platform.md).
    """

    content: str
    #: What actually served the call, which is not always what was asked for:
    #: a vendor may silently route an alias to a specific build. Recorded as
    #: provenance so a behaviour change traces to a model change.
    model: str
    vendor: AIVendor
    usage: InferenceUsage


@dataclass(frozen=True, slots=True)
class AIProviderDescriptor:
    """Static facts about an adapter, readable without calling it.

    **Capabilities first, identity last.** A future vendor integrates by
    *describing what it supports*, never by requiring conditional logic
    elsewhere — which is the difference between an abstraction and a
    dispatch table with extra steps.
    """

    #: Which models this adapter serves. Drives routing (see the registry)
    #: and the prompt manifest's release rule: a prompt may only be used with
    #: a model it was evaluated against (ADR-0028).
    models: frozenset[str]
    #: Whether the adapter can constrain output to a JSON Schema. **The one
    #: capability M8 cannot proceed without** — every guarantee in this
    #: module begins with a parseable structure — so the registry refuses an
    #: adapter that declares ``False`` rather than discovering it at 3am.
    supports_structured_output: bool
    #: Provenance and composition key only. Declared last, and never read to
    #: decide behaviour.
    vendor: AIVendor

    def serves(self, model: str) -> bool:
        return model in self.models


@runtime_checkable
class AIProviderAdapter(Protocol):
    """The port. Implemented identically by Ollama, Anthropic, and whatever
    comes next.

    Deliberately narrow: one describe, one complete. Tool use, streaming,
    embeddings and vision are absent because no caller needs them — a wider
    port would force every future vendor to implement methods most of them
    do not have, and the usual outcome is adapters raising
    ``NotImplementedError``, which is a contract that lies.
    """

    def describe(self) -> AIProviderDescriptor: ...

    async def complete(self, request: InferenceRequest) -> InferenceResult:
        """Run one inference.

        Raises only ``AIProviderError`` subclasses. Adapters may retry
        internally and report the count in ``InferenceUsage.retries``; they
        must not retry a permanent failure.
        """
        ...


@dataclass(frozen=True, slots=True)
class AIProviderRegistry:
    """The adapters available to this process, resolved **by model**.

    There is deliberately **no way to ask this registry for a vendor by
    name.** That is the structural form of vendor neutrality (CLAUDE.md §10):
    a caller states the capability it needs — this model — and the registry
    answers who provides it. Business code that cannot *name* a vendor cannot
    branch on one.

    This is a considered departure from ``ProviderRegistry``, which does
    expose ``get(provider)``. The difference is real rather than stylistic: a
    data sync genuinely targets a named provider — *fetch Apollo's view of
    this company* is the request — whereas an inference targets a **model**,
    and which vendor serves it is an operational detail the caller has no
    business knowing.

    Populated once at the composition root from ``Settings`` and read-only
    thereafter: no per-workspace state, no usage accumulators, no adaptive
    routing that learns from previous calls (the statelessness principle).
    """

    adapters: list[AIProviderAdapter] = field(default_factory=list)

    def register(self, adapter: AIProviderAdapter) -> None:
        """Add an adapter, refusing two kinds of misconfiguration outright.

        Both are caught here rather than at call time because composition is
        where a human is present and a stack trace is cheap.
        """
        descriptor = adapter.describe()
        if not descriptor.supports_structured_output:
            raise AIRegistrationError(
                descriptor.vendor,
                "this adapter cannot constrain output to a schema, so nothing it returns "
                "could be validated or grounded. An unstructured provider is not a "
                "degraded option here — it is unusable.",
            )
        if not descriptor.models:
            raise AIRegistrationError(descriptor.vendor, "this adapter serves no models.")
        for existing in self.adapters:
            clash = descriptor.models & existing.describe().models
            if clash:
                raise AIRegistrationError(
                    descriptor.vendor,
                    f"model(s) {sorted(clash)} are already served by "
                    f"{existing.describe().vendor}. Two adapters claiming one model makes "
                    "routing depend on registration order, and provenance would record "
                    "whichever happened to win.",
                )
        self.adapters.append(adapter)

    def for_model(self, model: str) -> AIProviderAdapter:
        """The adapter serving this model.

        The only routing this module offers, and the only one it should:
        every caller above the port asks for a *model*.
        """
        for adapter in self.adapters:
            if adapter.describe().serves(model):
                return adapter
        known = sorted(m for a in self.adapters for m in a.describe().models)
        raise ModelNotRegisteredError(
            f"no registered adapter serves model '{model}'. Registered: {known or 'none'}."
        )

    def descriptors(self) -> tuple[AIProviderDescriptor, ...]:
        """Every registered adapter's static facts, for health output.

        Reporting *which* adapters are wired is diagnostics, not behaviour —
        the distinction that keeps ``ProviderResponse.simulated`` legitimate
        while ``if simulated:`` is not (AC-21).
        """
        return tuple(adapter.describe() for adapter in self.adapters)

"""Composition root for the AI Platform.

**The only place that knows a vendor exists.** `AISettings` is constructed
here, the adapter is built from it, the registry is assembled, and `Infer` is
wired. Nothing above this file can name a vendor, which is what makes vendor
neutrality a property of the code rather than a rule people remember.

Configuration is a typed Settings object owned by the module whose behaviour
it governs (CLAUDE.md §6, ratified 2026-07-30). `AISettings` is the AI
Platform's; the platform's own lives in `signora_platform/settings.py`; no
module ever learns where another module's configuration came from.

The HTTP client and the explanation source are **parameters, not
constructions**: the client's lifetime belongs to the process that owns it,
and building an `OpportunityQueries` here would mean importing another
module's infrastructure.
"""

from __future__ import annotations

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.ai_platform.application.infer import Infer, InferencePolicy
from modules.ai_platform.application.narrate import Narrate
from modules.ai_platform.application.ports import ExplanationSource
from modules.ai_platform.domain.provider import (
    AIProviderRegistry,
    AIRegistrationError,
    AIVendor,
)
from modules.ai_platform.infrastructure.adapters.anthropic import AnthropicAdapter
from modules.ai_platform.infrastructure.adapters.mock import MockAdapter
from modules.ai_platform.infrastructure.adapters.ollama import OllamaAdapter
from modules.ai_platform.infrastructure.prompt_loader import load_prompt_registry
from modules.ai_platform.infrastructure.repository import (
    SqlInferenceRecorder,
    SqlNarrationRepository,
)
from modules.ai_platform.infrastructure.settings import AISettings
from signora_platform.event_bus import EventPublisher

#: The prompt M8 ships. Named here rather than passed by a caller: which
#: prompt narrates an account is the module's decision, and a caller free to
#: choose one could route around the release rule by naming an unevaluated
#: version.
NARRATION_PROMPT = "explanation_narration"
NARRATION_PROMPT_VERSION = 1


def build_provider_registry(
    settings: AISettings, *, client: httpx.AsyncClient
) -> AIProviderRegistry:
    """Register every adapter whose configuration is present.

    **An adapter is registered only when its credentials exist.** A missing
    key therefore produces *"no provider serves this model"* at resolution —
    a clear composition error — rather than a call that travels to a vendor
    and fails there with something less legible.

    There is deliberately **no fallback between them.** Development is
    deterministic and production is hosted (ADR-0028); a deployed service that
    could quietly reach a local runtime when its vendor was unreachable would
    serve customers from a model nothing evaluated.

    **The environment comes from this module's own `AISettings`**, which reads
    the same `SIGNORA_ENVIRONMENT` variable the platform does. Reaching into
    `signora_platform.Settings` for it would be the cross-module configuration
    read §6 forbids; taking it as a parameter would let a caller forget it,
    and the one thing this guard may never do is fail open.
    """
    registry = AIProviderRegistry()
    if settings.development_provider == "mock":
        if not settings.environment.is_development:
            raise AIRegistrationError(
                AIVendor.MOCK,
                f"the deterministic mock provider was selected in environment "
                f"'{settings.environment}'. It answers without reaching a model, so a service "
                "running on it is indistinguishable from one that works — which is "
                "strictly worse than the outage it would hide. Set "
                "SIGNORA_DEVELOPMENT_PROVIDER or configure a real provider's "
                "credentials.",
            )
        registry.register(MockAdapter(models=frozenset({settings.ollama_model})))
    else:
        registry.register(
            OllamaAdapter(
                client=client,
                models=frozenset({settings.ollama_model}),
                base_url=settings.ollama_base_url,
            )
        )
    if settings.anthropic_api_key:
        registry.register(
            AnthropicAdapter(
                client=client,
                api_key=settings.anthropic_api_key,
                models=frozenset({settings.anthropic_model}),
                base_url=settings.anthropic_base_url,
            )
        )
    return registry


def build_infer(
    recording_sessions: async_sessionmaker[AsyncSession],
    *,
    providers: AIProviderRegistry,
    policy: InferencePolicy | None = None,
) -> Infer:
    """Wire the only path to a model.

    A **session factory**, not a session: operational history commits on its
    own transaction so a rolled-back unit of work cannot discard the record of
    a failed call (ADR-0029). That the recorder opens its own session is an
    implementation detail of `SqlInferenceRecorder` — `Infer` sees only the
    `InferenceRecorder` port and knows nothing about transactions.
    """
    return Infer(
        providers=providers,
        prompts=load_prompt_registry(),
        recorder=SqlInferenceRecorder(recording_sessions),
        policy=policy or InferencePolicy(),
    )


def build_narrate(
    session: AsyncSession,
    *,
    recording_sessions: async_sessionmaker[AsyncSession],
    providers: AIProviderRegistry,
    source: ExplanationSource,
    publisher: EventPublisher,
    policy: InferencePolicy | None = None,
) -> Narrate:
    """Two persistence lifetimes, deliberately.

    The narration and its event share the caller's `session`, so a rolled-back
    unit of work leaves nothing behind — a narration nobody committed was
    never shown to anyone. The inference record does not: the call happened
    whatever became of the transaction that asked for it (ADR-0029).
    """
    return Narrate(
        infer=build_infer(recording_sessions, providers=providers, policy=policy),
        source=source,
        repository=SqlNarrationRepository(session),
        publisher=publisher,
        session=session,
        prompt_name=NARRATION_PROMPT,
        prompt_version=NARRATION_PROMPT_VERSION,
    )

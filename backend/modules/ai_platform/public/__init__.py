"""The AI Platform's public contract.

**Infrastructure, not a pipeline stage.** Every module before this one
answers a question about a customer's accounts. This one answers a question
about Signora itself:

> **How does Signora communicate with a model, and how does it know the
> answer is grounded?**

It does not decide *what* to say. Reasoning belongs to the AI Reasoning
Engine (M9); recommendation belongs to the Recommendation Engine (M11).

Two permanent principles govern everything exported here
(``docs/architecture/28-ai-platform.md``, ratified 2026-07-29):

**Grounding.** The platform never constrains what a model writes. It
constrains **what the model may reference.** The deterministic pipeline
defines the universe of facts and the platform treats that universe as
closed — every statement cited, every citation resolving, every number
present in cited evidence. *It may generate language. It must never
generate facts.*

**Statelessness.** Every invocation depends on exactly three inputs —
prompt, grounded evidence, configuration — and produces one grounded
structured response. No hidden memory, no cached reasoning, no implicit
conversation state. This is not a scaling preference: a grounded response
is only checkable against a *known* evidence set, so a platform that
carried facts between calls would validate against a set the model never
saw. **Statelessness is what makes grounding verifiable.**

And one that shapes what may cross this boundary
(``CLAUDE.md`` §10, ratified 2026-07-30):

**Vendor neutrality.** Business behaviour must never depend on which model
vendor served a call. Vendor selection is configuration. The platform
adapts to vendor-specific APIs internally; nothing outside it may branch on
which vendor answered.

What is exported is the **port and its vocabulary** — the contract a vendor
adapter satisfies and a consumer programs against. Note what is not here:
no vendor client, no model name, no way to ask for a vendor by name. A
consumer states the *model* it needs and the registry resolves who serves
it, which is what makes vendor neutrality structural rather than a rule
people remember.
"""

from modules.ai_platform.domain.provider import (
    AIPermanentError,
    AIPlatformError,
    AIProviderAdapter,
    AIProviderDescriptor,
    AIProviderError,
    AIProviderRegistry,
    AIRateLimitedError,
    AIRegistrationError,
    AITransientError,
    AIVendor,
    InferenceRequest,
    InferenceRequestError,
    InferenceResult,
    ModelNotRegisteredError,
)
from modules.ai_platform.domain.usage import InferenceUsage, UsageError

__all__ = [
    "AIPermanentError",
    "AIPlatformError",
    "AIProviderAdapter",
    "AIProviderDescriptor",
    "AIProviderError",
    "AIProviderRegistry",
    "AIRateLimitedError",
    "AIRegistrationError",
    "AITransientError",
    "AIVendor",
    "InferenceRequest",
    "InferenceRequestError",
    "InferenceResult",
    "InferenceUsage",
    "ModelNotRegisteredError",
    "UsageError",
]

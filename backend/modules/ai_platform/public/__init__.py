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

This surface is deliberately empty until T113. The package exists ahead of
its contents so the module boundary is enforced from the first line of code
rather than retrofitted around it.
"""

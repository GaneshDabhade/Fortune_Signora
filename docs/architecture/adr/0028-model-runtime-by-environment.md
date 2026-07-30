# ADR-0028: Model Runtime by Environment — Ollama for Development, Hosted Commercial Models for Production

**Status:** Accepted — 2026-07-30
**Amends:** [ADR-0012](0012-ai-platform-architecture.md)
**Relates to:** [ADR-0027](0027-local-first-development.md), [28-ai-platform.md](../28-ai-platform.md)

## Context

[ADR-0012](0012-ai-platform-architecture.md) ratified the AI Provider Abstraction Layer over three active vendors — **Anthropic Claude, OpenAI, Google Gemini** — with **Azure OpenAI** reserved. In its alternatives analysis it *considered and rejected* open-weight, self-hosted models:

> *"Would remove per-token vendor cost and vendor dependency entirely, but self-hosting competitive-quality models at Signora's current stage adds significant infrastructure/ops burden and, as of this decision, still trails frontier hosted models on the kind of nuanced reasoning AI Reasoning Engine depends on."*

M8 builds that abstraction layer and needs a model to develop against. **Ollama is a local runner for open-weight models — the rejected alternative.** Adopting it without a decision record would leave the repository asserting two contradictory things, and the reader two years from now would have no way to tell which one governs.

Two facts sharpen the question.

**The reasons ADR-0012 gave are production reasons.** Infrastructure and operations burden is a burden on a *deployed fleet*, not on a developer's machine. Trailing frontier models on nuanced reasoning matters when a customer reads the output; it does not matter when the thing being exercised is a validator, a retry policy, a prompt loader, or a contract suite.

**[ADR-0027](0027-local-first-development.md) made this load-bearing.** All verification is now local. A development model runtime is no longer a convenience for one engineer — it is a prerequisite for the evaluation harness, the smoke stage, offline demonstrations, and every future prompt-regression run. Without it, the milestone that introduces the first non-deterministic component would have no local way to exercise it.

## Decision

**Model runtime is determined by environment, and the two are never the same thing.**

| Environment | Runtime | Purpose |
|---|---|---|
| **Development** | **Ollama**, running locally | Prompt engineering · UI development · `make smoke` · the evaluation harness · offline demonstrations · simulation · integration testing · regression testing |
| **Production** | **Hosted commercial models** — ADR-0012's ratified vendors | Every customer-facing inference |

**M8 ships exactly two adapters:** Ollama and **Claude**. Gemini, OpenAI, Azure OpenAI and Bedrock arrive with real callers, per the roadmap's no-speculative-ports ruling.

Three consequences are binding:

**Ollama is a development dependency, never a production one.** No deployed Signora service may be configured to reach an Ollama endpoint. It is not a fallback, not a cost-reduction tier, and not a degraded mode.

**Selection is configuration, not code.** Both adapters satisfy the same `AIProviderAdapter` port, the registry is populated at the composition root from `Settings`, and **no business behaviour may branch on which vendor served a call.** Vendor identity is recorded as provenance on every inference and is never consulted for a decision — the same rule as pipeline neutrality (AC-21) in the provider layer.

**A prompt is released for the models it was evaluated against.** Developing against a small local model does not demonstrate behaviour on a frontier hosted one. The prompt manifest records evaluated `(model, dataset)` pairs, and a prompt may not be used with a model absent from that list. The gap between the two runtimes is made explicit rather than assumed away.

## What This Does Not Reverse

ADR-0012's rejection of open-weight self-hosted models **stands, unchanged, for production.** Every reason it gave still holds where it was aimed. This ADR does not adopt self-hosting; it records that a *local development runtime* is a different question that ADR-0012 never evaluated, and answers that one.

Stated plainly so the record reads as a refinement rather than a reversal:

> **ADR-0012 decided what serves customers. ADR-0028 decides what serves developers. Neither answer constrains the other.**

## Alternatives Considered

| Alternative | Why not chosen |
|---|---|
| **Develop against the production vendor (Claude) only** | Simplest record — no new runtime, no new ADR. But it makes every local test run a paid network call to a third party, which contradicts [ADR-0027](0027-local-first-development.md)'s premise that verification is local and self-contained, and puts the evaluation harness — designed to be run repeatedly on prompt changes — directly on a metered API. It also makes offline work impossible and couples the developer loop to vendor availability. |
| **A scripted fake adapter instead of a real local model** | Deterministic and free, and it is genuinely the right tool for the Security Invariants, which use recorded fixtures and must never call a model. But it cannot serve prompt engineering or the evaluation harness: a fake returns what it was told to return, so a harness run against it measures the fake. Grounding validation in particular must be exercised against *real* model output, because the failure it exists to catch — an invented quantity — is one a fake would never produce unless deliberately programmed to. **Both exist, for different jobs.** |
| **A hosted small/cheap model for development** (e.g. a mini tier) | Closer to production behaviour than a local model and cheaper than a frontier one, but still metered, still networked, still unavailable offline, and still a vendor account every contributor must hold. It solves cost without solving locality, which is the property ADR-0027 actually requires. |
| **Ollama in production as a cost tier** | Explicitly rejected. It would reintroduce exactly the operational burden ADR-0012 declined, put a materially weaker model in front of customers, and create a two-quality product where output depends on which tier served the request — unauditable from the outside and impossible to reason about in an incident. |
| **No local runtime; defer the harness to M9** | Would ship the AI Provider Port with no way to exercise it, making it the speculative port the roadmap forbids, and would leave M8's evaluation harness — the milestone's answer to Risk R-10 — untestable until the milestone after it. |

## Tradeoffs

**We gain:** a development loop that is free, offline, fast, and unmetered; an evaluation harness that can be run as often as prompts change without a cost conversation; a second adapter that proves the port is genuinely vendor-neutral rather than a description of its first implementation; and full compliance with Local-First verification.

**We give up:** behavioural fidelity between the development and production runtimes. A prompt that reads well under a local model may behave differently under Claude — this is real, it is the main risk of the decision, and it is mitigated by the manifest rule above rather than by hoping. We also take on one more adapter to maintain, and a developer prerequisite (Ollama installed and a model pulled) that must be documented.

## Risks

- **Prompt behaviour diverges between runtimes.** The central risk. Mitigated by recording evaluated `(model, dataset)` pairs in the prompt manifest and forbidding use of an unevaluated pairing (AC-70).
- **Ollama leaks into a deployed configuration.** Mitigated by configuration validation: a non-development environment configured with a local runtime is a startup error, not a warning.
- **A contributor cannot run the harness** without Ollama installed. Mitigated by documenting it as a prerequisite alongside Docker and `uv`; the deterministic tiers — the suite, the Security Invariants, `make smoke` — must remain runnable without it, since a guarantee that needs a model is not a guarantee.
- **R-01 (AI cost exposure)** is *reduced* by this decision: development traffic, which is the bulk of early inference volume, costs nothing.

## Migration Strategy

Adding a further production vendor requires a new adapter behind the existing `AIProviderAdapter` port and a configuration change — no domain-layer change, exactly as ADR-0012 specified. Removing Ollama, should a local runtime ever stop being useful, requires deleting one adapter and one configuration value; nothing depends on it structurally.

## Consequences

- [08-technology-stack.md](../08-technology-stack.md) records model runtime **by environment** rather than a single vendor list.
- The `AIProviderAdapter` contract suite runs against **both** adapters, unchanged — the keystone test, borrowed directly from the provider layer, where one shared suite across simulated and real adapters is the only mechanism that catches drift between paths.
- Ollama is documented as a development prerequisite; the deterministic gates never require it.
- ADR-0012 remains Accepted and is amended, not superseded: its vendor strategy, embeddings decision, and prompt-registry decision are untouched.

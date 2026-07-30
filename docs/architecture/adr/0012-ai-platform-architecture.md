# ADR-0012: AI Platform Architecture — Provider Abstraction, Multi-Vendor Models, Embeddings, Prompt Registry

**Status:** Accepted · **Amended by [ADR-0028](0028-model-runtime-by-environment.md) (2026-07-30):** the rejection of open-weight self-hosted models below stands **for production**, unchanged. A *local development* model runtime is a different question this ADR never evaluated; ADR-0028 answers it and adopts **Ollama for development only**. Vendor strategy, embeddings, and the prompt registry are untouched.

## Context

Principle 10 requires an AI Provider Abstraction Layer. AI Research Engine and AI Reasoning Engine ([ADR-0025](0025-module-boundary-evolution.md)) both depend on it. Signora also needs an embeddings/vector-retrieval strategy and a prompt-management approach, both left open in v1.

## Decision

An internal **AI Provider Abstraction Layer** (ports-and-adapters, per [14-ai-architecture.md](../14-ai-architecture.md)) fronting three active model vendors — **Anthropic Claude, OpenAI, Google Gemini** — with **Azure OpenAI** reserved as a future vendor. **OpenAI Embeddings** for all embedding generation, stored in **pgvector** ([ADR-0008](0008-search-and-vector-retrieval.md)). An **Internal Prompt Registry** (built, not bought) for versioned prompt template management.

## Alternatives Considered — Model Vendor Strategy

| Alternative | Why not chosen |
|---|---|
| **Single-vendor commitment (e.g., OpenAI only)** | Simpler to operate and evaluate, but creates a single point of failure for the product's core differentiator (both on vendor outage and on relative model-quality shifts, which happen frequently in this market) — and forecloses cost/latency/quality routing between vendors for different task shapes (AI Research Engine's agentic tool-use vs. AI Reasoning Engine's structured single-call reasoning may each favor a different model). |
| **A model-routing SaaS/gateway (e.g., a bought LLM gateway product)** | Would reduce the adapter-maintenance burden, but routes Signora's core AI traffic through a third party positioned exactly where Principle 10 says the domain must stay abstraction-owned, not vendor-owned — and most such gateways are themselves young, single-purpose vendors, trading one dependency for another without a clear quality benefit over a thin, self-owned abstraction. |
| **Open-weight, self-hosted models (e.g., Llama-family)** | Would remove per-token vendor cost and vendor dependency entirely, but self-hosting competitive-quality models at Signora's current stage adds significant infrastructure/ops burden and, as of this decision, still trails frontier hosted models on the kind of nuanced reasoning AI Reasoning Engine depends on — revisit if a specific cost or data-residency driver (R-02) makes it compelling later. |

## Alternatives Considered — Embeddings & Vector Store

Covered primarily in [ADR-0008](0008-search-and-vector-retrieval.md) for the vector-store half. For the embeddings model specifically:

| Alternative | Why not chosen |
|---|---|
| **Vendor-matched embeddings (Claude/Gemini-native embeddings)** | Neither Anthropic nor Google's embedding offerings were judged to have a decisive quality edge over OpenAI's for Signora's use case as of this decision, and standardizing on one embeddings model (rather than one per active LLM vendor) keeps the Knowledge Graph's and AI Research Engine's vector space consistent regardless of which model vendor handled a given reasoning/research call — mixing embedding models would fragment semantic search results in ways that are hard to reason about. |
| **Open-source embedding models (self-hosted)** | Would remove per-call cost, but adds hosting/serving infrastructure for a capability (embeddings generation) that isn't itself Signora's differentiation — the differentiation is in what's built on top (Knowledge Graph retrieval, AI Research Engine's context assembly), not the embedding model itself. |

## Alternatives Considered — Prompt Management

| Alternative | Why not chosen |
|---|---|
| **Bought prompt-ops SaaS (e.g., a third-party prompt versioning/testing platform)** | Prompt content is domain IP — see [14-ai-architecture.md](../14-ai-architecture.md)'s rationale. Routing it through a third-party platform would put a vendor between Signora and the artifact most directly responsible for AI output quality, for a capability (versioning, review) that Git and code review already provide. |
| **Unversioned prompts embedded inline in code with no registry concept** | Rejected — provenance (which prompt version produced which result) is required for debugging and future evaluation ([16-architecture-risks.md](../16-architecture-risks.md) R-10), and inline, unversioned prompts would make that untraceable. |

## Tradeoffs

**We gain:** resilience to any single AI vendor's outage or quality regression, cost/latency/quality routing flexibility, a consistent embedding space across all modules, and prompt IP that stays fully owned, versioned, and code-reviewed.

**We give up:** the operational simplicity of a single-vendor integration (three adapters to maintain and evaluate instead of one) and a bought prompt-ops platform's out-of-the-box testing/analytics UI (replaced by the Internal Prompt Registry's simpler, code-native equivalent, sufficient until Risk R-10's evaluation harness is built).

## Risks

- **R-01** (AI cost exposure) is directly relevant — three vendors means three cost surfaces to govern.
- **R-05** (AI prompt data-classification policy) and **R-10** (no evaluation methodology) are the two most consequential open risks against this decision — see [16-architecture-risks.md](../16-architecture-risks.md).
- Vendor data-retention/training terms must be re-verified at each contract renewal for all three vendors ([10-security.md](../10-security.md)).

## Migration Strategy

Adding, removing, or reweighting a model vendor requires only a new/changed adapter behind the existing AI Provider Port and a routing-configuration change — no domain-layer changes in AI Research Engine or AI Reasoning Engine. Azure OpenAI's addition (when triggered by a specific enterprise data-residency or existing-commitment need) follows this same path.

## Consequences

- AI Research Engine and AI Reasoning Engine each maintain independent model-routing configuration against the shared AI Provider Port.
- All embeddings, regardless of which module or which LLM vendor handled the associated reasoning/research call, use OpenAI Embeddings and are stored in pgvector.
- Prompt templates live in the Internal Prompt Registry, versioned in Git, reviewed like code, with every AI result recording its prompt version.

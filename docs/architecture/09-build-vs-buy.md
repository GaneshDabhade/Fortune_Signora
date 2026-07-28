# 09 — Build vs. Buy

> Status: **Living document — Architectural Constitution — RATIFIED**
> Audience: All engineers, EMs, and technical stakeholders at Signora
> Revision: **v2** — updated matrix per the Architecture Review Board's final ratification. See [ADR-0025](adr/0025-module-boundary-evolution.md) and [ADR-0011](adr/0011-background-processing-and-event-bus-transport.md) for the two changes this revision makes to the boundary.

## Purpose

This document is the canonical decision record for what Signora builds in-house versus buys from vendors, implementing Principles 14 and 15 from [02-principles.md](02-principles.md).

## The Core Test

> **Build it only if it is Signora's competitive advantage. Buy it if a mature vendor already solves it well.**

## We Build

These map directly onto the thirteen core intelligence modules in [04-modules.md](04-modules.md):

| Capability | Module | Why it's a competitive advantage |
|---|---|---|
| Knowledge Graph | Knowledge Graph | Entity resolution/graph quality across providers is a core data-moat capability. |
| Provider Platform | Provider Platform | Reliably, safely, and cost-effectively operating dozens of provider integrations at scale is explicit product scope ("multi-provider intelligence") and a genuine operational moat, not incidental plumbing — promoted from infrastructure to a build item in this revision. |
| Provider Normalization | Provider Normalization | Normalization quality across many providers is hard-won domain IP. |
| Observation Engine | Observation Engine | The provenance-tracked factual substrate is unique to how Signora reasons about companies. |
| Business Event Engine | Business Event Engine | Business-event taxonomy and detection quality directly determine signal quality — this is domain IP, consolidated in this revision from the prior Event Engine / Business Events split. |
| Signal Engine | Signal Engine | Scoring/correlation models are the proprietary "so what" layer no vendor sells off-the-shelf for this domain. |
| Buying Score Engine | Buying Score Engine | Composite, time-decayed account-level propensity scoring is Signora's synthesized point of view on buying readiness — new in this revision, previously implicit inside Opportunity Engine's qualification logic. |
| Opportunity Engine | Opportunity Engine | Qualification logic encodes Signora's product point of view on what counts as a real opportunity. |
| AI Research Engine | AI Research Engine | Agentic, deep-research synthesis over an account is a direct product differentiator — new in this revision, split out of what was previously a single AI Reasoning module. |
| AI Reasoning Engine | AI Reasoning Engine | The structured reasoning/explanation layer over opportunities is the product's core AI differentiation. |
| Recommendation Engine | Recommendation Engine | Turning reasoning into a specific, prioritized action is the last mile of the product's value. |
| Timeline | Timeline | The chronological narrative view is a primary user-facing product surface built on proprietary data. |
| Revenue Intelligence Platform | Revenue Intelligence Platform | The composed, workspace-level product surface is what customers actually buy Signora for. |

## We Buy

| Capability | Why it's commodity, not advantage | Vendor |
|---|---|---|
| Authentication | Identity/session management is a solved, security-critical problem. | Better Auth — [ADR-0010](adr/0010-identity-and-access.md) |
| Authorization | Fine-grained permission evaluation is well served by a mature policy engine. | Casbin — [ADR-0010](adr/0010-identity-and-access.md) |
| Billing | Subscription/usage billing and payment compliance (PCI) carry high liability if self-built. | Stripe — [ADR-0016](adr/0016-billing.md) |
| Notifications | Cross-channel notification delivery infrastructure is commodity. | Novu — [ADR-0017](adr/0017-notifications.md) |
| Email | Transactional delivery/deliverability reputation is a solved, specialized problem. | Resend — [ADR-0015](adr/0015-communication-email-and-calendar-integrations.md) |
| Search | Full-text/faceted search infrastructure is commodity infrastructure, distinct from the domain logic of what's indexed. | Meilisearch — [ADR-0008](adr/0008-search-and-vector-retrieval.md) |
| Monitoring | APM, tracing, and error monitoring are solved, specialized problems. | OpenTelemetry + Grafana + Sentry — [ADR-0018](adr/0018-monitoring-and-observability.md) |
| Analytics | Product/usage analytics infrastructure is commodity. | PostHog — [ADR-0019](adr/0019-analytics.md) |
| Feature Flags | Progressive rollout/experimentation infrastructure is commodity. | Flagsmith — [ADR-0020](adr/0020-feature-flags.md) |
| Object Storage | Blob storage is undifferentiated infrastructure. | MinIO (S3-compatible) / AWS S3 — [ADR-0009](adr/0009-object-storage.md) |
| Workflow Orchestration | Durable, resumable, long-running workflow execution is a solved distributed-systems problem with significant correctness pitfalls if built in-house. | Temporal (future path) — [ADR-0011](adr/0011-background-processing-and-event-bus-transport.md) |
| Background Queue | Job queue execution/retry/scheduling semantics are commodity. | Redis + ARQ — [ADR-0011](adr/0011-background-processing-and-event-bus-transport.md) |

**What changed in this revision:** Workflow Orchestration and Background Queue are now explicit "never build" line items. This closes a gap in v1, where async processing was named as a principle (Principle 13) but the queue/orchestration mechanism itself was left ambiguous enough that a team could plausibly have hand-rolled one. It is now unambiguous: Signora buys/adopts Redis+ARQ (and, for durable multi-step workflows, Temporal) rather than building bespoke job scheduling, retry, or workflow-state-machine logic.

## Where the Line Gets Subtle

- **AI/LLM model providers are bought; AI Research Engine and AI Reasoning Engine (the modules) are built.** We do not train or host foundation models. We build the research orchestration, reasoning orchestration, prompt design, and domain logic on top of bought models (Claude, OpenAI, Gemini), accessed through the AI Provider Abstraction Layer — see [14-ai-architecture.md](14-ai-architecture.md).
- **Company intelligence data providers are bought (Apollo, CoreSignal, BuiltWith, Similarweb, NeverBounce); Provider Platform and Provider Normalization are built.** We buy access to raw data; we build the operational orchestration of many providers and the normalization/resolution logic that turns their output into Signora's proprietary graph.
- **Search infrastructure (Meilisearch) and vector infrastructure (pgvector) are bought/adopted; what gets indexed, embedded, and how it's ranked is built.** Buying the retrieval engine does not mean buying the domain logic that decides what's relevant.
- **The background job queue (Redis + ARQ) and future workflow engine (Temporal) are bought/adopted; the specific pipeline stages that run on top of them (all thirteen build modules) are built.** The distinction is infrastructure-for-running-work vs. the-work-itself.
- **CRM/communication/email/calendar targets are integration surfaces, not build items.** Salesforce, HubSpot, Pipedrive, Zoho, Slack, Teams, Gmail, Microsoft 365, Google Calendar, and Outlook Calendar are all accessed through the Integration Abstraction Layer (Principle 11) — see [13-integrations.md](13-integrations.md). None of this is "built" in the competitive-advantage sense; the adapters are necessary connective tissue, not differentiation.
- **Authorization (Casbin) is bought as a policy-evaluation engine; Workspace & Tenancy's data model and RLS enforcement are built**, because the *concept* of Workspace as tenancy root and its enforcement in schema is inherent to Signora's own multi-tenant design — see [11-tenancy.md](11-tenancy.md) and [ADR-0010](adr/0010-identity-and-access.md).

## Process to Change a Build/Buy Decision

Unchanged from v1 — see the RFC process below, required for any reclassification:

1. State explicitly why the current classification is wrong.
2. Evaluate against the Core Test.
3. Get sign-off from the architecture owner.
4. Update this document, [04-modules.md](04-modules.md), and [08-technology-stack.md](08-technology-stack.md) together, plus a new or amended ADR.

## Design Rationale

Making the build list exactly equal to the thirteen core modules removes ambiguity. The two additions this revision makes to the "never build" list (Workflow Orchestration, Background Queue) close the one place v1 left room for an engineer to reasonably build something that should have been bought — a direct lesson from the Review Board's stack ratification process.

## Best Practices

- When starting any new work, check: is this capability in the "We Build" table? If not, look for a vendor before writing code.
- Treat vendor selection with the same rigor as a build decision — evaluate for RLS/workspace-scoping compatibility and abstraction-layer compatibility before committing.

## Anti-Patterns

- Building a bespoke job scheduler or workflow engine instead of using ARQ/Temporal.
- Building a bespoke permission-check system instead of using Casbin.
- Treating AI Research Engine or AI Reasoning Engine as places to also reimplement generic LLM plumbing (retries, streaming, tool-calling protocol handling) that the AI Provider Abstraction Layer's adapters should own instead.

## Tradeoffs

| Choice | We gain | We give up |
|---|---|---|
| Buy commodity infra (expanded to explicitly include workflow orchestration and queueing) | Speed, lower risk, less maintenance, avoids correctness pitfalls of hand-rolled distributed job/workflow systems | Vendor lock-in risk, recurring cost (accepted deliberately) |
| Build exactly the thirteen-module pipeline | Full control over the actual differentiator | Everything else takes longer to change (acceptable) |

## Future Evolution

- As Signora matures, a currently-bought capability might become worth building only if it becomes a genuine differentiator — this goes through the RFC process, not organic scope creep.
- Temporal's adoption (currently scoped to AI Research Engine's agentic workflows) may expand to other multi-step processes as they emerge — see [12-scalability.md](12-scalability.md) triggers.

## Decision Summary

Signora builds exactly its thirteen ratified core intelligence modules (plus the Workspace & Tenancy foundation) and buys everything else — including, as clarified in this revision, workflow orchestration and background queueing — with every vendor selection backed by a dedicated ADR and any future reclassification requiring an explicit RFC.

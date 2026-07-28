# 17 — Future Recommendations

> Status: **Living document — Architectural Constitution — RATIFIED**
> Audience: All engineers, EMs, and technical stakeholders at Signora
> New in **v2**.

## Purpose

This document is the Architecture Review Board's forward-looking roadmap: the specific, prioritized architectural investments recommended beyond what this revision ratifies, organized by horizon. It exists to separate "what we decided now" (the rest of this document set) from "what we should deliberately plan for next" — so the ten-year mandate behind this documentation package has a concrete near-term expression, not just a set of present-tense decisions.

## How to Read This Document

Each recommendation states: what to do, why it matters, what triggers it (if evidence-based rather than time-based), and which existing document it extends. Nothing here is ratified as done — these are the Board's prioritized recommendations for what engineering leadership should schedule next.

## Horizon 1 — Before General Availability

These are prerequisites, not optional polish, given the risks in [16-architecture-risks.md](16-architecture-risks.md).

1. **Build the AI evaluation harness (resolves R-10).** Golden test sets for both AI Research Engine and AI Reasoning Engine, human-review sampling, and regression testing wired into CI for prompt template changes. This is the single highest-leverage investment available for the product's core differentiator — see [14-ai-architecture.md](14-ai-architecture.md).
2. **Define AI spend governance (resolves R-01).** Per-workspace and platform-wide budget ceilings and alerting before AI Research Engine is enabled broadly.
3. **Load-test RLS, Meilisearch, and pgvector at target scale (resolves R-03, R-08).** Synthetic data generation to millions-of-companies scale, validating or revising the partitioning plan in [12-scalability.md](12-scalability.md) before it's discovered in production.
4. **Set up connection pooling (RDS Proxy) and per-stage ARQ worker pools before scaling worker concurrency**, per [12-scalability.md](12-scalability.md) — sequencing this before load arrives, not after.
5. **Escalate PII/retention policy and AI prompt data-classification policy to Legal/Compliance (resolves R-04, R-05).** Engineering cannot resolve these unilaterally; they should be scheduled as a cross-functional workstream now, given the lead time formal policy work requires.

## Horizon 2 — First 6–12 Months Post-GA

1. **AI Research Engine → Temporal migration.** Once production data confirms the trigger conditions in [12-scalability.md](12-scalability.md) (research tasks exceeding ARQ's practical timeout ceiling, or measurable job loss on worker restarts), migrate AI Research Engine's agentic workflows to Temporal for durable, resumable, checkpointed execution. This was scoped deliberately as a *future* decision in [ADR-0011](adr/0011-background-processing-and-event-bus-transport.md) rather than adopted upfront, to avoid paying Temporal's operational complexity before the workload justifies it — this recommendation is the trigger check, not a commitment to migrate on a calendar date.
2. **Formalize the cross-workspace admin/support access model (resolves R-06).** Design before customer-facing support tooling is built reactively.
3. **Establish latency SLOs from real telemetry (resolves R-07).** Feed into autoscaling policy and alerting thresholds.
4. **Expand the AI Provider Abstraction Layer's routing logic from static configuration to cost/latency/quality-aware dynamic routing**, once enough production data exists across Claude/OpenAI/Gemini to make routing decisions data-driven rather than configured by intuition — see [ADR-0012](adr/0012-ai-platform-architecture.md).
5. **Evaluate Bombora for intent-data ingestion** once Buying Score Engine's model formally calls for third-party intent as an input signal — see [ADR-0013](adr/0013-company-intelligence-provider-strategy.md).

## Horizon 3 — Scale-Driven, Evidence-Triggered

These are explicitly *not* scheduled on a calendar — they activate only when their trigger condition in the linked document is actually observed, per Principle 1's rationale against premature complexity.

1. **Module extraction** — Provider Platform and/or AI Research Engine are the leading candidates; see the concrete triggers in [12-scalability.md](12-scalability.md).
2. **Event transport evolution** — from Postgres-outbox-relayed-to-Redis/ARQ to a dedicated broker (Kafka/NATS/SQS), if queue depth and fan-out volume exceed what ECS-autoscaled ARQ workers can drain within SLA — see [06-events.md](06-events.md), [12-scalability.md](12-scalability.md).
3. **Database partitioning/read-replica routing** for the largest tenants, per [12-scalability.md](12-scalability.md), before ever considering database-per-tenant.
4. **Vector/search infrastructure migration** off pgvector/Meilisearch to a category-leader dedicated system, only if Horizon 1's load testing (or later production experience) actually surfaces the ceiling both [ADR-0008](adr/0008-search-and-vector-retrieval.md) and Risk R-08 anticipate as possible.

## Strategic Recommendations (Not Yet Triggers, Worth Planning For)

1. **Multi-region / data-residency architecture (relates to R-02).** Do not build this speculatively, but audit Workspace & Tenancy's schema and the event envelope (`workspace_id` as the sole scoping key) now for anything that would make region-pinning a workspace to a specific physical location structurally difficult to retrofit later. A cheap audit now avoids an expensive redesign under enterprise-deal pressure later.
2. **SOC 2 (or equivalent) compliance program (relates to R-12).** A program, not an architecture decision, but the observability, secrets-management, and tenant-isolation choices ratified in this revision were deliberately kept audit-compatible — engineering leadership should schedule the formal program in parallel with, not after, enterprise GTM ramp.
3. **Casbin policy model maturity.** As the permission matrix grows beyond initial RBAC into more nuanced enterprise requirements (custom roles, resource-level permissions), revisit whether Casbin's ABAC model needs to be adopted more fully — tracked against [ADR-0010](adr/0010-identity-and-access.md), not yet urgent.
4. **Provider Platform as a genuine internal platform.** As provider count grows past the initial five, consider whether Provider Platform needs a self-service internal interface (for adding/configuring providers without a code deploy) — currently out of scope, worth revisiting once provider count roughly doubles.
5. **Cost-aware AI routing as a product feature, not just an infrastructure optimization.** Once multi-vendor routing (Horizon 2, item 4) is mature, consider whether workspace-tier-aware AI quality/cost tradeoffs (e.g., a lower-cost model tier for lower-paying plans) becomes a deliberate product/pricing lever — a business decision this Board flags as an option, not a recommendation to build.

## What This Board Explicitly Did Not Recommend

Worth stating explicitly, since a review board's restraint is as much a signal as its recommendations:

- **No move to microservices** at any horizon above — nothing in this revision changes Principle 1's evidence-based extraction bar. Provider Platform and AI Research Engine are extraction *candidates*, not extraction *plans*.
- **No premature multi-region build-out** — flagged as a risk to audit against (R-02), not a project to schedule now.
- **No replacement of pgvector/Meilisearch pre-emptively** — both are adopted with explicit, documented exit paths, exercised only if load testing or production evidence actually demands it.
- **No abandonment of the Postgres-outbox-as-source-of-truth pattern** even as Redis/ARQ and, later, Temporal are layered on top — durability guarantees stay anchored to PostgreSQL throughout every horizon above.

## Design Rationale

Structuring recommendations by horizon and by "evidence-triggered vs. scheduled" keeps this document honest about the difference between things that must happen before GA (Horizon 1), things worth planning for without over-committing (Strategic Recommendations), and things that should explicitly *not* happen until specific evidence appears (Horizon 3). This mirrors the same discipline [12-scalability.md](12-scalability.md) applies to scaling decisions, applied to the roadmap as a whole.

## Best Practices

- Revisit this document at every quarterly architecture review alongside [16-architecture-risks.md](16-architecture-risks.md).
- Treat Horizon 1 items as blocking GA readiness, not a nice-to-have backlog.
- When a Horizon 3 trigger fires, write the extraction/migration as its own ADR referencing this document, rather than treating it as a routine engineering task.

## Anti-Patterns

- Scheduling a Horizon 3 item on a calendar instead of waiting for its trigger.
- Treating Horizon 1 items as deferrable because they're not customer-facing features.
- Building multi-region or a compliance program reactively, under deal pressure, instead of per the audit-now/build-when-needed sequencing recommended above.

## Future Evolution

This document itself should be revised at each quarterly architecture review: completed items move to a "delivered" appendix (to be added when the first item completes), new risks from [16-architecture-risks.md](16-architecture-risks.md) should generate corresponding recommendations here, and horizons should be re-evaluated as the product and customer base evolve.

## Decision Summary

The Board recommends five Horizon-1 investments before GA (AI evaluation harness, AI spend governance, load testing at scale, connection pooling/worker partitioning, and escalating PII/AI-data-classification policy), a set of evidence-triggered Horizon-2 and Horizon-3 investments tied directly to the trigger conditions already defined in [12-scalability.md](12-scalability.md) and [ADR-0011](adr/0011-background-processing-and-event-bus-transport.md), and explicitly declines to recommend microservices migration, pre-emptive multi-region build-out, or pre-emptive search/vector infrastructure replacement at this time.

# ADR-0025: Module Boundary Evolution — Provider Platform, Business Event Engine, Buying Score Engine, AI Research/Reasoning Split

**Status:** Accepted

## Context

v1's architecture ([04-modules.md](../04-modules.md)) defined eleven core modules plus one `[INFERRED]` foundational module. The final, ratified build-vs-buy matrix supplied for this revision names thirteen core modules with different boundaries: **Provider Platform** and **Buying Score Engine** are new; **Event Engine** and **Business Events** are consolidated into **Business Event Engine**; **AI Reasoning** is split into **AI Research Engine** and **AI Reasoning Engine**; **Revenue Intelligence** is renamed **Revenue Intelligence Platform**. This ADR is the single record of the reasoning behind every one of these changes, referenced throughout [04-modules.md](../04-modules.md), [05-module-dependencies.md](../05-module-dependencies.md), [06-events.md](../06-events.md), and [09-build-vs-buy.md](../09-build-vs-buy.md).

## Decision

Adopt the thirteen-module map exactly as specified in the ratified build list, with the following four boundary changes relative to v1, each justified independently below.

## Change 1: Provider Platform Promoted to a Core Module

**v1 state:** the Provider Abstraction Layer (Principle 9) was infrastructure — a shared kernel in `platform/provider-abstraction/`, not a bounded context with its own domain model.

**Decision:** Provider Platform becomes a full core module, owning the provider registry, credentials, quotas, scheduling, cost tracking, and health monitoring for every data provider.

**Alternatives considered:**

| Alternative | Why not chosen |
|---|---|
| Keep Provider Platform as infrastructure only (v1's model) | Reliably operating five-plus provider integrations at scale — each with distinct rate limits, auth schemes, cost structures, and failure modes — is nontrivial domain logic in its own right (scheduling policy, quota allocation across workspaces, circuit-breaking), not merely plumbing. Treating it as "just infrastructure" under-resourced a capability the product explicitly depends on ("multi-provider intelligence" is named project scope). |
| Fold Provider Platform's responsibilities into Provider Normalization | Would conflate two genuinely different concerns — "get data in reliably and cost-effectively" (operational/vendor-management) versus "shape data correctly" (domain transformation) — that change for different reasons and at different rates, the same argument that justifies keeping Provider Normalization and Knowledge Graph separate. |

**Consequence:** Provider Platform is now upstream of Provider Normalization in the pipeline ([04-modules.md](../04-modules.md), [05-module-dependencies.md](../05-module-dependencies.md)), publishing `provider.payload.received` rather than Provider Normalization owning ingestion directly.

## Change 2: Event Engine + Business Events Consolidated into Business Event Engine

**v1 state:** two separate bounded contexts — Event Engine (detection/classification runtime) and Business Events (taxonomy/schema ownership) — justified in v1 as changing at different rates (taxonomy = product/domain research; detection = data engineering).

**Decision:** Consolidate into a single Business Event Engine, with taxonomy as an internal concern.

**Alternatives considered:**

| Alternative | Why not chosen |
|---|---|
| Keep the v1 split | The ratified build list names one module ("Business Event Engine"), and on reflection the v1 split's stated rationale (different rates of change) does not, by itself, justify the coordination overhead of a full bounded-context boundary (separate events, separate public contracts, cross-module dependency to resolve for every detection) between two concerns that are used together on every single detection operation. A versioned internal taxonomy (tracked via `event_version`-style internal versioning, not a cross-module event contract) achieves the same "these change at different rates" property without the boundary cost. |

**Consequence:** `business_event_type.published` becomes an internal-to-the-module signal rather than a cross-module event with external consumers; Signal Engine's only upstream dependency is `business_event.detected` ([06-events.md](../06-events.md)).

## Change 3: Buying Score Engine Introduced

**v1 state:** no explicit account-level aggregate scoring module; Opportunity Engine implicitly performed qualification directly from signals.

**Decision:** Introduce Buying Score Engine between Signal Engine and Opportunity Engine, owning composite, time-decayed, cross-signal account-level scoring.

**Alternatives considered:**

| Alternative | Why not chosen |
|---|---|
| Keep composite scoring inside Opportunity Engine (v1's implicit model) | Conflates two distinct judgments — "how strong is this individual signal" (a per-event, largely stateless computation, Signal Engine's job) and "what is this account's overall propensity to buy right now, given everything we know and how it's decayed over time" (a stateful, portfolio-level judgment) — inside one module. This made Opportunity Engine responsible for both qualification *and* the scoring model feeding it, two concerns with different iteration cycles and different evaluation criteria (a scoring-model change is a data-science-style iteration; a qualification-threshold change is a product/GTM-style iteration). |
| Fold composite scoring into Signal Engine instead | Signal Engine's job is per-signal, not cross-signal/account-level aggregation with time-decay — a different computational shape (portfolio aggregation over time vs. single-event scoring) that warrants its own module boundary for the same reason Change 1 and the original Provider Normalization/Knowledge Graph split were justified. |

**Consequence:** Opportunity Engine's qualification logic now consumes `buying_score.updated` rather than reasoning over raw signals directly, giving each module (Signal Engine's per-signal scoring, Buying Score Engine's account-level aggregation, Opportunity Engine's qualification policy) an independently evolvable model.

## Change 4: AI Reasoning Split into AI Research Engine and AI Reasoning Engine

**v1 state:** a single AI Reasoning module handling all AI-driven analysis over opportunities.

**Decision:** Split into AI Research Engine (agentic, multi-step, open-ended research) and AI Reasoning Engine (structured, single-call reasoning), with AI Research Engine as an optional, non-blocking enrichment input to AI Reasoning Engine.

**Alternatives considered:**

| Alternative | Why not chosen |
|---|---|
| Keep one AI Reasoning module (v1's model) | The two workloads have fundamentally incompatible operating characteristics — latency (seconds vs. potentially minutes), cost predictability (bounded vs. variable), and failure/retry semantics (cheap retry-from-scratch vs. needing resumability) — detailed in [14-ai-architecture.md](../14-ai-architecture.md)'s comparison table. Conflating them meant every reasoning call paid research's latency tax, or research was cut for the sake of reasoning's speed requirement, either way underserving one workload to protect the other. |
| Make AI Research Engine a hard blocking dependency of AI Reasoning Engine | Would guarantee every reasoning result benefits from research, but would tie the fast, common-case reasoning path's latency to the slow, variable-cost research path's completion time — an unacceptable product-latency regression for the common case, addressed instead by the explicit non-blocking/timeout design in [05-module-dependencies.md](../05-module-dependencies.md). |

**Consequence:** This is the one deliberate non-blocking relationship in an otherwise strictly synchronous-or-async dependency graph ([05-module-dependencies.md](../05-module-dependencies.md)) — documented explicitly rather than left implicit, and the leading candidate for Temporal migration ([ADR-0011](0011-background-processing-and-event-bus-transport.md)) given AI Research Engine's agentic, potentially long-running shape.

## Tradeoffs (System-Wide)

**We gain:** module boundaries that map cleanly onto genuinely different rates of change, computational shapes, and operational profiles — Provider Platform's vendor-operations concerns, Business Event Engine's consolidated-but-versioned taxonomy, Buying Score Engine's portfolio-level aggregation, and AI Research/Reasoning's split latency/cost profiles are each now independently evolvable and independently scalable ([12-scalability.md](../12-scalability.md)).

**We give up:** two more modules than v1's eleven (thirteen total), meaning two more sets of `domain/application/infrastructure/interface/public` boundaries, two more sets of tests, and two more entries in the dependency graph to reason about — accepted because each addition is justified by a concrete operational or product argument above, not added speculatively.

## Risks

Module-boundary changes of this scope, made before any of the eleven-module v1 design was implemented in code, carry lower risk than they would post-implementation (no migration of existing code is required) — this revision is a design-time correction, not a refactor of running systems. The main residual risk is that Business Event Engine's consolidation (Change 2) could be revisited if the taxonomy ever needs independent product ownership (e.g., a dedicated taxonomy-curation team) — noted as a reversible decision, not treated as permanently settled.

## Migration Strategy

Because this ADR is adopted before implementation begins, "migration" here means: [04-modules.md](../04-modules.md) through [07-data-flow.md](../07-data-flow.md) and [09-build-vs-buy.md](../09-build-vs-buy.md) are updated in this same revision to reflect the thirteen-module map directly, with no interim dual-documentation period. If a future boundary change is proposed (e.g., re-splitting Business Event Engine), it follows the standard RFC process in [01-overview.md](../01-overview.md) and would be recorded as a new ADR superseding the relevant portion of this one.

## Consequences

- [04-modules.md](../04-modules.md) is revised to v2 with thirteen core modules plus Workspace & Tenancy.
- [05-module-dependencies.md](../05-module-dependencies.md), [06-events.md](../06-events.md), and [07-data-flow.md](../07-data-flow.md) reflect the new pipeline order: Provider Platform → Provider Normalization → Knowledge Graph → Observation Engine → Business Event Engine → Signal Engine → Buying Score Engine → Opportunity Engine → {AI Research Engine, AI Reasoning Engine} → Recommendation Engine, with Timeline and Revenue Intelligence Platform as read/composition modules.
- [09-build-vs-buy.md](../09-build-vs-buy.md)'s "We Build" table is updated to the thirteen-module list.

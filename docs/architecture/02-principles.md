# 02 — Architecture Principles

> Status: **Living document — Architectural Constitution — RATIFIED**
> Audience: All engineers, EMs, and technical stakeholders at Signora
> Note: the fifteen principles below are unchanged in v2. The module list they reference has evolved from eleven to thirteen core modules — see [04-modules.md](04-modules.md) and [ADR-0025](adr/0025-module-boundary-evolution.md) — and the full technology stack implementing these principles is now fully ratified in [08-technology-stack.md](08-technology-stack.md) and `docs/architecture/adr/`.

## Purpose

This document enumerates the non-negotiable architectural principles that govern every design decision at Signora. These principles were agreed upon as the foundation of the system; this document exists to make them explicit, explain the rationale behind each, and give engineers a shared standard against which to evaluate new proposals.

Every other document in this set is a *consequence* of these principles, not an independent source of truth. If a proposal conflicts with a principle here, the proposal must either change or the principle must be explicitly amended through the RFC process described in [01-overview.md](01-overview.md).

## Responsibilities

- State each principle clearly and unambiguously.
- Explain the rationale ("why") behind each principle, not just the rule.
- Give concrete guidance on what compliance and violation look like.
- Serve as the evaluation checklist for architecture reviews and RFCs.

## The Principles

### 1. Modular Architecture, NOT Microservices

Signora is built as a **single deployable modular monolith** composed of well-isolated modules (bounded contexts), not as a distributed system of independently deployed microservices.

**Rationale:** Microservices trade simplicity for independent scalability and deployability. At Signora's current stage, the dominant cost is *cognitive and operational overhead* (network calls, distributed transactions, service discovery, versioning, on-call surface area), not compute isolation. A modular monolith gives us most of the benefits of clear boundaries (see Principle 5) with none of the distributed-systems tax, while remaining a stepping stone to microservices later if and when it is justified by real scaling data.

See [03-system-architecture.md](03-system-architecture.md) for the resulting system shape.

### 2. Domain-Driven Design (DDD)

Modules are defined around **bounded contexts** derived from the business domain (revenue intelligence), not around technical layers (e.g., not a "controllers module" or a "database module"). Each module owns its own ubiquitous language, aggregates, and domain rules.

**Rationale:** Signora's value is in domain complexity (observations → events → signals → opportunities → reasoning), not incidental technical complexity. DDD keeps that complexity organized around the concepts domain experts and engineers both reason about, and prevents the "big ball of mud" failure mode of monoliths.

See [04-modules.md](04-modules.md) for the bounded context map.

### 3. Event-Driven Communication Between Modules

Modules communicate with each other primarily through **asynchronous domain events** published to an internal event bus, not through direct synchronous calls into each other's internals.

**Rationale:** Event-driven communication keeps modules decoupled at the boundary even though they share a process and a database. It is also a natural fit for Signora's pipeline shape (each stage reacts to the previous stage completing), and it is the mechanism that makes Principle 5 (future extraction) realistic later.

See [06-events.md](06-events.md) for the event catalog and [05-module-dependencies.md](05-module-dependencies.md) for what synchronous access is still permitted.

### 4. Clean Architecture Inside Every Module

Every module internally follows **Clean Architecture** (a.k.a. Hexagonal/Ports-and-Adapters): domain logic at the center, application/use-case orchestration around it, and infrastructure (DB, HTTP, providers, AI vendors) at the edge, depending inward only.

**Rationale:** This keeps domain logic testable and vendor-agnostic, and is what makes Principles 9–11 (provider, AI, and integration abstraction layers) enforceable rather than aspirational. It also means every module looks structurally familiar to every engineer, regardless of which module they're in.

See [15-project-structure.md](15-project-structure.md) for the concrete folder layout this produces.

### 5. Service Boundaries That Allow Future Extraction

Module boundaries are drawn as if each module *could* become an independently deployed service in the future, even though today it will not be. Modules do not share internal state, do not reach into each other's database tables directly, and communicate only through events and well-defined public interfaces.

**Rationale:** This is the principle that reconciles Principle 1 (monolith now) with future optionality (services later). Drawing boundaries this way costs little today and preserves the option to extract a module (e.g., AI Reasoning, or a high-throughput module like Observation Engine) without a rewrite, if and when independent scaling or deployment is justified.

See [12-scalability.md](12-scalability.md) for the extraction playbook this enables.

### 6. Single PostgreSQL Database

Signora runs on a **single PostgreSQL database** shared by all modules, rather than a database-per-module.

**Rationale:** A single database avoids distributed-transaction and cross-database consistency problems entirely, dramatically simplifies operations, and is sufficient for our current and foreseeable scale (see [12-scalability.md](12-scalability.md)). Module isolation is enforced at the schema/access-pattern level (Principle 5), not the database-instance level.

### 7. Shared Database Using Row-Level Security (RLS)

Multi-tenant data isolation is enforced using **PostgreSQL Row-Level Security**, not application-code-only filtering and not database-per-tenant or schema-per-tenant isolation.

**Rationale:** RLS pushes tenant isolation down to the data layer itself, so a bug in application-layer filtering cannot leak data across workspaces. It scales to a large number of tenants without the operational overhead of per-tenant databases/schemas.

See [11-tenancy.md](11-tenancy.md) for the full model and [10-security.md](10-security.md) for the security posture this supports.

### 8. Workspace-Based Tenancy

The unit of tenancy is the **Workspace**. Every piece of tenant-owned data belongs to exactly one workspace, and every request executes in the context of exactly one workspace.

**Rationale:** B2B sales teams operate as workspace-scoped units (a company's sales org). Workspace as the tenancy root is the simplest model that matches how the product is actually used and sold.

See [11-tenancy.md](11-tenancy.md).

### 9. Provider Abstraction Layer

All external data providers (firmographic, hiring, news, technographic, etc.) are accessed through a **provider abstraction layer** — a set of ports defined by the domain, implemented by provider-specific adapters. No module outside the abstraction's adapters may depend on a specific provider's API/SDK.

**Rationale:** Providers change, get added, get dropped, or get replaced for cost/coverage reasons. Abstracting them protects the domain (Provider Normalization, Knowledge Graph, etc.) from vendor churn and enables running multiple providers per data category simultaneously.

See [13-integrations.md](13-integrations.md).

### 10. AI Provider Abstraction Layer

All LLM/AI vendor access (for AI Reasoning and any other module that uses AI) goes through an **AI provider abstraction layer**, so the domain never depends on a specific model vendor's SDK or API shape.

**Rationale:** Model vendors and even specific models change rapidly and are frequently swapped for cost, quality, or capability reasons. This principle keeps Signora able to adopt the best available model without domain-level rewrites.

See [14-ai-architecture.md](14-ai-architecture.md).

### 11. Integration Abstraction Layer

All outbound and inbound third-party system integrations (CRM sync, calendar, email, notifications, etc., where applicable) go through an **integration abstraction layer**, following the same ports-and-adapters approach as the provider and AI abstraction layers.

**Rationale:** Consistency with Principles 9 and 10 — the domain should never be coupled to a specific third-party system's API.

See [13-integrations.md](13-integrations.md).

### 12. Internal Event Bus

Modules publish and subscribe to domain events through a single **internal event bus** abstraction, decoupled from whatever underlying transport implements it (in-process dispatch, transactional outbox, etc.).

**Rationale:** This is the concrete mechanism behind Principle 3. Centralizing it behind one abstraction means the underlying transport can evolve (see [12-scalability.md](12-scalability.md)) without every module changing.

See [06-events.md](06-events.md).

### 13. Async Processing Using Background Workers

Work that is not required to complete within the request/response cycle (provider polling, normalization, observation/event/signal/opportunity pipeline processing, AI reasoning calls, recommendation generation) is performed by **background workers** consuming from the internal event bus / job queue, not inline in HTTP request handlers.

**Rationale:** The core pipeline is inherently asynchronous and often I/O- and LLM-latency-bound. Background processing keeps the API responsive and lets each pipeline stage scale its worker pool independently of the web tier.

See [07-data-flow.md](07-data-flow.md) and [12-scalability.md](12-scalability.md).

### 14. Build Only Competitive Advantages

Signora builds, in-house, only the capabilities that constitute its actual competitive advantage and product differentiation: the intelligence pipeline itself.

**Rationale:** Engineering time is the scarcest resource. Every hour spent building commodity infrastructure is an hour not spent on the thirteen ratified core modules — Knowledge Graph, Provider Platform, Provider Normalization, Observation Engine, Business Event Engine, Signal Engine, Buying Score Engine, Opportunity Engine, AI Research Engine, AI Reasoning Engine, Recommendation Engine, Timeline, and Revenue Intelligence Platform (see [04-modules.md](04-modules.md)) — the things that actually make Signora valuable and defensible.

### 15. Buy Commodity Infrastructure

Anything that is not a competitive advantage — authentication, authorization, billing, email, notifications, search, monitoring, analytics, feature flags, object storage — is **bought**, not built.

**Rationale:** These problems are solved well, cheaply, and safely by mature vendors. Building them in-house is pure opportunity cost and unnecessary risk (e.g., rolling your own auth is a security liability, not an asset).

See [09-build-vs-buy.md](09-build-vs-buy.md) for the full decision table.

## Architecture Considerations

These principles are in tension with each other in places, by design:

- Principle 1 (monolith) vs. Principle 5 (extractable boundaries) — resolved by disciplined module isolation without physical service separation.
- Principle 6/7 (single shared DB with RLS) vs. classic microservice "database per service" — resolved deliberately in favor of operational simplicity at current scale.
- Principle 3 (event-driven) vs. the need for some synchronous, strongly-consistent reads (e.g., "does this workspace exist") — resolved in [05-module-dependencies.md](05-module-dependencies.md), which defines the narrow cases where direct synchronous access is allowed.

## Tradeoffs

| Principle | We gain | We give up |
|---|---|---|
| Modular monolith over microservices | Simplicity, atomic deploys, easy local dev, transactional consistency | Independent scaling/deployment per module (until extracted) |
| Single Postgres + RLS over DB-per-tenant | Operational simplicity, cross-tenant analytics, simple backups | Hard per-tenant resource isolation (mitigated in [12-scalability.md](12-scalability.md)) |
| Event-driven over direct calls | Loose coupling, extractability, natural async fit | Eventual consistency, harder end-to-end debugging (mitigated by [06-events.md](06-events.md) tracing conventions) |
| Buy commodity infra | Speed, safety, lower maintenance burden | Vendor dependency, recurring cost, less control (accepted deliberately) |

## Best Practices

- Cite the specific principle number when justifying an architecture decision in an RFC or PR description.
- When a principle appears to block a legitimate need, propose an amendment explicitly rather than quietly working around it.
- Re-read this document before designing any new module or cross-module interaction.

## Anti-Patterns

- Reaching into another module's database tables "just this once" — violates Principles 4 and 5.
- Adding a provider-specific type or SDK call outside the provider abstraction layer — violates Principle 9.
- Calling a third-party AI SDK directly from domain code — violates Principle 10.
- Building an in-house version of a bought capability "because it's easy" — violates Principles 14–15; requires an explicit build-vs-buy RFC (see [09-build-vs-buy.md](09-build-vs-buy.md)).
- Introducing a synchronous, blocking call from one core pipeline module into another instead of an event — violates Principle 3.

## Future Evolution

- As real scaling data accumulates, individual modules may be extracted into standalone services per Principle 5. This is a scaling decision, not a default trajectory — see [12-scalability.md](12-scalability.md) for triggers and process.
- The internal event bus transport may evolve from a Postgres-backed outbox to a dedicated broker without changing these principles — see [06-events.md](06-events.md).

## Decision Summary

Signora's architecture is a **modular, event-driven, domain-driven monolith** on a **single Postgres database with RLS-enforced workspace tenancy**, built with **Clean Architecture** inside every module, using **abstraction layers** for providers/AI/integrations, and deliberately **building only the intelligence pipeline** while **buying every commodity capability**. These fifteen principles are the evaluation criteria for every future architectural decision.

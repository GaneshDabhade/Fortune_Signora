# ADR-0011: Background Processing & Event Bus Transport — Redis + ARQ, Temporal as Future Path

**Status:** Accepted

## Context

Principle 13 requires background-worker-based async processing; Principle 12 requires an internal event bus. v1 proposed a pure Postgres-polling outbox for the event bus and left general background job processing unspecified. This ADR ratifies both together, since they must be reconciled (see [06-events.md](../06-events.md)).

## Decision

**Redis** as the job-queue broker, **ARQ** as the job execution framework, for all general asynchronous work including event dispatch. **PostgreSQL remains the durable source of truth** via the transactional outbox pattern; ARQ/Redis is purely a dispatch and concurrency mechanism layered on top, never the durability guarantee itself. **Temporal** is ratified as the *future* path specifically for AI Research Engine's agentic, multi-step, potentially long-running workflows, adopted only once concrete triggers (see below) are met — not adopted upfront.

## Alternatives Considered — Job Queue

| Alternative | Why not chosen |
|---|---|
| **Celery + RabbitMQ/Redis** | The long-established Python standard, but materially heavier configuration surface (task routing, result backends, worker concurrency models) than ARQ's minimal, async-native design — and Celery's synchronous-first task model is a worse fit for FastAPI/SQLAlchemy's async-native stack ([ADR-0001](0001-backend-language-and-runtime.md), [ADR-0002](0002-web-framework-and-api-style.md), [ADR-0005](0005-orm-and-schema-migrations.md)) than ARQ's `asyncio`-native jobs. |
| **RQ (Redis Queue)** | Simple and Redis-native like ARQ, but synchronous by default, again a worse fit for an async-first codebase. |
| **Dramatiq** | A credible, well-designed alternative with good ergonomics, but a smaller ecosystem/community than Celery and no clearer async-native advantage over ARQ specifically, which was purpose-built for `asyncio` + Redis. |
| **Cloud-native queue (AWS SQS directly, no framework)** | Would avoid Redis for queueing, but SQS lacks ARQ's Python-native job definition ergonomics and would require building scheduling/retry/worker-pool logic by hand — reintroducing exactly what Principle 15 says not to build (queue execution semantics are commodity). |

## Alternatives Considered — Durable/Agentic Workflow Orchestration

| Alternative | Why not chosen (for now) |
|---|---|
| **Adopt Temporal from day one** | Temporal is the stronger fit for AI Research Engine's eventual needs (durable, resumable, checkpointed multi-step execution), but adopting it upfront for the *entire* background-processing surface would mean operating Temporal's own server/persistence infrastructure before most of the workload (structured, fast, single-call jobs) needs anything beyond ARQ's simpler model — a clear violation of Principle 1's evidence-based-complexity discipline. |
| **Hand-rolled workflow/saga state machine on top of ARQ** | Explicitly rejected by Principle 15 (Workflow Orchestration is a "never build" line item, see [09-build-vs-buy.md](../09-build-vs-buy.md)) — durable workflow execution has serious correctness pitfalls (exactly-once semantics, replay determinism) that a mature engine solves and a bespoke implementation would likely get wrong. |

## Alternatives Considered — Event Bus Transport

| Alternative | Why not chosen |
|---|---|
| **Pure Postgres polling outbox (v1's original proposal)** | Correct and simple, but once Redis/ARQ is ratified as required infrastructure anyway for general background work, operating a second, independent dispatch mechanism purely for events would duplicate concurrency models, retry policies, and monitoring surfaces for no benefit — see [06-events.md](../06-events.md). |
| **Publish directly to Redis, no outbox** | Rejected — Redis cannot participate in the same ACID transaction as the domain write, reintroducing the dual-write problem (state committed, event lost, or vice versa) the outbox pattern exists to prevent. |
| **Dedicated message broker (Kafka/NATS) from day one** | The strongest long-term fan-out/throughput ceiling, but a materially heavier operational commitment than current/near-term event volume justifies — reserved as the ratified future path if the concrete triggers in [12-scalability.md](../12-scalability.md) are met, not adopted pre-emptively. |

## Tradeoffs

**We gain:** one background-processing infrastructure (Redis/ARQ) serving both general async work and event dispatch, avoiding duplicated operational surfaces; PostgreSQL remains the single durable source of truth throughout, so no decision here weakens the durability guarantee; and a clear, evidence-triggered (not calendar-triggered) path to Temporal for the one workload class that actually needs it.

**We give up:** Celery's larger ecosystem/maturity and Temporal's durability guarantees for the *general* job-processing surface today — both explicitly deferred, not rejected outright, with named trigger conditions.

## Risks

- ARQ is a smaller project than Celery — tracked as [16-architecture-risks.md](../16-architecture-risks.md) R-11.
- Running both a Postgres outbox and a Redis queue adds one extra hop (the relay process) versus either alone — accepted as a small, simple, stateless component; see [06-events.md](../06-events.md) for its design.

## Migration Strategy

- **ARQ → Celery or another framework**: job handlers are thin wrappers around each module's `application/` use cases ([15-project-structure.md](../15-project-structure.md)); a migration would touch only the ARQ-specific job-registration code, not business logic.
- **ARQ → Temporal for AI Research Engine specifically**: the ratified next step once triggers are met (see [12-scalability.md](../12-scalability.md) and [17-future-recommendations.md](../17-future-recommendations.md)) — AI Research Engine's application layer would be reimplemented as a Temporal workflow/activities, while `opportunity.created` still triggers it and `ai_research.completed` is still what it publishes, so no other module needs to change.
- **Postgres outbox + Redis relay → dedicated broker**: the Internal Event Bus abstraction ([06-events.md](../06-events.md)) means only the relay/dispatch implementation changes, not publisher/subscriber code in any module.

## Consequences

- All background work — pipeline event handlers and any other async job — runs through ARQ, never a second, parallel job mechanism.
- PostgreSQL's transactional outbox remains the durability guarantee for every domain event, unconditionally, even after any future Temporal adoption.
- AI Research Engine is explicitly named as the first Temporal migration candidate, with concrete trigger conditions defined in [12-scalability.md](../12-scalability.md) rather than left open-ended.

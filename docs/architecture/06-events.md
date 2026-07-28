# 06 — Events

> Status: **Living document — Architectural Constitution**
> Audience: All engineers, EMs, and technical stakeholders at Signora
> Revision: **v2** — updated event catalog for the thirteen-module map ([04-modules.md](04-modules.md)) and the ratified transport decision. See [ADR-0011](adr/0011-background-processing-and-event-bus-transport.md).

## Purpose

This document specifies Signora's **Internal Event Bus** (Principle 12): the event envelope contract, the full event catalog, delivery semantics, and the ratified transport implementation.

## Responsibilities

- Define the standard event envelope every domain event uses.
- Catalog every domain event, its producer, its consumer(s), and its payload shape at a high level.
- Define delivery, ordering, retry, and idempotency semantics.
- Define the transport implementation and its rationale.

## Event Envelope

```json
{
  "event_id": "uuid",
  "event_type": "opportunity.created",
  "event_version": 1,
  "workspace_id": "uuid",
  "occurred_at": "ISO-8601 timestamp",
  "producer_module": "opportunity-engine",
  "correlation_id": "uuid",
  "causation_id": "uuid | null",
  "payload": { "...": "event-specific, versioned shape" }
}
```

| Field | Meaning |
|---|---|
| `event_id` | Unique ID of this event instance; used for idempotency/dedup. |
| `event_type` | Dot-namespaced type, `<domain_concept>.<past_tense_verb>`. |
| `event_version` | Payload schema version for this event type. |
| `workspace_id` | Tenant scope — every event is workspace-scoped (Principle 8). |
| `occurred_at` | When the fact became true in the domain. |
| `producer_module` | The module that published the event. |
| `correlation_id` | Groups all events belonging to one end-to-end pipeline run, for tracing (see [07-data-flow.md](07-data-flow.md)). |
| `causation_id` | The `event_id` that directly caused this one. |
| `payload` | Event-specific data — validated as a Pydantic v2 model (see [ADR-0004](adr/0004-data-validation-and-serialization.md)); the canonical schema for each event type lives in `platform/event-bus/schemas/` (see [15-project-structure.md](15-project-structure.md)), not duplicated inline here. |

## Event Catalog

Events are listed in pipeline order. Payload fields below are illustrative and indicate intent; the Pydantic model is the binding contract.

| Event | Producer | Consumer(s) | High-level payload |
|---|---|---|---|
| `workspace.created` | Workspace & Tenancy | (informational) | `workspace_id`, `name`, `created_by` |
| `workspace.member_added` | Workspace & Tenancy | (informational) | `workspace_id`, `user_id`, `role` |
| `provider.payload.received` | Provider Platform | Provider Normalization | `provider`, `entity_type`, `raw_payload_ref`, `received_at` |
| `provider.health_changed` | Provider Platform | (operational; feeds monitoring, not domain modules) | `provider`, `status`, `reason` |
| `provider.record.normalized` | Provider Normalization | Knowledge Graph | `provider`, `entity_type`, `normalized_record`, `provenance` |
| `entity.created` | Knowledge Graph | Observation Engine | `entity_id`, `entity_type`, `attributes` |
| `entity.updated` | Knowledge Graph | Observation Engine | `entity_id`, `changed_fields`, `previous_values` |
| `entity.merged` | Knowledge Graph | Observation Engine | `surviving_entity_id`, `merged_entity_ids` |
| `observation.recorded` | Observation Engine | Business Event Engine, Timeline | `observation_id`, `entity_id`, `observed_at`, `fact`, `provenance` |
| `business_event_type.published` | Business Event Engine (internal taxonomy change) | Business Event Engine (self; versioning notification) | `event_type_id`, `schema_version`, `definition` |
| `business_event.detected` | Business Event Engine | Signal Engine, Timeline | `business_event_id`, `event_type_id`, `entity_id`, `source_observation_ids` |
| `signal.generated` | Signal Engine | Buying Score Engine, Timeline | `signal_id`, `entity_id`, `source_event_ids`, `score` |
| `signal.scored` | Signal Engine | Buying Score Engine, Timeline | `signal_id`, `score`, `scoring_model_version` |
| `buying_score.updated` | Buying Score Engine | Opportunity Engine, Timeline | `entity_id`, `score`, `trend`, `source_signal_ids`, `model_version` |
| `opportunity.created` | Opportunity Engine | AI Research Engine, AI Reasoning Engine, Timeline, Revenue Intelligence Platform | `opportunity_id`, `entity_id`, `source_buying_score`, `stage` |
| `opportunity.stage_changed` | Opportunity Engine | AI Reasoning Engine, Timeline, Revenue Intelligence Platform | `opportunity_id`, `previous_stage`, `new_stage` |
| `ai_research.completed` | AI Research Engine | AI Reasoning Engine (optional/non-blocking, see [05-module-dependencies.md](05-module-dependencies.md)) | `research_id`, `opportunity_id`, `artifact_ref`, `model_provenance` |
| `ai_reasoning.completed` | AI Reasoning Engine | Recommendation Engine, Revenue Intelligence Platform | `reasoning_id`, `opportunity_id`, `model_provenance`, `result_ref` |
| `recommendation.created` | Recommendation Engine | Timeline, Revenue Intelligence Platform | `recommendation_id`, `opportunity_id`, `action`, `priority` |
| `recommendation.status_changed` | Recommendation Engine | Timeline, Revenue Intelligence Platform, Signal Engine (feedback loop) | `recommendation_id`, `previous_status`, `new_status` |

## Event Flow Diagram

```mermaid
sequenceDiagram
    participant PP as Provider Platform
    participant PN as Provider Normalization
    participant KG as Knowledge Graph
    participant OE as Observation Engine
    participant BEE as Business Event Engine
    participant SE as Signal Engine
    participant BSE as Buying Score Engine
    participant OP as Opportunity Engine
    participant ARE as AI Research Engine
    participant AIR as AI Reasoning Engine
    participant RE as Recommendation Engine
    participant TL as Timeline
    participant RI as Revenue Intelligence Platform

    PP->>PN: provider.payload.received
    PN->>KG: provider.record.normalized
    KG->>OE: entity.created / updated / merged
    OE->>BEE: observation.recorded
    OE-->>TL: observation.recorded
    BEE->>SE: business_event.detected
    BEE-->>TL: business_event.detected
    SE->>BSE: signal.generated / signal.scored
    SE-->>TL: signal.generated
    BSE->>OP: buying_score.updated
    BSE-->>TL: buying_score.updated
    OP->>ARE: opportunity.created
    OP->>AIR: opportunity.created / stage_changed
    OP-->>RI: opportunity.created
    ARE-->>AIR: ai_research.completed (optional)
    AIR->>RE: ai_reasoning.completed
    AIR-->>RI: ai_reasoning.completed
    RE-->>TL: recommendation.created
    RE-->>RI: recommendation.created
```

## Delivery Semantics

- **At-least-once delivery.** Consumers MUST be idempotent, keyed on `event_id`.
- **Per-entity ordering, not global ordering.**
- **Retry with backoff and dead-lettering**, implemented as ARQ's native retry policy plus a dedicated dead-letter queue for jobs that exhaust retries.
- **Durability first.** An event is not "published" until durably committed in PostgreSQL.

## Transport: Postgres Outbox + Redis/ARQ Dispatch

The v1 architecture proposed a pure Postgres-polling outbox. The Architecture Review Board revisited this once background processing was ratified as **Redis + ARQ** (see [ADR-0011](adr/0011-background-processing-and-event-bus-transport.md)) and reconciled the two:

1. A module writes its domain state change and an outbox row to PostgreSQL in the **same transaction** — this remains the source of truth and the durability guarantee. Nothing is considered "published" until this commits.
2. A lightweight **relay process** (part of the worker fleet) tails the outbox via `LISTEN/NOTIFY` and enqueues a corresponding ARQ job on Redis for each subscriber, marking the outbox row relayed.
3. **ARQ workers** — already required for general background processing — consume these jobs using the same worker pools, queues, and retry/backoff semantics as every other background job in the system, rather than requiring a second, bespoke dispatch mechanism.
4. The Internal Event Bus abstraction referenced throughout this document set wraps this two-hop path (Postgres commit → relay → ARQ dispatch); modules publish/subscribe against that abstraction only.

```mermaid
flowchart LR
    Domain[Module Domain Logic] -->|same transaction| Outbox[(Outbox Table<br/>PostgreSQL)]
    Outbox -->|LISTEN/NOTIFY| Relay[Outbox Relay Process]
    Relay -->|enqueue job| Redis[(Redis)]
    Redis --> ARQWorker[ARQ Worker Pool]
    ARQWorker --> Handler1[Consumer Module Handler]
    ARQWorker --> Handler2[Consumer Module Handler]
    ARQWorker -->|on repeated failure| DLQ[(Dead Letter Queue<br/>Redis + Postgres audit table)]
```

**Why not skip the outbox and publish directly to Redis?** Redis alone cannot participate in the same ACID transaction as the domain write, reintroducing the dual-write problem (state committed but event lost, or event published but state rolled back) that the outbox pattern exists to eliminate. The outbox keeps PostgreSQL as the single durable source of truth for "did this event definitely happen"; Redis/ARQ is purely a dispatch and worker-concurrency mechanism layered on top, and is disposable/rebuildable from the outbox if ever lost.

**Why not skip Redis/ARQ and dispatch straight from outbox polling?** Because Redis + ARQ is already a required piece of infrastructure for general asynchronous work (Principle 13, [ADR-0011](adr/0011-background-processing-and-event-bus-transport.md)), reusing it for event dispatch avoids operating two separate background-processing mechanisms with two separate concurrency models, retry policies, and monitoring surfaces.

## Schema Evolution

- Event payloads are versioned via `event_version`; the Pydantic model is the source of truth (see [ADR-0004](adr/0004-data-validation-and-serialization.md)).
- Breaking changes require a new `event_version`, with the producer publishing both versions for a defined deprecation window.
- No consumer may depend on undocumented payload fields.

## Design Rationale

Keeping PostgreSQL as the transactional source of truth while using the already-required Redis/ARQ stack purely as a dispatch mechanism gives Signora durability guarantees without a dual-write risk and without operating two independent async infrastructures. This is a direct consequence of ratifying Redis + ARQ for background processing — see [ADR-0011](adr/0011-background-processing-and-event-bus-transport.md) for the full alternatives analysis (including why a dedicated broker like Kafka was rejected at this stage).

## Best Practices

- Always propagate `correlation_id`/`causation_id`.
- Design event handlers to be idempotent on `event_id` from day one.
- Never publish directly to Redis, bypassing the outbox — this breaks the durability guarantee.

## Anti-Patterns

- Publishing an event to Redis before the causing transaction commits.
- Using events as a substitute for synchronous request/response.
- Fat events embedding another module's entire internal state.
- Non-idempotent event handlers.

## Tradeoffs

| Choice | We gain | We give up |
|---|---|---|
| Outbox (Postgres) + dispatch (Redis/ARQ) | Transactional durability + reuse of one worker infrastructure for all async work | An extra relay hop vs. either pure-Postgres-polling or pure-Redis-pubsub alone (acceptable; relay is simple and stateless) |
| At-least-once + idempotent consumers | Simplicity, no message loss | Consumers must handle duplicates |

## Future Evolution

- If outbox/relay throughput becomes a bottleneck (see triggers in [12-scalability.md](12-scalability.md)), the relay can be sharded per module or per `workspace_id` range without changing the Internal Event Bus abstraction.
- Migration to Temporal for the highest-value long-running/agentic workflows (notably AI Research Engine) is the ratified future path — see [ADR-0011](adr/0011-background-processing-and-event-bus-transport.md) and [17-future-recommendations.md](17-future-recommendations.md). This does not replace the event bus; it replaces ad hoc multi-step orchestration inside a single ARQ job with durable, resumable workflow execution for the specific workloads that need it.

## Decision Summary

The Internal Event Bus is a versioned, envelope-standardized, at-least-once, per-entity-ordered event system implemented as a PostgreSQL transactional outbox for durability, relayed via `LISTEN/NOTIFY` into Redis/ARQ for dispatch and worker concurrency — reusing, not duplicating, the platform's general background-processing infrastructure.

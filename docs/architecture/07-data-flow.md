# 07 — Data Flow

> Status: **Living document — Architectural Constitution**
> Audience: All engineers, EMs, and technical stakeholders at Signora
> Revision: **v2** — updated for the thirteen-module pipeline and the ratified stack (FastAPI, PostgreSQL 17, Redis/ARQ). See [08-technology-stack.md](08-technology-stack.md).

## Purpose

This document traces **end-to-end data flow** through Signora for the system's key scenarios, connecting the module/event definitions into concrete, time-ordered stories.

## Primary Flow: Provider Data → Recommendation

```mermaid
sequenceDiagram
    autonumber
    participant Prov as External Provider
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
    participant AIVendor as AI Vendor (Claude/OpenAI/Gemini)
    participant RE as Recommendation Engine
    participant TL as Timeline
    participant DB as PostgreSQL
    participant Q as Redis / ARQ

    Note over Prov,PP: Scheduled poll or inbound webhook (ARQ worker)
    Prov->>PP: Raw payload
    PP->>DB: Persist raw payload + outbox: provider.payload.received
    DB-->>Q: relay dispatches job
    Q-->>PN: provider.payload.received
    PN->>PN: Normalize via Provider Abstraction Layer adapter
    PN->>DB: Persist normalized record + outbox: provider.record.normalized
    DB-->>Q: relay dispatches job
    Q-->>KG: provider.record.normalized
    KG->>KG: Resolve / merge entity
    KG->>DB: Persist entity + outbox: entity.*
    DB-->>Q: relay dispatches job
    Q-->>OE: entity.*
    OE->>DB: Persist observation + outbox: observation.recorded
    DB-->>Q: relay dispatches jobs
    Q-->>BEE: observation.recorded
    Q-->>TL: observation.recorded
    BEE->>DB: Persist business event + outbox: business_event.detected
    DB-->>Q: relay dispatches jobs
    Q-->>SE: business_event.detected
    Q-->>TL: business_event.detected
    SE->>DB: Persist signal + outbox: signal.generated/scored
    DB-->>Q: relay dispatches jobs
    Q-->>BSE: signal.*
    Q-->>TL: signal.*
    BSE->>DB: Persist buying score + outbox: buying_score.updated
    DB-->>Q: relay dispatches jobs
    Q-->>OP: buying_score.updated
    Q-->>TL: buying_score.updated
    OP->>DB: Persist opportunity + outbox: opportunity.created
    DB-->>Q: relay dispatches jobs
    Q-->>ARE: opportunity.created
    Q-->>AIR: opportunity.created
    Q-->>TL: opportunity.created
    par Optional, non-blocking
      ARE->>AIVendor: Agentic research (via AI Provider Abstraction Layer)
      AIVendor-->>ARE: Research findings
      ARE->>DB: Persist artifact + outbox: ai_research.completed
    and Proceeds without waiting
      AIR->>AIR: Wait up to research-timeout for ai_research.completed
      AIR->>AIVendor: Reasoning request (with or without research artifact)
      AIVendor-->>AIR: Reasoning result
    end
    AIR->>DB: Persist reasoning + outbox: ai_reasoning.completed
    DB-->>Q: relay dispatches job
    Q-->>RE: ai_reasoning.completed
    RE->>DB: Persist recommendation + outbox: recommendation.created
    DB-->>Q: relay dispatches job
    Q-->>TL: recommendation.created
```

**Characteristics of this flow:**

- Entirely **asynchronous** and **ARQ-worker-driven** end to end (Principle 13); no step blocks a user-facing HTTP request.
- Every domain state change commits to PostgreSQL first (outbox), then is relayed to Redis/ARQ for dispatch — see [06-events.md](06-events.md).
- `correlation_id`, assigned at `provider.payload.received`, threads through every subsequent event.
- The **AI Research Engine / AI Reasoning Engine fork** is the one explicitly non-blocking relationship in the graph: AI Reasoning Engine proceeds once either the research artifact arrives or a bounded timeout elapses, whichever is first — see [05-module-dependencies.md](05-module-dependencies.md) and [14-ai-architecture.md](14-ai-architecture.md) for the timeout policy.
- Latency across this flow is dominated by AI Research Engine (multi-step agentic tool use, potentially minutes) and, secondarily, AI Reasoning Engine (a single structured LLM call) — the primary input into worker pool sizing in [12-scalability.md](12-scalability.md).

## Secondary Flow: Revenue Intelligence Dashboard Read (Synchronous)

```mermaid
sequenceDiagram
    autonumber
    participant User as Sales User
    participant API as FastAPI API Layer
    participant Auth as JWT Verifier (public key)
    participant Authz as Casbin
    participant WS as Workspace & Tenancy
    participant RI as Revenue Intelligence Platform
    participant TL as Timeline
    participant Cache as Redis (cache)
    participant DB as PostgreSQL (RLS-scoped)

    User->>API: GET /workspaces/{id}/intelligence (Bearer JWT)
    API->>Auth: Verify RS256 signature + iss/aud/exp
    Auth-->>API: Authenticated principal (sub, sid, email)
    API->>WS: Verify membership server-side (authoritative)
    WS-->>API: Membership + role
    API->>API: Set RLS context (app.user_id, app.workspace_id)
    API->>Authz: Evaluate permission (Casbin, workspace-scoped)
    Authz-->>API: Allow
    API->>RI: Request workspace intelligence view
    RI->>Cache: Check cached composed view (short TTL)
    alt cache hit
      Cache-->>RI: Cached view
    else cache miss
      RI->>TL: Query timeline feed (sync)
      TL->>DB: SELECT ... (RLS-scoped)
      DB-->>TL: Rows
      RI->>DB: SELECT opportunities/recommendations (RLS-scoped)
      DB-->>RI: Rows
      RI->>Cache: Store composed view (short TTL)
    end
    RI-->>API: Composed view
    API-->>User: JSON response (OpenAPI-documented)
```

**Characteristics of this flow:**

- Synchronous, served by the FastAPI API tier.
- Reads only already-materialized data; Revenue Intelligence Platform never triggers pipeline processing inline.
- Every query is RLS-scoped by `workspace_id` (see [11-tenancy.md](11-tenancy.md)).
- Redis is used as a short-TTL read-through cache for composed views — never as a system of record (Principle 6).

## Secondary Flow: Recommendation Acted On (Feedback Loop)

```mermaid
sequenceDiagram
    autonumber
    participant User as Sales User
    participant API as FastAPI API Layer
    participant RE as Recommendation Engine
    participant DB as PostgreSQL
    participant Q as Redis / ARQ
    participant SE as Signal Engine

    User->>API: POST /recommendations/{id}/act
    API->>RE: Mark recommendation acted-on
    RE->>DB: Persist status + outbox: recommendation.status_changed
    API-->>User: 200 OK
    DB-->>Q: relay dispatches job
    Q-->>SE: recommendation.status_changed (new input signal)
```

## Tracing a Request End-to-End

`workspace_id`, `correlation_id`, and `causation_id` are carried on every OpenTelemetry span and structured log line, per [17-future-recommendations.md](17-future-recommendations.md) §Observability and [ADR-0018](adr/0018-monitoring-and-observability.md). To debug "why didn't this company get a recommendation":

1. Find `provider.payload.received` for the entity — was the data ingested at all?
2. Follow `correlation_id` through the outbox table and ARQ job history (Sentry/Grafana dashboards, see [ADR-0018](adr/0018-monitoring-and-observability.md)).
3. Identify at which stage the chain stopped.

## Design Rationale

Separating the primary async pipeline from secondary sync reads mirrors the real operational distinction engineers need. The AI Research Engine fork is drawn explicitly (`par`/non-blocking) rather than implied, because it is the one place in the flow where naive reasoning about "the pipeline runs in order" would be wrong.

## Best Practices

- Always propagate and log `correlation_id` and `workspace_id`.
- Cache only already-materialized, non-authoritative read data (Redis), never treat cache as the source of truth.
- Bound every AI Research Engine invocation with an explicit timeout that AI Reasoning Engine respects.

## Anti-Patterns

- Triggering AI Research Engine or AI Reasoning Engine synchronously from an API request.
- Making AI Reasoning Engine block indefinitely on AI Research Engine.
- Debugging pipeline issues without `correlation_id`.
- Caching authoritative pipeline state in Redis instead of PostgreSQL.

## Future Evolution

- As AI Research Engine's agentic workloads grow in complexity (multi-tool, multi-step, requiring durable resumability across process restarts), this flow's research step is the leading candidate to migrate from an ARQ job to a Temporal workflow — see [ADR-0011](adr/0011-background-processing-and-event-bus-transport.md).

## Decision Summary

Signora's dominant data flow is asynchronous, PostgreSQL-durable, Redis/ARQ-dispatched, and traceable end-to-end via `correlation_id`. The one deliberately non-blocking relationship — AI Research Engine enriching AI Reasoning Engine within a bounded timeout — is modeled explicitly rather than assumed.

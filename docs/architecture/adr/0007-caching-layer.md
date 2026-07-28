# ADR-0007: Caching Layer — Redis

**Status:** Accepted

## Context

Revenue Intelligence Platform's dashboard reads ([07-data-flow.md](../07-data-flow.md)) benefit from a short-TTL read-through cache over already-materialized composed views, to reduce repeated load on PostgreSQL for expensive cross-module aggregation queries. Signora also needs a broker for background job queueing ([ADR-0011](0011-background-processing-and-event-bus-transport.md)).

## Decision

**Redis**, provisioned as logically (and, in production, physically — see [12-scalability.md](../12-scalability.md)) separate clusters for caching versus job-queue brokering.

## Alternatives Considered

| Alternative | Why not chosen |
|---|---|
| **Memcached** | Simpler and slightly faster for pure key-value caching, but lacks Redis's data structures (sorted sets, streams) needed for ARQ's queue implementation — choosing Memcached for caching would still require Redis (or an equivalent) for queueing, adding a second technology for no net simplification. |
| **In-process caching (e.g., `cachetools`)** | Would not work across the horizontally-scaled, multi-instance ECS deployment ([ADR-0022](0022-devops-infrastructure-and-deployment-topology.md)) — cache entries would be inconsistent per instance, and would not share state with the ARQ job queue's need for a networked broker regardless. |
| **PostgreSQL as the cache (e.g., `UNLOGGED` tables)** | Would avoid a second technology, but adds write load to the primary database for a purely best-effort, disposable cache — directly counter to keeping the primary database free for pipeline and RLS-critical writes ([12-scalability.md](../12-scalability.md)). |

## Tradeoffs

**We gain:** one technology serving both caching and job-queue brokering needs (reducing operational surface versus adopting two separate technologies), sub-millisecond read latency for cached composed views, and a managed option (ElastiCache, [ADR-0022](0022-devops-infrastructure-and-deployment-topology.md)).

**We give up:** cache durability — Redis-as-cache is explicitly disposable/rebuildable, never a system of record (Principle 6) — which is a deliberate constraint, not a limitation to work around.

## Risks

Sharing Redis for both caching and queueing in a single cluster would let cache eviction pressure threaten queue durability, or vice versa — mitigated by provisioning **separate ElastiCache clusters** for each role from the start, per [12-scalability.md](../12-scalability.md), rather than treating this as a later optimization.

## Migration Strategy

Cache usage is isolated behind a thin caching interface in `backend/platform/`; a future migration to Memcached (for caching only, with Redis retained for queueing) would touch only that interface's implementation, not calling code.

## Consequences

- Redis is never used as a system of record for pipeline or tenant data — only for disposable caching and job-queue brokering.
- Two ElastiCache clusters are provisioned in production: one for caching, one for ARQ's queue broker.
- Cache keys are always `workspace_id`-scoped, and cached data is treated as RLS-equivalent-sensitive even though Redis itself has no native RLS — access to the cache layer is only ever performed by already-workspace-scoped application code, never exposed directly.

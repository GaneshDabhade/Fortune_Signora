# ADR-0006: Data Platform — Primary Database & Multi-Tenancy (PostgreSQL 17 + RLS)

**Status:** Accepted

## Context

Principles 6, 7, and 8 ([02-principles.md](../02-principles.md)) already fix the shape of this decision: a single shared database with Row-Level Security-enforced, workspace-based tenancy. This ADR ratifies the specific engine version and confirms the isolation mechanism against alternatives, since v1 left the exact version and a full alternatives comparison as `TODO`.

## Decision

**PostgreSQL 17+**, shared database, tenant isolation via native **Row-Level Security**.

## Alternatives Considered

| Alternative | Why not chosen |
|---|---|
| **Database-per-tenant** | Would provide the strongest resource isolation, but at hundreds-of-thousands-of-workspaces target scale ([12-scalability.md](../12-scalability.md)), per-tenant database provisioning/migration/backup fan-out becomes an operational scaling problem in its own right — directly contradicts Principle 6's rationale. |
| **Schema-per-tenant** | A middle ground, but PostgreSQL's connection/catalog overhead scales poorly past a few thousand schemas in a single instance, and migrations must still fan out per schema — does not meaningfully outperform RLS at target scale while adding real operational complexity. |
| **Application-layer-only tenant filtering (no RLS)** | Rejected outright — a single missed `WHERE workspace_id = ...` clause anywhere in the codebase becomes a cross-tenant data leak. RLS makes this a database-enforced invariant instead of a code-review-dependent one, directly per Principle 7's rationale. |
| **MySQL / other RDBMS** | PostgreSQL's native RLS support, mature extension ecosystem (notably pgvector, [ADR-0008](0008-search-and-vector-retrieval.md)), and JSON/JSONB support (useful for provider-normalization staging data) make it the stronger fit; MySQL lacks equivalent native RLS, which would force a return to the rejected application-layer-only model. |
| **PostgreSQL 15/16 (older major versions)** | Functionally adequate, but PostgreSQL 17's RLS planner improvements measurably reduce the historical performance tax of RLS-qualified queries on large, indexed tables — directly relevant given Signora's stated scale target and the Observation table's expected volume ([12-scalability.md](../12-scalability.md), [16-architecture-risks.md](../16-architecture-risks.md) R-03). Choosing the newest stable major version now avoids a disruptive in-place major-version upgrade once the database is under production load. |

## Tradeoffs

**We gain:** a single, ACID-transactional system of record supporting the transactional outbox pattern ([06-events.md](../06-events.md)) without a dual-write problem, database-enforced tenant isolation that survives application bugs, and a mature managed-service option (RDS for PostgreSQL, [ADR-0022](0022-devops-infrastructure-and-deployment-topology.md)).

**We give up:** the resource-isolation strength of database-per-tenant for the largest tenants — mitigated by the read-replica/partitioning escalation path in [12-scalability.md](../12-scalability.md), reserved for evidence-based triggers rather than adopted upfront.

## Risks

See [16-architecture-risks.md](../16-architecture-risks.md) R-03: RLS query performance at target scale is not yet load-tested. This is the primary open risk against this decision and is scheduled as a Horizon-1 action in [17-future-recommendations.md](../17-future-recommendations.md).

## Migration Strategy

If RLS-based isolation is ever proven insufficient for a specific large tenant (evidenced, not anticipated), the escalation path is tenant-aware read replicas, then `workspace_id`-based partitioning, then — only as a last resort — dedicated infrastructure for a specific named tenant, before ever reconsidering database-per-tenant wholesale. See [12-scalability.md](../12-scalability.md).

## Consequences

- Every workspace-owned table requires `workspace_id NOT NULL`, an RLS policy, and `FORCE ROW LEVEL SECURITY` — see [11-tenancy.md](../11-tenancy.md).
- Business Event Engine's taxonomy tables are the sole deliberate exception (global reference data, no RLS) — see [11-tenancy.md](../11-tenancy.md).
- All application code paths (FastAPI requests and ARQ jobs) must establish `SET LOCAL app.workspace_id` before any query.

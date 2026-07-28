# ADR-0005: ORM & Schema Migrations — SQLAlchemy 2.x + Alembic

**Status:** Accepted

## Context

Per [11-tenancy.md](../11-tenancy.md), the data-access layer must not obstruct raw PostgreSQL Row-Level Security session-variable control (`SET LOCAL app.workspace_id`), must support PostgreSQL 17-specific features (including pgvector, [ADR-0008](0008-search-and-vector-retrieval.md)), and must support async I/O consistent with FastAPI/ARQ's async-first design ([ADR-0002](0002-web-framework-and-api-style.md), [ADR-0011](0011-background-processing-and-event-bus-transport.md)).

## Decision

**SQLAlchemy 2.x** (async engine/session) as the ORM, **Alembic** for schema migrations.

## Alternatives Considered

| Alternative | Why not chosen |
|---|---|
| **Tortoise ORM** | Async-native and Django-inspired, but a smaller ecosystem and less mature RLS/raw-SQL escape-hatch support than SQLAlchemy 2.x, which matters given how central raw `SET LOCAL` session control is to this architecture ([11-tenancy.md](../11-tenancy.md)). |
| **Prisma (Python client)** | Excellent DX and migration tooling, but its Python client is a wrapper around a Node.js/Rust query engine binary — an unusual and heavier operational dependency for a Python-native stack, and its migration model is less flexible than Alembic for the kind of hand-authored RLS policy migrations this architecture requires. |
| **SQLModel** | Built on SQLAlchemy + Pydantic and appealing for reducing model duplication, but as of this decision trails SQLAlchemy 2.x's own async maturity and adds an extra abstraction layer over an already-adopted dependency (SQLAlchemy) for marginal DX gain — Pydantic models remain distinct from SQLAlchemy models in this architecture specifically so API/event contracts ([ADR-0004](0004-data-validation-and-serialization.md)) don't accidentally couple to database schema (a Clean Architecture violation, Principle 4). |
| **Raw SQL / `asyncpg` directly, no ORM** | Would maximize control over RLS session handling and query shape, but at the cost of hand-rolling all mapping, migration tooling, and query building — SQLAlchemy 2.x's Core (not just its ORM) already provides this level of control when needed, without giving up the ORM layer's productivity for standard CRUD-shaped repository code. |

## Tradeoffs

**We gain:** mature async support, full raw-SQL escape hatches for RLS session variables and pgvector-specific query construction, Alembic's battle-tested migration tooling (branching, autogenerate-with-review, downgrade paths), and a large, stable ecosystem.

**We give up:** SQLModel's reduced model duplication (Pydantic models and SQLAlchemy models are kept deliberately distinct — a Clean Architecture boundary decision, not an oversight) and Prisma's more polished migration DX (Alembic's autogenerate requires more manual review, which is treated as a feature given schema changes must be reviewed against [11-tenancy.md](../11-tenancy.md)'s RLS requirements anyway).

## Risks

- SQLAlchemy's ORM layer, if used carelessly, can generate N+1 query patterns — mitigated by code review discipline ([CLAUDE.md](../../../CLAUDE.md) §14) and repository-pattern conventions that make eager-loading explicit per module.
- Alembic's autogenerate does not detect RLS policy changes automatically (policies are not first-class SQLAlchemy constructs) — every migration touching a workspace-owned table's RLS policy must be hand-reviewed against [11-tenancy.md](../11-tenancy.md)'s `FORCE ROW LEVEL SECURITY` requirement.

## Migration Strategy

Each module's `infrastructure/` repositories are the only code depending on SQLAlchemy directly (Principle 4); a future ORM migration would be scoped module-by-module without touching domain/application layers or Pydantic-based public contracts.

## Consequences

- Every workspace-owned table's Alembic migration must include its RLS policy and `FORCE ROW LEVEL SECURITY` statement in the same migration that creates the table — never added as a follow-up.
- SQLAlchemy models live exclusively in each module's `infrastructure/` layer; they are never imported by `domain/`, `application/`, or `public/` ([15-project-structure.md](../15-project-structure.md)).
- Async session lifecycle (including `SET LOCAL app.workspace_id`) is centralized in `backend/platform/db/`.

# ADR-0002: Web Framework & API Style — FastAPI, REST, OpenAPI, Native DI

**Status:** Accepted

## Context

Given Python 3.13+ ([ADR-0001](0001-backend-language-and-runtime.md)), Signora needs a web framework for its interface layer ([15-project-structure.md](../15-project-structure.md)) that supports async I/O natively (the pipeline is I/O-bound throughout), integrates cleanly with Pydantic v2 for request/response validation ([ADR-0004](0004-data-validation-and-serialization.md)), and supports dependency injection idiomatically for Clean Architecture's ports (Principle 4).

## Decision

**FastAPI** as the web framework, **REST** as the API style, **OpenAPI** (auto-generated from FastAPI + Pydantic) for documentation, and **FastAPI's native `Depends()` system** for dependency injection — no separate DI container.

## Alternatives Considered

| Alternative | Why not chosen |
|---|---|
| **Django / Django REST Framework** | Batteries-included ORM and admin conflict with the ratified SQLAlchemy/Alembic choice ([ADR-0005](0005-orm-and-schema-migrations.md)) and Django's sync-first request model is a worse fit than FastAPI's async-native design for an I/O-bound, externally-integrated system. |
| **Flask** | Mature and flexible, but lacks FastAPI's native async support, built-in OpenAPI generation, and first-class Pydantic integration — all three would need to be bolted on. |
| **GraphQL (as API style)** | Offers flexible client-driven queries, but adds schema/resolver complexity that doesn't clearly pay for itself given Signora's API consumers are primarily its own first-party frontend and a small number of integration partners, not a broad third-party developer ecosystem needing query flexibility. REST + OpenAPI is simpler to secure (per-endpoint authorization mapping to Casbin, [ADR-0010](0010-identity-and-access.md)) and simpler to reason about for rate-limiting per Provider Platform-style concerns if ever exposed externally. |
| **Separate DI container (e.g., `dependency-injector`)** | Adds a second DI paradigm alongside FastAPI's own; FastAPI's `Depends()` is sufficient for constructor-style injection of application services into interface-layer routers and is idiomatic to the framework, avoiding unnecessary abstraction (per Principle 4's Clean Architecture requirement, not per any framework preference). |

## Tradeoffs

**We gain:** async-native request handling, automatic OpenAPI generation directly from Pydantic models (single source of truth for API contracts), a DI mechanism that requires no extra dependency, and a framework whose type-driven request/response validation reinforces the strong-typing discipline from [ADR-0001](0001-backend-language-and-runtime.md).

**We give up:** GraphQL's client-driven query flexibility (acceptable — not a demonstrated need) and Django's batteries-included admin/ORM (acceptable — SQLAlchemy/Alembic was chosen independently on its own merits).

## Risks

- FastAPI's `Depends()` DI is request-scoped by convention; care is required to avoid accidentally sharing state across requests in a way that could leak `workspace_id` context (see [11-tenancy.md](../11-tenancy.md)) — mitigated by always deriving workspace-scoped dependencies fresh per request, never caching them at module scope.

## Migration Strategy

REST/OpenAPI contracts are documented independently of FastAPI's implementation; a future framework migration would preserve the API contract and only change the interface-layer implementation, per Clean Architecture's isolation of interface from domain/application ([15-project-structure.md](../15-project-structure.md)). A GraphQL layer could be added later as an additional interface (not a replacement) if a specific external-developer use case emerges, without touching application/domain layers.

## Consequences

- Every module's `interface/` layer is a FastAPI router; every request/response model is a Pydantic v2 model.
- OpenAPI documentation is generated, not hand-maintained, and is the binding external API contract.
- Casbin authorization checks ([ADR-0010](0010-identity-and-access.md)) are wired as FastAPI dependencies, evaluated before a request reaches application-layer code.

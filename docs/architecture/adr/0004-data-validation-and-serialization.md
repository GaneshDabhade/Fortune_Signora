# ADR-0004: Data Validation & Serialization — Pydantic v2

**Status:** Accepted

## Context

Signora needs one consistent mechanism for validating and serializing data at every boundary: API request/response models ([ADR-0002](0002-web-framework-and-api-style.md)), event envelope payloads ([06-events.md](../06-events.md)), AI Reasoning/Research structured output ([14-ai-architecture.md](../14-ai-architecture.md)), and provider adapter output before it enters the domain ([13-integrations.md](../13-integrations.md)). This choice directly determines how reliably "validate before trusting" (a repeated rule across [10-security.md](../10-security.md) and [14-ai-architecture.md](../14-ai-architecture.md)) can actually be enforced.

## Decision

**Pydantic v2** as the sole validation/serialization library across the backend.

## Alternatives Considered

| Alternative | Why not chosen |
|---|---|
| **`attrs` + manual validation** | Excellent for lightweight value objects, but requires hand-rolled or bolted-on validation and JSON Schema generation, duplicating what Pydantic v2 provides natively — and FastAPI's OpenAPI generation ([ADR-0002](0002-web-framework-and-api-style.md)) depends on Pydantic models directly. |
| **`marshmallow`** | Mature schema/serialization library, but slower (Pydantic v2's Rust core, `pydantic-core`, is materially faster) and not natively integrated with FastAPI, which would mean maintaining two parallel validation idioms (FastAPI's native Pydantic dependency vs. marshmallow schemas elsewhere). |
| **Dataclasses + manual JSON Schema** | No built-in validation; would require reimplementing what Pydantic already solves, with no offsetting benefit. |

## Tradeoffs

**We gain:** a single, fast (Rust-core), consistent validation idiom across API contracts, event payloads, and AI output schemas; native FastAPI integration; and JSON Schema generation for free, which both powers OpenAPI docs ([ADR-0002](0002-web-framework-and-api-style.md)) and can validate AI vendor structured-output responses against the same schema definitions.

**We give up:** nothing material — Pydantic v2 is broadly considered the standard choice in the current Python ecosystem for this exact set of use cases, and this is the one decision in this stack chosen substantially *because* it is the mainstream default, precisely because no credible alternative offers a compelling reason to deviate.

## Risks

Low. Pydantic v2's `pydantic-core` (Rust) dependency means build/CI environments must support the compiled wheel for the target platform — a solved problem via standard wheel distribution, not an operational concern in practice.

## Migration Strategy

Not anticipated. If ever required, Pydantic models are structurally close enough to `attrs`/dataclasses that a mechanical migration is feasible, module by module, given each module's domain layer only depends on its own models (Principle 4).

## Consequences

- Every event payload (`06-events.md`), API request/response, and AI structured-output schema is a Pydantic v2 model — no ad hoc dict-based payloads anywhere in the system.
- AI Research Engine and AI Reasoning Engine validate all vendor output against Pydantic schemas before it is trusted, per [14-ai-architecture.md](../14-ai-architecture.md) and [10-security.md](../10-security.md).
- Event schema versioning ([06-events.md](../06-events.md)) is expressed as versioned Pydantic model classes.

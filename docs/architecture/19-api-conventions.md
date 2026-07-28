# 19 — API Conventions

> Status: **Living document — Architectural Constitution — RATIFIED**
> Audience: All engineers, EMs, and technical stakeholders at Signora
> New in **v3**.

## Purpose

This document specifies the conventions every Signora REST endpoint follows: the error contract, response envelopes, pagination, validation, versioning, and naming. Consistency here is not cosmetic — a client that must handle a different error shape per module is a client that handles errors badly.

Authentication is specified in [18-authentication.md](18-authentication.md); this document covers everything else about the HTTP surface.

## Foundational Rules

- **REST, documented by generated OpenAPI** ([ADR-0002](adr/0002-web-framework-and-api-style.md)). The OpenAPI document is generated from FastAPI routes and Pydantic models and is the binding external contract. Never hand-maintain API documentation alongside it.
- **Every request and response is a Pydantic v2 model** ([ADR-0004](adr/0004-data-validation-and-serialization.md)). No endpoint accepts or returns a bare `dict`.
- **Internal entities are never exposed directly.** Domain entities and SQLAlchemy models stay behind the interface layer; routes return purpose-built response schemas. This keeps the wire contract stable when the domain model changes, and prevents accidentally leaking internal fields.
- **Every endpoint belongs to exactly one module** and lives in that module's `interface/` layer, delegating immediately to an application-layer use case ([15-project-structure.md](15-project-structure.md)).

## Error Contract

Every error response — without exception, from every module — uses one envelope:

```json
{
  "error": {
    "code": "workspace_not_found",
    "message": "Workspace does not exist.",
    "details": [
      { "field": "name", "message": "String should have at most 200 characters" }
    ],
    "correlation_id": "0f2c…"
  }
}
```

| Field | Required | Meaning |
|---|---|---|
| `code` | yes | Stable, machine-readable, `snake_case` identifier. Clients branch on this, never on `message`. |
| `message` | yes | Human-readable, safe to display. Never contains internal identifiers, SQL, or stack traces. |
| `details` | no | Field-level validation problems. Present for `422`; usually absent otherwise. |
| `correlation_id` | yes | Ties the response to server-side logs and traces ([07-data-flow.md](07-data-flow.md)). This is what a support conversation is anchored on. |

`code` is part of the public contract: renaming one is a breaking change. Adding a new code is not.

### Status code usage

| Status | When |
|---|---|
| `200` | Successful read or update. |
| `201` | Resource created. Includes the created resource. |
| `204` | Successful delete, or an accepted action with no body. |
| `400` | Malformed request that is not a schema violation. |
| `401` | Missing, malformed, expired, or unverifiable token ([18-authentication.md](18-authentication.md)). |
| `403` | Authenticated and a verified workspace member, but Casbin denies the action. |
| `404` | Resource does not exist **or** the caller is not a member of its workspace — deliberately indistinguishable, to prevent enumeration. |
| `409` | Conflict with current state (e.g. adding a user who is already a member). |
| `422` | Request failed schema validation. Populates `details`. |
| `500` | Unhandled server fault. Message is always generic; the specifics go to logs and Sentry, never to the client. |

The `404`-not-`403` rule for non-members is a security property, not an oversight. See [18-authentication.md](18-authentication.md).

### Mapping domain errors to responses

Domain and application code raise **domain exceptions** and know nothing about HTTP. A single exception-handler registry in `signora_platform/api/` maps them to the envelope above. Consequences:

- A module never constructs an `HTTPException` in its domain or application layer.
- Adding a domain error means registering one mapping, not editing every route.
- Any unmapped exception becomes a `500` with a generic message — failing closed, never leaking internals.

## Success Responses

**Single resources** are returned as the resource object itself, not wrapped:

```json
{ "id": "8b0f…", "name": "Acme Revenue", "created_at": "2026-07-28T09:12:00Z" }
```

An envelope such as `{"data": …}` on single resources adds a level of nesting to every client access path and buys nothing — pagination, the usual justification, applies only to collections, which have their own envelope below.

**Collections** always use the paginated envelope, even when a result set is currently small. Retrofitting pagination onto an unpaginated endpoint is a breaking change; starting paginated costs nothing.

## Pagination

**Cursor-based**, not offset-based.

```json
{
  "items": [ … ],
  "next_cursor": "eyJpZCI6…",
  "has_more": true
}
```

- `next_cursor` is opaque to clients: they echo it back and never construct or parse it. This lets the server change the underlying keyset without breaking clients.
- `has_more` is explicit rather than inferred from `next_cursor` being non-null, so client code reads clearly.
- Request parameters: `limit` (bounded, with a documented default and maximum) and `cursor`.

**Why cursor over offset:** `OFFSET` degrades linearly as it grows — the database must scan and discard skipped rows — which is untenable against Signora's target scale of millions of companies ([12-scalability.md](12-scalability.md)). Offset pagination is also unstable under concurrent writes: rows shift between pages, so items are silently duplicated or skipped. Signora's pipeline writes continuously, making that failure mode routine rather than theoretical.

## Validation

- Validation is declarative on Pydantic models; handlers do not hand-roll checks that a model constraint expresses.
- FastAPI's validation errors are translated into the standard envelope with `code: "validation_error"` and per-field `details` — clients see one error shape whether the failure was schema-level or domain-level.
- **Client input is never trusted for authorization or scoping.** Notably, a `workspace_id` in a path or body is verified against membership before use ([18-authentication.md](18-authentication.md)).

## Naming and Structure

- Resource paths are plural nouns: `/workspaces`, `/workspaces/{workspace_id}/members`.
- Workspace-scoped resources are nested under `/workspaces/{workspace_id}/…`, making a request's tenant scope legible from its URL alone.
- Path and query parameters, and all JSON fields, are `snake_case` — matching Python and avoiding a serialization-layer rename with no benefit.
- Timestamps are ISO 8601 with an explicit UTC offset.
- Identifiers are UUIDs, serialized as strings.

## Versioning

The API is unversioned in its path today. Backward-compatible evolution — adding fields, adding endpoints, adding error codes — is the expected mode. A breaking change requires an explicit decision and a versioning strategy (path prefix or media-type), recorded as an ADR at that time. Choosing a scheme now, with one first-party client, would be speculative.

## Best Practices

- Return `201` with the created resource, not `200` with an id.
- Give every new error condition a specific `code`; resist a generic `error` catch-all, which pushes clients back to string-matching `message`.
- Paginate every collection from the first commit.
- Keep response schemas separate from domain entities even when they are currently field-identical — they diverge, and coupling them means a domain refactor becomes a client-breaking change.

## Anti-Patterns

- A module inventing its own error shape, or raising `HTTPException` from domain/application code.
- Returning `403` where `404` is required for non-members, reintroducing workspace enumeration.
- Offset pagination.
- Returning a SQLAlchemy model or domain entity directly from a route.
- Leaking exception text, SQL, or stack traces into `message`.
- Unbounded collection endpoints with no `limit` ceiling.

## Tradeoffs

| Choice | We gain | We give up |
|---|---|---|
| Single error envelope across all modules | Clients implement error handling once | Slightly more ceremony than raising `HTTPException` inline |
| Cursor pagination | Stable and performant at scale | Cannot jump to an arbitrary page — accepted; Signora's surfaces are feeds and prioritized lists, not page-numbered tables |
| Separate response schemas from domain entities | Wire contract survives domain refactors | Some duplication between schema and entity |
| Unversioned paths for now | No premature ceremony | A future breaking change requires designing versioning under time pressure |

## Decision Summary

Signora's REST API uses one error envelope with a stable machine-readable `code` and a `correlation_id`, cursor-based pagination for all collections, Pydantic v2 models on every request and response, domain-exception-to-HTTP mapping centralized in `signora_platform/api/`, and a deliberate `404`-for-non-members rule that prevents workspace enumeration. Internal entities are never exposed directly.

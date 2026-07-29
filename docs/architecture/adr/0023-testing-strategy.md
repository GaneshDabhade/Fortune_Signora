# ADR-0023: Testing Strategy

**Status:** Accepted · **Operating mechanism amended by [ADR-0027](0027-local-first-development.md) (2026-07-29):** the suite and the gate stand unchanged; **the gate runs locally**, not in CI.

## Context

[CLAUDE.md](../../../CLAUDE.md) §11 mandates tests for every change, with domain/application layers unit-tested using fakes and integration/e2e tests exercising real infrastructure. This ADR ratifies the concrete tooling for both backend and frontend.

## Decision

**Pytest** for backend test execution. **pytest-mock** for mocking. **HTTPX** for HTTP-layer/API testing. **Vitest** for frontend unit/component tests. **Playwright** for end-to-end browser tests.

## Alternatives Considered

| Layer | Alternative | Why not chosen |
|---|---|---|
| Backend test runner | `unittest` (standard library) | Pytest's fixture system, parametrization, and plugin ecosystem (including async support needed for FastAPI/SQLAlchemy async code, [ADR-0001](0001-backend-language-and-runtime.md), [ADR-0005](0005-orm-and-schema-migrations.md)) are materially more productive than `unittest`'s more verbose, class-based model — Pytest is close to a default choice in the current Python ecosystem for exactly this reason. |
| Mocking | `unittest.mock` directly | pytest-mock is a thin, idiomatic wrapper over `unittest.mock` integrated with Pytest fixtures (`mocker`); chosen for ergonomics, not a fundamentally different capability. |
| HTTP testing | `requests`-based test clients, FastAPI's `TestClient` (sync) only | HTTPX's async client matches FastAPI's async-native request handling ([ADR-0002](0002-web-framework-and-api-style.md)), avoiding the sync/async mismatch of testing an async application with a sync-only client. |
| Frontend unit tests | Jest | Vitest's native Vite/ESM support and materially faster execution (no separate transform step) make it the better fit alongside the Next.js/TypeScript stack ([ADR-0021](0021-frontend-application-stack.md)); Jest remains capable but is comparatively slower and requires more configuration for the same ESM-native codebase. |
| End-to-end | Cypress | Playwright's multi-browser support (including WebKit, relevant given Safari usage among target users), better parallelization, and native TypeScript support were judged superior to Cypress's Chromium-first design for Signora's cross-browser support needs. |

## Tradeoffs

**We gain:** an async-native testing stack matching the async-native application stack throughout (Pytest + HTTPX for backend, Vitest for a Vite/ESM-native frontend build), and Playwright's genuine cross-browser E2E coverage.

**We give up:** nothing material — each choice is close to the current mainstream default for its category, chosen because no compelling alternative displaced it, similar in spirit to [ADR-0004](0004-data-validation-and-serialization.md)'s Pydantic v2 decision.

## Risks

Low. This is a low-controversy, high-consensus cluster of decisions.

## Migration Strategy

Not anticipated. Test suites are organized per [15-project-structure.md](../15-project-structure.md) (module-local unit tests, `backend/tests/integration/` and `backend/tests/e2e/`, `frontend/tests/`), so a future tool swap would be scoped by test category, not require a full rewrite at once.

## Consequences

- Every module's `domain/`/`application/` unit tests use fakes for infrastructure Protocols, run via Pytest.
- API-layer tests use HTTPX's async client against the FastAPI app directly, without a running server process.
- CI ([ADR-0022](0022-devops-infrastructure-and-deployment-topology.md)) runs the full suite (Pytest, Vitest, Playwright) on every PR; a PR with failing or skipped tests does not merge, per [CLAUDE.md](../../../CLAUDE.md) §11.

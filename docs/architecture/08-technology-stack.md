# 08 — Technology Stack

> Status: **Living document — Architectural Constitution — RATIFIED**
> Audience: All engineers, EMs, and technical stakeholders at Signora
> Revision: **v2** — every item formerly marked `TODO` has been resolved by the Architecture Review Board. Full rationale, alternatives, tradeoffs, risks, and migration strategy for each decision below live in the linked ADR under `docs/architecture/adr/`. This document is the summary table; the ADRs are the record of *why*.

## Purpose

This document is the single, authoritative list of Signora's technology stack. Every entry was chosen against the same criteria: scalability, maintainability, developer experience, ecosystem maturity, enterprise readiness, AI-ecosystem fit, long-term ownership cost, operational simplicity, and future evolution path — never popularity alone.

## Responsibilities

- Give engineers one place to find "what do we use for X, and why."
- Link every decision to its ADR, which carries the full alternatives analysis.
- Distinguish what is **decided and binding** from what remains genuinely open (there are a small number of deliberate exceptions, called out explicitly).

## Backend

| Layer | Decision | ADR |
|---|---|---|
| Language & runtime | Python 3.13+ | [ADR-0001](adr/0001-backend-language-and-runtime.md) |
| Web framework | FastAPI | [ADR-0002](adr/0002-web-framework-and-api-style.md) |
| Package manager | uv | [ADR-0003](adr/0003-package-and-dependency-management.md) |
| Validation & serialization | Pydantic v2 | [ADR-0004](adr/0004-data-validation-and-serialization.md) |
| ORM | SQLAlchemy 2.x (async) | [ADR-0005](adr/0005-orm-and-schema-migrations.md) |
| Database migrations | Alembic | [ADR-0005](adr/0005-orm-and-schema-migrations.md) |
| Dependency injection | FastAPI's native `Depends` DI | [ADR-0002](adr/0002-web-framework-and-api-style.md) |
| API style | REST | [ADR-0002](adr/0002-web-framework-and-api-style.md) |
| API documentation | OpenAPI (generated from FastAPI + Pydantic) | [ADR-0002](adr/0002-web-framework-and-api-style.md) |

## Database & Data Platform

| Layer | Decision | ADR |
|---|---|---|
| Primary datastore | PostgreSQL 17+ | [ADR-0006](adr/0006-data-platform-primary-database-and-multi-tenancy.md) |
| Multi-tenancy model | Shared database | [ADR-0006](adr/0006-data-platform-primary-database-and-multi-tenancy.md) |
| Tenant isolation | PostgreSQL Row-Level Security | [ADR-0006](adr/0006-data-platform-primary-database-and-multi-tenancy.md) |
| Cache | Redis | [ADR-0007](adr/0007-caching-layer.md) |
| Full-text / faceted search | Meilisearch | [ADR-0008](adr/0008-search-and-vector-retrieval.md) |
| Vector search | pgvector (PostgreSQL extension) | [ADR-0008](adr/0008-search-and-vector-retrieval.md) |
| Object storage | MinIO (S3-compatible; AWS S3 in production) | [ADR-0009](adr/0009-object-storage.md) |

## Identity & Access

| Layer | Decision | ADR |
|---|---|---|
| Authentication authority | Better Auth, running in Next.js | [ADR-0010](adr/0010-identity-and-access.md), [ADR-0026](adr/0026-jwt-boundary-architecture.md) |
| API identity boundary | RS256 JWT issued by Next.js, verified by FastAPI | [ADR-0026](adr/0026-jwt-boundary-architecture.md) |
| JWT verification library | PyJWT (with `cryptography` for RS256) | [ADR-0026](adr/0026-jwt-boundary-architecture.md) |
| Authorization | Casbin (in-process, FastAPI) | [ADR-0010](adr/0010-identity-and-access.md) |
| OAuth identity providers | Google, Microsoft (via Better Auth, Next.js only) | [ADR-0010](adr/0010-identity-and-access.md) |
| Session management | Better Auth (Next.js). FastAPI is stateless and holds no sessions. | [ADR-0026](adr/0026-jwt-boundary-architecture.md) |

## Background Processing & Event Bus

| Layer | Decision | ADR |
|---|---|---|
| Job queue broker | Redis | [ADR-0011](adr/0011-background-processing-and-event-bus-transport.md) |
| Job execution framework | ARQ | [ADR-0011](adr/0011-background-processing-and-event-bus-transport.md) |
| Durable outbox (event source of truth) | PostgreSQL transactional outbox | [ADR-0011](adr/0011-background-processing-and-event-bus-transport.md), [06-events.md](06-events.md) |
| Durable/agentic workflow orchestration (future) | Temporal | [ADR-0011](adr/0011-background-processing-and-event-bus-transport.md) |

## AI Platform

| Layer | Decision | ADR |
|---|---|---|
| AI provider abstraction | Internal AI Provider Abstraction Layer (ports-and-adapters) | [ADR-0012](adr/0012-ai-platform-architecture.md) |
| Model providers (active) | Anthropic Claude, OpenAI, Google Gemini | [ADR-0012](adr/0012-ai-platform-architecture.md) |
| Model providers (future) | Azure OpenAI | [ADR-0012](adr/0012-ai-platform-architecture.md) |
| Embeddings | OpenAI Embeddings | [ADR-0012](adr/0012-ai-platform-architecture.md) |
| Vector store | pgvector | [ADR-0012](adr/0012-ai-platform-architecture.md), [ADR-0008](adr/0008-search-and-vector-retrieval.md) |
| Prompt management | Internal Prompt Registry | [ADR-0012](adr/0012-ai-platform-architecture.md) |
| Reasoning engine | Custom AI Reasoning Engine (build, see [09-build-vs-buy.md](09-build-vs-buy.md)) | [ADR-0012](adr/0012-ai-platform-architecture.md) |

## Company Data Providers

| Category | Decision | ADR |
|---|---|---|
| Firmographic / contact intelligence | Apollo | [ADR-0013](adr/0013-company-intelligence-provider-strategy.md) |
| Company / people data enrichment | CoreSignal | [ADR-0013](adr/0013-company-intelligence-provider-strategy.md) |
| Technographic data | BuiltWith | [ADR-0013](adr/0013-company-intelligence-provider-strategy.md) |
| Web traffic / engagement data | Similarweb | [ADR-0013](adr/0013-company-intelligence-provider-strategy.md) |
| Email verification | NeverBounce | [ADR-0013](adr/0013-company-intelligence-provider-strategy.md) |
| Future candidates | ZoomInfo, Bombora, Crunchbase, 6sense, PitchBook | [ADR-0013](adr/0013-company-intelligence-provider-strategy.md) |

## CRM Integrations

| Category | Decision | ADR |
|---|---|---|
| CRM (active) | Salesforce, HubSpot, Pipedrive, Zoho | [ADR-0014](adr/0014-crm-integration-strategy.md) |
| CRM (future) | Microsoft Dynamics 365 | [ADR-0014](adr/0014-crm-integration-strategy.md) |

## Communication, Email & Calendar

| Category | Decision | ADR |
|---|---|---|
| Team communication | Slack, Microsoft Teams | [ADR-0015](adr/0015-communication-email-and-calendar-integrations.md) |
| Transactional email | Resend | [ADR-0015](adr/0015-communication-email-and-calendar-integrations.md) |
| Email account integrations | Gmail, Microsoft 365 | [ADR-0015](adr/0015-communication-email-and-calendar-integrations.md) |
| Calendar integrations | Google Calendar, Outlook Calendar | [ADR-0015](adr/0015-communication-email-and-calendar-integrations.md) |

## Commodity Platform Services (Bought)

| Category | Decision | ADR |
|---|---|---|
| Billing | Stripe | [ADR-0016](adr/0016-billing.md) |
| Notifications | Novu | [ADR-0017](adr/0017-notifications.md) |
| Monitoring / tracing | OpenTelemetry + Grafana + Sentry | [ADR-0018](adr/0018-monitoring-and-observability.md) |
| Product analytics | PostHog | [ADR-0019](adr/0019-analytics.md) |
| Feature flags | Flagsmith | [ADR-0020](adr/0020-feature-flags.md) |

## Frontend

| Layer | Decision | ADR |
|---|---|---|
| Framework | Next.js 15+ | [ADR-0021](adr/0021-frontend-application-stack.md) |
| Language | TypeScript | [ADR-0021](adr/0021-frontend-application-stack.md) |
| Styling | Tailwind CSS | [ADR-0021](adr/0021-frontend-application-stack.md) |
| Component library | shadcn/ui | [ADR-0021](adr/0021-frontend-application-stack.md) |
| UI primitives | Radix UI | [ADR-0021](adr/0021-frontend-application-stack.md) |
| Forms | React Hook Form | [ADR-0021](adr/0021-frontend-application-stack.md) |
| Schema validation | Zod | [ADR-0021](adr/0021-frontend-application-stack.md) |
| Icons | Lucide | [ADR-0021](adr/0021-frontend-application-stack.md) |
| Animation | Motion (Framer Motion) | [ADR-0021](adr/0021-frontend-application-stack.md) |
| Tables | TanStack Table | [ADR-0021](adr/0021-frontend-application-stack.md) |
| List/grid virtualization | TanStack Virtual | [ADR-0021](adr/0021-frontend-application-stack.md) |
| Data fetching / server-state | TanStack Query | [ADR-0021](adr/0021-frontend-application-stack.md) |
| Markdown rendering | react-markdown | [ADR-0021](adr/0021-frontend-application-stack.md) |
| Rich text editing | Tiptap | [ADR-0021](adr/0021-frontend-application-stack.md) |
| Theming | next-themes | [ADR-0021](adr/0021-frontend-application-stack.md) |
| Charts | Recharts | [ADR-0021](adr/0021-frontend-application-stack.md) |
| Command palette | cmdk | [ADR-0021](adr/0021-frontend-application-stack.md) |
| Toasts / notifications (UI) | Sonner | [ADR-0021](adr/0021-frontend-application-stack.md) |

## DevOps & Infrastructure

| Layer | Decision | ADR |
|---|---|---|
| Local development / containers | Docker, Docker Compose | [ADR-0022](adr/0022-devops-infrastructure-and-deployment-topology.md) |
| CI/CD | GitHub Actions — **ratified but not operating**; all verification is local | [ADR-0022](adr/0022-devops-infrastructure-and-deployment-topology.md), [ADR-0027](adr/0027-local-first-development.md) |
| Edge routing / reverse proxy | Traefik | [ADR-0022](adr/0022-devops-infrastructure-and-deployment-topology.md) |
| Cloud provider | AWS | [ADR-0022](adr/0022-devops-infrastructure-and-deployment-topology.md) |
| Compute (production) | ECS | [ADR-0022](adr/0022-devops-infrastructure-and-deployment-topology.md) |
| Managed database | RDS for PostgreSQL | [ADR-0022](adr/0022-devops-infrastructure-and-deployment-topology.md) |
| Managed cache | ElastiCache for Redis | [ADR-0022](adr/0022-devops-infrastructure-and-deployment-topology.md) |
| Object storage (production) | S3 | [ADR-0022](adr/0022-devops-infrastructure-and-deployment-topology.md) |
| Log/metric aggregation (infra-level) | CloudWatch | [ADR-0022](adr/0022-devops-infrastructure-and-deployment-topology.md) |
| Secrets management | AWS Secrets Manager | [ADR-0022](adr/0022-devops-infrastructure-and-deployment-topology.md) |

## Testing

| Layer | Decision | ADR |
|---|---|---|
| Backend test framework | Pytest | [ADR-0023](adr/0023-testing-strategy.md) |
| Frontend unit/component tests | Vitest | [ADR-0023](adr/0023-testing-strategy.md) |
| End-to-end tests | Playwright | [ADR-0023](adr/0023-testing-strategy.md) |
| Mocking | pytest-mock | [ADR-0023](adr/0023-testing-strategy.md) |
| HTTP testing | HTTPX | [ADR-0023](adr/0023-testing-strategy.md) |

## Code Quality

| Layer | Decision | ADR |
|---|---|---|
| Backend linting/formatting | Ruff | [ADR-0024](adr/0024-code-quality-and-static-analysis.md) |
| Backend static typing | MyPy | [ADR-0024](adr/0024-code-quality-and-static-analysis.md) |
| Pre-commit enforcement | pre-commit | [ADR-0024](adr/0024-code-quality-and-static-analysis.md) |
| Frontend linting | ESLint | [ADR-0024](adr/0024-code-quality-and-static-analysis.md) |
| Frontend formatting | Prettier | [ADR-0024](adr/0024-code-quality-and-static-analysis.md) |

## Deliberately Still Open

Not every decision belongs at this layer of documentation. The following are intentionally left to be resolved at implementation time, each with a defined resolution path — these are not oversights:

| Item | Why it's still open | Resolution path |
|---|---|---|
| Exact PostgreSQL/Redis/Meilisearch managed-service tiers and instance sizing | Depends on real traffic/cost modeling not yet available | Resolved per-environment via infrastructure-as-code review, not an architecture decision |
| Specific Casbin policy model (RBAC vs. ABAC schema) | Depends on the final permission matrix product defines | Tracked as an implementation RFC against [ADR-0010](adr/0010-identity-and-access.md) |
| Exact ARQ vs. Temporal workload boundary beyond AI Research Engine | Requires operational experience with ARQ at production load first | Revisit at the trigger conditions defined in [12-scalability.md](12-scalability.md) and [ADR-0011](adr/0011-background-processing-and-event-bus-transport.md) |

## Design Rationale

Every decision above was made by the same method, documented per-decision in its ADR: identify 2–4 credible alternatives, evaluate them against scalability, maintainability, developer experience, ecosystem maturity, enterprise readiness, AI-ecosystem fit, long-term ownership cost, and operational simplicity, and select the option that wins on the combination — not the option that is currently most popular or most familiar. Several choices (Better Auth over a larger incumbent, Meilisearch over Elasticsearch, ARQ over Celery) are deliberately contrarian relative to "what most companies pick"; the ADRs explain why that is the right call for Signora specifically, not a default.

## Best Practices

- Before adding any new library, framework, or vendor, check this document; if it's not listed, raise an ADR first, following the template in `docs/architecture/adr/README.md`.
- When you disagree with a ratified decision, the mechanism is a new or amending ADR, not a unilateral substitution in a PR.
- Keep this table and the "Decided" state of each linked ADR in sync — if an ADR's status changes (superseded, deprecated), update this table in the same PR.

## Anti-Patterns

- Introducing a second job queue framework alongside ARQ "just for this one feature."
- Adding a vector database (Pinecone, Weaviate, etc.) when pgvector already covers the requirement — see [ADR-0008](adr/0008-search-and-vector-retrieval.md) for the explicit rejection rationale.
- Bypassing Better Auth/Casbin with a bespoke permission check "just this once."
- Treating the "Deliberately Still Open" table as license to leave other, non-listed items unresolved.

## Tradeoffs

See each linked ADR for the full per-decision tradeoff analysis. The system-wide tradeoff this stack makes, consistently, is: **fewer moving parts and stronger PostgreSQL-centrality over maximum per-concern specialization** — e.g., pgvector over a dedicated vector database, Redis-backed ARQ over a dedicated broker, a Postgres outbox over a message bus. This is a deliberate, repeated pattern, not thirteen unrelated choices, and it is the direct expression of Principle 6 and Principle 15.

## Future Evolution

- Every "commodity" bought vendor (Better Auth, Stripe, Novu, PostHog, Flagsmith, etc.) is accessed through an abstraction consistent with Principles 9–11 wherever the architecture calls for it, so it can be swapped with contained blast radius — see the relevant ADR's Migration Strategy section.
- The single largest medium-term evolution to plan for is workflow orchestration: Temporal is the ratified target for AI Research Engine's agentic workloads once ARQ's limitations for long-running, resumable, multi-step processes are actually hit in production — see [ADR-0011](adr/0011-background-processing-and-event-bus-transport.md) and [17-future-recommendations.md](17-future-recommendations.md).

## Decision Summary

Signora's technology stack is fully ratified: Python 3.13/FastAPI/uv/Pydantic v2/SQLAlchemy 2.x/Alembic on the backend; PostgreSQL 17 with RLS, Redis, Meilisearch, and pgvector on the data layer; Better Auth/Casbin for identity; Redis/ARQ (Postgres-outbox-backed) for background processing and the event bus, with Temporal as the ratified future path for durable agentic workflows; a multi-vendor AI Provider Abstraction Layer over Claude/OpenAI/Gemini; Next.js 15/TypeScript on the frontend; and AWS/ECS/RDS/ElastiCache/S3 for production infrastructure. Every decision is backed by a dedicated ADR carrying the full alternatives analysis.

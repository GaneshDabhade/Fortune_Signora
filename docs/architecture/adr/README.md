# Architecture Decision Records

This directory contains every Architecture Decision Record (ADR) ratified by Signora's Architecture Review Board. An ADR is the permanent record of *why* a decision was made — the alternatives considered, the tradeoffs accepted, the risks taken on, and the migration path if the decision needs to be reversed. [08-technology-stack.md](../08-technology-stack.md) and [09-build-vs-buy.md](../09-build-vs-buy.md) are the summary tables; these documents are the reasoning behind every row in those tables.

## Status

All ADRs below are **Accepted** as of this revision unless marked otherwise. An ADR is never edited to reverse a decision — a reversal is a new ADR that **supersedes** the old one, which is marked `Superseded by ADR-XXXX` but left in place as historical record.

## Template

Every ADR follows this structure:

1. **Status** — Proposed / Accepted / Superseded
2. **Context** — what problem/decision this addresses, and the constraints already fixed by [02-principles.md](../02-principles.md)
3. **Decision** — the concrete choice
4. **Alternatives Considered** — a table of credible alternatives and why each was not chosen
5. **Tradeoffs** — what we gain, what we give up
6. **Risks** — what could go wrong with this decision specifically (distinct from the system-wide register in [16-architecture-risks.md](../16-architecture-risks.md), though they cross-reference)
7. **Migration Strategy** — how we would move off this decision if it stopped being right
8. **Consequences** — what this decision requires of other parts of the system

## Index

| ADR | Title |
|---|---|
| [0001](0001-backend-language-and-runtime.md) | Backend Language & Runtime — Python 3.13+ |
| [0002](0002-web-framework-and-api-style.md) | Web Framework & API Style — FastAPI, REST, OpenAPI |
| [0003](0003-package-and-dependency-management.md) | Package & Dependency Management — uv |
| [0004](0004-data-validation-and-serialization.md) | Data Validation & Serialization — Pydantic v2 |
| [0005](0005-orm-and-schema-migrations.md) | ORM & Schema Migrations — SQLAlchemy 2.x + Alembic |
| [0006](0006-data-platform-primary-database-and-multi-tenancy.md) | Data Platform: Primary Database & Multi-Tenancy — PostgreSQL 17 + RLS |
| [0007](0007-caching-layer.md) | Caching Layer — Redis |
| [0008](0008-search-and-vector-retrieval.md) | Search & Vector Retrieval — Meilisearch + pgvector |
| [0009](0009-object-storage.md) | Object Storage — MinIO / AWS S3 |
| [0010](0010-identity-and-access.md) | Identity & Access — Better Auth + Casbin + OAuth |
| [0011](0011-background-processing-and-event-bus-transport.md) | Background Processing & Event Bus Transport — Redis + ARQ, Temporal future path |
| [0012](0012-ai-platform-architecture.md) | AI Platform Architecture — Provider abstraction, models, embeddings, prompt registry |
| [0013](0013-company-intelligence-provider-strategy.md) | Company Intelligence Provider Strategy |
| [0014](0014-crm-integration-strategy.md) | CRM Integration Strategy |
| [0015](0015-communication-email-and-calendar-integrations.md) | Communication, Email & Calendar Integrations |
| [0016](0016-billing.md) | Billing — Stripe |
| [0017](0017-notifications.md) | Notifications — Novu |
| [0018](0018-monitoring-and-observability.md) | Monitoring & Observability — OpenTelemetry + Grafana + Sentry |
| [0019](0019-analytics.md) | Analytics — PostHog |
| [0020](0020-feature-flags.md) | Feature Flags — Flagsmith |
| [0021](0021-frontend-application-stack.md) | Frontend Application Stack — Next.js 15 ecosystem |
| [0022](0022-devops-infrastructure-and-deployment-topology.md) | DevOps, Infrastructure & Deployment Topology — Docker/GitHub Actions/Traefik/AWS |
| [0023](0023-testing-strategy.md) | Testing Strategy |
| [0024](0024-code-quality-and-static-analysis.md) | Code Quality & Static Analysis Tooling |
| [0025](0025-module-boundary-evolution.md) | Module Boundary Evolution — Provider Platform, Business Event Engine, Buying Score Engine, AI Research/Reasoning split |
| [0026](0026-jwt-boundary-architecture.md) | JWT Boundary Architecture — authentication in Next.js, verification in FastAPI (amends 0010) |
| [0027](0027-local-first-development.md) | Local-First Development — all verification is local; GitHub is version control and backup only (amends the operating mechanism of 0022, 0023, 0024) |
| [0028](0028-model-runtime-by-environment.md) | Model Runtime by Environment — Ollama for development, hosted commercial models for production (amends 0012) |
| [0029](0029-operational-history-durability.md) | Operational History Durability — a failed inference's record survives a rolled-back unit of work; operational history has the lifetime of the operation, not the enclosing business transaction |
| [0030](0030-the-decision-package.md) | The Decision Package — what M9 produces, and who authors each part. **Deterministic Explainability**: whatever the platform already knows is derived, never regenerated; the model authors three fields of fifteen |
| [0031](0031-evidence-citation-protocol.md) | The renderer and the parser disagree about the citation protocol |
| [0032](0032-release-certification.md) | Release Certification: the evidence a version carries, not a sixth kind of test |
| [0033](0033-authentication-methods.md) | Authentication Methods Are Configuration — email + password alongside OAuth; the method changes and the authenticated identity does not |
| [0034](0034-ubiquitous-language.md) | The Product's Ubiquitous Language — *Organization* is what a customer says, *workspace* is what the platform says, and the boundary is enforced by a test |
| [0035](0035-commercial-profile.md) | Commercial Profile — the head of the intelligence pipeline: the bounded context that records what a customer declares, and the owner ICP never had |

## How to Propose a New ADR

Follow the RFC process in [01-overview.md](../01-overview.md). A new ADR is required for: any new vendor/technology adoption, any reversal of an existing ADR, or any change to module boundaries. Number sequentially from the highest existing ADR; never reuse a number.

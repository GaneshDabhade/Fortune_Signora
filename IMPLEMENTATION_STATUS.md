# Implementation Status

> ⚙️ **GENERATED — do not edit by hand.** Rebuild with `python3 infra/implementation-status.py`.
> **Manual edits are lost on the next run, and a generated file carrying them drifts while nobody trusts the regeneration.**

> Counted at `f7a0d1d`. **Every figure is arithmetic over the repository, never a claim about intent.**
> **What a screen looks like is not counted here** — the approved specification is
> [`410`](docs/architecture/410-approved-ui-specification.md), and UI convergence is tracked in
> [`412`](docs/architecture/412-backend-capability-matrix.md).

## Backend, by module

| Module | Domain | Application | Infrastructure | Interface | Endpoints | Events | `public/` | Tests | Design doc |
|---|---|---|---|---|---|---|---|---|---|
| `ai_platform` | ✅ | ✅ | ✅ | ✅ | 1 | 1 | ✅ | 12 | 28-ai-platform.md |
| `ai_reasoning_engine` | ✅ | ✅ | ✅ | ✅ | 1 | 1 | ✅ | 8 | 29-ai-reasoning-engine.md |
| `ai_research_engine` | ✅ | ✅ | ✅ | ✅ | 2 | 2 | ✅ | 12 | 33-ai-research-engine-scope.md |
| `business_event_engine` | ✅ | ✅ | ✅ | ✅ | 1 | 2 | ✅ | 4 | 24-business-event-engine.md |
| `buying_score_engine` | ✅ | ✅ | ✅ | ✅ | 1 | 1 | ✅ | 5 | 26-buying-score-engine.md |
| `commercial_profile` | ✅ | ✅ | ✅ | ✅ | 13 | 1 | ✅ | 8 | 40-commercial-profile.md |
| `integrations` | ✅ | ✅ | ✅ | ✅ | 5 | 0 | ✅ | 13 | 13-integrations.md |
| `knowledge_graph` | ✅ | ✅ | ✅ | ✅ | 2 | 6 | ✅ | 4 | 22-knowledge-graph.md |
| `observation_engine` | ✅ | ✅ | ✅ | ✅ | 1 | 2 | ✅ | 4 | 23-observation-engine.md |
| `opportunity_engine` | ✅ | ✅ | ✅ | ✅ | 5 | 2 | ✅ | 3 | 27-opportunity-engine.md |
| `provider_normalization` | ✅ | ✅ | ✅ | ✅ | 0 | 1 | ✅ | 0 | — |
| `provider_platform` | ✅ | ✅ | ✅ | ✅ | 0 | 4 | ✅ | 6 | 41-provider-platform.md |
| `sales_engagement` | ✅ | ✅ | ✅ | ✅ | 1 | 0 | ✅ | 14 | 50-sales-engagement.md |
| `signal_engine` | ✅ | ✅ | ✅ | ✅ | 4 | 2 | ✅ | 8 | 25-signal-engine.md |
| `timeline` | ✅ | ✅ | ✅ | ✅ | 1 | 0 | ✅ | 3 | 45-timeline.md |
| `workspace_tenancy` | ✅ | ✅ | ✅ | ✅ | 13 | 2 | ✅ | 0 | — |

**16 modules · 51 endpoints across 14 routers · 27 event types · 104 backend test files.**

## Frontend

| | Count |
|---|---|
| Routes (`page.tsx`) | 12 |
| API routes (`route.ts`) | 6 |
| Components | 48 |
| Test files | 62 |

> **51 endpoints behind 12 routes.** That ratio is the repository's
> central fact and the reason this file counts backend and frontend separately rather than blending them into
> one percentage — **one number would hide the only interesting thing here.**


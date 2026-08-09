# Implementation Status

> ⚙️ **GENERATED — do not edit by hand.** Rebuild with `python3 infra/implementation-status.py`.
> **Manual edits are lost on the next run, and a generated file carrying them drifts while nobody trusts the regeneration.**

> Counted at `a9bdca72`. **Every figure is arithmetic over the repository, never a claim about intent.**
> **What a screen looks like is not counted here** — the approved specification is
> [`410`](docs/architecture/410-approved-ui-specification.md), and UI convergence is tracked in
> [`412`](docs/architecture/412-backend-capability-matrix.md).

## Backend, by module

| Module | Domain | Application | Infrastructure | Interface | Endpoints | Events | `public/` | Tests | Design doc |
|---|---|---|---|---|---|---|---|---|---|
| `action_batch` | ✅ | ✅ | ✅ | — | 0 | 0 | ✅ | 4 | 53-action-batch.md |
| `ai_platform` | ✅ | ✅ | ✅ | ✅ | 1 | 1 | ✅ | 12 | 28-ai-platform.md |
| `ai_reasoning_engine` | ✅ | ✅ | ✅ | ✅ | 1 | 1 | ✅ | 9 | 29-ai-reasoning-engine.md |
| `ai_research_engine` | ✅ | ✅ | ✅ | ✅ | 2 | 2 | ✅ | 12 | 33-ai-research-engine-scope.md |
| `business_event_engine` | ✅ | ✅ | ✅ | ✅ | 1 | 2 | ✅ | 4 | 24-business-event-engine.md |
| `buying_score_engine` | ✅ | ✅ | ✅ | ✅ | 1 | 1 | ✅ | 5 | 26-buying-score-engine.md |
| `commercial_profile` | ✅ | ✅ | ✅ | ✅ | 13 | 1 | ✅ | 9 | 40-commercial-profile.md |
| `integrations` | ✅ | ✅ | ✅ | ✅ | 5 | 0 | ✅ | 13 | 13-integrations.md |
| `knowledge_graph` | ✅ | ✅ | ✅ | ✅ | 3 | 6 | ✅ | 5 | 22-knowledge-graph.md |
| `observation_engine` | ✅ | ✅ | ✅ | ✅ | 1 | 2 | ✅ | 4 | 23-observation-engine.md |
| `opportunity_engine` | ✅ | ✅ | ✅ | ✅ | 7 | 2 | ✅ | 6 | 27-opportunity-engine.md |
| `people` | ✅ | ✅ | ✅ | — | 0 | 0 | ✅ | 6 | 39-product-review-findings.md |
| `provider_normalization` | ✅ | ✅ | ✅ | ✅ | 0 | 1 | ✅ | 0 | — |
| `provider_platform` | ✅ | ✅ | ✅ | ✅ | 1 | 5 | ✅ | 9 | 41-provider-platform.md |
| `sales_engagement` | ✅ | ✅ | ✅ | ✅ | 1 | 0 | ✅ | 14 | 50-sales-engagement.md |
| `signal_engine` | ✅ | ✅ | ✅ | ✅ | 6 | 3 | ✅ | 11 | 25-signal-engine.md |
| `timeline` | ✅ | ✅ | ✅ | ✅ | 1 | 0 | ✅ | 3 | 45-timeline.md |
| `workspace_tenancy` | ✅ | ✅ | ✅ | ✅ | 30 | 2 | ✅ | 0 | — |

**18 modules · 74 endpoints across 15 routers · 29 event types · 126 backend test files.**

> **2 modules have no `interface/` layer: `action_batch` · `people`.**
> **Some of these are correct** — a pipeline stage is not a request surface. **The rest are the recurring
> pattern**: built, tested, published and unreachable. The three-question heuristic decides which is which —
> *does it exist · can a customer reach it · is it consumed elsewhere*.

## Frontend

| | Count |
|---|---|
| Routes (`page.tsx`) | 24 |
| API routes (`route.ts`) | 6 |
| Components | 67 |
| Test files | 85 |

> **74 endpoints behind 24 routes.** That ratio is the repository's
> central fact and the reason this file counts backend and frontend separately rather than blending them into
> one percentage — **one number would hide the only interesting thing here.**


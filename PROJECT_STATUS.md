# PROJECT_STATUS.md

> **Owner:** Technical Program Manager · **Audience:** Everyone
> **Cadence:** Updated at every milestone boundary and every sprint close. Updating this is part of the [Definition of Done](IMPLEMENTATION_ROADMAP.md#9-definition-of-done).
> **Last updated:** 2026-07-28 · **Reporting period:** Project inception → M0 close

---

## Overall Progress

```
Foundation      ████████████████████ 100%  ✅ Complete
Runtime Spine   ░░░░░░░░░░░░░░░░░░░░   0%  🔴 Next
Data Ingestion  ░░░░░░░░░░░░░░░░░░░░   0%
Intelligence    ░░░░░░░░░░░░░░░░░░░░   0%
AI Platform     ░░░░░░░░░░░░░░░░░░░░   0%
Product Surface ░░░░░░░░░░░░░░░░░░░░   0%
GA Readiness    ░░░░░░░░░░░░░░░░░░░░   0%
```

| Dimension | Status |
|---|---|
| **Overall completion to GA** | **~5%** by engineering effort (~14 of ~200–266 remaining engineer-weeks delivered) |
| Architecture & design | **100%** — 19 documents, 27 ADRs, ratified and internally consistent |
| Core modules | **1 of 14** (7%) |
| Backend platform | ~60% of foundation scope; 0% of pipeline scope |
| Frontend | **0%** — not started |
| Infrastructure-as-code | **0%** — local Docker Compose only |
| AI capability | **Level 0 of 12** ([AI_MATURITY_ROADMAP.md](AI_MATURITY_ROADMAP.md)) |

**Honest read:** documentation and foundation quality are well ahead of feature surface, which is the correct order for a system whose hardest-to-retrofit properties are tenancy and evidence provenance. But **~95% of differentiating capability remains to be built**, and the pipeline's strict dependency chain means it cannot be heavily parallelised. Progress percentage will look slow through Phases 1–2 and then accelerate.

---

## Completed Milestones

### ✅ M0 — Secure Multi-Tenant Foundation · closed 2026-07-28

| Delivered | Evidence |
|---|---|
| Full architecture documentation set | 19 docs + 27 ADRs; 651 cross-links verified |
| Product strategy | [PRODUCT_DIFFERENTIATORS.md](PRODUCT_DIFFERENTIATORS.md) |
| Engineering constitution | [CLAUDE.md](CLAUDE.md) |
| Workspace & Tenancy module | All 5 layers, 5 use cases, 4 REST endpoints |
| Platform: db, event_bus (publisher), auth, authorization, api, pagination | ~1,288 LOC |
| PostgreSQL RLS tenant isolation | 4 migrations, reversible, adversarially tested |
| JWT auth boundary (ADR-0026) | RS256, pinned algorithms, forged-attack tests |
| Casbin authorization | Workspace-scoped policy, unit-tested |
| CI pipeline definition | GitHub Actions: ruff, mypy, import-linter, pytest |

**Notable during M0 — three defects found by testing, not review:**

1. `FORCE ROW LEVEL SECURITY` does not constrain superusers. Connecting as one silently disables all tenant isolation. Fixed with a least-privilege role plus a test guard that fails the suite if pointed at a bypass-capable connection.
2. `membership`'s read policy never required the caller to *be* a member — only that `app.workspace_id` matched. Enforcement was effectively delegated to application code. Fixed in migration 0003 with `SECURITY DEFINER` predicates.
3. `platform` shadows a Python standard-library module, making the documented layout unrunnable. Renamed to `signora_platform`.

All three are documented in the architecture set rather than silently patched.

---

## Current Milestone

### 🔄 M1 — Runtime Spine · **NOT STARTED**

**Phase:** 1 · **Estimate:** ~22–30 engineer-weeks (~5–6 calendar weeks at reference staffing) · **Label:** 🏗️ Foundation

| Deliverable | Est. | Status |
|---|---|---|
| Event bus relay + ARQ worker fleet + DLQ | 5–7 ew | ⬜ Not started |
| Better Auth issuer (Next.js) + frontend shell | 6–8 ew | ⬜ Not started |
| Observability: OpenTelemetry, Sentry, structured logging | 4–5 ew | ⬜ Not started |
| Terraform/AWS baseline | 5–7 ew | ⬜ Not started |
| `pytest-cov` + coverage gate | 0.5 ew | ⬜ Not started |
| Abstraction layer scaffolds | 2–3 ew | ⬜ Not started |

**Exit condition:** an event published by Workspace & Tenancy is observably relayed to an ARQ worker, traced end-to-end, in a deployed environment, by a human who authenticated through Better Auth.

**Architecture checkpoint:** AC-1 — Event Bus Contract.

---

## Current Sprint

**Sprint:** Not yet started — M1 Sprint 1 pending kickoff.

**Proposed Sprint 1 scope** (highest-unblock-value first):

| # | Item | Why first |
|---|---|---|
| 1 | Event bus relay + ARQ worker fleet | Unblocks all 13 pipeline modules — nothing competes |
| 2 | Better Auth issuer in Next.js | Unblocks all human access; runs fully in parallel (different codebase) |
| 3 | `pytest-cov` + CI coverage gate | 0.5 ew; closes a measurement gap now rather than later |
| 4 | Knowledge Graph spike (timeboxed, 2 weeks) | Retires the roadmap's largest estimation risk while re-planning is still cheap |

**Not in Sprint 1:** any pipeline module. They are blocked on item 1 and starting them early produces rework.

---

## Blocked Items

| Item | Blocked by | Severity | Owner |
|---|---|---|---|
| All 13 core intelligence modules | Event bus relay | 🔴 Critical | Unassigned |
| Any human access / any demo | Better Auth issuer (Next.js) | 🔴 Critical | Unassigned |
| Any deployed environment | Terraform/AWS baseline | 🟠 High | Unassigned |
| Provider Platform | Provider Abstraction Layer scaffold | 🟠 High | Unassigned |
| Both AI engines | AI Provider Abstraction Layer + Prompt Registry | 🟠 High | Unassigned |
| Trustworthy AI output | AI Evaluation Harness (R-10) | 🟠 High | Unassigned |
| PII/retention implementation | **Legal/Compliance policy input** (R-04, R-05) | 🟡 Medium | **Escalated — not an engineering blocker** |

**Two blockers dominate.** The event bus relay and the Better Auth issuer sit in different codebases and can be worked simultaneously by different people. Until both clear, essentially no forward progress is possible on anything else.

**Staffing is currently the meta-blocker:** every item above is unassigned.

---

## Architecture Risks

Full register: [16-architecture-risks.md](docs/architecture/16-architecture-risks.md). **12 open, 1 resolved.**

| ID | Risk | Sev | Status |
|---|---|---|---|
| R-01 | AI vendor cost exposure without budget governance | 🔴 High | Open — must resolve before AI Research Engine is broadly enabled |
| R-04 | PII classification / retention / workspace lifecycle undefined | 🔴 High | **Escalated to Legal** — long lead time; start now |
| R-05 | AI prompt data-classification policy undefined | 🔴 High | **Escalated to Legal** |
| R-10 | No AI evaluation methodology | 🔴 High | Open — Phase 4, before engines ship |
| R-02 | Single-region vs. enterprise data residency | 🟠 Med | Open — audit schema now, build later |
| R-03 | RLS query performance not load-tested at scale | 🟠 Med | Open — Phase 6 |
| R-06 | Cross-workspace admin/support access undefined | 🟠 Med | Open — before support tooling is built |
| R-08 | Meilisearch/pgvector not validated at scale | 🟠 Med | Open — Phase 6 |
| R-12 | SOC 2 / enterprise compliance gap | 🟠 Med | Open — schedule in parallel with enterprise GTM |
| R-11 | Vendor concentration on younger projects | 🟡 Low-Med | Accepted, monitored quarterly |
| R-07 | API/pipeline latency SLOs undefined | 🟡 Low | Open — set from telemetry post-M1 |
| R-09 | AI Research Engine timeout undefined | 🟡 Low | Open — set from telemetry in Phase 4 |
| R-13 | Better Auth is TypeScript-native | — | ✅ **Resolved** by [ADR-0026](docs/architecture/adr/0026-jwt-boundary-architecture.md) |

**Most urgent by lead time, not severity:** R-04 and R-05. They require Legal/Compliance input that engineering cannot supply, and formal policy work has a long tail. Starting them at Phase 6 would be starting them late.

---

## Technical Debt

Deliberately small at this stage. Everything below is **known, recorded, and consciously accepted** — none of it is discovered debt.

| Item | Impact | Rationale for accepting | Repay by |
|---|---|---|---|
| **Test coverage unmeasured** — `pytest-cov` not installed | Medium | Oversight, not a decision | M1 Sprint 1 |
| **Event bus relay unimplemented** | 🔴 Critical | Deliberate: dispatch with zero consumers is untestable | M1 |
| **`apps/worker` is an empty stub** | High | Same deferral | M1 |
| **JWT key rotation requires a deploy** | Medium | JWKS adds a cache, fetch path, and failure mode not yet justified | Post-GA |
| **Token revocation not immediate** (15-min TTL window) | Medium | Standard JWT tradeoff; `sid`/`jti` carried so a revocation list needs no contract change | Post-GA if the window proves unacceptable |
| **No structured logging** | Medium | Deferred with observability | M1 |
| **Casbin policy is coarse RBAC** | Low | Correct for current permission needs | When enterprise custom roles are required |
| **No API versioning scheme** | Low | Deliberate: choosing one now, with a single first-party client, would be speculative | First breaking change |

**Debt ratio: healthy.** The dominant items are deferred-by-design and scheduled, not accumulated by shortcut.

---

## Known Bugs

**None open.**

Three defects were found and fixed during M0 (superuser RLS bypass, non-self-sufficient membership policy, stdlib name shadowing) — all documented in the architecture set with regression tests proven to fail against the pre-fix state.

**Caveat worth stating plainly:** "no known bugs" across ~2,660 LOC with one module in existence and zero production traffic is a weak signal. It should not be read as a quality claim.

---

## Test Coverage

| Metric | Value |
|---|---|
| Total tests | **116 passing**, 0 failing, 0 skipped |
| Unit tests | 79 (domain, application, JWT verifier, Casbin, pagination) |
| Integration tests | 37 (real PostgreSQL 17 as least-privilege role) |
| Test LOC | ~2,058 (~77% of production LOC — appropriate for security-critical foundation) |
| **Line coverage** | ⚠️ **Not measured** — `pytest-cov` not installed |
| Type coverage | ✅ mypy `strict`, 71 files, zero errors |
| Boundary enforcement | ✅ 3 import-linter contracts, verified to fail on deliberate violation |
| Migration reversibility | ✅ Verified across all 4 revisions |

**Test quality signals worth noting:**
- The `alg:none` and algorithm-confusion tests initially passed *for the wrong reason* — PyJWT refuses to mint those tokens. Both were rewritten with hand-forged tokens.
- RLS regression tests were run against pre-fix policies to confirm they fail, then re-run after. A test never seen to fail is not known to work.

**Action:** install `pytest-cov`, establish a baseline, add a CI gate. M1 Sprint 1.

---

## Documentation Status

| Document set | Status |
|---|---|
| Architecture (19 docs) | ✅ Complete, ratified, internally consistent |
| ADRs (27) | ✅ Complete; every technology and boundary decision recorded |
| [CLAUDE.md](CLAUDE.md) | ✅ Complete — 21 sections |
| [PRODUCT_DIFFERENTIATORS.md](PRODUCT_DIFFERENTIATORS.md) | ✅ Complete |
| [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) | ✅ New |
| [PRODUCT_ROADMAP.md](PRODUCT_ROADMAP.md) | ✅ New |
| [AI_MATURITY_ROADMAP.md](AI_MATURITY_ROADMAP.md) | ✅ New |
| PROJECT_STATUS.md | ✅ This document |
| API reference | ✅ Generated (OpenAPI) — not hand-maintained, by design |
| Operations runbook | ⬜ Not started — needed by M1 (first deployed environment) |
| Onboarding guide | ⬜ Not started — needed when team grows past ~3 |

**Documentation drift: zero.** All 651 internal links resolve. Docs have been updated in the same commit as the code they describe, every time.

**Gap:** no operations runbook. Becomes real the moment M1 produces a deployed environment.

---

## Next Task

### 🎯 Implement the event bus relay and ARQ worker fleet

**Why this and nothing else:** it unblocks all 13 core intelligence modules. No other available task has comparable leverage, and most other tasks are downstream of it.

**Scope:**
- Outbox relay: `LISTEN/NOTIFY` → Redis enqueue, marking rows relayed
- ARQ worker entry points under `apps/worker/`, partitioned per pipeline stage ([12-scalability.md](docs/architecture/12-scalability.md))
- Consumer registration against the Internal Event Bus abstraction
- Retry with backoff; dead-letter queue plus a Postgres audit table
- Idempotent delivery keyed on `event_id`
- `correlation_id` propagation through dispatch
- Integration tests: at-least-once delivery, duplicate handling, DLQ behaviour, ordering per entity

**Acceptance:** architecture checkpoint **AC-1** passes — an event published by Workspace & Tenancy is durably relayed, consumed idempotently, and traced end-to-end.

**Parallel track (different codebase, no contention):** Better Auth issuer in Next.js. Until it exists, nobody can log in and no demo is possible.

---

## Change Log

| Date | Change |
|---|---|
| 2026-07-28 | Initialized. M0 closed. Roadmap documents created. |

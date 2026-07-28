# PROJECT_STATUS.md

> **Owner:** Technical Program Manager · **Audience:** Everyone
> **Cadence:** Updated at every milestone boundary and every sprint close. Updating this is part of the [Definition of Done](IMPLEMENTATION_ROADMAP.md#12-definition-of-done-global).
> **Last updated:** 2026-07-28 · **Reporting period:** M1.2 delivery
> **Revision:** v6 — **M1.2 complete and approved.** Security Invariants suite established (47 invariants); M1.3 split into M1.3A/M1.3B; M1.4 Platform Smoke Test added

---

## Overall Progress

```
M0  Foundation             ████████████████████ 100%  ✅ Complete
M1.1 Platform Runtime      ████████████████████ 100%  ✅ Complete
M1.2 Auth Boundary         ████████████████████ 100%  ✅ Complete
M1.3A Deployment Foundation ░░░░░░░░░░░░░░░░░░░   0%  🔴 CURRENT — next
M1.3B Cloud Infrastructure  ░░░░░░░░░░░░░░░░░░░   0%  ⏸ Queued (after M1.3A)
M1.4 Platform Smoke Test    ░░░░░░░░░░░░░░░░░░░   0%  ⏸ Queued (after M1.3A)
M2.0 Simulation Framework   ░░░░░░░░░░░░░░░░░░░   0%  ⏸ Queued (after M1.4)
M2.1 → M15                 ░░░░░░░░░░░░░░░░░░░░   0%  ⏸ Queued
```

**Execution model: sequential single stream.** One milestone at a time, in the order above. Parallel workstreams are documented in [IMPLEMENTATION_ROADMAP.md §9](IMPLEMENTATION_ROADMAP.md#9-parallel-workstreams--retained-for-future-scaling) for future scaling but are **not** the current operating assumption.

| Dimension | Status |
|---|---|
| **Overall completion to GA** | **~16%** by engineering effort (~42 of ~239–319 total engineer-weeks; ~198–278 ew remaining) |
| Architecture & design | **100%** — 19 documents, 27 ADRs, ratified and internally consistent |
| Core modules | **1 of 14** (7%) |
| Backend platform | ~85% of foundation scope; 0% of pipeline scope |
| Frontend | **~25%** — auth boundary, shell, and API client complete |
| Infrastructure-as-code | **0%** — local Docker Compose only |
| Provider simulation | **0%** — newly scoped (M2.0) |
| AI capability | **Level 0 of 12** ([AI_MATURITY_ROADMAP.md](AI_MATURITY_ROADMAP.md)) |

### Calendar under sequential execution

Total effort is unchanged at **~225–305 ew**. Calendar time depends entirely on staffing, and sequential execution forfeits parallel compression:

| Team size | M1 (33 ew) | M1 + M2.0 | **To GA** |
|---|---|---|---|
| **1 engineer** | ~41 weeks | ~62–71 weeks | **~5.4–7.3 years** |
| **2 engineers** | ~21 weeks | ~31–36 weeks | **~2.7–3.7 years** |
| **3 engineers** | ~14 weeks | ~21–24 weeks | **~1.8–2.4 years** |

Assumes 80% effective capacity. Within a milestone, additional engineers help only up to the **critical path** — M1.1's chain (T6→T7→T8→T9→T10) is ~10 ew of serial work and cannot compress below that at any headcount.

**This is not an argument against the decision.** For a small team, context switching destroys more throughput than parallelism recovers. But the timeline consequence is owned here, at planning time, rather than surfaced later as a slip.

**Highest-leverage lever if the GA horizon matters commercially:** the second and third engineer. Moving 1 → 3 roughly triples throughput. Beyond ~3, the pipeline's serial dependency chain limits further gains.

**Honest read:** progress will look flat through M1 and M2.0, then accelerate. That is a property of building a runtime spine and a test substrate before features, not slow execution.

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
| CI pipeline definition | ruff, mypy, import-linter, pytest |
| Execution roadmap | 4 planning documents |

**Three defects found by testing, not review:** superuser RLS bypass · membership policy that delegated enforcement to application code · `platform` shadowing a stdlib module. All fixed, documented, and covered by regression tests proven to fail against the pre-fix state.

### ✅ M1.1 — Platform Runtime · closed 2026-07-28

All 11 tasks delivered. **Demo Checklist: 13/13 passed. AC-1 passed.**

| Delivered | Evidence |
|---|---|
| Coverage measurement + CI gate (T1, T2) | 95.01% measured, gate at 95%, Redis service in CI |
| Structured JSON logging with redaction (T3) | 23 tests; JWT/bearer/secret redaction proven |
| Event bus dispatch schema (T6) | Migration 0004: `processed_event`, `dead_letter_event`, relay columns |
| Outbox relay (T7) | 12 integration tests; concurrent-relay safety via `SKIP LOCKED` |
| Dispatch + platform-owned idempotency (T8) | 14 integration tests; exactly-once proven under concurrency |
| ARQ worker fleet, 7 pools (T9) | Per-stage pools; `ai_research` at concurrency 2 / 1800s timeout |
| Retry + dead-lettering (T10) | Capped exponential backoff; DLQ replay retains history |
| OpenTelemetry, Sentry, metrics (T4, T5, T11) | Trace context survives the relay hop; 8 pipeline metrics |

**Findings during delivery:**
- **Dead code removed.** The pagination refactor left `list_for_workspace` (no caller at all) and `list_for_user` (test-only caller) behind. Both deleted rather than covered with tests.
- **Coverage exclusion is narrow and justified.** Only `apps/worker/relay_main.py` (an `asyncio.run` entry point) is omitted. The *logic* inside the worker — `dispatch_event`'s retry and dead-letter policy, pool resolution — is tested directly.

### ✅ M1.2 — Authentication Boundary · closed 2026-07-28

All 7 tasks plus 3 added requirements delivered. **Demo Checklist 10/10. AC-2 passed.** [Architecture Validation Report](docs/architecture/ARCHITECTURE_VALIDATION_M1_2.md) issued: all seven confirmations hold.

| Delivered | Evidence |
|---|---|
| Next.js 15 scaffold, tooling, CI (T12) | ESLint, Prettier, tsc, Vitest, Playwright all green |
| Signing-key management (T15, done before T14 per approval) | Pair-match validation; 10 unit tests |
| Better Auth + Google/Microsoft OAuth (T13) | `auth` schema (migration 0005), password auth disabled |
| RS256 JWT issuance (T14) | **Cross-tier contract test: a real frontend-minted token verifies with the real Python verifier** |
| Typed API client (T16) | Token refresh, standard error envelope |
| Frontend shell (T17) | Sign-in, workspace create/list, sign-out |
| E2E auth journey (T18) | Playwright; skips cleanly without OAuth credentials |
| **Auth observability** (added) | 10 `AUTH_*` events across both tiers, shared vocabulary |
| **Auth health** (added) | Both tiers; key-pair match, JWT config, OAuth config, DB |

**First user-visible outcome in the project.** Design-partner onboarding is unblocked once M1.3B provides a deployed environment.

**Findings:**
- Two toolchain workarounds recorded in the validation report (ESLint flat-config bridge, `@vitejs/plugin-react` peer conflict). Neither is architectural.
- A skip condition in the contract test initially hid it — the frontend path was resolved one directory too shallow, so it silently skipped rather than running. Caught by running verbosely; a test that skips when it should run is worse than one that fails.
- **One defect found during validation and fixed:** `signora_auth` was created by migration 0005 but never connected as — the frontend defaulted to the database *owner*, which bypasses RLS on every application table and defeated the schema isolation the migration exists to create. Both tiers' permissions were individually correct; nothing asserted the relationship between them. Fixed and verified against a live database.

---

## Current Milestone

### 🔄 M1.3A — Deployment Foundation · **CURRENT** · ~4 ew

| Order | Task | Complexity | Status |
|---|---|---|---|
| 1 | T19 Production Docker images (API, worker, frontend) | M · 1.5 ew | ⬜ |
| 2 | T20 Migration runner + secrets management | M · 1.5 ew | ⬜ |
| 3 | T21 Production Compose stack + health/readiness wiring | M · 1 ew | ⬜ |

**Critical path:** T19→T20→T21 = 4 ew serial.
**Simulator required:** ❌ No.
**Checkpoint:** AC-3A Application Deployability — the stack starts from production images alone, migrations run under the migration identity, and **each tier connects under its own least-privileged role, verified from inside the running containers.**
**Demo Checklist:** 11 items — see [IMPLEMENTATION_ROADMAP.md §6](IMPLEMENTATION_ROADMAP.md#6-milestone-definitions).

The last checklist item is the one that makes the rest meaningful: the **Security Invariants suite must pass against the composed stack**, not only against a developer database. Credential separation that holds in `docker-compose.yml` and not in the images would be the M1.2 defect repeated one layer up.

<details>
<summary>M1.2 task detail (delivered)</summary>

### M1.2 — Authentication Boundary · ~11.5 ew · ✅

First milestone with a **user-visible outcome** — design-partner onboarding can begin at close.

| Order | Task | Complexity | Status |
|---|---|---|---|
| 1 | T12 Next.js 15 scaffold + tooling | M · 1.5 ew | ⬜ |
| 2 | T13 Better Auth + Google/Microsoft OAuth 🔴 | L · 3 ew | ⬜ |
| 3 | T14 RS256 JWT issuance per ADR-0026 🔴 | M · 1.5 ew | ⬜ |
| 4 | T15 Signing-key management | S–M · 1 ew | ⬜ |
| 5 | T16 Typed API client | M · 1.5 ew | ⬜ |
| 6 | T17 Frontend shell | M · 2 ew | ⬜ |
| 7 | T18 E2E auth journey | M · 1 ew | ⬜ |

**Critical path:** T12→T13→T14→T15→T18 ≈ 8 ew serial.
**Simulator required:** ❌ No.
**Checkpoint:** AC-2 Auth Boundary Integrity.
**Demo Checklist:** 10 items — see [IMPLEMENTATION_ROADMAP.md §6](IMPLEMENTATION_ROADMAP.md#6-milestone-definitions).

<details>
<summary>M1.1 task detail (delivered)</summary>

### M1.1 — Platform Runtime · ~15.5 ew · ✅

Sole active milestone. M1.2 does not begin until M1.1's **Demo Checklist passes**.

| Order | Task | Complexity | Status |
|---|---|---|---|
| 1 | T1 Coverage measurement + CI gate | XS · 0.25 ew | ⬜ |
| 2 | T2 Redis service in CI | XS · 0.25 ew | ⬜ |
| 3 | T6 Event bus schema (DLQ + idempotency ledger) | S–M · 1 ew | ⬜ |
| 4 | T3 Structured logging | M · 1.5 ew | ⬜ |
| 5 | T7 Outbox relay 🔴 | L · 3 ew | ⬜ |
| 6 | T8 Dispatch + platform-owned idempotency 🔴 | L · 3 ew | ⬜ |
| 7 | T9 ARQ worker fleet + per-stage pools | M · 1.5 ew | ⬜ |
| 8 | T10 Retry + dead-lettering | M · 1.5 ew | ⬜ |
| 9 | T4 OpenTelemetry tracing | M · 2 ew | ⬜ |
| 10 | T5 Sentry error tracking | S · 0.5 ew | ⬜ |
| 11 | T11 Pipeline observability metrics | S–M · 1 ew | ⬜ |

**Sequencing rationale:** cheap unblocking work first (T1, T2, T6); logging (T3) *before* the relay so the relay is debuggable as it is built rather than after; then the critical chain T7→T8→T9→T10; then remaining observability, which benefits from having real cross-process traffic to instrument.

**Critical path:** T6→T7→T8→T9→T10 ≈ **10 ew of serial work** — not compressible by adding engineers.

**Simulator required:** ❌ No — verified with a test-only consumer. The simulator enters at the Provider layer, which does not exist yet.

**Checkpoint:** AC-1 Event Bus Contract.

**Demo Checklist:** 13/13 passed, encoded as executable assertions in `tests/integration/test_m1_1_demo_checklist.py` — a checklist that is only ever read is a checklist that eventually lies.

</details>

---

## Queued Milestones

Sequential execution — each begins only when the previous milestone's Demo Checklist passes.

| Order | Milestone | Effort | Simulator | Gate |
|---|---|---|---|---|
| 1 | **M1.3B** Cloud Infrastructure | ~6 ew | ❌ | AC-3B · rollback executed and timed |
| 2 | **M1.4** Platform Smoke Test | ~1.5 ew | ❌ | AC-3C · every stage proven to fail when broken |
| 3 | **M2.0** Provider Simulation Framework | ~17–24 ew | ✅ builds it | AC-4 · identical adapter contract, config-only switching |
| 4 | M2.1 → M15 | ~175–240 ew | mostly ✅ | Per roadmap |

### Why M1.3 was split

M1.3A proves the **application** is deployable; M1.3B proves **AWS** is configured. Run together, a failure gives no signal about which one is wrong — and every application-level fault (a container that will not start, a migration runner racing two replicas, a readiness probe green before the database is reachable) costs minutes locally and an afternoon inside ECS.

### Why M1.4 exists

Verification is currently spread across a backend suite, a frontend suite, a cross-tier contract test, and a checklist a human reads. Each is individually green while the *composition* goes unverified — which is exactly where the M1.2 credential defect lived. One command turns "everything passes" into a claim about the system rather than about its parts.

### M2.0 — why it precedes every pipeline module

A permanent platform capability, not throwaway tooling — used for local development, integration testing, E2E testing, demos, AI evaluation, regression testing, performance benchmarking, and customer onboarding demos.

**It also builds the Provider Port**, as its first concrete implementation. That satisfies the YAGNI ruling and validates the port with working code before any vendor adapter is written or contract signed.

**Binding rule:** simulated providers implement *exactly* the same adapter contract as production providers. Switching is configuration only; no `if simulated:` branching may exist in any layer; the ingestion pipeline is byte-identical in both modes.

**Highest-risk control:** the simulator must never activate in production — it would fabricate customer intelligence. Guarded by an environment check, unambiguous ingestion logging, health-endpoint visibility, and an alert, all test-enforced.

---

## Current Sprint

**Sprint:** M1.3A Sprint 1 — awaiting approval.

**Scope — M1.3A only.** Single stream; no concurrent milestone work.

| Sprint 1 tasks | Rationale |
|---|---|
| T19 Production Docker images | Zero dependencies; everything else in M1.3A builds on it |
| T20 Migration runner + secrets | Where the migration/runtime credential split becomes executable rather than documentary |

**Note on T20.** The migration runner is the first place the new credential rule is enforced by machinery rather than by convention: migrations run as a discrete step under the migration identity, and no running service holds a credential that could apply one. The Security Invariants suite already asserts the runtime role cannot migrate — T20 makes that arrangement the only way the system starts.

---

## Blocked Items

| Item | Blocked by | Severity | Owner |
|---|---|---|---|
| ~~All 13 core intelligence modules~~ | ~~T7/T8 — event bus relay + dispatch~~ | ✅ **CLEARED** | M1.1 |
| ~~Any human access / any demo~~ | ~~T13/T14 — Better Auth issuer~~ | ✅ **CLEARED** | M1.2 |
| Any deployed environment | T22/T23 — Terraform + ECS (M1.3B) | 🟠 High | Unassigned |
| Reproducible local production stack | T19–T21 (M1.3A) | 🟠 High | Unassigned |
| Offline development, deterministic demos, AI eval datasets | M2.0 — simulation framework | 🟠 High | Unassigned |
| Provider Platform (M2.1) | M2.0 — Provider Port defined there | 🟠 High | Unassigned |
| Both AI engines | M8 — AI Provider Port + Prompt Registry | 🟡 Medium | Unassigned |
| Trustworthy AI output | M8 — Evaluation Harness (R-10) | 🟠 High | Unassigned |
| PII/retention implementation | **Legal/Compliance policy input** (R-04, R-05) | 🟡 Medium | **Escalated — not an engineering blocker** |

**One of the two dominant blockers is now cleared.** The event bus relay shipped in M1.1, unblocking all 13 pipeline modules. The remaining blocker is the Better Auth issuer: **there is still no working login**, so design-partner onboarding cannot begin until M1.2 closes.

**Staffing remains the meta-blocker** — every item above is unassigned, and headcount is the single largest determinant of the GA date (see Calendar above).

---

## Architecture Risks

Full register: [16-architecture-risks.md](docs/architecture/16-architecture-risks.md). **12 open, 1 resolved.**

| ID | Risk | Sev | Status | Addressed by |
|---|---|---|---|---|
| R-01 | AI vendor cost exposure without budget governance | 🔴 High | Open | M15 (earlier if AI Research enabled sooner) |
| R-04 | PII classification / retention / lifecycle undefined | 🔴 High | **Escalated to Legal** | M15 — start policy work now, long lead time |
| R-05 | AI prompt data-classification policy undefined | 🔴 High | **Escalated to Legal** | M15 |
| R-10 | No AI evaluation methodology | 🔴 High | Open — **partially de-risked by M2.0** | M8 |
| R-02 | Single-region vs. enterprise data residency | 🟠 Med | Open | Audit now, build later |
| R-03 | RLS query performance not load-tested at scale | 🟠 Med | Open | M15, using simulator-generated volume |
| R-06 | Cross-workspace admin/support access undefined | 🟠 Med | Open | Before support tooling |
| R-08 | Meilisearch/pgvector not validated at scale | 🟠 Med | Open | M15 |
| R-12 | SOC 2 / enterprise compliance gap | 🟠 Med | Open | M15, parallel with enterprise GTM |
| R-11 | Vendor concentration on younger projects | 🟡 Low-Med | Accepted, monitored | Quarterly review |
| R-07 | API/pipeline latency SLOs undefined | 🟡 Low | Open | Set from telemetry post-M1.1 |
| R-09 | AI Research Engine timeout undefined | 🟡 Low | Open | M10, from telemetry |
| R-13 | Better Auth is TypeScript-native | — | ✅ Resolved | [ADR-0026](docs/architecture/adr/0026-jwt-boundary-architecture.md) |

### New risk introduced by this revision

| ID | Risk | Sev | Mitigation |
|---|---|---|---|
| **R-14** | **Simulator activating in a production environment** would fabricate customer intelligence — a trust failure, not merely a bug | 🔴 High | Environment guard refusing activation in production absent an explicit logged override · ingestion logs mark simulated payloads unambiguously · simulator state in health output · alert on unexpected activation · **all four test-enforced**. To be added to the register during M2.0. |

**Most urgent by lead time, not severity:** R-04 and R-05. They need Legal/Compliance input engineering cannot supply, and formal policy work has a long tail. Starting them at M15 would be starting them late.

---

## Technical Debt

Small and deliberate. Nothing below is discovered debt.

| Item | Impact | Rationale | Repay by |
|---|---|---|---|
| ~~Test coverage unmeasured~~ | — | — | ✅ **Repaid in M1.1** — 95.01%, CI-gated |
| ~~Event bus relay unimplemented~~ | — | — | ✅ **Repaid in M1.1** |
| ~~`apps/worker` empty stub~~ | — | — | ✅ **Repaid in M1.1** — 7 pools |
| ~~No structured logging~~ | — | — | ✅ **Repaid in M1.1** |
| ~~No CI Redis service~~ | — | — | ✅ **Repaid in M1.1** |
| JWT key rotation requires a deploy | Medium | JWKS adds a cache, fetch path, and failure mode not yet justified | Post-GA |
| Token revocation not immediate (15-min TTL) | Medium | Standard JWT tradeoff; `sid`/`jti` carried so a revocation list needs no contract change | Post-GA if the window proves unacceptable |
| Casbin policy is coarse RBAC | Low | Correct for current needs | When enterprise custom roles are required |
| No API versioning scheme | Low | Deliberate — speculative with one first-party client | First breaking change |

| Relay `LISTEN/NOTIFY` wake-up not yet wired to the loop | Low | `notify_outbox` exists and polling is the correctness guarantee; the notification only collapses idle latency from ~1s | M1.3A or when latency matters |
| **`@vitejs/plugin-react` removed from frontend devDependencies** | Low | Its Vite version conflicts with `better-auth`'s optional Svelte peer dependencies. M1.2's tests target JWT and key-management logic, which is plain TypeScript and needs no React transform. Keeping the dependency would have meant `--legacy-peer-deps` across the whole install to satisfy a plugin nothing used. | **Scheduled: the first milestone introducing frontend component testing.** React component tests cannot run without it — reinstating it is a prerequisite of that work, not a follow-up to it. Resolve the peer conflict then, when there is a real consumer to validate against. |

**Debt ratio: healthy.** Five of the nine v3 items were repaid in M1.1. Two low-severity items now open, both with named repayment points.

**Scheduling rule.** Every item above carries a *repayment milestone*, not "later". Debt without a scheduled milestone is indistinguishable from a decision nobody revisits — the `@vitejs/plugin-react` entry exists precisely so its absence is discovered when component tests are planned rather than when they fail to run.

---

## Known Bugs

**None open.**

Three defects found and fixed during M0 and one during M1.2 validation, each with regression tests proven to fail against the pre-fix state.

### Open architectural question — raised, awaiting decision

**Platform tables are readable across every workspace.** `outbox_event` and `dead_letter_event` carry a `workspace_id` but have no RLS, and `signora_app` holds `SELECT` on both. Application code issuing an unfiltered query against either sees every workspace's event payloads.

The *absence of RLS* is deliberate — the relay must sweep all workspaces in one pass, which tenant-scoped RLS would prevent by construction. That rationale was recorded in `tests/conftest.py` but not in `11-tenancy.md`, whose stated exception list names only Business Event Engine's taxonomy. The documentation drift is now fixed.

What remains open is narrower: **the relay uses the privileged connection, and the publisher only ever inserts** — so `signora_app` appears to need `INSERT` but not `SELECT`. Revoking `SELECT` would close the cross-tenant read path without affecting the relay. That is a change to the tenancy model's grant surface, so it is raised rather than applied.

Encoded as a tracked deviation in `test_authorization.py::test_every_workspace_owned_table_has_rls_enabled_and_forced`: the two tables are named explicitly, and any *other* table reaching that list fails the build.

**Caveat worth restating:** "no known bugs" across ~2,660 LOC with one module and zero production traffic is a weak signal, not a quality claim.

---

## Test Coverage

| Metric | Value |
|---|---|
| Total tests | **198 passing**, 0 failing, 0 skipped |
| Unit tests | 129 |
| Integration tests | 69 (real PostgreSQL 17 + real Redis) |
| **Line coverage** | ✅ **95.01%**, CI-gated at 95% |
| Type coverage | ✅ mypy `strict`, 97 files, zero errors |
| Boundary enforcement | ✅ 3 import-linter contracts, verified to fail on deliberate violation |
| Migration reversibility | ✅ Verified across all 4 revisions |

**Test quality signals:** the `alg:none` and algorithm-confusion tests initially passed for the wrong reason (PyJWT refuses to mint those tokens) and were rewritten with hand-forged tokens. RLS regression tests were verified to fail against pre-fix policies before being trusted.

**M1.1 addition:** the Demo Checklist is itself a test file (`tests/integration/test_m1_1_demo_checklist.py`) — 11 tests covering all 13 items, run against real PostgreSQL and Redis. Milestone completion is verified by CI rather than by someone ticking boxes.

**Coming in M2.0:** the scenario library becomes a growing end-to-end regression suite, with each milestone extending its assertions.

---

## Documentation Status

| Document | Status |
|---|---|
| Architecture (19 docs) | ✅ Complete, ratified, consistent |
| ADRs (27) | ✅ Complete |
| [CLAUDE.md](CLAUDE.md) | ✅ Complete |
| [PRODUCT_DIFFERENTIATORS.md](PRODUCT_DIFFERENTIATORS.md) | ✅ Complete |
| [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) | ✅ **Updated to v3** |
| [PRODUCT_ROADMAP.md](PRODUCT_ROADMAP.md) | ✅ Valid — milestone numbers M2+ unchanged |
| [AI_MATURITY_ROADMAP.md](AI_MATURITY_ROADMAP.md) | ✅ Valid — levels unchanged |
| PROJECT_STATUS.md | ✅ **This document, v3** |
| API reference | ✅ Generated (OpenAPI) |
| `20-provider-simulation.md` + ADR | ⬜ **To be authored during M2.0** |
| Operations runbook | ⬜ **Required by M1.3A** (stack lifecycle), extended in M1.3B (deploy, rollback, restore) |
| Onboarding guide | ⬜ Needed when team exceeds ~3 |

**Documentation drift: zero.** All internal links resolve. Docs have been updated in the same commit as the code they describe, every time.

**Deliberate numbering choice:** M1 was split and M2.0 inserted *without renumbering M2+*, so PRODUCT_ROADMAP.md and AI_MATURITY_ROADMAP.md remain valid without edits. The mapping table is in [IMPLEMENTATION_ROADMAP.md §4](IMPLEMENTATION_ROADMAP.md#4-milestone-structure).

---

## Next Task

### 🎯 M1.3A · T19 — Production Docker images

**Why first:** zero dependencies, and both remaining M1.3A tasks build on it.

**Then:** T20 (migration runner + secrets) → T21 (production Compose stack) → M1.4 · T24 (platform smoke test) → M1.3B · T22 → T23.

**Note the ordering.** T24 depends on M1.3A, not M1.3B — the smoke command runs against the local production stack, so it becomes a release gate *before* anything reaches AWS rather than after.

**Awaiting:** approval to begin M1.3A, and staffing. Every task remains unassigned.

---

## Change Log

| Date | Change |
|---|---|
| 2026-07-28 | v6 — **M1.2 approved.** Security Invariants suite established: 47 permanent invariants across authentication, authorization, database, and platform, each proven to fail when its guarantee is deliberately removed; wired into CI as a separately-reported job. Migration/runtime credential separation adopted as a permanent engineering rule (CLAUDE.md §8). M1.3 split into M1.3A Deployment Foundation and M1.3B Cloud Infrastructure; M1.4 Platform Smoke Test added; AC-3 split into AC-3A/3B/3C and AC-13 added. `@vitejs/plugin-react` recorded as scheduled technical debt. One architectural question raised for decision: platform-table read scope. |
| 2026-07-28 | v5 — **M1.2 Authentication Boundary complete.** 7 tasks plus 3 added requirements; 242 backend and 29 frontend tests; Demo Checklist 10/10; AC-2 passed; Architecture Validation Report issued. One defect found during validation: `signora_auth` created but never connected as, with the frontend defaulting to the database owner. |
| 2026-07-28 | v4 — **M1.1 Platform Runtime complete.** 11 tasks, 82 new tests (198 total), coverage 95.01% CI-gated, Demo Checklist 13/13, AC-1 passed. Dead code from the pagination refactor removed. 06-events.md updated to v3. |
| 2026-07-28 | v3 — sequential single-stream execution adopted; calendar restated by team size; Demo Checklist added as a completion gate; progressive AI regression assertion model defined; simulator identical-adapter-contract rule recorded |
| 2026-07-28 | v2 — M1 split into M1.1/M1.2/M1.3; M2.0 Provider Simulation Framework added; per-milestone Demo Scenario, User-Visible Outcome, DoD, Rollback, Operational Readiness introduced; R-14 identified; estimate revised to 225–305 ew |
| 2026-07-28 | v1 — Initialized. M0 closed. Roadmap documents created. |

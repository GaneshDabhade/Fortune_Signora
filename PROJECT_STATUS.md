# PROJECT_STATUS.md

> **Owner:** Technical Program Manager · **Audience:** Everyone
> **Cadence:** Updated at every milestone boundary and every sprint close. Updating this is part of the [Definition of Done](IMPLEMENTATION_ROADMAP.md#12-definition-of-done-global).
> **Last updated:** 2026-07-28 · **Reporting period:** M0 close → M1 planning
> **Revision:** v2 — milestone structure revised (M1 split into M1.1/M1.2/M1.3; M2.0 Provider Simulation Framework added)

---

## Overall Progress

```
M0  Foundation             ████████████████████ 100%  ✅ Complete
M1.1 Platform Runtime      ░░░░░░░░░░░░░░░░░░░░   0%  🔴 Approved, not started
M1.2 Auth Boundary         ░░░░░░░░░░░░░░░░░░░░   0%  🔴 Approved, not started
M1.3 Infrastructure        ░░░░░░░░░░░░░░░░░░░░   0%  🟠 Approved, not started
M2.0 Simulation Framework  ░░░░░░░░░░░░░░░░░░░░   0%  🆕 Approved, not started
M2.1 → M15                 ░░░░░░░░░░░░░░░░░░░░   0%
```

| Dimension | Status |
|---|---|
| **Overall completion to GA** | **~5%** by engineering effort (~14 of ~239–319 total engineer-weeks) |
| Architecture & design | **100%** — 19 documents, 27 ADRs, ratified and internally consistent |
| Core modules | **1 of 14** (7%) |
| Backend platform | ~55% of foundation scope; 0% of pipeline scope |
| Frontend | **0%** — not started |
| Infrastructure-as-code | **0%** — local Docker Compose only |
| Provider simulation | **0%** — newly scoped (M2.0) |
| AI capability | **Level 0 of 12** ([AI_MATURITY_ROADMAP.md](AI_MATURITY_ROADMAP.md)) |

**Estimate revised upward.** v1 projected 190–266 ew to GA; v2 projects **225–305 ew (~11–16 months** at 6 engineers / 80% capacity). The increase is the Provider Simulation Framework (~17–24 ew), a deliberate investment that is partially repaid — M8's AI evaluation harness inherits its datasets and drops from 6–8 ew to ~4–6 ew.

**Honest read:** progress percentage will look flat through M1 and M2.0 and then accelerate. That is a property of building a runtime spine and a test substrate before features, not a sign of slow execution.

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

---

## Current Milestone

### 🔄 M1 — Runtime Spine · **APPROVED, NOT STARTED**

Now three parallel milestones. All approved 2026-07-28.

#### M1.1 — Platform Runtime · ~15.5 ew

| Task | Complexity | Status |
|---|---|---|
| T1 Coverage measurement + CI gate | XS · 0.25 ew | ⬜ |
| T2 Redis service in CI | XS · 0.25 ew | ⬜ |
| T3 Structured logging | M · 1.5 ew | ⬜ |
| T4 OpenTelemetry tracing | M · 2 ew | ⬜ |
| T5 Sentry error tracking | S · 0.5 ew | ⬜ |
| T6 Event bus schema (DLQ + idempotency ledger) | S–M · 1 ew | ⬜ |
| T7 Outbox relay 🔴 | L · 3 ew | ⬜ |
| T8 Dispatch + platform-owned idempotency 🔴 | L · 3 ew | ⬜ |
| T9 ARQ worker fleet + per-stage pools | M · 1.5 ew | ⬜ |
| T10 Retry + dead-lettering | M · 1.5 ew | ⬜ |
| T11 Pipeline observability metrics | S–M · 1 ew | ⬜ |

**Simulator required:** ❌ No — verified with a test-only consumer.
**Checkpoint:** AC-1 Event Bus Contract.

#### M1.2 — Authentication Boundary · ~11.5 ew

| Task | Complexity | Status |
|---|---|---|
| T12 Next.js 15 scaffold + tooling | M · 1.5 ew | ⬜ |
| T13 Better Auth + Google/Microsoft OAuth 🔴 | L · 3 ew | ⬜ |
| T14 RS256 JWT issuance per ADR-0026 🔴 | M · 1.5 ew | ⬜ |
| T15 Signing-key management | S–M · 1 ew | ⬜ |
| T16 Typed API client | M · 1.5 ew | ⬜ |
| T17 Frontend shell | M · 2 ew | ⬜ |
| T18 E2E auth journey | M · 1 ew | ⬜ |

**Simulator required:** ❌ No.
**Checkpoint:** AC-2 Auth Boundary Integrity.
**Note:** first milestone with **user-visible outcome** — design-partner onboarding can begin at close.

#### M1.3 — Infrastructure · ~6 ew

| Task | Complexity | Status |
|---|---|---|
| T19 Terraform baseline | L · 3 ew | ⬜ |
| T20 ECS + deploy pipeline + rollback validation | L · 3 ew | ⬜ |

**Simulator required:** ❌ No.
**Checkpoint:** AC-3 Deployment & Rollback.

---

## Next Milestone After M1

### 🆕 M2.0 — Provider Simulation Framework · ~17–24 ew · **APPROVED**

A permanent platform capability, not throwaway tooling. Enters the system at the Provider layer only; produces payloads byte-identical in shape to real vendor responses; runs the standard pipeline untouched.

**Also builds the Provider Port** — as its first concrete implementation. This satisfies the YAGNI ruling (no speculative ports) *and* validates the port with working code before any vendor adapter is written.

**Checkpoint:** AC-4 Simulator Fidelity.

**Highest-risk control in the milestone:** the simulator must never activate in production. A simulator silently running against customer workspaces would fabricate intelligence — treated as a P0-class hazard, guarded by an environment check, unambiguous ingestion logging, health-endpoint visibility, and an alert, all test-enforced.

---

## Current Sprint

**Sprint:** Not yet started. M1 Sprint 1 pending kickoff and staffing.

**Sprint 1 scope** — all three M1 milestones start simultaneously; they contend for nothing.

| Stream | Sprint 1 tasks | Rationale |
|---|---|---|
| **D — Platform** | T1, T2, T6, then T3 and T7 | Zero-dependency items first; then instrument before complexity arrives; then start the critical path |
| **C — Frontend** | T12, then T13 | Different codebase — fully parallel, no contention |
| **E — Infra** | T19 | Zero dependencies |
| **A — Pipeline** | Knowledge Graph spike (timeboxed, 2 weeks) | Retire the roadmap's largest estimation risk while re-planning is still cheap |

**Explicitly not in Sprint 1:** any pipeline module (blocked on T7/T8), and any provider adapter (blocked on M2.0).

---

## Blocked Items

| Item | Blocked by | Severity | Owner |
|---|---|---|---|
| All 13 core intelligence modules | T7/T8 — event bus relay + dispatch | 🔴 Critical | Unassigned |
| Any human access / any demo | T13/T14 — Better Auth issuer | 🔴 Critical | Unassigned |
| Any deployed environment | T19/T20 — Terraform + ECS | 🟠 High | Unassigned |
| Offline development, deterministic demos, AI eval datasets | M2.0 — simulation framework | 🟠 High | Unassigned |
| Provider Platform (M2.1) | M2.0 — Provider Port defined there | 🟠 High | Unassigned |
| Both AI engines | M8 — AI Provider Port + Prompt Registry | 🟡 Medium | Unassigned |
| Trustworthy AI output | M8 — Evaluation Harness (R-10) | 🟠 High | Unassigned |
| PII/retention implementation | **Legal/Compliance policy input** (R-04, R-05) | 🟡 Medium | **Escalated — not an engineering blocker** |

**Two blockers dominate**, and they sit in different codebases so they can be worked simultaneously: the event bus relay and the Better Auth issuer.

**Staffing remains the meta-blocker** — every item above is unassigned.

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
| Test coverage unmeasured (`pytest-cov` absent) | Medium | Oversight, not a decision | **M1.1 / T1** |
| Event bus relay unimplemented | 🔴 Critical | Deliberate: dispatch with zero consumers is untestable | **M1.1 / T7–T8** |
| `apps/worker` is an empty stub | High | Same deferral | **M1.1 / T9** |
| No structured logging | Medium | Deferred with observability | **M1.1 / T3** |
| No CI Redis service | Medium | Not needed until relay tests exist | **M1.1 / T2** |
| JWT key rotation requires a deploy | Medium | JWKS adds a cache, fetch path, and failure mode not yet justified | Post-GA |
| Token revocation not immediate (15-min TTL) | Medium | Standard JWT tradeoff; `sid`/`jti` carried so a revocation list needs no contract change | Post-GA if the window proves unacceptable |
| Casbin policy is coarse RBAC | Low | Correct for current needs | When enterprise custom roles are required |
| No API versioning scheme | Low | Deliberate — speculative with one first-party client | First breaking change |

**Debt ratio: healthy.** Six of nine items are scheduled for repayment in the next milestone.

---

## Known Bugs

**None open.**

Three defects found and fixed during M0, each with regression tests proven to fail against the pre-fix state.

**Caveat worth restating:** "no known bugs" across ~2,660 LOC with one module and zero production traffic is a weak signal, not a quality claim.

---

## Test Coverage

| Metric | Value |
|---|---|
| Total tests | **116 passing**, 0 failing, 0 skipped |
| Unit tests | 79 |
| Integration tests | 37 (real PostgreSQL 17 as least-privilege role) |
| Test LOC | ~2,058 (~77% of production LOC) |
| **Line coverage** | ⚠️ **Not measured** — resolved by T1 |
| Type coverage | ✅ mypy `strict`, 71 files, zero errors |
| Boundary enforcement | ✅ 3 import-linter contracts, verified to fail on deliberate violation |
| Migration reversibility | ✅ Verified across all 4 revisions |

**Test quality signals:** the `alg:none` and algorithm-confusion tests initially passed for the wrong reason (PyJWT refuses to mint those tokens) and were rewritten with hand-forged tokens. RLS regression tests were verified to fail against pre-fix policies before being trusted.

**Coming in M2.0:** the scenario library becomes a growing end-to-end regression suite, with each milestone extending its assertions.

---

## Documentation Status

| Document | Status |
|---|---|
| Architecture (19 docs) | ✅ Complete, ratified, consistent |
| ADRs (27) | ✅ Complete |
| [CLAUDE.md](CLAUDE.md) | ✅ Complete |
| [PRODUCT_DIFFERENTIATORS.md](PRODUCT_DIFFERENTIATORS.md) | ✅ Complete |
| [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) | ✅ **Updated to v2** |
| [PRODUCT_ROADMAP.md](PRODUCT_ROADMAP.md) | ✅ Valid — milestone numbers M2+ unchanged |
| [AI_MATURITY_ROADMAP.md](AI_MATURITY_ROADMAP.md) | ✅ Valid — levels unchanged |
| PROJECT_STATUS.md | ✅ **This document, v2** |
| API reference | ✅ Generated (OpenAPI) |
| `20-provider-simulation.md` + ADR | ⬜ **To be authored during M2.0** |
| Operations runbook | ⬜ **Required by M1.3** (first deployed environment) |
| Onboarding guide | ⬜ Needed when team exceeds ~3 |

**Documentation drift: zero.** All internal links resolve. Docs have been updated in the same commit as the code they describe, every time.

**Deliberate numbering choice:** M1 was split and M2.0 inserted *without renumbering M2+*, so PRODUCT_ROADMAP.md and AI_MATURITY_ROADMAP.md remain valid without edits. The mapping table is in [IMPLEMENTATION_ROADMAP.md §4](IMPLEMENTATION_ROADMAP.md#4-milestone-structure).

---

## Next Task

### 🎯 M1 Sprint 1 — three streams start simultaneously

**Stream D — Platform (highest leverage):** T1 (coverage), T2 (CI Redis), T6 (event bus schema) — all zero-dependency, same-day starts. Then T3 (logging) and T7 (relay).

**Why T7 leads the critical path:** it unblocks all 13 core intelligence modules. No other available task has comparable leverage.

**Stream C — Frontend:** T12 (Next.js scaffold) then T13 (Better Auth). Different codebase; zero contention with Stream D. Until this lands, **nobody can log in** and no demo is possible.

**Stream E — Infra:** T19 (Terraform baseline), zero dependencies.

**Stream A — De-risking:** timeboxed 2-week Knowledge Graph spike. Retires the roadmap's largest estimation variance while re-planning is still cheap.

**Awaiting:** staffing assignment. Every task is currently unassigned, which is the practical blocker ahead of all technical ones.

---

## Change Log

| Date | Change |
|---|---|
| 2026-07-28 | v2 — M1 split into M1.1/M1.2/M1.3; M2.0 Provider Simulation Framework added; per-milestone Demo Scenario, User-Visible Outcome, DoD, Rollback, Operational Readiness introduced; R-14 identified; estimate revised to 225–305 ew |
| 2026-07-28 | v1 — Initialized. M0 closed. Roadmap documents created. |

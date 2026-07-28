# PROJECT_STATUS.md

> **Owner:** Technical Program Manager · **Audience:** Everyone
> **Cadence:** Updated at every milestone boundary and every sprint close. Updating this is part of the [Definition of Done](IMPLEMENTATION_ROADMAP.md#12-definition-of-done-global).
> **Last updated:** 2026-07-28 · **Reporting period:** M1.2 delivery
> **Revision:** v12 — **M1.5 approved; both foundations frozen.** Simulation Architecture Review issued for M2.0 approval. **Revision v11 —** M1.5 Frontend Foundation complete. Design system, shared component library, application shell, query layer, session and workspace management, permission-aware routing, feedback primitives, and component testing in CI. **`@vitejs/plugin-react` debt repaid** — `--legacy-peer-deps` removed everywhere. The frontend foundation is now a contract (CLAUDE.md §20c)

---

## Overall Progress

```
M0  Foundation             ████████████████████ 100%  ✅ Complete
M1.1 Platform Runtime      ████████████████████ 100%  ✅ Complete
M1.2 Auth Boundary         ████████████████████ 100%  ✅ Complete
M1.3A Deployment Foundation ███████████████████ 100%  ✅ Complete · platform FROZEN
M1.4 Platform Smoke Test    ███████████████████ 100%  ✅ Complete · FOUNDATION CLOSED
M1.5 Frontend Foundation    ███████████████████ 100%  ✅ Complete · FE FOUNDATION CONTRACT
M2.0 Simulation Framework   ░░░░░░░░░░░░░░░░░░░   0%  🔴 CURRENT — next
M2.1 → M14b Pipeline        ░░░░░░░░░░░░░░░░░░░   0%  ⏸ Queued (§5b execution order)
M14.5 Cloud Infrastructure  ░░░░░░░░░░░░░░░░░░░   0%  ⏸ Deferred to Production Readiness
M15 GA Readiness            ░░░░░░░░░░░░░░░░░░░   0%  ⏸ Queued
M2.1 → M15                 ░░░░░░░░░░░░░░░░░░░░   0%  ⏸ Queued
```

**Execution model: sequential single stream.** One milestone at a time, in the order above. Parallel workstreams are documented in [IMPLEMENTATION_ROADMAP.md §9](IMPLEMENTATION_ROADMAP.md#9-parallel-workstreams--retained-for-future-scaling) for future scaling but are **not** the current operating assumption.

| Dimension | Status |
|---|---|
| **Overall completion to GA** | **~19%** by engineering effort (~63.5 of ~262–340 total engineer-weeks; **~199–277 ew remaining**) |
| Architecture & design | **100%** — 19 documents, 27 ADRs, ratified and internally consistent |
| Core modules | **1 of 14** (7%) |
| Backend platform | **100% of foundation scope** — 🔒 frozen from M1.3A; 0% of pipeline scope |
| Frontend | **~45%** — platform complete (design system, components, shell, routing, query layer); business screens are M12 |
| Infrastructure-as-code | **~35%** — local production stack complete and continuously verified; cloud IaC deferred to M14.5 |
| Provider simulation | **0%** — newly scoped (M2.0) |
| AI capability | **Level 0 of 12** ([AI_MATURITY_ROADMAP.md](AI_MATURITY_ROADMAP.md)) |

---

## Platform Contracts

Ratified 2026-07-28. These are **foundation capabilities, not work in progress** — the substrate every later milestone is built on.

| Contract | Established | What it guarantees |
|---|---|---|
| Platform Runtime | M1.1 | Outbox relay, dispatch, platform-owned idempotency, retry, dead-lettering, worker pools |
| Authentication Boundary | M1.2 | Better Auth issues, FastAPI only verifies; the API cannot mint a token it accepts (ADR-0026) |
| Deployment Foundation | M1.3A | Production images, per-tier identities, concurrency-safe migration runner, restart-safe stack |
| Platform Smoke Test | M1.4 | One command verifies the whole platform; required before every milestone and release |
| Security Invariants | M1.2–M1.4 | 59 permanent architectural guarantees, each proven to fail when its guarantee is removed |
| Tenant Isolation Policy | M1.3A | Every table classified; tenant tables carry forced RLS, required policies, and a non-null identifier |
| Platform Infrastructure Policy | M1.3A | Infrastructure tables owned by platform services; the application publishes and cannot read |
| Platform Freeze | M1.3A | `signora_platform/` changes only for a security fix, production defect, or approved change |
| **Frontend Foundation** | **M1.5** | 🔒 Frozen. Design system, components, shell, query layer, auth integration, and routing are consumed, not modified — except for a production defect, **accessibility issue**, security issue, or approved change (CLAUDE.md §20c) |

**One change since the freeze:** the relay's transient-failure handling (M1.4), under the production-defect exemption.

---

## Platform Health Metrics

Permanent indicators, reported every milestone. Each is machine-checked — none is a judgement call — so a number moving is evidence rather than opinion.

### Architecture Stability

How much the agreed architecture is churning. Sustained instability means the design is being discovered during implementation rather than before it.

| Indicator | Current | Target |
|---|---|---|
| ADRs superseded or reversed since ratification | **0 of 27** | 0 — reversal means the decision was made too early |
| Documents amended for *drift* (code disagreed with docs) | **3** (11-tenancy ×2, 18-authentication) | Trending to 0 |
| Dependency inversions caught before implementation | **5** (3 in v9, 2 more in v10) | All — an inversion caught in planning costs a paragraph; caught in code it costs a milestone |
| Roadmap status | 🔒 **Frozen** — changes are sequencing, dependency correction, or RFC (§5c) | Category 3 requires approval |
| Documents amended for *new decisions* | 3 | Healthy — this is the process working |
| Unplanned architectural changes mid-milestone | **0** | 0 — these belong to the RFC process |
| `signora_platform/` freeze status | 🔒 **Frozen** since M1.3A · **1 change**, under the production-defect exemption | Changes require security fix, production defect, or approval |
| Infrastructure Contract | ✅ **10 of 10** requirements satisfied | All, continuously — verified by `make smoke` |

**Reading:** stable. No ratified decision has been reversed. Both drift amendments were found by writing tests that asserted the documented behaviour, not by a production incident.

### Foundation Health

Whether the substrate the 13 pipeline modules will be built on is sound.

| Indicator | Current | Target |
|---|---|---|
| Backend tests | **313 passing**, 0 skipped, 0 xfail | 0 skipped — a skipped test is an untested claim |
| Coverage | **95.63%** (CI gate 95%) | ≥95% |
| mypy strict | Clean, 113 files | Clean |
| Migrations reversible | **7 of 7** revisions | 100% |
| Disaster recovery validated | **4 of 4** components restart-safe | All |
| Platform smoke stages | **16**, all proven to fail when broken | Every stage verified |
| Whole-stack verification | **`make smoke`**, ~46s, in CI | One command, every merge |
| Platform modules with a failure-path test | 12 of 12 | 100% |
| Open production defects | **0** | 0 |
| Defects found by tests vs. by use | **8 of 13 by tests**; 5 by running the stack | Falling ratio is expected and is why `make smoke` now exists |

**Reading:** sound. The metric worth watching is the last one: every defect so far was found by a test written to look for it, four of them by deliberately breaking a guarantee to check the test bites.

### Security Invariant Status

The permanent architectural guarantees. A drop here is never a test problem.

| Category | Invariants | Status |
|---|---|---|
| Authentication | 15 | ✅ All passing |
| Authorization | 11 | ✅ All passing |
| Tenant Isolation Policy | 12 | ✅ All passing |
| Database privilege separation | 9 | ✅ All passing |
| Platform durability | 12 | ✅ All passing |
| **Total** | **59** | ✅ **59 / 59**, also green against the running production stack |

| Indicator | Current | Target |
|---|---|---|
| Invariants proven to fail when their guarantee is removed | **59 of 59** | 100% — an unverified invariant may assert nothing |
| Invariants verified against a deployed stack | **59** (M1.3A local production) | Every milestone from M1.3A |
| Frontend guard tests (AC-14 / AC-15) | **13**, all proven to fail when violated | Every design-system change |
| Invariants weakened or removed to make a change pass | **0** | 0, permanently |
| Milestones adding invariants | 2 of 2 since introduction | Every milestone (AC-13) |
| Tables unclassified under the Tenant Isolation Policy | **0** | 0 — build fails otherwise |

**Reading:** healthy, with one caveat worth keeping visible. Writing this suite surfaced two of my own tests asserting nothing — a backoff cap compared against itself, and a marker hook that silently marked the whole suite. Both were caught only by deliberately breaking the guarantee. **The "proven to fail" column is the one that matters; the count alone would have looked identical while two tests were inert.**

### Cross-Module Boundary Violations

Whether the modular monolith is staying modular. These are the violations that are cheap now and structural later.

| Indicator | Current | Target |
|---|---|---|
| import-linter contracts | **3 kept, 0 broken** | 0 broken |
| Contracts proven to fail on a deliberate violation | 3 of 3 | 100% |
| Cross-module imports bypassing `public/` | **0** | 0 |
| Direct cross-module database access | **0** | 0 |
| Modules reading platform infrastructure tables | **0** (enforced by grant, not convention) | 0 |
| Synchronous cross-module calls | **0** — all inter-module communication is events | Exceptions require approval |

**Reading:** clean, but the sample is small — one module cannot violate a boundary with itself. This metric only becomes meaningful from M2.1, when a second module exists. The contracts are in place *before* they can be broken, which is the point.

---

### On the completion percentage

It has moved from ~19% (v8) to ~16% without a single engineer-week of work being lost or repeated. Three causes, all bookkeeping:

- **M1.5 makes explicit** ~14.5 ew of frontend platform work that was previously buried inside M12's estimate. M12 correspondingly drops from 28–40 to 24–35 ew.
- **M15 GA readiness was double-removed.** It had been folded inside the old `M4–M15` band; when that band was split into a pipeline row plus a separate M15 row, the pipeline figure was carried forward unchanged rather than reduced. The total was understated by roughly 16 ew as a result.
- **The total is now recomputed from the milestone table**, not carried forward. It is checked against the table each revision.

Recorded rather than quietly corrected: a denominator that moves without explanation is how estimates lose credibility.

### Calendar under sequential execution

Total effort is now **~262–340 ew** (recomputed — see above). Calendar time depends entirely on staffing, and sequential execution forfeits parallel compression:

Based on ~213–291 ew remaining at 80% effective capacity:

| Team size | M1.5 (14.5 ew) | M1.5 + M2.0 | **Remaining to GA** |
|---|---|---|---|
| **1 engineer** | ~18 weeks | ~40–48 weeks | **~5.1–7.0 years** |
| **2 engineers** | ~9 weeks | ~20–24 weeks | **~2.6–3.5 years** |
| **3 engineers** | ~6 weeks | ~13–16 weeks | **~1.7–2.3 years** |

Within a milestone, additional engineers help only up to the **critical path** — M1.5's chain (T25→T26→T28→T27→T29) is ~9 ew of serial work and cannot compress below that at any headcount.

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

**First user-visible outcome in the project.** Design-partner onboarding is unblocked once M14.5 provides a deployed environment.

**Findings:**
- Two toolchain workarounds recorded in the validation report (ESLint flat-config bridge, `@vitejs/plugin-react` peer conflict). Neither is architectural.
- A skip condition in the contract test initially hid it — the frontend path was resolved one directory too shallow, so it silently skipped rather than running. Caught by running verbosely; a test that skips when it should run is worse than one that fails.
- **One defect found during validation and fixed:** `signora_auth` was created by migration 0005 but never connected as — the frontend defaulted to the database *owner*, which bypasses RLS on every application table and defeated the schema isolation the migration exists to create. Both tiers' permissions were individually correct; nothing asserted the relationship between them. Fixed and verified against a live database.

---

## Current Milestone

### ✅ M1.5 — Frontend Foundation · closed 2026-07-28

All nine tasks delivered. **96 frontend tests** (29 → 96), ESLint/Prettier/tsc clean, `next build` green.

| Delivered | Evidence |
|---|---|
| T25 Design system | Tokens as CSS custom properties; Tailwind wired to them; light + dark |
| T26 Shared components | Button, Input, Select, Badge, Card, Dialog, EmptyState, Skeleton, Table |
| T28 API client + TanStack Query | Workspace-prefixed keys, 4xx-never-retry policy, mutations never retried |
| T27 Application shell | Sidebar, top bar, per-region error boundaries |
| T29 Session + workspace selector | Server-side session gate; stored workspace id validated against the API's list |
| T30 Permission-aware routing | Redirects rather than renders-and-hides |
| T31 Error boundaries, loading, empty, toasts | Correlation id surfaced to the user, not only logged |
| T32 Global state | Theme (with pre-paint script), active workspace |
| T33 Component testing + CI | 96 tests; **`@vitejs/plugin-react` debt repaid** |

**AC-14 and AC-15 are enforced structurally, not by review.** 13 guard tests assert no hardcoded palette utility, no hex, no `dark:` variant, every token defined in both themes, no component reading the theme, no fabricated business record, no fixture-named file, no business route. **Each was verified to fail when deliberately violated** — a hardcoded `bg-slate-100`, a `dark:` variant, a mock array, and a premature `companies/page.tsx` each produced the right failure.

**The `@vitejs/plugin-react` debt is genuinely repaid, not masked.** Two version conflicts were the actual cause: `@eslint/js` pinned to `^10` against `eslint@^9`, and `@vitejs/plugin-react@5` requiring Vite 6 under a Vitest that pins Vite 5. Fixed at the version level — plugin pinned to v4, `@eslint/js` aligned to `^9`. **`--legacy-peer-deps` is now removed from both CI workflows and the Dockerfile**, and `npm ci` succeeds without it.

**No mock business data anywhere.** Every section ships a designed empty state. Settings is the only screen backed by real data, because Workspace & Tenancy is the only shipped module — which makes it the proof that shell, query layer, toasts, and dialog compose against a real API rather than a fixture.

**One item deferred with a stated reason, not silently:** the caller's workspace role is currently hardcoded to `owner` for *presentation only*. Resolving it properly needs a `GET /workspaces/{id}/me` endpoint that does not exist, and adding one is an API change rather than a frontend decision. Marked `TODO(M2.1)` in `authenticated-shell.tsx` and raised below. **Server-side Casbin enforcement is unaffected** — it never consulted this value.

**Not re-verified in this session:** the production image build and `make smoke`. Docker's daemon could not reach the registry from this environment (IPv6 routing; `curl` reaches it, the daemon does not). The frontend Dockerfile changed only by removing `--legacy-peer-deps`, which `npm ci` was confirmed to tolerate on the host — but the image itself was not rebuilt, and that gap is real until it is.

---

## Queued Milestones

Sequential execution — each begins only when the previous milestone's Demo Checklist passes.

| # | Milestone | Effort | Gate |
|---|---|---|---|
| 2 | **M2.0** Provider Simulation Framework | ~17–24 ew | AC-4 · identical adapter contract, config-only switching |
| 3–4 | M2.1 Provider Platform · M2.2 Provider Normalization | ~14–20 ew | Per roadmap |
| 5–6 | M3A Knowledge Graph · M3B Observation Engine | ~17–23 ew | AC-6 tenancy under load |
| 7–10 | M4 Business Events · M5A Signals · M5B Buying Scores · M6 Opportunities | ~29–43 ew | **M6 is the first sellable moment** |
| 11–14 | M8 AI Platform · M9 AI Reasoning · M10 AI Research · M11 Recommendations | ~41–56 ew | AC-8, AC-9 |
| 15–16 | M7 Timeline · M12 Revenue Intelligence Platform + business screens | ~30–43 ew | Business UI lands here |
| 17–19 | M13 Integrations · M14a Notifications · M14b Billing | ~24–34 ew | Per roadmap |
| 20 | **M14.5** Cloud Infrastructure *(deferred from M1.3B)* | ~6 ew | AC-3B · rollback executed and timed |
| 21 | M15 GA readiness | ~20–27 ew | AC-11, AC-12 |

**Full order and rationale:** [IMPLEMENTATION_ROADMAP.md §5b](IMPLEMENTATION_ROADMAP.md#5b-execution-sequence). Milestone IDs are stable labels, not sequence numbers — they are deliberately non-monotonic so that PRODUCT_ROADMAP, AI_MATURITY_ROADMAP, and every ADR cross-reference stays valid.

### Dependency corrections applied

| Correction | Why |
|---|---|
| **AI Reasoning Engine reinstated** (position 12) | Ratified module, and load-bearing: `AI Reasoning → Recommendation Engine`, and RIP lists it as a dependency. Omitted, it would never be built and two downstream modules would lose an input. |
| **Timeline moved before Revenue Intelligence Platform** (15 before 16) | `05-module-dependencies.md:76` records *"Revenue Intelligence Platform → Timeline: synchronous query"*. RIP consumes Timeline, so Timeline must precede it. |
| **Integrations (M13) reinstated** (position 17) | Ratified scope with its own architecture document and product milestone. Dropping it silently would remove committed customer-facing capability. |

None adds, removes, or substitutes a module, contract, or technology — each restores a ratified dependency.

### Module boundary rulings

**Company Domain** → part of Knowledge Graph. **Activities** → part of Timeline unless later separated. **Assignments** → unassigned; no owning context, nothing scheduled. **Workspace & Tenancy** → complete at M0, removed from the active order, retained as documented foundational work.
| 3 | **M14.5** Cloud Infrastructure *(deferred from M1.3B)* | ~6 ew | ❌ | AC-3B · rollback executed and timed |
| 4 | M15 GA readiness | ~20–27 ew | ✅ load at volume | Per roadmap |

### Cloud infrastructure is deferred, not removed

**M1.3B has moved to M14.5, immediately before GA readiness.** Sequencing only: the target production architecture is unchanged, the scope is unchanged, and nothing is redesigned. [ADR-0022](docs/architecture/adr/0022-devops-infrastructure-and-deployment-topology.md) remains ratified.

Deferred: Terraform, ECS, RDS and ElastiCache provisioning, Secrets Manager integration, the cloud deployment pipeline, cloud rollback validation, production monitoring dashboards, Auto Scaling.

**Why.** M1.3A already produced a running production stack. Cloud infrastructure adds *reachability*, not capability — it makes no pipeline module work, and until the pipeline exists there is nothing to reach. Building it now means carrying a deployed environment through ~200 ew that does not need one.

**What it costs, plainly.** No externally reachable environment until M14.5. Design partners cannot use the product remotely before then; a demo is a local stack or a screen share. Accepted deliberately.

**What keeps it cheap:** the [Infrastructure Contract](IMPLEMENTATION_ROADMAP.md#5a-infrastructure-contract) — ten requirements, all satisfied today, enforced every milestone. The failure mode of "we'll add ops later" is discovering at M14.5 that stateful services and hardcoded configuration accumulated for two years. `make smoke` is what will notice.

### Why M1.3 was split

M1.3A proves the **application** is deployable; M14.5 proves **AWS** is configured. Run together, a failure gives no signal about which one is wrong — and every application-level fault (a container that will not start, a migration runner racing two replicas, a readiness probe green before the database is reachable) costs minutes locally and an afternoon inside ECS.

### Why M1.4 exists

Verification is currently spread across a backend suite, a frontend suite, a cross-tier contract test, and a checklist a human reads. Each is individually green while the *composition* goes unverified — which is exactly where the M1.2 credential defect lived. One command turns "everything passes" into a claim about the system rather than about its parts.

### M2.0 — why it precedes every pipeline module

A permanent platform capability, not throwaway tooling — used for local development, integration testing, E2E testing, demos, AI evaluation, regression testing, performance benchmarking, and customer onboarding demos.

**It also builds the Provider Port**, as its first concrete implementation. That satisfies the YAGNI ruling and validates the port with working code before any vendor adapter is written or contract signed.

**Binding rule:** simulated providers implement *exactly* the same adapter contract as production providers. Switching is configuration only; no `if simulated:` branching may exist in any layer; the ingestion pipeline is byte-identical in both modes.

**Highest-risk control:** the simulator must never activate in production — it would fabricate customer intelligence. Guarded by an environment check, unambiguous ingestion logging, health-endpoint visibility, and an alert, all test-enforced.

---

## Current Sprint

**Sprint:** M2.0 Sprint 1 — **awaiting approval.**

**Scope — M2.0 only.** Single stream; no concurrent milestone work.

M2.0 is the largest milestone since M0 (~17–24 ew) and the first that builds product capability rather than substrate. Its binding rules are already fixed in [IMPLEMENTATION_ROADMAP.md §8](IMPLEMENTATION_ROADMAP.md#8-provider-simulation-framework--design):

- **It builds the Provider Port**, as its first concrete implementation — satisfying the YAGNI ruling and validating the port with working code before any vendor adapter is written.
- **Simulated providers implement exactly the same adapter contract as production ones.** Switching is configuration only; no `if simulated:` branch may exist in any layer.
- **The simulator must never activate in production** — it would fabricate customer intelligence. Guarded by environment check, ingestion logging, health-endpoint visibility, and an alert, all test-enforced.

**What the foundation now guarantees it.** `make smoke` runs before this milestone starts and after every change in it, so a regression in the substrate is attributable to the change that caused it rather than discovered weeks later.

---

## Blocked Items

| Item | Blocked by | Severity | Owner |
|---|---|---|---|
| ~~All 13 core intelligence modules~~ | ~~T7/T8 — event bus relay + dispatch~~ | ✅ **CLEARED** | M1.1 |
| ~~Any human access / any demo~~ | ~~T13/T14 — Better Auth issuer~~ | ✅ **CLEARED** | M1.2 |
| Any *remote* environment | T22/T23 — Terraform + ECS (**M14.5, deliberately deferred**) | 🟡 Accepted | Unassigned |
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
| Workspace role hardcoded to `owner` in the frontend shell | Low | **Approved to remain.** Presentation only; server-side Casbin never consulted it. Adding `GET /workspaces/{id}/me` solely to satisfy frontend presentation would be an API shaped by a UI need rather than a domain one. | When the workspace domain naturally evolves — not before |
| Casbin policy is coarse RBAC | Low | Correct for current needs | When enterprise custom roles are required |
| No API versioning scheme | Low | Deliberate — speculative with one first-party client | First breaking change |

| Relay `LISTEN/NOTIFY` wake-up not yet wired to the loop | Low | `notify_outbox` exists and polling is the correctness guarantee; the notification only collapses idle latency from ~1s | M1.3A or when latency matters |
| ~~`@vitejs/plugin-react` removed from frontend devDependencies~~ | — | — | ✅ **Repaid in M1.5.** The stated cause was wrong: it was never `better-auth`'s Svelte peers. Two real conflicts — `@eslint/js` pinned to `^10` against `eslint@^9`, and `@vitejs/plugin-react@5` requiring Vite 6 under a Vitest pinning Vite 5. Both fixed at the version level, and **`--legacy-peer-deps` removed from both CI workflows and the Dockerfile**. A misdiagnosed cause is why the flag survived three milestones. |

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
| Operations runbook | ⬜ **Required by M1.3A** (stack lifecycle), extended in M14.5 (deploy, rollback, restore) |
| Onboarding guide | ⬜ Needed when team exceeds ~3 |

**Documentation drift: zero.** All internal links resolve. Docs have been updated in the same commit as the code they describe, every time.

**Deliberate numbering choice:** M1 was split and M2.0 inserted *without renumbering M2+*, so PRODUCT_ROADMAP.md and AI_MATURITY_ROADMAP.md remain valid without edits. The mapping table is in [IMPLEMENTATION_ROADMAP.md §4](IMPLEMENTATION_ROADMAP.md#4-milestone-structure).

---

## Next Task

### 🎯 M1.5 · T25 — Design system

**Why first:** zero dependencies, and every component in T26 is built from its tokens. A component library started before its design tokens hardcodes colours, spacing, and type scale into fifty files.

**Then:** T26 → T28 → T27 → T29 → T30 → T31 → T32 → T33.

**Then M2.0** Provider Simulation Framework, after which business screens become buildable against real domain models.

**Awaiting:** approval of the M1.5 task breakdown, and a decision on the three dependency findings in [IMPLEMENTATION_ROADMAP.md §5b](IMPLEMENTATION_ROADMAP.md#5b-updated-implementation-order). Every task remains unassigned.

---

## Change Log

| Date | Change |
|---|---|
| 2026-07-28 | v9 — **Platform Foundation approved and closed.** Eight platform contracts ratified (Platform Runtime, Authentication Boundary, Deployment Foundation, Platform Smoke Test, Security Invariants, Tenant Isolation Policy, Platform Infrastructure Policy, Platform Freeze). **M1.5 Frontend Foundation inserted** after M1.4 — frontend platform only, no business screens, no mock data. Business UI deferred until M2.0 produces real domain data. Cloud infrastructure confirmed at M14.5 with all task IDs and ADR references intact. Three dependency findings raised against the approved order (two graph inversions, five omitted modules, three unratified module names) — flagged, not silently reconciled. Sequencing only; the approved architecture is unchanged. |
| 2026-07-28 | v8 — **M1.4 Platform Smoke Test complete; platform foundation closed.** `make smoke`: 16 stages, ~46s, in CI, every stage proven to fail when deliberately broken. Two defects found by it — a relay that died permanently on a transient database failure (first and only post-freeze platform change, under the production-defect exemption), and two bugs in the smoke script itself that would have made it lie. **Cloud infrastructure deferred from M1.3B to M14.5** — sequencing only, nothing removed or redesigned — with a ten-point Infrastructure Contract (roadmap §5a) binding every milestone until then. 313 tests, coverage 95.63%. |
| 2026-07-28 | v7 — **M1.3A Deployment Foundation complete.** Production images (multi-stage, non-root, no secrets), concurrency-safe migration runner refusing runtime identities, 6-service production Compose stack, and Disaster Recovery Validation across Postgres/Redis/API/workers. Four defects found by running the stack rather than by tests — most seriously a worker that could never start while the whole suite passed. `signora_platform/` frozen. ADR-0022 updated with as-built topology. 310 tests, coverage 95.65%. |
| 2026-07-28 | v6 — **M1.2 approved.** Security Invariants suite established: 47 permanent invariants across authentication, authorization, database, and platform, each proven to fail when its guarantee is deliberately removed; wired into CI as a separately-reported job. Migration/runtime credential separation adopted as a permanent engineering rule (CLAUDE.md §8). M1.3 split into M1.3A Deployment Foundation and M1.3B Cloud Infrastructure; M1.4 Platform Smoke Test added; AC-3 split into AC-3A/3B/3C and AC-13 added. `@vitejs/plugin-react` recorded as scheduled technical debt. One architectural question raised for decision: platform-table read scope. |
| 2026-07-28 | v5 — **M1.2 Authentication Boundary complete.** 7 tasks plus 3 added requirements; 242 backend and 29 frontend tests; Demo Checklist 10/10; AC-2 passed; Architecture Validation Report issued. One defect found during validation: `signora_auth` created but never connected as, with the frontend defaulting to the database owner. |
| 2026-07-28 | v4 — **M1.1 Platform Runtime complete.** 11 tasks, 82 new tests (198 total), coverage 95.01% CI-gated, Demo Checklist 13/13, AC-1 passed. Dead code from the pagination refactor removed. 06-events.md updated to v3. |
| 2026-07-28 | v3 — sequential single-stream execution adopted; calendar restated by team size; Demo Checklist added as a completion gate; progressive AI regression assertion model defined; simulator identical-adapter-contract rule recorded |
| 2026-07-28 | v2 — M1 split into M1.1/M1.2/M1.3; M2.0 Provider Simulation Framework added; per-milestone Demo Scenario, User-Visible Outcome, DoD, Rollback, Operational Readiness introduced; R-14 identified; estimate revised to 225–305 ew |
| 2026-07-28 | v1 — Initialized. M0 closed. Roadmap documents created. |

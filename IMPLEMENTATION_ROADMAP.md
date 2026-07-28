# IMPLEMENTATION_ROADMAP.md

> **Owner:** CTO / Principal Architect · **Audience:** Engineering, TPM, Exec
> **Status:** Living document — revised at each milestone boundary
> **Revision:** **v3** — sequential single-stream execution model adopted; Demo Checklist added to every milestone; Provider Simulation Framework strengthened with the identical-adapter-contract rule; progressive AI regression assertion model defined.
> **Source of truth:** [`docs/architecture/`](docs/architecture/) (19 documents, 27 ADRs), [`CLAUDE.md`](CLAUDE.md), [`PRODUCT_DIFFERENTIATORS.md`](PRODUCT_DIFFERENTIATORS.md)
>
> This roadmap sequences *what gets built and in what order*. It does not introduce architecture — every module, boundary, and technology named here is already ratified. Where this document and the architecture set disagree, the architecture set wins and this document is the bug.

---

## 1. Execution Model

### Sequential single-stream execution

**Implementation proceeds as one prioritized stream.** The roadmap's dependency graph governs *order*; it does not imply concurrency. Optimising for minimal context switching is the ruling constraint, not maximal parallelism.

```
M1.1 Platform Runtime → M1.2 Authentication Boundary → M1.3A Deployment Foundation → M1.4 Platform Smoke Test → M1.5 Frontend Foundation
     → M2.0 Provider Simulation Framework → M2.1 → M3 → … → M15
```

The parallel-workstream design in §9 is **retained for future team scaling** and should be re-read the moment staffing increases. It is not the current operating assumption.

### Calendar consequence — stated plainly

Total effort is unchanged by this decision; **calendar time is not**. Sequential execution forfeits the compression that parallelism buys, and the arithmetic is worth seeing rather than discovering later.

| Team size | M1 (33 ew) | M1 + M2.0 | **To GA (225–305 ew)** |
|---|---|---|---|
| **1 engineer** | ~41 weeks | ~62–71 weeks | **~5.4–7.3 years** |
| **2 engineers** | ~21 weeks | ~31–36 weeks | **~2.7–3.7 years** |
| **3 engineers** | ~14 weeks | ~21–24 weeks | **~1.8–2.4 years** |
| 6 engineers *(parallel model, for reference)* | ~7 weeks | ~10–12 weeks | ~0.9–1.2 years |

Assumes 80% effective capacity. Note that within a milestone, extra engineers help only up to the **critical path**, which is serial work: M1.1's chain (T6→T7→T8→T9→T10) is ~10 ew and cannot be compressed below that regardless of headcount.

**This is not an argument against the decision.** For a small team, context switching genuinely destroys more throughput than parallelism recovers, and the v2 parallel plan assumed staffing that does not exist. The decision is sound; the timeline consequence simply needs to be owned explicitly at planning time rather than surfaced as a slip later.

**Recommendation:** if the GA horizon matters commercially, the highest-leverage lever is **the second and third engineer** — moving from 1 to 3 roughly triples throughput. Beyond ~3, the pipeline's serial dependency chain limits further gains until modules can be worked concurrently.

---

## 2. Current Implementation Audit

Audit performed against the ratified thirteen-module map in [04-modules.md](docs/architecture/04-modules.md).

| Dimension | Value |
|---|---|
| Architecture documents | 19 + 27 ADRs — complete and internally consistent (651 cross-links verified) |
| Core modules implemented | **1 of 14** (Workspace & Tenancy) |
| Production code | ~2,660 LOC (`signora_platform` 1,288 · `modules` 1,250 · `apps` 124) |
| Migration code | 581 LOC, 4 revisions, verified reversible |
| Tests | **116 passing** (79 unit, 37 integration) · ~2,058 LOC |
| Test coverage | **Not measured** — `pytest-cov` not installed |
| Type checking | mypy `strict` clean across 71 files |
| Boundary enforcement | 3 import-linter contracts, verified to fail on deliberate violation |
| Frontend | **Not started** |
| Infrastructure-as-code | **Not started** |

**Honest characterisation.** The foundation is disproportionately strong relative to surface area built — tenancy, auth, authorization, error contract, and transactional outbox are production-grade and adversarially tested. That is the correct order, since these are ruinous to retrofit. But **~95% of differentiating capability is still ahead.**

Two findings drive the M1 structure:

1. **No working end-to-end authentication path.** The API verifies tokens correctly; nothing mints them except the test suite. → **M1.2**
2. **The event bus is half-built, and that half is the blocking half.** The outbox (durability) is complete; the relay (dispatch) is not. All 13 pipeline modules are consumers. → **M1.1**

---

## 3. Existing Completed Modules

### Workspace & Tenancy — ✅ Complete

| Layer | Contents |
|---|---|
| `domain/` | Workspace, Membership aggregates · WorkspaceRole · domain events · exceptions |
| `application/` | 4 ports (Protocols) · 5 use cases |
| `infrastructure/` | SQLAlchemy models & repositories · outbox adapter · tenant-context adapter · query service · composition root |
| `interface/` | FastAPI router · schemas · error mappings |
| `public/` | Event payload contracts · `WorkspaceQueryPort` |

### Platform (`signora_platform/`)

| Component | Status |
|---|---|
| `db/` | ✅ Base, mixins, async sessions, RLS helpers, base repository |
| `event_bus/` | ⚠️ **Partial** — envelope, outbox model, publisher; **relay/dispatch missing** |
| `auth/` | ✅ RS256 verifier (pinned algorithms), principal, errors |
| `authorization/` | ✅ Casbin model, policy, enforcer |
| `api/` | ✅ Error envelope, handlers, DI chain, cursor-page envelope |
| `pagination.py` · `settings.py` | ✅ |

---

## 4. Missing Components

### Core intelligence modules — 13 of 13 outstanding

| # | Module | Complexity | # | Module | Complexity |
|---|---|---|---|---|---|
| 1 | Provider Platform | High | 8 | Opportunity Engine | Medium |
| 2 | Provider Normalization | Medium-High | 9 | AI Research Engine | **Very High** |
| 3 | Knowledge Graph | **Very High** | 10 | AI Reasoning Engine | High |
| 4 | Observation Engine | Medium | 11 | Recommendation Engine | Medium |
| 5 | Business Event Engine | High | 12 | Timeline | Medium |
| 6 | Signal Engine | High | 13 | Revenue Intelligence Platform | Medium-High |
| 7 | Buying Score Engine | Medium-High | | | |

### Platform components outstanding

| Component | Blocking? | Milestone |
|---|---|---|
| Event bus relay + worker fleet + DLQ | 🔴 Blocks all 13 modules | M1.1 |
| Observability (OTel, Sentry, structured logging) | 🟠 Blocks operability | M1.1 |
| Better Auth issuer (Next.js) | 🔴 Blocks all human access | M1.2 |
| Terraform / AWS IaC | Blocks any *remote* deploy — deliberately deferred; the local production stack covers development and demos | M14.5 |
| **Provider Simulation Framework** | 🟠 Blocks offline dev, deterministic demos, AI regression | **M2.0** |
| Provider Abstraction Layer | Built *with* the simulator (its first implementation) | M2.0 |
| AI Provider Abstraction Layer + Prompt Registry | Blocks both AI engines | M8 |
| AI Evaluation Harness | Blocks trustworthy AI | M8 |
| Integration Abstraction Layer | Blocks CRM/comms | M13 |

**Deferred by ruling (YAGNI):** no port is built speculatively. Provider Port in M2.0, AI Provider Port in M8, Integration Port in M13 — each with its first concrete implementation, per `CLAUDE.md` §6.

---

## 5. Milestone Structure

M1 is split into three; M2.0 is inserted before data ingestion. **All other milestone numbers are unchanged**, so [PRODUCT_ROADMAP.md](PRODUCT_ROADMAP.md) and [AI_MATURITY_ROADMAP.md](AI_MATURITY_ROADMAP.md) remain valid.

| Implementation milestone | Product milestone | Effort |
|---|---|---|
| M0 ✅ | M0 | — |
| **M1.1** Platform Runtime | M1 | ~15.5 ew |
| **M1.2** Authentication Boundary | M1 | ~11.5 ew |
| **M1.3A** Deployment Foundation | M1 | ~5.5 ew |
| **M1.4** Platform Smoke Test | *(foundation completion gate)* | ~1.5 ew |
| **M1.5** Frontend Foundation | M1 | ~14.5 ew |
| **M2.0** Provider Simulation Framework | *(internal enablement)* | ~17–24 ew |
| M2.1 Provider Platform & Normalization | M2 | ~14–20 ew |
| M3 Knowledge Graph & Observation Engine | M3 | ~17–23 ew |
| M4–M15 | M4–M13 | ~160–220 ew |
| **M14.5** Cloud Infrastructure *(deferred from M1.3B)* | *(production readiness)* | ~6 ew |

**Total to GA: ~246–326 ew** (M1.5 adds ~14.5 ew of frontend platform work previously absorbed inside M12). See §1 for calendar at various team sizes.

### Cloud Infrastructure is deferred, not removed

**M1.3B has moved to M14.5, immediately before GA readiness.** This is a sequencing change and nothing else: the target production architecture is unchanged, the scope is unchanged, and the milestone is not redesigned. [ADR-0022](docs/architecture/adr/0022-devops-infrastructure-and-deployment-topology.md) remains the ratified deployment topology.

What moved: Terraform, ECS, RDS provisioning, ElastiCache provisioning, Secrets Manager integration, the cloud deployment pipeline, cloud rollback validation, production monitoring dashboards, and Auto Scaling.

**Why the order changed.** M1.3A already produced a running production stack — production images, per-tier identities, a concurrency-safe migration runner, and validated restart behaviour. Cloud infrastructure adds *reachability*, not capability: it does not make a single pipeline module work, and until the pipeline exists there is nothing to reach. Building it now would mean carrying and maintaining a deployed environment through roughly 200 engineer-weeks of work that does not need one.

**What this costs, stated plainly.** No externally reachable environment until M14.5. Design partners cannot use the product remotely before then; a demo is a local stack or a screen share. That is a real cost and it is being accepted deliberately, not overlooked.

**What protects the decision from becoming expensive:** the Infrastructure Contract in §5a. Deferring cloud infrastructure is only cheap if the code stays deployable the entire time — the failure mode of "we'll add ops later" is discovering at M14.5 that stateful services, file-system state, and hardcoded configuration have accumulated for two years. Every requirement in that contract is already satisfied today and is enforced from here on, so M14.5 provisions infrastructure for an application that is already ready for it.

---

## 5a. Infrastructure Contract

**Binding on every milestone from M1.3A to GA.** Cloud infrastructure is deferred; cloud *readiness* is not. Every module must remain deployable to the architecture in [ADR-0022](docs/architecture/adr/0022-devops-infrastructure-and-deployment-topology.md) at all times, so that M14.5 provisions infrastructure for an application already ready for it rather than beginning a migration.

Each requirement below is already satisfied. The contract's purpose is that it stays that way through ~200 ew of pipeline work, when no deployed environment exists to notice a violation.

| Requirement | What it means | How it is enforced |
|---|---|---|
| **Stateless services** | No process holds state another process needs. No in-memory session, no local cache used as a system of record, no sticky routing. Scaling to *n* replicas changes throughput only. | Disaster Recovery Validation restarts every component; anything stateful loses data and fails. Extended each milestone. |
| **Environment-based configuration** | Every value read through `Settings`. No module calls `os.environ`, no configuration file ships in an image. | `signora_platform/settings.py` is the sole reader; import-linter keeps modules off it. |
| **Twelve-Factor compliance** | Config in the environment, backing services attached by URL, processes disposable, dev/prod parity, logs to stdout as a stream, admin tasks as one-off processes. | The migration runner is a discrete one-off process, not a service behaviour. Logs go to stdout. The local production stack *is* the parity check. |
| **Storage abstraction** | Nothing writes to the local filesystem expecting persistence. Object storage is reached through a port, never a path. | MinIO locally, S3 in production, one adapter — the same substitution ADR-0022 assumes. |
| **Health endpoints** | Liveness that does not touch dependencies, so a database blip never restarts a healthy process. | `/health`; asserted against an unreachable database. |
| **Readiness endpoints** | Dependency-aware, and **503 when not ready** — orchestrators route on the status code and never read the body. | `/ready` and the frontend's `/api/health`; both wired to container healthchecks. |
| **Structured logging** | Fielded JSON to stdout, every line carrying `workspace_id` and `correlation_id`. No file handlers, no rotation, no free-text concatenation. | `signora_platform/observability`; structural secret redaction on top. |
| **OpenTelemetry** | Every new asynchronous flow traceable end to end before it is considered complete. | Configured; absent exporter disables rather than fails. Required of each new flow by §12. |
| **Secret injection via configuration** | No secret in an image, a repository, or a default. Values arrive at start. | Image inspection asserts no secret-bearing layer; `.dockerignore` excludes `.env`. |
| **Production Docker images** | Multi-stage, non-root, no build toolchain in the runtime layer, immutable tags. | Both images; asserted by the smoke test. |

**Claude must not accept a change that violates this contract**, including one that would be "fixed during M14.5". A violation is cheap to prevent and expensive to unwind after it has been built on. If a module appears to require statefulness, local disk, or configuration outside `Settings`, that is a finding to raise — not a temporary exception to take.

---

## 5b. Updated Implementation Order

Approved 2026-07-28. **Sequencing only** — no module, technology, or contract changes.

### Phase 1 — Foundation ✅ complete

`M1.1 Platform Runtime` → `M1.2 Authentication Boundary` → `M1.3A Deployment Foundation` → `M1.4 Platform Smoke Test`

The platform is architecturally stable. `signora_platform/` is frozen (CLAUDE.md §20a); the Platform Runtime, Authentication Boundary, Deployment Foundation, Platform Smoke Test, Security Invariants, Tenant Isolation Policy, Platform Infrastructure Policy, and Platform Freeze are **platform contracts** — foundation capabilities, not work in progress.

### Phase 2 — Enablement

`M1.5 Frontend Foundation` → `M2.0 Provider Simulation Framework`

Neither builds a business feature. Together they are what makes every later milestone cheap: a frontend platform business screens plug into, and realistic domain data for them to render.

### Phase 3 — Pipeline

Follows the ratified dependency graph in [04-modules.md](docs/architecture/04-modules.md) and [05-module-dependencies.md](docs/architecture/05-module-dependencies.md), which fixes the order regardless of preference:

```
Provider Platform → Provider Normalization → Knowledge Graph → Observation Engine
  → Business Event Engine → Signal Engine → Buying Score Engine → Opportunity Engine
  → AI Platform (abstraction layer + Prompt Registry + eval harness)
  → AI Reasoning Engine → AI Research Engine → Recommendation Engine → Timeline
  → Revenue Intelligence Platform → Integrations → Billing & workflow
```

### Phase 4 — Production Readiness

`M14.5 Cloud Infrastructure` *(deferred)* → `M15 GA readiness` → **General Availability**

### Business UI is deferred to after M2.0

No company, opportunity, signal, timeline, AI-recommendation, or analytics screen is built before the Provider Simulation Framework exists. **Business screens consume real domain models, never temporary mocked JSON.**

A page built against hand-written JSON encodes a shape the domain does not have. The mock becomes the contract; the real model arrives; the page is rewritten — twice the work, and the first version silently teaches everyone the wrong model. M1.5 ships designed empty states instead, which every screen needs permanently anyway.

### Dependency verification

Three findings from checking the approved order against the ratified graph. **None is a disagreement with the intent — all three are places where the order as written could not be built.**

| # | Finding | Resolution applied |
|---|---|---|
| 1 | **Observation Engine before Knowledge Graph.** The graph is `KG → OE`: Observation Engine consumes the Knowledge Graph's entities. Building it first leaves it with nothing to observe. | Graph order retained: Knowledge Graph, then Observation Engine. |
| 2 | **Signal Engine before Business Events.** The graph is `BEE → SE`: signals are derived *from* business events. This also inverts [PRODUCT_ROADMAP.md](PRODUCT_ROADMAP.md), whose M4 is Business Events and M5 is Signals. | Graph order retained: Business Event Engine, then Signal Engine. |
| 3 | **Five ratified modules absent from the list**, three of them load-bearing: **Provider Normalization** (`PP → PN → KG`), **Buying Score Engine** (`SE → BSE → OP`), **AI Research Engine** (`OP → ARE`), plus the **AI Platform** milestone and **Revenue Intelligence Platform**. AI Reasoning Engine cannot precede the AI Platform — CLAUDE.md §10 requires all vendor access through the AI Provider Abstraction Layer and all prompts through the Prompt Registry, both of which the AI Platform milestone builds. | All five retained in graph position. |

Both inversions also contradict PRODUCT_ROADMAP's own ordering, which is why they read as transcription slips rather than intent. **Raised rather than silently reconciled** — if either is deliberate, it is a change to the dependency graph and belongs to the RFC process in [01-overview.md](docs/architecture/01-overview.md), not to a sequencing decision.

**Three names in the approved order are not ratified modules:** *Company Domain*, *Activities*, and *Assignments*. Nothing has been created for them. The nearest ratified homes are Knowledge Graph (company entities) and Timeline (activities); assignments have no current owner. Introducing any of them is a new bounded context and needs an RFC — flagged here rather than guessed at.

**Workspace & Tenancy appears in the order but is already complete** (M0, shipped). No work is scheduled for it.

---

## 6. Milestone Definitions

Every milestone specifies: Scope · Simulator Requirement · Demo Scenario · **Demo Checklist** · User-Visible Outcome · Definition of Done · Rollback Strategy · Operational Readiness Checklist.

**A milestone is not complete until its Demo Checklist passes.**

---

### ✅ M0 — Secure Multi-Tenant Foundation · COMPLETE

**Scope:** Architecture set, Workspace & Tenancy, platform foundation, RLS tenancy, JWT verification, Casbin, CI.

**Simulator requirement:** ❌ None.

**Demo scenario:** Internal. Run the RLS regression suite against pre-fix policies (fails) and post-fix (passes) — isolation proven, not asserted.

**Demo checklist:**
- [x] Full test suite green (116 tests)
- [x] RLS regression tests fail against pre-fix policies, pass after
- [x] import-linter fails on a deliberate boundary violation
- [x] Migrations reverse and re-apply cleanly

**User-visible outcome:** None.

**Definition of Done:** ✅ Met.

**Rollback strategy:** N/A — no deployed environment existed.

**Operational readiness:** N/A.

---

### 🔄 M1.1 — Platform Runtime · **NEXT**

**Scope:** Redis in CI · structured logging · OpenTelemetry · Sentry · event bus schema (DLQ + idempotency ledger) · outbox relay · subscription/dispatch · ARQ worker fleet · retry & DLQ · pipeline metrics · coverage gate.

**Effort:** ~15.5 ew · **Critical path:** T6→T7→T8→T9→T10 ≈ 10 ew serial · **Tasks:** T1–T11 (§7)

**Simulator requirement:** ❌ **Not required.** Verified with a test-only consumer. The simulator enters at the Provider layer, which does not exist yet.

**Demo scenario:**
> *"Watch an event travel the platform."* Create a workspace through the existing API. Show the `outbox_event` row committed in the same transaction as the domain write. Show the relay claiming it, marking `relayed_at`, and enqueueing to Redis. Show an ARQ worker consuming it. Deliver the same event twice — the handler runs **exactly once**. Force a handler failure: watch it retry with backoff, land in `dead_letter_event` without blocking the queue, then replay successfully. Throughout, follow one `correlation_id` across all three processes in a single trace.

**Demo checklist:**
- [ ] Workspace created via API; `outbox_event` row visible, committed atomically with the domain write
- [ ] Relay claims the row and sets `relayed_at` exactly once
- [ ] Message appears on the expected Redis queue
- [ ] ARQ worker consumes and acknowledges it
- [ ] **Duplicate delivery → handler invoked exactly once** (`processed_event` shown)
- [ ] Handler failure retries with visible exponential backoff
- [ ] Exhausted retries land in `dead_letter_event`; the queue keeps draining
- [ ] DLQ replay succeeds
- [ ] Two relay instances run concurrently; **no event double-enqueued**
- [ ] Redis stopped mid-run → events remain unrelayed, then drain on recovery, **zero loss**
- [ ] One `correlation_id` traced across API → relay → worker in a single OpenTelemetry trace
- [ ] Log lines show `workspace_id` + `correlation_id`; grep confirms **no token or secret** present
- [ ] Coverage report produced; CI gate demonstrated failing below baseline

**User-visible outcome:** **None.** Pure infrastructure. Do not demo to customers.

**Definition of Done:**
- [ ] Demo Checklist passes in full
- [ ] Idempotency is platform-owned via `processed_event`; no module implements its own
- [ ] RLS context established from the event envelope before any handler touches the database
- [ ] Worker pools independently runnable; graceful shutdown drains in-flight work
- [ ] Metrics emitted: queue depth, dispatch latency, retry rate, DLQ rate, outbox lag
- [ ] `06-events.md` updated: relay semantics, both new tables, platform-owned idempotency decision
- [ ] AC-1 passed

**Rollback strategy:**
- **Code:** relay and workers are separate services. Rollback = scale relay to zero; events accumulate in the outbox and drain on redeploy. **No data loss** — the outbox is the durable source of truth.
- **Schema:** migration 0004 reversible. `dead_letter_event` and `processed_event` are additive; dropping them loses dispatch bookkeeping only, never domain state.
- **Blast radius:** nil for the existing API — no current endpoint depends on dispatch.

**Operational readiness checklist:**
- [ ] Runbook: inspect outbox backlog · drain a queue · replay from DLQ
- [ ] Alert: DLQ write rate > 0
- [ ] Alert: outbox lag (oldest unrelayed event age) over threshold
- [ ] Alert: relay process down
- [ ] Dashboard: per-pool queue depth, dispatch latency, error rate
- [ ] Worker pool scaling procedure documented
- [ ] Redis failure mode tested and documented

---

### 🔄 M1.2 — Authentication Boundary

**Scope:** Next.js 15 scaffold · Better Auth · Google & Microsoft OAuth · RS256 JWT issuance · signing key management · typed API client · frontend shell · E2E auth journey.

**Effort:** ~11.5 ew · **Critical path:** T12→T13→T14→T15→T18 ≈ 8 ew serial · **Tasks:** T12–T18

**Simulator requirement:** ❌ Not required.

**Demo scenario:**
> *"First real login."* A human opens Signora, signs in with Google, creates the workspace "Acme Revenue", and sees it listed. A second human signs in with Microsoft, creates their own workspace, and **provably cannot see the first user's** — shown live. Then inspect the JWT: RS256, correct claims, 15-minute expiry. Finally, present a token signed by a different key and watch the backend reject it.

**Demo checklist:**
- [ ] Google sign-in completes; user lands authenticated
- [ ] Microsoft sign-in completes
- [ ] Workspace created through the UI against the real API
- [ ] Workspace list, switch, and sign-out all work
- [ ] Second user **cannot see** the first user's workspace (404, not 403)
- [ ] JWT decoded live: RS256, all required claims, 15-min expiry
- [ ] Token from a foreign signing key → **401**
- [ ] Expired token → `token_expired`, client refreshes and retries successfully
- [ ] **Private key demonstrably absent from backend configuration**
- [ ] E2E Playwright journey green in CI, including the isolation negative case

**User-visible outcome:** ✅ **First real user-visible functionality.** Design-partner onboarding can begin at close.

**Definition of Done:**
- [ ] Demo Checklist passes in full
- [ ] JWT claims match [18-authentication.md](docs/architecture/18-authentication.md) §JWT Contract exactly
- [ ] **Contract test in CI:** a token minted by Next.js verifies against the real Python verifier
- [ ] Better Auth tables in a dedicated `auth` schema in the existing PostgreSQL instance
- [ ] Frontend CI enforces ESLint, Prettier, TypeScript, Vitest
- [ ] `18-authentication.md` updated with issuer-side configuration as built
- [ ] AC-2 passed

**Rollback strategy:**
- **Frontend:** versioned static deploy; roll back by repointing to the previous build. No backend coordination.
- **Auth schema:** isolated in `auth`, so rollback cannot touch application tables.
- **Key rotation failure:** documented revert to the prior key pair — a configuration rollback, not a code deploy, since both tiers read keys from configuration.
- **Blast radius:** total for user access, nil for data.

**Operational readiness checklist:**
- [ ] Runbook: signing-key rotation, **executed at least once**
- [ ] Runbook: OAuth misconfiguration diagnosis
- [ ] Alert: authentication failure rate spike
- [ ] Alert: token verification failure rate at the API
- [ ] OAuth client secrets in AWS Secrets Manager
- [ ] Session and token TTLs documented and agreed
- [ ] Frontend Sentry wired with source maps

---

### 🔄 M1.3A — Deployment Foundation

**Scope:** Production Docker images (API, worker) · production Docker Compose stack · health checks · readiness checks · secrets management · migration runner · local production deployment.

**Effort:** ~5.5 ew · **Critical path:** T19→T20→T21→T21b = 5.5 ew serial · **Tasks:** T19–T21b

**Simulator requirement:** ❌ Not required.

**Why this comes first:** the application platform and the cloud platform fail for entirely different reasons, and debugging both at once means never knowing which one is broken. A container that will not start, a migration runner that races two API replicas, a readiness probe that reports healthy before the database is reachable — each of these is a two-minute diagnosis locally and an afternoon inside ECS. M1.3A proves the application is deployable; M14.5 proves AWS is configured. Neither answer is trustworthy if both are being asked simultaneously.

**Demo scenario:**
> *"docker compose up, and it's production."* From a clean checkout with no local Python or Node toolchain, bring up the full stack — Postgres, Redis, migration runner, API, worker pools, frontend — using production images. Migrations run once as a discrete pre-start step under the **migration identity**; the API then starts under `signora_app` and the frontend under `signora_auth`. Sign in, create a workspace, watch an event traverse the outbox relay into a worker. Then stop the database and watch readiness turn red while liveness stays green.

**Demo checklist:**
- [ ] API and worker images build from a clean checkout with no local toolchain
- [ ] Images are non-root, multi-stage, and contain no build toolchain in the final layer
- [ ] `docker history` shows **no embedded secrets**; all configuration arrives by environment
- [ ] Migration runner executes once as a discrete step, under the **migration identity**
- [ ] Migration runner is safe to run concurrently — two simultaneous starts do not race
- [ ] API starts as `signora_app`; frontend starts as `signora_auth` — **verified from inside the running containers**
- [ ] `/health` (liveness) stays green when the database is stopped; `/ready` turns red
- [ ] Worker pools start, consume from Redis, and report healthy
- [ ] Full demo flow — sign in → create workspace → event relayed → worker processes it — passes against the composed stack
- [ ] Stack comes up from `docker compose up` alone, with no manual step
- [ ] Security Invariants suite passes **against the composed stack**, not only against a developer database

**Disaster Recovery Validation (T21b):**

Restarting any component must lose nothing. Each row is a deliberate restart with assertions taken before and after — not an inference from the design.

| Restarted | Must survive |
|---|---|
| **PostgreSQL** | Unrelayed outbox rows; dead letters; the idempotency ledger. On reconnect the relay resumes from where it stopped, with no event relayed twice and none skipped. |
| **Redis** | Queued-but-unprocessed events. Redis is a *transport*, not the system of record — anything lost from the queue is still in the outbox and is re-relayed. This is the property the outbox exists to provide, and the restart is what proves it rather than assuming it. |
| **API** | Nothing in flight is acknowledged-then-lost: a request that returned 201 has its state and its events committed together. Authentication survives because sessions live in Better Auth's tables and tokens are stateless — no user is signed out by an API restart. |
| **Workers** | In-flight jobs. A worker killed mid-handler must not leave a consumed idempotency claim, so the redelivered event is processed exactly once on retry rather than dropped as a duplicate. |

Also asserted across every restart:

- **Tenant isolation holds** — the Security Invariants suite is re-run after each restart, not only at start. A pooled connection carrying stale `SET LOCAL` state, or a role that reconnected with different attributes, would show up here and nowhere else.
- **Event ordering per entity is preserved** — the relay claims in `event_id` order within a workspace using `FOR UPDATE SKIP LOCKED`; a restart must not reorder events for a given aggregate. Cross-entity ordering is explicitly *not* guaranteed and is asserted not to be relied upon.
- **No silent data loss** — event counts are reconciled across the restart boundary: published = relayed + pending, always.

**Why this belongs to M1.3A rather than M1.3B:** these are properties of the *application*, not of AWS. A worker that loses in-flight jobs on SIGTERM loses them identically on ECS, but there the restart is slower, the logs are further away, and the failure looks like an infrastructure problem. Proving resilience locally means that when something does break in M14.5, infrastructure is the only remaining suspect — and in the meantime the platform smoke test keeps that proof current.

**User-visible outcome:** None directly. The internal outcome is that "it works on my machine" stops being a meaningful distinction — the thing that runs locally is the thing that will run in production.

**Definition of Done:**
- [ ] Demo Checklist passes in full
- [ ] Secrets sourced from environment with a documented local mechanism that shares no values with production
- [ ] Migration runner documented as a release step, not a service behaviour
- [ ] `ADR-0022` updated with the container topology as built (there is no `13-deployment.md`; 13 is Integrations, and deployment topology is ADR-0022's subject)
- [ ] Disaster Recovery Validation passes for all four components
- [ ] **`signora_platform/` declared frozen** (CLAUDE.md §20a) — subsequent milestones change it only for security fixes, production defects, or approved architectural changes
- [ ] AC-3A passed

**Rollback strategy:**
- **Application:** image tags are immutable and versioned; rollback is running the previous tag.
- **Migrations:** reversible (CI-enforced). Expand-then-contract is adopted here, before cloud deployment makes it expensive to learn.
- **Blast radius:** local only. That is the point of doing it first.

**Operational readiness checklist:**
- [ ] Runbook: bring the stack up, tear it down, reset to clean state
- [ ] Documented: which identity runs which process, and why
- [ ] Container logs are structured JSON carrying `workspace_id` / `correlation_id`
- [ ] Image build is reproducible and pinned

---

### 🆕 M1.4 — Platform Smoke Test · **the platform foundation completion gate**

**Scope:** One command that verifies the complete local production stack — startup, authentication, JWT verification, Casbin authorization, PostgreSQL RLS, Redis, event bus, relay, workers, Security Invariants, demo flow, health, and readiness — wired into CI and required before every milestone and every release.

**Effort:** ~1.5 ew · **Tasks:** T24

**Simulator requirement:** ❌ Not required — M2.0 extends this command rather than replacing it.

**Why this closes the foundation.** Verification is currently spread across a backend suite, a frontend suite, a cross-tier contract test, a disaster-recovery script, and a checklist a human reads. Each is individually green while the *composition* goes unverified — which is exactly where M1.2's credential defect and all four of M1.3A's defects lived. Every one of those was invisible to a passing test suite and obvious within seconds of running the real stack.

With cloud infrastructure deferred to M14.5, this command also becomes the standing proof that the Infrastructure Contract (§5a) still holds. It is the only thing that will notice, across ~200 ew of pipeline work, that the application has stopped being deployable.

**The command:**

```
make smoke
```

**Stages, in order. Each fails fast and names itself:**

| # | Stage | Verifies |
|---|---|---|
| 1 | **Build** | Both production images build from a clean checkout with no local toolchain |
| 2 | **Startup** | Every container reaches healthy; the stack comes up from one command |
| 3 | **Migrations** | Applied under the migration identity as a discrete step; schema at `head`; runner refuses a runtime identity |
| 4 | **Identities** | API/worker are `signora_app`, relay is `signora_relay`, frontend is `signora_auth`, none is the owner — read from inside the containers |
| 5 | **Image hygiene** | No secret-bearing layer, no build toolchain, no `.env`, non-root |
| 6 | **Health** | `/health` green with the database stopped — liveness must not depend on dependencies |
| 7 | **Readiness** | `/ready` **503s** when a dependency is down and returns to 200 on recovery, without intervention |
| 8 | **Authentication** | A token minted by the real frontend issuance path is accepted by the real API |
| 9 | **JWT verification** | `alg:none`, algorithm confusion, a foreign key, a wrong audience, and an expired token are each rejected against the live API |
| 10 | **Authorization** | Casbin decides: a member may read and may not mutate; policy is evaluated before application code |
| 11 | **RLS / tenant isolation** | A second user gets `404` (never `403`) and an empty list; an unfiltered query returns one workspace |
| 12 | **Redis + event bus** | Events published in the causing transaction reach the queue |
| 13 | **Relay** | Every published event is relayed; per-entity ordering preserved; published = relayed + pending |
| 14 | **Workers** | The event is consumed exactly once; a redelivery does not double-process |
| 15 | **Security Invariants** | The full suite passes against the running stack — **last, because it truncates** |
| 16 | **Teardown** | Stack down; no orphaned containers or volumes |

**Demo scenario:**
> *"One command, one answer."* Run `make smoke` on a clean machine. It builds, starts, migrates, verifies every layer, exercises the demo flow, breaks a dependency and watches recovery, runs the invariants, and tears down — exiting non-zero on the first failed guarantee with a message naming which one.

**Demo checklist:**
- [ ] Single command; no prerequisite beyond Docker and Node
- [ ] Green from a clean checkout
- [ ] Exits non-zero and names the failed stage on any failure
- [ ] **Every stage proven to fail when deliberately broken** — an unverified stage may assert nothing
- [ ] Runs in CI on every merge to `main`
- [ ] Documented as required before every milestone and every release
- [ ] Completes in under 10 minutes — beyond that it stops being run
- [ ] Destructive stages cannot run against a database that has not opted in

**User-visible outcome:** None. The outcome is that "is the platform working?" has one answer instead of six partial ones.

**Definition of Done:**
- [ ] Demo Checklist passes in full
- [ ] Wired into CI and documented as a release gate
- [ ] Each stage's failure mode verified by deliberately breaking it
- [ ] `ADR-0022` documents the command
- [ ] AC-3C passed

**Rollback strategy:** Not applicable — additive, ships no runtime change.

**Operational readiness checklist:**
- [ ] Runbook: interpreting each stage's failure
- [ ] Documented as the first step of incident triage
- [ ] Extended by every subsequent milestone (AC-13)

---

### 🆕 M1.5 — Frontend Foundation

**Scope:** The frontend *platform*, not business features. Next.js application shell · layout system · navigation · authentication integration · workspace selector · design system · shared UI components · theme · routing · API client · TanStack Query · error boundaries · loading states · empty states · toast notifications · permission-aware routing · global state management · session management.

**Effort:** ~14.5 ew · **Tasks:** T25–T33

**Simulator requirement:** ❌ Not required — and that is the point. This milestone must be buildable with no business data at all.

**Explicitly out of scope.** No dashboard, companies page, opportunities page, timeline, signals, AI chat, recommendations, or analytics. **No mock business data.** Where a screen would show domain content, it shows an empty state — a real one, designed and shipped, not a placeholder to be replaced.

**Why business screens wait for M2.0.** A page built against hand-written JSON encodes a shape the domain does not have. The mock becomes the contract, the real model arrives, and the page is rewritten — twice the work, and the first version silently teaches everyone the wrong model. Business screens are built once, against real domain models produced by the Provider Simulation Framework.

**Why empty states are a deliverable, not a placeholder.** Every screen in this product will spend its first minutes empty for every new customer, and some will stay empty for accounts with no signal. An empty state designed at the end is an apology; designed now, it is the onboarding path.

**Demo scenario:**
> *"The application exists, and it has nothing to show you."* Sign in with Google. Land on a shell with working navigation, a workspace selector listing real workspaces from the real API, and a theme toggle that persists. Every section renders its empty state. Create a second workspace and switch to it — the whole shell re-scopes. Kill the API and watch error boundaries catch it and offer a retry rather than a white screen. Navigate to a route the caller's role does not permit and be redirected, not shown a forbidden page. Sign out.

**Demo checklist:**
- [ ] Sign in → shell → sign out, end to end against the real API
- [ ] Workspace selector lists real workspaces and switching re-scopes every query
- [ ] Design system: tokens, theme, dark mode, all documented in one place
- [ ] Shared components render in isolation with no application context
- [ ] TanStack Query: caching, invalidation on workspace switch, refetch on reconnect
- [ ] Token refresh happens transparently — a 15-minute session never interrupts a user
- [ ] Error boundary catches a thrown render error and offers retry, never a white screen
- [ ] A failed API call surfaces the error envelope's `correlation_id` to the user, so a support conversation can find the request
- [ ] Loading states on every async boundary; no layout shift on resolve
- [ ] Empty states on every section, designed rather than "No data"
- [ ] Toasts for success, error, and in-flight actions
- [ ] Permission-aware routing: a non-permitted route redirects, never renders-then-hides
- [ ] Component tests running in CI — **repays the `@vitejs/plugin-react` debt**
- [ ] `make smoke` still passes
- [ ] **No mock business data anywhere in the codebase** — asserted, not assumed

**User-visible outcome:** A real, signed-in application with working navigation and an honest empty state everywhere. Not demonstrable to a customer as *product*, but it is the first thing that looks and behaves like software rather than an API.

**Definition of Done:**
- [ ] Demo Checklist passes in full
- [ ] Every subsequent business screen can be added without touching shell, routing, auth, or query infrastructure
- [ ] Design system documented; no component invented ad hoc in a page
- [ ] `@vitejs/plugin-react` reinstated and component tests running (PROJECT_STATUS technical debt register)
- [ ] Frontend coverage gate established in CI
- [ ] AC-14 passed

**Rollback strategy:** Frontend-only; no schema change, no event contract change. Rollback is the previous image tag. Blast radius is the web tier alone — the API and workers are unaffected.

**Operational readiness checklist:**
- [ ] Frontend errors reach Sentry with `correlation_id` attached
- [ ] Client-side route and query failures are observable, not silent
- [ ] Bundle size measured and a budget recorded, before it is a problem
- [ ] Frontend health endpoint still covers auth, keys, and OAuth configuration

---

### 🆕 M2.0 — Provider Simulation Framework

**Scope:** Provider Port (first concrete implementation) · simulation framework (datasets, scenario engine, virtual clock) · realistic payload generation for 5 providers · fault/timing/duplicate injection · sync-mode simulation · 10 demo scenarios · deterministic AI-regression foundation.

**Effort:** ~17–24 ew · Design in **§8**

**Simulator requirement:** ✅ **This milestone builds it.**

**Demo scenario:**
> *"A company, simulated end to end — with the network cable pulled."* Select Scenario 1 (High-Growth SaaS). The simulator emits realistic Apollo, CoreSignal, BuiltWith, and Similarweb payloads through the **same ingestion path production uses**. Show raw payloads landing with full provenance. Re-run the identical scenario: byte-identical results — **deterministic**. Inject a provider timeout, a duplicate delivery, and a delayed update; show each handled correctly. Then flip a single configuration value to switch a provider from simulated to production and show **no code changed**.

**Demo checklist:**
- [ ] Scenario 1 runs end to end with **network egress blocked**
- [ ] Raw payloads for all 5 providers land with full provenance
- [ ] Payload shapes validated against each vendor's documented response format
- [ ] Same scenario + seed re-run → **byte-identical output** (diff shows nothing)
- [ ] Re-run on a different machine → still byte-identical
- [ ] Provider timeout injected → adapter surfaces a transient failure, retries
- [ ] Duplicate delivery injected → downstream unaffected
- [ ] Delayed/out-of-order update injected → handled correctly
- [ ] Full-snapshot and incremental-sync modes both exercised
- [ ] Simulated webhook delivery exercised
- [ ] **Config-only switch** between simulated and production adapter demonstrated; `git diff` shows no code change
- [ ] Ingestion logs unambiguously mark payloads as simulated
- [ ] **Simulator refuses to start with `environment=production`** (guard demonstrated live)
- [ ] All 10 scenarios listed and runnable
- [ ] Timing control demonstrated: instant, real-time, accelerated

**User-visible outcome:** **None for customers.** Substantial internally — every subsequent milestone becomes demonstrable, testable, and developable offline.

**Definition of Done:**
- [ ] Demo Checklist passes in full
- [ ] **Simulated adapters implement exactly the same Provider Port contract as production adapters** — identical signatures, identical return types, identical error semantics
- [ ] Adapter selection is **configuration only** — zero `if simulated:` branching in any layer
- [ ] Production safety guard test-enforced
- [ ] Datasets versioned; a dataset change is a reviewable diff
- [ ] Regression dataset structure supports **incremental extension** (see §8 Progressive Assertion)
- [ ] New architecture document `20-provider-simulation.md` + ADR
- [ ] AC-4 passed

**Rollback strategy:**
- **Code:** additive platform code. Disabling is a configuration change; no production path depends on it.
- **Accidental production activation:** mitigated by the environment guard — the single most important control in this milestone. A simulator silently active in production would fabricate customer intelligence, which is a trust failure rather than a bug.
- **Datasets:** versioned and immutable once published. A bad dataset is superseded by a new version, never edited in place — otherwise historical regression comparisons become meaningless.
- **Blast radius:** nil in production if the guard holds; total for development and demos if it breaks.

**Operational readiness checklist:**
- [ ] Simulator state (active/inactive, scenario, seed) exposed in non-production health output
- [ ] Logs unambiguously mark simulated payloads — an engineer must never mistake simulated data for real
- [ ] Alert: simulator active in any environment where it should not be
- [ ] Documented procedure: adding a new provider simulation
- [ ] Documented procedure: authoring a new scenario
- [ ] Documented procedure: extending a scenario's assertions at a later milestone
- [ ] Dataset provenance recorded (source, generation date, version)

---

### M2.1 — Provider Platform & Normalization

**Scope:** Provider Platform (registry, credentials, quotas, scheduling, health, circuit breaking) · real vendor adapters · Provider Normalization.

**Effort:** ~14–20 ew · **Simulator requirement:** ✅ Required — CI and integration tests run entirely simulated; real vendor calls only in a manually-triggered contract suite.

**Demo scenario:** Add a target account list. Watch ingestion populate raw records with provenance across five providers, the same company enriched by three simultaneously, conflicting values recorded rather than silently resolved. Deterministic version simulated; live version against one real provider.

**Demo checklist:**
- [ ] Full ingestion run against simulated providers, deterministic
- [ ] Same run against **one real provider**, proving the adapter contract holds for both
- [ ] Provider quota/rate-limit compliance observed under load
- [ ] Circuit breaker trips on a simulated provider outage and recovers
- [ ] Conflicting values across providers recorded, not silently resolved
- [ ] Per-provider cost tracked and visible
- [ ] Scenario assertions extended to **normalized entities** (§8)

**User-visible outcome:** Minimal — an ingestion status view.

**Definition of Done:** Provider Port **unchanged from M2.0** (proof the abstraction was right) · 5 real adapters · 100% provenance coverage · adding a 6th provider requires zero domain changes · AC-5 passed.

**Rollback strategy:** Per-provider feature flags — a misbehaving adapter is disabled without a deploy. Ingestion is idempotent, so replay after rollback is safe.

**Operational readiness:** Alerts on provider health, quota exhaustion, cost anomaly, ingestion failure rate · runbook for credential rotation and vendor outage.

---

### M3 — Knowledge Graph & Observation Engine

**Effort:** ~17–23 ew · **Simulator requirement:** ✅ Required — entity-resolution evaluation needs labelled, deterministic datasets.

**Demo scenario:** "Acme Corp", "Acme Corporation Inc.", and a differently-named legal entity resolve into one record, with merge history explaining why. Scenario 10 supplies labelled ground truth.

**Demo checklist:**
- [ ] Three variant records resolve to one canonical entity
- [ ] Merge history shows the reasoning
- [ ] An incorrect merge is reversed successfully
- [ ] Precision >95%, recall >90% reported against the labelled set
- [ ] Observations recorded with unbroken provenance to source payloads
- [ ] Scenario assertions extended to **observations and resolved entities** (§8)

**User-visible outcome:** One canonical company record per entity, visible in a basic entity view.

**Definition of Done:** Labelled evaluation set (≥1,000 pairs) · duplicate rate <2% · merges auditable and reversible · embeddings workspace-scoped and RLS-enforced · AC-6 passed.

**Rollback strategy:** Merges reversible by design; a bad resolution model is reverted and entities re-resolved from observations, which are immutable.

**Operational readiness:** Alerts on merge-rate anomaly and resolution latency · runbook for reversing an incorrect merge.

---

### M4–M15

Full Demo Checklist, Definition of Done, rollback, and readiness sections are authored **at each milestone's planning boundary**, when the preceding milestone's learnings are available. Planning distant milestones in near-milestone detail produces false precision. Scope, effort, and simulator requirements are fixed now:

| Milestone | Scope | Effort | Simulator | Scenario assertions added |
|---|---|---|---|---|
| **M4** | Business Event Engine | 10–14 ew | ✅ Required | Business Events |
| **M5** | Signal Engine + Buying Score Engine | 14–22 ew | ✅ Required | Signals, Buying Scores |
| **M6** | Opportunity Engine | 5–7 ew | ✅ Required | Opportunities |
| **M7** | Timeline | 6–8 ew | ✅ Required | Timeline entries |
| **M8** | AI Platform + Prompt Registry + **Eval Harness** | 15–20 ew | ✅ **Critical** | Golden sets seeded from scenarios |
| **M9** | AI Reasoning Engine | 8–12 ew | ✅ Critical | Reasoning output, **confidence scores** |
| **M10** | AI Research Engine | 12–16 ew | ✅ Critical | Research artifacts |
| **M11** | Recommendation Engine | 6–8 ew | ✅ Required | **Recommendations** |
| **M12** | Revenue Intelligence Platform + business screens | 24–35 ew | ✅ Required | Composed views |
| **M13** | CRM / comms / calendar integrations | 18–26 ew | ⚠️ Partial | — |
| **M14** | Billing, notifications, analytics, flags | 5–7 ew | ❌ Not required | — |
| **M14.5** | **Cloud Infrastructure** *(deferred from M1.3B — see below)* | 6 ew | ❌ Not required | — |
| **M15** | GA readiness: load testing, SOC 2, PII, spend governance | 20–27 ew | ✅ Load testing at volume | — |

---

### ⏸ M14.5 — Cloud Infrastructure · *deferred from M1.3B*

> **Sequencing change only.** Scope, technology, and topology are exactly as ratified in [ADR-0022](docs/architecture/adr/0022-devops-infrastructure-and-deployment-topology.md) and as originally planned for M1.3B. Nothing here has been removed or redesigned — only its position in the order. Runs immediately before M15 GA readiness, which depends on a deployed environment for load testing at volume.
>
> Until this milestone, the application stays deployable by the Infrastructure Contract (§5a) rather than by a deployed environment proving it.

**Scope — retained in full, technology for technology:** **Terraform** (VPC, **RDS** PostgreSQL 17, two **ElastiCache** clusters, **Secrets Manager**) · **ECS** services · ALB with TLS · **GitHub deployment pipeline** · staging · automated migrations · **rollback automation** and validation · **cloud monitoring dashboards** · Auto Scaling.

No technology is substituted and nothing is dropped. If any of these needs to change, that is a new ADR, not a consequence of the deferral.

**Effort:** ~6 ew · **Critical path:** T22→T23 = 6 ew serial · **Tasks:** T22–T23 (**IDs retained from M1.3B so the deferral stays traceable**)

**Simulator requirement:** ❌ Not required.

**Entry condition:** M14 complete, and M1.3A's local production stack still green. Every question this milestone asks is about AWS configuration, because the application-level questions were answered at M1.3A — roughly 200 ew earlier, and kept answered since by §5a and the platform smoke test.

**Demo scenario:**
> *"Ship it and un-ship it."* Merge to `main`; the pipeline runs migrations as a privileged pre-deploy task, deploys API and workers, and passes health/readiness. Then deliberately deploy a broken build, watch readiness fail, and **roll back using the documented procedure — timed.** Show `signora_app` connecting as a non-superuser in the deployed environment, and secrets resolving from Secrets Manager with none present in the image.

**Demo checklist:**
- [ ] `terraform plan` clean and idempotent on a second run
- [ ] Staging provisioned end to end from code
- [ ] Pipeline deploys API + at least one worker pool
- [ ] Migration task runs pre-deploy under the **migration identity**, never from a service
- [ ] `/health` and `/ready` green post-deploy
- [ ] Application connects as `signora_app`, frontend as `signora_auth` — verified in the deployed environment
- [ ] Two separate ElastiCache clusters confirmed (queue vs. cache)
- [ ] Secrets resolve from Secrets Manager; image inspection shows none embedded
- [ ] TLS terminated; HTTP redirects to HTTPS
- [ ] **Broken build deployed, rollback executed and timed (<10 min)**
- [ ] RDS backup restore performed once into a scratch instance
- [ ] Security Invariants suite passes against the deployed staging environment — against a **disposable** database, never one holding data (the suite truncates; it requires `SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1`)
- [ ] `make smoke` passes against the deployed environment
- [ ] Production monitoring dashboards live
- [ ] Auto Scaling configured and a scale event observed

**User-visible outcome:** None directly — but this is what makes M1.2's login reachable by anyone outside a developer's laptop.

**Definition of Done:**
- [ ] Demo Checklist passes in full
- [ ] All secrets from AWS Secrets Manager
- [ ] **Expand-then-contract migration rule enforced** — no deploy ships a destructive schema change alongside the code depending on it
- [ ] `ADR-0022` updated with as-built topology
- [ ] AC-3B passed

**Rollback strategy:**
- **Application:** ECS retains the previous task definition; rollback is a revision revert. Target **under 10 minutes, verified**.
- **Migrations:** all reversible (CI-enforced). Expand-then-contract keeps application rollback safe without a database restore.
- **Infrastructure:** Terraform state versioned; `plan` reviewed before every apply.
- **Blast radius:** total. This is where rollback discipline stops being theoretical.

**Operational readiness checklist:**
- [ ] Runbook: deploy · rollback · emergency stop
- [ ] Runbook: database restore, tested
- [ ] Alert: ECS service unhealthy / task flapping
- [ ] Alert: RDS CPU, connections, storage headroom
- [ ] Alert: ElastiCache memory and eviction (both clusters)
- [ ] Pipeline requires green CI to proceed
- [ ] On-call rotation and escalation defined
- [ ] Staging is a faithful shape of production

---

---

## 7. M1 Task Breakdown

### M1.1 — Platform Runtime

| ID | Task | Complexity | Depends on |
|---|---|---|---|
| T1 | Coverage measurement + CI gate | XS · 0.25 ew | — |
| T2 | Redis service in CI | XS · 0.25 ew | — |
| T3 | Structured logging foundation | M · 1.5 ew | — |
| T4 | OpenTelemetry tracing | M · 2 ew | T3 |
| T5 | Sentry error tracking | S · 0.5 ew | T3 |
| T6 | Event bus schema (`dead_letter_event`, `processed_event`, outbox columns) | S–M · 1 ew | — |
| T7 | Outbox relay process 🔴 | L · 3 ew | T2, T6 |
| T8 | Subscription registry, dispatch, platform-owned idempotency 🔴 | L · 3 ew | T6, T7 |
| T9 | ARQ worker entry points + per-stage pools | M · 1.5 ew | T8 |
| T10 | Retry policy + dead-lettering | M · 1.5 ew | T8, T9 |
| T11 | Pipeline observability metrics | S–M · 1 ew | T4, T7–T10 |

**Sequential order:** T1 → T2 → T6 → T3 → T7 → T8 → T9 → T10 → T4 → T5 → T11

Rationale: cheap unblocking work first (T1, T2, T6); logging (T3) before the relay so the relay is debuggable as it is built; then the critical chain; then remaining observability, which benefits from having real traffic to instrument.

### M1.2 — Authentication Boundary

| ID | Task | Complexity | Depends on |
|---|---|---|---|
| T12 | Next.js 15 scaffold + tooling | M · 1.5 ew | — |
| T13 | Better Auth + Google/Microsoft OAuth 🔴 | L · 3 ew | T12 |
| T14 | RS256 JWT issuance per ADR-0026 🔴 | M · 1.5 ew | T13 |
| T15 | Signing-key management | S–M · 1 ew | T14 |
| T16 | Typed API client | M · 1.5 ew | T12 |
| T17 | Frontend shell | M · 2 ew | T13, T16 |
| T18 | E2E auth journey | M · 1 ew | T15, T17 |

**Sequential order:** T12 → T13 → T14 → T15 → T16 → T17 → T18

### M1.3A — Deployment Foundation

| ID | Task | Complexity | Depends on |
|---|---|---|---|
| T19 | Production Docker images (API, worker, frontend) | M · 1.5 ew | — |
| T20 | Migration runner + secrets management | M · 1.5 ew | T19 |
| T21 | Production Compose stack + health/readiness wiring | M · 1 ew | T19, T20 |
| T21b | Disaster Recovery Validation (restart Postgres, Redis, API, workers) | M · 1.5 ew | T21 |

**Sequential order:** T19 → T20 → T21 → T21b

### M14.5 — Cloud Infrastructure *(deferred from M1.3B)*

| ID | Task | Complexity | Depends on |
|---|---|---|---|
| T22 | Terraform baseline (VPC, RDS, 2× ElastiCache, Secrets Manager) | L · 3 ew | T21 |
| T23 | ECS + deploy pipeline + rollback validation + dashboards + Auto Scaling | L · 3 ew | T22, T9 |

**Sequential order:** T22 → T23. Task IDs retained so the deferral is traceable rather than looking like new work.

### M1.4 — Platform Smoke Test

| ID | Task | Complexity | Depends on |
|---|---|---|---|
| T24 | Single-command platform verification, wired into CI | M · 1.5 ew | T21 |

**Depends on M1.3A, not M1.3B:** the command must run against the local production stack, so it is available as a gate *before* cloud deployment rather than after.

### M1.5 — Frontend Foundation

| ID | Task | Complexity | Depends on |
|---|---|---|---|
| T25 | Design system: tokens, theme, dark mode, Tailwind configuration | M · 1.5 ew | — |
| T26 | Shared UI component library (button, input, select, dialog, table, badge, skeleton, empty state) | L · 2.5 ew | T25 |
| T27 | Application shell: layout, navigation, responsive frame | M · 1.5 ew | T26 |
| T28 | TanStack Query integration + typed API client wiring | M · 1.5 ew | — |
| T29 | Session management, auth integration, workspace selector | M · 2 ew | T27, T28 |
| T30 | Permission-aware routing | M · 1.5 ew | T29 |
| T31 | Error boundaries, loading states, empty states, toasts | M · 1.5 ew | T26, T28 |
| T32 | Global state management (theme, active workspace, UI preferences) | S · 1 ew | T29 |
| T33 | Frontend testing foundation + component tests in CI | M · 1.5 ew | T26 |

**Sequential order:** T25 → T26 → T28 → T27 → T29 → T30 → T31 → T32 → T33

Rationale: the design system before components, because a component built before its tokens hardcodes them. T28 before T27 so the shell is wired to real data from its first render rather than retrofitted. T33 last, when there are components worth testing — and it is the scheduled repayment point for the `@vitejs/plugin-react` debt, which is a *prerequisite* of component testing rather than a follow-up to it.

**Critical path:** ~14.5 ew serial. The design system (T25→T26) is the long pole; T28 and T33 are the only tasks that parallelise cleanly if a second engineer is available.

---

## 8. Provider Simulation Framework — Design

> Full specification authored as `docs/architecture/20-provider-simulation.md` with an accompanying ADR during M2.0. This section fixes design intent.

### Status: permanent platform capability

The simulator is **not development-only tooling**. It is held to production standards — reviewed, typed, tested, boundary-enforced — and serves eight ongoing purposes:

| Purpose | Why it needs the simulator |
|---|---|
| **Local development** | Full pipeline runs offline, with no vendor account or cost |
| **Integration testing** | CI must never depend on third-party availability, rate limits, or spend |
| **End-to-end testing** | Deterministic full-pipeline runs |
| **Product demonstrations** | A demo depending on a live vendor is a demo that fails in front of a customer |
| **AI evaluation** | Identical inputs → comparable outputs across model and prompt versions |
| **Regression testing** | Scenarios become the pipeline's end-to-end regression suite |
| **Performance benchmarking** | Reproducible load at controlled volume and rate |
| **Customer onboarding demos** | A prospect sees a realistic account journey without their data being ingested first |

### The identical-contract rule

**Every simulated provider implements exactly the same adapter contract as a production provider** — identical method signatures, identical return types, identical error semantics, identical retry and rate-limit behaviour surface.

Consequences, all binding:

- Switching between simulated and production providers is **configuration only**
- **No `if simulated:` branching** may exist in any layer — domain, application, infrastructure, or interface
- The ingestion pipeline is **byte-identical** in both modes
- A simulated adapter that cannot satisfy the real contract is a defect in the *contract*, not a licence to special-case the simulator

This rule is what makes the simulator trustworthy for demos and regression: if the simulated path diverged from production, everything it proved would be worthless.

### Architectural placement

**The simulator enters at the Provider layer and nowhere else.**

```
Simulated Provider Adapter  ─┐
                             ├─→ Provider Port ─→ Provider Platform ─→ Provider Normalization
Real Provider Adapter       ─┘                          ↓
                                                  Knowledge Graph → Observation Engine
                                                        ↓
                                          Business Event Engine → Signal Engine
                                                        ↓
                                        Buying Score → Opportunity Engine
                                                        ↓
                                      AI Research / AI Reasoning → Recommendations
```

**No stage after Provider may be entered directly.** Injecting a synthetic observation or a pre-built signal would exercise a path production never takes and produce demos that prove nothing.

### Codebase placement

| Component | Location | Rationale |
|---|---|---|
| Simulation framework (datasets, scenario engine, clock, fault injection) | `signora_platform/simulation/` | Shared technical infrastructure; no module dependency — satisfies the `signora_platform` → `modules` prohibition |
| Simulated provider adapters | `modules/provider_platform/infrastructure/adapters/simulated/` | Adapters belong with adapters; `modules` → `platform` is the allowed direction |
| Scenario & dataset definitions | `signora_platform/simulation/datasets/`, `scenarios/` | Versioned, reviewable, diffable |

**The simulator is the first implementation of the Provider Port** — satisfying the YAGNI ruling and validating the port with working code before any vendor adapter is written or contract signed.

### Capabilities

| Capability | Detail |
|---|---|
| Load predefined datasets | Versioned company/people/technographic/traffic fixtures with stable identifiers |
| Generate realistic payloads | Per-vendor response shapes matching documented formats |
| Replay historical events | Ordered timelines against a virtual clock |
| Control event timing | Instant · real-time · accelerated |
| Simulate provider failures | Timeout · 5xx · rate limit · malformed payload · partial response |
| Simulate delayed updates | Late-arriving, out-of-order relative to `occurred_at` |
| Simulate duplicate events | Same payload delivered N times — exercises idempotency for real |
| Simulate webhook deliveries | Inbound webhook path, including replayed and out-of-order |
| Simulate incremental syncs | Delta-only payloads since a watermark |
| Simulate full snapshots | Complete re-sync, exercising dedup and merge |

### Determinism contract

Given the same **dataset version + scenario + seed**, the simulator produces byte-identical payloads on every run and every machine. All randomness is seeded; no wall-clock or ambient state leaks into generation. This is an acceptance criterion, not an aspiration — without it, AI regression over time is anecdote rather than measurement.

### Demo scenario library

| # | Scenario | Primary signal exercised |
|---|---|---|
| 1 | High-growth SaaS company | Composite growth: headcount, traffic, funding |
| 2 | Hiring surge | Job-posting velocity in a specific function |
| 3 | Technology migration | Technographic change — incumbent displacement |
| 4 | Executive change | Leadership hire in a buying-relevant role |
| 5 | Funding announcement | Capital event, budget-availability inference |
| 6 | Website traffic spike | Engagement inflection |
| 7 | Buying intent increase | Multi-source intent correlation |
| 8 | New office expansion | Geographic expansion |
| 9 | Competitor displacement | Technographic + hiring + content combined |
| 10 | Company becomes an ideal ICP match | Firmographic drift into ICP over time |

### Progressive assertion — the AI regression foundation

**Scenario assertions extend at each milestone; regression datasets are never recreated.** A scenario authored in M2.0 accumulates assertion layers as the pipeline is built, so by M11 each of the ten scenarios is a full end-to-end regression test.

| Milestone | Assertion layer added | Cumulative depth |
|---|---|---|
| **M2.0** | Raw provider payloads | Payloads |
| **M2.1** | Normalized entities | + Normalization |
| **M3** | Observations, resolved graph entities | + Substrate |
| **M4** | Business Events | + Interpretation |
| **M5** | Signals, Buying Scores | + Scoring |
| **M6** | Opportunities | + Qualification |
| **M9** | AI reasoning output, **confidence scores** | + Reasoning |
| **M11** | Recommendations | **Full pipeline** |

**Rules governing this evolution:**

1. **Extend, never recreate.** A dataset is versioned and added to. Regenerating a dataset invalidates every historical comparison built on it, which defeats the purpose of regression testing.
2. **Assertions are additive.** Adding an M4 assertion must not require rewriting M2.0's payload assertions.
3. **Dataset versions are immutable once published.** A correction ships as a new version, with the change reviewable as a diff.
4. **Every AI evaluation run records dataset version, model version, and prompt version** — so a quality change is attributable to exactly one of them.
5. **Confidence scores are asserted as ranges, not exact values.** Asserting an exact float would make the suite brittle against justified model changes; asserting calibration bands catches real regressions without punishing improvement.

**Estimated saving:** M8's evaluation harness inherits these datasets and expected outcomes, dropping from 6–8 ew to ~4–6 ew. Part of M2.0's cost is repaid directly.

### Safety

**The highest-risk control in this milestone.** A simulator active in production would fabricate customer intelligence — a trust failure, not a bug.

- Environment guard: refuses activation when `environment == "production"` absent an explicit, logged override
- Ingestion logs unambiguously mark simulated payloads
- Simulator state exposed in non-production health output
- Alert if active anywhere it should not be

All four are test-enforced, not conventions.

---

## 9. Parallel Workstreams — *retained for future scaling*

> **Not the current operating model.** §1 governs: implementation proceeds as a single prioritized stream. This section is preserved for the moment staffing increases, and should be re-read then.

| Stream | Scope | Staffing | Runs |
|---|---|---|---|
| **A — Pipeline** | M2.1 → M11 (critical path) | 2–3 eng | From M2.0 completion |
| **B — AI Platform** | M8, then M9/M10 support | 1–2 eng | From M4 |
| **C — Product Surface** | M1.2, then M7/M12 frontend | 1–2 eng + design | Continuous |
| **D — Platform & Ops** | M1.1, M1.3A, M1.4, M14.5, M15 | 1 eng | Continuous |
| **E — Simulation** | M2.0, then scenario extension per milestone | 1 eng, then ~0.5 | M2.0 onward |

**When staffing allows:** M1.1, M1.2, and M1.3A have no interdependencies, so they parallelise almost perfectly — the fastest available compression of the M1 phase.

**Stream E never ends.** Each milestone extends the scenario library with its own assertions (~0.5 ew per milestone). This is what keeps the library current rather than rotting into stale fixtures.

---

## 10. Architecture Checkpoints

| Checkpoint | When | Verifies |
|---|---|---|
| **AC-1 — Event Bus Contract** | M1.1 | At-least-once delivery; platform-owned idempotency; DLQ; `correlation_id` traced end-to-end |
| **AC-2 — Auth Boundary Integrity** | M1.2 | No private key in Python tier; claims match contract exactly; contract test green |
| **AC-3A — Application Deployability** | M1.3A | Stack starts from production images alone; migrations run under the migration identity; each tier connects under its own least-privileged role; readiness distinguishes liveness from dependency failure; **restarting any component loses no queued events, pending work, tenant isolation, or per-entity ordering** |
| **AC-3B — Deployment & Rollback** | M14.5 | Rollback executed and timed; expand-then-contract migrations; non-superuser connection in a deployed environment |
| **AC-3C — Platform Verification** | M1.4 | One command verifies the whole platform; every stage proven to fail loudly when deliberately broken |
| **AC-4 — Simulator Fidelity** | M2.0 | Identical adapter contract; config-only switching; enters only at Provider layer; determinism proven; production guard test-enforced |
| **AC-5 — Provider Abstraction Integrity** | M2.1 | Provider Port unchanged from M2.0; no vendor SDK type outside an adapter |
| **AC-6 — Tenancy Under Load** | M3 | Every new table: `workspace_id`, forced RLS, `SECURITY DEFINER` predicates, `WHERE`-less query test, both session shapes |
| **AC-7 — Evidence Chain Integrity** | M6 | Every signal/score/opportunity traces to source observations |
| **AC-8 — AI Abstraction & Safety** | M9 | No vendor SDK in domain/application; output validated before trust; prompt versions recorded |
| **AC-9 — AI Evaluation Gate** | M8 | Golden sets exist; regression CI-enforced; evidence-completeness a release gate |
| **AC-10 — Module Boundary Audit** | Every milestone | import-linter contracts extended and **proven to fail** on a deliberate violation |
| **AC-14 — Frontend Foundation Integrity** | M1.5 | Every business screen addable without touching shell, routing, auth, or query infrastructure; **no mock business data in the codebase**; component tests in CI |
| **AC-13 — Security Invariants** | Every milestone | The suite is extended with the milestone's new guarantees, and every added invariant is **proven to fail** when its guarantee is deliberately removed |
| **AC-11 — Scale Validation** | M15 | RLS, Meilisearch, pgvector load-tested at target scale using simulator-generated volume |
| **AC-12 — Security & Compliance** | M15 | Least privilege verified; PII policy implemented; SOC 2 evidence collectable |

---

## 11. Acceptance Criteria (per module)

- [ ] Five Clean Architecture layers, correctly directed
- [ ] `public/` contract exported; no module imports past it
- [ ] import-linter contract added **and demonstrated to fail** on a deliberate violation
- [ ] Every workspace-owned table: `workspace_id`, `created_at`, `updated_at`, `created_by`, `updated_by`, forced RLS, granted to `signora_app`, **in the same migration**
- [ ] Integration test with a `WHERE`-less query asserting only current-workspace rows return
- [ ] Both session shapes tested
- [ ] Published events match [06-events.md](docs/architecture/06-events.md); **idempotency is platform-provided — modules must not implement their own**
- [ ] Domain errors mapped centrally; no `HTTPException` in domain/application
- [ ] Endpoints follow [19-api-conventions.md](docs/architecture/19-api-conventions.md)
- [ ] mypy `strict` clean; ruff clean
- [ ] Unit tests use fakes; integration tests use real PostgreSQL as `signora_app`
- [ ] Failure paths tested
- [ ] **Scenario assertions extended** with this module's layer (from M2.0 onward)
- [ ] Architecture docs updated in the same PR

---

## 12. Definition of Done (global)

A milestone is done when **every** statement holds:

1. **Functionally complete** — all acceptance criteria met.
2. **Demo Checklist passed** — every item verified live. **A milestone is not complete until its Demo Checklist passes.**
3. **Architecturally verified** — the milestone's checkpoint has formally passed.
4. **Tested** — unit, integration, failure paths; suite green; coverage measured and not regressed.
5. **Observable** — every async flow traceable via `correlation_id`, emitting latency/throughput/error metrics.
6. **Secure** — tenant isolation proven by test; no secrets in code; least privilege verified.
7. **Documented** — architecture documents updated in the same change; new ADR for any new technology or vendor.
8. **Deployable** — starts from a production image under its own least-privileged identity, satisfies the Infrastructure Contract (§5a) at all times, and runs in a deployed environment from M14.5.
9. **Demonstrable** — the Demo Scenario runs successfully, **using simulated provider data wherever live integrations are unavailable**.
10. **Reversible** — rollback strategy documented and, for infrastructure milestones, executed at least once.
11. **Operationally ready** — readiness checklist complete: runbooks, alerts, dashboards.
12. **Regression-extended** — scenario assertions extended for this milestone's pipeline layer (from M2.0 onward).
13. **No shortcuts** — no TODOs in application code, no placeholders, no mocks, no dead code, no skipped tests.
14. **Risk register current** — [16-architecture-risks.md](docs/architecture/16-architecture-risks.md) updated.
15. **Status updated** — [PROJECT_STATUS.md](PROJECT_STATUS.md) reflects reality.

---

## 13. Immediate Sequence

Single stream. **M1.1 only** — M1.2 does not begin until M1.1's Demo Checklist passes.

| Order | Task | Why here |
|---|---|---|
| 1 | **T1** Coverage + CI gate | 0.25 ew; closes a measurement gap before more code lands |
| 2 | **T2** Redis in CI | 0.25 ew; required before any relay integration test can run |
| 3 | **T6** Event bus schema | Unblocks T7 and T8; small, self-contained |
| 4 | **T3** Structured logging | Before the relay, so the relay is debuggable *as it is built* rather than after |
| 5 | **T7** Outbox relay 🔴 | Start of the critical chain; unblocks all 13 modules |
| 6 | **T8** Dispatch + platform idempotency 🔴 | The contract 13 modules will program against — worth getting right once |
| 7 | **T9** ARQ worker fleet | Makes dispatch runnable |
| 8 | **T10** Retry + DLQ | Completes delivery guarantees |
| 9 | **T4** OpenTelemetry | Now there is real cross-process traffic to trace |
| 10 | **T5** Sentry | Small; completes observability |
| 11 | **T11** Pipeline metrics | Needs T4 and the full relay chain in place |

**Then:** M1.1 Demo Checklist → M1.2 → M1.3A → M1.4 → **M1.5** → M2.0. Cloud infrastructure (M14.5) is deferred to Production Readiness.

**Deferred until staffing allows:** the Knowledge Graph spike. Under single-stream execution it would displace critical-path work; it should run as soon as a second engineer is available, since it retires the roadmap's largest estimation variance.

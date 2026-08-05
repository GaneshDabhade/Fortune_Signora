# Decision Register — every Product Owner decision

> **The permanent record of what has been decided.** Established 2026-08-04, on the product owner's approval of the [Knowledge Continuity Framework](architecture/423-knowledge-continuity-framework.md).
>
> **Human-authored. Never generated.** A ruling is not derivable from the repository — it is a fact about a conversation, and this is the only place it is written down.

## Why this exists

**[`DECISION_PACKS.md`](DECISION_PACKS.md) states its own rule:** *"a **staging area, not a record** — a pack is deleted when its decision is taken, and the answer lives in the ADR or document it produced."*

**That is correct for packs, and it means rulings left no index.** An ADR records an *architectural* decision; **most Product Owner rulings are not ADRs** — a deferral, a partial approval, a scope ruling, an ownership resolution. **Three of the nine rulings on 2026-08-04 were deferrals, which produce no ADR and would otherwise leave no repository trace at all.**

> **A deferral is a decision.** *"Do not force a module boundary until implementation naturally reaches M14b"* binds as firmly as a ratification.

## What a row is, and is not

| | |
|---|---|
| **A row is** | The decision, its date, its status, the modules it affects, and its repository impact |
| **A row is not** | The deliberation. **That lives in the ADR, pack or document the row names** — never here |
| **A row is never deleted** | **Superseded is a status, not a removal.** A decision that was later reversed stays, with the decision that reversed it named |

**Status vocabulary — the five states of `CLAUDE.md` §20e, plus two:**

`APPROVED` · `DEFERRED` · `PARTIALLY APPROVED` · `SUPERSEDED` · `WITHDRAWN` — and for each, whether it is **`MERGED`** to `integration`, because **a decision is authoritative when ruled and actionable when recorded.**

---

## 2026-08-04 — the UI convergence rulings

**Nine items ruled at once, closing the Product Office queue.**

| # | Decision | Status | Merged | Affected | Repository impact |
|---|---|---|---|---|---|
| **D-021** | **[ADR-0400](architecture/adr/0400-person-as-an-entity.md) approved** — *"Person becomes a first-class entity within the approved bounded context. Proceed on that assumption for all future preparation."* | `APPROVED` | `lane-c-sync` | `knowledge_graph` · `observation_engine` · Epic C | **`EntityKind` gains `PERSON`.** Releases People Intelligence, half of Global Search, 4 ICP *Decision makers* criteria, Account 360's contacts and org chart. **Answers [C-221](LANE_COORDINATION.md)** |
| **D-022** | **[C-010](LANE_COORDINATION.md) resolved** — *"Do not create another engineering lane. Lane C's responsibilities are formally expanded to include Platform Foundation work that belongs to no product bounded context."* | `APPROVED` | `lane-c-sync` | `infra/` · `Makefile` · `signora_platform/simulation` | **`CLAUDE.md` §20e amended.** Lane C is rowed on the board for tooling. **Answers [C-021](LANE_COORDINATION.md)**; closes the gap that produced B-007, B-012, B-013, B-014 |
| **D-023** | **[C-326](LANE_COORDINATION.md) — [ADR-0300](architecture/adr/0300-inbound-customer-systems.md) Option A approved**, the sibling source port | `APPROVED` | `lane-c-sync` | `integrations` · `provider_platform` · Epic E1 · E2 | **[409](architecture/409-inbound-source-port-contract.md) is the contract.** [419](architecture/419-c326-narrowed-and-lane-b.md) measures the remaining slice as small — both ends are already built |
| **D-024** | **[ADR-0401](architecture/adr/0401-a-customers-crm-is-not-a-provider.md) approved** — *"Continue using the per-field falsifiability model exactly as documented."* | `APPROVED` | `lane-c-sync` | `provider_normalization` · Epic E1 | Falsifiability is tested **per field**, not per source |
| **D-025** | **[ADR-0402](architecture/adr/0402-a-rule-is-data.md) approved** — *"Epic F is now considered unblocked from a Product Office perspective."* | `APPROVED` | `lane-c-sync` | `workflow` *(new)* · Epic F | A rule is a condition tree, not an expression. **`workflow` publishes one event and calls nothing** |
| **D-026** | **[C-321](LANE_COORDINATION.md)** — *"Accept the documented recommendations as the default product behaviour. Only return to Product Owner if a recommendation materially changes customer-visible behaviour beyond what has already been documented."* | `PARTIALLY APPROVED` | `lane-c-sync` | Epic A · A6 | **A6 unblocked.** The escalation test narrows to *"does this change customer-visible behaviour beyond what the recommendation documents?"* |
| **D-027** | **[ADR-0040](architecture/adr/0040-notifications.md) deferred** — *"Do not ratify yet. Allow the Notification package to complete first, then review ADR-0040 together with the finished package."* | `DEFERRED` | `lane-c-sync` | `notifications` · Epic F phase 5 · Signal Center | **ADR-0402 already ensures Epic F does not wait on it.** Module 7's approved design is far larger than the popover the ADR was written against |
| **D-028** | **O3 — shell services placement deferred** — *"Deferred until implementation reaches the shared shell foundation. No further preparation is required at this stage."* | `DEFERRED` | `lane-c-sync` | App Shell · all 26 screens | **Wave 3 planning stops at the boundary.** Lane C prepares no further |
| **D-029** | **[C-200](LANE_COORDINATION.md) deferred** — *"Continue discovery work. Do not force a module boundary until implementation naturally reaches M14b."* | `DEFERRED` | `lane-c-sync` | M14b · Billing | [42-billing-and-entitlements.md](architecture/42-billing-and-entitlements.md) stays discovery |

## 2026-08-04 — governance and product identity

| # | Decision | Status | Merged | Affected | Repository impact |
|---|---|---|---|---|---|
| **D-030** | **The Fortune Signora Design Project is the authoritative UI specification** — the Product Transition Directive | `APPROVED` | `lane-c-sync` | Every frontend surface | **[410](architecture/410-approved-ui-specification.md)** records it. Lane C stops preparing UI assumptions |
| **D-031** | **Ten platform-foundation modules are final** — Authentication, Onboarding, Workspace Setup, Team Management, User Profile, Security Center, Notifications, Billing, Help, System States | `APPROVED` | `lane-c-sync` | 10 approved screens | **[418](architecture/418-platform-foundation-assessment.md)** assesses them. 26 approved screens total |
| **D-032** | **The module is the planning unit; the screen is a consumer** — Transition Directive Rev 2 | `APPROVED` | `lane-c-sync` | Product Office | **[412](architecture/412-backend-capability-matrix.md)** · [`PRODUCT_OFFICE.md`](PRODUCT_OFFICE.md) §5b |
| **D-033** | **The Standard Lane Report binds every lane** | `APPROVED` | `lane-c-sync` | All four lanes | **`CLAUDE.md` §20e.** Supersedes the Standard Lane Header of 2026-08-03 |
| **D-034** | **The five-state decision lifecycle** — `PREPARED` → `READY FOR PRODUCT OWNER` → `PRODUCT OWNER APPROVED` → `MERGED TO INTEGRATION` → `AVAILABLE FOR IMPLEMENTATION` | `APPROVED` | `lane-c-sync` | All four lanes | **`CLAUDE.md` §20e · [`PRODUCT_OFFICE.md`](PRODUCT_OFFICE.md) §11c.** Raised by Lane A's challenge to a Lane C report |
| **D-035** | **Fortune is the brand; Signora is the product** | `APPROVED` | `lane-c-sync` | Every user-facing string | **`CLAUDE.md` §4.** Prospective, never a rename exercise. **[421](architecture/421-product-naming-inventory.md)**: the inventory is empty |
| **D-036** | **The Portfolio Dashboard and UI Implementation Dashboard are permanent Lane C reporting** | `APPROVED` | `lane-c-sync` | Product Office | [`PRODUCT_OFFICE.md`](PRODUCT_OFFICE.md) §11a, §11b |
| **D-037** | **Environment Management is Environment Framework phase 3, not a new module** | `APPROVED` | `lane-c-sync` | `infra/` | **[420](architecture/420-environment-management-proposal.md).** No new bounded context. **No CI profile** — §20c-2 |
| **D-038** | **Knowledge Continuity Framework approved, five of eight documents refused as duplication** | `APPROVED` | `lane-c-sync` | Repository documentation | **[423](architecture/423-knowledge-continuity-framework.md).** This register is D-038's first output |
| **D-039** | **Synchronization by rebuild, not rebase** — abandon the 57-commit branch, replay only what still has value | `APPROVED` | `lane-c-sync` | Repository | **[422](architecture/422-synchronization-plan.md).** Six commits replace fifty-seven |

## 2026-08-04 — module assignment

| # | Decision | Status | Merged | Affected | Repository impact |
|---|---|---|---|---|---|
| **D-055** | **[C-414](LANE_COORDINATION.md) accepted as a clarification, not a decision.** *"Coordination items belong to the current assignee of the affected module, not to the lane that originally opened or previously owned it."* **C-213 is Lane A's** | `APPROVED` | `lane-c-sync` | `commercial_profile` · TASK-205 | **TASK-205 unblocks itself.** No ownership, boundary, ADR or governance rule changed |
| **D-056** | **Module assignment standardised** — **`commercial_profile` → Lane A**, **`knowledge_graph` → Lane A**. Lane B's implementation ownership becomes `integrations`, `provider_normalization`, CRM integrations, provider connectors, ingestion, normalization and future adapters. **Dual ownership of an implementation module is no longer permitted** | `APPROVED` | `lane-c-sync` | Lane A · Lane B | **Answers [C-415](LANE_COORDINATION.md) and [C-413](LANE_COORDINATION.md).** The authoritative table lives on [`ACTIVE_ASSIGNMENTS.md`](ACTIVE_ASSIGNMENTS.md) |
| **D-057** | **Module assignment is authoritative.** When ownership changes, **coordination items, backlog ownership and implementation responsibility all follow the module; historical authorship does not.** Write **current module assignee**, never **owner**, unless the responsibility is permanent and independent of assignment | `APPROVED` | `lane-c-sync` | All lanes | **`CLAUDE.md` §20e.** *One implementation module → one lane → one current assignee → one source of truth* |
| **D-058** | **Lane A is `PAUSED`; every implementation module consolidates on Lane B.** *"We'll continue with Lane B only for some time and will start Lane A later once this conflict issue gets resolved."* **Seventeen modules to one assignee**, `infra/` unchanged with Lane C. **Supersedes [D-056](#) after seven hours** — not because D-056 was wrong, but because the product owner judged the two-lane split itself to be the cost. **The transfer was free**: `lane-a-product-surface` was byte-identical to `origin/integration`, so **no unpromoted commit existed to hand over.** **Eleven of twelve board rows were claims, not code** — four returned `READY`, one returned `BLOCKED`, one ([TASK-205](BACKLOG.md)) **unblocked**, three were already QE's, one ([TASK-400](BACKLOG.md)) transferred as `CHANGES REQUESTED` | `APPROVED` | `lane-c-sync` | Lane A · Lane B · QE | **The one real unblocking is TASK-205.** [C-213](LANE_COORDINATION.md) closes as *overtaken, not answered* — the export and its consumer are now one lane's |
| **D-059** | **The Lane Coordination Model is `PREPARED`, not adopted** — [428](architecture/428-lane-coordination-model.md). Diagnosis: **three observed failures, one storage cause** — coordination state is prose, in shared files, travelling the code pipeline. Proposal: **one record one file · no stored assignee, joined from the registry at render time · coordination commits push direct to `integration` ungated**, widening the exception `--audit-claims` already guards. **TOML via stdlib `tomllib`**, because PyYAML is not a declared dependency and adding one is 🔴 | **`READY FOR PRODUCT OWNER`** | `lane-c-sync` | All lanes | **Step 1 is `modules.toml` alone and closes the C-213 class.** Steps 2–4 gated on step 1 holding, not on a date. **[`BACKLOG.md`](BACKLOG.md) keeps its hand-written order** — priority is judgement, not a field |
| **D-060** | **Distributed Product Development.** *"The organization should now evolve from centralized planning to distributed execution with centralized governance."* **Preparation moves to the lane that will implement it; Lane C reviews.** Lane A and Lane B become **Product Development lanes** owning the complete lifecycle of their modules — study the UI, audit reuse, size the slice, prepare, build, test, document, **and hold ~5 `READY` slices.** **Three new lifecycle states**: `PREPARING` · `UNDER REVIEW` · `REVISION REQUESTED`. **`READY` moves from the product owner to Lane C** — fitness, never priority. **QE unchanged in every respect.** **Transition is per module and event-driven**: a module switches when its current backlog is exhausted, so no lane switches mid-slice | `APPROVED` | `lane-c-sync` | All lanes | **The premise was measured before it was recorded**: 12 of 32 task rows are `TASK-4xx`, `integration` stood still for eleven polls, 8 commits unreachable today. **[429](architecture/429-distributed-delivery-model.md) §6 states the four costs**, one of them unmitigated — Lane C loses the deepest source of its module knowledge |
| **D-061** | **Ownership precedence, and git history demoted.** **① product architecture · ② bounded context · ③ long-term maintenance · ④ repository continuity · ⑤ historical implementation evidence.** *"Git history is evidence. It is not governance."* **Corrects [430](architecture/430-module-ownership-transition-plan.md)'s original basis**, which made recent commits primary. **Ownership optimises for cohesion, never arithmetic** — an 11/6 split is acceptable where it reflects the product's architecture, and **capacity is managed by epic sequencing rather than by redistributing modules.** **Standing rule added: do not divide ownership across an interface that has not yet stabilized** — C-213's general form. **`ai_platform` and `business_event_engine` are deliberately unassigned**, marked *review at first implementation*: **evidence over prediction** | `APPROVED` | `lane-c-sync` | All lanes | **Recent commits describe who was *available*, not who should be *responsible*** — promoting that to governance makes ownership a function of scheduling |
| **D-062** | **[`docs/coordination/modules.toml`](coordination/modules.toml) is the authoritative module ownership registry** — **428 step 1, adopted.** *"Define ownership in a single authoritative registry… then generate the ownership dashboards from that registry."* **Fields**: module · bounded context · current owner · future owner · transition stage · gate · review owner · implementation estimate · next milestone. **Only what cannot be derived is stored** — epic, slice, execution and QE status and blocker are still joined from the execution board. **The markdown assignment table was deleted from [`ACTIVE_ASSIGNMENTS.md`](ACTIVE_ASSIGNMENTS.md)**, and `_owners()` now reads the registry rather than scraping it. **TOML via stdlib `tomllib`** — no new dependency | `APPROVED` | `lane-c-sync` | All lanes | **A module absent from the registry renders `?`, never a default** — absence reported, not read as agreement (ADR-0032) |
| **D-063** | **AI Execution Modes — Development · Evaluation · Production.** **Development uses a deterministic mock provider and must never require a local model**; evaluation's provider is configurable and never forced; production is customer-configured. **Assessed in [431](architecture/431-ai-execution-modes.md), and the premise is half true**: the *tests* never needed Ollama — `MockTransport`, and *"a guarantee that needs a GPU to verify is not a guarantee"* — but **the running application has only two adapters and neither is deterministic.** **[ADR-0028](architecture/adr/0028-model-runtime-by-environment.md) already said the deterministic gates never require Ollama; what it never built was the third adapter.** **[TASK-415](BACKLOG.md)** builds it; **[TASK-416](BACKLOG.md)** waits on 431 §7. ⛔ **Streaming and tool-call simulation refused** — the port has neither, and **the mock must never lead the port** | **`READY FOR PRODUCT OWNER`** | `lane-c-sync` | `ai_platform` · all lanes | **[C-222](LANE_COORDINATION.md) dissolves under this**: it is a fact about `llama3.1:8b`'s wall-clock, not about the prompt, and it has blocked Epic G's release path since 2026-08-04 |

## 2026-08-04 — validation

| # | Decision | Status | Merged | Affected | Repository impact |
|---|---|---|---|---|---|
| **D-054** | **Repository Impact–Based Validation accepted as a framework.** *"The objective is not to run fewer tests… the repository decides."* | `APPROVED` | `lane-c-sync` | Certification · `infra/` · QE | **[427](architecture/427-impact-based-validation.md).** **Supersedes [426](architecture/426-change-aware-validation.md)'s narrow scope.** `REQUIRED_GATES` becomes **computed and recorded**, never passed. **Step 1 — [TASK-414](BACKLOG.md), report impact and skip nothing — is `READY`; steps 3–5 are gated on its evidence.** **An ADR is required when applied**, because it changes what a certification asserts |


| # | Decision | Status | Merged | Affected | Repository impact |
|---|---|---|---|---|---|
| **D-053** | **Change-Aware Validation Profiles — principle accepted, scope narrowed, timing deferred.** Mechanical and repository-driven, never discretionary; `make dr` mandatory for platform-affecting changes and every release candidate | `PARTIALLY APPROVED` | `lane-c-sync` | `infra/` · certification | **[426](architecture/426-change-aware-validation.md) · [TASK-413](BACKLOG.md) `SEQUENCED`.** Narrowed to **one rule** — `frontend/`-only skips `dr`. **Reuses `--next-cycle`'s classifier.** Deferred under §14: **no trigger has fired**, and the measured bottleneck is that certification is not being asked for |

## 2026-08-04 — synchronization recovery

| # | Decision | Status | Merged | Affected | Repository impact |
|---|---|---|---|---|---|
| **D-049** | **Do not force-push `lane-c-product-office`.** *"Treat `lane-c-sync` as the synchronization branch. Ask QE to validate it. Merge through the normal certification flow. After successful promotion, retire the old branch in a controlled cleanup. **Avoid rewriting published history unless absolutely necessary**"* | `APPROVED` | `lane-c-sync` | Repository | The rebuilt branch is **15 ahead, 0 behind** and fast-forwards. **Retirement of the old branch is deferred until after promotion** |
| **D-050** | **Implementation lanes derive executable work only from `origin/integration`, `READY` task rows and certified repository state.** **Product Office branches are planning artifacts, not execution contracts** | `APPROVED` | `lane-c-sync` | All lanes | `CLAUDE.md` §20e. **Lane A's unblock conditions named a Lane C branch**, so it waited on a ref the Task Claim Protocol never consults |
| **D-051** | **Synchronization becomes the highest repository priority whenever an implementation lane has been idle for more than one reporting cycle because `READY` work exists only outside `integration`** | `APPROVED` | `lane-c-sync` | Product Office | `CLAUDE.md` §20e. **It outranks the office's own queue** — the cost is paid twice, in the idle lane and in the preparation ageing while it waits |
| **D-052** | **The synchronization conflict resolutions are accepted** — remove duplicate TASK-403/404, keep only new executable rows, retain integration's ADR-0300 state | `APPROVED` | `lane-c-sync` | `BACKLOG.md` · ADR-0300 | **Both conflicts resolved toward *less* Lane C content**, which is the reduction intended |

## 2026-08-04 — implementation flow

| # | Decision | Status | Merged | Affected | Repository impact |
|---|---|---|---|---|---|
| **D-048** | **Product Office owns implementation flow.** *"It is also measured by implementation throughput. A successful Product Office is one where implementation lanes almost never become idle because executable work is unavailable."* **Implementation Support Mode · a five-slice READY buffer per lane · the self-check before any new package · synchronization as a first-class concern** | `APPROVED` | `lane-c-sync` | Product Office | [`PRODUCT_OFFICE.md`](PRODUCT_OFFICE.md) §12 · the Implementation Flow dashboard in every report. **A change of prioritisation, never of authority** — no rule is relaxed |

## 2026-08-04 — usage metering

| # | Decision | Status | Merged | Affected | Repository impact |
|---|---|---|---|---|---|
| **D-042** | **[D-029](#) stands — no Usage Accounting bounded context at this stage.** *"Do not force a module boundary until implementation naturally reaches it. If a future Billing capability naturally requires a dedicated boundary, we will introduce it then."* | `APPROVED` | `lane-c-sync` | Billing · M14b | **[424](architecture/424-usage-metering-assessment.md).** Preparation only. **Nothing claimable** |
| **D-043** | **The architectural direction is accepted** — *meter first, bill later*; operational facts stay independent of pricing policy; usage, pricing, subscriptions, invoices, taxes and payments remain separate concerns | `APPROVED` | `lane-c-sync` | Every module recording operational facts | **Confirms `CLAUDE.md` §10, which already ratified it on 2026-07-30.** No new rule |
| **D-044** | **OpenMeter and Kafka/ClickHouse architectures refused for this product stage.** *"Do not introduce additional datastores solely for usage metering. Continue extending existing PostgreSQL-backed operational telemetry unless objective scaling evidence later justifies a different architecture"* | `APPROVED` | `lane-c-sync` | Platform | **Principle 6 upheld.** The reversal condition is **objective scaling evidence**, never preference |
| **D-045** | **Build usage accounting, aggregation, reconciliation, snapshots and audit trail. Buy subscription management, invoicing, payments, taxes, the billing portal, dunning and collection.** **Stripe Billing is the preferred first integration; Lago a future self-hosted option if scale justifies it** | `APPROVED` | `lane-c-sync` | Billing | **§9 applied.** **Reconciliation and audit stay on the build side** — neither can be answered by a system that does not hold the operational facts |
| **D-046** | **Scope expanded to every billable operational fact** — AI inference and tokens, research jobs, CRM syncs, companies and people processed, workflow executions, notifications, storage, seats, API usage, exports, future capabilities | `APPROVED` | `lane-c-sync` | Every module | **A meter is added when the thing it meters exists, never before.** Each capability adds a `UsageReader` on its **own** `public/` — no central registry |
| **D-047** | **A second initiative is sequenced after Usage Accounting: Usage & Billing Observability** — internal and customer dashboards, summaries, forecasting, quotas, limit warnings, cost transparency, **meter health**, reconciliation, audit tooling | `APPROVED` | `lane-c-sync` | Billing · Support · Finance | **[424](architecture/424-usage-metering-assessment.md) §9b.** Four audiences. **Quotas are entitlement, forecasting is projection, anomaly detection is out of scope** |

## 2026-08-03 — the delegated rulings

**Ten rulings recorded in [ADR-0100](architecture/adr/0100-delegated-dependency-rulings.md), which states for each whether it rests on evidence or judgement — so the judgement ones stay cheap to reverse.**

| # | Decision | Status | Affected |
|---|---|---|---|
| **D-011** | **R-1 — platform composition.** One platform amendment, one RFC, four capabilities | `APPROVED` | `signora_platform` |
| **D-012** | **R-2 — a roadmap row is not claimable until it names its bounded context** | `APPROVED` | Repository process |
| **D-013** | **R-3 — ADR-0038 ratified** | `APPROVED` | Architecture |
| **D-014** | **R-4 — unassignable code: QE owns it; a rotating lane verifies QE's fixes** | ⚠️ **`SUPERSEDED` by D-022** | `infra/` · repository process |
| **D-015** | **R-5 — sellers see the commercial profile** | `APPROVED` | `commercial_profile` |
| **D-016** | **R-6 — contraction is not an opportunity** | `APPROVED` | `opportunity_engine` |
| **D-017** | **R-7 — Signora owns invitations** | `APPROVED` | `workspace_tenancy` |
| **D-018** | **R-8 — desktop-first** | `APPROVED` | Product surface |
| **D-019** | **R-9 — onboarding honesty as D39** | `APPROVED` | Product surface |
| **D-020** | **R-10 — ADR-0041 is not C-002.** The interpretation half deferred | `DEFERRED` | `commercial_profile` · `knowledge_graph` |

## Earlier — foundational rulings

**Recorded here as an index only; each is fully stated in the document named.**

| # | Decision | Date | Where it lives |
|---|---|---|---|
| **D-001** | **Lanes: parallel development, one assignee per module** | 2026-08-01 | `CLAUDE.md` §20e |
| **D-002** | **Local-first development — the correct quantity of CI is zero** | 2026-07-29 | [ADR-0027](architecture/adr/0027-local-first-development.md) · `CLAUDE.md` §20c-2 |
| **D-003** | **The platform freezes at M1.3A** | — | `CLAUDE.md` §20a |
| **D-004** | **The frontend foundation freezes at M1.5** | — | `CLAUDE.md` §20c |
| **D-005** | **Certification binds to a commit, never a branch** | 2026-08-02 | `CLAUDE.md` §20e · [ADR-0032](architecture/adr/0032-release-certification.md) |
| **D-006** | **Nobody assigns; lanes pull** — later amended so Lane C recommends and the product owner approves | 2026-08-02 | `CLAUDE.md` §20e |
| **D-007** | **Quality is the lane's, before it is QE's** | 2026-08-02 | `CLAUDE.md` §19 |
| **D-008** | **Identifiers are allocated from a per-lane block** | 2026-08-02 | `CLAUDE.md` §20e |
| **D-009** | **Lane C is established as the Product Office** | 2026-08-03 | `CLAUDE.md` §20e |
| **D-010** | **The product has a second ubiquitous language, and it is the customer's** | 2026-08-01 | [ADR-0034](architecture/adr/0034-ubiquitous-language.md) · `CLAUDE.md` §4 |
| **D-040** | **Model runtime is decided by environment** — Ollama in development, hosted in production | 2026-07-30 | [ADR-0028](architecture/adr/0028-model-runtime-by-environment.md) |
| **D-041** | **Deterministic Explainability** — of the Decision Package's fifteen parts the model authors three | 2026-07-30 | [ADR-0030](architecture/adr/0030-the-decision-package.md) |

---

## How this register is maintained

**Lane C records a row when the product owner rules.** The row names the decision, never restates the deliberation.

**Two things must be true of every row and are checkable:**

> **The `Merged` column says where the ruling is recorded, not where it was made.** A row reading `lane-c-sync` means the decision is **authoritative and not yet actionable** — `CLAUDE.md` §20e's five states, and the distinction Lane A's challenge established.
>
> **A superseded row is amended, never removed.** D-014 stays, marked `SUPERSEDED by D-022`, because *"a record of what was true then must not be rewritten"* (`CLAUDE.md` §2) — and because the reason a decision was reversed is usually more useful than the reversal.

**Identifiers are permanent and sequential.** `D-nnn` is never reused. **They are not per-lane blocks**, because only the product owner creates one.

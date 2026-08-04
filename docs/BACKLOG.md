# Repository backlog — the READY queue

> **The authoritative repository work queue.** Established 2026-08-02, on the product owner's direction, replacing QE-assigned scheduling. **Task ids added the same day**, so a claim has something immutable to refer to.
>
> **The product owner owns priority. Feature lanes pull from the top. QE never schedules.** A lane that has finished a slice does not wait to be told what to do next — it runs the **Task Claim Protocol** (`CLAUDE.md` §20e) and claims the highest eligible `READY` task.
>
> **The order of this queue *is* the priority.** Nothing else expresses it, and nothing else may contradict it.

## Why this exists

**QE was becoming the bottleneck for a model that exists to remove bottlenecks.** Quality engineering, integration, certification and promotion belong together — each is a judgement about the repository as a whole. **Scheduling is not one of those.** It is a product decision, and routing it through QE meant every idle lane waited for the one session that was busy certifying, which serializes exactly the parallelism the lanes were created for.

```
  planning            execution              quality and release
  ────────            ─────────              ───────────────────
  Product Owner  ──▶  feature lanes    ──▶   QE
  owns priority       claim and build        validates · certifies
  writes this file    record in              integrates · promotes
                      ACTIVE_ASSIGNMENTS     never schedules
```

## Task ids are permanent

**Every task carries a `TASK-nnn` that is never reused and never renumbered**, and **that id is what every other document refers to** — [`ACTIVE_ASSIGNMENTS.md`](ACTIVE_ASSIGNMENTS.md), a commit message, a Slice Handoff, a status report. Free-form titles drift; an id does not, and **an id is what makes "two lanes claimed the same task" a fact a machine can check** rather than a judgement about whether two sentences mean the same thing.

**A task's id, module and slice are stable. Its *status* and its *position* move.** Position is the product owner's; status follows the work.

| Status | Meaning |
|---|---|
| `READY` | **Claimable now.** Every input exists, no decision is outstanding, nobody holds it |
| `CLAIMED` | A lane holds it. The lane is named here, and [`ACTIVE_ASSIGNMENTS.md`](ACTIVE_ASSIGNMENTS.md) carries the detail. **Implementation begins immediately** |
| `IN PROGRESS` | Being built. **A claim flows straight into this** — there is no waiting state between them |
| `IN VALIDATION` | **Implemented and pushed.** Set by the implementing lane, the moment the work exists as commits QE can take. **The lane's responsibility ends here and it claims its next task immediately** |
| `CHANGES REQUESTED` | **QE**, during validation. Returned to the implementing lane with the corrections named; that lane fixes them and sets `IN VALIDATION` again |
| `VERIFIED` · `CERTIFIED` · `PROMOTED` | QE's stages, and **only QE's** — validation passed, `make certify` passed, `main` fast-forwarded |
| `WAITING` | Needs a **decision** from the product owner or another lane. **Named, always** |
| `BLOCKED` | Needs a **capability** that does not exist yet. **The capability is named** |
| `DONE` | Promoted to `main`. Removed at the next Closeout |

**`WAITING` and `BLOCKED` differ in who unblocks them**: one needs somebody to answer, the other needs somebody to build. A task nobody can move in either direction is a finding, not a backlog row.

> **The lane owns execution state; QE owns everything after it** (`CLAUDE.md` §20e, *Execution ownership ends at `IN VALIDATION`*). A lane moves its own task `CLAIMED` → `IN VALIDATION` when it pushes, and **stops there**. QE moves it through `VERIFIED` → `CERTIFIED` → `PROMOTED` → `DONE`, or back to `CHANGES REQUESTED`.
>
> **The point is that no state is nobody's.** QE was updating the execution status of work it did not write, which is bookkeeping rather than judgement — and a status nobody is clearly responsible for is the one that goes stale.
>
> **And a lane never waits here.** The moment it sets `IN VALIDATION` it returns to the `READY` queue and claims again — waiting for certification is idle capacity, and it is the cost that grows with every lane added. Four things stop a lane claiming, and *"my last slice is still with QE"* is not one of them (§20e, *Continuous execution*).

## What a lane may and may not do here

| May | May not |
|---|---|
| **Claim a `READY` task** — by the Task Claim Protocol, never by editing this file alone | **Reorder the queue.** Position is priority, and priority is the product owner's |
| **Record why it skipped the first `READY` task** — in that task's Notes | **Reprioritize** — including by claiming further down without saying why |
| **Move a task it holds through the lifecycle** — `CLAIMED` → `DONE` | **Insert a new `READY` task** without product-owner approval |
| **Report a defect or a dependency** — [`BUGS.md`](BUGS.md), [`LANE_COORDINATION.md`](LANE_COORDINATION.md) | **Remove a task**, or rewrite one it does not hold |

> **A skip is information, not an inconvenience.** *"Lane A skipped TASK-002 because it needs `signal_engine`, which Lane B holds"* tells the product owner something about the queue's shape. Silence tells them the queue is fine when it is not.

---

## READY — claimable now, in priority order

> **Seven tasks became claimable on 2026-08-03**, when [ADR-0100](architecture/adr/0100-delegated-dependency-rulings.md) resolved the decisions they were waiting on. **They are placed at the top because they have waited longest**, not because they are larger.

### TASK-300 · Epic A — surface what already exists

| | |
|---|---|
| **Module** | **Six slices across four modules** — see the table below. **Not one claimable unit**, which is the finding |
| **Slice** | A4 · A1 · A2 · A5 · A6, specified in [51-implementation-specifications.md](architecture/51-implementation-specifications.md) |
| **Status** | **`CLAIMED` — Lane B**, 2026-08-03. **Assigned directly by the product owner**, who named Lane B implementation owner for Epic A and set A4 as the first slice. Recorded here by Lane B because the row did not exist; **the priority is the product owner's, not this lane's** |
| **Notes** | **Verified against Lane A's branch before claiming, not against this register.** Of the six slices, **one is built, one is substantially built by Lane A this week, and every remaining one needs at least one module Lane A holds.** [C-323](LANE_COORDINATION.md) carries the evidence and a recommendation |

| Slice | Verified status, 2026-08-03 | Blocked on |
|---|---|---|
| **A4** freshness | **Not built.** No `last_observed_at` in any router or component | `provider_platform` **public port** (Lane A) · the render (Lane A). The response composition is `opportunity_engine` — **Lane B's** |
| **A1** search | **Not built.** No search endpoint in any router; `/account-identities` names ids you already hold and is not a lookup | The shell (Lane A) · **and the endpoint has no owning module yet** |
| **A2** accounts list | **Substantially built by Lane A**, `SW-01`…`SW-04`, this week — `TriageStrip`, `lib/state/triage.ts`, URL-driven narrowing | **Nothing. It is being delivered elsewhere** |
| **A5** company history | **Not built.** `claim.observed_at` holds the series; nothing exposes it | The render (Lane A). **Backend is `knowledge_graph` — unassigned** |
| **A6** needs identity | **Not built.** `AccountIdentityResponse.agreement` is the raw material | The render (Lane A). **Backend is `knowledge_graph` — unassigned** |
| **B2** first run | **Built by Lane A** — `first-run.test.tsx`, D36 | — |

> **This lane is not proceeding into Lane A's modules on the strength of a directive that predates the collision.** One assignee per module is §20e's hardest invariant, and the product owner's own instruction in the same assignment was *"do not quietly bypass module boundaries."* **[C-323](LANE_COORDINATION.md) asks which way to resolve it**; the two backends in unassigned `knowledge_graph` are claimable meanwhile.

### TASK-400 · Epic A completion — the surfaces that expose what the platform already knows

| | |
|---|---|
| **Epic** | **Epic A remainder**, [51-implementation-specifications.md](architecture/51-implementation-specifications.md). **Assigned whole, not sliced** |
| **Module** | `provider_platform` (A7) · Product Surface (A6 render) — **both Lane A's** |
| **Status** | **`IN PROGRESS` — Lane A, narrowed to A7 by Lane C 2026-08-03.** **A6 is withdrawn from this task and Lane A was right to hold it.** `51-implementation-specifications.md` §A6 states twice that its backend *"depends entirely on the [C-321] ruling"* — and **[C-321](LANE_COORDINATION.md) is `OPEN` and the product owner's.** **Lane C assigned A6 without reading that line**; narrowing the render does not escape it, because *what to render* **is** the ruling. **A6 returns when C-321 is answered** |
| **Assigned** | **Lane A, by Lane C 2026-08-03**, answering [C-217](LANE_COORDINATION.md). Decomposition of Epic A, **already approved by the product owner** — not new scope |

**Epic A verified slice by slice, across every branch, before assigning:**

| Slice | State | Who |
|---|---|---|
| **A1** search | ✅ built — `account_search` | Lane B |
| **A2** accounts list | ✅ built — `SW-01…04` | Lane A |
| **A4** freshness | ✅ built | Lane B |
| **B2** first run | ✅ built — `first-run.test.tsx` | Lane A |
| **A6** *needs identity* | ⬜ **render not built.** Raw material exists — `AccountIdentityResponse.agreement` | **This task** |
| **A7** last *looked* | ⬜ **not built.** No `attempted_at`/`polled_at` anywhere; `provider_watermark.position` advances only when records arrive | **This task** |
| **A5** company history | 🚫 **backend does not exist** — no history endpoint in `knowledge_graph`, and the module is unassigned | **Routed to Lane B**, see notes |

| | |
|---|---|
| **A7 — objective** | Every account can state when a provider last *attempted* to read it, whether or not anything came back. **`attempted_at` on `provider_watermark`, written on every completed run** |
| **A7 — the hard part** | **Not the column.** `subject` is the customer's typed company name and the brief holds an entity id; **the join is the open question.** Resolve it with Lane C rather than assuming it |
| **A7 — risk** | **Ship the word *checked* only once it is true.** A4 deliberately refuses it and `freshness.test.tsx` asserts the refusal — **that test is the contract** |
| **A6 — objective** | Unnamed records leave the working list. `agreement` is the raw material and nothing renders it |
| **Effort** | **S** (A7 column) + **M** (A6 render) · **M** if A7's join needs a design |
| **A5 is not in scope** | Its backend is unbuilt in an unassigned module. **Lane C has routed the backend to Lane B**, which already owns A1 and A4 in `knowledge_graph`. **A5's render returns to Lane A once the endpoint exists** — sequencing, not a blocker |

### TASK-401 · A5 backend — **BUILT 2026-08-03 by Lane B, before this row was written**

| | |
|---|---|
| **Epic** | **Epic A, slice A5's backend half.** [51-implementation-specifications.md](architecture/51-implementation-specifications.md) |
| **Module** | **`observation_engine`** — *not* `knowledge_graph`. **Lane C named the wrong module; the specification says Observation Engine and Lane B built it there** |
| **Status** | **`DONE` — superseded by `145345f`**, which shipped `GET /workspaces/{id}/accounts/{account_id}/observations?attribute=`, the Observation Engine's first HTTP surface, with a response-shape suite |
| **Notes** | **Lane C's *"verified unbuilt"* was verified against the wrong module.** `knowledge_graph/interface/router.py` genuinely has no history endpoint — **and never should have; the history lives in `observation_engine`**, which had carried thirteen fields since M4 with no interface layer at all |
| **Customer value** | *"Employee count 2024 → 350, 2025 → 500."* **Delivered.** The claim model already held every attribute's history with its source and observation time; the endpoint exposes what the platform computed years of design to be able to say |
| **Why it was cheap** | **No new storage and no new concept**, exactly as [50-product-capability-audit.md](architecture/50-product-capability-audit.md) predicted: *"not a feature to add; it is a `SELECT` over claims ordered by `observed_at`"* |
| **The render is not next** | **It is blocked twice**, and neither blocker was visible when this row was written: **[C-324](LANE_COORDINATION.md)** — where Epic A's rendering stops being Lane B's — and **[B-319](BUGS.md) 🟠**, which finds the Playground produces **no attribute transitions at all**. **The endpoint is correct and its screen would be empty.** Building it now ships a blank chart |
| **Two constraints any render must respect**, both recorded in [23-observation-engine.md](architecture/23-observation-engine.md) | **One series per provider** — Apollo saying 120 and CoreSignal saying 145 is *disagreement, not growth of 25* · **`previous_observed_at`…`observed_at` is an interval**, so a single dated point claims precision the evidence does not have |

### TASK-402 · Epic E1 — a customer's CRM becomes a source Signora can read

| | |
|---|---|
| **Epic** | **E1**, [51-implementation-specifications.md](architecture/51-implementation-specifications.md). **Assigned whole** |
| **Module** | `integrations` — **Lane B's**, which built S01, S02 and S09 |
| **Status** | `READY` — **after [B-400](BUGS.md)** |
| **Assigned** | **Lane B, by Lane C 2026-08-03**, under the authority to assign a fresh epic when approved scope runs out |

**Why this epic and not Epic D, correcting Lane C's own earlier recommendation.** [Pack I](DECISION_PACKS.md) recommended **D2 and D3**. **D3's own specification says *"depends on E1"*, and Lane C called it unblocked — that was wrong.** Verified in the catalog: of D1's four risk families, **`contraction_risk` and `decision_maker_departed` already exist**, and the two that do not — *usage decline* and *renewal approaching* — **need contract and usage data that only a CRM carries.** **Epic D is gated on this epic, so this one comes first.**

**The reuse audit changes the size, and it is the reason to take it now.** The specification calls E1 **XL**. **Most of the connection half is built:**

| Already built | Where |
|---|---|
| OAuth start + callback | `frontend/app/api/integrations/[slug]/{start,callback}/route.ts` — **a separate OAuth client from Better Auth's** |
| Connection, grant, catalog, resolve, connect/disconnect | `modules/integrations/{domain,application}` |
| Encrypted credential storage | `infrastructure/secrets.py` · migration **`0028_integration_secret`** |
| Public contract · router · schemas | `modules/integrations/{public,interface}` |

> **What remains is the *read*, not the plumbing:** a CRM adapter behind the existing port, normalization of accounts and opportunities into the canonical shape, and the events that carry them. **That is the difference between XL and L, and it is why this is worth starting rather than deferring.**

| | |
|---|---|
| **Customer value** | The specification's own words: **the single highest-leverage integration in the roadmap — it unblocks pipeline intelligence, forecasting, expansion and customer risk on its own** |
| **Unblocks** | **D3** directly · **D1's** two missing risk families · **E2** write-back · the whole expansion and renewal half of the vision |
| **Non-negotiable** | **A sign-in OAuth token must never be reused as an integration token** (§13). Separate grants, separate scopes, separate storage — **already the shape `integration_secret` and the separate OAuth client enforce** |
| **On claiming** | **Provider Normalization owns the canonical shape**, not `integrations` — a CRM payload is normalized the same way a provider payload is (§10, the anticorruption layer). **Do not invent a second normalization path**; open a `C-` item if the existing one does not fit |
| **Escalate if** | The read requires a new bounded context, or a commercial ruling about which CRMs are GA versus enterprise. **Neither is expected — E3 and E4 are the enterprise gate, not E1** |

### TASK-403 · A-i — the Decision Package becomes reachable

> **Drafted by Lane C on the product owner's instruction, 2026-08-04, from [417](architecture/417-executable-slice-audit.md) §4.** **Position here is grouping with the other `4xx` rows, not priority — ordering these four against the rest of `READY` is the product owner's.**

| | |
|---|---|
| **Objective** | **A customer can read a Decision Package.** The module that *"concludes"* has produced them since M10 and **nothing can reach one** |
| **Module** | `ai_reasoning_engine` — **Lane A's**, via TASK-202 |
| **Status** | `READY` |
| **Approved screen** | **AI Copilot** — the *Reason* verb, and the reasoning/evidence/confidence/sources apparatus |

> ⚠️ **This slice is larger than [417](architecture/417-executable-slice-audit.md) §2c implied, and Lane C corrects it here rather than letting the claiming lane find it.** 417 described *"an interface layer over a module's own `public/`."* **`ai_reasoning_engine/public/__init__.py` ends `__all__: list[str] = []`** — *"nothing here is exported yet: the module is scaffolded and its boundary contracts are registered."* **There is nothing to expose yet.**

| | |
|---|---|
| **Scope** | **Two ordered parts, one slice.** ① Publish the Decision Package read contract through `public/` — 🟠, the module's own. ② An `interface/` layer over it, modelled on `ai_research_engine/interface/` (`errors` · `handlers` · `router` · `schemas`) |
| **Dependencies** | **None.** [C-222](LANE_COORDINATION.md) governs *live inference*; **reading a package that already exists needs no model call** |
| **Affected modules** | `ai_reasoning_engine` only. One composition file, one router registration |
| **Repository reuse** | `ai_research_engine/interface/` **is the pattern** — four files, `202`/`200` split, `CurrentWorkspace`, purpose-built response schemas. `knowledge_graph/interface/router.py` for the batch argument |
| **Non-goals** | **No recommendation, no message, no cross-account ranking, no next action** — the module's own docstring refuses all four and names M11 as their owner. **No live inference. No prompt change. No new event. No write path** |
| **Acceptance** | A stored Decision Package is readable over HTTP, workspace-scoped, with **all fifteen parts** and their provenance · **the three model-authored parts are distinguishable from the twelve derived** ([ADR-0030](architecture/adr/0030-deterministic-explainability.md)) · `lint-imports` and `mypy --strict` clean · no `UPDATE` path |
| **Implementation order** | **First of the four.** ① then ② |
| **Validation** | Module suite · an API test asserting workspace isolation returns `404` not `403` · **a test that the surface exposes no recommendation or action field** — the refusal is the design, so assert it |
| **Escalate if** | Publishing the contract turns out to require a domain change, **or ② proves large enough to be its own slice** — split it and open a `C-` item rather than growing this row |

### TASK-404 · A-ii — Sales Engagement reaches a customer

| | |
|---|---|
| **Objective** | **The approach, its brief, its risks and its next actions become readable.** Built, tested, prompt-versioned, evaluated — **and unreachable** |
| **Module** | `sales_engagement` — **Lane A's**, which built it ([50-sales-engagement.md](architecture/50-sales-engagement.md)) |
| **Status** | `READY` |
| **Approved screens** | **AI Copilot** · **Opportunity Intelligence** — *"ranked by expected effect on this quarter · you approve, Signora drafts"* |
| **Scope** | An `interface/` layer over the **existing** `public/`. **Read-only** |
| **Dependencies** | **None** |
| **Affected modules** | `sales_engagement` only |
| **Repository reuse** | **`public/` already exports what the screens render** — `Approach`, `ApproachBrief`, `ApproachReasoning`, `NextAction`, `Recommendation`, `Risk`, `RiskKind`, `ProductFit`, `FitDimension`, `FitReason`, `RankedRole`, `Evidence`, `Passage`, `STALE_AFTER_DAYS`. **Nothing in `domain/` or `application/` changes.** `ai_research_engine/interface/` is the pattern |
| **Non-goals** | **No send, no draft-commit, no approval workflow** — *"nothing sends without your approval"* is a later slice and belongs to whoever owns the send. **No new model call. No ranking invented here** — the module already refuses cross-account urgency (`50-sales-engagement.md` §22) |
| **Acceptance** | An approach is readable per account, workspace-scoped · **`STALE_AFTER_DAYS` is honoured and staleness is visible**, never silently served · every rendered claim carries its `Evidence` · `lint-imports` and `mypy --strict` clean |
| **Implementation order** | **Second.** Independent of TASK-403 — order is preference, not dependency |
| **Validation** | Module suite · API test for workspace isolation · **a test that a stale approach is marked rather than hidden** |
| **Escalate if** | A screen needs a field `public/` does not export. **Do not widen `public/` to fit a layout** |

### TASK-405 · A-iii — a signal ends in a decision

| | |
|---|---|
| **Objective** | **Every signal leaves the queue by being actioned, assigned, snoozed or dismissed with a reason** — and the resolution is durable and auditable |
| **Module** | `signal_engine` — **Lane A's**, via TASK-203 |
| **Status** | `READY` |
| **Approved screen** | **Signal Center** — *"a triage queue, not a notification list"* |
| **Scope** | Resolution state for a signal: **assign · snooze-until · dismiss-with-reason · actioned**, each attributed and timestamped. A workspace-scoped read of the queue by state |
| **Dependencies** | **None. [O2](DECISION_PACKS.md) does not block this** — ADR-0040 governs notification *delivery*; **this is resolution state, which `signal_engine` owns** |
| **Affected modules** | `signal_engine` · one migration · `tenancy_policy.py` registration |
| **Repository reuse** | ⚠️ **`opportunity_engine` already owns the dismissal concept** — `DISMISSED`, *"deliberately distinct from `CLOSED_LOST`… one is feedback about Signora's judgement, the other is a sales outcome."* **A signal-level dismissal is that concept one level down. Reuse the vocabulary; do not define a second one** (§4). ⚠️ **`frontend/lib/state/triage.ts` is a naming collision, not prior art** — it *"counts and groups"* over server-computed facts and resolves nothing |
| **Non-goals** | **No notification, email, digest or alert rule** — that is ADR-0040 and unratified. **No rule retuning, no precision metrics, no threshold proposals** — the screen shows them; they are a later slice. **No deletion**: *"nothing is deleted — every resolution is auditable"* |
| **Acceptance** | A signal can be assigned, snoozed and dismissed, each recorded immutably with actor and time · **a dismissal cannot be recorded without a reason** — enforce in the type, not a check · **a snoozed signal returns at the stated time with its original evidence intact** · resolution never mutates the signal or its evidence · new table registered in `tenancy_policy.py` with forced RLS in the creating migration |
| **Implementation order** | **Third. The largest of the four, and entirely self-contained** |
| **Validation** | Module suite · **a Security Invariant for the new table** · migration reversible to base and back · a test that resolution history is append-only |
| **Escalate if** | The reuse of `DISMISSED` requires a cross-module dependency the graph does not have. **Open a `C-` item; do not copy the enum** |

### TASK-406 · A-iv — an ICP criterion is scored against outcomes

| | |
|---|---|
| **Objective** | **A criterion states what it predicts, measured against closed-won.** The ICP is declarable today and **nothing tells a customer whether it is any good** |
| **Module** | `commercial_profile` — **Lane A's**, via TASK-203 |
| **Status** | `READY` |
| **Approved screen** | **ICP Builder** — *"every criterion is scored against closed-won evidence, not opinion"* |
| **Scope** | Per-criterion lift against decided opportunities, with its sample size · the aggregate backtest — **win rate and median cycle, in-ICP versus outside** |
| **Dependencies** | **None.** `opportunity_engine` `GET /accounts/decided` supplies the outcomes and is published |
| **Affected modules** | `commercial_profile` · a read of `opportunity_engine`'s **`public/`** — **verify the edge exists in [05](architecture/05-module-dependencies.md) before writing it; if it does not, that is a `C-` item, not a new import** |
| **Repository reuse** | The ICP declaration, its versioning and `GET /icp-segments` all exist. **`/accounts/decided` exists.** No new persistence is expected — **lift is derived, not stored** (§2, *truth has exactly one authoritative representation*) |
| **Non-goals** | **No fitted weights, no refit, no drift markers** — the screen shows them; they are a model, not a measurement, and are a later slice. **No TAM funnel** — it needs a market database that does not exist. **No *Decision makers* criteria** — those are person-existence and are blocked by [O1](DECISION_PACKS.md). **No AI suggestions** |
| **Acceptance** | Each criterion reports lift and **its sample size** · a small sample is visibly small — the screen's own discipline is *"2.2× lift on only 22 deals; treat as directional, not settled"* · **the backtest reports both cohorts, never in-ICP alone** · a criterion no outcome data supports says so rather than reporting `1.0×` |
| **Implementation order** | **Fourth.** Independent of the other three |
| **Validation** | Module suite · a test that a zero-sample criterion is reported as unmeasured rather than neutral · **no new table** |
| **Escalate if** | The measurement requires reading `opportunity_engine`'s tables rather than its `public/`. **That is never permitted** (§5) |

### TASK-900 · The platform learns to compose a module into the runtime

| | |
|---|---|
| **Module** | `signora_platform` — 🔴, and **explicitly approved** by [ADR-0100](architecture/adr/0100-delegated-dependency-rulings.md) R-1 |
| **Slice** | **The RFC only.** No rewiring in this task |
| **Status** | `READY` |
| **Notes** | Four capabilities in one RFC: a session on `EventHandler` · `PublishableEvent` satisfiable by a frozen dataclass · a port from a handler to a provider adapter · a self-directed Casbin action. **Additive only** — a module not using one behaves identically |
| **On claiming** | **The RFC lands before any module is rewired.** §20a's approval branch means approved *then* implemented. Closes [C-012](LANE_COORDINATION.md), [C-013](LANE_COORDINATION.md), [C-021](LANE_COORDINATION.md), [C-207](LANE_COORDINATION.md) |

### TASK-901 · Seven modules consume the events they declare

| | |
|---|---|
| **Module** | Seven pipeline modules, **one per slice** |
| **Slice** | **Seven independently certifiable slices**, not one |
| **Status** | `BLOCKED` on TASK-900 — listed here so the sequence is visible |
| **Notes** | After each, `make runtime-composition` is measured and **`BLOCKED_BY_C012` shrinks by exactly one.** A module leaving that list is how the architecture records that it now expects live consumption |

### TASK-902 · M7 Timeline — the remaining slices

| | |
|---|---|
| **Module** | `timeline` |
| **Slice** | S05+ |
| **Status** | `READY` — **[ADR-0038](architecture/adr/0038-timeline.md) is ratified** |
| **Notes** | **Postgres first**; Meilisearch on a stated trigger — *the first customer asking to search or facet a timeline rather than scroll it*. **Ship the six live events**; the seventh joins when M11 resumes. **The customer surface already exists** — CX-03 mounted the feed on the account brief |
| **On claiming** | Supersedes `TASK-017`, which was waiting on exactly these three answers |

### TASK-903 · A seller can see what their company sells

| | |
|---|---|
| **Module** | `commercial_profile` (the read surface) · Product Surface (the mount) — **a two-lane build** |
| **Slice** | one slice each side |
| **Status** | **`READY` — but narrowed.** Verified against branches by Lane C 2026-08-03: the read surface overlaps [TASK-300](#task-300--epic-a--surface-what-already-exists) slice **A4**, which Lane B holds. **[C-323](LANE_COORDINATION.md) and [C-404](LANE_COORDINATION.md) carry the evidence** |
| **Notes** | **Read-only, for `member`, beside the account brief** — not under `/settings`, where the granted read is unreachable behind `workspace:update`. `policy.csv` already grants `member` read on `product`, `icp`, `buying_committee` and `commercial_focus`: **the API and the product disagree, and the API is right** |
| **On claiming** | Open a `C-` item for the mount if the two halves are claimed by different lanes. **Placement is judgement** ([ADR-0100](architecture/adr/0100-delegated-dependency-rulings.md) R-5) — say so in review if it reads wrong |

### TASK-904 · An organization can grow

| | |
|---|---|
| **Module** | `workspace_tenancy` |
| **Slice** | invitation table · acceptance · members list |
| **Status** | **`IN VALIDATION` — Lane A. Already built; corrected by Lane C 2026-08-03, [C-404](LANE_COORDINATION.md).** Verified on `lane-a-product-surface`: migration `0031_invitation.py`, `domain/invitation.py`, `application/use_cases/invite_member.py`, `tests/test_invitation.py`, across **TM-01…TM-06** — one titled *"an organization can grow"*, this row's own words. **Assigned directly by the product owner on 2026-08-02, a day before this row was written from [ADR-0100](architecture/adr/0100-delegated-dependency-rulings.md) R-7** |
| **Notes** | **Signora owns the invitation.** An `invitation` table keyed by email; acceptance matches a pending row against the **`email` claim already in the verified JWT**. **Better Auth's `organization` plugin is not adopted** — migration `0005` revokes `signora_app` from the `auth` schema, so plugin-owned membership is membership the Python tier cannot read, and §13 requires it re-verified every request |
| **On claiming** | **v1 delivery is a shareable link, not email.** No transactional-email dependency is added. **That half is judgement** and is the ruling to challenge first if you would rather ship with email |

### TASK-905 · A contraction risk stops looking like an opportunity

| | |
|---|---|
| **Module** | Product Surface · `buying_score_engine` owns posture |
| **Slice** | one slice |
| **Status** | **`READY`.** ⚠️ **Lane C marked this `IN VALIDATION` on 2026-08-03 and was wrong — restored the same day.** The `contractionary` marking in `attention.tsx` is real but arrives from **`0d8d325` (M12.3), already promoted to `main`** — **not** from Lane A's branch, which is what Lane C claimed. **Lane A, which owns the module, states nothing about this row has moved.** The module owner's reading stands over the office's inference. **What R-6 still requires beyond the promoted marking is Lane A's to state** |
| **Notes** | Posture reaches the attention row. **A contraction risk must not be confusable with a low-scoring opportunity** — they mean opposite things to a CRO scanning a list. **The treatment is yours**, within the design system; the ruling is only that they must differ |

### TASK-906 · M14b names its bounded context

| | |
|---|---|
| **Module** | **Undecided — that is the deliverable** |
| **Slice** | discovery |
| **Status** | `READY` |
| **Notes** | [ADR-0100](architecture/adr/0100-delegated-dependency-rulings.md) R-2: **a roadmap row is not claimable until it names its bounded context.** M14b's first task is therefore the discovery that names it. Lane A's analysis is already recorded — *one module and two integrations, not one and not three* |

### TASK-001 · Verify the three fixes QE may not close

| | |
|---|---|
| **Module** | Repository — `apps/`, documentation, process |
| **Slice** | one slice |
| **Status** | **`DONE`** — QE, 2026-08-02. Lane B verified [B-009](BUGS.md), [B-013](BUGS.md) and [B-014](BUGS.md) with evidence; all three are now `VERIFIED`. [B-012](BUGS.md) was reported alongside them and still awaits a non-QE verifier |
| **Notes** | **Explicitly not QE's.** [B-009](BUGS.md), [B-013](BUGS.md) and [B-014](BUGS.md) were all fixed by QE, which may not verify its own work. Reproduce each from a clean shell, from the original steps, **never from the diff**. Small, and it retires three rows |
| **On claiming** | **A fourth row is in the same condition and is not in this task's scope as written: [B-012](BUGS.md) is `FIXED` and awaiting verification by someone other than QE.** Lane B will verify it alongside the three and say so, but is **not** rewriting the task — inserting scope into a `READY` task is the product owner's, not a lane's. If that is unwanted, the fourth verification is reported and B-012's status is left alone |

### TASK-002 · An account with nothing live says nothing at all (R2-03)

| | |
|---|---|
| **Module** | Product Surface |
| **Slice** | PS-01 |
| **Status** | **`DONE`** — QE, 2026-08-02. Promoted in the PS/PP batch at `e5a266d` |
| **Notes** | 🟡. Overlaps R1-04 — read both before starting |
| **On claiming** | **R1-04 is 🟠, unimplemented, and is the same plumbing.** The brief receives `evidence` on the opportunity response and renders `is_current` only, so *cooling* never reaches it — and R2-03 cannot be answered without the brief learning the same fact. Lane A will surface evidence state on the brief once and let both findings read it, rather than adding a second path for the second finding. **The task is not being rewritten**: R1-04 has no id, and inserting `READY` scope is the product owner's. If the overlap should instead be a separate task, say so and the R1-04 half is reported rather than shipped |

### TASK-003 · The attributes are engineering's words (R11-06)

| | |
|---|---|
| **Module** | `knowledge_graph` |
| **Slice** | KG-01 |
| **Status** | `READY` |
| **Notes** | 🟡. [ADR-0034](architecture/adr/0034-ubiquitous-language.md)'s customer vocabulary reaches attribute names, and nothing enforces it there yet |
| **Skipped by Lane A**, 2026-08-02 | **Not claimable as written — [C-018](LANE_COORDINATION.md) opened.** Every available implementation contradicts something already written: `knowledge_graph` publishing labels contradicts AC-28 (*an entity is an identity, not a record*) and ADR-0034 (*the translation never travels inward*); translating in the browser contradicts [R11-06](architecture/39-product-review-findings.md) itself (*never in the browser*); the third option — a reviewed catalog of attribute labels — does not exist. **R11-06 also records itself as a deliberate trade-off** whose milestone is *"on evidence from a real reviewer"*, and no reviewer evidence has been recorded, so the trigger may not have fired. Lane A took **TASK-004** instead |

### TASK-004 · The brief distinguishes *not narrated* from *narrated against evidence that no longer resolves*

| | |
|---|---|
| **Module** | Product Surface |
| **Slice** | PS-02 |
| **Status** | **`DONE`** — QE, 2026-08-02. Promoted in the PS/PP batch at `e5a266d`. Taken after [TASK-003](#task-003--the-attributes-are-engineerings-words-r11-06) was skipped with its reason recorded |
| **Notes** | The lane's half of [B-010](BUGS.md). The `RUNNING.md` half is QE's and is done separately. **Do not "fix" it by deleting narrations** — a materialized AI artifact is a historical fact (§2) |

### TASK-005 · `state-check` learns the backlog

| | |
|---|---|
| **Module** | Repository tooling — `infra/` |
| **Slice** | one slice |
| **Status** | **`DONE`** — QE, 2026-08-02. The board-vs-backlog check is built and promoted; it is what reported these four stale rows |
| **On claiming** | **Only the unbuilt half.** [B-017](BUGS.md) asked whether this task was superseded; measured, it is *half* superseded. QE's `e1d2fa6` routed claims to `integration`, which makes cross-branch detection largely moot — **that half is withdrawn.** But *"every `CLAIMED` row has a matching lane on the board"* is **not built**: `state-check` check 5c reads the board only, so a backlog row reading `CLAIMED — Lane X` with no board row is invisible today. Lane B builds that half and leaves B-017's ruling to QE |
| **Notes** | Assert that no task is claimed twice and that every `CLAIMED` row has a matching lane on the board. **A slice, not a Closeout** — `infra/` decides whether gates pass ([B-014](BUGS.md)). *Partly delivered 2026-08-02; what remains is the id-level checking* |

---

## WAITING — on a decision, and on whom

| Id | Task | Module | Waiting on |
|---|---|---|---|
| **TASK-006** | [C-010](LANE_COORDINATION.md) — no lane is assignable to `apps/`, `signora_platform/` or repository process | Repository | **The product owner.** Four defects have landed in this gap: [B-007](BUGS.md), [B-012](BUGS.md), [B-013](BUGS.md), [B-014](BUGS.md). **The highest-value decision on this page** |
| **TASK-007** | [C-008](LANE_COORDINATION.md) — sellers cannot see what their company sells | Product Surface | **The product owner**, to choose between options A/B/C/D. The proposal is accepted; only the choice remains |
| **TASK-008** | [C-005](LANE_COORDINATION.md) — the signal-profile write path | `signal_engine` | **The product owner**, on whether a customer should author relevance at all. Ownership answered; sequencing is not |
| **TASK-009** | [C-009](LANE_COORDINATION.md) — an internal fault reaches a customer as a `422` | `signora_platform` | **The product owner.** A frozen-platform change under §20a, with a full proposal recorded |
| **TASK-010** | [C-006](LANE_COORDINATION.md) — which lane owns `test_api_<module>.py` | Repository | **The product owner**, and deliberately: *"avoid creating a local convention that later becomes repository behaviour"* |
| **TASK-011** | The brief's hierarchy pass (D20) | Product Surface | **A seller in the room.** A collaborative product-design activity, not a slice |
| **TASK-012** | M9.5 Step F | AI Platform | **The product owner.** Inserted, open, and the oldest outstanding commitment on the board |
| **TASK-013** | `reasoning@1` has no released model | `ai_reasoning_engine` | **The product owner.** The Decision Package would refuse at runtime. **Do not tune the prompt, delimiter, schema or timeout to make it pass** |
| **TASK-017** | **M7 — Timeline.** [C-020](LANE_COORDINATION.md) — no milestone definition, no module design, Meilisearch unprovisioned, event scope unagreed | `timeline` | **The product owner.** Two decisions: the §6 milestone definition, and Meilisearch now or Postgres-first on a stated trigger. **Assigned to Lane B 2026-08-02 and released the same day** — the module assignment stands; the work is not executable until the architecture is agreed |

## BLOCKED — on a capability, and on which

| Id | Task | Module | Blocked on |
|---|---|---|---|
| **TASK-014** | [C-007](LANE_COORDINATION.md) — the guided first run | Product Surface | The `target_accounts_changed` consumer in `provider_platform`. The sequencing condition has fired — all five declarations exist — so this is a missing capability, not a missing decision |
| **TASK-015** | [B-004](BUGS.md) — `provider_watermark` cannot tell two target accounts apart | `provider_platform` | The same consumer. **Not to be fixed opportunistically**: without it, the schema change has nothing exercising it |
| **TASK-016** | [R9-04 / D5](architecture/39-product-review-findings.md) — what changed since you last looked | Product Surface | Per-user read state, which does not exist. **Trigger unfired** — a design partner saying they cannot tell what is new |

> **`TASK-015` was moved to `READY` by Lane A and is withdrawn, 2026-08-02.** The row is restored exactly as the product owner wrote it. **The reasoning for unblocking it is not withdrawn — only the act of unblocking**, which is a priority decision and not a lane's ([B-019](BUGS.md)).
>
> **The fact the decision needs, stated once and not acted on:** the blocker read *"not to be fixed opportunistically — without it the schema change has nothing exercising it."* That condition is now **satisfied rather than waived**: PP-02 is the consumer that exercises it, [ADR-0036](architecture/adr/0036-target-account-contract.md) names this *"one defect that must be fixed before the consumer is built"*, and **both are implemented and with QE** as migrations `0029` and `0030`.
>
> **So the code exists whatever this row says.** It travels under PP-01 and PP-02 regardless of which section holds the id, which is why withdrawing costs nothing and unblocks certification immediately. **Ratify it where it stands, or leave it here** — either is correct, and only the product owner may choose.

## DONE — promoted, removed at the next Closeout

*These predate task ids and are recorded by commit, which is the immutable reference they do have.*

| Task | Lane | Promoted |
|---|---|---|
| R2-01 — the guidance says what it is pointing at | A | `efaa987`, in `1bbee30` |
| M12.5 slice 5 — target accounts. *M12.5 complete* | B | `3f4e988` |
| M12.4 — research on demand | A | `c1f5985` |
| Commit-bound certification | QE | `1bbee30` · `624f770` |
| Pull-based work allocation | QE | `3e36da9` |

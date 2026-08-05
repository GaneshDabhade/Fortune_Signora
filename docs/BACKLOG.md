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
| `READY` | **Claimable now.** Every input exists, no decision is outstanding, nobody holds it. **Set by Lane C on approving the implementation package** from 2026-08-04 ([D-060](DECISION_REGISTER.md)) — **a statement of fitness, never of priority.** The queue's *order* remains the product owner's |
| **`PREPARING`** | **The module's owning lane is authoring the implementation package** — reuse audit, slice boundary, contracts, sequencing. **Not claimable**, including by the lane preparing it *(added 2026-08-04, [429](architecture/429-distributed-delivery-model.md))* |
| **`UNDER REVIEW`** | **Submitted to Product Office.** **The preparing lane does not wait** — it prepares the next slice or implements an already-`READY` one. **Not claimable** |
| **`REVISION REQUESTED`** | **Lane C, on review.** Governance requires a change and **the reasons are named**; the package returns to `PREPARING`. **Deliberately not `CHANGES REQUESTED`**, which is QE's word for an implementation that did not hold — **different authority, different stage, different subject** |
| `CLAIMED` | A lane holds it. The lane is named here, and [`ACTIVE_ASSIGNMENTS.md`](ACTIVE_ASSIGNMENTS.md) carries the detail. **Implementation begins immediately** |
| `IN PROGRESS` | Being built. **A claim flows straight into this** — there is no waiting state between them |
| `IN VALIDATION` | **Implemented and pushed.** Set by the implementing lane, the moment the work exists as commits QE can take. **The lane's responsibility ends here and it claims its next task immediately** |
| `CHANGES REQUESTED` | **QE**, during validation. Returned to the implementing lane with the corrections named; that lane fixes them and sets `IN VALIDATION` again |
| `VERIFIED` · `CERTIFIED` · `PROMOTED` | QE's stages, and **only QE's** — validation passed, `make certify` passed, `main` fast-forwarded |
| `WAITING` | Needs a **decision** from the product owner or another lane. **Named, always** |
| `BLOCKED` | Needs a **capability** that does not exist yet. **The capability is named** |
| `DONE` | Promoted to `main`. Removed at the next Closeout |
| `SEQUENCED` | **Prepared, and waiting on a named trigger** — not `WAITING`, because nothing is undecided, and not `READY`, because nothing may be claimed. **The trigger is stated in the row and is checkable** *(added 2026-08-04, [D-042](DECISION_REGISTER.md))* |

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

### TASK-434 · An account can be asked whether it matches a criterion, and only one thing answers

| | |
|---|---|
| **Discovery** | **[443](architecture/443-account-matching-capability.md)** — the first assessment produced under [D-075](DECISION_REGISTER.md)'s Product-Led Domain Discovery |
| **Milestone** | **Domain** ([D-075](DECISION_REGISTER.md)'s separation) — **not Intelligence, not Customer Experience.** It renders nothing |
| **Module** | ⚠️ **`commercial_profile` — and *not* because [TASK-406](#task-406--a-iv--an-icp-criterion-is-scored-against-outcomes) needs it first.** **The criterion vocabulary is defined there** (`industries` · `countries` · `EmployeeRange` · `validate_criterion_list`) **and evaluating elsewhere means a second copy of it** |
| **Status** | **`PROMOTED` — QE, cycle 67, 2026-08-05**, certified at `6b7b04e` and on `main`. **Both slices delivered**: `IcpReader`/`IcpView` published, and `evaluate` pure in `domain/matching.py`. ⚠️ **Known limitation, declared by the lane: no screen asks the question yet.** Claimed at the head of the queue. ✅ **`READY`, placed here by the product owner** ([D-077](DECISION_REGISTER.md)) — **and it is the capability [C-330](LANE_COORDINATION.md) asked for.** This lane raised C-330 by refusing to invent matching inside TASK-406; the product owner broadened it to a foundational capability, Product Office assessed it in [443](architecture/443-account-matching-capability.md), and it returns here as a specified row. **The loop closed the way the governance says it should** |
| **Why it is at the head** | ⚠️ **[TASK-406](#task-406--a-iv--an-icp-criterion-is-scored-against-outcomes) is `IN PROGRESS` and its acceptance criterion is *"the backtest reports both cohorts, never in-ICP alone"* — which requires this predicate.** **Measured 2026-08-05: no matching code is on `integration`, so the first copy has not been written.** **Sixteen consumers would inherit whichever interpretation one backtest happened to need** |
| **The insight that makes it fit** | **The import contract forbids `commercial_profile` from *reading* the pipeline. It does not forbid it from being *given* facts.** **`evaluate(criteria, attributes) -> tuple[CriterionVerdict, ...]` is pure** — it imports nothing, queries nothing, knows no module, and **the caller supplies the attributes**. ✅ **Zero new dependency edges. `lint-imports` needs no amendment** |
| **Two slices** | **① Publish `IcpReader` + `IcpView` from `commercial_profile/public/`.** ⚠️ **Thirteen views are published and not one is the ICP — no module can read the criteria at all today.** [ADR-0403](architecture/adr/0403-signal-engine-reads-a-declaration.md) is the ratified precedent for this exact shape. **② The pure evaluation** |
| **⛔ The invariant it inherits** | **A match is a category with reasons and is never a number.** `MatchStrength` — *"a semantic category, never a number"*, ratified 2026-07-29 — and `Relevance`: *"a number invites weighting, weighting invites thresholds, and a threshold here would be a propensity judgement in the wrong module."* **A fit score would be a second propensity model competing with `buying_score_engine`** |
| **⛔ And the one that must be in the type** | **`unmeasured`, never `false`.** The customer declares free text — *"validated, never normalised"* — and the pipeline observes canonical `INDUSTRY`. **`SaaS` versus `Computer Software` returns `False` under string equality and the account silently drops out of its own ICP.** **A matcher that says `false` where it means *I could not tell* produces a smaller ICP, a cleaner backtest and a wrong answer**, and it is invisible from the result |
| **Not in scope** | **No synonym catalog** *(443 M1 — build it when `unmeasured` shows it is losing accounts, and it is a **reviewed catalog**, never a model)* · **no discovery** *(M3 — [50 §23](architecture/50-sales-engagement.md) already classifies the trigger)* · **no lift, no backtest** *(M4 is TASK-406 and is a **consumer** of this, not a sibling)* · **no fit score** |
| **Consumers, measured** | **16** — ICP Builder · TASK-406 · `FitDimension` *(already written down in [50 §23](architecture/50-sales-engagement.md))* · Account 360 · Companies · Segments · Executive Dashboard · Opportunity prioritization · Buying Score · AI Copilot · AI Reasoning · AI Research cohorts · Recommendations · Reports · **Workflow rule conditions** · **Epic E1 CRM arrival**. **Four were on no list** |
| **Governance** | 🟠 — **the module's own `public/`, announced in the commit message.** **Not 🔴: no new bounded context, no new edge, no ADR** |

### TASK-300 · Epic A — surface what already exists

| | |
|---|---|
| **Module** | **Six slices across four modules** — see the table below. **Not one claimable unit**, which is the finding |
| **Slice** | A4 · A1 · A2 · A5 · A6, specified in [51-implementation-specifications.md](architecture/51-implementation-specifications.md) |
| **Status** | **`IN VALIDATION` — Lane B**, 2026-08-03. **A4, A1 and A5's backend are pushed**; **A2 and B2 were struck as already built by Lane A**; **A6 is held on [C-321](LANE_COORDINATION.md)**, which is the product owner's. Claimed 2026-08-03 on the product owner's direct assignment, and recorded here by Lane B because the row did not exist |
| **Notes** | **Verified against Lane A's branch before claiming, not against this register.** Of the six slices, **one is built, one is substantially built by Lane A this week, and every remaining one needs at least one module Lane A holds.** [C-323](LANE_COORDINATION.md) carries the evidence and a recommendation |

| Slice | Verified status, 2026-08-03 | Blocked on |
|---|---|---|
| **A4** freshness | **Not built.** No `last_observed_at` in any router or component | `provider_platform` **public port** (Lane A) · the render (Lane A). The response composition is `opportunity_engine` — **Lane B's** |
| **A1** search | **Not built.** No search endpoint in any router; `/account-identities` names ids you already hold and is not a lookup | The shell (Lane A) · **and the endpoint has no owning module yet** |
| **A2** accounts list | **Substantially built by Lane A**, `SW-01`…`SW-04`, this week — `TriageStrip`, `lib/state/triage.ts`, URL-driven narrowing | **Nothing. It is being delivered elsewhere** |
| **A5** company history | **Not built.** `claim.observed_at` holds the series; nothing exposes it | The render (Lane A). **Backend is `knowledge_graph` — unassigned** |
| **A6** needs identity | **Not built.** `AccountIdentityResponse.agreement` is the raw material | The render (Lane A). **Backend is `knowledge_graph` — unassigned** |
| **B2** first run | **Built by Lane A** — `first-run.test.tsx`, D36 | — |

> **Recorded 2026-08-03, and correct on that day.** *"This lane is not proceeding into Lane A's modules on the strength of a directive that predates the collision. One assignee per module is §20e's hardest invariant, and the product owner's own instruction in the same assignment was 'do not quietly bypass module boundaries.' [C-323](LANE_COORDINATION.md) asks which way to resolve it; the two backends in unassigned `knowledge_graph` are claimable meanwhile."*
>
> ✅ **Resolved 2026-08-04 by the consolidation ([D-058](DECISION_REGISTER.md)), and the caution is withdrawn.** **Every module named here is Lane B's**, so proceeding into them crosses no boundary and bypasses nothing. **[C-323](LANE_COORDINATION.md) asked which way to resolve a two-lane collision and there is no longer a collision to resolve** — it closes as overtaken, not as answered. **The whole of Epic A's remaining scope is one lane's**, which is what the row above could not assume when it was written.

### TASK-400 · Epic A completion — the surfaces that expose what the platform already knows

| | |
|---|---|
| **Epic** | **Epic A remainder**, [51-implementation-specifications.md](architecture/51-implementation-specifications.md). **Assigned whole, not sliced** |
| **Module** | `provider_platform` (A7) · Product Surface (A6 render) — **both Lane B's** *(consolidated to Lane B 2026-08-04 — [D-058](DECISION_REGISTER.md))* |
| **Status** | **`IN PROGRESS` — Lane A**, 2026-08-05. **A6's render is delivered and on the branch with QE**; **A7's render is not started and is waiting on [C-219](LANE_COORDINATION.md)**, which is now `READY FOR LANE C` because **the proposal this lane owed has been brought.** ⚠️ **The task is not complete and is deliberately not `IN VALIDATION`** — a row covering two halves must not report the state of the finished one. Claimed 2026-08-05 by the Task Claim Protocol. ⚠️ **The row's own condition — *"not claimable until one is answered"* — is satisfied: [C-321](LANE_COORDINATION.md) is `RULED` (2026-08-05, Lane B's six answers adopted whole) and [C-219](LANE_COORDINATION.md) is `RULED` (2026-08-05, *"no Product Owner decision required"*). **Both**, not one.** **A6's render is buildable now.** **A7's render is not, and the thing holding it is this lane's own**: C-219 records that *"Lane A will bring Lane C a proposal rather than assume one"* for the `subject`↔entity join, and **no proposal has been brought.** That is an obligation, not a blocker owned elsewhere. Previously **`CHANGES REQUESTED` — `provider_platform`'s assignee**, which [`modules.toml`](coordination/modules.toml) records as **Lane A**; **the return reason is spent** — [B-107](BUGS.md) is `FIXED` and QE-`VERIFIED`. ⚠️ **Corrected 2026-08-05**: this row read *"transferred to Lane B"* under [D-058](DECISION_REGISTER.md)'s consolidation, **which was written while Lane A was paused and is now three days stale.** Both of this row's modules — `provider_platform` and Product Surface — are Lane A's in the registry. **The row stored an assignee; the registry is the only place a lane's name is an answer** ([C-412](LANE_COORDINATION.md)'s correction). **A7's backend shipped** at `d8f5832`; the return was [B-107](BUGS.md), **now `FIXED` and QE-`VERIFIED`, so the original return reason is spent.** What remains is two rulings: **A7's render on [C-219](LANE_COORDINATION.md)** (Lane C, the `subject`↔entity join) and **A6 on [C-321](LANE_COORDINATION.md)** (the product owner). **Not claimable until one is answered** |
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

| | |
|---|---|
| **Recorded here by Lane A on claiming** | **The row is Lane C's, copied verbatim from `lane-c-product-office` at `c681ab9`**, with only `Status` changed. It did not exist on `integration`, and under the product owner's direction of 2026-08-03 **a lane claims on Lane C's assignment rather than waiting for the row to arrive** — Lane C is the source of truth for assignment, `integration` for claims and history. **No scope was added, reworded or reordered**; if Lane C's wording moves, Lane C's wins |
| **Known gate** | **[B-400](BUGS.md) is 🔴 and blocks promotion for every lane.** It does not block implementation, and Lane C did not gate this row on it — unlike [TASK-401](#task-401--a5-backend--a-companys-history-from-the-claims-that-already-hold-it) and [TASK-402](#task-402--epic-e1--a-customers-crm-becomes-a-source-signora-can-read), which it marked `READY — after B-400`. **A7 adds a migration, so this lane expects to renumber on rebase and will say so** |

### TASK-402 · Epic E1 — a customer's CRM becomes a source Signora can read

| | |
|---|---|
| **Epic** | **E1**, [51-implementation-specifications.md](architecture/51-implementation-specifications.md). **Assigned whole** |
| **Module** | `integrations` — **Lane B's**, which built S01, S02 and S09 |
| **Status** | **`IN VALIDATION` — Lane B**, 2026-08-04, pushed at `605e76f`. **Resumed the moment [C-326](LANE_COORDINATION.md) was ruled.** **[ADR-0300](architecture/adr/0300-inbound-customer-systems.md) Option A approved by the product owner** — ⚠️ **awaiting integration synchronization**, so the work is held on the lane branch — and [409](architecture/409-inbound-source-port-contract.md)'s steps 1, 2 and 6 are built: the inbound source port, `Capability.CRM_RECORDS`, and `HubSpotCompanySource`. **Steps 3, 4 and 5 are `provider_platform`'s and were not touched** — [C-300](LANE_COORDINATION.md) asks who builds them. Everything before this remains as recorded: **Shipped around the blocker**: `HubSpotCompanyMapper` translates a customer's CRM into canonical claims with **no vocabulary extension**; `POST /connections` exposes a use case that had been complete and unreachable since S01 — which found that **disconnect was irreversible** and fixed it with the lifecycle already in the domain; the grant lifecycle gained revocation, refresh-on-use and `EXPIRED → CONNECTED` revival; and `HubSpotCompanies` reads the vendor behind typed failures. **What is left is one signature, not engineering** — the Provider Port cannot express a customer-held system, so nothing can put a record in front of that mapper until the inbound source port exists. *(That gate is now answered — [C-326](LANE_COORDINATION.md) was ruled on 2026-08-04 — and the sentence is kept as the dated record of what was true before it, §2.)* |
| **Assigned** | **Lane B, directly by the product owner, 2026-08-04** — *"Your next major initiative is Epic E1 — CRM Integration… own this epic end-to-end."* Lane C had prepared the row and marked it `READY — after [B-400](BUGS.md)`; **the product owner's sequencing supersedes that gate and is recorded here rather than argued** |

**Why this epic.** Lane C verified it against the catalog before offering it: of D1's four risk families, **`contraction_risk` and `decision_maker_departed` already exist**, and the two that do not — *usage decline* and *renewal approaching* — **need contract and usage data that only a CRM carries.** **Epic D is gated on this epic**, so this one comes first. D3's own specification says *"depends on E1"*.

**The reuse audit changes the size.** The specification calls E1 **XL**; **most of the connection half is already built** — OAuth start and callback (`frontend/app/api/integrations/[slug]/{start,callback}/route.ts`, a separate OAuth client from Better Auth's), connection, grant, catalog, resolve, connect and disconnect (`modules/integrations/{domain,application}`), encrypted credential storage (`infrastructure/secrets.py`, migration `0028`), and the public contract, router and schemas.

> **What remains is the *read*, not the plumbing:** a CRM adapter behind the existing port, normalization of accounts and opportunities into the canonical shape, and the events that carry them.

| | |
|---|---|
| **Customer value** | The specification's own words: **the single highest-leverage integration in the roadmap — it unblocks pipeline intelligence, forecasting, expansion and customer risk on its own** |
| **Unblocks** | **D3** directly · **D1's** two missing risk families · **E2** write-back · the whole expansion and renewal half of the vision |
| **Non-negotiable** | **A sign-in OAuth token must never be reused as an integration token** (§13). Separate grants, separate scopes, separate storage — **already the shape `integration_secret` and the separate OAuth client enforce** |
| **On claiming** | **Provider Normalization owns the canonical shape**, not `integrations` — a CRM payload is normalized the same way a provider payload is (§10, the anticorruption layer). **Do not invent a second normalization path**; open a `C-` item if the existing one does not fit |
| **Recorded here by Lane B on claiming** | **The row is Lane C's, copied from `lane-c-product-office`**, with `Status` and `Assigned` changed to record the product owner's direct assignment and this claim. It did not exist on `integration`. **No scope was added, reworded or reordered**; if Lane C's wording moves, Lane C's wins |

### TASK-301 · Global Search — a result says what kind of thing it is, and why it matched

| | |
|---|---|
| **Recommendation** | **[417 §4, slice B-i](architecture/417-executable-slice-audit.md)** — *"Global Search — typed grouping and explainable ranking over accounts"*, Lane C, 2026-08-04. **The only slice Lane C describes as Lane B's clean, unambiguous capacity**; B-ii, the saved-view store, is **not** taken here because Lane C attached a placement caveat to it and placement is the product owner's |
| **Module** | **`knowledge_graph`** — Lane B's, which built `account-search` |
| **Slice** | one slice |
| **Status** | **`IN VALIDATION` — Lane B**, 2026-08-04. Pushed at `e5f48d2`. **The matched name was already being read and discarded** — it is what `ORDER BY` sorts on — so the explanation cost a field rather than a query. `is_renamed` is what keeps it readable: only a row whose match is invisible in its own text is annotated. **The grouped rendering is deliberately not built** and is recorded as a limitation: one type is reachable by this search, and a branch no production data can enter is Decorative Logic (§2) |
| **Assigned** | **Lane B**, on **Lane C's recommendation** and the product owner's standing direction of 2026-08-04 — *"I want to work on tasks given by Lane C"* |
| **What is missing** | `GET /account-search` returns a **flat, untyped list ordered by matched name**. The approved Global Search screen needs a result to say **what kind of thing it is** and **why it matched** — and this endpoint's own docstring names the reason: *"a result may not visibly contain the search text, and that is the feature rather than a bug to hide."* **A row a customer cannot explain is a row they will not click** |
| **In scope** | Typed grouping over the object types that exist today · the matched name carried onto the result so a rename is explicable · a deterministic, stated ranking |
| **Not in scope** | **People, calls and deals.** People is blocked on [C-221](LANE_COORDINATION.md) and calls need conversation intelligence, which has never existed. **The approved specification's own structure allows a group to be absent** ([411 §3d](architecture/411-ui-convergence-assessment.md)) — the absent groups are not stubbed, and the endpoint must not imply it searched something it did not |
| **On claiming** | **Extend the existing endpoint's vocabulary; do not add a second search path.** `account-search` already refused to become `/account-identities` with a parameter, and the reasoning binds in this direction too. **Nothing here ranks by relevance a model invented** — the ordering stays derivable and repeatable (§2, *determinism outranks convenience*) |
| **Position is not a priority claim** | Placed beside the other Lane C-prepared Lane B row rather than at a rank. **Lane C's own order puts it fourth** ([417 §6](architecture/417-executable-slice-audit.md)); if the product owner wants it elsewhere in this queue, the position is theirs to set |
| **Recorded here by Lane B on claiming** | **The slice is Lane C's, quoted from `lane-c-product-office` at `9d72630`.** It did not exist on `integration`, and under the product owner's direction of 2026-08-03 **a lane claims on Lane C's assignment rather than waiting for the row to arrive.** **No scope was added, reworded or reordered** |

### TASK-407 · B-i — a connection says whether it actually works

| | |
|---|---|
| **Objective** | **A connection reports whether its credential still works, not whether its record still looks right.** Today a token that is structurally valid but has lost a permission reads as healthy |
| **Module** | `integrations` — **Lane B's**, via TASK-402 |
| **Status** | **`IN VALIDATION` — Lane B**, 2026-08-04. Pushed at `da874a5`. **`ConnectionState.VALIDATED` was written for this and had never been reachable** — the state was correct and nothing performed the call that earns it. **The first draft revoked a connection whose credential was rejected and that was wrong**: `REVOKED` means the customer withdrew Signora at the vendor, and a rotated secret is indistinguishable from a `401`. Degraded health carries it instead. **Nothing enters the pipeline**, asserted by counting `raw_provider_record`, `claim` and `outbox_event` across a check |
| **Approved screen** | **CRM Integrations** — *"Health is checked every minute. Two consecutive failures pause writes"* |
| **Scope** | A reachability probe against the connected system using the stored credential, its outcome classified by the **existing** error taxonomy, and the result surfaced on the connection. **Two consecutive failures mark the connection as degraded** |
| **Dependencies** | **None, and this is the point.** ⚠️ **[C-326](LANE_COORDINATION.md) does not block it** — [419](architecture/419-c326-narrowed-and-lane-b.md) §2 measures C-326 as blocking exactly two artifacts, the source port and the runner. **This slice uses neither** |
| **Affected modules** | `integrations` only. Possibly one migration for the probe outcome |
| **Repository reuse** | **Everything it needs is built.** `ResolveExecutionContext` supplies the credential · **`HubSpotCompanies`** makes the call · `CrmTransient` · `CrmRateLimited` · `CrmCredentialRejected` · `CrmPayloadInvalid` · `CrmPermanent` already classify the outcome · `ConnectionResponse.attention` and `.reason` already exist to carry it. **Do not introduce a second error taxonomy** |
| **Non-goals** | **No pausing of writes** — there are no writes; that is E2. **No signal to admins** — notification delivery is [ADR-0040](architecture/adr/0040-notifications.md) and unratified. **No sync, no records read into the pipeline, no source port, no runner.** **No `connectable: true`** — that flips only after a real handshake, and never in anticipation ([44](architecture/44-integrations.md) §9) |
| **Acceptance** | A connection whose credential has been revoked or downgraded **reports degraded rather than healthy** · a transient failure does not degrade a connection on its own — **two consecutive** · the probe never writes a claim, a raw record or an event · **no credential material is logged** (§16) · workspace-scoped throughout |
| **Implementation order** | **First for this lane.** Independent of TASK-408 |
| **Validation** | Module suite · a test that a `CrmCredentialRejected` outcome degrades and a single `CrmTransient` does not · **a test that nothing enters the pipeline** |
| **Escalate if** | The probe needs a scheduler this repository does not have. **ARQ exists; a new scheduling mechanism is 🔴** |
| **Recorded here by Lane B on claiming** | **The row is Lane C's, copied verbatim from `lane-c-product-office` at `04faf32`**, with only `Status` changed. It did not exist on `integration`. **No scope was added, reworded or reordered** |

### TASK-408 · B-ii — search results are grouped and the ranking is explainable

| | |
|---|---|
| **Objective** | **A search result says what kind of thing it is and why it ranked where it did.** `account-search` returns a flat list |
| **Module** | `knowledge_graph` — **Lane B's**, via TASK-300 |
| **Status** | **`PROMOTED` — QE, cycle 66, 2026-08-05**, certified at `772eebe` and on `main`. ⚠️ **This row still read `IN PROGRESS` when the work reached `main`** — the lane never set `IN VALIDATION`, so QE set the terminal state it owns and records the gap rather than tidying it away ([B-124](BUGS.md)). Claimed 2026-08-05 by the Task Claim Protocol **the moment the ruling landed**. ✅ **The contradiction is ruled, 2026-08-05, product owner**: *"Return the group with zero matches rather than omitting it. The absence of results and the absence of the group represent different business meanings."* **Three states the UI must be able to tell apart, and they may not be collapsed**: **the group exists and contains zero matching accounts** · **the group is not applicable** · **the group was not requested.** ⚠️ **This supersedes [TASK-301](#task-301--global-search--a-result-says-what-kind-of-thing-it-is-and-why-it-matched)'s *"an absent type is absent, never an empty group"* for the grouped shape** — that decision collapsed all three into one, which is exactly what the ruling forbids. **Skipped four times with the reason recorded rather than chosen inside a slice**, and the ruling is why that was right: the answer is a three-state distinction no lane would have invented |
| **Approved screen** | **Global Search** — *"groups are typed and ordered by intent, never by score"*; *"within a group, score is a weighted sum of six factors, and the dominant one is shown on the row when it is not lexical"* |
| **Scope** | Typed grouping of results · a ranking whose **dominant factor is reported per row** · the ordering rule stated in the response rather than implied |
| **Dependencies** | **None.** `GET /workspaces/{id}/account-search` exists |
| **Affected modules** | `knowledge_graph` only |
| **Repository reuse** | The existing search endpoint and its query path. **`AccountIdentityResponse.agreement` already models identity confidence** and is the natural non-lexical factor — **reuse it rather than inventing a second confidence notion** |
| **Non-goals** | **No people, calls or deals as searchable types** — people are blocked by [O1](DECISION_PACKS.md), calls have no source, and deals are `opportunity_engine`'s. **No saved or monitored searches** — monitoring produces a notification, which is ADR-0040. **No natural-language routing to the assistant** — that is the Copilot's, and shell-scoped |
| **Acceptance** | Results carry their type and are grouped by it · **the dominant ranking factor is present on a row whenever it is not lexical** · **a zero-match group is returned rather than omitted** — the approved screen requires absence to be visible · ordering is deterministic for identical input (§2) |
| **Implementation order** | **Second for this lane** |
| **Validation** | Module suite · a test that identical input yields identical order · **a test that an empty group is returned, not dropped** |
| **Escalate if** | Grouping requires reading another module's tables. **Never permitted** (§5) — open a `C-` item |
| ⚠️ **Reported by Lane B, not rescoped** | **[TASK-301](#task-301--global-search--a-result-says-what-kind-of-thing-it-is-and-why-it-matched) delivered part of this an hour before the row was drafted**, and was promoted in cycle 46. Already shipped: **every result carries `result_type`**, read from the entity rather than assumed · the **matched name and its source** on every row, with `is_renamed` marking the rows where it differs from the displayed name · **deterministic ordering, stated in the response schema**. **Lane C measured against an `integration` that predates the promotion.** Still outstanding: the **grouped shape**, and the **dominant ranking factor** — which needs the six-factor score the approved screen names, and TASK-301 deliberately shipped none. **The row is left `READY` and its scope untouched**; deciding what remains of it is Lane C's and the product owner's, not this lane's |
| ⚠️ **One acceptance criterion contradicts a shipped decision** | *"A zero-match group is returned rather than omitted"* is the opposite of TASK-301's *"an absent type is absent, never an empty group"*, and **both may be right about different cases**: an empty group is honest for a type Signora **searched** and found nothing in, and false for a type it **cannot search at all** — `people: []` would claim it looked. **Flagged rather than resolved**, because reconciling an approved screen with a shipped decision is a product ruling |
| ⏭️ **Skipped by Lane B, 2026-08-05, with the reason recorded** | **This was the highest `READY` row and it was not taken.** Building the grouped shape means choosing between the two rules above, and **choosing is the ruling itself** — a lane that picks one has made the product decision inside a slice, which is the failure §2 names (*governance describes reality; it never quietly changes it*). The row's own note already says deciding what remains of it is Lane C's and the product owner's. **[TASK-202](#task-202--epic-g--copilot) was claimed instead**, and the skip is recorded here rather than performed silently, because **a silent skip is a re-prioritization and priority is the product owner's** (§20e) |

### TASK-200 · CX-07 — the Responsive Product Surface

| | |
|---|---|
| **Epic** | **CX-07**, [43-customer-experience.md](architecture/43-customer-experience.md) §6. **Assigned whole, not sliced** |
| **Module** | **Product Surface** — every screen, plus the application shell |
| **Status** | **`IN VALIDATION` — Lane A**, 2026-08-03. **All four slices shipped**; [B-203](BUGS.md) fixed and the supported viewport recorded in [43 §4a](architecture/43-customer-experience.md) |
| **Assigned** | **Lane A, directly by the product owner, 2026-08-03** — *"I want Lane A to complete the Responsive Product Surface (CX-07) first"*. **Priority is the product owner's**; this row records the assignment rather than creating it |
| **Unblocked by** | **[C-205](LANE_COORDINATION.md), ruled 2026-08-03: a phone is in scope.** That item's own analysis then binds — **this is a milestone, not a slice** |
| **Scope** | The shell's navigation below `768px` · every screen's layout · the account brief's eleven sections in one column · touch targets and focus order · the interaction patterns that differ on a small viewport |
| **Makes [B-203](BUGS.md) a defect** | It was 🟠 *"an unreachable control — whether it is a defect or a non-goal depends on a product decision nobody has made"*. **The decision has been made.** §20c permits a foundation change for exactly this: *"an accessibility issue — a missing label, an unreachable control, a lost focus state. These are defects, not enhancements"* |
| **On claiming** | **The frontend foundation is frozen (§20c) and this touches it deliberately and narrowly.** Every such change is announced in its commit message with the ruling that permits it. **No shared component is bent to suit one page** |

### TASK-201 · Epic C — People Intelligence

| | |
|---|---|
| **Epic** | **Epic C**, [ADR-0400](architecture/adr/0400-person-as-an-entity.md) · [400-epic-c-people.md](architecture/400-epic-c-people.md). **Assigned whole** |
| **Module** | **A new bounded context — `people`** · `knowledge_graph` (`EntityKind.PERSON`) · `commercial_profile` (a stable role id, Lane B's) · Product Surface |
| **Status** | ✅ **`READY` — unblocked 2026-08-05, at narrowed scope.** **[C-221](LANE_COORDINATION.md) `APPROVED WITH MODIFICATION`**: *"**Do NOT expand the architecture around people until we have a reliable provider capability.** Epic C should initially focus on **role-based and organization-level intelligence**. Treat named-person intelligence as a future enhancement once supported by provider capabilities. **Avoid speculative architecture.**"* ⛔ **So no `people` bounded context is created**, and nothing models a person's name — **the platform ingests none** ([ADR-0400](architecture/adr/0400-person-as-an-entity.md) ❓1 checked and answered *no*). **What is buildable is what the data already carries**: `title`, `seniority`, `direction`, `occurred_on` |
| **Decomposed 2026-08-05 — [D-074](DECISION_REGISTER.md)** | **Epic C is four milestones, not one**: **[TASK-427](#task-427--m-d--the-people-domain--a-person-and-an-affiliation-with-an-end)** M-D domain · **[TASK-428](#task-428--m-i--what-the-domain-lets-other-modules-say)** M-I intelligence · **[TASK-429](#task-429--m-e--a-provider-supplies-a-person-identifier)** M-E provider enrichment · **[TASK-430](#task-430--m-u--the-people-experiences-a-customer-opens)** M-U the screens. **This row is not replaced and does not move** — its status, its position and its assignment are exactly as the product owner left them, because **position is priority and priority is not Lane C's.** ⚠️ **The one correction the decomposition makes to the row above: *"Assigned whole"* is no longer true of Epic C.** **A claim on this row means TASK-427 first and TASK-428 S3 second, in that order** — which is a statement of fitness ([D-060](DECISION_REGISTER.md)), never of priority |
| **Assigned** | **Lane A, directly by the product owner, 2026-08-04**, on Lane C's prepared research, ADR and specification |
| **Blocked by** | **[C-221](LANE_COORDINATION.md) — ADR-0400's own ❓1, checked first as the ADR instructs, and the answer is *no*.** The platform receives no person name at any point, so an identity model has nothing to identify. ⚠️ **Narrowed 2026-08-05 by [441 §1](architecture/441-people-roadmap.md): ❓1 gates [TASK-429](#task-429--m-e--a-provider-supplies-a-person-identifier) and everything after it. It does not gate the entity** — an anonymous `Person` with `Affiliation` intervals identifies a role at a company over a period, which is what the pipeline already produces and has nowhere to put |
| **On claiming** | ⚠️ **Stale, and dated rather than rewritten — [B-205](BUGS.md).** This read ***"ADR-0400 is `PROPOSED`, not ratified, and it says so in its own status block"***, **which was true when written on 2026-08-04 and the ADR moved the same day.** **Its status block reads `PRODUCT OWNER APPROVED`.** **What remains true is the sentence's point**: a new bounded context is 🔴, and **the product owner's approval is [D-074](DECISION_REGISTER.md)** — not this ADR's ratification stamp. A new bounded context is 🔴. The product owner's assignment is the epic approval; **the ADR still needs its ratification stamp, which only the product owner can apply** |

### TASK-202 · Epic G — Copilot

| | |
|---|---|
| **Epic** | **Epic G**, [404-epic-g-copilot.md](architecture/404-epic-g-copilot.md). **Assigned whole** |
| **Module** | `ai_reasoning_engine` · `ai_platform` (evaluation) · Product Surface |
| **Status** | ✅ **`READY` — unblocked 2026-08-05, verified on `origin/integration` rather than inferred from a row.** **Both blockers landed**: `infrastructure/adapters/mock.py` exists, `AIVendor.MOCK` is in the enum, and `provider` appears on the evaluation report. **[C-222](LANE_COORDINATION.md) was ruled 2026-08-04** — the evaluation provider is configurable and `reasoning@1` is re-evaluated under a chosen provider — **and [TASK-415](#task-415) and [TASK-416](#task-416) are the mechanism that ruling depends on.** ⚠️ **They read `IN VALIDATION`, which is not the same as promoted** — so this was checked against the tree a lane claims from, not against their status. **The code is there** |
| **Why it is blocked, measured rather than cited** | **Lane B reproduced Lane A's run independently on this workstation and got the committed policy's answer**: `UNMEASURABLE — 2 of 2 cases never reached a verdict`. [404 §0](architecture/404-epic-g-copilot.md) records the same pairing passing at **172.8 s for two cases**; `InferencePolicy.timeout_seconds` is **60.0** (`ai_platform/application/infer.py:79`). **The prompt is not the problem and the model is not the problem** — the only change that makes it pass is the one [TASK-013](#task-013) forbids in writing. **Every later phase depends on this one**: phase 2 needs a hosted-model evaluation ([C-410](LANE_COORDINATION.md)), phase 3 needs `require_model` to accept `reasoning@1`, phase 4 needs Epic C. **So the epic is blocked whole, not partly** |
| **Two corrections to [404](architecture/404-epic-g-copilot.md), found by claiming it** | ⚠️ **§3's *"`ai_reasoning_engine` has no `interface/` directory at all"* is stale** — [TASK-204](#task-204--a-i--the-ai-reasoning-engine-reaches-a-customer) built `router.py` and `schemas.py` and they are on `integration`. **G1 lacks the *ask* route, not the layer.** ⚠️ **The `reasoning` dataset half was not built, and deliberately.** Lane C withdrew it themselves — *"two things were bundled and only one mattered"* — and authoring one now would put a **second copy of an evidence set the module shares on purpose**: *"reasoning and narration operate over the identical closed evidence set and a second copy would be a second thing to keep in step"* (§2) |
| **Assigned** | **Lane B**, 2026-08-05, by claim. Approved by the product owner 2026-08-04; **approval survives the transfer, the claim does not.** No ADR: no boundary moves and every decision it needs is already ratified |
| **Validated on claiming** | **Every claim in Lane C's preparation checked against the manifests, and all hold.** `reasoning@1` has four recorded evaluations, **all against `explanation_narration`'s dataset**, on 2B and 3B models; **no `reasoning` dataset exists**; the three sibling prompts hold protocol-2 releases on `llama3.1:8b` at coverage 1.0 with zero grounding failures; and **all twelve evaluations across four manifests are Ollama models** |
| **First slice** | **Author a `reasoning` dataset and evaluate `reasoning@1` under protocol 2** — the work [TASK-013](#task-013) records as a product decision when it is a measurement nobody has taken |
| **Known workstation limit** | ⚠️ **`llama3.1:8b` was measured *unmeasurable* on this machine during SE-09c** — 7 of 10 calls exceeded the 90s budget and the harness abandoned the run. The pinned model is part of the benchmark and is **not** a lane's to change ([ADR-0028](architecture/adr/0028-model-runtime-by-environment.md)); reported as an observation about the machine |

### TASK-203 · Epic D — Risk Intelligence

| | |
|---|---|
| **Epic** | **Epic D**, [403-epic-d-risk.md](architecture/403-epic-d-risk.md). **Assigned whole**; Phase 1 is the independent slice |
| **Module** | `commercial_profile` (a fifth declaration) · `signal_engine` (a catalog row) · Product Surface |
| **Status** | ✅ **`DISPOSED` — Lane C, 2026-08-05.** Claimed by Lane B and **released the same day without a line of code, because the reuse audit the row itself demands found the work built.** **The row's own finding is decisive**: *"Epic D has no unbuilt, unblocked slice under this task id."* **Phase 1 is [TASK-905](#task-905)**, phase 4 needs E1 and phase 5 needs Epic C. **Removed from the eligible set rather than left `READY`** — a `READY` row nobody can start is the [C-412](LANE_COORDINATION.md) defect, and this office wrote C-412. **Epic D itself is not closed**; only this id stops advertising work that is built or blocked elsewhere |
| **The audit the row asked for, and what it returned** | The row says: *validate that `competitor` genuinely appears nowhere.* **It appears everywhere it would need to.** `commercial_profile/application/declare_competitors.py` calls itself **the sixth write in the module**, so the *"fifth declaration"* is neither new nor fifth · `domain/competitors.py` holds the aggregate · `public/` already exports `DeclaredCompetitorView`, `DeclaredCompetitorListView` and `DeclaredCompetitorReader` · `signal_engine` **already injects that reader** (`application/generate.py:81`, `infrastructure/composition.py:31`) and resolves the declared set at `generate.py:116` · `DetectionStrategy.DECLARED_MATCH` exists and is documented for exactly this case — *"adopting a rival is grounds; adopting anything else is not"* · `_declared_match` is implemented in `domain/rules.py:110` · the catalog row is at `catalog/signals@1.json` with `declared_match`, `technology_adopted`, a 180-day window and four recorded limitations · the weight and posture are in the reviewed scoring catalog — **`competitor_entry`, `contractionary`, `base_weight` 25** · the screen is `frontend/components/commercial/competitors.tsx` with its own test. **[403 §6](architecture/403-epic-d-risk.md) phase 2 is *"a fifth declaration + its screen"* and phase 3 is *"catalog row, weight, posture, detection"* — all seven elements exist** |
| **Verified by running, not by reading** | `pytest tests/signal_engine/test_generate.py -k "ompetitor or eclared"` → **8 passed**. The cases already cover the ones that matter: a declared rival is grounds · an undeclared adoption is not · a workspace that declared nobody grounds nothing · a workspace never asked grounds nothing · the match folds case and space · **and it resolves nothing beyond that**, deliberately, because a cleverer comparison here would disagree with the module that owns resolution |
| **What is actually left of Epic D** | **Phase 1 is [TASK-905](#task-905), a separate `READY` row this lane did not claim** — the row's own *"cheaper half"* note. **Phase 4 needs [E1](#task-402--epic-e1--a-customers-crm-becomes-a-source-signora-can-read)** for contract dates and **phase 5 needs Epic C** for a named champion; both are blocked elsewhere and neither moved. **Usage decline was already recommended out of scope.** So Epic D has no unbuilt, unblocked slice under this task id |
| **Assigned** | **Lane B**, 2026-08-05, by claim. Approved by the product owner 2026-08-04; **approval survives the transfer, the claim does not.** No ADR, deliberately: no boundary moves, no new bounded context, no new dependency |
| **First slice** | **Competitor entry** — the customer declares which technologies are competitors; `TECHNOLOGY_ADOPTED` for a declared competitor raises a **contractionary** `competitor_entry` signal, and the account becomes `contested`. **The detection half already exists** |
| **On claiming** | **Validate before building**, in this order: that `competitor` genuinely appears nowhere · that the four existing declarations share one shape a fifth can follow · that `TECHNOLOGY_ADOPTED` carries a resolvable technology identity rather than a free string · and that **no threshold enters code** — `signal_engine` keeps them in a reviewed catalog |
| **Not in scope** | **Usage decline** — Lane C recommends dropping it and Lane A agrees on the evidence: it needs product telemetry the platform has never had. **Champion departure** is blocked on Epic C (no person name exists); **renewal approaching** on E1 (only a CRM knows contract dates) |
| **Related** | **[TASK-905](#task-905) delivers most of Epic D's visible value with no new signal** — two contractionary signals already score and the attention list does not distinguish them. Not claimed here; reported as the cheaper half |

### TASK-204 · A-i — the AI Reasoning Engine reaches a customer

| | |
|---|---|
| **Recommendation** | **[417 §4, slice A-i](architecture/417-executable-slice-audit.md)** — *"`interface/` for `ai_reasoning_engine`"*, Lane C, 2026-08-04. **Priority 1** in [417 §6](architecture/417-executable-slice-audit.md) |
| **Module** | `ai_reasoning_engine` — **Lane B's** *(consolidated to Lane B 2026-08-04 — [D-058](DECISION_REGISTER.md))*, via [TASK-202](#task-202) |
| **Slice** | one slice |
| **Status** | **`IN VALIDATION` — Lane A**, 2026-08-04 |
| **Assigned** | **Lane A, by the product owner, 2026-08-04** — *"The Product Owner approves the READY implementation slices prepared by Product Office. Claim the READY items in priority order."* |
| **What was missing** | **The module concluded and nothing could read the conclusion.** `domain/` and `application/` were complete — `Reason` produces a Decision Package, stores it and publishes `ReasoningCompleted` — with **no `interface/` directory**, so no endpoint existed. It was one of only two modules in the repository without one |
| **The claim-time scope correction was itself wrong, and is withdrawn** | On claiming, this row recorded that 417 names the reuse as *"the module's own `public/`"*, that the surface is empty, and that **the slice was therefore larger than 417 stated.** ⚠️ **It was not.** An interface layer serves its **own** module's use cases and is not a cross-module consumer, so it imports `application/` and `domain/` directly — as all six existing interface layers do. `public/` stays empty and `test_the_public_contract_exports_nothing_yet` still holds. **417's estimate was right and mine was wrong**; recorded here rather than quietly deleted |
| **Delivered** | `GET /workspaces/{id}/accounts/{id}/decision-package` — the latest conclusion, its citations, what argues against it, what it cannot see, how to check it, and what produced it. **One route, and it is a read.** No domain change, no migration, no new event, no `public/` change |
| **In scope** | A read path to a Decision Package a customer already owns · whatever the module must publish for its own interface layer to serve it · the endpoint conventions of [19-api-conventions.md](architecture/19-api-conventions.md) |
| **Not in scope** | **Triggering reasoning from a request.** §7 forbids an endpoint that synchronously starts pipeline work, and `Reason` is dispatched by the pipeline. **No new inference, no second call path, no cross-account ranking** — the module's `public/` docstring rules all three out |
| **On claiming** | **Follow the six existing interface layers; do not invent a seventh shape.** The response is a purpose-built schema, never a domain type (§7). **Nothing here re-derives a fact the package already holds** — a Decision Package is a composition of fifteen parts and fourteen of them were authored by somebody better placed to be right |

### TASK-205 · A-ii — Sales Engagement reaches a customer

| | |
|---|---|
| **Recommendation** | **[417 §4, slice A-ii](architecture/417-executable-slice-audit.md)** — *"`interface/` for `sales_engagement`"*, Lane C, 2026-08-04. **Priority 1**, paired with [TASK-204](#task-204) |
| **Module** | `sales_engagement` — **Lane B's** *(consolidated to Lane B 2026-08-04 — [D-058](DECISION_REGISTER.md))*. Built by Lane A ([50-sales-engagement.md](architecture/50-sales-engagement.md)) — **authorship does not move assignment, and assignment does not move authorship** |
| **Slice** | one slice |
| **Status** | **`IN VALIDATION` — Lane B**, 2026-08-05, pushed at `ce95e5e`. **The module is reachable for the first time**: `GET /workspaces/{id}/accounts/{id}/approach` returns the ranked committee, the evidence behind each seat, what the platform cannot answer and what argues against approaching. **[C-213](LANE_COORDINATION.md) is answered by code** — the export it asked for exists; closing it belongs to the requesting lane. ⚠️ **One asymmetry recorded rather than changed**: with a product override and no evidence a seller sees every role and why each is unranked; without one `_widest` returns `()` and they see none. **A domain decision this slice does not own, and every new workspace meets it.** Claimed **after [TASK-203](#task-203--epic-d--risk-intelligence)'s first slice was found already built.** **Unblocked 2026-08-04 by the consolidation.** It waited on [C-213](LANE_COORDINATION.md), the Buying Committee export from `commercial_profile.public`, **which was a cross-lane dependency only for as long as there were two lanes.** `sales_engagement` and `commercial_profile` are now the same assignee, so **the export and its consumer are one lane's change** — the adapter `application/ports.py` predicted: *"a separate, small change once the export exists."* **This is the consolidation's one genuine unblocking, and it is the only one** |
| **Assigned** | **Lane A, by the product owner, 2026-08-04**, in the same ruling as [TASK-204](#task-204) |
| **What is missing** | **The contract is published and unreachable, and that is only half of it.** `public/` exports 39 names — `Approach`, `ApproachBrief`, `NextAction`, `Recommendation`, `Risk`, `ProductFit`, `RankedRole` among them — and the module has no `interface/`. **But `AssembleApproach` also requires three ports — `CommitteeReader`, `EvidenceReader`, `PortfolioReader` — and none has an implementation anywhere in the repository** |
| **Why it was blocked, and why it no longer is** | **Two of the three ports needed exports `commercial_profile.public` did not have** — nothing about the Buying Committee, nothing about the portfolio. That is [C-213](LANE_COORDINATION.md), opened by Lane A on 2026-08-03. `application/ports.py` predicted exactly this: *"the adapter that satisfies it is a separate, small change **once the export exists**."* **What made it a blocker was that the export and its consumer sat in two lanes** — writing it would have invented the shape of another lane's contract (§20e). **The 2026-08-04 consolidation removed that condition rather than answering the question**: one lane now holds both, so the export is an ordinary change inside its own module |
| **What 417 got wrong, recorded rather than absorbed** | ⚠️ **A-ii's reuse column reads *"25+ exported types, unchanged"* and rates the slice executable.** True of the contract, not of the module: the outward half was deliberately never written. **This is the second optimistic reuse column in 417 §4** — [TASK-204](#task-204)'s was optimistic in the harmless direction and this one is not |
| **In scope** | An interface layer over the module's **existing** `public/` · the endpoint conventions of [19-api-conventions.md](architecture/19-api-conventions.md) |
| **Not in scope** | **Any change to `public/`.** It is complete, 39 names, and this slice consumes it rather than growing it. **No new domain concept** — 417's own finding is that the pattern has never once required a domain change across six instances |
| **On claiming** | **Reuse before extension.** If a type the screen needs appears absent, it is more likely already exported under this module's vocabulary than genuinely missing (§4) |

### TASK-405 · A-iii — a signal ends in a decision

| | |
|---|---|
| **Objective** | **Every signal leaves the queue by being actioned, assigned, snoozed or dismissed with a reason** — and the resolution is durable and auditable |
| **Module** | `signal_engine` — **Lane A's again**, transitioned back on the 2026-08-05 resumption. **`coordination/modules.toml` records `current_owner = "Lane A"`, `transition = "settled"`** — this line said *Lane B's* and was stale, corrected on claiming rather than left to mislead the next reader |
| **Status** | **`IN VALIDATION` — Lane A**, 2026-08-05. **Every acceptance criterion is met except the route that records a decision**, which needs an authorization `Resource` that does not exist — **[C-224](LANE_COORDINATION.md)**, the product owner's, and the reason no tuple was reused is in the row. Shipped: the four outcomes as types, migration `0039` with forced RLS and its `tenancy_policy.py` registration, the repository, `ResolveSignal`, the workspace-scoped queue read by state, and the audit trail. **`CLAIMED` — Lane A**, 2026-08-05, by the Task Claim Protocol. **Claimed once before and released on the 2026-08-04 consolidation, carrying no code** — so nothing is inherited and nothing was lost |
| ✅ **The write route is unblocked** | **[C-224](LANE_COORDINATION.md) ruled 2026-08-05**: *"adding a new `Resource` enum member is a **declarative registration**, not an authorization grant. Authorization is granted only through `policy.csv`."* **So `Resource.SIGNAL` is a declaration this lane may make**, and the grant is a `policy.csv` row — the registry every lane already extends. **Recorded in `CLAUDE.md` §20a so it is not re-litigated** |
| **Assigned** | **Lane A, by the product owner, 2026-08-04** — *"you may proceed with A-iii and A-iv when their corresponding READY task rows exist on integration."* **The rows landed with Lane C's synchronization at `3ab3111`**, which is the condition the ruling named |
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
| ⏭️ **Skipped by Lane B, 2026-08-05, with the reason recorded** | **This was the highest `READY` row this lane could otherwise take.** [D-065](DECISION_REGISTER.md) resumes Lane A and **transitions `signal_engine` to it**, so claiming this would take a module the product owner has just reassigned. **Recorded rather than skipped silently, because a silent skip is a re-prioritization** (§20e). **[TASK-406](#task-406--a-iv--an-icp-criterion-is-scored-against-outcomes) was claimed instead** — `commercial_profile` is one of the three modules D-065 keeps here, *"so the work is not interrupted"* |

### TASK-406 · A-iv — an ICP criterion is scored against outcomes

| | |
|---|---|
| **Objective** | **A criterion states what it predicts, measured against closed-won.** The ICP is declarable today and **nothing tells a customer whether it is any good** |
| **Module** | `commercial_profile` — **Lane B's** *(consolidated to Lane B 2026-08-04 — [D-058](DECISION_REGISTER.md))*, via TASK-203 |
| **Status** | **`IN PROGRESS` — Lane B**, 2026-08-05, claimed by the Task Claim Protocol. **Taken as the next eligible row the moment [TASK-416](#task-416--an-evaluation-run-states-which-provider-served-it) left this lane**; **[TASK-408](#task-408--b-ii--search-results-are-grouped-and-the-ranking-is-explainable) stood higher and was skipped a third time on the reason already in its own row** — its acceptance criterion still contradicts TASK-301's shipped decision and no ruling has arrived. ✅ **Unblocked 2026-08-05 by [C-328](LANE_COORDINATION.md), which this lane raised**: *"Do not introduce the forbidden dependency. `commercial_profile` declares. `opportunity_engine` measures. Maintain the existing dependency direction."* **Lane B stopped at the boundary and the ruling confirms it was the boundary**. ⛔ **`BLOCKED` again 2026-08-05 on [C-332](LANE_COORDINATION.md), resuming after [TASK-434](#task-434--an-account-can-be-asked-whether-it-matches-a-criterion-and-only-one-thing-answers) promoted.** **The predicate is on `main` and nothing constructs its input**: `ObservedAttributes` has no producer, only `knowledge_graph` can build one (it alone holds the `entity_id → SubjectRef` binding that `ClaimReader` needs), and **`opportunity_engine` is forbidden `modules.knowledge_graph` in full** — [05](architecture/05-module-dependencies.md) gives it one upstream edge and it is Buying Score Engine. **No code written.** ⚠️ **And the `Dependencies` row below is wrong where it says the per-criterion lift half needs nothing new** — lift is `P(win | matches criterion) ÷ P(win)` and **every term needs the same predicate**, as [C-330](LANE_COORDINATION.md) already stated
| **Why it is blocked** | The row says *"a read of `opportunity_engine`'s `public/` — **verify the edge exists before writing it; if it does not, that is a `C-` item, not a new import**."* **It does not exist, and it is refused on purpose.** `pyproject.toml`'s contract *"commercial_profile declares; it never reads the pipeline"* lists `modules.opportunity_engine` **in full**, not merely its inner layers, and states why: *"if it could read a signal, a score or an opportunity, 'declaration' would quietly become 'declaration informed by our own conclusions'."* **The direction A-iv needs is closed; the opposite direction is already open** — `opportunity_engine` may read `commercial_profile.public` today. [C-328](LANE_COORDINATION.md) carries the alternatives, a recommendation and the trade-offs; **which module owns the measurement is a bounded-context decision and not a lane's** |
| **Assigned** | **Lane A, by the product owner, 2026-08-04** — *"you may proceed with A-iii and A-iv when their corresponding READY task rows exist on integration."* **The rows landed with Lane C's synchronization at `3ab3111`**, which is the condition the ruling named |
| **Approved screen** | **ICP Builder** — *"every criterion is scored against closed-won evidence, not opinion"* |
| **Scope** | Per-criterion lift against decided opportunities, with its sample size · the aggregate backtest — **win rate and median cycle, in-ICP versus outside** |
| **Dependencies** | ⚠️ **Amended 2026-08-05 — [TASK-434](#task-434--an-account-can-be-asked-whether-it-matches-a-criterion-and-only-one-thing-answers), for the backtest slice only.** *"the backtest reports both cohorts, never in-ICP alone"* **requires a predicate deciding which an account is, and [443](architecture/443-account-matching-capability.md) measured sixteen consumers of that predicate.** **The product owner sequenced TASK-434 ahead of this slice** ([D-077](DECISION_REGISTER.md)) — *"establish the reusable capability once rather than allowing multiple implementations to emerge independently."* **⛔ Do not inline an in-ICP test here; consume `commercial_profile/public/`'s.** ✅ **The per-criterion lift half is unaffected and needs nothing new.** Otherwise unchanged: `opportunity_engine` `GET /accounts/decided` supplies the outcomes and is published |
| **Affected modules** | `commercial_profile` · a read of `opportunity_engine`'s **`public/`** — **verify the edge exists in [05](architecture/05-module-dependencies.md) before writing it; if it does not, that is a `C-` item, not a new import** |
| **Repository reuse** | The ICP declaration, its versioning and `GET /icp-segments` all exist. **`/accounts/decided` exists.** No new persistence is expected — **lift is derived, not stored** (§2, *truth has exactly one authoritative representation*) |
| **Non-goals** | **No fitted weights, no refit, no drift markers** — the screen shows them; they are a model, not a measurement, and are a later slice. **No TAM funnel** — it needs a market database that does not exist. **No *Decision makers* criteria** — those are person-existence and are blocked by [O1](DECISION_PACKS.md). **No AI suggestions** |
| **Acceptance** | Each criterion reports lift and **its sample size** · a small sample is visibly small — the screen's own discipline is *"2.2× lift on only 22 deals; treat as directional, not settled"* · **the backtest reports both cohorts, never in-ICP alone** · a criterion no outcome data supports says so rather than reporting `1.0×` |
| **Implementation order** | **Fourth.** Independent of the other three |
| **Validation** | Module suite · a test that a zero-sample criterion is reported as unmeasured rather than neutral · **no new table** |
| **Escalate if** | The measurement requires reading `opportunity_engine`'s tables rather than its `public/`. **That is never permitted** (§5) |

### TASK-409 · Platform Foundation — a `demo` profile in the allocation table

> **Drafted 2026-08-04 after [O4](DECISION_PACKS.md) resolved [C-010](LANE_COORDINATION.md).** **Lane C now owns Platform Foundation work** (`CLAUDE.md` §20e) and claims these like any other lane. From [420](architecture/420-environment-management-proposal.md) §8.

| | |
|---|---|
| **Objective** | **`make demo` stops printing two commands for a human to run.** Today it prepares and then prints `uvicorn …` and `npm run dev`; `make review` needs neither |
| **Module** | `infra/` — **Lane C's**, from 2026-08-04 |
| **Status** | **`IN VALIDATION` — Lane C**, 2026-08-04. **The row is added and derives cleanly**: slot 7, port block 8 — web **3800**, API **8800**, database **`signora_demo`**, Redis index **7**, compose project **`signora-demo`**, owner **Lane C**, **coexists**. **No collision on any axis.** **No launcher** — that is [TASK-410](#task-410). ⚠️ **`--check` now reports two undocumented environments and one is pre-existing**: `lane-c` has derived ports 3500/8500 while [`RUNNING.md`](RUNNING.md) records *none*. **Both are QE's to write** — `RUNNING.md` is QE's file (`CLAUDE.md` §20e), so the check reports and does not repair |
| **Scope** | A `demo` entry in `infra/environments.py`'s profile table — slot, purpose, owner, port slot, coexistence. **The model only** |
| **Dependencies** | **None** |
| **Repository reuse** | **`environments.py` is Phase 1 of the Environment Framework and already models exactly this.** Adding a profile is a row, not a design |
| **Non-goals** | **No launcher yet** — that is TASK-410's shape and belongs to the generalisation, not to this row. **No new ports invented**: [`RUNNING.md`](RUNNING.md#running-a-lane) owns the allocation convention |
| **Acceptance** | `make environments` reports the new profile and its allocation · **no existing profile's allocation changes** · demo no longer runs inside a lane's slots |
| **Implementation order** | First of the Platform Foundation slices |
| **Validation** | `make environments --check` · **a test that two profiles cannot share a slot** |
| **Escalate if** | The allocation convention needs changing rather than extending. **That is `RUNNING.md`'s and QE's** |

### TASK-410 · Platform Foundation — one `make doctor`

| | |
|---|---|
| **Objective** | **One command answers *"is this environment ready?"*** Five tools answer it today and nothing asks all five |
| **Module** | `infra/` — **Lane C's** |
| **Status** | **`IN VALIDATION` — Lane C**, 2026-08-04. **`make doctor`, and it re-implements nothing** — every check runs as a subprocess and every one is still runnable alone. **Repairs nothing**: `workstation.py` is invoked `--check`, and a test asserts no check carries `--force`/`--fix`/`--write`. **Blocking and advisory are separated** — read from what the repository already says about each tool, not invented — so an advisory finding reports and does not fail the verdict, which is the `event-catalog` lesson. **`make validate` is deliberately not in the default run** and is printed as `not run` with its reason; **absence is never allowed to read as a pass.** ⚠️ **The verdict names its subject** — *"NOT READY to run Signora here"* — because Lane C holds no runtime by governance and a plain *"NOT READY"* would misdiagnose a clone that is correctly unable to run the product. **Seven tests** |
| **Scope** | A single target composing the **existing** checks and reporting one verdict |
| **Dependencies** | **None** |
| **Repository reuse** | **`workstation.py` · `reachability.py` · `state-check.py` · `runtime-composition.py` · `validate.py` all exist and all pass or fail on their own.** This composes; **it re-implements nothing** |
| **Non-goals** | **No new check.** ⚠️ **No repair** — `state-check.py` reports and never repairs, *because every inconsistency it finds has more than one correct resolution*, and a doctor that fixes things inherits that problem. **No CI, no scheduling** (§20c-2) |
| **Acceptance** | One command, one verdict, **every underlying tool still runnable alone** · a failure names which check failed and what to run · **exit code is the verdict** |
| **Implementation order** | Second. Independent of TASK-409 |
| **Validation** | A test that the composite fails when any component fails · **that it repairs nothing** |
| **Escalate if** | Two checks disagree. **That is a finding about the checks, not something the doctor resolves** |


### TASK-900 · The platform learns to compose a module into the runtime

| | |
|---|---|
| **Module** | `signora_platform` — 🔴, and **explicitly approved** by [ADR-0100](architecture/adr/0100-delegated-dependency-rulings.md) R-1 |
| **Slice** | **The RFC only.** No rewiring in this task |
| **Status** | ✅ **`RATIFIED` — the RFC is approved and the task is complete.** [435](architecture/435-platform-composition-rfc.md) → **[ADR-0404](architecture/adr/0404-platform-composition.md)**, product owner 2026-08-05: all four capabilities approved, **the single handler shape adopted** (*"we should not support two implementation patterns permanently"*), and the sole-owner question ruled — *"an owner may leave; a workspace may never become ownerless; enforce the invariant in the application layer rather than the authorization engine."* **Four coordination items close on it: [C-012](LANE_COORDINATION.md), [C-013](LANE_COORDINATION.md), [C-021](LANE_COORDINATION.md), [C-207](LANE_COORDINATION.md).** **No module was rewired and no production code was written by this office** — [TASK-901](#task-901) is where the rewiring happens |
| ⚡ **Why this is the highest-leverage row in the backlog** | **[TASK-901](#task-901) is *seven independently certifiable slices* and is `BLOCKED` on this one.** Nothing else in the repository converts a single decision into that much executable work. **Both lanes are at a four-of-five buffer and this is where the fifth through eleventh slices come from** |
| **Notes** | Four capabilities in one RFC: a session on `EventHandler` · `PublishableEvent` satisfiable by a frozen dataclass · a port from a handler to a provider adapter · a self-directed Casbin action. **Additive only** — a module not using one behaves identically |
| **On claiming** | **The RFC lands before any module is rewired.** §20a's approval branch means approved *then* implemented. Closes [C-012](LANE_COORDINATION.md), [C-013](LANE_COORDINATION.md), [C-021](LANE_COORDINATION.md), [C-207](LANE_COORDINATION.md) |
| ⏭️ **Skipped by Lane B, 2026-08-05, with the reason recorded** | **A platform-wide RFC is architecture preparation, not a feature lane's slice.** It is 🔴 `signora_platform`, it decides four capabilities at once and closes four `C-` items, and [D-065](DECISION_REGISTER.md) delegates task assignment to Lane C. **A lane writing the RFC that governs the substrate every module imports is the failure §20a exists to prevent**, even with ADR-0100 R-1's approval in hand. **[TASK-902](#task-902--m7-timeline--the-remaining-slices) was claimed instead** |

### TASK-901 · Seven modules consume the events they declare

| | |
|---|---|
| **Module** | Seven pipeline modules, **one per slice** |
| **Slice** | **Seven independently certifiable slices**, not one |
| **Status** | ⚡ **`READY` — released 2026-08-05.** **[ADR-0404](architecture/adr/0404-platform-composition.md) is ratified and [TASK-418](#task-418) is now buildable**, so the capabilities these seven slices consume have both an approved contract and an owner to build them. **Seven independently certifiable slices, one per pipeline module** — each claimable by whichever lane owns that module in [`modules.toml`](coordination/modules.toml). ⚠️ **Sequenced behind [TASK-418](#task-418)**: the capabilities must exist before a module can consume them, and **capability 1 changes `EventHandler`'s shape, so the two existing handlers migrate in TASK-418, not here.** **Run [ADR-0404](architecture/adr/0404-platform-composition.md) §Validation before the first slice** |
| **Notes** | After each, `make runtime-composition` is measured and **`BLOCKED_BY_C012` shrinks by exactly one.** A module leaving that list is how the architecture records that it now expects live consumption |

### TASK-902 · M7 Timeline — the remaining slices

| | |
|---|---|
| **Module** | `timeline` |
| **Slice** | S05+ |
| **Status** | ⚰️ **`DISPOSED` — Lane C, 2026-08-05, on the product owner's instruction**: *"Continue treating TASK-902 as unavailable **until Product Office decomposes or disposes it. Do not invent remaining scope.**"* **Disposed rather than decomposed, because `S05+` names no slice and never did** — the row's own audit below resolves all three of TASK-017's questions to *already done*, and **the only unbuilt capability it found is [C-215](LANE_COORDINATION.md), which is a written specification rather than a remainder of M7.** **That work is now [TASK-435](#task-435--a-seller-sees-what-changed-across-every-account-they-hold), on its own trigger.** ⚠️ **A row that has been claimed and released once for naming nothing is not a queue entry; it is the [C-412](LANE_COORDINATION.md) defect**, and this office left it `WAITING` when it should have ended it |
| ⚠️ **The error this corrects, and it was Lane C's** | **`lane-b.toml` carried TASK-902 as executable on the grounds that *"C-215 is a finished specification"*, while `BACKLOG.md` said `WAITING`.** **Both statements were defensible and the queue must not hold the more optimistic one** — that is inventing remaining scope, which is exactly what the instruction forbids. **The specification being finished makes it a *new row*, not a live one** |
| **Superseded by** | **[TASK-435](#task-435--a-seller-sees-what-changed-across-every-account-they-hold)** — one slice, fully specified, with a named trigger |
| **Prior status, retained as the dated record** | **`WAITING`** — **moved out of `READY` by Lane C, 2026-08-05.** ⚠️ **It names no remaining slice, so no lane can claim it**: Lane B took it on 2026-08-05 and released it the same day without code, for exactly that reason. **A row that cannot be started is not `READY`**, and leaving it there made both the queue and the READY count one deeper than they were. **It returns to `READY` when [ADR-0038](architecture/adr/0038-timeline.md)'s remaining slices are named.** *(Original note retained:*  *)* |
| **Notes** | **Postgres first**; Meilisearch on a stated trigger — *the first customer asking to search or facet a timeline rather than scroll it*. **Ship the six live events**; the seventh joins when M11 resumes. **The customer surface already exists** — CX-03 mounted the feed on the account brief |
| **On claiming** | Supersedes `TASK-017`, which was waiting on exactly these three answers |
| ⚠️ **Claimed and released by Lane B, 2026-08-05 — the three answers all resolve to *already done*** | **`S05+` names no slice that exists.** TASK-017 waited on two decisions: the milestone definition and Meilisearch-or-Postgres. **Neither produces work now.** Question 1 → *"built on Postgres"*, and its revisit trigger is **the first customer asking to search or facet a timeline**, which has not happened. Question 2 → *"six shipped"*; the seventh is `recommendation.created` and **awaits M11, which is deferred**. Question 3 → *"does the timeline reach a customer?"* — **it does now.** [45 §6](architecture/45-timeline.md) lists *"no mount point"* as the module's one real gap, and **CX-03 closed it**: `frontend/app/(app)/accounts/[accountId]/page.tsx` renders `AccountHistory` from `useAccountTimeline`, so [C-024](LANE_COORDINATION.md) is resolved |
| **Verified rather than assumed** | **Nine projection rules in `domain/projection.py`, and all nine render** — `feed.tsx` carries an emphasis and a label for every one, superseded kinds included. Domain, application, infrastructure, interface, migration `0026` with forced RLS and no `UPDATE` grant, nine worker subscriptions and the feed component are all built. **The one unbuilt capability is [C-215](LANE_COORDINATION.md)** — the feed is per-account and the workspace needs it per-seller — **and that is an unanswered coordination item, not a claimable slice.** This lane will not assume its answer |
| **Disposition** | **Lane C's and the product owner's.** The row is neither reordered nor removed here. **No code was written** |

### TASK-903 · A seller can see what their company sells

| | |
|---|---|
| **Module** | `commercial_profile` (the read surface) · Product Surface (the mount) — **a two-lane build** |
| **Slice** | one slice each side |
| **Status** | **`IN VALIDATION` — Lane A**, 2026-08-05. Claimed and shipped the same day, straight from [`queues/lane-a.toml`](coordination/queues/lane-a.toml)'s `future` with no round-trip. Narrowed to **stage 2** by Lane C 2026-08-05. ⚠️ **It was queued to Lane B as a `commercial_profile` read surface the module no longer owes.** **[C-008](LANE_COORDINATION.md) was ruled 2026-08-03 — *option C now, option D next* — and stage 1 shipped as CX-05 at `e3516c4`**: `/business`, member-reachable, five declarations. **This lane's own repository check settles the rest**: *"one lane, not two — stage 1 needed no backend change and the display half of stage 2 needs none either."* **The account brief is Product Surface, which is Lane A's.** ⛔ **Scope bound**: *anything asserting **this account matches this ICP** is still blocked on [C-002](LANE_COORDINATION.md)* — **display the declarations, assert no match** |
| **Notes** | **Read-only, for `member`, beside the account brief** — not under `/settings`, where the granted read is unreachable behind `workspace:update`. `policy.csv` already grants `member` read on `product`, `icp`, `buying_committee` and `commercial_focus`: **the API and the product disagree, and the API is right** |
| **Delivered** | **A *What you sell* card on the account brief** — the workspace's products, each with the roles that have to agree, beside the competitor list that was already there. **Both are workspace declarations and both say so**: *"the same on every account. Signora has not said this account is a candidate for any of it."* ⛔ **No ideal customer, and that is the ruling rather than a layout choice** — an ICP beside a real company is a comparison the reader completes whether or not the product does, and [C-002](LANE_COORDINATION.md) is unmoved. **The component takes no ICP prop**, so the bound is in the type. **The committee is here because contacts are nowhere**: no person's name enters the platform, so *who normally signs off* is answered by roles, and naming who holds each seat is Epic C's ([TASK-427](#task-427--m-d--the-people-domain--a-person-and-an-affiliation-with-an-end)). ⚠️ **Found [C-226](LANE_COORDINATION.md)'s class in `CompetitorContext`**, which this lane wrote three days earlier — a failed read and an undeclared workspace both rendered as silence. Both sections now distinguish them. **No backend change, no new endpoint, no new hook, no `keys.ts` entry, no permission change.** Recorded in [`37-product-surface.md`](architecture/37-product-surface.md) |
| **On claiming** | Open a `C-` item for the mount if the two halves are claimed by different lanes. **Placement is judgement** ([ADR-0100](architecture/adr/0100-delegated-dependency-rulings.md) R-5) — say so in review if it reads wrong |
| **Repository check, 2026-08-03 — Lane A** | **Half of this shipped, and the premise above is no longer true.** [C-008](LANE_COORDINATION.md) was ruled by the product owner — **option C now, option D next** — and stage 1 shipped as **CX-05** at `e3516c4`: `/business`, member-reachable, **five** declarations rather than four (`target_account` carries the same grant). **The granted read is no longer unreachable.** What remains is stage 2 — the declarations *on the account brief* — and it is **one lane, not two**: stage 1 needed no backend change and the display half of stage 2 needs none either. **Anything asserting *this account matches this ICP* is still blocked on [C-002](LANE_COORDINATION.md)**, which has no owner. **Not reclaimed, not reworded, not rescoped by this lane** — status and position are Lane C's and the product owner's ([C-217](LANE_COORDINATION.md)) |

### TASK-904 · An organization can grow

| | |
|---|---|
| **Module** | `workspace_tenancy` |
| **Slice** | invitation table · acceptance · members list |
| **Status** | **`IN VALIDATION` — Lane A**, 2026-08-05. **The whole slice is built** — invitation table (already shipped), **acceptance** (the piece [C-208](LANE_COORDINATION.md) blocked), and the members list (already shipped). Backend integrated at `839e8b0`. ⚠️ **`reachability.test.tsx` fails on one line that is QE's** — **[C-227](LANE_COORDINATION.md)**: `/join/*` has no in-product entrance by design and must be declared in `ENTERED_FROM_OUTSIDE`, a list its own comment calls *"a judgement, maintained by QE"*. Previously **`CLAIMED` — Lane A**, 2026-08-05, by the Task Claim Protocol. **`next` in [`queues/lane-a.toml`](coordination/queues/lane-a.toml)**, and `workspace_tenancy` is Lane A's in [`modules.toml`](coordination/modules.toml). ⚠️ **Claimed against [D-071](DECISION_REGISTER.md), not against [LANE_COORDINATION.md](LANE_COORDINATION.md)**, whose C-206 and C-208 rows still read `OPEN` and are stale — the register records both rulings, this row records them, and `queues/lane-a.toml` still carries a `[[blocked]]` entry naming them. **Three documents, two of them behind.** Previously ✅ **`READY` — unblocked 2026-08-05.** Both architectural blockers are ruled. **[C-206](LANE_COORDINATION.md) `APPROVED`**: *"Invitation lifecycle belongs to Signora. Authentication proves identity. **Workspace membership, invitations and tenancy belong to Signora.**"* **[C-208](LANE_COORDINATION.md) `APPROVED`**: *"Introduce an explicit authenticated-but-not-member state. **Do not weaken general RLS.** Provide only the minimum read path required for invitation acceptance."* ⚠️ **`signora_platform/db/` is frozen (§20a)** — the new state is a named, single-purpose read path, never a general policy change |
| **Notes** | **Signora owns the invitation.** An `invitation` table keyed by email; acceptance matches a pending row against the **`email` claim already in the verified JWT**. **Better Auth's `organization` plugin is not adopted** — migration `0005` revokes `signora_app` from the `auth` schema, so plugin-owned membership is membership the Python tier cannot read, and §13 requires it re-verified every request |
| **On claiming** | **v1 delivery is a shareable link, not email.** No transactional-email dependency is added. **That half is judgement** and is the ruling to challenge first if you would rather ship with email |

### TASK-905 · A contraction risk stops looking like an opportunity

| | |
|---|---|
| **Module** | Product Surface · `buying_score_engine` owns posture |
| **Slice** | one slice |
| **Status** | **`IN VALIDATION` — Lane A**, 2026-08-05. Claimed and shipped the same day. **`next` in [`queues/lane-a.toml`](coordination/queues/lane-a.toml)**; Product Surface and `buying_score_engine` are both Lane A's |
| **Notes** | Posture reaches the attention row. **A contraction risk must not be confusable with a low-scoring opportunity** — they mean opposite things to a CRO scanning a list. **The treatment is yours**, within the design system; the ruling is only that they must differ |
| **Delivered** | **A warning badge reading *At risk*, last in the row's status lane — beside the score**, because the confusion is with a number: a contraction risk ranks next to the weakest opportunities and means the opposite of one. **The M12.3 mark had two holes**: it hung off the catalog's *title*, so a contraction row rendered **unmarked on every first paint** and **permanently** for a score formed under a catalog version that no longer declares its key — and it sat in running text rather than in the lane a scanner reads. **`PostureMark` takes `posture` and no catalog key**, so a second commercial vocabulary in the browser is unconstructable rather than merely tested (§2). **No reordering, no filter, no change to the score, no backend change** — `posture` has been on `AccountAttentionResponse` since M12.3. **Answers [C-011](LANE_COORDINATION.md)**, which QE raised and QE closes. Recorded in [`37-product-surface.md`](architecture/37-product-surface.md) |

### TASK-906 · M14b names its bounded context

| | |
|---|---|
| **Module** | **Undecided — that is the deliverable** |
| **Slice** | discovery |
| **Status** | **`WAITING`** — **trigger: implementation naturally reaches M14b.** ⚠️ **Moved out of `READY` by Lane C, 2026-08-05**, on [C-412](LANE_COORDINATION.md)'s finding of 2026-08-04, which this office raised and then left uncorrected for a day. **[D-029](DECISION_REGISTER.md) defers it explicitly**: *"do not force a module boundary until implementation naturally reaches M14b."* **A row whose deliverable is a boundary the product owner deferred is not claimable**, and leaving it `READY` made the eligible count overstate itself by one every time it was read. **The scope is untouched and the order is untouched** — only the advertisement stops |
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
| **Status** | **`IN PROGRESS` — Lane B**, 2026-08-05, claimed by the Task Claim Protocol. **Claimed from the top of the queue**: [TASK-408](#task-408--b-ii--search-results-are-grouped-and-the-ranking-is-explainable) stood higher and was skipped a fourth time on the reason already in its own row, and [TASK-406](#task-406--a-iv--an-icp-criterion-is-scored-against-outcomes) is `BLOCKED` by the product owner's [C-330](LANE_COORDINATION.md) ruling. ✅ **Unblocked 2026-08-05.** **[C-018](LANE_COORDINATION.md) `APPROVED`**: *"Customer-facing terminology belongs in `explanation.py`. **Business language should never leak inward.**"* **The label is composed where the sentence is composed**, so [ADR-0034](architecture/adr/0034-ubiquitous-language.md)'s rule that translation never travels inward into `knowledge_graph` holds, and **AC-28 is untouched** |
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

### TASK-436 · `provider_platform` declares which adapters exist, and builds its own registry

| | |
|---|---|
| **Why this row exists at all** | ⚠️ **[TASK-419](#task-419--a-handler-can-reach-a-provider-adapter) is `BLOCKED` on this work, and this work had no id.** TASK-419's module is **`apps/` — Lane C's** ([C-010](LANE_COORDINATION.md)), so **Lane A could not claim it**, while `lane-a.toml` listed it as Lane A's next-but-two. **A queue pointing a lane at another lane's row is [C-412](LANE_COORDINATION.md)**, and this office wrote it |
| **Module** | **`provider_platform`** — [`modules.toml`](coordination/modules.toml) records it as **Lane A** |
| **Status** | **`PROMOTED` — QE, cycle 66, 2026-08-05**, certified at `772eebe` and on `main`. Claimed and shipped the same day, straight from [`queues/lane-a.toml`](coordination/queues/lane-a.toml)'s `next`. **Taken because `current` ([TASK-400](#task-400--epic-a-completion--the-surfaces-that-expose-what-the-platform-already-knows)) has one half delivered and the other held on [C-219](LANE_COORDINATION.md) with Lane C** — [D-070](DECISION_REGISTER.md): *a blocked task never idles a lane that owns other work.* Decomposition of already-approved scope, never new scope ([ADR-0404](architecture/adr/0404-platform-composition.md) capability 3, ratified 2026-08-05). **Position is the product owner's**; this row is placed last in `READY` and reorders nothing |
| **Objective** | **A typed `Settings` for `provider_platform` choosing which provider adapters exist, and a `build_provider_registry` at its composition root** |
| **Why here rather than in the platform** | **§10, quoted**: *configuration is always a typed Settings object **owned by the module that owns the behaviour***, and *"no module ever learns where another module's configuration came from."* **`provider_platform` owns provider behaviour** |
| **Measured before queueing** | **`SimulatedProviderAdapter` is constructed at 3 sites, all under `backend/tests/`.** **No composition root builds a provider registry today** — which is the correction ADR-0404 §capability 3 already carries |
| **Delivered** | **`ProviderSettings` and `build_provider_registry`** — the registry is built from configuration alone, and **a simulated adapter registered outside a local environment raises at startup**: the same invariant §10 states for the AI mock, and the stakes are higher, because a deployed service answering from the simulator is *indistinguishable from one that is working* while every score built on it is fabricated. ⚠️ **A Security Invariant refused the first draft and was right for a better reason than the one that made it fail.** `scenario`, `seed` and `page_size` sat on `ProviderSettings`; they are not *provider* configuration — a real adapter needs an API key, not a seed — so they moved to **`SimulationSettings`, beside the adapter that reads them.** §6 one level down. **`SIMULATED_PROVIDERS` is now one table** and the contract suite reads it, retiring five hand-written pairs that would have disagreed the first time a capability moved. **`make validate` PASSED: 3596 tests, clean migrate, clean `tsc`** |
| **Releases** | **[TASK-419](#task-419--a-handler-can-reach-a-provider-adapter)** — Lane C then adds the `WorkerRuntime` field, **and only then**. **One slice here unblocks the other lane's row** |
| **Governance** | 🟠 — the module's own `infrastructure/` and its composition root, **announced in the commit message.** **Not 🔴: `signora_platform/` is untouched**, which is the whole point of §10's placement rule |

### TASK-437 · A member can leave an organization, and the last owner cannot

| | |
|---|---|
| **Unblocked by** | **[TASK-418](#task-418--the-platform-gains-the-four-capabilities-adr-0404-approved) capability ④**, shipped 2026-08-05. **`Action.LEAVE` and its two policy grants exist and are asserted by a Security Invariant** — what is missing is the endpoint |
| **Module** | **`workspace_tenancy`** — [`modules.toml`](coordination/modules.toml) records it as **Lane A** |
| **Status** | **`IN VALIDATION` — Lane A**, 2026-08-05. Claimed and shipped the same day, straight from [`queues/lane-a.toml`](coordination/queues/lane-a.toml)'s `current` with no round-trip — **the first executable work this lane has had since its queue reached zero.** Decomposition of already-approved scope. [C-207](LANE_COORDINATION.md) is `CLOSED` by [ADR-0404](architecture/adr/0404-platform-composition.md); **[46 §2 and §3](architecture/46-team-management.md) documented the gap before either existed.** **Position is the product owner's** — placed last in `READY`, reordering nothing |
| **Why it exists, stated plainly** | ⚠️ **Capability ④ ships a reviewed authorization grant for an operation the product cannot perform**, and [46 §2](architecture/46-team-management.md) already names that exact shape as a defect: *"`p, owner, *, member, remove` is granted… and there is **no endpoint, no use case, and no domain method.** A reviewed authorization grant for an operation the system cannot perform."* **This row exists so capability ④ does not become the second instance of the thing that document complained about** |
| **Objective** | **`DELETE /workspaces/{id}/membership`** — or the shape `workspace_tenancy` prefers. **Leaving takes no target**, which is what makes it self-scoped: the caller's own membership ends |
| **Reuse — most of it is built** | ✅ **`Membership` models departure** · ✅ **`LastOwnerCannotLeaveError` already exists and is already raised** by `demote` and `remove` · ✅ **`Action.LEAVE` and the two grants** · ✅ **13 endpoints and the largest router in the repository** to pattern-match |
| **⛔ The invariant, and where it belongs** | **An owner may leave. A workspace may never become ownerless.** [ADR-0404](architecture/adr/0404-platform-composition.md), ruled: ***"Enforce the invariant in the application layer rather than the authorization engine"*** — a workspace invariant hidden in the policy model is invisible to anyone reading the workspace |
| **Not in scope** | **No `remove` endpoint** — that is [46 §2](architecture/46-team-management.md)'s separate gap and a different grant · **no membership suspension** · **no notification** |
| **Delivered** | **`POST /workspaces/{id}/membership/leave`** — no target, no body, no reason. The membership is found from the workspace and the verified token, so **there is no identifier to substitute and no ownership check that could be written wrongly.** The last-owner refusal is the domain's, reused from `Membership.end` rather than restated. 🔴 **The slice found [B-206](BUGS.md) in its own module**: `WorkspaceQueryService.get_membership` — the request-time membership check — **never filtered ended memberships, so removal did not revoke access.** `SqlMembershipRepository.get` did filter, and documented that exact outcome as its reason: two reads of one fact, and authorization consulted the unfiltered one. Fixed, with end-to-end regression tests for both the removed and the departed case. 🟠 **`LastOwnerCannotLeaveError` was mapped to no status code**, so *"Make somebody else an owner first"* reached customers as **500 "An unexpected error occurred."** Now `409`, which repairs `remove` and `demote` too. **`MembershipResponse` gained `ended_at`**, which `remove`'s docstring already claimed. **`make validate` PASSED — 3651 tests, clean migrate, clean `tsc`** |
| **Governance** | 🟠 — the module's own layers and a route, **announced in the commit message.** **No ADR: the model question was C-207 and it is closed** |

### TASK-438 · The Executive Dashboard's five sections that need nothing new

| | |
|---|---|
| **Discovery** | **[444](architecture/444-executive-dashboard-domain-assessment.md)** — the Executive Dashboard assessed to its domain |
| **Approved screen** | **Executive Dashboard** — [410](architecture/410-approved-ui-specification.md) #3, *"CEO/CRO homepage"* |
| **Module** | `opportunity_engine` — **Lane B's** · a read of `commercial_profile.public` for the ICP predicate |
| **Status** | **`CLAIMED` — Lane B**, 2026-08-05, by the Task Claim Protocol. **The only `READY` row in the backlog**, in a module [`modules.toml`](coordination/modules.toml) assigns to this lane. ⛔ **Claimed at reduced scope: four sections, not five.** *ICP coverage, in versus outside* is blocked by [C-332](LANE_COORDINATION.md) and the row's *"newly unblocked"* line does not survive checking — see below. **Originally: `READY` — decomposition of already-approved scope, and it needs an answer from nobody. Position is the product owner's**; placed last in `READY`, reordering nothing |
| **Delivers** | **Stage conversion · ageing · movement since a date · roll-up by owner · ICP coverage, in versus outside** |
| **Why it needs nothing new** | **One table already carries it.** `opportunity_state` is append-only with **`sequence · stage · owner_id · actor_id · reason · occurred_at`** — conversion is a sequence walk, ageing is a delta between consecutive rows, movement is `occurred_at > :since` with `reason` explaining each one, and **roll-up needs no new field because `owner_id` is already on every row** |
| **The fifth, newly unblocked** | **ICP coverage** — ⚡ **[TASK-434](#task-434--an-account-can-be-asked-whether-it-matches-a-criterion-and-only-one-thing-answers) is `PROMOTED`**, so *in-ICP versus outside* is a call to a published predicate rather than a second interpretation |
| **Reuse** | **`GET /accounts` and `GET /accounts/decided` are published and workspace-scoped.** `since` is a **declared parameter**, never stored read state — the rule [C-215](LANE_COORDINATION.md) established |
| **⛔ Not in scope, and this is the discipline of the row** | **No forecast · no probability · no deal value · no plan · no quarter.** **All five are [C-418](LANE_COORDINATION.md), and they are one question rather than five.** ⚠️ **`buying_score_engine` refuses probability in writing** — *"No probability, no likelihood, no prediction"* — **so a probability added here contradicts a ratified principle** |
| **⛔ And no second aggregation** | **Opportunity Intelligence needs the same aggregates**, which is why [412](architecture/412-backend-capability-matrix.md) puts both in wave 4. **Whatever this builds, that screen reads** |
| **Governance** | 🟠 — the module's own layers and read endpoints, **announced in the commit message.** **No ADR: no boundary moves, and the `commercial_profile.public` edge exists** |

## SEQUENCED — prepared, and waiting on a named trigger

### TASK-415 · A deterministic mock AI provider, and development stops needing a model

| | |
|---|---|
| **Objective** | **A developer can clone the repository, run the stack, and exercise every AI path without downloading a model.** Today `build_provider_registry` registers exactly two adapters — Anthropic and Ollama — so the running application has no deterministic option |
| **Module** | `ai_platform` |
| ✅ **Lane C review — `AIVendor.MOCK` is 🟠, and the lane may proceed** | **Answered 2026-08-05, and answered rather than escalated** because both rules already exist and reading them together changes no boundary, contract or invariant (`PRODUCT_OFFICE.md` §12, the QE-gates precedent). **The package asks whether a new `AIVendor` member is a 🟠 enum change or a 🔴 needing an ADR, and refuses to decide it inside a slice — which is correct and is the reason this review is short.** **It is 🟠.** `CLAUDE.md` §10 and [ADR-0028](architecture/adr/0028-model-runtime-by-environment.md)'s amendment **already ratify the deterministic mock as an execution mode and as a first-class development provider implementing the existing port.** Adding the member **records a decision the product owner has already made**; an ADR would re-decide it, which is the unnecessary work the AI directive explicitly warned against. **The enum's docstring forbids *speculative* members and this one is required by an approved task**, so the guard does not bite. ⚠️ **One condition, and it is checkable rather than a redesign**: §10 says *"business behaviour may never branch on a vendor."* **Confirm nothing reads `InferenceResult.vendor` to choose behaviour before adding the member** — if something does, that is a separate defect and a `B-` row, not this slice's to absorb. **The three other findings are accepted as written**: conditional Ollama registration is in scope (the registry refuses two adapters for one model, so it is a precondition rather than a preference) · the production guard taking environment as a parameter is right and is what makes the Security Invariant able to fail · **six constructor arguments, not six settings fields.** **Reusing `OLLAMA` is correctly refused** — an `ai_inference` row asserting a vendor that never ran is worse than no attribution |
| **Status** | **`IN VALIDATION` — Lane B**, 2026-08-05. **Approved by Product Office** — *"AIVendor.MOCK is a 🟠, and the lane may proceed"* — and built the same day, with **two deviations from the package stated in the commit and the design doc rather than absorbed.** Package below. Prepared by Lane B, `ai_platform`'s current assignee in [`modules.toml`](coordination/modules.toml), whose own `next_milestone` names this task. **Authoring the implementation package; `UNDER REVIEW` follows and Lane C reviews rather than authors it.** ✅ Approved by the product owner 2026-08-04. **This is the first task to run the [D-060](DECISION_REGISTER.md) loop end to end**, and **Lane C deliberately did not write the package** — *"do not centrally prepare implementation packages."* ⚠️ **The product owner's framing is a scope correction carried into the package**: *"it is not merely a test double. Treat it as a first-class development provider implementing the existing provider port"* |
| **Scope** | `modules/ai_platform/infrastructure/adapters/mock.py`, implementing the **existing** `AIProviderAdapter` port. Configurable **content · failure · latency · token usage · timeout · retry count**. Registered by `build_provider_registry` **only when explicitly configured** |
| **Repository reuse** | **The port is unchanged** — one `describe`, one `complete`. **The failure taxonomy already exists**: `AITransientError` · `AIRateLimitedError` · `AIPermanentError` · `AIOutputUnusableError`. **`tests/ai_platform/fakes.py` already does half of this** and its behaviour is promoted rather than rewritten. **`signora_platform/simulation/faults.py` is the proven pattern** at the data-provider boundary |
| **Non-goals** | ⛔ **No streaming simulation. No tool-call simulation.** The port has neither, deliberately — *"a wider port would force every future vendor to implement methods most of them do not have, and the usual outcome is adapters raising `NotImplementedError`, which is a contract that lies."* **The mock must never lead the port** |
| **Acceptance** | The stack runs and every AI path answers with **no Ollama and no API key** · each of the six knobs is independently settable · **a Security Invariant asserts the mock is never registered in a production configuration** |
| **Why that invariant is not optional** | `build_provider_registry` already warns that a service which *"could quietly reach a local runtime when its vendor was unreachable would serve customers from a model nothing evaluated."* **A mock makes that failure worse**: a production service answering from a deterministic stub would be indistinguishable from one that worked |
| **Change Budget** | 🟠 — a new adapter is an adapter registration, which [ADR-0028](architecture/adr/0028-model-runtime-by-environment.md) already governs. **No port change, no new bounded context, no new dependency** |
| **Escalate if** | The port needs to change. **That is a different task and an ADR** |

#### Implementation package — Lane B, 2026-08-05 · `UNDER REVIEW`

> **Authored by the owning lane, as [D-060](DECISION_REGISTER.md) requires.** Every claim below was read out of the code rather than recalled. **Four findings changed the shape of the task, and two of them mean the row's own `Change Budget` is wrong.**

**F1 · Ollama is registered unconditionally, and that is the actual defect.** `infrastructure/composition.py:62` calls `registry.register(OllamaAdapter(...))` with **no configuration guard**, while Anthropic sits behind `if settings.anthropic_api_key`. So the objective — *"a developer can clone the repository and exercise every AI path without downloading a model"* — is **not reached by adding an adapter.** It is reached by making Ollama's registration conditional, which is a **behaviour change to an existing code path**, not a new file beside it. `CLAUDE.md` §10 states the target directly: *"No implementation may assume Ollama is installed unless a developer explicitly selects it."*

**F2 · `AIVendor` has no member the mock can honestly use, and the two cheap answers are both wrong.** Reusing `OLLAMA` makes `InferenceResult.vendor` and every `ai_inference` row **assert a vendor that never ran** — §10's *failure attribution must be truthful*, whose own words are *"an incorrect attribution is worse than none."* Leaving it unset is not available: the field is required and `AIProviderDescriptor` declares it. **The package proposes `AIVendor.MOCK`.** The enum's docstring forbids *speculative* members — *"a member here with no ratified status"* — and this one is **ratified**: `CLAUDE.md` §10 names the deterministic mock as one of three execution modes and makes it the development default. **This is a change to `domain/provider.py`, which the row's 🟠 *"no port change"* did not anticipate.** It is still Lane B's module and still 🟠, but it is named here rather than discovered in review.

**F3 · The registry will refuse the mock if Ollama is still registered.** `AIProviderRegistry.register` raises `AIRegistrationError` when two adapters claim one model, deliberately — *"routing would depend on registration order."* The mock must serve the **configured development model**, which is the same string Ollama serves. **So F1 is not merely desirable, it is a precondition**: the two cannot both be registered for the same model, and the failure would be at composition rather than at call time.

**F4 · The production guard cannot read the platform's `environment`.** `signora_platform/settings.py:18` holds it, but §6 forbids one module reading another's configuration and §20a freezes the platform. **The guard therefore takes the environment as an explicit parameter at the composition root**, which already constructs both settings objects. A parameter is also what makes the Security Invariant able to fail — a guard reading a global would be untestable without mutating one.

| | The package |
|---|---|
| **Design** | `MockAdapter` in `infrastructure/adapters/mock.py`, a frozen dataclass implementing `describe` and `complete` **and nothing else**. **`tests/ai_platform/fakes.py::FakeAdapter` is promoted, not copied** — its scripted-content and scripted-error behaviour is the starting point, and the test fake then imports the real adapter rather than keeping a second implementation (§2, *truth has exactly one authoritative representation*) |
| **The six knobs** | `content` · `error` · `latency_ms` · `usage` *(input/output tokens)* · `timeout_seconds` · `retries`. **Constructor arguments on the adapter, not six `AISettings` fields.** Configuration selects *the mock*; a test configures *its behaviour*. Six environment variables to make a fake return a 429 is configuration surface nobody would use, and §6 forbids speculative flags |
| **Selection** | One `AISettings` field naming the development provider, defaulting to the mock. **`build_provider_registry` registers exactly one of mock or Ollama**, never both, and Anthropic stays conditional on its key as it is today |
| **The invariant** | `build_provider_registry` raises `AIRegistrationError` when the mock is selected and the environment is not local. **A Security Invariant asserts it**, and asserts the diagnostic **names the cause** — §10 requires the failure to be fast *and* legible |
| **Blast radius** | `domain/provider.py` *(one enum member)* · `infrastructure/adapters/mock.py` *(new)* · `infrastructure/settings.py` *(one field)* · `infrastructure/composition.py` *(the conditional)* · `tests/ai_platform/fakes.py` *(re-pointed)* · one Security Invariant. **No port method, no new dependency, no migration, no event, no API** |
| **Tests** | The six knobs independently · the taxonomy raised as configured · **the registry refusing mock-in-production, with its message asserted** · **the clash refusal** when both are somehow selected · and the objective itself: the registry builds and resolves the development model **with no Ollama and no API key** |
| **Revised Change Budget** | 🟠 — unchanged in tier, **wider in surface than the row stated**: it includes one `AIVendor` member and one behaviour change to `build_provider_registry`. **Announced here rather than in the commit message, because review is the point of this state** |
| **What this package does not do** | It does not touch `execution_mode` on the evaluation record — **that is [TASK-416](#task-416--an-evaluation-run-states-which-provider-served-it)**, and folding it in would merge two approved rows into one unreviewed slice |

⚠️ **One question for Lane C, and it is the only thing in this package a lane should not settle alone.** F2 adds a member to a ratified enum whose docstring governs what may be added. **Lane B's reading is that §10 already ratifies the mock**, so `AIVendor.MOCK` records a truth rather than reserving a speculation — but *"is the mock a vendor?"* is a modelling question about a published domain type, and **if the answer is no, the alternative is a separate provenance field and that is 🔴 with an ADR.** Implementation does not start until this is answered, because both paths write different code and one of them is not Lane B's to take.

### TASK-416 · An evaluation run states which provider served it

| | |
|---|---|
| **Objective** | Evaluation should **name its provider rather than inherit one.** `__main__.py` reads `model = args.model or settings.ollama_model` — **`--model` already works, so this is a default, not a constraint** |
| **Module** | `ai_platform` (evaluation) |
| **Status** | **`IN VALIDATION` — Lane B**, 2026-08-05. **`provider` shipped; `execution_mode` deliberately not built** — an evaluation run is in Evaluation mode by construction, so the field could never vary, and the argument is recorded in [28-ai-platform.md](architecture/28-ai-platform.md) rather than decided by a lane. **Preparing it found [B-324](BUGS.md), a hazard TASK-415 created.** Prepared by Lane B, **Taken as `next` the moment [TASK-415](#task-415--a-deterministic-mock-ai-provider-and-development-stops-needing-a-model) left this lane**, which [D-070](DECISION_REGISTER.md) requires without waiting for Lane C. **[TASK-408](#task-408--b-ii--search-results-are-grouped-and-the-ranking-is-explainable) stood higher and was skipped again, on the reason already recorded in its own row** — its acceptance criterion contradicts a decision shipped in TASK-301, and choosing between them is the ruling itself. ✅ **`APPROVED` — [431 §7](architecture/431-ai-execution-modes.md) is answered.** *"Evaluation reports may record the provider used for execution. This is operational metadata rather than product behaviour… it does not weaken the existing principle that evaluations remain model-centric."* **Awaiting the owning lane's package**, like TASK-415. **Four of the six required fields already exist** — `model`, `prompt_version`, `rendering_protocol_version`, and `prompt_fingerprint`, which is stronger than requested. **`provider` and `execution_mode` are the whole of the change** |
| **The question** | **`report.py` deliberately names no vendor**: *"nothing in evaluation may: the run asked for a model."* **Model-centric resolution is a ratified permanent principle** (`CLAUDE.md` §10). **Reproducibility wants to know what served a run; the principle says the model already is that.** **Likely they agree** — `claude-sonnet-4-5` names its server as precisely as `llama3.1:8b` does — **and if so this is a default change and nothing more** |
| **Repository reuse** | **The harness is already vendor-neutral** — *"it knows no vendor. It names a model; who serves it is the registry's business."* **Nothing needs building; a default needs choosing** |
| **Change Budget** | 🟢 for the default. **🔴 if the report gains a vendor field** — that amends ADR-0028 and touches a ratified principle |


### TASK-418 · The platform gains the four capabilities ADR-0404 approved

| | |
|---|---|
| **Recommendation** | **Decomposition of already-approved scope** — [ADR-0404](architecture/adr/0404-platform-composition.md), ratified 2026-08-05. **No new scope.** Lane C, decomposing rather than deciding (§20e) |
| **Module** | **`signora_platform/`** — Lane C (Platform Foundation), from [C-416](LANE_COORDINATION.md) |
| **Slice** | **Three platform edits, one slice.** Capability 3 is separate — it is in `apps/`, which is Lane C's |
| **Status** | **`IN VALIDATION` — Lane C**, 2026-08-05. ✅ **Capability ④ certified at `6b7b04e` and promoted, cycle 67 — the row stays open because ① and ② have not shipped**, which is QE recording what is true of each half rather than closing a task on one of them. **Capability ④ shipped**: `Action.LEAVE`, two policy grants, and a Security Invariant that fails without them. **[TASK-437](#task-437--a-member-can-leave-an-organization-and-the-last-owner-cannot) created so the grant does not dangle.** ⚠️ **① and ② remain, blocked on [C-417](LANE_COORDINATION.md)** — the row stays open until they land. ⚠️ **NARROWED TO CAPABILITY ④ ON CLAIMING, and the reason is [C-417](LANE_COORDINATION.md).** **[ADR-0404](architecture/adr/0404-platform-composition.md) §Validation was run first, as the ADR instructs, and ② failed**: the platform edit is Lane C's and its proof is five files in `backend/modules/`, which §20e forbids this lane from touching. **`mypy strict` implies `warn_unused_ignores`, so the two halves cannot be separated** — the change and the five one-line deletions are one atomic commit. **① has the same shape**; both `EventHandler` implementations are in `modules/`. **④ is entirely inside `signora_platform/authorization/` and is unaffected, so it ships now.** **A narrowing with a stated reason, never a silent skip.** *(Original status retained:* ✅ **`READY` — Lane C, unblocked 2026-08-05.** **[C-416](LANE_COORDINATION.md) ruled**: `backend/signora_platform/` is Lane C's as permanent architectural owner — *"shared infrastructure, not a bounded context… platform ownership must remain stable and independent of feature ownership."* ⚠️ **Ownership is not approval.** §20a still freezes the tree; **[ADR-0404](architecture/adr/0404-platform-composition.md) is what makes this buildable**, and this row exists because that ADR approved a contract with no task to build it .)* |
| **Why this exists** | **[TASK-901](#task-901) is the module-side consumption — seven slices that use the capabilities.** Nothing was the platform-side change that *creates* them, and ADR-0404 approved a contract with no row to build it. **A ratified ADR with no task is how an approval quietly becomes a plan nobody executes** |
| **In scope** | **① `EventHandler` takes the dispatcher's session** — `event_bus/subscriptions.py`, and `dispatch.py:116` passes it. **The two existing handlers migrate here**, not in TASK-901 · **② `PublishableEvent`'s six members become read-only properties** — `event_bus/publisher.py`, and **the eight `# type: ignore[arg-type]` are deleted in the same slice, which is how the change is proven** · **④ `Action.LEAVE` plus two policy lines** — `authorization/enforcer.py` and `policy.csv` |
| **Not in scope** | **Capability 3** (`WorkerRuntime.providers`) — `apps/` is Lane C's under [C-010](LANE_COORDINATION.md) and it is Lane C's to build · **any module rewiring** — that is TASK-901 · **`model.conf`** — the request tuple does not change, deliberately |
| **On claiming** | **Run [ADR-0404](architecture/adr/0404-platform-composition.md) §Validation first — all four.** Two of ADR-0403's five corrected its own first draft. **A validation that fails is a `C-` item, never an improvisation** |
| ✅ **The blocker it carried, resolved 2026-08-05** | **[C-416](LANE_COORDINATION.md) is `RULED` and [`modules.toml`](coordination/modules.toml) now allocates `backend/signora_platform/` entire to Platform Foundation.** **Nothing here is unowned any more.** *(The original statement is kept below as the dated record of why the row sat still.)* |
| ~~⚠️ The blocker, and it was one line of ownership~~ | **[C-010](LANE_COORDINATION.md) asked about `apps/` *and* `signora_platform/`. The 2026-08-05 ruling named `apps/` only.** `modules.toml` allocates just `backend/signora_platform/simulation/` to Platform Foundation; **the event bus and the authorization engine belong to nobody.** **Three of ADR-0404's four capabilities live there**, so **seven slices sit behind one unassigned directory** |

### TASK-419 · A handler can reach a provider adapter

| | |
|---|---|
| **Recommendation** | **Decomposition of already-approved scope** — [ADR-0404](architecture/adr/0404-platform-composition.md) capability 3. **No new scope** |
| **Module** | **`apps/`** — [`modules.toml`](coordination/modules.toml) records it as **Lane C**, from [C-010](LANE_COORDINATION.md), ruled 2026-08-05 |
| **Slice** | one slice |
| **Status** | ⏸️ **`BLOCKED` — on `provider_platform`'s half, which is Lane A's.** ⚠️ **Rescoped 2026-08-05, before a line was written.** [ADR-0404](architecture/adr/0404-platform-composition.md) sized this as *"`WorkerRuntime` gains a `providers` field, built at the worker's composition root exactly as the API's registry already is"* — **and no composition root builds a `ProviderRegistry` anywhere.** The registry that sentence compared it to is `ai_platform`'s **AI** provider registry: a different thing with a similar name, and **the collision is live in one file** — `apps/worker/subscriptions.py:153` already passes `providers=` to `Infer` |
| **Measured** | **`SimulatedProviderAdapter` is constructed only in tests** *(3 sites, all under `backend/tests/`)*. **`provider_platform` has no `Settings` object.** `build_run_sync` takes an `adapter` a caller supplies, and **no caller in `apps/` supplies one** |
| **In scope — Lane C** | **A `provider_registry` field on `WorkerRuntime`**, populated at the worker composition root. **Named `provider_registry`, not `providers`**, because that name is taken in the same file by the AI registry |
| **Blocked on — Lane A** | **A typed `Settings` for `provider_platform` choosing which adapters exist, and a `build_provider_registry` at its composition root.** §10: *configuration is always a typed Settings object **owned by the module that owns the behaviour***. `provider_platform` is Lane A's |
| **Not in scope** | **A new enqueue path.** ADR-0404 dissolves that half: with capability 1 the handler already holds a tenant-scoped session inside its own pool, so **it performs the sync where it stands.** `event_bus/queue.py` stays the relay's and the outbox remains the only way work is scheduled |
| **On claiming** | **Validate ③ first** — `apps/worker/` is outside every §20a-frozen path, and `modules.toml` names its owner. Both hold today; **check rather than assume** |
| **Why it is separate from [TASK-418](#task-418)** | **Different directory, different ownership state.** Bundling would put a buildable slice behind an unassigned one — [C-412](LANE_COORDINATION.md)'s shape |
| **Why it is sequenced, not bundled** | **A `WorkerRuntime` field pointing at a registry nothing populates is the decorative class §2 forbids.** Lane A's half lands first; this one follows and is then a genuinely small slice |

### TASK-417 · Account 360 renders what the platform already knows

| | |
|---|---|
| **Objective** | **Wave 1 of the approved UI, and the first screen built against it.** The approved Account 360 has **27 sections; [414](architecture/414-wave-1-account-360.md) found twelve already served by shipped contracts** — and **none of them is on a screen** |
| **Module** | **Product Surface** — Lane A's, per [`modules.toml`](coordination/modules.toml) |
| **Status** | **`IN VALIDATION` — Lane A**, 2026-08-05. **All ten buildable sections render, and every acceptance criterion is met.** Two were genuinely unmounted and shipped here — observations and competitors; eight already rendered and were **audited against [410](architecture/410-approved-ui-specification.md)'s *"each in six states"*** rather than assumed correct, which found and fixed **three sections that rendered a failed read as an empty account** — the class is now **[C-226](LANE_COORDINATION.md)**. *Twelve* was corrected to *ten* by **[C-225](LANE_COORDINATION.md)**: the technology stack section has no route and was also counted twice. Empty state asserted executably; *no mock business data* already enforced by `no-mock-data.test.tsx` and passing. Frontend suite 1202 across 57 files, `tsc` clean, `eslint` clean. Previously **`CLAIMED` — Lane A**, 2026-08-05, by the Task Claim Protocol. **`next` in [`queues/lane-a.toml`](coordination/queues/lane-a.toml)**, and Product Surface is Lane A's in [`modules.toml`](coordination/modules.toml). **[TASK-405](#task-405--a-iii--a-signal-ends-in-a-decision) is `IN VALIDATION`** — everything shipped except one route, held by **[C-224](LANE_COORDINATION.md)**, a product-owner ruling. **[TASK-904](#task-904--an-organization-can-grow) was not taken though it reads `READY`**: the queue records it blocked on **C-206 and C-208**, two of its three thirds are held, and §20e stops implementation rather than resuming it. Previously **`READY`** — approved scope, decomposed by Lane C 2026-08-05. **Not new scope**: the designs became authoritative on 2026-08-04 and [412](architecture/412-backend-capability-matrix.md) defined the waves |
| **Scope** | **Render only.** The twelve sections 414 marks 🟩: header identity · health score · why the score moved · observations · business events with evidence · detected signals · research · the account summary · opportunities · timeline · technology stack · competitors |
| **Repository reuse** | **Every section consumes a contract that already ships** — `knowledge_graph`, `buying_score_engine`, `observation_engine`, `business_event_engine`, `signal_engine`, `ai_research_engine`, `ai_platform`, `opportunity_engine`, `timeline`, `commercial_profile`. **No backend change, no new endpoint, no new event** |
| **Non-goals** | ⛔ **The other fifteen sections.** Two are person-dependent ([C-221](LANE_COORDINATION.md)), two belong to later waves, and **seven have no source** — 414 §3. **Building a section with no source is inventing data** (§20c) |
| **Why it is one slice and one lane** | **The module is the planning unit and the screen is a consumer** ([`PRODUCT_OFFICE.md`](PRODUCT_OFFICE.md) §5b). Every contract is already published, so this crosses no module boundary — **it is a Product Surface slice that reads `public/`** |
| **Acceptance** | Twelve sections render from live contracts · **a designed empty state where a workspace has no data** · **no mock business data** (§20c) · **the approved design is followed and not reinterpreted** ([410](architecture/410-approved-ui-specification.md)) |
| **Change Budget** | 🟢 — `frontend/` inside the assigned module |
| **Escalate if** | A section needs a contract that does not exist. **That is a finding, not an endpoint to add** |

### TASK-414 · Impact analysis, reported and nothing skipped

| | |
|---|---|
| **Status** | **`IN VALIDATION` — Lane C**, 2026-08-05. **The analysis is emitted at every `--next-cycle` and nothing is skipped.** **`certification-guard.py`'s classifier was extended; no second one was written.** Unknown paths escalate to `platform`; `infra/`, the `Makefile` and `tests/certification/` escalate unconditionally; profiles compose as a **union**. ⚠️ **The first real run found a disagreement, which is exactly what step 1 is for**: `CLAUDE.md` is not under `docs/`, so the impact rules escalated it to `platform` while `_is_closeout` — three hundred lines above, in the same file — treated it as non-executable. **Two classifiers, disagreeing on their first disagreement.** **The documentation rule now derives from `CLOSEOUT_PATHS`/`CLOSEOUT_SUFFIXES` rather than restating them**, and a test pins the agreement. **13 tests** |
| **Module** | `infra/` · `backend/tests/certification/` — **Lane C's** under [D-022](DECISION_REGISTER.md), **and QE's gates stay QE's** |
| **Objective** | **Every certification reports which validations the change required. Every validation still runs.** |
| **Scope** | Extend `--next-cycle`'s path classifier to emit the impact set and the computed profile. **Report only** |
| **Reuse** | **`make certified ARGS="--next-cycle"` already classifies a diff by path**, and `certification-guard.py --audit-main` already checks paths rather than commit messages. **Extend one; do not write a second** |
| **Non-goals** | **Nothing is skipped.** **`REQUIRED_GATES` is not yet computed.** **No option on `make certify`.** No profile is applied |
| **Acceptance** | The report names impacts detected and the profile that *would* apply · **an unrecognised path reports `platform`, never `none`** · **a change touching `infra/`, the `Makefile` or `tests/certification/` reports `platform` unconditionally** · **every existing gate still runs, and the record is unchanged** |
| **Why it is `READY` and TASK-413 is not** | **It removes nothing.** Its whole value is evidence: **if the classifier disagrees with reality even once, the framework is not ready — and finding that out costs nothing, because everything still ran** |
| **Validation** | A test that an unknown path escalates · a test that `infra/` escalates · **a test that the reported profile never omits a Security Invariant** |

### TASK-413 · Change-aware validation — `frontend/`-only skips `dr`

| | |
|---|---|
| **Status** | **`SEQUENCED`** — **trigger: a measured certification wall-clock that demonstrably delayed a promotion, recorded at least twice** |
| **Preparation** | [426](architecture/426-change-aware-validation.md) |
| **Module** | `infra/` — **Lane C's**, under [D-022](DECISION_REGISTER.md) |
| **Scope** | **One rule.** A slice touching only `frontend/**` skips `make dr`; everything else runs it; **a release candidate always runs it** |
| **Reuse** | ⚠️ **`make certified ARGS="--next-cycle"` already classifies a diff mechanically, and `certification-guard.py --audit-main` already checks paths rather than commit messages.** **Extend that classifier — do not write a second one.** Two would eventually disagree, and the one nobody maintains would be the one deciding what to skip |
| **Non-goals** | **No profile system** — a framework for one boundary is speculative abstraction. **No option on `make certify`**: the suite is *computed*, never *passed*. *"A command whose convenient path yields worthless evidence teaches people to use it"* |
| **Inherited constraint** | **`infra/` is never in the harmless set** — `smoke.sh`, `disaster-recovery.sh`, `state-check.py` and the compose files decide whether a gate passes. **Learned from [B-014](BUGS.md)** |
| **Acceptance** | The certification record **states which profile ran and why** · a `backend/`, `migrations/`, `infra/` or compose change always runs `dr` · **no flag exists to skip it** · a docs-only change still never opens a cycle |
| **Why not now** | §14 — **no scalability trigger has fired, and nothing in the repository records `dr` as costly.** The measured bottleneck is that certification is not being *asked for*, not that it is slow |


> **Not `WAITING`, because nothing is undecided, and not `READY`, because nothing may be claimed.** These carry a **trigger** rather than an owner: the work begins when the condition fires, and until then it is preparation the repository holds rather than loses.

### TASK-420 · Epic H — a second hosted vendor reaches production

| | |
|---|---|
| **Epic** | **Epic H · AI Platform — providers, policy and safety**, [437](architecture/437-ai-platform-future-epic.md). **Prepared 2026-08-05 on a Product Office directive; not scheduled** |
| **Module** | `ai_platform` |
| **Status** | **`SEQUENCED`** — **trigger: the approved UI waves are complete and `product_surface` is no longer the lowest-implementation module** *(45% today; every other module is 50%+)* |
| **Slice** | one — the OpenAI adapter |
| **Objective** | **A second hosted vendor serves production traffic with no change above the port.** `OPENAI` is **already ratified in [ADR-0012](architecture/adr/0012-ai-platform-architecture.md)** and *"gains an adapter when a real caller needs them"* |
| **Why it is first** | **It proves the claim the whole epic rests on.** ADR-0012 says a vendor integrates by describing what it supports; **nothing has ever tested that by adding one.** If anything above the port must change, **that is the finding**, and it is cheaper here than under a deadline |
| **Not in scope** | **Bedrock and Azure OpenAI.** They are *reserved* rather than recognised, and `AIVendor` says why: *"a member here with no ratified status is a speculative extension point, and the roadmap's no-speculative-ports ruling applies to enums too"* |

### TASK-421 · Epic H — PII never leaves the tenant unmasked

| | |
|---|---|
| **Epic** | **Epic H**, [437](architecture/437-ai-platform-future-epic.md) |
| **Module** | `ai_platform` |
| **Status** | **`SEQUENCED`** — after [TASK-420](#task-420) |
| **Objective** | **A masking pass at the port boundary, and a Security Invariant that fails when an unmasked field crosses it** |
| **Why it is the largest true gap** | **Measured 2026-08-05: `pii`, `redact` and `mask` appear in zero files under `ai_platform`.** Every inference sends an evidence set to a third party and **nothing inspects it first** |
| **Needs first** | **ADR-C — what is masked, by whom, and how the invariant proves it.** A masking rule with no executable check is a comment |

### TASK-422 · Epic H — a workspace states which providers it allows

| | |
|---|---|
| **Epic** | **Epic H**, [437](architecture/437-ai-platform-future-epic.md) |
| **Module** | ⚠️ **Undecided — that is part of the deliverable.** `workspace_tenancy`, `ai_platform`, or a new context |
| **Status** | **`SEQUENCED`** — after [TASK-421](#task-421), **and blocked on ADR-B** |
| **Objective** | Allowed providers · model restrictions · compliance constraints, **per workspace** |
| **Stays inside the ratified contract** | **Routing by policy is configuration**, which [ADR-0012](architecture/adr/0012-ai-platform-architecture.md) permits. ⛔ **Routing that learns from observed latency or cost is not** — the registry is *"read-only… no adaptive routing that learns from previous calls"* |

### TASK-423 · Epic H — prompt injection is detected and recorded

| | |
|---|---|
| **Epic** | **Epic H**, [437](architecture/437-ai-platform-future-epic.md) |
| **Module** | `ai_platform` |
| **Status** | **`SEQUENCED`** — after [TASK-421](#task-421) |
| **Objective** | **Detection and audit before blocking.** *Record what happened; compute judgements where the inputs are actually known* — the discipline `domain/usage.py` already applies to cost |
| **Measured** | **`injection` and `jailbreak` appear in zero files repository-wide** |

### TASK-424 · Epic H — a workspace has an AI budget

| | |
|---|---|
| **Epic** | **Epic H**, [437](architecture/437-ai-platform-future-epic.md) |
| **Module** | `ai_platform` · usage accounting |
| **Status** | **`SEQUENCED`** — after [TASK-422](#task-422) |
| **Objective** | A workspace-level AI budget and its enforcement point |
| ⚠️ **Not a new metering system** | **`domain/usage.py` already records tokens, latency and retries**, and **[TASK-411](#task-411) is already `SEQUENCED` for usage accounting.** This slice adds a *limit*, not a *meter* — **and pricing stays outside the port**, so a price change re-prices history |

### TASK-425 · A tenant administration surface

| | |
|---|---|
| **Recommendation** | **[437 §4](architecture/437-ai-platform-future-epic.md)** — a foundational gap found by repository-wide measurement, **not part of Epic H** |
| **Module** | Undecided |
| **Status** | **`SEQUENCED`** — **trigger: the first support request that cannot be answered without database access** |
| **Measured** | **`tenant admin`, `admin console` and `back-office` appear in zero documents and zero code files** |
| **Objective** | **Support can see a workspace's state without a database client.** Today they cannot, and that is how production credentials end up on a laptop |


### TASK-426 · A deletion and retention strategy, before there is data to regret

| | |
|---|---|
| **Recommendation** | **[438 §2](architecture/438-platform-initiatives.md) shared foundation S1** — the one row this office proposes out of roughly forty capabilities assessed, and the reason is timing rather than importance |
| **Module** | ⚠️ **Undecided — a repository-wide policy, not a module.** Likely `signora_platform/db/` *(🔴, frozen)* plus a per-module rule |
| **Status** | **`SEQUENCED`** — **trigger: whichever comes first —** *(a)* the first customer contract naming a retention or erasure obligation, *(b)* the first workspace deletion request, or *(c)* **migration 0050**, because the cost of this rises with every table |
| **Objective** | **One answer to: what happens when a workspace, a person or a record must go.** Soft versus hard deletion · cascade order · what survives for audit · restoration · legal hold |
| **Measured 2026-08-05** | **`deleted_at`, `is_deleted` and `soft delete` appear in ZERO files.** There is no strategy, consistent or otherwise, **and nothing has needed one yet.** Meanwhile **26 tables grant `FOR DELETE` and only 10 grant `FOR UPDATE`** — the repository is **edit-averse, not delete-averse**, so erasure is mechanically possible and only the policy is absent |
| **Why now rather than at GA** | **The erasure surface is near-zero today.** [C-221](LANE_COORDINATION.md), ruled 2026-08-05, keeps person-level data out of the platform — *"do not expand the architecture around people until we have a reliable provider capability."* **This is the cheapest moment in Signora's life to decide what erasure means**, and every migration after this makes it dearer |
| **The decision it contains** | **What survives an erasure?** **Immutability says a record of what was true then must not be rewritten** (§2, AC-47). **Erasure says a person's data must go.** Both are correct and they meet in the same row. **Recommended shape: erase the person, keep the event** — a signal that says *a named person changed role* becomes *a role changed*. **The business fact survives; the identity does not** |
| **Not in scope** | **Backup and restore.** `make dr` proves **restart survival**, not backup, and a backup policy is a separate absence — assessed in [438 §0④](architecture/438-platform-initiatives.md) and **not proposed** |
| **ADR candidate** | **The erasure/audit boundary.** A retention rule with no executable check is a comment — the same standard [TASK-421](#task-421) sets for PII masking |


### TASK-427 · M-D · The People domain — a person, and an affiliation with an end

| | |
|---|---|
| **Milestone** | **M-D · People Domain** 🟩 · [441 §1](architecture/441-people-roadmap.md) · stages **S1 · S2** |
| **Epic** | **Epic C**, decomposed by [D-074](DECISION_REGISTER.md). **[TASK-201](#task-201--epic-c--people-intelligence) is the parent row and is unchanged** |
| **Module** | **A new bounded context — `people`** · `knowledge_graph` (`EntityKind.PERSON`). **`modules.toml` gains a row when this is placed, not before** |
| **Status** | **`SEQUENCED`** — **trigger: the first dependent customer-facing capability enters implementation.** ⚠️ **Measured 2026-08-05: the trigger has fired.** **[TASK-202](#task-202--epic-g--copilot) is `READY` and its own row says *"phase 4 needs Epic C"*** — the dependent wrote the dependency down before this decomposition existed |
| **Objective** | **An anonymous `Person` and an `Affiliation` — *person × company × title × interval*.** *"A VP of Engineering joined Acme in March and left in September"* becomes **queryable**, where today it is an event that passes |
| **Blocked by** | **Nothing — and the authority is [D-074](DECISION_REGISTER.md), not [ADR-0400](architecture/adr/0400-person-as-an-entity.md)'s ratification.** ⚠️ **Corrected 2026-08-05 on [B-205](BUGS.md), raised by Lane A.** This cell read *"no ruling — ADR-0400 is ratified"*, and **the ADR says in its own status block that ratifying it *"neither approves nor unblocks Epic C"*** — so the cell cited a document that explicitly declines to authorise the work. **The approval exists and it is D-074**: *"I approve moving the **People domain** implementation earlier in the roadmap. **I am not approving the full People Intelligence feature set.**"* **Domain approved, feature set not** — which is what [441](architecture/441-people-roadmap.md)'s four milestones separate. **And ❓1 gates [TASK-429](#task-429--m-e--a-provider-supplies-a-person-identifier), not this row**: an anonymous `Person` with `Affiliation` intervals needs no person name. **No provider** — the intervals are derived from `RoleChangeValue(title, seniority, direction)` + `occurred_on` + company, **which flow in production today** |
| **Scope bound — [C-221](LANE_COORDINATION.md), unchanged** | ⛔ **No person's name, anywhere.** *"Role-based and organization-level intelligence"* is exactly what this delivers. **C-221's narrowing is not a constraint on this row — it is its specification** |
| **Cost, measured** | **`EntityKind.PERSON` — one enum member**, and the docstring reserves it. **`Affiliation` — a new table, never a migration**, because [ADR-0400](architecture/adr/0400-person-as-an-entity.md) stopped a `current_employer` field from ever shipping |
| **Forbidden in this row** | **No `seniority_score`, no `is_key_contact`, no `priority`, no ordered list read as a ranking.** *"A person is one plausible field away from becoming an influence model."* **Influence is `buying_score_engine`'s and stays there** |
| **Governance** | **A new bounded context is 🔴 and needs an ADR. [ADR-0400](architecture/adr/0400-person-as-an-entity.md) is that ADR, and it is ratified** |
| **On placing** | **Moving this to `READY` is the product owner's** — position is priority. **Lane C prepared the row and did not place it** |

### TASK-428 · M-I · What the domain lets other modules say

| | |
|---|---|
| **Milestone** | **M-I · People Intelligence** 🟦 · [441 §2](architecture/441-people-roadmap.md) · stages **S3** *(now)* and **S5** *(after TASK-429)* |
| **Module** | `timeline` · `commercial_profile` *(a stable `CommitteeRole` id)* · `signal_engine` · `people` |
| **Status** | **`SEQUENCED`** — **trigger: [TASK-427](#task-427--m-d--the-people-domain--a-person-and-an-affiliation-with-an-end) promoted** |
| **S3 delivers** | **A timeline event with a subject · a committee seat that cites a real affiliation · `new_decision_maker` and `decision_maker_departed` naming what changed.** **Two signals are live and scored today with no subject at all** |
| **S5 delivers** | **Org chart · relationship graph · champion tracking · executive movement by name.** ⛔ **Gated on [TASK-429](#task-429--m-e--a-provider-supplies-a-person-identifier)** |
| **Why one row and two stages** | **This is the split the four-milestone separation exists to make visible.** **S3 is C-221's approved scope and needs no provider; S5 is C-221's *"future enhancement once supported by provider capabilities"*.** **A single date for "People Intelligence" would hide a commercial decision sitting in the middle of it** |
| **Sequencing** | ⚠️ **S3 after [TASK-901](#task-901--seven-modules-consume-the-events-they-declare)** — `runtime-composition` reports **2 of 9** consumers wired, and a projection would land dark |
| **Cross-module** | **`commercial_profile` gains one field**, on **the trigger that module wrote down itself**: *"the first consumer that needs to cite a particular seat"* |

### TASK-429 · M-E · A provider supplies a person identifier

| | |
|---|---|
| **Milestone** | **M-E · Provider Enrichment** 🟩 · [441 §2](architecture/441-people-roadmap.md) · stage **S4** |
| **Module** | `provider_platform` *(an adapter)* · `provider_normalization` *(a claim attribute)* · `people` |
| **Status** | **`SEQUENCED`** — **trigger: a provider contract that supplies a person identifier.** ⛔ **A commercial decision, not an engineering one** |
| **Measured 2026-08-05** | **No person's name enters the platform from any source.** `simulation/generators/enrichment.py` emits `type · title · seniority · occurred_on`; `mappers/enrichment.py` reads `name` for **organisations and technologies only**. **[ADR-0400](architecture/adr/0400-person-as-an-entity.md) ❓1, re-checked and still *no*** |
| **Provider independence** | ✅ **[D-074](DECISION_REGISTER.md): *"the existence of the People domain must not depend on provider availability."*** **This row exists so that dependency has somewhere to live that is not TASK-427.** `ProviderPersonIdentity` and `IdentityState` are already the provider-neutral shape |
| **Sequencing** | ⚠️ **[TASK-426](#task-426--a-deletion-and-retention-strategy-before-there-is-data-to-regret) before named people land.** **This is where personal data enters the repository for the first time**, and erasure designed into a bounded context is cheap where retrofitted is not. **`person.forgotten` is TASK-426's first named consumer** |
| **Also gated here** | **[C-210](DECISION_QUEUE.md) + [C-203](DECISION_QUEUE.md)** — personal data, and rendering a person's name. **Deferred by the product owner *"with future People Intelligence work"*, and this is that row** |

### TASK-430 · M-U · The People experiences a customer opens

| | |
|---|---|
| **Milestone** | **M-U · People UI** 🟦 · [441 §2](architecture/441-people-roadmap.md) · stage **S6** |
| **Module** | Product Surface |
| **Status** | **`SEQUENCED`** — **trigger: wave 6, unchanged.** [412 §4](architecture/412-backend-capability-matrix.md) |
| **Delivers** | **The People Intelligence screen · Global Search's people group** |
| **Position, and why it did not move** | ✅ **[D-074](DECISION_REGISTER.md): *"the customer-facing People Intelligence module may still remain later in the roadmap. The underlying domain should not."*** **The anonymous surface is buildable from S3; the org chart and relationship views additionally need [TASK-429](#task-429--m-e--a-provider-supplies-a-person-identifier)** |


### TASK-435 · A seller sees what changed across every account they hold

| | |
|---|---|
| **Supersedes** | **[TASK-902](#task-902--m7-timeline--the-remaining-slices)**, disposed 2026-08-05. **This is the one slice that row was standing in front of** |
| **Module** | `timeline` |
| **Status** | **`SEQUENCED`** — **trigger: [SW-02](architecture/51-sales-workspace.md) is scheduled.** [C-215](LANE_COORDINATION.md) blocks SW-02 and SW-06 **and blocks nothing else** — SW-03, SW-04 and SW-05 compose over `GET /accounts`, which is already workspace-scoped |
| **Specification** | **[C-215](LANE_COORDINATION.md), and it is complete** — the signature, the endpoint, the index and its own scope bound are all named. **Product Office wrote no new scope here; it moved written scope onto a row that can carry a trigger** |
| **The gap** | **`GET /workspaces/{id}/accounts/{account_id}/timeline` is the only timeline endpoint**, hard-scoped `WHERE workspace_id = … AND entity_id = …`. ***"Three Target Accounts became significantly more active since you last looked"* is a query across everything a seller holds, and there is no way to ask it.** The browser alternative is one request per account — **the N+1 pattern §14 calls *a defect at write time, not a future task*** |
| **Contract** | **`feed_for_workspace(workspace_id, *, entity_ids=None, since=None, after, limit)`** beside the existing `feed`, as **`GET /workspaces/{id}/timeline`**. **Same entry shape, same cursor, same ordering** |
| **New index** | **`(workspace_id, occurred_at, id)`** — the existing index is entity-leading and cannot serve this |
| **⛔ Non-goals** | **Read-only, no new judgement.** *"Timeline ranks nothing and explains nothing, and this must not become the place that starts."* **No stored read state** — `since` is a **declared input**, so [TASK-016](#task-016)'s per-user read state is not a prerequisite and **a server-side read state later changes no contract** |
| **Reuse** | **Nine projection rules, migration `0026` with forced RLS and no `UPDATE` grant, nine worker subscriptions and the feed component are all built.** This adds a second read path over the same table |
| **Governance** | 🟠 — the module's own `public/`, a new endpoint and a migration, **announced in the commit message.** **No ADR: [ADR-0038](architecture/adr/0038-timeline.md) already governs the module and no boundary moves** |

### TASK-432 · A triaged signal says so, and the pipeline hears it

| | |
|---|---|
| **Discovery** | **[442 §F3](architecture/442-product-led-domain-discovery.md)** — Product-Led Domain Discovery from the approved UI |
| **Module** | `signal_engine` · [06-events.md](architecture/06-events.md) |
| **Status** | **`SEQUENCED`** — **trigger: the next `signal_engine` slice.** Small enough to travel with one |
| **The gap, measured 2026-08-05** | **Signal Center's specification is *"a triage queue, not a notification list — every signal ends in a decision"*, and `signal_engine/domain/resolution.py` implements it**: `Resolution` · `Actioned` · `Assigned` · `Snoozed` · `Dismissed` · `DismissalReason`. **The catalog publishes `signal.generated` and `signal.superseded` and nothing for the decision** |
| **Why it ranks above its screen count** | **A human decision is the one thing in this pipeline that produces no business event.** `timeline` cannot project it, **[TASK-406](#task-406--a-iv--an-icp-criterion-is-scored-against-outcomes) measures ICP criteria against outcomes and *dismissed with a reason* is an outcome**, and no report can count it. **The row records the state; nothing records the transition, so every day without it loses evidence that cannot be recovered** |
| **Reuse** | ✅ **The domain is built.** This adds **one event type** on the envelope the catalog already uses 34 times — **explicitly *"a use of the platform, not a change to it"* (§20a)** |
| **Not in scope** | **No notification.** [ADR-0040](architecture/adr/0040-notifications.md) is deferred by [D-027](DECISION_REGISTER.md) and this does not touch it — **an event is what the pipeline hears, not what a person is told** |

> ### Sequencing principle — **P-01 · Domain precedence** ([D-074](DECISION_REGISTER.md))
>
> **A foundational domain is introduced before *multiple* customer-facing capabilities begin building temporary representations of that same concept.**
>
> **A temporary representation is a stated absence, a placeholder, or a locally-shaped copy of the concept inside one screen's own module.** **The threshold is two**: one screen shipping an absence is a scope decision, **two is a sequencing defect** — the second is where rework begins. **Checked against [412 §2](architecture/412-backend-capability-matrix.md)'s `Screens` column and §4's wave order, whenever a wave plan is written or amended.** **The full statement and its check are [441 §5](architecture/441-people-roadmap.md).**

> ### Classification — every future initiative carries one ([D-072](DECISION_REGISTER.md))
>
> 🟦 **Customer Product** — a customer interacts with it · 🟧 **Internal Operations** — only Signora sees it · 🟩 **Platform / Foundation** — substrate every module uses · ⬜ **Architecture / Governance** — a decision or a rule, not a surface
>
> **The roadmap at Epic and Capability level lives in [438 §8](architecture/438-platform-initiatives.md).** **Rows here stay high-level for work far from execution**; the owning lane writes the implementation package when an initiative becomes active — **which is [D-060](DECISION_REGISTER.md) unchanged, applied to the roadmap.**


### TASK-411 · Usage Accounting — meter what a workspace consumed

| | |
|---|---|
| **Status** | **`SEQUENCED`** — **trigger: the Billing screen is scheduled for implementation** |
| **Preparation** | [424](architecture/424-usage-metering-assessment.md) §9a — six slices, most of them reads |
| **Module** | ⚠️ **Deliberately unnamed.** [D-042](DECISION_REGISTER.md): *"do not force a module boundary until implementation naturally reaches it"* |
| **Reuse** | **`ai_inference` · `provider_sync` · `membership` already meter, per workspace, immutably.** Slices 1–3 are `UsageReader` ports over tables and indexes that exist |
| **Non-goals** | **No `usage_event` table and no per-action usage event** — two representations of one call (§2). **No new datastore** ([D-044](DECISION_REGISTER.md)). **No pricing on an operational row** (§10) |
| **The one materialization** | **A closed billing period**, immutable — the `ai_narration` pattern. **Deriving it means a later data change silently re-prices a shipped invoice** |

### TASK-412 · Usage & Billing Observability

| | |
|---|---|
| **Status** | **`SEQUENCED`** — **trigger: TASK-411 slices 4–5 complete** |
| **Preparation** | [424](architecture/424-usage-metering-assessment.md) §9b |
| **Serves** | Customers · engineering · finance · support |
| **Reuse** | Every figure derives from TASK-411's readers. **No second aggregation** |
| **Non-goals** | **Quotas are entitlement, not metering** · **forecasting is a projection over recorded facts, never a model** · **anomaly detection is out of scope** — it is `signal_engine`'s shape, and a meter that decides something is anomalous has started inferring |
| **Worth naming** | **Meter health.** A meter that silently stops recording produces a *smaller* invoice, **so the failure is invisible from the billing side** and detectable only against operational history — which is the argument for building reconciliation rather than buying it |

## WAITING — on a decision, and on whom

| Id | Task | Module | Waiting on |
|---|---|---|---|
| ~~**TASK-006**~~ | ~~[C-010](LANE_COORDINATION.md) — no lane is assignable to `apps/`, `signora_platform/` or repository process~~ | Repository | ✅ **ANSWERED, TWICE, and removed from this table 2026-08-05.** **[D-022](DECISION_REGISTER.md)** expanded Lane C to Platform Foundation; **[C-416](LANE_COORDINATION.md) / [D-073](DECISION_REGISTER.md)** then gave it `backend/signora_platform/` entire. **`modules.toml` carries both paths.** **The four defects it named — [B-007](BUGS.md), [B-012](BUGS.md), [B-013](BUGS.md), [B-014](BUGS.md) — landed in a gap that no longer exists.** ⚠️ **It sat here reading *"the highest-value decision on this page"* for a day after it was ruled** |
| ~~**TASK-007**~~ | [C-008](LANE_COORDINATION.md) — sellers cannot see what their company sells | Product Surface | ✅ **CLOSED 2026-08-05 by delivery, not by a ruling.** **Answered 2026-08-03 — option C now, D next.** Stage 1 shipped as **CX-05**; **stage 2 shipped as [TASK-903](#task-903--a-seller-can-see-what-their-company-sells), `IN VALIDATION` — claimed and shipped the same day.** ⚠️ **This row said *"stage 2 is unclaimed and is not `READY` until the product owner places it"* while stage 2 was already being built** — Lane C narrowed TASK-903 to stage 2 and queued it, and never came back to the row that was still asking for the placement. **A placement act reported as outstanding after the work shipped is the same defect as a ruled decision left in the queue** |
| **TASK-008** | [C-005](LANE_COORDINATION.md) — the signal-profile write path | `signal_engine` | **The product owner**, on whether a customer should author relevance at all. Ownership answered; sequencing is not |
| **TASK-009** | [C-009](LANE_COORDINATION.md) — an internal fault reaches a customer as a `422` | `signora_platform` | **The product owner.** A frozen-platform change under §20a, with a full proposal recorded |
| **TASK-010** | [C-006](LANE_COORDINATION.md) — which lane owns `test_api_<module>.py` | Repository | **The product owner**, and deliberately: *"avoid creating a local convention that later becomes repository behaviour"* |
| **TASK-011** | The brief's hierarchy pass (D20) | Product Surface | **A seller in the room.** A collaborative product-design activity, not a slice |
| **TASK-012** | M9.5 Step F | AI Platform | **The product owner.** Inserted, open, and the oldest outstanding commitment on the board |
| **TASK-013** | `reasoning@1` has no released model | `ai_reasoning_engine` | **The product owner.** The Decision Package would refuse at runtime. **Do not tune the prompt, delimiter, schema or timeout to make it pass.** ⚠️ **Possibly answered 2026-08-05**: *"continue designing around hosted evaluation providers through the AI Gateway abstraction… the credential provisioning will be handled separately."* **That names the path; it does not yet name a released model, so the row stays until one exists** |
| **TASK-017** | **M7 — Timeline.** [C-020](LANE_COORDINATION.md) — no milestone definition, no module design, Meilisearch unprovisioned, event scope unagreed | `timeline` | **The product owner.** Two decisions: the §6 milestone definition, and Meilisearch now or Postgres-first on a stated trigger. **Assigned to Lane B 2026-08-02 and released the same day** — the module assignment stands; the work is not executable until the architecture is agreed |
| **TASK-431** | **A change is proposed, approved, applied as one named thing, and can be taken back.** [442 §F1](architecture/442-product-led-domain-discovery.md) — **six approved screens assert this guarantee in the design project's own words and the repository has no representation of it.** Workflow Automation *"approved before it writes, reversible after it does"* · Opportunity Intelligence *"nothing sends without your approval, reversible for 24 hours"* · Companies *"reversible for 24 hours as a single named batch"* · Settings *"attributed, reversible, in the audit log"* · **AI Copilot's 17 surfaces *"proposes rather than commits… attributable and reversible"*** · Account 360's AI sections inherit it. **The finding is that the AI contract and the bulk-edit contract are the same contract.** ✅ **Propose exists** (`Recommendation`; *"Intelligence suggests. Humans commit."*) · ✅ **attribution exists** (`actor_id`, 37 files) · ✅ **reversal-as-supersession exists five times** · ⛔ **a named unit, a window, and the verbs `approve`/`withdraw` do not** | **Undecided — 🔴** | **The product owner**, on **shape**: *(a)* a platform capability · *(b)* **a domain concept in one owning context — Lane C's recommendation** · *(c)* per-module, deliberately. **Nothing is prepared further until this is ruled**, and *(c)* is the five-implementations outcome |
| **TASK-433** | **Scope, a saved view, and a word that is already taken.** [442 §F2](architecture/442-product-led-domain-discovery.md) — the App Shell applies global scope *"before a module renders"* and **all 16 screens inherit it**; Companies needs *"saved views and segments"*; Global Search needs *"saved and monitored searches"*. **`saved_view`, `saved search` and `monitored` return zero matches repository-wide.** ⚠️ **And `Segment` is already `commercial_profile`'s** — a named ICP segment with its own state machine, meaning *who buys*. **Companies' "segment" is a saved filter over accounts. Two concepts, one word, and §4 forbids the collision in advance** | Product Surface · **undecided** | **The product owner — on the *naming*, not the placement.** **[O3](DECISION_REGISTER.md) stays deferred and this does not reopen it**: O3 asked *where shell services live*; this asks *whether a saved view is a domain concept and what it is called.* **One sentence today; a rename across a bounded context later** |

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

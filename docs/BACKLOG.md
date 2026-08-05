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
| **Status** | **`CHANGES REQUESTED` — transferred to Lane B**, 2026-08-04. *(consolidated to Lane B 2026-08-04 — [D-058](DECISION_REGISTER.md))* **A7's backend shipped** at `d8f5832`, and the return is [B-107](BUGS.md): ten tests in that slice have never passed. **A7's render is blocked on [C-219](LANE_COORDINATION.md)** (Lane C, the `subject`↔entity join) and **A6 on [C-321](LANE_COORDINATION.md)** (the product owner) — **neither moved with the transfer.** §20e sends returned work to the implementing lane, and **Lane B addresses it before claiming from the queue** |
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
| **Status** | **`READY` — partly delivered.** See the note below |
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
| **Status** | **`BLOCKED` — [C-221](LANE_COORDINATION.md)**, which is the product owner's. **Released from Lane A on the 2026-08-04 consolidation ([D-058](DECISION_REGISTER.md)) — the claim carried no code.** **It returns to the queue blocked rather than ready, and the transfer changed nothing about why**: no person's name enters the platform at any point, so an identity model still has nothing to identify. **A consolidation moves who would build it, never whether it can be built** |
| **Assigned** | **Lane A, directly by the product owner, 2026-08-04**, on Lane C's prepared research, ADR and specification |
| **Blocked by** | **[C-221](LANE_COORDINATION.md) — ADR-0400's own ❓1, checked first as the ADR instructs, and the answer is *no*.** The platform receives no person name at any point, so an identity model has nothing to identify |
| **On claiming** | **ADR-0400 is `PROPOSED`, not ratified**, and it says so in its own status block. A new bounded context is 🔴. The product owner's assignment is the epic approval; **the ADR still needs its ratification stamp, which only the product owner can apply** |

### TASK-202 · Epic G — Copilot

| | |
|---|---|
| **Epic** | **Epic G**, [404-epic-g-copilot.md](architecture/404-epic-g-copilot.md). **Assigned whole** |
| **Module** | `ai_reasoning_engine` · `ai_platform` (evaluation) · Product Surface |
| **Status** | **`BLOCKED` — [C-222](LANE_COORDINATION.md)**, 2026-08-05. Claimed by Lane B that morning, and **the epic's own first phase turned out to be blocked on a decision rather than on engineering.** **[TASK-408](#task-408--b-ii--search-results-are-grouped-and-the-ranking-is-explainable) stands higher and was skipped with its reason recorded in that row** |
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
| **Status** | ⚠️ **`READY` — and its first slice is already delivered.** Claimed by Lane B 2026-08-05 and **released the same day without a line of code, because the reuse audit the row itself demands found the work built.** **The disposition of this row is Lane C's and the product owner's, not this lane's** — it is neither reordered nor removed here |
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
| **Module** | `signal_engine` — **Lane B's** *(consolidated to Lane B 2026-08-04 — [D-058](DECISION_REGISTER.md))*, via TASK-203 |
| **Status** | **`READY`**. **Released from Lane A on the 2026-08-04 consolidation ([D-058](DECISION_REGISTER.md)) — the claim carried no code.** Returned to the queue; **Lane B claims it in priority order** rather than inheriting it, because the pull model is what keeps priority the product owner's |
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
| **Status** | **`CLAIMED` — Lane B**, 2026-08-05, by the Task Claim Protocol. **Released from Lane A on the 2026-08-04 consolidation ([D-058](DECISION_REGISTER.md)) — the claim carried no code**, and [D-065](DECISION_REGISTER.md) keeps `commercial_profile` with this lane because it holds active work there. **[TASK-405](#task-405--a-iii--a-signal-ends-in-a-decision) stands higher and was skipped with its reason recorded** — `signal_engine` transitions to Lane A |
| **Assigned** | **Lane A, by the product owner, 2026-08-04** — *"you may proceed with A-iii and A-iv when their corresponding READY task rows exist on integration."* **The rows landed with Lane C's synchronization at `3ab3111`**, which is the condition the ruling named |
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
| **Status** | `READY` |
| **Notes** | **Read-only, for `member`, beside the account brief** — not under `/settings`, where the granted read is unreachable behind `workspace:update`. `policy.csv` already grants `member` read on `product`, `icp`, `buying_committee` and `commercial_focus`: **the API and the product disagree, and the API is right** |
| **On claiming** | Open a `C-` item for the mount if the two halves are claimed by different lanes. **Placement is judgement** ([ADR-0100](architecture/adr/0100-delegated-dependency-rulings.md) R-5) — say so in review if it reads wrong |
| **Repository check, 2026-08-03 — Lane A** | **Half of this shipped, and the premise above is no longer true.** [C-008](LANE_COORDINATION.md) was ruled by the product owner — **option C now, option D next** — and stage 1 shipped as **CX-05** at `e3516c4`: `/business`, member-reachable, **five** declarations rather than four (`target_account` carries the same grant). **The granted read is no longer unreachable.** What remains is stage 2 — the declarations *on the account brief* — and it is **one lane, not two**: stage 1 needed no backend change and the display half of stage 2 needs none either. **Anything asserting *this account matches this ICP* is still blocked on [C-002](LANE_COORDINATION.md)**, which has no owner. **Not reclaimed, not reworded, not rescoped by this lane** — status and position are Lane C's and the product owner's ([C-217](LANE_COORDINATION.md)) |

### TASK-904 · An organization can grow

| | |
|---|---|
| **Module** | `workspace_tenancy` |
| **Slice** | invitation table · acceptance · members list |
| **Status** | `READY` |
| **Notes** | **Signora owns the invitation.** An `invitation` table keyed by email; acceptance matches a pending row against the **`email` claim already in the verified JWT**. **Better Auth's `organization` plugin is not adopted** — migration `0005` revokes `signora_app` from the `auth` schema, so plugin-owned membership is membership the Python tier cannot read, and §13 requires it re-verified every request |
| **On claiming** | **v1 delivery is a shareable link, not email.** No transactional-email dependency is added. **That half is judgement** and is the ruling to challenge first if you would rather ship with email |

### TASK-905 · A contraction risk stops looking like an opportunity

| | |
|---|---|
| **Module** | Product Surface · `buying_score_engine` owns posture |
| **Slice** | one slice |
| **Status** | `READY` |
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

## SEQUENCED — prepared, and waiting on a named trigger

### TASK-415 · A deterministic mock AI provider, and development stops needing a model

| | |
|---|---|
| **Objective** | **A developer can clone the repository, run the stack, and exercise every AI path without downloading a model.** Today `build_provider_registry` registers exactly two adapters — Anthropic and Ollama — so the running application has no deterministic option |
| **Module** | `ai_platform` |
| **Status** | ✅ **`APPROVED` by the product owner 2026-08-04 — awaiting the owning lane's implementation package.** **This is the first task to run the [D-060](DECISION_REGISTER.md) loop end to end**: `ai_platform`'s current assignee prepares, marks it `UNDER REVIEW`, and **Lane C reviews rather than authors it.** **Lane C has deliberately not written the package** — *"do not centrally prepare implementation packages."* ⚠️ **The product owner's framing is a scope correction worth carrying into the package**: *"it is not merely a test double. Treat it as a first-class development provider implementing the existing provider port"* |
| **Scope** | `modules/ai_platform/infrastructure/adapters/mock.py`, implementing the **existing** `AIProviderAdapter` port. Configurable **content · failure · latency · token usage · timeout · retry count**. Registered by `build_provider_registry` **only when explicitly configured** |
| **Repository reuse** | **The port is unchanged** — one `describe`, one `complete`. **The failure taxonomy already exists**: `AITransientError` · `AIRateLimitedError` · `AIPermanentError` · `AIOutputUnusableError`. **`tests/ai_platform/fakes.py` already does half of this** and its behaviour is promoted rather than rewritten. **`signora_platform/simulation/faults.py` is the proven pattern** at the data-provider boundary |
| **Non-goals** | ⛔ **No streaming simulation. No tool-call simulation.** The port has neither, deliberately — *"a wider port would force every future vendor to implement methods most of them do not have, and the usual outcome is adapters raising `NotImplementedError`, which is a contract that lies."* **The mock must never lead the port** |
| **Acceptance** | The stack runs and every AI path answers with **no Ollama and no API key** · each of the six knobs is independently settable · **a Security Invariant asserts the mock is never registered in a production configuration** |
| **Why that invariant is not optional** | `build_provider_registry` already warns that a service which *"could quietly reach a local runtime when its vendor was unreachable would serve customers from a model nothing evaluated."* **A mock makes that failure worse**: a production service answering from a deterministic stub would be indistinguishable from one that worked |
| **Change Budget** | 🟠 — a new adapter is an adapter registration, which [ADR-0028](architecture/adr/0028-model-runtime-by-environment.md) already governs. **No port change, no new bounded context, no new dependency** |
| **Escalate if** | The port needs to change. **That is a different task and an ADR** |

### TASK-416 · An evaluation run states which provider served it

| | |
|---|---|
| **Objective** | Evaluation should **name its provider rather than inherit one.** `__main__.py` reads `model = args.model or settings.ollama_model` — **`--model` already works, so this is a default, not a constraint** |
| **Module** | `ai_platform` (evaluation) |
| **Status** | ✅ **`APPROVED` — [431 §7](architecture/431-ai-execution-modes.md) is answered.** *"Evaluation reports may record the provider used for execution. This is operational metadata rather than product behaviour… it does not weaken the existing principle that evaluations remain model-centric."* **Awaiting the owning lane's package**, like TASK-415. **Four of the six required fields already exist** — `model`, `prompt_version`, `rendering_protocol_version`, and `prompt_fingerprint`, which is stronger than requested. **`provider` and `execution_mode` are the whole of the change** |
| **The question** | **`report.py` deliberately names no vendor**: *"nothing in evaluation may: the run asked for a model."* **Model-centric resolution is a ratified permanent principle** (`CLAUDE.md` §10). **Reproducibility wants to know what served a run; the principle says the model already is that.** **Likely they agree** — `claude-sonnet-4-5` names its server as precisely as `llama3.1:8b` does — **and if so this is a default change and nothing more** |
| **Repository reuse** | **The harness is already vendor-neutral** — *"it knows no vendor. It names a model; who serves it is the registry's business."* **Nothing needs building; a default needs choosing** |
| **Change Budget** | 🟢 for the default. **🔴 if the report gains a vendor field** — that amends ADR-0028 and touches a ratified principle |


### TASK-414 · Impact analysis, reported and nothing skipped

| | |
|---|---|
| **Status** | **`READY`** — **no trigger, no decision outstanding.** Step 1 of [427](architecture/427-impact-based-validation.md) |
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
| **TASK-006** | [C-010](LANE_COORDINATION.md) — no lane is assignable to `apps/`, `signora_platform/` or repository process | Repository | **The product owner.** Four defects have landed in this gap: [B-007](BUGS.md), [B-012](BUGS.md), [B-013](BUGS.md), [B-014](BUGS.md). **The highest-value decision on this page** |
| ~~**TASK-007**~~ | [C-008](LANE_COORDINATION.md) — sellers cannot see what their company sells | Product Surface | **Answered 2026-08-03 — option C now, D next.** Stage 1 shipped as **CX-05** by Lane A, under the product owner's explicit Product Surface assignment. **`IN VALIDATION`.** Stage 2 is unclaimed and is not `READY` until the product owner places it |
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

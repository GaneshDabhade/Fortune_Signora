# 417 — Executable slice audit: what can begin without the platform designs

> **Lane C — Product Office, 2026-08-04**, on the product owner's instruction to determine whether Lane A and Lane B can begin additional implementation immediately. Measured against `origin/integration`.
>
> **This recommends; it does not assign.** `CLAUDE.md` §20e: *"Lane C recommends; the product owner chooses."*

## 0 · The headline, before the tables

> **Neither lane is idle, and neither lane is starved.** Lane A holds **five** claimed tasks; Lane B holds **two**. **The question is not utilisation — it is whether the *blocked* ones are really blocked.**

**They mostly are.** The blocker re-audit found **three genuinely executable slices behind items previously treated as blocked**, and **one previously-exposed item that I have to withdraw** because it is blocked after all.

**And there is a constraint worth stating first, because it shapes every recommendation below:**

> **Almost all unblocked backend work sits in modules Lane A already holds.** Lane A currently has `signal_engine` and `commercial_profile` (Epic D), `ai_reasoning_engine` (Epic G), `sales_engagement`, `opportunity_engine`, `provider_platform` and Product Surface. **Lane B holds `knowledge_graph` and `integrations` — and `integrations` is the one blocked on C-326.**
>
> **So the honest finding is not *"here is work for both lanes."* It is *"there is real unblocked work, and one-lane-per-module puts most of it in one lane."*** That is a sequencing fact for the product owner, not something Lane C should resolve by inventing work for the other lane.

## 1 · Blocker re-audit

**Every remaining blocker, re-tested against the four categories the directive names.**

| Blocker | Blocks | Verdict |
|---|---|---|
| **O1 / [C-221](../LANE_COORDINATION.md) — Person** | **Implementation**, and more than I previously said | ✅ **genuine** |
| **[C-326](../LANE_COORDINATION.md) — inbound source port** | **Implementation.** [ADR-0300](adr/0300-inbound-source.md) consequence 1 is 🟠 Lane B, which looked executable — **but building the port *is* the ruling.** A lane may not proceed where proceeding encodes the answer | ✅ **genuine** |
| **[ADR-0402](adr/0402-a-rule-is-data.md) — workflow** | **Implementation.** A new bounded context is 🔴 | ✅ **genuine** |
| **O2 — notifications** | **Delivery only.** It does **not** block Signal Center triage, which is resolution state rather than notification | ⚠️ **narrower than recorded** |
| **O3 — shell services** | **Placement, not implementation** — for saved views. See §2a | ⚠️ **narrower than recorded** |
| **[C-222](../LANE_COORDINATION.md) / TASK-013** | **Already exposed** — Lane C found it was *"a measurement nobody has taken, not a product decision"*, and Lane A ran it | ✅ **resolved** |
| **Product telemetry** — usage, licences, NPS | **External system.** No source has ever existed | ✅ **genuine, external** |
| **HubSpot developer application** | **External system**, and the product owner's | ✅ **genuine, external** |

### The correction I owe

**In an earlier pass I reasoned that People Intelligence's *Coverage by role* card was role-level and therefore buildable without Person.** `CommitteeRole` is *"never a person's name: this is a template"*, which supported it.

**It does not survive checking.** The card reads *"Economic buyer — Missing — present in 91 of 96 won deals."* **Both halves need Person**: *missing* means no person fills the role at this account, and *91 of 96* means knowing which roles were filled in past deals. **The declared committee supplies the role vocabulary and nothing else.**

> **Person blocks more of Epic C than I said, not less.** The same applies to ICP Builder's *Decision makers* group — *"VP Operations or above · exists · identified"*, *"Sustainability owner · exists · named"* — **four criteria, all person-existence.**

## 2 · Executable slices exposed by the audit

### 2a · The saved-view store — required by four approved screens, blocked by nothing

**O3 asks *where the shell's scope service lives*. It does not ask whether a named view is persisted, and four approved screens say it must be:**

> **Companies** — *"pinning is per view, not per user, **so a shared view looks the same for everyone**"* · **App Shell §6** — *"survives navigation, serialises to the URL, and can be saved as a named view"* · **Global Search** — *"a saved search stores the query, the filters and the sort — not the results"* · **Reports** — *"views are shared by link and respect each viewer's permissions"*

**Shared, permission-respecting and durable means server-side.** It cannot be `localStorage` and satisfy *"looks the same for everyone."*

**So the store is required regardless of how O3 is answered.** O3 decides who *consumes* it.

> ⚠️ **One thing it does not resolve: which module owns it.** It is workspace-scoped, user-attributed, cross-module state. **That is the same shape as [C-010](../LANE_COORDINATION.md) / TASK-006** — *"no lane is assignable to `apps/`, `signora_platform/` or repository process"* — which the backlog already calls *"the highest-value decision on this page."* **Recommend the slice; flag that its home is a placement question, not an implementation one.**

### 2b · Signal Center triage state — absent, required, unblocked

**The approved screen: *"A triage queue, not a notification list · every signal ends in a decision"* — actioned, assigned, snoozed or dismissed with a reason; *"nothing is deleted — every resolution is auditable"*; *"snoozed signals return at the stated time with their original evidence intact"*; *"dismissal reasons feed rule precision."***

**None of it exists.** `frontend/lib/state/triage.ts` is a **naming collision, not an implementation** — its own docstring says *"every question below is a filter over a fact the server already computed… it counts and groups"* and *"this partitions; it never re-ranks."*

**O2 does not block it.** Notification *delivery* is ADR-0040; **resolution state is `signal_engine`'s own.**

> **One reuse constraint, and it is load-bearing.** `opportunity_engine` already models `DISMISSED`, *"deliberately distinct from `CLOSED_LOST`… one is feedback about Signora's judgement, the other is a sales outcome."* **A signal-level dismissal is that same concept one level down, and must not invent a second dismissal vocabulary** — `CLAUDE.md` §4, *never introduce a second definition of a concept a module already owns.*

### 2c · The two interface layers — built, tested, unreachable

**`sales_engagement` and `ai_reasoning_engine` have no `interface/` directory.** `sales_engagement`'s `public/` already exports `Approach`, `ApproachBrief`, `NextAction`, `Recommendation`, `Risk`, `ProductFit`, `RankedRole` — **every one of which the approved Copilot and Opportunity Intelligence screens render.**

**No ruling needed. An interface layer over a module's own `public/` is 🟠, not 🔴.** The pattern is now at six instances and has never once required a domain change.

## 3 · Screen classification — all 16

| Screen | Classification | |
|---|---|---|
| **Account 360** | **READY NOW** | Eleven sections; [414](414-wave-1-account-360.md) is the package |
| **AI Copilot** | **READY NOW** | The two interface layers, §2c |
| **Signal Center** | **READY NOW** | Triage state, §2b |
| **Companies** | **READY NOW** | Saved views §2a · bulk · export. Segments reuse `icp-segments` |
| **Design System v2** | **READY NOW** | **Needs no backend at all** |
| **ICP Builder** | **READY NOW**, partially | Criterion lift and backtest are computable from `/accounts/decided`. **Its *Decision makers* group is BLOCKED BY PRODUCT** |
| **Executive Dashboard** | **READY NOW**, partially | Coverage, conversion, ageing and movement are arithmetic over stages and dates. **The AI projection is BLOCKED BY PRODUCT** |
| **Global Search** | **READY NOW**, partially | Accounts are searchable today; typed grouping and explainable ranking are unblocked. **People blocked by O1; calls blocked externally** |
| **Reports** | **READY NOW**, and **deliberately last** | Nothing blocks it; nothing reuses into it; nothing depends on it |
| **Opportunity Intelligence** | **BLOCKED BY IMPLEMENTATION** | Needs the probability model and aggregates. Competitor mentions need conversation intelligence |
| **AI Research** | **BLOCKED BY IMPLEMENTATION** + **ARCHITECTURE** | Cohort research does not exist; the screen inherits shell scope ([416](416-ai-research-scope-gap.md)) |
| **App Shell** | **BLOCKED BY ARCHITECTURE** (O3) + **READY AFTER PLATFORM UI** | Five of its 22 sections overlap incoming modules ([415](415-platform-foundation-incoming.md) §3) |
| **Settings** | **READY AFTER PLATFORM UI** | Overlaps incoming Modules 3, 4, 6 and 8 |
| **People Intelligence** | **BLOCKED BY PRODUCT** | O1 / C-221 |
| **Workflow Automation** | **BLOCKED BY PRODUCT** | ADR-0402 unratified |
| **CRM Integrations** | **BLOCKED BY PRODUCT** + **EXTERNAL** | C-326, and the HubSpot developer application |

**Nine READY NOW in whole or part · four blocked by product · two waiting on platform UI · one blocked by implementation.**

## 4 · Recommended opportunities, by lane

**Recommendations only. Order within a lane is the product owner's.**

### Lane A — holds the modules most of this work lives in

| | Slice | Why this lane | Reuse |
|---|---|---|---|
| **A-i** | **`interface/` for `ai_reasoning_engine`** | **Already holds it** — TASK-202, Epic G | ⚠️ **Corrected in [TASK-403](../BACKLOG.md).** Its `public/` ends `__all__: list[str] = []` — **there is nothing to expose yet.** The slice is *publish the contract, then expose it*, and is larger than this row implied |
| **A-ii** | **`interface/` for `sales_engagement`** | **Built it** (`50-sales-engagement.md`) | 25+ exported types, unchanged |
| **A-iii** | **Signal Center triage state** | **Holds `signal_engine`** via Epic D | `opportunity_engine`'s dismissal vocabulary — **reuse, do not redefine** |
| **A-iv** | **ICP criterion lift and backtest** | **Holds `commercial_profile`** via Epic D | `/accounts/decided` · existing ICP declaration |

**Estimated 4 slices, in that order.** A-i and A-ii are independent of everything; A-iii is the largest and is self-contained; A-iv depends on neither.

### Lane B — narrower, and honestly so

| | Slice | Why this lane | Reuse |
|---|---|---|---|
| **B-i** | **Global Search — typed grouping and explainable ranking over accounts** | **Holds `knowledge_graph`**; `account-search` exists | The existing search endpoint |
| **B-ii** | **The saved-view store** | **No lane holds it**, and Lane B has capacity. ⚠️ **Placement is a C-010-shaped question** | Casbin for per-viewer permissions |

**Estimated 2 slices.** **B-ii is a recommendation with a caveat attached, not a clean one** — if the product owner would rather settle ownership first, that is the right call and Lane B has only B-i.

> **I am not going to pad this.** Lane B's clean, unambiguous capacity is **one slice**, because its second module is the one blocked on C-326. **Repository correctness is worth more than symmetry between lanes.**

## 5 · What must wait

| | |
|---|---|
| **Platform designs** | Settings · App Shell's user menu, notifications, shortcuts, error and empty states · anything in the ten incoming modules |
| **Architecture** | Shell scope service (O3) · AI Research cohort scope · `workflow` (ADR-0402) · the inbound source port (C-326) |
| **Product** | People Intelligence and ICP's decision-maker criteria (O1) · the Executive Dashboard's AI projection · M14b's bounded context (C-200) |
| **External systems** | Product usage telemetry · conversation intelligence · third-party intent · the HubSpot developer application |

## 6 · Updated priority order

**1** A-i · A-ii — interface layers · **2** Account 360 composition · **3** A-iii — triage state · **4** B-i — search grouping · **5** A-iv — ICP backtest · **6** B-ii — saved views *(pending placement)* · **7** Executive Dashboard aggregates · **8** everything blocked, in the order its blockers clear.

## 7 · The wave after the transition

> **Wave 2 stands and grows: the two interface layers, Signal Center triage, ICP backtest and search grouping.** All five are backend, all five are required by an approved screen, and **none needs a decision from anybody.**

**Wave 1 is unchanged** — Account 360, one screen ([414](414-wave-1-account-360.md)).

**Nothing was invented for this document.** Every slice above traces to a section of an approved screen and a module that already exists. **Where I could not find unblocked work — Lane B's second slice — I said so rather than filling the row.**

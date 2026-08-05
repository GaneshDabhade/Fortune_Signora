# 442 · Product-Led Domain Discovery — what the approved UI requires, and what the domain does not have

**Lane C · Product Office · established 2026-08-05, on the Product Owner directive *Product-Led Domain Discovery from Approved UI*.** **A living document.** *"This assessment should evolve as the product evolves."*

> **The methodology change, in one line:** *"The UI is now the primary source of product requirements."* **Planning runs from the finished product experience backwards to the domain**, instead of forwards from whatever implementation happened to discover.

**Measured against `origin/integration` @ `6cb87ad`. No screen is designed here, no lane is named, and nothing is implemented.**

---

# 0 · What this document is, and what it is not a second copy of

**Four documents already sit between the approved UI and the repository. This one goes a level below all of them, and it is deliberately the only one that does.**

| | Answers | Stops at |
|---|---|---|
| **[410](410-approved-ui-specification.md)** | *What became authoritative?* | The inventory of 16 specifications |
| **[411](411-ui-convergence-assessment.md)** | *Which module serves which screen?* | **Module** and **endpoint** |
| **[412](412-backend-capability-matrix.md)** | *In what order?* | **Wave** and **capability** |
| **[37](37-product-surface.md) · [PRODUCT_EXPERIENCE](../PRODUCT_EXPERIENCE.md)** | *What can a buyer not do?* | **Capability** — MC-1…MC-10 |
| **442 — this** | ***What must exist underneath?*** | **The domain concept**, and it does not stop until it reaches one |

> **Every one of those four answers a question at the level of a *capability*.** *"Saved views"*, *"triage state"*, *"notification"*, *"export"*. **A capability is what a customer is missing; it is not what the repository must model** — and the four rows above have been read to mean *"a screen needs an endpoint"* four times, which is where the ladder in §0a stops too early.

## 0a · The method — the ladder, and the gate at the bottom

**The directive's own instruction, applied literally**: *"Do not stop at APIs. Continue asking until reaching foundational concepts."*

```
  screen asserts a behaviour
        │
        ▼   what is it showing?          ──▶  entity
        ▼   what relates to what?        ──▶  relationship
        ▼   what changes it?             ──▶  lifecycle · state machine
        ▼   what records the change?     ──▶  business event
        ▼   who may cause it?            ──▶  Resource × Action
        ▼   what must survive it?        ──▶  history · audit · attribution
        ▼   what would five screens      ──▶  PLATFORM CAPABILITY
            each build separately?
```

**And every rung passes one gate before it becomes a finding:**

> ## ⛔ **The reuse gate.** *Does the repository already have this, under another name?*
>
> **This gate rejected seven candidates on the first pass, and one of them was mine.** **I searched for `class TriageState` and `class Snoozed` and reported triage as absent** — `signal_engine/domain/resolution.py` has **`Actioned`, `Assigned`, `Snoozed`, `Dismissed`, `DismissalReason` and `Resolution`**, and has had them for some time. **Searching by the name I expected instead of by the concept is [B-101](../BUGS.md) inside the instrument built to find missing concepts.**
>
> **Every row below §2 was therefore re-tested by concept**, against `domain/` layers rather than against class names. **What survives is what genuinely has no representation.**

---

# 1 · What the domain already has — the denominator

**Nothing is proposed in §2 without this table, because *"missing"* is a claim about a whole repository and the only honest way to make it is to measure the whole repository.**

| | Measured 2026-08-05 |
|---|---|
| **Backend modules** | **16** + `apps` + Platform Foundation |
| **Domain classes across all `domain/` layers** | **316** |
| **Catalogued event types** ([06](06-events.md)) | **34** |
| **Authorization `Resource` members** | **13** — `workspace` `member` `opportunity` `account` `product` `icp` `research` `buying_committee` `commercial_focus` `target_account` `timeline` `integration` `competitor` |
| **Authorization `Action` members** | **4** — `read` `update` `add` `remove` |
| **Explicit state machines** *(`_ALLOWED` + `next_state`)* | **3** — `ResearchStatus` · `SegmentState` · opportunity `Stage` |
| **Modules carrying `actor_id`** | **37 files** — attribution is widespread and already a habit |
| **HTTP endpoints · frontend routes** | **52 · 12** |
| **Approved screens · implemented** | **26 · 1** |

> **This is a large, coherent domain, and the honest headline is that most of what the approved product needs exists.** [411](411-ui-convergence-assessment.md) reached the same conclusion at the capability level and it holds at the domain level: **of sixteen screens, one is architecturally blocked and one has nothing to reuse.** **§2 is short because §1 is long.**

---

# 2 · The findings

**Ordered by how many approved screens depend on each — which is [441 §5 · P-01 Domain precedence](441-people-roadmap.md) used as the ranking function rather than as a rule applied afterwards.**

---

## 🔴 F1 · A change that is proposed, approved, applied as a named unit, and withdrawn within a window

> ### **Five screens name this guarantee, every AI surface inherits it, and the repository has no representation of it at all.**

**The evidence is [410 §What the design project asserts](410-approved-ui-specification.md), quoted rather than paraphrased:**

| Screen | What it asserts |
|---|---|
| **Workflow Automation** | *"Simulated before it runs, **approved before it writes, reversible after it does**."* |
| **Opportunity Intelligence** | *"**Nothing sends without your approval. Reversible for 24 hours.**"* |
| **Companies** | Bulk edit is *"**reversible for 24 hours as a single named batch**"* |
| **Settings** | Every change is *"**attributed, reversible, in the audit log**"* |
| **AI Copilot** *(17 surfaces)* | *"**proposes rather than commits**, and is **attributable and reversible**"* |
| **Account 360 · AI Research · Executive Dashboard** | **Inherit it** — every AI surface obeys the one contract |

### The discovery — the AI contract and the bulk-edit contract are the same contract

**This is the most valuable convergence in the assessment, and it is invisible screen-by-screen.**

**Read as an AI guarantee, *"proposes rather than commits, attributable and reversible"* sounds like AI governance.** **Read as a data guarantee, *"reversible for 24 hours as a single named batch"* sounds like a table feature.** **They are one concept**: *a change that does not take effect until a human says so, that is recorded as one named thing with an author, and that can be taken back inside a stated window.*

> **Built screen-by-screen this becomes five implementations of one idea**, in five modules, with five different windows and five different definitions of *applied*. **That is precisely the outcome the directive names**: *"will multiple teams eventually duplicate it?"*

### ✅ What already exists, and it is more than half

| Rung | Status |
|---|---|
| **Propose** | ✅ **`Recommendation`** in `sales_engagement` — *"what to do, why, and with whom"*, with `reason` citing its evidence. And the ratified principle **`MACHINE_AUTHORED = frozenset({Stage.TRACKING})`** — ***"Intelligence suggests. Humans commit."*** |
| **Attribute** | ✅ **`actor_id` in 37 files**, and `next_state` *"demands an `actor_id` with no default"* (§2, *types make incorrect architecture impossible*) |
| **Reverse** | ✅ **The mechanism exists and has never been generalised.** **Immutability forbids an edit** — *"a change is a new version, a new row, a new artifact naming the one it supersedes"* — and the repository already supersedes **five times**: `observation.superseded` · `signal.superseded` · `entity.superseded` · `business_event.superseded` · `opportunity` stage history. **A withdrawal is a supersession with an actor and a deadline** |
| **As a named unit** | ⛔ **Nothing.** There is no representation of *"these fourteen changes are one thing a person did"* |
| **Within a window** | ⛔ **Nothing.** `24 hour`, `undo` and `revert` return **zero** domain matches |
| **Approve** | ⛔ **Not even a verb.** The `Action` enum is `read · update · add · remove`. **There is no `approve` and no `withdraw`**, so the guarantee five screens assert cannot currently be *authorized*, let alone recorded |

> **`commercial_profile` wrote the trigger down itself**, in `segment.py`: *"editing and **approval workflows** be operations on drafts without polluting an…"* — **a module naming the absence in its own docstring, exactly as `knowledge_graph` and `commercial_profile` did for People.**

### What this asks for

**A decision, not an implementation.** **Three shapes are possible and they are genuinely different**, so this is the product owner's:

| | |
|---|---|
| **(a) A platform capability** | One representation every module composes. **Strongest reuse, and it is 🔴** — a new shared concept in frozen substrate |
| **(b) A domain concept in one owning context** | A bounded context that owns *proposed change* and is consumed through `public/`. **Fits the module model; needs an ADR** |
| **(c) Per-module, deliberately** | Each module reverses its own writes. **Cheapest per slice, and it is the five-implementations outcome** |

> **Lane C's recommendation is (b), and the reason is the reuse gate rather than taste:** *"a port belongs to the module that owns the language it represents"* (§6) — **and *approval* is a language the whole product speaks**, which is what distinguishes it from the five supersessions, each of which is one module's own vocabulary. **⚠️ Nothing is prepared further until this is ruled.**

---

## 🔴 F2 · Scope — the shell applies it before a module renders, and it is not modelled anywhere

**[410](410-approved-ui-specification.md), on the App Shell: *"Global scope — period, region, segment, owner — is applied **before** a module renders, serialises to the URL, and can be saved as a named view."*** **The shell has 22 numbered specifications and *"nobody consumes the App Shell."***

| Screen | Needs |
|---|---|
| **App Shell** *(wave 3, and **all 16 screens inherit it**)* | Global scope · saved views · system status |
| **Companies** | *"Saved views and segments"* |
| **Global Search** | *"Saved and monitored searches"* |
| **Reports** | A report is a saved question, and a scope is half of it |
| **Executive Dashboard** | *"Movement **since a date**"* — a period is scope |

### ⚠️ The word `Segment` is already taken, and this is how a duplicate concept gets born

> **`commercial_profile` owns `Segment`** — a named ICP segment with its own state machine *(`SegmentState`, `_ALLOWED`, `next_state`)*. **It describes *who buys*.**
>
> **Companies' *"segments"* is a saved filter over a list of accounts.** **Two different concepts, one word, and the word is already in the ubiquitous language** (§4: *"never invent a synonym, never repurpose a term from one module inside another"*).

**This is a naming decision that must be taken *before* the second one is built, not after.** **It costs one sentence today and a rename across a bounded context later.**

**What exists:** ⛔ **`saved_view`, `saved search`, `monitored` — zero matches anywhere in the repository.**
**What is decided:** **[O3](../DECISION_REGISTER.md) — *"shell services placement deferred… no further preparation is required at this stage."*** **That deferral stands and this document does not reopen it.** **O3 asked *where shell services live*. It did not ask *whether a saved view is a domain concept*, and the second question is the one five screens depend on.**

---

## 🟠 F3 · A signal ends in a decision, and the decision tells nobody

**Signal Center: *"a triage queue, not a notification list — **every signal ends in a decision**."* Written in `signal_engine/domain/resolution.py`, which implements it.**

| | |
|---|---|
| ✅ **The domain has it** | **`Resolution` · `Actioned` · `Assigned` · `Snoozed` · `Dismissed` · `DismissalReason`.** **This is the candidate the reuse gate rejected**, and rightly |
| ⛔ **The catalog does not** | **`signal_engine` publishes `signal.generated` and `signal.superseded`. There is no `signal.resolved`** |

> **So a human decision is the one thing in this pipeline that produces no business event.** **Nothing downstream can learn that somebody acted**: `timeline` cannot project it, ICP measurement cannot feed on it, `opportunity_engine` cannot see it, and no report can count it. **The pipeline records nine stages of what a provider said and zero of what a person did about it.**

**Cost of the gap, and it is the reason this ranks above its screen count:** **[TASK-406](../BACKLOG.md) measures an ICP criterion against outcomes** — and *dismissed with a reason* is an outcome. **A signal triaged today is unrecoverable evidence tomorrow**, because the row records the state and nothing records the transition.

**One event, on a shape the catalog already uses 34 times.** **Registering an event type is explicitly *"a use of the platform, not a change to it"* (§20a).**

---

## 🟠 F4 · The workspace has a lifecycle in the UI and one state in the model

**App Shell: *"trial and seat state"*. Settings: *"seats and billing"*. [PRODUCT_EXPERIENCE MC-8](../PRODUCT_EXPERIENCE.md): the guided first run.**

| | |
|---|---|
| **Exists** | **`Workspace`, `Membership`, `Invitation`, `WorkspaceRole`, `InvitationState`** — 19 domain classes, the largest router in the repository, and **`GET /workspaces/{id}/history`** *(the only history endpoint that exists)* |
| **Absent** | **`trial`, `seat`, `suspend`, `archive` — zero domain matches.** A workspace is created and then simply *is* |
| **Already on the roadmap** | ✅ **[438 §Epic I](438-platform-initiatives.md): *"Workspace lifecycle states — suspend · archive · restore"*, gated behind [TASK-426](../BACKLOG.md)** |

> ### ⚠️ This is a P-01 hit, and it is the second one found this week.
>
> **The App Shell is wave 3 and *every one of the sixteen screens inherits it*.** **The lifecycle it needs is scheduled inside a future data-governance epic whose trigger is a retention obligation.** **A foundational concept is behind the thing that inherits into everything** — which is [441 §5](441-people-roadmap.md) verbatim, arriving from a completely different direction ten hours later.
>
> **The finding is the ordering, not the capability.** **Nothing here needs building today; Epic I's row needs to know that the shell is its first consumer, not billing.**

---

## 🟠 F5 · An invitation is a lifecycle with no events

**Just shipped by [TASK-904](../BACKLOG.md), and worth recording while the code is warm.**

**`Invitation` and `InvitationState` are a real lifecycle** — pending, accepted, expired. **`invitation.delivered` exists and is a *log line*, not a domain event** *(`infrastructure/delivery.py:43` — checked before reporting it, because a log line and an event look identical in a grep)*. **The catalog has `workspace.created` and `workspace.member_added` and nothing between them.**

**Consequence, and it is small but it is the same shape as F3:** **Settings shows member history and the timeline cannot project how somebody arrived.** **Two events, on a lifecycle that already exists.**

---

## 🟡 F6 · Calls, and the intelligence the product claims from them

**Opportunity Intelligence: *"conversation intelligence (talk ratio, commitments)"*. Global Search: *"people, **calls** and deals as searchable types"* — one of four object types.**

⛔ **`transcript`, `call` — no domain representation.** ✅ **[PRODUCT_EXPERIENCE MC-10](../PRODUCT_EXPERIENCE.md) already classifies activity capture as *"future platform capability"*, and the Connection Center already refuses to advertise it.**

> **Classified as *evidence-gated*, exactly as People was before [D-074](../DECISION_REGISTER.md), and for the same measured reason: no source supplies it.** **It is recorded here so that when a source does appear, the sequencing question is asked before two screens shape their own version of a call.**

---

## 🟡 F7 · Reports — the one screen with nothing to reuse, and the concept underneath is not new

**[411](411-ui-convergence-assessment.md) marks Reports 🔴, *"nothing to reuse"*. At the capability level that is right. At the domain level it is not quite.**

**A report is *a saved question, answered over the reads that already exist, and materialised so three renderings show one answer*.** **The repository has that shape already** — `ai_narration` is *"a historical fact, not current truth"*, immutable, attributable to prompt and model and evidence. **A materialised report is the same category of artifact.**

> **So the honest finding is: Reports needs `ReportDefinition` and `Block`, and it does **not** need a new aggregation layer** — every figure comes from surfaces delivered in waves 1–4. **Wave 7 is correct and this changes nothing about it.** **What it changes is the expectation**: when Reports arrives it must not build a second aggregation, and §2's *truth has exactly one authoritative representation* is what stops it.

---

## 🟢 F8 · Authorization — the vocabulary is short by two verbs and five nouns

**Not a screen's requirement. It is what every screen above needs before it can be permitted.**

| | |
|---|---|
| **Missing verbs** | ⛔ **`approve` · `withdraw`.** **F1's guarantee cannot be expressed** — five screens assert an approval and the policy language has no word for one |
| **Missing nouns** | **`signal`** *(ruled at [C-224](../LANE_COORDINATION.md), unbuilt)* · **`report`** · **`saved_view`** · **`workflow`** · **`notification`** |
| **Missing dimension** | **Companies asserts *"export with field-level permissions"*.** **Casbin tuples are `(subject, workspace, object, action)` — there is no field term**, so the guarantee is currently unexpressible rather than merely unbuilt |

> **The first two are trivial and the third is architectural.** **Adding a `Resource` is a declarative registration** ([C-224](../LANE_COORDINATION.md), [D-073](../DECISION_REGISTER.md)); **adding a *field* dimension to the policy tuple is 🔴 and needs an ADR.** **Recorded now, before a screen ships an export that quietly ignores it.**

---

## ⏸ F9 · Deferred by you, and depended on by four screens — recorded, not re-raised

| | |
|---|---|
| **Notifications** | **App Shell · Signal Center · Global Search *(monitored searches)* · Workflow.** **[ADR-0040](adr/0040-notifications.md) is deferred by [D-027](../DECISION_REGISTER.md)** — *"allow the Notification package to complete first."* **The deferral stands. This document adds one fact to it: four screens, and Global Search's monitored search is a fifth consumer the ADR was not written against** |
| **Shell services placement** | **[O3](../DECISION_REGISTER.md), deferred.** See F2 — the *placement* stays deferred; the *concept* is the open question |
| **People** | ✅ **Answered today by [D-074](../DECISION_REGISTER.md).** [441](441-people-roadmap.md) |
| **Audit query surface** | ✅ **Already [438 §Epic I](438-platform-initiatives.md).** **What this assessment adds: Settings asserts it as a screen requirement — *"attributed, reversible, in the audit log"* — so it is a wave-6 product surface, not only a future operations tool.** **Attribution exists in 37 files; the queryable surface over it does not** |

---

# 3 · UI → domain traceability

**Every approved screen, and the *deepest* concept it needs rather than the endpoint it calls.** **✅ = the domain has it.**

| Screen | Deepest concept it requires | |
|---|---|---|
| **Design System v2** | — *(requires no backend)* | ✅ |
| **Account 360** | Entity · claim · observation · business event · score · timeline | ✅ **all** · ⛔ **People** (F-People) · ⛔ **F1** for its AI surfaces |
| **AI Research** | `ResearchRequest` + its state machine · immutable artifact | ✅ · ⛔ **F1** (*preserved edits through regeneration* is a supersession) |
| **Signal Center** | `Signal` · `Resolution` and its four outcomes | ✅ · ⛔ **F3** — the event |
| **ICP Builder** | `Icp` · `Segment` · criterion · closed-won outcome | ✅ · ⛔ **F3** — outcomes it cannot yet see |
| **Companies** | `Account` · list · **saved view** · **named batch** | ✅ · ⛔ **F2** · ⛔ **F1** |
| **Opportunity Intelligence** | `Opportunity` · `Stage` · contribution · **approval** · **call** | ✅ · ⛔ **F1** · ⛔ **F6** |
| **Executive Dashboard** | Quarter aggregate · plan · **movement** | ⛔ aggregates · ⛔ **F-People** (movements are affiliation intervals) |
| **AI Copilot** | Six verbs · grounding · scope · **propose** · **reverse** | ✅ AI · ⛔ **F1** · ⛔ **F2** |
| **CRM Integrations** | `Connection` · `SourceAdapter` · sync health | ✅ **built** — [C-326](../LANE_COORDINATION.md) ruled |
| **Workflow Automation** | Rule as data · **simulation** · **approval** | ✅ [ADR-0402](adr/0402-a-rule-is-data.md) · ⛔ **F1** |
| **Global Search** | Four object types · **saved and monitored search** | ✅ 1 of 4 · ⛔ **F-People** · ⛔ **F6** · ⛔ **F2** |
| **People Intelligence** | `Person` · `Affiliation` | ⛔ **[441](441-people-roadmap.md)** — planned |
| **Settings** | `Workspace` · `Membership` · `Invitation` · **audit** · **seats** | ✅ · ⛔ **F4** · ⛔ **F9 audit** |
| **App Shell** | **Scope** · saved views · notifications · **trial and seat state** | ⛔ **F2** · ⛔ **F9** · ⛔ **F4** |
| **Reports** | `ReportDefinition` · `Block` · materialised rendering | ⛔ **F7** — and no new aggregation |

> ## The shape of this table is the finding
>
> **Nine of sixteen screens are blocked on the same four concepts.** **F1 alone appears in six rows.** **Not one screen needs a new intelligence capability, a new pipeline stage, or a second copy of anything already built** — **which is [411](411-ui-convergence-assessment.md)'s conclusion holding one level deeper than it was tested.**

---

# 4 · What we would regret in six months

**The directive's question, answered with the four rows that have evidence behind them.**

| | If we build exactly what exists today | Regret |
|---|---|---|
| **F1** | **Five modules each implement approval, batching and a reversal window** | 🔴 **The highest-cost regret in this document.** Five definitions of *applied*, five windows, and no way to answer *"what did somebody change last Tuesday?"* — **and it is unpickable afterwards, because each will be load-bearing for its own screen** |
| **F2** | **`Segment` means two things** | 🔴 **A rename across a bounded context**, and §4 forbids the collision in advance |
| **F3** | **Triage decisions accumulate as state with no transitions** | 🟠 **Unrecoverable.** ICP measurement, reporting and the timeline all want history that was never written |
| **F4** | **Workspace lifecycle arrives after the shell every screen inherits** | 🟠 **The Account 360 pattern repeated** — a screen ships around an absence and is revisited |

> **All four are ordering problems, not capability problems.** **None asks for anything to be built today.** **Each asks that a decision be taken before the first dependent slice starts** — which is the whole content of the directive, and of [441 §5 · P-01](441-people-roadmap.md).

---

# 5 · Sequencing — where each lands, and nothing moves without a ruling

| | Finding | Recommended position | Depends on |
|---|---|---|---|
| **1** | **F1 · approved, applied, reversible** | **Before wave 2** — AI Copilot is the first screen that asserts it | **A ruling on shape (a)/(b)/(c).** Nothing else |
| **2** | **F2 · scope and saved views** | **With the shell, wave 3** — but **the naming decision is due now** | O3 remains deferred for placement |
| **3** | **F3 · `signal.resolved`** | **Now** — one event, and every day without it loses evidence | Nothing. §20a permits registering an event type |
| **4** | **F4 · workspace lifecycle** | **Epic I keeps it; the shell becomes its named first consumer** | [TASK-426](../BACKLOG.md) |
| **5** | **F5 · invitation events** | With the next `workspace_tenancy` slice | Nothing |
| **6** | **F8 · `approve` · `withdraw` · five resources** | **With F1**, because F1 cannot be authorized without them | F1's ruling |
| **7** | **F7 · report definitions** | **Wave 7, unchanged** | Nothing |
| **8** | **F6 · calls** | **Evidence-gated** — when a source exists | A provider or an activity-capture decision |

---

# 6 · Suggested backlog additions

**Three, and the restraint is deliberate:** *"success is not measured by the number of backlog items created."* **F4, F5, F7 and F8 are amendments to rows that already exist; F6 is evidence-gated; F2's placement is deferred by you.**

| Row | Status | Rationale |
|---|---|---|
| **[TASK-431](../BACKLOG.md)** — *a change is proposed, approved, applied as one named thing, and can be taken back* | **`WAITING`** — on the shape ruling | **Six screens.** The only 🔴 with no decision behind it |
| **[TASK-432](../BACKLOG.md)** — *a triaged signal says so, and the pipeline hears it* | **`SEQUENCED`** — trigger: the next `signal_engine` slice | **One event. Evidence is being lost while it does not exist** |
| **[TASK-433](../BACKLOG.md)** — *scope, a saved view, and a word that is already taken* | **`WAITING`** — on the naming decision only | **Five screens.** The concept question O3 did not ask |

---

## 🔭 The radar — capabilities under assessment, and where each one is

**[D-075](../DECISION_REGISTER.md) made this method permanent.** **A capability enters the radar when the approved product experience implies it and the repository has not decided where it lives; it leaves when it is ruled, built, or measured away.**

| Capability | Assessment | State |
|---|---|---|
| **Account matching / ICP matching** | **[443](443-account-matching-capability.md)** — **16 consumers, four on no list, one being implemented today.** Decomposed into vocabulary agreement · evaluation · discovery · measurement | ✅ **Assessed.** Ownership determined at 🟠 · **[TASK-434](../BACKLOG.md)** · **timing is the product owner's** |
| **F1 · proposed → approved → applied → withdrawn** | §F1 above | **[TASK-431](../BACKLOG.md)** — awaiting a shape ruling |
| **F2 · scope and saved views** | §F2 above | **[TASK-433](../BACKLOG.md)** — awaiting a naming ruling |
| **F3 · the triage event** | §F3 above | **[TASK-432](../BACKLOG.md)** — `SEQUENCED`, no ruling needed |
| **People — domain · intelligence · enrichment · experience** | **[441](441-people-roadmap.md)** | ✅ **Ruled [D-074](../DECISION_REGISTER.md)** — **[TASK-427–430](../BACKLOG.md)** |

> ### The separation this radar enforces, on every row
>
> **[D-075](../DECISION_REGISTER.md) generalised [D-074](../DECISION_REGISTER.md)'s four milestones beyond People:** **Domain · Intelligence · Provider Enrichment · Customer Experience** are **separate milestones with separate triggers**, and *"we should avoid coupling foundational domain work with customer-facing screens simply because they happen to be related."*
>
> **Applied to 443 immediately, and it is what keeps that row honest**: **[TASK-434](../BACKLOG.md) is `Domain`.** **It renders nothing, it is not ICP Builder, and it is not TASK-406's backtest** — which is exactly why it may be sequenced ahead of both.

# 7 · How this document stays true

**It is a register, not a report.** **It is re-measured whenever a screen is prepared, a wave is amended, or a domain concept lands** — and every row states what was measured and when, so a stale row is visible rather than merely wrong.

**A finding leaves this document in exactly three ways:** **it is built** *(and the row records where)* · **it is ruled and scheduled** *(and the row points at the task)* · **it is measured away** *(the reuse gate found it after all, as triage was)*.

---

# 8 · What this document did not do

**Nothing implemented · nothing assigned · no module created · no ADR ratified · no ownership changed · no queue file touched · no existing task's position altered.**

**No architecture was decided.** **F1 is the only 🔴 without a decision behind it, and it is stated as three alternatives with a recommendation and a reason — never as a design.**

**Nothing here reopens a settled decision.** **[ADR-0040](adr/0040-notifications.md), [O3](../DECISION_REGISTER.md), [C-002](../LANE_COORDINATION.md), [C-322](../DECISION_QUEUE.md) and [MC-10](../PRODUCT_EXPERIENCE.md) are all recorded as deferred and left that way** — the one thing added is *how many screens are behind each*, which is information about your deferral rather than a challenge to it.

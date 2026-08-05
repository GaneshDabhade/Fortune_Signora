# Domain Discovery Register

> **Every approved screen, mapped to the domain capabilities and platform services it requires — and the architectural radar that runs ahead of implementation.**
>
> **Established 2026-08-05 by product owner directive ([D-076](DECISION_REGISTER.md)).** **Standing responsibility of Lane C — Product Office.** **Continuously maintained; never a snapshot.**

**Measured against `origin/integration` @ `83f3281`.** **No screen is designed here, no lane is named, and nothing is implemented.**

---

## What this register is for, and the one thing it must never become

> **The approved UI is the authoritative expression of the intended product experience. Product Office derives the domain model, platform capabilities, workflows and architecture that enable it while preserving architectural integrity.**
>
> **The architecture enables the product. The product is not constrained by accidental gaps in today's backend.** **And the backend does not mirror pixels** — *"your responsibility is to derive the correct **reusable** domain."*

**Both halves of that are load-bearing, and each guards against a different failure.** **Without the first, the product is quietly cut down to what the backend already does.** **Without the second, the domain becomes a transcription of a layout** — sixteen screens, sixteen shapes, and the reuse policy is gone.

### It has exactly one responsibility

| | |
|---|---|
| **This register** | ***Which domain capabilities and platform services does each approved screen require, and where is each of those?*** |
| **[411](architecture/411-ui-convergence-assessment.md)** | Screen → module → endpoint. **Referenced, never restated** |
| **[412](architecture/412-backend-capability-matrix.md)** | Module → capability → wave. **The sequence lives there** |
| **[442](architecture/442-product-led-domain-discovery.md)** | **The dated findings** that populate this register, with their evidence |
| **[443](architecture/443-account-matching-capability.md)** *et seq.* | **A single capability, assessed in full** |
| **[BACKLOG](BACKLOG.md)** | Work. **A register row is not a task and never implies one** |

**A figure that belongs to another document is linked, not copied** (§2, *truth has exactly one authoritative representation*). **This register is an index over assessments; it is not a second copy of them.**

---

# Part A · Screen → domain

**Sixteen approved specifications ([410](architecture/410-approved-ui-specification.md)).** **✅ the domain has it · 🟨 partial · ⛔ absent.**

> **The platform baseline is universal and stated once rather than sixteen times:** **JWT verification · Casbin authorization · RLS workspace scoping · the error envelope · cursor pagination · structured logging with `correlation_id`.** **Every screen needs all six.** **The `Platform` column names only what is *beyond* the baseline** — so a filled cell is information and an empty one is too.

| # | Screen | Domain capabilities required | Platform beyond baseline | |
|---|---|---|---|---|
| 1 | **Design System v2** | **None** | **None** | ✅ **Requires no backend at all** |
| 2 | **App Shell** | **Scope** *(period · region · segment · owner)* · **saved view** · **workspace lifecycle** *(trial · seat)* · notification · system status | **Event bus** *(status)* | ⛔ **R-02 · R-04 · R-05.** **All 16 screens inherit this row** |
| 3 | **Account 360** | Entity · claim · observation · business event · buying score · timeline · research · narration | **Event bus** · **AI Platform** *(grounding)* | ✅ **shipped** · ⛔ **R-01 People** · ⛔ **R-03** for its AI sections |
| 4 | **Companies** | Account · **saved view** · **named batch, reversible** · import · export **with field-level permission** | — | 🟨 accounts ✅ · ⛔ **R-02 · R-03 · R-09** |
| 5 | **People Intelligence** | **`Person` · `Affiliation` interval** · org chart · relationship | — | ⛔ **R-01** — planned, [441](architecture/441-people-roadmap.md) |
| 6 | **Opportunity Intelligence** | Opportunity · `Stage` · contribution · **approval** · competitor · **call** | — | ✅ opportunity · ⛔ **R-03 · R-07** |
| 7 | **Signal Center** | Signal · catalog · **`Resolution`** · **the triage event** · rule precision | **Event bus** | ✅ **domain complete** · ⛔ **R-06** — the event |
| 8 | **ICP Builder** | Icp · criterion · **account matching** · closed-won outcome · lift | — | ✅ declaration · ⛔ **R-00** · 🟨 outcomes |
| 9 | **Workflow Automation** | Rule as condition tree · **simulation** · **approval** · **account matching** *(a condition)* | **Outbox · relay · ARQ** ✅ **built** | ✅ [ADR-0402](architecture/adr/0402-a-rule-is-data.md) · ⛔ **R-03 · R-00** |
| 10 | **CRM Integrations** | Connection · source adapter · field mapping · sync health · **account matching on arrival** | **Event bus** | ✅ **[C-326](LANE_COORDINATION.md) ruled** · ⛔ **R-00** |
| 11 | **AI Copilot** | Six verbs · evidence set · grounding · **scope** · **propose, attribute, reverse** | **AI Platform** ✅ | ✅ **AI complete** · ⛔ **R-03 · R-02** |
| 12 | **AI Research** | `ResearchRequest` + its **state machine** · plan · synthesis · **preserved edits** · recorded refusal | **AI Platform** ✅ | ✅ **built** · ⛔ **R-03** *(a preserved edit is a supersession)* |
| 13 | **Global Search** | Four object types · **saved and monitored search** | — | ✅ 1 of 4 · ⛔ **R-01 · R-07 · R-02** |
| 14 | **Executive Dashboard** | Quarter aggregate · plan · **movement** · **in-ICP cohort** | — | ⛔ aggregates · ⛔ **R-01** *(movements are affiliation intervals)* · ⛔ **R-00** |
| 15 | **Reports** | Report definition · block · materialised rendering · **permission-respecting share** | — | ⛔ **R-08.** **And no second aggregation** |
| 16 | **Settings** | Workspace · membership · invitation · role · **audit trail** · **seats** | — | ✅ **13 endpoints** · ⛔ **R-05 · R-10** |

---

# Part B · The product as one system

**The instruction is *"do not analyse screens independently."*** **Read down the `required` column instead of across it, and the shape changes: nine of sixteen screens are blocked on four concepts, and no screen needs a new intelligence capability.**

## The convergences — ranked by consumers, which is [P-01](architecture/441-people-roadmap.md) used as a sort

| | Concept | Consumers | State |
|---|---|---|---|
| **R-00** | **Account matching** | **16** — and **4 were on no list** | ✅ **Ruled and sequenced, [D-077](DECISION_REGISTER.md).** **[TASK-434](BACKLOG.md) is `READY` at the head, ahead of [TASK-406](BACKLOG.md)'s backtest** — *"establish the reusable capability once rather than allowing multiple implementations to emerge independently."* **[443](architecture/443-account-matching-capability.md)** |
| **R-02** | **Scope · saved view** | **5 named, and the shell inherits into all 16** | **[TASK-433](BACKLOG.md)** — awaiting a naming ruling |
| **R-03** | **Proposed → approved → applied → withdrawn** | **6** | **[TASK-431](BACKLOG.md)** — awaiting a shape ruling |
| **R-01** | **People · Affiliation** | **4 + Executive Dashboard's movements** | ✅ **Ruled [D-074](DECISION_REGISTER.md)** · **[TASK-427–430](BACKLOG.md)** |
| **R-04** | **Notification** | **4** | ⏸ **Deferred [D-027](DECISION_REGISTER.md).** Recorded, not re-raised |
| **R-05** | **Workspace lifecycle** | **Settings + the shell all 16 inherit** | 🟨 **[438 Epic I](architecture/438-platform-initiatives.md)** — **the shell is its first consumer, not billing** |

> ### The finding that only appears when the screens are read together
>
> **[442 §F1](architecture/442-product-led-domain-discovery.md): the AI contract and the bulk-edit contract are the same contract.** *"Proposes rather than commits, attributable and reversible"* reads as AI governance on Copilot and as a table feature on Companies. **Screen-by-screen it is two requirements. As one system it is one concept, and building it twice is the whole failure this method exists to prevent.**

## The candidate foundations — and half of them are already built

**The directive's own list, each tested against source rather than assumed.** **This is the reuse audit the method requires, applied to the candidates themselves.**

| Candidate | Verdict |
|---|---|
| **Identity Resolution** | ✅ **Built and mature.** `ResolutionRule` · `MatchStrength` · `NameAgreement` · `IdentityState` · `ResolutionOutcome`. **Never duplicate it** — `commercial_profile` already declined to, in a docstring |
| **Relationship Graph** | ✅ **Built.** `Relationship` · `relationship.established` · `relationship.ended` |
| **Timeline** | ✅ **Built.** `ProjectionRule` · `TimelineEntry` · `EntryKind`, with `PROJECTIONS` as the authority. ⚠️ **[TASK-901](BACKLOG.md)** — 2 of 9 consumers wired |
| **Explainability** | ✅ **Built, and it is a differentiator.** `EvidenceSet` · `GroundedOutput` · `GroundingReport` · `Violation` · `Derivation` · `Corroboration` · `Dissent` · `Recency` · `EpistemicOrigin`. **Nothing to add** |
| **Research Session** | ✅ **Built, with a state machine.** `ResearchRequest` · `ResearchStatus` · `_ALLOWED` · `ResearchPlan` · `SynthesisedResearch` |
| **Affiliation History** | 🟨 **Designed and unbuilt** — [ADR-0400](architecture/adr/0400-person-as-an-entity.md) ratified, [TASK-427](BACKLOG.md) sequenced |
| **ICP / Account Matching** | ⛔ **R-00.** [443](architecture/443-account-matching-capability.md) |
| **Action Batch** | ⛔ **R-03.** **`24 hour`, `undo`, `revert` return zero domain matches** |
| **Workspace Lifecycle** | ⛔ **R-05.** `trial`, `seat`, `suspend`, `archive` — zero domain matches |
| **Organization Hierarchy** | ⛔ **Nothing, on either side** — no `Team`, no `parent_id`, and no org chart without [TASK-427](BACKLOG.md) |
| **Recommendation Lifecycle** | ⚠️ **Declared and unbuilt, and the repository says so.** `Recommendation` and `NextAction` exist; **`recommendation.created` and `recommendation.status_changed` are catalogued and published by nothing** — `timeline/domain/projection.py`: *"**`recommendation.created` is deliberately absent.** M11 is deferred"* |
| **Audit** | ⚠️ **Attribution ✅ everywhere — `actor_id` in 37 files. A queryable surface ⛔** — **one endpoint, `GET /workspaces/{id}/history`.** [438 Epic I](architecture/438-platform-initiatives.md) |
| **AI Conversation** | ⛔ **Forbidden, and by a ratified principle rather than by absence.** **Statelessness**: *"**Statelessness says what the platform may remember: nothing**"*, and `ai_platform/domain/provider.py` — *"no conversation handle, no server-side session, no response cache."* **[437 §2.1](architecture/437-ai-platform-future-epic.md) ruled it.** **A conversation entity would silently invalidate grounding**, because the evidence set the validator checks would stop being the set the model saw |

> **Six of fourteen are already built, one is forbidden by a ratified principle, and one is declared-and-unbuilt with the reason written into the code.** **That ratio is the point of the reuse gate** — *"the preferred solution is almost always evolution of an existing concept rather than introducing a competing one."*

---

# Part C · The architectural radar

**Eight categories, on the product owner's instruction.** **A row enters by the test below and leaves when it is ruled, built, or measured away.**

## What gets on the radar — the four questions ([D-077](DECISION_REGISTER.md))

| Ask | And if the answer is |
|---|---|
| **Is this a screen-specific feature?** | **Yes → it is not a radar row.** It is the screen's, and the owning lane's package |
| **Is this a reusable domain capability?** | **Yes → radar** |
| **Is this actually a platform service?** | **Yes → radar**, and the bar is higher: 🔴, and the substrate is frozen |
| **Should this exist before multiple consumers require it?** | **Yes → radar, and it is a sequencing row rather than a capability row** |

> **The fourth question is the one that changes the schedule**, and it is [P-01](architecture/441-people-roadmap.md) asked prospectively rather than detected afterwards. **`R-00` and `R-01` both entered on it.**

## Before proposing anything — the reuse ordering, and it is an order

> **① Reuse an existing bounded context → ② extend an existing domain concept → ③ evolve an existing platform capability → ④ only then propose something new.**
>
> ***"The preferred outcome is always architectural evolution rather than architectural duplication."***

**Applied to the directive's own fourteen candidates, this stopped at ① or ② for eight of them** — six already built, one forbidden, one declared-and-unbuilt. **A candidate that stops at ① is the register working, not a wasted pass.**

### ⛔ Missing foundational concepts

**R-00 account matching** · **R-02 scope and saved view** · **R-03 action batch and approval** · **R-05 workspace lifecycle** · **R-08 report definition** · **R-10 field-level permission**

### 🟨 Concepts requiring evolution, not replacement

| | |
|---|---|
| **`CommitteeRole`** | **Gains a stable id at [TASK-428](BACKLOG.md)** — *"on the trigger that module already wrote down"* |
| **`EntityKind`** | **One member, `PERSON`.** The docstring already reserves it |
| **`Resource` · `Action`** | **Five nouns and two verbs.** ⚠️ **`approve` and `withdraw` do not exist, so R-03's guarantee cannot be *authorized***, let alone recorded |
| **Identity resolution** | **Resolves entities, not attribute values.** **[443 M1](architecture/443-account-matching-capability.md)** — and its extension is a **reviewed catalog**, never a model |
| **`FitDimension`** | **One value, and its own §23 already lists ICP match as the next, with its trigger** |

### ⏱️ Arriving too late in the roadmap

| | |
|---|---|
| **R-00** | ✅ **Caught and corrected, [D-077](DECISION_REGISTER.md).** **[TASK-406](BACKLOG.md) was `IN PROGRESS` and needed the predicate; measured at ruling time, no matching code had reached `integration`.** **The window closed with the capability on the right side of it** |
| **R-01** | ✅ **Corrected by [D-074](DECISION_REGISTER.md)** — wave 6 → wave 1.5, ahead of four dependents |
| **R-05** | **Scheduled inside a future data-governance epic; the App Shell inherits into all 16 screens.** **The ordering is the finding, not the capability** |

### ♻️ Reusable capabilities — do not rebuild

**Identity resolution · explainability and grounding · the evidence set · the timeline projection contract · the outbox, relay, dispatch, idempotency and dead-lettering chain · the provider adapter port · the signal catalog · the claim/observation model · `live_capabilities`.** **Reuse, unchanged** ([412 §6](architecture/412-backend-capability-matrix.md)).

### 🔗 Cross-module dependencies a discovery would create

| | |
|---|---|
| ✅ **Zero, for R-00 as recommended** | **`evaluate(criteria, attributes)` is pure.** `lint-imports` unchanged — the strongest available evidence a boundary is not being bent |
| ⚠️ **One read port missing** | **`commercial_profile/public/` publishes 13 views and not one is the ICP.** **[ADR-0403](architecture/adr/0403-signal-engine-reads-a-declaration.md) is the ratified precedent** |
| ⚠️ **R-01 P4** | `commercial_profile` gains one field |

### ⚠️ Future regression risks

| | |
|---|---|
| **A match that returns a number** | **Would be a second propensity model competing with `buying_score_engine`.** `MatchStrength` and `Relevance` both forbid it: *"a number invites weighting, weighting invites thresholds"* |
| **A match that returns `false` where it means *I could not tell*** | **Free-text criteria versus canonical claims.** *"SaaS" versus "Computer Software"* — **a smaller ICP, a cleaner backtest, and a wrong answer that is invisible from the result.** **`unmeasured` in the type** |
| **`Segment` meaning two things** | **The word is already `commercial_profile`'s.** §4 forbids the collision in advance |
| **R-03 built five times** | **Five definitions of *applied*, five windows, and unpickable afterwards** — each copy load-bearing for its own screen |
| **AI memory or caching** | ⛔ **Would reverse Statelessness and silently invalidate grounding** |

### 📐 Sequencing improvements

**R-00 ahead of [TASK-406](BACKLOG.md)'s backtest** · **R-01 at wave 1.5** ✅ ruled · **R-05's first consumer named as the shell** · **[TASK-426](BACKLOG.md) before any named-person work** · **[TASK-901](BACKLOG.md) before any new timeline projection.**

### 🚀 Platform opportunities

**R-03 as one composable capability rather than six** · **the audit query surface, which Settings needs as a product surface and operations needs anyway** · **a reviewed vocabulary-agreement catalog, sitting exactly where the Signal Catalog already sits on the least-powerful-author ladder.**

---

# Part D · How this register stays true

**A row carries what was measured and when, so a stale row is visible rather than merely wrong.**

| | |
|---|---|
| **Re-measured** | Whenever a screen is prepared, a wave amended, a domain concept landed, or a ruling made |
| **A finding leaves** | **Built** *(the row records where)* · **ruled and scheduled** *(the row points at the task)* · **measured away** *(the reuse gate found it after all)* |
| **⛔ Never** | **A row is not a task.** **Rows are not a productivity measure** — *"success is not measured by the number of backlog items created"* |

> ### The measure this register is kept against
>
> **Whether implementation reaches a feature and finds the foundations already there.** **An architectural surprise during implementation is a miss by this document, and it is the only miss that counts.**
>
> **Two are on the record already, and both were caught before they cost a slice:** **People, scheduled behind four dependents** ([D-074](DECISION_REGISTER.md)) · **account matching, needed by a task in progress** ([443](architecture/443-account-matching-capability.md)). **A third was caught inside this office's own instrument** — triage reported as missing because the search was by class name rather than by concept.

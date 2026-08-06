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
| 1 | **Design System v2** ✅ [460](architecture/460-people-and-design-system-traceability-audit.md) | **None** | **None** | ✅ **Requires no backend at all** |
| 2 | **App Shell** | **Scope** · saved view · workspace lifecycle · notification · **7 more cross-cutting concerns** | **Event bus** *(status)* | ✅ **Audited in full — [452](architecture/452-app-shell-traceability-audit.md).** **3 of 10 concerns complete** — identity, workspace context, search — **5 absent, 2 deferred with triggers, 1 ⬜.** ⚡ **[R-02](#) measured as the highest-leverage capability in the product** · **background activity reassigned to [R-03](#)** |
| 3 | **Account 360** | Entity · claim · observation · business event · buying score · timeline · research · narration | **Event bus** · **AI Platform** *(grounding)* | ✅ **Shipped, and audited — [449](architecture/449-account-360-traceability-audit.md).** **[414](architecture/414-wave-1-account-360.md)'s prediction matched delivery to the row.** ⚡ **R-15 found here, at 7 instances** · ✅ **authorization complete** · ✅ **3 completion events** · ⛔ **R-01** *(contacts M-E, committee M-D)* · ⬜ **7 sourceless sections** |
| 4 | **Companies** | Account · **saved view** · **named batch, reversible** · import · export **with field-level permission** | **ARQ + outbox** *(bulk is background work)* | ✅ **Audited in full — [446](architecture/446-companies-traceability-audit.md).** 9 elements: 5 ✅ · 3 🔴 · **1 ⬜ not yet extractable.** ⛔ **R-02 · R-03 · R-13** · ⚖️ **import challenged — §3** |
| 5 | **People Intelligence** ✅ [460](architecture/460-people-and-design-system-traceability-audit.md) | **`Person` · `Affiliation` interval** · org chart · relationship | — | ⛔ **R-01** — planned, [441](architecture/441-people-roadmap.md) |
| 6 | **Opportunity Intelligence** | Opportunity · `Stage` · contribution · **approval** · competitor · **call** | — | ✅ opportunity · ⛔ **R-03 · R-07** |
| 7 | **Signal Center** | Signal · catalog · **`Resolution`** · **the triage event** · rule precision · **snooze** | **Event bus** | ✅ **Audited in full — [447](architecture/447-signal-center-traceability-audit.md).** 10 elements: 6 ✅ · 2 🟡 · 2 🔴, **no new row and no new foundation.** ⚡ **It *supplies* the mechanism R-03 needed** · ⛔ **R-06** the event · 🟡 **R-07 · R-13** |
| 8 | **ICP Builder** | Icp · criterion · **account matching** · closed-won outcome · lift · **7 criterion groups** | — | ✅ **Audited in full — [448](architecture/448-icp-builder-traceability-audit.md).** 12 elements: 4 ✅ · 1 🔨 · 1 🟠 · 3 🔴 · **3 ⬜.** ⚡ **R-00 shipped and validated here** · ⚡ **R-01 split across M-D/M-E** · ⛔ **R-14** · ⚠️ **3 of 7 criterion groups modelled** |
| 9 | **Workflow Automation** | Rule as condition tree · **simulation** · **approval** · **account matching** *(a condition)* | **Outbox · relay · ARQ** ✅ **built** | ✅ [ADR-0402](architecture/adr/0402-a-rule-is-data.md) · ⛔ **R-03 · R-00** |
| 10 | **CRM Integrations** ✅ [456](architecture/456-crm-integrations-traceability-audit.md) | Connection · source adapter · field mapping · sync health · **account matching on arrival** | **Event bus** | ✅ **[C-326](LANE_COORDINATION.md) ruled** · ⛔ **R-00** |
| 11 | **AI Copilot** | Six verbs · evidence set · grounding · **scope** · **propose, attribute, reverse** | **AI Platform** ✅ | ✅ **Audited in full — [445](architecture/445-ai-copilot-traceability-audit.md).** 12 elements: 4 ✅ · 4 🟡 · 2 🟠 · 2 🔴, **and no new backlog row.** ⛔ **R-12** *(the verb taxonomy and the surface model — [C-419](LANE_COORDINATION.md))* · ⛔ **R-03 · R-02** · 🟡 **no `ai_reasoning` `Resource`** |
| 12 | **AI Research** ✅ [457](architecture/457-ai-research-traceability-audit.md) | `ResearchRequest` + its **state machine** · plan · synthesis · **preserved edits** · recorded refusal | **AI Platform** ✅ | ✅ **built** · ⛔ **R-03** *(a preserved edit is a supersession)* |
| 13 | **Global Search** | Four object types · **saved search** · monitored search · NL question | — | ✅ **Audited in full — [450](architecture/450-global-search-traceability-audit.md).** 11 elements: 2 ✅ · 2 🔨 · 3 🟡 · 4 🔴. ⚡ **R-02 *defined* by four screens and *narrowed* — monitored searches leave it** · **deals re-classified out of `EntityKind`** · ⚠️ **no search index exists: `meilisearch` `tsvector` `trigram` all 0** |
| 14 | **Executive Dashboard** | **Stage history ✅ · owner ✅ · in-ICP cohort ✅** · deal value · plan · fiscal period · team · **movement** | — | ✅ **5 of 6 sections buildable — [444](architecture/444-executive-dashboard-domain-assessment.md), [TASK-438](BACKLOG.md).** ⛔ **R-11** *(forecast — [C-418](LANE_COORDINATION.md))* · ⛔ **R-01** *(movements are affiliation intervals)* · ✅ **R-00 promoted** |
| 15 | **Reports** ✅ [459](architecture/459-reports-traceability-audit.md) | Report definition · block · materialised rendering · **permission-respecting share** | — | ⛔ **R-08.** **And no second aggregation** |
| 16 | **Settings** ✅ [458](architecture/458-settings-traceability-audit.md) | Workspace · membership · invitation · role · **audit trail** · **seats** | — | ✅ **13 endpoints** · ⛔ **R-05 · R-10** |

---

# Part B · The product as one system

**The instruction is *"do not analyse screens independently."*** **Read down the `required` column instead of across it, and the shape changes: nine of sixteen screens are blocked on four concepts, and no screen needs a new intelligence capability.**

## The convergences — ranked by consumers, which is [P-01](architecture/441-people-roadmap.md) used as a sort

| | Concept | Consumers | State |
|---|---|---|---|
| **R-00** | **Account matching** | **16** — and **4 were on no list** | ✅ **Ruled and sequenced, [D-077](DECISION_REGISTER.md).** **[TASK-434](BACKLOG.md) is `READY` at the head, ahead of [TASK-406](BACKLOG.md)'s backtest** — *"establish the reusable capability once rather than allowing multiple implementations to emerge independently."* **[443](architecture/443-account-matching-capability.md)** |
| **R-02** | **Scope · saved view** | **5 named, and the shell inherits into all 16** | **[TASK-433](BACKLOG.md)** — awaiting a naming ruling |
| **R-03** | **Proposed → approved → applied → withdrawn** | **6** | **[TASK-431](BACKLOG.md)** — awaiting a shape ruling. ⚡ **Its deadline half is answered: [447 §0](architecture/447-signal-center-traceability-audit.md) — `Snoozed.until` proves a window is a *read-time predicate*, never a scheduled transition. No scheduler, no timer, no expiry job** |
| **R-01** | **People · Affiliation** | **4 + Executive Dashboard's movements** | ✅ **Ruled [D-074](DECISION_REGISTER.md)** · **[TASK-427–430](BACKLOG.md)** |
| **R-15** | **Stated absence — a result says what it could not evaluate** | **7 instances · 5 screens · certification** | ⚠️ **The highest-density concept found, and it has never been built as a capability.** PS-01 · PS-02 · PS-06 · 410's 45% facet · [TASK-434](BACKLOG.md)'s `unmeasured` · [TASK-406](BACKLOG.md)'s unscored criterion · `missing_gates`. **PS-01 stated the rule; PS-02 rediscovered it two days later in an adjacent section.** **Name it before the eighth instance, do not refactor the seven** |
| **R-14** | **A human completion point that emits no business event** | **2 waiting · 1 satisfied** | ⛔ **Not systemic — `opportunity.stage_changed` and `target_accounts_changed` both exist, created when a consumer appeared.** **The rule is checkable: when a screen's completion point is a human decision, ask who downstream is now waiting.** [TASK-432](BACKLOG.md) is the first; `icp.declared` is the second |
| **R-13** | **The authorization model is short three dimensions** — **spend · field · quantity** | **3 screens, independently** | ⛔ **Casbin's tuple is `(sub, dom, obj, act)`.** Copilot needs *spend*, Companies needs *field* and *quantity*. **An architectural finding, not three feature gaps** |
| **R-12** | **The six verbs, and *17 surfaces one contract*** | **Every AI surface** | ⛔ **[C-419](LANE_COORDINATION.md)** — six values the design calls closed, and nothing closes them |
| **R-11** | **Forecast — deal value · plan · fiscal period · team** | **Executive Dashboard, and Opportunity Intelligence shares its aggregates** | ⛔ **[C-418](LANE_COORDINATION.md)** — **the approved UI says *forecast* and `buying_score_engine` refuses to forecast, in writing, twice.** **Four absences, one question** |
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

# Part B-2 · The taxonomy for reusable concepts ([D-084](DECISION_REGISTER.md))

**Three categories, and the discipline is that a concept enters the *narrowest* one that explains it.**

| | | Rule |
|---|---|---|
| ⚖️ **Architecture Principle** | **A repository-wide rule governing how the platform is designed** | ⛔ **Rare and stable.** **`CLAUDE.md` §2 is where they live and this register does not add to it** |
| 🏗️ **Platform Capability** | **Reusable implementation providing shared functionality across modules and screens** | **Matching · People · Timeline · Saved Views · Recommendation Lifecycle · Action Batch · Authorization dimensions** |
| 📐 **Product Pattern** | **Recurring product *semantics* — how information is presented or interpreted.** **Not necessarily a standalone component** | **Stated Absence · Transparent Partial Evaluation · Predicate-Based Evaluation · Explainability · Event-on-consumer** |

> ## ⛔ **The promotion test, and it runs downward**
>
> ***"Prefer existing repository principles whenever they already explain the observed behaviour. A new pattern should only be introduced when existing principles cannot adequately describe recurring product semantics."***
>
> **So: does `CLAUDE.md` §2 already explain it? → cite it, record nothing.** **Does it recur across screens as a *semantic*? → Product Pattern.** **Does it need code somebody owns? → Platform Capability.** **None of the above? → it is a screen's own feature and does not belong here.**

# Part B-3 · 📐 Product Patterns

| | Pattern | Explained by an existing principle? | Instances |
|---|---|---|---|
| **P-A** | **Stated absence** — *a result says what it could not evaluate* | ⚡ **No.** §2's *"the repository should tell the truth"* governs **documents**; this governs **results**, and nothing covers it | **7** — PS-01 · PS-02 · PS-06 · 410's 45% facet · `unmeasured` · unscored criterion · `missing_gates` |
| **P-A′** | **Transparent partial evaluation** | ✅ **Same pattern as P-A, stated from the evaluator's side.** **Recorded as one, not two** | *(see P-A)* |
| **P-B** | **Predicate over stored state** — *evaluate at read time; materialise nothing; schedule nothing* | 🟡 **Partly.** §2 explains the **engineering why** *(one authoritative representation · least powerful author)*; **it does not state the product semantic**, so the pattern is kept **and cites §2 rather than restating it** | **5** — `evidence_state` · `Snoozed.until` · `evaluate(criteria, attributes)` · a saved view *"not the results"* · **rule simulation** |
| **P-C** | **An event exists when a consumer appears** | 🟡 **Partly.** §2's *"no abstractions for hypothetical future needs"* explains the restraint; **the trigger — *a consumer appeared* — is the product half** | **4** — 2 satisfied · 2 waiting |
| **P-D** | **Explainability** — *a conclusion carries what it read and why* | 🟡 **Partly.** §2's *determinism* and *least powerful author* explain it; **the product semantic is that every AI surface renders its basis** | **Every AI surface** — `GroundedOutput` · `SupportBasis` · the Contribution Ledger · `EvidenceRef` |
| ~~**P-E**~~ | ~~Supersession, never mutation~~ | ✅ **Fully explained by §2** — *immutability is the default for anything that records a fact*. ⛔ **Removed from this table; cite `CLAUDE.md`** | — |
| ~~**P-F**~~ | ~~Action batches~~ | ⛔ **Not a pattern — a Platform Capability.** **[R-03](#)**, in Part B-2's second row | — |

> **Two rows were *removed* by applying the promotion test to a table this office had just written.** **That is the test working: a register that only accretes stops being evidence and becomes inventory.**

# Part B-4 · 🎯 The Trigger Register ([D-085](DECISION_REGISTER.md))

> **The observable condition that makes a capability necessary — never an anticipated need.** *"Avoid planning capabilities based solely on anticipated future needs. Instead, define the observable condition."*

**Eight triggers, and seven already existed scattered across documents. Collected, they sequence the roadmap.**

| Capability | 🎯 Observable trigger | Fired? | Source |
|---|---|---|---|
| **[R-01](#) People — the domain** | **A dependent customer-facing capability enters implementation** | ✅ **Fired** — [TASK-202](BACKLOG.md) is `READY` and names Epic C | [D-074](DECISION_REGISTER.md) |
| **[R-01](#) People — naming** | **A provider contract supplies a person identifier** | ⛔ **Not fired.** Re-measured 2026-08-05: no source | [TASK-429](BACKLOG.md) |
| **[R-03](#) Action batch** | ⚡ **The second module that must approve, apply and reverse** | ✅ **Fired, and structurally** — [ADR-0402](architecture/adr/0402-a-rule-is-data.md) makes *N* subscribers act | [451 §0](architecture/451-workflow-automation-traceability-audit.md) |
| **A search index** | ⚡ **The first search that must rank across more than one type** | ⛔ **Not fired.** *(Proposed replacement for [C-020](LANE_COORDINATION.md)'s timeline-shaped trigger)* | [450 §1](architecture/450-global-search-traceability-audit.md) |
| **An expression language** | ***"A real customer condition the tree cannot represent, not a hypothetical one"*** | ⛔ **Not fired** | [ADR-0402](architecture/adr/0402-a-rule-is-data.md) |
| **Notifications** | **Epic F phase 5** — *"a rule that matches and reaches nobody"* | ⛔ **Not fired** | [ADR-0402](architecture/adr/0402-a-rule-is-data.md) · [D-027](DECISION_REGISTER.md) |
| **Deletion and retention** | **First retention obligation · first deletion request · migration 0050** | ⛔ **Not fired** *(head is `0039`)* | [TASK-426](BACKLOG.md) |
| **Forecast** | ⚡ **Epic E1 delivers deal values from a customer's CRM** | ⛔ **Not fired** — [TASK-402](BACKLOG.md) is `IN VALIDATION` | [444](architecture/444-executive-dashboard-domain-assessment.md) · [C-418](LANE_COORDINATION.md) |

> **Two have fired and six have not.** ⚠️ **Both that fired are waiting on a product-owner act, not on engineering** — which is the most useful thing this table says.

# Part B-5 · 📖 Canonical Domain Vocabulary ([D-085](DECISION_REGISTER.md))

**Complements [ADR-0034](architecture/adr/0034-ubiquitous-language.md) — it does not replace it.** **ADR-0034 governs *customer-facing* words; this governs words used across *bounded contexts*.**

> ⚠️ **Building this found two collisions already in production, and neither had been noticed.**

| Term | Meanings in the repository | Verdict |
|---|---|---|
| **Owner** | ⚠️ **Two, both live.** **`WorkspaceRole.OWNER`** — an administrative role, the subject of every `policy.csv` row. **`opportunity_state.owner_id`** — *the seller working an account*, and `OwnerScope` is `ALL`/`MINE`/`UNASSIGNED` | 🔴 **A genuine collision.** *"Who owns this workspace"* and *"who owns this account"* are different questions with one word, **and the authorization model uses the first while every screen shows the second** |
| **Match** | ⚠️ **Two.** **`MatchStrength`** — identity resolution, *"a property of the rule, not a belief"*. **[TASK-434](BACKLOG.md)'s predicate** — does an account satisfy a criterion | 🟡 **Defensible and worth naming.** [443](architecture/443-account-matching-capability.md) already separates them as **resolution** and **evaluation** |
| **Segment** | ⚠️ **Two, possibly one** | ⬜ **Not extractable** — [446 §0](architecture/446-companies-traceability-audit.md) · [TASK-433](BACKLOG.md) |
| **Dismissed** | **One, deliberately.** `opportunity_engine` owns it — *"deliberately distinct from `CLOSED_LOST`… one is feedback about Signora's judgement, the other is a sales outcome"* — and a signal-level dismissal is **the same concept one level down** | ✅ **The worked example of this vocabulary working**: [417 §2b](architecture/417-executable-slice-audit.md) refused a second dismissal vocabulary before one was written |
| **Confidence** | **Deliberately absent as a name.** `MatchStrength` *"named rather than `confidence` deliberately — confidence invites probabilistic thinking"*; `SupportBasis` carries *the facts that produced a level* | ✅ **A word the repository refuses on purpose** |
| **Relevance** | **One** — `signal_engine`'s declared category, *"never computed"* | ✅ |
| **Resolution** | ⚠️ **Two, and both correct.** `signal_engine.Resolution` — a human decision. `ResolutionOutcome` — identity resolution | 🟡 **Same word, different contexts, no shared surface.** Watch, do not rename |
| **Absence · `unmeasured`** | **One idea, seven spellings** | 📐 **[P-A](#)** — the vocabulary case for naming it |

> **The rule this table enforces**: **§4's *"never introduce a second definition of a concept a module already owns"*, applied *across* contexts rather than within one.** **`Dismissed` proves it works; `Owner` proves it was needed earlier.**

# Part C-1 · 🚦 Foundation Readiness Matrix ([D-085](DECISION_REGISTER.md))

> ## **If engineering started this screen today, which foundations are already complete and which still need to exist?**

**Confidence is a statement about *this office's evidence*, not about the screen.** **🟢 audited · 🟡 assessed but not audited · ⬜ neither.** **Eight of sixteen are audited; the rest are honest placeholders and say so.**

| Screen | Wave | Foundations required | Complete today | Still needed | Confidence |
|---|---|---|---|---|---|
| **Design System v2** | — | **None** | ✅ **All** — needs no backend | — | 🟢 |
| **Account 360** | **1 ✅** | Entity · claims · score · timeline · research · narration | ✅ **10 sections shipped** | **[R-01](#)** *(contacts M-E, committee M-D)* · **[R-03](#)** for AI sections | 🟢 **[449](architecture/449-account-360-traceability-audit.md)** |
| **AI Copilot** | **2** | Grounding · evidence set · **[R-12](#)** · **[R-02](#)** · **[R-03](#)** | ✅ **The AI half entirely** — `DecisionPackage`, `EvidenceRef`, `SupportBasis`, the validator | **The *ask* route · [C-419](LANE_COORDINATION.md) verbs · an `ai_reasoning` `Resource` · [TASK-013](BACKLOG.md)'s released model** | 🟢 **[445](architecture/445-ai-copilot-traceability-audit.md)** |
| **Companies** | **3** | Account list · **[R-02](#)** · **[R-03](#)** · import · export | ✅ **List, owner scope, score, search** | **[R-02](#) · [R-03](#) · field authorization · import as a source adapter** | 🟢 **[446](architecture/446-companies-traceability-audit.md)** |
| **Signal Center** | **3** | Signal · catalog · resolution · **`signal.resolved`** | ✅ **Domain complete, all four outcomes, snooze** | **[TASK-432](BACKLOG.md)'s event · `Resource.SIGNAL` · [R-07](#)** | 🟢 **[447](architecture/447-signal-center-traceability-audit.md)** |
| **ICP Builder** | **3** | Declaration · **[R-00](#)** · lift · **[R-01](#)** | ✅ **Declaration, validation, and [TASK-434](BACKLOG.md) `PROMOTED`** | **[TASK-406](BACKLOG.md) in flight · `icp.declared` · 2 of 4 *Decision makers* need M-E · 3 criterion groups ⬜** | 🟢 **[448](architecture/448-icp-builder-traceability-audit.md)** |
| **Global Search** | **3** | Search · typed grouping · **[R-01](#)** · **[R-02](#)** | ✅ **Accounts searchable** | **`EntityKind.PERSON` · deals as a read · [TASK-408](BACKLOG.md) in flight · a ranking index when the trigger fires** | 🟢 **[450](architecture/450-global-search-traceability-audit.md)** |
| **Executive Dashboard** | **4** | Stage history · owner · **[R-00](#)** · forecast | ✅ **5 of 6 sections** — `opportunity_state` carries all of it | **[C-418](LANE_COORDINATION.md) — and *nothing* if the answer is pipeline health** | 🟢 **[444](architecture/444-executive-dashboard-domain-assessment.md)** |
| **Workflow Automation** | **5** | Rule · catalog · event · **[R-03](#)** · simulation | ✅ **[ADR-0402](architecture/adr/0402-a-rule-is-data.md) specifies all of it** | **The module itself · [R-03](#) · a pure evaluation entry point** | 🟢 **[451](architecture/451-workflow-automation-traceability-audit.md)** |
| **Opportunity Intelligence** | **4** | Probability · aggregates · competitors · calls | ✅ **Opportunity, stages, contributions, competitors declared** | ⚠️ **Shares wave 4's aggregates with Exec Dashboard — [C-418](LANE_COORDINATION.md) governs both** · calls evidence-gated | 🟡 **Assessed, not audited** |
| **CRM Integrations** | **5** | Connection · source adapter · sync health | ✅ **[C-326](LANE_COORDINATION.md) ruled, [409](architecture/409-inbound-source-port-contract.md) is the contract** | **[TASK-402](BACKLOG.md) in flight · the HubSpot developer application** | 🟡 |
| **AI Research** | **3** | Research request · plan · synthesis · cohort scope | ✅ **Built, with a state machine** | **Cohort research ([416](architecture/416-ai-research-scope-gap.md)) · shell scope · recorded refusals** | 🟡 |
| **People Intelligence** | **6** | **[R-01](#)** entirely | ⛔ **None** | **[TASK-427–430](BACKLOG.md), all four milestones** | 🟢 **[441](architecture/441-people-roadmap.md)** |
| **Settings** | **6** | Workspace · membership · invitation · audit · seats | ✅ **13 endpoints, the largest router** | **[R-05](#) lifecycle · [R-07](#) audit surface · [TASK-437](BACKLOG.md)** | 🟡 |
| **App Shell** | **3** | **[R-02](#) scope** · notifications · **[R-05](#)** · preferences · AI entry | ✅ **Identity, workspace context and search — the three nobody counts as shell work** | **[R-02](#) · [ADR-0040](architecture/adr/0040-notifications.md) · user preferences · the *ask* route · announcements** | 🟢 **[452](architecture/452-app-shell-traceability-audit.md)** |
| **Reports** | **7** | Report definition · block · rendering · share | ⛔ **None** | **[R-08](#) · [R-02](#) · field authorization** | ⬜ **Not audited** |

> ## What the matrix says that no single audit could
>
> **① Five screens are mostly ready and blocked by *one ruling each***: Executive Dashboard by [C-418](LANE_COORDINATION.md), Copilot by [C-419](LANE_COORDINATION.md) and [TASK-013](BACKLOG.md), Companies and Global Search by [TASK-433](BACKLOG.md), ICP Builder by nothing but time.
>
> **② The least-ready screen is the one every other screen inherits.** **App Shell is ⬜ and unaudited, and [R-02](#), notifications and [R-05](#) all land there.** ⚠️ **It should be audited next, ahead of any wave-4 screen.**
>
> **③ No screen is blocked by a missing *intelligence* capability.** **Eight audits, and the pipeline has never once been the gap.**

# Part C-2 · 🗺️ The Domain Coverage Matrix

> **The architectural navigation document.** **Due at ten screens ([D-081](DECISION_REGISTER.md) §7); ten are audited** — 444 · 445 · 446 · 447 · 448 · 449 · 450 · 451 · 452 · 453.

**Capability-first. [Part C-1](#) is the same evidence screen-first, and the two are deliberately different views of one body of work.**

**Criticality is scored on [D-089](DECISION_REGISTER.md)'s five dimensions: leverage · architectural criticality · risk of delay · complexity · expected future reuse.**

## 🏛️ The Architectural Confidence Lifecycle ([D-090](DECISION_REGISTER.md))

> **A capability moves through these on accumulated evidence, never on opinion — and the stage says *where this office should spend effort*.**

| Stage | Means | Product Office does |
|---|---|---|
| **Candidate** | One screen implies it | **Keep auditing** |
| **Emerging** | Two screens, independently | **Keep auditing** |
| **Validated** | Three or more, and no contradiction | **Keep auditing, start naming consumers** |
| 🏛️ **Architecturally Established** | ⛔ **Further audits would raise the consumer count without changing the conclusion** | **STOP proving. Finalise ownership, boundary, prerequisites, sequencing** |
| **Ready for Implementation** | Owner, boundary and sequence are ruled | **Hand to the owning lane** |
| **Implemented** | On `main` | **Discharge from the matrix** |

> ***"Do not continue collecting the same evidence once the architectural conclusion has become stable."*** **[R-02](#) and [R-03](#) crossed into 🏛️ at the tenth audit; [454](architecture/454-r02-r03-implementation-preparation.md) is what that transition produces.**

| Capability | Category | Owner | Consuming screens | Dependency chain | Status | Wave | 🎯 Trigger | Criticality |
|---|---|---|---|---|---|---|---|---|
| **[R-00] Criteria Evaluation** | 🏗️ | `commercial_profile` | **8** — ICP Builder · Companies · Copilot · Exec Dash · Search · Research · Workflow · E1 | ICP declaration → predicate → lift · cohorts · rules | ⚠️ **`PROMOTED`, no reachable caller** | Shipped | ✅ fired | ⚠️ **NOT discharged — [C-332](LANE_COORDINATION.md).** Nothing constructs an `ObservedAttributes` |
| **[R-02] Global scope · Saved view** | 🏗️ | ⚡ **`workspace_tenancy` recommended — [454 §1](architecture/454-r02-r03-implementation-preparation.md)** | **16 inherit · 5 name it** | Shell → every filtered read → Reports · Segments | 🔴 **Missing** | 3 | ⛔ not fired | 🏛️ **Ready for Implementation** — owner ruled, [Context Definition](architecture/455-context-definitions-r02-r03.md) written, **4 slices decomposed.** 🔴 **Blocked on a *name* alone** |
| **[R-03] Action batch** | 🏗️ | ⚡ **A new bounded context recommended — [454 §2](architecture/454-r02-r03-implementation-preparation.md)** | **7** — Workflow · Companies · Copilot · Opp Intel · Settings · Account 360 · Exec Dash | [ADR-0402](architecture/adr/0402-a-rule-is-data.md) → *N* subscribers → approve · apply · **withdraw via [P-B](#)** | 🔴 **Missing** | **before 2** | ✅ **fired, structurally** | 🏛️ **Ready for Implementation** — owner ruled, [Context Definition](architecture/455-context-definitions-r02-r03.md) written, **6 slices decomposed.** 🔴 **Blocked on a *shape*, which its ADR needs** |
| **[R-01] People · Affiliation** | 🏗️ | `people` *(new)* | **6** — People · Account 360 · ICP Builder · Copilot · Exec Dash · Search | ADR-0400 → `EntityKind.PERSON` → Affiliation → timeline · committee · criteria | **Sequenced** | **1.5** | ✅ fired | 🟠 **High. Split M-D/M-E** |
| **[R-13] Authz dimensions** | 🏗️ | `signora_platform` | **6** — Copilot *(spend)* · Companies *(field, quantity)* · Reports *(field)* · Search *(field)* · Workflow | Casbin `(sub,dom,obj,act)` → three absent terms | 🔴 **Missing** | — | ⛔ | 🟠 **Architectural. Every gap is in an unbuilt screen** |
| **[R-15] Stated absence** | 📐 **P-A** | ⚠️ **None — a pattern** | **5 + certification + the API contract** | PS-01 → PS-02 → PS-06 → 410 → `unmeasured` → unscored criterion → `missing_gates` → **score expiry** | ⚠️ **8 instances, 0 implementations** | — | — | 🟠 **Name before the ninth** |
| **[R-07] Audit surface** | 🏗️ | 🟡 **`workspace_tenancy` recommended — [454 §3](architecture/454-r02-r03-implementation-preparation.md)** | **3** — Settings · Signal Center · Copilot | `actor_id` in 37 files → one history endpoint → a query surface | 🟡 **Attribution ✅, query 🔴** | 6 | ⛔ | 🟡 **Medium** |
| **[R-14] Completion events** | 📐 **P-C** | per module | **2 waiting · 2 satisfied** | Human decision → event → timeline · measurement | **[TASK-432](BACKLOG.md) + `icp.declared`** | — | ✅ fired | 🟡 **Cheap, and losing evidence daily** |
| **[R-12] Verb taxonomy** | 🏗️ | `ai_reasoning_engine` | **2** — Copilot · Search | 410's six verbs → one route or 17 | 🔴 **[C-419](LANE_COORDINATION.md)** | 2 | ⛔ | 🟡 **Decides a published language** |
| **[R-05] Workspace lifecycle** | 🏗️ | `workspace_tenancy` | **2 + the shell all 16 inherit** | Trial → active → suspended → archived | 🔴 **Missing** | 6 | ⛔ | 🟡 **Ordering, not capability** |
| **[R-11] Forecast** | 🏗️ | ⛔ **Deliberately unassigned — [454 §3](architecture/454-r02-r03-implementation-preparation.md)** | **2** — Exec Dash · Opp Intel | Deal value *(E1)* → plan → fiscal period → team | 🔴 **[C-418](LANE_COORDINATION.md)** | 4 | ⛔ **behind E1** | 🟠 ⚠️ **Refused in writing 3×, once in the published API contract** |
| **[R-04] Notification** | 🏗️ | `notifications` *(new)* | **5** — Shell · Signal Center · Search · Workflow · Companies | [ADR-0040](architecture/adr/0040-notifications.md) → delivery → monitored search | ⏸ **Deferred [D-027](DECISION_REGISTER.md)** | — | **Epic F phase 5** | 🟡 |
| **[R-08] Report definition** | 🏗️ | ⚠️ Undecided | **1** | Definition → block → rendering → share | 🔴 | 7 | ⛔ | ⚪ **Low — and last on evidence** |
| **Timeline** | 🏗️ | `timeline` | **8** | 9 projection rules → 9 publishers | ✅ **Built** ⚠️ **2 of 9 wired** | — | — | 🟠 **[TASK-901](BACKLOG.md)** |
| **Explainability** | 📐 **P-D** | `ai_platform` | **Every AI surface** | Evidence set → grounding → citation → basis | ✅ **Built** | Shipped | — | ✅ **Discharged, and a differentiator** |
| **Identity Resolution** | 🏗️ | `knowledge_graph` | **4** | Claim → candidate → rule → binding | ✅ **Built** | Shipped | — | ✅ **Discharged** |

## What the matrix says that ten separate audits did not

**① Two capabilities are 🔴-critical and each is blocked by one sentence from the product owner.** **[R-02](#) waits on a *name*; [R-03](#) waits on a *shape*.** **Between them they are inherited by sixteen screens and needed by seven** — **and neither is blocked by engineering.**

**② Five capabilities are discharged.** **[R-00](#), Explainability, Identity Resolution, Timeline *(built)* and the authorization boundary.** **Everything the *intelligence pipeline* needed is done** — which is the same sentence the readiness matrix produced from the other direction.

**③ Nothing on this page is blocked by a missing intelligence capability.** **Ten audits. The pipeline has never once been the gap.**

**④ ⚡ Ownership was undecided for four of sixteen; [454](architecture/454-r02-r03-implementation-preparation.md) recommends three and deliberately leaves the fourth alone.** *(Original finding retained:* **ownership is undecided for four of sixteen** — [R-02](#), [R-03](#), [R-07](#), [R-11](#) — **and all four are cross-cutting.** ⚠️ **That is the [C-010](LANE_COORDINATION.md) shape recurring**: a capability that belongs to no bounded context belongs to whichever lane hits it first.*)

## 📊 Reuse density — permanent from [D-083](DECISION_REGISTER.md), six fields

**Maintained in [449 §5](architecture/449-account-360-traceability-audit.md) and re-measured every audit.** **Every count is a floor: 6 of 16 screens audited.**

| Capability | Category | Screens | Workflows | Owning module | Status · wave | **Trigger condition** |
|---|---|---|---|---|---|---|
| **[R-15] Stated absence** | 📐 **P-A** | **5 + certification** | Every read | ⚠️ **None — it is a pattern, not a module** | **7 instances, 0 implementations** | 🔴 **Highest, and unowned** |
| **[R-00] Account matching** | 🏗️ | **8** | Backtest · segments · rules · cohorts | `commercial_profile` | ⚠️ **`PROMOTED`, unusable — [C-332](LANE_COORDINATION.md)** | **High** |
| **[R-01] People · Affiliation** | 🏗️ | **6** | Committee · org chart · criteria · movements · search | `people` *(new)* | **Sequenced — wave 1.5, split M-D/M-E** | **High** |
| **[R-03] Action batch** | 🏗️ | **7** | Bulk · approve · AI apply · **rule subscribers** | ⚠️ Undecided | **Awaiting shape ruling** | ⚡ **The second module needing approve/apply/reverse — [451 §0](architecture/451-workflow-automation-traceability-audit.md) makes it structural** |
| **[R-02] Saved view** | 🏗️ | **4** | Every filtered read | ⚠️ Undecided | **Awaiting naming ruling — wave 3** | **Medium** ⚡ *defined by all four* |
| **[R-13] Authz dimensions** | 🏗️ | **4** | Spend · field · quantity | `signora_platform` | 🔴 **Missing** | **Medium** |
| **Timeline** | 🏗️ | **8** | Projection | `timeline` | ✅ Built · ⚠️ 2 of 9 wired | **High** |
| **Explainability / grounding** | 🏗️ | **Every AI surface** | Narration · reasoning · research | `ai_platform` | ✅ **Built** | **High** |
| **[R-14] Completion events** | 📐 **P-C** | **2 waiting · 2 satisfied** | Triage · ICP publication | `signal_engine` · `commercial_profile` | **[TASK-432](BACKLOG.md) + `icp.declared`** | **Low, correctly** |
| **[R-12] Verb taxonomy** | 🏗️ | **2** | Ask · route-to-assistant | `ai_reasoning_engine` | **[C-419](LANE_COORDINATION.md)** | **Low so far** |

### ⚖️ Prioritise by leverage, not only by urgency ([D-088](DECISION_REGISTER.md))

> ***"Estimate its consumer count — how many current and planned screens, workflows, APIs, AI capabilities and future roadmap items will reuse it. Prioritize foundational work not only by urgency but also by repository-wide leverage."***

| | Leverage | Trigger | |
|---|---|---|---|
| **[R-02](#) Global scope · saved view** | 🔴 **Highest in the product — 16 screens inherit** | Not fired | ⚠️ **Blocked on a *naming* question, [TASK-433](BACKLOG.md)** |
| **[R-03](#) Action batch** | 🔴 **7 screens + every rule subscriber** | ✅ **Fired** | ⚡ **The only capability with high leverage *and* a fired trigger — rule first on this measure** |
| **[R-01](#) People** | 🟠 6 screens | ✅ **Fired** | Awaiting placement |
| **[R-15](#) Stated absence** | 🟠 5 screens + certification | — | 7 instances, 0 implementations |

> **Leverage says something urgency did not: [R-02](#) is in front of sixteen screens and is blocked on one sentence.**

> **Density separates a foundation from a feature, and the first two measurements already disagree with intuition:** **the highest-density row is a *pattern with no owner*, and the lowest is the one that sounds most like platform work.**

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

# 461 · Product-Led Domain Discovery — the consolidated review

**Lane C · Product Office · 2026-08-05.** **The hand-off document for the discovery phase.** **[D-092](../DECISION_REGISTER.md).**

> **This is the reference implementation lanes read.** **Where it disagrees with an individual audit, the audit holds on evidence and this document holds on sequencing** — the audits are dated records; this is the current plan.

**Measured against `origin/integration`. Sixteen screens audited: [444](444-executive-dashboard-domain-assessment.md)–[460](460-people-and-design-system-traceability-audit.md).**

---

# 1 · 💰 Foundation Investment Roadmap

**Ranked on [D-089](../DECISION_REGISTER.md)'s five dimensions. *Return* is leverage × criticality ÷ complexity, stated as a judgement rather than a formula.**

| # | Capability | Criticality | Leverage | Readiness | Complexity | Depends on | Wave |
|---|---|---|---|---|---|---|---|
| **1** | **[R-03](../DOMAIN_DISCOVERY_REGISTER.md) Action Batch** | 🔴 **Structural** — [ADR-0402](adr/0402-a-rule-is-data.md)'s fan-out makes per-module duplication certain | **7 screens + every rule subscriber** | 🏛️ **Ready** — [Context Definition](455-context-definitions-r02-r03.md), 6 slices | 🟠 Medium | **A shape ruling → an ADR** | **Before 2** |
| **2** | **[R-02](../DOMAIN_DISCOVERY_REGISTER.md) Saved View** | 🟠 High | **16 inherit · 4 name it** | 🏛️ **Ready** — [Context Definition](455-context-definitions-r02-r03.md), 4 slices | 🟢 **Low** — one table, no behaviour | **A name** | **3** |
| **3** | **[R-01](../DOMAIN_DISCOVERY_REGISTER.md) People · Affiliation** | 🟠 High | **6 screens** | **Sequenced** — [441](441-people-roadmap.md), 4 milestones | 🟠 Medium | **A placement** | **1.5** |
| **4** | **[R-14](../DOMAIN_DISCOVERY_REGISTER.md) Completion events** | 🟡 **Losing evidence daily** | 2 waiting | **[TASK-432](../BACKLOG.md) `SEQUENCED`** | 🟢 **Trivial** — one event type | **Nothing** | **Now** |
| **5** | **[R-15](../DOMAIN_DISCOVERY_REGISTER.md) / [P-A](../DOMAIN_DISCOVERY_REGISTER.md) Stated Absence** | 🟠 ⚡ **Now a product promise on two screens** | **9 instances** | **Candidate** — no owner | 🟢 Low | **Naming it** | — |
| **6** | **[R-13](../DOMAIN_DISCOVERY_REGISTER.md) Authorization dimensions** | 🟠 **Architectural** — 🔴 and needs an ADR | **6 screens, all unbuilt** | **Validated** | 🔴 **High** — the policy tuple | **An ADR** | **Before the first export** |
| **7** | **[R-07](../DOMAIN_DISCOVERY_REGISTER.md) Audit surface** | 🟡 | 3 screens | **Owner recommended** | 🟢 Low | **Nothing** | 6 |
| **8** | **[R-12](../DOMAIN_DISCOVERY_REGISTER.md) Verb taxonomy** | 🟡 **Decides a published language** | 2 | **[C-419](../LANE_COORDINATION.md)** | 🟢 Low | **A ruling** | 2 |
| **9** | **[R-05](../DOMAIN_DISCOVERY_REGISTER.md) Workspace lifecycle** | 🟡 **Ordering, not capability** | 2 + the shell | **Emerging** | 🟠 | [TASK-426](../BACKLOG.md) | 6 |
| **10** | **[R-08](../DOMAIN_DISCOVERY_REGISTER.md) Report definition** | ⚪ Low | 1 | **Candidate** | 🟠 | Nothing | **7** |
| **—** | **[R-11](../DOMAIN_DISCOVERY_REGISTER.md) Forecast** | ⛔ **May not exist** | 2 | **Blocked on a product decision** | 🔴 | **[C-418](../LANE_COORDINATION.md), then E1** | — |
| **—** | **[R-04](../DOMAIN_DISCOVERY_REGISTER.md) Notification** | ⏸ **Deferred by ruling** | 5 | ⏸ | 🟠 | [ADR-0040](adr/0040-notifications.md) | — |

> ## The roadmap's one surprising row is #4
>
> **[TASK-432](../BACKLOG.md) is one event type, needs no ruling, and is the only item on this page that is *actively losing* something.** **Every day it does not exist, a human triage decision is recorded as state with no transition, and [TASK-406](../BACKLOG.md) is waiting to measure exactly those outcomes.** **On return per unit of effort it outranks everything above it.**

---

# 2 · 🏛️ Architectural Stability Assessment

| Class | Capabilities |
|---|---|
| ✅ **Architecturally Stable** | **The intelligence pipeline entire** — claim · observation · business event · signal · buying score · contribution ledger · timeline · identity resolution · explainability and grounding · the provider port · the outbox chain · **[R-00](../DOMAIN_DISCOVERY_REGISTER.md) Criteria Evaluation** · the authorization *model* · the JWT boundary · the tenancy model |
| 🟨 **Stable with Planned Evolution** | **[R-01](../DOMAIN_DISCOVERY_REGISTER.md)** *(ADR-0400 ratified, 4 milestones)* · **[R-02](../DOMAIN_DISCOVERY_REGISTER.md)** and **[R-03](../DOMAIN_DISCOVERY_REGISTER.md)** *(definitions written, decompositions ready)* · **`workflow`** *([ADR-0402](adr/0402-a-rule-is-data.md) ratified, unbuilt)* · **[R-07](../DOMAIN_DISCOVERY_REGISTER.md)** *(owner recommended)* · **`integrations`** *(built; blocked on a developer application)* |
| 🔍 **Requires Further Discovery** | **[R-13](../DOMAIN_DISCOVERY_REGISTER.md)** — three dimensions Casbin's tuple cannot express, and **no ADR has been attempted** · **[R-08](../DOMAIN_DISCOVERY_REGISTER.md)** · **[R-15](../DOMAIN_DISCOVERY_REGISTER.md)'s *shape*** — nine instances agree on the principle and none on a mechanism |
| ⏸ **Deferred by Explicit Product Decision** | **[R-04](../DOMAIN_DISCOVERY_REGISTER.md)** [D-027](../DECISION_REGISTER.md) · **[O3](../DECISION_REGISTER.md)** shell placement · **[C-020](../LANE_COORDINATION.md)** M7 scope · **[C-322](../DECISION_QUEUE.md)/[C-002](../LANE_COORDINATION.md)** · **[C-210](../DECISION_QUEUE.md)/[C-203](../DECISION_QUEUE.md)** personal data · **[C-005](../DECISION_QUEUE.md)** · **[C-025](../DECISION_QUEUE.md)** · **[R-11](../DOMAIN_DISCOVERY_REGISTER.md)** *(pending [C-418](../LANE_COORDINATION.md))* · **calls / activity capture** [MC-10](../PRODUCT_EXPERIENCE.md) |

---

# 3 · 📋 Architectural Readiness Summary

| Capability | Confidence | Owner | `public/` | Context Def | Decomposition | Dependent areas | Governance remaining | Wave |
|---|---|---|---|---|---|---|---|---|
| **[R-00](../DOMAIN_DISCOVERY_REGISTER.md)** | ⚠️ **Implemented, not usable** | `commercial_profile` | ✅ **Published** | ⚠️ [443](443-account-matching-capability.md), **corrected** | ✅ 2 slices, shipped | 8 screens | ⚠️ **[C-332](../LANE_COORDINATION.md) — an input with no producer** | ✅ |
| **[R-02](../DOMAIN_DISCOVERY_REGISTER.md)** | 🏛️ **Ready** | ✅ `workspace_tenancy` | **Slice 1** | ✅ [455 §1](455-context-definitions-r02-r03.md) | ✅ 4 slices | 4 + 16 inherit | **[TASK-433](../BACKLOG.md) — a name** | 3 |
| **[R-03](../DOMAIN_DISCOVERY_REGISTER.md)** | 🏛️ **Ready** | ✅ **New context** | **Slice 1** | ✅ [455 §2](455-context-definitions-r02-r03.md) | ✅ 6 slices | 7 screens | **[TASK-431](../BACKLOG.md) — a shape, then an ADR** | **before 2** |
| **[R-01](../DOMAIN_DISCOVERY_REGISTER.md)** | **Established** | ✅ `people` *(new)* | — | ✅ [ADR-0400](adr/0400-person-as-an-entity.md) | ✅ 4 milestones | 6 screens | **[TASK-427](../BACKLOG.md) placement** | 1.5 |
| **[R-14](../DOMAIN_DISCOVERY_REGISTER.md)** | **Established** | per module | n/a | — | ✅ [TASK-432](../BACKLOG.md) | 4 | ⛔ **None** | **now** |
| **[R-07](../DOMAIN_DISCOVERY_REGISTER.md)** | **Validated** | 🟡 `workspace_tenancy` | — | — | — | 3 | **Confirm the owner** | 6 |
| **[R-13](../DOMAIN_DISCOVERY_REGISTER.md)** | **Validated** | `signora_platform` | — | — | — | 6 | **An ADR — 🔴** | — |
| **[R-15](../DOMAIN_DISCOVERY_REGISTER.md)** | **Validated** | ⚠️ **None** | — | — | — | 5 + certification + the API | **Name it** | — |
| **[R-12](../DOMAIN_DISCOVERY_REGISTER.md)** | **Emerging** | `ai_reasoning_engine` | — | — | — | 2 | **[C-419](../LANE_COORDINATION.md)** | 2 |
| **[R-05](../DOMAIN_DISCOVERY_REGISTER.md)** | **Emerging** | `workspace_tenancy` | — | — | — | 2 + shell | — | 6 |
| **[R-08](../DOMAIN_DISCOVERY_REGISTER.md)** | **Candidate** | ⚠️ None | — | — | — | 1 | — | 7 |
| **[R-11](../DOMAIN_DISCOVERY_REGISTER.md)** | **Blocked** | ⛔ **Deliberately none** | — | — | — | 2 | **[C-418](../LANE_COORDINATION.md)** | — |

---

# 4 · 🕸️ Cross-screen dependency map

```
                    ┌──────────────────────────────────────────────┐
                    │  THE INTELLIGENCE PIPELINE — stable, shipped   │
                    │  claim → observation → business event →       │
                    │  signal → buying score → contribution ledger  │
                    └───────────────────────┬──────────────────────┘
                                            │  consumed by 10 screens
   ┌────────────────────┬──────────────────┼──────────────────┬────────────────────┐
   │                    │                  │                  │                    │
┌──▼──────┐      ┌──────▼─────┐     ┌──────▼──────┐    ┌──────▼──────┐   ┌─────────▼────────┐
│ R-02    │      │ R-03       │     │ R-01        │    │ R-00 ✅     │   │ R-13             │
│ Saved   │      │ Action     │     │ People      │    │ Criteria    │   │ Authz dimensions │
│ View    │      │ Batch      │     │ Affiliation │    │ Evaluation  │   │ spend·field·qty  │
└──┬──────┘      └──────┬─────┘     └──────┬──────┘    └──────┬──────┘   └─────────┬────────┘
   │ 16 inherit         │ 7 screens        │ 6 screens        │ 8 screens          │ 6 screens
   │                    │                  │                  │                    │
   ├ App Shell          ├ Workflow ◀───────┼──[ADR-0402]      ├ ICP Builder        ├ Copilot (spend)
   ├ Companies          ├ Companies        ├ Account 360      ├ Companies          ├ Companies
   ├ Global Search      ├ Copilot ×17      ├ ICP Builder      ├ Copilot            ├ Reports
   └ Reports            ├ Opp Intel        ├ Exec Dash        ├ Exec Dash          ├ Search
                        ├ Settings         ├ Global Search    ├ Workflow rules     ├ Settings
                        ├ Account 360      └ People Intel     ├ AI Research        └ Workflow
                        └ Exec Dash                           ├ Global Search
                                                              └ E1 arrival
   ┌─────────────────────────────────────────────────────────────────────────────┐
   │  P-A STATED ABSENCE — 9 instances, no owner, and 2 are customer promises     │
   │  PS-01 · PS-02 · PS-06 · 410's facet · unmeasured · unscored criterion ·     │
   │  missing_gates · score expiry (API) · recorded refusals (Research + Copilot) │
   └─────────────────────────────────────────────────────────────────────────────┘
```

> **The map's shape is the whole finding: four capabilities sit between one stable pipeline and sixteen screens, and every screen reaches the pipeline *through* them.**

---

# 5 · ⏸ Deferred, with their triggers

| | 🎯 Trigger | Fired? |
|---|---|---|
| **People — naming** | A provider contract supplying a person identifier | ⛔ |
| **A search index** | ⚡ **The first search that must rank across more than one type** | ⛔ |
| **An expression language** | *"A real customer condition the tree cannot represent"* | ⛔ |
| **Notifications** | Epic F phase 5 | ⛔ |
| **Deletion and retention** | First obligation · first request · **migration 0050** *(head is 0039)* | ⛔ |
| **Forecast** | **[C-418](../LANE_COORDINATION.md), then Epic E1 delivering deal values** | ⛔ |
| **Feature flags** | *"Propose when a slice needs one"* | ⛔ |
| **Calls · activity capture** | A source | ⛔ |
| **[R-01](../DOMAIN_DISCOVERY_REGISTER.md) — the domain** | The first dependent capability enters implementation | ✅ **Fired** |
| **[R-03](../DOMAIN_DISCOVERY_REGISTER.md)** | ⚡ **The second module needing approve/apply/reverse** | ✅ **Fired, structurally** |

---

# 6 · ⚖️ Remaining governance decisions — four, and none blocks engineering today

| | Decision | In front of |
|---|---|---|
| **[TASK-431](../BACKLOG.md)** | **R-03's shape** *(and its ADR)* | **6 prepared slices · 7 screens** |
| **[TASK-433](../BACKLOG.md)** | **R-02's name** ⬜ *(and the `Segment` semantics upstream of it)* | **4 prepared slices · 16 screens** |
| **[TASK-427](../BACKLOG.md)** | **People's placement** — trigger fired | **4 milestones** |
| **[C-417](../DECISION_QUEUE.md)** | **ADR-0404's ①②** — a bounded exception, five comment lines | **[TASK-901](../BACKLOG.md)'s 7 slices** |
| **[C-418](../LANE_COORDINATION.md)** | **Does Signora forecast?** | 4 concepts, 2 screens |
| **[C-419](../LANE_COORDINATION.md)** | **The verb taxonomy** | Copilot's 17 surfaces |

---

# 7 · 📐 Recommended implementation sequence

| | | Why here |
|---|---|---|
| **1** | **[TASK-432](../BACKLOG.md)** — `signal.resolved` | **One event, no ruling, and it is losing evidence now** |
| **2** | **[C-417](../DECISION_QUEUE.md)** ruled → **[TASK-418](../BACKLOG.md) ①②** → **[TASK-901](../BACKLOG.md)** | **Seven slices behind one ruling, and it is Lane A's only refill** |
| **3** | **[TASK-431](../BACKLOG.md)** ruled → **R-03 slice 1** | **Contract first: seven consumers unblock at once** |
| **4** | **[TASK-427](../BACKLOG.md)** placed → **R-01 M-D** | **Wave 1.5, ahead of four dependents** |
| **5** | **[TASK-433](../BACKLOG.md)** ruled → **R-02 slice 1** | **Before wave 3's shell** |
| **6** | **R-03 slices 2–6** · **R-02 slices 2–4** | ⚡ **Parallel, different lanes — neither touches the other** |
| **7** | **[R-13](../DOMAIN_DISCOVERY_REGISTER.md)'s ADR** | **Before the first export ships**, not after |

---

# 8 · 🔍 Product-Led Domain Discovery Outcomes

| | Count |
|---|---|
| **Screens audited** | **16 of 16** |
| **Documents produced** | **21** — [440](440-people-roadmap-integration.md)–[460](460-people-and-design-system-traceability-audit.md) |
| **Product-owner decisions recorded** | **18** — D-074…D-091 |
| **Foundational capabilities discovered** | **12** — R-00…R-15 |
| **Existing capabilities confirmed and reused unchanged** | **16** — the pipeline's nine stages, identity resolution, explainability, timeline, the outbox chain, the provider port, the tenancy model, the JWT boundary |
| ⚡ **Proposed concepts rejected through reuse** | **20** *(§8a)* |
| ⚡ **Architectural assumptions corrected** | **14**, plus **5 defects found inside this office's own instruments** *(§8b)* |
| **UI requirements producing genuine platform evolution** | **12** |
| **Backlog rows created** | **12** — TASK-427…TASK-438 |
| **Of which already shipped** | **2 `PROMOTED`** · 1 `CLAIMED` · 1 `READY` · 6 `SEQUENCED` · 2 `WAITING` |
| **Coordination items raised** | **4** — C-417…C-420, **1 ruled** |
| **Backlog rows from the final six audits** | ⚡ **0** |

## 8a · The twenty rejections, because the number means nothing without them

**Triage state** *(existed)* · **a scheduler for R-03** *(`Snoozed.until`)* · **a deadline-driven lifecycle as a new shape** *(not new)* · **supersession as a new pattern** *(§2)* · **action batches as a pattern** *(a capability)* · **Research Session** *(built)* · **Timeline** *(built)* · **Identity Resolution** *(built)* · **Relationship Graph** *(built)* · **Explainability** *(built)* · **AI Conversation** *(⛔ forbidden by Statelessness)* · **deals as an `EntityKind`** *(a read)* · **monitored search inside R-02** *(split out)* · **an org-chart confidence concept** *(`IdentityState`)* · ***"built once, read three ways"*** *(`MaterializedNarration`)* · **simulation as new architecture** *([P-B](../DOMAIN_DISCOVERY_REGISTER.md))* · **background activity as a shell feature** *(R-03's read surface)* · **a second aggregation for Reports** *(refused)* · **import as a new inbound door** *(`IntegrationSourceAdapter`)* · **a second dismissal vocabulary** *(refused before it was written)*.

## 8b · The corrections, including five to this office's own tools

**Architectural:** [439](439-people-intelligence-reassessment.md)'s *"build nothing"* was measured correctly and incompletely · [440](440-people-roadmap-integration.md)'s *"wave 2"* should have been wave 1.5 · [442](442-product-led-domain-discovery.md) reported triage missing · [442](442-product-led-domain-discovery.md)'s `Segment` collision became ⬜ · [446](446-companies-traceability-audit.md)'s *"genuinely new shape"* was not new · [448](448-icp-builder-traceability-audit.md) split R-01 across M-D/M-E · [449](449-account-360-traceability-audit.md) restated R-14 · [452](452-app-shell-traceability-audit.md) conflated two execution contexts · R-13 narrowed twice · [ADR-0404](adr/0404-platform-composition.md) said eight ignores and there are five · [ADR-0404](adr/0404-platform-composition.md)'s §Validation never asked who owns the trees a capability reaches · [404](404-epic-g-copilot.md)'s *"no `interface/` directory"* was stale · [417](417-executable-slice-audit.md)'s *"none of it exists"* was stale.

**Instruments, each found by running them rather than reading them:** `decision-queue.py` counted `OPEN` by substring and *"closed on the day it was opened"* matched · `READY FOR PRODUCT DECISION` read as **shut** · `vocabulary-check.py` demanded a module for a `reserved` term · and flagged a **canonical** term spreading, which is the success case · `state-check.py`'s stale-location guard flagged the document it was written to fix.

> ## The evidence the backend supports the approved product
>
> **① No screen is blocked by a missing intelligence capability.** **Sixteen audits, and the pipeline has never once been the gap.**
> **② Eleven of sixteen screens are mostly a read surface over intelligence that already exists** — [411](411-ui-convergence-assessment.md) said so before the audits and sixteen audits did not contradict it.
> **③ The final six audits produced zero new foundational rows.**
> **④ Twenty rejections against twelve discoveries.** **Reuse won more often than invention, by a factor approaching two.**

---

# 9 · How Product Office operates after this phase

**Discovery was a phase. Stewardship is not.**

| Then | Now |
|---|---|
| **Audit every screen** | **Audit each newly approved design as it arrives** — the same protocol, one screen at a time |
| **Discover foundations** | **Steward the twelve already discovered** — contracts, sequencing, ownership, and defending the boundaries in [455](455-context-definitions-r02-r03.md)'s non-responsibility lists |
| **Prove capabilities exist** | ⛔ **Stop at 🏛️ Established.** *"Do not continue collecting the same evidence once the conclusion has become stable"* |
| **Produce documents** | **Maintain five living instruments** — the [Register](../DOMAIN_DISCOVERY_REGISTER.md), the [Coverage Matrix](../DOMAIN_DISCOVERY_REGISTER.md), the [Readiness Matrix](../DOMAIN_DISCOVERY_REGISTER.md), the [Trigger Register](../DOMAIN_DISCOVERY_REGISTER.md) and the [Vocabulary](../coordination/vocabulary.toml) |

## The four standing responsibilities

**① Watch the triggers.** **Ten conditions are recorded and two have fired.** **A trigger firing is the signal to prepare, and nothing else is.**
**② Defend the Context Definitions.** ⚡ **A capability erodes through its non-responsibilities, one reasonable exception at a time.** **When a slice asks the batch to know what it is reversing, that is the moment.**
**③ Audit each new design on arrival**, not in a batch — **a screen audited before implementation costs a document; audited after, it costs a slice.**
**④ Keep the vocabulary graph current**, and **let it fail** — [452](452-app-shell-traceability-audit.md) found a collision the graph missed because neither term was registered, **and that is how the register earns entries.**

## What would mean this phase failed

> **Implementation reaching a screen and discovering an architectural question.** **Sixteen audits exist so that the next sixteen slices find answers rather than questions** — **and the only honest test of that is the first slice that hits one.**

---

# 9a · ⚠️ The first miss, recorded on the day the phase closed

**[D-093](../DECISION_REGISTER.md): *"if implementation reaches a feature and discovers a missing foundational concept that reasonably should have been identified during Product-Led Domain Discovery, that should be treated as a Product Office finding."*** **One arrived immediately.**

> **[C-332](../LANE_COORDINATION.md), raised by Lane B: `evaluate(icp, observed)` is promoted and correct, and *nothing in the repository constructs an `ObservedAttributes`*.** **[443](443-account-matching-capability.md) and [TASK-406](../BACKLOG.md)'s row both said *"the per-criterion lift half is unaffected and needs nothing new."* That is measurably wrong.**

**Why it was missed, stated precisely rather than apologised for:**

> ⚡ **[443](443-account-matching-capability.md) made the function pure *specifically* to avoid the import contract — *"the facts are handed to it"* — and never asked who hands them.**

**And it is the second instance of one failure mode.** **[ADR-0404](adr/0404-platform-composition.md)'s §Validation checked that `apps/worker` had an owner and never checked who owned the trees the capability reached** — [C-417](../LANE_COORDINATION.md). **Twice, this office designed a boundary and did not ask who stands on the other side of it.**

## The methodology change it earns

**Every Context Definition gains one line: *who constructs each input to this capability's public interface, and may they reach it?*** ⚡ **[455](455-context-definitions-r02-r03.md)'s two definitions are re-checked against it below, and both hold** — R-02's inputs are a name and an opaque declaration supplied by the caller; R-03's are supplied by the acting module, which is the party already doing the write.

> **A purity that removes an import contract from the *implementation* can move the problem to the *caller*, and a definition that lists non-responsibilities without naming its suppliers will not show it.**

# 10 · What this document did not do

**Nothing implemented · no lane named · no wave reordered · no module created · no ADR drafted · no queue file touched · no backlog row added.**

**And it discovered nothing.** **A consolidated review that produced a new finding would mean the phase it summarises had not finished.**

# 440 · People, integrated into the active roadmap — sequencing, not reversal

**Lane C · Product Office · 2026-08-05.** Product Office directive: *"plan this work into the active roadmap instead of treating it as a distant future initiative… this is now a sequencing exercise."*

**Supersedes nothing.** [ADR-0400](adr/0400-person-as-an-entity.md), [C-221](../LANE_COORDINATION.md) and [439](439-people-intelligence-reassessment.md) all stand. **This answers the question 439 did not ask.**

---

# 0 · The finding — People is scheduled *after* four of its own dependents

**[412](412-backend-capability-matrix.md) places People at wave 6 of 7. Measured against the same document's wave list, four earlier waves contain screens that need it.**

| Wave | Screens | Needs People for |
|---|---|---|
| **1** ✅ shipped | **Account 360** | **Contacts and org-chart sections — shipped as ⬜ stated absences** |
| **2** | **AI Copilot** | **Committee reasoning** — named in 412's own dependency graph |
| **3** | Shell · Companies · Signal Center · **ICP Builder** · AI Research | **The four *Decision makers* criteria** |
| **4** | Opportunity Intelligence · **Executive Dashboard** | ***"forecast, risk, ageing, movements"*** — movements are affiliation intervals |
| 5 | CRM Integrations · Workflow Automation | — |
| **6** | **People Intelligence · Global Search** | **Where People is currently scheduled** |

> **So the product owner is right, and the evidence is stronger than the directive assumed.** **The dependent screens are not "future capabilities" — three of them are in the next three waves**, and **one has already shipped around the gap.**

## ⚠️ Where my previous assessment was incomplete

**[439 §4](439-people-intelligence-reassessment.md) concluded *"build nothing"* on a cost-of-waiting analysis that measured only refactor cost** — one enum member, one field, a new table rather than a migration. **That analysis is still correct and it was not the whole cost.**

**It never measured wave order.** **The cost of waiting is not only what changes later; it is every screen that ships a stated absence and must be revisited when the absence fills.** **Account 360 already paid it once.**

> **A domain that arrives after its consumers is not a refactor problem. It is a rework problem**, and it lands in the UI rather than the backend — which is exactly why a backend-only assessment missed it.

---

# 1 · The reconciliation — C-221's narrowing *is* the buildable first phase

**This is the finding that dissolves the apparent tension, and it required no new decision from anybody.**

**C-221, ruled today:** *"Epic C should initially focus on **role-based and organization-level intelligence**… treat named-person intelligence as a future enhancement once supported by provider capabilities."*

**ADR-0400's model:** **`Affiliation` — *person × company × title × interval*.**

**And what the pipeline already produces, in production, today:**

> A provider reports a role change → `RoleChangeValue(title, seniority, direction)` + `occurred_on` → `LEADERSHIP_APPOINTED` / `LEADERSHIP_DEPARTED` → `new_decision_maker` / `decision_maker_departed` → scored.

**A title, a direction, a date and a company. That is an affiliation interval opening or closing** — **and it has nowhere to land.**

| | |
|---|---|
| ✅ **Buildable now, with no provider change** | **An anonymous `Person` with `Affiliation` intervals.** *"A VP of Engineering joined Acme in March and left in September"* — **true, useful, and derived entirely from data that already flows** |
| ⛔ **Still gated on ❓1** | **A *named* person.** No provider supplies one — re-measured 2026-08-05 |

> **So the provider question gates phases 3 and beyond. It does not gate the entity.** **ADR-0400's own words**: *"if the answer is no, Phase 2 degrades to 'a VP of Engineering left' — **today's behaviour**"* — and today's behaviour is precisely what C-221 approved.

**The entity is not speculative. It is the missing subject of intelligence that already ships.**

---

# 2 · Roadmap placement

> ## **People moves from wave 6 to wave 2 — before AI Copilot, its first dependent.**

**Argued from dependency, which is how 412 argues every other wave.** *"Its position is now argued from dependency alone"* is 412's own sentence about wave 6, **and the dependency runs the other way.**

| | |
|---|---|
| **Not wave 1** | Account 360 has shipped. Nothing is gained by preceding it |
| **Wave 2** | ✅ **Before AI Copilot's committee reasoning, ICP Builder's decision-maker criteria, and the Executive Dashboard's movements** |
| **Not later** | **Every wave after this ships a screen that either omits people or renders their absence** |

**Wave 6 keeps the *screen*** — People Intelligence and Global Search's people group are UI, and they belong where the UI sequence puts them. **What moves is the domain.**

---

# 3 · Phases — six, each independently certifiable

**Deliberately small, and the first three need no provider, no ruling and no new module beyond the one ADR-0400 already approved.**

| | Phase | Delivers | Needs |
|---|---|---|---|
| **P1** | **`EntityKind.PERSON` and an anonymous `Person`** | The identifier the graph says is missing | **Nothing.** One enum member, one aggregate |
| **P2** | **`Affiliation` intervals from existing role changes** | *"A VP of Engineering left Acme in September"* as a **queryable interval**, not a passing event | P1 |
| **P3** | **Timeline projection** | Person events on the account timeline | P2 · ⚠️ **[TASK-901](../BACKLOG.md)** — `runtime-composition` reports **2 of 9** consumers wired, and a projection would land dark |
| **P4** | **`CommitteeRole` gains a stable id; seats cite an affiliation when one matches** | Committee stops being a template | P2 · **the trigger `committee.py` already wrote down** |
| **P5** | **Provider contract for person identity** | ❓1 answered | ⛔ **A commercial decision, not engineering** |
| **P6** | **Named people · `ForgetPerson` · retention** | The full capability | P5 · ⚠️ **[TASK-426](../BACKLOG.md) first** — erasure designed in is cheap, retrofitted is not |

> **P1–P4 are buildable today and deliver real customer-visible intelligence.** **P5 is a purchase. P6 is where personal data enters the repository for the first time** — and it should never precede TASK-426.

---

# 4 · Dependencies

| Kind | What |
|---|---|
| **Blocker** | **None for P1–P2.** This is the finding |
| **Sequencing** | **P3 after [TASK-901](../BACKLOG.md)** — otherwise the projection is dark. **P6 after [TASK-426](../BACKLOG.md)** — otherwise erasure is retrofitted |
| **Provider** | **P5 only.** *"Design around a provider-neutral domain"* is already satisfied by `ProviderPersonIdentity` and `IdentityState` |
| **Cross-module** | **`commercial_profile` adds one field at P4** — Lane B's, and the module wrote its own trigger |
| **Governance** | **A new bounded context is 🔴 and needs an ADR. [ADR-0400](adr/0400-person-as-an-entity.md) is that ADR and it is ratified** |

---

# 5 · Repository reuse

| | |
|---|---|
| ✅ **Reused wholesale** | `knowledge_graph` identity resolution, provenance, `IdentityState`, ambiguity · the claim/observation model · the business-event taxonomy · the signal catalog · `timeline`'s projection contract · `provider_platform`'s adapter port |
| 🟨 **Extended, minimally** | **`EntityKind`** — one member, the docstring reserves it · **`CommitteeRole`** — one id, at P4, on its own written trigger |
| ⛔ **Untouched** | **`workspace_tenancy`.** *"A `Member` is a customer's employee using Signora; a `Person` is somebody at a target account who has never heard of Signora"* — **pinned by a test asserting the two are not joinable.** **Better Auth remains the sole Authentication Authority** |
| ⛔ **Never duplicated** | **Influence, scoring, buying posture, commercial judgement.** *"A person is one plausible field away from becoming an influence model"* — **a structural test refuses the words**, as `test_boundary.py` already does for the committee |

---

# 6 · Governance impact — everything holds

| | Impact |
|---|---|
| **[ADR-0400](adr/0400-person-as-an-entity.md)** | ✅ **Unchanged and now load-bearing.** Its model is the plan |
| **[C-221](../LANE_COORDINATION.md)** | ✅ **Unchanged. Its narrowing *is* P1–P4** — role-based and organization-level intelligence, exactly as ruled |
| **[TASK-426](../BACKLOG.md)** | ✅ Unchanged, **and now has a named first consumer**: `person.forgotten`. **Sequence it before P6** |
| **Epic C** | 🟨 **Re-scoped, not re-opened.** P1–P4 are Epic C at C-221's narrowed scope |
| **Module ownership** | ✅ **Unchanged.** A `people` module would be a new row when P1 is scheduled; **nothing moves today** |
| **Queues** | ✅ **Untouched.** No task assigned, no lane's sequence altered |

---

# 7 · Customer-facing impact — what P1–P4 unblock

| Screen | Today | With P1–P4 |
|---|---|---|
| **Account 360** *(shipped)* | Contacts and org chart are ⬜ **stated absences** | **Affiliation history renders** — anonymous, and real |
| **AI Copilot** *(wave 2)* | Committee reasoning has no subject | **A seat can cite an affiliation** |
| **ICP Builder** *(wave 3)* | Four *Decision makers* criteria unbuildable | **Buildable at role level** |
| **Executive Dashboard** *(wave 4)* | *"Movements"* has no entity | **Movements are interval events** |
| **Signal Center** | `new_decision_maker` fires with **no subject** | **The signal names what changed** |
| **People Intelligence** *(wave 6)* | — | **The screen becomes possible.** Org chart and relationships still need P5 |

> **Two signals are live and scored today with no subject at all.** **P1–P2 give them one** — which ADR-0400 called *"the smallest change with the largest visible effect in the epic"*, and that judgement now has four more consumers behind it.

---

# 8 · What this document did not do

**Nothing implemented · nothing assigned · no migration · no ownership change · no queue touched · no new module created.** **`grep` proof: no `docs/coordination/` file differs.**

**The one thing it asks for is a ruling on placement** — **wave 6 → wave 2 for the domain, wave 6 retained for the screen.** **On approval, P1 becomes a backlog row at Epic and Capability level ([D-072](../DECISION_REGISTER.md)), and the owning lane writes the implementation package.**

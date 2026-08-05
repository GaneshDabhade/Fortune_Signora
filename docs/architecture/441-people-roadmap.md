# 441 · The People roadmap — four milestones, six stages, one sequencing principle

**Lane C · Product Office · 2026-08-05.** **[D-074](../DECISION_REGISTER.md) `APPROVED WITH REFINEMENT`.** This document is the roadmap the ruling asked for. **[440](440-people-roadmap-integration.md) is the evidence; this is the plan.**

> ## The refinement, and it changes the shape of the plan
>
> > *"Do not think about this as 'bringing People Intelligence earlier.' Instead, think about it as introducing the People **domain** before its first dependent customer-facing capability."*
>
> **The customer-facing module stays late. The domain does not.** **440 argued for one move; the ruling separated it into four things that move independently** — and three of the four keep their existing position.

---

# 1 · The four milestones — separate responsibilities, separate positions

**These are the ruling's own four names, and they are the vocabulary the repository uses from here.** *"The distinction should remain explicit throughout the repository."*

| | Milestone | | What it is | What it is **not** | Position |
|---|---|---|---|---|---|
| **M-D** | **People Domain** | 🟩 | **The entity and the interval.** An anonymous `Person`, an `Affiliation` with a start and an end | **Not a feature.** Nothing renders. No screen changes | ⬆️ **Moves — wave 6 → before wave 2** |
| **M-I** | **People Intelligence** | 🟦 | **What the domain lets other modules say** — a timeline event with a subject, a committee seat that cites a real affiliation, a signal that names what changed | **Not the screen.** Not influence, not scoring, not ranking | **Follows M-D.** Split by the provider gate — see §2 |
| **M-E** | **Provider Enrichment** | 🟩 | **A provider contract that supplies a person identifier**, and the named people that become possible once it does | **Not a prerequisite of M-D or of M-I's first stage.** An enhancement | **Unmoved.** A commercial trigger, not an engineering one |
| **M-U** | **People UI** | 🟦 | **The People Intelligence screen and Global Search's people group** | Not required by any of the above | **Unmoved — wave 6** |

> **The reason the four must stay separate is that they have four different triggers.** M-D's is a dependent capability. M-I's is M-D. M-E's is a signature. M-U's is the UI sequence. **Collapsing them into "Epic C" is what put a domain behind a screen in the first place.**

---

# 2 · The six stages — the sequence, in time

**Milestones are *what*. Stages are *when*, and they are the ruling's own six.**

| Stage | | Milestone | Delivers | Gate |
|---|---|---|---|---|
| **S1** | **Domain foundation** | **M-D** | **`EntityKind.PERSON` and an anonymous `Person` aggregate.** The identifier `knowledge_graph`'s docstring says is missing | **None.** This is the finding of [440](440-people-roadmap-integration.md) |
| **S2** | **Affiliation model** | **M-D** | **`Affiliation` — *person × company × title × interval*.** *"A VP of Engineering joined Acme in March and left in September"* becomes a queryable interval instead of a passing event | S1 |
| **S3** | **Anonymous role-based intelligence** | **M-I** | **Timeline projection · committee seats cite an affiliation · `new_decision_maker` gains a subject** | S2 · ⚠️ **[TASK-901](../BACKLOG.md)** — `runtime-composition` reports **2 of 9** consumers wired, and a projection would land dark |
| **S4** | **Provider-backed identity enrichment** | **M-E** | **A contract supplying `person_identifier`** · resolution through the existing `IdentityState` model · named people · `ForgetPerson` | ⛔ **A signature, not engineering** · ⚠️ **[TASK-426](../BACKLOG.md) first** — erasure designed in is cheap, retrofitted is not |
| **S5** | **People Intelligence capabilities** | **M-I** | **Org chart · relationship graph · champion tracking · executive movement by name** | S4 |
| **S6** | **Customer-facing People experiences** | **M-U** | **The People Intelligence screen · Global Search's people group** | S3 for the anonymous surface · S5 for the full one |

> ## ⚠️ M-I is deliberately split across the provider gate, and this is the point of separating the milestones
>
> **S3 is role-based intelligence — [C-221](../LANE_COORDINATION.md)'s approved scope exactly, and it needs no provider.** **S5 is named-person intelligence — C-221's *"future enhancement once supported by provider capabilities"*, and it needs S4.**
>
> **One milestone, two stages, a commercial decision between them.** **Reporting "People Intelligence" as a single date would hide that**, and it is precisely the thing the four-way split exists to make visible.

## What S1–S3 cost, measured

| | |
|---|---|
| **`EntityKind.PERSON`** | **One enum member.** The docstring already reserves it |
| **`Affiliation`** | **A new table — never a migration of an old one.** No `current_employer` field exists to unpick, because [ADR-0400](adr/0400-person-as-an-entity.md) prevented one from shipping |
| **`CommitteeRole` stable id** | **One field**, on the trigger `commercial_profile` wrote down itself: *"the first consumer that needs to cite a particular seat"* |
| **New bounded context** | **One — `people`.** 🔴, and **[ADR-0400](adr/0400-person-as-an-entity.md) is its ratified ADR** |

---

# 3 · The dependency graph

**[412 §3](412-backend-capability-matrix.md) draws the graph for the whole product; this is the People sub-graph it now contains.** **The edges run downward, and every one of them was already written down somewhere before today.**

```
                    ┌───────────────────────────────┐
                    │  M-D · People Domain          │  🟩  S1 · S2
                    │  Person (anonymous)           │      no provider, no ruling,
                    │  Affiliation (interval)       │      no blocker
                    └───────────────┬───────────────┘
                                    │
        ┌───────────────────┬───────┴────────┬────────────────────┐
        │                   │                │                    │
  timeline           commercial_profile  signal_engine      knowledge_graph
  projection         CommitteeRole id    subject for two    EntityKind.PERSON
        │            (own trigger)       live signals              │
        │                   │                │                    │
        └───────────────────┴───────┬────────┴────────────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │  M-I · S3 anonymous           │  🟦  needs TASK-901
                    └───────────────┬───────────────┘
                                    │
       ┌──────────────┬─────────────┼──────────────┬─────────────────┐
       │              │             │              │                 │
  Account 360    AI Copilot    ICP Builder   Executive Dash    Signal Center
  affiliation    committee     4 decision-   "movements"       a signal names
  history        reasoning     maker criteria                  its subject
  (wave 1 ✅)    (wave 2)      (wave 3)      (wave 4)
       ▲              ▲             ▲              ▲
       └──────────────┴─────────────┴──────────────┘
              FOUR DEPENDENTS, AND THE DOMAIN SAT BEHIND ALL OF THEM

                    ┌───────────────────────────────┐
                    │  M-E · Provider Enrichment    │  🟩  S4 — ⛔ a signature
                    │  person_identifier · naming   │      TASK-426 first
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │  M-I · S5 identified          │  🟦  org chart · relationships
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │  M-U · People UI              │  🟦  S6 — wave 6, unmoved
                    └───────────────────────────────┘
```

> **The graph's shape is the finding, again.** **Nothing above M-D's box is a blocker** — no ruling, no provider, no module that does not exist. **Everything below it is a consumer.** A domain with four consumers and zero blockers, scheduled last, is the pattern the principle in §5 exists to catch.

---

# 4 · The implementation sequence — where each milestone lands

| Wave | Screens | People work | Why here |
|---|---|---|---|
| **1** ✅ shipped | Account 360 | — | **Shipped with contacts and org chart as ⬜ stated absences.** The cost is already paid once |
| **1.5** ⬅️ **new** | *(none — no screen)* | ⬆️ **M-D · S1 · S2** | **Before its first dependent, which is the ruling.** **It is not wave 2** because a wave is a set of screens and **this contains none** — naming it wave 2 would put a domain and a screen in one bucket and re-merge exactly what the ruling separated |
| **2** | **AI Copilot** | **M-I · S3** *(partial — committee reasoning)* | ⚠️ **[TASK-202](../BACKLOG.md)'s own row already says *"phase 4 needs Epic C"***. **The dependent wrote its dependency down before this assessment existed** |
| **3** | Shell · Companies · Signal Center · **ICP Builder** · AI Research | **M-I · S3** *(the four *Decision makers* criteria)* | Role-level criteria are buildable the moment affiliations exist |
| **4** | Opportunity Intelligence · **Executive Dashboard** | **M-I · S3** *("movements")* | A movement **is** an interval event. There is no second model |
| **5** | CRM Integrations · Workflow Automation | — | Unchanged |
| **6** | **People Intelligence · Global Search** | **M-U · S6** | **Unmoved.** *"The customer-facing People Intelligence module may still remain later in the roadmap"* |
| **7** | Reports | — | Unchanged |
| **⏸ out of wave** | — | **M-E · S4 → M-I · S5** | ⛔ **Triggered by a contract, not by a wave.** It joins the sequence wherever the signature lands |

> **Only one row moved.** **Four waves keep their screens, their order and their contents** — what changed is that the thing four of them quietly needed now arrives before the first of them, instead of after the last.

---

# 5 · The sequencing principle — stated, and checkable

> ## **P-01 · Domain precedence**
>
> **A foundational domain is introduced before *multiple* customer-facing capabilities begin building temporary representations of that same concept.**
>
> *(The product owner's rule, [D-074](../DECISION_REGISTER.md), verbatim in substance. It binds Product Office roadmap sequencing.)*

**A principle with no check is a comment**, so here is the check.

| | |
|---|---|
| **What counts as a temporary representation** | **A stated absence** *(a ⬜ section, an empty state that explains why it is empty)* · **a placeholder** · **a locally-shaped copy of the concept inside one screen's own module** |
| **The threshold is two, and deliberately** | **One screen shipping an absence is a scope decision** — [414](414-wave-1-account-360.md) made one openly and correctly. **Two or more is a sequencing defect**, because the second one is where rework begins |
| **Where it is checked** | **[412](412-backend-capability-matrix.md) §2's `Screens` column against §4's wave order.** When a concept appears in the `Screens` column for **two or more screens in waves earlier than the wave that builds it**, the domain is late |
| **When it is checked** | **Whenever a wave plan is written or amended** — which is the moment it is cheap, and the only moment it is |
| **The worked example** | **People.** Four dependent screens across waves 1–4; the domain at wave 6. **Account 360 shipped the first absence; the principle exists so the second one is caught before it ships** |

> **This was not knowable from the backend.** **[439 §4](439-people-intelligence-reassessment.md) measured the cost of waiting correctly and completely — one enum member, one field, a new table rather than a migration — and reached *"build nothing"*.** **What it never measured was wave order**, and the cost of arriving late is not paid in the domain. **It is paid in every screen that shipped around the gap.**
>
> **That is the whole content of P-01: a domain's cost of delay is not measured in the domain.**

---

# 6 · What the ruling explicitly preserved — each one, answered

**The ruling names eight things that must continue to hold. Every one is checked here rather than asserted.**

| | Holds because |
|---|---|
| **Repository Reuse Policy** | ✅ **§7's audit.** Six modules already run this intelligence and not one knows a person's name. **M-D adds an entity; it adds no pipeline** |
| **Existing module boundaries** | ✅ **Not one moves.** `people` is a **new** context, ratified in [ADR-0400](adr/0400-person-as-an-entity.md), and `modules.toml` gains a row **only when M-D is placed** — not today |
| **Provider neutrality** | ✅ **`ProviderPersonIdentity` is the provider-neutral shape and `IdentityState` already models *resolved · ambiguous · unresolved*.** **The mapper rule is untouched**: *"each mapper reads only its own vendor's shape"* |
| **The domain must not depend on provider availability** | ✅ **This is the structural point of the M-D / M-E split.** **S1–S3 name no provider at all.** M-E is an enhancement with its own row and its own trigger — *"provider enrichment is an enhancement; the domain itself is a product concept"* |
| **Better Auth ownership** | ✅ **Untouched.** `workspace_tenancy` is not extended, not joined and not read. *"A `Member` is a customer's employee using Signora; a `Person` is somebody at a target account who has never heard of Signora"* — **pinned by a test asserting the two are not joinable.** **Better Auth remains the sole Authentication Authority** |
| **Buying Score ownership** | ✅ **Influence, ranking and commercial judgement stay in `buying_score_engine`.** ADR-0400 names the failure mode — *"a person is one plausible field away from becoming an influence model"* — and **M-D ships no `seniority_score`, no `is_key_contact`, no `priority` and no ordered list** |
| **Affiliation model** | ✅ **Unchanged, and now load-bearing.** *"'Priya left Acme' is not a mutation of Priya — it is an interval closing"* |
| **No speculative implementation** | ✅ **S1–S3 are derived entirely from data that already flows in production** — `RoleChangeValue(title, seniority, direction)` + `occurred_on` + company. **S4–S6 are not prepared further** |
| **No duplicate concepts** | ✅ **A movement, a transition and a history are one query over one interval.** The alternative — four screens each shaping their own — **is the duplication this ruling prevents** |
| **Do not reopen settled decisions** | ✅ **[ADR-0400](adr/0400-person-as-an-entity.md) unchanged · [C-221](../LANE_COORDINATION.md) unchanged · [439](439-people-intelligence-reassessment.md) unchanged.** **439's conclusion is not reversed — it is completed.** Its measurement stands; a second measurement it never took now sits beside it |

---

# 7 · Backlog rows created

**Four rows, one per milestone, all `SEQUENCED` with a named trigger** — *"do not assign implementation immediately… make it part of the planned execution sequence so implementation begins at the correct time."*

| Row | Milestone | Trigger |
|---|---|---|
| **[TASK-427](../BACKLOG.md)** | **M-D · People Domain** | **The first dependent customer-facing capability enters implementation.** ⚠️ **Measured 2026-08-05: fired** — [TASK-202](../BACKLOG.md) is `READY` and names Epic C in its own phase 4 |
| **[TASK-428](../BACKLOG.md)** | **M-I · People Intelligence** | **TASK-427 promoted.** S5 additionally on TASK-429 |
| **[TASK-429](../BACKLOG.md)** | **M-E · Provider Enrichment** | **A provider contract supplying a person identifier.** [TASK-426](../BACKLOG.md) before named people land |
| **[TASK-430](../BACKLOG.md)** | **M-U · People UI** | **Wave 6, unchanged** |

**[TASK-201](../BACKLOG.md) is decomposed, not replaced.** It remains Epic C's row, at its existing position, with its existing assignment — **position is priority and priority is the product owner's, and Lane C changed neither.**

---

# 8 · What this document did not do

**Nothing implemented · nothing assigned · no migration · no module created · no ownership change · no queue file touched · no task's position changed.**

**One thing is left, and it is small:** **TASK-427's trigger has fired**, so the only remaining act is **the product owner moving it to `READY` and placing it** — which is a priority decision, and Lane C does not take those.

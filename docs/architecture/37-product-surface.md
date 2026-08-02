# 37 — The Product Surface: making nine stages of pipeline reachable

> Written 2026-07-31, at the product owner's direction to move from platform engineering to product implementation. This document is the design for **M12**, brought forward ahead of M11 and M7 — a Category 1 roadmap change ([IMPLEMENTATION_ROADMAP.md §5c](../../IMPLEMENTATION_ROADMAP.md)), and the product owner's to make.

## The finding, stated plainly

Signora has thirteen modules, 1825 tests, a certified platform, and a complete intelligence pipeline that turns a provider payload into a defensible commercial conclusion.

**A customer can sign in, create a workspace, invite a colleague, and look at three empty-state cards.** That is the entire product surface.

| Layer | Built |
|---|---|
| HTTP routers | **one** — `workspace_tenancy` (5 endpoints) |
| Frontend pages | **three** — overview (empty states), sign-in, settings |
| Endpoints exposing a company, observation, business event, signal, score, opportunity, narration, decision package, or research finding | **zero** |

Everything the pipeline computes lands in a table and an event, and **no HTTP path reaches any of it.**

This was predicted. [31-m10-design-review-evidence.md](31-m10-design-review-evidence.md) recorded a dissent that has now come true:

> *"The pipeline runs **nine stages ahead of any user-visible surface** — the Decision Package is produced, stored and announced, and no human can see it until M12. M10 adds the most expensive, slowest, least deterministic capability in the system to a pipeline whose output nobody can read."*

And [PRODUCT_ROADMAP.md](../../PRODUCT_ROADMAP.md) states that business screens *"arrive from M2 onward rather than being sketched earlier."* **They did not arrive.** The claim is false about the present and is corrected by this document rather than left standing.

## What this means for the work

**The read paths already exist.** Every module publishes a workspace-scoped query class through its application layer — `GraphQueries`, `ObservationQueries`, `BusinessEventQueries`, `SignalQueries`, `BuyingScoreQueries`, `OpportunityQueries` — and M8 and M10 already consume `OpportunityQueries.explanation()` in production code.

So the missing layer is narrow and specific: **each module's `interface/` layer, and the frontend.** Not new domain logic, not new persistence, not new platform abstractions. `workspace_tenancy/interface/router.py` is the pattern to copy, and it is 5 endpoints long.

That is the single most important estimate in this document, and it is evidence rather than optimism.

---

## 1 · Customer journeys

Six, in the order a salesperson actually encounters them. Everything else in the product exists to serve these.

### J1 — *"Which accounts deserve my attention today?"*
Opens Signora. Sees accounts ranked by buying score, each with its **why now** and how fresh the evidence is. Filters to what is assigned to them. **This is the daily habit; if it is not good, nothing else gets used.**

### J2 — *"Why this account?"*
Opens one. Sees the score and what contributed to it, the business events underneath, the grounded explanation in plain language, and the Decision Package's answers. **Every claim carries its citation.**

### J3 — *"Prove it."*
Clicks a citation. Sees the underlying fact — the event, its date, which providers reported it, whether they corroborated each other. **This is Signora's actual differentiator**: not that an AI said something, but that a human can follow every claim to a record and check it. No competitor's summary survives this click.

### J4 — *"I'm working this one."*
Assigns it, moves its stage, or dismisses it with a reason. The list reflects the decision tomorrow.

### J5 — *"Go find out more."*
Requests research on an account, sees it running, reads the brief when it lands, and can tell which parts were computed and which were narrated.

### J6 — *"What changed?"*
Sees the account's history as a sequence — score movements, new events, research runs. **Owned by M7 (Timeline), which is a queued milestone and not duplicated here.**

---

## 2 · Missing product capabilities

| Capability | Serves | Exists today |
|---|---|---|
| Account list, ranked and filterable | J1 | rows only |
| Account brief — score, contributions, events, explanation, package | J2 | rows only |
| Evidence resolution — citation → fact | J3 | **nothing at all** |
| Stage transitions and assignment over HTTP | J4 | domain only |
| Research dispatch, status, result | J5 | use case only, no entry point |
| Account history | J6 | **M7 owns this** |
| Search, comparison, saved views | — | deferred, see §3 |

---

## 3 · Priority, and two things deliberately *not* first

**Order: J1 → J2 → J3 → J4 → J5.**

The requested capability list led with *Research Management, Research History, Search, Comparison*. I am recommending against all four for the first milestone, on repository evidence:

**Research is the thinnest ice in the building.** `research_synthesis@2` earned its release yesterday, against **one local 8B model**, on **two structurally identical cases**, at **~54 s per task**. Leading the product with it would put the least-proven, slowest, least-deterministic capability in front of a customer first. It arrives in **M12.4**, after the surface that makes it legible exists.

**Search and comparison are premature.** Search is worth building when a customer has more accounts than a list can show; the golden set currently has *two*, and [28-ai-platform.md](28-ai-platform.md) already records "variety 1" as the main caveat on M8's evidence. Comparison is a feature of a mature list. Both are **evidence-triggered**, not scheduled — the trigger is a design partner with enough accounts to need them.

**What earns first place instead:** M6 was labelled *"first sellable moment"* and remains the most mature, most deterministic, most defensible thing in the system. It is also the only capability a salesperson would open **daily**.

---

## 4 · Dependencies

```
J1 account list ──► J2 account brief ──► J3 evidence ──► J4 working the list
                                    └──► J5 research on demand
```

- **J2 depends on J1** only for navigation; both read existing tables.
- **J3 depends on J2** — a citation needs somewhere to be clicked from.
- **J5 depends on J2** — a brief with no account page to live on is a JSON blob.
- **Nothing depends on M11 (Recommendation)**, which is why it can wait. The pipeline already answers *why now*; *what to do* is a further AI capability that would land on a surface that does not yet exist.
- **External dependencies: none.** No cloud, no CRM, no new vendor. The Provider Simulation Framework supplies data.

---

## 5 · Backend work

Per module, `interface/` only. **No domain change, no application change, no new module.**

| Module | Endpoints |
|---|---|
| `opportunity_engine` | list opportunities (cursor, filters) · get one · get explanation · transition stage · assign |
| `buying_score_engine` | score with contributions for an entity |
| `business_event_engine` | events for an entity |
| `signal_engine` | signals for an entity, including preserved dissent |
| `knowledge_graph` | entity summary — the "company" a customer names |
| `ai_platform` | latest narration for a subject |
| `ai_reasoning_engine` | latest decision package |
| `ai_research_engine` | request research · task status · latest findings and brief |

Each follows the shipped pattern exactly: handler translates, authorizes, delegates immediately; Casbin dependency with `workspace_id` in the tuple; RLS context established before any query; **404 not 403** for a non-member.

**One genuinely new backend capability**, and only one: **research dispatch**. `Research.run()` exists but nothing invokes it outside a test. It needs an ARQ job and an endpoint that accepts and returns immediately — §7 forbids an API handler blocking on pipeline work, and at ~54 s per task that rule is doing real work here.

---

## 6 · Frontend work

**Composed from the frozen foundation** (§20c) — `components/ui`, the app shell, the query layer, design tokens. Building a page must not modify a shared component.

| Page | Journey |
|---|---|
| `/accounts` | J1 — ranked list, filters, assignment |
| `/accounts/[id]` | J2 — score, contributions, events, explanation, package |
| Evidence drawer | J3 — citation → fact, opened from any cited statement |
| Stage / assign controls | J4 |
| Research panel | J5 — request, running state, brief |

**The one component the library lacks is the citation.** A cited statement is Signora's signature interaction and appears in narration, decision package and research brief alike. It belongs in `components/ui` with its tokens and its test — *added to the library, never around it.*

**Client-side permission checks stay presentational.** Casbin on the server is the decision; hiding a control is a courtesy.

---

## 7 · API changes

**No new conventions.** [19-api-conventions.md](19-api-conventions.md) is already ratified and unused by twelve modules: single error envelope with stable `code` and `correlation_id`, cursor pagination on every collection, purpose-built response schemas — never a domain entity or SQLAlchemy model returned directly.

**The one design decision worth recording: the account brief is composed in the frontend, not by a backend aggregator.**

A brief spans opportunity, score, signals, events, narration, package and research. §7 says an endpoint belongs to exactly one module. Three options were considered:

| | Approach | Verdict |
|---|---|---|
| **A** | Several endpoints, composed by the frontend query layer | **Chosen.** Boundaries stay honest, no new abstraction, and the query layer built in M1.5 is exactly the tool for it |
| **B** | A BFF / aggregation service | Rejected **for now**. It is a new platform concept, and the direction is explicit: no platform abstractions until product work proves them necessary. **Trigger to revisit:** measured round-trip latency on the account page, not intuition (§14) |
| **C** | One module's router aggregating the others | Rejected. It makes `opportunity_engine` the owner of every other module's presentation |

---

## 8 · Data model changes

**None for J1–J4.** Every field these journeys need is already stored, and pretending otherwise would be the speculative schema §6 forbids.

**J5 needs no new table either** — `research_task`, `research_finding` and `research_synthesis` shipped in migration `0018`. It needs a *job*, not a column.

The first honest candidate for a schema change is a **dismissal reason** on an opportunity transition (J4), and only if the Opportunity Engine's existing state model cannot carry it. That is checked during M12.3, not assumed now.

---

## 9 · Milestones

M12 was already *"Revenue Intelligence Platform + business UI"*. It is brought forward and split into shippable slices — IDs stay stable, per the roadmap's own rule.

| Slice | Delivers | Size |
|---|---|---|
| **M12.1** | **The list.** `/accounts` ranked by score with why-now; opportunity + score endpoints; the citation component | 3–4 ew |
| **M12.2** | **Names, then the brief.** *(Re-ordered 2026-07-31 on M12.1's evidence — see below.)* A Knowledge Graph read endpoint so accounts are named, then `/accounts/[id]` with contributions, events, signals, explanation, decision package | 4–5 ew |
| **M12.3** | **Evidence and action.** Citation → fact resolution; stage transitions and assignment | 3–4 ew |
| **M12.4** | **Research on demand.** Dispatch endpoint, ARQ job, status, brief on the account page | 3–4 ew |

**M12.1 is the one that changes the product's nature**: after it, Signora is something a person opens rather than a pipeline that runs.

---

## 10 · Definition of Done, per epic

Every slice inherits the Milestone Definition of Done (CLAUDE.md §19) and adds:

**M12.1 — The list**
- A customer signs in and sees their workspace's accounts ranked by buying score, each showing its trigger and evidence age.
- Cursor pagination; a workspace with no accounts shows the shipped empty state, not a spinner.
- A non-member requesting the workspace gets **404**.
- Frontend composes from `components/ui`; **zero mock business data** (`no-mock-data.test.tsx` still passes).
- Certification re-run and recorded.

**M12.2 — The brief**
- Every number on the page traces to a stored row; no figure is computed in the browser.
- The narration and decision package render with their citations intact and their **provenance visible** — which prompt, which model, when.
- An account with no AI artifact renders a designed empty state rather than a broken panel.

**M12.3 — Evidence and action**
- **Every citation in every AI artifact resolves to a fact the customer can read.** A citation that cannot resolve is a visible error, never a silent omission — the product-surface form of the grounding guarantee.
- A stage transition records its actor; the list reflects it on next load.
- A stage transition a caller is not permitted is refused server-side, and the test proves the client-side hide is not the only check.

**M12.4 — Research on demand**
- Requesting research returns immediately; **no API handler blocks on a model call.**
- The brief renders with findings distinguished from narration — a customer can tell which was computed and which was written.
- Requesting research for an account that already has a running task does not start a second one.
- The ~54 s task duration is honestly represented in the UI rather than hidden behind a spinner that implies seconds.

---

## What this document deliberately does not propose

**No new platform capability.** Not a BFF, not a cache, not a search index, not a new event type. If product work proves one necessary, that is a finding to raise with the measurement that proved it.

**No new AI capability.** M11 (Recommendation) stays queued. The pipeline already produces more intelligence than a customer can currently see, and adding a tenth stage ahead of the surface would repeat exactly the mistake this document exists to correct.


---

## Re-ordering inside M12.2 — recorded 2026-07-31

M12.1 shipped and produced evidence that changes the order of its successor.

**The attention list names each account by a truncated identifier.** No module in the ratified dependency graph reaches both workflow and entity names — `Opportunity Engine → Buying Score Engine` only, and `Revenue Intelligence Platform` never reaches the Knowledge Graph. So the row reads `6b8efd21` where a company name belongs, and **a seller cannot triage a list of identifiers.**

**Entity names therefore ship before the brief.** The reasoning:

- It is **smaller** — one Knowledge Graph read endpoint plus a frontend join, against a page composing seven sources.
- It **converts an existing screen from a proof into a tool**, so the value lands weeks earlier than the brief's would.
- It **de-risks the brief**, which needs the same endpoint anyway: building it first means the brief composes a proven read rather than two new ones at once.
- A placeholder name was never an option — it would be mock business data, which teaches a reader the wrong model and which `no-mock-data.test.tsx` forbids.

**This does not change M12.2's scope**, only the order inside it. Recorded as **D2** in [38-product-design-principles.md](38-product-design-principles.md).


---

## Roadmap review — 2026-07-31: M11 deferred, not cancelled

Asked whether the Recommendation Engine should remain the next milestone. **It should not**, and the decisive argument is not product preference — it is that **M11's own upstream dependency does not currently work.**

### The evidence

`Recommendation Engine → AI Reasoning Engine` is the ratified edge (05-module-dependencies.md). **`reasoning@1` has no released model**: `granite3.3:2b` refuses under rendering protocol 2 and `llama3.1:8b` is UNMEASURABLE on the evaluation hardware. The Decision Package stage would refuse in production today.

Building M11 now would layer a new AI module on top of a stage that cannot run, to produce recommendations that would surface on a product with **one screen**. Three ways of being premature at once.

### The product argument, stated without architecture

A recommendation answers *"what should I do about this account?"* That question only becomes the user's next question once they can already answer *"which accounts?"* and *"why this one?"* — J1 is shipped, **J2 and J3 are not**. A seller shown a recommended action for an account they cannot yet inspect is being asked to trust a conclusion whose evidence the product does not display. That is the opposite of what Signora sells.

**The differentiator is not that Signora recommends. It is that a human can follow every claim to a record and check it.** Shipping recommendations before the evidence surface would ship the commodity half first.

### Decision

**M11 is deferred, not cancelled.** It remains a ratified module in 04-modules.md and a node in the dependency graph; nothing about it is withdrawn. It is removed from the *next* position and re-queued after M12.

### Trigger to resume — stated in product terms

M11 resumes when **both** hold:

1. **`reasoning@1` holds a current release.** Its output is M11's only input; a recommendation derived from a stage that cannot run is not deferred work, it is impossible work.
2. **A design partner, using the account brief, asks *"so what do I do?"*** — that is, feedback shows the gap has moved from *what is true* to *what to do*. Until someone says it, a recommendation is a feature we imagined rather than one anyone asked for.

Deliberately **not** an engineering trigger. "When M12 is finished" would resume M11 on a schedule rather than on evidence, and the whole point of the deferral is that M11's value depends on a product state, not on a date.

---

## M12.2 — what building it revealed before a line was written

**An account has no name.** `Entity` is an identity and carries no attribute values, by explicit design:

> *"a `name` column here would be truth-resolution in miniature, and it would immediately disagree with the claims underneath it."*

A company's name is `LEGAL_NAME` — **a claim, from a provider, at a time**, and two providers may assert different ones. `ClaimSet.agrees()` exists precisely to report that.

So the instruction *"do not think entity endpoint, think Account Identity"* is more right than it looks. **Naming an account is a truth-resolution decision the Knowledge Graph deliberately refused to make**, and the identity layer is where it now has to be made — once, visibly, and with the disagreement preserved rather than hidden.

### The design that follows

**Resolve at read time; never store.** The same discipline `evidence_state` uses in M6: a stored display name would be a cached derivation that eventually contradicts the claims beneath it, which is the exact failure `Entity` was shaped to avoid.

**Surface disagreement rather than resolving it away.** When providers agree, show the name. When they do not, show the chosen name *and say so* — a quiet marker that opens the provider-by-provider view. This is J3 ("prove it") applied to the most ordinary field on the screen, and it is free: `ClaimSet` already computes it.

**A stated, tested selection rule.** The recommendation is **most recently observed claim wins**, because a company that renamed should display its new name, and recency is the only ordering the claim record supports without inventing provider trust rankings.

> **Corrected 2026-08-01.** This paragraph originally continued: *"Provider precedence is a **customer** policy — the same category as the scoring model and the opportunity policy"*, and flagged a future policy artifact letting a customer prefer one provider over another.
>
> **That is now ruled wrong.** Provider quality and conflict resolution are Signora's responsibility, not the customer's ([04-modules.md](04-modules.md), Provider Platform). A customer cannot sensibly rank suppliers they were never told about, and asking them to would hand Signora's core competence back across the table. **Recency is not a default awaiting a customer's ruling — it is Signora's stated resolution rule**, and improving it is Signora's job.
>
> The customer-facing half survives unchanged and is the part that mattered: **disagreement is shown, never hidden.** A customer sees *that* sources disagreed and which ones, as evidence. What they do not get is a dial.

---

## M12.2 — the brief, as built (2026-07-31)

Names shipped first, then the brief's spine. Both slices ran the shape §5 predicted: **`interface/` only — no domain change, no application change, no new module.**

### The first slice of the brief

`GET /workspaces/{workspace_id}/accounts/{account_id}/score` and `/opportunities/[accountId]` — the score, how it was reached, and every line that produced it. Detailed in [26-buying-score-engine.md](26-buying-score-engine.md).

**This is the point at which Signora stops being rankable and starts being arguable.** A ranked list is something any tool can produce; a number a customer can take apart line by line and reproduce with a division is the thing §1's J3 promised, arriving one journey earlier than expected because the ledger was already there to expose.

**Option A held.** The page composes two requests — the name from the Knowledge Graph, the score from the Buying Score Engine — exactly as this document chose over a BFF. No aggregation service, no new platform concept, and no measured latency problem yet to justify revisiting it.

### Two decisions the screen forced

**The route is `/opportunities/[accountId]`, with the segment named.** The parameter is an *account* identifier under a section called Opportunities. Naming the segment puts that fact in the URL rather than in a comment somebody has to find; the section keeps its name because a seller works a list of opportunities, and the brief is about the company one of them is on.

**Only the account name opens the brief, not the whole row.** A card-wide link would have to *contain* the disputed-name disclosure — a control inside a link is invalid, activates the wrong thing on touch, and lands in the wrong place in the keyboard order. The alternative, an absolutely-positioned overlay with the button raised above it, trades a real structural problem for a stacking-order one that breaks silently. The row's card hover was removed with the link: a card that lit up under the cursor anywhere would teach a reader the whole row is clickable and then fail them everywhere but one word.

### What the brief does not have yet, and says nothing about

The business events and observations beneath each line (J3, M12.3), the AI narration and Decision Package (M12.2's remaining scope), stage transitions and assignment (J4, M12.3), and research (J5, M12.4).

**Nothing on the page hints at any of them.** A control that looks clickable and is not costs more trust than the missing feature does — which is the same rule that put `signal_id` and `business_event_id` on the wire without rendering them as links.

---

## M12.3 — evidence and action, as built *(2026-08-01)*

Three slices, in the order §3 set: **what to check** → **the citation that opens** → **the decision that gets recorded**.

### J3 is closed

*"Clicks a citation. Sees the underlying fact — the event, its date, which providers reported it, whether they corroborated each other."* Every ledger line now resolves to a `business_event` record with its provider readings. **Narration citations do not yet open** — `signal_contribution`, `buying_score` and `opportunity` need resolvers, which is M12.4.

### J4 is closed, and it was the first write

*"Assigns it, moves its stage, or dismisses it with a reason. The list reflects the decision tomorrow."* All three, and the list reflects it on the next load rather than tomorrow.

**§5 predicted `interface/` only, and that held for the third time** — no domain change, no new module, no new persistence. One application-layer change was required and it was a question this milestone had been explicitly handed: whether a closed opportunity keeps its brief. It does.

### The Definition of Done in §10, checked

| | |
|---|---|
| Every citation in every **AI artifact** resolves | **Partly.** Every *ledger* citation resolves; narration's do not. Stated rather than claimed |
| A citation that cannot resolve is a visible error | ✅ The drawer says so and does not fail silently |
| A stage transition records its actor; the list reflects it | ✅ From the verified principal, never the body |
| A transition a caller is not permitted is refused server-side, and the test proves the client-side hide is not the only check | ✅ — **though not in the sense the line was written.** See below |

**What the last line actually proves, stated precisely.** Both workspace roles may work accounts, so there is no role whose transition is refused; a product where a member could not dismiss an account would be unusable. The client-side hide that *is* enforced independently is **which transitions are legal from the current stage** — the brief offers exactly `allowed_next`, and the server refuses everything else with the domain's own explanation. Reopening a won deal, skipping to `closed_won`, and a change that changes nothing are each asserted over the real HTTP path.

### What M12.3 has left

**The list.** R1-01, R1-02, R1-05, D20/R1-07 and now R4-04 are one coherent slice about *which* account you pick — the only part of the milestone still open.

---

## PS-01 — the brief stops rendering two different states as nothing *(2026-08-02)*

**TASK-002.** R2-03 as scoped, and R1-04 with it — they turned out to be one change, and the reason is worth recording because it is the kind of thing that is obvious once and never again.

### The two findings are one fact arriving twice

An account carries **two** independent statements about how its intelligence is holding up, and the brief was reading only one of them:

| | Owned by | Answers | On the brief before this slice |
|---|---|---|---|
| `is_current` · `valid_until` | the buying score | *is this reading inside its stated validity?* | rendered — *"exactly correct until Sep 20, 2026"* |
| `evidence` — `current` · `cooling` · `stale` | the opportunity | *how is this reading holding up against what somebody committed to?* | **on the wire, and ignored** |

Both are true, they answer different questions, and **no reader will ever reconstruct that.** The list showed *Cooling* on Adobe and HubSpot; the brief said the reading was exactly correct; a sales manager read both and concluded *"the list is noisy"* (R1-04). Separately, the *Before you act* section vanished on the one account holding nothing live, and a RevOps reader could not tell an empty answer from a failed request (R2-03).

**R2-03 cannot be answered without the brief learning the same fact R1-04 says it should be showing** — *"nothing is current"* is only actionable when the page can say **why**. One path, read by both.

### What changed

- **The brief renders `EvidenceHealth`** — *the attention list's own component*, beside the momentum line, so *"opened at 50, −15 since"* and *Cooling* sit together. **Not a second phrasing**: two wordings for one fact is how a customer catches a product contradicting itself, and this one already had. It stays silent on `current`, because *"everything is fine"* is noise that trains people to stop reading badges.
- **`ValidationBlock` answers three states rather than one** — *what to check*, *nothing is current*, *this did not load* — and they are told apart by what they say rather than by whether they appear.

### The rule this slice corrected, and its boundary

The section returned `null` on an empty list, on the reasoning that governs narration: **a panel announcing a gap is worse than the gap.** That reasoning is still right, and it was wrong here.

> **A narration that does not exist is Signora having nothing to add. Nothing *live* is not nothing to say.** On a page whose subject is an open commitment it means the commitment is running ahead of its evidence — the most actionable sentence on the screen.

**The test for which rule applies:** if absence and presence carry the same information, render nothing; if the absence *is* the finding, say it. And **absence can never distinguish itself from failure**, which is why the third state had to become copy rather than a missing section.

### What it deliberately does not do

- **It guesses at no cause it was not given.** Only `stale` produces a *why*, because only `stale` means the score is past its validity or absent. On `cooling` or `current` the empty sentence says what it knows and stops — a link between a falling score and an empty answer would be exactly the inference this surface exists not to make.
- **It says nothing about evidence on an account nobody has taken on.** There is no commitment for the reading to be held up against, and a badge there would be a state the product never computed.
- **It does not touch narration.** Narration has the same silent-absence shape and it is a *different* question — *not narrated* versus *narrated against evidence that no longer resolves* — which is [B-010](../BUGS.md) and TASK-004, and belongs to whoever takes that.

### Why the regression test is page-level

**For the third time, and the reason is the same each time** (D36, [B-006](../BUGS.md)). `EvidenceHealth` was never broken — it has rendered *Cooling* correctly on the list since M12.2 and its own tests passed throughout. **The defect was that the brief never called it.** Two screens disagreeing is the one failure a component test structurally cannot see, because neither component is wrong.

`frontend/tests/components/brief.test.tsx`. Six of its nine assertions were confirmed failing against the pre-slice page before the fix was trusted.


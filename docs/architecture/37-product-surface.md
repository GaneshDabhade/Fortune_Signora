# 37 — The Product Surface: making nine stages of pipeline reachable

> Written 2026-07-31, at the product owner's direction to move from platform engineering to product implementation. This document is the design for **M12**, brought forward ahead of M11 and M7 — a Category 1 roadmap change ([IMPLEMENTATION_ROADMAP.md §5c](../../IMPLEMENTATION_ROADMAP.md)), and the product owner's to make.
>
> ⚠️ **Its two halves aged differently, and the distinction matters (2026-08-04).** **The backend design shipped and is true** — this document is why 46 endpoints across 12 routers exist, and its central claim, *"the missing layer is each module's `interface/` layer and the frontend"*, is still the correct diagnosis; [412](412-backend-capability-matrix.md) finds two modules still in exactly that state. **Its UI half is superseded** by the [Fortune Signora Design Project](410-approved-ui-specification.md), which is now authoritative for frontend behaviour.

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

---

## PS-02 — three narration states that were one blank space *(2026-08-02)*

**TASK-004**, the lane's half of [B-010](../BUGS.md). The `RUNNING.md` half is QE's and is separate.

### The rule PS-01 established, applied to the section PS-01 deliberately left alone

PS-01 ended by saying narration was *a different question*, and it was — but it is the same **shape**, and the answer turns out to be the same:

> **Absence can never distinguish itself from failure.**

`NarrativeBlock` returned `null` when there was no narration, on stated reasoning: *"a box saying no narration yet would advertise a gap rather than fill one, and would appear on every account until a worker had caught up."*

**The reasoning was sound and the outcome was not.** A reviewer opened twelve briefs, found no explanation on any of them, and could not tell whether the feature was broken or simply had nothing to say. **It was broken** — a re-seed had orphaned all 748 narrations, and the screen said exactly as much about that as it says about a healthy quiet account: nothing.

**The objection was right about volume and wrong about silence.** So the empty state is one line of muted text under the existing heading, never an illustrated `EmptyState`: this is one section of a page that has already answered the reader's question, not a screen whose whole subject is missing.

| State | Before | Now |
|---|---|---|
| No narration written (`404`) | nothing | *"Signora has not written one for this account yet."* **An answer, and worded so it does not read as a fault** |
| The request failed | nothing | *"Signora could not load the explanation…"* — the page's own wording for a fault |
| Still loading | nothing | nothing. **Announcing either during the first paint is a confident wrong answer** |

### The defect reading the component revealed

**The one condition that strands a reader**, and it was invisible from either end:

When a narration's evidence can no longer be re-derived, every citation correctly degrades from a button to a plain count — *a citation drawn as clickable and going nowhere costs more trust than the missing feature does*. **But the sentence explaining why lived only inside the dialog that citation opens.** So in exactly the case where the explanation was needed, **there was no longer any control that could reach it.**

The fix is not to duplicate the sentence. It moves onto the panel **only when nothing resolves**, and stays in the dialog the rest of the time: **one explanation, placed wherever the reader can actually reach it.** A reader who *has* opened a citation is checking something, and that remains the better moment for it.

### What it deliberately does not do

- **It deletes nothing.** A materialized AI artifact is a historical fact and is immutable (§2). An orphaned narration correctly survives and correctly stops resolving; the residue is a seeding question, not a retention one.
- **It does not rewrite a dated narration.** The sentences still render in full — *"false means these sentences are dated, not wrong"* — because a narration is never edited to catch up with its account.
- **It says nothing about when one will appear.** The brief does not know, and a promise the repository cannot keep is the failure D39 names.

---

## Team — Implementation Waiting, declared 2026-08-02

**The customer-facing surface over `workspace_tenancy`.** Selected by the module-review methodology rather than from a queue: `GET /workspaces/{id}/members` was built, authorized and tested with **no caller**, `queryKeys.members` was declared with no use, and `Membership` was declared in `lib/api/types.ts` with no consumer. **Three declared contracts, none exercised.**

### Completed

| | |
|---|---|
| **TS-02** | The shell resolves the signed-in person's real role instead of hardcoding `owner`. A `TODO(M2.1)` had claimed this needed a `GET /workspaces/{id}/me`; **it did not** — `Membership` already carried `user_id` and `role`, and the session already carried the user's id |

### Suspended

| | Blocked on | Resume trigger |
|---|---|---|
| **TS-01** — the Team page | **[C-024](../LANE_COORDINATION.md)** — nothing in the product can render a person's name | A repository-wide identity-resolution approach is accepted |

**The blocker is not this page's.** `MembershipResponse` returns `user_id` and cannot return a name, correctly: Better Auth is the sole Authentication Authority and the Python tier only verifies ([ADR-0026](adr/0026-jwt-boundary-architecture.md)). **The same question appears in Timeline, comments, audit history, AI attribution, notifications, mentions and assignments** — so answering it inside the Team page would decide it for all of them by accident. §What this document deliberately does not propose already forbids the shortcut: *"not a BFF"*.

### Remaining implementation work, once C-024 lands

**The Team page itself**, in the customer's vocabulary — who belongs, each person's role, who owns the organization, and where collaboration begins. Everything but the names is already reachable.

**Deliberately unplanned: invitations.** `POST /workspaces/{id}/members` adds a member directly rather than inviting one, and [R11-01](39-product-review-findings.md) calls the existing capability *"a weaker capability wearing the name"*. **Whether a customer-facing invitation flow is in scope is a product question, not a reading of the architecture.**

---

## PS-03 — the brief says who put this account in front of you *(2026-08-02)*

**R1-06.** *"Signora is tracking this · nobody has taken it yet"*, identical on all twelve briefs — *"true, and after the first account it is furniture. A line that is constant across every instance carries no information at that instance."*

**`opened_by` has been on the wire since M12.1 and rendered nowhere**, and it is the fact that differentiates them. Found by the same audit that produced TS-02: a declared contract with no consumer.

**It is also the product's central claim, on the one screen where it matters.** *Intelligence suggests; humans commit* — and until now the brief could not tell a reader which of the two had happened. **The wording protects that**: *"Signora suggested this"*, never *"Signora decided this"*, because the domain is explicit that an automatic qualification *"is still only a suggestion — the opportunity opens at `tracking`, which commits nobody."* Overstating it on the screen whose job is to let a seller disagree would be the worst place to do it.

**Both facts, not one.** The stage says what is happening now; `opened_by` says why it started. Dropping the stage to make room would trade a current fact for a historical one.

---

## PS-04 — the decision is the end of the visit *(2026-08-02)*

**R10-02**, and the first slice chosen by the *product-refinement* lens rather than the contract lens.

> *"Take an account on: the dialog closes, the stage line changes, and the page is otherwise identical. **You have finished with this account and the product does not know it.** The decision is the one moment the product can be certain the reader is done — and it is the moment it does the least."*

**Where the sequence at the foot of the page could not reach.** D41 put *next* where a reader finishes *reading*; R10-02 is about where a reader finishes *deciding*, which is a different moment and the more certain one.

| Decision | Why |
|---|---|
| **An offer, never a redirect** | The finding is explicit: *a page that navigates itself after you click something takes the reader's place away from them, and a dismissal is exactly when somebody wants to check what they just wrote.* **Nothing moves until the reader says so**, and *Stay here* is a real choice rather than a dismissal affordance |
| **Nothing offered when there is no next** | The dialog closes exactly as before. **An offer that goes nowhere** is what this surface refuses in citations, in workflow controls and in the sequence |
| **Nothing offered when the name has not resolved** | *"Next: "* is worse than no offer. The sequence applies the same rule |
| **The question stops being asked** | The dialog's title changes to the past tense and the form is replaced. A dialog that keeps its question after the question is answered invites a second answer, which the domain would rightly refuse |
| **`nextInSequence` is exported and shared** | One definition of *next*, read from the same cached ranking. **Two places computing it separately is how a reader gets offered two different "next"s in one visit** (§2) |
| **Navigation belongs to the page** | The component takes a name and a callback. Reaching for a router inside a presentational control would make every test of a decision mount an app router to assert wording — and `Button` has no `as`, so a styled link would mean restyling a frozen component (§20c) |

---

## Journey review — 2026-08-02

**A different review from the two before it.** The contract review read the code and asked what was promised; the product review read [39-product-review-findings.md](39-product-review-findings.md) and asked what felt weak. **This one traces a customer from one end of a task to the other**, and it finds things that are invisible on any single screen because every screen involved is correct.

**Nine journeys, traced against the running product.** Every claim below was read out of the repository.

| Journey | Where it stops |
|---|---|
| **Reviewing an account** | **Nowhere.** List → brief → arithmetic → citations → what to check → decide → next. Complete end to end |
| **Discovering a new account** | **At the declaration.** A customer names a company to watch and nothing consumes it ([C-021](../LANE_COORDINATION.md)). The screen is honest — it says Signora *has been told*, not that it has *started looking* — which makes this a truthful stop rather than a broken one |
| **Taking ownership** | **At the second person.** See below |
| **Collaborating with teammates** | **At the first name.** [C-024](../LANE_COORDINATION.md) |
| **Understanding what your company sells** | **At the route guard.** [C-008](../LANE_COORDINATION.md), and its premise changed today — see the addendum there |
| **Returning to previously reviewed work** | **Partly served.** *Decided* accounts are listed below the attention list; accounts opened and left undecided are indistinguishable from accounts never opened ([R10-03](39-product-review-findings.md), needs per-user read state) |
| **Understanding why Signora concluded something** | **Served, except the Decision Package**, which waits on `reasoning@1` holding a release |
| **Managing connected systems** | **Deliberately absent.** Customers never configure providers (ruled 2026-08-01), so the absence is the design rather than a gap |
| **Understanding overall workspace health** | **Not built.** The RevOps question — *is the motion working?* — has no surface. That is M11 in the product roadmap, not a slice |

### Taking ownership stops at the second person

**You can take an account on. You can never hand it to anybody.**

`WorkflowActions` sends `owner_id` in exactly one circumstance — `stage === 'engaged'` and the viewer does not already hold it — so **the only assignment the product can perform is self-assignment.** The API accepts an arbitrary `owner_id`; no screen ever sends one.

**A sales manager cannot give an account to a rep. A rep going on holiday cannot hand theirs over.** The workflow models ownership fully and offers exactly half of it.

**Not raised as its own item, because it is [C-024](../LANE_COORDINATION.md) wearing different clothes**: assigning to somebody means naming them, and nothing in the product can render a person's name. **The two are one decision**, and recording them separately would invite them to be answered separately.

### PS-05 — the account remembers what was decided, and why *(2026-08-02)*

**Found by the journey review, and it is the one place the review found where the product knew something and did not say it.**

`AccountOpportunity.history` has travelled on every brief since M12.1 and **no screen has ever read it.** Each entry carries the stage, who decided, **why**, and when — *"Every workflow state in order, oldest first. Append-only and never rewritten — the status is the audit trail rather than something kept beside it."*

**It is the one record in Signora that nothing can reproduce.** Every score, signal, narration and finding can be recomputed from evidence; a decision cannot.

**The question it answers is *"what happened here before me?"*** A seller opening an account a colleague worked last month saw the current stage and nothing else — not that it was taken on and given up, not why. And when the colleague is themselves: a rep who dismissed an account in March and finds it back in June should not have to remember their own reasoning. **That is the effort this removes.**

| Decision | Why |
|---|---|
| **The reason leads; the stage follows** | *"Wrong segment — they're SMB"* is the record. The stage is how the product filed it, and leading with vocabulary would read as a status log rather than a colleague's note |
| **Rendered in the order it arrived** | The screen does not re-sort — the ledger's rule, for a stronger reason here: **a trail reordered by a browser can disagree with the record it claims to show** |
| **Nobody is named** | `decided_by` is an identifier. *"Somebody here"* is the truthful form, the same wording the workflow line has used since **D23**. When [C-024](../LANE_COORDINATION.md) settles identity this reads it and **nothing else changes** |
| **Signora's own entry says Signora** | `decided_by` is null on exactly one entry — *the one state Signora may author*. Calling that *"somebody"* would blur the distinction the product rests on |
| **Silent below one real decision** | Every account has an opening entry, so a section rendered for that alone would appear on every brief carrying nothing — which is what made the workflow line furniture (R1-06) |

**It needed no architecture.** The data was on the wire, and D23 had already established how to speak about a person the product cannot name — which is why this was buildable while collaboration itself is not.

### What this review changes about priority

**Three coordination items now hold six of the nine journeys**, and two of them — C-021 and C-024 — each block more than one. **That is the most useful thing this review produced**: not a new slice, but the observation that the remaining friction is concentrated rather than scattered, and that two rulings would unblock most of it.

---

## Usability review — six perspectives, 2026-08-02

**Traced against the running product, not imagined.** One executable slice, and the rest concentrated on the same four decisions.

| Perspective | State |
|---|---|
| **First-time customer** | **One slice found and shipped — PS-06 below.** The rest is [C-007](../LANE_COORDINATION.md), deliberately unscheduled |
| **Daily workflow** | **Served.** List → brief → citations → decide → next, with position, provenance and now a decision trail. This is the journey the product does well |
| **Manager** | **Not served.** A manager cannot see who holds what without opening every account, and cannot see a person's name at all ([C-024](../LANE_COORDINATION.md)) |
| **Administrator** | **Barely served.** Create an organization, rename nothing, see no members, monitor nothing. [C-024](../LANE_COORDINATION.md) and [C-008](../LANE_COORDINATION.md) |
| **AI trust** | **Served, and it is the product's strongest surface.** Provenance on every narration, limitations the catalog authored, *Signora suggested this* versus *somebody here added it*, and a decision trail that says which entry Signora may author. **No perspective found a place where inference is presented as fact** |
| **Long-running usage** | **Unknown, and stated as unknown.** The brief is eight sections and grows with each slice; whether that becomes clutter needs somebody who has used it for months, which nobody has |

### PS-06 — an empty list says why it is empty *(2026-08-02)*

**One sentence covered two situations that are not alike.** *"Nothing needs your attention"* is true of a workspace Signora has watched for weeks and found nothing hot in today. It is **not** true of one that has never been told which companies to watch.

**There the product reported an empty *result* where the truth was an empty *input*** — and a new customer would reasonably conclude Signora had looked and found nothing. **The product already knew**: a target account list at version 0 has never been declared.

| Decision | Why |
|---|---|
| **It says what is true and stops** | No button, no *"get started"*, no promise about what happens after declaring. The guided first run is [C-007](../LANE_COORDINATION.md) and a call to action here would answer part of it by accident |
| **No control, deliberately** | An owner already has Settings in the navigation; **a member cannot declare a watch list at all**, so a control offering it would be one they cannot use |
| **Silent while the declaration loads** | Announcing *"nobody has told Signora anything"* to a workspace that has is the confident wrong answer this page refuses everywhere else |
| **Reading it is always permitted** | `policy.csv` grants `member` read on `target_account`, so the question the empty state asks is one every caller may ask |

## Architectural concentration — which decisions hold which journeys

**Recorded so architectural work can be prioritized by customer impact rather than by implementation convenience.**

| Decision | Journeys held | Customer value unavailable | Affects | Slices unblocked |
|---|---|---|---|---|
| **[C-024](../LANE_COORDINATION.md)** — identity resolution | Collaborating · taking ownership beyond yourself · manager view · administration | **Nobody can be named anywhere in the product.** No team list, no reassignment, no *"Priya dismissed this"* | **Collaboration · administration · daily use** | **TS-01**, assignment, manager view, and every future mention, comment, notification and audit actor |
| **[C-021](../LANE_COORDINATION.md)** — provider dispatch | Discovering a new account · first run | **A customer names a company to watch and nothing looks at it.** The head of the pipeline is connected to nothing | **Onboarding · trust** | PP-02's last wire, PP-03, [C-007](../LANE_COORDINATION.md)'s guided first run |
| **[C-008](../LANE_COORDINATION.md)** — who may read the commercial profile | Understanding what your company sells | **A seller cannot see the ideal customer they are selling against.** Live since TS-02 removed the hardcoded owner | **Daily use · trust** | One route guard and a read-only mode on one screen |
| **[C-025](../LANE_COORDINATION.md)** — the Signal Catalog's purpose | Understanding Signora's vocabulary | **Nine terms on the first screen with no definition anywhere** | **Onboarding** | R5-04, already built and reverted, ~70 lines |

> **C-024 and C-021 are the two that matter.** Between them they hold five journeys, three product areas, and every collaboration capability the roadmap has ahead of it. **C-008 and C-025 are each one slice behind a one-sentence ruling.**

---

## Long-term review — 2026-08-02

**A different question from the journey review.** Not *where does a workflow stop*, but *what does this page become after six months and thirty visits a day*. The brief is now eleven sections; that is the thing worth watching.

### PS-07 — the same fact stops being said twice

**`is_current: false` implies `evidence: 'stale'`.** One derivation is read from the score, the other from the opportunity, and they cannot disagree: `evidence_state` is `stale` exactly when the score is absent or past its validity, which is what `is_current` reports.

So on an expired account the brief said it **twice in one card, three lines apart** — the badge saying *"Evidence expired"*, and `ReadingValidity` saying *"This reading expired on 20 Sep 2026. It is shown as it stood — nothing has replaced it yet."*

**The sentence is the better of the two**: it names the date and explains that the reading is preserved rather than broken. **The badge's remaining job is `cooling`**, which no other element on the page knows — and restricting it to that is the rule the component already applies to `current`: *"everything is fine" is noise that trains people to stop reading badges.*

**Introduced by PS-01 and removed here.** R1-04 was right that the brief had to say *cooling*; carrying `stale` along with it was the part that did not earn its place.

#### A test that had stopped asserting anything

`brief.test.tsx` asserted the badge appeared for an expired account — with a fixture pairing `evidence: 'stale'` and `is_current: true`. **The pipeline cannot produce that pair.** The test passed throughout and asserted nothing: a guard that cannot fail, in test form. It now sets the state that actually occurs and asserts the fact is stated **once**.

### What else the lens found, and did not act on

| Lens | Observation |
|---|---|
| **Information density** | **Eleven sections on the brief**, and every one earns its place today. **This is the thing to watch, not to fix** — the next slice that adds a twelfth should be asked whether something can go, and that question needs somebody who has used it daily, not an architect reading it |
| **Repeated information** | One more instance, deliberately kept: the *"Before you act"* empty state also says the evidence expired. **Different section, different question** — *why is there nothing to check* — and a reader can arrive there without reading the score card. Recorded so a future reviewer knows it was considered rather than missed |
| **Discoverability** | The decision controls sit at the top, under the account name, and every other section is reference. **Correct for a reader who already knows what they want**; unknown for a first-time reader, and that is the same unknown the six-perspective review recorded |
| **Workflow continuity** | Served: position in the list, next account by name at the decision, and the decision trail. **Nothing found** |
| **Operational transparency** | Provenance on narration, catalog-authored limitations, Signora-versus-person on every decision. **Nothing found**, and the same positive result as the AI-trust perspective |

---

## Subtraction review — 2026-08-02

**A deliberately different question: *what can disappear without reducing customer confidence?*** Eleven sections on the brief, each interrogated against five tests — does another section already answer this · can another absorb it · is another now redundant · does it help a decision or merely document a fact · would an experienced seller miss it.

**Conclusion: nothing should be removed today.** One candidate was found and is **not** being acted on, for a reason given below.

| Section | Verdict |
|---|---|
| **Back to list** | **Keep.** The sequence and the post-decision offer are *forward*; returning to the list is a different intent and R10-01 was about the absence of forward exits, not the presence of a backward one |
| **Workflow line** | **Keep — with one observation, below** |
| **Score arithmetic · why now** | **Keep.** *Why now* is on the brief precisely because R1-01 moved it off the row: *"why did this number move"* is a question somebody asks here and nowhere else |
| **Momentum · cooling badge** | **Keep.** Already reduced in PS-07 to the one state nothing else reports |
| **Reading validity** | **Keep, and it was the closest call.** *"Exactly correct until 20 Sep"* documents a fact rather than driving today's decision — but it is **the only statement that the score has a shelf life at all**, which is a trust property rather than a workflow one. Removing it would make the number look permanent |
| **Posture split** | **Keep.** Its own reasoning already answers this: *"all of this is expansion" is as much a finding as a split is* |
| **Contested — badge, note, since** | **Keep all three.** A **label** in scan position, an **explanation** that Signora refused to average opposing readings away, and whether it **became** contested or always was. Three different questions, and the note is the only place the trust argument is made. **Contextual reinforcement, not redundancy** |
| **Narration · validation · research · ledger · decision history · sequence** | **Keep.** Each answers a question no other section does |

### The one candidate, and why it is not being acted on

**The workflow line reads *"Signora is tracking this · Signora suggested this · nobody has taken it yet"*** on a typical account. `tracking` and `automatic` are near-perfectly correlated — the domain is explicit that an automatic qualification *"opens at `tracking`, which commits nobody"* — so on the most common account the middle phrase adds little to the first.

**It is informative in the other three combinations**: a person adding an account by hand, and any account somebody has since acted on.

**PS-03 added that phrase three slices ago, and it was accepted.** Suppressing it now for the common case would be **me re-reading my own copy without new evidence** — and the finding it answers, R1-06, came from a reviewer looking at twelve real briefs. **A wording judgement made by its own author days later is worth less than one made by somebody using the product**, so it is recorded here for the next reviewer rather than acted on.

### Why the answer is *nothing*, and why that is not inertia

**Every section on this page carries a written reason, and most of those reasons were reached by a reviewer with evidence** — R1-01 moved the trigger, R1-04 added the cooling badge, R2-02 promoted a limitation, R9-03 marked contraction, R10-01 added the sequence, R10-02 added the offer. **A page assembled that way is hard to subtract from**, because each addition already survived the question of whether it earned its place.

**The honest risk is the opposite one:** that additions keep passing the *"does this earn its place"* test individually while the page as a whole becomes dense. **That is a judgement no single slice can make and no architect can make by reading**, and it needs somebody who has opened the brief thirty times in a day. Recorded as the standing question for the first design partner review.

---

## Product Surface — Implementation Waiting, declared 2026-08-02

**Nine slices shipped, nine reviews run, and the reviews have stopped finding work.** The module is suspended rather than finished: it remains Lane A's, and it consumes no engineering capacity until the coordination items below have directions.

> **Why this record exists.** Under rotating assignment the lane that implements the next slice of this module is usually not the one that implemented the last (`CLAUDE.md` §20e), and it inherits this document and nothing else. **Somebody returning in six months should be able to read why the module paused without reading commit history.**

### What was completed

| | What a customer got |
|---|---|
| **PS-01** | An account with nothing live says so, instead of rendering two different states as one blank space |
| **PS-02** | Three narration states that were one blank space — including *narrated against evidence that no longer resolves* |
| **PS-03** | The brief says who put this account in front of you — Signora, or a colleague |
| **PS-04** | A decision is the end of the visit: recording one offers the next account rather than dropping you back where you were |
| **PS-05** | The account remembers what was decided about it, and why — the one record in Signora nothing can recompute |
| **PS-06** | An empty attention list says *why* it is empty: nothing declared, or nothing qualifying |
| **PS-07** | The same fact stops being said twice on one screen |
| **PS-08** | The keyboard shortcuts say they exist |
| **TS-02** | The product stops telling every signed-in person they are an owner |

**A pattern worth carrying forward, because it produced four of the nine.** PS-03, PS-05, TS-02 and (in Provider Platform) PP-04/05/06 were all **declared-but-unfulfilled contracts** — a field on the wire that no screen read, a role hardcoded behind a stale `TODO`, a rate limit nobody honoured. **The gaps were not missing features; they were promises the code was already making.** That seam is now **exhausted** in this module: every field on the account, opportunity and members responses is either rendered or deliberately not.

### What is waiting, and on what

| | Blocked on | Resume trigger | Customer impact while waiting |
|---|---|---|---|
| **TS-01 — the Team page** | [C-024](../LANE_COORDINATION.md) — nothing in the product can render a person's name | An identity-resolution direction is accepted | **An owner cannot see who is in their organization by name.** The page would render UUIDs, which is not a product |
| **R5-04 — the signal glossary** | [C-025](../LANE_COORDINATION.md) — does *"the catalog carries names and nothing else"* mean no prose, or no *duplicated* prose? | Either ruling; both are executable | Nine Signal Catalog terms meet a first-time reader with **no definition anywhere in the product**. Built and reverted; restorable in minutes |
| **A seller reading the commercial profile** | [C-008](../LANE_COORDINATION.md) — should members see it, and where? | An option is chosen | **Every AE and SDR, every day**, cannot see the ICP an account is meant to match or the buying committee they are selling into. **The cost stopped being theoretical when TS-02 shipped** — see that item's addendum |
| **Every responsive decision** | [C-026](../LANE_COORDINATION.md) — is Signora expected to work on a phone? | A supported viewport is stated | **Below 768px there is no navigation at all** ([B-019](../BUGS.md)). A signed-in customer on a phone cannot reach Settings |
| **The guided first run** | [C-007](../LANE_COORDINATION.md), which is itself blocked on [C-021](../LANE_COORDINATION.md) | Provider Platform can start a sync | The onboarding flow would end by asking which companies to watch, and **the answer would go nowhere** |
| **Customer-facing attribute names** | [C-018](../LANE_COORDINATION.md) — nobody owns them, and every available implementation contradicts something already ratified | An owner is named | Engineering's words reach a customer's screen ([R11-06](39-product-review-findings.md)) |

**Five of the six are product or architectural decisions.** None is waiting on engineering capacity, and **none can be worked around without deciding it by implementation** — which is what each item exists to prevent.

### Known limitations, stated rather than discovered later

| | |
|---|---|
| **The brief is eleven sections and has never been reviewed by somebody who opens it thirty times a day** | The subtraction review's standing question. Each section earned its place individually; whether the page as a whole is dense is a judgement no single slice can make |
| **`j`/`k` keycaps are hidden below `sm`** | A responsive assumption made in C-026's absence — the smallest one available, and flagged rather than left to pass as a decision |
| **The workflow line's middle phrase is near-redundant on the commonest account** | Found by the subtraction review, deliberately not acted on: it would be the author re-reading their own copy days later, against a finding a reviewer reached from twelve real briefs |
| **No accessibility or performance testing exists anywhere** | [C-014](../LANE_COORDINATION.md), QE's and unbuilt. Every slice here was checked by hand against roles and accessible names; **none was checked by a tool** |

### Future implementation opportunities, for whoever returns

**Recorded so they inform planning without becoming work nobody asked for.**

| | |
|---|---|
| **The demo test is the useful filter** | *"Would a design partner notice this in the first minute?"* found PS-04, PS-06 and R5-04. It is a better generator of work than a contract audit now that the contract seam is exhausted |
| **The next real finding will come from usage, not from reading** | Nine review lenses now converge on coordination items rather than slices. **That is the signal the module is mature, not that reviewing failed** — the class of defect that remains is the class only a design partner produces |
| **Responsive is a milestone if the answer to C-026 is *mobile*** | Every screen needs a pass, the brief's eleven sections need an order that survives one column, and the shell needs a navigation pattern that does not exist |
| **Identity unlocks more than the Team page** | C-024's answer also decides how AI-generated work names a responsible user, how audit history represents actors, and how notifications know who to reach. **It is the highest-leverage of the five** |

---

## Implementation Waiting ended — 2026-08-02, the same day it was declared

**The record above stands as what was true when it was written, and it is not being rewritten** (`CLAUDE.md` §2: *correct a claim about the present; date a record of the past*). **What follows is the correction.**

**Product Surface was suspended after nine review lenses converged on coordination items rather than slices.** That conclusion was right about the lenses and **wrong about the module**, and the product owner's redirection the same day is what showed why:

> *"The repository contains considerably more functionality than the application currently exposes."*

**Every lens applied up to that point looked at screens that exist.** Contract, journey, product, production-UI, long-term, subtraction, workflow, trust and responsive reviews all ask *is what is here correct?* — and by then it largely was. **None of them could see a capability that has no screen at all**, because there was nothing to review.

**The lens that was missing was the repository, not the surface.** A capability audit — 31 endpoints against 5 screens — found three slices in an afternoon, and none was cosmetic:

| | What it exposed |
|---|---|
| **CX-01** | A **complete module** — Integrations: backend, screen, OAuth, disconnect — that **nothing in the product linked to** |
| **CX-02** | The two pages a customer meets when something goes wrong, which the framework was supplying and the product had never claimed |
| **CX-03** | Timeline's endpoint, hook and component, **all built, mounted nowhere** ([C-024](../LANE_COORDINATION.md)) |

**The distinguishing property, and it is what makes the lens reusable:** every one was **invisible to every test in the repository.** Twenty component tests covered `feed.tsx` and not one could ask whether any page rendered it. A test asks *does this behave correctly*; **none of these was a behaviour defect.** They were absences of reachability, and only an audit that starts from the backlog of *capabilities* rather than the inventory of *screens* finds them.

### What this changes about when a module may be declared waiting

> **A module is not exhausted when reviews of its existing screens stop finding work. It is exhausted when every capability the repository has built is reachable through it.**

**The first test was the one applied on 2026-08-02, and it retired the module two initiatives early.** Product Surface is the layer through which everything else becomes a product, so its work is bounded by *what the repository has built*, not by *what it has already drawn*.

**Recorded here rather than in the module's status line**, because the mistake is more useful than the correction: the reviews were rigorous, converged honestly, and were measuring the wrong surface. **A conclusion reached carefully from the wrong frame still reads as a finished module.**

### Where the work is tracked now

**[43-customer-experience.md](43-customer-experience.md) is the driver** — the navigation map, screen inventory, capability mapping, the nine journeys and the CX roadmap. **This document remains Product Surface's design record**; the blueprint is what says which slice comes next.

---

## A4 — the brief says how current its evidence is *(2026-08-03)*

**Epic A's first slice, and the first Product Surface change made by Lane B** under the end-to-end ownership ruled in [C-323](../LANE_COORDINATION.md). **Sales Workspace remains Lane A's**; this touched the account brief's header and nothing else in that surface.

**What a customer sees.** One line under the account name: *"Latest evidence · 2 weeks ago"*, or *"No evidence collected yet"*.

**Why it sits directly under the name.** It qualifies the **whole page** rather than any one card. The score, its contributions, the narration and the validations are all built on evidence, and a reader who does not know how old that evidence is cannot calibrate any of them. Placing it beside the score would have made it read as a property of the number.

**Why it renders nothing while the name is loading.** Two skeletons stacked on arrival is a page that looks broken, and this is the least urgent line on it.

### The wording is a constraint, not a preference

**The product says *observed*, and must never say *checked*.** The fact behind the line is *when a provider observed the newest thing Signora holds* — read from `claim.observed_at`, not from a sync record. **Signora cannot currently say when it last looked at a given account**: `provider_sync` carries no subject, and `provider_watermark.position` advances only when records arrive, so a provider that ran and found nothing leaves no trace.

*"Last checked 2 hours ago"* is the more natural sentence and the product owner's own example, and it is **the one thing this line may not say.** `freshness.test.tsx` asserts the copy never drifts back to it, because the drift would be invisible to every other test and would put a claim on screen that no table supports.

### What it did not need

**No new endpoint · no new HTTP request · no new module dependency · no new table.** The brief already calls `/account-identities`, and Knowledge Graph already joins claims to entities to resolve names. **The whole slice is one field on a response that was already being fetched** — which is what Epic A is supposed to look like when the audit was right about the foundation.

---

## TASK-447 — the App Shell, and the invariant it could not enforce *(2026-08-06)*

**The shell's *"never a second search box"* is now a test.** [450 §5](450-global-search-traceability-audit.md) asked for exactly this — *"a structural test that refuses a second search input outside the shell… the fourth instance of a pattern the frontend already uses three times"* — and `tests/components/single-search.test.tsx` is it, written to `vocabulary` · `design-tokens` · `no-mock-data`'s shape.

### It forbids a second *implementation*, not a second input, and the reading is deliberate

**All three precedents forbid a practice rather than an element.** ⛔ **The literal reading would refuse an approved screen**: [410](410-approved-ui-specification.md) approves a *Search by name* on Companies **and** the shell's global search. **What the invariant protects is that there is one search — one request path, one cache identity, one global entry** — so a screen may *use* it and may not build another.

| The three checks | And the fourth |
|---|---|
| **One file reaches `/account-search?`** · **one file builds the `accountSearch` key** · **only the shell mounts `<AccountSearch />`** | ⚡ **The shell still mounts it.** Without this the other three pass over a product with no search at all — *a guard that cannot fail is documentation pretending to be code* (§2) |

**Every one was proven by reintroducing the violation**, including the anti-vacuity check.

⚠️ **If the product owner meant the literal reading — no search input anywhere but the shell — this file is where that ruling lands**, one line stricter rather than a redesign.

### Why the slice is this small, which is a finding rather than an apology

**Three of the shell's ten cross-cutting concerns are complete** — session and identity, workspace context, search — **and [452](452-app-shell-traceability-audit.md) produced *"no new backlog row"*.** ⛔ **Everything else in the shell is somebody else's**: global scope is [TASK-450](../BACKLOG.md)–[TASK-452](../BACKLOG.md), notifications are [ADR-0040](adr/0040-notifications.md), AI entry points are [C-419](../LANE_COORDINATION.md), and the rest is named out of scope by the row itself. **What was left was the one gap the audit named, and it is built.**

⛔ **The 22 numbered specifications are not in the repository** — three documents quote the same three sentences and none records the rest. **[C-233](../LANE_COORDINATION.md)**, and it is [C-230](../LANE_COORDINATION.md)'s shape one row later: a convergence task whose target the repository does not hold.

---

## TASK-440 — Companies, the book a seller scans *(built 2026-08-06 · **not shipped**)*

> ⛔ **This section describes a screen that is complete and is not in the repository.** Implementation, tests and two passing Playwright journeys exist; **the route is withheld because it has no entrance and the entrance is [C-229](../LANE_COORDINATION.md)'s to rule.** **Shipping it would leave `reachability` red in both `make reachability` and `tests/components/reachability.test.tsx`** — a blocking quality defect traded for a screen nobody can reach. **It lands unchanged, plus one link, the day the ruling arrives.** *This is recorded here rather than lost in a stash: the next lane in this module must not rebuild it.*

**`/accounts` — the whole tracked book, paged, as a table or as cards, with the owner filter and a search.** Attention answers *"who do I call today"*; **this answers *"where is everything"***, which is a different act and needs a different shape: a table exists so a reader can run their eye down a column, and a triage list that grew a *show all* control would stop being a triage list.

⛔ **It has no entrance, and that is the one thing to read before touching this screen.** [D38](39-product-review-findings.md) removed *Companies* from navigation by name — *"a company is what an account is"* — and [C-229](../LANE_COORDINATION.md) asks the product owner whether [410](410-approved-ui-specification.md) supersedes that. **`make reachability` fails on `/accounts` today, deliberately**: the screen is complete and the door is not this lane's to hang. **Do not add a navigation entry to make the gate pass** — that is the ruling, arriving as a commit.

### What the list contains, and the audit that got it wrong

⚠️ **[446](446-companies-traceability-audit.md) describes the table as *"every company this workspace watches"* and cites `GET /accounts`. That read returns open opportunities.** A company is *declared* the moment somebody types it and becomes *tracked* when its evidence crosses the qualification threshold, so **the two sets differ and the screen may not use the customer's word for the one it is not showing.**

**The subtitle names the set, and a test asserts it never drifts back** — the same treatment `freshness.tsx` gives *"last checked"*. **The gap itself is [C-232](../LANE_COORDINATION.md)**, and closing it needs account matching rather than a render.

### Every cell already existed, and the extraction is the slice's one structural change

**`AccountRow` moved out of `app/(app)/page.tsx` into `components/intelligence/account-row.tsx`, unchanged.** [446](446-companies-traceability-audit.md) calls the card view *"no backend at all — a rendering, not a capability"*, and **that only stays true if it renders something that already exists**: a second implementation of an account row is how two screens start disagreeing about what an account looks like. Attention's suite was not touched and still passes, which is the proof the move changed nothing.

**The three coverage sentences are imported from the header search rather than restated**, for the same reason.

### Three decisions a later change must not quietly reverse

| | |
|---|---|
| **The owner filter is applied in the page query, never over the page** | [446](446-companies-traceability-audit.md)'s own words: filtering returned rows *"reads correctly at twelve accounts and silently becomes a lie at two hundred"*. **This screen is the one built for two hundred**, which is also why it pages with `useInfiniteQuery` instead of reusing `useAccounts` |
| **A search replaces the list rather than filtering it** | Filtering the loaded pages searches the rows that happened to arrive. **And the projection has no notion of who owns an account**, so a seller filtered to *Mine* can be shown a company that is not theirs — **the screen says so above the results** rather than letting it become a bug report |
| **The view and the filter travel together in the URL** | Changing how the list is drawn must not silently widen whose list it is. Both are links, so both are bookmarkable and keyboard-reachable without a widget |

### What it did not need

**No endpoint, no index, no migration, no table, no event.** 🟢 render only, as the row said — and the only backend fact this slice established is one the audit had wrong.

---

## A1 — find an account by name *(2026-08-03)*

**Epic A's second slice.** *"Show me Databricks"* — the second question of every evaluation, and the one a ranked list structurally cannot answer.

**Where it lives, and why the shell.** A control in the application header, not a navigation entry: **search is a verb, not a place.** The shell owns *placement*; the feature owns *behaviour* — `components/shell/app-shell.tsx` gains one region and its error boundary, matching every other region in that file, and every line of logic is in `components/intelligence/account-search.tsx` behind `lib/query/hooks/search.ts`.

**Touching the shell is 🔴 and was approved by the product owner** for this slice, on the grounds that A1's specification places global search there. Recorded because a lane reading the Change Budget alone would conclude it could not.

### Two decisions a later change must not quietly reverse

| | |
|---|---|
| **No substring highlighting** | The server matches every name a source has ever claimed, so **a result may not contain the text that was typed** — a company found under its former name is listed under its current one. Highlighting promises *"this visible text matched"*, which is sometimes false. If explainability is wanted, say *"matched previous name: Acme Software Ltd."* |
| **The highlight resets when the answer changes** | Arrow down to the second result, type one more letter, and the list is a different list. Without the reset, Enter opens whatever has arrived in that position — **silent, and wrong every time.** Asserted |

**The keyboard path is the product, not the accessible alternative to it.** ⌘K from anywhere, arrows, Enter, Escape. One implementation serves both a seller who has learned the control and a customer who cannot use a mouse, which is why §20c treats an unreachable control as a defect rather than a missing enhancement.

**An account nobody has named is still a result**, shown as *Unnamed account*. Hiding it would make search quietly disagree with the list that shows it — and A6 is the slice that gives that state a name worth reading.

---

## TASK-905 — a contraction risk stops looking like an opportunity *(2026-08-05)*

**The ruling is [C-011](../LANE_COORDINATION.md), open since the register was created and answered by the product owner as a task**: *"A contraction risk must not be confusable with a low-scoring opportunity — they mean opposite things to a CRO scanning a list. The treatment is yours, within the design system; the ruling is only that they must differ."*

**What a customer sees.** On an account whose leading hypothesis points downward, a **warning badge reading *At risk*** in the row's status lane, immediately left of the score.

### Why the confusion exists at all, and why it is not a bug in the score

**The Buying Score Engine refuses to sign posture into the score** — *"two accounts can score identically and mean opposite things"* — and that refusal is correct. The score orders **attention**, not value. But a list ordered by attention puts a contraction risk **next to the weakest opportunities**: measured against the real twelve, both risk rows sat at positions **eleven and twelve**. A reader scanning downward treats the bottom of a list as *least important*, and for one of those two rows that is exactly backwards.

**So the row must carry what the number deliberately does not.** This is the module's refusal reaching the surface rather than being undone there.

### What was already there, and the two holes it had

**[R9-03](39-product-review-findings.md) marked contraction at M12.3**, inside the hypothesis line, and the product judgement it made is unchanged and correct: **only contraction is marked**, because the list is mostly expansion and a badge on every row saying *everything is fine* trains people to stop reading badges. **The marked minority is the signal.**

| | |
|---|---|
| **The mark waited for the catalog** | It hung off the hypothesis **title**, so a row whose title had not arrived rendered **unmarked** — on **every first paint**, and **permanently** for a score formed under a catalog version that no longer declares its key. **Posture travels on the wire precisely so a client never needs the catalog to know which way a row cuts**; spending it on a mark that was conditional on the catalog anyway gave the guarantee away |
| **It was in the quietest place on the row** | Running text on the left, at the same weight as three other phrases, while the row's **status lane** — where a scanner reads row state, and where *Contested* and the evidence badge already live — said nothing about the one fact that inverts the row's meaning |

### The treatment

**`PostureMark` is a component of its own, and takes `posture` and nothing else.** That is the load-bearing part rather than a tidiness preference: the mapping from a catalog key to a commercial meaning belongs to the Buying Score Engine, and a copy in the browser would be a second vocabulary — wrong the moment the catalog gained a type, and invisible when it did. **A component with no key to pattern-match cannot hold one** (§2, *types should make incorrect architecture impossible*), which retires a test that had been asserting the same property from outside.

**It sits last in the status lane, so it is the thing beside the number.** The confusion is with a *score*, so the correction belongs where the eye lands after the digits: ***At risk · 31*** cannot be read as a weak opportunity.

**The hypothesis line still says what happened, in the catalog's words, and that division of labour is the point.** `decision_maker_departed` **renders as a neutral sentence that never says *risk* at all** — on that row the badge is the only thing carrying it.

**Two words, and a sentence for a screen reader.** The badge lane is `shrink-0` beside the score and already reflows onto a second line at 320px, so the visible text is *At risk* and the sentence it abbreviates — *to existing revenue* — is read out rather than laid out. **An icon as well as a tone as well as words**: colour alone fails a colour-blind reader, and accessibility is a defect class rather than an enhancement (§20c). **`warning`, not `danger`** — a contraction risk is a different *kind* of attention, not something that has gone wrong.

### What this slice deliberately did not do

**No reordering** — marking beats reordering precisely because the ranking is the ranking, and a list whose order depended on posture would be answering a different question. **No filter** — D6's trigger has not fired at twelve accounts. **No change to the score**, which states an ordering and must not start stating a direction. **No backend change**: `posture` has been on `AccountAttentionResponse` since M12.3, so this is a render slice end to end.

---

## TASK-903 — what you sell reaches the account you are selling it to *(2026-08-05)*

**Stage 2 of [C-008](../LANE_COORDINATION.md), and the ruling named its contents exactly**: *"in-context placement of the **two declarations that need no matching**: the buying committee where contacts appear, and what we sell on the brief. **Explicitly not** *'this account fits ICP X'*, which waits on [C-002](../LANE_COORDINATION.md)."*

**What a customer sees.** On the account brief, below everything Signora derived: **a *What you sell* card** listing the workspace's products, each with the roles that have to agree — and, beneath it, the competitor list that was already there.

### The two questions it closes, at the moment they are asked

C-008 recorded them against the personas: the AE's *"which of our products is this account even a candidate for?"* and the SDR's *"who normally has to sign off on a deal like this?"* **Stage 1 made both answerable and only by leaving the account** — `/business` is a page a seller has to go to, and the questions arrive while looking at a company. **That gap is the whole argument for option D over option C**, and it is what this slice closes.

### The ideal customer is deliberately absent, and it is the one decision here worth defending

`/business` shows *who buys it* — industries, countries, company size — beside each product. **This does not**, and the ruling lists two declarations rather than three for the reason.

**An ICP rendered beside a real company is a comparison the reader completes whether or not the product does.** Signora would then be understood to have made a claim it never made and cannot support: comparing a real company to a description is **matching**, matching has no owner, and it is explicitly not Commercial Profile's — *the module records and computes nothing* ([ADR-0035](adr/0035-commercial-profile.md)). **A seller who wants the ideal customer opens `/business` and makes that comparison knowingly**, which is a different act from being shown one.

**The component takes no ICP prop at all**, so the boundary is in the type rather than in a reviewer's memory (§2).

### The committee is here because contacts are not anywhere

C-008 says *"the buying committee **where contacts appear**"* — **and no contacts appear in Signora.** No person's name enters the platform from any source: [ADR-0400](adr/0400-person-as-an-entity.md)'s own first question, checked and answered *no*, and the People domain is [TASK-427](../BACKLOG.md), `SEQUENCED`.

**The declaration answers the seller's question without them.** *Who normally has to sign off* is a statement about **roles**, and the committee is roles by construction — *"a role, never a person"*. **Naming which individual holds each seat is the part that needs people**, and it belongs to Epic C.

### Where it sits, and why beside the competitor list

**Both are workspace declarations** — identical on every account, describing the business rather than this company. Grouping them keeps one boundary legible: **everything above is what Signora derived about *this* account; these two are what the customer told us about themselves.** *What you sell* leads, because it is the frame a seller reads *who we are up against* inside.

**Each carries the sentence that stops it being read as an account fact**, which is the same device the competitor section already used: *"your declared catalog, the same on every account. Signora has not said this account is a candidate for any of it."*

### A defect this slice found in the section it sat next to

**[C-226](../LANE_COORDINATION.md)'s class, in `CompetitorContext`** — a section this lane wrote three days earlier. **A failed read and a workspace that has declared nothing both rendered as silence**, so an outage was indistinguishable from an empty declaration on the one screen where a seller would act on the difference.

**Found by having to decide the question for the new section** rather than by looking for it, which is the argument for C-226 being a class worth naming: it is invisible until a second instance forces the choice. Both sections now say when a read failed, and both say *nothing you declared has been lost* — because nothing was written, and a sentence implying otherwise sends somebody to re-type a catalog that is still there.

### What it did not need

**No backend change · no new endpoint · no new hook · no `keys.ts` entry · no permission change.** `policy.csv` has granted `member` read on `product` and `buying_committee` since those slices shipped, `useProductCatalog` and `useBuyingCommittee` already existed for `/business`, and the brief is a top-level route that no guard restricts. **The part label is imported from `components/commercial/vocabulary`**, where `/business` reads it, rather than restated — a second mapping of `CommitteePart` to English would be wrong the moment a part is added and invisible when it is.

---

## TASK-400 · A6 — a company nobody can name leaves the working list *(2026-08-05)*

**[C-321](../LANE_COORDINATION.md), ruled 2026-08-05**, wearing a slice's name. Six sub-questions, and the ruling adopted Lane B's answers whole: **appear yes · working list no · score yes · opportunity no · workable never · `Needs identity`, its own queue.**

**What a customer sees.** Accounts no source has named leave the morning list and appear below it under **Needs identity**, keeping their score and offering no action.

### Identity and significance are different axes, and the list was multiplying them into one number

`70b04700` has four weeks of elevated research on Design Systems, **peaked at 87**, and has no name ([PX-301](../PRODUCT_EXPERIENCE.md)). **That combination is genuinely interesting and genuinely not actionable** — and the working list offered *"I'm working this"* on it. **A button that cannot work, pressed by somebody who then has nothing to do.**

### The score is kept, unchanged, and that is the ruling rather than an omission

*Contribute to a score?* — **yes**, because **the score measures evidence and the evidence is real**. Discounting it here would be a render overruling a reviewed scoring model, which is not a screen's to do. What changes is not the number but the claim the list makes about it: **this is no longer a call list**.

### The guard is the whole risk in the change

**The partition runs only once names have actually arrived.** An identity request in flight — or one that failed — makes **every** account look unnamed, so an eager partition would empty the working list on first paint and leave a queue of everything, permanently, for as long as an outage lasted. **A seller would open Signora to an empty call list.** That is a worse product than the one A6 fixes, and it is the failure mode a reviewer would never see in a green test run against loaded data.

**So while names are loading or their read failed, nothing moves** and the page behaves exactly as it has for three milestones. Asserted three ways: in flight, errored, and all-named.

### It is a read today, and the limit is stated rather than papered over

C-321 says *"`Needs identity` — **a queue with its own workflow**, not a filter"*, and **the workflow was not specified — because there is nothing yet for a customer to do about it.** Signora has no capability by which a person names an account. **A6's own reuse audit reached the same place**: the derivable read *"is worthless without knowing what the queue does"*, so it was recorded rather than built.

**This builds the four answers that were ruled and invents no fifth.** *Opportunity: no* and the qualification rule behind it are `opportunity_engine`'s and `knowledge_graph`'s — **Lane B's**, and not this lane's to encode. **When a naming capability exists, this section is where its action belongs.**

### Two small decisions worth recording

| | |
|---|---|
| **Not `EntityName`, and deliberately not a link** | That component renders a truncated id as an *openable* heading, which is right on the working list — an unnamed account is the one a seller most wants to open, and withholding the link would hide the page that explains why. **Here the row is already the statement.** Dressing an id as a name would put the id back in the position the name would occupy |
| **A source count, never a judgement** | Four sources reporting on one unnamed record is a different thing from one, and it is the only signal a reader has about whether this is worth anybody's time. **The product does not say which, because it has no basis to** |

---

## TASK-1411 · The AI attribution primitive — one confidence, one source list, one *Show reasoning* *(2026-08-10)*

**`components/ui/attribution.tsx` · `AttributionStrip`.** 📁 **Three finalized designs draw the same line under a generated answer** — **Account 360**: *"Show reasoning · 6 sources · Confidence 4 of 5 · Generated 09:14"* · **Reports**: *"Confidence 4 of 5 · 3 sources"* · **AI Research**: *"14 sources · 3 excluded · Confidence 4 of 5"*. ⛔ **Three workflows reaching this separately build three of them, and they will disagree about what *4 of 5* means.**

### The confidence value does not exist, so the component states its absence

⚠️ **The row's own first slice was a read, and this lane performed it before claiming.** 📁 **`ai_platform/public/` exports `Infer`, the inference types, `ExplanationSource`, `EvidenceFact`, `EvidenceRef` and `EvidenceSet` — and no confidence value.** 📁 **`ai_reasoning_engine/public/` names confidence in prose only.** 📁 **The only `confidence` reaching an endpoint is `workspace_tenancy`'s `confidence_floor`, a threshold the customer sets.**

✅ **So `confidence` is optional and renders *Confidence not stated*.** 🔴 **Specifically never `0 of 5`** — ⛔ ***0 of 5* reads as *certainly wrong* where the truth is *not known***, and those are opposite claims. **[C-267](../LANE_COORDINATION.md) is open on exactly this figure and this component is what refuses it.**

⚠️ **It is deliberately not [`StatedAbsence`](../../frontend/components/feedback/stated-absence.tsx).** **That sentence ends *"reload to try again"*, which would be a false instruction here**: nothing failed to load, and reloading produces the same absence forever. 📁 **[P-A](../DOMAIN_DISCOVERY_REGISTER.md) is *a failed read must never render as an empty result*; this is the mirror case, and borrowing the failed-read wording would misreport a working system.**

### Two facts about a source that are never collapsed into one

| | |
|---|---|
| 🔴 **`readable: false` — not listed and NOT COUNTED** | **The row's Security Invariant, the same disclosure rule as [C-245](../LANE_COORDINATION.md).** ⚠️ **The count half is the one that is easy to get wrong**: hiding the row while still counting it tells the reader a source exists that they may not see, which is the leak itself |
| 📁 **`excluded: string` — shown, with its reason** | **AI Research**: *"excluded citations are shown as withheld rather than removed, so the argument stays auditable."* ⛔ **The type carries a reason rather than a boolean**: *"3 excluded"* with no reason is an unfalsifiable claim |

### What it reuses, and what it refuses to invent

✅ **`Confidence` gains its first production caller** — the `N of 5` component existed with zero importers ([C-266](../LANE_COORDINATION.md)). ✅ **`formatDay` is imported rather than re-implemented**, so the strip cannot drift into a second date format.

⛔ **The source list opens in place rather than in a docked panel.** 📁 **The design docks it beside the answer — that surface is the utility panel, [TASK-1433](../BACKLOG.md)'s, and it does not exist.** ✅ **A primitive does not invent it**; the individual source still opens at the cited moment through `onOpen`, which is where a citation actually ends.

⛔ **`reasoning` undefined renders no button at all** — **a *Show reasoning* control that opens an empty panel is the affordance-with-nothing-behind-it this surface has refused since the narration's fact count.**

### First consumer, and the limits recorded rather than papered over

✅ **`NarrativeBlock` mounts it**, which is Account 360's summary block. **`generated_at` moved out of the provenance sentence** so one fact has one rendering. ⛔ **Account 360's *"updates on new evidence"* is omitted deliberately**: that panel's own rule is *"a narration is never rewritten to catch up"*, so the phrase would be a false promise.

⚠️ **The row's Playwright requirement — *"the same component renders on Account 360 and on a report with the same markup"* — is NOT met, and is recorded rather than claimed.** ⛔ **There is no Reports screen**, and 📁 **`ai_narration` holds 0 rows in `signora_lane_a`**, so the strip has no runtime instance to visit on Account 360 either. ✅ **Twelve component tests cover every state**, and both invariants above were fire-tested by reverting them.

---

## TASK-1403 · Reason codes become a diagnosable record, not a log line *(2026-08-10)*

📁 **The design's sentence, which it states twice**: ***"Every rule carries a reason code. The code is written to the session, logged with the redirect, and shown to support in the diagnostics bundle — so 'why did I land here' is answerable WITHOUT REPRODUCING THE LOGIN."***

⚡ **That last clause is the requirement and everything else is implementation**, which is why the three ship together: ⛔ **a code on the session tells the person's own browser and nobody else · a line in a log has no session to join it to · a bundle with nothing in it is a screen.** **Any two of them still require reproducing the login.**

### `frontend/lib/entry/diagnostics.ts`, and it is pure like everything else in the module

| | |
|---|---|
| **`entryMark`** | ⛔ **The code, the gate and the moment — and NOT the route.** ⚠️ **A session carrying the destination is a second copy of a fact the URL already states**, and the two disagree the moment somebody navigates. 🔴 **And never the workspace id**: the session is readable by the browser, so anything on it is disclosed to whoever holds the machine |
| **`entryRecord`** | ⚡ **Shaped so the security event stream can take it verbatim** — `kind` is `entry.resolved` (`noun.verb_past`), **both identities travel together**, and a value that looks like a credential is refused on construction. ⛔ **Mirrored rather than trusted**: a producer that only learns the rule when the server rejects it has already put the secret in a browser's memory |
| **`diagnosticsBundle`** | 🔴 **Workspace-tenanted, and the scope is a required argument** — ⛔ **a signature that let a caller ask for *everything* is one somebody will eventually call that way.** ✅ **What was withheld is COUNTED**: support seeing eleven of fourteen needs to know the three exist, or they read the gap as a missing record and chase it |
| **`explainEntry`** | ⚡ **Names the gate, not only the code** — *"gate 4, workspace standing"* rather than `WS_ARCHIVED` alone. ⛔ **Not customer copy**: [ADR-0034](adr/0034-ubiquitous-language.md) governs what reaches a customer's screen, and this reaches an engineer's |

⚠️ **A record with no workspace is KEPT in the bundle.** 🔴 **Gates 1 and 2 fire before any workspace is loaded** — `ACCOUNT_SUSPENDED`, `SESSION_EXPIRED` — **and those are the refusals support is most often asked about.** ✅ **They belong to the person rather than to a tenant, so they leak nothing, and dropping them would answer the commonest question with silence.**

### ⛔ This is deliberately not a second log, and the producer is not this row

⚠️ **The row is explicit that a reason code is security-relevant** — `ACCOUNT_LOCKED`, `STEPUP_REQUIRED` say why somebody was refused — **so it belongs in the stream [TASK-492](../BACKLOG.md) writes.** ⛔ **The producer that hands it over is NOT this row**: the stream is Python, this is `frontend/lib/entry/**`, and the row's Change Budget is 🟢 this directory · 🟠 a session field · 🔴 **nothing.** ✅ **Stated rather than exceeded.**

### 🔴 It found a real defect on its first read — [B-230](../BUGS.md)

📁 **The design states gate 1's position as its own reason**: *"Evaluated before any workspace is loaded, **because a suspended account must not see workspace names it no longer has rights to**."* ⛔ **`resolveWorkspace` ran once before the rule walk and answered regardless**, so every gate 1 and gate 2 decision carried a resolved workspace id.

⚡ **It stayed invisible because the engine has no caller yet** — ⛔ **a leak nobody reads is a leak waiting for its first reader**, and this row is that reader: it hands the field to a bundle the row itself calls *"a data-egress surface… where tenancy is usually forgotten."* ✅ **Fixed in one expression, with the regression asserted over the whole sweep by gate number** rather than by fixture, so a future rule placed in gate 1 or 2 cannot reintroduce it.

⚠️ **And the first draft of the diagnostics fixture carried an `as EntrySession` cast that hid three wrong field names**, so a fixture describing no session at all compiled and the account-level test silently exercised gate 6. **Exactly [B-420](../BUGS.md)'s defect — a claim about a shape TypeScript believed because it was told to.** ✅ **The cast is gone and the fixtures are checked.**

---

## TASK-1412 · Settings — the audit log becomes somewhere you can go *(2026-08-10)*

⚡ **Claimed on the re-scope this lane's own finding produced.** ⛔ **The three removals were accepted rather than re-argued**: the roles matrix is [C-1416](../LANE_COORDINATION.md)'s, region and fiscal calendar are [C-1415](../LANE_COORDINATION.md)'s, and the user roster already exists at `/settings/team`.

### 🔴 What was measured before anything was built

| Deliverable | Found |
|---|---|
| **The identity block on `name`, unsourced fields designed-locked** | ⚠️ **Already built** at `/settings/organization` by TASK-468 — ⛔ **so a second one is the duplicate work [§21](../../CLAUDE.md) forbids**, the same objection Lane C accepted for the roster. ✅ **Two of the Settings design's six `workspaceFields` were missing and were added there**, locked with reasons |
| **A workspace rename to attribute** | ⛔ **There is no write path.** `workspace_tenancy`'s router publishes no `PATCH`/`PUT` on `/workspaces/{id}` — **so an `Edit` control would be the affordance-with-nothing-behind-it this surface has refused since the narration's fact count** |
| **The audit log** | 🔴 **The data existed and NOTHING could reach it** — and that is the slice |

### ⚡ The record had no door

📁 **The Settings design carries *"View audit log"* as a page action, *Audit log* as a Governance destination, and its page promise is *"Every change is attributed, reversible and visible in the audit log."*** ✅ **`GET /workspaces/{id}/history` already publishes it**, with `previous_role` and `new_role` on every entry — **which is the design's *"before and after values"*.**

⛔ **But the only surface rendering it was a section inside `/settings/team`**, so an administrator looking for an audit log had to already know it lived under *Your team*. 🔴 **That is this codebase's own CX-01 rule**, written in `settings/page.tsx`: *"a page not listed on this screen is a page nobody can reach… A closed loop with no door."* **The Connection Center was exactly that once, and this is the same defect one screen later.**

✅ **So the route and its card ship in the same commit** — the rule that file states — and **`OrganizationHistory` is reused unchanged**: ⚠️ **a second renderer of the same entries is how two surfaces start disagreeing about what a role change looked like, and an audit log that disagrees with itself is worth less than none.**

### ⛔ What the design promises that the platform cannot keep, shown locked

📁 *"Immutable · 7 years"* · *"Every entry records actor, before and after values, IP and session. Exportable to SIEM."* ✅ **Actor and before/after render.** ⛔ **IP, session, retention and export are shown designed-locked with reasons** ([D-225](../DECISION_REGISTER.md) §4).

🔴 **And no retention figure is printed.** ⚡ **Stating *7 years* would be [§20c](../../CLAUDE.md)'s mock business data on the one screen whose entire value is that it does not make things up** — **worse than absent, because a customer would rely on it in an audit.**

⚠️ **The sharpest state on this page is the failed read.** 📁 [P-A](../DOMAIN_DISCOVERY_REGISTER.md) — *a failed read must never render as an empty result* — **and on an audit log an empty list reads as *nothing happened*, which is a different and far more dangerous claim than *this did not load*.** ✅ **Both are tested, and so is the difference between them.**

---

## TASK-1402 · The intent resolver — what the person was trying to reach *(2026-08-10)*

📁 **The spec**: ***"Authentication hands over an identity AND AN INTENT — the route the person was trying to reach."*** ⚡ **Four of the twenty-four reason codes are intent codes**, so intent is a first-class input rather than a query parameter somebody remembered to forward.

✅ **The shape was already settled and is not re-decided.** 📁 `Intent` exists in [`session.ts`](../../frontend/lib/entry/session.ts) as `{ path, workspaceId, access }`, and its own comment names this file's boundary: *"⛔ Never computed here… the engine has no way to produce them — which is the point."* ⛔ **`frontend/lib/entry/intent.ts` is the producer of those four values and nothing else.**

### 🔴 Two security properties, and they are the row

#### ① A captured route must never become an open redirect

⚠️ **The classic vulnerability in exactly this feature.** **A login that faithfully returns you to where you were going is also a login that will send you to `https://evil.example` if it is told to** — and the attacker's link is indistinguishable from the honest one, because both are *"the page you asked for."*

✅ **The rule is POSITIVE rather than a blocklist**: *begins with exactly one `/`, no scheme, no control characters.* ⛔ **A blocklist of tricks is a list somebody eventually finds a gap in.** **Three refusals are worth naming because each defeats a different naive check:**

| Refused | Why the obvious check misses it |
|---|---|
| `//evil.example` · `/\evil.example` | ⛔ **They start with `/`** — *"starts with a slash"* is not the test people think it is |
| `/\njavascript:alert(1)` | ⛔ **No scheme AT THE MOMENT IT IS CHECKED.** ⚡ **The browser strips the newline and then there is one** |
| A malformed `%` escape | ⛔ **Refused rather than partially decoded** — passing it on hands the next reader a value this one could not parse |

🔴 **And the same test runs on the way back.** ⚡ **An attacker never calls `captureIntent`** — they hand the browser a crafted `?next=` — **so a sanitiser that runs only at capture protects the single path they do not use.**

#### ② `not_member` is reached WITHOUT asking whether the workspace exists

📁 **[§7](../../CLAUDE.md)**: *"A caller who is not a member of the workspace they name gets `404`, never `403`. This is a security property — it prevents workspace enumeration."*

⚡ **Applied BEFORE the question is asked rather than after it.** `classifyIntent` tests membership against the caller's own list, locally, and **only consults the server when the workspace is one of theirs** — which is why the server's answer arrives as a **callback rather than a value**: ⛔ **a value would already have been fetched.**

⛔ **The ordering is the control.** **A classifier that asked first and mapped `404` to `not_member` would be correct in its output and wrong in its behaviour** — it would have probed for a workspace the caller has no business knowing about, ⚠️ **and timing alone answers the question the status code refused to.**

✅ **Both properties were fire-tested**: removing the protocol-relative guard turns three tests red, and moving the server call ahead of the membership test turns three others red. ⛔ **A "never called" assertion passes just as well against a function nobody calls**, so the discriminating case — the same call for a workspace they ARE in — is asserted beside it.

---

## TASK-481 · Global search — the four states it owed *(2026-08-10)*

⚠️ **Two of the row's premises were already satisfied, and are recorded rather than rebuilt.** ⛔ **`CommandPalette` IS mounted** — [TASK-1442](../BACKLOG.md) landed it on ⌘K and owns it under [D-189](../DECISION_REGISTER.md) §3's whichever-lands-first rule — **and `account-search.tsx` is composed rather than rewritten**, which is what the row's *bound* requires: *"a component bent to suit one caller is slightly wrong for every other."*

### 🔴 What was genuinely missing was a real defect, and the row named it before it was met

📁 **The palette had ONE branch for an empty list**, and it read ***"Nothing matches"***. ⛔ **So a search still in flight, a search that failed, and a query nobody had typed all rendered as NO RESULTS.**

🔴 **[P-A](../DOMAIN_DISCOVERY_REGISTER.md): *a failed read must never render as an empty result*** — ⚡ **and on a search surface this is the most expensive version of that confusion.** ***"Nothing matches"* is a statement about the customer's DATA**, so somebody who reads it about a request that never completed concludes their record is gone. 📁 **[C-226](../LANE_COORDINATION.md) found the same mistake six times on one screen.**

| State | What it says, and why it is not the others |
|---|---|
| **`error`** | 🔴 *"Signora could not search just now. Nothing has changed — try again in a moment."* ⚡ **Three parts, as `StatedAbsence` established**: what failed · what is still true · what to do. **`role="alert"`, because a failure nobody hears is a failure nobody retries** |
| **`loading`** | *"Searching…"*, ⛔ **announced POLITELY** — a search that resolves in 200ms would otherwise interrupt a screen reader mid-word on every keystroke |
| **`idle`** | *"Type to search accounts, people and settings."* ⚡ **Saying *nothing matches ""* answers a question nobody asked** |
| **`ready`** | ✅ *"Nothing matches …"* — **unchanged, and asserted**, because three tests checking for its absence all pass if the sentence is simply deleted |

⛔ **A union rather than `isLoading | isError`.** ⚡ **A pair of booleans has a fourth combination that means nothing — *loading and failed at once* — and the first caller to set both decides what it renders.**

### ⚠️ `isFetching`, not `isLoading`, and the difference is the whole point

⛔ **`isLoading` is true only for the FIRST fetch of a query key.** ⚡ **Typing a second character against a cached-then-refetching query would report *ready* while a request was in flight** — **and the palette would say *nothing matches* about a search that had not finished**, which is the same defect one layer up.

### ✅ Additive, and the states only speak when there is nothing to show

⚠️ **`status` defaults to `ready`**, so every existing caller keeps its behaviour — [§20c](../../CLAUDE.md), this is *adding to the library* rather than bending a frozen component. ⛔ **And results are never replaced by a state screen**: a stale-while-revalidating search still has rows worth reading, and replacing them on every keystroke is the flicker that makes a palette feel slower than it is.

---

## TASK-482 · Ask Signora — the entry, the panel, and an honest refusal *(2026-08-10)*

📁 **App Shell §12**: ***"Four doors, one room. Wherever it opens from, the assistant inherits the current scope, states that scope above the input, and opens as a non-modal 420px drawer that pushes content. There is no floating bubble: a persistent circle in the corner is a consumer pattern and it covers data."***

✅ **`Drawer` already existed, tested, with ZERO callers**, so this **mounts it rather than building a second overlay** — 📁 the row's own *one, not two* and [D-189](../DECISION_REGISTER.md) §3's whichever-lands-first. ⚡ **It is already non-modal and already pushes content**, because §14 stated the mechanism rather than the look — **which is why it is the right primitive rather than a dialog with different padding.** ✅ **It left the reachability allowlist in the same commit, and the stale-entry test is what required that.**

### 🔴 The slice is the refusal, and the row says so

⛔ **There is no route and no request shape** — both Epic G's — and 📁 **[C-334](../LANE_COORDINATION.md) means there is no host credential.** 📁 **The Definition of Done**: *"it must state honestly when it cannot answer — a panel that renders a hopeful empty state instead of saying so is the false-affordance class this lane has refused three times."*

| ⛔ Refused | Why |
|---|---|
| **An input box** | 🔴 **A field that accepts a question nothing will answer is worse than no field.** ⚡ **Somebody types their real question, loses it, and learns the product is unreliable rather than unfinished** |
| ***"Try again"* / *"reload"*** | ⚠️ **The refusal is not an error state.** **Nothing failed — the capability is not built** — so borrowing [`StatedAbsence`](../../frontend/components/feedback/stated-absence.tsx)'s wording would be a false instruction, **exactly as it would be for [TASK-1411](../BACKLOG.md)'s absent confidence** |
| **A floating bubble** | 📁 **The design refuses one by name.** ✅ **The entry is a control in the flow of the shell's utilities** |
| ***"Everything"* as a scope** | ⛔ **A claim about what the assistant can see.** ✅ **No scope renders no scope line** |

✅ **And the refusal points at what DOES exist** — the narration, its evidence and the drawer are all shipped. ⚡ **A refusal that leaves somebody with nothing teaches them the product is empty**, which is a different and wronger lesson than *this part is not built yet*.

### ⚠️ Two of the four doors are elsewhere, deliberately

✅ **This owns the keyboard door — 📁 §15's own binding, `⌘⇧A`, read rather than chosen — and the shell's entry control.** ⛔ **The table-selection door and the explain-this-metric door belong to the surfaces that own those controls** — `table.tsx`'s AI summary row and [TASK-1411](../BACKLOG.md)'s attribution strip — **and building them here would put shell code inside a data table.**

---

## TASK-493 · Better Auth plugins — the two that actually ship *(2026-08-10)*

⚠️ **The row's central premise is half wrong, and it was measured before anything was written.** 📁 It states *"All four ship in Better Auth 1.6.25 and are UNREGISTERED"*. ✅ **`two-factor` and `multi-session` do.** ⛔ **`passkey` and `sso` do not** — `require.resolve('better-auth/plugins/passkey')` throws and neither name appears in the package.

🔴 **So two of the four are configuration and two are a NEW DEPENDENCY**, which [§6](../../CLAUDE.md) and [§21](../../CLAUDE.md) put behind an ADR — ⛔ **and the row's own budget is 🟠 one file with 🔴 nothing.** ✅ **Filed as [C-280](../LANE_COORDINATION.md); the half that ships is built.**

### ✅ Registered, and nothing configured against a design that has not spoken

| | |
|---|---|
| **`twoFactor()`** | 📁 **[§13](../../CLAUDE.md) forbids a bespoke authentication mechanism by name, and a hand-rolled TOTP loop is exactly that.** ⛔ **No issuer, digit count or window is set**: 📁 [D-185](../DECISION_REGISTER.md)'s standing rule — *"the framework should implement the product, not define it"* — **and the design has not yet said anything about second factors, so nothing is configured against it** |
| **`multiSession()`** | 🔴 **It changes no authorization.** ⛔ **[D-175](../DECISION_REGISTER.md) refuses Better Auth's organization roles permanently and this is not that**: Casbin still decides everything, `active_workspace_id` is still a routing hint re-verified server-side, and **each session verifies as its own RS256 token exactly as before** |

⚡ **Registering either changes no journey.** **They add endpoints nobody calls yet** — a person with no second factor enrolled signs in exactly as they did — **which is the row's own Definition of Done and what `auth-journey.spec.ts` proves.**

### ⛔ The test asserts the absence, and fails in the right direction

⚡ **`tests/unit/auth-plugins.test.ts` asserts that `passkey` and `sso` are NOT registered and that the package genuinely does not carry them.** ✅ **If a future upgrade ships them, the resolve-throws assertion breaks and the row becomes buildable** — ⛔ **until then it is what stops a later session quietly adding a dependency to satisfy a row that says all four ship.**

✅ **And it asserts the two the row named**: **RS256 stays pinned** ([ADR-0026](adr/0026-jwt-boundary-architecture.md)) and **no plugin brought an authorization model with it.**

---

## B-175 · A layout assertion that fails when the layout breaks *(2026-08-10)*

📁 **QE's repair instruction, and it is the whole row**: ***"a test asserting layout must assert the COMPUTED result, not the class attribute — the attribute is an input to the framework, and testing an input proves the caller's intent rather than the product's behaviour."***

⛔ **The rename did not fix these tests and was never going to.** 📁 The row says so: *"the five tests will go green again the moment the classes are renamed, while proving no more than they do today."* ✅ **That prediction was exactly right — after [B-424](../BUGS.md)'s rename all five were green again and proved nothing.**

### ⚡ It has to be a browser, because nothing else can answer

⛔ **jsdom has no stylesheet and no layout engine**, so `getComputedStyle` there returns what was set inline. **A component test cannot tell whether a Tailwind utility emitted CSS.** ✅ **[`auth-layout.spec.ts`](../../frontend/tests/e2e/auth-layout.spec.ts) compares the same element across two viewport widths** — radius across the `phone` floor, padding-top across it, justification across `smalllaptop`.

⚠️ **Each assertion compares two widths rather than pinning a value.** ⛔ **An absolute expectation — *the radius is 12px* — would pin a design decision**, and the question here is whether the band applies at all.

### 🔴 The fire-test is the evidence, and it discriminates

✅ **Renaming the `phone` band out of `tailwind.config.ts` turns 2 of the 3 layout tests RED**; restoring it returns all 5 to green. ⚡ **The `smalllaptop` test correctly stayed green**, because only the phone band was broken — **so the suite fails on the thing that broke rather than wholesale.**

⚠️ **One locator detail is load-bearing**: the card is found **two levels up from the `<h1>`**, the way the component test finds it — ⛔ **a selector built from `phone:rounded-xl` would match only when the class is present, so the test would pass by not running.**

### ✅ The five className assertions are kept and relabelled, not deleted

⛔ **A missing class is cheap to catch in a component test; a class that emits nothing can only be caught in a browser.** ⚡ **Both are worth having** — the block is now titled *intent, not layout* and points at the browser test, **so neither claims to be the other.**

---

## TASK-452 · Saved View — the consumer that owns the declaration *(2026-08-10)*

🔴 **Measured before anything was written**: 📁 **`workspace_tenancy` publishes four saved-view endpoints** — list/create, read/update, `retirement`, `revisions` — ⛔ **and ZERO files under `frontend/` mentioned any of them.** ⚡ **A complete backend capability with no door**, which is the class `settings/page.tsx` already named: *"a page nobody can reach… a closed loop with no door."*

### ⚡ The declaration belongs to the consumer, and 455 says so twice

📁 **[455 §4](455-context-definitions-r02-r03.md)**: ***"Never parses, validates, executes, ranks or optimises a declaration. Never knows what a filter or a sort means."*** **The store keeps an opaque `dict`** — *"stores the query, the filters and the sort — not the results"*.

⛔ **That cuts both ways.** **Nothing on the server will ever tell a screen that a declaration is wrong**, ✅ **so the screen has to be the thing that refuses one it does not understand.** `lib/views/working-list.ts` is that, for this consumer.

📁 **And one consumer, deliberately**: *"a contract proven by one real caller before six adopt it… a port with seven simultaneous first callers has no chance of being corrected cheaply."* ✅ **The working list is that caller** — its three URL params, `owner` · `raises` · `by`, **are the declaration**, and the URL is already where this screen keeps them.

### 🔴 Three refusals, and the reason each is a refusal rather than a best effort

| | |
|---|---|
| **Another screen's view** | ⚡ **The commonest real case, and not an error.** 📁 The store is workspace-wide and 455 names four consumers, **so a Reports view and a working-list view sit in the same list** — ⛔ **opening one on the other would silently show the wrong records** |
| **A newer Signora's view** | 🔴 **Partly applying is the worst outcome**: **the customer gets a list that is neither what they saved nor what they asked for, and nothing says so** |
| **Not a declaration at all** | ⛔ Refused, not coerced |

✅ **`whyNotApplicable` returns a SENTENCE rather than a boolean**, because the screen has to say *which* view it cannot open — 📁 `LockedField`'s rule: *a lock with no reason is worse than an absent field.*

⚠️ **An OLDER version stays readable, deliberately.** ⛔ **The version is bumped only when an old declaration would be MISREAD — not when a filter is added** — **because a missing key means *not narrowed*, which is what those views meant when they were written.**

### ⛔ Two smaller decisions worth recording

**A default is not written into the URL.** ⚡ A URL carrying every default is one nobody can read at a glance, and `scopeFrom` already answers `all` for a missing value.

**A view nobody named is never *"Untitled"*.** 📁 The store bounds a name at 200 characters *"long enough for a sentence a person would actually type"* — ✅ **so the default describes the filters**, and somebody scanning a list of views can tell them apart.

---

## TASK-1417 · Reports — one definition, three renderings *(2026-08-10)*

🔴 **Measured before anything was written, and the measurement changed the slice.** ⛔ **There is no `frontend/app/(app)/reports/` route, no reports module in `backend/modules/`, and `ai_platform` publishes exactly ONE endpoint** — `account_narration`, scoped to an account. ⚡ **So the row's line *"scheduling, exports and sharing each need a capability that does not exist"* was one item short: generating the narrative has nothing behind it either.**

### ✅ A report is stored as a saved-view declaration, and nothing new was built to hold it

📁 **[455 §4](455-context-definitions-r02-r03.md) names the consumers of the saved-view store**: *"Companies · App Shell · Global Search · **Reports**"*, and the store keeps *"the query, the filters and the sort — **not the results**"*. ✅ **That is a report definition exactly** — **no new table, no new module, no new endpoint** — and 📁 the store's lifecycle is already the design's: *"a declaration is never edited; a change is a new version naming the one it replaces"* beside the design's own ***"v7 · autosaved"***.

⚡ **Reports is the SECOND consumer**, which is why the three refusals moved to [`lib/views/declaration.ts`](../../frontend/lib/views/declaration.ts). 📁 **455 §4 asked for one caller first** — *"a contract proven by one real caller before six adopt it"* — ✅ **[TASK-452](../BACKLOG.md)'s working list was that caller, and two callers is where the shared half stops being speculation** ([§6](../../CLAUDE.md)). ⛔ **Only the refusals are shared; each screen still owns its own declaration shape**, because the refusals are about the STORE — workspace-wide, opaque, outliving the build that wrote a row — rather than about any screen.

### 🔴 The row's named risk was *"three renderers"*, and it is refused by the types

📁 **The design's acceptance sentence**: ***"The same blocks, re-laid out — never a separate deck to maintain."*** ⛔ **A second renderer would satisfy a screenshot review** while creating exactly the maintenance burden that sentence exists to prevent.

✅ **`LaidOutBlock` carries a `ReportBlock` taken from the definition and has no field into which a title, a figure or a sentence could be introduced.** ⚡ **There is nowhere to put invented content** ([§2](../../CLAUDE.md): *prefer a violation that is unrepresentable over one that is merely discouraged*), **so a mode decides which blocks appear, in what order, at what scale — and never what they say.** **A test asserts it as a property across all three modes rather than by reading the code.**

| Mode | What it does | 📁 Why |
|---|---|---|
| **Builder** | Everything, in the author's order, hover available | The divider means something here: it is where the author put a break |
| **Presentation** | Drops the divider and **only** the divider · `pointerAvailable: false` | *"One idea per slide"* — the slide boundary IS the divider. **A figure available only on hover does not exist in a room with a projector** |
| **Executive** | At most three, ordered by CLAIM · **every chart withheld and counted** | *"Three points maximum, each a claim rather than a topic"* · *"No chart unless it changes the decision"* |

⚠️ **Charts are withheld rather than included on a guess.** ⛔ **Nothing in the product can currently decide whether a chart changes a decision**, and including them would make executive mode a shorter builder, which is not what the design asks for. ✅ **`withheld` is a COUNT** — 📁 the design's own sharing rule, *"withheld with a count, never silently dropped, so totals stay honest"*, applied to a mode that deliberately shows less.

### ⚠️ A fire-test found one of these assertions decorative, and that is recorded rather than quietly fixed

⛔ **The first *"executive withholds every chart"* test passed with the rule REMOVED.** ⚡ **Its fixture had three non-chart blocks, so the cap of three excluded the chart whether or not the rule existed.** ✅ **A second fixture with two blocks, one of them a chart, is what the rule alone can satisfy** — **and admitting charts to the priority list now turns it red.** 📁 **[§2](../../CLAUDE.md)'s Decorative Logic, found the way it is always found: by removing the thing and watching nothing happen.**

### 🔴 The narrative's merge is built; its generation is [C-283](../LANE_COORDINATION.md)

📁 **The design's guarantee**: ***"Edited sentences are preserved through regeneration and marked, so the board sees what a person asserted versus what the model derived."*** ✅ **`regenerate` takes the incoming sentences as an ARGUMENT — it calls nothing, awaits nothing and knows no model** — **so the law is testable today.**

⛔ **Three things a regeneration may never do**: **① delete a sentence a person wrote** · **② relabel one as generated** — ⚠️ **the quieter failure, because the text is still on the page and the board is now told a human judgement came from the model** — · **③ move one**, since the narrative is an argument in order.

⛔ **Generating it is refused rather than approximated.** 📁 **[§10](../../CLAUDE.md): no mock provider, no fabricated inference** — **a template producing plausible sentences would be indistinguishable from a working narrative.** 🔴 **The ids are the contract C-283 must honour**: matching on text would treat a person's edit as a deletion plus an insertion, which is the outcome ① forbids.

### ⚡ The picker recommends from the shape, and the order of the checks IS the logic

📁 ***"The picker recommends a type from the shape of the data and explains why. No doughnuts, no dual axes, no 3D."*** ✅ **The three refusals are refused by `ChartType` having eight members** — ⛔ **a caller cannot ask for a doughnut, so no guard has to remember to say no** ([§2](../../CLAUDE.md): *a guard that cannot fail is documentation pretending to be code*).

⚠️ **Specific before general, and it is load-bearing.** ⛔ **A bridge's data is ALSO a comparison across categories, and a pace chart's is ALSO a measure over time** — **testing the general case first recommends `bar` for a bridge and `line` for a pace chart, both defensible, both wrong, and neither ever reported as a defect because a chart drew fine.** ✅ **Fire-tested by moving the general case to the top: five tests red.**

### ♿ Reordering is a pure function, so the pointer is one caller and never its owner

🔴 **The row**: ***"Drag-to-reorder MUST have a keyboard equivalent — a drag-only builder is unusable without a mouse."*** ⛔ **A reorder implemented inside a drag handler is a reorder a keyboard cannot reach**, which is how a builder becomes mouse-only without anybody deciding it should be. ✅ **`reorder` returns the SAME array when the move is impossible**, so identity is the signal and a focus announcement is not made for a move that did not occur.

### ⏸️ Named as remaining, not implied

⛔ **Scheduling · exports · sharing** — 📁 the row's own three, *"a job runner, a rendering pipeline, and a link with its own authorization"*. ⛔ **The narrative's generation** — [C-283](../LANE_COORDINATION.md). ⛔ **The query engine** — **`ReportQuery.produces` carries what a server will one day answer; the MECHANISM of the design's refusal is built, and the vocabulary of measures arrives with the engine that produces them.**

### 🔴 `/reports` ships a designed empty state, and the rail entry was a correction

⛔ **[§20c](../../CLAUDE.md): *"Never introduce mock business data. Screens without a shipped module behind them ship a designed empty state."*** 📁 **The design's screen is a Q3 board pack** — *"$42.8M commit"*, *"−$2.4M vs. Friday"*, *"3,104 opportunities"*, three named deals — ⚠️ **every figure from a query engine that does not exist.** ⛔ **A screen showing a plausible $42.8M would be indistinguishable from a working report tool, and somebody would eventually carry a figure from it into a meeting.**

✅ **What ships instead**: **the empty state, in the customer's words** — *"a report starts with one question… Signora cannot answer one across your pipeline yet"* — **and the chart library**, ⚡ **which is finalized product copy about what Signora draws and contains no customer data at all.** **A test names each refused figure literally**, so a reader can check the list against the design file rather than trusting a regex, **and adding one to the screen turns it red.**

⚠️ **The rail entry was added after this lane decided against it, and the repository was right.** ⛔ **The reasoning for holding back was this file's own warning** — *"at M12.3, three of six said `coming soon` on the screen a customer sees first"* — 🔴 **and `reachability.py` refused it: *"no entrance at all: 1 ← every one is a defect."*** ⚡ **The distinction the caution missed**: *coming soon* **is a screen that does not exist**; this one resolves and explains itself. ✅ **A route a customer cannot reach is the worse of the two**, and the journey now walks the door rather than typing the URL.

### 🔴 [B-233](../BUGS.md) — found by the headed review, not by the suite

⚡ **[D-134](../DECISION_REGISTER.md)'s headed review is *"continuous product review"* rather than verification, and this is what that buys.** ⛔ **Every authenticated screen carried a failure band** — 📁 *"Signora could not load the navigation"* — **at every viewport width**, and **2696 tests were green.**

🔴 **`MobileNavigation` mapped `RAIL_DESTINATIONS` raw** while `Navigation` resolved `[workspace]` and dropped an entry it could not fill. ⛔ **A dynamic href throws in the App Router**, and the phone bar is hidden with `smalllaptop:hidden` — **CSS, not conditional rendering** — **so it is mounted and throwing on a 1280px desktop.**

⚠️ **The file claimed *"one source, two renderings"* and meant the LIST.** ✅ **`resolved()` is shared now**, which is what that sentence had to mean to be true. 📁 **And the reason no test caught it is the useful half**: `mobile-navigation.test.tsx` **did not stub the workspace provider at all**, so **the renderer that was broken was the one nobody asked the question of.** ✅ **The third regression test is the general form** — ⚡ ***no rendered href contains `[`*** — because the defect was never about Home.

### ⚠️ Twelve red journeys that were this lane's database, not this repository

⛔ **Recorded because I nearly filed it as a defect.** **Six accessibility and six consistency journeys failed while [TASK-1417](../BACKLOG.md) was being verified**, and **none of them touched anything the slice changed.**

✅ **Established as pre-existing by measurement rather than by argument**: **the change was stashed and the same specs re-run.** ⚡ **The count went from 12 red to 13 red** — **[B-233](../BUGS.md)'s fix had turned one of them green** — **which is also the strongest evidence that B-233 was real.**

🔴 **Then established as NOT a repository defect at all.** 📁 **The twelve accounts every one of those journeys reads come from `tests.playground.seed`** — *"twelve accounts through the real pipeline"* — **and this lane's `signora_lane_a` had never been seeded, or had been truncated by `make test`.** ✅ **Seeded through that same approved door and re-run: 21 of 21 green.**

⚡ **The correction is to how this lane runs the suite, and the tooling already had it right.** 📁 **`make e2e` re-seeds and then runs Playwright**, in one target, *"so a run is reproducible"*. ⛔ **Running `npx playwright test` directly skips the seed**, which is what produced twelve failures that looked like product defects. 🔴 **[§20e](../../CLAUDE.md) is explicit about the trap on the other side**: ***a workstation gap must never be recorded as a repository defect*** — **so the row that was not written is the correct outcome here.**

---

## TASK-1433 · The utility panel — the dock is the shell's, the content is not *(2026-08-10)*

🔴 **The row names its own risk and it decided the shape of everything below**: ⚠️ ***"Building the chrome because it is the easy half. The chrome is not the deliverable."***

✅ **So the acceptance test is the Activity tab rendering `AccountHistory` on the account record**, and it is checked in a browser: **the panel docks at 300px, the content narrows, the tab carries the account's real history, and the section that used to hold it stands down.**

### ⚡ Measured first, and the measurement changed the work

📁 **`AccountHistory` already existed** — [`components/timeline/feed.tsx`](../../frontend/components/timeline/feed.tsx), with its own loading, empty and error states — **and was already mounted on the account record.** ⛔ **So this row was never *build a history*; it was *give the history a dock*, and the risk was building a panel and calling that done.**

### 🔴 The panel is not the only home for what it holds, and that is the load-bearing rule

📁 **Below 1024 the design gives the panel no width at all.** ⚠️ **A module that put its ONLY copy of something in the panel would lose it entirely on a phone** — ⛔ **and the design never says the CONTENT disappears, only the panel.**

✅ **`useUtilityPanel` therefore reports `carrying`**, and the account record renders the history inline when the panel is not taking it. ⚡ **One component, one data source, two placements decided by the band** — ⛔ **never two copies, and never both at once.** **A journey asserts both halves: at 1440 the body section is absent, at 390 the panel is absent and the section is there.**

### ⛔ Three defects of my own, each found in a browser and none by a test

| | |
|---|---|
| **The panel floated instead of docking** | ⚡ **The provider rendered it, and the provider wraps the whole shell** — so it landed *after* the frame's flex row and the rail's `Settings` link sat on its tabs. ⛔ **Playwright reported it as *"intercepts pointer events"***. ✅ **Placement moved to the layout (`UtilityPanelDock`) and state stayed with the provider**: a panel that *pushes* has to be a sibling of what it pushes |
| **[B-234](../BUGS.md) — two `complementary` landmarks** | 📁 **The design's table gives the rail `nav[navigation]` and the panel `aside[complementary]`.** ⚠️ **The rail's wrapper was an `<aside>`** — harmless while it was the only one, **a collision the moment the panel mounted.** ✅ **One element changed; fire-tested by restoring the `<aside>`** |
| **The stored preference clobbered the toggle** | ⛔ **`⌘.` pressed just after a route change did nothing**: the hydration effect was still queued and wrote the stored `false` over the `true` the keypress had set. ✅ **Hydration now happens once per module and never after a deliberate action** |

### ⚠️ And one thing that looked like a defect and was the feature

⛔ **A journey that clicked through from the attention list and pressed `⌘.` immediately kept failing.** ⚡ **The panel *"remembers its open state per module"***, so a keypress landing mid-navigation toggles the module being LEFT, and the arriving module then applies its own memory. ✅ **That is correct**, and 📁 **the journeys now enter by deep link** — which is the design's own reason for mandatory breadcrumbs: *"most sessions start from a deep link in Slack or email."*

### ✅ The skip link the shell owed since [TASK-1444](../BACKLOG.md)

📁 **Rule 2.4.1 names three targets**: content, navigation, **the utility panel.** ⛔ **The third was absent because the panel did not exist**, and [`skip-links.tsx`](../../frontend/components/shell/skip-links.tsx) said so. ✅ **It exists now** — ⚡ **and the link is CONDITIONAL rather than simply added**, because the file's own rule still binds: *a skip link to a missing landmark sends a keyboard user nowhere.* **The panel is absent below 1024, so both read one source and cannot disagree.**

### ⏸️ Named as remaining

⛔ **Insights and Notes carry the panel's own empty state and no content**, which is what the row asked for: *"tab stubs only if the design's own empty state is used; never invented copy."* **They gain content when a module publishes into them.**

---

## TASK-1415 · Account 360 — measured before it was built *(2026-08-11)*

🔴 **The row claims every section is *"a composition of intelligence the platform ALREADY produces"*.** ⚠️ **That is half true, and building on the claim would have invented the other half.**

✅ **Measured against the three modules that publish reads** — `hooks.ts`, `hooks/commercial.ts`, `hooks/timeline.ts` — **eight of the design's fifteen sections have one and seven do not**: customer health · buying intent · the organisation chart · the relationship graph · the technology stack · market signals · meetings.

### ⛔ The seven are RENDERED, not omitted

📁 **[§20c](../../CLAUDE.md)**: *"screens without a shipped module behind them ship a designed empty state"* — ⛔ **and an omission is not one.** ⚠️ **A page that silently left them out would be indistinguishable from a page with a bug**, and a rep who has seen the design would read a missing section as a broken screen.

🔴 **An absent section is NOT an empty one**, and 📁 [P-A](../DOMAIN_DISCOVERY_REGISTER.md) is the reason: **empty means *this account has none*; absent means *Signora cannot answer at all*.** ⚠️ **A rep who reads the first when the second is true concludes their account is quiet** — a commercial decision made on a false reading. ⛔ **And never *"coming soon"*** — the rail already paid for that at M12.3.

### ⚠️ Three defects of mine, and two were found by looking rather than by testing

| | |
|---|---|
| **Platform vocabulary in customer copy** | ⛔ Three absence sentences said *"workspace"*. 📁 [ADR-0034](adr/0034-ubiquitous-language.md): a customer says **Organization**. **Caught by my own test** |
| **The reads live in THREE modules and I checked one** | ⚠️ `useBuyingCommittee`, `useCompetitors` and `useAccountTimeline` are not in `hooks.ts`. ⛔ **Two files' worth of claims went unverified** until the test named them |
| 🔴 **The rail linked to nothing** | ⚠️ **Found in a headed review.** **Only the ABSENT sections carried an id**, so *Account score* and *Summary* were links to nowhere — ⛔ **precisely the defect the component was written to prevent, one level up.** ✅ **The rail now takes the ids the page actually renders and links to nothing else** |

### ⏸️ Named as remaining, not implied

⚠️ **`supplied` means a READ exists — not that this page renders it.** ⛔ **Three sections have reads and no section here yet**: *Open opportunities*, *Contacts & decision makers*, *Competitors*. **They are not in the rail**, because a link to nothing is the defect above.

⛔ **The seven absent sections render as a block after the existing content rather than interleaved in the design's order.** ⚡ **Interleaving needs the page restructured around the section list**, which is the larger Account 360 rebuild rather than this increment — **stated here so the next assignee does not read the current order as the design's.**

---

## TASK-1418 · AI Research — measured, and the law that moved *(2026-08-11)*

🔴 **The finding is the shape of the ask, not a count of gaps.** 📁 **`ai_research_engine` publishes two endpoints and research is scoped to an ACCOUNT.** ⛔ **The design's subject is a QUESTION** — *"Why is EMEA enterprise slipping?"*, scoped to a segment and a quarter — **and nothing in this product can be asked anything.** ⚠️ **Raised as [C-284](../LANE_COORDINATION.md) rather than built around**: a `/research` route with a question box would be [§20c](../../CLAUDE.md)'s failure in its worst form — **not an empty state over an unbuilt list, but a control that invites the product's headline promise and cannot honour it.**

### ✅ What already ships, which is why this is scoped rather than blocking

📁 **`ResearchPanel` surfaces every published feature** — the answer, its findings, the prompt, the model, the evidence digest, and `requested`/`running` with polling — **and already distinguishes a failed read from *nobody has asked***, which is [P-A](../DOMAIN_DISCOVERY_REGISTER.md). ⛔ **Rebuilding it would be the hybridisation [D-229A](../DECISION_REGISTER.md) forbids.**

### ⚡ `partial` is its own answer and is never collapsed into `absent`

⚠️ **`running` really is published**, and the read already polls while it holds; **what is missing is the design's *"step 4 of 5 · 8.4s elapsed"*.** ⛔ **Rendering that as absent would understate what the product does** — **the same failure as overstating it, in the other direction.**

### 🔴 The edit law moved on its second caller, and not before

📁 **Both designs write the same sentence.** **Reports**: *"edited sentences are preserved through regeneration and marked."* **AI Research**: *"Editable · your edits are preserved through regeneration."* ✅ **So the merge moved to [`lib/research/edits.ts`](../../frontend/lib/research/edits.ts)** — the discipline [455 §4](455-context-definitions-r02-r03.md) states for a port and [`lib/views/declaration.ts`](../../frontend/lib/views/declaration.ts) already followed: *"a contract proven by one real caller before six adopt it."*

⚡ **The extraction is behaviour-preserving and its own tests prove it**: `report-narrative.test.ts` passes **unchanged** against the moved law.

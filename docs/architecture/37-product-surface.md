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

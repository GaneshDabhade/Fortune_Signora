# 450 · Global Search — screen-by-screen traceability audit

**Lane C · Product Office · 2026-08-05.** **Sixth audit under [D-078](../DECISION_REGISTER.md)**, extended through [D-083](../DECISION_REGISTER.md).

**Screen 14 of 16** — *"One doorway, two exits, never a second search box"* ([410](410-approved-ui-specification.md)).
**Two rows are already in flight here** — [TASK-301](../BACKLOG.md) `IN VALIDATION`, [TASK-408](../BACKLOG.md) `IN PROGRESS`.

---

# 0 · The finding: the searchable set and the entity set were designed independently

| | |
|---|---|
| **The screen searches four types** | **Accounts · people · calls · deals** |
| **`EntityKind` has two members** | **`COMPANY` · `TECHNOLOGY`** |
| **They overlap in exactly one** | **Company/account.** ⚠️ **`TECHNOLOGY` is a first-class entity the screen never searches, and three of the screen's four types are not entities at all** |

**And the three absent types are absent for three *different* reasons, which is the useful half:**

| | | |
|---|---|---|
| **People** | 🔴 **Not an entity yet** | **[R-01](../DOMAIN_DISCOVERY_REGISTER.md)** — `EntityKind.PERSON` is [TASK-427](../BACKLOG.md)'s first line |
| **Deals** | 🟡 **A domain aggregate that is not a graph entity** | **`Opportunity` exists and is queryable.** ⚠️ **It is not in the graph and does not need to be** — searching deals is a read over `opportunity_engine`, not a new `EntityKind` |
| **Calls** | ⛔ **No source, external** | [MC-10](../PRODUCT_EXPERIENCE.md) — activity capture, evidence-gated |

> **So *"1 of 4 object types"* — [411](411-ui-convergence-assessment.md)'s figure — is right about the screen and misleading about the work.** **The four types need three different mechanisms**, and only one of them is *"add an `EntityKind`."*

---

# 1 · ⚠️ The second finding: there is no search index

**Measured across `modules/` and `signora_platform/`, excluding tests:**

> **`meilisearch` — 0. `tsvector` — 0. `trigram` — 0. `ILIKE` — 1.**

**Search today is one SQL `ILIKE` behind `GET /account-search`.** **That is correct for what it does** — one type, exact-ish name matching, and [C-020](../LANE_COORDINATION.md)'s Meilisearch question is **deferred by the product owner with a stated trigger**: *the first customer asking to search or facet a timeline rather than scroll it.*

| | |
|---|---|
| **What the approved screen asks for** | **Typed grouping · explainable ranking · four types · saved and monitored searches** |
| **What `ILIKE` supports** | **One type, and no ranking to explain** |
| ⚠️ **The honest consequence** | **[TASK-408](../BACKLOG.md) is `IN PROGRESS` and its title is *"search results are grouped and the ranking is explainable."*** **A ranking that is one `ILIKE` is explainable trivially — *it matched the name* — and that may be exactly right for one type and cannot survive four** |

> **This is not a gap to fill. It is a trigger to watch**, and [C-020](../LANE_COORDINATION.md)'s trigger was written for the timeline rather than for search. **Recommendation: the trigger should read *the first search that must rank across more than one type*, which is a checkable condition and arrives with People rather than with a customer complaint.**

---

# 2 · The traceability matrix

✅ exists · 🟡 extend · 🟠 conflicts · 🔴 missing · ⬜ not yet extractable

| UI element | Business meaning | Source of truth | Audit | Owner | Consumers | Priority |
|---|---|---|---|---|---|---|
| **One search box** | A single doorway into everything | **Projection** — `account-search` | ✅ **Built** | `knowledge_graph` | Global Search · App Shell | — |
| **"Never a second search box"** | **A product invariant, not a feature** | **Architectural pattern** | 🟡 **Nothing enforces it.** ⚠️ **`components/ui` has no rule against a page-local search**, and the frontend vocabulary test is the precedent for one | Product Surface | **All 16 screens** | **§5** |
| **A result says what kind of thing it is** | Typed results, grouped | **Projection** | 🔨 **[TASK-301](../BACKLOG.md) `IN VALIDATION`** | `knowledge_graph` | Global Search | — |
| **…and why it matched** | **Explainable ranking** | **Value object** — a match reason | 🔨 **[TASK-408](../BACKLOG.md) `IN PROGRESS`.** ⚠️ **See §1** | `knowledge_graph` | Global Search | — |
| **Accounts** | Companies this workspace watches | `EntityKind.COMPANY` | ✅ | `knowledge_graph` | — | — |
| **People** | Somebody at a target account | `EntityKind.PERSON` | 🔴 **[R-01](../DOMAIN_DISCOVERY_REGISTER.md)** — and it is **[TASK-427](../BACKLOG.md)'s first line**, so this screen is unblocked by M-D alone | `people` | 5 screens | **Wave 1.5** |
| **Deals** | An open or closed commercial pursuit | **Aggregate** — `Opportunity` | 🟡 **Exists, queryable, and *not a graph entity*** — searching it is a read over `opportunity_engine`, **not a new `EntityKind`** | `opportunity_engine` | Global Search · Exec Dashboard | **After typed grouping** |
| **Calls** | A recorded conversation | **External provider** | ⛔ **Evidence-gated** — [MC-10](../PRODUCT_EXPERIENCE.md) | — | Global Search · Opportunity Intelligence | — |
| **Saved and monitored searches** | *"A saved search stores the query, the filters and the sort — **not the results**"* | **Aggregate** — the saved-view store | 🔴 **[R-02](../DOMAIN_DISCOVERY_REGISTER.md).** ⚡ **And this screen supplies the sharpest definition of it yet** — §4 | ⚠️ Undecided | **4 screens** | **[TASK-433](../BACKLOG.md)** |
| **A monitored search** | *"Tell me when this query's answer changes"* | **Workflow** — a standing query with delivery | 🔴 ⚠️ **Not the same as a saved search, and [442 §F9](442-product-led-domain-discovery.md) grouped them.** §3 | ⚠️ Undecided | Global Search | **After [R-02](../DOMAIN_DISCOVERY_REGISTER.md)** |
| **A natural-language question routes to the assistant** | *"Never returning rows"* | **Domain rule** — an intent boundary | 🔴 **[R-12](../DOMAIN_DISCOVERY_REGISTER.md)** — **the verb taxonomy decides what "a question" is**, and [C-419](../LANE_COORDINATION.md) is that item | `ai_reasoning_engine` | Global Search · Copilot | **[C-419](../LANE_COORDINATION.md)** |

**Eleven elements: 2 ✅ · 2 🔨 · 3 🟡 · 4 🔴.**

---

# 3 · ⚡ Splitting a register entry: a monitored search is not a saved search

**[442 §F9](442-product-led-domain-discovery.md) listed *"saved and monitored searches"* as one consumer of [R-02](../DOMAIN_DISCOVERY_REGISTER.md). Auditing the screen separates them.**

| | | |
|---|---|---|
| **A saved search** | *"Stores the query, the filters and the sort — **not the results**"* | **A stored declaration. Nothing runs.** ✅ **[R-02](../DOMAIN_DISCOVERY_REGISTER.md)** |
| **A monitored search** | *"Tell me when this answer changes"* | **A standing query, re-evaluated, with delivery.** ⚠️ **That is not the saved-view store — it needs a trigger and a notification, and [ADR-0040](adr/0040-notifications.md) is deferred** |

> **The same word joined two concepts, exactly as `Segment` did on Companies** ([446 §0](446-companies-traceability-audit.md)). **The difference is that this one *is* extractable** — the design project states what a saved search stores, and *"not the results"* is decisive.
>
> ✅ **So [R-02](../DOMAIN_DISCOVERY_REGISTER.md) keeps saved searches and *loses* monitored ones**, which belong behind [ADR-0040](adr/0040-notifications.md). **The register gets smaller, and the deferred item gets one more named consumer.**

---

# 4 · The sharpest definition of R-02 yet, and it comes from here

**Four screens assert the saved-view concept and each states one property. Together they are a specification:**

| Screen | Property |
|---|---|
| **Companies** | *"Pinning is per view, not per user — **so a shared view looks the same for everyone**"* → **shared, not a preference** |
| **App Shell §6** | *"Survives navigation, **serialises to the URL**, and can be saved as a named view"* → **the state is a URL, and the entity is a name for one** |
| **Global Search** | *"Stores the query, the filters and the sort — **not the results**"* → **a declaration, never a materialisation** |
| **Reports** | *"Views are shared by link and **respect each viewer's permissions**"* → **evaluated per reader, at read time** |

> ## **Four unrelated screens, four properties, and no contradiction between them.**
>
> **A saved view is a named, shared, immutable declaration of a query, evaluated per reader at read time.** **Nobody wrote that sentence; four screens did, independently.**
>
> ⚡ **And it is [P-B predicate-over-stored-state](../DOMAIN_DISCOVERY_REGISTER.md) again** — *"not the results"* and *"respect each viewer's permissions"* both say **evaluate, never store.** **The same pattern that removed R-03's scheduler defines R-02's entity.**

---

# 5 · ⚖️ Challenging the implementation — *"never a second search box"*

**The screen states an invariant about the whole product, and nothing in the repository can enforce it.**

| | |
|---|---|
| **The precedent that fits exactly** | **`frontend/tests/components/vocabulary.test.tsx`** — *"a glossary nobody can violate is documentation pretending to be code"* — and **`design-tokens.test.tsx`** and **`no-mock-data.test.tsx`**, both structural refusals |
| **The recommendation** | **A structural test that refuses a second search input outside the shell.** **Cheap, and it is the fourth instance of a pattern the frontend already uses three times** |
| **What it is not** | ⛔ **Not a backend capability.** **Product Surface's, and 🟢 in the Change Budget** |

---

# 6 · Findings

| | |
|---|---|
| **Existing and correctly modelled** | `account-search` · `EntityKind`'s two members · `Opportunity` as a queryable aggregate · [TASK-301](../BACKLOG.md) and [TASK-408](../BACKLOG.md) in flight |
| **Extension candidates** | **Deals searchable as a read over `opportunity_engine`, not a new `EntityKind`** · **a structural test for the single search box** |
| **Architectural evolution** | ⚠️ **[C-020](../LANE_COORDINATION.md)'s Meilisearch trigger is written for the timeline and should read *the first search that must rank across more than one type*** |
| **Missing foundational capabilities** | ⛔ **None new.** [R-01](../DOMAIN_DISCOVERY_REGISTER.md) and [R-02](../DOMAIN_DISCOVERY_REGISTER.md), both already carried |
| **Missing workflows** | **A monitored search** — behind [ADR-0040](adr/0040-notifications.md) |
| **Missing entities** | **`EntityKind.PERSON`** — [TASK-427](../BACKLOG.md)'s first line |
| **Missing business events** | ⛔ **None.** ✅ **Search has no completion point — nothing is decided by searching**, which is [R-14](../DOMAIN_DISCOVERY_REGISTER.md) correctly *not* firing |
| **Missing permissions** | ⛔ **None new.** ⚠️ **But Reports' *"respect each viewer's permissions"* means a saved view is evaluated per reader** — which is [R-13](../DOMAIN_DISCOVERY_REGISTER.md)'s **field** dimension arriving from a fourth direction |
| **Missing projections** | **Typed grouping across four types** — [TASK-408](../BACKLOG.md) |
| **Missing platform capabilities** | ⛔ **None** |

---

# 7 · Cross-screen convergence

| | Screens | Change |
|---|---|---|
| **[R-02](../DOMAIN_DISCOVERY_REGISTER.md)** | **4** | ⚡ **Defined**, by four screens each contributing one property — §4. **And narrowed**: monitored searches leave it |
| **[R-01](../DOMAIN_DISCOVERY_REGISTER.md)** | **6** | ✅ **Confirmed again.** **Unblocked by M-D alone here** — a searchable person needs an identifier, not a name |
| **[R-13](../DOMAIN_DISCOVERY_REGISTER.md)** | **4** | 🟡 **Field-level authorization arrives from a fourth screen** — *"respect each viewer's permissions"* |
| **[R-12](../DOMAIN_DISCOVERY_REGISTER.md)** | **2** | ✅ **Confirmed** — *"a natural-language question routes to the assistant"* **is the verb taxonomy deciding what a question is** |
| **[R-15](../DOMAIN_DISCOVERY_REGISTER.md)** | — | ⬜ **No instance found here.** **Recorded, because a pattern that appears everywhere is a pattern nobody is testing** |

---

# 8 · What this produces

**No new backlog row.** **What it changes:** **[R-02](../DOMAIN_DISCOVERY_REGISTER.md) is defined and narrowed** · **[R-13](../DOMAIN_DISCOVERY_REGISTER.md) gains a fourth screen** · **[C-020](../LANE_COORDINATION.md)'s trigger is challenged** · **deals are re-classified out of `EntityKind`** · **the single-search-box invariant gets a testable form.**

---

# 9 · What this document did not do

**Nothing implemented · no lane named · no wave reordered · no module created · no ADR drafted · no queue file touched · no backlog row added.** **And it did not reopen [C-020](../LANE_COORDINATION.md)** — the deferral stands; **only its trigger is questioned, with a checkable alternative.**

# 51 — Implementation Specifications

> **The continuation of [50 — Product Capability Audit](50-product-capability-audit.md) §5**, dated 2026-08-03, by Lane B.
>
> **Each specification is written so a lane can claim it and start.** Objective · customer problem · customer value · existing foundation · modules · backend · frontend · UX · API · events · data model · acceptance criteria · risks · dependencies · effort · future evolution.
>
> **A specification no longer names a lane** (product owner, 2026-08-03). **Ownership is an operational decision and a specification is a durable one**, so embedding the first in the second dates the second the first time anything is reassigned — which happened to five of these within a day of writing them. Who builds it lives on the [execution board](../ACTIVE_ASSIGNMENTS.md); what it is lives here. The `Lane` rows below are struck rather than deleted, because a dated record of what was true then is not rewritten to match now (`CLAUDE.md` §2).
>
> **Nothing here is built.** Where a specification names a file, a schema or an event, it was read from the repository rather than assumed — and one slice was deleted during writing because it turned out to be finished already.
>
> ### Corrected 2026-08-03, before implementation began
>
> **That sentence was already wrong when it was written, and re-verifying the specifications against another lane's branch is what found it.** The audit behind this document read `integration` and the registers. It did not read `origin/lane-a-product-surface`, which was 128 files and ~19,000 lines ahead — and **two of Epic A's slices were being built there.**
>
> | Slice | Status, verified 2026-08-03 |
> |---|---|
> | **A2** · the accounts workspace | **Struck.** Lane A's `SW-01`…`SW-04` deliver it — `TriageStrip`, `lib/state/triage.ts`, URL-driven narrowing |
> | **B2** · the first-run path | **Struck.** Built by Lane A against D36; `first-run.test.tsx` |
>
> **The lesson is the same one C-024 taught, one level up.** A register can describe a gap somebody has closed; **so can a specification, and a specification is more dangerous, because a lane is meant to start from it.** *Verify against the branches, not only against `integration`* — an unmerged lane branch is where the newest truth lives, and it is invisible to every check in this repository.
>
> **The ownership consequence is [C-323](../LANE_COORDINATION.md), and it is blocking.** Every remaining Epic A slice needs a module Lane A holds, except the two `knowledge_graph` backends.

---

## How to read a specification

**Effort is S/M/L/XL**, and it is a judgement about *shape*, not a duration: **S** is one file and its test, **M** is a module's slice, **L** crosses two modules or needs a migration, **XL** needs an ADR before code.

**"Existing foundation"** is the most important field. **Epic A's slices are mostly composition of facts already computed** — if that section is long, the slice is smaller than it looks.

> **Two principles govern every specification below**, both proposed for ratification in §9:
>
> **1 · Expose before building.** If the capability exists, the slice is a read model and a screen, never a second engine.
>
> **2 · AI explains; deterministic reasoning decides.** No specification below puts a model in a decision path.

---

# Epic A · Surface what already exists

> **Fifteen modules behind five screens.** Every slice here exposes something the pipeline already computes. **Highest value per unit of work in the repository.**

---

## A4 · The product says how current its evidence is · **S** · Knowledge Graph

> ### BUILT 2026-08-03 — and the title changed, because the specification was wrong about the fact
>
> **This slice was specified as *"the product says when it last looked"*, sourced from `provider_watermark.position`, on the strength of reading the schema.** Tracing the code before writing any found three things that made that impossible, and every one is worth keeping:
>
> | What the specification assumed | What the code does |
> |---|---|
> | `position` records when a provider last read a subject | **It advances only when records arrive** — `run_sync.py:167`, `if sync.may_advance_watermark and sync.high_water is not None`. A provider that ran and found nothing leaves it untouched |
> | `provider_sync` says a run happened for an account | **It carries no subject.** One row per run, and the row cannot say which account the run was for |
> | `subject` can be reached from an `account_id` | **`subject` is the company name as the customer typed it** (ADR-0036 §5), unresolved by design. The brief holds an entity id, and resolution is deliberately downstream |
>
> **So Signora cannot currently say when it last looked at an account, and no amount of composition changes that.** The only per-account fact that exists is *when the newest evidence about it was observed*, from `claim.observed_at`.
>
> **That is what shipped, and it is what the screen says.** *"Latest evidence · 2 weeks ago"*, never *"Last checked"* — the second would be the product claiming a capability no table supports, on the surface where trust is being built. A test asserts the wording never drifts back.
>
> **The slice moved module as a result.** It was specified against Provider Platform and built in Knowledge Graph, which already joins claims to entities for `identities()` — so it needed **no new endpoint, no new HTTP request, no new module dependency and no new storage.** The account brief already calls `/account-identities`.
>
> **What is still missing is now a named gap rather than a wrong assumption.** *"When did Signora last look?"* needs either a subject on `provider_sync` or an attempt timestamp on the watermark. **That is a Provider Platform slice, small, and it is the honest other half of this one.**

**Start here.** Smallest slice in the roadmap, closes a real contradiction, and changes how the product *feels* more than anything else of its size.

| | |
|---|---|
| **Objective** | Every account states when its evidence was last collected |
| **Customer problem** | A seller cannot tell *"nothing has happened at this account"* from *"nothing has been collected since Tuesday."* Those demand opposite actions |
| **Customer value** | **The product's entire promise is *here is what changed*.** Today it never says when it last looked — searched, and no `as of` or `last synced` string exists anywhere in `app/` or `components/` |

**Existing foundation — the fact is already stored.**

```
provider_watermark(provider, capability, subject, position, workspace_id)
provider_sync(provider, capability, status, started_at, finished_at,
              records_received, failure_kind, workspace_id)
```

`provider_watermark.position` is *"how far this provider has read for this subject"*, per account. **No new storage.**

| | |
|---|---|
| **Modules** | `provider_platform` (owns both tables) · Product Surface (renders) |
| **Backend** | A read port on `provider_platform`'s `public/` — `last_observed_at(workspace_id, subject) -> datetime \| None`. **Derived at query time, never stored** (§2: truth has one authoritative representation). Compose into the account brief's response in the interface layer, the same way `signal_type` is already composed from the catalog |
| **Frontend** | One line on the account brief, near the score. A `useAccountFreshness` hook or — preferred — a field on the existing brief query, so it costs no extra request |
| **UX** | *"Last checked 2 hours ago"*, plain. **Not a new section**: the brief already measures 619 words ([PRODUCT_EXPERIENCE.md](../PRODUCT_EXPERIENCE.md)) and this must not add a heading. Consider the same line on each attention row later — **not in this slice** |
| **API** | `GET /workspaces/{id}/accounts/{account_id}/opportunity` gains `last_observed_at: datetime \| None` |
| **Events** | None |
| **Data model** | **None.** This is the point of the slice |
| **Acceptance** | ① An account with recent readings shows a recent time · ② An account whose providers have not run shows *"never checked"*, not a blank · ③ **The oldest watermark wins** where providers disagree — that is what bounds the claim · ④ The field is absent, not zero, when no provider has ever read the subject · ⑤ No extra HTTP request is added to the brief |
| **Risks** | *Last looked* is **per provider and per capability**; the screen needs one number. **Recommend the oldest**, because a customer reading *"2 hours ago"* must not be seeing the freshest of six providers while a seventh has been silent for a week |
| **Dependencies** | None. Buildable today |
| **Future** | The same field drives a staleness badge on the list, a *re-sync* control, and the freshness axis of A2's filters |
| ~~**Lane**~~ | ~~Provider Platform's current assignee~~ — *ownership moved to the board, 2026-08-03* |

---

## A1 · Find an account by name · **M** · Knowledge Graph + Product Surface

> ### BUILT 2026-08-03
>
> `GET /workspaces/{id}/account-search?q=&limit=` · `AccountSearch` in the shell header · `useAccountSearch`.
>
> **Built as the audit below proposed, not as the specification did.** Its own endpoint rather than a `q=` parameter; matched against `legal_name` claims rather than a resolved-name column, because there is no such column by design. **No index was added** — twelve accounts need none, and [12-scalability.md](12-scalability.md) forbids optimising before there is evidence.
>
> **Known limitation, recorded rather than hidden:** the bound is on *identities considered*, not accounts returned. Several providers naming one company are several matches, so a workspace where one account has many sources can return fewer than `limit` accounts while more exist. Collapsing in the database would need a cross-module join this deliberately does not have.


> ### Reuse audit, 2026-08-03 — three corrections before a line is written
>
> **1 · There is no resolved-name column, by design, so there is nothing to index.** The specification below says *"likely an index on the resolved-name column"*. **A name is not stored**: it is a `legal_name` claim, and the displayed name is `select_name()` — newest per provider, resolved on every request. The searchable text lives in `claim.value`, stored as `{"v": …}` JSONB.
>
> **2 · `identity_binding.legal_name` looks like the answer and is a trap.** It is a real column, it holds a company name, and it is **a resolution hint captured at binding time** — `resolve.py:92` takes the first non-null `subject_legal_name` it sees. Claims recorded afterwards never update it. **Searching it would find accounts by a name the product does not display**, which is the two-representations defect (§2) presenting as a search that returns the wrong label. It is the fastest thing to reach for and it must not be.
>
> **3 · The authoritative source finds former names for free, and that is a feature.** Matching over `legal_name` claims rather than the resolved name means *"Northwind Traders"* finds the company now shown as *"Northwind Group"* — which is what a seller who has not heard about the rename actually needs. **It falls out of the claim model rather than being built.**
>
> **The endpoint is separate, not a parameter on `/account-identities`.** That endpoint answers *"name these ids I already hold"* — `ids` is required, and its docstring is explicit that it is **not a page** and returns no order. Search answers *"which ids match this text"*, needs an order and a limit, and returns the same shape for a different question. **One path selecting between two contracts by which parameter arrived is two endpoints wearing one coat.** Proposed: `GET /workspaces/{id}/account-search?q=&limit=`, `knowledge_graph`, reusing `AccountIdentityResponse` unchanged.
>
> **Shape, end to end:** a new `ClaimReader` method returning subjects whose `legal_name` claim matches → `GraphQueries` maps subjects to entities through bindings → `identities()` resolves each display name, **which is the call A4 already extended.** No new table, no new module dependency.


| | |
|---|---|
| **Objective** | A customer can type a company name and reach its brief |
| **Customer problem** | **Minute two of every evaluation.** *"Show me Databricks."* Today the only route to an account is scrolling a ranked list |
| **Customer value** | **[MC-1](../PRODUCT_EXPERIENCE.md), classified Essential for GA.** A ranked list answers *"what should I do?"* and cannot answer *"what about this one?"* — and the second question is the one an evaluator asks to test whether the product knows their world |

**Existing foundation.** `GET /workspaces/{id}/account-identities` already resolves names for the attention list — the list holds `account_id` and never a name, deliberately, *"no single module may reach both workflow and entity names."* **Search is a query over the same identities `knowledge_graph` already serves.**

| | |
|---|---|
| **Modules** | `knowledge_graph` (owns names) · Product Surface (the control) |
| **Backend** | `GET /workspaces/{id}/account-identities?q=<text>&limit=` — a prefix/substring match over resolved names, **workspace-scoped and RLS-enforced like every other read**. Cursor pagination per [19-api-conventions.md](19-api-conventions.md) |
| **Frontend** | A search control **in the application shell header**, not the sidebar — search is a verb, not a place ([50](50-product-capability-audit.md) §5). Results link straight to `/accounts/{id}` |
| **UX** | Typeahead, keyboard-first, **⌘K** to open. Each result shows the name and its attention score if one is live, so the customer lands informed. **An unresolved account shows its `Needs identity` state rather than a hex string** — see A6 |
| **API** | One query parameter on an existing endpoint. **No new path** |
| **Events** | None |
| **Data model** | Likely an index on the resolved-name column. **Measure first**: twelve accounts need none, and [12-scalability.md](12-scalability.md) forbids speculative optimisation |
| **Acceptance** | ① Typing a name reaches the brief in one action · ② A name in another workspace is never returned — **a Security Invariant, not a feature test** · ③ No match shows a designed empty state, never a blank panel · ④ Search works before any account is scored · ⑤ Keyboard-only operable, per the existing `@a11y` suite |
| **Risks** | **Match quality on messy names.** *"Adobe"* must find *"Adobe Systems Incorporated"*, and the review found accounts whose sources disagree about their own name. **Recommend substring over the resolved display name for this slice** and defer fuzzy matching until somebody misses a search |
| **Dependencies** | None |
| **Future** | The same endpoint becomes universal search (people, signals, decisions) once C1 exists |
| ~~**Lane**~~ | ~~Product Surface~~ — *ownership moved to the board, 2026-08-03* |

---

## A2 · The accounts list — all of them, filtered · **L** · Product Surface

> ### STRUCK 2026-08-03 — Lane A is delivering this
>
> **`SW-01`…`SW-04` on `origin/lane-a-product-surface`.** `TriageStrip`, `lib/state/triage.ts`, URL-driven narrowing, and SW-04's own handoff describes the capability this specification asks for: *"Two more questions appear above the account list when accounts raise them, and each narrows the list."*
>
> **Lane A's shape is different from the one below, and better in one respect worth recording:** this specification reached for *filters* — score, posture, owner, freshness — and Lane A reached for **questions the list is being asked**, which disappear when nothing raises them. **A filter is a control the seller must think to use; a question is one the product volunteers.** The specification below is kept unedited as the alternative that was considered.
>
> **What survives:** the `GET /accounts/all` read is still unbuilt, and *every* account — not only ranked ones — is still unanswerable. **That is a smaller slice than this one and belongs to whoever holds the list.**


| | |
|---|---|
| **Objective** | Every account in the workspace, filterable by score, posture, owner and freshness, with saved views |
| **Customer problem** | **Twelve accounts scroll. Two thousand do not.** The attention list is deliberately a *ranked working list* and is not a way to answer *"show me every expansion opportunity I own that nobody has checked this month"* |
| **Customer value** | **[MC-2](../PRODUCT_EXPERIENCE.md), Essential for GA.** This is the slice that decides whether Signora survives a real book of business |

**Existing foundation.** Everything the filters need is already computed and already on the row: `score`, `trend`, `score_change`, `signal_type`, `contested`, plus ownership in `opportunity_state` and freshness from A4. **No new intelligence.**

| | |
|---|---|
| **Modules** | `opportunity_engine` (the query) · Product Surface |
| **Backend** | A second read on `opportunity_engine`: `GET /workspaces/{id}/accounts/all` with filter parameters. **Deliberately not overloading the attention list** — its docstring is explicit that it ranks by live score and pages on `(opened_at, id)`; adding filters would change what that endpoint means |
| **Frontend** | A new route. **`/accounts`**, which does not currently exist — the only account route is `/accounts/[accountId]` |
| **UX** | A table, not cards: this is a scanning surface. Filters as chips above it. **Column set: name · score · posture · trend · owner · last checked.** Saved views persist per person |
| **API** | New path. Filters: `score_min`, `score_max`, `posture`, `owner`, `stale_since`, `contested`. Cursor pagination |
| **Events** | None |
| **Data model** | Saved views are **per person, not per workspace** — which makes them the first user-owned data in the product and **collides with [C-302/C-307](../LANE_COORDINATION.md)**, the unresolved per-person RLS question. **Recommend shipping without saved views** and adding them once that ruling lands |
| **Acceptance** | ① Every open account appears, including ones the attention list ranks last · ② Filters compose · ③ A filtered result is linkable — the URL carries the filter · ④ Empty results explain which filter emptied them · ⑤ 2,000 accounts page without a full scan |
| **Risks** | **Two lists showing different things is a product problem, not a technical one.** *Attention* and *Accounts* must be visibly different answers to visibly different questions, or customers will ask which one is right |
| **Dependencies** | A1 (shared query shape) · A4 (freshness filter) · the per-person ruling, for saved views only |
| **Effort note** | **L**, and it is the largest slice in Epic A |
| ~~**Lane**~~ | ~~Product Surface~~ — *ownership moved to the board, 2026-08-03* |

---

## A5 · A company's history · **M** · Observation Engine + Product Surface

> ### BACKEND BUILT 2026-08-03 · the screen waits on [C-324](../LANE_COORDINATION.md)
>
> `GET /workspaces/{id}/accounts/{account_id}/observations?attribute=` — **the Observation Engine's first HTTP surface.**
>
> **Nothing was computed.** `Observation` has carried previous value, current value, direction, magnitude, both ends of the window and the provider since M4, and `ObservationQueries.observations()` has read them since. The module had no interface layer: thirteen fields of intelligence with no path to a customer. **That is what Epic A looks like when the audit was right.**
>
> **Two constraints the screen must respect**, both now in [23-observation-engine.md](23-observation-engine.md):
>
> | | |
> |---|---|
> | **One series per provider** | Apollo saying 120 on Monday and CoreSignal saying 145 on Tuesday is **disagreement, not growth of 25.** A chart joining them draws the phantom this module was built to avoid |
> | **`previous_observed_at`…`observed_at` is an interval** | The change happened *somewhere between*. A single dated point claims precision the evidence does not have |
>
> **And the finding that decides whether the screen is worth building yet: [B-319](../BUGS.md).** The Playground produces **no transitions at all** — every observation is a first sighting, because a transition needs one provider asserting a state attribute twice and the scenario enriches each account once. **The endpoint is correct and its screen would be empty.** Pinned by a test that fails the day the simulator changes.


| | |
|---|---|
| **Objective** | A screen showing how a company's attributes changed over time, with the source of each reading |
| **Customer problem** | *"Is this company actually growing, or did it hire once?"* The brief shows *"Grew headcount 15% over 32 days"* and nothing behind it |
| **Customer value** | **The vision document lists historical snapshots and time-travel as a capability products miss at enterprise scale. Signora has had it since the claim model shipped** — it has simply never been rendered |

**Existing foundation — this is a `SELECT`.**

```sql
SELECT attribute, value, observed_at, provider, payload_provenance
FROM claim WHERE workspace_id = ? AND subject_external_id = ?
ORDER BY attribute, observed_at
```

| | |
|---|---|
| **Modules** | `knowledge_graph` · `provider_normalization` (owns `claim`) · Product Surface |
| **Backend** | A read on the owning module returning claims grouped by attribute, ordered by `observed_at`. **Every row carries its provider and its `observed_at`** — that is the whole product value and it is already stored |
| **Frontend** | A company view at `/accounts/{id}/company`, or a tab on the brief. **Recommend a tab**: it is the same subject, and a separate route invites a second navigation concept |
| **UX** | **One small chart per attribute** — headcount, open roles, funding — plus a readings table. **This is the screen most worth making visual** rather than textual ([PRODUCT_EXPERIENCE.md](../PRODUCT_EXPERIENCE.md) measured the brief at 619 words) |
| **API** | `GET /workspaces/{id}/accounts/{account_id}/attributes` → `{attribute, readings: [{value, observed_at, provider}]}` |
| **Events** | None |
| **Data model** | None |
| **Acceptance** | ① Every reading shows its provider and date · ② Attributes with one reading render honestly, not as a flat line implying stability · ③ Conflicting readings from two providers are **both shown** — never silently reconciled, consistent with the disagreement disclosure the review named the best interaction in the product · ④ An account with no claims shows a designed empty state |
| **Risks** | **Volume.** `claim` is the largest table in the schema. Scope to one subject and paginate per attribute |
| **Dependencies** | A1, for a way to reach a company that is not on the attention list |
| **Future** | The same read powers a *what changed this week* digest ([MC-5](../PRODUCT_EXPERIENCE.md)) and the competitor monitoring in the audit's module 14 |
| ~~**Lane**~~ | ~~Product Surface, with `knowledge_graph`'s assignee for the read port~~ — *ownership moved to the board, 2026-08-03* |

---

## A6 · `Needs identity` — unnamed records leave the working list · **M** · Knowledge Graph

| | |
|---|---|
| **Objective** | A record no provider has named stops appearing as a workable account and gets a queue of its own |
| **Customer problem** | **[PX-301 and PX-316](../PRODUCT_EXPERIENCE.md).** `70b04700` sits fifth on the working list with a score of 33, a full brief, and three workflow buttons including *"I'm working this."* **A seller can take ownership of an account nobody can name.** Call whom? |
| **Customer value** | **The damage is not the row — it is that the ranking beside it stops being believable.** If Signora will rank that, what else is it ranking? |

**Existing foundation.** `entity`, `identity_binding` and `resolution_decision` already model resolution *and record the decision*. The product already renders *"— no source has named this account yet"*, so the state is known; it simply has no consequence.

| | |
|---|---|
| **Modules** | `knowledge_graph` (owns identity) · `opportunity_engine` (qualification) · Product Surface |
| **Backend** | **Depends entirely on the [C-321](../LANE_COORDINATION.md) ruling.** Lane B's recommendation, offered as input: the record **appears**, **scores** (the evidence is real), **never becomes an opportunity**, and is **never workable** |
| **Frontend** | A `Needs identity` surface — reachable from Settings or from the accounts list as a filter |
| **UX** | Each row shows **what is known** — *"4 weeks of elevated research on Design Systems, peaking at 87"* — and offers two actions: **name it** or **dismiss it**. A named record joins the book with its evidence intact |
| **API** | `GET /workspaces/{id}/unresolved` · `POST /workspaces/{id}/unresolved/{id}/identify` |
| **Events** | Reuses `entity.resolution_ambiguous`, already catalogued. **A resolution should publish `entity.identity_bound`**, which also already exists |
| **Data model** | Likely none — the state is derivable from the absence of a binding |
| **Acceptance** | ① An unnamed record never appears on the attention list · ② It is never offered a workflow action · ③ Naming it moves it onto the list **with its score and evidence preserved** · ④ Dismissing it is recorded, not deleted (§2, immutability) · ⑤ The count is visible somewhere, so the queue cannot silently grow |
| **Risks** | **Hiding it entirely loses real intelligence** — the evidence on that record is genuine. The queue must be discoverable or it becomes a place data goes to die |
| **Dependencies** | **[C-321](../LANE_COORDINATION.md) must be answered first.** This is the clearest case in the roadmap of a decision blocking a build |
| **Future** | The same queue absorbs merge/dedupe once two providers name one company differently |
| ~~**Lane**~~ | ~~`knowledge_graph`'s assignee, with Product Surface~~ — *ownership moved to the board, 2026-08-03* |

---

## A7 · The product says when it last *looked* · **S** · Provider Platform

**Proposed 2026-08-03, by building A4.** Not in the original audit — **it exists because implementing A4 proved the fact it assumed was missing.**

| | |
|---|---|
| **Objective** | Every account can state when a provider last attempted to read it, whether or not anything came back |
| **Customer problem** | A4 answers *"how old is what we know"*. It cannot answer *"is Signora still watching this?"* — and those diverge exactly where it matters: **an account nobody has found anything about looks identical to one nobody has checked** |
| **Customer value** | The second half of trust. A seller who sees *"Latest evidence · 5 weeks ago"* today cannot tell whether the account went quiet or the pipeline did |

**Why it does not exist, precisely.**

| Table | Why it cannot answer |
|---|---|
| `provider_sync` | One row per run, with `started_at`/`finished_at` — but **no `subject`**. It knows a run happened; it cannot say which account for |
| `provider_watermark` | Keyed by `subject`, but `position` advances **only when records arrive** (`run_sync.py:167`). A successful empty read leaves it untouched, which is the whole case |

| | |
|---|---|
| **Modules** | `provider_platform` (owns both tables) · Knowledge Graph (joins it to an account) · Product Surface (renders) |
| **Backend** | **Recommend `attempted_at` on `provider_watermark`**, written on every completed run regardless of `high_water` — one column, one write, no new table, and it keeps *how far we read* and *when we last tried* in the row that already has the subject. The alternative — `subject` on `provider_sync` — is more faithful to *runs* but adds a per-subject row to a table whose grain is per-run |
| **The hard part, and it is not the column** | **`subject` is the customer's typed company name; the brief holds an entity id**, and resolution is deliberately downstream (ADR-0036 §5). Joining the two needs either a resolved-subject link the Knowledge Graph can follow, or the answer surfaced per *target account* rather than per account entity. **This is the design decision the slice turns on** |
| **UX** | The same line A4 owns, extended — *"Latest evidence · 5 weeks ago · last checked today"*. **One line, not two**: the brief is already 619 words |
| **Acceptance** | ① An account checked today with nothing new says so · ② An account never checked is distinguishable from one checked and empty · ③ The existing A4 sentence is unchanged when this fact is absent |
| **Risks** | **Only ship the word *checked* once it is true.** A4 deliberately refuses it today, and `freshness.test.tsx` asserts the refusal — that test is updated by this slice, never worked around |
| **Dependencies** | None technically. **The subject↔entity join is the open question** |
| **Effort** | **S** for the column; **M** if the join needs a design |

---

# Epic B · Close the contradictions

---

## B1 · The ICP is consumed by scoring · **L** · Commercial Profile + Buying Score

| | |
|---|---|
| **Objective** | What a customer declares about who buys from them changes what Signora ranks |
| **Customer problem** | **[PX-314](../PRODUCT_EXPERIENCE.md).** *Your business* says Signora needs the catalogue *"before it can tell you anything useful about anyone else's company"*, then a freshly seeded organization with **no products** shows **twelve scored accounts** |
| **Customer value** | **This is what makes the entire commercial-profile module load-bearing instead of decorative.** A customer who fills it in should see the ranking change; today nothing observable happens |

| | |
|---|---|
| **Blocked by** | **[C-322](../LANE_COORDINATION.md), and it must be answered before a line is written.** Is an ICP a *description* or a *filter*? |
| **Modules** | `commercial_profile` (owns the declaration) · `buying_score_engine` (owns relevance) |
| **Backend** | Under the *filter* reading: a derived predicate from the declaration, consumed by the relevance step of scoring. **Under the hybrid Lane B recommends**: the prose stays the customer-facing artifact, a structured predicate is derived from it, and scoring consumes the predicate — preserving *"in your words, not ours"* while making the words consequential |
| **Frontend** | *Your business* shows the **effect**: *"3 of your 12 accounts match this"*, live. That preview is what makes the declaration feel real |
| **API** | `commercial_profile`'s `public/` gains a read port for the predicate. **A new cross-module dependency — check it against [05-module-dependencies.md](05-module-dependencies.md) before building; if absent, it is a graph change and needs approval** |
| **Events** | An ICP change must trigger rescoring. `commercial_profile` already publishes on declaration change; `buying_score_engine` subscribes |
| **Data model** | A structured predicate alongside the prose. **Versioned like everything else in that module** — `icp_segment_version` is the existing pattern |
| **Acceptance** | ① Declaring an ICP changes at least one account's score · ② Removing it reverts — and the revert is visible · ③ Scores are explainable **against the declaration**: the contribution ledger must say *"matches your ICP"* as a line · ④ **A workspace with no declaration keeps working** — no declaration must never mean no scores, or the product breaks for everybody mid-migration · ⑤ Rescoring is asynchronous and idempotent |
| **Risks** | **The highest-risk slice in the roadmap.** It changes the meaning of every score in the product, and scores are already on screens customers have seen. **Requires a rescoring migration and an answer to "what do existing workspaces see the morning after"** |
| **Dependencies** | C-322 |
| ~~**Lane**~~ | ~~Commercial Profile's assignee, with Buying Score's~~ — *ownership moved to the board, 2026-08-03* |

---

## B3 · A customer can verify their own email · **S** · Deployment

| | |
|---|---|
| **Objective** | An email transport exists in at least one environment somebody can review |
| **Customer problem** | **[PX-319](../PRODUCT_EXPERIENCE.md).** Sign-up requires verification; the link is written to the dev server's stdout. **In every environment this team has, a new customer's first hour ends at *"check your email"*** |
| **Customer value** | Without it, nobody can review onboarding — and **every account that has ever existed was created by a script that redeemed the token programmatically.** The front door is fully implemented and has never been walked |

| | |
|---|---|
| **Existing foundation** | `createEmailTransport` is already the seam. `AuthEmailTransportName` is a union with one member and `loadAuthConfig` refuses any other value. **Adding a vendor adds a member and a case** — the shape was built for this |
| **Modules** | Auth tier (`frontend/lib/auth/email.ts`) · deployment configuration |
| **Backend** | One transport implementation behind the existing type |
| **Acceptance** | ① A person can sign up and verify without reading a log · ② The console transport still refuses to exist in production · ③ No credential in the repository |
| **Risks** | **A new dependency needs an ADR** (§6). That is the real cost of this slice, not the code |
| **Dependencies** | **[C-320](../LANE_COORDINATION.md)** — the product owner's sequencing call: M14.5, or earlier because it gates onboarding review |
| ~~**Lane**~~ | ~~QE, or whoever holds M14.5~~ — *ownership moved to the board, 2026-08-03* |

---

## B2 · The first-run path · **M** · Product Surface

> ### STRUCK 2026-08-03 — built by Lane A
>
> **`first-run.test.tsx`**, against D36 — *"every branch on the page tested a falsy value, so nothing rendered at all"*. **The defect this slice was written for is fixed and pinned by a page-level test.**


| | |
|---|---|
| **Objective** | A new customer is led from sign-up to their first scored account |
| **Customer problem** | The empty states are **the best writing in the product** — *"Add the first thing your company sells. A name is enough to start."* — and **not one of them starts anything.** They describe; they do not lead |
| **Customer value** | **[MC-8](../PRODUCT_EXPERIENCE.md).** The first hour decides whether a trial continues, and today it ends at a single button with no sense of what comes after |

| | |
|---|---|
| **Modules** | Product Surface |
| **Frontend** | A progress affordance across the existing empty states: organization → product → who buys it → accounts to watch → **first evidence arrives** |
| **UX** | **Not a wizard and not a modal.** The screens already exist and are good; what is missing is **sequence and a sense of remaining steps**. Recommend a persistent, dismissible checklist that links into the screens rather than replacing them |
| **Acceptance** | ① A new customer reaches a scored account without being told what to do by a person · ② Every step is skippable · ③ It disappears permanently once complete · ④ **It never blocks a customer who wants to explore out of order** |
| **Risks** | **A checklist can make an empty product feel emptier** by enumerating what is missing. The copy must promise what arrives, not list what is absent |
| **Dependencies** | B3, to be reviewable end to end |
| ~~**Lane**~~ | ~~Product Surface~~ — *ownership moved to the board, 2026-08-03* |

---

# Epic C · People

> **The largest genuine gap in the audit, and the only new bounded context Epic A–B does not avoid.** Every persona in the review asked *"who do I call?"* and nothing answers.

---

## C1 · Person becomes an entity · **XL** · new module

| | |
|---|---|
| **Objective** | A bounded context owning people: identity, attributes, employment, and relationships |
| **Customer problem** | The buying committee is **job titles with no members**. A seller cannot contact a title |
| **Customer value** | Answers the first question every persona asked. Unblocks C2, C3, D1's champion-departure signal, and G2 |
| **Existing foundation** | **Reuse the claim model rather than inventing a second one.** `identity_binding` and `resolution_decision` already do exactly this work for organizations. A person is a different `entity.kind`, not a different mechanism |
| **Modules** | **New `people`** · consumes `provider_normalization` · consumed by `commercial_profile`, `ai_reasoning_engine` |
| **Data model** | Claims about people, keyed like claims about companies. **Employment is a relationship with a period, not a field** — that is what makes job-change detection possible later |
| **Acceptance** | ① A person resolves across two providers into one record · ② Every attribute carries provider and `observed_at` · ③ **Erasure is possible and recorded** · ④ Tenant isolation proven by a Security Invariant, not asserted |
| **Risks** | **PII is the whole risk, and one part is architectural.** §2 makes claims immutable; GDPR grants a right to erasure. **Those are in direct tension and must be resolved in the ADR, not discovered mid-implementation.** Lane B's input: erasure of a *person* is a documented, audited exception with its own table of tombstones — not a general licence to mutate claims |
| **Dependencies** | **An ADR before any code** — new bounded context (🔴, §20e) *and* the immutability/erasure ruling |
| **Future** | Reporting hierarchy · relationship graph · job-change signals |
| ~~**Lane**~~ | ~~Dedicated. **Not a side-slice of an existing lane**~~ — *ownership moved to the board, 2026-08-03* |

## C2 · Committee members · **L** · Commercial Profile
Roles gain people. Depends on C1. **The committee model stays role-first** — a role with no member is still valid, because that is how a seller discovers a gap.

## C3 · Derived committee roles · **L** · dedicated
Champion, economic buyer, blocker — **derived from observed engagement, never inferred by a model** (§10). AI may explain *why* somebody looks like a champion. Depends on C2 and on engagement data, which needs E1.

---

# Epic D · Risk — the missing half of the score

## D1 · A risk signal family · **L** · Signal Engine
Champion departure · usage decline · competitor entry · renewal approaching. **The catalog is the work**, and each entry carries its own *"what this cannot tell you"* like every existing signal. Champion departure depends on C1.

## D2 · Risk postures in the existing decomposition · **M** · Buying Score
**Not a second score** ([50](50-product-capability-audit.md) §2.5). A posture within the existing ledger, so a customer still reads one number and can still take it apart. **Acceptance: a contraction risk must never be confusable with a low-scoring opportunity** — they mean opposite things to a CRO scanning a list, which is already [TASK-905](../BACKLOG.md).

## D3 · Which accounts are already customers · **S** · Integrations
One boolean, from the CRM. Depends on E1. **Unblocks the whole expansion/renewal half of the vision** for very little work.

---

# Epic E · The enterprise gate

## E1 · CRM OAuth and read · **XL** · Integrations
**The single highest-leverage integration in the roadmap** — it unblocks pipeline intelligence, forecasting, expansion and customer risk, four vision modules, on its own. `integrations` has the connection and grant model; **no OAuth flow exists** ([C-025](../LANE_COORDINATION.md)). Needs developer credentials, which is a product-owner action.

**Non-negotiable:** a sign-in OAuth token must never be reused as an integration token (§13). Separate grants, separate scopes, separate storage — and `integration_secret` already exists for the second.

## E2 · CRM write-back · **L** · Integrations
Depends on E1. **RevOps asks about this in the first call**, and without it Signora is a second system to check.

## E3 · SSO and SCIM · **L** · QE
Better Auth covers sign-in; enterprise identity is a different surface. **Procurement blocks on it after the product has already won the evaluation.**

## E4 · Audit log · retention · API keys · webhooks · **L** · QE
Immutable operational history already exists; **what is missing is a customer-facing view of it and a retention policy.** Touches `signora_platform/` — RFC first (§20a).

---

# Epic F · Workflow automation

> **The strongest leverage in the audit.** 82 catalogued events, a transactional outbox, ARQ workers, idempotent handlers, dead-lettering and replay — **all built.** What is missing is a way for a customer to express a rule.

## F1 · The rule model · **L** · new `workflow` module
Conditions over catalogued events: `buying_score.updated`, `business_event.detected`, `signal.generated`, `opportunity.created` and 78 others. **Needs an ADR** (new bounded context).

## F2 · A safe action set · **M** · `workflow`
**Watch an account · raise a posture · notify a person · record a decision.** Deliberately **nothing that sends** — the vision's *"generate email, start outreach"* would have Signora acting outward, which it does not do and should not until E1 exists and a human is in the loop.

## F3 · The rule builder · **L** · Product Surface
Depends on F1 and A2 — a rule is a filter plus a trigger, and A2 already builds the filter vocabulary.

---

# Epic G · Copilot

## G1 · Ask about this account · **L** · AI Reasoning
**Explanation only, grounded in the contribution ledger.** Every claim in an answer must cite a reading that exists — the evidence-citation protocol ([ADR-0031](adr/0031-evidence-citation-protocol.md)) already defines how. **Needs a released prompt for the configured model**; the Decision Package's `reasoning@1` currently has none.

## G2 · Draft an approach · **L** · AI Reasoning
Communication, never conclusion. Depends on G1 and C2 — a draft addressed to nobody is not useful.

---

# 9 · Two principles proposed for ratification

**Both emerged from the audit and the product owner has endorsed both. They are written as ADR candidates because a principle repeated in prose drifts; one in an ADR is cited.**

### Principle 1 — Expose before building

> **Before building a capability, establish whether it already exists inside the platform. If it does, the work is a read model and a surface, never a second engine.**

**Evidence:** fifteen modules, eighty-two events, twenty-four endpoints, **five screens**. Five capabilities the vision document lists as enterprise differentiators — source attribution, lineage, history, entity resolution, explainability — **already exist in the claim model** and needed no engineering at all, only rendering.

**What it prevents:** a second reasoning engine solving a problem the first one already solved, which is the most expensive mistake available to a repository at this stage.

### Principle 2 — AI explains; deterministic reasoning decides

> **Every commercial conclusion originates from deterministic reasoning. AI communicates those conclusions in language a human uses naturally. AI may explain. AI must not decide.**

| Deterministic | AI |
|---|---|
| ranking · scoring · prioritisation · recommendations · champion identification · buying committee · opportunity detection · risk assessment | summaries · email drafting · meeting preparation · rewriting · explanation · executive narrative |

**Evidence:** it is already how the product works — *why now* comes from `BuyingScore.trigger` rather than a paraphrase; release is derived from evaluations; the digest is computed. **This ADR does not change behaviour; it names the line so the copilot cannot cross it slice by slice**, which is the pressure Epic G will be under from its first day.

---

# 10 · What this specification set deliberately does not contain

**Conversation intelligence · marketing attribution · territory management · forecasting.** Each is a product rather than a feature, and each is recorded in [50](50-product-capability-audit.md) as a **deliberate scope exclusion rather than unfinished work** — a distinction that matters, because unfinished work invites somebody to finish it.

**And one slice was deleted while this document was being written.** *Mount Timeline* was in the audit's roadmap on the strength of [C-024](../LANE_COORDINATION.md) being `OPEN`. It is mounted — `page.tsx:117` calls `useAccountTimeline`, and a product review walked the rendered feed. **The row was stale, the coordination item is now closed, and a lane was saved a slice it did not need to build.** That is the argument for verifying every specification against the code rather than against the register.

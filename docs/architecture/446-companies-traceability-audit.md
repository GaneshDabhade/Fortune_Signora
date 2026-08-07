# 446 · Companies — screen-by-screen traceability audit

**Lane C · Product Office · 2026-08-05.** **Second audit under [D-078](../DECISION_REGISTER.md)** ([`PRODUCT_OFFICE.md` §5f](../PRODUCT_OFFICE.md)), extended by **[D-079](../DECISION_REGISTER.md)**.

**Screen 4 of 16** — *"8,412 accounts — table, cards, segments, bulk work, import/export"* ([410](410-approved-ui-specification.md)). **[417](417-executable-slice-audit.md) calls it `READY NOW`.**
**Measured against `origin/integration` @ `6b7b04e`. Nothing implemented, no lane named.**

---

# 0 · The finding that changed one of my own

> ## ⚠️ **I asserted a naming collision in [442 §F2](442-product-led-domain-discovery.md). It may not be one, and the repository cannot tell me which.**

**[442](442-product-led-domain-discovery.md) said: *"`Segment` is already `commercial_profile`'s and means who buys; Companies' segment is a saved filter over accounts. Two concepts, one word."*** **[417 §2a](417-executable-slice-audit.md), written a week earlier, said the opposite in passing: *"Segments reuse `icp-segments`."***

**Both are defensible and they imply different architectures:**

| If Companies' *segments* are… | Then |
|---|---|
| **ICP segments rendered as a list** — *"show me accounts matching my Enterprise SaaS ICP"* | ✅ **No collision. One concept, two views**, and [TASK-434](../BACKLOG.md)'s predicate already answers it |
| **Arbitrary saved filters** — industry **and** score **and** owner | 🟠 **A different concept wearing a taken word**, and §4 forbids it |

> **I cannot evidence which from the repository, and the honest verdict is ⬜ *not yet extractable*.** **[D-079](../DECISION_REGISTER.md) makes that a recorded state rather than a gap to fill with a guess** — *"if a UI element cannot be observed, record it as not yet extractable rather than manufacturing requirements."*
>
> **This sharpens [TASK-433](../BACKLOG.md) rather than weakening it: the naming question is downstream of a semantic one, and asking the second first is cheaper.** **My earlier assertion is corrected here rather than left standing.**

---

# 1 · The traceability matrix

✅ exists · 🟡 extend · 🟠 conflicts · 🔴 missing · ⬜ **not yet extractable**

| UI element | Business meaning | Source of truth | Audit | Owner | Consumers | Priority |
|---|---|---|---|---|---|---|
| **The account table — 8,412 rows** | Every company this workspace watches | **Aggregate + read** — `GET /accounts`, cursor-paginated | ⛔ **CORRECTED 2026-08-07 — this cell was wrong, and it is the origin of everything that followed.** **It read *"✅ Exists, and correctly"* and `GET /accounts` does not return this.** **Its own summary is *"Accounts worth attention, most pressing first"*: open *opportunities* ranked by live buying score, authorized on `Resource.OPPORTUNITY`.** ⚡ **Browse and attention are different questions and this audit conflated them.** **The read that answers the design's *8,412 rows* is [TASK-472](../BACKLOG.md), built by Lane B on 2026-08-06 and published through `knowledge_graph/public/`.** ⚠️ **Found by Lane A from the screen and by Product Office from the backlog row within hours of each other ([C-232](../LANE_COORDINATION.md), [C-422](../LANE_COORDINATION.md)), and named precisely by Lane B.** **What the cell got right is preserved below and still holds:** `OwnerScope` is *"applied in the page query, never over the page"* — *"filtering returned rows reads correctly at twelve accounts and **silently becomes a lie at two hundred**"* | `opportunity_engine` | Companies · Executive Dashboard · Account 360 | — |
| **Card view** | The same accounts, differently rendered | — | ✅ **No backend at all.** A rendering, not a capability | — | Companies | — |
| **Owner filter** | Whose book this is | **Value object** — `OwnerScope` *(`ALL` · `MINE` · `UNASSIGNED`)* | ✅ **Exists** | `opportunity_engine` | Companies · Executive Dashboard | — |
| **Score, trend, contested** | Commercial attention, and why it moved | **Aggregate** — `BuyingScore` + the Contribution Ledger | ✅ **Built and published** | `buying_score_engine` | 4 screens | — |
| **Search by name** | Find a company the customer can name | **Projection** — `account-search` | ✅ **Exists.** [MC-1](../PRODUCT_EXPERIENCE.md)'s *"first thing every evaluator types"* | `knowledge_graph` | Companies · Global Search | — |
| **Segments** | ⬜ **Either an ICP cohort or a saved filter — see §0** | ⬜ | ⬜ **Not yet extractable** | ⬜ | Companies · ICP Builder · Global Search | **[TASK-433](../BACKLOG.md)** |
| **Saved views** — *"pinning is per view, not per user, so a shared view looks the same for everyone"* | **A named, shared, durable query** — not a user preference | **Aggregate** — a saved-view store | 🔴 **Missing.** `saved_view`, `saved search`, `monitored` return **zero** repository-wide | ⚠️ **Undecided** — [417 §2a](417-executable-slice-audit.md) flags it as a *placement* question, the [C-010](../LANE_COORDINATION.md) shape | **4 screens** — Companies · App Shell §6 · Global Search · Reports | **[R-02](../DOMAIN_DISCOVERY_REGISTER.md)** |
| **Bulk edit** — *"reversible for 24 hours as a single named batch"* | A change a human approves, applied as one thing, takeable back | **Aggregate** — an action batch | 🔴 **Missing.** `bulk`, `undo`, `revert`, `24 hour` return **zero** | ⚠️ Undecided | **6 screens** | **[TASK-431](../BACKLOG.md)** |
| **Import** | A customer's own list of companies arrives | **External provider** — an inbound source | 🔴 **Missing — and it must not be a new door.** §3 | `integrations` *(recommended)* | Companies · onboarding | **After E1** |
| **Export, with field-level permissions** | The customer takes their data out, minus what this reader may not see | **Platform capability** — a permission dimension | 🔴 **Missing, and unexpressible today.** Casbin tuples are `(sub, dom, obj, act)` — **there is no field term.** `field_permission` and `redact` return nothing in any domain layer *(the three `redacted` hits are credential `__repr__` in `integrations`)* | ⚠️ **Undecided — 🔴** | Companies · Reports · Settings audit export | **[R-10](../DOMAIN_DISCOVERY_REGISTER.md)** |

**Nine elements: 5 ✅ · 3 🔴 · 1 ⬜.** **Not one needs a new intelligence capability, and three of the four gaps are already carried by rows that exist.**

---

# 2 · Workflow — *a seller bulk-edits 8,412 accounts*

**The workflow audit again finds what the field audit cannot.**

| | | |
|---|---|---|
| **Inputs** | A selection, a change, an approval | 🔴 **The approval has no representation** — [R-03](../DOMAIN_DISCOVERY_REGISTER.md) |
| **Outputs** | A named batch a human can point at | 🔴 |
| **Business events** | ⛔ **Nothing.** No `batch.applied`, no `batch.withdrawn` | 🔴 **So the timeline cannot show it and no audit can count it** |
| **State transitions** | applied → withdrawn, inside a window | 🔴 **A lifecycle with a *deadline*, which nothing in the repository models.** `Segment` and `ResearchStatus` are event-driven; **this one changes because time passed** |
| **Domain rules** | Reversal is supersession, never an edit | ✅ **The mechanism exists five times over** and has never been generalised |
| **Validation** | A bulk change is still one domain rule applied *n* times | ✅ |
| **Permissions** | 🔴 **`p, member, *, opportunity, update` is granted today.** **Bulk is that grant × 8,412** — and the policy file cannot say *"a member may update one and an owner may update thousands"* | 🔴 **A quantity dimension the model has no term for** |
| **Side effects** | 8,412 writes, 8,412 score recomputations | 🔴 **See below** |
| **Notifications** | *"your batch of 8,412 completed"* | ⏸ [ADR-0040](adr/0040-notifications.md) deferred |
| **AI interactions** | ⛔ None | ✅ |
| **Background jobs** | 🔴 **Nothing on this screen can run in a request cycle** | **See below** |
| **Audit** | *"attributed, reversible, in the audit log"* — Settings' words, same guarantee | 🟡 **Attribution ✅ · a queryable surface 🔴** |

> ## The two workflow findings, and both are invisible field-by-field
>
> **① A time-bounded lifecycle has no precedent here.** The repository's three state machines — `ResearchStatus`, `SegmentState`, opportunity `Stage` — **all transition because something happened.** *"Reversible for 24 hours"* transitions **because nothing happened**, and **a deadline that expires with no actor is a state change with no event to carry it.** **That is a genuinely new shape**, and it belongs in [R-03](../DOMAIN_DISCOVERY_REGISTER.md)'s design rather than being discovered inside it.
>
> **② Bulk work is background work, and the screen never says so.** **§14 calls an unbounded synchronous loop *"a defect at write time, not a future task"*, and Principle 13 puts anything outside a request cycle in a worker.** **8,412 rows is not a request.** ✅ **ARQ, the outbox, the relay and dispatch are all built** — **so the capability exists and no screen has ever needed it.** **[R-03](../DOMAIN_DISCOVERY_REGISTER.md) must be designed as an asynchronous batch from the first line**, because retrofitting a progress state onto a synchronous design is the expensive version.

---

# 3 · ⚖️ Challenging the UI — import must not become a second door

**[D-079](../DECISION_REGISTER.md) §6 asks Product Office to challenge the UI where it encourages duplication. This is the first exercise of that, and the challenge is narrow.**

**"Import" reads as a file upload. Built that way it is a *second inbound path for customer data*, beside the one Epic E1 is building.**

| | |
|---|---|
| **What already exists** | **`IntegrationSourceAdapter`** and [409](409-inbound-source-port-contract.md)'s contract — **the ruled way a customer's own system delivers records** ([C-326](../LANE_COORDINATION.md)) |
| **What an import actually is** | **The same thing with a file instead of an API.** Same resolution, same provenance, same falsifiability, same *"each mapper reads only its own vendor's shape"* |
| **What two doors would cost** | **Two provenance stories.** An account that arrived by CSV and one that arrived by Salesforce would answer *"where did this come from?"* differently — **and provenance is the thing this repository is built on** |
| **And §20e already says it** | ***"Test data enters the way a customer's data enters."*** **A file import that bypasses the source port is exactly the private door that rule forbids** |

> **Challenge, stated as a recommendation rather than a decision: *import* is a `IntegrationSourceAdapter` whose transport is a file, and it sequences behind [TASK-402](../BACKLOG.md) rather than beside it.** **The screen is not wrong; the obvious implementation would be.**

---

# 4 · Findings, in the ten categories

| | |
|---|---|
| **Existing and correctly modelled** | ⛔ **`GET /accounts` is struck from this list — corrected 2026-08-07.** **It is the attention list, not a company browse; see the account-table row above.** ✅ **`OwnerScope` applied in the query** · `BuyingScore` + the Contribution Ledger · `account-search` · cursor pagination · the supersession mechanism · **ARQ, outbox, relay and dispatch — the background capability bulk needs, already built** |
| **Extension candidates** | **The audit surface** *(attribution exists; the query does not)* · **`IntegrationSourceAdapter` gains a file transport** — §3 |
| **Architectural evolution** | ⬜ **`Segment`'s meaning — §0, and it is not yet extractable** |
| **Missing foundational capabilities** | **[R-02](../DOMAIN_DISCOVERY_REGISTER.md) saved views — 4 screens, blocked by nothing, ownership undecided** · **[R-03](../DOMAIN_DISCOVERY_REGISTER.md) action batch — 6 screens** |
| **Missing workflows** | **Bulk apply → withdraw, asynchronous, with a deadline** |
| **Missing entities** | **A saved view** — *"pinning is per view, not per user"* makes it **a shared object with its own state, not a user preference** · **an action batch** |
| **Missing business events** | **`batch.applied` · `batch.withdrawn`** — without them the timeline cannot show a bulk change and no audit can count one |
| **Missing permissions** | **A field dimension** — Casbin's tuple has no term for one · **a quantity dimension** — the policy cannot distinguish updating one from updating 8,412 |
| **Missing projections** | ⛔ **None.** Every figure derives from published reads |
| **Missing platform capabilities** | **A time-bounded lifecycle** — every existing state machine transitions on an event, and this one transitions on a deadline |

---

# 5 · Cross-screen validation — [D-079](../DECISION_REGISTER.md) §8

**The AI Copilot findings, checked against this screen:**

| | |
|---|---|
| **[R-03](../DOMAIN_DISCOVERY_REGISTER.md) propose → apply → reverse** | ✅ **Confirmed independently.** Copilot asserts it as *"proposes rather than commits, attributable and reversible"*; **Companies asserts the same guarantee in completely different words** — *"reversible for 24 hours as a single named batch"* — **and this audit adds two properties Copilot's could not show: it is asynchronous, and its lifecycle turns on a deadline** |
| **[R-02](../DOMAIN_DISCOVERY_REGISTER.md) scope and saved views** | ✅ **Confirmed and strengthened — now 4 screens with a *published* semantic**: *"pinning is per view, not per user"* |
| **Authorization gaps** | ✅ **Confirmed as a pattern, not an instance.** Copilot needs a **spend** dimension, Companies needs **field** and **quantity** dimensions. **Three screens, three dimensions Casbin's four-term tuple cannot express** — that is an architectural finding rather than three feature gaps |

> **Two audits, two screens, and the same three foundations underneath both.** **That is the register doing what it is for.**

---

# 6 · What this produces

**No new backlog row.** **R-02 and R-03 are [TASK-433](../BACKLOG.md) and [TASK-431](../BACKLOG.md); the import challenge sequences behind [TASK-402](../BACKLOG.md); the authorization finding joins [C-419](../LANE_COORDINATION.md)'s as one pattern.**

**What it adds to rows that exist:** **R-03 must be designed asynchronous with a deadline-driven lifecycle** · **R-02's entity is a shared object, not a preference** · **TASK-433's naming question is downstream of a semantic one** · **the authorization model needs three dimensions it does not have.**

---

# 7 · What this document did not do

**Nothing implemented · no lane named · no wave reordered · no module created · no ADR drafted · no queue file touched · no backlog row added.**

**And it invented no UI element.** ⬜ **One row is recorded as *not yet extractable* rather than resolved by a plausible guess** — including where that meant **correcting an assertion this office had already published.**

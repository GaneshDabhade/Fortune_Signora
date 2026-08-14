# 40 — Commercial Profile (module design)

> Status: **As built** — M12.5 complete, slices 1–5. Lane B.
> Ratified by [ADR-0035](adr/0035-commercial-profile.md), which remains the module's architectural decision record and is **not** superseded by this document. The ADR says *why the bounded context exists*; this says **what was built inside it**, in the manner of [22](22-knowledge-graph.md)–[29](29-ai-reasoning-engine.md).
>
> Created 2026-08-01 with slice 2, because the module had no design document and `CLAUDE.md`'s reading order sends a session to one. A cold Lane B session had the ADR and the code, and nothing recording the decisions taken *during* implementation.

## The boundary, restated because everything below depends on it

> **It records. It computes nothing, resolves nothing, matches nothing, and calls no provider.**

Two import-linter contracts enforce it: `commercial_profile` may import no pipeline module, and no module may reach past its `public/`. A structural invariant — `tests/commercial_profile/test_boundary.py` — reads the domain package as a syntax tree and refuses any identifier naming a judgement (`score`, `priority`, `rank`, `propensity`, `fit`, `weight`). **Widened in slice 2 from one file to the whole package**, because each new aggregate is likelier than the last to attract one: an ideal customer is one plausible-looking method away from a fit score, and a buying committee is one plausible-looking *field* away from an influence model. Slice 3 adds two more guards of the same kind — a dataclass-shape assertion that a role has exactly `title` and `part`, and an OpenAPI assertion that no committee response field names an influence, a rank or a seniority.

## The aggregates

Several small ones, each versioned independently — never one profile object. Products change quarterly and a watch list changes weekly, and versioning them together would mint a version of everything each time anything moved.

| # | Aggregate | Table | Endpoint | Slice |
|---|---|---|---|---|
| 1 | `ProductCatalog` | `product_catalog` | `/workspaces/{id}/products` | 1 ✅ |
| 2 | `IcpDeclaration` | `icp_declaration` | `/workspaces/{id}/icp` | 2 ✅ |
| 3 | `BuyingCommittee` | `buying_committee` | `/workspaces/{id}/buying-committee` | 3 ✅ |
| 4 | `CommercialFocus` | `commercial_focus` | `/workspaces/{id}/focus` | 4 ✅ |
| 5 | `TargetAccountList` | `target_account_list` | `/workspaces/{id}/target-accounts` | 5 ✅ |
| 6 | `DeclaredCompetitors` | `declared_competitors` | `/workspaces/{id}/competitors` | Epic D ✅ |
| 7 | `AccountTag` · `TagVocabulary` | `account_tag`, `account_tag_assignment` | `/workspaces/{id}/account-tags` | TASK-466 ✅ |
| 8 | `TagBatch` | `account_tag_batch` | `…/account-tags/{tag_id}/batches` | TASK-466 ✅ |

⚠️ **Aggregates 7 and 8 break the sentence below, and the break is the design.** 📁 [ADR-0411](adr/0411-customer-organized-account-metadata.md) adds a second kind of customer authorship to this module: **a label, not a statement.** See *TASK-466 — a customer's own labels* at the end of this document.

Every **declaration** is **versioned, immutable and superseded**: a revision is a new row naming the one it replaces, the app role holds no `UPDATE` grant, and the repository offers no method the database would refuse. `DELETE` *is* granted — erasability is a property of the tenancy model, not a statement about what a row means.

**Currency is `MAX(version)`, never `supersedes IS NULL`.** On an immutable table the *new* row names its predecessor, so a null `supersedes` marks the first version permanently. `uq_(workspace_id, version)` is therefore the concurrency control: two callers who both read version 3 both build version 4, and the second insert is refused by the constraint rather than silently winning.

**Since slice 3 that rule exists once**, in `infrastructure/versioned.py`, standing on the abstract `DeclarationModel`. Three hand-written copies would have been three chances for the fourth to be written the way `signal_profile` wrote it — see F-B4.

## Slice 2 — the ICP declaration

**One aggregate for the workspace, holding one `ProductIcp` per product.** An ICP is *"the kind of company that buys **this**"*, so each profile names a product; the profiles are versioned together because they all change at the same slow rate, and because the ADR's objection to a mega-aggregate was about change rates differing by orders of magnitude, which these do not.

*Rejected: one aggregate per product.* It gives a finer audit trail — *"the ICP for Revenue Cloud, v3"* — and costs a collection endpoint, a second read shape, an N-query screen, and a second version stream to reason about. The diff between two whole versions already says which product changed. **Trigger to revisit: a customer with enough products that two people edit different profiles concurrently and collide.**

### What a profile holds, and what it deliberately does not

| Field | Shape | Why |
|---|---|---|
| `product_id` | UUID | Must be in the **current** catalog. A profile for a product the workspace does not sell is a citation resolving to nothing, in the module whose whole job is being citable |
| `industries` | free text | **The customer's words.** A seller says *"mid-market fintech"*; offering a taxonomy would make them translate their business into ours before telling us anything |
| `countries` | free text | Same |
| `employees` | `min`/`max`, either optional | A count of people. An integer needs no shared vocabulary and cannot drift from one |
| `notes` | free text | Read by a colleague, never parsed |
| **revenue band** | **absent** | See below — the most important decision in the slice |

**Revenue is excluded, and the accurate reason is narrower than the one first recorded.** `RevenueBand` already exists as a controlled enum in Provider Normalization's canonical vocabulary, so declaring revenue **as a `RevenueBand`** would mean either importing a pipeline module — which the boundary forbids outright — or defining a second copy, which *truth has exactly one authoritative representation* forbids more firmly.

> **Corrected before slice 3.** This paragraph originally ended *"any future criterion whose value space is already a controlled vocabulary hits the same wall"*, which is false and the module's own design disproves it: `industries` is free text and the canonical vocabulary also has an `industry` attribute. **Revenue is not blocked** — it is an ordinary design choice among free text, a numeric range plus currency, or a picklist, deferred because no customer has asked for it. See F-B2.

### The one judgement the domain makes

A profile with no industries, no countries and no size is **refused**. It is not a statement: it describes every company on earth, and it is indistinguishable from having said nothing — which a customer can already say by leaving the product out. This is a judgement about the *statement*, not about the world, which is the only kind this module is permitted.

An **empty declaration** (no profiles at all) is legal. *"We describe nobody"* has an author and a moment, which is what makes it different from never having said anything.

## Slice 3 — the buying committee

**One aggregate for the workspace, holding one `ProductCommittee` per product** — the ICP's shape exactly, and for the same reasons. What is new is a vocabulary and a set of deliberate omissions.

### Their words for *who*, a five-value vocabulary for *what part they play*

A role is a **title the customer typed** — *"Head of Clinical Informatics"* — and a `CommitteePart` from a closed set: **economic buyer · champion · evaluator · user · gatekeeper**. The split is the ideal customer's split between free-text industries and a structured size, for the same reason: the customer's language is what makes the declaration true, and a little structure is what makes it readable by a colleague six months later.

**The vocabulary is this module's own**, and the Canonical Vocabulary Principle below is what permits it: it is ordinary sales language a seller uses unprompted, it answers to no provider, and nobody translates into it. Two values were considered and rejected — **influencer**, too vague to act on, since every role influences and a value that fits everything sorts nothing; and **approver**, folded into `gatekeeper`, because procurement, legal and security are the same shape of obstacle and two values a customer cannot tell apart is worse than one.

### What a role deliberately does not carry

| Considered | Why it is absent |
|---|---|
| **Influence / weight / importance** | A judgement about a real deal. This is the single field that would turn the declaration into a scoring input, and it is asserted absent in three places: the domain test, the OpenAPI test, and `extra="forbid"` on the request |
| **Seniority band, headcount, department** | Facts about a company Signora will **observe**, not be told. Asking the customer to type them makes them stale the day after |
| **A person's name** | A committee is a template of roles. Person entities are deferred platform-wide (`EntityKind` has `COMPANY` only), and a name field would collect personal data with no consumer and no declared basis for holding it |
| **A stable role id** | A considered asymmetry with `Product`, which has one because everything declared later cites a product. **Nothing cites a role**, and an identifier nothing references is one nobody keeps meaningful. Within a committee a role is identified by its title, which is why two may not share one. **Trigger: the first consumer that needs to cite a particular seat** — realistically when person entities land |

**Two roles may share a part.** Security and legal are both gatekeepers, and that is the ordinary case rather than a mistake — only the title has to be distinguishable.

### Its own table, again

`buying_committee` rather than a column on `icp_declaration`, and the reason is the one that separated the first two: **a committee and an ideal customer change on different days.** Somebody adds a security reviewer without touching who the product is for, and one shared version would put both changes into an audit history that could no longer answer *what changed*. Asserted end to end: declaring a committee leaves the catalog and the ICP at their own versions.

## Slice 4 — the commercial focus

**What the company is pushing right now**: a set of products it currently sells, and what it is trying to do, in the customer's words. One workspace-level statement rather than a per-product map, because *"we're pushing Revenue Cloud this quarter"* is one sentence about the company, not several about products.

### It is not called a priority, and that was the slice's real decision

[ADR-0035](adr/0035-commercial-profile.md) and the roadmap name this capability **business priorities** — *"a priority is a ranking of these"*. The aggregate is deliberately not modelled that way, and the module's own guard is why: `test_boundary.py` refuses any domain identifier containing `priority` or `rank`, because **an ordinal in the head of the pipeline is one consumer away from a weight in a score.**

Three options were weighed:

| Option | Verdict |
|---|---|
| Store an ordinal and **exempt this file from the invariant** | **Rejected.** A guard with an exemption for the one place the temptation is strongest has stopped guarding — and the exemption would sit in the file it exempts |
| Store an ordinal and **weaken the invariant repository-wide** | **Rejected outright.** Weakening a guard to make a change pass is what §11 forbids by name |
| **Model what a seller actually says**: in focus, or not | **Taken.** No rank, no ordinal, no position — the API has no field a consumer could multiply, and `extra="forbid"` refuses one arriving from a client |

**The third option is not a workaround; it is a better model.** A seller says *"we're pushing Revenue Cloud"*, never *"Revenue Cloud is priority two"*. Ranking five products 1–5 is an artificial exercise that produces a number nobody would defend. **The concept name differs from the roadmap's word, which is F-B3's business** — the manifest row should read `CommercialFocus`.

### What it deliberately does not carry

| Considered | Why it is absent |
|---|---|
| **A rank or position** | See above. Also asserted absent on the dataclass, on the wire, and by `extra="forbid"` |
| **A period** — *"Q3 2026"* | `updated_at` already answers *"when did we last say this?"*, and a typed period would be a second representation of that fact, free to disagree with it. **Trigger: a customer who needs to declare next quarter's focus in advance**, which is a genuinely different fact |
| **Anything about signals** | *"Funding rounds matter more to us than hiring"* is **signal relevance** and belongs to the Signal Engine's `signal_profile`. *"We're pushing Revenue Cloud"* is this. The two are one careless sentence apart and must never merge — see the finding below |

### The one place it differs from the ideal customer

**An empty focus is legal.** In the ICP, an entry with no criteria is refused, because an entry that says nothing is indistinguishable from leaving the product out — and leaving it out was always available. Here the aggregate *is* the statement, so there is nothing to leave out: an empty focus is how a customer says *"we are not pushing anything in particular"*, and it has an author and a moment, which is exactly what makes it different from never having said anything. It is also the only retraction path this module offers.

## How free text stays future-proof

*Recorded 2026-08-01 on the product owner's direction: today's free-text inputs must be able to support autocomplete, suggestions, synonym assistance and canonical mapping **without changing the API contract**.*

**They already can, and the reason is the Canonical Vocabulary Principle rather than anything clever in the schema.** Because translation is not this module's job, none of those four capabilities requires this module's contract to change:

| Capability | Where it lives | What changes here |
|---|---|---|
| **Autocomplete · suggestions** | A read of a suggestion source, offered as the customer types. The stored value is still whatever they chose to type | **Nothing.** A new read endpoint, owned by whoever owns the suggestion source |
| **Synonym assistance** | The same — a hint at the edge, never a rewrite of what was stored | **Nothing** |
| **Canonical mapping** | A **projection** computed by whoever does matching, keyed by the stored text | **Nothing.** A stored mapping here would be the translation this module must not perform |

**The one thing that would break it, recorded so it is not discovered late:** if a mapping had to survive the customer *editing* a term — *"Fintech"* becoming *"Financial technology"* — the term would need a stable identity, and free strings have none. **Trigger: the first consumer that must keep a mapping attached across an edit.** The fix at that point is a per-term id, exactly as `Product` has one, and it is an additive field rather than a reshape.

**The rule this sets for slices 5+**: a term-like free-text field stores the customer's words and nothing else; anything derived from it lives outside this module and is keyed by the text. Slice 4 introduced no term-like field — `objective` is a sentence, not a term — so nothing here needed the treatment.

## Refusals a customer can act on

*The module's whole error surface, in one place rather than per slice.*

| Code | Status | When |
|---|---|---|
| `catalog_version_conflict` · `icp_version_conflict` · `committee_version_conflict` · `focus_version_conflict` | 409 | A colleague saved first. Always reported **before** any product check — a stale caller's product list is stale too, so naming the product would send them to fix the wrong page |
| `icp_unknown_product` · `committee_unknown_product` · `focus_unknown_product` | 422 | A declaration names a product not in the current catalog. **One shared check, distinct codes**: it is the only refusal fixed on a *different* page, and a client that cannot tell the two apart can only say *"something was wrong"* |
| `catalog_refused` · `icp_refused` · `committee_refused` · `focus_refused` | 422 | What each aggregate's domain refuses. Distinct because the three are fixed in three different places |

> **There are now three codes for one condition** (`*_unknown_product`), as predicted in slice 3, and the shape is visibly wrong. A single neutral `unknown_product` is the right answer and is **still not taken**: renaming a shipped code is outside this lane's budget (⚫). **Raised for the product owner a second time** — it is the only outstanding item in this module that gets worse with every slice.

## The Canonical Vocabulary Principle

*Made explicit 2026-08-01, on the product owner's direction, before slice 3. It was the reasoning behind three separate slice-2 decisions and had never been written down as one rule — which is how a principle gets rediscovered by the next session instead of applied.*

> **The customer declares in their own language. Signora owns every translation into its own.**

Three responsibilities, permanently separate:

| Owns | Module | In one line |
|---|---|---|
| **What the customer means** | **Commercial Profile** | Records their words, unchanged |
| **What a provider said, in Signora's terms** | Provider Normalization | The anticorruption layer for vendor vocabulary |
| **What is true of a company** | Knowledge Graph | Resolution among disagreeing claims |

A customer declares *Healthcare*, *Manufacturing*, *Fintech*, *Security*, *United States*, *Germany*, *mid-market*, *enterprise*. **They never see, choose, or are asked to translate into** an Apollo industry, a Bombora topic, a CoreSignal employee band, or any other provider category — that is Signora's supplier's vocabulary, and a screen exposing it has moved Signora's core competence onto the customer's desk ([04-modules.md](04-modules.md), ruled 2026-08-01). The same rule that keeps provider *configuration* away from a customer keeps provider *taxonomy* away from them.

**What this permits, and what it forbids, inside this module:**

- ✅ Free text where the customer has words — `industries`, `countries`, a role's title.
- ✅ A **small vocabulary this module owns**, where the structure is what makes the declaration usable and the words are the customer's own trade language — `CommitteePart` in slice 3. Owned here means: defined here, versioned here, translated by nobody, and answerable to no provider.
- ❌ Restating another module's controlled vocabulary as a field here — `RevenueBand` is Provider Normalization's, and a second copy is duplicated truth.
- ❌ Translating at declaration time. Mapping *"United States"* onto whatever a claim carries is **resolution**, and it happens where resolution happens — never at the point somebody types.

**The asymmetry this exposes is the real finding, and it is F-B1 below:** Signora has an anticorruption layer for provider language and **none for customer language**. Provider Normalization exists precisely so vendor models cannot leak inward. Nothing plays that part for the words a customer types, because nothing has needed to yet.

> **This statement binds Commercial Profile and is written here because Lane B may not edit `04-modules.md` (🔴).** Its cross-module form belongs in that document, beside the provider-configuration ruling it extends — recorded in F-B3 for the integrator, deliberately **not** duplicated here as a second copy of a rule.

## Findings, reviewed before slice 3

*Each slice-2 finding was re-argued rather than carried forward. Two changed materially; one was wrong as stated.*

**F-B1 — the customer's language has no anticorruption layer. `Sharpened.`** As stated in slice 2 this was *"reconciliation has no owner"*, which is true and understates it. The precise gap: Provider Normalization is an **anticorruption layer for vendor vocabulary** — it exists so provider models cannot leak inward, and it is the clearest ACL in the codebase. **Nothing plays that part for customer vocabulary.** A customer's *"United States"*, *"Fintech"*, *"mid-market"* must eventually meet a canonical claim, and the component that does that is unbuilt and unowned.

ADR-0035 answers half of it — resolution among disagreeing claims is a Knowledge Graph slice. It does not answer the other half: *whose job is it to know that "Fintech" and the canonical industry value are the same thing?* Three candidate homes, none chosen: the Knowledge Graph (it already resolves), a new matching context (it is a distinct concern with a distinct failure mode), or a translation table owned here (**rejected** — it would make this module resolve, and it is the module least equipped to review a resolution).

**Roadmap impact: none before slice 5.** Slice 3 and slice 4 declare nothing that needs translating. **It must be answered before anything matches an account against an ICP** — tracked as [C-002](../LANE_COORDINATION.md#c-002--customer-language-has-no-anticorruption-layer).

**F-B2 — ~~a controlled value space cannot cross this boundary~~. `Corrected — the slice-2 statement was too strong.`** It claimed revenue *cannot be declared here* and that three criteria were architecturally blocked. That is wrong, and the module's own design disproves it: `industries` is free text and the canonical vocabulary also has an `industry` attribute — the same overlap, shipped and correct.

**The accurate rule is narrower**, and it is the Canonical Vocabulary Principle above: *this module must not restate another module's controlled vocabulary as a typed field; it may always record the customer's words about the same subject.* Revenue is therefore **not blocked** — it is an ordinary design choice among three viable options (free text like industries · a numeric range plus currency · a picklist), deferred because no customer has asked for it, not because an ADR is owed. **Nothing queues behind it.**

*Why it was overstated:* the impossibility of importing `RevenueBand` is real, and I generalised from a genuine constraint on **one implementation** to a false constraint on **the capability**. Worth naming, because it is the shape of error that turns a design choice into a phantom blocker in a roadmap.

**F-B3 — `04-modules.md` is stale, and Lane B may not edit it (🔴).** The accumulated edits moved to [C-004](../LANE_COORDINATION.md#c-004--shared-documents-lag-commercial-profile) when the register was created, so the integrator has one place to find them. For reference:
- Commercial Profile manifest → **Endpoints**: add `/workspaces/{id}/icp` and `/workspaces/{id}/buying-committee`; **Tables**: add `icp_declaration` and `buying_committee`.
- **Also worth folding in:** the cross-module form of the Canonical Vocabulary Principle above, beside the existing provider-configuration ruling in the Provider Platform entry, which it extends rather than repeats.
- **No dependency edge changed** by slice 2 or slice 3. Nothing new imported, nothing published, graph untouched.

**F-B4 — `signal_profile`'s inverted supersession. `Unchanged, and it fired this module's extraction trigger.`** Still Lane A's to fix. What changed is the consequence *here*: slice 3 is the **third** table in this module reading "the row in force", and the reason `MAX(version)` is correct rather than `supersedes IS NULL` is subtle enough that `signal_profile` got it backwards. Three hand-written copies is three chances for the fourth to be written wrongly, so the rule is now expressed **once**, in `infrastructure/versioned.py`, where it cannot be got wrong per table. This is *types make incorrect architecture impossible* applied to the one line in this module that a careful engineer has already got wrong somewhere else.

**F-B6 — `signal_profile` is customer-authored configuration living in Lane A's module, and nobody owns its write path.** `New in slice 4.` [B-001](../BUGS.md) says the defect *"becomes reachable the moment a customer can edit their relevance profile, which is Lane B's territory but Lane A's module"* — and that sentence contains an unresolved ownership question, not just a bug.

**The boundary this module has drawn makes the answer clear, and it is not Lane B's.** *"Funding rounds matter more to us than hiring"* is **signal relevance** — a statement about what Signora should treat as interesting — and the Signal Engine owns relevance by ratified principle. It is not a declaration about the customer's own commercial position, which is all this module holds. **Commercial Profile must not acquire it**, however customer-authored it looks: that is exactly the drift the module's boundary exists to prevent, and the slice-4 focus is one careless sentence away from it (*"we're pushing Revenue Cloud"* vs *"product-launch signals matter to us"*).

**Recommendation:** the signal-profile write path is **Lane A's**, in `signal_engine`. Tracked as [C-005](../LANE_COORDINATION.md#c-005--who-owns-the-signal-profile-write-path).

**F-B7 — three codes for one condition, and it now grows every slice.** `New in slice 4.` `icp_unknown_product`, `committee_unknown_product`, `focus_unknown_product` — one shared check, one shared message, three wire codes, because renaming a shipped code is ⚫. **This is the only thing in the module that gets worse with each slice**, and slice 5 makes it four. Tracked as [C-003](../LANE_COORDINATION.md#c-003--three-wire-codes-for-one-condition).

**F-B5 — endpoint tests live in QE's tree. `Now a concrete proposal rather than an open question.`** §20e gives QE `backend/tests/**` except *a module's own suite*, and `tests/integration/test_api_<module>.py` tests exactly one module's endpoints while living in QE's directory. **Proposed rule, now [C-006](../LANE_COORDINATION.md#c-006--which-lane-owns-test_api_modulepy):** *a file named `test_api_<module>.py` is that module's own suite regardless of directory; QE owns everything else in the tree, including any cross-module flow test.* That keeps the two lanes' edits disjoint without moving files or splitting a suite mid-module. Slices 1–3 follow the existing precedent until it is ruled on.

## The shape of the customer's first hour

*Assessed 2026-08-01 at the product owner's direction, before slice 3, and deliberately **not implemented**. The question: should products, ICP, buying committee, priorities and target accounts remain five independent settings pages, or become one guided experience?*

**The answer is one guided experience over five unchanged aggregates — and the architecture already permits it with no backend change at all.** What follows is why, and the two things that would make it go wrong.

**The five are not settings.** A setting is something a working product lets you adjust. These are the condition of the product working: **the pipeline cannot run until a target account exists**, and nothing in the product says so. Presenting a gate as a settings tree tells a first-time customer that five optional switches are available, when in fact one specific subset is the difference between an empty screen and a working one.

| Perspective | What the settings-tree shape does |
|---|---|
| **First-time setup** | No stated order, no stated end. A customer cannot tell which of five pages they must complete before anything happens |
| **Workflow** | The five are *semantically* sequential — an ICP is *"who buys **this**"*, a committee is *"who decides about **this**"*, a priority is a ranking **of these** — and independent pages hide a dependency the domain enforces anyway (slice 2 already refuses a profile for an undeclared product, which as a settings page is a confusing error and as step 2 of 5 is simply impossible) |
| **Trust** | Signora's product promise is that its conclusions can be defended. A flow that says *why* each answer matters teaches the mental model the explanation later depends on. A settings page teaches nothing |
| **Discoverability** | Today the entire head of the pipeline is two clicks inside **Settings**, a menu customers open when something is wrong |
| **Completion rate** | The strongest argument. Five optional-looking pages, no progress, no end state — and the product is inert until the last one is done |

**But independent editing must survive it.** In month six a customer adds a product without re-running onboarding. So the destination is *both*: a guided first run **and** the direct pages, over the same endpoints.

**Three architectural constraints on doing it, which is the part that belongs in this document:**

1. **The aggregates stay separate and the endpoints stay as they are.** A guided flow is a **composition over existing reads and writes**, not a new backend concept. Anything that would add a `POST /commercial-profile/onboarding` has put a *workflow* into the module that records.
2. **Completeness is derived, never stored.** *"Has this customer finished setting up?"* is answerable from the versions already returned by the reads the screen makes. A stored `onboarding_completed` flag would be a second representation of a derivable fact — and it would lie the moment somebody deleted their last product. This is *truth has exactly one authoritative representation* applied to a progress bar.
3. **It is a two-lane build.** Lane B owns `components/commercial/**` and `settings/products`; **Lane A owns the shell, the routing and the rest of `app/(app)/`**, so a first-run route belongs to Lane A composing Lane B's components. Neither lane can ship it alone, and it needs sequencing between them rather than a surprise.

**Recommended sequencing: after slice 5, not before**, and it is a two-lane build — tracked as [C-007](../LANE_COORDINATION.md#c-007--the-guided-first-run-is-a-two-lane-build).  Guiding a customer through a flow whose last two steps do not exist would demonstrate an incomplete thing well — and §20d forbids building slice 5's capability to make slice 3 demonstrable. Until then the settings pages are correct and honest.

**One thing worth doing sooner, and it is Lane A's call:** *Your business* sits under **Settings**, and it is not a setting. Moving it to a first-class destination is a navigation change in the shell, not a change here.

## Slice 5 — the target account list, and the module's first contract

**The slice that gives the pipeline an input.** `RunProviderSync` has taken a `subject: str` since M2.1 and nothing has ever supplied one; every company the platform has processed arrived from a seeder. A customer can now name companies, and the rest of the platform can read them.

Governed by **[ADR-0036](adr/0036-target-account-contract.md)**, negotiated through [C-001](../LANE_COORDINATION.md#c-001--the-target-account-contract). The reasoning lives there and is **not repeated here**; what follows is what was built.

### Three surfaces, and only one of them is new in kind

| Surface | What it is |
|---|---|
| `PUT`/`GET /workspaces/{id}/target-accounts` | The fifth declaration, on the same terms as the other four |
| **`commercial_profile.target_accounts_changed`** | The module's **first published event**. `workspace_id` on the envelope, `declaration_version` in the payload, **nothing about accounts** |
| **`TargetAccountReader` on `public/`** | The module's **first public contract**. Frozen views, the whole list, never a delta |

### An entry has a stable id, and a committee role does not

Slice 3 gave `CommitteeRole` no identifier and recorded the trigger for adding one: *the first consumer that needs to cite a particular entry.* **That trigger fired here**, for the reason ADR-0036 states — without an id a rename is indistinguishable from a remove-and-add, and those are different instructions about spending money. Client-chosen, like `Product`'s, which is also what makes the save idempotent.

### What the table and the payload deliberately do not hold

**No synchronization state anywhere.** No watermark, no last-fetched, no provider, no cadence, no status — not as a column, not as a response field, not on the event. Each would be this module holding a fact about synchronization, and the wire contract is asserted in a test rather than reviewed for, because *a watch list looks like a job queue* and the first field to arrive would be a status.

**No resolution.** The name is what the customer typed. There is no search, no autocomplete against a company database, and no check that a company exists. Asking for a domain would be asking a customer to do resolution.

**`MAX_ACCOUNTS` is a typo guard, not a plan limit.** How many companies a customer is *entitled* to watch is commercial packaging and a cost model — the first is not this module's and the second is Provider Platform's.

### Every accepted declaration is announced

Including one that removes the last account, and one whose content matches the previous version. **Deciding that a restatement changes nothing requires knowing what has already been synchronized** — a fact Provider Platform holds and this module does not. Suppressing an event to save a consumer some work would be this module reasoning about synchronization.

The event is published on the request's own session, **after the save and inside the same transaction**. Asserted three ways: the use case records the ordering, the endpoint test reads the outbox under the privileged identity, and a refused declaration is proven to announce nothing.

### The one thing the screen may not say

Saving records the list and announces the change. **Nothing consumes that announcement yet** — the consuming side is Lane A's and unbuilt (see `B-004`). So the screen says Signora *has been told*, and does not say it has started looking. A screen promising monitoring the platform is not doing would be the product asserting something untrue, which is worse than under-promising. Enforced by a test.

### The `public/` surface is a stable interface from today

Adding fields is compatible; removing or repurposing one is not, and a breaking change is a new version with a stated deprecation window (§9). Three things it must never grow — a delta, a resolved value, anything about synchronization — are named in the package docstring, because the next person to touch it will not have read this document.

## Product review — 2026-08-01, the four declarations end to end

*A dated record. Requested by the product owner while slice 5 was blocked on [C-001](../LANE_COORDINATION.md#c-001--the-target-account-contract), and written **before** any fix, so the findings are not shaped by what was convenient to change. Reviewed as five people, not as an engineer reading their own JSX.*

**The headline: the module is honest and the screen is not finished.** Every claim the four sections make about what Signora does with a declaration is true, and none of them tells a first-time customer what to do, in what order, or when they are done. Two defects are real enough to have bug rows.

### What each person actually experiences

| Person | What they get today | The finding |
|---|---|---|
| **First-time customer** (owner, day one) | Four sections stacked on one page, no stated order, no end | Nothing says *"do these four, then Signora can start"*. The page ends with no next step, because the step that starts the pipeline is slice 5. **They cannot tell whether they are finished** |
| **Product manager** | Can declare products, buyers, committees and focus, and see who last changed each | The best-served persona. Their one gap is history: four screens promise *"every version is kept"* and none can show one |
| **Sales administrator** | The owner role, so full write access; the natural custodian of all four | Removing a product is a one-click, unconfirmed action that **silently breaks the other three sections** — [B-005](../BUGS.md) |
| **SDR** | **Nothing. Cannot reach the page at all** | `/settings/*` is owner-guarded, so a member sees none of it — even though the API deliberately grants `member` read on all four resources. [C-008](../LANE_COORDINATION.md#c-008--sellers-cannot-see-what-their-company-sells) |
| **AE** | **Nothing, same reason** | An AE working an account cannot see the ICP that account is supposed to match, or the committee they are supposed to be selling into. This is the review's most valuable finding |

### Defects, with bug rows

**[B-005](../BUGS.md) — removing a product locks the customer out of the other three sections.** 🟠 The ICP, committee and focus editors each send *everything stored* on save. A profile whose product has been removed from the catalog is no longer displayed — but it is still sent, and the server correctly refuses it with `icp_unknown_product` naming a product that is **not on the screen**. The customer cannot clear it through the UI, because clearing also re-sends it. Reproducible in four clicks, and the three sections are affected identically.

**[B-006](../BUGS.md) — three of the four sections vanish silently when their query fails.** 🟡 The page renders each section only when its data has arrived, and only the catalog's `isError` produces a message. If the ICP request fails, the customer sees products, no ideal customer section, and no explanation — the absence looks like a feature they do not have.

### Findings that are not defects

**The promise nothing can keep.** All four sections say *"Every version is kept — a change is a new one, never an edit."* It is true, it is the module's best property, and **there is no way to see a single earlier version.** The rows exist and are immutable; no endpoint exposes them. Either the product should show history, or the sentence is a claim a customer cannot check. **Recommendation: a read endpoint per aggregate returning prior versions, and a "history" disclosure per section.** It is the smallest slice that turns the module's discipline into something a customer benefits from rather than reads about.

**Four empty states, three of them identical.** A workspace with no products shows *"No products yet"* followed by *"Add a product first"* three times. Honest, and it reads as a broken page rather than a sequence.

**No orientation and no completion.** The header says what the page is for; nothing numbers the four, orders them, or marks what is done. A first-time customer cannot answer *"what do I still owe Signora?"* — which is [C-007](../LANE_COORDINATION.md#c-007--the-guided-first-run-is-a-two-lane-build)'s argument arriving from a different direction: the guided flow is not polish, it is the missing answer to a question the page provokes.

**Destructive actions have no confirmation and no undo.** *Remove the description for X*, *Remove the committee for X*, and deleting a product all fire on one click. Versioning means nothing is truly lost — but with no history surface, the customer has no way to believe that, and no way to recover.

**The link says "Products" for a page called "Your business."** `/settings` links to `/settings/products`, whose heading is *Your business* and which now holds four things. The route name is a slice-1 artifact.

**Validation messages are good, and one is not.** The refusals a customer can hit read well — *"reload to see their version before saving yours, so neither of you loses work"* explains the consequence, not the rule. The exception is the one behind B-005, which names a product the customer cannot see.

**The copy is honest about non-use, and that raises a fair question.** Each section says what Signora will *not* do with the declaration — *"it does not grade anyone against it"*, *"no judgement about how much any of them matters"*, *"nothing here is ranked"*. That is correct and worth keeping. But nothing says what Signora **will** do, because for the committee and the focus nothing consumes them yet. A customer entitled to ask *"then why am I filling this in?"* has no answer on the page.

### What Lane B proposes to fix, in order

1. **B-005** — the defect that locks a customer out. A fix belongs in the editors: send only entries whose product is still in the catalog, and say so on screen when one is dropped.
2. **B-006** — render each section's error, not only the catalog's.
3. **Version history** — the promise the module already keeps and cannot show.
4. Empty-state consolidation, confirmation on destructive actions, and the route name — genuine, and none of them is worth a slice on its own.

**Not proposed:** the guided flow ([C-007](../LANE_COORDINATION.md#c-007--the-guided-first-run-is-a-two-lane-build), two lanes, after slice 5) and read access for sellers ([C-008](../LANE_COORDINATION.md#c-008--sellers-cannot-see-what-their-company-sells), frozen foundation).

## Epic D phase 1 — the competitor declaration

**The sixth, and the first that is about a risk rather than an ambition.** The other five say what a customer wants; this says what they are up against.

**It exists because the pipeline was missing a fact, not a mechanism.** `business_event_engine` has emitted `TECHNOLOGY_ADOPTED` and `TECHNOLOGY_RETIRED` since M4, and `displacement_opportunity` and `modernization_underway` already consume them. What no provider can report is **which of those technologies the customer is losing deals to** — that is knowledge only the customer has, and this holds their answer.

### It resolves nothing, and could not

**A competitor is a technology name exactly as typed, with a client-chosen stable id** — the same two fields as a `TargetAccount`, for the reason [ADR-0036](adr/0036-target-account-contract.md) gives about that one: asking for a vendor or a website would be *asking a customer to do resolution*, and resolution quality is Signora's competence, not theirs.

**The preparation package recommended the opposite** — *"a competitor declaration should reference a resolvable technology, not a free string"* — and two things in this repository refuse it:

- the import contract **`"commercial_profile declares; it never reads the pipeline"`** (`pyproject.toml`) forbids reaching the Knowledge Graph; and
- **`knowledge_graph/public/` publishes nothing to reach.**

> **That is the boundary working, not a gap.** Matching *"Salesforce"*, *"salesforce.com"* and *"SFDC"* to one technology is exactly the job the graph exists to do, and a second resolver here would be free to disagree with the first. **The match between a declared name and a detected `TECHNOLOGY_ADOPTED` belongs to `signal_engine`**, reading this list through `public/` — which is where the reuse was wanted all along.

The stable id survives for the watch list's reason: without one, a customer *renaming* an entry is indistinguishable from *removing one and adding another*.

### It grades nobody, and a test says so

**No `threat_level`, no `severity`, no rank, no ordinal.** A technology is a competitor or it is not.

This is the module's standing temptation arriving in its sharpest form: a competitor is *about* a threat, so a number feels natural — and it would be a weight in the head of the pipeline, declared by a customer, consumed by a score, reviewed by nobody. **What a `competitor_entry` signal contributes belongs in `scoring_model@1.json`**, a reviewed artifact with a content hash that a diff can argue with. That is the least powerful author capable of getting it right.

`test_competitors.py` refuses the vocabulary in the file somebody would add it to, and the integration test refuses it in the response body. `test_boundary.py` already refuses `priority` and `rank` module-wide.

### An empty declaration is legal, and is not version 0

*"We do not track competitors"* reads as **version 1 with an empty list**; never having said anything reads as **version 0**. A consumer that collapsed them would report an empty *result* where the truth is an empty *input* — the defect D6 already names on the attention list, and the same distinction `focus.py` keeps.

### It has a second reader, and that changes what `public/` is

**`signal_engine` reads the competitor list through this module's `public/`** — `DeclaredCompetitorView`, `DeclaredCompetitorListView`, `DeclaredCompetitorReader`, mirroring the target-account triple exactly, implemented in `infrastructure/competitor_reader.py` and injected by the composition root. Authorised by **[ADR-0403](adr/0403-signal-engine-reads-a-declaration.md)**; the ADR's own validation found the existing `lint-imports` contracts already permit it, so **no contract amendment was needed.**

> **This module now has two consumers**, which is the point at which its `public/` stops being a courtesy and becomes a contract whose stability matters. Add fields, never remove or repurpose them.

**`DeclaredCompetitorListView` carries no `version`, and the asymmetry is deliberate.** `TargetAccountListView` carries one because the same integer travels on `target_accounts_changed`, so a consumer handling that event can confirm which declaration it is acting on. **Nothing announces the competitor list**, so a version here would be a number with nothing to compare it against.

### Nothing is announced

**Unlike the watch list, this write publishes no event.** No downstream module consumes it yet, and an event with no counterparty is the speculative half-contract the roadmap forbids twice. **And it stayed that way when the consumer arrived.** ADR-0403 ruled that `signal_engine` needs no trigger: detection already runs on `business_event.detected`, and the declaration is configuration consulted *during* that run — exactly as `SignalProfile` is. Adding `CompetitorsChanged` would create a trigger nothing needs.

### What is not here

**No *lost to* or *won against*.** That is an outcome with a date, an account and an amount — a fact about one deal, where this is a standing statement about a market. Recording it here would be a workflow event stored as configuration. **Trigger for adding one: [E1](../BACKLOG.md) landing**, at which point a customer's own CRM already holds it and this module should read rather than restate.

## Deliberately deferred

- **~~The fourth duplication.~~ `Trigger fired in slice 3; extracted, but only the dangerous part.`** With three aggregates the shared shape is finally visible rather than guessed. **Extracted:** the abstract `DeclarationModel` (`id`, `version`), the `latest()` select that encodes *"the row in force is `MAX(version)`, never `supersedes IS NULL`"* once, and `sold_products()`, the *"a declaration may only cite something we sell"* check. **Deliberately left duplicated:** the aggregates and the use cases. A frozen-slots dataclass base would force field-ordering contortions to accommodate `supersedes`'s default, and `version + 1` is not where a subtle defect hides — the *read* is, which is exactly what F-B4 shows and exactly what was centralised.
- **Retracting a description** without deleting a product. A customer removes the last profile instead; a first-class *"we no longer sell to anybody"* has no evidence behind it yet.
- **A `TagField` in `components/ui`.** Two screens now compose a list-of-typed-entries from `Input` + `Button`, in different enough shapes (free text · title plus a part) that the shared component is still a guess. It moves when a third wants it, or when two want the *same* one.
- **A period on the focus.** Trigger: a customer declaring next quarter's focus before the quarter starts.
- **A note on a committee**, the way a profile has one. No evidence anybody needs it; the escape hatch is that a role's title is free text. **Trigger: a customer writes a role title that is really a sentence.**
- **Consolidating `*_unknown_product` into one code.** See the refusals table.
- **`public/` stays empty.** Nothing downstream consumes a declaration until slice 5's `TargetAccountReader`. Publishing a reader now would be a contract with no counterparty.

## How to see it

Sign in as an owner and open **Settings → Your business → Products**. Three things, in the order a customer would do them:

1. **Declare a product.**
2. **Describe who buys it** — industries and countries in your own words, a size range in people, a note.
3. **Say who has to agree** — add *Chief Financial Officer* as the economic buyer, *Head of Security* as a gatekeeper, whatever your deals actually look like.
4. **Say what you are pushing** — tap the products you are actively selling, and write what you are trying to do this quarter.
5. **Name the companies you are watching** — type them the way you say them. No website, no legal name, no lookup.
6. **Name who you compete against** — the products you lose deals to, again the way you say them. **Signora records them and ranks none of them**, and it promises no alert, because nothing consumes the list yet.

Each section shows your own words back to you, each version line names you and the date, and every earlier version is still stored. The five are versioned separately: renaming the product leaves the other four where they were.

**Step 5 is the one that changed the platform.** Saving it announces `commercial_profile.target_accounts_changed`, which is the first thing this module has ever told anybody. **Nothing consumes it yet** — the consuming side is Lane A's and unbuilt — so the screen says Signora has been told and does not claim it has started looking. Open the page in a second browser, save from both, and the second is told a colleague got there first rather than quietly losing the work.

**Nothing on any of the five screens grades a company, a person or a committee against what you typed, and nothing ranks anything** — those are different modules' jobs, and they are not built.


---

## ICP-01 — an ICP becomes a thing a customer can name

> Ratified in proposal by [ADR-0041](adr/0041-icp-aggregate.md). **This section describes what was built**; the ADR holds why, including the two reversals discovery produced.

**The screen this delivers did not exist in any form.** An ideal customer was reachable only through the product it belonged to, so *"show me everything we've said about who buys from us"* had no page — and a company selling one product to two different kinds of buyer could not say so at all.

### What changed, and what deliberately did not

| | |
|---|---|
| **Added** | `Segment`, `SegmentVersion`, `SegmentCriteria`, `SegmentTransition` · four tables (migration `0031`) · `SegmentQueries` · `SqlSegmentReader` · `GET /workspaces/{id}/icp-segments` · the *Who you sell to* list |
| **Reused unchanged** | `EmployeeRange`, `validate_criterion_list`, `IcpError` — **imported, not copied**, so a rule fixed in one place stays fixed in both |
| **Untouched** | `IcpDeclaration`, `ProductIcp`, `DeclareIcp`, `icp_declaration`, `GET`/`PUT /workspaces/{id}/icp`, the ICP editor, and all 69 of their tests |

**The old path still serves the editor.** Migration `0031` copies and deletes nothing: old read, then new read, then old write disabled, then retirement. The customer-facing swap happens when the new path has earned it, not when the new tables exist.

### The four tables, and why each is separate

`icp_segment` is **identity and nothing else** — what every future citation points at. If the versioned row *were* the segment, each revision would mint a new id and every citation an opportunity ever made would stop resolving. `icp_segment_version` is **published content only**; a draft is not a version, which is what lets an abandoned one cost nothing. `icp_segment_product` is versioned *with* the content, so *"we added CPQ in March"* is recoverable. `icp_segment_state` is append-only, each row a complete statement — **the status is the audit log**, the shape `opportunity_state` already uses.

**No `UPDATE` grant on any of them.** State is derived from the latest transition rather than stored, so *"who archived this, and when?"* has an answer without a mutable column.

**`icp_segment_product` carries no foreign key to a product**, because products have no table — they live inside `product_catalog`'s versioned JSONB. A removed product therefore leaves the reference intact and the screen resolves it against the current catalog, saying plainly how many are missing. That is `keptForCatalog`, already built for [B-005](../BUGS.md).

### The read model, and what it refuses to carry

A row carries **name, state, version, products, last changed**. Not the criteria: nobody reads *"Fintech · US, UK · 100–1000"* across forty rows — they read names, find the one they meant, and open it.

**No precomputed counts.** The count worth having is *"how many opportunities did this segment produce?"*, no module can answer it, and a stored product count would be a copy of a joined fact that goes stale the moment a version publishes.

**Paged on `(created_at, id)`.** The first draft paged on `(name, id)` because a customer finds a segment by name — and the platform's `CursorPosition` is `(datetime, UUID)` and frozen, so that would have been a type lie to save the client a `sort()`. **Alphabetical is a display concern** until a workspace actually pages; a server-side name sort needs its own cursor and waits for evidence.

**Archived segments are excluded by default and never hidden.** They are retired, not deleted — everything Signora found under one was found *because* of it.

### Continuing this module

- **The list is the only surface today.** Create, edit, publish, archive, restore and duplicate are ICP-02 onward, and until they exist the only segments a workspace has are the ones the migration produced.
- **Never add a verdict.** `tests/commercial_profile/test_boundary.py` reads the domain as a syntax tree and refuses any identifier naming a judgement; *effectiveness*, *health* and *"is this too broad?"* all need matching, and matching needs [C-002](../LANE_COORDINATION.md).
- **A consumer cites `(segment_id, version_id)`** — identity says *which segment*, version says *which definition*. Citing only the version loses the first and is the one shape that would create debt.


---

## The ICP has no consumer, and that is a capability gap rather than a wiring one

**Recorded 2026-08-03, from the end-to-end journey review ([48](48-customer-journey-review.md) §6a).**

`commercial_profile/public/` publishes **only** `TargetAccountReader`. **No module imports an ICP.** A customer can spend real effort describing who buys each product, and nothing in the platform uses it — so today an ICP is *stored information rather than operational intelligence*.

**Twelve candidate consumers were tested, and the result is not what "wire the ICP in" implies:**

> **Almost nothing should consume the ICP directly. Most consumers need to know whether a company *matches* it — and matching has no owner.**

**Two modules would consume the description itself**, and both are unbuilt: **company discovery** (an ICP *is* the search criteria) and **AI Research** (the ICP is prompt context). Everything else — a score, a ranking, a prioritisation — needs a **match result**, and this module *"records a description; it never matches anybody against it"*, by design and by a boundary test that reads the domain as a syntax tree.

**Matching is blocked by [C-002](../LANE_COORDINATION.md)**, the anticorruption layer between a customer's free-text *"mid-market fintech"* and Provider Normalization's canonical vocabulary — open since M12.5 and named in this document's own *revenue band* discussion.

**The consequence for whoever continues this module:** *"connect the ICP to the pipeline"* is not a Commercial Profile slice. **It is a decision about who owns matching**, and doing it here would put free-text comparison inside the module whose entire guarantee is that it holds no judgement.

---

> ⚠️ **The two sections below were briefly in a second file, and it should never have existed** ([B-126](../BUGS.md)). Lane B wrote them into `25-commercial-profile.md` at TASK-434 — **colliding with `25-signal-engine.md`, and duplicating the document you are reading.** A module has one design doc; this is it, and it was already numbered `40`.
>
> **Merged here and the second file deleted, rather than renumbered.** Renumbering would have kept two design documents for one module, which is the defect §2 names — *"truth has exactly one authoritative representation"* — and the number collision was only the symptom that made it visible. **No new document number was allocated, which is the better outcome given B-126's finding that document numbers have no allocation block.**

## TASK-434 — an account can be asked whether it matches a criterion

**Delivered 2026-08-05 by Lane B.** **The capability [C-330](../LANE_COORDINATION.md) asked for**, and the loop that produced it is worth recording because it is the governance working rather than a lane being clever.

This lane claimed TASK-406, found that lift needs a predicate nothing could supply, and **refused to invent one inside a slice**. The product owner declined the framing and broadened it — *"a foundational platform capability that multiple future product areas will depend upon"*. Product Office assessed it in [443](443-account-matching-capability.md) and found it is three problems, not one. [D-077](../DECISION_REGISTER.md) sequenced it ahead of its dependent. **No workaround was built at any point, and the interim one that was permitted was never needed.**

### Why the matcher lives in the module that records the declaration

**The criterion vocabulary is defined here** — `industries`, `countries`, `EmployeeRange`, `validate_criterion_list`. A matcher built anywhere else needs a second copy of it, and the copy nobody maintains is the one that decides whether an account is in its own ICP.

**And it does not breach the contract this module lives under.** `pyproject.toml` forbids `commercial_profile` from importing the pipeline — *"commercial_profile declares; it never reads the pipeline"*. `evaluate` **reads nothing**: it imports no module, queries no repository, opens no session and knows no caller. **The prohibition is on reaching for the pipeline, and being handed a value is not reaching** — which is what lets the ruled dependency direction hold while the comparison stays where the vocabulary is.

### Two invariants, both in the type rather than the prose

**A verdict is a category with a reason and never a number.** `MatchStrength` established this in resolution; the same door would open here. A number invites a weight, a weight invites a threshold, and a threshold is a propensity judgement this module has no standing to make. **There is no score, confidence or weight on anything in `matching.py`**, and `test_boundary.py`'s domain scan would fail if there were.

**`UNMEASURED` is never `NO`.** The customer declares free text; the pipeline observes canonical values. Under string equality `SaaS` against `Computer Software` returns *no match*, and the account **silently drops out of its own ICP** — a wrong answer that looks decided. Absence of an observation and absence of a match are different facts, which is the same distinction the product owner ruled for search groups at TASK-408 on the same day.

### What is deliberately not here

**No overall verdict.** Rolling three answers into *"matches"* needs a rule for `UNMEASURED`, and every available rule is a judgement — treat it as a pass and an unmeasured account looks qualified, as a fail and it looks disqualified. **That rule belongs to whichever consumer has a reason for it**, stated where a customer can see it.

**No synonym catalog.** Case and spacing are folded, which is not interpretation — the same string typed twice. Anything cleverer decides what two different words mean, and 443 records that as a **reviewed catalog** to build *"when `UNMEASURED` shows it is losing accounts"*. **The limitation is asserted in a test** so it stays visible rather than being discovered by a customer.

**No lift and no backtest.** That is TASK-406, which is sequenced behind this.

### The published surface

`IcpReader` is the module's **third published read and its thirteenth view** — and the first that carries the criteria. Until it existed no module could read them at all, which is how sixteen consumers accumulated behind a capability nobody could build. `notes` is **not** published: it exists to be read by a human and is explicitly *"never parsed"*, so publishing it would invite exactly the parsing it forbids.

*+23 tests. 3600 backend passed, coverage 95.37%; `icp_reader.py` 100%, `matching.py` 95%.*

> ⚠️ **`matching.py` became `evaluation.py` on 2026-08-05**, after the product owner ruled [C-420](../LANE_COORDINATION.md) / [D-087](../DECISION_REGISTER.md). **`Match` carried two concepts and now carries none alone**: **Identity Resolution** is `MatchStrength` in `knowledge_graph` — ratified 2026-07-29 and unchanged — and **Criteria Evaluation** is this. **The good word had already won at the call site**; only the filename disagreed, which made it 🟢 and module-internal. **The window was open because nothing outside the module ever imported the path**, and `public/` never exported the predicate.

---

## Epic C preparation — the one piece that is this module's, and the question in it

**Prepared 2026-08-05 by Lane B.** [TASK-201](../BACKLOG.md) is blocked on [B-205](../BUGS.md) — three documents disagree about whether the People context is buildable — and the product owner ruled *"do not implement against conflicting governance documents."* **Nothing here implements.** It records what this module's share would be, so that when Lane C reconciles the documents the work is scoped rather than surveyed.

### What TASK-201 names as this module's

*"`commercial_profile` (a stable role id, Lane B's)"* — one item, and it does not exist today.

`CommitteeRole` carries **`title` and `part`, and no identifier**. `BuyingCommitteeRoleView` publishes the same two. So nothing outside this module can refer to a particular seat; it can only describe one.

### Why an id is wanted, and why it is not trivial

Epic C's narrowed scope is **role-based intelligence** — C-221: *"do NOT expand the architecture around people… focus on role-based and organization-level intelligence."* **A role that cannot be named cannot be tracked**, so *"the CFO seat has been vacant since March"* needs the seat to have an identity that survives a re-declaration.

**And that is the difficulty.** A committee is stored as a **versioned JSONB declaration**, so:

- **Existing declarations carry no ids**, and they are immutable historical records — *"a change is a new version, never an edit"*. **Ids cannot be backfilled**, only assigned going forward.
- **A derived id would not be stable.** `(product_id, title, part)` identifies a seat within a version, but renaming *"VP Finance"* to *"CFO"* would mint a new identity for the same seat — which is precisely the tracking the epic wants, broken.
- **A minted id must survive the next declaration**, which means the write path has to match an incoming role to an existing one — and matching by title is the same instability wearing a different coat.

> ⚡ **Answered and built, 2026-08-06 — and the answer removed the difficulty rather than solving it.**
>
> **The id is *derived*, not minted**: `seat_id(product_id, title)`, a `uuid5` in a pinned namespace. **Every objection above was an objection to storing one.** Existing declarations are immutable and carry no ids — so a derivation gives them one for free, and there is nothing to backfill because there is nothing to fill. §2 arrives as a practical dividend rather than a rule to obey: *"a stored copy of a derivable fact is a defect."*
>
> ⚠️ **The rename limitation is unchanged and is now asserted in a test.** *"VP Finance"* becoming *"CFO"* is a different seat, and a citation to the old id points at one that no longer exists. **Carrying identity across a rename needs somebody to say *"same seat, renamed"* — which only an editing surface knows, and none exists.** Matching on write by title has the same weakness plus a stored field, which is why it was not chosen. **Trigger for revisiting: a consumer that needs identity to survive a rename, whose own need decides the shape.**
>
> **Published as `BuyingCommitteeRoleView.id`** and derived on read in `committee_reader.py`. **`SEAT_NAMESPACE` is pinned by a test**, because changing it re-identifies every seat in every workspace.

> **That is a real design question and it is the whole of this module's piece.** It is recorded now rather than discovered mid-slice, and it is **not** answered here: the shape of a role's identity is architecture, and B-205 shows the surrounding documents do not yet agree on the epic it serves.

**Nothing is blocked on it today.** `BuyingCommitteeRoleView` gaining an `id` is additive (§9), and no consumer asks for one yet.


## TASK-466 — a customer's own labels, and the module's first non-declaration

> **Status: as built, 2026-08-13.** [ADR-0411](adr/0411-customer-organized-account-metadata.md) ratifies the capability; [D-235](../DECISION_REGISTER.md) rules the three questions building it raised.

### Why it is in this module at all

**Decided by authorship, which is [ADR-0411](adr/0411-customer-organized-account-metadata.md)'s own rule:**

> *"These are customer-authored organizational concepts, distinct from provider/CRM commercial facts… They therefore must NOT be merged with C-209 / ADR-0409."*

The Knowledge Graph publishes *"identity and evidence, never a resolved value"* — everything in it traces to a provider. **Nobody asserted a customer's own tag.** `commercial_profile` is the only bounded context here whose author is the customer, so a label a seller puts on an account is the same *kind* of sentence as what they sell and who buys it.

**Counter-evidence, recorded because a future reader will find it:** `target_accounts.py`'s docstring says *"who works an account is the Opportunity Engine's, and it already has an assignment model."* That file predates ADR-0411, the ADR decides by authorship, and the ruling wins. The note is stale rather than wrong.

### A label is not a declaration, and the grants differ

| | The six declarations | `account_tag` |
|---|---|---|
| **Shape** | A complete statement, versioned | A label, corrected in place |
| **`UPDATE` grant** | ⛔ None — a revision is a new row | ✅ Granted, `USING` **and** `WITH CHECK` |
| **Why** | Editing destroys the record of what was said | A rename is a correction to a customer's own filing, and versioning it would keep a history nobody would ever cite |

`account_tag_assignment` carries no `UPDATE` grant and sits in `IMMUTABLE_TENANT_TABLES`: an assignment is made or removed, and there is no third thing to say about it.

### Identity is not the name

Without an id, renaming *At risk* to *Churn risk* is indistinguishable from deleting one label and creating another, and every account would silently lose it. **The same reasoning `target_accounts.py` records for its entries.**

Uniqueness is `(workspace_id, lower(name))` as a functional index. **The domain folds with `casefold` and Postgres has none**, so the two agree on everything a customer types and the domain is the stricter — which is the safe direction: it refuses pairs the index would allow, never the reverse.

### The tone is the customer's, and `ai` is unreachable

The design draws four chip tones — `risk`, `warn`, `pos`, `neutral` — and a fifth, `ai`, reserved for what Signora inferred. **`TagTone` has four members and the frontend map is total over exactly those four**, so a human opinion cannot wear the platform's mark. Asserted in both tiers.

### 🔴 The reversal rule, which is the hardest thing in this slice

> **Reversing *Add tag* is NOT *remove the tag from those accounts*.**

If three of forty-one selected companies were already tagged in June, taking the batch back must leave those three — **they were not this batch's doing**, and stripping them destroys a fact the customer authored and never asked to undo.

So `TagApplication` records what **changed**, and `inverse()` may read nothing else. `account_tag_batch.changed` is **nullable and the null is load-bearing**:

| | |
|---|---|
| `NULL` | Not applied yet. Nothing to reverse |
| `[]` | Applied, and every selected account already had the tag. **Still nothing to reverse, for a different reason** |
| `[…]` | Applied. Reversal removes exactly those |

**A boolean expresses two of three**, and a caller reading *nothing to reverse* as *never applied* would offer undo on a finished batch.

### How a batch travels, and what this module does not own

```
  screen ──propose──▶ commercial_profile ──propose──▶ action_batch
                        (payload row)                  (the batch)
                              ▲                              │
                              │        action_batch.applied  │
                              └──────────────────────────────┘
```

**`propose` is the only write `action_batch` publishes** ([D-235](../DECISION_REGISTER.md) ①) — approval is a human decision on a screen, and a consuming domain may never approve. Both writes happen on **one session**, which is what makes *no batch-without-payload* true rather than aspirational.

**The work returns as an event.** `apps/worker/subscriptions.py` hands handlers a generic `EventEnvelope`, so **this module imports nothing from `action_batch`** except the published `propose` port. A batch this module did not propose is silent rather than an error — the Action Batch is a shared lifecycle.

**The reversible window is `action_batch`'s to enforce**, not re-checked here: `has_settled` lives there, and a second implementation would let the two disagree about whether a customer may still undo something.

### What is NOT built, and each has a reason

| | |
|---|---|
| **`remove` on the tag port** | Written and cut. This row draws no delete control, and deleting a tag cascades every assignment — the first caller should arrive with a confirmation designed for it |
| **Segments** | [D-235](../DECISION_REGISTER.md) ② settles the naming; the enumerated grouping itself is unbuilt |
| **Owner / CSM** | [ADR-0411](adr/0411-customer-organized-account-metadata.md) ratifies it; not started |
| **An approvals screen** | [C-1507](../LANE_COORDINATION.md) — the lifecycle is complete at the API and **no screen approves a batch** |
| **The reversible window's number** | [C-1506](../LANE_COORDINATION.md) — 24 hours is the design's number for *imports*, and is an inference here |


---

## TASK-1479 ⓶ — who owns an account, and who looks after it

**[ADR-0411](adr/0411-customer-organized-account-metadata.md)'s second capability.** Tags shipped as [TASK-466](../BACKLOG.md); this is **Account Owner and CSM**. ⛔ **Segments is the third and is deliberately not here** — see the last section.

### ⛔ A reference to a member, never a name

📁 **The ruling's own words**: *"A reference to a workspace **member**, not free text. A person who leaves must not leave a dangling string — the reference is what makes removal answerable."*

⚡ **So `account_assignment` stores a `member_user_id`**, and the screen resolves it against the member list it already holds. **No name is stored, and none travels on the response** — a name would be stale the day somebody changed theirs, and it is the duplicated identity the reference exists to avoid.

🔴 **A reference that is never verified is free text with a `UUID` type.** `AssignAccounts` refuses a user who is not a member of this workspace, **before anything is written**, through `WorkspaceQueryPort` — 📁 the approved synchronous cross-module read at [05-module-dependencies.md](05-module-dependencies.md) line 60, *sync, for workspace scope*. ⛔ **This module keeps no copy of a membership**: a cached one would be a second representation of a tenancy fact, and the copy is the one that is wrong the day somebody leaves.

⚠️ **Membership is checked twice and it is not redundant.** At proposal, so a customer is refused immediately rather than after approval; and again on apply, **because a member who leaves between proposing and approving must not be assigned on acceptance.** Two moments, two checks, because the answer can differ between them.

### ⚡ Row per role, and the reason is the inverse

**Two nullable columns on the account would also refuse a second owner.** The row shape — `(workspace_id, account_id, role)` as the primary key — is chosen for what it does to the **reversal**.

📁 [ADR-0405](adr/0405-an-action-is-approved-before-it-is-effective.md) puts the inverse with the domain that performed the operation, and **the inverse of *"set the owner on these forty accounts"* is *"restore what each one had"*** — which needs a prior value **per account**, not a column that can hold one.

### 🔴 The reversal, which is the hardest thing in this slice and was wrong twice

**`Reassignment` carries `previous` — accounts that actually moved, with who held each before — and `inverse()` returns it and never `unchanged`.** ⛔ Reversing an account that did not move would take an owner away from somebody who always had one.

**Two defects were found here, and neither by reasoning:**

| | |
|---|---|
| **The absences** | ⛔ An account that had **no** owner before must end with **no** owner. **Writing nothing for a `None` leaves the new owner in place**, so the reversal reports success while half of it did not happen. **Found by writing the naive version and running the tests** |
| **The world moved** | 🔴 `restore` was **unconditional** — it wrote the prior state over whatever it found. **The batch set an owner, a colleague chose a different one, and *take it back* silently discarded their choice.** ⚡ **A lost update wearing an undo's clothes.** **Found by QE naming an axis this lane had not tested** |

⚡ **The distinction the fix turns on:** `restore` was doing ***"make the world look like it used to"*** when what the customer pressed was ***"undo my change"***. **Those are different operations and only the second is what the button says.**

✅ **So `Reassignment` carries `assigned_to`** — what the batch put there — **and every write in `restore` is conditional on that value still being in place.** An account somebody else has since claimed is left alone; a second reversal finds nothing matching and does nothing. **The condition cannot be recomputed later, which is why it is stored on the batch row.**

### ⚠️ The one question this slice did NOT answer

📁 **[C-1510](../LANE_COORDINATION.md)**: **what may *take it back* do when the previous owner has left the workspace?**

⛔ **The shipped path restores faithfully** — the prior holder was a member when the batch ran, and replaying that is the batch's own change undone. ⚠️ **QE's counter is stronger than the argument in the code**: *"an account silently owned by somebody who cannot open it is worse than an account with no owner, because the empty state is visible and the invalid one is not."*

**Two live options and a third this lane would propose** — restore faithfully **and report** which accounts returned to somebody who has since left — **are in the register.** ⛔ **Not decided here**: the shipped behaviour is an encoded assumption, documented rather than silent, and that is what makes it an item rather than a note.

### The screen

**The Companies table's Owner column**, and 📁 [`table.ts`](../../frontend/lib/accounts/table.ts)'s own header is corrected: **two of its five source-less columns now have one.** ⚡ **Three states, and only one of them is *nobody*** — an unread answer renders **nothing**, an account held by somebody no longer in the member list says so, and a genuinely unassigned account says *Unassigned*. 📁 [P-A](../DOMAIN_DISCOVERY_REGISTER.md)'s loading cousin, which [C-226](../LANE_COORDINATION.md) found six times on one screen.

### ⛔ Segments is not here, and the reason is this module's own vocabulary

📁 **ADR-0411's third capability is *"a named, saved grouping of accounts"*.** 🔴 **`commercial_profile` already owns the word**: [ADR-0041](adr/0041-icp-aggregate.md)'s ICP **is** *"a named customer segment"*, served at `/workspaces/{id}/icp-segments` under the summary *"Every customer segment this workspace sells to."*

⚠️ **Two customer-facing meanings of one word in one bounded context is [§4](../../CLAUDE.md)'s exact prohibition**, and **the honest answer may be reuse rather than construction**: `workspace_tenancy`'s `SavedView` is already a named, versioned, immutable, workspace-scoped **declaration** — which is what *"a stored predicate"* means, and ADR-0411 §3 leaves that choice to this lane.

⛔ **Routed to Product Office rather than decided inside a slice**, because it is vocabulary and ownership rather than implementation.

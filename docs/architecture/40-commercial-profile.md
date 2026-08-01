# 40 — Commercial Profile (module design)

> Status: **As built** — slices 1–4 of 5. Lane B.
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
| 5 | Target account list | — | — | 5 |

Every one is **versioned, immutable and superseded**: a revision is a new row naming the one it replaces, the app role holds no `UPDATE` grant, and the repository offers no method the database would refuse. `DELETE` *is* granted — erasability is a property of the tenancy model, not a statement about what a row means.

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

## Slice 5 is paused, deliberately

**It carries the first edge this module has ever had** — `commercial_profile → provider_platform`, typed **Customer–Supplier** in [05-module-dependencies.md](05-module-dependencies.md), whose rule is that *the downstream lane's needs shape the contract*. Drawing it alone and asking afterwards would produce a contract shaped by the producer, which is the one failure that pattern exists to prevent.

**The seven open questions live in [`LANE_COORDINATION.md` C-001](../LANE_COORDINATION.md#c-001--the-target-account-contract)**, with Lane B's opening position on each, and are deliberately not repeated here. **Lane B will not begin slice 5 until that item is `ANSWERED`.**

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

Each section shows your own words back to you, each version line names you and the date, and every earlier version is still stored. The four are versioned separately: renaming the product leaves the other three where they were. Open the page in a second browser, save from both, and the second is told a colleague got there first rather than quietly losing the work.

**Nothing on any of the four screens grades a company, a person or a committee against what you typed, and nothing ranks anything** — those are different modules' jobs, and they are not built.

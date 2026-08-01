# 40 — Commercial Profile (module design)

> Status: **As built** — slices 1 and 2 of 5. Lane B.
> Ratified by [ADR-0035](adr/0035-commercial-profile.md), which remains the module's architectural decision record and is **not** superseded by this document. The ADR says *why the bounded context exists*; this says **what was built inside it**, in the manner of [22](22-knowledge-graph.md)–[29](29-ai-reasoning-engine.md).
>
> Created 2026-08-01 with slice 2, because the module had no design document and `CLAUDE.md`'s reading order sends a session to one. A cold Lane B session had the ADR and the code, and nothing recording the decisions taken *during* implementation.

## The boundary, restated because everything below depends on it

> **It records. It computes nothing, resolves nothing, matches nothing, and calls no provider.**

Two import-linter contracts enforce it: `commercial_profile` may import no pipeline module, and no module may reach past its `public/`. A structural invariant — `tests/commercial_profile/test_boundary.py` — reads the domain package as a syntax tree and refuses any identifier naming a judgement (`score`, `priority`, `rank`, `propensity`, `fit`, `weight`). **Widened in slice 2 from one file to the whole package**, because the second aggregate is where a judgement is far more likely to arrive: an ideal customer is one plausible-looking method away from a fit score.

## The aggregates

Several small ones, each versioned independently — never one profile object. Products change quarterly and a watch list changes weekly, and versioning them together would mint a version of everything each time anything moved.

| # | Aggregate | Table | Endpoint | Slice |
|---|---|---|---|---|
| 1 | `ProductCatalog` | `product_catalog` | `/workspaces/{id}/products` | 1 ✅ |
| 2 | `IcpDeclaration` | `icp_declaration` | `/workspaces/{id}/icp` | 2 ✅ |
| 3 | Buying-committee role templates | — | — | 3 |
| 4 | Business priorities | — | — | 4 |
| 5 | Target account list | — | — | 5 |

Every one is **versioned, immutable and superseded**: a revision is a new row naming the one it replaces, the app role holds no `UPDATE` grant, and the repository offers no method the database would refuse. `DELETE` *is* granted — erasability is a property of the tenancy model, not a statement about what a row means.

**Currency is `MAX(version)`, never `supersedes IS NULL`.** On an immutable table the *new* row names its predecessor, so a null `supersedes` marks the first version permanently. `uq_(workspace_id, version)` is therefore the concurrency control: two callers who both read version 3 both build version 4, and the second insert is refused by the constraint rather than silently winning.

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

**Revenue is excluded, and the reason generalises.** `RevenueBand` already exists as a controlled enum in Provider Normalization's canonical vocabulary. Declaring revenue here would mean either importing a pipeline module — which the boundary forbids outright — or defining a second `RevenueBand`, which *truth has exactly one authoritative representation* forbids more firmly. Neither is acceptable, so revenue waits for a decision rather than arriving as a quiet copy. **Any future criterion whose value space is already a controlled vocabulary hits the same wall.**

### The one judgement the domain makes

A profile with no industries, no countries and no size is **refused**. It is not a statement: it describes every company on earth, and it is indistinguishable from having said nothing — which a customer can already say by leaving the product out. This is a judgement about the *statement*, not about the world, which is the only kind this module is permitted.

An **empty declaration** (no profiles at all) is legal. *"We describe nobody"* has an author and a moment, which is what makes it different from never having said anything.

### Refusals a customer can act on

| Code | Status | When |
|---|---|---|
| `icp_version_conflict` | 409 | A colleague saved first. Reported **before** any product check — a stale caller's product list is stale too, so naming the product would send them to fix the wrong page |
| `icp_unknown_product` | 422 | A profile names a product not in the current catalog. The only refusal here fixed on a different page, which is why it has its own code |
| `icp_refused` | 422 | Everything the domain refuses. Distinct from `catalog_refused` because the two are fixed in different places |

## Findings

**F-B1 — the ICP is stated in the customer's words; claims are recorded in Signora's.** A customer types *"United States"*; a provider claim carries whatever the canonical `COUNTRY` attribute holds. **Reconciling the two is what matching does, and matching has no owner today** (ADR-0035 records it as a Knowledge Graph slice: *generalise `select_name` to industry and size*). This module deliberately does not pre-solve it — translating at declaration time would be resolution, in the module least equipped to review it. Recorded so whoever builds matching finds it stated rather than discovers it.

**F-B2 — a controlled value space cannot cross this boundary.** See *revenue is excluded*. The general form: **a declaration criterion whose values are already a canonical vocabulary needs an architectural decision before it can be declared here.** Three candidates queue behind it — revenue band, technology, intent topic. Not a defect; a decision nobody has been asked for yet.

**F-B3 — `04-modules.md` and `05-module-dependencies.md` are stale by two rows, and Lane B may not edit them** (🔴, `docs/architecture/01`–`21`). For the integrator at merge, the exact edits:
- `04-modules.md`, Commercial Profile manifest → **Endpoints**: add `/workspaces/{id}/icp`; **Tables**: add `icp_declaration`.
- No dependency edge changed. Nothing new is imported, nothing new is published, and the graph is untouched.

**F-B4 — `signal_profile`'s inverted supersession is still open** (found in slice 1, recorded in `PROJECT_STATUS.md`). Both of this module's aggregates read `MAX(version)` and are unaffected. It becomes reachable the moment the signal profile gets a write API — **Lane A's module, Lane A's fix.**

**F-B5 — the module's endpoint tests live in `backend/tests/integration/`, which §20e assigns to QE.** Slice 1 set that precedent and slice 2 followed it rather than inventing a second location mid-module. Worth a ruling: either they are *a module's own suite* wherever they sit, or they move under `tests/commercial_profile/`. Raised, not decided.

## Deliberately deferred

- **The fourth duplication.** `PublishProductCatalog` and `DeclareIcp` share a shape — read current, compare version, build, save — and the two repositories share another. Duplicated at two instances on purpose: extracting a `Declaration` base from two examples would be guessing at the third. **Trigger: slice 3.** What *was* shared in slice 2 is a constant and an error (`domain/declaration.py`), because *"nothing has been declared is version 0"* is one fact and a second copy is how two aggregates start disagreeing.
- **Retracting a description** without deleting a product. A customer removes the last profile instead; a first-class *"we no longer sell to anybody"* has no evidence behind it yet.
- **A `TagField` in `components/ui`.** One screen needs it, and a shared component added for a single caller is one every later caller has to bend (§20c). It moves when a second screen wants it.
- **`public/` stays empty.** Nothing downstream consumes a declaration until slice 5's `TargetAccountReader`. Publishing a reader now would be a contract with no counterparty.

## How to see it

Sign in as an owner, open **Settings → Your business → Products**. Declare a product, then describe who buys it: industries and countries in your own words, a size range in people, and a note. Save. The row shows your description back to you, the version line names you and the date, and every earlier version is still stored. Open the same page in a second browser, save from both, and the second one is told a colleague got there first rather than quietly losing the work.

**Nothing on the screen grades a company against what you typed** — that is a different module's job, and it is not built.

# ADR-0041: The ICP aggregate — a named segment, and the products it buys

**Status:** **Proposed, not accepted.** Lane B, 2026-08-02, after the reuse audit ([C-303](../../LANE_COORDINATION.md)) and an adversarial review of the audit's own recommendation.

> **This ADR reverses the recommendation the audit made hours earlier.** C-303 §3 recommended **Option B** — an ICP names exactly one product. Challenging that recommendation on the product owner's direction found the reasoning contained a conflation, and the conclusion does not survive it. **The change of position, and the specific error, are recorded in §2 rather than quietly corrected.**

---

## Context

An ICP has no identity today. `ProductIcp` is a value object inside one workspace-wide `IcpDeclaration`, addressed by `product_id`, with no id, no name and no lifecycle; a second ICP for one product is structurally refused. Every verb the ICP Management brief asks for — create, duplicate, archive, restore, activate, default, draft, search, compare, per-ICP history — needs an identity and a lifecycle that do not exist.

**Nothing downstream consumes an ICP.** `commercial_profile/public/` publishes only `TargetAccountReader`. There are no consumers to migrate and no event contract to version, which is what makes this change cheap now and expensive later.

The product owner ruled that **ICP remains inside Commercial Profile** — identical ubiquitous language, identical invariant, identical lifecycle, and an ICP references a product from this module's own catalog — and asked one question to be answered with evidence before implementation: **is Product the strongest aggregate root for ICP ownership?**

---

## Decision

> **An ICP is a *named customer segment*, owned by a workspace, that names **one or more** products from that workspace's catalog. Never zero.**

```
Icp
├── id            identity — the thing every verb in the brief needs
├── name          the customer's words: "Mid-market Fintech", "UK Insurance"
├── products      1..n, from the catalog. Never empty
├── criteria      industries · countries · employees · notes   (unchanged)
├── state         draft · active · archived
└── version       immutable content, superseded — unchanged
```

**This is Option E.** It was not among the four options C-303 offered, and it emerged from taking the product owner's own bundle example seriously.

---

## 1 · Why Product remains the aggregate root — the challenge, answered

**The question was whether customers think in products, offerings, bundles, product families or GTM motions.** They think in all five, and the evidence says that is an argument about *cardinality*, not about *ownership*.

**Product stays the anchor, for three reasons that survive the challenge:**

**It is the only one of the five that already exists as a reviewed, identified thing.** `Product` is in the catalog, has a stable id across every catalog revision, and is what a customer already maintains. *Offering*, *bundle*, *family* and *motion* are none of those — introducing one would mean asking a customer to model their commercial structure twice before describing a single buyer.

**It keeps the sentence that makes an ICP citable.** *"The kind of company that buys **what we sell**"* is what every future consumer will ask. An ICP anchored to nothing is *"companies we like"* — vaguer for a customer to reason about and much vaguer for a consumer to act on.

**A bundle is expressible without being modelled.** *"Revenue Cloud + CPQ + Billing, sold together to mid-market fintech"* is **one ICP naming three products.** The customer's commercial structure is described by the ICP itself, which is exactly where it belongs — it is a fact about who buys, not a second catalog.

> **The correction is to cardinality, not to ownership.** Product remains the anchor; **one ICP may anchor to several.**

**If a customer later needs *offering* as a first-class thing** — priced, versioned, sold as a unit — that is a Product Catalog change, not an ICP one, and this design does not foreclose it: an ICP naming an offering instead of three products is the same shape with a different referent.

---

## 2 · The self-challenge, and where the earlier recommendation broke

**Option B was recommended six hours ago. It is wrong, and the error is specific.**

C-303 §3 stated Option C as *"an ICP is a named segment; product is one criterion among many (**0..n** products)"* and rejected it because *"an ICP naming no product is 'companies we like'"*.

> **That rejection is sound and it rejects the wrong thing.** It is an argument against **optionality** — the `0`. It was applied to **multiplicity** — the `n` — and the two were never separated. **Nothing about letting an ICP name three products requires letting it name none.**

**Once separated, B does not survive its own strongest counter-example** — which is the product owner's:

| | A company sells Revenue Cloud, CPQ and Billing as one offering to one segment |
|---|---|
| **Under B** | **Three ICPs**, identical but for the product. The customer maintains three copies of one description, and **they will drift** — the first time somebody adds *"only where they already run Salesforce"* to one of them |
| **Under E** | **One ICP naming three products.** What the customer said, once |

**Duplicated truth is this repository's most-cited failure mode**, and B does not merely permit it — **B makes it the only way to express a real and common commercial arrangement.** The workaround is *duplicate* (JI4), which produces the drift by design.

**The decisive test, and it is the repository's own:** *make incorrect architecture impossible.*

- **Under B**, *"one segment, three products"* is unrepresentable. The customer works around it, three sources of truth exist for one segment, they diverge, and **nothing in the system refuses it** — because from the model's point of view three unrelated ICPs is a perfectly ordinary state.
- **Under E**, *"one segment, one product"* is representable exactly. **E is a strict superset of B with no added optionality**, so it forbids nothing B allows and permits one thing B forces a workaround for.

**E strictly dominates B unless the extra structure costs something real.** It costs a join table and a slightly richer uniqueness rule. **The migration cost is identical** — under both, each existing `ProductIcp` becomes one `Icp` naming one product, 1:1, no data loss, no judgement call.

### The strongest argument *for* C, stated fairly

**Some customers have a company-level ICP before they think per-product** — early-stage, one product, or a founder describing their buyer before the catalog is filled in. C's optional product removes friction at first value, which is the moment friction costs most.

**It does not carry**, for a reason that is already settled and load-bearing: the module *already* requires a product before an ICP — *"you cannot describe who buys something you have not said you sell"* — and a workspace with one product has a one-product catalog, so naming it is one click, not a modelling exercise. **The friction C removes has already been paid**, and C would buy it back at the cost of every consumer branching on whether an ICP names anything.

### The strongest argument *against* E

**Two, and both are real.**

**A product-scoped screen becomes ambiguous.** *"Which ICPs apply to Revenue Cloud?"* can return an ICP that is mostly about two other products. **Answered by the customer having chosen it** — an ICP spanning three products is a statement they made deliberately, and a screen showing it under each is showing the truth. Under B it would return only single-product ICPs, which is tidier and less true.

**`default` becomes harder to define**, and that is §3.

---

## 3 · `default` is challenged, not designed

**The brief asks for a default ICP. E makes it awkward to define — and that awkwardness is evidence worth surfacing rather than engineering around.**

An ICP spanning three products cannot be *"the default"* for one of them and not the others without inventing a per-product override. But before building that:

> **What job does `default` actually do?**

**In a single-ICP world it has an obvious one:** there is one description, and it is the one Signora uses.

**In a multi-ICP world it may have none.** If Signora monitors and prioritises accounts matching **any active ICP**, then *"which one is default"* never needs answering — `active` carries the whole meaning, and `default` is a leftover from the model being replaced.

**Lane B's position:** `active` / `draft` / `archived` is the lifecycle; **`default` is not implemented in Day One** unless a customer question is named that `active` cannot answer. **If one is named, it is a product-scoped pointer** — *"when something must pick one ICP for Revenue Cloud, pick this"* — and it belongs to whichever capability has to pick, not to the ICP itself.

**This is the Connection Center rule applied to a field:** do not ship a control whose meaning the product cannot state.

---

## 4 · Long-term evolution, three to five years

| Horizon | B | **E** |
|---|---|---|
| **Bundled offerings** | Duplication, drift, and eventually a customer asking to link ICPs — which is E, arrived at through a migration under real data | Native |
| **Offering as a first-class concept** | ICP re-anchors from product to offering — a breaking change for every consumer | ICP names an offering *or* products; the join changes referent |
| **Per-ICP signal relevance, scoring, discovery** | Works | Works |
| **Effectiveness measurement** (elsewhere) | Per-ICP metrics | Per-ICP metrics, and **per-product metrics need the join** — which E has and B derives |
| **Marketplace / shared templates** | A template is an ICP without a workspace. Same under both | Same |

**The asymmetry that matters:** **B's failure mode arrives as a data migration under live customer data with real ICPs already drifted.** E's failure modes are screens that show a little more than a customer expected. **The first is expensive and irreversible; the second is a design iteration.**

---

## 5 · Downstream effects, module by module

**Every one of these needs *identity*, which B and E both provide.** The join is what separates them, and it matters in three.

| Module | Effect | B vs E |
|---|---|---|
| **Target Accounts** | Eventually *"we watch this account because of the EMEA ICP"* — a citation from a named list to a named segment | Same |
| **Provider Platform** | **The largest future consumer.** Discovery — *"find companies matching this ICP"* — cites one ICP id. Ownership boundaries stay exactly as [ADR-0036](0036-target-account-contract.md) fixed them | Same |
| **Knowledge Graph** | Matching needs an anticorruption layer between the customer's words and canonical values — **[C-002](../../LANE_COORDINATION.md), still open.** Nothing here pre-solves it | Same |
| **Signal Engine** | Relevance could vary per segment — *"funding rounds matter for enterprise, hiring for mid-market"*. **Per-ICP `signal_profile` scoping** | Same |
| **Buying Score** | A scoring model per segment. **Never per ICP-and-product**, which B would invite | **E cleaner** |
| **Opportunity Engine** | Records human commitment; unaffected | Same |
| **Analytics / effectiveness** | *"Which segment converts?"* is per-ICP. *"Which product converts?"* is per-product. **E answers both from one join; B answers the second only by grouping ICPs that happen to share a description** | **E materially better** |
| **AI Recommendations** | An ICP becomes prompt context. **A three-product ICP is one coherent paragraph; three near-identical ICPs are three, and the model cannot tell they are the same segment** | **E materially better** |
| **Billing / entitlements** | *"How many ICPs?"* as a limit. **Under B a bundled customer burns three for one segment** — a pricing artefact of a modelling error | **E fairer** |
| **Feature flags** | Unaffected | Same |
| **Notifications** | *"Your EMEA segment has matched nothing in 30 days"* — needs identity, and reads worse if it fires three times | **E cleaner** |

---

## 6 · Repository and boundary implications

**No module boundary changes.** ICP stays in Commercial Profile, on the product owner's ruling and the evidence in C-303 §4. No new cross-module dependency; no new bounded context; the dependency graph is untouched.

**The module's invariant is untouched and still guarded.** `tests/commercial_profile/test_boundary.py` reads the domain as a syntax tree and refuses any identifier naming a judgement — `score`, `rank`, `fit`, `weight`. **Nothing in this design introduces one**, and effectiveness explicitly stays out (§5).

**Storage is normalized**, on the product owner's direction and for a reason independent of everything above: `icp_declaration.profiles` is a JSONB array read whole on every request and rewritten whole on every save. **That is wrong at hundreds regardless of which option is chosen.**

```
icp            id · workspace_id · name · state · version · supersedes · criteria · audit
icp_product    icp_id · product_id                      ← the join E needs and B does not
```

**Two things stay exactly as they are**, because they are correct and load-bearing: **content is immutable and superseded** (a revision is a new row naming its predecessor; no `UPDATE` grant on content), and **lifecycle state is updatable on named columns only** — the same split ADR-0040 draws for notifications, enforced by the grant rather than by intent.

**Migration preserves every customer's data.** Each existing `ProductIcp` becomes one `Icp` naming one product, named from its product. **1:1, no data loss, no judgement call, and identical under B and E** — which is why the choice costs nothing to defer to the right answer and everything to get wrong.

---

## Consequences

**Accepted.** One join table. A product-scoped view that may show an ICP spanning other products. A migration that moves customer data — the module's first.

**Given up.** The simplicity of one product per ICP, and with it the tidiness of a product-scoped list that only ever shows single-product ICPs.

**Deferred, with reasons recorded:** `default` (§3) · effectiveness, health and *"is this too broad?"* — all of which need matching, and matching needs [C-002](../../LANE_COORDINATION.md) · templates and AI-assisted creation, which are provenance rather than new concepts · offering as a first-class catalog concept, whose trigger is a customer who prices a bundle as a unit.

**The risk worth naming.** E lets a customer put every product in one ICP and stop segmenting — the model permits a workspace with one ICP named *"Everyone"*. **That is not a modelling failure; it is a customer describing a real strategy**, and the honest response is the product asking *"is this too broad?"*, which it cannot answer until matching exists. **Recorded so nobody solves it with a validation rule** — refusing a broad ICP would be this module making a judgement about the world, which is the one thing it may never do.

---

## Alternatives considered

| | | |
|---|---|---|
| **A** | Keep product-keyed; *"multiple"* means multiple products | Does not satisfy the brief. Recorded so the rejection is visible |
| **B** | One product per ICP | **Recommended by C-303 and reversed here.** §2 |
| **C** | Product optional, 0..n | Optionality makes every consumer branch on whether an ICP names anything, and the friction it removes has already been paid |
| **D** | B with the product optional | Two meanings for one type |
| **E** ✅ | **1..n products per ICP** | This ADR |

---

## References

[C-303](../../LANE_COORDINATION.md) · [ADR-0035](0035-commercial-profile.md) · [ADR-0036](0036-target-account-contract.md) · [40-commercial-profile.md](../40-commercial-profile.md) · [ADR-0034](0034-ubiquitous-language.md) — *ICP* passes the test: a salesperson says it unprompted.

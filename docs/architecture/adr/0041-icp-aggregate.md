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
| **Provider Platform** | **Consumer** | **The largest future consumer.** Discovery — *"find companies matching this ICP"* — cites one ICP id. Ownership boundaries stay exactly as [ADR-0036](0036-target-account-contract.md) fixed them | Same |
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

## Amendment — 2026-08-02, after challenging Option E on the same terms

**Option E was challenged the way Option B was. It survives, and two things in the decision above are wrong as written.** Both are corrected here rather than edited into §1, so the reasoning that produced them stays readable.

### The identity test, and what it actually proves

> **"If Products were removed from the repository tomorrow, would an ICP still make sense?"**

**Yes.** *"Mid-market fintech in the US and UK, 100–1000 employees"* is a coherent, complete description of a customer segment — it is what a company puts in a strategy deck, and it needs no product to be understood.

**So Product is a relationship, not part of identity.** Option E is confirmed by the product owner's own test, from evidence rather than intuition.

**But the test also shows §1 justified the `1..n` rule wrongly.** §1 argued that an ICP must name a product because otherwise it is *"companies we like"* — an **identity** argument. The identity test disproves it: the concept stands on its own.

> **The real reason for `≥ 1` is actionability, not identity.** Signora exists to find accounts that will buy **something the customer sells**. An ICP naming no product cannot be acted on by any consumer — discovery cannot prioritise, scoring cannot attribute, analytics cannot answer *"which product converts?"*
>
> **That is an invariant about usefulness, and usefulness is a property of a *published* ICP, not of a draft.**

**Correction 1 — the rule binds at publication, not at creation.**

| State | Products |
|---|---|
| **Draft** | **May be empty.** A draft is incomplete by definition, and refusing to save one until a product is chosen is friction at exactly the moment of first value |
| **Published / archived** | **`≥ 1`, always** |

This also retires the argument §2 used against Option C. C's real appeal was *"don't force a product choice up front"* — and this gives that, without giving up the invariant where it matters.

### Correction 2 — identity and version are separate rows

§1 sketched `version` and `supersedes` on the `Icp` itself, carrying the existing `IcpDeclaration` shape forward. **That does not work once an ICP has a stable identity**, and the scenario that breaks it is the product owner's:

> *"If Product A is sunset, should historical opportunities still reference the same ICP?"*

**They must** — a citation from an opportunity, a signal or an analytics row points at *the ICP*, not at version 7 of it. If the versioned row **is** the ICP, every revision mints a new id and every citation ever made becomes unresolvable.

```
icp           id · workspace_id · state · created_at/by      ← stable. What everything cites
icp_version   id · icp_id · version · name · criteria ·
              supersedes · created_at/by                     ← immutable content
icp_version_product   icp_version_id · product_id            ← versioned with the content
```

**The product set is content, not identity**, which answers *"should product relationships be versioned?"* — **yes, and the join hangs off the version.** *"We added CPQ to this segment in March"* is a fact about a moment, and it is recoverable.

**`state` is on the identity row and is the one updatable thing** — the same split ADR-0040 draws for notifications, enforced by granting `UPDATE` on that column and no other. **Name is content**, so a rename is a revision: a customer renaming *"EMEA Enterprise"* to *"Europe Enterprise"* made a statement, and the previous one stays citable.

### The rest of the challenge, answered

| Scenario | Answer |
|---|---|
| **Can one ICP become the whole market?** | **Yes, and it must stay possible.** Recorded as the named risk in *Consequences*. **Never refused by validation** — refusing a broad ICP is this module judging the world |
| **Can it reference every product?** | Yes. **Bounded naturally by the catalog**; no arbitrary limit. `MAX_CRITERIA` guards typed text, and products are *selected*, so a typo guard has no job here |
| **Product removed from the catalog** | **The reference is immutable content and is kept.** The screen resolves it against the current catalog and says one is missing — which is **`keptForCatalog` and `DroppedWithTheirProduct`, already built for [B-005](../../BUGS.md)**. Same rule as *"store the fact, resolve the subject"* (ADR-0040 §2). **A published ICP whose every product is gone is unactionable, and the product says so rather than silently deactivating it** |
| **Product split** (Revenue Cloud → Pro + Standard) | **No concept needed.** Two catalog additions, one removal, and the customer revises the ICP. The aggregate absorbs it |
| **Products merged** | Same — a revision |
| **Product sunset, historical citations** | **Answered by correction 2.** Citations point at identity; content changes underneath them |
| **Products in different business units** | Structurally possible. **The repository has no business-unit concept**, so it is not ICP's to model. Recorded rather than designed around |

### Lifecycle — what Day One carries, and what the aggregate absorbs later

**Day One:** draft · published · archived · duplicate · version history · customer-authored.

**Absorbed without a structural change**, and each named so nobody builds it early:

| | |
|---|---|
| **Deprecated** | Another `state` value |
| **Merged · split** | Operations producing new ICPs whose first version names its predecessors. **The `supersedes` chain already expresses it** |
| **Imported · template-based · AI-generated** | **Provenance on a version**, not new lifecycles. AI-authored content additionally needs [ADR-0031](0031-evidence-citation-protocol.md)'s citation discipline before it ships |
| **Shared · copied across workspaces** | **Needs tenancy work this repository has not done.** A template with no workspace is a different tenancy shape, and it is out of scope rather than deferred |

### Migration reversibility — where it ends, exactly

**Forward is mechanical**: each `ProductIcp` becomes one `Icp` + one `icp_version` + one `icp_version_product`, named from its product. No interpretation, no heuristics.

> **Reverse is exact until the first write in the new shape, and ambiguous immediately after.**

| | |
|---|---|
| **Reversible without loss** | Every `Icp` whose current version names **exactly one** product, where **no product is named by two ICPs** |
| **Ambiguity begins** | The moment a customer creates a **multi-product ICP** (which `ProductIcp` cannot hold) or a **second ICP for one product** (which `IcpDeclaration.__post_init__` refuses). **Neither is representable in the old model, so a reverse migration would have to discard or merge — and both are lossy** |

**The practical rule QE needs:** **the migration is reversible until the first customer uses the capability it enables.** A rollback plan measured in hours is real; one measured in days is not. **Stated before implementation rather than discovered during it.**

## The publication-bound invariant, and it is not new

**The product owner asked for this to be documented as reusable. It is more reusable than expected — the repository already enforces it somewhere else, and nobody had noticed the two were the same rule.**

> **A draft exists for a human. A published artefact exists for the platform. If the platform cannot execute against it, it must not be publishable.**

**The second instance is the Prompt Registry.** `CLAUDE.md` §10: *"A prompt is not 'released' until it has been evaluated against the supported `(model, dataset)` combinations, and it may never be used with a pairing absent from that record."* A prompt may be written, revised and read at any time; **it may not be *released* until the platform can demonstrably execute it.**

**Identical shape, different module:**

| | Prompt Registry | ICP |
|---|---|---|
| **Freely created** | any version | a draft |
| **Gate** | evaluated against every supported pairing | names at least one product |
| **Why the gate** | the platform cannot demonstrate it works | the platform cannot act on it |
| **What the gate is *not*** | a quality judgement — `REFUSED` is a legitimate outcome | a judgement about the segment — a broad ICP is never refused |

**The last row is the part worth carrying.** In both cases the gate asks *"can the platform execute against this?"* and never *"is this good?"* — which is what keeps it from becoming a validation rule that judges the customer's business.

**Where it will recur:** signal profiles, playbooks, automation rules, campaigns, notification rules — anything a customer authors that the platform then acts on unattended. **Its permanent home is `CLAUDE.md` §2 if the product owner wants it; a lane does not write governance.** Stated here so the two existing instances are visibly one rule rather than two coincidences.

## Amendment 2 — 2026-08-02, challenging the version model

**Nine scenarios. Eight are absorbed; one breaks it, and the fix is a shape this repository already ships.**

### The break: a draft is not a version

*"Deleting Draft Version 7"* is the scenario that does not work, and the reason is that **the phrase contains a category error the model would otherwise inherit.**

If a draft is a version, an abandoned one leaves either a hole in the sequence or a version that was never a statement — **and the whole value of an immutable version chain is that every entry is something the customer actually declared.** A discarded draft is not.

> **Versions are published statements. A draft is not a version.**

| | |
|---|---|
| **`icp_version`** | **Only ever published content.** Immutable, sequential, and every row is something a customer said out loud |
| **A pending draft** | **Mutable working state**, at most one per ICP, deleted freely because it was never a statement. Publishing it **mints the next version** |

**This also fixes a state clash the earlier sketch had.** A published ICP being edited is not *"in draft"* — it is published, with a pending draft. So `state` describes the ICP's lifecycle and the pending draft is independent of it:

| Situation | `state` | Versions | Pending draft |
|---|---|---|---|
| Just created, never published | `draft` | none | yes |
| Live | `published` | 1..n | no |
| Live, being edited | `published` | 1..n | **yes** |
| Retired | `archived` | 1..n | no |

**And it answers the AI scenarios without a new concept**, which is the visionary challenge's real question: **an AI proposal is a pending draft with provenance**, and *"customer rejects version 9"* is discarding a draft. Nothing published, nothing to roll back, no approval state required for the simple case.

### The second correction: state is a transition log, not a column

*"Archiving Version 6"* is the other category error — **you archive an ICP, never a version.** State belongs to identity. But a mutable `state` column answers *"is it archived?"* and loses *"who archived it, and when?"*, which is exactly what the product owner's audit question asks for.

**The repository has already solved this**, in Opportunity Engine: `opportunity_state` is append-only, each row a *complete* statement rather than a delta, so **the status is the audit log rather than something kept beside it.**

```
icp                   identity — what everything cites, forever
icp_version           published content, immutable, sequential
icp_version_product   the product relationship, versioned with the content
icp_state             append-only transitions, each naming its actor
```

**`state` is therefore derived from the latest transition, never stored** — the same rule that makes `evidence_state` derived and release derived from evaluations. **And *created by · published by · archived by* all fall out with no extra fields:** authorship of a version is `icp_version.created_by`, and every state change names its actor by construction.

### Downstream citations name both

*"Publishing Version 2 while Version 1 still drives active opportunities"* is the scenario that decides what a consumer stores.

> **A citation is `(icp_id, icp_version_id)`.** Identity alone loses *which definition* produced the opportunity; version alone loses *which segment it belongs to*. Both, always — the same shape as an evidence citation.

**Rollback is a new version, never a re-pointer.** *"Go back to version 1"* publishes version *n+1* whose content equals version 1's and which records what it was restored from. **Re-pointing at version 1 would erase the fact that on 3 March somebody chose to go back**, and that is a decision a customer is entitled to see.

### The remaining scenarios

| Scenario | Answer |
|---|---|
| **Compare v4 with v2** | A read over immutable rows. No model change |
| **Restore v5** | Rollback — a new version. Same as above |
| **Two users editing one draft** | **Optimistic concurrency on the draft**, the `expected_version` pattern `DeclareIcp` already uses. Per-user drafts are speculative and deferred |
| **Approval workflows** | `pending_review` is one more transition in `icp_state`, and its approver is the actor on the row. **Absorbed; not built** |

### Lifecycle — where each concept lands

**Day One:** draft · published · archived · duplicate · version history · customer-authored.

| Concept | Where it goes | Structural change? |
|---|---|---|
| **Deprecated · locked · pending review · needs attention** | Transitions in `icp_state` | **None** |
| **Imported · template · AI-generated · AI-suggested · customer-modified** | **Provenance on a version or a draft.** Not lifecycles — *how the content arrived* | **None** |
| **Duplicated** | A new ICP whose first version records its source | **None** |
| **Merged · split** | New ICPs whose first version names its predecessors. **The `supersedes` chain already expresses it** | **None** |
| **Copied / shared across workspaces** | **Needs tenancy work this repository has not done.** A template belonging to no workspace is a different tenancy shape | **Out of scope, not deferred** |

### Future relationships — where the pressure actually is

**Asked: does E absorb capabilities, packages, plans, entitlements, markets, regions, business units, industries, competitors, partners, buying motions, sales plays and campaigns?**

**The answer is that most of them point the wrong way.** Sorting them reveals three groups and only one touches this aggregate:

| Group | Examples | Effect on the aggregate |
|---|---|---|
| **Things we sell** | capabilities · packages · plans · entitlements | **Another join off `icp_version`.** The aggregate does not change — this is the axis E was widened along, and widening it again costs a table |
| **Things that describe the buyer** | industries · markets · regions · business units | **Already criteria**, and free text today. **The pressure point:** `markets`/`regions` overlap `countries`, and adding them as *relationships* while `countries` stays a criterion would be two representations of one fact. **Resolve by widening criteria, never by adding a join** |
| **Things that consume an ICP** | competitors · partners · buying motions · sales plays · campaigns | **They cite the ICP; the ICP does not know them.** They need identity — which E provides — and nothing else. A campaign naming an ICP is the campaign's foreign key |

> **The one real pressure point is the second group**, and it is a criteria-modelling question rather than an aggregate question. **Noticed now so nobody adds `icp_version_region` beside a `countries` list.**

### Ownership — deliberately not modelled

**Authors and approvers are answered by the shape above; owners are not, and should not be.**

*Created by* is `icp_version.created_by`. *Published by* and *archived by* are actors on `icp_state` rows. **All three exist without a field being added.**

**An `owner_id` is different, and Day One does not have one.** Ownership only means something if it *grants* something, and authorization in this repository is Casbin over workspace roles — **a field that grants nothing is decoration, and a permission model that lives on a row rather than in the policy is a second authorization system.** If per-ICP permissions are ever wanted, that is a Casbin question first.

### The downstream map — simplify · complicate · neutral

**One verdict per module, so accidental coupling is visible before it is built.** Read against Option B, since that is the alternative.

| Module | Role | Verdict | Why |
|---|---|---|---|
| **Target Accounts** | **Reference** | **Neutral** | A named list of companies. Eventually cites an ICP id; identity is what it needs, and both options give it |
| **Provider Platform** | **Consumer** | **Neutral** | **The largest future consumer** — discovery cites one ICP id. [ADR-0036](0036-target-account-contract.md)'s four ownership boundaries are untouched |
| **Provider Normalization** | **—** | **Neutral** | Never sees an ICP |
| **Knowledge Graph** | **Reference** | **Neutral** | Matching needs an anticorruption layer between the customer's words and canonical values — **[C-002](../../LANE_COORDINATION.md), open.** Neither option pre-solves it |
| **Observation · Business Event Engine** | **—** | **Neutral** | Upstream of any ICP use |
| **Signal Engine** | **Consumer** | **Simplifies** | Per-segment relevance — *"funding rounds matter for enterprise, hiring for mid-market"* — is **one profile per segment**. Under B it is one per segment **per product**, and the three copies of a bundled segment need three |
| **Buying Score** | **Consumer** | **Simplifies** | A scoring model per segment, never per segment-and-product |
| **Opportunity Engine** | **Reference** | **Neutral** | Records human commitment; cites identity if anything |
| **Timeline** | **Observer** | **Neutral** | Projects events; an ICP change would be one more rule |
| **Notifications** | **Observer** | **Simplifies** | *"Your EMEA segment matched nothing in 30 days"* fires **once**. Under B, three times for one segment — and [ADR-0040](0040-notifications.md) forbids semantic deduplication, so nothing would collapse them |
| **AI prompts / Recommendations** | **Consumer** | **Simplifies materially** | An ICP becomes prompt context. **A three-product segment is one coherent paragraph; three near-identical ICPs are three, and a model cannot tell they are one segment.** Under B the prompt either repeats itself or the assembler has to *infer* that three ICPs are the same — inference the platform already knows deterministically, which §10 of `CLAUDE.md` forbids |
| **Analytics / effectiveness** | **Observer** | **Simplifies materially** | *"Which segment converts?"* is per-ICP under both. *"Which product converts?"* is **one join under E**, and under B is only answerable by grouping ICPs that happen to look alike — a heuristic over customer text |
| **Billing / entitlements** | **Observer** | **Simplifies** | *"How many ICPs?"* as a limit is fair under E. **Under B a bundled customer burns three for one segment** — charging for a modelling artefact |
| **Feature flags** | **—** | **Neutral** | No relationship |
| **Revenue Intelligence Platform** | **Consumer** | **Neutral, with one caution** | It composes; it must **read** ICPs through a port and never derive effectiveness inside Commercial Profile. **The boundary test enforces the second half** |

**Commercial Profile is the sole `Owner`; nothing else may write an ICP.** `Consumer` reads to act, `Reference` cites without acting, `Observer` measures or reports. **The map's real use is that no module appears twice** — the moment one is both `Owner` and something else, ownership has leaked.

**Nothing is complicated by E.** Five simplify, ten are neutral, and the three marked *materially* are the ones where B would have forced a heuristic — and **a heuristic over customer-typed text is the shape of every duplicated-truth defect this repository has fixed.**

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

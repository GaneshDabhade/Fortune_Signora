# 403 — Epic D · Risk — implementation preparation

> **Prepared by Lane C — Product Office. No code was written and none should be.** **Every claim verified against source on 2026-08-04.**
>
> ⚠️ **Links to [51-implementation-specifications.md](51-implementation-specifications.md) do not resolve on this branch** — it lives on `lane-b-commercial-profile`. Everything relied on is quoted inline.
>
> **No ADR is prepared for Epic D, deliberately.** It needs no new bounded context, no new dependency and no reversal of an existing decision — **it is a fifth declaration in an existing module and rows in two existing catalogs.** *An ADR is required when a boundary moves; manufacturing one here would be process for its own sake.*

> **Observability, testing, operations and deployment: [405-cross-cutting-concerns.md](405-cross-cutting-concerns.md)** — written once for every prepared package rather than five times. **Epic D's deltas are in its §6 row.** In short: **Measure the `contested` rate** — it is the property the whole ledger exists to protect. **And say what the Playground shows**, or repeat [B-319](../BUGS.md).

---

## 1 · The finding: D2 is already built

**Epic D asks for *"risk — the missing half of the score."* The mechanism is not missing. It shipped.**

> **D2 · *"Risk postures in the existing decomposition."* Not a second score — a posture within the existing ledger, so a customer still reads one number and can still take it apart.**

**Every word of that is already true in code:**

| | Exists today | Evidence |
|---|---|---|
| **`Posture`** | `EXPANSIONARY` · **`CONTRACTIONARY`** · `NEUTRAL` | `buying_score_engine/domain/scoring_model.py:49` |
| **Never netted** | *"Never summed into the score. Posture is what makes contradiction visible; folding it into the arithmetic as a sign is exactly the netting this module refuses"* | same file |
| **Unsigned weights** | `TypeWeight.base_weight` is *"unsigned, for every posture. A contraction risk earns attention just as an expansion opportunity does"* | `scoring_model.py:103` |
| **Contradiction surfaced** | **`contested`** is published on `buying_score.updated` | `domain/events.py:38` |
| **The explanation** | **The Contribution Ledger** — *"the authoritative explanation of a score"*, each `Contribution` carrying its own posture | `domain/ledger.py:55` |
| **Two risk signals already scored** | **`contraction_risk`** (contractionary, 25) · **`decision_maker_departed`** (contractionary, 15) | `scoring/scoring_model@1.json` |

> **D2's remaining work is not in the score. It is on the screen** — *"a contraction risk must never be confusable with a low-scoring opportunity, because they mean opposite things to a CRO scanning a list."* **That is [TASK-905](../BACKLOG.md), it is Product Surface's, and it is already `READY` in the backlog.**

> ### Roadmap integrity, 2026-08-04 — **Epic D *is* a governing differentiator that appears in zero milestones**
>
> **[PRODUCT_DIFFERENTIATORS.md](../../PRODUCT_DIFFERENTIATORS.md) names *"Negative Signal / Deprioritization Intelligence"*** — *"the system explicitly tells reps which accounts are **not** worth pursuing right now, with reasoning, rather than only surfacing positive signals."* Its own assessment: **cost *"Low-Medium — a policy/product decision more than a new module"*; value *"Medium-High — cheap to build, high differentiation, currently unclaimed territory."***
>
> **README records it among the unowned capabilities as *"deprioritization intelligence (owner exists, no milestone)"***, and [SESSION_HANDOFF.md](../SESSION_HANDOFF.md) is blunter: **a governing differentiator in zero milestones**, one of four capabilities that entered through a Demo Scenario rather than a Scope entry.
>
> **It is not missing. It is unlabelled, and it is mostly built.** `Posture.CONTRACTIONARY`, `contraction_risk` and `decision_maker_departed` are scored today; **what remains is exactly §1's finding — the screen, which is [TASK-905](../BACKLOG.md), already `READY`.** The differentiator document's own cost estimate — *"a policy/product decision more than a new module"* — **is the same conclusion this package reached from the code.**
>
> **The recommendation is a rename, not a build:** *Epic D phase 1 delivers the Deprioritization Intelligence differentiator.* **Saying so converts a governing differentiator with no milestone into a `READY` task with an owner**, at no engineering cost.

---

## 2 · D1 is four families, and they are in four different conditions

**The specification: *"Champion departure · usage decline · competitor entry · renewal approaching. The catalog is the work."*** **The catalog is indeed the work — for one of them.**

| Family | What it needs | Condition |
|---|---|---|
| **Champion departure** | To know **whose** champion. `decision_maker_departed` fires today but names nobody | **Blocked on [Epic C](400-epic-c-people.md)** — its specification says so, and Epic C §1 confirms the signal already fires without a subject |
| **Competitor entry** | **A declaration of who your competitors are.** The detection mechanism exists | ✅ **Buildable today.** §3 — and it is the whole of Epic D's independent value |
| **Renewal approaching** | Contract dates | **Blocked on [E1](401-epic-e1-crm-read.md).** Only a CRM knows them |
| **Usage decline** | Telemetry of **your product's** usage by an account | ⚠️ **Recommend dropping.** §4 |

**So Epic D contains exactly one independently executable slice, and it is not the one the specification leads with.**

---

## 3 · Competitor entry — the slice, and why it is small

**The detection half exists.** `BusinessEventType.TECHNOLOGY_ADOPTED` and `TECHNOLOGY_RETIRED` are detected today (`business_event_engine/domain/rules/point.py:105,125`), and two signals already consume them — `displacement_opportunity` (*"a retired system suggests a replacement decision"*) and `modernization_underway`.

**What is missing is one fact only the customer knows: which technologies are competitors.**

> **`grep -rln "competitor" backend/modules/` returns nothing.** The concept does not exist anywhere in the repository.

**And there is an obvious, cheap home for it.** `commercial_profile` holds **four declarations** — catalog, ICP, buying committee, commercial focus — each *"a sentence somebody typed about their own business"*, each immutably versioned with `supersedes`, each with the same shape. **A fifth is a well-trodden path**: `focus.py` is 163 lines and `declare_focus.py` is 113.

```
  customer declares competitors  →  TECHNOLOGY_ADOPTED for a declared competitor
                                              │
                                              ▼
                              competitor_entry signal (contractionary)
                                              │
                                              ▼
                        contested = true on an account you thought was safe
```

**The customer outcome is sharp and testable:** *"Acme just adopted a competitor's product"* — **and it is the single most actionable risk a seller can receive**, because it is specific, dated and cited.

**Two design notes for whoever builds it:**

- **The declaration names competitors, never scores them.** `commercial_profile` *"records; it evaluates nobody."* A field like `threat_level` would be the same failure `committee.py` names against itself — *one plausible field away from becoming a scoring model in the module least equipped to review it.*
- **Reuse the technology vocabulary the graph already resolves.** `EntityKind.TECHNOLOGY` exists. **A competitor declaration should reference a resolvable technology, not a free string** — otherwise *"Salesforce"*, *"salesforce.com"* and *"SFDC"* are three competitors.

---

## 4 · Usage decline — recommend removing it from Epic D

**Signora has no product telemetry, and acquiring it would be a different product.**

*"Usage decline"* means an account using **the customer's own product** less. That data lives in the customer's application, not in any provider and not in a CRM. Obtaining it means a product-analytics integration — **Segment, Amplitude, or a customer's own event stream** — which is a new provider class, a new ingestion path and a new lawful-basis question, for one signal family.

> **Recommendation: drop it from Epic D and record it as a strategic candidate.** It is the only one of the four that requires a capability the platform has never had, and **carrying it inside Epic D makes the epic look blocked when three-quarters of it is not.**

**The honest alternative if the outcome is wanted sooner:** a CRM already carries *last activity date*, and *"nobody has touched this account in 90 days"* is a different and weaker signal that **E1 would deliver for free**. Not the same thing; worth knowing it exists.

---

## 5 · Repository reuse — what must NOT be built

| ❌ Do not build | ✅ Exists as | Consequence |
|---|---|---|
| **A risk score, or a second score** | **`Posture` + the Contribution Ledger** | **The exact netting the module refuses.** Two numbers a customer must reconcile |
| **A negative weight or a minus sign** | `base_weight` is **unsigned for every posture** | Contradiction becomes invisible instead of `contested` |
| **A contradiction flag** | **`contested`**, published today | |
| **A risk explanation surface** | The Contribution Ledger — *"the authoritative explanation of a score"* | |
| **A signal detection strategy** | `signal_engine/domain/rules.py` — two strategies, **no thresholds in code** | A threshold in code is *"a claim about the world somebody must be able to argue with"* |
| **A technology detector** | `TECHNOLOGY_ADOPTED` · `TECHNOLOGY_RETIRED` | |
| **A technology identity model** | `EntityKind.TECHNOLOGY` in the graph | Three spellings, three competitors |
| **A declaration lifecycle** | Four existing declarations, versioned with `supersedes`, **no `UPDATE` grant** | |
| **A departure detector** | `decision_maker_departed`, catalogued and scored | |

### Surface rather than build

**Two contractionary signals already score today and the attention list does not distinguish them.** [TASK-905](../BACKLOG.md) is that gap, it is `READY`, and it delivers **most of Epic D's visible customer value with no new signal at all.**

---

## 6 · Phases

| # | Phase | Delivers | Effort | Depends on |
|---|---|---|---|---|
| **1** | **Risk is legible** — [TASK-905](../BACKLOG.md) | A contraction risk stops looking like a weak opportunity | **S** | **Nothing.** Product Surface |
| **2** | **Competitor declaration** | A fifth declaration + its screen | **M** | Nothing |
| **3** | **`competitor_entry` signal** | Catalog row, weight, posture, detection | **S** | Phase 2 |
| **4** | **Renewal approaching** | Contract dates from the CRM | **M** | **[E1](401-epic-e1-crm-read.md)** |
| **5** | **Champion departure, named** | *Your* champion, not *a* leader | **S** | **[Epic C](400-epic-c-people.md)** |
| — | ~~Usage decline~~ | **Removed** — §4 | — | — |

> **Phases 1–3 are independent of every other epic**, and phase 1 needs nothing at all. **Phases 3–5 are each a catalog row and a weight once their input exists** — which is what *"the catalog is the work"* was pointing at, and why Epic D is **M** in total rather than the **L** its first slice suggests.

**Stop-after-any-phase:** phase 1 alone fixes the confusion a CRO actually hits. Phases 2–3 add the sharpest risk signal in the product.

---

## 7 · Risks, and what is not escalated

| Class | Risk | Mitigation |
|---|---|---|
| **Architectural** 🟠 | **A risk score appears beside the buying score** | §5 — posture, never a second number. **The module already refuses it; keep it refusing** |
| **Architectural** 🟠 | The competitor declaration acquires a `threat_level` | **`commercial_profile` records and evaluates nobody.** Same guard `committee.py` uses |
| **Data** 🟠 | Competitors as free strings | **Reference `EntityKind.TECHNOLOGY`** |
| **Product** 🟠 | **Epic D reads as blocked** because two families wait on C and E1 | §2 — **it is not.** Phases 1–3 are independent |
| **Scope** 🟡 | Usage decline drags a provider class into Epic D | §4 — **remove it** |
| **Product** 🟡 | A competitor signal that fires on a technology a customer does not care about | The declaration is the filter, and **the customer owns it** |

**Not escalated — engineering can answer these:** the weight and relevance window for `competitor_entry` *(the catalog is the authoring surface, and a domain expert owns it — a lane should propose, not decide alone)* · whether the declaration is per-product or workspace-wide · the screen's placement among four existing declarations.

## 8 · Definition of done, and open questions

**Done when a seller can tell a contraction risk from a weak opportunity at a glance, and when an account adopting a declared competitor says so with a date and a citation.**

**Gates:** no second score and no negative weight · `contested` reaches the screen · a competitor is a resolved technology, not a string · **the declaration carries no judgement field** · `competitor_entry` has a catalog entry with hypothesis and rationale, like all nine existing signals · **no threshold in code.**

### Open questions

> **🟢 Background — is *usage decline* dropped from Epic D?** Lane C recommends yes (§4), recorded as a strategic candidate. **Nothing waits on the answer.**

> **🟢 Background — should the competitor declaration be a fifth `commercial_profile` declaration, or its own thing?** Lane C recommends the fifth: identical shape, identical lifecycle, and the module's own versioning already solves it. **Engineering could reverse this cheaply if it proves wrong.**

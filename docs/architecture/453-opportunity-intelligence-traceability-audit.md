# 453 · Opportunity Intelligence — screen-by-screen traceability audit

**Lane C · Product Office · 2026-08-05.** **Tenth audit under [D-078](../DECISION_REGISTER.md)**, extended through [D-089](../DECISION_REGISTER.md). **The threshold screen — the [Domain Coverage Matrix](../DOMAIN_DISCOVERY_REGISTER.md) follows.**

**Screen 7 of 16** — *"the revenue cockpit — probability, contributions, competitors"* ([410](410-approved-ui-specification.md)). **Wave 4, sharing its aggregates with Executive Dashboard.**

---

# 0 · [C-418](../LANE_COORDINATION.md) is confirmed independently, and the third statement is published to customers

**[444](444-executive-dashboard-domain-assessment.md) found the Executive Dashboard's first word — *forecast* — contradicted by `buying_score_engine`, twice, in its own code.** **This screen's first named capability is *probability*, and the refusal turns up a third time — in a place the first two were not.**

> **`opportunity_engine/interface/schemas.py`, the response schema a customer reads in the OpenAPI documentation:**
>
> ***"Commercial attention, 0–100. **An ordering, not a probability and not a prediction.** Null when the evidence behind it has expired."***

| | |
|---|---|
| **Statement 1** | `buying_score_engine/domain/events.py` — *"No probability, no likelihood, no prediction"* |
| **Statement 2** | `domain/score.py` — *"They do not estimate probability"* |
| ⚡ **Statement 3** | **The published API contract.** **Not an internal principle — a promise to consumers** |

> ## **So two unrelated screens, audited nine days apart in the plan and hours apart in fact, each named a capability the platform refuses in writing — and the third refusal is in the contract.**
>
> **[C-418](../LANE_COORDINATION.md) does not need re-raising; it needs this evidence attached.** ⚠️ **And it changes what a *yes* would cost: answering *"Signora forecasts"* now means **changing a published API description**, not only adding a field.**

---

# 1 · The traceability matrix

✅ exists · 🟡 extend · 🟠 conflicts · 🔴 missing · ⬜ not extractable

| UI element | Business meaning | Source of truth | Audit | Owner | Consumers | Priority |
|---|---|---|---|---|---|---|
| **Contributions** — *why this number* | The arithmetic that produced a score | **Aggregate** — `ContributionLedger` · `Contribution` | ✅ **Built, and it is the strongest thing on this screen**: *"every entry that produced a score, **and the arithmetic that did it**"*, refusing to exist when it *"cannot be trusted to explain its score"* | `buying_score_engine` | 4 screens | — |
| **Score, and its expiry** | Commercial attention now | **Aggregate** — `BuyingScore` | ✅ **Built.** ⚡ **And it is [P-A](../DOMAIN_DISCOVERY_REGISTER.md) in the API**: *"Null when the evidence behind it has expired — the opportunity is still open and the number that justified it is no longer current"* — **an eighth instance, in a contract** | `buying_score_engine` | 4 screens | — |
| **Stage and its history** | Where a pursuit stands, and how it got there | **Aggregate** — `opportunity_state`, append-only | ✅ **Built** — sequence, actor, reason, timestamp | `opportunity_engine` | Opp Intelligence · Exec Dashboard | — |
| **Competitors** | Who this workspace is up against | **Aggregate** — `DeclaredCompetitors` | ✅ **Shipped whole** — [ADR-0403](adr/0403-signal-engine-reads-a-declaration.md), reader, view, endpoint, and `competitor_entry` as a signal | `commercial_profile` | Opp Intelligence · Account 360 | — |
| **Probability** | *How likely is this to close* | **AI capability, or a model** | 🟠 **Refused in writing, three times, and once in the published contract** — §0 | ⚠️ **[C-418](../LANE_COORDINATION.md)** | Opp Intelligence · Exec Dashboard | **Ruling due** |
| **Quarter aggregates** | Roll-ups over a period | **Computed view** | 🔴 **Missing, and shared with Executive Dashboard** — which is why [412](412-backend-capability-matrix.md) puts both in wave 4: *"building either separately produces the second copy the reuse rules exist to prevent"* | `opportunity_engine` | **Both wave-4 screens** | **Wave 4** |
| **Competitor *mentions*** | Where a rival came up in a conversation | **External provider** | ⛔ **Needs conversation intelligence.** ⚠️ **Distinct from *declared* competitors, which ship** | — | Opp Intelligence | **Evidence-gated** |
| **Talk ratio · commitments** | What was said on a call | **External provider** | ⛔ **[MC-10](../PRODUCT_EXPERIENCE.md)** — activity capture, no source | — | Opp Intelligence · Global Search | **Evidence-gated** |
| **Next actions** | What to do about this pursuit | **Aggregate** — `Recommendation` · `NextAction` | 🟡 **Built and unreachable until [TASK-205](../BACKLOG.md) lands.** ⚡ **And *"nothing sends without your approval, reversible for 24 hours"* is [R-03](../DOMAIN_DISCOVERY_REGISTER.md)** | `sales_engagement` | 7 screens | **[TASK-431](../BACKLOG.md)** |

**Nine elements: 4 ✅ · 1 🟡 · 1 🟠 · 3 🔴/⛔.**

---

# 2 · Workflow, and the finding is an absence of one

**This screen has no completion point of its own.** **A seller reads it and then acts *somewhere else*** — takes the account on Account 360, sends an approach from Copilot, resolves a signal in Signal Center.

| | |
|---|---|
| **Business events** | ⛔ **None, and correctly.** ✅ **[R-14](../DOMAIN_DISCOVERY_REGISTER.md) does not fire — reading is not deciding** |
| **State transitions** | ⛔ **None here.** The stage machine is `opportunity_engine`'s and is exercised from Account 360 |
| **Permissions** | ✅ **Complete** — `Resource.OPPORTUNITY`, `read` and `update`, and the Security Invariant pinning the boundary |
| **Background jobs** | ⛔ **None** — quarter aggregates are reads, not materialisations |
| **Audit** | ✅ **`opportunity_state` is the audit** — append-only, attributed, reasoned |

> **A screen with no workflow of its own is worth recording rather than skipping.** **It means every capability here is *shared* by construction**, and it is why this screen contributes almost nothing new to the register while confirming four existing entries.

---

# 3 · ⚖️ Separating the platform capability from the presentation ([D-089](../DECISION_REGISTER.md))

> ***"Is this actually a shell feature, or is the shell merely the consumer of a reusable platform capability?"*** — **applied here to a screen rather than the shell, because the same question decides two of its elements.**

| Element | Owned here, or consumed? |
|---|---|
| **The contribution bars** | **Consumed.** `ContributionLedger` is `buying_score_engine`'s and **four screens render it.** ⛔ **Opportunity Intelligence must not compute a second explanation** |
| **Quarter aggregates** | ⚠️ **Genuinely undecided, and shared with one other screen.** **Whoever builds it first owns it, which is exactly the condition [412](412-backend-capability-matrix.md) put both screens in one wave to avoid** |

**Recommendation: the aggregates belong to `opportunity_engine` and both screens consume them** — **`opportunity_engine` already owns the stage history the aggregates are computed from**, and §2's *least powerful author* puts a derivation next to the facts it derives from.

---

# 4 · Findings

| | |
|---|---|
| **Existing and correctly modelled** | `ContributionLedger` and its refusal to exist untrustworthy · `BuyingScore` with expiry · `opportunity_state` · `DeclaredCompetitors` end to end · the authorization boundary |
| **Extension candidates** | **Quarter aggregates in `opportunity_engine`**, consumed by both wave-4 screens |
| **Architectural evolution** | 🟠 **Probability — [C-418](../LANE_COORDINATION.md), now with a third refusal published in the API contract** |
| **Missing foundational capabilities** | ⛔ **None new.** **[R-03](../DOMAIN_DISCOVERY_REGISTER.md) confirmed for the seventh time** |
| **Missing workflows** | ⛔ **None — the screen has none** |
| **Missing entities** | ⛔ **None** |
| **Missing business events** | ⛔ **None.** ✅ **Correctly** |
| **Missing permissions** | ⛔ **None** |
| **Missing projections** | **Quarter aggregates** |
| **Missing platform capabilities** | ⛔ **None** |

---

# 5 · Vocabulary check ([D-087](../DECISION_REGISTER.md) §3, run inside the audit)

| Concept | Verdict |
|---|---|
| **Competitor** | ✅ **Owned by `commercial_profile`, one meaning.** ⚠️ **But *declared competitor* and *competitor mention* are two concepts** — one is a customer declaration, the other an observation from a call. **Candidate qualification, on the `Owner` pattern** |
| **Probability** | ✅ **Already `rejected` in the register** as `CONFIDENCE_REJECTED`'s neighbour — **and this audit adds the API-contract evidence** |
| **Contribution** | ✅ **Canonical, `buying_score_engine`** — no collision |

---

# 6 · What this produces

**No new backlog row.** **What it changes:** ⚡ **[C-418](../LANE_COORDINATION.md) gains a third refusal, published in the API contract — so a *yes* means changing a promise to consumers** · **quarter aggregates are recommended to `opportunity_engine`** · **[P-A](../DOMAIN_DISCOVERY_REGISTER.md) gains an eighth instance, in a schema description** · **`Competitor` is a qualification candidate.**

---

# 7 · What this document did not do

**Nothing implemented · no lane named · no wave reordered · no module created · no ADR drafted · no queue file touched · no backlog row added.** **And it did not re-raise [C-418](../LANE_COORDINATION.md)** — **an item raised once and confirmed independently gets its evidence attached, not a duplicate.**

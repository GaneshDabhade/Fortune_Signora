# 444 · Executive Dashboard — the screen assessed to its domain

**Lane C · Product Office · 2026-08-05.** **[Product-Led Domain Discovery](442-product-led-domain-discovery.md), applied to one screen at full depth**, on the product owner's direction to work through the approved UI screen by screen.

**Measured against `origin/integration` @ `6b7b04e`. Nothing implemented, no lane named.**

---

# 0 · The headline, and it is not a missing field

**[410](410-approved-ui-specification.md) describes the screen in five words: *"CEO/CRO homepage — **forecast**, risk, ageing, movements."***

> ## ⛔ **The repository has a ratified principle that refuses to forecast, and it sits in the module the forecast would come from.**
>
> **`buying_score_engine/domain/events.py`:** ***"No probability, no likelihood, no prediction. A buying score prioritizes commercial attention; it does not forecast a purchase."***
> **`domain/score.py` says it again:** *"They do not estimate probability."*

**This is not a gap. It is a boundary, stated twice, in the place a forecast would naturally be built.** **[412](412-backend-capability-matrix.md) records the same thing from the other side** — *"a probability model distinct from the rep's stage"* — and calls it missing rather than refused.

> **So the Executive Dashboard's first word contradicts a ratified principle, and nothing in the repository says which wins.** **That is the finding, and it is worth more than the four missing entities below**, because it is the one that would be discovered halfway through building the screen.

---

# 1 · ✅ Ready now — and more than [417](417-executable-slice-audit.md) could say when it was written

**[417](417-executable-slice-audit.md) called this screen *"READY NOW, partially — coverage, conversion, ageing and movement are arithmetic over stages and dates."* That was right, and one of its four is newly unblocked.**

**The reason all four are computable is one table**, and it is better than the assessment assumed:

```
opportunity_state — sequence · stage · owner_id · actor_id · reason · occurred_at
```

**An append-only stage history with an actor, an owner, a reason and a timestamp on every row**, protected by three check constraints including *`actor_id IS NOT NULL OR stage = 'tracking'`* — ***"Intelligence suggests; humans commit. The machine may author exactly one stage, and the database makes that structural."***

| Section | Computable from | |
|---|---|---|
| **Stage conversion** | `sequence` over `opportunity_state` | ✅ **Nothing new** |
| **Ageing** | `occurred_at` deltas between consecutive rows | ✅ **Nothing new** |
| **Movement since a date** | `occurred_at > :since`, and `reason` explains each one | ✅ **Nothing new** |
| **Team roll-up** | **`owner_id` is already on every state row** | ✅ **Nothing new** |
| **ICP coverage — in vs outside** | **[TASK-434](../BACKLOG.md)** | ⛔ **CORRECTED 2026-08-06 · [B-327](../BUGS.md).** ~~✅ `PROMOTED` today~~ — **the predicate is promoted and nothing can call it.** Blocked on [C-332](../LANE_COORDINATION.md) |

> ⚠️ **Corrected 2026-08-06.** **Four of the screen's sections need no new domain concept; the fifth needs a producer of observed attributes that does not exist** — [C-332](../LANE_COORDINATION.md). **`GET /accounts` and `GET /accounts/decided` are published and workspace-scoped**, and that was never the missing part.
>
> **What this document got wrong is worth naming rather than overwriting:** it read *`TASK-434` is `PROMOTED`* as *the section is buildable*, which is [B-327](../BUGS.md)'s whole shape — **a promoted predicate is a foundation, and a section needs a caller that can reach one.**

---

# 2 · ⛔ What is genuinely absent — four concepts, and they are one question

**Measured across every module's `domain/`:**

| | Concept | Evidence |
|---|---|---|
| **①** | **A deal has no value** | **`Opportunity` carries `id · workspace_id · entity_id · generation · originating_buying_score_id · score_at_creation · contested_at_creation · qualification · policy_version · created_at · created_by`.** ⛔ **No amount, no currency, no expected close date.** *(`amount` matches in `business_event_engine` — that is a funding round being formatted, not a deal.)* |
| **②** | **There is no plan** | ⛔ **`quota`, `target_amount`, `forecast` return nothing in any domain layer.** ***"Projection against a plan"* needs a plan, and no aggregate holds one** |
| **③** | **There is no period** | ⛔ **`fiscal` returns zero.** **A quarter is a workspace declaration** — when the year starts, what a period is — **and nothing declares it.** Every aggregate on this screen is *per quarter* |
| **④** | **There is no team** | ⛔ **No `Team`, no `manager_id`, no `reports_to`, no hierarchy anywhere in `workspace_tenancy`.** **[MC-6](../PRODUCT_EXPERIENCE.md) said it first**: *"the buyer is a CRO and **there is no screen addressed to one**"* |

> ## These are not four decisions. They are one.
>
> **Ask *"does Signora forecast revenue?"* and all four follow or none do.**
>
> **Yes** → a deal needs a value and a close date, a workspace needs a fiscal calendar, somebody needs a plan, and the probability question must be settled against a ratified principle.
> **No** → **the screen is coverage, conversion, ageing and movement — all five of which are buildable today** — and it is a *pipeline health* dashboard rather than a forecast, which is a naming decision and not an engineering one.

**Raised as [C-418](../LANE_COORDINATION.md), one item rather than four.**

---

# 3 · Where the value would come from, and it is not a text box

**If ① is approved, the source matters more than the field.**

| | |
|---|---|
| ⛔ **Not by asking a seller** | **[ADR-0036](adr/0036-target-account-contract.md)'s standard**: *"asking them for a domain, a country or a registration number would be asking a customer to do resolution, and resolution quality is Signora's competence, not theirs."* **A deal value typed into Signora is a second copy of a number that already exists in a CRM, and the two will disagree** |
| ✅ **From the customer's own system** | **Epic E1 — [TASK-402](../BACKLOG.md), `IN VALIDATION`.** **The inbound source port is ruled ([C-326](../LANE_COORDINATION.md)) and [409](409-inbound-source-port-contract.md) is the contract.** A deal amount is exactly what a CRM holds and Signora does not |
| ⚠️ **And it changes the sequencing** | **A forecast built before E1 lands is a forecast over numbers nobody entered.** **This is the strongest argument for answering C-418 *before* wave 4, not during it** |

---

# 4 · Permissions — the gap nobody has hit yet

**Every current grant is workspace-wide: `p, member, *, opportunity, read`.**

> **The Executive Dashboard shows one seller's numbers to another seller.** **A roll-up by owner is, by construction, everybody's performance on one page** — and the policy file currently permits every member to read it.

**No `Resource` exists for a plan, a target or a forecast.** ⚠️ **And this is the first screen in the approved set whose *data* is sensitive between colleagues rather than between tenants** — every prior authorization question has been *may this role act*, never *may this person see that person's numbers*.

**Recorded, not proposed.** **It becomes real only if C-418 is answered *yes*** — coverage and ageing are facts about accounts, not about people.

---

# 5 · Reuse — what must not be rebuilt

| ✅ **Reuse unchanged** | `opportunity_state` and its three constraints · `GET /accounts` · `GET /accounts/decided` · `buying_score_engine`'s catalog, weights and postures · **[TASK-434](../BACKLOG.md)'s matching predicate** · the `since`-as-a-parameter pattern from [C-215](../LANE_COORDINATION.md) |
|---|---|
| ⛔ **Never duplicated** | **A second aggregation.** [412 §5](412-backend-capability-matrix.md) puts this screen in wave 4 *"because it needs aggregates that would otherwise be built twice"* — **Opportunity Intelligence needs the same ones**, and the two are one wave for that reason |
| ⛔ **Never a second scorer** | **A probability model beside `buying_score_engine` is two systems ranking commercial attention.** If C-418 is answered *yes*, **the probability belongs where the scoring catalog already is, or it belongs nowhere** |
| 🟨 **Extended minimally, and only on a *yes*** | `Opportunity` gains value and close date **from E1** · a `FiscalCalendar` is a **declaration**, so `commercial_profile`'s shape · a `Plan` is a new aggregate and needs its own home |

---

# 6 · What this produces

| | |
|---|---|
| **[TASK-438](../BACKLOG.md)** | ⚠️ **CORRECTED 2026-08-06 · [B-327](../BUGS.md).** ~~The five sections that need nothing… it needs no answer from anybody~~ → ✅ **Four sections that need nothing** — conversion, ageing, movement, roll-up by owner. ⛔ **ICP coverage needs [C-332](../LANE_COORDINATION.md)**, and **Lane B delivered four rather than five** on exactly this |
| **[C-418](../LANE_COORDINATION.md)** | **One question — *does Signora forecast revenue?*** — carrying all four missing concepts, the ratified conflict, the E1 sequencing and the permission consequence |

**Two artifacts from sixteen screen sections.** **Deliberately** — *"success is not measured by the number of backlog items created."*

---

# 7 · What this document did not do

**Nothing implemented · no lane named · no wave reordered · no module created · no ADR drafted · no queue file touched.**

**It did not decide whether Signora forecasts.** **That is a product decision with a ratified principle on one side of it**, and Lane C prepares those rather than taking them.

**And it did not move the screen out of wave 4.** **Five of its sections are buildable now and the wave plan is still right**: the sections that are not buildable need aggregates Opportunity Intelligence needs too, and building either screen alone produces the second copy the reuse rules exist to prevent.

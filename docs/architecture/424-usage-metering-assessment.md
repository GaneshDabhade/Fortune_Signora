# 424 — Usage Intelligence & Metering: repository assessment

> **Lane C — Product Office, 2026-08-04.** **A backlog planning and architecture exercise.** No implementation package, no new module, no code. Measured against `origin/integration`.
>
> **The brief asked to be challenged where repository evidence disagrees. It does, in three places.**

> ✅ **Ruled 2026-08-04, product owner.** **[D-029](../DECISION_REGISTER.md) stands — no Usage Accounting bounded context at this stage.** The architectural direction, the OpenMeter refusal and *meter first, bill later* are accepted; **the scope is expanded to every billable operational fact, and a second initiative is sequenced after this one.** §7–§9 record what changed.

## 1 · The three findings, before the detail

> **1 · Signora already meters.** Per workspace, immutably, with forced RLS. **`ai_inference` records `input_tokens`, `output_tokens`, `latency_ms`, `retries`, `outcome`, `served_model` and `vendor`, indexed on `(workspace_id, outcome, created_at)`** — which is a time-window usage aggregation index and nothing else.

> **2 · *Meter first, bill later* is not a new philosophy. It is ratified constitution**, and it is stronger than the brief states. `CLAUDE.md` §10: *"**Operational facts and commercial policy stay separate.** Records describe what happened — tokens, latency, retries, timings — **and never what it cost.** A price is a contract term that changes without the code changing, so a currency figure written onto an operational row is correct briefly and wrong permanently. **Pricing is applied at reporting time over stored facts, which also lets a rate change re-price history correctly.**"

> **3 · A `usage_event` table would be the defect §2 forbids.** *"Truth has exactly one authoritative representation… when implementation reveals two independent representations of one fact, **remove one rather than synchronising both**."* **A usage row duplicating `ai_inference` is two representations of one call.**

**So the gap is real but it is not where the brief places it. Signora is not missing meters. It is missing *aggregation, projection and entitlement* — all of which are read concerns over data that already exists.**

## 2 · What already exists — the reuse audit

| Brief's requirement | Repository today | |
|---|---|---|
| **AI actions consumed** | **`ai_inference`** — tokens in/out, latency, retries, outcome, model, vendor, `correlation_id`. Workspace-scoped, **forced RLS**, immutable *(no `UPDATE` policy, by design)*, indexed for time-window queries | 🟩 **Built** |
| **Provider / enrichment usage** | **`provider_sync`** — `records_received`, `pages_fetched`, status, `started_at`/`finished_at`, failure kind. Workspace-scoped | 🟩 **Built** |
| **Storage usage** | Derivable by row count — `raw_provider_record` · `claim` · `observation` · `ai_narration` · `research_synthesis`, all workspace-scoped | 🟠 **Derivable, not exposed** |
| **Seats** | **`membership`** + **`membership_role_change`** — *"seats are counted on unique active users per month"* is a query over these | 🟠 **Derivable, not exposed** |
| **Research runs** | `research_request` · `research_task` · `research_request_state` | 🟩 **Built** |
| **Entitlement gate** | **`LIVE_CAPABILITIES`** — *"a Connection Center that promised meeting intelligence Signora cannot yet produce would be the product asserting something untrue"* | 🟠 **A pattern, not per-workspace** |
| **Event substrate** | **`outbox_event`** — transactional outbox, relay, dispatch, idempotency, dead-lettering, ARQ pools. **Every event carries `workspace_id`, `correlation_id`, `causation_id`** | 🟩 **Built** |
| **Cost attribution** | `vendor` · `served_model` · `input_tokens` · `output_tokens` per inference — **everything a rate card needs** | 🟩 **The facts exist; the rate card does not, deliberately** |
| **Workflow runs** | — | 🔴 **`workflow` does not exist** ([ADR-0402](adr/0402-a-rule-is-data.md) approved, unbuilt) |
| **API calls** | — | 🔴 **No request log** |
| **Search usage** | — | 🔴 **No search service** |
| **Notifications** | — | 🔴 **`notifications` does not exist** ([D-027](../DECISION_REGISTER.md) deferred) |
| **Aggregation · projection · overage · invoice** | — | 🔴 **None** |

**Nine of thirteen categories already have their meter. Four have no meter because the thing being metered does not exist yet.**

> **The four missing meters are missing modules, not missing metering.** A workflow-run meter cannot precede `workflow`. **Building a metering platform for capabilities that do not exist is speculative abstraction** (`CLAUDE.md` §6), and it is the failure mode this assessment exists to prevent.

## 3 · Challenging the proposed direction

### 3a · The pipeline — `Modules → Usage Publisher → Usage Gateway → OpenMeter → Lago → Stripe`

**Two of the five stages conflict with ratified architecture, and one is already built.**

| Stage | Verdict |
|---|---|
| **Every module publishes a Usage Event** | ⚠️ **Half right, and the half that is wrong matters.** The event substrate exists and every event already carries `workspace_id` and `correlation_id`. **But a `usage.recorded` event alongside `ai_inference` is the same fact twice** (§2). **A module should not publish usage; usage should be *read from* what the module already records** |
| **Usage Gateway** | ⚠️ **A new bounded context (🔴) for a routing concern.** No aggregate, no ubiquitous language a customer speaks — the same tests [420](420-environment-management-proposal.md) §4 applied to EMP |
| **OpenMeter** | ⛔ **Refused on Principle 6.** OpenMeter requires **Kafka and ClickHouse**. *"There is exactly one PostgreSQL database… never introduce a second datastore"* — **this is two.** It is also a streaming aggregator for volumes Signora does not have |
| **Lago** | 🟠 **Viable, and premature.** Self-hostable, its own PostgreSQL — a vendor's own store, like Redis, so Principle 6 is arguable rather than violated. **But it is a deployed service, and deployment is M14.5** (§20c-2) |
| **Stripe** | 🟢 **Lowest architectural cost.** An API, not a datastore. **Stripe Meter Events would consume the aggregation Signora must build either way** |

> **The pipeline's *principle* is right and worth keeping: no business module knows about invoices, subscriptions, pricing, plans, taxes or finance.** **That principle is already enforced** — §10 forbids a currency figure on an operational row, and no module imports anything commercial. **The pipeline restates a constraint the repository already holds rather than adding one.**

### 3b · The name

**The brief prefers *Usage Intelligence* over *Billing* because billing is one consumer. Agreed, and the repository agrees more strongly than the brief does** — but *Intelligence* is a loaded word here.

> **Signora's `*_engine` modules produce *inference*: hypotheses grounded in evidence.** A meter counts. **Calling counting *intelligence* would put a deterministic aggregation in the same vocabulary as the pipeline that must be defensible**, and `CLAUDE.md` §2's least-powerful-author rule exists precisely to keep those apart.

**Recommended: *Usage Accounting*.** It says what it does — **facts, aggregated, attributable, immutable at period close** — and it does not borrow a word the pipeline owns.

### 3c · Which responsibilities belong together

| Belongs | Because |
|---|---|
| **Meter definitions · aggregation · time-window queries · current-cycle usage · historical usage · projections · usage APIs · period close** | One aggregate: *a workspace's consumption over a window*. **Its invariants — a closed period never changes — nothing else can enforce** |
| **Entitlement evaluation · quota enforcement** | 🟠 **Adjacent, and a genuine boundary question.** An entitlement is *what the plan permits*; usage is *what happened*. **They share a workspace and nothing else** |

| Does **not** belong | Where it goes |
|---|---|
| **Invoices · taxes · currencies · discounts · credits · payment** | **Buy it.** §9 — *build the advantage, buy the commodity.* **Billing is a commodity and Signora's advantage is not in it** |
| **AI cost tracking · provider cost tracking · profitability · FinOps** | **A rate card applied at reporting time over `ai_inference` and `provider_sync`.** §10 already forbids storing the cost. **This is a report, not a store** |
| **Usage anomaly detection** | ⚠️ **`signal_engine`'s shape, not a meter's.** A meter that decides something is anomalous has started inferring |
| **Audit trail** | **Already exists** — every operational table is immutable by design, and §16 requires `workspace_id`/`correlation_id` on every log line |
| **Capacity planning** | **Operations, and evidence-triggered** — §14 and [12-scalability.md](12-scalability.md). No trigger has fired |

## 4 · The architectural recommendation

> **Not A (new Platform Foundation capability). Not C (an existing module owns it). **B — an extension**, and the smallest one available.**

**The meters exist in five modules. Aggregation must not read their tables** (§5), so it reads their `public/`. **That makes it a composition, exactly like Account 360's batch** ([414](414-wave-1-account-360.md) §2).

### The one thing that genuinely needs storage, and only one

**Derivation is correct for live usage and wrong for an invoice.** If a period's total is recomputed from module tables, **a later data change silently re-prices a closed invoice.**

> **So: derive continuously, materialize at period close.** A closed period is a **materialized historical fact** — the fifth data category `CLAUDE.md` §2 already defines: *"a persisted record of what the platform actually produced at that moment… therefore immutable."*
>
> **That is not duplication.** Live usage has exactly one representation (the module tables); a closed period has exactly one representation (the closed record). **They answer different questions, and the second cannot be recomputed by design.**

**This is the same pattern as `ai_narration` and `ai_reasoning`, and it needs no new principle.**

### What the extension actually is

| | |
|---|---|
| **Owner** | ⚠️ **Genuinely open.** `workspace_tenancy` owns seats, plan and membership and is the closest fit. **Naming it now would force the boundary [D-029](../DECISION_REGISTER.md) explicitly deferred** |
| **Public contract** | A read port per metered module — **`UsageReader.consumed(workspace_id, window) -> MeterReading`** — published through each module's own `public/`, because **a port belongs to the module that owns the language it represents** (§6) |
| **New tables** | **One:** the closed billing period. **Nothing else** |
| **New events** | **One:** `usage.period_closed`. **Not a per-action usage event** |
| **ADR required** | **Yes, when the boundary is decided** — a new bounded context is 🔴. **Not yet** |

## 5 · Build vs buy

| | Fit | Verdict |
|---|---|---|
| **OpenMeter** | Kafka + ClickHouse | ⛔ **Two new datastores. Principle 6.** And it solves a throughput problem Signora does not have |
| **Kill Bill** | JVM, plugin architecture, its own store | ⛔ **Operational complexity far above the problem** |
| **Lago** | Self-hosted, own PostgreSQL, good API, AGPL/commercial | 🟠 **The best of the self-hosted options, and premature.** Revisit at M14.5 |
| **Stripe Meter Events + Billing** | API only, no datastore, no self-hosting | 🟢 **Recommended when billing is real.** It consumes the aggregation Signora must build regardless, so **nothing is wasted if it is later replaced** |
| **Build invoicing** | — | ⛔ **§9. Taxes, currencies, dunning and revenue recognition are a commodity, and getting them wrong is expensive in a way that is not architectural** |

> **The build/buy line: build the aggregation, buy the invoicing.** Aggregation is unavoidable — **every option above needs Signora to say how many AI actions a workspace consumed**, and only Signora can. **Everything downstream of that number is a commodity.**

## 6 · Priority, and why it is not P0

> **P2, incremental, and after the Billing UI is scheduled — not before it.**

**Three reasons, and the first is a ruling.**

**[D-029](../DECISION_REGISTER.md), 2026-08-04:** *"Continue discovery work. **Do not force a module boundary until implementation naturally reaches M14b.**"* **This initiative asks for a module boundary.** Recording it now as a Platform Foundation initiative would do exactly what that ruling deferred.

**Second: four of the thirteen meters cannot exist yet** — workflow, notifications, API and search all wait on modules that are unbuilt or deferred. **A metering platform built now would meter nine things and stub four.**

**Third: nothing is blocked by its absence.** No approved screen except **Billing** consumes usage, and **Billing is `DEFERRED` by ruling.**

**What *is* worth doing now, and is small:**

| | Slice | Size | Why now |
|---|---|---|---|
| **1** | **A `UsageReader` port on `ai_platform`** — AI actions consumed, per workspace, per window | **Small** | **The table and its index already exist.** It is a query and a `public/` export |
| **2** | **The same on `provider_platform`** — sync runs and records received | **Small** | Same shape |
| **3** | **Seat counting** — unique active users per month, from `membership` | **Small** | The approved Billing screen specifies exactly this |

**Three small read slices, no new module, no new table, no ADR.** They make the numbers *available*, which is the whole gap, and **they commit to no boundary** — so D-029 stays honoured.

## 7 · Expanded scope — every billable operational fact

**Ruled: prepare so Signora can eventually meter anything billable, not only AI.** **The classification is unchanged and the list is longer.**

| Meter | Source today | |
|---|---|---|
| **AI inference · AI tokens** | `ai_inference` — `outcome`, `input_tokens`, `output_tokens` | 🟩 |
| **Research jobs** | `research_request` · `research_task` | 🟩 |
| **CRM synchronizations** | `provider_sync` — once E1's inbound port lands ([D-023](../DECISION_REGISTER.md)) | 🟩 |
| **Companies processed** | `entity` · `raw_provider_record`, workspace-scoped | 🟠 derivable |
| **People processed** | `entity`, **once `EntityKind.PERSON` exists** ([D-021](../DECISION_REGISTER.md)) | 🟠 |
| **Storage** | Row counts across workspace-scoped tables | 🟠 derivable |
| **Seats** | `membership` · `membership_role_change` | 🟠 derivable |
| **Exports** | — **no export path exists** | 🔴 |
| **Workflow executions** | — `workflow` unbuilt ([D-025](../DECISION_REGISTER.md) approved) | 🔴 |
| **Notifications** | — `notifications` deferred ([D-027](../DECISION_REGISTER.md)) | 🔴 |
| **API usage** | — no request log | 🔴 |

> **The rule that keeps this from becoming speculative abstraction:** **a meter is added when the thing it meters exists, never before.** Six meters exist or are derivable today; **five wait on capabilities that are unbuilt or deferred, and building their meters now would meter nothing.**

**What preparation means here, concretely:** every future capability adds **a `UsageReader` port on its own module's `public/`** — *a port belongs to the module that owns the language it represents* (§6). **There is no central registry to edit**, which is what makes the list extensible without a bounded context.

## 8 · Build vs buy — refined

| **Build** | **Buy** |
|---|---|
| Usage accounting · aggregation · **reconciliation** · **snapshots** · **audit trail** | Subscription management · invoicing · payment processing · taxes · customer billing portal · **dunning** · collection |

**The line is unchanged and now stated in the owner's words.** **Only Signora can say what a workspace consumed; everything downstream of that number is a commodity** (§9, *build the advantage, buy the commodity*).

> **Reconciliation and audit trail sit on the *build* side deliberately.** They are the questions *"does our meter agree with the invoice?"* and *"why was this workspace charged for that?"* — **and neither can be answered by a system that does not hold the operational facts.** A vendor's dispute tool would be reasoning about numbers it received rather than the runs that produced them.

**Stripe Billing is the preferred first integration.** An API rather than a datastore, so it adds nothing to operate and **consumes the aggregation Signora must build regardless** — nothing is wasted if it is later replaced.

**Lago is the future self-hosted option, revisited only on scale evidence.** §14 and [12-scalability.md](12-scalability.md): **performance and platform changes are evidence-triggered, never scheduled.** The trigger is stated rather than left to judgement — **a billing volume or contract structure Stripe cannot express**, not a preference for self-hosting.

## 9 · The two initiatives, sequenced

### 9a · Usage Accounting — first, and it is mostly reads

**No new module. No new event per action. One table, and only at period close.**

| | Slice | Depends on |
|---|---|---|
| **1** | `UsageReader` on `ai_platform` — AI actions and tokens per workspace per window | — |
| **2** | `UsageReader` on `provider_platform` — sync runs, records received | — |
| **3** | Seat counting from `membership` — unique active users per month | — |
| **4** | A closed billing period — **the one materialization**, immutable, the `ai_narration` pattern | 1–3 |
| **5** | `usage.period_closed` | 4 |
| **6** | Stripe Billing integration | 4, 5 |

### 9b · Usage & Billing Observability — second

**Ruled 2026-08-04. It serves four audiences and that is why it follows rather than accompanies.**

| Audience | Needs |
|---|---|
| **Customers** | Usage dashboard · cost transparency · limit warnings · daily and monthly summaries |
| **Engineering** | **Meter health** · reconciliation · audit tooling |
| **Finance** | Reconciliation · forecasting · monthly summaries |
| **Support** | *"Why was this workspace charged for that?"* — the audit trail, per row |

> **Meter health is the item worth naming, because it is the one nobody asks for until it has failed.** A meter that silently stops recording produces a **smaller** invoice, so **the failure is invisible from the billing side and only detectable against the operational history.** That is the argument for building reconciliation rather than buying it.

**Three constraints carried from the assessment:**

**Quotas and limit warnings are *entitlement*, not metering** — §3c. They read usage and belong to whoever owns the plan. **Forecasting is a projection over recorded facts, never a model** — §2's least-powerful-author rule: a projection that infers has climbed a rung it did not need. **Anomaly detection is out of scope entirely** — it is `signal_engine`'s shape, and a meter that decides something is anomalous has started inferring.

### The trigger, stated so it is checkable

> **Neither initiative starts until Billing naturally reaches this stage.** **The trigger is the Billing screen being scheduled for implementation** — not a date, and not a lane becoming available.
>
> **[D-029](../DECISION_REGISTER.md) is why**: *"do not force a module boundary until implementation naturally reaches it."* **Preparation is complete; nothing is claimable.**

## 10 · Risks

| | |
|---|---|
| **1** | **A usage event stream would be built alongside meters that already exist.** The brief's *"every module publishes a Usage Event"* is the most likely path to §2's duplicate-truth defect |
| **2** | **A closed period is the only immutable record, and if it is derived instead of materialized, a data change re-prices a shipped invoice.** Silent, and discovered by a customer |
| **3** | **Naming it *Intelligence* invites inference into a component that must only count** — and an anomaly detector inside a meter is how that starts |

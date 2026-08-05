# 455 · Context Definitions — R-02 Saved View and R-03 Action Batch

**Lane C · Product Office · 2026-08-05.** **[D-091](../DECISION_REGISTER.md).** **Both ownerships are approved; this is the implementation contract.**

> ***"This should become the implementation contract rather than allowing individual slices to redefine the capability as they progress."***

**Nothing implemented. No lane named. No ADR drafted** — R-03's still waits on [TASK-431](../BACKLOG.md)'s shape ruling.

---

# 1 · Saved View — `workspace_tenancy`

| | |
|---|---|
| **Purpose** | **Persist and retrieve a named, shared declaration of a query.** Four screens wrote the definition independently: *"stores the query, the filters and the sort — **not the results**"* |
| **Owning context** | **`workspace_tenancy`** — approved [D-091](../DECISION_REGISTER.md) |
| **Bounded responsibility** | A **name** · an **author** · a **workspace** · an **opaque declaration** · retrieval · permission-aware listing · versioning |
| ⛔ **Explicit non-responsibilities** | **Never parses, validates, executes, ranks or optimises a declaration.** **Never knows what a *filter* or a *sort* means.** **Never materialises results** — *"not the results"* is the specification. **Never a user preference** ([452](452-app-shell-traceability-audit.md): a view is *"per view, not per user"*, and a preference is the opposite concept). **Never enforces the consumer's permissions on the query's *contents*** — it governs who may read **the view**; the consumer governs what the query returns |
| **Public interface** | **`SavedViewView` · `SavedViewListView` · `SavedViewReader` · `SavedViewWriter`** — the `View · ListView · Reader` triple this module already publishes three times |
| **Expected consumers** | **Companies · App Shell · Global Search · Reports** — and **16 screens inherit the shell's** |
| **Lifecycle** | **Created → superseded → retired.** ⛔ **A declaration is never edited.** A change is a **new version naming the one it replaces**, exactly as `IcpDeclaration` does — *"an edited one would make those citations unresolvable"* |
| **Events produced** | ⛔ **None, and deliberately.** **[P-C](../DOMAIN_DISCOVERY_REGISTER.md): an event exists when a consumer appears, and none has.** ✅ **The first consumer that must know a view changed is what creates `saved_view.changed`, not this definition** |
| **Events consumed** | ⛔ **None** |
| **Repository reuse** | **The publishing triple · `IcpDeclaration`'s versioning · RLS and `workspace_id` scoping · cursor pagination · `WorkspaceQueryPort`'s existing edge** — ✅ **`opportunity_engine` already imports it, so no contract is amended** |
| **Implementation constraints** | **The store imports no consumer module, ever.** **No `UPDATE` grant** — immutability is enforced where it lives. **`FORCE ROW LEVEL SECURITY` and registration in `tenancy_policy.py` in the same change that creates the table** |

> ## The one rule that keeps this small
>
> ***"Its responsibility is persistence and retrieval, not execution."*** ⚡ **A declaration this store could call *invalid* would make `workspace_tenancy` responsible for another module's semantics** — the boundary `commercial_profile` holds by never reading the pipeline.

---

# 2 · Action Batch — a new bounded context

| | |
|---|---|
| **Purpose** | **Record that a change was proposed, approved, applied as one named unit, and whether it can still be taken back.** |
| **Owning context** | **New** — approved [D-091](../DECISION_REGISTER.md). ⚠️ **🔴 and its ADR waits on [TASK-431](../BACKLOG.md)'s shape ruling** |
| **Bounded responsibility** | **Intent · approval · the named unit · the execution lifecycle · the reversal window** |
| ⛔ **Explicit non-responsibilities** | **Never performs a write.** **Never knows what the change means.** ⚡ **Never knows how to reverse it** — *"each participating bounded context owns how its own business operation is executed and reversed"*. **Never schedules anything** ([P-B](../DOMAIN_DISCOVERY_REGISTER.md): the window is a read-time predicate). **Never notifies** — [ADR-0040](adr/0040-notifications.md) is deferred and this must not become a second delivery path. ⛔ **Never acquires business knowledge belonging to a consumer** |
| **Public interface** | **A port the acting module calls** — propose · approve · record-applied · withdraw — **and a reader answering *is this still withdrawable*.** **The acting module supplies the inverse operation; the batch calls nothing** |
| **Expected consumers** | **7** — Workflow subscribers · Companies bulk · Copilot's 17 surfaces · Opportunity next-actions · Settings · Account 360's AI sections · Executive Dashboard |
| **Lifecycle** | **`proposed` → `approved` → `applied` → `withdrawn`.** ⚡ **There is no *settled* state** — *"settled"* is `now() >= applied_at + window`, **computed, never stored**, and **`Snoozed.until` is the precedent** ([447 §0](447-signal-center-traceability-audit.md)) |
| **Events produced** | ✅ **`batch.applied` · `batch.withdrawn`** — **and [P-C](../DOMAIN_DISCOVERY_REGISTER.md) is satisfied**: [446](446-companies-traceability-audit.md) found the consumers already waiting — *"the timeline cannot show it and no audit can count it"* |
| **Events consumed** | ⛔ **None.** ⚡ **A rule match is consumed by the *subscriber*, which then proposes a batch** — the batch context never subscribes, which is what stops it becoming a second orchestrator |
| **Repository reuse** | **Outbox · relay · dispatch · idempotency · ARQ** — all built. **Supersession as reversal** *(five instances)*. **`actor_id`** *(37 files)*. **`MACHINE_AUTHORED = frozenset({Stage.TRACKING})`'s discipline** — *"intelligence suggests; humans commit"*, made structural by a database constraint |
| **Implementation constraints** | **Imports no consumer module.** **Bulk application runs in a worker** ([446](446-companies-traceability-audit.md): *"8,412 rows is not a request cycle"*). ⚠️ **Its progress surface must distinguish *running* from *failed* from *never started*** — [P-A](../DOMAIN_DISCOVERY_REGISTER.md), and *"absence can never distinguish itself from failure"* |

---

# 3 · ⚡ Implementation independence — the contract lands first, alone

**[D-091 §4](../DECISION_REGISTER.md): *"multiple implementation lanes can safely build against it without becoming tightly coupled… through stable public contracts and published events rather than direct module knowledge."***

> ## **So slice 1 of each is the `public/` contract and nothing else.**
>
> **A consumer lane can compile, type-check and write its tests against a published port before a single row is persisted.** **`lint-imports` proves the coupling never forms**, and **`mypy --strict` proves the contract is honoured** — which is stronger than a convention and is how this repository already works.

**And the two capabilities are independent of each other.** ⛔ **The batch does not store a saved view; a saved view is not applied.** **They can be built in parallel by different lanes**, which is the point of preparing both now.

---

# 4 · Decomposition — R-02, four slices

| | Slice | Depends on | Parallel? |
|---|---|---|---|
| **1** | **`public/` contract** — the four types, no implementation | **Nothing** | ⚡ **Unblocks every consumer immediately** |
| **2** | **Domain + persistence** — the aggregate, its versioning, the migration with forced RLS and `tenancy_policy.py` registration | 1 | |
| **3** | **Application + interface** — reader, writer, endpoints, permission-aware listing | 2 | |
| **4** | **UI integration** | 3 · **[TASK-433](../BACKLOG.md)'s name** | ✅ **Product Surface's, in parallel with nothing else** |

⛔ **No events. No projections.** **Both would be speculative** — [P-C](../DOMAIN_DISCOVERY_REGISTER.md) and *"not the results"*.

# 5 · Decomposition — R-03, six slices

| | Slice | Depends on | Parallel? |
|---|---|---|---|
| **1** | **`public/` contract** — the port and the reader | **The ADR** | ⚡ **Unblocks all seven consumers** |
| **2** | **Domain** — proposal, approval, the named unit, **the window as a predicate** | 1 | |
| **3** | **Persistence** — append-only, no `UPDATE` grant, forced RLS | 2 | |
| **4** | **Application + the two events** | 3 | |
| **5** | **Asynchronous application + the progress surface** | 4 | ⚠️ **[P-A](../DOMAIN_DISCOVERY_REGISTER.md) applies here** |
| **6** | **First consumer end to end** — ⚡ **recommend Companies bulk**, because [446](446-companies-traceability-audit.md) audited it and it is the only consumer whose *whole* workflow is already specified | 5 | ✅ **Then six more, in parallel, each in its own module** |

> **Slice 6 is one consumer, deliberately.** **A contract proven by one real caller before six adopt it** is the discipline [ADR-0403](adr/0403-signal-engine-reads-a-declaration.md) used, and **a port with seven simultaneous first callers has no chance of being corrected cheaply.**

---

# 6 · What this asks for

**Nothing new.** **Both definitions are complete and neither needs a ruling** — **R-02 can be prepared as backlog rows the moment [TASK-433](../BACKLOG.md) names it; R-03 needs its ADR, and the ADR needs [TASK-431](../BACKLOG.md)'s shape.**

**The two rulings already on your page are still the only things in front of ten slices.**

---

# 7 · What this document did not do

**Nothing implemented · no lane named · no ADR drafted · no module created · no wave reordered · no queue file touched · no backlog row added.**

**And it deliberately specified no event for R-02.** **[P-C](../DOMAIN_DISCOVERY_REGISTER.md) says an event exists when a consumer appears; none has** — **and a context definition is exactly where a speculative event catalog would otherwise be born.**

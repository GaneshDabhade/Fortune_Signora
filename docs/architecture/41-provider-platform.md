# 41 — Provider Platform: how evidence enters, and what stops it entering twice

> **The module design doc, started 2026-08-02 — four milestones after the module.** Provider Platform was built in M2.0 and M2.1 and has had no design document since; the modules documented in `22`–`29` all arrived later and all got one. This is the gap closed, and the circumstance is recorded rather than tidied away: under rotating assignment a module's design doc is the next assignee's only inherited context (`CLAUDE.md` §12), and this module — the one every other module's data passes through first — had none.
>
> **What this document covers, honestly.** The synchronization model as it stands today and the target-account contract being built on it. It is **not** a retrospective reconstruction of M2: the Provider Port, the adapter contract and the simulation framework are specified in [20-provider-simulation.md](20-provider-simulation.md) and [21-intelligence-pipeline.md](21-intelligence-pipeline.md), and this document references them rather than restating them (§2, *truth has exactly one authoritative representation*).

## What the module owns

**Synchronization — entirely** ([ADR-0036](adr/0036-target-account-contract.md) §1): cadence, polling policy, cost, provider selection, failover, backoff, deltas.

**None of it is a customer's to configure**, ruled 2026-08-01. A customer says *watch this company*; everything about how often, from whom, at what cost and in what order is Signora's. That is the boundary most likely to be taken by a neighbour, which is why the ADR states it as a permanent ownership rule rather than a design preference.

**What it deliberately does not own:** intent (Commercial Profile), understanding (Knowledge Graph), intelligence (Signal Engine). A `subject` arrives unresolved and **stays** unresolved — resolution happens downstream, in the module whose competence it is.

## The synchronization state

| | What it records | Why it is separate |
|---|---|---|
| `provider_sync` | One run: when, how many pages, how many records, how it ended | The history of what happened |
| `provider_watermark` | **How far one subject has been read**, and **when a provider last looked** | Resetting it is the standard recovery from a bad run, and **recovery must not destroy the record of what went wrong** |
| `raw_provider_record` | What arrived, before interpretation | Evidence. Immutable, and cited by every conclusion downstream |

### A watermark records *when we looked*, not only *what we found* — A7 *(2026-08-03)*

**`position` could not answer whether Signora is still watching an account**, and that is a different question from how fresh the evidence is. It advances **only when records arrive**, so a successful read that returned nothing left no trace at all:

> **An account nobody has found anything about is indistinguishable from one nobody has checked.**

A seller reading *"Latest evidence · 5 weeks ago"* could not tell whether **the account went quiet or the pipeline did** — and those are opposite conclusions about whether to call.

**`attempted_at` is written on every completed run**, regardless of `high_water`. One column, one write, no new table, and it keeps *how far we read* and *when we last tried* in the row that already knows the subject.

| | |
|---|---|
| **Why not `subject` on `provider_sync`** | More faithful to *runs* — but it adds a per-subject row to a table whose grain is deliberately per-run |
| **Why not a new table** | Nothing about the fact is independent of the watermark. Two tables keyed identically is the duplication §2 forbids |
| **Why completed runs only** | A run that raised **did not successfully look.** Recording it here would relocate the false certainty this field exists to remove; what happened is on `provider_sync`, which is the record for it |

**`SyncWatermark.attempted()` always moves, deliberately unlike `advanced_to()`.** A position going backwards would re-deliver evidence between the two; **an attempt time is a statement about when a run finished, and the run writing it finished last.** The asymmetry is the design, not an oversight, and it has a test.

**A watermark row now exists where none did before**, and that is safe by a property the module already had: `subjects_with_a_position` filters on **`position IS NOT NULL`**, not on the row — *"a watermark with no position records an attempt that stored nothing"* ([ADR-0036](adr/0036-target-account-contract.md) §4). **A row created purely to record an attempt cannot make an unread subject look read.**

**Not backfilled, and the null is the honest value.** Every existing row was read at some point and nothing recorded when. `now()` would assert every subject was checked at migration time; `created_at` would assert each was checked once and never since. **Both are false, so the product says it does not know.**

> **What A7 did not yet deliver, and it was the open half.** `subject` is the customer's typed company name; the brief holds an entity id, and resolution is deliberately downstream ([ADR-0036](adr/0036-target-account-contract.md) §5). **Joining the two is unresolved** — [C-219](../LANE_COORDINATION.md), with Lane C. Until it is, **nothing renders this**, and **the word *checked* does not reach a screen**: A4 refuses it and `freshness.test.tsx` asserts the refusal, which is the contract the render slice updates rather than works around. *(Closed 2026-08-06 — see below.)*

### The column reaches a screen, and it did so without a join — A7's render *(2026-08-06)*

**[C-219](../LANE_COORDINATION.md) was ratified by Lane C on 2026-08-06: option ③, freshness renders *per target account*.** The paragraph above framed the open half as a join to be designed. **The ruling's finding is that there was never a join to perform**, and the code is why:

| | |
|---|---|
| **`TargetAccount` is `(id, name)`** | And **nothing else.** `target_accounts.py`: *"It names companies; it finds none… It does not resolve the name"* |
| ⚡ **The key identity** | **`TargetAccount.name` is what becomes `RunProviderSync(subject=…)`.** The two keys are the same string from the same source |
| ⛔ **Why ② was refused, not merely deferred** | A subject↔entity binding table is **the only route to the brief, and the brief is closed**: `TargetAccount` carries no entity id *deliberately* and [ADR-0036](adr/0036-target-account-contract.md) makes that permanent. Sequenced behind a stated trigger — *a screen that must state freshness for an account reached through something other than a target declaration.* **Not fired** |
| ⛔ **Why ① was refused outright** | Matching subjects to entities by name is **a second resolver, by a weaker method than the resolver's** — and its failure is silent and confident |

**`GET /workspaces/{id}/target-account-coverage`** — this module's **first and only HTTP surface**. It takes the subjects a caller is rendering and answers one entry each.

> **Why the endpoint is here rather than a field on the target account list.** That list is Commercial Profile's, and the dependency matrix runs **Commercial Profile → Provider Platform** ([05](05-module-dependencies.md)). **The module holding the list may not read the module holding the attempts**, and reversing the edge would make the graph cyclic. **So the frontend composes the two** — the same arrangement `account-identities` uses to put names on accounts, and the option that needed no graph change.

**Four states, carried by two nullable-independent fields rather than one status string.** A string would enumerate them, and the enumeration would then exist twice — here and wherever it is rendered.

| `last_attempt` | `stored_anything` | |
|---|---|---|
| `null` | `false` | **Nobody has ever looked** |
| a moment | `false` | **Looked, and found nothing** — the case `position` could not express, and the reason the column exists |
| a moment | `true` | **Looked, and evidence arrived** |
| `null` | `true` | **Read before `attempted_at` existed.** The null the migration deliberately did not backfill, surfacing exactly as itself |

**Rows collapse across providers and capabilities.** A subject has one watermark per `(provider, capability)`, and the question a seller asks is *when did anybody last look* — not *when did Apollo's company enrichment last look*. **The latest attempt wins; evidence from any of them counts.**

**A subject with no watermark comes back as an entry, never as an omission.** *Never checked* is an answer, and a caller reading a missing key renders a blank — which is the state A4 already refuses in words rather than in whitespace.

**The word *checked* now ships, and `freshness.test.tsx`'s refusal was scoped rather than lifted.** `Freshness` still may not say it and its test still asserts so, because on the brief it still would not be true. `LastChecked` is **a second export beside it** — which is what that component's own docstring said the second kind would be — so the honest sentence and the dishonest one are not one boolean apart inside one component.

**Authorization reuses `target_account, read`.** The timestamps beside a list a member may already read say nothing that list does not; a new resource for them would be a distinction `policy.csv` could not defend.

### A watermark belongs to one subject — PP-01, B-004 *(2026-08-02)*

**The key was `(workspace_id, provider, capability)` and carried no subject**, so a workspace watching two accounts shared one position between them.

> Sync Acme to Tuesday. Sync Initech. Initech's run reads Acme's position, asks the provider for everything *since* it, and **every Initech record older than Tuesday is never requested.**

**No error, no log, no failed sync.** Evidence that never becomes a signal, on an integration that looks healthy — which is why it gets a suite of its own rather than an assertion inside an existing test.

**It was latent, and PP-02 is what ends that.** Nothing outside the Provider Simulation Framework has ever supplied a `subject` — `RunProviderSync` has taken one since M2.1 and no caller has filled it — so no workspace has yet had two. The consumer gives every declared account one. [ADR-0036](adr/0036-target-account-contract.md) therefore names this *"one defect that must be fixed before the consumer is built"*, and the ordering is the whole reason it is slice 1.

**`subject` is part of the identity, not a label on it.** `SyncWatermark` gives it no default: a watermark that cannot name its account **is** the defect, so the type refuses to construct one, and `get_watermark` requires it rather than accepting `None`. A caller that could omit it would get another account's position — silently, which is the property that made the original bug expensive.

**Rows written before the column keep an empty subject** (migration `0029`). Which account an old position belongs to is not recoverable, and inventing an attribution would be worse than admitting none. An empty subject matches no real one, so those rows are inert and the first sync of each subject requests a full snapshot — **which is what an absent watermark already means**, so nothing new exists to handle it.

**The downgrade discards watermarks and says so.** Narrowing the constraint means collapsing many rows into one and there is no correct choice of which to keep; it keeps the furthest-advanced position, which is safe for the *constraint* and unsafe for *coverage*. Recorded in the migration rather than left for someone to discover — the honest recovery afterwards is to reset the affected watermarks, which destroys no history because syncs and raw records are separate tables.

## The target-account contract — what PP-02 and PP-03 build

**Specified in full by [ADR-0036](adr/0036-target-account-contract.md); the shape is repeated here only as far as a lane needs to navigate it.**

```
  commercial_profile                        provider_platform
  ──────────────────                        ─────────────────
  target_accounts_changed  ──trigger──▶     the consumer
   (workspace_id, declaration_version)          │
                                                │ calls
  TargetAccountReader      ◀──payload───────────┘
   (the whole list, never a delta)               │
                                                 ▼
                                          delta vs provider_watermark
                                                 │
                                                 ▼
                                          RunProviderSync per subject
```

**The event triggers; the port supplies.** Not a choice between them — events carry identity, ports carry payload.

**Provider Platform computes its own delta**, because a delta from Commercial Profile is a delta between two *declarations*, and what matters is the delta against **what has actually been synced**. Re-adding an account that was declared before and never successfully fetched is *"no change"* to a declaration and real work here.

**`declaration_version` orders what idempotency cannot.** Idempotency on `event_id` handles redelivery; it does not handle two declarations in quick succession arriving out of order. An event older than the version already acted on is ignored — compared locally, with no coordination.

**Removal stops polling and deletes nothing** (§6). Raw records are evidence that conclusions a customer has already read and acted on still cite. *Erasability is a property of the tenancy model* — it belongs to deleting a workspace, not to un-watching a company. **The watermark stays**, so re-adding resumes incrementally.

## The implementation sequence

**The order is the ADR's, not a preference.** PP-01 must precede PP-02 because the consumer is what gives a workspace two subjects; PP-03 must follow PP-02 because *stopping* polling is meaningless before anything starts it.

| Slice | What it establishes | State |
|---|---|---|
| **PP-01** — a watermark belongs to one subject | [B-004](../BUGS.md), and the precondition [ADR-0036](adr/0036-target-account-contract.md) names | Built 2026-08-02 · [TASK-015](../BACKLOG.md) |
| **PP-02** — the consumer | The module's first real input | **Built to the composition root; blocked there by [C-021](../LANE_COORDINATION.md)** |
| **PP-03** — un-watching stops the spending | [ADR-0036](adr/0036-target-account-contract.md) §6 | **Re-scoped before it started — see below** |
| **PP-04** — the module can be measured | §17 · [12-scalability.md](12-scalability.md)'s extraction trigger | Built 2026-08-02 |
| **PP-05** — the platform paces itself | `rate_limit_per_minute`, declared in M2.0 and read by nobody | Built 2026-08-02 |
| **PP-06** — ingestion says where a payload came from | [20-provider-simulation.md](20-provider-simulation.md), stated three times | Built 2026-08-02 |

> **PP-02 and PP-03 are proposed slices, not registered tasks** (product-owner refinement, 2026-08-02). A feature lane plans its own sequence inside its implementation area; **it does not mint repository task identifiers** — that namespace is registered centrally, so two lanes cannot extend it independently. This table is the plan; [`BACKLOG.md`](../BACKLOG.md) is the register, and only QE writes ids into it.

### What PP-02 built, and where it stops

**Everything a lane may build.** The delta rule (`domain/targets.py`), the version ordering, `target_sync_state` (migration `0030`), its repository, the `SyncDeclaredTargets` use case and the event handler — typed, and covered by 17 unit tests against fakes.

**It stops at one thing: the handler cannot reach a provider adapter.** `RunProviderSync` needs a `ProviderAdapter`, which lives in the ARQ task context; an event handler receives a `WorkerRuntime`, which holds a session factory, an HTTP client and AI settings and **no provider registry**. And no module can enqueue ARQ work — the only enqueue path is the relay's, driven from the outbox and frozen under §20a.

**So the consumer can decide what to sync and has no way to start it.** Both routes out are outside a lane's Change Budget, which is [C-021](../LANE_COORDINATION.md).

**`SyncDispatcher` is a port precisely so this is a question about which adapter to write**, not about what to redesign. Nothing above it changes whichever way the decision goes.

### Three outcomes, and why none of them is an error

`SyncDeclaredTargets` returns a reason rather than a bare *"nothing happened"*, because three ordinary situations produce no work and one of them is worth investigating:

| | Means |
|---|---|
| `stale` | The event announced a declaration already overtaken. **Checked before the declaration is read**, so a stale event costs nothing |
| `never_declared` | The workspace has never declared a list. *"They have not told us yet"* is a state to wait in |
| `nothing_new` | Every declared company has already been read. **The version is still recorded**, or the next event would recompute an identical delta forever |

**Dispatch happens before the version is recorded.** If recording fails, the event redelivers, the delta is recomputed against the same watermarks and the same companies are dispatched again — wasteful once, and every layer below is idempotent. Recording first and failing to dispatch would lose the work **silently**, and nothing downstream would notice a company that was never fetched.

## Operational considerations

### Ingestion records its own provenance — PP-06 *(2026-08-02)*

**[20-provider-simulation.md](20-provider-simulation.md) states this three times, and the strongest statement is not about observability:**

> *"Every ingestion log line marks the payload as simulated, names the dataset version, scenario, and seed. **This is a safety control as much as an observability one: if simulated data ever reaches a place it should not, the logs must say so unambiguously and immediately.**"*

**`ProviderResponse.simulated` and `.replay` have carried that since M2.0, `ReplayContext.as_log_fields()` was written to emit it, and nothing had ever called it.** The framework's own guard refuses to *activate* outside development; **this is the other half** — proving from the record what a given row was built from.

| Decision | Why |
|---|---|
| **`simulated` on every line, not only simulated ones** | A field that appears only when true makes its absence ambiguous — *not simulated* and *logged before this line existed* look identical, and an operator filtering for real data would be trusting a silence |
| **The replay fields travel with it** | *"When output changes, what changed?"* Scenario, seed, manifest, generator, clock and dataset separate a model change from a prompt change from a quietly-updated payload shape, and **separating them after the fact is impossible** |
| **Per page, not per record** | One line per response covers every record in it through `sync_id`; per record would put thousands of identical provenance lines in the way of reading anything |
| **Never in the payload body** | That would change its shape and defeat the identical-contract rule that makes simulation worth having |
| **The use case never names simulation** | `ProviderResponse.provenance_fields()` assembles the line's provenance in `domain/provider.py` — **the one file AC-21 permits to know simulation exists**. The use case asks for provenance and spreads the answer without knowing what is in it |

**The Security Invariant caught the first attempt.** Reading `response.simulated` directly in `application/run_sync.py` failed `test_no_new_simulation_knowledge_enters_the_pipeline` — correctly: *a pipeline able to name where a payload came from is one able to branch on it.* **The fix was the code, never the test.** The resulting shape is also the better one, which is the usual outcome when that suite refuses something.

### The platform paces itself — PP-05 *(2026-08-02)*

**`ProviderDescriptor.rate_limit_per_minute` was declared in M2.0 and read by nothing in production.** Its own docstring states the purpose — *"declared so the platform can pace itself rather than discovering the limit by being throttled"* — and the contract suite asserts every adapter declares one or explicitly declares none. The declaration was honoured by nobody.

**What that cost is not politeness.** `_drain` fetches up to `MAX_PAGES` — five hundred — back to back, as fast as the network allows. Against an adapter declaring sixty requests a minute, one sync can spend the whole quota in seconds and then receive `ProviderRateLimitedError`, which is **transient**: the sync fails, the watermark is deliberately left untouched, and the retry runs against a quota that is still exhausted. **The pages already fetched survive. The requests that bought them are spent twice.**

| Decision | Why |
|---|---|
| **No declared limit means no waiting** | Never a default rate. Inventing one for a provider that stated none would slow every sync to a speed nobody asked for — and the contract suite permits declaring none |
| **The first page is never delayed** | It follows nothing this loop issued. Pacing it would add latency to every sync in exchange for spacing that is already there |
| **Elapsed time counts against the interval** | A provider that took two seconds has already spent two seconds of its own spacing; waiting the full interval on top punishes a slow provider twice |
| **A declared limit of zero is refused** | *"Never ask"* is not a rate limit — it is a disabled provider, and that is a different decision made somewhere else |
| **The waiting is a port; the arithmetic is not** | `RequestPace` is domain and asserted directly; `AsyncioPacer` is the one line that cannot be. **A test that slept for real would be measuring `asyncio`**, slowly, and would still not prove the arithmetic |

**`asyncio.sleep`, never a blocking wait.** A paced sync must not hold a worker's event loop while it waits, or one throttled provider would stall every other sync sharing the pool.

#### What this deliberately does not solve

**Pacing is per sync, not per provider.** Two syncs running concurrently against the same provider each pace themselves correctly and **together exceed the declared rate.**

**Fixing that needs shared quota state** — a counter in Redis or a row every sync contends on — which is a different architectural decision from *"honour a number the adapter already declares"*, and one with its own failure modes. **Not built, and not disguised as built.** What ships here bounds a single sync from five hundred requests in seconds to the declared rate, which is a strict improvement over nothing; it does not make the limit a platform-wide guarantee.

**The trigger to revisit** is more than one concurrent sync per provider per workspace, which nothing schedules today — the same absence that re-scoped PP-03.

### The module emits metrics — PP-04 *(2026-08-02)*

**Built while PP-03 waits on [C-021](../LANE_COORDINATION.md), because the module was not out of executable work — only its next planned slice was.**

**[12-scalability.md](12-scalability.md) states this module's extraction trigger:** *"if provider count and polling volume grow to the point where its scheduling/quota logic needs an independent deployment and on-call surface."* **That trigger was unmeasurable.** §17 exists for exactly this: stage latency, throughput and error rate are instrumented *because* the scaling triggers depend on them.

#### Why counters, when every sync is already a row

**`provider_sync` cannot answer a platform-wide question.** It is workspace-owned with forced RLS and every runtime identity is scoped to one workspace — permanently, by design. So *"what is the failure rate right now"* and *"is polling volume growing"* would require reading across every tenant, which is what the tenancy model exists to prevent.

**Not a duplicated truth** (§2): the row records what happened to **one workspace's sync**; the instrument records how **the platform** is behaving. Only one of them is readable by an operator, and only the other can be shown to a customer.

| Instrument | The decision it serves |
|---|---|
| `signora.provider.sync_duration_ms` | Latency, for the extraction trigger. **Recorded on failure too** — a sync that failed after four minutes and one that failed instantly are different incidents, and a series that excluded failures would look healthiest exactly when a provider started timing out |
| `signora.provider.records_received` | Throughput. **Received, not stored**: storage deduplicates, so stored measures novelty and the trigger is about how much a provider is being *asked* for |
| `signora.provider.sync_failures` | Error rate, attributed by `SyncFailureKind`. **`CONTRACT` is the sharp one** — a provider's payload stopped matching the adapter, which is an integration silently dropping data rather than one that is down. Today the first sign would be a customer asking why an account went quiet |

**Provider is an attribute, never a metric name.** A metric per vendor makes *"is polling volume growing"* a query nobody can write without knowing the vendor list, and the vendor list changes.

#### Two decisions inside it worth keeping

**The reporter is a port in `application/`, and only the adapter knows OpenTelemetry exists.** The use case states what happened; whether that becomes a histogram, a log line or nothing belongs to the composition root.

**Silence is the thing you have to ask for.** `build_run_sync` defaults to the real reporter and the null one is explicit — an observability gap is invisible by construction, so the default must not be the one that hides it. And a **null object rather than an optional reporter**: a `None` check at every call site is one behaviour duplicated at each of them, and the skip branch is the one nothing exercises.

**Nothing here is a spend figure.** Operational facts and commercial policy stay separate (§10) — cost is applied at reporting time over these counts, never written beside them.

**Fan-out is the known scaling question, and it is deliberately not designed for yet.** A declaration of *n* companies becomes *n* syncs. Under the recommended dispatch (C-021, route A) they run in one handler invocation on the `provider_sync` pool.

**The trigger to revisit is a declaration large enough to exceed that pool's job timeout** — not a number chosen now. §14 is explicit that performance work is justified by evidence rather than intuition, and the largest declaration in existence is twelve. **The failure mode is also self-healing**: a timeout dead-letters the event, redelivery recomputes the delta against watermarks that have since advanced, and the remaining work shrinks on every attempt.

### Nothing polls, and PP-03 was named for stopping it

**`WorkerSettings.functions = [dispatch_event]`, and `run_provider_sync` appears nowhere in `apps/`.** There is no cron, no schedule and no recurring job. A sync happens once, when something calls it — and **nothing calls it.** Every sync that has ever run in this repository ran as a direct in-process call from a test or a seeder.

**So PP-03 — *"un-watching stops the polling"* ([ADR-0036](adr/0036-target-account-contract.md) §6) — is named for something that does not exist.** The half of §6 that is implementable today is already true and needed no code: the consumer only ever dispatches *declared* subjects, so removing one stops it being dispatched, and nothing deletes anything, so *"deletes nothing"* holds by construction.

**Recorded before the slice starts rather than at its first commit.** A lane arriving at PP-03 would write the stopping logic, find nothing to stop, and either invent a scheduler or ship a no-op — **and the no-op would be indistinguishable from working code.** Both belong to [C-021](../LANE_COORDINATION.md), which any answer settles.

**PP-02 is what [TASK-014](../BACKLOG.md) and [C-007](../LANE_COORDINATION.md) are blocked on** — the guided first run ends by publishing a declaration nothing consumes, and *"a guided first run is the most prominent place in the product to make a promise."*

---

## Implementation Waiting — declared 2026-08-02

**Every executable capability inside the accepted architecture has been built.** What remains needs an architectural decision, and the module is therefore suspended rather than finished — it is still Lane A's, and it consumes no engineering capacity until [C-021](../LANE_COORDINATION.md) has a direction.

### Completed

| | |
|---|---|
| **PP-01** | A watermark belongs to one subject. [B-004](../BUGS.md), migration `0029` |
| **PP-02** | The target-account consumer — delta against what was read, ordering by declaration version. Migration `0030` |
| **PP-04** | Latency, throughput and failure-by-kind, which [12-scalability.md](12-scalability.md)'s extraction trigger depended on |
| **PP-05** | The declared rate limit is honoured instead of discovered by being throttled |
| **PP-06** | Ingestion records whether a payload was simulated, and its replay provenance |

**Three of those five fulfil contracts the module had declared and never honoured** — `rate_limit_per_minute`, `ProviderResponse.simulated`/`.replay`, and the scaling trigger's inputs. **That pattern is the most useful thing found here**: the gaps were not missing features, they were promises the code was already making.

### Suspended

| | Blocked on | Resume trigger |
|---|---|---|
| **PP-02's last wire** — nothing starts a sync | [C-021](../LANE_COORDINATION.md) — an event handler cannot reach a provider adapter, and no module may enqueue ARQ work | A dispatch direction is accepted |
| **PP-03** — un-watching stops the spending | The same, plus **there is no polling to stop** | The same decision settles both |

### Operational observations, for future milestones rather than current work

**Recorded so they inform planning without becoming work nobody asked for.**

| | |
|---|---|
| **Provider quota is per sync, not per provider** | Two concurrent syncs each pace correctly and together exceed the declared rate. Global quota needs shared coordination, distributed state and failure recovery — **a new architectural capability**, not an extension of PP-05 |
| **Nothing schedules a sync** | No cron, no recurring job, and `run_provider_sync` is registered with no worker. Every sync in this repository's history was an in-process call from a test or seeder |
| **Fan-out is unbounded by design** | A declaration of *n* companies becomes *n* syncs. Revisit when a declaration exceeds the `provider_sync` pool's job timeout; the largest in existence is twelve |
| **Retry is the platform's, not the module's** | Transient failures leave the watermark untouched and rely on ARQ above. That is correct today and becomes a question the moment anything schedules syncs, because a retry storm and a schedule interact |
| **`MAX_PAGES = 500`** | The only bound on one sync's size. With pacing it is now also a bound on duration — 500 pages at 60/min is over eight minutes, which exceeds some pool timeouts. **Not changed here**: no adapter has approached it, and §14 forbids tuning for load nobody has |

# 53 — Action Batch (module design)

> Status: **Slices 1–2 of six — the `public/` contract, and the domain behind it.** Lane B, 2026-08-06 and 2026-08-07.
> Ratified by [ADR-0405](adr/0405-an-action-is-approved-before-it-is-effective.md), approved at [D-126](../DECISION_REGISTER.md); the context was assigned to Lane B by the product owner at [D-127](../DECISION_REGISTER.md). Decomposition: [455 §5](455-context-definitions-r02-r03.md).
>
> ⚠️ **Document number taken from the highest free number and checked against every branch first** — architecture numbers still have no allocation block ([B-401](../BUGS.md)/[B-328](../BUGS.md) family). `53` was free on `integration`, `lane-a`, `lane-c-sync` and `lane-qe`.

## The boundary, stated first

> **This context coordinates lifecycle. Business domains own business behaviour.**

| **It owns** | **The consuming domain owns** |
|---|---|
| The action as the canonical unit of work · approval · withdrawal · approval state · the reversible window · execution metadata · **the public contract** | **Interpreting** the action · **performing** the operation · **validating** business rules · **executing** the change · **implementing the inverse** |

⛔ **It is not responsible for business semantics**, and that sentence is the whole boundary. It is [ADR-0402](adr/0402-a-rule-is-data.md)'s shape reused: a rule is data, evaluated centrally, **and the module that owns an operation is the only thing that knows how to perform or undo it.**

**An import contract makes it structural**: `action_batch` imports **no business module at all** — seventeen of them, listed exhaustively rather than by layer, because there is no layer of any of them it may reach. A consumer hands it a lifecycle to coordinate; **it never reaches back for the meaning.**

## Why the contract shipped alone

**[P-E](../DOMAIN_DISCOVERY_REGISTER.md), ratified at [D-121](../DECISION_REGISTER.md).** Seven consumers are waiting, and **publishing first is what stops seven approval models being invented while this is built.** ADR-0405 states it as architecture rather than review practice:

> **Any future workflow requiring approval, deferred execution, reversible execution, withdrawal, human confirmation or staged execution must first evaluate whether it should *consume* this capability before introducing another approval model.**

**A consumer can compile, type-check and write its tests against the port before a single row is persisted** — `lint-imports` proves the coupling never forms and `mypy --strict` proves the contract is honoured. **The same shape [TASK-457](../BACKLOG.md) used for `people` hours earlier.**

## The window is a predicate, never a stored state

**`is_settled(now=…)` is computed, materialised nowhere, scheduled by nothing** — ADR-0405 §2, and the precedent is `Snoozed.until` in `signal_engine`, which [447](447-signal-center-traceability-audit.md) named *"the pattern R-03 should copy."*

**A stored `is_settled` column would be two representations of one fact** (§2) and a scheduler to flip it is machinery [P-B](../DOMAIN_DISCOVERY_REGISTER.md) exists to refuse. **Tests assert both the behaviour and the absence of the field.**

**Two cases a consumer will otherwise get wrong**, and both are pinned:

| | |
|---|---|
| **Never applied** | **Not settled.** It has no window to have elapsed, and reading it as settled would say a reversal is no longer possible for something that never happened |
| **No window declared** | **Not settled, and not expired either.** Reversal was never offered — a different sentence from *"the window has passed"* |

### ⚡ Slice 2 gave the predicate something to enforce, and one place to live

**Slice 1's window was true and unenforced.** `ActionBatchView.is_settled` answered the question and **nothing consulted the answer** — which is precisely the Decorative Logic §2 names: implementation that appears to protect a property whose removal changes nothing.

**`ActionBatch.reversed_by` is the guard that makes it real.** A reversal after the window raises; the boundary instant is refused, because the window is *for* 24 hours rather than *through* the instant it ends (`>=`, not `>`).

**And the rule now exists exactly once.** `domain.batch.has_settled` is the single executable statement; **the aggregate and the published view both call it.** A test asserts the two agree across four offsets — **including both boundary instants** — so a future restatement in either place fails rather than drifts. *A window computed in two places is a window that will eventually disagree with itself about whether a customer may still undo something.*

> ⚠️ **The two `False` cases are indistinguishable to the predicate and must not be to the customer.** *Never applied* and *no window declared* both answer `False`, and neither means *"still reversible"*. **`reversed_by` refuses each with its own reason** — *never took effect* versus *never offered* — because the predicate cannot tell them apart and a person reading the refusal must.

## The lifecycle, and what each transition refuses

**Every transition returns a new value and takes an `actor_id` with no default** (§2). **No method reads a clock** — `now` and `at` are arguments, because a clock read inside a domain method is a hidden input that defeats replay.

| Transition | From | Refuses |
|---|---|---|
| `approved_by` · `rejected_by` · `withdrawn_by` | `PROPOSED` **only** | A second decision — *"a batch leaves the proposed state exactly once, and the record of how it left is the thing an audit cites"* |
| `applied_on` | `APPROVED` **only** | Applying twice — *"two applications of one approval means the change was performed twice, which is a defect to surface rather than a timestamp to overwrite"* |
| `reversed_by` | applied, **inside the window** | Never applied · no window offered · already reversed · **window closed** |

⛔ **`applied_on` takes no `actor_id`, and that is deliberate.** Application is performed by the consuming domain **on the authority of the approval already recorded**; inventing a second actor would attribute the write to whoever happened to flush it.

> ⚠️ **One discrepancy resolved in favour of the published contract, and recorded rather than left silent.** **[455 §2](455-context-definitions-r02-r03.md) sketches the lifecycle as `proposed → approved → applied → withdrawn`**, which reads as though withdrawal follows application. **Slice 1's `public/` says otherwise and says it precisely**: `WITHDRAWN` is *"taken back **before** approval… a decision that was never made, rather than one that was reversed"*, and `REVERSED` is *"undone **after** it took effect."*
>
> **The contract wins.** It is what seven consumers compile against, it distinguishes two facts a customer is told differently, and **455's arrow is a one-line sketch in a decomposition table rather than a specification of the states.** ⛔ **So `withdrawn_by` is refused after approval** — that path is `reversed_by`, and it has a window. **Named here because the next reader will hit the same two sentences and should not have to re-derive which one binds.**

**Nothing may predate its own proposal.** A decision or an application timestamped before `proposed.at` is refused — a clock skew that would otherwise produce a history reading backwards.

## Where the vocabulary lives — corrected in slice 2

**`ApprovalState` was defined in `public/` by slice 1 and now lives in `domain/batch.py`, re-exported from `public/`.**

⚡ **The published API is unchanged** — same names, same `__all__`, same import path for every consumer. **What changed is which layer defines it.** §6: *a port belongs to the module that owns the language it represents… it lives in that module's `domain/` and is published through its `public/`* — the shape `knowledge_graph/public/attributes.py` and `commercial_profile/public/` both already use.

**The alternative was `domain/` importing from `public/`** — a dependency pointing outward, which every later slice would have inherited. **Slice 1 was not wrong to put it there; there was no `domain/` to hold it.**

## Five states, and two pairs that must not merge

**`WITHDRAWN` and `REJECTED` are different facts** — the proposer changing their mind, and a reviewer declining. A customer reading a history needs to tell them apart.

**`APPROVED` does not imply applied.** Approval and application are two moments, and `APPROVED` with a null `applied_at` is a real state rather than an inconsistency — slice 5 is what makes the gap between them visible.

> ⚠️ **One test was written as `WITHDRAWN is not REJECTED` and `mypy --strict` refused it** — a non-overlapping identity check, a tautology the type system sees through. **The real assertion is that the enum carries both**, which is what a later collapse into one value would break. Recorded because the first form looked like a test and asserted nothing.

## A count, never the items

`ActionBatchView` publishes `item_count`. **What each item *means* belongs to the domain that proposed it**, and publishing the items here would put business semantics in the context whose entire boundary is that it holds none. **Asserted, not merely intended.**

## ⚠️ `action_batch` is the context's identity, not the product's word

**No customer-facing name is ratified.** [D-127](../DECISION_REGISTER.md) forbids a placeholder becoming production terminology because implementation started first, and ADR-0405 leaves it open deliberately: *"a name is [ADR-0034](adr/0034-ubiquitous-language.md)'s test — would a salesperson use this word unprompted?"*

**So nothing here names the concept in customer language**, and a consumer rendering it takes its wording from the ratified name when there is one.

## The store is two tables, and the split is what keeps it append-only

**Slice 3, migration `0042`.** **`action_batch` is the identity, written once and never touched again**; every lifecycle event afterwards is a row in **`action_batch_transition`**. A single table carrying `state`, `applied_at` and `reversal` would need `UPDATE` on all three — and **an approval that can be edited is an approval nobody can cite** (§2).

> ⚡ **The precedent is `opportunity_state`** (migration 0014), copied deliberately rather than re-invented: *"append-only, each row a **complete** statement of workflow state rather than a delta. The status **is** the audit log rather than something kept beside it, so the two cannot drift."*

**Neither table carries `UPDATE`, and no exception is argued.** `affiliation` in `0040` **is** an exception and argues itself at length — `ended_on` moves exactly once and nothing else is touched. **Nothing here has that shape**: every row is a fact about a moment, and a fact about a moment is never corrected in place. **Both are registered in `tenancy_policy.py`** — in `TENANT_OWNED_TABLES` *and* `IMMUTABLE_TENANT_TABLES` — which is what earns them the Security Invariants rather than a local test restating them.

**There is no `state` column and no `applied_at` column.** Both derive from the log (§2), and a stored copy is the one that eventually disagrees with the record an audit cites. **`reversible_for` *is* stored**, because it is *declared* at proposal; whether it has elapsed is still computed by `has_settled`.

### ⚠️ `actor_id` is nullable on the log, and slice 2's handoff said it never would be

**Both statements are right about different things, and the difference is worth keeping.** `Decision.actor_id` in the domain is non-nullable and always will be. **The log's `actor_id` is nullable for exactly one transition — `applied` —** because `applied_on` takes no actor: application is performed by the consuming domain **on the authority of the approval already recorded**, and inventing a second actor there would attribute the write to whoever happened to flush it.

⛔ **It is not a loosened rule; it is a constrained one.** A `CHECK` permits `NULL` **only** for `applied`, so the database refuses an unattributed approval — the same device `opportunity_state` uses for *"intelligence suggests; humans commit."*

### The current state is derived by replaying the log through the domain

**Reconstruction calls `approved_by` / `applied_on` / `reversed_by`**, never sets fields behind them. So **the domain's guards run on load**: a log that could not have been produced legally raises rather than yielding an aggregate that is quietly wrong. ⚡ **Replay is deterministic because no domain method reads a clock** — a reversal replays with the moment it was recorded at, so it is inside its window forever.

> ⚠️ **A defect the round-trip tests caught, recorded because it is not obvious.** The transition a decision represents is **not** simply the current state: **a reversal overwrites `state` with `REVERSED`**, so reading it off the state recorded an approval *as* a reversal — leaving a batch that replayed as something nobody ever approved. **It is still derived rather than stored**: only an approved batch can be applied and only an applied one reversed, so `applied_at` entails the approval.

## ⛔ What slices 1–3 deliberately do not contain

**No endpoint, no events, and no write path a consumer can reach.** The published reader is read-only because **a port that could write before the application layer exists would let a consumer commit to a lifecycle nobody has built.**

**Events are slice 4 and neither of the two is designed** — [P-C](../DOMAIN_DISCOVERY_REGISTER.md): *an event exists when a consumer appears.*

> ⚠️ **A test pinned slice 1's scope as *"the module has no layer but `public`"*, and every slice since has been chartered to break it.** **Re-aimed twice rather than deleted, and stronger each time**: it no longer counts directories at all. It asserts that **nothing here is reachable from outside the process and nothing here announces itself** — by reading the source for `OutboxEvent`, `publish(` and `event_bus`, which is where slice 4 will add them and where a directory check would never look.

## What the next assignee needs, and it is one paragraph

**Slice 4 is the application layer and the two events.** The port is already published at `application/ports.py` — **`add`, `record`, `get`, and deliberately no `update`** — and `SqlActionBatchRepository` implements it. **`record` appends whatever transition the aggregate most recently underwent, and derives its position from the aggregate's own history**, which is what makes it idempotent: re-recording the same aggregate writes the same `sequence` and collides with `uq_action_batch_transition_sequence` instead of storing the fact twice. ⛔ **Do not replace that with `max(sequence) + 1`** — it would silently duplicate.

**The domain refuses invalid transitions and the repository does not re-implement those checks** — a second copy of the lifecycle in SQL is the duplicated truth §2 forbids. **Persist the result of a transition; never decide one.**

## How to see it

**You cannot, and that is still true after slice 3.** The demonstration belongs to **slice 6 — one consumer end to end**, recommended as Companies bulk, *"because a contract proven by one real caller before six adopt it"* is the discipline [ADR-0403](adr/0403-signal-engine-reads-a-declaration.md) used. **A port with seven simultaneous first callers has no chance of being corrected cheaply.**

⚠️ **So this slice is not a completed product slice under §2** — it is infrastructure that has not reached a customer, and it is reported as such rather than as a demoable increment.

---

## Slice 5 · Applying asynchronously, and saying so while it runs *(TASK-465, 2026-08-10)*

🔴 **The row's risk is a sentence rather than a race**: ⛔ ***"a customer told **applied** before the work finishes."*** 📁 **The response to an apply request means *durably accepted*** ([§14](../../CLAUDE.md)), **and this slice is what makes the difference representable.**

### ⚡ The domain named this slice before it existed

📁 **`applied_at`'s own comment, written in slice 2**: *"`APPROVED` with no `applied_at` is a real state, not an inconsistency: approval and application are two moments, **and the gap between them is what slice 5 makes visible**."* ✅ **That is exactly what was built**, which is worth recording because it is the strongest evidence this module's documentation is load-bearing: **a slice arriving three rows later found its own specification already written down.**

### 🔴 Progress is DERIVED, and there is no fifth state

**Two transitions join the alphabet — `dispatched` and `application_failed` — and `ApplicationProgress` derives four answers from them.** ⛔ **Nothing is stored to say how far the work got**, for the reason this module already paid for once: 📁 *a reversal overwrote `state`, so reading the decision off it recorded an approval AS a reversal.*

| Progress | When | 📁 Why it is its own answer |
|---|---|---|
| `NOT_STARTED` | Approved, nothing asked to run | ⛔ Not the same as *failed* |
| `ACCEPTED` | `dispatched_at` set, no outcome | 🔴 **The row's risk in one word** — a screen saying *applied* here is the defect |
| `APPLIED` | `applied_at` set | The work finished |
| `FAILED` | a failure recorded | 📁 **[P-A](../DOMAIN_DISCOVERY_REGISTER.md)**, which [455](455-context-definitions-r02-r03.md) applies to this slice by name |

⚡ **`progress` reports failure AHEAD of acceptance, and that ordering is the P-A rule in code**: **a failed batch still carries its `dispatched_at`**, so testing acceptance first would report it as *accepted* and leave somebody waiting for work that has stopped.

### ⛔ A third event, in a file whose first line says two

📁 **The claim in `domain/events.py` is unchanged and still true**: *only `applied` and `reversed` change anything outside this module.* ⚡ **`action_batch.application_requested` is a WORK TRIGGER** — **nothing outside subscribes to it**, its only consumer is this module's own worker, and it exists because [§9](../../CLAUDE.md) forbids publishing directly to Redis. 📁 **`ai_research_engine` established the shape**; this follows it rather than inventing a second mechanism. **Catalogued in [06-events.md](06-events.md).**

⚠️ **The test asserting *two events* failed, and that is what made this a decision rather than a drift.** ✅ **It now asserts the closed set AND, separately, that there is still no `action_batch.approved`** — so the set cannot quietly absorb the refusal it was written for.

### ⚡ A worker is not an actor

⛔ **Three transitions are now unattributed** — `dispatched`, `applied`, `application_failed` — **on the authority of the approval already recorded.** **Naming the approver as the author of a background failure would put a false name in a history somebody may have to defend.**

⚠️ **`record`'s `actor_id` is a DIFFERENT question and stays one**: it writes the audit columns — *who wrote this row* — while the transition's own actor is derived by `_history`. **A person does press Apply, so the audit columns have a real answer**; the transition stays unattributed.

## ⚠️ Observations for whoever holds this module next

**Recorded because each cost time and none is a defect.**

**① A failure had to become a value, not a string.** ⚡ **The log is rebuilt by replaying the aggregate, so every entry needs the moment it happened** — a bare `reason` had none, and `_history` could not place it in order. ✅ **`ApplicationFailure(reason, at)`**, and the `reason` column is the one thing about a failure the aggregate cannot recompute.

**② `_replay` refused every NULL actor outside `applied`.** ⛔ **So a dispatched batch could not be read back at all.** ✅ **Caught by the round-trip tests slice 3 wrote for exactly this** — and it is the second time those tests have earned their keep.

**③ Amending a migration that has not left the branch is correct; alembic will not notice.** ⚠️ **`0048` was already stamped, so an edit to it never re-ran, and `downgrade` then failed trying to drop a column the earlier version never added.** ✅ **Recreating the lane database from base is the honest fix** — it also verifies what QE will do: **49 migrations apply cleanly and `0048` reverses and re-applies.** ⛔ **A `0049` adding a column to a table `0048` had just touched would have been noise**, and the immutability rule protects *shipped* migrations rather than unshipped ones.

**④ A status token inside a REFERENCE is not a status, and it has now produced two false positives.** ⚠️ **The [B-168](../BUGS.md) directional check flagged a row as losing a QE cell** because the replacement line *mentioned* `PROMOTED`; ⚠️ **a board classifier read `TASK-465` as `PROMOTED`** because its cell says *"TASK-464 is `PROMOTED`"*. ✅ **The reliable pattern is the FIRST backticked state token in the `Status` cell**, and ⛔ **either way the answer is verified directly before anything is removed** — both times the check was right to fire and wrong about which row.

### 🔴 [B-236](../BUGS.md) — the two events could never have been published

⚠️ **Found by the first code path that publishes through the real outbox**, which is this row's apply endpoint. ⛔ **`PublishableEvent` requires `event_type`, `event_version`, `causation_id` and `to_payload()`, and neither existing event declared any of them.**

🔴 **Why it was invisible is the useful half.** ⛔ **Every test of these events used a fake publisher** that records what it is handed and asks nothing of it. 📁 **This is [B-172](../BUGS.md)'s lesson one level up**: *"an import is not an execution"* becomes **a fake more permissive than the real port proves the caller compiles, not that it works.** ⚡ **The `# type: ignore[list-item]` on `_publish` was the visible tell**, and its comment named a real constraint while hiding a simpler one: the fields were absent entirely.

✅ **All three events now declare what the protocol asks for**, and the regression is the API test that found it — **it publishes through the real outbox and reads the row back**, so a future unpublishable event fails there rather than in production.

### ⚡ The HTTP surface, and the guard that has now moved twice

📁 **Two endpoints**: `POST …/action-batches/{id}/apply` → **`202`**, and `GET …/action-batches/{id}` → progress. 🔴 **The status code IS the contract** — ⛔ **`200` would say the work is done.**

⚠️ **`test_public_contract.py`'s HTTP-surface guard has been re-aimed twice in two increments, and each time the comment says why.** ⛔ **It began as *the module has no `interface/` directory***, a cheap proxy while the layer was empty; **a worker handler lives in `interface/` too**, so the proxy stopped meaning what it said. ⛔ **Then *no `router.py`*, which this row's own Definition of Done was always going to break.** ✅ **It now asserts the SHAPE of the edge — two transports and no more** — **which is a constraint that survives the next slice**, because a third transport is an architectural decision rather than something a slice adds quietly.

### ⏸️ What remains, named rather than implied

⛔ **`fail_application` has no caller.** ✅ **Slice 6 is it**: the consuming domain performs the work, so it is what discovers the work could not be done and records why. ⚠️ **Until then a batch whose application genuinely fails cannot be told so** — 📁 the progress model supports it and nothing produces it.

⛔ **There is still no propose or approve endpoint.** ⚡ **The apply endpoint assumes an approved batch exists**, and slice 6's consumer is what creates one through a customer-facing path.

---

## TASK-1419 slice ⓐ — a batch that may never take effect, and a guard I removed for failing to be one

**Workflow 26's design subtitle is the whole workflow**: 📁 *"Simulated before it runs, approved before it writes, reversible after it does."* ⚡ **The second and third clauses were already this module.** **The first was not, and it is lifecycle rather than semantics — which is why it belongs here.**

### 🔴 A simulation is not a batch that happens to be unapproved

⛔ **The tempting model is *propose it, look at it, and never approve it*.** ⚠️ **That is a promise, not a guarantee**: the batch is one ordinary call away from being effective for its whole life. 🔴 **Anything that approves batches in bulk — a retry, an operator script, a future bulk-approval screen — would apply it**, and the customer was shown a preview.

✅ **So `Effect` is a property fixed at proposal.** ⛔ **There is no method that turns a `DRY_RUN` into a `LIVE` batch, and a test asserts that absence** — because a helpfully-added `promote()` would make every refusal a speed bump and would look like a feature.

### 🔴 The guard that matters is `__post_init__`, not the methods

⚠️ **A repository reconstructs a batch by CONSTRUCTING it, not by replaying transitions.** ⛔ **A refusal that lived only in the transition methods would be bypassed on every read** — which is how a forbidden state reaches a system that checks for it in all the obvious places.

✅ **Every method returns a new batch through `replace`, so construction re-runs on every transition.** ⚡ **That is what makes the invariant hold on paths nobody enumerated.**

### ⛔ And one guard was removed for being unable to fail

🔴 **A dry-run refusal was written into `dispatched_on` and deleted after fire-testing it.** ⚡ **A dry run can never be `APPROVED`, and `dispatched_on` already refuses anything that is not approved — so the branch was unreachable.**

📁 **[§2](../../CLAUDE.md): *a guard that cannot fail is not protection — it is documentation pretending to be code*.** ⚠️ **It would have been decorative logic in the one slice whose entire subject is guards**, and it survived until the fire test because removing it left every test green.

> ✅ **The protection is real and comes from two places that ARE reachable: `approved_by` refuses, and `__post_init__` refuses.** **The test asserts the CHAIN — dispatch requires approval, approval is refused — rather than a message from a branch that cannot run.**

### ⚠️ The first version of the tests could not tell the two guards apart

🔴 **Both refusals said *"cannot be approved"*, so removing the method's call left every test GREEN.** ✅ **The two messages are now deliberately distinct** — **the method names the VERB, the constructor names the STATE** — **and each test pins the guard it is about.**

⚡ **Both are needed and they answer different questions**: *"a dry run cannot be approved"* tells somebody what they did; *"constructed in a state only a live batch can reach"* tells a repository author what they built.

### ✅ Additive by construction

⚡ **`effect` defaults to `LIVE` and `ProposeBatch.dry_run` defaults to `False`.** ⛔ **Every existing caller — including [TASK-466](../BACKLOG.md)'s shipped Companies-bulk consumer — keeps proposing live batches without knowing the field exists.** **A test asserts the default, so the additive property is checked rather than assumed.**

### ⚠️ What slice ⓐ does NOT do

⛔ **It does not persist `effect`** — the column, the repository and the endpoint are slice ⓑ. ⛔ **It does not know what a simulation would DO**: 📁 *"nothing here knows what an action means"* is unchanged, and **the description of the would-be work belongs to the consuming domain exactly as the payload always has.** ⛔ **And it builds no surface** — 📁 [TASK-1416](../BACKLOG.md) is the simulation-results dependency and is still blocked on a report rendering one real figure.

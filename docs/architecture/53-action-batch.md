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

## ⛔ What slices 1–2 deliberately do not contain

**No table, no endpoint, no events, and no write path.** The reader is read-only because **a port that could write before the application layer exists would let a consumer commit to a lifecycle nobody has built.**

**Persistence is slice 3** — append-only, **no `UPDATE` grant**, `ENABLE` *and* `FORCE ROW LEVEL SECURITY` in the creating migration, and classification in `tenancy_policy.py` in the same change (§8). ⚡ **The standard to match is [TASK-427](../BACKLOG.md)**, whose Closeout called it *"a new bounded context that brought its own guarantees"* — both tables forced, separate `SELECT`/`INSERT`/`DELETE` policies, and the one `UPDATE` policy carrying **both** `USING` and `WITH CHECK`, *"without the second, a row could be updated out of its own workspace."*

**Events are slice 4 and neither of the two is designed** — [P-C](../DOMAIN_DISCOVERY_REGISTER.md): *an event exists when a consumer appears.*

> ⚠️ **A test pinned slice 1's scope as *"the module has no layer but `public`"*, and slice 2 is chartered to break it.** **Re-aimed rather than deleted, and strictly stronger**: it now asserts the context has **no `infrastructure`, `interface` or `application`** — which is what slices 3 and 4 add and what a lane could otherwise smuggle in early. **Counting the layers to one asserted that only by accident.**

## What the next assignee needs, and it is one paragraph

**Slice 3 persists this aggregate and nothing more.** `ActionBatch` is the shape to store: five states, two `Decision` records (`decided`, `reversal`), `applied_at`, and `reversible_for`. ⛔ **Do not add an `is_settled` column** — that is the one thing this context has said no to twice, in the ADR and in the code. **`Decision` is a value object, not a table**; whether it becomes two columns or an embedded type is slice 3's call, but **`actor_id` is never nullable**.

**The domain refuses invalid transitions and the repository must not re-implement those checks** — a second copy of the lifecycle in SQL is the duplicated truth §2 forbids. **Persist the result of a transition; never decide one.**

## How to see it

**You cannot, and that is still true after slice 2.** The demonstration belongs to **slice 6 — one consumer end to end**, recommended as Companies bulk, *"because a contract proven by one real caller before six adopt it"* is the discipline [ADR-0403](adr/0403-signal-engine-reads-a-declaration.md) used. **A port with seven simultaneous first callers has no chance of being corrected cheaply.**

⚠️ **So this slice is not a completed product slice under §2** — it is infrastructure that has not reached a customer, and it is reported as such rather than as a demoable increment.

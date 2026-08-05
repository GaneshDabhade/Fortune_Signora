# 435 · Platform composition — the RFC

**TASK-900.** Lane C, 2026-08-05. **For product owner approval.**

> **What this is.** §20a freezes `signora_platform/` and admits changes only through an approved RFC. **Four capabilities have accumulated behind that freeze**, each raised by a lane that stopped rather than working around it. This proposes all four, together, because **they are one question asked four times: how does a module's code participate in the runtime the platform composes?**
>
> **What this is not.** **No module is rewired here and no production code is written by this office.** The RFC lands, the product owner approves, and an implementation lane builds — which is [TASK-901](../BACKLOG.md), **seven independently certifiable slices, one per pipeline module.**

## Why one RFC and not four

**Because deciding them separately is how the substrate drifts.** [C-021](../LANE_COORDINATION.md) is the worked example: ruled alone, it would add an enqueue path to satisfy one handler, and the next handler would add another.

> **All four touch the same surface, and three of the four are answered by the *same* change.** Capability 1 gives a handler a session; **once it has one, capability 3 stops needing a new enqueue path at all.** That is only visible if they are read together.

**Each capability below states: what was measured · what is proposed · why it is safe · what it deliberately does not do · how approval is verified.**

---

# Capability 1 · A handler runs inside the dispatcher's transaction

**Closes [C-012](../LANE_COORDINATION.md).** Raised by the product owner's own RFC requirement; **surviving since M3A.**

## Measured

| At `54c2e70` | |
|---|---|
| `EventHandler` | `Callable[[EventEnvelope], Awaitable[None]]` — [`subscriptions.py:20`](../../backend/signora_platform/event_bus/subscriptions.py#L20) |
| The dispatcher opens a session | [`dispatch.py:96`](../../backend/signora_platform/event_bus/dispatch.py#L96), tenant-scoped |
| It claims idempotency **in that session** | `dispatch.py:101` |
| It calls the handler | `dispatch.py:116` — **`await subscription.handler(envelope)`, and the session is not passed** |
| Subscriptions the deployed worker registers | **10** — `ai_research.requested`, plus **9** Timeline projections read from `PROJECTIONS` |
| **Distinct handler functions behind them** | **2** — `_run_requested_research` · `_project_to_timeline` |
| Event types module code publishes | **23** |

> ⚠️ **[C-012](../LANE_COORDINATION.md) records *"1 subscription"*, measured at `c62760b`. It is 10 now** — Timeline's projection handler landed since, closing [B-301](../BUGS.md). **Re-measured rather than quoted**, because the count is what capability 1's recommendation rests on and a three-day-old number is not evidence about today.

**So a handler must open its own session, in a second transaction.** The module's own docstring promises *"handler work and the idempotency record share one transaction, so a crash can never leave one without the other"* — **and no handler can keep that promise today.**

> **This is why the deployed worker consumes nothing while every gate is green.** The pipeline is exercised end to end through its real handlers in the integration suite, which composes them directly. **The tests pass through a path production does not use.**

## Proposed

**`EventHandler` takes the dispatcher's session, keyword-only:**

```python
EventHandler = Callable[[EventEnvelope, AsyncSession], Awaitable[None]]
```

and `dispatch.py:116` becomes `await subscription.handler(envelope, session)`.

## Why one shape rather than two

**The backlog row says *"additive only — a module not using one behaves identically."* This capability is the one place that instruction is worth arguing with, and the argument is arithmetic.**

**The additive form would be a second handler type registered through a second method**, with the dispatcher branching on which the `Subscription` carries. It breaks nothing. **It also means two ways to write a handler, forever, and the wrong one keeps working** — so the wrong one keeps being written.

> **The measured blast radius of the single shape is two functions.** **Ten subscriptions are registered and they run two handlers** — `_run_requested_research` and `_project_to_timeline`. **Migrating two functions is smaller than the branch that would avoid migrating them**, and it leaves the repository with **one way to write a handler** rather than one right way and one that silently loses transactionality.
>
> **And `_project_to_timeline` is the argument in miniature — not because it is broken, but because of what it had to do not to be.** Its own docstring names the cost: *"**Idempotent without the dispatcher's ledger.** The entry id is derived from `event_id`… **That is what lets this consumer exist while C-012 is still open**: it needs no share of the dispatcher's transaction, because it cannot write twice."*
>
> **That is a correct handler, and it is correct by design constraint rather than by the platform's guarantee.** **The escape only exists for writes that can be made naturally idempotent.** A handler that must do something a second time differently — increment, append, call a provider — **has no such escape, and that is the whole of TASK-901's seven slices.** **One of two handlers had to be shaped around a missing capability; the seven that follow cannot all be.**

*(Recorded because I first wrote that this handler could lose a projection on a crash. **It cannot** — the dispatcher's claim is uncommitted while the handler runs, so a raise rolls it back and the event redelivers. **The code's own docstring says so and I asserted before reading it**, which is the defect I spent today correcting in four other places.)*

**Recommendation: the single shape.** **This is the only capability here that is not strictly additive, and it is flagged as such rather than described as free.**

## What it does not do

**It does not make the handler's session the handler's to commit.** The dispatcher owns the transaction boundary; a handler that commits or rolls back is a defect the same as one that swallows an exception. **It does not change tenancy** — the session arrives already scoped, and that is the point.

## Verified by

**A test asserting that a handler's write and the idempotency row are lost together when the handler raises.** Today that test cannot be written; **its existence is the acceptance criterion.**

---

# Capability 2 · `PublishableEvent` is satisfiable by a frozen dataclass

**Closes [C-013](../LANE_COORDINATION.md).** **Cosmetic today, and it is the cheapest of the four.**

## Measured

**The Protocol declares mutable attributes** — [`publisher.py:26–31`](../../backend/signora_platform/event_bus/publisher.py#L26):

```python
event_type: str
event_version: int
...
```

**A mutable attribute member requires a settable attribute.** A frozen dataclass field is read-only, so it does not conform, so **eight publish sites carry `# type: ignore[arg-type]`.** *(Measured: 8.)*

> **The cost is not the eight.** It is that **eight identical suppressions train the ninth**, and a suppression at a publish site is the one place a real type error would look identical.

## Proposed

**Declare the members read-only:**

```python
@property
def event_type(self) -> str: ...
```

## Why it is safe

**It widens what conforms and narrows nothing.** A mutable attribute satisfies a read-only property; the reverse is what fails today. **And nothing in the platform assigns to these fields** — `PostgresOutboxEventPublisher` reads all six and writes none *(verified: no assignment to any of the six anywhere in `signora_platform/`)*.

**🟢 by the change budget.** The eight suppressions are deleted in the same slice, **and deleting them is how the change is proven** — if one is still needed, the fix was wrong.

---

# Capability 3 · A handler reaches a provider adapter

**Closes [C-021](../LANE_COORDINATION.md).** **Raised as an architectural blocker; the RFC finds it is two problems and proposes to solve one and dissolve the other.**

## Measured

| | |
|---|---|
| `RunProviderSync` needs a `ProviderAdapter` | supplied from `ctx["provider_registry"]` in the **ARQ task** context |
| An event handler receives a `WorkerRuntime` | `session_factory` · `http` · `ai` — [`apps/worker/subscriptions.py:98`](../../backend/apps/worker/subscriptions.py#L98). **No provider registry** |
| A module cannot enqueue ARQ work | `event_bus/queue.py` is the relay's, driven from the outbox, **frozen** |

**Everything a lane may build is built** — delta rule, version ordering, state table, repository, use case, handler, 17 unit tests.

## Proposed — and the smaller half is the whole of it

**① `WorkerRuntime` gains a `providers` field**, built at the worker's composition root exactly as the API's registry already is.

> ⚠️ **This is not a platform change.** `WorkerRuntime` lives in **`apps/worker/`, which §20a does not freeze.** **C-021 has been carried as a platform blocker for three days and the field it needs is in a file no freeze covers.** What `apps/worker/` actually lacks is an **assignable owner** ([C-010](../LANE_COORDINATION.md)) — an ownership gap wearing an architecture gap's clothes.

**② The enqueue half is dissolved rather than solved.** **With capability 1, the handler already holds a tenant-scoped session inside its own worker pool** — which is what pools exist for: *"a slow, expensive stage runs at low concurrency without starving a fast one."*

> **So the handler performs the sync where it stands. No new enqueue path is added, `queue.py` stays the relay's, and the frozen surface is untouched.** **The capability C-021 asked for turns out not to be needed once capability 1 exists**, which is the argument for reading the four together.

## What it does not do

**It does not let a module reach ARQ.** That direction stays closed, deliberately — **the outbox remains the only way work is scheduled**, and a module that could enqueue directly would have bypassed the transactional guarantee the outbox exists to provide.

---

# Capability 4 · A self-directed action

**Closes [C-207](../LANE_COORDINATION.md).** **Blocks leaving an organization, and every self-directed operation the product will ever have.**

## Measured

**`model.conf` defines `r = sub, dom, obj, act`, and `sub` is the caller's *role*, deliberately not their identity** — because membership lives in PostgreSQL under RLS and mirroring it into Casbin would let two sources of truth drift. **That reasoning is correct and this RFC does not touch it.**

> **So the model can say *"an owner may remove a member"* and cannot say *"anybody may remove themselves."***

**The three obvious repairs are each worse than the block**, and C-207 says why: a policy `p, member, *, member, remove` would **assert that members may remove members, which is false** — a false statement in the file an auditor reads first.

## Proposed

**Leaving is a different action, not a self-directed `remove`:**

```
Action.LEAVE = "leave"          # enforcer.py — the one frozen line
p, member, *, member, leave     # policy
p, owner,  *, member, leave
```

## Why this is the right shape

> **Identity never enters the tuple, because it never needed to.** **The scoping to *self* is a property of the endpoint, not of the policy**: leaving takes no target, so there is no other membership it could act on. **Casbin answers *"may this role leave?"* — which is a true, complete question — and the handler's resource resolution does the rest.**

**Every statement the policy file makes stays true.** `member, member, remove` is never granted. **No model change, no request-tuple change, no second source of truth**, and `Action` gains one member — which is why this needs the RFC at all.

⚠️ **One product question inside it, and it is genuinely yours:** **may a sole owner leave?** The policy above says yes and would strand a workspace with no owner. **Recommendation: the policy permits it and the handler refuses the last owner**, because *"an owner may leave"* is a true authorization statement and *"a workspace must keep an owner"* is an invariant of the workspace, not of the caller's role. **Encoding it in Casbin would put a workspace invariant in the authorization model**, where it would be invisible to anyone reading the workspace.

---

# What approval releases

| | |
|---|---|
| **Coordination items closed** | **[C-012](../LANE_COORDINATION.md) · [C-013](../LANE_COORDINATION.md) · [C-021](../LANE_COORDINATION.md) · [C-207](../LANE_COORDINATION.md)** — four rulings retired by one approval |
| **Tasks unblocked** | **[TASK-901](../BACKLOG.md) — seven independently certifiable slices**, one per pipeline module |
| **And beyond the queue** | **The deployed worker starts consuming.** 23 event types are published and **1 subscription is registered**; capability 1 is what makes the other stages registrable |

**Change budget, per capability:** **① 🟠** — one frozen signature, one call site, one migration · **② 🟢** · **③ 🟢**, and it is in `apps/worker/`, not the platform · **④ 🟠** — one enum member and two policy lines.

> **Three of four are small. The RFC is required because they are in `signora_platform/`, not because they are large** — and that is the correct reason for a freeze to exist.

# Rejected

| | Why |
|---|---|
| **Two handler shapes** (capability 1, additive) | **Two ways to write a handler forever, and the wrong one keeps working.** Blast radius of the single shape is **one** call site |
| **A new enqueue path for handlers** (capability 3) | **Unnecessary once capability 1 lands**, and it would put a second scheduling route beside the outbox |
| **Identity in the Casbin tuple** (capability 4) | **Duplicates a source of truth `model.conf` deliberately refuses to duplicate.** The comment explaining why is older than the problem |
| **`p, member, *, member, remove`** (capability 4) | **Asserts something false**, in the file an auditor reads first |
| **Deciding these separately** | **How the substrate drifts.** C-021 dissolves only when read next to C-012 |

# The decision asked of the product owner

**① Approve the four capabilities, or any subset — they are separable and ③ needs nothing from you but an owner for `apps/worker/`.**
**② Confirm the single-shape handler in capability 1**, which is the one deviation from *additive only* in the task row.
**③ Rule the sole-owner question in capability 4.**

**On approval this becomes an ADR and [TASK-901](../BACKLOG.md) becomes claimable.** **No module is rewired by this document.**

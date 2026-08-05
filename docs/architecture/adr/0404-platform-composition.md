# ADR-0404: A module's code participates in the runtime the platform composes

## Status

**RATIFIED — 2026-08-05, by the product owner.** Drafted by Lane C as [435 · Platform composition](../435-platform-composition-rfc.md), under [TASK-900](../../BACKLOG.md). **§20a admits changes to `signora_platform/` only through an approved RFC; this is that approval.**

**Nothing is implemented here.** The RFC lands, this records the ruling, and **an implementation lane rewires** — which is [TASK-901](../../BACKLOG.md), **seven independently certifiable slices, one per pipeline module.**

> **Four coordination items close on this one ADR:** **[C-012](../../LANE_COORDINATION.md)** · **[C-013](../../LANE_COORDINATION.md)** · **[C-021](../../LANE_COORDINATION.md)** · **[C-207](../../LANE_COORDINATION.md)**.

## Context

**Four capabilities accumulated behind the platform freeze**, each raised by a lane that stopped rather than worked around it. **They are one question asked four times: how does a module's code participate in the runtime the platform composes?**

**Deciding them separately is how the substrate drifts** — and reading them together dissolved one of the four outright.

## Decision

### 1 · A handler runs inside the dispatcher's transaction — closes C-012

`EventHandler` becomes `Callable[[EventEnvelope, AsyncSession], Awaitable[None]]`, and `dispatch.py` passes the session it already holds.

**Measured:** the dispatcher opens a tenant-scoped session, claims idempotency **in it**, and then calls the handler with only the envelope. The module's own docstring promises *"handler work and the idempotency record share one transaction"* — **and no handler could keep that promise.**

> ✅ **Single shape, ratified.** *"We should not support two implementation patterns permanently."* **The blast radius is two functions** — ten subscriptions run `_run_requested_research` and `_project_to_timeline`. **Migrating two is smaller than the branch that would avoid migrating them.**

**The dispatcher keeps the transaction boundary.** A handler that commits or rolls back is a defect, the same as one that swallows an exception.

### 2 · `PublishableEvent` is satisfiable by a frozen dataclass — closes C-013

Its members become read-only properties.

**A mutable attribute member requires a settable attribute; a frozen dataclass field is read-only.** Eight publish sites carry `# type: ignore[arg-type]` because of it. **The change widens what conforms and narrows nothing** — verified: **nothing in `signora_platform/` assigns to any of the six.**

**The eight suppressions are deleted in the same slice, and deleting them is how the change is proven.**

### 3 · A handler reaches a provider adapter — closes C-021

**`WorkerRuntime` gains a provider-registry field**, populated at the worker's composition root.

> ⚠️ **Correction, 2026-08-05, before a line was written.** This ADR said *"built at the worker's composition root **exactly as the API's registry already is**"* — **and no composition root builds a `ProviderRegistry` anywhere.** The registry I was comparing it to is `ai_platform`'s **AI** provider registry, which is a different thing with a similar name. **`SimulatedProviderAdapter` is constructed only in tests, and `provider_platform` has no `Settings` object at all.**
>
> **So capability 3 is larger than one field and it is cross-lane.** A typed `Settings` choosing which adapters exist belongs to **the module that owns the behaviour** (§10) — that is `provider_platform`, **Lane A's**. Only the `WorkerRuntime` field is `apps/`, which is Lane C's.
>
> **The decision stands; the sizing was wrong.** [TASK-419](../../BACKLOG.md) carries the correction, and **the two halves are sequenced rather than bundled** — a `WorkerRuntime` field pointing at a registry nothing populates would be the decorative class §2 forbids.

> ⚠️ **This was never a platform change.** `WorkerRuntime` lives in **`apps/worker/`, which §20a does not freeze** — its own text says adding a subscription or a pool is *a use of the platform, not a change to it*. **C-021 was an ownership gap ([C-010](../../LANE_COORDINATION.md)) wearing an architecture gap's clothes**, and C-010 is now ruled: **`apps/` is a first-class assignable module.**

**And the enqueue half dissolves.** With capability 1 the handler already holds a tenant-scoped session inside its own worker pool — **so it performs the sync where it stands.** **No new enqueue path; `queue.py` stays the relay's; the frozen surface is untouched.**

> **A module still may not reach ARQ.** The outbox remains the only way work is scheduled.

### 4 · A self-directed action — closes C-207

**`Action.LEAVE`, and two policy lines:**

```
p, member, *, member, leave
p, owner,  *, member, leave
```

**Identity never enters the request tuple, because it never needed to.** `model.conf` keeps `sub` as the caller's *role* — membership lives in PostgreSQL under RLS, and mirroring it into Casbin would let two sources of truth drift. **The scoping to *self* is a property of the endpoint: leaving takes no target.**

**Every statement the policy file makes stays true.** `member, member, remove` is never granted — the repair that would have asserted something false.

> ✅ **The sole-owner question, ruled:** ***"An owner may leave. A workspace may never become ownerless. Enforce the invariant in the application layer rather than the authorization engine."***
>
> **A workspace invariant does not belong in the authorization model**, where it would be invisible to anyone reading the workspace.

## Consequences

**[TASK-901](../../BACKLOG.md) becomes claimable — seven independently certifiable slices.** **The deployed worker starts consuming**: 23 event types are published and 10 subscriptions run 2 handlers; capability 1 is what makes the rest registrable.

**Change budget:** ① 🟠 · ② 🟢 · ③ 🟢 *(and in `apps/`, not the platform)* · ④ 🟠.

> **The RFC was required because these are in `signora_platform/`, not because they are large.** **That is the correct reason for a freeze to exist.**

## Validation — to be run by the implementing lane, before the first slice

**①** `EventHandler`'s two call sites are the only ones — `grep -rn "subscribe(" apps/worker/`.
**②** No assignment to any `PublishableEvent` member anywhere in `signora_platform/`; **all eight `# type: ignore[arg-type]` at publish sites are removable.**
**③** `apps/worker/` is outside every §20a-frozen path, and `modules.toml` names its owner.
**④** `Action` gains exactly one member; **`policy.csv` grants no `member, member, remove`.**

> ⚠️ **Correction, 2026-08-05, from running these four.** **② failed, and it failed twice.**
>
> **The count is wrong: there are *five* `# type: ignore[arg-type]` at publish sites, not eight** — `observation_engine/application/record.py:124` · `signal_engine/application/generate.py:158` · `business_event_engine/application/detect.py:129` · `knowledge_graph/application/resolve.py:329` · `knowledge_graph/application/relationships.py:240`. **The other three are `provider_normalization` (×2) and `ai_research_engine`, and none is at a publish site.**
>
> **And the ownership question was never asked.** **③ checks that `apps/worker/` has an owner; nothing checks that the *modules* a capability reaches have one.** **All five files are in `backend/modules/`, which Lane C — this ADR's author and `signora_platform/`'s owner — may never touch**, and `mypy strict`'s `warn_unused_ignores` makes the platform change and the five deletions one atomic commit. **[C-417](../../LANE_COORDINATION.md) carries the ruling; capabilities ① and ② wait on it. ④ shipped.**
>
> **A future §Validation should ask which trees a capability's proof lives in, and who owns each.**

**Any validation that fails is a `C-` item, not an improvisation** — the rule [ADR-0403](0403-signal-engine-reads-a-declaration.md) established and the reason two of its five corrected its own first draft.

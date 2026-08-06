# ADR-0405: An action is approved before it is effective, and reversible after

## Status

**PRODUCT OWNER APPROVED — 2026-08-06, [D-126](../../DECISION_REGISTER.md), option (b).** Drafted by Lane C — Product Office, **after** the shape ruling and not before it.

> ⚠️ **[455](../455-context-definitions-r02-r03.md) said in its seventh line *"no ADR drafted — R-03's still waits on [TASK-431](../../BACKLOG.md)'s shape ruling"*, and this office nearly drafted one anyway.** **[443](../443-account-matching-capability.md) and [451](../451-workflow-automation-traceability-audit.md) both recorded that an ADR written ahead of a ruling gets its sizing wrong. The ruling now exists.**

**A new bounded context is 🔴 under `CLAUDE.md` §6 and needs an ADR. This is that ADR.**

---

## Context

**Six approved screens assert one guarantee in six different vocabularies** ([442 §F1](../442-product-led-domain-discovery.md)):

> *"Approved before it writes, reversible after it does."* · *"Nothing sends without your approval, reversible for 24 hours."*

⚡ **The finding that makes this one capability rather than six features: the AI contract and the bulk-edit contract are the same contract.** **Screen by screen that is invisible** — one reads as AI governance, the other as a table feature. **Read together they are one lifecycle with one set of verbs.**

### More than half is already built, and it is not built here

| | |
|---|---|
| **A machine proposes and does not commit** | **`MACHINE_AUTHORED = frozenset({Stage.TRACKING})`** — *"Intelligence suggests. Humans commit."* |
| **A proposal exists as a type** | `Recommendation` |
| **Attribution** | **`actor_id` in 37 files**, and `opportunity_state` is *"append-only, attributed, reasoned"* |
| **Reversal-window precedent** | ⚡ **`Snoozed.until` — a window evaluated at read time and materialised nowhere** ([P-B](../../DOMAIN_DISCOVERY_REGISTER.md)) |

**Genuinely absent: a named unit of change · a window · and the verbs.** **`Action` is `read · update · add · remove` — there is no `approve` and no `withdraw`, so the guarantee six screens promise cannot be expressed.**

---

## Decision

> ## **R-03 is a first-class domain capability in a single owning bounded context, exposed through a stable `public/` contract.**

⛔ **Not a per-screen implementation · not a per-module implementation · not a platform utility.**

**Its responsibility is to manage the lifecycle of an action that requires explicit approval before becoming effective and remains reversible for a defined window.**

### 1 · The responsibility boundary, and it is the load-bearing part

| **The Action context owns** | **The consuming domain owns** |
|---|---|
| The **`Action`** as the canonical unit of work · **approval** · **withdrawal** · approval **state** · **lifecycle** · approval **metadata** · the **reversible window** · execution **metadata** · **the public contract** | **Interpreting** the action · **performing** the business operation · **validating** business rules · **executing** the change · **implementing the inverse** where reversal is supported |

> ## **The Action context coordinates lifecycle. Business domains own business behaviour.**

⛔ **It is *not* responsible for business semantics**, and that sentence is the whole boundary. ⚡ **It is [ADR-0402](0402-a-rule-is-data.md)'s shape reused**: a rule is data, evaluated centrally, **and the module that owns an operation is the only thing that knows how to perform or undo it.**

### 2 · The window is a predicate, never a stored state

**`settled` is `now() >= applied_at + window`** — **computed at read time, materialised nowhere, scheduled by nothing.**

⚡ **The precedent is `Snoozed.until` in `signal_engine`**, and [447](../447-signal-center-traceability-audit.md) named it *"the pattern [R-03](../../DOMAIN_DISCOVERY_REGISTER.md) should copy."* ⛔ **A stored `is_settled` column is two representations of one fact** (§2) **and a scheduler to flip it is the machinery [P-B](../../DOMAIN_DISCOVERY_REGISTER.md) exists to refuse.**

### 3 · The record is append-only

**No `UPDATE` grant. Supersession is the pattern.** ⚡ **An approval that can be edited is an approval nobody can cite** — §2, *immutability is the default for anything that records a fact* — **and an approval record is exactly a record of what somebody decided at a moment.**

### 4 · Consumers reach it only through `public/`

⛔ **No consuming module reaches an implementation detail, and no consuming module duplicates approval behaviour.**

> **Any future workflow requiring approval, deferred execution, reversible execution, withdrawal, human confirmation or staged execution must first evaluate whether it should *consume* this capability before introducing another approval model.**
>
> **The repository converges on one approval lifecycle unless a future requirement proves it insufficient.**

⚡ **This is the reuse gate stated as architecture rather than as review practice**, and it is why the capability is worth a context: **six screens each inventing an approval model is six lifecycles a customer must learn separately.**

### 5 · What this ADR deliberately does not decide

| | |
|---|---|
| ⬜ **The context's name** | **Not settled here.** ⛔ **A name is [ADR-0034](0034-ubiquitous-language.md)'s test — *would a salesperson use this word unprompted?* — and it is worth one deliberate pass rather than a placeholder that ships** |
| ⬜ **Its owning lane** | 🔴 **Module ownership is never Lane C's** (§20e). **Recommended below with evidence; confirming it is the product owner's** |
| ⛔ **Events** | **Two are named in [455 §5](../455-context-definitions-r02-r03.md) slice 4 and neither is designed here.** **[P-C](../../DOMAIN_DISCOVERY_REGISTER.md): an event exists when a consumer appears** |

---

## Alternatives

| | | |
|---|---|---|
| **(a)** | **Per-screen implementation** | ⛔ **Six approval models. The customer learns each one, and no two agree about what *approved* means** |
| **(b)** | ✅ **One owning context, consumed through `public/`** | **Ruled.** §6: *a port belongs to the module that owns the language it represents* |
| **(c)** | **A platform utility in `signora_platform/`** | ⛔ **Refused.** §2: *the platform composes modules; it never becomes the owner of their internals* — **and approval carries domain vocabulary, which is precisely what the substrate must not accumulate** |
| **(d)** | **Extend an existing module** | ⛔ **No existing module owns *approval as a concept*.** `signal_engine` owns a *resolution*; `opportunity_engine` owns a *transition*. **Both are decisions about their own subject, not a general lifecycle** |

---

## Consequences

✅ **Five screens stop waiting on a capability nobody was building** — Companies, Opportunity Intelligence, Workflow Automation, AI Copilot, AI Research.
✅ **`Action` gains `approve` and `withdraw`**, and the guarantee six screens print becomes expressible.
⚠️ **A new bounded context is 🔴 and carries the obligations §11 attaches**: **its tables classified in `tenancy_policy.py` in the creating migration, RLS enabled *and* forced, and a Security Invariant proving enforcement.** ⚡ **[TASK-427](../../BACKLOG.md) is the standard to match — QE's Closeout called it *"a new bounded context that brought its own guarantees"*, 389 → 392 invariants.**
⛔ **One import contract is added, not widened**: consumers reach `public/` only, and `lint-imports` proves the coupling never forms.

---

## Validation

**Run before the first slice, and each is checkable rather than asserted:**

**① `settled` appears in no column, no migration and no scheduler** · **② the context has no `UPDATE` grant** · **③ no consuming module imports below `public/`** · **④ `Action` has `approve` and `withdraw`** · **⑤ no second approval model exists anywhere in `backend/modules/`** — ⚡ **the reuse gate, executable as a grep.**

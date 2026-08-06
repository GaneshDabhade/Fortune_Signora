# 53 — Action Batch (module design)

> Status: **Slice 1 of six — the `public/` contract, and nothing else.** Lane B, 2026-08-06.
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

## Five states, and two pairs that must not merge

**`WITHDRAWN` and `REJECTED` are different facts** — the proposer changing their mind, and a reviewer declining. A customer reading a history needs to tell them apart.

**`APPROVED` does not imply applied.** Approval and application are two moments, and `APPROVED` with a null `applied_at` is a real state rather than an inconsistency — slice 5 is what makes the gap between them visible.

> ⚠️ **One test was written as `WITHDRAWN is not REJECTED` and `mypy --strict` refused it** — a non-overlapping identity check, a tautology the type system sees through. **The real assertion is that the enum carries both**, which is what a later collapse into one value would break. Recorded because the first form looked like a test and asserted nothing.

## A count, never the items

`ActionBatchView` publishes `item_count`. **What each item *means* belongs to the domain that proposed it**, and publishing the items here would put business semantics in the context whose entire boundary is that it holds none. **Asserted, not merely intended.**

## ⚠️ `action_batch` is the context's identity, not the product's word

**No customer-facing name is ratified.** [D-127](../DECISION_REGISTER.md) forbids a placeholder becoming production terminology because implementation started first, and ADR-0405 leaves it open deliberately: *"a name is [ADR-0034](adr/0034-ubiquitous-language.md)'s test — would a salesperson use this word unprompted?"*

**So nothing here names the concept in customer language**, and a consumer rendering it takes its wording from the ratified name when there is one.

## ⛔ What slice 1 deliberately does not contain

**No domain, no table, no endpoint, no events, and no write path.** The reader is read-only because **a port that could write before the domain exists would let a consumer commit to a lifecycle nobody has built.**

**Events are slice 4 and neither of the two is designed** — [P-C](../DOMAIN_DISCOVERY_REGISTER.md): *an event exists when a consumer appears.*

## How to see it

**You cannot, and that is what slice 1 is.** The demonstration belongs to **slice 6 — one consumer end to end**, recommended as Companies bulk, *"because a contract proven by one real caller before six adopt it"* is the discipline [ADR-0403](adr/0403-signal-engine-reads-a-declaration.md) used. **A port with seven simultaneous first callers has no chance of being corrected cheaply.**

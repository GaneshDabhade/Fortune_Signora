# 429 — Distributed Product Development: the delivery model

> **Lane C — Product Office, 2026-08-04.** **PRODUCT OWNER DIRECTIVE — recorded, not proposed.** Drafted by Lane C on the product owner's instruction, which is the only route by which `CLAUDE.md` is amended (§20e, *shared files have one owner*).
>
> **This document records the model and its mechanics.** The binding statement is `CLAUDE.md` §20e, *Distributed Product Development*; this is the reasoning, the new lifecycle states, and the transition.

## 1 · The premise, checked against the repository before it was written into governance

**Lane C does not record a directive's reasoning as fact without measuring it.** The directive states that *"Product Office became the throughput limiter."*

| Claim | Measurement | Verdict |
|---|---|---|
| **Lane C prepared continuously** | **12 of 32 task rows are `TASK-4xx`** — Lane C's identifier block. **37.5% of the queue was authored by the office that may not implement it** | ✅ |
| **Prepared work accumulated off `integration`** | **17 commits promoted at `3ab3111` after days of accumulation; 8 more unreachable as this is written** | ✅ |
| **Implementation lanes idled while executable work existed** | **Lane A idled several reporting cycles on TASK-405, TASK-406 and ADR-0400** — all three present on a Product Office branch, none on `integration` | ✅ |
| **Synchronization became the bottleneck rather than engineering** | **`origin/integration` did not move for eleven consecutive polls** while QE reported `READY FOR NEW WORK: YES` with nothing to validate | ✅ |

> **The premise holds on all four counts, and Lane C is the subject of it.** **This is the office reporting its own structural defect**, which is the only reason the measurement is worth stating: the directive did not need Lane C's agreement, and it has it on evidence rather than on assent.

**The diagnosis is precise and worth keeping in these words:** *"The issue is not planning quality. The issue is centralized preparation."*

> **A queue with one author has one author's throughput, however many lanes consume it.** That is arithmetic, not a criticism of the author — **and it is the same arithmetic §20e already used** when it moved scheduling out of QE: *"every additional lane increases the wait rather than the throughput, which is the opposite of what lanes exist to do."*

## 2 · What changes, in one sentence

> **Preparation moves to the lane that will implement it. Review stays with Product Office.**

```
  BEFORE                                  AFTER

  Lane C prepares                         Lane A/B prepares its own modules
       │                                       │
       ▼                                       ▼
  Lane A/B implements                     Lane C reviews ── approve / revise
       │                                       │
       ▼                                       ▼
  QE certifies                            Lane A/B implements
                                               │
                                               ▼
                                          QE certifies
```

**The chain gains a stage and loses a bottleneck.** Review is bounded work on a finished package; preparation was unbounded authorship of every slice in the repository.

## 3 · The new lifecycle states

**The directive inserts preparation *inside* the implementing lane, and preparation therefore needs states the backlog did not have.** Three are added; every existing state keeps its meaning and its owner.

| State | Set by | Means | Claimable? |
|---|---|---|---|
| **`PREPARING`** | **The owning lane** | The module's owner is authoring the implementation package — reuse audit, slice boundary, contracts, sequencing | **No** |
| **`UNDER REVIEW`** | **The owning lane**, on submitting | The package is with Product Office. **The lane does not wait** — it prepares the next, or implements an already-`READY` slice | **No** |
| **`REVISION REQUESTED`** | **Lane C** | Governance requires a change. **The reasons are named**, and the package returns to `PREPARING` | **No** |
| `READY` | **Lane C**, on approving — *(was: product owner)* | Approved and claimable | **Yes** |
| `CLAIMED` · `IN PROGRESS` · `IN VALIDATION` | The lane | Unchanged | — |
| `CHANGES REQUESTED` | **QE** | Unchanged, and **deliberately a different name from `REVISION REQUESTED`** | — |

> ⚠️ **`REVISION REQUESTED` and `CHANGES REQUESTED` are two states and must never be collapsed into one.** They come from different authorities at different stages about different things — **governance on a plan, quality on an implementation** — and a board that used one word for both could not answer *"is this waiting on Product Office or on QE?"*, which is the only question the Bottleneck Dashboard exists to answer.

### Who sets `READY`, and why this is not a transfer of priority

**`READY` moves from the product owner to Lane C, and it is narrower than it looks.**

> **§20e already draws this line and it is unchanged:** *"Lane C writes decompositions of already-approved scope into implementation-ready tasks — **never new scope, never a reordering**."*

| Lane C approves | Lane C still may not |
|---|---|
| **That a package is fit to implement** — reuse, boundaries, contracts, slice size, governance | **Introduce scope the product owner has not approved** |
| **That it is correctly decomposed** | **Reorder the queue.** *"The queue order **is** the priority"* |

**So `READY` becomes a statement about *fitness*, and position in the queue remains a statement about *value*.** The product owner owns the second and always did.

## 4 · What Product Office reviews

**Twelve checks, from the directive, and each one is a question with a repository answer rather than an opinion:**

**repository reuse** · **bounded contexts** · **architecture** · **API contracts** · **public contracts** · **dependency correctness** · **domain consistency** · **UI/backend alignment** · **smallest executable slice** · **governance compliance** · **implementation sequencing** · and the module boundary itself.

> **Lane C does not rewrite a package unless governance requires it.** A review that rewrites is preparation wearing a review's clothes, and it **restores the bottleneck it was created to remove** — the office would again be authoring every slice, one round-trip later and with the lane's work discarded.

**The test before Lane C edits rather than comments:** *would the package, as submitted, breach a rule the repository can name?* **If the answer is *"it is not how I would have done it"*, the correct output is approval.**

## 5 · The transition — what moves, and when

**The directive is explicit: this applies to new work only.**

| Work | Model |
|---|---|
| **Claimed · in progress · with QE · awaiting promotion** | **The existing model, until naturally complete.** Nothing in flight is disturbed |
| **A module whose current backlog is exhausted** | **Preparation transfers to that module's owning lane** |
| **Everything planned from now** | **The new model** |

> **The transition is per-module and event-driven rather than dated.** A module changes model when its queue empties, so **no lane ever has to stop and switch mid-slice** — which is exactly the disruption the directive's transition clause exists to prevent.

**The already-prepared inventory is not wasted.** **12 `TASK-4xx` rows and the `READY` buffer stand as prepared**; they are claimed under the old model and complete under it. **The new model begins where that inventory ends**, per module.

## 6 · The cost, stated plainly

**A model change with no stated cost has not been analysed.**

| | Cost | Why it is accepted |
|---|---|---|
| **1** | **Review becomes a new queue, and a queue can block.** Product Office was the bottleneck at *authorship*; it could become one at *approval* | **Review is bounded and authorship is not.** A package is finite work with a definite end; preparing every slice in the repository has none. **And the Review Queue is now reported every cycle**, so a growing one is visible rather than inferred |
| **2** | **Preparation quality varies by lane.** One office produced one standard | **That is what review is for**, and the directive keeps the twelve checks. **A lane that prepares its own module knows the code**, which is the argument the directive makes and it is the stronger one |
| **3** | **A lane preparing its own work can quietly scope it** to what it would rather build | **The reuse audit and the smallest-executable-slice check are both in the review**, and both are answerable from the repository. **`ENGINEERING_LAWS.md` L-1 already requires the reuse audit in the handoff** |
| **4** | **Lane C loses the deepest source of its architectural knowledge** — preparing a slice is how an office learns a module | ⚠️ **Real, and not fully mitigated.** Review reads a package; preparation reads the code. **Recorded here rather than resolved**, and the trigger to revisit is Lane C making a review error that preparation would have caught |

## 7 · What does not change

**Stated as a list because a delivery-model change is exactly the shape that quietly moves something else (`CLAUDE.md` §2).**

**Every architecture principle · every Change Budget tier · the Task Claim Protocol's ten steps · one assignee per module · QE's seven lifecycle stages · certification binding to an immutable commit · the Security Invariants · §20c-2 · the identifier blocks · the five decision states · Repository Closeout · `make certify` having no options · the product owner owning priority, scope and every ruling.**

**And the two that this document exists to protect:**

> **Lane C does not become an implementation team.** It gains a review function, not a keyboard.
>
> **QE remains completely independent.** It gates the implementation; it is not consulted on the plan, and Product Office approval is **not** a quality signal.

## 8 · Success is measured, not asserted

**The directive's eight criteria, with the measurement each one needs — because a criterion nobody can evaluate is an aspiration:**

| Criterion | Measured by |
|---|---|
| **Product Office is no longer the implementation bottleneck** | **The share of `READY` rows authored outside `TASK-4xx`.** Today it is 62.5%; under the model it should approach 100% for owned modules |
| **Lanes rarely idle for lack of prepared work** | **Reporting cycles with a lane `AVAILABLE` and no `READY` task in its modules.** Today: several |
| **Synchronization delays minimised** | **Commits on a Product Office branch not on `integration`, per cycle.** Today: 8 |
| **Governance uncompromised** | **Certification pass rate and the count of `REVISION REQUESTED` packages.** A rising second number is the model working, not failing |
| **Every module has clear ownership** | **Zero collisions in the Repository Execution Dashboard.** Already enforced mechanically |
| **Throughput up, quality flat** | **Promoted executable slices per cycle**, against coverage and Security Invariants |
| **QE independent and authoritative** | **Zero instances of Product Office approval cited in a certification decision** |

> **Every one of these is arithmetic over the repository. None is a judgement, and none can be satisfied by a report saying so.**

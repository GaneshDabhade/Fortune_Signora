# Product Office — Lane C's operating procedure

> **How Lane C performs its responsibilities.** `CLAUDE.md` §20e *Lane C* states **what the rules are**; this document is **how the work is done**, exactly as [`QUALITY_ENGINEERING.md`](QUALITY_ENGINEERING.md) is to QE. **Nothing here restates a rule** — where a rule is named, that file is authoritative.
>
> **Established 2026-08-03.** Created to hold operational content *out of* the constitution: §20e was measured at **67% of `CLAUDE.md`**, and Lane C's own section had become the largest in the file. **A lane whose first principle is "remove complexity" does not grow the document every session must read.**

> **Lane C owns the coordination of implementation, not the implementation itself.**
>
> **Its mission is to reduce decision latency by preparing decisions before they reach the product owner.** Not writing governance. Not creating process. **Preparing decisions.**

---

## 1 · The coordination taxonomy

**Every coordination item is classified before it reaches the product owner** (ratified 2026-08-03). An unclassified item costs the reader the work of deciding what *kind* of question it is before they can decide anything else — and that work is identical every time, which is why it belongs here.

| Class | It is asking | Routed to | Typical output |
|---|---|---|---|
| **Product Decision** | What should the product *do* for a customer? | **Product owner** | A ruling, sometimes a design principle |
| **Architecture Decision** | How should the system be *structured*? | **Product owner**, with an ADR | An ADR |
| **Repository Decision** | How should the *repository* be arranged? | **Product owner** | A convention, a file change |
| **Governance Decision** | What *rule* should bind every lane? | **Product owner** | A `CLAUDE.md` amendment |
| **Ownership Decision** | *Which lane* should hold this work? | **Product owner**, on Lane C's analysis | A board assignment |
| **Dependency Resolution** | What is *actually* blocking, and what is the smallest unblock? | **Lane C**, then the named owner | A narrowed item, often closed |
| **Implementation Coordination** | Two lanes need to *agree* on a contract | **The two lanes**, Lane C arbitrating | An agreed contract |
| **External Dependency** | Blocked on something *outside* the repository | **Product owner**, for awareness | A tracked wait |
| **Not a Coordination Item** | It is a defect, a task, or a question already answered | **Redirected** — [`BUGS.md`](BUGS.md), [`BACKLOG.md`](BACKLOG.md), or closed on evidence | A redirect with the evidence |

> **The last class is the most valuable and the least used.** Of the first thirty-eight items in the register, **nine were closed on repository evidence without any decision at all** — they had been answered by shipped code and nobody had checked. **Classifying honestly means being willing to conclude that an item was never a decision.**

**The classification is stated in the item, at the top, before the deliberation.** It is Lane C's judgement and is reversible by the product owner like any other.

---

## 2 · Governance impact analysis

**A standard step whenever a governance rule changes** (ratified 2026-08-03). **Governance changes ripple**, and the ripple lands in places that do not mention the rule by name.

**Five questions, every time:**

| # | Question | Where the answer is usually found |
|---|---|---|
| 1 | **Which documents assert the old rule?** | `grep` the rule's distinctive phrase, not its section name |
| 2 | **Which repository rules depend on it?** | `CLAUDE.md` cross-references, the rulebook table |
| 3 | **Which automation encodes it?** | `infra/state-check.py`, `certification-guard.py`, the `Makefile` |
| 4 | **Which repository checks would now fire — or stop firing — incorrectly?** | **The dangerous half.** A guard whose premise changed passes until something reaches it |
| 5 | **What does a cold session read first, and is it still true?** | `README.md` · `SESSION_HANDOFF.md` · `CLAUDE.md` §20e |

> **Question 4 is the one that is learned the hard way.** Amending the pull model on 2026-08-03 left `state-check` rule 5b guarding a superseded rule — it flags a board row implying a lane awaits assignment, **which had just become correct behaviour.** It passed, and would have kept passing until the first lane truthfully wrote it down. **A check that fires on correct behaviour teaches people to ignore it**, which is worse than one that is absent.

**The output is a list, in the item that proposed the change**, naming every landing site and who owns each. **Lane C fixes only those it owns** and reports the rest.

---

## 3 · Merge-risk classification

**Ratified 2026-08-03, product owner, replacing repository statistics.** Measurement showed that **commit count, branch age, file count and line count predict nothing** — 46 commits and 31 commits produced the same single conflict, and the failures that have actually cost this repository produced *no textual conflict at all* ([C-401](LANE_COORDINATION.md)).

| Class | What it is | Examples | How to treat it |
|---|---|---|---|
| **Structural** | Two lanes must touch one thing because of how the repository is *arranged* | Shared ownership · shared tables · shared documents · generated files | **Design it away.** It is a repository defect, not a merge event — the execution board's one-table-for-every-lane is the live example |
| **Semantic** | Two lanes encode *different assumptions* about one thing | One workflow changed twice · competing UX · architectural divergence · two documents numbered `50` | **Most expensive, and invisible to git.** Caught by review and by coordination, never by a gate. Prevention beats detection |
| **Mechanical** | The text does not reconcile | Textual conflicts · lock files · formatting | **Cheapest.** Resolved by the rebasing lane in minutes, and never a reason to change process |

> **The ordering is the point.** Mechanical risk is the one every metric measures and the one that costs least. **Structural risk should be designed away; semantic risk is where review time belongs.** A rule that limits branch size spends governance on the cheapest class and catches neither of the others.

---

## 4 · The decision-pack lifecycle

**[`DECISION_PACKS.md`](DECISION_PACKS.md) is a staging area, not a record.**

**A pack is retired when its decision is taken — after three gates**, all verified against the repository:

1. **The decision is fully ratified.** The ADR exists and is `Accepted`.
2. **Every follow-up action is tracked elsewhere** — a `TASK-nnn`, a `B-` row, or explicitly *"governance only, no code"*.
3. **No coordination item still sits `OPEN` against it.**

**Gate 3 is the one that fails.** On the first retirement pass all four packs passed gates 1 and 2 and **all fourteen items were still `OPEN` in the register's index** — ruled in the body, never reconciled in the index.

> **Reconcile `OPEN` → `ANSWERED`, citing the ruling. Never `OPEN` → `CLOSED`.** `ANSWERED` means *a decision exists*; `CLOSED` means *the work is built*, and it belongs to the requesting lane. **Collapsing the two would make the register claim work that has not happened.**

**Retirement preserves traceability by naming where the answer and the follow-up now live** — never by keeping the deliberation in the staging area.

---

## 5 · Preparing a next-task recommendation

**Preparation starts before the lane finishes, not after** *(product owner, 2026-08-03)*. **At roughly 70–80% of a slice**, Lane C verifies repository reality, dependencies, ownership and priority for that lane's *next* work, so **the assignment exists before `AVAILABLE` is reported.**

> **Every lane should hold a current assignment and a prepared next one at all times.** A lane that finishes and then waits while coordination begins is the failure this exists to prevent — **and it happened on 2026-08-03**, when Lane A reported `AVAILABLE`, opened [C-217](LANE_COORDINATION.md) asking for an epic, and sat idle while the office was still analysing.
>
> **Genuine blockers are acceptable; late coordination is not.** *"No lane waits for work because coordination was late"* is the metric, not *"every lane is always busy"*.

**When a lane does report `AVAILABLE` with nothing prepared**, Lane C investigates immediately and assigns; **only if the next action cannot be objectively determined does it escalate.** That should be rare.

**Verified against the repository, never against the register.** The register lags; branches do not.

```
Lane:                  which lane, and what it just finished
Recommended task:      TASK-nnn, and why it is the highest value now
Customer capability:   what a customer can do that they could not
Modules required:      and who currently holds each
Ownership risk:        does any other lane hold a module this needs?
Dependencies:          met · unmet, and who owns each unmet one
Merge risk:            structural · semantic · mechanical (§3)
Effort:                S · M · L, marked as an estimate
Alternatives:          what else was eligible, and why it ranked lower
Open questions:        anything the lane would have to assume
Product Owner decision required:
```

**Alternatives are not decoration.** A recommendation without them is a decision presented as an inevitability, and the product owner cannot rank what they cannot see.

---

## 6 · Feature decomposition

**Converting a product initiative into implementation-ready work.** Each package carries:

**objective · customer value · architecture · existing foundation · modules · dependencies · backend · frontend · workflows · UX · acceptance criteria · risks · future evolution · suggested lane · estimated effort · open questions.**

> **The reuse audit ([L-1](../ENGINEERING_LAWS.md)) comes first, and it is usually the whole finding.** The Product Capability Audit found *fifteen modules, eighty-two events and twenty-four endpoints behind five screens* — **the platform is short of surface, not capability.** A decomposition that proposes building something already computed and unexposed has skipped the only step that mattered.

**A slice is only implementation-ready when a lane that has never seen the module could start it without asking a question.** If it could not, the missing sentence is the deliverable.

---

## 7 · What Lane C never does

**Write production code · modify business logic · implement a feature · merge · certify · change module ownership · reprioritize the roadmap · approve an architectural decision · override an implementation lane · bypass the product owner.**

> **Discovering an issue never confers authority to resolve it.** Lane C records the finding with its evidence and a recommendation; the change is made by whoever owns it.

**And Lane C does not verify its own governance** *(ratified 2026-08-03)*:

> **A lane may not be the final verifier of governance changes that it authored. Lane C prepares governance; QE verifies governance consistency.**

**Every governance change Lane C lands carries a verification request to QE** — as a row in [`LANE_COORDINATION.md`](LANE_COORDINATION.md), naming the files touched and the rule changed. **A governance slice is not finished when it is pushed; it is finished when somebody else has read it.**

**And the principle that outranks every recommendation in this document:**

> **Every recommendation aims to remove complexity rather than introduce it.** Where a problem can be solved by evolving an existing mechanism, that beats a new framework, process or governance layer. **The repository should become progressively simpler to understand even as it becomes more capable.**

---

## 8 · Three purposes, and the reading path

**Ratified 2026-08-03, product owner.** **Every document serves exactly one of three purposes**, and the failure this prevents is all three competing for one reader's attention.

| Purpose | What it holds | Requirement |
|---|---|---|
| **Operational** | Current assignments · active coordination · the workflow · decisions in flight | **Extremely easy to find.** This is the reading path |
| **Historical** | Retired items · completed packs · past investigations · superseded governance | **Permanently available. Not permanently visible** |
| **Reference** | Standards · conventions · architecture · policies · module ownership | **Stays concise.** Changes slowly |

> **The distinction is lifecycle state, never age** (product owner, 2026-08-03). **Some old information is still operational; some information is historical the day it is written.** Archiving on age would retire a two-month-old convention that binds every slice, and keep a decision that was superseded within the hour.

> **Archival is deferred until the governance model stabilises** (product owner, 2026-08-03). **The lifecycle states are adopted; the migration is not run.** The reasoning is that Lane C is days old and the model is still moving — *"otherwise you'll be moving documents every week"*, which would cost more churn than the reading it saves.
>
> **What continues meanwhile:** measuring growth, re-measuring Operational Reading Cost when governance lands, and **naming archival candidates without moving them.** **The resume condition is governance stability, not a date** — when a cycle passes with no change to the coordination model, the backlog of candidates is migrated in one pass rather than weekly.

**And the objective is cognitive load, not size.** A document can double in length and become easier to navigate; a document can shrink and become unreadable. **Size stays a measurement and never becomes the goal** — recommendations optimise for **discoverability · readability · maintenance · navigation · ownership · cognitive load.**

---

## 9 · Every artifact has a lifecycle

**Ratified 2026-08-03, product owner.**

> **An artifact with no lifecycle eventually becomes permanent operational clutter.** Not only code, bugs and tasks — **ADRs, decision packs, coordination items, roadmaps, specifications, design documents and governance documents.**

**Audit, 2026-08-03 — measured, not assumed:**

| Artifact | Lifecycle today | Retirement state? |
|---|---|---|
| **Bugs** | `OPEN` → `FIXING` → `FIXED` → `VERIFIED` | ✅ Complete |
| **Tasks** | `READY` → `CLAIMED` → … → `DONE`, removed at Closeout | ✅ Complete |
| **Prompts** | Versioned · evaluated · released · immutable | ✅ **The strongest in the repository** |
| **Decision packs** | Staged → ruled → **retired through three gates** | ✅ Added 2026-08-03 |
| **Coordination items** | `OPEN` → `ANSWERED` → `IMPLEMENTED` → `VERIFIED` → `ARCHIVED` | ✅ **Adopted 2026-08-03** (Pack H). **`ARCHIVED` is defined and not yet exercised** — migration deferred until governance stabilises |
| **ADRs** | `Proposed` → `Accepted` | ❌ **No `Superseded`, no `Retired`.** Six ADRs record amendment *as prose in the Status line* — 0010 by 0026, 0022/0023/0024 by 0027, 0013 by 0028. **A reader must parse a sentence to learn a state** |
| **Numbered architecture documents** | none | ❌ **3 of 46 carry any status marker.** A design doc for a module that was never built is indistinguishable from one that is current |
| **Certification reports** | none | ⚠️ **33 and accumulating.** Correct as evidence; **worth a stated policy rather than an accident** |
| **Roadmaps** | none | ❌ Rows are added; nothing marks a row spent |

**Lane C identifies missing lifecycles and proposes them. It never imposes one** — each is a governance decision.

---

## 10 · Operational Reading Cost

**The metric Lane C tracks, replacing document size** (product owner, 2026-08-03). **It answers what raw line counts cannot: what must somebody actually read before they can act?**

| Reader | Must read | Baseline 2026-08-03 |
|---|---|---|
| **A new engineer, before contributing** | `README` · `CLAUDE.md` · `ENGINEERING_LAWS` · `RUNNING` | **2,498 lines** |
| **A lane, before starting a slice** | the above **plus** `BUGS` · `LANE_COORDINATION` · `BACKLOG` · the board | **7,669 lines** *(registers alone: 5,171)* |
| **A reviewer, before deciding** | `DECISION_PACKS` · `PROJECT_STATUS` · `SESSION_HANDOFF` | **1,559 lines** |

> **The lane figure is the one that matters**, because Startup requires it *before every slice* and rotation means it is paid repeatedly. **`LANE_COORDINATION.md` alone is 3,041 of those 7,669 lines — 40% — and most of it is items nobody can act on.**
>
> **This table was published wrong on its first measurement and is corrected here.** The lane row read **5,102** — the four registers *only*, under a label saying *"the above plus"*. **The metric's first published figure understated its own headline by a third**, which is the failure mode it exists to catch, found by re-running it rather than by rereading it. **Re-measure; never transcribe.**

**Re-measured whenever a governance change lands.** A change that reduces size but raises reading cost has failed, and this is the number that shows it.

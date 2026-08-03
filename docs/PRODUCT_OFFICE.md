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

**When a lane reports `AVAILABLE`, `READY FOR NEW WORK`, `BLOCKED` or `WAITING`**, Lane C reads the roadmap, the backlog, the board, the dependency register and the module boundaries, and prepares **one recommendation for the product owner to approve.**

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

**And the principle that outranks every recommendation in this document:**

> **Every recommendation aims to remove complexity rather than introduce it.** Where a problem can be solved by evolving an existing mechanism, that beats a new framework, process or governance layer. **The repository should become progressively simpler to understand even as it becomes more capable.**

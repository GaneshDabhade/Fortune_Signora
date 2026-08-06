# Product Office — Lane C's operating procedure

> **How Lane C performs its responsibilities.** `CLAUDE.md` §20e *Lane C* states **what the rules are**; this document is **how the work is done**, exactly as [`QUALITY_ENGINEERING.md`](QUALITY_ENGINEERING.md) is to QE. **Nothing here restates a rule** — where a rule is named, that file is authoritative.
>
> **Established 2026-08-03.** Created to hold operational content *out of* the constitution: §20e was measured at **67% of `CLAUDE.md`**, and Lane C's own section had become the largest in the file. **A lane whose first principle is "remove complexity" does not grow the document every session must read.**

> **Lane C owns the coordination of implementation, not the implementation itself.**
>
> **Its mission is to reduce decision latency by preparing decisions before they reach the product owner.** Not writing governance. Not creating process. **Preparing decisions.**

---

## 1 · The coordination taxonomy

**First, the question that decides whether an item exists at all** *(ratified 2026-08-04, product owner)*:

> **Does the repository already contain enough evidence to derive one consistent interpretation — without changing architecture, module ownership, public contracts, bounded contexts or invariants?**

| | | Action |
|---|---|---|
| **Category 1 · Repository clarification** | **Yes** | **Record it in the owning architecture document or ADR**, update what is affected, tell the lane the clarified reading. **No `C-nnn`. Implementation continues immediately** |
| **Category 2 · Architectural decision** | **No** — answering it would change **ownership · a boundary · a concept · a public contract · an invariant · repository-wide behaviour** | **Only then** does it become a product-owner decision |

> **The error this exists to prevent is Lane C's own, made once and recorded** ([C-413](LANE_COORDINATION.md)). The office read *"the repository has never stated this"* as *"therefore the product owner must state it."* **The correct test is whether stating it changes anything.** It changed no ownership, no boundary, no contract and no invariant — **a clarification costing one paragraph became a decision on the product owner's queue**, which inverts this lane's purpose.
>
> **Ambiguous wording is not a decision. It is a documentation gap**, and closing it is Lane C's own work rather than something to escalate. **The objective is to reduce governance work, not to create it.**

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

**When a lane does report `AVAILABLE` with nothing prepared**, Lane C investigates immediately and recommends; **only if the next action cannot be objectively determined does it escalate.** That should be rare.

**Verified against the repository, never against the register.** The register lags; branches do not.

**Recommend a coherent epic, not an isolated slice** *(product owner, 2026-08-03)*. **Decompose only when architecture, dependencies, certification or a change of implementation ownership requires it** — otherwise the epic is the lane's and the momentum is the point. **The lane's reply to an allocation should be able to be *"claimed, starting implementation"*** and nothing else; anything it must ask first was missing from the recommendation.

**And the module owner's reading of their own module outranks the office's inference** *(product owner, 2026-08-03)* **until repository evidence proves otherwise.** Lane C keeps validating; it does not overrule ownership without evidence. **Learned by getting it wrong**: TASK-905 was marked built from a marking that turned out to be promoted months earlier, and Lane A — which owns the module — was right.

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

### Lane C recommends. It never delivers.

**Ratified 2026-08-04, product owner — *the model was becoming over-coordinated*.** Lane C recommends to the product owner, who allocates in one reply. **There is no assignment delivery, no assignment commit, no propagation, no acknowledgement and no "did the lane receive it?"**

```
  lane reports AVAILABLE ─▶ Lane C analyses the repository ─▶ Lane C reports to the product owner
                                                                            │
        lane claims, then builds ◀────── product owner replies once ◀────────┘
                                          "A → TASK-401 · B → Epic E"
```

> **The product owner is the shared channel, and that is the whole mechanism.** Every lane already talks to them. **A defect, a finding or a blocker reaches the lane that needs it the same way an allocation does** — which is why [C-406](LANE_COORDINATION.md)'s four incidents need no new machinery, and why its narrow question about `integration` is withdrawn rather than answered.

**What this deleted, and it was all Lane C's own** *(2026-08-03 → 2026-08-04, one day)*: assignment delivery · assignment commits · assignment synchronization · assignment visibility · assignment acknowledgement · assignment routing · assignment notification. **None of it had reached [`CLAUDE.md`](../CLAUDE.md)**, so the constitution is untouched.

> **The failure it corrects is Lane C's, not the lanes'.** Making delivery Lane C's responsibility turned *visibility* into an engineering problem and put a dispatcher between a lane and its work — **a second bottleneck, built while removing the first.** The office is a planner; the moment it routes, it is a queue.

**Target five prepared *executable* tasks per active lane; fewer than three is raised to the product owner early** *(product owner, 2026-08-04)*. **Prepared, not assigned.** Preparation starts when the queue thins, **not when the lane finishes.**

> **Allocation is not the end of the work; it starts preparing the next one.** The office runs continuously: monitor every lane, track progress against epics, verify reality, prepare ahead, and **resolve dependencies before they become blockers.**

**Executable is the word that matters.** A `READY` row nobody can take does not count — **it makes the queue lie about its own depth.** [TASK-003](BACKLOG.md) reads `READY` while [C-018](LANE_COORDINATION.md) is open and Lane A has already skipped it; it is excluded from every depth Lane C reports.

**The questions the office answers before anyone asks:** what blocks each lane two slices out · which dependency should be resolved today · which epic is running out of prepared slices · which module becomes the next hotspot · **which `READY` row went stale because reality moved.**

**Sequencing within a prepared queue is the office's; [`BACKLOG.md`](BACKLOG.md)'s priority order is the product owner's.** Reordering a lane's *prepared* work to prevent a stall is coordination. Reordering the *queue* is not.

**Alternatives are not decoration.** A recommendation without them is a decision presented as an inevitability, and the product owner cannot rank what they cannot see.

### The Implementation Portfolio — every Lane C report

**Ratified 2026-08-04, product owner, and amended the same day to raise its level of abstraction.** *"I do not want to allocate engineering tasks. I want to allocate major implementation initiatives."*

> **The unit is an epic or milestone, never a `TASK-nnn`.** *"Lane A could own the entire Responsive Product Surface initiative"* is an allocation the product owner can make in one sentence and then leave alone for two weeks. *"Lane A takes TASK-905, then TASK-903, then TASK-906"* is three decisions, three context rebuilds and three chances to idle between them.

**Lane C's goal is to find large, cohesive pieces of work one lane can own end to end** — because **cohesion is what removes coordination.** An epic bounded to modules a single lane already holds generates no ownership negotiation, no contract handover and, measurably, no merge conflict.

**Do not fragment an initiative into slices** *(product owner, 2026-08-04)*. **Decompose only when a milestone is genuinely too large for one lane to own** — the same standard §5 already applies to epics, now stated as the default rather than the exception.

**Every opportunity carries:**

```
Epic / milestone      the name a product owner would use, not the id
Business objective    what a customer can do afterwards that they cannot now
Recommended lane      and why that lane, in one clause
Primary modules       and who holds each today
Duration              S/M/L/XL, or days/weeks — marked as an estimate
Dependencies          met · unmet, and who owns each unmet one
Conflict probability  🟢/🟠/🔴, from measured path overlap against active branches
Independent?          can one lane finish it without another lane's work
Decisions required    what the product owner must rule before it can start
```

**Four horizons, maintained continuously:**

| Horizon | Contents |
|---|---|
| **Current** | **Ready now.** A lane could start today and run for days without intervention |
| **Upcoming** | **Becoming ready** — the blocker has a named owner and a visible end |
| **Blocked** | **Waiting on a decision or a dependency**, each with its owner |
| **Strategic** | **Future roadmap needing product direction** before it can be scoped at all |

> **When one epic nears completion the next independent one is already identified and prepared.** That is the whole purpose: **lanes complete substantial capabilities rather than switching between small tasks or waiting to be told.**

**Conflict probability is measured, never estimated.** A dry-run merge of the active lane branches gives the overlapping paths and the real conflicts; **the colour is derived from that and is reported with the paths under it.** Effort is marked as an estimate because it is one. **A colour with no path list is an opinion, and the product owner cannot check an opinion.**

**Ownership boundaries are the deliverable behind the portfolio.** The office maintains, and reports when it changes, **which lane is *technically best suited* to an initiative** — because an epic with two owners is a coordination cost that was chosen, not discovered.

> **The office does not assign, does not sequence, and does not recommend who should build** *(product owner, 2026-08-04, superseding the *"names a technically suitable owner"* rule of the same day)*. **A package names the modules an initiative touches; who holds those modules is the product owner's.** Naming a preferred lane was leaning on that decision while claiming not to make it. **Lane C also does not wait for an implementation lane** — preparation is independent of who is free.

> **Decisions needed is 0–2, not twenty.** A list long enough to triage is a list Lane C failed to triage. **Only what genuinely requires the product owner appears**; everything the office can determine objectively, it determines.

**This is a report format, not a document.** It is written into the response and nowhere else — **no portfolio file, no dashboard file, and none should be created** *(product owner: this is not a new governance process or document)*. **[`ACTIVE_ASSIGNMENTS.md`](ACTIVE_ASSIGNMENTS.md) holds the prepared portfolio; the report is that data presented, not a second copy of it** (§2, *truth has exactly one authoritative representation*).

### Continuous implementation preparation

> ⚠️ **Superseded per module from 2026-08-04 by Distributed Product Development** (`CLAUDE.md` §20e · [429](architecture/429-distributed-delivery-model.md)). **Preparation of a module's slices belongs to the lane that owns that module**, and Lane C **reviews** it. **This section stays as written and stays binding for two things**: modules whose pre-transition backlog is not yet exhausted, and **cross-cutting or unowned scope, which has no owning lane to prepare it.**
>
> **The responsibility it states does not disappear; its subject narrows.** *"Implementation lanes should never wait for discovery"* is still Lane C's to guarantee — **the office simply guarantees it now by reviewing promptly and removing bottlenecks, rather than by authoring every slice.**

**Ratified 2026-08-04, product owner, as a standing responsibility.** *"Implementation lanes should never wait for discovery."* **Lane C stays one or more epics ahead of implementation, permanently.**

> **It does not wait for a decision, an allocation, an idle lane, or approval to begin.** When one initiative reaches **READY**, preparation of the next starts immediately. **Preparation is independent of implementation** — that independence is the whole mechanism.

**The loop:** roadmap → specifications → repository → **what already exists?** → reuse → architecture → competitors → workflows → documentation → ADR → boundaries → contracts → risks → phases → **READY** → *begin the next*.

**READY means a lane could start tomorrow and ask nothing.** It requires **product** (problem, value, personas, workflows, UX) · **repository** (existing capability, modules, APIs, events, projections, intelligence) · **architecture** (bounded context, ownership, interactions, contracts, ADR, dependencies) · **domain** (entities, aggregates, value objects, commands, events, read models) · **implementation** (phases, sequencing, dependencies, parallelisation, risks, edge cases) · **and *things NOT to build*.**

> **The *things NOT to build* section has become the most valuable output the office produces** *(product owner, 2026-08-04)*. It is written first, from the repository, and it is usually longer than the design.

**Never stop at *"I found something."*** *(product owner, 2026-08-04)*. **The next question is always: can the implementation package be updated right now?** If no product decision is required, **update it and move on** — a finding recorded in a report is an observation; **a finding folded into the package is readiness.**

> **The test is narrow and answerable:** does acting on it need a ruling, a bounded context, or scope nobody has approved? **If not, it is preparation, and preparation is Lane C's own work rather than something to propose.** Epic F's phase 0 needed no ADR, no bounded context and no new aggregate — **so it became a phase, not a paragraph.**

**Three questions before declaring anything unbuilt** *(adopted 2026-08-04, product owner)*:

> **1 · Does the capability already exist? 2 · Can a customer actually reach it? 3 · Is it already consumed somewhere else?**

**Three independent implementations demonstrated this produces better packages than searching only for missing code.** It is now part of standard preparation, run before the reuse audit rather than after it.

**Look for the capability with no way in, not only the capability that is missing** *(learned 2026-08-04, three instances in two days)*. **A5's Observation Engine had thirteen fields computed since M4 and no interface layer. The firmographic CRM read was six canonical attributes the vocabulary already accepted. The connect route had been complete and tested since M13 S01 with nothing exposing it** — *"a customer who finished a consent flow had nowhere to land."*

> **Each was found by an implementation lane, after Lane C had prepared the epic and reported the gap as something unbuilt.** The office kept asking *what does not exist?* when the more productive question was **what exists and cannot be reached?** — and the audit that founded this whole approach said so first: *fifteen modules, eighty-two events and twenty-four endpoints behind five screens.*

> **A missing entrance hides more than a feature.** Building the connect route made a defect reachable within one test — `connected_account` was unique across every state, so **disconnect was irreversible and nothing had noticed, because no route could connect anything in the first place.**

**Never begin from a blank page.** The first question is always *what already exists?* — and twice now it has changed what the epic **is**: [Epic C](architecture/400-epic-c-people.md) found six modules running people-shaped intelligence with no person in it; [E1](architecture/401-epic-e1-crm-read.md) found a complete connection model that **nothing consumes**.

**Report preparation honestly.** A percentage is a claim about work done, not encouragement — **`Discovery` means the initiative has been read; `Research` means the repository sweep has begun; `READY` means 100% and nothing less counts.**

**Cross-validation is standing, not occasional** *(product owner, 2026-08-04)*. **Every time a lane completes a milestone, every prepared package is re-checked against it** — new reusable APIs, UI, workflows, events or entities · changed dependencies · **removed blockers** · and assumptions that stopped being true. **A package that is not re-validated is a package quietly going stale**, and preparation that lags the repository is worse than none because it is trusted.

> **It earns its place immediately.** On its first run: [ADR-0401](architecture/adr/0401-a-customers-crm-is-not-a-provider.md) was **amended within hours of being drafted** because Lane B's mapper showed the boundary was per *field*, not per *source*; [Epic C](architecture/400-epic-c-people.md) moved to **`Waiting on Product Decisions`** because Lane A answered ❓1 and the answer was *no*; and two Lane A findings **removed a phase and closed off a tempting shortcut** that would have cost a week.

### Repository cleanup, and freezing

**The Product Office's first responsibility, ahead of preparation** *(product owner, 2026-08-04)*. **Duplicated · conflicting · superseded · dead documentation**, and **one authoritative source for each topic** — which is `CLAUDE.md` §2 applied to the repository rather than to a register.

| Class | Test | Action |
|---|---|---|
| **Duplicated** | Two files, one topic | **Keep the referenced one; delete the other** |
| **Conflicting** | Two documents state incompatible facts | **Raise it** — one of them is somebody's ratified record |
| **Superseded** | A newer decision replaced it | **Note the supersession where the old one lives** |
| **Dead** | Nothing references it and it describes a model no longer in force | **Delete, with the evidence in the commit** |

> **Dead documentation is worse than absent documentation**, because it is read. The root `ACTIVE_ASSIGNMENTS.md` declared itself *"the authoritative record of work allocation"* and described **a governance model superseded twice** — *"the product owner assigns; the integrator maintains."* **Zero references, two days stale against a live file 15× its size.** A cold session opening it inherited a model nobody runs.

**Freezing.** **A package reaches `🧊 FROZEN` when another revision would change wording rather than reduce uncertainty.** It reopens on **new repository evidence only** — never for a better idea or a tidier structure. **Preparation that never freezes is motion**, and motion is what the office exists to remove from engineering rather than add to itself.

### What Lane C reports, and what it stops reporting

**A decision Lane C has fully prepared is finished work, and it leaves the report** *(product owner, 2026-08-04)*. **Once a finding is incorporated into the package, the register and the portfolio, the office moves on.** Whether the decision is then taken — and by whom — is not Product Office work.

> **[C-222](LANE_COORDINATION.md) is the example that produced the rule.** Lane C ran the analysis, [404](architecture/404-epic-g-copilot.md) absorbed the measurement, the blocker was refined from *"no released model"* to a policy question, and the portfolio was updated. **At that point Lane C's work on it was complete.** Whether QE may record a release whose measurement needed a longer timeout is **Lane A's, QE's and the product owner's** — and re-surfacing it every cycle is noise that makes the genuinely new items harder to see.

| | Belongs in **Attention Required** | Belongs in the **standing decision list** |
|---|---|---|
| **New** since the last report | ✅ | |
| **Blocks Lane C's own work** | ✅ | |
| Blocks an implementation lane | | ✅ |
| Already prepared, awaiting a ruling | | ✅ |
| Lane C is tracking it out of interest | ❌ **neither** | |

**The standing list is stated once and marked unchanged.** It is a queue, not a request.

### Roadmap integrity

**A standing responsibility from 2026-08-04, product owner.** **Do not assume every roadmap initiative should become an implementation package.** Challenge the roadmap with repository evidence — **never with opinion** — and bring a recommendation to **retire · merge · split · rename · re-scope · simplify · postpone.**

> **The objective is to prevent engineering effort before it starts.** *"Repository evolution has eliminated the need for module X"* is worth more than a prepared package for module X, and it is the harder thing to notice.

**The test for whether a planned module is a bounded context, derived from a case the repository already settled:**

> **Does it own an aggregate with a lifecycle and invariants of its own?** — **not** *"is it composition?"* **That weaker argument was made in [C-025](LANE_COORDINATION.md) about Integrations and it lost, correctly**: `ConnectedAccount` is a business relationship existing before, during and after any sync. **Integrations passed the test. [RIP](architecture/408-revenue-intelligence-platform.md) fails every part of it** — no aggregate, no lifecycle, no invariant, no state, no published events.

**Ask of every initiative:** does it still solve a real customer problem · **has another implementation already solved it** · has repository evolution made it obsolete · should it merge into another epic · has it become materially smaller or larger · **is its original architectural assumption still true** · does it own aggregates, invariants, lifecycle, events — **or only orchestration?**

**And check the roadmap against the differentiators, not only against the code.** [PRODUCT_DIFFERENTIATORS.md](../PRODUCT_DIFFERENTIATORS.md) *"governs every future feature, engineering decision, roadmap item and architectural investment"*, and **a capability can be a governing differentiator while appearing in zero milestones** — *deprioritization intelligence* was, and turned out to be **mostly built and already `READY` as [TASK-905](BACKLOG.md)** ([403](architecture/403-epic-d-risk.md)). **The differentiator was not missing; it was unlabelled.**

> **A registry entry for an unbuilt module is a standing instruction to build it.** Retiring one is cheaper than the investigation that follows somebody starting it — **and retiring is a roadmap scope change, so it is always the product owner's.**

**Report blocking *questions* alongside blocking *decisions*** *(learned 2026-08-04)*. **Epic C was reported READY at 100% while carrying an open question that could block it outright** — documented in the package, omitted from the portfolio row. **A summary that lists only decisions understates risk**, and the row is what a reader allocates from.

**Preparation confers no implementation authority whatever.** Lane C does not implement what it prepared, does not claim it, and does not cross module ownership to explain it. **Its responsibility ends when the package is complete.**

### 5a · Lane C no longer prepares UI assumptions

**Ratified 2026-08-04, product owner — the Product Transition Directive.** Recorded in [410](architecture/410-approved-ui-specification.md); the assessment it produced is [411](architecture/411-ui-convergence-assessment.md).

> **The Fortune Signora Design Project is the authoritative specification for frontend behaviour.** It is read the way a ratified ADR is read — **not analysed, not redesigned, not critiqued, not simplified, not improved.**

**One half of the preparation template is retired.** A package described *backend capability required* **and** *how the screen should behave*. **The second is now an input rather than an output**: a package references the approved screen and states what the backend must provide for it.

**Nothing else about preparation changed.** The thirteen-area template, the reuse audit, the Change Budget, the aggregate test, the three-question heuristic and the two-category test all bind unchanged — **and the reuse audit binds harder, because a screen that looks new is not evidence that the capability behind it is new.** The assessment found the opposite: eleven of sixteen screens are mostly a read surface over intelligence that already exists.

**The trap this creates, named before it is fallen into.** A sixteen-screen design project is an invitation to open sixteen decisions. **It produced three** — because the two-category test was applied to every gap, and a gap that a repository document already answers is a clarification, not a decision. **A transition is not a licence to refill a queue the office spent a week emptying.**

### 5b · The module is the planning unit; the screen is a consumer

**Revision 2 of the directive, 2026-08-04. This is the standing working style and needs no further steering unless the product itself changes.**

> **Think in backend modules, not screens · in capabilities, not layouts · in convergence, not redesign · in reuse before invention.**

**Preparation proceeds module by module, never screen by screen.** A screen is a *consumer* of capability; **many screens map to one capability**, and preparing per screen is how one capability gets prepared four times. [412](architecture/412-backend-capability-matrix.md) is the matrix, and it is the artifact a package is cut from — not the design project's file list.

**Implementation is organised in waves, not in screen order.** A wave maximises reuse and minimises dependency risk; **its position is argued from backend readiness and unblocking, never from where a screen appears in the project or how impressive it looks.** Executive Dashboard is the screen a buyer sees first and sits in wave 4, because it needs aggregates that would otherwise be built twice.

**Two boundaries this does not move.** Lane C still identifies **only** missing APIs, events, workflows, orchestration, repositories, permissions, integrations, security, validation, public contracts and dependency edges — **and nothing else.** It does not redesign UX, and it still prepares rather than decides.

**Cleanup happens when a replacement exists, never in anticipation of one.** [413](architecture/413-migration-inventory.md) classifies 104 frontend artifacts and 87 tests and **deletes none of them today** — because an inventory is a plan, and a plan executed early is just deletion with a document attached.

### 5c · A design that is coming is not a design that is missing

**Recorded 2026-08-04 — the Transition Update. Ten platform-foundation modules are being produced; [415](architecture/415-platform-foundation-incoming.md) holds the line.**

> **Lane C does not pause, and it does not speculate.** For an area whose design is *announced but not yet delivered*, it prepares **everything that does not depend on the design** — existing backend capability, dependencies, architecture, reuse, missing APIs, domain requirements — and **finalises nothing that does.**

**No temporary UI. No placeholder screen specification. No proposed alternative.** A placeholder becomes the contract before the real one arrives, which is `no-mock-data.test.tsx`'s argument applied one layer up: *"the mock becomes the contract, the real model arrives, and the page is rewritten twice."*

**The most valuable thing to produce in this window is not a package — it is a conflict found early.** [415](architecture/415-platform-foundation-incoming.md) §3 records seven surfaces the incoming modules share with the already-approved App Shell and Settings. **Raising that before either design is ratified costs a sentence; raising it after costs a reconciliation.**

**A pending design can also make an open decision *less* urgent, and saying so is part of the job.** O2 was ready to sign; **a Notification Center module is being designed, so Lane C recommends waiting.** An ADR amended in its first week costs the ADR's authority, and **nothing is lost by waiting for a design that was announced.**

### 5d · An endpoint's existence is evidence about the backend, never about the screen

**Learned 2026-08-04, twice in one day, and both times before implementation.**

**[412](architecture/412-backend-capability-matrix.md) placed two screens in wave 1 by counting the routers that appeared to serve them.** Reading the screens instead:

| | |
|---|---|
| **Account 360** | Eight endpoints, yes — **and 27 sections, of which eleven are served, two are blocked by O1, and seven have no source anywhere** ([414](architecture/414-wave-1-account-360.md) §0) |
| **AI Research** | A built router, yes — **researching one account, where the approved screen researches a cohort and reports what its members share** ([416](architecture/416-ai-research-scope-gap.md) §0) |

> **The matrix's unit — routers and events — is right for planning and wrong for placement.** A module can be complete, tested and published and still not answer the question its apparent screen asks.

**So: before a screen enters a wave, read its sections against the contracts that would serve them.** Not the module's name, not its endpoint count, not whether it has an `interface/` layer. **Each correction cost a document because it was caught early; either would have cost a slice if caught during implementation.**

### 5e · Product-Led Domain Discovery — planning runs from the finished experience backwards

**Ratified 2026-08-05, product owner directive. A change in planning *methodology*, and explicitly not a change in governance.** The register it produces is [442](architecture/442-product-led-domain-discovery.md), and it is **continuously evolving** rather than a one-time assessment.

> **The approved UI is now the primary source of product requirements.** **Start from the finished product experience and derive the domain model, bounded contexts, entities, workflows, contracts, events, permissions, APIs, AI capabilities and foundation that must exist so the frontend can actually function.**

**What changes is the direction of enquiry.** Product Office was reacting to implementation — *this task needs a contract, this module needs an export, this dependency blocks another task.* **Those responsibilities remain in full.** What is added is the other direction: **given the approved experience, what must exist underneath it?**

**§5b is not superseded and this is the distinction that matters.** *"Think in modules, not screens"* is still how work is **planned and cut**. **Discovery reads the screens; preparation still proceeds module by module** — a screen is where a requirement is *found*, never where a package is *scoped*.

#### The ladder, and the gate at the bottom

**Do not stop at APIs.** *"An endpoint"* is not a finding. **Keep asking until the answer is a domain concept:** what is it showing → what relates to what → what lifecycle exists → what events record the change → who may cause it → what must survive it → **and what would five screens each build separately.** **APIs are outputs of the model, never the model.**

> ## ⛔ **Every rung passes the reuse gate before it becomes a finding: *does the repository already have this, under another name?***
>
> **Test by concept, never by the name you expect.** **442 reported triage as missing because `class TriageState` and `class Snoozed` returned nothing** — `signal_engine` has **`Resolution`, `Actioned`, `Assigned`, `Snoozed`, `Dismissed` and `DismissalReason`**, and had them all along. **That is [B-101](BUGS.md) inside the instrument built to find missing concepts**, and it is the failure mode this method is most prone to: **a discovery document that invents a duplicate is worse than no discovery document**, because it arrives with evidence attached.

#### The standing artifact — ratified [D-076](DECISION_REGISTER.md)

> **[`docs/DOMAIN_DISCOVERY_REGISTER.md`](DOMAIN_DISCOVERY_REGISTER.md) is the register, and it is Lane C's.** **Part A** maps every approved screen to the domain capabilities and platform services it requires · **Part B** reads the product as one system · **Part C** is the architectural radar.

**Discovery became the *primary* planning methodology on 2026-08-05, not an additional one.** **Two sentences frame it and each guards a different failure:**

> **The architecture enables the product** — *"the product should not be constrained by accidental gaps in today's backend."* **And the backend does not mirror pixels** — *"your responsibility is to derive the correct **reusable** domain."*

**Without the first, the product is quietly cut down to what the backend already does. Without the second, the domain becomes a transcription of a layout** — sixteen screens, sixteen shapes, and the reuse policy is gone.

**Study the product as one coherent system.** *"Do not analyse screens independently."* **The most valuable findings only appear when the `required` column is read down rather than across** — [442 §F1](architecture/442-product-led-domain-discovery.md) is the worked example: the AI contract and the bulk-edit contract are the same contract, and screen-by-screen they are two requirements.

**The radar runs ahead, in eight categories**: missing concepts · concepts needing evolution · **concepts arriving too late** · reusable capabilities · cross-module dependencies · regression risks · sequencing · platform opportunities. ***"Do not wait until engineering becomes blocked."***

#### What it is measured by, and the metric changed

> ## **Success is whether implementation reaches a feature and finds the foundations already there.**
>
> ***"Success is not measured by the number of backlog items created."*** **An architectural surprise during implementation is a miss by this office, and it is the only miss that counts.**

**A discovery that produces one ruling and no tasks has succeeded if it stopped a concept being built twice.** **A register row is never a task, and rows are never a productivity measure.**

**Six measures, not one** ([D-081](DECISION_REGISTER.md) §6): **architectural surprises prevented · unnecessary capabilities removed before implementation · repository reuse increased · foundational concepts identified early · multiple consumers building on shared capabilities · implementation arriving to find the foundations already there.**

> ### ⛔ **An earlier finding is never preserved because it exists.**
>
> ***"The objective is architectural correctness, not historical consistency"*** ([D-081](DECISION_REGISTER.md) §1). **[447](architecture/447-signal-center-traceability-audit.md) invalidated [446](architecture/446-companies-traceability-audit.md) within the hour and that was the most valuable thing it did.** **A register that only accretes is a register nobody can trust to be current.**

**The corollary, and it is the harder half:** **a candidate that turns out to be already built is a *result*, not a wasted pass.** **Six of the fourteen foundations the product owner listed were already in the repository, one is forbidden by the ratified Statelessness principle, and one is declared-and-unbuilt with its reason written into `timeline`'s own code.** **Reporting that ratio honestly is the reuse policy working.**

**The ranking function is [441 §5 · P-01 · Domain precedence](architecture/441-people-roadmap.md), applied as a sort rather than as a rule checked afterwards**: a finding's priority is *how many approved screens would otherwise build their own version of it.*

#### The two boundaries this does not move

**Everything in §5b's last paragraph still binds** — Lane C identifies missing APIs, events, workflows, orchestration, repositories, permissions, integrations, security, validation, public contracts, dependency edges **and now domain concepts**, and nothing else. **It does not redesign UX, and it prepares rather than decides.**

**And a discovery is not a licence to build.** *"Do not implement them immediately. Instead, plan them before dependent work begins."* **A finding becomes a backlog row only when it names its screens, its trigger and its reuse verdict** — and a 🔴 finding with no ruling behind it is stated as alternatives with a recommendation, **never as a design.**

### 5f · The Screen-by-Screen Domain Traceability Audit

**Ratified 2026-08-05, product owner directive ([D-078](DECISION_REGISTER.md)). Permanent, and an extension of §5e rather than a replacement.**

> **Every approved UI screen undergoes a complete architectural traceability audit *before implementation reaches it*.** **When implementation begins on a screen, the required domain model and platform foundations should already exist.**

**Every screen is its own investigation. Never assume another screen covered it** — the convergences in [442 §Part B](DOMAIN_DISCOVERY_REGISTER.md) were found by auditing screens separately and *then* reading across them, and they would have been invisible either way alone.

#### The seven columns

**Every element gets a row: ① what is displayed · ② the *business* concept it represents, never the UI · ③ its single source of truth · ④ the repository verdict · ⑤ the owning module · ⑥ every consumer, not just this screen · ⑦ whether it must exist before implementation reaches it.**

| Verdict | Means |
|---|---|
| ✅ **Exists** | Nothing required |
| 🟡 **Extend** | **The architecture is right. Extend, never duplicate** |
| 🟠 **Conflicts** | The current design does not support the approved experience. **Recommend evolution, with evidence** |
| 🔴 **Missing** | Prepare the work |
| ⬜ **Not yet extractable** | **The repository cannot evidence what the screen does.** ⛔ **Record it. Never resolve it with a plausible guess** ([D-079](DECISION_REGISTER.md)) |

**③ admits exactly one answer** — domain entity · aggregate · value object · workflow · projection · knowledge graph · platform service · AI capability · computed view · external provider · derived data. **Two sources is the defect, not the answer.**

#### Workflows are audited too, and they find what fields cannot

**Twelve dimensions: inputs · outputs · business events · state transitions · domain rules · validation · permissions · side effects · notifications · AI interactions · background jobs · audit.**

> **[445 §2](architecture/445-ai-copilot-traceability-audit.md) is the worked example.** Two gaps appeared only when the flow was read end to end — **nothing records that a question was asked**, and **nothing separates reading an answer from spending a model call.** **Neither is a field, so neither could appear in the matrix.**

#### The reuse search, and it is exhaustive before anything is proposed

**Eight searches: bounded contexts · platform capabilities · domain concepts · value objects · workflows · business events · projections · existing ADRs.** **Only after all eight is new work proposed.**

#### ⛔ The rule that protects the matrix

> **Never invent a UI element.** **A row for something the repository cannot evidence puts a fabricated requirement into the one document implementation is meant to trust** — which is worse than a missing row, because it will be built.
>
> ⚠️ **The approved designs are an external project.** The repository holds **section-level detail for one screen** — Account 360, via [414](architecture/414-wave-1-account-360.md) — **and assertions for the other fifteen.** **Every row cites its evidence, and the audit *is* the extraction**: each screen's matrix becomes the repository's record of that screen's elements.

#### ⚖️ Challenge the *implementation*, not the screen ([D-080](DECISION_REGISTER.md) §3)

> **Do not assume the existing architecture is always correct.** If the approved experience shows a foundational capability is missing or wrongly placed, **bring it forward with evidence.**
>
> **And the other half is narrower than [D-079](DECISION_REGISTER.md) first framed it.** ⚠️ ***"Continue challenging implementations, not the UI."*** **The approved UI describes the intended product experience. It does not prescribe implementation** — so the target of a challenge is **the obvious implementation**, never the screen.
>
> **Product Office reconciles product vision with architectural integrity — it does not favour one blindly.**

**Two worked examples, and both take the same form.** **[446 §3](architecture/446-companies-traceability-audit.md)**: *import* reads as a file upload, and built that way it is a second inbound path for customer data — **two provenance stories for one fact.** **[447 §3](architecture/447-signal-center-traceability-audit.md)**: *"snoozed signals return at the stated time"* reads as a scheduler, **and `signal_engine` already answered it with a read-time predicate that needs no scheduler at all.**

> **Each time, the screen was right and the obvious implementation was wrong.** **That is the shape to look for**, and it is why the frame matters: *"the UI is wrong"* invites a redesign nobody asked for.

**A challenge is a recommendation with evidence, never a refusal to build.**

#### Before proposing infrastructure — four questions ([D-081](DECISION_REGISTER.md) §2)

> **Does this mechanism already exist elsewhere? · Is there an existing lifecycle expressing the same behaviour? · Can this be a reusable *predicate* rather than a new runtime capability? · Can existing platform behaviour satisfy it?**

**[447 §0](architecture/447-signal-center-traceability-audit.md) is why they are written down.** **[R-03](DOMAIN_DISCOVERY_REGISTER.md) was one audit away from acquiring a scheduler**, and the third question removed it: `Snoozed.until` proves a deadline is a read-time predicate. **`cron`, `scheduled_for`, `wake_at` and `due_at` return zero repository-wide.**

> ## **Removing an unnecessary capability before it is implemented counts as much as finding a missing one** ([D-081](DECISION_REGISTER.md) §6).

#### At every human completion point — four more ([D-081](DECISION_REGISTER.md) §4)

> **Should this emit a business event? · Which downstream consumers require it? · Does an equivalent already exist? · Can existing event infrastructure be reused?**

**Reusable domain events, never feature-specific notifications.** **[R-14](DOMAIN_DISCOVERY_REGISTER.md) is what these found**: two screens whose completion point is a human decision, and **neither emits an event because no consumer had appeared when they were built.** **Both now have one.**

#### Partial evaluation must never look complete ([D-081](DECISION_REGISTER.md) §4, [D-082](DECISION_REGISTER.md) §4)

> **Whenever a capability cannot evaluate every criterion, the platform states exactly what it evaluated and what it did not.**

**⚠️ This is not a new principle. It is the most-rediscovered one in the repository** — **[449 §0](architecture/449-account-360-traceability-audit.md) counts seven independent instances**, and **PS-01 stated the rule exactly**: *"if absence and presence carry the same information, render nothing; **if the absence is the finding, say it**. And **absence can never distinguish itself from failure**."*

**PS-01 and PS-02 are the warning**: two slices, two days apart, fixing the identical shape in **adjacent sections of one page**, because the first ended by calling the second *"a different question."* **It was the same question.** **Every audit checks for the eighth instance.**

#### Three standing artifacts ([D-085](DECISION_REGISTER.md))

| | Answers | Where |
|---|---|---|
| 🎯 **Trigger Register** | ***What observable condition makes this capability necessary?*** ⛔ **Never an anticipated need** | [Part B-4](DOMAIN_DISCOVERY_REGISTER.md) |
| 🚦 **Foundation Readiness Matrix** | ***If engineering started this screen today, which foundations are complete and which still need to exist?*** | [Part C-1](DOMAIN_DISCOVERY_REGISTER.md) |
| 📖 **Canonical Domain Vocabulary** | ***Is this business concept named the same way in every bounded context?*** **Complements [ADR-0034](architecture/adr/0034-ubiquitous-language.md); never replaces it** | [Part B-5](DOMAIN_DISCOVERY_REGISTER.md) |

> **Confidence in the readiness matrix is a statement about *this office's evidence*, not about the screen.** **An unaudited screen is ⬜ and says so** — the same discipline as ⬜ *not yet extractable*, one artifact up.

#### 📄 A Context Definition before implementation ([D-091](DECISION_REGISTER.md))

> **Every foundational capability gets one *before* implementation begins, and it is the implementation contract** — *"rather than allowing individual slices to redefine the capability as they progress."*

**Eleven fields**: purpose · **bounded responsibility** · ⛔ **explicit non-responsibilities** · public interface · owning context · expected consumers · lifecycle · **events produced** · **events consumed** · repository reuse · implementation constraints.

> ⚡ **The non-responsibilities do the work.** **[455](architecture/455-context-definitions-r02-r03.md)'s two definitions are held small entirely by what they refuse**: the saved-view store *"never parses, validates, executes or ranks a declaration"*, and the action batch *"never knows how to reverse"* the change it records.

#### 🔗 Implementation independence ([D-091](DECISION_REGISTER.md) §4)

> **Multiple lanes must be able to build against a capability without coupling to it.** **So slice 1 of every foundational capability is the `public/` contract and nothing else.**

**A consumer lane can compile, type-check and write its tests against a published port before a row is persisted.** ✅ **`lint-imports` proves the coupling never forms and `mypy --strict` proves the contract is honoured** — stronger than a convention, and how this repository already works.

#### ⚖️ Foundation Criticality — five dimensions, not one ([D-089](DECISION_REGISTER.md))

> ***"A capability inherited by many screens is important. A capability without which the platform cannot operate is foundational. Those are related but not identical."***

**Leverage · architectural criticality · risk of delaying · implementation complexity · expected future reuse.** **Scored in the [Domain Coverage Matrix](DOMAIN_DISCOVERY_REGISTER.md).**

#### The shell presents; it does not own

> ***"Is this actually a shell feature? Or is the shell merely the consumer of a reusable platform capability?"***

**[452](architecture/452-app-shell-traceability-audit.md) is the worked example** — background activity looked like a shell widget and is [R-03](DOMAIN_DISCOVERY_REGISTER.md)'s read surface. **[453 §3](architecture/453-opportunity-intelligence-traceability-audit.md) applies the same test to an ordinary screen**, because it decides ownership there too.

#### 📊 Reuse density ([D-082](DECISION_REGISTER.md) §5)

**Per foundational capability: consuming screens · consuming workflows · dependent modules · implementation status · planned wave.** **Maintained in [Part C-2](DOMAIN_DISCOVERY_REGISTER.md), and it becomes the Domain Coverage Matrix at ten screens.**

> **Its purpose is to separate a platform foundation from a feature.** **The first measurement earned itself immediately**: the highest-density concept in the product — **[R-15](DOMAIN_DISCOVERY_REGISTER.md), at seven instances — has zero implementations**, because every instance was written separately.

#### Two sweeps every audit runs ([D-080](DECISION_REGISTER.md) §4, §5)

| | Look for |
|---|---|
| **Lifecycle** | **temporal workflows · background execution · scheduled transitions · long-running operations · reversible actions · approval workflows · compensation workflows** |
| **Authorization, beyond CRUD** | **spend · field-level · quantity or bulk · AI capability · workflow · approval** |

> **Ask of each: should this become a reusable platform authorization capability, or is it feature-specific?** ⚠️ **[447 §5](architecture/447-signal-center-traceability-audit.md) shows the discipline cuts both ways** — Signal Center's authorization gap is *a missing `Resource`*, which is **the existing model applied**, not a new dimension. **Not every authorization gap is architectural, and saying so is what keeps [R-13](DOMAIN_DISCOVERY_REGISTER.md) honest.**

#### Findings, in ten categories

**Existing · extension candidates · architectural evolution · missing foundational capabilities · missing workflows · missing entities · missing business events · missing permissions · missing projections · missing platform capabilities.**

**A concept that multiple screens require stops being a feature.** **It goes on the [radar](DOMAIN_DISCOVERY_REGISTER.md) as a candidate foundation and is sequenced ahead of its consumers.**

#### After the discovery phase — four standing responsibilities ([D-092](DECISION_REGISTER.md))

**[461](architecture/461-product-led-domain-discovery-review.md) closed the screen-by-screen phase.** **Discovery was a phase; stewardship is not.**

**① Watch the triggers** — ten recorded, two fired. **A trigger firing is the signal to prepare, and nothing else is.**
**② ⚡ Defend the Context Definitions** — **a capability erodes through its non-responsibilities, one reasonable exception at a time.** **When a slice asks the action batch to know what it is reversing, that is the moment.**
**③ Audit each newly approved design on arrival**, one at a time — **a screen audited before implementation costs a document; audited after, it costs a slice.**
**④ Keep the vocabulary graph current and let it fail** — [452](architecture/452-app-shell-traceability-audit.md) found a collision the graph missed because neither term was registered, **and that is how the register earns entries.**

> ⛔ **Stop at 🏛️ Established.** **Re-proving a settled capability is the one activity this office must now refuse.** ***"Once a capability reaches Architecturally Established, the burden of proof shifts from proving it again to protecting its boundaries."***

#### Extended to eight, 2026-08-06 ([D-099](DECISION_REGISTER.md))

> ***"Going forward I expect Product Office to shift from discovery to stewardship."***

**The four above stand and are unchanged.** **Four more are added, and each is a duty this office was already performing without a line saying it must.**

**⑤ Protect established domain boundaries** — ②'s general form, applied beyond the Context Definitions to every 🏛️ Established capability.
**⑥ Review implementation proposals against the approved Context Definitions** — **including [§6a](#6a--reviewing-implementation-preparation)'s four reachability checks**, which are what C-332 cost.
**⑦ Maintain queue health as an operational metric** — **[§11](#-queue-integrity-is-a-standing-operational-duty-d-097)'s six causes, and *"implementation lanes should not reach a genuine zero-`READY` state without Product Office immediately investigating why."***
**⑧ ⚡ Proactively identify future foundational capabilities before implementation reaches them** — **the only forward-looking duty in the list, and the one the other seven exist to make affordable.**

> ## **The measure changed with them.**
>
> ***"The goal is no longer discovering everything. The goal is ensuring the architecture remains coherent as implementation accelerates."***
>
> ⚡ **Which is why ⑧ is not a licence to reopen discovery.** ⛔ **[D-093](DECISION_REGISTER.md) still forbids a broad initiative.** **The difference is scope: ⑧ acts on a *named, approaching* consumer — a trigger that fired, a design that arrived, a lane about to reach a gap — and never on a survey.**

#### ⚠️ A missed foundation is a Product Office finding ([D-093](DECISION_REGISTER.md))

> ***"If implementation reaches a feature and discovers a missing foundational concept that reasonably should have been identified during Product-Led Domain Discovery, that should be treated as a Product Office finding and analyzed so the methodology continues to improve."***

**[C-332](LANE_COORDINATION.md) is the first, and it arrived on the day the phase closed.** **[461 §9a](architecture/461-product-led-domain-discovery-review.md) records it**: [443](architecture/443-account-matching-capability.md) made a function pure *specifically* to avoid an import contract — *"the facts are handed to it"* — **and never asked who hands them.**

> ⚡ **Second instance of one failure mode**, with [C-417](LANE_COORDINATION.md): **a boundary designed without asking who stands on the other side of it.**

**So every Context Definition now carries one more line: *who constructs each input to this capability's public interface, and may they reach it?*** **A purity that removes an import contract from the implementation can move the problem to the caller.**

#### The success criterion, restated

> **Product implementation becomes largely an exercise in assembling existing capabilities rather than inventing architecture during development.**
>
> **An audit that produces no backlog row has succeeded if every element traced to something that already exists.** **[445](architecture/445-ai-copilot-traceability-audit.md) produced none** — twelve elements, and everything missing was already carried by a row somebody else had raised.

### 5g · Canonical Vocabulary Governance — prevention, not detection

**Ratified 2026-08-05, product owner directive ([D-086](DECISION_REGISTER.md)).** *"Our objective is no longer just to detect vocabulary conflicts. Our objective is to **prevent them from being introduced in the first place**."*

> ## **[`docs/coordination/vocabulary.toml`](coordination/vocabulary.toml) is the register, and [`infra/vocabulary-check.py`](../infra/vocabulary-check.py) reads it.**
>
> **A TOML file rather than a table, and the reason is the repository's own**: `vocabulary.test.tsx` exists because ***"a glossary nobody can violate is documentation pretending to be code"*** ([ADR-0034](architecture/adr/0034-ubiquitous-language.md)). **A markdown table is a glossary. This is a check.**

**It is a first-class artifact on the footing of `modules.toml`, the ADRs, the Discovery Register, the Readiness Matrix and the Trigger Register.** **It complements [ADR-0034](architecture/adr/0034-ubiquitous-language.md): that governs the words a *customer* sees; this governs the words *bounded contexts share*.**

#### Six questions, before any new term enters the repository

**① Does this concept already exist?** — search entities, value objects, enums, events, aggregates, permissions, workflows, APIs, UI copy, ADRs, the backlog and the register. **Reuse is the default.**
**② Is this the same concept under a different name?** — *owner · administrator · assignee · responsible · primary · lead · coordinator · manager · custodian*. **Accidental synonym, or genuinely different?**
**③ Is one word carrying two concepts?** — unify, rename, or **qualify**.
**④ Is it scoped correctly?** — **`context-specific` where it belongs to one module; `canonical` only where it must be shared.** ⛔ **Avoid unnecessary global vocabulary and duplicated local vocabulary alike.**
**⑤ Does the name describe responsibility rather than implementation?**
**⑥ Will future AI reasoning understand it?** — the domain model is increasingly what a model reads.

#### From vocabulary governance to **semantic** governance ([D-087](DECISION_REGISTER.md))

> ***"The objective is no longer simply preventing duplicate words. The objective is preventing duplicate business concepts."*** **Two words may be one concept; one word may be two concepts when qualified.** **Review business meaning, not spelling.**

| | |
|---|---|
| 🆔 **Concept Identity** | **Every term carries a stable `concept`** — `PERSON`, `ICP_EVALUATION`, `WORKSPACE_OWNER`. **The wording may change; the concept does not**, so documentation, prompts, UI copy and implementation cite something that does not move, **and a rename stops being a migration** |
| 🕸️ **Concept relationships** | `parent` · `related` · `consumed_by` · `produces_event`. **The register is a semantic graph, not a glossary** |
| ❓ **The question it exists to answer** | ***"If this concept changes, what else is affected?"*** — **before implementation begins.** `vocabulary-check.py --impact ICP_EVALUATION` |

> ⚠️ **The impact query walks *inbound* edges, and the direction is the point.** **A term's own `parent` and `related` lists say what it depends on — the easy half.** **What a change *costs* is everything pointing back at it, and no single row can show that.**

#### Vocabulary review is part of every screen audit, not a separate activity

**Four questions on every newly discovered concept:** **is it actually new · does another module already own this *business meaning* · does the repository express the idea differently · should this extend existing vocabulary instead of adding a term.**

#### Eight statuses

**`proposed` · `reserved` · `canonical` · `context-specific` · `alias` · `qualified` · `deprecated` · `rejected` · `historical`** — **an explicit lifecycle, so terminology evolves deliberately rather than by drift.** *(`historical` was added by [D-087](DECISION_REGISTER.md): a word that was true then and is not now, kept so old records stay readable — the vocabulary form of §2's *date a record, never rewrite it*.)* — and **every owned term names a bounded context from `modules.toml`, or `platform` for a word no single module can rule on.**

#### The review gate

> **Before a backlog row introduces terminology: is it already defined · does it conflict · is it reusable · does another module own it · does it need qualification · does it need architectural review?**
>
> ## **The preferred outcome is *"no new vocabulary required."***

#### ⚠️ What the checker deliberately does not do

**It makes no judgement it cannot defend from a grep.** **A synonym is a judgement** — question ② is Product Office's, not a script's. **And it fires on a *declaration*, never on a mention**, because a docstring naming another context's concept is how this repository explains itself.

> **Its first run found three things and two were its own bugs**: a `reserved` term names a context that deliberately does not exist yet, and **a *canonical* term appearing in many modules is the success case, not the defect** — `Dismissed` is in `signal_engine` precisely because [417](architecture/417-executable-slice-audit.md) refused a second dismissal vocabulary. **A canonical term spreading is the goal; a context-specific one escaping is the defect.**

---

## 6 · Feature decomposition

**Converting a product initiative into implementation-ready work.** Each package carries:

**objective · customer value · architecture · existing foundation · modules · dependencies · backend · frontend · workflows · UX · acceptance criteria · risks · future evolution · suggested lane · estimated effort · open questions.**

> **The reuse audit ([L-1](../ENGINEERING_LAWS.md)) comes first, and it is usually the whole finding.** The Product Capability Audit found *fifteen modules, eighty-two events and twenty-four endpoints behind five screens* — **the platform is short of surface, not capability.** A decomposition that proposes building something already computed and unexposed has skipped the only step that mattered.

**A slice is only implementation-ready when a lane that has never seen the module could start it without asking a question.** If it could not, the missing sentence is the deliverable.

---

## 6a · Reviewing implementation preparation

**From 2026-08-04, product owner directive** ([429](architecture/429-distributed-delivery-model.md)). **The Product Development lane prepares its own modules; Lane C reviews the package and sets `READY` or `REVISION REQUESTED`.**

**Twelve checks, and each is a question the repository answers rather than an opinion Lane C holds:**

**repository reuse** · **bounded contexts** · **architecture** · **API contracts** · **public contracts** · **dependency correctness** · **domain consistency** · **UI/backend alignment** · **smallest executable slice** · **governance compliance** · **implementation sequencing** · **module boundary.**

> **The one rule that decides whether review stays review:**
>
> **Lane C does not rewrite a package unless governance requires it.** The test is *would this, as submitted, breach a rule the repository can name?* — **and if the answer is *"it is not how I would have done it"*, the correct output is approval.**
>
> **A review that rewrites is preparation wearing a review's clothes.** It restores the bottleneck the model was created to remove, one round-trip later and with the owning lane's work discarded — **and the owning lane knows its module better, which is the directive's own argument.**

### The four reachability checks, on every Context Definition ([D-099](DECISION_REGISTER.md))

> ***"Continue validating that Context Definitions identify who owns the capability, who constructs every input, who consumes every output, and whether all required dependency edges already exist. I want these checks to become part of the standard Product Office review process going forward."***

**These are not four of the twelve above. They run in addition, on any package that defines or extends a capability**, and they are asked in this order because each one's answer constrains the next.

| | The check | ⛔ What it refuses |
|---|---|---|
| ① | **Who owns the capability?** | An owner chosen because a lane arrived at it first. **Ownership is an architectural decision, never an implementation accident** ([D-090](DECISION_REGISTER.md)) |
| ⚡ ② | **Who constructs every input?** | **A named type with no producer anywhere in the repository** |
| ③ | **Who consumes every output?** | A published contract nothing calls — and, on [P-C](DOMAIN_DISCOVERY_REGISTER.md), **an event declared before a consumer exists** |
| ⚡ ④ | **Do all required dependency edges already exist?** | A design whose ownership and inputs are both correct **and where the constructor may not reach the module holding the facts** |

> ## ⚠️ **② and ④ exist because their absence produced [C-332](../docs/LANE_COORDINATION.md), and it is this office's own miss.**
>
> **`evaluate(icp, observed)` is `PROMOTED` and correct. Nothing constructs an `ObservedAttributes`, and `opportunity_engine` — the module ruled to do the measuring — is forbidden from `knowledge_graph`, the only module that could build one.**
>
> ⚡ **And the cause is worth more than the finding: [443](architecture/443-account-matching-capability.md) made the function pure *specifically* to satisfy the import contract, and never asked who would hand it the facts.** **Passing ④ by construction is what made ② invisible** — the boundary was clean because nothing crossed it, including the data.

**Second instance of one failure mode, with [C-417](LANE_COORDINATION.md): a boundary designed without asking who stands on the other side.** **Two instances is why this is a standing check rather than a lesson.**

**Two queues are reported every cycle, and Lane C computes both because each measures Lane C:**

| Queue | What a growing one means |
|---|---|
| **Review Queue** — packages awaiting Product Office | ⚠️ **Product Office has become the bottleneck again, at approval instead of authorship.** The one risk this model takes |
| **Synchronization Queue** — approved and not yet on `integration` | **The failure the model was created to end**, recurring |

**Both are emitted by `infra/repository-dashboard.py` §9 and §10** — **computed, never a lane's claim about itself.**

---

## 7 · What Lane C never does

**Write production code · modify business logic · implement a feature · merge · certify · change module ownership · reprioritize the roadmap · approve an architectural decision · override an implementation lane · bypass the product owner.**

> **And, from 2026-08-04: rewrite an implementation package it was asked to review.** **The review function is new; the prohibition on becoming an implementation team is not.** Lane C gained a review, not a keyboard.

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

---

## 11 · How Lane C reports

**Ratified 2026-08-04, product owner. Permanent, and reporting-only** — it changes no responsibility, no methodology and no governance rule.

> **The Product Owner must be able to tell, within fifteen seconds and without reading implementation detail, whether any action is required.**
>
> **The dashboard is the authoritative summary. Implementation detail is secondary.** Ordering is what changes; **depth, evidence and repository analysis do not.**

### The order, and it is fixed

**1** Lane Status · **2** Product Owner Dashboard · **3** Executive Summary *(≤5 bullets)* · **4** Priority Dashboard *(P0–P4)* · **5** Dependency Matrix *(a table)* · **6** Lane Availability · **7** Implementation Detail · **8** Decisions Made · **9** Risks *(≤3)* · **10** Final Status Line *(one sentence)*.

### Execution Buffer Health — mandatory whenever a lane reports `WAITING`, `BLOCKED` or `IDLE`

**Ratified 2026-08-05, product owner.** ***"A lane becoming idle is not merely an implementation event — it is a planning signal."*** **The goal is to make repository throughput measurable.**

```text
Execution Buffer Health
  Assigned queue size:
  Immediately executable:
  Blocked assignments:
  Dependencies preventing execution:
  Estimated slices released by resolving each dependency:
  Primary bottleneck:
  Recommended Product Office action:
```

**And when a lane's queue is exhausted because everything left is blocked, that is *not normal lane behaviour*.**

> ## **An exhausted queue is a Product Office capacity finding, and it is stated as one.**
>
> **Assigned queue exhausted · the reason it cannot be replenished · which dependency prevents replenishment · which Product Office backlog item resolves it · how many slices that would release.**

**The five fields live in the lane's queue file as a `[capacity_finding]` table**, not only in a report — **a finding that exists only in prose is a finding nothing can check.** `lane-a.toml` carries the first one.

> ⚠️ **The distinction that makes the finding useful.** *"Blocked"* and *"empty"* are different diagnoses and only one of them is the product owner's. **Lane A's queue on 2026-08-05 was neither** — its rows were `CLAIMED`, `IN VALIDATION` or another lane's, and **the honest bottleneck was that Product Office had not prepared the next slices.** **Reporting that as a dependency would have pointed at the wrong person.**

### 🚦 Queue integrity is a standing operational duty ([D-097](DECISION_REGISTER.md))

> ***"Product Office should proactively validate repository state rather than waiting for implementation lanes to identify the issue."***

**Every summary reports queue health.** **And when a lane reports no claimable work, a stale queue, a wrong eligible count or a dependency inconsistency, Product Office validates *before* replying** — `python3 infra/state-check.py`, which carries C-333's eight queue checks.

> ⚠️ **The distinction that matters, and Lane A is the worked example.** **Its queue read 0 of 5 and that was *correct*** — the only two startable rows on the board are in Lane B's modules. **What was wrong was the bookkeeping beside it**: a `PROMOTED` row and two `IN VALIDATION` rows sitting in `held`.
>
> ⚡ **And the first seven checks passed it, because they validated `current`/`next`/`future` and never read the arrays describing what a lane is *not* doing.** **A queue is not only a list of what to take; it is a claim about everything else, and that claim was unchecked.** **Check ⑧ exists because a queue this office had already corrected once was still wrong.**

**A lane must never appear to have executable work when it has none, nor appear empty when executable work exists.** **The second is a Product Office capacity finding; the first is a defect.**

#### The six causes, ruled out one at a time ([D-099](DECISION_REGISTER.md))

> ***"Implementation lanes should not reach a genuine zero-`READY` state without Product Office immediately investigating why… Whenever a lane becomes `WAITING` because of planning rather than engineering, investigate."***

**A lane is not reported as correctly waiting until all six have been checked and the check is recorded.** *"The queue says zero"* is the beginning of the investigation, never its conclusion.

| | Cause | The question that tests it |
|---|---|---|
| ① | **Stale dependencies** | **Is any named blocker already resolved?** Read the register, not the queue — **the queue is the thing suspected of being wrong** |
| ② | **Incorrect queue ordering** | Is a startable row sitting below an unstartable one? |
| ③ | **Decomposition opportunities** | **Is there a smaller piece inside a blocked row that needs none of what blocks it?** |
| ④ | **Resequencing opportunities** | Would a different order let work begin without changing scope or priority? |
| ⑤ | **Reusable preparatory slices** | **Is prepared work sitting outside `integration`?** Prepared work that has not reached `integration` does not exist (§12) |
| ⑥ | **Outdated blockers** | **Is a blocker's *note* still true, even where its identifier still exists?** |

> ⚡ **① and ⑥ are different questions and the difference cost a day.** **① asks whether the blocker was resolved. ⑥ asks whether the sentence describing it is still accurate** — and a `C-nnn` can remain legitimately open while the reason it blocks has inverted.

##### The worked example, and it is this office's own

**Run 2026-08-06 against Lane A, which had read `0 of 5` for two cycles.**

| | |
|---|---|
| ① **Stale dependency** | ⚡ **Found.** `TASK-400`'s entry named **`C-321`**, which was **`RULED` on 2026-08-05** — *"Adopt Lane B's proposed behaviour. Proceed."* **The A6 half had been executable for a full day while the lane's own file said otherwise** |
| ⑥ **Outdated blocker** | ⚡ **Found, and it is the more serious one.** The entry read *"Lane C is not holding it, because no proposal has been brought."* **The proposal was brought on 2026-08-05.** `C-219` is still legitimately open — **but the holder had inverted, and the note named the wrong lane** |
| ②③④⑤ | **Checked and clear.** Ordering correct · [455](architecture/455-context-definitions-r02-r03.md)'s slices already decomposed and blocked on a ruling rather than on preparation · no resequencing available without touching priority · nothing prepared sitting off `integration` |

> ## ⛔ **The conclusion was not *"Lane A is idle."* It was that Lane A had executable work it could not see, and that the item blocking the rest was sitting with the office running the investigation.**

⚠️ **And the count was right the whole time.** `eligible_count = 0` **counts claimable `TASK-nnn` rows, and a review obligation is not one** — so an office holding the single item blocking another lane reports itself as empty, **correctly, by the schema.** **Recorded and not fixed**: the freeze wants an *observed* execution problem, and **one observation is not evidence.** **If a second review obligation goes unseen the same way, that is the trigger.**

### 🔗 Dependency reporting — eleven fields, always ([D-099](DECISION_REGISTER.md))

> **Whenever a report states a dependency, a waiting state or a blocked condition, it carries all eleven.** *"This has become one of the most valuable parts of the status reporting and should remain standard."*

```text
  Dependency:              the identifier — C-nnn · TASK-nnn · B-nnn
  Current Owner:           the lane or person who can move it, TODAY
  Category:                governance · architecture · ownership · synchronization
                           · external · product decision · repository health
  Affected Tasks:          every id it holds, not only the nearest
  Current Status:          the state that identifier is actually in
  Why it blocks:           the mechanism, not the label
  Expected Next Action:    what happens next, and who does it
  Product Owner action?    YES with one sentence of why · or NO
  Product Office action?   YES with one sentence of why · or NO
  Decomposable further?    YES — naming the smaller piece that could start
                           now · or NO, with the reason
  Impact if unresolved:    what it costs to leave it — and the honest form,
                           which is often "throughput, not product"
```

**Three fields were added 2026-08-06 and each closes a specific way the eight-field form failed.**

| Field | What it caught that the eight could not |
|---|---|
| **`Category`** | **Eight items all reading *blocked on the product owner* are not one queue.** A governance dependency and an architectural one need different responses, and the old form flattened them |
| ⚡ **`Product Office action?`** | **The one that matters most, and it is the mirror of the field beside it.** *"Product Owner action? NO"* previously read as *nobody need do anything* — **and on 2026-08-06 the item blocking Lane A's render was sitting with this office**, described in its own queue as waiting on Lane A. **A report with no field for its author's own obligations will not surface them** |
| **`Decomposable further?`** | **Asked prospectively rather than after a lane goes idle.** [455](architecture/455-context-definitions-r02-r03.md)'s slice 1 — the `public/` contract alone — is what this field is looking for, and it existed for a month before anybody asked whether a smaller piece could start |

> **The ranking field exists because the others describe a dependency and none of them ranks it** ([D-095](DECISION_REGISTER.md)). **Two items can both be `READY FOR PRODUCT DECISION`, both owned by the product owner, and one unblocks seven slices while the other tidies a document.**

> ⚠️ **`Why it blocks` and `Expected Next Action` are the ones that get skipped, and they are the ones that matter.** **A report saying *"blocked on C-417"* names something; a report saying *"C-417 is `READY FOR PRODUCT DECISION` and blocks because the platform edit's proof lives in five files this lane may not touch"* lets somebody act without opening a second document.**

> ⚠️ **The fourth and fifth fields are the ones that get skipped, and they are the ones that matter.** **A report saying *"blocked on C-417"* names something; a report saying *"C-417 is `READY FOR PRODUCT DECISION` and blocks because the platform edit's proof lives in five files this lane may not touch"* lets somebody act without opening a second document.**

### The rules that carry the weight

| | |
|---|---|
| **§2 is mandatory and binary** | 🔴 **action required** — with the decision, why, options, recommendation and cost of delay — or 🟢 **no action required.** Never absent, never hedged |
| **No hidden decisions** | If §2 says no action is required, **the report asks nothing later.** A question buried in implementation detail is a decision the Product Owner never saw |
| **Not everything is urgent** | Implementation · monitoring · polling · validation · background preparation · blocked work · decisions **are different states and must read differently.** A report that sounds the same every time carries no information in its tone |
| **§8 exists because of this office's own history** | Corrections and withdrawals were previously found inside implementation prose. **Accepted · rejected · withdrawn · corrected · clarified**, listed — because a correction nobody noticed is a correction that did not happen |
| **§9 is risks, not observations** | Three maximum. **A finding is not a risk unless it can still cost something** |
| **Confidence below High needs one sentence** | Stating *why* is the whole value; a bare *Medium* is a mood |

### Its relationship to the Standard Lane Report

**`CLAUDE.md` §20e — the Standard Lane Report — binds every lane and is authoritative for the header, the close and the closing line.** **This section does not restate it** (§2). What lives here is only what is **Lane C's alone**: the ten-section body order, and §11a's Portfolio Dashboard.

> **Adopted repository-wide 2026-08-04.** The sequence the product owner set — *use it · evaluate whether it genuinely improves decision-making · recommend only if it does* — **completed in one step**, because the product owner directed adoption before Lane C reached the evaluation. **The recommendation was never made, and the record says so rather than implying the office earned the outcome.**
>
> **Lane C drafted the amendment; it did not decide it.** `CLAUDE.md` is the product owner's and the drafting route is the one §20e names — *only when the product owner has approved it, never on its own initiative.*

**Notification is the amendment.** Lane C has no channel to Lane A, Lane B or QE — **the product owner is the shared channel**, and `CLAUDE.md` is what every lane reads at Startup step 1. **A lane that rebases onto this commit has been told.**

### 11a · The Portfolio Dashboard

**Ratified 2026-08-04, product owner. Permanent, and reporting-only.** **It sits inside the Executive Summary, between §3 and the detail** — eight sections: module portfolio · epics · active slices · decision queue · implementation readiness · module health · **priority for the Product Owner** · changes since last report.

> **The repository has outgrown narrative updates.** The dashboard exists so the whole portfolio is legible in under a minute. **It never replaces the detailed report, which remains the authoritative explanation.**

**Three rules, and the third is the one that protects the repository:**

| | |
|---|---|
| **No separate dashboard document** | It lives **only** in the report. A dashboard file would be a fourth record of repository state, and there are already three with one responsibility each |
| **Every item gets exactly one priority** | 🔴 action now · 🟠 review soon · 🟡 information · 🟢 no action. **Priorities are never mixed within an item** |
| **Lane C's figures are estimates, and must say so** | — |

#### Why the third rule exists, and it is not pedantry

**`CLAUDE.md` §20e gives repository-wide state to QE, exclusively, measured from the promoted commit:** *"a dashboard assembled from lane reports is a sum of intentions."* **`PROJECT_STATUS.md` is that dashboard and this is not a second one.**

**So the Portfolio Dashboard reports two kinds of number and never blurs them:**

> **Counted** — register rows, task ids, endpoints, contracts, ADRs. **Read from the repository at report time, and re-read every time.** Never transcribed from the last report.
>
> **Estimated** — module and epic progress percentages. **Lane C's judgement about maturity, marked as such, and never a planning commitment.** Where one would contradict `PROJECT_STATUS.md`, **the measurement wins and the estimate is wrong.**

**A percentage that starts being quoted as a measurement has become the defect this rule prevents.** The Operational Reading Cost table (§10) is the worked example of getting this wrong once already: **its first published figure understated its own headline by a third, and it was found by re-running rather than rereading.**

### 11b · The UI Implementation Dashboard

**Ratified 2026-08-04, product owner. Permanent, reporting-only, and in every future report.**

> **At any point the product owner should understand, in under a minute, how much of the approved product has actually been implemented.**

**Seven parts:** summary counts · per screen · module summary · overall progress · wave summary · **READY FOR IMPLEMENTATION** · **BLOCKED SCREENS**.

#### The rule that makes it worth having

> **Measure against the approved design project. Never estimate from assumption.**

**A screen is `DONE` when it matches the approved specification** — not when something with its name exists. **The repository contains provisional UI built before the design project existed, and [413](architecture/413-migration-inventory.md) classifies all of it `REPLACE`.** Counting it as progress would make the dashboard describe a product nobody approved.

**So on the day convergence begins the honest number is zero, and the dashboard says zero.** A dashboard that opens at 40% because screens with matching names exist has failed at its only job.

#### Its relationship to the other dashboards

**It does not restate them** (§2). The Portfolio Dashboard (§11a) reports **modules, epics and decisions**; this reports **screens against a specification**. Where a fact belongs to one, the other references it.

| | |
|---|---|
| **Informational only** | **It assigns nothing, creates no slice, and estimates nothing from opinion.** A screen appearing under **READY FOR IMPLEMENTATION** is a measurement, not an allocation — allocation is still the product owner's |
| **State changes are reported** | Every move — `READY → IN PROGRESS → BACKEND COMPLETE → INTEGRATED → QE → DONE` — appears under *Changes Since Last Report*. **A screen that changed state silently is the thing this dashboard exists to prevent** |
| **Backend and frontend readiness are separate axes** | Because they diverge, and the repository's whole history is that divergence: **46 endpoints behind 11 routes.** Collapsing them into one percentage would hide the only interesting fact |

### 11c · Five states, never conflated

**Ratified 2026-08-04, product owner, after Lane A challenged a Lane C report.** **The challenge was correct and the correction is recorded here rather than argued.**

> **Prepared · Ruled · Recorded are three different facts, and a report that blurs them tells a lane it may proceed when the repository does not yet say so.**

| State | Means | Set by | A lane may act? |
|---|---|---|---|
| **PREPARED** | Lane C has produced the analysis, options and recommendation | **Lane C** | **No.** A recommendation is not a decision |
| **READY FOR PRODUCT OWNER** | Complete, alternatives assessed, nothing unresolved left in it | **Lane C** | **No** |
| **PRODUCT OWNER APPROVED** | **The product owner has ruled.** Authoritative from that moment | **Product owner** | **In principle — but see the next row** |
| **MERGED TO INTEGRATION** | Recorded where lanes read: `origin/integration` | **QE** | **Yes** |
| **AVAILABLE FOR IMPLEMENTATION** | Approved **and** merged **and** its `TASK-nnn` is claimable | — | **Yes, and only here** |

#### The rule that follows

> **A decision is authoritative when the product owner rules it. It is *actionable* when `integration` records it.** Those are different days, and **Lane C reports both, always.**

**The Task Claim Protocol claims from `integration`** (`CLAUDE.md` §20e, step 1: *synchronize*). **A `TASK-nnn` existing only on `lane-c-product-office` is invisible to every lane, and reporting it as `READY` overstates what any lane can do.**

**Never write *"ratified"* alone.** Write **"ruled 2026-08-04; not yet on `integration`"** — a cold session reading `RATIFIED` reasonably assumes the repository agrees, and until the merge it does not.

**Never write *"unblocked"* to mean *"a ruling exists"*.** **`Blocked: 0` is a claim about `integration`, not about the product owner's inbox.**

#### Why this was Lane C's error, not a labelling preference

**The rulings were real** — all nine were ruled explicitly. **What was wrong was the inference**: the report said the queue was empty, Epic C released and Lane B unblocked, while **57 Lane C commits — including the ADRs themselves — had never reached `integration`.** Lane A could not see ADR-0400 at all.

> **Preparing a decision well does not make it available.** Reporting as though it does is the same defect as a dashboard describing the previous milestone (`CLAUDE.md` §2) — **the repository asserting something that is not true of it.**

---

## 12 · Implementation flow

**Ratified 2026-08-04, product owner.** **A change of prioritisation, never of authority** — Lane C still prepares, still assigns nothing, and still bypasses no rule.

> **The governance has successfully prevented architectural drift and exposed a new bottleneck: implementation lanes can idle while the Product Office prepares.** **Correctness is not the only thing this office is measured on. Throughput is the other.**

### The self-check, before any new package, assessment or ADR

> **Are implementation lanes fully utilised?**
> **YES** → continue. **NO** → **stop, and prepare executable work instead.**

**It is asked first, every time, and its answer is measured rather than assumed** — which means reading `origin/integration`, because **that is what a lane can claim from.**

### Implementation Support Mode

**Entered automatically when Lane A or Lane B is idle for lack of executable work** — no claimable `READY` task, no active implementation, waiting only on documentation, synchronization, assignment or preparation.

> **Idle is not the same as blocked.** A lane waiting on an external system or a genuine product decision is **not** idle; a lane waiting on Lane C is.

**While active, priority is fixed:** ① produce executable `READY` work · ② convert approved preparation into claimable work · ③ synchronize repository state · ④ remove unnecessary waiting · ⑤ unblock implementation. **Only then does planning resume.**

**Paused while it is active** — new discovery · new initiatives · speculative assessments · roadmap expansion · future package preparation. **Unless the product owner asks for one**, in which case it is not speculative.

### The READY buffer

**Target: five claimable slices per implementation lane.** **Below that, replenishing is the highest Product Office priority.**

> **Claimable, not prepared.** A slice on a Lane C branch is not a slice a lane can take — `CLAUDE.md` §20e's five states, and the distinction Lane A's challenge established. **Counting preparation as buffer is how this office would fool itself.**

### 12a · The pipeline is continuous, never a batch

**Ratified 2026-08-05, product owner — [D-070](DECISION_REGISTER.md).**

> **"Do not wait because the current queues look sufficient."** **"The moment one item leaves `PREPARING`, the next candidate should enter `PREPARING`."** **"I do not want only 2 or 3 assigned tasks… If twenty tasks are independently executable, then twenty tasks should already be assigned."**

**The five-slice target is a floor, not a cap.** Every eligible task is assigned to a lane queue the moment it becomes eligible. **A queue is never trimmed to look tidy.**

**The eligibility test, and all five must hold:**

| | Test | Checked against |
|---|---|---|
| ① | **Approved** | `BACKLOG.md` status, or a product owner ruling |
| ② | **No unresolved architectural dependency** | `LANE_COORDINATION.md`, the item's own `Blocks` field |
| ③ | **No product owner decision pending** | the blocker's `Owner` row |
| ④ | **Assignable safely** | [`modules.toml`](coordination/modules.toml), joined — **never a stored assignee** |
| ⑤ | **Violates no ownership or governance rule** | §20e, §20a, the change budget |

> **A task failing only ② or ③ is not dropped — it is carried in the queue's `blocked` array with its blocker and that blocker's owner.** **Everything a lane owns appears in one file**, so a dependency is visible before it is met rather than discovered on claiming.

**And the narrowing rule, which is where most of the buffer actually comes from:** **a task whose halves have different blockers is carried at the buildable half's scope, not held whole.** `TASK-400` is the worked example — [C-219](LANE_COORDINATION.md) says *"A7 proceeding, A6 held"*, and reading the item rather than the row's status field moved a whole task from `blocked` to `future`. **This is sequencing, not preparation: Lane C narrows the scope and names the evidence; the owning lane still writes the package** ([D-060](DECISION_REGISTER.md) is untouched).

### 12b · A shortfall is a finding, and it names its cause

**Below the five-slice target, the report says so** — per lane, with the number, and **with the reason attributed.**

> **The distinction that makes the finding useful:** **a shortfall caused by under-preparation is this office's defect.** **A shortfall caused by an unanswered ruling is not** — and reporting the two the same way would hide the only one anybody can act on.

**So every shortfall is reported with the blocked tasks that would clear it and who owns each blocker.** **If the blocked column is upstream, the finding is addressed upward, not absorbed.**

### 12c · A dependency never idles a lane that owns other work

**When an assigned task becomes blocked:** ① **document the dependency** · ② **follow dependency resolution** (§1) · ③ **ownership does not change** unless the product owner decides otherwise · ④ **the lane moves to its next assigned task immediately.**

> **Nothing waits for Lane C in that sequence**, which is the point. **The lane advances first and the paperwork follows.**

### 12d · Derivable is not visible

**The queue files exist so no lane has to join ownership to find its own work.** Both lanes idled on 2026-08-05 with claimable tasks in modules they owned, **because the backlog rows name modules and the lanes were reading for their own name.**

> **A queue nobody reads is a queue that was not published, however correct its contents.** [C-329](LANE_COORDINATION.md) — Lane B reported an empty queue **while `lane-b.toml` named `TASK-408` as its current task.** The file was on `integration` and the polling procedure did not point at it.

**So publishing is not complete until the procedure a lane runs names the file.** §20e's polling steps are the delivery mechanism; the file is only the payload.

### Synchronization is a first-class concern, and it is Lane C's to notice

**Prepared work that cannot reach `integration` is unavailable, and unavailable work is indistinguishable from work that does not exist.**

> **Never assume another lane owns that observation.** The 2026-08-04 incident — 57 commits, eight prepared slices, and both lanes unable to see any of them — **was reported by Lane A, not by the office that created it.**

**Report `PREPARED` · `PRODUCT OWNER APPROVED` · `MERGED TO INTEGRATION` · `CLAIMABLE` separately, always.**

### The pipeline, and the question to ask of it

```
Ideas → Architecture → Preparation → READY → Lane A / Lane B → QE → Integration → Main
```

> **Whenever one stage accumulates while the next is empty, name it explicitly** — with the stage, the reason, and a priority. **An empty stage downstream of a full one is the definition of a bottleneck**, and it is visible only to whoever is looking at both.

### A clarification is answered, not escalated — the QE gates case

**2026-08-04.** QE asked whether three `infra/` defects it had just fixed — `certification-guard.py`, the runbook, `validate.py` — become Lane C's under [D-022](DECISION_REGISTER.md).

**It is a Category 1 repository clarification and was answered rather than escalated**, because both rules already exist and reading them together changes no ownership, boundary, concept, contract or invariant: **§20e's *QE removes its own blockers* is untouched by D-022**, and §20e already classes *fixing a gate* as a slice.

> **D-022 filled a gap; it did not take QE's instruments.** `infra/` had no assignable lane and four defects landed there. **QE's gates were never in that gap.**

**Worth recording for how QE raised it, not only what it asked.** It declined to open a coordination item **because the ruling is on a lane branch and not on `integration`** — *"filing against text that hasn't merged is precisely the 'approved is not merged' confusion"*. **That is §11c applied correctly by a lane that did not write it**, which is the strongest evidence the rule is legible.

### Prepared work that has not reached `integration` does not exist

**Ratified 2026-08-04, product owner** — `CLAUDE.md` §20e, *Executable work comes from `integration`*.

> **It is not buffer. It is not capacity. It is not a reason a lane should wait.**

**Lane C caused an idle lane by treating its own branch as though it were the repository.** Lane A's unblock conditions named `TASK-405`, `TASK-406` and `ADR-0400` — **all three on `lane-c-sync`, none on `integration`** — so it polled correctly and waited on nothing claimable.

**Two obligations follow, and both are this office's:**

> **① Synchronization outranks the office's own queue** whenever a lane has been idle for more than one reporting cycle on work that exists only outside `integration`. **Above further preparation, above new initiatives, above everything.**
>
> **② Lane C reports the condition itself.** On 2026-08-04 it was reported by Lane A — **the lane that was starving noticed before the office that was starving it.**

**And the measurement discipline that would have caught it:** *throughput is not availability.* The flow audit read commit history, saw five slices land, and concluded the lanes were flowing. **They had flowed, that morning, and then run out** — a lane's *availability* is what it can claim now, never what it shipped earlier.

### The dashboard reports execution state, never planning state

**Corrected 2026-08-04, product owner, after Lane C reported `Claimable: 7` while both implementation lanes reported that nothing could be claimed.** **Both statements cannot be true, and the lanes were right.**

#### Claimable has one definition

> **A task is `Claimable` only if it is on `origin/integration`, `READY`, unclaimed, in a module the claiming lane holds or that no lane holds, with no unmet dependency and no deferral against it.**

**Everything else is a different stage and is counted as one.** The failure was counting `READY` in a file as claimable by anybody — **`READY` is a status; claimable is a fact about a particular lane on a particular day.**

#### Activity and capacity are separate rows

**Never report a lane as `Working` when it is polling.** Both, always:

```text
Lane A
  Current Activity:        Polling
  Implementation Capacity: Idle
  Reason:                  No claimable work on integration
```

> **A lane that is busy and a lane that has capacity are different facts**, and collapsing them hides the only one that needs action.

#### The Synchronization Pipeline is a permanent section

**Prepared → Product Owner Approved → Merged to Integration → Claimable → Claimed → In Progress → QE → Main.** **Actual repository state at every stage, counted, never planned.**

> **A full stage above an empty one is a bottleneck**, and the pipeline exists so it cannot be described any other way.

#### Implementation Support Mode triggers on either condition

**Either implementation lane has no executable work on `integration`** — **or synchronization is the bottleneck between Product Office and implementation.** **The second is the one this office will miss**, because from inside the preparation stage everything looks full.

> **Prefer operational truth over planned capacity. An optimistic count is worse than no count** — it reports health that the lanes can see is absent, and the office loses the credibility its numbers depend on.

### What this does not change

**No rule is relaxed.** Reuse first · no regression · public contracts · bounded contexts · ADR compliance · import rules · tenancy · security · evidence before assumptions · smallest executable slice · no speculative abstraction · no duplicate concepts.

> **Throughput is never bought with governance.** A slice produced to fill a buffer, that a lane then has to unpick, has reduced throughput — **and the office would have measured itself as succeeding while doing it.**

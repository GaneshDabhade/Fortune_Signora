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

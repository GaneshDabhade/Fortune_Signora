# 490 · The Product Office operating model, critiqued

**Lane C · Product Office · 2026-08-07.** **[D-171](../DECISION_REGISTER.md), which asks for this in its own closing paragraph: *"critique it as if you were an independent Chief Product Officer and Chief Architect… then adopt the strongest model rather than following these instructions mechanically."***

> ⛔ **This is a critique, not a counter-proposal to the direction.** **Nine of the twelve sections are right and are adopted unchanged.** ⚠️ **Six weaknesses are named, each with repository evidence, and each with the amendment this office is adopting unless overruled.**

---

## 0 · The six, before the reasoning

| | | |
|---|---|---|
| **①** | ⛔ **§1's uniform pipeline depth will produce stale plans, and this session already proves it** | **Depth-graded decomposition** |
| **②** | ⚠️ **§12 gives one office six continuous duties and no capacity model** | **Name the contention out loud** |
| **③** | 🔴 **§9 asks the audit to catch what a file-reading office cannot see** | **Say what it cannot catch, and close the gap in QE** |
| **④** | 🔴 **§2/§3's *"identify before consumption"* is speculative generality — and this repository has already paid for it twice** | **Identify early, extract at the second consumer** |
| **⑤** | ⚠️ **§11 contradicts the governance freeze in `CLAUDE.md`** | **The ruling must say it supersedes it** |
| **⑥** | ⚠️ **[D-169](../DECISION_REGISTER.md) removed the gate and nothing replaced it as a bound on feedback latency** | **A soft cap of two unreviewed workflows** |

---

## 1 · ⛔ Uniform pipeline depth produces stale plans

**§1 requires every upcoming workflow to carry twenty-three artifacts** — journey decomposition, business objectives, epics, tasks, slices, dependency graph, acceptance criteria, reuse, accessibility, responsive, animation, testing strategy, and eleven more — **so that *"implementation can begin immediately without requiring additional analysis."***

**With twenty-seven workflows that is 621 prepared artifacts.** ⚠️ **The cost is not the objection. The staleness is.**

> ### **Evidence, from this session and this repository.**
>
> **`docs/BACKLOG.md` has 284 commits. `TASK-467`'s row alone has been rewritten in 10 of them** — **and it is the *active* workflow, planned six days ago.**
>
> **What rewrote it: [D-153](../DECISION_REGISTER.md) made it a replacement rather than a refinement · [D-154](../DECISION_REGISTER.md) forbade starting from the legacy screen · [D-156](../DECISION_REGISTER.md) widened its scope from three screens to four · [D-158](../DECISION_REGISTER.md) re-sequenced it · [D-161](../DECISION_REGISTER.md) put a foundation row in front of it · [D-169](../DECISION_REGISTER.md) changed its release condition.**
>
> ⛔ **Six rulings in one session revised the plan for the workflow currently being built.** ⚡ **A workflow ten slots away would have been revised twenty times before anyone opened it — and every revision is planning work spent twice.**

**This is not an argument against planning ahead. It is an argument that *fidelity* should decay with distance, because *certainty* does.**

### ✅ Adopted — depth-graded decomposition

| Distance | What is prepared | Why |
|---|---|---|
| **Active + next** | ⚡ **All twenty-three artifacts.** §1 in full | **Near-certain. This is where §1's value is real** |
| **N+2 to N+4** | **Journey · screens · states · dependencies · platform capabilities · reusable components · backend and API requirements** | **Enough that a decomposition is a day's work, not a week's** |
| **Beyond N+4** | **Journey identified · design named · blockers named · platform capabilities named** | ⛔ **Anything more will be rewritten before it is read** |

⚡ **The two things that *must* be deep everywhere are exactly the two §2 and §3 care about: platform capabilities and dependencies.** **Those are what change slowly and what other workflows inherit.** ⛔ **Acceptance criteria and animation specifications for workflow 22 are not.**

⚠️ **[`workflows.toml`](../coordination/workflows.toml) already encodes this honestly** — **nineteen workflows read `planned` rather than `decomposed`, and that field was written to stop a full-looking pipeline being built on optimistic states.** ✅ **The amendment makes the ruling agree with the file.**

---

## 2 · ⚠️ Six continuous duties, one office, no capacity model

**§12: *"Product Office continuously researches · continuously plans · continuously decomposes · continuously improves architecture · continuously governs design · continuously prepares future implementation."*** **Six, all continuous, all one session.**

> ### **Evidence: nineteen rulings — [D-151](../DECISION_REGISTER.md) through [D-171](../DECISION_REGISTER.md) — landed in this session, and each consumed a cycle.**
>
> ⚡ **Almost every cycle went to *processing a ruling* rather than to the research the ruling asked for.** ⛔ **[D-168](../DECISION_REGISTER.md) requested three decision packages; [D-170](../DECISION_REGISTER.md) and [D-171](../DECISION_REGISTER.md) arrived before the first was written.**

⛔ **This is not a complaint and the rulings were right.** ⚠️ **It is a structural observation: Product Office is simultaneously the *research* function and the *ruling-response* function, and those compete for the same cycles.** **The model has no statement about which yields.**

### ✅ Adopted — the contention is reported rather than absorbed

**Every report names what research advanced and what did not, and why.** ⚡ **This document is the first instance: the Security Center package is still not written, and the reason is that three operating-model rulings arrived first.**

⚠️ **The alternative — silently deprioritising research to answer rulings — is how a planning function becomes a secretarial one**, and neither of us would see it happen.

---

## 3 · 🔴 §9 asks the audit to catch what this office cannot see

**§9: *"I should never discover Design System deviations during manual review if they could reasonably have been detected beforehand."***

⛔ **The word *reasonably* is carrying the whole sentence, and it should be replaced with a list.**

> ### **This office cannot see a rendered screen.** **It has said so since [487 §1](487-legacy-ui-migration-status.md) and it is still true.** **The conformance audit reads files.**

| ✅ **The audit reliably catches** | ⛔ **The audit cannot catch** |
|---|---|
| **Wrong token values** — it found 7 in [TASK-491](../BACKLOG.md) | **Correct tokens composed into a wrong layout** |
| **Literal colours, arbitrary sizes, `!important`, inline `style`** | **A jarring transition, or one that fires twice** |
| **A missing breakpoint** *(zero in `app/(auth)/` before Workflow 1)* | **A layout that breaks at 900px while having all three breakpoints** |
| **A missing component or an absent state** | **A state that renders but reads wrong** |
| **Vocabulary, via `vocabulary.test.tsx`** | **Focus that lands somewhere legal and unhelpful** |

⚡ **The first review found a legacy palette — a file-level fact, and the audit now catches that class.** ⛔ **A future review will find something in the second column, and §9 as written would read as an audit failure when it is an audit *limit*.**

### ✅ Adopted — and one proposal that would close most of the gap

**The audit report states, every time, which checks ran and which classes it cannot cover.** ⛔ **A gate that overstates its coverage is worse than one that admits a gap** (§2).

> ⚡ **The proposal: screenshot diffing belongs in QE, and the harness already exists.** **`frontend/tests/e2e/visual.spec.ts` is in the repository today, and [D-153](../DECISION_REGISTER.md) already gives QE *"visual regressions (where applicable)"*.** **A per-workflow baseline captured at certification would catch most of the right-hand column** — ⛔ **and it is QE's to build, not this office's, because how QE certifies is not this office's to specify** (§20e).

---

## 4 · 🔴 *Identify before consumption* is speculative generality, and this repository has paid twice

**§2: *"Platform capabilities should be identified before individual screens consume them."*** **§3 applies it to sixteen security capabilities.**

⛔ **`CLAUDE.md` §6 forbids the adjacent thing in terms: *"Do not add abstractions, configuration flags, or generalization for hypothetical future needs."*** **And the repository has a recorded, twice-paid precedent:**

> ### **`CLAUDE.md` §6, on ports:** ***"This was learned twice — `15-project-structure.md` placed both the Provider Port and the AI Provider Port in platform packages that were never built, and the implementation put each in its owning module both times."***

⚡ **That is exactly §2's failure mode: a capability identified as platform *before* a consumer existed, placed in the platform, and wrong both times.**

### ✅ Adopted, with the distinction that makes it safe

| | |
|---|---|
| ✅ **Identify at planning time** | **Name the capability, name which workflows will consume it, name where it would live.** ⚡ **This is §2's real value and it costs nothing to be wrong about** |
| ⛔ **Do not *build* it at the first consumer** | **Build it inside the first workflow that needs it, shaped so it can move** |
| ⚡ **Extract at the second consumer** | **The second consumer is the first evidence that the abstraction is real.** **One consumer is a guess; two is a shape** |

⚠️ **The exception, and it is genuine: a *contract* that two lanes must agree on is different from an *implementation* two workflows share.** **A contract is designed up front or two lanes ship incompatible halves — which is [C-213](../LANE_COORDINATION.md)'s two-day cost.** ✅ **So: contracts early, implementations at the second consumer.**

---

## 5 · ⚠️ §11 contradicts the governance freeze

**§11 asks Product Office to *"periodically evaluate how Product Office itself can become more effective"* and to bring forward better planning, governance, decomposition, review and dependency models.**

⛔ **`CLAUDE.md`'s governance freeze says the opposite, in a paragraph naming this office:**

> **"Prohibited unless a significant issue is discovered *during implementation*: large governance redesigns · workflow redesigns · execution-model redesigns · organizational restructuring."** **And: *"Evolving the delivery model is not among [Lane C's standing responsibilities]."***

⚠️ **[D-171](../DECISION_REGISTER.md) is the product owner's and supersedes it — but only if it says so.** ⛔ **A cold session reading `CLAUDE.md` finds the freeze, reads §11 in a register it may not open, and resolves the contradiction conservatively.** ⚡ **That is the same defect [C-432](../LANE_COORDINATION.md) just cost a cycle to fix, one section away.**

### ✅ Adopted — recorded in the register, and offered for `CLAUDE.md`

**This document records the supersession.** ⛔ **The freeze's paragraph is the product owner's to amend, and the wording is offered rather than written** — **one sentence: *the freeze bars redesign argued from theory; it does not bar improvement argued from measured execution evidence, which §11 requires.***

⚡ **And the freeze's underlying rule is worth keeping rather than deleting: *a governance change needs an observed execution problem, not a foreseeable one*.** ✅ **Every improvement this office brings will carry the evidence, which is what §11 asks for anyway.**

---

## 6 · ⚠️ Nothing bounds how far implementation runs ahead of feedback

**[D-169](../DECISION_REGISTER.md) removed the approval gate — correctly. §12 says the product owner reviews *"meaningful customer journey milestones."*** ⛔ **Neither states how many unreviewed workflows may accumulate.**

⚡ **The safety property is real and already in place: [D-161](../DECISION_REGISTER.md) ④ and [D-162](../DECISION_REGISTER.md) ④ require a mismatch to be fixed in the foundation or a shared component, never on a screen — so a correction propagates to everything built meanwhile.** ⚠️ **That bounds the *cost* of a token or component finding. It does not bound the cost of a finding about a *journey* — that the flow is wrong, a step is missing, the sequence confuses people.** ⛔ **No foundation fix propagates that.**

### ✅ Adopted — a soft cap, reported rather than enforced

> **When three customer workflows sit on `main` unreviewed, Product Office says so in its report and recommends a review.** ⛔ **It does not stop implementation** — [D-169](../DECISION_REGISTER.md) is explicit that only the product owner pauses the migration.

⚡ **Three rather than two, deliberately**: **two is the natural steady state once Lane A is one workflow ahead of a review, and a threshold that fires in the normal case is one people read past** — **the failure this office corrected in its own pipeline check the day it wrote it.**

---

## 7 · ✅ What is adopted unchanged, and why it is worth saying

**§4 commodity-versus-differentiation · §5 repository-wide reuse · §6 research before recommending · §7 challenge the direction · §8 implementation never waits · §10 think beyond the current workflow · §12's role split.**

⚡ **§7 is the one that changes this office's behaviour most, and this document is its first exercise.** **Nineteen rulings in one session were implemented without a single disagreement recorded** — ⛔ **and an office that never disagrees is either always right or not looking.**

⚠️ **§4's classification is adopted with one refinement: *Commodity · Platform Extension · Domain Differentiator* is missing the category most of the security list falls into** — **capabilities that are commodity in *mechanism* and differentiating in *presentation*.** **Session revocation is Better Auth's; the screen that shows a seller which devices hold their pipeline data is Signora's.** ✅ **The Security Center package will classify mechanism and surface separately rather than forcing one verdict per capability.**

---

## 8 · The single strongest objection, if only one survives

> ## ⛔ **§1 and §9 both ask for a completeness this office cannot honestly deliver — one because plans decay, the other because it cannot see a screen.**
>
> ## ⚡ **Both are safe once stated as limits rather than promised as coverage. Neither is safe if a review or a slice discovers the limit instead.**

**Everything else in [D-171](../DECISION_REGISTER.md) makes the repository better, and the platform-first direction in §2 and §3 is the most valuable thing in it** — **provided the abstraction is *named* early and *extracted* late.**

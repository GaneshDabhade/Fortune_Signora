# Decision Packs — architectural decisions, grouped

> **For the product owner. Prepared and maintained by QE.**
>
> **The problem this solves:** thirty-two open coordination items, presented one at a time over weeks, each needing context rebuilt from scratch. **They are not thirty-two decisions.** Grouped by the question actually being asked, they are **five** — and three of the five have a recommendation the repository's own evidence supports.
>
> **QE owns the process, never the decision.** Every pack states a recommendation because a pack without one is a question wearing a suit; **none of them is acted on until you rule.**

**Reviewed against `main` at `d39b136`, 2026-08-03.**

---

## 0 · What the review changed before any decision was needed

**Seven items were closed on repository evidence, not on your time.** Each was verified against shipped code, not against its own description.

| Item | Why it is closed | Evidence |
|---|---|---|
| **C-024** — Timeline has nowhere to mount | **Implementation answered it.** The feed is mounted on the account brief | `accounts/[accountId]/page.tsx:335` renders `AccountHistory`; the rationale is in the file, Option A chosen, B and C ruled out |
| **C-026** — Connection Center reachable only by URL | **Shipped as CX-01** | `settings/page.tsx:148` links it |
| **C-019** — a claim is invisible to arbitration | **Superseded by governance** | Claims now push to `integration`; `certification-guard.py --audit-claims` enforces the boundary |
| **C-006** — which lane owns `test_api_<module>.py` | **Answered by `CLAUDE.md` §20e** | *"QE creates repository-wide automated tests; lanes own the tests specific to the slices they implement"* |
| **C-022** — which governance rules are in force | **The governance is on `main`** | *Execution ownership ends at `IN VALIDATION`* and *Continuous execution* are both promoted |
| **C-201** — identifier collision is only *unlikely* | **Made impossible** | Block allocation ratified in `CLAUDE.md`; `state-check` rules 5e/5f detect any residue |
| **C-001** — the target-account contract | **Ratified as ADR-0036** | Already `ANSWERED`; only the move to `Closed` was outstanding |

> ⚠️ **C-024 is the one I got wrong, and it is worth stating plainly.** I escalated it in **two consecutive cycle reports** as *"the sharpest item — ten lines of routing separate a working capability from a customer."* **Lane A had already mounted it**, and said so in its handoff. I was reading the register instead of the repository, which is the exact failure [L-2](../ENGINEERING_LAWS.md) exists to prevent — **written by me, violated by me, in the same week.**

**Net effect: 32 open items → 25**, with no decision required from you.

---

## 1 · The consolidation — 25 items, 5 decisions

**The largest finding of this review is that most remaining items are not independent.** They are one architectural question surfacing in several modules, and answering them one at a time means answering the same question repeatedly with no guarantee of consistency.

```
  PACK A · The platform freeze          C-012 · C-013 · C-021 · C-207
  PACK B · Roadmap row → milestone      C-020 · C-023 · C-200
  PACK C · Customer vocabulary          C-002 · C-018 · C-204 · ADR-0041
  PACK D · Unassignable code            C-010 · C-004 · C-014 · C-006*
  PACK E · Product surface calls        C-008 · C-011 · C-017 · C-205 · C-206
                                        ( * C-006 closed above; listed for its ruling history )
  Independent, not packable             C-003 · C-005 · C-007 · C-009 · C-025 · C-203
```

---

## 0b · Prioritized — by customer value unlocked, not by dependency count

**Re-validated against `7e43841`, 2026-08-03.** Two items moved on evidence; the estimates below are QE's and are marked as estimates.

| Pack | Customer value unlocked | Modules unblocked | Journeys unblocked | Reversible? | Risk if delayed | Effort after approval |
|---|---|---|---|---|---|---|
| **A** — platform composition | **None directly. Everything indirectly** — no pipeline stage is independently scalable or observable | **7** | 0 today | **Yes** — additive | **Compounding.** 13+ files now carry the workaround, up from 8 | RFC + 2–3 slices, then 7 one-slice rewirings |
| **B** — roadmap → milestone | **None directly.** Releases three stalled milestones | 3 milestones | — | **Yes** — a queue rule | **High.** Three lanes have hit it independently | **Governance only. No code** |
| **C** — customer vocabulary | **High and direct.** Nothing can match an account against an ICP until it is answered — the commercial-profile value proposition | 2 | **ICP → account matching** | Partly — a catalog is diffable | High | 1 slice + a reviewed catalog |
| **D** — unassignable code | None directly | `apps/` · `signora_platform/` · frontend foundation | — | Yes | **Compounding.** 8 defects have landed here | **Governance only** |
| **E** — five product calls | **[C-008](LANE_COORDINATION.md) is the highest single-item customer value on this page** — every AE and SDR, every day | 1–2 each | 1–3 each | Yes | Low each | 1 slice each |

> **If the objective is customer value rather than a shorter register, the order is C → E(C-008) → B → A → D.** That is *not* the order by dependency count, and the difference is the point: **Pack A unblocks the most modules and ships nothing a customer can see**, while [C-017](LANE_COORDINATION.md) is a paste and [C-206](LANE_COORDINATION.md) is one question.

**Two items moved on re-validation** ([`LANE_COORDINATION.md`](LANE_COORDINATION.md)): **C-020 narrowed** — Timeline's design doc now exists, so only ADR-0038's ratification remains — and **C-023 closes**, because it asked whether M13 was executable and Lane B executed three slices of it.

---

## PACK A · Does the platform freeze admit a composition amendment?

**Four items. One question. It is the most expensive open decision in the repository.**

| | |
|---|---|
| **Decision** | **May `signora_platform/` be amended to let a module compose itself into the runtime?** |
| **Background** | §20a froze the platform on completion of M1.3A, permitting only security fixes, production defects and approved architectural change. **Four modules have since hit the same wall from four directions** |
| **Current implementation** | `EventHandler` receives no session ([C-012](LANE_COORDINATION.md), open since **M3A**) · `PublishableEvent` cannot be satisfied by a frozen dataclass ([C-013](LANE_COORDINATION.md)) · an event handler cannot reach a provider adapter ([C-021](LANE_COORDINATION.md)) · Casbin cannot express an action on yourself ([C-207](LANE_COORDINATION.md)) |
| **Repository evidence** | **`make runtime-composition` measures the cost every cycle: 7 of 9 modules that declare consumers are unwired**, and every one names C-012. The deployed worker consumes **2** of them |
| **Options** | **A** — amend the platform once, under one RFC covering all four · **B** — four separate RFCs · **C** — keep the freeze; modules work around it individually · **D** — reclassify the freeze as expired now the platform is proven |
| **Trade-offs** | **A** is one review, one migration, one consistent shape — and a larger single change. **B** guarantees four inconsistent shapes for one problem. **C** is the status quo, and its cost is measured above. **D** discards the guarantee that a module written in M7 behaves like one written in M2 |
| **Repository impact** | 🔴 — `signora_platform/**`, frozen |
| **Customer impact** | **None directly. Everything indirectly**: the pipeline runs in-process, so no stage is independently scalable or independently observable |
| **Engineering impact** | Unblocks 7 modules' event consumption, PP-02's last wire, all of PP-03, C-007's guided first run, and leaving an organization |
| **Migration impact** | Additive. No customer data; no schema change |
| **Risk** | **Low to make, high to defer.** The workaround cost compounds: *"every new event pays it"* (C-013) |
| **Recommendation** | **Option A.** One RFC, four capabilities, one shape. **The freeze is doing its job — it is why this is a decision and not four silent commits** — and a single amendment preserves that while paying the debt once |
| **Future pressure** | **This is the largest architectural pressure in the next six months.** Every module added meets the same wall |
| **Rollback** | The amendment is additive; a module not using the new capability is unaffected |
| **Deadline · urgency** | **Highest urgency of any pack.** Open since M3A — **the longest-running blocker in the repository** |
| **Dependencies created** | An ADR superseding part of §20a |
| **Dependencies removed** | **C-012 · C-013 · C-021 · C-207**, and unblocks C-007 |
| **Effort** | RFC ~1 slice · implementation ~2–3 slices · **7 module re-wirings, one slice each, independently certifiable** |
| **Order** | RFC → platform amendment → re-wire modules one at a time, measuring `runtime-composition` after each |
| **Rejected** | **B**, because four solutions to one problem is the duplication [L-1](../ENGINEERING_LAWS.md) forbids. **D**, because *"a frozen platform is not a finished one — it is one where change requires a stated reason"*, and that sentence is still right |

---

## PACK B · How does a roadmap row become an executable milestone?

**Three items, identical shape: a milestone exists on the roadmap with no scope, no module and no bounded context.**

| | |
|---|---|
| **Decision** | **What must exist before a roadmap row may be claimed?** |
| **Background** | [C-020](LANE_COORDINATION.md) (M7) · [C-023](LANE_COORDINATION.md) (M13) · [C-200](LANE_COORDINATION.md) (M14b). **Three lanes hit this independently**, which by `CLAUDE.md` §20e is the threshold at which governance may evolve |
| **Current implementation** | A roadmap row is prose. `BACKLOG.md` carries `TASK-nnn` with a module. **Nothing connects them**, so a lane claiming a milestone-level task discovers the gap after claiming |
| **Repository evidence** | M14b has *"two roadmap table rows and no scope section, no module and no bounded context"*. **Lane A stopped rather than choosing one** — correctly, because *"every route into implementation decides the boundary by implementing it"* |
| **Options** | **A** — a milestone is not `READY` until it names a bounded context and a module · **B** — a discovery slice is the first slice of every milestone · **C** — case by case, as now |
| **Trade-offs** | **A** front-loads your decision and guarantees no lane discovers a 🔴 mid-slice. **B** legitimises what the lanes already do (all three wrote a discovery document) but spends a slice before scope is agreed. **C** has produced three identical blockers |
| **Repository impact** | 🔴 — the roadmap and `CLAUDE.md` |
| **Customer impact** | None directly. **Three milestones are stalled behind it** |
| **Risk** | Low. It is a queue-admission rule |
| **Recommendation** | **A, with B as the fallback.** A roadmap row becomes `READY` only when it names its bounded context; where you would rather not decide up front, commission an explicit discovery slice. **This is what all three lanes did unprompted** — the rule just stops them discovering it separately |
| **Deadline · urgency** | **High.** M7, M13 and M14b are all held |
| **Dependencies removed** | **C-020 · C-023 · C-200** |
| **Effort** | Governance only — one `CLAUDE.md` amendment. **No code** |
| **Rejected** | **C**, on evidence: three lanes, three identical blockers, three separate discovery documents |

---

## PACK C · Where does customer language meet canonical data?

| | |
|---|---|
| **Decision** | **Which component owns translating a customer's words into a canonical claim?** |
| **Background** | [C-002](LANE_COORDINATION.md) (no anticorruption layer for customer vocabulary) · [C-018](LANE_COORDINATION.md) (nobody owns an attribute's customer-facing name) · [C-204](LANE_COORDINATION.md) (the catalog explains nine words to nobody) · **[ADR-0041](architecture/adr/0041-icp-aggregate.md)** (the model has no place to put an ICP) |
| **Current implementation** | Provider Normalization is an ACL for **vendor** vocabulary and is the clearest in the codebase. **Nothing plays that part for customer vocabulary.** [ADR-0034](architecture/adr/0034-ubiquitous-language.md) put the translation at the frontend edge; `vocabulary.test.tsx` enforces it |
| **Repository evidence** | ADR-0035 answered *resolution among disagreeing claims* (a Knowledge Graph slice) and **not** *whose job it is to know that "Fintech" and the canonical industry value are the same thing*. ADR-0041 reaches the same gap from the ICP side |
| **Options** | **A** — Knowledge Graph owns it (it already resolves) · **B** — a new matching module · **C** — a reviewed catalog of customer terms, owned by the domain expert · **D** — the frontend edge only, per ADR-0034 |
| **Trade-offs** | **D** is the current rule and **is already insufficient** — a browser cannot match an account against an ICP. **C** is what `CLAUDE.md` §2's least-powerful-author rule points at: a reviewed catalog is less powerful than inference and a domain expert signs it. **A** risks AC-28 (*an entity is an identity, not a record*). **B** is a new bounded context, 🔴 |
| **Customer impact** | **Direct.** Nothing can match an account against an ICP until this is answered — which is the whole of the commercial-profile value proposition |
| **Recommendation** | **C**, a reviewed catalog owned by the domain expert, read by the Knowledge Graph. **It is the least powerful author capable of being correct**, it is diffable, and it is the one option ADR-0034 does not contradict |
| **Deadline · urgency** | **High** — it gates ADR-0041, and Lane B is stopped behind it |
| **Dependencies removed** | **C-002 · C-018 · C-204**, and unblocks ADR-0041 |
| **Rejected** | **D**, on evidence that it cannot do the matching. **A**, pending a ruling on AC-28 |

---

## PACK D · Who owns code that belongs to no module?

| | |
|---|---|
| **Decision** | **Assign an owner for `apps/`, `signora_platform/`, the frontend foundation and repository process.** |
| **Background** | [C-010](LANE_COORDINATION.md), open **8 cycles** — the longest-waiting item after C-012 |
| **Repository evidence** | **Eight defects have now landed in this gap**: B-007, B-012, B-013, B-014, B-022, B-025, B-100, B-101. **The last three were all found and fixed by QE in three consecutive cycles** |
| **The compounding cost, precisely** | QE fixes them because nobody else may. **QE cannot verify its own fixes**, so each one waits for a lane to volunteer — which is why [TASK-001](BACKLOG.md) had to be created and why three rows sat unverified for two days |
| **Options** | **A** — QE owns it, and a nominated lane verifies QE's fixes each cycle · **B** — rotate it like any module · **C** — a standing Lane C · **D** — leave it; QE fixes and verification queues |
| **Trade-offs** | **A** matches what already happens and fixes only the verification half. **B** applies the rotation model the repository already runs on. **C** costs a lane. **D** is the status quo, measured above |
| **Recommendation** | **A.** QE already does the work; **name a verifying lane and the gap closes without changing anything else.** [C-004](LANE_COORDINATION.md) and [C-014](LANE_COORDINATION.md) resolve as consequences |
| **Effort** | Governance only |
| **Dependencies removed** | **C-010 · C-004 · C-014** |

---

## PACK E · Five independent product calls

**Not consolidatable — each is a genuine product judgement, and none blocks the others.** Listed with the single question each needs.

| Item | The one question | Blocks |
|---|---|---|
| **[C-008](LANE_COORDINATION.md)** | Who sees the commercial profile — options A/B/C/D stated | Every AE and SDR, every day |
| **[C-011](LANE_COORDINATION.md)** | Should a contraction risk look different from an opportunity? | R9-03 only |
| **[C-017](LANE_COORDINATION.md)** | Ratify the onboarding honesty principle — **text ready to paste as `D39`** | Every future onboarding flow |
| **[C-205](LANE_COORDINATION.md)** | Is Signora expected to work on a phone? | [B-019](BUGS.md) and every responsive decision |
| **[C-206](LANE_COORDINATION.md)** | How is an invitation email delivered? | **Narrowed by Lane A to this alone** |

> **[C-017](LANE_COORDINATION.md) and [C-206](LANE_COORDINATION.md) are the two cheapest decisions in this document.** One is a paste; the other is a single choice Lane A has already reduced from a plugin adoption to an email question.

---

## If you answer only three

1. **PACK A** — it has been waiting since M3A and its cost is measured every cycle.
2. **PACK B** — governance only, no code, and it releases three stalled milestones.
3. **[C-017](LANE_COORDINATION.md)** — ratifiable text, already written.

---

## How this document is maintained

**Refreshed by QE at every Repository Closeout**, against the promoted commit. **Every item is re-challenged, never merely carried forward:** is it still real · still blocking · narrowable · splittable · already answered by implementation, an ADR or a repository rule.

**A pack is deleted when its decision is taken**, and the answer lives in the ADR or document it produced — never here. **This is a staging area, not a record.**

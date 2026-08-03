# Decision Packs — architectural decisions, grouped

> **For the product owner. Prepared and maintained by Lane C** — transferred from QE on 2026-08-03, when decision preparation became the Product Office's (`CLAUDE.md` §20e *Lane C*). **QE's authorship of everything below this line is preserved and is not rewritten**; what changes is who maintains it next.
>
> **The problem this solves:** thirty-two open coordination items, presented one at a time over weeks, each needing context rebuilt from scratch. **They are not thirty-two decisions.** Grouped by the question actually being asked, they were **five** — **four are now ruled and retired below, and one remains.**
>
> **Lane C owns the process, never the decision.** Every pack states a recommendation because a pack without one is a question wearing a suit; **none of them is acted on until you rule.**

**Reviewed against `main` at `d39b136`, 2026-08-03. Retirement pass 2026-08-03 — 183 lines to 68.**

---

## Retired — decisions taken, and where each answer now lives

**Four packs retired 2026-08-03 by Lane C**, under this document's own rule: *a pack is deleted when its decision is taken, and the answer lives in the ADR or document it produced — never here.*

**Three gates were verified before each retirement**, on the product owner's direction: the decision is fully ratified · the follow-up work is tracked elsewhere · no coordination item still sits `OPEN` against it.

| Pack | Items | Decision | Ratified in | Follow-up now tracked as |
|---|---|---|---|---|
| **A** — platform composition | C-012 · C-013 · C-021 · C-207 | One platform amendment, one RFC, four capabilities | [ADR-0100](architecture/adr/0100-delegated-dependency-rulings.md) **R-1** | [TASK-900](BACKLOG.md) *(the RFC)* → [TASK-901](BACKLOG.md) *(seven rewirings)* |
| **B** — roadmap → milestone | C-020 · C-023 · C-200 | A roadmap row is not claimable until it names its bounded context; ADR-0038 ratified | **R-2 · R-3** | [TASK-902](BACKLOG.md) *(M7)* · [TASK-906](BACKLOG.md) *(M14b context)* |
| **D** — unassignable code | C-010 · C-004 · C-014 | QE owns it; a rotating lane verifies QE's fixes | **R-4** | Governance only — no code |
| **E** — five product calls | C-008 · C-011 · C-017 · C-205 · C-206 | Five independent rulings | **R-5 · R-6 · R-7 · R-8 · R-9** | [TASK-903](BACKLOG.md) · [TASK-904](BACKLOG.md) · [TASK-905](BACKLOG.md) |

> **Retiring them was blocked by a defect, and finding it was the more useful half.** All four decisions were ruled on 2026-08-03, and **every one of the fourteen coordination items was still `OPEN` or `WAITING` in the register's own index** — the body recorded the rulings and the index never caught up. **A register whose index disagrees with its own contents is the defect class `CLAUDE.md` §2 names**, and this register has recorded that exact failure against itself once before.
>
> **The index is reconciled to `ANSWERED`, citing the ruling, and no item was moved to `CLOSED`** — that belongs to the requesting lane once the work is built, and it is the difference between *a decision exists* and *the work is done*.

**The deliberation is not lost.** Each pack's options, trade-offs and rejected alternatives are preserved verbatim in `git log` and, where they became architecture, in [ADR-0100](architecture/adr/0100-delegated-dependency-rulings.md) — which states for every ruling whether it rests on **evidence or judgement**, so the judgement ones stay cheap to reverse.

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

---

## PACK F · How should the execution board be structured?

**Commissioned by the product owner 2026-08-03, after [C-401](LANE_COORDINATION.md) measured it as the only textual conflict in 77 commits.**

| | |
|---|---|
| **Decision** | **How is [`ACTIVE_ASSIGNMENTS.md`](ACTIVE_ASSIGNMENTS.md) arranged so two lanes stop conflicting on it?** |
| **Background** | Every lane's rows sit **adjacent in one table**, and each lane's branch carries a snapshot of *every other lane's rows* — including QE's. The conflict hunk read `Cycle 28` against `Cycle 35`, neither of which the conflicting lanes wrote |
| **Repository evidence** | **77 commits · 211 file-touches · +31,623 lines · exactly one conflicting file, both times.** `CLAUDE.md` says *"update only your own row"*, and **the file's shape makes that unexpressible as a non-conflicting diff** |
| **Class** | **Structural risk** ([`PRODUCT_OFFICE.md`](PRODUCT_OFFICE.md) §3) — *design it away*, rather than resolve it every cycle |

| | Option | Readability | Merge behaviour | Maintenance | Discoverability | Scalability |
|---|---|---|---|---|---|---|
| **A** | **One table** *(today)* | **Best** — every lane visible in one glance, sortable by eye | **Worst** — adjacent rows guarantee a conflict whenever two lanes both update | Low, but **a conflict every multi-lane cycle**, resolved by QE who wrote neither row | Best | **Degrades linearly** — each lane added raises collision probability |
| **B** ✅ | **One section per lane**, fixed order, one file | Slightly worse — a heading between lanes; **still one screen at five lanes** | **Disjoint line ranges; git has nothing to reconcile** | **Lowest** — a lane edits only under its own heading | Best — same file, same path | **Flat** — a new lane appends a section |
| **C** | **One file per lane** | **Worst** — no single view; the board stops being a board | **Perfect** — separate files never conflict | Higher — *n* files to open, and a cold session must know they exist | **Worst** — the one document a session reads first becomes a directory | Flat, but the fragmentation compounds |

**Recommendation: B.** It removes the structural cause rather than managing the symptom, **keeps the single-file readability that makes the board useful**, and is a one-off reshape with no new mechanism — `CLAUDE.md`'s *"update only your own row"* becomes true rather than aspirational.

**Rejected: A**, because the conflict is not a git problem and will recur every cycle at increasing cost. **C**, because it solves merges by destroying the property the document exists for — and [`CLAUDE.md`](../CLAUDE.md) §12 forbids new documentation files where an existing one serves.

**Effort** — one reshape of one file, by **QE**, who owns the board's reconciliation. **No lane branch needs to rebase**; the shape changes at merge.

---

## PACK G · The repository's documentation is growing faster than its code

**Raised by the product owner 2026-08-03: *"each file is getting too much inflated… make sure we are not losing any important piece."***

| | |
|---|---|
| **Decision** | **What limits documentation growth without losing a single recorded fact?** |
| **Class** | **Repository Decision** |

**Measured, not estimated:**

| | |
|---|---|
| **Markdown** | **37,267 lines** against 97,437 lines of backend Python |
| **Growth** | `LANE_COORDINATION.md` **0 → 2,968 lines in under three days** · `BUGS.md` **84 → 1,737** · `CLAUDE.md` **561 → 1,371** |
| **Concentration** | **Four files are 20% of all documentation.** In the coordination register, **12 items are 52% of the file**, and the largest — C-025, at 408 lines — **is already closed** |
| **Cold-start cost** | **2,891 lines** before a first commit |
| **Composition** | **§20e is 67% of `CLAUDE.md`.** The constitution is now mostly *how lanes coordinate* rather than *how software is built* |

> **The register's own rule already says it should shrink. The mechanism to make it shrink was never built** — that is the whole finding. Nothing is being lost today; **everything is being kept in the reading path**, which is a different problem with a different fix.

| | Option | Consequence |
|---|---|---|
| **A** | **Do nothing** | Growth is ~3 days old and steep. **The cold-start cost is the tax**, paid by every lane on every rotation, and rotation is the model |
| **B** | **Separate the reading path from the record** — a closed item's *deliberation* retires to a dated archive; the register keeps its **decision and link** | **Loses nothing** — the decision stays visible, the deliberation stays verbatim and dated. It is what §2 already requires: *correct a claim about the present; date a record of the past* |
| **C** | **Operational content leaves the constitution** for the owning lane's procedure document | **Proven this session**: `DECISION_PACKS.md` 183 → 68 · Lane C's `CLAUDE.md` section 92 → 39, **with nothing deleted** — both moved to their owner |
| **D** | **Split large documents by topic** | **Rejected.** Fragmentation raises discoverability cost, and §12 forbids new files where an existing one serves. It converts one big file into five a session must know about |
| **E** | **Summarise in place, keep full text only in git** | **Rejected.** `git log` is not a reading path — *"a record nobody can cite"*. It is the one option that genuinely risks losing something |

**Recommendation: C now, B next.**

**C is already demonstrated and costs nothing** — it is the `QUALITY_ENGINEERING.md` pattern applied consistently, and `CLAUDE.md` already states the principle: *where another document owns operational content, this one references it and never restates it.*

**B is the larger win and needs one ruling:** *where does a closed item's deliberation go?* **Lane C recommends a dated archive per register** — `docs/archive/coordination-2026-08.md` — appended to, never rewritten, with the register keeping one row per closed item naming its decision and linking the archive. **Retiring C-025 alone recovers 408 lines from the path every lane reads before every slice.**

**Not recommended, and stated so it is not proposed later:** a line limit, a documentation gate, or a periodic prune. **A gate on prose measures the wrong thing**, and the repository has just spent a cycle proving that size metrics predict nothing.

**Effort** — C is done. **B is one archive file per register plus a retirement pass**, and is Lane C's to perform once the ruling exists.

---

## PACK H · The coordination register has no retirement — **APPROVED, migration deferred**

> **Approved in principle 2026-08-03, product owner.** The lifecycle **is adopted** and is recorded in [`LANE_COORDINATION.md`](LANE_COORDINATION.md) and `CLAUDE.md` §20e *Coordination*.
>
> **The migration is deliberately not run.** *"Do not begin large-scale archival until the governance model has stabilized — otherwise you'll be moving documents every week."* **Lane C continues measuring and naming candidates and moves nothing.** The resume condition is a cycle passing with no change to the coordination model.
>
> **Retained below as the record of what was approved and why** — it is retired from the staging area once the migration runs.

**Commissioned by the product owner 2026-08-03: *"prepare a simple lifecycle for coordination items… before implementation."***

| | |
|---|---|
| **Decision** | **What lifecycle retires a coordination item, and where does a retired one live?** |
| **Class** | **Governance Decision** |
| **Evidence** | [`LANE_COORDINATION.md`](LANE_COORDINATION.md) is **2,972 lines — 58% of the 5,102 a lane must read before every slice.** Its own rule says it *should shrink*; it has only grown. **12 items are 52% of it, and the largest — C-025 at 408 lines — has been closed since 2026-08-03** |

### The proposed lifecycle

```
  OPEN  ──▶  ANSWERED  ──▶  IMPLEMENTED  ──▶  VERIFIED  ──▶  ARCHIVED
   │            │                │               │              │
 raised    a decision       the work is      QE confirms    leaves the
           exists           built            it holds       reading path
```

**Two states are new. The existing five are unchanged in meaning**, which is what makes this cheap:

| State | Set by | Means | New? |
|---|---|---|---|
| `OPEN` · `WAITING` | Any lane | Raised · the owner has it | |
| `ANSWERED` | The named owner | **A decision exists.** Implementation may not have started | |
| `IMPLEMENTING` → **`IMPLEMENTED`** | The requesting lane | **The work is built and pushed** | **Renamed** — a state, not an activity |
| **`VERIFIED`** | **QE** | The answer holds in the promoted repository | **New** |
| **`ARCHIVED`** | **Lane C**, at Closeout | **Moved out of the reading path**, fully searchable | **New** |

> **`VERIFIED` is the gate that makes archiving safe.** Without it, an item leaves the register on the *claim* that it was built — which is the failure `ANSWERED` vs `CLOSED` already exists to prevent, one step later.

### Where an archived item goes

| | Option | Consequence |
|---|---|---|
| **A** ✅ | **`docs/archive/coordination-YYYY-MM.md`**, append-only, dated. The register keeps **one row**: id · title · decision · link | **Historical, not invisible** (§8). Full deliberation preserved verbatim; `grep` still finds it; the reading path loses 58% of its bulk. **Reuses the dated-record convention `CLAUDE.md` §2 already requires** |
| **B** | Keep everything; collapse closed items behind detail markers | **Rejected.** The bytes stay in the file a lane opens, and the rule becomes *"scroll past"* — which is the current state with extra syntax |
| **C** | Delete; rely on `git log` | **Rejected.** *"A record nobody can cite."* It is the one option that genuinely loses something |
| **D** | One file per item | **Rejected.** Trades a long file for a directory nobody can scan, and §12 forbids new files where an existing one serves |

**Recommendation: A, archiving only at `VERIFIED`, monthly, by Lane C at Closeout.**

**Immediate effect if approved:** the nine items already closed on evidence plus C-025 leave the path — **roughly 900 lines, ~30% of the register**, on the first pass alone.

**What this does not change.** Ids are never reused. An archived item keeps its `C-nnn` and its anchor. **Archiving is not closing** — only a `VERIFIED` item is eligible, and verification is QE's.

---

## PACK I · Epics B–G are specified and unapproved, and the queue is running dry

**Raised by Lane C 2026-08-03 — an *epic approval* decision, which the escalation criteria reserve for the product owner.**

| | |
|---|---|
| **Decision** | **Which of Epics B–G, if any, enter the backlog?** |
| **Class** | **Product Decision** — scope, and therefore not Lane C's |

**The queue is thin, and it is thin for a good reason.** Three `READY` rows turned out to be already built ([C-404](LANE_COORDINATION.md)); [TASK-400](BACKLOG.md) was queued from Epic A's own decomposition. **What remains unclaimed for an idle lane is [TASK-900](BACKLOG.md), a platform RFC, which Lane B has already declined as a different discipline.**

**Meanwhile [51-implementation-specifications.md](architecture/51-implementation-specifications.md) carries 21 specified slices** — objective, module-assigned, effort-estimated — **of which only Epic A is approved.**

| Epic | What it closes | Modules | Note |
|---|---|---|---|
| **B** · Close the contradictions | The ICP is declared and **nothing consumes it**; the first-run path | `commercial_profile` · `buying_score_engine` · Product Surface | **B1 is the commercial-profile value proposition** and is gated by [Pack C](#pack-c--where-does-customer-language-meet-canonical-data) |
| **C** · People | *"Who do I call?"* — the gap every persona names first | **A new bounded context** (C1, XL) | 🔴 — needs an ADR before it is claimable ([ADR-0100](architecture/adr/0100-delegated-dependency-rulings.md) R-2) |
| **D** · Risk | Risk signal families, risk postures, who is already a customer | `signal_engine` · `buying_score_engine` · `integrations` | **D2 and D3 are S/M and unblocked** |
| **E** · Enterprise | CRM OAuth and write-back, SSO, SCIM, audit | `integrations` · QE | **Commercial decision** — enterprise versus GA |
| **F** · Workflow | Rules, safe actions, a builder | **A new `workflow` module** | 🔴 — new bounded context |
| **G** · Assistance | Ask about an account; draft an approach | `ai_reasoning_engine` | Gated by `reasoning@1` having no released model ([TASK-013](BACKLOG.md)) |

> ⚠️ **Corrected 2026-08-03, and the correction is Lane C's own.** This pack recommended **D2 and D3** as *"S/M and unblocked"*. **D3's specification says plainly that it depends on E1**, and verification of the signal catalog showed **D1's two missing risk families need contract and usage data only a CRM carries.** **Epic D is gated on Epic E1**, so the sequencing below is wrong and E1 comes first — queued as [TASK-402](BACKLOG.md) under the authority to assign a fresh epic.
>
> **What survives:** **D2** alone is genuinely independent — a posture within the existing ledger, no CRM required. It stays a candidate and is not urgent.

**Lane C's original recommendation, superseded above: approve *D2 and D3* only.** They are **S/M**, sit in modules with no open coordination item, need no new bounded context and no commercial ruling, and **D3 — *which accounts are already customers* — changes what the attention list means for every seller**, because an expansion opportunity and a net-new opportunity are not the same row.

**Not recommended now:** **C** and **F** each need a new bounded context and an ADR; **E** is a commercial call; **B1** waits on Pack C; **G** waits on a released model.

> **This is escalated rather than queued because it is epic scope, and scope is the product owner's.** [TASK-400](BACKLOG.md) was different: it decomposes Epic A, which is already approved. **The line Lane C is holding is that decomposing approved work is coordination, and admitting new epics is not.**

---

## PACK J · A lane can report `AVAILABLE` and the office that assigns it cannot see the signal

**Raised by Lane A as [C-218](LANE_COORDINATION.md); investigated by Lane C 2026-08-03, at the product owner's direction.** *"Do not assume Lane A's proposed solution is correct. Do not assume it is wrong either."*

| | |
|---|---|
| **Class** | **Repository Decision** |
| **Implementation** | **QE's**, if any is required |

### Is the problem real? — **Partly, and the precise version matters**

**The claim:** *Lane C reads `integration`; availability exists only on the lane branch; therefore Lane C never receives the signal.*

**Measured, and the last clause is false.** Lane A's `AVAILABLE` commit `31f22e7` is on `lane-a-product-surface` and **Lane C read it** — that is how [C-217](LANE_COORDINATION.md) was answered. Every lane's board is readable from `refs/remotes/origin/lane-*` in **18 milliseconds**.

> **What is true is narrower and still real: nothing obliges Lane C to look, and nothing tells it when.** Lane A idled not because the signal was unreachable but because **the office was analysing something else and had no defined moment to check.** The defect is in Lane C's operating procedure, **not in the repository's plumbing.**

**How widespread:** structural rather than one-off — **it recurs every time any lane finishes**, for every lane, and it gets worse with lane count. **But it is one-sided:** the `IN VALIDATION` → QE path is unaffected, because QE is *told* by a push it already watches for.

**One measurement nuance for whoever implements:** naive `grep` on a board returns the **legend row**, not the lane's status — all four refs report `IN VALIDATION` that way. **Parsing is required**, and `infra/registers.py` already does exactly this for `BUGS.md`.

### The options

| | Flow | Advantages | Disadvantages | Repository impact | Certification impact | Complexity | Maintainability |
|---|---|---|---|---|---|---|---|
| **A** ✅ | **Lane C reads every `lane-*` ref** at a defined cadence — at each assignment, and after every push of its own | **Zero repository change. Zero QE work. Works today; it is what already happened.** No new file, workflow, state or commit type | **Pull, not push** — Lane C must look. Nothing happens if Lane C is not running | **None** | **None** | **Procedure only** | **Highest** — nothing to maintain |
| **B** | **A lane pushes a status commit to `integration`**, bounded to the two registers like a claim | Signal on the shared ref, **visible to every lane and QE**, and auditable | **Widens the one exception a feature lane may push.** `--audit-claims` greps `^Claim TASK-`, so a status commit **is neither permitted nor audited today** — the guard must change | Guard + `CLAUDE.md` | Low, but **it touches the promotion guard** | QE change | Medium |
| **C** | **QE relays availability at Closeout** | No new mechanism | **Couples assignment latency to the certification cycle** — a lane finishing mid-cycle waits for a promotion. **Directly contradicts the objective** | None | Adds coupling | Low | Poor |
| **D** | **A dedicated signal file or queue** | Explicit | **A new coordination artifact for a fact two registers already hold.** Rejected on `CLAUDE.md` §12 and the standing principle | New artifact | None | Medium | Worst |

### Recommendation — **A**

**It is the only option that reduces latency, and B does not.** The signal arriving on `integration` rather than on a lane ref **changes nothing about when Lane C notices**, because both are pull — Lane C reads either one when it looks. **B buys visibility to other lanes, which nobody has asked for, at the cost of widening the one exception a feature lane may push to a shared branch.**

**A also preserves every principle named:** `integration` stays the source of truth for *merged work* — a lane ref is the source of truth for *that lane's state*, which is what is being read. **No certification guarantee moves, QE is not bypassed, no manual coordination is added, and no governance is created.**

**What Lane C changes in its own procedure, and nothing else:**

- **Read every `lane-*` ref at the start of every assignment cycle**, parsing the board rather than grepping it.
- **Re-read after pushing** — the moment Lane C's own attention returns to the repository is the cheapest moment to notice a lane that finished meanwhile.
- **Treat a lane at `AVAILABLE` with no prepared assignment as a finding against Lane C**, not against the lane.

> **If A proves insufficient — if a lane idles again despite it — B is the fallback**, and the evidence for it will be an *observed* idle gap rather than a forecast one. **That is the same standard `CLAUDE.md` sets for changing governance at all: not one lane's inconvenience, but demonstrated recurrence.**

**Lane C has implemented nothing.** If B is ever chosen, the guard and `CLAUDE.md` are QE's and the product owner's respectively.

---

## What remains open

**One pack, and it is the one the product owner declined to consolidate.** [ADR-0100](architecture/adr/0100-delegated-dependency-rulings.md) **R-10** kept ADR-0041 and C-002 separate: *"ADR-0041 defines how customer intent is modeled, versioned, governed and referenced. C-002 defines how that intent is interpreted against normalized provider data. They are complementary capabilities, not one combined decision."*

**Also open and deliberately unruled**, each with its reason recorded in ADR-0100: **C-203** *(how the product names a person)* · **C-302** *(a notification is per-person, and workspace RLS is not enough — tenancy is never decided inside a session)* · **C-003** and **C-005**, both re-validated and confirmed non-blocking.

---

---

## How this document is maintained

**Owned by Lane C** *(QE until 2026-08-03)*. **Refreshed against the promoted commit at every Repository Closeout, and whenever a ruling lands** — because a pack that outlives its decision turns the decision queue from operational into historical, which is what this document was doing until today.

**Every item is re-challenged, never merely carried forward:** is it still real · still blocking · narrowable · splittable · **already answered by implementation, an ADR or a repository rule.**

> **This is a staging area, not a record.** A pack is deleted when its decision is taken — after the three gates above — and the answer lives in the ADR or document it produced.

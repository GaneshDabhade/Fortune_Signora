# Decision Packs — architectural decisions, grouped

> **For the product owner. Prepared and maintained by Lane C** — transferred from QE on 2026-08-03, when decision preparation became the Product Office's (`CLAUDE.md` §20e *Lane C*). **QE's authorship of everything below this line is preserved and is not rewritten**; what changes is who maintains it next.
>
> **The problem this solves:** thirty-two open coordination items, presented one at a time over weeks, each needing context rebuilt from scratch. **They are not thirty-two decisions.** Grouped by the question actually being asked, they were **five** — **four are now ruled and retired below, and one remains.**
>
> **Lane C owns the process, never the decision.** Every pack states a recommendation because a pack without one is a question wearing a suit; **none of them is acted on until you rule.**

**Reviewed against `main` at `d39b136`, 2026-08-03. Retirement pass 2026-08-03 — 183 lines to 68. Dissolution pass 2026-08-04 — Packs J and K removed as questions, not answers.**

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

> ⚠️ **The premise was wrong, corrected 2026-08-04 by Lane C against itself.** This pack was raised because *"the queue is running dry."* **It was not.** [CX-07](architecture/43-customer-experience.md) — responsive shell and screens, **XL, 2–3 weeks, Lane A's modules alone** — was **ruled executable on 2026-08-03** by [C-026](LANE_COORDINATION.md), which put phone in scope. **Lane C escalated an approval for scope that had already been approved**, and reported Lane A as nearly out of work while a multi-week initiative sat unallocated in its own architecture document.
>
> **What the mistake was, precisely:** the office tracked *"does this have a `TASK-nnn`?"* and treated the absence as *"unscoped."* **CX-07 had a ruling, an objective, named modules and an effort estimate — everything except an id.** That is the failure mode the epic-level portfolio exists to prevent *(product owner, 2026-08-04: do not optimize around backlog rows)*.

**What is genuinely unapproved is narrower, and it is still worth deciding.** Three `READY` rows turned out to be already built ([C-404](LANE_COORDINATION.md)); [TASK-400](BACKLOG.md) decomposes Epic A, which is approved. **What no lane can start without you is a *new epic*.**

**Meanwhile [51-implementation-specifications.md](architecture/51-implementation-specifications.md) carries 21 specified slices** — objective, module-assigned, effort-estimated — **of which only Epic A is approved.**

| Epic | What it closes | Modules | Note |
|---|---|---|---|
| **B** · Close the contradictions | The ICP is declared and **nothing consumes it**; the first-run path | `commercial_profile` · `buying_score_engine` · Product Surface | **B1 is the commercial-profile value proposition** and is gated by [Pack C](#pack-c--where-does-customer-language-meet-canonical-data) |
| **C** · People | *"Who do I call?"* — the gap every persona names first | **A new bounded context** (C1, XL) | ✅ **Prepared 2026-08-04** — [400-epic-c-people.md](architecture/400-epic-c-people.md), **[ADR-0400](architecture/adr/0400-person-as-an-entity.md) drafted and `Proposed`** ([C-408](LANE_COORDINATION.md)). **Narrowed, not confirmed XL**: the intelligence already runs and lacks only a subject |
| **D** · Risk | Risk signal families, risk postures, who is already a customer | `signal_engine` · `buying_score_engine` · `integrations` | **D2 and D3 are S/M and unblocked** |
| **E** · Enterprise | CRM OAuth and write-back, SSO, SCIM, audit | `integrations` · QE | **Commercial decision** — enterprise versus GA |
| **F** · Workflow | Rules, safe actions, a builder | **A new `workflow` module** | 🔴 — new bounded context |
| **G** · Assistance | Ask about an account; draft an approach | `ai_reasoning_engine` | Gated by `reasoning@1` having no released model ([TASK-013](BACKLOG.md)) |

> ⚠️ **Corrected 2026-08-03, and the correction is Lane C's own.** This pack recommended **D2 and D3** as *"S/M and unblocked"*. **D3's specification says plainly that it depends on E1**, and verification of the signal catalog showed **D1's two missing risk families need contract and usage data only a CRM carries.** **Epic D is gated on Epic E1**, so the sequencing below is wrong and E1 comes first — queued as [TASK-402](BACKLOG.md) under the authority to assign a fresh epic.
>
> **What survives:** **D2** alone is genuinely independent — a posture within the existing ledger, no CRM required. It stays a candidate and is not urgent.

### Recommendation, restated at the epic level — **approve E, and nothing else yet**

| | | |
|---|---|---|
| **Approve** | **Epic E1 — CRM OAuth and read** | **The single highest-leverage integration in the roadmap.** It unblocks pipeline intelligence, forecasting, expansion and customer risk — **four vision modules, on its own** — and **Epic D3 with one boolean.** `integrations` is Lane B's alone, so it is 🟢 and independent. **It needs one thing from you that is not an approval: developer credentials** |
| **Keep as a candidate** | **Epic D2 — risk postures** | Genuinely independent — a posture inside the existing ledger, no CRM. **M**, not urgent, and it is where [TASK-905](BACKLOG.md) belongs |
| **No decision needed** | **CX-07** | **Already ruled.** It needs allocation, not approval |
| **Not yet** | **C · F · G · B1** | **C** and **F** each need a new bounded context and an ADR; **G** waits on a released model ([TASK-013](BACKLOG.md)); **B1** waits on [Pack C](#pack-c--where-does-customer-language-meet-canonical-data) |

> **E is described above as *"a commercial decision — enterprise versus GA"*, and that is true of E3 and E4, not of E1.** SSO, SCIM and audit are the enterprise gate. **Reading a customer's CRM is the product working**, and it is what most of the vision is waiting on.

> **This is escalated rather than queued because it is epic scope, and scope is the product owner's.** [TASK-400](BACKLOG.md) was different: it decomposes Epic A, which is already approved. **The line Lane C is holding is that decomposing approved work is coordination, and admitting new epics is not.**

---

## PACK J · The availability signal — **dissolved 2026-08-04, not ruled**

**Raised by Lane A as [C-218](LANE_COORDINATION.md); investigated by Lane C 2026-08-03.** *"Do not assume Lane A's proposed solution is correct. Do not assume it is wrong either."*

> **It needed no ruling, and taking one off the product owner's queue is the point.** The measured finding stands: **every lane's board is readable from `refs/remotes/origin/lane-*` in 18 milliseconds**, so Lane A's claim that the signal was *unreachable* was false — Lane C had already read `31f22e7` and answered [C-217](LANE_COORDINATION.md) with it. **What was true is narrower: nothing obliged Lane C to look, and nothing told it when.**
>
> **The 2026-08-04 model answers it without any repository change.** A lane reports `AVAILABLE` **to the product owner**, who asks the office for a recommendation. **The signal is a message on a channel that already exists**, and the three build-something options (a status commit to `integration`, QE relaying at Closeout, a dedicated signal file) are all moot.
>
> **What Lane C keeps as procedure, costing nothing:** read every `lane-*` ref at the start of each planning pass, **parsing the board rather than grepping it** — naive `grep` returns the legend row and reports all four refs as `IN VALIDATION`. **Treat a lane at `AVAILABLE` with nothing prepared as a finding against Lane C**, not against the lane.
>
> **Lane C implemented nothing, and the promotion guard is untouched.**

---

## PACK K · Assignment delivery — **dissolved 2026-08-04, not ruled**

> **The product owner dissolved the question rather than answering it.** *"The current model is becoming over-coordinated"* — Lane C recommends, the product owner allocates in one reply, and **there is nothing to deliver.** Assignment delivery, commits, propagation, synchronization, visibility, acknowledgement and routing are all deleted; **the shared channel is the product owner, who already talks to every lane.**
>
> **Both of this pack's answers were right about the wrong problem.** Option A had lanes read a ref; the direct-reply supersession had Lane C send a message. **Each made delivery a mechanism, and the correct move was to have no delivery.** Kept as one paragraph because the mistake generalises: **when a coordination problem needs a channel built, check first whether a channel already exists that nobody thought to use.**
>
> **What survives, and it is not part of this pack:** the lane's own `Claim TASK-nnn` commit remains the only thing a feature lane pushes to `integration`, bounded by `CLAIM_PATHS`. **That was true before Pack K and is untouched by dissolving it.**

## What remains open

**One pack, and it is the one the product owner declined to consolidate.** [ADR-0100](architecture/adr/0100-delegated-dependency-rulings.md) **R-10** kept ADR-0041 and C-002 separate: *"ADR-0041 defines how customer intent is modeled, versioned, governed and referenced. C-002 defines how that intent is interpreted against normalized provider data. They are complementary capabilities, not one combined decision."*

**Also open and deliberately unruled**, each with its reason recorded in ADR-0100: **C-203** *(how the product names a person)* · **C-302** *(a notification is per-person, and workspace RLS is not enough — tenancy is never decided inside a session)* · **C-003** and **C-005**, both re-validated and confirmed non-blocking.

---

## PACK N · The engineering-blocking queue, reduced to four decisions

**Produced 2026-08-04 on the product owner's direction: *shrink the decision queue*.** Five items were named in priority order; **each was verified against source, and one of the five needs no ruling of its own.** No new architecture, no replacement `C-` items.

| # | Item | Still valid? | **The smallest decision** |
|---|---|---|---|
| **1** | **[C-326](LANE_COORDINATION.md)** | ✅ **Yes, and much smaller than when raised** | **Ratify [ADR-0300](architecture/adr/0300-inbound-customer-systems.md) §1 — *a customer-held system is a source, not a provider*.** One sentence; everything else follows |
| **2** | **[C-221](LANE_COORDINATION.md)** | ✅ Yes — **Lane C's half is done** *(below)* | **Park Epic C until [E1](architecture/401-epic-e1-crm-read.md) lands, or drop it.** Nothing else can move it |
| **3** | **[C-321](LANE_COORDINATION.md)** | ✅ Yes | **Accept the six recommendations as a set, or name the ones you would change.** They are already yes/no |
| **4** | **[C-021](LANE_COORDINATION.md)** | ✅ Valid — **but it needs no ruling of its own** | **None. It is gated on [C-010](LANE_COORDINATION.md)**, and ruling that unblocks both |
| **5** | **[C-200](LANE_COORDINATION.md)** | ✅ Yes | **Is M14b one module, two, or three?** Lane A's discovery says *"one module and two integrations"* |

### Verified against `origin/integration` — 2026-08-04, and it closed two more

**Rule 5 applied: every finding below is read from `origin/integration`, not from this branch.** A rebase was attempted, hit a conflict on a claim commit already upstream, and was **aborted on the product owner's direction** — *documentation conflicts and historical Product Office commits are not engineering effort worth spending.* **Nothing here rests on local state.**

| Item | Verified on integration | Outcome |
|---|---|---|
| **[C-223](LANE_COORDINATION.md)** | **`competitor_entry` is in the catalog (10 types).** `commercial_profile/public/` exports `DeclaredCompetitorView`, `DeclaredCompetitorListView` and `DeclaredCompetitorReader.current(workspace_id) -> …\| None`. **`signal_engine/application/generate.py` imports it** | ✅ **Answered by implementation.** [ADR-0403](architecture/adr/0403-signal-engine-reads-a-declaration.md)'s contract was built exactly as specified |
| **[B-400](BUGS.md)** 🔴 | **One `0031` remains**; Lane A's chain renumbered to `0032`–`0035`. **The revision map is linear** | ✅ **Closed.** Fixed the opposite way to the recommendation, and **the better way** — the unpromoted chain moved |
| **[C-025](LANE_COORDINATION.md)** | Already **`ANSWERED`** — *"all four decisions"*; blocks *"nothing. The remaining work needs a HubSpot developer application, not a decision"* | ✅ **Not a queue item** |
| **[C-023](LANE_COORDINATION.md)** | Its own row: *"Overlaps Lane B's [C-025](LANE_COORDINATION.md) in substance — two lanes reached it independently"* | ✅ **Duplicate.** Resolves against C-025, which is answered. **No separate ruling** |

> **[ADR-0403](architecture/adr/0403-signal-engine-reads-a-declaration.md)'s §Validation 2 claim is confirmed by what shipped: no import contract was amended.** Integration has 35 contracts to this branch's 34, and **the new one is `sales_engagement`** — unrelated. `signal_engine` was already named a permitted source of `commercial_profile.public`, exactly as the validation found.

### ⚠️ A register defect on integration — reported, not fixed

**[C-326](LANE_COORDINATION.md) is in three states at once on `origin/integration`:** its **body sits after the `## Closed` marker** (line 4020, marker at 2556), its **`Status` field says `OPEN`**, and it has **no index row at all.**

**It is genuinely open** — Lane B is waiting on it and its content is current. **Lane C is not fixing it**: this branch is 151 commits behind, and editing a shared register from here creates exactly the conflict the product owner directed should not be spent on. **Raised for whoever reconciles the register next.**

### Category 1 — resolved by Lane C, no ruling needed

**Two items were carrying claims the repository has since falsified. Neither is closed** — both still hold a real question — **but the argument that made them urgent is gone, and that is what was making them look bigger than they are.**

| Item | The claim it carried | What the repository says now |
|---|---|---|
| **[C-012](LANE_COORDINATION.md)** | *"**The deployed worker consumes nothing**"* — the reason it survived since M3A | ⚠️ **Obsolete.** The deployed worker consumes. **`_project_to_timeline` and `_run_requested_research` are wired**, each binding a session at call time via `tenant_scoped_session(current.session_factory, …)`. [B-301](BUGS.md) and README record it: *"the deployed worker consumes it"* |
| **[C-003](LANE_COORDINATION.md)** | *"Blocks nothing — **but it gets worse with every slice**"*, predicting a fourth wire code at slice 5 | ⚠️ **Disproven.** There are still **exactly three** — `icp_`, `committee_`, `focus_`. **Slice 5 added none.** The growth argument has not materialised across every slice since |

> **C-012 is reduced but deliberately not closed, and the item itself is why.** It warned: *"**Not to be worked around inside a product milestone, which is how it would become permanent.**" **A pattern did ship, and whether it is the answer or the predicted workaround is exactly the judgement C-012 reserved.** Closing it on Lane C's reading would be the office deciding the thing the item exists to protect.
>
> **So it reduces from an RFC to a yes/no:** *is binding a session in the worker's wrapper the answer, or the workaround C-012 named?* **What is no longer true is that anything is blocked** — every module that wants to consume an event now has a working precedent, twice.

**C-003 reduces to a permission with no urgency:** rename three wire codes, or leave them. **⚫ under the Change Budget, every consumer is Lane B's own frontend, and nothing degrades while it waits.**

### Category 2 — ADRs ready for ratification, and processing continues past them

**Three are complete, carry no unresolved alternatives, and need only a signature.** **Lane C is not waiting beside them.**

| ADR | Alternatives | Open questions | Status |
|---|---|---|---|
| **[ADR-0402](architecture/adr/0402-a-rule-is-data.md)** — a rule is data | **Five assessed, one recommended** | ❓1 🟡 M14a sequencing *(phase 5 only)* · ❓2 🟢 *(engineering answers)* | **READY FOR RATIFICATION** |
| **[ADR-0401](architecture/adr/0401-a-customers-crm-is-not-a-provider.md)** — CRM is not a provider | **Four assessed, one recommended, amended on Lane B's evidence** | ❓1–❓3 downstream of the decision | **READY FOR RATIFICATION** |
| **[ADR-0400](architecture/adr/0400-person-as-an-entity.md)** — a person becomes an entity | **Five assessed, one recommended** | **❓1 is now answered — *no***. ❓2 is [C-221](LANE_COORDINATION.md)'s route choice · ❓3 affects phase 4 only | **READY FOR RATIFICATION** |

> **Ratifying [ADR-0400](architecture/adr/0400-person-as-an-entity.md) does not approve Epic C and does not unblock it** — it records the bounded context so the decision is not re-derived whenever the epic resumes. **The two acts were separated in the ADR itself and remain separate.**

> **[ADR-0402](architecture/adr/0402-a-rule-is-data.md) is the highest-value signature on the board.** It is the only one that turns a **`🧊 FROZEN — READY`** epic into a startable one, **and Epic F's phase 0 needs nothing at all.**

---

### 1 · C-326 — the ruling moves a file and rewrites a wrapper

**Lane B's own row already narrowed it, and the narrowing is the important part:** *"This row said implementation had stopped. **It had not.**"* Interpretation, acquisition, grant lifecycle and the vendor read **all reached `main` on 2026-08-04.**

> **What remains gated is exactly one thing: how a fetched record reaches `raw_provider_record`.** Lane B: *"the ruling **moves a file and rewrites a wrapper — no behaviour moves with it**."*

**[ADR-0300](architecture/adr/0300-inbound-customer-systems.md) is `Proposed`, and that is the whole blocker.** **[409](architecture/409-inbound-source-port-contract.md) is the contract that follows from its §1**, specified so implementation resumes without inventing architecture — and it establishes that the change needs **no migration, no new event, no vocabulary addition and no downstream change**, because `raw_provider_record.provider` is already `String(64)` and normalization already keys on a `str`.

**So the decision is a yes/no on one sentence**, and the cost of *yes* has already been measured at near zero.

### 2 · C-221 — Lane C's half is complete; the remaining half is a route

**C-221's owner is split — *product owner (the epic) · Lane C (the specification)*. The specification half is done** and needs nothing further:

| | |
|---|---|
| **[400-epic-c-people.md](architecture/400-epic-c-people.md) §0** | Records that ❓1 is answered **no**, that phases 1–3 do not split into a blocked and an executable half, and that the buying score needs no change at all |
| **[ADR-0400](architecture/adr/0400-person-as-an-entity.md)** | Carries the model, the alternatives and the three open questions |

**What is left is one choice, and no work of any kind changes it:** **the provider returns no person name**, so Epic C's phases 1–3 have no input. **Route B — read people from the customer's own CRM once [E1](architecture/401-epic-e1-crm-read.md) lands — is the only path**, and Lane C recommended it in ADR-0400 ❓2 for independent reasons.

> **Park or drop. There is no third option that repository evidence supports**, and holding [TASK-201](BACKLOG.md) claimed-and-blocked costs Lane A a row on its board.

### 3 · C-321 — already six yes/no answers awaiting a signature

**Lane B reduced it to six sub-questions with recommendations**, and the A6 reuse audit *"settled two things so the ruling does not have to."*

| | Recommended |
|---|---|
| Should an unnamed company appear at all? | **Yes** — hiding it discards real intelligence |
| On the working list? | **No** — that list answers *"who should I call?"* |
| Contribute to a score? | **Yes** — the score measures evidence, and the evidence is real |
| Become an opportunity? | **No** — an opportunity is something a person can pursue |
| Be workable? | **Never.** Today it is |
| What is it, then? | **`Needs identity` — a queue with its own workflow**, not a filter |

**Lane C adds nothing and recommends nothing here** — the analysis is Lane B's and is complete. **The smallest decision is to accept the set or name exceptions.**

### 4 · C-021 — valid, and it is not a decision

**Verified still valid:** `provider_platform/application/sync_targets.py` is **179 lines, built and tested**, and **`apps/worker/subscriptions.py` does not wire it** — grep for `sync_targets`, `target_accounts_changed` and `SyncTargets` returns nothing. **Nothing yet reads a company a customer declared. The row is accurate.**

> **But its stated owner reason is *"`apps/worker/` has no assignable lane ([C-010](LANE_COORDINATION.md))"*** — and that is [C-010](LANE_COORDINATION.md)'s question, not a second one. **C-021 is C-010 wearing a slice's name.**

**No ruling is needed on C-021.** Ruling C-010 — *how is code that belongs to no module assigned when it needs a fix?* — unblocks PP-02's last wire, PP-03, and [C-007](LANE_COORDINATION.md) with it. **Two items, one decision. That is the reduction.**

**Not merged and not closed**, because C-021 also records a genuine technical finding an implementer needs. **It is marked as gated on C-010 rather than carried as an independent decision.**

### 5 · C-200 — one question, three candidate answers

**M14b is three concerns in one roadmap row** — billing, analytics, feature flags — **and none has a module.** Lane A's discovery reached a specific answer: ***"It is one module and two integrations, not one and not three."***

**The smallest decision is which of the three that is.** **Lane C makes no recommendation** — M14b's scope is product scope, and Lane C's own [408](architecture/408-revenue-intelligence-platform.md) test would only tell you whether the result owns an aggregate, which cannot be applied until the boundary is chosen.

---

> **Net effect: five priority items → four decisions**, and **three of the four are a signature rather than a design** — C-326 is one sentence, C-321 is six yes/no answers already written, C-221 is park-or-drop. **Only C-200 requires original product thinking.**

---

## PACK M · OAuth client credentials — **withdrawn 2026-08-04, a clarification rather than a decision**

**Opened and withdrawn the same day.** Lane B's [C-327](LANE_COORDINATION.md) asked where Signora's own OAuth client credentials live; Lane C prepared it as a decision and **that was the misclassification**, not the analysis.

> **The repository already held one consistent interpretation.** **[13-integrations.md](architecture/13-integrations.md) — ratified — states that integration OAuth grants are *"stored per-tenant, RLS-scoped, distinct from Better Auth's sign-in credentials"* and names *"reusing a Better Auth sign-in credential as an integration OAuth token"* an anti-pattern.** And the reading was already load-bearing: **`integration_secret` stores encrypted third-party credential material in the Python tier, and `IntegrationSettings` holds a Signora-owned long-lived secret there** — both shipped, neither ever flagged.
>
> **So [18-authentication.md](architecture/18-authentication.md):49's prohibitions govern *identity* credentials.** Recorded there as a scope note; **[C-413](LANE_COORDINATION.md) withdrawn.**

**What survives, and it is the part worth keeping:** *"never implement an OAuth flow, callback handler, or authorization-code exchange"* **binds regardless of whose credential it is**, which is why acquisition stays in Next even for integrations. **The clarification narrows one prohibition and leaves the other untouched.**

**Also fixed, because it was doing real damage in the argument:** [18-authentication.md](architecture/18-authentication.md) listed *"token refresh"* among Next's responsibilities meaning **a Signora user's session**, while [C-327](LANE_COORDINATION.md) concerns **a customer's third-party grant.** One word, two operations — **now *"session token refresh."***

> **The one thing genuinely left to decide is not architectural.** Holding the client pair in both tiers means **two rotation targets** until a vault arrives at M14.5. **That is an operational trade-off with a known end state, not a boundary question** — and it is Lane B's and QE's to weigh, not a product-owner decision.

---

## PACK L · Repository architecture — a decision that has been waiting outside the queue

**Surfaced 2026-08-04 by Lane C during repository cleanup. Not authored by Lane C** — [`REPOSITORY_ARCHITECTURE_PROPOSAL.md`](REPOSITORY_ARCHITECTURE_PROPOSAL.md) was written **2026-07-30** and has read **`PROPOSED — awaiting approval`** for five days.

| | |
|---|---|
| **Class** | **Repository Decision** |
| **Why it is here** | **It is a decision, and it was not in the decision queue.** Nothing in this document pointed at it, so it aged where no queue could show it |

**Part 1 — documentation organisation.** Recommends **four directories rather than the brief's seven**, moving **7 files and 0 directories**, leaving the 58 highest-linked documents on their existing paths. **`docs/architecture/` and `adr/` do not move at all.**

> **Its strongest argument is an objection to its own brief**, and it is worth reading before anyone proposes this again: moving `22`–`28` out of `architecture/` *"looks most obviously right"* and is recommended **against**, because moving coherently requires renumbering, renumbering falsifies existing references, **and commit messages cannot be updated** — *"renaming `26-buying-score-engine.md` makes `ed7f9e9`'s message point at nothing."*

**Part 2 — business scenario tests.** Recommends **three scenarios rather than eleven**, chosen to exercise disjoint machinery. **Neither clearly built nor clearly superseded**: `backend/tests/simulation/test_scenario.py` exists; whether it is these three was not established.

**Relationship to what has since been ratified.** [`PRODUCT_OFFICE.md`](PRODUCT_OFFICE.md) §8's **three-purpose model** classifies documents by *purpose*; this proposal organises them by *location*. **They are compatible and neither references the other** — which is the coordination gap, not a conflict.

> **Lane C makes no recommendation on the merits.** It did not author this, the reasoning is the original author's and is strong, and **surfacing it into the queue is the cleanup — deciding it is not Lane C's.** The narrow question is whether it is still live at all, five days on.

---

## The decision queue, as of 2026-08-04

**Two items genuinely need the product owner. Not twenty** — and the office's job is to keep it that way.

| | Item | Blocking | Why it cannot be determined objectively |
|---|---|---|---|
| 🔴 | **[C-321](LANE_COORDINATION.md)** | **A6, now** | Its specification says twice that A6 *"depends entirely on the C-321 ruling"*. **What to render *is* the ruling** — narrowing the slice does not escape it |
| 🟠 | **[Pack I](#pack-i--epics-bg-are-specified-and-unapproved-and-the-queue-is-running-dry)** — Epics B–G scope | — | ⚠️ **Superseded in practice.** Epics C, D, E1, F and G were all approved and assigned directly between 2026-08-03 and 2026-08-04. **What remains of it is Epic B**, which [C-322](LANE_COORDINATION.md) already carries |

> **The engineering-blocking queue is [Pack N](#pack-n--the-engineering-blocking-queue-reduced-to-four-decisions), and it is four decisions.** Everything below this line is either ruled, dissolved or blocking nothing.

> **Everything else the office could determine, it determined.** Packs J and K were dissolved rather than escalated, Pack F was ruled, Pack H adopted. **A decision list long enough to need triage is a list Lane C failed to triage.**

---

## How this document is maintained

**Owned by Lane C** *(QE until 2026-08-03)*. **Refreshed against the promoted commit at every Repository Closeout, and whenever a ruling lands** — because a pack that outlives its decision turns the decision queue from operational into historical, which is what this document was doing until today.

**Every item is re-challenged, never merely carried forward:** is it still real · still blocking · narrowable · splittable · **already answered by implementation, an ADR or a repository rule.**

> **This is a staging area, not a record.** A pack is deleted when its decision is taken — after the three gates above — and the answer lives in the ADR or document it produced.

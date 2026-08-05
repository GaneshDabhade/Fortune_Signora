# Product Owner Decision Queue

**The single place the product owner reviews when making rulings.** Established 2026-08-05 by product owner directive.

> ## ⚠️ Three things are waiting on you, and two arrived from the same method.
>
> **① [Placing TASK-427](#-task-427--the-people-domains-trigger-has-fired-and-placing-it-is-yours)** — **the People domain.** One row, one position, and **its trigger has already fired.**
> **② [TASK-431](#-task-431--six-screens-assert-one-guarantee-and-the-repository-has-no-word-for-it)** — **the highest-value decision on this page.** Six approved screens assert one guarantee; the repository has no representation of it.
> **③ [TASK-433](#-task-433--segment-already-means-something-else)** — **one word, and it costs a sentence today.**
>
> **② and ③ are the first output of [Product-Led Domain Discovery](architecture/442-product-led-domain-discovery.md).** **Both are rulings, not work** — neither asks for anything to be built.
>
> ✅ **Both of the items that stood here on 2026-08-05 are ruled and cleared** — **[C-416](LANE_COORDINATION.md)** gave `signora_platform/` a permanent owner and released [TASK-418](BACKLOG.md) with [TASK-901](BACKLOG.md)'s seven slices; **[C-224](LANE_COORDINATION.md)** settled the authorization `Resource`, and `CLAUDE.md` §20a now names it in the carve-out. **Both were ruled by [D-073](DECISION_REGISTER.md).** *(This banner still asked for them the next morning. **`--check` reported C-224 as `STALE` and it was right** — the queue is only true if a ruling removes its own row.)*
>
> **The 2026-08-05 rulings cleared every item that existed when they were made.** **Fourteen approved, three confirmed, eight deferred, three closed** — and the four platform items collapsed into one ADR. **Every remaining row below is either deferred by you or blocks nothing being built.**
>
> **This is the healthy state, not an empty document.** *"Our objective is not to close the maximum number of governance items. Our objective is to maximize engineering throughput."*

## What the ruling released

| | |
|---|---|
| ⚡ **[TASK-901](BACKLOG.md)** | **Seven independently certifiable slices** — [ADR-0404](architecture/adr/0404-platform-composition.md) ratified [435](architecture/435-platform-composition-rfc.md) whole |
| **[TASK-904](BACKLOG.md)** | Team Management — C-206 and C-208 both ruled |
| **[TASK-003](BACKLOG.md)** | Attribute vocabulary — C-018 ruled |
| **[TASK-406](BACKLOG.md)** | ICP measurement — C-328 ruled, at changed scope |
| **[TASK-201](BACKLOG.md)** | Epic C — C-221 ruled, at narrowed scope |
| **[TASK-400](BACKLOG.md)** | A6 — C-321 ruled |
| **[TASK-418](BACKLOG.md)** | `signora_platform/` has a permanent owner — **C-416 ruled** ([D-073](DECISION_REGISTER.md)) |
| **Lane A's resolution route** | The authorization `Resource` — **C-224 ruled**, and `CLAUDE.md` §20a's carve-out now names it |

**Eight tasks and seven slices, from two sittings.** **A ruled item leaves this file the same day** — its record is [LANE_COORDINATION.md](LANE_COORDINATION.md)'s, and its ruling is [DECISION_REGISTER.md](DECISION_REGISTER.md)'s.

## How this stays true

**Two kinds of column.** **Derived** — status, blocks, lanes waiting — computed from [`LANE_COORDINATION.md`](LANE_COORDINATION.md), [`BACKLOG.md`](BACKLOG.md) and [`modules.toml`](coordination/modules.toml). **Judgement** — priority, recommendation, cost — Lane C's.

> **`python3 infra/decision-queue.py --check` fails when this file and the register disagree.** It reported every ruled row still sitting here within a minute of the ruling, which is how this rewrite got scoped.

---

## 📌 TASK-427 · The People domain's trigger has fired, and placing it is yours

**Not a `C-` item and deliberately** — **nothing is undecided.** [D-074](DECISION_REGISTER.md) ruled the direction; **what is left is a position in the queue, which is a priority act and not Lane C's.**

| | |
|---|---|
| **Summary** | **[TASK-427](BACKLOG.md) · M-D · the People domain** is `SEQUENCED` with the trigger *"the first dependent customer-facing capability enters implementation."* ⚠️ **Measured 2026-08-05: fired.** **[TASK-202](BACKLOG.md) is `READY` and its own row says *"phase 4 needs Epic C"*** |
| **Why it is here rather than in the `READY` queue** | **Your instruction**: *"do not assign implementation immediately… make it part of the planned execution sequence so implementation begins at the correct time."* **The row is prepared and unplaced.** A lane may not insert a `READY` task and Lane C may not reprioritize — **so one move by you is the whole remaining step** |
| **Impact** | **Four screens across waves 1–4.** Account 360 has already shipped two ⬜ stated absences; **AI Copilot is the next one to pay** |
| **Blocked tasks** | **[TASK-428](BACKLOG.md) entirely.** TASK-429 and TASK-430 have their own, later triggers |
| **Lanes waiting** | **None yet, and that is the argument for placing it now rather than the argument against.** Epic C is assigned to **Lane A** |
| **Priority** | **P1 — it is in front of a wave that is claimable today** |
| **Recommended** | ✅ **Place [TASK-427](BACKLOG.md) in `READY` above [TASK-202](BACKLOG.md).** **Nothing gates it** — no ruling, no provider, no missing module. **Alternative, if wave 2 should not wait**: place it immediately *below* TASK-202 and accept that AI Copilot's phase 4 stalls where phases 1–3 do not |

## 📌 TASK-431 · Six screens assert one guarantee, and the repository has no word for it

**Not a `C-` item — no lane is blocked and nothing is undecided about *whether*.** **The question is the shape**, and it is 🔴, so it is yours.

| | |
|---|---|
| **Summary** | **[442 §F1](architecture/442-product-led-domain-discovery.md).** *"Approved before it writes, reversible after it does"* · *"nothing sends without your approval, reversible for 24 hours"* · *"reversible for 24 hours as a single named batch"* · *"attributed, reversible, in the audit log"* · **AI Copilot's 17 surfaces: *"proposes rather than commits… attributable and reversible"***. **Five screens in the design project's own words, plus every AI surface** |
| **The finding** | **The AI contract and the bulk-edit contract are the same contract**, and that is invisible screen-by-screen — one reads as AI governance, the other as a table feature. **They are one concept: a change that waits for a human, is recorded as one named thing with an author, and can be taken back inside a window** |
| **Already built** | **More than half.** `Recommendation` proposes · **`MACHINE_AUTHORED = frozenset({Stage.TRACKING})` — *"Intelligence suggests. Humans commit."*** · `actor_id` in **37 files** · **reversal-as-supersession, five times** (`observation` · `signal` · `entity` · `business_event` · opportunity stage) |
| **Genuinely absent** | **A named unit of change · a window · and the verbs.** The `Action` enum is `read · update · add · remove` — **there is no `approve` and no `withdraw`, so the guarantee cannot currently be *authorized*, let alone recorded** |
| **Impact** | **Six screens.** **AI Copilot is wave 2 and is the first to need it** |
| **Blocked tasks** | **[TASK-431](BACKLOG.md).** Nothing is blocked today — **the cost is paid later, and paid five times** |
| **Lanes waiting** | **None.** This is why it is cheap to rule now |
| **Priority** | **P1 — the only 🔴 in [442](architecture/442-product-led-domain-discovery.md) with no decision behind it** |
| **Recommended** | ✅ **(b) — a domain concept in one owning context, consumed through `public/`.** **The reason is the reuse gate, not taste**: *"a port belongs to the module that owns the language it represents"* (§6), and **approval is a language the whole product speaks** — which is exactly what distinguishes it from the five existing supersessions, each of which is one module's own vocabulary. **(a)** puts a shared concept in frozen substrate; **(c)** is the five-implementations outcome, and it is unpickable afterwards because each copy will be load-bearing for its own screen |

## 📌 TASK-433 · `Segment` already means something else

| | |
|---|---|
| **Summary** | **[442 §F2](architecture/442-product-led-domain-discovery.md).** The App Shell applies global scope *"before a module renders"* and **all 16 screens inherit it**; **Companies** needs *"saved views and segments"*; **Global Search** needs *"saved and monitored searches"*. **`saved_view`, `saved search`, `monitored` — zero matches repository-wide** |
| **The collision** | **`commercial_profile` owns `Segment`** — a named ICP segment with its own state machine, meaning ***who buys***. **Companies' "segment" is a saved filter over a list of accounts.** **Two concepts, one word, and the word is already in the ubiquitous language** — §4: *"never repurpose a term from one module inside another"* |
| **What this does *not* ask** | ⛔ **[O3](DECISION_REGISTER.md) stays deferred.** O3 asked **where shell services live**; this asks **whether a saved view is a domain concept, and what it is called.** *"No further preparation"* is respected — no placement is proposed here |
| **Impact** | **Five screens**, and the shell inherits into all sixteen |
| **Lanes waiting** | **None** |
| **Priority** | **P2 — trivial now, a rename across a bounded context later** |
| **Recommended** | ✅ **Rule the name before the second one is built.** **Lane C's suggestion is `SavedView` for the filter and `Segment` unchanged for the ICP concept** — the customer says *"my saved view"* and *"my segment"* about different things already, so [ADR-0034](architecture/adr/0034-ubiquitous-language.md)'s test is satisfied without inventing anything |

## C-225 · Wave 1's technology stack section has no route

✅ **Answered by delivery.** Wave 1 shipped **ten sections, not eleven** — [414](architecture/414-wave-1-account-360.md) was corrected before anything was built, and **Lane A built the ten.** **The product owner's half of this item — *does wave 1 ship the subset or wait* — is answered by the subset having shipped.** What remains is **Lane B's**: whether `knowledge_graph` gets a route for `USES_TECHNOLOGY`, which is a capability with no customer-facing edge. **No decision needed from you.**

## C-329 · Lane B had nothing claimable, and the row that said otherwise

✅ **Substance addressed 2026-08-05.** Both halves were acted on: **[C-412](LANE_COORDINATION.md) was corrected** — it named the wrong lane on *both* pairs — and **`lane-c-product-office` was measured and holds nothing** *(59 ahead, 268 behind, zero files newer)*. **Closure is Lane B's**, which raised it. **No decision needed from you.**


---

# ⏸️ Deferred by you — do not work these

**Recorded so nobody re-raises them, and so the trigger is written down rather than remembered.**

| ID | Summary | Trigger |
|---|---|---|
| **C-320** | No environment can complete a sign-up | **Highest of this group. After the current engineering wave** |
| **C-322** + **C-002** | *Is an ICP a description or a filter?* · customer-language anticorruption | **When Epic B1 begins. Grouped, not split** |
| **C-210** + **C-203** | Personal data · rendering a person's name | **[TASK-429](BACKLOG.md) — M-E · Provider Enrichment**, which is now the row that carries them. *(Was *"with future People Intelligence work"*; [D-074](DECISION_REGISTER.md) split that into four milestones and **these two belong to exactly one of them** — no person's name exists to render before M-E, and none of M-D or M-I S3 produces one)* |
| **C-020** | M7 scope | **Explicitly deferred.** ⚠️ Half stale — Timeline has a design, and [C-215](LANE_COORDINATION.md) is queued to Lane B as buildable work |
| **C-025** | M13 is not a module | Deferred |
| **C-005** | Who owns the signal-profile write path | **When implementation reaches the feature** |

> ⚠️ **[C-002](LANE_COORDINATION.md) is deferred and still load-bearing.** It is the live scope bound on **[TASK-903](BACKLOG.md)**: *display the declarations, assert no match.* **Deferred does not mean inert.**

# 📎 Standing — blocks nothing being built

**C-003** three wire codes for one condition · **C-006** which lane owns `test_api_<module>.py` *(16 files)* · **C-007** the guided first run is a two-lane build · **C-009** an internal fault reaches a customer as a `422` · **C-011** a contraction risk reads like a small opportunity *(**[TASK-905](BACKLOG.md)** is this, queued to Lane A)* · **C-014** accessibility and performance testing · **C-017** the onboarding honesty principle · **C-204** the catalog explains nine words to nobody · **C-211** where an approach brief lives · **C-212** which product an opportunity is about · **C-223** `competitor_entry` across a boundary *(**resolved in principle by C-328's ruling** — same shape, same answer)*

> **No action, by ruling:** *"Continue collecting evidence. Do not spend engineering effort on these until implementation naturally reaches them."*

# 🔧 Open, and not yours

| | Owner | |
|---|---|---|
| **C-214** | **Lane B** *(joined from `modules.toml`)* | Its own text says *"Implementation impact. Blocks nothing"* |
| **C-215** | **Lane B** | **Not a decision — a finished specification.** Queued as [TASK-902](BACKLOG.md) |
| **C-216** | **QE** | Same defect as [B-105](BUGS.md), open in two registers |
| **[436](architecture/436-execution-isolation.md) ③b and ④** | **QE** | The `conftest.py` guard and certification asserting its own isolation. **Designed in full; scheduled by QE** |

---

## Closed on 2026-08-05

**C-019** the claim protocol already implements it · **C-008** ruled 2026-08-03, stage 1 shipped · **C-205** **responsive web is officially part of Signora**; native mobile is a future roadmap item · **C-200** deferral confirmed · **C-012 · C-013 · C-021 · C-207** — **all four by [ADR-0404](architecture/adr/0404-platform-composition.md)**

# Product Owner Decision Queue

**The single place the product owner reviews when making rulings.** Established 2026-08-05 by product owner directive.

> ## ⚠️ Four items, and one is a Product Office miss. Three others are waiting and you are holding all three deliberately.
>
> ⚠️ **[C-332](#c-332--the-predicate-landed-and-task-406-still-cannot-call-it) — Lane B found that a promoted capability has no reachable caller, and it falsifies a claim this office published.** **[TASK-406](BACKLOG.md) is blocked whole.**
>
> ⚠️ **[C-419](#c-419--the-six-verbs-have-no-representation-and-17-surfaces-one-contract-is-undecided) — the six verbs have no representation, and mounting the assistant would let every member spend a model call on every page.** **Blocks nothing; wave 2 reaches this screen next.**
>
> ⚠️ **[C-418](#c-418--does-signora-forecast-revenue) — the Executive Dashboard's first word is *forecast* and a ratified principle refuses to forecast.** **Blocks nothing** — five of the screen's six sections ship without it — **and it decides four missing concepts at once.**
>
> ⚠️ **[C-417](#c-417--adr-0404-approved-three-platform-capabilities-and-its-owner-may-not-finish-two-of-them) — raised today, and it is in front of seven slices and a starving lane.** **ADR-0404's own §Validation caught it before the first line was written**, which is the good news; **the ADR is Lane C's, which is not.**
>
> ✅ **The previously time-critical row is ruled.** **[TASK-434](BACKLOG.md) is `READY` at the head of the queue**, sequenced ahead of TASK-406's backtest by [D-077](DECISION_REGISTER.md) — *"establish the reusable capability once rather than allowing multiple implementations to emerge independently."* **The window closed with the capability on the right side of it.**
>
> **① [Placing TASK-427](#-task-427--the-people-domains-trigger-has-fired-and-placing-it-is-yours)** — **the People domain.** Its trigger has already fired.
> **② [TASK-431](#-task-431--six-screens-assert-one-guarantee-and-the-repository-has-no-word-for-it)** — six approved screens assert one guarantee; the repository has no word for it.
> **③ [TASK-433](#-task-433--segment-already-means-something-else)** — one word, and it costs a sentence today.
>
> **①–③ are held in the planned sequence at your instruction** — *"I will review their individual architectural shape separately."* **Discovery has not waited on them** ([D-075](DECISION_REGISTER.md)): **[443](architecture/443-account-matching-capability.md) and the [Domain Discovery Register](DOMAIN_DISCOVERY_REGISTER.md) were both produced while they sat here.**
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
| **The vocabulary** | `Owner` and `Match` — **C-420 ruled** ([D-087](DECISION_REGISTER.md)). **Qualified, not renamed** |

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

## ⏱️ TASK-434 · The only time-critical row on this page

**Not a shape question — you asked Product Office to determine the architectural home and [443](architecture/443-account-matching-capability.md) determines it, at 🟠 with no ADR and no new dependency edge.** **What is yours is *when*.**

| | |
|---|---|
| **Why now** | **[TASK-406](BACKLOG.md) is `IN PROGRESS` with Lane B**, and its acceptance criterion is *"**the backtest reports both cohorts, never in-ICP alone**"* — **which requires a predicate deciding which an account is.** **Measured on `integration`: no matching code has landed.** The window is open **by days** |
| **Impact if it closes** | **Sixteen consumers** inherit whichever interpretation TASK-406's backtest happened to need — including **Workflow rule conditions**, **Epic E1's CRM arrival** and **AI Research cohorts**, none of which was on any list |
| **The ownership answer** | **`commercial_profile`, and explicitly *not* because TASK-406 needs it first** — **the criterion vocabulary is defined there and evaluating elsewhere means a second copy of it.** **The move that makes it fit: the contract forbids that module from *reading* the pipeline and does not forbid it from being *given* facts.** **`evaluate(criteria, attributes)` is pure** — zero new edges, `lint-imports` unchanged |
| **⚠️ The finding that makes it foundational** | **The two sides do not speak the same language.** A customer types `SaaS`; a provider reports `Computer Software`; **string equality returns `False` and the account silently drops out of its own ICP.** **`unmeasured` must be a value in the type, never `false`** |
| **Blocked tasks** | **None today.** **This is the argument for acting, not against it** |
| **Lanes waiting** | **None.** Lane B is building TASK-406 and would consume this rather than wait for it |
| **Priority** | **P0 on timing · P3 on difficulty.** Two small slices |
| **Recommended** | ✅ **Sequence [TASK-434](BACKLOG.md) ahead of TASK-406's backtest slice.** ⚠️ **First slice is a prerequisite regardless of any of this**: **`commercial_profile/public/` publishes thirteen views and *not one is the ICP* — no module can read the criteria at all today**, and every one of the sixteen consumers is blocked on that one missing read port. **[ADR-0403](architecture/adr/0403-signal-engine-reads-a-declaration.md) is the ratified precedent for exactly this shape** |

## C-332 · The predicate landed and TASK-406 still cannot call it

⚠️ **Raised by Lane B, and it falsifies a claim this office published.** **[443](architecture/443-account-matching-capability.md) and [TASK-406](BACKLOG.md)'s row both say *"the per-criterion lift half is unaffected and needs nothing new."* Lane B measured that and it is wrong.**

| | |
|---|---|
| **The problem** | **`evaluate(icp, observed)` shipped and is correct. Nothing in the repository constructs an `ObservedAttributes`, and the module ruled to do the measuring is forbidden from every module that could** |
| **Why this office missed it** | ⚡ **[443](architecture/443-account-matching-capability.md) made the function pure *specifically* to avoid the import contract — *"the facts are handed to it"* — and never asked **who hands them.** **The same class as [ADR-0404](architecture/adr/0404-platform-composition.md)'s §Validation, which checked that `apps/worker` had an owner and never checked who owned the trees the capability reached.** **Twice now: a boundary designed without asking who stands on the other side** |
| **What is verified** | `ClaimReader.for_subjects` keys on `SubjectRef`, a *provider* identity. **The `entity_id → SubjectRef[]` binding lives only in `knowledge_graph`.** ⛔ **`pyproject.toml` forbids `opportunity_engine → knowledge_graph` in full.** ⛔ **The score carries *"no name, no domain, no industry"*, deliberately.** ⛔ **And [C-328](LANE_COORDINATION.md) already ruled the opposite direction shut** |
| **Impact** | **[TASK-406](BACKLOG.md) whole — both halves.** Lane B returned it to `BLOCKED` and wrote no code, correctly |
| **Priority** | **P1 — a promoted capability with no reachable caller** |
| **Proposal** | ⚡ **[462](architecture/462-observed-attributes-proposal.md), prepared 2026-08-06 on your instruction — and it changed its own recommendation while being written.** **`GraphQueries` and `ClaimSet` are *already published*, so the first reading — *"there is no reader"* — was wrong.** **The real argument is that `ClaimSet` publishes *evidence* where a resolved *fact* is needed: it hands a caller three providers disagreeing about an industry and no rule for settling it, and a consumer projecting that is a second resolver — which this repository has refused in writing twice.** **With eight consumers of R-00, *"the caller projects it"* means up to eight rules for what an account's industry is, and the disagreements would be invisible** |
| **Recommended** | ✅ **`knowledge_graph` publishes an `AccountAttributesReader` in its `public/`** — canonical `industry`, `country`, `employee_count` per entity — **and `opportunity_engine` gains a `public/`-only edge.** ⚡ **[ADR-0403](architecture/adr/0403-signal-engine-reads-a-declaration.md) is the exact precedent for a different pair**: a new edge to `public/` alone, the reader shaped as the module's existing `View · Reader` triple, no inner layer reached. **A new cross-module edge is 🔴 and needs an ADR; the shape does not need inventing** |
| **Alternative, if the edge is refused** | **The projection travels as an event.** ⚠️ **More machinery, and it makes a measurement depend on delivery** — recorded so the cheaper option is a choice rather than an assumption |

## C-419 · The six verbs have no representation, and *17 surfaces, one contract* is undecided

**Found by [445](architecture/445-ai-copilot-traceability-audit.md) — the first Screen-by-Screen Domain Traceability Audit, on the screen wave 2 reaches next.**

| | |
|---|---|
| **Two halves** | **[410](architecture/410-approved-ui-specification.md) asserts *"**six verbs and no others**"* and *"17 surfaces, one contract."*** ⛔ **No verb taxonomy exists in any `domain/` layer** — six values the design calls closed, and nothing closes them. **And seventeen endpoints is seventeen chances for one of the five guarantees to differ, with no way to check that it did not** |
| **What already argues one way** | ✅ **The guarantees are already single** — `GroundedOutput`, `EvidenceRef`, `SupportBasis` and the never-repairing validator are one implementation each. **The contract is a platform capability in substance today** |
| **Impact** | **Nothing blocked.** [TASK-202](BACKLOG.md) waits on C-222 for unrelated reasons |
| **Lanes waiting** | **None** |
| **Priority** | **P2 — free now, and it decides a module's published language** |
| **Recommended** | ✅ **The verb taxonomy and surface identifier go in `ai_reasoning_engine`'s `public/`; the 17 surfaces are consumers, not variants.** **§6's rule, not preference**: *"a port belongs to the module that owns the language it represents."* **Put it in the frontend and the closed set stops being closed the first time a screen wants a seventh.** **Trade-off stated: one parameterised route reads less obviously than seventeen named ones** — and the repository took that trade before, deliberately: the provider registry *"exposes `for_model(model)` and no vendor-keyed lookup, so business code that cannot name a vendor cannot branch on one"* |
| ⚠️ **A separate, cheaper finding** | **There is no `Resource` for reasoning.** `Resource.RESEARCH` exists because *"reading an account is free and asking for research spends a model call… without it every reader becomes a spender."* **AI Copilot is 17 surfaces on pages every member already reads** — mounted without the same separation, **it grants every member the ability to spend, on every page.** **One `Resource` and two policy lines**, which [C-224](LANE_COORDINATION.md) already makes a lane's to register |

## C-418 · Does Signora forecast revenue?

**Found by [444](architecture/444-executive-dashboard-domain-assessment.md), assessing the Executive Dashboard to its domain — not by implementation reaching it.**

| | |
|---|---|
| **The conflict, in two quotations** | **[410](architecture/410-approved-ui-specification.md) describes the screen as *"CEO/CRO homepage — **forecast**, risk, ageing, movements."*** **`buying_score_engine` says, twice, in its own code: *"**No probability, no likelihood, no prediction.** A buying score prioritizes commercial attention; **it does not forecast a purchase**."*** **The approved UI's first word contradicts a ratified principle, in the module the forecast would come from** |
| **Four absences, one question** | **`Opportunity` has no amount, no currency and no close date · `quota`/`target_amount`/`forecast` return nothing · `fiscal` returns zero · there is no `Team`, no `manager_id`, no `reports_to`.** **Answer the question and all four follow, or none do** |
| **Impact** | **None today.** **[TASK-438](BACKLOG.md) delivers five of the screen's sections without it** — conversion, ageing, movement, roll-up by owner, and ICP coverage |
| **Lanes waiting** | **None** |
| **Priority** | **P2 — cheap now, and it decides four things at once** |
| **Recommended** | ✅ **B for now — pipeline health — and A only behind Epic E1**, stated as a sequence rather than a refusal. **A forecast needs a deal value, and the value must come from the customer's CRM rather than a text box** ([ADR-0036](architecture/adr/0036-target-account-contract.md): *"asking them would be asking a customer to do resolution"*). **A forecast built before [TASK-402](BACKLOG.md) lands is a forecast over numbers nobody entered.** ⚠️ **[417](architecture/417-executable-slice-audit.md) reached the same split independently** — *"the AI projection is BLOCKED BY PRODUCT"* |
| **The consequence nobody has hit** | **Every grant today is workspace-wide.** **A roll-up by owner is everybody's performance on one page**, and this is **the first approved screen whose data is sensitive between colleagues rather than between tenants.** **Recorded, not proposed — it becomes real only on answer A** |

## C-417 · ADR-0404 approved three platform capabilities, and its owner may not finish two of them

**Found by running [ADR-0404](architecture/adr/0404-platform-composition.md) §Validation before the first slice — which is what that section is for.** **The ADR is Lane C's own, so this is this office's error surfacing exactly where it was designed to surface.**

| | |
|---|---|
| **Summary** | **The platform edit is Lane C's. The proof it worked is five files in `backend/modules/`, and §20e forbids Lane C from touching that tree** — ⚫ *refactor a module you are not assigned* |
| **Why the halves cannot be split** | **`mypy strict = true` implies `warn_unused_ignores`.** The moment `PublishableEvent`'s members become read-only, the five `# type: ignore[arg-type]` go unused and **the gate fails.** **Platform change and five one-line deletions are one atomic change whether anybody likes it or not.** Capability ① is the same shape — the two `EventHandler` implementations are in `modules/` |
| **What the modules already said** | **`observation_engine/application/record.py:120`, in the code, before this item existed:** *"the platform's `PublishableEvent` Protocol declares settable members, which frozen domain events cannot satisfy. **Raised as a finding, not fixed here.**"* **Three modules carry that comment. They declined to cross the boundary, correctly — and ADR-0404 is the fix they were waiting for** |
| **Impact** | **[TASK-418](BACKLOG.md) ① and ②, and [TASK-901](BACKLOG.md)'s seven slices behind them.** ⚠️ **TASK-901's slices are the only prepared work left for Lane A, whose queue is 0 of 5** |
| **Lanes waiting** | **Lane C now. Lane A when its two in-flight rows land** |
| **Priority** | **P1 — it is in front of seven slices and a starving lane** |
| **Recommended** | ✅ **A bounded, named exception**: *the slice may delete `# type: ignore[arg-type]` comments at publish sites and may change no other line in `backend/modules/`*. **Five deleted comments, provably behaviour-free, and a reviewer can verify the bound from the diff alone** — the same standard §20a's carve-out already uses for a `Resource` member. **The alternative that bends no rule delivers the capability never**: those comments have sat there for weeks precisely because no slice makes anybody touch them |
| ⚠️ **Two corrections to the ADR, same validation** | **It says *"all eight"* ignores; there are **five** at publish sites** — the other three are `provider_normalization` (×2) and `ai_research_engine` and none is at a publish site. **And §Validation checks that `apps/worker/` has an owner but never checks that the *modules* the change reaches have one** — which is the check that would have caught this at ratification |

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

> ✅ **C-011 left this list 2026-08-05, closed by delivery.** It was *"a contraction risk reads like a small opportunity"*, and **[TASK-905](BACKLOG.md) is that item built** — shipped by Lane A the same day. **`--check` reported it as ruled-and-still-queued within the hour**, which is the queue doing its job: **an item that resolves by delivery leaves no ruling behind**, so nothing but the checker would have noticed.

**C-003** three wire codes for one condition · **C-006** which lane owns `test_api_<module>.py` *(16 files)* · **C-007** the guided first run is a two-lane build · **C-009** an internal fault reaches a customer as a `422` · **C-014** accessibility and performance testing · **C-017** the onboarding honesty principle · **C-204** the catalog explains nine words to nobody · **C-211** where an approach brief lives · **C-212** which product an opportunity is about · **C-223** `competitor_entry` across a boundary *(**resolved in principle by C-328's ruling** — same shape, same answer)*

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

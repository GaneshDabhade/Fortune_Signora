# Product Owner Decision Queue

**The single place the product owner reviews when making rulings.** Established 2026-08-05 by product owner directive.

> ## ⚠️ Two things are waiting on you.
>
> **① An owner for `signora_platform/`** — [TASK-418](BACKLOG.md) and **[TASK-901](BACKLOG.md)'s seven slices** sit behind it. **② [C-224](#c-224--a-new-write-surface-needs-an-authorization-resource-and-two-rules-disagree-about-who-may-add-one)** — small, and every future write surface hits it.
>
> **The 2026-08-05 ruling cleared every item that existed when it was made.** Two have arrived since. **Fourteen approved, three confirmed, eight deferred, three closed** — and the four platform items collapsed into one ADR. **Every remaining row below is either deferred by you or blocks nothing being built.**
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

**Six tasks and seven slices, from one sitting.**

## How this stays true

**Two kinds of column.** **Derived** — status, blocks, lanes waiting — computed from [`LANE_COORDINATION.md`](LANE_COORDINATION.md), [`BACKLOG.md`](BACKLOG.md) and [`modules.toml`](coordination/modules.toml). **Judgement** — priority, recommendation, cost — Lane C's.

> **`python3 infra/decision-queue.py --check` fails when this file and the register disagree.** It reported every ruled row still sitting here within a minute of the ruling, which is how this rewrite got scoped.

---

## C-224 · A new write surface needs an authorization `Resource`, and two rules disagree about who may add one

✅ **On `integration` at `b6313ed`** — it promoted with cycle 58, so it is **actionable now**, not pending. *(I first wrote that it was still on a lane branch. It is not; `--check` found it in the register, which is why the check reads the register rather than trusting the queue.)*

| | |
|---|---|
| **Raised by** | **Lane A**, implementing [TASK-405](BACKLOG.md) — **at the route, after the domain, persistence, use case and read surface were complete and green** |
| **Summary** | A signal's resolution must call `context.authorize(Resource.?, Action.?)`. **None of the thirteen existing resources is a signal.** Adding one takes **two files with opposite authorities** |
| **The conflict** | `enforcer.py`'s `Resource` enum is **🔴 — product owner + ADR** *(`signora_platform/**`)*. `policy.csv` is **any lane, append-only** *(§20e, "registries every lane extends")*. **They are one registration in two files**: a policy row naming an absent enum member is unreachable; an enum member with no policy row denies everyone |
| **Impact** | **One route** — `POST` a resolution. **TASK-405 is not blocked**; everything else shipped |
| **Lanes waiting** | **Lane A**, for one route. And **every future write surface** hits this |
| **Priority** | **P2 — small, and it recurs** |
| **Recommended** | ✅ **Ratify what the repository has already done twelve times.** **Every resource after `workspace` and `member` was added by a feature lane**, three with inline justifications citing §20a — *"a use of the platform rather than a change to it."* **Amend §20a's carve-out to name authorization resources explicitly**, so the practice becomes the written rule instead of twelve separate justifications. **The safety argument points the same way**: an enum member alone **grants nothing** — `policy.csv` grants, and that file is *already* any-lane append-only. **The 🔴 half is the harmless half** |


---

# ⏸️ Deferred by you — do not work these

**Recorded so nobody re-raises them, and so the trigger is written down rather than remembered.**

| ID | Summary | Trigger |
|---|---|---|
| **C-320** | No environment can complete a sign-up | **Highest of this group. After the current engineering wave** |
| **C-322** + **C-002** | *Is an ICP a description or a filter?* · customer-language anticorruption | **When Epic B1 begins. Grouped, not split** |
| **C-210** + **C-203** | Personal data · rendering a person's name | **With future People Intelligence work**, alongside the narrowed C-221 |
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

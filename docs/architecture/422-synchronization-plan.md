# 422 — Synchronization plan: 57 commits → `integration`

> **Lane C — Product Office, 2026-08-04.** **Prepared for review. Nothing is executed.** Audited at file level against `origin/integration`, not from commit titles.
>
> **This is a synchronization exercise, not a rebase.** The objective is the correct repository state in the smallest, cleanest set of changes — **not the preservation of 57 historical commits.**

## 1 · The measurement

| | |
|---|---|
| Commits ahead | **57** · behind **151** |
| Merge base | `47cdfd0` |
| Files touched | **44** — **27 pure additions, 17 modifications** |
| Lines in new Lane C documents | **3,784** |

> **The 27 additions carry almost all the value and can conflict with nothing.** They are `docs/architecture/4xx` and `adr/04xx` — **Lane C's identifier block, which exists precisely so this is true.** `git checkout` of those paths onto `integration` is a clean, complete transfer.
>
> **The entire risk is in the 17 modifications, and most of them should not be replayed at all.**

## 2 · Classification

### Category 1 — already represented on `integration`

**Verified present upstream. Replaying any of these would re-litigate a settled state.**

| | Evidence |
|---|---|
| **C-223 · C-326 · C-321** register work | All three present in `LANE_COORDINATION.md` on `integration` |
| **B-400** | **Fixed upstream, the opposite way to my recommendation and the better way** — the unpromoted chain moved |
| **TASK-400 · 401 · 402** | Present in `BACKLOG.md` on `integration` |
| **ADR-0403's implementation** | `competitor_entry` in the catalog; `generate.py` imports `DeclaredCompetitorReader` |

**Action: none.**

### Category 2 — reporting history that needs no replay

| | Why |
|---|---|
| **`PROJECT_STATUS.md`** *(4+)* · **`SESSION_HANDOFF.md`** *(15+)* | ⚠️ **These are QE's files** (`CLAUDE.md` §20e). **Lane C should not have edited them.** Integration's versions are newer and measured from the promoted commit |
| **`ACTIVE_ASSIGNMENTS.md`** *(195+/5-)* | Operational metadata. **Integration's board carries TASK-200–203, which my copy has never seen.** The product owner already ruled this is reconciled through integration, not by Lane C |
| **~20 commits of the assignment-era arc** | `027aa01` · `1f4a02b` · `52ce116` · `1280cab` · `0794549` · `e444ba7` and neighbours |

**Action: drop. Do not replay.**

### Category 3 — superseded by later repository changes

| | Superseded by |
|---|---|
| **The assignment-delivery model** | **Recommend-only**, then the product owner assigning directly. **Integration's board already shows the newer model** |
| **`C-413`** | **Withdrawn the day it was opened.** Absent from `integration`, and correctly so |
| **`C-400`** | **Answered** — the identifier-block rule it asked for is in `CLAUDE.md` |
| **`B-400` row** | Category 1 — fixed upstream |
| **Root `ACTIVE_ASSIGNMENTS.md` deletion** | ⚠️ **Still present on `integration`.** The dead duplicate I deleted is still there — **2,661 B against the live 40,634 B, zero inbound references.** This one is **not** superseded and moves to category 4 |

**Action: drop, except the root-file deletion.**

### Category 4 — still required on `integration`

| | Size | Conflict risk |
|---|---|---|
| **27 new documents** — `400`–`422`, `adr/0400`–`0403` | 3,784 lines | **None.** Lane C's identifier block; absent upstream |
| **`DECISION_PACKS.md`** | 405+/117- | **None — `integration` has not touched it since the merge base** |
| **`18-authentication.md`** | 8+/2- | **None — untouched upstream** |
| **`BACKLOG.md` — only TASK-403–410** | 8 rows | **Low.** Append-only into the READY section |
| **`05` · `25` · `37` · `40` · `43` · `adr/README`** | 20 lines total | **Low.** Small notes; upstream moved separately |
| **Delete root `ACTIVE_ASSIGNMENTS.md`** | −2,661 B | **None** |

### Category 5 — rulings needing minimal, hand-applied updates

| | Why it cannot be replayed |
|---|---|
| **`CLAUDE.md` — three amendments** | **`integration` has independently rewritten Lane C's section** — it now reads *"Product Office & Architecture Office"* with *"Four responsibilities, and they do not overlap"*. **My 251 lines were written against text that no longer exists.** This is **semantic merge risk** ([`PRODUCT_OFFICE.md`](../PRODUCT_OFFICE.md) §3) — the class that is invisible to git and the most expensive |
| **`ADR-0300` status** | On `integration` it still reads **`Status: Proposed`**. Lane B is correctly treating C-326 as unruled. **One line, on Lane B's ADR** |

**The three `CLAUDE.md` amendments, re-applied rather than replayed:** the **Standard Lane Report** (§20e) · **Lane C's Platform Foundation remit** (§20e, resolving C-010) · **the Fortune/Signora naming convention** (§4).

## 3 · The plan — six commits, not fifty-seven

| # | Commit | Contents | Risk |
|---|---|---|---|
| **1** | **Lane C's document set** | `git checkout lane-c-product-office -- docs/architecture/4*.md docs/architecture/adr/040*.md` — **27 files, one commit** | **None** |
| **2** | **Decision packs and the authentication note** | Two files `integration` has not touched | **None** |
| **3** | **TASK-403–410** | Eight READY rows appended | **Low** |
| **4** | **Six small architecture notes** | `05` · `25` · `37` · `40` · `43` · `adr/README`, applied by hand | **Low** |
| **5** | **`CLAUDE.md` — three amendments, re-applied** | Written onto `integration`'s current §4 and §20e. **Hand-applied, read once against the live text** | **Medium — the only one** |
| **6** | **Two deletions and one status line** | Root `ACTIVE_ASSIGNMENTS.md` deleted · `ADR-0300` → `PRODUCT OWNER APPROVED` | **None** |

**Explicitly excluded:** `PROJECT_STATUS.md` · `SESSION_HANDOFF.md` · `ACTIVE_ASSIGNMENTS.md` · every assignment-era commit · every superseded register row.

> **Six commits replace fifty-seven, and five of the six carry no conflict risk at all.**

## 4 · Who performs it

**`CLAUDE.md` §20e: a feature lane may push only a claim commit to `integration`; everything else arrives when QE fast-forwards a validated lane branch.**

**This branch will not fast-forward** — it is 151 behind — **so it cannot arrive the normal way, and the product owner has ruled out a large rebase.**

> **Recommended: Lane C prepares the six commits on a fresh branch cut from `origin/integration`, and QE takes that branch through the ordinary lifecycle.** The current branch is then abandoned as history rather than merged.
>
> **This is the smallest, cleanest route**: a branch cut from `integration` fast-forwards by construction, every gate runs against the state that will actually ship, and **Lane C does not verify its own governance** — QE does, exactly as §20e requires.

## 5 · What is deliberately lost, and why that is correct

**Fifty-one commits of Lane C history do not reach `integration`.** They remain in `git log` on `lane-c-product-office`.

> **The repository's rule is that a record of what was true then must not be rewritten** (`CLAUDE.md` §2) — **and it does not require every branch to be merged.** The deliberation is preserved; **what ships is the conclusion.**

**The one thing that must not be lost is the correction itself:** ADR-0400, ADR-0401 and ADR-0402 arrive marked **`PRODUCT OWNER APPROVED`**, never `RATIFIED` alone, and [`PRODUCT_OFFICE.md`](../PRODUCT_OFFICE.md) §11c travels with them — **so a lane reading `integration` learns both the ruling and the lifecycle in the same commit.**

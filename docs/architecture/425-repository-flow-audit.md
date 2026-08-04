# 425 — Repository Flow Audit

> **Lane C — Product Office, 2026-08-04. P0.** Measured against `origin/integration` **after a fresh fetch**, and against every lane branch.
>
> **The audit's first finding is that its premise is false, and that the error is Lane C's.**

## 1 · The finding

> **Neither lane has been idle. Both shipped today. Lane C reported otherwise because it was measuring a stale `origin/integration`.**

**`origin/integration` on 2026-08-04, in one day:**

| Commit | What shipped |
|---|---|
| `605e76f` | **E1 — *"a customer's CRM has a door, and the port it opens onto"*.** The inbound source port, built |
| `da874a5` | **TASK-407** — the connection health probe. **A Lane C slice, claimed and built** |
| `1f4fe1c` | **A-i — *"Signora's conclusion about an account can finally be read"*.** `ai_reasoning_engine`'s interface layer |
| `e5f48d2` | **TASK-301** — Global Search typed grouping and explainable ranking |
| `7a95403` | **A-ii found blocked on C-213** — *"and 417's reuse column is why it did not look it"* |

**Every branch is at the same commit.** `lane-a-product-surface`, `lane-b-commercial-profile`, `lane-qe`, `integration` and `main` are all `797f01f` — **zero ahead of integration.** Everything the lanes built has been validated, certified and promoted.

> **That is not an idle repository. It is a repository between slices, with everything promoted and eight tasks in QE.**

## 2 · Why Lane C reported idleness — the actual defect

**`origin/integration` is a local ref, and it is only as fresh as the last `git fetch`.** Lane C fetched early in the session and then measured against that snapshot for several reporting cycles. **The fetch at the start of this audit advanced it by dozens of commits.**

**Every figure in the last four reports was therefore taken from a repository state that had already been superseded** — including *"Claimable: 4"*, *"both lanes below buffer"* and *"the empty stage is Merged to Integration"*.

> **The irony is exact.** The office that established *a decision is authoritative when ruled and actionable when `integration` records it* **then failed to read `integration`.**

**Fixed, structurally, not by resolving to be careful:** `infra/repository-dashboard.py` now **fetches before measuring** and **prints how far the ref advanced** when it does. *"Never report a number whose age is unknown to the reader."*

## 3 · The eight questions, answered

| | |
|---|---|
| **Why is Lane A not implementing?** | **It is.** TASK-202, TASK-203 active; TASK-200, TASK-204, TASK-400 in QE. **Two rows are genuinely blocked** — TASK-201 and TASK-205 |
| **Why is Lane B not implementing?** | **It is.** TASK-402 in progress; TASK-300, TASK-301, TASK-407 in QE |
| **Genuine engineering blockers** | **One: [C-213](../LANE_COORDINATION.md).** `commercial_profile.public` exports `TargetAccountReader` and **nothing about the Buying Committee**, so `sales_engagement`'s interface layer (A-ii / TASK-205) cannot read the roles it needs. **Owner: Lane B. Fix: one `BuyingCommitteeReader` export, shaped like the one beside it** |
| **Process / synchronization blockers** | **`lane-c-sync` — 13 ahead, 26 behind.** It carries the Decision Register, `PRODUCT_OFFICE.md` §11–12, ADR-0400/0401/0402's approvals, C-411/412/413 and three generators. **None of it is on `integration`** |
| **Blocked only because prepared work is not claimable** | **TASK-405, 406, 409, 410.** ⚠️ **TASK-403 and TASK-404 are not among them** — the lanes did not wait. **They allocated their own ids in their own blocks and built the work** as TASK-204 and TASK-205 |
| **READY slices releasable immediately after synchronization** | **TASK-405** *(Signal Center triage)*, **TASK-406** *(ICP backtest)*, **TASK-409**, **TASK-410** *(Environment Framework, Lane C's own)* |
| **Waiting only on a backlog row** | The four above. **Everything else either exists on `integration` or is blocked on something real** |
| **Reassignable to restore flow** | **C-213 is the highest-value unblock in the repository** — it is one export, it is Lane B's, and it releases A-ii which is otherwise ready |

## 4 · What the lanes did that is worth recording

> **They routed around Lane C rather than waiting for it, and that is the healthiest signal in this audit.**

**Lane B built TASK-407 from a Lane C row that reached it, and independently narrowed C-326 the same way [419](419-c326-narrowed-and-lane-b.md) did** — its board row read *"shipping around the blocker."*

**Lane A did not wait for TASK-403 and TASK-404.** It opened **TASK-204 and TASK-205** in its own identifier block and built the same two interface layers. **The identifier-block rule made that safe** — no collision was possible.

**And one lane corrected Lane C's work in a commit message:** *"A-ii is blocked on C-213, **and 417's reuse column is why it did not look it**."* **[417](417-executable-slice-audit.md) called A-ii *"genuinely thin — the `public/` already exports what the screens render."* It does not export the Buying Committee.** The reuse column was checked against `sales_engagement`'s exports and not against `commercial_profile`'s.

## 5 · Recovery plan

### Immediate — next 24 hours

| | |
|---|---|
| **1** | **Rebase `lane-c-sync` onto the current `integration` and hand it to QE.** 26 behind; the six-commit structure holds and most of it is additive |
| **2** | **Raise C-213's priority with Lane B.** One export, and it is the only genuine engineering blocker in the repository |
| **3** | ✅ **Done in this audit** — the dashboard fetches before measuring |

### Short term — 3–5 days

| | |
|---|---|
| **4** | **Retire TASK-403 and TASK-404** — Lane A built them as TASK-204/205. **Two rows for one slice is the duplicate-truth defect** |
| **5** | **Resolve [C-413](../LANE_COORDINATION.md)** — `knowledge_graph` named by two lanes |
| **6** | **Correct [417](417-executable-slice-audit.md) §2c** — its reuse claim about A-ii was wrong, and a lane found it |
| **7** | **Reconcile TASK-408** — `READY — partly delivered`, because Lane B shipped most of it as TASK-301 |

### Governance — to prevent recurrence

| | Change | Prevents |
|---|---|---|
| **G1** | **A measurement of remote state fetches first, or states its age.** ✅ implemented | **This audit's cause** |
| **G2** | **Lane C's rows are not the only path to work.** A lane may open a row in its own block for prepared work that has not reached `integration`, **citing the Lane C document** — which is what Lane A did unprompted | **Synchronization becoming a hard dependency** |
| **G3** | **Implementation Support Mode's trigger is measured, never inferred** — from a freshly-fetched `integration`, never from a report | **Entering the mode when no lane is idle**, which wastes the office's time and the product owner's |
| **G4** | **A Lane C branch older than one QE cycle is a finding, reported by Lane C.** `lane-c-sync` reached 26 behind without the office noticing | **Prepared work ageing out of relevance** |

## 6 · The honest conclusion

**The repository is not in recovery. It is flowing, and it flowed while Lane C was reporting that it was not.**

> **The bottleneck was never Lane A or Lane B. It was the Product Office's own branch, and the Product Office's own measurement** — and the lanes worked around both without being asked.

**One genuine engineering blocker exists — C-213 — and it is one export.**

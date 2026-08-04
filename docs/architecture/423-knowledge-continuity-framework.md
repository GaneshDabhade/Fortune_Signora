# 423 — Repository Knowledge Continuity Framework

> **Lane C — Product Office, 2026-08-04.** **Prepared, not implemented.** No production code, no new product functionality.
>
> **The brief asked for eight documents. The reuse audit says one is genuinely missing, two should be generated, and five already exist.** That finding is the framework's most important output, because the brief also says *"do not introduce unnecessary documents"* and *"avoid duplicate sources of truth."*

## 1 · The audit — eight proposed against what exists

| Proposed | Already answered by | Verdict |
|---|---|---|
| **`PROJECT_STATE.md`** | **`PROJECT_STATUS.md` §1 — *"Repository, the one-minute view"*** plus §1a lane dashboard, §1b customer capability, §1c dependencies. **QE writes it from the promoted commit** | ⛔ **Duplicate.** A second state document is the defect `CLAUDE.md` §2 names |
| **`SESSION_BOOTSTRAP.md`** | **`README.md` §*"Read these first, in this order"*** — already a numbered list with a *why* per document | ⛔ **Exists.** Extend it |
| **`ROADMAP.md`** | **`IMPLEMENTATION_ROADMAP.md` · `PRODUCT_ROADMAP.md` · `AI_MATURITY_ROADMAP.md`** | ⛔ **Three already.** A fourth is the problem, not the fix |
| **`DESIGN_REFERENCE.md`** | **[410](410-approved-ui-specification.md)** — records the DesignSync project as authoritative, duplicates no design, names the project id | ⛔ **Exists, verbatim to the brief** |
| **`GOVERNANCE_SUMMARY.md`** | **`CLAUDE.md`'s own rulebook table** — *"what are the rules"* against *"where is it performed"* | ⛔ **A summary is a second representation and will drift.** Answer the need with an **index**, never a restatement |
| **`IMPLEMENTATION_STATUS.md`** | Partly: `README.md` module registry · `PROJECT_STATUS.md` §2–§3 · [412](412-backend-capability-matrix.md) · [413](413-migration-inventory.md) | ⚙️ **Generate it.** The per-module × per-layer matrix is real and absent; **hand-maintaining it guarantees drift** |
| **`PROJECT_HISTORY.md`** | Partly: `PROJECT_STATUS.md` §9 · the ADR index · dated records `30`+ · `git log` | ⚙️ **Generate it** from ADR dates, milestone records and Closeout commits |
| **`DECISION_REGISTER.md`** | **Nothing** | ✅ **Genuinely missing. Build it** |

## 2 · Why the Decision Register is the one real gap

**`DECISION_PACKS.md` states its own rule:**

> *"This is a **staging area, not a record**. A pack is deleted when its decision is taken — and the answer lives in the ADR or document it produced."*

**That is correct for packs and it means the repository has no index of rulings.** An ADR records *an architectural* decision; **most Product Owner rulings are not ADRs** — a deferral, a partial approval, a scope ruling, an ownership resolution.

> **The proof is recent and it is Lane C's own.** On 2026-08-04 the product owner ruled nine items at once. **Reconstructing what had been ruled required reading the conversation**, because `DECISION_PACKS.md` had been rewritten and the packs retired. **Three of the nine — O2, O3, C-200 — are deferrals that produce no ADR and would leave no repository trace at all.**

**A deferral is a decision.** *"Do not force a module boundary until implementation naturally reaches M14b"* is as binding as a ratification, and **nothing in the repository records it today.**

## 3 · The documentation hierarchy

**Five tiers, by *how a document changes* — which is what decides whether it can be trusted.**

| Tier | Changes | Examples | Rule |
|---|---|---|---|
| **Constitutional** | Only by product-owner ruling | `CLAUDE.md` · `ENGINEERING_LAWS.md` · ratified ADRs | **Never edited to match reality.** Reality is changed to match it, or the rule is amended |
| **Measured** | **Regenerated every cycle from the promoted commit** | `PROJECT_STATUS.md` · repository metrics · *(proposed)* `IMPLEMENTATION_STATUS.md` | **Never transcribed.** A figure carried forward describes a repository that no longer exists |
| **Operational** | Continuously, by whoever owns the row | `BACKLOG.md` · `ACTIVE_ASSIGNMENTS.md` · `BUGS.md` · `LANE_COORDINATION.md` | **One owner per file.** Append-only where ids are allocated |
| **Durable** | Rarely, and never rewritten | Architecture `01`–`21` · module designs `22`–`29` · Lane C's `4xx` · *(proposed)* `DECISION_REGISTER.md` | **Amended by addition.** A correction is dated, not a rewrite |
| **Historical** | **Never** | Dated records `30`+ · retrospectives · review findings | **Read as history, never as instruction** (`CLAUDE.md` reading guide) |

> **The tier answers the question a cold reader actually has: *can I trust this today?*** Measured — yes, it was regenerated. Historical — only about its date. **Mixing the two is how a dashboard starts describing the previous milestone.**

## 4 · Source-of-truth map

**One question, one document. If a sentence would be true in two, it belongs in one and is referenced from the other.**

| Question | Authority | Owner |
|---|---|---|
| *What are the rules?* | `CLAUDE.md` | Product owner |
| *How is an implementation built?* | `ENGINEERING_LAWS.md` | Product owner |
| *Where are we?* | `PROJECT_STATUS.md` | **QE**, measured at Closeout |
| *What should the next session know?* | `docs/SESSION_HANDOFF.md` | QE |
| *What may I claim?* | `docs/BACKLOG.md` | Product owner |
| *Who is doing what?* | `docs/ACTIVE_ASSIGNMENTS.md` | The claiming lane |
| *What is broken?* | `docs/BUGS.md` | Any lane opens · QE verifies |
| *What is one lane waiting on?* | `docs/LANE_COORDINATION.md` | Any lane opens |
| *What is the architecture?* | `docs/architecture/**` + `adr/**` | Product owner |
| *What does the product look like?* | **[410](410-approved-ui-specification.md)** → the DesignSync project | Product owner |
| *What has been decided?* | ⚠️ **`DECISION_REGISTER.md` — proposed** | Lane C records; product owner rules |
| *What is being decided?* | `docs/DECISION_PACKS.md` — **staging, not record** | Lane C |
| *How does Lane C work?* | `docs/PRODUCT_OFFICE.md` | Lane C |
| *How does QE work?* | `docs/QUALITY_ENGINEERING.md` | QE |
| *Where do I start?* | `README.md` §*Read these first* | — |

## 5 · Session bootstrap — extend `README.md`, do not add a file

**`README.md` already orders the reading.** **Four additions make it a complete cold start:**

1. **[410](410-approved-ui-specification.md) after the pipeline document** — *"what the product must look like"*. A cold session currently learns the architecture and never learns that an approved UI exists.
2. **The proposed `DECISION_REGISTER.md`** — *"what has already been ruled, so you do not re-ask it"*.
3. **A one-line lane-state check:** `git log --oneline -1 origin/integration` and `python3 infra/state-check.py`. **A reading list that does not end in a command leaves the reader unsure whether what they read is current.**
4. **The five-state lifecycle** (`CLAUDE.md` §20e) — *"a decision may be approved and not yet actionable"*, which is the single most confusing thing about this repository's current state.

> **Target: `CLAUDE.md` + `ENGINEERING_LAWS.md` + `21-intelligence-pipeline.md` + `PROJECT_STATUS.md` + `410` + the register + one module design.** **Seven documents to be productive**, and the Operational Reading Cost metric (`PRODUCT_OFFICE.md` §10) already measures whether that stays true.

## 6 · Recovery procedure

**Four scenarios, one path, and the path is short because `integration` is authoritative.**

| Scenario | Procedure |
|---|---|
| **Fresh clone · new laptop** | `git clone` → `git checkout integration` → **`make workstation`** *(installs and reports what it cost)* → `make doctor` *(proposed, [TASK-410](../BACKLOG.md))* → read the seven |
| **Fresh Claude session** | **Read the seven. Then `python3 infra/state-check.py`** — if it disagrees with what you read, **the repository is right and the document is a defect** |
| **New engineer** | The seven, plus `docs/RUNNING.md` for the environment allocation |
| **Restored from backup** | **`git log --oneline -1 main` against `PROJECT_STATUS.md`'s named commit.** If they differ, the dashboard is stale and QE's Closeout did not complete |

> **The recovery test, and it is checkable:** *could a session that has never seen this repository continue the current slice without reading commit history?* **`CLAUDE.md` §12 already sets it for module documentation; this framework applies it to the repository as a whole.**

## 7 · State transitions — what changes, and when

**The five-state lifecycle (`CLAUDE.md` §20e) with its repository consequences made explicit.**

| Event | What changes | Where | By |
|---|---|---|---|
| **Product Owner approves** | A row in `DECISION_REGISTER.md` · the ADR's status | Durable | **Lane C records** |
| **ADR ratified** | ADR status · `adr/README.md` index · any architecture document it changes | Durable | Lane C |
| **Merged to integration** | The ruling becomes **actionable**; `BACKLOG.md` rows become claimable | Operational | **QE** |
| **QE certifies** | Certification record · repository metrics | Measured | QE |
| **Promoted to `main`** | `PROJECT_STATUS.md` · `SESSION_HANDOFF.md` · board reconciled · *(proposed)* `IMPLEMENTATION_STATUS.md` regenerated | Measured | **QE, at Closeout** |
| **Release** | Deferred to M14.5 — **there is no release today** ([ADR-0027](adr/0027-local-first-development.md)) | — | — |

> **Exactly one authoritative document per state, and none of them is a lane report.** **A report is transient by design**; §8 says what must escape it.

## 8 · What must be persisted out of reports

**The test: *would a fresh session need this, and does any document own it?***

| Persist | Where | Why |
|---|---|---|
| **Every Product Owner ruling** | `DECISION_REGISTER.md` | **The gap §2 proves** |
| **Every correction and withdrawal** | The document corrected, dated in place | Lane C's reports carry a *Decisions Made* section precisely so these are visible; **they must land in a file** |
| **Findings reported but not fixed** | `BUGS.md` or `LANE_COORDINATION.md` | Today several live only in commit messages — the C-326 register defect, the duplicate `51`, the *"lanes pull"* heading |
| **Measured counts** | `PROJECT_STATUS.md`, regenerated | Never a report |
| **Do NOT persist** | Progress percentages · dashboard snapshots · narrative status | **Estimates and snapshots go stale the day they are written.** A dashboard file would be a fourth state record |

## 9 · Automation — manual, generated, hybrid

| Document | Class | Note |
|---|---|---|
| `CLAUDE.md` · `ENGINEERING_LAWS.md` · ADRs · architecture | **Manual** | Judgement. **Never generated** |
| **`IMPLEMENTATION_STATUS.md`** *(proposed)* | **Generated** | Routers, events, migrations, test counts, frontend routes — **all countable.** `infra/` already has `reachability.py`, `runtime-composition.py`, `event-catalog.py`, `coverage-debt.py` |
| **`PROJECT_HISTORY.md`** *(proposed)* | **Generated** | ADR dates + Closeout commits + milestone records |
| `PROJECT_STATUS.md` | **Hybrid** | Metrics generated; narrative QE's |
| `DECISION_REGISTER.md` | **Manual** | A ruling is not derivable from the repository |
| `BACKLOG.md` · `ACTIVE_ASSIGNMENTS.md` · `BUGS.md` | **Manual, machine-checked** | `state-check.py` already validates ids and cross-references |

> **The rule: generate what is countable, hand-write what is judgement, and never generate something a human will then edit.** A generated file with hand edits is the worst of both — it drifts *and* nobody trusts the regeneration.

## 10 · Archive strategy

**`CLAUDE.md` §2 forbids rewriting a dated record. Archiving moves a file out of the reading path without altering it.**

**Proposed: `docs/archive/`, flat, with a one-line index. Nothing is edited on the way in.**

| Candidate | Recommendation |
|---|---|
| `docs/REPOSITORY_ARCHITECTURE_PROPOSAL.md` | **Archive** if its proposal is ruled — a proposal in the active path reads as a plan |
| Superseded Lane C preparation, once its epic ships | **Archive**, not delete |
| Dated records `30`+ | **Keep in place.** They are already marked historical by the reading guide and are cited by later documents |
| Every ADR | **Never archived** |
| Operational duplicates — e.g. the root `ACTIVE_ASSIGNMENTS.md` | **Delete.** *"Do not archive operational documents that should simply disappear"* |

> **Recommend archiving nothing today.** Twenty-four root and `docs/` documents is not clutter, and **an archive created before it is needed is a second place to look.** The structure is defined now so that the first genuine candidate has somewhere to go.

## 11 · Recommended implementation plan

| | Step | Size | Depends on |
|---|---|---|---|
| **1** | **`DECISION_REGISTER.md`**, seeded with the nine rulings of 2026-08-04 and every prior ruling recoverable from `ADR-0100` and the retired packs | **Small** | — |
| **2** | **Extend `README.md`'s reading list** — four additions, §5 | **Small** | 1 |
| **3** | **Persist the findings currently living only in commit messages** into `BUGS.md` / `LANE_COORDINATION.md` | **Small** | — |
| **4** | **Generate `IMPLEMENTATION_STATUS.md`** — an `infra/` script, Lane C's under Platform Foundation | **Medium** | — |
| **5** | **Generate `PROJECT_HISTORY.md`** | **Small** | 4 |
| **6** | **`docs/archive/` + index**, empty until needed | **Small** | — |

**Steps 1–3 need no decision and are the whole continuity gain.** **Steps 4–5 are `infra/` work and belong to the Environment Framework queue.**

> **Five of the eight proposed documents are not created, and that is the deliverable.** The repository does not need more documents; **it needs one missing register, a reading list that names the design project, and findings that stop living in commit messages.**

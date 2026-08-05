# 428 — The Lane Coordination Model: one source of truth that does not wait for a merge

> **Lane C — Product Office, 2026-08-04.** **PREPARED — READY FOR PRODUCT OWNER.** Prepared on the product owner's instruction: *"come up with a good scalable lane coordination model so that these kinds of conflicts won't be faced, or even if faced will be handled gracefully… a single source of truth for bug, dependency, module, epic, task, slice assignment which will always be updated and won't depend on code merge to the `integration` branch."*
>
> **Nothing here is implemented.** §2 — *governance describes reality; it never quietly changes it.*

## 1 · The diagnosis, measured rather than felt

**Four coordination documents carry the repository's entire execution state.** Measured on `origin/integration` at `2591951`:

| File | Lines | Commits touching it | Who writes it |
|---|---|---|---|
| [`ACTIVE_ASSIGNMENTS.md`](../ACTIVE_ASSIGNMENTS.md) | 165 | **133 — the highest-churn file in the repository** | **Every lane** |
| [`LANE_COORDINATION.md`](../LANE_COORDINATION.md) | **4 735** | 111 | **Every lane** |
| [`BUGS.md`](../BUGS.md) | **3 212** | 73 | **Every lane** |
| [`BACKLOG.md`](../BACKLOG.md) | 565 | 47 | Product owner · Lane C · claiming lanes |
| | **8 677** | **364** | |

> **Three failures have been observed this week, and they are not three problems.** They are three consequences of one storage decision.

| Observed | What actually happened | Property that caused it |
|---|---|---|
| **Conflict** | `ACTIVE_ASSIGNMENTS.md` conflicted on rebase **twice in one session** — two lanes editing two different rows of one table | **Shared file** |
| **Staleness** | [C-213](../LANE_COORDINATION.md) named an owner **correct on 2026-08-03 and wrong on 2026-08-04**. The lane that could act would not; the lane named could not. **TASK-205 was blocked for two days by one word** | **Copied fact** |
| **Invisibility** | Lane A idled for several reporting cycles on three artifacts that existed only on a Product Office branch | **Travels the code pipeline** |

**The one sentence:**

> **Coordination state is stored as prose, in shared files, that travel the same pipeline as code.** *Shared* is why it conflicts. *Prose* is why it goes stale. *Travelling the pipeline* is why it is invisible until QE promotes it.

**None of the three is a discipline failure.** Every lane followed the protocol exactly. C-213 in particular was written correctly and became false while nobody touched it — **which is the defect class no amount of care can prevent.**

## 2 · The crux — C-213 could not have happened

**This is the design decision; everything else is mechanism.**

**C-213's row copied the assignee into the coordination record.** `owner: Lane B (commercial_profile)`. When `commercial_profile` moved to Lane A, **one fact now had two representations, and only one of them was updated.**

> **`CLAUDE.md` §2 already rules this: *truth has exactly one authoritative representation; everything else derives from it.* And the repository already knows the consequence — *"a stored copy of a derivable fact is a defect waiting for the two to disagree."***

| | |
|---|---|
| **Today** | A record stores **the module** *and* **the assignee.** Moving a module requires an audit to find every copy — **which is exactly the audit the product owner ordered on 2026-08-04**, and it found two rows by grep |
| **Proposed** | A record stores **the module only.** The assignee is **joined from the module registry when the view is rendered** |

**Under the proposed model, moving `commercial_profile` updates every coordination item, backlog row and board row that touches it — atomically, in one edit, with no audit.** A stale assignee stops being *detectable* and becomes **unrepresentable**.

> **That standard is not new here.** §20e chose identifier *blocks* over a collision detector for exactly this reason: *"a block makes it unrepresentable, which is the standard §2 already prefers — a violation that is unrepresentable over one that is merely discouraged."* **This is that ruling applied to assignment instead of to numbering.**

## 3 · The model — three changes, one per failure

| Failure | Change | Why it is structural rather than procedural |
|---|---|---|
| **Conflict** | **One record, one file**, named by its immutable id — `bugs/B-301.toml`, not row 47 of a 3 212-line table | Two lanes editing two records now touch **two files**. Git merges them without conflict **by construction**. **The identifier-block rule already guarantees two lanes never choose the same filename** |
| **Staleness** | **Records are structured data; the boards become generated views** | A field cannot drift from prose that no longer exists. **The markdown a human reads is rendered, not maintained** |
| **Invisibility** | **Coordination commits push direct to `integration`, ungated** | The Task Claim Protocol **already does this** for claims. This widens the payload; it invents no mechanism |

### 3a · Where it lives

```
docs/coordination/
  modules.toml              ← THE registry. module → current assignee. Product owner only
  lanes/lane-b.toml         ← one file per lane; only that lane writes it
  bugs/B-301.toml
  items/C-213.toml          ← coordination items
  tasks/TASK-405.toml
  epics/E1.toml
```

**Generated from it, never hand-edited:**

`ACTIVE_ASSIGNMENTS.md` · the `BUGS.md` index · the `LANE_COORDINATION.md` index · the status columns of `BACKLOG.md`

### 3b · The format is TOML, and the constraint chose it

**PyYAML is not a declared project dependency** (`backend/pyproject.toml`), and adding one is 🔴 + ADR (§6). **`tomllib` is in the Python 3.13 standard library.**

> **So the format is TOML, read with `tomllib`, and it costs nothing.** Humans write it, tooling reads it, generators emit markdown. **Read-only stdlib parsing is a feature, not a limitation:** the tooling can never rewrite a lane's record and lose its wording.

```toml
# docs/coordination/items/C-213.toml
id       = "C-213"
title    = "the Buying Committee is not exported from commercial_profile.public"
opened   = 2026-08-03
by       = "lane-a"
module   = "commercial_profile"      # ← the ONLY assignment fact. No `owner` field exists.
severity = "amber"
state    = "OPEN"
blocks   = ["TASK-205"]
```

> **There is no `owner` field, and that is the entire point.** A record cannot store a stale assignee if the schema has nowhere to put one.

### 3c · Who may write what

**A file boundary now enforces what a sentence used to ask for.** §20e already says *"a lane edits only its own row"* — under one-file-per-record, a lane editing another lane's record is a visible, reviewable, greppable act rather than an invisible line in a shared table.

| File | Writer |
|---|---|
| `modules.toml` | **Product owner only.** The one place assignment exists |
| `lanes/<lane>.toml` | **That lane only** |
| `bugs/B-nnn.toml` | **Any lane creates.** The module's current assignee updates `state`. **Only QE writes `VERIFIED`** |
| `items/C-nnn.toml` | Any lane creates. **Lane C moves `IN ANALYSIS` → `READY FOR PRODUCT DECISION`.** The product owner rules |
| `tasks/TASK-nnn.toml` | The claiming lane, for `state` and `claimed_by`. **Order and scope stay the product owner's** |

**Every one of those rules already exists in §20e.** Nothing new is being asked of anybody — **the change is that the rules are now expressible as file ownership instead of as etiquette inside a shared document.**

### 3d · What does *not* move, deliberately

> **`BACKLOG.md` keeps its hand-written order, and the product owner keeps writing it.**

**Queue order is a judgement, not a fact**, and §20e ratified that *"the queue order **is** the priority"* and *"the board does not define priority."* A record store can hold a task's **state** — claimed by whom, blocked on what — and it must not hold its **rank**. Turning priority into a sortable field is how a queue quietly becomes something a lane can argue with.

**So the split is the one the repository already draws:** the coordination store holds *facts*; `BACKLOG.md` holds *the order*; they never restate each other.

## 4 · How it stops depending on a merge

**The requirement was *"won't depend on code merge to the `integration` branch."* Stated precisely, the dependency to remove is the wait for QE — validate, certify, promote.**

> **That exception already exists and is already guarded.** §20e: *"This is the one thing a feature lane may push to `integration`… a claim commit touches `ACTIVE_ASSIGNMENTS.md` and `BACKLOG.md` and nothing else."* Enforced by `infra/certification-guard.py --audit-claims`, which today reads `CLAIM_PATHS = ("docs/ACTIVE_ASSIGNMENTS.md", "docs/BACKLOG.md")`.

**One line changes.** `CLAIM_PATHS` gains `docs/coordination/**` and the generated views. Then:

```
lane writes a record  ─▶  commit  ─▶  push to integration  ─▶  every lane sees it
                                          seconds                on next fetch
```

**No QE gate, because there is nothing to gate.** A coordination record is not executable: it cannot fail a test, break a migration or violate an import contract. `make certified ARGS="--next-cycle"` already classifies non-executable change as **not warranting a certification cycle**, so these commits accumulate exactly as documentation does today.

> **The failure this fixes is the one that cost the most this week.** A ruling made on Monday reached `integration` on Wednesday, and Lane A idled in between. **Under this model a ruling is a two-line edit to `modules.toml` that every lane sees on its next `git fetch`.**

## 5 · Alternatives considered, and why each was rejected

**The product owner asked to discuss the approach, so the rejected ones are shown with their reasons rather than omitted.**

| | Approach | Verdict |
|---|---|---|
| **A** | **A shared filesystem directory** — `/home/ganesh/Projects/.signora-coordination/`, outside every clone. **All six lanes are on one machine**, so it is genuinely instant: no fetch, no push, no ref | ⚠️ **Runner-up, and rejected on auditability.** **No history** — *"who changed this assignment, and when?"* is precisely the question C-213 needed answered, and a bare directory cannot answer it. **No backup. Invisible to a fresh clone.** And it puts the repository's most contested truth **outside the repository**, which §2 forbids in spirit. **Available if the product owner values speed over the audit trail — the design below works unchanged on top of it** |
| **B** | **A dedicated `coordination` orphan branch**, never merged into `integration` | ❌ **Rejected on complexity.** It buys separation the repository **already has** — the claim exception — and charges a second ref, a worktree per lane and a sync step for it. *"Every recommendation should aim to remove complexity rather than introduce it"* |
| **C** | **GitHub Issues, Linear, Jira** | ❌ **Refused by §20c-2.** GitHub is version control, remote backup and future collaboration — **not the system of record.** And a cold session with a clone could no longer read the repository's own state, which is the property every governance document here depends on |
| **D** | **A database — SQLite, or a table in Postgres** | ❌ **Principle 6** (no second datastore), and unreadable from a clone |
| **E** | **Keep the markdown; add a staleness linter** | ❌ **The weaker standard.** It makes C-213 *detectable*. §20e has already ruled, for identifier allocation, that **unrepresentable beats detectable** — and a linter is one more thing that must be run, by somebody, before it helps |

## 6 · Migration — four steps, each independently valuable

| | Step | Value standing alone | Size |
|---|---|---|---|
| **1** | **`modules.toml` alone**, and render the module-assignment table into `ACTIVE_ASSIGNMENTS.md` | **This alone closes the C-213 class.** One file, one generator, one table | **Very small** |
| **2** | **`lanes/<lane>.toml`** — the board rows | **Closes the rebase-conflict class.** `ACTIVE_ASSIGNMENTS.md` becomes generated | Small |
| **3** | **`bugs/` and `items/`** | Retires the 4 735-line and 3 212-line files as *hand-maintained* documents. **Their history is preserved; they become rendered indexes** | Medium |
| **4** | **`tasks/`** — state only. **Order stays the product owner's** | The status columns stop being copied between two files | Small |

> **Step 1 is the whole design decision, and it is roughly an afternoon.** If the generated table disagrees with the hand-written one even once, the model is wrong and it costs one file to abandon. **This is the same staged shape [427](427-impact-based-validation.md) uses, for the same reason: earn the rest with evidence.**

**Reuse is high, and nothing new is built:** `infra/registers.py` is already *"reading the registers, in one place"* and becomes the renderer's parser · `infra/implementation-status.py` already establishes the **generated-file banner and `--check` mode** · `infra/state-check.py` already compares documents against the repository and gains one rule: **a generated view that differs from a fresh render is a finding.**

## 7 · Risks, honestly

| | Risk | Mitigation |
|---|---|---|
| **1** | ⚠️ **A hand edit to a generated file is silently lost** | **The banner `implementation-status.py` already uses**, plus `state-check.py --check` failing when a view differs from a fresh render. **Both patterns exist and are proven** |
| **2** | **Two representations exist during migration** — a half-migrated register is exactly the drift this document is about | **Each step converts a file completely or not at all**, and the generated view replaces the hand-written one in the same commit. **No file is ever half-structured** |
| **3** | **Ungated pushes to `integration` become a channel for smuggling change** | **`--audit-claims` is the guard and it already refuses this** — a commit calling itself coordination while touching `backend/` is rejected by **path, never by commit message** |
| **4** | **TOML is one more thing to learn** | It is five typed fields per record. **The alternative being replaced is a 4 735-line markdown file with an implicit schema that only `registers.py` knows** |
| **5** | **Governance churn.** §20e says *"do not redesign a stable process without evidence"* | **The evidence is the trigger.** Two of §20e's four stated conditions are met: *a real defect exposed a weakness* (C-213 cost two days) and *multiple lanes hit the same friction* (Lane A idled; Lane C conflicted twice) |

## 8 · What this does not change

**Stated explicitly, because a coordination change is exactly the shape that quietly reassigns things (§2).**

**No module changes owner because of this document.** **No lifecycle stage moves.** **QE keeps every gate.** **The Task Claim Protocol is unchanged in all ten steps** — only the file a claim writes to. **The Change Budget, the identifier blocks, the five decision states and Repository Closeout are untouched.** **Priority remains the product owner's, and `BACKLOG.md` remains hand-written.**

## 9 · Recommendation

| | |
|---|---|
| **The diagnosis** | ✅ **Three observed failures, one storage cause.** Measured, not inferred |
| **The model** | ✅ **Adopt.** One record one file · no stored assignee · direct-push coordination |
| **Step 1** | ✅ **Do it first and alone.** `modules.toml` plus a rendered table **closes the C-213 class for an afternoon's work** |
| **Steps 2–4** | ⏸️ **Gated on step 1 holding**, not on a date |
| **Approach A** *(shared directory)* | ⏸️ **Available on request.** Faster; **no audit trail.** The record design is identical either way |

> **The honest summary: the protocol was never the problem.** Every lane followed §20e correctly and the repository still lost two days, because **a fact was written down twice and only one copy was maintained.** The fix is not more process — **it is one fewer copy.**

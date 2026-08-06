# Bug register

> **The single register.** Not a file per bug, not scattered TODOs. **Any lane opens a row; QE reconciles the register at every promotion** (`CLAUDE.md` §20e). A lane edits only the `Status` of a bug it has fixed.
>
> **Why this file exists.** Open defects had no home. They were split between `39-product-review-findings.md` (a *dated record of reviews*, append-only, and not a feature lane's to edit) and `PROJECT_STATUS.md`'s known-limitations table. Neither can carry a row whose status changes, and a review finding is not the same thing as a defect with an owner and a fix. This file replaces that responsibility rather than adding one.

## Identifier blocks — per lane, from 2026-08-02

**Product owner's direction.** New rows use the opening lane's allocated block, so two lanes can no longer allocate the same number and QE no longer renumbers at merge (which is what [B-017](#b-017--a-lanes-merged-slice-disappeared-from-integration-and-the-backlog-reoffers-it)'s neighbourhood cost once already).

| Lane | Bugs | Coordination | Tasks |
|---|---|---|---|
| **Lane B** | `B-3xx` | `C-3xx` | `TASK-3xx` |

**Only Lane B's block has been stated to Lane B.** The blocks for Lane A, QE and the unclaimed lanes are the product owner's to allocate, and **this table is deliberately incomplete rather than guessed** — a lane inventing another lane's range is exactly the collision the scheme removes. Rows numbered below 100 predate the scheme and keep their identifiers permanently; an id is never renumbered.


## How it works

**Any lane opens. The module's current assignee fixes. QE verifies and closes** — never the lane that fixed it.

**A defect belongs to a module, not to a lane.** The module is permanent; the lane assigned to it rotates (`CLAUDE.md` §20e). A row therefore names **the module**, and whoever is currently assigned it resolves the defect. A row whose module has no current assignee waits for one — which is not the same as being unowned.

**Reporting is every lane's duty, not only QE's.** Finding a defect outside your assignment is not permission to fix it — it is an obligation to record it, with every field below filled, before carrying on inside your Change Budget. **Only QE sets `VERIFIED`.**

> **No defect disappears because the lane that found it could not fix it.** That is the single failure this register exists to prevent, and it is the one a busy lane commits by accident — in a comment, in a commit message, in an intention to come back.

**Before starting any slice, a lane reads every `OPEN` and `FIXING` row** (`CLAUDE.md` §20e, *Startup*). Rows against the module it is assigned are fixed first, or deferred **with the reason stated in the commit message**. Silence reads as *nobody looked*.

> **Finding a bug never grants implementation ownership.** *Discovery* decides who reports it; **the affected module decides who fixes it.** They are rarely the same lane, and that is the point. Ownership moves only by explicit reassignment, never by having noticed.

**A defect is not a dependency.** If your work is blocked because another module has not yet built or agreed something, that is a coordination item — [`LANE_COORDINATION.md`](LANE_COORDINATION.md) — not a bug. A bug is something that behaves wrongly today.

### Defects in code that belongs to no module

`signora_platform/**` (frozen, §20a), `apps/` (the composition root) and the frontend foundation (§20c) are not modules, so no assignment reaches them. **QE cannot fix them either — it changes no production code.**

Such a row names the code, records **Current assignee: none — not assignable**, and **waits for the product owner**. It is never quietly adopted by whoever is nearest.

**This gap appeared on 2026-08-01** when the Integrator role was absorbed into QE. [B-007](#b-007--the-migration-runner-locks-one-database-and-migrates-another) is its first instance, and [C-010](LANE_COORDINATION.md) is the item that will resolve it — deciding how unassignable code gets assigned is an architectural decision, not a lane's to make.

**`integration` never fast-forwards to `main` with an open 🔴.** That is the one blocking rule; 🟠 and below are the product owner's call.

| Severity | Meaning |
|---|---|
| 🔴 | Blocks a milestone |
| 🟠 | Wrong behaviour a customer would hit |
| 🟡 | Wrong but survivable |
| 🟢 | Cosmetic |

| Status | Meaning |
|---|---|
| `OPEN` | Reproduced, not started |
| `FIXING` | The current assignee is on it |
| `FIXED` | Lane says done, with a regression test |
| `VERIFIED` | QE reproduced the fix. **Only QE sets this** |
| `WONTFIX` | Deliberate, with the reason stated |

**Where the regression test goes:** the affected module's suite, written by the lane that fixes it — never this file. The rule requiring one is `CLAUDE.md` §11.

**Bug ids are `B-nnn`, allocated sequentially and never reused.** A finding from a product review keeps its `R-` id there and gets a `B-` row here only if it is a defect rather than an improvement.


## How the registers were reconciled, 2026-08-02

**Two lanes allocated `B-003`…`B-006` independently while the repository ran on two baselines.** The rows promoted to `main` keep their numbers; **QE renumbered the later set**, which is this file's stated rule for an id collision.

| Was, on `lane-qe` | Is now | Why |
|---|---|---|
| `B-001` · `B-002` | — | The same two defects as the promoted rows. The duplicates were dropped, not renumbered |
| `B-003` the migration runner | **[B-007](#b-007--the-migration-runner-locks-one-database-and-migrates-another)** | Renumbered. It is the **code** half of promoted [B-003](#b-003--a-lane-following-runningmd-exactly-cannot-run-its-own-suites), which is the documentation half |
| `B-004` the truncation claim | **[B-008](#b-008--the-suite-says-it-truncates-every-table-and-truncates-five)** | Renumbered |
| `B-005` the documented API command | **[B-009](#b-009--the-documented-command-for-starting-the-api-cannot-start-the-api)** | Renumbered |
| `B-006` orphaned narrations | **[B-010](#b-010--re-seeding-the-playground-orphans-every-narration-silently)** | Renumbered |
| `B-007` `make` absent | **[B-011](#b-011--make-is-not-installed-on-this-workstation--not-a-repository-defect)** | Renumbered, and resolved on the workstation |

**No row was lost and none was silently merged.** An id, once promoted, is never reused for a different defect.

---

## Open

### B-207 · An expired score renders as *no score* — **withdrawn, and the mistake is the interesting part**

| | |
|---|---|
| **Module** | **Product Surface** — the attention list. `frontend/components/intelligence/attention.tsx` |
| **Current assignee** | **Lane A** — Product Surface is its in [`modules.toml`](coordination/modules.toml), and this lane wrote the component |
| **Severity** | 🟠 · **Wrong behaviour a customer would hit**, on the first screen they see, about the number the screen is sorted by |
| **Status** | ⛔ **`CLOSED` — withdrawn by the lane that raised it**, 2026-08-06, within the hour, on checking the composed row rather than the component. **The id is retired and never reused.** **There is no defect: the surface already says *Evidence expired*** — see the correction below |
| **Found** | 2026-08-06, `bcea8ba` |

**Steps to reproduce.** Open the homepage with an account whose buying score has expired — `score: null` on `AccountAttentionResponse`.

**Expected.** *"We scored this, and the evidence behind it is no longer current."*

**Actual.** An em dash, labelled **`"No current score"`**.

```tsx
export function AttentionScore({ score }: { score: number | null }) {
  if (score === null) {
    return <span aria-label="No current score">—</span>;
  }
```

### The API says what null means, and it does not mean absent

**`opportunity_engine/interface/schemas.py`, in the published OpenAPI description a consumer reads:**

> ***"Commercial attention, 0–100… Null when the evidence behind it has expired — the opportunity is still open and the number that justified it is no longer current."***

**So `null` carries a specific, actionable fact and the surface renders it as an absence.** A seller reading `—` concludes *Signora has nothing on this account*; the truth is *Signora had something and it went stale*, on an opportunity that **is still open**. **Those demand opposite actions** — the first is a reason to ignore the row, the second is a reason to distrust the ranking it is sitting in.

### It is [P-A](DOMAIN_DISCOVERY_REGISTER.md), and the repository already knows the pattern

**[C-226](LANE_COORDINATION.md) is this exact class** — *a failed read rendering as an empty account* — and this lane fixed three sections of it in [TASK-417](BACKLOG.md). **The account brief already does it correctly**: a 404 from the score read renders *"Nothing has scored this account yet"* and any other error renders *"Could not load this account"*, because **never scored** and **could not find out** are different sentences.

> **The list never got the third one.** The brief distinguishes *never* from *failed*; **nothing anywhere distinguishes *expired*** — and expired is the only one of the three that the attention list can actually be showing, because a row is there precisely because an opportunity is open.

### Why it survived review

**The component is right about everything else and says so at length** — why the score is typographic rather than a gauge, why it is subordinate to the account name. ⚡ **`aria-label="No current score"` is even *literally* true**: there is no current score. **It is the inference a reader draws that is wrong**, which is why no test caught it and why reading the component does not reveal it. **The defect is only visible against the API contract**, and [453](architecture/453-opportunity-intelligence-traceability-audit.md) is what put the two side by side.

⛔ ### Withdrawn — 2026-08-06, by Lane A, an hour after filing

**Everything above reads `AttentionScore` on its own. The row that composes it already says the thing.**

```tsx
// app/(app)/page.tsx — the status lane, immediately before the score column
<ContestedMark contested={account.contested} />
<EvidenceHealth evidence={account.evidence} />   // ← "Evidence expired"
...
<AttentionScore score={account.score} />          // ← "—"
```

**And the two cannot disagree**, which is the fact that settles it:

```python
# opportunity_engine/application/queries.py
def evidence_state(opportunity, score, moment) -> EvidenceState:
    if score is None or not score.is_valid_at(moment):
        return EvidenceState.STALE
```

> ## **`score is None` implies `stale`, by construction. Every row with an em dash carries the *Evidence expired* badge, one element to its left.**

**So the surface is correct and is arguably better than what this row proposed.** The badge states *why there is no number*; the em dash states *that there is no number*. **Two facts, each where it belongs** — and putting the word *expired* into the score column would have said one of them twice, in the column the page is scanned down.

### What this lane got wrong, recorded rather than quietly deleted

**The filing judged an element in isolation and drew a conclusion the composition does not support.** ⚡ **That is the same error this lane had criticised [447](architecture/447-signal-center-traceability-audit.md) for one poll earlier** — counting a thing as present without checking the context it lives in — **committed while writing up [C-228](LANE_COORDINATION.md), which is the item making that criticism.**

**The `aria-label` observation was the tell and was misread.** *"No current score"* is literally true, and this row treated its literal truth as evidence that a reader would infer something false. **The reader is not reading the label alone either.**

⚠️ **What survives, and it is small.** **`AttentionScore` is also called by `NeedsIdentity`**, where no `EvidenceHealth` badge sits beside it — so a company nobody can name shows an em dash with nothing explaining it. **That is not this row's claim** (it asserted a defect on the attention list, where the badge exists) and it is not a defect either: an account with no identity has no evidence health to state. **Recorded so the next reader does not re-derive it.**

**[TASK-441](BACKLOG.md)'s rule is unaffected and still binds** — *"an expired score must render as expired, never as absent and never as current."* **The lesson for that screen is now concrete rather than theoretical: the badge is where expiry is said, and the new screen must carry it rather than inventing a second way to say the same thing.**

### B-402 · `ENGINEERING_LAWS.md` is classified `platform`, so editing it demands a DR run

| | |
|---|---|
| **Module** | `infra/certification-guard.py` — `CLOSEOUT_PATHS` |
| **Current assignee** | ⚠️ **QE.** **`certification-guard.py` is named in `CLAUDE.md` §20e as QE's**, and this constant decides **what may promote as a Closeout** — so changing it changes what a gate *means*. ⛔ **Lane C found it while building on the classifier and may not repair it** |
| **Severity** | 🟡 — **nothing is wrong today; the plan is too wide rather than too narrow**, which is the safe direction. **It becomes 🟠 the moment a lane distrusts the plan and starts ignoring it** |
| **Status** | **`OPEN`** — reported with evidence, **not fixed: it is a gate's meaning** |
| **Found** | 2026-08-06 by Lane C, **testing the [D-115](DECISION_REGISTER.md) validation planner against a real diff** rather than by reading the constant |

**Steps to reproduce.**

```bash
python3 infra/certification-guard.py --plan origin/main..HEAD
→   Impacts
      documentation  CLAUDE.md, PROJECT_STATUS.md (+11)
      platform       ENGINEERING_LAWS.md, docs/coordination/queues/lane-a.toml (+5)
    Gates (16)  … dr, migration-reversibility, prompt-evaluation …
```

**Expected.** **Two governance markdown files at the repository root classify alike.**
**Actual.** **`CLAUDE.md` is `documentation` and `ENGINEERING_LAWS.md` is `platform`** — so **a governance edit demands `dr`, `migration-reversibility` and `prompt-evaluation`.**

### The cause is one missing entry, and the comment above it predicted this class

```python
CLOSEOUT_PATHS = ("certification/", "docs/", "PROJECT_STATUS.md", "README.md", "CLAUDE.md")
```

⚡ **`ENGINEERING_LAWS.md` is not in it, and it is the Repository Engineering Standard** — `CLAUDE.md` §19 and §20e both delegate to it. **It sits at the root beside `CLAUDE.md` and `README.md`, and only it is missing.**

⚠️ **The classifier's own comment records the identical defect being fixed once already**: *"The first real run of this analysis classified `CLAUDE.md` as `platform` — it is not under `docs/`… Two classifiers in one file, disagreeing on their first disagreement."* **The fix shared the rule; it did not complete the list.**

### Why the direction matters more than the instance

✅ **The plan is too *wide*, which is the correct failure.** [D-114](DECISION_REGISTER.md)'s rule — *unknown widens, never narrows* — worked exactly as designed and this defect is what it looks like when it fires.

⚠️ **But a plan that demands a disaster-recovery run to edit a markdown file is one lanes will learn to ignore**, and an ignored plan is worse than no plan. **That is the cost, and it is why this is filed rather than tolerated.**

### The fix, for QE

**Add `ENGINEERING_LAWS.md` to `CLOSEOUT_PATHS`.** ⚠️ **And check the rest of the root** — `IMPLEMENTATION_ROADMAP.md`, `PRODUCT_DIFFERENTIATORS.md` and any other root governance file have the same shape. ⛔ **Lane C did not enumerate them, because proposing the full list would be proposing the fix.**

**Regression guard.** ✅ **Available and cheap**: assert every tracked root-level `.md` classifies as `documentation`. **A new governance file added at the root then fails visibly rather than silently demanding a DR run.**

### B-328 · `state-check.py` reports 54 `READY` tasks when there are two, because it counts headings

| | |
|---|---|
| **Module** | `infra/state-check.py` — the backlog summary line, check 5c |
| **Current assignee** | **Lane C** — `infra/` is Platform Foundation ([D-022](DECISION_REGISTER.md)), and [B-125](#b-125--the-new-document-location-check-silently-no-ops-on-a-clone-without-originintegration) is already assigned there for this same file |
| **Severity** | 🟠 · **Reassuring rather than merely wrong.** *"54 READY"* reads as a healthy queue on a day when two rows are `READY` and both are blocked |
| **Status** | ✅ **`FIXED` — Lane C, 2026-08-06.** **QE verifies; the lane that fixed it does not close it.** ⚡ **Fixed independently and hours apart** — this office found the same defect while writing [D-099](DECISION_REGISTER.md)'s queue work and corrected it in the same commit, and Lane B's `B-328` commit dropped as a duplicate on rebase. **Both diagnoses were right and the second cost one rebase to discover** — recorded as [C-103](LANE_COORDINATION.md)'s second instance. **The line now reads `Backlog: 61 task(s), 9 startable (…)`, and it lists the ids** |
| **Found** | 2026-08-06 by Lane B, checking its own reporting against the gate after [C-333](LANE_COORDINATION.md) added seven queue validations |

### B-401 · `04-modules.md` disagrees with `backend/modules/` in four places

| | |
|---|---|
| **Module** | Repository architecture — [`docs/architecture/04-modules.md`](architecture/04-modules.md), the ratified module reference |
| **Current assignee** | ⚠️ **Product owner** — `docs/architecture/01`–`21` is 🔴 (Change Budget). **Lane C reports; it may not repair** |
| **Severity** | 🟠 — **wrong information a lane would act on.** It has already produced one wrong statement in a ratified ADR |
| **Status** | **`OPEN`** — reported with evidence, **not fixed: 🔴 and not this office's** |
| **Found** | 2026-08-06 by Lane C, auditing the Notification Center ([468 §1](architecture/468-notification-center-traceability-audit.md)) — **while checking another document's stated blocker rather than by inspecting this one** |

**Steps to reproduce.**

```bash
python3 infra/state-check.py | grep 'Backlog:'
→ ok   Backlog: 69 task(s), 54 READY, no task claimed twice.

grep -oE '^\| \*\*Status\*\* \| [^|]{0,40}' docs/BACKLOG.md \
  | sed 's/| \*\*Status\*\* | //; s/[*`]//g' | awk '{print $1, $2}' | sort | uniq -c | sort -rn
→ 20 IN VALIDATION · 16 SEQUENCED · 4 DONE · 3 PROMOTED · 3 IN PROGRESS
   2 ✅ READY · 2 ⏸️ BLOCKED · 1 RATIFIED · 1 DISPOSED · 1 DISPOSED · 1 WAITING
```

**Expected.** The count of rows whose status is `READY`.
**Actual.** **54 — the number of `### TASK-nnn` headings**, which is neither the `READY` count (2) nor the task count (69, which the same line reports separately and correctly).

### The line

```python
ready = len(re.findall(r"^### TASK-\d+", backlog, re.M))
notes.append(f"Backlog: {len(known)} task(s), {ready} READY, no task claimed twice.")
```

**It never reads a status.** `_STARTABLE = {"READY", "CHANGES REQUESTED"}` exists twenty lines above and is not consulted here.

### Why 🟠 rather than cosmetic

**This is the only number in the gate's output that answers *"how much claimable work exists?"***, and it is the number a session would quote. **It is wrong in the reassuring direction**, which is [§2](../CLAUDE.md)'s class exactly: a repository asserting something untrue is worse than one that says nothing, *because it is trusted*.

⚠️ **And [C-333](LANE_COORDINATION.md) has just made queue health a validated concern.** One of its seven checks is *"`READY` rows in no queue"* — **which cannot be doing what it claims if `READY` is being read this way anywhere else in the file.** Worth checking whether the two share a helper; **this row does not assume they do.**

### What it cost, and it is not hypothetical

**This lane matched the same status the wrong way and reported *"zero `READY` rows"* across four polls.** The right answer is **two — [TASK-201](BACKLOG.md) and [TASK-202](BACKLOG.md), both externally blocked** — so every conclusion drawn from it survived, and the phrasing did not. **The emoji prefix is what both readers missed**: the rows are `✅ READY`, not `` `READY` ``.

> **Two independent readers got the same field wrong on the same day, in opposite directions.** That is the argument for the status being **parsed once, in one place**, rather than pattern-matched wherever it is needed.

grep -oE "^### [A-Z].*" docs/architecture/04-modules.md   # Module Reference entries
ls -d backend/modules/*/                                   # what exists
```

**Expected.** The ratified module reference names the modules the repository has.
**Actual.** **Sixteen entries and sixteen directories, and they are not the same sixteen.**

| Direction | Modules | Consequence |
|---|---|---|
| ⚠️ **In code, absent from the document** | **`sales_engagement`** — **zero mentions; no heading, no Module Reference entry** · **`integrations`** — mentioned three times, **no Module Reference entry** | **Two shipped bounded contexts the architecture does not define.** A lane resolving module ownership against `04-modules.md` (§1, *"resolving that ambiguity against `04-modules.md` is the first step of the task"*) finds nothing |
| ⚠️ **In the document, absent from code** | **Recommendation Engine** · **Revenue Intelligence Platform** | **Correct and deferred** — but indistinguishable, in that document, from the two that shipped |

### It has already cost something, which is why it is a row rather than a note

**[ADR-0040](architecture/adr/0040-notifications.md)'s status block states its ratification blocker as *"a fifteenth entry in `04-modules.md`"*.** ⚡ **It would be the seventeenth.** **The ADR is not careless — that count was defensible on 2026-08-02** — **but a ratification gate stated against a stale count is a gate nobody can check.**

### The fix, and it is not four edits

**Decide what `04-modules.md` is.** If it describes **what exists**, `sales_engagement` and `integrations` need entries and the two unbuilt modules need marking as planned. If it describes **the intended architecture**, then two modules shipped without one and that is the finding instead. ⛔ **Lane C will not choose** — `CLAUDE.md` §2: *a governance edit that changes what somebody does tomorrow needed a decision yesterday.*

### Regression guard

⚡ **Available and cheap, unlike [B-327](#b-327--three-documents-say-the-executive-dashboards-icp-section-is-buildable-and-a-coordination-item-on-integration-says-it-is-not)'s.** **This one *is* mechanically checkable** — a directory listing against a document's headings, which is exactly what `state-check` already does for architecture-document numbering. **Proposed, not built**: it belongs with whoever rules on the paragraph above, because the check's correct assertion depends on which of the two answers is chosen.

### B-327 · Three documents say the Executive Dashboard's ICP section is buildable, and a coordination item on `integration` says it is not

| | |
|---|---|
| **Module** | Repository records — [`BACKLOG.md`](BACKLOG.md)'s TASK-438 row · [444](architecture/444-executive-dashboard-domain-assessment.md) · [448](architecture/448-icp-builder-traceability-audit.md) · [`DOMAIN_DISCOVERY_REGISTER.md`](DOMAIN_DISCOVERY_REGISTER.md) |
| **Current assignee** | **Lane C** — all four are its documents, and the registers are its to reconcile |
| **Severity** | 🟠 · **Wrong information a lane would act on.** It already produced a `READY` row with an unbuildable section |
| **Status** | ✅ **`FIXED` — 2026-08-06, all seven documents.** **QE verifies; the lane that fixed it does not close it** |
| **Found** | 2026-08-05 by Lane B, claiming [TASK-438](BACKLOG.md) and reading its acceptance before writing |
| **Commit found** | `f14db51e` — and [C-332](LANE_COORDINATION.md) landed at `714f4663`, **one commit earlier** |

**Steps to reproduce.**

```bash
git log --oneline --reverse 714f4663..f14db51e
→ 714f4663 C-332 — the predicate is on main and nothing can call it
  ...
  f14db51e 448 — ICP Builder, and the screen the product owner named split R-01 in two

grep -c "C-332" docs/architecture/448-icp-builder-traceability-audit.md
→ 0
```

**Expected.** A document merged after C-332 either reflects it or says why not.
**Actual.** Four records assert the opposite of it, and none mentions it.

### The four claims, and what each would cause

| Where | What it says | What it causes |
|---|---|---|
| **[TASK-438](BACKLOG.md)**, *"The fifth, newly unblocked"* | *"**ICP coverage** — ⚡ TASK-434 is `PROMOTED`, so *in-ICP versus outside* is **a call to a published predicate***" | **The most expensive one.** A `READY` row telling the claiming lane that a section needs nothing |
| **[444 §108](architecture/444-executive-dashboard-domain-assessment.md)** | TASK-438 is *"**the five sections that need nothing** — conversion, ageing, movement, roll-up by owner, ICP coverage… **it needs no answer from anybody**"* | The row above derives from this |
| **[448 §7](architecture/448-icp-builder-traceability-audit.md)** | **R-00 matching — ✅ *"Shipped. Validated by the screen that needed it most"*** | Tells the cross-screen view a capability is available |
| **[`DOMAIN_DISCOVERY_REGISTER.md`](DOMAIN_DISCOVERY_REGISTER.md)** row 8 · row 14 | *"⚡ R-00 shipped and validated here"* · Executive Dashboard *"**in-ICP cohort ✅**"* | **Sixteen consumers read R-00 to decide whether they are blocked** |

### Why the claim does not survive checking

**What shipped at [TASK-434](BACKLOG.md) is a predicate.** `evaluate(icp, observed)` is correct, promoted, and takes an `ObservedAttributes`.

> **Nothing in `backend/modules/` constructs one**, and the only module that could — `knowledge_graph`, which alone holds the `entity_id → SubjectRef` binding `ClaimReader` needs — is **forbidden to `opportunity_engine` in full.** [05](architecture/05-module-dependencies.md) gives that module one upstream edge and it is the Buying Score Engine.

**"Shipped" is true of the predicate and false of the capability**, and the register does not distinguish them — which is the whole defect. **A predicate nothing can call is a foundation, not a capability**, and [443 §2](architecture/443-account-matching-capability.md) already said so by decomposing matching into four milestones: **M2 shipped, M4 is TASK-406, and the step that turns claims into the values M2 compares is in neither.**

### It is not hypothetical — it has already cost something

**Lane B claimed TASK-438 on the strength of that row**, discovered the fifth section on the reuse audit, and **delivered four sections rather than five**. That is the cheap outcome. **The expensive one was available**: a lane that trusted *"a call to a published predicate"* would have built the arithmetic and met the missing input at the end.

### The fix, and it was one line of judgement rather than seven edits

**Decide what R-00 means, then say it once.** *"Shipped"* is defensible for M2 and misleading for the capability — so the register needed the distinction it collapsed. **Every downstream document then derives from it**, which is [§2](../CLAUDE.md)'s rule: truth has exactly one authoritative representation.

> ## **The word adopted, and it is now the register's: *implemented, not usable*.**
>
> **A promoted predicate with no reachable caller is a foundation, not a capability.** **Both halves are true and stating only the first is what cost Lane B a section.**

### ⚡ The fix ran twice, and the second half is a Product Office finding

**Two reconciliations happened on 2026-08-06 and neither knew about the other**, because **they were filed under one id and I did not notice.**

| | Documents | When |
|---|---|---|
| **① [D-094](DECISION_REGISTER.md)'s reconciliation** | **[443](architecture/443-account-matching-capability.md) · [TASK-406](BACKLOG.md)'s row · [Register](DOMAIN_DISCOVERY_REGISTER.md) rows 312/346 · [461](architecture/461-product-led-domain-discovery-review.md)** | 2026-08-06, morning |
| ⚠️ **② The three this row actually named** | **[444](architecture/444-executive-dashboard-domain-assessment.md) §42 and §108 · [448](architecture/448-icp-builder-traceability-audit.md) §129 and §143 · [Register](DOMAIN_DISCOVERY_REGISTER.md) rows 8, 14, 69 and the coverage matrix** | **2026-08-06, on [D-099](DECISION_REGISTER.md) — after the row already read `FIXED`** |

> ⛔ **So this row read `FIXED` for part of a day while three of the documents it names still said the section was buildable.** **The duplicate id is what concealed it**: two rows under `B-327` meant the fix row and the report row were never read together, and each looked complete on its own.
>
> ⚡ **`state-check` caught the duplicate id and could not have caught the partial fix** — it compares identifiers, not claims. **The instrument found the *cause* and a human had to find the *consequence*, which is the honest division and worth recording rather than smoothing over.**

### Regression guard

⛔ **None, and deliberately.** **A document agreeing with a *capability's reachability* is not mechanically checkable** — `state-check` can compare a document to a commit, not a claim to a codebase. **Saying so beats a check that would pretend to cover it.**

✅ **What *is* now guarded is the thing that hid it.** The duplicate-identifier check already existed and worked; **what was missing was reading its output before declaring the fix complete.** **[D-099](DECISION_REGISTER.md) makes `state-check` a precondition of closing any Product Office row, not a report written after one.**

### B-325 · B-118's fix allocates Lane B its own database, and the document that tells a lane how to run still names the shared one

| | |
|---|---|
| **Module** | Development environment — [`docs/RUNNING.md`](RUNNING.md), the *Running a lane* invocation |
| **Current assignee** | **QE** — `RUNNING.md` is QE's in the shared-files table (`CLAUDE.md` §20e). **The `infra/` half is already built and correct; nothing is asked of Lane C** |
| **Severity** | 🟠 — **it makes measurement untrustworthy**, which is [B-118](#b-118--lanes-share-one-postgresql-so-two-suites-running-at-once-fabricate-each-others-failures)'s own severity and for B-118's own reason |
| **Status** | **`OPEN`** — reported with evidence; **not fixed, because `RUNNING.md` is not this lane's to edit** |
| **Found** | 2026-08-05 by **Lane B**, when B-118 reproduced against it **after B-118 was marked `FIXED`** |

**Steps to reproduce.** Follow [`RUNNING.md` § Running a lane](RUNNING.md#running-a-lane) exactly, as a lane is required to, and run the suite while another lane runs theirs.

**Expected.** Isolation. B-118 is `FIXED`: *"create separate environment for each lane so that nothing could be shared."*

**Actual.** Contention, exactly as B-118 describes — two failures in modules the run never touched, both passing on an isolated re-run of the same commit.

### The fix is built and the instructions do not reach it

**`infra/` is correct.** `docker-compose.yml` reads `${SIGNORA_POSTGRES_PORT:-5432}` and `${COMPOSE_PROJECT_NAME:-signora-v2}`, and `environments.py` allocates a port per lane:

```
lane-a | postgres 5732
lane-b | postgres 5832
demo   | postgres 6232
```

**`RUNNING.md` still tells Lane B to use 5432**, in the block a lane copies verbatim:

```
export SIGNORA_TEST_APP_DATABASE_URL=postgresql+asyncpg://…@localhost:5432/signora_lane_b
export SIGNORA_TEST_ADMIN_DATABASE_URL=postgresql+asyncpg://…@localhost:5432/signora_lane_b
export SIGNORA_DATABASE_URL=postgresql+asyncpg://…@localhost:5432/signora_lane_b
```

**And 5832 is not listening** — only 5432 is. So the separate stack exists in the model and has never been started by the lane it was allocated to, because nothing told that lane to start it.

> **This is the class `CLAUDE.md` §2 names: the repository telling a lane something that is no longer true.** A defect marked `FIXED` whose fix nobody can reach is worse than one still marked open — **every lane reads the register, believes the row, and keeps reproducing the defect while believing it cannot.** It is also why this row exists rather than a re-opening of B-118: **B-118's fix is real and correct**, and re-opening it would misattribute a documentation gap to the engineering that closed it.

### What Lane B is doing meanwhile

**Not editing `RUNNING.md`** — it is QE's, and a lane rewriting another's file is how two records start disagreeing. **Not inventing its own ports either** ([`RUNNING.md`](RUNNING.md#running-a-lane) is authoritative on allocation and `environments.py` already holds the answer).

**Publishing no number measured during contention**, which is B-118's own rule, and re-running in isolation to tell a real failure from a fabricated one.

### ⚠️ Measured 2026-08-05 — it is wider than this row says, and the evidence is deterministic

**This row blamed `RUNNING.md`. The `Makefile` target has the same defect, and that is the half a lane cannot read its way past.**

| | |
|---|---|
| **`make test`** | `cd backend && … uv run pytest --cov` — **passes no database URL at all**, so `tests/conftest.py` falls back to its literal default: `…@localhost:5432/signora`, the historical shared stack |
| **`make demo-prepare`** | `SIGNORA_DATABASE_URL=$(OWNER_DATABASE_URL)`, where `OWNER_DATABASE_URL` derives its port from `infra/environments.py --exports` — **correctly lane-aware** |

**Two targets in one file, one resolving the lane's allocation and one ignoring it.** So a lane that reads `infra/`, trusts the allocation and runs the documented gate **still lands on 5432** — the instructions are not the only thing pointing at the shared database.

**What it produced here, and it is not contention:** **62 failures, deterministic, `relation "signal_resolution" does not exist"`** — the shared database sits at migration `0038` while `integration` is at `0039`. **That reads exactly like a broken tree** and is a stale schema on a database this lane was never allocated.

**Confirmed by fixing only the environment:** the lane's own stack brought up at **5832**, migrated to head, suite re-run with the three `SIGNORA_TEST_*` URLs pointed at it — **3624 passed, 1 skipped, coverage 95.37%.** **Nothing in the tree changed between the two runs.**

**Still not fixed by this lane.** `RUNNING.md` is QE's and the `Makefile` is Platform Foundation's ([D-022](DECISION_REGISTER.md)) — **but the gate half is QE's under §20e's own test**: this changes whether a gate *runs* against the right database, not what it *means*.

### B-326 · A git conflict marker is committed inside the defect register

| | |
|---|---|
| **Module** | Repository records — `docs/BUGS.md` |
| **Current assignee** | **QE** — register reconciliation is theirs (`CLAUDE.md` §20e), and this file has no module owner |
| **Severity** | 🟡 — nothing behaves wrongly; **the repository's own account of itself contains a fragment of a merge that never finished** |
| **Status** | **`OPEN`** — reported, **not fixed.** One line, one obvious resolution, and still another lane's file |
| **Found** | 2026-08-05 by Lane B, grepping its own working copy for markers after a run of hand-resolved rebases |

**Steps to reproduce.**

```bash
git show origin/integration:docs/BUGS.md | grep -n '^>>>>>>>'
```

**Expected.** Nothing.

**Actual.**

```
1238:>>>>>>> 603a077 (ADR-0040 proposed — Notifications answers a different question from Attention)
```

**A closing marker with no opening one**, so the conflict was resolved by hand and one line was missed. It renders as literal text in the middle of the register.

### Why it is worth a row rather than a quiet deletion

**§2: the repository itself should always tell the truth.** A defect register is the document a lane reads to learn what is broken, and **a fragment of an unfinished merge sitting inside it is the register failing at its own job** — mildly, but in the one file whose credibility is the point.

**Not fixed here for the reason this lane has now applied four times**: finding a defect outside your assignment is an obligation to report it, never permission to fix it. `BUGS.md` has no module owner and QE reconciles it at merge, so the deletion is theirs. **It is one line and it is obvious — which is exactly when the rule is easiest to break.**

### B-324 · TASK-415 made the mock the local default, and evaluation resolves through the same registry

| | |
|---|---|
| **Module** | `ai_platform` — `evaluation/release.py`, `evaluation/__main__.py` |
| **Current assignee** | **Lane B** — the module's current assignee, **and the lane that caused it** |
| **Severity** | 🟠 — **it makes a measurement untrustworthy**, and the untrustworthy result is one that *passes* |
| **Status** | ✅ **`FIXED` — Lane B, 2026-08-06**, in the shape this row designed. **`AIProviderDescriptor` gains `output_is_evidence`**; the mock declares `False`; **`record()` refuses a report carrying it** — before the manifest is read, so a refusal leaves the file untouched. **Six regression tests**, including one asserting the refusal *names no vendor and no adapter*, which is the constraint that reverted the first attempt. **`Infer.output_is_evidence(model)` is where the capability is read**, because the harness has no registry and giving it one would change a constructor four evaluation entrypoints call — **one of them another module's**. `Infer` already holds the registry and every harness already holds `Infer`, so **all four are protected without any of them changing.** ⚠️ **The field defaults to `True` rather than being required** — the stronger shape would break a descriptor built in `tests/ai_research_engine/`, which is not this lane's to edit. **The default is right for the population**: every real adapter is evidence, and a fake is written by somebody who knows it is one. **`VERIFIED` is QE's.** **Originally: reported with the fix designed and deliberately not shipped.** [TASK-416](BACKLOG.md) records the provider on every evaluation, so a mock-served run is now **visible**; **refusing one needs a change to `AIProviderDescriptor` and is not in this slice** (below) |
| **Found** | 2026-08-05, by this lane, **preparing TASK-416's package** — reading how a provider would be recorded, not by a test failing |

**Steps to reproduce.** On a fresh clone at `32b6467`, with no Ollama and no API key:

```bash
cd backend && uv run python -m modules.ai_platform.evaluation --prompt explanation_narration --record
```

**Expected.** A refusal. Nothing about a scripted response is evidence.

**Actual, before the fix.** The run resolves the **deterministic mock**, measures whatever content the mock was configured to return, and **records it into the manifest as an evaluation.**

### Why it is worse than a wrong number

**`Prompt.released_for` reads that list.** An evaluation in the manifest is what makes a `(model, dataset)` pairing usable, so a scripted response could have **earned a real release** — and a release is what the runtime checks before letting a prompt reach a customer. `CLAUDE.md` §10: *"a quality measurement taken against a fake measures the fake"*, and the mock's grounding and schema failures are a property of its script, not of the prompt.

### What caused it, precisely

**[TASK-415](BACKLOG.md) did**, and this lane wrote it. Before that slice `build_provider_registry` could not produce a mock at all, so the hazard did not exist. Making the mock the local default was correct and approved; **what was missed is that the evaluation entry points resolve through that same registry.**

> **The codebase said it could not happen, in a comment.** `evaluation/__main__.py` read *"Nothing here constructs an adapter, so nothing here can construct a fake."* **True when written, false after TASK-415** — the exact class §2 names: *a comment justifying a guarantee the code no longer makes is a false claim sitting in the codebase.* It was found by reading that comment and checking whether it was still true.

### What TASK-416 does about it, and what it deliberately does not

**Done: the run is visible.** Every evaluation now records which provider served it, so a mock-served measurement is identifiable in the manifest rather than indistinguishable from a real one.

**Not done: it is not yet refused** — and the reason is worth reading, because the obvious fix is wrong.

> **The first attempt was `if report.provider is AIVendor.MOCK` in `record()`, and a Security Invariant refused it within the hour.** `TestTheEvaluationFrameworkNamesNoVendor` states that evaluation code *"may not name a vendor, name a concrete adapter, or reach a vendor's URL"*, and `CLAUDE.md` §10 says the same thing generally: **no `if vendor == …` outside an adapter.** The check was reverted rather than the test weakened (§11).

**The correct shape is a capability, not an identity**, and `domain/provider.py` already prescribes it: *"Capabilities first, identity last. A future vendor integrates by describing what it supports, never by requiring conditional logic elsewhere."* So the refusal reads a flag on `AIProviderDescriptor` — *does this adapter measure a real model?* — which names no vendor and **covers every future stub automatically** rather than the one that exists today.

**That is a second change to a published domain type in one day**, after `AIVendor.MOCK`, and it needs the same review rather than being appended to a slice at the end of a session. **Filed here so it cannot be lost, with the design named so the next lane does not rediscover it.**

⚠️ **Until it lands, the hazard is real on a fresh clone**: `make eval-*` with default settings measures the mock. **The mitigation available today is the visibility this slice added**, plus the manifest's own record — a reader can now tell.

### B-323 · `mypy --strict` fails on `integration`, in the test that proves the skip check can fire

| | |
|---|---|
| **Module** | Repository tooling — `backend/tests/test_repository_impact.py`, the suite covering `infra/certification-guard.py` |
| **Current assignee** | **Lane C** — `infra/`, the `Makefile` and repository process are Platform Foundation ([D-022](DECISION_REGISTER.md)) |
| **Severity** | 🟠 — **Blocking Quality Defect.** No customer behaviour is wrong; **a required gate fails, so no commit can be certified** |
| **Status** | **`FIXED`** at `56b9c53` by the lane whose file it is — three annotations. **`VERIFIED` is QE's.** Reported by Lane B and **deliberately not fixed by it**: not this lane's module, and finding a defect is an obligation to report it rather than permission to fix it (§20e). ✅ **Confirmed green from this lane**: `mypy --strict` clean over 733 files |
| **Found twice within the hour** | **QE opened [B-117](#b-117) certifying; Lane B opened this rebasing.** QE merged the two and kept both rows, deferring to this one on the cause. **Certification of cycle 55 was refused on it**, which is the gate doing precisely what it exists for |
| **Found** | 2026-08-05, by Lane B, rebasing onto `integration` and re-running the gates because the rebase carried executable change |

**Steps to reproduce.** At `bfbeeef`, from `backend/`:

```bash
./.venv/bin/mypy --strict .
```

**Expected.** `Success: no issues found`.

**Actual.**

```
tests/test_repository_impact.py:189: error: Function is missing a type annotation for one or more parameters  [no-untyped-def]
tests/test_repository_impact.py:207: error: Function is missing a type annotation for one or more parameters  [no-untyped-def]
tests/test_repository_impact.py:224: error: Function is missing a type annotation for one or more parameters  [no-untyped-def]
Found 3 errors in 1 file (checked 733 source files)
```

### The mechanism, in one line

**Three test functions take `monkeypatch` with no annotation.** `pyproject.toml` runs `mypy --strict`, which requires every parameter to be annotated; the fixture's type is `pytest.MonkeyPatch`.

### Why it is worth more than three annotations

**The three tests are the ones that make the new skip check trustworthy** — *"a guard that cannot fail is documentation pretending to be code"*, in their own docstrings. **They are correct tests, and they were added in the same commit that fixed the guard's false positives.** Nothing about the check is wrong; the gate simply was not run over them.

> **This is [B-115](#b-115--task-301-fails-mypy---strict-on-a-test-helper-narrower-than-the-type-it-builds)'s class again, and Lane B caused that one.** The lesson recorded there was that `mypy --strict modules signora_platform apps` is not the gate — **the gate is `mypy --strict .` from `backend/`, and the difference is `tests/`.** A test file is the easiest place in the repository to miss, because a lane running its own module's suite never type-checks it.

**Not fixed by Lane B.** `infra/` and repository process are Lane C's ([D-022](DECISION_REGISTER.md)), and the file exists to test `certification-guard.py`. **The fix is three annotations; the judgement about whose file it is is not this lane's to make.**

### B-322 · Duplicate of [B-111](#b-111--tsc---noemit-is-in-no-gate-qe-runs-and-main-is-red) — withdrawn

| | |
|---|---|
| **Status** | **`CLOSED` — duplicate.** The id is retired and never reused |
| **Found** | 2026-08-04, by Lane B, rebasing onto `integration` |

**Lane B opened this for the `tsc` failure in `triage-strip.test.tsx`. QE opened [B-111](#b-111--tsc---noemit-is-in-no-gate-qe-runs-and-main-is-red) for the same failure within the hour, and split it better than this row did.**

**The split is the part worth keeping.** This row treated it as one defect in a fixture. B-111 separates two: **the type error, which is Lane A's**, and **the gate gap, which is QE's** — `tsc --noEmit` is in the Definition of Done for every lane and in no gate QE runs, which is how `main` reached a red state through a passing certification. **The second is the one that would have recurred.**

**Both are fixed on `integration`** at `b332aea`. Nothing is left for this row to track, and two rows for one defect is the register drifting from the repository.


### B-130 · D-107 removed `UI_WAVE_TASKS` and left its test referencing it

| | |
|---|---|
| **Module** | `infra/repository-dashboard.py` — Platform Foundation ([D-022](DECISION_REGISTER.md)) |
| **Current assignee** | **Lane C** — it authored `D-107` |
| **Severity** | 🟠 · **Blocking Quality Defect class** — a failing test, so the slice cannot be promoted |
| **Status** | **`OPEN` — `CHANGES REQUESTED`.** Reported with the line identified; **not fixed, another lane's file** |
| **Found** | 2026-08-06 by QE, cycle 77, validating the candidate |

**Steps to reproduce.**

```bash
make validate
→ AttributeError: module 'repository_dashboard' has no attribute 'UI_WAVE_TASKS'
   tests/certification/test_repository_generators.py:105
   TestAFigureIsDerivedRatherThanStated::test_implemented_counts_the_wave_rows_it_is_given
```

**Expected.** A slice that renames or removes a symbol updates the test that reads it, in the same change.

**Actual.** `b86a6bfd` (D-107) reshaped `repository-dashboard.py` — 48 lines changed — and **removed `UI_WAVE_TASKS`**. `backend/tests/certification/test_repository_generators.py:105` still binds it, so the suite fails on import of the attribute.

### The test is the good kind, which is why it must be repaired rather than deleted

```python
wave = next(iter(dashboard.UI_WAVE_TASKS))
assert dashboard._ui_implemented([(wave, "x", "IN VALIDATION")]) == 1
assert dashboard._ui_implemented([(wave, "x", "READY")]) == 0
```

Its own docstring says why it exists: *"`Implemented 0` and `Integrated 0` were both literals. The test that catches a constant is not one that checks today's number — it is one that **changes the input and requires the output to follow**."*

> **Whatever `UI_WAVE_TASKS` became, the property still holds** and the test should be pointed at the new name. **Deleting it would remove the guard against the exact defect D-107 was written to fix.**

### Why this is QE's finding rather than a gate's

**`make validate` catches it in one run**, and the Definition of Done requires the lane to have run its own gates on the rebased branch (§19, *self-validation performed*). **The slice reached QE without that**, which is the check that was skipped rather than a check that is missing.

**Lane A's work was not held for it.** [TASK-432](BACKLOG.md) validated and certified on its own; Lane C's six commits are returned and rejoin the next cycle once the test binds a symbol that exists.


### B-129 · `git reset --hard` destroyed a certification record, and `--audit-main` refused until it was re-earned

| | |
|---|---|
| **Module** | QE's own release procedure — the ordering of branch surgery against uncommitted records |
| **Current assignee** | **QE** |
| **Severity** | 🟠 · **The record of a run that happened was lost.** No data lost, and the repository asserted an untruth until repaired |
| **Status** | ✅ **`FIXED` — 2026-08-06, cycle 77.** ⚠️ **It recurred once before the fix was mechanical** — see *Third instance* below |
| **Found** | 2026-08-06 by QE, cycle 76, when the manifest count did not move after a promotion |

**Steps to reproduce.**

```bash
make certify                 # writes certification/manifest.json — uncommitted
git checkout lane-qe && git reset --hard main
python3 infra/certification-guard.py --audit-main
→ REFUSED — 7 commits neither certified, nor an ancestor of one, nor a Closeout
```

**`make certify` writes the manifest into the working tree.** Every branch operation between the run and the commit that stores it can discard it, and `reset --hard` does.

### The repair, and why the obvious one was refused

**The report file survives** — `reset --hard` does not remove untracked files — **and it holds the whole run**: gates, coverage, conditions, timestamp. **Reconstructing the manifest entry from it would have taken a minute.**

> ⛔ **A hand-written certification record is a fabricated record**, and it is worse than a missing one: the missing one is visible to `--audit-main` and the fabricated one is not. [§0b](QUALITY_ENGINEERING.md) forbids constructing a SHA for the same reason — *the repository's most load-bearing claim must never be produced by hand.*

**The record was re-earned instead**: `make certify` re-run at the same commit, unchanged tree, every gate passing again — **12 minutes, and a genuine record.** `--audit-main` clean afterwards: 70 certified, 500 inside a snapshot, none outside.

### ⚠️ Third instance — **after** the rule forbidding it was written

**Cycle 77, one cycle later.** `git reset --hard main` on `lane-qe`, the manifest entry for `a7c98393` destroyed, `--audit-main` refusing again. **§0e existed, was correct, and did not prevent it.**

> **A rule lives in a document; the command lives in muscle memory.** Three occurrences say the fix has to be *unrepresentable* rather than *written down* (`CLAUDE.md` §2 — prefer a violation that cannot be expressed over one that is merely discouraged).

**The fix, ratified by the product owner 2026-08-06** — *"always prefer operations that refuse unsafe states over operations that silently recover from them"*:

| Banned | Use |
|---|---|
| `git reset --hard <ref>` | `git switch <branch>` · `git merge --ff-only <ref>` |

**`merge --ff-only` refuses a dirty tree *and* a non-fast-forward. `reset --hard` refuses neither** — it succeeds under every condition, which is exactly what makes it wrong when a cycle's uncommitted output is in the tree.

**And the uncomfortable part: [`REPOSITORY_RELEASE_CHECKLIST.md`](REPOSITORY_RELEASE_CHECKLIST.md) never contained `reset --hard`.** Its synchronization step has always been `checkout && merge --ff-only`, which would have refused all three times. **The defect was improvisation, not documentation** — a faster equivalent typed instead of the step as written. The checklist now also asserts a clean tree before any branch operation, so the guard is in the runbook rather than in the reader.

### Second instance this session

**The first destroyed a bug filing** and produced a commit message claiming a row was closed when `grep -c` returned 0. **This one destroyed a certification record.** The pattern is the same: **`reset --hard` run while something the cycle produced was still only in the working tree.**

**The rule that prevents both: the record is committed before the branch is touched.** Certification produces an artifact; a cycle that moves a branch before storing it is racing its own evidence.

**Not automated, deliberately.** A guard here would have to know which uncommitted files matter, and it would be one more check whose output nobody branches on ([B-128](#b-128--a-rejected-push-did-not-stop-the-promotion-and-main-diverged-from-integration)). **The ordering is the fix.**


### B-128 · A rejected push did not stop the promotion, and `main` diverged from `integration`

| | |
|---|---|
| **Module** | QE's own release procedure — [`QUALITY_ENGINEERING.md` §0c](QUALITY_ENGINEERING.md) |
| **Current assignee** | **QE** |
| **Severity** | 🟠 · **No data lost and no guarantee broken** — but the repository spent several minutes in a state its own model forbids |
| **Status** | **`OPEN`** |
| **Found** | 2026-08-06 by QE, cycle 76, reading the output of its own integrate step |

**Steps to reproduce.**

```
PUSH_EXIT=1
local e636018b · origin/integration b7eb036c     ← printed, and not acted on
GUARD_EXIT=0
PROMOTE_EXIT=0                                   ← promoted anyway
```

**A lane pushed a claim commit to `integration` during certification**, so the integrate push was rejected as non-fast-forward. **The compound command continued** and promoted the certified commit to `main`.

### What did not go wrong, stated first so the severity is legible

| | |
|---|---|
| **`promoted == certified`** | ✅ Held. `e636018b` was the certified SHA, confirmed by the guard *before* the promotion |
| **`--audit-main`** | ✅ Clean — 70 certified, 500 inside a snapshot, **none outside** |
| **Anything lost** | ✅ Nothing. The claim commit stayed on `integration`; the promoted work stayed on `main` |

**What broke is the ordering invariant**: `main` must be an ancestor of `integration`, and for several minutes it was not. **Repaired by rebasing the claim commit onto `main`** — Closeout activity 10, performed early.

### [§0c](QUALITY_ENGINEERING.md) was followed and was not enough

**§0c says an integrate step ends by comparing the two refs**, *"because agreement is a fact and a zero exit code is an inference."* **The comparison ran. It printed. Nothing consumed it.**

> **A check whose result is printed and not branched on is Decorative Logic** (`CLAUDE.md` §2) — it produces the reassurance of verification without the effect of it. **§0c described the measurement and left out the consequence**, and a rule that stops at *"look at this"* depends on the reader, which is exactly what a gate is for.

**The fix is one word in the procedure and one line in the script: the comparison must gate the next step.**

```bash
git push origin HEAD:integration || exit 1
[ "$(git rev-parse HEAD)" = "$(git rev-parse origin/integration)" ] || exit 1
```

**Second instance this session of a captured exit code being read and not obeyed** — the first is §0c's own origin. **That is the argument for making it mechanical rather than writing the rule a third time.**


### B-127 · The revocation guarantee lives in a feature test, and not in the Security Invariants

| | |
|---|---|
| **Module** | `backend/tests/security_invariants/` — the suite, which is QE's |
| **Current assignee** | **QE** |
| **Severity** | 🟡 · **Non-blocking.** The behaviour is correct and tested. The *guarantee* is not where §11 puts it |
| **Status** | ✅ **`FIXED` — QE, cycle 70, 2026-08-05**, certified at `ce1a658`. **387 → 389 invariants**, mutation-checked |
| **Found** | 2026-08-05 by QE, certifying cycle 69 — the invariant count did not move while a tenancy defect was being fixed |

**Steps to reproduce.**

```bash
make certify | grep security-invariants
→ 387 invariants        # 387 before TASK-437, 387 after
grep -rn "ended" backend/tests/security_invariants/ | wc -l
→ 0
```

**[B-206](#b-206) was a live authorization defect**: `WorkspaceQueryService.get_membership` selected on `(workspace_id, user_id)` only, so **an ended membership still resolved on every authenticated request** and `member:remove` — shipped in M1 — revoked nothing. Lane A found it, fixed it, and covered it **through the customer's door** in `tests/integration/test_api_leave_workspace.py`.

**That test is correct and it is the wrong home for this guarantee.**

### Why §11 wants it in both places

> *"The Security Invariants suite states architectural guarantees — token verification, Casbin enforcement, workspace isolation, RLS … rather than feature behaviour. **Deliberate overlap with feature tests is intended so that rewriting a feature cannot remove its guarantee.**"*

**The feature here is *leaving*. The guarantee is *an ended membership grants nothing*** — and those have different lifetimes. A future slice that reshapes the leave endpoint, or replaces `test_api_leave_workspace.py` wholesale, **takes the only proof of the guarantee with it**, and nothing would notice: the defect it protects against was invisible for the entire life of the repository precisely because nothing asked.

### What QE will add

**One invariant, asserted at the authorization boundary rather than through the endpoint** — `resolve_role` refuses an ended membership — so it holds whatever route ends one. **QE writes tests in any module's suite; it does not change that module's production code**, and here there is nothing to change: the fix is already in.

> **This row exists rather than the test, because adding the test is an executable change and needs its own certified cycle.** Filing it is how it survives the gap.


### B-126 · Four architecture document numbers are claimed twice, and QE promoted the newest without seeing the warning

| | |
|---|---|
| **Module** | `commercial_profile` documentation — `docs/architecture/25-commercial-profile.md` |
| **Current assignee** | **Lane B** — it authored the second file |
| **Severity** | 🟡 · **Non-blocking.** No gate fails; a reference to *"document 25"* is now ambiguous |
| **Status** | **`FIXED` for `25` — Lane B, 2026-08-05.** ⚠️ **And the collision was the smaller half.** **`40-commercial-profile.md` already existed and is this module's design doc** — so `25-commercial-profile.md` was not merely misnumbered, it was **a second design document for one module**, which is the duplicated-truth defect (§2) rather than an identifier clash. **Its two sections are merged into `40` and the file is deleted.** **No new number was allocated**, which is the right outcome while document numbers still have no allocation block. **`49`, `50` and `51` are untouched — they need the ruling this row asks for, and `VERIFIED` is QE's** |
| **Found** | 2026-08-05 by `infra/state-check.py` at cycle 67 Closeout. **Reported then, seen at cycle 68** |

**Steps to reproduce.**

```bash
ls docs/architecture/25-*
→ 25-commercial-profile.md   25-signal-engine.md
python3 infra/state-check.py | grep 'document 25'
→ Architecture document 25 is claimed by 2 files … the collision class C-201 names
```

**Expected.** One number, one document. **Actual.** Two, and `main` carries both.

**And `25` is not alone.** Read in full, `state-check.py` reports **four collisions**, three of them older than this cycle:

| Number | Claimed by | Assignee |
|---|---|---|
| **`25`** | `25-signal-engine.md` · `25-commercial-profile.md` | **Lane B** — it added the second, 2026-08-05 |
| **`49`** | `49-end-to-end-product-validation.md` · `49-lead-ownership.md` | **Unassigned — needs a ruling** |
| **`50`** | `50-product-capability-audit.md` · `50-sales-engagement.md` | **Unassigned — needs a ruling** |
| **`51`** | `51-implementation-specifications.md` · `51-sales-workspace.md` | **Unassigned — needs a ruling** |

**One row, not four**, because it is one class with one resolution: **architecture document numbers have no allocation block.** `B-`, `C-`, `TASK-` and ADR numbers all do (§20e), and none of them has ever collided since. **Document numbers were left out, and they are the only identifier still allocated by *"the highest number I can see"*** — which is precisely the model §20e replaced after `B-024` was allocated twice.

### The half of this that is QE's

**`state-check.py` printed this at cycle 67's Closeout and QE did not read it**, because the output went through `head -14` and the finding was on line 19. **The hard checks were read; the advisory list underneath them was truncated away.**

> **[§0a](QUALITY_ENGINEERING.md) said *never read a gate's verdict through a pipe*.** It did not say *and that includes everything printed after the verdict*. **This is the third instance this session of a verdict read through something that discarded part of it**, and the first where the discarded part was a real finding about `main`.

**The renumbering itself is a governance choice, not a repair QE may make** — `state-check.py` says so in as many words: *"each of these has more than one correct resolution, and choosing between them is a governance decision."*


### B-125 · The new document-location check silently no-ops on a clone without `origin/integration`

| | |
|---|---|
| **Module** | `infra/state-check.py` — check 5c-2, added 2026-08-05 |
| **Current assignee** | **Lane C** — it authored the check, and `infra/` is its Platform Foundation responsibility ([D-022](DECISION_REGISTER.md)) |
| **Severity** | 🟡 · **Non-blocking.** Advisory tooling, and the failure is *under*-reporting rather than a false alarm |
| **Status** | **`OPEN`** |
| **Found** | 2026-08-05 by QE, validating the check that introduced it |

**Steps to reproduce.**

```python
tracked = set(_git("ls-tree", "-r", "--name-only", "origin/integration").splitlines())
for doc in ...:
    if relative not in tracked:
        continue          # genuinely absent — the warning is true.
```

```bash
git ls-tree -r --name-only origin/nonexistent   # rc 128, stdout empty
```

**A clone with no `origin/integration`, or one that has not fetched, produces an empty `tracked` set** — so **every document is treated as genuinely absent and the check never fires.** It reports success by reporting nothing.

### This is [B-112](#b-112--the-gatekeeper-answers-from-a-stale-clone)'s class, in the file B-112 was fixed in

**B-112**: `--next-cycle` answered *"Repository Ready"* from stale local refs. The fix was to **refuse when the clone is behind rather than answer from it** — *"a stale clone produces a confident wrong answer rather than a visible failure."*

**The same shape, one file over**: a silent no-op is a confident *absence* of a wrong answer, which is harder to notice than a wrong one.

> **The fix is the same shape too.** Establish the precondition or refuse — `git rev-parse --verify origin/integration` first, and say so when it is missing. **The check is worth having; it just needs to know when it cannot run.**


### B-124 · Backlog rows never reach a terminal state, so seventeen of them describe work that is on `main`

| | |
|---|---|
| **Module** | Repository process — [`BACKLOG.md`](BACKLOG.md)'s execution states, and `infra/state-check.py` |
| **Current assignee** | **QE** — terminal execution states are QE's exclusively (`CLAUDE.md` §20e) |
| **Severity** | 🟡 · **Non-blocking.** Nothing fails; the repository simply asserts something untrue about itself |
| **Status** | **`OPEN`** |
| **Found** | 2026-08-05 by QE, during cycle 66 Closeout, while setting `PROMOTED` on the two rows it had just certified |

**Steps to reproduce.**

```bash
# every row still in a non-terminal state
grep -n '^| \*\*Status\*\* |' docs/BACKLOG.md | grep -E 'IN VALIDATION|IN PROGRESS'
# then, for any id it names
git log main --oneline --grep=TASK-903 | grep -v ' Claim '
→ fourteen commits on main
```

**Expected.** A row whose work is on `main` reads `PROMOTED` or `DONE`.

**Actual.** **Seventeen rows read `IN VALIDATION` or `IN PROGRESS` while carrying implementation commits on `main`** — TASK-300, TASK-402, TASK-301, TASK-407, TASK-200, TASK-204, TASK-205, TASK-405, TASK-409, TASK-410, TASK-903, TASK-904, TASK-905, TASK-415, TASK-416, TASK-417, TASK-414.

### Why it accumulates rather than being an oversight

**The lifecycle has no step that writes the terminal state.** Repository Closeout activity 3 reconciles [`ACTIVE_ASSIGNMENTS.md`](ACTIVE_ASSIGNMENTS.md) — *"promoted claims marked `COMPLETE` and then removed"* — and **says nothing about the backlog row**, which is a different file with a different lifecycle. The lane sets `IN VALIDATION` and its responsibility ends there by rule; QE removes the board row; **nobody is sent back to the backlog.**

> **Lane C found the same class from the other end** at `1d15198`, *"Queue reconciliation — four rows reported outstanding work that had already been done"* — the queue files had it too. **Two registers drifting the same way is the tell that the process, not either lane, is what is missing a step.**

### Why QE did not simply mass-correct the seventeen

**A `grep` proves commits mention the id. It does not prove the task's scope is complete**, and at least one row — [TASK-400](BACKLOG.md) — is explicitly part-delivered with its other half held on a coordination item. **Marking that `PROMOTED` would replace one false statement with a worse one.**

**Each row needs its completeness confirmed by the lane that built it**, and then the terminal state set by QE. **The two rows certified in cycle 66 were set directly**, because QE measured those itself.

### The fix worth making

**A check, not a habit.** `infra/state-check.py` already compares the documents against git; it should refuse a Closeout that leaves a backlog row in a non-terminal state while `git log main --grep=<id>` shows implementation commits. **A rule kept by discipline can be kept by a machine instead** (`CLAUDE.md` §20e) — and this one has not been kept by discipline for at least seventeen rows.


### B-123 · The frontend suite is in no gate, and a failing test is on a lane branch right now

| | |
|---|---|
| **Module** | Repository tooling — the certification gate set, and `make validate` |
| **Current assignee** | **QE** — the gate set is QE's |
| **Severity** | 🟡 · **was 🟠.** Stage 1 runs the suite from cycle 71, so *nothing runs them* is no longer true — what remains is that **certification does not** |
| **Status** | **`OPEN` — half fixed.** ✅ `make validate` runs `vitest`, cycle 71, certified at the commit below. ⚠️ **`REQUIRED_GATES` still six**, and making it seven needs a ruling — see the bottom of this row |
| **Found** | 2026-08-05 by QE, running `vitest` by hand on a slice whose tests are entirely frontend |

**Steps to reproduce.**

```bash
grep -oE 'name="[a-z-]+"' backend/tests/certification/__main__.py | sort -u
→ import-linter · mypy · pytest · security-invariants · smoke · tsc
```

**No `vitest`.** And `make validate` ran the backend suite and `tsc` — **also no `vitest`**, asserted deliberately by what was then `test_it_runs_the_two_gates_it_claims_and_no_others`.

### ✅ Half closed, 2026-08-05, cycle 71 — stage 1 now runs it

```
1  migrate       signora_validate_<commit>
2  tsc --noEmit  clean
3  vitest        Tests  1255 passed (1255)      ← added
4  suite         the whole suite, with coverage
```

**`vitest` meets the admission rule `validate.py` already applies to `tsc`**: needs nothing, takes seconds, in no other gate. **Skipped for a subset run** — `-m security_invariant` is a question about the backend, and answering it with the whole frontend suite is the padding that teaches people to reach for `--quick`.

**The summary line is read, never assumed.** A reporter change that stopped printing totals must produce a line that *says* it found nothing rather than one that looks like a pass — [B-125](#b-125--the-new-document-location-check-silently-no-ops-on-a-clone-without-originintegration)'s class, and the branch has its own test so it is not decorative.

### ⚠️ The other half stays open, and it is not a coding session's to close

**`REQUIRED_GATES` is deliberately untouched.** Adding a seventh gate would make **every certification record ever written unsatisfied** — none of them ran it, `missing_gates` would be non-empty, and `is_certified` would read false across the whole history that `--audit-main` walks.

**The record format anticipates this**: `RECORD_VERSION` exists *"so that a reader can tell a missing field from one that never existed."* Making the required set version-aware is the shape of the fix — **and it changes what certification means** ([ADR-0032](architecture/adr/0032-release-certification.md)), which is a product-owner decision rather than one taken inside a slice.

> **So a frontend regression can still reach `main` if QE's stage 1 is skipped**, and the honest scope of this fix is: **it will not reach `main` through a validation QE actually ran.** That is most of the exposure and not all of it.

### This is [B-111](#b-111--tsc---noemit-is-in-no-gate-qe-runs-and-main-is-red)'s class, one level over

**B-111**: `tsc --noEmit` was in the Definition of Done and in no gate, and `main` reached a state where it failed. **The fix added `tsc` and stopped there.** `vitest` was never added, so **the same hole remains for the 1235 tests that check what a customer sees.**

> **`smoke` cannot cover it**: `.dockerignore` excludes `tests/`, which is the same reason it could not see `tsc` failures — recorded in B-111 and still true.

**A slice whose tests are entirely frontend passes `make validate` completely** — as [TASK-903/904/905](BACKLOG.md) just did at **3573 backend, unchanged**, because eleven executable files were all frontend and four of them were the tests.

### What it caught the moment it was run by hand

```
FAIL tests/components/reachability.test.tsx > the live repository > has no route without an entrance
  → expected '…Customer Reachability…' to match /No entrance at all\s+0/
```

**A real finding, and arguably a correct one**: the slice adds `/join/[workspaceId]`, which is reached from an **invitation email** and deliberately has no in-app entrance. **The check does not know that yet.** Whether the route needs an exemption or the check needs widening is the implementing lane's call — but **nothing in the repository would have asked the question.**


### B-121 · QE validated on the shared stack all day, because its branch name derives nothing

| | |
|---|---|
| **Module** | QE's own operating practice — the validation branch |
| **Current assignee** | **QE.** `infra/` is correct and nothing is asked of Lane C |
| **Severity** | 🟠 — **it made QE's own measurements untrustworthy**, which is [B-118](#b-118--lanes-share-one-postgresql-so-two-suites-running-at-once-fabricate-each-others-failures)'s severity for B-118's reason |
| **Status** | **`FIXED`** 2026-08-05 — QE's stack is up (`signora-lane-qe`, PostgreSQL 5632) and the practice is [§0d](QUALITY_ENGINEERING.md). **`VERIFIED` is another lane's** |
| **Found** | 2026-08-05 by QE, after a validation dissolved into `FEFEFEFE` with one other suite running |

**Steps to reproduce.**

```bash
git checkout qe-validate && python3 infra/environments.py --exports
→ # no environment derived (not on a lane branch) — historical shared stack
→ COMPOSE_PROJECT_NAME=signora-v2 · SIGNORA_POSTGRES_PORT=5432

git checkout lane-qe    && python3 infra/environments.py --exports
→ COMPOSE_PROJECT_NAME=signora-lane-qe · SIGNORA_POSTGRES_PORT=5632
```

**QE validates a lane's tree by pointing a throwaway branch — `qe-validate` — at their tip.** The derivation keys off the *branch name*, so **every QE validation today used the shared stack** while the lanes moved onto their own. **That is why [B-118](#b-118--lanes-share-one-postgresql-so-two-suites-running-at-once-fabricate-each-others-failures) kept reproducing after it was fixed: the fix worked and QE was not standing in it.**

> **`environments.py` announced it every single time**, in the line above the value — *"Named, not silent. Falling back is correct on `integration`; doing it without saying so is how four clones came to share one server."* **It said so. QE did not read it.**

### This row was filed once, destroyed, and written again

**The original filing was lost to QE's own `git reset --hard`** while cleaning the working tree, and QE did not notice — **then published a commit message announcing the row was closed when the row did not exist.** Caught by `grep -c "B-121" docs/BUGS.md` returning `0` during that same commit's verification.

**That is the third time in this session a git command of QE's destroyed uncommitted work**, and the second time a claim was published before it was checked. **The register is the record; a commit message asserting something about it is not.**

### The fix, and the half that must not be copied

| | |
|---|---|
| **`make validate`** | **QE's own stack.** A six-minute suite that runs while lanes work |
| **`make certify`** | **The default stack, unforced.** Certify also drives the production stack on 3100/8100; overriding `COMPOSE_PROJECT_NAME` made `smoke` fail at *4 stages in 27s* |


### B-120 · The repository's self-describing generators have no tests, and have been wrong three times

| | |
|---|---|
| **Module** | Platform Foundation — `infra/repository-dashboard.py`, `infra/decision-queue.py`, `infra/implementation-status.py`, `infra/project-history.py` |
| **Current assignee** | **Lane C** — Platform Foundation |
| **Severity** | 🟡 — wrong but survivable. **These are not gates**, so a wrong figure blocks nothing; it misinforms |
| **Status** | **`OPEN`** — observation, **not a blocker.** The slice that prompted it was validated and promoted |
| **Found** | 2026-08-05 by QE, validating Lane C's register-audit slice |

**Steps to reproduce.**

```bash
grep -rl "repository-dashboard\|decision-queue" backend/tests/
→ (no results)
```

**Four generators produce the documents the repository uses to describe itself, and no test executes any of them.** They are outside the coverage gate's scope (`modules`, `signora_platform`, `apps`), so their absence is invisible to every measurement QE publishes.

### The evidence is Lane C's own commit titles

| | |
|---|---|
| *"**Implemented 0 was hardcoded**, and wave 1 made it false"* | A count that was a literal |
| *"**Integrated 0 while wave 1 sat on `main`** — the label meant one thing, the data another"* | A field name that did not match its contents |
| *"**Eighteen index rows disagreed with their own item bodies**"* | A summary that had drifted from its detail |

> **Three wrong outputs, each caught by a person reading them.** That is exactly the detection method §2 rejects elsewhere — *"a violation that is unrepresentable beats one that is merely discouraged"* — and each of these was **representable, shipped, and found later.**

### Why QE is recording it rather than blocking on it

**A wrong dashboard is not a wrong product.** These generate documentation, not behaviour; no gate consumes them, and the slice that prompted this row passed every gate and was promoted. **Blocking on it would be QE deciding a priority that is not QE's.**

**But the repository's own standard is unambiguous** — *"no change ships without tests"* (§11) — and the exemption these enjoy is accidental rather than reasoned: they sit in `infra/`, which the coverage gate does not scope. **A generator asserting `implemented: 0` while wave 1 sits on `main` is the repository telling a reader something untrue about itself**, which is the defect class §2 exists for.

**One test per generator that runs it and asserts one derived figure against a known input** would have caught all three.


### B-119 · The lease fix left its old test behind, and two test files now describe one module

| | |
|---|---|
| **Module** | Platform Foundation — `infra/environment-lease.py` and its tests |
| **Current assignee** | **Lane C** — Platform Foundation, and the author of the slice |
| **Severity** | 🟠 · **Blocking Quality Defect** — 14 errors, certification would refuse |
| **Status** | ✅ **`FIXED`** — Lane C, 2026-08-05. **`VERIFIED` is QE's.** **Repaired rather than deleted**: the certification file carried **fourteen** tests to the new file's four — inherited leases, release on failure, the child's environment, partial writes, a live lease not reclaimed, and the `dr`/`smoke` Makefile wiring — so deleting it would have lost ten real properties to fix a fixture. **Its fixture now redirects `LEASE_DIR` instead of a `LEASE` constant that no longer exists**, the four cross-clone tests fold in as their own class, and `backend/tests/test_environment_lease.py` is gone. **One file describes one module.** ✅ **17 lease tests · 101 certification tests · `mypy --strict` 735 files clean · 3446 collected.** ⚠️ **The one gate this clone cannot run is stated rather than skipped silently**: `tests/integration/test_worker_retry.py` needs `database_url`, and **Lane C holds no runtime by governance** — `make doctor` says so. Unchanged by this slice, and last touched at `dc86b34` |
| **Found** | 2026-08-05 by QE, validating the [B-118](#b-118--lanes-share-one-postgresql-so-two-suites-running-at-once-fabricate-each-others-failures) fix |

**Steps to reproduce.** On `lane-c-sync` at `f81fe13a`:

```bash
make validate
→ 3438 passed, 14 errors
```

**Actual — all fourteen in one file, all the same:**

```
ERROR tests/certification/test_environment_lease.py …
E   AttributeError: <module 'environment_lease'> has no attribute 'LEASE'
```

### The cause is the fix's own good idea, half-applied

**The lease moved from a module-level constant to a computed path** — `LEASE` became `_lease_path()`, so that every clone driving one Docker project resolves the same file. **That is the whole point of B-118 and it is right.**

**A new test file was added** at `backend/tests/test_environment_lease.py`. **The old one was not removed**: `backend/tests/certification/test_environment_lease.py` still references `LEASE` in **eight** places, and it is now the only thing in the repository that believes the constant exists.

> **Two test files now describe one module, and one of them is wrong.** §2 — *truth has exactly one authoritative representation.* The fix should delete the old file or move its surviving cases into the new one; **keeping both is the duplicated truth the principle forbids, and the stale copy is the one that fails.**

### This is signal, and QE says so explicitly because the last three runs were not

**3438 passed. Fourteen errors, one file, one deterministic `AttributeError`.** That is nothing like [B-118](#b-118--lanes-share-one-postgresql-so-two-suites-running-at-once-fabricate-each-others-failures)'s signature — 40 then 238 failures scattered across six unrelated modules with deadlocks and missing catalogs. **A real defect names one cause in one place and reproduces.**

**Nothing else in the slice is in question.** The lease relocation itself is correct, well-argued, and is the fix QE has been blocked by.


### B-118 · Lanes share one PostgreSQL, so two suites running at once fabricate each other's failures

| | |
|---|---|
| **Module** | Development environment — `infra/docker-compose.yml`, the shared PostgreSQL instance |
| **Status** | ✅ **`FIXED`** — Lane C, 2026-08-05. **`VERIFIED` is QE's.** **436 change ② is built and approved**: *"create separate environment for each lane so that nothing could be shared."* `docker-compose.yml` reads `${COMPOSE_PROJECT_NAME:-signora-v2}` and `${SIGNORA_*_PORT}`; `environments.py` derives **PostgreSQL `5432+100n`, Redis `6379+100n`, MinIO `9000/9001+100n`** and resolves this clone from `SIGNORA_ENVIRONMENT`, else the branch, else nothing. **The Makefile derives every value — no lane types a port.** ✅ **12 allocation tests** assert no two environments collide on any port; **113 certification tests pass; `mypy --strict` 736 files clean.** ⚠️ **Slot 0 is unchanged**, so nothing that worked stops working |
| **Current assignee** | **Lane C — Platform Foundation**, 2026-08-05, product owner direction. **QE raised it and cannot be the lane that repairs the instrument it certifies with** — it needs this fix in order to certify, which is precisely why it should not also own it. **Assessed in [436](architecture/436-execution-isolation.md)**: root cause is `infra/docker-compose.yml` line 6, `name: signora-v2`, hard-coded — while `environments.py` derives `compose_project` per environment and **nothing in the repository reads it** |
| **Severity** | 🟠 · **it makes measurement untrustworthy**, which is worse than a failing test: a failing test is information |
| **Status** | **`OPEN`** — reported with evidence; **no fix attempted yet** |
| **Found** | 2026-08-05 by QE, validating Lane A's `0039` slice twice and getting two different wrong answers |

**Steps to reproduce.** Have two lanes run `make validate` at the same time. Each creates its *own* disposable database, so this looks safe. It is not: **they share one PostgreSQL server, one connection pool, one lock manager.**

**Actual — two runs of the same commit, minutes apart:**

| Run | Result | While |
|---|---|---|
| 1 | **40 failed, 87 errors** | Lane A's own suite running |
| 2 | **238 failed, 22 errors** | Lane A's suite still running, deeper overlap |

```
21 × asyncpg.exceptions.DeadlockDetectedError
13 × asyncpg.exceptions.InvalidCatalogNameError    ← "database does not exist"
 3 × ConnectionDoesNotExistError: connection was closed in the middle of operation
```

**Confirmed from the process table, not inferred:**

```
/home/ganesh/Projects/LaneA/signora-lane-a/backend/.venv/bin/pytest --cov
/home/ganesh/Projects/Signora-QE/backend/.venv/bin/pytest --cov
```

### The fix has a bootstrap problem, and cycle 57 hit it

**Certifying the fix itself aborted**, on a shared object no per-database isolation could have protected:

```
sqlalchemy.exc.InternalError: tuple concurrently updated
[SQL: ALTER ROLE signora_app NOBYPASSRLS]
```

**A PostgreSQL role is cluster-wide.** Two suites reaching `ALTER ROLE` together collide however many databases they each own — so **the lease, not the database, is the only mechanism that can prevent this**, which is what Lane C's fix does.

> **But a workstation lease only excludes clones that hold it.** QE's tree had the fix; **Lane A's clone did not**, because it is not promoted yet. QE took a workstation-scoped lease, Lane A took a repository-scoped one, and **two leases over one resource exclude nobody.**

**Recorded as an abort, not a failure** — the gate never evaluated the repository, it was interrupted by a resource another clone was using, and no certification record was written. *A failure is a statement about the commit; an abort is a statement about the run.*

**The sequencing consequence, for whoever schedules this:** the fix takes effect for a lane **only once it has promoted and that lane has rebased onto it.** Until every clone carries it, contention persists exactly as before — and the window in which the fix exists but is not yet universal is the window in which it looks like it does not work.

### The mechanism, found by Lane C — and one test that demonstrates it exactly

**Lane C diagnosed the cause while QE was blocked by the symptom**, and their finding is the better one:

> `infra/docker-compose.yml` line 6 reads **`name: signora-v2`, hard-coded.** `environments.py` derives `compose_project = signora-<name>` per environment. **Repository-wide search for `COMPOSE_PROJECT_NAME`: no results.** So every lane's `docker compose` targets one project and all four clones share one PostgreSQL server.
>
> **"It is an enforcement problem wearing a design problem's clothes."**

**The repository already allocates every isolation the directive asks for** — a database, an auth database, a Redis index, a bucket and a compose project, for each of nine environments. **Three of those allocations are ignored by the code that would have to honour them.** Nothing needs designing; something needs wiring.

**`B-118` and `B-317` moved to Lane C as Platform Foundation on the product owner's direction.** QE raised this while blocked by it, and `infra/` is not QE's to change.

#### One test demonstrates it in a single line

```python
# backend/tests/certification/test_disposable_database.py:87
name = "signora_certify_selftest01"          # ← fixed, in every clone
```

**A run on a quiet database gave `1 failed, 3473 passed`** — against **40** and **238** on the same code minutes earlier. **The one failure was this test**, asserting *"a previous run left this behind"*, because Lane A's suite reached the identical hard-coded name at the same moment. The database was **gone seconds later**, which is what a race looks like rather than a leak.

> **That single failure is the whole bug at 1:3474 scale**, and it is the cleanest evidence in this row: **a fixed name is only safe when the server is not shared.**

### Why this is worse than a failing test

**The failures land in modules the slice never touches** — `simulation`, `sales_engagement`, `knowledge_graph`, `observation_engine` — and they name real-looking causes. **A lane reading that list would chase a phantom in its own code**, and QE reading it would file a defect against a lane that did nothing wrong.

> **This class has now come close to producing a fabricated defect report three times in one day.** Twice the cause was QE's own invocation ([B-116](#b-116--the-safe-database-route-existed-only-for-the-whole-suite-so-every-narrower-question-left-it), and the shared-database runs that preceded `make validate`). **This time the cause was another lane doing its job correctly**, which is the version no amount of QE discipline can prevent.

**The instance is the boundary that is missing.** [RE-03](RELEASE_ENGINEERING.md) and [B-116](#b-116--the-safe-database-route-existed-only-for-the-whole-suite-so-every-narrower-question-left-it) gave every run its own *database*; **isolation stops at the schema.** Deadlock detection, connection limits and `DROP DATABASE … WITH (FORCE)` all operate at the *server*, and that is still shared.

### What QE is doing about it now, and what it is not

**Not doing:** killing another lane's suite to obtain a green run. *"Never stop somebody else's review session to obtain a green pipeline"* (product owner) — and the same reasoning covers a lane's validation. **Not doing:** publishing any number measured during contention.

**Doing:** waiting for a quiet instance, bounded — **because the honest possibility is that no quiet window exists.** With three active lanes each validating, contention may be the normal state rather than the exception, and *"QE cannot obtain a trustworthy measurement while lanes are working"* would be a far more serious finding than any slice waiting behind it.

**This row exists before the fix, deliberately.** Lane A and Lane B were both running suites while it was written. **Either could be reading a contended failure list right now**, and a lane chasing a phantom in its own module is the cost this record is meant to prevent.

### ✅ Lane C — the arbitration half is built, and a design for the instance QE found

**Change ① of [436](architecture/436-execution-isolation.md) shipped 2026-08-05.** The lease was `REPO_ROOT/.environment-lease` — **four clones, four lease files, one Docker project**, so Lane A holding the environment was invisible to QE *by construction*. It now lives at `${XDG_RUNTIME_DIR}/signora-leases/<compose-project>.lease`, **beside the resource and named for it.** Verified in two processes from two directories: the second printed `BLOCKED`, named the holding clone, and exited `4` without running its command.

> **That makes contention refused. It does not make it impossible** — that is change ②, and it needs a product owner ruling because it costs four container sets on one workstation.

**On `signora_certify_selftest01`, and it is QE's to change rather than this lane's.** The recommendation is **key the name on the clone, not on the run**:

| | |
|---|---|
| **A fixed name** | Two clones race. **What QE observed** |
| **A per-run unique name** | No race — **and `assert not _exists(name), "a previous run left this behind"` becomes vacuous.** The residue check is the point of the test |
| ✅ **A per-clone name** | **Two clones cannot collide, and a re-run in one clone still detects its own residue.** The assertion keeps its meaning |

**Something like `signora_certify_selftest01_<8 hex of the repo path>`.** **The symmetry is worth stating**: the lease is keyed on what is *shared* and this name must be keyed on what is *not*. Same question, opposite answer, and getting either backwards is this defect.

**Not applied here.** `backend/tests/certification/` is QE's instrument and is run by `make certify`, which is QE's gate — **the same reason this lane left `conftest.py` alone in [B-317](#b-317)**, and the reason Lane B left [B-117](#b-117) alone in `infra/`.

### B-117 · `test_repository_impact.py` fails `mypy --strict` — three unannotated `monkeypatch` parameters

| | |
|---|---|
| **Module** | Platform Foundation — `backend/tests/test_repository_impact.py` |
| **Current assignee** | **Lane C** — Platform Foundation, and the author of the slice |
| **Severity** | 🟠 · **Blocking Quality Defect** — a failing type check prevents promotion (`CLAUDE.md` §20e) |
| **Status** | ✅ **`FIXED`** — Lane C, 2026-08-05. **Three `monkeypatch` parameters annotated `pytest.MonkeyPatch`.** `mypy --strict .` from `backend/`: **733 source files, no issues.** 27 tests still pass. **`VERIFIED` is QE's to set** |
| **Found** | 2026-08-05 by QE, certifying cycle 55 |

**Steps to reproduce.**

```bash
cd backend && uv run mypy --strict .
```

**Expected.** Clean — `CLAUDE.md` §19 lists `mypy --strict` among the conditions for a slice to be implementation-complete.

**Actual.**

```
tests/test_repository_impact.py:189: error: Function is missing a type annotation for one or more parameters  [no-untyped-def]
tests/test_repository_impact.py:207: error: …
tests/test_repository_impact.py:224: error: …
Found 3 errors in 1 file (checked 733 source files)
```

**The fix is three annotations.** `monkeypatch` needs `pytest.MonkeyPatch`:

```python
def test_the_skip_check_can_actually_fire(
    guard: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
```

### Duplicated as [B-323](#b-323--mypy---strict-fails-on-integration-in-the-test-that-proves-the-guard-fires), and Lane B's analysis is the better one

**Two lanes found this within the hour, independently** — QE certifying, Lane B rebasing onto `bfbeeef` and re-running its gates because *"the rebase carried executable change."* **Both rows stand; neither is retired**, and this one defers to theirs on the cause:

> **The gate is `mypy --strict .` from `backend/`, and the difference is `tests/`.** A lane running its own module's suite **never type-checks its own test files** — which is why *"a test file is the easiest place in the repository to miss."*

**That is [B-115](#b-115--task-301-fails-mypy---strict-on-a-test-helper-narrower-than-the-type-it-builds)'s class, and Lane B caused that one.** They named the connection themselves rather than waiting for QE to.

**Lane B did not fix it, and was right not to.** The file tests `certification-guard.py`; `infra/` and repository process are Lane C's under D-022. *"The judgement about whose file it is is not this lane's to make."* **Finding a defect outside your assignment is an obligation to report it, never permission to fix it** (`CLAUDE.md` §20e) — applied exactly.

### Why `make validate` did not catch it, and that is not a gap

**`make validate` runs the suite and `tsc`; `mypy` belongs to certification** — asserted deliberately by `test_it_runs_the_two_gates_it_claims_and_no_others`, so that stage 1 does not become a slow second certification. **The gate that owns this check ran and refused.** Nothing failed to work.

### One observation on the gate's message, and QE is not fixing it

Certification reported:

```
mypy                no summary line
  · gate 'mypy' failed: no summary line
```

**That reads like a parsing glitch when the truth is three type errors.** `CLAUDE.md` §10 — *failure attribution must be truthful; an error must never name a component that was not involved* — and *"an incorrect attribution is worse than none, because it misdirects the investigation."* A reader would go looking at the gate before looking at their code.

**Recorded rather than repaired.** The gate ran and refused correctly, so this is a diagnostic improvement rather than *a repair so QE can certify* — which puts it on Lane C's side of the [D-022 clarification](../CLAUDE.md), not QE's.


### B-116 · The safe database route existed only for the whole suite, so every narrower question left it

| | |
|---|---|
| **Module** | Repository tooling — `infra/validate.py` |
| **Current assignee** | **QE** — its own tooling |
| **Severity** | 🟠 — **it reproduced the exact defect it was written to prevent**, in QE's own hands |
| **Status** | **`FIXED`** 2026-08-04, with two regression tests. **`VERIFIED` is another lane's** |
| **Found** | 2026-08-04 by QE, **by committing it** while validating Lane A's A-i slice |

**Steps to reproduce.** Ask a narrower question than the whole suite:

```bash
make validate ARGS="-m security_invariant"
```

**Expected.** The subset, against a database the run creates.

**Actual.**

```
usage: validate.py [-h] [--quick]
validate.py: error: unrecognized arguments: -m security_invariant
```

**So the only way to ask was `pytest` by hand** — no disposable database, straight at whatever the shell resolves.

### How it was found, which is the part worth keeping

A-i replaces a Security Invariant and adds one, and the handoff claimed **+1 net**. QE went to verify that count and ran:

```bash
cd backend && uv run pytest -m security_invariant -q
→ 12 failed, 368 passed
```

**Every one of those failures was the invocation's.** The same suite had passed inside `make validate` minutes earlier, and re-run against a migrated disposable database it gave **380 passed** — precisely the number the lane claimed.

> **This is [B-022](#b-022--tests-resolve-their-database-from-the-shell-that-launched-them)'s class, for the fourth time**, and the first time in QE's own hands *after* the tool existed to prevent it. It was caught only because a full green run existed to compare against. **With no full run to contradict them, twelve fabricated failures against `test_tenancy_policy.py` would have looked exactly like a tenancy defect** — which is how this class nearly cost Lane B a fabricated bug report.

### The fix, and the one judgement inside it

`parse_known_args()`, and everything unrecognised is forwarded to pytest.

**Coverage is dropped when a subset is requested.** A partial run cannot satisfy a repository-wide floor, and failing the gate for that reason says nothing about the code — worse, **the habit it teaches is `--quick`, reflexively**, including on the full runs where the floor is the entire point.

**The progress line was also lying.** It read *"with coverage"* while the code correctly dropped it, because it consulted `--quick` and not what the command actually contained. It now reports the scope and what was measured, derived from the command itself.


### B-115 · TASK-301 fails `mypy --strict`, on a test helper narrower than the type it builds

| | |
|---|---|
| **Module** | `knowledge_graph` — `backend/tests/knowledge_graph/fakes.py` |
| **Current assignee** | **Lane B** — the module's current assignee, and the author of the slice |
| **Severity** | 🟠 · **Blocking Quality Defect** — a failing type check prevents promotion (`CLAUDE.md` §20e) |
| **Status** | **`FIXED`** by Lane B 2026-08-04, in the shape named — and **`VERIFIED` by QE** on the revalidation: `mypy --strict` clean over 708 files |
| **Found** | 2026-08-04 by QE, validating TASK-301 at `81df236` |

**Steps to reproduce.**

```bash
cd backend && uv run mypy --strict .
```

— the identical invocation certification runs (`tests/certification/__main__.py:130`).

**Expected.** Clean. `CLAUDE.md` §19 lists `mypy --strict` among the conditions for a slice to be implementation-complete, and **the Slice Handoff claims it**: *"mypy --strict clean"*.

**Actual.**

```
tests/knowledge_graph/test_use_cases.py:767: error:
  Argument "domain" to "bound_binding" has incompatible type "None"; expected "str"  [arg-type]
Found 1 error in 1 file (checked 708 source files)
```

### The fix is one annotation, and the helper is the wrong half

`IdentityBinding.domain` is **`str | None = None`** ([`domain/identity.py:296`](../backend/modules/knowledge_graph/domain/identity.py)). The new test is right to pass `None` — a `TECHNOLOGY` entity resolved from `builtwith` has no domain, which is the whole point of the case it asserts. **`bound_binding`'s annotation is narrower than the type it constructs**:

```python
# backend/tests/knowledge_graph/fakes.py:288
def bound_binding(entity: Entity, *, provider: str, external_id: str, domain: str) -> IdentityBinding:
                                                                   # ^^^ str | None = None
```

**Do not change the call site.** The test is asserting the correct thing — *the kind is the entity's and not a constant* — and narrowing it to satisfy the helper would delete the case that makes the field a derivation rather than a decoration.

### Everything else passed

**Nothing else is wrong with this slice**, and the rest of it is measured green: **3269 backend** (+6), **1163 frontend** (+1), **95.06%** coverage, 379 Security Invariants, `tsc --noEmit` clean, **35 import contracts kept, 0 broken** — including the amber `ClaimReader` return-type change, which the contracts accept.

### Fixed within the hour, and the docstring is the part that lasts

Lane B widened `domain` to `str | None = None` and **wrote down why it had been wrong** — *"it was annotated `str` and had been narrower than the type it builds since it was written — invisible until a caller used the type honestly."* **That sentence is what stops it being re-narrowed** by a future reader who sees an optional parameter with one `None` caller and tidies it.

**Revalidated in full**, not just on the failing gate: 3269 backend, 1163 frontend, 95.06%, 379 invariants, `mypy --strict` clean over 708 files, `tsc` clean, 35 contracts kept.

> **The runtime is unaffected** — the suite passes, because `None` is a legitimate value at runtime and always was. **This is exactly the class `mypy --strict` exists to catch and nothing else can**: a helper that has been quietly lying about its own contract since it was written, found by the first caller to use the type honestly.


### B-114 · The release runbook's `make dr` step cannot succeed as written

| | |
|---|---|
| **Module** | QE's operating procedure — `docs/REPOSITORY_RELEASE_CHECKLIST.md` stage 2 |
| **Current assignee** | **QE** — the runbook is QE's |
| **Severity** | 🟠 — **a documented gate that aborts as written**, and whose abort output reads like a product failure |
| **Status** | **`FIXED`** 2026-08-04. **`VERIFIED` is another lane's** |
| **Found** | 2026-08-04 by QE, running cycle 45 |

**Steps to reproduce.** Follow stage 2 of the runbook exactly:

```bash
make certify   # passes
make dr        # the next line in the runbook
```

**Expected.** Disaster Recovery Validation runs.

**Actual.**

```
Baseline
  ✗ API did not become ready within 90s
make: *** [Makefile:62: dr] Error 1
```

**Three individually correct decisions, combining into an unrunnable step** — the same shape as [B-108](#b-108--the-production-image-cannot-build-because-a-root-config-imports-a-directory-the-image-does-not-ship):

| | |
|---|---|
| `make certify` runs `smoke` | which **tears the stack down when it finishes** — correct; it is what leaves the workstation clean |
| `make dr` runs against an **already-running** stack | correct, and documented in the Makefile: its precondition is the *inverse* of `release-preflight`'s, which is why it is deliberately not preflighted |
| The runbook puts them adjacent | with no `make up` between them |

**So `dr` has never been runnable straight from the runbook.** Earlier cycles passed it because QE brought the stack up from memory of the sequence — which is precisely the knowledge a runbook exists to stop depending on, and the next session would not have had it.

### Why this is filed rather than shrugged off

**The abort is indistinguishable from a failure in the output.** `API did not become ready within 90s` reads as *the product cannot start*, and the honest reading is *the gate was asked to test a stack nobody started*. **A failure is a statement about the commit; an abort is a statement about the run** — the distinction the product owner ratified, and the first thing this defect destroys.

**A runbook that requires memory to execute is a runbook that has stopped telling the truth** (§2). The next QE session reads it cold.

### Fixed 2026-08-04

`make up` before and `make down` after, with the reason stated inline so the pair is not later "tidied up"; the migration-reversibility command written out, since the checklist asked for it and named no command; and a note that an abort must be diagnosed before it is retried.

**Verified by the run that found it** — aborted as written, passed once the precondition was established: 5 stages, every guarantee held, 379 Security Invariants against the restarted stack.


### B-113 · Every claim audit refuses, on a commit from 2026-08-02 that can never be fixed

| | |
|---|---|
| **Module** | Repository governance history — `infra/certification-guard.py --audit-claims` |
| **Current assignee** | **none — not assignable.** The offending commit is 235 commits back on `main`, and rewriting it is ⚫ (`CLAUDE.md` §20e). **The product owner rules on the disposition** |
| **Severity** | 🟡 — wrong but survivable. `--audit-claims` is not a certification gate, so nothing is blocked. **What it costs is the audit itself** |
| **Status** | **`OPEN`** — reported, deliberately not fixed by QE |
| **Found** | 2026-08-04 by QE, running the audits after changing the guard |

**Steps to reproduce.**

```bash
python3 infra/certification-guard.py --audit-claims
```

**Expected.** `every one touches only ACTIVE_ASSIGNMENTS.md and BACKLOG.md.`

**Actual.**

```
REFUSED — 1 claim commit(s) carried more than a claim:
  · 9af1641  Claim TASK-004 — and why TASK-003 was not taken
      also changed docs/LANE_COORDINATION.md
```

`9af1641` is dated **2026-08-02** — the day the Task Claim Protocol was ratified. The lane recorded *why it skipped a task* in the coordination register within the same commit, which the protocol had just bounded to the two registers.

### Why QE is reporting this rather than fixing it

**Three routes exist and QE may take none of them.**

| | |
|---|---|
| **Rewrite the commit** | ⚫ — *"rewrite a dated record"*, and it is an ancestor of 235 promoted commits |
| **Baseline the audit past it** | **A gate quietly narrowed to stop it failing.** The authority QE has is *to make a documented gate runnable, never to make it pass* (§20e) |
| **Add a named historic exception** | Defensible, and **a governance decision** — it declares one past deviation permanently accepted, which is the product owner's to declare, not a lane's |

> **The real cost is that the audit can never pass.** A check with a permanent known failure stops being read: the next genuine violation arrives underneath a `REFUSED` everybody has learned to scroll past. **That is the same defect class as a guard that cannot fail** (§2) — inverted, and quieter, because nothing about it looks broken.

**What is *not* wrong.** The audit is correct — the commit really did carry a third file, and `RULE_RATIFIED_AT` already baselines the check properly at ratification. **Nothing here is a defect in the tool.**


### B-112 · The gatekeeper reported `Repository Ready` while a commit waited on `origin/integration`

| | |
|---|---|
| **Module** | Repository tooling — `infra/certification-guard.py` |
| **Current assignee** | **QE** — its own tooling |
| **Severity** | 🟠 — **a confident false negative on the question the gatekeeper exists to answer**, indistinguishable from the true answer |
| **Status** | **`FIXED`** 2026-08-04, with a regression test. **`VERIFIED` is another lane's** |
| **Found** | 2026-08-04 by QE, live, assessing Lane B's push to `integration` |

**Steps to reproduce.** In a clone whose `integration` is behind `origin/integration` — which is every clone that fetches without fast-forwarding:

```bash
git fetch origin                                  # moves origin/integration
python3 infra/certification-guard.py --next-cycle  # never touches it
```

**Expected.** Either the pending commits, or a refusal to answer.

**Actual.**

```
Repository Ready — `integration` == `main`. Nothing awaits certification.
```

`origin/integration` was one commit ahead at the time.

### Why it survived thirty-nine cycles

**Because the workflow that exposes it is the one QE only recently adopted.** The continuous gatekeeper loop **fetches every 60 seconds and fast-forwards nothing** — a local branch is moved only when a cycle begins. So between cycles the local ref is routinely behind by exactly the commits worth asking about, and the older workflow (fetch, then immediately ff, then ask) never produced the gap.

> **The staleness of a local ref was a hidden input** (`CLAUDE.md` §2). It changed the answer without appearing in the question, and it changed it toward the reassuring one — **the direction that gets acted on**. Had Lane B's commit been executable rather than a board update, QE would have concluded no cycle was needed and gone back to waiting.

### The fix

**Refuse for `--next-cycle`; note it for the audits**, and the asymmetry is the design rather than a compromise:

| | |
|---|---|
| **`--next-cycle` refuses** | It *decides*. An answer derived from stale refs is worthless, and its wrong answer is the comfortable one |
| **`--audit-claims` / `--audit-main` report the gap and proceed** | `integration` **moves while QE certifies, by design** (§20e). An audit that refused for staleness would be wrong exactly when it is most used — and would push QE to chase the head mid-cycle, which the Certification Snapshot forbids |

**Not by fetching inside the tool.** A gate that reaches the network fails offline and acquires a second hidden input in place of the first. It compares against what `origin` last returned and says so.

**Verified by watching it refuse**, on the real clone: reset `integration` back one commit → `REFUSED`, exit 1, with the fast-forward command named; restored → the real assessment, exit 0. Seven regression tests in `backend/tests/test_promotion_guard_stale_refs.py` build a real clone with a real remote, because the premise under test is a property of git — *a fetch leaves the local branch behind* — and that premise is asserted as its own control.


### B-111 · `tsc --noEmit` is in no gate QE runs, and `main` is red

| | |
|---|---|
| **Module** | Repository tooling — `backend/tests/certification/__main__.py`, and QE's stage 1 practice |
| **Current assignee** | **QE** — the gate set is QE's. **The type error itself is Lane A's** (below) |
| **Severity** | 🟠 — **`main` currently fails a check the Definition of Done requires of every lane**, and reached that state through a passing certification |
| **Status** | **`FIXED`** — the gate by QE, the fixture by Lane A, 2026-08-04. **`VERIFIED` is another lane's** |
| **Found** | 2026-08-04 by **Lane B** while rebasing. QE verified it independently on `main` |

**Steps to reproduce.** On `main` at `178697e`:

```bash
cd frontend && npx tsc --noEmit
```

**Expected.** Clean — `CLAUDE.md` §19 lists *"Type checking clean: `mypy --strict` · `tsc --noEmit`"* among the conditions for a slice to be implementation-complete.

**Actual.**

```
tests/components/triage-strip.test.tsx(89,5): error TS2741:
  Property 'last_observed_at' is missing in type '{ … }'
  but required in type 'AccountIdentity'.
```

### Fixed 2026-08-04, in both halves

**The gate — QE.** `tsc --noEmit` is now a **required** certification gate, so a record omitting it is a run that *cannot certify* rather than one that quietly skipped, and `make validate` runs it **before** the suite because it needs nothing and takes seconds.

**Verified by watching it refuse.** It failed on its first run against the red tree and passed after the fixture landed — a gate confirmed by a refusal rather than by a green.

**The fixture — Lane A.** One field, within an hour of the row. `main` type-checks again, and `b332aea69c12` is **the first certification record in this repository to carry a `tsc` gate.**

### Two gaps, and the second is the one that let it through

| | |
|---|---|
| **Certification does not run it** | `make certify` runs pytest, coverage, Security Invariants, `mypy`, `import-linter`, `smoke` and the scenario. **There is no frontend type check.** `smoke` builds the production image, which *does* type-check — but `.dockerignore` excludes `tests/`, so an error in a test file is invisible to it |
| **QE's stage 1 does not run it either** | QE validated Lane A's candidate with the vitest suite, `mypy` and `lint-imports`. **`tsc --noEmit` was never run**, so QE could not have caught what the lane missed |

> **A check named in the Definition of Done and absent from every gate is a check nobody performs.** The lane is asked for it, QE never verifies it, and certification cannot see it — so the only thing standing behind it is that a lane remembered.

### What is *not* true, and Lane B's framing deserves the correction

Lane B reported it as a **combination** defect: *"each branch type-checked cleanly alone… no lane gate can see it, because a lane gate runs on a lane branch."* **That class is real and worth watching** — it is [C-103](LANE_COORDINATION.md)'s neighbour.

**This instance is not one.** Both halves are Lane A's: `AccountIdentity.last_observed_at` was added in A4, and `triage-strip.test.tsx` was last written in `1e28f33` — SW-05a, **also Lane A**. The fixture predates the field, in the same lane's own branch. **Their own `tsc --noEmit` would have caught it**, which is exactly why §19 asks for it.

### The fix, in two parts

**Gate set — QE's.** Add `tsc --noEmit` to certification, and run it in stage 1 validation. It is seconds, it needs no database, and it is already the repository's stated standard.

**The type error — Lane A's.** One fixture missing one required field. **Not urgent for a lane's branch and urgent for `main`**, which is currently in a state the repository's own rules would reject.

> **Lane A's half is done, 2026-08-04.** `triage-strip.test.tsx`'s fixture now carries `last_observed_at`, set **newer than `observed_at`** rather than equal to it — the ordinary case is that a name was reported once and something else about the account has been reported since, and a fixture pinning both to the same instant would quietly stop exercising the difference. `tsc --noEmit` is clean; 1162 frontend tests pass. **No regression test is added because `tsc --noEmit` is the regression test** — the defect was never that the check failed, only that nothing ran it. **The gate half is QE's and the row stays theirs; `Status` is deliberately untouched.**

### B-110 · The promotion guard refuses any commit that adds a migration

| | |
|---|---|
| **Module** | Repository tooling — `infra/certification-guard.py` |
| **Current assignee** | **QE** |
| **Severity** | 🟡 — wrong but survivable. **It refuses a valid promotion**, and the operator must know to stand somewhere else |
| **Status** | **`FIXED`** — QE, 2026-08-04. **`VERIFIED` is another lane's** |
| **Found** | 2026-08-04, the first promotion since RE-03 to carry a migration |

**Steps to reproduce.** With `main` at migration head `0030` and a certified commit that adds `0031`:

```bash
git checkout main
python3 infra/certification-guard.py <the certified sha>
```

**Expected.** `CERTIFIED — <sha> may be promoted.`

**Actual.**

```
REFUSED — 9a112ae is certified against migration head 0031,
          and the repository is at 0030.
```

**Run the identical command from a tree at the certified commit and it passes.** Same SHA, same manifest, opposite verdict.

### Fixed 2026-08-04 — by narrowing which tree counts, not by removing the check

`_migration_head()` now takes the commit it is being asked about and reads **that commit's tree** via `git ls-tree`. With no argument it still globs the working directory, because `make certified` with no argument asks about `main`'s head and that *is* the checked-out tree.

**The expiry rule is untouched.** A record whose conditions have moved still refuses — and a test asserts the comparison survives, because deleting it would have been the easy way to stop the false refusals.

**Verified against the two commits that exposed it:** `9a112ae` reads `0031` and `a955016` reads `0037` from a single working tree, and both now certify from `main` where both previously refused. A control test asserts the two heads genuinely differ, because if they ever converge every other assertion passes while the defect is fully present.

### The mechanism

**The guard compares the record's conditions against the *checked-out tree*, not against the commit it is being asked about.** For every promotion that does not change the migration head those are the same thing, which is why this has never fired in thirty-odd cycles.

**A migration-bearing promotion breaks the equivalence**: `main` is by definition at the *old* head at the moment you ask, so the check refuses exactly the commits it should be scrutinising most carefully.

> **The condition itself is right and must stay.** *"A certification expires by derivation — add a migration and `is_certified` reads false"* is the rule that stops a stale record certifying a changed repository. **What is wrong is which tree it reads**, and the documented promotion sequence — `git checkout main && git merge --ff-only <sha>` — puts the operator in the one place where the answer is false.

### Why it is 🟡 rather than 🟠

**It refuses; it never wrongly permits.** A false REFUSED costs an operator a diagnosis. The inverse would be a false CERTIFIED, and nothing here can produce one.

**Worked around for this promotion by running the guard from `integration`**, which was already at the certified commit — and `--audit-main` confirmed the guarantee held afterwards across 200 commits.

### B-109 · The candidate pushes the repository below the coverage floor, and five new files have never been executed

| | |
|---|---|
| **Module** | `sales_engagement` · `workspace_tenancy` · `provider_platform` — the modules the slice introduced or extended |
| **Current assignee** | **Lane A** |
| **Severity** | 🟠 — **Blocking Quality Defect.** No customer behaviour is wrong; the coverage gate refuses the commit |
| **Status** | **`VERIFIED`** — QE, 2026-08-04. Coverage 94.27% → **95.10%**, floor met, no introduced file at 0%. Certified at `a955016` and promoted |
| **Found** | 2026-08-04, immediately after [B-107](#b-107) was fixed. **The suite itself is green** |

**Steps to reproduce.** On Lane A's candidate rebased onto `integration`, against a database at its own migration head:

```bash
cd backend && SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 uv run pytest --cov
```

**Expected.** `Required test coverage of 95.0% reached.`

**Actual.**

```
2973 passed
FAIL Required test coverage of 95.0% not reached. Total coverage: 94.27%
```

**Every test passes.** This is not a behaviour defect — it is 0.73 percentage points of floor, and the gate refuses the commit.

### Verified 2026-08-04 — coverage as a consequence, not a target

**Lane A closed it by testing what the seams own**, not by chasing a percentage. Their own commits say what each test asserts: *"which envelope fields it reads, that the workspace comes from the envelope rather than the payload, that it opens its own tenant-scoped session as the platform rather than as a person, and that a skipped outcome is not a failure."*

And in the slice whose only goal was a number: **"Every test writes to a copy of the prompt directory. The shipped manifest is never touched — a record of what was true then is not rewritten to pass a test."** That is `CLAUDE.md` §2 applied unprompted, where the easy version of the fix mutates the manifest and passes.

### Five files the slice introduced have never been executed by a test

```
  0%  modules/sales_engagement/evaluation/__main__.py        missing 24-110
  0%  modules/sales_engagement/evaluation/release.py         missing 45-130
  0%  modules/sales_engagement/infrastructure/model.py       missing 34-89
  0%  modules/provider_platform/interface/handlers.py        missing 21-89
  0%  modules/integrations/public/__init__.py                missing 14-21
```

**`CLAUDE.md` §19 names this exactly**: *"no file the slice introduced sits at 0%, and the slice does not push the repository under the floor."* Both halves are violated.

> **One of the five is Lane B's, and is fixed.** `modules/integrations/public/__init__.py` belongs to `integrations`, so it is that module's assignee's regardless of which row it was found in. **It was at 0% because nothing in the repository imports it** — its only intended consumer is whatever synchronizes through a connection, which [C-326](LANE_COORDINATION.md) decides — so the contract has been correct and unused since it was written. Now pinned by `tests/integrations/test_public_contract.py`: the five published names, that none of them is a use case or names where credentials live, and that importing the contract reaches neither this module's infrastructure nor any other module. **A contract with no consumer is the one nothing else would notice drifting.** *Recorded by Lane B, 2026-08-04; the row and its other four files remain Lane A's.*

### And the largest single contributors below 80%

| | |
|---|---|
| **43%** | `modules/workspace_tenancy/infrastructure/query_service.py` — missing 71–191, **121 lines** |
| **49%** | `modules/workspace_tenancy/application/use_cases/invite_member.py` — missing 169–177 |
| **63–73%** | six `interface/router.py` files, `apps/worker/main.py`, `apps/worker/subscriptions.py` |

**`query_service.py` alone is the largest block of unexecuted lines in the candidate**, and Team Management is the capability it serves.

### Why the lane could have seen this in seconds

**`make coverage-debt` reads the data `pytest --cov` already wrote** — it runs nothing. `CLAUDE.md` §19 puts it in the lane's own Definition of Done, before handover:

> *"A coverage gap found at certification is the same gap that was visible to the lane in seconds. **Quality moves left because it is cheaper there, not because QE minds looking.**"*

### A QE finding from the same investigation

**`infra/coverage-debt.py` reported *"No coverage data"* while `backend/.coverage` existed and was 1.2 MB.** QE recorded the tool as broken.

**Corrected 2026-08-04, same day.** The tool was not broken. The same command succeeded minutes later — its `coverage json` subprocess had failed transiently under memory pressure, and **every failure inside the reader collapsed into one message advising *"run the suite"***. That is correct for exactly one cause and misleading for the rest.

> **It answered *five minutes of suite* to a problem that was not the suite.** A lane following that advice would have run it twice and learned nothing — and would reasonably conclude the coverage gap was not theirs.

**Fixed by making it say which failure occurred**, and by refusing to advise a re-run when the data is present. Four tests assert the distinction, including that the reader returns a reason rather than `None` — because `None` carries no information and every caller then invents the same wrong one.

### B-108 · The production image cannot build, because a root config imports a directory the image does not ship

| | |
|---|---|
| **Module** | Frontend — `frontend/playwright.config.ts`, `frontend/tsconfig.json` |
| **Current assignee** | **Lane B** — the lane that wrote it |
| **Severity** | 🟠 — **Blocking Quality Defect.** No customer behaviour is wrong; **no production image can be built** |
| **Status** | **`VERIFIED`** — QE, 2026-08-04. All four production images build; `tsc --noEmit` clean; certified at `9a112ae` and promoted to `main` |
| **Found** | 2026-08-04, at `make smoke` stage 1 of 24. **Every other gate on this candidate passed** |

**Steps to reproduce.** On Lane B's candidate, rebased onto `integration`:

```bash
docker compose --env-file infra/.env.prod-local -f infra/docker-compose.prod.yml build
```

**Expected.** Images build.

**Actual.**

```
Type error: Cannot find module './tests/e2e/fixtures/environment'
           or its corresponding type declarations.
ERROR: process "/bin/sh -c npm run build" did not complete successfully: exit code: 1
```

### The mechanism, and why nothing else could see it

```
frontend/playwright.config.ts:3
import { browserEnvironment, resolveAppUrl } from './tests/e2e/fixtures/environment';

frontend/.dockerignore:6
tests/

frontend/tsconfig.json:21
"include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"]
"exclude": ["node_modules", "tests/e2e"]
```

**Three correct decisions that are wrong together.** `tests/` is excluded from the image because a production image has no business shipping tests. `playwright.config.ts` lives at the root because that is where Playwright looks for it. `tsconfig` includes `**/*.ts` because it should. **So the image contains a root config that imports a directory the image does not contain**, and `next build` type-checks it.

**`tsconfig` excludes `tests/e2e` but not `playwright.config.ts`** — the config *importing* the excluded directory is itself included, which is why local `tsc` resolves it (the files are on disk) and the image does not (they are not).

> **This is precisely the class `make smoke` exists for.** The candidate passed **2783 backend tests, 899 frontend tests, 372 Security Invariants, `mypy --strict` over 635 files and 34 import contracts** — and cannot produce a deployable image. **Only the gate that builds the production images sees it**, which is why that gate is not optional ([B-013](#b-013) was the same shape).

### A second, independent defect in the same candidate

**`tsc --noEmit` fails: 15 errors, all in `frontend/tests/unit/acquisition-exchange.test.ts`** — `TS2532: Object is possibly 'undefined'`.

This is a gate the lane owns and runs itself (`CLAUDE.md` §19 — *type checking clean: `mypy --strict` · `tsc --noEmit`*). It is unrelated to the build failure above and must be fixed separately.

### The fix is Lane B's to choose

QE names the constraint, not the design. Any of these satisfies it: exclude `playwright.config.ts` from `tsconfig`'s `include`; move the fixture out of `tests/`; or keep the config free of imports from an excluded directory. **What must hold is that the production image builds without shipping tests.**

**No regression test is required.** `make smoke` is the regression test, and it caught this on the first run.

### The branch is growing on a base that cannot certify

**Recorded 2026-08-04, as an observation rather than a second defect.** Lane B has pushed three further slices since this was raised — the branch is **40 commits** ahead of `integration` with two blocking gates still failing.

---

## Fix — Lane B, 2026-08-04

**The image no longer contains the config**, rather than the config no longer being type-checked. `frontend/.dockerignore` excludes `playwright.config.ts` beside the `tests/` it configures.

**Excluding it from `tsconfig` was the other obvious fix and is worse.** That file has real imports and real logic, and removing it from `tsc --noEmit` would mean nothing ever checks it again — trading a build failure for a silent one. **It is absent from the image because nothing in the image runs it**, which is a true statement rather than a workaround, and the local gate is unchanged.

**Verified by building the image, not by reading the diff:**

```
docker compose -f infra/docker-compose.prod.yml build frontend
  →  naming to docker.io/library/signora-prod-frontend:latest
     Image signora-prod-frontend  Built
```

### The second defect was already fixed, and the report could not know

**`tsc --noEmit` is clean** — 0 errors, verified on the rebased branch. The 15 `TS2532` errors were real at `b327b2c` and were fixed at `db1fb78`, in the slice that added the `only()` and `required()` helpers, **before this row was visible to this lane.**

> **That is [C-102](LANE_COORDINATION.md) exactly, from the other side.** QE measured a defect this lane had already repaired and could not have known it, because the report and the repair were on branches neither could see. **Both halves were correct and neither was reachable** — and this lane went on to push four more slices past a blocking image failure it also could not see.

**Found by polling rather than by being told.** This lane fetched, compared branches and read `integration`'s registers; nothing pushed the report to it. **That is the workflow gap C-102 names, and this row is a second instance of it.**

**That is within the model** (*a lane never idles waiting for validation*, `CLAUDE.md` §20e), and QE is not asking the lane to stop. What is worth stating is the arithmetic: **every new commit lands on a base that cannot produce a deployable image**, and both failing gates are the lane's own, runnable in under two minutes:

```bash
npx tsc --noEmit
docker compose --env-file infra/.env.prod-local -f infra/docker-compose.prod.yml build
```

**The defect is not getting harder to fix; it is getting further from the top of the branch.**

### B-107 · Ten tests in the A7 slice have never passed, and they hang the suite for everyone

| | |
|---|---|
| **Module** | `provider_platform` — `backend/tests/provider_platform/test_last_looked.py` |
| **Current assignee** | **Lane A** — the module's current assignee, and the lane that wrote it |
| **Severity** | 🟠 — **Blocking Quality Defect.** No customer behaviour is wrong; the repository cannot certify |
| **Status** | **`FIXED`** — Lane A, 2026-08-04. **`VERIFIED` by QE**: their rebased candidate ran 2973 tests green with no errors in that file |
| **Found** | 2026-08-04, validating Lane A's 55-commit candidate. **Reproducible on the first attempt and every attempt since** |

**Steps to reproduce.** On `lane-a-product-surface` at `c70b32c`:

```bash
cd backend && SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 uv run pytest tests/provider_platform/test_last_looked.py -q
```

**Expected.** 10 passed.

**Actual.** `10 errors in 1.19s`. **Every test in the file errors — none has ever passed.**

### Verified 2026-08-04 — and the fix exceeded the request

QE asked for a marker removed. **Lane A removed it and made the objection executable**: `backend/tests/test_async_test_convention.py` refuses `anyio` in any test file, placed at the repository root because the rule is about the repository's async convention rather than the one file that had the defect. **Verified load-bearing by re-adding the marker**, with a second test asserting the glob matches something.

> QE reported that `E` looks like `.` in a `-q` run as an *explanation* for how ten never-passing tests survived. **Lane A turned the explanation into a check.**

### The mechanism, in one line

```python
backend/tests/provider_platform/test_last_looked.py:145
pytestmark = pytest.mark.anyio
```

**This is the only file in the repository that touches `anyio`**, and `backend/pyproject.toml` says why that matters in its own comment:

```toml
asyncio_mode = "auto"
# Session-scoped loop for both tests and fixtures: the integration suite
# shares session-scoped asyncpg engines, and asyncpg connections cannot be
# used across event loops.
asyncio_default_fixture_loop_scope = "session"
asyncio_default_test_loop_scope = "session"
```

`pytest.mark.anyio` makes **anyio** drive the test on **its own loop**, while every fixture the test depends on was built on the session loop. The result is the error asyncpg raises when exactly that happens:

```
RuntimeError: Task <Task pending name='Task-12003' …> got Future <Future pending …>
attached to a different loop
```

### Why it is a *blocking* defect rather than ten failing tests

**It does not merely fail — it stalls the whole run.** Three full-suite attempts stopped at **68%**, each at the same point, with `E.E.E.E.E.E..` and then no further progress. A suite that normally completes in ~4 minutes ran for 25 without finishing. **Nothing else in the candidate is at fault**: deselecting this one file gives

```
2922 passed, 10 deselected, in 308s
```

So the candidate is otherwise green — `mypy --strict` clean over 673 files, `lint-imports` 35/35, frontend 945 passing, reachability 0 unreachable.

### Why it reached `IN VALIDATION`

**Not carelessness, and worth recording because QE made the same mistake reading it.** `E` markers in a `-q` run are visually near-identical to `.` — QE's own first pass reported this candidate as green on everything but the backend suite, having read past the same characters. **Anything that hides a failure behind a character that looks like success will be missed by whoever is going fastest**, which on a 55-commit candidate is everybody.

### The fix

**Remove the `anyio` marker.** The repository's convention is `asyncio_mode = "auto"` — an `async def` test needs no marker at all, which is why no other file has one. The tests themselves look correct; only the driver is wrong.

**QE does not fix it** (`CLAUDE.md` §20e — QE reports, feature lanes fix). **A regression test is not required**: the file *is* the test, and it passing is the proof.

### B-106 · A certification gate read a variable nobody declared, and two runs of one commit disagreed

| | |
|---|---|
| **Module** | Repository tooling — `backend/tests/integration/test_migration_runner.py`, `TestConcurrencySafety` |
| **Current assignee** | **QE** — a test-only defect in a repository-wide suite |
| **Severity** | 🟠 — **the certification gate was not reproducible.** No customer-visible behaviour is wrong |
| **Status** | **`FIXED`** — QE, 2026-08-03, with the input declared in the test. **`VERIFIED` is another lane's** |
| **Found** | 2026-08-03, by QE, running the full suite at `68a643e` — the commit whose ancestor `909374a` had certified hours earlier |

**Steps to reproduce.** At `68a643e`, in a shell with no `SIGNORA_DATABASE_URL` exported:

```bash
cd backend && SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 uv run pytest tests/integration/test_migration_runner.py
```

**Expected.** 7 passed — the result `make certify` recorded for this tree.

**Actual.** `3 failed, 4 passed`, all three with `RuntimeError: SIGNORA_DATABASE_URL must be set to run migrations`. Export the variable and the same command gives `7 passed`. **The commit did not change; the shell did.**

### The mechanism

`migrations/env.py` reads `os.environ["SIGNORA_DATABASE_URL"]` directly. It cannot see the `Settings` object these tests construct, and nothing bridged the two — so the tests named a database in `_settings(DEFAULT_ADMIN_DATABASE_URL)` while Alembic read whichever one the operator's shell happened to hold, **or failed outright if it held none.**

### Why this is worse than a flaky test

**`CLAUDE.md` §2: hidden inputs are architecture defects**, because they make the same declared inputs produce different results. In a certification gate that is not an inconvenience — it is the guarantee failing quietly:

> The run that certified `909374a` and the run that reproduced it were measuring different things, and **nothing in the record said so.** A certification is *"this commit satisfied these guarantees under these conditions"*, and one of the conditions was an environment variable nobody wrote down.

**[B-022](#b-022--make-certify-inherits-the-database-environment-and-silently-measures-less-when-it-is-absent) predicted exactly this class** — *"`make certify` inherits the database environment, and silently measures less when it is absent"* — and stayed open. This is the first time the prediction was observed rather than reasoned about, and the direction is the alarming one: **the certified run was the lucky one.**

### The fix

An autouse fixture on `TestConcurrencySafety` sets `SIGNORA_DATABASE_URL` to the value the tests already name, so the environment and the settings cannot disagree. **Verified by removing the variable from the environment entirely** — `env -u SIGNORA_DATABASE_URL … 7 passed` — which is the only run that proves the dependency is gone rather than merely satisfied.

**This does not close B-022.** That row is about `make certify` inheriting an environment at large; this is one gate inside it, found and closed. The general remedy — a certification run that declares its whole environment — remains open, and this is the evidence for prioritising it.

### B-105 · The documented quickstart cannot work: nothing loads `frontend/.env.local` for the setup scripts

| | |
|---|---|
| **Module** | Frontend tooling — `frontend/scripts/auth-migrate.ts`, `frontend/scripts/demo-users.ts`, and the `demo-prepare` target |
| **Current assignee** | **QE**, joined from [C-216](LANE_COORDINATION.md). ⚠️ **Cross-referenced 2026-08-05 — this bug and that coordination item are the same defect, open in two registers.** C-216 — *"the setup scripts do not load `.env.local`, and fall back silently"* — records **`owner: QE`**, on the grounds that [`RUNNING.md`](RUNNING.md) and the setup scripts are QE's. **This row read `unassigned` because it reasoned from the *frontend foundation*, and the defect is in the scripts rather than in the foundation they configure.** **Not closed as a duplicate**: a bug row and a coordination item answer different questions, and B-105 is where the reproduction lives. **QE decides whether to close one** |
| **Severity** | 🟠 — **the documented first-run path fails**, and it is the path every new environment takes |
| **Status** | **`OPEN`** — found by QE while building `make review`, 2026-08-03 |
| **Found** | 2026-08-03, on a workstation with no `frontend/.env.local`, following `docs/RUNNING.md` exactly |

**Steps to reproduce.** On a clean checkout: `cp frontend/.env.example frontend/.env.local`, edit in the two required values, then `make demo`.

**Expected.** The Playground is seeded and the product is reviewable.

**Actual.** It stops at `npm run auth:migrate` with

```
SIGNORA_AUTH_DATABASE_URL is required and is not set. It has no default:
guessing one would connect this tier to somebody else's environment.
```

**Next.js loads `frontend/.env.local`; `tsx` does not.** `next dev` and `next build` read the file through Next's own loader, so the application tier has always seen it. `npm run auth:migrate` and `npm run demo:users` are plain `tsx` scripts run from `make`, and nothing in that path loads it — not `tsx`, not npm, not make.

**Why it appeared now, and why that is the good news.** It is not new. Before [B-104](#b-104--the-auth-tier-had-one-database-for-every-environment-and-a-signing-secret-in-the-repository) removed the fallbacks, these scripts silently used the shared `signora` database whatever the operator had configured — so the quickstart *appeared* to work while writing to the wrong place. **Removing the fallback did not break this; it revealed it.** That is the fallback's whole indictment: a defect that fails loudly today was a silent data-placement bug for as long as the default existed.

**Not fixed here, deliberately.** `infra/review.py` loads the file itself for the subprocess it starts, which makes `make review` work. **That is a launcher's workaround, not the fix** — a second env-loading mechanism hidden inside one command is how two environments start disagreeing about what configuration means, and `make demo` is still broken for anyone running it directly.

**The fix belongs in one place.** Either the two scripts load the file (Node's `--env-file`, or the loader Next already uses), or `demo-prepare` exports it before invoking them. Whichever is chosen, `infra/review.py`'s `_dotenv` should be deleted in the same change — it exists only because this is open.

### B-104 · The auth tier had one database for every environment, and a signing secret in the repository

| | |
|---|---|
| **Module** | Frontend foundation — `frontend/lib/auth/config.ts` (🔒 §20c) |
| **Current assignee** | **QE** ([ADR-0100](architecture/adr/0100-delegated-dependency-rulings.md) R-4) |
| **Severity** | 🟠 — **customer data written to the wrong database**, and a committed signing secret that activates silently |
| **Status** | **`FIXED`** — QE, 2026-08-03. **`VERIFIED` is another lane's** |
| **Found** | 2026-08-03, **by the product owner**, whose review session wrote Better Auth users into another environment's database |

**Steps to reproduce.** Follow the README: `cp frontend/.env.example frontend/.env.local`, then sign up. **That is the whole reproduction.**

**Expected.** A review session writes to the review environment.

**Actual.** It writes to the **shared `signora`** database — as does every lane, QE, and anything else that copied the example unedited.

### Two mechanisms, and the second is worse

**1 · `required()` was a lie.** It took an optional `fallback`, and **with one supplied it could never throw**:

```ts
function required(name: string, fallback?: string): string {
  const value = process.env[name] ?? fallback;   // never undefined
  if (!value) throw new Error(...);              // unreachable
  return value;
}
```

Six values used it. A reader seeing `required('BETTER_AUTH_SECRET', …)` reasonably believes it is required. **It was not.**

**2 · The fallbacks pointed at shared resources.**

| Value | Silent default | Consequence |
|---|---|---|
| `SIGNORA_AUTH_DATABASE_URL` | the **shared `signora`** | **The incident.** Users written to another environment |
| `BETTER_AUTH_SECRET` | `local-dev-secret-change-me` | **A signing secret committed to this repository.** Every clone using it mints JWTs any other clone can forge — §13: *no credential is ever hardcoded or committed* |

**And `.env.example` shipped the same shared values**, so following the README's own instruction produced the defect. **The documentation and the code agreed, and both were wrong.**

### Why nothing caught it

**`RUNNING.md` allocates per-lane ports, PostgreSQL databases and Redis indices — for the backend only.** `SIGNORA_AUTH_DATABASE_URL` appears in it **zero times**. The backend tier has environment isolation; **the frontend auth tier never did**, and no check compared them.

### The fix

**`required()` no longer accepts a fallback and genuinely refuses.** `developmentDefault()` is a separate, named function for values whose default is harmless — **the distinction is now visible at the call site.**

> **The asymmetry that decides which is which:** a URL with a wrong default fails **loudly and immediately**; a database with a wrong default fails **silently and permanently**. Ports keep their defaults so a first clone still runs. The database and the secret do not.

**Four of the frontend's own tests failed on this change** — they had been exercising the defaults without meaning to. **Their setup was fixed, not the guard**: the defaults were the defect.

**Permitted under §20c** as a security issue and a production defect, and QE's to fix under R-4.

### Three more defects, found only because the fallbacks stopped hiding them

**Removing the fallbacks failed the build. Chasing that failure is what exposed the rest** — and every one had been live since M1.5.

**1 · The build was connecting to a database.** **All five authenticated pages were statically prerendered**, every one reads a session, and reading a session opens the auth pool. So `npm run build` opened the **shared `signora`** database to render signed-in screens. That is §20b inverted: configuration resolved at *build* time into an artifact that must read it at *boot*. Fixed by `export const dynamic = 'force-dynamic'` on `(app)/layout.tsx` — **the segment, so five pages cannot each forget it.**

**2 · A comment asserting the opposite of what the code did.** `app/api/auth/[...all]/route.ts` read *"**Never evaluated at build time.**"* directly above `toNextJsHandler(auth())` **at module scope**, which is precisely build-time evaluation. `force-dynamic` governs *rendering*; Next.js still imports every route module during *Collecting page data*. **Decorative Logic (§2) with a false claim beside it.** The handler is now built on first request.

**3 · The API client loaded the entire auth config for one URL.** `apiBaseUrl` is not an authentication concern, and reaching it through `loadAuthConfig()` made **every server-rendered page depend on the auth database and the signing secret it never uses.** Now read directly.

### The design changed mid-fix, and the second shape is the right one

**The first fix required both values at config-*read* time.** It failed the build, and after patching three call sites it was clearly whack-a-mole — the next page added would reintroduce it.

> **A build legitimately has no environment.** Reading configuration into a struct harms nobody; **connecting and signing** are what matter.

Both values are now **getters** — required at point of *use*, not point of *read*. A prerendered page reading `passwordEnabled` never touches them; `getAuthPool()` and `createAuth()` always do. **That fixes the class rather than the instances.**

**Two axes, and the second is what the first fix got wrong:**

| | |
|---|---|
| **Convenience vs trust** | A port default is convenience. A database or secret default is trust |
| **Read vs use** | Reading a secret into a struct is harmless. **Using it to connect or sign is the boundary** |

**What this does not fix.** There is still **no `signora_review` database and no `make review`** — the product owner has no environment to be isolated *into*. That is the assignment this bug was found inside, and it is not yet built.

**And one of the same class remains open:** `signora_platform/settings.py` declares `redis_url: RedisDsn = RedisDsn("redis://localhost:6379/0")` while [`RUNNING.md`](RUNNING.md) allocates an index per lane and states *"no lane invents ports; no lane shares a database."* **The allocation table exists and the code does not require it to be used.** Redis carries the ARQ queue and the outbox relay, so two environments on index 0 means **one environment's workers consume the other's jobs** — cross-environment *execution*, not merely storage. Tracked as part of the Human Review Environment work.


---

### Closing the `BETTER_AUTH_SECRET` investigation — 2026-08-03

**An unresolved question needs an owner more than it needs an answer.** The operational scope of the committed signing secret could not be determined, and it was never going to become determinable by waiting. Leaving it open indefinitely would mean the repository carried an unowned uncertainty — which is worse than a recorded one, because nothing forces a reader to notice it.

**So the operational investigation is closed here, on the product owner's direction, with the uncertainty stated rather than resolved.**

| | |
|---|---|
| **Known incident** | `BETTER_AUTH_SECRET=local-dev-secret-change-me` was committed in `frontend/.env.example` and was **live by default** — `required()` took a fallback and, with one supplied, could never throw. Any clone that copied the example unedited signed sessions with a value every other clone also held |
| **Deployment scope** | **Unknown, and it will stay unknown.** No deployed environment exists ([ADR-0027](architecture/adr/0027-local-first-development.md)) and no telemetry records which clones ran with the default. The absence of evidence is not evidence here |
| **Assumption adopted** | **Worst case.** The value is treated as public and permanently compromised. Not *"probably only local"* — the product owner's standing instruction is to assume the worst until disproven, and nothing disproves it |
| **Mitigation completed** | The fallback is gone: `required()` no longer accepts one, so the tier **refuses to start** rather than signing with a shared value. The example file now carries an explicit warning naming the value as committed and telling the reader to generate their own. Verified by the tier failing to start with the variable unset |
| **Monitoring retained** | The committed string stays in `.env.example` **deliberately**, marked, so a `grep` for it identifies any environment still using it. Removing it would erase the only detection mechanism there is. If a deployed environment ever exists, the secret is rotated as a precondition of deploying — not as a follow-up |

> **What this closes and what it does not.** It closes the *investigation* — there is no further finding to be had from asking. It does not close the *risk*: the worst-case assumption remains in force, and any future deployment inherits it as a rotation requirement rather than a resolved question.

### B-103 · An internal invariant tells a customer their request was refused

| | |
|---|---|
| **Module** | `opportunity_engine` · `ai_research_engine` — **the same shape in both, arrived at independently** |
| **Current assignee** | **Unassigned.** Neither module has a current lane; whoever is next assigned fixes it |
| **Severity** | 🟠 — **the product tells a customer something false about their own request** |
| **Status** | **`FIXED` in `ai_research_engine` — Lane A**, 2026-08-05. **`OPEN` in `opportunity_engine`**, which is Lane B's and untouched here. **The row stays open** until both halves are closed; only QE closes it. `ResearchRequestInvariantError` splits the invariant from the refusal and maps to `500 research_request_invalid`; the 422 refusal is unchanged, as the row requires. Regression test: `tests/ai_research_engine/test_error_attribution.py`. **Not generalised into a repository-wide invariant** — one asserted from here would fail Lane B's build for a half they have not taken (§20e) |
| **Found** | 2026-08-03, by QE, re-validating [C-009](LANE_COORDINATION.md) against current code |

**Steps to reproduce.** Trigger any condition that raises a domain invariant rather than a domain refusal — for example a negative generation or a negative state sequence.

**Expected.** A `5xx`. Nobody's request can cause a negative sequence number; it is a bug in Signora.

**Actual.** `422 transition_refused` — *your request was refused* — because one exception class carries both meanings:

| Module | The raise | What the customer is told |
|---|---|---|
| `opportunity_engine` | `OpportunityError("an opportunity's generation cannot be negative.")` | `422 transition_refused` |
| `ai_research_engine` | `ResearchRequestError("a state's sequence cannot be negative.")` | `422 research_request_refused` |

**`workspace_tenancy` is *not* affected** — `InvalidWorkspaceNameError` genuinely is bad customer input, and 422 is correct there. **The defect is mixing two meanings in one class, not the status code itself.**

**Why this is 🟠 and not cosmetic.** `CLAUDE.md` §10 states it directly: *"An error must never name a component that was not involved… an incorrect attribution is worse than none, because it misdirects the investigation."* Here the misdirection points at **the customer**. A seller is told their transition was refused; support looks at their data; the bug is in ours.

### The finding that matters more than the defect

**[C-009](LANE_COORDINATION.md) has been open five cycles as a frozen-platform change under §20a, requiring an RFC and a product-owner ruling. It is none of those things.**

`opportunity_engine/interface/errors.py` documents the mechanism in its own comment:

> *"handler lookup walks the exception's **MRO**, so the two rows above still win for their own types."*

**A module can already map an invariant separately from a refusal.** It needs a second exception class and one more row in its own `ERROR_MAPPING` — **entirely inside the module, no platform change, no RFC, no decision.**

**The fix, for whoever takes it.** Split the hierarchy so meaning is in the type: a refusal the customer caused, and an invariant they could not. Map the invariant to `500` with a neutral code. **Do not widen the existing mapping** — a refusal must stay 422, because those messages are written to be read and that is the point of the module.

**Add a regression test that a domain invariant does not surface as a 4xx.** Without it the next class added re-merges them.

| | |
|---|---|
| **Module** | None — `docs/LANE_COORDINATION.md`, a shared register ([C-010](LANE_COORDINATION.md)) |
| **Current assignee** | **QE** |
| **Severity** | 🟠 — **the register that exists to stop lanes encoding contradictory assumptions was itself internally contradictory** |
| **Status** | **`FIXED`** — QE, 2026-08-03. Register repaired; `conflict_markers` added to `infra/registers.py` and wired into `state-check`. **`VERIFIED` is another lane's** |
| **Found** | 2026-08-03, by QE, performing the Dependency Health Review |

**Steps to reproduce.** Read `docs/LANE_COORDINATION.md` on `main` at `d39b136`, line 118.

**Expected.** A register whose index agrees with its contents.

**Actual.**

```
>>>>>>> 603a077 (ADR-0040 proposed — Notifications answers a different question from Attention)
```

**A conflict marker, committed, promoted, and carried through several certification cycles.** Its damage was not cosmetic:

| | |
|---|---|
| **One row stranded** | `C-027` sat **outside** the table it belonged to, so the index under-reported what was waiting |
| **Two rows duplicated** | `C-024` and `C-025` each appeared **twice, with contradictory statuses** — `C-025` read `ANSWERED — all four decisions taken` in one row and `OPEN` in the other |
| **The table split** | A blank line broke it into two, so any tool reading it as one table saw half |

**Why nothing caught it.** `malformed_tables` was built for the residue of a split section and looks for a separator with no header above it. **A `>>>>>>>` line inside a table is not a table separator**, so the check that was closest to this defect could not see it. Every other gate reads code.

**This is the same class as [B-100](#b-100--a-lanes-rebase-silently-reverted-the-execution-board-by-seven-cycles-and-every-gate-passed), one week and one file apart** — [ADR-0039](architecture/adr/0039-release-engineering-model.md) RC-4: *the registers are a multi-writer database written in markdown*. **Third instance of the predicted class.**

**The fix.** `conflict_markers()` in `infra/registers.py`, checked by `state-check` across all four registers. **`=======` is matched exactly rather than as a prefix**, so a setext heading underline does not fire — with the one genuine false positive (a seven-character underline) asserted in the test rather than hidden, so nobody silences it later.

**What it does not fix.** The register is still hand-merged, so the *next* corruption will be a different shape. **RC-4's actual answer is not to store multi-writer state in markdown**, and that remains ADR-0039's to propose and the product owner's to schedule.

### B-101 · The KPI block counted nine bug rows twice, under a banner promising nothing was typed by hand

| | |
|---|---|
| **Module** | None — `infra/kpi.py`, governance tooling ([C-010](LANE_COORDINATION.md)) |
| **Current assignee** | **QE** |
| **Severity** | 🟠 — **a published figure that was wrong in the direction of looking healthier**, in the one table that advertises itself as machine-measured |
| **Status** | **`FIXED`** — QE, 2026-08-02. `BugRow.state` added to `infra/registers.py`; the four buckets now sum to the row count. **`VERIFIED` is another lane's** |
| **Found** | 2026-08-02, by QE, auditing `PROJECT_STATUS.md` §4 for drift |

**Steps to reproduce.** `make kpi` against any register where a row records its fix and names the state it has not yet reached — the repository's own convention, e.g. *"**`FIXED`** — Lane B, 2026-08-02. **`VERIFIED` is QE's to set**"*.

**Expected.** Each row counted once. The four buckets sum to the number of rows.

**Actual.** `register_kpis` substring-matched the whole status cell:

```python
fixed    = sum(1 for r in rows if "FIXED"    in r.status)
verified = sum(1 for r in rows if "VERIFIED" in r.status)
```

**Nine rows contained both words**, so `13 open · 17 fixed · 11 verified · 1 won't fix` totalled **42 against 33 rows.**

**The banner is what makes it 🟠 rather than 🟡.** The block carries *"`make kpi` writes this block. It is regenerated at every Closeout and **never edited by hand** — a number somebody typed is a number that stops being true quietly."* **That claim is true and was the reason to trust the wrong figure.** A hand-typed number invites checking; a machine-generated one does not.

**Two things were found underneath it, and both matter more than the miscount.**

**1 · Three rows were verified in name only.** [B-009](#b-009--make-smoke-has-not-run-since-the-platform-was-frozen), [B-013](#b-013--the-worker-and-the-relay-cannot-start-from-a-production-image) and [B-014](#b-014--a-closeout-commit-may-touch-infra-and-change-what-certification-means) had a verification note appended to a cell that still opened with `FIXED`. Corrected to open with `VERIFIED`.

**2 · QE's own audit used the same broken precedence the tool did.** I counted a row as `VERIFIED` if the word appeared anywhere, and reported **11 verified** in the cycle-23 summary. **The true figure was 5.** I also reported the severity counts as wrong when they were correct — `bug_rows` deliberately takes the *first* marker in a conditional cell, and my check took 🔴 wherever it appeared. **Both of my numbers were wrong in the same direction as the tool's, because they made the same assumption.**

**The fix is the rule the module already applied to severity, extended to status.** `BugRow.state` returns the **first** lifecycle token in the cell; the rest is commentary, and a row that *names* its next state has not reached it. It lives in `registers.py` because that module exists precisely so `state-check` and `kpi` cannot disagree — the same defect class, one layer up, which is why it belongs there rather than in `kpi.py`.

**Not affected:** `state-check`'s promotion gate. `unresolved` reads the cell's *prefix* and was always correct, so **no 🔴 was ever mis-cleared** — verified across all 33 rows.

### B-100 · A lane's rebase silently reverted the execution board by seven cycles, and every gate passed

| | |
|---|---|
| **Module** | None — `docs/ACTIVE_ASSIGNMENTS.md`, a shared register |
| **Current assignee** | **QE** — the mechanism is QE's, and the repaired rows were QE's own |
| **Severity** | 🟠 — **the repository asserted a state that was seven cycles stale**, and nothing in the pipeline could see it |
| **Status** | **`FIXED`** — QE, 2026-08-02. Board repaired at integration; `state-check` rule 5g added. **`VERIFIED` is another lane's** |
| **Found** | 2026-08-02, by QE, validating Lane A's branch at `cb5cd33` |

**Steps to reproduce.** Rebase a long-lived lane branch onto an `integration` that QE has written a Closeout commit into. Resolve the inevitable conflict in `ACTIVE_ASSIGNMENTS.md` by keeping the branch's side — which is the natural resolution, because the rest of the file *is* the lane's own rows.

**Expected.** The board describes the promoted repository.

**Actual.** The board went **backwards**:

| | before the rebase | after |
|---|---|---|
| Header | `2262bb5` — cycle 22 | **`3451f8b`** |
| QE's row | *Cycle 22 promoted. 22 pinned, 18 certified* | **Cycle 15 promoted. 15 of 15 certified** |
| Completed | 11 rows | **9** — `2262bb5` and `e5a266d` deleted |
| Lane B | one current row | **two rows describing B-023 and B-024**, both fixed and promoted |

**Nothing was careless, and that is the finding.** Lane A resolved a conflict in a file that is mostly its own rows by keeping its own version — the resolution a careful engineer makes. **The two rows it destroyed were QE's, in the same table, and git had no way to say so.**

**Every gate passed.** `state-check` ran clean on the branch: it verifies `PROJECT_STATUS.md` names a commit reachable from `main`, and that file was untouched. **No check read the board's own header**, so a seven-cycle regression was invisible to a repository whose whole discipline is that its records tell the truth (§2).

**This is [ADR-0039](architecture/adr/0039-release-engineering-model.md) RC-2 arriving in the wild** — *fast-forward-only × shared mutable files ⇒ a mandatory rebase that is lossy by construction* — and it is the **second** instance after [B-018](#b-018--lane-as-branch-carries-two-of-lane-bs-pre-rebase-commits-and-will-not-fast-forward). RC-2 predicted the class before it happened twice.

**The fix, in two parts.** The rows are repaired at integration, which is QE's job at Closeout anyway. **The durable half is `state-check` rule 5g**: the board's `Current — as of` SHA must be reachable from `main` and must not name a commit older than the one `PROJECT_STATUS.md` names. A stale board is now a finding rather than a thing somebody happens to notice.

**What it does not fix.** Rule 5g catches the *header*. A lane that reverted only a row would still pass — the header is a proxy, not a proof. **Recorded rather than solved**: the real answer is RC-2's, which is to stop storing derivable state in a hand-merged file, and that is ADR-0039's to propose and the product owner's to schedule.

### B-321 · `doc-drift` names one document per module, and two of those names are stale

| | |
|---|---|
| **Module** | Repository tooling — `infra/doc-drift.py` |
| **Current assignee** | **QE** — repository tooling and governance checks |
| **Severity** | 🟡 — **it reports two findings that can never be cleared**, which is how a check stops being read |
| **Status** | **`OPEN`** — reported by Lane B, **not fixed.** `infra/` decides whether a gate passes, so changing one is a slice ([B-014](#b-014--a-closeout-commit-changed-a-certification-gate)) |
| **Found** | 2026-08-03, by Lane B, **while doing exactly what the check is for** — verifying Epic A's documentation was accurate rather than asserting it |

**Steps to reproduce.** Change anything in `modules/provider_normalization/` or `modules/commercial_profile/`, document it correctly, and run `python3 infra/doc-drift.py`.

**Expected.** Correct documentation clears the finding.

**Actual.** It cannot. The map is one file per module and two entries point at documents that are no longer where those modules' design lives:

| Module | `doc-drift` expects | Where the documentation actually is |
|---|---|---|
| `provider_normalization` | `34-knowledge-contract.md` | **`05-module-dependencies.md`** — the `ClaimReader` port and its methods, which is what a change to that module usually is |
| `commercial_profile` | `adr/0035-commercial-profile.md` | **`40-commercial-profile.md`** (the module design doc) and **`adr/0041-icp-aggregate.md`** (its newest decision) |

**Both fired against this branch while the correct documents were updated in the same commits** — `05` gained both new `ClaimReader` methods, `40` gained 62 lines and `0041` is a 541-line ADR written by the slice that changed the module.

**The check is right about everything else, which is the evidence it works.** `observation_engine` → `23-observation-engine.md` is correct, A5 updated exactly that file, and A5 does not appear in the output.

**Why it matters more than two lines of noise.** A standing false positive is the *"gate that cries wolf"* failure named in [B-316](#b-316--two-better-auth-session-tokens-were-committed-and-pushed-to-the-remote)'s retrospective: **two findings nobody can ever clear teach every lane to skim the output**, and the day a real drift appears it is in a list that has always had two entries. The tool's own footer is honest — *"this check sees whether a file changed, never whether what it says is true"* — and that honesty is exactly why the file list has to be right.

**Fix shape.** Allow more than one document per module — the structure is already a tuple — and correct the two entries. **A lane changing `provider_normalization`'s public port should satisfy the check by documenting the port**, which is where the port is documented.

### B-320 · Two modules naming a response model the same thing silently rename a shipped API contract

| | |
|---|---|
| **Module** | Repository-wide — every module's `interface/schemas.py` |
| **Current assignee** | **QE** — a repository-wide contract check, in the same family as `lint-imports` and `tenancy_policy.py` |
| **Severity** | **🟠** — **it breaks a client and nothing reports it.** Not 🔴: no collision is currently live |
| **Status** | **`OPEN`** — reported by Lane B. **The instance was fixed; the class was not** |
| **Found** | 2026-08-03, by Lane B, **by causing it** while adding A5's endpoint |

**Steps to reproduce.** Add a response model to any module whose class name matches one in another module. Fetch `/openapi.json`.

**Expected.** A name collision across fifteen modules is caught by something.

**Actual.** FastAPI qualifies both classes to disambiguate them, so **`components.schemas["ObservationResponse"]` stops existing** — and the Business Event Engine's evidence drawer, which has shipped under that name, is renamed on the wire by a change in a module it has never heard of. A generated client regenerates against a different type; a hand-written one 404s on a `$ref`.

**What it survived.** `mypy --strict` (two classes in two modules is legal Python) · `lint-imports` (no import crosses anything) · OpenAPI generation itself (**the qualification is FastAPI working as designed**) · the module's own tests, which import the class rather than reading the schema.

**What caught it.** `test_every_response_field_is_documented`, which iterates a **hardcoded list** of two schema names it happens to care about, and raised `KeyError`. **It found this by accident.** A collision between two names that list does not mention would ship silently.

**The fix is one assertion, and the repository already has the shape for it.** Walk every `interface/schemas.py`, collect classes deriving from `BaseModel`, assert the names are unique — the same discipline as `TENANT_OWNED_TABLES` classifying every new table, and cheaper. It could equally read `/openapi.json` and assert that every registered response model's class name appears as a component key, which catches the qualification directly.

**Not fixed by Lane B.** The check binds every module's naming and belongs beside the other repository-wide contracts. **The collision itself is fixed**: A5's model is `AccountObservationResponse`, and the *newer* name moved because the older one is already a client contract.

### B-319 · The Playground produces no attribute transitions, so a company's history has nothing to draw

| | |
|---|---|
| **Module** | Provider Simulation Framework — `signora_platform/simulation/`, and the Playground scenario it drives |
| **Current assignee** | **QE** — the simulation framework and the Playground seeder are repository-wide test infrastructure |
| **Severity** | **🟠** — **it makes a shipped capability look empty rather than wrong.** A5's screen would render correctly and show a customer nothing |
| **Status** | **`OPEN`** — reported by Lane B, **not fixed.** Changing what the simulator emits changes every downstream fixture in the repository |
| **Found** | 2026-08-03, by Lane B, while building A5's endpoint — **by a test asserting a transition and finding none** |

**Steps to reproduce.** Seed the Playground, then `GET /workspaces/{id}/accounts/{account_id}/observations`.

**Expected.** A company's history contains transitions — *"employee count went from 120 to 145 between 30 May and 1 July"*. That is what A5 exists to show and what the brief's *"Grew headcount 15% over 32 days"* is derived from.

**Actual.** Every observation is `occurrence_observed` with `previous_value: null`:

```
occurrence_observed  headcount_change
occurrence_observed  intent_topic_surge
occurrence_observed  technology_detected
occurrence_observed  technology_removed
```

**The architecture is right; the data does not exercise it.** `EMPLOYEE_COUNT` is classified `STATE` in `ATTRIBUTE_KINDS` and **does** produce transitions — `test_derivation.py` proves it with two constructed claims. A transition needs **one provider asserting the same state attribute twice**, and the scenario enriches each account **once**. `HEADCOUNT_CHANGE` is deliberately an occurrence because CoreSignal reports a delta directly, and deriving a transition from it would double-count against `EMPLOYEE_COUNT` — that reasoning is correct and must not be changed to make this pass.

> **So the fix is a second enrichment pass at a later `observed_at`, not a reclassification.** Anything that turns an occurrence into a transition to fill a screen would corrupt the pipeline the screen is supposed to be showing.

**Why every gate passed.** 2714 tests, and none of them asks *"does the demonstration data exercise the transition path?"* Unit tests construct their own claims and pass; the pipeline tests assert that occurrences were recorded correctly, which they were. **The gap is between a capability being correct and being demonstrable**, and it is exactly the class §2 added *"every completed slice is demoable by a non-engineer"* to catch.

**Pinned executably.** `test_the_seeded_pipeline_records_occurrences_and_no_transitions` asserts the limitation and **fails the day it is fixed** — because that day is the day A5's screen becomes worth building, and nothing else in the repository would say so.

**Not fixed by Lane B.** The simulator is shared infrastructure; a second enrichment pass changes claim counts, observation counts, signal inputs and score inputs in every fixture that seeds the Playground. **That is a repository-wide change with a coverage and certification blast radius**, and it belongs to whoever owns the framework.

### B-318 · A Security Invariant matches text, so a comment fails it and an alias evades it

| | |
|---|---|
| **Module** | `backend/tests/security_invariants/test_ai_platform.py` — `TestAnAccountsNameIsResolvedInExactlyOnePlace` |
| **Current assignee** | **QE** — the Security Invariants suite is repository-wide and QE's |
| **Severity** | 🟡 — **the guarantee is weaker than it reads, and it has never been wrong yet.** Not 🟠: nothing is currently evading it |
| **Status** | **`OPEN`** — reported by Lane B, **not fixed.** A lane must never weaken a Security Invariant, and it should not silently rewrite one either |
| **Found** | 2026-08-03, by Lane B, **by failing it with a docstring** while building A1 |

**Steps to reproduce.** Write `select_name()` inside a comment or docstring in any file under `modules/`. Run `pytest tests/security_invariants -k ResolvedInExactlyOnePlace`.

**Expected.** The invariant states *"`select_name` is called from one place"*. A comment calls nothing.

**Actual.** It fails. The check is `if "select_name(" in path.read_text()`, so **a mention is indistinguishable from a call.** A1's claim-port docstring explained where the displayed name comes from and failed the build.

**The half that matters more, and it points the other way.** The same text match means a genuine second caller can evade it entirely:

```python
from modules.knowledge_graph.domain.naming import select_name as pick
winner = pick(claims)          # a second surface deciding which name wins
```

**No file contains `select_name(`, the invariant passes, and the property it protects is gone** — two surfaces choosing what a company is called, which is exactly the defect it exists to prevent.

**Why it is written that way, and it is a defensible choice.** The docstring records that a broader rule *"could not be stated correctly"* and was narrowed deliberately rather than faked into passing (§2, decorative logic) — which is the right instinct. **The narrowing just landed one level short of the AST**: `ast.walk` looking for a `Call` whose func resolves to the imported name catches both problems and keeps the property honest. The neighbouring test in the same class already parses with `ast`, so the tool is present in the file.

**Not fixed by Lane B.** *"Never delete, skip, or weaken one of these tests"* (§11) is a rule about not making them pass — and rewriting one to be stricter is still a change to a repository-wide guarantee that QE owns. **The A1 docstring was reworded instead**, which is the change that was Lane B's to make.

### B-317 · `make test` takes no environment lease, so two runs in one lane silently corrupt each other

| | |
|---|---|
| **Module** | Repository tooling — `Makefile`, `infra/environment-lease.py` |
| **Current assignee** | **Lane C — Platform Foundation**, 2026-08-05, on the product owner's direction: *"treat this as a repository execution infrastructure issue rather than merely a testing inconvenience… it should be enforced mechanically."* **Was QE's**, and QE raised its larger sibling [B-118](#b-118) **while blocked by it**. `infra/` and the `Makefile` are Lane C's under [D-022](DECISION_REGISTER.md). **Assessed in [436](architecture/436-execution-isolation.md) §③** |
| **Severity** | 🟠 — **the failure is silent and the result looks like a normal run.** Not 🔴: it needs two concurrent runs in one lane, which is a mistake rather than a routine |
| **Status** | **`FIXED` for `make test`** — Lane C, 2026-08-05. The target now runs under `environment-lease.py run test`, exactly as `certify`, `smoke`, `dr`, `up`, `down` and `e2e` already did. **Verified by causing it**: with the lease held, `make test` prints `BLOCKED`, names the holder and exits non-zero. **`VERIFIED` is QE's.** ⚠️ **The bare-`pytest` half is deliberately NOT fixed and is not this lane's to fix.** [436 §③](architecture/436-execution-isolation.md) proposes that `backend/tests/conftest.py` refuse to start when another pid holds the lease — the same shape as the guard that already refuses to truncate without `SIGNORA_ALLOW_DESTRUCTIVE_TESTS`, and the design is written out there. **It changes startup behaviour for every lane on every targeted test run, and the suite's fixtures are QE's.** Finding a defect outside your assignment is an obligation to report it, never permission to fix it (§20e) — **the same rule Lane B applied to [B-117](#b-117) in this office's own file, and Lane A applied to `opportunity_engine` in [B-103](#b-103) today.** **This row stays `OPEN` until QE rules on that half** |
| **Found** | 2026-08-03, by Lane B, **by causing it** — a `make test --cov` was running when a targeted `pytest tests/knowledge_graph` was started against the same lane database |

**Steps to reproduce.** In one lane, run `make test`. Before it finishes, run `pytest tests/<anything>` in the same checkout.

**Expected.** The second run refuses, exactly as `make certify`, `make smoke`, `make dr`, `make e2e` and `make product-demo` all do: *"BLOCKED — the environment is leased by another operation."*

**Actual.** Both run. `tests/conftest.py` truncates every table after each test, so each run is deleting the other's fixtures mid-suite. **The output of both is unreliable and neither says so.**

**This is the same failure the lease was built for.** The Makefile records it beside the lease itself — *"a second operation contaminated a certification"*, cycle 25's `pytest 134 passed` against a suite of 2589. **Eight targets take a lease and the one every lane runs most does not.**

**Why it was not caught.** The lease was introduced for the targets that bind *ports* — the production stack, the review environment, Playwright. `make test` binds no port, so it looked unaffected. **It binds something scarcer: the one database whose tables it truncates.**

**Not fixed by Lane B.** `make test` is the gate every lane and QE runs, `environment-lease.py` is repository tooling, and **a gate is a slice rather than a passing edit** ([B-014](#b-014--a-closeout-commit-changed-a-certification-gate)). The fix is one line by analogy with the eight that already have it; the judgement is whether `test` should share the existing lease names or hold its own, which decides whether a lane may run its suite while a review stack is up.

**Lane B's own run was re-done cleanly**, single-run, after killing the concurrent one — the coverage figure reported for this slice is from that run and not from the contaminated pair.

### B-316 · Two Better Auth session tokens were committed and pushed to the remote

| | |
|---|---|
| **Module** | Repository — `frontend/tests/e2e/.auth/` |
| **Current assignee** | **Lane B** — it committed them, and it has remediated the branch |
| **Severity** | 🟡 — **the class is 🔴 and the instance is not.** See *impact*, which is stated rather than assumed |
| **Status** | **`FIXED`** — Lane B, 2026-08-03. **`VERIFIED` is QE's**, and the residual question below is genuinely QE's to answer |
| **Found** | 2026-08-03, by Lane B, when a rebase refused to overwrite two untracked files and the reason turned out to be that an earlier commit had tracked them |

**Steps to reproduce (the original defect).** Run the E2E suite so Playwright writes its storage state, then commit before `2026-08-03`. `frontend/tests/e2e/.auth/` was not ignored, so `git add` took it.

**Actual.** `81f6952` added `dana-reyes-northwind-example.json` and `marcus-hale-northwind-example.json`, each containing a live `better-auth.session_token`. **Both were pushed to `origin/lane-b-commercial-profile`.** `efce071` deleted them, which removed them from the tip and left them in the history.

**Impact, measured rather than assumed.** `"domain": "localhost"`, `"secure": false`, expiring 2026-08-09, valid against **one lane's local database on one workstation**. There is no reachable service they authenticate to. **The exploitable risk is nil; the process defect is real**, and the two must not be conflated in either direction — inflating it teaches people to discount the register, and dismissing it teaches them the rule is soft.

**Why every gate passed.** Nothing in the repository looks for a credential in a diff. `make certify`, `lint-imports`, `mypy` and the frontend suite are all indifferent to file *content* of this kind. **§13's rule — *"no credentials, API keys, or secrets are ever hardcoded or committed"* — is enforced by nothing.**

**Fixed, in two parts.** `c35cd57` added `frontend/tests/e2e/.auth/` to `.gitignore`, so it cannot recur — **that landed before this row existed and is why the defect is already closed at the class level.** The branch history was then rewritten during the 2026-08-03 rebase so no commit on `lane-b-commercial-profile` contains either file, and the branch was force-pushed.

**What is not fixed, and is QE's.** **A force-push removes the ref, not the object.** The two commits remain retrievable by SHA on the remote until it garbage-collects, and Lane B has no authority over the hosting account. **The durable answer is a gate, not a cleanup**: a pre-commit or certification check that refuses a diff containing a private-key header, an `.env` value or a session-token shape. That is repository-wide tooling and is recorded here rather than built.

> ### Retrospective — requested by the product owner, 2026-08-03
>
> **How it happened.** Playwright writes storage state to `frontend/tests/e2e/.auth/` on every authenticated run. That directory did not exist when the ignore rules were written, and nothing added it when the E2E suite arrived. **The commit that carried the tokens was a documentation commit** — `git add -A` after a review session, which is when a working tree is fullest of things nobody is thinking about.
>
> **Why it was not detected.** Three layers each had a reason not to see it:
>
> | Layer | Why it was silent |
> |---|---|
> | `.gitignore` | **The rule that would have caught it was written four days later**, by this same lane, for an unrelated reason ([`c35cd57`](#) — stopping the suite touching the review environment). The fix preceded the report by accident |
> | Every gate | `make certify`, `mypy`, `lint-imports`, `pytest`, `vitest` and `tsc` are all indifferent to file *content* of this kind. **§13's rule is enforced by nothing** — it is a sentence in a governance document |
> | Review | A diff of *"+30 lines, two JSON files"* inside a 40-file documentation commit is exactly the shape a reader skims |
>
> **The lightweight improvement, and it is one gate rather than a policy.** A path-and-content check in `infra/`, run by `make certify`, that refuses a commit introducing: a `BEGIN ... PRIVATE KEY` header · a file named `.env` or `.env.*` (other than `.example`) · a Playwright storage-state shape (`"cookies": [` with a `"value"` beside it) · an `Authorization: Bearer` literal outside a test fixture.
>
> **Deliberately not a secret scanner.** A general entropy scanner produces false positives on UUIDs, hashes and fixture ids, and **a gate that cries wolf is a gate people learn to pass with `--no-verify`.** Four named shapes catch the classes this repository actually generates, and each can be explained in one line when it fires.
>
> **Deliberately not a hook, either.** A pre-commit hook lives on one workstation and is invisible to the repository (§20c-2's reasoning: the local run is the only run, so it must be the one that decides). **In `make certify` it binds every lane identically.**
>
> **What this cannot fix, stated plainly.** A gate catches the *next* one. Nothing in a lane's authority removes an object already on a remote — that needs the hosting account, and it is why the impact assessment above is the honest mitigation rather than the cleanup.

### B-315 · Every dialog claims the same HTML id, so a screen reader can be told the wrong title

| | |
|---|---|
| **Module** | Frontend foundation — `frontend/components/ui/dialog.tsx` (frozen, §20c) |
| **Current assignee** | **QE** — `components/ui` is theirs. Reported by Lane B |
| **Severity** | 🟡 — invisible to a sighted user, wrong for everybody else |
| **Status** | `OPEN` |
| **Found** | 2026-08-03, by Lane B, during the product review |

**Steps to reproduce.** Open Your business and count duplicate ids:

```js
const ids = [...document.querySelectorAll('[id]')].map(e => e.id);
ids.filter((v, i) => ids.indexOf(v) !== i)
// ["dialog-title", "dialog-title"]
```

**Expected.** `aria-labelledby` on an open dialog resolves to that dialog's own title.

**Actual.** `Dialog` hardcodes `id="dialog-title"` and points every instance's `aria-labelledby` at it. **Three dialogs are mounted on that page at once**, so the attribute resolves to whichever appears first in the document — **not the open one**. Also invalid HTML.

**Fix shape.** A generated id per instance (`useId`), used by both the heading and the `aria-labelledby`. **Not fixed by Lane B**: same frozen component as [B-312](#b-312--a-dialog-a-keyboard-cannot-reach-anything-inside), same reasoning.

---

### B-314 · Every account brief carries a sentence that stops halfway

| | |
|---|---|
| **Module** | **Product Surface** — the account brief |
| **Current assignee** | **Lane A** — the product surface's assignee. Reported by Lane B, not fixed |
| **Severity** | 🟡 — on every brief in the product, in every state |
| **Status** | **`FIXED`** — Lane A, 2026-08-04, in `9cf1973`, **promoted at `178697e`**. The line now reads *"unchanged since it opened"* and *"−10 since it opened"*. **`VERIFIED` is QE's** |
| **Found** | 2026-08-03, by Lane B, during the product review |

**Steps to reproduce.** Open any account brief and read the line under the score.

**Expected.** A sentence that finishes.

**Actual**, in both states, verified in the DOM rather than in a screenshot:

```
Opened at 33, 5 weeks ago      unchanged since      ← the score has not moved
Opened at 20, 5 weeks ago      -10 since            ← the score has fallen
```

***Unchanged since* what?** The element contains those two fragments and nothing else, so nothing follows in either case.

**Why it matters more than a typo.** It sits directly beneath the number the whole screen exists to justify, and it is the one line that describes the score's *history* — the thing a seller checks before deciding whether a change is worth acting on.

---

### B-313 · The account brief has no top-level heading, and it is the screen sellers live on

| | |
|---|---|
| **Module** | **Product surface** — `frontend/app/(app)/accounts/[accountId]/page.tsx` |
| **Current assignee** | **Lane A** — the product surface's assignee. **Reported by Lane B, not fixed** |
| **Severity** | 🟡 — invisible to sighted users, and the page has no name at all for anybody navigating by structure |
| **Status** | **`FIXED`** — Lane A, 2026-08-04, in `9cf1973`, **promoted at `178697e`**. The brief now carries one `<h1>` naming the account, with both `<h2>`s beneath it. **`VERIFIED` is QE's** |
| **Found** | 2026-08-03, by Lane B, when a reload assertion waited for an `<h1>` and timed out |

**Steps to reproduce.** Open any account brief and list its headings:

```js
[...document.querySelectorAll('h1,h2,h3')].map(h => h.tagName + ' ' + h.textContent)
// ["H2 What contributed", "H2 What has happened"]
```

**Expected.** One `<h1>` naming the account, with the sections beneath it — the structure every other screen has.

**Actual.** **No `<h1>` anywhere on the page.** Two `<h2>`s hang under nothing. A screen-reader user who jumps by heading lands on *"What contributed"* with no idea which account they are looking at, and the document outline begins at level 2.

**Why nothing caught it.** `accessibility.spec.ts` asserts *"exactly one level-1 heading"* for the attention list, Your business and Settings — **and not for the brief**, because the list was written from the screens that had one. **A test suite written by looking at what exists inherits what is missing**, which is the same shape as the `@smoke` list only covering screens somebody remembered.

> **Not fixed by Lane B.** It is product-surface markup and the product surface has an assignee (`CLAUDE.md` §20e: *finding a defect outside your assignment is not permission to fix it*). It is a small change — a heading naming the account — and it should carry a `@a11y` assertion for the brief in the same commit, so the gap cannot reappear.

---

### B-312 · A dialog a keyboard cannot reach anything inside

| | |
|---|---|
| **Module** | Frontend foundation — `frontend/components/ui/dialog.tsx` (frozen, §20c) |
| **Current assignee** | **QE** — `components/ui` is theirs. **Reported by Lane B, attempted and reverted** (below) |
| **Severity** | 🟡 — the modal works with a mouse and strands a keyboard |
| **Status** | **`OPEN`** — and **asserted executably**: `interaction-boundaries.spec.ts` carries a `test.fail()` that passes while the defect exists and turns red the moment it is fixed |
| **Found** | 2026-08-03, by Lane B, probing where focus actually goes during an open modal |

**Steps to reproduce.** Open an account brief, open a citation, and press Tab eight times:

```
BODY · BODY · BODY · BODY · BODY · BODY · BODY · BODY
```

**Expected.** Something to land on, and something to press.

**Actual.** **The evidence drawer contains no focusable element of any kind** — no close button, no link, only text. Every Tab lands on `document.body`. The isolation is intact (focus never reaches the page behind, which was verified separately), but a keyboard user is **stranded inside a modal whose only exit is a key nothing on screen mentions.**

**Why the focus trap being "correct" hid it.** A trap is normally tested by checking focus stays inside. It did — trivially, because there was nowhere for it to go. **The half nobody asserts is that a dialog contains something to reach**, and a trap around an empty room is not protection.

For contrast, the editing dialog is fine, and the probe shows why:

```
INPUT [in dialog] → BUTTON "Cancel" [in dialog] → BODY → INPUT [in dialog] → …
```

— it has controls, and `body` at the wrap point is Chromium behaving normally.

**The fix, and why Lane B did not land it.** A close control in `Dialog`'s header, so **every** dialog has one rather than only those whose footer happens to carry a Cancel button — the defect class is *"a Dialog need not offer a way out"*, and fixing `evidence.tsx` alone leaves the next dialog free to repeat it.

**It was written, and reverted.** §20c's accessibility clause would have permitted it, on the same basis as [B-307](#b-307--the-page-scrolls-underneath-an-open-dialog-and-the-component-says-it-does-not). **Three things say it is not this lane's to land:**

| | |
|---|---|
| It **breaks a test in a module Lane B is not assigned** | `tests/components/narration.test.tsx` asserts a dialog contains no button when nothing resolves. Making the repository green would mean editing the product surface's test — outside the Change Budget |
| It **changes every dialog in the product** | §20c requires a human to look at a changed screen, and five screens change at once |
| The blast radius **is the signal** | B-307 was a self-contained fix inside one component. This one reaches other modules' assertions, which is the difference between an accessibility fix and a design change |

> **Left open on purpose, with the evidence and the diff description attached rather than the diff.** Whoever holds `components/ui` can land it in minutes; what they cannot reconstruct is the eight-tabs-eight-`body`s probe that proves it matters.

---

### B-311 · The E2E suite passed or failed depending on which terminal it was run from

| | |
|---|---|
| **Module** | None — `frontend/playwright.config.ts` |
| **Current assignee** | **Lane B** — found and fixed in the same slice |
| **Severity** | 🟠 — **every test fails, and the failure looks like a broken suite rather than a missing variable** |
| **Status** | **`FIXED`** — 2026-08-03, Lane B. Awaiting QE verification |
| **Found** | 2026-08-03, by Lane B, when a suite that had passed 119/119 the day before failed 128/128 |

**Steps to reproduce.** From a shell that has not exported `LD_LIBRARY_PATH`:

```
$ make e2e
  Running 128 tests using 1 worker
  ✘ 1 [authenticate] › sign in as the owner (5ms)
  ✘ 2 [authenticate] › sign in as a member (4ms)
  … 128 failures, every one in 4–5ms
```

**Expected.** The suite behaves the same way twice.

**Actual.** `browserType.launch: Target page, context or browser has been closed`, on every test, because Chromium cannot find `libnspr4.so`. **The same suite, the same commit, passed completely in a different terminal ten hours earlier.**

**Cause.** `npx playwright install-deps` requires `sudo`, which a lane does not have, so the browser's shared objects were unpacked into `~/.cache/ms-playwright-deps/lib` and reached with an **exported shell variable**. Nothing in the repository knew about it.

> **This is a hidden input, and hidden inputs are architecture defects** (`CLAUDE.md` §2): *"any input that influences behaviour without being part of the declared contract… makes the same declared inputs produce different results."* Here it decided whether **anything at all** ran.
>
> **The tempting fix was to document the variable in `RUNNING.md`.** That would have been the wrong one — a documented hidden input is still hidden the first time somebody does not read the document, and the whole point of §2 is to *remove* them rather than describe them.

**Fix.** `browserEnvironment()` in `tests/e2e/fixtures/environment.ts` — the file that already owns *"which environment this suite may drive"* — supplies the path when the unpacked cache exists and returns `undefined` when it does not, so a properly provisioned machine is unaffected. Wired into `playwright.config.ts` (`use.launchOptions.env`) and into the endurance recorder. **Verified by running the suite with `env -u LD_LIBRARY_PATH`.**

**One thing this corrects in my own record.** `record.ts` briefly carried a comment claiming *"the Playwright test runner adds that directory and the library does not"*. **That was wrong** — neither does; the runner had simply always been launched from a shell where it was set. The comment was written before the suite was tried from a clean environment, and it is exactly the kind of confident wrong explanation §2 warns about.

---

### B-310 · The Playground seeder tells every lane to go and open Human Review

| | |
|---|---|
| **Module** | None — `backend/tests/playground/seed.py`, shared test infrastructure |
| **Current assignee** | **Lane B** — found and fixed in the same slice |
| **Severity** | 🟡 — wrong for everybody except the person who wrote it, and it points at the one environment nobody may write to |
| **Status** | **`FIXED`** — 2026-08-03, Lane B. Awaiting QE verification |
| **Found** | 2026-08-03, by Lane B, reading its own endurance run's output |

**Steps to reproduce.** Seed any lane's Playground, from any lane:

```
$ make endurance            # Lane B: database signora_lane_b, app on 3400
  …
  members     4 signed-in user(s) enrolled

  Open http://localhost:3000          ← Human Review, and not this lane's data
```

**Expected.** After seeding *this* database, be told where to see *this* data.

**Actual.** Every lane, every time, is directed at `http://localhost:3000` — **Human Review's port, which belongs to the product owner and to no lane** (`RUNNING.md` § Running a lane). A lane that followed the instruction would find a different organization, conclude the seed had not worked, and might act on rows it did not create. The `else` branch is worse: it sends the reader to `http://localhost:3000/sign-up` **to create accounts**, which is a write.

**Cause.** Two hardcoded strings, correct only on the one stack that happens to sit on the default ports.

**Fix.** `_app_url()` reads `SIGNORA_APP_URL` — the variable every lane already sets — and falls back to 3000 only when nothing else is known. The Makefile now passes it to the seed step as well as to the browser.

> **This is the third instance of one shape, and the shape is worth naming.** The suite defaulted to port 3000 ([the environment guard](../frontend/tests/e2e/fixtures/environment.ts)), the auth database was shared because it was never allocated ([B-104](#b-104)), and now the seeder printed it. **Each was a default that was right for whoever wrote it and wrong for everybody who came after** — and the product owner's rule covers all three: *if a mistake is predictable, the repository should refuse to make it.* A default cannot refuse; only a required value can. This one still has a fallback because a print statement cannot safely refuse to print, and that is the weaker fix, stated as such.

---

### B-309 · `clean_database` truncates five tables and relies on a cascade that cannot happen

| | |
|---|---|
| **Module** | None — `backend/tests/conftest.py`, shared test infrastructure |
| **Current assignee** | **QE** — repository-wide test infrastructure, and every lane's database is affected |
| **Severity** | 🟡 — **no test is wrong and nothing is slow; every environment's database grows without bound and stops describing anything** |
| **Status** | **`OPEN`** — reported by Lane B, not fixed. It is one change affecting every lane's suite |
| **Found** | 2026-08-03, by Lane B, while investigating why a browser suite had become slow |

**Steps to reproduce.** Run any backend suite against any database a few dozen times, then count what is left behind:

```sql
select count(*) from opportunity o
  where not exists (select 1 from workspace w where w.id = o.workspace_id);
```

**Expected.** A truncating fixture leaves the database as it found it.

**Actual — measured 2026-08-03, across every database on this workstation.**

| Database | Rows in tenant tables | Orphaned | Live workspaces | On disk |
|---|---|---|---|---|
| `signora` (Human Review) | 1,100,278 | **1,100,278** | **0** | 486 MB |
| `signora_lane_a` | 481,989 | **481,989** | 0 | 232 MB |
| `signora_lane_b` | 225,428 | **223,918** | 1 | 119 MB |
| `signora_lane_qe` | 0 | 0 | 0 | 13 MB |
| | | **1.81 million** | | **850 MB** |

> **Two corrections to this row's first version, both made by measuring rather than by re-reading it.**
>
> **The count was a fraction of the truth.** It said *"4164 orphaned rows across 1673 dead workspaces"* and named 28 tables; that was one table's figure — `opportunity` — presented as the total. **43 tables carry `workspace_id`**, and the real figure is **1.81 million rows in 850 MB**, three orders of magnitude larger.
>
> **And the stated symptom was wrong.** It said the suite *"gets slower"*. **It does not, and that is now measured**: every table carrying `workspace_id` has an index that includes it, so a workspace-scoped read of the bloated `claim` table (56,874 rows, 149 of them live) is an index-only scan returning in **0.14 ms**. Nothing is slow. The wrong version was the more alarming one, which is exactly why it needed checking.

**Cause.**

```python
"TRUNCATE membership, workspace, outbox_event, "
"processed_event, dead_letter_event CASCADE"
```

**`CASCADE` follows foreign keys, and there are none to follow.** Twenty-eight tables carry `workspace_id` and **not one has a foreign key to `workspace`**:

```
ai_inference · ai_narration · ai_reasoning · business_event · buying_committee
buying_score · claim · commercial_focus · connected_account · entity
icp_declaration · icp_segment · icp_segment_product · icp_segment_state
icp_segment_version · identity_binding · integration_grant · integration_secret
normalization_outcome · observation · opportunity · opportunity_state
product_catalog · provider_sync · provider_watermark · …
```

> **That absence is correct and should not be "fixed".** A foreign key from every module's table to `workspace_tenancy`'s table would couple every module's schema to another module's, and Principle 5 requires any module to be extractable into its own service without changing its domain or application layers. **The schema is right; the fixture's assumption about it is wrong.**

**Why it has never been noticed.** Nothing reads the orphans. Every query filters by `workspace_id`, RLS scopes to the live one, and every such column is indexed — so the rows are invisible to correctness *and* to performance. **The only thing they affect is what the database is a description of**, and nothing asserts that.

---

#### How often, and how widely — the frequency evidence

| | |
|---|---|
| **The fixture** | `clean_database` in `backend/tests/conftest.py`, **`autouse=True` at function scope in the top-level conftest** |
| **Tests that run it** | **All 2671.** Autouse in the root conftest means every test in `backend/tests/` truncates on teardown — including pure unit tests that never opened a connection |
| **Suites affected** | **Every one.** `security_invariants` has its own conftest but inherits this fixture; the Playground seeder, `make smoke`, `make dr` and `make certify` all run against databases this has been leaking into |
| **Leak per test** | Every row a test wrote to any of the other 40 tenant-owned tables |
| **Cost of the truncate itself** | 8 ms, on the bloated `signora_lane_b`. **2671 tests × 8 ms ≈ 21 seconds a run**, paid by every test including those that never touch a database |
| **Environments affected** | Four of four on this workstation, including **Human Review**, whose database is the largest of them |

#### Why the assumption is wrong, precisely

`TRUNCATE ... CASCADE` extends only along **foreign keys that reference the truncated tables**. There is exactly one in the whole schema:

```
membership.workspace_id → workspace.id
```

and `membership` is **already named in the statement**. **`CASCADE` therefore reaches nothing that the explicit list does not already reach.** Removing the keyword changes no behaviour at all — which makes it textbook Decorative Logic (`CLAUDE.md` §2): *implementation that appears to enforce a property but whose removal does not change the property it claims to protect.* It reads as a cleanup guarantee, and there has never been one.

> **The missing foreign keys are correct and must not be added.** 42 tables are classified tenant-owned in `tenancy_policy.py`; a foreign key from each to `workspace` would couple every module's schema to Workspace & Tenancy's, and Principle 5 requires any module to be extractable into its own service without changing its domain or application layers. **The schema is right. The fixture's assumption about the schema is wrong.**

#### What cleanup should mean — proposed semantics, for QE to decide

Stated as a contract rather than as an implementation, because the implementation is QE's call:

1. **A test leaves the database as it found it, or the fixture is not a cleanup.** Partial cleanup is worse than none: it looks like the guarantee while providing a fraction of it.
2. **The table list is derived, never written by hand.** A hand-maintained list is the same defect one migration later — and the derivation already exists in `TENANT_OWNED_TABLES` and `PLATFORM_INFRASTRUCTURE_TABLES`, which `CLAUDE.md` §8 already requires every new table to join in the migration that creates it. **A new table is then cleaned up because it was classified, not because somebody remembered two files.**
3. **Whatever cleans up must fail loudly when it is incomplete.** A Security Invariant asserting *"no table carrying `workspace_id` holds a row after teardown"* would have caught this on the day it was introduced, and would catch the next table to escape the list.
4. **Cost is bounded per test, not per suite.** 2671 truncates of 42 tables is a different proposition from 2671 truncates of 5; a per-session schema reset (RE-03's disposable database) may well be cheaper than either.

#### How future end-to-end suites should think about cleanup — and why they are different

**An E2E suite must not use this fixture, and Lane B's does not.** The reasoning generalises, so it is recorded here rather than in one lane's design doc:

| | Backend suite | End-to-end suite |
|---|---|---|
| **Writes through** | fixtures, directly | **the product, as a customer** |
| **Can it truncate?** | Yes — it created the rows | **No.** It never learned which rows it caused; the product decided that |
| **So it isolates by** | truncation between tests | **re-seeding a fresh workspace before the suite** |
| **And its unit of isolation is** | the test | **the run** |

**The rule this suggests: an end-to-end suite owns an environment, never a table.** It re-seeds through the same door a customer's data enters (`20-provider-simulation.md`), asserts against what that produced, and deletes nothing — because a suite that reached into tables to tidy up would be doing the one thing the product-owner rule forbids: *"you are not allowed to bypass the product / manually insert rows into the database."* **Deleting is bypassing too.**

That is why [B-308](#b-308--re-seeding-the-playground-adds-an-organization-instead-of-replacing-one) mattered enough to fix immediately: **re-seeding is the only cleanup an E2E suite is permitted**, so a re-seed that accumulates rather than replaces takes the mechanism away.

**Not fixed by Lane B, deliberately.** The fix changes a fixture every module's suite depends on, its correct form is a decision between three shapes (derive the list · reset the schema per session · RE-03's disposable database), and **shared test infrastructure is QE's**. Reported with the measurement, the frequency, the cost and the proposed semantics so the decision can be made on evidence rather than on a hunch.

---

### B-308 · Re-seeding the Playground adds an organization instead of replacing one

| | |
|---|---|
| **Module** | None — `backend/tests/playground/seed.py`, the demonstration seeder |
| **Current assignee** | **Lane B**, End-to-End Product Confidence |
| **Severity** | 🟠 — **a reviewer opens the product and finds an empty list, in a database holding twelve full ones** |
| **Status** | **`FIXED`** — Lane B, 2026-08-03. **`VERIFIED` is QE's** |
| **Found** | 2026-08-03, by Lane B — **by the browser suite failing, not by reading the seeder** |

**Steps to reproduce.** Run `make demo-seed` twice. Open the product.

**Expected.** One organization, freshly seeded.

**Actual.** Two, both named *Playground*. After twelve runs:

```
select name, count(*) from workspace group by name;
 Playground | 12
```

The organization selector offers *Playground* twelve times, indistinguishably. The active one is whichever the browser stored — and if that is an early one, **its accounts were superseded long ago and the attention list is empty.** That is what the suite hit: `main a[href^="/accounts/"]` found nothing, on a database with twelve fully seeded organizations in it.

**Why it went unseen.** `_tracked` creates a workspace and nothing removed the last. Harmless while nobody re-seeded — and **`make e2e` re-seeds before every run**, which is what turned a latent trap into a daily one. The same trap was always waiting for anybody who ran `make demo-seed` twice.

**Fix.** The seeder retires previous Playgrounds before seeding. **This is what *re*-seed has always meant**; accumulating is the surprising reading, and it was the one implemented. Scoped to the seeder's own workspace name — a workspace somebody created by hand is not its to delete.

### The fix's own incident, and the correction to my first account of it

**The development PostgreSQL went into crash recovery while the first version of this fix ran.**

```
LOG:  database system was not properly shut down; automatic recovery in progress
LOG:  redo starts at 4/9BD8CA98 … redo done … 3.40 s
LOG:  database system is ready to accept connections
```

**My first explanation was that a twelve-workspace bulk delete was too heavy. That was wrong, and the real cause is worse.**

The host had **14 of 15 GiB of memory in use and a load average of 54**, because this lane had accumulated **four `next dev` servers, five orphaned Playwright workers and seven vitest workers** across a day of runs — every one of them mine, none of them cleaned up. The delete was the *trigger*; **the exhausted host was the cause**, and PostgreSQL was one of several things about to fall over.

> **Recorded in full because the wrong version was more flattering.** *"A heavy query crashed the database"* is a database story. *"I leaked processes until the machine ran out of memory and something died"* is an operator story, and operator stability is a dimension [`RELEASE_ENGINEERING.md`](RELEASE_ENGINEERING.md) §8 already names as unmeasured — *"cycle 25 was entirely this, and nothing distinguishes it."* **This is a second data point for that, from a different lane.**

**Nothing was lost.** `signora`, `signora_lane_a` and `signora_lane_qe` were verified intact afterwards and no other lane was mid-operation. After reclaiming the leaked processes, memory went 14 GiB → 8.6 GiB and load 54 → 19.

**The fix is kept anyway, and rewritten to delete one workspace per transaction**: the normal case is one, so the pathological case becomes twelve bounded steps rather than one unbounded one. That is correct regardless of how much memory the host has.

**The operator lesson, which is the transferable one:** a lane that runs a browser suite repeatedly must reclaim its dev servers and its browsers, and `pkill` between runs is not optional housekeeping — it is what keeps the shared PostgreSQL alive.

---

### B-307 · The page scrolls underneath an open dialog, and the component says it does not

| | |
|---|---|
| **Module** | None — `frontend/components/ui/dialog.tsx`, the frozen design system |
| **Current assignee** | **Lane B**, End-to-End Product Confidence |
| **Severity** | 🟡 — **wrong but survivable.** A reader loses their place in the argument they were checking; nothing is lost or misstated |
| **Status** | **`FIXED`** — Lane B, 2026-08-03. **`VERIFIED` is QE's** |
| **Found** | 2026-08-03, by Lane B, driving a real browser — and **only on the second run**, which is the more interesting half |

**Steps to reproduce.** Open an account brief long enough to scroll. Click any citation. Scroll the wheel.

**Expected.** Nothing behind the dialog moves.

**Actual.** The page scrolls underneath it — measured `scrollY` 886 → 1458. The reader closes the drawer and returns to a page that has moved.

**Cause.** `Dialog` is built on the native `<dialog>` element and `showModal()`. That gives focus trapping, top-layer stacking and Escape handling, and it makes background content inert **to pointer and keyboard interaction** — it does *not* stop the root scroller. A wheel gesture over an open modal scrolls the page behind it.

> **The comment is the finding.** The component's docstring claimed the platform provided *"inertness of the background"*. It provides most of it, and **the sentence asserted a property the code did not have** — the defect class `CLAUDE.md` §2 names: *a comment beside it is then a false claim that survives review*. The docstring is now correct about what `showModal()` does and does not do.

**Fix.** Lock `document.body.style.overflow` while open, restoring the **previous** value rather than clearing it — something else may legitimately have set it, and clobbering it would be this component deciding a page-level concern on its way out.

**Why a frozen component was changed.** §20c permits it for *"an accessibility issue — a missing label, an unreachable control, a lost focus state. These are defects, not enhancements, and never wait for a business milestone to justify them."* Background content that is not inert is that class: it is the WAI-ARIA modal pattern's central requirement. **Announced 🟠 in the commit; QE to verify.**

**And the test that found it had already passed once, vacuously.** Its first run opened a brief shorter than the window, so there was nowhere to scroll and the assertion held for a dialog that locked nothing. It now skips when the page cannot scroll rather than passing. **A test that can pass vacuously is documentation pretending to be code**, and this one proved it by doing so.

---

### B-306 · An owner is thrown out of Settings by pressing F5

| | |
|---|---|
| **Module** | None — `frontend/app/(app)/authenticated-shell.tsx`, the application shell |
| **Current assignee** | **Lane B**, End-to-End Product Validation |
| **Severity** | 🟠 — **the entire administrative surface is unreachable by address**: products, the ideal customer, the buying committee, target accounts, connections. Not bookmarkable, not shareable, gone on refresh |
| **Status** | **`FIXED`** — Lane B, 2026-08-03. **`VERIFIED` is QE's** |
| **Found** | 2026-08-03, by Lane B. **Every Settings test in the new E2E suite failed at once**, which is how a systematic redirect announces itself |

**Steps to reproduce.** Sign in as an owner. Click **Settings** in the sidebar — it opens. **Press F5.**

**Expected.** Settings, still.

**Actual.** The attention list. The same for `/settings/products`, `/settings/connections`, and any link a colleague pastes.

```
owner   /settings             ->  /   | Attention
owner   /settings/products    ->  /   | Attention
owner   /settings/connections ->  /   | Attention
```

**Cause, in two halves — and the second is why an obvious fix would not have worked.**

**1.** `useViewerRole` answers `{ role: null, resolved: true }` when there is no workspace, correctly: *"no workspace means nothing to have a role in."* **On a fresh page load there is no workspace yet** — the list is in flight, `activeWorkspace` is legitimately `null` — so the hook reported a resolved *"not a member"*, `RouteGuard` evaluated `can(null, 'workspace:update')` as false, and redirected.

> The hook's own comment says `resolved` exists so that nobody is *"sent to the front page for the half-second before their own membership arrived."* **The defect arrived through the other input**: the workspace, not the membership.

**2.** Gating on `isLoading` alone is **not sufficient**, and the first fix attempt proved it by still redirecting. `WorkspaceProvider` chooses the active workspace in an effect that runs *after* the list resolves, so there is a render where loading is finished and `activeWorkspace` is still `null`.

**Fix.** The shell answers both questions before anything is guarded:

```ts
const workspaceKnown =
  !workspacesLoading && (activeWorkspace !== null || workspaces.length === 0);
const resolved = viewer.resolved && workspaceKnown;
```

*Which organization is this* and *what is this person in it* — an active organization, or a list that came back empty. **Genuinely open in between.**

**Not weakened for anybody.** Verified in the same run: a member is still redirected out of all three routes, and the server still refuses their write with `403`.

**Regression tests.** `business-setup.spec.ts` — *"the administrative surface is reachable by address"*, three direct loads plus a reload; `permissions.member.spec.ts` holds the other side.

---

### B-305 · Clicking Sign out showed a page of vendor JSON and left the person signed in

| | |
|---|---|
| **Module** | None — `frontend/app/(app)/authenticated-shell.tsx`, the application shell |
| **Current assignee** | **Lane B**, End-to-End Product Validation |
| **Severity** | 🔴 — **a session-termination control that does not terminate the session.** On a shared machine, a person who signed out was still signed in, and the product had told them otherwise by navigating away from itself |
| **Status** | **`FIXED`** — Lane B, 2026-08-03. **`VERIFIED` is QE's** |
| **Found** | 2026-08-03, by Lane B, on the first run of an authenticated Playwright journey |

**Steps to reproduce.** Sign in. Click **Sign out**.

**Expected.** The session ends and the sign-in page is shown.

**Actual.** The browser navigates to a page of raw JSON:

```json
{"message":"Content-Type \"application/x-www-form-urlencoded\" is not allowed. Allowed types: application/json","code":"UNSUPPORTED_MEDIA_TYPE"}
```

**and the session is still valid.** Reloading the product signs straight back in.

**Cause.** The control was a native `<form action="/api/auth/sign-out" method="post">`. A browser submits a form as `application/x-www-form-urlencoded`; Better Auth accepts `application/json` only, so the request was rejected before it reached the vendor's sign-out handler.

**Fix.** Call `signOut()` from `lib/auth/client.ts`, which has always done this correctly — the vendor's own client sends JSON and then navigates to `/sign-in`. **Nothing new was written: one duplicate of a behaviour was removed in favour of the one that works.**

**Regression test.** `frontend/tests/e2e/auth-journey.spec.ts` — *"signing out ends the session and the product is closed again"*, which asserts the redirect **and** that `/api/token` then refuses to mint. `resilience.spec.ts` asserts a second tab is closed too.

**Why nothing caught it.** No test had ever signed in. See [B-303](#b-303--the-browsers-only-route-to-the-api-has-never-existed).

---

### B-304 · Every sign-in landed on a 404, and the fix that recorded it never worked

| | |
|---|---|
| **Module** | None — `frontend/lib/auth/client.ts`, the authentication client |
| **Current assignee** | **Lane B**, End-to-End Product Validation |
| **Severity** | 🔴 — **the first screen after authentication was *"That address does not lead anywhere"*, for every person, by every method** |
| **Status** | **`FIXED`** — Lane B, 2026-08-03. **`VERIFIED` is QE's** |
| **Found** | 2026-08-03, by Lane B, driving the real sign-in form in a browser |

**Steps to reproduce.** Sign in with an address and a password.

**Expected.** The attention list.

**Actual.** `http://localhost:3400/workspaces` → **404**, *"That address does not lead anywhere"*. `/workspaces` has never been a route in this application.

**Cause, and the part worth keeping.** `AFTER_SIGN_IN = '/workspaces'` was passed as Better Auth's `callbackURL`. **D38 recorded exactly this defect and fixed only half of it**: `sign-in-form.tsx` gained a `router.push('/')` after a successful sign-in, which reads like the defect was closed. It never could be — **Better Auth performs its own navigation to `callbackURL`, and it wins the race.**

> **This is Decorative Logic** (CLAUDE.md §2): implementation that appears to enforce a property, whose removal would not change the property it claims to protect — with a comment beside it asserting the correction. It survived three further slices because the constant read as fixed.

**Fix.** `AFTER_SIGN_IN = '/'`. The `router.push` stays, because it is still the right destination when the vendor does not navigate, and it is now the same one.

**Regression test.** `auth-journey.spec.ts` — *"@smoke a person with an address and a password reaches their morning"*, and `auth.setup.ts`, which asserts the destination on every run of every project.

---

### B-303 · The browser's only route to the API has never existed, so no screen has ever shown real data

| | |
|---|---|
| **Module** | None — `frontend/lib/api/client.ts` named a route; `frontend/app/api/proxy/` was never built |
| **Current assignee** | **Lane B**, End-to-End Product Validation |
| **Severity** | 🔴 — **the entire product, in every environment, since M1.2.** Every screen rendered its shell and its empty state and never once its own data |
| **Status** | **`FIXED`** — Lane B, 2026-08-03. **`VERIFIED` is QE's** |
| **Found** | 2026-08-03, by Lane B, watching the network while a signed-in owner opened the attention list |

**Steps to reproduce.** Sign in as the owner of a seeded organization and open `/`.

**Expected.** Twelve accounts, ranked.

**Actual.** *"You are not part of an organization yet"*, and in the network panel:

```
200 GET  /api/auth/get-session
200 POST /api/token
404 GET  /api/proxy/workspaces        ← HTML, from Next's not-found handler
```

**Cause.** `lib/api/client.ts` has chosen `/api/proxy` as the browser's base URL since **`ad52e66` — M1.2, the Authentication Boundary** — deliberately, because the API is not internet-facing in the deployed topology (ADR-0022). **The route it named was never implemented**, and no rewrite exists in `next.config.ts`. One reference, no route, for eleven milestones.

Confirmed against the **production** stack as well as the dev server, so it is not a dev-mode artifact:

```
prod /api/token           -> 401   (the route exists and refuses)
prod /api/proxy/workspaces -> 404  (the route does not exist)
```

**Fix.** `frontend/app/api/proxy/[...path]/route.ts` — a transport hop that forwards method, path, query and body and returns the API's response untouched, including the error envelope `ApiError` parses. It makes **no authorization decision**; the caller's own Bearer token is forwarded and the API verifies it, re-verifies membership and applies Casbin exactly as before. It requires a session so it is not an open forwarder into a service that is otherwise unreachable, and it forwards two headers — notably **not `Cookie`**.

> **🟠 announced, and larger than a lane normally takes.** A new route in the frontend foundation is close to 🔴. It was taken because §20c permits a change for *"a production defect — the foundation is demonstrably wrong"*, because it restores behaviour the code has declared since M1.2 rather than deciding anything new, and because **the assigned work was impossible without it** — an E2E suite against this product could only ever have asserted empty states.
>
> **Ratified by the product owner, 2026-08-03**, on the reasoning that it *"completes architecture that has already existed since M1.2"* — the missing implementation was a production defect, not an architectural decision, and the route restores the declared architecture rather than inventing one. **QE still verifies the security characteristics** at validation: session required, caller's own token forwarded, no cookie forwarded, no authorization decision made.

**Why nothing caught it, and this is the finding under the finding.**

| Gate | Why it passed |
|---|---|
| ~2000 backend tests | call the API directly |
| Vitest component tests | mock the hooks |
| `frontend/tests/e2e/` | one file, and it never signed in |
| `make smoke` | mints a real token through the real frontend path and then calls **the API directly** — the browser→Next→API hop is in no gate |

**Every component was proven and the composition between them was never exercised.** That is now the fourth instance of one pattern — [B-024](#b-024) (fakes accepted a row the database refused), [B-301](#b-301) (the deployed worker never registered a handler), [B-302](#b-302) (the Playground never composed one), and this. **[C-301](LANE_COORDINATION.md) is the assertion that catches the class**, and this is the strongest evidence yet for it.

---

### B-302 · The Playground's account brief shows no history, and it is the only place anybody reviews the product

| | |
|---|---|
| **Module** | `timeline` — the defect is in `backend/tests/pipeline.py`, the pipeline composition root the Playground runs |
| **Current assignee** | **Lane B**, Timeline's feature lead. **The composition root is shared** — see below |
| **Severity** | 🟠 — **a shipped capability is empty in the environment human product review uses.** Not 🔴 only because no customer runs a deployed environment yet |
| **Status** | **`FIXED`** — Lane B, 2026-08-03, **on the product owner's explicit ruling** that a small, customer-facing composition gap is an implementation opportunity rather than a reason to stop. **`VERIFIED` is QE's** |
| **Found** | 2026-08-03, by Lane B, **running the product rather than reading it** — the Complete Product Experience Audit |

**Steps to reproduce.**

```bash
make demo                       # or: python -m tests.playground.seed
# open any of the twelve accounts → "What has happened"
grep -c timeline backend/tests/pipeline.py     # 0
```

**Expected.** An account brief seeded with observations, business events, signals, a score and an opportunity shows a history of them. Lane A mounted the section in `CX-03` and it is correct.

**Actual.** **Empty, for all twelve accounts.** `tests/pipeline.py` — the composition root the Playground runs — wires provider ingestion, normalization, knowledge graph, observations, business events, signals, buying scores and opportunities, and **does not wire Timeline's projection.** Its only mention of the word is in a docstring.

Measured on a freshly seeded database:

```
signal          6311        timeline_entry  156
buying_score    4090        …and every one of those 156 came from
opportunity     3956           Lane B's integration tests, not the Playground
workspaces with buying scores   1703
workspaces with timeline entries   52   ← all of them test workspaces
```

**Why this is B-301's twin, and why it matters more.** [B-301](#b-301--timeline-is-promoted-wired-and-consumes-nothing) was the *deployed worker* not registering the projection. This is the *Playground* not composing it. **Two composition roots, the same module missing from both, found a day apart** — and this one is worse in one specific way: **the deployed worker has no customers yet, and the Playground is where the product owner reviews the product.** A capability that is empty there reads as a capability that does not work.

**It also makes a real capability look like a stub.** *"What has happened"* is the section that answers **R9-04** and **[C-024](LANE_COORDINATION.md)**, both of which were treated as high-value; a reviewer opening the brief today would conclude Timeline had not shipped.

### Fix — Lane B, 2026-08-03

**Originally reported without a fix**, on the ground that `tests/pipeline.py` belongs to no module. **The product owner ruled otherwise**, and the rule is worth quoting because it now applies generally:

> *"If the issue is clearly customer-facing, the implementation is small, does not violate module boundaries, does not duplicate logic, and fixing it preserves repository integrity, then implement it even if it lives in a shared composition root. The ownership model exists to prevent architectural erosion, not to prevent obvious improvements."*

**`project_all` — the ninth stage**, added to `tests/pipeline.py` beside the eight already there, and called from `_tracked` after `qualify_all`. **Reads `PROJECTIONS` rather than naming event types**, exactly as the deployed worker does since [B-301](#b-301--timeline-is-promoted-wired-and-consumes-nothing), so the projection table stays the single authoritative statement of what Timeline consumes.

**It runs last, and that is safe rather than convenient.** Entry ids derive from `event_id` and the insert is `ON CONFLICT DO NOTHING`, so projecting once at the end is identical to interleaving — and it keeps the ordering of the stages that genuinely depend on each other readable.

**No new architecture, no duplicated logic, no boundary crossed.** It composes two already-approved capabilities that had never been introduced to each other.

**Verified by re-seeding the Playground**, not by reading the diff:

```
timeline entries in the seeded workspace: 121      (was 0)
   observation_recorded      60      accounts with any history: 12 of 12
   business_event_detected   20      entries per account: 17, 13, 12, 12 …
   signal_generated          17
   buying_score_updated      12
   opportunity_created       12
```

**108 tests pass** across `opportunity_engine`, `timeline` and the explanation-source suite that shares `_tracked`. `mypy --strict` clean.

**QE is notified by this row**: the shared composition root gained a stage, and every future Playground seed produces account history. **The Playground itself is unchanged** — it calls `_tracked`, which is where the stage was added.

**The general finding, and it now has three instances.** [B-024](#b-024--the-credential-store-that-must-not-be-readable-has-no-tests-at-all) — fakes accepted a row the database refused. [B-301](#b-301--timeline-is-promoted-wired-and-consumes-nothing) — the worker never registered a handler. **B-302** — the Playground never composed one. **Every component proven, the composition never exercised**, three times in two days, and [C-301](LANE_COORDINATION.md) is the assertion that would catch all three.

---

### B-301 · Timeline is promoted, wired and consumes nothing — the deployed worker never registers its projection

| | |
|---|---|
| **Module** | `timeline` — the defect is in `apps/worker/subscriptions.py`, the composition root |
| **Current assignee** | **Lane B**, Timeline's feature lead |
| **Severity** | 🟠 — **a shipped, customer-facing capability that does not work in a deployed environment.** Not 🔴 only because no customer is running a deployed environment yet |
| **Status** | **`FIXED`** — Lane B, 2026-08-02, in the same slice that found it. **`VERIFIED` is QE's to set** |
| **Found** | 2026-08-02, by Lane B, auditing its own modules before starting M14a |

**Steps to reproduce.**

```bash
grep -c "registry.subscribe" backend/apps/worker/subscriptions.py   # 1
grep -rn "project_to_timeline" backend/apps/ --include=*.py         # no match
```

**Expected.** A customer opens an account and sees what has happened to it. Timeline projects nine event types, and the deployed worker consumes them.

**Actual.** The deployed worker registered **exactly one** subscription — `ai_research.requested`, the AI Research Engine consuming its own event. **`project_to_timeline` was referenced nowhere outside tests.** The read API is wired, the router is included, the table exists, the component renders — and **nothing ever writes a row**, so an account timeline stays empty forever.

**Why every gate was green.** Timeline's unit tests drive `ProjectEvent` directly; its integration tests drive the handler directly. **A composition root is the one file no module's own suite covers** — each module tests its half and assumes the wiring. There was no test anywhere asserting what the deployed worker subscribes to, which is why 2518 passing tests said nothing about it.

**This is the same class as [B-024](#b-024--the-credential-store-that-must-not-be-readable-has-no-tests-at-all), one level up.** There, fakes accepted what the database would refuse. Here, tests accepted a handler nothing calls. **Both are a suite proving the parts and never the join.**

### Fix — Lane B, 2026-08-02

**Nine subscriptions, one handler, registered from `PROJECTIONS`** rather than a hand-written list — the projection table is the single authoritative statement of what Timeline consumes, and a list beside it would drift the first time a rule was added.

**On the `read_model` pool**, which has been declared in `pools.py` since M1.1 as *"Timeline, Revenue Intelligence Platform — projection updates"* and **had never been used.** High concurrency, short timeout: the right shape for one insert, and it keeps a projection storm off the pool the pipeline itself runs in.

**It does not need [C-012](LANE_COORDINATION.md) answered first, and does not work around it.** Timeline's entry id is derived from `event_id`, so redelivery — or a dead letter replayed months later — derives the same id and `ON CONFLICT DO NOTHING` refuses it. **The handler is idempotent by construction and needs no share of the dispatcher's transaction**, which is the property C-012 is actually about. The wrapper follows the shape `ai_research_engine` established as the repository's first production consumer.

**Regression tests:** `backend/tests/integration/test_worker_subscriptions.py`, and they assert the join in both directions — every event Timeline projects has a consumer, **and** it subscribes to nothing it cannot project (a subscription with no rule wakes a worker to do nothing and returns `False`, which is indistinguishable from working). Plus: the consumer name is the module's own, registration is idempotent, and every subscription routes to a declared pool.

**The general finding, recorded because it will recur:** **the repository has no test that asserts what the deployed worker consumes.** Every module that adds a consumer from here on can ship the same defect, and the file that would catch it is the one no module owns. This test is Timeline's half; **a repository-wide version belongs to QE**, and is raised as [C-301](LANE_COORDINATION.md) with four concrete validation rules. **The lesson is written into the module's design document** — [45-timeline.md §4](architecture/45-timeline.md) — so the next lane assigned Timeline reads it where entries are explained rather than in a bug register.

---

### B-022 · `make certify` inherits the database environment, and silently measures less when it is absent

| | |
|---|---|
| **Module** | Repository tooling — `Makefile`, the `certify` target |
| **Current assignee** | **none — not assignable.** [C-010](LANE_COORDINATION.md), and the fourth defect to land in that gap |
| **Severity** | 🟠 — the gate reports a number that looks like a regression and is actually a misconfiguration. **It does not fail; it under-measures** |
| **Status** | **`FIXED`** — QE, 2026-08-03, **by removal rather than by care** (RE-03). **`VERIFIED` is another lane's** |
| **Found** | 2026-08-02, by QE, certifying `c3435a0` — it cost two full gate runs before the cause was clear |

**Steps to reproduce.** From a shell without the lane database variables:

```bash
make certify
#   pytest              2238 passed          ← 110 fewer than the suite has
#   coverage            94.34%               ← below the 95% floor
#   security-invariants 337 invariants       ← 17 fewer
#   scenario            164 assertions       ← 15 fewer
#   NOT CERTIFIED
```

Then, same commit, same tree, with the three variables [`RUNNING.md`](RUNNING.md#running-a-lane) requires:

```bash
export SIGNORA_TEST_APP_DATABASE_URL=… SIGNORA_TEST_ADMIN_DATABASE_URL=… SIGNORA_DATABASE_URL=…
make certify
#   pytest 2348 · coverage 95.57% · 354 invariants · 179 assertions · CERTIFIED
```

**Expected.** A gate either runs or refuses to run. **`make certify` has no options, deliberately** (§20e) — *"a mode that skipped a gate would produce a run that cannot certify, and a command whose convenient path yields worthless evidence teaches people to use it."* An environment that silently deselects 110 tests is exactly that mode, arrived at by omission.

**Actual.** The target is `cd backend && SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 uv run python -m tests.certification` — it sets one variable and inherits three. Without them the database-backed tests deselect, and **every gate reports a smaller, plausible number.** Nothing says *"the database was not reachable"*; it says `NOT CERTIFIED · coverage 94.34% is below 95.0%`, which reads as a coverage regression somebody introduced.

**Why it is worth a row rather than a note to self.** This is the failure mode §2 names directly: **the repository asserted something untrue about itself, in the one artifact whose entire purpose is being trustworthy.** The misconfigured run wrote a manifest entry recording `commit c3435a0 · coverage 94.34 · tree_clean true` — a measurement of a broken instrument, indistinguishable to every future reader from a measurement of the repository. That entry was discarded and this row is what replaces it; **the finding is durable, the false number is not.**

**And the part that makes this worth acting on rather than re-documenting.** [`REPOSITORY_RELEASE_CHECKLIST.md`](REPOSITORY_RELEASE_CHECKLIST.md) **already carries the warning**, in bold, directly above the `make certify` line, with measured evidence from earlier the same day: *"the same commit certified 2223/94.36% against the shared default and 2325/95.59% against the lane's own database. A gate pointed at the wrong database is not a gate."*

**QE read that checklist, wrote that warning, and still ran the gate wrong** — because the variables were exported in one shell and `make certify` was invoked from another. **A rule that its own author violates within hours, while looking at it, is not a rule that needs restating; it is a rule that needs replacing with a check.** The fix is a preflight in the target, not a stronger sentence in the runbook.

**Fix.** Make the target fail loudly when the variables are absent, rather than proceeding with a partial selection — a preflight that asserts reachability and exits non-zero with the missing variable named. **Do not fix it by hardcoding a lane's database into the `Makefile`**: the file is shared, and every lane has its own (`RUNNING.md` § *Running a lane*).

**Second-order finding, and the more interesting one.** The first run left `certification/manifest.json` modified, which made the tree dirty, which failed the *next* run's cleanliness check — so one misconfiguration cost two runs rather than one. **The certification record lives in the tree it certifies.** That is precisely the assumption [ADR-0039](architecture/adr/0039-release-engineering-model.md) §II-3.2 identifies as the root of the divergence chain, arriving here as an ordinary operational nuisance. **It is evidence for that ADR, not a reason to act on it** — recorded and left alone, per the governance bar.

**Recovered 2026-08-02, by an audit of the register.** This row was written at Closeout `7a08922`, reached `main`, and then **vanished from both branches** — removed without record when `integration` was rebased in the following cycle. **Nobody noticed; an audit found it.** That is the point: a defect that leaves the register is indistinguishable from one that was never reported. Same failure mode as [B-017](BUGS.md), now applied to the register that exists to prevent it.

---

### Closed 2026-08-03 by RE-03 — the input no longer exists

**This row predicted a class and then produced an instance of it.** An attempt record written by `make certify`, before the first gate:

```
"test_database": "(unset — defaults to shared)"
```

**That is this bug observed rather than reasoned about**, and the direction was the alarming one: the run that certified was the lucky one.

**`make certify` now creates `signora_certify_<commit>`, migrates it to head, runs every gate against it, and drops it in a `finally`.** The same field, one cycle later:

```
"test_database": "signora_certify_630fc79b7d3f"
```

**Fixed by removal, not by discipline.** There is no longer a variable to forget — the environment is constructed by the run rather than inherited from the shell that launched it. **The workstation may affect execution speed; it can no longer affect execution correctness.**


### B-026 · The repository does not own its line endings, and depends on every contributor's git config

| | |
|---|---|
| **Module** | Repository configuration — a missing `.gitattributes` |
| **Current assignee** | **none — not assignable.** [C-010](LANE_COORDINATION.md) |
| **Severity** | 🟡 — **latent, not active.** Nothing is broken today; the exposure is real and cheap to close |
| **Status** | `OPEN` |
| **Found** | 2026-08-02, by QE, investigating a suspected line-ending problem at the product owner's request |

**First, the honest correction.** **There is no CRLF problem in this repository today**, and QE did not report one. The investigation was asked for on the assumption that a CRLF observation had been made; it had not. What the investigation *did* find is the condition that would produce one.

**Measured.**

```bash
ls .gitattributes                              # No such file
git config --get core.autocrlf                 # unset
git ls-files --eol | awk '{print $1}' | sort | uniq -c
#   824 i/lf        ← every text file is LF in the index
#   102 i/none      ← binary
```

**Expected.** A repository states its own line-ending policy, so that a clone behaves identically on Linux, macOS, WSL and Windows regardless of who configured what.

**Actual.** **No `.gitattributes` exists.** Normalisation depends entirely on each contributor's `core.autocrlf`, which on this workstation is unset — and unset is only safe *because the workstation is Linux*. **A Windows contributor with git's default `core.autocrlf=true` would commit CRLF into `infra/smoke.sh` and `infra/disaster-recovery.sh`**, and a shell script with CRLF line endings fails with `bad interpreter: /bin/bash^M` — an error that names neither the file's real problem nor the machine that caused it.

**Why it matters more here than in most repositories.** Under [ADR-0027](architecture/adr/0027-local-first-development.md) **the local run is the only run**, and `smoke.sh` and `disaster-recovery.sh` are two of the gates that decide whether anything ships. **A line-ending accident in those two files disables certification for whoever receives it**, with a message that reads like a broken interpreter rather than a checkout artifact.

**Smallest sufficient fix, recommended and deliberately not implemented.** A single `.gitattributes` at the repository root:

```gitattributes
* text=auto eol=lf
*.sh text eol=lf
*.png binary
*.jpg binary
*.ico binary
```

`* text=auto eol=lf` makes the repository — not the contributor — the authority: LF in the index and LF in every working tree. The explicit `*.sh` line is redundant under it and is kept because **the two files whose corruption would be most expensive should be the two nobody has to reason about.**

**Why the repository should own this rather than documenting it** (§2): a rule kept by every contributor configuring their client correctly is a rule that will be broken by the first person who does not, and the failure lands on somebody else's machine. **This is convention replaced by enforcement**, which is the substitution the repository already prefers everywhere else.

**Scheduled, not deferred indefinitely** (product owner, 2026-08-02). **Apply during a maintenance cycle when no feature branch is open** — the fix is a content no-op today, but `.gitattributes` changes how git *normalises* on checkout, and landing it while two lanes hold long branches invites merge churn for no benefit. **The board shows when that window is open:** every lane `AVAILABLE`.

**One caveat for whoever implements it.** Adding `.gitattributes` to a repository that is already uniformly LF is a no-op for content — verified above, 824 of 824 text files are already `i/lf` — so **no renormalisation commit is needed and none should be made.** If that ever stops being true, `git add --renormalize .` is the mechanism, and it must be its own commit.


### B-024 · The credential store that must not be readable has no tests at all

| | |
|---|---|
| **Module** | `integrations` · `timeline` |
| **Current assignee** | **Lane B**, feature lead for both |
| **Severity** | 🟠 — it rejected a Release Candidate, and one file of it is security-relevant |
| **Status** | **`FIXED`** — Lane B, 2026-08-02. All four named files at **100%**; three real defects came out from under it. **`VERIFIED` is QE's to set** |
| **Found** | 2026-08-02, by QE, certifying `9ba0ea6` — **the candidate was rejected and abandoned** |

**Steps to reproduce.**

```bash
cd backend && uv run pytest --cov -q
# FAIL Required test coverage of 95.0% not reached. Total coverage: 94.79%
# 2460 passed          ← every test passes; nothing is broken
uv run coverage report --skip-covered --sort=miss | tail -8
```

**Expected.** Coverage at or above the 95% floor.

**Actual.** **94.79%**, and the gap is concentrated in the two newest modules:

| File | Cover | Missed |
|---|---|---|
| `modules/integrations/infrastructure/secrets.py` | **0%** | **34** |
| `modules/integrations/infrastructure/repository.py` | **35%** | 26 |
| `modules/timeline/interface/handlers.py` | **0%** | 11 |
| `modules/timeline/infrastructure/repository.py` | **52%** | 9 |
| `modules/integrations/application/queries.py` | 90% | 8 |

**88 of the repository's 491 missed statements — 18% — sit in two modules built in the last two days.**

**The percentage is the least interesting part of this row.** `secrets.py` is **0% covered**, and the commit that introduced it is titled *"a credential that is not readable"*. **A guarantee about credential confidentiality that no test exercises is a guarantee nobody has checked** — §11 requires the failure paths, and §2 is explicit that a guard which cannot fail is documentation pretending to be code. `timeline/interface/handlers.py` at 0% is the module's event-consumption path, which is how every entry it will ever hold gets there.

**This was predicted, and the prediction is in the record.** Coverage fell 95.57 → 95.37 → 95.19 → 95.16 across four cycles, and cycle 15's Closeout stated the failure mode exactly: *"the next sizeable slice lands the repository below the floor, and a candidate is rejected for coverage rather than for a defect."* **The gate did its job.**

**Second rejection, 2026-08-02 — candidate `a2ca53d`, and nothing moved.** M13-S05, M13-S06 and the M13 module review landed on `integration` in between and **touched no backend file**: the frontend suite grew 511 → 595, the backend stayed at 2460 and coverage stayed at **94.79%**, to the statement.

```
modules/integrations/infrastructure/secrets.py     34  34   0%   ← unchanged
modules/integrations/infrastructure/repository.py  43  26  35%   ← unchanged
modules/timeline/interface/handlers.py             11  11   0%   ← unchanged
modules/timeline/infrastructure/repository.py      21   9  52%   ← unchanged
```

**The `tests/integrations/` files are not new.** `test_connection.py` arrived with S01, `test_queries.py` with S02, `test_connect.py` with S04 — all before the first rejection. **No test has been added against any of the four files above since this row was opened.**

**Two candidates have now been rejected for one unfixed defect.** `9ba0ea6` and `a2ca53d`, both abandoned, both correctly. **Nothing on `integration` can certify until these four files are covered**, which is the shared-base pattern again — now at **three occurrences**, counting [B-023](BUGS.md).

### Candidate `d758754` — NOT CERTIFIED, 2026-08-02

| | |
|---|---|
| **Release Candidate** | ❌ **NOT CERTIFIED.** **Disposition: permanently abandoned** — `d758754` will never be promoted to `main` |
| **Implementation** | **IN PROGRESS — not rejected.** Lane B's work stands and moved the number. The resulting commits form a **new** candidate; **no implementation effort is discarded** |
| **Next action** | **Lane B** — cover `modules/timeline/interface/handlers.py`, push. **QE pins and certifies the new snapshot immediately** |

### Third rejection, and it is 0.02% away

**Real progress, and the number says so.** `secrets.py` went **0% → 61%** (34 missed → 12); the suite grew 2460 → 2476; coverage moved **94.79% → 94.98%**. Lane B did the work this row asked for.

**It is short by 0.02 percentage points — roughly three statements.** Two files carry what remains:

| File | Cover | Missed | |
|---|---|---|---|
| `modules/timeline/interface/handlers.py` | **0%** | **11** | **Covering this file alone clears the floor with room to spare** |
| `modules/integrations/infrastructure/repository.py` | 35% | 26 | The larger gap, and not needed to certify |

**`timeline/interface/handlers.py` is the recommendation, and not because it is the cheapest.** It is the module's **event-consumption path** — the route by which every entry Timeline will ever hold arrives. **It has never been executed by a test**, and Timeline is already promoted and on `main`.

**Three candidates now rejected on this row** — `9ba0ea6`, `a2ca53d`, `d758754` — all abandoned, all correctly. **The trend is toward resolution rather than away from it**, which is why this is a progress note rather than a second escalation.

### Escalation — 2026-08-02

**This defect has now blocked two consecutive certification cycles and is a repository bottleneck.**

| | |
|---|---|
| **Cycles blocked** | **2** — cycle 16 (`9ba0ea6`) and cycle 17 (`a2ca53d`), both rejected and abandoned |
| **Work waiting** | **9 commits on `integration`** cannot promote · **25 commits on `lane-a-product-surface`** sit behind the same base, **none of which touch `integrations` or `timeline`** |
| **Owner** | **Lane B**, feature lead for both modules |
| **Progress** | **None measurable.** Between the two rejections Lane B shipped M13-S05, M13-S06 and the M13 module review — **all frontend and documentation, no backend file touched.** The four named files are unchanged to the statement |
| **Is it a bottleneck?** | **Yes.** Two lanes' finished work is unreleasable, and the repository has not promoted since `3451f8b` |

**Recorded, not editorialised.** Lane B may have reasons for the sequencing that QE cannot see, and finding a defect outside one's assignment is an obligation to report rather than a licence to prioritise somebody else's queue. **What QE will not do is normalise the repetition:** a second identical rejection is reported as an escalation, not as *"candidate rejected again."*

**Not to be fixed by lowering the floor**, and not by adding assertions that execute lines without testing behaviour. The two 0% files are the work; the percentage follows.

### Fix — Lane B, 2026-08-02

**QE's escalation was accurate and its last sentence was the important one.** The percentage was never the defect; the two 0% files were. **Three real defects were sitting under them, and every one would have reached a customer.**

| # | Defect | Why no existing test could see it |
|---|---|---|
| 1 | **Every connection insert would have failed.** `connected_account.created_by` and `updated_by` are `NOT NULL`; nothing supplied them. **The first customer to connect anything would have hit it** | Every repository test used a fake, and **a fake cannot refuse an insert** |
| 2 | **The write order violated the foreign keys.** `ConnectSystem` wrote credential material before the connection it references. Both `integration_secret` and `integration_grant` have an FK to `connected_account` | Same — the doubles accepted any order, and one unit test *asserted* the wrong one |
| 3 | **`ConnectionNotFound` escaped as a `500`.** It had no entry in the central error mapping, so a caller naming another organization's connection was told the platform had broken rather than being refused | No test had ever called the route with a connection id it could not see |

**Fixes.** `ConnectedAccount` and `IntegrationGrant` gain a required `actor_id` with **no default** — the rule `next_state` already follows — which makes `ConnectInput.actor_id` load-bearing after four slices of being declared and never read, and answers *"who disconnected our CRM?"* at the only moment the answer exists. `created_by` is never reassigned on update, so a later disconnection cannot destroy the record of who connected it. The write order is now connection → material → grant → connection, with the row landing in `AUTHORIZING` first, which **preserves the property the old ordering was protecting**: a partial failure leaves *"you started this and did not finish"*, never *Ready to use* over a credential that does not exist. `modules/integrations/interface/errors.py` maps `ConnectionNotFound` to **404, never 403**.

**Tests — 42 added, all against real PostgreSQL as `signora_app`:**

| File | What it proves |
|---|---|
| `tests/integration/test_integrations_persistence.py` | A connection survives the schema · who connected it is not overwritten by who disconnected it · the unique identity constraint is live · **the material is not what lands in the column** · a rotated key refuses rather than resolving to something · purging actually removes it · another organization's credential is invisible under RLS |
| `tests/integration/test_timeline_persistence.py` | The projection path end to end · redelivery losing the race against a unique index · **ties broken identically by PostgreSQL and by the cursor** — the unit suite pages against a fake that reimplements the same rule, so only the database can prove they agree |
| `tests/integration/test_api_connections.py` | Authorization at the route: a member may read and **may not** disconnect · 404-never-403 · the disconnect names its caller · nothing is advertised as `connectable` before it is |

**Measured on the fixed tree**, `HEAD` of `lane-b-commercial-profile`:

```
2518 passed        (was 2460, then 2476)
Required test coverage of 95.0% reached. Total coverage: 95.69%     (was 94.79%, then 94.98%)
```

| File | Before | After |
|---|---|---|
| `modules/integrations/infrastructure/secrets.py` | **0%** | **100%** |
| `modules/integrations/infrastructure/repository.py` | 35% | **100%** |
| `modules/timeline/interface/handlers.py` | **0%** | **100%** |
| `modules/timeline/infrastructure/repository.py` | 52% | **100%** |

`mypy --strict` clean · `lint-imports` 34 kept, 0 broken · frontend `tsc` clean, 616 tests.

**The general lesson, recorded because it will recur:** a fake that reimplements a rule can only ever agree with itself. Where the rule lives in the database — a constraint, an ordering, a keyset predicate, RLS — the test has to be there too. Written up in [44-integrations.md §10](architecture/44-integrations.md).

### B-025 · A coverage failure is reported as a test failure, and names the wrong gate

| | |
|---|---|
| **Module** | Repository tooling — `backend/tests/certification/` |
| **Current assignee** | **none — not assignable.** [C-010](LANE_COORDINATION.md) |
| **Severity** | 🟡 — diagnosis only; the certification decision was correct |
| **Status** | `OPEN` |
| **Found** | 2026-08-02, by QE, reading the rejection of `9ba0ea6` |

**Steps to reproduce.** Certify a commit whose coverage is below the floor.

```
❌ pytest — 2457 passed
❌ smoke  — 3 stages in 93s
Coverage 94.79%

Why this run does not certify
  · gate 'pytest' failed: 2457 passed        ← reads as a test failure
  · coverage 94.79% is below 95.0%           ← the actual cause
```

**Expected.** A failing gate names what actually failed (§10, *failure attribution must be truthful* — *"an incorrect attribution is worse than none, because it misdirects the investigation"*).

**Actual.** `pytest` is invoked with `--cov`, so `--cov-fail-under` makes it exit non-zero when coverage is short. The harness reads the exit code and marks the **pytest** gate failed, printing *"2457 passed"* as its reason — **a failure message whose entire content is a success count.** The same defect is then reported twice, once under a name that is not responsible.

**It cost real time here.** The first reading was *"three tests are failing"* — 2460 in a direct run against 2457 here — and diagnosing that took a second full suite run to establish that **nothing was broken at all.**

**Fix.** Either run coverage as its own gate and drop `--cov-fail-under` from the pytest invocation, or report the pytest gate as passed-with-coverage-short. **Do not merely reword the message**: the gate is currently wrong about which component failed, not just unclear.


### B-027 · The connect screen promises a disconnect that does not exist

| | |
|---|---|
| **Module** | `integrations` — `frontend/components/integrations/connect-panel.tsx` |
| **Current assignee** | **Lane B**, M13's owner |
| **Severity** | 🟠 — **the product asserts a capability it does not have**, to a customer who is deciding whether to trust it with their CRM |
| **Status** | **`FIXED`** — Lane B, 2026-08-02. Disconnect is a lifecycle, not a button; all three gaps closed. **`VERIFIED` is QE's** |
| **Found** | 2026-08-02, by Lane B, in M13's end-to-end module review — **in its own slice** |

**Steps to reproduce.** Open the connect panel for any system. Read the section headed *If you change your mind*:

> *"You can disconnect {name} at any time from this page. Signora stops reading from it immediately."*

**Expected.** A way to disconnect.

**Actual.** There is none. `ConnectionState.DISCONNECTED` exists, `UNUSABLE_STATES` contains it, the query layer treats it as *not broken*, and the Connection Center renders it as *Turned off* — and **no use case transitions to it.** `grep` for a caller finds only comments.

**This is the principle Lane B proposed in [C-017](LANE_COORDINATION.md) violated by Lane B's own copy**: *a surface never advertises a capability the system cannot execute*. It is the more embarrassing kind of instance — the sentence exists precisely to reduce a customer's hesitation before they commit, so it is doing persuasive work that the product cannot back.

**Two related gaps found in the same review, recorded here rather than as separate rows** because one fix closes all three:

**`EncryptedSecretStore.purge_for` is never called.** It exists so that disconnecting removes credential material rather than merely forgetting the pointer — which is the compliance finding from M13's own architecture review, arriving as unreached code.

**`SecretUndecryptable` is raised and never caught.** A rotated or wrong key surfaces as an unhandled exception rather than as a connection a customer is told to reconnect.

**The fix, for whoever takes it — which is Lane B.** A `DisconnectSystem` use case transitioning to `DISCONNECTED`, revoking the grant, calling `purge_for`, and an endpoint plus a control behind it. **The copy is not the thing to change**: the promise is the right promise, and the product should keep it.

### Fix — Lane B, 2026-08-02

**The copy was not changed.** The promise was right; the software now keeps it.

| | |
|---|---|
| **Verification performed** | The disconnect lifecycle against the conditions that make it matter, not the path where everything works |
| **Result** | **`PASS`** — 436 tests including the full Security Invariants suite, 76 of them this module's |
| **Commands executed** | `pytest tests/security_invariants tests/integrations` · `mypy --strict` · `lint-imports` · OpenAPI route check |
| **Lifecycle** | **Not advanced.** `VERIFIED` is QE's |

**Three rules, each because the obvious implementation gets it wrong.**

**A vendor cannot block a disconnect.** Revocation is attempted, its failure recorded, never propagated. Withdrawing access is what somebody does *in a hurry* — a disconnect that failed because HubSpot was down would hold a security action hostage to the system it protects them from. Tested with a revoker that raises.

**Material is destroyed, not orphaned.** `purge_for` is called unconditionally, so *"Signora can no longer read from this"* is true rather than believed.

**It is idempotent.** A second disconnect is a customer clicking twice; it changes nothing and does not move the first one's record.

**`NoRevoker` reports failure rather than success**, because claiming a revocation that never happened would tell a customer their access was withdrawn at the vendor while the credential is still live there — the more dangerous of the two lies. The response carries `revoked_at_provider` so the screen can say so.

**`SecretUndecryptable` now subclasses `SecretNotFound`**, and resolution raises `CredentialUnreadable`. A rotated key and a purged secret are the same fact above the adapter — *this connection has to be made again* — which is something a customer can act on, unlike a stack trace.

### A lifecycle gap the fix's own tests found

**An abandoned half-finished connection could not be disconnected.** `AUTHORIZING` permitted only `CONNECTED` and `NOT_CONNECTED`, so a customer who closed the tab mid-flow had a row reading *Not finished* that nothing could clear. Found by a parameterised test asserting every state can be left, not by reading the table — **which is the argument for that test existing.**

---

### B-023 · `tsc --noEmit` fails on the Timeline feed tests, and the suite that passes cannot see it

| | |
|---|---|
| **Module** | `timeline` — `frontend/tests/components/timeline-feed.test.tsx` |
| **Current assignee** | **Lane B**, Timeline's feature lead |
| **Severity** | 🟠 — a stated Completion gate fails on `integration`. **Two characters to fix; it is blocking four finished slices** |
| **Status** | **`FIXED`** — Lane B, 2026-08-02. A narrowing guard, not a cast; all four gates re-run. **`VERIFIED` is QE's to set** |
| **Found** | 2026-08-02, by QE, validating snapshot `7df2073` at lifecycle stage 1 |

**Steps to reproduce.**

```bash
cd frontend && npx tsc --noEmit
# tests/components/timeline-feed.test.tsx(79,19): error TS2345:
#   Argument of type 'HTMLElement | undefined' is not assignable to 'HTMLElement'.
# tests/components/timeline-feed.test.tsx(80,19): error TS2345: (same)
```

**Expected.** `tsc --noEmit` clean. It is named in `CLAUDE.md` §20e *Completion* step 2 — *"its module suite, impacted integration tests, `mypy --strict`, `lint-imports`, frontend suite, production build"* — and in *Which gates run when* for both the lane's hand-off and QE's validation.

**Actual.** `screen.getAllByRole('listitem')` returns `HTMLElement[]`, and under `noUncheckedIndexedAccess` the elements `items[0]` and `items[1]` are `HTMLElement | undefined`. `within()` will not take that.

**Fix.** Assert the shape the test already depends on — the two `listitem` elements it just rendered — rather than widening a type. A local `const [first, second] = screen.getAllByRole('listitem')` with an explicit `expect(first).toBeDefined()`, or an index guard, keeps the test honest about what it is asserting.

**Why the other gates missed it, which is the part worth keeping.** **Vitest passed — 488 tests, including these two — and `npm run build` passed.** Vitest transpiles without full type checking, and the Next.js production build type-checks *application* sources rather than the test tree. **So the only gate that can see this class of defect is the one that was run last**, and a lane running its suite and its build would reasonably believe it was green.

**Not a governance proposal, an observation for the record** (governance is frozen, and this has happened once): the lane-side gate list and the order it is run in are what caught this, and they caught it only at QE. If it recurs, the cheap structural answer is that `tsc` runs *before* the suite rather than after, so the fast feedback comes first.

**Escalated 2026-08-02: it is not blocking one candidate, it is blocking the pipeline.**

### Fix — Lane B, 2026-08-02

| | |
|---|---|
| **Verification performed** | The four Completion gates, re-run in full |
| **Result** | **`PASS`** — `tsc --noEmit` clean · 488 frontend tests · `eslint` clean · production build clean |
| **Commands executed** | `npx tsc --noEmit` · `npx vitest run` · `npx eslint tests/components/timeline-feed.test.tsx` · `npm run build` |
| **Environment** | Lane B clone, rebased on `integration` |
| **Lifecycle** | **Not advanced.** `VERIFIED` is QE's |

**A guard that narrows, not a cast.** `expect(first).toBeDefined()` satisfies a reader and narrows nothing — TypeScript does not learn from a matcher — so it would have needed `!` beside it, which is a type escape wearing an assertion's clothes. `if (!first || !second) throw` narrows properly, states what the test already depends on, and fails with a readable message if the feed ever renders no rows.

**QE's diagnosis of why the other gates missed it is correct, and Lane B can add the specific error.** The gates were run in the order they are listed, and `tsc` was run **before** this test file existed — the component was type-checked, the test was added afterwards, and only Vitest and the build ran again. Both pass: Vitest transpiles without type-checking and the Next.js build type-checks application sources rather than the test tree.

**So the ordering observation is right and the mechanism is narrower than a habit:** any gate run before the last file is written is a gate that did not run. Re-running the full set at hand-off is what catches it, and that is what was skipped here.

The defect is on `integration`, and **every branch cut from `integration` inherits it.** Verified:

```bash
git show origin/lane-a-product-surface:frontend/tests/components/timeline-feed.test.tsx | sed -n '79p'
#   expect(within(items[0]).getByText(...))     ← the same two lines
```

**Lane A's six unrelated slices — PS-01, PS-02, PP-01, PP-02, PP-04, PP-05 — cannot certify either**, and nothing in them touches Timeline. A two-character type error in one lane's test file is holding two lanes' finished product work.

**This is the clearest evidence the repository has produced for [ADR-0039](architecture/adr/0039-release-engineering-model.md) §II-2, assumption 2** — *validation happens after merge* — and for what that assumption costs. A candidate validated **before** entering the shared line fails alone; a defect that reaches the shared line **fails everything downstream of it, forever, until somebody fixes it.** Recorded as evidence. **Not acted on** — the ADR is a north star, the governance bar is unmet at one occurrence, and the fix here is Lane B's.

| | |
|---|---|
| **Module** | Repository tooling — `Makefile`, the `certify` target |
| **Current assignee** | **none — not assignable.** [C-010](LANE_COORDINATION.md), and the fourth defect to land in that gap |
| **Severity** | 🟠 — the gate reports a number that looks like a regression and is actually a misconfiguration. **It does not fail; it under-measures** |
| **Status** | `OPEN` |
| **Found** | 2026-08-02, by QE, certifying `c3435a0` — it cost two full gate runs before the cause was clear |

**Steps to reproduce.** From a shell without the lane database variables:

```bash
make certify
#   pytest              2238 passed          ← 110 fewer than the suite has
#   coverage            94.34%               ← below the 95% floor
#   security-invariants 337 invariants       ← 17 fewer
#   scenario            164 assertions       ← 15 fewer
#   NOT CERTIFIED
```

Then, same commit, same tree, with the three variables [`RUNNING.md`](RUNNING.md#running-a-lane) requires:

```bash
export SIGNORA_TEST_APP_DATABASE_URL=… SIGNORA_TEST_ADMIN_DATABASE_URL=… SIGNORA_DATABASE_URL=…
make certify
#   pytest 2348 · coverage 95.57% · 354 invariants · 179 assertions · CERTIFIED
```

**Expected.** A gate either runs or refuses to run. **`make certify` has no options, deliberately** (§20e) — *"a mode that skipped a gate would produce a run that cannot certify, and a command whose convenient path yields worthless evidence teaches people to use it."* An environment that silently deselects 110 tests is exactly that mode, arrived at by omission.

**Actual.** The target is `cd backend && SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 uv run python -m tests.certification` — it sets one variable and inherits three. Without them the database-backed tests deselect, and **every gate reports a smaller, plausible number.** Nothing says *"the database was not reachable"*; it says `NOT CERTIFIED · coverage 94.34% is below 95.0%`, which reads as a coverage regression somebody introduced.

**Why it is worth a row rather than a note to self.** This is the failure mode §2 names directly: **the repository asserted something untrue about itself, in the one artifact whose entire purpose is being trustworthy.** The misconfigured run wrote a manifest entry recording `commit c3435a0 · coverage 94.34 · tree_clean true` — a measurement of a broken instrument, indistinguishable to every future reader from a measurement of the repository. That entry was discarded and this row is what replaces it; **the finding is durable, the false number is not.**

**And the part that makes this worth acting on rather than re-documenting.** [`REPOSITORY_RELEASE_CHECKLIST.md`](REPOSITORY_RELEASE_CHECKLIST.md) **already carries the warning**, in bold, directly above the `make certify` line, with measured evidence from earlier the same day: *"the same commit certified 2223/94.36% against the shared default and 2325/95.59% against the lane's own database. A gate pointed at the wrong database is not a gate."*

**QE read that checklist, wrote that warning, and still ran the gate wrong** — because the variables were exported in one shell and `make certify` was invoked from another. **A rule that its own author violates within hours, while looking at it, is not a rule that needs restating; it is a rule that needs replacing with a check.** The fix is a preflight in the target, not a stronger sentence in the runbook.

**Fix.** Make the target fail loudly when the variables are absent, rather than proceeding with a partial selection — a preflight that asserts reachability and exits non-zero with the missing variable named. **Do not fix it by hardcoding a lane's database into the `Makefile`**: the file is shared, and every lane has its own (`RUNNING.md` § *Running a lane*).

**Second-order finding, and the more interesting one.** The first run left `certification/manifest.json` modified, which made the tree dirty, which failed the *next* run's cleanliness check — so one misconfiguration cost two runs rather than one. **The certification record lives in the tree it certifies.** That is precisely the assumption [ADR-0039](architecture/adr/0039-release-engineering-model.md) §II-3.2 identifies as the root of the divergence chain, arriving here as an ordinary operational nuisance. **It is evidence for that ADR, not a reason to act on it** — recorded and left alone, per the governance bar.

---

### B-021 · The coordination register's `Closed` section holds only open items, and every closed one sits above it

| | |
|---|---|
| **Module** | **none** — [`LANE_COORDINATION.md`](LANE_COORDINATION.md) |
| **Current assignee** | **QE**, at the next cycle's stage-3 reconciliation — the register is QE's to reconcile at merge |
| **Severity** | 🟠 — two tools report *"3 closed"*, and the true figure is *"0 closed, 2 answered and misfiled"* |
| **Status** | **`FIXED`** — QE, 2026-08-02. By the time it was fixed the heading sat above **five** open items, not three. **Awaiting verification by a lane other than QE** |
| **Found** | 2026-08-02, by QE, reading C-020 and noticing it was filed under `Closed` while marked `OPEN` |

**Steps to reproduce.**

```bash
awk '/^## C-/{i=$0} /^\| \*\*Status\*\*/{print i" -> "$0}' docs/LANE_COORDINATION.md
python3 infra/kpi.py | grep Coordination      # 18 · 3 closed
```

**Expected.** Items under `## Closed` are closed. `state-check` and `kpi` both count *"items appearing after the `## Closed` heading"*, so that heading is load-bearing.

**Actual.** The section is inverted. **The three items below `## Closed` — C-015, C-017, C-020 — are all `OPEN`**, including the one blocking all of M7. **The two carrying `ANSWERED` — C-001, ratified as ADR-0036, and C-016 — are above it.** Lanes append new items at end of file, which has been past the heading since it was introduced.

**Consequence beyond the count.** The rule this heading serves is *"a register that only grows has become the discussion log it is not allowed to be"* — and `state-check` only fires that finding when **zero** items are closed. Three phantom closures have kept it silent across every cycle since. **A check whose input is wrong is not a check** (§2).

**Fix.** Move `## Closed` to end of file and relocate C-001 and C-016 beneath it. **Deliberately deferred to the next cycle rather than done now**: Lane A's branch adds 196 lines to this file, and reordering it today would hand that lane a conflict for no gain. It is reconciled where reconciliation belongs — stage 3, with the lane's changes in hand.

---

### B-020 · `state-check` reads a task id anywhere in a board row, including the explanation of why a lane *cannot* take it

| | |
|---|---|
| **Module** | Repository tooling — `infra/state-check.py`, rule 5c(a) |
| **Current assignee** | **Lane B**, inside [TASK-005](BACKLOG.md) — that task is *"`state-check` learns the backlog"*, and this is the same code |
| **Severity** | 🟡 — advisory output only, but it is the failure mode that teaches people to ignore an advisory |
| **Status** | **`FIXED`** — Lane B, in [TASK-005](BACKLOG.md) (`8da47b5`). **The register lagged the fix; corrected 2026-08-02** during a Lane B ownership audit. **`VERIFIED` is QE's to set** |
| **Found** | 2026-08-02, by QE, writing a board row that explained which tasks Lane B could **not** claim |

**Steps to reproduce.** Put a task id in a row's `Next action` cell for a lane that does not hold it, then:

```bash
python3 infra/state-check.py
#  ·  TASK-002 is claimed by Lane A and Lane B at once.
```

**Expected.** A task is *claimed* by the lane whose **`Task` column** names it.

**Actual.** `board_rows` scans the entire line — `re.findall(r"\bTASK-(\d+)\b", row)` — so a row saying *"Lane A holds TASK-002, which is why I am idle"* registers as a competing claim. The contested-claim check then fires on the one arrangement it should read as correct.

**Fix.** Read the `Task` column only: split the row on `|` and take the second field, exactly as the lane name is already taken from the first. The prose in the remaining cells is explanation, not assertion.

**Why it is worth fixing rather than working around.** The board's own rule is *"a row names a `TASK-nnn`"* precisely so that *"are these the same task?"* is a fact. **A checker that punishes precise prose pushes rows toward vague prose**, which costs the board the property the ids were introduced to give it — and today's workaround was exactly that: the ids were removed from Lane B's cell to silence a check that was wrong.

### Fix — Lane B, `8da47b5`. The register lagged it; audited and corrected 2026-08-02.

**Fixed as written**, inside TASK-005 and in the same code. `_board_claims` reads **`cells[2]` — the `Task` column — and nothing else**, so prose in `Next action` is explanation rather than assertion, which is what the bug asked for.

**Regression test:** `backend/tests/test_claim_agreement.py::TestTheBoardIsReadByColumn::test_a_next_action_referencing_another_task_is_not_a_claim`, which is the reported reproduction verbatim — a `CLAIMED` row for `TASK-005` whose `Next action` reads *"blocked behind TASK-009"*. 16 tests in the file, all passing.

**Verified from the original steps rather than the diff**, using the exact arrangement the report describes — a row saying *"Lane A holds TASK-002, which is why I am idle"*:

```
board claims: {'002': {'Lane A'}, '005': {'Lane B'}}
contested   : none
```

**Why this row stayed `OPEN` for a day after being fixed, recorded because it is the interesting part.** TASK-005's commit carried the fix and its test but **did not update this row**, because the row is filed under repository tooling and the task was filed under `state-check`. **A defect and the task that fixes it are not the same record**, and closing one does not close the other — which is precisely the gap a per-lane ownership audit exists to catch, and the reason this one is now part of Lane B's routine before starting new work.

---

### B-019 · The constitution's branch table now says two different things about `integration`

| | |
|---|---|
| **Module** | **none** — `CLAUDE.md`, on `lane-a-product-surface` only. It has not reached `main` |
| **Current assignee** | **Lane A**, to remove during the B-018 rebase — it is that lane's edit |
| **Severity** | 🟠 — a governing rule that contradicts itself is followed differently by two readers |
| **Status** | **`VERIFIED`** — QE, 2026-08-02, reproduced from the original steps rather than the diff: the duplicate row is gone and the survivor is the correct one, retaining the claim-commit exception. **The `BACKLOG.md` half remains the product owner's** |
| **Found** | 2026-08-02, by QE, reading `16896ca` during validation |

**Steps to reproduce.**

```bash
git show origin/lane-a-product-surface:CLAUDE.md | grep -c '^| `integration` | Permanent'
# 2
```

**Expected.** One row per branch in the *Branches and promotion* table. **Truth has exactly one authoritative representation** (§2).

**Actual.** `16896ca` **appended** revised `integration` and `lane-*` rows instead of replacing the originals, so the table carries both. They disagree on the rule that matters most: the surviving original says *"a lane may fast-forward `integration` with a claim-only commit — that is the arbitration point, and it is the only exception"*, and the addition says *"**QE only.** A lane rebases and pushes."* **The first is correct and load-bearing** — it is what makes the Task Claim Protocol atomic, and `certification-guard.py --audit-claims` enforces it. The second would silently disable claim arbitration.

**Fix.** Keep the original `integration` row verbatim, including the claim-commit exception. Keep the *new* `lane-*` row, which is the one this refinement actually changed. Delete the other two.

**The finding underneath it, and it is larger than the table.** `CLAUDE.md` is 🔴 in the Change Budget and *"Product owner"* in *Shared files have one owner*, and `16896ca`, `f262d2c` and `835388f` wrote 74 lines of it from a feature lane. **The content is not the problem** — it matches what the product owner has since ratified, and *Continuous execution* is a genuine improvement. **The concurrency is:** two sessions editing the constitution on separate branches produced a contradiction that neither could see, and no gate reads that file.

**The same branch does it a second time, in [`BACKLOG.md`](BACKLOG.md).** `f28792d` **inserts two new `READY` tasks** — TASK-018 and TASK-019, PP-02 and PP-03 — and moves TASK-015 out of `BLOCKED`. The rule is explicit: *"a lane never reorders, reprioritizes, removes, or inserts `READY` work without the product owner"*, and *"a lane writes **only** its claim"*. **Again the content looks right**: all three derive from the ratified [ADR-0036](architecture/adr/0036-target-account-contract.md), and TASK-015's unblocking is argued rather than waived — its blocker is being built by the same lane in the same effort.

**Both need the product owner, not QE.** Either the rows are ratified where they stand, or Lane A withdraws them and they are re-entered by their owner. **QE will not decide it**, and will not certify the branch while it is undecided — a lane that can add its own `READY` work has taken priority, however good the work is.

---

### B-018 · Lane A's branch carries two of Lane B's pre-rebase commits and will not fast-forward

| | |
|---|---|
| **Module** | **none** — repository process. The affected branch is `lane-a-product-surface` |
| **Current assignee** | **Lane A** — it is that lane's rebase, and §20e reserves conflict resolution to the lane that is rebasing |
| **Severity** | 🟠 — four finished slices, two of them executable and substantial, cannot be validated |
| **Status** | **`FIXED`** — Lane A, 2026-08-02. `git merge-base --is-ancestor origin/integration HEAD` now exits 0, and neither `a599201` nor `945e120` appears in `git log origin/integration..HEAD`. **QE verifies; the reporting lane does not close its own row** |
| **Found** | 2026-08-02, by QE, taking `1a348ef` into lifecycle stage 1 |

**Steps to reproduce.**

```bash
git fetch origin
git merge-base --is-ancestor origin/integration origin/lane-a-product-surface   # exit 1
git log --oneline origin/integration..origin/lane-a-product-surface | tail -2
#   945e120 M7 returns to WAITING, and Lane B rescans rather than waits
#   a599201 Claim M7 — Timeline, and why it cannot start
```

**Expected.** A branch handed to QE fast-forwards onto `integration` (§20e, *Completion* step 3: the lane rebases and resolves its own conflicts).

**Actual.** The branch's merge base with `integration` is `f80f57d` — a `main` commit from an earlier Closeout — and it carries **two commits that belong to Lane B**: `a599201` and `945e120`, the M7 claim and its release. Both are already on `integration` under different hashes (`4c4b0d3`, `0a86d7a`), rebased there when QE integrated them. Replaying the branch therefore replays two commits whose content is already present, and `a599201` conflicts in [`ACTIVE_ASSIGNMENTS.md`](ACTIVE_ASSIGNMENTS.md) and [`LANE_COORDINATION.md`](LANE_COORDINATION.md).

**The fix is two commands, and it is Lane A's.**

```bash
git checkout lane-a-product-surface
git rebase origin/integration      # git skips 945e120 automatically
git rebase --skip                  # a599201 — Lane B's, already on integration
```

**Then re-run the gates on the rebased branch** (*Completion* step 4 — rebasing changes the program), push, and set the row back to `IN VALIDATION`. **The implementation area does not move**: Product Surface and Provider Platform stay with Lane A throughout.

**Two findings worth carrying, both larger than the rebase.**

**One — a lane branch acquired another lane's commits.** It happened at `6eb8cb0`, where Lane A branched from a point that already held Lane B's unrebased claim rather than from `integration`. Startup step 1 exists to prevent exactly this, and the cost is invisible until the branch is handed over — nothing fails while the lane is working. **Worth checking at push time rather than at merge time**, which is a `state-check` rule somebody could write.

**Two — this is what the certified-commit rule looks like from the other side.** QE rebases lanes onto `integration` at merge, so a lane branching from another lane's *pre-merge* commit is building on a tree that will never exist again. **Branch from `integration`, always** — never from another lane's branch, however current it looks.

---

### B-017 · A lane's merged slice disappeared from `integration`, and the backlog reoffers it

| | |
|---|---|
| **Module** | **none** — repository process |
| **Current assignee** | **none — not assignable.** [C-010](LANE_COORDINATION.md) |
| **Severity** | 🟠 — work was lost from the integration line, and the queue now offers a task that was built |
| **Status** | `OPEN` |
| **Found** | 2026-08-02, by Lane B, on the startup workflow for its next assignment |

**Steps to reproduce.** On `integration` at `f80f57d`:

```bash
git merge-base --is-ancestor 9c32daa origin/integration   # exit 1
grep -c "5d — the collision" infra/state-check.py          # 0
ls backend/tests/test_claim_collisions.py                  # No such file
```

**Expected.** `9c32daa` — *TASK-005, state-check reads the claims that have not merged yet* — was committed, pushed to `lane-b-commercial-profile`, and fast-forwarded onto `integration` (`c8a16c0..9c32daa`). It should be on `integration` or deliberately superseded with that recorded.

**Actual.** It is on neither. `integration` was rebuilt: Lane B's two TASK-001 commits were **rebased** and survive as `a062adf` and `cc9a320`, and the **two TASK-005 commits were dropped** — the claim (`626e343`) and the implementation (`9c32daa`). Nothing records the decision.

**Nothing is unrecoverable.** `9c32daa` is intact on `origin/lane-b-commercial-profile` and, incidentally, on `origin/lane-a-product-surface`, which rebased onto it.

**Why it is worth a row rather than a shrug.** [`BACKLOG.md`](BACKLOG.md) now reads `TASK-005 · READY`, with the note *"what remains is the id-level checking"* — **which is what `9c32daa` implemented, with twelve tests.** The next lane to run the Task Claim Protocol will claim it and build it again. That is the duplicate implementation the protocol exists to prevent, arriving through the register instead of through a race.

**It may well have been deliberate, and that is the point.** QE's `e1d2fa6` fixed the same problem better — claims now go to `integration`, which is the option Lane B recommended first in its own C-019 — and with claims in one place a cross-branch detector is largely redundant. **If TASK-005 was superseded, the defect is only that nothing says so**: a lane cannot tell a supersession from a lost commit, and the two call for opposite responses.

**For whoever takes it.** Decide TASK-005's real state and record it: `DONE` (superseded, with `e1d2fa6` named), or `READY` with `9c32daa` cherry-picked back, or `READY` with its note corrected so it no longer asks for work that exists. **Also worth a rule:** when a Closeout rebuild drops a lane's commit, the drop is named in the Closeout message — the rebuild is legitimate, the silence is not.

---


### B-015 · The certification audit passes vacuously in every lane's clone

| | |
|---|---|
| **Module** | **none** — repository process, `infra/certification-guard.py` |
| **Current assignee** | **none — not assignable.** [C-010](LANE_COORDINATION.md), and this is a fifth defect in that gap |
| **Severity** | 🟠 — **the audit reports success while examining nothing.** No history is wrong today; the check that would notice is inert wherever a lane runs it |
| **Status** | **`FIXED`** — QE, 2026-08-02. **Awaiting verification by somebody other than QE** |
| **Found** | `a9cc204`, by Lane B while verifying [B-014](#b-014--two-commits-reached-main-outside-certification-and-nothing-noticed) under [TASK-001](BACKLOG.md) |

**Steps to reproduce.** From any feature lane's clone, on a lane branch:

```bash
python3 infra/certification-guard.py --audit-main
```

**Expected.** The 12 commits promoted since ratification are audited, as they are when the same logic runs against the ref holding the promoted history.

**Actual.**

```
audit — no commit has been promoted since the rule was ratified.
```

**Exit code `0`.** Nothing was examined and the run reports success.

**The cause is one word.** [`certification-guard.py:162`](../infra/certification-guard.py#L162) resolves the range `f"{RULE_RATIFIED_AT}..main"`, and `main` is the **local** ref. Line 165 does the same for `_is_ancestor(c, "main")`.

**A feature lane's local `main` is always stale, by design.** A lane never checks out `main` and never promotes to it — QE does, on its own clone. This clone's `main` sits at `f996a42`, **35 commits behind `origin/main`**, and `f996a42..` contains none of the promoted work, so the range is empty and the audit short-circuits on `if not commits`.

**Proof it is the ref and not the history.** The same script with `main` → `origin/main`, changed nowhere else, reports `12 commit(s) … 0 violations. The guarantee holds.` The audit is correct; it is pointed at the wrong ref.

**Why it is worth a row.** This is the failure mode [B-014](#b-014--two-commits-reached-main-outside-certification-and-nothing-noticed)'s own text names — *a guard that cannot fail is documentation pretending to be code* — reappearing one level up. The guard **can** fail, and does when it sees the real history; but every lane that runs it as documented gets a green result that means nothing, and a green result is the one nobody investigates. It is **Decorative Logic** in the sense `CLAUDE.md` §2 defines: removing the check would not change the property it appears to protect, for the people most likely to run it.

**The fix, for whoever takes it.** Resolve the promoted ref explicitly rather than trusting a local branch name — `origin/main`, or a `--ref` argument, or `git rev-parse --verify` on both and prefer the one that is ahead. **And make the empty range loud rather than silent:** *"no commit has been promoted"* and *"the ref you gave me has no promoted commits on it"* are different facts, and today they print the same sentence and the same exit code. The second should be an error.

**Not fixed here.** `infra/` has no assignable lane ([C-010](LANE_COORDINATION.md)) and Lane B is verifying, not fixing. Reported rather than repaired, which is the correct alternative to touching another owner's file.

---

### B-016 · The documented startup command reads a key file nothing creates

| | |
|---|---|
| **Module** | repository documentation — [`docs/RUNNING.md:54`](RUNNING.md) |
| **Current assignee** | **QE** — `RUNNING.md` is QE's (`CLAUDE.md` §20e) |
| **Severity** | 🟡 — the API still starts; the key is silently empty, and the symptom appears later as *"signed in, every screen empty, everything 401s"* |
| **Status** | **`FIXED`** — QE, 2026-08-02. **Awaiting verification by somebody other than QE** |
| **Found** | `a9cc204`, by Lane B while verifying [B-009](#b-009--the-documented-command-for-starting-the-api-cannot-start-the-api) under [TASK-001](BACKLOG.md) |

**Steps to reproduce.** From a fresh clone, follow [`RUNNING.md`](RUNNING.md) exactly: `cp backend/.env.example backend/.env`, `npm install`, `npm run keys:generate`, `make demo`. Then copy the documented backend command, which contains:

```bash
SIGNORA_JWT_PUBLIC_KEY="$(cat .dev-keys/public.pem)" \
```

**Expected.** The public key, as the preceding steps produced it.

**Actual.** `cat: .dev-keys/public.pem: No such file or directory`, and `SIGNORA_JWT_PUBLIC_KEY` is set to the **empty string**. The API starts anyway — `Application startup complete` — so nothing announces the problem at the moment it is caused.

**`.dev-keys/` is never created by anything in this repository.** It appears exactly once, in that command. [`frontend/scripts/generate-keys.ts`](../frontend/scripts/generate-keys.ts) does not write PEM files — it prints `SIGNORA_JWT_PRIVATE_KEY=` and `SIGNORA_JWT_PUBLIC_KEY=` lines to paste into `frontend/.env.local` and `backend/.env`, which is what the setup step above tells the reader to do. **The command is a leftover from a file-based mechanism that no longer exists.**

**The sharp edge, and it is stated as an inference rather than a measurement.** The reader has just pasted the correct key into `backend/.env`. An environment variable set on the command line takes precedence over a `.env` value in pydantic-settings, so **the documented command plausibly overrides a correctly configured key with an empty one** — turning a working setup into the 401 symptom that [`RUNNING.md:203`](RUNNING.md) already has a troubleshooting row for. **Lane B did not verify the override**, only that the file is absent and the variable ends up empty. Confirming it is the fix's first step.

**The fix, for whoever takes it.** Delete the `SIGNORA_JWT_PUBLIC_KEY` line from the command block — the key is already in `backend/.env` by then, which is the mechanism `keys:generate` actually implements. **Same class as [B-009](#b-009--the-documented-command-for-starting-the-api-cannot-start-the-api), in the same command block:** *"every command below is copy-pasteable from a fresh clone"*, and one line of it is not.

**Fixed 2026-08-02.** The line is gone from the command block, with a comment beside it saying why it is absent — the key reaches the backend through `backend/.env`, which is the mechanism `keys:generate` actually implements. **`.gitignore` gains `*.pem` and `.dev-keys/`** so that a reader who creates the directory by hand, as Lane B did while verifying, cannot commit a private key. **Lane B's inference about the override was not tested by QE either**, and the fix does not depend on it: a variable read from a file that does not exist is wrong regardless of precedence.

**A second, smaller note for the same fix.** `.gitignore` covers `.env` and `.env.*` but has **no entry for `.dev-keys/` or `*.pem`**. Nothing creates that directory today, so nothing is at risk — but a reader who takes the command literally and creates it by hand, as Lane B did while verifying, ends up with an **RSA private key as an untracked, unignored file**. If the command block keeps any reference to a key directory, the ignore rule belongs with it (`CLAUDE.md` §13).

---

### B-002 · `make smoke` cannot run while any dev server is up

| | |
|---|---|
| **Owner** | Lane QE |
| **Severity** | 🟡 |
| **Status** | `OPEN` |
| **Found** | `73d1c28` |

**Steps to reproduce.** Start `npm run dev` (port 3000). Run `make smoke`.

**Expected.** Either a green run, or a failure that names the cause.

**Actual.** `✗ stack did not reach healthy` at stage 2. The real cause — `failed to bind host port 0.0.0.0:3000: address already in use` — is only visible in `docker compose logs`, and the reported message sends the reader looking at the application.

**Why it matters more now.** With three lanes there are more dev servers running more of the time, and `make smoke` is a QE gate on `integration`. Documented in `docs/RUNNING.md`; the honest fix is a preflight port check in `infra/smoke.sh`, which is QE's own file.

---

### B-003 · A lane following `RUNNING.md` exactly cannot run its own suites

| | |
|---|---|
| **Owner** | Integrator — `docs/RUNNING.md` |
| **Severity** | 🟡 |
| **Status** | `OPEN` |
| **Found** | `960b604`, by Lane B at the start of a slice |

**Steps to reproduce.** Follow [RUNNING.md § Running a lane](RUNNING.md#running-a-lane) exactly — export `SIGNORA_TEST_APP_DATABASE_URL` and `SIGNORA_TEST_ADMIN_DATABASE_URL`, nothing else. Then run the impacted suites the way §20e requires during a slice: `cd backend && uv run pytest tests/<module>`.

**Expected.** The suite runs against the lane's own database.

**Actual.** Every test errors in setup with `RuntimeError: This suite TRUNCATES every table after each test. Set SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1…`, and `tests/integration` additionally fails to **collect** — `test_worker_retry.py` builds `Settings()` at import time and raises a Pydantic `ValidationError` without `SIGNORA_DATABASE_URL`.

**Why it is a documentation defect rather than a code one.** Both variables are correct and deliberate — the truncation guard exists because the invariants once emptied a real stack. They are documented in `docs/SESSION_HANDOFF.md` §Local prerequisites and set by `make test`. But **a lane does not run `make test`** (it truncates the wrong database and §20e forbids repository-wide gates during a slice), and `RUNNING.md` is the document a lane is told is authoritative for its environment. The two disagree, and the lane-facing one is the incomplete one.

**The fix, for whoever takes it.** Add both to step 2 of § Running a lane, beside the two already there. No code change:

```bash
export SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1
export SIGNORA_DATABASE_URL=postgresql+asyncpg://signora_app:signora_app_local_dev@localhost:5432/signora_lane_<x>
```

**Not a defect, checked while reproducing:** Redis needs no per-lane database. `RUNNING.md` already states *"one Postgres, one Redis, many databases — nothing in the test path touches Redis today"*, and that is still true.

---

### B-004 · `provider_watermark` cannot tell two target accounts apart

| | |
|---|---|
| **Owner lane** | **Lane A** |
| **Affected module** | `provider_platform` — `provider_watermark`, migration `0007` |
| **Severity** | 🟠 unreachable today · 🔴 the moment a workspace watches two accounts |
| **Status** | **`FIXED`** — Lane A, **PP-01**, migration `0029` (renumbered twice on rebase, from `0026` then `0027`). `subject` joined the unique constraint and the lookup; **PP-02 built the consumer in the same effort**, so the *Fix belongs to* condition below was satisfied rather than waived. **QE verifies** |
| **Found** | `f6b6a41`, while answering [`C-001`](LANE_COORDINATION.md#c-001--the-target-account-contract) |
| **Fix belongs to** | The slice that builds the `target_accounts_changed` consumer. **Not to be fixed opportunistically** — the consumer is what makes it reachable, and fixing one without the other leaves a schema change nothing exercises |

**Trigger conditions.** All three must hold, and none does yet:

1. Commercial Profile publishes a target-account list with **two or more entries** in one workspace (M12.5 slice 5);
2. Provider Platform consumes it and runs a sync **per subject** (Lane A, unbuilt);
3. A second sync runs for the same `(provider, capability)` in that workspace — that is, the **second account is fetched at all**.

**Steps to reproduce.** Not reproducible today, and the reason is the interesting part: `RunProviderSync` has accepted a `subject` since M2.1 and **nothing has ever supplied one** except the Provider Simulation Framework, which drives every subject through one scenario without ever re-reading a watermark between two of them. Once the trigger conditions hold: declare accounts *A* and *B*, sync *A*, then sync *B* against the same provider and capability.

**Expected.** Each watched account carries its own incremental position, so what has been fetched for *A* has no effect on what is fetched next for *B*.

**Actual.** `uq_provider_watermark_scope` is `(workspace_id, provider, capability)` — **there is no `subject` in the key, and none in the row.** One watermark covers every account in the workspace for that provider and capability. Syncing *A* advances the position that *B*'s next sync reads as its `since`, so *B* fetches only what changed after *A*'s run and **silently skips its own history**.

**Impact.** A customer sees one account richly enriched and another mysteriously thin, with **nothing in the product explaining the difference** — no error, no warning, no gap in the evidence drawer, because from the pipeline's point of view the provider simply returned little. It degrades every stage downstream: fewer claims, fewer observations, fewer business events, a lower buying score, and an account that looks genuinely quiet rather than under-fetched. **It is a data-completeness defect that presents as a commercial conclusion**, which is the worst way for one to present in this product.

The cost is also asymmetric: a full re-fetch after the fix recovers it, but every conclusion drawn in the meantime was drawn on partial evidence and was shown to a customer as though it were not.

**The fix, for whoever takes it.** `subject` joins the unique constraint and the lookup. The domain already carries the subject on every `ProviderRequest`, so nothing above the repository changes — it is a migration and a widened `where`. The same slice must build the consumer, per *Fix belongs to* above.


---

### B-005 · Removing a product locks the customer out of the ideal customer, committee and focus

| | |
|---|---|
| **Owner** | **Lane B** — `commercial_profile` (frontend) |
| **Severity** | 🟠 — wrong behaviour a customer would hit, with no way out through the product |
| **Status** | `FIXED` — awaiting QE. All three editors, one shared rule, and a mutation check |
| **Found** | `80d9511`, by Lane B in the slice-4 product review |

**Steps to reproduce.** Declare two products. Describe an ideal customer for both. Remove the second product from the catalog. Now edit the *first* product's ideal customer and save.

**Expected.** The edit saves. The removed product's profile is history, and history does not block a new declaration.

**Actual.** `422 icp_unknown_product` — *"you cannot describe who buys a product you have not said you sell"* — naming a product **that is no longer on the screen**. The customer cannot clear it either: the remove path re-sends the whole declaration too. **The section is unusable until the product is added back.**

**Why.** All three editors send *everything stored*, which is correct for a whole-statement `PUT`, and render only entries whose product is in the current catalog. The two diverge the moment a product is removed. The server is behaving correctly — the client is sending a declaration the customer cannot see.

**Observed, not inferred.** Rendering `IcpEditor` with a catalog of one product and a declaration holding two profiles — one for the surviving product, one for a removed one — then clicking *Remove the description for Revenue Cloud*:

```
ON SCREEN:            removed product NOT visible
SENT product_ids:     ["eeeeeeee-…"]      ← only the removed product's profile
SENT the removed one? true
```

The request the customer's click produces consists **entirely of a declaration for a product that no longer exists**. Their own edit is discarded from the payload and the invisible one is all that is sent, so the server refuses the whole request. It is not merely a confusing message: the visible work is dropped before it leaves the browser.

**Affects identically:** the ideal customer, the buying committee, and the focus.

**Fixed.** `components/commercial/catalog-scope.tsx` holds the rule once — *the catalog is the authority on which declarations still exist* — and all three editors read `kept` rather than what they were handed. An orphaned entry is **dropped and announced**: `DroppedWithTheirProduct` says it before the save, and says the version holding it is kept, because dropping it quietly would have been a second and quieter defect.

**Regression tests** in each editor's own suite, plus a **mutation check**: reintroducing the defect in `icp.tsx` alone makes `B-005 · is never sent back to the server` fail, and restoring it makes it pass. A guard that cannot fail is documentation pretending to be code.

---

### B-006 · Three of the four sections vanish silently when their query fails

| | |
|---|---|
| **Owner** | **Lane B** — `commercial_profile` (frontend) |
| **Severity** | 🟡 |
| **Status** | `FIXED` — awaiting QE. Page-level test, the same shape as D36's |
| **Found** | `80d9511`, by Lane B in the slice-4 product review |

**Steps to reproduce.** Make `GET /workspaces/{id}/icp` fail — stop the API after the catalog has loaded, or block the request.

**Expected.** A message saying the ideal customer could not be loaded, in the same words the catalog already uses: *a fault in Signora, not a missing declaration*.

**Actual.** The section is simply absent. The customer sees Products and nothing else, with no explanation — **an outage is indistinguishable from a feature they do not have.**

**Why.** `settings/products/page.tsx` renders each section on `data && <query>.data`, and only the catalog's `isError` produces copy. The other three queries' error states are never read.

**Fixed.** Each of the four sections reports its own failure through a page-local `CouldNotLoad`, in wording that distinguishes *Signora failed* from *you never declared one* and states that nothing has been lost.

**Regression test** is `frontend/tests/components/your-business.test.tsx` — **page-level deliberately**, because the defect never lived in a component and every component test passed throughout its life. The same reasoning as `first-run.test.tsx` and D36.

---

---

### B-007 · The migration runner locks one database and migrates another

| | |
|---|---|
| **Module** | **none** — `apps/migrate/` is composition-root production code |
| **Current assignee** | **none — not assignable.** See *[Defects in code that belongs to no module](#defects-in-code-that-belongs-to-no-module)* and [C-010](LANE_COORDINATION.md) |
| **Severity** | 🟠 — three tests fail on the documented setup path today; the split-brain case is latent |
| **Status** | `OPEN` |
| **Found** | `f996a42`, during the QE lane's first full-suite run |

**Steps to reproduce.** From a fresh clone, follow [`RUNNING.md`](RUNNING.md) exactly: `cp backend/.env.example backend/.env`, then `make test`.

**Expected.** A green suite. `backend/.env` is the documented way to configure the backend, and `SIGNORA_DATABASE_URL` is in `.env.example`.

**Actual.** Three failures in `tests/integration/test_migration_runner.py::TestConcurrencySafety`, all ending in `RuntimeError: SIGNORA_DATABASE_URL must be set to run migrations.` Exporting the same variable into the shell makes all three pass.

**The cause is one fact with two authorities.** `apps/migrate/main.py::_run_with_lock` takes the advisory lock on a connection built from `settings.database_url` — which pydantic-settings resolves from the environment **or `backend/.env`**. It then calls `_upgrade_to_head()`, which builds a fresh `Config("alembic.ini")` and lets [`migrations/env.py:57`](../backend/migrations/env.py#L57) resolve the URL again, from `os.environ` **only**. The settings object governs the lock; the environment variable governs the migration, and nothing reconciles them.

Three consequences, in ascending order of seriousness:

1. **Configured by `.env` alone** — the documented path — the lock is taken and the migration then fails.
2. **Configured by both, disagreeing** — which is exactly what a three-lane repository invites — the runner serialises on database A and migrates database B. The concurrency guarantee the module exists to provide is void, and silently.
3. **`SIGNORA_DATABASE_URL` is a third lane variable that [`RUNNING.md` § Running a lane](RUNNING.md#running-a-lane) does not mention.** It lists two. A lane that sets only those two runs these tests against whatever the shared default names.

**Why the suite has been green anyway.** `SESSION_HANDOFF.md` §1 documents the variable as a shell export, and every run so far has been from a shell that had it. Nothing asserts the two resolutions agree, so the day they disagree there is no test to notice.

**Half of this is now closed.** [`RUNNING.md` § Running a lane](RUNNING.md#running-a-lane) lists all three variables and says why the third cannot live in `backend/.env` (2026-08-01, product-owner direction). **The row stays `OPEN` because the defect is the code, not the documentation** — one fact still has two authorities, and documenting a trap is not removing it.

**For whoever takes it.** One authority. `_upgrade_to_head` should be handed the URL the lock was taken on rather than re-deriving it — `alembic.ini`'s `sqlalchemy.url` is settable from `Config` in-process. The regression test is the one this bug describes: set the two to different databases and assert the runner refuses rather than proceeds.

---

---

### B-008 · The suite says it truncates every table, and truncates five

| | |
|---|---|
| **Module** | shared test infrastructure — `backend/tests/conftest.py` |
| **Current assignee** | QE |
| **Severity** | 🟡 — no test is known to fail because of it; the false claim is the confirmed defect |
| **Status** | `OPEN` |
| **Found** | `f996a42`, during the QE lane's first full-suite run |

**Steps to reproduce.** Record `select count(*) from claim` in the target database. Run the suite. Record it again.

**Expected.** The number the suite started with. `require_explicit_consent_to_truncate` refuses to run at all unless you confirm the database is disposable, and the reason it gives is *"This suite TRUNCATES every table after each test."*

**Actual.** It grows, permanently. `signora_lane_qe` went from **1 row to 15,931** across one run, and `signora_lane_a` currently carries 22,795 rows of accumulated residue. `clean_database` truncates `membership, workspace, outbox_event, processed_event, dead_letter_event CASCADE` — **five of the schema's thirty-one tables** — and `membership` is the only table in the database with a foreign key to `workspace`, so `CASCADE` reaches nothing else.

**Why it matters, in order.**

1. **The claim is false where a developer reads it** — in the `RuntimeError` that gates the whole suite, and repeated in [`RUNNING.md`](RUNNING.md) (*"`make test` truncates every table in the same database"*). The practical advice there is still right for the wrong reason: truncating `workspace` does empty the Playground's screens.
2. **Residue is a hidden input** (`CLAUDE.md` §2). Every run starts from the accumulated state of every previous run. Tests pass today because each mints a fresh `workspace_id` and the queries are workspace-scoped — an accidental guarantee, not an enforced one.
3. Lane databases grow without bound.

**For whoever takes it.** Truncate the tables the suite actually writes, or state honestly what is cleaned and why the rest need not be. **Do not widen the truncation without running the suite twice in one database** — a test that has been passing on residue will fail, and that failure is the finding.

---

---

### B-009 · The documented command for starting the API cannot start the API

| | |
|---|---|
| **Module** | repository documentation — `docs/RUNNING.md`, `Makefile`, `README.md` |
| **Current assignee** | QE |
| **Severity** | 🟠 — it stopped a reviewer at the first step, and the error did not name the cause |
| **Status** | **`VERIFIED`** — QE, 2026-08-02, on Lane B's independent evidence below ([TASK-001](BACKLOG.md)). Fixed by the QE lane under product-owner direction, 2026-08-01 |
| **Found** | `f996a42`, QE lane, first attempt to start the product |

**Steps to reproduce.** Run `make demo`. Copy the command it prints — the same one in [`RUNNING.md`](RUNNING.md) lines 41 and 153:

```bash
cd backend && uv run uvicorn apps.api.main:app --reload --port 8000
```

**Expected.** A running API. `RUNNING.md` opens with *"Assume nothing is already running and nothing is already known. Every command below is copy-pasteable from a fresh clone."*

**Actual.**

```
ERROR:    Error loading ASGI app. Attribute "app" not found in module "apps.api.main".
```

`apps/api/main.py` exports **only the factory** `create_app(settings=None)`; there is no module-level `app`. The working invocation exists and is used everywhere a machine reads it — `backend/Dockerfile:78` and `infra/docker-compose.prod.yml:92` both say `apps.api.main:create_app --factory`. **Only the three places a human reads are wrong**, which is exactly why no gate catches it: `make smoke` starts the API from the container command.

Three sites: `docs/RUNNING.md:41`, `docs/RUNNING.md:153`, `Makefile:80`. `README.md` sends the reader to the first of them.

**Why it matters beyond the typo.** *Every completed slice is demoable by a non-engineer* is binding from M12.3 (`CLAUDE.md` §2), and the instructions for the demonstration do not work. A reviewer who has never seen this repository gets an ASGI import error and no route to the answer — the correct form is only discoverable by reading a Dockerfile.

**The fix.** `uv run uvicorn apps.api.main:create_app --factory --reload --port 8000`, in all three places. Verified working against the Playground during this review.

**The regression test.** `backend/tests/test_documented_commands.py` extracts every `apps.api.main:<target>` from `RUNNING.md`, the `Makefile`, the `Dockerfile` and `docker-compose.prod.yml`, and asserts each target exists on the real module and is invoked with `--factory` when it is one. **Proven to fail:** reintroducing `:app` in the `Makefile` produced `Makefile:80 tells a reader to start the API at 'apps.api.main:app', which does not exist`. A control test fails if the pattern ever stops matching, so the file cannot quietly become decoration.

**Two notes on the resolution, both deliberate.**

**When the fix was written the three sites were Integrator-owned**, and QE edited them under explicit product-owner direction. Later the same day the Integrator role was absorbed into QE and the files became QE's outright, so the exception is now moot — recorded because the sequence is the record, not because it is still needed.

**QE fixed this, so QE may not close it.** `VERIFIED` is set by someone else reproducing the original steps from a clean shell — not by reading the diff, and not by the lane that wrote the fix. **The role merge does not dissolve this rule**; it is the one place QE genuinely needs a second pair of eyes.

### Verification report — Lane B, 2026-08-02, [TASK-001](BACKLOG.md)

| | |
|---|---|
| **Verification performed** | Reproduce the documented startup from the original steps on a clone with no prior setup |
| **Result** | **`PASS`** |
| **Commands executed** | `cp backend/.env.example backend/.env` · the [`RUNNING.md:57`](RUNNING.md) command block verbatim · `curl localhost:8000/health` · `SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1 uv run pytest tests/test_documented_commands.py` |
| **Environment** | Lane B clone at `a9cc204`; Python tier local, PostgreSQL and Redis in Docker; no `backend/.env` and no `.dev-keys/` at the start |
| **Defects discovered** | [B-016](#b-016--the-documented-startup-command-reads-a-key-file-nothing-creates) — the same command block reads a key file nothing creates |
| **Lifecycle** | **Not advanced.** `VERIFIED` is QE's to set on this evidence |

**From the original steps, never from the diff.** This clone had no `backend/.env` and no `.dev-keys/`, so the starting point was genuinely the one a new reviewer has.

| Check | Result |
|---|---|
| `apps/api/main.py` exports a module-level `app` | **No** — parsed the module: `create_app` only. The original command would still fail, which is why the fix was to the documentation |
| The **documented** command from [`RUNNING.md:57`](RUNNING.md), copy-pasted with its env block | **Started.** `Application startup complete`, no `Error loading ASGI app` |
| `GET /health` | **`200`** · `{"status":"ok","environment":"local"}` |
| All five `apps.api.main:` sites agree | **Yes** — `RUNNING.md:57`, `RUNNING.md:187`, `Makefile:80`, `Dockerfile:78`, `docker-compose.prod.yml:92`, every one `create_app` with `--factory` |
| `backend/tests/test_documented_commands.py` | **11 passed** |

**One thing the verification hit that is not this bug.** The regression test errors with `RuntimeError: This suite TRUNCATES every table…` unless `SIGNORA_ALLOW_DESTRUCTIVE_TESTS=1` is set — **even though it touches no database**, being pure static analysis of documentation. A session-scoped fixture applies the guard to the whole suite. Harmless once known, and adjacent to [B-003](#b-003--a-lane-following-runningmd-exactly-cannot-run-its-own-suites). **Not opened as a defect** — the guard is correct and deliberately broad; recorded so the next person to run this file in isolation is not stopped by it.

---

---

### B-010 · Re-seeding the Playground orphans every narration, silently

| | |
|---|---|
| **Module** | the Playground — `backend/tests/playground/` · the *"stale versus absent"* half is the product surface |
| **Current assignee** | QE · Lane A for the brief half |
| **Severity** | 🟠 — M12.3's headline feature cannot be demonstrated at all |
| **Status** | `OPEN` |
| **Found** | `f996a42`, QE lane, first review pass over the Playground |

**Steps to reproduce.** `make demo-narrate`, confirm a brief narrates, then `make demo-seed`. Open any account brief.

**Expected.** *"Roughly ten of twelve accounts narrate"* ([RUNNING.md](RUNNING.md)), each with citations that open — the M12.3 slice.

**Actual.** `GET /workspaces/{w}/accounts/{a}/narration` returns **404 for all twelve**, measured 2026-08-01:

```
  ---> 0 of 12 accounts narrate
```

**And the narrations are not missing — they are orphaned.** `ai_narration` holds **748 rows** across **215 distinct subjects**, the newest written 2026-08-01 19:29, roughly an hour before this review. **Not one of them names a current account.** A re-seed mints new entity identifiers; a narration is an immutable historical fact keyed to the identifier it was written against, so it correctly survives and correctly stops resolving. Nothing says so on any screen or in any document.

**The same mechanism has left the Playground enormous.** `signora` carries **1,054,673 rows — 70,129 entities and 11,140 opportunities for a twelve-account demo.** Seeding clears the same five tables [B-008](#b-008--the-suite-says-it-truncates-every-table-and-truncates-five) describes and leaves every derived generation behind. The Playground is a haystack containing the demo.

**For whoever takes it.** Three separable pieces, and the first is worth doing alone:

1. **Say so.** `demo-narrate` must follow *every* `demo-seed`, not just the first. That is a `RUNNING.md` line, and QE's to write.
2. **The brief should distinguish *not narrated yet* from *narrated against evidence that no longer resolves***. The dialog already refuses to present today's facts as the ones the model saw ([D42](architecture/39-product-review-findings.md)); this is the same honesty one level up, and it is Lane A's.
3. **Do not "fix" it by deleting narrations.** A materialized AI artifact is a historical fact and is immutable (`CLAUDE.md` §2). The residue is a seeding question, not a retention one.

**Piece 2 is delivered — Lane A, `PS-02`, 2026-08-02.** `NarrativeBlock` now separates three states that were one blank space: **never written** (`notNarrated`, a 404 answered as an answer), **the request failed** (`isError`), and **narrated against evidence that no longer resolves** (`stranded` — `evidence_unchanged` false with no facts resolving), which is the state this row describes. In the third, the explanation moves onto the panel itself, because every citation renders as a plain count rather than a button and **the dialog that would explain why has no way to be opened**.

**Pieces 1 and 3 remain QE's**, and the row stays `OPEN` for them. **A lane closing a row on the strength of its own half is how a half-fixed defect gets forgotten.**

---

---

### B-014 · Two commits reached `main` outside certification, and nothing noticed

| | |
|---|---|
| **Module** | **none** — repository process |
| **Current assignee** | **none — not assignable.** [C-010](LANE_COORDINATION.md) |
| **Severity** | 🟡 — the changes were small, reviewed and correct; **the process gap is the defect** |
| **Status** | **`VERIFIED`** — QE, 2026-08-02, on Lane B's independent evidence below ([TASK-001](BACKLOG.md)), both cases. The rule that prevents it is enforced by `infra/certification-guard.py`; [B-015](#b-015--the-certification-audit-passes-vacuously-in-every-lanes-clone) should be read before it |
| **Found** | `e44819b`, by `certification-guard.py --audit-main` on its first run — **against the commits QE had just written** |

**Steps to reproduce.** `python3 infra/certification-guard.py --audit-main`, with `RULE_RATIFIED_AT` set to the certified commit `f669172`.

**Expected.** Every commit on `main` is certified, or changes nothing executable.

**Actual.** Two Closeout commits — `b5cc283` and `e44819b` — each modified `infra/state-check.py`, which is executable code, while carrying a Closeout message. **They were promoted without passing through certification at all**, because Closeout runs after promotion by design.

**Why it happened, and why it is worth a row.** The commit-binding rule did not exist when they were written; under the previous reading, certification bound to a *tree* and Closeout was documentation. `state-check.py` was edited during Closeout because that is when its defect was found, which felt like documentation work and was not. **A repository-wide gate is exactly the kind of thing that gets edited at the moment it is being used**, so this will recur unless something refuses it.

**The fix is the rule.** `CLAUDE.md` §20e now binds certification to an immutable commit, and `certification-guard.py --audit-main` proves that every commit on `main` since ratification is either certified or **verifiably** docs-only — a fact about paths, not about the commit message. `infra/` is deliberately **not** in the permitted set: `smoke.sh`, `disaster-recovery.sh` and the compose files decide whether a gate passes.

**For whoever verifies it.** Run the audit; it must report zero violations. Then edit `infra/state-check.py`, commit it to `main` with a Closeout message, and confirm the audit refuses it. **A guard that cannot fail is documentation pretending to be code**, and this one was written by finding a real violation on its first run.

### Verification report — Lane B, 2026-08-02, [TASK-001](BACKLOG.md)

| | |
|---|---|
| **Verification performed** | The audit against the promoted history, **and a deliberate violation to prove the guard can refuse one** |
| **Result** | **`PASS`** on both cases — 0 violations on real history; `REFUSED` with exit `1` on the probe |
| **Commands executed** | `python3 infra/certification-guard.py --audit-main` · in a throwaway clone: `git branch -f main 2c35d86`, an edit to `infra/state-check.py`, `git commit -m "Repository Closeout — a probe that must be refused"`, the audit again |
| **Environment** | A **throwaway clone** under the session scratchpad, deleted afterwards. **The probe was never committed to this repository and never pushed** |
| **Defects discovered** | [B-015](#b-015--the-certification-audit-passes-vacuously-in-every-lanes-clone) — the audit examines nothing, and reports success, wherever a lane runs it |
| **Lifecycle** | **Not advanced.** `VERIFIED` is QE's to set, and B-015 should be read first |

**Both halves run, and the negative case is the one that matters.** The violation was committed in a **throwaway clone** under the session scratchpad, never in the working repository and never pushed; the clone was deleted afterwards.

| Case | Result |
|---|---|
| **Positive** — audit against the promoted `main` (`2c35d86`) | **12 commits since ratification · 0 violations.** 4 certified · 7 inside a certified snapshot · 1 Closeout. *"The guarantee holds"*, exit `0` |
| **Negative** — `infra/state-check.py` edited, committed to `main` with a Closeout subject | **`REFUSED — 1 commit(s) reached main uncertified`**, naming the commit and the offending path, **exit `1`** |

**The guard can fail, and does.** It identified `infra/state-check.py` as executable despite the Closeout message, which is the precise distinction the fix exists to draw — a fact about paths, not about the commit subject.

**The claim in this row is therefore true**, and the property it asserts about `main` holds today.

> **But the verification also found the guard reporting a clean pass while examining nothing** — see **[B-015](#b-015--the-certification-audit-passes-vacuously-in-every-lanes-clone)**. That is a new defect in the fix's *reliability*, not a retraction of the fix: the guarantee above was confirmed by running the same logic against the ref that actually holds the promoted history.

---

### B-013 · The worker and the relay cannot start from a production image

| | |
|---|---|
| **Module** | **none** — `apps/worker/` is composition-root production code, plus `backend/pyproject.toml` |
| **Current assignee** | **none — not assignable.** [C-010](LANE_COORDINATION.md) |
| **Severity** | 🔴 — **two of the six production services crash-loop.** Nothing deployed would process an event |
| **Status** | **`VERIFIED`** — QE, 2026-08-02, on Lane B's independent evidence below ([TASK-001](BACKLOG.md)). Fixed by QE under product-owner direction, 2026-08-02 |
| **Found** | `3f4e988`, by QE at lifecycle stage 1, the first `make smoke` run since 2026-07-31 |

**Steps to reproduce.** `make smoke`.

**Expected.** Twenty-one stages green.

**Actual.** `✗ relay is 'restarting', expected running` at stage 2. Both the worker and the relay restart forever:

```
File "/app/apps/worker/subscriptions.py", line 27, in <module>
    import httpx
ModuleNotFoundError: No module named 'httpx'
```

**The cause is one line in the wrong list.** `httpx>=0.27` is declared in `[dependency-groups].dev` of [`backend/pyproject.toml`](../backend/pyproject.toml), and [`backend/Dockerfile:40`](../backend/Dockerfile#L40) installs with `uv sync --locked --no-dev`. **Production code imports it at module scope** — `apps/worker/main.py:15` and `apps/worker/subscriptions.py:27`, and every AI Platform adapter besides. It is a runtime dependency that has always been classified as a test one; nothing noticed because the API imports it lazily and **the worker had no module-scope import until `subscriptions.py` arrived**.

**Why no test caught it.** Every suite runs in the dev environment, where `httpx` is present — it is what `pytest` uses for the API client. **Only `make smoke` builds the production images**, and `make smoke` had not run since 2026-07-31: it was blocked on this workstation first by a missing `make` ([B-011](#b-011--make-is-not-installed-on-this-workstation--not-a-repository-defect)) and then by a dev server holding port 3000 ([B-002](#b-002--make-smoke-cannot-run-while-any-dev-server-is-up)).

**This is what [B-012](#b-012--main-was-advanced-by-a-merge-commit-through-a-github-pull-request) cost, made concrete.** The change reached `main` through a pull request rather than through the lifecycle, so the gate that exists to catch exactly this never ran. **The defect is not that somebody wrote the import; it is that the promotion skipped stage 1.**

**For whoever takes it.** Move `httpx` from `[dependency-groups].dev` into `[project].dependencies`, `uv lock`, rebuild. It is not a new dependency — it is an approved one filed under the wrong heading, so this is a classification fix rather than an adoption ([ADR-0024](architecture/adr/0024-code-quality-and-static-analysis.md) is untouched). **The regression test is `make smoke` itself**, which is now the only thing that proves the production image can start — and it must run before every promotion, which is lifecycle stage 1.

**Fixed 2026-08-02.** `httpx>=0.27` moved into `[project].dependencies` with the reason recorded beside it, `uv lock` re-run, and **`make smoke` passes end to end — 21 stages, 125s**, having failed at stage 2 immediately before. Not a new dependency and no ADR required: it was an approved one filed under the wrong heading. **QE applied it under explicit product-owner direction**, because `apps/` and `pyproject.toml` have no assignable lane ([C-010](LANE_COORDINATION.md)) — and **QE may not verify its own fix.**

### Verification report — Lane B, 2026-08-02, [TASK-001](BACKLOG.md)

| | |
|---|---|
| **Verification performed** | A full `make smoke` run — the regression test this bug names as its own |
| **Result** | **`PASS`** — `PLATFORM SMOKE TEST PASSED`, 128s, 24 stage headings, zero failures |
| **Commands executed** | `bash infra/smoke.sh` |
| **Environment** | Lane B clone at `a9cc204`; production images built from the tree; ports 3000 and 8000 confirmed free first; `make` absent ([B-011](#b-011--make-is-not-installed-on-this-workstation--not-a-repository-defect)) |
| **Defects discovered** | None |
| **Lifecycle** | **Not advanced.** `VERIFIED` is QE's to set on this evidence |

**The regression test for this bug is `make smoke` itself**, as the fix says, so the verification is a full run from the original step. `make` is absent on this workstation ([B-011](#b-011--make-is-not-installed-on-this-workstation--not-a-repository-defect), `WONTFIX`), so it ran as `bash infra/smoke.sh` — the same script the target invokes.

**`PLATFORM SMOKE TEST PASSED` — 128s, 24 stage headings, zero failures.**

| The stage that failed before | Result |
|---|---|
| Stage 1 — images | ✓ API, worker, relay and frontend images built |
| **Stage 2 — startup** | ✓ **No `relay is 'restarting'`.** This is the exact assertion that failed |
| Stage 12 — event bus, relay, workers | ✓ workers consuming without error · ✓ **relay running without error**, having survived the database restart in stage 6 |
| Stage 15 — Security Invariants | ✓ 354 passed against the running stack |

**The two services that crash-looped now start from a production image and process events**, which is the property the bug says was broken. Nothing was read from the diff: the run builds the images from the tree and starts them.

---

### B-012 · `main` was advanced by a merge commit through a GitHub pull request

| | |
|---|---|
| **Module** | **none** — repository process, not code |
| **Current assignee** | **none — not assignable.** The process is the product owner's and QE's; see [C-010](LANE_COORDINATION.md) |
| **Severity** | 🟠 — no code is wrong; the repository's history and its stated invariant disagree |
| **Status** | `FIXED` — the branches were reconciled 2026-08-02. **Awaiting verification by someone other than QE** |
| **Found** | `d54f55b`, by QE while beginning a promotion |

**Steps to reproduce.** `git log --format='%h %p %s' -1 main` at `d54f55b`.

**Expected.** One parent. `CLAUDE.md` §20e: *"Fast-forward only, everywhere. No merge commits. `main` advances only from `integration`."*

**Actual.** Two parents — `d54f55b` is *Merge pull request #1 from GaneshDabhade/integration*, created on GitHub at 04:09 on 2026-08-02.

**What it cost.** `integration` then advanced three commits without the merge, so **`main` stopped being an ancestor of `integration`** and no fast-forward was possible in either direction. The next promotion could not have happened without either a second merge commit or a rewrite — which is exactly the state the fast-forward rule exists to prevent. It also crossed [ADR-0027](architecture/adr/0027-local-first-development.md): GitHub is version control, backup and future collaboration, and **a `git push` performs one action**. A pull request is a workflow, and the workflow is local.

**The reconciliation.** On the product owner's direction, **`integration` was rebased onto `main`** (`e1a34a6 053aa70 4d5f19f` → `bdb014f 5b1e388 3f4e988`) and force-pushed. `main`'s history was left untouched, including the merge commit — *correct a claim about the present; date a record of the past*. Lanes A and B rebase onto the new `integration` at their next startup, which their startup sequence already requires.

**Why it stays open as a record.** The merge is still in `main`'s history and always will be. This row is what explains it to whoever finds it, and the fix is procedural: **`main` moves by `git merge --ff-only` from `integration`, run locally by QE, and by nothing else.**

### Verification — Lane B, 2026-08-02. **Evidence only; the status is deliberately unchanged**

**This row is in the same condition as the three in [TASK-001](BACKLOG.md) — `FIXED` by QE, awaiting somebody else — but the task names three, and a lane does not widen `READY` work.** So the checks were run and recorded; **setting the status is left to the product owner or QE.**

| Check | Result |
|---|---|
| Merge commits on `main` since the reconciliation (`e44819b..origin/main`) | **None.** History is linear |
| `origin/main` and `origin/integration` related by fast-forward | **Yes** — `integration` is exactly 1 ahead, and that one is this task's claim commit |

**The reconciliation held**, and the condition that made the next promotion impossible is gone. The merge commit itself remains in history, as this row says it always will.

---

### B-201 · `state-check` reads the history table as a second claim

> **Renumbered from `B-017` by QE at merge, 2026-08-02.** `B-017` was already allocated to a different finding; the later claim moves, and Lane A's block is `200`+ (`CLAUDE.md` §20e). **The original `B-017` is untouched.**

| | |
|---|---|
| **Module** | Repository tooling — `infra/state-check.py` |
| **Current assignee** | **Lane B** — it holds [TASK-005](BACKLOG.md), which added this check and is `IN VALIDATION` |
| **Severity** | 🟡 — advisory output only; nothing is blocked. **But it is a false positive that now fires on every completed task**, and an advisory nobody believes is worse than none |
| **Status** | **`FIXED`** — no longer reproduces, 2026-08-04. **`VERIFIED` is QE's** |
| **Found** | `bff371b`, by Lane A while rescanning the backlog after TASK-004 |

**Steps to reproduce.** Have one task appear both in `ACTIVE_ASSIGNMENTS.md`'s **Current** table and in its **Recently completed** table. Run `python3 infra/state-check.py`.

**Expected.** Nothing. One lane holds the task; the second mention is history, and the two tables are different sections with different meanings.

**Actual.**

```
  ·  TASK-001 is claimed by B and Lane B at once. The Task Claim Protocol
     requires the later claim to be abandoned (CLAUDE.md §20e).
```

**Why.** `board_rows` selects **every** line in the file starting `| ` that contains `TASK-`, so it reads *Recently completed* as claims. The two tables also spell the lane differently — `Lane B` in Current, `B` in Recently completed — so the same lane compares unequal and looks like two lanes racing.

**Why it matters.** The check exists to make *"two lanes claimed one task"* a fact a machine can decide. **It now reports that fact falsely, on the most ordinary state the board has** — a task that was completed. The next real collision will arrive in a report that already contains one, and it will be read as more noise.

**For whoever takes it.** Scope the scan to the **Current** section, the way [`state-check.py`'s handoff check is already scoped](../infra/state-check.py) — *"scoped to the `Current` section deliberately"* is a comment that file already carries about a different check. **Do not fix it by renaming the column in one of the tables**: the section a row is in is what decides its meaning, and matching on lane spelling would leave the check reading history as intent.

---

---


### No longer reproduces — Lane B, 2026-08-04

**Measured on `integration` at `2242820`:** `python3 infra/state-check.py` reports **no task claimed twice.** The double-claim advisory this row describes does not fire; the only collisions it now reports are architecture document numbers, which are [C-201](LANE_COORDINATION.md)'s class and awaiting a ruling.

**Two corrections to the row while closing it.**

**Its assignee was wrong, and stating that matters more than the fix.** The row reads *"Lane B — it holds [TASK-005](BACKLOG.md), which added this check."* **TASK-005 is `DONE`, held by QE**, and `infra/state-check.py` is repository tooling, which is QE's ([ADR-0100](architecture/adr/0100-delegated-dependency-rulings.md) R-4). A row can outlive the assignment that produced it, and this one did — **it sat against a lane that could not have edited the file it names.**

**Closed on evidence rather than on work**, like [B-202](#b-202--tsc---noemit-fails-on-integration) above. Neither was fixed for its own sake; both were carried away by other changes and stayed `OPEN` because nothing was positioned to notice.

### B-202 · `tsc --noEmit` fails on `integration`

> **Renumbered from `B-018` by QE at merge, 2026-08-02.** `B-018` was already allocated to a different finding; the later claim moves, and Lane A's block is `200`+ (`CLAUDE.md` §20e). **The original `B-018` is untouched.**

| | |
|---|---|
| **Module** | `timeline` (frontend tests) — `frontend/tests/components/timeline-feed.test.tsx` |
| **Current assignee** | **Lane B** — it holds `timeline` |
| **Severity** | 🟠 — **a lane gate is red on `integration`.** Every lane that rebases inherits it, and the honest response to a failing gate you did not cause is hard to distinguish from ignoring one you did |
| **Status** | **`FIXED`** — no longer reproduces, 2026-08-04. **`VERIFIED` is QE's** |
| **Found** | `4714496`, by Lane A while type-checking the Team slice |

**Steps to reproduce.** From `integration`, `cd frontend && npx tsc --noEmit`.

**Expected.** Clean. `tsc` is a lane gate (`CLAUDE.md` §20e, *Lane → QE*).

**Actual.**

```
tests/components/timeline-feed.test.tsx(79,19): error TS2345:
  Argument of type 'HTMLElement | undefined' is not assignable to parameter of type 'HTMLElement'.
tests/components/timeline-feed.test.tsx(80,19): error TS2345: (the same)
```

**Confirmed not caused by the reporting lane.** Reproduced with Lane A's own new file stashed out; both errors remain.

**Why it matters beyond two lines.** The frontend suite passes — 521 tests green — so nothing *fails*, and a lane running only `vitest` would never see it. **A type gate that is already red is a gate that stops being read**, which is the same defect class as an audit that passes vacuously ([B-015](#b-015--the-certification-audit-passes-vacuously-in-every-lanes-clone)).

**Not fixed here.** `timeline` is Lane B's, and finding a defect outside your assignment is an obligation to report it rather than permission to fix it (§20e).

---

---


### No longer reproduces — Lane B, 2026-08-04

**Measured on `integration` at `2242820`:**

```bash
cd frontend && npx tsc --noEmit
  →  (no output)
```

**Clean, including `timeline-feed.test.tsx`.** This row was opened at `4714496` on 2026-08-02 against a `timeline` fixture, and the file has changed hands and shapes several times since. **Nothing here was fixed deliberately for this row** — it was carried away by other work, which is why it sat `OPEN` while green.

> **That is the more useful finding, and it is [B-111](#b-111--tsc---noemit-is-in-no-gate-qe-runs-and-main-is-red)'s.** A gate nobody runs cannot close its own defects: `tsc --noEmit` was in the Definition of Done and in no gate QE ran, so a row raised against it could neither be confirmed still-broken nor observed fixed. **B-111 put it in the gate**, and this row is the first thing that gate can now retire.

### B-203 · Below 768px the product has no navigation at all

> **Renumbered from `B-019` by QE at merge, 2026-08-02.** `B-019` was already allocated to a different finding; the later claim moves, and Lane A's block is `200`+ (`CLAUDE.md` §20e). **The original `B-019` is untouched.**

| | |
|---|---|
| **Module** | Frontend foundation — `frontend/components/shell/app-shell.tsx` |
| **Current assignee** | **Lane A**, from 2026-08-03 — [TASK-200](BACKLOG.md) / CX-07. **It became assignable when [C-205](LANE_COORDINATION.md) was ruled**: a phone is in scope, so this is a defect rather than a non-goal, and §20c names *an unreachable control* as a class the frozen foundation is changed for |
| **Severity** | 🟠 — **an unreachable control**, which is §20c's own example of a foundation defect. Whether it is a *defect* or a *non-goal* depends on a product decision nobody has made |
| **Status** | **`FIXED`** — Lane A, 2026-08-03. A bottom navigation bar below `md`, reading the same `ITEMS` and applying the same guard as the sidebar. **`VERIFIED` is QE's** |
| **Found** | `9d6635e`, by Lane A during a production-UI review |

**Steps to reproduce.** Sign in. Narrow the viewport below `768px`, or open the product on a phone.

**Expected.** Some way to reach Settings and the attention list.

**Actual.** `app-shell.tsx:31` — `<aside className="hidden w-sidebar … md:block">`. The aside holds **the wordmark and the entire `<Navigation>`**, and below `md` it is removed. **Nothing replaces it.** The topbar carries only the workspace selector, the theme toggle and sign-out.

**So on a phone a signed-in customer cannot reach Settings at all**, and can reach the attention list only from an account brief's *"All accounts"* link. Landing on `/settings` from a bookmark is a dead end short of editing the URL.

**It was not an oversight in one place — it is the whole surface.** Across `app/` and `components/`, **three files carry any responsive rule**: `button.tsx`, `app-shell.tsx` and `authenticated-shell.tsx`. Every product screen has none.

**Why `hidden md:block` is evidence rather than a decision.** A product that had chosen to be desktop-only would leave the sidebar visible and let the layout be cramped. Hiding it says somebody saw it did not fit and removed it — **and the replacement was never built.**

**Not fixed by the reporting lane, for two reasons.** The file is frozen foundation, and more importantly **the fix depends on a product decision that does not exist**: whether Signora is expected to work on a phone at all. Restoring navigation on a viewport where the account brief is unusable would be polish on a screen nobody supports, and inventing that requirement is not a lane's ([C-026](LANE_COORDINATION.md)).

---

### B-200 · Two colour tokens that do not exist, on 44 lines

| | |
|---|---|
| **Module** | `integrations` (4 files) · `timeline` (1 file) |
| **Current assignee** | **Lane B**, which is assigned both modules |
| **Severity** | **🟠** — raised from 🟡 by Lane A, 2026-08-02. **See the note below**: it was 🟡 while both modules were unreachable, and CX-03 put one of them on the most-visited screen in the product |
| **Status** | **`FIXED`** — Lane B, 2026-08-03. **`VERIFIED` is QE's** |
| **Found** | 2026-08-02, by Lane A during the repository-wide customer experience audit |

> ### Fixed 2026-08-03 — Lane B
>
> **All 44 uses replaced**: `text-muted-foreground` → `text-content-muted` (30) and `text-foreground` → `text-content` (14), across the five files listed below. `tsc` clean; 857 frontend tests pass.
>
> **The reporting lane's count was right and the fixing lane's first count was wrong.** Lane B initially measured 30, having grepped only for `muted-foreground` — the row says *"two colour tokens"* in its own title, and **there were two.** The 14 remaining were found by the new assertion rather than by re-reading the row, which is the argument for writing the check before believing the count.
>
> **The regression test is the part that matters**, because the fix is a rename and the gap is what let it happen. `design-tokens.test.tsx` gains two things:
>
> | | |
> |---|---|
> | **Four directories** | `integrations`, `timeline`, `commercial` and **`app/(app)`** — the last carried four of the 44. The list had been correct on the day it was written and silently incomplete every day after |
> | **A check for the opposite defect** | Every assertion in that file caught a component **pinning** a colour a theme swap cannot reach. **None could catch one naming a colour that does not exist**, which generates no CSS at all and inherits silently |
>
> **The check is load-bearing, and that was verified rather than assumed** (§2 — *a guard that cannot fail is documentation pretending to be code*). Run against the unfixed tree it produces **five failures naming five files**; after the fix, 183 pass. **The legal token names are read from `tailwind.config.ts` rather than restated**, so the test cannot pass against its own stale copy of the palette.
>
> **What it still cannot see, stated rather than implied.** It catches the `-foreground` family and any undefined *variant* of a defined root (`text-content-mutd`). **A shadcn root this repository never defines at all — `bg-muted`, `bg-card`, `border-input` — would still pass**, because there is nothing to compare it against. None are present today; the residual gap is recorded here rather than papered over.
>
> **Why no colour is worse than a wrong colour.** A wrong colour is visible and somebody files it. **No colour looks like a design decision somebody made** — which is how this survived a repository-wide customer-experience audit, three product reviews and every gate in the repository.

**Steps to reproduce.** Open `/settings/connections`. Compare the description under the heading with the equivalent line on `/settings` or `/settings/products`.

**Expected.** Secondary text in the muted content colour, as everywhere else in the product.

**Actual.** It renders in the **primary** content colour, because `text-muted-foreground` resolves to no CSS rule at all and the element simply inherits.

**The cause is a token name that was never defined.** `tailwind.config.ts` declares `content` · `content-muted` · `content-subtle` · `content-inverted`, wired to `--color-content-*` in `globals.css`. **There is no `foreground` colour**, in the config or in Tailwind's own palette — `foreground`/`muted-foreground` is a shadcn convention, not this repository's. An undefined utility generates nothing, so the class is inert.

| File | Uses |
|---|---|
| `components/integrations/connect-panel.tsx` | 14 |
| `components/integrations/disconnect-dialog.tsx` | 9 |
| `components/timeline/feed.tsx` | 9 |
| `components/integrations/connection-center.tsx` | 8 |
| `app/(app)/settings/connections/page.tsx` | 4 |

**Why every gate passed.** `design-tokens.test.tsx` checks for **Tailwind's default palette** — `bg-slate-100`, `text-gray-500` — because that is the failure it was written for: a component *pinning* a colour a theme swap cannot reach. **An undefined token is the opposite defect** — no colour at all — and the check has no way to see it. It also scans `ui`, `shell`, `feedback`, `intelligence`, `(auth)` and `workspace`, and **`integrations` and `timeline` are in neither list.**

> **That is the same gap the check already records finding once**, at M12.3: *"this check scanned `components/` and nothing else, so `app/(auth)` — the first screen every customer sees — had been using `bg-white` since M1.5."* **A rule with a gap in its enforcement is a rule the code eventually finds the gap in**, and it has now happened twice.

**The fix for the enforcement half is already written, in another test in the same directory.** Found 2026-08-02 while checking whether the newly-mounted feed was covered:

| | How it selects files | Covers `integrations` / `timeline`? |
|---|---|---|
| `vocabulary.test.tsx` | **Walks `app/` and `components/` entirely.** No list to maintain | **Yes**, automatically, and every future directory too |
| `design-tokens.test.tsx` | **A hand-written list of six directories** | **No** |

**Two repository-wide tests, one repository, and only one of them has the gap.** The vocabulary check has never needed extending because it cannot fall behind — a new directory is covered the moment it exists. **The token check has now been extended twice** (M12.2 for `intelligence`, M12.3 for `(auth)`, both recorded in its own docstring as *"a rule with a gap in its enforcement is a rule the code eventually finds the gap in"*) and is behind again.

**So the fix is not "add two directories" — it is to select files the way the test beside it already does.** That closes the directory half permanently. The *undefined-token* half still needs a second assertion, because both checks look for wrong colours and neither looks for absent ones.

**Coordination on the structural half — 2026-08-02, on the product owner's direction.** *"Fix enforcement, not symptoms. `design-tokens.test.tsx` should adopt the same discovery mechanism instead of extending another hardcoded list."*

**Lane A is not implementing it** and is naming the owner instead: the check is repository-wide test infrastructure, which is **QE's**, and the 44 lines are **Lane B's**. **The two halves can be fixed independently and in either order** — a walk-based check will simply start failing on the 44 lines, which is the correct sequence if QE goes first.

**Two fixes, and they are different owners.** The 44 lines are Lane B's, in Lane B's modules. **Strengthening the check so a third instance is impossible is the frontend foundation's**, which has no assignee — recorded here rather than opened as a separate row, because it is the same defect seen from the enforcement side. A check that can only catch one of the two ways a colour goes wrong is worth saying out loud.

**Not fixed by the reporting lane.** Both modules are Lane B's, and *finding a defect is an obligation to report it, never permission to fix it* (`CLAUDE.md` §20e).

### Exposure changed on 2026-08-02, and so did the severity

**When this row was opened, both affected modules were unreachable** — the Connection Center had no entrance and `components/timeline/feed.tsx` was mounted nowhere. A flat visual hierarchy on a screen nobody can open is survivable, and 🟡 was right.

**CX-01 gave Connections a door and CX-03 mounted the feed on the account brief**, which is the screen a seller opens all day. **Nine of the forty-four lines now render on the most-visited surface in the product**, beside sections that use the real tokens — so the inconsistency is not only visible, it is visible *by comparison*, which is the form a customer notices.

**Nothing about the defect changed. What changed is who sees it**, and severity is a statement about that. **Raised to 🟠 by the reporting lane rather than the owning one**, with the reason stated so the owner can disagree.

---

---

## Verified

### B-001 · `signal_profile` reads the wrong row as "current"

| | |
|---|---|
| **Owner** | Lane A — `signal_engine` |
| **Severity** | 🟠 — latent today, 🔴 the moment the signal profile gets a write path |
| **Status** | **`VERIFIED`** — QE, 2026-08-02. Reproduced on `6aadea9`: `tests/signal_engine/test_profile_currency.py` writes a superseding version and asserts `current()` returns it, across all three tables, and passes in the promoted tree. Migration `0023` |
| **Found** | `1ae600d`, while building `commercial_profile` |

**Steps to reproduce.** Write a `SignalProfile` at version 1. Write a second superseding it (`supersedes = <v1 id>`). Call `SqlProfileRepository.current(workspace_id)`.

**Expected.** Version 2 — the profile in force.

**Actual.** Version 1, permanently. `current()` selects `WHERE supersedes IS NULL`, and on an immutable table the row with a null `supersedes` is the **first** version; the *new* row is the one that names its predecessor. `uq_signal_profile_current`, the partial unique index, is built on the same inverted assumption.

**Why it has never bitten.** Nothing has ever written a second profile version — there is no API and no UI, and every test writes v1. **It becomes reachable the moment a customer can edit their relevance profile**, which is Lane B's territory but Lane A's module.

**The fix, for whoever takes it.** `product_catalog` (migration `0019`) solves the same problem by reading `MAX(version)` and letting `uq_(workspace_id, version)` be the concurrency control — no partial index, no `UPDATE` grant needed. Same shape applies here.


## Won't fix

*None yet.*

### B-011 · `make` is not installed on this workstation — *not a repository defect*

| | |
|---|---|
| **Module** | none — the developer workstation |
| **Severity** | — |
| **Status** | `WONTFIX` — **reclassified 2026-08-01, product owner** |
| **Found** | `f996a42`, QE lane, adding a `make` target |

**What was observed.** No `make` on this machine: absent from `/usr/bin`, `/bin`, `/usr/local/bin` and `/snap/bin`; `dpkg -l` shows neither `make` nor `build-essential`. Every documented gate — `make demo`, `make smoke`, `make test`, `make certify`, `make dr`, `make eval` — fails with `command not found`.

**Why it is not a repository defect.** The Makefile is correct and every recipe it names resolves: `infra/smoke.sh`, `infra/disaster-recovery.sh` and the four `uv run python -m …` entry points all exist and were exercised directly during this slice. **Nothing in the repository is wrong; a required tool is missing from one machine.** Leaving a permanent bug row for a local environment would make the register describe workstations rather than the product.

**Where it went instead.** [`RUNNING.md` § What you need once](RUNNING.md) now lists `make` as a prerequisite, with the reason it matters more here than elsewhere: under [ADR-0027](architecture/adr/0027-local-first-development.md) the local run is the only run, so a missing gate runner is a missing gate.

**Resolved on the workstation, 2026-08-02.** GNU Make 4.4.1 installed to `~/.local/bin/make` **without root** — `apt-get download make`, `dpkg -x`, copy the binary — after `sudo` proved to require interactive authentication. Every documented gate now runs as written; the recipe is in [`RUNNING.md`](RUNNING.md).

**And it produced a rule.** The product owner ratified `CLAUDE.md` §20e *QE removes its own blockers* the same day: **when a documented prerequisite is missing and installing it is within QE's authority, QE installs it rather than stopping the workflow**, and escalates only when the OS, policy or an unavailable dependency genuinely refuses. Leaving a gate unrun because a tool needed installing is not an acceptable outcome.

**Kept as a row rather than deleted** because the finding was real and the reasoning that reclassified it is worth being able to find. *Correct a claim about the present; date a record of the past.*

---

### B-206 · A removed member kept full access, because the request-time membership check never filtered ended memberships

| | |
|---|---|
| **Module** | **`workspace_tenancy`** — [`infrastructure/query_service.py`](../backend/modules/workspace_tenancy/infrastructure/query_service.py), `WorkspaceQueryService.get_membership` |
| **Current assignee** | **Lane A**, joined from [`modules.toml`](coordination/modules.toml) |
| **Severity** | 🔴 · **Blocking Quality Defect.** **Removal did not revoke access.** A tenancy control that records an intention and does not enforce it is the failure `CLAUDE.md` §13 exists to prevent |
| **Status** | **`FIXED` — Lane A**, 2026-08-05, in the [TASK-437](BACKLOG.md) slice that found it. **`VERIFIED` is QE's** |
| **Found** | 2026-08-05, building the leave endpoint, by an acceptance test that asserted a leaver could no longer read the organization — **and got `200`** |

**Steps to reproduce**, before the fix:

```
owner creates a workspace · invites somebody · they accept
owner POSTs /workspaces/{id}/members/{membership_id}/remove   → 200, membership ended
removed person GETs /workspaces/{id}/members                  → 200  ← should be 404
```

**Expected.** An ended membership authenticates into nothing. `resolve_role` is *"the authoritative membership check performed on every authenticated request"* — its own docstring — and `active_workspace_id` in the token is only a hint ([18-authentication.md](architecture/18-authentication.md)).

**Actual.** It resolved a role for somebody whose membership had ended, so **every workspace-scoped route in the product kept serving them.**

### The cause, and why it survived review

**Two reads of one fact, and only one was filtered.**

| | |
|---|---|
| `SqlMembershipRepository.get` | **Filters `ended_at IS NULL`**, and says why in its own docstring: *"an ended membership that still resolved here would keep somebody signed in to an organization they had been removed from."* |
| `WorkspaceQueryService.get_membership` | Selected on `(workspace_id, user_id)` and **nothing else** |

**The second is the one the request path uses.** The correct behaviour was written down, tested, and implemented — in the object that authorization does not consult.

**Nothing detected it because nothing asked.** `member:remove` shipped with no integration test at all; the module's unit tests use a fake whose `get` *is* live-only, so every double behaved correctly while the deployed system did not — **the fake was more correct than the code it stood in for.**

### Blast radius

**Both callers were affected and both wanted live-only**, which is why the filter belongs in the query rather than at each of them:

* **`signora_platform/api/dependencies.py`** — `resolve_role`, on every authenticated request.
* **`modules/opportunity_engine/application/transition.py`** — the check before handing an account to a colleague. **Handing one to somebody who has left is the same defect wearing different clothes.**

### The fix

**One `WHERE` clause**, plus the docstring that says it is a security control rather than a tidiness.

**Regression tests are end-to-end and asserted through the customer's door**: a removed member and a departed member each get `404` from the members list and from the workspace itself. **The first attempt seeded a membership row directly and PostgreSQL refused it** — row-level security doing its job — which is §20e's *"test data enters the way a customer's data enters"* arriving as an error rather than as a rule somebody remembered. **The end-to-end version is the stronger assertion anyway**, because it travels the dependency chain a request actually travels.

### B-205 · Three documents disagree about whether the People bounded context is buildable

| | |
|---|---|
| **Module** | Repository governance — [`BACKLOG.md`](BACKLOG.md) [TASK-201](BACKLOG.md) and [TASK-427](BACKLOG.md), and [ADR-0400](architecture/adr/0400-person-as-an-entity.md)'s own status block |
| **Current assignee** | **Lane C** — it authored [441](architecture/441-people-roadmap.md), TASK-427 and the decomposition, and `BACKLOG.md` governance is its own |
| **Severity** | 🟠 — **a lane acting on the wrong one would create a 🔴 bounded context believing it was unblocked** |
| **Status** | ✅ **`FIXED` — Lane C, 2026-08-05.** All three corrected, and **a regression guard added for the one of the three a machine can catch.** **QE verifies; the lane that fixed it does not close it.** *(Original: `OPEN` — reported by Lane A, not fixed, because every row is Lane C's and finding a defect outside your assignment is an obligation to report it rather than permission to fix it, §20e. **Lane A was right on all three counts.**)* |
| **Fix** | **① [TASK-427](BACKLOG.md)'s `Blocked by` now cites [D-074](DECISION_REGISTER.md), which is the approval that exists** — *"I approve moving the **People domain** implementation earlier… I am not approving the full People Intelligence feature set."* **The cell was right in substance and wrong in citation**: it named an ADR whose own status block declines to authorise the work. **② [TASK-201](BACKLOG.md)'s sentence is dated rather than rewritten** — it was true on 2026-08-04 and the ADR moved the same day; §2 forbids falsifying a record of what was true then. **③ [ADR-0400](architecture/adr/0400-person-as-an-entity.md)'s status block records that [D-074](DECISION_REGISTER.md) superseded *"neither approves nor unblocks Epic C"* for the domain, and that ❓1 gates [TASK-429](BACKLOG.md) rather than the entity** |
| **Regression guard** | **`infra/state-check.py` now reports a document warning that it is not on `origin/integration` while it is.** ⚠️ **It found three more instances immediately** — [430](architecture/430-module-ownership-transition-plan.md), [ADR-0401](architecture/adr/0401-a-customers-crm-is-not-a-provider.md), [ADR-0402](architecture/adr/0402-a-rule-is-data.md) — **all Lane C's, all fixed in the same change.** **Its first version flagged the document it was written for**, because the correction *quotes* the warning it replaced; a line carrying ✅ or `~~` is now exempt. **A check that cannot tell its own fix from the defect is one people learn to read past.** ⛔ **The other two findings are prose disagreeing across three documents and are not mechanically checkable.** Saying so is more honest than a check that would pretend to cover them |
| **Found** | 2026-08-05, `1d15198`, by Lane A validating claimability after its queue reached 0 of 5 |

**Steps to reproduce.** Read the three, in this order, on `origin/integration`.

| Says | Where |
|---|---|
| *"**Blocked by — Nothing.** No ruling — **ADR-0400 is ratified**"* | [TASK-427](BACKLOG.md) |
| *"**ADR-0400 is `PROPOSED`, not ratified**, and **it says so in its own status block**"* | [TASK-201](BACKLOG.md) |
| *"**PRODUCT OWNER APPROVED — 2026-08-04**… **Ratifying this ADR records the bounded context… it neither approves nor unblocks Epic C**"* · *"❓1 is now answered — the provider returns no person name, **which blocks the epic**"* | [ADR-0400](architecture/adr/0400-person-as-an-entity.md) |

**Expected.** One answer to *"may a lane build the `people` bounded context today?"*

**Actual.** Three, and they do not agree.

1. **TASK-201's claim about the ADR is now false.** It says the status block reads `PROPOSED`; the block reads **`PRODUCT OWNER APPROVED`**. The row was right when written and the ADR moved.
2. **TASK-427 says *nothing* blocks it. The ADR says it neither approves nor unblocks Epic C**, and that ❓1 *"blocks the epic"*. **TASK-427 is the entity — the ADR is explicit that recording the bounded context is not the same as authorising the work**, which is precisely the distinction its own last paragraph draws.
3. **The ADR's status block is stale about its own location.** It warns *"⚠️ Not yet on `origin/integration` — this file does not exist there"*, and it does exist there. A lane obeying that warning would decline to act on a ruling the repository already carries — **the exact failure [D-076](DECISION_REGISTER.md)'s five decision states exist to prevent, in the file that names them.**

**Why this is 🟠 rather than cosmetic.** A new bounded context is 🔴 — product owner plus ADR. **TASK-427 is the one row of the three a lane would read on claiming**, it is `SEQUENCED` today, and the moment somebody places it, its `Blocked by` cell says *nothing blocks this*. **The safeguard against building a 🔴 on a misreading is that cell, and it currently reads the most permissive of three defensible statements** — which is the failure Lane C named in its own queue an hour earlier: *"the queue must never hold the more optimistic of two defensible readings."*

**Not a coordination item.** Nothing of Lane A's is blocked by it — the queue is empty for unrelated reasons and TASK-427 is `SEQUENCED`, so no lane can claim it today. **This is a defect in what the repository says**, and it will be believed by whoever arrives after the placement.

**For whoever takes it.** The ADR itself is the authority and is the least ambiguous of the three: **recording the decision is not authorising the epic.** TASK-427's `Blocked by` is the cell to correct; TASK-201's sentence about the status block is stale and dated rather than wrong when written; the ADR's *"not yet on integration"* warning has been overtaken and is the cheapest of the three to clear.

### B-204 · The demo environment shows intelligence about accounts and nothing about the business

| | |
|---|---|
| **Module** | The Product Playground — `backend/tests/playground/seed.py` |
| **Current assignee** | Whoever holds the Playground. **Not claimed by Lane A** — finding a defect outside an assignment is an obligation to report it, not permission to fix it (`CLAUDE.md` §20e) |
| **Severity** | **🟠** — wrong behaviour a reviewer hits on the first screen they open |
| **Status** | `OPEN` |
| **Found** | 2026-08-03, by Lane A, the moment **CX-05** built the first screen that reads this data |

**Steps to reproduce.** `make demo`, sign in as any demo user, open **Your business**.

**Expected.** The products the demo company sells, who buys them, and who has to agree — the declarations every score on the attention list is supposed to be relative to.

**Actual.** *"Nothing declared yet."* **All five declarations are empty in every seeded workspace**, measured directly: `product_catalog`, `icp_declaration`, `buying_committee`, `commercial_focus` and `target_account_list` all return version 0.

**The seeder runs the whole intelligence pipeline and declares no business.** `seed.py` drives provider simulation → ingestion → normalization → knowledge graph → observations → business events → signals → buying scores → opportunities across twelve accounts, and its own docstring is right that *"no state here is set"* — every band is computed. **The customer's own side of the story was simply never part of it**, because until CX-05 no screen read it and nothing made the absence visible.

**Why it matters more than a thin demo.** Signora's whole claim is that it compares what a company sells against what it finds. **A demo environment where the first half is blank cannot demonstrate that claim**, and it quietly invites a reviewer to read the scores as absolute rather than as relative to a declared business.

**Why no gate caught it.** Every check asks whether a route is served, called, or written to. **None can ask whether the demo tells a coherent story** — the same limit already recorded against the endpoint census in [43-customer-experience.md](architecture/43-customer-experience.md) §8.1.

**Worked around for review, not fixed.** Lane A declared a coherent profile for the Playground workspace **through the real `PUT` endpoints, as an owner, with a signed-in session** — the customer's door, and the only one `CLAUDE.md` §20e permits. **It is runtime state and a re-seed loses it**, which is exactly why the row stays open: the fix is five declarations in the seeder, so the demo is reproducible rather than repaired by hand.

**Suggested fix.** Two products, an ideal customer for each, a buying committee for each, one focus, three target accounts — enough that the read surface has shape, and coherent with the twelve accounts the scenario already seeds, which are technology companies.

---

⚠️ **A second `B-327` row stood here until 2026-08-06.** **It described the same defect from the fix side while the report side sat under `## Open` at the top of this file, and neither referenced the other.** **Merged into the single row above** — **`state-check`'s duplicate-identifier check is what found it**, and the partial fix it was concealing is recorded there.

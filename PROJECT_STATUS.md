# Signora — Project Status

> **The executive dashboard, and QE's alone to write** (`CLAUDE.md` §20e). A feature lane never edits it: repository-wide state is a property of everything merged together, and only the session that ran the gates on `main` has seen it. **A dashboard assembled from lane reports is a sum of intentions.**
>
> **Measured against `main` at `f954477`, 2026-08-09.** Every figure below is read from the promoted commit — never carried forward from a plan, never copied from a development report. **QE re-measures at every promotion**, during Repository Closeout (lifecycle stage 5).
>
> **This file answers one question — *"where are we?"*** Repository state · current milestone · overall completion · milestone progress · repository health · certification status · current blockers · active work · recently completed work · recommended next work.
>
> **It is a dashboard, not an engineering journal.** [`SESSION_HANDOFF.md`](docs/SESSION_HANDOFF.md) answers a different question — *"what should the next session know?"* — and does not repeat what is here. Historical implementation detail belongs in ADRs and module documentation; **the appendices below are dated records and are never rewritten to match the present.**

---

## 1 · Repository — the one-minute view

**Measured from the promoted commit `f954477`, 2026-08-09.** Every figure is read from the repository, never carried forward.

| | |
|---|---|
| **`main`** | **`f954477`** — the certified commit itself |
| **`integration`** | ⛔ **DIVERGED — `origin/integration` at `227a074f` carries `main`'s patches under different SHAs, plus two.** ⚡ **Its two unique commits are one documentation commit and one claim — nothing executable.** **The repair is the rebase Closeout step 10 prescribes; the force-push was refused by this environment, so it is outstanding** — see [B-161](docs/BUGS.md) and §1d |
| **Release candidate** | ⚡ **Cycle 146 promoted the scope ladder** — **and found that the Task Claim Protocol's own step 7 pushes a lane's unpromoted code to `integration`** ([B-161](docs/BUGS.md)) |
| **Certification** | ✅ [`f954477e9e42`](certification/reports/f954477e9e42.md) · migration head **`0045`** · protocol **v2** · profile **`documentation+frontend`** · **first attempt** |
| **Release phase** | **Ready.** All seven lifecycle stages complete |
| **Promotion** | `promoted == certified` ✓ · `--audit-main`: **clean, none outside a certified snapshot** |
| **Blocking Quality Defects** | ✅ **None — and this is *derived*, not typed** ([B-151](docs/BUGS.md)): `registers.bug_rows()` reads **148 rows, 46 unresolved, 0 unresolved 🔴**, and the repaired predicate is proved able to fail. ⚠️ **[B-211](docs/BUGS.md) remains 🟠 and ungated.** ✅ **[B-209](docs/BUGS.md) fixed and closed.** ⛔ **The gate reporting this was blind for six days** ([B-413](docs/BUGS.md)) — **now proved able to fail.** **[B-209](docs/BUGS.md)** — eleven Playwright journeys failing on `integration`, four `@journey` and five `@regression`, found by Lane A 2026-08-06 · **[B-211](docs/BUGS.md)** — `ruff check .` red across the whole tree and **no gate invokes it**. ⚡ **Re-measured 2026-08-08: 232 errors, exit 1.** ⛔ **QE published `None` while both rows were open** — see §1d |
| **Implementation waiting** | ✅ **Nobody.** ⚡ **Lane A delivered `TASK-1409` and claimed `TASK-1408` — the Application Shell, which six backlog rows are waiting for** |
| **Validation queue** | **Empty.** ⚠️ **Two documentation commits sit on `origin/integration` uncertified** — permitted by §20e, and next cycle's input |
| **Customer value this cycle** | ✅ ⚡ **A failure now claims the smallest surface it can** — four screens had each decided severity, wording and identifier presentation for themselves, and **three printed a correlation id in three shapes, one of which could not be copied** |
| **Overall progress** | **~81%** by engineering effort — an estimate, and marked as one. **Unchanged for six cycles, correctly** |

> ⚠️ **The frontend suite is in no gate, and running it by hand caught a failure on its first use** ([B-123](docs/BUGS.md)). `certify` gates on pytest, invariants, mypy, import-linter, `tsc` and smoke; `validate` runs the backend suite and `tsc`. **Neither runs `vitest`** — so **1255 frontend tests are run by nobody**, and a slice whose tests are entirely frontend passes `make validate` completely. **This is [B-111](docs/BUGS.md)'s class one level over**: that row found `tsc` in the Definition of Done and in no gate, and the fix added `tsc` and stopped.

**Repository health:** **4278 backend tests** · **95.07% coverage** ✅ *(floor 95)* · **1930 frontend tests** *(+30)* across **84 files** *(+2)* *(**gated in stage 1** since [B-123](docs/BUGS.md); **certification still does not run them**)* · **398 Security Invariants** · mypy strict over **851 files** · **46 migrations**, `0000`–`0045`, **verified reversible this cycle** · **37 import-linter contracts**, 0 broken · `tsc --noEmit` clean *(gated since [B-111](docs/BUGS.md))* · smoke 24 stages in **212s** *(⚠️ `Researched account 23s` — the slow-population stage on a fast run, second time, [B-141](docs/BUGS.md))* · **disaster recovery passed** — 5 restart stages, nothing lost · **18 module directories** · **53 ADRs** · **142 numbered architecture documents**.

---

## 1a · Lane dashboard — who is moving what, right now

**Module assignment is [`modules.toml`](docs/coordination/modules.toml)'s and is not restated here** (`CLAUDE.md` §20e). This table records execution.

| | **Lane A** | **Lane B** | **Lane C** | **QE** |
|---|---|---|---|---|
| **Last promoted** | **TASK-451** — a saved view a colleague can open | ⚡ **M-I** — who has held a role at a company, and who left | ⚡ **Workflow 1 at 12 of 12 design elements** | **Cycle 113** |
| **Execution phase** | **Building** | **Building** | **Governing** | **Certified · Promoted · Closed out** |
| **Branch** | Level with `main` | Level with `main` | Level with `main` | Level with `main` |
| **Validation status** | — | — | ✅ **Promoted this cycle** | — |
| **Blocked?** | **No** | **No** | **No** | **No** |
| **Waiting on QE?** | No | No | No | — |
| **Next executable work** | ⚡ **`TASK-485`** — released this cycle | — | Stewardship | ⚡ **[D-167](docs/DECISION_REGISTER.md) — impact-aware certification** |

> **Declarations that had existed since M5 finally have consumers.** `signal_engine` and `buying_score_engine` were declaring subscriptions nothing acted on — **the declaration was true, and no gate could tell the difference**, which is [B-131](docs/BUGS.md)'s shape one layer down.
>
> ⚠️ **`reasoning@2` ships unreleased, and QE checked rather than assumed.** Zero evaluations, so under [ADR-0028](docs/architecture/adr/0028-model-runtime-by-environment.md) it is usable with nothing. **That is what a new version looks like, not a regression** — and `prompt-evaluation` stays in the shortfall until a real model measures `@1` or `@2` on this hardware.
>
> **Three lanes, six commits, first attempt, no aborts.**

---

## 1b · Customer capability — can a customer actually use it?

| Capability | Backend | UI | Reachable | Demo | Production | Note |
|---|---|---|---|---|---|---|
| **Sign in · workspaces** | ✅ | ✅ | ✅ | ✅ | ✅ | |
| **Attention list** | ✅ | ✅ | ✅ | ✅ | ✅ | |
| **Account brief** | ✅ | ✅ | ✅ | ✅ | ✅ | **Improved this cycle** — says who put the account in front of you, stops repeating itself, explains an empty list |
| **Evidence trail** | ✅ | ✅ | ✅ | ✅ | ✅ | |
| **Decisions** | ✅ | ✅ | ✅ | ✅ | ✅ | **The account now remembers what was decided, and why** |
| **Your business** | ✅ | ✅ | ✅ | ✅ | ✅ | |
| **Research on demand** | ✅ | ✅ | ✅ | ✅ | ✅ | |
| **Connected systems** | ✅ | ✅ | **✅** | ✅ | ⚠️ | **Now reachable — CX-01 gave the Connection Center a door.** No OAuth flow yet ([C-025](docs/LANE_COORDINATION.md)) |
| **Provider ingestion** | ✅ | — | — | ✅ | ✅ | **Six slices promoted**: per-account watermarks, self-pacing, measurable, says where a payload came from |
| **Account history** *(Timeline)* | ✅ | ✅ | ❌ | ❌ | ❌ | **Backend now genuinely works** — [B-301](docs/BUGS.md) fixed and promoted; nine subscriptions registered from the projection table, and `make runtime-composition` reads **0 unexpected**. **Still mounted nowhere** — [C-024](docs/LANE_COORDINATION.md) is now the only thing between this and a customer |
| **Decision Package** | ✅ | ✅ | ⚠️ | ❌ | ❌ | 🔴 `reasoning@1` has no released model |
| **Recommendations · notifications · billing** | — | — | — | — | — | M11 deferred · M14a/b not started |

> **Two capabilities were complete and unreachable last cycle. One of them is fixed** — CX-01 gave the Connection Center a navigation entry.
>
> **Timeline was not "ten lines away", and this dashboard said it was.** [B-301](docs/BUGS.md) — raised by Lane B while auditing its own modules — found that the deployed worker consumed **nothing**: the read API was wired, the router included, the table created and the component rendering, and **no subscription ever wrote a row.** Mounting the feed would have shipped a screen that is empty forever.
>
> **QE certified and promoted four Timeline slices without noticing.** Every gate was green because a composition root is the one file no module's own suite covers — each module tests its half and assumes the join. **2563 passing tests said nothing about what the deployed worker subscribes to.**

---

## 1c · Dependency dashboard

| Dependency | Affected milestone | Owner | Status | Resume trigger |
|---|---|---|---|---|
**Every row below is the product owner's, and every one is now blocking a lane rather than merely open.** That is the change this cycle: the register stopped being a queue of questions and became the reason both lanes are writing documents.

| Dependency | Affected milestone | Owner | Cycles | Resume trigger — **one executable step** |
|---|---|---|---|---|
| **[C-010](docs/LANE_COORDINATION.md)** — nothing is assignable to `apps/`, `signora_platform/`, repository process | Repository | **Product owner** | **7** | **Assign an owner.** **7 defects have now landed in this gap**, [B-100](docs/BUGS.md) the newest |
| **[C-020](docs/LANE_COORDINATION.md)** — M7 scope | M7 | **Product owner** | **6** | **Ratify, amend or reject ADR-0038** |
| **[C-024](docs/LANE_COORDINATION.md)** — Timeline has nowhere to mount | **M7** | **Product owner** (placement) → **Lane A** (route) | **5** | **Choose where the feed mounts.** Then ~10 lines in `accounts/[accountId]` |
| **[C-025](docs/LANE_COORDINATION.md)** — M13's OAuth ownership | **M13** | **Product owner** | **5** | **Rule which tier may run the flow** |
| **[C-021](docs/LANE_COORDINATION.md)** — Provider Platform dispatch direction | M2.1 | **Product owner** | 2 | **Choose a dispatch direction.** Lane A has built everything inside the accepted architecture |
| **[C-200](docs/LANE_COORDINATION.md)** — M14b's bounded context is 🔴 | M14b | **Product owner** | 2 | **Name the bounded context.** Every route into implementation decides it by implementing it |
| **[C-206](docs/LANE_COORDINATION.md)** · **[C-207](docs/LANE_COORDINATION.md)** — invitation email delivery · leaving a team | Team Management | **Product owner** | 2 | Two narrow product rulings. **Neither blocks the invitation slice itself** |
| **[ADR-0041](docs/architecture/adr/0041-icp-aggregate.md)** — the ICP aggregate | `commercial_profile` | **Product owner** | 1 | **Ratify or reject.** Lane B is stopped behind it |
| **28 others** | various | mixed | — | See the register |

**37 items · 5 closed.** ⚠️ **Four items have now waited five cycles or more, and every one of them needs the same person.** [C-024](docs/LANE_COORDINATION.md) is the sharpest: Timeline's backend was proven live this cycle by `runtime-composition`, so **ten lines of routing separate a working capability from a customer.**

---

## 1d · Release summary — 2026-08-09, cycle 136

**Derived from the promoted commit `901935d`.** **Ninety-one promotions.** ⛔ **QE promoted a duplicate identifier, its own check caught it, and QE had grepped past the finding.**

### ⛔ [B-153](docs/BUGS.md) — the check was run and *filtered*

```
$ python3 infra/state-check.py
B- identifiers are allocated twice: B-152.
```

**`state-check` ran before the Closeout commit, exactly as [B-150](docs/BUGS.md) requires.** ⚡ **It caught this.** ⛔ **QE piped it through `grep -icE "conflict marker"`, read `0`, and promoted.**

> ⚠️ **B-150 was *the check was skipped*. This is *the check was run and filtered* — and the second is worse, because the output said `0` and looked like a pass.** ✅ **The fix is one word: read the finding list, not a count of the finding you expected.**

### ⚠️ How the duplicate arose — a correct habit with a predictable cost

**QE filed [B-152](docs/BUGS.md) and held it on `lane-qe` for five polls**, because §20e holds documentation-only work until executable change accompanies it. ✅ **That is correct and QE will keep doing it.** ⛔ **But a held row is invisible to every other lane** — Lane C could not see it, and after QE described the condition in a poll, Lane C wrote its own row under the same id.

✅ **Folded, not renumbered.** **They are one defect, and two ids for one defect is exactly what the identifier rule exists to prevent.** **Both accounts survive in one row.**

### ⚡ [D-200](docs/DECISION_REGISTER.md) — Smart Certification Strategy, ruled

**The product owner ruled impact-based certification this cycle.** ⚡ **QE's assessment, measured rather than estimated, is [below in §1f](#1f--d-200-smart-certification-strategy--what-exists-and-what-does-not).**

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4272 backend** · **1827 frontend** · **95.07%** · **398 invariants** · **851 files typed** · **37 contracts** · ⛔ **`ruff` red, ungated — [B-211](docs/BUGS.md)** |
| **Release** | **141 runs recorded, 133 certified** · `promoted == certified` ✓ · `--audit-main` clean · **first attempt** |
| **Architecture** | Migration `0045` **reversible, verified** · **DR nothing lost** · smoke 189s |
| **Dependency** | ✅ **Lane A unblocked last cycle**; `TASK-1400` is `READY` on `integration` |
| **Customer Value** | ⛔ **None.** **A register repair** |
| **Process** | 🔴 **Third QE self-defect of this class** — [B-150](docs/BUGS.md) skipped a check, [B-151](docs/BUGS.md) transcribed instead of measuring, [B-153](docs/BUGS.md) filtered a check's output. ⚡ **All three are one habit: trusting the shape of an answer instead of reading it** |

---

## 1d · Release summary — 2026-08-09, cycle 146

**Derived from the promoted commit `f954477`.** **101 promotions.** ⚡ **A slice that consolidated four improvised failure surfaces, and a governance defect found by a push that would not fast-forward.**

### ✅ What a customer gets

> **A failure claims the smallest surface it can.**

⛔ **Four surfaces already rendered system states and each decided severity, wording, identifier presentation and actions for itself** — `app/not-found.tsx`, `app/error.tsx`, `components/feedback/error-boundary.tsx`, `components/ui/error-state.tsx`. ⚠️ **Three rendered a correlation id in three different shapes and one of those could not be copied.**

⚡ ***"None was wrong alone; the set was."*** ✅ **The ladder is read out of the design document rather than transcribed** — and **the parse failed twice before it passed**, the vacuity guard catching an anchor that matched a template reference instead of the declaration.

### ✅ The budget was correct, and the 🔴 edge was found by hitting it

**+738 insertions, 0 deletions.** 🟠 **Two new `components/ui` components announced in the commit message**, exactly as §20e requires — **no shared component bent for one caller.**

> ⛔ **`app-shell.tsx` was deliberately not converged.** *"Four of the five improvised boundaries live in `app-shell.tsx`, which is the shell, red, and this row's budget grants nothing red."* ⚡ ***"The edit was made and reverted rather than argued about"*** — **[C-254](docs/LANE_COORDINATION.md).**

### ✅ A guard failed, and the lane did not reword its way past it

**[C-252](docs/LANE_COORDINATION.md).** The region boundary **is not in this commit, and that is the finding.** It was written, and **TASK-445's guard failed it**: `StatedAbsence` already owns the region-scope failed-read sentence.

| | |
|---|---|
| **The row assumed** | absence and failure are separable |
| **The code says** | `StatedAbsence`'s actual sentence is *"Signora could not load X"* — ⚡ **a failure, not an absence** |
| **So** | **`StatedAbsence` has the sentence and no retry, attempt count or identifier; the ladder has all three and no sentence.** ⛔ **Two primitives claim one concern** |

⚡ ***"The boundary was removed rather than reworded, because rewording to dodge a regex is the fork the guard exists to prevent."*** **That is a surviving-mutation response done correctly** (§2).

### ⛔ [B-161](docs/BUGS.md) — the Task Claim Protocol's own step 7 pushed a lane's unpromoted code to `integration`

**QE's `git push origin integration` was refused as a non-fast-forward, which is how this was found.** `origin/integration` had gained **six code files** — `TASK-1409` — **underneath a perfectly bounded claim commit.**

> ⚡ **Nobody did anything wrong, and that is the finding.** **Step 7 says `git checkout integration && git merge --ff-only <lane-branch> && git push`.** ⛔ **A fast-forward carries the whole branch**, and §20e's *Continuous execution* rule **guarantees the branch usually holds an unpromoted slice** — *"the moment a lane sets `IN VALIDATION`, it claims the next `READY` task."* **The protocol that requires the claim and the rule that keeps work on the branch are in direct conflict.**

**What it cost, measured rather than assumed: nothing.** ✅ **QE had independently rebased and certified the same two patches, and `git patch-id --stable` confirms byte-equivalence:**

```
integration 554dd74c → cbbab267…     main 6636e6ce → cbbab267…
integration 03a81b5d → b9cbb641…     main f954477e → b9cbb641…
```

✅ **`promoted == certified` held · `--audit-main` clean · no uncertified code on `main`.**

⛔ **`--audit-claims` could not have caught it**: it reads commits whose subject begins `Claim TASK-`, and **it never inspects the commits a claim's own push brings with it.**

### ⚠️ `integration` is left diverged, and the repair is computed but unpushed

**The rebase Closeout step 10 prescribes was run and verified locally** — duplicates dropped, both genuinely-new commits replayed, `main` confirmed an ancestor. ⛔ **The force-push to the shared branch was refused by this environment**, twice.

**The rebased result is preserved on the local branch `qe-integration-rebased`** — ⚠️ **computed against `f954477`, so `main`'s Closeout commit has since moved past it and it needs one more replay before it can be pushed.** ⚡ **The repository still functions**: `origin/integration`'s two unique commits are **one documentation commit and one claim, nothing executable**, and next cycle builds by rebasing onto `main` exactly as this cycle did. ⚠️ **The divergence grows until the push happens, and it is the one outstanding step of lifecycle stage 6.**

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4278 backend** · **1930 frontend** *(+30, +2 files)* · **95.07%** · **398 invariants** · **851 files typed** · **37 contracts** · ⛔ **`ruff` red, ungated — [B-211](docs/BUGS.md)** |
| **Release** | **151 runs recorded, 143 certified** · `promoted == certified` ✓ · **first attempt** |
| **Architecture** | Migration `0045` **reversible, verified** · **DR nothing lost** · smoke 24 stages in **212s** · **53 ADRs** |
| **Dependency** | ⛔ **`integration` diverged — [B-161](docs/BUGS.md), repair computed, push outstanding** |
| **Customer Value** | ✅ ⚡ **One failure vocabulary instead of four** |
| **Process** | ✅ **No QE self-defect.** ⚡ **The defect QE did find is in `CLAUDE.md` itself, and is the product owner's** |

---

## 1d · Release summary — 2026-08-09, cycle 145

**Derived from the promoted commit `97a13ce`.** **One hundred promotions.** ⚡ **[B-159](docs/BUGS.md) closed on measurement, and the check that found it stopped being able to mean it.**

### ✅ [B-159](docs/BUGS.md) — `VERIFIED`, and verified by measuring rather than by reading the fix

| Cycle 144, on `main` | Cycle 145, on `main` |
|---|---|
| `claimable_now = 0` | ✅ **`claimable_now = 22`** |
| `backlog = []` | ✅ **22 entries** |
| `awaiting_sync = 23` | ✅ **`awaiting_sync = 0`** |
| ⛔ notice said *"Build"* | ✅ **notice and counters agree** |

⚡ **`BACKLOG.md` carries 22 claimable rows, so the projection now matches its authority** ([D-144](docs/DECISION_REGISTER.md)).

### ⛔ [B-160](docs/BUGS.md) — and this one is the cost of having reported the last four cycles honestly

**`coordination.py --check` still exits 1 on the promoted commit.** ⚡ **QE diffed `_content` in-process rather than believing either answer, and the entire difference is two numbers:**

```
-awaiting_qe_transition = 0     +awaiting_qe_transition = 6
-lane_utilization   = 1.2       +lane_utilization   = 0.0
```

✅ **Every task, every backlog entry, every claimable count is identical.**

> ⛔ **Neither number can be fixed by republishing.** `awaiting_qe_transition` counts rows stranded at `IN VALIDATION`; `lane_utilization` derives from what lanes are working. **Both move when *another* lane pushes** — **so the file goes stale through nobody's inaction**, and `--check` passes only between a regeneration and the next lane's push.

⚠️ **[B-134](docs/BUGS.md) is the same defect one field over, and its fix was half of one.** **It removed `[meta]` from the comparison** — *"a check that reports stale about an accurate file teaches a reader to ignore it"* — ⛔ **and left two numbers inside `_content` with exactly the property it had just excluded.**

**Why QE files it rather than tolerating it.** ⛔ **QE reported *"the coordination source is stale"* for four cycles from this check.** **Three times it was true and material.** ⚠️ **The fourth was metric drift — and the output is identical either way**, so a real `claimable_now = 0` and a harmless utilization delta print the same sentence. ⚡ **The signal that found B-159 can no longer be trusted to mean it.**

### ✅ The rulings, and the gate Lane C wrote against itself

**[D-210](docs/DECISION_REGISTER.md) — the shell audit is clean, and both apparent gaps were the auditor's own vocabulary.** ⛔ *"Route transitions"* and *"split layouts"* were reported absent **because a term search found no match**, and both were fully specified — one as `loadingCases → "Route change · module to module · shell, filters and utility panel persist"`, the other as the utility panel's *"selecting a table row fills the panel rather than opening a second surface."*

**[D-212](docs/DECISION_REGISTER.md) puts a gate in front of the next one:** ⚡ ***one question before anything is raised — can this be answered by an existing finalized design document?*** **Two product-owner interruptions avoided, caught before they were raised.**

> ⚡ **And it declines to build a mechanism for its own rule**: *"a validator cannot answer 'is this already in a design', so a check would only add ceremony."* **That is §2's *a guard that cannot fail is documentation pretending to be code*, applied by choosing not to write the guard.**
>
> ✅ **§4 recorded as owed rather than claimed**: six workflows are on `main` and none has been audited against its finalized design since shipping.

### ✅ Lane C fast-forwarded, and the claim commit was checked rather than assumed

**`integration` moved without QE** — the one permitted exception. ✅ **`2afe285d` touches `ACTIVE_ASSIGNMENTS.md` and `BACKLOG.md` and nothing else**, and `--audit-claims` names it in no finding. **Lane C was 0 behind, so `--ff-only` was the whole integration.**

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4278 backend** · **1900 frontend** · **95.07%** · **398 invariants** · **851 files typed** · **37 contracts** · ⛔ **`ruff` red, ungated — [B-211](docs/BUGS.md)** |
| **Release** | **150 runs recorded, 142 certified** · `promoted == certified` ✓ · **first attempt** · **one hundred promotions** |
| **Architecture** | Migration `0045` **reversible, verified** · **DR nothing lost** · smoke 24 stages in **149s** · **53 ADRs** |
| **Dependency** | ✅ **Nothing excluded, nothing held.** ✅ **[B-159](docs/BUGS.md) closed — the projection both lanes read is current** |
| **Customer Value** | ⚪ **None directly.** ⚡ **An audit that found nothing, and said so** |
| **Process** | ✅ **No QE self-defect.** ⚠️ **Four QE-owned rows now open on instruments** — [B-156](docs/BUGS.md), [B-157](docs/BUGS.md), [B-158](docs/BUGS.md), [B-160](docs/BUGS.md) — **and every one of them is a gate, so every one is a slice rather than a Closeout** |

---

## 1d · Release summary — 2026-08-09, cycle 144

**Derived from the promoted commit `7bc4b53`.** **Ninety-nine promotions.** ⚡ **One ruling promoted, fifteen commits correctly refused, and a QE self-defect caught by `git status` rather than by discipline.**

### ✅ What the ruling buys

**[D-209](docs/DECISION_REGISTER.md) answers [C-251](docs/LANE_COORDINATION.md) — the two Signal Center row fields Lane A reported absent last cycle — *"and the answer was smaller than the question."***

| The design wanted | Where it already was |
|---|---|
| `summary` | ⚡ **`signal.py:81` already carries `rationale`, and its comment is the design's own sentence** · `:64` carries `relevance` |
| `confidence` | ⚡ **`components/ui/confidence.tsx` already exists and is imported by nothing** — *"use it, do not fork it"* |

⛔ **`QueueEntryResponse` simply publishes neither.** ✅ **`TASK-1427` widens the schema by two fields.** ⚡ **That is [ENGINEERING_LAWS.md](ENGINEERING_LAWS.md) L-1 finding an answer that was already in the repository** — **the row Lane A was right not to invent.**

### ⛔ Fifteen of sixteen were already promoted

**`lane-c-sync` read 16 ahead / 16 behind.** ⚡ **Patch-id says fifteen are duplicates of what cycle 143 promoted**, and the rebase dropped every one of them by itself. **One commit was real.**

> ✅ **This is the standing instruction earning its place.** **Believing the ref count would have re-certified fifteen already-certified commits**, and the tell is not visible in `git log` — **only `git patch-id --stable` distinguishes *held work* from *a pointer that has not moved.***

### ⛔ [B-159](docs/BUGS.md) — the coordination source says *Build* and *zero claimable* in the same block

**Measured on the promoted commit, not on a candidate:**

```
[meta] generated_from = "14abd98"        ← two promotions behind
[lane.Lane_A]
  notice        = "Build. 24 rows and none needs invented behaviour. …"
  backlog       = []
  claimable_now = 0
```

**Regenerating against `main` yields `claimable_now = 22`.** ✅ **The generator is correct; only the published file is behind** — QE rendered in-process and diffed `_content` to zero.

> ⛔ **This is [B-216](docs/BUGS.md)'s class with the halves swapped, and it is the worse orientation.** **There, prose asserted a state and the counters caught it.** ⚠️ **Here the prose is right and the counters are wrong — and `_notice()` now refuses state words in prose, so the half a reader is directed to trust is the half that is stale.**

✅ **Lane A has not idled on it**, because it reads `BACKLOG.md` too. ⛔ **But the source exists precisely so a lane need not**, and this is its fourth consecutive stale cycle. **Not repaired by QE: republishing a projection QE does not own would give it a second author, which is the one thing its guarantee rests on.**

### ⛔ [B-158](docs/BUGS.md) — QE ran `--dry-run` during a live certification, and it wrote

**`coordination.py --dry-run` rewrites `coordination.toml`.** `main()` falls through to an **unconditional** `OUT.write_text(fresh)` before it ever consults `--publish`; the flag is documented as *"with `--publish`: validate only"* and is ignored on its own.

⚠️ **QE ran it on a clean tree while `make certify` was in flight, and that half is QE's defect rather than the tool's** — **an unfamiliar flag is read before it is run, which is exactly what cycle 115 already recorded.**

> ✅ **The record reads `tree_clean: true` and it is true**: `git status` caught the modification and it was restored before the run sampled. ⛔ **That was timing, not discipline, and it is recorded as timing.**

⚡ **The row is worth filing because of what the flag promises.** **The repository's standard is *prefer operations that refuse unsafe states over operations that silently recover from them*** — and **a flag whose name is a promise of safety and whose behaviour is a write will next be reached for by somebody doing precisely what QE was doing: trying to look without disturbing.**

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4278 backend** · **1900 frontend** · **95.07%** · **398 invariants** · **851 files typed** · **37 contracts** · ⛔ **`ruff` red, ungated — [B-211](docs/BUGS.md)** |
| **Release** | **149 runs recorded, 141 certified** · `promoted == certified` ✓ · **first attempt** · profile **`platform`** |
| **Architecture** | Migration `0045` **reversible, verified** · **DR nothing lost** · smoke 24 stages in **149s** · **53 ADRs** |
| **Dependency** | ✅ **Nothing excluded.** ⚠️ **[B-159](docs/BUGS.md) — the projection both lanes are meant to read is two promotions behind** |
| **Customer Value** | ⚪ **None directly.** ⚡ **[D-209](docs/DECISION_REGISTER.md) turns a blocked screen field into a two-field schema widening** |
| **Process** | ⛔ **One QE self-defect — [B-158](docs/BUGS.md)**, and it is the second time this session that reading before running would have prevented one |

---

## 1d · Release summary — 2026-08-09, cycle 143

**Derived from the promoted commit `6ccea5f`.** **Ninety-eight promotions.** ⚡ **The seven-cycle exclusion ended, and it ended the way [B-155](docs/BUGS.md) said it should — by the branch becoming integrable, not by QE forcing it.**

### ✅ [B-155](docs/BUGS.md) is answered by the repository, not by QE

**Lane C's fifteen commits replayed onto `integration` with ZERO conflicts.** ⛔ **Nobody hand-resolved a generated file, and nobody had to.**

> ⚡ **This is the refinement from cycle 142 doing its job.** **The test is not the ahead/behind count — it is the rebase.** Lane C read **15 ahead / 3 behind**, which is *more* divergent by the numbers than the state that got it excluded seven times running. **The rebase said otherwise, and the rebase is the only thing that actually knows.**

**Held work now on `main`:** **[D-198](docs/DECISION_REGISTER.md) through [D-208](docs/DECISION_REGISTER.md)** — eleven rulings — plus **[D-204](docs/DECISION_REGISTER.md)'s decomposition of all 29 workflows**, two coordination republishes, and one ADR.

### ⚡ The finding of the cycle is Lane C's, filed against itself

> **[B-216](docs/BUGS.md) — *"I built a channel to route past QE, then used it to assert a state."***

**Lane A caught it on the poll it was published.** A notice read *"TASK-1400 is READY"* while `BACKLOG.md` on `integration` read `SEQUENCED` — **and the tell was three lines below, in the same block:**

```
current       = ""
claimable_now = 0
```

⚡ ***"The counters agreed with the backlog. My prose did not."***

⛔ **Third instance of one class — [B-148](docs/BUGS.md), [B-152](docs/BUGS.md), this** — *"and every time a projection asserted a state the backlog did not carry. **Twice I fixed the instance. The class only closes if a projection CANNOT say it.**"*

> ✅ **So it is refused rather than discouraged.** `_notice()` now rejects any string matching a state word and substitutes a pointer to the authority — **[D-144](docs/DECISION_REGISTER.md)'s sentence enforced instead of restated.** **Proved both ways: the exact text Lane A caught is withheld; the corrected text passes.**
>
> ⚡ **That is §2's *unrepresentable over discouraged* applied to a projection**, and it is the same move QE has been unable to make on its own two open gate rows.

### ✅ Repository consistency improved measurably

| | |
|---|---|
| **`state-check` findings** | **5 → 2.** The six parked `SEQUENCED` rows released, and `lane-a.toml` stopped offering finished work |
| **Still open** | ⚠️ **The canonical coordination source is stale even after two republishes in this batch** · **`timeline` publishes an empty `public/`** |

### ⚠️ Lane C changed `infra/state-check.py`, and QE is naming the boundary rather than blocking on it

**+127 lines in the instrument QE closes out with.** ⛔ **[§20e](CLAUDE.md) draws the line at *meaning* versus *running*** — and this changes what the check means.

✅ **It is within [D-022](docs/DECISION_REGISTER.md)'s Platform Foundation grant, and `state-check` is advisory rather than a certification gate**, so certification's meaning is untouched: `make certify` still decides on pytest · coverage · invariants · mypy · import-linter · tsc · smoke · scenario. ⚠️ **Recorded because the neighbouring rule is *Lane C may not verify governance it authored*, and this batch is Lane C validating a check Lane C wrote.** **QE ran it independently, before and after — that is what makes the 5 → 2 a measurement rather than the author's claim.**

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4278 backend** · **1900 frontend** · **95.08%** *(+0.01)* · **398 invariants** · **851 files typed** · **37 contracts** · ⛔ **`ruff` red, ungated — [B-211](docs/BUGS.md)** |
| **Release** | **148 runs recorded, 140 certified** · `promoted == certified` ✓ · **first attempt** · profile **`platform`**, 16 gates planned |
| **Architecture** | Migration `0045` **reversible, verified** · **DR nothing lost** · smoke 24 stages in **149s** *(fastest in many cycles)* · **53 ADRs** *(+1)* |
| **Dependency** | ✅ **Nothing excluded.** ⚡ **First cycle since 136 with no held branch** |
| **Customer Value** | ⚪ **None directly — a planning batch.** ⚡ **It refills the queue both lanes pull from** |
| **Process** | ✅ **No QE self-defect.** ⛔ **[B-156](docs/BUGS.md) and [B-157](docs/BUGS.md) still open and unfixed** — both are gates, and fixing a gate is a slice |

---

## 1d · Release summary — 2026-08-09, cycle 142

**Derived from the promoted commit `14b3985`.** **Ninety-seven promotions.** ⚡ **A lane that shipped half a workflow, refused the other half out loud, and gave the reason in one sentence a security docstring had already written.**

### ✅ What a customer gets

> **A person following an invitation that has aged out is told so** — at `/invite/expired`, the route the design gives it, on Signora's own ground.

⛔ **It could not be written before.** **An expired invitation and one that never existed both arrived as `invitation_not_found`**, so the join page had nothing to branch on — **and a screen nothing can reach must not be built.** ✅ **[B-214](docs/BUGS.md), this lane's own fix, is what made the entrance exist**: `InvitationExpiredError` now yields `invitation_expired`. ⚡ ***The domain always knew; only the transport had flattened it.***

### ⚡ The refusal is the finding of the cycle

**Screen 13 and `/invite/mismatch` are not built, and the lane said why rather than reporting a blocker.**

> *"Buildable only by weakening a deliberate security property, **and I am not asking for permission to do it.**"*

**`InvitationNotFoundError`'s own docstring had already ruled it:** *"Telling them apart would answer **'has this workspace invited this person?'** to anybody who can sign in — **a fact about a customer's hiring.**"* ⛔ **A *Wrong account* screen must say the opposite: that an invitation exists here, for somebody else.**

> ⚡ **And this is the half worth keeping.** **It is the same flattening [B-214](docs/BUGS.md) had just fixed** — *"having just fixed one instance of a class, the tempting move was to fix the next one that looked identical, **and that would have undone a security property while looking like consistency.**"*
>
> ✅ **Expiry was safe to separate; wrong-account is not.** **Knowing an invitation aged out reveals nothing about who was invited.** ⚡ **The lane drew that line itself, offered a disclosure-free alternative *as input rather than authority*, and left the ruling with the product owner** ([C-245](docs/LANE_COORDINATION.md)).

### ✅ Both slices were found by re-testing blockers, not by reading them

> *"`READY` was zero again, so I re-tested the blockers on every row I hold **instead of reading their status lines.**"*

**Two rows were genuinely blocked and stayed blocked.** **`TASK-489` was not** — its own row already recorded that half had cleared, and nothing had been built against it. ⚡ **That is the second consecutive cycle a lane has found real work behind a stale status line**, and it is the same distinction QE keeps reporting from the other side ([B-152](docs/BUGS.md)).

### ⚡ QE refined [B-155](docs/BUGS.md) rather than applying it mechanically

**Lane A was 2 ahead / 1 behind — diverged by the letter, so B-155 would have returned it to its lane.** ⛔ **That reading is wrong, and this cycle is why.**

> **The *1 behind* was QE's own Closeout commit.** **Every lane is 1 behind immediately after a Closeout, by construction** — so *"return whenever behind > 0"* would mean **QE never integrates anything without a round-trip, every single cycle.**

✅ **The line that actually holds: rebase, and let the rebase decide.** **Lane A replayed onto `integration` with zero conflicts** — mechanically identical to a fast-forward. **Lane C's fourteen still conflict across eight files, four of them narrative registers.** ⚡ **One is a moved base; the other is diverged content, and only the rebase can tell them apart.**

### ✅ Lane B's branch is a stale pointer, resolved rather than assumed

**`lane-b-commercial-profile` reads 2 ahead / 237 behind.** ⚡ **Patch-id over a 300-commit window: one is a duplicate already on `main`, and the other is an abandoned claim commit for [TASK-468](docs/BACKLOG.md) — a row `integration` now records against Lane A.** ✅ **Nothing is held.** **Lane B was retired by [D-165](docs/DECISION_REGISTER.md); the branch is harmless and stays, because a lane branch is permanent by name.**

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4278 backend** · **1900 frontend** *(+9, +1 file)* · **95.07%** · **398 invariants** · **851 files typed** · **37 contracts** · ⛔ **`ruff` red, ungated — [B-211](docs/BUGS.md)** |
| **Release** | **147 runs recorded, 139 certified** · `promoted == certified` ✓ · **first attempt** |
| **Architecture** | Migration `0045` **reversible, verified** · **DR nothing lost, 5 restart stages** · smoke 24 stages in 203s |
| **Dependency** | ⚠️ **Lane C diverged, seventh exclusion — [B-155](docs/BUGS.md)** · nobody blocked · ⛔ **[C-245](docs/LANE_COORDINATION.md) needs the product owner, and Lane A shipped around it rather than waiting** |
| **Customer Value** | ✅ ⚡ **An expired invitation says so** |
| **Process** | ✅ **No QE self-defect this cycle.** ⚡ **[B-156](docs/BUGS.md) and [B-157](docs/BUGS.md) remain open and unfixed — both are gates, and fixing a gate is a slice** |

---

## 1d · Release summary — 2026-08-09, cycle 141

**Derived from the promoted commit `a540f5e`.** **Ninety-six promotions.** ⚡ **A screen, a defect the browser found that no static gate structurally could, and a lane branch that fast-forwarded for the first time in six cycles.**

### ✅ What a customer gets

> **A seller opens the Signal Center, sees what is waiting and on which account, and every item leaves the queue by a decision.**

Three states as tabs with a count, grouped and counted by signal type. ⚡ **A dismissal cannot be recorded without a reason** — and the lane recorded *why* that is not politeness: *"dismissal reasons feed rule precision"*, so an empty one is a lost measurement.

### ⚡ The headed walk earned its place, and this is the finding of the cycle

> *"The first draft put the entrance inside the attention list's **POPULATED** branch. A workspace with an empty attention list had **no way into the Signal Center at all** — and that is the reader most likely to want one."*

⛔ **`reachability.py` passed it.** **A static scan sees a `Link` in the source and cannot see which branch renders it.** ✅ **The browser found in seconds what the gate structurally cannot**, and the entrance moved to page level with a journey asserting it so it cannot regress.

> ⚡ **This is [D-134](docs/DECISION_REGISTER.md)'s whole argument arriving as evidence rather than as policy** — *"the purpose is not verification; the assertions already did that."* **Here the assertions passed and the product was broken for exactly the customer it was built for.**

### ✅ Two design fields reported absent rather than invented

**[C-251](docs/LANE_COORDINATION.md).** The design draws five row fields; the contract carries three.

| | |
|---|---|
| **`summary`** | The catalog's `why_it_matters` is **a fact about the *type***. Rendering it per row prints one sentence under every signal of that type — ⛔ *"it would look right and be wrong on every row"* |
| **`confidence`** | **The string appears nowhere in `lib/api/types.ts`**, and `components/ui/confidence.tsx` is imported by nothing — **a primitive built for a fact the platform does not publish** |

✅ **Reported, not invented.** ⚡ **That is [D-151](docs/DECISION_REGISTER.md) ④ applied one layer up, by the lane, unprompted.**

### ⛔ [B-156](docs/BUGS.md) — QE's own journey run reported 157 failures and had measured nothing

**QE ran the full journey suite because the plan named it, and got eleven red suites across authentication, workflows and commercial profile.** ⚠️ **It looked exactly like [B-209](docs/BUGS.md).**

**It was an abort.** `E2E_URL` is built as `http://localhost:$(SIGNORA_WEB)`, and `environments.py` derives no web port off a lane branch — **so the URL was `http://localhost`, with no port**, and every test failed in ~300ms against port 80.

⛔ **Both of the suite's URL guards passed it, and both are correct.** The URL *is* set; the port is not 3000 or 8000 — **because there is no port at all.** Proved rather than reasoned: `new URL("http://localhost").port === ""`.

> ⚡ **The instruction that caught it is the standing one**: *"if a result changes on an unchanged tree, read the error before reporting a verdict."* ⛔ **Reporting those 157 as a regression would have pointed a false lead at whichever lane last touched the frontend.**

**So this cycle's claim is bounded, and stated as such: the journey suite was *not* run at `a540f5e`.** Two attempts, both aborted on environment. **Playwright sits inside the gate shortfall [B-131](docs/BUGS.md) prints every run**, so certification neither ran it nor claimed to. **Lane A reports it walked headed and passing — recorded as the lane's claim.**

### ✅ Lane A fast-forwarded — the §20e path, not a cherry-pick

**Six cycles of selective cherry-picking ended here**: `lane-a-product-surface` was **3 ahead / 0 behind**, so `git merge --ff-only` was the whole integration. ⚡ **Two of its three commits were already on `lane-qe` by patch-id and the ff made that irrelevant** — which is the argument in [B-155](docs/BUGS.md) demonstrating itself one branch over.

### ⛔ Lane C excluded a sixth time — now a row, not an observation

| | |
|---|---|
| **Held** | [D-203](docs/DECISION_REGISTER.md) §2 · [D-204](docs/DECISION_REGISTER.md) — *all 29 workflows decomposed* · [D-205](docs/DECISION_REGISTER.md) · two coordination republishes |
| **Diagnosis** | ⚡ **Not "generated files".** `origin/lane-c-sync` is **12 ahead / 2 behind — diverged**, and a mid-series pick conflicts across **eight files, four of them narrative registers** |
| **Is anyone blocked?** | ⛔ **No.** Lane A delivered this cycle and holds `TASK-1400` |
| **The correction** | ✅ **§20e already says it** — *"a branch that will not fast-forward is returned to its lane."* **[B-155](docs/BUGS.md) is filed against QE's own procedure** |

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4278 backend** · **1891 frontend** *(+20, +1 file)* · **95.07%** · **398 invariants** · **851 files typed** · **37 contracts** · ⛔ **`ruff` red, ungated — [B-211](docs/BUGS.md)** |
| **Release** | **146 runs recorded, 138 certified** · `promoted == certified` ✓ · **first attempt** |
| **Architecture** | Migration `0045` **reversible, verified** · **DR nothing lost, 5 restart stages** · smoke 24 stages in 210s |
| **Dependency** | ⚠️ **Lane C diverged, sixth exclusion — [B-155](docs/BUGS.md)** · nobody blocked |
| **Customer Value** | ✅ ⚡ **The Signal Center is reachable, including from an empty attention list** |
| **Process** | ⛔ **One QE self-defect — [B-156](docs/BUGS.md)**, after two clean cycles. ✅ **Caught by QE's own standing rule before it reached a report** |

---

## 1d · Release summary — 2026-08-09, cycle 140

**Derived from the promoted commit `2bf7450`.** **Ninety-five promotions.** ⚡ **A lane that found its own next task by re-reading its held rows, and a design note implemented as a property rather than as copy.**

### ✅ What a customer gets

> ***"Skip the rest of setup?"* with the consequence stated in product terms.**

**The design's note is implemented as a *property*, not as wording:**

> *"States the consequence in product terms and lets them go. **No dark pattern, no second ask.**"*

⚡ **Skip performs exactly one navigation, to the flow's single exit seam — and a test case fails if a second prompt appears.** ⛔ **That is the difference between honouring a design note and quoting it**: the promise is enforceable, so it cannot rot into a second confirmation later.

### ✅ The lane did not idle on "nothing READY"

> *"`TASK-1400` is delivered and on `main`; the `READY` filter showed zero rows, **but the test is genuine dependency, not dispatch state.** Re-reading this lane's OWN held rows found `TASK-469` with milestone 2 outstanding and nothing blocking it."*

⚡ **That is §20e's continuous-execution rule read correctly**: a lane stops when there is no work, not when a projection says so. **QE has spent several cycles reporting the opposite condition — a queue naming work that did not exist** ([B-152](docs/BUGS.md)) — **and this is the same distinction from the lane's side.**

### ⛔ Lane C's work has been excluded four cycles running

**All four of its commits conflicted on `coordination.toml` and `queues/lane-a.toml` again.** ⚡ **QE does not hand-resolve a generated file — the repair is the generator** — **but four consecutive exclusions is a measurement, not an incident.**

| | |
|---|---|
| **Held** | [D-203](docs/DECISION_REGISTER.md) §2 · [D-204](docs/DECISION_REGISTER.md) — *all 29 workflows decomposed, five platform rows* · a coordination republish |
| **Is anyone blocked?** | ⛔ **No.** **Lane A has `TASK-1400` claimable and is working**, and Lane C is **6 commits behind `integration`** |
| **Cost** | ⚠️ **Planning throughput, not delivery.** **Lane C rebases and the conflicts recur, because `integration` moves under it every cycle** |

> ⚡ **Recorded rather than acted on.** ⛔ **The fix is not QE resolving generated files by hand** — that is how [B-411](docs/BUGS.md) happened one register over. ✅ **If it persists it earns a row against the generator's rebase story, which is Lane C's.**

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4278 backend** · **1871 frontend** *(+9)* · **95.07%** · **398 invariants** · **851 files typed** · **37 contracts** · ⛔ **`ruff` red, ungated — [B-211](docs/BUGS.md)** |
| **Release** | **145 runs recorded, 137 certified** · `promoted == certified` ✓ · `--audit-main` clean · **first attempt** |
| **Architecture** | Migration `0045` **reversible, verified** · **DR nothing lost** · smoke 203s |
| **Dependency** | ⚠️ **Lane C excluded four cycles running** on generated-file conflicts — **nobody blocked, planning throughput the cost** |
| **Customer Value** | ✅ ⚡ **Setup can be left, once, with the cost stated** |
| **Process** | ✅ **Two consecutive cycles with no QE self-defect**, after five |

---

## 1e · Release summary — 2026-08-09, cycle 139

**Derived from the promoted commit `070bef1`.** **Ninety-four promotions.** ⚡ **[B-153](docs/BUGS.md)'s lesson paid for itself one cycle after it was written.**

### ✅ The check caught a duplicate, and this time QE read the list

**Cherry-picking Lane C's rebased branch produced a second `B-413` row** — its fix was promoted in cycle 138, and the rebased variant carried the row again, **byte-identical at 4179 characters.**

```
B- identifiers are allocated twice: B-413.
```

⚡ **QE read the finding list rather than grepping for the finding it expected**, which is exactly what [B-153](docs/BUGS.md) cost one cycle earlier. ✅ **Folded before certifying; nothing lost, the sections were identical.**

> ⛔ **The habit that produced [B-150](docs/BUGS.md), [B-151](docs/BUGS.md), [B-153](docs/BUGS.md) and [B-154](docs/BUGS.md) is the same one: trusting the shape of an answer instead of reading it.** ✅ **This is the first cycle where it was caught by the practice rather than by a lane.**

### ✅ Both lanes closed their own rows

| | |
|---|---|
| **[B-217](docs/BUGS.md)** *(Lane A)* | Closed as fixed by [B-154](docs/BUGS.md) — ⚡ **and the lane noted its own miss: *"the severity was wrong for three polls"*** |
| **[B-216](docs/BUGS.md)** *(Lane A)* | ⚡ ***"Found by re-checking, which is the rule B-217 just cost"*** |
| **Workflow 9's state** *(Lane C)* | Read `planned` while two of its three milestones were on `main` |

### ⛔ Two Lane C commits excluded, same reason as always

**[D-202](docs/DECISION_REGISTER.md) and [D-203](docs/DECISION_REGISTER.md) §2 conflicted on `coordination.toml` and `queues/lane-a.toml`.** ⚡ **Generated files — the repair is the generator, and QE does not hand-resolve one.**

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4278 backend** · **1862 frontend** · **95.07%** · **398 invariants** · **851 files typed** · **37 contracts** · ⛔ **`ruff` red, ungated — [B-211](docs/BUGS.md)** |
| **Release** | **144 runs recorded, 136 certified** · `promoted == certified` ✓ · `--audit-main` clean · **first attempt** |
| **Architecture** | Migration `0045` **reversible, verified** · **DR nothing lost** · smoke 175s |
| **Dependency** | ✅ Nothing held |
| **Customer Value** | ⛔ **None.** **Three rows closed and a register kept honest** |
| **Process** | ✅ **A quiet cycle, and the first in five where the defect QE would have promoted was caught by QE's own practice** |

---

## 1e · Release summary — 2026-08-09, cycle 138

**Derived from the promoted commit `5bc7ef5`.** **Ninety-three promotions.** 🔴 **The first promotion in six days made under a promotion gate that actually works.**

### 🔴 [B-413](docs/BUGS.md) — the gate said *"not blocked"* seventy times, and could not have said anything else

**Lane C found it.** ⛔ **`unresolved` required the state token at character zero; the register writes `` **`OPEN`** `` in bold.** **29 of 39 open rows read as resolved, and `blocks_promotion` returned `False` for every row in the file.**

> ⚡ **`registers.py` exists because two tools answered *"is this bug blocking?"* differently — and it then contained the divergence itself:** `state` located the token with `find`, `unresolved` demanded position zero. ✅ **`unresolved` is now derived from `state`. One reading, one question asked of it.**
>
> ⚠️ **And the test that should have caught it passed on an asymmetry:** *"`FIXED` constructed bolded, `OPEN` bare — so the only form the register uses for an open row was never built."*

### 🔴 The six days are QE's to account for

**§20e: *"`integration` never fast-forwards to `main` with an open 🔴 bug."*** ⛔ **[B-209](docs/BUGS.md) was 🔴 and `OPEN` from 2026-08-06. There have been 70 Closeout commits since.**

> ⛔ **QE is not claiming those promotions were harmless — that is not knowable in retrospect.** ✅ **What is knowable: the rule was not enforced, QE did not notice, and the reason is that QE read the gate's answer instead of the register.**
>
> ⚠️ **[B-151](docs/BUGS.md) said exactly that about a different line three cycles ago, and QE fixed the sentence rather than the habit.**

### ✅ So QE fixed [B-209](docs/BUGS.md) rather than carrying it

**It was assigned to QE all along** — the repository-wide journey suite is QE's under §20e — **and the fix was the one word the row itself prescribed.**

| | |
|---|---|
| `pages/business.ts:37` | `getByLabel('Name')` → **`{ exact: true }`**. The App Shell header search is on every screen, named *"Find an account by name"* |
| `commercial-profile.spec.ts:174` | **The same defect on a second browser context**, same shell, same dialog |
| `auth-journey.spec.ts` | ⛔ **Deliberately untouched** — `/sign-in` and `/sign-up` carry no shell header. **Changing a passing test on a pattern match is [B-411](docs/BUGS.md)'s failure in the other direction** |

✅ **And QE proved the repaired gate can fail before trusting it**: reopened B-209 in the tree → *"BUGS.md carries 1 unresolved 🔴 (B-209)"*; restored → silence.

### ✅ What a customer gets — and D-200 already moving

| | |
|---|---|
| ⚡ **`TASK-1400` — the Authenticated Entry Engine** *(Lane A)* | One resolver, twenty-one reason codes, **+35 frontend tests**. `resolveEntry` exists, five cycles after [D-193](docs/DECISION_REGISTER.md) ruled it |
| ✅ **[C-105](docs/LANE_COORDINATION.md) §2 adopted** *(Lane A)* | **Lane A submissions now carry an `Impact` field**, `TASK-1400` the first — **[D-200](docs/DECISION_REGISTER.md) §2, one cycle after it was ruled, without QE asking twice** |

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4278 backend** *(+6)* · **1862 frontend** *(+35)* · **95.08%** · **398 invariants** · **851 files typed** · **37 contracts** · ⛔ **`ruff` red, ungated — [B-211](docs/BUGS.md)** |
| **Release** | **143 runs recorded, 135 certified** · `promoted == certified` ✓ · `--audit-main` clean · **first attempt** |
| **Architecture** | Migration `0045` **reversible, verified** · **DR nothing lost** · smoke 211s |
| **Dependency** | ✅ **Four Lane C commits excluded** on generated-file conflicts — **the repair is the generator** |
| **Customer Value** | ⚡ **The entry decision has one owner instead of five hardcoded redirects** |
| **Process** | 🔴 **Four QE self-defects of one family this session** — [B-150](docs/BUGS.md) skipped a check, [B-151](docs/BUGS.md) transcribed, [B-153](docs/BUGS.md) filtered, [B-154](docs/BUGS.md) read a check that did not cover the file. ⛔ **[B-413](docs/BUGS.md) is the fifth and the most expensive: QE trusted a gate's silence for six days.** ⚡ **Every one was found by measuring, and three of five by another lane** |

---

## 1e · Release summary — 2026-08-09, cycle 137

**Derived from the promoted commit `f94c06a`.** **Ninety-two promotions.** ⛔ **A conflict marker sat in the decision register on `main` for two cycles, and the check that should have caught it did not read that file.**

### ⛔ [B-154](docs/BUGS.md) — found by Lane A, in a register QE had promoted

```
209:<<<<<<< HEAD
213:>>>>>>> 809a3e43 (D-194 — the reconciliation found the entry decision already shipped)

$ python3 infra/state-check.py
(no marker finding)
```

**It arrived in `809a3e43` — a commit QE cherry-picked and promoted.** ⛔ **It wrapped the `D-195` and `D-196` rows against an empty incoming side: a pure deletion that deleted nothing anybody wrote.** ✅ **Both rows kept.**

### ⛔ Three of this class, and each failed differently

| | |
|---|---|
| **[B-150](docs/BUGS.md)** | The check **was skipped** |
| **[B-153](docs/BUGS.md)** | The check **was run and filtered** — output said `0` and looked like a pass |
| **[B-154](docs/BUGS.md)** | ⛔ **The check was run, read in full, and did not cover the file** |

> ⚡ **[B-150](docs/BUGS.md)'s row argued against building a second instrument, because *"the first was not consulted"*. That was right then and is not an argument here** — **this time nothing existed to consult.** ⛔ **The list was the defect, not the check.**

✅ **The loop now reads six registers**, adding `DECISION_REGISTER.md` and `DECISION_QUEUE.md`, and **was proved able to fail before shipping**: 1 finding against the corrupt tree, 0 against the repaired one.

> ⚠️ **The rule QE is applying rather than proposing: a register QE reconciles at merge is a register the corruption check must read.** **`DECISION_REGISTER.md` was reconciled by QE in every cycle it appeared in, and read by nothing.**

✅ **Found by a lane, not by QE — the third time this session**, and §20e's own claim about this repository.

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4272 backend** · **1827 frontend** · **95.07%** · **398 invariants** · **851 files typed** · **37 contracts** · ⛔ **`ruff` red, ungated — [B-211](docs/BUGS.md)** |
| **Release** | **142 runs recorded, 134 certified** · `promoted == certified` ✓ · `--audit-main` clean · **first attempt** |
| **Architecture** | Migration `0045` **reversible, verified** · **DR nothing lost** · smoke 153s |
| **Dependency** | ✅ **Lane A is building `TASK-1400`**, the Authenticated Entry Engine |
| **Customer Value** | ⛔ **None.** **A register repair and a widened guard** |
| **Process** | ⚡ **Three QE self-defects of one class in three cycles, each with a different cause and a different fix.** ⛔ **The pattern is not carelessness at one step — it is trusting an instrument's silence without checking what it looks at** |

---

## 1f · [D-200](docs/DECISION_REGISTER.md) Smart Certification Strategy — what exists, and what does not

**Ruled 2026-08-09 by the product owner.** ⚡ **QE's assessment, and the honest headline is that most of §1 already exists and has never been *applied*.**

### ✅ What already exists — the Validation Planner, since [D-115](docs/DECISION_REGISTER.md)

**`certification-guard.py --plan <range>` already answers §1's eight questions**, and QE has printed its verdict in every cycle of this session:

```
VALIDATION PLAN — 22 changed path(s)
profile: platform
  documentation  docs/BUGS.md, docs/LANE_COORDINATION.md
  frontend       app/(app)/profile/locale-panel.tsx (+7)
  module         workspace_tenancy/application/use_cases/preferences.py (+7)
  persistence    migrations/versions/0044_person_preferences.py
  platform       signora_platform/authorization/enforcer.py
  security       authorization/policies/policy.csv
```

⚡ **It discriminates**: this session produced `platform`, `documentation`, `documentation+frontend`, and `documentation+frontend+module+persistence`. ⛔ **`docs/coordination/**` classifies as `platform` because three gates read it — a directory prefix would have called it documentation.**

### ⛔ The gap is one line, and it is [B-131](docs/BUGS.md)

**`REQUIRED_GATES` is a constant.** ⚡ **Every run executes all six regardless of the computed profile**, and the record says so out loud every time:

```
validation plan   platform: 10 planned gate(s) NOT recorded
                  reported only — nothing skipped, nothing refused (B-131)
```

✅ **[427](docs/architecture/427-impact-based-validation.md) is exactly D-200, written as a five-step migration.** **Step 2 — *record the computed profile, still run everything* — has been live for ~20 runs.** ⛔ **Steps 3–5 apply it, and were gated on step 1's evidence.** ⚡ **That evidence now exists.**

### ⚠️ What QE cannot yet tell you, and it is the thing D-200 optimises

> **The certification record captures gates, coverage, invariants, tools, conditions and profile. ⛔ It does not capture *duration*.**

**So the bottleneck has never been measured.** ⚡ **Total is ~17–18 minutes; `smoke` is the only timed stage at 141–303s.** ⛔ **Everything else is unattributed**, and QE will not propose narrowing a suite it cannot show is the cost.

✅ **First step, and it is [427](docs/architecture/427-impact-based-validation.md) step 2's own shape — record before acting: per-gate duration in the certification record.** **One cycle of data then says whether the win is in `pytest`, `smoke`, database provisioning, or the frontend build.**

### 🔴 The constraint that does not move

**[D-167](docs/DECISION_REGISTER.md), the product owner's own earlier ruling:** ***"If impact cannot be determined confidently: default to broader certification. Correctness always takes priority over execution speed."***

⛔ **And the planner already enforces it structurally — *unknown paths widen, never narrow*.** ⚡ **The vacuity risk [427](docs/architecture/427-impact-based-validation.md) §1 names is the one to design against: under a *computed* required set, a gate may be legitimately absent — and a mis-classification then reads as a pass.** ✅ **`missing_gates` measures against the full set today, and must keep doing so.**

### ⚠️ Two parts of D-200 are not QE's to implement

| § | Whose |
|---|---|
| **§2 — Lane A submits an impact summary** | **Lane A's**, and it belongs in the **Slice Handoff**, which already carries `Reuse`, `Preserved`, `Reachable`, `Rollback`, `Budget` |
| **§5 — Product Office states expected impact on task creation** | **Lane C's** |

⛔ **QE cannot write either lane's obligations into their files.** ✅ **Raised as a coordination item so both learn their half from `integration` rather than from a poll narrative** — **which is the lesson [B-153](docs/BUGS.md) cost one hour ago.**

---

## 1e · Release summary — 2026-08-09, cycle 135

**Derived from the promoted commit `3373af7`.** **Ninety promotions.** ⛔ **Opened by §20e's synchronization rule, not by executable change — and the distinction from six polls earlier is the whole point.**

### ⛔ Why this cycle ran when the last six did not

**QE reported the same condition for seven consecutive polls and declined to open a cycle each time.** ⚡ **The rule fires on one clause: *"`READY` work exists only outside `integration`."***

| Poll | Measured | Verdict |
|---|---|---|
| **135 ×6** | `TASK-1400` **`SEQUENCED` everywhere** — Lane C 36 behind, nothing to merge | ⛔ **A preparation gap.** No cycle |
| **This one** | `TASK-1400` **`READY` on `lane-c-sync`, `SEQUENCED` on `integration`** | ✅ **A delivery gap.** Highest repository priority |

> ⚡ **Same symptom, opposite answer, and the difference is which side the missing work is on.** ⛔ **Calling the first one synchronization would have sent QE looking for a merge with nothing to merge; calling the second one preparation would have left a lane idle with its work sitting on a branch.**

### ✅ [B-152](docs/BUGS.md) `VERIFIED` — Lane C repaired the *ruling*, not the file

```
key=lambda r: (not r.on_integration, …)
```

⛔ ***"That merely PREFERRED an on-integration row. With none available it named an off-integration one anyway."*** ✅ **[C-425](docs/LANE_COORDINATION.md) says *"the ref does not get to be ahead; it gets to be fast"* — and `on_integration` was added to prevent exactly this, then wired as a tiebreak.** **Now a filter.**

**And the office named its own miss unprompted:** *"This office republished twice in between and did not check — **the check existed and was not run against the thing it was written for.**"* ⚡ **That is [B-150](docs/BUGS.md)'s lesson reached independently, one office over, within a day.**

### ⚡ A check that was wrong for one commit, and firing it is what proved it

**QE observed the second projection still named the blocked row** and **declined to file a second row** — same defect mid-repair. **Lane C's first fix demanded the two files be *identical*, and running it immediately fired on a correct state:**

| File | What `current` means |
|---|---|
| `coordination.toml` | **claimable on `integration` today** |
| `queues/lane-a.toml` | **the next row prepared** |

⛔ ***"A check that calls a correct state a defect is worse than no check."*** ✅ **Narrowed to what [C-425](docs/LANE_COORDINATION.md) actually says: neither file may name a row whose state on `integration` contradicts it.** **QE re-ran it: zero findings, and `TASK-470` is caught.**

### ✅ The result, measured on `main`

```
TASK-1400   ⏸️ SEQUENCED   →   ✅ READY
```

⚡ **The Authenticated Entry Engine is claimable, and `resolveEntry` — ruled at [D-193](docs/DECISION_REGISTER.md) and unbuilt for five cycles — has a row that may build it.**

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4272 backend** · **1827 frontend** · **95.07%** · **398 invariants** · **851 files typed** · **37 contracts** · ⛔ **`ruff` red, ungated — [B-211](docs/BUGS.md)** |
| **Release** | **140 runs recorded, 132 certified** · `promoted == certified` ✓ · `--audit-main` clean · **first attempt** |
| **Architecture** | Migration `0045` **reversible, verified** · **DR nothing lost** · smoke 184s |
| **Dependency** | ✅ **Cleared.** **Lane A has a claimable row for the first time in eight polls** |
| **Customer Value** | ⛔ **None.** **The cycle's product is an unblocked lane** |
| **Process** | ⚡ **Two offices caught their own misses this cycle without being told** — Lane C's unrun check, and QE's earlier refusal to file a second row that would have been wrong. **The register cost one row and no rework** |

---

## 1e · Release summary — 2026-08-08, cycle 134

**Derived from the promoted commit `9378e82`.** **Eighty-nine promotions.** ⚡ **[B-215](docs/BUGS.md) closed on its third hypothesis — and the two wrong ones were cleared by measurement, not argument.**

### ✅ [B-215](docs/BUGS.md) — it was a lost keystroke, not a lost request

> **The profile said *"Saved"* and stored nothing.**

**The cause was in the panel, not the transport:** *"the load effect seeded the inputs from the server, and when it resolved after the first character it overwrote what had been typed. Save then sent the empty field as `null`, the row stored `null`, and the screen confirmed a save that had happened exactly as instructed."*

⚡ **Both earlier suspects were cleared by measurement rather than argument** — a `PATCH` straight to the API stored the value; the same `PATCH` through `/api/proxy` stored it too. ***"Only after both came back correct was it obvious that nothing was lost in transit."***

> ⛔ **Three hypotheses, two withdrawn, one right.** ✅ **The lane never softened a wrong lead into a maybe** — cycle 133 deleted the proxy theory outright, and this cycle names the actual line.
>
> ⚠️ **And the defect class is the expensive one: a UI that *confirms* a write it did not make.** **Nothing downstream was wrong** — the row stored exactly what it was sent.

### ✅ Screen 04 — five preferences, and two of them are policies

**Migration `0045` adds five columns to the table `0044` created** — ⚡ *"five columns rather than a second table, because they are the same person's choices in the same workspace and splitting them would give one aggregate two rows to keep in step."* **Verified down to `0044` and back.**

> ✅ **Consent is never inferred, and the defaults are where that is said.** *"Everything unexpressed sits at the conservative end. Two default to on and that is not a contradiction: **neither is a permission over the customer's data.**"*

### ✅ Milestone 3 blocked, with both reasons stated

**`TASK-470` reports milestones 1 and 2 delivered and milestone 3 blocked** — **named rather than silently deferred**, which is the `Limitations` field doing its job again.

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4272 backend** · **1827 frontend** *(+13)* · ✅ **95.08%** *(recovering)* · **398 invariants** · **851 files typed** · **37 contracts** · ⛔ **`ruff` red, ungated — [B-211](docs/BUGS.md)** |
| **Release** | **139 runs recorded, 131 certified** · `promoted == certified` ✓ · `--audit-main` clean · **first attempt** |
| **Architecture** | ⚡ **Migration `0045`, reversed to base and re-applied** · **no new table — columns on `person_preferences`, so no classification needed** · **DR nothing lost** · smoke 198s |
| **Dependency** | ⚠️ **`resolveEntry` still ruled and unbuilt** — `TASK-1400` |
| **Customer Value** | ✅ ⚡ **A person chooses what Signora may do for them — and the screen no longer lies about saving it** |
| **Process** | ⚡ **A defect register that carried three hypotheses and ended with one, having deleted the other two.** **That is the register staying believable**, which is the only property that makes it worth reading |

---

## 1e · Release summary — 2026-08-08, cycle 133

**Derived from the promoted commit `2ecfe98`.** **Eighty-eight promotions.** ⚡ **A lane withdrew its own hypothesis from the defect register rather than softening it — and a sentence in the design decided where a value is stored.**

### ✅ [B-215](docs/BUGS.md) — the hypothesis was wrong, and the register says so

**The row had said the `/api/proxy` hop appears not to forward a `PATCH` body.** ⛔ **It does** — *"the route exports `PATCH`, includes it in `FORWARDED`, and reads the body with `await request.text()` for every method except `GET`. **Ruled out by reading it.**"*

> ⚡ ***"Withdrawn rather than softened. A hypothesis in a defect register is read as a lead, and a wrong one costs the next person the same afternoon it cost this lane."*** ✅ **The symptom and its evidence are unchanged and still measured; only the guess is gone.** ⛔ **And narrowed without guessing a second time.**
>
> **This is the register used as an instrument rather than a diary** — §2's *the repository itself should always tell the truth*, applied to a lead nobody had acted on yet.

### ✅ Appearance belongs to the account, not the browser

**The design's own sentence decided the storage:** *"applies to this account on every device you sign in from, not to this browser."*

⛔ **So it is server-persisted preference and there is no `localStorage` in the panel — and a test asserts there is none**, because *"a theme cached in the browser is right on the laptop it was chosen on and wrong on every other one, which is the precise promise that sentence makes."*

✅ **`system` is stored as `system` and never resolved.** *"Follows your device, switching at sunset"* is a deferral; **answering it with `light` or `dark` would replace the deferral with a snapshot of the moment it was chosen.**

### ✅ Coverage held — the fall stopped

```
95.38%  →  95.18%  →  95.19%  →  95.07%  →  95.07%     floor 95
```

⚡ **Flagged last cycle before it became a surprise; this cycle it did not move.** **No action taken and none was needed** — the frontend-only profile went in at +15 tests with no backend surface.

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4272 backend** · **1814 frontend** *(+15)* · ✅ **95.07%** *(held)* · **398 invariants** · **851 files typed** · **37 contracts** · ⛔ **`ruff` red, ungated — [B-211](docs/BUGS.md)** |
| **Release** | **138 runs recorded, 130 certified** · `promoted == certified` ✓ · `--audit-main` clean · **first attempt** |
| **Architecture** | Migration `0044` **reversible, verified** · **DR nothing lost** · smoke 228s |
| **Dependency** | ⚠️ **`resolveEntry` still ruled and unbuilt** — `TASK-1400` |
| **Customer Value** | ✅ ⚡ **A theme that follows the person rather than the machine** |
| **Process** | ⚡ **A lane deleted its own wrong lead from a shared register.** **That is harder than filing one and worth more** — the register only stays useful if what is in it is still believed |

---

## 1e · Release summary — 2026-08-08, cycle 132

**Derived from the promoted commit `2fe9843`.** **Eighty-seven promotions.** ⚡ **Three of the design's seven profile fields do not ship, and the design's own headline number is why.**

### ✅ What a customer gets

**Workflow 9 screens `01` and `02`, composed into `/profile`** — the identity the account holds, **the two fields a person actually owns**, language, time format, and the timezone prompt.

### ⛔ The three that do not ship, and the number that decided it

> **The design's headline number on this screen is `0` — *"edits accepted that a sync would undo"* — and the three field kinds exist to keep it true.**

**Measured: no directory integration exists anywhere in the repository.** So:

| Field | Why not |
|---|---|
| **Job title · Department** | Drawn *"From directory"*. ⛔ **Nothing in the product knows them.** *"A locked field with no sync behind it is a rule the product does not have painted as one it does"* ([D-156](docs/DECISION_REGISTER.md) ④) |
| **Mobile number** | Drawn under *"Verified 14 Mar 2026"*. ⛔ **Nothing stores a number and nothing verifies one** |

> ⚡ **This is the fifth consecutive workflow where the lane refused to render what the product cannot honour** — `/join`, `/sso`, screen 07's OTP boxes, Workflow 5's device count, and now three profile fields. **Every one measured first.**

### ✅ No shell, deliberately

> *"The panels stand alone because the App Shell is Workflow 13 and not built, so there is no shell here and building one would be the §20d defect."*

⚡ **[§20d](CLAUDE.md) is *strict milestone ownership*, and the lane named it rather than borrowing ahead.**

### ✅ The second `Resource` this session, on the same terms

**`Resource.PREFERENCES` + four `policy.csv` rows.** ⛔ **Its own resource *"because a preference is one person's, and every other resource here is the workspace's."*** ✅ **And the scoping is stated as the endpoint's and the RLS policy's, not the policy file's** — *"a grant cannot be widened into reading a colleague's preferences by editing `policy.csv`."*

### ⚠️ Coverage has fallen three cycles running

```
95.38%  →  95.18%  →  95.19%  →  95.07%     floor 95
```

⛔ **Still above the floor and no gate has failed.** ⚠️ **But it is 0.31 points off in four cycles, and the margin is now 0.07** — **recorded here so the fourth fall is met with a measurement rather than a surprise.** ⚡ **The cause is visible and benign so far: three large slices landed backend code faster than backend tests**, and each carried its own module suite.

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4272 backend** *(+5)* · **1799 frontend** *(+31)* · ⚠️ **95.07%** *(floor 95)* · **398 invariants** · **851 files typed** · **37 contracts** · ⛔ **`ruff` red, ungated — [B-211](docs/BUGS.md)** |
| **Release** | **137 runs recorded, 129 certified** · `promoted == certified` ✓ · `--audit-main` clean · **first attempt** |
| **Architecture** | Migration `0044` **reversible, verified** · **DR nothing lost** · smoke 226s |
| **Dependency** | ⚠️ **`resolveEntry` still ruled and unbuilt** — `TASK-1400` |
| **Customer Value** | ✅ ⚡ **A person's profile, honest about what it cannot do** |
| **Process** | ⚡ **A design's own success metric was used as the argument for shipping less of it** — the strongest form of the refusal this lane keeps making |

---

## 1e · Release summary — 2026-08-08, cycle 131

**Derived from the promoted commit `a85d852`.** **Eighty-six promotions.** ⚡ **A lane received a ruling through the notice channel, verified it was not yet actionable, and built the half that was — without inventing the half that was not.**

### ⚡ The notice channel carried its first ruling, and the lane checked it

**[D-193](docs/DECISION_REGISTER.md)/[D-194](docs/DECISION_REGISTER.md) reached Lane A through the channel Lane C built two cycles ago:**

> *"'Authenticated Entry' is now the authority for ALL post-login behaviour. `TASK-468` and `TASK-469` have NO DEFINED EXIT… do NOT choose a destination in either flow."*

✅ **The lane measured rather than assumed:** *"`resolveEntry` exists nowhere on `origin/integration`, and D-193/D-194 are not in its decision register. **So the ruling is authoritative and not yet actionable** — §20e, executable work comes from `integration` and nowhere else, and a decision is actionable when `integration` records it."*

> ⛔ ***"`resolveEntry` was NOT written here. Inventing the spec's shape is how the next lane inherits a guess."*** ⚡ **So onboarding stopped choosing a destination, and did not invent the mechanism that will choose one.** **That is the [five states of a decision](CLAUDE.md) applied exactly** — authoritative at ruling, actionable at `integration`.

### ✅ [B-214](docs/BUGS.md) fixed by the lane that found it, in its own module

**An expired invitation and a withdrawn one no longer arrive identical.**

> *"The domain always knew which settled state it was. `InvitationNotPendingError` has carried `state` since it was written, and its own docstring says **'this was withdrawn' and 'this expired' are different sentences to a customer and only one of them offers a next step.**"*

⚡ **No backlog row was needed** — *"the bug register is the authority for a defect and the module's current assignee fixes it"* — **and it corrects what this lane reported one cycle earlier.**

### ✅ `TASK-470` — the preference store, and the scoping question it refused to assume

**Migration `0044`, `person_preferences`.** ✅ **Verified by QE: classified in `TENANT_OWNED_TABLES` (54 tables), inside the invariant loops, and `0044` reverses to base and re-applies.**

### ⚠️ What QE had to resolve carefully, and nearly lost

**`docs/BACKLOG.md` conflicted in two regions where `THEIRS` carried *two* lines: a stale status **and a new [D-193](docs/DECISION_REGISTER.md) constraint row Lane C had added.**

⛔ **A naive "take ours" would have silently dropped both constraint rows** — the [B-411](docs/BUGS.md) failure exactly. ✅ **Resolved as the lane's newer status *plus* Lane C's new row, asserted line by line**, and the apparent duplicate afterwards was checked and is benign: **the same constraint deliberately applied to `TASK-468` and `TASK-469`.**

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4267 backend** *(+16)* · **1768 frontend** · **95.19%** *(floor 95)* · **398 invariants** · **849 files typed** · **37 contracts** · ⛔ **`ruff` red, ungated — [B-211](docs/BUGS.md)** |
| **Release** | **136 runs recorded, 128 certified** · `promoted == certified` ✓ · `--audit-main` clean · **first attempt** |
| **Architecture** | ⚡ **Migration `0044`, reversed and re-applied** · **54 tenant-owned tables** · **DR nothing lost** · smoke 218s |
| **Dependency** | ⚠️ **`resolveEntry` is ruled and unbuilt** — `TASK-1400` carries it, and two workflows now correctly exit nowhere until it lands |
| **Customer Value** | ✅ ⚡ **An expired invitation says so** |
| **Process** | ⚡ **The notice channel's first delivery worked, and the receiving lane still verified the claim against `integration` before acting on it.** **Both halves are the model working** |

---

## 1e · Release summary — 2026-08-08, cycle 130

**Derived from the promoted commit `089a119`.** **Eighty-five promotions.** ⚡ **The largest slice of the session — 41 files, a new module aggregate, migration `0043` — and the lane named what it had *not* run and handed it to QE.**

### ✅ What a customer gets

> **A new customer is walked through setting up Signora in about ninety seconds, and can walk away in the middle without losing a thing.**

**Screens 01/02 Welcome, 04 Company, 05 You, 06 Goals**, the onboarding container, and three new `components/ui` primitives — `StepRail`, `ChoiceCards`, `Inferred`.

### ✅ The design's own sentence set the aggregate's shape

> *"Confirm, don't collect. Eleven of the fifteen values are inferred."*

⚡ **So a value is never a bare value — it is a value *and where it came from*, and `Answer` has no default provenance**, because *"a caller that could omit it could store a guess that renders without the `Inferred` badge."*

| Decision | Why |
|---|---|
| **Every answer column nullable** | *"An abandoned onboarding still produces a customer."* A `NOT NULL industry` would make the person who left at step 3 unwritable |
| **No `features` column** | The goals imply them deterministically, so the aggregate **derives on read** — §2, *a stored copy of a derivable fact is a defect waiting for the two to disagree* |
| **Composite key `(workspace, person)`** | A single run per workspace *"would let the second member resume the first member's"* |

### ✅ The enforcement proof the lane handed QE — run, and it passed

**The Slice Handoff was explicit:** *"NOT RUN, AND NOT CLAIMED: the DB-backed security-invariant suites, including the RLS enforcement tests for `onboarding_run`… the enforcement proof is QE's to run."*

⚠️ **`security-invariants` reported 398, unchanged — and QE checked that rather than accepting the flat number.** ✅ **The suite *iterates* `TENANT_OWNED_TABLES` inside each test rather than parametrising**, so a new table changes what the existing assertions cover without changing the count. **Verified: `onboarding_run` is in the set (53 tables), and three loops walked it** — non-null `workspace_id`, `relrowsecurity`/`relforcerowsecurity`, and policy coverage. **Migration `0043` reversed to base and re-applied.**

### ✅ The platform touch is the permitted one

**`Resource.ONBOARDING` in `signora_platform/authorization/enforcer.py` is 🔴 territory**, and it is exactly the case [§20a](CLAUDE.md) and [C-224](docs/LANE_COORDINATION.md) carve out: ***a `Resource` member declares that a resource exists; who may act on it is granted only in `policy.csv`.*** **The comment says so itself**, and explains why it is not a `WORKSPACE` reuse: *"a workspace grant would have made every owner able to read a colleague's run."* **Four `policy.csv` rows in the append-only registry.**

### ⚡ Three guards refused this slice, and every refusal was right

| Guard | What it caught |
|---|---|
| `no-mock-data.test.tsx` | An array named for a business noun → renamed `SIZE_BANDS`. ⚠️ **Third instance of the check reading *comment text*** — written down at last |
| `vocabulary.test.tsx` | *"Workspace"* on the rail → **translated to Organization** ([ADR-0034](docs/architecture/adr/0034-ubiquitous-language.md)), and **[C-246](docs/LANE_COORDINATION.md) raised** rather than fixed silently, because `TASK-468` carries the same word |
| `reachability.py` | **All four routes had no entrance.** ⚡ **The resume banner *is* the entrance**, so it shipped a milestone early — and only for an unfinished run, because *"an entrance that was always visible would be a permanent offer to continue something that does not exist"* |

### ✅ And the headed run caught what no suite would

**Two scenarios failed with `409` — because the product was right.** *"A finished run refuses every later change, because onboarding answers become settings the moment the run ends."* ⛔ **Fixed by ordering, not by a reset endpoint** — *"which would exist only for tests and would be a way to edit a settled record that no customer has."*

> ⚡ **The lane also reported a flake as a flake**: the sign-out scenario failed on two of four full anonymous runs. **Reported rather than called green.**

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4251 backend** *(+50)* · **1768 frontend** *(+38)* · **95.18%** *(floor 95)* · **398 invariants** · **847 files typed** · **37 contracts** · ⛔ **`ruff` red, ungated — [B-211](docs/BUGS.md)** |
| **Release** | **135 runs recorded, 127 certified** · `promoted == certified` ✓ · `--audit-main` clean · **first attempt** |
| **Architecture** | ⚡ **Migration `0043`, reversed to base and re-applied** · **53 tenant-owned tables** · **DR nothing lost** · smoke 207s |
| **Dependency** | ⚠️ **[C-246](docs/LANE_COORDINATION.md) opened** — one label, two rows, and the lane refused to translate it twice |
| **Customer Value** | ✅ ⚡ **Workflow 8 — a guided, resumable arrival** |
| **Process** | ⚡ **The handoff named what it had not run and gave it to QE by name.** **That is the Slice Handoff's `Limitations` field doing exactly what it exists for**, and it is the difference between a limitation and a defect found three slices later |

---

## 1e · Release summary — 2026-08-08, cycle 129

**Derived from the promoted commit `f5d9be5`.** **Eighty-four promotions.** ⚡ **The expiry Workflow 4 refused to misstate two cycles ago is now true, and the fix moved the product rather than the copy.**

### ✅ The loop closes: disclose, rule, implement

| Cycle | What happened |
|---|---|
| **121** | **Workflow 4 printed the *true* 60 minutes instead of the design's 30**, because `resetPasswordTokenExpiresIn` defaults to `3600` and nothing set it |
| **—** | **[C-243](docs/LANE_COORDINATION.md) raised.** [D-185](docs/DECISION_REGISTER.md) §1, product owner: **thirty minutes** |
| **129** | **`resetPasswordTokenExpiresIn: 1800`** — ✅ **the configuration moved and the design did not** |

> ⚡ **The ruling carries a sentence well beyond this row:** ***"the framework should implement the product, not define it."*** ⛔ **A vendor default had been silently setting a security parameter, and the screen was honest about it rather than complicit.**

### ⚡ Why config and copy had to move in one change

**The row states the pairing and it is load-bearing:**

| Alone | What it would produce |
|---|---|
| **Config only** | ⛔ **A screen understating a credential's life** |
| **Copy only** | ⛔ ***"Exactly the lie this lane refused to print for four workflows"*** |

✅ **Three screens state the expiry, not one** — the confirmation the row named, plus the page description and the expired-link screen.

### ✅ Also promoted — Lane C

| | |
|---|---|
| **[D-191](docs/DECISION_REGISTER.md)** | ⚡ ***"The premise does not hold, and I recommend against both options."*** **An evaluation that rejected the question it was asked**, recorded with its falsifiers |
| **[D-192](docs/DECISION_REGISTER.md)** | 🔴 ***"Three shipped journeys end nowhere, and the design said so all along"*** |
| **Routine cycle** | **[C-244](docs/LANE_COORDINATION.md) queued, the floor restored**, and ⚡ ***"one row I refused to write"*** |

> ⚠️ **[D-192](docs/DECISION_REGISTER.md) is the finding to read.** **Three journeys QE has certified and promoted end nowhere** — and the office's own note is that **the design said so all along**, so this was discoverable before any of them shipped.

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4201 backend** · **1730 frontend** · **95.38%** · **398 invariants** · **843 files typed** · **37 contracts** · `tsc` and `eslint` clean · ⛔ **`ruff` red, ungated — [B-211](docs/BUGS.md)** |
| **Release** | **134 runs recorded, 126 certified** · `promoted == certified` ✓ · `--audit-main` clean · **first attempt** |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · smoke 216s |
| **Dependency** | ⚠️ **[C-245](docs/LANE_COORDINATION.md) 🔴 open** · ⚠️ **[D-192](docs/DECISION_REGISTER.md) names three journeys that end nowhere** |
| **Customer Value** | ✅ ⚡ **A stated credential lifetime that is true** |
| **Process** | ⚡ **A disclosure became a ruling became an implementation, across eight cycles, without anyone building the wrong thing in between** — **and the screen was never wrong at any point in that span** |

---

## 1e · Release summary — 2026-08-08, cycle 128

**Derived from the promoted commit `b082413`.** **Eighty-three promotions.** ⚡ **Two defects named by the lane that found them and left for the lane that owns them — and an office that built a channel after its own answer was stranded.**

### ✅ Two findings raised, neither fixed by its finder

| | |
|---|---|
| 🔴 **[C-245](docs/LANE_COORDINATION.md)** *(Lane A)* | ***"Screen 13 shows a reader six facts they are not permitted to see."*** A permissions leak found while building, **raised rather than patched** |
| **[B-214](docs/BUGS.md)** *(Lane A)* | ***"The domain knows an invitation expired and the API cannot say so."*** The knowledge exists one layer below the boundary that would report it |

> ⚡ **Both were found by a lane building an adjacent screen, and neither is in that lane's Change Budget to repair.** ✅ **[§20e](CLAUDE.md): *"finding a defect outside your assignment is not permission to fix it — it is an obligation to report it."***

### ⚡ Lane C declined to open a row, and that is the register working

> *"[B-214](docs/BUGS.md) needs no row — it is already Lane A's to fix, measured."*

⛔ **The office checked ownership before adding a second record of one defect** (§2, *truth has exactly one authoritative representation*). **A duplicate row would have split the fix across two ids.**

### ⚡ The notice channel, and the irony is in its own commit message

**Lane C built [`docs/coordination/notices.toml`](docs/coordination/notices.toml) after discovering the problem by living it:**

> *"The notice channel — **my B-214 answer was stuck behind the ref it was about.**"*

**And then, one commit later:** *"The notice channel, re-applied — **the rebase dropped it and kept its data**."*

> ⚡ **A lane's answer to a defect could not reach the lane that needed it, because the answer travelled by the same ref the defect was blocking.** ✅ **The mechanism it built is the one thing that would have carried it.**

### ✅ Also promoted

**[D-187](docs/DECISION_REGISTER.md) · [D-188](docs/DECISION_REGISTER.md) · [D-189](docs/DECISION_REGISTER.md)** *(Lane C)* — the queue arithmetic corrected, **the dashboard made generated rather than written** ([`infra/pipeline-dashboard.py`](infra/pipeline-dashboard.py)), and the floor met at 20.

> ⚡ **[D-188](docs/DECISION_REGISTER.md) is the same lesson [B-151](docs/BUGS.md) cost QE two cycles ago, reached independently: a dashboard that is typed will eventually be wrong, so generate it.**

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4201 backend** · **1729 frontend** · **95.38%** · **398 invariants** · **843 files typed** · **37 contracts** · `tsc` and `eslint` clean · ⛔ **`ruff` red, ungated — [B-211](docs/BUGS.md)** |
| **Release** | **133 runs recorded, 125 certified** · `promoted == certified` ✓ · `--audit-main` clean · **first attempt** |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · smoke 149s |
| **Dependency** | ⚠️ **[C-245](docs/LANE_COORDINATION.md) is 🔴 and open** — a permissions leak with a named owner |
| **Customer Value** | ⛔ **None directly** — **two defects named before a customer could meet them** |
| **Process** | ⚡ **Both lanes reported into another lane's territory and neither touched it.** **That is the register's whole purpose, exercised twice in one cycle** |

---

## 1e · Release summary — 2026-08-08, cycle 127

**Derived from the promoted commit `9b43575`.** **Eighty-two promotions.** ⚡ **Workflow 5 ships, and the most valuable thing in it is a sentence the screen refuses to print.**

### 🔴 The sentence Workflow 5 will not print, and why refusing was the security decision

**The design says:** *"This signs you out of 4 other devices, including the iPad last used 3 days ago."*

⛔ **It is not printed, and the first half is *false* rather than merely unsupported.** **`revokeSessionsOnPasswordReset` is a Better Auth option and `lib/auth/server.ts` does not set it** — **other sessions survive a reset.**

> ⚡ **Printing it would tell somebody who has just been compromised that they are safe** — *"the most expensive place in the product to be wrong."* ⛔ **And the count has no source either: nothing lists sessions and nothing records a device.**
>
> ✅ **This is the fourth consecutive workflow where Lane A refused a false affordance rather than drawing it** — `/join`'s *Request access*, `/sso`'s domain field, screen 07's six OTP boxes, and now this. **Every one was found by opening the dependency rather than reasoning about it.**

### ✅ What a customer gets

| | |
|---|---|
| ⚡ **Workflow 5 · Password Reset** *(Lane A)* | **Screens `09` and `10`.** A person sets a new password and is told it worked |
| ⚡ **`TASK-474`** *(Lane A)* | **The mailbox is an experience now** — a developer can see, open and resend every email |

### ✅ §20c paid off exactly one workflow later

**Screens 09 and 10 compose `PasswordField` and `PasswordStrength` from `components/ui`** — **the library components Workflow 2 added because screen 06 needed them.** ⚡ **Added *to* the library rather than beside the page, and the next workflow simply used them.**

**And `10` is its own route rather than a state of `09`:** *"the reset token is spent once the password changes, so re-rendering 09 with a success flag would leave a form on screen whose submit could never work again."*

### ✅ Lane C's audit batch

**Eight commits** — [D-186](docs/DECISION_REGISTER.md), [D-187](docs/DECISION_REGISTER.md), [B-411](docs/BUGS.md)'s rebase, a project audit, and two routine checks. ⚡ **[D-187](docs/DECISION_REGISTER.md) is the office correcting its own arithmetic**: *"one claimable, twenty prepared behind it. The correction is mine."*

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4201 backend** · **1729 frontend** *(+12)* · **95.38%** · **398 invariants** · **843 files typed** · **37 contracts** · `tsc` and `eslint` clean · ⛔ **`ruff` red, ungated — [B-211](docs/BUGS.md)** |
| **Release** | **132 runs recorded, 124 certified** · `promoted == certified` ✓ · `--audit-main` clean · **first attempt** |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · smoke 201s |
| **Dependency** | ✅ Nothing held |
| **Customer Value** | ✅ ⚡ **Workflows 1–5 are all on `main`** — sign in, register, verify, forgot, reset |
| **Process** | ⚡ **A security ruling made by a lane refusing to render, and recorded where the next reader will find it** — the opposite of the three QE defects this session, which were all beliefs acted on without measurement |

---

## 1e · Release summary — 2026-08-08, cycle 126

**Derived from the promoted commit `2a35ac1`.** **Eighty-one promotions.** ⛔ **The dashboard's single most consequential line was false for eleven cycles, and no gate could have told anybody.**

### 🔴 [B-151](docs/BUGS.md) — "Blocking Quality Defects: None" was typed, not derived

| Where | What it said |
|---|---|
| `PROJECT_STATUS.md` | ✅ **None** |
| [`BUGS.md`](docs/BUGS.md) | 🔴 **[B-209](docs/BUGS.md)** eleven Playwright journeys failing, since **2026-08-06** · 🟠 **[B-211](docs/BUGS.md)** `ruff` red tree-wide with no gate invoking it, since **2026-08-07** |

⛔ **Both are marked Blocking Quality Defects. QE wrote `None` in every Closeout across that span.**

### ⛔ The mechanism is [B-150](docs/BUGS.md)'s, one file over

**QE re-measures the certification figures every cycle and transcribed everything around them.** ⚡ **Cycle 118 caught four stale figures exactly this way and fixed them** — **and did not ask what else on the page was typed rather than read.**

**Second instance, same period:** QE's poll report closed with a fixed six-row findings list carried from the prompt. ⚡ **The register holds 41 rows not closed, 21 of them QE's.**

> ⛔ **§20d states the rule and QE quotes it in its own Closeouts** — *"repository metrics are measured, never transcribed"*. **QE applied it to the numbers and not to the sentences.**

### ⚠️ Why eleven cycles of gates never caught it

**`state-check` does read the register's blocking rule**, and reported *"No unresolved 🔴 across 122 bug row(s) — promotion is not blocked"* on every run. ⚡ **That is a different question.**

| Instrument | Question it answers |
|---|---|
| `state-check` | **Is a 🔴 unresolved by my own parse?** |
| The dashboard line | **What does the register currently hold?** |

⛔ **Nothing was lying and nothing was broken. Two true instruments answered two questions, and the sentence between them was written by hand.**

> ⚡ **It was found by being asked a direct question and measuring instead of reciting.** **That is not a gate, and QE is not proposing one** — the fix is that the line is derived from the register at Closeout, which is what §20d already required.

### ✅ The correction, measured

**B-211 re-measured before the row was written: `232 errors, exit 1`.** The row said 238 on 2026-08-07 — **smaller, still red.**

⛔ **B-209 is not re-measured and QE does not claim it.** **`make e2e` has no launchable environment for QE** ([B-149](docs/BUGS.md)), so **Lane A's measurement is carried as Lane A's.**

### ✅ Also promoted

| | |
|---|---|
| ⚡ **`TASK-474` milestone 1** *(Lane A)* | **The developer mailbox — its store, its transport and its refusal.** `lib/auth/mailbox.ts`, +8 tests |
| ✅ **[B-213](docs/BUGS.md) answered** *(QE)* | **`VERIFIED — NOT A DEFECT`.** The `BUGS.md` marker is a fenced quotation inside [B-102](docs/BUGS.md)'s own row, and `state-check` already reads that file **and is fence-aware** |

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4201 backend** · **1717 frontend** *(+8)* · **95.38%** · **398 invariants** · **843 files typed** · **37 contracts** · `tsc` and `eslint` clean · ⛔ **`ruff` red, ungated — [B-211](docs/BUGS.md)** |
| **Release** | **131 runs recorded, 123 certified** · `promoted == certified` ✓ · `--audit-main` clean · **first attempt** |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · smoke 303s |
| **Dependency** | ✅ Nothing held |
| **Customer Value** | ⚡ **A developer can be shown the emails the product sends** — the store half |
| **Process** | 🔴 **Three QE self-defects in four cycles** — [B-411](docs/BUGS.md)'s inference, [B-150](docs/BUGS.md)'s staging, [B-151](docs/BUGS.md)'s transcription. ⚡ **All three are the same root: acting on a belief where a measurement was one command away** |

---

## 1e · Release summary — 2026-08-08, cycle 125

**Derived from the promoted commit `c6e9278`.** **Eighty promotions.** ⚡ **Three controls that four workflows each shipped without, landing in the one file every one of those rows correctly forbade.**

### ✅ [`TASK-498`](docs/BACKLOG.md) — the row that may touch `lib/auth/server.ts`, and decides nothing

> *"[C-434](docs/LANE_COORDINATION.md) was Workflow 1's, [C-240](docs/LANE_COORDINATION.md) Workflow 2's, [C-241](docs/LANE_COORDINATION.md) Workflow 3's. Every authentication workflow needed one line in `lib/auth/server.ts`, every row correctly forbade it, and every screen shipped without its control and said so. This is the row that may touch it, and it decides nothing."*

| Control | What it restores |
|---|---|
| **`haveIBeenPwned()`** | ⚡ **The design's fourth password rule on screen `06`** — *"k-anonymity, so the password never leaves the process"*. ⛔ **The cost is accepted with the ruling**: an unreachable range API becomes an inability to register, and *"softening that here would be this file deciding a semantic the ruling did not"* |
| **`rateLimit: { enabled: true }`** | **Better Auth defaults it to production only**, so the throttled screen Workflow 1 built **against the real `429` and the real `X-Retry-After` could not be reached at any review** |
| **`emailOTP({ otpLength: 6 })`** | ⚡ **The control screen `07` was built without.** *"`otpLength` is a READ, not a choice: the design says 'Enter the 6-digit code' and [D-138](docs/DECISION_REGISTER.md) makes the snapshot the authority"* |

> ⚡ **This is the discipline paying out.** **Four screens each refused to draw a control they could not honour, each raised an item, each said so in a test** — and **one row, holding the ruling, turned all of them on at once.** ⛔ **No screen was built twice and no false affordance ever shipped.**

### ✅ Also promoted

**[`TASK-483`](docs/BACKLOG.md)** — *"the shell was already correct, so the deliverable is the guard"*. ⚡ **A slice whose product is a test**, plus `auth-shell.test.tsx`.

### ⚡ The first non-`platform` profile of the session

```
profile: documentation+frontend        Gates (8)
```

**Every prior candidate this session touched `docs/coordination/**` and classified as `platform` — 16 or 17 gates.** ⚡ **This one did not, and the planner narrowed to eight.** ⛔ **Recorded, never applied** — all six required gates still ran ([427](docs/architecture/427-impact-based-validation.md) step 2). **It is the first evidence in the impact-based-validation record that the classifier discriminates rather than always widening.**

### ✅ QE's own two practices held

**[B-150](docs/BUGS.md) produced two rules yesterday and both were exercised today.** ⚡ **The `TASK-483` row conflicted `CLAIMED` against `IN VALIDATION`** — a state advance, the lane's to set — **and the resolution ran as a *gated* sequence rather than a chained one:**

```
resolve → GATE: refuse to stage if any marker remains → git add → continue
```

✅ **`state-check` ran before this Closeout commit, not after.**

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4201 backend** · **1709 frontend** *(+15)* · **95.38%** · **398 invariants** · **843 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **130 runs recorded, 122 certified** · `promoted == certified` ✓ · `--audit-main` clean · **first attempt** |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · smoke 193s |
| **Dependency** | ✅ **Three coordination items discharged at once** — C-434, C-240, C-241 |
| **Customer Value** | ✅ ⚡ **Breach checking, reachable rate limiting, and a 6-digit code** |
| **Process** | ⚡ **The best argument yet for refusing to build what you cannot honour**: four screens deferred one line each, said so, and got all three back in a single reviewed row |

---

## 1e · Release summary — 2026-08-08, cycle 124

**Derived from the promoted commit `82084ed`.** **Seventy-nine promotions.** 🔴 **QE promoted an unresolved conflict marker to `main` in cycle 123 and repaired it here — and the check that names it was skipped, not missing.**

### 🔴 [B-150](docs/BUGS.md) — the register was corrupt on `main`

```
docs/ACTIVE_ASSIGNMENTS.md carries an unresolved merge-conflict marker at
line(s) 80, 83, 85. The register is corrupt, and every reader of it is
reading a merge that never finished.
```

**`6f41816a` carried `<<<<<<< HEAD` / `=======` / `>>>>>>> 774b380c` inside the Lane A block**, and it was certified and promoted.

### ⛔ The mechanism is two lines of shell

```
git add docs/ACTIVE_ASSIGNMENTS.md && git cherry-pick --continue
```

**The line before it was a Python resolver whose assertion *failed*.** ⚡ **`&&` chains on the exit status of `git add`, not on the resolver's.** **The resolver aborted without writing, `git add` staged the conflicted file, and `--continue` committed it.** **The next commit then conflicted, printed its own `U` list, and QE read that as *"the continue refused"*.**

> ⛔ **QE made this exact mistake earlier in the same session and caught it** — *"my assertion failed but `git add` still staged the conflicted file"* — **and did not carry the lesson into the next resolution.**

### 🔴 The check was not missing. It was skipped.

**`conflict_markers()` already covers `ACTIVE_ASSIGNMENTS.md` and names the three exact lines.** ✅ **Verified both ways: run against the corrupted tree it fires; against the repaired tree it is clean.**

**QE ran `state-check` in cycles 113 through 122 and did not run it in 123.** ⚡ **The gate did its job in every cycle it was given.**

> ⛔ **Adding a check here would be building a second instrument because the first was not consulted** — the Decorative Logic class in its purest form. ✅ **`state-check` is advisory by design, and QE treated advisory as optional. It is not: it is the last read before Repository Ready, and the checklist places it there for exactly this.**

### ✅ Two practices, both mechanical

| | |
|---|---|
| **Never chain `git add` after a resolver with `&&`** | ⛔ **Assert the file is marker-free as a separate, gating step**, then stage |
| **`state-check` runs before every Closeout commit** | ⚡ **Not before *most*.** It caught this on its first run against the bad tree |

### ⚠️ What the gates could and could not see

**Certification passed on the corrupt tree, correctly.** ⛔ **No certification gate reads a coordination register for markers** — `pytest`, coverage, invariants, `mypy`, `import-linter`, `tsc` and smoke all describe code. ⚡ **`--audit-main` passed too: the commit *was* inside a certified snapshot. It was certified and wrong.**

> ⚠️ **This is [B-102](docs/BUGS.md)'s class returning** — *"a conflict marker, committed, promoted, and carried through several certification cycles"*. **The instrument built after that one worked. The step that runs it was omitted.**

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4201 backend** · **1694 frontend** · **95.38%** · **398 invariants** · **843 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **129 runs recorded, 121 certified** · `promoted == certified` ✓ · `--audit-main` clean · **first attempt** |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · smoke 141s |
| **Dependency** | ✅ Nothing held |
| **Customer Value** | ⛔ **None.** **A repository repair** |
| **Process** | 🔴 **Two QE defects in two cycles, both from resolving register conflicts by hand** — [B-411](docs/BUGS.md)'s inference and [B-150](docs/BUGS.md)'s staging. ⚡ **Both were caught within one cycle and both are recorded against QE** |

---

## 1e · Release summary — 2026-08-08, cycle 123

**Derived from the promoted commit `adce341`.** **Seventy-eight promotions.** ⛔ **QE deleted a line from the backlog in cycle 122 and restored it here — and a lane caught it, not a gate.**

### ⛔ [B-411](docs/BUGS.md) — Lane C filed it against QE, and it is correct

**Cycle 121 excluded `D-183`/`D-184` on `TASK-486`'s `Features` line, checked three things, and concluded *"Lane C's tip genuinely carries no such line — so the deletion is deliberate."***

⚡ **The observation was exact. The inference was wrong.** **Lane C deleted it by accident**, and the mechanism is worth carrying:

> **`re.S` makes `.` match newlines, so a non-greedy `.*?` in a `Status`-cell pattern stops at the *next row's* terminator whenever the target cell has none.** ⛔ **The match succeeds, the regex looks correct, nothing errors, and the row below is silently replaced.**

**And the commit that did it was the one *restoring* a lane-owned state Lane C had overwritten** — *"fixing one violation while committing a silent deletion, because a correction is written quickly and reviewed as 'just putting it back.'"*

### ⛔ Where QE went wrong, stated exactly

**Cycle 121's caution was right. Cycle 122's resolution was the error.**

⚡ **QE proved *authorship*** — `git log -L` named `6e7fc924`, a Lane C package — **and then answered a different question with it.**

| | |
|---|---|
| **What authorship establishes** | ✅ **That a conflict is not cross-lane.** QE was entitled to act |
| **What it says about intent** | ⛔ **Nothing at all** |

**QE inferred intent from absence, which is precisely what B-411 says cannot be done.** ⚠️ **Cycle 122's summary calls that resolution correct; it is left standing as the dated record it is** (§2 — *falsifying history to make the repository look consistent is the same failure wearing the opposite coat*).

### ✅ The repair, and why it had to be QE's

⛔ **No commit on `lane-c-sync` restores the line.** **Its tip carries it from its *base* at `3f22184b`, which predates the removal** — so cherry-picking could never bring it back. ⚡ **A deletion that exists only as a difference between two bases is not an edit anybody made.**

**QE restored it from the pre-removal blob**, and verified rather than asserted: **byte-identical to Lane C's repaired tip, and at the same offset (9 lines) within `TASK-486`.**

> ✅ **The check QE adds, and it is one line: when a conflict is a pure deletion, ask whether any commit on the branch performs it.**

### ✅ What else was promoted

| | |
|---|---|
| ⚡ **`TASK-484`** *(Lane A)* | **The two journeys that work and nobody verifies** — *"one journey delivered, one honestly bounded"*. A new `search-journey.spec.ts` |
| **[D-185](docs/DECISION_REGISTER.md)** *(Lane C)* | Both decisions applied — *"and §5 caught me inside its own commit"* |
| **[C-242](docs/LANE_COORDINATION.md) · [C-243](docs/LANE_COORDINATION.md)** *(Lane C)* | Indexed, **and one of them is a real decision** |

⛔ **Lane C's rebased `D-183` was skipped** — `main` already carries it, and the incoming version conflicted across **two generated files** (`coordination.toml`, `queues/lane-a.toml`) plus `state-check.py`. **The repair for a generated file is the generator** (§20e).

### ⚠️ Smoke named `Researched account` on a *fast* run

**172s, and the slowest stage is `Researched account 22s`** — the stage that named itself on both 2652s outliers and on the 621s run. ⛔ **The three-population reading QE has repeated ten times does not explain this one**, and it is recorded as the first observation that complicates it rather than confirms it.

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4201 backend** · **1694 frontend** · **95.38%** · **398 invariants** · **843 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **128 runs recorded, 120 certified** · `promoted == certified` ✓ · `--audit-main` clean · **first attempt** |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · smoke 172s |
| **Dependency** | ✅ Nothing held |
| **Customer Value** | ⚡ **One journey delivered, one bounded and said so** |
| **Process** | 🔴 **A gate did not catch this and could not have** — the loss was one line of markdown inside a register. ⚡ **A lane re-measured its own file against `integration` and found it**, which is §20e's claim about this repository restated from the other side |

---

## 1e · Release summary — 2026-08-08, cycle 122

**Derived from the promoted commit `3ed76cf`.** **Seventy-seven promotions.** ⛔ **QE released a hold it had placed itself — and the evidence that resolved it was one `git log -L` away the whole time.**

### ⛔ What QE was holding, and what it cost

**Cycle 121 excluded [D-183](docs/DECISION_REGISTER.md) and [D-184](docs/DECISION_REGISTER.md) on a `BACKLOG.md` conflict QE judged unadjudicable.** ⚡ **Lane A measured the consequence and reported it before QE noticed:**

> *"TASK-483, 484, 474, 498, 488 and 489 are all `READY` on `lane-c-sync` and `SEQUENCED` on `origin/integration`, so all six are invisible to the Task Claim Protocol, which claims from `integration` and nowhere else."*

⛔ **Six rows, and the proximate cause was QE's exclusion.**

### ✅ The check that resolved it, and why it should have been the first one

**The contested line was `TASK-486`'s `Features` cell. QE's cycle-121 reasoning was: Lane C deletes it, `integration` holds a longer version, neither contains the other, therefore not QE's to judge.** ⚡ **What that reasoning never asked was *who wrote the longer version*.**

```
git log -L 1053,1053:docs/BACKLOG.md origin/integration
  → 6e7fc924  D-160 — the pipeline is 27 workflows deep …
```

✅ **A Lane C decision package.** ⛔ **Both versions are Lane C's own text, and Lane C's tip says delete** — **so there was never a cross-lane judgement to make.**

> ⚡ **The caution was not wrong; it was under-investigated.** **"Neither side contains the other" is a fact about two blobs. "Whose text is this?" is a fact about authorship, and it is the one that decides whether a conflict is QE's at all.** ✅ **That question is now part of the resolution: before excluding a register conflict, blame the contested line.**

### ✅ What that released, measured on `main`

```
eligible_count = 1     →     eligible_count = 10
```

| Row | State on `main` |
|---|---|
| **`TASK-483` · `474` · `498` · `488` · `489`** | ✅ **`READY`** |
| **`TASK-484`** | 🔵 **`CLAIMED`** — Lane A took it mid-cycle |

⚡ **[D-184](docs/DECISION_REGISTER.md)'s floor is ten, and ten is what `main` now offers** — *"every one decomposed."*

### ✅ Also promoted

| | |
|---|---|
| **[D-183](docs/DECISION_REGISTER.md)** *(Lane C)* | Five claimable rows, in an order, **and [D-163](docs/DECISION_REGISTER.md) amended rather than reinterpreted** |
| **[D-184](docs/DECISION_REGISTER.md)** *(Lane C)* | The floor is ten, **and two of them cost real decomposition** |
| **[C-242](docs/LANE_COORDINATION.md) update** *(Lane A)* | The measurement above, taken on both refs |

### ⚡ Lane A's report is the model for this class of finding

**It named the count, named the mechanism, and named the counter-evidence against its own alarm:**

> *"`TASK-487` is not in the table because it reached `integration`: this lane claimed it, built it and it is `IN VALIDATION`. That is the proof the mechanism works the moment the ref moves — one fast-forward took the lane from idle to a delivered workflow inside one poll."*

⛔ **And it declined to re-argue the part that was already owned:** *"Two of the six are rows Lane C says it should have released yesterday… Recorded rather than re-argued; Lane C found it and owns it."*

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4201 backend** · **1694 frontend** · **95.38%** · **398 invariants** · **843 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **127 runs recorded, 119 certified** · `promoted == certified` ✓ · `--audit-main` clean · **first attempt** |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · smoke 154s |
| **Dependency** | ✅ **Cleared.** ⛔ **The dependency was QE's own hold, and it lasted one cycle** |
| **Customer Value** | ⛔ **None directly** — **ten claimable rows where there was one** |
| **Process** | ⚠️ **A lane measured a constraint QE had created and reported it without accusation.** ⚡ **That is the register working, and the correction cost one cycle rather than a governance change** |

---

## 1e · Release summary — 2026-08-08, cycle 121

**Derived from the promoted commit `5e06adc`.** **Seventy-six promotions.** ⚡ **Workflow 4 shipped one cycle after the unblock that made it claimable — and the screen tells the truth about a credential's lifetime rather than repeating the design.**

### ✅ What a customer gets

| | |
|---|---|
| ⚡ **Workflow 4 · Forgot Password** *(Lane A)* | **A person who has forgotten their password can reset it.** Screen `08 Reset your password`, to the approved design |

### ⚡ The expiry it prints is true, and that is the slice's best decision

**The design says the link expires in 30 minutes. It expires in an hour.** ⛔ **`better-auth`'s `resetPasswordTokenExpiresIn` defaults to `3600`** — *"`dist/api/routes/password.mjs`, read rather than assumed"* — **and `lib/auth/server.ts` does not configure it.**

> ⚡ **Printing the design's number would state a false thing about a credential's lifetime**: *"a customer returning at forty minutes would believe a working link was dead."* ✅ **So the screen prints the true number inside the design's own sentence.**
>
> **This is the third consecutive slice where Lane A opened the dependency rather than reasoning about it** — the OTP port in cycle 119, `emailOTP`'s registration state, and now a token TTL in a vendor's compiled output. **Each time the finding changed what shipped.**

### ✅ The security property is one sentence, and it is mutation-tested

> *"The response must be identical for a known and an unknown address."*

**It is the one page nobody has to authenticate to reach, so a form that distinguished them would be an enumeration oracle open to the internet.** ✅ **The confirmation renders on success *and* on a refusal this screen cannot distinguish from success, and the server's words about the address are withheld deliberately.** ⚡ **Mutation-tested: surfacing the refusal fails the test that exists for it** — which is §2's own standard, *a guard that cannot fail is documentation pretending to be code*.

### ⛔ Two Lane C commits excluded, and QE did not adjudicate

**`docs/BACKLOG.md` collided on `TASK-486`'s `Features` line.** ⚡ **QE checked three things before deciding rather than picking a side:**

| Check | Result |
|---|---|
| Did any Lane A commit touch it? | ⛔ **No — 0 hunks across all three** |
| Did Lane C's two earlier commits touch it? | ⛔ **No** |
| Does Lane C's tip still carry the line? | ⛔ **No — the deletion is deliberate** |

**So neither side contains the other**: Lane C means to delete it, and `integration` holds a longer version Lane C's base never had. ⛔ **That is a content judgement between two lanes and it is not QE's.**

> ✅ **[D-183](docs/DECISION_REGISTER.md) and [D-184](docs/DECISION_REGISTER.md) are excluded and Lane C rebases.** ⚡ **It cost one rebase and held nothing of Lane A's** — the executable slice and Lane C's two earlier commits all promoted in the same cycle.

### ✅ The unblock loop, measured end to end

**Cycle 120 promoted the queue repair. Lane A claimed `TASK-487` within a minute. Cycle 121 promoted the delivered screen.** ⚡ **Two cycles from *"the queue advertises finished work"* to *"a customer can reset their password"*.**

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4201 backend** · **1694 frontend** *(+8)* · **95.38%** · **398 invariants** · **843 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **126 runs recorded, 118 certified** · `promoted == certified` ✓ · `--audit-main` clean · **first attempt** |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · smoke 195s |
| **Dependency** | ⚠️ **Two Lane C commits excluded** on an unadjudicable register conflict — **rebase, not a defect** |
| **Customer Value** | ✅ ⚡ **Workflows 1–4 are all on `main`** — sign in, register, verify, reset |
| **Process** | ⚡ **QE excluded rather than resolved, and said which three checks made that the answer** — the alternative was QE silently choosing one lane's text over another's |

---

## 1e · Release summary — 2026-08-08, cycle 120

**Derived from the promoted commit `2f858a3`.** **Seventy-five promotions.** ⛔ **The first cycle QE has run on a candidate with no executable change — and the reason is a rule, not a judgement.**

### ⛔ Why a planning-only candidate was certified

**QE declined to certify planning alone on the previous three polls.** ⚡ **This time `origin/integration` contained a measurable defect:**

```
queues/lane-a.toml   current = "TASK-494"   eligible_count = 1
```

⛔ **`TASK-494` was promoted in cycle 118 and QE advanced its row to `PROMOTED` itself.** **Lane A's queue was advertising finished work as its only claimable item**, its branch was level with `main` with nothing in flight, and **the release that would unblock it existed only on `lane-c-sync`.**

> ✅ **[§20e](CLAUDE.md) covers this case in a ruled sentence, and it is not [C-435](docs/LANE_COORDINATION.md):**
>
> *"Whenever an implementation lane has been idle for more than one reporting cycle because `READY` work exists only outside `integration`, **synchronizing that work becomes the highest repository priority** — above further preparation, above new initiatives, above every planning activity."*
>
> ⛔ **QE did not decide the C-435 deadlock and still has not.** **That item asks whether a planning correction may be integrated *without* certification. QE ran the ordinary cycle instead** — certify, then promote — **which needs no new rule and leaves `promoted == certified` untouched.**

**Result, measured on `main`:**

```
queues/lane-a.toml   current = "TASK-487"   eligible_count = 1
```

⚡ **Workflow 4 · Forgot Password, 22/22 prepared, claimable where finished work stood.**

### ✅ What was promoted

| | |
|---|---|
| ⚡ **Workflow 4 released** *(Lane C)* | And **[C-241](docs/LANE_COORDINATION.md) answered** — *"two screens above where I looked"* |
| **The release-trigger routine check** *(Lane C)* | *"fired for ten rows and nothing re-asked"* |

### ⚠️ The defect QE promoted was QE's own to see

**`state-check` reported it last cycle, in QE's own Closeout run:**

> *"lane-a: queues `TASK-494` as executable and its row says `PROMOTED` — finished work advertised as available"*

⛔ **QE read that line, declared Repository Ready, and did not connect it to the planning commit it was declining to integrate.** ⚡ **The two findings were one finding**, and the second poll is where they joined up.

> **What changed between the polls was not the repository — it was QE actually checking whether a lane could claim.** ✅ **The check is cheap and it is now part of the poll**: when a planning commit is held, read the queue it repairs.

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4201 backend** · **1686 frontend** · **95.38%** · **398 invariants** · **843 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **125 runs recorded, 117 certified** · `promoted == certified` ✓ · `--audit-main` clean · **first attempt** |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · smoke 143s |
| **Dependency** | ✅ **Lane A unblocked** — `TASK-487` claimable. ⚠️ **[C-241](docs/LANE_COORDINATION.md) answered by Lane C** |
| **Customer Value** | ⛔ **None.** **The cycle's product is an unblocked lane** |
| **Process** | ⚡ **The rule that applied was already written and QE had to go looking for it** — which is the argument for §20e being long rather than short |

---

## 1e · Release summary — 2026-08-08, cycle 119

**Derived from the promoted commit `67d662e`.** **Seventy-four promotions.** ⚡ **A slice whose most valuable output is the thing it refused to build — and a test that asserts the refusal.**

### ✅ What was promoted

| | |
|---|---|
| ⚡ **`TASK-486` milestone 1 — screen `07 Verify email`** *(Lane A)* | **A person who has just registered sees where to go next.** The resend timer is the design's — *"starts at 45s and doubles; the third resend suggests checking spam and the corporate filter"* — and **the remaining time is printed rather than the control merely disabled**, which the design's own accessibility note asks for |
| **[D-182](docs/DECISION_REGISTER.md)** *(Lane C)* | Workflow 8 decomposed, *"because it was the cliff"* |

### ⛔ The six boxes are not built, and that is the finding rather than the omission

**The design draws six single-character boxes for a 6-digit code. This screen sends a *link*.** ⚡ **Lane A opened the code rather than reasoning about it**: `lib/auth/server.ts:73` sends `{ user, url }`, the port's `AuthEmail` carries `url` and nothing else, and **no endpoint would accept a typed code.**

**`better-auth/plugins/email-otp` is installed and unregistered** — and registering it means editing `lib/auth/server.ts`, **the one file `TASK-486` states in terms it does not touch**, plus choosing `otpLength`, *"a security parameter nobody has chosen."* ✅ **Raised as [C-241](docs/LANE_COORDINATION.md), from Lane A's own `200+` block.**

> ⚡ **Six boxes wired to nothing would be a false affordance, and the strongest version of one: *"it looks like it worked right up until it does not."*** **The lane has now refused that three times** — `/join` never offers *Request access* because nothing can grant it, `/sso` locks its domain field and gives the reason, and this.
>
> ✅ **A test asserts the boxes' absence rather than leaving it to be noticed.** ⛔ **That is the difference between a declared limitation and a discovered one**, and it is [P-A](docs/DOMAIN_DISCOVERY_REGISTER.md) answered before it could happen.

### ✅ Two details worth keeping

| | |
|---|---|
| **The countdown starts on a successful send, never on the click** | *"A failure that began a 45-second wait would punish somebody for the product's own error and leave them no way to retry"* |
| **`useResendTimer` goes into `components/ui`, not beside the page** | §20c — **screens `08` and `09` draw the same control.** ⚡ **Added *to* the library rather than beside it**, which is the rule most often lost under time pressure |

### ✅ Planning travelled the way §20e intends

**[D-182](docs/DECISION_REGISTER.md) sat unintegrated across three polls** because it changed nothing executable — **and rode in the moment Lane A pushed a screen.** ⛔ **QE declined to open a cycle for it on its own** and declined equally to decide [C-435](docs/LANE_COORDINATION.md), the open deadlock about whether it should have: **acting either way would have been QE ruling an unruled governance question.**

> ⚡ **What it cost, measured rather than argued: one planning commit, held 11 minutes at the first poll and integrated within the hour, with no lane starved at any point.** **That is the evidence [D-136](docs/DECISION_REGISTER.md) asks for.**

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4201 backend** · **1686 frontend** *(+14)* · **95.38%** · **398 invariants** · **843 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **124 runs recorded, 116 certified** · `promoted == certified` ✓ · `--audit-main` clean · **first attempt** |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · smoke 194s |
| **Dependency** | ⚠️ **[C-241](docs/LANE_COORDINATION.md) opened** — the OTP plugin is installed, unregistered, and its length is an unmade security decision |
| **Customer Value** | ✅ **Workflow 3 has its first screen**, and it does not pretend to do what it cannot |
| **Process** | ⚡ **The best slice of the session on one measure: it names what it did not build, says why in the product's own code, files the decision, and tests the absence** |

---

## 1e · Release summary — 2026-08-08, cycle 118

**Derived from the promoted commit `891e2c4`.** **Seventy-three promotions.** ⚡ **A ratified decision became working software for the first time under [D-179](docs/DECISION_REGISTER.md) — and QE found three of its own dashboard figures stale while measuring it.**

### ✅ What was promoted

| | |
|---|---|
| ⚡ **`TASK-494` — email leaves the process through Resend** *(Lane A)* | **Behind the port `lib/auth/email.ts` already earned**, whose own comment said *"what arrives later is a vendor."* ✅ **+8 tests, `email-transport.test.ts`.** ⛔ **It does not replace the developer mailbox** — one is the development substitution [D-167](docs/DECISION_REGISTER.md) ① permits at an infrastructure boundary, the other is the production adapter, and both sit behind one port |
| **[C-240](docs/LANE_COORDINATION.md) is `RULED`** *(Lane A)* | All three approved — **and none has a row that may execute them** |
| **[D-181](docs/DECISION_REGISTER.md)** *(Lane C)* | The coordination ref is recovered and the hand-rolled push is gone |

### ⚡ The first adoption, and it is the point of [D-179](docs/DECISION_REGISTER.md)

**Resend was ratified in [`09-build-vs-buy.md`](docs/architecture/09-build-vs-buy.md) and unbought.** [D-178](docs/DECISION_REGISTER.md) measured the cost — **eight of twelve ratified *buy* decisions unadopted**, with *"a workflow blocked or a lane building a workaround while the vendor sits ratified and unbought."* **[D-179](docs/DECISION_REGISTER.md) made adoption a tracked state, the check fired in its first minute, and this is the row it produced arriving on `main`.**

> ✅ **QE checked the dependency rather than waving it through.** **`resend@^6.18.1` in `package.json` is 🔴 under [§6](CLAUDE.md)** — *"never introduce a major dependency without explicit approval"* — **and the approval is `09-build-vs-buy.md`, cited by D-178 and D-179.** ⚡ **This is the *adoption* of an existing decision, not a new one**, which is exactly the distinction D-179 exists to make visible.

### ⚠️ A claim raced a planning correction, and the lane won correctly

**`docs/BACKLOG.md` conflicted on [`TASK-486`](docs/BACKLOG.md).**

| | |
|---|---|
| **Lane C, 06:43:30Z** | ⏸️ **`SEQUENCED`** — behind `TASK-494`, on a Product Office branch |
| **Lane A, 06:53:35Z** | 🔵 **`CLAIMED`** — **against `integration`, where the row still read `READY`** |

✅ **The claim stands.** **§20e claims from `integration` and nowhere else**, `CLAIMED` is the lane's to set, and **Lane A followed the protocol exactly.** ⚡ **The sequencing reason is discharged in the same candidate anyway** — Lane C wanted `TASK-486` behind `TASK-494`, and **Lane A delivered `TASK-494` first.**

> ⚡ **Recorded inside the row rather than resolved silently, because it is the second observed instance** — [C-422](docs/LANE_COORDINATION.md) was the first. ⛔ **[D-136](docs/DECISION_REGISTER.md) asks for evidence across cycles rather than a governance change argued from one bad day**, so this is evidence and nothing more.

### ⛔ Three dashboard figures were stale, and QE wrote them

**Found by re-measuring instead of editing the number in front of it:**

| Figure | Said | Is |
|---|---|---|
| **Frontend tests** | 1636 across 68 files | ✅ **1672 across 70** — stale since cycle 112 |
| **Module directories** | 17 | ✅ **18** |
| **ADRs** | 44 | ✅ **52** |
| **Architecture documents** | 54 | ✅ **142** |
| **Migrations** | *(not stated)* | ✅ **43**, `0000`–`0042` |

> ⛔ **§20d is explicit — *"repository metrics are measured, never transcribed"*, and *"a figure carried forward describes a repository that no longer exists."*** ⚡ **QE has been re-measuring the certification figures every cycle and carrying the surrounding ones forward**, which is the same defect the rule names, in the file that states it. ✅ **The anchored-replacement discipline is what caught it: the edit asserting `count == 1` failed against three dated release summaries, and dated records are exactly what must not be rewritten.**

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4201 backend** · **1672 frontend** *(+8)* · **95.38%** · **398 invariants** · **843 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **123 runs recorded, 115 certified** · `promoted == certified` ✓ · `--audit-main` clean · **first attempt** |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · smoke 233s · **18 modules · 52 ADRs · 142 architecture documents** |
| **Dependency** | ✅ **Nothing held.** ⚡ **A ratified vendor is adopted rather than worked around** |
| **Customer Value** | ⚡ **A verification email can leave the process** — the thing Workflows 3, 4 and 5 each needed |
| **Process** | ⛔ **QE corrected four of its own figures this cycle.** ⚡ **The mechanism that found them is the one that refuses a broad replacement** — an assertion that the text appears exactly once |

---

## 1e · Release summary — 2026-08-08, cycle 117

**Derived from the promoted commit `063908a`.** **Seventy-two promotions.** ⚡ **A quiet cycle whose whole content is three registers agreeing with each other — and one id that three parties reached independently.**

### What was promoted

| | |
|---|---|
| ⚡ **[C-240](docs/LANE_COORDINATION.md)** *(Lane A)* | **Renumbered into Lane A's own block, by Lane A** — *"the allocation was this lane's defect"* |
| ✅ **[B-149](docs/BUGS.md) closed** *(Lane A)* | The lane's own account of the fix, and its own account of the ordering defect behind it |
| **[D-180](docs/DECISION_REGISTER.md)** *(Lane C)* | Execution mode accepted; ⑩ stopped at a permission refusal |

### ⚡ Three parties reached `C-240` independently, and none of them coordinated

| | |
|---|---|
| **QE, cycle 115** | Renumbered Lane A's item to `C-240` at merge — ⛔ **on the candidate it then excluded**, so it never reached `main` |
| **Lane A, cycle 116** | Renumbered to **`C-436`** on rebase, unaware — **still Lane C's block** |
| **Lane A, cycle 117** | ✅ **Moved it again to `C-240`**, naming the real fault: *"the allocation was this lane's defect"* |

> ⚡ **The block model produced one answer from three directions**, which is the argument for it: **`200+` is Lane A's and nothing else had to be agreed.** ⛔ **What it did not prevent is the original mistake** — allocating *next-free-after-`C-434`* instead of next-free in one's own block — **and no instrument can, because the duplicate exists only in the union of two branches and nothing reads the union.**

### ✅ [B-149](docs/BUGS.md) closed with both accounts kept, not merged into one

**The row conflicted at merge: QE had set `VERIFIED`, Lane A had set `FIXED`.** ⛔ **`VERIFIED` is QE's and stands** — **and Lane A's account is preserved verbatim beside it rather than overwritten**, because it carries what QE could not know:

> *"This lane ran it **after** pushing the milestone rather than before, so a broken commit sat on `origin` and was certifiable for twenty-seven minutes… The repair is not a code change: the headed journey runs before the push, not after it."*

⚡ **It also corrects QE's framing.** **The locator was fixed at `05:06:04Z`, an hour before the row was filed** — the lane had already hit the identical violation in its own headed run. ⛔ **What reached `origin` was the broken commit, and the row was right to name it.** ✅ **And the scoping was deliberate, not a sweep**: three Workflow 2 locators got `{ exact: true }` and **the four sign-in locators were deliberately left bare**, because `/sign-in` has no meter.

> ⛔ **A register that overwrote the lane's account with QE's would have lost the only part nobody else could write.** **Status is authority; the account is evidence, and they are not the same field.**

### ⚡ Two claims landed on `integration` mid-certification, and nothing had to stop

**`TASK-486` — Workflow 3 · Email Verification** and **`TASK-494` — email through the ratified vendor**, both bounded to the two files a claim may touch, both arriving after the Certification Snapshot.

> ✅ **`integration` kept moving and QE never chased it.** **The certified commit was promoted; the two claims belong to the next cycle by construction** — and **Lane A's zero-claimable window, reported three times yesterday, closed by itself.**

### ✅ Smoke 152s, `slowest 2. Startup 19s` — a fifth confirmation

**Backend-only cycles: 144s, 152s, naming `Startup` or nothing. Frontend cycles: 214s, 225s, naming `Build`. Outliers: 621s, 2652s, naming `Researched account`.** ⚡ **[B-141](docs/BUGS.md) is three populations with five confirmations.**

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4201 backend** · **1664 frontend** · **95.38%** · **398 invariants** · **843 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **122 runs recorded, 114 certified** · `promoted == certified` ✓ · `--audit-main` clean · **first attempt** |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · smoke 152s |
| **Dependency** | ✅ **Nothing held, and nothing idle** — both lanes claimed this cycle |
| **Customer Value** | ⛔ **None directly.** **Registers, and the next two journeys claimed** |
| **Process** | ⚡ **The cheapest possible cycle: six changed paths, sixteen gates, first attempt** — and its content is the repository correcting its own bookkeeping without anybody being told to |

---

## 1e · Release summary — 2026-08-08, cycle 116

**Derived from the promoted commit `50e8113`.** **Seventy-one promotions. Sixteen commits, both lanes, first attempt.** ⚡ **A customer can create an account — and the slice that shipped it is the one QE returned an hour earlier.**

### ✅ What a customer gets

| | |
|---|---|
| ⚡ **Workflow 2 · Registration** *(Lane A)* | **Screen `06 Create account`, to the approved design.** A person types a name, an address and a password, watches a strength meter answer as they type, and reaches verification. **The meter reports and never gates** — a long all-lowercase password satisfies one rule of three and is still accepted, because refusing it would be the screen inventing a security policy |
| **Eight decision packages** *(Lane C)* | **[D-172](docs/DECISION_REGISTER.md)** person-scoped tenancy · **[D-174](docs/DECISION_REGISTER.md)** Security Center · **[D-175](docs/DECISION_REGISTER.md)** Casbin only · **[D-176](docs/DECISION_REGISTER.md)** · **[D-177](docs/DECISION_REGISTER.md)** authorization is three questions · **[D-178](docs/DECISION_REGISTER.md)** · **[D-179](docs/DECISION_REGISTER.md)** adoption becomes state |

### ✅ [B-149](docs/BUGS.md) `VERIFIED` — returned, fixed, and re-checked by the instrument that found it

**Lane A found the same defect independently and made the same repair QE would have named** — `getByLabel('Password', { exact: true })` at all three call sites.

**Re-run at `50e81139` against the same unseeded stack that found it: 6 passed, 1 failed, where the same selection was 3 failed.** ⛔ **The remaining one is not evaluated and QE does not claim it**: that stack holds **`0` of the four Better Auth tables**, measured, and the scenario creates a real account. ⚡ **Lane A reports 7 of 7 headed on a provisioned environment, plus Workflow 1 at 27 of 27 as a regression check on the `PasswordField` extraction** — **recorded as the lane's claim, because it is one.**

> ⚡ **The whole loop cost one cycle.** **Returned 05:0x, fixed and promoted the same hour** — and the lane's own account of the repair names the substring rule, the exact fix, and a second unrelated thing the headed run taught it about an `aria-hidden` on a tick `svg`. ⛔ **That is what `CHANGES REQUESTED` is supposed to look like, and it is the first time this session it has been exercised.**

### ⚠️ Two corrections to cycle 115's record, and neither is tidied away

| | |
|---|---|
| ⛔ **`C-240` does not exist** | **Cycle 115's Closeout says QE renumbered Lane A's item to `C-240` at merge. It did — on the candidate that was then excluded**, so the renumber went with it. ✅ **The live id is [`C-436`](docs/LANE_COORDINATION.md), renumbered by Lane A itself on rebase**, which is what §20e asks a lane to do |
| ⚠️ **The streak was miscounted** | **Cycle 115 called its abort *"the eighteen-cycle first-attempt streak ends here"*. ⚡ It was QE's own dirty tree, not a gate** — and **this cycle certified sixteen commits from two lanes on the first attempt** |

> ⚡ **The first correction is the interesting one: QE's dated record described a repository state that a later decision in the same cycle undid.** **The commit was excluded and the sentence was not re-read.** ⛔ **Correct a claim about the present; date a record of the past** (§2) — **and a Closeout is both, which is exactly why it needs re-reading after an exclusion.**

### ⚠️ Lane A reports zero claimable, for the third time today

**[C-435](docs/LANE_COORDINATION.md) is now a three-instance pattern rather than an incident.** ⚡ **Lane A delivered Workflow 2 and went straight to `claimable = 0`** — and **[D-179](docs/DECISION_REGISTER.md) landed a check for exactly this in the same cycle, which *"fired in its first minute"*.**

### ✅ Smoke 214s, `slowest 1. Build 57s` — the reading holds a fourth time

**Frontend cycles name `Build` (225s, 214s). Backend-only cycles name `Startup` or nothing (144s). The outliers name `Researched account` (621s, 2652s).** ⚡ **Three populations, four confirmations — [B-141](docs/BUGS.md) is a characterisation now, not a mystery.**

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4201 backend** · **1664 frontend** · **95.38%** · **398 invariants** · **843 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **121 runs recorded, 113 certified** · `promoted == certified` ✓ · `--audit-main` clean · ⚡ **sixteen commits, two lanes, one attempt** |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · smoke 214s |
| **Dependency** | ⚠️ **Lane A at zero claimable** — [C-435](docs/LANE_COORDINATION.md), third instance |
| **Customer Value** | ✅ ⚡ **A person can create an account.** **The second of the approved journeys is on `main`** |
| **Process** | ⚡ **The return loop worked end to end for the first time**: QE excluded on evidence, named the defect precisely, held no other lane — **and the fix was back, verified and promoted within the hour** |

---

## 1e · Release summary — 2026-08-08, cycle 115

**Derived from the promoted commit `e60e5e3`.** **Seventy promotions.** ⛔ **The first cycle in eighteen to exclude a slice, and the first in this session where QE aborted its own run.**

### What was promoted — Lane C only

| | |
|---|---|
| **[D-173](docs/DECISION_REGISTER.md)** *(Lane C)* | **[491](docs/architecture/491-planning-synchronization-architecture.md) — the coupling is a ruling already made and half-implemented** |
| **[C-435](docs/LANE_COORDINATION.md)'s id collision, reported** *(Lane C)* | ⚡ **The office found the duplicate, named the rule that resolves it, and declined to act** — *"renumbering an existing identifier is QE's, and this office may not edit another lane's row."* **QE renumbered Lane A's to [C-240](docs/LANE_COORDINATION.md) at merge** |

### ⛔ What was excluded — [B-149](docs/BUGS.md), and the journey is how it was found

**`TASK-485` milestone 1 — screen `06 Create account` — was certified and then excluded**, because QE ran the Playwright journey §19 requires the implementing lane to have run.

```
strict mode violation: getByLabel('Password') resolved to 2 elements:
  1) <input type="password" autocomplete="new-password" …>
  2) <div role="meter" aria-label="Password strength" …>
```

⚡ **`getByLabel` matches on substring, so `'Password'` matches `'Password strength'`** — **the meter the same slice introduced.** ⛔ **The spec and the component were written together and the spec cannot address the component.** **Three scenarios fail, one of them the `@journey` scenario itself.**

> ⚠️ **Every certification gate passed on that candidate** — [`18853e430119`](certification/reports/18853e430119.md) is a true record and stands. **Playwright is in the ten-gate shortfall [B-131](docs/BUGS.md) prints every run**, so certification could not have caught it. ⚡ **This is the first time that shortfall has cost a promotion, and it is the strongest evidence yet for closing it.**
>
> ⛔ **Lane A is not held on Lane C's account and Lane C was not held on Lane A's.** The cycle was rebuilt with Lane C's two commits alone and promoted the same hour.

### ⚠️ Three of five failures were Lane A's, and two were QE's — proved, not assumed

**QE has no supported way to run the journey.** `make e2e` derives `SIGNORA_PG_PORT=5632` for `lane-qe`, and **nothing in the repository launches that environment** — `infra/environments.py` says so itself: *"Phase 1: the model only."* **QE pointed Playwright at the production stack instead, unseeded.**

| Failure | Whose |
|---|---|
| **3 × strict-mode violation** on `/sign-up` | ⛔ **Lane A's.** Pure DOM — no database, no API, no session, no seed. **Identical on every machine** |
| **2 × sign-in scenarios** | ✅ **QE's environment.** **That stack has no `user` table at all** — Better Auth's are created by `npm run auth:migrate`, which nothing ran there |

> ⚡ **A sign-in test cannot fail meaningfully against a database with nobody in it**, and reporting those two would have put a false lead in front of the lane. **The check is whether a failure is a statement about the commit or about the run** — and a strict-mode violation is the clearest possible case of the first.

### ⚠️ QE aborted its own certification, and the record says so

**[`e60e5e3d4202`](certification/reports/e60e5e3d4202.md) was run twice.** The first attempt read **`NOT CERTIFIED · the working tree was dirty, so the tree certified was never stored`** — **every gate passed and only `tree_clean` failed**, because QE edited `BUGS.md` while the run was in flight.

> ⛔ **That is an abort, not a failure** — a statement about the run, never about the commit ([REPOSITORY_RELEASE_CHECKLIST.md](docs/REPOSITORY_RELEASE_CHECKLIST.md)). **Both attempts are in the manifest and neither was deleted** (§2): **120 runs now, where a tidier account would show 118.**
>
> ⚠️ **The checklist already warned about exactly this** — *"Commit the slice first, certify second, then commit the record it produces."* **QE knew the rule and broke it by filing a bug row at the wrong minute.**

### ✅ Smoke 144s, `slowest 2. Startup 19s` — and the two-population reading held again

**The excluded frontend candidate measured 225s with `slowest 1. Build 58s`; this backend-only one measured 144s.** ⚡ **Frontend cycles name `Build`, slow cycles name `Researched account`, quiet ones name neither** — [B-141](docs/BUGS.md) is now a three-way separation rather than an anomaly.

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4201 backend** · **1664 frontend** *(+28, measured on the excluded candidate)* · **95.38%** · **398 invariants** · **843 files typed** · **37 contracts** |
| **Release** | **120 runs recorded, 112 certified** · `promoted == certified` ✓ · `--audit-main` clean · ⛔ **the eighteen-cycle first-attempt streak ends here, by QE's own hand** |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · smoke 144s |
| **Dependency** | ✅ **Nothing held.** ⚡ **Lane C promoted while Lane A's slice was returned — the two clocks working as designed** |
| **Customer Value** | ⛔ **None.** **The customer-visible slice is the one that did not ship** |
| **Process** | ⚡ **The suite found nothing and the journey found everything**, which is §20e's own claim about this repository: *every defect that has mattered was found by using the product, not by the suite* |

---

## 1e · Release summary — 2026-08-08, cycle 114

**Derived from the promoted commit `d989172`.** **Sixty-nine promotions.** ⚡ **A starvation check that could not see starvation, and two coordination files that told a lane the opposite of what the backlog said.**

### What was promoted

| | |
|---|---|
| ⚡ **[B-409](docs/BUGS.md) — the starvation check counted finished work** *(Lane C)* | `in_flight` collapses **eight** declared states and **only three are work a lane can touch.** **Lane A idled 136 cycles holding 48 in-flight rows, every one `IN VALIDATION` and untouchable**, and the check stayed silent *because the number was large.* **`actionable` is published beside it and `state-check` now reads that** |
| **[C-435](docs/LANE_COORDINATION.md) — the synchronization deadlock** *(Lane C)* | Two rules, each correct, deadlock: **§20e** *"only executable change opens a cycle"* decides **whether** a cycle happens; **[D-136](docs/DECISION_REGISTER.md)** orders planning corrections **within** one. **Neither can start one** — so the condition that makes a correction urgent is the condition that prevents it landing |

### ⚡ The deadlock C-435 describes resolved itself while C-435 was being written

**Lane C measured it at 04:03 and filed it at 04:14.** **QE promoted `f6f9c851` at 04:10 and Lane A claimed `TASK-485` immediately after.**

> ⛔ **That does not make the finding wrong, and QE is not reporting it as wrong.** **The escape was luck of timing**: `f6f9c851` happened to carry coordination TOML, the planner classifies that as **`platform`** because three gates read it, so a planning-only push *was* certifiable. ⚡ **Change one of those facts and the deadlock is real.**
>
> **What the cycle actually demonstrated is narrower and worth stating: the planner's classification is what broke the tie.** A directory prefix would have called it documentation, no cycle would have been warranted, and Lane A would still be idle ([D-115](docs/DECISION_REGISTER.md)).

### ⚠️ [B-148](docs/BUGS.md) filed — the queue tells Lane A not to claim what it is building

**`queues/lane-a.toml` carries a 🔴 block: *"DO NOT CLAIM TASK-485 YET… integration says TASK-485 is SEQUENCED."*** ⛔ **It says `CLAIMED`.** Lane A claimed it in cycle 113 and is mid-slice.

**The notice names its own discharge condition** — *"WHAT UNBLOCKS YOU, precisely: QE integrating `lane-c-sync`. Nothing else."* — **and both commits it names by SHA are now on `main`.**

> ⚠️ **Distinct from [B-145](docs/BUGS.md), and the distinction is the fix.** B-145 is a *generated* value drifting by the clock, so the repair is the generator. ⛔ **This is a hand-written instruction frozen into a generated file: regenerating does not remove it, nothing computes it, and it has no expiry.**
>
> ⚡ **The office was right about the condition and right to publish it.** **What it published was a point-in-time judgement in a file whose entire contract is *what is true when you read it*.** **A register is read as history; a lane's queue is read as instruction.**

### ⚠️ Smoke 621s — the slow population names the same stage a third time

**`Researched account 420s` of 621s.** The two 2652s outliers named it too; every fast cycle names `Build`. ⚡ **Two populations, one stage, three observations — [B-141](docs/BUGS.md) now has a suspect rather than a mystery.**

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4201 backend** · **1636 frontend** · **95.38%** · **398 invariants** · **843 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **117 runs recorded, 110 certified** · `promoted == certified` ✓ · `--audit-main` clean · **seventeenth consecutive first-attempt certification** |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · ⚠️ **smoke 621s** |
| **Dependency** | ✅ Nothing held. **Lane A is building `TASK-485`** |
| **Customer Value** | ⛔ **None directly.** Instrumentation and coordination |
| **Process** | ⚠️ **Two of this cycle's three commits are the Product Office reporting on its own supply line**, and **both findings are correct.** ⛔ **A third — [B-148](docs/BUGS.md) — is the same office instructing a lane from a state that had already changed** |

---

## 1e · Release summary — 2026-08-08, cycle 113

**Derived from the promoted commit `f6f9c85`.** **Sixty-eight promotions.** ⚡ **A screen that was 3 of 12 against its design is 12 of 12, and the one override it still carried was removed by adding the token it wanted.**

### What was promoted

| | |
|---|---|
| ⚡ **Workflow 1 — design conformance** *(Lane C)* | **Screen 02 is 12 of 12 elements against the finalized design.** It was **3 of 12 on 2026-08-07.** Card geometry 4 of 4, responsive present, seven foundation gaps closed, every state and accessibility affordance present |
| **Workflow 2 released** *(Lane C)* | Under [D-169](docs/DECISION_REGISTER.md), **reaching `main` is the release condition between workflows** — so no approval was waited for. **`TASK-485` is Lane A's current** |

### ⚡ The override was removed by closing the gap, not by patching the screen

**`max-w-[400px]` is gone; it is `max-w-card`** — the token `TASK-491` added, consumed exactly as [D-162](docs/DECISION_REGISTER.md) ④ required.

> **A gap named, closed in the foundation, and the screen simplified rather than worked around.** That is the shape §20c asks for and the shape a lane under time pressure does not take: the cheap fix was to leave the literal and note it.

### ⚠️ Three greps returned a hit, and the lane published all three

| Hit | Why it is legitimate |
|---|---|
| `bg-slate-50` | **Inside a comment explaining the ban** |
| `!important` | **Inside `prefers-reduced-motion`, where it must win** |
| `w-[calc(100vw-2.5rem)]` | **Paired with `max-w-card`** for the design's 20px mobile gutters — **a viewport calc is not expressible as a token** |

> ⚡ **The third is the honest edge, and it is recorded so nobody "fixes" it.** A lane reporting *"zero findings"* would have been believed; **a lane reporting three hits and defending each is the more useful claim**, because the next reader can check it.

### ✅ The profile is recorded for the first time

**`profile: platform`** appears in [`f6f9c8510bac`](certification/reports/f6f9c8510bac.md) — **[427](docs/architecture/427-impact-based-validation.md) step 2 landing on real traffic.** ⛔ **Recorded, never applied**: `REQUIRED_GATES` is unchanged, all six ran, and `satisfied` never read the field.

> **The planner classified `docs/coordination/**` as `platform` and it was right to.** Three gates read those files, so a diff of nothing but coordination TOML is a platform change — **which a directory prefix would have called documentation** ([D-115](docs/DECISION_REGISTER.md)).

### ⚠️ `--audit-main` refused between promotion and Closeout, correctly

**The audit reads the *committed* manifest. The record for `f6f9c851` was still in QE's working tree**, so for the minutes between the push and this commit `main` genuinely carried a commit the repository could not prove was certified.

> **It is an ordering artifact and not a defect — and it is worth stating rather than quietly resolving.** The direct guard-check on the SHA passed before promotion (§0e-3), which is the check that gates. ⛔ **But an auditor that reads red for a real window is a fact about the process, not noise to suppress**, and a session polling in that window would have been right to stop.

### ⚠️ [B-147](docs/BUGS.md) filed — the same commit released a journey and declared none in flight

**`f6f9c85` moved Workflow 1 `active` → `on_main` and Workflow 2 `decomposed` → `ready`.** ⛔ **`state-check` counts the string `active` and now finds zero**, two findings above the one reporting `TASK-485` startable in the same run.

> ⛔ **Which of the two is wrong is Lane C's to decide and QE deliberately did not.** **The row states both readings and picks neither** — the file is Lane C's, the check's vocabulary drifted from it, and *"the repair is the generator"*.

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4201 backend** · **1636 frontend** · **95.38%** · **398 invariants** · **843 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **117 runs recorded, 109 certified** · `promoted == certified` ✓ · `--audit-main` clean · **sixteenth consecutive first-attempt certification** |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · smoke 184s |
| **Dependency** | ✅ Nothing held. **Lane A unblocked** — `TASK-485` released by this cycle |
| **Customer Value** | ⚠️ **Indirect.** The first workflow now looks like the approved design |
| **Process** | ⚡ **Fifty consecutive quiet polls preceded this cycle.** The repository was idle, not stalled — and the poll that found work found it within ten minutes |

---

## 1e · Release summary — 2026-08-07, cycle 112

**Derived from the promoted commit `1e09e25`.** **Sixty-seven promotions.** ⚡ **A governance edit QE read before certifying, and the fastest smoke of the session.**

### What was promoted

| | |
|---|---|
| **[D-170](docs/DECISION_REGISTER.md)** *(Lane C)* | Three rulings applied — ⚡ **including the one edit Product Office has ever made to `CLAUDE.md`** |
| **[D-171](docs/DECISION_REGISTER.md)** *(Lane C)* | **[490](docs/architecture/490-operating-model-critique.md) — the operating model, critiqued as it asked, and six weaknesses named with evidence** |

### ⚠️ The `CLAUDE.md` edit, checked rather than waved through

**`CLAUDE.md` is the product owner's** (§20e); Lane C drafts amendments **on their instruction and nowhere else.** The diff is six lines under **§20c**, the frontend foundation freeze:

> *"The UI Migration Program is a standing approved architectural change under the fourth exemption… **Replacing the design tokens, the shells and the shared components to match the finalized Signora Design System is the programme, not a breach of the freeze.**"*

**Three things made it certifiable without QE adjudicating governance:**

| | |
|---|---|
| **It names its authority** | [D-170](docs/DECISION_REGISTER.md) §2, *"on the product owner's explicit instruction and their wording"*, resting on **D-153 · D-154 · D-161**, all ruled |
| **It clarifies rather than changes** | §20c already exempts *"an explicitly approved architectural change (RFC)"* — **this says the migration is one**, not that the freeze is narrower |
| ⚡ **It preserves what the freeze exists for** | *"The freeze continues to bar ad-hoc modification for one page's benefit… **the distinction is the direction of the change: toward the finalized design is the migration; away from it, to suit one caller, is the defect.**"* |

> **That is the second governance-shaped commit QE has read this session before certifying it** — [D-165](docs/DECISION_REGISTER.md) removed a lane from the active model. **Both named a ruling; neither needed QE to decide anything.** ⛔ **The check is cheap and the alternative is certifying a rule change nobody authorised.**

### ✅ Smoke 141s — the fastest reading of the session

**No frontend in the candidate, and the gate returns to the low end of its band.** ⚡ **`Build` has named the slowest stage on every frontend cycle and none of the others** — the separation `_slowest_stage` was added to expose, holding across ten cycles now.

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4201 backend** · **1636 frontend** · **95.38%** · **398 invariants** · **843 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **116 runs recorded, 108 certified** · `promoted == certified` ✓ · `--audit-main` clean · **fifteenth consecutive first-attempt certification** |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · ✅ **smoke 141s** |
| **Dependency** | ✅ Nothing held. Lane A level with `main` |
| **Customer Value** | ⛔ **None directly.** Governance and a self-critique |
| **Process** | ⚡ **The operating model was asked to critique itself and named six weaknesses with evidence** — [490](docs/architecture/490-operating-model-critique.md) |

---

## 1e · Release summary — 2026-08-07, cycle 111

**Derived from the promoted commit `9aae52b`.** **Sixty-six promotions.** ⚡ **Workflow 1 is complete, and a lane's poll reported it had not started.**

### What was promoted

| | |
|---|---|
| ⚡ **Workflow 1 milestone 4** *(Lane A)* | ***"what the product says while it waits, and what it says when the answer is no"*** — **the workflow is now complete to the boundary [D-156](docs/DECISION_REGISTER.md) drew** |
| **TASK-491** *(Lane A)* | **The design foundation's remaining gaps, *measured rather than read off the row*** — the seven the conformance audit found |
| **D-167 · D-168 · D-169** *(Lane C)* | Including **charting ruled — `visx`**, *"and the second figure is what decides it"* |

**+32 frontend tests.** ⚠️ **`visx` is ruled and not yet installed** — `package.json` is untouched, so no dependency gate applies this cycle.

### ⛔ A lane reported Workflow 1 had not reached `main`. It had, three times

**A poll arrived stating** *"QE has not certified `lane-a-product-surface`, and Workflow 1 has not reached `main`, so the D-158 review gate has not opened."*

**Measured, not argued:**

```
75b8b464  Workflow 1 milestone 3 — the front door, the enterprise route…
d103fa39  Workflow 1 milestone 2 — the sign-in experience
8295fdb1  Workflow 1 milestone 1 — the authentication shell
```

**All three on `origin/main`, all three CERTIFIED** — cycles 104, 105 and 109. ⚡ **So the review gate was open and the lane was holding on nothing.**

> **The lane's evidence was sound and its inference was not.** *"My branch carries unpromoted commits"* was **true** — TASK-491, three of them, verified `on_main=0`. *"Workflow 1 has not reached `main`"* was **false**. ⛔ **A branch ahead by ref says nothing about whether earlier work was promoted**, because its content lands under different SHAs after a rebase.
>
> ⚡ **This is why QE resolves every ahead-count by patch-id before believing it** — a habit that has retired a false *"held"* reading in **eight of the last twelve cycles**, and here it corrected a lane that was blocking itself.

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4201 backend** · **1636 frontend** *(+32)* · **95.38%** · **398 invariants** · **843 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **115 runs recorded, 107 certified** · `promoted == certified` ✓ · `--audit-main` clean · **fourteenth consecutive first-attempt certification** |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · smoke **198s**, `Build 57s` — the frontend shape |
| **Dependency** | ✅ Nothing held. ⚠️ **`visx` ruled, not installed** — the dependency gate applies when it arrives |
| **Customer Value** | ⚡ **A customer can sign in end to end** — the front door, the enterprise route, what the product says while it waits, and what it says when the answer is no |
| **Process** | ⚡ **A measurement corrected a lane that had blocked itself on a condition already satisfied** |

---

## 1e · Release summary — 2026-08-07, cycle 110

**Derived from the promoted commit `16ba152`.** **Sixty-five promotions.** ⚡ **[D-167](docs/DECISION_REGISTER.md)'s first step, and the most useful thing in the cycle is a measurement QE got wrong.**

### What was promoted

| | |
|---|---|
| ⚡ **[427](docs/architecture/427-impact-based-validation.md) step 2** *(QE)* | **A run records the profile the Validation Planner computed for its diff.** ⛔ **`REQUIRED_GATES` unchanged, every gate still runs, `satisfied` never reads the field** |

✅ **The first record carrying one landed this cycle**: `profile: "platform"`.

### D-167 already had a design, and step 1 was already running

⚡ **[427](docs/architecture/427-impact-based-validation.md) is a five-step migration plan, and step 1 — *emit the analysis, change nothing else* — has executed at every certification since TASK-414.** **D-167's safety rule is already the planner's stated law**: *"unknown paths widen it, never narrow it."*

### ⛔ QE tried to answer step 1's exit question and got it wrong

**427**: *"If the classifier disagrees with reality even once during step 1, the framework is not ready."*

**Across 112 runs, seven have a failing gate.** QE re-derived each one's profile and reported:

```
4d37ede0  smoke   documentation  *** NO — classifier disagreed ***
4b3da374  pytest  documentation  *** NO — classifier disagreed ***
6aaf45ef  pytest  documentation  *** NO — classifier disagreed ***
```

⛔ **Four of seven. That would have declared the framework unsafe — and the measurement was wrong.** QE diffed each failing commit against **its own parent**; every candidate was multi-commit and the last commit was usually QE's own doc-only bug row. **The proxy classified a diff nobody ever certified.**

**Against the real bases:**

```
4d37ede0  base ace4460d  16 paths  profile=platform  'smoke'  in plan: True
4b3da374  base f3ec15f2  73 paths  profile=platform  'pytest' in plan: True
6aaf45ef  base f3ec15f2  72 paths  profile=platform  'pytest' in plan: True
```

> ⚡ **The classifier was right every time.** **And *"a measurement taken from the wrong range is indistinguishable from a finding"* is precisely the argument for step 2** — record the number when it is computed, rather than reconstructing it from a range nobody kept.

### Two safety properties, both mutation-checked

| | |
|---|---|
| **The profile never changes a verdict** | Making `missing_gates` return empty for a `documentation` profile **kills the vacuity test** — the defect [427 §1](docs/architecture/427-impact-based-validation.md) names, where a mis-classification reads as a pass |
| **An absent profile reads as empty, never inferred** | Defaulting it to `"platform"` kills two tests: **112 historical records would claim a measurement nobody took** |

✅ **All 112 existing records still parse** under `extra="forbid"`; `satisfied` unchanged at 66/112.

⏸️ **Steps 3–5 — actually applying the profile — stay gated on step 1's evidence**, exactly as 427 requires.

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4201 backend** *(+8)* · **1604 frontend** · **95.38%** · **398 invariants** · **843 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **114 runs recorded, 106 certified** · `promoted == certified` ✓ · `--audit-main` clean · **thirteenth consecutive first-attempt certification** |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · ⚡ **the certification record gained a field for the first time since it was written** |
| **Dependency** | ✅ Nothing held |
| **Customer Value** | ⛔ **None directly.** The instrument that decides what ships got one step smarter |
| **Process** | ⚡ **QE published its own wrong measurement, corrected it, and made the correction the argument for the change** |

---

## 1e · Release summary — 2026-08-07, cycle 109

**Derived from the promoted commit `f6df17e`.** **Sixty-four promotions.** ⚡ **Workflow 1's third milestone, and the largest frontend slice of the session.**

### What was promoted

| | |
|---|---|
| ⚡ **Workflow 1 milestone 3** *(Lane A)* | **The front door, the enterprise route, and the two states between signed in and signed out** — Welcome, SSO, throttled sign-in, service status, session lock, an auth client, **307 lines of state tests** and **59 more lines of journey**. **1,206 insertions** |
| **C-434** *(Lane A)* | *"three of Login's remaining screens need a decision, and one of them shipped against a ruling"* |
| **D-166** *(Lane C)* | *"testing metadata on eight rows, and the forward pass found Welcome has no route"* |

**+38 frontend tests, 68 files.**

### ⚡ Two lanes found the same gap from opposite ends, in one cycle

**Lane C's forward pass through the design found *"Welcome has no route."*** **Lane A's C-434, working backward from what it had just built, found *"three of Login's remaining screens need a decision, and one of them shipped against a ruling."***

> ⛔ **Neither is a `B-` row, and neither should be.** **One is planning discovering a gap before implementation reaches it; the other is implementation discovering a decision it needs.** ⚡ **They met in the same cycle because the design snapshot is one artifact and both lanes read it** — which is what [D-138](docs/DECISION_REGISTER.md) made it for.

### The frontend smoke signature, fourth consecutive confirmation

**`slowest 1. Build 53s`** on a cycle adding **six screens**. ⛔ **Every high smoke reading since cycle 101 names `Build`; the two [B-141](docs/BUGS.md) outliers name `Researched account`.** **The two populations have not overlapped once in nine cycles.**

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4193 backend** · **1604 frontend** *(+38)* · **95.38%** · **398 invariants** · **842 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **113 runs recorded, 105 certified** · `promoted == certified` ✓ · `--audit-main` clean · **twelfth consecutive first-attempt certification** |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · smoke **192s, cause named** |
| **Dependency** | ✅ Nothing held |
| **Customer Value** | ⚡ **A customer can now meet the front door, take the enterprise route, and be told honestly when the service is down or their session has locked** — the states a login screen usually pretends do not exist |
| **Process** | ⚡ **[B-146](docs/BUGS.md) is open against QE and is not being closed by a bulk edit** |

---

## 1e · Release summary — 2026-08-07, cycle 108

**Derived from the promoted commit `18fa051`.** **Sixty-three promotions.** ⚡ **The organisation changed shape, a new certification strategy arrived, and QE found a defect in its own bookkeeping.**

### What was promoted

| | |
|---|---|
| **[D-165](docs/DECISION_REGISTER.md)** *(Lane C)* | **One implementation lane is permanent; Product Office becomes a continuous planning function.** Lane B leaves the *active* model — ⛔ **history intact**, and `queues/lane-b.toml` deleted because the generator emits a block only where rows resolve to it |

**QE read the register entry before certifying**, because §20e is explicit that an ownership change *"requires its own explicit decision… never arriving inside a governance edit."* ✅ **D-165 is that decision, `APPROVED`, in the register.** **Form correct; not QE's to adjudicate further.**

### ⚡ [D-167](docs/DECISION_REGISTER.md) — risk-based certification, and most of it already exists

**The product owner directed impact-aware certification.** ⚡ **The Validation Planner ([D-115](docs/DECISION_REGISTER.md)) already performs the analysis** — profiles `documentation · frontend · module · contract · persistence · security · platform`, a computed gate list, and a journey selection.

> **D-167's safety rule is already the planner's stated law**: *"This plan is computed, not chosen. **Unknown paths widen it, never narrow it.**"*

⛔ **The missing half is exactly [B-131](docs/BUGS.md)**, reported every cycle this session: **the planner requires 16–17 gates and the record contains 6.** **D-167 is the decision B-131 and [B-123](docs/BUGS.md) were waiting on** — closing them means making `REQUIRED_GATES` profile-aware, which changes what *certified* means and could not be done unilaterally.

⚠️ **One constraint QE will preserve**: `make certify` stays optionless. **The scope comes from the computed plan, never from a flag a human picks** — ADR-0032's reasoning, unchanged.

### ⛔ [B-146](docs/BUGS.md) — QE's own bookkeeping, filed against QE

**49 rows read `IN VALIDATION`. 4 read `PROMOTED`.** Across sixty-three promotions, that is not plausible — and **`PROMOTED` is QE's exclusively.** QE reconciled the *board* at every Closeout and never advanced the *backlog*.

⚡ **It surfaced because D-165 reasons from those rows** — *"twelve `IN VALIDATION` rows… need QE, not an implementer"* — **correct governance applied to a state QE never advanced.**

⛔ **QE did not bulk-fix it, and stated why**: the obvious check is `git log --grep`, which matches every commit *mentioning* an id. **That is [B-101](docs/BUGS.md)'s class and what [B-144](docs/BUGS.md) cost when a grep decided a gate.** **Rows advance as each is verified by opening what it claims to have shipped.**

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4193 backend** · **1566 frontend** · **95.38%** · **398 invariants** · **842 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **112 runs recorded, 104 certified** · `promoted == certified` ✓ · `--audit-main` clean · **eleventh consecutive first-attempt certification** |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · smoke **155s** |
| **Dependency** | ✅ Nothing held. Lane A fully promoted before the cycle began |
| **Customer Value** | ⛔ **None directly.** An organisational decision and a certification directive |
| **Process** | ⚠️ **QE filed a 🟡 against itself and declined to close it with one commit** — an understated board is better than a confidently wrong one |

---

## 1e · Release summary — 2026-08-07, cycle 107

**Derived from the promoted commit `5391744`.** **Sixty-two promotions.** ⚡ **The palette defect ends the way governance says it should — with a test, not a promise.**

### What was promoted

| | |
|---|---|
| ⚡ **TASK-490** *(Lane A)* | **The design foundation, *from the canonical source and checked by a test*** — `globals.css`, `layout.tsx`, `tailwind.config.ts`, and **116 lines of `design-foundation.test.tsx`** |
| **D-163** *(Lane C)* | *"the queue advances itself, and a check now says so every run"* |

**+18 frontend tests, 67 files.**

### ⚡ Three cycles, and the arc is the point

| | |
|---|---|
| **105** | Lane C's **D-161**: *"Lane A built the right screen against the wrong palette, and that is my defect"* |
| **106** | **D-162**: the foundation gates everything |
| **107** | ⚡ **TASK-490: the foundation rebuilt from the canonical source, and a test that fails if it drifts again** |

> ⛔ **The defect was not closed by an assertion that it had been fixed.** **§20c already required design tokens to be enforced by test rather than by convention** — *"a theme change must be a token edit, enforced by `design-tokens.test.tsx`"* — **and this slice extends that enforcement to the foundation itself.** ⚡ **A guarantee that needs a person to remember it is not a guarantee.**

### Smoke 200s — the confirmed shape, third time

**`slowest 1. Build 56s`.** ⛔ **Every high smoke reading since cycle 101 has been a frontend cycle, and every one has named `Build` as the slowest stage.** The two [B-141](docs/BUGS.md) outliers named `Researched account` instead. **Two populations, cleanly separated by the field `_slowest_stage` was added to record.**

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4193 backend** · **1566 frontend** *(+18)* · **95.38%** · **398 invariants** · **842 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **111 runs recorded, 103 certified** · `promoted == certified` ✓ · `--audit-main` clean · **tenth consecutive first-attempt certification** |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · smoke **200s, cause named** |
| **Dependency** | ✅ Nothing held anywhere |
| **Customer Value** | ⚡ **Every screen now inherits the approved palette from one source**, and a test refuses the legacy one |
| **Process** | ⚡ **A defect an office admitted, a lane corrected, and a test now prevents** — three cycles, no `B-` row needed |

---

## 1e · Release summary — 2026-08-07, cycle 106

**Derived from the promoted commit `d8f5ab1`.** **Sixty-one promotions.** ⚡ **A short cycle, and the shortest report is the honest one.**

### What was promoted

| | |
|---|---|
| **D-162** *(Lane C)* | *"the foundation gates everything, and the one override in the repository is the right kind"* — the sequencing consequence of the palette defect [D-161](docs/DECISION_REGISTER.md) named as its own |

**Lane A was fully promoted before this cycle began** — all four of its commits resolved `dup=1`. ⛔ **A branch four ahead by ref and zero by content is a stale pointer**, and that check is now the first thing every poll does.

### ✅ Smoke 155s — the frontend explanation held

**196s · 193s · 155s.** ⚡ **The two high readings were `Build ~52s` on the cycles Lane A shipped frontend; this cycle shipped none and the gate returned to its norm.** ⛔ **That is not a resolution of [B-141](docs/BUGS.md)** — whose signature is `slowest 14k. Researched account` — **but it does close out the frontend-build explanation as confirmed rather than plausible.**

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4193 backend** · **1548 frontend** · **95.38%** · **398 invariants** · **842 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **110 runs recorded, 102 certified** · `promoted == certified` ✓ · `--audit-main` clean · **ninth consecutive first-attempt certification** |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · ✅ **smoke 155s** |
| **Dependency** | ✅ Nothing held. A claim landed mid-cycle and was replayed onto the promotion |
| **Customer Value** | ⛔ **None directly.** A sequencing decision following the palette correction |
| **Process** | ⚡ **Nine cycles without a failed gate**, since [B-144](docs/BUGS.md) cleared |

---

## 1e · Release summary — 2026-08-07, cycle 105

**Derived from the promoted commit `ab1ba57`.** **Sixty promotions.** ⚡ **Two milestones of Workflow 1 in two cycles, and a lane that found its own defect one commit after shipping it.**

### What was promoted

| | |
|---|---|
| ⚡ **Workflow 1 milestone 2** *(Lane A)* | **The sign-in experience** — the form rebuilt, and the journey spec grown from 62 lines to 182 |
| ⚡ **D-162** *(Lane A)* | *"the visual foundation was the legacy one, and it is replaced"* — `globals.css`, 108 lines changed |
| **D-157 · D-158 · D-160 · D-161** *(Lane C)* | ⚡ Including **D-161 — *"Lane A built the right screen against the wrong palette, and that is my defect"*** |

### ⚡ Two lanes, one defect, and neither blamed the other

**Lane A shipped milestone 1 against the legacy palette. Lane C's D-161 names the cause as its own** — the visual foundation it had published was the legacy one. **Lane A then replaced it in D-162, one commit later.**

> ⛔ **Neither raised a `B-` row against the other.** **The design was wrong, the office that published it said so, and the lane that consumed it fixed it** — inside two cycles and with the record naming both halves.

### ⚡ Lane C's `D-157` landed after two cycles held, and the rebase is why

**QE excluded it twice** for conflicting on **generated** `.toml` files, and declined to hand-resolve them — *the repair is the generator, not the merge.* **Lane C rebased; all four of its commits applied cleanly with no conflict at all.**

> **The exclusion cost two cycles and no work.** ⚡ **Hand-resolving would have cost a wrong file that nobody could tell was wrong**, which is what a union merge on `lane-a.toml` already did once this session.

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4193 backend** · **1548 frontend** · **95.38%** · **398 invariants** · **842 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **109 runs recorded, 101 certified** · `promoted == certified` ✓ · `--audit-main` clean · **eighth consecutive first-attempt certification** |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · smoke **193s**, `Build 51s` — the third frontend cycle with the same explicable shape |
| **Dependency** | ✅ **Nothing held anywhere.** Lane C's two-cycle backlog cleared itself with a rebase |
| **Customer Value** | ⚡ **A customer signing in now meets the approved design rather than the legacy one** — the screen and the palette both |
| **Process** | ⚡ **An exclusion that held for two cycles was resolved by the owning lane in one command, and cost nothing but time** |

---

## 1e · Release summary — 2026-08-07, cycle 104

**Derived from the promoted commit `8295fdb`.** **Fifty-nine promotions.** ⚡ **Workflow 1 stops having zero implementation.**

### What was promoted

| | |
|---|---|
| ⚡ **Workflow 1 milestone 1** *(Lane A)* | **The authentication shell, rebuilt from the design** — plus `workflow1-login.spec.ts`, a 62-line journey the lane wrote itself |

> ⚡ **[D-153](docs/DECISION_REGISTER.md) measured Workflow 1 as *"3 of 12 elements plus one file of colours"*. [D-155](docs/DECISION_REGISTER.md) placed it above every business workflow and recorded that it had **zero implementation**. This is the first commit against it.**

### ⚠️ It touches `playwright.config.ts`, which governance names by file

**`CLAUDE.md` cites that file directly under [D-134](docs/DECISION_REGISTER.md)** — the headed-execution policy — **and [TASK-476](docs/BACKLOG.md) exists to change its default.** QE read the diff rather than waving it through:

```diff
-      testMatch: /auth-journey\.spec\.ts/,
+      testMatch: /(auth-journey|workflow1-login)\.spec\.ts/,
```

✅ **One line, adding the new spec to the `anonymous` project**, with the reason in the file: *"signing in is by definition something a signed-out person does, so it cannot run under a project that arrives already authenticated."* ⛔ **The `headless` default is untouched**, so **D-134 and TASK-476 are unaffected. Within budget.**

**The planner selected `ALL` journeys** — correctly, since `playwright.config.ts` is shared infrastructure — **and they remain among the ten unrecorded gates** ([B-131](docs/BUGS.md)).

### Smoke 196s, and the shape is the explicable one

**`slowest 1. Build 53s`** — the same signature as cycle 101's 201s, when Lane A last shipped frontend. ⛔ **Not [B-141](docs/BUGS.md)'s pattern**, which is `slowest 14k. Researched account`. **A recompiled shell costs build time; that is a cause, not a mystery.**

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4193 backend** · **1548 frontend** · **95.38%** · **398 invariants** · **842 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **108 runs recorded, 100 certified** · `promoted == certified` ✓ · `--audit-main` clean · **seventh consecutive first-attempt certification** |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · smoke **196s, cause named** |
| **Dependency** | ⚠️ **Lane C's `D-157` has not landed for two cycles** — it conflicts on generated `.toml` files and needs a rebase, not a fix |
| **Customer Value** | ⚡ **The sign-in screen a customer meets first now matches the approved design** — and the top-priority workflow has an implementation for the first time |
| **Process** | ⚡ **A change to a governance-named file was read before it was gated**, and it turned out to be one line and correct |

---

## 1e · Release summary — 2026-08-07, cycle 103

**Derived from the promoted commit `ba0520a`.** **Fifty-eight promotions.** ⚡ **The chain that has been building for a week reaches the pipeline.**

### What was promoted

| | |
|---|---|
| ⚡ **TASK-458** *(Lane A)* | **A decision-maker signal can say which seat, and for how long.** A `Seat` domain value, `GenerateSignals` consuming the `AffiliationReader` port, the worker composition wired, **+20 backend tests** |

> ⚡ **This is the far end of a chain the register has been tracking all week.** [C-235](docs/LANE_COORDINATION.md) refused the row for eleven polls because `people/public/` was git's empty blob. [C-237](docs/LANE_COORDINATION.md) found types with no way to read them. [C-238](docs/LANE_COORDINATION.md) found a `Protocol` nothing implemented. **Lane B published the port, then the reader, then the builder — and this cycle Lane A consumed all three.**

**`make runtime-composition`: 0 unexpected missing wiring, four modules subscribed** — the measure that says a capability does not ship complete and do nothing.

### ⛔ Lane C's commit was excluded, and not for a failing gate

**It conflicted on two *generated* `.toml` files** — `coordination.toml` and `queues/lane-a.toml`. ⛔ **QE does not hand-resolve generated files**, and a union merge on a `.toml` is what broke `lane-a.toml` earlier this session.

⚡ **The right repair is the generator, not the merge**: Lane C rebases and re-emits against the new baseline, which is what `infra/coordination.py` exists for. **Lane A was not held for it.**

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4193 backend** *(+20)* · **1548 frontend** · **95.38%** · **398 invariants** · **842 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **107 runs recorded, 99 certified** · `promoted == certified` ✓ · `--audit-main` clean · **sixth consecutive first-attempt certification** |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · smoke **148s** · ✅ **runtime-composition 0 unexpected** |
| **Dependency** | ⚠️ Lane C must rebase and regenerate; Lane B remains a stale ref |
| **Customer Value** | ⚡ **A signal about a departed decision-maker now carries which seat they held and for how long** — the difference between *someone left* and *the person who signs left last month* |
| **Process** | ⚡ **Four coordination items, three lanes, one week, and the chain closed without any lane inventing the other's half** |

---

## 1e · Release summary — 2026-08-07, cycle 102

**Derived from the promoted commit `67fe1a8`.** **Fifty-seven promotions.** ⚡ **A defect Lane A hit by running the command the repository told it to run.**

### What was promoted

| | |
|---|---|
| ⚡ **[B-212](docs/BUGS.md)** *(Lane C)* | **`make up` referenced `infra/.env.prod-local`, which the repository neither shipped nor described.** `docker compose` fails hard on a missing `--env-file` and **its message names neither the file's purpose nor how to make one** |

**The fix is a `prod-local-env` prerequisite** — *"the check costs one `test -f` and replaces a compose error with the two lines that fix it"* — **plus `infra/.env.prod-local.example`, 52 lines, so the file now exists to copy.**

> ⚡ **This is §2's defect exactly**: *the repository itself should always tell the truth.* **A documented command pointing at a file that was never shipped is a repository asserting something untrue of itself**, and **Lane A found it by following the documentation.**

### ⚠️ It changes a gate's prerequisite chain, so QE verified it before depending on it

**`make up` now depends on `prod-local-env`, and `make dr` runs `make up`.** ⛔ **A guard on the path to a gate can stop the gate.** QE ran the target standalone first — `RC=0` — then let `make dr` exercise it for real. **Nothing lost, 5 restart stages.**

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4173 backend** *(+1)* · **1548 frontend** · **95.37%** · **398 invariants** · **840 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **106 runs recorded, 98 certified** · `promoted == certified` ✓ · `--audit-main` clean · first attempt, no aborts |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · ✅ **smoke 148s**, back to the norm after the explicable 201s |
| **Dependency** | ✅ Nothing held. Lane A and Lane B are stale refs, resolved by patch-id |
| **Customer Value** | ⛔ **None directly** — but a developer can now run the documented command on a fresh clone |
| **Process** | ⚡ **A lane hit a defect by trusting the repository, reported it, and another lane fixed it the same day** |

---

## 1e · Release summary — 2026-08-07, cycle 101

**Derived from the promoted commit `a4de1c3`.** **Fifty-six promotions.** ⚡ **A customer-visible screen, and a slow smoke run that explains itself.**

### What was promoted

| | |
|---|---|
| ⚡ **TASK-468** *(Lane A)* | **Organization setup — *honest about what it cannot do yet*.** A settings screen, a new `Locked` component in `components/ui`, **186 lines of component tests and an 86-line Playwright journey** |
| **D-156** *(Lane C)* | *"Workflow 1 is four screens, not three, and C-431 answered itself"* |

**+25 frontend tests · 66 files.** ⚡ **The lane shipped its own journey spec**, which is what [D-114](docs/DECISION_REGISTER.md) asks of it.

### ✅ Smoke 201s, and this one is explicable

**`slowest 1. Build 55s`.** ⛔ **Not [B-141](docs/BUGS.md)'s pattern.** The two unexplained runs were `slowest 14k. Researched account` at 2495s and 23s; **this is `next build` compiling a page and a component that did not exist before.**

> ⚡ **A slow gate with a named, causal reason is a different observation from a slow gate without one** — and `_slowest_stage` exists precisely so the record can tell them apart. **It was added after two outliers that could not be explained afterwards, because the record kept one number.**

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4172 backend** · **1548 frontend** *(+25)* · **95.37%** · **398 invariants** · **840 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **105 runs recorded, 97 certified** · `promoted == certified` ✓ · `--audit-main` clean · first attempt, no aborts |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · smoke **201s, cause named** |
| **Dependency** | ✅ Nothing held; `integration` moved mid-run and was rebased at Closeout, as designed |
| **Customer Value** | ⚡ **A person can open Organization settings** — and the screen says plainly what it cannot do yet rather than pretending |
| **Process** | ⚡ **The planner selected `ALL` Playwright journeys for this change**, and they remain among the ten unrecorded gates — [B-131](docs/BUGS.md), unchanged and still measured every run |

---

## 1e · Release summary — 2026-08-07, cycle 100

**Derived from the promoted commit `ecc2cc3`.** **Fifty-five promotions, and the hundredth cycle.** ⚡ **The cycle where a merge conflict turned out to be two lanes executing the protocol correctly.**

### What was promoted

| | |
|---|---|
| **D-155** *(Lane C)* | **Execution mode: the priority is published, and Workflow 1 has zero implementation.** [TASK-467](docs/BACKLOG.md) now stands above the business workflows until Workflow 1 clears human review |
| **Two decision-queue entries retired** *(Lane C)* | *"both were answered and both still asked"* |

### ⚡ The conflict that was the protocol working

**`BACKLOG.md` conflicted on one row's `Status`, and the two sides said:**

| | |
|---|---|
| **Lane A** | ⏸️ `BLOCKED` — *"⛔ **`READY` is Lane C's to set** (§20e), so this lane records the fact and does not move the state"* |
| **Lane C** | ✅ `READY` — *"Lane A closed the item and explicitly left the state alone… **which is the protocol working, and this is the other half of it**"* |

⚡ **Lane A cleared its own blocker, verified the fix by opening the files on `integration`, and deliberately declined to set `READY` because that authority is not its own. Lane C then set it.** ⛔ **The conflict is an artifact of the two writing at the same time — not of disagreement.**

**QE took Lane C's row, and not by adjudicating**: it is a **strict superset** — the `(Previously …)` chain is one level deeper and wraps Lane A's entire history intact — **and `READY` is Lane C's under §20e.**

> **Third register conflict this week resolved by finding that one side contained the other.** ⚡ **When two lanes are both following the rules, their edits nest rather than compete**, and QE's job is to notice that rather than to choose.

### ✅ Smoke 143s — the fastest of the last six cycles

**184s · 188s · 150s · 143s.** ⛔ **[B-141](docs/BUGS.md) stays open**, but the two slow readings now sit alone against four normal ones, and nothing executable changed across any of them.

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4172 backend** · **1523 frontend** · **95.37%** · **398 invariants** · **840 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **104 runs recorded, 96 certified** · `promoted == certified` ✓ · `--audit-main` clean · first attempt, no aborts |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · ✅ **smoke 143s** |
| **Dependency** | ✅ Every lane level or stale; nothing held |
| **Customer Value** | ⛔ **None directly.** A priority ruling and two register cleanups |
| **Process** | ⚡ **A conflict between two lanes that were both right, and the record says so** |

---

## 1e · Release summary — 2026-08-07, cycle 99

**Derived from the promoted commit `c2aecd3`.** **Fifty-four promotions.** ⚡ **The planner separated two branches by profile, and smoke came back inside its norm.**

### What was promoted

| | |
|---|---|
| **C-238 closed** *(Lane A)* | *"the port has an implementation, and a builder for it"* |
| **The queue corrected** *(Lane C)* | *"D-152, D-153 and D-154 are all on `main`, and the queue stops saying otherwise"* |

### ⚡ The planner separated the two branches, and the difference is the point

**Both branches carried exactly one commit and neither touched `backend/`, `frontend/` or `infra/`.**

| | | |
|---|---|---|
| **Lane A** | `docs/BACKLOG.md`, `docs/LANE_COORDINATION.md` | **profile `documentation` — 2 gates** |
| **Lane C** | `docs/coordination/coordination.toml`, `queues/lane-a.toml` | ⚡ **profile `platform` — 16 gates** |

⛔ **A path-prefix heuristic sees one category here. The planner sees two**, because `docs/coordination/**` is read by `coordination.py --check`, `state-check` and `test_coordination_source.py`, and the rest of `docs/` is not.

### ✅ Smoke returned to 150s

**184s and 188s in the two preceding cycles; 150s here, inside the 149–162s norm.** ⛔ **Two high readings and one normal one is not a resolution** — [B-141](docs/BUGS.md) stays open — but it does say the slow runs were **not** caused by anything promoted, since nothing executable changed between them.

⚡ **What did change is the workstation**: every container was stopped between the last two polls, and QE restored only the cluster certification provisions from. **A quieter machine and a faster smoke is consistent with the contention hypothesis** and is recorded as one more observation, not a conclusion.

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4172 backend** · **1523 frontend** · **95.37%** · **398 invariants** · **840 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **103 runs recorded, 95 certified** · `promoted == certified` ✓ · `--audit-main` clean · first attempt, no aborts |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · ✅ **smoke 150s, back inside the norm** |
| **Dependency** | ✅ Lane A and Lane C both level with `main`; Lane B remains a stale ref |
| **Customer Value** | ⛔ **None directly.** A coordination item closed and a queue corrected |
| **Process** | ⚡ **A poll returned `18 errors` on an unchanged tree and QE reported it as an abort** — every container was down. **Third time this session, and the check before the verdict is now reflex** |

---

## 1e · Release summary — 2026-08-07, cycle 98

**Derived from the promoted commit `6555968`.** **Fifty-three promotions.** ⚡ **The second consecutive cycle the planner named and the poll heuristic would have missed.**

### What was promoted

| | |
|---|---|
| **D-154** *(Lane C)* | *"one file asserts a visual value, and one test is why"* — with [489](docs/architecture/489-legacy-ui-standards-audit.md), the legacy UI standards audit |

### ⚡ Twice now, and the lesson has stuck

**Lane C's single commit touched no `backend/`, `frontend/` or `infra/` path.** By the poll's own wording it was documentation. **The planner classified it `platform`**, because it changes `docs/coordination/coordination.toml` and `queues/lane-a.toml` — **files that `coordination.py --check`, `state-check` and `test_coordination_source.py` all read.**

> ⚡ **QE now asks the planner instead of matching path prefixes.** [D-115](docs/DECISION_REGISTER.md): *"This plan is computed, not chosen. Unknown paths widen it, never narrow it."*

### ⚠️ And a cherry-pick range that was too wide

The first attempt picked from the merge-base and **conflicted on `DECISION_REGISTER.md` against a `D-153` row already integrated.** ⛔ **Two of the three commits in that range were duplicates by patch-id — QE had already measured that and picked the range anyway.**

**Aborted, picked the one genuinely new commit, clean.** ⚡ **The patch-id check is only worth running if its answer is then used**, which is [B-142](docs/BUGS.md)'s lesson — *a comparison that does not gate the next step is decoration* — arriving in a third place.

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4172 backend** · **1523 frontend** · **95.37%** · **398 invariants** · **840 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **102 runs recorded, 94 certified** · `promoted == certified` ✓ · `--audit-main` clean · first attempt, no aborts |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · ⚠️ **smoke 184s**, second consecutive run above the 149–162s norm — [B-141](docs/BUGS.md) |
| **Dependency** | ✅ Lane A and Lane B remain stale refs, resolved by patch-id |
| **Customer Value** | ⛔ **None directly.** Planning and an audit |
| **Process** | ⚡ **The planner named the cycle for the second time running** |

---

## 1e · Release summary — 2026-08-07, cycle 97

**Derived from the promoted commit `7bf7380`.** **Fifty-two promotions.** ⚡ **The cycle QE would have skipped, and the repository's own instrument said otherwise.**

### ⚡ The poll classified the change as documentation. The planner disagreed, and was right

**QE's poll routine looks for executable change under `backend/`, `frontend/`, `infra/`.** Lane C's two commits touched neither — they are `docs/`, and QE was about to report *no cycle warranted*.

**`certification-guard.py --next-cycle` said:**

```
2 executable commit(s)
  Repository impact — 8 path(s)
    platform  docs/coordination/coordination.toml, docs/coordination/queues/lane-a.toml
```

⛔ **`docs/coordination/**` is machine-read.** `infra/coordination.py --check` validates it, `state-check` calls that on every run, and `test_coordination_source.py` tests the generator that writes it. **A change there can break a gate**, which is what *executable* means — **and the directory prefix QE was matching on is a heuristic, not the definition.**

> **The Validation Planner is the definition, and it was built for exactly this** ([D-115](docs/DECISION_REGISTER.md)): *"This plan is computed, not chosen. Unknown paths widen it, never narrow it."*

### What was promoted

| | |
|---|---|
| **D-152 · D-153** *(Lane C)* | **Nine of ten screens are legacy, and the design says token migration rather than rewrite** · **Workflow 1 is Login, and the gap is 3 of 12 elements plus one file of colours** — with [488](docs/architecture/488-workflow-1-login-gap.md) |
| **[B-145](docs/BUGS.md)** *(QE)* | Filed into the cycle that found it |

### ⚠️ [B-145](docs/BUGS.md) — a freshness check that cannot stay green

**`coordination.py --check` fails minutes after the file is published**, and most of the 70 differing lines are elapsed time:

```diff
-blocked_days   = 0.2        +blocked_days   = 0.0
```

**`_blocked_days` computes `datetime.now(utc) - then` at 0.1-day granularity and bakes it into the file.** ⚡ **So it drifts every ~2.4 hours with nothing changing anywhere.**

⛔ **This is [B-134](docs/BUGS.md)'s family through a different door.** That one was the `[meta]` stamp making `--check` *never* pass, fixed by `_content()` excluding it. **This is the body carrying a continuously-varying input, so it cannot *stay* passing** — and `_content()`'s own docstring already names the principle: *"`[meta]` is provenance, not content."* **An elapsed-time metric is the same category.**

**It matters because §20e now says a lane learns what to build from `origin/coordination`.** A check that cries stale every 2.4 hours **trains every lane to ignore the one signal that would tell them the queue really is out of date** — B-134's own warning, in that row's words.

⛔ **Not blocking, and QE did not treat it as one.** `--check` is not a certification gate. **This cycle certified with it red, deliberately and on the record.**

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4172 backend** · **1523 frontend** · **95.37%** · **398 invariants** · **840 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **101 runs recorded, 93 certified** · `promoted == certified` ✓ · `--audit-main` clean · first attempt, no aborts |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · ⚠️ **smoke 188s**, slowest stage *Researched account* at 23s |
| **Dependency** | ✅ Lane A and Lane B are stale refs — **resolved by patch-id, not by counting** |
| **Customer Value** | ⛔ **None directly.** The cycle carried planning and a finding |
| **Process** | ⚡ **The planner overrode QE's own heuristic and the cycle happened because of it** |

---

## 1e · Release summary — 2026-08-07, cycle 96

**Derived from the promoted commit `ba90459`.** **Fifty-one promotions.** ⚡ **A clean cycle — first attempt, no aborts, no lease wait — and the reader two rows had been waiting on.**

### What was promoted

| | |
|---|---|
| ⚡ **M-I** *(Lane B)* | **`who has held a role at a company, and who left`** — the `people` affiliation reader: 102 lines of infrastructure, its composition root, and **276 lines of tests.** ✅ **This is the reader [C-237](docs/LANE_COORDINATION.md) and [TASK-458](docs/BACKLOG.md) were both held on** |
| **D-151 ① · ②** *(Lane C)* | `frontend/` assigned to Lane A, **[C-430](docs/LANE_COORDINATION.md) closed**, three rows released, and the five journeys measured — *"one of them is a single row away"* |

**+10 backend tests · 840 files typed · migration `0042` verified reversible again.**

### ⚡ Lane A looked four commits ahead and was holding nothing

**QE checked rather than counting refs.** Two of its four were duplicates by patch-id; the other two were already represented on `integration` **by content** — `TASK-451` reads `IN VALIDATION` there, and the `TASK-468` claim is present as `ff85253e`, the rebased copy from cycle 95.

> ⛔ **A branch that is "ahead" by ref and level by content is a stale pointer, not held work** — and reporting it as held would have put a lane on the blocked list that was never blocked.

**The same check retired Lane B's branch as stale in cycle 94 and again in 95.** ⚡ **It is now the standard first question of every poll**, because rebasing lanes make ref-counting wrong more often than it is right.

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4172 backend** *(+10)* · **1523 frontend** · **95.37%** · **398 invariants** · **840 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **100 runs recorded, 92 certified** · `promoted == certified` ✓ · `--audit-main` clean · ⚡ **first attempt, no aborts, no lease wait** |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · smoke **149s** |
| **Dependency** | ✅ **Nothing held** — every lane's remaining commits are documentation or already integrated |
| **Customer Value** | ⚡ **A person's employment history is readable across a module boundary** — which is what unblocks Signal Engine reading the People contract |
| **Process** | ✅ **Clean.** The hundredth certification run was recorded this cycle |

---

## 1e · Release summary — 2026-08-07, cycle 95

**Derived from the promoted commit `2894c40`.** **Fifty promotions.** ⚡ **A customer-visible slice, and the first time the promotion audit refused for real.**

### What was promoted

| | |
|---|---|
| ⚡ **TASK-451** *(Lane A)* | **A seller can save a view of their accounts, and a colleague can open it** — the application layer, the interface, and permission-aware listing on top of the aggregate cycle 91 shipped |
| **C-430** *(Lane C)* | *"holds two lanes, not one — Lane A found the far end of its own chain"* |

**+57 backend tests · 837 files typed · migration `0042` verified reversible again.**

### ⚡ The audit refused, and it was right to — [B-407](docs/BUGS.md) firing for the first time

**Immediately after promoting, `--audit-main` reported:**

```
REFUSED — 2 commit(s) reached `main` uncertified:
  · 10aaed2  TASK-451 — a saved view a colleague can open
  · 2894c40  C-430 holds two lanes, not one
```

⛔ **`2894c40` was the commit that had *just been certified*.** The cause is the window [B-407](docs/BUGS.md) documents and marks `WONTFIX`: **`make certify` writes the record into the working tree, QE parks it to promote, and it is committed at Closeout** — so between stage 4 and stage 5, `main`'s tip is certified and **`main`'s own tree does not yet say so.** The audit reads the manifest, found no entry, and correctly refused.

**Restoring the record and re-running gave `88 certified · 743 ancestors · the guarantee holds`.**

> ⚡ **Lane C raised B-407 from a `grep` that returned `0` in that window; QE answered it by measurement and closed it `WONTFIX`. This cycle the instrument itself hit the same window and behaved exactly as the row predicts** — **which is the strongest evidence either of us produced, and neither of us had to argue for it.**

**The second flagged commit is the same cause once removed**: `10aaed2` is an ancestor of `2894c40`, and with no record for the descendant it could not be recognised as an ancestor of a certified commit either.

### ⛔ `integration` moved mid-certification, and the gate caught it

The fast-forward into `integration` **aborted** — a claim commit had landed during the run. ✅ **That is the documented model working**: *"`integration` keeps moving, and that is fine. QE certifies C and promotes C."* Promotion is by SHA to `main`, which was unaffected, and `integration` is rebased onto the promoted commit at Closeout.

### Two register conflicts, resolved without adjudicating between lanes

**In each case one side contained the other**, so nothing had to be chosen:

| | |
|---|---|
| [`LANE_COORDINATION.md`](../docs/LANE_COORDINATION.md) | Lane C had **widened** a `Blocks` field to three tasks; Lane A's named one, with the same ADR note. **A strict superset** — kept it, and preserved Lane A's genuinely new row |
| [`ACTIVE_ASSIGNMENTS.md`](../docs/ACTIVE_ASSIGNMENTS.md) | HEAD carried a Lane B claim Lane A's branch predates; Lane A's commit moves `TASK-451` to `IN VALIDATION`. **Kept HEAD's rows, took Lane A's row** |

### ⚠️ The slice touched frozen platform, and it was checked rather than assumed

The plan flagged a **`security`** impact. The whole `signora_platform/**` diff is **one line** — `SAVED_VIEW = "saved_view"` — which **§20a permits by name**: *"a declarative registration, never an authorization grant."* The five grants are append-only rows in `policy.csv`, and `remove` goes to `owner` only.

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4162 backend** *(+57)* · **1523 frontend** · **95.37%** · **398 invariants** · **837 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **99 runs recorded, 91 certified** · `promoted == certified` ✓ · `--audit-main` clean · ⚠️ **one lease abort, waited 370s, never forced** |
| **Architecture** | Migration `0042` **reversible, verified** · **DR nothing lost** · smoke **156s** · a `Resource` registered without a platform change |
| **Dependency** | ✅ Lane B fully integrated by content; its branch is only a stale ref |
| **Customer Value** | ⚡ **A saved view a colleague can open** — the first half of Saved View reached a person rather than a table |
| **Process** | ✅ **Three gates fired correctly and none was overridden** — the integration fast-forward, the promotion audit, and the lease |

---

## 1e · Release summary — 2026-08-07, cycle 94

**Derived from the promoted commit `d437932`.** **Forty-nine promotions.** ⚡ **The largest cycle in this series — fifteen commits, all three lanes, first attempt — and it began with the repository unable to certify at all.**

### What was promoted

| | |
|---|---|
| ⚡ **[B-144](docs/BUGS.md) fixed** *(Lane C)* | **The fix that unblocked everything.** QE found the hidden input in `premature_releases`; ⛔ **Lane C found it in three functions rather than one** — *"the hidden input had moved up one frame, and it was in three functions rather than one"* |
| ⚡ **TASK-463** *(Lane B)* | **The Action Batch's persistence** — append-only, **no `UPDATE` grant**, migration `0042` with its `tenancy_policy.py` registration in the same change |
| **TASK-202** *(Lane B)* | The Reasoning Engine's public contract — 176 lines, with 266 of contract tests |
| **C-238** *(Lane A)* | *"The port is typed, and nothing implements it"* |
| **484 · 485 · 486** *(Lane C)* | UI conformance, platform readiness, and cross-application experience audits |

**+84 backend tests · +6 Security Invariants · migration `0042` verified reversible to base and back.**

### ⛔ The repository could not certify at the start of this cycle, twice over

**[B-144](docs/BUGS.md) made `main` red** — a certification gate reading the clone, so a lane writing a task id in a commit message changed the answer. **Four polls reported it and stopped.** Lane C's fix is one parameter, applied three times.

**And then the gate could not run at all.** `make certify` provisions its disposable database from a **hardcoded** `localhost:5432`:

```python
ADMIN: Final = "postgresql://signora:signora@localhost:5432/postgres"
_HOST: Final = "localhost:5432"
```

**That is the shared review cluster, and it had been stopped.** QE restored it — *make the documented gate runnable, never make it pass.*

### ⚠️ Which sharpens [B-141](docs/BUGS.md) rather than closing it

**Lane C's [483](docs/architecture/483-environment-isolation-audit.md) concluded the stacks are isolated — three separate PostgreSQL clusters — and that is true.** ⛔ **But certification's own database is created inside the *review* cluster on `5432`, not inside QE's on `5632`.** [`infra/environments.py`](../infra/environments.py) states the consequence itself:

> *"A PostgreSQL **role** is cluster-wide: two suites reaching `ALTER ROLE` collide however many databases they own, **which is what aborted cycle 57.** Per-database separation cannot reach a shared cluster; a separate cluster has separate roles."*

⚡ **So the contention hypothesis for B-141 is stronger than QE recorded, and by a mechanism the repository had already written down.** **Measured, not concluded** — the row stays open.

### ⚡ A poll nearly reported a false regression

The measurement came back `17 errors` instead of the familiar `1 failed`, on an unchanged `main` — **which is precisely B-144's own symptom.** ⛔ **It was `ConnectionRefusedError` on a stopped stack: an abort, not a failure.** Reporting it as a regression would have put a false lead in front of the lane already fixing it. **QE then removed the dependency rather than the symptom**, bringing up its own lane cluster so the poll no longer needs anybody else's.

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4105 backend** *(+84)* · **1523 frontend** · **95.38%** · **398 invariants** *(+6)* · **832 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **97 runs recorded, 90 certified** · `promoted == certified` ✓ · `--audit-main` clean · ⚡ **first attempt, no aborts** |
| **Architecture** | ✅ **Migration `0042` reversible, verified** · **DR nothing lost** · smoke **162s** · a new table with RLS registered in the same change |
| **Dependency** | ✅ **Every branch level with `main`** |
| **Customer Value** | ⚡ **A batch of actions now survives a restart** — proposed, approved, reversible, and append-only by grant rather than by convention |
| **Process** | ✅ **A four-poll block cleared, and both halves of why it took four polls are on the record** |

---

## 1e · Release summary — 2026-08-07, cycle 93

**Derived from the promoted commit `6fdb6cc`.** **Forty-eight promotions.** ⚡ **Eighteen commits held across five polls, released by one word, certified on the first attempt.**

### What was promoted

| | |
|---|---|
| ⚡ **The environment lease is fixed** *([D-146](docs/DECISION_REGISTER.md), [483](docs/architecture/483-environment-isolation-audit.md))* | **`_resource()` read the compose `name:` line with a regex and got back the literal `'${COMPOSE_PROJECT_NAME:-signora-v2}'`** — Docker Compose expands that; the regex did not. **So every clone contended on one key naming no stack, and the `"signora-v2"` fallback was unreachable because the middle term returned a truthy literal.** ✅ **QE verified the fix by executing it: `_resource()` now returns `'signora-v2'`** |
| **TASK-455 · TASK-463 · TASK-479** | The demo environment gains a pointer; a release; a disposal — *"Lane B built the port inside the row that needed it"* |
| **[B-139](docs/BUGS.md) · [B-143](docs/BUGS.md)** | ✅ **Both closed by Lane C** |
| **49 · 50 · 51 renumbered** | ✅ **Three document-number collisions, open for days, are gone** |

**+23 backend tests**, including two new files that did not exist before — `test_environment_exports.py` and `test_environment_lease_key.py`. ⚡ **The lease defect now has a test that would have caught it.**

### ⛔ The cost of the hold, stated because it was real

**Five polls.** The branch reached eighteen commits behind a parametrised case that ran in **0.39 seconds**, and QE reported it every poll without escalating: queue order is the lane's, the row named the fix, and the gate was doing exactly what it exists to do.

> ⚡ **When it moved, it moved cleanly**: `mypy` over 824 files, 37 contracts, 64 passes across the five touched test files, and **certification on the first attempt with no aborts.**

### ⚠️ Lane C raised [B-407](docs/BUGS.md) against QE, and QE answered it by measuring

***"One commit of production code is on `main` without a certification run."*** ⛔ **The conclusion is wrong and the observation was real.** QE checked three ways:

| | |
|---|---|
| ① | **`e64f64fb` is an ancestor of the certified `e932b87d`** — §20e's explicit middle case: *"not a loophole; it is what a fast-forward does"* |
| ② | `--audit-main`: **85 certified · 700 ancestors · 1 Closeout · the guarantee holds** |
| ③ | Their `grep -c → 0` **returns `1` today** |

⚡ **③ is the finding.** A certification record cannot contain its own commit hash, so `certify` writes it to the working tree, QE parks it, promotes, and commits it at Closeout. **Between stage 4 and stage 5 `main`'s tip is certified and `main`'s own tree does not yet say so** — and Lane C polled inside that window.

**`WONTFIX`, because every repair is worse**: recording before promotion certifies a commit that was not promoted; a placeholder is not evidence; and closing the window merges Closeout into promotion, which §20e forbids for the reason it states.

> ⛔ **Their [B-142](docs/BUGS.md) comparison does not hold, and the difference is the whole answer.** **There, a comparison did not gate. Here it gated and passed** — `promoted == certified` was asserted equal before the push, and the audit confirms it after.

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **4021 backend** *(+23)* · **1523 frontend** · **95.34%** · **392 invariants** · **824 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **96 runs recorded, 89 certified** · `promoted == certified` ✓ · `--audit-main` clean · ⚡ **first attempt, no aborts, no lease wait** |
| **Architecture** | Migration `0041` **reversible, verified this cycle** · **DR nothing lost** · smoke **153s** · ✅ **three document-number collisions closed** |
| **Dependency** | ✅ **Every branch level with `main`** — nothing held anywhere |
| **Customer Value** | ⛔ **None directly.** The cycle repaired the instruments the other cycles run on |
| **Process** | ✅ **A lane audited QE, QE measured rather than defended, and both records say what happened** |

---

## 1e · Release summary — 2026-08-07, cycle 92

**Derived from the promoted commit `e932b87`.** **Forty-seven promotions.** ⚡ **A clean cycle — one lane, one slice, first attempt, no aborts.**

### What was promoted

| | |
|---|---|
| ⚡ **TASK-428** *(Lane B)* | **A role change becomes an affiliation** — `people`'s application layer, its public contract widened, and **[C-237](docs/LANE_COORDINATION.md)'s reader**: the row that had *"types to read and no way to read them"* now has the way |

**+11 backend tests · 822 files typed · 37 contracts · migration `0041` verified reversible again.**

### ⛔ Lane C excluded for a fourth consecutive poll — [B-143](docs/BUGS.md)

**The branch is now sixteen commits deep behind a parametrised case that runs in 0.39 seconds.** What is waiting inside it: **TASK-455**, **TASK-463**, **TASK-479's disposal**, the **D-146 lease-key fix**, and **Lane C's own [B-139](docs/BUGS.md) fix.**

**QE checked the three things that normally explain a stall**, because *"accessible is a claim to be tested"*:

| | |
|---|---|
| **Is the row on Lane C's branch?** | ✅ **Yes**, twice |
| **Is the branch stale?** | ❌ **Level with `integration`** |
| **Has the lane disputed it?** | ❌ Its own copy reads **`Current assignee: Lane C`**, **`Status: OPEN`** |

> ⛔ **The finding is visible, current, accepted and unfixed.** **QE is not escalating it** — queue order is the lane's, the row names the fix precisely, and the gate is doing exactly what it exists to do. **It is recorded because four polls is where *"waiting on Lane C"* stops being self-explanatory.**

### ⚡ Two lanes brought evidence to a QE row, and one of them argued against itself

**[B-141](docs/BUGS.md) gained entries from both other lanes this cycle.**

| | |
|---|---|
| **Lane C** | The environment lease keys on an **unexpanded shell variable** — `_resource()` returns the literal `'${COMPOSE_PROJECT_NAME:-signora-v2}'`. **QE verified by executing it rather than reading it.** So every clone contends on a key naming no stack |
| **Lane A** | ⚡ **It restarted the shared `signora-v2` PostgreSQL container while other lanes were active** — *"reported because only this lane saw it"*, and explicitly claiming no causation |

**That is evidence for the hypothesis QE had just called the weaker one, offered by the lane it reflects on.** ⛔ **Neither resolves B-141**, and both narrow it: contention explains the *waiting*, not the *anomalies*.

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **3998 backend** *(+11)* · **1523 frontend** · **95.34%** · **392 invariants** · **822 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **95 runs recorded, 88 certified** · `promoted == certified` ✓ · `--audit-main` clean · ⚡ **first attempt, no aborts, no lease wait** |
| **Architecture** | Migration `0041` **reversible, verified this cycle** · **DR nothing lost** · smoke **149s** |
| **Dependency** | ⚠️ **Lane C holds sixteen commits**, four other rows inside them |
| **Customer Value** | **A person's role change is recorded as an affiliation rather than an overwrite** — the shape [TASK-427](docs/BACKLOG.md) established, now reachable by another module |
| **Process** | ✅ **Clean.** ⚡ **Two lanes volunteered evidence to a register row neither owns** |

---

## 1e · Release summary — 2026-08-07, cycle 91

**Derived from the promoted commit `02fe658`.** **Forty-six promotions.** ⚡ **The largest customer-visible cycle in this series — and the first where a failing gate named its own test.**

### What was promoted

**Eight commits, two lanes, five slices.**

| | |
|---|---|
| ⚡ **TASK-478** *(Lane A)* | **Design System v2, the canonical set** — command palette, drawer, error state, confidence, badge, and the standing model. Built against the design's own nineteen sections, **verified openable before claiming** ([D-137](docs/architecture/adr/)) |
| **TASK-450** *(Lane A)* | **Saved View** — the aggregate, its versioning, migration `0041` with `FORCE ROW LEVEL SECURITY` and `tenancy_policy.py` registration **in the same change that creates the table** |
| **TASK-441** *(Lane A)* | **Opportunity Intelligence** — *"where does everything stand, as a view and not a screen"* |
| **TASK-444** *(Lane A)* | **The catalog learns which rules misfire** — precision per signal type, computed from `DismissalReason` |
| **TASK-457** *(Lane B)* | **`people` publishes a subject** — *"and the file was empty for a day"* |

**+48 backend tests · +75 frontend tests · migration `0041` verified reversible to base and back.**

### ⚡ [B-140](docs/BUGS.md) earned itself one cycle after it was built

Attempt 1 failed, and **for the first time the verdict was followed by the evidence**:

```
NOT CERTIFIED
  · gate 'pytest' failed: 3991 passed

  pytest — last 40 line(s), 592 elided
    …
    FAILED tests/test_claim_agreement.py::TestBacklogClaims::test_every_holding_status_counts[IN VALIDATION]
```

**Cycle 90 spent three attempts and a re-run to learn nothing.** ⚡ **Cycle 91 spent one line.**

### ⚠️ QE's first attribution was wrong, and the reason is worth keeping

QE ran `git switch --detach origin/integration` **while a cherry-pick sequencer was active.** The working tree still carried candidate content, so the test appeared to fail on `integration` too — which would have exonerated the lane that caused it.

> ⛔ **A checkout that did not happen looks exactly like one that did.** **`git worktree add --detach` is the honest instrument**, and it reversed the answer: `7 passed` on `integration`.

### ⛔ Lane C excluded — [B-143](docs/BUGS.md), and it is the third of one shape

| | | |
|---|---|---|
| [B-138](docs/BUGS.md) | cycle 89 | An annotation naming a type behind an `importlib`-loaded module |
| [B-139](docs/BUGS.md) | cycle 90 | `_delivered` made row-scoped; **its test left asserting the old contract** |
| **[B-143](docs/BUGS.md)** | **cycle 91** | **`HOLDING_STATUSES` narrowed; its test left asserting the old contract** |

⚡ **Every change is well-reasoned and documented in the code — `HOLDING_STATUSES` dropping `IN VALIDATION` is `CLAUDE.md` §20e's own rule applied.** **The pattern is not bad thinking. It is that a change and its existing test are moving at different times**, and **each is caught by a gate needing no database** — this one runs in **0.32 seconds** on constructed text.

⚠️ **Lane C's own B-139 fix is on that branch and waits with it.**

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **3987 backend** *(+48)* · **1523 frontend** *(+75)* · **95.33%** · **392 invariants** · **820 files typed** · **37 contracts** · `tsc` and `eslint` clean |
| **Release** | **94 runs recorded, 87 certified** · `promoted == certified` ✓ · `--audit-main` clean · **one lease abort, waited out at 270s, never forced** |
| **Architecture** | ✅ **Migration `0041` reversible, verified this cycle** · **DR nothing lost** · smoke back to **152s** · ✅ **the three document-number collisions are gone** |
| **Dependency** | ⚠️ Lane C holds eight commits including its own fix |
| **Customer Value** | ⚡ **Real, and the most in this series** — a canonical component set, a saved view a seller can keep, where opportunities stand, and which rules misfire |
| **Process** | ✅ **No gate bent.** ⚡ **The instrument built last cycle paid for itself in this one** |

---

## 1e · Release summary — 2026-08-07, cycle 90

**Derived from the promoted commit `dae6417`.** **Forty-five promotions.** ⚡ **Three candidates, and the cycle's real product is that certification can now explain itself.**

### What was promoted

| | |
|---|---|
| ⚡ **TASK-462** *(Lane B)* | **A batch of actions is proposed, approved, and can still be taken back** — 302 lines of domain, 258 of tests, the `action_batch` public contract |
| **[B-140](docs/BUGS.md)** *(QE)* | **A failing gate now prints the last 40 lines of its own output** |

### ⛔ The cycle that could not diagnose itself

**Attempt 2 recorded `pytest — 3928 passed` beside `NOT CERTIFIED`, and nothing else anywhere.** `_run()` captured the output, a regex read a number out of it, and the transcript was dropped. **By the time the verdict printed there was nothing left to read** — in any file, log or record.

**The same command passed twice on re-run**: `make validate` green at `3931 passed`, and certify's exact invocation against a disposable database at `EXIT 0, 3931 passed`.

> **So the cycle held a failure reporting three fewer tests than a passing run of the same command, and it was undiagnosable.** ⚡ **A gate that reports a verdict without the evidence forces the next step to be *"run it again and hope"* — which is how a flake becomes indistinguishable from a defect, and how a real defect gets re-run until it hides.**

**Fixed before re-certifying, deliberately**, so that if it recurred the next run would name it. Eight tests, **mutation-checked twice** — returning early kills four, printing for passing gates kills two. **An absent transcript says so rather than reading as silence.**

### ⚠️ [B-141](docs/BUGS.md) — recorded as a measurement, deliberately not diagnosed

**Two abnormal pytest runs in one cycle**: the undiagnosable `3928`, and a `smoke` gate at **`2652s` against a normal `142–179s`** — **18×**, with `slowest 14d. Change detection 2495s`.

**Both are pytest runs**, and stage `14d` connects to the **shared** stack at `5433` rather than to a disposable database. **Two hypotheses — contention, or something in the suite — and QE chose between them not at all.** Naming a cause on this evidence would be [B-136](docs/BUGS.md)'s mistake in reverse.

⚡ **This is the first outlier where the record names the stage**, which is what `_slowest_stage` was added for after two unexplainable ones. **The row exists so the next occurrence has a predecessor.**

### Lane C excluded — [B-139](docs/BUGS.md)

`C-428` changed `_delivered` from lane-scoped to row-scoped for a good reason, and **left the test asserting the old contract.** The half worth more: **the new implementation never reads `ahead` and answers from `git log` against real refs in the running clone** — so the test does not test the function, and the result varies by workstation. **§2: a hidden input makes the same declared inputs produce different results.**

**QE checked attribution rather than inferring it**: 12 passed on `integration` without C-428, 1 fails with it. **Lane B was not held** — the candidate was rebuilt as `integration` + Lane B alone.

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **3939 backend** *(+32)* · **1448 frontend** · **95.32%** · **392 invariants** · **815 files typed** · **37 contracts** · `tsc` clean |
| **Release** | **92 runs recorded, 86 certified** · `promoted == certified` ✓ · `--audit-main` clean · ⚠️ **two failed attempts, one of them undiagnosable — and that is now fixed** |
| **Architecture** | Migration `0040` **reversible, verified this cycle** · **DR passed — nothing lost** · ⚠️ **smoke 2652s, [B-141](docs/BUGS.md)** |
| **Dependency** | Lane A claimed three rows straight from the coordination source |
| **Customer Value** | ⚡ **A batch of actions can be proposed, approved and taken back** — the first slice of `action_batch`'s domain |
| **Process** | ✅ **No gate bent across three candidates.** ⚡ **The two instruments this cycle needed and lacked were both built inside it** |

---

## 1e · Release summary — 2026-08-07, cycle 89

**Derived from the promoted commit `eb07eb0`.** **Forty-four promotions.** ⚡ **The Coordination subsystem is live, and it took three attempts to get there — every one of them stopped by a gate, and every finding closed by the lane that owned it.**

### What was promoted

**Seventeen commits, one lane.**

| | |
|---|---|
| ⚡ **The Coordination subsystem** *([D-144](docs/DECISION_REGISTER.md), [479](docs/architecture/479-coordination-architecture.md))* | **A lane's poll becomes one fetch and one read.** `origin/coordination` is an **orphan ref** carrying `coordination.toml` and a README — no history, so a lane fetches two files rather than a repository. **It is generated and never edited**: `BACKLOG.md` stays authoritative for scope, `modules.toml` for ownership, `LANE_COORDINATION.md` for dependencies |
| **TASK-419** | **The data-provider registry reaches the worker composition root** — ADR-0404 capability 3, the row Lane A had been blocked on |
| **[B-136](docs/BUGS.md) · [B-134](docs/BUGS.md) · [B-135](docs/BUGS.md) · [B-138](docs/BUGS.md)** | **All four closed by Lane C** |

> **The measurement that made the case, kept on the record:** *"a lane read 14,392 lines across seven files to learn what to build, and none of it arrived until QE integrated."*

### ⛔ Three attempts, three gates, and none of them bent

| Attempt | Stopped by | What it was |
|---|---|---|
| **Cycle 87** | **`smoke`, at Startup** | The worker crash-looped in the production stack — nothing set `SIGNORA_PROVIDERS`, and the guard the slice made reachable refuses simulated adapters outside a local environment |
| **Cycle 89a** | **`mypy --strict`** | One annotation. `coordination` is loaded by `importlib`, so it has no static symbol behind the dot |
| **Cycle 89b** | — | ✅ **CERTIFIED** |

**The second return cost the repository real time**, and it is recorded rather than argued: `origin/coordination` named `TASK-478` as Lane A's `current` while `TASK-478` did not appear in `BACKLOG.md` on `integration` **at all**, so Lane A could not claim it. ⛔ **QE did not weigh that against the gate.** *A gate that bends when the cost is high enough only ever matters in the case where it bends.*

### ⚡ The finding Lane C wrote better than QE did

QE's [B-134](docs/BUGS.md) said the freshness check could never pass. **Lane C's own test docstring said why nobody had noticed:**

> *"I reported the instrument clean the cycle before QE found this. It was — for the minutes between regenerating and committing, which is the only window I ever ran it in. **Running a check only where it passes is not running it.**"*

**And on [B-138](docs/BUGS.md):** *"the constraint I hid behind was narrower than I treated it."* **The backend suite does truncate the demo database and does stay with QE. `mypy --strict` needs no database at all** — it took 40 seconds and named the file, the line and the symbol.

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **3907 backend** *(+12)* · **1448 frontend** — **gated in stage 1** · **95.30%** · **392 invariants** · **811 files typed** · **37 contracts** · `tsc` clean and gated |
| **Release** | **89 runs recorded, 85 certified** · `promoted == certified` ✓ · `--audit-main` clean · ⚠️ **one lease abort, never forced** |
| **Architecture** | Migration `0040` **reversible, verified this cycle** · **DR passed — 5 restart stages, nothing lost** · smoke 24 stages in 142s |
| **Dependency** | ✅ **Lane A is unblocked** — `TASK-478` is now where a lane claims from |
| **Customer Value** | ⛔ **None directly.** The slice removes planning latency between slices, which is throughput rather than product |
| **Process** | ✅ **Three gates held under real cost, and the lane closed all four findings itself** |

---

## 1e · Release summary — 2026-08-07, cycle 87

**Derived from the promoted commit `d66e223`.** **Forty-three promotions.** ⚡ **The cycle that certification failed, and the reason it is worth a summary is what the failure exposed about the instrument that reports it.**

### What was promoted

**One QE slice, three findings, and a blocked branch.**

| | |
|---|---|
| **[B-137](docs/BUGS.md)** *(QE)* | **`state-check` read the last certification *attempt* and called it the last certification.** The manifest records failures deliberately — a failed run is evidence about a commit, and §2 forbids deleting a record of what was true then. So `runs[-1]` is routinely a run that did **not** certify. **It had been correct for eighty-six cycles because every previous cycle ended in a pass** |

> ⛔ **`certification-guard.py` was right throughout and refused the promotion.** Only the advisory view inverted — **and that is the more dangerous half.** A refusal is read once, at the moment it fires. **An advisory is what a cold session reasons from**, and this one would have said a failed commit was certified and merely unpromoted.

**The predicate is now borrowed from the guard, never re-derived.** A second copy of *"did this run certify?"* is a second answer, and only one of them gates a promotion (§2). **Five regression tests on constructed manifests; mutation-checked** — restoring `runs[-1]` fails three.

### ⛔ Lane C's branch was excluded, and the defect is not where it looks

**[B-136](docs/BUGS.md).** TASK-419 wires the data-provider registry into the worker composition root — **ADR-0404 capability 3, and correct.** Its guard refuses simulated adapters outside a local environment — **also correct, and deliberately fail-fast**: a deployed worker serving generated company data would fabricate every score built on it.

**Nothing sets `SIGNORA_PROVIDERS` in `docker-compose.prod.yml`, so the first environment to reach the new code is the one that cannot satisfy it.** The worker crash-loops; `smoke` stops at stage 2 of 24. ⚡ **The fix is one line in the environment. The guard is not the defect and must not be relaxed.**

### ⚡ Three cycles, three defects `make validate` structurally cannot see

| Cycle | Row | Caught by | Why `validate` was blind |
|---|---|---|---|
| 84 | [B-132](docs/BUGS.md) | `mypy --strict` | `pytest` is green — Python does not enforce `Protocol` at runtime |
| 82 | [B-133](docs/BUGS.md) | `next build`'s ESLint, inside `smoke` | An unused import is valid TypeScript |
| **87** | **[B-136](docs/BUGS.md)** | **`smoke`'s Startup, on the production images** | ⚡ **`validate` never composes the production stack** |

**All three are [B-131](docs/BUGS.md) in the concrete**, and the second and third were both named by the Validation Planner for their change.

### Two more rows against the same branch

| | |
|---|---|
| **[B-134](docs/BUGS.md)** 🟠 | **`coordination.py --check` can never pass.** It stamps the running `HEAD` into the file it generates, then compares the whole file including the stamp. **A generated file cannot contain the SHA of the commit that contains it** — so it exits 1 on the commit whose message is *"Regenerate the coordination source"*, and `state-check` calls it on every run. **A guard that cannot pass, which ends where a guard that cannot fail ends** |
| **[B-135](docs/BUGS.md)** 🟡 | **285 lines of new tooling, zero tests.** Nineteen of twenty-three `infra/` tools are covered, and `test_claim_agreement.py` already loads `state-check.py` by path. **One test catches B-134 on its first run** |

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **3895 backend** *(+10)* · **1448 frontend** — **gated in stage 1** · **95.30%** · **392 invariants** · **810 files typed** · **37 contracts** · `tsc` clean and gated |
| **Release** | **88 runs recorded, 84 certified** · `promoted == certified` ✓ · `--audit-main` clean · ⚠️ **one failed certification, which is the gate working** |
| **Architecture** | Migration `0040` **reversible, verified this cycle** · **DR passed — 5 restart stages, nothing lost** · smoke 24 stages in 145s |
| **Dependency** | ⚠️ **Lane A reads 0 claimable** until Lane C's planning rows integrate |
| **Customer Value** | ⛔ **None this cycle.** The slice hardened the instrument that measures the others |
| **Process** | ⚠️ **A certification failed and the pipeline behaved correctly**: the guard refused, the slice was excluded, the owning lane was named, and no other lane was held |

---

## 1e · Release summary — 2026-08-07, cycle 86

**Derived from the promoted commit `9ba145f`.** **Forty-two promotions.** **Declarations that had existed since M5 finally have consumers** — and a new prompt version arrived with zero evaluations, which is the honest state rather than a defect.

### What was promoted

**Six commits, three lanes, and the theme is things finally consuming what they declare.**

| | |
|---|---|
| **TASK-901 slice 2** *(Lane A)* | **`signal_engine` consumes what it has declared since M5** |
| **TASK-901 slice 3** *(Lane A)* | `buying_score_engine` consumes what it declares |
| **TASK-202** *(Lane B)* | **`reasoning@2`**, *"and why the credential was never sufficient"* |
| **D-139 · D-140** *(Lane C)* | Both self-caught — *"the test failed twice on the day it was written, and both were mine"*, and *"the protocol's first act was to catch two of my own conclusions"* |
| **410 corrected** *(Lane C)* | *"The eighteen never existed, and 410 said they did"* |

> **A declared subscription with no consumer is the shape [B-131](docs/BUGS.md) is about, one layer down**: the declaration was true, nothing acted on it, and no gate could tell the difference. **Slices 2 and 3 close it for two modules**, and `infra/runtime-composition.py` — itself one of the ten unrecorded gates — is what proves it.

### ⚠️ `reasoning@2` exists and is **not released**, which is the honest state

**QE checked rather than assumed**, because `prompt-evaluation` has appeared in every shortfall this session on account of `reasoning@1`:

```
reasoning@1 : 4 evaluations · released: False
reasoning@2 : 0 evaluations · released: False
```

**A new version inherits the limitation rather than resolving it.** Under [ADR-0028](docs/architecture/adr/0028-model-runtime-by-environment.md) a prompt is usable only with the exact `(model, dataset)` pairs it has passed — **and `@2` has passed none.**

> **This is not a defect and not a regression.** `reasoning@1` has no released model on this hardware because `granite3.3:2b` refuses under protocol 2 and `llama3.1:8b` is unmeasurable here. **`@2` starting empty is what a new version looks like**; the standing limitation is unchanged, and **`prompt-evaluation` will keep appearing in the shortfall until a real model measures one of them.**

### The cheap-gates order picked up a new file type

**The candidate added `prompts/manifest.json`.** QE parsed it alongside the TOML before validation started — **not because a rule said to, but because the allowlist rewrite made "is this structured?" the first question about any conflicted or new file.** It parsed; nothing was found; the check cost a second.

### Repository Health — six dimensions

| | |
|---|---|
| **Technical** | **3885 backend** *(+6)* · **1448 frontend** — **gated in stage 1** · **95.30%** · **392 invariants** · **809 files typed** · **37 contracts** · `tsc` clean and gated |
| **Release** | **86 certification runs recorded, 83 certified** · `promoted == certified` ✓ · `--audit-main` clean · **first attempt, no aborts** |
| **Architecture** | Reachability 0 doorless · migration `0040` **reversible, verified this cycle** · **a new bounded context, with its ADR, its ownership row, its RLS and its invariants all present** · event catalog 1 known drift |
| **Dependency** | 69 items, 31 closed |
| **Customer Value** | ⚠️ **Foundational.** Two pipeline modules now consume subscriptions they had declared since M5 |
| **Process** | ✅ **Clean — first attempt, no conflicts in code, no aborts.** ⚠️ **`reasoning@2` ships unreleased with zero evaluations**, which is the correct state for a new version and leaves `prompt-evaluation`'s shortfall exactly where it was |

### Repository Health Trend

| | Five days ago | Today |
|---|---|---|
| **Structural checks** | 3 | **12, and stopping** |
| **Unexplained variance** | 3 events | **0** |
| **Process failure modes** | 2 open | **0 — both guarded** |
| **Smoke duration** | unexplained 104–4830s | **129–186s, and diagnosable** |
| **Gates with a hidden input** | unknown | **2 found, 2 fixed** — [B-106](docs/BUGS.md) the shell's database, [B-112](docs/BUGS.md) the local ref's position |
| **Runbook steps that cannot run as written** | unmeasured | **1 found, 1 fixed** — [B-114](docs/BUGS.md); it had been passing on memory |
| **Steps to review the product** | 6, across two terminals | **1** — `make review` |
| **Work in one physical location** | unmeasured | **27 files, measured and surfaced** — `make unsaved` |
| **Review vs certification** | mutually exclusive | **concurrent, proven** — 3000/8000 vs 3100/8100 |
| **Lost certification attempts** | invisible | **counted** — 13 started, 12 verdicts, 1 abort |


## 2 · Milestone progress

**Every active milestone names its owner, its execution phase, and what it is waiting on.** *"In Progress"* is not a status.

| Milestone | Status | Phase | Owner | Module | Promoted? | Blocked by / next action |
|---|---|---|---|---|---|---|
| **M12.3** Evidence and actions | 🔵 Active | **On Main** | **Lane A** | Product Surface | ✅ **PS-01…PS-08 promoted** | D20 hierarchy remains |
| **M2.1** Provider Platform *(re-opened)* | ✅ Complete | **On Main** | — | `provider_platform` | ✅ **PP-01…PP-06 promoted** | — |
| **M13** Integrations | 🔵 Active | **Backend + UI** | **Lane B** | `integrations` | **S01–S09 on `main`** | 🔴 **[C-025](docs/LANE_COORDINATION.md)** — no tier may run the OAuth flow |
| **M7** Timeline | 🟠 **Implementation waiting** | **Integration** | **Lane B** *(built)* → **Lane A** *(route)* | `timeline` | **S01–S04a on `main`** | 🔴 **[C-024](docs/LANE_COORDINATION.md)** — the feed is mounted nowhere |
| **M14a** Notifications | 🔵 Active | **Discovery** | **Lane B** | — | No | Scope, then implementation |
| **M9.5** Evidence Citation Protocol | 🟠 Open | **Implementation waiting** | **Product owner** | `ai_platform` | Steps A–D only | Step F, the oldest outstanding commitment |
| **M12.5** Commercial Profile | ✅ Complete | On main | — | `commercial_profile` | ✅ | — |
| **M12.4** Research on demand | ✅ Complete | On main | — | `ai_research_engine` | ✅ | — |
| **M12.1 · M12.1.5 · M12.2** | ✅ Complete | On main | — | Product Surface | ✅ | — |
| **M0 → M10** Foundation and pipeline | ✅ Complete | On main | — | 13 modules | ✅ | Ten pipeline stages, frozen behind them |
| **M11** Recommendation Engine | 🟣 Deferred | — | **Product owner** | — | No | Resumes on a product trigger |
| **M14b · M14.5 · M15** | ⏳ Queued | — | **Product owner** | — | No | Not scoped |
| — | 🎯 | **General Availability** | | | | |

**Legend — phase:** Discovery · Architecture · Planning · Backend Implementation · Frontend Implementation · UI/UX · Integration · In Validation · Certified · On Main · Implementation Waiting · Blocked · Deferred · Completed.

> **Two milestones are "implementation waiting" rather than blocked, and the distinction matters.** M7's code is written, tested and promoted; it waits on a **decision**, not on engineering. M9.5 has waited longest of anything on this page.

**Two foundations are frozen** and consumed rather than modified: `signora_platform/` (§20a) and the frontend foundation (§20c). **`ai_platform/` is frozen as of M10's close (2026-07-31)** — deliberately not after M9, because a port that had only served a single-call workload had never been asked for tool use or resumability ([28-ai-platform.md](docs/architecture/28-ai-platform.md), Condition 2).

---

## 3 · Task progress

### ✅ M9 — complete, T122–T130

| Task | Delivered |
|---|---|
| T122 | Module scaffold · graph node · four import-linter contracts |
| T123 | `ReasonedOutput` — the model's three fields, premise breadth as a **type invariant** |
| T124 | `SupportBasis` / `SupportLevel` — derived support introducing **no new threshold** |
| T125 | `TemporalExplanation` — why now · why not earlier · what changed · freshness |
| T126 | Signal catalog extension — `limitations`, `suggested_validation` |
| T127 | `DecisionPackage` + `Reason` — fifteen parts, `answers()` as executable acceptance |
| T128 | `reasoning@1` · rubric extension · **release earned** |
| T129 | Migration `0017` — `ai_reasoning`, forced RLS, no `UPDATE` grant |
| T130 | Model · repository · context adapter · composition root · event · smoke stage 14j |

### ✅ M10 — complete, T131–T138 · **Internal Research** *(ruled 2026-07-31)*

| Task | Delivered |
|---|---|
| T131 | Module scaffold · graph node · four import-linter contracts (25 → 29) · six invariants |
| T132 | `EpistemicOrigin` · `ResearchTask` · `ResearchFinding` · `ResearchSynthesis` — three origins, three identity disciplines |
| T133 | Migration `0018` — **three tables because there are three data categories**; forced RLS, no `UPDATE` grant, tenancy registration |
| T134 | Internal retrieval — `ResearchFactSource` over `opportunity_engine.public`; business events and dissent, the two things M8's assembler omits |
| T135 | The planner — a closed derivation catalog, steps that cannot carry a conclusion, and **stopping as a legal answer** |
| T136 | The orchestrator — three deterministic derivations, type↔rule pairing checked at import, and **no counter, no timeout** *(see R-09 below)* |
| T137 | `research_planning@1` — prompt, M10's own golden dataset, evaluation entry point, and **release EARNED** on `llama3.1:8b` after eight consecutive passing runs |
| T138 | The lifecycle closed — synthesis, persistence, `ai_research.completed`, composition root, smoke stage 14k. **`research_synthesis@1` REFUSED**, and R-09 answered by measurement |

**`research_synthesis@1`'s refusal is what forced M9.5.** It was the third prompt blocked by the citation protocol defect, and the milestone stopped rather than tuning around it.

**The scope ruling landed before T132** and narrowed the milestone materially: research explores, compares and synthesises knowledge Signora already owns, and reaches no external source. See [33-ai-research-engine-scope.md](docs/architecture/33-ai-research-engine-scope.md) for the analysis and the ruling it records.

### 🟠 M9.5 — Evidence Citation Protocol *(ADR-0031, unplanned, **not closed**)*

| Step | Delivered |
|---|---|
| A | Three refusals recorded — the ADR's evidence base existed only as prose until this step |
| B | The **Prompt Rendering Protocol** made a first-class concept; every evaluation records it, every release is bound to it |
| C | Protocol **2** — the citation presented as a copyable unit; three releases withdrew themselves by derivation |
| D | `research_planning@2` and `research_synthesis@2` — the workaround deleted, both **RELEASED** |
| **F** | 🟠 **Incomplete.** `explanation_narration@1` re-released; **`reasoning@1` refused on every available model** |

### ✅ M12.1 — complete

| Step | Delivered |
|---|---|
| 1–2 | `attention_list` — the first workspace-wide read path; plural buying-score read; identity-keyed cursor |
| 3 | `GET /workspaces/{id}/accounts` — router, schemas, authorization, 20 full-stack tests |
| 5 | `/opportunities` — the first business screen, composed from the frozen design system |
| 6 | ⏳ Performance review — deferred to M12.3, where the row gains an affordance worth measuring |

### 🔵 M12.2 — Account Identity and the score breakdown shipped

| Delivered | |
|---|---|
| **`AccountIdentity`** | A read model, not a string. `Entity` stores no name — naming an account is the truth-resolution the graph declined to make, so it happens once, at read time, in `select_name` |
| **`GET …/account-identities`** | Batched; a page costs one request. Returns the name **and** whether sources agreed |
| **`EntityName`** | The canonical way Signora renders a company. Agreement is invisible; **disputed names are marked** |
| **`GET …/accounts/{id}/score`** | The score **with its full ledger** — every business event that contributed, what each added, and why the ones that added nothing added nothing |
| **`/opportunities/[accountId]`** | The account brief. `68 of 120 points` beside the number: a customer checks the score with a division rather than trusting it |
| **`GET …/accounts/{id}/opportunity`** | What Signora committed to, and what has happened since — **the movement the list structurally cannot show**, because the list only knows about today |
| **`GET …/accounts/{id}/narration`** | The grounded explanation, statement by statement, each with the evidence it rests on and the model and prompt that wrote it |
| **Tests** | 20 resolver · 7 identity endpoint · 14 score endpoint · 13 commitment endpoint · 44 component · 3 Security Invariants |
| ⏳ **Next** | **M12.3** — Review 1's three high findings and the citation gap are one coherent slice. F-11 still needs a ruling |
| 🚫 **Deferred** | **The Decision Package panel.** `reasoning@1` has no released model; building UI around an unavailable capability would ship a panel that cannot be filled (§7) |

### 🔵 M12.1.5 — Playground v2, inserted 2026-07-31

A demo environment worth reviewing a product against. Requested by the product owner after M12.2's brief showed that **the dataset, not the architecture, had become the constraint** (D17).

| Delivered | |
|---|---|
| **`playground@2`** | Twelve recognisable companies, twelve **invented** business situations, spanning five months. `playground@1` is superseded, retained and unedited |
| **The epoch belongs to the runner** | A scenario declares offsets and no date; the seeder anchors it relative to today. Asserted by a test, because a date baked into the narrative is what made v1 demonstrate seven-month-old evidence |
| **Two scoring passes** | Opportunities qualify against scores as they stood five weeks ago; the scheduled sweep last ran three days ago. **Current, cooling and stale all occur and none is declared** |
| **Three unreachable capabilities fixed** | See §5 — each was complete in every layer except the one that had to supply the evidence |
| **Product review** | Recorded as D19 and D20 in [38-product-design-principles.md](docs/architecture/38-product-design-principles.md) |

### 🔵 M12.5 — Commercial Profile, slice 1: the product catalog

**The fourteenth module, and the first with no upstream dependency.** Signora had thirteen modules that process companies and nothing that said *which* companies — `RunProviderSync` has taken a `subject` since M2.1 and nothing has ever supplied one. Ratified in [ADR-0035](docs/architecture/adr/0035-commercial-profile.md).

| Delivered | |
|---|---|
| **`commercial_profile`** | Records what a customer declares. **It computes nothing, resolves nothing, and calls no provider** — which is what lets it sit upstream of a ten-stage pipeline without knowing the pipeline exists. Two import-linter contracts enforce it (29 → 31) |
| **`ProductCatalog`** | Versioned, immutable, superseded — the `signal_profile` discipline. **A product's identity outlives the catalog containing it**, so everything declared later can cite one and still resolve twelve revisions on |
| **`GET`/`PUT …/products`** | The catalog is saved **whole**, because it is the versioned unit. `expected_version` turns a colleague's concurrent save into a **409 a person can act on** rather than an overwrite neither of them sees. Client-chosen product ids make the `PUT` idempotent |
| **Migration `0019`** | Forced RLS, no `UPDATE` grant. **Currency is `MAX(version)`, not `supersedes IS NULL`** — see the finding below |
| **`/settings/products`** | The first screen where a customer tells Signora something. Already owner-guarded by `GUARDED_ROUTES`; the server refuses a member's write independently (403, asserted) |
| **Tests** | 17 domain · 16 endpoint · 14 component · 2 new Security Invariant registrations |

**Two architectural findings, both from building it.**

**`signal_profile`'s supersession direction is inverted.** The new row carries `supersedes = <old id>` and `current()` selects `WHERE supersedes IS NULL` — which is the **first** version, permanently. It is latent only because nothing has ever written a second profile, and **it would become reachable the moment the signal profile gets a write API**, which is slice 2/4 territory. Not fixed here: different module, and the fix wants its own change. `product_catalog` deliberately reads `MAX(version)` instead.

**The Security Invariants refused my first migration, and were right.** I withheld `DELETE` to protect the audit history. *Erasability is a property of the tenancy model, not of what a row means* — a table the app role cannot delete from is a workspace that cannot be erased. Immutability is an **application** concern and is enforced where it belongs: no `UPDATE` grant, and a repository offering no delete method.

**Deliberately not built:** no event (nothing consumes a declaration until slice 5) · no `public/` contract (the package exists and is empty, so the first consumer arrives through it) · no ICP matching, no discovery, no provider integration.

### 🔵 M12.3 — evidence and actions

**The milestone's goal, set by the product owner:** reduce uncertainty *after* an account has been selected, and begin answering **"what should I do?"** — with no Recommendation Engine, no invented AI, and only deterministic information the platform already holds.

| Delivered | |
|---|---|
| **`GET …/accounts/{id}/validation`** | Per live hypothesis: what it proposes, **what it does not prove**, and what to confirm before acting. Owned by the Signal Engine |
| **"Before you act"** | The checks open; the limitations one disclosure away, in the accessibility tree either way. No checkbox — nothing owns per-user state, and a control that forgets is worse than none |
| **The source** | `limitations` and `suggested_validation` have been in `signals@1.json` since **M5A** and had never been displayed. No model, no new table, no new module |
| **Tests** | 9 endpoint · 13 component |
| **`GET …/business-events/{id}`** | Where a citation ends: the event, its readings, and **which providers reported it**. The only content on the brief Signora did not write |
| **The evidence drawer** | A ledger line opens it. The affordance was withheld for two slices *because it had nowhere to go* |
| **Tests** | 8 endpoint · 5 component |
| **`POST …/opportunities/{id}/states`** | **The first write in the product.** A seller takes an account on, dismisses it, or records an outcome — each with a sentence, each naming who decided. `actor_id` is not on the request contract at all |
| **The decision controls** | Beside the stage line, so workflow lives in one place on the screen. The legal moves arrive from the domain via `allowed_next`; the client reimplements no rule and the server refuses anything else regardless |
| **A closed brief survives** (**D27**) | M12.2 deferred *"what should a closed opportunity's brief say"* to this milestone. It keeps it — otherwise a dismissal would delete the seller's own words and make a legal reopening unreachable |
| **Tests** | 24 endpoint · 17 component · 1 new Security Invariant |
| **`GET …/signal-catalog`** | The hypothesis vocabulary — **the one place a signal type has a name.** Nine types, versioned, reviewed like code, in the repository since M5A |
| **The list says what is happening** | The *why now* column carried `ScoreTrigger` and produced **two** distinct values across twelve real accounts. It now names the leading hypothesis and produces **six**. Closes **R1-01**, closes **R1-02** for free, halves the invisible ties of **R1-05** |
| **`ContributionLedger.leading()`** | *Which hypothesis most explains this number* is a question for the ledger — the module that ranks accounts is forbidden from reaching the one that forms hypotheses, and ties break on the event id rather than on storage order |
| **Tests** | 12 endpoint · 5 component · 4 ledger unit |
| **Sign-in methods** (**ADR-0033**) | Email + password alongside Google and Microsoft. **The method is configuration; the authenticated identity is invariant** — the JWT carries no record of how anybody signed in, so every future method is free downstream. Register, verify, sign in, sign out, reset: all real, none bypassed |
| **Two dormant defects, each hiding the other** | Better Auth's tables had **never been created** by anything in the repository, and the observability hook broke every *completed* auth request. Neither could be seen, because no authentication request had ever finished. **Sign-in had not worked on a fresh clone by any method** |
| **Tests** | 15 auth-method unit · 3 JWT-contract · 5 e2e journey · design tokens extended to `app/(auth)` |
| **The first run** | Being a new customer for ninety seconds found **three defects in a chain, each concealing the next** — the two tiers had never agreed on what a user id *is* (every real API call would have 401'd), the seeder looked for users in the wrong schema and printed a false statement, and a signed-in user with no workspace saw a heading and blank space |
| **Tests** | 2 id-contract · 4 page-level first-run regression · 4 empty-state |
| **The information architecture** (**D38**) | Reviewed from first principles and approved. **Six navigation entries became two.** Companies, Signals and Timeline were four of thirteen pipeline modules with a menu item each — a data model rendered as navigation, and none of them a customer journey. `/` is now **Attention**, the ranked list: a seller's first screen is their morning's work rather than a placeholder promising an integration a milestone away. **D1** is settled with it, after two deferrals |
| **A reviewer reaches the product in one command** | `make demo` brings up the stack, migrates the schema, creates Better Auth's tables, creates **four sign-in accounts through Better Auth's own sign-up and verification routes**, and seeds twelve accounts. `docs/RUNNING.md` is the single source of truth for setup, credentials and troubleshooting |
| **Tests** | navigation invariant rewritten · 4 first-run regression · 4 empty-state |
| **D20, evaluated and closed** (**D39**) | Every option measured against the real twelve before anything was written. **Grouping produces six groups for twelve rows, three of them holding a single row** — a feature of a long list, and D6's trigger has not fired. **Pure score ordering stays**, and D20's premise is rejected: in a ranked list, position *is* the judgement, and the complaint was written before rows said anything |
| **The list knows what you are working** (**D40**) | J4 shipped *"I'm working this"* and the list rendered nothing with it — `owner_id` had been on the wire since M12.1, unused. Rows now read *Yours* / *Taken* / *Being worked*, and **the same list reads differently to each person**. No filter and no reordering: both are volume features |
| **Tests** | 5 ownership component tests |
| **The morning is a sequence** (**D41**) | Walking the whole journey found where momentum stopped: the brief had **one exit and it pointed backwards**, so twelve accounts cost **twenty-four navigations** and every return scrolled the list to row 1. The brief now names the next account, shows the position, and answers `j`/`k`. **No new request** — it reads the same cached list the attention page holds, so *next* means *next most pressing* |
| **Tests** | 11 sequence component tests |
| **Every citation opens** (**D42**) | *"3 facts"* was a count for two milestones because there was nowhere for it to go. It now opens **exactly what the model was given** — the summaries and figures that went into the prompt. **No new endpoint:** the facts are re-derived through the same pure assembler that produced them, because storing a copy of a reproducible truth is the duplicated-truth defect arriving through a presentation layer. R10-04's framing (*three resolvers*) was rejected first: all three cited kinds are things Signora wrote, and a citation may not end at another of its own summaries |
| **And the explanation says whether it still holds** | `ai_narration.evidence_digest` has been stored since M8 and **read by nothing**. Comparing it against the re-derived set is what makes re-derivation honest — without it the screen would present today's facts as the ones the model saw. A changed digest is stated, never hidden, and **never repaired by editing the narration** |
| **Tests** | 6 endpoint · 7 component |
| **The customer's own vocabulary** (**ADR-0034**) | *Workspace* is Signora's word for a tenant and had become **the word the product said to a customer** — because nothing had ever written down that it should not. Every new account read *"You are not in a workspace yet"*; the new-organization dialog explained **RLS to a salesperson**; the header's accessible name said *workspace*, so a screen-reader user was the only customer told the internal term. **And a password sign-in redirected to `/workspaces`, a route that has never existed** — three slices of every password sign-in landing on the not-found page, caught by a vocabulary audit rather than by 2312 tests |
| **Enforced, not documented** | `vocabulary.test.tsx` scans user-visible strings for internal terms, forbids a route path named after one, and asserts **every `router.push` resolves to a page that exists**. It found a leak the manual audit had missed on its first run. **Nothing renamed inward**: `workspace_id`, RLS, the API path and the JWT claim all stay, because *workspace* is precise about isolation in a way *organization* is not |
| **Tests** | 4 vocabulary invariants · 5 empty-state assertions reworded, none weakened |
| **Second Consistency Pass** | *Organization* appears **nowhere in the repository** — the intent lived in discussion, never reached a document, so the product built the only word it had. **The ICP pattern in a different register.** Three more capabilities found entering through a Demo Scenario rather than a Scope entry: **deprioritization intelligence** (a named differentiator in zero milestones) and **the RevOps surface** (Job 7 — the economic buyer has no screen in the product surface design). **Four confirmed instances now**, which makes it the dominant way capability leaves this roadmap |
| **Vision & Roadmap Consistency Review** | Commissioned at this boundary. **Nine of twenty lifecycle stages implemented, five more built and unreachable.** ICP confirmed forgotten — deferred out of M5A, M5B and M6, named in three architecture documents, never given a milestone. **Target account selection is worse:** written into M2.1's demo scenario, never into its scope, and recorded as missing for the first time here. Two documents making provider configuration a customer responsibility corrected. Recorded in [PRODUCT_ROADMAP.md](PRODUCT_ROADMAP.md) |
| ⏳ **Next** | **R9-03** — a contraction risk still reads like a small opportunity; posture on the row, using the pipeline's own word. **Wants a seller's ruling.** Then M12.3 closes: certification re-cut and full gates |

> **🟠 It ships to the Playground and not to a customer until F-3 closes.** The catalog's guidance is *engineering-authored pending domain review*, and *"ask on a first call which division the investment sits in"* is advice a real seller will act on. Good content is not the same as signed content.

### ⏳ Next tasks

| Task | Scope |
|---|---|
| M12.3 | **The list slice** — R1-01 (*why now* repeats 11 of 12), R1-02 (trigger and evidence state contradict), R1-05 (invisible tiebreak), D20/R1-07 (a 50 and a 1 render identically). One coherent change about *which* account you pick |
| M12.3 | **R4-04** — a dismissed account is unreachable once you navigate away. A *closed and dismissed* filter, which is the same list slice |
| M12.2 | The Decision Package panel, **on the trigger `reasoning@1` earns a release** and not before |
| M12.4 | Research on demand — dispatch, status, and the brief. The one genuinely new backend capability the product surface still needs |
| **M12.5** | **Commercial Profile**, slices 2–5 — ICP declaration · buying committee templates · business priorities · target account list. The last of these publishes `target_accounts_changed` and finally gives Provider Platform the `subject` it has taken since M2.1 |
| unassigned | **D32** — the other half of D23. Naming a person needs a cross-tier profile contract and belongs in an ADR, not a slice |

**Deterministic-first ordering, unchanged from M8 and M9:** storage before retrieval, retrieval before orchestration, generation and evaluation last. **Embeddings, pgvector, external retrieval and provider re-query are deferred**, each with a stated trigger.

---

### The standing rule for every M12.x slice

> **No frontend screen is complete until a human has reviewed it in the demo environment.**
>
> **And every user-visible feature gets a recorded product review before the next one starts** — as the five people who would use it and as the designers whose products set the bar. Findings land in [39-product-review-findings.md](docs/architecture/39-product-review-findings.md) with a priority and a milestone, and are implemented immediately **only** when they fix a correctness bug, materially reduce cognitive load, or are essential to the current milestone.

Set by the product owner on 2026-08-01. Gates prove a screen is correct; only a person opening it can say whether it is *persuasive*, and every finding in [38-product-design-principles.md](docs/architecture/38-product-design-principles.md) from D9 onward came from looking rather than from a test.

---

## 4 · Repository health

> **Not transcribed. Cited.** Every figure below comes from
> [`certification/manifest.json`](certification/manifest.json) — written by
> `make certify`, never by hand (ADR-0032). A number in this table that nobody
> measured is the defect the certification record exists to remove, so this
> section names its evidence and stops.

**Latest certification — [`d392ed5326da`](certification/reports/d392ed5326da.md) · 2026-08-04 · ✅ CERTIFIED**

**Certified commit `d392ed5` · promoted commit `d392ed5`.** Identical, checked by `infra/certification-guard.py` before the fast-forward.

| Gate | Recorded |
|---|---|
| **pytest** | **3256 passed** |
| **coverage** | **95.5%** *(floor 95%)* |
| **Security Invariants** | **379 invariants**, each proven to fail when its guarantee is removed |
| **import-linter** | **34 kept, 0 broken** |
| **MyPy** | **strict, clean over 707 files** |
| **`make smoke`** | **24 stages in 135s, slowest 2. Startup 20s** |
| **Scenario — `baseline@1` research lifecycle** | **179 assertions** |

**Conditions the certification is bound to:** rendering protocol **v2** · migration head **`0030`** · scenario set `0cf6b2c581e4` · working tree clean.

**Also verified this cycle, and not yet certification gates:** frontend 701 tests · **migration reversibility to base and back** · **`make dr`** — every component restarted, nothing lost, 360 invariants re-run · **runtime composition**, 2 of 2 expected, 0 unexpected.

> ⚠️ **Recorded when it happened, and it did not recur: a cycle once needed three certification attempts and the manifest recorded only the third.** A failed run leaves the tree dirty and is correctly discarded, so **the manifest structurally cannot measure stability** — see [`RELEASE_ENGINEERING.md`](docs/RELEASE_ENGINEERING.md) §1. The *Certification run success rate* below is an artefact of that discard, not a measurement, and **RE-01 exists to fix it.**

| Indicator | Value | Target |
|---|---|---|
| **Frontend tests** | **719 passing**, 0 failing, 0 skipped | 0 skipped |
| **Modules** | **15 implemented** · **46** numbered architecture documents · **40** ADRs | — |
| **Module count, reconciled** | [`04-modules.md`](docs/architecture/04-modules.md) ratifies **13 core + 1 platform = 14**; `integrations` and `timeline` were added since under [ADR-0025](docs/architecture/adr/0025-module-boundary-evolution.md). **15 directories is the measured figure**; [README](README.md) still says *fourteen* | reconcile |
| **Migrations** | **`0000`–`0030`**, additive and reversible — verified to base and back this cycle | — |
| **Architecture drift** | **0** — no ratified ADR reversed | trending to 0 |
| **Open defects** | **38 rows: 14 `OPEN`** · **17 `FIXED` awaiting verification** · **5 `VERIFIED`** · 1 `WONTFIX` · **0 unresolved 🔴** ([docs/BUGS.md](docs/BUGS.md)) | 0 🔴 |
| **Coordination items** | **55** — **25 closed**, the rest open or waiting ([docs/LANE_COORDINATION.md](docs/LANE_COORDINATION.md)) | shrinking |

> ⚠️ **Every figure in the two tables above was stale until this audit, and two were stale by two cycles.** §4 named `e5a266d17203` while `main` had been certified twice since; the defect and coordination counts were less than half their real values. **Nothing detected it** — `state-check` verifies that §1 names a reachable commit and never reads §4. Recorded as the reason the audit happened at all, and as a gap: **the dashboard has one checked section and eight unchecked ones.**

> **A certification expires by derivation, not by decision.** Change the rendering protocol, re-release a prompt, add a migration or edit a scenario, and the recorded run stops describing the repository — `is_certified` reads false and the report says *awaiting re-certification*. Nothing is edited, and **nothing can be marked certified by hand**.

> **What the gates caught this cycle, and nothing else did.** `make smoke` had not run since 2026-07-31 and its first honest run failed at startup: the worker and relay could not start from a production image ([B-013](docs/BUGS.md)). **2325 passing tests did not see it, because only `make smoke` builds the production images.** Certification also measured 2223/94.36% when pointed at the shared default database and 2325/95.59% against the lane's own — the same commit, two answers. **A gate pointed at the wrong database is not a gate**, which is now written into the runbook.

*Frontend tests and migration reversibility are not yet certification gates — they are verified per milestone and remain transcribed here until `make certify` measures them.*

**Every gate runs locally.** `make certify` runs them in one pass and records the result; each remains individually runnable. A gate moving from CI to local did not make it optional — it made the local run the only run, and therefore the one that decides.

**Caveat worth restating:** these numbers describe a system with zero production traffic. They are evidence of discipline, not of field reliability — which is why every certification report ends with that sentence.

---

### Engineering KPIs

**How the process is running — never whether the software is correct.** A short certification is not a good one; the gates decide that, and these describe throughput. Reading them the other way round is how a team starts optimising the measurement.

| Indicator | Value |
|---|---|
| **Certification** | |
| Certification cycles | 41 |
| Certified | 29 of 30 |
| Mean time to certify (last 5) | 13.3 min |
| Mean smoke duration | 327.9 s |
| Mean certify → Ready (last 5) | 6.0 min |
| **Release flow** | |
| Certification run success rate | 97% (29 of 30 runs) |
| ↳ excludes | rejected candidates, and every failed or aborted attempt |
| ↳ see instead | Pipeline stability below — measured from the attempt log |
| Commits per release | mean 7.6, median 4, range 1–49 |
| Mean candidate age | 153.3 min  — oldest commit → certified |
| Release frequency | 0.39 releases/hour over 74h |
| **Pipeline stability** | |
| Attempts | 9 |
| ↳ certified | 8 |
| ↳ failed | 1 |
| ↳ aborted | 0  (started, never reached a verdict) |
| First-pass rate | 88.9%  — attempts that certified |
| Completion rate | 100.0%  — attempts that reached a verdict |
| Failures by gate | smoke 1 |
| **Defects and queues** | |
| Queue depth (claimable now) | 7 — a lane with none reaches for undefined work |
| Open bugs | 14 open · 16 fixed awaiting verification · 5 verified · 1 won't fix |
| Bugs by severity | 🔴 1 · 🟠 24 · 🟡 10 |
| Open 🔴 (blocks promotion) | 0 |
| Coordination items | 55 · 25 closed |
| Backlog | 24 tasks · 12 READY · 12 WAITING/BLOCKED · 4 claimed |
| **Automation** | |
| Governance checks, executable | 30 |
| Security Invariant files | 6 |
| Gate commands | make test · smoke · dr · certify · certified · state-check · doc-drift · kpi |

> **`make kpi` writes this block.** It is regenerated at every Closeout and **never edited by hand** — a number somebody typed is a number that stops being true quietly, and the first person to notice is the one who trusted it.

---

## 5 · Released AI prompts

A prompt is usable **exactly where a measurement says it is** — per `(model, dataset)`, and since M9.5 per **rendering protocol** too. Release is *derived* from the recorded evaluation, never declared.

| Prompt | Model | Protocol | Grounding / schema failures | Coverage | State |
|---|---|---|---|---|---|
| `explanation_narration@1` | `llama3.1:8b` | **2** | 0 / 0 | 1.00 | ✅ **Released** |
| `research_planning@2` | `llama3.1:8b` | **2** | 0 / 0 | 1.00 | ✅ **Released** |
| `research_synthesis@2` | `llama3.1:8b` | **2** | 0 / 0 | 1.00 | ✅ **Released** |
| `reasoning@1` | `granite3.3:2b` | 2 | **2** / 0 | 0.00 | 🔴 **REFUSED** |
| `reasoning@1` | `llama3.1:8b` | 2 | — | — | ⚪ **UNMEASURABLE** — times out on this hardware |
| `research_planning@1` · `research_synthesis@1` | — | 1 | — | — | ⚫ Superseded by `@2`; measurements retained |

**Every refusal above is in a manifest**, not only in prose — which is M9.5 Step A's whole purpose and what makes this table checkable.

**🔴 `reasoning@1` is the open blocker.** M9's Decision Package cannot be produced in production until it earns a release. Nothing has been tuned to make it pass: not the prompt, the delimiter, the schema, the timeout or the rubric. See the correction appended to [ADR-0031](docs/architecture/adr/0031-evidence-citation-protocol.md).

---

## 6 · Current AI architecture

A dashboard, not a specification. Authoritative detail: [28-ai-platform.md](docs/architecture/28-ai-platform.md) · [29-ai-reasoning-engine.md](docs/architecture/29-ai-reasoning-engine.md) · [ADR-0030](docs/architecture/adr/0030-the-decision-package.md).

| Component | State | What it guarantees |
|---|---|---|
| **AI Platform** (`modules/ai_platform`) | ✅ Built, **freezes after M10** | The one path to a model. Domain and application know nothing of the pipeline; the single reach into `opportunity_engine.public` happens in `infrastructure/` behind a Protocol |
| **Provider Registry** | ✅ Built, provider-neutral | Resolves **by model** — `for_model(model)`, with **no vendor-keyed lookup**. Business code that cannot *name* a vendor cannot branch on one. Ollama + Anthropic registered; a new vendor is an adapter registration |
| **Prompt Registry** | ✅ Built, per-directory | Each module owns its prompts. A version is immutable and fingerprinted; the loader refuses to start if the file disagrees with its fingerprint |
| **Evaluation** | ✅ Built, offline-refusing | The **only** command requiring a real model. Names no vendor in executable code (enforced by Security Invariant). A run that cannot execute produces **no verdict** rather than a partial average |
| **Grounding** | ✅ Built, unchanged since M8 | Five `ViolationKind`s. Validates that every citation resolves **inside a closed evidence set** — it does **not** validate that a fact in the set is true |
| **Decision Package** (M9) | ✅ Built | Fifteen parts; **the model authors three**. Eleven customer questions answered, eight without a model having spoken |
| **AI Reasoning Engine** | ✅ Built | Structured, single-call. Exactly one inference per package, enforced by test |
| **AI Research Engine** | ✅ **Complete** — M10, closed 2026-07-31 | Agentic, multi-step, minutes not seconds — over **Signora's own ledger**. Ruled **Internal Research** 2026-07-31: no external retrieval, and embeddings and pgvector deferred, because the Knowledge Graph stores typed edges and enum kinds rather than a corpus to embed |

**The organising principle**, ratified 2026-07-30:

> **Every field has the least powerful author capable of producing it correctly.** The database owns timestamps. Code owns derived facts. Domain experts own static knowledge. AI owns inference.

Its practical consequence: because twelve of fifteen parts need no model, **a failure to reach a model degrades a Decision Package rather than emptying it.**

---

## 7 · Active architectural findings

Only open items. Closed findings live in the milestone records (Appendix A) and the change log (Appendix B).

| ID | Finding | Severity | Owner milestone |
|---|---|---|---|
| **[ADR-0031](docs/architecture/adr/0031-evidence-citation-protocol.md)** | **Protocol 2 shipped, and did not remove over-copying.** The renderer and parser no longer disagree — the citation is presented exactly as `EvidenceRef.parse` accepts it, and no prompt instructs a transformation. But `granite3.3:2b` now copies the token **plus the em dash plus the summary**: protocol 1 *closed* the citation with a bracket, protocol 2 opens it at the line start and never terminates it. **`reasoning@1` therefore has no released model**, and M9's Decision Package cannot be produced in production. A protocol 3 that terminates the citation is the obvious hypothesis and belongs to a ratified amendment, not to the session that found this. *(Historical statement of the original defect retained in the ADR.)* | 🔴 **High** | **M9.5, open** | `render.py` emits `[token]`; `EvidenceRef.parse` accepts only `token`; the prompt says *"cite by their exact reference strings"*. Three of five models were REFUSED for **obeying literally**, across two independent model families. Passing since M8 on one model's bracket-stripping habit. **T138 produced its clearest instance yet**: `research_synthesis@1` was REFUSED because the model stripped the `research_finding:` prefix on one case and not the other — same prompt, same model, same run. **PROPOSED, deliberately unimplemented** — an M8 defect whose fix invalidates every released prompt, now three | 🔴 **High** | M8 / M9.5 |
| **F-1** | **One `ollama_model` setting versus several certified prompts.** ⚪ **Dormant rather than resolved.** Three of the four live prompts are now certified for `llama3.1:8b` alone, so one configuration currently serves every *released* path. It returns the moment `reasoning@1` earns a release on a different model — which is the likely outcome, since `llama3.1:8b` cannot measure it at all on this hardware | 🟠 **Medium** *(was High)* | M9.5 |
| **F-2** | **The Evidence Set question.** *(Narrowed by [32](docs/architecture/32-knowledge-ontology.md) and [34](docs/architecture/34-knowledge-contract.md), then **downgraded by the Internal Research ruling**.)* The immediate exposure is closed by design: a `ResearchSynthesis` has **no address**, so no consumer can cite model-authored prose even deliberately, and `ResearchFinding` is DERIVED with `EvidenceRef.kind = research_finding`. What remains open is the *deferred* question — **may an ATTESTED external claim be cited?** — which arrives with external retrieval and not before | 🟠 **Medium** *(was High)* | Deferred with external retrieval |
| **F-8** | **Three declared capabilities had no possible input, found by building a demo dataset (M12.1.5).** Only Apollo claimed `LEGAL_NAME`, so the naming resolver's `AGREED` and `DISPUTED` states — which M12.2 built the product to display — could never occur. Neither Crunchbase nor CoreSignal offered a domain, so a registry could reach an existing company only by naming it *identically*, and **every workforce fact resolved to a nameless entity of CoreSignal's own**: the account a seller could see and the account the hiring evidence described were two different rows. Crunchbase declared `acquisitions` in `known_fields` since M2.2 and never translated them, leaving `acquisition_announced`, `consolidation_underway` and its scoring weight dead at the source. **All three are fixed**; the finding kept open is the *class* — every one passed the tests it had, and none could run | 🟠 Medium | **Fixed M12.1.5; class unassigned** |
| **F-10** | **~~The pipeline computed *"grew headcount 3678%"*, and every layer faithfully passed it on.~~ Fixed 2026-08-01.** `_HeadcountRule` pools `EMPLOYEE_COUNT` and `OPEN_ROLES` into one series, so a ratio is taken from an open-roles baseline of 900 to an employee count of 34,000 — then labelled `employee_count`. The module's docstring guards the *provider* axis (*"nothing can combine them into a synthetic truth"*) and not the attribute axis. **Grounding could not catch it: the figure is in the evidence, and the model invented nothing.** Every component satisfied its own contract while a false statistic crossed the whole system. Present since M4; invisible to every gate because `baseline@1` never gave one entity both measures in one window, and **twelve varied accounts found it on the first run**. *Fix:* evaluate per attribute rather than pooled | ✅ **Fixed 2026-08-01** | Business Event Engine |
| **F-11** | **A zero-padded figure can never ground its unpadded form.** `_normalise` folds thousands separators and trailing decimal zeros, not leading ones — so evidence carrying `2026-08-01` yields `08`/`01` while a model writing *"August 1, 2026"* yields `1`, and the statement is refused. Correct by the letter of the check, wrong by its purpose; any date in the first nine days of a month fails. **Initially misdiagnosed as a golden-set variety problem** — the success rate went from 2/12 to 10/12 on a *date* change, not a prompt change. Grounding refused rather than admitted, which is the right direction to be wrong in. *Fix:* `lstrip("0")` in `_normalise`; **not applied** — `ai_platform/` is frozen and this loosens a guarantee, which is the product owner's call | 🟠 Medium | **AI Platform — needs a ruling** |
| **F-3** | Signal catalog `limitations` / `suggested_validation` are **engineering-authored pending domain review** | 🟠 Medium | Unassigned |
| **F-5** | `PublishableEvent` Protocol vs frozen domain events — requires a `type: ignore` at every publish site | 🟢 Low | Unassigned |
| **F-6** | **Nine `CHECK` constraints cannot reject what they were written to reject.** `array_length('{}', 1)` returns NULL, and a `CHECK` fails only on FALSE — so `array_length(x, 1) >= 1` accepts the empty array. Proven end to end: a `signal` citing **no** business events inserts successfully. Affects `observation`, `business_event`, `signal`, `buying_score`, `ai_narration`, `ai_reasoning` across six milestones. **No production defect** — every write path goes through a domain type that refuses the empty case — but nine comments claim a guarantee that does not hold. Repaired only in migration `0018`, which found it. See [36](docs/architecture/36-empty-array-checks.md) | 🟠 Medium | `T-CK1`, unscheduled |
| **F-7** | **Four `uuid5` namespaces and most derivation inputs survive mutation.** Documentation says *"never change it"*; nothing enforces it. See [35](docs/architecture/35-deterministic-identity.md) | 🟠 Medium | `T-ID1` / `T-ID2`, unscheduled |

**Resolved and recorded here because the dashboard previously claimed otherwise:** the cross-workspace read path on `outbox_event` is **closed**. Migration `0006` revokes all from `signora_app` and grants `INSERT` only; the relay identity holds `SELECT`. This document described it as "raised rather than applied" until 2026-07-31 — a claim the repository had already falsified.

---

## 8 · Known risks

Full register with mitigations and owners: [16-architecture-risks.md](docs/architecture/16-architecture-risks.md).

### 🔴 High

| ID | Risk | Note |
|---|---|---|
| R-01 | **AI vendor cost exposure without budget governance** | M8 made cost *measurable*; nothing governs it. The register says explicitly: define budgets **before AI Research Engine is enabled broadly.** M10 is the caller that makes this real |
| R-04 | PII classification / retention undefined | **Escalated to Legal.** Long lead time |
| R-05 | AI prompt data-classification policy undefined | **Escalated to Legal.** **M10 does not widen it** — under the Internal Research ruling, egress stays model-vendor-only, identical in kind to M8 and M9 today. *This row previously said research reaches public sources; that was the roadmap's assumption, not the ruling* |
| ADR-0031 | Citation protocol inconsistency | §7. Grows more expensive with every prompt released |

### 🟠 Medium

| ID | Risk | Note |
|---|---|---|
| R-09 | **AI Research timeout value undefined** | **Both halves now measured (T138).** A complete research task is **two model calls and nothing else of consequence**: planning **32.8 s** median (48.3 s cold), synthesis **20.8 s** median, derivations in microseconds — so **~54 s steady-state and ~70 s cold** end to end on this hardware, for a 2-fact account. Token cost is ~890 in / ~200 out for planning and ~760 in / ~125 out for synthesis; retries were 0 across nine measured calls. **The shape is the finding: the cost is two calls, not *N*** — the plan cannot name a derivation twice, so it is bounded by the catalog. The `ai_research` queue budget of 1800 s is ~26× the measured cold task. **Still not converted into a threshold**: this is a local 8 B model on 4 GiB of VRAM against the smallest realistic account, and production runs hosted models (ADR-0028). What is now known is the *shape*; the number belongs to the first hosted measurement |
| R-10 | AI output quality regression | Substantially mitigated: golden sets, rubrics, `ai_inference`, two evaluated prompts. **Not** closed — no human-rated sample yet |
| **New** | **Two new capability surfaces in M10** — agentic loop and *internal* tool use. Was four; embeddings and pgvector were deferred by the Internal Research ruling. M8 flagged tool use as *"carrying its own security surface deserving its own review"*, and internal tools reduce that surface without removing it |
| **New** | **Fixture-shaped coverage.** Six M9 mutations survived because one seeded scenario cannot vary contested scores, shared events or shared caveats. Every future module inherits that fixture | |

### 🟢 Low

JWT key rotation requires a deploy · token revocation bounded by a 15-min TTL · Casbin policy is coarse RBAC · no API versioning scheme (deliberate, with one first-party client) · `reasoning@1` coverage margin 0.667 against a 0.66 floor — an **observation**, explicitly not a reason to modify the prompt.

---

## 9 · Recent milestone summary — M10, closed 2026-07-31

| | |
|---|---|
| **Delivered** | T131–T138. Retrieval over `opportunity_engine.public` · a closed derivation catalog · three deterministic derivations · a planner that chooses work and cannot conclude · synthesis grounded against *findings* rather than facts · migration `0018`'s three tables · `ai_research.completed` · smoke stage 14k |
| **Architectural outcome** | **Every citable thing M10 produces is deterministic.** The model chooses which comparisons to run and writes the brief; neither produces a fact anyone may cite. `ResearchSynthesis` has no address, so narration structurally cannot become evidence. `ai_platform` is frozen on this evidence — a port that has now served an agentic, resumable workload |
| **Major findings** | The **Internal Research ruling** narrowed the milestone before T132 and removed every item with no repository support. `research_synthesis@1`'s refusal was the third prompt blocked by the citation protocol and **forced M9.5** rather than being tuned around. R-09 was answered by measurement — two model calls, ~54 s steady-state — and deliberately not converted into a threshold |
| **Deferred** | External retrieval · browser tools · public web search · embeddings · pgvector · provider re-query · ATTESTED findings — each with a stated trigger. `T-ID1`, `T-ID2`, `T-CK1` remain unscheduled |
| **Engineering lesson** | **A refusal is a finding, not an obstacle.** The milestone stopped on a REFUSED prompt, investigated instead of optimising, and the investigation produced a first-class repository concept (the Prompt Rendering Protocol) plus a certification framework. It also produced a *correction*: protocol 2 fixed less than predicted, and that is recorded rather than quietly absorbed |

**M9's full review: [30-m9-retrospective.md](docs/architecture/30-m9-retrospective.md).** Fourteen sections, written for an engineer arriving months later.

**What changed.** M9 is the first module that produces propositions its input did not contain. Everything before it derives, projects or restates; this one **concludes** — and the interesting half was never making a model reason, but *remaining accountable for a conclusion that cannot be checked against a fact.*

**The number that summarises it:** the model authors **3 of the Decision Package's 15 parts**. Support, temporal explanation, alternative readings, limitations and validation steps are all derived, composed or read from a reviewed catalog.

**Ownership moved five times**, always toward the component that already knew the fact — limitations to the signal catalog, rejected hypotheses to derivation rather than storage, the catalog itself to `SignalQueries`.

**Two ADRs:** [ADR-0030](docs/architecture/adr/0030-the-decision-package.md) (accepted) and [ADR-0031](docs/architecture/adr/0031-evidence-citation-protocol.md) (proposed, unimplemented). **No ratified ADR was reversed.**

**T128's assumption was disproved by measurement.** `reasoning@1` was believed to require a hosted model. It required **4 GiB of VRAM**: `llama3.1:8b` needs 5.6 GB and ran 58% on CPU, missing the 60s timeout. A 1.9 GB model resident 100% in GPU passed **eight consecutive times**. On this hardware *stronger → larger → more CPU offload → slower*, so the answer was a **smaller** model. No architectural change was required.

**The defining characteristic**, and the thing most worth carrying forward:

> **The repository improved the architecture by refusing incorrect assumptions** — through import-linter contracts, surviving mutations, unreachable guards, database grants, a layering rule, and four evaluation refusals. **Not one was worked around.** Nine stated assumptions proved false; five guards were removed for being unreachable; eleven mutations were run and six exposed genuine gaps.

---

## 10 · Current milestone — M12, the product surface

> **M12 was brought forward ahead of M11 and M7** on 2026-07-31, a Category 1 roadmap change and the product owner's to make. The reason is recorded evidence rather than preference: [31-m10-design-review-evidence.md](docs/architecture/31-m10-design-review-evidence.md) predicted this in a dissent — *"the pipeline runs nine stages ahead of any user-visible surface"* — and by M10's close it had come true. Full design: [37-product-surface.md](docs/architecture/37-product-surface.md).

| | |
|---|---|
| **Objective** | Make ten stages of pipeline reachable by a customer. Not more intelligence — **the first intelligence anyone can see** |
| **Shape** | Four slices. **M12.1** the attention list · **M12.2** the account brief · **M12.3** evidence resolution and workflow actions · **M12.4** research on demand |
| **Constraint** | No BFF, no new persistence, no new platform abstraction. The read paths exist; each module's `interface/` and the frontend are what is missing |
| **Scale** | ~13–17 ew across the four slices |

### M12.1 — in progress

Delivered: the first workspace-wide read path (`attention_list`), `GET /workspaces/{id}/accounts` with 20 full-stack tests, and `/opportunities` — **the first business screen in the repository's history.** Step 6, the performance review, is not yet measured.

### M12.2 — next, and re-ordered on usability evidence

**Entity names ship before the account brief.** The roadmap had M12.2 as the brief; building M12.1 produced the evidence to change that order.

**Why.** The attention list currently names each account by a truncated identifier — `6b8efd21` where a company name belongs — because no module in the ratified dependency graph can reach both workflow and entity names. **A seller cannot triage a list of identifiers**, so M12.1's screen is presently demonstrable rather than usable. Resolving names is a *smaller* change than the brief (one Knowledge Graph read endpoint plus a frontend join) and it is what converts M12.1 from a proof into a tool. Shipping it first makes the existing screen useful weeks before the brief would.

Recorded as **D2** in [38-product-design-principles.md](docs/architecture/38-product-design-principles.md).

*Both halves shipped: names, then the score breakdown. The narration and Decision Package panels remain.*

### M12.1.5 — inserted 2026-07-31, because the data had become the constraint

**A Category 1 insertion and the product owner's call.** M12.2's brief was the first surface with enough detail to expose what the demo dataset could not do: every account read *"evidence expired"*, and the account whose story was *stale evidence* showed a fresh ledger (D17). Design decisions, UX reviews and prompt evaluations were all being made against data that could not exercise them.

**Scope:** a demonstration dataset optimised for product review rather than for unit testing — twelve recognisable companies, twelve invented business situations, anchored on today so freshness varies on its own; complete identity coverage; determinism preserved; and the same pipeline, with no demo-only path.

**What it cost, and what it found.** The dataset itself was the smaller half. Building it surfaced **three declared capabilities with no possible input** (§7, F-8) — the naming resolver's multi-source states, every workforce fact's route to the company it described, and the entire acquisition chain. Each was complete in every layer except the one that had to supply the evidence, and each passed the tests it had.

**The rule this establishes:** a fixture set rich enough to demonstrate the product is also the first thing that exercises every declared attribute end to end. It belongs *before* the surfaces that depend on it, not after.

### M11 — deferred 2026-07-31, and why it is not cancelled

**`Recommendation Engine → AI Reasoning Engine`** is the ratified edge, and **`reasoning@1` has no released model**. M11 would layer a new AI module on a stage that cannot run, to produce recommendations surfacing on a product with one screen.

The product argument stands on its own: a recommendation answers *"what should I do?"*, which only becomes the user's question once they can answer *"which accounts?"* and *"why this one?"* — J1 ships, J2 and J3 do not. **Signora's differentiator is that a human can check every claim, not that it recommends**; shipping recommendations before the evidence surface ships the commodity half first.

**Trigger to resume — product maturity, deliberately not engineering effort:**

1. `reasoning@1` holds a current release, and
2. a design partner using the account brief asks *"so what do I do?"* — feedback showing the gap has moved from *what is true* to *what to do*.

*"When M12 is finished"* was rejected as a trigger: it would resume M11 on a schedule, and the deferral exists precisely because M11's value depends on a product state rather than a date. Full rationale in [37-product-surface.md](docs/architecture/37-product-surface.md).

### 🔴 The open blocker, restated

**`reasoning@1` has no released model.** This is M9.5's, not M12's, and it does not block M12 — but it means the shipped pipeline would refuse at the Decision Package stage, and no amount of green gates changes that. It must not be closed by tuning.

---

## Appendix A — Milestone records *(historical)*

> Dated records of what was true when written. **Corrected only for factual errors about the past, never rewritten to match the present.** Recent milestones are covered in more depth by [30-m9-retrospective.md](docs/architecture/30-m9-retrospective.md) and [docs/SESSION_HANDOFF.md](docs/SESSION_HANDOFF.md).

### Completed milestones

### ✅ M0 — Secure Multi-Tenant Foundation · closed 2026-07-28

| Delivered | Evidence |
|---|---|
| Full architecture documentation set | 19 docs + 27 ADRs; 651 cross-links verified |
| Product strategy | [PRODUCT_DIFFERENTIATORS.md](PRODUCT_DIFFERENTIATORS.md) |
| Engineering constitution | [CLAUDE.md](CLAUDE.md) |
| Workspace & Tenancy module | All 5 layers, 5 use cases, 4 REST endpoints |
| Platform: db, event_bus (publisher), auth, authorization, api, pagination | ~1,288 LOC |
| PostgreSQL RLS tenant isolation | 4 migrations, reversible, adversarially tested |
| JWT auth boundary (ADR-0026) | RS256, pinned algorithms, forged-attack tests |
| Casbin authorization | Workspace-scoped policy, unit-tested |
| CI pipeline definition | ruff, mypy, import-linter, pytest |
| Execution roadmap | 4 planning documents |

**Three defects found by testing, not review:** superuser RLS bypass · membership policy that delegated enforcement to application code · `platform` shadowing a stdlib module. All fixed, documented, and covered by regression tests proven to fail against the pre-fix state.

### ✅ M1.1 — Platform Runtime · closed 2026-07-28

All 11 tasks delivered. **Demo Checklist: 13/13 passed. AC-1 passed.**

| Delivered | Evidence |
|---|---|
| Coverage measurement + CI gate (T1, T2) | 95.01% measured, gate at 95%, Redis service in CI |
| Structured JSON logging with redaction (T3) | 23 tests; JWT/bearer/secret redaction proven |
| Event bus dispatch schema (T6) | Migration 0004: `processed_event`, `dead_letter_event`, relay columns |
| Outbox relay (T7) | 12 integration tests; concurrent-relay safety via `SKIP LOCKED` |
| Dispatch + platform-owned idempotency (T8) | 14 integration tests; exactly-once proven under concurrency |
| ARQ worker fleet, 7 pools (T9) | Per-stage pools; `ai_research` at concurrency 2 / 1800s timeout |
| Retry + dead-lettering (T10) | Capped exponential backoff; DLQ replay retains history |
| OpenTelemetry, Sentry, metrics (T4, T5, T11) | Trace context survives the relay hop; 8 pipeline metrics |

**Findings during delivery:**
- **Dead code removed.** The pagination refactor left `list_for_workspace` (no caller at all) and `list_for_user` (test-only caller) behind. Both deleted rather than covered with tests.
- **Coverage exclusion is narrow and justified.** Only `apps/worker/relay_main.py` (an `asyncio.run` entry point) is omitted. The *logic* inside the worker — `dispatch_event`'s retry and dead-letter policy, pool resolution — is tested directly.

### ✅ M1.2 — Authentication Boundary · closed 2026-07-28

All 7 tasks plus 3 added requirements delivered. **Demo Checklist 10/10. AC-2 passed.** [Architecture Validation Report](docs/architecture/ARCHITECTURE_VALIDATION_M1_2.md) issued: all seven confirmations hold.

| Delivered | Evidence |
|---|---|
| Next.js 15 scaffold, tooling, CI (T12) | ESLint, Prettier, tsc, Vitest, Playwright all green |
| Signing-key management (T15, done before T14 per approval) | Pair-match validation; 10 unit tests |
| Better Auth + Google/Microsoft OAuth (T13) | `auth` schema (migration 0005), password auth disabled |
| RS256 JWT issuance (T14) | **Cross-tier contract test: a real frontend-minted token verifies with the real Python verifier** |
| Typed API client (T16) | Token refresh, standard error envelope |
| Frontend shell (T17) | Sign-in, workspace create/list, sign-out |
| E2E auth journey (T18) | Playwright; skips cleanly without OAuth credentials |
| **Auth observability** (added) | 10 `AUTH_*` events across both tiers, shared vocabulary |
| **Auth health** (added) | Both tiers; key-pair match, JWT config, OAuth config, DB |

**First user-visible outcome in the project.** Design-partner onboarding is unblocked once M14.5 provides a deployed environment.

**Findings:**
- Two toolchain workarounds recorded in the validation report (ESLint flat-config bridge, `@vitejs/plugin-react` peer conflict). Neither is architectural.
- A skip condition in the contract test initially hid it — the frontend path was resolved one directory too shallow, so it silently skipped rather than running. Caught by running verbosely; a test that skips when it should run is worse than one that fails.
- **One defect found during validation and fixed:** `signora_auth` was created by migration 0005 but never connected as — the frontend defaulted to the database *owner*, which bypasses RLS on every application table and defeated the schema isolation the migration exists to create. Both tiers' permissions were individually correct; nothing asserted the relationship between them. Fixed and verified against a live database.

---

### Milestone records — written at each close

### ✅ M6 — Opportunity Engine · **CLOSED** 2026-07-29

| Field | Value |
|---|---|
| **Status** | ✅ **Completed** |
| **Completion date** | 2026-07-29 |
| **Commits** | `c638d1c` (proposal) · `8034cfb` (ratification + binding milestone DoD) · `6cec891` (T102–T110) |
| **`HEAD` at close** | `6cec891` |
| **Exit gate** | ✅ **`make smoke` passed** — 95s, fresh images, clean Compose stack, **20 stages**, 261 invariants green against the running system |
| **Effort** | ~8–12 ew scoped · delivered within range |

**The milestone in one line.** Signora's **first workflow module** — and the first sellable moment: the point where derived intelligence becomes something a person commits to.

**The permanent principle it establishes:**

> **Intelligence suggests. Humans commit.**
>
> A buying score may **create** an opportunity. **Only a human may progress one beyond the machine-authored boundary.** Commercial intelligence informs workflow; it never owns it.

**The distinction the milestone turned on.** Every module before M6 *derives*: delete its table, re-run the pipeline, and the same rows return byte for byte. An opportunity records that a human committed, and nothing reproduces that. That introduces **workflow state** as a third category of platform data, and with it an operational contract: until now *"rebuild the pipeline"* was universally safe; it is now safe **for derived intelligence only** — asserted by test rather than remembered.

**The lifecycle question, answered explicitly.** An opportunity **always outlives** the score that created it. A score is a reading with a stated expiry; an opportunity is a commitment. Nothing happening at a company is not evidence that a deal is dead. Cooling evidence is surfaced (`CURRENT`/`COOLING`/`STALE`, derived at read time, never stored) and **never acted upon** — creation is automatic, closure never is.

**Scope delivered.** `opportunity_policy@1` artifact · `Opportunity` (written once) and `OpportunityState` (append-only, complete state per row) · five stages with `TRACKING` the only machine-authored one · migration 0014 (three tables, forced RLS, no `UPDATE` grant) · customer-authored qualification policy with artifact fallback · `QualifyOpportunity` and `TransitionOpportunity` · membership verified server-side on every assignment · derived `evidence_state` · `OpportunityQueries` · `opportunity.created` and `opportunity.stage_changed` · smoke stage 14h.

**Acceptance criteria satisfied.** AC-58 through AC-65, plus tenancy, event-contract, and Security Invariant criteria. **29 new Security Invariants**, each proven to fail when its guarantee was removed.

**Architectural decisions recorded.** Workflow required **no exception to immutability** — no `UPDATE` grant on any of the three tables, and no `delete` on the repository either (derived tables offer deletion so regeneration can be their rollback; workflow has no regeneration). The machine/human boundary is enforced **three ways**: the type system, the domain, and a database CHECK. Reopening is a transition with `CLOSED_WON` terminal; `DISMISSED` stays distinct from `CLOSED_LOST` because one is feedback about Signora and the other a sales outcome.

**Two departures from the approved proposal**, recorded in [27-opportunity-engine.md](docs/architecture/27-opportunity-engine.md): the state log records **complete state rather than deltas** (a delta row can contradict the row before it; a state row cannot) · the citation is protected by **`ON DELETE RESTRICT`** (immutability governs updates and says nothing about deletes, and derived tables deliberately keep `DELETE`).

**Technical debt introduced.** None.

**Known limitation.** The simulated scenario produces a modest buying score, and Signora's shipped threshold correctly declines it. The demonstration has the *workspace* author its own threshold rather than lowering a product default to make a demo pass — both behaviours are asserted. **No product default was tuned.**

---

### ✅ M5B — Buying Score Engine · **CLOSED** 2026-07-29

| Field | Value |
|---|---|
| **Status** | ✅ **Completed** |
| **Completion date** | 2026-07-29 |
| **Commits** | `bc78021` (proposal) · `8c6333b` (ratification + decay reversal) · this change (T93–T101) |
| **Exit gate** | ✅ **`make smoke` passed** — 87s, fresh images, clean Compose stack, **22 stages**, 223 invariants green against the running system |
| **Effort** | ~8–12 ew scoped · delivered within range |

**The milestone in one line.** The pipeline's **first intentional reduction** — many live commercial hypotheses become one number per account, and everything the number discards stays recoverable through the ledger that produced it.

**The permanent principle it establishes:**

> **Buying scores prioritize commercial attention. They do not predict purchasing behaviour. They do not estimate probability. They do not resolve contradiction. They summarize *explainable* commercial attention.**
>
> A buying score may **summarize** intelligence; it must **never replace** it.

**The decision the milestone turned on.** *Prioritizing* is not *resolving*. Deciding which of two contradictory hypotheses is true needs evidence this module does not have and judgement belonging to AI Reasoning and to humans; ordering attention while the contradiction stands needs neither. That rules out the obvious implementation: **opposing hypotheses never cancel arithmetically**, because netting would score a fought-over account like an inert one — under the shipped model, 4 versus 45.

**Scope delivered.** `scoring_model@1` artifact (posture, weights, relevance multipliers, age bands, ceiling) · `ContributionLedger` as a first-class domain object with reproduction and no-double-count invariants checked at construction · `BuyingScore` projected from its ledger, immutable, with derived identity · migration 0013 (`buying_score`, `workspace_scoring_model`, forced RLS, no `UPDATE` grant) · customer-authored scoring models with artifact fallback · event-unit attribution · step decay · contradiction detection with named dissent · `ComputeBuyingScore` · the evidence-derived staleness sweep · `BuyingScoreQueries` · `buying_score.updated` · smoke stage 14g.

**Acceptance criteria satisfied.** AC-50 through AC-57, plus tenancy, event-contract, and Security Invariant criteria. **16 new Security Invariants**, each proven to fail when its guarantee was removed.

**Architectural decisions recorded.** Step decay over linear, exponential and none — *the decisive argument was semantic consistency, not accuracy*: a stored score promises to be exactly correct until `valid_until`, and only a discrete curve can keep that promise without continuous recomputation, which the platform has rejected. Also: the third ownership layer (`workspace_scoring_model` beside `signal_profile`, never inside it), posture as Signora's and weights as the customer's, the business event as the unit of contribution, and account fit deferred to M6.

**Three departures from the approved proposal**, each recorded in [26-buying-score-engine.md](docs/architecture/26-buying-score-engine.md): the sweep is workspace-scoped rather than cross-tenant (a cross-workspace query cannot be served under forced RLS without a role that bypasses it, and no such role may exist) · the score records `model_artifact_version` + `scoring_model_version` rather than four version numbers · the Signal Engine is reached through a `SignalReader` port rather than concretely.

**Technical debt introduced.** None. One unrelated defect repaid: `test_migration_runner.py` pinned the head revision to `"0012"`, so a test about *concurrency* failed on every new migration; it now reads head from the Alembic script directory.

**Carried forward.** The scheduled M2.0 simulation work — evidence recent enough that several hypotheses are concurrently live — is now the gating item for exercising the contested, multi-signal path at wall-clock now rather than through historical replay. **No fixture was tuned to make the demonstration look better.**

**M5B required no change to M5A and no new edge in the dependency graph** — the strongest available evidence that the Signal Engine boundary was drawn in the right place.

---

### ✅ M5A — Signal Engine · **CLOSED** 2026-07-29

| Field | Value |
|---|---|
| **Status** | ✅ **Completed** |
| **Completion date** | 2026-07-29 |
| **Commits** | `cde2218` (proposal) · this change (T84–T92) |
| **Exit gate** | ✅ **`make smoke` passed** — 76s, fresh images, clean Compose stack, **21 stages**, 186 invariants green against the running system |
| **Effort** | ~8–13 ew scoped · delivered within range |

**The milestone in one line.** The first module in Signora that produces something **true for only one customer** — and the point at which the platform stops describing the world and starts interpreting it commercially.

**The permanent principle it establishes:**

> **Business events describe objective business phenomena. Signals describe customer-specific commercial hypotheses.**
>
> Signals are therefore the **first subjective layer** in the intelligence pipeline. Everything above the Signal Engine remains globally true; everything below remains traceable back to globally true information. That subjectivity stays explicit, explainable, and constrained.

**Acceptance criteria satisfied**

| AC | Status |
|---|---|
| **AC-42** Customer-specific interpretation | ✅ Two workspaces, byte-identical business events, different signals — asserted through the real pipeline |
| **AC-43** No commercial scoring | ✅ Column-name invariant on `signal`; relevance is a category with no numeric meaning; no number in the module beyond windows and counts |
| **AC-44** Contradiction preserved | ✅ Opposing hypotheses coexist for one entity; nothing suppressed or reconciled |
| **AC-45** Two-part explainability | ✅ Every signal names both its evidence and the profile entry that made it relevant, in one call |
| **AC-46** Unbroken chain | ✅ Signal → business events → observations → entity → claims → raw records; zero orphans at every hop |
| **AC-47** Configuration is auditable | ✅ Profiles immutable, versioned, attributed; one current profile per workspace enforced by a partial unique index |
| **AC-48** Replay is explicit | ✅ Historical and current modes both work and are never conflated |
| **AC-49** The vocabulary stays global | ✅ A workspace-invented type is **unrepresentable** — `ProfileEntry.signal_type` is typed as `SignalType` |
| **AC-6** · **AC-1** · **AC-13** | ✅ Tenancy · event contract · invariants extended 154 → 186 |

**Scope delivered.** Signal catalog artifact, schema, and startup validation · domain and deterministic identity · profile model with versioning, supersession, and catalog-default fallback · two detection strategies · migration 0012 · `GenerateSignals` with relevance resolution and supersession · read port with four-question explanations · two event contracts · demonstration, smoke stage 14f, and 32 new Security Invariants.

**Architectural decisions.**

- **Global catalog, per-workspace relevance profile.** A workspace configures relevance over Signora's vocabulary and **can never invent a signal type** — the constraint that keeps AI prompting, benchmarking, analytics, and support able to speak about signals across customers.
- **Ownership decides where configuration lives, not technology.** The catalog is Signora's and ships as a repository artifact; the profile is the customer's and lives in versioned rows. A customer cannot be asked to wait for a release to say what matters to them.
- **Profiles are immutable and versioned.** An edited profile would make every historical signal unexplainable — *"why was I told this?"* would have no answer, because the reason changed underneath it.
- **Relevance is a category, never a number**, so the module contains no scores at all. This forced two corrections to the v2 event catalog: `signal.generated` **lost its `score`**, and **`signal.scored` was removed** — its only possible producer is a scoring model in M5B.
- **Composites enrich rather than replace.** Constituent signals are generated and stored in their own right, and the composite **names them**. Refined during review from "both stand" to a navigable hierarchy.
- **Catalog entries declare a detection *strategy*, not a procedure.** Adopted during review, and it proved to be more than terminology: the catalog now holds domain semantics only, so an improved implementation never changes what a signal *means*.
- **Replay has two first-class modes** — historical (reproduce what we told them) and current (what would we say now). Never conflated, and the second is what will let a customer preview a configuration change against their own history.

**Signal profiles are the first genuinely customer-authored data in the platform.** Unlike every other table, `signal_profile` cannot be regenerated from anything — it is a statement a customer makes about their own commercial position. Signals are derived and rebuildable; profiles are not, and they need backup and restore treatment derived tables do not. Asserted directly: a signal rebuild leaves the profile intact.

**One honest limit in the demonstration.** The baseline scenario's evidence is months old and every catalog type declares a shorter shelf life, so its hypotheses are formed, remain readable, and are **no longer live** — asserted explicitly. That is the lifecycle working, but it means the live-set behaviour is exercised by the negative case only. A scenario with recent evidence is now the fourth item of scheduled M2.0 simulation work.

**Technical debt.** None introduced. None outstanding.

---

### Records: what was 'next' when written

### ✅ M8 — AI Platform · **COMPLETE**

The AI Provider Abstraction Layer, the Internal Prompt Registry, and an evaluation harness — everything the reasoning and research modules will be built on.

**Built and pushed:** ADR-0028 (model runtime by environment) · the module scaffold and its five import-linter contracts · the AI Provider Port, failure taxonomy and model-keyed registry · the closed evidence set with a type-tagged digest · the five grounding checks · the Prompt Registry with content-hash identity and a derived release rule · Ollama and Anthropic adapters behind one contract suite · `application/infer.py`, the only path to a model · migration `0015` and the `ai_inference` operational record · the evaluation harness, rubric, golden dataset and `make eval`.

**Verified against a real model 2026-07-30.** `explanation_narration@1` passed evaluation against `llama3.1:8b` — 2 cases, 0 grounding failures, 0 schema failures, coverage 1.000 — and is **released for that model and refused for every other**, including `claude-sonnet-4-5`. Production runs hosted models, so the prompt M8 ships is deliberately not yet usable in production; closing that gap is an evaluation run, not a code change.

**Retry reporting closed before T121.** The first real run needed three calls for two cases — a cold model load pushed one past the 60 s policy timeout — and nothing in Signora's own report said so. `RunLog` now surfaces retries per case, in aggregate, and in the durable manifest record, and is deliberately excluded from the release criteria: retrying is what the platform is supposed to do about a transient failure.

**T121 completed the composition.** Migration `0016` adds `ai_narration` — a **fifth data category, the materialized AI artifact**: immutable, forced RLS, provenance denormalized so a row answers *which evidence · which prompt · which model · which inference · when* without a join. `ai.narration_completed` is cataloged with its producer. Smoke stage **14i** proves the chain end to end and deliberately calls no model.

**[ADR-0029](docs/architecture/adr/0029-operational-history-durability.md) closed the last finding.** `Infer` wrote an `ai_inference` row on every outcome but shared the caller's transaction, so a grounding failure that propagated rolled the record back — AC-69 held in the domain and **not in production**, and the ungrounded rate would have read 0% forever, confidently. Operational history now commits on its own transaction: *operational history answers "what happened?", business data answers "what became true?"*, and those take different lifetimes. `ai_narration` deliberately keeps the caller's transaction — a narration nobody committed was never shown to anyone. A failed operational write is itself observable (ERROR line plus `signora.ai.recording_failures`); the recorder never fails its caller, but never loses a record silently either.

**M8 is architecturally closed.** Nothing outstanding.

**Five permanent principles ratified during implementation** and recorded in CLAUDE.md §2/§6/§10: types make incorrect architecture impossible · hidden inputs are architecture defects · a guard that cannot fail is documentation pretending to be code · truth has exactly one authoritative representation · behaviour exists exactly once · ownership and configuration always align · observability is a product capability · evaluation measures compatibility with Signora's contract, not general model quality.

**Why it follows M6.** Opportunities are the first artifact expensive enough to justify agentic research and model reasoning. M8 builds the substrate; M9 and M10 use it.

**Recorded for later, not for M8:**

- **Account fit / ICP** was deferred out of M5A, M5B and M6. It needs **resolved entity attribute values**, which the Knowledge Graph deliberately does not provide — so it needs a *resolution policy*, a first-class architectural decision with its own principles. It deserves its own milestone rather than being smuggled into one that is about something else.

**Awaiting:** architecture proposal and approval, as with every prior milestone.

---

### Records: queue as written

Sequential execution — each begins only when the previous milestone's Demo Checklist passes.

| # | Milestone | Effort | Gate |
|---|---|---|---|
| 3–4 | M2.1 Provider Platform · M2.2 Provider Normalization | ~14–20 ew | Per roadmap |
| 5–6 | M3A Knowledge Graph · M3B Observation Engine | ~17–23 ew | AC-6 tenancy under load |
| 7–10 | M4 Business Events · M5A Signals · M5B Buying Scores · M6 Opportunities | ~29–43 ew | **M6 is the first sellable moment** |
| 11–14 | M8 AI Platform · M9 AI Reasoning · M10 AI Research · M11 Recommendations | ~41–56 ew | AC-8, AC-9 |
| 15–16 | M7 Timeline · M12 Revenue Intelligence Platform + business screens | ~30–43 ew | Business UI lands here |
| 17–19 | M13 Integrations · M14a Notifications · M14b Billing | ~24–34 ew | Per roadmap |
| 20 | **M14.5** Cloud Infrastructure *(deferred from M1.3B)* | ~6 ew | AC-3B · rollback executed and timed |
| 21 | M15 GA readiness | ~20–27 ew | AC-11, AC-12 |

**Full order and rationale:** [IMPLEMENTATION_ROADMAP.md §5b](IMPLEMENTATION_ROADMAP.md#5b-execution-sequence). Milestone IDs are stable labels, not sequence numbers — they are deliberately non-monotonic so that PRODUCT_ROADMAP, AI_MATURITY_ROADMAP, and every ADR cross-reference stays valid.

### Dependency corrections applied

| Correction | Why |
|---|---|
| **AI Reasoning Engine reinstated** (position 12) | Ratified module, and load-bearing: `AI Reasoning → Recommendation Engine`, and RIP lists it as a dependency. Omitted, it would never be built and two downstream modules would lose an input. |
| **Timeline moved before Revenue Intelligence Platform** (15 before 16) | `05-module-dependencies.md:76` records *"Revenue Intelligence Platform → Timeline: synchronous query"*. RIP consumes Timeline, so Timeline must precede it. |
| **Integrations (M13) reinstated** (position 17) | Ratified scope with its own architecture document and product milestone. Dropping it silently would remove committed customer-facing capability. |

None adds, removes, or substitutes a module, contract, or technology — each restores a ratified dependency.

### Module boundary rulings

**Company Domain** → part of Knowledge Graph. **Activities** → part of Timeline unless later separated. **Assignments** → unassigned; no owning context, nothing scheduled. **Workspace & Tenancy** → complete at M0, removed from the active order, retained as documented foundational work.
| 3 | **M14.5** Cloud Infrastructure *(deferred from M1.3B)* | ~6 ew | ❌ | AC-3B · rollback executed and timed |
| 4 | M15 GA readiness | ~20–27 ew | ✅ load at volume | Per roadmap |

### Cloud infrastructure is deferred, not removed

**M1.3B has moved to M14.5, immediately before GA readiness.** Sequencing only: the target production architecture is unchanged, the scope is unchanged, and nothing is redesigned. [ADR-0022](docs/architecture/adr/0022-devops-infrastructure-and-deployment-topology.md) remains ratified.

Deferred: Terraform, ECS, RDS and ElastiCache provisioning, Secrets Manager integration, the cloud deployment pipeline, cloud rollback validation, production monitoring dashboards, Auto Scaling.

**Why.** M1.3A already produced a running production stack. Cloud infrastructure adds *reachability*, not capability — it makes no pipeline module work, and until the pipeline exists there is nothing to reach. Building it now means carrying a deployed environment through ~200 ew that does not need one.

**What it costs, plainly.** No externally reachable environment until M14.5. Design partners cannot use the product remotely before then; a demo is a local stack or a screen share. Accepted deliberately.

**What keeps it cheap:** the [Infrastructure Contract](IMPLEMENTATION_ROADMAP.md#5a-infrastructure-contract) — ten requirements, all satisfied today, enforced every milestone. The failure mode of "we'll add ops later" is discovering at M14.5 that stateful services and hardcoded configuration accumulated for two years. `make smoke` is what will notice.

### Why M1.3 was split

M1.3A proves the **application** is deployable; M14.5 proves **AWS** is configured. Run together, a failure gives no signal about which one is wrong — and every application-level fault (a container that will not start, a migration runner racing two replicas, a readiness probe green before the database is reachable) costs minutes locally and an afternoon inside ECS.

### Why M1.4 exists

Verification is currently spread across a backend suite, a frontend suite, a cross-tier contract test, and a checklist a human reads. Each is individually green while the *composition* goes unverified — which is exactly where the M1.2 credential defect lived. One command turns "everything passes" into a claim about the system rather than about its parts.

### M2.0 — why it precedes every pipeline module

A permanent platform capability, not throwaway tooling — used for local development, integration testing, E2E testing, demos, AI evaluation, regression testing, performance benchmarking, and customer onboarding demos.

**It also builds the Provider Port**, as its first concrete implementation. That satisfies the YAGNI ruling and validates the port with working code before any vendor adapter is written or contract signed.

**Binding rule:** simulated providers implement *exactly* the same adapter contract as production providers. Switching is configuration only; no `if simulated:` branching may exist in any layer; the ingestion pipeline is byte-identical in both modes.

**Highest-risk control:** the simulator must never activate in production — it would fabricate customer intelligence. Guarded by an environment check, unambiguous ingestion logging, health-endpoint visibility, and an alert, all test-enforced.

---

---

## Appendix B — Change log

| Date | Change |
|---|---|
| 2026-07-31 | v28 — **M9 AI Reasoning Engine COMPLETE.** `reasoning@1` **released** against `granite3.3:2b`: 2 cases, 0 grounding failures, 0 schema failures, coverage 0.833, recorded after **eight consecutive passing runs** with **no change to the benchmark, dataset, rubric, schema, timeout or release criteria** — only `SIGNORA_OLLAMA_MODEL`. **The assumption that M9 needed a hosted model was disproved by measurement.** The constraint was **4 GiB of VRAM**, not reasoning capability: `llama3.1:8b` needs 5.6 GB and ran 58% on CPU, missing the 60 s timeout; a 1.9 GB model resident 100% in GPU passed eight times. On this hardware *stronger* means *larger* means *more CPU offload* means *slower* — the answer was a **smaller** model, which is the opposite of where the investigation started. No architectural change was required; `SIGNORA_OLLAMA_MODEL` already reached the registry. **[ADR-0031](docs/architecture/adr/0031-evidence-citation-protocol.md) written and deliberately NOT implemented:** the renderer emits `[token]` while `EvidenceRef.parse` accepts only `token`, and the prompt says *"cite by their exact reference strings"* — so three of five models were REFUSED for **obeying literally**. It is an **M8** defect that has been passing since M8 on one model's bracket-stripping habit, and fixing it requires re-evaluating both released prompts. `granite3.3:2b` is therefore recorded as **currently certified, not permanent**. Coverage sits at 0.667 against a 0.66 floor in seven of eight runs — recorded as an engineering observation, explicitly **not** a reason to modify the prompt. **Full [M9 retrospective](docs/architecture/30-m9-retrospective.md)**: nine stated assumptions proved false, five unreachable guards removed, eleven mutations run with six exposing genuine gaps — including one that would have told every customer nothing disagreed with their conclusion. 1564 tests, coverage ~95.8%, 295 invariants, 25 contracts, smoke green over 22 stages. |
| 2026-07-30 | v27 — **M9 T130 complete; M9 implementation finished, milestone not yet closed.** The Decision Package is produced, stored and announced end to end. **The principle the milestone establishes:** *every field has the least powerful author capable of producing it correctly* — which leaves the model authoring **3 of 15** parts, and makes a failure to reach a model degrade a package rather than empty it. T130 delivered the SQLAlchemy model, `SqlDecisionPackageRepository`, the `PipelineReasoningContext` adapter, `build_reason`, `ai_reasoning.completed` in the event catalog, and **smoke stage 14j** (109 tests, calling no model). **T128's architectural half closed:** both evaluation entry points now resolve providers through `build_provider_registry`, so `--model claude-sonnet-4-5` is configuration alone; the Ollama-specific `/api/tags` probe was **removed** rather than made conditional — it gated a *hosted* release run on a *local* runtime, and it was never what prevented a fake being substituted (composition is). A new Security Invariant enforces structurally that the evaluation framework names no vendor in executable code, prose exempt, with a positive control. **`reasoning@1` remains unreleased.** Run against the production model it returned **UNMEASURABLE — no adapter serves that model**, because no credential is configured here; a release could have been hand-written into the manifest in a minute and would have been a lie, so it was not, and a test now fails if one appears unearned. **Four findings, every one from the repository refusing something:** `public/` cannot publish a filesystem prompt loader (the layering contract was right, and binding prompts to an `Infer` is the application composition root's job); `SignalQueries` already owned the catalog, so a second injected copy was removed before it could disagree with itself; `signora_app` cannot read `outbox_event`, so the test uses the relay identity as the Platform Infrastructure Policy requires; and a redundant deduplication was deleted after a mutation proved it protected nothing. Eleven mutations run, six exposing real gaps that became permanent tests — including one that would have silently told every customer their evidence was single-sourced. 1563 tests, coverage 95.75%, 295 invariants, 25 contracts, `make smoke` green over 22 stages in 117s. |
| 2026-07-29 | v25 — **M5A Signal Engine complete.** The first module producing something true for only one customer. Permanent principle ratified: *business events describe objective business phenomena; signals describe customer-specific commercial hypotheses* — signals are the first subjective layer, everything above stays globally true, everything below stays traceable back. **Ownership, not technology, decides where configuration lives:** the signal catalog is Signora's and ships as a repository artifact; the profile is the customer's and lives in immutable, versioned, attributed rows. **A workspace can never invent a signal type** — unrepresentable, not merely discouraged. Relevance is a category with no numeric meaning, so the module holds no scores at all, forcing two catalog corrections: `signal.generated` loses its `score` and `signal.scored` is removed. Composites **enrich rather than replace** — constituents are stored independently and named by the composite. Catalog entries declare a detection *strategy*, keeping domain semantics separate from mechanics. Replay has two first-class modes, historical and current, never conflated. `signal_profile` is the first customer-authored table in the platform and cannot be regenerated from anything. 905 tests, coverage 95.50%, 186 invariants, 13 contracts, `make smoke` green over 21 stages. |
| 2026-07-29 | v24 — **M4 Business Event Engine complete.** The first module whose output reads as intelligence, and the first whose correctness is a product judgement. Permanent boundary: *answers "why is this business-relevant?", never "should we engage?"* — no priority, score, urgency, or rank, enforced by a column-name invariant. **Taxonomy is data; rules are code**, and the split is machine-enforced: rule modules are parsed as **syntax trees** and any numeric literal in a comparison other than 0 or 1 fails the build, with parameter declarations reconciled in both directions. Agreement is evidence, never truth — each provider's series is evaluated alone and two providers reaching one conclusion produce one event recording both. Taxonomy and payload versions kept separate so tuning a threshold never breaks a consumer contract. `business_event_type.published` removed: a repository artifact has no runtime publication to announce. **The CRO test changed three of nine proposed type names before implementation** — `EXECUTIVE_CHANGE` and `REVENUE_BAND_SHIFT` split by direction, `INTENT_SURGE` renamed — leaving eleven types across six business domains. Two limitations recorded rather than engineered around: the baseline scenario produces no intent surge under defensible thresholds, and AC-40 re-evaluation is wired at contract level only. 822 tests, coverage 95.39%, 154 invariants, 11 contracts, `make smoke` green over 20 stages. |
| 2026-07-29 | v23 — **M3B Observation Engine complete.** Permanent layering principle ratified: *claims preserve evidence · the graph resolves identity · the Observation Engine detects change · the Business Event Engine determines business meaning · the Signal Engine determines commercial meaning.* Change is computed **within one provider's series** — cross-provider comparison rejected as the central error, since disagreement merged into a series manufactures growth that never happened. First values establish a baseline and produce no observation. Observation identity is derived from observed facts, so deduplication is a primary-key conflict and a mapper fix cannot duplicate the table. Late arrival refines by append-only supersession. `entity.evidence_attached` approved and added to the Knowledge Graph; the canonical vocabulary formally recognised as a platform-wide contract. A Security Invariant reads derivation as a **syntax tree** to prove no threshold has crept in. Two defects found by running rather than by tests, one of them by `make smoke` against a fresh stack. 729 tests, coverage 95.10%, 124 invariants, 9 contracts, `make smoke` green over 19 stages. |
| 2026-07-29 | v22 — **M3A Knowledge Graph complete.** The first module that must *decide*. Permanent invariant ratified: *the Knowledge Graph resolves identity, not truth* — `entity` carries no attribute columns, and `ClaimSet` returns every contributing claim rather than a chosen value. `MatchStrength` ratified as a semantic category that can never become a number, with the type itself refusing numeric conversion and ordering. Ambiguity merges nothing, enforced by a database CHECK constraint. Migration 0009: four workspace-owned tables, forced RLS, `resolution_decision` immutable. Per-module-pair import-linter contracts added, immediately catching **two real boundary violations in shipped code** (M2.1 and M2.2), both fixed with read ports. **Two platform findings raised, not worked around** — `EventHandler` receives no session, so no module handler is registered in the live registry; and `PublishableEvent` cannot be satisfied by a frozen dataclass. One correction to the approved demonstration recorded honestly: three of five providers resolve together, not five, because the other two supply no matchable identity. 650 tests, coverage 95.54%, 99 invariants, 7 contracts, `make smoke` green over 18 stages. **[21-intelligence-pipeline.md](docs/architecture/21-intelligence-pipeline.md) authored.** |
| 2026-07-28 | v9 — **Platform Foundation approved and closed.** Eight platform contracts ratified (Platform Runtime, Authentication Boundary, Deployment Foundation, Platform Smoke Test, Security Invariants, Tenant Isolation Policy, Platform Infrastructure Policy, Platform Freeze). **M1.5 Frontend Foundation inserted** after M1.4 — frontend platform only, no business screens, no mock data. Business UI deferred until M2.0 produces real domain data. Cloud infrastructure confirmed at M14.5 with all task IDs and ADR references intact. Three dependency findings raised against the approved order (two graph inversions, five omitted modules, three unratified module names) — flagged, not silently reconciled. Sequencing only; the approved architecture is unchanged. |
| 2026-07-30 | v17 — **[ADR-0029](docs/architecture/adr/0029-operational-history-durability.md) ratified and implemented; M8 architecturally closed.** *Operational history answers "what happened?"; business data answers "what became true?"* — different categories of truth, therefore different lifetimes. `SqlInferenceRecorder` now owns a session factory and commits independently, so a grounding failure that rolls the unit of work back no longer discards the record of the call that failed. **AC-69 holds in production, not only in the domain.** The independent session stays an implementation detail: `Infer` sees only the `InferenceRecorder` port. The recorder scopes from `record.workspace_id`, taken from the verified evidence set, so a cross-workspace write is **unrepresentable** rather than merely refused. `ai_narration` keeps the caller's transaction and the asymmetry is asserted with a positive control. **A failed operational write is itself observable** — ERROR line plus the module-owned `signora.ai.recording_failures` counter; the recorder never fails its caller, but never loses a record silently. Options B and C explicitly rejected in the ADR because they appear to solve the problem and do not: a savepoint is inside the transaction that rolls back, and so is an outbox insert. Four mutations bite. Three further M8 principles recorded in CLAUDE.md §2 (determinism outranks convenience · immutability is the default for anything recording a fact · a module owns everything required to realize its behaviour). Verified: 1425 passed, 0 skipped · 280 invariants · 22 contracts · mypy strict clean over 383 files · coverage 95.36% · `make smoke` green. |
| 2026-07-30 | v16 — **M8 complete: T121 composes the validated platform.** Migration `0016` adds `ai_narration` — a **fifth data category, ratified 2026-07-30: the materialized AI artifact**, neither derived intelligence nor configuration nor workflow nor operational history, but a grounded explanation deliberately persisted for auditability, UX and provenance. Immutable (no `UPDATE` grant, no `UPDATE` policy, "current" derived from timestamps), forced RLS, provenance denormalized so a row answers *which evidence · which prompt · which model · which inference · when* without a join, `inference_id` deliberately carrying no foreign key because operational history and a customer-visible artifact have different lifetimes, and the subject addressed as `subject_kind`/`subject_id` so the pipeline's vocabulary stays out of the substrate's schema. `ai.narration_completed` cataloged with its producer, carrying **identity and counts, never the prose**. Smoke stage **14i** proves the chain end to end and deliberately calls no model — `make eval` remains the only command that does. **The stop condition was checked and not triggered:** grounding makes a proposition the pipeline did not compute inexpressible, so the M8/M9 boundary is mechanical. Nine mutations, all bitten. **One open finding, material and raised rather than fixed:** `Infer` writes an `ai_inference` row on every outcome, but `tenant_scoped_session` wraps `session.begin()`, so a grounding failure that propagates rolls the record back — AC-69 holds in the domain and *not* in production, which would make the ungrounded rate read 0% forever. Verified: 1417 passed, 0 skipped · 277 invariants · 22 contracts · mypy strict clean over 382 files · coverage 95.35% · `make smoke` green over 14i and 15. |
| 2026-07-30 | v15 — **M8 T111–T120 built, and the evaluation harness run against a real model.** Every model call in Signora now passes through one validated path; there is no way to obtain unvalidated model output. `ai_inference` (migration `0015`) makes the platform accountable for its own behaviour — a fourth data category, immutable, forced RLS, no `UPDATE` grant, with three PostgreSQL constraints stating what a row may claim and deliberately no SQL copy of the outcome enum. **First genuine evaluation:** `explanation_narration@1` passed against `llama3.1:8b` (2 cases, 0 grounding failures, 0 schema failures, coverage 1.000, floor 0.66) and is now released for that model and refused for every other — AC-74 satisfied, R-10 exercised for the first time. Ollama installed **rootless** into `~/.local` (no `sudo` available; SHA-256 verified rather than piping a script to a shell). Observations recorded rather than tuned away: 29.4 s cold load, 43–52 s per case, and **the first call hit the 60 s policy timeout and was retried** — the retry policy working, with a thin margin on this hardware. Three defects found and fixed: two in T118 that T119's table exposed (a provider failure recorded no vendor; a failed call recorded zero retries), and one in T120's own tests, which asserted the refusal-to-run-without-a-model guarantee by *inheriting* an absent runtime and broke the moment one was installed. Three false documentation claims corrected (`migrations/env.py` twice, `test_tenancy_policy.py` once). Two harness gaps raised, not fixed: the report does not surface retries, and the golden set's two cases are structurally identical. Verified: 1392 passed, 0 skipped · 274 invariants · 22 contracts · mypy strict clean over 377 files · coverage 95.36% · `make smoke` green. |
| 2026-07-30 | v14 — **Pre-flight repository synchronization; M8 design RATIFIED.** No architecture changed and no code written — this commit exists so the repository represents the architecture already approved. **Statelessness** recorded as the AI Platform's second permanent principle, with its consequences for `infer.py`, adapters, the registry, request lifecycle, replayability and future Business Capability Verification. `28-ai-platform.md` promoted from *approved in direction* to **RATIFIED**. `SESSION_HANDOFF.md` corrected — it had been instructing the next session to write a proposal that already existed. Current `HEAD` added per §20d. `make smoke`/`make dr` invoke through `bash`, removing dependence on an executable bit that commit `0309193` had dropped and that does not survive every checkout. Coverage now quoted as **~95.3%** rather than to two decimals: two identical runs measured 95.25% and 95.27%, so the earlier precision was false. Verified: 1089 passed, 0 skipped · 261 invariants · 17 contracts · mypy strict clean, 330 files · smoke green, 21 stages, 40 checks. |
| 2026-07-29 | v13 — **Local-First Development adopted ([ADR-0027](docs/architecture/adr/0027-local-first-development.md), CLAUDE.md §20c-2).** GitHub Actions disabled at repository level; all three workflows retained with `workflow_dispatch` as their only trigger and every job definition preserved. **A `git push` now stores the repository and triggers nothing.** The cross-tier JWT contract test gained a local home as `make smoke` stage 15b, which **fails if it is skipped** — the gap CI was silently covering. Documentation asserting CI as the current authority corrected to *local*; dated records of what was true at earlier milestones deliberately left intact. Two pre-existing drifts found while verifying: `make smoke` had **21 stages, not 23**, and measured coverage is **95.25%**. Re-verified locally: 1089 passed, 0 skipped · coverage 95.25% · 261 invariants · 17 contracts · mypy strict clean over 330 files · smoke green, 21 stages, 84s. |
| 2026-07-28 | v8 — **M1.4 Platform Smoke Test complete; platform foundation closed.** `make smoke`: 16 stages, ~46s, in CI, every stage proven to fail when deliberately broken. Two defects found by it — a relay that died permanently on a transient database failure (first and only post-freeze platform change, under the production-defect exemption), and two bugs in the smoke script itself that would have made it lie. **Cloud infrastructure deferred from M1.3B to M14.5** — sequencing only, nothing removed or redesigned — with a ten-point Infrastructure Contract (roadmap §5a) binding every milestone until then. 313 tests, coverage 95.63%. |
| 2026-07-28 | v7 — **M1.3A Deployment Foundation complete.** Production images (multi-stage, non-root, no secrets), concurrency-safe migration runner refusing runtime identities, 6-service production Compose stack, and Disaster Recovery Validation across Postgres/Redis/API/workers. Four defects found by running the stack rather than by tests — most seriously a worker that could never start while the whole suite passed. `signora_platform/` frozen. ADR-0022 updated with as-built topology. 310 tests, coverage 95.65%. |
| 2026-07-28 | v6 — **M1.2 approved.** Security Invariants suite established: 47 permanent invariants across authentication, authorization, database, and platform, each proven to fail when its guarantee is deliberately removed; wired into CI as a separately-reported job. Migration/runtime credential separation adopted as a permanent engineering rule (CLAUDE.md §8). M1.3 split into M1.3A Deployment Foundation and M1.3B Cloud Infrastructure; M1.4 Platform Smoke Test added; AC-3 split into AC-3A/3B/3C and AC-13 added. `@vitejs/plugin-react` recorded as scheduled technical debt. One architectural question raised for decision: platform-table read scope. |
| 2026-07-28 | v5 — **M1.2 Authentication Boundary complete.** 7 tasks plus 3 added requirements; 242 backend and 29 frontend tests; Demo Checklist 10/10; AC-2 passed; Architecture Validation Report issued. One defect found during validation: `signora_auth` created but never connected as, with the frontend defaulting to the database owner. |
| 2026-07-28 | v4 — **M1.1 Platform Runtime complete.** 11 tasks, 82 new tests (198 total), coverage 95.01% CI-gated, Demo Checklist 13/13, AC-1 passed. Dead code from the pagination refactor removed. 06-events.md updated to v3. |
| 2026-07-28 | v3 — sequential single-stream execution adopted; calendar restated by team size; Demo Checklist added as a completion gate; progressive AI regression assertion model defined; simulator identical-adapter-contract rule recorded |
| 2026-07-28 | v2 — M1 split into M1.1/M1.2/M1.3; M2.0 Provider Simulation Framework added; per-milestone Demo Scenario, User-Visible Outcome, DoD, Rollback, Operational Readiness introduced; R-14 identified; estimate revised to 225–305 ew |
| 2026-07-28 | v1 — Initialized. M0 closed. Roadmap documents created. |

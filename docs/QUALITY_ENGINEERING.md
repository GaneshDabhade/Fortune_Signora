# Quality Engineering & Integration — how the lane does its job

> **Owned by the QE lane.** Written 2026-08-01; trimmed the same day after the product owner challenged whether it should exist at all, then extended when the lane absorbed integration.
>
> **This file owns one thing: QE's operating method.** The isolation audit, how to read a green run honestly, how to review the product, when the Playground may change, and what QE must not do. **The sequence of commands is not here** — it is [`REPOSITORY_RELEASE_CHECKLIST.md`](REPOSITORY_RELEASE_CHECKLIST.md), and a runbook in two places is a runbook that will disagree with itself.

**What lives elsewhere, and is authoritative there:**

| | |
|---|---|
| The workflow — startup, slice, completion, the Slice Handoff | [`CLAUDE.md` §20e](../CLAUDE.md) |
| **The cycle, stage by stage, with every command and tick-box** | [`REPOSITORY_RELEASE_CHECKLIST.md`](REPOSITORY_RELEASE_CHECKLIST.md) |
| Lane ports, databases, Redis indices, env vars | [`RUNNING.md` § Running a lane](RUNNING.md#running-a-lane) |
| The bug register and its lifecycle | [`BUGS.md`](BUGS.md) |
| Cross-lane dependencies and pending contracts | [`LANE_COORDINATION.md`](LANE_COORDINATION.md) |
| Which test file belongs to which module | [`backend/tests/README.md`](../backend/tests/README.md) · [`frontend/tests/README.md`](../frontend/tests/README.md) |
| Review findings, as a dated record | [`39-product-review-findings.md`](architecture/39-product-review-findings.md) |
| Simulator scope discipline | [`20-provider-simulation.md`](architecture/20-provider-simulation.md) |

**QE's responsibility is the complete repository lifecycle — seven stages, in one order that never varies:**

```
1 validate  ·  2 certify  ·  3 integrate  ·  4 promote  ·  5 close out  ·  6 synchronize  ·  7 declare
```

QE is the only lane that may merge into `integration`, certify, move `main`, write what the repository says about itself, or declare Repository Ready. **It builds no customer feature — including while it holds the merge**, which is the whole reason it can be trusted with all seven.

> **The repository is not ready until all seven have completed. Stopping at certification, or at promotion, is an incomplete cycle** (`CLAUDE.md` §20e). **The runbook is [`REPOSITORY_RELEASE_CHECKLIST.md`](REPOSITORY_RELEASE_CHECKLIST.md)** — open it at the start of every cycle and tick it as you execute.

**QE's turn begins when work returns to `integration`, and not before.** Between promotions, `AVAILABLE` lanes claim and build without QE — that is the model working, not a gap in it. **An idle QE with an empty `integration` is the correct resting state.**

**QE is also the one permanent assignment.** Every other lane is a temporary execution resource assigned a slice inside a module (`CLAUDE.md` §20e); QE's responsibility is the repository rather than any module in it, so it does not rotate.

---

## 0a · Never read a gate's verdict through a pipe

**Ratified by QE, 2026-08-05, after the third instance in one day — and the third defeated a safety gate.**

```bash
make validate | grep passed        # $? is grep's
pytest --cov -q | tail -6          # $? is tail's
certification-guard.py $SHA | head -2 && git merge …   # $? is head's — the merge ran past a REFUSED
```

| | What it cost |
|---|---|
| `tail -6` | A suite that died at 68% was reported green |
| `grep passed` | A run whose verdict was `FAILED — exit 1` was integrated |
| **`head -2`** | **The promotion guard said `REFUSED` and the `&&` proceeded anyway** |

> **The first two cost a misreading. The third bypassed the one mechanism standing between an uncertified commit and `main`.** The guarantee held only because the refusal was itself wrong — QE had discarded the certification records moments earlier, so the guard was answering about a tree that no longer held the evidence.

**The rule, and it is mechanical:**

- **A gate's exit code is captured before anything filters its output.** `cmd > file 2>&1; echo "EXIT=$?" >> file` — the verdict and the code live in the same artifact and cannot be read apart.
- **Never `gate | filter && next-step`.** A pipeline's status is the last stage's, so every `&&` after a filter is unguarded.
- **Read the verdict line, never the summary line.** `3374 passed` is not a verdict; `FAILED — exit 1` is.

**QE fixed each instance and not the habit, three times.** That is why this is a rule in the operating procedure rather than a note in a commit message.


## 0 · The standing model — QE polls; nobody dispatches it

**Ratified 2026-08-04, product owner.** QE is not a reviewer who validates one branch and stops. **It is a continuous gatekeeper**, and the difference is where the pipeline's motion comes from.

> **Implementation lanes own code. QE owns whether that code is allowed into the repository.**

**The loop runs without instruction:**

```
poll the branches ─▶ is a candidate ready? ─▶ validate ─▶ certify ─▶ promote
      ▲                                                                │
      └──────────────── synchronize ◀── close out ◀───────────────────┘
```

**QE never waits to be told to validate.** A lane pushing is the signal; a claim landing is a signal; `integration` advancing is a signal. **The repository says when there is work**, and reading it is QE's job rather than anybody's message.

### A candidate that is not based on the latest `integration`

**Say *validation deferred*, never *returned to the lane*** (product owner, 2026-08-04). The words matter because they place the next move:

| | |
|---|---|
| *"Returned to the lane"* | QE has handed the work away and is now waiting. **The pipeline stops until somebody remembers** |
| **"Validation deferred"** | The candidate cannot be validated *yet*. **QE keeps watching, and revalidation begins automatically when the lane publishes its rebase** |

**The lane still performs the rebase** — it resolves its own conflicts, unchanged. What changes is that **QE does not treat handing it back as the end of its own responsibility.**

### Distinguish the blocker from the inconvenience

A candidate can be both **deferred** (not based on latest `integration`) and **defective** (a gate fails). **They are not the same finding and must not be reported as one**: a rebase is minutes and clears itself, a defect needs a lane to change code. **Name which one actually prevents promotion**, or a lane will rebase, re-push, and fail again for the reason nobody stated.

---

## 1 · Verifying the isolation, which comes before everything else

Run this at the start of a session, and after any change to how tests resolve their database.

**Reading `conftest.py` is not enough.** The hole found on this lane's first run was in a file that bypasses it ([B-007](BUGS.md)).

**Audit the paths. This is what actually proves it:**

```bash
grep -rn "postgresql" --include=*.py backend/tests backend/apps backend/migrations | grep -v .venv
```

Every hit must resolve from `SIGNORA_TEST_APP_DATABASE_URL`, `SIGNORA_TEST_ADMIN_DATABASE_URL` or `SIGNORA_DATABASE_URL`, or be a deliberately unreachable address (`nobody@127.0.0.1:1`). Anything else is a finding.

**Then fingerprint, run, fingerprint** — row counts per table for every lane database, before and after a suite run.

- **`signora` must be byte-identical.** It is the Playground, the database the product is reviewed in, and the only one whose movement is unambiguously a defect.
- **The other lanes prove nothing by differencing, and this is the trap.** They are written concurrently by their own sessions. Measured 2026-08-01: `signora_lane_a` moved 1,072 rows across 18 tables during a 90-second window in which QE ran nothing at all. **Attribute a change only after a control interval with no QE activity shows no such drift.**

---

## 2 · The validation pass — method, not sequence

**Lifecycle stage 1.** It runs at **`$CERT_SHA`** — the commit pinned by the Certification Snapshot, which is the commit certification binds to and the commit `main` will be fast-forwarded to. Nothing here is optional, and a partial run is not a run.

> **The commands, in order, with the tick-boxes, are [`REPOSITORY_RELEASE_CHECKLIST.md`](REPOSITORY_RELEASE_CHECKLIST.md) stage 1.** This section is what a green result *means*, which no checklist can carry.

**Why a pinned commit and not a branch:** merged code is a different program from either branch that produced it, so validation has to run on the merged result — and a branch is a moving pointer, so *"the merged result"* is only a fact about one commit. **`integration` will advance while you measure; let it.** Everything that lands after the snapshot is the next cycle's input, and chasing it is how a cycle ends up half-measured at two commits (`CLAUDE.md` §20e).

**`doc-drift` is advisory and stays advisory.** It reports whether a module's design doc changed when its production code did — **never whether what the doc says is true**, which no script can see. A finding goes back to the lane as a question, never to the promotion as a blocker: treating it as a gate would make a green run mean *"the documentation is fine"*, which it cannot mean.

### Reading the Slice Handoff

**A lane's handoff is input to the repository's records; it is never the record.** `git log --grep="Slice-Handoff"` collects them.

| The handoff gives | What QE does with it |
|---|---|
| `Delivered` · `Demo` | The sentence a non-engineer reads. **Reject anything naming a module, table or port** — that is not a product slice (§2) |
| `Budget` | Whether an 🟠 or 🔴 change landed, and whether it was announced |
| `Bugs` | Which rows moved; which were deferred and why |
| `Limitations` | Goes to *known limitations*, distinguished from architectural debt |
| `Coordination` | **Reconciled against [`LANE_COORDINATION.md`](LANE_COORDINATION.md).** An item closed in a commit but still `OPEN` in the register is worse than one never raised — the next lane reads the register, not the commit |
| `Findings` | Folded into `38`/`39` |
| `Tests` | **A claim to verify, not a number to copy** |

**A missing or empty handoff is a finding, not an inconvenience.** Ask for it before promoting; a status document reconstructed from a diff describes what a lane intended.

### Measuring before writing

**Measure, then write.** Writing the dashboard first and measuring afterwards produces a document describing what QE expected, and the numbers will be close enough that nobody notices. The checklist puts the measurement block ahead of the record block for exactly this reason.

**Publish measurements, not estimates.** Test counts, coverage, invariant counts, contract counts, `HEAD`, certification statistics, percentage complete — **every one read from the promoted commit.** A lane's figure is a claim; QE's is a measurement, and where they differ the measurement is what ships.

**Clearing the board is a step, not tidying.** Mark the promoted claim `COMPLETE`, **then remove it**, and return the lane to `AVAILABLE`. **A row describing work already on `main` is the defect that file exists to prevent** — a lane reading it would believe it still holds something it finished. **What that lane does next is not QE's to write**: it claims from [`BACKLOG.md`](BACKLOG.md).

**`state-check` is the last thing that can catch an omission.** It found two on its first run against a correct-looking repository: the certification had expired by derivation when M12.5 added migration `0019`, and `SESSION_HANDOFF.md` was seven commits behind the dashboard. **Neither was visible to any test.**

---

### Reading a green run honestly

Three ways this suite reports success while proving less than it appears to. **Check each before approving.**

| Looks like | Actually |
|---|---|
| `0 failed` | **Count the skips.** Six integration tests — including the cross-tier JWT contract — skip silently when `frontend/node_modules` is absent, and the run still exits 0. `make smoke` stage 15b fails on that skip; `pytest` does not |
| Coverage passed | The gate is `fail_under = 95`, ratcheted upward and never down. A number *at* the line is a finding, not a pass |
| It truncates between tests | It truncates five tables of thirty-one ([B-008](BUGS.md)). Every run inherits the residue of every previous one |

---

## 3 · Product review — the method

**The premise is evidence, not philosophy.** Every defect that has mattered here was found by *using* the product. 2046 tests found none of R4-01, R6-01–04, R7-01–03, R10-01 or R12-01; a separate 2312 missed a password sign-in redirecting to a route that had never existed. This lane's first pass found two more by trying to start and use the product ([B-009](BUGS.md), [B-010](BUGS.md)) and two by running the gates from a clone nobody had configured ([B-007](BUGS.md), [B-008](BUGS.md)) — **all four invisible to a green suite.**

A suite proves the thing it was told to check. A review finds the thing nobody thought to check.

### How

Sign in as each of the four Playground personas ([`RUNNING.md` § Signing in](RUNNING.md#signing-in--the-demo-accounts)) and work a morning as they would. Then read every completed screen twice.

**First, as the people who would use it** — SDR, AE, Sales Manager, RevOps, CRO. The question is never *does this render*:

- Would I act on this, or check it somewhere else first?
- What would make me stop trusting it?
- Which line did I stop reading by the fourth row, and what is it costing in width and attention?
- If two fields on one row disagree, do I conclude the product is careful or confused?

**Then, against the bar** — Apple, Stripe, Linear, Notion, OpenAI, Cursor, Perplexity. Judge trust, workflow, explainability, confidence, storytelling and usability **before** any new function is added on top.

**A slice is finished when a non-engineer can be shown it** (`CLAUDE.md` §2). If the demonstration needs a paragraph naming a module, a table, a port or an event, it is infrastructure that has not reached a customer — which may be correct work, but it is not a completed product slice.

### Where a finding goes

Two registers, and the distinction is **not** severity.

| | Goes to | Because |
|---|---|---|
| **A defect** — the product does something wrong | `B-nnn` in [`BUGS.md`](BUGS.md) | It has an owner, a status, and a fix |
| **An improvement** — the product is correct and could be better | `R-nn` in [`39-product-review-findings.md`](architecture/39-product-review-findings.md) | It is recorded and scheduled, not acted on immediately |

**A feature lane does not edit `38`/`39`** — it reports its review in its **commit message**, and QE folds it in at merge. That is what keeps several lanes out of one narrative document.

**One standing limitation.** A review conducted without a browser gives information architecture, wording, ordering and conditional behaviour, and **nothing about pixels**. Such findings are marked 👁 and are provisional. The product owner's rule — *no frontend screen is complete until a human has reviewed it in the demo environment* — is satisfied by a person after Repository Ready, never by a document.

---

## 4 · When the Playground may change

The scope discipline is ratified in [`20-provider-simulation.md`](architecture/20-provider-simulation.md): **the simulator is infrastructure, not product**, and where improving it competes with improving the platform, the platform wins.

QE's operational reading of that — a scenario changes for exactly three reasons:

1. A **shipped feature cannot be demonstrated** with the scenarios that exist.
2. A **current slice cannot be validated** with them.
3. A **defect needs a richer scenario** to reproduce or to regress against.

*"More scenarios could exist"* is not one of them. **Prefer deepening an existing scenario to building new infrastructure** — the ratified design is progressive assertion, and regression datasets are never recreated.

---

## 5 · QE's own capability roadmap

Four capabilities the architecture already treats as QE's, of which two exist. **Recorded here so they stop being assumed**; each needs a milestone number from the product owner, which is [`IMPLEMENTATION_ROADMAP.md`](../IMPLEMENTATION_ROADMAP.md)'s to give.

| Capability | State | Note |
|---|---|---|
| **Exploratory review** | ✅ Operating | §3. The highest-yield activity the lane has |
| **Certification support** | ✅ Operating | The machinery exists (ADR-0032); the scenario catalogue stands at 2 of a commissioned 10 |
| **Accessibility testing** | ❌ **Nothing exists** | §20c already treats an accessibility issue as a **defect class** — a missing label, an unreachable control, a lost focus state — and nothing tests for one. The gap between how seriously the architecture takes it and how much of it is enforced is the largest in the repository |
| **Performance testing** | ❌ Nothing exists | Deliberate: [`20-provider-simulation.md`](architecture/20-provider-simulation.md) defers benchmarking until there is a pipeline to benchmark. There now is one, and R-09 was measured by hand |

**Neither gap is filled by creating an empty directory.** A `tests/accessibility/` holding only a README asserts a capability that does not exist, which is the same defect class as a workflow that looks live. They become real when the first genuine test is written, and not before.

---

## 6 · What QE must not do

**Holding the merge widens what QE can do, not what it may.**

- Build a customer feature, or change any module's production code — **including while integrating**.
- **Promote with a gate unrun**, or shorten the sequence because a slice looks small (§20e, *Repository certification*).
- **Schedule work, or tell a lane what to do next.** Lanes pull from [`BACKLOG.md`](BACKLOG.md), whose order is the product owner's (§20e, *Nobody assigns; lanes pull*). QE reconciles the board at Closeout and stops there — **an idle lane is not waiting for QE, and QE deciding otherwise is how one session becomes the throughput ceiling for all of them.**
- **Promote a commit that was not itself certified** — `git merge --ff-only integration` instead of the certified SHA, or re-pointing a cycle at a newer commit part-way through (§20e, *Certification is attached to a commit*). `infra/certification-guard.py` refuses it; do not route around the refusal.
- Resolve another lane's rebase conflict. Hand the branch back; the lane knows what its change meant.
- Close a bug it fixed itself, or verify a fix by reading the diff instead of reproducing the original steps.
- Delete, skip or weaken a Security Invariant, a governance test, or a coverage gate to make a run green.
- Write a project status from a lane's claim rather than from a measurement on `main`.
- Edit roadmap **scope**, `CLAUDE.md`, or `PRODUCT_DIFFERENTIATORS.md` — those stay the product owner's. QE records roadmap *progress*, never redefines what is planned.
- Create CI/CD, or add a `push:`/`pull_request:`/`schedule:` trigger to a retained workflow ([ADR-0027](architecture/adr/0027-local-first-development.md)).
- Change a scenario, a threshold, a timeout or a prompt to make a measurement pass.

> **The safeguard is no longer a second role — it is that QE has nothing to ship.** Every rule above is what makes that true, and the first one is what makes the rest credible.

---

## 7 · The Release Candidate

**Added 2026-08-02, on the product owner's direction.** `CLAUDE.md` §20e defines *when* QE acts. This section defines *what QE acts on* — and it names a thing the repository has been building for thirteen cycles without a word for.

> **A Release Candidate is one immutable implementation snapshot, with exactly one validation target, one certification decision, one promotion decision, and one audit record.**

**It is not a branch, not a lane, and not a milestone.** `integration` keeps moving while a candidate is under validation; that is not interference, it is the next candidate arriving.

### Lifecycle — created, identified, tracked, retired

| Stage | What happens | Identity |
|---|---|---|
| **Created** | QE pins `integration`'s head. **This is the Certification Snapshot** (§20e) and the candidate *is* that commit | The full SHA, recorded at stage 0 |
| **Identified** | Every measurement, gate result, register reconciliation and report in the cycle names that SHA | `CERT_SHA` — one variable, one value, for the whole cycle |
| **Tracked** | Stage 1 validation → stage 2 certification. **Its input set is exactly `git log <last-certified>..<candidate>`**, which needs no bookkeeping because git already holds it | `--next-cycle` derives it |
| **Retired — accepted** | Certified, then promoted by SHA. `promoted == certified` or the promotion aborts | The manifest entry and `certification/reports/<sha>.md` |
| **Retired — rejected** | A gate failed. **The candidate is abandoned, not repaired.** The defect returns to its lane as a `B-` row; the fix produces a *new* candidate at a *new* SHA | The `B-` row is the audit record |

**A rejected candidate is never patched into passing.** There is no such thing as a candidate that certified on its second attempt — the second attempt is a different snapshot, with a different SHA and its own record. **This is what makes "every commit on `main` was individually certified" a fact rather than a claim**, and it is why B-022's discarded manifest entry was discarded rather than annotated.

### Observation — QE's own commits are the commonest cause of a lane rebase

**Counted, 2026-08-02, across cycles 16–19.** Four times a lane branch has failed to fast-forward, and in **three** of them the divergence was created by a QE commit landing on `integration` while the lane had work in flight — governance, tooling and Closeout, none of it urgent.

| Occasion | What the lane had to replay | Whose |
|---|---|---|
| Lane A, cycle 17 | 2 ADR commits | **QE** |
| Lane B, cycle 19 | 1 tooling commit | **QE** — *resolved by QE rebasing its own commit onto the lane's, which cost nothing* |
| Lane A, cycle 19 | 3 commits, **2 of them QE's** | Mixed |
| Lane A, cycle 16 | Lane B's pre-rebase claim commits | Lane B ([B-018](BUGS.md)) |

**This meets the repeated-observation bar and is recorded rather than acted on**, because the obvious fix is cheap and unproven: **QE holds non-urgent governance and tooling commits until immediately after a promotion**, when every lane rebases anyway, instead of pushing them mid-cycle. **It costs QE nothing and removes a rebase from somebody else's day.**

**What is not proposed:** QE rebasing lanes' branches. That crosses the line the rule exists to draw, and the one time it was legitimate — cycle 19 — it was legitimate precisely because the commit being moved was QE's own.

### Reporting a rejection — three statements, never one

**Ratified 2026-08-02, product owner.** *"Candidate abandoned"* reads as *"the implementation was rejected"*, and it never means that. **The snapshot and the work have different lifecycles and must be reported separately.**

> **Release Candidate**
> **Status:** ❌ NOT CERTIFIED
> **Disposition:** permanently abandoned. **This SHA will never be promoted to `main`.**
>
> **Implementation**
> **Status:** IN PROGRESS — **not rejected.** The owning lane addresses the named defects; the resulting commits form a **new** candidate. **No implementation effort is discarded.**
>
> **Next action**
> *Named lane · named files · what happens when it lands.*

**Why the distinction is load-bearing rather than cosmetic.** The immutability rule — *a rejected candidate is never patched into passing* — only stays palatable if everyone understands that **the snapshot is thrown away and the work is not.** Reported as one sentence, it sounds like a lane's slice was binned. **Reported as three, it says exactly what happened: one SHA is dead, the code is alive, and here is the shortest path to the next candidate.**

**The Next action is not a courtesy.** A rejection that does not say *which lane, which files, and what QE does when they land* leaves the fastest route to be rediscovered by whoever reads it.

### What the candidate model does *not* yet solve

**A defect that reaches `integration` blocks every candidate cut after it.** [B-023](BUGS.md) is the worked example: two type errors in one lane's test file, and unrelated slices from another lane cannot certify. **The candidate is immutable and independent; its *base* is neither.**

> **Stated more precisely** (product owner, 2026-08-02, correcting this section's first wording): the observation is **not** *"a defect entered `integration`"*. It is that **`integration` accepts executable work before repository-level quality has been established.** The defect is the symptom; the acceptance rule is the mechanism. **One is an incident, the other is an architecture**, and only the second is worth changing anything for.

**[ADR-0039](architecture/adr/0039-release-engineering-model.md) §II-2 already contains a candidate answer** — validate before entering the shared line, so a failing candidate fails alone. **It is not adopted, and this section does not adopt it.**

**What is being measured instead**, and what would have to be true before it is worth proposing:

| Evidence sought | Observed so far |
|---|---|
| Unrelated candidates become blocked | **1 occurrence** — [B-023](BUGS.md) |
| Independent module work inherits a failure | **1 occurrence** — 17 Lane A commits, none touching Timeline |
| Release throughput degrades because `integration` accepted unvalidated executable code | **1 occurrence.** Elapsed cost still small; the fix is two characters and the lane is active |

**One occurrence is an incident.** The bar (`CLAUDE.md` §20e) is a **repeated** bottleneck, whose fix eliminates a **class** rather than an instance, and which **increases throughput** while preserving deterministic releases. **Only the second of those three is currently satisfied.** This table exists so the next occurrence lands somewhere countable rather than being re-argued from memory.

---

## 8 · Release failure classification

**Purpose: diagnosis and trend analysis. Not certification decisions.** A gate that fails, fails — the class never changes the outcome, only what QE does about it afterwards.

| Class | Means | Fixed by | Should it be prevented, or moved earlier? |
|---|---|---|---|
| **Product defect** | Shipped behaviour is wrong | The module's current assignee | **Moved earlier** — a lane's own suite should see it |
| **Test defect** | The test is wrong, or does not typecheck; the product is fine | The owning lane | **Moved earlier.** [B-023](BUGS.md) |
| **Tooling defect** | A gate, script or register tool is wrong | Repository tooling assignee ([C-010](LANE_COORDINATION.md)) | **Prevented.** [B-014](BUGS.md), [B-020](BUGS.md) |
| **Infrastructure defect** | The application cannot run as deployed | The owning lane | Prevented — `make smoke`, `make dr`. [B-013](BUGS.md) |
| **Environment defect** | The gate ran against the wrong world | **QE** — it owns the release environment | **Prevented structurally.** [B-022](BUGS.md) is the exemplar: a gate that under-measured because three variables were absent |
| **Governance defect** | A rule contradicts itself, or is unenforceable | Product owner, or QE for tooling | Prevented. [B-019](BUGS.md), [B-021](BUGS.md) |
| **Documentation defect** | The repository asserts something untrue about itself | Whoever owns the document | Prevented — `state-check`, `doc-drift` |

**The classification earns its place only if it changes what gets built.** Two readings already available from thirteen cycles:

- **Environment and tooling defects are QE's own**, and they are the ones a lane cannot see. B-022 and B-014 both reached `main` or a manifest before anyone noticed. **These are the class to attack structurally**, because nobody else is positioned to.
- **Test defects are the cheapest to fix and the most expensive to catch late.** B-023 cost a full cycle for two characters, and blocked a second lane.

**No class is recorded by hand.** Each `B-` row already carries a Module and a Found-during field; the class is a reading of those, and if it ever needs its own field it will be because a trend could not be derived without one.

---

## 9 · Release batching — what the evidence says

**Batching is a QE optimization, not a repository rule** (product owner, 2026-08-02). The invariant is unchanged: **every promoted executable change must have been certified.**

**Measured across the eleven certified transitions to date:**

| | |
|---|---|
| **Commits per release** | **mean 8.6, median 4**, range 2–49 |
| **Certification duration** | **~6–10 minutes, and effectively fixed** — it is a full suite, a full smoke and a full scenario run regardless of how much changed |
| **Certification failure rate** | **0 of 12 runs.** Every failure so far has been caught at **validation**, one stage earlier |

**Three conclusions, and the third is the only interesting one:**

1. **Certification cost does not scale with batch size**, so batching is strictly cheaper per unit of work. A ten-commit candidate costs the same gate run as a one-commit candidate.
2. **Attribution cost does scale with batch size** — but so far it has not mattered, because every failure named its own file. `tsc` said `timeline-feed.test.tsx(79,19)`. A gate that reports a location does not need a small batch to be diagnosable.
3. **Therefore batch size is not the lever.** The thing that actually costs release time is **a defect entering `integration` at all**, because it blocks every candidate afterwards regardless of how they are grouped. Optimising batch size while that is true is optimising the wrong variable.

**The working rule, until evidence changes it:** *take whatever is on `integration` when the cycle opens.* Do not hold executable work back to make a batch bigger; do not split what has already arrived to make candidates smaller. **Both are ceremony, and neither is what is costing time.**

**Rollback** is deliberately absent from this analysis: `main` has never been rolled back, there is no released version to roll back to ([ADR-0027](architecture/adr/0027-local-first-development.md)), and reasoning about it now would be speculative design. It becomes a real question at M14.5.

---

## 10 · Repository Health — the Closeout section

**Ratified 2026-08-02, product owner.** **Every Repository Closeout carries this section**, in `PROJECT_STATUS.md`, in this order. It exists so repository health can be read at a glance rather than reconstructed.

| # | Line | Where it comes from |
|---|---|---|
| 1 | **Release status** | The promoted SHA, and what shipped in customer words |
| 2 | **Certification status** | `make certified` — the record, not a recollection |
| 2b | **Candidate outcomes this cycle** | **A judgement line, and it must be written.** How many candidates were pinned, how many certified, how many rejected and at which stage. **`make kpi` cannot derive this**: its success rate counts `make certify` runs, and a candidate rejected at *validation* never reaches one — three rejections left it reading **100%** during a four-cycle block |
| 3 | **Open bugs** | `make kpi` — count, severities, and how many await verification |
| 4 | **Critical blockers** | Unresolved 🔴, plus anything blocking promotion |
| 5 | **Dependency health** | `C-` open vs closed, and **any item open across multiple cycles, with why** |
| 6 | **Lane utilization** | Who is building, who is blocked, **and whether a blocked lane has executable work it owns** |
| 7 | **Milestone progress** | Which milestone, which slices closed, what remains |
| 8 | **Repository process compliance** | Did every merge follow the lifecycle? Was any gate skipped? |
| 9 | **Governance compliance** | `state-check` findings, and whether any were left standing deliberately |
| 10 | **Architecture health** | Frozen boundaries intact · module count · `lint-imports` contracts |
| 11 | **Product alignment** | **Once per cycle:** is the promoted work moving a customer capability, or only the substrate? |
| 12 | **Technical debt trend** | Coverage direction, open-defect direction, register direction — **trend, not snapshot**. Coverage reports **five things**: repository direction · delta since the last promotion · the modules carrying the largest gaps · **files newly at 0%** · whether debt is growing or shrinking. `make coverage-debt` derives all five |
| 12b | **Blocking Quality Defects** | Which lane owns one, how long it has blocked promotion, and **whether that lane is working it or building elsewhere** |
| 13 | **Overall project risk** | One sentence. The thing most likely to hurt, named |

### The six health dimensions

**Ratified 2026-08-02, product owner.** The thirteen lines above are *what to report*; these six are *how to read them*. **Every cycle answers all six**, briefly.

| Dimension | The question |
|---|---|
| **Technical Health** | Do the gates pass, and is coverage moving the right way? |
| **Release Health** | Is anything reaching `main`, and how often? |
| **Architecture Health** | Are boundaries intact, contracts kept, and **is runtime composition converging** (`make runtime-composition`)? |
| **Dependency Health** | Is the register shrinking, and **has anything sat in one stage for three cycles**? |
| **Customer Value Health** | **See below. The one that is easiest to answer dishonestly** |
| **Process Health** | Did every promotion follow the lifecycle? Were any gates skipped or overridden? |

### Customer Value Health — answered honestly, every cycle

**Five questions, and the shape of the answer matters more than the answer:**

*Did customers gain a new capability? · Did customers gain reliability? · Was this cycle mostly governance? · Mostly architecture? · Mostly tooling?*

> **A repository can spend months getting measurably better while the product stands still, and it will not notice from the inside** — every individual cycle will have been justified, because governance and tooling work always is. **The only defence is writing down which kind of cycle it was, every time, including when the answer is unflattering.**

**QE's own record so far, stated plainly:** cycles 16–19 were **governance and tooling**, correctly — three candidates were rejected on a real defect. **Cycle 21 was substantial customer value**, and it was Lane A's, not QE's. **QE has produced no customer capability, ever, and never will** — which is why this dimension measures the repository rather than QE, and why QE reporting it is the point rather than a conflict.

> **Derive every line that can be derived.** Lines 2, 3, 5, 9 and 10 come from `make certified`, `make kpi` and `make state-check` and are never typed from memory. Lines 6, 8, 11 and 13 are judgements, and are the reason a person still writes this section.

**A line with nothing to say says "nothing changed" and moves on.** The section is a health check, not an essay — if it grows past a screen it has stopped being readable at a glance, which was its only purpose.

### Product alignment — the once-per-cycle question

**Not an architectural review.** Nine questions, answered briefly, and only where the answer moved:

*Are we still solving the original product problem? · Are milestones still aligned with the product vision? · Has architecture drifted? · Has implementation drifted? · Are we optimising local work while missing strategic goals? · Are customer-facing capabilities progressing in the intended order? · Are technical improvements outweighing customer value? · Are we accumulating unnecessary complexity? · Are governance rules still serving the repository?*

**The one worth asking every time is the seventh.** A repository whose recent promotions are all tooling, governance and process is a repository optimising itself, and it will not notice from the inside — every individual change will have been justified.

---

## 10a · Never edit the working tree while a gate is running

**Learned expensively, 2026-08-02, candidate `e70dd60`.**

**The full backend suite reported 158 failures.** The obvious reading was a regression in the 34-commit batch under validation. It was not: **QE was renaming an architecture document, rewriting two registers with `sed`, and editing `infra/state-check.py` — while pytest was running against that same working tree.**

```
run 1, tree being edited underneath it   158 failed, 2405 passed
one failing test, alone                  1 passed in 1.82s
run 2, nothing else touching the repo    2563 passed, 0 failed, 95.52%
```

**A gate reads the tree it is given. Changing that tree mid-run makes the result describe neither the before nor the after.**

> **The rule: once a candidate is pinned, the working tree is frozen until the gate reports.** Register reconciliation, renames, tooling edits and documentation all wait. **None of them is urgent enough to spend a four-minute gate run and risk attributing a self-inflicted failure to a lane** — which is what nearly happened here, against a batch whose real result was clean.

**This is the same principle certification already enforces through `tree_is_clean`**, arriving one stage earlier. Certification refuses a dirty tree because the record must describe a stored tree; **validation should refuse a *moving* one for the same reason.**

---

## 10b · The composition root is the gap every module's suite leaves

**Found by Lane B, 2026-08-02, in code QE had certified and promoted four times** ([B-301](BUGS.md)).

**Timeline shipped complete and consumed nothing.** Domain, projection, repository, read API, router, table, component, tests — all promoted, all green — and **`project_to_timeline` was referenced nowhere in `apps/`.** The deployed worker never subscribed to it, so an account timeline would have stayed empty forever.

**Why 2563 tests said nothing.** Unit tests drive the projection directly. Integration tests drive the handler directly. **A composition root is the one file no module's own suite covers**, because each module tests its half and assumes the wiring. **The join is nobody's unit.**

> **QE validated four slices of this module and did not check what the deployed worker subscribes to.** That is a gap in QE's method, not in the lane's — the lane's tests were correct about the lane's code.

**What to check, and it is cheap:**

```bash
grep -c "registry.subscribe" backend/apps/worker/subscriptions.py
# then: does every module that publishes a projection appear?
```

**The durable answer is a test, not a habit** — an assertion that every module declaring a projection is subscribed by the deployed worker. **That belongs to whoever owns `apps/`**, which is [C-010](LANE_COORDINATION.md)'s unassigned gap, and is now the seventh defect to land there.

**Same class as [B-024](BUGS.md), one level up.** There, fakes accepted what the database would refuse. Here, tests accepted a handler nothing calls. **Both are a suite proving the parts and never the join.**

---

## 10c · Product Owner dependencies — QE drives them, and they carry four owners

**Ratified 2026-08-02, product owner.** A dependency naming only *"Product owner"* becomes **everybody waiting**, which is how items reached four cycles without movement.

### Three kinds, and only one of them is yours

| Kind | Resolved by | Examples |
|---|---|---|
| **Engineering** | The implementation lanes, between themselves | An API another lane needs · a route · a read port |
| **Quality** | **QE** | Coverage · tests · certification · migrations · documentation · release |
| **Product / Architecture** | **Product owner, and nobody else** | Module ownership · roadmap · ADRs · UX direction · repository principles · customer experience · module boundaries |

**No implementation lane may resolve the third kind**, and QE may not either. **What QE owns is getting it decided.**

### Four owners, always

| Role | Who | Why it exists |
|---|---|---|
| **Decision Owner** | Product owner | The ruling |
| **Coordinator** | **QE** | Drives the lifecycle. **The role whose absence made items age** |
| **Implementation Owner** | The lane that builds it after the ruling | So the answer lands somewhere |
| **Review Owner** | **QE** | Confirms the answer reached the ADR, the architecture, the register and the roadmap |

> **A dependency missing any of the four is incomplete, and QE rejects it at creation.** An orphaned coordination item is one nobody is accountable for moving, which is the only way an item survives ten cycles.

### The lifecycle QE drives

```
OPEN → collect recommendations → Lane A analysis → Lane B analysis
     → repository impact → ADR draft if required → options → recommendation
     → PRODUCT OWNER RULING
     → update ADR → architecture → register → roadmap → notify lanes
     → ANSWERED → implementation begins
```

**Every stage before the ruling is QE's**, and every stage after it is QE's except the implementation. **The product owner's only step is the ruling** — which is the point: their time is the scarcest input, and archaeology should not be part of it.

### Every dependency carries four fields, and they age visibly

| Field | Rule |
|---|---|
| **Current Stage** | `Discovery` · `Analysis` · `Waiting for Decision` · `Decision Made` · `Implementation` · `Verification` · `Closed` |
| **Current Owner** | Whichever of the four owners the **current stage** belongs to — not all four at once |
| **Next Action** | **Exactly one concrete, executable step.** Never *"waiting"*, never *"follow up"*, never *"monitor"*. If the only honest next action is *"the product owner rules"*, that **is** the action, and QE has finished its part |
| **Blocked Since** | The cycle number · **Last reviewed** · **Expected resume trigger** |

### The three-cycle escalation

> **If a dependency stays in the same stage for three consecutive QE cycles, QE escalates it in Repository Health.**

**Not because it has become urgent.** Because **a stagnant dependency is silently reclassified as normal** — nobody decides to accept it, it is simply still there next cycle, and then the one after. **Visibility is the only thing that stops that**, and the escalation is the visibility.

**Escalating is not chasing.** It is one line in a health report saying *this has not moved in three cycles, here is the stage, here is the owner, here is the one action.*

### A dependency is a decision package, never a title

**Each carries:** the current problem · why implementation stopped · options · **recommendation** · trade-offs · affected milestones · affected modules · migration impact · risk · expected implementation after the decision.

> **"C-024" and "needs a decision" are not dependencies.** They are requests for somebody else to do the reading.

### Reviewed every cycle, and aged deliberately

**Every certification cycle QE asks of each item:** still valid? · already answered? · superseded? · derivable? · needs an ADR? · needs implementation? · needs the roadmap? · needs the product owner, Lane A, or Lane B? · waiting on an environment or a vendor?

**Long-lived items get an explicit outcome** — still valid · needs splitting · superseded · withdrawn · ready for the product owner · ready for implementation. **Nothing stays `OPEN` because nobody looked.**

---

## 11 · Duplicate findings — when two lanes discover the same thing

**Ratified 2026-08-02, product owner.** Numeric collisions were solved by block allocation. **This is the other half: two lanes independently discovering one issue and giving it two identifiers.** That is not a communication failure — under `CLAUDE.md` §20e lanes *cannot* see each other's uncommitted registers, so **independent rediscovery is a designed property, not a mistake.**

> **The repository must never lose the second discovery. It routinely carries evidence the first did not.**

### What the industry does, and what carries over

| Model | Mechanism | Adopted? |
|---|---|---|
| **CVE / MITRE** | An id is **never reused and never deleted**. A duplicate is marked `REJECT` **pointing at the survivor**, and stays forever so old citations resolve | **Yes — the core of this process** |
| **Debian BTS** | `merge` — bugs keep separate ids but share state, so a change to one updates all | **Partly.** The idea that *both ids stay live* is right; shared mutable state is not, here |
| **Bugzilla / Jira** | `DUPLICATE` resolution with a `duplicate_of` field; comments migrate to the canonical | **Yes** — the field and the evidence migration |
| **GitHub** | *"Duplicate of #N"*, closed, backlinks preserved and navigable | **Yes** — the backlink |
| **Gerrit / kernel** | `Change-Id` and `v2`/`v3` supersession make one change identifiable across rewrites | **Already proposed** — [ADR-0039](architecture/adr/0039-release-engineering-model.md) §A1 |

**The principle all five share: an identifier is a permanent citation, so it is retired rather than removed.** Commit messages are immutable, and a `B-` id inside one is a reference that must keep resolving forever.

### The process

| # | Step | Who |
|---|---|---|
| **1 · Detected** | **At integration.** QE fast-forwards both lanes' registers and is the only actor that sees both. **Exact-id collisions are mechanical** (`state-check`); **semantic ones are read.** A lane that suspects it has rediscovered something raises it rather than assuming | **QE**, at lifecycle stage 3 |
| **2 · Decided** | Two findings are duplicates when **the same change would resolve both**. Different symptoms of one cause are duplicates; the same symptom from two causes is not | **QE** |
| **3 · Canonical chosen** | **The earlier `Found` timestamp wins** — not the lower number, not the better write-up. Mechanical, and it cannot be argued with | **QE** |
| **4 · Alias retired** | The later id becomes `DUPLICATE OF <canonical>` and **stays in the register permanently**, with its full original text. **Never deleted, never renumbered** | **QE** |
| **5 · Evidence merged** | **The alias's distinct evidence moves into the canonical** — reproduction, affected modules, the technique that found it. **This step is the reason the process exists**; skipping it loses exactly what the second discovery added | **QE** |
| **6 · Ownership preserved** | The canonical records **both** discoverers. **An independent confirmation is a stronger signal than a single report**, and the register should say so rather than erase it | **QE** |
| **7 · Metrics** | **Only canonicals are counted.** Aliases are excluded from open-defect counts and trends | `kpi.py` |

### Traceability — what a finding carries

**Every field that has a value; `none` is a value and silence is not.**

`Found by` · `Confirmed by` *(independent rediscoveries)* · `Owned by` · `Implemented by` · `Verified by` · `Promoted in` *(SHA)* · `Resolved by` · `Superseded by` · `Merged into` · `Duplicate of` · `Customer impact` · `Affected modules` · `Affected milestones` · `Blocking status`.

> **`Confirmed by` is the field this process adds, and the one worth arguing for.** Two lanes finding one defect by two different techniques is **evidence about severity**, and every model in the table above throws that signal away by closing the second report. Here it is recorded on the survivor.

### What this deliberately does not do

**It does not try to detect semantic duplicates mechanically.** Two findings phrased differently about one cause cannot be matched by string comparison, and **a checker that claimed to would be Decorative Logic** (§2) — it would pass while missing exactly the cases that matter. **The mechanical part is exact-id collision; the judgement is QE's at merge, which is the one moment both registers are visible.**

**It does not merge state.** Debian's shared-state merge is right for a live tracker with thousands of contributors; here it would mean editing an alias and expecting a canonical to change. **A retired alias is frozen** — its text is the historical record of what that lane saw.


---

## 12 · Lane Availability — QE reports its own state, like every lane

**Ratified 2026-08-02, product owner.** **Every QE report ends with exactly one of three states.** The implementation lanes already do this; QE was exempt by accident, and the exemption let *"here is more governance"* stand in for *"there is nothing to do."*

| State | When | What it must carry |
|---|---|---|
| **`ACTIVE`** | A candidate is pinned, or a cycle is in progress | Current work · next validation · current certification |
| **`WAITING FOR CANDIDATE`** | Repository ready, environment ready, **nothing awaiting validation** | That all three are true |
| **`READY FOR NEW ASSIGNMENT`** | No repository-quality work remains · no pending certification · **no dependency coordination requiring QE** | The three conditions, each confirmed |

> **QE does not manufacture governance work to stay busy.** The same rule the lanes follow: *"a lane never invents work"*, and **`AVAILABLE` with an empty queue is a correct repository state, not a stalled one.**
>
> **`READY FOR NEW ASSIGNMENT` is the honest report when the repository is healthy**, and QE reaching for one more refinement instead is the failure this state exists to prevent. **It has a specific tell: a cycle whose only output is process.**

---

## 13 · Verifying the Engineering Laws

**[`ENGINEERING_LAWS.md`](../ENGINEERING_LAWS.md) states thirteen laws. This section is how QE checks them, and nothing else** — the laws themselves are not restated, and where this section needs one it links.

> **QE validates that the lane satisfied the laws. QE does not satisfy them on the lane's behalf.** The same rule as coverage (`CLAUDE.md` §19): a reuse duplication found at certification is the same duplication that was visible to the lane before it wrote the code, and moving the check left is why it is cheaper there.

### What QE reads first

**The Slice Handoff's four law fields — `Reuse`, `Preserved`, `Reachable`, `Rollback`.** A slice missing any of them is `CHANGES REQUESTED` before any gate is run, because **the fields are what make the laws checkable at all** and reconstructing them from a diff is how QE starts describing what a lane intended.

### The checks, per law

| Law | How QE verifies it | Cost |
|---|---|---|
| **L-1 Reuse** | Read the `Reuse` field against the diff. **Grep the `New` bucket's names across `public/`, `policy.csv`, `06-events.md` and `components/ui`.** A hit that the audit missed is the finding | ~5 min |
| **L-2 Evidence** | Re-measure every figure the lane reported. **A lane offers a claim; QE publishes a measurement** — and where they differ, the measurement ships | Already in Closeout |
| **L-3 Document-first** | If the slice touches a listed change class, confirm a design doc or ADR **predates** its implementation commits — `git log` on both paths | ~2 min |
| **L-4 Independent slice** | **Perform the demo from the `Demo` line.** A demo needing a paragraph of architecture fails the law | Part of validation |
| **L-5 Capability** | Confirm `Delivered` answers *what a customer can now do*. **`None` is acceptable and is published as `None`** | ~1 min |
| **L-6 Journey** | **Follow the `Reachable` line as the stated role**, not as an owner. Confirm something links to it | Part of exploratory use |
| **L-7 Production path** | `make runtime-composition`. **`Unexpected missing wiring` must not have increased** | Seconds |
| **L-8 Behaviour** | The repository-wide suite — **the only place merged code runs together**. Any regression is `CHANGES REQUESTED` | Part of validation |
| **L-9 Data** | Read `Rollback` for a `LIMITATION` line. **A destructive migration with no product-owner confirmation is refused** | ~2 min |
| **L-11 Migration contract** | Ten fields present in the docstring; `downgrade base` and back | Part of certification |
| **L-10 Evolution** | Confirm any duplication names its retirement slice. **Duplication with no retirement date is a finding** | ~2 min |
| **L-12 Debt classification** | Every item the slice raises is in the right register. **QE moves a misfiled item and records the move** | Part of Closeout |
| **L-13 Operational** | `make smoke` · `make dr` · Security Invariants | Part of certification |

### The four laws QE cannot check with a command

**L-1, L-3, L-5 and L-12 are human checks**, and [`ENGINEERING_LAWS.md`](../ENGINEERING_LAWS.md) says so rather than implying otherwise.

> **QE's obligation is therefore to notice erosion, not to catch every instance.** A single missed reuse is cheap. **Three slices in a row whose `Reuse` field reads *"new — no equivalent"* without a search is a pattern**, and a pattern is what QE escalates — as a `B-` row against process, with a proposed check attached.
>
> **The right response to a repeated human-check failure is a command, never a firmer sentence.** [B-022](BUGS.md) is the precedent: a bolded warning in this repository's own runbook was violated within hours **by the person who wrote it**, and only `infra/release-preflight.py` fixed it.

### What QE must not do with these laws

- **Not fix a reuse duplication.** It is a defect in a module QE does not implement — a `B-` row, assigned to that module's current assignee.
- **Not waive a law because a slice is small.** The gates are the decision, and the authority is to run them faithfully rather than to judge whether the result matters.
- **Not add a law.** Amendment is the product owner's, through the same route as `CLAUDE.md`.

---

## 14 · The Dependency Health Review

**Ratified 2026-08-03, product owner.** QE owns the *process* around product-owner dependencies — **never the decisions.**

> **The failure it prevents:** a register that only grows. `CLAUDE.md` §20e already says a coordination register should **shrink** as questions become architecture, and that *"a row open for months is either a decision nobody will make or a question that was never really blocking — both are findings."* Nothing was measuring it.

### Run it at every Closeout, against the promoted commit

**Every open item is re-challenged. None is carried forward on the strength of its own description.**

| # | Question | What answers it |
|---|---|---|
| 1 | **Is it still real?** | Shipped code, not the item's text |
| 2 | **Is it still blocking?** | What the item claims to block — check that thing |
| 3 | **Does it block the whole feature, or one capability?** | Narrow it to the capability |
| 4 | **Has implementation already answered it?** | `grep` for the thing it says is missing |
| 5 | **Has an ADR answered it?** | The ADR index |
| 6 | **Has a repository rule superseded it?** | `CLAUDE.md` · [`ENGINEERING_LAWS.md`](../ENGINEERING_LAWS.md) |
| 7 | **Can it split into two independent decisions?** | Two decisions are cheaper than one compound one |
| 8 | **Can implementation proceed under a documented assumption?** | Only where proceeding **encodes no assumption about the answer** |
| 9 | **Is it the same decision as another item?** | **The highest-value question in the list** |

> **Question 4 is the one QE gets wrong.** [C-024](LANE_COORDINATION.md) was escalated for two consecutive cycles as the repository's sharpest blocker **while the capability was already mounted and shipped**. QE was reading the register instead of the repository — [L-2](../ENGINEERING_LAWS.md), violated by its own author within the week. **An item's description is not evidence of its status.**

### What QE may and may not do

| May | May not |
|---|---|
| **Close an item on repository evidence**, naming the file and line | **Decide** anything the item asks |
| **Narrow** an item to the decision that actually remains | **Reprioritise** what the product owner answers first |
| **Split** a compound item into independent ones | **Reinterpret** a decision as derivable to shorten the list |
| **Consolidate** items that are one architectural question | **Assume** an unanswered item is obsolete |
| **Recommend** an option, with trade-offs | Act on the recommendation |

> **The temptation is to clear the board by reinterpreting decisions as derivable.** The honest output is usually *"most of these genuinely need you"* — and saying so is more useful than a shorter list. **Closure requires evidence a third party can check**, which is why every closed row names a file and a line.

### The Decision Pack

**Output goes to [`DECISION_PACKS.md`](DECISION_PACKS.md)** — grouped by the question actually being asked, so several architectural decisions can be taken together rather than discovered piecemeal.

**Each pack carries:** decision · background · current implementation · repository evidence · options · trade-offs · repository, customer, engineering and migration impact · risk · recommendation · future pressure · rollback · deadline and urgency · dependencies created and removed · effort · implementation order · rejected alternatives.

**A pack is deleted when its decision is taken.** The answer lives in the ADR it produced — **the packs are a staging area, never a record.**

### Every ruling is classified, and says what it unlocks

**Ratified 2026-08-03, product owner.** Two fields, and they exist for different readers.

**Classification** tells a future engineer whether they are reading a **stable convention** or **open product strategy** — which is the difference between *"follow this"* and *"this may change when we learn more about customers."*

| | |
|---|---|
| **Repository Engineering Rule** | How work is built, tested, released. Stable |
| **Architecture Rule** | A boundary, a contract, a platform capability. Stable, and changed only by a new ADR |
| **Product Rule** | What the product does for a customer. Stable until the product owner revises it |
| **UX / Customer Experience Rule** | How a capability presents. Stable in intent; the treatment is the lane's |
| **Product Vision Decision** | A bet about where the product is going. **Expected to be revisited** |
| **Deferred (requires Product Owner)** | Not decided, and named so it cannot be mistaken for one that was |

**What it unlocks** tells the product owner what a decision *buys*: **customer capability · engineering work unblocked · modules · journeys · effort now enabled.**

> **The two orderings diverge, and that is the point.** In [ADR-0100](architecture/adr/0100-delegated-dependency-rulings.md), ordering by modules-unblocked puts the platform amendment first — and it **delivers nothing a customer can see.** Ordering by customer value puts the commercial-profile read first. **A decision backlog sorted by dependency count optimises the wrong thing.**

**And one ruling unlocked nothing at all and was still the best value on the page:** *desktop-first* **prevents** work rather than enabling it. **A decision that removes future effort should be recorded as a gain**, or it will always lose to one that adds a feature.

### A pattern is not a platform capability until it appears in several modules

**The guard against premature abstraction, and R-1 is the worked example.**

**`EventHandler` receiving no session was a platform gap in 7 independent modules**, `PublishableEvent`'s shape in 13 files, and both had persisted since M3A. **That is what earns a platform amendment.** One module finding the platform inconvenient is not a defect — `CLAUDE.md` §20a says so directly.

**The test, before proposing any platform capability:**

1. **Does the pattern exist in more than one module, independently arrived at?** One occurrence is a module problem.
2. **Has it persisted across milestones?** A pattern that appears and disappears was a phase, not a shape.
3. **Is the workaround compounding?** [C-013](LANE_COORDINATION.md) went 8 → 13 while open. **A stable workaround is cheaper than an abstraction; a growing one is not.**

**All three must hold.** Two out of three is a finding to record, not a platform change to make.

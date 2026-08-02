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
| 3 | **Open bugs** | `make kpi` — count, severities, and how many await verification |
| 4 | **Critical blockers** | Unresolved 🔴, plus anything blocking promotion |
| 5 | **Dependency health** | `C-` open vs closed, and **any item open across multiple cycles, with why** |
| 6 | **Lane utilization** | Who is building, who is blocked, **and whether a blocked lane has executable work it owns** |
| 7 | **Milestone progress** | Which milestone, which slices closed, what remains |
| 8 | **Repository process compliance** | Did every merge follow the lifecycle? Was any gate skipped? |
| 9 | **Governance compliance** | `state-check` findings, and whether any were left standing deliberately |
| 10 | **Architecture health** | Frozen boundaries intact · module count · `lint-imports` contracts |
| 11 | **Product alignment** | **Once per cycle:** is the promoted work moving a customer capability, or only the substrate? |
| 12 | **Technical debt trend** | Coverage direction, open-defect direction, register direction — **trend, not snapshot** |
| 13 | **Overall project risk** | One sentence. The thing most likely to hurt, named |

> **Derive every line that can be derived.** Lines 2, 3, 5, 9 and 10 come from `make certified`, `make kpi` and `make state-check` and are never typed from memory. Lines 6, 8, 11 and 13 are judgements, and are the reason a person still writes this section.

**A line with nothing to say says "nothing changed" and moves on.** The section is a health check, not an essay — if it grows past a screen it has stopped being readable at a glance, which was its only purpose.

### Product alignment — the once-per-cycle question

**Not an architectural review.** Nine questions, answered briefly, and only where the answer moved:

*Are we still solving the original product problem? · Are milestones still aligned with the product vision? · Has architecture drifted? · Has implementation drifted? · Are we optimising local work while missing strategic goals? · Are customer-facing capabilities progressing in the intended order? · Are technical improvements outweighing customer value? · Are we accumulating unnecessary complexity? · Are governance rules still serving the repository?*

**The one worth asking every time is the seventh.** A repository whose recent promotions are all tooling, governance and process is a repository optimising itself, and it will not notice from the inside — every individual change will have been justified.

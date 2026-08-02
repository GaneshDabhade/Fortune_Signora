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

**Clearing the assignment board is a step, not tidying.** Mark the promoted assignment `COMPLETE`, **then remove it**, and return the lane to `AVAILABLE`. **A row describing work already on `main` is the defect that file exists to prevent** — a lane reading it would believe it still holds something it finished.

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
- **Promote a commit that was not itself certified** — `git merge --ff-only integration` instead of the certified SHA, or re-pointing a cycle at a newer commit part-way through (§20e, *Certification is attached to a commit*). `infra/certification-guard.py` refuses it; do not route around the refusal.
- Resolve another lane's rebase conflict. Hand the branch back; the lane knows what its change meant.
- Close a bug it fixed itself, or verify a fix by reading the diff instead of reproducing the original steps.
- Delete, skip or weaken a Security Invariant, a governance test, or a coverage gate to make a run green.
- Write a project status from a lane's claim rather than from a measurement on `main`.
- Edit roadmap **scope**, `CLAUDE.md`, or `PRODUCT_DIFFERENTIATORS.md` — those stay the product owner's. QE records roadmap *progress*, never redefines what is planned.
- Create CI/CD, or add a `push:`/`pull_request:`/`schedule:` trigger to a retained workflow ([ADR-0027](architecture/adr/0027-local-first-development.md)).
- Change a scenario, a threshold, a timeout or a prompt to make a measurement pass.

> **The safeguard is no longer a second role — it is that QE has nothing to ship.** Every rule above is what makes that true, and the first one is what makes the rest credible.

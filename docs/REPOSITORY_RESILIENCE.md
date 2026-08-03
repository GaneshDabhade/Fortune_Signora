# Repository Resilience — a proposal, and the measurement that justifies it

> **Status: proposed, 2026-08-03, by QE at the product owner's direction. Nothing here is implemented.**
>
> **This is a design document, and it exists because a near-miss is evidence and a scenario list is not.** The product owner asked for resilience rules against sixteen imagined incidents. Before writing rules for sixteen, QE measured which of them the repository is actually exposed to **right now**. The answer is one, it is specific, and it is smaller than the brief — which is why the proposal is six rules rather than a backup strategy.

---

## 1 · What was measured

**Every working copy on this workstation, 2026-08-03**, immediately after cycle 34 was promoted:

| Working copy | Branch | Modified | **Untracked files** | Unpushed | Last commit |
|---|---|---|---|---|---|
| `Signora-QE` | `lane-qe` | 0 | 0 | **0** | minutes |
| `Signora-LaneB` | `lane-b-commercial-profile` | 13 | **5** | **0** | 3 hours |
| `LaneA/signora-lane-a` | `lane-a-product-surface` | 6 | **22** | **0** | 2 hours |
| `Signora-Demo/Fortune_Signora` | `main` | 819 | 0 | **0** | **26 hours** |
| `SignoraHumanReview` | — | *empty directory* | — | — | — |

> **The 819 is noise, and the last column is why the column exists.** That clone is a stale checkout carrying GitHub workflow files this repository removed months ago. Without the age beside it, the loudest row in the report is the one that matters least — and a report whose largest number is noise teaches people to skim it.

### The finding, stated exactly

> **Committed work is not at risk. Every branch on this machine is pushed — zero unpushed commits across four repositories.**
>
> **Twenty-seven untracked files across two lanes exist in exactly one physical location.** A disk failure this afternoon loses them and nothing else.

**Corrected 2026-08-03, within hours of first publishing it.** This table first said *"seven untracked paths"*, because `git status --porcelain` **collapses an untracked directory into a single line** and the count was taken from it. The real figure is 27, and the difference was not cosmetic:

```
Lane A   backend/modules/sales_engagement/          an entire module — 22 files
           domain/ application/ infrastructure/
           prompts/executive_summary@1.md           ← a prompt release
           prompts/manifest.json                    ← a prompt manifest
           evaluation/datasets/approach@1.json      ← an evaluation dataset
         backend/tests/sales_engagement/            5 test files
Lane B   frontend/tests/e2e/interaction-boundaries.spec.ts
         frontend/tests/e2e/pages/sign-in.ts
         frontend/tests/endurance/  ·  tests/unit/endurance/
```

**A module that appears in neither [`04-modules.md`](architecture/04-modules.md) nor [`README.md`](../README.md), containing a prompt release and an evaluation dataset, exists nowhere but one disk.** Those are the precise artifacts R-3 below calls production assets that must never be regenerated to recover them — **regenerating a prompt release produces a different artifact, not the same one back.**

> **The understatement is itself the evidence.** The measurement that justified this document was wrong in the direction that would have made the document unnecessary, and `infra/unsaved.py` inherited the same defect until a test was written for it. **A resilience tool that under-reports is worse than none**, because the number is believed.

### What the measurement removes from the brief

| Imagined incident | Actual exposure today |
|---|---|
| Branch deleted locally · remotely · force-push mistake · Git index corruption | **Covered.** Every branch is on `origin`; `main` additionally carries a certification manifest that binds each commit |
| Prompt datasets · evaluation artifacts lost | **Covered, and by design.** `prompts/manifest.json`, `prompts/*.md`, `evaluation/datasets/*.json` are **tracked files**. They were made repository artifacts because immutability required it (`CLAUDE.md` §10), and resilience came free |
| Docker volume loss · WSL corruption · machine rebuilt | **Covered by reproduction, not backup.** Every volume is rebuildable: `make demo` reconstructs the Playground from a tracked scenario, `make up` rebuilds the stack. **Verified this cycle** — `make dr` restarted every component and lost nothing |
| Disk failure · theft · `rm -rf` · directory deletion | **The seven paths above, and nothing else** |
| Review evidence deleted | **Real, and new this cycle.** `review/` is git-ignored by a decision recorded in `infra/review.py` |

> **Five of the six scenario classes are already covered, and none of them by a backup.** They are covered because the repository already treats prompts, datasets, scenarios and certification records as **tracked artifacts** rather than generated ones. **That is the resilience strategy, and it was arrived at for other reasons** — immutability, auditability, determinism. Resilience is what it produced.

---

## 2 · The four states, applied

The product owner's taxonomy, with every artifact in this repository placed in it. **The value of the taxonomy is that a misplacement is visible.**

| State | Meaning | Here |
|---|---|---|
| **Repository** | Committed. Survives everything git survives | Code · prompts · prompt manifests · evaluation datasets · scenarios · certification manifest and reports · architecture · registers · governance |
| **Generated** | Recreatable from the repository by a documented command | Playground data (`make demo`) · Docker images and volumes (`make up`) · coverage data · `node_modules` · `.venv` · every cache |
| **Versioned artifact** | Records something that *was* true. **Must be committed, and never edited** | Prompt releases · evaluation runs · certification records — **all tracked today.** ⚠️ **Review evidence is not** |
| **Disposable** | Never worth keeping | Caches · build outputs · lock files of a running process |

### Two misplacements, and they are the whole proposal

**⚠️ Review evidence is a versioned artifact stored as if it were disposable.** `review/` is git-ignored. The reasoning is recorded and still correct — committing it needs `--audit-main` to accept a new class of commit on `main`, which is governance — but *"we have not decided yet"* is a different state from *"disposable"*, and today the filesystem says the second.

**⚠️ Local environment files are irreplaceable and are in none of the four states.** `backend/.env`, `frontend/.env.local` and `infra/.env.prod-local` hold generated key pairs. They are **correctly** never committed (§13), and they are **not** reproducible — regenerating a JWT pair invalidates every existing session, and a mismatched pair mints tokens that 401 with no clue why. **A machine rebuild loses them**, and the recovery is "generate a new pair and update both tiers", which nothing documents as a procedure.

> **A fifth state is not the answer.** `.env` files are *reproducible by regeneration, at a stated cost*. What is missing is the command, not the category — see R-5.

---

## 3 · The proposed rules

**Six, matching the product owner's draft, each narrowed to what the measurement supports.** A rule with no exposure behind it is documentation.

### R-1 · Recoverability

**Every valuable engineering artifact is committed, reproducible by a documented command, or explicitly disposable.** A fourth answer — *"it is on my machine"* — is the one this rule exists to remove.

*Exposure:* 27 untracked files, measured above. *Enforced by:* `make unsaved` (RS-1, shipped). *Verified by:* a check that reports untracked non-disposable paths older than a session. *Retires when:* it reports zero for a sustained period across every lane, which would mean the habit holds without it.

### R-2 · Generated artifacts are never the only copy

**If something is classified *generated*, the command that generates it must exist, be documented, and be exercised.** A generated artifact whose generator has drifted is not generated; it is lost and nobody knows yet.

*Exposure:* none observed. **Listed because `make demo` was in exactly this state until this cycle** — classified reproducible, and [B-105](BUGS.md) shows it could not actually run on a clean workstation. *Verified by:* the generator running in a gate. *Retires when:* every generator is exercised by an existing gate, making the rule redundant.

### R-3 · Prompt assets are production assets

**Prompts, their manifests, evaluation datasets and release records are tracked files, reviewed like code, and never regenerated to recover them.**

*Exposure:* none — **already satisfied**, and recorded here so a future change cannot quietly move them out of the repository. *Retires when:* never foreseeably. A prompt release that is not a tracked file cannot be cited, which is a correctness property before it is a resilience one.

### R-4 · Review evidence survives workstation cleanup

**A product review's record outlives the environment that produced it.** *"What did we demonstrate before signing that contract?"* is unanswerable from a torn-down stack, and today it is unanswerable from a rebuilt laptop.

*Exposure:* **real and current.** `review/` is git-ignored. *Ruled 2026-08-03:* **the summary is committed; binary evidence stays external, named and hashed in a committed manifest** (§5). *Retires when:* never — it is the reason the Product Review Platform exists.

### R-5 · Machine independence

**A developer recreates a working environment from the repository plus documented commands.** Where a value cannot be committed — a key pair, a secret — the **procedure to regenerate it and the consequences of doing so** are documented as precisely as the value would have been.

*Exposure:* real. QE reconstructed `frontend/.env.local` this cycle by reading four files and writing an ad-hoc script; **nothing in the repository describes that as a procedure**, and the consequence (every existing session invalidated, both tiers must be updated together) is stated nowhere. *Verified by:* the procedure existing and being run. *Retires when:* a `make workstation` exists and is exercised.

### R-6 · Recovery is exercised, not assumed

**A recovery procedure that has never been run is documentation.** The repository already believes this about gates; it should believe it about recovery.

*Exposure:* partial — **`make dr` already does this for the running system** and passed this cycle: every component restarted, nothing lost, 360 invariants re-run. **Nothing does it for the workstation.** *Retires when:* never. This is the rule that keeps the other five honest.

---

## 4 · What QE proposes to build, and what it does not

**Ordered by exposure, which is not the order the scenarios suggested.**

| | | Why now | Size |
|---|---|---|---|
| ~~**RS-1**~~ | ~~An untracked-work check~~ | **✅ Shipped 2026-08-03** — `make unsaved`, `make unsaved ARGS=--workstation`. Always exits 0; `.gitignore` is the disposability classifier | **S** |
| **RS-2** | **`make workstation`** — regenerate `.env` files and key pairs, with the consequences stated | R-5's gap, hit by QE this cycle | **M** |
| **RS-3** | **Decide where review evidence lives** — a product-owner decision, not an implementation | R-4 is blocked on it and cannot be built around it | **decision** |

**Deliberately not proposed:**

| | |
|---|---|
| **A backup system** | Nothing measured is lost by a disk failure except the seven paths, and a commit fixes those. **A backup would be a second copy of what `origin` already holds** |
| **Automatic committing or auto-stashing** | It would defeat the reason the exposure exists: engineers experiment, and forcing tiny commits makes history worse. **The law targets recoverability, deliberately, not commits** |
| **A recovery runbook document** | Nobody reads a runbook during an incident they have never rehearsed. **R-6 says exercise it**; a document that is not exercised is the thing R-6 exists to reject |
| **Monitoring machine resources per lane** | Raised as a possibility and correctly deferred — one lane's memory growth is one observation, not evidence |

---

## 5 · Where review evidence lives — **RULED 2026-08-03, product owner**

> **The repository stores the summary. Binary evidence remains external.**

| **Committed** | **External** |
|---|---|
| review metadata · summary · findings · reviewer notes | screenshots · videos |
| certification reference · dataset version · playbook version | Playwright traces · HAR files |
| **screenshots manifest · hashes · fingerprints** | browser recordings · logs |

**Option B of the three considered**, and the reason it is right is that it is the shape the certification manifest already has: the record is committed and the evidence it points at is not. **The hashes are what make it more than a file list** — the repository can prove which image was shown, and detect one that has been replaced, without storing it.

**R-4 is unblocked.** The implementation is [`PRODUCT_REVIEW_PLATFORM.md`](PRODUCT_REVIEW_PLATFORM.md) §7 PR-3, and it requires `--audit-main` to accept a `review/` path class bounded to `.json` and `.md` — the binary exclusion enforced by the path rule rather than by care.

---

## 6 · The proposed Engineering Law

**Offered for ratification, not adopted.** [`ENGINEERING_LAWS.md`](../ENGINEERING_LAWS.md) requires an incident that already happened or a named failure mode in current code. **This has the second, measured**, and the product owner's framing is the right one — it is a near-miss rather than a loss.

> ### L-18 · No engineering work exists in only one physical location past the end of a working session
>
> **Why it exists.** Seven untracked paths across two lanes — new Playwright page objects, an endurance suite, an interaction-boundaries spec — existed in exactly one place on 2026-08-03. Every *committed* branch on the machine was pushed; the exposure was entirely pre-commit. **Nothing was lost, and that is the only reason this is a law rather than a retrospective.**
>
> **What it requires.** By the end of a working session, work is **recoverable** — committed, pushed to a branch, or stashed and pushed. **Not merged, not reviewed, not finished.** A WIP commit on a lane branch satisfies it; so does a pushed stash-branch. **Nothing about this demands small commits**, because forcing them would trade a resilience risk for a history quality one.
>
> **How it is enforced.** `make unsaved` (RS-1, shipped 2026-08-03): an advisory check at a session boundary, reporting untracked non-disposable paths. **Advisory rather than blocking**, because a lane mid-experiment is doing exactly what the law permits — the check is a reminder at a session boundary, not a gate.
>
> **What evidence proves it works.** The check reporting zero at the end of sessions where it reported non-zero at the start.
>
> **What would retire it.** **Sustained zero across every lane for a month** — which would mean the habit holds without the rule, and this file is one law lighter. *This is the first law written with a retirement condition that is plausibly reachable, and that is intentional.*
>
> **Who owns its ongoing validity.** QE, which runs the check and is the lane that measured the exposure.

---

## 7 · How this document is maintained

**QE re-measures §1 whenever this document is touched.** The table is a measurement of one moment; carried forward it becomes a claim about a repository that no longer exists — the same rule the certification metrics follow.

**A rule is removed when its retirement condition is met**, and the measurement that met it is recorded in the commit that removes it. **A rule set that only grows becomes impossible to evolve**, which is the reason retirement conditions exist at all.

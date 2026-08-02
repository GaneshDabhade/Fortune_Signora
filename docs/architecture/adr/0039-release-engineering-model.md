# ADR-0039 · Release Engineering — the integration model becomes architecture

**Status:** **Proposed.** Nothing in this document is in force. It changes no rule, no branch, no tool, and no commit. It is a design exercise requested by the product owner on 2026-08-02, to be ratified, amended or rejected as a whole.

**Author:** QE (Quality Engineering & Integration)
**Supersedes:** nothing. **Amends, if ratified:** `CLAUDE.md` §20e (*Branches and promotion*, *Completion*, *Repository Closeout*), [ADR-0032](0032-release-certification.md) (extends commit-binding upstream from certification to validation)

---

## 1 · Context — why an integration model needs designing at all

The repository's governance is stable. Certification is deterministic and commit-bound, work allocation is pull-based, module ownership is clear, and eleven certification cycles have all certified. **The constraint has moved: it is now the mechanics by which work travels from a lane to `main`.**

The same class of failure has recurred across cycles — replayed commits, duplicate SHAs, moving validation targets, claim visibility, branch synchronization conflicts, and the question nobody could answer mechanically: *was this work superseded, or was it lost?*

**One measurement makes the case better than the list does.**

```
  commits on `integration`, 2026-08-01 → 2026-08-02        66
    touching a shared narrative markdown file              54   (82%)
    touching backend/ frontend/ infra/ Makefile            30   (45%)
```

**Four out of five commits in this repository touch a file that every lane writes to.** Under a fast-forward-only policy every lane must rebase before merging, so four out of five commits are a conflict candidate on every rebase — and rebase conflict resolution is where commits get dropped.

**And one has been dropped.** As of this writing:

```
$ git cat-file -e 9c32daa && git for-each-ref --contains 9c32daa
9c32daa  exists in the object store · reachable from NO branch

$ git show --stat 9c32daa
TASK-005 — state-check reads the claims that have not merged yet
 backend/tests/test_claim_collisions.py | 177 +++++++++
 infra/state-check.py                   | 128 ++++++++
 … 365 insertions
```

**365 lines of implementation — a 177-line test file and 128 lines of governance tooling — are reachable from no branch in this repository.** They were committed, pushed, and fast-forwarded onto `integration`. They survive only as unreferenced objects in one clone, and `git gc` will remove them. A fresh clone does not have them. **Meanwhile Lane B has re-claimed TASK-005**, and will rebuild some part of what already exists.

That is the exact duplicate implementation the Task Claim Protocol was written to prevent, arriving through the register instead of through a race — recorded as [B-017](../../BUGS.md), where it is still, correctly, marked *"it may well have been deliberate, and that is the point."*

> **The repository cannot currently distinguish deliberate supersession from silent loss. That is not a defect to fix; it is a property of the integration model, and it is what this ADR is about.**

---

## 2 · Current integration architecture

### 2.1 · The lifecycle as built

```
   BACKLOG.md            lane branch                integration            main
   ──────────            ───────────                ───────────            ────
   READY task
      │ claim commit ──────────────────────────────────▶ (lane pushes)
      ▼
   CLAIMED ──▶ implement ──▶ rebase onto integration ──┐
                                  ▲                    │
                             (conflicts, 82%)          │
                                  │                    ▼
                             IN VALIDATION ──▶ QE validates the BRANCH
                                                       │
                                            QE pins CERT_SHA, certifies
                                                       │
                                            QE --ff-only ─▶ integration
                                                       │
                                            QE --ff-only ─▶ main ◀── Closeout commit
                                                       │              (main only)
                                            QE rebases integration ◀──┘
                                            QE fast-forwards idle lanes
```

### 2.2 · What each branch is currently responsible for

| Branch | Responsibilities it currently carries | Count |
|---|---|---|
| `lane-*` | Workspace · deliverable · validation target · claim vehicle · rebase target | **5** |
| `integration` | Shared mainline · pre-certification staging · claim arbitration ledger · rebase base · Closeout rebase target | **5** |
| `main` | Certified history · dashboard host · Closeout host | **3** |

**No branch has one purpose.** Every one of the recurring failures lives at a point where two of these responsibilities meet.

---

## 3 · Root-cause analysis

Seven root causes. Each is stated with the observed evidence, not as a hypothesis.

### RC-1 · The lane branch is simultaneously the workspace and the deliverable

A lane branch is mutable and rebased, yet it is also what QE validates and what gets merged. **Rebase rewrites every SHA**, so the object QE validated and the object that reached `integration` are different objects with no recorded relationship.

> [ADR-0032](0032-release-certification.md) fixed exactly this problem one stage later — *"a branch is a moving pointer; a certification is a statement about an immutable tree"* — and stopped at certification. **Validation still targets a moving pointer.**

**Observed:** Lane A's branch was `1a348ef` when QE opened validation and `d82325c` an hour later, with all twelve SHAs rewritten. Nothing about the first tip survives.

### RC-2 · Fast-forward-only × shared mutable files = mandatory rebase, and rebase is lossy

The ban on merge commits forces every lane to rebase. 82% of commits touch a file every lane writes. Therefore **almost every rebase conflicts**, and conflict resolution during a rebase offers `git rebase --skip` — a command that **discards a commit and leaves no record that it existed.**

**Observed:** `9c32daa` and `626e343`, unreachable, 365 lines, no record of the decision. **`git rebase --skip` is the loss mechanism, and it is one keystroke inside the operation the process mandates.**

### RC-3 · Ordering is achieved by rewriting, and a rewrite erases identity

Rebase produces a new commit with a new SHA and no link to its predecessor. Git records no "X was replaced by X′". So *replayed*, *superseded* and *lost* are indistinguishable after the fact.

**Observed:** Lane A's branch carried `a599201` and `945e120` — Lane B's M7 claim commits, already on `integration` as `4c4b0d3` and `0a86d7a` **with different SHAs and identical content**. Nothing in the repository connected the two pairs; it took a human reading commit subjects ([B-018](../../BUGS.md)).

### RC-4 · Coordination state is a multi-writer database stored as line-oriented markdown

`BUGS.md`, `LANE_COORDINATION.md`, `ACTIVE_ASSIGNMENTS.md` and `BACKLOG.md` are append-heavy, multi-writer, table-structured records that git merges **textually**. Git has no concurrency control for this; it has a diff algorithm.

**Observed, three distinct symptoms of one cause:**

| Symptom | Bug |
|---|---|
| Structural corruption — a stranded header and an orphan `\|---\|---\|` survived four certifications | [B-004 repair](../../BUGS.md) |
| Section inversion — every `OPEN` item filed under `## Closed`, because lanes append at end of file, which has been past the heading since it was introduced. Two tools then reported *"3 closed"* when the truth was *"0 closed"* | [B-021](../../BUGS.md) |
| Id collisions requiring QE to renumber `B-` and `C-` rows at merge | recorded in `BUGS.md` §*How the registers were reconciled* |

> **The repository already contains the proof of the fix.** `docs/architecture/adr/` is **one file per record**, written by every lane, and has produced **zero merge conflicts and zero structural corruption** in 39 records.

### RC-5 · Claim atomicity is grafted onto the content channel

The Task Claim Protocol arbitrates by pushing a claim commit to `integration`. It works — and it makes feature lanes writers of the shared mainline, and makes each claim a commit that must later survive somebody else's rebase.

**Observed:** `a599201` in RC-3 is a *claim* commit, replayed onto the wrong lane's branch.

### RC-6 · `main` and `integration` diverge by construction, every cycle

Closeout commits land on `main` only. `integration` therefore falls behind by exactly the Closeout on every cycle, requiring a forced rebase of `integration` — **eleven cycles, eleven forced rebases** — and a bounded exception in the certification rule to permit a commit on `main` that was never certified.

**This is GitFlow's `develop`/`master` divergence, arrived at accidentally.**

### RC-7 · The dashboard is a stored copy of a derivable fact

`PROJECT_STATUS.md` is measured from the promoted commit and then **written down**. The repository's own principle says a stored copy of a derivable fact is a defect waiting for the two to disagree (§2, *truth has exactly one authoritative representation*). It is the reason a Closeout commit must exist at all, and therefore the reason RC-6 exists.

---

## 4 · Comparison with mature industry release models

Studied for *why they evolved* and *what problem each solves*, not for imitation.

| Model | Problem it evolved to solve | Core mechanism | Applicable here? |
|---|---|---|---|
| **Trunk-Based Development** (Google, Meta, most high-throughput orgs) | Merge cost grows superlinearly with branch lifetime | Branch lifetime measured in hours; integrate continuously | **Partly — already adopted.** §20e's *"a slice lives two days maximum"* is TBD's central rule |
| **Google Piper + CitC + TAP** | Thousands of concurrent authors on one trunk | The **change (CL)**, not the branch, is the unit. **Submit is performed by the system**, which rebases and tests immediately before landing. TAP validates at trunk head continuously | **The principles, yes.** The infrastructure, no — it presumes a build fleet |
| **Chromium Commit Queue** | Tip-of-tree moves while a change is being tested | The CQ tests a CL **against tip-of-tree** and retries if the tree moved; release branches are immutable except for tracked cherry-picks | **The immutability of the tested artifact, yes.** The queue service, no |
| **Kubernetes / Tide** | Hundreds of contributors, no human should rebase | Automated **merge pool with batch testing**; `release-x.y` branches; cherry-picks carry explicit `Cherry pick of #N` provenance | **Explicit supersession provenance, yes.** The bot, no |
| **Linux kernel** | Thousands of contributors, no shared write access, no CI | **Maintainer hierarchy and pull requests. Merge commits are provenance, not pollution.** `linux-next` is an integration tree **rebuilt daily and explicitly disposable** — *no work lives only there*. Patch series carry explicit `v2`/`v3` supersession | **Directly, and more than any other.** It is the only model designed for an environment with no automated gatekeeper |
| **Android / Gerrit** | Rebase destroys the identity of a change under review | **`Change-Id` trailer** — a stable identifier in the commit message that survives rebase, amend and cherry-pick. Submission is server-side | **The `Change-Id` idea is the single most directly applicable thing in this table** |
| **GitHub Flow / GitLab Flow** | Small teams needing review + protected mainline | PR-based; merge commits; provenance in PR metadata | **Partly.** Provenance lives outside git, which ADR-0027 rules out |
| **GitFlow** | Versioned desktop software with long release stabilization | Long-lived `develop` + `release/*` alongside `master` | **No — and this is what the repository accidentally became** (RC-6) |
| **Microsoft engineering system** | Windows-scale monorepo, gated check-in | Merge queue / gated builds; VFS for Git | **The serialization principle only** |

### The five convergent principles

Every model above, independently, arrived at some subset of these:

1. **A change has a stable identity independent of its SHA** — Gerrit `Change-Id`, Chromium CL number, k8s PR number, kernel `Message-Id`.
2. **Integration is performed by a serializer, not by the contributing human** — CQ, Tide, Piper submit, the maintainer who pulls.
3. **The validated artifact and the promoted artifact are the same immutable object.**
4. **A long-lived integration branch is either avoided or declared disposable** — `linux-next` is rebuilt daily *because nothing is allowed to live only there*.
5. **Shared mutable coordination state does not live in the source tree** — issue trackers and review systems exist outside git precisely because git has no concurrency control.

**This repository already satisfies 2 and 3-at-certification. It satisfies none of 1, 4, or 5.** Principle 5 is in genuine tension with [ADR-0027](0027-local-first-development.md), which forbids external services — so the recommendation below satisfies it *inside* git, by removing the concurrency, not by adding a service.

---

## 5 · What to adopt

| # | Adopt | From | Solves |
|---|---|---|---|
| **A1** | **`Change-Id` trailer on every commit** | Gerrit / Android | RC-3 · makes replay, loss and supersession **mechanically detectable** |
| **A2** | **Immutable, tagged snapshots as the validation target** | Chromium CQ · ADR-0032's own logic | RC-1 · the validated object stops moving |
| **A3** | **Merge, don't rebase, into `integration`; `--first-parent` for readability** | Linux kernel · k8s | RC-2 · eliminates replay and `--skip` loss entirely |
| **A4** | **One file per record for every register** | The repository's own `adr/` directory | RC-4 · removes 82% of conflict surface |
| **A5** | **Explicit supersession provenance** (`Supersedes-Change:`) | k8s cherry-pick tracking · kernel `v2` | RC-3 · *"lost or superseded"* becomes a field, not an inference |
| **A6** | **Derived repository state** (`make status`) | Piper/TAP — trunk state is queried, not stored | RC-6 · RC-7 · deletes the Closeout commit, the divergence, and the certification exception together |

## 6 · What not to adopt, and why

| Rejected | Why |
|---|---|
| **GitFlow's long-lived `develop`** | It is RC-6. The correct move is to *remove* the divergence, not formalise it |
| **A hosted merge queue** (Tide, Zuul, CQ, GitHub merge queue) | [ADR-0027](0027-local-first-development.md): *"a `git push` performs one action"*. **The principle is adopted without the service** — QE is already a single-threaded serializer, which is what a merge queue is |
| **Gerrit as a server** | The value is the `Change-Id`, which is a commit-message trailer and needs no server |
| **Feature-flagged direct-to-trunk commits** | Real TBD trades branch isolation for flag infrastructure and production telemetry. The repository has neither, and [ADR-0020](0020-feature-flags.md) is unbuilt. **Premature** |
| **CitC / VFS for Git** | Solves a scale problem three orders of magnitude away |
| **Release branches with tracked cherry-picks** | Correct, and **not yet needed** — there is no released version to patch. Revisit at M14.5 |
| **An external issue tracker for the registers** | Would satisfy convergent principle 5 directly, and violate ADR-0027. **A4 achieves the same result inside git** |

---

## 7 · Recommended target architecture

### 7.1 · One purpose per branch

| Branch | **Exactly one** responsibility | Mutable? | Who writes |
|---|---|---|---|
| `lane-*` | **The lane's workspace.** Where a slice is written | Yes, freely, until the slice is offered | The lane only |
| `slice/<task>/<n>` | **The immutable deliverable.** A tag, not a branch — created when the lane offers a slice, never moved | **No** | The lane creates; nobody edits |
| `integration` | **The single shared mainline.** Every slice arrives here by merge, in order | Append-only. **Never rebased, never rewritten** | QE only |
| `main` | **The certified subset of `integration`.** A pointer, nothing more | Fast-forward only | QE only |
| `cycle/<nnnn>` | **The immutable release snapshot.** What was validated, certified and promoted | **No** | QE creates |

**`main` becomes what it should always have been: a pointer into `integration`'s history that lags by exactly the uncertified tail.** It never carries a commit `integration` does not have, so the two can never diverge, and the bounded Closeout exception in §20e becomes unnecessary rather than merely bounded.

### 7.2 · The lifecycle

```
  PRODUCT OWNER        LANE                          QE (release engineering)
  ─────────────        ────                          ────────────────────────

  docs/backlog/
   TASK-018.md
       │
       │  claim = create docs/claims/TASK-018.md
       │           (same path ⇒ push collides ⇒ arbitration is free)
       ▼
   READY ──────▶ implement on lane-*
                 every commit carries Change-Id
                      │
                      │  merge integration INTO the lane  ◀── lane resolves, once,
                      │  (never rebase — SHAs survive)         keeping its own SHAs
                      ▼
                 tag slice/TASK-018/1  ── immutable ──────▶  validate the TAG
                      │                                          │
                      │  lane claims the next task               │  merge --no-ff
                      │  immediately (unchanged)                 │  slice/… ▶ integration
                      ▼                                          │  (conflict-free by
                  next slice                                     │   construction)
                                                                 ▼
                                                       tag cycle/0012 at integration
                                                                 │
                                                       certify cycle/0012  (ADR-0032,
                                                                 │          unchanged)
                                                       main --ff-only ▶ cycle/0012
                                                                 │
                                                       make status ─ derived, not stored
                                                                 │
                                                       Repository Ready
```

### 7.3 · The six mechanisms

**A1 · `Change-Id`.** Every commit carries a trailer generated once by a local `commit-msg` hook:

```
Change-Id: I8f3c1a94e6b27d05f1a2c8e4b7d09f3a6c15e802
```

Git preserves commit messages across rebase, cherry-pick and amend, so **the identity survives every operation that destroys the SHA.** From this, three questions become one script:

| Question | Answer |
|---|---|
| Was this replayed? | The same `Change-Id` appears under two SHAs |
| Was this lost? | A `Change-Id` that reached `integration` is unreachable from `main`, with no supersession record |
| Was it superseded? | A later commit carries `Supersedes-Change: <id>` |

**`infra/change-ledger.py` answers all three and refuses a promotion that would lose a change.** This is the mechanism that would have made B-017 impossible to create silently.

**A2 · Immutable slice and cycle tags.** A slice is offered by *tagging*, not by pushing a branch. The tag is the validation target. If the lane discovers a problem, it fixes it and offers `slice/TASK-018/2`; version 1 remains in history, exactly as a Gerrit patchset does. **Nothing QE is validating can move underneath it, ever.**

**A3 · Merge, not rebase.**

- **The lane merges `integration` into its branch** to resolve conflicts. It resolves its own conflicts — **unchanged from §20e** — but its SHAs survive, and no commit can be dropped by `--skip`.
- **QE merges the slice tag into `integration` with `--no-ff`.** Because the lane already merged, this merge is conflict-free by construction; QE never adjudicates code it did not write — **also unchanged from §20e, and now structurally true rather than procedurally hoped for.**
- The merge commit records provenance: which slice, which lane, which task.

**On the three stated reasons for fast-forward-only:**

| Stated reason | Assessment |
|---|---|
| *"Alembic's chain is linear"* | **A non-sequitur.** Alembic linearity is a property of `down_revision` in file content, not of git history. Two lanes authoring migrations concurrently create an Alembic branch under **either** strategy — Lane A is adding `0026` and `0027` right now — and the fix is editing `down_revision`, which merge and rebase require equally |
| *"Records are append-only narratives"* | **Inverted by measurement.** Append-only narratives conflict *more* under rebase, because every commit is replayed separately against the same file. A4 removes the problem at its source |
| *"Linear history is readable"* | **Real, and preserved.** `git log --first-parent` on a merge-based history yields exactly the changelog `--oneline` gives today. It is what the kernel and Kubernetes rely on for the same purpose |

**A4 · One file per record.**

```
docs/bugs/B-018.md            docs/coordination/C-021.md
docs/backlog/TASK-018.md      docs/claims/TASK-018.md
```

Each with a small typed front-matter block (`id`, `severity`, `status`, `module`, `assignee`) and prose below. **`BUGS.md`, `LANE_COORDINATION.md`, `BACKLOG.md` and `ACTIVE_ASSIGNMENTS.md` become generated indexes** — `make registers` — never hand-edited.

This removes, structurally: register merge conflicts · section inversion (B-021 — status is a field, and there is no heading to append past) · prose-parsing fragility (B-020 — the `Task` field is a field) · id renumbering at merge (creating the same filename collides on push, visibly) · and the register half of the 82%.

**And the claim race resolves itself for free:** two lanes claiming TASK-018 both create `docs/claims/TASK-018.md`, so **the second push is rejected by git.** The arbitration the Task Claim Protocol performs in ten steps becomes a property of the filesystem.

**A5 · Explicit supersession.** `Supersedes-Change:` in the commit message, and a required field when a lane or QE deliberately drops work. **Dropping a change without recording supersession fails the ledger check.**

**A6 · Derived repository state.** `PROJECT_STATUS.md` is generated by `make status` from the certification manifest, git, and the registers — the thing the repository already insists on in prose (*"measured, never transcribed"*) made structural.

**Consequences, and they are the point:** no Closeout commit is needed on `main` · `main` and `integration` stop diverging · the eleven-times-per-eleven-cycles forced rebase of `integration` disappears · [ADR-0032](0032-release-certification.md)'s bounded exception for uncertifiable Closeout commits becomes unnecessary · and `--audit-main`'s special case for "a Closeout commit that provably changes nothing executable" can be deleted rather than maintained.

### 7.4 · Answering the four focus questions directly

| Question | Recommendation |
|---|---|
| **Should feature branches be rebased after `IN VALIDATION`?** | **No — and they should not be the validation target at all.** The lane offers an **immutable tag**; the branch keeps moving because the lane keeps working. A correction produces version 2, not a rewrite of version 1 |
| **Should `integration` become the authoritative implementation artifact?** | **Yes.** Append-only, never rewritten, the single mainline. `main` becomes a pointer into it |
| **What should validation operate on?** | **An immutable SHA, named by a tag.** A tag is pushed, immutable, human-referenceable, and survives branch movement — which a SHA in a session's memory does not. **Validate the slice tag; certify the cycle tag** |
| **How do replay, supersession and loss become impossible or detectable?** | **Merge instead of rebase makes replay and `--skip` loss impossible** (SHAs are never rewritten). **`Change-Id` plus the ledger makes every remaining case mechanically detectable**, and `Supersedes-Change` makes deliberate removal a recorded decision rather than an absence |

---

## 8 · Governance changes required

**None are made by this ADR.** If ratified:

| § | Change |
|---|---|
| §20e *Branches and promotion* | The branch table gains `slice/*` and `cycle/*`; **rebase-onto-`integration` is replaced by merge-`integration`-into-lane**; `--ff-only` is retained for `main` and dropped for `integration` |
| §20e *Completion* | Step 3 becomes *merge `integration` in*; step 6 becomes *tag and push the slice*; step 12 (synchronize) **is deleted** — nothing diverges |
| §20e *Repository Closeout* | Activity 10 (*rebase `integration` onto `main`, always*) **is deleted**. Activities 1 and 5 become *run `make status`* |
| §20e *Task Claim Protocol* | Shortens from ten steps to four: **create the claim file, push, and read the result of the push.** Steps 6–9 exist to simulate an atomic test-and-set that the filesystem now provides |
| §20e *Shared files have one owner* | Register rows become files; the ownership rules are unchanged, and are now enforceable per file |
| [ADR-0032](0032-release-certification.md) | Extended: certification binds to a **cycle tag**. The bounded Closeout exception is **removed**, not narrowed |
| §2 | One new sentence, and it is the ADR in a line: **work leaves the repository only by a recorded decision** |

**Everything the product owner asked to preserve is preserved:** pull-based claiming (strengthened — arbitration becomes atomic), module ownership, independent lanes, deterministic certification, commit-bound promotion, executable-slice delivery, repository state updates, architectural ownership, product-first development.

## 9 · Tooling changes required

| Tool | Change | Size |
|---|---|---|
| `.githooks/commit-msg` | Generate `Change-Id` if absent | ~20 lines |
| `infra/change-ledger.py` | **New.** Detect replay, loss, supersession; refuse a promotion that loses a change | ~200 lines |
| `infra/registers.py` | Parse record **files** and front-matter instead of markdown tables. **Simpler than today** | net negative |
| `infra/render-registers.py` | **New.** Generate the four index documents | ~150 lines |
| `infra/state-check.py` | Rules 3, 5b, 5c, 5d **deleted** — each checks a failure the new model makes impossible | net negative |
| `infra/certification-guard.py` | `--audit-main`'s Closeout special case **deleted**; certification binds to a cycle tag | net negative |
| `infra/status.py` | **New.** Derive `PROJECT_STATUS.md` | ~250 lines |
| `Makefile` | `make registers` · `make status` · `make ledger` | ~10 lines |

> **Net: roughly 630 lines added, and four categories of checking deleted.** The test of A4 and A6 is not that they add tooling — it is that they let checks be **removed**, because the failure they guarded no longer has a way to occur. Where a check can only be deleted by weakening a guarantee, it is kept.

## 10 · Migration strategy

**Six phases. Each is independently valuable, independently reversible, and none blocks feature work.** Phases 1–2 alone would have prevented every incident in §3.

| Phase | Does | Risk | Reversible by |
|---|---|---|---|
| **0 · Recover** | **Restore `9c32daa` and `626e343` to a branch before `git gc` removes them**, then decide and record: superseded, or re-integrated. **Do this first and independently of ratification** | None | — |
| **1 · Identity** | `Change-Id` hook + `infra/change-ledger.py`, reporting only. **No behaviour change whatever** | None — a trailer nothing yet reads | Deleting a hook |
| **2 · Immutability** | Slice tags and cycle tags. Validation and certification target tags | Low | Tags are additive |
| **3 · Registers** | Records become files; indexes generated | **Medium** — a mechanical conversion of ~40 records, and lanes must land their in-flight work first | The generated indexes are byte-comparable with today's |
| **4 · Merge** | Merge-based integration; `--first-parent` becomes the reading convention | **Medium** — the largest habit change | Rebase still works; policy revert only |
| **5 · Derived state** | `make status`; delete the Closeout commit, the divergence, and the certification exception | Low, once 1–4 hold | Re-committing a static dashboard |

**Sequencing constraint:** phase 3 before phase 4. Converting registers while also changing the merge strategy would make the first merge-based cycle also the first cycle with a new register format, and a failure in either would be indistinguishable.

**Phase 0 is not conditional on this ADR.** Unreferenced objects are one `git gc` from gone.

## 11 · Risks and trade-offs

| Risk | Severity | Mitigation |
|---|---|---|
| **Merge commits reduce `git log --oneline` legibility** — a real loss, and §20e values that log as a changelog a cold session reads | Medium | `git log --first-parent --oneline` is identical to today's output. Make it the documented convention and the default in `make` targets |
| **Generated indexes drift from their source files** — a stored copy of a derivable fact, which is the defect A6 exists to remove | Medium | Generate at check time; `state-check` fails if the committed index differs from the regenerated one. **Never hand-edit** |
| **A lane forgets the `Change-Id` hook** in a fresh clone | Medium | `state-check` refuses a commit without one; `make setup` installs hooks |
| **Phase 3 is a big mechanical diff** across every in-flight branch | Medium | Perform it in a cycle where every lane is `AVAILABLE`. That state occurs regularly and is visible on the board |
| **The model is designed for 2–3 lanes and evaluated at 2** | Low | §12 analyses the scaling behaviour; every mechanism is order-independent |
| **This is a large change to a system that currently works** | **Highest** | **Phases 1 and 2 deliver most of the safety for almost none of the disruption.** If only two phases are ratified, ratify those. Nothing later depends on doing them all |
| **Time spent here is time not spent on product** | **The one that matters** | §13 |

**Trade-offs accepted, plainly:** a merge-based history is less linear than today's · one file per record is more files and one more generation step · tags accumulate (cheap, and they are the record) · `Change-Id` adds a line to every commit message.

**Trade-offs refused:** nothing here slows a lane down. The lane's loop is unchanged except that *rebase* becomes *merge*, and the claim protocol gets **shorter**. Throughput is not traded for determinism anywhere in this design.

## 12 · Long-term scalability

| Property | Today, at N lanes | Target, at N lanes |
|---|---|---|
| Shared-file conflicts | **O(N²)** pairwise, on 82% of commits | **~0** — records are separate files |
| Rebases per cycle | **O(N)**, each a chance to drop a commit | **0** — merges, which cannot drop one |
| Forced `integration` rebases | **1 per cycle, always** | **0** — nothing diverges |
| Claim arbitration | 10 protocol steps, correctness by discipline | **1 push, correctness by git** |
| *"Was work lost?"* | **Unanswerable** | **`make ledger`** |
| QE serialization | Real, and it is correct that QE serializes | Unchanged — but per-merge work becomes O(1) and mechanical |

**The serialization point stays and should stay.** Every model in §4 has one, because *"integration is performed by a serializer"* is convergent principle 2. **What changes is that QE's per-merge cost stops scaling with how much the tree moved while it worked.**

**Where this model stops working:** somewhere past 6–8 concurrent lanes, QE's single-threaded validation becomes the limit — and at that point the answer is the one every organisation in §4 reached: **an automated merge queue.** That requires automated remote execution, which [ADR-0027](0027-local-first-development.md) forbids today and revisits when the architecture stabilises. **This design is the correct one for the interval between here and there**, and it is deliberately the same shape, so that adopting a queue later replaces the operator without redesigning the model.

## 13 · Final recommendation

> **Adopt phases 0, 1 and 2 now. Ratify 3–5 as direction and schedule them into cycles where the board is quiet.**

**Phase 0 is urgent and unconditional** — 365 lines of implementation are one `git gc` from permanent loss.

**Phases 1 and 2 are cheap, additive, reversible, and deliver most of the safety.** `Change-Id` plus immutable validation targets would have made B-017, B-018 and the replayed claim commits either impossible or automatically detected, and neither changes how anybody works.

**Phases 3–5 are where the 82% goes away**, and they are the ones worth doing deliberately rather than quickly.

**Against the product-first test — *does this make it easier to build and release the best possible product?*** — the honest answer for each phase:

| Phase | Answer |
|---|---|
| 0 · Recover | **Yes.** Rebuilding lost work is the most expensive thing a repository can ask a lane to do |
| 1 · Identity | **Yes.** It removes a question that currently costs a human investigation each time |
| 2 · Immutability | **Yes.** QE stops re-validating a moving target; lanes stop being blocked by a rebase they did not cause |
| 3 · Registers | **Yes, and it is the largest single win** — 82% of commits stop being conflict candidates |
| 4 · Merge | **Yes, indirectly.** It ends a whole class of loss, at the cost of a less linear log |
| 5 · Derived state | **Marginal.** It deletes real complexity, but no lane is currently blocked by it. **Do it last, or not at all** |

**Phase 5 is included for completeness and is the one to drop first if this is too much.** The rest earn their place.

---

## 14 · Consequences

- [ADR-0032](0032-release-certification.md) gains a cycle tag and loses an exception.
- §20e loses a synchronization stage, six protocol steps, and four `state-check` rules — **the review's best evidence that it is the right direction is how much governance it deletes.**
- `docs/BUGS.md`, `docs/LANE_COORDINATION.md`, `docs/BACKLOG.md` and `docs/ACTIVE_ASSIGNMENTS.md` become generated artifacts; their ownership rules survive unchanged and become enforceable per file.
- **No module, no boundary, no event contract, no schema and no product behaviour is affected.** This ADR is entirely about how work travels, and not at all about what the work is.

---
---

# Part II · First principles — what would emerge if we designed this today

**Added 2026-08-02, at the product owner's direction, before ratification.** Part I began with the repository's git workflow and improved it. **Part II deliberately does not.** It asks what release architecture would emerge if this repository had no branching strategy at all, and only afterwards compares that with what exists — because a review that starts from the current model can only ever optimise around it.

**Two technical claims in Part II were verified experimentally rather than asserted.** Both are load-bearing, and both are reproduced in §II-3.

---

## II-1 · First-principles release architecture

### II-1.1 · What the system actually is, with git removed

Strip away branches, and the repository is a system with:

- **one prioritized work queue**, written by one author;
- **N concurrent workers** that must not duplicate each other;
- **a body of source** that must move forward without losing contributions;
- **a proof obligation** — some states are provably fit to publish, most are not;
- **one published sequence** that consumers depend on.

It must be able to answer, at any instant and without ambiguity:

| # | Question | Nature of the answer |
|---|---|---|
| 1 | What work exists? | An ordered set |
| 2 | Who holds what? | A **mutual-exclusion** problem |
| 3 | What has been contributed? | An **immutable, identified** artifact |
| 4 | In what order was it accepted? | A **total order** |
| 5 | What has been proven, and about which exact state? | An **annotation on an immutable object** |
| 6 | What is published? | A **checkpoint** into that order |
| 7 | What was removed, and by whose decision? | An **append-only record of exceptions** |

> **These are seven independent facts with seven different concurrency profiles. The repository currently encodes all seven in one mutable structure — the branch topology plus hand-edited markdown in the working tree.** That is the architectural error. Rebase-versus-merge is a symptom of it, not the cause.

### II-1.2 · What each fact needs, chosen on its own merits

| Fact | Correct primitive, from first principles | Why |
|---|---|---|
| **Queue** | Independent records, one author | Single-writer: no concurrency problem exists. Any storage works; the only requirement is that concurrent *readers* never conflict |
| **Claim** | **Compare-and-swap on a unique key** | Mutual exclusion has exactly one correct solution shape. A protocol that *simulates* CAS with ten ordered steps is a distributed lock implemented in prose |
| **Contribution** | **Immutable, content-addressed, stably identified, versioned** | If it can be rewritten, "what was validated" is unanswerable. If identity dies with the SHA, supersession and loss are indistinguishable |
| **Order** | **Append-only log with a single serializer** | Total order requires serialization. Append-only is what makes loss impossible rather than merely detectable |
| **Proof** | **Annotation keyed by the hash of the proven state, stored outside it** | A proof about state X must name X. If it is stored *inside* X it changes X, and the record can never describe the thing that carries it |
| **Publication** | **A checkpoint pointer into the log** | Nothing more. A published state is a position, not a copy |
| **Removal** | **An explicit, append-only exception record** | The only way "lost" and "superseded" can differ is if one of them is written down |

### II-1.3 · The architecture that emerges

```
   WORK                CONTRIBUTION           ORDER + PROOF            PUBLICATION
   ────                ────────────           ─────────────            ───────────

   queue records       lane workspace         serializer               checkpoint
   (one per task,      (private, mutable,     ┌──────────────┐
    single author)      disposable)           │ candidate =  │
        │                    │                │ order + slice│
        │  CAS claim         │  offer         │      ↓       │
        ├──────────────▶ ────┴────▶ immutable │  certify     │
        │  (unique key)       slice artifact  │      ↓       │        ┌─────────┐
        │                     + stable id     │ pass → adopt ├───────▶│ trunk   │
        │                                     │ fail → drop, │        │ every   │
        │                                     │   with a     │        │ state   │
        │                                     │   reason     │        │ proven  │
        │                                     └──────────────┘        └─────────┘
        ▼                                              │                    │
   projections  ◀────────────── derived ───────────────┴────────────────────┘
   (queue · board · bugs · dashboard · release notes)
```

**Six properties fall out of the shape, not out of any rule:**

1. **Nothing that has been contributed can leave without a written decision** — the log is append-only, so removal is an act rather than an absence.
2. **What was validated and what was published are the same object** — the candidate *becomes* the published state; it is not re-derived.
3. **Two workers cannot take one task** — CAS, not protocol.
4. **Repository state cannot be stale** — it is a projection, and a projection is rebuilt, never maintained.
5. **There is exactly one long-lived name** — the trunk. Everything else is either private, immutable, or ephemeral.
6. **The proof travels with the thing proven**, and is not part of it.

**Notice what is absent.** There is no permanent integration branch, no synchronization step, no branch-reset ceremony, no reconciliation pass, no dashboard to keep current, and no ten-step protocol. **Not because they were removed — because nothing in the derivation ever produced them.**

---

## II-2 · Assumptions challenged

Every assumption the current model rests on, tested against §II-1 rather than against its own history.

| # | Assumption | Verdict |
|---|---|---|
| 1 | **A permanent `integration` branch is necessary** | **Retire.** It names the window between *merged* and *certified*. That window is **6.5 minutes** — the measured mean certification time. A permanent branch for a six-minute state is what produced the divergence, the eleven forced rebases, and the certification exception |
| 2 | **Validation happens after merge** | **Retire.** Validating after merge means a failure has already entered the shared line and must be removed — the operation that loses work. **Validate the merge *result* before adopting it** (speculative merge). Failure then costs nothing but a discarded candidate |
| 3 | **A branch is the unit of validation** | **Retire.** A branch is a mutable name. ADR-0032 established this for certification and stopped one stage short |
| 4 | **Lane branches must be permanent by name and reset after each merge** | **Retire.** With immutable slice artifacts, a lane branch is a private scratchpad. Permanence buys nothing and costs a reset ceremony |
| 5 | **Feature branches must survive after their slices merge** | **Retire.** The slice artifact survives; the branch need not |
| 6 | **Registers are documents that lanes edit** | **Retire.** They are **projections**. [B-021](../../BUGS.md) was never a corruption bug — it was a hand-maintained projection drifting from its source, which is what hand-maintained projections do |
| 7 | **The certification record must live in the working tree** | **Retire — and this is the keystone.** It is the sole reason ADR-0032 needs a bounded exception, `--audit-main` needs a Closeout special case, and `main` needs commits `integration` does not have. **See §II-3** |
| 8 | **`PROJECT_STATUS.md` must be maintained** | **Retire.** Derived. The repository's own §2 already says a stored copy of a derivable fact is a defect waiting to happen |
| 9 | **Claiming requires a ten-step protocol** | **Retire.** It is a compare-and-swap written out longhand. **See §II-3** |
| 10 | **Fast-forward-only everywhere** | **Split.** Keep for the trunk — a checkpoint should only advance. Retire for integration, where it is the direct cause of mandatory rebase |
| 11 | **The queue and the board are separate documents** | **Retire the duplication, keep the separation.** The board is derivable from claims: *who holds which task* is exactly the set of claim keys |
| 12 | **QE must synchronize branches after every cycle** | **Retire.** Only divergent things need synchronizing |
| 13 | **A single serializer is required** | **Keep.** Convergent across every system in §4 and §II-5. Total order requires it |
| 14 | **Certification binds to an immutable commit** | **Keep, and extend.** The best decision in the repository's governance history |
| 15 | **Work is pulled, never assigned** | **Keep, and strengthen** — CAS makes the pull safe rather than merely disciplined |
| 16 | **One assignee per module** | **Keep.** An architectural invariant, unrelated to release mechanics |
| 17 | **All verification is local** ([ADR-0027](0027-local-first-development.md)) | **Keep. It is a binding constraint on this design, and the design satisfies it** — every mechanism below is a local git operation with no service |
| 18 | **Only executable change opens a cycle** | **Keep** |
| 19 | **Lanes never idle waiting for QE** | **Keep. Non-negotiable** — it is the throughput property everything else must not damage |

## II-3 · The two verified mechanisms

Both were tested against a scratch repository rather than reasoned about, because both replace a governance rule with an architectural guarantee, and a guarantee that turns out not to hold would be Decorative Logic at the scale of the whole process.

### II-3.1 · A claim is a ref, and git enforces mutual exclusion

```bash
# Lane A
git push origin HEAD:refs/claims/TASK-018
 * [new reference]   HEAD -> refs/claims/TASK-018

# Lane B, same task, same moment
git push origin HEAD:refs/claims/TASK-018
 ! [rejected]  (fetch first)

# Lane B, trying harder — expecting-absent lease
git push --force-with-lease=refs/claims/TASK-018: origin HEAD:refs/claims/TASK-018
 ! [rejected]  (stale info)
```

**The second lane cannot win, and cannot force its way past.** This is a genuine compare-and-swap, enforced by the remote, requiring no service, no protocol and no discipline.

**What it deletes:** Task Claim Protocol steps 6, 7, 8 and 9 — *commit it alone*, *push the claim to `integration`*, *pull and rebase again*, *if somebody else claimed it first, abandon*. Those four steps exist to simulate exactly this operation. **It also removes the one exception that lets a feature lane write to `integration`**, and with it `certification-guard.py --audit-claims`, whose whole job is checking that claim commits carry nothing else. **A claim stops being a commit, so it can never be replayed, rebased, conflicted, or dropped** — which is precisely what happened to `a599201` in [B-018](../../BUGS.md).

**The board becomes a projection:** `git ls-remote origin 'refs/claims/*'` *is* the answer to *"who holds what?"*, and it cannot disagree with itself.

### II-3.2 · The proof attaches to the commit without being inside it

```bash
C=$(git rev-parse HEAD)
git notes --ref=certification add -m '{"commit":"'$C'","certified":true,...}' $C
git rev-parse HEAD        # unchanged — the commit is not rewritten
git push origin refs/notes/certification
# from a fresh clone:
git fetch origin 'refs/notes/*:refs/notes/*'
git notes --ref=certification show $C   →  the record
```

**A commit can carry its own certificate.** ADR-0032 states the opposite as a law:

> *"A certification record cannot contain its own commit hash, so the commit that writes the record is always created after the run it records."*

**That is true of a record stored in the tree, and false of a record stored beside it.** It is an artifact of the storage choice, not a property of certification — and the entire chain of consequences hangs off it:

```
  record lives in the tree
        └─▶ Closeout must be a commit
              └─▶ that commit cannot be certified
                    └─▶ ADR-0032 needs a bounded exception
                          └─▶ --audit-main needs a path allowlist  (and B-014 came from it)
                                └─▶ Closeout lands on main only
                                      └─▶ main and integration diverge every cycle
                                            └─▶ 11 forced rebases of integration
                                                  └─▶ a synchronization stage exists at all
```

**Move the record out of the tree and the whole chain collapses at the top.** `refs/notes/certification` is itself a git history — append-only, pushable, auditable, and every past certification is `git log refs/notes/certification`.

**This is the single highest-leverage finding in either part of this ADR**, and Part I did not see it, because Part I started from the branch topology and this problem is not visible from there.

---

## II-4 · Which assumptions remain valid

**The execution model is not what needs changing, and this review does not touch it.** Independent feature lanes · pull-based execution · module ownership · deterministic certification · commit-bound promotion · executable-slice delivery · architecture-first implementation · product-first decision making — **all preserved, and three of them strengthened**: claiming becomes atomic rather than disciplined, commit-binding extends from certification to validation, and executable-slice delivery gets faster because the merge ceremony around it shrinks.

**What was right all along, and is worth stating because the rest of this document is a list of corrections:**

- **The single serializer.** Every system in §4 and §II-5 has one. QE's role is correct.
- **Commit-bound certification.** ADR-0032 is the best decision in the repository's governance history; Part II extends it, and contradicts nothing in it except a storage assumption.
- **Local-first.** It is a real constraint, and it is what rules out every off-the-shelf merge queue. **The design satisfies it with no service and no daemon.**
- **Lanes never wait for QE.** Preserved exactly.

## II-5 · Comparison with mature systems, by discipline

Part I compared *release workflows*. Part II compares the **disciplines** the repository actually resembles.

| Discipline | Principle extracted | Where it lands |
|---|---|---|
| **Database concurrency** | The registers are a table with no transactions: lost updates ([B-017](../../BUGS.md)), phantom reads (a stale queue), and no unique constraint (id collisions QE renumbers at merge). The four fixes are textbook: **unique constraint** → ref/path uniqueness · **serializable isolation** → single serializer · **MVCC snapshot** → immutable candidate · **WAL + checkpoint** → append-only log with a published pointer | II-1.2, II-3.1 |
| **Event sourcing** | **One write model, many read models.** Commits, refs and notes are the events; the registers and the dashboard are **projections**, rebuilt rather than maintained. A corrupt projection is not a defect — it is a rebuild | II-1.3 fact 4 |
| **Queueing** | A claim is a **lease**. Today it has no expiry, so an abandoned claim blocks a task indefinitely, with only human observation to catch it. A ref-based claim carries its commit time, and staleness becomes a check | II-3.1 |
| **Distributed systems** | **Idempotence** — advancing a checkpoint to an already-published state is a no-op, so promotion can be retried safely. **At-least-once with dedup** — a contribution offered twice is one change with a stable id. **Linearizability** — from the serializer. **Partition tolerance** — lanes already work offline, which is what git is for | throughout |
| **Build engineering** | **Hermetic, content-addressed artifacts with provenance.** A build output is identified by the hash of its inputs, and a build that cannot say what went into it is not reproducible. Applied here: the slice artifact is the input, the candidate is the output, and the note is the provenance | II-1.3 |
| **Release engineering** | **Cut, prove, publish, and never edit what was published.** Also: **a release is a decision recorded about an artifact, never a property of a branch** — which the repository already believes | II-1.3 |
| **Monorepo engineering** | **Presubmit against the state you will actually land on**, because a change validated against a stale tree is validated against nothing. This is the argument for speculative merge, and against validating a lane branch | II-2 #2 |

## II-6 · Alternative end-state architectures

Four credible end states, described honestly enough to be chosen against.

### Option A · Evolve the current model — Part I, phases 1–5

Keeps `integration` as a permanent branch. Adds `Change-Id`, slice tags, merge-based integration, file-per-record registers, derived status.

**For:** smallest conceptual change; every step reversible; no unfamiliar git surface.
**Against:** **keeps assumptions 1, 2, 7 and 9** — so it keeps the divergence, the synchronization stage, the certification exception and the ten-step protocol. It makes the current model safe rather than making it simple.

### Option B · Merge-queue trunk — *recommended*

One permanent branch. Immutable slice artifacts. Ephemeral certified candidates. Claims as refs. Certification as notes. Registers and dashboard as projections.

```
  lane-*          private, mutable, disposable      the lane's workspace
  slice/<id>/<n>  immutable, versioned              the offer
  cand/<n>        ephemeral                          order + slice, before proof
  main            append-only, every state proven    the only permanent branch
  refs/claims/*   CAS                                who holds what
  refs/notes/*    append-only annotation             what was proven, about what
```

**For:** every failure class in Part I §3 becomes structurally impossible rather than detectable; **deletes more governance than it adds**; keeps every strength in §II-4; runs entirely locally.
**Against:** topology change; `refs/claims/*` and `refs/notes/*` are unfamiliar and are **not fetched or pushed by default**; a failed candidate must be attributed to a slice.

### Option C · Patch-series, kernel style

Contributions are versioned patch series; the integrator applies them; supersession is explicit (`v2`, `v3`).

**For:** the most loss-resistant model in existence; needs no shared write access at all.
**Against:** ceremony calibrated for thousands of contributors and dozens of maintainers. **At two or three lanes with one integrator it is pure overhead**, and it would slow the product down — which §II-9 rules out.

### Option D · Change-first, no branches at all (Sapling / Phabricator / stacked diffs)

The unit is a *change* with a stable id; branches disappear entirely; changes stack and land independently.

**For:** the cleanest expression of §II-1; scales furthest; **its identity model is already Option B's `Change-Id`**.
**Against:** requires a client and a server the repository would have to build. **Correct destination, wrong decade.** Option B is deliberately shaped so that D remains reachable.

## II-7 · Trade-offs, compared

| | **A · Evolve** | **B · Merge-queue trunk** | **C · Patch series** | **D · Change-first** |
|---|---|---|---|---|
| Loss impossible? | Detectable | **Impossible** | Impossible | Impossible |
| Permanent branches | 2 + N lanes | **1 + N private** | 1 | **0** |
| Governance rules removed | 4 | **~14** | ~6 | ~16 |
| New concepts a lane must learn | 2 | **3** | 4 | 5 |
| Tooling to build | ~630 lines | **~700 lines** | ~400 | thousands |
| Local-first compatible | Yes | **Yes** | Yes | No, as bought |
| Migration risk | Medium | **Medium-high, phased to low** | High | Very high |
| Throughput effect | Neutral | **Positive** | **Negative** | Positive |
| Reaches D later? | Awkwardly | **Directly** | No | — |

## II-8 · Recommended long-term architecture

> **Option B, reached in the order of §II-9 — and the first four steps are worth taking whatever is decided about the rest.**

**The end state, stated once:**

- **One permanent branch, `main`.** Every commit on it was proven before it arrived. It only ever advances.
- **Lane branches are private, mutable and disposable.** A lane rebases, squashes and rewrites its own workspace as freely as it likes, because nothing outside it depends on those objects.
- **A slice is offered as an immutable, versioned artifact** carrying a stable `Change-Id`. A correction is version 2; version 1 remains.
- **The serializer builds a candidate** — the merge of `main` and the slice — **certifies the candidate, and adopts it or discards it.** Validation happens on the object that will actually be published, which is the only object worth validating.
- **A discarded candidate costs nothing**, because nothing was published. The slice returns to its lane with the failure named.
- **Claims are refs.** Mutual exclusion is enforced by git.
- **Proofs are notes.** They attach to the exact object proven and never alter it.
- **Every register, board and dashboard is a projection**, regenerated on demand, never hand-maintained.
- **Removal is always an explicit record.** There is no way for a contribution to leave silently, because the log only appends.

**What no longer exists, and this is the measure of the design:** the integration branch · the synchronization stage · the branch-reset ceremony · the register reconciliation pass · the Closeout commit · the certification exception · the audit special case · six of the ten claim-protocol steps · and four `state-check` rules that check for failures the architecture no longer permits.

## II-9 · Migration roadmap, ordered by return over risk

**This is the prioritization requested.** Every row is independently valuable and independently reversible; **nothing below depends on anything above it being adopted**, except where stated.

### High value · low risk — *adopt first, regardless of the rest*

| Move | Value | Cost | Risk | Why it is safe |
|---|---|---|---|---|
| **Loss detection** (`change-ledger`) | **Highest** — answers *"was it lost?"*, which is currently unanswerable | ~200 lines | **Very low** | Reports only; changes nothing |
| **`Change-Id` trailer** | **Highest** — identity survives the operation that destroys the SHA | ~20 lines | **Very low** | A trailer nothing yet reads |
| **Claims as refs** | **Highest** — deletes 4 protocol steps, an `integration` write exception, and an audit mode; makes duplicate claiming *impossible* | ~30 lines | **Very low** | **Verified §II-3.1.** Touches no file; coexists with the current protocol during changeover |
| **Certification as notes** | **Highest** — collapses the entire divergence chain at its source | ~60 lines | **Low** | **Verified §II-3.2.** Notes can be written alongside the current manifest until trusted |
| **Immutable slice tags** | High — validation stops chasing a moving branch | ~20 lines | **Low** | Purely additive |

> **These five are the recommendation.** They are roughly 330 lines, none changes how a lane works, and **together they would have prevented every incident in Part I §3.** If nothing else in this document is adopted, adopt these.

### Medium value · medium risk — *schedule deliberately*

| Move | Value | Risk | Constraint |
|---|---|---|---|
| **Registers → one file per record + projection** | High — removes 82% of the conflict surface | Medium | ~40 records to convert; **needs a cycle where every lane is `AVAILABLE`**, which the board shows regularly |
| **Derived `PROJECT_STATUS.md`** | Medium — deletes the Closeout commit | Low-medium | Follows certification-as-notes |
| **Append-only removal records** | Medium — makes supersession a decision | Low | Follows `Change-Id` |
| **Claim leases with visible staleness** | Medium | Low | Follows claims-as-refs |

### High value · high risk — *last, and only once the above hold*

| Move | Value | Risk | Why last |
|---|---|---|---|
| **Merge instead of rebase** | High — ends `--skip` loss | Medium | The largest habit change; needs `--first-parent` to become the reading convention |
| **Retire the `integration` branch; candidate-based integration** | **Highest structural value** | **High** | A topology change. **Safe only after slice tags, notes and merge-based integration are all in place** — each removes one reason `integration` currently exists |
| **Disposable lane branches** | Low | Low | Cosmetic once the above are done |

**Sequencing constraints, and there are only three:** registers before merge-strategy (so a failure in the first merge-based cycle is attributable) · notes before derived status · everything before retiring `integration`.

## II-10 · Expected impact

| Dimension | Today | Option B end state |
|---|---|---|
| **Engineering throughput** | A lane rebases against an 82%-contended tree and may lose a commit doing it | **Higher.** Claim: 10 steps → 1 push. Conflicts: one resolution, or none. **The lane loop is otherwise unchanged, and lanes still never wait for QE** |
| **Serializer capacity** | ~6.5 min per certification, plus reconciliation, sync and Closeout | ~6.5 min per candidate, and **nothing else** — roughly **8 slices/hour against a demand of a few per day**, about 20× headroom |
| **Repository complexity** | 2 permanent shared branches, 4 hand-maintained registers, 1 hand-maintained dashboard | **1 permanent branch, 0 hand-maintained records** |
| **Governance burden** | 7-stage lifecycle, 10-step claim protocol, 16-step completion sequence | **~14 rules deleted**, none added. The lifecycle keeps its stages and loses its ceremony |
| **Traceability** | *"Lost or superseded?"* requires a human investigation | **`make ledger`** |
| **Recoverability** | An unreferenced object in one clone ([B-017](../../BUGS.md)) | Structurally impossible — the log only appends |
| **Scalability** | O(N²) shared-file conflicts; O(N) rebases per cycle | **~0 conflicts, 0 rebases.** Serializer-bound at roughly 6–8 lanes, at which point the answer is an automated queue — and **Option B is already that shape**, so adopting one replaces the operator, not the model |

### II-10.1 · The product test

**Does this make it easier to build and release the best possible product?**

| | |
|---|---|
| **Yes, clearly** | The five high-value/low-risk moves. They remove a class of lost work, delete protocol steps, and change nothing about how a lane spends its day |
| **Yes, with scheduling** | Registers-as-files. The largest single reduction in friction, and the one that needs a quiet board |
| **Yes, eventually** | Retiring `integration`. The most structural improvement, and the one with the most to lose if rushed |
| **No** | Option C, and any rule added for symmetry rather than for a failure that has actually occurred |

> **The release process exists to serve product engineering, and the honest summary of this review is that the current one has begun to cost more than it returns.** Not because it is badly designed — it is carefully designed — but because it maintains by procedure what could be guaranteed by structure, and the procedure now has to be executed by every session, forever.

## II-11 · Consequences of Part II, beyond Part I

- **[ADR-0032](0032-release-certification.md) loses its bounded exception entirely**, rather than narrowing it. The sentence *"a certification record cannot contain its own commit hash"* is retired as a storage artifact.
- **`refs/claims/*` and `refs/notes/*` must be in the fetch and push refspecs** — they are not by default. This is the single most likely operational mistake in the design, and it is a two-line `git config` plus one `state-check` rule.
- **`git log --first-parent` becomes the documented reading convention**, replacing `--oneline` as the changelog a cold session reads.
- **No module, boundary, event contract, schema or product behaviour is affected — unchanged from Part I.**
- **Part II contradicts Part I in one place and defers to it in another.** It retires Part I's retention of `integration` (Part I asked whether it should be authoritative; Part II asks whether it should exist), and it keeps Part I's ordering discipline — **do not retire `integration` early.** Where the two disagree, **Part II is the target and Part I is the path.**

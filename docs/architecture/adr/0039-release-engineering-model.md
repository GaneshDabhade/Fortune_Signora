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

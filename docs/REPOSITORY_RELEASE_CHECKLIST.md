# Repository Release Checklist

> **The runbook for one repository cycle, end to end.** Established 2026-08-02, on the product owner's direction.
>
> **This is an operational document, not a governance one.** `CLAUDE.md` §20e states *what must happen and why*; this file is *how QE performs it* — every command, in order, with a tick-box against each. Where the two disagree, `CLAUDE.md` is right and this file is a defect.
>
> **Owned by QE.** A feature lane never runs it.

## How to use it

**Copy the checklist into the cycle's working notes and tick as you go.** Do not tick ahead, and do not tick from intention.

> **An unticked box is not a failure — an untrue tick is.** The next session trusts this file the way it trusts a test result, which is exactly why a box ticked for work that was not done is worse than having no checklist at all.

**Every stage must complete before the next begins.** The order is not a suggestion: certification before integration is what makes the certified tree and the promoted tree the same tree, and Closeout before Repository Ready is what stops the repository describing a state it has left.

**If a gate fails, the cycle stops there.** Record the failure, open the `B-nnn` row, return the branch to its lane. There is no partial promotion, no expedited path, and no manual override.

---

## The seven stages

| Stage | Name | Deterministic? |
|---|---|---|
| 1 | Validate feature lanes | No — judgement; findings become bug rows |
| 2 | Execute repository-wide certification | **Yes** |
| 3 | Integrate validated work into `integration` | Yes |
| 4 | Promote `integration` to `main` | **Yes** |
| 5 | Execute Repository Closeout | Yes |
| 6 | Synchronize repository branches | Yes |
| 7 | Declare Repository Ready | Yes |

---

## Stage 0 · Before you start

- [ ] **Every dev server is down**, including the human-review stack. `make smoke` binds ports 3000 and 8000 ([B-002](BUGS.md))
- [ ] **The documented prerequisites are installed** — `make`, Docker, Docker Compose, `uv`, Node ([RUNNING.md](RUNNING.md)). **If one is missing and installing it is within your authority, install it** (`CLAUDE.md` §20e, *QE removes its own blockers*); escalate only if the OS or policy refuses
- [ ] **The stack is up** — `docker compose -f infra/docker-compose.yml up -d`
- [ ] **The lane's branch is rebased onto `integration` and pushed**, and the lane has said it is ready. A push is backup, not a trigger

```bash
git fetch origin
git checkout <lane-branch> && git pull --ff-only
git merge-base --is-ancestor integration HEAD && echo "rebased: will fast-forward"
```

---

## Stage 1 · Validate feature lanes

**Runs on the rebased lane branch — the exact tree that will become `integration` and then `main`.** Nothing here is optional, and a partial run is not a run.

```bash
# the frontend must be installed, or six backend tests skip and the run still exits green
cd frontend && npm install

# the full backend suite, with the coverage gate
cd ../backend && uv run pytest --cov

# the architectural guarantees
uv run pytest -m security_invariant

# types and boundaries
uv run mypy .
uv run lint-imports

# the frontend
cd ../frontend && npm run test && npm run typecheck && npm run lint && npm run build

# the whole stack, production images
cd .. && make smoke

# advisory — did documentation move with the code? (CLAUDE.md §12)
make doc-drift ARGS="main..HEAD"
```

- [ ] Full backend suite passes, coverage gate met
- [ ] Security Invariants pass — **none skipped, none weakened**
- [ ] `mypy --strict` clean
- [ ] `lint-imports` — every contract kept
- [ ] Frontend: tests · typecheck · lint · production build
- [ ] `make smoke` green
- [ ] `doc-drift` reviewed — **advisory; a finding goes back to the lane as a question, never blocks promotion**
- [ ] **The product was used, not only tested** — [QUALITY_ENGINEERING.md §3](QUALITY_ENGINEERING.md) is the method
- [ ] Every defect found is a `B-nnn` row in [BUGS.md](BUGS.md), with all fields filled
- [ ] The Slice Handoff is present, complete, and its claims verified

> **The environment variables this needs are in [RUNNING.md § Running a lane](RUNNING.md#running-a-lane).** All three of them — the third is the one a lane forgets ([B-003](BUGS.md)), and the code behind that trap is [B-007](BUGS.md).

---

## Stage 2 · Execute repository-wide certification

**Immediately after validation, on the same tree.** ADR-0032.

```bash
# The three lane variables must be exported here too — `make certify` runs the
# whole suite, and without them it resolves the default database. Measured
# 2026-08-02: the same commit certified 2223/94.36% against the shared default
# and 2325/95.59% against the lane's own database. A gate pointed at the wrong
# database is not a gate.
make certify        # writes certification/manifest.json — no options, deliberately
# migration reversibility, and disaster recovery against the running stack
make dr
```

> **Certify from a clean tree.** `tree_is_clean` is a recorded condition, so a run with anything uncommitted — including the report a previous run just wrote — records *"the tree certified was never stored"* and cannot certify. **Commit the slice first, certify second, then commit the record it produces.**

- [ ] `make certify` succeeded
- [ ] Migration reversibility verified
- [ ] `make dr` succeeded
- [ ] The certification record names **this commit** and the current migration head

> **Certification expires by derivation, never by decision.** Change the rendering protocol, re-release a prompt, add a migration or edit a scenario and `is_certified` reads false on its own. **Nothing is ever marked certified by hand.**
>
> **If any gate fails: stop.** The cycle does not continue, and no part of the promotion happens.

---

## Stage 3 · Integrate validated work into `integration`

```bash
git checkout integration && git merge --ff-only <lane-branch>
```

- [ ] Fast-forward succeeded — **a branch that will not fast-forward goes back to its lane**; QE never resolves another lane's conflicts
- [ ] [BUGS.md](BUGS.md) reconciled — ids unique, statuses match what the slice actually did
- [ ] [LANE_COORDINATION.md](LANE_COORDINATION.md) reconciled against every handoff's `Coordination` field
- [ ] Findings folded into `docs/architecture/38` and `39`

---

## Stage 4 · Promote `integration` to `main`

```bash
git checkout main && git merge --ff-only integration
```

- [ ] `main` fast-forwarded

> **Certification passed, so this happens.** No approval is sought, none is required, and **no waiting state exists between stage 2 and here.** A pause for judgement would mean the gates did not decide.
>
> **The one blocking rule:** `integration` never fast-forwards to `main` with an open 🔴 bug.

---

## Stage 5 · Execute Repository Closeout

**Mandatory. Eleven activities, in order. Every figure measured from the promoted commit — nothing copied from a lane's report.**

### First, measure

```bash
cd backend
uv run pytest --cov 2>&1 | tail -3            # totals + coverage
uv run pytest -m security_invariant -q | tail -1
uv run mypy . | tail -1                       # file count
uv run lint-imports | tail -1                 # contracts kept
ls migrations/versions | wc -l                # migration count; head is the last id
cd ../frontend && npm run --silent test 2>&1 | tail -3
cd .. && git rev-parse --short=7 main
git log --grep="Slice-Handoff" main~10..main  # what the lanes reported
```

- [ ] pytest totals
- [ ] frontend totals
- [ ] Security Invariants
- [ ] `mypy --strict` file count
- [ ] `lint-imports` contracts
- [ ] coverage
- [ ] `make smoke` status
- [ ] certification status
- [ ] migration head
- [ ] architecture metrics — modules, ADRs, numbered documents

> **Repository metrics are measured. They are never transcribed.**

### Then write the records

- [ ] **1 · `PROJECT_STATUS.md`** — repository state · current milestone · overall completion · milestone progress · repository health · certification status · current blockers · active work · recently completed · recommended next work. **Concise, always representing `main`**
- [ ] **2 · [`SESSION_HANDOFF.md`](SESSION_HANDOFF.md)** — current repository state · certification state · active lanes · open blockers · pending work · recommendations. **Not a second dashboard**
- [ ] **3 · [`ACTIVE_ASSIGNMENTS.md`](ACTIVE_ASSIGNMENTS.md)** — promoted assignments marked `COMPLETE` **and removed**; lanes returned to `AVAILABLE`; no stale rows
- [ ] **4 · Certification state** refreshed
- [ ] **5 · Repository metrics** refreshed
- [ ] **6 · Milestone progress** refreshed
- [ ] **7 · Roadmap progress** refreshed against [IMPLEMENTATION_ROADMAP.md](../IMPLEMENTATION_ROADMAP.md)
- [ ] **8 · Repository health** refreshed — gates, open defects by severity, coordination register size, technical debt
- [ ] **9 · Release summary published** — features delivered · bugs fixed · ADRs accepted · migrations · architectural changes · metrics · remaining blockers · recommended next work. **A section of `PROJECT_STATUS.md`, not a new document**

---

## Stage 6 · Synchronize repository branches

```bash
git checkout integration && git merge --ff-only main
# idle lanes only — a lane mid-slice is left alone
for lane in <idle-lane-branches>; do
  git checkout "$lane" && git merge --ff-only main
done
git checkout main
git branch -v                 # every synchronized branch at one commit
git push origin main integration <idle-lane-branches>
```

- [ ] **10 · `integration` fast-forwarded to `main`**
- [ ] **Every idle lane** fast-forwarded
- [ ] **Every lane in active development left untouched** — it rebases at the start of its next slice, and moving it underneath would rewrite work in progress
- [ ] `git branch -v` verified: every synchronized branch shares the promoted baseline
- [ ] Pushed to `origin` — **backup only; a push triggers nothing** ([ADR-0027](architecture/adr/0027-local-first-development.md))

---

## Stage 7 · Declare Repository Ready

```bash
python3 infra/state-check.py      # advisory: do the documents agree with the repository?
```

- [ ] `state-check` run and every finding resolved or consciously accepted — **it reports, it never repairs, and each finding has more than one correct resolution**
- [ ] Every box above is ticked, and every tick is true
- [ ] **11 · Repository Ready declared**

**Then, and only then, the next development cycle may begin.**

---

## What happens after

| | |
|---|---|
| **Human product review** | Product owner, on `main`, in the demo environment (3000/8000). **After Repository Ready, never gating it** — a gate a person holds is not a deterministic gate |
| **Release** | Deferred to M14.5. There is no release today ([ADR-0027](architecture/adr/0027-local-first-development.md)) |

---

## The one-page version

```
0  stack up · prerequisites installed · lane rebased
1  validate     pytest --cov · invariants · mypy · lint-imports · frontend · smoke · use it
2  certify      make certify · migration reversibility · make dr
3  integrate    git merge --ff-only <lane-branch>       into integration
4  promote      git merge --ff-only integration         into main
5  close out    measure → PROJECT_STATUS · SESSION_HANDOFF · ACTIVE_ASSIGNMENTS
                → certification · metrics · milestone · roadmap · health · release summary
6  synchronize  integration + idle lanes → main         active lanes untouched
7  declare      state-check → Repository Ready
```

**Stopping at 2 or at 4 is an incomplete repository cycle**, not a finished one with paperwork outstanding.

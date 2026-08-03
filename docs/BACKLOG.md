# Repository backlog — the READY queue

> **The authoritative repository work queue.** Established 2026-08-02, on the product owner's direction, replacing QE-assigned scheduling. **Task ids added the same day**, so a claim has something immutable to refer to.
>
> **The product owner owns priority. Feature lanes pull from the top. QE never schedules.** A lane that has finished a slice does not wait to be told what to do next — it runs the **Task Claim Protocol** (`CLAUDE.md` §20e) and claims the highest eligible `READY` task.
>
> **The order of this queue *is* the priority.** Nothing else expresses it, and nothing else may contradict it.

## Why this exists

**QE was becoming the bottleneck for a model that exists to remove bottlenecks.** Quality engineering, integration, certification and promotion belong together — each is a judgement about the repository as a whole. **Scheduling is not one of those.** It is a product decision, and routing it through QE meant every idle lane waited for the one session that was busy certifying, which serializes exactly the parallelism the lanes were created for.

```
  planning            execution              quality and release
  ────────            ─────────              ───────────────────
  Product Owner  ──▶  feature lanes    ──▶   QE
  owns priority       claim and build        validates · certifies
  writes this file    record in              integrates · promotes
                      ACTIVE_ASSIGNMENTS     never schedules
```

## Task ids are permanent

**Every task carries a `TASK-nnn` that is never reused and never renumbered**, and **that id is what every other document refers to** — [`ACTIVE_ASSIGNMENTS.md`](ACTIVE_ASSIGNMENTS.md), a commit message, a Slice Handoff, a status report. Free-form titles drift; an id does not, and **an id is what makes "two lanes claimed the same task" a fact a machine can check** rather than a judgement about whether two sentences mean the same thing.

**A task's id, module and slice are stable. Its *status* and its *position* move.** Position is the product owner's; status follows the work.

| Status | Meaning |
|---|---|
| `READY` | **Claimable now.** Every input exists, no decision is outstanding, nobody holds it |
| `CLAIMED` | A lane holds it. The lane is named here, and [`ACTIVE_ASSIGNMENTS.md`](ACTIVE_ASSIGNMENTS.md) carries the detail. **Implementation begins immediately** |
| `IN PROGRESS` | Being built. **A claim flows straight into this** — there is no waiting state between them |
| `IN VALIDATION` | **Implemented and pushed.** Set by the implementing lane, the moment the work exists as commits QE can take. **The lane's responsibility ends here and it claims its next task immediately** |
| `CHANGES REQUESTED` | **QE**, during validation. Returned to the implementing lane with the corrections named; that lane fixes them and sets `IN VALIDATION` again |
| `VERIFIED` · `CERTIFIED` · `PROMOTED` | QE's stages, and **only QE's** — validation passed, `make certify` passed, `main` fast-forwarded |
| `WAITING` | Needs a **decision** from the product owner or another lane. **Named, always** |
| `BLOCKED` | Needs a **capability** that does not exist yet. **The capability is named** |
| `DONE` | Promoted to `main`. Removed at the next Closeout |

**`WAITING` and `BLOCKED` differ in who unblocks them**: one needs somebody to answer, the other needs somebody to build. A task nobody can move in either direction is a finding, not a backlog row.

> **The lane owns execution state; QE owns everything after it** (`CLAUDE.md` §20e, *Execution ownership ends at `IN VALIDATION`*). A lane moves its own task `CLAIMED` → `IN VALIDATION` when it pushes, and **stops there**. QE moves it through `VERIFIED` → `CERTIFIED` → `PROMOTED` → `DONE`, or back to `CHANGES REQUESTED`.
>
> **The point is that no state is nobody's.** QE was updating the execution status of work it did not write, which is bookkeeping rather than judgement — and a status nobody is clearly responsible for is the one that goes stale.
>
> **And a lane never waits here.** The moment it sets `IN VALIDATION` it returns to the `READY` queue and claims again — waiting for certification is idle capacity, and it is the cost that grows with every lane added. Four things stop a lane claiming, and *"my last slice is still with QE"* is not one of them (§20e, *Continuous execution*).

## What a lane may and may not do here

| May | May not |
|---|---|
| **Claim a `READY` task** — by the Task Claim Protocol, never by editing this file alone | **Reorder the queue.** Position is priority, and priority is the product owner's |
| **Record why it skipped the first `READY` task** — in that task's Notes | **Reprioritize** — including by claiming further down without saying why |
| **Move a task it holds through the lifecycle** — `CLAIMED` → `DONE` | **Insert a new `READY` task** without product-owner approval |
| **Report a defect or a dependency** — [`BUGS.md`](BUGS.md), [`LANE_COORDINATION.md`](LANE_COORDINATION.md) | **Remove a task**, or rewrite one it does not hold |

> **A skip is information, not an inconvenience.** *"Lane A skipped TASK-002 because it needs `signal_engine`, which Lane B holds"* tells the product owner something about the queue's shape. Silence tells them the queue is fine when it is not.

---

## READY — claimable now, in priority order

> **Seven tasks became claimable on 2026-08-03**, when [ADR-0100](architecture/adr/0100-delegated-dependency-rulings.md) resolved the decisions they were waiting on. **They are placed at the top because they have waited longest**, not because they are larger.

### TASK-300 · Epic A — surface what already exists

| | |
|---|---|
| **Module** | **Six slices across four modules** — see the table below. **Not one claimable unit**, which is the finding |
| **Slice** | A4 · A1 · A2 · A5 · A6, specified in [51-implementation-specifications.md](architecture/51-implementation-specifications.md) |
| **Status** | **`CLAIMED` — Lane B**, 2026-08-03. **Assigned directly by the product owner**, who named Lane B implementation owner for Epic A and set A4 as the first slice. Recorded here by Lane B because the row did not exist; **the priority is the product owner's, not this lane's** |
| **Notes** | **Verified against Lane A's branch before claiming, not against this register.** Of the six slices, **one is built, one is substantially built by Lane A this week, and every remaining one needs at least one module Lane A holds.** [C-323](LANE_COORDINATION.md) carries the evidence and a recommendation |

| Slice | Verified status, 2026-08-03 | Blocked on |
|---|---|---|
| **A4** freshness | **Not built.** No `last_observed_at` in any router or component | `provider_platform` **public port** (Lane A) · the render (Lane A). The response composition is `opportunity_engine` — **Lane B's** |
| **A1** search | **Not built.** No search endpoint in any router; `/account-identities` names ids you already hold and is not a lookup | The shell (Lane A) · **and the endpoint has no owning module yet** |
| **A2** accounts list | **Substantially built by Lane A**, `SW-01`…`SW-04`, this week — `TriageStrip`, `lib/state/triage.ts`, URL-driven narrowing | **Nothing. It is being delivered elsewhere** |
| **A5** company history | **Not built.** `claim.observed_at` holds the series; nothing exposes it | The render (Lane A). **Backend is `knowledge_graph` — unassigned** |
| **A6** needs identity | **Not built.** `AccountIdentityResponse.agreement` is the raw material | The render (Lane A). **Backend is `knowledge_graph` — unassigned** |
| **B2** first run | **Built by Lane A** — `first-run.test.tsx`, D36 | — |

> **This lane is not proceeding into Lane A's modules on the strength of a directive that predates the collision.** One assignee per module is §20e's hardest invariant, and the product owner's own instruction in the same assignment was *"do not quietly bypass module boundaries."* **[C-323](LANE_COORDINATION.md) asks which way to resolve it**; the two backends in unassigned `knowledge_graph` are claimable meanwhile.

### TASK-900 · The platform learns to compose a module into the runtime

| | |
|---|---|
| **Module** | `signora_platform` — 🔴, and **explicitly approved** by [ADR-0100](architecture/adr/0100-delegated-dependency-rulings.md) R-1 |
| **Slice** | **The RFC only.** No rewiring in this task |
| **Status** | `READY` |
| **Notes** | Four capabilities in one RFC: a session on `EventHandler` · `PublishableEvent` satisfiable by a frozen dataclass · a port from a handler to a provider adapter · a self-directed Casbin action. **Additive only** — a module not using one behaves identically |
| **On claiming** | **The RFC lands before any module is rewired.** §20a's approval branch means approved *then* implemented. Closes [C-012](LANE_COORDINATION.md), [C-013](LANE_COORDINATION.md), [C-021](LANE_COORDINATION.md), [C-207](LANE_COORDINATION.md) |

### TASK-901 · Seven modules consume the events they declare

| | |
|---|---|
| **Module** | Seven pipeline modules, **one per slice** |
| **Slice** | **Seven independently certifiable slices**, not one |
| **Status** | `BLOCKED` on TASK-900 — listed here so the sequence is visible |
| **Notes** | After each, `make runtime-composition` is measured and **`BLOCKED_BY_C012` shrinks by exactly one.** A module leaving that list is how the architecture records that it now expects live consumption |

### TASK-902 · M7 Timeline — the remaining slices

| | |
|---|---|
| **Module** | `timeline` |
| **Slice** | S05+ |
| **Status** | `READY` — **[ADR-0038](architecture/adr/0038-timeline.md) is ratified** |
| **Notes** | **Postgres first**; Meilisearch on a stated trigger — *the first customer asking to search or facet a timeline rather than scroll it*. **Ship the six live events**; the seventh joins when M11 resumes. **The customer surface already exists** — CX-03 mounted the feed on the account brief |
| **On claiming** | Supersedes `TASK-017`, which was waiting on exactly these three answers |

### TASK-903 · A seller can see what their company sells

| | |
|---|---|
| **Module** | `commercial_profile` (the read surface) · Product Surface (the mount) — **a two-lane build** |
| **Slice** | one slice each side |
| **Status** | `READY` |
| **Notes** | **Read-only, for `member`, beside the account brief** — not under `/settings`, where the granted read is unreachable behind `workspace:update`. `policy.csv` already grants `member` read on `product`, `icp`, `buying_committee` and `commercial_focus`: **the API and the product disagree, and the API is right** |
| **On claiming** | Open a `C-` item for the mount if the two halves are claimed by different lanes. **Placement is judgement** ([ADR-0100](architecture/adr/0100-delegated-dependency-rulings.md) R-5) — say so in review if it reads wrong |

### TASK-904 · An organization can grow

| | |
|---|---|
| **Module** | `workspace_tenancy` |
| **Slice** | invitation table · acceptance · members list |
| **Status** | `READY` |
| **Notes** | **Signora owns the invitation.** An `invitation` table keyed by email; acceptance matches a pending row against the **`email` claim already in the verified JWT**. **Better Auth's `organization` plugin is not adopted** — migration `0005` revokes `signora_app` from the `auth` schema, so plugin-owned membership is membership the Python tier cannot read, and §13 requires it re-verified every request |
| **On claiming** | **v1 delivery is a shareable link, not email.** No transactional-email dependency is added. **That half is judgement** and is the ruling to challenge first if you would rather ship with email |

### TASK-905 · A contraction risk stops looking like an opportunity

| | |
|---|---|
| **Module** | Product Surface · `buying_score_engine` owns posture |
| **Slice** | one slice |
| **Status** | `READY` |
| **Notes** | Posture reaches the attention row. **A contraction risk must not be confusable with a low-scoring opportunity** — they mean opposite things to a CRO scanning a list. **The treatment is yours**, within the design system; the ruling is only that they must differ |

### TASK-906 · M14b names its bounded context

| | |
|---|---|
| **Module** | **Undecided — that is the deliverable** |
| **Slice** | discovery |
| **Status** | `READY` |
| **Notes** | [ADR-0100](architecture/adr/0100-delegated-dependency-rulings.md) R-2: **a roadmap row is not claimable until it names its bounded context.** M14b's first task is therefore the discovery that names it. Lane A's analysis is already recorded — *one module and two integrations, not one and not three* |

### TASK-001 · Verify the three fixes QE may not close

| | |
|---|---|
| **Module** | Repository — `apps/`, documentation, process |
| **Slice** | one slice |
| **Status** | **`DONE`** — QE, 2026-08-02. Lane B verified [B-009](BUGS.md), [B-013](BUGS.md) and [B-014](BUGS.md) with evidence; all three are now `VERIFIED`. [B-012](BUGS.md) was reported alongside them and still awaits a non-QE verifier |
| **Notes** | **Explicitly not QE's.** [B-009](BUGS.md), [B-013](BUGS.md) and [B-014](BUGS.md) were all fixed by QE, which may not verify its own work. Reproduce each from a clean shell, from the original steps, **never from the diff**. Small, and it retires three rows |
| **On claiming** | **A fourth row is in the same condition and is not in this task's scope as written: [B-012](BUGS.md) is `FIXED` and awaiting verification by someone other than QE.** Lane B will verify it alongside the three and say so, but is **not** rewriting the task — inserting scope into a `READY` task is the product owner's, not a lane's. If that is unwanted, the fourth verification is reported and B-012's status is left alone |

### TASK-002 · An account with nothing live says nothing at all (R2-03)

| | |
|---|---|
| **Module** | Product Surface |
| **Slice** | PS-01 |
| **Status** | **`DONE`** — QE, 2026-08-02. Promoted in the PS/PP batch at `e5a266d` |
| **Notes** | 🟡. Overlaps R1-04 — read both before starting |
| **On claiming** | **R1-04 is 🟠, unimplemented, and is the same plumbing.** The brief receives `evidence` on the opportunity response and renders `is_current` only, so *cooling* never reaches it — and R2-03 cannot be answered without the brief learning the same fact. Lane A will surface evidence state on the brief once and let both findings read it, rather than adding a second path for the second finding. **The task is not being rewritten**: R1-04 has no id, and inserting `READY` scope is the product owner's. If the overlap should instead be a separate task, say so and the R1-04 half is reported rather than shipped |

### TASK-003 · The attributes are engineering's words (R11-06)

| | |
|---|---|
| **Module** | `knowledge_graph` |
| **Slice** | KG-01 |
| **Status** | `READY` |
| **Notes** | 🟡. [ADR-0034](architecture/adr/0034-ubiquitous-language.md)'s customer vocabulary reaches attribute names, and nothing enforces it there yet |
| **Skipped by Lane A**, 2026-08-02 | **Not claimable as written — [C-018](LANE_COORDINATION.md) opened.** Every available implementation contradicts something already written: `knowledge_graph` publishing labels contradicts AC-28 (*an entity is an identity, not a record*) and ADR-0034 (*the translation never travels inward*); translating in the browser contradicts [R11-06](architecture/39-product-review-findings.md) itself (*never in the browser*); the third option — a reviewed catalog of attribute labels — does not exist. **R11-06 also records itself as a deliberate trade-off** whose milestone is *"on evidence from a real reviewer"*, and no reviewer evidence has been recorded, so the trigger may not have fired. Lane A took **TASK-004** instead |

### TASK-004 · The brief distinguishes *not narrated* from *narrated against evidence that no longer resolves*

| | |
|---|---|
| **Module** | Product Surface |
| **Slice** | PS-02 |
| **Status** | **`DONE`** — QE, 2026-08-02. Promoted in the PS/PP batch at `e5a266d`. Taken after [TASK-003](#task-003--the-attributes-are-engineerings-words-r11-06) was skipped with its reason recorded |
| **Notes** | The lane's half of [B-010](BUGS.md). The `RUNNING.md` half is QE's and is done separately. **Do not "fix" it by deleting narrations** — a materialized AI artifact is a historical fact (§2) |

### TASK-005 · `state-check` learns the backlog

| | |
|---|---|
| **Module** | Repository tooling — `infra/` |
| **Slice** | one slice |
| **Status** | **`DONE`** — QE, 2026-08-02. The board-vs-backlog check is built and promoted; it is what reported these four stale rows |
| **On claiming** | **Only the unbuilt half.** [B-017](BUGS.md) asked whether this task was superseded; measured, it is *half* superseded. QE's `e1d2fa6` routed claims to `integration`, which makes cross-branch detection largely moot — **that half is withdrawn.** But *"every `CLAIMED` row has a matching lane on the board"* is **not built**: `state-check` check 5c reads the board only, so a backlog row reading `CLAIMED — Lane X` with no board row is invisible today. Lane B builds that half and leaves B-017's ruling to QE |
| **Notes** | Assert that no task is claimed twice and that every `CLAIMED` row has a matching lane on the board. **A slice, not a Closeout** — `infra/` decides whether gates pass ([B-014](BUGS.md)). *Partly delivered 2026-08-02; what remains is the id-level checking* |

---

## WAITING — on a decision, and on whom

| Id | Task | Module | Waiting on |
|---|---|---|---|
| **TASK-006** | [C-010](LANE_COORDINATION.md) — no lane is assignable to `apps/`, `signora_platform/` or repository process | Repository | **The product owner.** Four defects have landed in this gap: [B-007](BUGS.md), [B-012](BUGS.md), [B-013](BUGS.md), [B-014](BUGS.md). **The highest-value decision on this page** |
| **TASK-007** | [C-008](LANE_COORDINATION.md) — sellers cannot see what their company sells | Product Surface | **The product owner**, to choose between options A/B/C/D. The proposal is accepted; only the choice remains |
| **TASK-008** | [C-005](LANE_COORDINATION.md) — the signal-profile write path | `signal_engine` | **The product owner**, on whether a customer should author relevance at all. Ownership answered; sequencing is not |
| **TASK-009** | [C-009](LANE_COORDINATION.md) — an internal fault reaches a customer as a `422` | `signora_platform` | **The product owner.** A frozen-platform change under §20a, with a full proposal recorded |
| **TASK-010** | [C-006](LANE_COORDINATION.md) — which lane owns `test_api_<module>.py` | Repository | **The product owner**, and deliberately: *"avoid creating a local convention that later becomes repository behaviour"* |
| **TASK-011** | The brief's hierarchy pass (D20) | Product Surface | **A seller in the room.** A collaborative product-design activity, not a slice |
| **TASK-012** | M9.5 Step F | AI Platform | **The product owner.** Inserted, open, and the oldest outstanding commitment on the board |
| **TASK-013** | `reasoning@1` has no released model | `ai_reasoning_engine` | **The product owner.** The Decision Package would refuse at runtime. **Do not tune the prompt, delimiter, schema or timeout to make it pass** |
| **TASK-017** | **M7 — Timeline.** [C-020](LANE_COORDINATION.md) — no milestone definition, no module design, Meilisearch unprovisioned, event scope unagreed | `timeline` | **The product owner.** Two decisions: the §6 milestone definition, and Meilisearch now or Postgres-first on a stated trigger. **Assigned to Lane B 2026-08-02 and released the same day** — the module assignment stands; the work is not executable until the architecture is agreed |

## BLOCKED — on a capability, and on which

| Id | Task | Module | Blocked on |
|---|---|---|---|
| **TASK-014** | [C-007](LANE_COORDINATION.md) — the guided first run | Product Surface | The `target_accounts_changed` consumer in `provider_platform`. The sequencing condition has fired — all five declarations exist — so this is a missing capability, not a missing decision |
| **TASK-015** | [B-004](BUGS.md) — `provider_watermark` cannot tell two target accounts apart | `provider_platform` | The same consumer. **Not to be fixed opportunistically**: without it, the schema change has nothing exercising it |
| **TASK-016** | [R9-04 / D5](architecture/39-product-review-findings.md) — what changed since you last looked | Product Surface | Per-user read state, which does not exist. **Trigger unfired** — a design partner saying they cannot tell what is new |

> **`TASK-015` was moved to `READY` by Lane A and is withdrawn, 2026-08-02.** The row is restored exactly as the product owner wrote it. **The reasoning for unblocking it is not withdrawn — only the act of unblocking**, which is a priority decision and not a lane's ([B-019](BUGS.md)).
>
> **The fact the decision needs, stated once and not acted on:** the blocker read *"not to be fixed opportunistically — without it the schema change has nothing exercising it."* That condition is now **satisfied rather than waived**: PP-02 is the consumer that exercises it, [ADR-0036](architecture/adr/0036-target-account-contract.md) names this *"one defect that must be fixed before the consumer is built"*, and **both are implemented and with QE** as migrations `0029` and `0030`.
>
> **So the code exists whatever this row says.** It travels under PP-01 and PP-02 regardless of which section holds the id, which is why withdrawing costs nothing and unblocks certification immediately. **Ratify it where it stands, or leave it here** — either is correct, and only the product owner may choose.

## DONE — promoted, removed at the next Closeout

*These predate task ids and are recorded by commit, which is the immutable reference they do have.*

| Task | Lane | Promoted |
|---|---|---|
| R2-01 — the guidance says what it is pointing at | A | `efaa987`, in `1bbee30` |
| M12.5 slice 5 — target accounts. *M12.5 complete* | B | `3f4e988` |
| M12.4 — research on demand | A | `c1f5985` |
| Commit-bound certification | QE | `1bbee30` · `624f770` |
| Pull-based work allocation | QE | `3e36da9` |

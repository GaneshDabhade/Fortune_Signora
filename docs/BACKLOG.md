# Repository backlog — the READY queue

> **The prioritized queue of work available to be claimed.** Established 2026-08-02, on the product owner's direction, replacing QE-assigned scheduling.
>
> **The product owner owns priority. Feature lanes pull from the top. QE never schedules.** A lane that has finished a slice does not wait to be told what to do next — it claims the highest `READY` item it can take and records the claim in [`ACTIVE_ASSIGNMENTS.md`](ACTIVE_ASSIGNMENTS.md).

## Why this exists

**QE was becoming the bottleneck for a model that exists to remove bottlenecks.** Quality engineering, integration, certification and promotion belong together — each is a judgement about the repository as a whole, and one authority running the same gates in the same order is worth more than a separation. **Scheduling is not one of those.** It is a product decision, and routing it through QE meant every idle lane waited for the one session that was busy certifying, which serializes exactly the parallelism the lanes were created for.

```
  planning            execution              quality and release
  ────────            ─────────              ───────────────────
  Product Owner  ──▶  feature lanes    ──▶   QE
  owns priority       pull and claim         validates · certifies
  writes this file    record in              integrates · promotes
                      ACTIVE_ASSIGNMENTS     never schedules
```

## How it works

**A lane may claim only a `READY` item.** Not `WAITING`, not `BLOCKED` — those are here so nothing disappears, not so a lane can start them.

**Claiming is one action with two halves, and both happen before the first line of implementation:** move the row to `DONE`-side tracking by adding your lane to [`ACTIVE_ASSIGNMENTS.md`](ACTIVE_ASSIGNMENTS.md), and mark the item `CLAIMED` here with your lane's name. **A claim that is not written down is not a claim** — it is two lanes about to build the same thing.

**Claim from the top.** The order is the product owner's judgement about value, and a lane skipping down the queue is quietly re-prioritizing. If the top item genuinely cannot be taken — it needs a module another lane is inside, or a decision that has not been made — **say so in the item's note and take the next one.** That is information the product owner needs; silence is not.

> **A lane may not reorder, reprioritize, add or remove items.** Raise it: a defect belongs in [`BUGS.md`](BUGS.md), a dependency in [`LANE_COORDINATION.md`](LANE_COORDINATION.md), and anything else is a conversation with the product owner. **The one thing a lane writes here is a claim.**

| Status | Meaning |
|---|---|
| `READY` | **Claimable now.** Every input exists; no decision is outstanding |
| `CLAIMED` | A lane has taken it. The lane is named, and [`ACTIVE_ASSIGNMENTS.md`](ACTIVE_ASSIGNMENTS.md) carries the detail |
| `WAITING` | Needs a decision from the product owner or another lane. **Named, always** |
| `BLOCKED` | Needs a capability that does not exist yet. **The capability is named** |
| `DONE` | Promoted to `main`. Kept until the next Closeout, then removed |

**`WAITING` and `BLOCKED` are different, and the difference decides who unblocks it.** `WAITING` needs somebody to answer; `BLOCKED` needs somebody to build. An item nobody can move in either direction is a finding, not a backlog row.

---

## READY — claimable now, highest value first

| # | Item | Where | Notes |
|---|---|---|---|
| 1 | **Verify [B-009](BUGS.md), [B-013](BUGS.md) and [B-014](BUGS.md)** | Repository | **Explicitly not QE's** — QE wrote all three fixes and may not close its own. Reproduce each from a clean shell, from the original steps, not from the diff. Small, and it unblocks the register |
| 2 | **R2-03** — an account with nothing live says nothing at all | Product Surface | 🟡. Overlaps R1-04, so read both before starting |
| 3 | **R11-06** — the attributes are engineering's words | Knowledge Graph | 🟡. The customer's vocabulary rule ([ADR-0034](architecture/adr/0034-ubiquitous-language.md)) reaches attribute names, and nothing enforces it there yet |
| 4 | **[B-010](BUGS.md)** — re-seeding orphans every narration | Playground · Product Surface | Two separable halves. The `RUNNING.md` half is QE's; **the brief distinguishing *not narrated yet* from *narrated against evidence that no longer resolves* is a lane's** |
| 5 | **Teach `state-check` about the backlog** | Repository tooling | Assert that no `READY` item has been claimed twice, and that every `CLAIMED` row has a matching lane in `ACTIVE_ASSIGNMENTS.md`. **A slice, not a Closeout** — `infra/` decides whether gates pass ([B-014](BUGS.md)) |

## WAITING — on a decision, and on whom

| Item | Where | Waiting on |
|---|---|---|
| **[C-010](LANE_COORDINATION.md)** — no lane is assignable to `apps/`, `signora_platform/` or repository process | Repository | **The product owner.** Four defects have now landed in this gap: [B-007](BUGS.md), [B-012](BUGS.md), [B-013](BUGS.md), [B-014](BUGS.md). **The single highest-value decision on this page** |
| **[C-008](LANE_COORDINATION.md)** — sellers cannot see what their company sells | Product Surface | **The product owner**, to choose between options A/B/C/D. The proposal is accepted; only the choice remains |
| **[C-005](LANE_COORDINATION.md)** — the signal-profile write path | `signal_engine` | **The product owner**, on whether a customer should author relevance at all. Ownership is answered; sequencing is not |
| **[C-009](LANE_COORDINATION.md)** — an internal fault reaches a customer as a `422` | `signora_platform` | **The product owner.** A frozen-platform change under §20a, with a full proposal already recorded |
| **[C-006](LANE_COORDINATION.md)** — which lane owns `test_api_<module>.py` | Repository | **The product owner**, and deliberately: *"avoid creating a local convention that later becomes repository behaviour"* |
| **The brief's hierarchy pass (D20)** | Product Surface | **A seller in the room.** A collaborative product-design activity, not a slice — recorded so it stops being mistaken for one |
| **M9.5 Step F** | AI Platform | **The product owner.** Inserted, open, and the oldest outstanding commitment on the board |
| **`reasoning@1` has no released model** | `ai_reasoning_engine` | **The product owner.** The Decision Package would refuse at runtime. Do not tune the prompt, delimiter, schema or timeout to make it pass |

## BLOCKED — on a capability, and on which

| Item | Where | Blocked on |
|---|---|---|
| **[C-007](LANE_COORDINATION.md)** — the guided first run | Product Surface | The `target_accounts_changed` consumer in `provider_platform`. **The sequencing condition has fired** — all five declarations exist — so this is now genuinely a missing capability rather than a missing decision |
| **[B-004](BUGS.md)** — `provider_watermark` cannot tell two target accounts apart | `provider_platform` | The same consumer. **Not to be fixed opportunistically**: fixing it without the consumer leaves a schema change nothing exercises |
| **[R9-04 / D5](architecture/39-product-review-findings.md)** — what changed since you last looked | Product Surface | Per-user read state, which does not exist. **Trigger unfired** — a design partner saying they cannot tell what is new |

## DONE — promoted, and removed at the next Closeout

| Item | Lane | Promoted |
|---|---|---|
| **R2-01** — the guidance says what it is pointing at | A | `efaa987`, in `1bbee30` |
| **M12.5 slice 5** — target accounts. *M12.5 complete* | B | `3f4e988` |
| **M12.4** — research on demand | A | `c1f5985` |
| **Commit-bound certification** | QE | `1bbee30` · `624f770` |

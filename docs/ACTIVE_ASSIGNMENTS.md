# Active assignments

> **What each lane is working on right now.** Not a roadmap and not a backlog — a claim board, so two lanes cannot start the same slice.
>
> **Created 2026-08-02 by Lane A**, on the product owner's direction: *"Claim the next available task before beginning implementation. Update `ACTIVE_ASSIGNMENTS.md` immediately so no other lane starts the same work."* The file did not exist on any branch.
>
> **Its steward is the integrator**, on the same terms as [`LANE_COORDINATION.md`](LANE_COORDINATION.md) — a lane edits only its own row. The format below is a first proposal and the integrator should change it freely; what matters is that a claim is visible before work starts, not that the table looks like this.

## How it works

**Claim before you build.** A lane reads this file during the startup sequence, alongside [`BUGS.md`](BUGS.md) and [`LANE_COORDINATION.md`](LANE_COORDINATION.md), and writes its row **before** the first line of implementation — not at the end with the slice.

**A lane edits only its own row.** Adding somebody else's claim, or clearing one, is the integrator's.

> **Unblocked is not assigned.** A task nobody has claimed is available; a task nobody has claimed is *not* yours until you have claimed it. That distinction is the whole point of the file.

**A claim ends when the slice merges to `integration`.** The row moves to *Recently completed*, which exists so a lane returning after a break can see what changed without reading the log.

| Status | Meaning |
|---|---|
| `CLAIMED` | A lane has taken it and is building |
| `BLOCKED` | Claimed, and waiting on a coordination item or another lane |
| `PAUSED` | Claimed, and set down deliberately. The reason is stated |

---

## Claimed now

| Lane | Module | Slice | Status | Since | Notes |
|---|---|---|---|---|---|
| **A** | `signal_engine` · `opportunity_engine` (Product Surface) | **R2-01** — two accounts get identical guidance | `CLAIMED` | 2026-08-02 | Named by the product owner as the strongest remaining candidate |
| **B** | `commercial_profile` | M12.5 slice 5 — target accounts | — | — | Unblocked by [ADR-0036](architecture/adr/0036-target-account-contract.md); not recorded here by Lane A |
| **QE** | — | Verification of `B-001`, `B-005`, `B-006` | — | — | Not recorded here by Lane A |

> **Lane A has filled in only its own row.** The other two are shown greyed for context and should be written by their own lanes or by the integrator — a lane claiming on another lane's behalf is exactly the confusion this file prevents.

---

## Available, unclaimed

Highest value first, as assessed at the last product review. **Claim before starting.**

| Item | Where | Why it is not claimed |
|---|---|---|
| **R2-03** — an account with nothing live says nothing at all | Product Surface | 🟡, and overlaps R1-04 |
| **R11-06** — the attributes are engineering's words | Knowledge Graph | 🟡 |
| **R9-04 / D5** — what changed since you last looked | Product Surface | Needs per-user read state. **Trigger unfired** — a design partner saying they cannot tell what is new |
| **The brief's hierarchy pass** | Product Surface | **Deliberately not available to a lane.** A collaborative product-design activity that needs a seller present |

---

## Blocked, and on what

| Item | Lane | Blocked on |
|---|---|---|
| **B-004** — `provider_watermark` cannot tell two target accounts apart | A | Lane B's M12.5 slice 5. The consumer is what makes it reachable, and the product owner directed it is not to be fixed opportunistically |
| **C-005 implementation** — the signal-profile write path | A | The product owner's ruling on *whether* a customer should author relevance at all. Ownership is answered; sequencing is not |
| **C-007 implementation** — the guided first run | A | M12.5 slice 5 |
| **C-009** — an internal fault reaches a customer as a `422` | A | The product owner. A `signora_platform/` change under §20a, with a full proposal recorded |

---

## Recently completed

| Slice | Lane | Merged |
|---|---|---|
| R4-02 · R4-03 — the words the product uses when it refuses you | A | `e1a34a6` |
| B-005 · B-006 — the two defects a customer would have hit | B | `a440fad` |
| R2-02 · R3-01 — saying what the evidence cannot support | A | `64d9f2e` |
| ADR-0036 — the contract leaves the register and becomes architecture | A | `7fd512b` |
| R4-04 — a decision you can undo | A | `fba0647` |
| B-001 — `supersedes IS NULL` was never currency | A | `c0bef97` |
| M12.4 — research on demand | A | `c1f5985` |

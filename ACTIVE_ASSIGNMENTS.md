# Active assignments

> **Who is working on what, right now.** The authoritative record of work allocation, designated as such by the product owner on 2026-08-01.
>
> **Created by Lane B, and the circumstance matters.** The startup workflow was updated to require reading this file before every slice, and the file did not exist. Lane B has recorded **only the assignment the product owner made in writing**, and has deliberately left every other row unfilled rather than infer what the other lanes are doing — inferring them here would be exactly the self-assignment this register exists to prevent.

## How it works

**The product owner assigns. The integrator maintains. A lane reads.**

**A lane never assigns itself.** If its assignment completes and no new one has been made, it marks the row `Awaiting QE`, says so, and stops. Idle is a correct state; picking up the next interesting thing is not.

**Modules own architecture. Lanes are execution resources. Assignments are temporary.** A lane is assigned to a module for a slice, not for a milestone and not for good.

| Status | Meaning |
|---|---|
| `Assigned` | The lane may begin |
| `In progress` | Implementation under way |
| `Awaiting QE` | Merged to `integration`; QE has not yet validated it |
| `Available` | No assignment. **The lane waits** |

---

## Current

| Lane | Module | Slice | Status | Notes |
|---|---|---|---|---|
| **B — Commercial Profile** | `commercial_profile` | **M12.5 slice 5 — the target account list** | `In progress` | Assigned by the product owner 2026-08-01. The module's **first public contract and first published event**, governed by [ADR-0036](docs/architecture/adr/0036-target-account-contract.md). Slices 1–4 merged and awaiting QE |
| **A — Product Surface** | *not recorded* | *not recorded* | — | Lane B does not know Lane A's assignment and will not guess it. Lane A or the integrator should fill this row |
| **QE** | *not recorded* | *not recorded* | — | Same |

## Completed this milestone

| Lane | Slice | Merged | Status |
|---|---|---|---|
| B | M12.5 slice 1 — product catalog | `1ae600d` | `Awaiting QE` |
| B | M12.5 slice 2 — ICP declaration | `30e66d0` | `Awaiting QE` |
| B | M12.5 slice 3 — buying committee | `960b604` | `Awaiting QE` |
| B | M12.5 slice 4 — commercial focus | `3931b3c` | `Awaiting QE` |
| B | B-005 · B-006 — customer-visible defects | `a440fad` | `Awaiting QE` |

## Related registers

| For | Read |
|---|---|
| Defects | [`docs/BUGS.md`](docs/BUGS.md) |
| Cross-lane decisions | [`docs/LANE_COORDINATION.md`](docs/LANE_COORDINATION.md) |
| Environment | [`docs/RUNNING.md`](docs/RUNNING.md) |

# Decision Index

**Navigation only — enough to prevent rediscovery, and no more.**
⛔ **Not a decision register.** [`LANE_COORDINATION.md`](../../LANE_COORDINATION.md) holds every item's evidence, options and history; [`DECISION_REGISTER.md`](../../DECISION_REGISTER.md) holds the rulings. **This file restates neither.**

**Measured 2026-08-12** by filtering `LANE_COORDINATION.md` to items that are **unruled *and* block something.** ⚠️ **Regenerate rather than edit — a hand-maintained index drifts, and a stale one is worse than none.**

```
196 items in the register
 96 not terminal
 25 unruled AND blocking          ← this file
 12 of those are the product owner's or Design Authority's
 13 are Lane C's own
```

## ⚠️ The finding this index produced on its first run

⛔ **13 of the 25 blocking items are Lane C's own to answer, not the product owner's.** This office has been reporting the PO queue while carrying more blocking items than the product owner does. **That is the bottleneck §20e names — *Product Office becoming the bottleneck at approval instead of at authorship*.**

## Product owner · Design Authority — 12

| | Blocks | Topic |
|---|---|---|
| **C-106** | Promotion, jointly with C-107 | B-428's second criterion is 🔴 |
| **C-1405** | **TASK-1421 + TASK-1423** | Entry Coverage Review — 5 documents to commission |
| **C-1408** | TASK-1401, TASK-1402 | Rule precedence and interaction |
| **C-1410** | TASK-1426 | Rule 04's landing with no intent |
| **C-1419** | Named per row | The decision briefs — the PO queue itself |
| **C-1424** | B-253 | Unresolved read renders as denied permission |
| **C-1425** | TASK-466 | Action Batch's first consumer has no domain |
| **C-1428** | 2 of TASK-1462's 3 halves | §03 needs two facts nothing models |
| **C-258** | 5 of 13 call sites | `StatedAbsence` callers |
| **C-287** | **TASK-1430 entirely** | ADR-0408's mechanism vs route scope |
| **C-338** | TASK-003 | Customer attribute labels |
| **C-223** | Epic D detection half | `competitor_entry` across modules |

## Lane C's own — 13

⛔ **These need no ruling. They need this office to answer them.**

| | Blocks |
|---|---|
| **C-203** | A person's name — narrowed 2026-08 |
| **C-253** | The 403 state |
| **C-261** | The role-change producer |
| **C-262** | One sentence of TASK-1436 |
| **C-265** | One sentence of TASK-1410 |
| **C-266** | The data half of TASK-1411 |
| **C-267** | The confidence half of TASK-1427 |
| **C-268** | The route half of TASK-1405 |
| **C-274** | One clause of TASK-1440 |
| **C-275** | Top-bar slot 4 + the help half |
| **C-422** | One element of TASK-440 |
| **C-1404** | TASK-1413 |
| **C-426** | ⚠️ **QE's** — 18 Lane A rows read `IN VALIDATION` |

## Resolved — do not re-investigate

| | Resolution | Where |
|---|---|---|
| **C-107** | ✅ **`RESOLVED` 2026-08-12, no PO decision.** `_promote()` reads no severity; the circularity was one row's close condition, and B-183 closed | [C-107 row](../../LANE_COORDINATION.md) |

## How to regenerate

**Filter `LANE_COORDINATION.md` on the `Status` and `Blocks` cells: drop anything terminal — `CLOSED` · `RESOLVED` · `ANSWERED` · `SUPERSEDED` · `WITHDRAWN` · `OPERATIONAL` · `REVIEW NOTE` · `RULED` · `READY FOR IMPLEMENTATION` · `PARKED` · `REVIEW LATER` — then drop anything whose `Blocks` is empty or begins *Nothing*.**

⚠️ **The vocabulary is eleven words, not two.** 📁 **[B-432](../../BUGS.md): reading two of them is what made this office report 63 live items where there were 29.**

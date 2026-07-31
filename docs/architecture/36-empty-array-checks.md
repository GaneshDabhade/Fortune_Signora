# 36 — Nine constraints that cannot reject what they were written to reject

**Status:** Finding. **Not repaired**, beyond the two constraints in the migration that discovered it.
**Date:** 2026-07-31 · **Found during:** M10 T133, by a test written to prove a constraint fires.

---

## The defect

```sql
CHECK (array_length(evidence_ids, 1) >= 1)
```

`array_length('{}', 1)` returns **NULL**, not `0`. `NULL >= 1` is **NULL**, and a `CHECK` constraint
fails only on **FALSE**. **So the empty array — the one case each of these constraints exists to
reject — passes.**

Measured directly:

```
SELECT array_length(ARRAY[]::text[], 1) IS NULL   -- t
       (array_length(ARRAY[]::text[], 1) >= 1) IS NULL  -- t
       cardinality(ARRAY[]::text[])               -- 0
```

**And proven end to end on a shipped table.** Inserting into `signal` under a workspace context, with
`contributing_event_ids = '{}'`:

```
INSERT 0 1
ACCEPTED — a signal citing no business events is storable
```

`ck_signal_cites_business_events` did not fire. The comment above it in migration `0012` says the
opposite.

## Scope — nine constraints, five tables, six milestones

| Table | Constraint | What it claims to guarantee |
|---|---|---|
| `observation` (0010) | `ck_observation_cites_evidence` | An observation names the claims it was derived from |
| `business_event` (0011) | `ck_business_event_cites_evidence` | An event traces back to its observations |
| `business_event` (0011) | `ck_business_event_names_a_provider` | *Every conclusion is **according to** someone* |
| `signal` (0012) | `ck_signal_cites_business_events` | A hypothesis with no evidence is not a signal |
| `signal` (0012) | `ck_signal_names_event_types` | A signal names the event types beneath it |
| `buying_score` (0013) | `ck_buying_score_dissent_is_named` | **A contested score names its dissent** |
| `ai_narration` (0016) | `ck_ai_narration_cites_evidence` | A narration cites the evidence it rests on |
| `ai_reasoning` (0017) | `ck_ai_reasoning_cites_evidence` | A conclusion that cites nothing is not a conclusion |
| `ai_reasoning` (0017) | `ck_ai_reasoning_states_its_limits` | The signal catalog was consulted |

`ck_buying_score_dissent_is_named` is the sharpest: `NOT contested OR array_length(dissenting, 1) >= 1`
evaluates to NULL when a score **is** contested and its dissenting list is empty — so the one row the
constraint exists to catch is the one it passes. *Contradiction survives to the last stage* is a
ratified principle, and at the database layer nothing enforces it.

**The same migrations get the JSONB form right.** `ck_ai_narration_says_something` uses
`jsonb_array_length(statements) > 0`, which works, because `jsonb_array_length` returns `0` for `[]`.
The author knew the property mattered; **the array spelling is the trap**, and it was copied forward
six times.

## Severity

**No production defect exists today.** Every affected write path goes through a domain type that
refuses the empty case at construction — `Signal.__post_init__`, `BusinessEvent.__post_init__`, and so
on. These constraints are defence in depth, and the depth is currently zero.

**What is wrong is the claim.** Each constraint sits under a comment asserting that the domain's
guarantee also holds *"at rest, so a row arriving by any other path cannot claim to be…"*. That
sentence is false in nine places. By this repository's own definition:

> **A guard that cannot fail is not protection — it is documentation pretending to be code.**

This is the purest instance of Decorative Logic found so far: not a branch that never executes, but a
constraint the database evaluates on **every insert** and that can never return FALSE.

## Repaired here

Only the two in migration `0018`, the migration whose tests discovered it:
`ck_research_finding_cites_evidence` and `ck_research_synthesis_rests_on_findings`, now written with
**`cardinality(x) >= 1`**, which returns `0` for the empty array. Both are proven by a test that
inserts the empty case by raw SQL and requires rejection.

**The other nine are not touched**, for the same reason the identity findings were not: repairing five
tables across six milestones is not T133's scope, and the correct vehicle is one deliberate migration
with its own tests rather than a change smuggled into a task about a different module.

## Proposed follow-up — `T-CK1`

One migration replacing `array_length(x, 1) >= 1` with `cardinality(x) >= 1` in all nine constraints,
plus one test per constraint inserting the empty case and requiring rejection. **The tests are the
deliverable** — without them the next copy of the idiom reintroduces it.

`ALTER TABLE … DROP CONSTRAINT … ADD CONSTRAINT …` is additive and reversible, and no existing row can
violate the corrected form, because the domain has been refusing the empty case all along. That should
be **verified against the live tables before the migration runs**, not assumed.

**Worth pairing with `T-ID2`** (the deterministic identity registry): both are the same failure — a
guarantee stated in a comment and never asserted — and both are found the same way, by writing the
test that proves the guard fires and discovering that it cannot.

## The general rule this suggests

> **Never write `array_length(x, 1) >= n`. Use `cardinality(x) >= n`.**

Proposed for `08-technology-stack.md` or a database-conventions note, wherever PostgreSQL idioms
belong. It is one line, and it would have prevented six repetitions.

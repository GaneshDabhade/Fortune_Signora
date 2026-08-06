# 27 — Opportunity Engine

> Status: **Implemented — M6 closed 2026-07-29. This document is marked *as built*; departures from the approved proposal are recorded at the end.**
> Milestone: **M6** · Module: Opportunity Engine · Position: pipeline stage 8 · Migration **0014**
> Audience: engineers, architects, product
> Prepared: 2026-07-29, after reviewing the implemented M5B rather than its proposal.

---

## The transition this module represents

Seven stages exist. Every one of them **derives**.

A claim is a function of a raw record. An entity is a function of claims. An observation is a function of a provider's claim series, a business event of observations, a signal of business events and a profile, a buying score of signals and a scoring model. Delete any of these tables and re-run the pipeline: you get the same rows back, byte for byte, because every identity is derived from the evidence beneath it.

> **M6 is the first module whose output cannot be regenerated.**

An opportunity records that **a human committed to something**. A seller took it up, moved it to engaged, assigned it to a colleague, closed it lost with a reason. No amount of provider data reproduces that. Re-run the pipeline and every derived table returns; an opportunity does not, because it was never a function of anything.

That is the defining challenge, and it is not really about state machines:

> ## **Intelligence suggests. Humans commit.**
>
> ***Permanent architectural principle — ratified 2026-07-29.***
>
> Derived intelligence and workflow state are different kinds of data, and the platform must never let them blur. Intelligence is **rebuildable, immutable, and machine-authored**. Workflow is **accumulated, human-authored, and irreplaceable**.
>
> A buying score may **create** an opportunity. **Only a human may progress one beyond the machine-authored boundary.** Intelligence informs workflow; it never owns it.
>
> The moment workflow starts caching intelligence — or intelligence starts deciding workflow — a pipeline rebuild becomes a data-loss incident, and today it is a routine operation.

---

## The boundary, stated first

**The Opportunity Engine answers exactly one question:**

> **"What should Sales actively track?"**

It does not answer, and must never be extended to answer:

| Question | Owner |
|---|---|
| *What should Sales do?* | Recommendation Engine |
| *Which message should be sent?* | Recommendation Engine / messaging |
| *Why did this account score the way it did?* | Buying Score Engine — the ledger already answers it |
| *How should we think about this account?* | AI Reasoning Engine |
| *Which outreach should occur, and when?* | Recommendation Engine |
| *How much attention does this deserve?* | Buying Score Engine |

And one refusal specific to this module:

> **An opportunity holds no derived intelligence of its own.**
>
> It does not store the current buying score, the current signals, or a recomputed judgement of any kind. It cites the score that **caused it to exist**, immutably, and reads everything else live. A workflow table that cached a score would be a second, stale copy of the pipeline's output — and within a year something would read it in preference to the real thing.

---

## The third category of data

The platform currently holds two kinds of data. M6 introduces a third, and naming it is what keeps the boundary enforceable.

| Category | Tables | Rebuildable? | Authored by |
|---|---|---|---|
| **Derived intelligence** | `claim`, `entity`, `identity_binding`, `resolution_decision`, `relationship`, `observation`, `business_event`, `signal`, `buying_score` | **Yes** — regeneration is the rollback for a bad mapper or rule | The machine |
| **Customer configuration** | `signal_profile`, `workspace_scoring_model` | No — but **declarative**: a statement about the customer's business | A human, deliberately |
| **Workflow state** *(new)* | `opportunity`, `opportunity_state` | No — and **accumulated**: the record of work performed | A human, over time |

The second and third are both irreplaceable, but they fail differently. Losing configuration means a customer re-enters their preferences. Losing workflow means a seller's pipeline disappears — deals they were working, with no way to reconstruct which.

**Operational consequence, stated as a contract:** a pipeline rebuild regenerates category one and touches neither of the others. The `opportunity` tables join `signal_profile` and `workspace_scoring_model` in the never-rebuilt set, for a different and stronger reason.

> **A payoff of the identity discipline, worth naming.** Because every upstream id is *derived* from evidence, a full rebuild reproduces byte-identical buying score ids — so **not a single opportunity's citation is orphaned by it**. Had scores used allocated ids, a rebuild would have severed every opportunity from its reason. That was not designed for; it falls out of the rule, which is the point of the rule.

---

## Should an opportunity outlive the buying score that created it?

*Answered explicitly, as you asked, because assuming it either way silently designs the module.*

> **Yes. Always. The buying score is the reason it was *opened*, never the reason it stays open.**

A buying score is a reading with a stated expiry — M5B made that a contract. An opportunity is a commitment. If score expiry closed opportunities, then a seller mid-deal would watch it vanish because no new provider payload arrived for six weeks. **Nothing happening at a company is not evidence that a deal is dead**; it is evidence that nothing happened.

The two have different clocks, and pretending otherwise produces the worst failure mode this module could have: workflow whiplash, where a data refresh silently revokes a human's decision.

Three consequences follow:

**The citation survives supersession.** The opportunity records `originating_buying_score_id`, and because scores are **immutable** a superseded score remains readable forever. The explanation chain does not break when the score moves — it never could, because nothing upstream is ever deleted.

**The current score is read, never stored.** *"What is this account's attention today?"* is answered live through `BuyingScoreQueries`. Storing it would copy derived state into a workflow table and guarantee drift.

**Cooling evidence is surfaced, never acted upon.** An opportunity exposes a derived `evidence_state` — computed at read time from the current score, never stored, never a transition:

| `evidence_state` | Meaning |
|---|---|
| `CURRENT` | a live score exists and is within its validity |
| `COOLING` | the current score has fallen materially since the opportunity opened |
| `STALE` | the score is past its `valid_until`, or no live score exists at all |

The seller sees that the evidence went cold. **Signora does not close the deal for them.**

### The asymmetry between creation and closure

| | Automatic? | Why |
|---|---|---|
| **Creation** | **Yes** | A suggestion costs a glance to dismiss. Auto-creation is the product: the platform's job is to surface what deserves tracking. |
| **Closure** | **No** | Closing something a human is working on destroys their work. There is no symmetric argument, and the asymmetry is principled rather than cautious. |

*Recommended.* The one exception worth considering is a workspace explicitly opting into auto-dismissal of *never-engaged* `TRACKING` opportunities after a declared period — that closes a suggestion nobody accepted, not work somebody did. Offered as an option, not a default.

---

## State: alternatives evaluated

Every derived table in the platform is immutable, and `signora_app` holds **no `UPDATE` grant** on any of them. Workflow has stages. Something has to give — or does it?

**A — Mutable aggregate: a `status` column, plus a separate audit table.**
The conventional answer. *Rejected on two grounds.* It requires restoring the `UPDATE` grant on a tenant table, breaking a property that has held across nine tables and is asserted by Security Invariant. Worse, the audit table becomes a **parallel** record of the status column: two sources of truth for one fact, and when they drift they drift silently.

**B — Supersession chain: each transition is a new row naming the one it replaces.**
Exactly the `buying_score` and `signal` pattern, and appealingly consistent. *Rejected.* **The id changes on every transition**, and an opportunity is the first object in this platform that a *human* tracks by identity. "The Acme opportunity" must remain one thing across five stage changes, and M13's CRM integration will hold external references to it. Consistency with derived tables is not worth an identity that moves under the user.

**C — Immutable aggregate plus an append-only state log — recommended.**

- **`opportunity`** holds identity and the immutable facts of its creation: workspace, entity, originating score, the policy version that qualified it, when, and by what. Written once, **never updated**.
- **`opportunity_state`** is append-only. Each row is a **complete statement of the workflow state** — stage, owner, reason, actor, moment — not a delta. The latest row *is* the current state.

Three properties earn the recommendation:

1. **Stable identity across a changing lifecycle.** The thing a human tracks never moves.
2. **The status is the audit log.** Not derived from it, not kept beside it — *is* it. Drift is unrepresentable rather than merely unlikely.
3. **No `UPDATE` grant anywhere.** The platform's strongest data property survives its first contact with workflow instead of being carved out for it.

Recording complete state rather than deltas is deliberate: reading current state is one row, adding a future workflow field needs no discriminator, and no row can describe a transition whose starting point disagrees with the row before it.

**D — Full event sourcing with a materialized read model.**
*Rejected as over-engineering.* The projection would need updating (the grant returns) or rebuilding (a second rebuild path with different rules), and there is no read volume that justifies either.

### Proposed stages

| Stage | Meaning | Set by |
|---|---|---|
| `TRACKING` | Signora suggests tracking this account | **Machine** |
| `ENGAGED` | A human has taken it up | Human |
| `CLOSED_WON` | Business won | Human |
| `CLOSED_LOST` | Pursued and lost | Human |
| `DISMISSED` | Not a real opportunity — *we should not have been shown this* | Human |

> **`TRACKING` is the last machine-authored state; every state after it requires a human.** The intelligence/workflow boundary is therefore visible in the data itself rather than only in prose.

**`DISMISSED` is deliberately distinct from `CLOSED_LOST`.** One is feedback about Signora's judgement; the other is a sales outcome. Collapsing them would destroy the only signal the platform gets about its own qualification quality — the same discipline that made M5A's `IGNORED` distinct from absence.

**Reopening** is a transition, not a new opportunity: from `CLOSED_LOST` or `DISMISSED` back to `TRACKING`/`ENGAGED`, preserving one history in one place. **`CLOSED_WON` is terminal** — a won deal does not reopen, and the next deal at that account is genuinely a new opportunity.

### One open opportunity per account, and the honest limit

Without a cap, auto-creation would open a new opportunity on every qualifying score update. The rule is **at most one open opportunity per (workspace, entity)**.

**This is the one invariant in the platform that a database constraint cannot fully express.** "Open" means *the latest state row is not terminal*, and no index can say "latest". Rather than denormalize openness onto a mutable column — which would restore the `UPDATE` grant to buy a constraint — the recommendation converts the dangerous case into a conflict:

`opportunity` carries a **`generation`**, derived as the count of prior opportunities for that entity, under a unique index on `(workspace_id, entity_id, generation)`. Two concurrent auto-creations both compute generation `0`; one wins on the index and the other conflicts — the same technique that makes derived identity deduplicate throughout the pipeline. The residual case (deliberately opening a second opportunity while one is open) is refused in the application, inside the same transaction.

*Recorded as an asymmetry rather than hidden:* this is the first invariant here enforced primarily in application code, and the reason is structural, not convenience.

---

## Qualification, and the fourth ownership layer

*"At what point is an account worth tracking?"* is a commercial judgement about the customer's own business. By the ownership criterion that has decided this three times already, it is **theirs**.

| Layer | Owner | Answers |
|---|---|---|
| Signal catalog | Signora | *What hypotheses exist, and what do they mean?* |
| Signal profile | Customer | *Which do we care about?* |
| Scoring model | Customer | *How much attention does each earn?* |
| **Opportunity policy** | **Customer** | ***At what point do we start tracking?*** |

`workspace_opportunity_policy` — immutable, versioned, attributed, with a Signora-shipped default artifact so out-of-box behaviour is reviewable in a pull request. It declares the minimum score, whether a `contested` score qualifies, whether auto-creation is on, and (if adopted) the auto-dismissal period for never-engaged suggestions.

**Kept separate from the scoring model**, on the same reasoning that kept the scoring model out of the signal profile: different question, different cadence, and every opportunity records the policy version that qualified it. Folding them together would mean tuning a threshold churns the explanation of unrelated history.

> **The emerging pattern, worth stating once:** each module owns its own customer-authored policy, versioned immutably alongside its output. Four modules, four policies, no shared configuration table — which is also what keeps any of them extractable.

**What `contested` should do here is a real question.** A contested score means opposing readings are both live. Recommendation: **contested accounts qualify by default** — a fought-over account is exactly what a seller should look at — but the policy may require confidence, and the opportunity records that it was qualified from a contested score so nobody has to rediscover it.

---

## Explainability

The chain must extend, unbroken, through workflow:

```
Opportunity → Buying Score → Contribution Ledger → Signals →
Business Events → Observations → Knowledge → Claims → Provider Records
```

Three mechanisms, matching the discipline of the two modules before it:

1. **The citation is immutable and durable.** `originating_buying_score_id` is written once and points at an immutable row. It cannot be updated, and the score it names cannot be deleted or altered.
2. **The read port composes rather than copies.** `OpportunityQueries.explanation()` returns the opportunity, its full state history, and the `BuyingScoreExplanation` for the originating score — which already carries the ledger and one `SignalExplanation` per contributing signal. **M6 adds one link and re-exposes the rest; it re-derives nothing.**
3. **The chain is tested, not asserted.** AC-61 walks opportunity → raw provider record for every opportunity in the demonstration, exactly as AC-52 does for scores.

**Workflow additionally explains itself.** Every state row carries the actor and a reason, so *"why is this closed?"* has an answer that is not *"someone changed it"*.

---

## Domain model

### `Opportunity` — created once, never updated

`id` · `workspace_id` · `entity_id` · `generation` · `originating_buying_score_id` · `score_at_creation` · `contested_at_creation` · `qualification` (`AUTOMATIC` | `MANUAL`) · `policy_version` · `created_at` · `created_by` · `payload_version`

`score_at_creation` is denormalized deliberately — the same reasoning as `signal.relevance`: the opportunity stays self-describing (*"opened at 61"*) without a join, and it is a **historical fact**, not a cache of a current value.

**Identity is allocated, not derived.** The first allocated id in the pipeline, and the change is itself a signal: derived identity is what makes rebuildable things deduplicate, and an opportunity is not rebuildable. A derived id would collide a human-managed object with a re-run.

### `OpportunityState` — append-only, complete state per row

`id` · `opportunity_id` · `workspace_id` · `sequence` · `stage` · `owner_id` · `reason` · `actor_id` · `occurred_at`

`actor_id` is the human or system that caused it; `owner_id` is who holds it now. The first row is always `TRACKING` with no owner, written in the same transaction as the opportunity.

### `Opportunity.evidence_state` — derived at read time, never stored

Computed from the current score. Storing it would be caching intelligence in workflow, which is the one thing this module exists not to do.

---

## Storage

Two new module-owned tables: `opportunity` and `opportunity_state`, plus the customer-authored `workspace_opportunity_policy`. All three **tenant-owned, forced RLS, immutable** (no `UPDATE` grant), registered in `tenancy_policy.py` and added to `IMMUTABLE_TENANT_TABLES` in the same change that creates them.

`opportunity_state` is a child table rather than JSONB — unlike the contribution ledger. The ledger is written once and read whole; state rows are appended over time, queried by "latest per opportunity", and ordered. A JSONB array appended to would need an `UPDATE`.

---

## Event model

`opportunity.created` and `opportunity.stage_changed` are ratified in [06-events.md](06-events.md). Both need their payloads extended before implementation — additions to unimplemented contracts, not breaking changes:

| Event | Proposed payload |
|---|---|
| `opportunity.created` | `opportunity_id`, `entity_id`, `originating_buying_score_id`, `score_at_creation`, `contested_at_creation`, `qualification`, `stage`, `policy_version`, `payload_version` |
| `opportunity.stage_changed` | `opportunity_id`, `entity_id`, `previous_stage`, `new_stage`, `owner_id`, `actor_id`, `reason`, `sequence`, `payload_version` |

`opportunity.closed` is **not** added: `stage_changed` already carries it, and an event whose information is fully contained in another is a contract nobody keeps.

---

## Replay — and why this module breaks the pattern

Every module so far supports two replay modes. **M6 supports neither, and that must be stated loudly rather than discovered.**

Replaying opportunity creation against history would either duplicate work a human already did or overwrite it. There is no version of it that is safe.

What exists instead is **audit history**, which the state log already provides completely: every stage, owner, actor, reason, and moment, in order, immutable.

> **The operational contract:** a pipeline rebuild regenerates everything through buying scores and **must not touch `opportunity`, `opportunity_state`, `workspace_opportunity_policy`, `signal_profile`, or `workspace_scoring_model`.** Until now "rebuild the pipeline" was universally safe. After M6 it is safe *for derived intelligence* — a distinction that must be explicit in the runbook and asserted by test, not left to whoever runs it next.

---

## Account fit / ICP — recommended for separation, with the reasoning

Fit was deferred out of M5A, then out of M5B, with M6 named as its home. **Reviewing it properly for this proposal changed that recommendation, and I would rather say so than quietly include it.**

Qualifying on fit requires **resolved entity attribute values** — *this company's industry, this company's size*. The Knowledge Graph deliberately holds none: `entity` has no attribute columns, `ClaimSet` returns every contributing claim rather than a chosen value, and `ClaimReader` has no `current_value` precisely so truth resolution cannot hide behind an innocuous call. Ratified 2026-07-28.

So fit needs a **resolution policy** — a stated, versioned, explainable rule for choosing among disagreeing providers. That is a first-class architectural decision with its own principles (provider precedence? recency? corroboration? and what happens when they conflict), and inventing it inside a workflow milestone is exactly the kind of thing that belongs to the architecture rather than to an implementation session.

**Recommendation:** keep M6 focused on workflow, and treat resolved-value projection as its own small milestone before fit-based qualification is built. M6's policy declares a score threshold; a later policy version can add a fit condition without changing the opportunity model at all.

---

## Task breakdown — T102–T110 · ~8–12 ew

| ID | Task | Complexity | Depends on |
|---|---|---|---|
| **T102** | Default opportunity policy artifact, schema, loader, startup validation | M · 1 ew | — |
| **T103** | Domain: `Opportunity`, `OpportunityState`, `Stage`, allowed transitions | M · 1.5 ew | T102 |
| **T104** | Migration 0014 — three tables, forced RLS, immutable, generation index | M · 1.5 ew | T103 |
| **T105** | Customer opportunity policy: versioning, supersession, artifact fallback | S · 1 ew | T104 |
| **T106** | `QualifyOpportunity`: auto-creation, the open-per-entity rule, events | L · 2 ew | T105 |
| **T107** | `TransitionOpportunity`: stage rules, assignment with membership verification, reopening | L · 2 ew | T106 |
| **T108** | Derived `evidence_state`, read port, `explanation`, module `public/` API | M · 1.5 ew | T107 |
| **T109** | Rebuild-safety guard: derived-only regeneration, asserted by test | S · 0.5 ew | T104 |
| **T110** | Demonstration + smoke stage 14h + Security Invariants | M · 1.5 ew | all |

**Order:** T102 → T103 → T104 → T105 → T106 → T107 → T108 → T109 → T110

**Dependencies.** Inbound: M5B (buying scores), M0 (Workspace & Tenancy, for membership verification on assignment — the approved synchronous read), M1.1 (event bus). Outbound: blocks M8–M11. External: none.

---

## Acceptance criteria

| ID | Criterion |
|---|---|
| **AC-58** | **Intelligence and workflow stay separate** — `opportunity` stores no current score, no signals, and no recomputed judgement; asserted structurally |
| **AC-59** | **An opportunity outlives its originating score** — superseding, expiring, or lowering the score changes no stage, and the citation still resolves |
| **AC-60** | **Workflow is append-only** — no `UPDATE` grant on any of the three tables; stage, owner, actor and reason are recoverable in order for every opportunity |
| **AC-61** | **The chain is unbroken** — opportunity → buying score → ledger → signals → business events → observations → knowledge → claims → raw provider records, zero orphans at every hop |
| **AC-62** | **Creation is automatic; closure is not** — qualifying scores open opportunities, and no code path closes one without a human actor |
| **AC-63** | **One open opportunity per account** — concurrent qualification produces exactly one, and the loser conflicts rather than duplicating |
| **AC-64** | **A rebuild regenerates intelligence only** — regenerating the derived pipeline leaves every opportunity, state row, and policy untouched |
| **AC-65** | **Qualification is auditable** — every opportunity names the policy version that qualified it and whether it was automatic; every state row names its actor and reason |
| **AC-6** · **AC-1** · **AC-13** | Tenancy · event contract · Security Invariants extended, **each proven to fail** when its guarantee is removed |

---

## Demonstration scenario

> *"A number becomes a decision, and the decision survives the number."*
>
> An account qualifies: a buying score above the workspace's declared threshold opens an opportunity at `TRACKING`, citing the score that caused it. A second qualifying score arrives — **no second opportunity is created**.
>
> A human engages it, assigns it to a colleague who is verified as a workspace member, and assignment to a non-member is refused.
>
> Then the evidence cools: the sweep re-scores the account downward as hypotheses age out. **The opportunity does not move.** Its `evidence_state` reads `COOLING`, its stage is untouched, and its originating score — now superseded — is still readable and still explains itself in full.
>
> A human closes it `CLOSED_LOST` with a reason. The state log shows every stage, owner, actor, and reason in order. Reopening it moves it back rather than creating a new one.
>
> Finally, regenerate the derived pipeline from raw provider records. Claims, entities, observations, business events, signals and buying scores are all rebuilt — **with identical ids** — and every opportunity, every state row, and the policy are untouched. The citation still resolves.

---

## Deferred, with reasons

- **Account fit / ICP qualification** — needs a resolution policy, which is its own architectural decision (above).
- **Multiple concurrent opportunities per account** — real multi-product selling has them; the trigger is CRM integration (M13), where the external system's model becomes the constraint.
- **Opportunity value, forecast, and close date** — forecasting is a different product surface, and a value field invites the prediction this platform refuses.
- **Notes, tasks, activities** — CRM features, not intelligence. M13 integrates with the system that owns them rather than rebuilding it.
- **Automatic closure of engaged opportunities** — no argument for it that survives the asymmetry above.
- **Learned qualification thresholds** — same sequencing as every other inference: explicit configuration first, inference later *proposing* changes a human accepts.

---

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| **Workflow starts caching intelligence** — a `current_score` column appears "for the dashboard" | AC-58 as a structural invariant over the table's columns, and no such field on the read port |
| **A rebuild destroys workflow** — the runbook treats all tables alike | AC-64 asserts it by test; the never-rebuilt set is named in the operational contract |
| **The open-per-entity rule leaks** — enforced in application, not fully in the database | Generation + unique index converts the concurrent case to a conflict; the residual is a single-writer path with a regression test, and the asymmetry is recorded rather than hidden |
| **Stage sprawl** — every customer wants their own pipeline stages | Stages are Signora's vocabulary, as signal types are. Per-workspace stages are a CRM concern; the trigger is M13 |
| **Assignment to a non-member** | Membership verified server-side through the approved `WorkspaceQueryPort` read on every assignment, never trusted from the request |

---

## Definition of Done — M6

Implementation satisfying AC-58 through AC-65 plus tenancy, event-contract, and Security Invariant criteria; `make smoke` green with a new stage; `docs/architecture/` updated in the same change including `04-modules.md`, `05-module-dependencies.md`, `06-events.md`, and `21-intelligence-pipeline.md` stage 8 moved from *planned* to *built*; this document marked **as built** with every departure recorded and justified; `PROJECT_STATUS.md` and `SESSION_HANDOFF.md` updated before M7 begins.

---

## As built: decisions taken, and two departures

Every ruling of 2026-07-29 shipped as approved: **intelligence suggests, humans commit**; workflow state as a third data category with its rebuild contract; the immutable aggregate plus append-only state log; opportunities outliving their score with no automatic closure; the five stages with `DISMISSED` distinct; reopening as a transition with `CLOSED_WON` terminal; `workspace_opportunity_policy` as a separate customer-authored artifact; contested scores qualifying by default; and account fit deferred.

**The machine/human boundary is enforced three ways** — the type system (`next_state` demands an `actor_id` with no default), the domain (`OpportunityState` refuses a non-`TRACKING` stage without one), and a database CHECK. Three layers, because a boundary this important should not depend on one of them being reached.

**Workflow required no exception to immutability.** `signora_app` holds no `UPDATE` grant on any of the three tables, exactly as for every table since 0008 — and the repository offers no `delete` either, which is the stronger statement: derived tables offer deletion precisely so regeneration can be their rollback, and workflow has no regeneration to roll back to.

### Departure 1 — the state log records complete state, not transitions

The proposal described `opportunity_transition` with `from_stage`/`to_stage`. It shipped as **`opportunity_state`**, where each row is the whole workflow state — stage, owner, actor, reason.

The reason emerged while writing it: a delta row can describe a transition whose starting point disagrees with the row before it, and nothing prevents that. A state row cannot be internally inconsistent, reading the current state is one row rather than a fold, and adding a future workflow field needs no discriminator. The append-only property and the audit trail are unchanged; only the shape of the row is different.

### Departure 2 — the citation is protected by `ON DELETE RESTRICT`

The proposal said the citation was safe because scores are immutable. That is true of *updates* and says nothing about deletes — and derived tables deliberately keep `DELETE`, because regeneration is their rollback.

So a buying score cited by an opportunity cannot be deleted at all: `RESTRICT`, guarded by a Security Invariant. **Workflow is the thing here that cannot be regenerated**, so it wins the tie against a rebuild that would otherwise sever it from its reason.

### What the demonstration shows, including one honest limit

A qualifying score opens a suggestion nobody owns; re-running qualification opens nothing new; a human engages, assigns to a verified member, and closes with a reason; assignment to a non-member is refused; reopening keeps one opportunity and one history; an expiring score moves no stage while `evidence_state` reads `STALE`; the originating score still explains itself in full; and **regenerating the derived pipeline leaves every opportunity, state row, and policy untouched with its citation intact.**

**The limit:** the simulated scenario produces a modest buying score, and Signora's shipped threshold correctly declines to suggest tracking on it. Lowering the product default to make a demonstration succeed would be tuning the fixture to fit the story, so the demonstration has the **workspace author its own threshold** — which exercises the ownership layer this milestone added, and is what a real customer would do. Both behaviours are asserted: the default declines, the configured workspace qualifies. **No product default was tuned to make a demonstration pass.**

### Verified at close

**1089 backend tests** passing · **95.27%** coverage · **261 Security Invariants**, of which the 29 new ones were each proven to fail when their guarantee was removed (the actor requirement deleted, `MACHINE_AUTHORED` widened, `actor_id` given a default, an automatic-closure surface added, qualification made to write a terminal stage, `CLOSED_WON` made reopenable, a business constant introduced, the membership check removed, the contested default flipped, and at the database: five constraints dropped, the `UPDATE` grant restored, `FORCE` RLS removed, a current-score column added, and the citation FK switched to `CASCADE`) · **17 import-linter contracts** kept · mypy strict clean over 330 files · `make smoke` green across **23 stages**.
## Approval record

### Ratified 2026-07-29

| | |
|---|---|
| **1 · Intelligence suggests; humans commit** | **Ratified as a permanent architectural principle.** A buying score may *create* an opportunity; only a human may progress one beyond the machine-authored boundary. |
| **2 · Workflow state as a third data category** | Approved. Derived intelligence · customer configuration · workflow state, kept explicitly distinct, with the rebuild contract that follows. |
| **3 · The append-only state log** | **Strongly approved.** Prefer immutable history over mutable state wherever practical: the latest state may be derived; **history must never be rewritten.** |
| **4 · Opportunities outlive their score** | Approved. Buying scores explain *why* an opportunity was created; they do not control whether it remains active. |
| **5 · Account fit removed from M6** | Approved. *"Do not solve unresolved architectural problems opportunistically."* It needs an entity resolution policy, and that deserves its own milestone. |

### Resolved without asking

| Question | Resolution |
|---|---|
| **Auto-dismissal of never-engaged suggestions** | **Left out of v1.** It is configuration for a need nobody has demonstrated, which CLAUDE.md §6 forbids outright. The recorded trigger: a workspace accumulating `TRACKING` opportunities nobody ever engages. Adding it later changes one policy field and no part of the model. |

### Resolved 2026-07-29 — all as proposed

| | Question | Ruling |
|---|---|---|
| **A** | **The stage set** | `TRACKING` · `ENGAGED` · `CLOSED_WON` · `CLOSED_LOST` · `DISMISSED`. `DISMISSED` stays distinct from `CLOSED_LOST` — one is feedback about Signora's judgement, the other a sales outcome — and `TRACKING` is the only machine-authored stage. |
| **B** | **Reopening** | A transition back to `TRACKING`/`ENGAGED`, preserving one history and one stable id. **`CLOSED_WON` is terminal**; the next deal at that account is a new opportunity. |
| **C** | **The fourth ownership layer** | `workspace_opportunity_policy` is a **separate** customer-authored artifact. Folding it into the scoring model would make a threshold change churn the recorded explanation of every historical buying score. |
| **D** | **Contested scores** | **Qualify by default.** A fought-over account is exactly what a seller should look at; the policy may require confidence, and the opportunity records that it was qualified from a contested score. |

**Every question is settled. Implementation proceeds.**

---

## The write surface — M12.3, 2026-08-01

Until this slice the module had exactly one HTTP path shape: two reads, both of them the pipeline reporting itself. **`POST /workspaces/{workspace_id}/opportunities/{opportunity_id}/states` is the first write a customer can perform anywhere in Signora**, and everything about its shape follows from what it records.

### It is `states`, not `transitions`

The collection name is the storage model, deliberately. An `OpportunityState` is a *complete statement of workflow state*, not a delta — reading the current one is a single row, a future workflow field needs no discriminator, and no row can describe a change whose starting point disagrees with the row before it. Calling the collection `transitions` would name something the module does not store.

There is **no `PATCH`**, and no update grant behind one. Progress is an append, which is what makes the status *be* the audit trail rather than something kept beside it.

### `actor_id` is not on the request contract

`RecordDecisionRequest` carries `stage`, `reason` and an optional `owner_id`. Who decided comes from the verified principal.

A caller able to name its own actor could sign another member's name to a dismissal, and **the workflow history is the one record in Signora that nothing recomputes** — every derived table rebuilds byte for byte from the evidence beneath it; a decision does not. An integration test asserts the field set rather than only the behaviour, because a future author adding `actor_id` "for the CRM sync" would make impersonation possible with no other test failing.

Who *decided* and who *holds it* stay separate facts, because a manager assigning work depends on them being separate.

### The legal moves are published, never inferred

`AccountOpportunityResponse.allowed_next` is derived from `allowed_from(stage)` and ordered by the `Stage` enum's own declaration — `tracking → engaged → won → lost → dismissed`, the order work actually moves in. A client renders them in order and reimplements nothing.

Two reasons the ordering is part of the contract rather than a client concern:

- `allowed_from` returns a `frozenset`, whose iteration order would otherwise be a **hidden input** to the response.
- The first implementation sorted alphabetically — equally deterministic, and it put **"Lost"** ahead of **"I'm working this"** on every account in the product.

**The server refuses anything else regardless.** A list a caller can ignore is not enforcement, and the integration suite proves the refusal independently of the offer.

### A closed opportunity keeps its brief

`brief()` returns the open opportunity when there is one and otherwise the most recent generation. M6 shipped `None` for a closed account and M12.2 recorded the question as this milestone's to settle.

A brief that vanished the moment somebody dismissed an account would take **their own words** with it — the dismissal reason is the only feedback the platform ever receives about its own qualification quality — leave a legal reopening unreachable, and read as the product deleting the account they had just judged.

The attention list still shows open work only. **The commitment outlives the score that created it; the record outlives the commitment.**

### Failures, and what each one is honestly about

| Raised | HTTP | Why |
|---|---|---|
| `OpportunityNotFound` | **404** `opportunity_not_found` | An opportunity the caller cannot see is indistinguishable from one that never existed. A 422 saying *"that transition is illegal"* would confirm it exists, and identifiers would become enumerable one status code at a time |
| `MembershipError` | **422** `owner_not_a_member` | The *assignee* is not a member. Not 403: the caller is permitted to do this, and naming the wrong person is a fault in the request rather than in their permissions. **An incorrect attribution is worse than none** |
| `OpportunityError` | **422** `transition_refused` | Everything the domain refuses. Handler lookup walks the exception's MRO, so the two rows above still win for their own types |

**The domain's messages reach the caller verbatim**, because they were written to be read — *"A won deal does not reopen — the next deal at that account is genuinely a new opportunity, and conflating them distorts every win-rate figure computed later."* Recorded as **R4-03**: those sentences were also written for logs, and some carry identifiers a customer cannot use.

### Authorization

`opportunity:update` is granted to **owner and member alike**. A member *is* the seller; an SDR who could not take an account on or dismiss one would find the product unusable. A Security Invariant states the boundary the grant does not cross — a member still cannot rename the workspace or add a colleague — so a rewrite of this feature cannot take it away.

### Composition

`apps/api/composition/workflow.py`, separate from the read surface and not for tidiness. The attention list is six modules deep because a row needs a live score; **progressing an opportunity needs the workflow tables and a membership check, and nothing else at all.**

That asymmetry is this module's design showing through the composition root: an opportunity holds no derived intelligence, so changing one consults none. A falling score cannot revoke a seller's commitment, and a composition that handed this path a score reader would be the first step toward one that could.

---

## The row carries posture *(Lane A, 2026-08-01 — closes R9-03)*

**Recorded before implementation**, in this module's own document rather than in `38-product-design-principles.md`, which the Integrator owns (`CLAUDE.md` §20e).

### The finding

*Datadog · Contraction risk · 5 · stale* sits eleventh on the attention list, and **renders identically to** *Salesforce · New decision maker · 10*. Every element of both rows is correct.

**The word is already there and nothing shows it.** The catalog title says *"Contraction risk"*, so a reader who reads the row learns it — and a CRO scanning twelve rows for trouble has to read twelve titles. R9-03 called this *"the honest remainder of D20"*, and it is a **visual-encoding** problem rather than a missing-data one.

The Buying Score Engine computes `Posture` and **refuses to net it into the score**, precisely because *"two accounts can score identically and mean opposite things"*. The list is where that refusal stopped being visible.

### The decision

**`AccountAttentionResponse` carries `posture`, taken from the same leading contribution that already supplies `signal_type`.**

`ledger.leading()` is called on the line above and its `posture` was being dropped. This is the M12.2 `owner_id` shape again and the M12.3 `signal_type` shape again: **the field was on the object, computed, and never surfaced.**

**Null exactly when `signal_type` is null** — both come from the live score, so an account whose evidence has expired has neither. One absence, not two.

### Why the client is given a posture rather than a mapping

A component holding `{displacement_opportunity: 'risk', contraction_risk: 'risk', …}` would be a **second commercial vocabulary**, wrong the moment the catalog gained a type and invisible when it did. The same reasoning that keeps the hypothesis *title* in the catalog (**D33**) keeps its *posture* in the pipeline. The module that ranks accounts still names no hypothesis and still forms no judgement — it passes through what the ledger decided.

### Only contraction is marked, and that is a product judgement

**Expansionary and neutral rows render exactly as they do today.** Marking every row would mark almost every row — the list is mostly expansion — and this module's own rule already says it: *"a badge on every row saying 'everything is fine' is noise that trains people to stop reading badges."* **The marked minority is the signal.**

Stated plainly because it is a judgement rather than a derivation: the pipeline treats the three postures as equal categories, and the product decides that **risk earns attention a seller would otherwise have to hunt for.**

### Marked with an icon and a tone, not with colour alone

A downward arrow plus the `warning` token. **Colour alone would fail a colour-blind reader**, and accessibility is a defect class rather than an enhancement (§20c).

**`warning`, not `danger`.** A contraction risk is not an error and the account is not broken — it is a different *kind* of attention. `danger` reads as *something has gone wrong*, which would be the product overstating what the evidence says.

### What it deliberately does not do

**It does not reorder the list.** Pure score ordering stays (**D39**); posture changes what a row *says*, never where it sits — netting posture into rank is the same defect as netting it into the score.

**It does not filter.** *Show me only risk* is a volume feature and D6's trigger has not fired.

**It does not mark the brief.** The brief already shows posture per ledger line, where it belongs and where a reader has come for detail.

### Measured against the real twelve, and R9-03 understated it

| Posture | Rows |
|---|---|
| expansionary | 9 |
| **contractionary** | **2** |
| neutral | 1 |

**Two of twelve marked — 17%.** The *marked minority is the signal* design holds empirically rather than by assertion.

**Two things the measurement showed that the finding did not.**

**Both risk rows sit at the very bottom**, at scores 5 and 1 — positions eleven and twelve of twelve. That is pure score ordering working exactly as **D39** decided, and it is precisely why marking beats reordering: a manager scanning for trouble was being asked to read to the end of the list to find it.

**One of the two says nothing about risk.** `contraction_risk` renders as *"Contraction risk"* and a careful reader might catch it. **`decision_maker_departed` renders as *"Decision maker departed"*** — a neutral sentence, at score 1, at the bottom. Nothing in that row's prose tells a manager their champion has gone. R9-03 said *"the hypothesis names the risk and nothing shows it"*; for this row **the hypothesis does not name the risk either**, and posture is the only thing that carries it.

> **Recorded for the product owner, not acted on:** the two accounts most worth worrying about are the two lowest-scored. That is correct — a contraction risk with thin evidence *should* score low — and it means score answers *"how much attention"* while posture answers *"what kind"*. Ranking risk higher would net posture into the ordering, which is the defect the Buying Score Engine refuses by construction. **Whether a seller wants a risk-first view is a product question, and D6's trigger has not fired.**

---

# R4-04 — a decision you can undo *(M12.3 remainder, 2026-08-01, Lane A)*

**Recorded before implementation.** The finding is R4-04: *dismissing an account removes it from the attention list — correctly, because the list is open work — and there is no path back to it from anywhere in the product.*

## Why this, over the roadmap's next item

**Because it is not an inconvenience, it is a disabled feedback loop.** This module draws a distinction almost nothing else in the platform draws:

> `DISMISSED` is *"we should not have been shown this"*. `CLOSED_LOST` is a sales outcome. **Collapsing them would destroy the only signal the platform gets about its own qualification quality.**

And the Sales Manager's reaction to R4-04 was: *"I'd tell my reps not to dismiss anything, which defeats the point of asking them."* A rep who will not dismiss produces no qualification-quality signal at all. **The defect does not merely annoy a user — it quietly switches off the mechanism by which Signora learns it is wrong.** That is worth more than another read surface.

**It has also got worse since it was written.** D41 made the account brief read the ranked list, so a dismissal now removes an account from the *sequence a seller is working*, not merely from the list they left behind. A 🟠 that compounds is one to take.

## The decision

**The attention page grows a second section: the accounts you have decided about — and it appears only when there are some.**

```
  ATTENTION            12 accounts, ranked
  ─────────────────────────────────────────
  …
  ─────────────────────────────────────────
  ▸ 3 accounts you have decided about
```

**Not a filter.** D6 rejected a *mine / everyone* control on the grounds that *"a control that always shows the same thing teaches people to ignore controls"*, and that reasoning binds here. A filter implies browsing; what R4-04 needs is a **way back**. So the disclosure is absent — not empty, absent — in a workspace where nobody has decided anything, and it costs a reader who never dismisses nothing at all.

**Not a navigation entry.** The sidebar is two items and D38 settled why: *none of the six customer journeys is "show me all the X"*, and navigation is journeys rather than data. *"What did I decide?"* is a question about the one list, asked from the one list. The shell is also frozen (§20c), and a slice that needed to change it would be a finding rather than a change.

**At the bottom, under the list.** The same reasoning D41 used for the sequence: a reader who has worked the list is at the bottom of it, and that is where the question *"wait, what did I just dismiss?"* is actually asked.

**It shows the reason, in the customer's own words.** `opportunity_state.reason` is required on every transition and has never been rendered anywhere. It costs nothing to show — the row already carries it — and it is the only place in Signora that shows a customer their own judgement back to them. That is what makes the section worth opening rather than merely reachable.

**The row opens the same brief.** Reopening already works there and was built to survive closure in M12.3, *"precisely because this was foreseeable"*. No second workflow surface, no second set of moves.

## What it deliberately does not do

**No undo button.** A dismissal is a recorded decision with a reason; un-recording it would edit history. Reopening is a *transition* — a new state row, with its own reason and its own actor — and the brief already offers exactly that. The distinction is the module's whole design and a one-click undo would erase it.

**No "who dismissed it" beyond what the tier knows.** **D23** stands: the Python tier verifies tokens without learning who a person is, so a row says *yours* or *taken*. A manager reviewing their reps' dismissals wants a name, and that is a cross-tier profile contract rather than a list feature.

**No time window.** *"Decided today"* would need a threshold nobody measured, and §14 is explicit about that. Newest first, paginated, the whole history.

**No count on the attention rows.** The number of accounts an account has been dismissed and reopened is real and is nobody's morning question.

---

# R4-02 and R4-03 — the words the product uses when it refuses you *(2026-08-02, Lane A)*

**Recorded before implementation.** The one screen where a seller *acts* is the one screen whose failure copy nobody has read as a customer.

## Why this slice

Every reachable journey is shipped and the brief's hierarchy pass is **deliberately not a lane's to take alone** — it is a collaborative product-design activity that wants real sellers. What is left that a lane can do well is the refinement nobody has looked at: **what Signora says when it says no.**

**R4-03 turned out to be a pattern rather than an instance**, which is the shape the last two slices found twice. Scanning every exception type registered in an `ERROR_MAPPING` — the messages that reach a customer *verbatim* — found three defects in one function:

| What a customer sees | Why it is wrong |
|---|---|
| `opportunity 6d1510af-… is already engaged with the same owner.` | An identifier the reader cannot use. **R4-03** |
| `'tracking' cannot become 'closed_won'.` | The platform's schema keys, on a screen ADR-0034 says never shows them |
| `Allowed from here: ['closed_lost', 'dismissed', 'engaged']` | **A Python list repr.** Brackets, quotes and underscores, rendered to a salesperson |

The third was not in R4-03 and is the worst of the three. *(RevOps: "It looks like a stack trace leaked into the UI." They were describing the UUID. They had not seen the list.)*

## The decisions

### R4-02 · A move is named for where it is going **and where it came from**

*"What's the difference between Lost and Not a real opportunity if I never touched it?"* — which is exactly the distinction this module exists to protect, unreadable at the point of use.

`ACTION_WORDING` is keyed by target stage. **It becomes keyed by `(from, to)`**, and one entry changes: from `tracking`, `closed_lost` reads **"Lost without pursuing"**. Everything else is unchanged, because everything else already reads correctly from every state it is offered from.

**The domain is not touched.** The stage set is right — a deal you knew about, did not chase, and that closed elsewhere *is* a loss — and R4-02 says so. This is a labelling problem and the fix stays in the label.

### R4-03 · Identifiers leave the messages, at the source

Per R4-03's own recommendation, and it is the stronger of the two options it offered: **a message that needs sanitising before display is a message that will be shown unsanitised somewhere else.**

The opportunity id is already on the row, in the log line and on the correlation id. It is in the message because the message was written for a log, and it has been customer copy since M12.3 without anybody re-reading it as one.

**Asserted repository-wide, not per-message.** A Security Invariant now walks every exception type registered in an `ERROR_MAPPING` and refuses any that formats an identifier into its message. The same shape as the `supersedes IS NULL` scan, and for the same reason: this is a pattern a developer following the file in front of them will reproduce.

### The transition refusal gets a sentence about **staleness**, because that is what it means to a person

**A departure from M12.3's rule that the domain's own words reach the customer, and the reason is narrow.**

That rule is right where the domain's explanation is something a customer can act on. Here it is not: **a customer can only ever reach this refusal by being out of date.** The dialog offers exactly `allowed_next`, derived server-side, so an illegal move requires a stale page or a colleague acting concurrently — and *"'tracking' cannot become 'closed_won'"* answers a question they did not ask.

So `transition_refused` renders **"This account has moved since you opened this page. Reload to see where it stands."**

**This is not a second copy of the rules.** It states no rule — that is precisely what makes it safe to hold client-side, where a transition table would not be. The server's prose is unchanged and still reaches logs, the API and any other consumer.

## What this deliberately does not do

**It does not restructure the error envelope.** The correct long-term fix is the domain raising *facts* — from-stage, to-stage — and the interface carrying them in `details` so the client composes the sentence from the wording map it already owns. **`details` exists on the envelope and the platform's domain handler does not populate it**, and that handler is `signora_platform/` and frozen (§20a). **Raised as a coordination item rather than half-built.**

**It does not soften `dismissed`.** *"Not a real opportunity"* stays. It is feedback about Signora's judgement rather than a sales outcome, and blurring the two would destroy the only signal the platform gets about its own qualification quality.

**It does not add a confidence or severity to a refusal.** A refusal is certain; the product knows exactly why it refused.

## What the invariant found, and the finding underneath it

Writing the scan as a repository-wide rule rather than a per-message assertion found **four more** beyond the three R4-03 described — in a second module as well as this one:

```
  ai_research_engine/application/queries.py   ResearchArtifactMissing  {task_id}
  ai_research_engine/domain/request.py        ResearchRequestError     {task_id}
  opportunity_engine/domain/opportunity.py    OpportunityError         {id}
  opportunity_engine/domain/opportunity.py    OpportunityError         {opportunity_id}
```

All seven are fixed. **But the four the scan found are a different kind of error from the three R4-03 described, and that difference is a finding.**

### One exception class is serving two purposes, and the mapping cannot tell them apart

The three R4-03 named are **refusals**: *you cannot do that.* The four the scan found are **invariant violations**: *this cannot have happened.* A negative score at creation, a state row with no reason, a completed request whose artifact is missing — none is anything a customer did.

`ERROR_MAPPING` maps `OpportunityError → 422 transition_refused`, and `OpportunityError` is the base of both. **So an internal fault renders to a customer as though they had made an illegal move**, under a code that names a transition. That is a false attribution of exactly the kind the AI Platform ruled against:

> **Failure attribution must be truthful.** *An error must never name a component that was not involved… an incorrect attribution is worse than none, because it misdirects the investigation.*

Removing the identifiers makes the messages safe to show, which is this slice. **It does not make them true.**

**The fix is to split the hierarchy** — a base for refusals, which maps to `422`, and a separate one for invariant violations, which does not map at all and becomes a `500`. It is a small change in both modules and it needs one thing this lane cannot supply: **`signora_platform/api/errors.py` registers no catch-all handler**, so an unmapped exception bypasses the standard envelope entirely and returns a bare framework `500`. Splitting the hierarchy without that would trade a wrong code for a wrong envelope.

**Raised as a coordination item rather than half-built**, per the rule that a slice needing another module pauses instead of designing both halves alone.

---

## TASK-406 preparation — the predicate exists; its inputs are the remaining design

**Prepared 2026-08-05 by Lane B**, under the product owner's preparation-first model. TASK-406 is blocked only on sequencing — [TASK-434](../BACKLOG.md) shipped the predicate and is with QE — so this records what the slice will actually be, to eliminate the investigation before it starts.

> ⚠️ **Corrected the same day, on resuming after TASK-434 was promoted.** *"Blocked only on sequencing"* was **wrong**, and the correction is the reason this section exists at all: **the projection below is not merely undesigned, it is unreachable from here.** `ClaimReader.for_subjects` keys on a **provider** identity, the `entity_id → SubjectRef` binding lives only in `knowledge_graph`, and **`pyproject.toml` forbids `modules.opportunity_engine` → `modules.knowledge_graph` in full** — [05](05-module-dependencies.md) gives this module **one** upstream edge and it is the Buying Score Engine. **Raised as [C-332](../LANE_COORDINATION.md); a new edge is 🔴 and no code was written.**
>
> **The correction is dated rather than rewritten** (`CLAUDE.md` §2). The design below stands and is what the slice becomes **once an edge exists** — the finding is that reading a claim set from here is not currently permitted, not that the projection was the wrong idea.
>
> ⛔ **And it blocks both halves.** The backlog's *"the per-criterion lift half is unaffected and needs nothing new"* does not survive arithmetic: lift is `P(win | matches criterion) ÷ P(win)`, and **every term needs the predicate**, which needs these attributes. [C-330](../LANE_COORDINATION.md) said so before TASK-434 was written; the amendment overlooked it.

### Three pieces, and two of them now exist

| | Where | State |
|---|---|---|
| **The criteria** | `commercial_profile/public/` `IcpReader` | ✅ **Shipped at TASK-434.** Thirteen views existed and none was the ICP |
| **The predicate** | `commercial_profile/domain/evaluation.evaluate` | ✅ **Shipped at TASK-434.** Pure; the caller supplies the facts |
| **The observed attributes** | — | ⚠️ **Does not exist, and this is the slice** |

**`ObservedAttributes` takes `industry`, `country`, `employees`, and the canonical vocabulary carries all three** — `ClaimAttribute.INDUSTRY`, `COUNTRY`, `EMPLOYEE_COUNT`. So the facts are recorded. **What is missing is the step from claims to a value.**

### Why that step is a design and not a lookup

`knowledge_graph/public/` publishes *"identity and evidence, **never a resolved value**"*, and [22](22-knowledge-graph.md) states the consequence deliberately:

> *"If a downstream module demonstrates it needs a resolved value, that is a **projection to design with its rule stated** — not a convenience method."*

**TASK-406 is that demonstration.** It reads `ClaimSet` for the three attributes and must decide which claim is *the* observed value.

### The precedent is in the same module and is exact

**`select_name` already does this for the account name** and states its rule in the code: *"the most recently observed claim wins… ties break on provider name"*, reporting `NameAgreement` alongside — and it explicitly refuses provider precedence, because *"provider precedence is a customer policy… encoding one here would put an unreviewed judgement in the substrate"*.

**The projection TASK-406 needs is that shape, three more times.** Most-recent-wins, ties on provider, agreement reported. Nothing new is invented and the refusal is inherited: a lane must not rank providers here either.

### The one question the slice must answer, and it is not a lane's to assume

**What does a *disputed* attribute mean to the predicate?** `select_name` can return `DISPUTED` — two providers naming the same company differently. For a name the product shows the newest and says so. For an ICP criterion the question is sharper:

> **If one provider says `Fintech` and another says `Banking`, is the account measured or `UNMEASURED`?**

**Both answers are defensible and they are not equivalent.** Taking the newest makes the verdict decisive on evidence the customer can see is contested. Returning `UNMEASURED` is honest and will mark more accounts unknown than a seller expects.

**Recorded rather than chosen.** TASK-434 deliberately left the `UNMEASURED` policy to *"whichever consumer has a reason for it, stated where a customer can see it"* — and this is the first consumer, so this is where that reason gets written down.

### What remains genuinely out of scope

**No fitted weights, no refit, no drift** — TASK-406's own non-goals, and they are a model rather than a measurement. **No synonym catalog** — 443 M1, a reviewed artifact, and TASK-434 asserts the limitation in a test so it stays visible.

---

## TASK-438 — the pipeline says how it is doing

**Delivered 2026-08-05 by Lane B.** `GET /workspaces/{id}/pipeline-health`, four sections in one response, and **every figure derived on request from `opportunity_state`** — a table that was already append-only and already carried everything needed.

### Why nothing was stored

**No migration, no table, no column.** Conversion is a set intersection over stages, ageing is a subtraction, movement is a `WHERE occurred_at >`, and a roll-up is a `GROUP BY` — so a stored dashboard row would be a second representation of a fact the state log already holds, and the two would eventually disagree (§2). **The state log is the authoritative representation; this is a view of it.**

### Where the split falls, and why it is not the obvious one

**The counting is in SQL and the rules are in `domain/pipeline_health.py`**, which is deliberately not *"aggregation is infrastructure, so put it all there"*.

| | |
|---|---|
| **In the repository** | `GROUP BY`, `COUNT(DISTINCT …)`, the self-join that finds the start of a stage's *current run*. **A workspace's history is unbounded** and counting it in Python would mean fetching all of it (§14) |
| **In the domain** | Which stages form the funnel · what a conversion is when nothing entered · how a median breaks on an even count · whether `DISMISSED` is a loss |

**The test is whether a customer could argue with it.** Nobody disputes a `COUNT`; people dispute whether a dismissal counts as a loss. **Everything disputable is a pure function with a test naming the sentence a CRO would say.**

### Three rules worth stating, because each had a wrong answer available

**A rate over nothing is `null`, never `0%`.** A new workspace reading *"0% conversion"* would act on a measurement nobody took. This is [TASK-406](../BACKLOG.md)'s discipline — *"a criterion no outcome data supports says so rather than reporting `1.0×`"* — and it is the same defect either way: **a figure invented from no evidence looks exactly like one measured from plenty.**

**`DISMISSED` is counted in neither `won` nor `lost`.** It is a qualification judgement rather than a commercial outcome, and folding it into `lost` would make a rep who triages honestly look like a rep who loses deals — which is precisely the incentive `DISMISSED` exists to avoid creating.

**Ageing measures the *current run* of a stage.** An account closed lost in March and reopened yesterday has been in `TRACKING` for one day. Reporting five months would put the wrong account at the top of the list somebody is meant to chase.

### `now` is a parameter and has no default

Reading the clock inside the query would make two sections of one dashboard disagree by however long the request took, and would stop the same request replaying to the same answer. **A hidden input is an architecture defect, not an implementation detail** (§2) — so the router reads the clock once, at the composition edge, and passes it in.

### ⛔ The fifth section is absent, and absent is not empty

**The approved screen has five sections. This delivers four.** *ICP coverage, in versus outside* needs a predicate that can say which cohort an account is in; the predicate exists and **nothing constructs what it reads**, and this module is forbidden `modules.knowledge_graph` in full ([C-332](../LANE_COORDINATION.md)).

> **It is not returned as zeroes.** A zero would render as *"no accounts match your ICP"* — a different statement, and a false one. **The field is not in the response at all**, which is the only shape that cannot be misread.

⚠️ **[TASK-438](../BACKLOG.md)'s row calls this section *"newly unblocked"* and *"a call to a published predicate"*, and [444 §108](444-executive-dashboard-domain-assessment.md) lists it among *"the five sections that need nothing."* Both were written before C-332 and neither survives checking.** Recorded here rather than corrected there — those are Lane C's documents.

### No forecast, and that is the row's discipline rather than an omission

**No probability, no deal value, no plan, no quarter.** All four are [C-418](../LANE_COORDINATION.md), and `buying_score_engine` refuses the first in writing: a score *"prioritizes commercial attention; it does not forecast a purchase."* **This endpoint reports what the pipeline is, never what it will be.**

### The roll-up by owner exposes nothing new, and that was checked rather than assumed

[C-418](../LANE_COORDINATION.md) records that *"a roll-up by owner is, by construction, everybody's performance on one page"* and that this is the first screen whose data is sensitive between colleagues. **Measured before building it: `OwnerScope.ALL` is already the default on the shipped attention list**, and every member may call it — so every member can already read every account and its `owner_id`, one page at a time. **A roll-up aggregates data the product already discloses**; it discloses no new fact. C-418's concern is real for plans, targets and quotas, **none of which exist**, and 444 reaches the same place: it *"becomes real only if C-418 is answered yes."*

### How to see it

**Settings → nothing.** This is an API slice: `GET /workspaces/{id}/pipeline-health`. Move an account from *tracking* to *engaged* on the accounts list, call it again, and the funnel's first step moves from *0 of 2* to *1 of 2* with the reason you typed at the top of the movement feed. **There is no screen yet, and that is stated rather than dressed up** (§2) — the Executive Dashboard is [410](410-approved-ui-specification.md) #3 and unbuilt.

---

## TASK-406 — an ICP criterion is scored against outcomes

**Delivered 2026-08-06 by Lane B.** `GET /workspaces/{id}/icp-performance`. **The row three coordination items were about**, and the reason all three were worth raising.

### The chain, because it is the point

| | What was missing | Found by |
|---|---|---|
| **[C-330](../LANE_COORDINATION.md)** | Nothing could say whether an account matches a criterion | Claiming this row and **refusing to invent one inside it** |
| **[C-332](../LANE_COORDINATION.md)** | Nothing could construct the predicate's input | TASK-434 promoting |
| — | Nothing outside `commercial_profile` could **call** the predicate | Resuming this row |
| — | The attributes reader was **per-account**; a backtest needs **per-cohort** | Wiring the measurement |

**Each was invisible until the next step existed**, and each would have been a silent wrong answer if inlined instead. **The first refusal cost three items and was worth all three**: the alternative was up to sixteen consumers each deciding for themselves what *"in the ICP"* means, with every disagreement invisible because each answer looks right in isolation.

### Where it lives, and why

**[C-328](../LANE_COORDINATION.md), ruled:** *"`commercial_profile` declares. `opportunity_engine` measures."* **The module that owns outcomes measures against them.** The trade-off was stated rather than buried — the surface is the ICP Builder, which is `commercial_profile`'s screen, so **the value a seller reads is computed by a module they never see named.** That is already true of every derived fact in the product; the alternative is a declaring module grading its own input.

**Both reads are through `public/` and nothing else**, on the two edges that were ruled open — and the predicate is **called, never reimplemented**.

### The arithmetic and the four decisions in it

> **Lift is `P(won | criterion satisfied) ÷ P(won overall)`.**

| | |
|---|---|
| **`UNMEASURED` accounts leave the denominator** | TASK-434 left this policy to *"whichever consumer has a reason for it"*, **and this is that consumer.** An account nobody has described is **not evidence** about whether a criterion predicts. Counting it as failing would make a criterion look worse the less Signora knew — the opposite of the truth. `unmeasured` reports how many left |
| **A `DISPUTED` attribute is still measured** | The reader returns the most recent value with the disagreement named. **Treating a contested observation as unknown discards evidence the platform genuinely has** — the surface shows the dispute, the measurement uses the value |
| **`DISMISSED` is not an outcome** | It is feedback about Signora's own qualification. **Folding it into losses would make a criterion look unpredictive because the platform surfaced the wrong accounts** — a different failure with a different owner |
| **`None`, never `1.0`** | Nothing satisfied it, nothing measured, or **nothing won yet** — the last is what a young workspace hits, where `1.0` would read *"this criterion is neutral"* when the truth is *"there are no wins to compare against"* |

**Below 1.0 is a real answer**: the criterion is selecting *against* you. **The most useful thing this can say, and the one nobody expects to see.**

**`is_directional` is `satisfied < 22`, taken from the approved screen's own sentence** — *"2.2× lift on only 22 deals; treat as directional, not settled"* — so the measurement and the screen agree about what small means rather than each carrying its own number.

### Bounded, and guarded at the boundary

**`MEASUREMENT_LIMIT = 500`** — a backtest over unbounded history is an unbounded fetch wearing a date (§14). Far past the point where a lift stops being directional, so it constrains cost and not the answer.

**Two guards where a published boundary meets a typed predicate**: a value that arrived as the wrong shape produces `UNMEASURED` rather than a `TypeError` inside the predicate, and `bool` is rejected for `employee_count` because `bool` is an `int` in Python and would silently measure `True` as one employee.

### ⛔ No overall verdict

Rolling three criteria into *"your ICP is good"* needs a rule for the unmeasured ones, and every available rule is a judgement. **The endpoint returns the evidence and leaves the judgement where it belongs.**

### How to see it

**Declare an ICP under Settings → Products, decide a few accounts, then ask for ICP performance.** A criterion your won deals share reads above `1.0×`; one they do not reads below it; one nothing supports reads `null` rather than pretending to be neutral — and every figure says how many accounts it is standing on.

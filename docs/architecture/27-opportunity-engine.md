# 27 — Opportunity Engine

> Status: **Proposal — awaiting approval. Not implemented.**
> Milestone: **M6** · Module: Opportunity Engine · Position: pipeline stage 8
> Audience: engineers, architects, product
> Prepared: 2026-07-29, after reviewing the implemented M5B rather than its proposal.

---

## The transition this module represents

Seven stages exist. Every one of them **derives**.

A claim is a function of a raw record. An entity is a function of claims. An observation is a function of a provider's claim series, a business event of observations, a signal of business events and a profile, a buying score of signals and a scoring model. Delete any of these tables and re-run the pipeline: you get the same rows back, byte for byte, because every identity is derived from the evidence beneath it.

> **M6 is the first module whose output cannot be regenerated.**

An opportunity records that **a human committed to something**. A seller took it up, moved it to engaged, assigned it to a colleague, closed it lost with a reason. No amount of provider data reproduces that. Re-run the pipeline and every derived table returns; an opportunity does not, because it was never a function of anything.

That is the defining challenge, and it is not really about state machines:

> **Derived intelligence and workflow state are different kinds of data, and the platform must never let them blur.**
>
> Intelligence is **rebuildable, immutable, and machine-authored**. Workflow is **accumulated, human-authored, and irreplaceable**. The moment workflow starts caching intelligence — or intelligence starts depending on workflow — a pipeline rebuild becomes a data-loss incident, and today it is a routine operation.

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

## Open questions for approval

1. **Intelligence versus workflow as a permanent principle** — do you ratify *"derived intelligence is rebuildable and machine-authored; workflow state is accumulated and irreplaceable; neither may store the other"*, with the rebuild contract that follows?
2. **The state model** — approve the immutable aggregate plus append-only state log (option C), accepting a join for "current stage" in exchange for stable identity and no `UPDATE` grant?
3. **Opportunities outlive their score** — approve, with `evidence_state` derived at read time and **no automatic closure**?
4. **The stage set** — approve `TRACKING` / `ENGAGED` / `CLOSED_WON` / `CLOSED_LOST` / `DISMISSED`, with `DISMISSED` distinct as feedback about Signora's own judgement?
5. **Reopening** — approve reopening as a transition, with `CLOSED_WON` terminal?
6. **The fourth ownership layer** — approve `workspace_opportunity_policy` as a separate customer-authored artifact?
7. **Contested scores qualify by default** — approve, with the policy able to require confidence?
8. **Account fit separated from M6** — approve deferring it until a resolution policy exists, rather than inventing one inside this milestone?
9. **Auto-dismissal of never-engaged suggestions** — offer it as an opt-in policy field, or leave it out of v1 entirely?

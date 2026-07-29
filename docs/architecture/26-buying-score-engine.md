# 26 — Buying Score Engine

> Status: **Proposal — awaiting approval. Not implemented.**
> Milestone: **M5B** · Module: Buying Score Engine · Position: pipeline stage 7
> Audience: engineers, architects, product
> Prepared: 2026-07-29, after reviewing the implemented M5A rather than the M5A proposal.

---

## The transition this module represents

Every stage built so far has **added** information and destroyed none.

Claims preserved what each provider asserted, disagreements intact. The Knowledge Graph resolved identity without resolving truth. The Observation Engine detected change without judging significance. The Business Event Engine determined business meaning without assigning importance. The Signal Engine formed customer-specific hypotheses — and, when two of them contradicted each other, **kept both**.

> **M5B is the first module that deliberately reduces.**

Many live hypotheses, each with its own type, relevance, age, evidence, and rationale, become **one number and a direction**. That reduction is the module's entire product value — a seller cannot read forty signals across three hundred accounts every morning — and it is also the first genuine opportunity this architecture has had to destroy something it cannot recover.

The whole design below follows from one commitment:

> **A buying score is a *projection* of the underlying intelligence, never a replacement for it.**
>
> The number is a lossy view. The intelligence it views is not lossy, is not modified, and remains the thing a customer can challenge. If the score and the evidence ever disagree, **the evidence is right** — and the architecture must make that statement enforceable rather than aspirational.

---

## The boundary, stated first

**The Buying Score Engine answers exactly one question:**

> **"How much commercial attention should this account receive?"**

It does not answer, and must never be extended to answer:

| Question | Owner |
|---|---|
| *Is there an opportunity here?* | Opportunity Engine (M6) |
| *What should we do about it?* | Recommendation Engine |
| *How should we think about this account?* | AI Reasoning Engine |
| *What should we say to them?* | Recommendation Engine / messaging |
| *Which of these contradictory hypotheses is true?* | **Nobody, yet — see below** |
| *Does this account look like our best customers?* | Deferred — recommended for M6 |

And one refusal that is specific to this module:

> **The score is a decision-support artifact, not a source of truth about an account.**
>
> An account's truth lives in claims, the Knowledge Graph, observations, and business events. A score is what those things looked like, to one workspace, under one scoring model, at one moment. The moment a system reads the score *instead of* the intelligence, the pipeline has been quietly replaced by its own summary.

This is enforced structurally, not by convention — see [Never becoming canonical](#never-becoming-canonical).

---

## Does this module resolve contradiction, or prioritize it?

You asked whether those are the same thing. **They are not, and the distinction turns out to be the most important decision in the milestone.**

**Resolving** a contradiction means deciding which hypothesis is true. `CONTRACTION_RISK` and `EXPANSION_OPPORTUNITY` are live for Acme; resolution says *"the expansion reading is correct, discard the other."* That requires evidence this module does not have and judgement it is not qualified to make — it would need to know which provider is better informed, what the account said on last week's call, and what the seller already knows. Some of that is AI Reasoning's job; some of it is a human's; none of it is arithmetic over signals.

**Prioritizing** means ordering attention *while the contradiction stands*. It says *"whatever is happening at Acme, it warrants your attention today more than the other two hundred accounts do — and be aware it is contested."*

> **Recommendation: the Buying Score Engine prioritizes. It never resolves.**
> *Proposed permanent architectural principle.*

This has a sharp, testable consequence that rules out the most obvious implementation:

**Opposing signals must never net arithmetically.** If contraction subtracts what expansion adds, then an account being fought over scores the same as an account where nothing is happening. Those are the two most different accounts in the book, and the number would make them identical — an unrecoverable reduction, because a ledger showing `+30 −28 = 2` and a ledger showing `0` are distinguishable only if someone thinks to look, and the whole point of a score is that nobody looks.

> **A contested account warrants *more* attention, not average attention.**

So: every live signal contributes **attention**, and attention is unsigned. The commercial *posture* of each contribution (expansionary, contractionary, neutral) is preserved per-contribution in the ledger and summarized on the score as `contested`, with the dissenting signals named. The scalar answers *how much*; the ledger answers *of what kind*; the resolution is left to the modules that can actually perform it.

A worked comparison, same weights, three accounts:

| Account | Live signals | Netting model | Recommended model |
|---|---|---|---|
| Acme | expansion (strong), contraction (strong) | **2** — looks dead | **68 · contested** — look now |
| Globex | nothing | **0** | **0** |
| Initech | expansion (strong) | **30** | **34** |

The netting model gives Acme and Globex nearly the same answer. That is the failure this module exists to avoid.

---

## The reduction, examined explicitly

### What information is reduced

The scalar discards, by construction:

- **Cardinality** — nine signals and two signals both become a number.
- **Type** — which hypotheses are held.
- **Posture** — whether the attention is expansionary or defensive.
- **Recency** — whether the evidence is from Tuesday or from March.
- **Evidence** — which business events, observations, claims, and provider records underwrite it.
- **Interpretation** — which profile entry made each hypothesis relevant here.
- **Disagreement** — that two readings are in tension.

### What must remain recoverable

**All of it, exactly, from stored data — never by recomputation against today's world.**

The mechanism is the **contribution ledger**: stored with every score, one entry per contributing business event, naming the signal that carried it, the weights and decay applied, and the resulting contribution. Two properties make it recovery rather than documentation:

1. **The score is reproducible from its own ledger.** Sum the entries, apply the declared normalization, and you get the stored value — exactly, as integer arithmetic, with no reference to the clock or to current configuration. *Machine-enforced (AC-51).*
2. **Every ledger entry is walkable to a raw provider record.** Score → signal → business event → observation → entity/claim → raw record, with no orphan at any hop. *Machine-enforced (AC-52).*

### What must never be discarded

Four things, each of which would be unrecoverable if dropped even with a ledger present:

| Must never be discarded | Why it is unrecoverable otherwise |
|---|---|
| **The identity of every contributing signal** | A ledger of amounts without ids is arithmetic nobody can audit; the chain breaks at its first link. |
| **The fact of contradiction** | Netting destroys it *before* the ledger is written. Nothing downstream can tell "contested" from "quiet." |
| **The versions in force** — scoring model, profile, catalog, payload | Without them a historical score cannot be explained, only recomputed — and recomputation answers a different question. |
| **Superseded scores** | Trend is a fact about history. A mutable score has no history, so it has no trend and no audit trail of what the customer was told. |

> Stated as one rule: **a score may lose detail, but it may never lose the ability to point at the detail it lost.**

---

## Architectural alternatives, evaluated

### Storage: is a score a stored artifact or a projection?

The tension recorded at the M5A boundary is real: a score changes continuously as signals age, so a stored score is stale the moment the clock moves — but a projection cannot publish `buying_score.updated`, cannot carry `trend`, and leaves no record of what the customer was actually told.

**A — Pure projection, computed on read.** No table, always current, no staleness.
*Rejected.* `buying_score.updated` has two ratified consumers (Opportunity Engine, Timeline). There would be no history, therefore no trend, and no auditable record of the number a customer acted on six weeks ago. "What did you tell me in March?" would be answerable only by recomputing March against today's configuration, which is a different question wearing the same clothes.

**B — Stored immutable snapshot, event-triggered.** A reading, exactly as an observation is a reading. Supersession chain gives history and trend.
*Sound but incomplete.* Every input arrives as an event — except one. **Shelf-life expiry produces no event.** A signal simply stops being live when the clock passes `relevant_until`, and nothing publishes that. Scores would drift permanently upward, every account decaying into a false hot state.

**C — Stored immutable snapshot + evidence-derived staleness sweep — recommended.**
B, plus each score carries **`valid_until` = the earliest `relevant_until` among its contributions** — the first moment at which its own arithmetic provably changes. A periodic worker re-scores exactly those entities whose `valid_until` has passed.

The sweep is deterministic rather than a polling heuristic: it does not guess an interval, it reads a boundary the evidence itself declared. An entity is re-scored when, and only when, something it depends on has demonstrably aged out — and the resulting score explains itself as *"re-scored because evidence aged out"* rather than as an unexplained overnight drop.

> **A score is a reading with a stated expiry, not a live gauge.** `computed_at` and `valid_until` are both on the record, and a consumer reading a score past its `valid_until` can tell.

**Recompute triggers:** `signal.generated` · `signal.superseded` · scoring-model version change · signal-profile version change · staleness sweep.

### Decay: how much is a hypothesis worth as it ages?

| Option | Assessment |
|---|---|
| **None** — full weight until `relevant_until`, then gone | A cliff. An account drops fourteen points overnight for no business reason a customer can name. |
| **Exponential half-life** | Introduces a per-type constant with no business meaning. *"Why 0.87?"* has no honest answer, and the AST invariants inherited from M4/M5A forbid exactly this kind of undeclared constant in rule code. |
| **Linear from `occurred_at` to `relevant_until`** — **recommended** | Full weight the day it happened, zero at the shelf life the catalog already declares, straight line between. Explainable in one sentence, and **introduces no new constant whatsoever** — it is computed entirely from two fields M5A already publishes. |

The catalog's `relevance_window_days` is already a reviewed, per-type, product-owned declaration of how long a hypothesis stays current. Linear decay reuses that judgement instead of inventing a second one beside it.

### Weighting: where does the scoring model live?

M5A settled the criterion, and it applies again unchanged: **ownership decides, not technology.** *Which* factors exist is Signora's design; *how much each matters commercially* is the customer's judgement.

**A — Weights hardcoded in M5B.** Rejected outright: it is a commercial judgement, and the module would be making it for every customer.

**B — Weights folded into `signal_profile`.** Tempting — one customer-authored table instead of two. *Rejected on two grounds.* They answer different questions at different cadences: relevance is *"do we care about this hypothesis?"*, weight is *"how much attention does caring earn?"*. Worse, folding them means every weight tweak mints a new **profile** version, and since every signal records its profile version, tuning a score would churn the explanation of every historical signal. A tuning knob must not rewrite the audit trail of a neighbouring module.

**C — A `scoring_model` table beside the profile, immutable and versioned — recommended.**
The second customer-authored artifact in the platform, a sibling of `signal_profile`. A workspace that has authored nothing falls back to a **Signora-shipped default model artifact** in the repository — the same pattern as the taxonomy and the catalog, so out-of-box behaviour is reviewable in a pull request instead of emerging from an empty table.

This gives the platform a clean three-layer ownership split:

| Layer | Owner | Where it lives | Answers |
|---|---|---|---|
| Signal catalog | **Signora** | repo artifact | *What hypotheses exist, and what do they mean?* |
| Signal profile | **Customer** | database, immutable | *Which do we care about?* |
| **Scoring model** | **Customer** | database, immutable | *How much attention does each earn?* |

The shipped default artifact declares what is globally true — per signal type, its **posture** and base weight; per relevance category, its multiplier; and the normalization ceiling. A customer's model overrides **weights and multipliers only**. It may never override posture: whether `CONTRACTION_RISK` is contractionary is a fact about the English language, not a commercial preference, and letting a workspace invert it would make `contested` meaningless across the platform.

### Deduplication: the contribution unit is the business event

The requirement recorded during M5A — *deduplicate on contributing business events, not on signals* — is best satisfied by making it structurally impossible rather than by a dedup pass.

> **The unit of contribution is the business event.** Each distinct business event contributes **at most once** to a score. Where several signals cite the same event, the contribution is attributed to the **highest-weighted citing signal**, and the others record it as `already_counted` with a stated reason and a zero contribution.

This makes the composite/constituent overlap — named rather than discovered in M5A — a non-event: a composite and the signals it enriches rest on the same grounds read two ways, and the grounds are counted once. The composite typically carries the higher weight, so it wins attribution naturally, and its added meaning ("several distinct kinds of evidence agree") shows up exactly where it should.

Both signals remain in the ledger. **Nothing is silently dropped** — a zero contribution with a reason is information; an absent row is a mystery.

*Machine-enforced (AC-53): no business event id appears twice with a non-zero contribution in any ledger.*

### Scale: what does the number mean?

`buying_score.updated` is ratified with a `score` field, so a scalar it is.

An unbounded sum is honest but unreadable — *"412"* means nothing to a CRO and cannot be compared across workspaces with different models. Bands (`COLD`/`WARM`/`HOT`) would match the `MatchStrength`/`Relevance` discipline but contradict the ratified contract and discard ordering the product needs.

**Recommended: an integer 0–100, normalized against a ceiling declared in the model artifact.** The ceiling is a declared, reviewable constant in data — the same discipline that put every materiality threshold in the taxonomy's `parameters` — never a literal in scoring code, where the inherited AST invariants would forbid it anyway. Saturation at 100 is accepted and honest: it means *"as much attention as we can justify."*

### Trend

Scores are immutable with a supersession chain, so the previous reading is exactly `supersedes` — no window, no regression, no smoothing constant. `trend` is the direction against that single previous reading, with the delta stored.

One consequence worth accepting deliberately: **a sweep-driven re-score produces `FALLING`.** An account whose evidence is aging with nothing new arriving *is* cooling, and *"nothing has happened here for six weeks"* is real commercial information that a trend computed only from new signals would hide.

### Account fit / ICP

**Recommended: not here.** Fit is a property of the account that is true whether or not anything happened; attention is a response to what happened. Folding a static property into a dynamic score means a well-fitting account with no activity permanently outranks a poorly-fitting one that just raised a round — and no consumer could tell which of the two reasons produced the number.

It belongs where *"is this worth acting on?"* is asked, with the score as one input and fit as another. **Recommend deferring to M6 (Opportunity Engine)** and recording it there rather than leaving it homeless again.

---

## Domain model

### `BuyingScore` — a reading, per workspace, per entity

| Field | Notes |
|---|---|
| `id`, `workspace_id`, `entity_id` | |
| `value` | integer 0–100 |
| `trend` | `RISING` · `STEADY` · `FALLING` — against `supersedes` |
| `delta` | signed integer against the previous reading; `0` for a first score |
| `contested` | at least one expansionary **and** one contractionary live contribution |
| `dissenting_signal_ids` | named, never merely counted — empty unless `contested` |
| `contributions` | the ledger — see below |
| `computed_at` | when Signora computed it |
| `valid_until` | earliest `relevant_until` among contributions — when the arithmetic provably changes |
| `basis_at` | the derived moment the ledger's composition last changed (identity input) |
| `trigger` | `SIGNAL_GENERATED` · `SIGNAL_SUPERSEDED` · `MODEL_CHANGED` · `PROFILE_CHANGED` · `EVIDENCE_AGED` |
| `scoring_model_version`, `profile_version`, `catalog_version`, `payload_version` | |
| `supersedes` | **backwards**, forced by immutability — the established pattern across six tables |

**No account attributes. No name, domain, industry, size, or anything else copied from the Knowledge Graph.**

### `Contribution` — one ledger entry

`business_event_id` · `signal_id` · `signal_type` · `posture` · `relevance` · `base_weight` · `relevance_multiplier` · `age_factor` · `contribution` · `counted` · `reason`

Every number that went into the arithmetic is present, so the total is checkable by hand. `reason` carries the sentence a customer reads — *"funding round, primary relevance, 12 days old"* — rendered from the same fields the auditor checks, so the explanation and the arithmetic cannot diverge. This is the two-halves discipline M5A established, applied one layer up.

### Identity

Derived, `uuid5`, keyed on `workspace_id | entity_id | scoring_model_version | profile_version | sorted(contributing signal ids) | basis_at`.

`basis_at` is **derived from evidence, never read from the clock** — the maximum over the contributing signals' generation moments and any expiry moment that triggered the re-score. A replay therefore reproduces byte-identical score ids, and the established insert-conflict deduplication continues to work. Allocating ids instead would be simpler and would break replay; the precedent across four modules is worth keeping.

---

## Never becoming canonical

Three mechanisms, because the failure mode here is cultural and will not be caught by review alone:

1. **The table cannot hold account facts.** A column-name invariant over the migration rejects attribute-like columns on `buying_score` — the same technique that keeps `entity` attribute-free in M3A. A score row that grew a `company_name` would be a de facto account record within a year, and consumers would read it.
2. **The read port exposes no account.** `BuyingScoreQueries` returns scores and explanations. It offers no entity lookup, no account summary, no "top accounts with details" convenience — those compose from the Knowledge Graph, which owns them. *(Precedent: `ClaimReader` deliberately has no `current_value`.)*
3. **The chain is tested, not asserted.** AC-52 walks score → raw provider record for every score in the demonstration. Explainability that is only documented decays; explainability that fails the build does not.

---

## Storage

One new module-owned table, `buying_score`, plus one customer-authored `scoring_model`. Both **tenant-owned, forced RLS, immutable** (no `UPDATE` grant), registered in `tenancy_policy.py` and added to `IMMUTABLE_TENANT_TABLES` **in the same change that creates them** — otherwise classification by omission silently exempts them.

The ledger is stored as `JSONB` on the score rather than as a child table: it is written once, read whole, never queried across rows, and never updated. A child table would add a join and a second immutability surface for no gain.

---

## Event model

`buying_score.updated` — ratified in [06-events.md](06-events.md) with `entity_id`, `score`, `trend`, `source_signal_ids`, `model_version`. The shape survives review unchanged, which is a good sign for the boundary.

**One proposed addition: `contested`.** A consumer that cannot tell a fought-over account from a quiet one will eventually reconstruct that fact by querying signals, which puts scoring logic in Opportunity Engine. The event is not yet implemented, so this is an addition to an unimplemented contract rather than a breaking change; it is documented in `06-events.md` in the same change.

Published through the transactional outbox, in the same transaction as the score insert. Consumers idempotent on `event_id`.

---

## Replay

Two modes, unchanged from the M5A precedent:

| Mode | Uses | Answers |
|---|---|---|
| **Historical** | the scoring model and profile versions in force at the time | *"Reproduce the number we showed them."* |
| **Current** | today's model and profile, same signal history | *"What would we say now?"* |

The second is what lets a customer preview a weighting change against their own book before adopting it — the most commercially useful thing this module can offer beyond the score itself.

---

## Task breakdown — T93–T101 · ~8–12 ew

| ID | Task | Complexity | Depends on |
|---|---|---|---|
| **T93** | Default scoring model artifact, schema, loader, startup validation | M · 1.5 ew | — |
| **T94** | Domain: `BuyingScore`, `Contribution`, `Posture`, `Trend`, derived identity | M · 1.5 ew | T93 |
| **T95** | Migration 0013 — `buying_score`, `scoring_model`, forced RLS, immutable | M · 1.5 ew | T94 |
| **T96** | Customer scoring model: versioning, supersession, artifact fallback | M · 1 ew | T95 |
| **T97** | Scoring: event-unit attribution, linear decay, normalization, ledger | L · 2 ew | T94 |
| **T98** | Contradiction detection, `contested`, dissent capture | S · 0.5 ew | T97 |
| **T99** | `ComputeBuyingScore` use case, supersession, trend, triggers, events | L · 2 ew | T96, T98 |
| **T100** | Staleness sweep worker driven by `valid_until` | M · 1 ew | T99 |
| **T101** | Read port, explanation, `public/` API, demonstration, smoke stage, Security Invariants | M · 1.5 ew | all |

**Order:** T93 → T94 → T95 → T96 → T97 → T98 → T99 → T100 → T101

**Dependencies.** Inbound: M5A (signals), M4 (business events, for the chain), M1.1 (event bus, ARQ scheduling). Outbound: blocks M6 and everything after. External: none. **Requires no change to M5A** — which is the strongest available evidence that the M5A boundary was drawn in the right place.

---

## Acceptance criteria

| ID | Criterion |
|---|---|
| **AC-50** | **Contradiction is prioritized, never resolved** — a contested account scores materially above an inert one; opposing contributions never net; `contested` and the dissenting signals are recorded |
| **AC-51** | **The score is reproducible from its own ledger** — recomputing from stored contributions yields the stored value exactly, with no reference to the clock or to current configuration |
| **AC-52** | **The chain is unbroken** — score → signals → business events → observations → knowledge → claims → raw provider records, zero orphans at every hop |
| **AC-53** | **No double counting** — no business event contributes twice to one score; overlapping signals appear with a zero contribution and a stated reason, never absent |
| **AC-54** | **The score is never canonical** — `buying_score` carries no account attributes, asserted structurally; the read port exposes no account representation |
| **AC-55** | **Decay is declared, not hidden** — ageing follows the catalog's own relevance window; no undeclared constant in scoring code, asserted by syntax-tree invariant |
| **AC-56** | **Staleness is evidence-derived** — a score expires at the earliest `relevant_until` among its contributions, and the sweep re-scores exactly those entities |
| **AC-57** | **Configuration is auditable and replayable** — every scoring model version is immutable and attributed; every score names the versions that produced it; both replay modes work and are never conflated |
| **AC-6** · **AC-1** · **AC-13** | Tenancy · event contract · Security Invariants extended, **each proven to fail** when its guarantee is removed |

---

## Demonstration scenario

> *"Three accounts, one number each — and every number survives being challenged."*
>
> **Acme** is contested: expansion evidence and contraction evidence, both live, both strong. **Globex** is quiet. **Initech** has one strong recent expansion signal.
>
> Acme scores high and is marked `contested`, naming both dissenting signals. Under a netting model it would have scored near zero — the demonstration shows both numbers side by side, because the difference *is* the architecture.
>
> Every score opens into its ledger: which business events, through which signals, at what weight, aged by how much, and which contributions were already counted and why. Following any single line reaches a raw provider payload without the caller writing a join.
>
> Then move the clock forward past a shelf life. The sweep re-scores Acme, the number falls, `trend` reads `FALLING`, and the new score explains itself as *evidence aged out* — with the previous reading still intact and still explainable through the model version that produced it.
>
> Finally, change the workspace's weighting and replay in **current** mode. The numbers change; the evidence does not; the historical scores are untouched.

---

## Deferred, with reasons

- **Account fit / ICP** — recommended for M6, where *"worth acting on"* is asked. Recorded there rather than left homeless.
- **Resolving which contradictory hypothesis is true** — needs evidence and judgement this module lacks. AI Reasoning (M8) and humans.
- **Cross-account normalization / percentile ranking** — a ranking is a different artifact from a score, and building it before a consumer exists is a contract nobody keeps.
- **Learned weights** — same sequencing as inferred relevance in M5A: explicit configuration first, inference later *proposing* changes a human accepts.
- **Score-derived alerting or thresholds** — *"notify me above 80"* is a product feature over the score, not part of it.

---

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| **The score becomes the account** — consumers read it instead of the intelligence | Three structural mechanisms (§ Never becoming canonical), one of them a build-failing chain test |
| **Sweep cost at scale** — re-scoring every expiring entity | Driven by an indexed `valid_until`, so the sweep touches only entities that provably changed; no full scans, no polling interval |
| **Weight tuning becomes unauditable** — customers tune until the number looks right | Immutable versioned models, attributed; current-mode replay lets them preview against their own history instead of tuning blind |
| **Trend noise** — many small re-scores produce jittery direction | `STEADY` band declared in the model artifact, not in code; delta stored so a consumer can apply its own view |
| **Contested becomes meaningless** if posture were configurable | Posture is Signora-owned in the shipped artifact and not overridable |

---

## Definition of Done — M5B

Implementation satisfying AC-50 through AC-57 plus tenancy, event-contract, and Security Invariant criteria; `make smoke` green with a new stage; `docs/architecture/` updated in the same change including `04-modules.md`, `05-module-dependencies.md`, `06-events.md`, and `21-intelligence-pipeline.md` stage 7 moved from *planned* to *built*; this document marked **as built** with every departure from the proposal recorded and justified; `PROJECT_STATUS.md` and `SESSION_HANDOFF.md` updated before M6 begins.

---

## Open questions for approval

1. **Prioritization over resolution** — do you ratify *"the Buying Score Engine prioritizes competing hypotheses; it never resolves them"* as a permanent principle, with the no-netting rule that follows from it?
2. **Contested as a first-class property** — approve `contested` and named dissent on the score, and its addition to the `buying_score.updated` payload?
3. **The third ownership layer** — approve `scoring_model` as a **separate** customer-authored artifact rather than folded into `signal_profile`?
4. **Posture is Signora's, weights are the customer's** — approve that a workspace may tune weights but may never invert what a signal type means commercially?
5. **The score as an expiring reading** — approve stored immutable snapshots with an evidence-derived `valid_until` and a staleness sweep, rather than a live projection?
6. **Scale** — approve 0–100 with the ceiling declared in the model artifact?
7. **Account fit deferred to M6** — approve, and record it there?

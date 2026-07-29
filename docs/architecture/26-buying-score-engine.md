# 26 — Buying Score Engine

> Status: **Proposal — core principles ratified 2026-07-29; six questions open. Not implemented.**
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

> **The Buying Score Engine prioritizes. It never resolves.**
>
> ***Permanent architectural principle — ratified 2026-07-29.***
>
> A buying score may **summarize** intelligence. It must **never replace** it.

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
B, plus each score carries **`valid_until` = the next moment at which its own arithmetic provably changes** — the earliest band transition or expiry across its contributions (see [Decay](#decay-how-much-is-a-hypothesis-worth-as-it-ages), which is what makes this boundary exact rather than approximate). A periodic worker re-scores exactly those entities whose `valid_until` has passed.

The sweep is deterministic rather than a polling heuristic: it does not guess an interval, it reads a boundary the evidence itself declared. An entity is re-scored when, and only when, something it depends on has demonstrably aged out — and the resulting score explains itself as *"re-scored because evidence aged out"* rather than as an unexplained overnight drop.

> **A score is a reading with a stated expiry, not a live gauge.** `computed_at` and `valid_until` are both on the record; the number is **exactly correct** between them, and a consumer reading a score past its `valid_until` can tell.

**Recompute triggers:** `signal.generated` · `signal.superseded` · scoring-model version change · signal-profile version change · staleness sweep.

> **This option and the decay strategy are one decision, not two.** A stored snapshot with a stated expiry is only honest if the value is constant across that interval — which rules out continuous decay, and is the finding that reversed the decay recommendation below.

### Decay: how much is a hypothesis worth as it ages?

*Evaluated in full at your instruction, on explainability, reproducibility, and operational simplicity. **The evaluation reversed the recommendation made in the first draft of this document.** The reasoning is recorded here rather than quietly corrected.*

Let a contribution have weight `w`, with `t0 = occurred_at` and `t1 = relevant_until` from the signal. Decay is an `age_factor ∈ [0,1]` multiplying `w`.

#### The axis the first draft missed

A stored score is a **snapshot with a stated expiry**. That design promises something specific:

> Between `computed_at` and `valid_until`, the stored number is *correct* — not merely recent.

**A continuous decay function breaks that promise at every instant.** If `age_factor` changes smoothly with the clock, the stored score is wrong the moment after it is written, and the error grows silently until the next sweep. A customer who checks the ledger arithmetic at 3pm against the score on their dashboard finds a mismatch, and both are "right."

So the real question is not which curve is most faithful to how commercial interest fades. It is **which decay strategy lets a stored score tell the truth**, given that continuous recomputation was already rejected under storage.

#### The four strategies

**A — No decay.** `age_factor = 1` until `t1`, then the signal is not live at all.

- *Explainability:* perfect locally, poor temporally. The score drops overnight with **no business reason a customer can name** — "nothing happened, that's precisely why."
- *Reproducibility:* perfect. The ledger stores `1.0`.
- *Operational simplicity:* **best.** The score is exactly correct until `valid_until`.
- *Cost:* no gradation at all. A three-day-old funding round and an eighty-nine-day-old one count identically, and recency is the single strongest input in prospecting. Commercially wrong.

**B — Step, in bands declared as fractions of the type's own window — recommended.**
`FRESH` (first third, ×1.0) · `RECENT` (second third, ×0.6) · `AGEING` (final third, ×0.3).

- *Explainability:* **best.** The ledger entry reads *"funding round · primary · **recent** (×0.6)"*. A band is a word a CRO already uses, and the multiplier is a rule they can argue with — *"we count evidence past a month at 60%"* is a sentence a customer can disagree with. Linear's `×0.7213` is arithmetically honest and semantically mute.
- *Reproducibility:* **best.** Decimal multipliers, no floating point, no clock dependence *within* a band. Given AC-51 demands the stored value reproduce **exactly**, avoiding float accumulation in a stored ledger is worth real money.
- *Operational simplicity:* **the deciding property.** Transitions are knowable in advance, so `valid_until` becomes *the next moment anything changes* — `min(next band transition, earliest expiry)` — and the stored score is **exactly correct** for that whole interval. The `valid_until` sweep works unmodified and now states something true.
- *Cost:* three small cliffs instead of one large one — but **each has a name**. A score that moves because evidence crossed from *Recent* to *Ageing* has a reason in the ledger. A no-decay cliff has none.

**C — Linear** from `t0` to `t1`. *(The first draft's recommendation.)*

- *Explainability:* good as a sentence, weak as a ledger entry. A customer reading `×0.7213` learns nothing they can act on or contest.
- *Reproducibility:* exact only with a moment supplied, and float-valued.
- *Operational simplicity:* **worst.** Continuous divergence between the stored score and the "true" score, permanently and silently. `valid_until` bounds only when a contribution *disappears*, not when the number *changes* — so the elegance I claimed for `valid_until` was, under linear decay, a promise the model could not keep.
- *Why the first draft preferred it:* it introduces no new constant. That remains true and is a genuine virtue — but fractional band boundaries keep it, and the trade purchased mathematical tidiness at the cost of the very explainability this module exists to protect.

**D — Exponential** half-life per type.

- *Explainability:* **worst.** *"Why 0.87?"* has no honest answer. This is exactly the undeclared magic constant the M4 and M5A syntax-tree invariants exist to forbid.
- *Reproducibility:* float-valued and never reaching zero, so it needs a cutoff constant on top of the half-life constant.
- *Operational simplicity:* linear's continuous-divergence problem, plus a second unexplainable number.

#### Summary and recommendation

| | Explainability | Reproducibility | Operational simplicity | Stored score honest? |
|---|---|---|---|---|
| No decay | Poor temporally | Perfect | Best | **Yes** |
| **Step — recommended** | **Best** | **Best** | **Good** | **Yes** |
| Linear | Moderate | Float-valued | Worst | **No** |
| Exponential | Worst | Float-valued + cutoff | Worst | **No** |

> **Recommendation: step decay, in bands expressed as fractions of the type's own relevance window.**
>
> **Step decay is the only strategy that also gives gradation and lets a stored score be exactly correct.** Continuous functions force a choice between continuous recomputation (rejected under storage) and permanent silent drift.

Boundaries are fractions of `relevance_window_days`, so they scale per type automatically — the catalog's existing per-type judgement about how long a hypothesis stays current is reused rather than duplicated, which was linear's best property and is kept. The whole platform's decay is then **five declared numbers** — three multipliers and two fractions — living in the scoring model artifact, versioned and reviewable, never in code.

Because *"how fast evidence goes stale for us"* is a commercial judgement, a customer may override the multipliers and boundaries in their own scoring model, on the same terms as weights.

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
| `ledger` | the `ContributionLedger` — see below. **The score's explanation, not a field beside it.** |
| `computed_at` | when Signora computed it |
| `valid_until` | the next band transition or expiry across contributions — derived by the ledger |
| `basis_at` | the derived moment the ledger's composition last changed (identity input) |
| `trigger` | `SIGNAL_GENERATED` · `SIGNAL_SUPERSEDED` · `MODEL_CHANGED` · `PROFILE_CHANGED` · `EVIDENCE_AGED` |
| `scoring_model_version`, `profile_version`, `catalog_version`, `payload_version` | |
| `supersedes` | **backwards**, forced by immutability — the established pattern across six tables |

**No account attributes. No name, domain, industry, size, or anything else copied from the Knowledge Graph.**

### `ContributionLedger` — a first-class domain object

*Ratified as first-class at your instruction. It is **the explanation of the score**, not an implementation detail of computing one — without it the score is opaque, and an opaque score is precisely the artifact this module must not produce.*

Modelling it as a bare `list[Contribution]` would be the anemic-model smell §4 forbids: the behaviour that gives the ledger meaning would drain into a service, and each caller would re-derive it slightly differently. The ledger therefore **owns the questions only it can answer**:

| Behaviour | Answers |
|---|---|
| `total()` | the raw sum before normalization |
| `reproduce() -> int` | the score, recomputed from stored entries alone — no clock, no configuration (AC-51) |
| `is_contested` | at least one expansionary **and** one contractionary counted contribution |
| `dissent()` | the opposing signals, **named** |
| `valid_until(from)` | the next moment the arithmetic changes — earliest band transition or expiry |
| `counted_events()` | the distinct business events counted exactly once (AC-53) |
| `posture_summary()` | attention by posture, never summed into the scalar |

Two invariants live on the object, checked at construction: **no business event counted twice**, and **`reproduce()` equals the score it belongs to**. A ledger that does not reproduce its own score is not a discrepancy to reconcile later — it is a corrupt explanation, and it must fail loudly at the moment it is built.

The ledger is also the **reversal mechanism**: every reduction the score performs is undone by reading it. That is what makes the reduction safe rather than lossy.

#### `Contribution` — one entry

`business_event_id` · `signal_id` · `signal_type` · `posture` · `relevance` · `base_weight` · `relevance_multiplier` · `age_band` · `age_factor` · `contribution` · `counted` · `reason`

Every number that went into the arithmetic is present, so the total is checkable by hand. `age_band` carries the word (`FRESH`/`RECENT`/`AGEING`) beside the multiplier, because a band is what a customer can argue with and a decimal is not. `reason` carries the sentence they read — *"funding round · primary · recent (×0.6)"* — rendered from the same fields the auditor checks, so the explanation and the arithmetic cannot diverge. This is the two-halves discipline M5A established, applied one layer up.

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
| **T97** | `ContributionLedger` as a domain object: event-unit attribution, band decay, normalization, reproduction and no-double-count invariants | L · 2 ew | T94 |
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
| **AC-55** | **Decay is declared, not hidden** — bands are fractions of the catalog's own relevance window, declared in the model artifact; no undeclared constant in scoring code, asserted by syntax-tree invariant; every contribution names its band |
| **AC-56** | **A stored score is exactly correct until it expires** — recomputing at any moment between `computed_at` and `valid_until` yields the stored value unchanged; the sweep re-scores exactly those entities whose boundary has passed |
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

## Approval status

### Ratified 2026-07-29

| | |
|---|---|
| **1 · Prioritization over resolution** | **Ratified as a permanent architectural principle**, with the no-netting rule that follows from it. |
| **2 · Contradiction preserved** | Approved. Opposing hypotheses never cancel mathematically; the ledger preserves competing interpretations. |
| **3 · The ledger is first-class** | Approved. Modelled as a domain object with behaviour — *it is the explanation of the score*. |
| **4 · Reduction framing** | Approved. Every design decision is evaluated against *reduced / recoverable / never discarded*. |
| **5 · Non-canonical, structurally** | Approved. A score remains a projection over signals, never an alternative representation of account state. |
| **6 · Decay** | **Evaluated as directed; recommendation reversed to step decay.** Awaiting confirmation of the reversal. |

### Still open — implementation waits on these

| | Question | My recommendation |
|---|---|---|
| **A** | **The reversal itself** — linear → **step decay** in bands that are fractions of the type's own relevance window. The deciding argument is that a continuous function makes a stored score permanently and silently wrong, while a discrete one makes `valid_until` state something true. | Adopt step. |
| **B** | **The third ownership layer** — `scoring_model` as a **separate** customer-authored artifact, not folded into `signal_profile`, so tuning a score never churns the audit trail of every historical signal. | Separate. |
| **C** | **Posture is Signora's, weights are the customer's** — a workspace tunes weights, multipliers, and band boundaries, but may never invert what a signal type means commercially. | Approve. |
| **D** | **Scale** — integer 0–100, ceiling declared in the model artifact rather than in code. | Approve. |
| **E** | **`contested` on the `buying_score.updated` payload** — an addition to a ratified-but-unimplemented contract, so not a breaking change. | Add it. |
| **F** | **Account fit / ICP deferred to M6** and recorded there rather than left homeless again. | Defer. |

Implementation begins once **A–F** are settled. Nothing is coded before then.

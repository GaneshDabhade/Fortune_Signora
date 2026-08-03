# 23 — Observation Engine

> Status: **IMPLEMENTED** — M3B, 2026-07-29
> Audience: All engineers, EMs, and technical stakeholders at Signora
> Revision: **v2** — the design as built. All four review questions were answered before implementation; the outcomes and two departures are recorded in *[As built](#as-built-decisions-taken-and-what-changed)*.
>
> Prerequisite reading: [21-intelligence-pipeline.md](21-intelligence-pipeline.md), [22-knowledge-graph.md](22-knowledge-graph.md), and the claim vocabulary in `modules/provider_normalization/domain/vocabulary.py`.

---

## The transition this module represents

M2.2 established the unit of evidence. M3A established identity: the pipeline now knows *who* a provider is talking about.

**M3B is where time becomes first-class.** A claim is a point. An observation is a *difference between points*, attributed to the source that reported it. Everything downstream — business events, signals, buying scores — reasons about movement, and none of it is expressible until movement is.

This is also the first module whose main job is **subtraction**. In a polling pipeline the overwhelming majority of claims re-assert what was already known: a nightly Apollo sync reports the same headcount for weeks. Deciding what is *not* an observation is most of the work, and getting it wrong in either direction is expensive — too permissive floods every downstream stage with noise, too aggressive silently discards the movement the product exists to detect.

---

## The central question

> **What constitutes a meaningful observation?**

Two candidate meanings of "meaningful", and the distinction matters more than anything else in this document:

**Meaning A — *something actually changed*.** A structural test. Did the provider assert something different from what it last asserted? Answerable from the claim series alone, with no judgement.

**Meaning B — *something worth caring about*.** A materiality test. Is a headcount move of 120 → 121 worth anyone's attention?

**This proposal recommends the Observation Engine implement Meaning A, and only Meaning A.**

Meaning B requires a threshold, and a threshold here would be exactly the hidden heuristic this platform has consistently refused: a magic number nobody can justify that four modules trust within a year. Worse, materiality is not a property of the change — it is a property of the change *in a commercial context*. A headcount move of 5 is noise at Acme and a signal at a 12-person startup. The Business Event Engine (M4) owns a **curated, versioned, reviewable taxonomy**; that is where a materiality rule can be stated, argued about, and changed without a migration.

What the Observation Engine contributes to materiality is the **structural inputs that make it expressible**: magnitude, direction, elapsed duration, and which provider said so. It computes those and stops.

### On "what changed, and why does that matter?"

Taking the framing seriously: the Observation Engine should answer **"what changed, and according to whom"**. The *"why does that matter"* half belongs to M4, and the split is deliberate rather than pedantic.

If this module answered both, the materiality rule would live in derivation code — unversioned, untestable against a taxonomy, and invisible in the evidence chain. A seller asking *"why was I told about this?"* would get an answer that bottoms out in a constant. Keeping the two apart is what lets M4 say *"this is a **hiring surge** because headcount grew 21% in 8 weeks, which exceeds the taxonomy's threshold for this segment"* — a sentence with a reviewable rule in the middle of it.

**The one-line rule this module implements:**

> **A meaningful observation is a change in what a provider asserts, or the first sighting of an occurrence it asserts. Re-assertion is never an observation. Disagreement is never an observation.**

---

## The distinction the vocabulary already contains

The canonical vocabulary holds two kinds of claim, and the module's whole shape follows from noticing it.

| | Attributes | What a claim asserts | What an observation is |
|---|---|---|---|
| **State** | `EMPLOYEE_COUNT`, `REVENUE_BAND`, `INDUSTRY`, `FOUNDED_YEAR`, `COUNTRY`, `LEGAL_NAME`, `OPEN_ROLES` | *This is currently true.* | A **transition** — value moved from X to Y between t₁ and t₂ |
| **Occurrence** | `FUNDING_ROUND`, `ACQUISITION`, `TECHNOLOGY_DETECTED`, `TECHNOLOGY_REMOVED`, `ROLE_CHANGE`, `HEADCOUNT_CHANGE`, `INTENT_TOPIC_SURGE` | *This happened.* | A **first sighting** — the occurrence, deduplicated across re-syncs |

`HEADCOUNT_CHANGE` is instructive: CoreSignal reports a *delta* directly. It is already an assertion that something happened, and deriving a transition from it would double-count against `EMPLOYEE_COUNT`.

`INTENT_TOPIC_SURGE` is one claim per observed week. Each week is a distinct occurrence, keyed on `(topic, observed_week)` — so a re-report of week 3 in week 5 deduplicates, and the weekly series survives intact as a series of observations. The *trajectory* is then readable downstream without this module inventing a trend rule.

**Classification is declared, never inferred**, in one table in the domain — the same discipline as `TENANT_OWNED_TABLES`. Adding a canonical attribute already requires an RFC; classifying it is part of that RFC, and an unclassified attribute fails the build rather than defaulting to a behaviour nobody chose.

---

## The four candidate architectures

### A — Cross-provider observations

One series per `(entity, attribute)`, all providers merged by `observed_at`.

**Rejected.** It manufactures change that never happened. Apollo reports 120 on Monday; CoreSignal reports 145 on Tuesday; the merged series says *"grew 25 in one day"*. Nothing grew — the sources disagree.

Avoiding that requires deciding which provider is authoritative, which is **truth resolution** — forbidden by the invariant M3A ratified, and forbidden here for the same reason: no module at this depth has the context to justify the choice.

This is the single most important rejection in the document. It is also the most tempting design, because a cross-provider series is what a person intuitively means by "Acme's headcount over time".

### B — Per-provider observations, attributed to the entity — **recommended**

One series per `(entity, provider, attribute)`. An observation reads:

> *According to CoreSignal, Acme's `EMPLOYEE_COUNT` went from 120 to 145 between 15 Jan and 1 Mar.*

Change is computed **within** one provider's series, so disagreement can never masquerade as movement. The entity attribution comes from the Knowledge Graph, so every observation is about a resolved identity.

Corroboration — two providers independently reporting growth — is *stronger evidence*, and weighing it is interpretation. It belongs to the Signal Engine, which receives both observations and can say so explicitly.

### C — B, plus a derived cross-provider "consensus observation"

**Rejected for M3B**, and worth stating why precisely: it is Option D from M3A arriving one layer up. It puts a collapsed value in the schema before any module has asked for one, and a stored consensus becomes the de facto truth — within a year consumers read the consensus and nobody reads the per-provider series.

If M4 or M5A demonstrates it needs corroboration as a first-class artifact, **that** is the evidence, and by then the rule it should use will be knowable. Building it now means inventing the rule with no consumer to validate it.

### D — Observations as a read-time projection, not stored

Derive on read from the claim series; store nothing.

**Rejected.** Two modules need to *react* to an observation — the Business Event Engine consumes it, Timeline renders it — and an event cannot be published from a projection nobody computed. It also discards `recorded_at`: the record of *when Signora learned something*, which is distinct from when it was true and is what makes a backfill distinguishable from a burst of real activity.

---

## Domain model

Two concepts. Deliberately fewer than M3A, because this module derives rather than decides.

### `Observation`

```
Observation(id, workspace_id, entity_id, provider, attribute, kind,
            from_value, to_value, magnitude, direction,
            observed_at, previous_observed_at, recorded_at,
            evidence_claim_ids, supersedes)
```

| Field | Why it exists |
|---|---|
| `provider` | An observation is always *according to someone*. Dropping this is how disagreement becomes phantom change. |
| `kind` | `VALUE_CHANGED` or `OCCURRENCE_OBSERVED`. |
| `from_value` / `to_value` | `from_value` is null for an occurrence. Both stored as the claim's JSON form. |
| `magnitude` / `direction` | Structural inputs to materiality, computed only where the vocabulary types make them meaningful (numeric attributes). **Not a score** — magnitude is the arithmetic delta, nothing more. |
| `observed_at` / `previous_observed_at` | When the provider says these were true. Their difference is the window the change occurred within — never narrower than the evidence supports. |
| `recorded_at` | When Signora learned it. The gap from `observed_at` is **reporting lag**, and it is real: Bombora reports week 3 in week 5. Collapsing the two makes a backfill look like a burst of activity. |
| `evidence_claim_ids` | One claim for an occurrence, two for a transition. The link that makes the chain traceable. |
| `supersedes` | Backward pointer, for the same reason as `ResolutionDecision` — see below. |

**No confidence, no score, no importance.** For the same reason `Claim` has none and `MatchStrength` is not a number.

### `AttributeSemantics`

The declared classification — state or occurrence — plus, for occurrence attributes, the **occurrence key**: the part of a value that identifies *which* occurrence it is.

| Attribute | Occurrence key |
|---|---|
| `FUNDING_ROUND` | `round_type` + `announced_on` |
| `ACQUISITION` | `counterparty` + `announced_on` |
| `TECHNOLOGY_DETECTED` / `TECHNOLOGY_REMOVED` | normalized technology name |
| `ROLE_CHANGE` | `title` + `direction` + `observed_at` |
| `HEADCOUNT_CHANGE` | `observed_at` + delta |
| `INTENT_TOPIC_SURGE` | `topic` + `observed_week` |

This is vocabulary knowledge and lives in **one function**, on the same reasoning as `normalize_domain`: when authentic payloads replace fixtures these keys will need revisiting, and that revision should be a single edit rather than a hunt.

---

## Observation identity — deterministic, not allocated

An observation's id is **derived from what it observes**, not allocated:

```
id = uuid5(OBSERVATION_NAMESPACE,
           workspace_id | entity_id | provider | attribute | kind | key)

key (transition) = canonical(from_value, previous_observed_at, to_value, observed_at)
key (occurrence) = occurrence_key(attribute, value)
```

This makes deduplication a **database property** rather than a code path: `INSERT … ON CONFLICT DO NOTHING` on the primary key, and re-processing the same evidence is a no-op no matter how many times an event is redelivered or a series re-derived.

**Deliberately keyed on values and times rather than on claim ids.** Claim ids are allocated at mapping time, so regenerating claims after a mapper fix would mint new ids — and a claim-keyed observation id would duplicate every observation in the workspace. Keying on the observed facts survives regeneration, which is the rollback path the whole pipeline depends on.

This is the same philosophy the Match Strength invariant follows: **where practical, enforce structurally.** Idempotency guarded by a code path is idempotency until someone adds a second write site.

---

## Derivation — a pure function of a claim series

Given the ordered claim series for one `(entity, provider, attribute)`, derivation is total and deterministic:

**State attributes.** Walk the series in `observed_at` order. The **first claim establishes a baseline and produces no observation.** Each subsequent claim whose value differs from the previous one produces a `VALUE_CHANGED`. Each claim whose value is unchanged produces nothing.

**Occurrence attributes.** Each distinct occurrence key produces one `OCCURRENCE_OBSERVED`, at the earliest `observed_at` it was asserted. Re-assertions produce nothing.

### Why the first value produces no observation

This is the sharpest application of *"not every change should become an observation"*, and it is worth being explicit because it is a real trade-off.

Onboarding a workspace with 5,000 companies means roughly 30,000 first-value claims. Emitting an observation for each would flood Timeline and the Business Event Engine on day one with a message that says only *"Signora has started tracking this"* — which `entity.created` already says, once, per company.

The counter-argument is genuine: *"we now know Acme is in manufacturing"* is a change in **knowledge**, even though nothing changed in the world. The proposal's position is that the claim already records it, the entity's creation already announces it, and 30,000 observations asserting no movement would degrade every consumer's signal-to-noise for the life of the workspace.

> **Flagged for decision.** If the preference is to record first values, the cleanest form is a distinct `VALUE_ESTABLISHED` kind that downstream can filter — not a `VALUE_CHANGED` with a null `from_value`, which would silently inflate every "things are changing" metric.

---

## Late arrival — refine, never rewrite

Claims arrive out of order routinely. Bombora reports week 3 in week 5; a backfill re-delivers a quarter of history at once.

Consider a series that arrives t₁ = 120, t₃ = 145, producing **O₁: 120 → 145 over t₁…t₃**. A later claim lands at t₂ = 130.

O₁ is not *false* — headcount did go 120 → 145 across that window. It is **less precise** than the evidence now supports, and leaving it alongside the two finer observations would double-count the growth.

**Recommendation: append-only supersession.** Re-derive the series; emit **O₂: 120 → 130** and **O₃: 130 → 145**, each carrying `supersedes = O₁`. O₁ remains readable as what was believed then.

The pointer points **backwards**, exactly as `ResolutionDecision.supersedes` does, and for the same forced reason: a forward pointer would have to be written onto the older row, which requires the `UPDATE` grant an immutable table withholds. `observation` joins `IMMUTABLE_TENANT_TABLES`.

This makes a correction *visible* rather than silent. Downstream sees a refinement it can react to — a Timeline entry can say *"this was later refined"* — instead of a value quietly changing underneath it.

**Cost.** Re-deriving one `(entity, provider, attribute)` series on each new claim. A series is tens of claims, not millions, and it is bounded by construction. This is the cheapest correct option, and correctness here is not negotiable: an observation engine that gets late arrival wrong produces phantom growth, which produces phantom signals, which produces recommendations nobody can defend.

---

## Replay

Because derivation is a pure function of an immutable, complete claim series with deterministic identity, the entire `observation` table can be **dropped and rebuilt byte-identically**. That is the rollback for a bad derivation rule, and the reason claims are stored rather than streamed.

Proposed as an acceptance criterion asserted by test — a rebuild that does not reproduce the same rows means derivation has acquired a hidden dependency on processing order or wall-clock time.

---

## Triggering — and one dependency question that needs a decision

The Observation Engine must run whenever **new evidence lands for a resolved entity**. That trigger does not currently exist, and the reason is a deliberate M3A decision:

> M3A writes no resolution decision and publishes no event when re-resolution reaches the same answer. A nightly Apollo re-sync therefore produces new claims and **no graph event** — so an Observation Engine subscribed to `entity.identity_bound` would never see the claims it exists to read.

Two ways to close it.

### Option 1 — Knowledge Graph publishes `entity.evidence_attached` · **recommended**

```
entity.evidence_attached { entity_id, provider, provider_external_id,
                           raw_record_id, claim_ids }
```

Published by the Knowledge Graph on **every** `claim.recorded` it processes, including those that change no identity.

- Preserves the ratified dependency graph exactly: **Knowledge Graph → Observation Engine**, no new edge.
- It is a genuine graph responsibility. Attributing evidence to identity is what the module does; an event announcing the attribution is the natural output of it.
- The Observation Engine can never see a claim that is not attributable to an entity, which makes *"every observation traces to an entity"* structural rather than aspirational.

**Cost:** it adds an event to a module whose milestone is closed. Under §20d that is a finding to raise rather than a licence to build, which is why it appears here rather than in the implementation.

### Option 2 — Observation Engine subscribes to `claim.recorded` directly

Adds a **Provider Normalization → Observation Engine** edge to the dependency graph, and requires the Observation Engine to resolve subject → entity itself on every claim. It also permits observations about unresolved subjects, which the recommendation deliberately forbids.

**A dependency-graph change requires an RFC** ([05-module-dependencies.md](05-module-dependencies.md)).

### The vocabulary dependency — also needs a decision

The Observation Engine must reason in canonical attributes. Those types live in `provider_normalization/public`, and the Knowledge Graph already imports them — a `ClaimSet` is made of `ClaimView`s.

The alternative is each downstream module defining its own copy of the vocabulary, which §4 explicitly forbids: *never introduce a second definition of a concept a module already owns*.

> **Proposed:** recognise `provider_normalization/public` — the canonical vocabulary and claim views — as a **shared contract every downstream pipeline module may depend on**, documented as such in [05-module-dependencies.md](05-module-dependencies.md). It is a *vocabulary* dependency, not a data-access one: reading claim **data** still goes through the Knowledge Graph's `GraphQueries`.
>
> This is already true in practice as of M3A. Recording it makes it a reviewed decision rather than a precedent nobody voted on.

---

## Relationships are not observed here

The Knowledge Graph derives `USES_TECHNOLOGY` edges from technographic claims and publishes `relationship.established` / `relationship.ended`.

**The Observation Engine deliberately does not consume those.** They are the graph's structural view of the *same* `TECHNOLOGY_DETECTED` / `TECHNOLOGY_REMOVED` claims that produce occurrence observations here. Observing both would double-count every technology migration — the exact scenario the product is most interested in detecting.

One rule, stated once: **observations are derived from claims, never from another module's derivation of claims.**

---

## Storage

One workspace-owned table, `observation`, with forced RLS and its full policy set in the migration that creates it, registered in `tenancy_policy.py`, and added to `IMMUTABLE_TENANT_TABLES` — no `UPDATE` grant.

Indexes: `(workspace_id, entity_id, attribute, observed_at)` for the entity view; `(workspace_id, observed_at)` for Timeline; `supersedes` for refinement lookups.

**On scale.** Observations are far fewer than claims — one per *change*, where claims are one per *assertion*. In a polling pipeline that ratio is the module's whole value proposition, and it is worth measuring in production: an observation-to-claim ratio approaching 1 means the change detection has stopped detecting anything.

---

## Event model

| Event | When | Payload |
|---|---|---|
| `observation.recorded` | A change or first sighting was derived | `observation_id`, `entity_id`, `provider`, `attribute`, `kind`, `direction`, `observed_at` |
| `observation.superseded` | A late-arriving claim refined an earlier observation | `observation_id`, `supersedes`, `entity_id`, `attribute` |

Following the established rule — **events carry identity, ports carry payload** — neither event carries `from_value`/`to_value`. A consumer reads them through the module's read port, so a vocabulary addition is never an event-contract change.

`observation.superseded` is a first-class event rather than a log line: a consumer that acted on the coarser observation needs to know it was refined.

---

## Module API

```
observations(workspace_id, entity_id, attribute=None, since=None) -> list[Observation]
observation_evidence(workspace_id, observation_id)               -> ObservationEvidence
series(workspace_id, entity_id, provider, attribute)             -> list[Observation]
```

`observation_evidence` returns the observation together with the claims behind it — the traversal an evidence export and an AI citation both need.

**Deliberately absent: any method returning a current value, a consensus, or a trend.** All three are interpretation. The Signal Engine reads the series and forms its own.

---

## Relationship with the modules downstream

**Business Event Engine (M4).** Consumes `observation.recorded`. Applies its curated taxonomy to decide that *"headcount +21% over 8 weeks, corroborated by two providers"* is a **hiring surge**. It receives magnitude, direction, duration, and provider attribution and needs nothing else from here. **The materiality threshold lives there, versioned and reviewable.**

**Timeline (M7).** Consumes `observation.recorded` for the account narrative, ordered by `observed_at` — not `recorded_at`, or a backfill would render as a wall of activity on the day it was ingested. `observation.superseded` lets the narrative show a refinement rather than silently changing what it said yesterday.

**AI Reasoning (M9).** Observations are its primary structured input, and the shape here is chosen with that in mind. Because every observation names its provider, reasoning can say *"CoreSignal shows 21% growth; Apollo has not reported since January"* — a sentence that is impossible if observations are cross-provider. Because every observation cites its claims, a citation is **verifiable** rather than plausible.

The rule this places on every later module: **never aggregate observations in a way that loses provider attribution.** That attribution is what lets the product say *"sources disagree"*, which is one of the six questions customers are buying answers to.

---

## Definition of Done — M3B

- [x] Demonstration passes; AC-30 through AC-34, AC-6, AC-1, AC-13 all satisfied
- [x] Migration 0010 with forced RLS and full policies in the same revision; `observation` registered in `tenancy_policy.py` and in `IMMUTABLE_TENANT_TABLES`
- [x] Security Invariants extended 99 → 124, each addition **proven to fail** when its guarantee is removed
- [x] `04-modules.md`, `05-module-dependencies.md`, `06-events.md`, and `21-intelligence-pipeline.md` updated in the same change
- [x] `make smoke` extended with stage 14d, change detection
- [x] PROJECT_STATUS and SESSION_HANDOFF updated at the boundary

The two platform findings raised in M3A remain open and are **not** worked around here: `EventHandler` receives no session, and `PublishableEvent` cannot be satisfied by a frozen dataclass. Both are queued as RFCs for the platform milestone.

---

## Task breakdown — T67–T74 · ~8–11 ew

| ID | Task | Complexity | Depends on |
|---|---|---|---|
| **T67** | Domain: `Observation`, `ObservationKind`, `AttributeSemantics`, occurrence keys, deterministic identity | M · 1.5 ew | — |
| **T68** | Schema + migration 0010 — `observation`, forced RLS, immutable, registered | S · 1 ew | T67 |
| **T69** | Derivation engine — pure series → observations, including refinement on late arrival | L · 2.5 ew | T67 |
| **T70** | `RecordObservations` use case + repository, idempotent on deterministic id | M · 1.5 ew | T68, T69 |
| **T71** | `entity.evidence_attached` (Knowledge Graph) + subscription — **subject to approval** | S · 1 ew | T70 |
| **T72** | Read port + module `public/` API | S · 1 ew | T70 |
| **T73** | Event contracts: `observation.recorded`, `observation.superseded` | S · 0.5 ew | T70 |
| **T74** | Demonstration + smoke stage + Security Invariants | M · 1 ew | all |

**Order:** T67 → T68 → T69 → T70 → T72 → T73 → T71 → T74

T71 late, because it is the one task touching another module and should land only once everything it feeds is proven.

**Dependencies.** Inbound: M3A (entities, claim sets), M2.2 (vocabulary), M1.1 (event bus). Outbound: blocks M4 and everything after. External: none.

---

## Acceptance criteria

| ID | Criterion |
|---|---|
| **AC-30** | **Re-assertion is never an observation** — a provider repeating the same value produces nothing, asserted by re-running a sync |
| **AC-31** | **Disagreement is never change** — two providers reporting different values for the same attribute produce no transition between them |
| **AC-32** | **Unbroken provenance** — every observation cites ≥1 claim, and traverses to entity, resolution decision, and raw record. Zero orphans, asserted by join |
| **AC-33** | **Deterministic and replayable** — dropping and rebuilding the table from claims reproduces it identically |
| **AC-34** | **Late arrival refines, never rewrites** — a claim arriving out of order supersedes rather than mutates; the coarser observation stays readable |
| **AC-6** | Tenancy — new table, forced RLS, full policies, registered in the policy |
| **AC-1** | Event contract — cataloged, idempotent, correlation-traced |
| **AC-13** | Security Invariants extended, each proven to fail when its guarantee is removed |

---

## Demonstration scenario

> *"The pipeline notices what moved, and never invents movement."*
>
> Run the baseline scenario, then run it **again** unchanged. The second pass produces **zero observations** — every claim re-asserted what was already known. This is the assertion that matters most; a change-detection engine that fires on a no-op sync is worse than no change detection.
>
> Advance the scenario: CoreSignal reports Acme's headcount rising. One `VALUE_CHANGED` is recorded, naming CoreSignal, with magnitude, direction, and the window it occurred within.
>
> Apollo continues to report a *different* absolute headcount throughout. **No observation is produced from the difference between them** — that is disagreement, and both claims remain individually retrievable.
>
> BuiltWith reports the legacy ERP retired. One `OCCURRENCE_OBSERVED`. Re-syncing BuiltWith five more times produces no further observations.
>
> Deliver a claim out of order, between two already observed. The coarse observation is superseded by two finer ones; all three remain readable, and the growth is not double-counted.
>
> Finally, truncate `observation` and rebuild from claims: an identical table.

---

## Deferred, with reasons

| Deferred | Why |
|---|---|
| **Materiality thresholds** | A judgement requiring commercial context. Belongs in M4's curated taxonomy, where it is versioned and reviewable — not in derivation code, where it would be a constant nobody can justify. |
| **Cross-provider consensus observations** | No consumer has asked. If M4 or M5A demonstrates it needs one, that is the evidence — and the rule will be knowable by then. |
| **Trend and velocity derivation** | Interpretation over a series. The Signal Engine has the context; a trend computed here would be a hidden model. |
| **Relationship observations** | Would double-count technographic claims already observed as occurrences. |
| **Person-level observations** | No person identity exists to attach them to (deferred in M3A for the same reason). |
| **Observation retention / archival** | A volume decision requiring production evidence, per [12-scalability.md](12-scalability.md)'s trigger discipline. |

---

## Rollback strategy

**Schema:** additive — one new table; downgrade drops it. **Data:** entirely derived. Drop and rebuild from claims — the rollback for a bad derivation rule, and the reason AC-33 exists. **Application:** previous image tag. **Blast radius:** one workspace; a bad rule produces wrong observations there only.

---

## Operational readiness

- [ ] Metric: **observation-to-claim ratio** — the leading indicator. Approaching 1 means change detection has stopped detecting; approaching 0 means it has stopped firing.
- [ ] Metric: supersession rate — a rising rate means providers are delivering out of order more often, which is an ingestion story as much as an observation one.
- [ ] Metric: reporting lag distribution (`recorded_at` − `observed_at`) per provider.
- [ ] Alert: observation volume spike — the signature of a derivation rule that has started firing on re-assertion.
- [ ] Runbook: rebuilding observations from claims; investigating a suspected phantom change.
- [ ] `correlation_id` traceable from raw record through claim, decision, entity, and observation.

---

## Risks and mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| **Phantom change from cross-provider comparison** | 🔴 High | Structurally impossible in the recommended design — series are per-provider. Asserted by AC-31. |
| **Initial-load observation flood** | 🟠 Medium | First value establishes a baseline and produces no observation. Flagged for decision, since it is a real trade-off. |
| **Late arrival double-counts growth** | 🟠 Medium | Series re-derivation with append-only supersession (AC-34). The cheapest correct option; correctness is not negotiable here. |
| **Occurrence keys are wrong for authentic payloads** | 🟠 Medium | Fixture-derived keys will need revisiting. Centralised in one function so the revision is a single edit. |
| **The engine quietly becomes a materiality filter** | 🟡 Low | No threshold exists in the module. A constant appearing in derivation is a review failure; AC-30/AC-31 are structural, not numeric. |
| **`entity.evidence_attached` volume** | 🟡 Low | One event per raw record — the same order as `claim.recorded`, which the bus already carries. |

---

## As built: decisions taken, and what changed

### The four review questions, answered

| Question | Outcome |
|---|---|
| **Is Meaning A the right scope?** | **Approved, and elevated to a permanent architectural principle**: *claims preserve evidence · the Knowledge Graph resolves identity · the Observation Engine detects change · the Business Event Engine determines business meaning · the Signal Engine determines commercial meaning.* Recorded in [21-intelligence-pipeline.md](21-intelligence-pipeline.md). |
| **Should the first value produce an observation?** | **No.** The first assertion establishes knowledge; it does not represent change. If "knowledge established" is ever needed it becomes a separate domain concept rather than an expansion of this module. |
| **`entity.evidence_attached` in the Knowledge Graph?** | **Approved.** The Knowledge Graph remains the Observation Engine's only upstream dependency; the alternative Provider Normalization → Observation Engine edge was explicitly rejected. |
| **Recognise the canonical vocabulary as a shared contract?** | **Approved** and documented as a platform-wide architectural contract in [05-module-dependencies.md](05-module-dependencies.md). |

### The observation model, refined

Every observation explicitly carries **previous value, current value, direction, magnitude, provider, observation timestamp, and originating entity** — so downstream reasons directly over observations rather than reconstructing transitions from claim history, which would mean every consumer reimplementing this module and diverging from it.

Two shapes were evaluated against that requirement, and the one built is deliberately not uniform:

- **`previous_value` is null exactly when the observation is an occurrence**, and that absence is meaningful rather than missing — there is genuinely nothing a funding round moved *from*. Forcing a placeholder would be a value nobody observed. The database enforces the pairing (`ck_observation_shape_matches_kind`), so no write path can produce a half-formed observation.
- **`magnitude` exists only for counts.** Subtracting two industries is meaningless, and inventing a distance between them would be exactly the manufactured number this platform refuses. `direction` is always present: `INCREASED`/`DECREASED` where the vocabulary orders the values, `CHANGED` where it does not, `OCCURRED` for an occurrence.

Revenue bands get a direction because the vocabulary orders them **by definition** — `under_1m` to `over_1b` — which is a structural reading rather than a heuristic. A test asserts that order explicitly, so reordering the enum fails the build instead of silently inverting every revenue direction in the platform.

### Two departures from the proposal

**1. Occurrence keys are read from a single function, and one of them surprised the design.** `TECHNOLOGY_DETECTED` is keyed on the technology name *alone*, not on the detection window: a vendor re-reporting the same technology with a later `last_detected` is the same detection, not a new one. Keying on the window would have produced a new observation on every sync — the exact re-assertion flood the module exists to prevent.

**2. `previous_value` needed `none_as_null=True`.** Without it SQLAlchemy writes JSON `null` into a JSONB column rather than SQL `NULL`, and the constraint distinguishing an occurrence from a change never sees the absence it tests for. Found by the constraint rejecting a legitimate write, which is the constraint doing its job.

### What the baseline scenario can and cannot demonstrate

The scenario reports each subject once per provider, so it contains **occurrences but no movement**. Every negative assertion is therefore exercised by the real pipeline — first sync observes nothing, a repeated sync observes nothing new — while the positive case (a second, differing assertion by the same provider produces exactly one transition) is constructed explicitly in the demonstration.

That split is recorded rather than papered over: a scenario with genuine multi-week movement is **scheduled M2.0 work**, alongside the fixture enrichment M3A identified. Both are simulation artifacts, and editing them mid-milestone would blur what these demonstrations prove.

---

## A5 — the module's first HTTP surface *(2026-08-03)*

`GET /workspaces/{id}/accounts/{account_id}/observations?attribute=` — every recorded change to one account, with what it moved from, what it moved to, who observed it, and the window it happened in.

**Nothing new was computed.** `Observation` has carried `previous_value`, `current_value`, `direction`, `magnitude`, `observed_at`, `previous_observed_at`, `recorded_at` and `provider` since M4, and `ObservationQueries.observations()` has read them since. **The module simply had no interface layer** — thirteen fields of intelligence with no path to a customer.

### The response is bounded by this module's own refusals

The wire shape carries **no `significance`, `score`, `importance` or `summary`**, matching `public/`'s stated contract exactly: *whether a move matters is the Business Event Engine's question.* A field here would be filled in by whoever rendered it, which is the judgement this module exists not to make. Asserted at both the schema and the HTTP layer.

### `provider` on every row is a correctness constraint, not provenance decoration

> **A reading is only ever a change according to one source.** Apollo saying 120 on Monday and CoreSignal saying 145 on Tuesday is **disagreement, not growth of 25** — the phantom change this module was built to avoid, and `series()` is per-provider by construction for the same reason.

**A client that joins these into one line per attribute draws exactly that phantom.** The endpoint's docstring says *group by provider before plotting*, and the schema says why beside the field. **Any chart built on this must have one series per provider**, or show one provider at a time.

### `previous_observed_at` bounds an interval, and a point would be a lie

The change happened *somewhere between* it and `observed_at`, never more precisely. A visualisation drawing a single dated point claims a precision the evidence does not have — and the field exists specifically so it does not have to.

### The response model is `AccountObservationResponse`, and the name is not cosmetic

`ObservationResponse` was already taken by the Business Event Engine's evidence drawer. **Two response models sharing a class name share an OpenAPI component name**: FastAPI qualifies both, the original key disappears, and a shipped client contract is renamed by a change in an unrelated module. **The newer name moved, because the older one is already a contract.** [B-320](../BUGS.md) records that nothing in the repository checks for this — it was caught by a test that happened to name the schema it cared about.

### Not paged, deliberately

An account watched for a year has tens of changes, not thousands, and `attribute` narrows further. **If a real workspace makes this large, that measurement is the trigger** ([12-scalability.md](12-scalability.md)) rather than a guess made now.

### The limitation that matters for the screen

**The Playground produces no transitions** — [B-319](../BUGS.md). A transition needs one provider asserting a state attribute twice and the scenario enriches each account once, so every observation a demonstration can show is a first sighting. **The endpoint is correct and its screen would be empty.** Pinned by a test that fails the day the simulator changes.

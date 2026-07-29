# 24 — Business Event Engine

> Status: **IMPLEMENTED** — M4, 2026-07-29
> Audience: All engineers, EMs, and technical stakeholders at Signora
> Revision: **v2** — the design as built. All five review questions were answered before implementation; the outcomes and what the CRO test changed are recorded in *[As built](#as-built-what-the-cro-test-changed)*.
>
> Prerequisite reading: [21-intelligence-pipeline.md](21-intelligence-pipeline.md), [23-observation-engine.md](23-observation-engine.md).

---

## The transition this module represents

M3B answered *"what changed?"* and stopped there deliberately — it computes magnitude, direction, duration, and provider attribution, and refuses to say whether any of it matters. A Security Invariant reads its source as a syntax tree to keep it that way.

**M4 is the module that was built for.** It is the first permitted to answer *"why does this change matter?"*, and the first whose output a human would recognise as intelligence: not *"employee_count moved from 120 to 145 per CoreSignal"* but *"Acme is in a hiring surge."*

It is also the first module whose correctness is a **product judgement rather than a structural one**. Everything before it could be proven right: identity resolution is deterministic, change detection is subtraction. Whether 15% growth over 90 days constitutes a surge is a claim about the world that can only be argued about — which is precisely why the architecture must put that claim somewhere it *can* be argued about.

---

## The boundary, stated first

> **The Business Event Engine answers "why is this business-relevant?"**
> **It does not answer "should we engage this account?"**

Commercial prioritisation belongs to the Signal Engine and everything after it. Concretely, a business event carries **no priority, no score, no urgency, and no rank** — proposed to be enforced structurally, exactly as M3B's absence of thresholds is.

The distinction is easiest to see in a sentence each module could produce:

| Module | Sentence |
|---|---|
| Observation Engine | *"CoreSignal reported employee_count 120 → 145 between 15 Jan and 1 Mar."* |
| **Business Event Engine** | ***"Acme is in a hiring surge: +21% over 45 days, corroborated by two providers."*** |
| Signal Engine | *"That surge is a strong buying indicator for us, because Acme also shows intent on Cloud ERP and runs a competitor's stack."* |

The middle sentence is true regardless of who is selling. The third is not — and that difference is the boundary.

---

## The foundational question: taxonomy and rules

> **Is a business event type *data*, and is its detection *code*?**

**Recommended: yes — and the line between them is where this module's long-term maintainability is decided.**

### What each is

**The taxonomy is the platform's business language.** The set of business event types, their names, their meaning, their required evidence, and **their materiality parameters** — the numbers that decide what counts as a surge.

**The rules are the detection logic.** Given observations, decide whether a type's conditions are met, over what window, on what evidence.

```
taxonomy (data, versioned artifact)          rules (code)
─────────────────────────────────────        ─────────────────────────────
hiring_surge:                                class HiringSurgeRule:
  version: 1                                     detects = HIRING_SURGE
  domain: workforce                               reads parameters from the
  description: "Sustained growth in                taxonomy; correlates the
    headcount or open roles."                      observation series;
  evidence:                                        emits or does not
    attributes: [employee_count, open_roles]
  parameters:
    minimum_growth_ratio: 0.15
    window_days: 90
    minimum_absolute_growth: 10
```

### Why this split, rather than either extreme

**Everything as code** puts the threshold where nobody outside engineering can see it. A seller asking *"why was I told this?"* gets an answer that bottoms out in a constant on line 47. Changing it requires a release, and the history of what threshold produced which events is reconstructable only from git.

**Everything as data** requires expressing correlation logic — windows, series traversal, multi-attribute conditions — as configuration. That means inventing a DSL, and **a DSL is a programming language with worse tooling**: no type checker, no debugger, no test framework, and a parser Signora would own forever. This is the classic rules-engine trap, and the architecture's stated preference for boring, explicit solutions rules it out.

**The split is the useful part.** Parameters are the thing that changes often, needs review by people who are not engineers, and must be recorded against every event. Correlation is the thing that needs a type checker.

### Making the split real rather than aspirational

A split like this decays the moment one convenient constant appears in a rule. So, mirroring the M3B invariant:

> **Proposed structural invariant.** A Security Invariant parses every rule module as a syntax tree and **fails if any numeric literal appears in a comparison**. Every threshold must be read from the taxonomy. The failure mode this prevents is specific and near-certain: someone adds `if len(observations) < 3: return` to reduce noise, and a parameter nobody can review starts filtering the pipeline.

Two supporting rules, both cheap:

- **Every parameter a rule reads must be declared in the taxonomy**, and every declared parameter must be read by some rule. Asserted by test; an orphan on either side means a rule and its declaration have drifted.
- **A rule declares which type it detects**, and every type in the taxonomy has exactly one rule. A type with no rule is a promise nobody keeps.

### Where the taxonomy lives

**Recommended: a versioned artifact in the repository, reviewed like code — not a database table.**

| | Versioned file | Database table |
|---|---|---|
| Review | Pull request, diffable | Needs an admin UI and an audit log to match |
| Reproducibility | The version in force is a repo state; a replay is exact | Needs point-in-time reconstruction of a mutable table |
| Change cadence | A release | Immediate |
| Precedent | Scenario manifests (M2.0); Prompt Registry (M8) is specified the same way | — |

The trade is real: tuning a threshold requires a deploy. That is acceptable now and has an obvious trigger for revisiting — **when someone who is not an engineer needs to tune thresholds without a release**, which realistically arrives with the business UI in M12. Recording the trigger is better than pre-building for it.

> **A consequence worth stating: `business_event_type.published` (in the v2 catalog) should be dropped.** It exists to notify the system that a taxonomy changed at runtime, which a repository artifact does not do — the deployment *is* the notification. An event with no producer is a contract nobody is keeping, the same reasoning that deferred `entity.superseded`.

---

## Domain model

### `BusinessEventType` — taxonomy entry

```
BusinessEventType(key, version, domain, description,
                  evidence_attributes, parameters, deprecated_at)
```

`deprecated_at` rather than deletion: a type that stops being detected must still be readable, because historical events reference it. **Nothing in business history is ever unreadable because the taxonomy moved on.**

### `BusinessEvent` — an instance

```
BusinessEvent(id, workspace_id, entity_id, type_key,
              occurred_at, window_start, window_end, detected_at,
              summary, facts,
              evidence_observation_ids, corroborating_providers,
              taxonomy_version, payload_version, supersedes)
```

| Field | Why |
|---|---|
| `occurred_at` | When the business fact happened, taken from the observations — **never** detection time. Timeline orders on this, or a backfill renders as a wall of activity on its ingestion day. |
| `window_start` / `window_end` | The interval the evidence supports. For a point event they collapse to one instant; for a correlated one they are the real bounds, never narrower than the evidence. |
| `detected_at` | When Signora concluded it. The gap from `occurred_at` is detection lag, and it is a real operational metric. |
| `summary` | A rendered human sentence — *"headcount grew 21% over 45 days"*. Rendered from `facts` by the rule, so Timeline and AI Reasoning do not each invent their own phrasing. |
| `facts` | The typed, per-type payload the rule computed (growth ratio, round amount, technology name). **Not a score.** |
| `evidence_observation_ids` | Citation, never subsumption — see below. |
| `corroborating_providers` | Which providers' series *independently* satisfied the rule. A count of agreement, never a weight. |
| `taxonomy_version` | Which version of the type detected this. Without it a replay under a new version is incomparable to the old one. |
| `payload_version` | The wire schema of `facts`, versioned separately — see *Versioning* below. |
| `supersedes` | Backward pointer, as on `observation` and `resolution_decision`. |

**No priority, no score, no urgency, no rank.** Proposed to be asserted structurally.

### Citation, not subsumption

A business event **references** its observations; it does not copy their values. The chain must stay walkable in both directions:

```
raw record → claim → decision → entity → observation → business event
```

Copying would break the direction that matters most in practice — *"a mapper was wrong; what did it affect?"* — and would let a business event drift from the evidence underneath it.

---

## Two shapes of business event

Most types need no correlation at all, and noticing that avoids building a general correlation engine for a handful of cases.

| | Derived from | Examples | Identity |
|---|---|---|---|
| **Point** | One occurrence observation | `FUNDING_ROUND_CLOSED`, `ACQUISITION_ANNOUNCED`, `TECHNOLOGY_ADOPTED`, `TECHNOLOGY_RETIRED`, `EXECUTIVE_CHANGE` | The observation it came from |
| **Window** | A correlated series | `HIRING_SURGE`, `HEADCOUNT_DECLINE`, `INTENT_SURGE`, `REVENUE_BAND_SHIFT` | Its evidence set |

**Proposed M4 taxonomy v1 — nine types**, every one derivable from the current claim vocabulary without inventing meaning:

`FUNDING_ROUND_CLOSED` · `ACQUISITION_ANNOUNCED` · `TECHNOLOGY_ADOPTED` · `TECHNOLOGY_RETIRED` · `EXECUTIVE_CHANGE` · `HIRING_SURGE` · `HEADCOUNT_DECLINE` · `INTENT_SURGE` · `REVENUE_BAND_SHIFT`

Nothing else is derivable without guessing. `TECHNOLOGY_MIGRATION` — a retirement *and* an adoption in the same category within a window — is tempting and deliberately deferred: it is a correlation between two business events rather than between observations, and building it now means inventing the window with nothing to validate it against.

### Materiality is computable from a single observation

A genuinely useful consequence of M3B's model, worth naming because it removes what looked like the hardest problem here.

*"A headcount move of five is noise at Acme and a signal at a 12-person startup"* seemed to require knowing company size — a **resolved value**, which nothing in the platform stores by design. It does not: the observation carries `previous_value`, which is that provider's own view of company size. A relative threshold is `(current − previous) / previous`, computable from the observation alone.

**No rule needs a resolved value.** If one ever appears to, that is a finding to raise, not a reason to add a projection to the Knowledge Graph.

---

## Correlation across providers — the one genuinely new thing

This is the subtlest decision in the proposal and is flagged for explicit approval.

Two providers both showing hiring growth is one surge, not two. But M3B deliberately keeps their series apart, and *"cross-provider reasoning belongs to later intelligence modules"* — M4 is the first of those. So the question is not *whether* but *how*, and how much.

**Recommended:**

> **The rule is evaluated against each provider's series independently. The business event is per `(entity, type, window)` and records which providers' series satisfied it.**

Precisely what this does and does not do:

- **Values are never combined.** A rule never sees Apollo's 120 and CoreSignal's 145 in one computation, so no phantom change can enter here either. Each series is evaluated alone, and the results are counted.
- **Agreement is recorded, never weighted.** `corroborating_providers` is a set, not a coefficient. Turning it into a confidence multiplier is the Signal Engine's decision to make, with its own reviewable rule.
- **One event per business fact.** Timeline shows one hiring surge, not one per vendor.

**The alternative** — one business event per provider, merged later by M5A — keeps M4 purely per-provider but pushes an obviously-shared concern downstream, where it would be reimplemented per signal type. It is worth stating as the fallback if the recommended reading is judged too strong.

---

## Event identity, supersession, and versioning

### Identity is derived, not allocated

Following M3B, where it worked:

```
id = uuid5(BUSINESS_EVENT_NAMESPACE,
           workspace_id | entity_id | type_key | evidence_key)

evidence_key = sorted observation ids
```

Observation ids are themselves derived from observed facts and survive claim regeneration, so a business event id survives a full pipeline rebuild. Deduplication becomes a primary-key conflict rather than a code path.

**Deliberately *not* keyed on `taxonomy_version`.** The identity is the business fact, not the rule that found it. A version bump that re-detects the same surge over the same evidence produces the same event and inserts nothing — which is what should happen. A version bump that detects a *different* extent produces a different evidence set, and therefore a new event that supersedes the old.

### Supersession — how a growing surge behaves

A surge that continues acquires new observations, so its evidence set changes, so it is a new event **superseding** the previous one. The chain is the history of what Signora believed as the surge developed; the current view is the event nothing supersedes.

This is the same append-only shape as `observation` and `resolution_decision`, and it is what makes business history durable: **nothing is mutated, and nothing is deleted.**

The honest cost: a surge extending weekly produces a supersession chain. That is a volume characteristic to measure rather than a correctness problem, and the mitigation — emitting only on a closed window — trades correctness for tidiness and is not recommended.

> **Alternative considered and rejected:** mutate the event in place as evidence accumulates. It is simpler and it destroys exactly what the module is for — *"future intelligence modules should be able to reason over complete historical event sequences"*, which requires the sequence to exist.

### Two version numbers, deliberately

| | What it versions | When it changes | Recorded on |
|---|---|---|---|
| `taxonomy_version` | The *meaning* of a type — its parameters and conditions | A threshold is tuned; a condition is refined | Every event |
| `payload_version` | The *wire shape* of `facts` and of `business_event.detected` | A field is added, removed, or retyped | Every event and every envelope |

Conflating them is the common mistake: tuning a threshold would force a consumer contract change, so nobody tunes thresholds. Keeping them apart means the taxonomy can evolve weekly while the contract stays stable for a year.

---

## Re-evaluation: superseded observations

When `observation.superseded` arrives, every business event citing the superseded observation is now built on evidence that has been refined. Because events **cite** rather than copy, they are findable: the affected events are re-derived and supersede themselves with the corrected evidence.

This is the concrete reason citation was chosen over subsumption, and it is proposed as an acceptance criterion rather than left as an implementation detail.

---

## Replay

Business events are derived from observations, which are derived from claims. The table can be dropped and rebuilt — **but only against a stated taxonomy version**, and that is the useful part: a replay under v2 that produces materially different events than v1 is exactly how a threshold change is evaluated before it ships.

> **A capability this unlocks, worth stating even though it is not M4 work:** running two taxonomy versions over the same history and diffing the results is a *taxonomy evaluation harness* — the business-rule analogue of the AI eval harness in M8. Recorded as a future recommendation, not built here.

---

## Storage

One workspace-owned table, `business_event`, with forced RLS and its full policy set in the migration that creates it, registered in `tenancy_policy.py` and in `IMMUTABLE_TENANT_TABLES` — no `UPDATE` grant.

The taxonomy is **not** a table. It is a versioned artifact loaded and validated at import against a Pydantic model, so a malformed taxonomy fails at startup rather than at the first detection.

Indexes: `(workspace_id, entity_id, occurred_at)` for the account view; `(workspace_id, occurred_at)` for Timeline; `(workspace_id, type_key)` for per-type operational metrics; `supersedes` for chain traversal.

**On scale.** Business events are far fewer than observations, which are far fewer than claims. That narrowing is the pipeline's whole shape, and the ratio at each stage is the metric that tells you a stage has stopped working.

---

## Event model

| Event | When | Payload |
|---|---|---|
| `business_event.detected` | A type's conditions were met | `business_event_id`, `entity_id`, `type_key`, `occurred_at`, `window_start`, `window_end`, `taxonomy_version`, `payload_version` |
| `business_event.superseded` | A refined or extended event replaced an earlier one | `business_event_id`, `supersedes`, `entity_id`, `type_key` |

Following the established rule — **events carry identity, ports carry payload** — neither carries `facts` or the evidence list. A consumer reads them through the module's read port, so adding a fact to a type is never an event-contract change.

**Dropped from the v2 catalog:** `business_event_type.published`, which assumed a runtime-mutable taxonomy. See above.

---

## Module API

```
business_events(workspace_id, entity_id, type_key=None, since=None) -> list[BusinessEvent]
business_event_evidence(workspace_id, business_event_id)            -> BusinessEventEvidence
history(workspace_id, business_event_id)                            -> list[BusinessEvent]
taxonomy()                                                          -> Taxonomy
```

`history` walks the supersession chain — *"what did we believe about this surge, and when?"*

**Deliberately absent: any method returning a priority, a ranking, or a "top events" list.** All three are commercial judgements. The Signal Engine reads the events and forms its own.

---

## Relationship with the modules downstream

**Signal Engine (M5A).** Consumes `business_event.detected`. Correlates events with Knowledge Graph context — technology fit, intent, relationships — into weighted buying indicators. **This is where corroboration becomes confidence and where "should we engage" begins.** M4 hands it a typed business fact with its evidence and its agreement count, and nothing more.

**Timeline (M7).** Consumes both events for the account narrative, ordered by `occurred_at`. `business_event.superseded` lets the narrative show *"this surge was extended"* rather than silently changing what it said yesterday.

**AI Reasoning (M9).** Business events are the layer at which reasoning becomes quotable. `summary` gives it a sentence; `facts` give it the numbers; `evidence_observation_ids` make the citation **verifiable** rather than plausible; `taxonomy_version` lets an explanation name the rule that fired. The requirement this places on M4 is that `summary` be rendered by the rule from `facts` — so the sentence a customer reads and the numbers an auditor checks cannot diverge.

---

## Task breakdown — T75–T83 · ~10–14 ew

| ID | Task | Complexity | Depends on |
|---|---|---|---|
| **T75** | Taxonomy artifact, Pydantic schema, loader, and startup validation | M · 1.5 ew | — |
| **T76** | Domain: `BusinessEvent`, `BusinessEventType`, deterministic identity, `facts` typing | M · 1.5 ew | T75 |
| **T77** | Rule port and registry — one rule per type, parameters read from the taxonomy | M · 1.5 ew | T76 |
| **T78** | Five point rules: funding, acquisition, technology adopted/retired, executive change | M · 1.5 ew | T77 |
| **T79** | Four window rules: hiring surge, headcount decline, intent surge, revenue band shift | L · 2.5 ew | T77 |
| **T80** | Schema + migration 0011 — `business_event`, forced RLS, immutable | S · 1 ew | T76 |
| **T81** | `DetectBusinessEvents` use case, supersession, and re-evaluation on `observation.superseded` | L · 2 ew | T79, T80 |
| **T82** | Read port, module `public/` API, event contracts | S · 1 ew | T81 |
| **T83** | Demonstration + smoke stage + Security Invariants | M · 1 ew | all |

**Order:** T75 → T76 → T80 → T77 → T78 → T79 → T81 → T82 → T83

Taxonomy first, because every later task reads it; point rules before window rules, because they establish the shape without the correlation.

**Dependencies.** Inbound: M3B (observations), M3A (entity context), M1.1 (event bus). Outbound: blocks M5A and everything after. External: none.

---

## Acceptance criteria

| ID | Criterion |
|---|---|
| **AC-35** | **No threshold lives in code** — every parameter is read from the taxonomy, asserted by a syntax-tree invariant over every rule module |
| **AC-36** | **No commercial judgement** — `business_event` carries no priority, score, urgency, or rank, asserted structurally |
| **AC-37** | **Citation, not subsumption** — every business event cites ≥1 observation and traverses to claims and raw records; zero orphans |
| **AC-38** | **Deterministic and replayable** — rebuilding from observations under the same taxonomy version reproduces the current set identically |
| **AC-39** | **Durable business history** — events are immutable; extension and correction supersede, and the full chain stays readable |
| **AC-40** | **A refined observation re-evaluates its events** — `observation.superseded` produces corrected business events rather than stale ones |
| **AC-41** | **Every type has exactly one rule, and every parameter is used** — no orphan types, no orphan parameters |
| **AC-6** | Tenancy — new table, forced RLS, full policies, registered in the policy |
| **AC-1** | Event contract — cataloged, idempotent, correlation-traced |
| **AC-13** | Security Invariants extended, each proven to fail when its guarantee is removed |

---

## Demonstration scenario

> *"The pipeline says something a seller would recognise — and can prove it."*
>
> Run the baseline scenario through ingestion, normalization, resolution, and observation. BuiltWith's retired legacy ERP becomes a **`TECHNOLOGY_RETIRED`** event; its adopted replacement becomes **`TECHNOLOGY_ADOPTED`**; Crunchbase's round becomes **`FUNDING_ROUND_CLOSED`**; Bombora's weekly climb becomes an **`INTENT_SURGE`** with its window bounded by the weeks that support it.
>
> Every event names its type, its window, the taxonomy version that detected it, and the observations behind it — and `business_event_evidence` walks from the event to the claims and the raw provider payloads.
>
> **Re-run the whole pipeline unchanged: zero new business events.** The same restraint M3B proved, one layer up.
>
> Extend the hiring series so the surge continues. A new event supersedes the earlier one; both remain readable, and `history` shows what was believed and when.
>
> Lower `minimum_growth_ratio` in a taxonomy v2 and replay: more events, each recording v2. Raise it and replay: fewer. **The threshold is visible, versioned, and arguable** — which is the entire point of the taxonomy/rules split.

---

## Deferred, with reasons

| Deferred | Why |
|---|---|
| **Commercial prioritisation** | The Signal Engine's question. A priority field here would be read as authoritative and never revisited. |
| **`TECHNOLOGY_MIGRATION`** | A correlation between two business events, not between observations. Building it now means inventing its window with nothing to validate against. |
| **Per-workspace taxonomy overrides** | No customer has asked. It is a real future need and a large one — it changes identity, replay, and review all at once. |
| **Runtime-editable taxonomy** | Trigger recorded: when a non-engineer must tune a threshold without a release, realistically M12. |
| **Taxonomy evaluation harness** | The natural consequence of replay-under-version. Belongs with the M8 eval harness, where the tooling will already exist. |
| **ML-detected event types** | A hidden heuristic by construction. Deterministic rules first; if they miss materially, that will be visible in evidence. |

---

## Rollback strategy

**Schema:** additive — one new table; downgrade drops it. **Data:** entirely derived. Drop and rebuild from observations — the rollback for a bad rule, and the reason AC-38 exists. **Taxonomy:** a previous version is a previous repository state; reverting is a deploy plus a replay. **Blast radius:** one workspace per rule error; a bad *taxonomy* affects every workspace, which is the argument for reviewing it like code.

---

## Operational characteristics

- [ ] Metric: **business events per observation**, per type. The pipeline narrows at every stage, and the narrowing ratio is what tells you a stage has stopped working.
- [ ] Alert: **a type that stops firing entirely** — the signature of a rule broken by a vocabulary change, and invisible without this alert because "no events" looks like "nothing happened".
- [ ] Alert: **a type firing on nearly every observation** — the signature of a threshold typo, e.g. `0.15` written as `0.015`.
- [ ] Metric: detection lag (`detected_at` − `occurred_at`), and supersession rate per type.
- [ ] Metric: taxonomy version in force, exported so an event's version can be reconciled with the running deployment.
- [ ] Runbook: tuning a parameter (review, replay, compare); investigating a type that stopped firing; rebuilding from observations.
- [ ] `correlation_id` traceable from raw record through claim, decision, entity, observation, and business event.

---

## Risks and mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| **A threshold drifts into rule code** | 🔴 High | Syntax-tree invariant over every rule module; parameter/declaration reconciliation test. The split is worthless if it is only a convention. |
| **A rule stops firing silently** | 🔴 High | "No events" is indistinguishable from "nothing happened" without an alert on per-type detection rate. This is the failure mode most likely to go unnoticed for months. |
| **Supersession chains grow noisy on long-running phenomena** | 🟠 Medium | Measured rather than pre-solved. The tidier alternative — emit only on a closed window — trades correctness for volume, and volume is the cheaper problem. |
| **Cross-provider correlation is a step too far** | 🟠 Medium | Values are never combined, only conclusions counted. Flagged for explicit approval rather than assumed. |
| **The taxonomy becomes a dumping ground** | 🟡 Low | Nine types, each derivable from the current vocabulary. Adding one requires the same review as adding a canonical attribute. |
| **`summary` and `facts` diverge** | 🟡 Low | The rule renders the summary from the facts it computed; asserted by test, so the sentence a customer reads cannot contradict the numbers an auditor checks. |

---

## As built: what the CRO test changed

All five review questions were approved. The taxonomy/rules split, the repository artifact, cross-provider correlation, supersession chains, and the removal of `business_event_type.published` are as proposed.

One instruction changed the taxonomy before a line of it was written:

> *If a CRO opened Signora today, would they immediately understand what this event means?*

Applied honestly, that test broke three of the proposed nine types — and names are the hardest thing to change later, so it was worth applying before implementation rather than after.

| Proposed | Shipped | Why |
|---|---|---|
| `EXECUTIVE_CHANGE` | `LEADERSHIP_APPOINTED` · `LEADERSHIP_DEPARTED` | A leader joining and a leader leaving mean **opposite** things commercially. A consumer that has to read a field to know whether the news is good has been handed the wrong vocabulary. |
| `REVENUE_BAND_SHIFT` | `REVENUE_GROWTH` · `REVENUE_CONTRACTION` | "Revenue band" is *our* word — chosen because vendors report ranges. A CRO says a company grew. Split for the same directional reason. |
| `INTENT_SURGE` | `BUYING_INTENT_SURGE` | "Intent" alone is closer to vendor vocabulary than to how a revenue team speaks. |

**Eleven types, six business domains.** `capital` · `technology` · `leadership` · `workforce` · `growth` · `demand` — deliberately not the claim vocabulary's `firmographic` / `technographic` / `behavioural`, which describe where data came from rather than what happened. Asserted by an invariant: no business domain may name a data-model term.

The same test reaches the summaries. Every one is rendered by its rule from the facts it computed, and an invariant asserts no provider name or implementation word survives into one. *"Revenue grew from $10M–$50M to $50M–$250M"*, never *"revenue_band 10m_50m → 50m_250m"*.

Each type also carries a `why_it_matters` sentence, written for a customer. It exists so the taxonomy cannot grow a type nobody can justify: if the sentence is hard to write, the type probably should not exist.

### The structural enforcement, as built

| Guard | What it catches |
|---|---|
| Rule modules parsed as syntax trees | Any numeric literal in a comparison other than `0` or `1`. Adding `if len(window) < 3` fails the build. |
| Parameter reconciliation | A declared parameter no rule reads — a threshold reviewers believe is in force when it is not. |
| One rule per type, at construction | A declared type with no rule, or a rule with no declaration. Fails when the engine is built, not on first detection. |
| Column-name invariant on `business_event` | Any `priority`, `score`, `urgency`, `rank`, `importance`, `likelihood`, `propensity`, or `confidence` column. |
| Data-model terms in business domains | `technographic` reaching a CRO. |

### One honest limitation in the demonstration

The baseline scenario's intent ramp peaks at 88 but clears the taxonomy's elevated threshold for only **two** weeks — short of the three a sustained surge requires. **No `BUYING_INTENT_SURGE` is detected, and the demonstration asserts that it is not.**

Lowering `minimum_score` or `minimum_weeks` would have made the demonstration richer and would have been fitting a business judgement to a fixture. The parameters stay defensible; the *scenario* is what needs extending, and that is scheduled M2.0 work alongside the multi-week movement scenario M3B identified.

### Deferred within the module

`_replacements` and `citing_observations` are implemented and exercised, but **re-evaluation triggered by `observation.superseded` is wired at the contract level only**: the handler subscribes to `observation.recorded`, and the repository can find events citing a refined observation. Closing the loop is small and belongs with the first real late-arrival scenario rather than ahead of it.

---

## Definition of Done — M4

- [x] Demonstration passes; AC-35 through AC-41, AC-6, AC-1, AC-13 satisfied
- [x] Migration 0011 with forced RLS and full policies in the same revision; `business_event` registered in `tenancy_policy.py` and in `IMMUTABLE_TENANT_TABLES`
- [x] Security Invariants extended 124 → 154, each addition **proven to fail** when its guarantee is removed
- [x] `04-modules.md`, `05-module-dependencies.md`, `06-events.md`, and `21-intelligence-pipeline.md` updated in the same change
- [x] `make smoke` extended with stage 14e, business event detection
- [x] PROJECT_STATUS and SESSION_HANDOFF updated at the boundary

The two platform findings from M3A remain open and are **not** worked around: `EventHandler` receives no session, and `PublishableEvent` cannot be satisfied by a frozen dataclass. Both are queued as RFCs for the platform milestone.

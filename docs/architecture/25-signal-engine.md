# 25 — Signal Engine

> Status: **IMPLEMENTED** — M5A, 2026-07-29
> Audience: All engineers, EMs, and technical stakeholders at Signora
> Revision: **v2** — the design as built. All six review questions were approved; the outcomes and one refinement are recorded in *[As built](#as-built-decisions-taken-and-one-refinement)*.
>
> Prerequisite reading: [21-intelligence-pipeline.md](21-intelligence-pipeline.md), [24-business-event-engine.md](24-business-event-engine.md).

---

## The transition this module represents

Everything the pipeline has built so far is **globally true**. A claim is what a provider asserted. An entity is who it is about. An observation is what changed. A business event is what that means in business terms — *"Acme grew headcount 40% over 90 days"* is true whoever is reading it.

**Signals are the first thing in Signora that is true only for one customer.**

*"Acme is in a hiring surge"* is a fact. *"Acme's hiring surge is an expansion opening for us"* is a claim about **this workspace's** commercial position — false for a company selling something else, and unknowable from the evidence alone.

That is the defining characteristic of M5A, and it introduces a category the platform has never had: **workspace-specific interpretation of globally-true intelligence.** Every design decision below is downstream of keeping those two things apart.

---

## The boundary, stated first

> **The Signal Engine answers "why might this matter to this customer?"**
> **It does not answer how likely a purchase is, which account to prioritise, what to recommend, or what to do.**

Those belong to the Buying Score Engine, the Opportunity Engine, and the Recommendation Engine.

The pipeline now reads as five questions, and the fifth is new:

| Stage | Question | True for |
|---|---|---|
| Claim | What was asserted? | everyone |
| Knowledge Graph | Who is it about? | everyone |
| Observation | What changed? | everyone |
| Business Event | Why is that business-relevant? | everyone |
| **Signal** | **Why might that matter to *this* customer?** | **one workspace** |
| Buying Score | How much does it matter, overall? | one workspace |

---

## Signals are hypotheses, not facts

This is the second framing that shapes the whole module, and it needs to be visible in the domain model rather than only in prose.

**A business event describes reality. A signal proposes a commercial reading of it.** The proposal makes that structural in four ways:

**1. A signal asserts nothing about the world.** It carries no facts of its own — only a reference to the business events that carry them, plus the interpretation this workspace applies. Everything factual in a signal is a citation.

**2. Contradiction is preserved, never resolved.** A `CONTRACTION_RISK` and an `EXPANSION_OPPORTUNITY` can be live for the same account at once, drawn from different business events. **The Signal Engine must not pick.** This is the claim-disagreement principle one layer up: two hypotheses about the same company are information, and collapsing them destroys exactly what a seller needs to see. Reconciling them is the Buying Score Engine's job, with its own reviewable rule.

**3. A hypothesis has a shelf life.** A hiring surge from eight months ago is weaker grounds than last week's. The catalog declares a relevance window per signal type, and the signal records `relevant_until` — a *derived date*, not a weight.

**4. A signal explains its own reasoning, in two halves.** Not only *what evidence*, but *why that evidence matters here*:

> *"Flagged as an **expansion opportunity** because your profile treats hiring surges and funding rounds as primary expansion indicators. Based on: Acme grew headcount 40% over 90 days; Acme raised 24M USD in a Series B round."*

The first sentence is the interpretation; the second is the fact. A customer can challenge either independently — and being able to challenge it is what makes it trustworthy.

---

## What belongs to the platform, and what belongs to a workspace

The most consequential question in this milestone. Getting it wrong in either direction is expensive: too much global and signals are just business events again; too much per-workspace and the vocabulary forks into a thousand private dialects nothing downstream can reason about.

| Concept | Platform (global) | Workspace |
|---|---|---|
| **Signal catalog** — the types, what each hypothesis *means*, which business event types may contribute, the relevance window | ✅ | |
| **Detection rules** — single-event vs composite, window traversal | ✅ | |
| **Which types are relevant, and how central** | | ✅ |
| **Tuning within catalog-declared bounds** — window length, minimum contributors | | ✅ |
| **Signal instances** | | ✅ (data, RLS) |

> **A workspace can never invent a signal type.** It configures *relevance* over a global catalog.

That constraint is not a limitation to remove later — it is what makes the rest of the pipeline possible. The user's own instruction for business events applies with equal force here: future Buying Scores, Opportunities, AI explanations, analytics, and documentation must be able to **reference signal types directly**. A per-workspace type vocabulary would mean AI Reasoning could not be prompted about `EXPANSION_OPPORTUNITY`, benchmark analytics could not compare across customers, and every downstream module would re-derive meaning from business events — forking the vocabulary a second time.

### Why this differs from M4, and why that is principled

M4 put its taxonomy in a **repository artifact**; M5A puts its profile in the **database**. The two look inconsistent until you ask *whose configuration it is*:

| | Business event taxonomy | Signal profile |
|---|---|---|
| Whose? | **Signora's** — our language | **The customer's** — their commercial position |
| Who changes it? | Us, in a pull request | Them, eventually through the UI (M12) |
| Change cadence | A release | Whenever their strategy changes |
| Home | Versioned repository artifact | Versioned rows, per workspace |

**The deciding factor is ownership, not convenience.** A customer cannot be asked to wait for a Signora release to say that hiring surges matter to them. Equally, Signora's business vocabulary cannot be edited at runtime by anyone, or replay and review both collapse.

The **signal catalog** — the global half — stays a repository artifact for exactly M4's reasons.

---

## Configuration alternatives, evaluated

### A — One global signal catalog, no per-workspace configuration

Every workspace gets the same signals.

**Rejected.** It makes the Signal Engine a second business event layer with a different name. If the interpretation is identical for everyone, the stage has no reason to exist — and the module's entire premise is that *"hiring surge indicates expansion opportunity"* is customer-specific.

### B — Free-form per-workspace rules

Each workspace authors its own detection logic, in a DSL or an embedded scripting layer.

**Rejected, twice over.** It is the rules-engine trap from M4 multiplied by every tenant: a language Signora owns forever, with no type checker and no debugger. It also executes customer-authored logic inside the pipeline, which is a security surface nobody asked for. And it forks the vocabulary, so nothing downstream can reason about signals across workspaces.

### C — Global catalog + per-workspace **relevance profile** — **recommended**

The catalog declares what commercial hypotheses exist and how each is detected. The profile declares, per workspace, which of them matter and how centrally.

This keeps interpretation customer-specific while keeping the *language* global. It is the smallest change that makes signals genuinely customer-relative, and it is the only option that preserves cross-workspace explainability.

### D — Inferred relevance

Learn what matters to a workspace from its own behaviour — which accounts it works, which signals it acts on.

**Deferred, not rejected.** It is a genuinely good idea and it is unbuildable now: there is no behaviour to learn from until the product has users. It also cannot be the *only* mechanism, because a new workspace would get nothing. **The right sequencing is an explicit profile first, with inference later proposing changes to it** — a recommendation a human accepts, which keeps the configuration explainable. Recorded as a future recommendation.

---

## Configuration lifecycle

The profile is data a customer changes, so it needs the same treatment as everything else that changes: **immutable, versioned, superseded rather than edited.**

```
SignalProfile(id, workspace_id, version, entries, created_at, created_by, supersedes)
ProfileEntry(signal_type, relevance, window_days?, minimum_contributors?)
```

| Property | Why |
|---|---|
| **Immutable, `supersedes` backwards** | A signal records the profile version that produced it. If the profile could be edited, every historical signal would become unexplainable — *"why was I told this?"* would have no answer, because the reason changed underneath it. |
| **`created_by` on every version** | Auditability. A configuration change is a commercial decision, and a customer should be able to see who made it and when. |
| **An absent profile falls back to the catalog default** | Declared in the catalog artifact, so the out-of-box behaviour is reviewable rather than emergent. A signal produced under it records `profile_version = 0`. **No seeding write, and no new dependency on Workspace & Tenancy.** |
| **`IGNORED` is an explicit relevance** | Distinct from absence. "We deliberately do not care about displacement" and "nobody has configured this yet" are different facts, and only one of them should be revisited. |

### Relevance is a category, never a number

```
PRIMARY · SUPPORTING · CONTEXTUAL · IGNORED
```

Declared per workspace, never computed — the same discipline as `MatchStrength`, and for the same reason: a number invites weighting, weighting invites thresholds, and a threshold here would be a propensity judgement in the wrong module.

> **Consequence worth stating plainly: the Signal Engine contains no scores at all.** The only numbers anywhere in it are windows and counts. The Buying Score Engine maps relevance categories to weights *in its own configuration*, which is where "how much does this matter" belongs.

This also means the v2 catalog needs correcting — see *Event model*.

---

## Signal composition — atomic, composite, or both

The question posed: is a signal one business event's commercial reading, or may several combine?

> Hiring Surge **+** Funding Raised **+** Technology Modernization → **Expansion Opportunity**

### A — Atomic only

One signal per business event; composition happens downstream.

**Rejected.** *"Expansion opportunity"* is precisely what a customer wants to see, and if M5A does not produce it, the only remaining homes are the Buying Score Engine — a *scoring* module, which would have to grow interpretation logic — or AI Reasoning, which is non-deterministic. Both are worse homes for a rule that should be explainable and reviewable.

### B — Composite only

Every signal requires several contributing events.

**Rejected.** A funding round on its own is a legitimate commercial signal. Requiring composition would invent correlations to satisfy the model.

### C — Both, with composition declared per type — **recommended**

Each catalog type declares its shape:

- **`SINGLE`** — one contributing business event is enough (`BUDGET_UNLOCKED` from a funding round).
- **`COMPOSITE`** — at least *N* **distinct** contributing business event *types* within a window (`EXPANSION_OPPORTUNITY` from any two of hiring surge, revenue growth, funding).

This mirrors M4's point/window split exactly, one layer up, and it is declarative: whether a hypothesis needs corroborating phenomena is a property of the hypothesis, not of the code.

**Distinct *types*, deliberately** — three hiring surges are one phenomenon reported repeatedly, not three independent grounds for believing a company is expanding.

### The overlap this creates, named rather than discovered later

An atomic `EXPANSION_OPPORTUNITY`-contributing signal and a composite one may cite the same business event. Both stand — **suppressing the constituent would destroy evidence** — and the overlap is visible because both cite the same business event ids.

> **This places one requirement on M5B, recorded now so it is not discovered late: the Buying Score Engine must deduplicate on contributing business events, not on signals.** Two signals resting on one hiring surge are one piece of evidence read two ways.

---

## Domain model

### `SignalType` — catalog entry (global)

```
SignalType(key, title, hypothesis, why_it_matters, shape,
           contributing_event_types, minimum_contributors,
           window_days, relevance_window_days, default_relevance)
```

`hypothesis` is the sentence the type proposes — *"Sustained investment suggests the company is expanding capacity"* — written for a customer, and phrased as a **possibility**. Every type passes the CRO test, and the language stays hypothetical: *suggests*, *may indicate*, never *is*.

### `Signal` — an instance (per workspace)

```
Signal(id, workspace_id, entity_id, signal_type, relevance,
       occurred_at, window_start, window_end, generated_at, relevant_until,
       rationale, contributing_event_ids, contributing_event_types,
       catalog_version, profile_version, payload_version, supersedes)
```

| Field | Why |
|---|---|
| `relevance` | The category from the profile **at generation time**, denormalized so the signal stays self-describing when the profile later changes. |
| `rationale` | The two-part sentence — interpretation *and* evidence. Rendered by the rule, so what a customer reads and what an auditor checks cannot diverge. |
| `contributing_event_ids` | Citation. The chain must never break. |
| `contributing_event_types` | Carried alongside the ids so a consumer can reason about *shape* — "this rests on hiring and funding" — without a join. |
| `occurred_at` | From the business events, never generation time. Timeline orders on it. |
| `relevant_until` | Derived from `occurred_at` + the catalog's relevance window. **A date, not a weight.** |
| `catalog_version` / `profile_version` | The two halves of *why this exists*. Without both, a historical signal is unexplainable. |
| `supersedes` | Backwards, as everywhere else. |

**No score, no priority, no likelihood, no rank** — proposed to be enforced by the same column-name invariant M4 uses.

---

## Proposed catalog v1 — nine types

Every one is derivable from the eleven business event types without inventing meaning, and every one passes the CRO test.

| Type | Shape | Rests on | The hypothesis |
|---|---|---|---|
| `EXPANSION_OPPORTUNITY` | composite (≥2) | hiring surge · revenue growth · funding round closed | Sustained investment suggests capacity is being added |
| `BUDGET_UNLOCKED` | single | funding round closed | New capital usually precedes new spending |
| `DISPLACEMENT_OPPORTUNITY` | single | technology retired | Something was dropped; the replacement decision is recent or imminent |
| `MODERNIZATION_UNDERWAY` | composite (≥2) | technology adopted · technology retired | A stack is being replaced, not merely extended |
| `NEW_DECISION_MAKER` | single | leadership appointed | New leaders re-examine what they inherited |
| `DECISION_MAKER_DEPARTED` | single | leadership departed | Decisions their owner was driving may stall or reopen |
| `ACTIVE_EVALUATION` | single | buying intent surge | Research precedes purchase; an evaluation may already be under way |
| `CONSOLIDATION_UNDERWAY` | single | acquisition announced | Acquisitions force system and budget consolidation |
| `CONTRACTION_RISK` | composite (≥1) | headcount decline · revenue contraction | Spending authority and priorities are being re-scoped |

**Overlap is deliberate.** An acquisition produces both `BUDGET_UNLOCKED` and `CONSOLIDATION_UNDERWAY` — two hypotheses from one fact, both preserved, neither resolved. That is the module working correctly, not a modelling error.

**`DECISION_MAKER_DEPARTED`, not "champion lost"** — Signora does not know whether they were a champion, and a vocabulary that claims more than the evidence supports is exactly what the CRO test exists to catch.

---

## Explainability

The chain must be walkable end to end, and M5A adds one link plus one new dimension:

```
Signal → Business Events → Observations → Knowledge Graph → Claims → Raw Provider Records
   │
   └── Signal Profile version + Signal Catalog version   ← why it matters *here*
```

Every earlier stage answered *"what is the evidence?"*. A signal must also answer *"why does that evidence matter to me?"*, and the profile version is what makes that answerable months later.

**Proposed acceptance criterion:** `signal_explanation(workspace_id, signal_id)` returns the signal, its rationale, its business events *with their summaries*, and the profile entry that made it relevant — one call, no joins by the caller.

The five questions this module is designed against:

| Question | Answered by |
|---|---|
| Would a customer understand why this signal exists? | `hypothesis` + `rationale`, written for a CRO |
| Could they explain it to a colleague? | The two-part rationale — interpretation and evidence |
| Would they trust it? | Every fact is a citation; the module asserts nothing itself |
| Could they challenge it? | Both halves are separately challengeable — the evidence, and their own profile |
| Could Signora justify it? | `catalog_version` + `profile_version` name the exact rules in force |

---

## Identity, supersession, and replay

**Identity is derived**, as everywhere since M3B:

```
id = uuid5(SIGNAL_NAMESPACE, workspace_id | entity_id | signal_type | sorted(business_event_ids))
```

**Deliberately not keyed on the profile version.** The identity is *this hypothesis over this evidence*. A profile change that keeps the type produces the same signal and inserts nothing; a change in *relevance* is recorded on the new generation only if the evidence also changed. A profile change that removes a type simply stops producing it — historical signals remain, interpretable through their recorded `profile_version`.

**Supersession** works as in M4: a composite whose evidence grows supersedes the smaller view, and the chain is the history of what was believed.

**Replay has two legitimate modes**, and the design must make which one explicit rather than defaulting silently:

| Mode | Uses | Answers |
|---|---|---|
| **Historical** | the profile version in force at the time | *"Reproduce what we told them."* The audit rebuild. |
| **Current** | the current profile | *"What would we say now, given the same history?"* The evaluation rebuild — how a customer previews a configuration change before committing it. |

The second is a genuine product capability falling out of the architecture: **preview a profile change against your own history before adopting it.** Not M5A work, but the design must not preclude it, which means never conflating the two modes.

---

## Storage

Two workspace-owned tables, both with forced RLS, full policy sets in the migration that creates them, registered in `tenancy_policy.py`, and both in `IMMUTABLE_TENANT_TABLES` — no `UPDATE` grant:

- **`signal`** — instances.
- **`signal_profile`** — versioned configuration, superseded rather than edited.

The **catalog** is not a table: a versioned repository artifact validated at startup, exactly as the business event taxonomy is.

Indexes: `(workspace_id, entity_id, occurred_at)` for the account view · `(workspace_id, occurred_at)` for Timeline · `(workspace_id, signal_type)` for per-type operational metrics · `(workspace_id, relevant_until)` for the live set · GIN on `contributing_event_ids` for the supersession and re-evaluation queries.

---

## Event model

| Event | When | Payload |
|---|---|---|
| `signal.generated` | A hypothesis is supported for this workspace | `signal_id`, `entity_id`, `signal_type`, `relevance`, `occurred_at`, `relevant_until`, `catalog_version`, `profile_version` |
| `signal.superseded` | A composite grew, or a conclusion was corrected | `signal_id`, `supersedes`, `entity_id`, `signal_type` |

**Two corrections to the v2 catalog are proposed**, both consequences of the layering:

1. **`signal.generated` loses its `score`.** The Signal Engine produces no scores; propensity is M5B's.
2. **`signal.scored` is removed entirely.** Its producer would have to be a scoring model, which lives in the Buying Score Engine — and that module already publishes `buying_score.updated`. An event with no producer is a contract nobody is keeping, the same reasoning that removed `business_event_type.published`.

> **Deferred: `signal_profile.updated`.** M5B will eventually want to re-evaluate when interpretation changes, but M5B does not exist. Adding it now would be an event with no consumer.

---

## Module API

```
signals(workspace_id, entity_id, signal_type=None, live_only=True) -> list[Signal]
signal_explanation(workspace_id, signal_id)                        -> SignalExplanation
history(workspace_id, signal_id)                                   -> list[Signal]
profile(workspace_id)                                              -> SignalProfile
catalog()                                                          -> SignalCatalog
```

`live_only` filters to signals that are unsuperseded, still within `relevant_until`, and whose type is not `IGNORED` in the current profile — the three ways a hypothesis stops being current.

**Deliberately absent: any method returning a ranked list, a top-N, or a score.** All three are the Buying Score Engine's question. A convenience method here would put propensity behind an innocuous call, and within a year every consumer would use it.

---

## Relationship with the modules downstream

**Buying Score Engine (M5B).** Consumes `signal.generated`. Aggregates signals into a propensity score per account, applying its own weighting to relevance categories and its own decay to `relevant_until`. **The two requirements M5A places on it, recorded now:** deduplicate on contributing *business events* rather than on signals, and resolve contradictory signals with a stated, reviewable rule rather than by picking.

**Timeline (M7).** Consumes both events, ordered by `occurred_at`. `signal.superseded` lets the narrative show a hypothesis being strengthened rather than silently changing.

**AI Reasoning (M9).** Signals are where reasoning becomes *commercially* quotable. Because the catalog is global, a prompt can be written about `EXPANSION_OPPORTUNITY` once and apply to every customer; because `rationale` is rendered from the profile and the evidence, a generated explanation can cite a real chain rather than a plausible one.

---

## Task breakdown — T84–T92 · ~8–13 ew

| ID | Task | Complexity | Depends on |
|---|---|---|---|
| **T84** | Signal catalog artifact, schema, loader, startup validation | M · 1.5 ew | — |
| **T85** | Domain: `Signal`, `SignalType`, `Relevance`, deterministic identity | M · 1.5 ew | T84 |
| **T86** | Schema + migration 0012 — `signal`, `signal_profile`, forced RLS, immutable | M · 1.5 ew | T85 |
| **T87** | Profile model, versioning, supersession, and catalog-default fallback | M · 1.5 ew | T86 |
| **T88** | Rule port and registry; single-event rules | M · 1.5 ew | T85 |
| **T89** | Composite rules — distinct contributing types within a window | L · 2 ew | T88 |
| **T90** | `GenerateSignals` use case: profile resolution, supersession, relevance | L · 2 ew | T87, T89 |
| **T91** | Read port, `signal_explanation`, module `public/` API, event contracts | M · 1.5 ew | T90 |
| **T92** | Demonstration + smoke stage + Security Invariants | M · 1 ew | all |

**Order:** T84 → T85 → T86 → T87 → T88 → T89 → T90 → T91 → T92

**Dependencies.** Inbound: M4 (business events), M3A (entity context), M1.1 (event bus). Outbound: blocks M5B and everything after. External: none.

---

## Acceptance criteria

| ID | Criterion |
|---|---|
| **AC-42** | **Customer-specific interpretation** — the same business events produce different signals in two workspaces with different profiles, and identical signals in two workspaces with identical profiles |
| **AC-43** | **No commercial scoring** — `signal` carries no score, priority, likelihood, or rank, asserted structurally; no numeric relevance anywhere |
| **AC-44** | **Contradiction preserved** — opposing signals coexist for one entity; nothing is suppressed or reconciled |
| **AC-45** | **Two-part explainability** — every signal names both its evidence and the profile entry that made it relevant, in one call |
| **AC-46** | **Unbroken chain** — signal → business events → observations → entity → claims → raw records, with zero orphans at every hop |
| **AC-47** | **Configuration is auditable** — every profile version is immutable, attributed, and reproducible; every signal names the version that produced it |
| **AC-48** | **Replay is explicit** — historical and current replay modes both work and are never conflated |
| **AC-49** | **The vocabulary stays global** — a workspace cannot introduce a signal type; profiles configure relevance only |
| **AC-6** · **AC-1** · **AC-13** | Tenancy · event contract · Security Invariants extended, each proven to fail |

---

## Demonstration scenario

> *"The same company, two customers, two different readings — and both can be challenged."*
>
> Run the pipeline to business events. **Workspace A** sells capacity-planning tooling and marks hiring surges and funding as `PRIMARY`. **Workspace B** sells an ERP competitor and marks technology retirement `PRIMARY`, hiring `IGNORED`.
>
> The **same** business events produce **different signals**: A sees `EXPANSION_OPPORTUNITY`; B sees `DISPLACEMENT_OPPORTUNITY` and no expansion signal at all. Neither is wrong, and the business events underneath are byte-identical.
>
> Every signal explains itself in two halves — *"because your profile treats technology retirement as a primary displacement indicator"* and *"based on: Acme stopped using LegacyERP"* — and `signal_explanation` walks from the signal to the raw provider payload without the caller writing a join.
>
> Introduce contraction evidence alongside the expansion evidence. **Both signals stand.** The Signal Engine does not decide which reading wins.
>
> Change Workspace A's profile to mark hiring `IGNORED`. Historical signals remain readable with their original `profile_version`; a **current-mode replay** produces the smaller set, and a **historical-mode replay** reproduces what the customer was originally told.
>
> Finally, re-run the whole pipeline unchanged: **zero new signals.**

---

## Deferred, with reasons

| Deferred | Why |
|---|---|
| **Propensity scoring and prioritisation** | The Buying Score Engine's question. A score here would be read as authoritative and never revisited. |
| **ICP / account-fit filtering** | *"Does this account look like our customers?"* is a property of the account, not of an event — and it is prioritisation. Belongs with M5B or M6. |
| **Inferred relevance (Option D)** | No behaviour to learn from until the product has users. The right sequencing is explicit profiles first, with inference later *proposing* changes a human accepts. |
| **Per-workspace signal types** | Would fork the vocabulary and make cross-customer reasoning, benchmarking, and AI prompting impossible. |
| **`signal_profile.updated`** | M5B does not exist; an event with no consumer is a contract nobody keeps. |
| **Profile-change preview UI** | The capability falls out of current-mode replay; the interface belongs with the business UI at M12. |

---

## Rollback strategy

**Schema:** additive — two new tables; downgrade drops them. **Data:** entirely derived, except profiles, which are customer configuration and must survive a signal rebuild. **Catalog:** a previous version is a previous repository state. **Blast radius:** one workspace per profile error; a bad *catalog* affects every workspace, which is the argument for reviewing it like code.

> **One asymmetry worth stating: `signal` is derived and rebuildable; `signal_profile` is not.** It is the first genuinely customer-authored data in the platform, and it cannot be regenerated from anything. It needs backup and restore treatment that derived tables do not.

---

## Operational readiness

- [ ] Metric: **signals per business event, per type, per workspace.** The pipeline narrows at every stage; here the narrowing is also *configuration-dependent*, so a workspace generating none is a profile problem, not a pipeline problem — and telling those apart matters.
- [ ] Alert: a signal type that stops firing across **all** workspaces — a broken rule. Distinct from one that stops in a single workspace, which is usually a deliberate `IGNORED`.
- [ ] Alert: a workspace with an empty live signal set for an extended period — the leading indicator of a misconfigured profile, and invisible without it.
- [ ] Metric: profile version churn, and the distribution of relevance categories across workspaces.
- [ ] Runbook: changing a profile (preview, adopt, replay) · investigating a signal a customer disputes · rebuilding signals from business events.
- [ ] `correlation_id` traceable from raw record through claim, decision, entity, observation, business event, and signal.

---

## Risks and mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| **The vocabulary forks per workspace** | 🔴 High | Types are catalog-only; profiles configure relevance. Asserted structurally — a workspace-authored type must be unrepresentable, not merely discouraged. |
| **A score creeps in to serve M5B** | 🔴 High | Relevance is a category with no ordering or numeric conversion, guarded as `MatchStrength` is; column-name invariant on `signal`. The pressure will be real, because M5B needs *something* — categories are enough. |
| **Contradictory signals get quietly reconciled** | 🟠 Medium | AC-44 asserts coexistence directly. The temptation appears the first time a UI has to show both. |
| **A profile edit makes historical signals unexplainable** | 🟠 Medium | Profiles are immutable and versioned; every signal records the version. This is the single strongest argument against configuration-as-mutable-row. |
| **Composite and atomic signals double-count downstream** | 🟠 Medium | Named here, with the deduplication requirement placed on M5B explicitly rather than left to be discovered. |
| **The default profile becomes the de facto product** | 🟡 Low | If most workspaces never change it, the "customer-specific" premise is untested. Worth measuring: profile-change rate is a product metric, not just an operational one. |

---

## As built: decisions taken, and one refinement

All six review questions were approved as proposed. The global catalog with a per-workspace relevance profile, the profile in versioned database rows on ownership grounds, composite signals, the removal of `signal.scored`, nine catalog types, and `relevant_until` as a derived date all ship as designed.

Two instructions sharpened the design before implementation:

### "Composite signals must enrich rather than replace"

The proposal said constituent signals would *both stand* and that the overlap would be visible through shared business event ids. The refinement asks for more: **every constituent must remain independently visible and explainable**, and the composite must add context without collapsing history.

So a composite now **names its constituents** — `constituent_signal_ids` — giving a navigable hierarchy rather than merely a detectable overlap:

> `MODERNIZATION_UNDERWAY` cites the technology adopted *and* retired, and names the `DISPLACEMENT_OPPORTUNITY` signal it enriches. Both are stored, both are queryable, and the composite adds a reading on top of one that stands on its own.

Asserted directly: a composite never suppresses the hypothesis it builds on.

### "Detection strategy" rather than "how signals are detected"

Adopted, and it turned out to be more than terminology. `SignalTypeDefinition.detection_strategy` declares **what kind of evidence supports a hypothesis** — one contributing event, or several distinct types within a window. The mechanics live in `domain/rules.py`. The catalog now states domain semantics only, so an improved implementation never changes what a signal *means* — the same separation the business event taxonomy makes, and the reason meaning can evolve slowly while derivation evolves fast.

### The structural enforcement, as built

| Guard | What it catches |
|---|---|
| Column-name invariant on `signal` | Any `score`, `priority`, `likelihood`, `propensity`, `rank`, `weight`, or `confidence` column |
| Detection strategies parsed as syntax trees | Any numeric literal in a comparison other than `0` or `1` — a window or contributor count hidden in code |
| `ProfileEntry.signal_type` typed as `SignalType` | A workspace-invented type, unrepresentable rather than discouraged |
| Hedging-language invariant on every hypothesis | A type stating its hypothesis as a **fact**, which would mean it had drifted into the Business Event Engine's territory |
| `ck_signal_relevance_is_held` | A stored signal of a type the workspace marked `IGNORED` |
| ~~`uq_signal_profile_current`~~ → `uq_signal_profile_version` | Two live interpretations for one workspace, which would make every signal generated during the overlap unexplainable. **The row above is corrected, not rewritten** — see `B-001` below |
| `signal_profile.created_by NOT NULL` | An unattributed configuration change — a commercial decision with no author |

### What the demonstration shows, including one honest limit

Two workspaces receive byte-identical business events. One reads a `DISPLACEMENT_OPPORTUNITY` and a `MODERNIZATION_UNDERWAY`; the other, having marked both `IGNORED`, reads neither — and the business events underneath are provably identical. That is the milestone's central claim, exercised through the real pipeline.

**The scenario's hypotheses are also all past their shelf life, and the demonstration asserts it.** The baseline evidence is months old and every catalog type declares a window shorter than that, so the signals were formed, remain readable, and are no longer *live*. That is the lifecycle working rather than a gap — but it does mean the live-set behaviour is exercised by the negative case only. A scenario with recent evidence is scheduled M2.0 work, alongside the three items M3B and M4 already recorded.

---

## What a signal type does not imply *(added 2026-07-30, M9 T126)*

Every `SignalTypeDefinition` carries two required fields beyond its detection rules:

- **`limitations`** — what this type does **not** prove. A property of the *type*, identical for every account and every day, so it is authored once and versioned rather than regenerated per reasoning call.
- **`suggested_validation`** — how a human independently checks or disproves it. Deliberately **not commercial advice**: it says what to verify, never what to do about it. Recommending belongs to the Recommendation Engine (M11), and a test asserts no validation step contains an imperative to contact anyone.

Both are **required** — a signal type with no stated limitations is an authoring omission, and the enterprise customers they exist for will ask the question whether or not it has been answered. Asserted against the shipped artifact, because a `min_length` constraint proves nothing about a catalog nobody filled in.

**Owned here, not by the AI Reasoning Engine** ([ADR-0030](adr/0030-the-decision-package.md), Decision 5). A parallel catalog in M9 keyed by `SignalType` would put a type's limitations somewhere other than where the type is defined. The Decision Package composes them.

> **The shipped text is engineering-authored pending domain review.** It was written to be honest rather than authoritative. That it *can* be revised by a domain expert without touching code, under version control and review, is the entire reason it lives in the catalog rather than in a prompt.

## Alternative readings: hypotheses tested and not supported *(added 2026-07-30, M9 T126)*

`SignalQueries.unsupported_types()` answers which types this entity's evidence was evaluated against and did not support, with the rules' own reason.

**Derived on demand, never stored.** Recording every non-result would write a row per (entity, type) on every run — a large table describing mostly nothing.

**No rule is re-implemented.** It is driven by `ground()`, the same function that decides whether a signal is generated at all; a second copy of that logic would diverge and the two would disagree about one set of evidence. A test asserts the query never branches on `detection_strategy`.

Two exclusions matter:

- **Types the workspace switched off are not reported.** *"Your workspace does not track this"* and *"the evidence does not support this"* are different statements, and conflating them would present a customer's own configuration as a finding about their account.
- **A live signal is never reported as unsupported**, even once its grounds have aged out of the *grounding* window. The hypothesis is still held, and contradicting the signal on the same screen would be worse than saying nothing. *(This case was found by a surviving mutation: every earlier test ran against an empty signal repository, so the check was untested.)*

> **Correcting the record:** [ADR-0030](adr/0030-the-decision-package.md) originally asserted that the Signal Engine *already* recorded rejected hypotheses. It did not — `ground()` returned an empty tuple and the fact was discarded. T122 found that and the ADR was corrected before anything was built on it.


## Definition of Done — M5A

- [x] Demonstration passes; AC-42 through AC-49, AC-6, AC-1, AC-13 satisfied
- [x] Migration 0012 with forced RLS and full policies in the same revision; both tables registered in `tenancy_policy.py` and in `IMMUTABLE_TENANT_TABLES`
- [x] Security Invariants extended 154 → 186, each addition **proven to fail** when its guarantee is removed
- [x] `04-modules.md`, `05-module-dependencies.md`, `06-events.md`, and `21-intelligence-pipeline.md` updated in the same change
- [x] `make smoke` extended with stage 14f, commercial interpretation
- [x] PROJECT_STATUS and SESSION_HANDOFF updated at the boundary

The two platform findings from M3A remain open and are **not** worked around: `EventHandler` receives no session, and `PublishableEvent` cannot be satisfied by a frozen dataclass. Both are queued as RFCs for the platform milestone.


---

## `supersedes IS NULL` was never currency — `B-001`, fixed 2026-08-01

**The row above claimed a guard that could not fail.** `uq_signal_profile_current` was `UNIQUE (workspace_id) WHERE supersedes IS NULL`, and `SqlProfileRepository.current` read the same predicate.

**On an immutable table that predicate selects the *first* version.** A revision is a new row *naming* its predecessor, so version 1 keeps the null pointer forever. Two consequences, and the second was invisible until somebody looked:

1. **`current()` returned version 1 permanently.** Every revision a customer made would have been silently ignored, and every signal generated afterwards attributed to a profile nobody was using.
2. **The index could not fail after the first write.** Two concurrent version-2 writes both carry `supersedes = <v1>`, neither is null, and both insert — the exact condition the table above said it prevented.

**It never bit because nothing has ever written a second profile version.** There is no endpoint and no screen; every test writes v1. It becomes reachable the moment a customer can edit their relevance profile, which is why it was carried as 🟠-today/🔴-then rather than closed as theoretical.

### The fix, and what it replaced the guard with

`current()` reads `MAX(version)`. A maximum cannot invert. `product_catalog` (`0019`) and `research_request` (`0021`) already read currency this way; **this is the older code catching up with the newer, not a new idea.**

The index is dropped (migration `0023`). `uq_signal_profile_version (workspace_id, version)` is what actually protects the invariant — it refuses a duplicate version at *every* version rather than only the first, so two concurrent revisions computing the same next number collide and one loses.

**`supersedes` stays.** It is a true statement about lineage and historical explanation reads through it. It is simply not a currency marker, and an invariant now refuses any index that treats it as one.

### The finding that made this worth more than one bug fix

`B-001` was raised against `signal_profile`. The regression guard was written as a **repository-wide scan** — *no index anywhere may key currency on `supersedes IS NULL`* — rather than as an assertion about one table.

**It failed immediately against two more:** `uq_scoring_model_current` (migration `0013`) and `uq_opportunity_policy_current` (`0014`), with the identical inverted `current()` reader behind each. All three are customer-authored configuration; all three are the same defect copied forward by a developer following the pattern in front of them.

**A per-table assertion would have closed one bug and left two.** That is the argument, stated generally: when a defect is a *pattern*, the invariant that prevents its return should scan for the pattern, because the same reasoning that produced it once has usually produced it more than once.

---

# R2-02 and R3-01 — saying what the evidence cannot support *(2026-08-02, Lane A)*

**Recorded before implementation.** Two findings, one argument, at two depths of the same screen.

## Why this is the highest-value slice remaining

**Every reachable journey is shipped.** J1 *which accounts*, J2 *why this one*, J3 *prove it*, J4 *act*, J5 *research* — M12.4 closed the last of them. What remains in M12 is refinement, and the question becomes which refinement a salesperson would notice.

**R2-02 is the one that is about the thing Signora sells.** The limitations disclosure is the only place any competitor's product does not go:

> *"No competitor tells a seller what their signal cannot prove. It is the most differentiating sentence on the screen and it is the smallest text on it, behind a click."*

And the Sales Manager's reaction names both the value and the failure in one line: ***"This is the bit I'd want my reps to read, and it's the bit they'll never open."***

**It is also the deterministic counterpart to what M12.4's real-model run found.** A research statement passed grounding while misreading its own evidence — *grounding guarantees provenance, not reasoning*. The catalog's limitations are the opposite kind of claim: **written by a domain expert, versioned, reviewed, identical for every account, and produced with no model at all.** Promoting the honest half of the page is worth more the day the inferred half is shown to be fallible.

**R3-01 is the same sentence one click deeper**, and it was scheduled M12.4 and not built. Together they are one slice with one argument: *Signora says what it cannot support, at every depth a reader goes.*

### What was considered and not chosen

**The brief's hierarchy pass** — *"the brief reads as panels, not a story"*, four reviews old and made worse by M12.4's seventh panel. **Still the largest open design finding, and still not this slice**: it changes every section at once, and the ordering it needs is a product judgement that wants a seller in the room. D39 refused D20 for exactly that reason. **R2-02 is a piece of it done honestly** — it makes the most valuable panel more visible without inventing an order for the rest.

**R9-04 / D5** — *what changed since you last looked*. Needs per-user read state, which is a real schema decision with an unfired trigger.

**B-004** is Lane A's and stays deferred: the product owner directed that it belongs to the slice that builds the Provider Platform consumer, which is **blocked on Lane B's slice 5**. Fixing it now would ship a schema change nothing exercises.

## The decisions

### One limitation inline, the rest behind the disclosure

The catalog **orders** them and the first is the strongest — *"investment ahead of growth says nothing about budget for **your** category"*, *"a funding round is not earmarked for any particular category"*. Showing the first is not showing an arbitrary one.

**The original reasoning is not reversed, it is calibrated.** Twelve caveats across four hypotheses reads as a product that does not believe itself, and that is still true. One caveat per claim reads as a product that knows what its claim is worth — **the difference is not the volume, it is whether each caveat sits beside the thing it qualifies.**

The disclosure keeps the rest and its count changes to *"2 more"*, because a trigger that still said *three* beside a limitation already on screen would be counting something the reader can see.

**Styled as calibration, not as warning.** No icon, no tone, no border — the same muted prose the hypothesis itself uses. A limitation drawn as an alert would make Signora look unsure of a conclusion it is in fact sure of; what it is unsure of is precisely and only what the line says.

### Absence of corroboration is stated, not implied

Fifteen of sixteen business events read *"Reported by coresignal"*. **A reader who sees one provider four times stops reading the line**, and then misses it on the account where two sources agree.

So the single-source case says **"Only coresignal has reported this"** and the corroborated case keeps *"Reported by coresignal and apollo"*. **Nothing is marked and no badge is added** — the contrast does the work, which is what makes it survive a reader who is skimming. A badge on the rare case would be a second vocabulary for a distinction the sentence already carries.

## What this deliberately does not do

**It does not caveat the score.** The limitations are properties of a *hypothesis type*, identical for every account; attaching one to the arithmetic would imply the arithmetic is uncertain, and it is not — it is a division a customer can repeat.

**It does not add a confidence number.** A percentage here would be a judgement nobody reviewed, and the catalog deliberately holds sentences rather than scores for the same reason `Relevance` is a category.

**It does not surface the catalog's own pending-review caveat.** `signals@1.json` says its limitations are *"engineering-authored pending domain review"*. That is true, it is a real finding, and it belongs to the people revising the catalog — **not on a seller's screen**, where it would undermine the sentence it qualifies without giving the reader anything to do about it.

**Raised by promoting them:** these sentences now carry more weight than they did behind a click, which makes the pending domain review more valuable than it was this morning. Recorded rather than acted on — the catalog is a reviewed artifact and revising it is a domain expert's job, not a coding session's.

## Measured against the seeded Playground

**R3-01 said *"fifteen of sixteen events read `Reported by coresignal`"*. Across the twelve seeded accounts the real ratio is starker:**

| Providers behind a business event | Events |
|---|---|
| **one** | **1,783** |
| two | 17 |

**Fewer than one event in a hundred is corroborated.** The old sentence was therefore identical on 99.06% of everything a reader could open — which is not a wording weakness, it is a line that **could not be read as information**, because nothing it said ever varied. R3-01 understated its own finding.

It also settles the design question the finding left open. *"Say something when corroboration is absent"* sounds like adding noise to the common case; at this ratio it is the opposite: **the common case was the one carrying no signal, and stating it is what gives the rare case somewhere to stand out from.**

### The finding underneath, which is not a code defect

**Corroboration is nearly absent from the dataset, and that may be a property of the simulation rather than of the world.** Each provider in `playground@2` contributes different facts about a company — which is realistic for *coverage* and means two providers rarely describe the *same* phenomenon, so the corroboration path is exercised 17 times in 1,800.

**D17 again — *the dataset, not the architecture, is the constraint*.** The pipeline computes corroboration correctly and the surface now reports it legibly; what neither can do is make a dataset produce agreement it does not contain. **Raised for whoever next extends the Playground**: a scenario in which two providers report the same headcount move, disagreeing on the number, would exercise the strongest thing the evidence drawer can say and currently exercises almost nothing. Not this lane's file (§20e) and not a defect — a demonstration gap, recorded so the next simulator change knows it is worth closing.

---

# R2-01 — the guidance is generic; what it points at is not *(2026-08-02, Lane A)*

**Recorded before implementation.** Two accounts holding `expansion_opportunity` get **word-for-word the same checks**, and an AE said the sentence that makes this the highest-value refinement left:

> *"It gave me the same advice for two different companies, so I assumed it wasn't really looking at either."*

**That is a customer concluding the product is generic** — which attacks the one claim Signora is built on, that it reasons about *this* account from *this* evidence.

## The design, and the thing it refuses to do

**The checks stay generic, and that is not a compromise.** `suggested_validation` is a property of the hypothesis *type*: what `expansion_opportunity` fails to prove is identical for every account in every workspace, which is precisely what lets it be shown with no model, no confidence figure and no caveat. **Making it per-account would make it a recommendation**, which is a different product with a different burden of proof and an owner that does not exist yet.

**So nothing above the checks changed. What changed is that the reader can see what they are pointed at.**

R2-01's own suggestion was to rewrite the check with the account's data interpolated — *"NVIDIA added 5,000 people and 500 open roles in 38 days; which functions?"* **Rejected.** It would put the product in the business of editing a domain expert's reviewed sentence, and the catalog would need placeholders whose correctness nobody could review independently of the data. **The evidence goes beside the check instead of inside it.**

### What arrives on the wire

Each hypothesis gains `observed` — the recorded business events it cites, carrying **the Business Event Engine's own summary, unedited**, and **the same `business_event_id` the score's ledger already cites**.

**One citation, one drawer, one wording.** A second phrasing of one fact is how a customer catches a product contradicting itself, and a second citation concept would be a second thing to learn for no gain.

### Two reads, not one per hypothesis

Every signal about an account cites events belonging to that account, so `live_with_evidence` fetches signals once and events once and pairs them in memory. A per-signal join would make a four-hypothesis page cost five queries to answer one question.

**Order is `contributing_event_ids` order** — the order the pipeline recorded — so the same account renders identically twice. Insertion order is not a fact about a company.

**A cited event that no longer resolves is skipped, never faked.** A signal cannot be constructed citing nothing, so an empty list means the events were removed underneath it, and the surface renders that as absence.

## What the tests had to work around, and why it is recorded

**The baseline scenario's evidence is months old on purpose**, so every hypothesis it forms is past its shelf life and this surface — which shows *live* hypotheses only — correctly returns nothing. That is the lifecycle working and is asserted in its own right above.

The integration tests therefore ingest at a recent epoch, **the same way the Playground seeder does** — same code path, same scenario file, only the clock differs.

**One test uses the twelve-account `playground@2` cast**, because the two-account baseline holds each hypothesis exactly once and the central R2-01 assertion — *two accounts sharing a hypothesis get identical checks and different evidence* — would otherwise **skip**. A test that skips is a claim nobody checked. Only that one test pays the cost.

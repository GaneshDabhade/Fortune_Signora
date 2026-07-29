# 25 — Signal Engine

> Status: **PROPOSAL — awaiting review** · 2026-07-29
> Audience: All engineers, EMs, and technical stakeholders at Signora
> Revision: **v1** — the M5A architecture proposal. **No implementation exists.**
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

## Questions for review

1. **Is the global-catalog / per-workspace-profile split right?** Everything rests on it. In particular: is *"a workspace can never invent a signal type"* the right constraint, given it trades flexibility for cross-customer reasoning?
2. **Approve the profile living in versioned database rows** while the business event taxonomy stays a repository artifact — on the grounds that ownership, not convenience, decides?
3. **Approve composite signals in v1** (Option C), accepting the overlap with atomic ones and the deduplication requirement it places on M5B?
4. **Approve removing `signal.scored`** and dropping `score` from `signal.generated`, since the Signal Engine produces no scores?
5. **Are nine catalog types the right v1**, and does each pass the CRO test as a *hypothesis* — phrased as a possibility rather than a fact?
6. **Is `relevant_until` the right shape for shelf life** — a derived date on the signal — rather than leaving recency entirely to M5B?

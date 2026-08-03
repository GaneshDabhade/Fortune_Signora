# ADR-0200: Sales Engagement — the module that owns commercial synthesis

## Status

**PROPOSED — 2026-08-03, by Lane A, assigned Sales Engagement Intelligence.**

Drafted after the discovery in [50-sales-engagement.md](../50-sales-engagement.md) found that the assignment's central noun — a person — does not exist in the platform, and that eight of its eleven questions are answerable without one. The product owner refined the direction the same day and **approved a dedicated bounded context**, with this ADR to define it.

**Two decisions are deliberately left open** and marked ❓. Both are the product owner's.

## Context

**Sixteen modules exist. Every one of them owns facts.**

| | |
|---|---|
| Knowledge Graph | what a company *is* |
| Provider Normalization | what a provider *said* |
| Observation Engine | what *changed* |
| Business Event Engine | what *happened* |
| Signal Engine | what it might *mean* |
| Buying Score Engine | how much it *matters* |
| Commercial Profile | what the customer *sells*, to *whom*, and who has to *agree* |
| Opportunity Engine | what the *state of the work* is |
| Timeline | what has *happened*, in order |
| AI Reasoning Engine | prose *about* an account, beside its evidence |

**Nothing owns the synthesis.** Every fact needed to tell a seller *which role to approach, why, why now, what to ask and what Signora still does not know* is already recorded — in six different modules, none of which may read the others, and none of which is permitted to draw a commercial conclusion from the combination.

**The discovery found the join concretely.** Commercial Profile holds *"for Revenue Cloud my champion is the VP of Engineering"*. Business Event Engine holds *"they appointed a new VP of Engineering three weeks ago"*. **Nothing joins them**, and the buying committee's own docstring records the consequence: *"nothing downstream reads it yet."*

## Decision

### The boundary, in one line

> **Sales Engagement owns commercial synthesis. It composes facts other modules own into a conclusion about how to approach an account, and it owns no fact of its own.**

Every module upstream has already made *its* judgement. This one is the first that is allowed to make a judgement **about the combination** — and it is the only one that will be.

### It owns reasoning, not data

| | |
|---|---|
| **Owns** | The reasoning graph · role ranking · unknowns · risks · questions · the AI synthesis contract · the seller's disagreement with a recommendation |
| **Stores** | **Only what cannot be recomputed**: a seller's override, a seller's disagreement, and materialized AI syntheses (which are historical facts, `CLAUDE.md` §2) |
| **Never owns** | Companies · people · claims · observations · events · signals · scores · declarations · workflow · the timeline |
| **Never stores** | A ranking · a confidence · an inferred product · an unknown · a risk. **Every one is derived at read time**, the same rule `evidence_state` follows |

**The property that keeps it honest, stated as a test:** *drop everything this module stores except overrides and syntheses, and every recommendation it makes is reproduced byte for byte.*

### Deterministic reasoning and AI synthesis are separate layers, and the separation is structural

**This is the ADR's most important decision.**

```
  ┌── Layer 1 · the reasoning graph ─── DETERMINISTIC ──────────────┐
  │  committee ⨯ business events ⨯ signals ⨯ validation ⨯ score     │
  │  → ranked roles, with the evidence that ranked each             │
  │  → unknowns, as absences in the evidence                        │
  │  → risks, as contradictions and thin corroboration              │
  │  → questions, from what validation says is unproven             │
  │  **Reproducible. Testable against fakes. No model is called.**  │
  └─────────────────────────────┬───────────────────────────────────┘
                                │  a closed, cited evidence set
  ┌─────────────────────────────▼─── AI ────────────────────────────┐
  │  Layer 2 · synthesis                                            │
  │  Reads the graph's output and nothing else. Writes prose a      │
  │  seller consumes in seconds.                                    │
  │  **It may not add a fact, a role, a risk or an unknown that     │
  │  layer 1 did not produce.**                                     │
  └─────────────────────────────────────────────────────────────────┘
```

**Why the split is structural rather than a convention:** layer 2's input is a **closed set** — the same rule the evidence digest follows. A synthesis naming a role the graph did not rank, or a risk it did not find, **fails validation and is refused**, exactly as a citation to evidence outside the set is refused today.

**And layer 1 must never call a model.** *If the system already knows something deterministically, never ask a model to invent it again* (`CLAUDE.md` §2). A title matching a declared role is a string comparison; a contradiction between two providers is a set difference. **Both are known.**

> **The reasoning graph is the product. The synthesis is how it is read.** Delete the synthesis and a seller still gets ranked roles with evidence; delete the graph and there is nothing to synthesise.

### Every conclusion is derived and citable, or it is not shown

| Output | Derived from | Never |
|---|---|---|
| **Ranked role** | A declared committee role whose title is named by an observed event | Stored, scored numerically, or inferred by a model |
| **Confidence** | Corroborating providers · recency · directness · contest | **A percentage.** Banded words, as `MatchStrength` and revenue bands already are |
| **Unknown** | An **absence** in the evidence set — a committee part with no supporting event, an attribute no provider reported | Invented by a model |
| **Risk** | A contradiction between providers, a single-source claim, an inference from a weak link | A confidence figure wearing different words |
| **Question** | What `AccountValidation` records as **asserted and unproven** | A generated conversation starter |
| **Likely product** | ICP match · signal alignment · intent · research, **and always overridable** | Certain |

### Person Intelligence is designed for and not built

**The reasoning operates entirely on roles.** A role is a job title in the customer's own words, and it is not personal data.

**The architecture must not make people impossible**, and it does not: a ranked role is a *slot*, and a person — if [C-210](../../LANE_COORDINATION.md) is ever answered — **fills a slot without changing the graph that produced it.** No ranking, no evidence, no question and no risk changes shape when a name arrives.

**Until then no person is named, no person is stored, and no person reaches a prompt.**

### Relationships to every module it reads

**Conformist to all of them**, and it publishes nothing they consume. Reads through `public/` only, exactly as the AI engines already read the Opportunity Engine.

| Reads | For |
|---|---|
| `commercial_profile.public` | The committee, the portfolio, the ICP |
| `signal_engine.public` · `business_event_engine.public` | What might be true, and what happened |
| `buying_score_engine.public` | Why now, and how much |
| `opportunity_engine.public` | Which accounts, and who holds them |
| `ai_platform.public` | The synthesis, through the provider port and never a vendor SDK |

**⚠️ This is a new node reading five modules, which is the largest single addition to the dependency graph since M1.** It is justified only because the composition *is* the capability — and it is one-directional: **nothing reads Sales Engagement except the API layer.**

### What it publishes

**One event, and only when a human acts:** `sales_engagement.recommendation_rejected`, carrying the role, the reason and the actor. **Nothing else** — a derived conclusion is not news, and publishing one would invite a consumer to store it.

## Consequences

**Good.** The committee gets its first consumer. Every existing capability gains a purpose it did not have. No pipeline stage is duplicated. AI is confined to a layer whose input is closed and whose output is checkable. People can be added later without redesign.

**Costly.** A sixteenth module with five inbound edges. A second place (after AI Reasoning) where prose is generated. A reasoning graph that must be re-derived on every read — **acceptable, because it is composition over already-cached reads, and cheaper than a stored ranking that would go stale.**

**Refused alternatives.** Extending the Opportunity Engine — its own ownership contract forbids it ([49](../49-lead-ownership.md) §19) and its import contract forbids reaching the Signal Engine. A composition in the API layer — commercial reasoning with no owner, no tests and no boundary. Extending AI Reasoning Engine — it would put deterministic work behind a model.

## Open questions

**❓ Q-1 — does a rejected recommendation change future ranking?** A seller saying *"the VP Engineering is not my champion here"* is the only feedback this module will ever get. Learning from it makes the ranking non-reproducible from evidence alone. **Recommendation: record it, show it, and do not learn from it yet.**

**❓ Q-2 — is the synthesis materialized or generated per read?** Materialized is auditable and immutable (`CLAUDE.md` §2) and goes stale as evidence moves; per-read is always current and unciteable. **Recommendation: materialized, superseded when the evidence set changes** — the same rule narration follows.

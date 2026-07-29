# 22 — Knowledge Graph

> Status: **Architecture proposal — awaiting review**
> Audience: All engineers, EMs, and technical stakeholders at Signora
> Revision: **v1** — the M3A architecture proposal. **No implementation exists.**
>
> Prerequisite reading: [11-tenancy.md](11-tenancy.md), and the Claim model in `modules/provider_normalization/domain/claim.py`.

---

## The transition this module represents

Everything built so far has deliberately avoided deciding anything.

Provider Platform preserved raw payloads. Provider Normalization preserved evidence — it translates and never interprets, and we removed the confidence field precisely because normalization has no authority to estimate one.

**The Knowledge Graph is the first module that must decide.** Apollo's `acme-corp` and BuiltWith's `acme.example` either are the same company or they are not. No amount of deferral avoids that; the entire pipeline downstream is meaningless until something answers it.

That makes this the module where the platform's philosophy is genuinely tested. It is easy to preserve evidence when you never have to conclude anything.

---

## The central question, examined

> **Where should conflicting evidence be resolved?**

Apollo reports 120 employees. CoreSignal reports 145. Both claims are true statements about what a provider asserted. Something must eventually decide what to show a seller — but *where*?

### Four candidate architectures

**A — The graph resolves everything.** Store resolved entities carrying resolved attribute values. One company, one headcount.

*Rejected.* Disagreement dies at the earliest possible moment. AI Reasoning can never say *"confidence is lower because sources disagree"* — one of the six questions customers are buying answers to. Worse, the Observation Engine loses its input: change is only visible across a series, and a collapsed current value has no series. It would have to diff successive collapses, losing which provider drove the change. This is the design that makes the product ordinary.

**B — The graph resolves identity only; claims stay untouched.** Entities and edges, nothing else. Consumers query claims by resolved entity.

*Rejected, narrowly.* It preserves everything, which is right. But it gives downstream no coherent surface: "what is Acme's headcount?" has no answer, only a set of claims. Every consumer writes its own interpretation, and within three milestones that logic is duplicated in four modules and diverges. Preserving evidence is not the same as refusing to organise it.

**C — The graph resolves identity and exposes *claim sets*, never collapsed values.** Entity = identity + relationships. Plus a query surface returning, for `(entity, attribute)`, all contributing claims with their sources and times — a **set**, deliberately not a value.

**Recommended.** The graph adds *knowledge* (these claims describe the same company) without destroying *evidence* (they disagree, and here is exactly how). Downstream modules receive an organised, entity-scoped view and each decides what it needs: the Observation Engine sees the series, the Buying Score Engine can weigh sources, AI Reasoning can cite the disagreement.

**D — Graph plus a stored "resolved value" projection**, with links back to contributing claims and a recorded resolution rule.

*Rejected for M3A, and worth stating why carefully.* It is defensible — fast reads, explainable, recomputable. But it puts a collapsed value in the schema before any module has asked for one, and a stored value becomes the de facto truth: within a year, consumers read the projection and nobody reads the claims. That is Option A arriving by the back door. **If a downstream module later demonstrates it needs a resolved value, adding this projection is straightforward and by then we will know the rule it should use.** Building it now means inventing the rule with no consumer to validate it.

### The recommendation

> **The graph decides identity. The graph never decides truth.**

Identity is irreducible — the graph is the only module positioned to answer it. Attribute conflict is *not* irreducible: it can be carried forward intact, and every downstream module has more context to weigh it than the graph does.

This split is the same discipline as M2.2, applied one layer up: **decide only what cannot be deferred.**

---

## Domain model

Five concepts. Deliberately few, and each earning its place.

### `Entity`

A canonical thing in the business world, with a stable identifier and a kind.

```
Entity(id, workspace_id, kind, created_at)
```

**Carries no attribute values.** An entity is an *identity*, not a record. Its name, headcount, and industry live in claims; giving the entity a `name` column would be Option A in miniature, and the column would immediately disagree with the claims underneath it.

**Kinds in M3A:** `COMPANY`, `TECHNOLOGY`. Person is deferred — see below.

### `IdentityBinding`

Links a provider's `SubjectHint` to an `Entity`.

```
IdentityBinding(id, workspace_id, entity_id, provider, provider_external_id,
                decision_id, superseded_by, created_at)
```

This is the answer to *"is Apollo's `acme-corp` the same as BuiltWith's `acme.example`?"* — one binding per provider identity, all pointing at one entity when they resolve together.

### `ResolutionDecision`

**Why a binding exists.** Immutable, superseded rather than edited — the same pattern as claims, for the same reason.

```
ResolutionDecision(id, workspace_id, rule, matched_on, candidate_entity_ids,
                   outcome, evidence_claim_ids, superseded_by, decided_at)
```

`outcome ∈ {BOUND, CREATED, AMBIGUOUS}`. `matched_on` records the actual matched value (`domain=acme.example`), so an engineer reading the decision months later sees *what* matched, not just that something did.

This is what makes the module's decisions **explainable, revisable, and auditable**:

- **Explainable** — the decision names its rule and its matched evidence.
- **Revisable** — a wrong merge is corrected by a *new* decision superseding the old. Nothing is mutated, and the claims underneath are untouched.
- **Auditable** — the full history of what was believed, when, and why survives. This is what an enterprise audit or a customer evidence export actually needs.

### `Relationship`

An edge between entities, derived from claims and citing them.

```
Relationship(id, workspace_id, kind, source_entity_id, target_entity_id,
             valid_from, valid_to, evidence_claim_ids, superseded_by)
```

**Kinds in M3A:** `USES_TECHNOLOGY`. Nothing else is derivable from the current claim vocabulary without inventing meaning.

`valid_to` is what makes a *removal* first-class: `TECHNOLOGY_REMOVED` ends a relationship rather than deleting it. The history of what a company used and stopped using is exactly what a competitive-displacement signal reads.

### `ClaimSet`

Not a stored table — the **query surface**. For `(entity, attribute)`, returns every contributing claim with its provider, value, `observed_at`, and provenance.

```
ClaimSet(entity_id, attribute, claims[], providers[], agrees: bool)
```

`agrees` is computed, not stored, and is the one derived signal the graph offers — because "do sources agree?" is a question about *identity resolution having grouped them*, which is the graph's own job.

---

## Identity resolution strategy

### Deterministic rules only

No fuzzy or probabilistic matching in M3A. A similarity threshold is a hidden heuristic — a magic number nobody can justify that four modules will trust within a year. The philosophy says prefer deterministic behaviour, and identity is the worst possible place to start guessing.

Rules, in precedence order:

| # | Rule | Matches on |
|---|---|---|
| 1 | `SAME_PROVIDER_ID` | Same provider + same `provider_external_id` |
| 2 | `EXACT_DOMAIN` | Normalized domain equality (lowercased, `www.` stripped) |
| 3 | `EXACT_LEGAL_NAME_AND_COUNTRY` | Both present and exactly equal |

A hint matching no rule **creates a new entity**. That is a normal outcome, not a failure.

### The asymmetry that shapes everything

**Under-merging and over-merging are not equally bad.**

- *Under-merge* → two entities for one company. Visible in the UI, reported by a user, fixable by a new decision. Annoying.
- *Over-merge* → two companies become one. One customer's intelligence contaminates another's. **Invisible** — the data looks clean — and it silently corrupts every downstream signal, score, and recommendation.

Therefore: **when two candidate entities both match, do not merge.** Record an `AMBIGUOUS` decision naming both candidates and leave them separate. An unresolved ambiguity is a queue item; a wrong merge is a trust incident.

### Determinism

Given the same claims processed in any order, resolution must reach the same entity structure. Achieved by making rules order-independent: a binding is decided by evaluating rules against *all* existing bindings, not against processing history. Asserted by a test that shuffles claim order and compares the resulting graph.

---

## Evidence attachment

Every entity, binding, relationship, and decision cites the claims that produced it. Traversal in both directions must work:

- **Entity → evidence:** *"Why do we believe this?"* — the export an enterprise customer asks for.
- **Claim → conclusions:** *"What did this depend on?"* — what makes a corrected mapper's blast radius knowable.

The chain is now: **raw record → claim → decision → entity → (downstream)**. No link may be weakened.

---

## Storage model

Single PostgreSQL, per the ratified architecture. Four workspace-owned tables — `entity`, `identity_binding`, `resolution_decision`, `relationship` — each with forced RLS and full policies **in the migration that creates them**, registered in `tenancy_policy.py`.

**`resolution_decision` is immutable** (`IMMUTABLE_TENANT_TABLES`, no `UPDATE` grant), for the same reason claims are: a decision that can be edited is a decision whose history cannot be trusted.

`identity_binding` and `relationship` carry `superseded_by` and are also insert-only in practice; supersession is a new row, and the current state is `WHERE superseded_by IS NULL`.

**On scale.** Claims are the large table — billions, eventually. The graph is small: entities ≈ companies, bindings ≈ providers × companies. Postgres handles this comfortably at the scales in view, and partitioning claims by workspace and time is available later without touching the graph. **No graph database.** Introducing one would add an operational component, a second consistency model, and a second query language to serve a dataset that fits comfortably in the database we already run — and Principle 6 (single datastore) exists precisely to prevent that trade being made casually.

---

## Event model

| Event | When | Payload |
|---|---|---|
| `entity.created` | A hint matched no existing entity | `entity_id`, `kind`, `decision_id` |
| `entity.identity_bound` | A provider identity resolved to an entity | `entity_id`, `provider`, `decision_id` |
| `entity.resolution_ambiguous` | Two candidates matched; nothing merged | `candidate_entity_ids`, `decision_id` |
| `entity.superseded` | A resolution was corrected | `entity_id`, `superseded_by`, `decision_id` |
| `relationship.established` | An edge began | `relationship_id`, `kind`, `source`, `target` |
| `relationship.ended` | An edge closed (`valid_to` set) | `relationship_id`, `valid_to` |

`entity.resolution_ambiguous` is a **first-class event, not a log line** — it is a work queue and an operational signal that a provider's identity data has degraded.

---

## Module API

Exposed through `public/`; no other module reaches deeper.

```
resolve_entity(workspace_id, hint) -> Entity
claim_set(workspace_id, entity_id, attribute) -> ClaimSet
entity_evidence(workspace_id, entity_id) -> list[Claim]
relationships(workspace_id, entity_id, kind=None, as_of=None) -> list[Relationship]
resolution_history(workspace_id, entity_id) -> list[ResolutionDecision]
```

`as_of` on `relationships` is the seam for historical replay. Adding it now costs nothing; retrofitting a temporal query onto a non-temporal API costs a rewrite of every caller.

---

## Deferred, with reasons

| Deferred | Why |
|---|---|
| **Person entities** | Claims carry `ROLE_CHANGE` with title and seniority but **no person identifier**. There is no identity to resolve. Adding people now means inventing one. Revisit when a provider supplies person identity. |
| **Fuzzy / probabilistic matching** | A hidden heuristic. Deterministic rules first; if they under-merge materially, that will be visible in `entity.resolution_ambiguous` volume and in duplicate entities — evidence, rather than speculation, will justify it. |
| **Resolved-value projection** (Option D) | No consumer has asked for one. Adding it later is straightforward; adding it now means inventing a rule with nothing to validate it against. |
| **Manual merge/unmerge UI** | The domain supports it (supersession). The interface belongs with the business UI in M12. |
| **Cross-workspace resolution** | Never. Entities are workspace-owned; resolution across tenants would be a tenancy breach, not a feature. |

---

## Task breakdown — T59–T66 · ~9–12 ew

| ID | Task | Complexity | Depends on |
|---|---|---|---|
| **T59** | Domain: `Entity`, `IdentityBinding`, `ResolutionDecision`, `Relationship` | M · 1.5 ew | — |
| **T60** | Resolution rules + the deterministic rule engine | L · 2 ew | T59 |
| **T61** | Schema + migration 0009 — four tables, forced RLS, `resolution_decision` immutable | M · 1.5 ew | T59 |
| **T62** | `ResolveEntity` use case — binding, creation, ambiguity, supersession | L · 2 ew | T60, T61 |
| **T63** | Relationship derivation from technographic claims | M · 1.5 ew | T62 |
| **T64** | `ClaimSet` query surface + module `public/` API | M · 1.5 ew | T62 |
| **T65** | Event contracts + subscription from `claim.recorded` | S · 1 ew | T62 |
| **T66** | Demonstration + smoke stage + Security Invariants | M · 1 ew | all |

**Order:** T59 → T61 → T60 → T62 → T63 → T64 → T65 → T66

Domain before schema so the table follows the model. T60 after T61 because the rule engine is easier to test against real storage than against a fake, and the rules are the part most likely to change under review.

**Dependencies.** Inbound: M2.2 (claims), M1.1 (event bus, idempotency), M0 (RLS). Outbound: blocks M3B and everything after. External: none.

---

## Acceptance criteria

| ID | Criterion |
|---|---|
| **AC-25** | **Explainable resolution** — every binding traces to a decision naming its rule and matched value; `resolution_history` returns the full chain |
| **AC-26** | **Revisable without evidence loss** — a corrected resolution supersedes rather than mutates; the claims underneath are untouched and the prior decision remains readable |
| **AC-27** | **Deterministic resolution** — the same claims in any order produce the same graph, asserted by shuffling |
| **AC-28** | **Evidence preserved, not collapsed** — conflicting claims for one `(entity, attribute)` are both retrievable; the graph stores no resolved attribute value |
| **AC-29** | **Bias against over-merge** — two matching candidates produce `AMBIGUOUS` and no merge |
| **AC-6** | Tenancy — four new tables, forced RLS, full policies, registered in the policy |
| **AC-1** | Event contract — cataloged, idempotent, correlation-traced |

---

## Demonstration scenario

> *"Five providers, one company, and the disagreement survives."*
>
> Run the ERP Replacement scenario. Apollo, BuiltWith, CoreSignal, Crunchbase, and Bombora each report on Acme under different identifiers. The graph resolves all five to **one entity** — and `resolution_history` shows exactly why each bound: `EXACT_DOMAIN` on `acme.example` for three, `SAME_PROVIDER_ID` for the rest.
>
> Apollo says 120 employees; CoreSignal says 145. `claim_set(acme, EMPLOYEE_COUNT)` returns **both**, with providers and timestamps, and `agrees = False`. Nothing was picked. Nothing was lost.
>
> BuiltWith reports the legacy ERP removed: the `USES_TECHNOLOGY` relationship gains a `valid_to` rather than disappearing, and `relationships(as_of=<January>)` still shows it live.
>
> Then introduce a second company sharing a legal name in a different country. The graph records `AMBIGUOUS`, merges nothing, and emits the event.
>
> Finally, shuffle the claim processing order and rebuild: byte-identical graph.

---

## Definition of Done

- [ ] Demonstration passes; AC-25 through AC-29, AC-6, AC-1 all passed
- [ ] Migration 0009 with RLS in the same revision; tables registered in `tenancy_policy.py`
- [ ] `resolution_decision` added to `IMMUTABLE_TENANT_TABLES`, with the no-`UPDATE` grant asserted
- [ ] Security Invariants extended; each addition **proven to fail** when its guarantee is removed
- [ ] `04-modules.md` and `06-events.md` updated in the same change
- [ ] `make smoke` extended with a resolution stage, green against fresh images
- [ ] PROJECT_STATUS and SESSION_HANDOFF updated at the boundary
- [ ] **"The Intelligence Pipeline"** (`21-intelligence-pipeline.md`) authored — this milestone is its trigger

---

## Rollback strategy

**Schema:** additive — four new tables; downgrade drops them. **Data:** the graph is *derived*. It can be dropped and rebuilt from claims, which is the rollback for a bad resolution rule — and the reason claims are stored rather than streamed. **Application:** previous image tag. **Blast radius:** one workspace. A bad rule produces wrong entities in that workspace only, correctable by rebuild.

---

## Operational readiness

- [ ] Alert: `entity.resolution_ambiguous` rate — the leading indicator of degrading provider identity data
- [ ] Alert: entity creation rate diverging from claim rate — the signature of a broken rule creating an entity per claim
- [ ] Metrics: bindings per entity, resolution latency, supersession rate, relationship churn
- [ ] Runbook: investigating an ambiguity, correcting a wrong merge, rebuilding the graph from claims
- [ ] `correlation_id` traceable from raw record through claim, decision, and entity

---

## Risks and mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| **Over-merge contaminates a customer's intelligence** | 🔴 High | Deterministic rules only; ambiguity never merges; supersession makes correction non-destructive; alert on ambiguity rate |
| **Fixture-derived identity hints are unrealistically clean** | 🟠 Medium | Real provider data is messier — inconsistent domains, trailing whitespace, subsidiaries. The rules will likely need extension when authentic payloads arrive. **Normalization of the matched value is centralised in one function** so that extension is one place. |
| **Determinism breaks under concurrency** | 🟠 Medium | Two workers resolving the same hint could create two entities. Mitigated by a unique constraint on `(workspace_id, provider, provider_external_id)` — the database, not the application, prevents it |
| **The graph quietly becomes a database** | 🟡 Low | AC-28 forbids stored attribute values; asserted structurally |
| **Downstream reimplements conflict resolution** | 🟡 Low | `ClaimSet` gives them a shared surface. Watch for duplication in M3B/M5B; if it appears, that is the evidence justifying Option D |

---

## Questions for review

1. **Is the identity/truth split right?** Everything above rests on it. If the graph *should* resolve attribute conflict, this design is wrong at its root and better rejected now.
2. **Should `AMBIGUOUS` block downstream processing for that entity, or proceed with the unmerged entities?** I lean toward proceeding — a partially-resolved company is more useful than none, and the ambiguity is visible — but it means downstream may briefly see two entities for one company.
3. **Is deferring people acceptable for M3A?** It scopes the milestone honestly, but the Timeline (M7) and role-change signals will eventually want person identity, and adding an entity kind later is cheaper than adding it wrongly now.

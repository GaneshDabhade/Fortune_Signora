# 22 — Knowledge Graph

> Status: **IMPLEMENTED** — M3A, 2026-07-29
> Audience: All engineers, EMs, and technical stakeholders at Signora
> Revision: **v2** — the design as built. Four departures from the v1 proposal are recorded in *[As built](#as-built-what-changed-during-implementation)*; everything else stands as approved.
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

### The recommendation — **now a permanent invariant**

> **The Knowledge Graph resolves identity. The Knowledge Graph does not resolve truth.**
>
> Ratified 2026-07-28. Identity and truth are different problems. Identity belongs to the graph; truth belongs to downstream modules that possess additional context. **Changing this requires an RFC.**

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
ResolutionDecision(id, workspace_id, provider, provider_external_id, outcome,
                   reasons, entity_id, candidate_entity_ids,
                   evidence_claim_ids, decided_at, supersedes)
```

**The supersession pointer points backwards, and immutability forces that.** A forward `superseded_by` would have to be written onto the *older* row, which needs an `UPDATE` grant this table deliberately does not have. A correction is therefore a new row naming its predecessor, and the current decision is the one no other decision names.

### `IdentityState` — explicit, not inferred

A binding carries its resolution state rather than downstream inferring it from decision history:

| State | Meaning | What downstream should do |
|---|---|---|
| `IDENTIFIED` | Bound to exactly one entity by a matching rule | Use it |
| `AMBIGUOUS` | Two or more candidates matched; **nothing merged** | Proceed, but the entity may be one of several — a score built on it is provisional |
| `UNRESOLVED` | No rule matched and no entity created yet | Ignore until resolved |

Making this explicit means each downstream module *decides* how to treat each state, rather than silently treating everything as identified. That decision becomes reviewable.

### `MatchStrength` — a property of the rule, not of the decision

Rules genuinely differ in reliability, and downstream should be able to weigh that. But a computed confidence *number* per decision is the trap avoided in M2.2: if it is a pure function of the rule, it adds no information, and the moment the field exists there is constant pressure to make it "smarter" by combining rules or weighting providers. That is how a hidden heuristic is born.

So strength is **declared once per rule**, denormalized onto the decision at decision time so the audit record is self-describing:

| Strength | Rule | Why |
|---|---|---|
| `CERTAIN` | `SAME_PROVIDER_ID` | The provider's own key. It cannot be wrong about its own identifiers. |
| `STRONG` | `EXACT_DOMAIN` | Very reliable, not certain — subsidiaries and agencies share domains. |
| `MODERATE` | `LEGAL_NAME_AND_COUNTRY` | Two unrelated "Acme Ltd" in one country is a real scenario. |

**Never computed. Never combined. Never probabilistic.** It is named `MatchStrength` rather than `confidence` deliberately: "confidence" invites probabilistic thinking, and this is a statement about how strong a match was, not a belief about the world.

> **Permanent invariant, ratified 2026-07-29.** `MatchStrength` is a semantic category. It must never become a numeric score, never participate in a weighted calculation, and never become the basis of heuristic identity resolution. The two doors into that drift are numeric conversion and ordering comparison, so **the type itself closes both**: `int()`, `float()`, and every ordering operator raise `TypeError`. A future engineer cannot convert it into probabilistic scoring by accident. Asserted structurally in the Security Invariants suite, including that no graph table carries a column named like a score, weight, confidence, probability, or rank.

A decision is made by **exactly one rule** — the engine stops at the first rule that matches anything — so every reason on it shares one strength and there is nothing to combine. `ResolutionDecision.strength` states that as an invariant and raises if it is ever violated, rather than quietly reducing with `min`/`max`: a reduction would be the seam through which "two moderate matches make a strong one" eventually arrives.

If a rule's declared strength is later revised, that is a **new decision superseding the old** — the mechanism already exists.

### `ResolutionReason` — what actually matched

`outcome ∈ {BOUND, CREATED, AMBIGUOUS}`. Each decision carries one or more reasons, each naming the rule, the field, and the **actual value** that matched:

```
ResolutionReason(rule=EXACT_DOMAIN, field="domain", value="acme.example", strength=STRONG)
```

An engineer or an auditor reading this months later sees *what* matched, not just that something did. Future explainability depends entirely on these surviving.

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
identities(workspace_id, entity_ids) -> dict[UUID, AccountIdentity]
find_accounts(workspace_id, text, limit) -> tuple[AccountMatch, ...]
relationships(workspace_id, entity_id, kind=None, as_of=None) -> list[Relationship]
resolution_history(workspace_id, entity_id) -> list[ResolutionDecision]
```

`as_of` on `relationships` is the seam for historical replay. Adding it now costs nothing; retrofitting a temporal query onto a non-temporal API costs a rewrite of every caller.

### `find_accounts` — searching by name, and why it searches names nobody displays

**Added 2026-08-03 by Epic A slice A1.** `GET /workspaces/{id}/account-search?q=&limit=`.

**Three steps, and none is a join across a module boundary.** Provider Normalization finds the identities whose `LEGAL_NAME` claim matched (`ClaimReader.subjects_named_like`) · this module maps those to accounts through its own bindings (`entities_for_subjects`) · `identities()` resolves each account's displayed name.

**It matches every name a source has ever claimed, not the displayed one.** Matching only the displayed name would require resolving every account in the workspace before knowing which to keep — and it would be worse product: **a company that renamed is found under its old name and shown under its new one**, which is what a seller who has not heard about the rename types.

**Two consequences to preserve, both asserted:**

| | |
|---|---|
| **A result may not contain the search text** | The customer typed a former name. **The list must never highlight a matched substring** — highlighting promises the match is in the visible text, and sometimes it is not. **Explainability arrived as this section predicted**, below: the row *states* the matched name instead of decorating the text |
| **A blank query returns nothing** | An empty pattern matches every claim in the workspace. The guard is in `find_accounts` rather than only in the browser, so every future caller inherits it |

**`identity_binding.legal_name` is not the searchable text, and it looks like it should be.** It is a resolution hint frozen at binding time (`resolve.py` takes the first non-null `subject_legal_name`), and claims recorded afterwards never update it. **Searching it would return accounts under a name the product does not display** — the two-representations defect (§2) presenting as a search with the wrong labels.

**The bound is on identities considered, not accounts returned.** Several providers naming one company are several matches, so a workspace where one account has many sources can return fewer than `limit` accounts while more exist. A known limitation rather than a hidden one: collapsing in the database would need the cross-module join this deliberately does not have.

**Wildcards are escaped.** `_` and `%` are `LIKE` syntax; unescaped, a customer searching for a name containing `%` receives their entire book of business and it looks like the search working.

### `AccountMatch` — what kind of thing it is, and why it is here

**Added 2026-08-04 by [TASK-301](../BACKLOG.md), from Lane C's [417 §4 slice B-i](417-executable-slice-audit.md).** `find_accounts` returns `AccountMatch` rather than `AccountIdentity`: the account, its `kind`, the `matched_name`, the `matched_source`, and `is_renamed`.

**This is the explainability the section above said to build, built the way it said to build it.** The surface refused to highlight because *"the match is sometimes not in the text"* — an honest refusal that left a customer with an unexplained row. **Stating the matched name replaces a refusal with a disclosure**, and `is_renamed` is what keeps it readable: only a row whose match is invisible in its own text is annotated, because a list that explains every row is one people stop reading.

**The matched name cost nothing to obtain and was being discarded.** `SqlClaimReader.subjects_named_like` already selected it — it is what `ORDER BY` sorts on — and dropped it one line later. `ClaimReader` now returns `NameMatch(subject, name)`, which is a 🟠 change to Provider Normalization's published contract with one consumer.

| | |
|---|---|
| **`kind` is read from the entity, never assumed from the endpoint** | A caller grouping results by type must be told the type. Inferring it from *which URL was called* breaks the first time one URL answers for two kinds, and puts this module's vocabulary in a caller's hands. `entities_for_subjects` therefore returns `ResolvedSubject` — which identity resolved to which entity, **and what kind that entity is** — joined in the one query rather than read in a second pass |
| **Which identity explains the row is the first one, not the last** | Two of a company's providers can both match one search. The ranking is by matched name, so the **earlier** is the better match; collapsing to the later would show the worse match as the reason the row is there |
| **There is no relevance score, and nowhere to put one** | The order is the matched name, ascending — derivable, repeatable, and now *readable off the results*, because the field it sorted on is on every row. **That is what makes the ranking explicable**; a number would make it neither. Same door `MatchStrength` closes in resolution (§2) |
| **An absent type is absent, never an empty group** | Signora searches companies. **An empty `people: []` would claim it looked and found nothing**, which is a different statement and a false one — so the response is a flat, typed list and a caller groups by `result_type` |

**The grouped *rendering* is not built, deliberately, and this is the slice's stated limitation.** Only one type is reachable by this search: technology entities are created by `find_or_create_canonical_entity` and hold no provider binding, so they never resolve through `entities_for_subjects` in practice. **A grouping branch no production data can enter is Decorative Logic** (§2) — the contract carries the type so the approved Global Search screen can group, and the shell's typeahead renders the one group that exists. **The second group arrives with the second searchable type, and Global Search's screen is Product Surface's.**

### `AccountIdentity.last_observed_at` — how current the account's evidence is

**Added 2026-08-03 by Epic A slice A4.** The newest `observed_at` across **every** claim bound to the entity, from `ClaimReader.latest_observed_at`. Derived on every request; nothing is stored.

**Why it is on this read model rather than a new one.** The join it needs — entity → bindings → claims — is the one `identities()` already performs, and the account brief already calls the endpoint that returns it. **No new endpoint, no new request, no new module dependency, no new table.**

**Why it belongs to this module at all.** *"How current is what we know about this account?"* is a question about **claims grouped by entity**, and grouping claims by entity is this module's whole job. The Opportunity Engine holds the brief but reaches only Buying Score (`05-module-dependencies.md`); composing it there would have needed a new ratified edge to answer a question that was never the workflow's.

**What it is not, and this must not drift.** It is **not** *"when Signora last looked"*. Nothing in the repository records that per account: `provider_sync` carries no subject, and `provider_watermark.position` advances only when records arrive — so an account a provider checked and found nothing about is indistinguishable from one it never checked. **Closing that gap is a Provider Platform slice**, and until it exists the product says *observed*, never *checked*.

**The one deliberate cost.** A second query per page of accounts, aggregate and grouped, rather than widening `for_subjects` to every attribute — which would fetch every claim about fifty companies to keep fifty timestamps.

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

## Demonstration scenario — as built

> *"Five providers, one company where the evidence allows it, and the disagreement survives."*
>
> Run the baseline scenario through all five providers. **Apollo, BuiltWith, and Bombora resolve to one entity** — each states `acme.example`, and `resolution_history` shows exactly why: `EXACT_DOMAIN` on `acme.example`, with the matched value recorded, not merely the rule.
>
> **Crunchbase and CoreSignal stay separate, and that is the correct answer.** Neither fixture payload carries a domain, and their only shared token with Apollo is the subject key — which is the *simulator's* naming, not a cross-provider identifier. Binding on it would mean treating one provider's private key as another's, which in production is precisely the over-merge this module exists to refuse. An under-merge is a visible duplicate; an over-merge silently mixes two customers' intelligence.
>
> `claim_set(acme, EMPLOYEE_COUNT)` returns **every** contributing claim with its provider, timestamp, and provenance. Nothing was picked. Nothing was lost.
>
> BuiltWith reports the legacy ERP retired: the `USES_TECHNOLOGY` edge carries a `valid_to` rather than disappearing, and `relationships(as_of=<before it ended>)` still shows it live.
>
> Two workspaces receive identical evidence in different processing orders and produce the same graph *structure* — the same provider identities grouped together. Entity identifiers differ because they are allocated, not derived, so the comparison is structural rather than byte-level.

> **Correction to the v1 proposal.** v1 claimed all five providers would resolve to one entity, "`SAME_PROVIDER_ID` for the rest". That was wrong: `SAME_PROVIDER_ID` matches only *within* one provider, and no other rule can fire without a shared domain or a name-plus-country. The rules behaved correctly; the demonstration overstated what deterministic matching can do with the fixtures as they stand.
>
> The follow-up that would widen it is a **fixture enrichment**, not a rule change: real Crunchbase and CoreSignal payloads carry a website, and the development fixtures do not. Adding one to those generators is M2.0 work and would let cross-provider resolution be demonstrated at full breadth without weakening any rule. Recorded as scheduled work rather than done here, because editing another milestone's fixtures mid-M3A would blur what this demonstration proves.

---

## As built: what changed during implementation

Four departures from the approved v1 design, each forced by a property of the design itself rather than chosen.

**1. `ResolutionDecision.superseded_by` became `supersedes`.** v1 specified a forward pointer on an immutable table. Those are incompatible: writing `superseded_by` onto the older row requires the `UPDATE` grant that immutability withholds. The pointer now points backwards. `IdentityBinding` and `Relationship` keep forward `superseded_by` — they are not immutable and hold an `UPDATE` grant.

**2. Technology entities are keyed by canonical name.** Technology has no provider identity: vendors report a *name*, not an identifier. The graph assigns technologies a `canonical:technology:<normalized name>` namespace, so two providers reporting "SAP ERP" reach one entity. The honest limitation: "SAP" and "SAP ERP" become two entities. That is deterministic and it under-merges — the direction this module is biased in. A technology catalog that reconciles vendor naming is real work, and guessing at it here would silently merge two different products.

**3. A technology seen only as *removed* is recorded as an already-closed edge.** A vendor reporting current state only tells Signora that LegacyERP was retired without ever having said it was running. v1 implied such a claim would find no edge to close and be dropped. But the claim carries `first_seen` and `last_seen`, so the interval is known — and discarding it would lose exactly the history a competitive-displacement signal reads. The edge is written with both `valid_from` and `valid_to` set.

**4. Re-resolution that reaches the same answer writes nothing.** A decision records a *change* of identity. Writing one per re-sync would bury the corrections that matter under thousands that say nothing, and would inflate the supersession-rate metric into noise.

Two properties worth stating explicitly, both consequences of the approved rules rather than changes to them:

- **A bound identity does not drift.** `SAME_PROVIDER_ID` is `CERTAIN` and matches an identity's own binding on every later pass, so a binding never moves to another entity on its own. Correcting a *wrong merge* is an operator action, whose interface is deferred to M12.
- **An ambiguous identity is reconsidered every time.** It binds to nothing, so it is re-evaluated on each new record and becomes identified once the duplicate candidate is gone. This is the supersession path M3A actually exercises.

**`entity.superseded` is deferred.** It appears in the v1 event model, but nothing publishes it: the only producer would be the operator merge action deferred to M12. An event with no producer is a contract nobody is keeping.

---

## Definition of Done — M3A

- [x] Demonstration passes; AC-25 through AC-29, AC-6, AC-1 all satisfied
- [x] Migration 0009 with forced RLS and full policies in the same revision; four tables registered in `tenancy_policy.py`
- [x] `resolution_decision` added to `IMMUTABLE_TENANT_TABLES`, with the no-`UPDATE` grant asserted
- [x] Security Invariants extended; each addition **proven to fail** when its guarantee is removed
- [x] `04-modules.md`, `05-module-dependencies.md`, and `06-events.md` updated in the same change
- [x] `make smoke` extended with stage 14c, identity resolution
- [x] PROJECT_STATUS and SESSION_HANDOFF updated at the boundary
- [x] **"The Intelligence Pipeline"** ([21-intelligence-pipeline.md](21-intelligence-pipeline.md)) authored — this milestone was its trigger

### Open findings raised, not silently worked around

Both concern `signora_platform/`, which is frozen (CLAUDE.md §20a). Neither was fixed inside this milestone.

| Finding | Effect today | What it would take |
|---|---|---|
| **`EventHandler` receives no session.** The registry's handler signature is `(envelope) -> None`, but a handler must do its work in the *same transaction* as the dispatcher's idempotency claim. A handler that opened its own session would break the exactly-once guarantee the platform is built on. | No module handler is registered in the live registry. The pipeline is exercised end-to-end through its real handlers in the integration suite and in `make smoke`, but the deployed worker consumes nothing. | A platform interface change (pass the session, or expose it via a context variable) — an RFC decision, not a coding-session one. |
| **`PublishableEvent` cannot be satisfied by a frozen dataclass.** The Protocol declares settable attributes; every domain event in the codebase is immutable, as the architecture requires. Each publish site therefore carries a `# type: ignore`. | Cosmetic but spreading — three modules now carry the suppression. | Declaring the Protocol's members read-only. Widens what satisfies it; breaks nothing. |

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

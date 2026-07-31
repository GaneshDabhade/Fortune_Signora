# 32 — Signora Knowledge Ontology

> Status: **OPEN — 2026-07-31.** A conceptual model for a ruling. **No implementation, no tables, no APIs.**
> Audience: the product owner, and anyone deciding what M10 and later milestones are permitted to know.
> Anchors: [21-intelligence-pipeline.md](21-intelligence-pipeline.md) · [28-ai-platform.md](28-ai-platform.md) · [29-ai-reasoning-engine.md](29-ai-reasoning-engine.md) · [31-m10-design-review-evidence.md](31-m10-design-review-evidence.md) · [ADR-0030](adr/0030-the-decision-package.md) · CLAUDE.md §2

The M10 design review asked *"should research become evidence?"* This document steps back and asks what kinds of knowledge Signora holds at all, so that question becomes a lookup rather than a debate.

---

## 1 · Method, and what was already there

Reconstructed from the repository: every workspace-owned table in `tenancy_policy.py`, every reviewed artifact under version control, and the domain types that carry them. Nothing here is aspirational except where marked **(proposed)**.

**Two classification axes already exist and are ratified. A third is missing, and its absence is the whole problem.**

### Axis 1 — Storage category *(ratified, five values)*

How a thing behaves under rebuild, deletion and time.

| Category | Meaning | Under a pipeline rebuild |
|---|---|---|
| **Derived intelligence** | Recomputable from evidence | Regenerates byte-identically |
| **Customer configuration** | Authored by a workspace | **Irreplaceable** — nothing reproduces it |
| **Workflow state** | Records human commitment | **Unreproducible** — must not be touched |
| **Operational history** | Signora's account of its own behaviour | Untouched; commits on its own transaction (ADR-0029) |
| **Materialized AI artifact** | What the platform produced at one moment | **Never regenerated** — a new artifact supersedes, never edits |

### Axis 2 — Universality *(ratified)*

[21-intelligence-pipeline.md](21-intelligence-pipeline.md) draws it precisely:

> Everything up to and including business events is **globally true**; everything from signals onward is **customer-specific** but still traceable back to globally true information.

### Axis 3 — Epistemic provenance *(MISSING — this document's finding)*

**How the thing came to be known, and therefore what it takes to check it.**

Axes 1 and 2 say nothing about this. A `Signal` and a hypothetical research finding could both be "derived intelligence, workspace-specific" while one is reproducible from a rule and the other is a model's opinion.

**The principle that defines this axis already exists** — it simply was never made a property of the data:

> **Every field has the least powerful author capable of producing it correctly.** The database owns timestamps. Code owns derived facts. Domain experts own static knowledge. AI owns inference.

**The ladder *is* the epistemic axis.** Four rungs, in increasing freedom to be wrong in ways nothing can check:

| Rung | Class | How a reader checks it |
|---|---|---|
| 1 | **RECORDED** | It was observed and stored verbatim. Check by re-reading the record |
| 2 | **DERIVED** | Computed by versioned code from RECORDED inputs. Check by recomputing |
| 3 | **ATTESTED** | A named external party asserts it. Check by consulting that party |
| 4 | **INFERRED** | A model produced it. **Cannot be checked** — only corroborated or contradicted |

**Signora already tracks this once, at the earliest layer.** `ClaimSource.payload_provenance` exists so that *"a claim derived from a development fixture stays identifiable for as long as fixtures exist — and a downstream conclusion built on one can be found when authentic payloads arrive."*

That is the exact problem shape research raises, solved once, five milestones ago, at one layer only.

---

## 2 · The ontology

Columns: **Det/Prob** (deterministic or probabilistic) · **AI?** (may AI author it) · **Code?** (may deterministic code author it) · **Cite?** (may a model cite it) · **ES?** (may it enter an Evidence Set) · **Cust?** (customer-visible) · **Reason?** (may influence reasoning) · **Rec?** (may influence recommendations).

Rows marked **(proposed)** do not exist yet.

### 2.1 · Ingested knowledge — RECORDED

| # | Type | Owner | Source | Det/Prob | AI? | Code? | Cite? | ES? | Cust? | Reason? | Rec? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Raw Provider Record** | Provider Platform | A vendor API response, verbatim | Det | ❌ | ✅ | ❌ | ❌ | ⚠️ audit only | Indirect | Indirect |
| 2 | **Claim** | Provider Normalization | One attribute assertion by one provider at one `observed_at` | Det | ❌ | ✅ | Indirect | Indirect | ✅ via chain | ✅ | ✅ |
| 3 | **Normalization Outcome** | Provider Normalization | Why a record produced the claims it did | Det | ❌ | ✅ | ❌ | ❌ | ⚠️ support | ❌ | ❌ |

**Definition (Claim):** the atomic unit of external assertion — *provider P says attribute A of subject S had value V at time T*. **Immutable; new information is a new claim.** A claim is not "true"; it is *truly asserted*. That distinction is the root of this entire ontology and the architecture has honoured it since M2.2.

**Retention/audit:** permanent and immutable. Claims are the bottom of every explanation chain; losing them makes every downstream conclusion unexplainable. `payload_provenance` must survive forever.

### 2.2 · Globally-true derived knowledge — DERIVED

| # | Type | Owner | Source | Det/Prob | AI? | Code? | Cite? | ES? | Cust? | Reason? | Rec? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 4 | **Entity / Identity Binding** | Knowledge Graph | Resolution rules over claims | Det | ❌ | ✅ | Indirect | Indirect | ✅ | ✅ | ✅ |
| 5 | **Resolution Decision** | Knowledge Graph | The rule and strength that bound an identity | Det | ❌ | ✅ | ❌ | ❌ | ⚠️ support | ❌ | ❌ |
| 6 | **Relationship** | Knowledge Graph | Edges with validity intervals | Det | ❌ | ✅ | Indirect | Indirect | ✅ | ✅ | ✅ |
| 7 | **Observation** | Observation Engine | A detected change between claims | Det | ❌ | ✅ | Indirect | Indirect | ✅ | ✅ | ✅ |
| 8 | **Business Event** | Business Event Engine | Taxonomy rules over observations | Det | ❌ | ✅ | Indirect | Indirect | ✅ | ✅ | ✅ |

**Why none is AI-authorable:** each is fully determined by versioned rules over RECORDED inputs. Asking a model to decide whether two identities match, or whether a hiring pattern is a surge, would replace a reproducible answer with an unrepeatable one — *the top rung of the ladder, climbed by accident*.

**Retention/audit:** immutable, permanent, supersession-linked. A correction is a new row naming the one it replaces; `taxonomy_version` records the rules in force.

### 2.3 · Workspace-specific derived knowledge — DERIVED

| # | Type | Owner | Source | Det/Prob | AI? | Code? | Cite? | ES? | Cust? | Reason? | Rec? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 9 | **Signal** | Signal Engine | Catalog rules + workspace profile over business events | Det | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 10 | **Buying Score + Contribution Ledger** | Buying Score Engine | Weighted aggregation; the ledger *is* the explanation | Det | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 11 | **Unsupported Reading** | Signal Engine | Hypotheses tested and not supported | Det | ❌ | ✅ | ⚠️ snapshot | ❌ | ✅ | ✅ | ⚠️ |
| 12 | **Support Basis** | AI Reasoning Engine | Distinct providers + `EvidenceState` + contention | Det | ❌ | ✅ | ❌ | ❌ | ✅ | n/a | ✅ |
| 13 | **Temporal Explanation** | AI Reasoning Engine | Composed from `trigger`, `basis_at`, `delta`, `trend` | Det | ❌ | ✅ | ❌ | ❌ | ✅ | n/a | ✅ |

**A signal is a hypothesis, not a fact** — *this workspace would consider this commercially meaningful*. It is false for a company selling something else. **It is nonetheless DERIVED**, because the rule that produced it is versioned, inspectable and reproducible. **Reproducibility, not certainty, is what makes something DERIVED.**

**Unsupported Reading (#11) is the architecture's existing answer to "should we store non-results?"** — *derived on demand, never stored*, because recording every non-result writes a row per (entity, type) describing mostly nothing. It is **snapshotted** onto a Decision Package because the *rules* that produced the rejection are versioned code.

**Retention/audit:** signals and scores are immutable and supersession-linked; `catalog_version` / `profile_version` / `scoring_model_version` are recorded so a historical row is explainable through the rules that produced it, never today's.

### 2.4 · Customer-authored configuration — ATTESTED (by the customer)

| # | Type | Owner | Source | Det/Prob | AI? | Code? | Cite? | ES? | Cust? | Reason? | Rec? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 14 | **Signal Profile** | Signal Engine | The workspace declares which signals matter | Det | ❌ | ❌ **human only** | ❌ | ❌ | ✅ | Indirect | Indirect |
| 15 | **Workspace Scoring Model** | Buying Score Engine | The workspace's own weighting | Det | ❌ | ❌ **human only** | ❌ | ❌ | ✅ | Indirect | Indirect |
| 16 | **Workspace Opportunity Policy** | Opportunity Engine | Qualification thresholds | Det | ❌ | ❌ **human only** | ❌ | ❌ | ✅ | Indirect | Indirect |

**The only knowledge class that neither code nor AI may author.** It is *irreplaceable* — nothing regenerates a customer's judgement about their own market. **Immutable and versioned**: an edit in place would make every historical signal unexplainable, because the reason it exists would have changed underneath it.

### 2.5 · Signora-authored reviewed artifacts — ATTESTED (by a domain expert)

| # | Type | Owner | Source | Det/Prob | AI? | Code? | Cite? | ES? | Cust? | Reason? | Rec? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 17 | **Signal Catalog** | Signal Engine | Domain experts; versioned repository artifact | Det | ❌ | ❌ **reviewed** | ⚠️ snapshot | ❌ | ✅ | ✅ | ✅ |
| 18 | **Business Event Taxonomy** | Business Event Engine | Domain experts | Det | ❌ | ❌ **reviewed** | ❌ | ❌ | ✅ | Indirect | Indirect |
| 19 | **Prompt** | Owning module | Engineers; fingerprinted, evaluated, released per `(model, dataset)` | Det | ❌ | ❌ **reviewed** | ❌ | ❌ | ❌ | Governs | Governs |
| 20 | **Golden Dataset + Rubric** | AI Platform | Engineers; fingerprinted | Det | ❌ | ❌ **reviewed** | ❌ | ❌ | ❌ | ❌ | ❌ |

**These are ATTESTED rather than DERIVED because a human signed them**, and a diff shows the change. A catalog entry can be wrong — but wrong in a way a named person owns.

**Note #17's `limitations` are currently engineering-authored pending domain review** (finding F-3). The provenance claim is not yet fully true, and it is marked as such in the artifact.

### 2.6 · Human workflow — RECORDED (of a human act)

| # | Type | Owner | Source | Det/Prob | AI? | Code? | Cite? | ES? | Cust? | Reason? | Rec? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 21 | **Opportunity** | Opportunity Engine | Machine-created at `TRACKING`; **only a human progresses it** | Det | ❌ | ⚠️ creation only | ✅ | ✅ | ✅ | ✅ | ✅ |
| 22 | **Opportunity State** | Opportunity Engine | A person decided, with `actor_id` and reason | Det | ❌ | ❌ **human only** | Indirect | Indirect | ✅ | ✅ | ✅ |

> **Intelligence suggests. Humans commit.** Nothing regenerates a human's decision, which is why a pipeline rebuild is safe *for derived intelligence only*.

### 2.7 · Operational history — RECORDED (of the platform's own behaviour)

| # | Type | Owner | Source | Det/Prob | AI? | Code? | Cite? | ES? | Cust? | Reason? | Rec? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 23 | **AI Inference Record** | AI Platform | Every model call, on **every** outcome | Det *(about a probabilistic act)* | ❌ | ✅ | ❌ | ❌ | ⚠️ audit | ❌ | ❌ |
| 24 | **Outbox / processed / dead-letter** | Platform | Event durability machinery | Det | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

**#23 is a deterministic record of a non-deterministic event** — the distinction that makes the ungrounded rate defensible. Commits on its own transaction (ADR-0029) so a rolled-back unit of work cannot discard the record of a failed call. **#24 is platform infrastructure: no module may read it, and `signora_app` holds `INSERT` only.**

### 2.8 · AI-authored knowledge — INFERRED

| # | Type | Owner | Source | Det/Prob | AI? | Code? | Cite? | ES? | Cust? | Reason? | Rec? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 25 | **Narration** | AI Platform | Model restatement of computed facts, grounded | **Prob** | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| 26 | **Decision Package** | AI Reasoning Engine | 3 of 15 parts model-authored; 12 derived/composed | **Mixed** | ⚠️ 3/15 | ✅ 12/15 | ❌ | ❌ | ✅ | n/a | ✅ |
| 27 | **Proposition / Stated Reasoning** | AI Reasoning Engine | The model's conclusion and its account of it | **Prob** | ✅ | ❌ | ❌ | ❌ | ✅ | n/a | ✅ |

**#25 announces language; #26 announces a conclusion.** That is the M8/M9 boundary in one line.

**#27 is named for what it is.** A model has no introspective access to its own computation; what it emits when asked to explain itself is *a plausible account generated alongside the answer*. It is **never presented as chain-of-thought**.

**Nothing in this section may be cited or enter an Evidence Set.** Every one is a *consumer* of evidence, not a source. **This is currently a convention, not a constraint** — see §3.

### 2.9 · Proposed knowledge — M10 and beyond

| # | Type | Owner | Source | Det/Prob | AI? | Code? | Cite? | ES? | Cust? | Reason? | Rec? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 28 | **Research Finding (sourced)** *(proposed)* | AI Research Engine | An agent retrieved a document; the **document** asserts it | **ATTESTED** | ⚠️ locates, does not author | ❌ | **OPEN** | **OPEN** | ✅ | **OPEN** | ✅ |
| 29 | **Research Synthesis** *(proposed)* | AI Research Engine | The agent's interpretation across findings | **Prob / INFERRED** | ✅ | ❌ | **should be ❌** | **should be ❌** | **OPEN** | **OPEN** | ⚠️ |
| 30 | **Agentic Step Trace** *(proposed)* | AI Research Engine | What the agent did, tool by tool | Det *(about a prob. act)* | ❌ | ✅ | ❌ | ❌ | ⚠️ audit | ❌ | ❌ |
| 31 | **Retrieval Context / Embedding** *(proposed)* | AI Research Engine | Vector similarity over prior artifacts | **Prob** *(ranking)* | ⚠️ model-produced vectors | ✅ | ❌ | ❌ | ❌ | ⚠️ selection only | ❌ |
| 32 | **Recommendation** *(M11)* | Recommendation Engine | Proposed action from a Decision Package | **Prob** | ✅ | ⚠️ partly | ❌ | ❌ | ✅ | ❌ | n/a |
| 33 | **Timeline Entry** *(M7)* | Timeline | Projection of events already published | Det | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |

**#28 and #29 are the crux, and separating them is the finding.** They were conflated as "a research artifact" in the design review. They sit on **different rungs**:

- **#28 is ATTESTED.** The agent *located* it; a named external source *asserts* it. It is checkable the way a claim is checkable — by consulting the source. **It is structurally the same shape as a Claim (#2), differing only in that the asserting party is a public document rather than a contracted provider.**
- **#29 is INFERRED.** No party asserts it. It is the agent's opinion, and no amount of provenance makes it checkable.

**#31 deserves care.** An embedding is model-produced and a ranking is probabilistic — but it only *selects* what to look at. **Non-deterministic selection over deterministic facts leaves the facts deterministic.** It becomes dangerous only if the *ranking* is presented as meaning.

---

## 3 · Is "Evidence Set" still the right abstraction?

**Verdict: the mechanism is right. The abstraction is incomplete, and its incompleteness is load-bearing.**

### What Evidence Set does correctly

Three properties, all enforced by types, all worth keeping:

1. **Closure.** Built once, never added to. A model may reference nothing outside it.
2. **Workspace stamping.** Refuses a set assembled from more than one workspace.
3. **Canonical identity.** The digest is computed over a canonical form, so two identical sets are identical facts.

**None of these should change.**

### What it silently assumes

**Every fact in an Evidence Set is deterministically derived and therefore checkable.**

That assumption is true today — everything in a set comes from #2–#10 and #21 — and it is **enforced by nothing**. `EvidenceRef.kind` is an unconstrained string; `EvidenceFact`'s docstring declares *"one thing that is true"* without any mechanism making it so.

So the Evidence Set conflates two ideas that have been identical until now:

> *"the closed universe a model may reference"* and *"the set of checkable derived facts"*

**M10 is the first milestone where those come apart.** A sourced research finding belongs in the first and — depending on the ruling — may or may not belong in the second. A research synthesis belongs in neither.

### The structural diagnosis

Grounding's five checks all ask *"does this citation resolve **inside the set**?"* **Not one asks what kind of thing it resolved to.** So the guarantee is:

> *"Every statement references something in the set."*

which the architecture has been reading as:

> *"Every statement is supported by a checkable fact."*

**Those are the same sentence only while the set contains nothing but checkable facts.** The second reading is what customer trust rests on; the first is what the code enforces. **Today the gap is zero. M10 opens it.**

This is the same defect shape as [ADR-0031](adr/0031-evidence-citation-protocol.md), one level up: *two components share a protocol and neither owns it.* There, the renderer and parser disagreed about a token's form. Here, the builder and the checker disagree about what a fact **is** — and, as with ADR-0031, it has been passing on the fact that no caller has yet supplied the awkward case.

### What the ontology implies

**Evidence Set should carry epistemic class per fact.** Not a new container — the existing one, with the axis it was always implicitly using made explicit:

- **The four rungs already exist as a ratified principle.** Recording which rung authored a fact adds no new concept; it stops discarding one the architecture already relies on.
- **It makes the rules expressible rather than remembered.** *"INFERRED may not enter an Evidence Set"* becomes a construction-time refusal instead of a convention M10 could break with no test failing — and *types should make incorrect architecture impossible*.
- **It gives the Decision Package something true to show a customer.** *"Two premises derived from your provider data; one attested by a named source you can open"* is a materially better answer to *"which evidence supports it?"* than an undifferentiated list.
- **It gives `SupportBasis` a defensible question to ask.** Support currently counts *distinct corroborating providers*. With a provenance class it can decide, explicitly and visibly, whether an external attestation corroborates — rather than silently not counting, which is today's accidental behaviour.
- **It has precedent in this repository.** `ClaimSource.payload_provenance` already does exactly this at the claim layer, for exactly this reason.

### What it does *not* imply

- **Not a second Evidence Set type.** Two containers would be two protocols, and §3's whole diagnosis is that two owners of one protocol is the defect.
- **Not a change to grounding's five checks.** They are correct. A sixth check — *"is this fact's provenance permitted for this consumer?"* — would be a **construction-time** rule, not a grounding rule, and it would sit where the set is built.
- **Not a licence to admit synthesis.** The ontology's clearest result is that #29 belongs in no evidence set under any option.
- **Not an M9 rewrite.** Every fact M9 sees today is DERIVED; a default of DERIVED leaves M9's behaviour unchanged.

---

## 4 · What the ontology settles, and what it does not

### Settled by classification

| Question | Answer |
|---|---|
| May research *synthesis* (#29) be cited? | **No.** It is INFERRED. Nothing checks it, and citing it makes one model's opinion another model's evidence |
| May the agent's *step trace* (#30) be cited? | **No.** Operational history, like #23 |
| May embeddings (#31) influence reasoning? | **Only by selecting** what is looked at, never by supplying meaning |
| May a Decision Package (#26) become evidence for a later one? | **No.** A consumer of evidence, never a source. Otherwise conclusions compound on conclusions |
| May a Recommendation (#32) influence reasoning? | **No** — that is the hidden feedback loop the dependency graph forbids |

**Five questions that were open in the design review are now answered by the classification rather than by argument.** That is the value of doing this first.

### Still requiring a ruling

**One question, and it is genuinely a judgement call rather than a derivation:**

> **Is an ATTESTED external claim (#28) admissible as evidence?**

The ontology sharpens it considerably. **A sourced research finding is structurally the same shape as a Claim (#2)** — an assertion by a named party, at a known time, stored verbatim, checkable by consulting that party. The only difference is that a Claim's asserter is a contracted provider under a data agreement, and a finding's asserter is a public document.

So the real question is:

> **Is "a party asserted this" evidence, or is only "Signora derived this from a contracted provider" evidence?**

Three sub-questions follow, and none is answerable by classification alone:

1. **Does an external attestation corroborate?** `SupportBasis` counts *distinct providers*. If a public source counts, "independent corroboration" changes meaning. If it does not, a well-sourced conclusion may read `LIMITED`.
2. **What verifies an attestation?** A model can fabricate a URL as readily as a quantity, and `UNGROUNDED_QUANTITY` does not cover *"this source does not say that"*. **Admitting #28 requires a verification step that does not exist.**
3. **Does the customer-visible distinction have to be explicit?** If derived and attested premises are shown identically, the class exists in the schema and not where it matters.

---

## 5 · The one-line summary

> **Signora's architecture has always classified knowledge by *how long it lives* and *who it is true for*. It has never classified knowledge by *how it came to be known* — because until M10, everything came to be known the same way.**

The Evidence Set is not wrong. It is **an abstraction whose implicit precondition is about to stop holding**, and the ontology's recommendation is to make that precondition explicit **before** the first caller violates it — rather than discovering it afterwards in stored rows that cannot be reclassified.

**Next:** the repository-wide rules that follow from this classification are stated in **[34-knowledge-contract.md](34-knowledge-contract.md)** — 23 invariants, every one discovered already operating in the repository rather than invented. It narrows §4's remaining question further but does not answer it.

**Then:** a ruling on §4's remaining question. The design review's five options are unchanged, but three of them (B, D, and the synthesis half of C) are now excluded by classification rather than by preference.

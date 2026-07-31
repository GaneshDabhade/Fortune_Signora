# 34 — The Knowledge Contract

> Status: **PROPOSED — 2026-07-31.** A repository-wide architectural contract, binding on every module once ratified.
> Audience: every engineer adding a knowledge object to Signora, in any module, ever.
> Anchors: [32-knowledge-ontology.md](32-knowledge-ontology.md) · [31-m10-design-review-evidence.md](31-m10-design-review-evidence.md) · [21-intelligence-pipeline.md](21-intelligence-pipeline.md) · [28-ai-platform.md](28-ai-platform.md) · [ADR-0030](adr/0030-the-decision-package.md) · CLAUDE.md §2, §8, §10

This document stands to knowledge as the layering contracts stand to imports and RLS stands to tenancy: **a set of invariants every object must satisfy regardless of which module owns it.** The ontology said what exists. This says what is *always true*.

**Nothing here is invented.** Every rule below was found already operating somewhere in the repository, usually in one module, usually undocumented. The contribution is generalisation and enforcement, not design.

---

## 0 · What a knowledge object is

**A knowledge object is anything Signora stores or transmits that asserts something about a customer's world.**

That deliberately excludes: HTTP requests, worker jobs, cache entries, indexes, embeddings-as-vectors, connection state, and the outbox. Those are *machinery*. A knowledge object is something a customer could, in principle, be shown and could, in principle, disagree with.

**The test:** *if this were wrong, could a customer be misled?* If yes, it is knowledge and this contract binds it.

---

## 1 · Identity

### 1.1 · The discovered invariant

The repository already has a rigorous identity discipline that **nobody wrote down**. Four modules derive identity from content; two mint it. The split is not arbitrary:

| Object | Identity | Keyed on |
|---|---|---|
| `Observation` | `uuid5` | workspace · entity · provider · attribute · kind · transition key |
| `Business Event` | `uuid5` | workspace · entity · type · sorted evidence observation ids |
| `Signal` | `uuid5` | workspace · entity · signal type · evidence |
| `Buying Score` | `uuid5` | workspace · entity · model/profile versions · sorted signals · `basis_at` |
| `Claim` | `uuid4` | *minted* |
| `Opportunity`, `AI Narration`, `AI Reasoning` | `uuid4` | *minted* |

The docstrings state the reason each time, in almost identical words: *"survives a full pipeline rebuild"*, *"keying on the observed facts survives regeneration"*, *"a version bump that re-detects the same surge over the same evidence produces the same id and inserts nothing."*

> **RULE 1 — Identity is derived from content if and only if the object is reproducible from its inputs. Otherwise identity is minted.**

**This is not the epistemic ladder, and the difference matters.** Identity tracks *computation versus act*:

- A **computation** repeated over identical inputs is the *same* object. Re-running must insert nothing.
- An **act** — a provider asserting, a human deciding, a model generating — repeated is a *second* act, even if it produces identical words.

So minting is correct for RECORDED (an observation happened twice), for workflow (a person decided twice), and for INFERRED (a model was called twice). Content-derivation is correct for DERIVED alone. **The ladder is non-monotonic here, and that is right.**

### 1.2 · Consequences

> **RULE 2 — Identity never changes.** Not on correction, not on supersession, not on reclassification. A corrected fact is a **new object naming the one it supersedes**, and supersession pointers point *backwards* — forced by immutability, since a forward pointer would require an `UPDATE` grant these tables withhold.

> **RULE 3 — Identity is owned by the module that owns the object**, and its derivation is part of that module's domain, not its infrastructure. An id minted in a repository is an id the domain cannot reproduce.

**Open consequence for M10:** a Research Finding is *both*. The **retrieval** is an act (a document was fetched at a moment); the **claim the document makes** is content that does not change on re-retrieval. §7 resolves this.

---

## 2 · Epistemic origin

> **RULE 4 — Every knowledge object has exactly one epistemic origin: RECORDED, DERIVED, ATTESTED, or INFERRED.**

Not zero (unclassified knowledge is knowledge nobody can weigh) and not two (an object that is *partly* inferred is inferred — see 2.2).

> **RULE 5 — Epistemic origin is immutable for the lifetime of the object.**

The justification is the same as for identity, and stronger: **origin determines how a reader checks the thing.** An object whose origin could change would be one whose verification procedure changed retroactively, invalidating every audit that relied on the old one. This is *immutability is the default for anything that records a fact* applied to the fact's own provenance.

**Repository precedent:** `ClaimSource.payload_provenance` is already immutable and propagated *"for as long as fixtures exist — and a downstream conclusion built on one can be found when authentic payloads arrive."* That is Rule 5, implemented once, at one layer, five milestones ago.

### 2.2 · Mixed-origin objects

A Decision Package holds twelve DERIVED parts and three INFERRED ones. It is not "mixed origin".

> **RULE 6 — A composite object's origin is that of its *most powerful* author.** A Decision Package is INFERRED as an object, even though most of it is derived — because a reader cannot trust the whole more than its weakest-checkable part.

But:

> **RULE 7 — A composite must preserve the origin of its parts, not flatten it.** This is what makes Rule 6 tolerable rather than destructive: the package is INFERRED, and yet `supporting_evidence`, `support`, `temporal` and `limitations` each remain individually checkable. **A composite that flattened origin would make a conclusion and its evidence equally untrustworthy, which is exactly backwards.**

---

## 3 · Knowledge promotion

**Can an object move between epistemic classes?**

> **RULE 8 — No object ever changes its epistemic class. Promotion does not exist.**

What *can* happen — and what is routinely mistaken for promotion — is that **a new object of a different class is created, citing the old one.** The distinction is the whole contract:

| Apparent promotion | What actually happens |
|---|---|
| RECORDED → DERIVED | A claim is *not* promoted. A **new** Observation (DERIVED) is created **citing** claims. Both persist |
| ATTESTED → DERIVED | A catalog entry is not promoted. A **new** Signal (DERIVED) is created by applying it |
| INFERRED → ATTESTED | **Never.** No process converts a model's output into someone's assertion. A human *reviewing* it creates a **new** ATTESTED object recording *that a named person signed it* |
| INFERRED → DERIVED | **Never, under any circumstance.** Determinism is a property of how something was produced. It cannot be conferred afterwards |

**The one case that looks like a real exception, examined:** a model proposes a signal; the Signal Engine's rules independently support it; a Signal is generated. **Nothing was promoted.** The model's proposal remains INFERRED forever; the Signal is DERIVED because *the rules derived it*, and it would have been derived had the proposal never existed. **The proposal directed attention; it did not confer status.**

> **RULE 9 — Attention and status are different things.** An INFERRED object may legitimately direct where deterministic machinery looks. It may never determine what that machinery concludes.

Rule 9 is what makes M10 architecturally possible at all, and §7 rests on it entirely.

---

## 4 · The citation contract

### 4.1 · What grounding checks today, precisely

Five `ViolationKind`s: `MALFORMED_CITATION`, `UNRESOLVED_CITATION`, `UNCITED_STATEMENT`, `UNGROUNDED_QUANTITY`, `WORKSPACE_ESCAPE`.

**Every one is a question about *existence and resolution*.** Not one asks what *kind* of thing was resolved. So grounding's guarantee is:

> *"Every statement references something inside the closed set."*

which the architecture has been reading as:

> *"Every statement is supported by a checkable fact."*

**Those are the same sentence only while the set contains nothing but checkable facts.** Today the gap is exactly zero. M10 is the first caller that could open it.

### 4.2 · Existence versus admissibility

> **RULE 10 — Grounding validates identity. Admissibility is validated at construction, not at grounding.**

This is deliberate and I want the reasoning on the record, because the intuitive answer is to add a sixth `ViolationKind`.

**Why admissibility does not belong in grounding:**

1. **Grounding is a property of an *output*; admissibility is a property of an *input*.** By the time a model has cited something inadmissible, the inadmissible thing was already put in front of it — and a model shown a fact and told not to use it is being set up to fail.
2. **It would make the failure a model's fault when it is a composition error.** *Failure attribution must be truthful*: an error must never name a component that was not involved. The model that cited an inadmissible fact did nothing wrong.
3. **Refusing at construction makes the violation unrepresentable rather than merely detected** — *types should make incorrect architecture impossible*.
4. **The repository already does this.** The release rule (`require(model, dataset)`) is an admissibility check, and it fires *before* the call, not after. That is the precedent, and it is exactly the right shape.

> **RULE 11 — A knowledge object that may not be cited must never enter the set a model can see.** Admissibility is enforced by refusing construction, not by detecting misuse.

### 4.3 · Who may be cited

| Origin | Citable | Why |
|---|---|---|
| **RECORDED** | ✅ indirectly, through what derives from it | A claim is checkable by re-reading the record |
| **DERIVED** | ✅ **yes — the default and the norm** | Checkable by recomputation |
| **ATTESTED** | ⚠️ **the open question** — see §7 | Checkable only by consulting the asserting party |
| **INFERRED** | ❌ **never** | Nothing checks it. Citing it makes one model's output another model's evidence |

> **RULE 12 — INFERRED knowledge is never citable, by any consumer, under any configuration.**

---

## 5 · The Evidence Set

**Verdict: the abstraction is correct and must not be replaced. It is incomplete in exactly one respect.**

### 5.1 · What must not change

Three properties, all type-enforced, all load-bearing:

1. **Closure** — built once, never added to. A model may reference nothing outside it.
2. **Workspace stamping** — refuses a set assembled from more than one workspace.
3. **Canonical identity** — the digest is computed over a canonical form, so identical sets are identical facts and a customer can cite one.

**A second container would be strictly worse.** Two evidence types would be two protocols with two owners, which is the defect shape [ADR-0031](adr/0031-evidence-citation-protocol.md) documents one level down. **Do not split the Evidence Set.**

### 5.2 · The one incompleteness

`EvidenceRef.kind` is an unconstrained string, and `EvidenceFact`'s docstring declares *"one thing that is **true**"* with nothing enforcing it. The container therefore carries an **unstated precondition**: everything in it is deterministically derived.

> **RULE 13 — Every `EvidenceFact` declares its epistemic origin explicitly. The default is DERIVED, and INFERRED is unrepresentable.**

This adds no new concept — the ladder is already a ratified principle. It stops *discarding* a classification the architecture already depends on.

> **RULE 14 — The evidence digest must remain a function of deterministic content only.** Whatever enters the set, two assemblies over unchanged pipeline state must produce the same digest. A digest that varied with a model call would break replay, regression testing, and the customer's ability to cite a fixed universe.

Rule 14 is the sharpest constraint in this document, and it independently rules out admitting anything whose *content* is model-authored — regardless of how it is labelled.

---

## 6 · Decision Packages, recommendations, and compounding

> **RULE 15 — A Decision Package is never evidence.** It is INFERRED (Rule 6), and Rule 12 therefore forbids it. No exception exists for "our own" AI output; *especially* not for our own.

> **RULE 16 — A Recommendation is never evidence**, and never an input to reasoning. `05-module-dependencies.md` already forbids the mechanism — *a downstream module publishing an event an upstream module subscribes to as a hidden feedback loop*. This states the knowledge-level rule the dependency rule implies.

> **RULE 17 — Conclusions do not compound.** No conclusion may rest on another conclusion. Every conclusion resolves to RECORDED, DERIVED or (pending §7) ATTESTED knowledge in **one hop**, never through a chain of inferences.

**Why compounding is uniquely dangerous:** errors in derived knowledge are *bounded* — a wrong rule produces a wrong answer, reproducibly, and a test can catch it. Errors in compounded inference are **unbounded and invisible**: each step is individually plausible, each cites something real, and the chain drifts with nothing anywhere reporting a failure. A customer inspecting the final package would find every citation resolving correctly.

**The permitted exception, stated precisely so it is not mistaken for compounding:** a *later* Decision Package may cite a *later buying score* that was itself influenced by signals a *previous* package's existence caused a human to investigate. That is fine — because a **human acted**, and the human's act is RECORDED. *Intelligence suggests; humans commit* is what breaks the chain.

---

## 7 · Research

The ontology's most useful result was separating things that were being discussed as one thing. Applying this contract to each:

| Artifact | Knowledge? | Origin | Citable | May influence reasoning | Customer-visible |
|---|---|---|---|---|---|
| **Research Finding** *(sourced)* | ✅ Knowledge | **ATTESTED** | ⚠️ **open — §7.2** | ⚠️ open | ✅ yes |
| **Research Synthesis** | ✅ Knowledge | **INFERRED** | ❌ **never** (Rule 12) | ❌ not as evidence | ⚠️ only if labelled as opinion |
| **Hypothesis** *(a proposed signal)* | ✅ Knowledge | **INFERRED** | ❌ never | ✅ **as attention only** (Rule 9) | ❌ not directly |
| **Tool trace / agentic step** | ❌ **Implementation artifact** | — *(operational history)* | ❌ | ❌ | ⚠️ audit only |
| **Embedding vector** | ❌ **Implementation artifact** | — | ❌ | ⚠️ **selection only** | ❌ |
| **Semantic retrieval ranking** | ❌ **Implementation artifact** | — | ❌ | ⚠️ **selection only** | ❌ |

### 7.1 · The selection/meaning boundary

> **RULE 18 — Non-deterministic *selection* over deterministic facts leaves the facts deterministic. Non-deterministic *ranking* presented as meaning does not.**

An embedding may decide *what to look at*. It may never decide *what is true*, and a similarity score must never be shown to a customer as significance. This is the same distinction that keeps `ProviderResponse.simulated` legitimate as diagnostics while `if simulated:` is forbidden as behaviour.

**Consequence for Rule 14:** because retrieval only selects, an evidence set assembled after retrieval is still deterministic **provided the selection is recorded**. A set whose *membership* depended on an unrecorded ranking would have a hidden input.

> **RULE 19 — If a non-deterministic process selects what enters an evidence set, the selection must be recorded as operational history, and the resulting set's digest computed over the members — never over the ranking.**

### 7.2 · What remains genuinely open

**Exactly one question, and this contract sharpens it as far as it can go without a ruling:**

> **May an ATTESTED external claim be cited?**

The contract establishes what an answer must satisfy:

- **Rule 14 binds regardless.** A finding's *content* must be a verbatim excerpt from a retrieved document, never the model's paraphrase — a paraphrase is INFERRED and Rule 12 excludes it. So an admissible finding is `(verbatim excerpt, source identity, retrieved_at)` and nothing else.
- **Rule 1 resolves its identity.** The excerpt plus the source is content and reproducible → `uuid5`. The *retrieval* is an act and belongs in operational history with a minted id. **Two objects, not one.**
- **Rule 11 places the check.** Admissibility is refused at construction. So *"is this excerpt genuinely present in the retrieved document?"* must be answered **before** the set is built — mechanically, not by a model. **This verification step does not exist and is a genuine new build.**
- **Rule 8 forbids the shortcut.** A finding a model *believes* is well-sourced is INFERRED and stays INFERRED. Only a mechanical check against a retrieved document produces ATTESTED status.

**What this contract cannot decide:** whether Signora *wants* third-party assertions in its evidence at all. That is a product and trust judgement — is *"a named public source says X"* the same kind of thing as *"Signora derived X from a contracted provider"*? — and it is the product owner's.

---

## 8 · Support

`SupportBasis` derives from two yes/no questions: are there ≥2 **distinct corroborating providers**, and is the evidence `CURRENT`. It introduces no threshold, and that property must survive.

> **RULE 20 — INFERRED knowledge never contributes to Support, in any form.** A model's agreement is not corroboration; it is the same generator producing the same bias twice.

**On ATTESTED knowledge, three positions, and the contract's constraint on each:**

| Position | Consequence |
|---|---|
| External sources **do not** corroborate | A well-sourced conclusion may read `LIMITED`, which under-reports it. Support stays exactly as defined today |
| External sources corroborate **as equals** | *"Two independent providers"* silently changes meaning. A blog post and a contracted data provider would weigh identically — and the level would become a claim Signora cannot defend |
| External sources corroborate **as a distinct class** | Honest, and shows a customer *"one provider, plus two named public sources"*. **Costs a new distinction in a type that deliberately has none** |

> **RULE 21 — Corroboration means *independent sources agreeing*, and independence is a property of the sources, not of the count.** Whatever is ruled, the definition may not become a tuned number. One provider repeating itself across ten events remains one source; the same logic must apply to one publication republished across ten sites.

**The trap worth naming:** external sources are *far less independent than providers*. Three outlets reporting one press release are **one source**. A contracted provider's independence is contractual and auditable; a public source's is not. **If ATTESTED knowledge is admitted to Support, independence must be established at the level of the originating claim, not the retrieved document** — and no mechanism for that exists today.

---

## 9 · Auditability

For each origin: how a human checks it, how an auditor checks it, and whether it can ever be *fully* verified.

| Origin | A human checks it by | An auditor checks it by | Fully verifiable? |
|---|---|---|---|
| **RECORDED** | Reading the stored record | Comparing the record to the vendor's own copy; `payload_provenance` distinguishes fixture from authentic | ✅ **Yes** — within Signora's boundary. Whether the provider was *right* is outside it |
| **DERIVED** | Recomputing from the cited inputs | Re-running the pipeline and diffing; content-derived ids make the diff exact and empty when correct | ✅ **Yes**, and uniquely so — this is the only class where verification is *mechanical and total* |
| **ATTESTED** | Consulting the asserting party — opening the document, reading the catalog entry | Confirming the assertion was made, by whom, when, and that the stored excerpt matches | ⚠️ **Partially, and decayingly.** Verifiable *that it was asserted*; never *that it is true*. And a public source can change or vanish — so the excerpt and `retrieved_at` must be stored, or verifiability decays to zero |
| **INFERRED** | **Cannot.** Only corroborate or contradict against other classes | Confirming *what was produced, from which inputs, by which prompt and model, when* | ❌ **Never.** The *act* is fully auditable; the *content* is not verifiable even in principle |

> **RULE 22 — For INFERRED knowledge, auditability is a property of the act, never of the content.** This is why every AI artifact carries complete denormalized provenance — which evidence, which prompt, which model, which inference, when — and why `ai_inference` records failures as faithfully as successes.

> **RULE 23 — ATTESTED knowledge must store what it relies on.** A reference to an external source is not sufficient: the excerpt and retrieval time must be captured, because the referent is outside Signora's control. This is the same reasoning that snapshots catalog content onto a Decision Package while merely referencing an immutable buying score.

**The asymmetry worth stating plainly:** DERIVED is the only class that can be *fully* verified, and it is the class Signora produces most of. That is not a coincidence — it is the architecture's central bet, and this contract exists to keep it from being traded away one convenience at a time.

---

## 10 · Repository invariants

The concise list. **Every rule below was found operating in the repository**; none is newly invented.

**Identity**
1. Identity is derived from content **iff** the object is reproducible from its inputs; otherwise minted.
2. Identity never changes. A correction is a new object naming the one it supersedes, pointing backwards.
3. Identity is owned by the owning module's **domain**, not its infrastructure.

**Origin**
4. Every knowledge object has **exactly one** epistemic origin.
5. Epistemic origin is **immutable**.
6. A composite's origin is that of its **most powerful** author.
7. A composite **preserves** the origin of its parts; it never flattens it.

**Promotion**
8. **Promotion does not exist.** A new object of a different class is created, citing the old.
9. INFERRED knowledge may direct **attention**; it may never confer **status**.

**Citation**
10. Grounding validates identity. **Admissibility is validated at construction.**
11. Anything that may not be cited **never enters the set a model can see**.
12. **INFERRED knowledge is never citable**, by any consumer, under any configuration.

**Evidence Set**
13. Every `EvidenceFact` declares its origin. Default DERIVED; **INFERRED unrepresentable**.
14. **The evidence digest is a function of deterministic content only.**

**Composition**
15. A Decision Package is never evidence.
16. A Recommendation is never evidence and never an input to reasoning.
17. **Conclusions do not compound** — every conclusion resolves to non-INFERRED knowledge in one hop.

**Selection**
18. Non-deterministic **selection** over deterministic facts is permitted; non-deterministic **ranking as meaning** is not.
19. A non-deterministic selection into an evidence set must be **recorded**; the digest covers members, never the ranking.

**Support**
20. INFERRED knowledge **never** contributes to Support.
21. Corroboration means **independent sources agreeing**; independence is a property of sources, never a tuned count.

**Audit**
22. For INFERRED knowledge, auditability is a property of the **act**, never the content.
23. ATTESTED knowledge **stores what it relies on** — excerpt and retrieval time, not merely a reference.

---

## 11 · The search for further hidden axes

The ontology found one missing axis. **I looked for others deliberately, and report both what I found and what I rejected.**

### Rejected — already covered

| Candidate | Why it is not a new axis |
|---|---|
| **Trust** | Not independent. Trust is a *reading* of epistemic origin plus corroboration. Formalising it would create a score, and a score would be averaged |
| **Certainty** | Deliberately absent, and must stay absent. ADR-0030 Ruling 1 rejected model-emitted confidence; `SupportLevel` refuses `int` and `float` and refuses ordering. A certainty axis would reintroduce exactly that |
| **Authority** | Covered by ownership plus immutability. *Who may supersede this* is already answered by the owning module and the human-only rule |
| **Visibility** | A presentation concern, and correctly so — nothing in the pipeline branches on it |
| **Verifiability durability** | Real, but a **property of ATTESTED** rather than an axis. Captured as Rule 23 |

### Identified — one, and it is genuinely missing

**Disclosure class: what a knowledge object may be shown to, and in which direction.**

**Repository evidence, not intuition:**
- `10-security.md:68` — *"What workspace data may be included in AI prompts: **TODO**"*.
- **R-04** (PII classification/retention) and **R-05** (prompt data-classification policy) are both 🔴 High and both **escalated to Legal**.
- R-05's mitigation names the enforcement point explicitly: *"an allowlist/blocklist enforced in AI Research Engine's and AI Reasoning Engine's context-assembly step"* — a control that does not exist.

**Why it is orthogonal to all three existing axes:** a DERIVED, globally-true, permanently-stored business event may contain a named individual. A RECORDED provider payload may be entirely public. Sensitivity does not follow origin, storage category, or universality.

**Why M10 raises it now rather than later.** Every AI call so far has been **outbound-to-vendor with inbound-only content** — Signora sends its own facts to a model. M10 introduces a **new egress direction**: an agent issues *queries* to public services. A search query containing a customer's account name, or an inference about their buying intent, is a disclosure of workspace data to a party with no contract — and it leaves no trace in any table this architecture currently defines.

**My honest assessment:** this is a real fourth axis, but it is **not yet an engineering classification** — it is a legal and product policy with an escalation already open, and formalising the axis before the policy exists would encode a guess. It **does not block the evidence question**, and it **does block M10's tool-use design specifically**.

> **Recommendation: do not add it to this contract now.** Raise it as a precondition on M10's tool-use task, and formalise it when R-05 returns from Legal. Adding an axis to complete a pattern is exactly what §11 was asked to avoid.

---

## Architectural Consequences

### What changes for M10

**M10 gets narrower, more specified, and more buildable.**

- **Three of the design review's five options are excluded by contract**, not by preference. Option B violates Rules 12, 13 and 14. Option D creates a hidden input. The *synthesis* half of any option violates Rule 12.
- **Research synthesis, tool traces, embeddings and rankings are settled** — none is citable, none enters an evidence set, and two of them are not knowledge at all. That removes most of the surface that felt undecided.
- **Hypotheses have a permitted role**: Rule 9 lets research direct attention without conferring status, which is what makes the "research proposes signals" shape architecturally legal.
- **One new build is now visible that was not before:** an ATTESTED finding requires a **mechanical excerpt-verification step** (Rule 11 + Rule 8). It cannot be a model checking itself.
- **Two objects, not one** (Rule 1): the retrieval is an act with a minted id in operational history; the finding is content with a derived id.
- **A precondition is now explicit:** the disclosure question (§11) blocks tool-use design specifically.

### What changes for future AI modules

- **M11 (Recommendation) is constrained before it starts.** Rules 15, 16 and 17 mean a recommendation may never re-enter reasoning and conclusions may never compound — the failure mode that would otherwise arrive quietly in M11 or M12.
- **Every future module inherits a lookup instead of a debate.** *"What origin is this, and what does the contract permit?"* replaces re-deriving the argument each time.
- **`ai_platform`'s freeze after M10 becomes safer**, because the substrate freezes against a stated knowledge contract rather than an implicit one.

### Is the ontology now complete?

**For M10's purposes, yes.** The ontology classifies what exists; this contract states what is always true; together they answer every question the design review raised except one.

**Not permanently, and the boundary is known:** the disclosure axis (§11) is identified, evidenced, and deliberately unformalised pending R-05. When it is formalised, it will extend the ontology rather than revise it — a fourth axis alongside three, not a correction to them.

### Does any unresolved question still block M10?

**One blocks the evidence design; one blocks tool-use design; neither blocks starting.**

1. **🔴 Blocking the evidence design — a ruling only you can give.** *May an ATTESTED external claim be cited?* This contract has narrowed it as far as analysis can: it establishes that an admissible finding must be a verbatim excerpt with a source and retrieval time, that verification must be mechanical and precede construction, and that Support must not treat a republished press release as three corroborating sources. **What remains is a product judgement:** is *"a named public source asserts X"* the same kind of thing as *"Signora derived X from a contracted provider"*?
2. **🟠 Blocking tool-use design.** The disclosure question — R-05, escalated to Legal.

**Everything else in M10 is now an implementation exercise**, which was the objective. Retrieval infrastructure, artifact storage, agentic orchestration, resumability, evaluation and the event contract are all specified enough to build against the rules above.

**And the sequencing recommendation from [31](31-m10-design-review-evidence.md) §7 is unchanged and now better supported:** a short M9.5 should precede M10 — ADR-0031 invalidates two released prompts today and three after M10, and M10 is the milestone most likely to misread its symptoms as model capability findings.

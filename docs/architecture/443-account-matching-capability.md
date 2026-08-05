# 443 · Account matching — one capability, three separable problems, and a vocabulary nobody has agreed

**Lane C · Product Office · 2026-08-05.** Product Owner directive: *"Treat this as a **foundational reusable capability**, not as an implementation detail of TASK-406… **the objective is not to unblock TASK-406.**"*

**Produced by [Product-Led Domain Discovery](442-product-led-domain-discovery.md).** **Measured against `origin/integration` @ `f183197`. Nothing is implemented and no lane is named.**

---

# 0 · Four findings, before the assessment

## ① The window is open, and it is open by days

**[TASK-406](../BACKLOG.md) is `IN PROGRESS` with Lane B right now**, and its acceptance criterion is ***"the backtest reports both cohorts, never in-ICP alone."***

> **A backtest that reports *in-ICP versus outside* requires a predicate that decides which an account is.** **That predicate is the capability this document is about, and it does not exist.**

**Measured on `origin/integration`: no matching code has landed.** `git log` over `commercial_profile` shows readers, competitors and committee work and nothing else. **So the first copy has not been written yet** — and *"whichever module happened to need it first"* is a live risk with a name and a date rather than a general concern.

## ② `commercial_profile` cannot own this, and the repository already enforces that

**Not a judgement. An import contract, with a reason, and a test that fails:**

> **`"commercial_profile declares; it never reads the pipeline"`** — `pyproject.toml`, forbidding **`knowledge_graph`** among ten others, *"because if it could read a signal, a score or an opportunity, **'declaration' would quietly become 'declaration informed by our own conclusions'** — the module would start computing, and the one boundary it has would be gone."*

**Matching compares a declaration to what the pipeline observed. The declaring module is mechanically forbidden from seeing the second half.** **The product owner's instinct — *"it should not belong solely to `commercial_profile` simply because TASK-406 happens to need it first"* — is confirmed by an enforcement written before the question was asked.**

## ③ The module already reasoned about this, about a different match, and reached the same answer

**`commercial_profile/domain/competitors.py`, on why it cannot resolve a competitor's technology:**

> *"**This module could not resolve one even if it should.** The import contract… forbids reading the Knowledge Graph. **That is the boundary working, not a gap** — matching *"Salesforce"*, *"salesforce.com"* and *"SFDC"* to one technology is exactly the job the graph exists to do, and **a second resolver here would be free to disagree with it.**"*

**A module arguing itself out of owning a matcher, in a docstring, months before this directive.** **§1 is short because this kind of thing is everywhere.**

## ④ ⚠️ The hard problem is not the predicate. It is that the two sides do not speak the same language.

| | |
|---|---|
| **What the customer declares** | `ProductIcp.industries: tuple[str, ...]` — **free text**, and `validate_criterion_list` says so: ***"Validated, never normalised. The customer's own capitalisation and spacing are part of what they said, and a module that records has no business tidying it."*** |
| **What the pipeline observes** | **`INDUSTRY`, `COUNTRY`, `EMPLOYEE_COUNT`** — canonical claim attributes in `provider_normalization/domain/vocabulary.py`, produced by an anticorruption layer |

> ### **A customer types `SaaS`. A provider reports `Computer Software`. String equality returns `False`, and the account silently drops out of its own ICP.**
>
> **This is the finding that makes the capability foundational rather than incidental.** **Scoped as *"a predicate TASK-406 needs"*, it is a comparison. Scoped honestly, it contains a vocabulary-resolution problem** — and resolution is a competence this repository already has, in exactly one place, deliberately.

---

# 1 · Reuse audit — everything matching-shaped that already exists

**Five, and not one of them is the missing capability. Each is evidence about the *shape* the missing one must take.**

| | What it matches | Verdict |
|---|---|---|
| **`knowledge_graph` — `ResolutionRule` · `MatchStrength` · `ResolutionOutcome` · `NameAgreement` · `SelectedName` · `IdentityState`** | ***Is this provider record the same company as that one?*** **Identity.** | ✅ **Reuse the discipline, and probably the mechanism** — §4. **This is the repository's resolution competence and there must not be a second** |
| **`signal_engine` — `Relevance` · `SignalProfile` · `ProfileEntry`** | ***How central is this hypothesis to this workspace?*** | ✅ **Reuse the discipline.** A declared category, never computed |
| **`sales_engagement/domain/fit.py` — `FitDimension`** | ***Which of the customer's products fits this account?*** | ⚠️ **A named consumer, and it already wrote this row down** — §5 |
| **`commercial_profile` — `ProductIcp` · `SegmentCriteria`** | **Nothing. They *declare* criteria and evaluate none of them** | ⚠️ **And they are already two representations of one criteria set** — `SegmentCriteria` says so: *"Identical in substance to `ProductIcp` minus the product… the validation is the same function"* |
| **`commercial_profile` — `TargetAccount`** | **Nothing. `id` and `name`, and *"deliberately two fields"*** | ⛔ **Target accounts are *declared*, never *discovered*** |

## The two disciplines this capability inherits, and they are ratified

> ### ⛔ **A match is a category with reasons. It is never a number.**
>
> **`MatchStrength`** — *"Named `MatchStrength` rather than `confidence` deliberately… **a semantic category, never a number** (permanent invariant, ratified 2026-07-29)."*
> **`Relevance`** — *"declared per workspace and never computed — **the same discipline as `MatchStrength`, and for the same reason: a number invites weighting, weighting invites thresholds, and a threshold here would be a propensity judgement in the wrong module.**"*

**This is the single most important constraint on any answer.** **An ICP match that returns a score becomes a second propensity model**, competing with `buying_score_engine`, which already holds *"how much does this matter"* in a reviewed catalog with weights and postures. **Two scorers disagree the first time either changes**, and the disagreement would be about a customer's commercial judgement.

**So the output shape is fixed before the owner is chosen: *per criterion, does it hold, and on what evidence.*** **Never a fit score, never a ranking, never a threshold.**

---

# 2 · The decomposition — this is not one capability

**The directive asks for *"the minimum reusable foundation."* The minimum is smaller than it looks, because three separable problems are currently hiding inside one phrase.**

| | Problem | Question | Home |
|---|---|---|---|
| **M1** | **Criterion vocabulary agreement** | *Does the declared term `SaaS` denote what the observed term `Computer Software` denotes?* | **`knowledge_graph`.** ⚠️ **It resolves *entities*, not *attribute values* — this is new work in an existing competence** |
| **M2** | **Criterion evaluation** | *Given resolved values and a declared criteria set, does each criterion hold, and why?* | **A pure function over `commercial_profile`'s own vocabulary** — §3 |
| **M3** | **Selection · discovery** | *Which accounts satisfy this ICP?* | **The consumer's**, over M2. ⚠️ ***"Discovery is not built"*** — [50 §23](50-sales-engagement.md) |
| **M4** | **Measurement** | *How well does this criterion predict closed-won?* | **[TASK-406](../BACKLOG.md), and it is a consumer of M2 rather than a sibling of it** |

> **Conflating M2 and M4 is what makes matching *"an implementation detail of TASK-406"*. Conflating M1 and M2 is what makes it look easy.** **Naming them separately is most of the value of this document**, because three of the four already have an obvious home and only one is genuinely open.

---

# 3 · Ownership — the recommendation, and it needs no new bounded context

> ## **M2 is a pure function in `commercial_profile`'s domain, published through `public/`, that reads nothing.**

**The move that makes this possible, and it is the whole insight:**

> **The import contract forbids `commercial_profile` from *reading* the pipeline. It does not forbid it from being *given* facts.**
>
> **`evaluate(criteria, attributes) -> tuple[CriterionVerdict, ...]`** — a comparison whose inputs are both parameters. **It imports nothing, queries nothing, and knows no module.** **The caller supplies the attributes, and the caller is whoever already reads the graph.**

### Why here, and it is explicitly *not* because TASK-406 needs it first

| | |
|---|---|
| **§6 — *"a port belongs to the module that owns the language it represents"*** | **A *criterion* is `commercial_profile`'s language.** `industries`, `countries`, `EmployeeRange`, `MAX_CRITERIA`, `validate_criterion_list` and the rule that a criteria set *"describes nobody in particular"* all live there and are already shared between two declarations |
| **§2 — *truth has exactly one authoritative representation*** | **The alternative is a second copy of the criteria vocabulary in whichever module evaluates.** **`SegmentCriteria` shows exactly how that begins** — two representations already, kept honest only by sharing one validator |
| **§2 — *the least powerful author capable of producing it correctly*** | **A pure comparison over supplied values is the least powerful thing that can produce a verdict.** No query, no I/O, no ordering, no hidden input |
| **The import contract** | ✅ **Unchanged. Zero new edges, because nothing is read.** `lint-imports` needs no amendment — the strongest possible evidence that a boundary is not being bent |
| **The Change Budget** | 🟠 **`commercial_profile`'s own `public/`** — a lane may do it and announce it. **Not 🔴, because no new bounded context and no new dependency appears** |

### The alternatives, measured rather than dismissed

| | Why not |
|---|---|
| **`opportunity_engine`** *(where [C-328](../LANE_COORDINATION.md) put the measurement)* | **It is the right home for M4 and the wrong one for M2.** Every future consumer — ICP Builder, Copilot, Segments, Analytics, agents — would depend on the **opportunity** module for a question with no opportunity in it. **That is the "needed it first" trap relocated, not avoided** |
| **`buying_score_engine`** | **Owns commercial judgement, and that is precisely the risk.** `MatchStrength`'s invariant exists to stop a match becoming a weight; putting the matcher inside the scorer removes the only thing standing between them |
| **`knowledge_graph`** | ✅ **Correct for M1 and wrong for M2** — evaluating a *commercial* criterion is a judgement about a customer's market, and the graph is deliberately free of commercial semantics |
| **A new bounded context** | ⛔ **Not justified.** 🔴, an ADR, a module — **for a pure function over one module's existing vocabulary.** *"Missing bounded contexts: only if truly justified"* |

---

# 4 · M1 — the vocabulary problem, and what it must not become

**M2 is only useful if the values it compares mean the same thing. Today they cannot be assumed to.**

| | |
|---|---|
| **The competence exists** | `knowledge_graph` owns resolution: `ResolutionRule`, `MatchStrength`, `NameAgreement`, `SelectedName`, `ResolutionOutcome`, `ResolutionReason` |
| **It is aimed elsewhere** | **It resolves *entities* — is this record that company. It does not resolve *attribute values*** — is `SaaS` the same industry as `Computer Software` |
| **⛔ What it must never become** | **A model.** *"If the system already knows something deterministically, never ask a model to invent it again."* **An industry synonym set is a reviewed catalog** — a domain expert signs it, a diff shows the change, and it sits exactly where the Signal Catalog and the scoring catalog already sit on the least-powerful-author ladder |
| **✅ The honest interim** | **Exact agreement, and say so.** A criterion that cannot be evaluated reports **unmeasured**, never *false* — the same discipline [TASK-406](../BACKLOG.md) already carries: *"a criterion no outcome data supports says so rather than reporting `1.0×`"* |

> **This is the one part that could genuinely be got wrong quietly.** **A matcher that returns `False` where it means `I could not tell` produces a smaller ICP, a cleaner-looking backtest and a wrong answer** — and it is invisible from the result, exactly like the meter that silently stops recording in [TASK-412](../BACKLOG.md). **`unmeasured` must be a value in the type, not a convention.**

---

# 5 · Consumer audit — repository-wide, and the directive's list was not complete

**✅ = confirmed against source or an approved screen. Sixteen consumers; the directive named fourteen.**

| Consumer | Needs | |
|---|---|---|
| **ICP Builder** *(wave 3)* | **In-ICP vs outside cohorts** — the screen's own words | ✅ M2 · M4 |
| **[TASK-406](../BACKLOG.md) backtest** | *"the backtest reports both cohorts"* — **`IN PROGRESS` today** | ✅ **M2, now** |
| **`sales_engagement` — `FitDimension`** | ⚠️ **Already written down**: *"**ICP match** — needs a record of which ICP discovered this Target Account. **Discovery is not built.**"* [50 §23](50-sales-engagement.md) | ✅ M2 · M3 |
| **Account 360** | Which product fits, and why | ✅ M2 |
| **Companies · Segments** | *"Saved views and segments"* — **and *in my ICP* is the first filter anybody writes** | ✅ M3 · **[TASK-433](../BACKLOG.md)** |
| **Executive Dashboard** | Coverage of ICP vs outside | ✅ M3 |
| **Opportunity prioritization** | Fit as one input among many | ✅ M2 |
| **Buying Score** | ⚠️ **Consumes a *verdict*, never a *score*** — §1 | ✅ M2, **bounded** |
| **AI Copilot · AI Reasoning** | **Grounding.** *"Why is this account a fit"* must cite criteria, not assert fit | ✅ M2 |
| **AI Research** | **Cohort research** — [416](416-ai-research-scope-gap.md): *"researches a cohort and reports what its members share."* **A cohort *is* a match result** | ✅ M3 |
| **Recommendations** | `Recommendation.reason` — the *why now* | ✅ M2 |
| **Reports · Analytics** | In-ICP as a dimension | ✅ M2 |
| ⚠️ **Workflow Automation** *(found, not listed)* | **[ADR-0402](adr/0402-a-rule-is-data.md): *a rule is a condition tree*. *"Account is in ICP"* is a condition** — and a rule engine that re-implements it is the second matcher | ✅ M2 |
| ⚠️ **`provider_platform` target-account sync** *(found)* | **Target accounts are declared today. M3 is what would let them be discovered** | M3 |
| ⚠️ **Epic E1 — a customer's CRM** *(found)* | **[TASK-402](../BACKLOG.md): accounts arriving from a customer's own system must be classified on arrival** | M2 |
| ⚠️ **Global Search** *(found)* | Filtering results by fit | M3 |

> ## Sixteen consumers, four of them not on anybody's list, and **one of them is being implemented today.**
>
> **This is [441 §5 · P-01 · Domain precedence](441-people-roadmap.md) at the largest scale it has been measured.** **People had four dependents. This has sixteen.**

---

# 6 · Provider-neutral, and implementation-specific

| **Provider-neutral — permanently** | **Implementation-specific — correctly** |
|---|---|
| **The criterion vocabulary.** `industries`, `countries`, `EmployeeRange` are the customer's words | **Which provider supplied the observed value**, recorded as provenance and **never consulted for a decision** (§10, vendor neutrality) |
| **The verdict shape.** Category + reasons, never a score | **The claim's freshness and its evidence chain** — already the graph's |
| **The synonym catalog.** A reviewed artifact, versioned like the Signal Catalog | **A vendor's own industry taxonomy** — stays inside its mapper. *"Each mapper reads only its own vendor's shape"* |

> **The anticorruption layer already does the hard half.** `INDUSTRY` is canonical *because* a mapper normalised it. **M1 is not a second normaliser — it is agreement between the customer's vocabulary and the canonical one**, which is a different problem and has never been solved anywhere in this repository.

---

# 7 · Sequencing that minimises refactoring

| | Step | Trigger | Why this order |
|---|---|---|---|
| **1** | **Publish `IcpReader` and an `IcpView` from `commercial_profile/public/`** | **Now** | ⚠️ **Thirteen views are published and *not one is the ICP*.** **No module can read the criteria at all today** — every consumer above is blocked on one missing read port, and [ADR-0403](adr/0403-signal-engine-reads-a-declaration.md) is the ratified precedent for exactly this shape |
| **2** | **M2 — `evaluate(criteria, attributes)`, pure, with `unmeasured` in the type** | With step 1 | **Reads nothing, adds no edge, needs no ADR.** **This is the minimum reusable foundation the directive asked for** |
| **3** | **[TASK-406](../BACKLOG.md) consumes M2 instead of inlining a predicate** | ⚠️ **Now, or the first copy exists** | **The only time-critical row in this document** |
| **4** | **M1 — the synonym catalog, reviewed** | When exact agreement is measurably losing accounts | **Do not build it speculatively.** Step 2's `unmeasured` makes the gap *visible*, which is the trigger |
| **5** | **M3 — discovery** | When a screen selects rather than filters | **[50 §23](50-sales-engagement.md) already classifies this as a *Repository* trigger** |

---

# 8 · What this asks for, and what it does not do

**Nothing implemented · nothing assigned · no module created · no ADR drafted · no ownership changed · no queue file touched · no task's position altered.**

**One row is time-critical and it is not a ruling**: **[TASK-406](../BACKLOG.md) is being implemented today and its backtest needs the predicate.** **The recommendation is that step 1 and step 2 precede it** — which is the same shape as [D-074](../DECISION_REGISTER.md), arriving from a different direction, and **the second time this week that a foundational concept was scheduled behind something that needs it.**

**The decision this contains is small**: **M2's home**. **Everything else in this document is measurement, and every alternative was tested against source rather than argued.**

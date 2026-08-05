# 445 · AI Copilot — screen-by-screen traceability audit

**Lane C · Product Office · 2026-08-05.** **The first audit under [D-078](../DECISION_REGISTER.md)'s Screen-by-Screen Domain Traceability protocol** ([`PRODUCT_OFFICE.md` §5f](../PRODUCT_OFFICE.md)).

**Screen 12 of 16** ([410](410-approved-ui-specification.md)) — *"17 surfaces, one contract."* **Wave 2, and the next screen implementation reaches.**
**Measured against `origin/integration` @ `6b7b04e`. Nothing implemented, no lane named.**

---

# 0 · ⚠️ The evidence bound, stated before the matrix

**The directive asks for every badge, chip, tooltip, loading state and icon. I can evidence none of those, and saying so is the first finding.**

> **The approved designs live in an external design project** — `1d043179-1ee9-4c9f-b59e-592e04297cad`, read in full by Lane C on 2026-08-04 and recorded in [410](410-approved-ui-specification.md). **The repository holds the *inventory* and the *assertions extracted from it*, not the screens.**
>
> **Section-level detail exists for exactly one screen: Account 360, whose 27 sections [414](414-wave-1-account-360.md) enumerated.** For the other fifteen, **the repository records what the design project asserts, not what it draws.**

**So every row below cites its evidence, and no row invents a UI element.** **A matrix row for a badge I cannot see would be worse than a missing row** — it would put a fabricated requirement into the one document implementation is meant to trust.

> ## **The audit *is* the extraction.** **Each screen's matrix becomes the repository's record of that screen's elements**, and it can only be as deep as the evidence reaching the repository. **Deepening it is a real deliverable and it is named in §6.**

---

# 1 · The traceability matrix

**Seven columns, per [D-078](../DECISION_REGISTER.md).** ✅ exists · 🟡 extend · 🟠 conflicts · 🔴 missing.

| UI element | Business meaning | Source of truth | Audit | Owner | Consumers | Priority |
|---|---|---|---|---|---|---|
| **The answer** | A grounded explanation of a conclusion Signora already reached | **Domain aggregate** — `DecisionPackage` | ✅ **Exists.** `domain/decision.py` · `package.py`, 19 files | `ai_reasoning_engine` | 17 surfaces · Account 360 · AI Research | — |
| **Every citation, as a link** | A reference resolving to a reading that exists | **Value object** — `EvidenceRef.token` / `.parse` | ✅ **One owned grammar.** [ADR-0031](adr/0031-evidence-citation-protocol.md) `ACCEPTED`, `domain/rendering.py` is its display form | `ai_platform` | Every AI surface | — |
| **Confidence, *with its basis*** | Not a number — the facts that produced a level | **Value object** — `SupportBasis` | ✅ **Exactly this.** *"The facts that produced a level, **so the level never stands alone**… nothing here is new information"* | `ai_reasoning_engine` | 17 surfaces | — |
| **What it read** | The closed evidence set the answer is checkable against | **Aggregate** — `EvidenceSet` · `GroundedOutput` · `GroundingReport` | ✅ **Built, with a validator that never repairs** | `ai_platform` | Every AI surface | — |
| **A refused answer** | *An answer whose citation does not resolve is not shown at all* | **Domain rule** — `Violation` · `UngroundedOutputError` | 🟡 **The refusal happens; the *record* is not surfaced.** [411](411-ui-convergence-assessment.md) lists *"recorded refusals"* as an AI Research gap and **the same gap is here** | `ai_platform` | AI Copilot · AI Research | **Both wave 2–3** |
| **The question box** | A customer asks in their own words | **Interface route** | 🔴 **Missing — the *route*, not the layer.** ⚠️ **[404](404-epic-g-copilot.md) says *"`ai_reasoning_engine` has no `interface/` directory at all"* and that is now stale**: both it and `sales_engagement` have one, built by TASK-204 and TASK-205. **What is absent is the *ask* route** | `ai_reasoning_engine` | AI Copilot | **Wave 2 — this is the screen's front door** |
| **The six verbs** — *Explain · Summarize · Predict · Recommend · Generate · Reason* | The closed taxonomy of what a customer may ask for | **Value object** — an intent enum | 🔴 **Missing entirely.** No verb, intent or capability taxonomy exists in any `domain/` layer | ⚠️ **Undecided** — see §3 | **All 17 surfaces**, by construction | **Wave 2** |
| **17 surfaces, one contract** | The same guarantees wherever the assistant appears | **Platform capability**, or 17 endpoints | 🟠 **Architecturally unresolved** — §3 | ⚠️ Undecided | Every screen with an AI surface | **Wave 2** |
| **"Inherits scope"** | Period · region · segment · owner, applied before the module renders | **Platform service** — shell scope | 🔴 **[R-02](../DOMAIN_DISCOVERY_REGISTER.md)** — `saved_view`, `monitored` return zero repository-wide | ⚠️ Undecided — **[TASK-433](../BACKLOG.md)** | **5 screens named, all 16 inherit** | **Ruling due** |
| **"Proposes rather than commits"** | A suggestion a human turns into an action | **Aggregate** — `Recommendation` | 🟡 **Half built.** `Recommendation` proposes and **`MACHINE_AUTHORED = frozenset({Stage.TRACKING})`** makes it structural. **The *apply* half is [R-03](../DOMAIN_DISCOVERY_REGISTER.md)** | `sales_engagement` | **6 screens** | **[TASK-431](../BACKLOG.md)** |
| **"Attributable and reversible"** | Who caused it, and taking it back | **Platform capability** | 🟡 **Attribution ✅ — `actor_id` in 37 files. Reversal 🔴** — `undo`, `revert`, `24 hour` return zero | ⚠️ Undecided — **[TASK-431](../BACKLOG.md)** | **6 screens** | **Ruling due** |
| **Answer appears beside the ledger it cites** | The explanation sits next to the number it explains | **Aggregate** — the Contribution Ledger | ✅ **Built.** *"the authoritative explanation of a score"* | `buying_score_engine` | Account 360 · Copilot | — |
| **A released model behind it** | The answer came from a pairing that was measured | **Domain rule** — `Prompt.is_released_for` · `require_model` | 🟠 **The mechanism exists and `reasoning@1` has no release.** **[TASK-013](../BACKLOG.md) / [C-222](../LANE_COORDINATION.md)** — *"the Decision Package would refuse at runtime"* | `ai_platform` | Copilot · every reasoning surface | **Blocks Epic G** |

> **Twelve elements. Four ✅, four 🟡, two 🟠, two 🔴** — and **not one of them needs a new intelligence capability.** **The module, the grammar, the validator, the ledger, the harness and the prompt are all built. What is missing is the way in, and the vocabulary of asking.**

---

# 2 · Workflow — *a customer asks a question*

**The directive requires workflows, not only fields.** **One workflow carries this screen.**

| | | |
|---|---|---|
| **Inputs** | A question, a scope, an account | 🔴 **Scope is [R-02](../DOMAIN_DISCOVERY_REGISTER.md)** |
| **Outputs** | A `DecisionPackage` with citations and a support basis | ✅ |
| **Business events** | ⛔ **None.** `ai_reasoning.completed` and `.failed` are catalogued | 🟡 **Nothing publishes an *asked* event** — so no timeline entry, no audit of what a customer asked, no usage record per question |
| **State transitions** | ⛔ **None — and correctly.** An answer is produced or refused | ✅ **Statelessness**: *"what the platform may remember: nothing"* |
| **Domain rules** | Every claim cites a reading that exists; **refusal is the design** | ✅ |
| **Validation** | `grounding.py` — *"it validates; it never repairs"* | ✅ |
| **Permissions** | `Resource.RESEARCH` distinguishes reading from spending a model call | 🟡 **No `Resource` for reasoning.** Research was separated *"so a reader does not become a spender"* — **the same argument applies here and nobody has made it** |
| **Side effects** | A model call, metered | ✅ `InferenceRecord` · `InferenceUsage` |
| **Notifications** | ⛔ None | ⏸ [ADR-0040](adr/0040-notifications.md) deferred |
| **AI interactions** | One structured single call — never agentic | ✅ **The module split is architectural** |
| **Background jobs** | ⛔ None, and deliberately — the answer is synchronous to the question | ✅ |
| **Audit** | ⛔ **What a customer asked is not recorded anywhere a person can read** | 🟡 **[R-07](../DOMAIN_DISCOVERY_REGISTER.md) audit surface** |

> ## The workflow finding, which the field matrix could not show
>
> **Two gaps only appear when the flow is read end to end: nothing records *that a question was asked*, and nothing distinguishes *reading an answer* from *spending a model call*.**
>
> **The second has a precedent one module over and it was deliberate**: `Resource.RESEARCH` exists *"because reading an account is free and asking for research spends a model call, and one resource could not express both **without making every reader a spender**."* **AI Copilot is 17 surfaces on pages every member reads.** **Without the same separation, mounting the assistant grants every member the ability to spend, on every page.**

---

# 3 · 🟠 The architectural question: is *17 surfaces, one contract* a platform capability?

**This is the row a field-by-field audit would have recorded as a UI detail.**

| | |
|---|---|
| **What the design asserts** | **One contract** — inherits scope, cites what it read, states confidence with its basis, proposes rather than commits, is attributable and reversible — **holding identically across 17 places** |
| **What "17 endpoints" would mean** | **17 chances for one of the five guarantees to be implemented differently**, and no way to check that they were not |
| **What the repository already does** | ✅ **The guarantees are already centralised** — `GroundedOutput`, `EvidenceRef`, `SupportBasis` and the validator are all one implementation. **The contract is *already* a platform capability in substance** |
| **What is genuinely undecided** | **Whether a surface is a parameter of one route, or 17 routes sharing a library** — and **who owns the verb taxonomy** that would make the first possible |

> **Recommendation: the verb taxonomy and the surface identifier belong to `ai_reasoning_engine`'s `public/`, and the 17 surfaces are consumers rather than variants.** **The reason is §2's rule** — *"a port belongs to the module that owns the language it represents"* — **and *Explain · Summarize · Predict · Recommend · Generate · Reason* is that module's language, not the frontend's.**
>
> ⚠️ **This is 🟠 and it is not Lane C's to decide.** **Raised as part of [C-419](../LANE_COORDINATION.md)** rather than assumed, because a wrong answer produces 17 implementations of five guarantees.

---

# 4 · Findings, in the ten categories

| | |
|---|---|
| **Existing and correctly modelled** | `DecisionPackage` · `EvidenceRef` + ADR-0031's single grammar · `SupportBasis` · `EvidenceSet`/`GroundedOutput`/`GroundingReport` · the never-repairing validator · the Contribution Ledger · `Prompt.is_released_for` · `InferenceRecord`/`InferenceUsage` · the reasoning/research module split |
| **Extension candidates** | **Recorded refusals surfaced** *(same gap as AI Research)* · **`Recommendation` gains its apply half** *([R-03](../DOMAIN_DISCOVERY_REGISTER.md))* · **an `ai_reasoning` `Resource`** |
| **Architectural evolution** | **17 surfaces — one route or seventeen** *(§3)* · **`reasoning@1` has no released model** *([TASK-013](../BACKLOG.md))* |
| **Missing foundational capabilities** | **[R-02](../DOMAIN_DISCOVERY_REGISTER.md) scope** *(all 16 screens)* · **[R-03](../DOMAIN_DISCOVERY_REGISTER.md) propose→apply→reverse** *(6 screens)* |
| **Missing workflows** | ⛔ **None.** The ask workflow is complete in design and lacks only its route |
| **Missing entities** | **A verb taxonomy** — the six verbs have no representation anywhere |
| **Missing business events** | **Nothing records that a question was asked.** No timeline entry, no audit, no per-question usage |
| **Missing permissions** | **No `Resource` for reasoning** — `Resource.RESEARCH` made exactly this separation and the argument was *"without it every reader becomes a spender"* |
| **Missing projections** | ⛔ **None.** Statelessness forbids a stored answer, and that is correct |
| **Missing platform capabilities** | **The contract-as-capability question** *(§3)* |

---

# 5 · Reuse — audited before anything was proposed

**Eight searches, per the protocol:** bounded contexts · platform capabilities · domain concepts · value objects · workflows · business events · projections · existing ADRs.

**They rejected five candidates.** **A citation format** — one owned grammar, and [404](404-epic-g-copilot.md) records that a second cost three invalidated releases. **A prompt store** — fingerprinted registries exist. **A model adapter** — *"others arrive with real callers"*. **A second explanation of a score** — the Contribution Ledger is authoritative. **A conversation or answer store** — ⛔ **forbidden by Statelessness**, and [437 §2.1](437-ai-platform-future-epic.md) ruled it.

**What survived: a route, a verb taxonomy, an event, a `Resource`, and one architectural question.**

---

# 6 · What this produces

| | |
|---|---|
| **[C-419](../LANE_COORDINATION.md)** | **The verb taxonomy and the surface model** — one item, because the second cannot be answered without the first |
| **⚠️ [404](404-epic-g-copilot.md) corrected** | Its *"no `interface/` directory at all"* is stale — **both modules have one.** **The gap is the *ask* route** |
| **A deliverable named, not created** | ⚠️ **Fifteen of sixteen screens have no section-level record in the repository.** **Extracting each screen's elements is what makes this audit possible for them**, and it is the constraint §0 names. **Recommended as the next Product Office activity, screen by screen, ahead of each wave** |

**No backlog row.** **Everything 🔴 here is already carried by [TASK-431](../BACKLOG.md), [TASK-433](../BACKLOG.md), [TASK-013](../BACKLOG.md) or [TASK-202](../BACKLOG.md)** — *"success is not measured by the number of backlog items created."*

---

# 7 · What this document did not do

**Nothing implemented · no lane named · no wave reordered · no module created · no ADR drafted · no queue file touched · no backlog row added.**

**And it invented no UI element.** **Where the repository does not record what the screen draws, this document says so** rather than filling the gap with a plausible one.

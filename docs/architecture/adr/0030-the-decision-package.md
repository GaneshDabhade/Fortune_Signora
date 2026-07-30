# ADR-0030 — The Decision Package: what M9 produces, and who authors each part

> Status: **ACCEPTED — 2026-07-30.** Ratified with the partitioning and all nine decisions as written, including the six that modified the original request. **No code has been written against it yet.**
> Deciders: Product Owner · Architecture Review Board
> Amends: [29-ai-reasoning-engine.md](../29-ai-reasoning-engine.md) (proposed, not yet ratified)
> Anchors: [28-ai-platform.md](../28-ai-platform.md) · [04-modules.md](../04-modules.md) · [21-intelligence-pipeline.md](../21-intelligence-pipeline.md) · [26-buying-score-engine.md](../26-buying-score-engine.md) · [27-opportunity-engine.md](../27-opportunity-engine.md)

## Context

The M9 proposal asked *"what should a seller understand that the pipeline did not already compute?"* The product owner has reframed the success criterion:

> Not *"can the model produce a conclusion?"* but ***"will a customer trust the conclusion enough to act on it?"***

**That reframing is correct and it changes the module's shape.** A `ReasonedConclusion` — text plus citations plus a derived support category — is sufficient for an engineer auditing the pipeline and insufficient for a CRO deciding whether to spend a quarter's attention on an account. The eleven questions a real user asks (*why · why now · why not earlier · what contradicts this · could it be wrong · what would change it · what does it not mean*) are the actual requirements, and a proposition answers roughly two of them.

So the Decision Package is accepted in principle. This ADR is about **what it must not become**, because as enumerated it is roughly ten fields, most of them prose, and **prose from a model is the one thing in this system that cannot be trusted without a check.** Ten free-text fields is ten times the hallucination surface and ten times the evaluation burden, on a module whose entire purpose is to be trustworthy.

## Design Principle: Deterministic Explainability

**Ratified 2026-07-30. This is the principle the rest of the ADR applies.**

> **The Decision Package exists to make conclusions explainable rather than merely persuasive.**
>
> Whenever the platform already owns a fact deterministically, that fact is **derived rather than regenerated** by a language model.
>
> Consequently most Decision Package fields are deterministic, with model-authored content limited to the **grounded conclusion and its stated reasoning**.

This minimizes hallucination surface, reduces evaluation burden, improves reproducibility, and — the reason that outranks the others — **allows customers to independently validate Signora's conclusions.**

The general form, recorded in CLAUDE.md §2: *if the system already knows something deterministically, never ask a model to invent it again.* Use AI only where inference is genuinely required; everything else comes from deterministic computation, versioned configuration, or reviewed repository artifacts.

**The general rule this follows** (CLAUDE.md §2, ratified 2026-07-30):

> **Every field has the least powerful author capable of producing it correctly.** The database owns timestamps, code owns derived facts, domain experts own static knowledge, AI owns inference. If a less powerful component can produce a field correctly, it owns that field.

Power means *freedom to be wrong in ways nothing can check*. The partition table below is that ladder applied field by field, which is why it reads as a demotion of the model rather than a restriction on it: the model keeps exactly the rung nothing else can reach.

**The four questions that assign every field:**

| If the information… | Then it is… |
|---|---|
| already exists elsewhere in the platform | **derived** |
| is static and domain-expert knowledge | **authored once in the catalog, and versioned** |
| is operational | **computed** |
| genuinely requires inference | **model-authored, and grounded** |

Only the last is a model's job: *derive a grounded conclusion, and explain that conclusion in natural language.* Everything else stays deterministic.

**Persuasion is explicitly not the goal.** A fluent, confident, well-written conclusion that a customer cannot check is worse than a plainer one they can — because the first is trusted without grounds and the second is verified. This is the same reasoning that removed the un-cited `summary` from M8's output type: the sentence with the most rhetorical weight must carry the most evidence, not the least.

---

## The central decision: partition the package by author

The insight that makes the Decision Package tractable — and the one this ADR exists to record:

> **Most of the Decision Package should not come from the model at all.**

Each part is assigned to the authority that can actually be held to it. Fifteen parts: **three** are model-authored and grounded, **nine** are derived deterministically from facts the pipeline already owns and already records, **two** are repository artifacts reviewed like code, and **one** is not M9's.

*(The list grew from the ten originally enumerated because the temporal questions — freshness, why now, why not earlier, what changed — turned out to be separable fields rather than parts of a narrative. Every one of the five additions is derived, which is the principle above producing more transparency at no additional model cost.)*

| # | Part | Authored by | Why |
|---|---|---|---|
| 1 | Executive Summary | **Model**, grounded | Compression is a language task |
| 2 | Proposition | **Model**, grounded | The conclusion is the reasoning |
| 3 | Supporting Evidence | **Derived** | The citations *are* the evidence; nothing to author |
| 4 | Reasoning Chain | **Model**, grounded — *and renamed* | See Decision 2 |
| 5 | Contradicting Evidence | **Derived** | Already computed upstream. See Decision 3 |
| 6 | Support | **Derived** | Ruling 1, accepted and unchanged |
| 7 | Assumptions | **Derived** from provenance | See Decision 4 |
| 8 | Limitations | **Repository artifact** | See Decision 5 |
| 9 | Suggested Validation | **Repository artifact** | See Decision 5 |
| 10 | Suggested Next Action | **Not M9** | See Decision 6 — the one firm disagreement |
| 11 | Evidence Freshness | **Derived** | `EvidenceState` + per-provider refresh times, already recorded |
| 12 | Why Now | **Derived** | `BuyingScore.trigger`. See Decision 9 |
| 13 | Why Not Earlier | **Derived** | `basis_at`, and the superseded score, still readable |
| 14 | What Changed | **Derived** | `delta` and `trend` against the superseded score |
| 15 | Alternative Readings | **Derived** | Signal types evaluated and not supported. See Decision 7 |

The consequence is the point: **the model authors three fields out of fifteen.** Evaluation covers three. Twelve are reproducible, explainable and testable without a model — and the derived ones are the fields customers will trust *most*, because they can be recomputed and defended rather than believed.

This is the north star applied literally — the richer artifact makes the architecture *smaller*, because most of it turns out to be a projection of facts the pipeline already holds.

---

## Decision 1 — the Executive Summary is a grounded statement, never a string

**Agreed, with a constraint that is not optional.**

M8 removed exactly this field once already. `GroundedNarrative` originally carried `summary: str`, and Departure 4 deleted it: *"the one sentence a reader looks at first would have been the one statement exempt from grounding."*

An Executive Summary understandable in seconds is the field with the **highest** trust leverage and therefore the **least** entitlement to an exemption. It is a `GroundedStatement` — text plus citations — like every other sentence. If a summary cannot be written while citing its evidence, that is a signal the conclusion is thinner than it reads.

## Decision 2 — store the reasoning chain, and name it truthfully

**Agreed on storage. Challenged on naming, and the challenge matters for exactly the reasons storage was requested.**

Storing it is right, and for the stated reasons: historical reproducibility, auditability, governance, and an explanation six months later that does not depend on a second model call. That is already the ratified *materialized AI artifact* category.

But **"the logical path from evidence to conclusion" is a claim we cannot support.** A language model has no introspective access to its own computation. What it emits when asked to explain itself is a *plausible account* generated alongside the answer — post-hoc rationalisation, not a causal trace. This is well established, and it matters here more than anywhere: the field is being stored **for audit and governance**, and an audit record that misdescribes its own nature is worse than an absent one. It would be a false claim sitting in the customer-visible product, which is the §2 defect in its most expensive form.

**Proposed:** the field is `stated_reasoning` — *"the reasoning Signora stated for this conclusion"* — and the documentation says plainly that it is the explanation offered, not a trace of how the conclusion was computed. Every step remains a `GroundedStatement`, so each step's evidence is real even though the ordering is narrative.

Nothing is lost by naming it honestly. Everything the product owner wants from it — explainability, audit, defence, debugging — works identically. What is avoided is a governance artifact that asserts a causal claim under scrutiny it cannot survive.

## Decision 3 — contradicting evidence is supplied *to* the model, never discovered *by* it

**Agreed on necessity. Disagreed on mechanism, and the disagreement improves it.**

Asking a model *"what contradicts this?"* produces something plausible. It will find contradictions where none exist and miss the one that matters, and neither failure is detectable from the output.

**Signora already knows the answer deterministically.** `BuyingScore.contested` is computed, `dissenting_signal_ids` **names** the outweighed reading rather than counting it, and this exists precisely because *the Buying Score Engine prioritizes; it never resolves* (ratified 2026-07-29). Opposing hypotheses never cancel arithmetically — they survive, named, all the way to this module.

So contradiction is an **input** to reasoning, present in the closed evidence set, not an output of it. The model's job is to *restate* the contradiction it was handed, which grounding can check. Its job is not to *find* one, which nothing can check.

*"If none exists, state that explicitly"* becomes derived and reliable: the score either is contested or is not, and that fact is recorded.

**And it becomes enforceable:** *if the originating score is contested, the reasoning result must cite at least one dissenting signal.* A reasoning result over a contested account that reads as though nothing disagreed has destroyed what six pipeline stages preserved.

## Decision 4 — assumptions are derived from the provenance chain

**Agreed on value. Disagreed on source.**

Model-authored assumptions are ungrounded propositions — the precise thing the stop condition forbids — and they are unfalsifiable and unevaluable. A model asked what it assumed will produce a reasonable-sounding list with no relationship to what actually shaped the answer.

**The pipeline's real assumptions are already recorded, and they are the ones that matter:**

- which providers supplied the evidence, and when each was last refreshed
- the workspace's **own** signal profile version — *why it matters here* is the workspace's configured reading, not a universal truth
- the scoring model version and its ceiling
- the business event taxonomy version
- evidence freshness, and `EvidenceState` (`current` · `cooling` · `stale`), already derived and never stored

Every one is deterministic, already carried, and genuinely load-bearing. *"This rests on Apollo headcount last refreshed nine days ago, under your team's own relevance configuration v3"* is a far more useful and more defensible assumption than anything a model would compose — and it is recomputable.

## Decision 5 — limitations and suggested validation are repository artifacts, per signal type

**Agreed on both. Disagreed that either belongs to a per-call model output.**

*"What this does not mean"* is **stable per signal type**, not per account. What `DISPLACEMENT_OPPORTUNITY` does not imply is the same on Tuesday as on Wednesday and the same for Northwind as for Contoso. Generating it per call means paying for it every time, evaluating it every time, and getting a subtly different answer every time — for a sentence that should be identical.

Same for validation: *how a human disproves a displacement signal* is a property of the signal type, authored once by someone who understands it.

**Proposed:** both live in the signal catalog as reviewed repository artifacts, exactly as the business event taxonomy, the scoring model and the opportunity policy already do — *taxonomy is data; rules are code*, the M4 split. The Decision Package **composes** them by signal type; the model never writes them.

This is strictly better on every axis the product owner named: identical across accounts (so benchmarks compare), reviewable by a domain expert rather than a prompt engineer, free at inference time, and impossible to hallucinate.

## Decision 6 — Suggested Next Action does not belong to M9

**This is the one firm disagreement, and I want to be direct about it.**

Three ratified statements place it elsewhere:

- [04-modules.md](../04-modules.md), Recommendation Engine: *"Converts AI Reasoning Engine output and opportunity context into concrete, actionable **recommendations** for sales users"* — and AI Reasoning Engine explicitly *"does not own turning reasoning into a user-facing recommendation."*
- [21-intelligence-pipeline.md](../21-intelligence-pipeline.md), Stage 8: *"**Refuses:** what to do about it. What should Sales do, which message, and why the account scored this way belong to the Recommendation Engine, AI Reasoning, and the ledger."*
- [27-opportunity-engine.md](../27-opportunity-engine.md): ***Intelligence suggests. Humans commit.***

If M9 emits a next action, **M11 becomes a formatting layer around M9's prose.** The recommendation lifecycle M11 owns — open, acted-on, dismissed, expired — would then attach to text produced by a module that knows nothing about it, and the *"what should I do"* answer would have skipped the module built to be accountable for it.

It is also the field most likely to cause harm. A wrong explanation costs credibility; a wrong instruction costs a customer relationship. The module that issues instructions should be the one designed for that responsibility, with its own evaluation and its own lifecycle.

**What I propose instead, which I believe answers the real need:** *Suggested Validation* (Decision 5) already tells a user **what to check** — *"confirm the ERP retirement on their careers page"* — without telling them what to do commercially. That is the trust-building half, it is falsifiable, and it is legitimately M9's because it concerns the conclusion's own soundness.

`ai_reasoning.completed` is consumed by the Recommendation Engine. **M11 is where the action arrives, one milestone later, with an owner.**

## Decision 7 — competing hypotheses: yes, but derived, and never called "discarded"

**Agreed on value. The framing needs correcting for the same reason as Decision 2.**

A model listing alternatives it *"discarded"* is confabulating: it did not enumerate and reject them: it generated plausible alternatives after the fact. Storing that as an audit record of a decision process would be storing a fiction.

**But there is a real, deterministic competing-hypothesis set already.** The Signal Engine evaluates a global catalog against business events; for any set of events, some signal types were supported and others were **evaluated and not supported**. That is a genuine record of alternatives considered and rejected, by rules, with reasons — and `Contribution.counted` and `Contribution.reason` already carry exactly this shape for scoring.

**Proposed:** `alternative_readings` records signal types the same evidence was evaluated against and did not support, with the rule's own reason. Deterministic, honest, invaluable for debugging and evaluation as the product owner intends — and *more* useful than a model's guesses, because it reflects what the system actually considered.

Not shown to end users in M9. Recorded on the artifact.

## Decision 8 — Support and Reasoning Robustness stay separate, and only one is per-artifact

**Agreed that they are different concepts and must not collapse.** Support measures the *evidence*. Robustness asks whether another reasonable analyst would reach the same conclusion from it — a property of the **reasoning**, not the evidence.

**But I disagree that robustness can be a per-artifact field in M9**, on two grounds.

First, *"would another reasonable analyst agree?"* is precisely the question LLM-as-judge would answer, and that is rejected as a gate: change the judge and every historical value moves, so a genuine regression and a judge upgrade become indistinguishable.

Second, the only reproducible measure is **self-consistency** — run the same reasoning *n* times and measure agreement. That is a real technique and I recommend adopting it, but per-artifact in production it costs *n*× tokens and *n*× latency on every conclusion, and M8's own numbers put a single call at 43–52 s locally. **Paid on every account, forever, for one number.**

**Proposed:** robustness is measured **at evaluation time, over the golden set, as a property of the prompt** — `reasoning@1` is *n*-sampled per case and disagreement is reported in the evaluation record. It becomes a release criterion for the prompt rather than a field on each artifact. A prompt whose conclusions vary run to run does not earn its release; one that has earned it is robust for every artifact it subsequently produces.

If per-artifact robustness is wanted later, it is a product decision with a stated cost, and the harness will already have proven the measure.

## Decision 9 — *why now* is a pipeline question with a recorded answer, and must not go to a model

**Agreed that these four questions are fundamental to enterprise trust.** They are also, and this is the useful part, **already answered deterministically**:

| Question | Where the answer already lives |
|---|---|
| Why? | The contribution ledger — one entry per contributing business event |
| Why now? | `BuyingScore.trigger` — a signal arrived · a signal was superseded · configuration changed · **evidence aged** |
| Why not earlier? | `basis_at` — the evidence-derived moment the ledger's composition last changed; and the superseded score, still readable |
| What changed? | `delta` and `trend` against the superseded score; and the Observation Engine's own record of what changed, per provider |

Routing these through a language model would **replace a fact with a guess** — and a guess about causality, which is the least checkable kind. `trigger` exists specifically so a number that moved has an explainable reason; M4's ratified split (*taxonomy is data; rules are code*) exists so that reason is not invented.

**Proposed:** these four are derived and rendered, never generated. The model may *narrate* them — that is grounded restatement, which is M8's proven capability — but the answers come from the pipeline.

This is the clearest case of the reframing making the system simpler: the most trust-critical questions turn out to be the ones we can already answer exactly.

---

## Traceability — every customer question to its source

The checklist the Decision Package must satisfy, and where each answer comes from. **Two of the ten involve a model; eight do not.**

| A customer asks | Answered by | Author |
|---|---|---|
| What is the conclusion? | Proposition | Model, grounded |
| Why did Signora reach it? | Stated reasoning | Model, grounded |
| Which evidence supports it? | Citations on every statement | Derived |
| Which evidence challenges it? | `contested` · `dissenting_signal_ids` | Derived |
| How recent is the evidence? | `EvidenceState` · provider refresh times | Derived |
| Why did this appear now? | `BuyingScore.trigger` | Derived |
| What changed since last time? | `delta` · `trend` vs the superseded score | Derived |
| What does it assume? | Provenance chain — providers, profile version, model version | Derived |
| What are its limitations? | Signal catalog, per signal type | Authored once, versioned |
| How do I validate it independently? | Signal catalog, per signal type | Authored once, versioned |

**This table is the acceptance criterion for M9's customer-facing value**, and it is testable: a Decision Package that cannot populate a row has a defect, and every derived row can be asserted without calling a model.

---

## Consequences if ratified

**The artifact.** `ai_reasoning` (migration `0017`) stores the complete package — a materialized AI artifact, immutable, provenance denormalized, superseded by recency. Three model-authored grounded fields, eleven derived or composed. The six-month-old explanation is served from the row, never regenerated.

**Evaluation covers three fields, not ten.** Grounding and schema at zero, premise breadth, dissent acknowledgement on contested accounts, action abstinence, plus *n*-sample robustness. All deterministic except the last, which is deterministic in aggregate.

**Cost stays bounded.** One inference per reasoning result in production. The *n*-sampling cost is paid at evaluation time, on a golden set, by an engineer.

**M11 keeps its purpose.** The Decision Package is a *decision input*, not a decision. The action arrives with the module accountable for it.

**Accepted risks.** The three model-authored fields remain subject to the residual failure M8 named — correctly cited and mischaracterising. Support and robustness are new derived measures with no calibration history; their first release establishes a baseline, not a validated scale, and the documentation must say so. `alternative_readings` depends on the Signal Engine exposing evaluated-but-unsupported types through its `public/` contract, which is a graph question to confirm before implementation, not assume.

## Status

**Accepted 2026-07-30**, with the product owner's clarification recorded as the guiding principle above: the concern was never that M9 should generate *more* AI text, but that every customer-visible signal must be **defensible** — answerable with concrete, deterministic facts the platform already owns.

That clarification and the partitioning are the same idea reached from two directions, which is why the ADR needed no structural change to accommodate it.

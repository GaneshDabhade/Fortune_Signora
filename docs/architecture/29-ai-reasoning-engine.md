# 29 — AI Reasoning Engine

> Status: **RATIFIED — 2026-07-30.** Milestone **M9**, not started. Read with [ADR-0030](adr/0030-the-decision-package.md), which is binding on what M9 produces.
> **Amended by [ADR-0030](adr/0030-the-decision-package.md)** (accepted 2026-07-30): the product owner reframed the success criterion from *"can the model produce a conclusion?"* to *"will a customer trust it enough to act on it?"*, which replaces this document's `ReasonedConclusion` with a **Decision Package**. Rulings 1, 2, 4 and 5 below survive; Ruling 3's rubric is extended there. Read ADR-0030 first.
> Audience: engineers, architects, and anyone who has to defend what Signora concluded.
> Anchors: [28-ai-platform.md](28-ai-platform.md) · [04-modules.md](04-modules.md) §AI Reasoning Engine · [05-module-dependencies.md](05-module-dependencies.md) · [21-intelligence-pipeline.md](21-intelligence-pipeline.md) Stage 9 · [ADR-0012](adr/0012-ai-platform-architecture.md) · [ADR-0028](adr/0028-model-runtime-by-environment.md)

## Customer trust

**The objective of M9 is not to maximize AI-generated explanations.** It is to produce enterprise-grade decision packages that customers can independently inspect, understand, and validate.

Every customer-visible signal should answer the natural questions a customer will ask — *why · why now · why not earlier · what supports this · what challenges it · how fresh is it · what does it assume · what does it not mean · how do I check it* — using **deterministic information wherever possible**. AI is used only where inference is genuinely required.

The distinction matters because of who is reading. A Sales Executive, CRO or RevOps Manager opening Signora will not ask *"what prompt produced this?"* They will ask *"why do you think this, and could you be wrong?"* — and the answer must be evidence they can check, not fluency they are asked to trust.

> **Customers should never be asked to trust the AI. They should be shown enough to reach their own judgement.**

This is why [ADR-0030](adr/0030-the-decision-package.md) partitions the Decision Package by author rather than generating all of it: the fields a customer will lean on hardest are precisely the ones that must be reproducible. See *Design Principle: Deterministic Explainability* there.

---

## The question this module answers

> **What should a seller understand about this opportunity that the pipeline did not already compute — and how does Signora stay accountable for saying it?**

M8's question was *how does Signora talk to a model, and how does it know the answer is grounded.* This one is different in kind. **M9 is the first module that produces propositions its input did not contain.** Everything before it derives, projects, or restates; this one concludes.

That is worth naming precisely, because the interesting half of M9 is not making a model reason. It is **remaining accountable for a conclusion that, by construction, cannot be checked against a fact.**

---

## Reconstruction: what the code says, and where the documentation is stale

### Finding 1 — grounding already permits inference. Only the prompt forbade it.

The most consequential result of reconstructing M8, and it changes what M9 has to build.

`ViolationKind` has five members: `MALFORMED_CITATION`, `UNRESOLVED_CITATION`, `UNCITED_STATEMENT`, `UNGROUNDED_QUANTITY`, `WORKSPACE_ESCAPE`. **Not one of them forbids a novel relational claim.** They forbid fabricated references, unsupportable statements, invented figures, and another tenant's data. A sentence reading *"the retired system and the new hire together suggest an active replacement programme"* cites real facts, invents no number, and **passes M8's grounding unchanged.**

What actually held M8 to restatement was `explanation_narration@1` rule 4 (*"Do not draw conclusions"*) and the ratified stop condition — a **prompt** and a **process**, not a mechanism.

Two consequences:

1. **M9 reuses `GroundedOutput`, `verify()` and the five checks unmodified.** No loosening, no exception, no new violation kind. That the substrate needed no change for a workload of a genuinely different shape is the strongest available evidence that M8 was factored correctly — and it is exactly the "consume, do not redefine" boundary in practice.
2. **The guarantee M9 inherits is weaker than it sounds, and must be stated honestly.** Grounding will confirm that a reasoning result cites real facts and invents no figures. It will say nothing about whether the conclusion *follows*. M8 recorded this as the residual failure mode ("a correctly-cited but mischaracterising sentence"); in M9 it stops being residual and becomes **the central risk of the module**.

### Finding 2 — a stale docstring, corrected in the same change

`grounding.py` says *"Four distinct causes"* above five members. `WORKSPACE_ESCAPE` was added and the count was not. Trivial, and exactly the drift §2 forbids; it is corrected as part of M9's first task rather than left because it is small.

### Finding 3 — the v2 event payload is vaguer than every event since M4

[06-events.md](06-events.md) reserves `ai_reasoning.completed` with `reasoning_id`, `opportunity_id`, `model_provenance`, `result_ref`. Both `model_provenance` and `result_ref` are placeholders from before the catalog learned its own conventions — the same shape as `source_buying_score` before M6 sharpened it. M8 has since settled what provenance means concretely (prompt name, version, fingerprint, model, vendor, evidence digest, inference id), and `result_ref` predates the decision that **events carry identity, ports carry payload**. Proposed replacement is below.

### Finding 4 — the optional research input has no producer, and must not be built

[05-module-dependencies.md](05-module-dependencies.md) documents `AI Research Engine → AI Reasoning Engine` as the pipeline's one deliberate non-blocking edge, with a timeout and a fallback. **M10 does not exist.** Building the timeout, the fallback and the optional-consumption path in M9 would be constructing both sides of a contract with no counterparty — the speculative-port pattern the roadmap already forbids twice.

**Proposed:** M9 ships with no AI Research integration at all. The graph edge stays documented, the reasoning context assembler is written so an additional evidence source is an argument rather than a rewrite, and the integration lands in M10 **with its consumer**. This is the same call M8 made about embeddings and tool use.

---

## The defining challenge: accountability without a checkable fact

Grounding answers *"is every input real?"* Nothing answers *"is the conclusion sound?"*, and nothing can — that is what makes it reasoning rather than projection.

Three mechanisms are proposed in place of a check that cannot exist. None claims to verify soundness; each makes an unsound conclusion **visible, attributable, or falsifiable**.

**1. Every conclusion names its premises, and the premise set is closed.** A `ReasonedConclusion` is a `GroundedStatement` — text plus citations — so the facts a conclusion rests on are recorded, not implied. A reader who disagrees can see exactly what was used, and a conclusion citing two weak facts is visibly different from one citing six strong ones **without anyone scoring it**.

**2. Confidence is derived, never asserted.** See the ruling requested below.

**3. Contradiction survives.** The Buying Score Engine's permanent principle — *it prioritizes; it never resolves* — reaches its consumer here. A contested score arrives with `dissenting_signal_ids` naming the outweighed reading, and **M9 must not resolve the contradiction into a clean story.** A reasoning result over a contested account that reads as though nothing disagreed has destroyed the one thing the pipeline preserved through six stages. Proposed as a testable rule: *if the originating score is contested, the reasoning result must cite at least one dissenting signal.*

---

## Rulings requested

### Ruling 1 — confidence is derived from evidence, not emitted by the model

**The roadmap lists "confidence scores" as M9's deliverable.** I want to challenge the shape before it is built.

A model-emitted confidence number is a magic number nobody can justify. It is not calibrated, not comparable between two runs, not comparable between two models, and it moves when the vendor updates a checkpoint. This codebase has refused exactly that shape twice on exactly that reasoning: **`MatchStrength` refuses numeric conversion** because a category that becomes a number gets averaged by four modules within a year, and **money is kept off `InferenceUsage`** because a figure that looks authoritative and is not gets trusted.

Worse, it is *self-referential*: asking the thing that might be wrong how confident it is produces a number that is high precisely when the model is most fluently wrong.

**Proposed instead: confidence is a derived category over facts the pipeline already owns** — how many independent business events support the conclusion, whether the originating score is contested, how stale the evidence is (`EvidenceState` already exists and is already derived), and how many distinct providers corroborate. Every input is deterministic and already recorded. The result is reproducible, explainable to a customer, comparable across accounts, and unchanged by a vendor's checkpoint.

If a model-supplied confidence is ever wanted, it may be recorded as **provenance, never consulted for a decision** — the same treatment `vendor` gets.

### Ruling 2 — what replaces the stop condition

M8's stop condition was *"halt if narration needs a proposition the input does not contain."* M9's whole purpose is to introduce propositions, so that rule cannot carry over unchanged — and leaving M9 with **no** halt rule would remove the mechanism that protected every milestone boundary so far.

**Proposed replacement:**

> **M9 may conclude only about the opportunity in front of it, from evidence in its closed set. It must never recommend an action, compose a message, rank one account against another, or assert a fact about the world that no cited evidence contains.**
>
> If a reasoning result needs any of those, **stop**: recommending is M11, messaging is M11, cross-account ranking is the Revenue Intelligence Platform, and new facts about the world are M10's research.

This is testable in the same mechanical way M8's was: the output type has no field for an action, a message, or a ranking, and a conclusion asserting an unsupported fact fails `UNGROUNDED_QUANTITY` or `UNCITED_STATEMENT`.

### Ruling 3 — how a reasoning result is evaluated

`reasoning@1` must earn its release through `make eval` exactly as `explanation_narration@1` did — that machinery is M8's and M9 consumes it. But **the rubric cannot be reused unchanged**: coverage measures whether a narrative *mentioned* the load-bearing facts, which is the right question for restatement and the wrong one for reasoning.

Deterministic measures proposed, all computable without a judge:

- **Grounding and schema failures — zero.** Unchanged. Definitions, not thresholds.
- ~~**Premise breadth**~~ — **removed from the rubric at T123 and moved into the type.** `ReasonedOutput` refuses a conclusion resting on fewer than `MINIMUM_PREMISES` distinct facts, so it is enforced on every call in production rather than counted on a golden set before release. A constraint that can be made unrepresentable should not also be a thing an evaluation measures; the ladder asked for the demotion and the rubric got shorter.
- **Dissent acknowledgement** — on a contested account, at least one dissenting signal cited. Directly enforces the Buying Score Engine's principle at its consumer.
- **Action abstinence** — no conclusion contains an imperative. Crude, and it makes Ruling 2 measurable rather than aspirational.

**LLM-as-judge remains rejected as a gate**, on M8's reasoning: change the judge and every historical score moves, so a quality regression and a judge upgrade become indistinguishable. The genuinely subjective question — *is this reasoning any good?* — is answered by a human-rated sample on a fixed rubric, recorded per release and never automated into a gate.

### Ruling 4 — storage, and which category it belongs to

A reasoning result is a **materialized AI artifact**, the category ratified at T121: immutable, provenance denormalized, superseded by recency rather than edited. A re-run against a changed score produces a new result; the old one records what a seller was actually shown.

`ai_reasoning` is proposed as its own table rather than a `kind` column on `ai_narration`. The two have different shapes and different consumers (Recommendation Engine and the Revenue Intelligence Platform read reasoning; nothing reads narration yet), and a shared table with a discriminator would be one representation serving two truths.

### Ruling 5 — the event payload

Replacing the v2 placeholders, following every convention settled since M4:

| Event | v | Payload |
|---|---|---|
| `ai_reasoning.completed` | 1 | `reasoning_id`, `opportunity_id`, `entity_id`, `prompt_name`, `prompt_version`, `prompt_fingerprint`, `model`, `vendor`, `evidence_digest`, `conclusion_count`, `confidence`, `contested`, `inference_id`, `payload_version` |

Identity and counts, never the prose. `confidence` travels as the **string category** it is, exactly as `MatchStrength` and `Relevance` do — never a number. `contested` travels so a consumer need not re-derive it by querying signals, which would put scoring logic in the wrong module.

---

## Scope

**In:** the reasoning domain and its output type · context assembly from opportunity, score, ledger, signals and graph context · derived confidence · `reasoning@1` with a golden dataset and an evaluation run · `ai_reasoning` (migration `0017`) · `ai_reasoning.completed` · the composition root and one smoke stage.

**Out, with reasons:** AI Research integration (no producer until M10) · recommendations and messaging (M11) · cross-account ranking (Revenue Intelligence Platform) · streaming (no UI until M12) · tool use (M10's mechanism, with its own security surface) · runtime-editable prompts (same trigger as every other artifact).

---

## What I am *not* proposing

No change to `ai_platform`. No new violation kind, no loosened grounding, no altered release rule, no new provider behaviour, no rewritten evaluation harness. If implementation appears to require any of those, that is the halt condition, and the question to bring back is *"is this genuinely an M8 defect, or is M9 absorbing another milestone?"*

The one change M9 makes outside itself is a one-line docstring correction in `grounding.py` (Finding 2) — a stale count, not a behaviour.

---

## Task breakdown — T122–T130 · ~8–12 ew

| | Task |
|---|---|
| **T122** | Module scaffold, `ai_reasoning_engine` graph node, import-linter contracts per module pair · the `grounding.py` docstring correction (Finding 2) |
| **T123** | `domain/decision.py` — the Decision Package: `Proposition`, `StatedReasoning`, `Support`, `NarrationSubject` reuse. Every model-authored field a `GroundedStatement` |
| **T124** | `domain/support.py` — derived support and its inputs. **No model, no number the platform did not compute** |
| **T125** | `domain/temporal.py` — why now · why not earlier · what changed · freshness, all derived from `trigger`, `basis_at`, `delta` and `EvidenceState` |
| **T126** | Signal catalog extension — limitations and suggested validation per signal type, as reviewed repository artifacts with a content hash |
| **T127** | `application/reason.py` — the use case. Context assembly, one inference through `ai_platform`, package composition |
| **T128** | `prompts/reasoning@1` + golden dataset + rubric extension (premise breadth · dissent acknowledgement · action abstinence · *n*-sample robustness) · `make eval` run and release |
| **T129** | Migration `0017` — `ai_reasoning`, forced RLS, no `UPDATE` grant, `tenancy_policy.py` registration |
| **T130** | `ai_reasoning.completed` cataloged with its producer · composition root · one smoke stage |

Ordering follows M8's lesson: **the deterministic fields are built before the model-authored ones**, so the package is demonstrably valuable before a single inference happens — and so a failure to reach a model degrades the package rather than emptying it.

---

## Approval record

### Ratified 2026-07-30

Five rulings settled, all as proposed:

1. **Confidence is derived, never emitted by the model** — and renamed **Support**, since "confidence" invites the numeric reading the decision rejects.
2. **The replacement stop condition** — M9 may conclude; it must never recommend an action, compose a message, rank accounts against each other, or assert an uncited fact about the world.
3. **A reasoning-specific rubric** — coverage measures the right thing for restatement and the wrong thing for conclusions.
4. **`ai_reasoning` is its own materialized-artifact table**, not a discriminator column on `ai_narration`.
5. **The sharpened event payload**, replacing the v2 placeholders `model_provenance` and `result_ref`.

Plus [ADR-0030](adr/0030-the-decision-package.md): the Decision Package, partitioned by author, under **Deterministic Explainability**.

**No change to `ai_platform`** — no new violation kind, no loosened grounding, no altered release rule, no rewritten harness. If implementation appears to require one, that is the halt, and the question to bring back is *"is this genuinely an M8 defect, or is M9 absorbing another milestone?"*

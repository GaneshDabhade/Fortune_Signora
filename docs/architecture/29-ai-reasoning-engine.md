# 29 — AI Reasoning Engine

> Status: **RATIFIED — 2026-07-30. Milestone M9 COMPLETE — 2026-07-31**, T122–T130 delivered and `reasoning@1` released against `granite3.3:2b`. Read with [ADR-0030](adr/0030-the-decision-package.md), which is binding on what M9 produces, and [ADR-0031](adr/0031-evidence-citation-protocol.md), which records a platform finding M9 surfaced and deliberately did not fix.
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
| **T130** | SQLAlchemy model + repository · `ReasoningContext` adapter · `ai_reasoning.completed` cataloged with its producer · composition root · one smoke stage |

**All ten tasks complete as of 2026-07-31.** T128 closed last, after the investigation recorded below disproved the assumption that it needed a hosted model.

Ordering follows M8's lesson: **the deterministic fields are built before the model-authored ones**, so the package is demonstrably valuable before a single inference happens — and so a failure to reach a model degrades the package rather than emptying it.

---

## Evaluation runs against a configured provider, not a fixed one

**Ruled 2026-07-30, after T129.** The benchmark is unchanged by which provider executes it; only the provider changes. A local workstation gives developer feedback, and **the release that counts is earned against the hosted production model.**

**The capability already exists in the AI Platform and needs no architectural extension** — verified rather than assumed:

- `build_provider_registry(settings, client)` already registers Ollama *and* Anthropic, the latter whenever `anthropic_api_key` is present.
- `AIProviderRegistry.for_model(model)` resolves by **model**; no caller can name a vendor.
- Both evaluation entry points already accept `--model`.

**The only gap is that the entry points bypass that function**, hand-registering `OllamaAdapter` directly. Routing them through it makes `--model claude-sonnet-4-5` work as configuration alone. Neither vendor is special-cased, and adding OpenAI or Gemini later is an adapter registration rather than a change here.

**The wrinkle, and how it was resolved (T130).** The pre-flight reachability probe hit `/api/tags`, which is Ollama-specific, so a *hosted* evaluation was gated on a *local* runtime answering. Three options were on the table: make the probe conditional on the resolved adapter, move it behind the port, or drop it.

**It was dropped, and the reason is stronger than "the least bad option."** The probe was documented as the thing enforcing *"the harness never substitutes a fake for a model"* — and it was not. Nothing prevents a fake except **composition**: the entry points now build their registry through `build_provider_registry`, so no fake is reachable from them. What the probe actually contributed was a nicer message for one vendor's outage, and *"the runtime is unreachable"* is a fact the transport already discovers. Two representations of one truth, the second able to be right about only one vendor.

Making it conditional on the resolved adapter was rejected outright: that is vendor-specific logic in the one framework that must have none. Moving it behind the port would have meant expanding the AI Provider abstraction, which is the M9 halt condition.

A run against an unreachable or unregistered provider now abandons and reports **UNMEASURABLE** — the correct answer, and always the correct answer.

**Enforced, not merely intended.** `TestTheEvaluationFrameworkNamesNoVendor` in the Security Invariants suite parses every module under both `evaluation/` packages and fails if one imports or constructs a concrete adapter, or names a vendor in executable code. Docstrings are deliberately exempt — the first draft failed on three passages explaining *why* the framework is vendor-neutral, which would have banned exactly the writing that keeps the rule understood. One attribute is allowed by name, `settings.ollama_model`, as the default a developer run uses when `--model` is absent: **a default is not a branch**, nothing consults it, and registering a Gemini adapter still requires no edit there.

## T128 — halted, with two findings

**`reasoning@1` is written and its manifest ships. It has not been evaluated, and it is therefore not released.** Two things stopped the run, and both are raised rather than worked around.

### Finding 1 — the evaluation entry point breaks M9's own boundary contract

An M9 evaluation run cannot use M8's `make eval`: `ai_platform/evaluation/__main__.py` hardcodes `output_type=Narration`, and importing `ReasonedOutput` there would break *"no upstream module depends on the AI Reasoning Engine"*. So M9 needs its own entry point — which is right, and which the machinery already supports, since `load_prompt_registry(directory)` is per-directory and each module owns its own prompts.

**But an M9 entry point breaks the other contract.** *"`ai_reasoning_engine` reaches other modules only through `public/`"* forbids `ai_platform.infrastructure` and `ai_platform.evaluation` — and an evaluation entry point needs `AISettings`, `OllamaAdapter`, `load_prompt_registry`, `Harness`, `load_dataset` and `record`, none of which is exported through `public/`.

It was written, it broke the contract, and **it was reverted rather than committed**. A ruling is needed:

| | Approach | Assessment |
|---|---|---|
| **A** *(recommended)* | Exempt `modules.ai_reasoning_engine.evaluation` from the through-`public` contract | A composition root is *by definition* where infrastructure is wired — M8's own contracts carve out `infrastructure/` for exactly this reason. Narrow, and the exemption is visible in the contract itself |
| **B** | Export the harness surface through `ai_platform.public` | Cleaner in principle, but publishes a large surface whose only consumer is a developer command, and freezes it before M10 has used it |
| **C** | One shared entry point that resolves output types from a registry | Indirection to route around a boundary, and the registry becomes a place every module must remember to register in |

### Finding 2 — the benchmark does not execute on this workstation

Six consecutive `/api/generate` calls returned 500 after **exactly 60 seconds** — `InferencePolicy.timeout_seconds`, not a cold-start artifact. Narration completed in 43–52 s on the same hardware and the same model.

The likely cause is the output schema: `ReasonedOutput` is **1307 bytes against narration's 866**, and nested rather than flat. Ollama constrains output by grammar, and a nested schema is materially slower to decode.

**This is neither `EARNED` nor `REFUSED`. It is unmeasurable**, and the harness said so — it abandoned the run rather than averaging over the cases that survived. That refusal working on its first real encounter with a genuinely broken run is the most useful thing this task produced.

**Nothing was tuned in response.** The pinned model is part of the benchmark, the timeout is a policy the whole platform shares, and the schema is the shape the Decision Package requires. Each is a decision for the product owner, not a knob to turn until a number appears. Options, for a ruling:

- **Raise `InferencePolicy.timeout_seconds`** — but it is platform-wide and was chosen for production, not for a 4 GiB workstation GPU.
- **Evaluate against a hosted model** — production runs hosted models anyway, and `reasoning@1` must eventually earn a release against one regardless.
- **Accept that M9's benchmark is not locally executable** and record it, as ADR-0028 already anticipates for a development runtime.

**`reasoning@1` remains a draft, and the release rule refuses it.** That is the system working.

### T128 — CLOSED 2026-07-31. `reasoning@1` is RELEASED.

**The release was earned against `granite3.3:2b`, under a benchmark that did not change in any respect.** Same prompt fingerprint `9bc851470552`, same dataset `explanation_narration@1` `2cce0492a6bc`, same rubric v1, same criteria, same 60 s policy timeout, same schema. The only variable was `SIGNORA_OLLAMA_MODEL`.

```
prompt   reasoning@1  9bc851470552
model    granite3.3:2b
dataset  explanation_narration@1  2cce0492a6bc
rubric   v1    run on 2026-07-31

cases
  ok   northwind                        coverage 0.67
  ok   contoso                          coverage 1.00

sample size         2
grounding failures  0
schema failures     0
transport failures  0
retries             0
coverage            0.833

release             EARNED
```

**Recorded after eight consecutive passing runs**, not one. Every run: zero grounding failures, zero schema failures, zero transport failures. Seven of eight measured coverage 0.667; one measured 0.833.

### The assumption that was disproved

**T128 had concluded that `reasoning@1` required a hosted model.** That was wrong, and the repository proved it wrong with measurement rather than argument.

The binding constraint was never reasoning capability. It was **VRAM**. This workstation has a Quadro T1000 with 4 GiB, and `ollama ps` reports the split directly:

| Model | Resident | Processor | Result |
|---|---|---|---|
| `llama3.1:8b` | 5.6 GB | **58% CPU** / 42% GPU | UNMEASURABLE — 60 s timeout |
| `qwen3:4b` | 3.2 GB | 27% CPU / 73% GPU | UNMEASURABLE — 60 s timeout |
| `qwen2.5:7b-instruct-q3_K_M` | 4.2 GB | 46% CPU / 54% GPU | REFUSED — 2 grounding failures |
| `qwen2.5:3b` | 1.9 GB | mostly GPU | REFUSED — 1 grounding failure |
| `llama3.2:3b` | 2.6 GB | 10% CPU / 90% GPU | REFUSED — 1 grounding failure |
| **`granite3.3:2b`** | **1.9 GB** | **100% GPU** | **EARNED ×8** |

**On this hardware "stronger" means "larger" means "more CPU offload" means "slower".** The answer was a model that stays *entirely resident in VRAM*, not a bigger one — which is the opposite of the intuition the investigation started from. `qwen3:4b` failed for a second reason worth recording: it is a thinking model, and its reasoning tokens compete with a 2048-token ceiling and grammar-constrained decoding.

**No architectural change was needed.** `SIGNORA_OLLAMA_MODEL` already flows to `build_provider_registry` and to the entry point's default. The capability the investigation needed had existed since M8.

### `granite3.3:2b` is *currently certified*, not permanent

**Ruled 2026-07-31.** Three of the four non-passing models failed on **citation form rather than reasoning** — see [ADR-0031](adr/0031-evidence-citation-protocol.md): the renderer presents `[token]` and the parser accepts only `token`, so a model that follows *"cite by their exact reference strings"* literally is marked ungrounded for obeying.

`granite3.3:2b` succeeds because it strips the brackets, which is a stylistic habit rather than a capability. **The field of locally-usable models is very likely wider than the table above suggests**, and the comparison should be re-run once the protocol inconsistency is corrected. Until then this is the certified model, and nothing more.

### The coverage margin — an engineering observation, not a blocker

Seven of eight runs measured **0.667 against a 0.66 floor**. Because each case has three load-bearing facts, coverage is quantised: the verdict requires *both cases to cite at least 2 of 3*, and a single dropped citation flips the run to REFUSED.

**The benchmark says the prompt passed, and the benchmark is accepted.** This is recorded so a future prompt revision can improve robustness deliberately — and explicitly **not** as a reason to modify `reasoning@1`, which would be tuning a prompt to widen a margin rather than to fix a defect.

### The re-run this section asked for — protocol 2, 2026-08-04 (Lane A, Epic G)

**The section above ends with an instruction: *"the comparison should be re-run once the protocol inconsistency is corrected."*** [ADR-0031](adr/0031-evidence-citation-protocol.md) corrected it, `PROMPT_RENDERING_PROTOCOL_VERSION` became **2**, and the comparison was never re-run. **`reasoning@1` is refused at runtime today**, and the code says why in its own words:

> `_refuse_stale_protocol` — *"passed for this pairing under rendering protocol [1], but this process renders at protocol 2… **Re-evaluate under the current protocol — do not re-author the prompt.**"*

**The certified model did not survive the correction.** The manifest's one protocol-2 row is `granite3.3:2b` at **coverage 0.0 with 2 grounding failures** — the model whose release rested on *"a stylistic habit rather than a capability"* lost it the moment the renderer stopped rewarding the habit. **The section predicted this outcome and named the reason before it happened.**

**`llama3.1:8b` was re-measured, and it passes protocol 2 cleanly:**

```
prompt   reasoning@1  9bc851470552      model    llama3.1:8b
dataset  explanation_narration@1  2cce0492a6bc
rubric   v1    render protocol v2       run on 2026-08-04

  ok   northwind   coverage 0.67        grounding failures  0
  ok   contoso     coverage 0.67        schema failures     0
                                        transport failures  0
sample size 2       coverage 0.667      release  EARNED
```

**It is not recorded, and the reason is the whole finding.** The run needed **172.8 s for two cases — ~86 s each** — against `InferencePolicy.timeout_seconds = 60`. Under the committed policy this same pairing reports **UNMEASURABLE**, and Ollama's log shows why: generation was healthy at **4.7 tokens/sec and 270 tokens decoded** when the client hung up at exactly 60 s. **The `500` is the client disconnecting, not the provider failing.**

> **The table above lists `llama3.1:8b` as UNMEASURABLE and stops there. That was a fact about the clock, not about the model** — and no one had established what it would score if allowed to finish. It scores a release.

**So the constraint is unchanged and better understood.** A Quadro T1000 holds 4 GiB; `llama3.1:8b` is a 4.9 GiB weight file, so it runs 58% on an i7-10750H. **The one model that satisfies protocol 2 is the one that does not fit in VRAM**, and the one that fits no longer satisfies protocol 2. Every locally-runnable model is now on one side or the other of that line.

**Nothing was tuned and nothing was recorded.** The measurement above was taken by a throwaway script outside the repository, altering the client timeout and **nothing else** — same prompt fingerprint, same dataset, same rubric, same schema, same protocol. It is a fact about this workstation, and it is deliberately **not** in the manifest: [TASK-013](../BACKLOG.md) forbids adjusting the timeout in writing, and recording a row the committed policy cannot reproduce would make the manifest claim a release this repository cannot re-measure. **Raised as [C-222](../LANE_COORDINATION.md).**

---

## T130 — four findings, every one from the repository saying no

**Nothing here was designed in advance.** Each came from a contract, a grant or an existing type refusing what was being written, and each refusal was investigated before it was worked around.

### 1 · `load_prompt_registry` cannot be published, and the contract is right

M9 owns its own prompts, and `load_prompt_registry(directory)` is per-directory precisely so each module can. The obvious move was to export it through `ai_platform.public` so M9's composition root could bind its own prompt directory the way M8's does.

**The Clean Architecture layering contract refuses it:** `public/` sits *below* `infrastructure/`, and a loader that reads the filesystem is infrastructure. Publishing it would put an infrastructure dependency underneath every consumer of the AI Platform's contract.

The refusal is correct, and the resolution follows from it: **binding a module's prompt directory to an `Infer` is the application composition root's job** — the one place that may legitimately import both modules' infrastructure, and the same place `build_narrate` is already called from. `build_reason` therefore takes `infer` as a parameter and exports `PROMPT_DIR`, while still naming the prompt and version itself, because those are the release-rule decisions a caller must not be able to route around.

**No change to `ai_platform` was required.** The halt condition was approached and not crossed.

### 2 · The catalog was about to have two authorities

`PipelineReasoningContext` was first written taking a `SignalCatalog` as its own constructor argument. `SignalQueries` already exposes `catalog()` — so a composition could have handed M9 one revision while the signals it was describing were produced under another, and the package would have stated limitations from a version that never applied to it.

The parameter was **removed**. There is one catalog in force, and the module that owns signals is the one that knows which. *Compose deterministic knowledge; do not duplicate it.*

### 3 · `support_level` and `contested` are duplicated truth, and are now inert

Migration `0017` stores the full `SupportBasis` as JSONB **and** `support_level`/`contested` as scalar columns. The scalars are derivable from the JSONB, which makes them a stored copy of a derivable fact — a defect waiting for the two to disagree.

They earn their place as an **operator query surface** (*"which accounts are on limited support?"*), so rather than change an applied migration the duplication was neutralised: `save()` writes both from one in-memory object so they cannot disagree at write time, and **`_to_package` never reads them** — `SupportBasis` derives its own level. Asserted two ways, because either alone would be weak: the scalar agrees with the derived level at write time, and an AST check proves the read path contains no reference to the columns at all. A drift can therefore never reach a customer.

*Raised rather than silently accepted: if the query surface turns out not to be needed, the honest fix is a migration dropping both columns.*

### 4 · The test tried to read `outbox_event`, and the grant refused it

The integration test asserted publication with `SELECT count(*) FROM outbox_event` under the application role. PostgreSQL refused: `permission denied`. `signora_app` holds no read grant on a platform infrastructure table (migration `0006`, CLAUDE.md §8), and the correct response is never to restore one.

`tests/pipeline.py::_published` already reads the outbox **under the relay's identity**, which is how the relay itself does it. The test now uses it and asserts more than it originally would have: the producer module, the workspace, the payload's `reasoning_id` and `support` — and that **no prose travels in the envelope**.

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

---

## A-i — the conclusion becomes readable, 2026-08-04 (Lane A)

**The module has concluded since T130 and nothing could read the conclusion.** [417 §2c](417-executable-slice-audit.md) found it as one of only two modules in the repository with a complete `domain/` and `application/` and no `interface/` — *"built, tested, unreachable."* This slice is the layer, and only the layer.

### One endpoint, and it is a read

```
GET /workspaces/{workspace_id}/accounts/{account_id}/decision-package
```

**The most recent package for an account, or `404`.** Packages accumulate and are never edited, so *most recent* is derived from the rows rather than from a stored current flag — `latest_for` already worked that way and needed no change.

**There is no `POST`, and a Security Invariant now says so.** Reaching a conclusion is a model call: §7 forbids an API handler blocking on pipeline work and Principle 13 puts it in a background worker. `test_the_module_publishes_no_route_that_writes` asserts it over the router's decorators, and was verified by adding a `POST` and watching it fail.

**`404` when nothing has been concluded** — the ordinary state of a new account, and the same answer an account in another workspace receives, so the endpoint cannot be used to discover that a workspace holds one.

### What the response carries, and why it is shaped that way

**ADR-0030's split is the shape of the response, not a note beside it.** The three model-authored statements are grouped and carry their citations; the twelve derived and catalog parts are returned as the facts they are.

| | |
|---|---|
| **Authored, and grounded** | `proposition` · `summary` · `stated_reasoning` — each with its evidence tokens, and **no flattened paragraph.** Joining them would discard the mapping from claim to evidence, which is the only reason to trust any of it |
| **Derived** | `supporting_evidence` · `support` · `temporal` · `alternative_readings` |
| **Snapshotted from the catalog** | `limitations` · `suggested_validation` · `catalog_version` |
| **Provenance** | `model` · `vendor` · `prompt_name` · `prompt_version` · `created_at` |

**Facts travel; sentences are the frontend's.** `SupportBasis.explain()`, `TemporalExplanation.why_now()` and `DecisionPackage.answers()` phrase things for a reader — that is presentation, and [ADR-0034](adr/0034-ubiquitous-language.md) puts presentation at the frontend edge. The response therefore carries `contested`, `dissenting_signals`, `alternative_readings`, `trend` and `delta` rather than the sentences built from them, and **nothing in this layer re-implements a phrasing the domain already owns.**

**`support.level` is derived on the way out, exactly as it is on the way in.** The table's `support_level` column stays inert: the repository does not read it and neither does this layer, so a drift between the two still cannot reach a customer.

**What is deliberately absent**, following the precedent `ai_platform`'s narration schema set: `id`, `correlation_id`, `inference_id`, `prompt_fingerprint` and `evidence_digest`. The first four are how an engineer traces a call, not how a seller decides anything. The digest is a hash a customer cannot recompute — the verifiable form of *"which evidence"* is the citation tokens, which are on every statement.

### Three findings, all of them the repository refusing something

**1 · `public/` is still empty, and that is correct.** 417 named A-i's reuse as *"the module's own `public/`"*, and that surface exports nothing. It turned out not to matter: **an interface layer serves its own module's use cases and is not a cross-module consumer**, so it imports `application/` and `domain/` directly, exactly as the six existing interface layers do. `public/` stays empty until something outside this module consumes a Decision Package, and `test_the_public_contract_exports_nothing_yet` still holds.

**2 · The import contract caught a reach past `ai_platform.public`.** The schema first imported `GroundedStatement` from `ai_platform.domain.grounding`, which compiles and runs perfectly well. `lint-imports` refused it. Fixed at the import, not at the contract.

**3 · A Security Invariant expired, and was replaced rather than deleted.** `test_interface_is_absent_until_it_has_a_caller` asserted this directory did not exist, because *"a directory made for a caller that does not exist is the speculative structure §6 forbids."* A-i gave it a caller, so **the condition can no longer occur and the guard could no longer fail** (§2). It now asserts that the layer exists *and* is mounted at the composition root, and the no-write invariant above was added beside it — which is the property genuinely at risk from here.

### What this slice did not do

**No new conclusion, no second inference path, no cross-account ranking, no recommendation** — all four are ruled out by the module's own contract and none was approached. **The domain was not changed.** The one fixture that failed did so because `TemporalExplanation` refuses a first reading with a non-zero delta, which is the invariant working; the fixture was corrected.

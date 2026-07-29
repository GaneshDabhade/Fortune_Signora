# 28 — AI Platform

> Status: **APPROVED IN DIRECTION — 2026-07-29.** Milestone **M8**. Not yet implemented.
> Audience: engineers, architects, and anyone who has to trust what Signora says.
> Anchors: [14-ai-architecture.md](14-ai-architecture.md) · [ADR-0012](adr/0012-ai-platform-architecture.md) · [04-modules.md](04-modules.md) · [21-intelligence-pipeline.md](21-intelligence-pipeline.md) · [16-architecture-risks.md](16-architecture-risks.md) R-01, R-05, R-10
>
> This document proposes the AI Platform. It is not yet built.

---

## The question this module answers

**Ratified 2026-07-29.** The AI Platform answers exactly one question:

> **"How does Signora communicate with a model, and how does it know the answer is grounded?"**

It does not answer *what* to say. It answers *what may be said at all*, and it is the machinery that makes every later answer checkable.

### The correction that produced it

The original brief gave the AI Platform the question *"What reasoning should be presented to the user?"* **That is the AI Reasoning Engine's question** — [04-modules.md](04-modules.md) §AI Reasoning Engine already owns it, *"reason over an opportunity, its buying score, signals, Knowledge Graph context … producing structured explanations, prioritization, and analysis"* — and that module is M9. Had M8 answered it, the roadmap would have had two names for one module and the substrate M9 and M10 stand on would have been built as a by-product of a feature.

Accepted 2026-07-29. Everything else in the brief — provider abstraction, Ollama, versioned prompts, an evaluation harness — was already exactly that substrate, so only the framing sentence changed, not the scope.

### The permanent principle

**Ratified 2026-07-29.** Alongside *identity never truth*, *change never significance*, *prioritizes never resolves*, and *intelligence suggests, humans commit*:

> **Grounding.** The AI Platform never constrains what a model writes. It constrains **what the model is permitted to reference.** The deterministic intelligence pipeline defines the universe of facts, and the AI Platform treats that universe as **closed**. Every statement must be supported by citations · every citation must resolve · every numeric value appearing in generated text must exist in cited evidence.
>
> **It may generate language. It must never generate facts.**

Most of this document is about making that a schema rule instead of an aspiration.

---

## Reconstruction: what the code says, where the documentation disagrees

Per the standing process rule — *implementation is truth, documentation may drift* — M8's inputs were reconstructed from the repository. Two disagreements were found, and both bear directly on M8.

### Drift 1 — the Provider Port is not where the structure document says it is

[15-project-structure.md](15-project-structure.md):109 states the Provider Port lives in `backend/signora_platform/provider_abstraction/`. **That package does not exist.** The port is [`modules/provider_platform/domain/provider.py`](../../backend/modules/provider_platform/domain/provider.py) — inside the module that owns it, not in the platform.

This was almost certainly the right call and nobody wrote it down. It matters here because **line 110 of the same document makes the identical claim about the AI Provider Port** (`signora_platform/ai_provider_abstraction/`). A stale sentence should not decide where M8's most important seam lives. It is re-examined below on its merits, and 15-project-structure.md is corrected either way as part of this milestone.

### Drift 2 — neither Ollama nor Bedrock is a ratified vendor

[ADR-0012](adr/0012-ai-platform-architecture.md) ratifies **Claude, OpenAI, Gemini**, with **Azure OpenAI** reserved. It also explicitly *considered and rejected* open-weight self-hosted models:

> *"Would remove per-token vendor cost and vendor dependency entirely, but self-hosting competitive-quality models … adds significant infrastructure/ops burden and … still trails frontier hosted models."*

**Ollama is that rejected alternative**, and Bedrock is not in the decision at all. The brief's direction is sound — the *reason* for rejection was production self-hosting, and using Ollama strictly for local development is a different decision that the ADR never evaluated — but a ratified ADR is not amended by a session. **M8 requires ADR-0028** (*Local model runtime for development; Bedrock as a production vendor*), superseding the relevant clauses of ADR-0012, with [08-technology-stack.md](08-technology-stack.md) updated in the same change. Written as part of this milestone, not assumed by it.

### What M8 inherits and can rely on

| | |
|---|---|
| Input | `opportunity_engine.public` — `tracked()`, `explanation()`, `history()`; `opportunity.created`, `opportunity.stage_changed` |
| Already reachable from one call | opportunity → buying score → contribution ledger → signals → business events → observations → knowledge → claims → raw provider records |
| Artifact precedent | `taxonomy/business_events@1.json`, `scoring/scoring_model@1.json`, `policy/opportunity_policy@1.json`, each with an `infrastructure/*_loader.py` |
| Port precedent | `ProviderAdapter` — narrow Protocol, typed failure taxonomy, registry populated from configuration, identical contract suite run against simulated and real adapters |
| Configuration | `signora_platform/settings.py` only; no module reads `os.environ` |
| Constraints | forced RLS · every new table registered in `tenancy_policy.py` or the build fails · platform frozen (§20a) · frontend foundation frozen (§20c) |

---

## The defining challenge

Every guarantee this platform has made so far is deterministic, and every one is proven by removal: delete the guard, watch the invariant fail, restore it. 261 invariants, each mutation-proven. That method is the reason the architecture is trustworthy, and **it does not survive contact with a language model.** You cannot delete a guard and watch a probability distribution fail.

The naive responses are both wrong:

- **Test the model.** Assert the output equals a reference string. It won't, twice in a row, and the test gets deleted within a month — the anti-pattern CLAUDE.md §11 exists to prevent.
- **Don't test the model.** Ship the one component in the system with no guarantee attached, sitting directly in front of the user, speaking in Signora's voice about a customer's accounts.

The way out is not a weaker guarantee. It is **a different thing to guarantee.**

We stop trying to constrain what the model *says* and constrain what it is *permitted to refer to*. Wording is probabilistic; the set of referable facts is not. And it happens that Signora, uniquely among products that put an LLM in front of a customer, already has that set: **eight pipeline stages of typed, identified, workspace-scoped, individually-cited facts.** Every claim, observation, business event, signal, ledger entry, score, and opportunity has an id, and every id resolves back to a raw provider record.

That is the asset M8 spends.

---

## The proposal: a closed evidence set, and grounding as a schema rule

### The evidence set

The AI Platform never receives free text. It receives an **Evidence Set**: a frozen, workspace-stamped bundle of typed facts, each carrying the id the pipeline already minted for it.

```
EvidenceSet
  workspace_id: UUID
  facts: tuple[EvidenceFact, ...]     # each with kind, ref, and typed content
  assembled_at: datetime
  digest: str                          # content hash — the reproducible half of the input
```

Two properties are structural rather than documented:

- **A mixed-workspace set is unrepresentable.** Every fact carries its own `workspace_id`, and construction refuses a set whose facts disagree with the set's own. A cross-tenant prompt is not "forbidden" — it cannot be built. This is the same move that made `SignalType` unable to be invented per workspace and `MatchStrength` unable to become a number.
- **The set is closed.** Nothing is added after construction, and the renderer that turns it into prompt text can render only what is in it. There is no path by which arbitrary text reaches a model without passing through a fact with a ref.

### Grounded output

The model is never asked for prose. It is asked for a structure in which **every statement cites the facts it rests on**:

```
GroundedNarrative
  summary: str
  points: tuple[NarrativePoint, ...]

NarrativePoint
  text: str
  evidence: tuple[EvidenceRef, ...]    # non-empty, enforced
```

Validation runs before the output is trusted by anything, and each check is a first-class failure with its own type:

| # | Check | Failure |
|---|---|---|
| 1 | Parses against the Pydantic v2 schema, `extra="forbid"` | `OutputSchemaInvalid` |
| 2 | Every `EvidenceRef` resolves inside the set | `UngroundedOutput` |
| 3 | Every point cites at least one fact | `UncitedStatement` |
| 4 | Every number appearing in `text` appears in a cited fact | `UngroundedQuantity` |
| 5 | Every ref belongs to the requesting workspace | `WorkspaceEscape` |

Check 5 is redundant given the set's construction, and is asserted anyway — the same defence-in-depth as filtering by `workspace_id` under forced RLS.

**Check 4 is the one that earns its place.** The characteristic LLM failure in this product is not inventing a company; it is inventing a *quantity* — a headcount that grew 40% when the observation says 12%, a raise of $30M when the business event says $24M. A number in the output that appears in no cited fact is a mechanical, deterministic, unambiguous defect, and it fails the call.

**Hallucination becomes a schema violation.** Not a quality score, not a review finding — a typed error on a code path with a test, exactly like `ProviderPayloadInvalidError`.

### Why grounding is what keeps AI output inside the existing category system

M6 ratified three permanent categories of platform data: **derived intelligence** (rebuildable, machine-authored) · **customer configuration** (declarative, irreplaceable) · **workflow state** (accumulated, irreplaceable).

AI output does not obviously fit any of them. It is machine-authored, so it is not configuration or workflow — but it is not rebuildable either, because running the same prompt twice produces different words. On the face of it, M8 introduces a fourth category and breaks the rebuild contract that M6 just finished asserting by test.

It does not, and the reason is grounding:

> **The conclusion is rebuildable; the wording is not.**

Because a grounded narrative contains no proposition absent from its evidence set, regenerating it produces *different prose over an identical fact set*. The information content is reproducible even though the expression is not. AI output therefore stays **derived intelligence**, with one stated caveat, rather than becoming a fourth thing.

This holds only while grounding holds. Stated as sharply as it deserves:

> **The day Signora permits ungrounded generation is the day "rebuild the pipeline" stops being safe.**

Grounding is not primarily a hallucination defence. It is what keeps the AI layer inside the architecture the previous seven milestones built.

### What grounding does not guarantee — stated plainly

Grounding is containment, not comprehension. A narrative can cite the correct business event and still characterise it wrongly: *"Raised 24M USD in a Series B"* cited accurately but described as a down round. Checks 1–5 pass; the sentence is misleading.

**That failure is real, and it belongs to the probabilistic tier below — it is not solved here, and this proposal does not claim it is.** What grounding buys is that the *misleading* case is the residual, rather than one of a dozen open failure modes including fabricated companies, invented numbers, and other tenants' data.

---

## The two-tier guarantee

M8's answer to *"what can an evaluation harness assert when the output is not deterministic?"* is that two different things are being asserted and the project has been treating them as one.

| | **Deterministic correctness** | **Probabilistic quality** |
|---|---|---|
| Question | Is this output *permissible*? | Is this output *good*? |
| Verified by | Code, on every call, in production | A harness, on a golden set, before release |
| Depends on a model | **No** — runs against recorded fixtures | Yes |
| Reproducible | Yes | No |
| Proven by removal | **Yes** — Security Invariants, mutation-proven | No |
| Gate | Blocks the call and the build | Blocks release on regression |
| Covers | schema · grounding · citation · quantities · workspace · prompt-version recorded · provenance complete | faithfulness · completeness · usefulness · tone |

Two consequences follow, and both are non-negotiable in the implementation:

**Security Invariants never call a model.** They run against recorded outputs held as fixtures — including deliberately corrupt ones (a fabricated ref, an invented number, a foreign workspace's id). The invariant suite stays fast, offline, and deterministic. A guarantee that needs a GPU to verify is not a guarantee.

**The evaluation harness is not part of `make test`.** It is `make eval`: slower, model-dependent, run against Ollama locally and against production vendors before release. Folding a non-deterministic run into the test gate is how a project ends up with a flaky suite people learn to re-run until it passes — which is worse than no gate.

### What the harness measures, and one rejection

The golden dataset is `(evidence_set, prompt_version, reference_answer, assertions)`, seeded from the M2.0 simulation scenarios exactly as [IMPLEMENTATION_ROADMAP.md](../../IMPLEMENTATION_ROADMAP.md) anticipated — the datasets exist, the expected pipeline outcomes exist, and this is the milestone that collects on them.

Reported per `(prompt_version, model, dataset_version)`:

- **Grounding pass rate — must be 100%.** It is deterministic; anything less is a defect, not a score.
- **Schema validity rate**, and the retry rate needed to reach it — the practical cost signal for a given model.
- **Coverage** — the proportion of the evidence set's *load-bearing* facts (highest-weighted ledger contributions, the originating score, the contested reading if present) that the narrative actually mentions. Deterministic, and it catches the real quality failure: an output that is correct and says nothing.
- **Human sample rating** on a fixed rubric, on a fixed sample size, recorded per release.

**Rejected as the primary gate: LLM-as-judge.** Scoring one model's output with another model makes the ruler itself non-reproducible and vendor-dependent — change the judge and every historical score moves, so a quality regression and a judge upgrade become indistinguishable after the fact. It may be recorded as a secondary signal. It may never gate a release. This is the same reasoning that keeps `MatchStrength` from being a number and thresholds out of rule code: *a magic number nobody can justify will be trusted by four modules within a year.*

### Reproducibility, honestly framed

> **The inputs are exactly reproducible. The output is recorded.**

Every inference records prompt name and version, model id and vendor, sampling parameters, the evidence-set digest, and the full ref list — so any result can be *re-attempted* under identical conditions even though it cannot be *re-derived*.

And explicitly: **`temperature=0` is not determinism.** Batching, hardware, and silent vendor-side model updates all move the output. No part of this design may claim reproducibility on the strength of a sampling parameter.

---

## Where the AI Platform lives

**Recommendation, requested 2026-07-29: `modules/ai_platform/`** — with two conditions that matter more than the directory, stated after the comparison. Adding the node is a dependency-graph change ([05-module-dependencies.md](05-module-dependencies.md), CLAUDE.md §5).

| | Option A — `signora_platform/ai/` | Option B — `modules/ai_platform/` **(recommended)** | Option C — build it inside M9 |
|---|---|---|---|
| Matches | 15-project-structure.md:110, as written | 15-project-structure.md:109, **as built** | The YAGNI ruling, most literally |
| Prompts | Business IP inside a package that must hold none | Alongside the taxonomy, scoring model, and policy artifacts | Same |
| Freeze | Born frozen (§20a), before a consumer exists | Frozen after M9 consumes it — the M1.3A rule | n/a |
| Extractability | Platform code is not independently extractable | An IO-bound, differently-scaled, differently-failing service — the textbook extraction candidate (Principle 5) | Buried in a reasoning module |
| Cost | Every M9 lesson becomes a freeze exception | One graph node, one document correction | M9 becomes very large and the harness ships under feature pressure |

**Recommendation: Option B.** Four arguments, in order of weight:

1. **The platform must contain no business logic**, and prompts are the single most business-loaded artifact in the system — [14-ai-architecture.md](14-ai-architecture.md) calls prompt content *"domain IP … part of the product's differentiation."* Putting them in `signora_platform/` contradicts the rule that package is defined by.
2. **Freezing precedes proving.** `signora_platform/` was frozen at M1.3A *after* it was demonstrably deployable. An AI substrate frozen at construction, before M9 or M10 has used it, freezes guesses — and every lesson M9 learns then arrives as a freeze exception.
3. **Implementation already ruled on the analogous question** and put the Provider Port in the module. Consistency with the built system beats consistency with a sentence nobody has run.
4. **`ai_platform` is a real bounded context**, not a bag of utilities. It owns prompt versions, inference records, evaluation runs, and the evidence-set contract; it has a vocabulary; and `provider_platform` is the same shape of module and has held up for four milestones.

Graph changes required: one new node, `AI Platform`, with `AI Reasoning Engine → AI Platform` and `AI Research Engine → AI Platform` recorded now and consumed in M9/M10.

### Condition 1 — the substrate never depends on the pipeline

A directory alone does not answer *"what best supports future evolution"*, because the real hazard is not where `ai_platform` sits but **what it ends up knowing**.

Shipping grounded narration gives `ai_platform` a reason to read `opportunity_engine.public`. Left alone, that makes one module simultaneously the substrate M9 and M10 stand on **and** a participant in the pipeline they consume. Legal, acyclic, and a slow structural problem: every future capability adds another pipeline dependency to the thing that was supposed to be vendor plumbing, and by M11 the substrate cannot be extracted or reasoned about independently.

**So it does not read the pipeline at all.** The narration use case depends on an `ExplanationSource` Protocol declared in `ai_platform/application/ports.py`; an adapter in `infrastructure/` satisfies it by reading `opportunity_engine.public`, wired at the composition root.

This is not a new pattern — it is the M5B `SignalReader` finding applied deliberately rather than discovered under duress:

> *If a fake cannot stand in for a dependency, the dependency was never really a boundary.*

The result: `domain/` and `application/` know nothing about opportunities, buying scores, or any pipeline concept. `ai_platform` stays extractable (Principle 5), testable with fakes alone, and — the point — **still pure substrate on the day M9 arrives**, whatever M8 shipped on top of it.

### Condition 2 — freeze after M10, not after M8

`signora_platform/` was frozen at M1.3A *after* it was proven deployable. The same criterion applies here, and the trigger is specific:

> **`ai_platform` freezes on the same terms as the platform (§20a) once M9 *and* M10 have both consumed it.**

Not M8, which would freeze guesses. Not M9 alone either — a port that has only served a structured single-call workload has never been asked for tool use, streaming, or resumability, and freezing it before M10 would guarantee an immediate exception. Two consumers with genuinely different shapes is the evidence that the abstraction is real rather than a description of its first caller.

Until then `ai_platform` is ordinary module code, changed with ordinary review.

### On the name

`ai_platform` sits beside `provider_platform`, which has held for four milestones, and the `signora_platform/` collision is a naming discomfort rather than a structural one — `provider_platform` already lives with it. `ai_gateway` was considered and rejected: a gateway implies routing and nothing else, and this module owns prompts, grounding, and evaluation, which are not gateway concerns.

---

## Prompts: ownership, versioning, immutability

The ownership criterion ratified in M5A has now decided this question four times: **Signora's language ships as versioned repository artifacts; the customer's position lives in versioned, attributed rows.** A prompt is unambiguously Signora's language. It ships in the repository.

```
modules/ai_platform/prompts/
    manifest.json                          # name → versions, models evaluated, status
    explanation_narration@1.md
```

Matching `taxonomy/business_events@1.json` and `scoring/scoring_model@1.json`, loaded by an `infrastructure/prompt_loader.py`, reviewed like code — because it *is* code, in the specific sense that changing it changes program behaviour without changing any Python.

Two rules go beyond the existing artifact pattern:

**A released prompt version is immutable, enforced by content hash.** `manifest.json` records the SHA-256 of every released version, and a test fails the build if a released file's hash changes. Editing a prompt in place would silently invalidate every recorded result claiming that version — the same class of defect as mutating a scoring model, and every artifact in this platform is already immutable once shipped. A change is a new version, always.

**A prompt is released *for specific models*.** The manifest records which `(model, dataset)` pairs it has been evaluated against, and a prompt may not be used with a model it was never evaluated on. This is the direct consequence of developing against Ollama and running production on Claude: a prompt tuned on a small local model has *not* been shown to behave on a frontier one, and the manifest is where that is stated rather than assumed.

Prompts stay out of the database. The trigger to revisit is the same one recorded for every other artifact — *a non-engineer must tune one without a release*, realistically M12.

---

## Context assembly: module or platform?

**Both, split by whether it contains judgement.**

- **The container is infrastructure.** `EvidenceSet`'s construction rules — single workspace, closed membership, digest, every fact carrying a resolvable ref — are tenancy machinery. They belong to `ai_platform` and are identical for every caller, forever.
- **The contents are domain.** *Which* facts matter when explaining a buying score is a domain question that only the module asking the question can answer. M9 assembles reasoning context; M10 assembles research context; neither is `ai_platform`'s business.

So `ai_platform` publishes an `EvidenceSetBuilder` that **refuses to build an invalid set**, and consuming modules decide what to put in it. Getting the workspace scoping wrong is then not a bug a reviewer must catch — it raises.

This generalises, and is worth stating as the rule: **when a concern is part tenancy and part domain, the tenancy half is a type that refuses, and the domain half is a caller that chooses.**

---

## Cost and latency: what the port exposes, and what it refuses to

Yes to both, with one deliberate refusal.

Every call returns, alongside its result, a normalised `InferenceUsage`: input tokens, output tokens, model id, vendor, latency in milliseconds, and retry count. All are scaling triggers in [12-scalability.md](12-scalability.md), all are vendor-specific in the raw, and normalising them is exactly what a port is for.

**The port never reports money.** Cost is a pricing fact: vendor-specific, time-varying, contract-dependent, and it changes without a line of code changing. A dollar figure stored on an inference record would be true for one week and quietly wrong forever after — while tokens are a fact about what happened and stay true. Pricing is a table applied outside the port at reporting time, over stored usage.

This is the same discipline that keeps normalization from inventing a confidence score: *record what happened; compute judgements where the inputs are actually known.*

---

## Providers: Ollama, and the precedent that already exists

The AI Provider Port copies the `ProviderAdapter` pattern deliberately, including its failure taxonomy, because that pattern has held for four milestones:

```
AIProviderAdapter (Protocol)
    describe() -> AIProviderDescriptor          # vendor, models, structured-output support, context window
    complete(request: InferenceRequest) -> InferenceResult
```

Failures mirror the provider taxonomy exactly — `AIProviderError` · `AITransientError` · `AIRateLimitedError` (carrying the vendor's stated wait) · `AIPermanentError` · `AIOutputInvalidError`. No vendor SDK exception escapes an adapter; a caller catching the base has caught everything.

**Ollama is to the AI Platform what the simulated adapter is to the Provider Platform**, and the architecture for that is already ratified in [20-provider-simulation.md](20-provider-simulation.md). Reused wholesale:

- **One contract suite, run against every adapter** — local and production. This is the keystone test in the provider layer and the only mechanism that catches drift between paths; there is no reason to invent a second answer.
- **Behavioural neutrality (the AC-21 rule).** Metadata may say which vendor served a call — it must be recorded — but **no business behaviour may branch on it.** No `if vendor == …` anywhere outside an adapter, asserted directly, exactly as pipeline neutrality is asserted today.
- **Provenance on every result**: vendor, model, prompt version, evidence digest.

What is *not* copied: Ollama is a real vendor adapter, not a simulator. It returns genuine model output, which is the entire point — prompt engineering, the harness, and offline demos need real generation, and a scripted fake would evaluate nothing.

Adapters proposed for M8: **Ollama** (development) and **one production vendor** — Claude, as the ratified default. Gemini, OpenAI, and Bedrock adapters wait for a caller, per the no-speculative-ports ruling. The port is proven multi-vendor by having two adapters and one contract suite, not by having five.

---

## Domain model

```
modules/ai_platform/
  domain/
    provider.py      AIProviderAdapter · InferenceRequest/Result · failure taxonomy · registry
    evidence.py      EvidenceSet · EvidenceFact · EvidenceRef · digest
    grounding.py     the five checks and their typed failures
    prompt.py        PromptName · PromptVersion · PromptTemplate · release status
    usage.py         InferenceUsage — tokens, latency, retries; never money
  application/
    infer.py         render → call → validate → record. The only path to a model.
    ports.py         InferenceRepository · PromptRepository
  infrastructure/
    adapters/ollama.py · adapters/anthropic.py
    prompt_loader.py · models.py · repository.py
  prompts/           manifest.json · explanation_narration@1.md
  evaluation/        harness · rubric · datasets/
  public/            AIProviderPort · EvidenceSetBuilder · frozen result views
```

The invariant that shapes the module: **`application/infer.py` is the only code that may call an adapter**, and it always validates before returning. There is no way to obtain unvalidated model output, in the same way there is no way to obtain a `BuyingScore` that disagrees with its ledger.

---

## Storage

One table. Workspace-owned, forced RLS, immutable, registered in `tenancy_policy.py` in the same change.

**`ai_inference`** — one row per model call: `id`, `workspace_id`, `prompt_name`, `prompt_version`, `model_id`, `vendor`, `evidence_digest`, `evidence_refs`, `outcome` (`ok` · `schema_invalid` · `ungrounded` · `transient` · `permanent`), `input_tokens`, `output_tokens`, `latency_ms`, `retry_count`, `correlation_id`, `created_at`.

Two decisions worth stating:

**The rendered prompt text is not stored.** It is fully reconstructable from `prompt_version` plus `evidence_refs`, both of which are stored — so nothing is lost, and Signora avoids accumulating a large, untriaged blob of provider-sourced text with no data classification behind it. **R-05 (prompt data-classification policy undefined) is an open escalation requiring legal input**, and this design routes around needing it resolved before M8 can ship rather than pretending a coding session may decide it.

**Failed calls are recorded, not just successful ones.** An ungrounded output is the single most important thing this platform can measure about itself, and a table that only records successes cannot report the rate. `outcome` is the column that makes AC-9 (the AI evaluation gate) measurable in production rather than only in the harness.

Whether the *output* is stored depends on the scope ruling below; if M8 ships a narration capability it needs a `narrative` table, and if it does not, the harness writes reports to files.

---

## Event model

**M8 publishes no new events.**

A substrate that emits events no module consumes is speculative by definition, and [06-events.md](06-events.md) already reserves `ai_reasoning.completed` (M9) and `ai_research.completed` (M10) for the modules that produce them. If the scope ruling adds a narration capability, it publishes exactly one — `ai.narration_completed` — cataloged in the same change. Not before.

M8 consumes nothing directly either; it is called, not triggered. This also means M8 is unaffected by the open `EventHandler` platform finding, which is a small piece of good news for sequencing.

---

## Scope — grounded narration, under a strict rule

**Ratified 2026-07-29: Option B**, bounded by a rule stated more strictly than the proposal asked for:

> **M8 may only generate language that restates deterministic intelligence already present in its input. It must never introduce a proposition absent from that input.** Reasoning, inference, prioritization and recommendation remain the responsibilities of later modules.
>
> **Stop condition.** If implementation reveals that this boundary cannot be maintained cleanly, implementation halts and the architectural issue is presented before proceeding.

That stop condition is the reason the ruling is safe to take. Four times now, implementation has exposed something an approved proposal got wrong — a forward supersession pointer incompatible with immutability, a `valid_until` promise continuous decay could not keep, a cross-tenant query forced RLS cannot serve, and a delta-based state log that could contradict itself. The risk here is the same shape: a narration that is *useful* may turn out to require one small inferential step, and the moment it does, M8 has become M9 quietly. The rule above makes that a **halt**, not a judgement call made at speed.

The reasoning that produced the ruling follows.

The problem: the YAGNI ruling in [IMPLEMENTATION_ROADMAP.md](../../IMPLEMENTATION_ROADMAP.md) says *"no port is built speculatively … AI Provider Port in M8, with its first concrete implementation."* But a port with adapters and no caller is exactly a speculative port, and an evaluation harness whose only prompt is a test fixture measures the harness rather than the product.

| | **A — substrate only** | **B — substrate + grounded narration (ratified)** | **C — merge M8 into M9** |
|---|---|---|---|
| Ships | Port, Ollama + Claude adapters, prompt registry, harness | The above, plus one prompt and one use case | Substrate plus full reasoning |
| Harness evaluates | A fixture prompt | A shipped prompt on real pipeline output | Real reasoning |
| §20d risk | None | **Real — see below** | Removes the boundary by merging it |
| Cost | Grounding is unproven end to end until M9 | One capability, provably not reasoning | One very large milestone; the harness ships under feature pressure |

**B, drawn narrowly**, and the boundary that makes it defensible is the ratified principle itself:

> *It may generate language. It must never generate facts.*

M8's capability generates **language only, provably**: it narrates the explanation the pipeline has *already computed* — `OpportunityQueries.explanation()`, which already carries the ledger and one `SignalExplanation` per contributing signal — and grounding guarantees the output contains no proposition absent from that structure. It draws no inference. It reaches no conclusion. It renames nothing.

M9 does the opposite: it produces propositions that were *not* in its input. That is what reasoning is, and it is why it needs the harness M8 builds.

So the test separating the two is mechanical rather than a matter of taste: **does the output contain a proposition absent from the input?** For M8, never — asserted by AC-68. For M9, always.

**The counter-argument, recorded because it does not go away with the ruling:** a seller reading M8's paragraph will experience it as *"the AI explained my opportunity"*, and M9 is the module that owns explaining opportunities. The ruling accepts that experiential overlap because the *architectural* boundary is mechanical and testable. It is also precisely why the stop condition exists: the first time a narration needs a proposition its input does not contain, the boundary has moved and the correct response is to halt rather than to widen it.

---

## Task breakdown — T111–T121 · ~15–20 ew

| | Task |
|---|---|
| **T111** | **ADR-0028 — Model runtime by environment.** States the split directly: **development → Ollama** (prompt engineering, UI work, smoke, evaluation, offline demos, regression) · **production → hosted commercial models**, ADR-0012's ratified vendors. Records why ADR-0012's rejection of open-weight self-hosting still stands *for production* and does not bear on a local development runtime, so the architectural record reads consistently rather than looking reversed. Supersedes the relevant ADR-0012 clauses; 08-technology-stack.md gains a **runtime-by-environment** row in the same change. |
| **T112** | Module scaffold, `ai_platform` graph node, import-linter contracts per module pair, 15-project-structure.md corrected (both drifts) |
| **T113** | `domain/provider.py` — port, failure taxonomy, registry, descriptor |
| **T114** | `domain/evidence.py` — evidence set, refusal of mixed workspaces, digest |
| **T115** | `domain/grounding.py` — the five checks, typed failures, fixture corpus including deliberately corrupt outputs |
| **T116** | `prompts/` + manifest + loader + the content-hash immutability test |
| **T117** | Ollama adapter · Claude adapter · **one shared contract suite run against both** |
| **T118** | `application/infer.py` — the only path to a model; retry/timeout policy; usage recording |
| **T119** | Migration `0015`: `ai_inference`, forced RLS, no `UPDATE` grant, `tenancy_policy.py` registration |
| **T120** | `evaluation/` — harness, rubric, golden datasets seeded from M2.0 scenarios, `make eval` |
| **T121** | *(Option B only)* `explanation_narration@1`, the narration use case, its table and event, one smoke stage |

---

## Acceptance criteria

| ID | Criterion |
|---|---|
| **AC-66** | **No module touches a vendor SDK** — every model call passes through `AIProviderAdapter`; asserted by import analysis, not review |
| **AC-67** | **A cross-workspace evidence set is unrepresentable** — construction refuses mixed workspaces, and every ref is re-verified against the requesting workspace before the call |
| **AC-68** | **Output is grounded or rejected** — a fabricated ref, an uncited statement, or a number appearing in no cited fact fails the call with a typed error; verified against recorded fixtures, without a model |
| **AC-69** | **Provenance is complete** — every inference records prompt name and version, model, vendor, evidence digest, refs, usage, latency and outcome; failures recorded as faithfully as successes |
| **AC-70** | **A released prompt cannot change** — editing a released version fails the build; a prompt cannot be used with a model it was never evaluated against |
| **AC-71** | **Nothing branches on vendor** — no business behaviour differs between Ollama and Claude; one contract suite passes against both |
| **AC-72** | **The port reports usage, never money** — no currency-typed field exists on any inference record or result |
| **AC-73** | **The harness is separable and reproducible in its inputs** — `make eval` runs outside `make test`; no Security Invariant calls a model; results are recorded per `(prompt_version, model, dataset_version)` |
| **AC-74** | **Grounding pass rate is 100% on the golden set**, and coverage of load-bearing facts is reported and above its stated floor |
| **AC-9** | **The AI evaluation gate** — golden sets exist, regression is enforced locally before release, evidence completeness is a release gate *(inherited from the roadmap; M8 is where it lands)* |
| **AC-6** · **AC-1** · **AC-13** | Tenancy · event contract · Security Invariants extended, **each proven to fail** when its guarantee is removed |

---

## Demonstration scenario

Against the live stack, as a new smoke stage:

1. A simulated provider payload traverses the eight built stages and an opportunity opens.
2. `explanation()` returns the opportunity, its state history, and the buying score's ledger with one `SignalExplanation` per contributing signal.
3. An evidence set is assembled from that structure — every fact carrying the id the pipeline minted for it.
4. Ollama produces a grounded narrative. Every point cites at least one fact; every number in the prose appears in a cited fact; the model, prompt version, digest, tokens and latency are recorded.
5. **The mutation:** the same evidence set is submitted with one fact removed, so a cited ref no longer resolves. The call fails with `UngroundedOutput`, and the failure is recorded with `outcome = 'ungrounded'`.
6. **The tenancy mutation:** a fact from another workspace is added to the set. Construction raises. Nothing reaches a model.

Step 5 is the milestone's real demonstration. It is what *"proven to fail when its guarantee is removed"* looks like when the component under test is probabilistic — the guard is deterministic even though the thing it guards is not.

---

## Deferred, with reasons

- **Embeddings, pgvector, semantic retrieval** — ratified in ADR-0012, needed by M10's research retrieval, and with no caller in M8. Building it now is the speculative port the ruling forbids.
- **Streaming responses** — a UI concern with no UI until M12.
- **Tool use / function calling** — M10's mechanism. Building it in M8 would be building the agentic engine early, and it carries its own security surface deserving its own review.
- **Gemini, OpenAI, Bedrock adapters** — one contract suite and two adapters prove the port. The rest arrive with callers.
- **A cost/budget governor (R-01)** — M8 makes cost *measurable* by recording usage. Governing spend needs a pricing table, a budget owner, and a policy on what happens when a workspace exceeds it; that is a product decision, not a substrate one.
- **Prompt data-classification policy (R-05)** — an open escalation requiring legal input. M8 minimises exposure by storing refs rather than rendered text; it does not resolve the policy, and must not appear to.
- **Runtime-editable prompts** — same trigger as every other artifact: a non-engineer must tune one without a release. Realistically M12.
- **LLM-as-judge as a release gate** — rejected above, on reproducibility.

---

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| **Prompt injection via provider free text.** A company description is provider-sourced and may contain instructions. | Structured rendering, never raw interpolation; grounding bounds what the output may reference; and decisively, **M6's boundary already holds** — only a human may progress an opportunity, so no model output can commit anything. *M6 is what makes injection non-catastrophic here.* |
| **A prompt tuned on a small local model behaves differently on a frontier one.** | The manifest records evaluated `(model, dataset)` pairs; a prompt may not be used with a model it was not evaluated on (AC-70). The gap is made visible rather than assumed away. |
| **Vendor-side model updates change behaviour with no code change.** | `model_id` is pinned in configuration, never left to a floating alias, and recorded on every inference. Behaviour change becomes traceable to a model change rather than a mystery. |
| **The harness rots** — slow, model-dependent, outside `make test`. | It is a Definition-of-Done item for M9 and M10, not an optional extra: neither milestone closes without a passing golden-set run. Named here so the obligation is inherited rather than rediscovered. |
| **R-01 — cost exposure.** | Usage recorded per call from day one, with outcome. A retry storm is visible in `retry_count` before it is visible in an invoice. |
| **Grounding gives false confidence** — a correctly-cited but mischaracterising sentence. | Stated plainly above as the residual failure mode; measured by the human-rated sample, not claimed to be solved. |

---

## Definition of Done — M8

Per CLAUDE.md §19, binding.

**Implementation** — T111–T121 (T121 subject to the scope ruling).
**Quality** — all tests passing · coverage gate · `make smoke` green · import-linter green · MyPy strict clean · Security Invariants extended and each mutation-proven · **`make eval` green on the golden set**.
**Architecture** — ADR-0028 written · 14-ai-architecture.md marked as built · 08-technology-stack.md, 04-modules.md, 05-module-dependencies.md, 15-project-structure.md (both drifts), 21-intelligence-pipeline.md, 16-architecture-risks.md (R-10) updated · `docs/SESSION_HANDOFF.md` and `PROJECT_STATUS.md` updated and verified against the repository.
**Repository** — committed, **pushed to `origin/main`**, working tree clean.

---

## Approval record

### Ratified 2026-07-29

| | Decision |
|---|---|
| **Module responsibility** | *"How does Signora communicate with a model, and how does it know the answer is grounded?"* — the original wording overlapped M9 and was corrected. |
| **Grounding** | Elevated to a **permanent architectural principle**. The platform constrains what may be *referenced*, never what may be written; the fact universe is **closed**; every statement cited, every citation resolving, every number present in cited evidence. |
| **Rebuildability** | *Facts remain rebuildable. Language is recorded. Meaning is deterministic. Expression may vary.* The M6 rebuild contract is preserved rather than excepted. |
| **Two tiers** | Deterministic correctness in production and the build; probabilistic quality in the harness. **Never mixed** — a failing evaluation must never make deterministic tests flaky. |
| **LLM-as-judge** | **Rejected as a release gate.** Human-reviewed golden datasets and deterministic validation instead. |
| **Scope** | **Option B**, under the strict restatement-only rule and its stop condition. |
| **Ollama** | Permitted for development, recorded in **ADR-0028** rather than silently contradicting ADR-0012. |
| **Frozen packages** | Confirmed: experimental AI infrastructure does not accumulate in a frozen platform package. |

### Recommended 2026-07-29, awaiting confirmation

| # | Question | Recommendation |
|---|---|---|
| 1 | **Module location** *(requested)* | **`modules/ai_platform/`**, under two conditions that matter more than the directory: the substrate **never depends on the pipeline** (narration reaches `opportunity_engine.public` through an `ExplanationSource` Protocol satisfied in `infrastructure/`, the M5B `SignalReader` pattern), and it **freezes after M10, not after M8** — two consumers of genuinely different shape are the evidence an abstraction is real. |
| 2 | **Production adapter for M8** | **Claude**, ADR-0012's default. One local plus one hosted vendor proves the port; the rest arrive with callers. |
| 3 | **Events** | **One** — `ai.narration_completed`, cataloged in the same change. M8 consumes none and is therefore unaffected by the open `EventHandler` platform finding. |

*Nothing in this document has been implemented.*

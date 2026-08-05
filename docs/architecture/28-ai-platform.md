# 28 — AI Platform

> Status: **RATIFIED — 2026-07-29.** Milestone **M8** — **COMPLETE and architecturally closed, T111–T121 plus [ADR-0029](adr/0029-operational-history-durability.md).** `make eval` has been run against a real model and `explanation_narration@1` is released for `llama3.1:8b`. No findings outstanding.
> Audience: engineers, architects, and anyone who has to trust what Signora says.
> Anchors: [14-ai-architecture.md](14-ai-architecture.md) · [ADR-0012](adr/0012-ai-platform-architecture.md) · [04-modules.md](04-modules.md) · [21-intelligence-pipeline.md](21-intelligence-pipeline.md) · [16-architecture-risks.md](16-architecture-risks.md) R-01, R-05, R-10
>
> This document is the ratified design of the AI Platform, being built now. The *Implementation status* block in the approval record tracks what exists.

---

## The question this module answers

**Ratified 2026-07-29.** The AI Platform answers exactly one question:

> **"How does Signora communicate with a model, and how does it know the answer is grounded?"**

It does not answer *what* to say. It answers *what may be said at all*, and it is the machinery that makes every later answer checkable.

### The correction that produced it

The original brief gave the AI Platform the question *"What reasoning should be presented to the user?"* **That is the AI Reasoning Engine's question** — [04-modules.md](04-modules.md) §AI Reasoning Engine already owns it, *"reason over an opportunity, its buying score, signals, Knowledge Graph context … producing structured explanations, prioritization, and analysis"* — and that module is M9. Had M8 answered it, the roadmap would have had two names for one module and the substrate M9 and M10 stand on would have been built as a by-product of a feature.

Accepted 2026-07-29. Everything else in the brief — provider abstraction, Ollama, versioned prompts, an evaluation harness — was already exactly that substrate, so only the framing sentence changed, not the scope.

### Three permanent principles

**Grounding and statelessness ratified 2026-07-29; vendor neutrality 2026-07-30.** Alongside *identity never truth*, *change never significance*, *prioritizes never resolves*, and *intelligence suggests, humans commit*:

> **Grounding.** The AI Platform never constrains what a model writes. It constrains **what the model is permitted to reference.** The deterministic intelligence pipeline defines the universe of facts, and the AI Platform treats that universe as **closed**. Every statement must be supported by citations · every citation must resolve · every numeric value appearing in generated text must exist in cited evidence.
>
> **It may generate language. It must never generate facts.**

> **Vendor neutrality.** **Business behaviour must never depend on which model vendor served a call.** Vendor selection is configuration, not business logic. The AI Platform adapts to vendor-specific APIs *internally*; the rest of Signora stays vendor-neutral, and behaves identically whether the configured provider is Ollama, Claude, GPT, Gemini, Bedrock, or one that does not exist yet. *(Ratified 2026-07-30; CLAUDE.md §10.)*

> **Statelessness.** Every AI invocation depends on exactly three inputs — **prompt · grounded evidence · configuration** — and produces one output: a **grounded structured response**.
>
> **No hidden memory. No cached reasoning. No implicit conversation state.**
>
> If conversational memory is ever wanted, it is a **separate capability with its own name and its own architecture**, never an emergent property of the substrate.

Most of this document is about making **grounding** a schema rule rather than an aspiration. The *Statelessness* section states what the second forbids, and **vendor neutrality** is enforced the same way pipeline neutrality is in the provider layer — one contract suite across every adapter, and nothing outside the module permitted to branch on which one answered.

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

## Statelessness — and what it forbids

**Ratified 2026-07-29.** Grounding says what the model may *refer to*. Statelessness says what the platform may *remember*: nothing.

> `infer(prompt_version, evidence_set, config) -> GroundedResponse`
>
> Two invocations with identical inputs are **indistinguishable in everything except the wording of the output.** No third input exists, hidden or otherwise.

This is a constraint on the substrate, not an implementation preference, and it is worth stating plainly *why*: a stateful inference layer makes every guarantee in this document conditional on invocation history. A grounded response is only checkable against a **known** evidence set — and if the platform silently carried facts forward from a previous call, the set the validator checks against would not be the set the model saw. **Statelessness is what makes grounding verifiable at all**, rather than a second property bolted alongside it.

### The consequences, concretely

**`application/infer.py`** — takes everything it needs as arguments and holds nothing between calls. No memoisation of responses, no accumulated context, no "last evidence set", no conversation buffer. The use case may be constructed once per process or once per request with identical behaviour, and a test asserts that: the same call twice produces the same recorded inputs, and the second call's outcome does not depend on the first having happened.

**Provider adapters** — hold connection-level resources only (an HTTP client, a base URL, credentials from `Settings`). **Never** a vendor conversation handle, a thread id, a server-side session, or a response cache. Vendor APIs that offer stateful conversations are used in their stateless form; the adapter's job is to translate a complete request, and a vendor feature that requires remembering the last one does not cross the port. `InferenceRequest` carries the entire request.

**The provider registry** — populated once at the composition root from configuration, then read-only. It maps a name to an adapter and nothing else: no per-workspace state, no usage accumulators, no adaptive routing that learns from previous calls. Routing is configuration, per ADR-0012.

**Request lifecycle** — a workspace's evidence never outlives its invocation. Nothing is retained after the response is validated and the inference row is written, which is also the cleanest possible answer to cross-tenant leakage through a cache: there is no cache to leak from. This is the same reasoning that made a mixed-workspace `EvidenceSet` unrepresentable rather than merely forbidden.

**Replayability** — with no hidden input, the *inputs* to any recorded inference are exactly reconstructable from `prompt_version` + `evidence_refs`, which is precisely the claim made under *reproducibility, honestly framed* below. **That claim is only true because of this principle.** A stateful platform could not honour it: re-issuing the same recorded inputs would not re-create the same conditions.

**Horizontal scaling** — falls out for free, and is required by the Infrastructure Contract (CLAUDE.md §20b): no process holds state another needs, so scaling to *n* replicas changes throughput only. Worth noting the ordering — statelessness was adopted for verifiability, and deployability is the side effect, not the motive.

### Why this matters for Business Capability Verification

The scenario layer proposed for after M8 is an executable specification: a complete customer workflow, run start to finish, asserted in the customer's vocabulary. Such a suite is only trustworthy if a scenario's outcome depends solely on what the scenario itself set up.

A stateful AI Platform would break that at the root — a scenario could pass because an earlier scenario warmed something, and fail when run alone or reordered. That failure is close to undiagnosable, and the usual resolution is that somebody deletes the scenario.

**Because the platform is stateless, an AI step inside a scenario is a pure function of the evidence that scenario constructed.** Scenarios stay independent, order-free, and individually runnable. The narration step remains non-deterministic in its *wording* — which is exactly why a scenario asserts grounding and citation rather than prose — but it is fully determined in its *inputs*, and that is what a specification needs.

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

### A prompt is a first-class engineering artifact

*Ratified 2026-07-30.* `manifest.json` carries six fields per prompt, not one:

| Field | Why it is required |
|---|---|
| **Version** | Provenance is meaningless without it — every result records which version produced it |
| **Owner** | A prompt is domain IP and behaves like code; unowned code is unmaintained code |
| **Evaluation history** | What was measured, when, against which golden dataset |
| **Supported models** | See the release rule below |
| **Supported datasets** | An evaluation is only evidence about the data it ran on |
| **Release history** | When a version became usable, and what superseded it |

> **A prompt is not "released" until it has been evaluated against its supported `(model, dataset)` combinations**, and it may never be used with a pairing absent from that record.

This is the direct consequence of [ADR-0028](adr/0028-model-runtime-by-environment.md): development runs on Ollama, production on hosted models, and a prompt tuned against a small local model has **not** been shown to behave on a frontier one. The manifest is where that gap is stated rather than assumed away.

Two further rules go beyond the existing artifact pattern:

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

**`ai_inference`** — one row per model call: `id`, `workspace_id`, `correlation_id`, `prompt_name`, `prompt_version`, `prompt_fingerprint`, `requested_model`, `served_model`, `vendor`, `evidence_digest`, `evidence_refs`, `outcome` (`ok` · `schema_invalid` · `ungrounded` · `transient` · `permanent`), `input_tokens`, `output_tokens`, `latency_ms`, `retries`, `detail`, `created_at`.

*(As built, migration `0015`. The proposal listed `model_id` and `retry_count`; the built columns split the first into **requested** and **served** — a tag may resolve to a specific build, and "the model changed underneath us" is otherwise indistinguishable from "the prompt got worse" — and renamed the second to match `InferenceUsage`. `prompt_fingerprint` and `detail` were added; see the T119 notes below.)*

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
| **T120** | `evaluation/` — harness, rubric, golden datasets seeded from M2.0 scenarios, `make eval` ✅ *(built and run; prompt released for `llama3.1:8b`)* |
| **T121** | *(Option B only)* `explanation_narration@1`, the narration use case, its table and event, one smoke stage ✅ |

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
| **AC-74** ✅ | **Grounding pass rate is 100% on the golden set**, and coverage of load-bearing facts is reported and above its stated floor — *satisfied 2026-07-30: 2/2 cases, 0 grounding failures, 0 schema failures, 0 retries, coverage 1.000 against a floor of 0.66* |
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
| **Statelessness** | Elevated to a **permanent architectural principle**. Every invocation depends only on prompt · grounded evidence · configuration, and produces a grounded structured response. No hidden memory, no cached reasoning, no implicit conversation state. Conversational memory, if ever wanted, is a separate capability. |
| **Module location** | **`modules/ai_platform/`**, under two conditions that matter more than the directory. The substrate **never depends on the pipeline** — narration reaches `opportunity_engine.public` through an `ExplanationSource` Protocol satisfied in `infrastructure/` (the M5B `SignalReader` pattern), so `domain/` and `application/` know nothing of opportunities or scores. And it **freezes after M10, not after M8**: one consumer proves nothing; two of genuinely different shape begin to validate an abstraction. |
| **Dependency direction** | The AI Platform never depends directly on the Opportunity Engine, Buying Score Engine, Signal Engine or Business Event Engine. It consumes **stable ports**; business modules supply adapters. The platform stays unaware of where the information originated. |
| **Production adapter** | **Claude** only, alongside Ollama for development. Gemini, OpenAI, Azure and Bedrock adapters wait for real callers — the abstraction exists to make additions easy, never to justify speculative ones. |
| **Events** | **One** — `ai.narration_completed`, cataloged in the same change. M8 consumes none, and is therefore unaffected by the open `EventHandler` platform finding. |
| **Stop condition** | **Binding.** If implementation requires a proposition that does not already exist within deterministic intelligence, implementation **stops** and the architectural issue is presented. Reasoning is not quietly moved into M8. |

### Implementation status

**T111 ✅** — [ADR-0028](adr/0028-model-runtime-by-environment.md) written as a refinement of ADR-0012, not a reversal; [08-technology-stack.md](08-technology-stack.md) records runtime by environment.

**T112 ✅** — `modules/ai_platform/` scaffolded (`domain` · `application` · `infrastructure` · `public`); the module added to [04-modules.md](04-modules.md) and to the graph in [05-module-dependencies.md](05-module-dependencies.md); **four import-linter contracts** registered (21 total, from 17); **8 Security Invariants**, each mutation-proven; both [15-project-structure.md](15-project-structure.md) drifts corrected.

**T113 ✅** — `domain/provider.py` and `domain/usage.py`: the port, a semantic failure taxonomy, the descriptor, and the registry, published through `public/`. **26 tests**, six mutation-proven guarantees. Two departures, recorded below.

**T114 ✅** — `domain/evidence.py`: the closed evidence set, its builder, typed values, the citation ref, and a stable digest. **44 tests**, ten mutation-proven guarantees. One departure and one defect found by mutation, recorded below.

**T115 ✅** — `domain/grounding.py` and `domain/errors.py`: the five checks, distinguishable violations, the deterministic report, and a schema derived from the validating type. **35 tests** against a deliberately corrupt corpus, eleven mutation-proven guarantees. One defect found by mutation, recorded below.

**T116 ✅** — `domain/prompt.py`, `infrastructure/prompt_loader.py`, `prompts/manifest.json`, and `explanation_narration@1` as a **draft**. Content-hash identity, the enforceable release rule, append-only evaluations. **34 tests**, ten mutation-proven guarantees. One departure, recorded below.

**T117 ✅** — the Ollama and Anthropic adapters, a shared transport-to-semantics mapping, and **one contract suite run against both**. **53 tests**, eleven mutation-proven guarantees. Two decisions recorded below.

**T118 ✅** — `application/infer.py`, `application/render.py`, `application/ports.py`, `domain/record.py`: the only path to a model, an explicit seven-stage lifecycle, semantic retry, and a record written on every outcome. **31 tests**, twelve mutation-proven guarantees.

**T119 ✅** — migration `0015`, `infrastructure/models.py`, `infrastructure/repository.py`: the `ai_inference` table with forced RLS, no `UPDATE` grant, and registration in `tenancy_policy.py`. **14 tests**, twelve mutation-proven guarantees. Two defects in T118 found and fixed; see below.

**T120 ✅** — `evaluation/` (dataset · rubric · report · harness · release · `__main__`), `infrastructure/explanation.py`, `infrastructure/settings.py`, the golden dataset seeded from the M2.0 baseline scenario, and `make eval`. **46 tests**, twelve mutation-proven guarantees, 22 import-linter contracts. One structural exception introduced and invariant-enforced; see below.

**T120 has been run.** `make eval` passed against `llama3.1:8b` on 2026-07-30, and `explanation_narration@1` is **released for that model and no other**. The measurement is recorded in `prompts/manifest.json`; AC-74 is satisfied. See *"The first genuine evaluation"* below for the observed output and what it cost.

**T121 ✅** — migration `0016` (`ai_narration`), `domain/narration.py`, `domain/events.py`, `application/narrate.py`, `infrastructure/composition.py`, `ai.narration_completed` cataloged in [06-events.md](06-events.md), and smoke stage **14i**. **17 tests**, nine mutation-proven guarantees. One material finding recorded below.

**M8 implementation is complete.**

`interface/` is deliberately absent: M8 has no HTTP surface, the layering contract marks the layer optional, and a directory created for a caller that does not exist is the speculative structure CLAUDE.md §6 forbids.

---

## As built: departures, recorded as they arise

### Departure 1 — the registry offers no vendor-keyed lookup

The proposal copied `ProviderRegistry`, which exposes `get(provider)`. The AI Platform's registry deliberately does not: its only routing method is **`for_model(model)`**.

The difference is real rather than stylistic. A data sync genuinely targets a named provider — *fetch Apollo's view of this company* is the request, and Apollo is part of it. An inference targets a **model**, and which vendor serves that model is an operational detail the caller has no business knowing.

This is what turns vendor neutrality from a rule people remember into a property of the type: **business code that cannot name a vendor cannot branch on one.** A test pins the registry's public surface, so adding `get(vendor)` fails the build.

### Departure 2 — the failure taxonomy is split by whether a vendor exists

`ProviderError` takes a vendor unconditionally, because every failure it models is a vendor's. Copying that shape here produced error messages that lie: a request naming no model never reached a vendor, and a model no adapter serves was answered by *nobody*. Both were initially stamped with a placeholder vendor, which would have put a false attribution in the first place an engineer looks during an incident.

The taxonomy is therefore split under one base:

```
AIPlatformError
├── InferenceRequestError      caller bug, before a vendor is chosen — no vendor
├── AIRegistrationError        composition-time misconfiguration — names the adapter
├── ModelNotRegisteredError    routing: nobody serves this model — no vendor
└── AIProviderError            a vendor call failed — always names the vendor
    ├── AITransientError → AIRateLimitedError
    └── AIPermanentError → AIOutputUnusableError
```

`AIOutputUnusableError` is deliberately distinct from a grounding failure: this is the *transport* contract breaking (truncated, unparseable), that is the *content* contract breaking (a valid structure making an unsupported claim). Conflating them would hide a systemic vendor problem inside a per-call quality metric.

Found while writing the code rather than while reviewing it — the fifth time implementation has corrected an approved design.

### Registration refuses two misconfigurations outright

An adapter that cannot constrain output to a schema, and two adapters claiming the same model. Both are caught at composition, where a human is present and a stack trace is cheap. The second matters more than it looks: two adapters serving one model makes routing depend on registration order, and provenance would record whichever happened to win.

---

### Departure 3 — insertion order is discarded, not preserved

The proposal said facts were held in a tuple and said nothing about order, which in practice would have meant *insertion order*. They are held in **canonical order** (by kind, then id) instead, and the digest is computed over that.

Order is not information about evidence. Letting insertion order survive would make the rendered prompt — and therefore the model's output — depend on how the caller happened to loop, which is a hidden input, and statelessness exists precisely to forbid those. A narrative needing chronology sorts on a fact's own timestamp, explicitly.

`assembled_at` is excluded from the digest for the same reason in reverse: it records *when* evidence was gathered, not what it contains, and including it would give identical evidence a new identity on every assembly — so replay comparison would never match.

### Defect found by mutation — the canonical form did not encode type

Values were canonicalised with `str()`, and the mutation that should have proved the `bool` branch load-bearing **passed**. The comment justifying that branch was simply wrong.

Investigating it surfaced a real defect: without a type tag, `True` and the string `"true"` produced identical canonical forms, as did `1` and `"1"`, and a `date` and its own ISO text. **Two different facts would have digested identically**, and a digest that cannot distinguish them cannot answer *did these two inferences see the same evidence?* — which is the only question it exists to answer.

Values are now tagged with their type (`b:` `i:` `n:` `t:` `d:` `s:`), with `bool` tested before `int` and `datetime` before `date` since each is a subclass of the other. Eight cross-type pairs are asserted distinct, and the tag each type receives is pinned directly — because reversing a subclass check mislabels a value without colliding, and a canonical form nobody can read back is one nobody can debug.

**This is the value of insisting a mutation actually bites.** A passing mutation is not a formality to wave through; here it was the only thing pointing at a live collision.

---

### Departure 4 — grounding knows nothing about narration

The proposal defined `GroundedNarrative` with a `summary` and `points`, and put it in grounding. Grounding instead defines only **`GroundedStatement`** — text plus citations — and a `GroundedOutput` base that subclasses shape as they like.

Two reasons. The narration wrapper is *language*, and quality 6 of the brief keeps language out of this domain. And M9's reasoning result and M10's research artifact are different shapes carrying the same obligation, so the unit they share is the statement, not the wrapper.

It also closed a hole the proposal had: `summary: str` carried no citations, so the one sentence a reader looks at first would have been the one statement exempt from grounding.

**The requested schema is derived from the validating type** (`output_schema(T)` → `T.model_json_schema()`), so the shape asked for and the shape enforced cannot drift. A hand-written schema would be a second definition of one contract, and within a year the disagreement would look like a model regression.

### Departure 5 — one error root, extracted

`AIPlatformError` declared itself *"the base for everything this module raises"* while `EvidenceError` descended from `ValueError` alone. A caller writing the broad `except` the docstring promised would have missed the module's most serious failure — a cross-workspace evidence set.

The base now lives in `domain/errors.py` and every failure descends from it. A base class that does not actually cover its module is worse than none: the gap surfaces as an unhandled exception in production rather than as a review comment.

### Defect found by mutation — a dead guard, again

`_numbers_in_evidence` skipped boolean attributes, with a comment claiming `True` would otherwise license the figure `1`. **The mutation removing it passed.** `str(True)` is `"True"`, which contains no digits, so the guard could never have done anything.

Removed, and the test that appeared to cover it now says what is actually true: a boolean attribute licenses no figure *because of how it reads*, not because code defends it.

This is the second time in two tasks a surviving mutation exposed a false justification rather than a missing assertion. **A guard nobody can make fail is not protection — it is a claim.** Two other mutations (`ON DELETE`-style quantity scoping, decimal normalisation) also survived first and produced real tests rather than being waved through.

---

### Departure 6 — release is derived, and two manifest fields were dropped

The ratified manifest carried six fields: version, owner, evaluation history, supported models, supported datasets, release history. Two are gone, and one changed shape.

**`status` does not exist.** A declared status could say *released* while no evaluation supported it — a field that can lie about the thing beside it. `is_released` is **derived**: a prompt is usable exactly where it has an evaluation that passed. Nothing to keep in sync, and nothing to forge.

**`supported_models` and `supported_datasets` do not exist either.** They would be a second statement of what the evaluations already record, and the two would eventually disagree. `supports(model, dataset)` reads the evaluations directly.

**`release_history` was dropped as speculative.** No consumer today; supersession is implicit in the version sequence, and evaluations carry their own dates. It arrives if something needs it.

**`owner` was kept, and is the one field with no code consumer.** It answers *who reviews a change to this*, which is a real question about an artifact that alters model behaviour without altering code. Flagged rather than smuggled.

The **fingerprint covers name, version and text — never evaluations**. They are observations *about* an artifact, not part of it, exactly as an observation is not the thing observed; a fingerprint that moved every time a prompt was measured could not identify anything. This is what makes append-only evaluation and immutable identity coexist.

### What the content-hash lockfile does and does not promise

`PINNED_FINGERPRINTS` in the test suite pins every shipped version, draft included. It does **not** make an in-place edit impossible — nothing in a repository can, since a determined change can edit the file, the manifest, and the test together. It makes one impossible to perform *quietly*: the edit now touches a test literal, which is a deliberate reviewable act rather than a diff nobody reads.

Append-only evaluation is enforced the same way. The loader refuses a duplicate record; truncation across time is a review-and-git property, and is stated as such rather than claimed.

### `explanation_narration@1` shipped as a draft, and was unusable *(as at T119)*

It had passed no evaluation, so the release rule refused it — asserted by test. That was the system working rather than an omission: **T120 is what earns a prompt its release.** Shipping the artifact then let the loader, the identity scheme and the release rule be exercised against something real instead of a fixture.

> **Superseded by T120**, which measured it against `llama3.1:8b` and earned the release it now holds. Left here in the past tense rather than deleted: the sequence is the point, and a record of the past is dated rather than rewritten.

---

### Decision — both adapters speak HTTP, not a vendor SDK

Neither the `anthropic` nor the `ollama` package is used. Adding either would be a **new dependency requiring approval** (CLAUDE.md §6), and each brings its own retry and timeout behaviour to argue with the platform's. `httpx` is already ratified.

The stronger reason is what it does to the contract suite: with one transport under both adapters, Ollama and Anthropic agreeing means *the adapters* agree — not that two SDKs happen to normalise the same way. The cost is that request and response shapes are written by hand and can drift if a vendor changes its API; the pinned `anthropic-version` header bounds that on the production side. **If the SDKs are preferred, that is an approval to give and this reverses cleanly** — nothing above the adapter would change.

### Decision — no configuration was added, deliberately

Both adapters take their client, base URL, key and model set as constructor arguments. Nothing was added to `signora_platform/settings.py`.

That defers a question worth deciding rather than assuming: **the platform is frozen (§20a), and the Infrastructure Contract (§20b) requires every value to arrive through `Settings`.** No module has ever added a field to it. Whether doing so counts as *using* the platform or *changing* it is a ruling, and it belongs at the composition root — T118 — not smuggled in beside an adapter.

### The suite is the specification, and it caught a fourth dead guard

Every behaviour is stated once and run against both adapters unmodified: structured output reaches the vendor · content is a string whatever the vendor returned · truncation is `AIOutputUnusableError`, never a grounding failure · 5xx and timeouts are transient · 429 carries the vendor's stated wait, or `None` when it gave none · 401 and 403 are permanent · no vendor exception escapes · the adapter holds nothing between calls.

Two further tests assert the two adapters produce *identical* results and classify identical failures identically — vendor neutrality demonstrated rather than described.

The 401/403 branch survived its mutation: those statuses already fall through to permanent, so the branch changes only the **message**. Since a rejected credential is the most common misconfiguration there is, the diagnostic *is* the property — so it is now asserted, and the mutation bites. Fourth instance in four tasks of the same finding.

**Nothing in this suite calls a model.** It proves adapters translate correctly; whether a model reasons well is the harness's question (T120), and conflating them is what the two-tier split exists to prevent.

---

### The lifecycle, and what is not in it

    resolve prompt → render → select provider → execute (retry) → parse → ground → record → return

Nothing happens between those stages. `Infer.execute` is the only way to obtain model output, and there is no way at all to obtain *unvalidated* output — the same shape as `BuyingScore.projected_from` being the only constructor of a score.

**Retry is confined to transport.** Transient failures retry with exponential backoff, or with the vendor's stated wait when it gave one. Permanent failures raise on the first attempt. **Schema and grounding failures are never retried** — they are content failures, and quietly re-rolling one would burn tokens while making the ungrounded rate unmeasurable, which is the one number this platform most needs about itself.

**Every outcome is recorded**, including the ones that failed before a model answered. A table holding only successes cannot report a failure rate. A transport failure records zero usage rather than none, because a failed call still happened and a row with no usage is indistinguishable from one never attempted.

### Applying *behaviour exists exactly once* to the request

`InferenceRequest.temperature` and `.timeout_seconds` **lost their defaults** and are now required. Once `InferencePolicy` owns those values, a default on the request would be a second place deciding them — and the two would eventually disagree with nobody noticing, since both are plausible. The policy is now the single source, and it is provider-agnostic, so no adapter's own idea of a timeout can leak upward.

`PromptVersion.require_model` was added alongside `require(model, dataset)`. These answer different questions rather than duplicating one: at **runtime** there is no dataset — the dataset is what an evaluation was *conducted on*, and it belongs to the record supporting a release rather than to the call relying on it.

### Configuration — the ruling, and the principle it produced

**Ratified 2026-07-30.** The question raised at T117 and made due at T118 is answered: **`AISettings` is owned by `modules/ai_platform/infrastructure/`, not added to `signora_platform/settings.py`.**

The reasoning generalises beyond this module, and was elevated to a permanent principle (CLAUDE.md §2, §6):

> **Configuration is always a typed Settings object owned by the module that owns the behaviour.**

The rule was never really *"configuration must go through `Settings`"* — that was one file mistaken for the principle. Platform `Settings` holds the **platform's** configuration; `AISettings` holds the AI Platform's; `ReasoningSettings` will hold M9's. The composition root is the only place independently owned Settings objects meet, and **no module ever learns where another module's configuration came from.**

What the alternative would have cost is the argument: adding `ai_*` fields to the frozen platform grows its public surface for one module, and M9, M10 and M13 would each ask for the same — until the substrate every module imports is the registry of every module's configuration surface. Ownership and configuration have to align, or the platform slowly becomes responsible for everything.

Everything the old rule protected still holds: values are typed and validated, no module reads `os.environ`, and construction happens once, at the composition root (T121).

---

### T119 — the table, and two defects it exposed in T118

`ai_inference` introduces a **fourth kind of data**. Everything before it is derived intelligence (rebuildable), customer configuration (irreplaceable), or workflow state (unreproducible). This is an **operational record**: Signora's account of its own behaviour. Nobody authored it, nothing regenerates it, and it is the only place the ungrounded rate can be read from — which is how R-10 stops being an open risk and becomes a number.

**No foreign key points anywhere.** The substrate does not learn the pipeline's vocabulary at the database any more than it does in `domain/`. A reference to `opportunity` here would have been the quiet way to make the module unextractable whatever the import graph said.

**Three constraints state what a row may claim**, enforced by PostgreSQL rather than by the writer — because the writer is exactly what a future change replaces:

- *A success cannot come from nobody.* `outcome = 'ok'` requires both `vendor` and `served_model`. Output that arrived from nobody is a result nobody can attribute, and an inference nobody can attribute is not evidence of anything (AC-69).
- *A failure always states a reason, and a success never carries one.* Both halves matter: a failed row with no `detail` is an incident with no first line, and a successful row carrying one means something was swallowed.
- *Usage is non-negative.* No call consumes a negative amount of anything.

**There is deliberately no `CHECK` enumerating the five outcomes.** `InferenceOutcome` is the authoritative representation; a SQL list of the same five strings would be a synchronised second copy that goes stale silently. One test pins `InferenceOutcome.OK.value == "ok"`, because the two constraints above are written against that literal and would otherwise stop applying rather than fail.

**`detail` is bounded at 1024 characters, and the writer truncates to fit.** The bound is load-bearing rather than decorative: a grounding report quotes short excerpts of the model's own output, and without a ceiling this column is how the untriaged blob of text the design avoids would accumulate anyway. Truncation belongs to the writer because the *most* thoroughly ungrounded output produces the *longest* message — losing that row to a length error would discard exactly the evidence the table exists to keep.

#### Defect 1 — a provider failure recorded no vendor

`_write` derived `vendor` from the response, so a failure that never produced one recorded `vendor = NULL`. But **every `AIProviderError` names the vendor that raised it** — that is the whole point of Departure 2. A rate-limit incident was therefore attributable to nobody, which is the same defect as a false attribution wearing the opposite coat, and it made R-01's stated mitigation unusable: you cannot attribute a retry storm to a vendor the row declines to name.

`vendor` and `served_model` are now passed explicitly rather than derived together, because **they are not known together**: a failure that reached a vendor names it while nothing served the call.

#### Defect 2 — a failed call recorded zero retries

The retry count lived inside the retry loop and only travelled out on success; the failure path passed a hardcoded `0`. So a call that failed after three attempts recorded `retries = 0` — **a retry storm was invisible in exactly the rows that prove one happened.**

The count now travels out inside a private `_ProviderCallError`, which never escapes `execute` (asserted: the caller still catches the vendor's own exception, with the wrapper suppressed from the traceback). A permanent failure raised on the second attempt is a different operational fact from one raised on the first, and both are lost if only the error travels.

Neither defect was caught by T118's twelve mutations, and the reason is worth recording: **every one of them was aimed at the success path or at whether a row was written at all.** Nothing asked whether a failed row was *correct*. The guarantee "failures are recorded as faithfully as successes" was tested as *recorded*, not as *faithfully* — which is a gap in how the mutation was chosen, not in the technique.

#### Three claims corrected while passing through

Documentation drift found in files this change touched, corrected rather than left (CLAUDE.md §12):

- `migrations/env.py` claimed migrations use *"the exact same `get_settings()` configuration the application uses — there is no separate migration-specific database configuration"*. It reads `os.environ` directly, and the configuration is separate **on purpose** (CLAUDE.md §8: a runtime service connected as the owner is exempt from RLS on every table it touches). The claim inverted a security property.
- The same file required every module's ORM models be imported for autogenerate. Seven modules never were, and nothing broke — migrations here are hand-authored, and autogenerate cannot produce an RLS policy anyway. The rule had no consumer.
- `test_tenancy_policy.py` justified the `DELETE` grant on immutable tables as *"both tables hold derived data"*. That stopped being true at M6 and again here. Erasability is a property of the **tenancy** model — a workspace that cannot be deleted is a retention problem on every table it owns. The assertion was right; the reason given for it was not.

---

### T120 — the harness, and the circularity it had to resolve

**The release rule blocks the evaluation that earns it.** A prompt may be used only with a model it has passed evaluation against; evaluating it requires calling it. Both cannot come first.

Resolved **structurally rather than with a flag**. `Infer.execute` enforces the rule and is the only path a request may take; `Infer.measure` runs the identical lifecycle without it, and **a Security Invariant asserts it is called from `evaluation/` and nowhere else**, with a positive control asserting `execute` still enforces the rule. A boolean `skip_release_check` would have been smaller and would eventually have been passed `True` by a request path at three in the morning; an exception that a test can locate by name cannot spread quietly. Both mutations bite.

Everything else about the two paths is identical, deliberately: a harness measuring a different code path from the one production runs measures the wrong thing.

#### Golden datasets are recorded, not generated

The dataset is produced **once** from the M2.0 baseline scenario by running the real pipeline (`tests/ai_platform/seed_golden_dataset.py`), then checked in, reviewed, and versioned. **Seeding needs the pipeline; evaluating does not** — an import-linter contract forbids `evaluation/` from importing any business module, so a change upstream cannot move a prompt's score without the prompt, the model or the criteria changing.

Hand-authoring the cases was rejected: it would mean inventing business data and then measuring a model's fidelity to an invention, with the evidence shaped by what is convenient to narrate. Every fact in the shipped set traces to a simulated provider payload and the id the pipeline minted for it.

`fingerprint` covers `cases` and nothing else, so a reformat is not a revision and an edited expectation fails to load. Revising a case is a version bump, and every result records `dataset_version`.

#### The rubric measures; the domain judges

Three deterministic measures, **no weighting between them and no combined score**: grounding failures (must be zero), schema failures (must be zero, counted separately because a model that cannot hold a structure and a model that invents facts are different problems), and coverage of load-bearing facts. A weighted total would let strong coverage compensate for a grounding failure, and grounding failures are not compensable.

The criteria live in `Evaluation.passed`, in the domain, beside the release rule that consumes them. `rubric.criteria()` *renders* them by reading `MINIMUM_COVERAGE` rather than restating it — a test asserts that function contains no number of its own, because a literal there would be a second representation of a release rule.

`MINIMUM_COVERAGE = 0.66` is the one judgement in the criteria, and it is stated with its reasoning: not 1.0, because a narrative that must mention every load-bearing fact is a list rather than a summary and the harness would be measuring length; not lower, because below two thirds the strongest contribution to a score can go unmentioned while the run still passes.

**Coverage is measured from citations, not prose.** A narrative mentioning a figure without citing its fact is making an uncited claim, which grounding already refuses — so the citation is the only evidence of coverage that means anything.

#### A run that did not complete produces no record

A transport failure **abandons** the run rather than lowering its score. A vendor being down says nothing about a prompt, and a partial average recorded as a result would grant a release on the cases that happened to succeed. `EvaluationAbandonedError` is the absence of a measurement, deliberately distinct from a failing one.

Failing runs *are* recorded. A manifest holding only passes shows a prompt with a clean history and no sign it was measured and found wanting — and the next engineer repeats the work.

#### Configuration, as ruled

`AISettings` lives in `modules/ai_platform/infrastructure/`, owned by the module whose behaviour it governs, constructed only at the composition root (`evaluation/__main__.py` for a harness run). `signora_platform/settings.py` was not touched. There is deliberately **no fallback from a hosted vendor to Ollama**: a production service that could quietly reach a local runtime when its vendor was unreachable would serve customers from a model nothing evaluated.

#### The first genuine evaluation

Run 2026-07-30 against `llama3.1:8b` on the development workstation. The observed output, verbatim:

```
prompt   explanation_narration@1  be511c4152c8
model    llama3.1:8b
dataset  explanation_narration@1  2cce0492a6bc
rubric   v1    run on 2026-07-30

cases
  ok   northwind                        coverage 1.00
  ok   contoso                          coverage 1.00

sample size         2
grounding failures  0
schema failures     0
transport failures  0
retries             0
coverage            1.000

release             EARNED
```

*(The recorded run, after retry reporting was added. The **first** run — before the `retries` line existed — reported the same result but needed three calls for two cases, because a cold model load pushed the first past the 60-second policy timeout. Both facts are below.)*

`explanation_narration@1` is now **released for `llama3.1:8b` and refused for every other model** — asserted by test, including `claude-sonnet-4-5`. That refusal is the point: a prompt tuned against an 8B local model has not been shown to behave on a frontier hosted one, and production runs on hosted models (ADR-0028). **M8 ships a prompt that production cannot yet use**, and closing that gap is an evaluation run against the production model, not a code change.

**What it cost, recorded because performance is an observation.** Quadro T1000 (4 GiB VRAM, 3.2 GiB available), 12 cores, 15 GiB RAM; CUDA compute 7.5; context 4096, prompt 695 tokens.

| | |
|---|---|
| Model cold-load | 29.4 s |
| Case latency | 42.9 s · 51.7 s |
| Calls for two cases, cold | **three** — the first timed out |
| Calls for two cases, warm | two — no timeout, `retries 0` |

**On the cold run, the first call hit the 60-second policy timeout and was retried.** Cold-load plus generation exceeded `InferencePolicy.timeout_seconds`; the retry succeeded, so the case ended `ok` and `transport_failures` is correctly 0. The retry policy worked exactly as designed — and the margin on this hardware is thin: 43–52 s of generation under a 60 s ceiling leaves a cold start no room. On production hosted models this is not expected to bind, so **the timeout is not changed on the strength of one workstation's numbers**; it is recorded as an observation for the M9 latency budget.

**A gap this run exposed in the harness itself, and closed before T121.** The report did not surface retries: one call timing out and being retried is materially different from a clean run, and nothing in the printed output or the recorded `Evaluation` said it happened — it was found by reading the Ollama server log. Under *observability is a product capability* that is a defect, not a nicety.

`RunLog` closes it. It is an `InferenceRecorder` — the same port the production recorder satisfies — that keeps its records in memory and lets the harness read back what happened. **One object in two roles**, wired once at the composition root: the port `Infer` writes every outcome to, and the record the harness reads. It replaced `_StdoutRecorder`, which never printed to stdout and whose name was therefore a small lie.

Two details that matter more than the plumbing:

- **Lookup is by `correlation_id`, never by position.** The harness knows the id it sent for each case, so nothing depends on records arriving in submission order — an assumption that holds today and breaks the first time cases are evaluated concurrently.
- **A failed case reports its retries too**, read from the log rather than from a returned record. `Infer` writes a record on every outcome but *returns* one only on success; a grounding failure raises and takes the returned record with it. Without the log, precisely the failures worth diagnosing would have reported zero.

`retries` is now on `Evaluation` and therefore durable in the manifest — the printed report is lost when the terminal closes. It is **deliberately excluded from `Evaluation.passed`**: retrying is what the platform is *supposed* to do about a transient failure, and penalising a prompt for its provider's bad afternoon would make the release criteria measure the wrong thing. It is a cost and reliability signal (R-01), not a quality one.

**The measurement was re-taken rather than back-filled.** The first run's recorded evaluation predated the field, and defaulting it to `0` would have written a false fact about a run that had one retry. The entry was cleared and `make eval --record` re-run against the same model and dataset. The second run reported **0 retries** — genuinely, on a warm model: two `/api/generate` calls, no timeout, confirmed against the server log. Observing zero proves nothing about the plumbing, which is why all six mutation-proven tests for it force a retry.

#### The runtime is installed rootless, and that is now the documented path

`sudo` requires interactive authentication on this workstation, so the official `curl … | sh` installer cannot run. The release tarball is extracted into `~/.local` and the server runs as the developer's own user: no system modification, no systemd unit, removable by deleting a directory, and the download verified against the published SHA-256 rather than a script piped into a shell. `make eval`'s failure message now names this path alongside the official one, because the official one does not work without root.



### T121 — composition, and a finding it exposed

**Nothing new was invented.** Every collaborator existed and was verified in T111–T120; `Narrate` adds sequencing. The stop condition was checked before a line was written and was not triggered: `Narration` is text plus citations, and grounding refuses any statement that cites nothing resolvable — so **a proposition the pipeline did not compute cannot be expressed**, which is why the M8/M9 boundary is mechanical rather than a matter of taste.

**A fifth data category, ratified 2026-07-30: the materialized AI artifact.** Not derived intelligence (rebuildable), not customer configuration (irreplaceable), not workflow state (unreproducible), not operational history (`ai_inference`). It is a grounded explanation deliberately persisted for auditability, user experience and provenance — and the first row in the platform holding text a customer reads.

**Immutable, for a reason specific to the category.** A stored narration records what the platform *actually produced* at that moment. Prompt evolution produces a new narration; editing one would destroy the only record of what a customer was shown and silently invalidate every audit citing it. No `UPDATE` grant, no `UPDATE` policy, and "current" is a query over timestamps rather than a mutable flag that could disagree with the rows.

**Provenance is denormalized on purpose**, so the row answers *which evidence · which prompt · which model · which inference · when* without a join. `inference_id` carries **no foreign key** to `ai_inference`: the two have different lifetimes, and a customer-visible artifact must not become unreadable because the operational row describing it aged out under a retention policy.

**The subject is addressed in the module's own vocabulary** — `subject_kind` + `subject_id`, the `EvidenceRef` shape. An `entity_id` column would have put the pipeline's vocabulary into the substrate's schema, the same mistake `ai_inference` avoids by carrying no foreign key at all.

**The event carries identity and counts, never the prose.** `statement_count` says how many; nothing says what. A paragraph in an envelope makes every wording change an event-contract change, and copies customer-visible text into a queue whose retention nobody has reasoned about.

**Smoke stage 14i does not call a model, deliberately.** `make eval` is the only command in this repository that does; Ollama is never a production dependency (ADR-0028), and a deployment gate needing a GPU is a gate people learn to skip. What 14i proves is the deterministic half, and it is the half worth gating on: composition wires, evidence assembles from the real pipeline, a grounded narration is stored with complete provenance, the event reaches the outbox — and **an invented proposition is refused rather than stored.**

#### Closed finding — operational history now outlives the work it describes

Found by writing the demonstration, and material enough to state plainly.

`Infer` writes an `ai_inference` row on **every** outcome, which is what AC-69 asks for. But `tenant_scoped_session` wraps `session.begin()`, so when a grounding failure propagates out of the unit of work, the transaction rolls back and **takes the failure record with it**. The row is written and then discarded.

The consequence is precise: **AC-69 holds in the domain and does not hold in production.** A caller that lets the exception propagate — which is the natural and correct thing for a caller to do — loses exactly the rows the ungrounded rate is computed from, so that rate would read 0% forever. It is the same defect T119 fixed twice at a smaller scale (a lost vendor, a lost retry count), reappearing one layer out.

**Raised rather than worked around, then decided and implemented.** [ADR-0029](adr/0029-operational-history-durability.md) states the problem, evaluates four options, and was **ratified on Option A**: `SqlInferenceRecorder` owns a session factory and commits on its own transaction. Two of the four are *explicitly* rejected because they appear to solve the problem and do not — a savepoint is inside the transaction that rolls back, and an outbox insert is in it too.

**`ai_narration` keeps the caller's transaction**, and the asymmetry is the point: a narration nobody committed was never shown to anyone, while a model call that happened, happened. A Security Invariant asserts both halves, with a positive control on the narration side.

**A failed operational write is itself observable** — an ERROR line naming what was lost plus `signora.ai.recording_failures`, a module-owned counter. The recorder never fails its caller, because business success and operational persistence are deliberately decoupled; but a silent loss would make the ungrounded rate optimistic a second time by a second mechanism, so the swallow is loud. The integration test asserts today's behaviour explicitly, with the desired behaviour written into its failure message, so the day it is fixed the test is where it is noticed.

---

#### Known limitations of the shipped golden set

Recorded rather than smoothed over:

- **Two cases, one shape.** The M2.0 baseline scenario produces structurally identical opportunities for `northwind` and `contoso`, so the sample size is 2 and the *variety* is 1. Broadening it means more scenarios, which is M2.0's asset to grow — not something to fabricate here. **This is the main caveat on the passing run:** a clean sweep over two near-identical cases is real evidence and thin evidence at the same time, and the recorded `sample_size` of 2 is what lets a reader see that for themselves.
- **`opened_on` moves with the calendar.** It comes from `opportunity.created_at`, which the pipeline sets to wall-clock now, so re-seeding on a later day changes the fingerprint without any expectation having changed. The file is checked in and regenerated deliberately, so this surfaces as a reviewable diff rather than as drift — but it does mean "regenerate to confirm nothing changed" is not available. Fixing it belongs to M6's clock, not to the harness.

---

*T111–T121 built. Verified against a real model. One open finding: operational history does not survive a rolled-back unit of work.*

---

## M9.5 — the Prompt Rendering Protocol

> Added 2026-07-31 by [ADR-0031](adr/0031-evidence-citation-protocol.md), Step B. **Behaviour-neutral**: no prompt renders differently, no parser changed, no release moved.

### The fourth experimental condition

A prompt evaluation measures a system with **four** inputs. Until M9.5, three were bound to every measurement and one was not:

| Input | Bound by | Drift detected? |
|---|---|---|
| Prompt text | `PromptVersion.fingerprint`, verified on every load | yes — `PromptTamperedError` |
| Dataset | the dataset's own fingerprint | yes — refuses to load |
| Model | recorded on the evaluation, enforced by `require_model` | n/a — named explicitly |
| **Rendered evidence** | **nothing** | **no** |

The gap was not an oversight so much as a blind spot with a plausible cover story. `prompt_fingerprint` *looks* like it covers the prompt — but the template contains `{facts}`, not facts. `evidence_digest` *looks* like it covers the evidence — but it hashes `canonical_form()`, which `evidence.py` documents as *"for hashing only. Not for prompts."* Between them sits `render.py`, covered by neither.

> **Two inferences carrying an identical prompt fingerprint and an identical evidence digest could have been shown different text.** All that was required was for the renderer to change between them.

That is a hidden input, and hidden inputs are architecture defects (CLAUDE.md §2). It is also why ADR-0031's defect survived two milestones: nothing recorded the one thing that would have shown the renderer and the parser disagreeing.

### Where it lives, and why not beside the grammar

The citation *grammar* — `EvidenceRef.token` and `EvidenceRef.parse` — lives in `domain/evidence.py`, and those two have never drifted precisely because they are neighbours. ADR-0031 originally proposed putting the *display* form there too.

**That would have violated a rule `evidence.py` states about itself**: *"Evidence is truth; prompts are language, and the moment a fact knows how it will be phrased, changing the wording becomes a change to the evidence model."* A fact must not learn how it will be presented.

So the protocol is its own concept in `domain/rendering.py`, **depending on** the grammar without living inside it. Language that is a contract is domain language — the same reason `prompt.py` is domain rather than infrastructure. The ADR's intent was right and its address was wrong; the correction is recorded there.

### What the version identifies

A bare integer with no referent would be worse than nothing: nobody could say whether a given change required a bump, so bumping would become discipline — and discipline is exactly what failed. **The version identifies a specification**, stated in the module and pinned by a specimen in `tests/ai_platform/test_rendering_protocol.py`. Changing what a model sees without bumping the version fails that test, the same guarantee `PINNED_FINGERPRINTS` gives prompt text.

Protocol **1** is the form shipped since M8 — bracketed citation, indented attributes — specified as it *is* rather than as it should be, defect included. Naming a defect and correcting it are separate changes, so that the release invalidation in Step C has exactly one cause.

### `passed` and `earns_release` are different questions

`Evaluation.passed` is unchanged and stays a fact about the **past**: the run really did satisfy the criteria, under the conditions that existed. Folding the protocol check into it would retroactively describe a clean run as a failing one — which is not what happened, and would make the manifest lie about its own history.

The protocol check is a fact about the **present**, so it is separate:

- `passed` — the measurement satisfied the criteria.
- `measured_under_current_protocol` — those conditions are still in force.
- `earns_release` — both. Every release derivation reads this.

**A protocol change therefore withdraws every stale release by derivation, not by anyone remembering to withdraw them.** Prompt immutability and released history are untouched: the record stays, and stops applying.

The refusal says so in its own words, because the two failures have opposite remedies — told only *"has not passed for this model"*, an engineer re-authors a prompt that was already correct:

> `prompt reasoning@1 passed for this pairing under rendering protocol [1], but this process renders at protocol 2. That measurement is still true and is still on record; it no longer describes what the model would be shown. Re-evaluate under the current protocol — do not re-author the prompt.`

### Two decisions that are not obvious from the diff

**The duplicate-evaluation key includes the protocol.** Without it, re-evaluating a prompt on the same model and dataset the day a protocol changes is refused as a repeat — which is exactly the run a protocol change exists to require, rejected with a message about overwriting history. Both the loader's uniqueness rule and the recorder's key carry it, and each has a test that dies without it.

**The field has no default, anywhere.** A default on `Evaluation` would let a measurement whose conditions nobody recorded present itself as valid; a default in the manifest schema would silently promote every legacy entry into a valid release. The six existing entries were stamped `1` explicitly, because that is the protocol they were genuinely measured under — not because it was the convenient value.

### Deliberately not built

**The protocol version is not written to `ai_inference`.** Enforcement at the point of use already prevents a stale release from running, so a column here would be forensic rather than protective, and it is a migration nobody has needed yet. Recorded as a candidate, not built (CLAUDE.md §6 — no speculative generalisation).

### Verified

Nine mutations, all fatal — including the two that survived the first round: the recorder's duplicate key silently dropping the protocol, and the report stamping a literal `1` instead of reading the constant. The second is the more interesting: at protocol 1 the mutation produces an identical program, so it is invisible to any test that does not move the constant. It is killed by a test that raises the running protocol and asserts the stamp follows — which is the property that makes Step C's bump propagate on its own.

*1751 tests · 29 contracts · mypy strict clean over 448 files · coverage 95.85%.*

---

### Step C — the form moves, and three releases withdraw themselves

> 2026-07-31. **The first behaviour-changing step**, and the one the versioning existed for.

**Protocol 2 presents a citation as a complete, copyable unit:**

```
signal_contribution:3f40f486-98e5-5ff7-812d-feca5aa54af7 — A retired system suggests …
  contribution: 30
  relevance: primary
```

The string the model must produce is now a string it can *copy*. Under protocol 1 no form the parser accepted was ever visible as a delimited unit — the model had to **derive** one by removing characters, and every observed grounding failure across three prompts and four models was an error in how much to remove: too little (the bracket transcribed) or too much (the kind prefix stripped). A form requiring no transformation has no mechanism for either.

**The em dash is load-bearing, and a hyphen would not have done.** A UUID contains hyphens, so `-` sits inside the token's own alphabet and a model deciding where a citation ends would have to reason about position rather than about characters. An em dash appears nowhere in `kind:uuid`, so the boundary is unambiguous by construction. Asserted, because the reason is not visible from the character.

#### What withdrew, and what did not move

One constant changed from `1` to `2`. As a consequence, **by derivation and with nothing edited by hand**:

| Prompt | Passed on | Status now |
|---|---|---|
| `explanation_narration@1` | `llama3.1:8b` | awaiting re-evaluation |
| `reasoning@1` | `granite3.3:2b` | awaiting re-evaluation |
| `research_planning@1` | `llama3.1:8b` | awaiting re-evaluation |

**No manifest entry was removed, no release was withdrawn by hand, no migration ran, and no prompt was touched.** Every measurement still says it passed, still names protocol 1, and is still on record. `passed` is unchanged; only `earns_release` moved — which is the whole demonstration that release validity is derived rather than declared.

Three tests that asserted those releases now assert the withdrawal. `test_the_narration_prompt_awaits_re_evaluation_under_protocol_2` has now been rewritten twice — it first asserted the prompt was *unusable* (true before T120), then that it held a release (true under protocol 1), and now that it awaits re-measurement. **The sequence is the record, and the rule behaved identically all three times.**

#### Ownership, enforced rather than described

`application/render.py` is now four statements: check the placeholder, substitute `render_facts`. It cannot reach inside a fact — a Security Invariant reads its **syntax tree** and refuses any reference to `token`, `ref`, `summary`, `attributes` or `EvidenceFact`. A renderer that cannot see a fact cannot format one.

Two further invariants make the specific defect unrepresentable rather than merely superseded: no file under `modules/` may wrap a citation token in a delimiter, and only `domain/rendering.py` may declare a protocol version. The round trip is asserted over the **rendered bytes** — the assertion whose absence let the writer and the reader drift apart for two milestones.

**The parser was not touched, and tests assert it still refuses everything it always refused**: a bracketed citation, a bare UUID, and a token with attributes appended. The fix is entirely on the producing side; a parser that repaired its input would make the failure rate unmeasurable.

#### One coupling, found where the plan predicted it

M10's scripted adapter read citations by stripping brackets off each line — the only place in the suite coupled to the form, and precisely why a renderer change had to be a version bump rather than an edit. Its replacement takes the first token of each line and keeps the ones that **parse**, which is how protocol 2 intends a model to succeed. A first attempt matched on the delimiter instead and picked up prose from the planning prompt's own derivation catalog: *a delimiter is a weaker signal than parseability.*

M8's pipeline test now supplies a registry double stamped at the running protocol — the same distinction M10 already draws: **a double for the registry, never for the release rule.** The shipped manifests are untouched, and `test_prompts.py` asserts what they actually hold.

*Seven mutations, all fatal — including reverting the version, re-decorating the citation, swapping the em dash for a hyphen, and re-authoring the fact line inside `render.py`.*

*1757 tests · 321 invariants · 29 contracts · mypy strict clean · coverage 95.9%.*

---

### Step D — the workaround is deleted, and the refused prompt earns a release

> 2026-07-31. Prompt authoring only. No platform behaviour, no parser change, no rendering change.

`research_planning@2` and `research_synthesis@2` are new artifacts — `@1` is immutable and untouched, and the fingerprints differ, because content identity outranks version identity.

**What was removed.** Both `@1` prompts told the model to perform surgery on what it saw:

> *"Cite the exact reference, **without the square brackets**. The facts are shown as `[business_event:2f7c9a10-...]`; write `business_event:2f7c9a10-...`."*

Both `@2` prompts ask only that it be copied:

> *"**Cite the reference exactly as shown.** Copy it character for character — do not add anything, and do not remove anything."*

#### The result

| Prompt | Protocol | Grounding failures | Outcome |
|---|---|---|---|
| `research_planning@1` | 1 | 0 | earned, then withdrawn by Step C |
| `research_synthesis@1` | 1 | **1**, four consecutive runs | **REFUSED** |
| `research_planning@2` | 2 | 0 | **EARNED** |
| `research_synthesis@2` | 2 | **0** | **EARNED** |

**`research_synthesis@2` is ADR-0031's central prediction, confirmed by measurement.** The same model, the same dataset, the same rubric, the same schema, the same criteria — and the prompt that failed four times in a row now passes. The only things that changed are what the model was shown and an instruction to stop editing it.

Three consecutive clean runs of each, mirroring the three consecutive identical refusals in the other direction. Coverage 1.00 on both cases of both prompts.

**Only the recorded run is in the manifest.** The two stability runs were executed without `--record`, because `record()` refuses a duplicate `(model, dataset, dataset_version, protocol, date)` — correctly, since evaluations accumulate and overwriting one is how an inconvenient result stops existing. The repetitions are reported here as an observation, not promoted into evidence they are not.

#### Two things Step D had to change beyond the prompts

**M10's request path now names `@2`** (`plan.py`, `research.py`). A prompt nothing requests is a dead artifact, and leaving the pipeline pointed at `@1` would have left it permanently refused.

**One test's premise was removed by its own milestone.** `test_an_unreleased_synthesis_prompt_stores_nothing` proved that a run failing *after* deriving findings stores nothing — and it borrowed its failure from the shipped manifest, where `research_synthesis@1` genuinely had no release. Step D earned one. The arrangement is now constructed explicitly, with planning released and synthesis withheld, because **a guarantee that depends on a real prompt staying broken expires the moment the prompt is fixed.**

#### The success criterion, asserted rather than described

`test_no_prompt_the_pipeline_uses_instructs_a_transformation` reads the shipped `@2` files and refuses any prompt containing *"without the brackets"*, *"square bracket"*, *"strip"* or *"remove the"*. A future author reintroducing the workaround fails a test rather than rediscovering the defect.

*1763 tests · 321 invariants · 29 contracts · mypy strict clean · coverage 95.85% · smoke green.*

---

## TASK-415 — the deterministic provider, and the assumption it removed

**Delivered 2026-08-05 by Lane B**, `ai_platform`'s current assignee. The task was approved by the product owner on 2026-08-04 and its package was authored by this lane and reviewed by Product Office, which is the first end-to-end run of the [D-060](../DECISION_REGISTER.md) loop.

### What was actually wrong, and it was not a missing file

The objective — *a developer clones the repository and exercises every AI path without downloading a model* — reads like it needs a new adapter beside the two that exist. **It did not.** `build_provider_registry` registered `OllamaAdapter` **unconditionally**, while Anthropic sat behind `if settings.anthropic_api_key`. So the defect was an existing code path assuming a 4.7GB local runtime, and `CLAUDE.md` §10 names the target directly: *"No implementation may assume Ollama is installed unless a developer explicitly selects it."*

**Adding an adapter without changing that registration would not have worked at all.** `AIProviderRegistry.register` refuses two adapters claiming one model — deliberately, because *"routing would depend on registration order"* — and both the mock and Ollama serve the configured development model. The conditional is therefore a **precondition**, not a preference, and the failure would have been at composition rather than at call time.

### `AIVendor.MOCK`, and why the cheap answer was refused

The mock needs a vendor label: `AIProviderDescriptor` declares one and `InferenceResult` carries it onto every `ai_inference` row. **Reusing `OLLAMA` was available and is wrong** — it would make the operational record assert a runtime that never started, which is §10's *"an incorrect attribution is worse than none, because it misdirects the investigation."*

**The enum's own docstring forbids speculative members**, and Product Office ruled this one is not speculative: §10 ratifies the deterministic mock as one of three execution modes and ADR-0028 as amended names it a first-class development provider. **The member records a decision already taken.** The review attached one condition — *confirm nothing branches on `InferenceResult.vendor`* — and it holds: there is no `if vendor == …` anywhere outside an adapter, and the only branches on the field test it for `None`, which asks *did anything serve this*, a different question.

### The guard, and where its input comes from

**The mock must never be registered outside a local environment**, because a service answering from a deterministic stub is indistinguishable from one that is working — strictly worse than the outage it hides.

The environment is a field on **`AISettings`**, reading `SIGNORA_ENVIRONMENT` — the same variable `signora_platform.Settings` reads, because both objects carry the `SIGNORA_` prefix and this is one process's environment with several owners.

| Rejected | Why |
|---|---|
| Read `signora_platform.Settings` | A module reading another module's configuration (§6), and reaching into a frozen substrate to do it (§20a) |
| Take it as a parameter | A caller can forget a parameter, and **the one thing this guard may never do is fail open** |

**Neither object stores the other's value**; both read one source, which is what keeps this outside §2's duplicated-truth rule. It also stays testable — a test constructs `AISettings(environment="production")` and the guard fires without a global being mutated, which is what stops it becoming a guard that cannot fail.

### Two deviations from the approved package, both stated rather than absorbed

**The sixth knob is derived, not settable.** The row lists *timeout* beside *latency*. They are one fact: a mock scripted to take 5s and time out at 30s would raise a timeout while reporting that it did not. So `latency_ms` decides both — it is what the result reports, and the call raises `AITransientError` when it exceeds the request's own `timeout_seconds`. That is also what a real adapter does, since the budget lives on `InferenceRequest` and an adapter carrying its own would be the duplicated default §2 names.

**`tests/ai_platform/fakes.py::FakeAdapter` was not replaced**, though the package proposed promoting it. Inspecting its 35 call sites changed the conclusion: `FakeAdapter` sets `vendor` freely so tests can assert provenance **across** vendors, while `MockAdapter` fixes it to `MOCK`. They are a scripted stand-in for *any* vendor and *the mock vendor* respectively — different things, not two copies of one, so folding them would have lost coverage rather than removing duplication.

### What a lane arriving cold needs to know

**Development is deterministic by default.** `SIGNORA_DEVELOPMENT_PROVIDER` selects `mock` (the default) or `ollama`; exactly one is registered for the development model, never both. A hosted credential still registers Anthropic alongside either. **Nothing above the port can tell which answered**, which is the property that makes the deterministic path worth having — a mode that skipped the port would prove the mock works and say nothing about the product.

*27 new tests in `tests/ai_platform/test_mock_adapter.py`.*

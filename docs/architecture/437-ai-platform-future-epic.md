# 437 · The AI Platform as a future epic — assessment and decomposition

**Lane C · Product Office · 2026-08-05.** Product Office directive: *"Do not implement anything. Do not assign implementation work yet. This is backlog preparation only."*

> ## The finding, before the decomposition
>
> **The AI Gateway this directive describes already exists, is ratified, and is 75% built.** `modules/ai_platform` is **41 files** across domain, application, evaluation, infrastructure, interface and public. **[ADR-0012](adr/0012-ai-platform-architecture.md)** is titled *"Provider Abstraction, Multi-Vendor Models, **Embeddings**, Prompt Registry"* and is `Accepted`.
>
> **And four of the twenty requested areas do not extend that architecture — they reverse it.** Not by oversight: the properties they would remove are the ones three other guarantees rest on.

**So this document does not propose an AI Platform.** It reports what is built, names what is genuinely absent, **and separates the additions from the reversals** — because those are different kinds of decision and only one of them is a backlog item.

---

# 1 · The directive's requirements, measured against what ships

## ✅ Already built and ratified — no work required

| Requirement | Where it lives |
|---|---|
| **No business module talks to a vendor** | `domain/provider.py` — the AI Provider Port. **This is the anti-corruption layer the directive asks for**, and it is four milestones old |
| **Vendor identity never drives behaviour** | *"`AIVendor` … is recorded and never consulted — no business behaviour may differ because Ollama rather than Claude served a call."* **Structural, not aspirational** — §10, [ADR-0028](adr/0028-model-runtime-by-environment.md) |
| **Capability registration, not type checks** | `AIProviderDescriptor` — *"**Capabilities first, identity last.** A future vendor integrates by describing what it supports, never by requiring conditional logic elsewhere — which is the difference between an abstraction and a dispatch table with extra steps"* |
| **Prompt registry, versioning, lifecycle, approval, rollback** | `domain/prompt.py`, `infrastructure/prompt_loader.py`, and the **release rule**: a prompt may only be used with a model it was evaluated against |
| **Evaluation** — datasets, scoring, regression, reproducibility | `evaluation/` — 7 modules: `dataset` · `harness` · `release` · `report` · `rubric` · `run_log` |
| **Observability** — latency, tokens, retries, failures | `domain/usage.py`, `infrastructure/metrics.py`, `ai_inference` records |
| **Cost tracking** | `domain/usage.py`, and its refusal is correct: *"**Deliberately no money anywhere in this file.** A price is a contract term… A dollar figure written onto an inference record would be correct for about a week."* **Pricing is applied outside the port at reporting time, so a price change re-prices history** |
| **Execution modes** — production · evaluation · mock | §10, [ADR-0028](adr/0028-model-runtime-by-environment.md), and **TASK-415/416 shipped today** |
| **Embeddings** | Ratified in ADR-0012 |
| **Failure taxonomy, retries** | `domain/errors.py` — *"a port that returns data on success and raises whatever the vendor SDK raised has not abstracted the vendor at all"* |

> **Ten of the twenty areas are done.** Proposing them as new work would be the duplicate abstraction the directive explicitly forbids.

## 🟨 Genuinely absent — and these are the epic

| Requirement | State | Note |
|---|---|---|
| **Bedrock · Azure OpenAI adapters** | **0 files** | ⚠️ **Deliberately absent, not missing** — see §2.4 |
| **OpenAI · Gemini adapters** | **Ratified in ADR-0012, no adapter** | *"gain adapters when a real caller needs them"* — the rule is already written |
| **Prompt injection / jailbreak defence** | **0 files** | **The largest true gap** |
| **PII masking before egress** | **0 in `ai_platform`** | 6 files elsewhere; nothing on the AI path |
| **Multi-tenant AI policy** — allowed providers, budgets, rate limits | **0** | Needs a bounded context; see §3 |
| **Tool calling · MCP** | **0** | Refused once already ([431](431-ai-execution-modes.md)) |
| **RAG** — vector storage, chunking, citation | **1 file mentions vectors** | Citation exists via grounding; retrieval does not |
| **Customer-provided API keys** | **0** | Credential custody — a security decision before an engineering one |

---

# 2 · The four reversals — decisions, not backlog items

**Each of these is forbidden by a ratified principle whose removal costs more than the feature.** **Naming them as tasks would smuggle an architectural reversal in as an increment.**

## 2.1 Memory ❌ conflicts with Statelessness

**Ratified 2026-07-29** ([28 §Statelessness](28-ai-platform.md)):

> *"Grounding says what the model may refer to. **Statelessness says what the platform may remember: nothing.**"*
> *"`application/infer.py` — no memoisation of responses, no accumulated context, no 'last evidence set', **no conversation buffer**."*

**Why it cannot be added alone:** *"A grounded response is only checkable against a **known** evidence set — if the platform silently carried facts forward, the set the validator checks against would not be the set the model saw. **Statelessness is what makes grounding verifiable at all.**"*

**Three guarantees fall with it:** grounding verifiability · **reproducibility** (*"the inputs to any recorded inference are exactly reconstructable… that claim is only true because of this principle"*) · **Business Capability Verification** (*"a scenario could pass because an earlier scenario warmed something, and fail when run alone or reordered"*).

## 2.2 Caching ❌ conflicts with Statelessness, and with tenancy

> *"Provider adapters — **never** a vendor conversation handle, a thread id, a server-side session, or **a response cache**."*
> *"A workspace's evidence never outlives its invocation… **which is also the cleanest possible answer to cross-tenant leakage through a cache: there is no cache to leak from.**"*

**A semantic cache is the one shape where a near-match across two workspaces is a data breach rather than a bug.** ⚠️ **This is the reversal I would counsel hardest against.**

## 2.3 Adaptive model routing ❌ conflicts with the registry contract

> *"The provider registry — populated once at the composition root from configuration, then read-only. **No per-workspace state, no usage accumulators, no adaptive routing that learns from previous calls. Routing is configuration, per [ADR-0012](adr/0012-ai-platform-architecture.md).**"*

**Routing by task type, quality tier or workspace policy is compatible** — it is configuration. **Routing that learns from latency or cost observed at runtime is not.** The directive lists both under one heading; **they are opposite decisions.**

## 2.4 Bedrock and Azure OpenAI in the enum ❌ conflicts with the no-speculative-ports ruling

> `AIVendor`: *"Azure OpenAI and Bedrock are **reserved** rather than recognised, and are deliberately absent: **a member here with no ratified status is a speculative extension point, and the roadmap's no-speculative-ports ruling applies to enums too.**"*

**Adding them before a customer needs one reverses a standing ruling.** **The mechanism to add them already exists** — ratify the vendor, then build the adapter when a real caller appears. **OpenAI and Gemini are already through that gate and waiting.**

> ### What I recommend
>
> **Take the three additive reversals as one product decision, not four tasks.** **Memory, caching and adaptive routing are one question**: *may the AI Platform hold state?* **Answer it once.** If the answer is yes, grounding, reproducibility and scenario independence each need a replacement guarantee **designed before anything is built** — that is an ADR, and a large one.
>
> **My recommendation is no, and to solve the underlying needs differently:** conversation continuity as **an explicit evidence set the caller assembles** (stateless, groundable, tenant-safe) · cost control by **budget and model tier**, not by a learning router · **no response cache at all**, and prompt-level caching only if a vendor offers it inside a single request.

---

# 3 · The decomposition — one epic, five slices, no lane

## **Epic H · AI Platform — providers, policy and safety**

> **The name matters and I am proposing against the directive's suggestion.** *"AI Platform"* and *"AI Gateway"* both name **a module that already exists**, and an epic sharing its name would read as *build the thing* rather than *extend it*. **The epic is what it adds.**

| | Slice | Depends on | Notes |
|---|---|---|---|
| **H1** | **A second hosted vendor reaches production** — the OpenAI adapter | nothing | **The port already supports it.** H1 exists to prove that by adding a vendor **with no change above the port** — the claim ADR-0012 makes and nothing has tested |
| **H2** | **PII never leaves the tenant unmasked** | H1 | **The largest true gap.** A masking pass at the port boundary, and a Security Invariant that fails if an unmasked field crosses it |
| **H3** | **A workspace states which providers it allows** | H2 | ⚠️ **Needs a bounded context decision** — is this `workspace_tenancy`, `ai_platform`, or new? **Routing by policy is configuration and stays inside the ratified contract** |
| **H4** | **Prompt injection is detected and recorded** | H2 | Detection and audit **before** blocking — *"record what happened; compute judgements where the inputs are known"* |
| **H5** | **A workspace has an AI budget** | H3 | **Builds on `domain/usage.py` and [TASK-411](../BACKLOG.md)**, which is already `SEQUENCED`. **Not a new metering system** |

**Deferred out of the epic, deliberately:** RAG · tool calling / MCP · agent workflows · Bedrock/Azure · customer-supplied keys. **Each needs a decision first** — a bounded context, a reversal, or a customer.

## ADRs this epic would need

| | |
|---|---|
| **ADR-A** | **May the AI Platform hold state?** — the §2 question. **Blocks memory, caching and adaptive routing, and nothing else** |
| **ADR-B** | **Where does AI policy live?** — the H3 bounded context |
| **ADR-C** | **PII at the port boundary** — what is masked, by whom, and how the invariant proves it |

---

# 4 · Other foundational gaps, measured

| Capability | State | Recommendation |
|---|---|---|
| **Billing / usage accounting** | **Already in the backlog** — [TASK-411](../BACKLOG.md) and [TASK-412](../BACKLOG.md), both `SEQUENCED` with triggers | **Nothing to add.** The trigger is *the Billing screen is scheduled* |
| **Workflow orchestration** | **47 docs, 37 code files** — the outbox, the relay, the dispatcher, worker pools | **Exists.** Not an AI concern |
| **Feature flags** | 7 docs, **1 code file** | **A genuine gap, and small.** Propose only when a slice needs one — **a flag framework with no flag is the speculative-port shape** |
| **Tenant administration console** | **0 and 0** | **A genuine gap.** Support cannot see a workspace's state without database access today |
| **Plugin framework** | 3 docs, **0 code** | ⛔ **Do not propose.** No customer, no extension point, and §20a exists to prevent exactly this |
| **Webhooks (outbound)** | 11 docs, **0 code** | **A real integration gap**, and the outbox already provides the delivery semantics |
| **Notifications / email** | 25 docs, 5 code | ⚠️ **Already load-bearing**: [TASK-904](../BACKLOG.md) ships invitations as **a shareable link, not email**, precisely because no transactional-email dependency exists |

---

# 5 · What this document does *not* do

**Per the directive, and verifiable:**

| | |
|---|---|
| **No lane queue changed** | Epic H appears in **no** `docs/coordination/queues/*.toml` |
| **No task is assigned** | Every row below is `SEQUENCED` with a trigger, not `READY` |
| **No current priority moved** | Lane A stays on **TASK-417 · Account 360**; Lane B on **TASK-416** and its six |
| **No module ownership changed** | `ai_platform` remains `review-at-first-implementation`, future owner **undecided** — and **this epic is not that first implementation** |
| **No ADR was written** | Three are *proposed*. Writing one before the epic is scheduled would be the anticipation the governance freeze forbids |
| **Repository policy** | No new dependency · no second datastore · no CI · **no `signora_platform/` change** · nothing in `backend/modules/` touched by this office |
| **No regression** | **Nothing executable changed.** This document and backlog rows only — `mypy`, the suites and every gate are untouched by construction |

> **The trigger for Epic H, stated once so it is checkable:** **the approved UI waves are complete and `product_surface` is no longer the lowest-implementation module.** It is **45%** today and every other module is 50% or above.

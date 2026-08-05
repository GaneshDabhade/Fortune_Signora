# 431 — AI Execution Modes and the deterministic mock provider: assessment

> **Lane C — Product Office, 2026-08-04.** **PREPARED — READY FOR PRODUCT OWNER.** Prepared on the directive: *"Please assess introducing a deterministic mock AI provider… Determine whether any [AI packages] currently assume a mandatory local Ollama dependency… Do not introduce unnecessary work. Reuse existing provider abstractions wherever possible. Raise new backlog items only where genuinely required."*
>
> **The direction is accepted. The premise is half true, and the half that is false matters, because it changes how much work this is.**

## 1 · The premise, measured

**The directive observes that *"current development and evaluation appear to assume a locally running Ollama model as the primary execution target."* That is one claim about two different things, and the repository answers them differently.**

| | Claim | Measured | |
|---|---|---|---|
| **Tests** | Development *tests* assume a local model | **False.** `backend/tests/ai_platform/contract/test_adapters.py` builds `OllamaAdapter` over **`httpx.MockTransport`** — the contract suite never reaches a network. The Security Invariants state it as a rule: *"they never call a model. **A guarantee that needs a GPU to verify is not a guarantee**"* | ✅ already right |
| **The running application** | Development *of the app* assumes a local model | **True.** `build_provider_registry` registers **exactly two adapters — Anthropic and Ollama.** There is no third. **A developer running the stack and exercising any AI path needs Ollama on localhost:11434** | ⚠️ **the real gap** |
| **Evaluation** | Evaluation forces a provider | **Mostly false.** The harness *"knows no vendor… it names a model; who serves it is the registry's business"*, and `__main__.py` accepts `--model`. **What is Ollama-shaped is the default**: `model = args.model or settings.ollama_model` | ⚠️ **a default, not a constraint** |

> **So the repository already separates functional correctness from model quality — the directive's central principle is ratified and enforced.** `CLAUDE.md` §10: *"Scripted fakes and real models solve different problems, and the separation is permanent."* **[ADR-0028](adr/0028-model-runtime-by-environment.md) already concluded it in the sentence the directive would have written**: *"Ollama is documented as a development prerequisite; **the deterministic gates never require it**."*

**What ADR-0028 did not do is give the *application* a deterministic provider.** It evaluated *"a scripted fake adapter instead of a real local model"* and answered **"Both exist, for different jobs"** — then put the fake in `backend/tests/`, where the running application cannot reach it.

> **That is the whole of the gap, stated precisely: the fake is a test double, not a provider.** **`make up` still needs Ollama; `make test` never did.**

## 2 · Reuse audit — what exists before anything is built

**[`ENGINEERING_LAWS.md`](../ENGINEERING_LAWS.md) L-1. The directive asks for eleven capabilities; the repository already has the boundary and some of the machinery.**

| Directive asks for | Exists today | Verdict |
|---|---|---|
| **predictable responses** | `FakeAdapter.content` | ✅ **exists** |
| **configurable failures** | `FakeAdapter.error`, and the full taxonomy — `AITransientError` · `AIRateLimitedError` · `AIPermanentError` · `AIOutputUnusableError` | ✅ **exists** |
| **structured output** | `FakeAdapter.supports_structured_output` | ✅ **exists** |
| **malformed output** | Set `content` to unparseable text; `AIOutputUnusableError` already models the outcome | ✅ **exists** |
| **configurable token usage** | ❌ **Hardcoded** — `InferenceUsage(input_tokens=10, output_tokens=5, latency_ms=42)` | ⚠️ **gap, small** |
| **configurable latency** | ❌ Absent | ⚠️ **gap, small** |
| **timeout simulation** | ❌ Absent. `InferencePolicy.timeout_seconds` exists and **nothing can exercise it deterministically** | ⚠️ **gap, and see §5** |
| **retry scenarios** | Partly — `InferenceUsage.retries` is recorded and the port says adapters *"must not retry a permanent failure"*; **nothing tests that against a controllable adapter** | ⚠️ **gap** |
| **streaming simulation** | ❌ **The port has no streaming** | ⛔ **do not build — §3** |
| **tool call simulation** | ❌ **The port has no tool use** | ⛔ **do not build — §3** |
| **it becomes the default development provider** | ❌ Not registered anywhere outside tests | ⚠️ **the gap that matters** |

**And the pattern is already proven one boundary over.** `signora_platform/simulation/` — `faults.py`, `clock.py`, `scenario.py`, `delivery.py` — does exactly this for the **data provider** boundary, and its header is the argument for doing it at the AI boundary too:

> *"A real provider cannot be asked to time out on demand, return a truncated body, or deliver the same record three times. **Without injection, the retry logic, the backoff, the dead-lettering, and the idempotency ledger are all code that has never been exercised by the thing it exists to handle.**"*

**Substitute *model* for *provider* and every word still holds.** **The AI boundary is the one abstraction layer in this repository with no simulator behind it.**

## 3 · Two capabilities to refuse, and refusing them is the recommendation

> ⛔ **Streaming simulation and tool-call simulation should not be built.**

**The port refuses both today, deliberately and in writing:**

> *"Deliberately narrow: one describe, one complete. **Tool use, streaming, embeddings and vision are absent because no caller needs them** — a wider port would force every future vendor to implement methods most of them do not have, and the usual outcome is adapters raising `NotImplementedError`, **which is a contract that lies.**"*

**A mock that simulated streaming would be simulating a capability nothing in Signora can consume.** That is `CLAUDE.md` §6 exactly — *"do not add abstractions, configuration flags, or generalization for hypothetical future needs"* — and §20's *speculative abstraction*.

> **The right sequencing is stated rather than the capability dropped: when a caller needs streaming, the *port* gains it, both real adapters gain it, and the mock gains it in the same change.** **The mock must never lead the port** — a simulator ahead of the thing it simulates is the one that teaches people the wrong contract.

**Nine of the eleven capabilities are in scope. Two are deferred with their trigger named.**

## 4 · The three modes, and what naming them actually costs

**The directive's three modes are the right frame, and two of the three already exist unnamed.**

| Mode | Today | Change required |
|---|---|---|
| **Development** | **Tests: already deterministic.** **The app: requires Ollama** | **Register a mock adapter and make it the default.** The real change |
| **Evaluation** | Harness is vendor-neutral; `--model` selects | **Change the *default*** so evaluation states its provider rather than inheriting Ollama's |
| **Production** | Anthropic adapter, registered only when credentials exist; **no fallback, by design** | **None.** ADR-0028's no-fallback rule already forbids exactly what a mock could break |

> ⚠️ **The one thing a mode selector must not do is become a fallback.** `build_provider_registry`'s own comment: *"a deployed service that could quietly reach a local runtime when its vendor was unreachable would serve customers **from a model nothing evaluated**."* **A mock provider makes that failure worse, not better** — a production service silently answering from a deterministic stub would be indistinguishable from one that worked.
>
> **So the mock is registered only when explicitly configured, never as a default in a deployed service, and a Security Invariant must assert it.** That test is not optional scope; it is the thing that makes this safe.

## 5 · The backlog review, and the finding worth the whole document

**Which AI packages assume a mandatory local Ollama? One, and it is blocking an epic.**

| Item | Assumes Ollama? | |
|---|---|---|
| **[TASK-202](../BACKLOG.md) · Epic G — Copilot** | **Yes, through [C-222](../LANE_COORDINATION.md)** | see below |
| **[TASK-013](../BACKLOG.md)** — *`reasoning@1` has no released model* | **Yes, same root** | |
| Every other AI test and package | **No** — `MockTransport`, fixtures, or no model at all | ✅ |

### C-222, re-read under this policy

**The measurement, unchanged:** `reasoning@1` on **`llama3.1:8b`** under rendering protocol 2 scores **0 grounding failures, 0 schema failures, coverage 0.667 — `EARNED`.** It took **~86 s per case**. `InferencePolicy.timeout_seconds` is **60**. Under the committed policy the identical pairing reports **UNMEASURABLE**.

**The lane refused to change the timeout, and was right to** — TASK-013 forbids it in writing, and *"an argument is exactly what that prohibition exists to refuse from a lane."*

> **But the directive reframes the question, and the reframing dissolves the blocker.**
>
> **C-222 is not a fact about `reasoning@1`. It is a fact about `llama3.1:8b` on this workstation.** The prompt passes protocol 2 on quality; **it fails only on wall-clock, against a local runtime the product will never use.**
>
> **Under Evaluation Mode with a configurable provider, `reasoning@1` can be evaluated against a hosted model — the Anthropic adapter already exists and is already registered when credentials are present.** **No timeout is tuned, no prompt is re-authored, no rule is bent.** The pairing changes, and **a pairing is what an evaluation record names.**

**Why this is the product owner's to rule and not Lane C's to do.** `CLAUDE.md` §10: *"the pinned evaluation model is part of the benchmark… changing the model is an architectural decision that belongs to the product owner, never to a coding session working around slow hardware."* **This directive is the product owner making exactly that decision at policy level** — but **C-222 should be closed by an explicit ruling naming the evaluation provider**, not by inference from a policy document.

## 6 · What to build, and it is two items

**Deliberately minimal, per *"do not introduce unnecessary work."***

| | Item | Scope | Size |
|---|---|---|---|
| **TASK-415** | **A deterministic mock AI adapter, registered and default in development** | `modules/ai_platform/infrastructure/adapters/mock.py` implementing the **existing** `AIProviderAdapter` port — no port change. Configurable **content · failure · latency · token usage · timeout · retry count**. Registered by `build_provider_registry` **only when explicitly configured**. **A Security Invariant asserting it is never registered in a production configuration.** Promote `tests/ai_platform/fakes.py`'s behaviour rather than re-writing it | **🟠 Amber** — a new adapter is an adapter registration, which ADR-0028 already classes as *"an adapter registration, never an edit here"* |
| **TASK-416** | **Evaluation states its provider** | The harness already accepts `--model`. Change the **default** so a run names its provider explicitly instead of inheriting `settings.ollama_model`, and **record the provider in the evaluation report** — which `report.py` currently and correctly refuses to do, because *"it names no vendor"*. ⚠️ **That refusal is deliberate and must be re-examined, not overridden**: provenance on the *run* is different from a vendor influencing a *score* | **🟢 Green**, and **it needs the §7 question answered first** |

**No new bounded context. No port change. No new dependency. No ADR strictly required for TASK-415** — ADR-0028 already governs adapter registration and vendor neutrality, and a mock adapter is an instance of both. **TASK-416 touches evaluation provenance and should carry an ADR amendment if the report starts naming a provider.**

## 7 · The one question this assessment cannot answer

> **`report.py` deliberately names no vendor**: *"nothing in evaluation may: the run asked for a model."* **Model-centric resolution is a ratified permanent principle** (§10) — *"business intent is 'execute against this model', never 'execute against this vendor'."*
>
> **Evaluation Mode asks a run to be reproducible, and reproducibility needs to know what served it.** **Those are not obviously compatible**, and resolving it by adding a vendor field would weaken a principle the repository states twice.
>
> **The likely answer is that the *model* is already the identifier and the vendor is genuinely irrelevant** — `claude-sonnet-4-5` names its server as precisely as `llama3.1:8b` does. **If that holds, TASK-416 is a default change and nothing more.** Stated rather than assumed, because it is the only place this directive could quietly weaken something.

## 8 · Recommendation

| | |
|---|---|
| **The three modes** | ✅ **Adopt as vocabulary.** Two of three already exist; **naming them makes the missing one visible** |
| **The mock provider** | ✅ **Build — TASK-415.** Nine capabilities, reusing the existing port and the existing failure taxonomy |
| **Streaming · tool calls** | ⛔ **Refuse for now.** The port has neither. **The mock must never lead the port** |
| **Evaluation default** | ✅ **TASK-416**, after §7 is answered |
| **C-222** | 🔴 **Close it with a ruling naming the evaluation provider.** It is a fact about a local model, not about the prompt — **and it has blocked Epic G's release path since 2026-08-04** |
| **ADR-0028** | **Amend, do not supersede.** Its reasoning is intact and its central sentence already says what this directive wants; **what it lacked was a provider for the application, not a decision** |

> **The honest summary: the repository is not Ollama-first, and it was designed not to be.** **Its tests never needed a model, its port never named a vendor, and its ADR said so.** **What it never built was the third adapter** — and the cost of that omission is one blocked epic and a clone nobody can run productively without downloading a model.

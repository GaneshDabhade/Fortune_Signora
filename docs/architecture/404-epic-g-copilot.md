# 404 — Epic G · Copilot — implementation preparation

> **Prepared by Lane C — Product Office. No code was written and none should be.** **Every claim verified against source on 2026-08-04**, including the release manifests.
>
> ⚠️ **Links to [51-implementation-specifications.md](51-implementation-specifications.md) do not resolve on this branch.** Everything relied on is quoted inline.
>
> **No ADR is prepared for Epic G, deliberately.** No boundary moves, no dependency is added, and the decisions it would need — [ADR-0028](adr/0028-model-runtime-by-environment.md), [ADR-0030](adr/0030-the-decision-package.md), [ADR-0031](adr/0031-evidence-citation-protocol.md), [ADR-0012](adr/0012-ai-platform-architecture.md) — **are all already ratified.** *An ADR is required when a boundary moves.*

---

## 1 · The finding: Epic G's blocker is not the one recorded

**[TASK-013](../BACKLOG.md) says:** *"`reasoning@1` has no released model — **the product owner.** The Decision Package would refuse at runtime."* **It is filed under WAITING, on a decision.**

**The manifests say something different.** `ai_reasoning_engine/prompts/manifest.json` records **four evaluations of `reasoning@1`, and every one of them has the same defect:**

| Model | **Dataset** | Protocol | Coverage | Grounding failures |
|---|---|---|---|---|
| `granite3.3:2b` | **`explanation_narration`** | 1 | 0.83 | 0 |
| `qwen2.5:3b` | **`explanation_narration`** | 1 | 0.33 | 1 |
| `llama3.2:3b` | **`explanation_narration`** | 1 | 0.33 | 1 |
| `granite3.3:2b` | **`explanation_narration`** | **2** | **0.00** | **2** |

> **`reasoning@1` has never been evaluated against a reasoning dataset.** Every recorded run borrows `explanation_narration`'s. **There is no `reasoning` dataset in the repository.**

**And the model choice is not what the siblings use.** Under protocol 2, three prompts hold passing releases — `explanation_narration@1`, `research_planning@2`, `research_synthesis@2` — **all on `llama3.1:8b`, all at coverage 1.0 with zero grounding failures.** The three models tried against `reasoning@1` are **2B and 3B**. **`llama3.1:8b` has never been run against it.**

> **So the missing thing is a dataset and an evaluation run — engineering work — not a product ruling.** It is possible `reasoning@1` fails on `llama3.1:8b` too and a genuine decision follows. **Nobody has measured it, and the backlog records a product-owner decision where a measurement is owed.**

**Recommendation: reclassify [TASK-013](../BACKLOG.md) from `WAITING` to `READY`**, scoped as *author a `reasoning` dataset and evaluate `reasoning@1` on `llama3.1:8b` under protocol 2*. **If it passes, Epic G's stated blocker disappears. If it fails, the product decision is then real and arrives with evidence.**

---

## 2 · The larger finding, which outranks Epic G

**No prompt in this repository has ever been evaluated against a production model.**

**Every evaluation in all three manifests** — nine of them — **is an Ollama model**: `llama3.1:8b`, `granite3.3:2b`, `qwen2.5:3b`, `llama3.2:3b`.

**[ADR-0028](adr/0028-model-runtime-by-environment.md) is unambiguous about what that means:**

> *"Model runtime is determined by environment… **Development: Ollama, running locally.** **Production: hosted commercial models** — ADR-0012's ratified vendors. **Every customer-facing inference.**"*

**And the release rule binds a prompt to the exact pairs it passed** — `Prompt.is_released_for(model)` and `require_model(model)` refuse anything else, by design.

> **Every AI capability in Signora is released for development and for nothing else.** Not a defect in any module — **each of them is behaving exactly as designed, and the design is what makes it visible.** But it means **the first customer-facing inference of any kind requires an evaluation nobody has run.**

**This is Epic G's real cost and it is not Epic G's fault.** G1 is the first feature whose *whole value* is customer-facing inference; narration and research can degrade gracefully, an assistant cannot. **Raised as [C-410](../LANE_COORDINATION.md)** because it affects M9/M10/M11 equally and should not be discovered inside Epic G.

---

## 3 · What already exists — and it is most of G1

| | Exists today | Evidence |
|---|---|---|
| **The module** | `ai_reasoning_engine` — application, domain, evaluation, infrastructure, public | 19 files |
| **The reasoning contract** | `domain/decision.py` · `package.py` · `support.py` · `context.py` · `temporal.py` | |
| **Grounded citation** | **`EvidenceRef.token` / `.parse`, one owned grammar with `domain/rendering.py` as its display form** | [ADR-0031](adr/0031-evidence-citation-protocol.md), **ACCEPTED**, implemented as M9.5 |
| **A validator that never repairs** | *"It validates; it never repairs… a validator that quietly fixed its input would make the failure rate unmeasurable"* | `grounding.py` |
| **The release mechanism** | `Prompt.is_released_for` · `require_model` · fingerprinted, append-only manifests | `ai_platform/domain/prompt.py` |
| **The evaluation harness** | `make eval` · `make eval-reasoning` · `ai_platform/evaluation/` | `Makefile` |
| **The explanation to ground in** | **The Contribution Ledger** — *"the authoritative explanation of a score"* | `buying_score_engine/domain/ledger.py` |
| **The prompt** | **`reasoning@1` is authored and fingerprinted** — it is unreleased, not unwritten | `manifest.json` |

> **G1 — *"ask about this account, explanation only, grounded in the contribution ledger"* — is a released prompt away from existing.** The module, the grammar, the validator, the ledger, the harness and the prompt are all built.

---

## 4 · Repository reuse — what must NOT be built

| ❌ Do not build | ✅ Exists as | Consequence |
|---|---|---|
| **A citation format, or tolerance for one** | **One owned grammar** — [ADR-0031](adr/0031-evidence-citation-protocol.md) A+D+E | **Two grammars again — the exact defect that ADR fixed**, and it cost three invalidated releases |
| **A prompt store, versioning or release gate** | Fingerprinted registries, `require_model` | A prompt usable where it was never measured |
| **A model adapter** | Ollama and Claude ship in M8; *"others arrive with real callers"* | Speculative ports, refused by the roadmap |
| **A new explanation of a score** | **The Contribution Ledger** | Two explanations that will disagree |
| **A reasoning engine** | `ai_reasoning_engine`, built | |
| **Retry or repair of a bad citation** | **Refusal is the design** | *"…would make the failure rate unmeasurable, which is the one number this platform most needs about itself"* |
| **An evaluation harness** | `make eval-reasoning` | |
| **A conclusion** | **G1 is *explanation only*** | §5 |

---

## 5 · The product boundary, and the one line that holds it

> **G1 explains what Signora already concluded. It concludes nothing itself.**

**Every claim in an answer must cite a reading that exists** — and the repository can enforce that, because refusal is already the behaviour when a citation does not resolve. **An assistant that reasons independently of the ledger would be a second intelligence pipeline whose disagreements with the first are invisible**, and the layering principle already forbids it one level down.

**G2 — *"draft an approach"* — is communication, never conclusion**, and its specification says it *"depends on G1 and C2 — a draft addressed to nobody is not useful."* **[Epic C](400-epic-c-people.md) §1 confirms C2 is real and prepared.**

**UX, in one paragraph, because it is not the hard part:** the answer appears where the question is asked — **on the account brief, beside the ledger it cites** — and every citation is a link to the reading. **An answer with an unresolvable citation is not shown at all**, which is the existing refusal made visible rather than a new behaviour.

---

## 6 · Phases

| # | Phase | Delivers | Effort | Depends on |
|---|---|---|---|---|
| **1** | **A `reasoning` dataset, and an evaluation** | **`reasoning@1` released, or a measured reason it cannot be** | **S** | Nothing — §1 |
| **2** | **A production-model evaluation** | The first prompt released for a hosted model | **M** | **API credentials** · [C-410](../LANE_COORDINATION.md) |
| **3** | **G1 — ask about this account** | Grounded explanation on the brief | **L** | Phase 1 · Product Surface for the render |
| **4** | **G2 — draft an approach** | An addressed draft | **L** | Phase 3 · **[Epic C](400-epic-c-people.md) C2** |

> **Phase 1 is small, blocked by nothing, and decides whether Epic G is blocked at all.** It should happen regardless of when Epic G is scheduled — **it converts a recorded product-owner decision into either a release or evidence.**

**Phase 2 is not Epic G's** — it belongs to whoever runs the first customer-facing inference, and Epic G merely arrives first.

---

## 7 · Risks

| Class | Risk | Mitigation |
|---|---|---|
| **Product** 🔴 | **An assistant that concludes rather than explains** | §5 — grounded in the ledger, refusal on unresolvable citation |
| **Operational** 🔴 | **Shipping on a model evaluated only locally** | §2 · [C-410](../LANE_COORDINATION.md). **`require_model` already refuses**; the risk is working around it |
| **Process** 🟠 | Tuning the prompt, delimiter, schema or timeout until it passes | **[TASK-013](../BACKLOG.md) already forbids this in writing.** Keep the prohibition visible |
| **Cost** 🟠 | Per-question hosted inference, unbounded | **Not modelled anywhere.** A product decision before phase 3, not after |
| **Architectural** 🟠 | Citation tolerance creeps back in | ADR-0031 cost three releases; **the parser stays strict** |
| **Product** 🟡 | An answer that cannot cite is shown anyway | Refuse. **An empty answer is honest** |

---

## 8 · Definition of done, and questions

**Done when a seller can ask *"why is this account being shown to me?"* and receive an answer in which every claim links to a reading that exists — or no answer at all.**

**Gates:** `reasoning@1` released for the model it runs on, **and for the environment it runs in** · every citation resolves, and refusal is exercised by test · **no second explanation of a score** · no tolerance in the parser · **the prompt, delimiter, schema and timeout are unchanged from the ones evaluated.**

### Questions

> **🟡 Upcoming — is a production-model evaluation scheduled before any customer-facing inference?** §2, [C-410](../LANE_COORDINATION.md). **Affects M9, M10 and M11 as much as Epic G.**

> **🟢 Background — what is the cost ceiling for a customer question?** Not modelled anywhere. **Needed before phase 3, not before phase 1.**

> **Not escalated, because a measurement answers it:** *does `reasoning@1` pass on `llama3.1:8b`?* — **run phase 1.** [TASK-013](../BACKLOG.md) records this as a product decision; **it is an unrun evaluation**, and Lane C recommends reclassifying it.

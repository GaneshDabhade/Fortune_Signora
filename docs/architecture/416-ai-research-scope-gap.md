# 416 — AI Research: the approved screen is not the built endpoint

> **Lane C — Product Office, 2026-08-04.** Prepared as the second half of wave 1. **It is not a package, because the work is not wave 1.** Verified against `origin/integration`.
>
> **Approved UI** — **AI Research**. This document states what the backend must provide for it, and why that is more than was assumed.

## 0 · The second correction to [412](412-backend-capability-matrix.md) in two days

**I placed AI Research in wave 1 on the grounds that `ai_research_engine` is *"built, with an interface layer."* It is. That was the wrong measurement.**

| | |
|---|---|
| **What is built** | `POST` / `GET` **`/workspaces/{id}/accounts/{account_id}/research`** — research about **one account** |
| **What the approved screen is** | *"Scope: EMEA · Enterprise · Q3 FY26 · **11 open renewals**"* → *"Three of eleven open EMEA enterprise renewals are slipping, and they share **one mechanism** rather than three separate problems"* |

> **The built endpoint researches an account. The approved screen researches a cohort and finds what its members have in common.** That is not the same capability with a different page around it — **it is a different question**, and the sentence that makes the screen worth having (*"one mechanism rather than three separate problems"*) is precisely the one a per-account endpoint cannot produce.

**Both corrections came from the same change of method.** [414](414-wave-1-account-360.md) §0 found the first by reading Account 360's sections instead of counting its endpoints. **This is the same mistake in the same week: an endpoint existing is not evidence that the screen it appears to serve can be built.**

## 1 · Where per-account research does ship

**Nothing is lost.** [414](414-wave-1-account-360.md) already delivers the built capability as **Account 360's Research section** — *company, strategic priorities, financial posture, relationship history* — which is exactly what `ResearchArtifactResponse` produces.

> **So the endpoint reaches a customer in wave 1. The screen does not.**

## 2 · What the contract already gives the approved screen

**The existing types are close, and were designed for this shape without knowing it.**

| Approved screen needs | `ai_research_engine` provides | |
|---|---|---|
| Cited sentences | `ResearchStatementResponse.text` + `cites` | 🟩 |
| Individually inspectable sources | `ResearchFindingResponse` — `ref`, `derivation`, `question`, `attributes`, `cites` | 🟩 |
| *"Steps are named before they run"* | `POST` returns **202**; `status` ∈ `REQUESTED`/`RUNNING`/`COMPLETED`/`NOTHING_TO_RESEARCH`/`FAILED` | 🟩 |
| *"Nothing is written to a record from research"* | **There is no write path. The module cannot violate this** | 🟩 |
| Provenance on the document | `prompt_name`, `prompt_version`, `model`, `evidence_digest` | 🟩 |

**`NOTHING_TO_RESEARCH` deserves naming.** Its docstring says *"a run that legitimately found nothing must not be reported as a failure — the product would be blaming itself for an account that simply has little evidence."* **The approved screen states the same principle as a product behaviour:** *"Rather than hedge, the research states the gap and names what would close it."*

**They agree, and neither was written from the other.** The gap is only that the approved version **names the remediation** — *"connect the churn history export, or widen the cohort to Nordic mid-market (adds 34 accounts, lowers precision)"* — where the built status says only that there was nothing.

## 3 · The backend gap

| | | |
|---|---|---|
| **Cohort-scoped research** | A request whose subject is *a set of accounts*, not one. **The scored comparison across members is the whole product value** | 🔴 **the substantive gap** |
| **Sections** | The screen renders *"4 of 5 sections"* and names them. `ResearchArtifactResponse.statements` is **flat** | 🟠 |
| **Editable statements, preserved through regeneration** | *"Edited sentences are preserved through regeneration and marked."* **There is no write path at all**, and the module's own guarantee is that there isn't one | 🔴 **and it needs care** |
| **Refusal that names its remedy** | `NOTHING_TO_RESEARCH` exists; **the remediation does not** | 🟠 |
| **Per-recipient citation permissions** | *"Excluded citations are shown as withheld rather than removed, so the argument stays auditable"* | 🟠 |
| **Research timeline** | *"Refusals are recorded in the research timeline, so a question is never silently dropped"* | 🟠 |

### The editable-statements gap is the one to think about before building

**`ai_research_engine` produces a materialized AI artifact, and `CLAUDE.md` §2 is explicit:**

> *"A persisted model output records what the platform actually produced at that moment… It is therefore **immutable**: prompt evolution or better evidence produces a **new** artifact, never an edit to an existing one, because editing one would destroy the only record of what a customer was actually shown."*

**The approved screen requires human edits to survive regeneration.** These are reconcilable and must not be reconciled by accident:

> **A human edit is not an edit to the artifact — it is a separate, attributed assertion that overlays it.** The screen already says so: *"the board sees **what a person asserted** versus what the model derived."* **Two authors, two records, one rendering.**

**That reading preserves the immutability rule exactly and delivers the approved behaviour.** It is recorded here so that whoever builds it does not reach for `UPDATE` on a materialized artifact — which the architecture would refuse anyway, having granted no `UPDATE` policy.

## 4 · Why the screen is not wave 1, and where it goes

**The screen inherits its scope from the shell** — *"Scope: EMEA · Enterprise · Q3 FY26"*, in the same shape the Copilot uses (*"I inherit the filters on screen"*).

> **So AI Research depends on the shell's global scope service, which is [O3](../DECISION_PACKS.md), which is wave 3.** And its substantive backend gap — cohort-scoped research — is independent of that and larger than the screen.

**Recommended placement: wave 3, beside the shell services**, with cohort research as its own preparation once O3 is ruled. **Not wave 1.**

## 5 · Wave 1, restated

> **Wave 1 is [Account 360](414-wave-1-account-360.md), and it is one screen.**

**That is a smaller wave 1 than [412](412-backend-capability-matrix.md) claimed, and it is the true one.** Eleven sections of existing intelligence become customer-visible, `ai_research_engine` reaches a customer through one of them, and **nothing in it waits on a ruling.**

**No other wave moves.** AI Research shifts from 1 to 3; waves 2 and 4–7 are unchanged.

## 6 · What this says about the method

**Two wave-1 items, two corrections, both found the same way — by reading the approved screen rather than the endpoint list.**

> **An endpoint's existence is evidence about the backend. It is not evidence about the screen.** [412](412-backend-capability-matrix.md)'s matrix was built from routers and events, which is the right unit for planning and the wrong unit for **placement**.

**The rule this produces, and it is cheap:** *before a screen enters a wave, read its sections against the contracts that would serve them.* **Both corrections cost a document each because they were caught before implementation. Either would have cost a slice if caught during it.**

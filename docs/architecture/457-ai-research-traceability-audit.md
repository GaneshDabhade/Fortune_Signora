# 457 · AI Research — screen-by-screen traceability audit

**Lane C · Product Office · 2026-08-05.** **Twelfth audit under [D-078](../DECISION_REGISTER.md).**
**Screen 13 of 16** — *"A workspace — answers become documents that keep their sources"* ([410](410-approved-ui-specification.md)). **Wave 3.**

---

# 0 · The finding: the repository has an explicit epistemology, and only this screen renders it

**`ai_research_engine` carries four types that exist nowhere else in the product:**

> **`Corroboration` · `Dissent` · `Recency` · `EpistemicOrigin`** — **and `Derivation` with its `DerivationType` and `DerivationDefinition`.**

**A finding does not merely cite a source. It records *how many sources agree*, *which disagree*, *how fresh the agreement is*, and *where the belief came from*.** ⚡ **That is [P-D Explainability](../DOMAIN_DISCOVERY_REGISTER.md) at its richest instance in the repository**, and **[449](449-account-360-traceability-audit.md) rated explainability a discharged differentiator on weaker evidence than this.**

| | |
|---|---|
| ✅ **Built** | `ResearchRequest` + its state machine · `ResearchPlan` · `PlannedStep` · `ResearchTask` · `ResearchFinding` · `ResearchSynthesis` · `SynthesisedResearch` · two events |
| 🔴 **Cohort research** | **[416](416-ai-research-scope-gap.md)**: *"The built endpoint researches an account. The approved screen researches a cohort and finds what its members have in common."* **Not the same capability** |
| 🔴 **Shell scope** | **[R-02](../DOMAIN_DISCOVERY_REGISTER.md)** — and 416 already placed this screen in wave 3 *because* of it |
| 🟡 **Recorded refusals** | *"AI Research **refuses** a question it cannot answer and records the refusal"* — **the refusal happens; the record is not surfaced** |

---

# 1 · ⚡ [P-A](../DOMAIN_DISCOVERY_REGISTER.md) reaches nine instances, and this one is a *product promise*

**410 states it as approved behaviour: *"AI Research refuses a question it cannot answer and records the refusal."*** **[445](445-ai-copilot-traceability-audit.md) found the same gap on Copilot.**

> **Two screens promise a recorded refusal and neither can show one.** **Stated absence now has nine instances, two of which are promises to a customer rather than internal discipline** — ⚡ **and that changes its classification: [P-A](../DOMAIN_DISCOVERY_REGISTER.md) is no longer only a pattern the repository keeps re-deriving. It is a capability two approved screens sell.**

---

# 2 · Findings

| | |
|---|---|
| **Existing and correctly modelled** | The request state machine · plan and steps · synthesis · **the epistemology — corroboration, dissent, recency, origin** · two events · `Resource.RESEARCH` separating reading from spending |
| **Extension candidates** | **A surfaced refusal record** — shared with Copilot |
| **Architectural evolution** | ⛔ **None.** **Cohort research is new scope, not an evolution** — 416 says so |
| **Missing foundational capabilities** | **[R-02](../DOMAIN_DISCOVERY_REGISTER.md)** *(already carried)* |
| **Missing workflows** | **Cohort research** — [416](416-ai-research-scope-gap.md), prepared and unscheduled |
| **Missing entities · events · permissions · projections · platform capabilities** | ⛔ **None** |
| **Vocabulary** | ✅ **`Research Session` is `ResearchRequest` + `ResearchRequestState`, already built** — the directive's candidate list named it and the repository already owns it |

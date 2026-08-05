# 459 · Reports — screen-by-screen traceability audit

**Lane C · Product Office · 2026-08-05.** **Fourteenth audit under [D-078](../DECISION_REGISTER.md).**
**Screen 15 of 16** — *"Built once, read three ways"* ([410](410-approved-ui-specification.md)). **Wave 7, and [411](411-ui-convergence-assessment.md) calls it *"the only screen with nothing to reuse."***

---

# 0 · The finding: *"nothing to reuse"* is right about capability and wrong about shape

**[411](411-ui-convergence-assessment.md) marked Reports 🔴 with an empty Reuses column, and at the capability level that is correct — no endpoint serves it.** **At the *concept* level, three of its four elements are already owned.**

| Element | 411 said | This audit finds |
|---|---|---|
| **Report definition · blocks** | 🔴 nothing | 🔴 **Confirmed.** **Genuinely new** |
| **"Built once, read three ways"** | 🔴 nothing | ⚡ **`MaterializedNarration`'s shape exactly** — *"a persisted model output records what the platform actually produced… **it is therefore immutable**"*. **A materialised report is the same category of artifact, and the rule that governs it is already ratified** |
| **"Views are shared by link and respect each viewer's permissions"** | 🔴 nothing | ⚡ **Two carried capabilities** — **[R-02](../DOMAIN_DISCOVERY_REGISTER.md)** *(this screen contributed the fourth property of its definition)* and **[R-13](../DOMAIN_DISCOVERY_REGISTER.md)'s field dimension** |
| **Narrative regeneration** | 🔴 nothing | ⚡ **`ai_platform`'s narration, with its ratified rule**: a change is **a new artifact naming the one it supersedes**, never an edit |

> ## **So Reports needs one new concept — `ReportDefinition` and its blocks — and inherits the other three.**
>
> ⛔ **And the constraint [442 §F7](442-product-led-domain-discovery.md) named still binds: *no second aggregation*.** **Every figure comes from surfaces delivered in waves 1–4**, which is why this screen is last **on evidence rather than on taste.**

---

# 1 · Findings

| | |
|---|---|
| **Existing and correctly modelled** | **The materialised-artifact pattern** · narration and its supersession rule · every underlying read |
| **Extension candidates** | ⛔ **None** |
| **Architectural evolution** | ⛔ **None** |
| **Missing foundational capabilities** | **[R-08](../DOMAIN_DISCOVERY_REGISTER.md) report definition — one concept** · **[R-02](../DOMAIN_DISCOVERY_REGISTER.md)** · **[R-13](../DOMAIN_DISCOVERY_REGISTER.md)** *(field, sixth screen)* |
| **Missing workflows** | ⛔ **None** — a report is a saved question, answered over existing reads |
| **Missing entities** | **`ReportDefinition` · `Block`** |
| **Missing business events** | ⛔ **None.** ✅ **Reading a report decides nothing** — [R-14](../DOMAIN_DISCOVERY_REGISTER.md) correctly silent |
| **Missing permissions** | **[R-13](../DOMAIN_DISCOVERY_REGISTER.md) field-level, and this is its clearest statement**: *"respect each viewer's permissions"* on a shared link |
| **Missing projections · platform capabilities** | ⛔ **None** |

> **A screen with one new entity, three inherited capabilities and no workflow is exactly what *"last on evidence"* looks like from the inside.**

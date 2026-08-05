# 460 · People Intelligence, and Design System v2 — the last two audits

**Lane C · Product Office · 2026-08-05.** **Fifteenth and sixteenth audits under [D-078](../DECISION_REGISTER.md). The screen-by-screen phase is complete.**

---

# 1 · People Intelligence — the only screen audited *before* it was audited

**Screen 6 of 16** — *"Buying committee, org chart, relationships, people timeline"* ([410](410-approved-ui-specification.md)). **Wave 6.**

> **Every element traces to [R-01](../DOMAIN_DISCOVERY_REGISTER.md), and [441](441-people-roadmap.md) decomposed R-01 into four milestones nine documents ago.** **There is nothing here the roadmap has not already placed.**

| UI element | Milestone | |
|---|---|---|
| **The committee, as roles** | **M-D** — `Affiliation` intervals, anonymous | 🔴 [TASK-427](../BACKLOG.md) |
| **People timeline** | **M-I** — projection, after [TASK-901](../BACKLOG.md) | 🔴 [TASK-428](../BACKLOG.md) |
| **The committee, as *names*** | **M-E** — needs a provider identifier | 🔴 [TASK-429](../BACKLOG.md) |
| **Org chart** — *confirmed vs inferred* | **M-E.** ⚠️ ***"Confirmed vs inferred"* is `IdentityState` reused** — resolved · ambiguous · unresolved — **and that is a reuse nobody had spotted** | 🔴 [TASK-429](../BACKLOG.md) |
| **Relationships** | **M-E** · ✅ **`Relationship`, `relationship.established`, `relationship.ended` already exist** | 🔴 [TASK-430](../BACKLOG.md) |
| **The screen itself** | **M-U** | 🔴 [TASK-430](../BACKLOG.md) |

## The one new finding

> ⚡ ***"Confirmed vs inferred"* on the org chart is `IdentityState`.** **`knowledge_graph` already models *resolved · ambiguous · unresolved*, and the screen is asking for exactly that distinction rendered.** **So the org chart needs no new confidence concept** — ⛔ **and inventing one would have been a second belief model beside a ratified one.**

**Everything else confirms [D-074](../DECISION_REGISTER.md)'s split.** **Two of six elements are M-D; four are M-E.**

---

# 2 · Design System v2 — the control case

**Screen 2 of 16.** **[411](411-ui-convergence-assessment.md): *"None. This screen requires no backend at all."***

> ## **Audited, and the finding is that there is nothing to find.**
>
> **A methodology that cannot produce an empty result is a methodology that produces findings on demand.** **This screen is the control**, and it returns: **zero entities · zero workflows · zero events · zero permissions · zero platform capabilities · zero vocabulary.**

⚠️ **One boundary worth stating**: **the design system is where [ADR-0034](adr/0034-ubiquitous-language.md)'s customer vocabulary is enforced** — `vocabulary.test.tsx`, `design-tokens.test.tsx`, `no-mock-data.test.tsx`. **Three structural refusals, and [450 §5](450-global-search-traceability-audit.md) recommends a fourth for the single search box.** **That is frontend work and it is 🟢.**

---

# 3 · The phase is complete

**Sixteen screens. Sixteen audits.** **[444](444-executive-dashboard-domain-assessment.md) · [445](445-ai-copilot-traceability-audit.md) · [446](446-companies-traceability-audit.md) · [447](447-signal-center-traceability-audit.md) · [448](448-icp-builder-traceability-audit.md) · [449](449-account-360-traceability-audit.md) · [450](450-global-search-traceability-audit.md) · [451](451-workflow-automation-traceability-audit.md) · [452](452-app-shell-traceability-audit.md) · [453](453-opportunity-intelligence-traceability-audit.md) · [456](456-crm-integrations-traceability-audit.md) · [457](457-ai-research-traceability-audit.md) · [458](458-settings-traceability-audit.md) · [459](459-reports-traceability-audit.md) · and this document's two.**

**The consolidated review follows.**

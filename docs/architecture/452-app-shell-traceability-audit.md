# 452 · App Shell — screen-by-screen traceability audit

**Lane C · Product Office · 2026-08-05.** **Ninth audit under [D-078](../DECISION_REGISTER.md)**, extended through [D-088](../DECISION_REGISTER.md).

**Screen 1 of 16 — *"the frame every module mounts inside"*, 22 numbered specifications** ([410](410-approved-ui-specification.md)).
**The [Foundation Readiness Matrix](../DOMAIN_DISCOVERY_REGISTER.md) named it the highest-value remaining audit: it is the only ⬜ screen that all sixteen inherit.**

---

# 0 · The headline: seven of ten cross-cutting concerns have no representation, and the shell has the highest leverage in the product

**[D-088](../DECISION_REGISTER.md) asks for a consumer count on every foundational capability. The shell is where that measure means most, because *every* count starts at sixteen.**

| # | Concern | Repository today | Consumers | |
|---|---|---|---|---|
| **7** | **Session and identity context** | ✅ **Complete.** Better Auth in Next.js is the sole Authentication Authority; the Python tier verifies RS256 only; `active_workspace_id` is *"a routing hint, never a grant"* and membership is re-verified server-side on every request | **16 + every API call** | ✅ |
| **1** | **Workspace context** | ✅ **Complete** — `CurrentWorkspace`, membership verification, `SET LOCAL app.workspace_id` | **16** | ✅ |
| **3** | **Universal search entry** | 🟡 **`account-search` exists.** ⚠️ ***"Never a second search box"* has no enforcement** — [450 §5](450-global-search-traceability-audit.md) proposes the structural test | **16** | 🟡 |
| **1b** | **Global scope** — period · region · segment · owner | 🔴 **[R-02](../DOMAIN_DISCOVERY_REGISTER.md).** *"Applied **before** a module renders"* | **16 inherit · 5 name it** | 🔴 |
| **2** | **Notifications and activity** | ⏸ **[ADR-0040](adr/0040-notifications.md) deferred** by [D-027](../DECISION_REGISTER.md) | **4 named** | ⏸ |
| **4** | **AI entry points** | 🔴 **The *ask* route is missing** ([445](445-ai-copilot-traceability-audit.md)); the verb taxonomy is [C-419](../LANE_COORDINATION.md) | **17 surfaces** | 🔴 |
| **6** | **User preferences** | 🔴 **Nothing.** ⚠️ **And deliberately *not* saved views** — those are *"per view, not per user, so a shared view looks the same for everyone"* | ⬜ | 🔴 |
| **8** | **Feature flag visibility** | 🔴 **Zero matches.** ✅ **Already deferred with a trigger** — [438 Epic J](438-platform-initiatives.md): *"propose when a slice needs one"* | ⬜ | ⏸ |
| **9** | **Announcement surfaces** | 🔴 **Zero.** [438 Epic J](438-platform-initiatives.md), behind an operator identity | ⬜ | 🔴 |
| **10** | **Background activity indicators** | 🔴 **Zero.** ARQ runs jobs and **nothing surfaces their state** | **§3** | 🔴 |
| **5** | **Global actions** | ⬜ **Not extractable** — the repository does not record what they are | ⬜ | ⬜ |

> ## **Three complete, one deferred with a trigger, one deferred by ruling, five absent, one unknown.**
>
> **And the two that are complete are the two nobody thinks of as shell capabilities** — identity and workspace context. **The shell's *visible* concerns are the missing ones.**

---

# 1 · ⚠️ The correction this audit made to itself

**`ResolveExecutionContext` appears in [411](411-ui-convergence-assessment.md) as *"built and unwired"* and it is tempting to read it as the shell's workspace context. It is not.**

> **It is `integrations`' — it resolves the execution context of a *connected account*, and [411](411-ui-convergence-assessment.md) lists it under CRM Integrations, correctly.** **The shell's workspace context is `signora_platform/api/dependencies.py`'s `CurrentWorkspace`, and it is complete.**

**Two capabilities, similar names, different modules** — **and the [vocabulary graph](../coordination/vocabulary.toml) is exactly the instrument that should have caught it.** ⚡ **It did not, because neither term is registered.** **Recorded: `Execution Context` is a candidate `qualified` term, and this audit is the first evidence for it.**

---

# 2 · The shell's own resolution rule already decides most of this

**[415](415-platform-foundation-incoming.md) quotes the App Shell specification stating its own boundary:**

> ***"Every capability a module thinks it needs from the shell is either…"*** — **the shell states the test rather than leaving it to negotiation.**

**And [415 §3](415-platform-foundation-incoming.md) found five of the shell's 22 sections overlapping incoming platform modules** — workspace switching and preferences with Module 3; the security surfaces with Module 6; branding, seats and invoices with Modules 3 and 8.

| | |
|---|---|
| **Reported then** | *"Seven surfaces will need one owner"* |
| **Withdrawn then, and correctly** | *"Every one of these surfaces defers explicitly"* |
| ⚡ **What this audit adds** | **Two of those five are now on the readiness matrix as absent capabilities with named consumers — user preferences and workspace switching.** **The deferral held; the *capabilities* did not disappear**, and the register is where they now sit |

---

# 3 · ⚡ The convergence: background activity is not a shell feature

**Concern #10 has no representation, and the audit that needs it is not this one.**

> **[446](446-companies-traceability-audit.md) established that bulk work is background work — *"8,412 rows is not a request cycle"*, and ARQ, the outbox, relay and dispatch are all built.**
>
> **A named batch that runs in a worker needs somewhere to say it is running. That is concern #10.**

**So a *"background activity indicator"* is not a shell widget in search of a backend. It is [R-03](../DOMAIN_DISCOVERY_REGISTER.md)'s read surface**, and it should be designed with the batch rather than bolted onto the frame afterwards.

⚠️ **And it inherits [P-A](../DOMAIN_DISCOVERY_REGISTER.md)**: a progress indicator that cannot distinguish *running* from *failed* from *never started* is the same defect PS-01 fixed on the account brief. ***"Absence can never distinguish itself from failure."***

---

# 4 · Findings

| | |
|---|---|
| **Existing and correctly modelled** | **Session and identity** — the JWT boundary, `active_workspace_id` as a hint, server-side membership verification · **workspace context** and RLS scoping · **account search** |
| **Extension candidates** | **A structural test for the single search box** ([450 §5](450-global-search-traceability-audit.md)) · **`Execution Context` as a qualified vocabulary term** — §1 |
| **Architectural evolution** | ⛔ **None. The shell needs no boundary to move** |
| **Missing foundational capabilities** | **[R-02](../DOMAIN_DISCOVERY_REGISTER.md) global scope — highest leverage in the product** · **user preferences, and they are *not* saved views** |
| **Missing workflows** | **Workspace switching** — [415 §3](415-platform-foundation-incoming.md)'s Module 3 overlap, still unowned |
| **Missing entities** | **A user preference.** ⚠️ **Distinct from a saved view by the design's own words** |
| **Missing business events** | ⛔ **None.** ✅ **The shell decides nothing** — [R-14](../DOMAIN_DISCOVERY_REGISTER.md) correctly does not fire |
| **Missing permissions** | ⛔ **None new.** ✅ **The identity layer is the one part of this screen that is finished** |
| **Missing projections** | **Background activity state** — §3, and it belongs to [R-03](../DOMAIN_DISCOVERY_REGISTER.md) |
| **Missing platform capabilities** | **Feature flags** *(deferred, triggered)* · **announcements** *(behind an operator identity)* · **system status** — ⚠️ **`ConnectionHealth` is *integration* health, not *system* status; the shell's concern has no source** |

---

# 5 · 📊 Leverage — the measure [D-088](../DECISION_REGISTER.md) asks for

**Consumer count across current screens, planned screens, workflows and roadmap items. Nine screens audited, so every figure is a floor.**

| Capability | Screens | Workflows | APIs | AI | Roadmap | **Leverage** |
|---|---|---|---|---|---|---|
| **[R-02](../DOMAIN_DISCOVERY_REGISTER.md) Global scope + saved view** | **16 inherit** | Every filtered read | Every list endpoint | Every scoped AI answer | Reports · Segments | 🔴 **Highest in the product** |
| **[R-03](../DOMAIN_DISCOVERY_REGISTER.md) Action batch** | **7** | Bulk · approve · AI apply · **rule subscribers** | Write paths | Every *proposes* surface | Epic F | 🔴 **Highest with a fired trigger** |
| **[R-01](../DOMAIN_DISCOVERY_REGISTER.md) People** | **6** | Committee · org chart · criteria · movements · search | Search · account | Copilot committee reasoning | Epic C entire | 🟠 **High** |
| **[R-00](../DOMAIN_DISCOVERY_REGISTER.md) Criteria Evaluation** | **8** | Backtest · segments · rules · cohorts | ICP · accounts | Cohort research | E1 arrival | ✅ **Shipped** |
| **[R-15](../DOMAIN_DISCOVERY_REGISTER.md) Stated absence** | **5 + certification** | Every read | Every response | Every refusal | — | 🟠 **7 instances, 0 implementations** |
| **User preferences** | ⬜ | ⬜ | ⬜ | — | Module 3 | ⚪ **Unknown — and that is the finding** |

> ## What leverage says that urgency did not
>
> **[R-02](../DOMAIN_DISCOVERY_REGISTER.md) has the highest leverage in the product and it is blocked on *a naming question*** — [TASK-433](../BACKLOG.md), which I have described three times as costing *"one sentence."* **Leverage says that sentence is in front of sixteen screens.**
>
> **And [R-03](../DOMAIN_DISCOVERY_REGISTER.md) is the only capability with both high leverage *and* a fired trigger** — [ADR-0402](adr/0402-a-rule-is-data.md)'s fan-out made it structural. **On leverage, it is the one to rule first.**

---

# 6 · What this produces

**No new backlog row.** **What it changes:** ⚡ **[R-02](../DOMAIN_DISCOVERY_REGISTER.md) is measured as the highest-leverage capability in the product** · **background activity is reassigned from the shell to [R-03](../DOMAIN_DISCOVERY_REGISTER.md)'s read surface** · **user preferences are separated from saved views** · **`Execution Context` is recorded as a vocabulary candidate** · **the shell's readiness rises from ⬜ to 🟢 with three of ten concerns complete.**

---

# 7 · What this document did not do

**Nothing implemented · no lane named · no wave reordered · no module created · no ADR drafted · no queue file touched · no backlog row added.**

**And it did not reopen [O3](../DECISION_REGISTER.md).** **The deferral is about *where shell services live*; this audit says only what they are and how many screens wait on each** — which is the distinction [450](450-global-search-traceability-audit.md) drew for [C-020](../LANE_COORDINATION.md) and [451](451-workflow-automation-traceability-audit.md) drew for [ADR-0402](adr/0402-a-rule-is-data.md).

# 449 · Account 360 — screen-by-screen traceability audit

**Lane C · Product Office · 2026-08-05.** **Fifth audit under [D-078](../DECISION_REGISTER.md)**, extended through [D-082](../DECISION_REGISTER.md).

**Screen 5 of 16, and the only one that has shipped.** **[414](414-wave-1-account-360.md) already holds its field matrix — 23 rows, eleven 🟩, two 🟠, two ➡️, seven ⬜.**
**So this audit does not repeat it. It runs the sweeps 414 predates — lifecycle, events, authorization, partial evaluation — against a screen that exists.**

---

# 0 · The headline: the most reused capability in the product has no name

**[D-082 §4](../DECISION_REGISTER.md) asks Product Office to find places where *"incomplete evaluation could otherwise appear complete."*** **Account 360 is where the repository already solved that, six times, without ever naming it.**

> **PS-01 stated the rule exactly:** ***"If absence and presence carry the same information, render nothing; if the absence **is** the finding, say it. And absence can never distinguish itself from failure."***

| Instance | Where | What it fixed |
|---|---|---|
| **PS-01** | Account 360's brief | *"Two different states rendered as nothing"* |
| **PS-02** | The narration section, **two days later** | *"Three narration states that were one blank space"* — **the same shape in an adjacent section, fixed separately** |
| **PS-06** | An empty list | *"An empty list says why it is empty"* |
| **410** | Every approved screen | *"A facet with zero matches stays visible at 45% **so the absence is information**"* |
| **[TASK-434](../BACKLOG.md)** | The matching predicate | **`unmeasured` is a value in the type, never `false`** |
| **[TASK-406](../BACKLOG.md)** | Criterion lift | *"A criterion no outcome data supports **says so** rather than reporting `1.0×`"* |
| **`missing_gates`** | Certification | ***"Absence is not a pass"*** |

> ## **Seven instances. One idea. No name, no owner, and no shared mechanism.**
>
> **PS-01 and PS-02 are the proof**: two slices, two days apart, fixing the identical shape in adjacent sections of one page — **because the first one ended by saying narration was *"a different question."*** **It was the same question.**
>
> **Recorded as [R-15 · Stated absence](../DOMAIN_DISCOVERY_REGISTER.md).** ⚠️ **It is the highest-reuse concept found in five audits and the only one that was never missing** — it was rediscovered every time somebody needed it.

---

# 1 · What shipped, and what 414 predicted

| | |
|---|---|
| **414 predicted** | Eleven 🟩 buildable in wave 1 |
| **Corrected before a line was written** | **Ten** — the technology-stack section had *"no contract a screen can reach"*, and **it had been counted twice** |
| **Shipped** | ✅ **Ten sections, `PROMOTED`.** **The prediction and the delivery agree exactly** |

> **That is the method's own regression test, and it passes.** **A section-level audit run before implementation predicted the shipped scope to the row**, once its two counting errors were caught by reading rather than by building.

**The two 🟠 are unchanged and are [R-01](../DOMAIN_DISCOVERY_REGISTER.md)**: contacts and the org chart. ⚡ **[448 §3](448-icp-builder-traceability-audit.md) split that dependency, and the split applies here too** — *"24 known contacts"* needs **M-E**; *"6 on the committee"* is role-level and needs **M-D**.

---

# 2 · Lifecycle sweep — the one screen with a human decision that *does* emit

**PS-03, PS-04 and PS-05 shipped a real workflow on this page**: *"the brief says who put this account in front of you"* · *"the decision is the end of the visit"* · *"the account remembers what was decided, and why."*

| | |
|---|---|
| **The completion point** | **A seller takes, dismisses or advances an account** |
| **Does it emit?** | ✅ **Yes — `opportunity.created` · `opportunity.stage_changed` · `opportunity.closed`** |
| **Is the decision recorded?** | ✅ **`opportunity_state`, append-only, with `actor_id`, `reason` and `occurred_at`**, and a constraint making *"intelligence suggests, humans commit"* structural |

> ## This sharpens [R-14](../DOMAIN_DISCOVERY_REGISTER.md) rather than confirming it
>
> **Three screens now have a human completion point. Account 360's emits; Signal Center's and ICP Builder's do not.**
>
> **The difference is not importance — it is age.** **Account 360's decision loop was built when `timeline` and `buying_score_engine` were already consuming it.** **Signal Center's resolution and ICP publication were built before anyone needed to hear them, and consumers appeared later.**
>
> ✅ **So [R-14](../DOMAIN_DISCOVERY_REGISTER.md) is not *"human decisions lack events"*. It is: *an event is created when a consumer appears, and two consumers appeared after the fact.*** **That is the repository behaving correctly and the register having to notice the second half.**

---

# 3 · Authorization sweep

| | |
|---|---|
| **Reading the page** | ✅ `Resource.ACCOUNT`, `read`, both roles |
| **Taking an account** | ✅ `Resource.OPPORTUNITY`, `update`, **granted to `member` deliberately** — *"a member **is** the seller; an SDR who could not take an account on would find the product unusable"* |
| **The boundary that grant does not cross** | ✅ **Asserted in a Security Invariant**: a member still cannot rename the workspace or add a colleague |
| **Asking for research** | ✅ `Resource.RESEARCH` — *"reading an account is free and asking for research spends a model call"* |
| **New dimensions needed** | ⛔ **None.** **The one screen that ships is the one screen whose authorization model is complete** |

> **[R-13](../DOMAIN_DISCOVERY_REGISTER.md) narrows again.** **Four screens audited; the three needing new dimensions are all unbuilt, and the built one needs nothing.** **That is evidence the dimensions are real requirements rather than an audit artifact** — they appear exactly where new capability appears.

---

# 4 · The seven ⬜ sections, re-checked against [D-082 §4](../DECISION_REGISTER.md)

**Product usage · intent · calls · documents · notes · key facts · relationship history.** **Seven sections with no source, on a shipped page.**

| | |
|---|---|
| **Did the screen ship them as absences?** | ✅ **They were not shipped at all** — wave 1 delivered ten sections and 414 drew the boundary before anything was built |
| **The honest risk this raises** | ⚠️ **A page showing ten of twenty-three sections does not, by itself, tell a customer that thirteen exist.** **PS-01's rule governs a section that renders nothing; it says nothing about a section that is not there** |
| **Whether that is a defect** | ⬜ **Not extractable.** **Whether the approved design shows absent sections as placeholders or omits them is a fact about the design project**, and the repository does not record it |

> **This is exactly the case [D-082 §4](../DECISION_REGISTER.md) describes and I cannot resolve it from evidence.** **Recorded ⬜ with the question stated precisely, which is more useful than either answer guessed.**

---

# 5 · 📊 Platform reuse density ([D-082 §5](../DECISION_REGISTER.md))

**First measurement. Five screens audited of sixteen, so every count is a floor.**

| Capability | Consuming screens | Workflows | Dependent modules | Status | Wave |
|---|---|---|---|---|---|
| **[R-15](../DOMAIN_DISCOVERY_REGISTER.md) Stated absence** | **7 instances across 5 screens + certification** | Every read | **Product Surface · `ai_platform` · `commercial_profile` · certification** | ⚠️ **Exists 7×, named 0×** | — |
| **[R-00](../DOMAIN_DISCOVERY_REGISTER.md) Account matching** | **8** | Backtest · segments · rules · cohorts | `commercial_profile` + consumers | ✅ **`PROMOTED`** | Shipped |
| **[R-01](../DOMAIN_DISCOVERY_REGISTER.md) People** | **5** | Committee · org chart · criteria · movements | `people` · `knowledge_graph` · `commercial_profile` · `timeline` | **Sequenced, split M-D/M-E** | **1.5** |
| **[R-03](../DOMAIN_DISCOVERY_REGISTER.md) Action batch** | **6** | Bulk · approve · AI apply | ⚠️ **Undecided** | **Awaiting shape ruling** | — |
| **[R-02](../DOMAIN_DISCOVERY_REGISTER.md) Scope · saved view** | **5 named, 16 inherit** | Every filtered read | ⚠️ **Undecided** | **Awaiting naming ruling** | 3 |
| **Timeline** | **8** *(414 · 411 · 445 · 447)* | Projection | `timeline` + 9 publishers | ✅ **Built** ⚠️ 2 of 9 wired | [TASK-901](../BACKLOG.md) |
| **Explainability / grounding** | **Every AI surface** | Narration · reasoning · research | `ai_platform` · both engines | ✅ **Built** | Shipped |
| **[R-13](../DOMAIN_DISCOVERY_REGISTER.md) Authz dimensions** | **3, all unbuilt** | Spend · field · quantity | `signora_platform` | 🔴 **Missing** | — |
| **[R-14](../DOMAIN_DISCOVERY_REGISTER.md) Completion events** | **2 waiting, 1 satisfied** | Triage · ICP publication | `signal_engine` · `commercial_profile` | **[TASK-432](../BACKLOG.md) + `icp.declared`** | — |

> **The density measurement immediately says something the audits could not**: **the most-reused concept in the product is the one nobody has ever built as a capability.** **R-15 is at seven instances and zero implementations** — every one of them written separately.

---

# 6 · Findings

| | |
|---|---|
| **Existing and correctly modelled** | Ten shipped sections · `opportunity_state` with its constraint · the three completion events · `Resource.ACCOUNT`/`OPPORTUNITY`/`RESEARCH` and the invariant pinning their boundary · the evidence chain behind every section |
| **Extension candidates** | ⛔ **None on the shipped surface** |
| **Architectural evolution** | ⚠️ **[R-15](../DOMAIN_DISCOVERY_REGISTER.md) should be a named, owned capability rather than a habit** |
| **Missing foundational capabilities** | ⛔ **None new** |
| **Missing workflows · entities · permissions · projections · platform capabilities** | ⛔ **None** — **the shipped screen is architecturally complete for what it shows** |
| **Missing business events** | ⛔ **None.** ✅ **The one screen with a mature completion point already emits three** |

---

# 7 · What this produces

**No new backlog row.** **[R-15](../DOMAIN_DISCOVERY_REGISTER.md) is recorded and deliberately not proposed as work** — *"introduce new foundations only when multiple independent consumers justify them"* is satisfied seven times over, **and the honest recommendation is to name it before the eighth instance is written, not to refactor the seven.**

**What it changes:** **[R-14](../DOMAIN_DISCOVERY_REGISTER.md) is restated as *an event is created when a consumer appears*** · **[R-13](../DOMAIN_DISCOVERY_REGISTER.md) narrows again — the built screen needs no new dimension** · **[R-01](../DOMAIN_DISCOVERY_REGISTER.md)'s M-D/M-E split applies to contacts and org chart** · **the first reuse-density table exists.**

---

# 8 · What this document did not do

**Nothing implemented · no lane named · no wave reordered · no module created · no ADR drafted · no queue file touched · no backlog row added.**

**And it did not re-litigate [414](414-wave-1-account-360.md).** **That document's field matrix stands, its prediction matched the delivery to the row, and this audit added the four sweeps it predates.**

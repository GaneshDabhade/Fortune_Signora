# 464 · TASK-433 — the implementation impact of delaying a naming decision

**Lane C · Product Office · 2026-08-06.** **[D-097](../DECISION_REGISTER.md), on the product owner's request for an updated recommendation with its implementation impact.**

> **The recommendation is unchanged. The *argument* has changed, and it is now much shorter.**

---

# 0 · The finding, and it came out of Lane A's queue rather than out of R-02

**Every previous case for [TASK-433](../BACKLOG.md) was made in screens: *"sixteen inherit it"*, *"highest leverage in the product"*. Correcting Lane A's queue today produced a better one.**

| | |
|---|---|
| **[R-02](../DOMAIN_DISCOVERY_REGISTER.md)'s owner, ruled [D-091](../DECISION_REGISTER.md)** | **`workspace_tenancy`** |
| **`workspace_tenancy`'s owner, from [`modules.toml`](../coordination/modules.toml)** | ⚡ **Lane A** |
| **Lane A's claimable work, measured today** | ⚡ **Zero. The only two startable rows on the board — [TASK-201](../BACKLOG.md) and [TASK-202](../BACKLOG.md) — are both in Lane B's modules** |

> ## **TASK-433 is not a naming question in front of sixteen screens. It is a naming question in front of the idle lane's next four slices.**
>
> **[455 §4](455-context-definitions-r02-r03.md) decomposed R-02 into four slices, in a module Lane A owns, and slice 1 is the `public/` contract alone — the cheapest possible start.** **The ruling and the lane's next work are the same sentence.**

---

# 1 · The five dimensions asked for

| | |
|---|---|
| **Implementation leverage** | **16 screens inherit the shell's scope; 4 name a saved view directly** — Companies, App Shell §6, Global Search, Reports. **Unchanged, and it was never the strongest argument** |
| **Repository impact** | 🟢 **Small and bounded.** One table, one reader, one writer, **no behaviour**, in a module with 14 routes and the largest router in the repository. **Zero new dependency edges** — `opportunity_engine` already imports `WorkspaceQueryPort` from `workspace_tenancy.public`, so the pattern is running |
| **Affected screens** | **Companies · App Shell · Global Search · Reports**, and **every screen that mounts inside the shell** |
| **Downstream prepared slices** | **4, decomposed and waiting** ([455 §4](455-context-definitions-r02-r03.md)) — **and slice 1 unblocks all four consumers before a row is persisted** |
| ⚡ **Opportunity cost of continued delay** | **Lane A is idle with zero claimable rows, and this is the work it would take.** **Everything else in its six modules is `IN VALIDATION`, `IN PROGRESS`, or behind [C-417](../LANE_COORDINATION.md)** |

---

# 2 · What the delay actually costs, stated without inflation

**⛔ It is not blocking a customer.** **No approved screen is being built today that needs a saved view** — the shell is wave 3, Companies is wave 3, Reports is wave 7.

**⛔ And it is not an emergency.** **A month of delay costs nothing to a screen nobody is building.**

> ## **What it costs is that the repository's only idle lane stays idle.**
>
> **That is a throughput cost, not a product one, and it is worth stating as the smaller thing it is.**

⚠️ **One second-order cost is worth naming, because it grows rather than waits:** **App Shell is wave 3 and *all sixteen screens inherit it*.** **A shell built before scope has a home is a shell that grows its own** — and [452](452-app-shell-traceability-audit.md) found the shell is *"the least-ready screen and the one every other screen inherits."* **The window where this is a naming decision closes when wave 3 starts.**

---

# 3 · ⬜ The complication that has not gone away

**[446 §0](446-companies-traceability-audit.md): the naming question is *downstream of a semantic one*, and the semantic one is not extractable from the repository.**

| If Companies' *"segments"* are… | Then |
|---|---|
| **ICP cohorts** | ✅ **No collision at all.** [TASK-434](../BACKLOG.md)'s predicate already answers it, and R-02 needs no new word |
| **Arbitrary saved filters** | 🟠 **A different concept holding a taken word**, and §4 forbids it |

> **So a ruling has two forms, and the cheaper one may be available:** ***"Companies' segments are ICP cohorts"*** **ends the question without naming anything** — **or `SavedView` is adopted as the canonical term and `Segment` stays `commercial_profile`'s.**
>
> ⚡ **Lane C's recommendation is unchanged and is the second**: **`SavedView` for the filter, `Segment` unchanged for the ICP concept.** **The customer already says *"my saved view"* and *"my segment"* about different things, so [ADR-0034](adr/0034-ubiquitous-language.md)'s test is satisfied without inventing a word.**

---

# 4 · Recommendation

> **Unchanged: adopt `SavedView`, leave `Segment` with `commercial_profile`, and register both** ([`vocabulary.toml`](../coordination/vocabulary.toml) already holds `Segment` as `proposed` with the dispute recorded).

**What changed is only the reason to do it now rather than at wave 3:**

| | |
|---|---|
| **Then** | *"Sixteen screens inherit it"* |
| ⚡ **Now** | **"It is the idle lane's next four slices, and the lane is idle today"** |

⛔ **And what has not changed: this office does not place the row.** **A ruling makes R-02 preparable; [TASK-433](../BACKLOG.md)'s position in the queue remains the product owner's.**

---

# 5 · What this document did not do

**Nothing implemented · no lane named to the work · no row placed · no vocabulary term promoted · no ADR drafted.**

⚠️ **And it did not inflate the cost.** **The honest headline is that delay costs throughput rather than product, and saying so is more useful than an urgency this evidence does not support.**

# 454 · R-02 and R-03 — from discovery to execution

**Lane C · Product Office · 2026-08-05.** **[D-090](../DECISION_REGISTER.md): both capabilities are architecturally established, so this office stops proving they exist and prepares them.**

> ***"Do not continue collecting the same evidence once the architectural conclusion has become stable."***

**This document finalises ownership, boundaries, prerequisites, consumers and sequencing.** **It implements nothing and assigns nothing.**

---

# 0 · Why these two, and why now

| | [R-02](../DOMAIN_DISCOVERY_REGISTER.md) Saved view · global scope | [R-03](../DOMAIN_DISCOVERY_REGISTER.md) Action batch |
|---|---|---|
| **Independent screens** | **4 state a property each, and none contradicts another** | **7 assert the guarantee in different words** |
| **Confidence** | 🏛️ **Architecturally Established** | 🏛️ **Architecturally Established** |
| **Trigger** | Not fired | ✅ **Fired, structurally** — [ADR-0402](adr/0402-a-rule-is-data.md)'s fan-out |
| **Blocked by** | **A name** — [TASK-433](../BACKLOG.md) | **A shape** — [TASK-431](../BACKLOG.md) |
| **Owner today** | ⚠️ **None** | ⚠️ **None** |

> **[D-090 §4](../DECISION_REGISTER.md): *"Avoid allowing implementation lanes to implicitly become the owner simply because they encounter the capability first. Ownership should be an architectural decision rather than an implementation accident."*** **Both are one slice away from exactly that.**

---

# 1 · R-02 · Saved view — recommended owner: **`workspace_tenancy`**

## The specification four screens wrote without conferring

> **A saved view is a *named, shared, immutable declaration of a query, evaluated per reader at read time*.**

**Companies** — *"pinning is per view, not per user, **so a shared view looks the same for everyone**"* · **App Shell §6** — *"survives navigation, **serialises to the URL**, and can be saved as a named view"* · **Global Search** — *"stores the query, the filters and the sort — **not the results**"* · **Reports** — *"views are shared by link and **respect each viewer's permissions**"*.

## Why `workspace_tenancy`, and it is not a process of elimination

| | |
|---|---|
| ✅ **It already owns this shape** | **Workspace-scoped, member-attributed, permission-respecting durable state** is `Membership`, `Invitation`, `WorkspaceRole` and the organization history — **thirteen endpoints and the largest router in the repository** |
| ✅ **"Respects each viewer's permissions" *needs* it** | **A view evaluated per reader needs that reader's role and membership**, which is this module and no other |
| ✅ **The precedent is built and running** | **`opportunity_engine/application/transition.py` imports `WorkspaceQueryPort` from `workspace_tenancy.public`.** **A business module already reads tenancy through `public/`** — the edge exists, the contracts permit it, and nothing needs amending |
| ✅ **No commercial semantics leak** | ⚡ **The store never interprets the query.** It holds a name, an author, a workspace and **an opaque declaration**; the *consumer* interprets it. **A saved view of accounts and a saved search of entities are one row shape** |
| ⛔ **Not `signora_platform`** | §20a freezes it, and *"the platform composes modules; it never becomes the owner of their internals."* **A named view is product state, not substrate** |
| ⛔ **Not a new bounded context** | 🔴 and an ADR, **for a table with four columns and no behaviour.** *"Missing bounded contexts: only if truly justified"* |
| ⛔ **Not the frontend** | *"Shared, permission-respecting and durable **means server-side**. It cannot be `localStorage` and satisfy 'looks the same for everyone'"* — [417 §2a](417-executable-slice-audit.md) |

> ## ⚠️ The one thing this recommendation does **not** decide
>
> **[O3](../DECISION_REGISTER.md) is deferred and stays deferred.** **O3 asks *where the shell's scope service lives* — who *consumes* the store.** **This asks who *owns* it.** **[417 §2a](417-executable-slice-audit.md) drew that line first: *"the store is required regardless of how O3 is answered."***

## Public boundary

**`SavedViewReader` and `SavedViewWriter` in `workspace_tenancy/public/`**, on the `View · ListView · Reader` triple the module already publishes three times.

⛔ **The store never parses, validates, executes or ranks a query.** **A view that could be *wrong* would make this module responsible for another module's semantics** — which is the boundary `commercial_profile` holds by never reading the pipeline.

## Prerequisites · consumers · sequencing

| | |
|---|---|
| **Prerequisites** | ⚠️ **One, and it is [TASK-433](../BACKLOG.md)** — **the name.** ⬜ **And the `Segment` question is upstream of it**: if Companies' segments *are* ICP cohorts, one consumer disappears |
| **Consumers** | **Companies · App Shell · Global Search · Reports** — and **16 screens inherit the shell's** |
| **Sequence** | **After [TASK-433](../BACKLOG.md), before wave 3.** **The shell is wave 3 and all sixteen screens inherit it** |
| **Complexity** | 🟢 **Low.** One table, one reader, one writer, no behaviour |

---

# 2 · R-03 · Action batch — recommended owner: **a new bounded context**, and here is why nothing else fits

## What seven screens assert

> **A change that waits for a human, is recorded as one named thing with an author, and can be taken back inside a stated window.**

## The disqualifications, each on a rule rather than a preference

| | |
|---|---|
| ⛔ **Not per-module** | **[ADR-0402](adr/0402-a-rule-is-data.md) §2 makes *N* subscribers act on one event.** **Per-module means implementing the guarantee once per subscriber** — [451 §0](451-workflow-automation-traceability-audit.md) |
| ⛔ **Not `signora_platform`** | **§20a.** ***An approval is product semantics*** — who approved what, and until when — **not substrate.** *"The platform composes modules; it never becomes the owner of their internals"* |
| ⛔ **Not `opportunity_engine`** | **It owns the *pattern*** — `opportunity_state` is append-only with actor, reason and `MACHINE_AUTHORED = frozenset({Stage.TRACKING})` — **and generalising from it would make every module's approvals depend on the opportunity module** |
| ⛔ **Not `workspace_tenancy`** | ⚠️ **This is where the R-02 argument stops.** **A saved view is opaque to its store; a batch is not** — it carries what was proposed and what withdrawing means, **which is domain content** |

## The boundary that makes a new context small

> ## ⚡ **The batch owns the *decision and the window*. The acting module owns the *inverse operation*.**

| The batch context holds | The acting module holds |
|---|---|
| **What was proposed, by whom or by what** | **The write itself** |
| **Who approved it, and when** | **How to undo its own write** |
| **The named unit, and how many changes it covers** | **Its own domain rules** |
| **Whether `now() < applied_at + window`** — **[P-B](../DOMAIN_DISCOVERY_REGISTER.md), a read-time predicate** | — |

**Because only a module knows how to reverse its own write** — §2's *least powerful author*, and the reason this context stays small enough to be justified. ⚡ **And it is [ADR-0402](adr/0402-a-rule-is-data.md)'s own shape reused: one context records, the acting modules act.**

## Prerequisites · consumers · sequencing

| | |
|---|---|
| **Prerequisites** | **[TASK-431](../BACKLOG.md)'s shape ruling**, and 🔴 **an ADR — a new bounded context always needs one.** ✅ **[447 §0](447-signal-center-traceability-audit.md) already removed the hardest part: no scheduler** |
| **Consumers** | **Workflow subscribers · Companies bulk · Copilot's 17 surfaces · Opportunity next-actions · Settings · Account 360's AI sections · Executive Dashboard** |
| **Sequence** | ⚡ **Before wave 2.** **AI Copilot is wave 2 and asserts the guarantee on 17 surfaces** |
| **Complexity** | 🟠 **Medium** — one context, one port, **and a progress surface** ([452 §3](452-app-shell-traceability-audit.md)), **which must state *running* / *failed* / *never started* distinctly** ([P-A](../DOMAIN_DISCOVERY_REGISTER.md)) |

---

# 3 · The other two ownerless capabilities, named rather than left

**[D-090 §4](../DECISION_REGISTER.md) makes ownership higher priority than more evidence. Four were ownerless; two are recommended above.**

| | Recommendation | Confidence |
|---|---|---|
| **[R-07](../DOMAIN_DISCOVERY_REGISTER.md) Audit surface** | **`workspace_tenancy`** — it already publishes **the only history endpoint in the repository**, `GET /workspaces/{id}/history`, and *"a history only administrators may read is a history…"* is its sentence | 🟡 **Validated, not established** — 3 screens |
| **[R-11](../DOMAIN_DISCOVERY_REGISTER.md) Forecast** | ⛔ **Do not assign an owner.** **[C-418](../LANE_COORDINATION.md) may answer *no*, and an owner for a capability that may not exist is the accident §4 warns about** | 🟡 **Blocked on a product decision** |

---

# 4 · What this asks for

**One ruling covers both, and it is smaller than it looks:**

> **[TASK-433](../BACKLOG.md) — the name — and [TASK-431](../BACKLOG.md) — the shape — each gain a recommended owner.** **Approving the owner alongside the ruling turns two open questions into two prepared slices.**

**Nothing else is requested.** **No ADR is drafted, no module created, no lane named, no row assigned** — **and R-03's ADR is deliberately not written until its shape is ruled**, because [443](443-account-matching-capability.md) and [451](451-workflow-automation-traceability-audit.md) both showed an ADR written ahead of a shape ruling gets its sizing wrong.

---

# 5 · What this document did not do

**Nothing implemented · no lane named · no ADR drafted · no module created · no wave reordered · no queue file touched · no backlog row added.**

**And it stopped collecting evidence.** **Both capabilities were confirmed by four and seven independent screens respectively, and further audits would have raised the count without changing the conclusion** — which [D-090](../DECISION_REGISTER.md) names as the point to stop.

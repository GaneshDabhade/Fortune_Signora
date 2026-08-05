# 451 · Workflow Automation — screen-by-screen traceability audit

**Lane C · Product Office · 2026-08-05.** **Seventh audit under [D-078](../DECISION_REGISTER.md)**, extended through [D-084](../DECISION_REGISTER.md).

**Screen 10 of 16** — *"Simulated before it runs, approved before it writes, reversible after it does"* ([410](410-approved-ui-specification.md)).
**[ADR-0402](adr/0402-a-rule-is-data.md) is `RATIFIED` and specifies the module.** **This screen carries [R-03](../DOMAIN_DISCOVERY_REGISTER.md)'s third independent statement.**

---

# 0 · The headline: a ratified ADR already answers R-03's owner question

**[ADR-0402 §2](adr/0402-a-rule-is-data.md), ratified:**

> ***"`workflow` performs no action, delivers no message, and invokes no other module. A match is an event. Whoever should act subscribes."***

**The screen says *"approved before it writes."*** **At first reading that contradicts a module that never writes. It does not — and the resolution is the finding.**

| | |
|---|---|
| **What `workflow` does** | **Matches a condition tree and publishes `workflow.rule_matched`.** **It never writes** |
| **Who writes** | **The subscriber.** *"Whoever should act subscribes"* |
| **So whose approval is it?** | ⚡ **Not `workflow`'s. The acting module's** |

> ## And that decides something [TASK-431](../BACKLOG.md) has been waiting on.
>
> **ADR-0402 makes one event and *N* subscribers the architecture.** **If approval-apply-reverse belongs to each acting module, it is implemented *N* times** — which is the duplication [R-03](../DOMAIN_DISCOVERY_REGISTER.md) exists to prevent, arriving through a door nobody was watching.
>
> ✅ **So the ratified architecture argues for [TASK-431](../BACKLOG.md) option (b) — one owning context, consumed through `public/` — and against (c) per-module.** **Not because Lane C prefers it: because a ratified ADR already committed this repository to a fan-out, and (c) multiplies by the fan-out.**

**This is the screen I said would tell us whether R-03 is a domain capability or a platform one. It says: whichever it is, it must be *one*.**

---

# 1 · The traceability matrix

✅ exists · 🟡 extend · 🟠 conflicts · 🔴 missing · ⬜ not yet extractable

| UI element | Business meaning | Source of truth | Audit | Owner | Consumers | Priority |
|---|---|---|---|---|---|---|
| **A rule** | A trigger plus a condition | **Domain type** — a condition tree, versioned like a declaration | 🔴 **The module is unbuilt.** ✅ **Fully specified — [ADR-0402](adr/0402-a-rule-is-data.md), and *"phases 1–4 depend on nothing unbuilt"*** | `workflow` *(new)* | Workflow Automation | **Wave 5** |
| **The trigger catalog** | What a rule may fire on | **Reviewed catalog** | 🔴 **Unbuilt, specified.** ✅ **And it *"refuses what cannot fire"*** — the Signal Catalog's discipline, reused | `workflow` | Workflow Automation | — |
| **"Simulated before it runs"** | **Show me what this rule *would* have matched** | **Computed view** — the condition tree over recorded events | 🔴 **Missing, and unspecified.** ⚠️ **ADR-0402 does not mention simulation.** `dry_run`, `preview`, `what_if` return **zero** | `workflow` | Workflow Automation | **§2** |
| **"Approved before it writes"** | A human authorises the consequence | **[R-03](../DOMAIN_DISCOVERY_REGISTER.md)** | 🔴 **And it is the *subscriber's*, not `workflow`'s** — §0 | ⚠️ **[TASK-431](../BACKLOG.md)** | **7 screens now** | **Ruling due** |
| **"Reversible after it does"** | Taking back what was written | **[R-03](../DOMAIN_DISCOVERY_REGISTER.md)** + **[P-B](../DOMAIN_DISCOVERY_REGISTER.md)** | 🔴 ✅ **The mechanism is settled** — [447 §0](447-signal-center-traceability-audit.md): a window is a read-time predicate | ⚠️ [TASK-431](../BACKLOG.md) | **7 screens** | — |
| **A rule matched** | The one thing `workflow` emits | **Business event** — `workflow.rule_matched` | 🔴 **Unbuilt, specified.** ✅ **[P-C](../DOMAIN_DISCOVERY_REGISTER.md) satisfied in advance** — the event exists *because* subscribers are the architecture | `workflow` | Notifications · acting modules | — |
| **A rule that reaches nobody** | A match with no delivery | — | ⏸ **[ADR-0040](adr/0040-notifications.md), deferred.** ✅ **And ADR-0402 was written so this is not a block**: *"phases 1–4 depend on nothing unbuilt"* | `notifications` | — | — |
| **Rule authoring UI** | A customer builds a condition | **Domain type**, rendered | ⬜ **Not extractable.** **Whether the screen exposes the tree, a natural-language builder, or templates is a design fact the repository does not hold** | Product Surface | Workflow Automation | **Extraction** |
| **A rule writing to a declaration** | — | — | ✅ **Forbidden, and already ruled**: [ADR-0402 §4](adr/0402-a-rule-is-data.md) — **a rule may not write to a customer's declarations** | — | — | — |

**Nine elements: 3 ✅ · 5 🔴 · 1 ⬜** — **and every 🔴 but one is specified rather than undesigned.**

---

# 2 · Simulation — the element ADR-0402 does not cover

**"Simulated before it runs" is the screen's first word, and the ratified ADR is silent on it.**

| | |
|---|---|
| **What it means** | **Evaluate the condition tree over events that already happened, and show what would have matched — without publishing anything** |
| **Is it new architecture?** | ⛔ **No.** ✅ **It is [P-B](../DOMAIN_DISCOVERY_REGISTER.md) exactly**: evaluate at read time, materialise nothing, act on nothing. **A simulation is the rule's predicate applied to history** |
| **Does the history exist?** | ✅ **`business_event_engine` stores business events with their evidence, and a trigger catalog *"refuses what cannot fire"*** — so the triggerable set and the recorded set are the same set |
| **What it must not become** | ⛔ **A second evaluator.** **The simulation and the live match must be one condition-tree evaluation with two callers**, or they will disagree — and **the one that disagrees silently is the simulation, because nobody checks it** |

> **Recommendation: simulation is a *second caller of the same evaluator*, named in ADR-0402's phase plan rather than added later.** ⚠️ **It is cheap now and expensive after phase 1 ships**, because a live evaluator written without a pure entry point acquires one by refactor.
>
> **Recorded as an amendment candidate to [ADR-0402](adr/0402-a-rule-is-data.md), not a new ADR** — the decision it needs is *"phases 1–4 include a pure evaluation entry point"*, which is a sizing change, not an architectural one.

---

# 3 · 🎯 Trigger conditions ([D-084](../DECISION_REGISTER.md) §3)

**This screen's ADR is unusually good at these, and they should be tracked rather than rediscovered.**

| Capability | Trigger condition, stated | Source |
|---|---|---|
| **An expression language instead of a condition tree** | ***"A real customer condition the tree cannot represent, not a hypothetical one"*** | [ADR-0402](adr/0402-a-rule-is-data.md) |
| **Notifications** | **Epic F phase 5** — *"a rule that matches and reaches nobody needs Notifications to become useful"* | [ADR-0402](adr/0402-a-rule-is-data.md) |
| **A search index** | ⚡ **Proposed [450 §1](450-global-search-traceability-audit.md)**: *the first search that must rank across more than one type* | [C-020](../LANE_COORDINATION.md) |
| **[R-03](../DOMAIN_DISCOVERY_REGISTER.md)** | ⚡ **Named here**: **the second module that needs to approve, apply and reverse.** **Workflow's subscribers make that structural rather than hypothetical** | This audit |
| **Person naming** | **A provider contract supplying an identifier** | [TASK-429](../BACKLOG.md) |
| **Deletion strategy** | **First retention obligation · first deletion request · migration 0050** | [TASK-426](../BACKLOG.md) |

> **Six triggers, five of which already existed in scattered documents.** **Collected, they are the repository's actual roadmap** — *"the point at which an existing implementation naturally stops scaling."*

---

# 4 · Findings

| | |
|---|---|
| **Existing and correctly modelled** | [ADR-0402](adr/0402-a-rule-is-data.md) whole — condition tree as data, one event, no actions, no writes to declarations · the outbox chain the event will use · `business_event_engine`'s stored history |
| **Extension candidates** | **A pure evaluation entry point in phases 1–4**, so simulation and live matching are one evaluator — §2 |
| **Architectural evolution** | ⛔ **None. The ADR holds** |
| **Missing foundational capabilities** | **[R-03](../DOMAIN_DISCOVERY_REGISTER.md)** — and this screen makes its *shape* argument, not just its count |
| **Missing workflows** | **Simulation** |
| **Missing entities** | ⛔ **None unspecified** — the rule, the catalog and the event are all designed |
| **Missing business events** | ⛔ **None.** ✅ **`workflow.rule_matched` is [P-C](../DOMAIN_DISCOVERY_REGISTER.md) satisfied in advance** |
| **Missing permissions** | ⚠️ **Authoring a rule is an administrative act; a rule matching is not.** **No `Resource.WORKFLOW` exists** — the same shape as `Resource.SIGNAL`, ruled and unbuilt |
| **Missing projections** | **Simulation results** — §2 |
| **Missing platform capabilities** | ⛔ **None** |

---

# 5 · Cross-screen convergence

| | Screens | Change |
|---|---|---|
| **[R-03](../DOMAIN_DISCOVERY_REGISTER.md)** | **7** | ⚡ **Its owner question is answered by a ratified ADR** — §0. **The fan-out makes (c) per-module untenable** |
| **[P-B](../DOMAIN_DISCOVERY_REGISTER.md) predicate over stored state** | **4 screens** | ✅ **Confirmed again** — simulation is the same predicate with a different caller |
| **[R-13](../DOMAIN_DISCOVERY_REGISTER.md)** | **5** | 🟡 **Workflow authoring is administrative; matching is not.** **A `Resource` gap, not a new dimension** — R-13 stays at three dimensions |
| **[R-15](../DOMAIN_DISCOVERY_REGISTER.md)** | — | ⬜ **No instance.** ⚠️ **Second screen with none** — worth watching, because a simulation that silently omits an unevaluable condition is exactly P-A's failure mode |

---

# 6 · What this produces

**No new backlog row.** **What it changes:** ⚡ **[TASK-431](../BACKLOG.md)'s shape question gains a ratified argument** · **simulation is recorded as an ADR-0402 sizing amendment rather than a new capability** · **six trigger conditions are collected in one place for the first time** · **[R-13](../DOMAIN_DISCOVERY_REGISTER.md) is held at three dimensions rather than grown.**

---

# 7 · What this document did not do

**Nothing implemented · no lane named · no wave reordered · no module created · no ADR amended · no queue file touched · no backlog row added.**

**And it did not reopen [ADR-0402](adr/0402-a-rule-is-data.md).** **It found the ADR silent on one element and recorded the amendment as a sizing question** — the same distinction [443](443-account-matching-capability.md) drew when ADR-0404's sizing was wrong and its decision stood.

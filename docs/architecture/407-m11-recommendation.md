# 407 — M11 · Recommendation Engine — implementation preparation

> **Prepared by Lane C — Product Office. No code was written and none should be.** **Every claim verified against source on 2026-08-04.**
>
> **Observability, testing, operations and deployment: [405-cross-cutting-concerns.md](405-cross-cutting-concerns.md).** M11's deltas are in §9.

> **Approved UI** — **Opportunity Intelligence** · **Companies**. The [Fortune Signora Design Project](410-approved-ui-specification.md) is authoritative for frontend behaviour (2026-08-04). **This package no longer states what the screen looks like; it states what the backend must provide for it.** *"Ranked by expected effect on this quarter · you approve, Signora drafts"* and *"Nothing sends without your approval. Reversible for 24 hours."* **`sales_engagement` already produces `Recommendation`, `Risk` and `NextAction`; it has no `interface/` layer** ([412](412-backend-capability-matrix.md)).


---

## 1 · Executive summary, and the finding

**M11 is the last module of the intelligence pipeline** — `06-events.md` marks it *"**M11** | Recommendations | **Full pipeline**"*. Its purpose is settled and has been for months:

> **`04-modules.md`:** *"Converts AI Reasoning Engine output and opportunity context into concrete, actionable **recommendations** for sales users."* **Owns:** generation rules, prioritisation, **lifecycle (open / acted-on / dismissed / expired)**. **Consumes:** `ai_reasoning.completed`. **Publishes:** `recommendation.created`, `recommendation.status_changed`.

**The finding is about its input, and it is the same blocker Epic G has.**

| | Verified state |
|---|---|
| **The module** | **Does not exist.** `ls backend/modules/` — sixteen modules, no recommendation engine |
| **Its consumed event** | **`ai_reasoning.completed` is published** — `ai_reasoning_engine/domain/events.py:61` |
| **Anything consuming it** | **Nothing.** `apps/worker/subscriptions.py` wires **two** handlers: `_run_requested_research` and `_project_to_timeline` |
| **Whether it ever fires** | ⚠️ **`reasoning@1` has no released model.** [404](404-epic-g-copilot.md) §1 — four evaluations, all against the wrong dataset, none on `llama3.1:8b` |
| **Its published events** | Catalogued, **no publisher** — [402](402-epic-f-workflow.md) §1 counted them among the eleven |
| **Its consumers** | **Timeline** (built) and **Revenue Intelligence Platform** (**does not exist**) |

> **M11 sits between a producer whose output has never been released and a consumer that has not been built.** **It is not blocked by anything M11-shaped**, and no amount of preparing M11 changes that.

**And the repository predicted this.** `ai_platform/domain/events.py:5` — *"**A substrate emitting events nobody consumes is speculative by definition**, and `ai_reasoning.completed` (M9) and `ai_research.completed` (M10) are already reserved for the modules that will actually produce them."* **The reservation was made; the module never arrived.**

---

## 2 · The principle that decides M11's shape

> **`opportunity_engine`, ratified 2026-07-29:** ***"Intelligence suggests. Humans commit."***

**A recommendation is the purest form of *suggests* in the entire product.** Everything upstream derives — a claim, an observation, an event, a signal, a score. **M11 is the first module whose output is addressed to a person as something to do.**

**Which fixes three boundaries before any design begins:**

| | |
|---|---|
| **M11 never acts** | Not a CRM write ([E2](406-epic-e2-crm-write-back.md)), not a message, not a stage change. **It produces content and a lifecycle** |
| **M11 never concludes** | *"Does Not Own: the reasoning content itself (AI Reasoning Engine)."* **It converts a conclusion into an action a person could take** |
| **Acting on one requires a human** | `acted-on` needs an `actor_id`, exactly as `opportunity_engine` requires beyond `MACHINE_AUTHORED` |

**Three modules now sit adjacent and must not converge**, and the repository has already drawn two of the three lines:

```
  what Signora concluded   →  AI Reasoning        content, grounded, cited
  what to do about it      →  Recommendation      ← M11: content + lifecycle
  that somebody should be
  told about it            →  Notifications       ADR-0040, Proposed
  a condition a customer
  wrote was met            →  Workflow            ADR-0402, Proposed
```

> **[ADR-0040](adr/0040-notifications.md) already states the M11/Notifications line:** *"**A recommendation is content; a notification is that somebody should be told about it.** Recommendation Engine is also not started."* **The line M11 must add is against [Epic F](402-epic-f-workflow.md):** a workflow rule fires because **a customer wrote a condition**; a recommendation exists because **Signora reasoned**. **Same shape on screen, opposite authorship** — and if they converge, a customer cannot tell which of their own rules produced advice they did not write.

---

## 3 · Repository reuse — what must NOT be built

| ❌ Do not build | ✅ Exists as | Consequence |
|---|---|---|
| **Reasoning, or a second explanation** | `ai_reasoning_engine` · the **Contribution Ledger** | Two explanations that will disagree |
| **A grounding or citation protocol** | **[ADR-0031](adr/0031-evidence-citation-protocol.md)** — one owned grammar | The defect that cost three releases |
| **Event delivery, idempotency, dead-lettering** | The outbox substrate | [402](402-epic-f-workflow.md) §3 |
| **A notification, or delivery** | **[ADR-0040](adr/0040-notifications.md)** | *"They are different products and must never converge"* |
| **An attention or priority model** | ADR-0040: *"attention is derived and never stored"* | ⚠️ **M11 *"owns prioritisation/ranking"* per `04-modules.md`** — §7 ❓2 |
| **A workflow or stage change** | `opportunity_engine` — **the only module that records commitment** | *Intelligence suggests; humans commit* |
| **A per-entity feed** | `timeline` — already a listed consumer | |
| **A prompt registry or release gate** | Fingerprinted manifests · `require_model` | |

### Surface rather than build

**Everything a recommendation would cite already exists and is already surfaced** — the score, its ledger, the signals, the business events, the opportunity. **M11 adds the sentence *"so do this"*, and a lifecycle for whether anyone did.** That is a genuinely small module sitting behind two large blockers.

---

## 4 · Domain

| | |
|---|---|
| **Aggregate** | **`Recommendation`** — workspace · subject · action · rationale reference · **status** · created-from |
| **Value objects** | `Action` · `Priority` *(❓2)* · `RecommendationStatus` |
| **Status** | `OPEN → ACTED_ON \| DISMISSED \| EXPIRED`. **`ACTED_ON` and `DISMISSED` require an `actor_id`; `EXPIRED` is the only machine-authored transition** |
| **Events** | `recommendation.created` · `recommendation.status_changed` — **both already catalogued with their payloads** |
| **Consumes** | `ai_reasoning.completed` |
| **Owns** | Generation rules · ranking · lifecycle |
| **Never owns** | The reasoning · delivery · presentation · any action |

**`EXPIRED` as the sole machine-authored transition is the direct analogue of `MACHINE_AUTHORED = {TRACKING}`**, and it should be enforced the same way — by construction, raising when an actor is absent. **A recommendation quietly marked *acted-on* by a machine would be the product claiming a person did something.**

> **Events carry identity and counts, never prose.** `ai_platform/domain/events.py`: *"Putting a paragraph of model output in an envelope would make every wording change an event-contract change, and would copy customer-visible text into a queue whose retention nobody has reasoned about."* **`recommendation.created`'s catalogued payload is already correct** — `recommendation_id`, `opportunity_id`, `action`, `priority`.

---

## 5 · Workflows

**Seller:** a recommendation appears on the account or opportunity it concerns, **citing the reasoning that produced it** → the seller acts, dismisses, or ignores → **dismissal is signal, and `recommendation.status_changed` already lists `Signal Engine (feedback loop)` as a consumer.**

> **The feedback loop is catalogued and should stay unbuilt in v1 — *deferred, not dropped*, and the distinction matters.** A dismissal-weighted signal model is a second scoring system learned from behaviour, in a repository whose scoring is deliberately a **reviewed artifact** a customer can argue with. **Recording dismissals is v1; learning from them is a decision, not a slice.**
>
> ⚠️ **Corrected on roadmap-integrity review:** [PRODUCT_DIFFERENTIATORS.md](../../PRODUCT_DIFFERENTIATORS.md) names the ***Self-Improving Recommendation Loop*** — *"`recommendation.status_changed` feeds back into Signal Engine… **near-impossible to copy quickly**"* — and calls it ***"the mechanism behind the Product Flywheel"***, rated **High, long-term.** **This package initially read as though it were an optional extra. It is a governing differentiator.** The v1 deferral stands on its architectural merits; **what changes is that `recommendation.status_changed` must be designed as the flywheel's input from the first commit**, not retrofitted — which is free if known, and expensive if not.

**Failure paths:** reasoning fails → **no recommendation, and no placeholder** · a citation does not resolve → **refuse to show it**, per ADR-0031's *validates, never repairs* · the opportunity closes → **outstanding recommendations expire**, machine-authored and correct · **the same conclusion recurs → supersede rather than duplicate**, exactly as `signal.superseded` and `business_event.superseded` already do.

---

## 6 · Phases

| # | Phase | Delivers | Effort | Depends on |
|---|---|---|---|---|
| **0** | **Unblock the input** | **`reasoning@1` released** | **S** | **[404](404-epic-g-copilot.md) §1 — not M11's** |
| **1** | **The module and lifecycle** | `Recommendation`, statuses, both events | **M** | Phase 0 |
| **2** | **Generation from reasoning** | A conclusion becomes an action | **L** | Phase 1 |
| **3** | **Surface** | It reaches a seller and can be acted on or dismissed | **M** | Phase 2 · Product Surface |
| **4** | **Ranking** | Order across many | **M** | Phase 3 · **❓2** |
| — | ~~Feedback loop~~ | **Not v1** — §5 | — | — |

> **Phase 0 is not M11's work and is the whole of its critical path.** Preparing M11 further before it clears is preparing a module whose input has never fired. **This package is therefore complete at *Architecture*, not at *READY*** — and saying so is more useful than claiming readiness that a lane would discover is hollow on day one.

---

## 7 · Risks and open questions

| Class | Risk | Mitigation |
|---|---|---|
| **Product** 🔴 | **M11 converges with Notifications or Workflow** | §2 — three modules, three authorships, stated before any code |
| **Product** 🔴 | A machine marks a recommendation *acted-on* | `EXPIRED` is the only machine transition, **by construction** |
| **Architectural** 🟠 | **Ranking becomes a second scoring model** | ❓2 |
| **Architectural** 🟠 | Prose in an event envelope | §4 — identity and counts only |
| **Dependency** 🟠 | **Built against an input that never fires** | **Phase 0 first**, and it is somebody else's |
| **Product** 🟡 | Advice a customer cannot trace | Cite the reasoning; **refuse rather than show an unresolvable citation** |
| **Deployment** 🟡 | **[C-410](../LANE_COORDINATION.md)** — no production-model evaluation | M11 is customer-facing inference by definition |

### Open questions

> **🟡 Upcoming — ❓1 · Is Revenue Intelligence Platform in the roadmap ahead of M11?** `recommendation.created`'s catalogued consumers are **Timeline and RIP**, and RIP does not exist. **Timeline alone is a sufficient v1 consumer**, so this does not block — **but M11 shipping to one of two intended consumers should be a choice rather than a discovery.**

> **🟡 Upcoming — ❓2 · What is a recommendation's priority, and where does it come from?** `04-modules.md` gives M11 *"prioritisation/ranking"*, while ADR-0040 rules **attention is derived and never stored** and ADR-0038 keeps Timeline free of judgement. **Lane C recommends: derive order from the buying score and the reasoning's own confidence, and store no priority.** A stored priority is a second scoring model **in the module least equipped to review it** — the phrase `commercial_profile` and `buying_score_engine` both use against themselves. **Deferrable to phase 4.**

> **Not escalated:** the generation rules' authoring surface *(catalog or code — the catalog pattern is the obvious first answer)* · expiry windows · whether phase 3 is its own screen or a section on the brief.

## 8 · Definition of done

**Done when a seller sees, on the account it concerns, a concrete action Signora suggests — with the reasoning it rests on — and can act on it or dismiss it, and when nothing in the product claims they did either.**

**Gates:** `ACTED_ON` and `DISMISSED` carry an `actor_id`, **enforced by construction** · every recommendation cites resolvable reasoning, **or is not shown** · **no priority is stored** *(❓2)* · events carry identity, never prose · **no delivery, no action, no second explanation** · a recurring conclusion supersedes rather than duplicates.

## 9 · Cross-cutting deltas ([405](405-cross-cutting-concerns.md))

| Concern | Delta | Decision it serves |
|---|---|---|
| **Metric** | **Dismissal rate** | *Is the advice any good?* — **the one number that tells you M11 is working**, and it needs no feedback loop to be worth watching |
| **Metric** | Recommendations created per reasoning completion | *Is generation firing at all?* — the input is the risk |
| **Testing** 🔴 | **Structural: no status transition to `ACTED_ON`/`DISMISSED` without an actor** | The product must never claim a person acted |
| **Testing** | Unresolvable citation → not shown, **exercised** | ADR-0031 cost three releases |
| **Deployment** | **[C-410](../LANE_COORDINATION.md)** applies in full | M11 is customer-facing inference |

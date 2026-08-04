# 402 — Epic F · Workflow automation — implementation preparation

> **Prepared by Lane C — Product Office. No code was written and none should be.** **Every claim verified against source on 2026-08-04.**
>
> ⚠️ **Links to [51-implementation-specifications.md](51-implementation-specifications.md) and [50-product-capability-audit.md](50-product-capability-audit.md) do not resolve on this branch** — both live on `lane-b-commercial-profile` and reach `main` at the next merge. **Everything relied on is quoted inline**, and the event counts below were measured against code on this branch rather than taken from either document.

> **Observability, testing, operations and deployment: [405-cross-cutting-concerns.md](405-cross-cutting-concerns.md)** — written once for every prepared package rather than five times. **Epic F's deltas are in its §6 row.** In short: **Add nothing for delivery** — the outbox, dispatch and dead-letter metrics already cover the substrate this epic reuses. **Matched-but-undelivered is the metric that makes §2's honesty claim true.**

---

## 1 · Two findings, and the second one changes the epic

**Epic F's specification makes a claim, and it is half right.**

> *"The strongest leverage in the audit. **82 catalogued events**, a transactional outbox, ARQ workers, idempotent handlers, dead-lettering and replay — **all built.** What is missing is a way for a customer to express a rule."*

### Finding 1 — the substrate is real, and the number is not

**The infrastructure is exactly as described.** Verified: `event_bus/relay.py` (274 lines) · `dispatch.py` · `idempotency.py` · `dead_letter.py` · `outbox_model.py` · the outbox migration is **`0000`**, the first in the repository · ARQ `WorkerPool`s in `apps/worker/pools.py`. **None of this needs building and none of it should be touched.**

**The event count does not survive checking.**

| | Count | Source |
|---|---|---|
| **Claimed** | **82** | [50-product-capability-audit.md](50-product-capability-audit.md), citing `06-events.md` |
| **Named in `06-events.md`** | **34** distinct event types | `grep` of the catalog document |
| **Actually published in code** | **23** | `event_type: str = "…"` across every module's `public/` and `domain/events.py` |

**Eleven catalogued events have no publisher** — `recommendation.created`, `recommendation.status_changed`, `entity.merged`, `entity.updated`, `entity.superseded`, `opportunity.closed`, `signal.scored`, `provider.health_changed`, `ai.narration_failed`, `ai_reasoning.failed`, `business_event_type.published`.

> **This is good news stated accurately, not a problem.** **Twenty-three real triggers is more than enough for a rule builder**, and a vocabulary of 23 is small enough to be **a reviewed catalog a domain expert owns** rather than something inferred — which is the *least powerful author* rule (`CLAUDE.md` §2) and the pattern the Signal Catalog and the Integrations Catalog both already use.
>
> **The danger is building the trigger list from the document.** A builder offering 82 triggers would advertise **59 that never fire** — precisely the failure `integrations/domain/catalog.py` already refuses with `LIVE_CAPABILITIES`: *"a Connection Center that promised meeting intelligence Signora cannot yet produce would be the product asserting something untrue."* **Epic F needs the same guard, and it exists to be copied.**

### Finding 2 — there is nothing for a rule to do

**F2 is *"a safe action set."* Not one safe action exists today.**

| Candidate action | Status | Evidence |
|---|---|---|
| **Send an email** | **Nothing.** No SMTP, no provider, no mailer anywhere in `backend/` | ADR-0015 is `Accepted` and **unbuilt** |
| **Post to Slack** | **Catalogued and explicitly not live** — `MESSAGE_DELIVERY` is excluded from `LIVE_CAPABILITIES` because *"its consumers are deferred and unbuilt"* | `integrations/domain/catalog.py` |
| **Notify in-product** | **No module.** **[ADR-0040](adr/0040-notifications.md) is `Proposed`**, and names Novu as *"bought · unused on Day One"* | `ls backend/modules/` — no notifications |
| **Write to the CRM** | **Epic E2**, unbuilt, and depends on [E1](401-epic-e1-crm-read.md) | |
| **Change a declaration** — ICP, committee, target accounts | **Built, and must never be a rule's action.** These are *"sentences somebody typed about their own business"*; a rule rewriting a customer's own declaration is the module's central prohibition | `commercial_profile/domain/committee.py` |
| **Transition an opportunity** | **Built** — `TransitionOpportunity` | **A judgement about a deal.** Automating it puts a conclusion in the module least equipped to review it |

> **Epic F has the same shape as [Epic C](400-epic-c-people.md): the expensive half is built and the last cheap step is missing. Here the missing step is not cheap — it is a bounded context.**
>
> **The dependency nobody has recorded: Epic F depends on Notifications (M14a / [ADR-0040](adr/0040-notifications.md)), not on Slack, not on email, not on E2.** ADR-0040 already defines the addressee, the read/dismiss/snooze lifecycle, severity, one row per recipient, and two rules that stop a backfill paging everybody. **That is exactly what a rule's output needs, and it is already designed.**

---

## 2 · The recommendation that makes F independent anyway

**F1 must not build delivery. It publishes an event and stops.**

```
  a catalogued event fires  →  rules are evaluated  →  workflow.rule_matched
                                                              │
                             Notifications, when it exists  ◀──┘  consumes it like any other event
```

**This is the layering principle the repository already holds**, stated in `06-events.md` about the engines above it: *"`signal.generated` is not a claim that anyone should act. How likely a purchase is, which account to prioritise, and what to recommend belong downstream."* **A workflow rule is the same kind of statement: it says a condition was met, never that somebody should be paged.**

**Three consequences, and they are the reason to prefer this over waiting:**

1. **F1 becomes genuinely independent of M14a.** It can be built, tested and certified with no delivery mechanism in existence.
2. **The action set stops being a design problem.** *"Which actions are safe?"* becomes *"which consumers subscribe?"* — and every future action (notification, Slack, CRM write) is a subscriber, not a change to the rule model.
3. **A rule that fires into nothing is visible and honest**, the same way `live_capabilities` is. **The UI can say *"this rule has matched 14 times; you are not being told about it yet."***

> **The alternative — F1 invoking actions directly — makes the workflow module a caller of five other modules, which is the god-module the two-layer split exists to prevent** ([C-025](../LANE_COORDINATION.md) makes exactly this argument about Integrations).

> ⚠️ **A naming collision, found 2026-08-04 and worth ten seconds before it costs more.** **`apps/api/composition/workflow.py` already exists** and means something different: *"composing the **Opportunity Engine's write surface** — progressing an opportunity needs the workflow tables and a membership check, and nothing else at all."* **Two meanings of *workflow*, one repository.** Not a blocker and not worth an ADR; **a lane building `modules/workflow/` will meet this file, and knowing beforehand costs nothing.** [ADR-0034](adr/0034-ubiquitous-language.md) owns naming if it turns out to matter.

---

## 3 · Repository reuse — what must NOT be built

| ❌ Do not build | ✅ Exists as | Consequence |
|---|---|---|
| **Event delivery, retry, ordering** | Outbox (`0000`) · `relay.py` · `dispatch.py` | **The largest duplication available in F** |
| **Idempotency** | `event_bus/idempotency.py` — platform-owned | Double-firing rules; the worst possible bug in this epic |
| **Dead-lettering and replay** | `event_bus/dead_letter.py` | |
| **A worker pool or scheduler** | `apps/worker/pools.py`, ARQ | |
| **An event envelope or schema-evolution scheme** | `event_bus/envelope.py` · `06-events.md` §Schema Evolution | |
| **A trigger vocabulary by inference** | **The catalog pattern** — Signal Catalog, Integrations Catalog | §1 — and a `LIVE_TRIGGERS` guard is the copy that matters |
| **A notification, its lifecycle, or delivery** | **[ADR-0040](adr/0040-notifications.md)** designs all of it | Two notification products that must never converge |
| **An attention or priority model** | **Deliberately absent.** ADR-0040: *"attention is derived and never stored"* | |
| **Audit of what fired** | `timeline` — a projection that owns none of its data | |

### Surface rather than build

**`business_event.detected`, `signal.generated`, `buying_score.updated` and `opportunity.created` are the four events a customer would actually write rules about, and all four publish today.** A v1 builder over those four plus the entity events is **most of the product value at a fraction of the scope.**

---

## 4 · Technical research — how to express a rule

**A customer-authored rule is code a customer wrote, running inside Signora.** The question is what shape it takes.

| | Approach | Assessment |
|---|---|---|
| **A** ✅ | **A structured condition tree, owned as a domain type** — trigger + typed predicates over the event's own fields, composed with `all` / `any` | **Recommended.** No dependency (no 🔴 ADR), no evaluator to sandbox, **diffable and reviewable**, and the versioning story is the one `commercial_profile` already uses for declarations. **A rule becomes data, and data is what this repository is good at** |
| **B** | **CEL** (Google Common Expression Language) — designed for exactly this, non-Turing-complete, sandboxed by design | **The strongest rival, and rejected on cost not merit.** A new project dependency is 🔴 and needs its own ADR; the Python implementations are markedly less mature than the Go/C++ ones; and **a string expression is not diffable in a way a customer can review** |
| **C** | **JSONLogic** — small, declarative, widely used | Lighter than CEL, **and it accepts arbitrarily nested logic no domain type constrains.** The permissiveness is the problem: it can express conditions the pipeline cannot answer |
| **D** | **A general expression language** — Lua, Starlark, sandboxed Python | **Rejected outright.** Turing-complete customer code inside the request path is an operational and security surface this repository has no need to acquire |

> **Option A follows a rule the repository already enforces against itself.** `signal_engine/domain/rules.py` is parsed as a syntax tree by a Security Invariant that **fails on any numeric literal in a comparison other than `0` or `1`** — because *"anything else is a claim about the world somebody must be able to argue with."* **A customer-authored expression string cannot be audited that way; a structured condition tree can be inspected field by field.**

**Non-negotiables for whichever is chosen:** evaluation is **pure** — no I/O, no clock, no network — matching `signal_engine`'s strategies · **bounded** — no unbounded iteration or recursion · **workspace-scoped** — a rule can never observe another workspace's events · **versioned** — a rule that fired must be reconstructable, which is `commercial_profile`'s declaration model exactly.

**Rate and loop safety, learned from the category:** a rule must not be able to trigger itself. **`workflow.rule_matched` must not be a valid trigger** — the cheapest possible guard, and it must be in the type rather than in a check.

---

## 5 · Domain and phases

**A new bounded context — `workflow` — and it is genuinely new.** 🔴 under §6, which is why **[ADR-0402](adr/0402-a-rule-is-data.md)** is drafted.

| | |
|---|---|
| **Aggregate** | **`Rule`** — workspace, trigger, condition tree, enabled, **version** |
| **Value objects** | `Trigger` (a catalogued event key) · `Condition` · `Predicate` |
| **Commands** | `CreateRule` · `ReviseRule` · `EnableRule` · `DisableRule` |
| **Events** | **`workflow.rule_matched`** — and nothing else on day one |
| **Read models** | A customer's rules · **match history** — *"this fired 14 times"* |
| **Consumes** | The catalogued events, via the existing subscription mechanism |
| **Owns** | **No delivery, no action, no notification, no priority** |

| # | Phase | Delivers | Effort | Depends on |
|---|---|---|---|---|
| **1** | **The trigger catalog** | A reviewed table of **live** triggers, with a `LIVE_TRIGGERS` guard | **S** | — |
| **2** | **The rule model** | `Rule`, conditions, versioning, evaluation. **No UI, no firing** | **L** | **[ADR-0402](adr/0402-a-rule-is-data.md)** |
| **3** | **Evaluation and `rule_matched`** | Rules run against live events; matches are recorded | **M** | Phase 2 |
| **4** | **The builder** | The customer expresses a rule | **L** | Phase 3 · **Lane A** — Product Surface |
| **5** | **Delivery** | A match reaches a person | **M** | **Notifications / [ADR-0040](adr/0040-notifications.md)** |

> **Phases 1–3 are one lane's, back-end only, and depend on nothing outside the repository.** **Phase 4 is the only cross-lane crossing** and it is a screen. **Phase 5 is somebody else's epic** and F should not wait for it.

**Stop-after-any-phase:** after phase 3 the product has rules that match and tell nobody — **visible, honest, and immediately useful as evidence for whether the trigger vocabulary is right before a builder is designed around it.**

---

## 6 · Risks

| Class | Risk | Mitigation |
|---|---|---|
| **Product** 🔴 | **A builder offering 82 triggers, 59 of which never fire** | §1 — **`LIVE_TRIGGERS`, copied from `LIVE_CAPABILITIES`** |
| **Architectural** 🔴 | **`workflow` calls five modules to perform actions** and becomes a god-module | §2 — **publish an event and stop** |
| **Architectural** 🟠 | A rule mutates a customer declaration | **Forbid in the type.** Declarations are the customer's sentences |
| **Security** 🟠 | Customer-authored logic in the request path | §4 — **structured tree, pure, bounded, no expression language** |
| **Operational** 🟠 | **A rule triggers itself** | `workflow.rule_matched` is **not a valid trigger**, enforced in the type |
| **Operational** 🟠 | A backfill fires every rule at once | **ADR-0040 already solved this** for notifications — *"two rules that keep a backfill from paging everyone."* **Reuse the reasoning** |
| **Performance** 🟡 | Every event evaluated against every rule | Index by trigger; **bounded conditions make the cost predictable.** Measure first |
| **Product** 🟡 | **Rules that match and reach nobody**, if phase 5 never comes | **Honest by construction** — and the reason to sequence M14a |
| **Repository** 🟡 | 2 of 9 consumers wired ([TASK-901](../BACKLOG.md)) | `workflow` would be the third. **Sequence after, or accept it** |

---

## 7 · Definition of done, and open questions

**Done when a customer can express a condition over something Signora already knows, and see it match — without Signora claiming anybody was told.**

**Gates:** every offered trigger publishes today, guarded structurally · a rule is **data, versioned, diffable, reconstructable** · evaluation is **pure and workspace-scoped**, asserted by test · `workflow` **publishes one event and calls no module** · **no rule can trigger itself** · no second outbox, idempotency, dead-letter, worker pool or notification model.

### Open questions

> **🟡 Upcoming — is Notifications (M14a) sequenced before Epic F's phase 5?** Not a blocker for phases 1–4, and **the answer decides whether F ships useful or merely correct.** [ADR-0040](adr/0040-notifications.md) is `Proposed` and already designs everything phase 5 needs. **Lane C's recommendation: ratify ADR-0040 and build M14a before F reaches phase 5** — F is then pure gain and needs no delivery decisions of its own.

> **🟢 Background — is the 82-event figure worth correcting at source?** [50-product-capability-audit.md](50-product-capability-audit.md) reports 82 citing a document naming 34, of which 23 publish. **It is a headline number in a document lanes read for scope.** Not raised as a coordination item — **the audit is a dated record and the correction belongs in whatever supersedes it**, but a lane quoting 82 into a customer-facing builder would be the second-order cost.

**Not escalated, because engineering can answer them:** how conditions are indexed per trigger · whether match history is its own table or a timeline projection · the builder's interaction model. **None needs a product ruling, and each has an obvious first answer.**

# ADR-0402: A rule is data, and it publishes one event

## Status

**PRODUCT OWNER APPROVED — 2026-08-04.** ⚠️ **Not yet on `origin/integration`** — this file does not exist there. **The ruling is authoritative; the repository does not yet record it.** A lane may act on it only once QE has merged this branch ([`PRODUCT_OFFICE.md`](../../PRODUCT_OFFICE.md) §11c). Drafted by Lane C — Product Office. **Epic F is unblocked from a Product Office perspective.**

> **Phases 1–4 depend on nothing unbuilt**, which is what this ADR was written to achieve: §2 makes `workflow` publish an event rather than call a notifier, so **Notifications stops being a blocker and becomes a subscriber.** ❓1 remains a phase-5 sequencing question and blocks nothing.

**Complete: five alternatives assessed, one recommended, no unresolved alternative.** Its two open questions are downstream — ❓1 affects phase 5 only, ❓2 is engineering's. **Phases 1–4 depend on nothing unbuilt.**

> Prepared ahead of allocation so the lane that owns [Epic F](../402-epic-f-workflow.md) inherits these decisions rather than making them while writing the first evaluator. **An ADR is required here and is not being manufactured: `workflow` is a new bounded context, which is 🔴 under `CLAUDE.md` §6.**

## Context

**Epic F asks for *"a way for a customer to express a rule"* over events the platform already publishes.** The substrate is real and verified — a transactional outbox (`migrations/versions/0000_*`), a relay, dispatch, platform-owned idempotency, dead-lettering and ARQ worker pools. **None of it needs building.**

**Two facts change what the epic is, and neither is in its specification** ([402-epic-f-workflow.md](../402-epic-f-workflow.md) §1):

**First, the trigger vocabulary is 23, not 82.** The audit reports 82 citing `06-events.md`; that document names **34** distinct event types; **23 have a publisher in code.** A builder offering the catalogued set would advertise triggers that never fire.

**Second, there is no safe action.** No email exists anywhere in the backend; `MESSAGE_DELIVERY` is explicitly excluded from `LIVE_CAPABILITIES` because its consumers are unbuilt; **Notifications is [ADR-0040](0040-notifications.md), `Proposed`, with no module**; CRM write-back is E2. The only built write operations are **customer declarations** — which a rule must never rewrite, because they are *"sentences somebody typed about their own business"* — and `TransitionOpportunity`, which is a judgement about a deal.

> **So the epic's two open ends are: what a rule *is*, and what it is allowed to *do*.** This ADR answers both, and the second answer is what lets Epic F proceed without waiting for a module that does not exist.

**What the architecture already fixes and this ADR does not reopen:** event delivery, ordering, idempotency, dead-lettering and replay · the event envelope and schema evolution · the layering principle that a producer never asserts anyone should act · the catalog pattern for reviewed static knowledge · notification lifecycle and delivery ([ADR-0040](0040-notifications.md)).

## Decision

### 1 · A rule is data, never an expression

> **A rule is a trigger plus a structured condition tree over the triggering event's own fields — a domain type, versioned like a declaration.** Not a string, not an embedded language, not customer code.

**Evaluation is pure — no I/O, no clock, no network — bounded, and workspace-scoped**, matching `signal_engine`'s detection strategies exactly and for the same reason: *"the same evidence yields the same hypothesis on every machine and in any processing order."*

**The alternative this rejects is the popular one.** CEL, JSONLogic and sandboxed scripting all exist to solve this, and each is a new project dependency (🔴, its own ADR) that buys expressiveness the pipeline cannot use. **The deciding argument is auditability, and the repository already made it against itself**: `signal_engine/domain/rules.py` is parsed as a syntax tree by a Security Invariant that fails on any numeric literal in a comparison other than `0` or `1`, *"because anything else is a claim about the world somebody must be able to argue with."* **A customer's expression string cannot be inspected that way. A condition tree can be, field by field.** Full comparison in [402-epic-f-workflow.md](../402-epic-f-workflow.md) §4.

### 2 · A rule publishes `workflow.rule_matched`, and calls nothing

> **`workflow` performs no action, delivers no message, and invokes no other module.** A match is an event. Whoever should act subscribes.

**This is the layering principle applied one level up.** `06-events.md` already states it of the engines below: *"`signal.generated` is not a claim that anyone should act."* **A rule matching is the same kind of statement** — a condition was met, and nothing follows from that except to whoever chose to listen.

**Three consequences, and the first is why Epic F is buildable now:**

1. **F is independent of Notifications.** Phases 1–4 need no delivery mechanism to exist. **A module that does not exist stops being a blocker and becomes a subscriber.**
2. **"Which actions are safe?" stops being a design question** and becomes *"which consumers subscribe?"* — every future action is additive.
3. **`workflow` cannot become a god-module**, which is the outcome a module calling five others reaches. [C-025](../../LANE_COORDINATION.md) makes exactly this argument about Integrations, and it was right.

**A rule that matches and reaches nobody is honest and must be visible** — *"this has matched 14 times; you are not being told about it yet"* — the same discipline `live_capabilities` already enforces on the Connection Center.

### 3 · The trigger catalog is reviewed, and refuses what cannot fire

**Triggers are a table a domain expert owns**, like the Signal Catalog and the Integrations Catalog. **A `LIVE_TRIGGERS` guard — copied from `LIVE_CAPABILITIES` — makes it structurally impossible to offer a trigger with no publisher.** `integrations/domain/catalog.py` states the rule this borrows: *"a Connection Center that promised meeting intelligence Signora cannot yet produce would be the product asserting something untrue."*

**`workflow.rule_matched` is not a valid trigger.** A rule cannot cause a rule. **Enforced in the type, not in a check** — the cheapest guard available and the most expensive omission.

### 4 · A rule may not write to a customer's declarations

**ICP, buying committee, commercial focus and target accounts are the customer's own statements about their business.** `commercial_profile` is built on that and refuses to compute over them. **A rule rewriting one would make the customer's declaration something Signora inferred**, which is the failure that module exists to prevent.

## Alternatives considered

| | Option | Why not |
|---|---|---|
| **A** ✅ | **Condition tree as data; publish one event; no actions** | **Recommended.** No dependency, auditable, versioned like a declaration, **and independent of every unbuilt module** |
| **B** | **Rules invoke actions directly** | Makes `workflow` a caller of five modules, **couples F to Notifications/E2/Slack**, and reintroduces *"which actions are safe?"* as a permanent design surface |
| **C** | **CEL or JSONLogic** | **Strongest rival, rejected on cost.** New 🔴 dependency; expressiveness the pipeline cannot use; **a string is not reviewable the way the repository reviews its own rules** |
| **D** | **Rules inside `signal_engine`** | That module produces *hypotheses grounded in evidence*, from a reviewed catalog. **A customer's arbitrary condition is not a hypothesis**, and mixing them puts customer-authored logic inside the scored intelligence path |
| **E** | **Wait for Notifications (M14a)** | **The default if this ADR is not taken**, and it costs Epic F entirely — F would sit blocked behind a `Proposed` ADR for a module nobody has scheduled |

## Consequences

**Positive.** **Epic F becomes buildable today** — phases 1–4 depend on nothing unbuilt. Every future action is a subscriber rather than a change. Rules are diffable, versioned and reconstructable, so *"why did this fire?"* is answerable. **No new dependency, so no second 🔴.**

**Negative.** A condition tree is **less expressive than an expression language**, and the first customer request Signora cannot express will feel like the wrong call. **Stated deliberately: the trigger for revisiting is a real customer condition the tree cannot represent, not a hypothetical one.** And a rule that matches and reaches nobody **needs Notifications to become useful** — F ships correct before it ships valuable, and §2 makes that visible rather than hidden.

**Neutral.** One new bounded context. One new event. **No change to any existing module.**

## Open questions

> **🟡 Is Notifications (M14a) sequenced before Epic F's phase 5?** Not a blocker for phases 1–4. **Lane C recommends ratifying [ADR-0040](0040-notifications.md) and building M14a before F reaches phase 5**, at which point F is pure gain and needs no delivery decision of its own.

> **🟢 Should the condition vocabulary be per-trigger or shared?** A shared predicate set is simpler; per-trigger typing is safer. **Engineering can answer this**, and it is not escalated.

## Compliance

**`Proposed`. Nothing to comply with yet.** On ratification: **evaluation is pure and bounded**, assertable the way `signal_engine`'s strategies already are · **`workflow` imports no other module's application layer** — a structural test, and the cheapest guard in this decision · **`workflow.rule_matched` is not in the trigger catalog** · **every offered trigger has a publisher**, asserted against the code rather than the catalog document · **no rule may target a declaration command.**

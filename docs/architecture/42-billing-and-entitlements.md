# M14b — Billing, Analytics & Feature Flags: domain discovery

> **Status: discovery. No code has been written, and none will be until the ruling in [C-200](../LANE_COORDINATION.md) lands.**
>
> Assigned to Lane A by the product owner on 2026-08-02, with the explicit instruction *"do not begin by writing code — begin by understanding the domain. Do not invent a module. Discover it."* This document is that discovery, and it ends in a question rather than a plan because **the answer is a bounded-context decision, which is 🔴 and no lane's** (`CLAUDE.md` §20e).

---

## 1 · What the repository already believes about M14b

**Everything below was read out of the repository. Nothing is inferred, and every claim is cited.**

### The three technology decisions are already ratified — and none is implemented

| | ADR | Status | In the codebase |
|---|---|---|---|
| **Billing** | [ADR-0016](adr/0016-billing.md) — **Stripe** | Accepted | **Nothing.** No SDK, no dependency, no adapter, no table |
| **Analytics** | [ADR-0019](adr/0019-analytics.md) — **PostHog** | Accepted | **Nothing** |
| **Feature flags** | [ADR-0020](adr/0020-feature-flags.md) — **Flagsmith** | Accepted | **Nothing** |

**There are no open technology choices here** (`CLAUDE.md` preamble), and adopting each one is a dependency addition that the ADRs have already authorised. **What is missing is not a vendor. It is a domain.**

### All three ADRs place their adapter in a directory that does not exist

Each names `backend/platform/bought_infra_adapters/` as the isolation point. **That path has never existed**, and `signora_platform/` was frozen at M1.3A without it.

**This is the third instance of a pattern `CLAUDE.md` §6 already records as learned twice:** [15-project-structure.md](15-project-structure.md) placed both the Provider Port and the AI Provider Port in platform packages that were never built, and the implementation put each in its **owning module** both times. The ratified rule that came out of it:

> **A port belongs to the module that owns the language it represents.** It is not shared platform infrastructure, and **it never moves to `signora_platform/` because more than one module consumes it.**

**So the ADRs' migration strategies are still satisfiable and their stated path is not.** A Stripe adapter belongs to whichever module owns commercial language — which is the question this document is about.

### The roadmap asserts a bounded context that `04-modules.md` does not contain

[IMPLEMENTATION_ROADMAP.md §5b](../../IMPLEMENTATION_ROADMAP.md) justifies splitting M14 into M14a and M14b with: *"each has its own bounded context, so splitting is more honest than a combined milestone whose halves ship weeks apart."*

**[04-modules.md](04-modules.md) ratifies thirteen core modules plus one foundational platform module. None of them is billing, entitlements, analytics or flags.** The roadmap's justification for the split rests on a bounded context the module reference does not define.

### M14b has no scope section anywhere

**Two table rows in [IMPLEMENTATION_ROADMAP.md](../../IMPLEMENTATION_ROADMAP.md) — position 19, `~3–4 ew` — and nothing else.** No demo scenario, no demo checklist, no acceptance criteria, no task ids, no entry condition. Every other milestone in that document has all of them.

**This is the same shape as [C-020](../LANE_COORDINATION.md)** (*M7 has no scope, and Timeline has no design*) **and [C-023](../LANE_COORDINATION.md)** (*M13 is ratified architecture, not an executable milestone*), both found the same way and both still open.

### Workspace & Tenancy is told it does not own billing, and owns no lifecycle either

[04-modules.md](04-modules.md) is explicit: Workspace & Tenancy **does not own** *"billing/subscription state (Stripe, [ADR-0016](adr/0016-billing.md))"*. It **does** own *"workspace lifecycle, workspace-level settings"*.

**Neither exists.** `Workspace` in [`backend/modules/workspace_tenancy/domain/entities.py`](../../backend/modules/workspace_tenancy/domain/entities.py) has `id`, `name`, audit columns and a single `create` classmethod. **There is no lifecycle to attach a plan to, no settings, no state, no suspension, no trial, and no deletion.**

And [ADR-0016](adr/0016-billing.md)'s own consequence says *"Workspace & Tenancy tracks subscription/plan state as a reference to Stripe's subscription object"* — which is in **tension with 04-modules' "does not own"**, not contradiction: one is talking about the system of record, the other about who holds the foreign key. **Both readings are defensible, and nobody has chosen.**

### `plan` was deliberately removed from the one module that used the word

[PRODUCT_ROADMAP.md](../../PRODUCT_ROADMAP.md)'s consistency review records that [04-modules.md](04-modules.md) once said Provider Platform owns *"which providers are enabled **per workspace/plan**"*, and that it was **rewritten** because it was *"ambiguous between Signora's commercial packaging and a customer toggle."*

**The ambiguity was resolved by deleting the word, not by giving packaging an owner.** That owner is still unnamed, and it is precisely what M14b would be.

### Usage is already measured, per workspace, and has been since M8

**This is the most important existing asset, and it is easy to miss.** Migration `0015` created `ai_inference`: per-workspace, RLS-enforced, forced, recording `input_tokens`, `output_tokens`, `latency_ms`, `retries`, `outcome`, `requested_model`, `served_model` and `vendor` — **on every call, failures included.**

**And it deliberately records no money.** [`usage.py`](../../backend/modules/ai_platform/domain/usage.py) and [28-ai-platform.md](28-ai-platform.md) AC-72 are unambiguous:

> **The port reports usage, never money** — no currency-typed field exists on any inference record or result. *"Pricing is a table applied outside the port, at reporting time, over stored usage — so a price change re-prices history correctly."*

**That is not a gap. It is half of usage-based billing already built, and built correctly.** What is missing is the *other* half: the pricing table, and an owner for it.

### R-01 says the missing half is a product decision, and says so by name

[16-architecture-risks.md](16-architecture-risks.md) R-01 — **AI Vendor Cost Exposure Without Budget Governance**, Severity High, Likelihood High:

> *"Spend is now measurable… Governing spend is still open, and deliberately so: it needs a **pricing table**, a **budget owner**, and a **policy on what happens when a workspace exceeds one**, which is a **product decision rather than a substrate one**."*

**Three named prerequisites, all three of them M14b's, and the risk register has been waiting for this milestone without saying its number.**

### Spend governance is currently roadmapped *after* M14b, at M15

M15's scope line reads *"load testing, SOC 2, PII, **spend governance**"* — position 21, two milestones after M14b. **That is a sequencing question rather than a defect**: it is defensible that M14b builds the pricing table and M15 builds the ceiling that reads it. It is also defensible that they are one thing. **Named here so the M14b scope decision is made knowing M15 already claims a piece of it.**

### Nothing anywhere expresses a limit, a quota, an entitlement or a plan

Searched across `backend/`, `frontend/`, `policy.csv` and every architecture document. **No entitlement concept. No quota. No usage limit. No trial. No plan tier. No seat count.** [`policy.csv`](../../backend/signora_platform/authorization/policies/policy.csv) carries `owner` and `member` and no third dimension.

**The absence is total, which is good news:** there is no half-built version to reconcile with, and no wrong model already teaching people the wrong thing.

### One product-strategy constraint that bears directly on the pricing model

[PRODUCT_DIFFERENTIATORS.md](../../PRODUCT_DIFFERENTIATORS.md): *"the flywheel is powered by Recommendation Engine's feedback loop and Provider Platform's expanding coverage, **not by raw usage or seat count**."*

**That is a statement about what drives value, not a prohibition on how to charge** — but it is the only sentence in the repository that touches pricing philosophy, and a plan model built purely on seats would be selling something the product's own strategy says is not where the value is.

---

## 2 · Challenging the architecture

**The product owner asked six questions. Answering them honestly splits M14b into three things that do not belong together.**

### Q: Are these one module or several?

> **Three concerns, three different owners of truth, and only one of them is a bounded context.**

| | System of record | What it is | Bounded context? |
|---|---|---|---|
| **Billing & entitlements** | **Stripe** for money; **Signora** for what a customer is allowed to do | A commercial agreement with the customer, which the product must **explain** | **Yes** — aggregates, invariants, customer language, events, an audit obligation |
| **Feature flags** | **Flagsmith** | **Signora's own operational configuration** — [ADR-0020](adr/0020-feature-flags.md) says so in exactly those words: *"flags themselves are not RLS-enforced tenant data (they are Signora's own operational configuration, not customer data)"* | **No.** No aggregate, no invariant, no customer-facing vocabulary |
| **Product analytics** | **PostHog** | Telemetry about how the product is used. [ADR-0019](adr/0019-analytics.md): *"integrated at the frontend/API boundary, **not woven into domain logic**"* | **No.** Explicitly an edge integration |

**So the recommendation is: one module and two integrations.** Not three modules, and not one.

### Q: Does Billing deserve its own bounded context? — **Yes, and it is not Workspace & Tenancy's**

**Three tests, and it passes all three.**

**It has invariants nothing else can hold.** *A workspace cannot exceed the limits of the plan it is on. A trial ends. A downgrade cannot silently destroy data the higher plan created.* None of these is a tenancy rule, and Workspace & Tenancy has no vocabulary for any of them.

**Its language is nobody else's.** Plan, entitlement, allowance, trial, seat, overage, invoice, dunning. **Putting these on the Workspace aggregate would give the tenancy root a commercial vocabulary**, and the tenancy root is imported by every module in the system — which is precisely the substrate-erosion failure `CLAUDE.md` §2 names: *"when something a module needs starts accumulating in the substrate every module already imports, the substrate has stopped being a substrate."*

**Its lifecycle is independent.** A subscription changes on Stripe's clock — renewals, failures, dunning, cancellations — and a workspace changes on the customer's. Modelling them as one aggregate would force a webhook from a payment processor into the transaction that adds a team member.

### Q: Should Feature Flags belong here? — **No, and conflating them with entitlements is the mistake to avoid**

**This is the single most important finding in this document.**

> **A feature flag answers *"is this built and switched on?"* An entitlement answers *"is this customer allowed?"* They look identical at the call site and they are opposites everywhere else.**

| | **Feature flag** | **Entitlement** |
|---|---|---|
| **Whose state** | Signora's | **The customer's** |
| **Why it is off** | We are still rolling it out | **You are not paying for it** |
| **May a customer see the reason?** | No — it is internal | **Yes, and it must be explainable** |
| **Audit obligation** | None | **Who changed the plan, when, and what it cost** |
| **Where it lives** | A vendor console | **A workspace-owned, RLS-enforced table** |
| **Failure mode when wrong** | A feature appears early | **A customer is billed for something they cannot use, or uses something they have not bought** |

**Implementing entitlements in Flagsmith would put a customer's commercial rights in a vendor's operational console** — no RLS, no audit trail, no `workspace_id`, and no way to answer *"who changed our plan?"*. **That is a commercial-trust defect, not a shortcut**, and it is exactly what the product owner's *"customers must never be surprised by why access changed"* forbids.

**Flags stay a bought-infrastructure port**, reached through an adapter, used for rollout and kill switches. **They are never the source of an entitlement decision.**

### Q: Should Analytics belong here? — **No**

[ADR-0019](adr/0019-analytics.md) already rules on this twice: analytics is *"distinct from Signora's own domain analytics"*, and building it on the existing event bus was **rejected** because *"repurposing it for product analytics would conflate two different concerns with different retention, PII, and query-pattern needs."*

**Analytics has no aggregate and no invariant.** It is an SDK at the edge with a PII obligation. **Bundling it into a billing module would attach a data-classification problem to a commercial one for no reason beyond both appearing in the same roadmap row.**

**One genuine connection exists and should not be mistaken for module membership:** *feature adoption* is an analytics question that a plan-upgrade conversation reads. That is a reporting join, not a shared boundary.

### Q: What language belongs in each? — the customer's, and it is already ruled

[ADR-0034](adr/0034-ubiquitous-language.md) binds: **the translation lives at the frontend edge and never travels inward.** Applied here:

| The customer says | The platform says |
|---|---|
| **Plan · What you get · Your usage · Limit · Trial · Upgrade · Downgrade · Invoice · Seats** | `subscription`, `entitlement`, `allowance`, `quota`, `grant`, `stripe_subscription_id`, `billing_period` |
| **Organization** | `workspace` |

**Two words are deliberately identical on both sides — `Plan` and `Usage`** — for the same reason `Signal` and `Opportunity` are: a salesperson uses both unprompted about their own job, which is ADR-0034's stated test.

**And one phrase must never reach a screen: *"entitlement".*** Nobody says *"I do not have the entitlement"*. They say ***"that is not on our plan."***

### Q: What belongs somewhere else?

| | Where it belongs | Why |
|---|---|---|
| **Seat counting** | **Workspace & Tenancy** produces the number; billing *reads* it | Membership is already its aggregate. A billing module counting memberships would be reading another module's truth |
| **AI usage facts** | **AI Platform**, unchanged | `ai_inference` is operational history and stays there. Billing reads usage through a port; **it never gets a currency column on somebody else's table** (AC-72) |
| **Authorization** | **Casbin**, unchanged | An entitlement decides *what the plan includes*; Casbin decides *what this person may do*. **Both apply, and neither replaces the other** — a member on an unlimited plan still cannot change it |
| **Spend ceilings** | **Open** — M15 currently claims *spend governance* | See §1. The pricing table is M14b's; whether the ceiling is too needs a ruling |

---

## 3 · The shape that would follow, if the recommendation is accepted

**Not a plan. A demonstration that the recommended shape is buildable, and that it absorbs the long list the product owner asked it to survive.**

### Every field placed by the least-powerful-author rule

`CLAUDE.md` §2's decision rule maps this domain unusually cleanly, which is itself evidence the boundary is drawn in the right place.

| Field | Least powerful author capable of getting it right |
|---|---|
| **When a plan changed** | **The database.** `DEFAULT now()` |
| **What a customer is entitled to** | **Derived** from the plan they are on. **Never stored** — *"truth has exactly one authoritative representation; everything else derives from it"* |
| **What they have used** | **Derived** from `ai_inference` and membership counts. Never a running total maintained by hand |
| **Which plan they are on** | **Customer configuration** — irreplaceable, versioned, immutable per change |
| **What a plan contains** | **A reviewed repository artifact**, like the signal catalog. A domain expert signs it, a diff shows the change |
| **What it costs** | **A pricing table applied at reporting time**, exactly as AC-72 already requires |
| **Whether a limit was reached** | **Computed** from the two above. **Never a stored boolean** — the same reasoning that makes `evidence_state` derived |
| **Anything at all** | **Never AI.** Nothing here requires inference |

**A stored entitlement is a defect waiting for the plan and the entitlement to disagree**, and the disagreement always surfaces as a customer being denied something they are paying for.

### Commercial trust, expressed as an architecture rather than a promise

The product owner's additional responsibility — *customers must never be surprised* — has a concrete form the repository already knows:

> **An entitlement decision carries its reason the way a `BuyingScore` carries its `trigger`.**

Not *"unavailable"*. **"Not on the Team plan"** · **"You have used 500 of 500 this month — resets 1 September"** · **"Your trial ended on 14 August"**. The reason is **derived from the same data as the decision**, so it can never drift from it — and it is never a second string somebody maintains beside the check.

**And every plan change is an immutable record naming its actor**, because *"who changed our plan?"* is one of the questions the product owner listed and it is unanswerable from a mutable row. `next_state` demanding an `actor_id` with no default is the pattern already in the repository.

### The customer questions, mapped

| The customer asks | Answered from |
|---|---|
| *Which plan am I on?* | The plan record |
| *What features do I have?* | Derived from the plan's catalog entry |
| *Why is this feature unavailable?* | The **reason** on the derived decision |
| *Who changed our plan?* | The immutable change record's actor |
| *What usage counts toward billing?* | `ai_inference` + membership, through a read port |
| *What limits are we approaching?* | Derived usage against derived allowance |
| *What happens if we upgrade / downgrade?* | A **preview** computed by the same derivation, against a different plan |
| *What trial do we have remaining?* | The plan record's period |
| *Why was this account limited?* | The same reason, retained |

**Eight of nine are derivations over two stored facts** — which plan, and what happened. **That is what makes them explainable**, and it is the whole argument for deriving rather than storing.

### The several-years list, tested — not built

**None of this is implemented, and the test is only whether today's shape would absorb it without redesign.**

| | Absorbed by |
|---|---|
| **Multiple tiers · promotional plans · grandfathered pricing · custom enterprise plans** | The plan is a **reviewed catalog artifact, versioned and immutable**. A grandfathered customer is on an older version — which is how prompts, taxonomies and the commercial profile already work |
| **Seat-based · usage-based · hybrid** | An allowance is a **derivation over a measured quantity**. Seats and tokens are two quantities; nothing structural distinguishes them |
| **Trials** | A plan record with a period. **Not a boolean on the workspace** |
| **Subscriptions · invoices · payment providers · currencies · taxation** | **Stripe's, per [ADR-0016](adr/0016-billing.md)**, behind an adapter. Signora holds a reference and never re-implements proration or dunning |
| **Enterprise contracts · organization-level billing · resellers · partner licensing** | **The one that does not fit today, and it is honest to say so.** All four need a **billing entity above the workspace**, and no such concept exists anywhere in the architecture. It is *addable* — a plan would reference it instead of a workspace — but it is a real boundary change, not an absorption |
| **Delegated billing administrators** | A Casbin role, not a new concept |
| **Usage analytics · feature adoption · experimentation · A/B testing** | **PostHog and Flagsmith, at the edge.** Deliberately outside the module |
| **Audit history** | Immutable change records, which the architecture defaults to already |

**Stating the one that does not fit is the point of running the exercise.** A design that absorbed all twenty-three would mean the test was not applied.

---

## 4 · What is blocked, and why no code follows this document

**Every route into implementation crosses a 🔴 boundary.**

| To build | Needs | Whose |
|---|---|---|
| **A billing/entitlement module** | A **new bounded context** in [04-modules.md](04-modules.md) and a dependency-graph edge | 🔴 — product owner + ADR |
| **Anything on Workspace & Tenancy instead** | Reversing *"does not own billing/subscription state"* | 🔴 — [04-modules.md](04-modules.md) |
| **The Stripe adapter** | A **new dependency**, and a home that is not the non-existent `bought_infra_adapters/` | 🔴 |
| **PostHog or Flagsmith** | **New dependencies** | 🔴 |
| **A pricing table over `ai_inference`** | A reader, which needs an owning module — the first row again | 🔴 |

**There is no smaller slice inside this that does not decide the boundary by implementing it**, which is the exact failure the coordination register exists to prevent — and the same reason [C-025](../LANE_COORDINATION.md)'s implementation was written and reverted rather than pushed.

**Raised as [C-200](../LANE_COORDINATION.md)**, with the problem, the affected modules, the alternatives, a recommendation, the trade-offs and the implementation impact, as `CLAUDE.md` §20e requires of an architectural blocker.

> **This is an architectural blocker, not an implementation one.** Nothing is waiting to be finished by somebody else. **No accepted architecture exists for the next step**, and it resumes when a direction is chosen rather than when a dependency frees up.

---

## 5 · What this document deliberately does not do

- **It does not name a module.** *Commercial Entitlement*, *Billing*, *Plans* — the name is part of the ruling, and choosing one here would make the decision look made.
- **It does not write an ADR.** ADRs are 🔴 and this lane may recommend, never ratify.
- **It does not propose a pricing model.** What Signora charges for is a commercial decision this lane has no standing to make, and the architecture above is deliberately indifferent to it.
- **It does not build the smallest possible piece to look productive.** Every candidate decides the boundary by implication.
- **It does not touch M14a.** Notifications is a separate milestone and nothing here assumes anything about it.

# ADR-0035: Commercial Profile — the head of the intelligence pipeline

## Status

**Accepted** — 2026-08-01, on the product owner's approval of the RFC reviewed across three sessions. Introduces the fourteenth module. Ratifies the module boundary, the pipeline's new head, and one new dependency edge.

Amends [04-modules.md](../04-modules.md) (new module entry) and [05-module-dependencies.md](../05-module-dependencies.md) (one new edge). Supersedes nothing.

## Context

**Signora had thirteen modules that process companies and nothing that said which companies.**

`RunProviderSync` takes a `subject: str`. Nothing in the repository supplies one. There is no scheduler, the deployed worker registers one function, and the Playground seeder has been the only thing that ever named a company. The pipeline is a ten-stage machine with **no input stage** — and that is not a missing feature, it is a missing bounded context.

Three consistency reviews found nine capabilities with no owning module. Four of them — **products, ICP, buying committee, target accounts** — turned out to be facets of one question the roadmap had been treating as four gaps: *what is this customer's commercial position?* Nothing had a name for the thing they belong to, which is why each was deferred individually and correctly, and why they all deferred into the same hole.

**ICP is the recorded instance.** Deferred out of M5A, M5B and M6 with a stated reason each time, named in five documents, and never given a milestone.

## Decision

**A new bounded context, `commercial_profile`, records what a customer declares about their own commercial position. It is the head of the intelligence pipeline.**

### The boundary, in one line

> **It records. It computes nothing, resolves nothing, and calls no provider.**

**Owns:** product catalog · solutions · ICP definition · buying-committee role templates · target account list · business priorities · commercial versioning · commercial audit history.

**Does Not Own** — each with a named owner, so the boundary cannot be misread:

| Not owned | Owner |
|---|---|
| Provider configuration · precedence · selection · normalization · quality | **Provider Platform**, entirely |
| Identity resolution | Knowledge Graph |
| **Truth resolution** | **Nobody today**, deliberately — see *ICP is smaller than it looked* |
| Signal generation · relevance | Signal Engine |
| Opportunity qualification | Opportunity Engine |
| Recommendation · Research | Recommendation / AI Research Engine |
| **Company discovery** | A future context — see *Discovery is excluded* |
| **Person entities** | Deferred; `EntityKind` has `COMPANY` only |

### Several small aggregates, not one

**Refined during implementation.** The RFC implied a single versioned `CommercialProfile`. That is wrong: products change quarterly and a target account list changes weekly, so versioning them as one aggregate would mint a catalog version every time somebody added a company — **thousands of versions, and an audit history nobody can read.**

The context holds **several small aggregates, each versioned independently**. The first is `ProductCatalog`.

### Versioned, immutable, superseded

The same discipline as `signal_profile`, for the same reason: the moment anything downstream records *"this is about Product X"*, an edited catalog makes that citation unresolvable — *"which product did you mean?"* would have no answer, because the answer changed underneath it.

**A product's identity outlives the catalog containing it.** `Product.id` is stable across versions; revising the catalog mints a new *catalog* version and does not mint new products. That is what lets a future reference survive twelve revisions of the list it lives in.

### Why products first

Products anchor everything else: an ICP is *"the kind of company that buys **this**"*, a buying committee is *"who decides about **this**"*, and a priority is a ranking **of these**. The product owner's sequencing, and it is right — every later slice gets a natural reference point, and the first slice stays small.

## Pipeline position

```
Workspace & Tenancy ⟶ scopes everything
          │
   commercial_profile          ← the new head
          │ target_accounts_changed
   Provider Platform           ← finally has a subject
          ▼
   Provider Normalization ▸ Knowledge Graph ▸ Observation Engine
          ▼
   Business Event Engine ▸ Signal Engine ▸ Buying Score Engine
          ▼
   Opportunity Engine ▸ AI Research ⟶ AI Reasoning
          ▼
   Timeline ⟶ Revenue Intelligence Platform
```

**Exactly one new edge is required**, and it does not exist yet:

| Edge | Type | Status |
|---|---|---|
| `commercial_profile → provider_platform` | Event | **Slice 5** — arrives with the target account list |
| `commercial_profile → knowledge_graph` | Sync read | Slice 5 |
| `opportunity_engine → commercial_profile` | Sync read | Future — the fit condition on a policy version |
| `RIP → commercial_profile` | Sync read | Future — composition |

**The graph stays acyclic, trivially:** `commercial_profile` has no upstream dependency except tenancy. It is the cheapest module the architecture could gain — nothing can point at it.

**Enforced, not documented.** Two import-linter contracts ship with slice 1: `commercial_profile` may not import any pipeline module, and no module may reach past its `public/`. If it could read a signal or a score, *"declaration"* would quietly become *"declaration informed by our own conclusions"*, and the one boundary it has would be gone.

## ICP is smaller than five documents claim

[27-opportunity-engine.md](../27-opportunity-engine.md) deferred fit three times on one reason: *"fit needs a resolution policy — a stated, versioned, explainable rule for choosing among disagreeing providers… provider precedence? recency? corroboration?"*

**Two things have since made that a much smaller problem:**

1. **The ownership half is decided.** Provider precedence is Signora's, not the customer's ([04-modules.md](../04-modules.md), ruled 2026-08-01). The question was hard partly because it looked like customer configuration. It is not, so it never enters this module.
2. **The mechanism half already ships.** `select_name` resolves a company's name at read time — *most recently observed claim wins*, never stored, disagreement surfaced. **That is a resolution policy, in production, for one attribute.**

So the remaining work is *"generalise `select_name` to industry and size"* — a **Knowledge Graph slice**, not a milestone, and deliberately not in this ADR. This module owns the ICP *declaration*; matching against it is separate, which is what lets the declaration ship and be useful first.

## Discovery is excluded

Automated company discovery needs a provider *company-search* capability no adapter has. Naming a module for it now is the speculative abstraction §6 forbids.

> **Trigger, recorded so it is not a judgement call later: a provider adapter exposing company search against firmographic criteria.** Until then there is no context, no module, and nothing scheduled — recorded in [04-modules.md](../04-modules.md) the way `Assignments` already is.

The **manual** target account list is not discovery and is owned here from slice 5. It is how every ABM tool starts, and it is what finally gives Provider Platform a subject.

## Consequences

**We gain:** an owner for four ownerless capabilities · the pipeline's missing input · the first module a customer authors end to end · a natural anchor for ICP, buying committee and priorities · and a lane boundary with almost no overlap with the product surface.

**We give up:** a fourteenth module's coordination cost — the smallest available, since nothing depends on it.

**We accept:** that a customer types company names until discovery exists. Correct, and it makes the pipeline demonstrable end to end for the first time.

## Alternatives considered

**Two modules — declaration and discovery.** The split is real (different change rates, failure modes, dependencies) and the second half cannot be built. Rejected as speculative; discovery is recorded as a future context with a trigger instead.

**Fold it into Signal Engine, beside `signal_profile`.** Rejected: relevance over hypotheses and fit of a company are different questions, and merging them would put *"is this company like our customers?"* inside the module that forms hypotheses — which is the module least equipped to review it.

**One mega-aggregate.** Rejected during implementation — see *several small aggregates*.

**Name it `go_to_market`.** The runner-up. Correct seller vocabulary and it survives territories, but GTM also means campaigns, pricing, messaging and enablement — it *invites* the junk drawer this module's main risk names. **Rename trigger recorded:** if territories and seller assignment land here, it has become go-to-market and should be renamed then.

## References

- [04-modules.md](../04-modules.md) — the module entry and manifest
- [05-module-dependencies.md](../05-module-dependencies.md) — the graph and the context map
- [ADR-0034](0034-ubiquitous-language.md) — *Product* and *ICP* are customer-facing terms; *workspace* is not
- [PRODUCT_ROADMAP.md](../../../PRODUCT_ROADMAP.md) — the consistency reviews that found the gap

# ADR-0411 — Signora owns customer-organized account metadata

| | |
|---|---|
| **Status** | ✅ **RATIFIED — product owner, 2026-08-12, as [C-1425](../../LANE_COORDINATION.md)** |
| **Decision** | ✅ ***"Signora should own these as CUSTOMER-ORGANIZED ACCOUNT METADATA: Account Owner / CSM · Tags · Segments."*** |
| **Scope** | ⛔ **Those three. Nothing else** |

## 1 · Why this is a different ADR from [0409](0409-commercial-account-facts.md)

📁 **The ruling says so, and the reason is [§2](../../../CLAUDE.md)'s least-powerful-author rule:**

> *"These are customer-authored organizational concepts, distinct from provider/CRM commercial facts such as ACV, Renewal and Commercial Stage. They therefore must NOT be merged with C-209 / ADR-0409."*

| | **This ADR** | **[ADR-0409](0409-commercial-account-facts.md)** |
|---|---|---|
| **Author** | ✅ **The customer**, organising their own book | **The provider** — facts a CRM already holds |
| **Provenance** | **Direct authorship in Signora** | **A claim, normalized from a payload** |
| **If wrong** | A label is wrong and the customer fixes it | ⛔ **Signora asserts a false commercial fact** |

⛔ **So these are NOT `ClaimAttribute`s and must not be added to the claim vocabulary.** ⚡ **A claim records *what a provider asserted*; nobody asserted a customer's own tag.** **Putting them there would make the provenance of every claim ambiguous.**

## 2 · One contract, reused everywhere

📁 ***"The exact domain model, ownership boundary and APIs must be defined once and reused by: Companies · Account 360 · Action Batch / TASK-466 · any other approved surface."***

⛔ **No screen-specific model.** ⚠️ **Companies draws *Owner* and *New segment*; Account 360 draws *Owner* and *CSM*. Same concepts, and if two screens model them separately they will disagree within a release.**

## 3 · What the three are

| | Semantics |
|---|---|
| **Account Owner / CSM** | ⚡ **A reference to a workspace *member*, not free text.** ⛔ **A person who leaves must not leave a dangling string** — the reference is what makes removal answerable |
| **Tags** | **Workspace-scoped, customer-authored, many-per-account.** ⚡ **A flat vocabulary the customer owns** |
| **Segments** | **A named, saved grouping of accounts.** ⚠️ **Whether a segment is a stored list or a stored predicate is an implementation choice and is Lane A's** — ⛔ **but it is ONE choice, made once, not per screen |

## 4 · Ownership boundary

| | |
|---|---|
| **Owning module** | ⚠️ **NOT fixed here.** ⛔ **The ruling approves the *capability*, not its address.** ✅ **Lane A proposes the owning module in its Slice Handoff, from the boundaries it can see** — 📁 [§20e](../../../CLAUDE.md): *ownership becomes obvious when implementation reaches a module; predicting it earlier buys nothing and can be wrong* |
| **Tenancy** | 🔴 **Workspace-owned, without exception.** **Non-nullable `workspace_id` · RLS enabled *and* forced · registered in `tenancy_policy.py` in the same change** ([§8](../../../CLAUDE.md)) |
| **Consumers** | **Read the one contract.** ⛔ **No consumer defines a local tag or segment type** |

## 5 · What this releases

✅ **[TASK-466](../../BACKLOG.md)** — 📁 the ruling: ***"Do NOT build fake Action Batch actions before the underlying capability exists."*** ⚡ **This ADR is that capability, so the Action Batch's first consumer now has a real operation to apply and an inverse to reverse** — which was [C-1425](../../LANE_COORDINATION.md)'s whole blocker.

✅ **Companies** — *Owner*, *New segment*, and the tag-based filters, excluded from [TASK-1475](../../BACKLOG.md).
✅ **Account 360** — the header's *Owner* and *CSM*, excluded from [TASK-1476](../../BACKLOG.md).

## 6 · What this ADR deliberately does not decide

⛔ **Which module owns it · table or column design · API shape · the migration · whether a segment is a list or a predicate · any UI · whether tags are shared across workspaces (they are not — §4) beyond that.**

⚠️ **And explicitly NOT approved by this ruling: field-level permissions.** 📁 **[C-210](../../LANE_COORDINATION.md)'s ruling says so in terms** — *"field-level permissions are ALSO NOT implicitly approved… that is a separate authorization capability question."* ⚡ **It belongs with [ADR-0410](0410-authorization-capability-layer.md), not here.**

# ADR-0036: The Target Account Contract — customer intent, and where it stops

## Status

**Accepted** — 2026-08-02, on the product owner's direction, ratifying the answer Lane A gave to coordination item [`C-001`](../../LANE_COORDINATION.md#c-001--the-target-account-contract) and four ownership boundaries alongside it.

Refines [ADR-0035](0035-commercial-profile.md) (which introduced the module and named the edge) and [05-module-dependencies.md](../05-module-dependencies.md) (which types the edge Customer–Supplier). Supersedes nothing.

**This ADR exists so the decision stops living in a coordination register.** `LANE_COORDINATION.md` is a working file for questions in flight; an answer that stays there is an answer a cold session has to go looking for. The register shrinks as the architecture absorbs it, and this is one of those absorptions.

## Context

`commercial_profile → provider_platform` is **the first and only edge the fourteenth module has ever had**, and the first time anything downstream consumes a customer's declaration. [05-module-dependencies.md](../05-module-dependencies.md) types it **Customer–Supplier**, whose stated rule is that *the downstream lane's needs shape the contract* — so drawing it from the producing side and asking afterwards would produce exactly the contract that pattern exists to prevent.

It also closes a gap open since M2.1: **`RunProviderSync` has taken a `subject: str` for four milestones and nothing has ever supplied one** outside the Provider Simulation Framework.

Seven questions were raised by the producing lane and answered by the consuming one. What follows is the decision, not the exchange.

## Decision

### 1 · Four ownership boundaries, permanent

Stated together because the contract below is only defensible if these hold, and because each has been re-derived at least twice in review:

> **Commercial Profile owns customer intent.**
> **Provider Platform owns synchronization.**
> **Knowledge Graph owns understanding.**
> **Signal Engine owns intelligence.**

They are not four restatements of the module list. Each names the thing most likely to be taken by a neighbour:

| Boundary | The mistake it forbids |
|---|---|
| Commercial Profile owns **intent** | …and therefore not scheduling, not matching, not resolution. A module that records *"watch Acme"* must not grow an opinion about how often to look |
| Provider Platform owns **synchronization** | …and therefore *entirely*: cadence, polling policy, cost, provider selection, failover, backoff, deltas. None of it enters a customer's declaration, and none of it is a customer's to configure ([04-modules.md](../04-modules.md), ruled 2026-08-01) |
| Knowledge Graph owns **understanding** | …so an unresolved customer-typed name stays unresolved until it reaches the module whose job resolution is. Nobody upstream resolves helpfully |
| Signal Engine owns **intelligence** | …including **relevance**. *"Funding rounds matter more to us than hiring"* is a statement about interpretation, not about commercial position, however customer-authored it looks |

### 2 · The event triggers; the port supplies

**`commercial_profile.target_accounts_changed` is what Provider Platform consumes. `TargetAccountReader` on `commercial_profile/public/` is what its handler then calls.**

Not a choice between them. The event is the *trigger* and the port is the *payload* — the repository's standing rule (*events carry identity; ports carry payload*) stated as a control flow.

A read port alone would make Provider Platform **pull**, and pulling needs a trigger anyway; the only honest trigger is *"the customer changed their mind"*, which is an event by definition.

### 3 · The event carries identity and change only

`workspace_id` on the envelope, `declaration_version` in the payload, **nothing about accounts**. Embedding names would make every future field an event-contract change, and would put a copy of a truth that lives in an aggregate onto a bus.

### 4 · Provider Platform receives the complete declaration state and computes its own deltas

**The port returns the whole list, never a delta.** Three reasons, and the first is the one that decides it:

**A delta from Commercial Profile answers the wrong question.** It is a delta between two *declarations*. What Provider Platform needs is a delta against **what it has actually synced** — a different set. A customer can re-add an account that was declared before and never successfully fetched, and a declaration-delta would call that *"no change"*.

**Provider Platform already owns the state that answers the real question** (`provider_watermark`), so computing the delta there needs nothing new and puts it beside the thing it is a delta against.

**A whole list is idempotent to apply and a delta is not**, which matters on a bus with at-least-once delivery.

> **Commercial Profile must never compute synchronization logic.** It records what a customer declared; what has and has not been fetched is not a fact it holds.

### 5 · `subject` stays a `str`, and stays unresolved

`ProviderRequest.subject` is *"a domain identifier of the subject (a company key, a domain name)"*, **opaque to the platform and interpreted only by the adapter**. A company name as the customer typed it is exactly what belongs there.

**Provider Platform does not want a domain, a country, or any other qualifier.** Asking for one would ask a customer to perform resolution, and resolution quality is Signora's competence rather than theirs (ruled 2026-08-01). If an unresolved name is a weak key for a given provider, that is **the adapter's problem to solve and Provider Platform's to own** — which is the entire reason `subject` is opaque.

**Resolution belongs downstream**, in the Knowledge Graph, where it already lives.

One field beyond the name: **the declaration entry's stable id**, so that *renaming* an entry is distinguishable from *removing one and adding another*. Those are different instructions about spending money.

### 6 · Removal stops polling and deletes nothing

**Polling stops.** A customer who un-watches an account has said not to spend on it.

**Nothing already gathered is deleted.** Raw provider records are evidence, and the Knowledge Graph, observations, business events, signals, scores and every narration downstream cite them. Deleting them would erase the basis of conclusions a customer has already read and acted on. *Erasability is a property of the tenancy model* — it belongs to deleting a workspace, not to un-watching a company.

**The watermark stays**, so re-adding resumes incrementally rather than re-fetching a full snapshot.

### 7 · The version travels, and the reason is ordering

Idempotency on `event_id` handles **redelivery**. It does not handle **ordering**: two declarations in quick succession are two workspace-level events, and per-entity ordering does not order them against one another. A handler for version 5 running after version 6's would sync a list one revision stale.

So `declaration_version` is on the payload, and **Provider Platform ignores an event older than the version it has already acted on** — a comparison it makes locally, with no coordination.

## Consequences

**Commercial Profile stays a module that records.** Its one edge carries a version and a change, and everything else is read through a port on demand. Nothing about providers, schedules or costs can reach it, because none of it is on the wire.

**Provider Platform gains its first real input.** `subject` stops being a parameter nothing supplies.

**One defect must be fixed before the consumer is built** — [`B-004`](../../BUGS.md): `provider_watermark` is keyed `(workspace_id, provider, capability)` and carries **no `subject`**, so a workspace watching two accounts would advance one account's position and silently skip evidence for the other. It is Provider Platform's, on the consuming side, and belongs to the slice that builds the consumer.

**The relevance profile is not this.** *"Product-launch signals matter to us"* is Signal Engine's, by the boundary in §1 — recorded here because it is one careless sentence away from Commercial Profile and was asked as [`C-005`](../../LANE_COORDINATION.md#c-005--who-owns-the-signal-profile-write-path).

## Alternatives considered

**A read port with no event.** Rejected: Provider Platform would have to poll a declaration to find out when a declaration changed, which is a scheduler for a question an event answers exactly.

**An event carrying the account list.** Rejected: every future field becomes an event-contract change, and the bus would hold a copy of an aggregate that is versioned and immutable three feet away.

**A delta from Commercial Profile.** Rejected in §4 — it is a delta against the wrong baseline, and it is not idempotent.

**Requiring a resolved domain from the customer.** Rejected: it hands Signora's core competence back across the table, and a customer who mistypes a domain gets silence rather than a match Signora could have made.

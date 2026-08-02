# ADR-0038: Timeline — the pipeline's account of itself

## Status

**PROPOSED — 2026-08-02, by Lane B, assigned M7.**

**Not ratified, and nothing is implemented.** Drafted at the product owner's direction after [C-020](../../LANE_COORDINATION.md) recorded that Timeline had a bounded context and no design. It follows the route [ADR-0035](0035-commercial-profile.md) took for Commercial Profile: the assigned lane drafts, the product owner ratifies, and slice 1 begins after ratification and not before.

**Three decisions are deliberately left open** and marked ❓ below. They are the product owner's, and each changes what M7 builds.

## Context

Timeline is milestone **M7**, position 15 of 21, and the fifteenth module. It is named in [04-modules.md](../04-modules.md), placed in the dependency graph in [05-module-dependencies.md](../05-module-dependencies.md), given a technology in [ADR-0008](0008-search-and-vector-retrieval.md), and described nowhere else. Every module built since M3A has had a design document written as it was built; Timeline has five lines.

**What the architecture already fixes, and this ADR does not reopen:**

| | |
|---|---|
| **Purpose** | A chronological feed of everything that has happened for a given entity |
| **Owns** | The Timeline read model, chronological aggregation, the timeline query API |
| **Does not own** | *Any* of the source-of-truth data it displays. **Timeline is a projection** |
| **Publishes** | **Nothing.** A pure read-side consumer |
| **Consumes** | Seven event types, plus three supersession events named in the catalog |
| **Relationship** | **Conformist** to every upstream — it owns none of what it displays |

**Six of its seven consumed events are published by modules running today.** Only `recommendation.created` awaits M11, which is deferred rather than cancelled.

## Decision

### The boundary, in one line

> **Timeline records that something happened, in the words the module that owned it used, and never decides what any of it means.**

Every module upstream has already made its judgement — an observation was recorded, a signal was found relevant, a score moved, an opportunity opened. **Timeline re-states those facts in time order and adds no opinion of its own.** It does not rank, score, summarise, correlate, or explain. When a reader wants to know *why* an entry matters, the answer is on the entry's own module's surface, and Timeline links there rather than reproducing it.

This is the same discipline `commercial_profile` took from the other end: that module **records and computes nothing**; this one **projects and computes nothing**. Between them they bracket a pipeline whose thirteen middle modules do all the deciding.

### A projection is derived, and therefore rebuildable

**`timeline_entry` holds no fact that does not exist upstream.** Every row is derived from an event whose source of truth is another module's table, and the entry stores the identifiers needed to go back there.

This follows *truth has exactly one authoritative representation; everything else derives from it* (`CLAUDE.md` §2) and it has a concrete consequence worth stating as a property rather than an aspiration:

> **The entire timeline can be dropped and rebuilt from the source modules without loss.**

A projection that cannot be rebuilt has quietly become a source of truth. This one is placed in the *derived intelligence* data category — rebuildable — and never in *operational history*, which is the platform's account of its own behaviour and is not.

> ### ⚠️ This property is not achievable as drafted — found 2026-08-02, in review, before ratification
>
> **Rebuilding requires replaying the events the entries derive from, and the outbox is a delivery mechanism rather than an event store.** A relayed row has done its job; nothing in the architecture undertakes to keep it for the life of the workspace. So a rebuild has exactly two sources and **this ADR is entitled to neither**:
>
> | Source | Why it is unavailable |
> |---|---|
> | The upstream modules' own tables | **Forbidden outright.** No module may query another's tables (§5) — the rule with no exceptions |
> | A read port on each of the six upstreams | **None exists.** Six ports, six `public/` contracts, six owning modules — and every one is another lane's to publish |
>
> **The cost of honouring it is larger than the milestone.** Six read ports negotiated across six modules is not a slice inside M7; it is comparable to M7 itself, and by [05-module-dependencies.md](../05-module-dependencies.md) each is a Conformist relationship the *downstream* module does not get to define alone.
>
> **Three ways out, and the choice is the product owner's:**
>
> | | |
> |---|---|
> | **A · Drop the claim** | Timeline becomes rebuildable only from whatever event history is retained. Honest, smaller, and it means a projection defect is repaired by migration rather than by replay |
> | **B · Keep it and fund it** | Six read ports enter M7's scope, and M7 stops being a 6–8 ew milestone |
> | **C · Make the outbox retain** | The property becomes real for every projection, not just this one — and it changes a **platform** component under §20a, so it is an RFC rather than a milestone decision |
>
> **Lane B recommends A for M7 and C as the eventual answer**, because *"a projection can be rebuilt"* is a property the platform should provide once rather than each projection arranging privately. **Recorded rather than quietly deleted:** the claim was load-bearing in the argument for placing Timeline in the rebuildable data category, and a reader who sees only the conclusion would inherit reasoning that no longer holds.

### Entries are immutable, and correction is a new entry

An entry records **what was true when the event arrived**. Upstream supersession — `observation.superseded`, `business_event.superseded`, `signal.superseded` — does not edit the entry it supersedes; it **adds** one that names its predecessor, exactly as the upstream modules do.

**A timeline that edits its past is a timeline nobody can cite**, and the entries most worth editing are always the inconvenient ones (§2, immutability).

### The entry is one shape, not seven

❓ **Open question 1 is below; this is the recommendation.**

Seven event types produce **one** `TimelineEntry` with a discriminated `kind`, not seven tables and not seven aggregates. The alternative — a table per source — makes the one query the module exists to serve (*"everything for this entity, newest first"*) a seven-way union that grows a branch per upstream.

The entry carries: the workspace, the entity, `occurred_at` (the domain time, **not** the arrival time), the kind, the originating `event_id`, the source module, a **stable reference to the row upstream**, and a short customer-facing summary line.

**`occurred_at` is the domain's time and ordering is by it.** Arrival order is a fact about the bus, not about the account — and a feed ordered by arrival tells a seller that a thing that happened in March happened after a thing that happened in June.

### Vocabulary is the customer's

[ADR-0034](0034-ubiquitous-language.md) binds: a seller reads *Signal*, *Opportunity*, *Evidence*, *Account*. **They must never read *observation*, *business event*, *projection*, *entry kind* or *entity*.** The translation lives at the frontend edge and does not travel inward — the column stays `kind`, the screen says what a salesperson would say.

**This module is where that rule is most easily broken**, because its content is literally a list of other modules' internal milestones. A feed that reads *"observation.recorded — employee_count"* is the pipeline talking to itself in front of a customer.

### Idempotency is on `event_id`, and the projection is replay-safe

At-least-once delivery means every handler sees duplicates. An entry is keyed by its originating `event_id`, so a redelivery writes nothing and a full replay reproduces the identical feed. **This is what makes the rebuild property above true rather than hoped for.**

## The three open questions

**Each is the product owner's, and each changes what M7 builds.**

### ❓ 1 · Meilisearch now, or Postgres first

[ADR-0008](0008-search-and-vector-retrieval.md) selects Meilisearch **by name and on Timeline's behalf** — *"materially better out-of-the-box for the kind of sales-user-facing search Timeline needs"*. It is in **no compose file, no `make smoke` stage, and no Settings object.**

| | |
|---|---|
| **A · Meilisearch in M7** | Honours ADR-0008 immediately. Adds a backing service, its Settings object, its health and readiness wiring, a `make smoke` stage, and a second write path to keep consistent with Postgres |
| **B · Postgres first, Meilisearch on a stated trigger** | Ships the feed sooner. The primary query — *entity, newest first, cursor-paginated* — is an index, not a search. **ADR-0008's own justification is typo-tolerance, relevance ranking and faceting**, none of which a chronological feed needs until somebody searches it |

**Lane B recommends B, with the trigger stated in the design:** *the first customer asking to search or facet a timeline rather than scroll it.* ADR-0008 ratifies the technology; it does not schedule it, and standing up a backing service for a query that is `ORDER BY occurred_at DESC` would be building for a load with no evidence (§14).

**This is a recommendation and not a decision.** If the answer is A, the design absorbs it and M7 grows an infrastructure slice.

### ❓ 2 · Six events now, or wait for the seventh

Six of the seven upstreams are live; `recommendation.created` awaits deferred M11.

**Lane B recommends shipping the six**, adding the seventh when M11 resumes. A projection that cannot absorb a new entry kind later is the wrong design regardless, so this costs nothing and proves the extensibility on the first occasion.

### ❓ 3 · Does the timeline reach a customer in M7, or is it read-only infrastructure

`CLAUDE.md` §2 binds from M12.3: **every completed slice is demoable by a non-engineer**, and a slice whose demonstration needs a paragraph of architecture is infrastructure that has not reached a customer.

A backend-only Timeline is exactly that. But the frontend surface is **Lane A's** by the Change Budget, and the navigation decision is [D38](../38-product-design-principles.md)'s — which retired *Timeline* as a menu entry, on the reasoning that navigation is journeys rather than data.

**Lane B's position: the account brief is the timeline's home**, not a menu entry — *what has happened with this account* belongs beside *what we think about this account*. That makes M7's last slice a two-lane build like [C-007](../../LANE_COORDINATION.md), and it should be agreed before slice 1 rather than discovered at slice 4.

## Pipeline position

```
observation · business_event · signal · buying_score · opportunity  ──┐
                                                                      ├──▶  Timeline  ──▶ (read)
recommendation  (M11, deferred)  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┘
```

**No new edge is introduced.** Every arrow above is already in [05-module-dependencies.md](../05-module-dependencies.md), typed Conformist. Timeline publishes nothing, so nothing downstream gains a dependency on it except Revenue Intelligence Platform's already-documented synchronous query.

## Consequences

**We gain** a single place that answers *"what has actually happened with this account?"* — today that question is answered by opening four surfaces and mentally merging them.

**We accept** a projection that must be kept correct as seven upstreams evolve. The mitigation is that it is rebuildable: a projection bug is repaired by replaying, not by migrating.

**We accept** that Timeline is only as good as its upstreams' vocabulary, and that the customer-facing summary line for each kind is **static knowledge a domain expert owns** — the least-powerful-author rule (§2). It is a reviewed catalog of phrasings, not a model output and not a string built in a handler.

**We defer** search, faceting and cross-entity feeds, each with a stated trigger.

## Alternatives considered

| Alternative | Why not |
|---|---|
| **No Timeline module — each surface renders its own history** | The question *"what happened with this account"* has no owner, and every surface answers a seventh of it. This is the state today |
| **Timeline as a view over the source tables** | No new storage, always consistent — and a seven-way `UNION` across seven modules' private tables, which §5 forbids outright: no module may query another's tables |
| **Timeline stores its own copy of the facts** | Makes the feed self-sufficient and duplicates truth that lives upstream. The copy is the one that goes stale, and it can never be corrected without an edit |
| **One aggregate per source event type** | Faithful to the upstreams and turns the module's one query into a union that grows a branch per upstream forever |

## References

- [04-modules.md](../04-modules.md) — the Timeline bounded context
- [05-module-dependencies.md](../05-module-dependencies.md) — six Conformist upstreams; RIP's synchronous query
- [06-events.md](../06-events.md) — the seven consumed events and the three supersession events
- [ADR-0008](0008-search-and-vector-retrieval.md) — Meilisearch, ratified for this module
- [ADR-0034](0034-ubiquitous-language.md) — the customer's vocabulary
- [ADR-0035](0035-commercial-profile.md) — the pattern this ADR follows
- [C-020](../../LANE_COORDINATION.md) — the coordination item that produced this draft

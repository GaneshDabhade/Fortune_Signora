# 45 — Timeline (module design)

> Status: **As built.** M7 slices S01–S04a promoted, plus [B-301](../BUGS.md). Lane B.
>
> Ratified in proposal by [ADR-0038](adr/0038-timeline.md), which remains **`Proposed, not accepted`** and holds three open questions. The ADR says *why the module exists and what it should be*; this says **what was built**, in the manner of [22](22-knowledge-graph.md)–[29](29-ai-reasoning-engine.md), [40](40-commercial-profile.md) and [41](44-integrations.md).
>
> **Created 2026-08-02, after the module was promoted rather than before it** — which is the wrong order and is recorded as such. Timeline shipped four slices with an unratified ADR and no as-built document, and in that gap it also shipped [B-301](../BUGS.md): a projection the deployed worker never subscribed to. **A design document would not have caught B-301. What it would have caught is that nobody had written down where entries come from in production**, which is the sentence the defect was hiding in.

---

## 1 · The boundary, and the one sentence everything follows from

> **Timeline records what upstream modules said, in time order. It interprets nothing, and it owns no meaning of its own.**

Every field on an entry is either copied from an event or derived deterministically from one. There is no rule in this module that decides what an event *means*, how important it is, or what to do about it — those belong to the Signal Engine, the Buying Score Engine, the Opportunity Engine and Recommendation Engine respectively, and each has already published its answer by the time Timeline sees the event.

**Timeline subscribes and publishes nothing.** A pure read-side consumer, so there is no outbox write here and no event to catalog in [06-events.md](06-events.md).

**What it owns:** the `timeline_entry` projection · the projection rules · the feed query and its cursor.

**What it does not own:** what happened (the producing modules) · what currently needs attention (Revenue Intelligence Platform) · what changed since a person last looked (Notifications — [ADR-0040](adr/0040-notifications.md), and the distinction is drawn there because these two are the pair most likely to converge) · where the feed is mounted (the product surface, Lane A).

---

## 2 · A projection is derived, and therefore rebuildable

`timeline_entry` holds **no fact that does not exist upstream.** Delete every row and replay the outbox and the identical feed returns.

That is what makes the table a *projection* rather than a second copy of the truth, and it is the property that decides several arguments below: nothing here may be edited, nothing here may be the only record of anything, and a change to a projection rule is a rebuild rather than a migration.

**The entry id is derived, not generated:**

```python
uuid5(TIMELINE_NAMESPACE, str(event_id))
```

**A redelivery derives the same id and writes nothing.** A dead letter replayed months later does the same. **This is the whole idempotency story** — no ledger, no read-then-write, no dependence on the dispatcher's transaction. It is also what allowed B-301's fix to register a consumer while [C-012](../LANE_COORDINATION.md) is still open: the handler cannot write twice, so it needs no share of anybody's transaction.

Written with `ON CONFLICT DO NOTHING` rather than a read-then-write. Two workers handling one redelivery would both find nothing and both insert; **the database already refuses the duplicate, and asking it to say so is cheaper and correct under concurrency.**

---

## 3 · One shape, nine rules, and an allow-list

**One entry shape, not one per kind.** A feed with seven row types is seven components, seven empty states and seven ways to be inconsistent. `TimelineEntry` carries `kind`, `occurred_at`, `entity_id`, `source_module`, `source_ref` and a `detail` map.

**`PROJECTIONS` is a table, not a chain of branches.** Nine event types, each naming its `kind`, its `source_module`, the payload key holding its source reference, and the payload keys it may carry into `detail`.

**`detail_keys` is an allow-list, and that is the design decision in this module most worth keeping.** A projection that copied whole payloads would make Timeline a second store of upstream data — it would grow whenever an upstream added a field, it would be a place a customer's data leaked into unnoticed, and the *"holds no fact that does not exist upstream"* property would become impossible to check. **The allow-list makes the rule mechanical**: a field reaches the feed because somebody named it, or it does not reach the feed.

**`time_key` exists for exactly one upstream, and earns it.** Most events happened when the envelope says. `business_event.detected` did not: **detection can lag occurrence by days**, and a seller reading a feed wants the funding round on the day it was announced, not the day Signora noticed. Absent, the envelope's time is used.

**A mapped event with a missing entity or a missing source reference is refused, not defaulted.** `UnprojectableEvent` surfaces an upstream contract change as an error on the projection, rather than as a row on a customer's feed that points nowhere. **The module holds no meaning of its own to fall back on**, so there is nothing to default to.

**An unmapped event writes nothing and does not raise.** Most of the bus is not this module's business, and silence is the correct response.

---

## 4 · How entries actually arrive — and the defect that lived here

**Nine subscriptions, one handler, on the `read_model` pool**, registered in `apps/worker/subscriptions.py` and derived from `PROJECTIONS` rather than listed by hand.

> **This is the paragraph whose absence was [B-301](../BUGS.md).** Timeline was promoted with domain, table, repository, read API, router and feed component all built and tested — and **no subscription**. `project_to_timeline` was referenced nowhere outside tests. A customer would have seen a timeline that stayed empty forever, and 2518 passing tests, the coverage gate, MyPy strict, import-linter, `make smoke` and a full certification cycle all said nothing.
>
> **None of them could have.** `apps/worker/subscriptions.py` is a composition root, and **a composition root is the one file no module's own suite covers**: the unit tests drive `ProjectEvent` directly and the integration tests drive the handler directly, so both halves were proven and the join never was.
>
> **The general form, because it will recur:** *every component proven, the composition never exercised.* [B-024](../BUGS.md) is the same defect one level down — fakes accepted a row the database would refuse. **Where a guarantee lives in a join — a composition root, a foreign key, an RLS policy, a keyset predicate — the test has to live there too.** The repository-wide version of this assertion is [C-301](../LANE_COORDINATION.md) and is QE's.
>
> **It recurred twice more, and the prediction is now a measured pattern.** [B-302](../BUGS.md) — the Playground's own composition root wired nine pipeline stages and not this projection, so *"What has happened"* was empty on all twelve demonstration accounts in the only environment anybody reviews the product in. Then [B-303](../BUGS.md), one layer further out again: **the browser's only route to the API had never been built**, so no screen in this product had ever rendered its own data, and this feed could not have been seen even after B-302 was fixed. **Four instances, one shape.** [C-308](../LANE_COORDINATION.md) asks the browser-boundary half of the question C-301 asks at the worker boundary.

**Verified in a browser, not only in a database.** `frontend/tests/e2e/daily-usage.spec.ts` opens a real account brief as a signed-in seller and asserts the section is not empty — which is the first time any Timeline guarantee has been checked through the surface a customer actually uses. Before that, every assertion about this module stopped at the API.

**Why `read_model`.** [pools.py](../../backend/apps/worker/pools.py) has declared it since M1.1 as *"Timeline, Revenue Intelligence Platform — projection updates"* and it had **never been used.** High concurrency, short timeout — the right shape for one insert, and it keeps a projection storm off the pool the pipeline itself runs in.

**Nine subscriptions rather than one** because the registry keys on `(consumer, event_type)` and the relay needs the triple to choose a queue. That is a routing table, not repetition.

---

## 5 · Reading the feed

**One question: *what has happened to this account, newest first.***

**Keyset, never `OFFSET`, never `COUNT`.** Positioned on `(occurred_at, id)` — `id` breaks ties because **two entries can share a timestamp, and a paginated feed whose order is not total silently drops or repeats rows at a page boundary.** The index `(workspace_id, entity_id, occurred_at, id)` exists to serve exactly this.

**Row-wise tuple comparison** rather than `occurred_at < x OR (= x AND id < y)`: one predicate the planner drives straight off the index, and one expression that cannot be got subtly wrong at a tie.

**`has_more` is answered without counting.** A `COUNT` on a feed is a full scan the customer never asked for.

**Paging by `occurred_at` is safe here only because entries are immutable.** Paging by anything the pipeline can move would let a projection arriving between two requests skip an entry or repeat it. `CursorPosition` names its first field `created_at` because it is the platform's generic sort key — that is not a claim about a column.

**`workspace_id` is filtered explicitly beside RLS**, which is the authoritative control (§8, defence in depth).

---

## 6 · What was built, and what was not

| Layer | What |
|---|---|
| **Domain** | `EntryKind`, `TimelineEntry` with `project()`, `PROJECTIONS`, `ProjectionRule`, `rule_for` |
| **Application** | `ProjectEvent`, `TimelineQueries`, `FeedPage`; ports `EntryStore` (append) and `FeedReader` (read) |
| **Infrastructure** | `SqlEntryStore`, composition |
| **Interface** | `project_to_timeline` (consumer `timeline.project`), the feed route, response schemas |
| **Migration** | `0026_timeline_entry` — RLS enabled and **forced**, registered in `tenancy_policy.py`, **no `UPDATE` grant** |
| **Worker** | 9 subscriptions on `read_model` |
| **Frontend** | the feed component |

**`EntryStore` and `FeedReader` are separate ports over one implementation**, deliberately: a component that only reads a feed must not be handed the ability to append to it.

**No `AuditMixin`, and that is a decision rather than an omission.** It requires a non-nullable `created_by`, and **a projection row has no actor** — nobody *did* this; an upstream module published a fact and the projection recorded it. Filling the column with a system UUID would invent an author for an audit trail, which is worth less than the honest absence.

### Known limitations

- **No mount point.** The feed component exists and nothing renders it — [C-024](../LANE_COORDINATION.md), Lane A's shell. **Until it is mounted the capability is unreachable**, exactly as `/settings/connections` was before [M13-S08](44-integrations.md).
- **Six of seven upstreams.** `recommendation.created` awaits M11, which is deferred. The rule is absent rather than stubbed.
- **No search.** [ADR-0008](adr/0008-search-and-vector-retrieval.md) names Meilisearch *on Timeline's behalf*; it is in no compose file, no `make smoke` stage and no Settings object. See §7.
- **ADR-0038 is unratified**, and three questions in it are open.

---

## 7 · The open questions, and where they stand

**All three are ADR-0038's and remain the product owner's.** Restated here because a lane arriving at Timeline will read this document first, and an open question it cannot see is one it will answer by accident.

| | Question | Where it stands |
|---|---|---|
| **1** | **Meilisearch now, or Postgres first?** | **Built on Postgres.** The primary query is `ORDER BY occurred_at DESC` over an index, not a search, and ADR-0008's justification is typo tolerance, relevance ranking and faceting — none of which a chronological feed needs. **Trigger to revisit, stated so it is not forgotten: the first customer who asks to *search* or *facet* a timeline rather than scroll it.** ADR-0008 ratifies the technology; it does not schedule it |
| **2** | **Six events now, or wait for the seventh?** | **Six shipped.** A projection that cannot absorb a new kind later is the wrong design regardless, so adding `recommendation.created` when M11 resumes costs one row in `PROJECTIONS` |
| **3** | **Does the timeline reach a customer in M7?** | **Not yet, and it is the module's one real gap.** Lane B's position is that **the account brief is the timeline's home** — *what has happened with this account* belongs beside *what we think about this account* — rather than a menu entry, which [D38](38-product-design-principles.md) retired. That makes it a two-lane build; [C-024](../LANE_COORDINATION.md) |

---

## 8 · Continuing this module

**The test to apply before calling a Timeline slice done, learned from B-301:** *if this were deployed right now, what would write the row?* If the answer is a test, the slice is not finished.

- **Adding an entry kind** is a row in `PROJECTIONS`, a value in `EntryKind`, a subscription — which is now automatic, since registration iterates the table — and a rendering. **The allow-list means the payload contract is explicit**: name the keys or they do not travel.
- **Never add a field Timeline derives itself.** The moment an entry carries something no upstream said, the rebuild property is false and this document's first sentence stops being true.
- **Never make an entry mutable.** There is no `UPDATE` grant and the repository offers no method the database would refuse; a correction is a new entry.
- **The pair to watch is Notifications**, not Timeline's own upstreams. Both project the same events. **Timeline is entity-addressed and immutable; a notification is person-addressed and mutable**, and [ADR-0040 §2](adr/0040-notifications.md) is where that boundary is defined. **A `read_at` column appearing on `timeline_entry` is the convergence beginning.**

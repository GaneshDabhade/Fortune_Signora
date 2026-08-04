# ADR-0403: Signal Engine reads a declaration through its owner's public read port

## Status

**PROPOSED — 2026-08-04, drafted by Lane C — Product Office**, taking ownership of **[C-223](../../LANE_COORDINATION.md)**. **Not ratified, and nothing is implemented.**

> **Scope is C-223 and nothing else.** Lane A reduced the item to facts and stopped; **how the boundary is crossed is Product Office's, and whether it may be crossed is the product owner's.** A new cross-module dependency is 🔴.

## Context

**`signal_engine` cannot see `commercial_profile`'s competitor declaration, and `competitor_entry` cannot be written without it.**

Established by Lane A and verified independently: the declaration is **`commercial_profile`** — aggregate `DeclaredCompetitors`, table `declared_competitors`, migration `0036`, `GET`/`PUT /workspaces/{id}/competitors`, **shipped**. The consumer is **`signal_engine`** — `competitor_entry` is its catalog row, its detection rule and its scoring weight. **The minimal data is the set of declared names and each entry's stable id**, bounded at `MAX_COMPETITORS = 200`. **No dependency path exists in either direction**, and two enforcements each independently prevent one: the `lint-imports` contract, and §5's rule that a cross-module dependency must match an edge already in the graph.

### Four verifications, run before proposing anything

| | Question | Answer |
|---|---|---|
| **1** | **Does an equivalent cross-module pattern already exist?** | ✅ **Yes, and it is exactly this class.** `provider_platform/application/sync_targets.py` imports **`TargetAccountReader`** from `commercial_profile.public` to read the target account declaration |
| **2** | **Can an existing public interface be reused?** | ✅ **The module, the shape and the semantics.** `commercial_profile/public/` already publishes a `View` · `ListView` · `Reader` triple, and **`TargetAccountView` is the shape C-223 asks for**: *"`name` is **exactly what they typed** — unresolved, unnormalised"* and *"`id` is stable across every revision, which is what lets a consumer tell a rename from a remove-and-add"* |
| **3** | **Does an existing event or projection solve this class?** | ✅ **The pattern exists and half of it is not needed here.** `sync_targets.py` states the rule: ***"The event is the trigger and the port is the payload… nothing about accounts travels on the bus, so adding a field to a declaration is never an event-contract change."*** `TargetAccountsChanged` triggers a sync; **`signal_engine` needs no trigger** — see below |
| **4** | **Does a dependency edge already exist elsewhere?** | ✅ **`provider_platform → commercial_profile.public`**, and it is the graph's only `Commercial Profile` edge. **The edge this ADR proposes is new; the mechanism is not** |

### The symmetry that decides the shape

**`signal_engine` already reads per-workspace customer-authored configuration at generation time.** `application/ports.py` declares:

```python
class ProfileRepository(Protocol):
    """Persistence for customer-authored configuration."""
    async def current(self, workspace_id: UUID) -> SignalProfile | None: ...
```

**`None` means the workspace configured nothing and the catalog defaults apply.** `generate.py` resolves it per run.

> **A competitor reader is the same call shape, at the same moment, with the same absent-versus-empty semantics** — and `TargetAccountReader.current()` already draws that distinction for the same reason: *"'they have not told us yet' is a state to wait in, and 'they told us to watch nobody' is an instruction to act on."*
>
> **`signal_engine` therefore learns no new kind of thing.** It learns a second instance of something it already does, resolved the way it already resolves the first.

## Decision

> **A consumer reads a customer declaration through a read port published by the module that owns the declaration, resolved on demand at the moment it is needed.**

**Concretely:** `commercial_profile/public/` gains **`DeclaredCompetitorView`**, **`DeclaredCompetitorListView`** and **`DeclaredCompetitorReader`** — mirroring the target-account triple exactly, including `current(workspace_id) -> …ListView | None`. **`signal_engine` depends on `commercial_profile.public`**, and the composition root injects the implementation, *"so a consumer never learns that this is backed by SQL — and never learns anything else about this module either."*

**What this adds:** **one dependency edge**, `signal_engine → commercial_profile`, matching the existing `provider_platform → commercial_profile` edge in kind.

**What this does not add:** **no new event · no new projection · no new table · no new interface pattern · no new mechanism.** Three types in an existing `public/` module, following a triple that is already there.

### No event, and that is a reduction rather than an omission

**The ratified pattern has two halves — *event as trigger, port as payload* — and this consumer needs only the second.** `provider_platform` needs a trigger because a sync is a *scheduled action* that must start when a declaration changes. **`signal_engine` has no such moment**: detection already runs on `business_event.detected`, and the declaration is *configuration consulted during that run*, exactly as `SignalProfile` is.

> **Adding `CompetitorsChanged` would create a trigger nothing needs.** It is worth stating because the symmetry with target accounts is otherwise tempting, and copying the whole pattern where half of it applies is how machinery accretes.

## Alternatives considered

| | Option | Assessment |
|---|---|---|
| **A** ✅ | **Read port in `commercial_profile/public/`** | **Recommended.** Second instance of the one ratified pattern for this exact class. One edge, no new mechanism |
| **B** | **`signal_engine` declares the port in its own `application/ports.py`; the composition root adapts `commercial_profile.public` behind it** | **The strongest alternative, and it buys something real: no dependency edge at all.** Rejected because **the repository has already placed this reader** — `TargetAccountReader` lives in the *owning* module's `public/`, not in the consumer's ports. **Taking the other route creates two patterns for one question**, and the second reader of a declaration is precisely where a pattern becomes a convention. *(`ProfileRepository` lives in `signal_engine` correctly — `SignalProfile` is signal_engine's own aggregate.)* |
| **C** | **Event + projection into `signal_engine`'s own storage** | **Most machinery for least benefit.** A new event, a new table, a new consumer and eventual consistency, to avoid a read the platform already performs synchronously elsewhere — and it contradicts *"nothing about a declaration travels on the bus"* |
| **D** | **Move the competitor declaration into `SignalProfile`** | **Moves ownership.** A declaration is *"a sentence somebody typed about their own business"* and `commercial_profile` owns those. It would also put a customer's commercial statement inside signal configuration, where a revision would silently rewrite scoring history |
| **E** | **`business_event_engine` performs the join** | **Wrong layer.** It detects *what happened*; whether an adopted technology matters to *this* customer is *what it means*, which the layering places in `signal_engine` |

## Consequences

**Positive.** `competitor_entry` becomes writable. **The declaration stays under one owner**, and adding a field to it is still not an event-contract change. **`signal_engine` resolves it exactly as it resolves `SignalProfile`**, so there is one timing story rather than two. **200 rows per workspace, read once per generation run** — no caching question worth opening.

**Negative, and stated plainly.** **A second module now depends on `commercial_profile`**, which makes that module's `public/` a genuine contract with two consumers rather than one — the point at which its stability starts to matter. **And the `lint-imports` contract must be amended**, which is the mechanical part of a 🔴 change and is not a lane's.

**Neutral.** No event, no projection, no table, no migration. **Nothing downstream of `signal.generated` is affected.**

## Out of scope, deliberately

**Lane A recorded that no existing detection strategy expresses *"only when the adopted technology is one the customer declared"*** — the catalog has `single_event` and `composite`. **That is a `signal_engine`-internal question, not a boundary one**, and it is **not answerable until the data is visible**, which is what this ADR is for. **It needs no ADR and is not bundled here.**

## Compliance

**`Proposed`. Nothing to comply with yet.** On ratification: **`signal_engine` imports from `commercial_profile.public` and nowhere else in that module** — the existing `lint-imports` contract, extended by one entry, is what checks it · **`current()` returns `None` for *never declared*, never an empty list** · **no `CompetitorsChanged` event exists** · **the declaration carries no judgement field**, which is `commercial_profile`'s own standing invariant and unaffected by being read.

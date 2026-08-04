# ADR-0403: Signal Engine reads a declaration through its owner's public read port

## Status

**RATIFIED — 2026-08-04, by the product owner.** Drafted by Lane C — Product Office, taking ownership of **[C-223](../../LANE_COORDINATION.md)**. **Nothing is implemented; this ADR authorises the boundary and records the contract.**

✅ **IMPLEMENTED — verified on `origin/integration` 2026-08-04.** `competitor_entry` is in the signal catalog, `commercial_profile/public/` exports the three types **exactly as §Validation 3 specified**, and `signal_engine/application/generate.py` imports `DeclaredCompetitorReader`. **No import contract was amended**, confirming §Validation 2.

**The dependency graph is updated** — [05-module-dependencies.md](../05-module-dependencies.md) carries the edge, the module table row, the relationship pattern and the synchronous-read entry.

**Five validations were run against source before this status was set** (§Validation). **All five hold, and two of them corrected claims in the first draft** — the change needs **no import-linter amendment**, because the contract that permits it already names `signal_engine`.

> **Scope is C-223 and nothing else.** Lane A reduced the item to facts and stopped; **how the boundary is crossed is Product Office's, and whether it may be crossed is the product owner's.** A new cross-module dependency is 🔴.

## Context

**`signal_engine` cannot see `commercial_profile`'s competitor declaration, and `competitor_entry` cannot be written without it.**

Established by Lane A and verified independently: the declaration is **`commercial_profile`** — aggregate `DeclaredCompetitors`, table `declared_competitors`, migration `0036`, `GET`/`PUT /workspaces/{id}/competitors`, **shipped**. The consumer is **`signal_engine`** — `competitor_entry` is its catalog row, its detection rule and its scoring weight. **The minimal data is the set of declared names and each entry's stable id**, bounded at `MAX_COMPETITORS = 200`. **No dependency path exists in either direction.** ⚠️ **C-223 records two enforcements as preventing one; validation found that only one does** — §5's rule that a cross-module dependency must match an edge already in the graph. **The `lint-imports` contracts already permit this import** (§Validation 2).

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

**Negative, and stated plainly.** **A second module now depends on `commercial_profile`**, which makes that module's `public/` a genuine contract with two consumers rather than one — the point at which its stability starts to matter. **The dependency graph in [05-module-dependencies.md](../05-module-dependencies.md) gains an edge**, which is documentation the ruling produces.

> ⚠️ **Corrected on validation: no `lint-imports` amendment is required.** The first draft of this ADR said the contract *"must be amended."* **It must not** — see §Validation 2. The mechanical cost of this change is **zero**; what remains is the architectural judgement and the graph edge.

**Neutral.** No event, no projection, no table, no migration. **Nothing downstream of `signal.generated` is affected.**

## Validation

**Five checks run against source on 2026-08-04, before this ADR was marked ready.**

### 1 · Every existing consumer follows the same ownership model — with one class of exception, and it is not one

**Exactly one module consumes `commercial_profile`:** `provider_platform/application/sync_targets.py`, importing `TargetAccountReader` from `commercial_profile.public`. **No module reaches `domain`, `application`, `infrastructure` or `interface`.**

**Recorded so the claim is precise rather than absolute:** `apps/api/composition/products.py` and `apps/api/main.py` **do** import `commercial_profile.application`, `.infrastructure` and `.interface`. **That is the composition root doing what it exists for** — *"the only place that may see two modules' infrastructure at once"* — and it is outside every `importlinter` contract by construction, because each names only `modules.*` in `source_modules`. **It is not an exception to the ownership model; it is the place the model is assembled.**

### 2 · No new cycle, and **no contract amendment** — this corrects the first draft

**Two ratified contracts settle it, and neither needs changing.**

> **`"other modules reach commercial_profile only through public/"`** — a `forbidden` contract whose **`source_modules` explicitly names `modules.signal_engine`**, with `commercial_profile`'s four non-public layers forbidden. **`signal_engine → commercial_profile.public` is therefore already permitted**, and the contract's own comment states the intent: *"Nothing consumes it yet, and the contract exists now so that when something does, **it arrives through `public/` rather than by reaching inside**."*

> **`"commercial_profile declares; it never reads the pipeline"`** — `source_modules = ["modules.commercial_profile"]`, **with `modules.signal_engine` among its forbidden modules.** **A cycle is structurally impossible**, enforced independently of this decision.

**Two premises are corrected by this.** [C-223](../../LANE_COORDINATION.md) records that *"the contract… lists the modules it may reach, and `commercial_profile` is not among them"* — **that contract is `type = "forbidden"`, so its list is what `signal_engine` may *not* reach, and `commercial_profile` is absent from it.** And this ADR's own first draft claimed the contract *"must be amended."* **Neither holds.**

> **What remains genuinely new is the *graph*, not the *permission*.** [05-module-dependencies.md](../05-module-dependencies.md) has no `Signal Engine → Commercial Profile` edge, and §5 requires a graph change to be approved first. **The enforcement anticipated this consumer; the documentation has not caught up.** That is what ratification produces.

**No other contract is affected.** Of 34 contracts, the seven mentioning `commercial_profile` are: the layering container, the two above, and four that forbid *other* modules from reaching it or it from reaching them — **none of which this change touches.**

### 3 · The exact public contract to be added

```python
@dataclass(frozen=True, slots=True)
class DeclaredCompetitorView:
    id: UUID          # stable across every revision of the list
    name: str         # exactly what the customer typed — unresolved, unnormalised

@dataclass(frozen=True, slots=True)
class DeclaredCompetitorListView:
    workspace_id: UUID
    competitors: tuple[DeclaredCompetitorView, ...]

class DeclaredCompetitorReader(Protocol):
    async def current(self, workspace_id: UUID) -> DeclaredCompetitorListView | None: ...
```

**Semantics, stated because they are the contract and not the shape:**

| | |
|---|---|
| **`None` vs empty** | **`None` means never declared; an empty tuple means declared as empty.** The same distinction `TargetAccountReader` draws — *"'they have not told us yet' is a state to wait in, and 'they told us to watch nobody' is an instruction to act on"* |
| **`name`** | **Uninterpreted.** Matching it against an adopted technology is the consumer's judgement, exactly as `ProviderRequest.subject` is *"opaque to the platform"* |
| **`id`** | **Stable across revisions**, which is what lets a consumer tell a rename from a remove-and-add |
| **Resolution** | **On demand, per generation run.** No caching contract, no freshness guarantee beyond *the version in force when it was called* |
| **Implementation** | **`commercial_profile/infrastructure/`, injected by the composition root** — *"so a consumer never learns that this is backed by SQL"* |

**`__all__` gains three names. Nothing existing changes.**

### 4 · Why no event, projection, cache or replicated state — on evidence

| | Repository evidence |
|---|---|
| **No event** | `sync_targets.py`: ***"The event is the trigger and the port is the payload… nothing about accounts travels on the bus, so adding a field to a declaration is never an event-contract change."*** `provider_platform` needs a trigger because a sync is a scheduled action. **`signal_engine`'s trigger already exists** — detection runs on `business_event.detected`, and the declaration is configuration consulted *during* that run |
| **No projection or replicated state** | The `timeline` contract states the cost in the repository's own words: a module that could re-derive what an owner already decided *"would be one convenience away from re-deriving meaning the owning module has already decided — and **a second opinion about a fact is how two surfaces start disagreeing about one account**."* **A projected copy of a declaration is a second opinion about what a customer said** |
| **No cache** | **`MAX_COMPETITORS = 200`**, one row-set per workspace, read once per generation run — **and `signal_engine` already performs exactly one such read per run** for `SignalProfile` via `ProfileRepository.current()`, uncached. **A cache here would be a second freshness model for the second thing read at the same moment** |
| **No eventual consistency** | A synchronous read cannot be stale relative to itself. **A projection would introduce a window in which a customer has declared a competitor and detection has not yet seen it** — a window the current design does not have and would have to explain |

### 5 · Compatibility impact — additive only

| | |
|---|---|
| **Existing consumers** | **Unchanged.** `provider_platform`'s use of `TargetAccountReader` is untouched; `__all__` grows and nothing in it is modified |
| **Migration** | **None.** `declared_competitors` and migration `0036` are shipped; this adds a read path over existing rows |
| **Event contracts** | **None.** No event is added, removed or altered. `TargetAccountsChanged` is untouched |
| **Persistence** | **None.** No table, column, index or constraint |
| **Import contracts** | **None** — §Validation 2 |
| **Public API** | **None.** `GET`/`PUT /workspaces/{id}/competitors` are unchanged; this is a module-to-module read |
| **Net** | **Additive only.** Three types, one `__all__` entry set, one graph edge in documentation |

---

## Out of scope, deliberately

**Lane A recorded that no existing detection strategy expresses *"only when the adopted technology is one the customer declared"*** — the catalog has `single_event` and `composite`. **That is a `signal_engine`-internal question, not a boundary one**, and it is **not answerable until the data is visible**, which is what this ADR is for. **It needs no ADR and is not bundled here.**

## Compliance

**`Proposed`. Nothing to comply with yet.** On ratification: **`signal_engine` imports from `commercial_profile.public` and nowhere else in that module** — **the existing `lint-imports` contract already checks this and needs no entry added** · **`current()` returns `None` for *never declared*, never an empty list** · **no `CompetitorsChanged` event exists** · **the declaration carries no judgement field**, which is `commercial_profile`'s own standing invariant and unaffected by being read.

# 409 — The inbound source port — implementation contract

> **Produced by Lane C — Product Office, on the product owner's direction, to resolve [C-326](../LANE_COORDINATION.md).** **This is not a decision and does not reopen one.** [ADR-0300](adr/0300-inbound-customer-systems.md)'s recommendation — *a customer-held system is a source, not a provider* — is the frame; **this document is the contract that follows from it**, specified so Lane B resumes without inventing architecture.
>
> **No code was written.** Every type, column and signature below was checked against source on 2026-08-04.
>
> ⚠️ **[ADR-0300](adr/0300-inbound-customer-systems.md) and [51-implementation-specifications.md](51-implementation-specifications.md) live on `lane-b-commercial-profile`** and do not resolve from this branch until QE merges. **Everything relied on from them is quoted inline**, and every repository fact below was verified against code present here.
>
> **🧊 Frozen on completion.** Scope is [C-326](../LANE_COORDINATION.md) and nothing else.

---

## 1 · What this contract does not change

**Stated first, because it is most of the value.** Downstream of `raw_provider_record`, **nothing changes at all** — normalization, claims, the Knowledge Graph, observations, business events, signals and the score are untouched.

| Already true, verified | Consequence |
|---|---|
| `raw_provider_record.provider` is **`sa.String(64)`** | **A catalog slug stores with no migration** |
| `NormalizeRawRecord` does `self._mappers.get(record.provider)` — **keyed by `str`** | `HubSpotCompanyMapper`, **already built and registered**, receives records the day they land |
| `ProviderRecordReceived.to_payload()` emits **`self.provider.value`** — a string | **The wire contract is already open**; see §6 |
| `ExecutionContext` exists, is tested, and is exported from `integrations/public/` | **The credential hand-off needs nothing new** |
| `Capability` exists in `integrations/domain/catalog.py` | **The source vocabulary has a home and an owner** |

> **Six of the seven firmographic attributes already map with no RFC.** **The first slice of this contract requires no vocabulary addition whatever** — ADR-0300 §3 separates that ruling deliberately, and §5 below shows it is not on the critical path.

---

## 2 · Ownership, and the one line it turns on

| Concern | Module | Why |
|---|---|---|
| **The port, its types, its errors** | **`integrations`** | *A port belongs to the module that owns the language it represents* (`CLAUDE.md` §6). *Connected Account*, *grant*, *scope*, *credential* and *capability* are this module's words |
| **Driving it, watermarks, raw records, events** | **`provider_platform`** | The 2026-08-02 ruling: **Integrations owns the relationship; Provider Platform owns the synchronization** |
| **Interpreting what lands** | **`provider_normalization`** | Unchanged. **It needs no structural change at all** |
| **The adapter implementation** | **`provider_platform/infrastructure/adapters/`** | Beside `simulated/`, where adapters live |

**Dependency direction: `provider_platform → integrations`.** Already the stated direction, and **`integrations` gains no dependency** — it defines a port and does not know who drives it.

---

## 3 · The port

**`modules/integrations/domain/source.py`, exported through `public/`.**

```python
class IntegrationSourceAdapter(Protocol):
    def describe(self) -> IntegrationSourceDescriptor: ...
    async def fetch(self, request: IntegrationFetchRequest) -> IntegrationPage: ...
```

**Two methods, deliberately** — the same narrowness `ProviderAdapter` argues for: *"a wider port would need every future vendor to implement methods most of them do not have, and the usual outcome is adapters raising `NotImplementedError` — which is a contract that lies."*

### The types

```python
@dataclass(frozen=True, slots=True)
class IntegrationFetchRequest:
    context: ExecutionContext        # workspace, connection, endpoint, scopes, credential
    capability: Capability           # integrations/domain/catalog.py — NOT ProviderCapability
    since: datetime | None = None    # incremental watermark; None requests a full snapshot
    cursor: str | None = None        # opaque, interpreted only by the adapter
    limit: int = 100                 # adapters may return fewer, never more

@dataclass(frozen=True, slots=True)
class IntegrationRecord:
    external_id: str                 # the customer's system's own id, for dedup
    occurred_at: datetime            # when the described thing happened, per the source
    payload: dict[str, Any]          # untrusted, untyped — normalization validates it

@dataclass(frozen=True, slots=True)
class IntegrationPage:
    records: tuple[IntegrationRecord, ...]
    next_cursor: str | None = None
    has_more: bool = False
```

**Three differences from the Provider Port, and each is the reason a sibling exists rather than an extension:**

| | |
|---|---|
| **No `subject`** | **This is the whole distinction.** A provider is asked *about one company*; a source is asked for *the customer's own records*. An enumeration has no subject |
| **`context` replaces nothing — it is additive** | A provider adapter holds Signora's credential from the composition root. **A customer's credential is per workspace, per connection, and expires**, so it travels with the request |
| **`IntegrationRecord` carries no `provider`** | `ProviderRecord` does, because the adapter knows which supplier it is. **Here the slug is on `context.integration`** — one authoritative place, and the record cannot disagree with the connection it came from |

> **`next_cursor` and `has_more` stay separate**, for the reason `ProviderResponse` already gives: *"a provider legitimately returns a cursor with no further records, and conflating them produces an extra empty request per sync."*

### Capability — reuse, not a new enum

**Use `integrations.domain.catalog.Capability`.** It already exists, already means *"what connecting a system gives Signora"*, is already owned by the right module, and already has the `LIVE_CAPABILITIES` guard that stops the Connection Center promising what the pipeline cannot do.

**E1 adds one member: `CRM_RECORDS = "crm_records"`** — accounts and opportunities, the read [D3](51-implementation-specifications.md) needs. **A row in an existing table, by that module's own design.** `CRM_ACTIVITY` remains what it always was and is not what E1 reads ([401](401-epic-e1-crm-read.md) §5).

> **Do not use `ProviderCapability`.** It enumerates what *suppliers* sell — `COMPANY_ENRICHMENT`, `TECHNOGRAPHICS`, `WORKFORCE` — and a CRM read is none of them. **Two vocabularies, two owners, and the type system keeps them apart.**

### Errors

**Mirror the Provider Port's hierarchy exactly**, in `integrations/domain/source.py`:

```
IntegrationSourceError
├── IntegrationSourceTransientError      → SyncFailureKind.TRANSIENT
├── IntegrationSourceRateLimitedError    → SyncFailureKind.TRANSIENT
├── IntegrationSourcePermanentError      → SyncFailureKind.PERMANENT
│   └── IntegrationCapabilityUnsupportedError
└── IntegrationPayloadInvalidError       → SyncFailureKind.PERMANENT
```

**`SyncFailureKind` is reused unchanged** — it is deliberately coarse, because *"the platform's decision is only resume later or stop and alert."*

**One case the Provider Port has no equivalent for, and it must not be swallowed:** **a connection that is revoked, expired or disconnected.** `ExecutionContext` resolution already raises **`ConnectionUnusable`**, and it is **not** an adapter error — **it is resolved before `fetch` is called, and the sync never starts.** A revoked connection is a customer decision, not a failure.

### The wrapper — how a vendor fetcher becomes the port

**Added 2026-08-04 on new repository evidence.** Lane B has built **`integrations/infrastructure/hubspot.py` — `HubSpotCompanies`**, and it deliberately *"holds no port, publishes no event, writes no row."* **The wrapper is the seam between it and §3**, and it is the last thing E1 needed specified.

**`modules/integrations/infrastructure/hubspot_source.py`:**

```python
class HubSpotCompanySource:                      # implements IntegrationSourceAdapter
    def __init__(self, companies: HubSpotCompanies) -> None: ...

    def describe(self) -> IntegrationSourceDescriptor: ...

    async def fetch(self, request: IntegrationFetchRequest) -> IntegrationPage: ...
```

**Four responsibilities, and nothing else.** It is a translation layer; **it fetches nothing and decides nothing.**

| # | Responsibility | Contract |
|---|---|---|
| **1** | **Unwrap the credential** | `request.context.credential.material` → `access_token`. **The wrapper is the only place `ExecutionContext` meets a vendor client**, which is what keeps `HubSpotCompanies` ignorant of connections |
| **2** | **Pass through the loop parameters** | `since` · `cursor` · `limit` map **one-to-one** onto `HubSpotCompanies.page(...)`. **No reinterpretation** — the fetcher already owns *which endpoint runs*, and a wrapper that chose would reimplement the choice |
| **3** | **Lift each payload into `IntegrationRecord`** | §below — **the only place vendor field names appear in this direction** |
| **4** | **Translate the error hierarchy** | `CrmReadError` → `IntegrationSourceError`, one-to-one (§below) |

#### Lifting a payload — the two fields the port requires

`CompanyPage.records` is `tuple[dict[str, Any], ...]` — raw HubSpot objects. `IntegrationRecord` requires `external_id` and `occurred_at`, and **extracting them is vendor knowledge, so it belongs here and not in the runner:**

| Port field | From | Rule |
|---|---|---|
| `external_id` | `payload["id"]` | **Required.** Absent ⇒ `IntegrationPayloadInvalidError` — a record with no identity cannot be deduplicated |
| `occurred_at` | `payload["properties"]["hs_lastmodifieddate"]` | **Required.** Absent ⇒ `IntegrationPayloadInvalidError`. It is the field the watermark advances on, and **guessing `now()` would make every backfill look like today** |
| `payload` | the object **unchanged** | **Nothing is stripped, renamed or normalised.** Interpretation is `HubSpotCompanyMapper`'s |

> **`occurred_at` is `hs_lastmodifieddate`, and that is the same field the fetcher filters on** — *"`GT`, not `GTE`… a record modified in the same millisecond as the previous boundary was already delivered."* **Watermark, filter and record timestamp must be one field, or a sync re-reads or skips.** This is the single most important line in the wrapper.

#### Error translation

| `HubSpotCompanies` raises | Wrapper raises | Resulting `SyncFailureKind` |
|---|---|---|
| `CrmRateLimited` *(carries the vendor's own wait)* | `IntegrationSourceRateLimitedError`, **wait preserved** | `TRANSIENT` |
| `CrmTransient` | `IntegrationSourceTransientError` | `TRANSIENT` |
| `CrmCredentialRejected` | `IntegrationSourcePermanentError` | `PERMANENT` |
| `CrmPermanent` *(missing permission)* | `IntegrationSourcePermanentError` | `PERMANENT` |
| `CrmPayloadInvalid` | `IntegrationPayloadInvalidError` | `PERMANENT` |

> **Lane B's separation is preserved and must not be collapsed:** *"a rejected credential is separate from a missing permission, because **reconnecting fixes one and not the other**."* Both map to `PERMANENT` for the *platform's* retry decision — **and the distinct types survive to the surface that tells a customer what to do.**

#### Who supplies the properties — the composition root, from the mapper

**`HubSpotCompanies.__init__` takes `properties: frozenset[str]`, and `HubSpotCompanyMapper.translated_properties()` publishes exactly that set** — *"a CRM returns only the properties you ask for. A mapper that knows `industry` and a client that never requests it produce a claim that silently never appears, and nothing fails."*

> **Contract: the composition root wires `HubSpotCompanies(properties=HubSpotCompanyMapper.translated_properties())`.** **Neither the wrapper nor the runner may hold a property list** — a second copy is the defect Lane B's own test was written to catch, and duplicating it here would defeat that test by putting the truth in a third place.
>
> **This is the one edge in the contract that crosses modules** — `integrations` fetching, `provider_normalization` declaring. **It is a composition-root wiring, not an import**: `integrations` does not depend on the mapper, and `apps/api/composition/` is *"the only place that may see two modules' infrastructure at once."*

#### `IntegrationSourceDescriptor`

```python
@dataclass(frozen=True, slots=True)
class IntegrationSourceDescriptor:
    integration: str                       # the catalog slug — "hubspot"
    capabilities: tuple[Capability, ...]   # what this source can be asked for
```

**Deliberately smaller than `ProviderDescriptor`.** A provider descriptor carries qualification metadata because a provider is a supplier Signora chose; **a source is a system the customer chose, and Signora qualifies nothing about it.**

---

## 4 · The use case

**`modules/provider_platform/application/run_integration_sync.py`, beside `run_sync.py`.**

```python
@dataclass(frozen=True, slots=True)
class RunIntegrationSyncInput:
    workspace_id: UUID
    connected_account_id: UUID       # replaces `subject` — the honest key for an enumeration
    capability: Capability
    incremental: bool = True
    page_size: int = 100
```

**It writes exactly what `RunProviderSync` writes:** `raw_provider_record` rows with `provider = context.integration` *(the catalog slug)*, and publishes **`provider.record.received`** unchanged. **Pagination is the caller's loop**, as it already is. **Pacing, sync history and failure classification are reused as they stand.**

### The watermark

**`provider_watermark` is `(workspace_id, provider, capability, subject)`** after [migration 0029](../../backend/migrations/versions/0029_watermark_per_subject.py) — and Lane B is right that **`subject` has nothing truthful to hold for an enumeration.**

> **Contract: `subject` holds the `connected_account_id`, and the column's documented meaning widens from *"the company this position is about"* to *"the scope this position is for."*** For a provider sync that scope is a company; for an integration sync it is a connection. **One tuple, still unique, still truthful.**
>
> **No migration, and that is the argument.** The alternative — a nullable `connected_account_id` column — makes the unique constraint depend on NULL semantics, which Postgres treats as distinct, **so two full-snapshot rows for one connection would both be permitted.** A widened `subject` cannot express that.
>
> **The widening must be written into `0029`'s successor documentation and the column's model docstring**, or the next reader inherits the old meaning. **B-004's lesson is exactly this class**: a position shared between two things that silently skips records.

---

## 5 · Vocabulary, lifecycle, events, boundaries

**Vocabulary — nothing is required for slice one.** `HubSpotCompanyMapper` already maps six firmographic attributes onto existing `ClaimAttribute` members with no RFC. **Commercial attributes — *is already a customer*, contract value, renewal date, stage — are out of scope here and out of scope for claims entirely** ([ADR-0401](adr/0401-a-customers-crm-is-not-a-provider.md), amended): they are workspace-scoped facts, never evidence about the world. **ADR-0300 §3's separate ruling is therefore not on E1's critical path.**

**Lifecycle.** `ConnectionState` governs whether a sync may start; **`ProviderSync` governs the run.** They are already separate lifecycles and stay so — *"a healthy connection can have a failed sync, and a revoked grant can have a completed one."*

**Events.** `ProviderSyncStarted` · `ProviderRecordReceived` · `ProviderSyncCompleted` · `ProviderSyncFailed`, **all unchanged in name, payload and consumer.**

> **One annotation widens, and nothing else.** These carry `provider: ProviderName`, a closed enum a catalog slug cannot construct. **`to_payload()` already emits `self.provider.value` — a string — so the wire contract is open today.** Widening the four dataclass fields to `provider: str` **changes no payload, no consumer and no test that reads the wire.** `ProviderName` stays closed and keeps meaning *"a supplier with a ratified qualification record"*; **it simply stops being the type of a field that must also hold a slug.**

**Boundaries — four, and each is a test rather than a sentence:**

1. **`integrations` imports nothing from `provider_platform`.** The port is defined by the module that owns its language; the driver depends on the port.
2. **No `ProviderName` member is ever added for a customer system.** A CRM is not a supplier.
3. **Python performs no authorization-code exchange.** Acquisition stays in Next ([18-authentication.md](18-authentication.md), [44-integrations.md](44-integrations.md) §5) — **this contract touches only refresh and read**, both credential *management*.
4. **No commercial CRM field becomes a `ClaimAttribute`.** Pinned by the test `HubSpotCompanyMapper` already carries.

---

## 6 · Implementation sequence

| # | Step | Module | Budget | Gated on |
|---|---|---|---|---|
| **1** | **The port, its types and its errors** | `integrations` | 🟠 | **Nothing — ready now** |
| **2** | **`Capability.CRM_RECORDS`**, and whether it is `LIVE` | `integrations` | 🟢 | Step 1 |
| **3** | **Widen `provider: ProviderName` → `str`** on the four sync events | `provider_platform` | 🟢 | Nothing |
| **4** | **`RunIntegrationSync`** + the watermark widening and its documentation | `provider_platform` | 🔴 | Steps 1–3 |
| **5** | **A `simulated` source adapter**, proving the path end to end with no vendor | `provider_platform` | 🟠 | Step 4 |
| **6** | **`HubSpotCompanySource`** — the wrapper (§3), wired to `HubSpotCompanies` | `integrations` | 🟢 | Steps 1–2 |
| **7** | **Composition-root wiring**, properties from `HubSpotCompanyMapper.translated_properties()` | `apps/api` | 🟢 | Steps 4 · 6 · **developer application** to run against the vendor |

> **The wrapper is 🟢 and depends on no ruling.** `HubSpotCompanies` is built and tested; §3's wrapper is translation only, and **Lane B can write it the moment steps 1–2 exist.**

> **Step 5 is the one to insist on, and it is the same argument [401](401-epic-e1-crm-read.md) §8 makes about the consumption edge.** A simulated source adapter drives the whole path — port, use case, watermark, raw record, event, `HubSpotCompanyMapper`, claims — **with no vendor, no credential and no developer application.** It is the only step that proves the contract before anything external is involved, and **a lane that merges 5 and 6 debugs OAuth and the ingestion path at once.**

**Steps 1–6 need nothing from the product owner.** **Only step 7's live run against the vendor needs the developer application**, which is environmental and already recorded — and steps 1–6 are verifiable without it.

> ⚠️ **Step 4 is 🔴 and touches `provider_platform`, which is in Implementation Waiting on [C-021](../LANE_COORDINATION.md).** **That is an assignment question, not an architectural one** — the contract is complete either way, and who executes step 4 is the product owner's.

---

## 7 · What this contract deliberately excludes

**Simulation provenance.** `ProviderResponse` carries `simulated` and `ReplayContext`; `IntegrationPage` does not. **A customer's CRM is not replayable from a scenario manifest**, and adding the fields to satisfy symmetry would put a concept in the port that no real source can populate. **Step 5's simulated adapter is a test double, not the Provider Simulation Framework.**

**Write-back.** [E2](406-epic-e2-crm-write-back.md)'s territory. **This port is read-only, and `fetch` is its only verb.**

**The commercial vocabulary ruling.** ADR-0300 §3, and **not on E1's critical path** (§5).

**Anything about who implements which step.** §6's budget column states cost, not ownership.

---

## 8 · Definition of done

**Done when a record from a customer's own system reaches `HubSpotCompanyMapper` through the same `raw_provider_record` row a provider writes** — and when nothing downstream can tell the difference.

**Gates:** `integrations` imports nothing from `provider_platform` · no `ProviderName` member added · the four events' payloads are byte-identical to today's · **a simulated source adapter drives the full path with no vendor credential** · the watermark's widened meaning is documented where `0029` documented the old one · **no commercial CRM field reaches `ClaimAttribute`** · `LIVE_CAPABILITIES` refuses to advertise `CRM_RECORDS` until step 4 lands.

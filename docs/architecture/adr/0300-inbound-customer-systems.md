# ADR-0300: How a customer's own system delivers evidence into the pipeline

> **Status: PRODUCT OWNER APPROVED — 2026-08-04. Option A.** ⚠️ **Awaiting integration synchronization** — this ruling is not yet recorded on `origin/integration`, and the lifecycle that distinguishes the two is [`PRODUCT_OFFICE.md`](../../PRODUCT_OFFICE.md) §11c: **a decision is authoritative when the product owner rules it, and *recorded* when `integration` carries it.**
>
> **The implementation proceeded on the product owner's explicit standing instruction** — *"a product owner decision authorizes implementation; integration synchronization authorizes repository convergence, and implementation should not remain idle solely because synchronization has not completed."* **The work is held on `lane-b-commercial-profile` until Product Office's synchronization reaches `integration`** and normal QE promotion follows.
>
> *Original note, kept because a dated record is not rewritten (§2):* **Written by Lane B, 2026-08-04**, on being assigned Epic E1 (CRM OAuth and read) and finding that **no path exists for a customer-held system to reach the intelligence pipeline.** It was proposed rather than accepted because every option below is 🔴 — a ratified port, a closed domain type, or the canonical vocabulary — and none of those is a coding session's to decide (`CLAUDE.md` §20e). **Nothing was built against any option while it was open**; Epic E1's read stopped at this document, which is what an architectural blocker requires: *"implementation stops, architecture discussion begins."* **It stopped for eleven hours and everything around it shipped meanwhile** — interpretation, acquisition, the grant lifecycle and the vendor read all reached `main` on the same day.

---

## Context

**Epic E1's specification calls it *"the single highest-leverage integration in the roadmap"*, and estimates it as reduced from XL to L on the grounds that *"what remains is the read, not the plumbing."*** That estimate assumed the inbound plumbing could carry a CRM. **It cannot, and this document is the measurement.**

### What already exists, and it is most of the acquisition half

[44-integrations.md](../44-integrations.md) records the module as *as built, and paused*: `ConnectedAccount`, `IntegrationGrant`, `Credential`, the lifecycle, encrypted credential storage, the catalog, the Connection Center, and the OAuth start and callback routes at the frontend edge. **`ResolveExecutionContext` already turns a connection into an `ExecutionContext`** — endpoint, scopes and credential, with the lifecycle checks in front of it — and it is complete, tested, published through `public/`, and deliberately unwired, because nothing consumes it.

**The pipeline behind it also exists, in full:**

```
adapter.fetch()  →  raw_provider_record  →  provider.record.received
                 →  mapper  →  claim  →  claim.recorded
                 →  Knowledge Graph  →  Observation  →  Business Event  →  Signal  →  Buying Score
```

### And the two halves cannot be joined

**Measured against the code, not inferred from the documents.**

| # | The obstruction | Where |
|---|---|---|
| **1** | **`ProviderName` is a closed `StrEnum`** — `apollo`, `builtwith`, `crunchbase`, `coresignal`, `bombora`, documented as *"providers with a ratified qualification record."* `ProviderRecord.provider` and `ProviderRegistry` are both typed by it. **A CRM slug is unconstructable**, which is the type system working exactly as §2 asks it to | `provider_platform/domain/provider.py` |
| **2** | **`ProviderCapability` has no CRM member** — company enrichment, technographics, capital events, workforce, behavioural intent | same |
| **3** | **`ProviderRequest` carries no connection.** A provider adapter holds Signora's own credential, configured once at the composition root. **A customer-held credential is per workspace, per connection, and expires** — there is nowhere to put it | same |
| **4** | **`ProviderRequest.subject` is required, and a CRM sync has no subject.** Providers are asked *about one company*; a CRM is asked *for the customer's accounts*. The watermark is keyed `(workspace, provider, capability, subject)`, so a CRM sync has nothing truthful to put in the fourth column | same · `provider_watermark` |
| **5** | **`ClaimAttribute` has no CRM concept** — nothing for *is already a customer*, *contract value*, *renewal date*, *opportunity stage* or *last activity*, and `ClaimDomain` has no commercial or relationship domain. The file says **RFC required to extend** | `provider_normalization/domain/vocabulary.py` |
| **6** | **No HubSpot developer application exists** — no client id, no client secret, no registered redirect URI. **Environmental, and the product owner's**, named as such in E1's own specification and in [44-integrations.md](../44-integrations.md) §9 | — |

### One thing that is not an obstruction, and it matters

**`NormalizeRawRecord` keys its mappers by `provider: str`, and `raw_provider_record.provider` is `String(64)`.** The canonical shape is already open to a system that is not one of the five. **No second normalization path is required**, which is the constraint Epic E1's assignment named first — a CRM mapper is one more `ProviderMapper` subclass, and nothing about it is special.

**So the gap is narrower than it looks: it is entirely in *acquisition of records*, and not at all in *interpretation of them*.**

### What the ratified architecture already says

[13-integrations.md](../13-integrations.md) lists CRM's use case as *"sync opportunities/recommendations outward; **pull CRM-native activity as an observation source**"* — so an inbound read is in scope and always was. Its onboarding procedure then says, as step 1:

> **Confirm the port exists on the relevant consuming module, or define a new one via RFC.**

**No such port exists, and no consuming module is named.** The ratified document routes this decision to an RFC by its own instruction, which is this one.

---

## Decision

**PRODUCT OWNER APPROVED — 2026-08-04. Option A: the sibling source port. Awaiting integration synchronization.**

> **Recorded here, not decided here.** The ruling is the product owner's, taken on 2026-08-04 alongside [ADR-0401](0401-a-customers-crm-is-not-a-provider.md) and recorded in [`DECISION_PACKS.md`](../../DECISION_PACKS.md); this status is the ADR catching up with a decision that already exists. **[C-326](../../LANE_COORDINATION.md) is answered by it**, and [409](../409-inbound-source-port-contract.md) is the implementation contract that follows.
>
> **The word *ratified* was used here first and was wrong** — not about the decision, which is real, but about the repository, which does not yet record it. **A cold session reading `RATIFIED` reasonably assumes `integration` agrees**, and until the merge it does not (§11c).
>
> **§3 remains unruled and is deliberately separable** — what a CRM contributes to the canonical language is its own question, and [409 §5](../409-inbound-source-port-contract.md) measured it as **not on E1's critical path**: `HubSpotCompanyMapper` needs no vocabulary extension.

> **A customer-held system is a *source*, not a *provider*, and it delivers into the same pipeline through a port of its own.**

Three parts, and the third is separable from the first two.

### 1 · A sibling port, owned by Integrations

`IntegrationSourceAdapter` is defined in `modules/integrations/domain/` and published through `public/` — **because a port belongs to the module that owns the language it represents** (`CLAUDE.md` §6), and *Connected Account*, *grant*, *scope* and *credential* are this module's words. It takes the `ExecutionContext` that already exists:

```
describe() -> IntegrationSourceDescriptor
fetch(IntegrationFetchRequest) -> IntegrationPage
```

`IntegrationFetchRequest` carries the **`ExecutionContext`**, a capability, `since`, `cursor` and `limit` — and **no subject**, because enumerating a customer's own records is what makes this different from asking a vendor about one company. Failure outcomes mirror the Provider Port's exactly: transient, rate-limited, permanent, payload-invalid, capability-unsupported.

**`ProviderName` is left closed.** It keeps meaning *"a supplier with a ratified qualification record"*, which is a guarantee worth more than the convenience of one shared enum.

### 2 · Provider Platform runs it, and writes what it already writes

Synchronization stays where [44-integrations.md](../44-integrations.md) §1 put it, on the product owner's own 2026-08-02 ruling: **Integrations owns the relationship, Provider Platform owns the synchronization**, and the dependency runs `provider_platform → integrations`, enforced by an import contract.

Provider Platform gains a use case beside `RunProviderSync` that drives the new port and **writes the same `raw_provider_record` rows and publishes the same `provider.record.received`.** Downstream of that row, *nothing changes at all* — normalization, claims, the Knowledge Graph, observations, events, signals and the score are untouched.

**Watermarks key on the connection rather than a subject**, which is the honest key for an enumeration and needs `provider_watermark` to accept it.

### 3 · The vocabulary extension is a separate ruling

**What a CRM contributes to the canonical language is its own question**, and it should not be smuggled in beneath a plumbing decision. It is listed under *Consequences* and deliberately not decided here.

---

## Alternatives Considered

| Alternative | Why not |
|---|---|
| **Extend the Provider Port** — add CRM slugs to `ProviderName`, a CRM `ProviderCapability`, and a connection reference to `ProviderRequest` | **The cheapest option and the one that costs the most later.** It reuses the runner, the watermarks, the raw records and the events with no new port at all. But it deletes the sentence the module boundary was built on — *"a provider is Signora's supplier and Signora holds the credential; an integration is the customer's own system and the customer holds it"* — and it opens a closed type whose closure is a real guarantee. **Every adapter would then have to answer *"is my credential mine or the customer's?"*, and nothing in the type would make the wrong answer impossible.** `ProviderRequest.subject` would also have to become optional for every provider so that one caller could omit it |
| **A second ingestion path owned entirely by Integrations** — its own read port, its own raw-record store, its own sync runner, its own watermarks | **Buildable today by one lane with no cross-module dependency, which is exactly what makes it tempting.** It is *two* sync runners, *two* watermark stores and *two* raw-record tables for one concept — **truth with two authoritative representations** (§2), and the second copy is the one nobody maintains. It also duplicates pacing, pagination bounds, failure classification and sync history, all of which already exist and are tested |
| **Bypass raw records — Integrations produces claims directly** | Removes the storage duplication above, and breaks the rule that makes evidence defensible: **every claim cites a raw record.** A claim with no stored payload behind it cannot be re-normalized when a mapper improves, cannot be replayed, and cannot be shown to a customer as *"this is what your CRM actually said"* |
| **Wait for the HubSpot developer application and decide then** | The credential is genuinely required before anything can be *demonstrated*, and it is not required to decide *any* of the above. **Deferring the architecture until the credential arrives means deciding it under time pressure**, which is how a plumbing decision quietly becomes a vocabulary decision |

---

## Tradeoffs

| We gain | We give up |
|---|---|
| **One ingestion path.** Raw records, watermarks, pacing, sync history, failure classification, events and the whole downstream pipeline are reused unchanged | **A second port to maintain**, deliberately parallel to the Provider Port and free to drift from it |
| **The boundary sentence survives.** A customer-held credential never leaves `integrations`, and `ProviderName` keeps meaning what it says | **Provider Platform learns that customer systems exist**, where today it knows only suppliers |
| **The port lives with its language** (§6), so `ExecutionContext` — already built — becomes the thing an adapter takes | **Two use cases in Provider Platform** doing recognisably similar work, which will invite a premature generalization at least once |
| **The vocabulary question stays visible** rather than arriving inside an implementation | **E1 needs two rulings, not one**, and cannot ship on the first alone |

---

## Risks

| Risk | Mitigation |
|---|---|
| **The two ports drift**, and a fix applied to one is forgotten in the other | A shared contract test suite, exactly as [20-provider-simulation.md](../20-provider-simulation.md) principle 8 already does for simulated and production provider adapters |
| **The vocabulary extension becomes the real work**, and is larger than the plumbing | It is separated here for that reason. **Part 3 can be ruled on independently and can arrive later**; a connection that syncs and produces rejections is still a connection that demonstrably works |
| **Nothing can be demonstrated until a developer application exists**, so the architecture ships unexercised | **Do not build it unexercised.** The simulation framework proves the pipeline against the Provider Port today; whether it can serve this port is a design question inside part 1, and if it cannot, **this work should wait for the credential rather than ship untested** |
| **`connectable: false` becomes true before it is true** | An API test already asserts every catalog entry is `connectable: false`. **It flips only after a real handshake has succeeded** ([44](../44-integrations.md) §9 step 4), and never in anticipation |

---

## Migration Strategy

**If this decision proves wrong, the reversal is small, and that is a deliberate property of it.**

The new port has one implementation and one caller. Reversing to *"extend the Provider Port"* means deleting the port, moving the adapter behind `ProviderAdapter`, and widening `ProviderName` — **and every row already written stays valid**, because `raw_provider_record.provider` is a string and the mapper is keyed by one. **No data migration, no re-normalization, no claim rewritten.**

That is the strongest argument for deciding this now rather than later: **the cost of being wrong is bounded and known, and it grows only after the first customer connects.**

---

## Consequences

**What this requires of the rest of the system, stated so the ruling is made with the whole cost visible.**

| # | Consequence | Budget | Whose |
|---|---|---|---|
| 1 | A new port and its types in `integrations/domain` and `public/` | 🟠 | Lane B |
| 2 | A use case in `provider_platform` that drives it, and a watermark keyed on a connection | 🔴 — a module another lane is assigned | **Product owner**, then that module's assignee |
| 3 | **New `ClaimAttribute` members and probably a new `ClaimDomain`** for what a CRM asserts | 🔴 — *"RFC required to extend"* | **Product owner**, its own ruling |
| 4 | A HubSpot adapter, and a mapper registered under `"hubspot"` | 🟢 / 🟠 | Lane B |
| 5 | **A HubSpot developer application** — client id, client secret, registered redirect URI | environmental | **Product owner**. Nothing can be demonstrated without it |
| 6 | `06-events.md` gains nothing — **the same `provider.record.received` carries these records** | — | — |

> **Five of the six were already written down before Epic E1 was assigned.** [44-integrations.md](../44-integrations.md) §9 named the missing developer application and recorded *"nothing synchronizes; the first consumer is Provider Platform, and it has not arrived."* [13-integrations.md](../13-integrations.md) named the missing port and said an RFC defines it. **What this document adds is the measurement that the existing port cannot be reused, and a shape that does not require inventing a second pipeline.**

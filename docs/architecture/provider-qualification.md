# Provider Qualification Register

> Status: **Living document** — updated whenever a provider's status changes
> Governed by the payload provenance rule in [20-provider-simulation.md](20-provider-simulation.md)
> Revision: **v2** — M2.0 · T34 · assessed 2026-07-28; development fixtures approved

## The rule

A simulated payload's shape must originate from one of four sources:

1. Official vendor documentation
2. Vendor sandbox responses
3. Recorded test-account responses
4. Sanitized production responses

**If none is available, the provider is not implemented with an authentic payload.** A fabricated schema produces a normalizer that works perfectly against the fabrication and fails against the vendor — discovered during a paid integration, after every downstream stage has assumed the shape.

## Statuses

| Status | Meaning | Consequence |
|---|---|---|
| **Qualified** | A permitted source is in hand and recorded below | Generator may be implemented |
| **Conditional** | Architecture settled; a legitimate payload source still required | That generator waits. **Nothing else does.** |
| **Deferred** | Not pursued this phase, reason recorded | Stays in the roadmap; implementable later with **no architectural change** |

A Conditional or Deferred provider never blocks the milestone — see Provider Independence (principle 9).

---

## Approved temporary strategy — development fixtures

**Approved 2026-07-28.** To unblock architecture validation, each provider has a **development fixture** generator: a representative structure covering the *kind* of information that provider is expected to expose. These exist to exercise the Provider Port, adapters, scenario engine, and — from M2.1 — normalization and the pipeline beyond it.

**The provenance policy is unchanged.** No fixture is presented as an authentic payload:

- Every generator declares `PayloadProvenance.DEVELOPMENT_FIXTURE`, asserted by test.
- Every payload body carries a `_fixture` field naming itself as **not** an authentic payload — inside the body, so a payload copied into a bug report or a demo carries its own warning.
- Ingestion logs mark the provenance of every emitted payload.
- A generator falsely claiming authenticity fails the suite; verified by making one claim it.

### Replacement procedure

When a legitimate artifact arrives for a provider:

1. Replace the fixture shape in that provider's generator (**one file**).
2. Update normalization if the real shape differs.
3. Set `provenance` to the matching source and record `source_reference`.
4. Remove the `_fixture` field from the payload body.
5. Re-run the shared contract suite.
6. Re-run all scenario assertions.
7. Update this register: `Conditional` → `Qualified`.

The architecture does not change. That is the design constraint the fixtures were built under: a generator owns only the shape it emits and the mapping into it, so nothing else in the system knows either.

## Assessment — 2026-07-28

| Provider | Category | Status | Source in hand | Generator |
|---|---|---|---|---|
| Apollo | Company enrichment | 🟡 **Conditional** | None | ⚠️ Development fixture |
| BuiltWith | Technographics | 🟡 **Conditional** | None | ⚠️ Development fixture |
| Crunchbase | Capital events | 🟡 **Conditional** | None | ⚠️ Development fixture |
| CoreSignal | Workforce | 🟡 **Conditional** | None | ⚠️ Development fixture |
| Bombora | Behavioural intent | 🟡 **Conditional** | None | ⚠️ Development fixture |

**Every generator is a development fixture.** Status stays `Conditional` until a legitimate artifact replaces it — a fixture existing does not qualify a provider, and conflating the two would make the register a record of what was built rather than of what is trustworthy.

**No provider is Qualified.** The repository contains no vendor documentation extract, no sandbox credentials, no recorded test-account response, and no sanitized production capture. A search for any of the five vendors across the codebase returns only roadmap and architecture prose.

### Why not "Qualified" from general knowledge

Each of these vendors publishes API documentation, and an approximate response shape could be written from recollection of it. **That is not one of the four permitted sources**, and treating it as one would defeat the rule rather than satisfy it:

- It cannot be cited to a documentation version, so a future reader cannot tell what it was derived from or whether the vendor has since changed it.
- It cannot be diffed against the real response when one eventually arrives.
- It would look identical, in the codebase, to a properly-sourced schema — which is the specific failure the rule exists to prevent. A wrong shape that *looks* sourced is worse than an absent one, because nobody re-checks it.

An approximate shape is a **guess wearing the costume of provenance**. The rule's whole point is that the costume is not available.

### Why not "Deferred"

Deferred implies a decision not to pursue. These five are all approved and wanted; what is missing is an artifact, not a decision. **Conditional** states the position accurately: the architecture is settled, the generator is specified, and one obtainable input is outstanding.

---

## What each provider needs

Any **one** of the following unblocks a given provider. None requires a paid contract.

| Provider | Cheapest sufficient artifact |
|---|---|
| **Apollo** | A saved response from the documented `/organizations/enrich` endpoint (free tier available), or the documentation page captured to the repo |
| **BuiltWith** | A saved response from the free `/v20/api.json` domain lookup, or its documentation capture |
| **Crunchbase** | A saved `/entities/organizations/{id}` response from the Basic tier, or an ODM documentation capture |
| **CoreSignal** | A sandbox or trial response for company and employee-change endpoints |
| **Bombora** | A Company Surge® delivery sample — a **weekly time series**, not a single snapshot, since the trajectory is the thing being simulated |

**Format for a supplied artifact:** JSON committed under `backend/signora_platform/simulation/provenance/<provider>/`, with a sibling `SOURCE.md` naming which of the four categories it is, where it came from, and the date. Sanitized: no real company names, no contact PII, no API keys.

---

## Impact of the current state

**The framework is unaffected.** Provider Independence means the Provider Port, contract test suite, safety guards, dataset store, virtual clock, scenario engine, fault injector, delivery mechanism, and observability are all provider-agnostic. They are implemented in M2.0 regardless of qualification outcomes.

**What waits:** replacing the five fixtures with authentic payloads. Everything else — generators, adapters, the shared contract suite, scenario assertions — is built and green against fixtures.

**Bombora specifically.** Its fixture models the property that matters — a *trajectory*, not a snapshot — so the behavioural-intent pathway is exercised end to end: emergence, sustain, decay, reactivation, concurrent topics, and noise are each asserted. What remains unverified is whether the real payload carries a weekly history at all, or requires the platform to accumulate one. **That is the single most consequential thing an authentic Bombora artifact would tell us**, and it is a design input rather than a shape detail.

---

## Change log

| Date | Change |
|---|---|
| 2026-07-28 | v2 — development fixtures approved as a temporary strategy. All five remain **Conditional**; each now has a fixture generator, clearly designated. Replacement procedure recorded. |
| 2026-07-28 | v1 — initial assessment. All five Conditional; no permitted source present in the repository. Required artifact named per provider. |

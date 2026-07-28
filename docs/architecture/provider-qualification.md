# Provider Qualification Register

> Status: **Living document** — updated whenever a provider's status changes
> Governed by the payload provenance rule in [20-provider-simulation.md](20-provider-simulation.md)
> Revision: **v1** — M2.0 · T34 · assessed 2026-07-28

## The rule

A simulated payload's shape must originate from one of four sources:

1. Official vendor documentation
2. Vendor sandbox responses
3. Recorded test-account responses
4. Sanitized production responses

**If none is available, the provider is not implemented.** A fabricated schema produces a normalizer that works perfectly against the fabrication and fails against the vendor — discovered during a paid integration, after every downstream stage has assumed the shape.

## Statuses

| Status | Meaning | Consequence |
|---|---|---|
| **Qualified** | A permitted source is in hand and recorded below | Generator may be implemented |
| **Conditional** | Architecture settled; a legitimate payload source still required | That generator waits. **Nothing else does.** |
| **Deferred** | Not pursued this phase, reason recorded | Stays in the roadmap; implementable later with **no architectural change** |

A Conditional or Deferred provider never blocks the milestone — see Provider Independence (principle 9).

---

## Assessment — 2026-07-28

| Provider | Category | Status | Source in hand |
|---|---|---|---|
| Apollo | Company enrichment | 🟡 **Conditional** | None |
| BuiltWith | Technographics | 🟡 **Conditional** | None |
| Crunchbase | Capital events | 🟡 **Conditional** | None |
| CoreSignal | Workforce | 🟡 **Conditional** | None |
| Bombora | Behavioural intent | 🟡 **Conditional** | None |

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

**What waits:** the five payload generators (T39, T40), the payload-layer assertions in the 13 Scenario Manifests (T43), and AC-18/AC-19, which are Bombora-specific.

**Bombora specifically.** It is an independent track and does not block the milestone. If it stays Conditional through M2.0, the behavioural-intent pathway is untested until it qualifies, and scenarios 6, 7, 8, 10, 11, 12, and 13 run without their intent component. That is a real reduction in coverage and is recorded here rather than discovered later — **but it is a coverage gap, not a design gap.** Every contract Bombora would satisfy already exists and is tested by the framework.

---

## Change log

| Date | Change |
|---|---|
| 2026-07-28 | v1 — initial assessment. All five Conditional; no permitted source present in the repository. Required artifact named per provider. |

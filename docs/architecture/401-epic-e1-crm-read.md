# 401 — Epic E1 · CRM OAuth and read — implementation preparation

> **Prepared by Lane C — Product Office. No code was written and none should be.** **Every claim about the repository was verified against source on 2026-08-04.**
>
> **Prepared because it is next, not because it was asked for.** E1 is the initiative Lane C is recommending Lane B start, and its specification is **five lines for an XL**. That gap is the reason this exists — preparation belongs ahead of allocation, not after it.
>
> ⚠️ **Links to [51-implementation-specifications.md](51-implementation-specifications.md) do not resolve on this branch** — Epic E's specification lives on `lane-b-commercial-profile`. Everything relied on is quoted inline.

> **Approved UI** — **CRM Integrations**. The [Fortune Signora Design Project](410-approved-ui-specification.md) is authoritative for frontend behaviour (2026-08-04). **This package no longer states what the screen looks like; it states what the backend must provide for it.** The approved screen specifies connect, per-object direction, field mapping, sync health, held writes and disconnect. **Its governing sentence — *"the CRM stays the system of record; Signora writes only what it declares"* — is [ADR-0401](adr/0401-a-customers-crm-is-not-a-provider.md) arriving from the design side.**


> **Observability, testing, operations and deployment: [405-cross-cutting-concerns.md](405-cross-cutting-concerns.md)** — written once for every prepared package rather than five times. **Epic E1's deltas are in its §6 row.** In short: **Verify `Credential.__repr__`'s refusal survives the logging path**, and **measure connection-state transitions** — §10's *silently dead connection* is unmeasurable without it. **Sync metrics already exist; add none.**

---

## 0 · Cross-validated 2026-08-04 — the interpretation half was already free

> **Lane B claimed E1 as TASK-402 and found a slice this package said did not exist.** **It was right, and the correction is Lane C's.**

**`HubSpotCompanyMapper` is built, registered and tested** (`provider_normalization/infrastructure/mappers/crm.py`, verified against source). **Six firmographic fields map straight onto existing canonical attributes** — `LEGAL_NAME`, `INDUSTRY`, `COUNTRY`, `EMPLOYEE_COUNT`, `FOUNDED_YEAR`, `REVENUE_BAND` — **with no RFC, no new table, no new event and no migration.**

**Lane B's own account of the error is the useful part:** *"That claim came from asking what a CRM could contribute; the right question was what the canonical vocabulary already accepts."* **This package asked the first question in §5 and reached a scope debate; the second question had an answer sitting in the vocabulary.**

**Three things the vendor forced, recorded because they generalise to the next CRM:** every value arrives as a **string** — `"350"`, not `350` — so the mapper parses and **an unreadable value is reported rather than dropped**; the **properties bag** is checked for unknown fields, not just the fixed top level, or the guarantee is *"formally satisfied and practically decorative"*; and **revenue arrives as a figure where the vocabulary holds bands** — placing a known figure in a declared band **loses precision and invents nothing**, which is the legal direction of a conversion `RevenueBand` otherwise forbids.

**And it refuses everything commercial**, pinned by a test: *"is-a-customer, contract value, renewal date, opportunity stage have no canonical attribute, and a test fails the day one is added here rather than through the RFC the vocabulary requires."*

**Second pass, later the same day — Lane B found another slice this package did not see, and a defect behind it.**

**`POST /workspaces/{id}/connections` — the connect route.** Lane B: *"Found a use case that had been complete and tested since M13 S01 with nothing exposing it: a customer who finished a consent flow had nowhere to land. **Same shape as the Observation Engine's thirteen computed fields with no interface layer, one module over.**"*

> **That is the third instance of one pattern in two days** — A5's observations, the firmographic mapper, and now the connect route. **The repository's recurring defect is not missing capability; it is capability with no way in.** §1's *"nothing consumes it"* was the same observation from the other end, and **this package should have looked for the unexposed use case rather than only the unbuilt one.**

**And building the route made a defect reachable within one test.** `connected_account` is unique on `(workspace, integration, external account)` **across every state**, so a disconnected connection kept the identity permanently — **disconnect was irreversible, and the same portal could never be reconnected.** *"Nothing had noticed, because no route could connect anything in the first place."*

> **A missing entrance was hiding a broken exit.** [406](406-epic-e2-crm-write-back.md) §6 lists *"re-connecting after disconnect"* as an edge case to decide; **it was already a defect, and it took the entrance to expose it.**

### What this changes

| | |
|---|---|
| **[ADR-0401](adr/0401-a-customers-crm-is-not-a-provider.md) is amended** | **It was too broad.** *"CRM data is never a claim"* → **a CRM field is a claim exactly when it is falsifiable and about the world.** A CRM is **two sources wearing one credential**, and Lane B applied this document's own falsifiability test *per field* where Lane C applied it *per source* |
| **§5's scope question is narrower** | *Records or activity* still stands for the **commercial** read. **The firmographic read is neither, and it is done** |
| **§1's three-part shape holds, and is sharper** | Lane B: *"The gap Epic E1 found is in **acquiring** records, not in **interpreting** them — which is exactly what makes the interpretation half safe to finish first."* **The consumption edge and acquisition remain the whole of the work** |

> **The `HubSpotCompanyMapper` encodes nothing about acquisition** — *"a mapper receives a stored record and translates it; who fetched it, with whose credential, through which port, is a question this layer has never been able to ask."* **The layering held, and it is why this slice could land ahead of the credential decision.**

---

## 1 · The finding that should decide everything else

**The business half of integrations is built and excellent. The consumption half does not exist, and nothing says so.**

| | What exists **today** | Evidence |
|---|---|---|
| **Connected account** | `ConnectedAccount`, `ConnectionState` — *"an account, never a person"*, with connection state deliberately separate from run state | `domain/connection.py` |
| **Credential** | `IntegrationGrant` with `secret_ref` · `Credential(kind, material)` that **refuses to render itself** in logs or tracebacks | `domain/grant.py` |
| **Secret storage** | **`integration_secret` — encrypted `ciphertext`, workspace-scoped, `ON DELETE CASCADE` from the connection.** Shipped | `migrations/versions/0028_integration_secret.py` |
| **Resolution** | **`ExecutionContext(workspace_id, connected_account_id, integration, endpoint, scopes, credential)`** — *"deliberately larger than a credential"* | `application/resolve.py:48` |
| **Catalog** | 7 systems, 4 capabilities, `live_capabilities` so the UI cannot promise what the pipeline cannot do | `domain/catalog.py` |
| **Surface** | Connection Center, shipped and reachable | CX-01 |
| **Sync machinery** | `run_sync`, `pacing`, `TargetSyncStateRepository`, `ProviderSyncStarted/Completed/Failed`, `record_reader` | `provider_platform/` |

**And then two facts that are not written down anywhere:**

> **1 · Nothing consumes it.** `integrations/public/__init__.py` states *"Provider Platform depends on Integrations; Integrations depends on nothing."* **`grep -rn "from modules.integrations" backend/modules/provider_platform/` returns nothing.** The dependency is stated in prose and absent in code. **Only `apps/api` and tests import the module at all.**
>
> **2 · Every catalog entry is `connectable=False`** — and the module says why, truthfully: *"no acquisition path exists yet, because the OAuth flow belongs at the frontend edge and has not been built."*

**So E1 is exactly three things, and the middle one is invisible in the specification:**

```
  acquisition          the consumption edge            the read
  (OAuth, frontend  →  provider_platform learns    →   a CRM adapter behind
   edge + callback)     to run against a                the existing sync model
                        ConnectedAccount
```

**The specification names the first and third.** The second is the one a lane would discover on day three, and it is the one that decides whether E1 is L or XL.

---

## 2 · Product research

### The customer problem

**A seller's CRM is where their work already lives.** Signora currently knows everything about a company *except* whether that company is already a customer, already in a deal, or already talked to last week. **A seller reading an account brief has to hold that context in their head**, and the ones who cannot are the ones who send an expansion email to a churned account.

### Value, per persona

| Persona | What they get |
|---|---|
| **AE / SDR** | The attention list stops showing accounts already in a deal. **An expansion opportunity and a net-new opportunity stop looking identical** |
| **Manager** | Coverage against the actual pipeline, not against a provider's idea of the market |
| **CRO** | **The four vision modules E1 unblocks** — pipeline intelligence, forecasting, expansion, customer risk |
| **RevOps** | One connection, no CSV, no mapping UI |

### What it unblocks, and why it is first

**E1's specification calls it *"the single highest-leverage integration in the roadmap"*, and the dependency graph agrees:** **D3** — *which accounts are already customers* — is **S** and depends entirely on E1, and D3 *"unblocks the whole expansion/renewal half of the vision."* **[Epic C](400-epic-c-people.md) §7 routes its contact half through E1** rather than buying personal data. **E2** is write-back. **One integration is load-bearing for three epics.**

### Competitors, and the differentiation

**Every revenue tool connects to a CRM; this is table stakes and not a differentiator.** What is unusual is what Signora would do with it: **the repository already refuses to merge disagreeing evidence silently**, and a CRM is the single richest source of disagreement a customer owns — a stale account owner, a closed-lost from 2023, a duplicate account. **Most tools overwrite. Signora's existing model shows both and says which it believes and why.**

> **That is also the trap.** See §4 — the decision that a customer's CRM is *not* a provider is what preserves this, and getting it wrong is the most expensive mistake available in E1.

---

## 3 · Repository reuse — what must NOT be built

| ❌ Do not build | ✅ It exists as | Consequence |
|---|---|---|
| **A connection/connected-account model** | `ConnectedAccount`, `ConnectionState` | A second lifecycle for one relationship |
| **A credential type or token store** | `IntegrationGrant` · `Credential` · **`integration_secret`, encrypted** | **Tokens in a table that is backed up and replicated** — the exact thing the grant design avoids |
| **OAuth refresh as a special case** | `Grant.refreshable` — *"a property, never a special case"* | Puts OAuth's shape into a type every other mechanism must fit |
| **A per-adapter credential resolution** | `ExecutionContext` — *"deliberately larger than a credential"* | Every future concern couples to whichever was first |
| **A system catalog or capability list** | `CATALOG` · `Capability` · `LIVE_CAPABILITIES` | The Connection Center starts promising what the pipeline cannot do |
| **A sync runner, pacing or watermark model** | `run_sync`, `pacing`, `TargetSyncStateRepository`, three sync events | **The largest duplication available in E1.** Provider Platform already runs paced, resumable, reported syncs |
| **A Connection Center screen** | Shipped in **CX-01** | A second entrance to one capability |
| **A claim/evidence/provenance model** | `Claim`, `ClaimSource`, resolution, ambiguity states | §4 — **and reusing it wrongly is worse than rebuilding it** |
| **Vendor branching above the adapter** | `ExecutionContext.integration` is *"the slug an adapter was chosen by; nothing above the adapter is expected to read it"* | The vendor leaks upward, and HubSpot→Salesforce stops being a row |

### Surface rather than build

**The Connection Center exists and lists seven systems, all `connectable=False`.** E1's first visible increment is **one entry becoming `True`** — no new screen, no new route, no new information architecture. **The button already has a home.**

### What genuinely does not exist

**Acquisition** — an OAuth authorization-code flow at the frontend edge and a callback that mints a grant. **The consumption edge** — `provider_platform` running against a `ConnectedAccount`. **A CRM adapter.** **And a decision about what CRM data *is*** (§4).

---

## 4 · The architectural decision — a customer's CRM is not a provider

> **This is the question E1 must answer before any adapter is written, and it is not in the specification.**

`ClaimSource.provider` is a plain string and `Claim` is already workspace-scoped, **so nothing in the code stops a HubSpot record becoming a claim.** It would work on the first day and be very hard to reverse on the hundredth.

**It should not, and the reason is a distinction the repository already draws in prose:**

> `integrations/domain/connection.py:3` — *"a **provider** is Signora's supplier and Signora holds the credential; an **integration** is the **customer's own system** and the customer holds it. That is a business relationship, not a synchronization mechanism."*

| | A provider says | A customer's CRM says |
|---|---|---|
| **Epistemic status** | *"This is what we observed about the world."* | *"This is what we believe about our own business."* |
| **Authority** | Contested — resolved against other providers | **Authoritative for the customer, and not evidence about the world at all** |
| **Staleness** | An observation with a date | **Often wrong, and the customer is entitled to have it anyway** |
| **Correction** | Signora resolves | **Only the customer can correct their own CRM** |

**If CRM records become claims, a stale `closed-lost` from 2023 competes with a provider observation inside identity resolution**, and the Knowledge Graph — which is designed to adjudicate between *sources that are trying to describe the same world* — starts adjudicating between a description of the world and a customer's private opinion of it. **Those are different kinds of statement, and one of them is not falsifiable.**

**Recommendation: CRM data is a *workspace-scoped fact*, held alongside the graph and never inside it.** *"Acme is a customer"* is true in this workspace and meaningless in another; a provider's *"Acme has 500 employees"* is a claim about the world. **Full reasoning and four alternatives are in [ADR-0401](adr/0401-a-customers-crm-is-not-a-provider.md).**

---

## 5 · The scope question — *read what, exactly?*

**"CRM read" is under-specified, and two documents disagree about the answer.**

| Source | Says | Status |
|---|---|---|
| **`Capability` enum** | **`CRM_ACTIVITY`** only — *"calls, emails, meetings logged against an account"* | **Shipped code**, 2026-08-02 |
| **[ADR-0014](adr/0014-crm-integration-strategy.md)** | *"each adapter targets the common integration surface (**opportunity/activity** sync)"* | **Accepted ADR** |
| **Epic D3** | *"which accounts are already customers — one boolean, from the CRM"* | Needs **records**, not activity |

**Activity and records are different reads with different shapes, different volumes and different value.** Activity is a stream; accounts and opportunities are a set. **D3 — the highest-value thing E1 unblocks — needs the read the catalog does not model.**

> **Recommendation: E1 reads *records* — accounts and opportunities — and not activity.** It is what D3 needs, it is a bounded set rather than an unbounded stream, it is the cheaper first sync, and **it delivers the visible customer outcome (*"already a customer"*) in slice one.** Activity is `CRM_ACTIVITY`'s own slice and should follow. **This requires adding a capability to the catalog — a row, by the module's own design.**

### And a governance finding, raised rather than resolved

> **[ADR-0014](adr/0014-crm-integration-strategy.md) is `Accepted` and contradicted by shipped code.** It rules **four CRMs at launch — Salesforce, HubSpot, Pipedrive, Zoho** — and *explicitly rejects* narrowing the launch set. **The catalog contains two CRMs; Pipedrive and Zoho do not appear anywhere in the repository**, and the module records a **later product-owner ruling (2026-08-02): *"Day One is one CRM and one calendar… HubSpot is the first CRM, and Salesforce is the second."***
>
> **The later ruling is almost certainly right and the ADR is almost certainly stale** — but an `Accepted` ADR contradicting shipped code is the drift class `CLAUDE.md` §2 names, and **a lane starting E1 would read both.** Raised as **[C-409](../LANE_COORDINATION.md)**; **Lane C does not amend a ratified ADR.**

---

## 6 · Domain and contracts

**No new bounded context.** E1 extends two existing modules and adds an adapter. **That is why it is XL by volume and not by risk** — the opposite of [Epic C](400-epic-c-people.md).

| Concern | Owner | Change |
|---|---|---|
| **The business relationship** | `integrations` | **A capability row** for record read; **acquisition** — the authorization-code flow and callback |
| **Synchronization** | `provider_platform` | **The consumption edge**: run a sync against a `ConnectedAccount` via `ExecutionContext`. **Pacing, watermarks, events and reporting are reused unchanged** |
| **The adapter** | `provider_platform/infrastructure/adapters/hubspot/` | Alongside `simulated/`, behind the existing port |
| **What CRM records *are*** | **New — a workspace-scoped read model** | §4 · [ADR-0401](adr/0401-a-customers-crm-is-not-a-provider.md) |
| **The account brief** | Product Surface | *"Already a customer"* — **Lane A's**, and the only cross-lane crossing in E1 |

**Contracts needed:** `integrations` publishes *connection authorized* · `provider_platform` accepts a connection-backed sync target · the CRM read model publishes *account linked* / *opportunity observed*. **Contracts that exist:** `ExecutionContext`, the sync port, the three sync events, `SecretStore`.

**Events consumed by `timeline`** — ⚠️ `make runtime-composition` reports **2 of 9 consumers wired** ([TASK-901](../BACKLOG.md)). E1's events would land dark unless that is sequenced first.

---

## 7 · Security — the non-negotiable, and what enforces it

**E1's specification states it and the repository does not yet enforce it:**

> *"A sign-in OAuth token must never be reused as an integration token. Separate grants, separate scopes, separate storage."*

**Storage is already separate and already correct** — `integration_secret` is its own table, encrypted, workspace-scoped, cascading from the connection, and **no secret material sits on the grant aggregate**. Sign-in is Better Auth's and lives nowhere near it.

**What is missing is anything that would *catch* a violation.** The rule is prose. **Recommendation: a Security Invariant** — the repository's existing mechanism — asserting that no code path reads a session token into an `IntegrationGrant` or a `Credential`. **The pattern exists** (`tests/security_invariants/`), and ⚠️ **[B-318](../BUGS.md) finds those invariants match text, so a comment fails one and an alias evades one.** **Write it structurally, and know that limitation going in.**

---

## 8 · Implementation phases

| # | Phase | Delivers | Effort | Depends on |
|---|---|---|---|---|
| **1** | **Acquisition** | HubSpot authorization-code flow, callback, grant minted. **`connectable=True` for one system** | **L** | **Developer credentials — product owner** |
| **2** | **The consumption edge** | `provider_platform` runs against a `ConnectedAccount`. **No CRM logic yet — prove it with the simulated adapter** | **M** | Phase 1 |
| **3** | **Records read** | Accounts and opportunities, paced and resumable, as a workspace read model | **L** | Phase 2 · **[ADR-0401](adr/0401-a-customers-crm-is-not-a-provider.md) ratified** |
| **4** | **The customer outcome** | *"Already a customer"* on the brief and the attention list — **this is [D3](51-implementation-specifications.md)** | **S** | Phase 3 · **Lane A** for the render |
| **5** | **Salesforce** | The architecture's own test — *"would a second CRM require architectural change?"* | **M** | Phase 3 |

> **Phase 2 is the one to insist on.** Running the *existing simulated adapter* through a connection-backed path proves the consumption edge with **no vendor involved** — and it is the only phase that can be verified without credentials. **A lane that merges phases 1 and 3 will debug OAuth and the sync edge simultaneously, and will not know which is failing.**

**Critical path:** credentials → phase 1 → phase 2. **ADR-0401 blocks phase 3 only**, so preparation and acquisition proceed in parallel with the ruling.

**Parallelisable:** the catalog capability row · phase 4's render (Lane A) · the Security Invariant (§7) · the ADR-0014 reconciliation (§5).

**Stop-after-any-phase:** phases 1–2 leave the product with a working connection and no read — **honest and visible, and `live_capabilities` already models exactly that state.**

---

## 9 · Risks

| Class | Risk | Mitigation |
|---|---|---|
| **Architectural** 🔴 | **CRM records enter the claim stream** and a stale CRM row competes with provider evidence | **§4 · [ADR-0401](adr/0401-a-customers-crm-is-not-a-provider.md) before phase 3.** Cheap now, very expensive later |
| **Security** 🔴 | A sign-in token reused as an integration token | §7 — **and nothing currently detects it** |
| **Scope** 🟠 | **Activity vs records** decided by implementing it | §5 — decide first; **D3 needs records** |
| **Governance** 🟠 | **An `Accepted` ADR contradicts shipped code** | **[C-409](../LANE_COORDINATION.md)** — product owner's |
| **External** 🟠 | **Developer credentials are a product-owner action, not an engineering task** | **Request them the day E1 is allocated**, not the day phase 1 finishes |
| **Integration** 🟠 | Vendor branching leaks above the adapter | The rule exists in `ExecutionContext`'s docstring; **assert it** |
| **Operational** 🟡 | Token refresh, revocation, expiry | `refreshable` models it; **`ConnectionState` must reach the customer** — a silently dead connection is worse than none |
| **Data** 🟡 | CRM account ↔ Signora entity matching | **Reuse the graph's resolution, do not invent a second matcher** — but as a *link*, never a claim (§4) |
| **Performance** 🟡 | Full sync on a large CRM | **Pacing and watermarks already exist.** Measure before optimising |

---

## 10 · Edge cases

| Case | Recommended behaviour |
|---|---|
| **Customer revokes the grant in the CRM** | `ConnectionState` reflects it; **the last read survives and is dated.** Never silently stale |
| **Token expires mid-sync** | The sync fails as a sync — `ProviderSyncFailed` exists. **Connection state does not change**; that separation is already designed |
| **CRM account matches no Signora entity** | **Record the link as unresolved.** The graph already models this for companies |
| **Two CRM accounts match one entity** | **Both linked, ambiguity visible.** Never merge on name |
| **The CRM says customer, the provider says otherwise** | **The CRM wins for *"is a customer"*** — it is the customer's own business fact. §4 is what makes this expressible |
| **A duplicate/merged CRM account** | Follow the CRM's own merge; **the CRM is authoritative for its records** |
| **Sandbox vs production** | HubSpot avoids this; **Salesforce does not** — a reason HubSpot is first |
| **Re-connecting after disconnect** | A new grant, same connection, **watermarks reset or resume — decide explicitly**; a silent resume can skip records |
| **Rate limits** | `pacing` exists. **Do not write a second backoff** |
| **Empty CRM** | An honest empty state; the attention list is unchanged |

---

## 11 · Definition of done

| Gate | Measurable |
|---|---|
| **Capability** | A customer connects HubSpot from the Connection Center **without leaving the product** |
| **Capability** | The account brief says **"already a customer"**, sourced from the CRM — **this is D3** |
| **Architecture** | **CRM records are workspace-scoped and are not claims** (§4), verifiable by diff |
| **Reuse** | **No second sync runner, secret store, credential type, catalog or backoff.** Verifiable by diff |
| **Security** | An invariant asserts sign-in tokens cannot reach an integration grant |
| **Honesty** | `connectable` and `live_capabilities` are true; a revoked connection says so |
| **Portability** | Salesforce is **a new adapter and a catalog row**, and nothing above it changes |

---

## 12 · What this preparation could not settle

1. **Developer credentials.** Product owner's, and **the critical path starts there.**
2. **[ADR-0401](adr/0401-a-customers-crm-is-not-a-provider.md)** — ratification. Blocks phase 3 only.
3. **[ADR-0014](adr/0014-crm-integration-strategy.md)'s contradiction** ([C-409](../LANE_COORDINATION.md)) — a ratified ADR is not Lane C's to amend.
4. **Records or activity** (§5) — recommended, not ruled.
5. **Effort.** **L/M/L/S/M** as estimates. **The specification's XL is not contradicted**; phase 2 is the term Lane C is least confident in, because nothing has run through that edge.

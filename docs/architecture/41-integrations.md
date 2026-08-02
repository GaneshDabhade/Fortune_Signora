# 41 — Integrations (module design)

> Status: **As built, and paused.** M13 slices S01–S09 complete. Lane B.
>
> **The paused state is the point of this document.** M13 stops at a deliberate boundary: everything that does not require a vendor's developer application is finished, and the one thing that does is not started. A lane picking this up months from now needs to know *what exists*, *what does not*, *why the line falls where it does*, and *what would have to be true to resume* — none of which is recoverable from the code, and all of which would otherwise live only in commit messages.
>
> [13-integrations.md](13-integrations.md) is the ratified architecture and is **not** superseded by this document. That one says *what the Integration Abstraction Layer is*; this says **what was built inside it**, in the manner of [22](22-knowledge-graph.md)–[29](29-ai-reasoning-engine.md) and [40](40-commercial-profile.md).
>
> Created 2026-08-02, at the pause, because the module had none.

---

## 1 · What this module is, and the ruling that put it here

**A *provider* is Signora's supplier and Signora holds the credential. An *integration* is the customer's own system and the customer holds it.** That single sentence is the boundary; everything below follows from it.

The module was nearly not built at all. The implementation readiness review ([C-025](../LANE_COORDINATION.md)) found that [04-modules.md](04-modules.md) defines fourteen modules and Integrations is not among them, and that [13-integrations.md](13-integrations.md) puts the Integration Port inside the **consuming** module. Read literally, M13 was a capability spread across consumers rather than a bounded context.

**The product owner ruled otherwise on 2026-08-02, and the reason is the one that matters:**

> **A Connected Account exists independently of synchronization.** It exists before any sync runs, while syncing is paused, after a grant is revoked, and even if synchronization never happens at all. A thing whose entire lifecycle is independent of another module's activity is not that module's data.

So `modules/integrations/` owns the **relationship**; Provider Platform owns the **synchronization** and consumes the relationship through `public/`. The dependency runs `provider_platform → integrations`, never the reverse, and an import-linter contract enforces it: *"integrations owns connections; it never depends on what synchronizes them."*

**What the module owns:** Connected Account · Integration Grant · Credential storage · the connection lifecycle · the catalog of systems Signora understands · the read model behind the Connection Center.

**What it does not own:** synchronization, scheduling, polling, watermarks, rate limits, cost (Provider Platform) · what the synced data *means* (Provider Normalization onwards) · **credential acquisition** (the frontend edge, §5) · any vendor's API shape (an adapter, when one exists).

---

## 2 · The domain, and the three properties that shaped it

### Connected Account

**An account, never a person.** Google domain-wide delegation and Microsoft Graph app-only permissions bind one grant to an entire organisation. A model assuming one human behind a connection breaks on the second integration, and it was designed out on day one rather than discovered.

**The endpoint is not the credential.** Salesforce returns a per-org `instance_url` beside its token. Storing the address on the grant would mean rotating a credential in order to correct an address.

**Connection state and run state are different lifecycles.** A healthy connection can have a failed sync; a revoked grant can have a completed one. Only the first is something a customer can act on, and merging them would make *"the customer revoked us in Salesforce"* indistinguishable from *"last night's sync timed out."*

`integration` is an **opaque slug, never an enum** — a closed enum cannot admit a partner-published or customer-written connector, which is the assumption a marketplace breaks first.

### The lifecycle

```
NOT_CONNECTED ──▶ AUTHORIZING ──▶ CONNECTED ──▶ VALIDATED
                       │              │              │
                       │              ├──▶ EXPIRED ──┤
                       │              ├──▶ REVOKED   │
                       └──────────────┴──▶ DISCONNECTED
```

A **table** of allowed transitions, not a chain of `if`s: adding a state is a row, and an illegal transition is refused by construction rather than by whichever branch happened to be written.

Two states earn their place against the obvious objection that they are redundant:

- **`AUTHORIZING` is persisted, not transient.** OAuth device flow leaves a connection here for minutes while somebody types a code on another device. It is also where a connection sits mid-write (§4).
- **`VALIDATED` is distinct from `CONNECTED`.** A grant that authenticates but lacks a scope is the commonest integration failure there is, and it is indistinguishable from healthy until the first sync. `CONNECTED` means *a grant exists*; `VALIDATED` means *a real call succeeded with it*.

`transition()` takes `by: UUID` **with no default**, the rule `next_state` already follows in the Opportunity Engine: *"who disconnected our CRM?"* is asked during an incident, and this is the only moment the answer exists.

**Every usable state reaches `DISCONNECTED`.** `AUTHORIZING → DISCONNECTED` was missing and was found by a parameterised *"every state can be left"* test rather than by reading the table — without it, an abandoned half-finished connection showed a row reading *Not finished* that nothing could clear. `REVOKED` is the one exception and is deliberate: access is already gone at the vendor, and the route back is re-authorization.

### Integration Grant

**A grant is secret material bound to a connection, and nothing about what it is for.**

**Nothing on it knows how the credential was obtained.** The mechanism belongs to acquisition and must never reach synchronization. An adapter able to ask *"was this OAuth?"* is vendor-shaped and would not survive the first mechanism that is not a bearer token.

**`refreshable` and `expires_at` are properties, never special cases.** An API key is a grant that does not expire and cannot be refreshed. Modelling that as an exception would put OAuth's shape into the type every other mechanism has to fit.

**No material is stored on the aggregate** — only a `secret_ref`. A grant row is backed up, replicated and readable by anybody with database access.

**Two exceptions rather than one boolean:** `GrantExpired` and `GrantRevoked`, because a caller does different things — an expired refreshable grant is refreshed, a revoked one needs the customer back. **Revocation outranks expiry**, so a revoked grant that also expired never looks refreshable.

### Credential

**Opaque by construction, and mTLS is what forced it.** Every other mechanism resolves to something an adapter attaches to a request; a client certificate configures the TLS context *before* a request exists. An abstraction shaped as *"the value for the `Authorization` header"* cannot express that, so `Credential` carries material an adapter hands to a factory and never formats itself.

It refuses to render itself — `__repr__` redacts — because a credential in a traceback, a log line or a pytest diff is a credential in a log aggregator.

### The stress test that produced this shape

Before implementation, the model was tested against API keys, OAuth 2.1, Device Flow, service accounts, Microsoft Graph, Salesforce Connected Apps, Slack and Stripe webhooks, SAML-backed APIs, mTLS, signed callbacks, polling, event streaming and GraphQL subscriptions. **Three broke it, and the model is what it is because of them:** mTLS forced `Credential` to be opaque rather than header-shaped; device flow forced `AUTHORIZING` to be persisted; per-org endpoints forced the endpoint off the grant.

---

## 3 · Where credentials live

`integration_secret` — its own table, **encrypted at rest with Fernet**, behind the same `SecretStore` port a vault will implement.

**Its own table rather than a column on `integration_grant`.** The grant is lifecycle — read on every connections screen, listed, counted. Material is read only when a call is about to be made. Separating them keeps ciphertext out of the common query and makes the eventual move to AWS Secrets Manager ([ADR-0022](adr/0022-devops-infrastructure-and-deployment-topology.md), provisioned at M14.5) a dropped table rather than a column migrated out of a hot aggregate.

**The key has no default.** A default would ship a known key, which is worse than no encryption because it reads as protection. `IntegrationSettings` is the module's own typed object (§6), constructed only at the composition root.

**No `UPDATE` grant.** A rotation writes a new `secret_ref` and leaves the old one to be purged; editing material in place would make the previous value unrecoverable at exactly the moment a rotation is being diagnosed.

Three ports rather than one — `SecretStore` (read), `SecretWriter` (write), `SecretPurger` (destroy) — so a component that only needs to read a credential cannot be handed the ability to write one.

`SecretUndecryptable` subclasses `SecretNotFound`: **a rotated key and a purged secret are the same fact above the adapter** — this connection must be made again — while the distinct type survives for the log line, where the difference is the whole diagnosis.

---

## 4 · Connecting and disconnecting

### Connecting

The write order is **connection → material → grant → connection again**, and it is not stylistic.

`integration_secret` and `integration_grant` both carry a foreign key to `connected_account`, so writing either first is refused by the database. The first version wrote material first, reasoning that a grant with no credential behind it would make the screen say *Ready to use* about something that does not exist. **That reasoning is right and the ordering was wrong** — it passed only because the tests used fakes, and a fake cannot refuse an insert.

The resolution keeps the property and satisfies the schema: the connection lands first **in `AUTHORIZING`**, so a failure anywhere below leaves a row reading *you started connecting this and did not finish* — which is true, is what the Connection Center already says, and is already something a customer can remove. `CONNECTED` is written last, once material and grant both exist.

Found by the first test to run this against PostgreSQL rather than a double ([B-024](../BUGS.md)).

### Disconnecting

**A lifecycle, not a state change**, and three rules shape it because the obvious implementation gets each one wrong.

**A vendor cannot block it.** Revocation is attempted, its failure recorded, never propagated. Withdrawing access is what somebody does in a hurry, and a disconnect that failed because HubSpot was down would hold a security action hostage to the system it protects them from.

**Material is destroyed, not orphaned.** `purge_for` runs unconditionally. Marking a grant revoked while its credential sits in storage is the gap the capability exists to close — and it was a real gap: the module review found `purge_for` written and never called.

**It is idempotent.** A second disconnect is a customer clicking twice. It returns success, touches nothing, and does not move the first one's timestamp.

`NoRevoker` is the default and **reports failure**. No adapter calls a vendor's revocation endpoint yet, and claiming a revocation that never happened would tell a customer their access was withdrawn at the vendor while the credential is still live there — the more dangerous of the two available lies. The Connection Center passes that through verbatim: *"Signora could not tell HubSpot… you may also want to remove Signora from your HubSpot settings."*

---

## 5 · The OAuth boundary — where acquisition happens, and why

**The authorization-code flow executes entirely in Next.js. Python never sees it.**

This looked like a conflict with [18-authentication.md](18-authentication.md):49, which forbids the Python tier from holding *"an OAuth flow, callback handler, or authorization-code exchange."* Precise reading resolves it — **a refresh-token grant is none of those three**, so credential *management* may live in Python while credential *acquisition* may not.

| Concern | Where | Why |
|---|---|---|
| Redirect, consent, `state`, code exchange | **Next.js** (`app/api/integrations/[slug]/{start,callback}`) | 18-authentication.md:49. Signora users' authentication and external-system authorization remain completely separate grants |
| Storage, validation, refresh, revocation, lifecycle | **Python** (this module) | Workspace ownership, auditability and RLS |

The `state` parameter is **HMAC-signed and single-use**, with a 10-minute TTL, compared in constant time, and **expiry checked before the nonce** so an expired state cannot be distinguished from an unknown one by timing.

**`ConnectInput` names nothing about OAuth.** An API key, a service account file or a certificate arrives through the same door.

---

## 6 · The read model, and what the product refuses to say

`IntegrationQueries` answers two questions, and the second is why there are two routes:

- **`connections()`** — every connection in every state, **including the broken ones**. A revoked Salesforce is the most important row on the screen, and a list that quietly omitted it would leave somebody believing their data was flowing.
- **`systems()`** — **catalog-first**, so a screen built only from what somebody already did can still answer *"what are we missing?"* A connection whose catalog entry was later withdrawn still belongs to the customer and does not vanish.

**`working` is not "has a connection."** A revoked connection is a connection, and answering *"is my CRM connected?"* with *yes* would be this screen's worst possible lie.

**Attention is derived at read time, never stored** — `NONE` / `SOON` / `NOW`, computed from the connection and its grant. A credential that expired overnight reads correctly the next morning without anything having run. This is the least-powerful-author rule: a stored copy of a derivable fact is a defect waiting for the two to disagree.

**Capabilities listed are only ones Signora can act on today.** Anything waiting on unbuilt work is *absent*, not greyed out — advertising a capability the platform cannot execute is a promise the product cannot keep.

**Every catalog entry reports `connectable: false`, and that is correct, not unfinished.** No developer application exists for any vendor, so nothing can genuinely be connected. The product says *Not available yet* rather than offering a button that fails. An API test asserts this so it cannot become true by accident.

**Not paginated, deliberately.** A customer connects a handful of systems. If that ever stops being true it becomes a cursor-paginated collection like any other.

---

## 7 · Day One scope

**HubSpot (CRM) and Google Calendar.** Set by the product owner, 2026-08-02.

Salesforce is next and was argued for at the time — it is the enterprise default and the harder integration, so building it first would prove more. **The counter-argument won and is recorded here rather than lost:** HubSpot's developer experience is dramatically faster to a working handshake, and the goal of Day One is to prove the *abstraction*, not the hardest vendor. The model was already stress-tested against Salesforce Connected Apps and per-org endpoints (§2), so the design does not owe Salesforce anything it has not already paid.

**Slack is deferred until there is something worth delivering into it.** A notification channel with no notifications behind it is a connection a customer maintains for nothing.

---

## 8 · What exists

| Layer | What |
|---|---|
| **Domain** | `ConnectionState`, `ConnectedAccount`, `IntegrationGrant`, `Credential`, `CatalogEntry`, `Capability`, `CATALOG` |
| **Application** | `ConnectSystem`, `DisconnectSystem`, `ResolveExecutionContext`, `IntegrationQueries`; ports `ConnectedAccountRepository`, `GrantStore`, `SecretStore`, `SecretWriter`, `SecretPurger`, `ProviderRevoker` |
| **Infrastructure** | `SqlConnectedAccountRepository`, `SqlGrantStore`, `EncryptedSecretStore`, `IntegrationSettings`, composition |
| **Interface** | 3 routes, purpose-built response schemas, `ERROR_MAPPING` |
| **Public** | `ConnectedAccount`, `ConnectionState`, `ConnectionUnusable`, `Credential`, `ExecutionContext` |
| **Migrations** | `0027` (`connected_account`, `integration_grant`), `0028` (`integration_secret`) — all three registered in `tenancy_policy.py`, RLS enabled and **forced** |
| **Frontend** | `/settings/connections` · `ConnectionCenter` · `ConnectPanel` · `DisconnectDialog` · `useIntegrations` / `useDisconnect` · the OAuth client routes · 9 `ConnectOutcome`s |

**Authorization:** `integration:read` for owner and member; `integration:update` (disconnect) for owner only. Withdrawing an organization's access to its own CRM is an owner's decision; the client hides the control as a courtesy, and Casbin is what decides.

---

## 9 · What does not exist, and what would resume it

**One thing is missing, and it is environmental rather than architectural.**

| Missing | Needs |
|---|---|
| **The HubSpot token exchange** | A HubSpot developer application — **client id, client secret, registered redirect URI** |
| **End-to-end verification** | The above, plus a real consent round trip |
| **Production credential validation** | A first real call, which is what moves a connection `CONNECTED → VALIDATED` |

The callback route deliberately returns `provider_unavailable` rather than a stub. **Nothing simulates a completed connection**, because a product that reports a connection it does not have is worse than one that admits it cannot connect yet.

### Resume conditions

**When real credentials exist, the remaining work is one slice and it is small:**

1. Put `HUBSPOT_CLIENT_ID`, `HUBSPOT_CLIENT_SECRET` and the registered redirect URI in the frontend environment. `credentialsFor()` already returns `null` when they are absent, and that absence is what `connectable: false` currently reflects.
2. Implement the token exchange in `app/api/integrations/[slug]/callback/route.ts`, at the single point that today returns `provider_unavailable`.
3. Call `ConnectSystem` with the resulting `ConnectInput`. **The endpoint, the use case, the storage, the encryption, the lifecycle and every screen already exist and are tested.**
4. Flip the catalog entry's `connectable` to `true` — **only once a real handshake has succeeded**, never in anticipation.
5. Add the first real call so a connection can reach `VALIDATED`; that is also the natural home for the first `ProviderRevoker`.

**No further product development is required.** If a resuming lane finds itself designing a screen, a state or a port, something has changed underneath this document and the change is the first thing to write down.

### Known limitations, stated rather than discovered later

- **No `ProviderRevoker` adapter.** Disconnect always reports `revoked_at_provider: false`, and the dialog tells the customer to tidy up at the vendor. Honest, and it stops being necessary the moment an adapter exists.
- **No refresh.** `refreshable` is recorded and nothing acts on it. A grant that expires reads `NOW` on the Connection Center and needs reconnecting by hand.
- **`ResolveExecutionContext` is not wired at the composition root.** It is complete and tested; a factory that could only raise would be a wiring that lies about what exists. Provider Platform wires it when it consumes a connection.
- **Nothing synchronizes.** This module records relationships. The first consumer is Provider Platform, and it has not arrived.
- **No navigation entry.** `/settings/connections` is reachable by URL and nothing links to it — the shell is Lane A's, recorded as a coordination item rather than edited across a boundary.

---

## 10 · The tests, and what each layer is for

Domain and application against **fakes**; infrastructure and interface against **real PostgreSQL as `signora_app`**. The split matters more here than usual, and B-024 is the worked example: every repository was exercised only through doubles, **the doubles accepted a `ConnectedAccount` the database would not** — `created_by` and `updated_by` are `NOT NULL` and nothing supplied them — and every insert would have failed the first time a customer connected anything, with a green suite throughout.

Three defects came out of closing it, none of which a fake could have surfaced: the missing audit columns, the write ordering against the foreign keys (§4), and `ConnectionNotFound` escaping as a `500` because it had no entry in the central error mapping.

**The lesson is general enough to state here:** a fake that reimplements a rule can only agree with itself. Where the rule lives in the database — a constraint, an ordering, a keyset predicate, RLS — the test has to be there too.

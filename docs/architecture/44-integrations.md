# 44 — Integrations (module design)

> Status: **Acquisition complete; the read blocked.** M13 slices S01–S09, plus Epic E1's connection surface (2026-08-04). Lane B.
>
> **Epic E1 found the module's pause was in the wrong place.** Everything between a customer's consent and a stored credential is now built — the connect route (§4), the code exchange and the hand-off (§5) — and what remains for *acquisition* is a developer application, not engineering. **What is genuinely blocked is the read**: no path exists for a customer-held system to deliver records into the pipeline, recorded as [ADR-0300](adr/0300-inbound-customer-systems.md) and [C-326](../LANE_COORDINATION.md).
>
> **The paused state was the point of this document, and the note below is what it asked for.** M13 stops at a deliberate boundary: everything that does not require a vendor's developer application is finished, and the one thing that does is not started. A lane picking this up months from now needs to know *what exists*, *what does not*, *why the line falls where it does*, and *what would have to be true to resume* — none of which is recoverable from the code, and all of which would otherwise live only in commit messages.
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

**What it does not own:** synchronization, scheduling, polling, watermarks, rate limits, cost (Provider Platform) · what the synced data *means* (Provider Normalization onwards) · **credential acquisition** (the frontend edge, §5).

> **`HubSpotCompanies` sits here provisionally, and the qualifier is the point.** This line used to end *"any vendor's API shape (an adapter, when one exists)"*, which was written when the only vendor call imagined was a sync. Three now exist — revoke, renew, read — and the first two are unambiguously grant management, which is this module's. **The read is the one [ADR-0300](adr/0300-inbound-customer-systems.md) decides**: it is vendor logic with no port, no event and no storage, taking a token and a cursor and returning raw payloads, so **all three options in that ADR call something that does exactly what it does.** The ruling moves a file and rewrites a wrapper. It is written here because this module already holds the credential, and because writing it inside a module another lane is assigned would be the boundary violation.

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

**`kind` says what the material is, and the acquisition flow stores `oauth2`** — a JSON object carrying the access token and, when the provider issued one, the refresh token. `Credential` is opaque by construction precisely so that a kind can be more than one string, and there is exactly one `secret_ref` per grant, so a refresh token has nowhere else to live.

> **The first version of the exchange discarded the refresh token while recording `refreshable: true`** — a flag nothing could ever act on, which is the Decorative Logic §2 names. It was worse than untidy: **HubSpot access tokens expire in 1800 seconds**, so every connection would have died within half an hour with no way back but reconnecting by hand. Found by sweeping the epic rather than by a test, and now pinned by one asserting the two can never disagree.

**Its own table rather than a column on `integration_grant`.** The grant is lifecycle — read on every connections screen, listed, counted. Material is read only when a call is about to be made. Separating them keeps ciphertext out of the common query and makes the eventual move to AWS Secrets Manager ([ADR-0022](adr/0022-devops-infrastructure-and-deployment-topology.md), provisioned at M14.5) a dropped table rather than a column migrated out of a hot aggregate.

**The key has no default.** A default would ship a known key, which is worse than no encryption because it reads as protection. `IntegrationSettings` is the module's own typed object (§6), constructed only at the composition root.

**No `UPDATE` grant.** A rotation writes a new `secret_ref` and leaves the old one to be purged; editing material in place would make the previous value unrecoverable at exactly the moment a rotation is being diagnosed.

Three ports rather than one — `SecretStore` (read), `SecretWriter` (write), `SecretPurger` (destroy) — so a component that only needs to read a credential cannot be handed the ability to write one.

`SecretUndecryptable` subclasses `SecretNotFound`: **a rotated key and a purged secret are the same fact above the adapter** — this connection must be made again — while the distinct type survives for the log line, where the difference is the whole diagnosis.

---

## 4 · Connecting and disconnecting

### Connecting

**`POST /workspaces/{id}/connections` is the route, added 2026-08-04.** The use case had been complete and tested since S01 and nothing exposed it, so a customer finishing a consent flow had nowhere to land — the same shape as the Observation Engine's thirteen computed fields with no interface layer.

The write order is **connection → material → grant → connection again**, and it is not stylistic.

`integration_secret` and `integration_grant` both carry a foreign key to `connected_account`, so writing either first is refused by the database. The first version wrote material first, reasoning that a grant with no credential behind it would make the screen say *Ready to use* about something that does not exist. **That reasoning is right and the ordering was wrong** — it passed only because the tests used fakes, and a fake cannot refuse an insert.

The resolution keeps the property and satisfies the schema: the connection lands first **in `AUTHORIZING`**, so a failure anywhere below leaves a row reading *you started connecting this and did not finish* — which is true, is what the Connection Center already says, and is already something a customer can remove. `CONNECTED` is written last, once material and grant both exist.

Found by the first test to run this against PostgreSQL rather than a double ([B-024](../BUGS.md)).

### Refreshing, and the boundary it stops at

**A refresh is a new grant, never an edit.** New `secret_ref`, new grant saved *before* the old is revoked so `current_for` never returns nothing, scopes carried forward — a refresh asks the customer for nothing, so it cannot widen or narrow what they permitted. **A provider that issues no new refresh token has not withdrawn the old one**; Google does exactly that, and overwriting with `None` would destroy the only thing that could renew the grant again.

**It revives an expired connection** through `EXPIRED → CONNECTED`, an edge the transition table already held. That is what makes a refresh invisible to the customer, which is the entire reason `refreshable` is recorded.

**It never renews a withdrawn connection.** `DISCONNECTED` and `REVOKED` are refused outright — renewing either would resurrect access a customer or a vendor deliberately removed, and `REVOKED` is the sharper case: the customer withdrew Signora *at the vendor*, and quietly restoring it would be the product overriding them.

**Five outcomes rather than a boolean**, because a caller does something different with each: `RENEWED` is silent, `NOT_REFRESHABLE` means reconnect, `REFUSED` may mean the customer withdrew access at the vendor, `UNREADABLE` is an operational fault on Signora's side, and `UNUSABLE` means there was nothing to renew.

**Signora's own client credentials reach it through an interface.** `ClientCredentialsStore` says *what this module needs*; `IntegrationSettings` says where it comes from, which is where §6 already puts a module's configuration. **A deployment that has configured none gets `NoTokenRefresher`** — the identical refusal `credentialsFor()` performs at the other tier, and the same honesty `NoRevoker` had. Empty is a working state and a defaulted client secret would be a known one.

**A renewal is attributed to the platform, not to the customer.** `SYSTEM_ACTOR_ID` — the same value `provider_platform` uses for its own unattended writes, declared here rather than imported, because a module does not reach into another's internals and the convention is the shared thing. Naming the person who consented months earlier would put them on an action they did not take, which is the one thing an audit column exists to prevent.

> **The renewal itself is RFC 6749 §6** — the same endpoint as the code exchange with a different `grant_type` — so no vendor-specific branch exists. A refresh-token grant is not a redirect, a consent screen or an authorization-code exchange, which is the precise reading §5 already relies on to keep credential *management* here.

### Reconnecting, and the disconnect that could not be undone

**`connected_account` is unique on `(workspace, integration, external_account_id)`** — one HubSpot portal is one relationship however many times somebody consents to it. The index spans *every* state, so a disconnected connection keeps the identity permanently.

**That made disconnect irreversible, and nothing had ever noticed**, because no route could connect anything. Building one made it reachable within a single test.

**The fix was already in the domain.** The transition table has allowed `DISCONNECTED → AUTHORIZING` and `REVOKED → AUTHORIZING` since it was written — §2's *"the route back is re-authorization"* — and no code had used either edge, because `ConnectSystem` always minted a fresh id. It now **reuses the existing connection** when one exists and is not usable, and refuses with `AlreadyConnected` → `409` when it is.

| The customer did | What happens |
|---|---|
| Connected HubSpot for the first time | A new connection |
| Disconnected, then connected again | **The same connection**, a new grant, and their label survives |
| Re-consented while it was still working | **`409`.** Discarding a grant that works to find out whether a new one does is the expensive way to learn |
| Connected a second HubSpot portal | A second connection — the index names the *account*, never the system |

**A reconnection keeps the connection's label and `endpoint`.** The label is the customer's own name for a relationship that persisted through a gap, and the acquisition flow does not ask twice. **Keeping the endpoint is correct for every shipped system and would not be for one whose host can move between authorizations** — Salesforce is that case and is not shipped.

**`secret_ref` is per *grant*, not per connection** (`integration/{connection}/{grant}`). A reconnection writes new material while the old may still exist, which is §3's rotation rule rather than a new one: *a rotation writes a new ref and leaves the old to be purged.*

**The unique index is the single guard, and it decides.** The repository flushes on insert and translates the constraint violation into `AlreadyConnected`; there is no second pre-read rule to race with it. Before that translation existed the violation escaped as an unhandled `500` — *the platform broke* — when in fact it had refused the caller, which is the same defect class as `ConnectionNotFound` in §11.

### Disconnecting

**A lifecycle, not a state change**, and three rules shape it because the obvious implementation gets each one wrong.

**A vendor cannot block it.** Revocation is attempted, its failure recorded, never propagated. Withdrawing access is what somebody does in a hurry, and a disconnect that failed because HubSpot was down would hold a security action hostage to the system it protects them from.

**Material is destroyed, not orphaned.** `purge_for` runs unconditionally. Marking a grant revoked while its credential sits in storage is the gap the capability exists to close — and it was a real gap: the module review found `purge_for` written and never called.

**It is idempotent.** A second disconnect is a customer clicking twice. It returns success, touches nothing, and does not move the first one's timestamp.

**`HttpProviderRevoker` is the default from 2026-08-04**, and it closes the gap the dialog had been apologising for. `NoRevoker` remains for a system with no revocation endpoint, and still reports failure — because claiming a revocation that never happened would tell a customer their access was withdrawn while the credential is still live at the vendor, which is the more dangerous of the two available lies.

**Its endpoints live in Python, not beside the acquisition ones.** `providers.ts` holds where a customer is *sent* and where a code is *exchanged* — acquisition, which §5 reserves to the Next tier. `revocation.py` holds where a grant is *destroyed* — management, which §5 puts here. **No URL appears in both tables and neither tier could use the other's.**

**Three properties, each of which the obvious implementation gets wrong:**

| | |
|---|---|
| **The vendor is sent the token it asks for** | HubSpot revokes a *refresh* token and the access token will not do. Sending the wrong one returns a cheerful success that revokes nothing — **the product would report the credential withdrawn while it still worked** |
| **A `404` counts as revoked** | The grant is already gone, which is the outcome the customer wanted. Reporting failure would send them to tidy up something already tidy |
| **Nothing raises** | Every failure — a refusal, an unreachable host, unreadable material, a system with no endpoint — returns `False` and is logged with its reason. `DisconnectSystem` catches broadly anyway, so a raise would still not stop a customer; it would arrive as a discarded traceback instead of a line naming the cause |

**Material it cannot read is a refusal, never a guess.** A `bearer` credential, malformed JSON, JSON that is not an object, an object with no refresh token — each reports failure rather than sending part of something to a vendor on the chance it works.

---

## 5 · The OAuth boundary — where acquisition happens, and why

**The authorization-code flow executes entirely in Next.js. Python never sees it.**

This looked like a conflict with [18-authentication.md](18-authentication.md):49, which forbids the Python tier from holding *"an OAuth flow, callback handler, or authorization-code exchange."* Precise reading resolves it — **a refresh-token grant is none of those three**, so credential *management* may live in Python while credential *acquisition* may not.

| Concern | Where | Why |
|---|---|---|
| Redirect, consent, `state`, **code exchange** | **Next.js** (`app/api/integrations/[slug]/{start,callback}`, `lib/integrations/{exchange,record}.ts`) | 18-authentication.md:49. Signora users' authentication and external-system authorization remain completely separate grants |
| Storage, validation, refresh, revocation, lifecycle | **Python** (this module) | Workspace ownership, auditability and RLS |

**The workspace travels inside the signed state, never in the query string.** It is decided when the flow starts, cannot be edited by whoever returns, and the API re-verifies membership regardless — which is what keeps it a routing hint rather than a grant (§13).

**The callback mints its own access token rather than forwarding one.** A customer returning from a consent screen arrives on a redirect carrying cookies and no `Authorization` header, so there is nothing to forward. The session is exchanged exactly as `/api/token` does — same issuer, same key, same claims — because a second route to the API would be a second authentication surface.

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
| **Application** | `ConnectSystem`, `DisconnectSystem`, `RefreshGrant`, `ResolveExecutionContext`, `IntegrationQueries`; ports `ConnectedAccountRepository` (`get`, `find_identity`, `list_for_workspace`, `save`), `GrantStore`, `SecretStore`, `SecretWriter`, `SecretPurger`, `ProviderRevoker` |
| **Infrastructure** | `SqlConnectedAccountRepository`, `SqlGrantStore`, `EncryptedSecretStore`, `HttpProviderRevoker`, `HttpTokenRefresher`, `SettingsClientCredentials`, **`HubSpotCompanies`** *(provisionally — see §1)*, `VENDOR_ENDPOINTS`, `IntegrationSettings`, composition |
| **Interface** | **4 routes**, purpose-built request and response schemas, `ERROR_MAPPING` |
| **Public** | `ConnectedAccount`, `ConnectionState`, `ConnectionUnusable`, `Credential`, `ExecutionContext` |
| **Migrations** | `0027` (`connected_account`, `integration_grant`), `0028` (`integration_secret`) — all three registered in `tenancy_policy.py`, RLS enabled and **forced** |
| **Frontend** | `/settings/connections` · `ConnectionCenter` · `ConnectPanel` · `DisconnectDialog` · `useIntegrations` / `useDisconnect` · the OAuth client routes · 9 `ConnectOutcome`s |

**Authorization:** `integration:read` for owner and member; `integration:update` (**connect and disconnect**) for owner only. Withdrawing an organization's access to its own CRM is an owner's decision; the client hides the control as a courtesy, and Casbin is what decides.

---

## 9 · What does not exist, and what would resume it

**One thing is missing, and it is environmental rather than architectural.**

| Missing | Needs |
|---|---|
| ~~**The HubSpot token exchange**~~ | **Built 2026-08-04.** RFC 6749 §4.1.3, tested against a fake `fetch`. The one step no RFC covers — *whose account is this token for* — is **configuration** in `providers.ts` and is the only part a live handshake has yet to confirm |
| **Developer applications** | **Client id, client secret and a registered redirect URI, per provider.** Until they exist `credentialsFor()` returns `null`, every catalog entry stays `connectable: false`, and no customer can reach the flow |
| **End-to-end verification** | The above, plus a real consent round trip |
| **Production credential validation** | A first real call, which is what moves a connection `CONNECTED → VALIDATED` |

**Nothing simulates a completed connection.** The exchange is exercised against a substituted `fetch` in a test and never in the product; a real environment with no credentials refuses before reaching it. **A product that reports a connection it does not have is worse than one that admits it cannot connect yet**, and that has not changed — what changed is that the code between consent and storage now exists and is tested rather than being a comment describing itself.

### Resume conditions

**Steps 2 and 3 were built on 2026-08-04. What remains is credentials and a first handshake:**

1. Put `SIGNORA_HUBSPOT_CLIENT_ID`, `SIGNORA_HUBSPOT_CLIENT_SECRET` and the registered redirect URI in the frontend environment. `credentialsFor()` returns `null` when they are absent, and that absence is what `connectable: false` reflects.
2. ~~Implement the token exchange~~ — **`lib/integrations/exchange.ts`**, RFC 6749 §4.1.3, with §5.2 error codes translated into `ConnectOutcome`s. 22 tests against a substituted `fetch`.
3. ~~Call `ConnectSystem`~~ — **`lib/integrations/record.ts`** posts to `POST /workspaces/{id}/connections` (§4), minting its own access token because a customer returning on a redirect carries cookies and no `Authorization` header.
4. **Confirm the one unverified step.** `identityUrl` and `identityAccountField` in `providers.ts` answer *whose account is this token for*, which no RFC standardises. They are documented behaviour rather than observed behaviour, and a first handshake confirms or corrects them.
5. Flip the catalog entry's `connectable` to `true` — **only once a real handshake has succeeded**, never in anticipation.
6. Add the first real call so a connection can reach `VALIDATED`; that is also the natural home for the first `ProviderRevoker`.

**No further product development is required for acquisition.** If a resuming lane finds itself designing a screen, a state or a port, something has changed underneath this document and the change is the first thing to write down — as it was on 2026-08-04, below.

> ### The resuming lane designed a port, 2026-08-04
>
> **This paragraph asked to be told, and it was right to.** Lane B took Epic E1 (*CRM OAuth and read*) and found that the five steps above describe **acquisition** completely and **synchronization** not at all — and that the sentence in §1, *"Provider Platform owns the synchronization and consumes the relationship through `public/`"*, has never been checked against Provider Platform's code.
>
> **It does not hold as written.** The Provider Port cannot express a customer-held system: `ProviderName` is a closed enum of five ratified suppliers, `ProviderRequest` carries no connection and so has nowhere to put a per-workspace credential, and `ProviderRequest.subject` is required while a CRM sync enumerates rather than asks about one company. `ClaimAttribute` has no CRM concept and says *RFC required to extend*.
>
> **What does hold, and is the useful half of the finding:** `NormalizeRawRecord` keys mappers by `provider: str` and `raw_provider_record.provider` is `String(64)`, so **the canonical shape is already open and no second normalization path is needed.** The gap is entirely in *acquiring* records, not in *interpreting* them. `ExecutionContext` turns out to be exactly the right shape for what an inbound adapter would take — which is why it was built and left unwired.
>
> **The design is [ADR-0300](adr/0300-inbound-customer-systems.md), proposed and not accepted; the blocker is [C-326](../LANE_COORDINATION.md).** Nothing was built against it. **Steps 1–5 above remain correct** — they describe the connection, and the connection is still what a developer application unblocks.

### Known limitations, stated rather than discovered later

- **No credential rotation on a live connection.** A working grant cannot be replaced in place; the customer disconnects and reconnects. **Reconnection itself works** (§4), so the path exists and costs two steps.
- ~~**No `ProviderRevoker` adapter.**~~ **Built 2026-08-04** (§4). Two systems have endpoints; anything else still reports failure honestly.
- **The read has no caller.** `HubSpotCompanies` fetches and translates every failure, and nothing invokes it: **who calls it is exactly what [ADR-0300](adr/0300-inbound-customer-systems.md) decides.** The properties it requests come from `HubSpotCompanyMapper.translated_properties()` and a test asserts the two sets are equal — **a CRM returns only what you ask for**, so a mapped property nobody requests is a claim that silently never appears.
- **Refresh happens on use, and there is no scheduled sweep.** `ResolveExecutionContext` renews an expired grant and returns a working context, so a caller never learns the credential lapsed. That needs no scheduler — and none exists: `WorkerSettings` has no `cron_jobs`, and adding one is runtime composition rather than this module's. **A grant that expires while nothing is using it stays expired until something is**, which is the correct time to care and is stated so nobody later reads the absence as an oversight.
- **Two client-credential values, one per tier.** Acquisition reads `SIGNORA_HUBSPOT_CLIENT_ID`/`_SECRET` from the Next environment; renewal reads `SIGNORA_INTEGRATIONS_CLIENT_CREDENTIALS` here. **Both are the same registration and a deployment must keep them in step.** It is stated rather than solved: a vault ([ADR-0022](adr/0022-devops-infrastructure-and-deployment-topology.md), M14.5) is what collapses them to one, and until then the interface means only `SettingsClientCredentials` changes.
- **`ResolveExecutionContext` is now wired and still uncalled.** `build_resolve_execution_context` exists because the resolver can finally do its whole job — resolve, and renew what has expired. **Its consumer is whatever synchronizes through a connection**, which is [ADR-0300](adr/0300-inbound-customer-systems.md)'s to decide.
- **Nothing synchronizes.** This module records relationships. The first consumer is Provider Platform, and it has not arrived.
- **No navigation entry.** `/settings/connections` is reachable by URL and nothing links to it — the shell is Lane A's, recorded as a coordination item rather than edited across a boundary.

---

## 10 · Recorded direction — the next question is confidence, not connection

**Product owner, 2026-08-02, recorded rather than implemented.**

> **Customers do not care about connections. They care about confidence.**

Everything in §6 answers *is it connected?* The questions a customer actually has are one level above it:

*Can I trust this connection? · Is my CRM actually healthy? · Is Signora receiving fresh data? · Is anything silently failing? · Has anything changed recently? · Will this affect my recommendations? · What business capability is degraded because of this?*

**None of those is answerable by this module alone, and that is the point of writing them down here.** *Fresh data* and *silently failing* are facts about **synchronization**, which is Provider Platform's; *has anything changed* is **Timeline's**; *will this affect my recommendations* crosses into the intelligence pipeline. A connections screen that tried to answer them would be this module deriving judgements it has no evidence for — the same error `Attention` was carefully kept away from by deriving only from the connection and its grant.

**What this module can honestly contribute is the input, not the verdict:** the connection's state, its grant's lifetime, and eventually the result of a real call — which is exactly what `VALIDATED` was reserved for and what nothing yet produces.

> **The third input arrived on 2026-08-04 as [TASK-407](../BACKLOG.md), and §12 below is it.** *Can I trust this connection?* is now answerable from evidence rather than from records. The rest of the list above is unchanged and still not this module's — freshness is Provider Platform's, *what changed* is Timeline's, and *will this affect my recommendations* crosses into the pipeline.

**The trigger to revisit** is the first consumer: when Provider Platform synchronizes through a Connected Account, *"is Signora receiving fresh data?"* becomes answerable from a watermark it already owns, and the composition of the two into one confidence answer is a design question for whichever module owns that screen. **It is not a reason to add a field here first.**

## 11 · The tests, and what each layer is for

Domain and application against **fakes**; infrastructure and interface against **real PostgreSQL as `signora_app`**. The split matters more here than usual, and B-024 is the worked example: every repository was exercised only through doubles, **the doubles accepted a `ConnectedAccount` the database would not** — `created_by` and `updated_by` are `NOT NULL` and nothing supplied them — and every insert would have failed the first time a customer connected anything, with a green suite throughout.

Three defects came out of closing it, none of which a fake could have surfaced: the missing audit columns, the write ordering against the foreign keys (§4), and `ConnectionNotFound` escaping as a `500` because it had no entry in the central error mapping.

**The lesson is general enough to state here:** a fake that reimplements a rule can only agree with itself. Where the rule lives in the database — a constraint, an ordering, a keyset predicate, RLS — the test has to be there too.

---

## 12 · The connection that looks perfect and does not work

**Built 2026-08-04, [TASK-407](../BACKLOG.md)**, from Lane C's [417 §4 slice B-i](417-executable-slice-audit.md), against the approved **CRM Integrations** screen: *"Health is checked every minute. Two consecutive failures pause writes."*

**Everything §6 answers is derived from records** — a grant exists, it has not expired, nobody revoked it. **None of that is evidence.** The commonest way an integration breaks is a credential that authenticates perfectly and has quietly lost a permission, and no record anywhere can see it. Until this slice the Connection Center reported such a connection as healthy, which is the failure the whole screen exists to prevent.

**`ConnectionState.VALIDATED` was written for this and had never been reachable.** Its docstring already said *"a real call succeeded with it… a grant that authenticates but lacks a scope is the commonest integration failure and is indistinguishable from healthy until the first sync."* The state was correct; nothing performed the call that earns it. **It is earned here and nowhere else.**

### What the slice is

| | |
|---|---|
| **`ProbeResult`** | The adapter's `Crm*` taxonomy expressed once in this module's words — reachable · credential rejected · permission missing · unusable response · unavailable. **No third vocabulary between them** |
| **`ConnectionProbe`** | One recorded attempt. **Immutable**, migration `0038`, no `UPDATE` grant, registered in `tenancy_policy.py` |
| **`health_from`** | What a *run* of probes means. **Derived on every read, never stored** — a `health` column would be wrong the moment a credential was revoked without anybody writing to it |
| **`ProbeConnection`** | Resolves, asks, records, and moves the connection when the answer settles something |
| **`HubSpotReachability`** | The anticorruption layer. One company, one property — the question is whether the door opens |
| **`POST /connections/{id}/check`** | Owner-only. **A `POST` because it does something**: it spends the customer's own API quota and writes a record |

### Four decisions worth keeping

**A single transient failure is not a verdict.** It takes **two consecutive** inconclusive results to report a connection as not working. A vendor having a bad minute must not send somebody to reconnect a CRM that is fine — and *consecutive* means consecutive: a success in between breaks the run.

**Nothing tried is `UNKNOWN`, never healthy.** An unprobed connection is one nobody has established anything about, and reporting it as working would be the same lie the record-derived view already tells. The screen says nothing rather than claiming *Checked and working*.

**A probe does not revoke a connection, and the first draft did.** `REVOKED` means *the customer withdrew permission at the vendor* and reaches a screen as *access was removed in the other system*. **A rejected credential is not evidence of that** — a rotated secret, an unreadable stored material and a vendor authentication incident are indistinguishable from a `401`, and telling a customer they revoked Signora when they did not is a worse failure than the one this slice set out to fix. Degraded health carries it instead, with the reason `not_working`: what happened, and no diagnosis nobody established.

**A missing permission is not a rejected credential.** The adapter's own distinction between `401` and `403` survives all the way to what the platform does: reconnecting with the same permissions would fail identically, so a `403` never asks a customer to reconnect.

### Why this could be built while C-326 is open

**The probe reads, classifies and discards.** No raw record, no claim, no event, no watermark — asserted by a test that counts `raw_provider_record`, `claim` and `outbox_event` across a check and finds them unchanged. **[C-326](../LANE_COORDINATION.md) decides how a customer's records *travel*; this decides whether the door is open**, and the two share no artifact. [419 §2](419-c326-narrowed-and-lane-b.md) is the measurement that made the distinction visible.

### Its limits, stated rather than discovered later

- **Nothing schedules it.** The approved screen says *"checked every minute"*; this is checked when somebody asks. **A scheduler is 🔴 and this repository does not have one** — ARQ exists and a periodic sweep is a slice with its own trigger, not something to add inside this one.
- **One vendor.** `HubSpotReachability` is wired directly rather than through a registry keyed by slug: the second adapter is the change that earns a registry, and it will arrive with one to put in it.
- **No writes are paused, because there are no writes.** That is E2.
- **No signal to admins.** Notification delivery is [ADR-0040](adr/0040-notifications.md) and unratified.
- **`connectable` is still `false` for every catalog entry.** It flips after a real handshake against a real developer application, never in anticipation (§9).

---

## 13 · The inbound source port — how a customer's system reaches the pipeline

**Built 2026-08-04**, the moment [ADR-0300](adr/0300-inbound-customer-systems.md) was approved as **Option A** by the product owner, to the contract in [409](409-inbound-source-port-contract.md). **The ADR is awaiting integration synchronization**, and this code is held on its lane branch until Product Office's set reaches `integration` ([`PRODUCT_OFFICE.md`](../PRODUCT_OFFICE.md) §11c). **This module's half only** — steps 1, 2 and 6 of that document's seven.

**The sentence it turns on** is the one §1 already records: *a provider is Signora's supplier and Signora holds the credential; an integration is the customer's own system and the customer holds it.* The Provider Port asks a supplier **about one company**. This asks a customer's system for **the customer's own records** — and **an enumeration has no subject**, which is why a sibling exists rather than an extension.

### What is here

| | |
|---|---|
| **`domain/source.py`** | `IntegrationSourceAdapter` · `IntegrationFetchRequest` · `IntegrationRecord` · `IntegrationPage` · `IntegrationSourceDescriptor` · the error hierarchy, mirroring the Provider Port's exactly |
| **`domain/execution.py`** | `ExecutionContext`, **moved out of `application/`** — a domain port cannot name a type defined in an outer layer |
| **`Capability.CRM_RECORDS`** | Added, and **deliberately not in `LIVE_CAPABILITIES`** |
| **`infrastructure/hubspot_source.py`** | `HubSpotCompanySource` — the wrapper, translation only |
| **`public/`** | The port is published, because its driver is another module |

### The four properties worth keeping

**No `subject`.** Asserted structurally, because a `subject` field appearing here would be the Provider Port arriving under a different name, and it would look like ordinary code.

**This module's `Capability`, never `ProviderCapability`.** One enumerates what suppliers sell — enrichment, technographics, workforce — and a CRM read is none of them. **Two vocabularies with two owners, kept apart by the type rather than by a comment.**

**`integrations` imports nothing from `provider_platform`.** The port is defined by the module that owns its language; the driver depends on the port and not the reverse. **`ProviderName` stays closed** and no catalog slug is ever added to it — it means *"a supplier with a ratified qualification record"*, and that guarantee is worth more than one shared enum.

**`occurred_at` is `hs_lastmodifieddate`, and it is the same field the fetcher filters on.** Watermark, filter and record timestamp must be one field or a sync re-reads or silently skips — [B-004](../BUGS.md)'s class. **An unreadable one raises rather than defaulting to `now()`**, which would advance the position past records nobody has seen.

### Why `CRM_RECORDS` is not live

**The port exists and nothing drives it.** The runner is [409](409-inbound-source-port-contract.md) step 4, in `provider_platform`. Advertising the capability now would be the Connection Center promising something the pipeline cannot deliver — **the one thing `LIVE_CAPABILITIES` exists to prevent** (§9). It joins the set when the runner lands, and a test asserts the absence rather than a comment requesting it.

### What is not here, and whose it is

| Step | | |
|---|---|---|
| **3** | Widen `provider: ProviderName` → `str` on the four sync events | `provider_platform` — **Lane A's** |
| **4** | `RunIntegrationSync`, and the watermark's widened meaning | `provider_platform` — **🔴, and the product owner's to assign** |
| **5** | A simulated source adapter driving the whole path with no vendor | `provider_platform` |
| **7** | The live run | Needs the **HubSpot developer application**, which is environmental |

> **Step 5 is the one to insist on.** It proves the contract end to end — port, runner, watermark, raw record, event, mapper, claims — **with no credential and no developer application**, and a lane that merges it with step 7 debugs OAuth and ingestion at once.

**`build_hubspot_source(properties)` is wired and called by nothing**, exactly as `build_resolve_execution_context` was before the probe. **The properties are a parameter** because they are `HubSpotCompanyMapper.translated_properties()` and that mapper is Provider Normalization's: the composition root is the only place that may see two modules' infrastructure at once, and a second property list here would defeat the test that keeps the fetcher and the mapper in step.

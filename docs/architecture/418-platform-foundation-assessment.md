# 418 — Platform Foundation: repository impact and capability assessment

> **Lane C — Product Office, 2026-08-04.** The ten platform-foundation modules are delivered and final. **Read in full**, not sampled. Measured against `origin/integration`.
>
> Companion to [415](415-platform-foundation-incoming.md), which held the line while they were produced. **This document replaces its speculation with measurement.**

## 1 · Inventory, and one defect in the source

**Twenty-six approved screens now: sixteen business, ten platform foundation.**

| # | Module | Scope |
|---|---|---|
| **1** | **Authentication** | 16 states · one 400px card · SSO branch points |
| **2** | **Onboarding** | 6 steps, one required · *"asks for four and infers the rest"* |
| **3** | **Workspace Setup** | Region · URL · domain verification · branding · deletion |
| **4** | **Team Management** | Invitations · bulk CSV · seats · roles · accept/decline/expired |
| **5** | **User Profile** | Personal, and **three field ownerships** |
| **6** | **Security Center** | Sessions · devices · MFA · step-up · *Secure my account* |
| **7** | **Notification Center** | Event×channel matrix · digests · quiet hours · custom rules |
| **8** | **Billing** | Annual commitment · true-up · notice period · read-only degradation |
| **9** | **Help Center** | Tickets · contractual SLAs · regional status · version-aware docs |
| **10** | **System States** | **15 states, one grammar, three questions before a button** |

> ⚠️ **The design project contains two Workspace Setup files, and they are not identical.** `Fortune Signora Workspace Setup.dc.html` (88,887 B) and `Workspace Setup.dc.html` (88,764 B), **both labelled *Platform foundation · Module 3***. Diffed: the only difference is a **responsive-layout fix** — `flex-wrap`, `white-space: nowrap`, and the Replace/Remove controls grouped — present in the prefixed file and absent from the other.
>
> **So `Workspace Setup.dc.html` is a superseded earlier copy.** `CLAUDE.md` §2 — *truth has exactly one authoritative representation* — and the authoritative source now has two. **Lane C reports it and does not delete it**: the design project is the product owner's.

## 2 · The finding I raised in [415](415-platform-foundation-incoming.md) §3, and its answer

**I reported that the incoming modules would overlap the approved sixteen in seven places, and recommended settling ownership before both were ratified.**

> **The designs settled it themselves, and used the App Shell's own rule to do it.**

| Evidence, quoted from the delivered designs | |
|---|---|
| **Security Center** — *"Workspace-wide controls live in **Settings** and are shown here as context, **never as something you can change**"* | ✅ defers |
| **Security Center** — *"Salesforce is shown on a tinted row because it belongs to the workspace, not to you… the control lives in Settings"* | ✅ defers |
| **System States** — full-page states *"**keep the shell** and centre their content"*; the rail *"collapses to icons but stays, because losing navigation during an error strands people"* | ✅ defers |

**And the split is consistent across all ten**, declared in each module's own subtitle: **`personal surface`** (Profile, Security, Notifications) versus **`admin surface`** (Workspace Setup, Team Management). **Nothing is specified twice.**

> **The concern was worth raising and the answer is that it was already handled.** Recorded as a withdrawal in §7 rather than left looking like an open risk.

**This produces a real architectural line, and it is the most useful thing in this document:**

> **Person-scoped configuration and workspace-scoped configuration are different aggregates.** A profile preference, a notification matrix and a session belong to a **person within a workspace**; branding, domain verification, SSO enforcement and seats belong to the **workspace**. **Both are workspace-tenanted and only one is workspace-owned** — and `CLAUDE.md` §8 requires every new table to declare which before it ships.

## 3 · Capability matrix — the ten platform modules

**Classified in the vocabulary the directive names.**

| Module | Classification | Built and reusable | Missing |
|---|---|---|---|
| **4 · Team Management** | **PARTIALLY READY** | **8 of `workspace_tenancy`'s 13 endpoints** — members, invitations, resend, revoke, ownership, role, remove, history | Invitation **expiry** (7d, single-use, address-bound) · **bulk CSV** with per-row validation · **seats** and reclaim · **Guest** role for unverified domains · **decline** |
| **1 · Authentication** | **PARTIALLY READY** | **Better Auth** — Google, Microsoft, email+password, verification, forgot/reset. `18-authentication.md` | **Magic link** · **MFA / recovery codes** · **per-workspace SSO enforcement** · domain→IdP routing · session-expiry state · invitation sign-in |
| **5 · User Profile** | **API MISSING** | Theme provider · theme toggle | Profile · locale · timezone · accessibility · shortcut remapping · **the three-way field-ownership model** |
| **2 · Onboarding** | **PARTIALLY READY** | `POST /workspaces` · **`ProviderCapability.COMPANY_ENRICHMENT`** — *"infers the rest from the email domain, the enrichment record behind it"* | Onboarding state · step progress · inferred-value marking · **goals→features** |
| **3 · Workspace Setup** | **DOMAIN MISSING** | `workspace_tenancy` workspaces · `44-integrations.md` for callbacks | **Data region** *(permanent, no migration path — a tenancy matter)* · **URL change with forwarding and callback impact** · **DNS TXT domain verification** · branding with a 4.5:1 contrast gate · deletion |
| **6 · Security Center** | **BACKEND MISSING** | Password reset via Better Auth · `18-authentication.md` | Sessions · devices · login history · MFA · backup codes · **step-up (10 min)** · **the *Secure my account* cascade** · breach check |
| **7 · Notification Center** | **BLOCKED BY PRODUCT** | Outbox, relay, dispatch, idempotency, dead-lettering, ARQ — **the whole delivery substrate** | The module. **[ADR-0040](adr/0040-notifications.md) unratified**; `MESSAGE_DELIVERY` absent from `LIVE_CAPABILITIES` |
| **8 · Billing** | **BLOCKED BY PRODUCT** | — | The module. **[C-200](../LANE_COORDINATION.md) unruled**; [42-billing-and-entitlements.md](42-billing-and-entitlements.md) is discovery |
| **9 · Help Center** | **BACKEND MISSING** | **`correlation_id` propagates end-to-end** (§16) — *"every route into support arrives carrying the workspace, the plan, the screen, and the correlation ID"* · `live_capabilities` for per-connection health | Tickets · SLA clocks · status feed · doc versioning |
| **10 · System States** | **PARTIALLY READY** | `error.tsx` · `not-found.tsx` · `ui/skeleton` · `ui/empty-state` · **App Shell §16–18** | Failure **scoping** (widget / region / page) · **local draft and filter preservation** · 404 merge provenance · 403 role-request |

## 4 · Three places the approved design and the ratified architecture already agree

**None of these was reconciled — they were written independently and match.**

> **System States:** *"Where the existence of a record is itself confidential, the platform returns **404 instead of 403**."* **`CLAUDE.md` §7:** *"A caller who is not a member of the workspace they name gets `404`, never `403`. This is a security property… not an inconsistency to tidy up."*

> **Help Center:** *"Signora writes to three Salesforce fields and reads from twelve. The write set is deliberately small: an integration that can modify arbitrary fields cannot be reasoned about during a security review."* **[ADR-0401](adr/0401-a-customers-crm-is-not-a-provider.md)**, and the approved CRM Integrations screen, say the same thing.

> **Notification Center:** *"No suggestion is applied automatically — a product that quietly stops notifying you is indistinguishable from one that is broken."* **`MACHINE_AUTHORED = frozenset({Stage.TRACKING})`** — *intelligence suggests, humans commit.*

**Where an approved design and a ratified ADR agree without having been reconciled, neither needs to move.** That is the cheapest evidence available that both are right.

## 5 · Two cross-cutting consequences that are not any one module's

### 5a · Billing's read-only degradation reaches every module

> *"On 22 August the workspace becomes **read-only**: everyone can sign in, read and export, and nothing is deleted. **Agents stop, integrations stop writing, and new records cannot be created.**"*

**That is an entitlement enforced at every write path in the repository** — not a billing screen. It is the same shape as `live_capabilities`, and it is 🔴.

**It is also evidence for [C-200](../LANE_COORDINATION.md).** The question is whether M14b is one module, two or three; **this design shows the customer-visible half is a state the whole platform reads**, which is an argument about where the boundary falls rather than a new question.

### 5b · Two modules now compute "precision", and they must not do it twice

**Signal Center:** *"Rules below 60% acted-on are proposed for retuning automatically."* **Notification Center:** *"Each rule carries its own **precision figure** — how often it fired and how often you acted — because a rule you never act on is not a preference, it is noise you configured yourself."*

> **Same mechanic, two modules, and `CLAUDE.md` §4 forbids a second definition of a concept a module already owns.** **[TASK-405](../BACKLOG.md) explicitly excludes rule precision** — that exclusion is now load-bearing rather than merely scope-limiting, and whoever builds the second one must reuse the first.

## 6 · Priority — dependency order, not design order

**Following the directive's own ranking: shared platform capability, then foundations, then workflows, then business value.**

| | | Why |
|---|---|---|
| **1** | **Team Management gaps** | **Highest reuse in all 26 screens.** Eight endpoints exist; expiry, seats and bulk are additive |
| **2** | **System States scoping** | **Every screen inherits it.** *"One chart cannot reach its service, and a person loses their filters"* is a defect in 26 screens at once |
| **3** | **Authentication gaps** | Gates Onboarding and Team Management's accept flow. **Next.js tier only** |
| **4** | **User Profile** | Person-scoped aggregate — **the pattern Notification Center then reuses** |
| **5** | **Workspace Setup** | Domain verification gates SSO enforcement and join-without-invitation |
| **6** | **Onboarding** | Needs 3 and 5; reuses enrichment |
| **7** | **Security Center** | Largest, and needs MFA from 3 |
| **8** | **Notification Center** | **Blocked on ADR-0040** |
| **9** | **Billing** | **Blocked on C-200** |
| **10** | **Help Center** | Nothing depends on it |

**Waves 1–7 in [412](412-backend-capability-matrix.md) are unchanged.** This is a parallel track: **platform foundation is mostly `workspace_tenancy` and the Next.js auth tier, and touches almost none of the intelligence pipeline.**

## 7 · Corrections and withdrawals

| | |
|---|---|
| **Withdrawn** | **[415](415-platform-foundation-incoming.md) §3's overlap risk.** I predicted seven contested surfaces; the delivered designs defer explicitly in every case, using the App Shell's own amendment rule. **Right to raise, and already handled** |
| **Corrected** | **[413](413-migration-inventory.md)'s auth files move from `PENDING` to `REPLACE`** — Module 1 exists, and the 11 files have an approved successor |
| **Corrected** | **[415](415-platform-foundation-incoming.md) called Module 5 and Module 6 an internal overlap on *Connected Accounts*.** They are not: **Module 6 shows workspace integrations as read-only context and names Settings as the control.** Withdrawn |
| **Clarified** | **O2's hold was correct.** Notification Center is an event×channel matrix with per-person volume measurement, digests, quiet hours and custom rules — **not the App Shell's popover.** ADR-0040 must be read against it before ratification |
| **Reported, not fixed** | The duplicate Workspace Setup file |

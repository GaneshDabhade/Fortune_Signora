# 493 · Security as platform capability — the reference architecture

**Lane C · Product Office · 2026-08-08.** **[D-174](../DECISION_REGISTER.md) *(issued as D-173; see the note at §0)*, which asks the fundamental question rather than the screen question: *"What security capabilities should exist as reusable platform services that every current and future workflow can inherit?"***

> ⚡ **Sources are labelled throughout, as [D-171](../DECISION_REGISTER.md) §6 requires: 📁 repository evidence · 🌐 external research · 🧠 this office's judgement.**

---

## 0 · ⚠️ Two things before the analysis

**① A decision-register collision.** **This ruling arrived as `D-173`, and `D-173` is already the synchronization model review recorded on 2026-08-08.** ⛔ **Recorded here as `D-174`.** ⚡ **`D-` numbers are the product owner's block (`900+` is theirs for tasks, but the decision register has always been sequential and single-author) — this is the first collision in it, and it is worth one sentence: the register has no allocation guard, unlike `B-`, `C-` and `TASK-`, which `state-check` checks.**

**② The headline finding, before the matrix.**

> ## 🌐 **Better Auth's SSO plugin already provides domain→IdP routing, SAML 2.0, per-organization SSO, and domain verification by DNS TXT record.**
>
> ## ⛔ **[418](418-platform-foundation-assessment.md) lists *per-workspace SSO enforcement*, *domain→IdP routing* and *DNS TXT domain verification* as three separate Signora gaps across two workflows. They are one plugin.**

⚡ **That single finding changes [C-431](../LANE_COORDINATION.md), Workflow 1's SSO control, Workflow 5's screen `04`, and Workspace Setup's domain verification — and it was found by reading the plugin catalogue rather than by reasoning about it.**

---

## 1 · 📁 Current repository assessment

| | Measured |
|---|---|
| **Better Auth configuration** | **`frontend/lib/auth/server.ts`** — email+password with `minPasswordLength` and `requireEmailVerification: true` · email verification with `sendOnSignUp` and `autoSignInAfterVerification` · password reset · `socialProviders` · `session` with `expiresIn` 7 days and `updateAge` 1 day |
| ⛔ **Plugins configured** | **None.** **`grep plugins frontend/lib/auth/server.ts` returns nothing** |
| **Authorization** | **Casbin — `signora_platform/authorization/` with `model.conf` and `policy.csv`, and a `Resource` enum of 15 members** |
| **Tenancy** | **`workspace` · `membership` · `invitation` · `membership_role_change` · `saved_view`.** ⚡ **`membership_role_change` is an audit row and nobody calls it that** |
| **Person scope** | ✅ **`app.user_id` set on every transaction; RLS policies in migrations `0001` and `0003` already read it** ([492](492-person-scoped-tenancy.md)) |
| **JWT** | **RS256 verification only, in `signora_platform/auth/jwt_verifier.py`. The Python tier never signs** ([ADR-0026](adr/0026-jwt-boundary-architecture.md)) |

> ## ⚡ **The single most useful fact: Better Auth is running with zero plugins.** **Every capability below marked *Reuse Better Auth* is a configuration change to one file, not an integration project.**

---

## 2 · 🌐 Better Auth capability mapping — researched, not recalled

**Current line: 1.5. Plugins confirmed in the official catalogue:**

| Plugin | What it provides |
|---|---|
| **Two-Factor** | **TOTP and OTP, with server routes and client methods** |
| **Passkey** | ⚡ **WebAuthn / FIDO2, its own package, its own table, conditional-UI autofill** |
| **Organization** | **Roles — owner, admin, member — a flexible access-control system, and custom permission sets** |
| **Multi-Session** | **Concurrent sessions across devices, with listing and revocation** |
| **SSO** | ⚡ **OIDC *and SAML 2.0*, domain→IdP mapping, per-organization providers, DNS TXT domain verification, attribute mapping, provisioning callbacks** |
| **OIDC Provider** | **Signora *as* an identity provider — not needed now, and worth knowing exists** |
| **Admin** | **User administration, impersonation, ban/unban** |

---

## 3 · The build-versus-reuse matrix

**🟢 Reuse Better Auth · 🔵 Extend Better Auth · 🟡 Reuse other OSS · 🔴 Build in Signora**

### Identity

| Capability | Verdict | Why |
|---|---|---|
| **Authentication · OAuth providers** | 🟢 | 📁 **Already running** |
| **Passkeys · WebAuthn** | 🟢 | 🌐 **A plugin.** ⛔ **Building WebAuthn is building cryptography — the clearest commodity on this page** |
| **MFA · TOTP · Recovery codes** | 🟢 | 🌐 **The two-factor plugin.** ⚠️ **Recovery-code *presentation* is ours; generation and verification are not** |
| **SAML · OIDC · Enterprise SSO** | 🟢 | 🌐 **One plugin, and it closes three separate gaps [418](418-platform-foundation-assessment.md) records as builds** |
| **Password policies** | 🔵 | 📁 **`minPasswordLength` exists.** **The design specifies four rules including a breach-corpus check** — 🌐 **that is `haveibeenpwned`'s k-anonymity API, ⛔ never a corpus we host** |

### Sessions

| Capability | Verdict | Why |
|---|---|---|
| **Active sessions · revocation · concurrent control** | 🟢 | 🌐 **Multi-session plugin** |
| **Session timeout · history** | 🔵 | 📁 **`expiresIn`/`updateAge` exist; *history* is an audit projection** |
| **Device management · trusted devices** | 🔵 | 🌐 **Sessions carry user-agent and IP.** 🧠 **"Trusted device" is a *policy* over that data — the mechanism is Better Auth's, the meaning is ours** |

### Authorization

| Capability | Verdict | Why |
|---|---|---|
| **RBAC · permission evaluation · policy enforcement** | 📁 **Already built — Casbin** | ⛔ **Do NOT adopt Better Auth's organization roles.** ⚡ **[§13](../../CLAUDE.md) makes Casbin the authorization decision and [§7](../../CLAUDE.md) requires `workspace_id` in every policy tuple. Two role systems is [§2](../../CLAUDE.md)'s two-representations defect in the security layer** |
| **Workspace roles** | 📁 **Already built** | **`membership.role`, and `membership_role_change` already records every transition** |

### Security monitoring — 🔴 **where Signora's work actually is**

| Capability | Verdict | Why |
|---|---|---|
| **Login history** | 🔵 | **Better Auth owns the events; the *timeline* is ours** |
| **Audit events · security timeline** | 🔴 | ⚡ **This is the domain.** 📁 **The repository already publishes an immutable outbox and `membership_role_change`; what is missing is one audit stream every module writes to** |
| **Risk signals · suspicious login · impossible travel · geo** | 🔴 | 🧠 **And this is the differentiator.** ⚡ **Signora already computes buying signals from behaviour; a *security* signal is the same pipeline with a different catalogue** |
| **Device fingerprinting** | 🟡 | 🌐 **A commodity library, ⛔ and a privacy decision before a technical one** |

### Compliance · administration

| Capability | Verdict | Why |
|---|---|---|
| **Security reports · audit export · compliance logs · evidence history** | 🔴 | ⚡ **Enterprise-buyer surface, and [§2](../../CLAUDE.md)'s immutability rules already describe how to store it** |
| **Data retention** | 🔴 | 📁 **`TASK-426` already exists** |
| **Org security settings · password requirements · session policies · MFA enforcement · provider config** | 🔵 | 🧠 **Better Auth enforces; the *policy object* is workspace-owned and is ours** |

---

## 4 · 🧠 The architecture — five platform services, and the Security Center consumes them

> ## **The Security Center is a *screen*. These five are the platform, and four of them have consumers long before it exists.**

| Service | Owns | First consumer | Also consumed by |
|---|---|---|---|
| ⚡ **`SecurityEvent`** — one append-only stream | **Authentication, authorization and administrative facts** | **Workflow 1 (Login) — already producing them** | **Team Management · Settings · Workspace Setup · Security Center · Compliance** |
| **`SessionService`** | **List, revoke, describe a device** | **Workflow 5 (Password Reset)** — *"signs you out of 4 other devices"* | **Settings · User Profile · Security Center** |
| **`PersonSetting`** ([492](492-person-scoped-tenancy.md)) | **Person-scoped preference** | **Workflow 9 (User Profile)** | **Notifications · Theme · Accessibility · Copilot** |
| **`WorkspacePolicy`** | **Workspace-owned security policy** | **Workflow 6 (Workspace Creation)** | **Team Management · Security Center · SSO enforcement** |
| **`RiskSignal`** | **Derived security signals** | **Security Center** | **Notifications · Compliance** |

⚠️ **Note which appears first: `SecurityEvent` has a producer *today*, in the workflow already on `main`.** ⛔ **Every day it does not exist is a day of login history nobody can reconstruct** — [§2](../../CLAUDE.md): *"the record cannot be added retroactively; the runs that would have explained the problem are gone."*

---

## 5 · 🧠 Challenging the premise — [D-174](../DECISION_REGISTER.md) §7

| | |
|---|---|
| ⛔ **Security Center should not be one screen** | ⚡ **The design's own sixteen capabilities split cleanly by *audience*: a **person** manages their devices, passkeys and MFA — that is **User Profile**; an **administrator** sets policy and reads the audit — that is **Settings › Security**.** 🧠 **A single "Security Center" merges two audiences with different permissions and different frequencies.** ✅ **Recommend: the capabilities ship into the two screens that already exist, and Security Center becomes the *administrator* half rather than a new destination** |
| ⚠️ **The audit stream should not be security-specific** | 📁 **`membership_role_change` already exists and is an audit row that does not know it.** 🧠 **One `SecurityEvent` stream that is really an *account activity* stream serves compliance, support and the customer's own timeline** — ⛔ **building a security-only log means building the second one later** |
| ⚡ **Adopt the plugins in one slice, not per workflow** | 🧠 **Passkey, two-factor, multi-session and SSO are four configuration blocks in one file.** ⛔ **Spreading them across four workflows means four migrations and four review cycles for what is one change** |

---

## 6 · Roadmap — ordered by *what unblocks the most*, not by screen

| | Slice | Unblocks |
|---|---|---|
| **1** | ⚡ **`SecurityEvent` — the append-only stream and its first producers** | **Login history · audit · compliance · risk.** ⛔ **Earliest, because the data is unrecoverable** |
| **2** | **Better Auth plugin adoption — SSO, multi-session, two-factor, passkey** | 🔴 **[C-431](../LANE_COORDINATION.md) · Workflow 1's SSO control · Workflow 5 screen 04 · Workspace Setup domain verification** |
| **3** | **`SessionService` over the multi-session plugin** | **Workflow 5's device count · User Profile · Settings** |
| **4** | **`WorkspacePolicy`** | **SSO enforcement · MFA enforcement · session policy** |
| **5** | **`RiskSignal`** | **Security Center's differentiating half** |

⚡ **Slices 1 and 2 are both prerequisites of workflows already in the pipeline.** ⛔ **Slice 5 is the only one that waits for Security Center itself.**

---

## 7 · Risks, and the one that matters

| | |
|---|---|
| 🔴 **Two role systems** | **Better Auth's organization plugin ships roles. Casbin is the authorization decision.** ⛔ **Adopting the organization plugin for *roles* would create a second authority.** ✅ **Adopt it — if at all — for its *SSO linkage* only, and keep every authorization decision in Casbin** |
| ⚠️ **Plugin tables are Better Auth's schema** | 📁 **`authSchema` already separates it, and the Python tier only verifies RS256.** ✅ **The boundary [ADR-0026](adr/0026-jwt-boundary-architecture.md) draws already holds** |
| ⚠️ **`haveibeenpwned` is an outbound call in a request path** | 📁 **[§7](../../CLAUDE.md)'s four conditions permit it — the call's result *is* the response, nothing enters the pipeline, it is timeout-bounded, and it goes through a port** |

---

## 8 · The recommendation

> ## ✅ **Reuse Better Auth for all of identity and most of sessions — four plugins, one file. Keep authorization in Casbin, unchanged. Build exactly three things: the security event stream, the workspace policy object, and risk signals.**
>
> ## ⛔ **And build the stream first, because it is the only capability whose data cannot be recovered later.**

⚡ **This matches [D-174](../DECISION_REGISTER.md) §3's stated default without being chosen to match it: everything commodity is reused, and the three built items are the three where Signora's domain — workspace tenancy, an immutable evidence model, and a signal pipeline — already gives it an advantage nothing off the shelf has.**

# 415 — Platform Foundation: ten incoming design modules

> **Lane C — Product Office, 2026-08-04.** Recorded on the product owner's Transition Update. **A second Design Project is being produced.** It is not a redesign; it is the platform foundation the first project does not cover.
>
> **This document holds the line and does the work that does not depend on the designs.** No implementation package is finalised for any of these ten areas, no frontend is assumed, and no placeholder screen is written.

## 1 · The hold, stated exactly

**Frozen until the approved designs arrive:** frontend assumptions · screen specifications · implementation packages for these ten areas · any wave placement for them.

**Not frozen, and done below:** backend capability that already exists · dependencies · architecture · reuse · missing APIs · domain requirements.

> **The distinction matters because most of this backend is already built.** Team & Invitation is **eight of `workspace_tenancy`'s thirteen endpoints**, and Authentication is a working Better Auth installation. **Waiting for a design is not a reason to be ignorant of what the repository already does.**

## 2 · Backend capability, per incoming module

| | Module | Already built | Absent | |
|---|---|---|---|---|
| **1** | **Authentication** | **Better Auth in Next.js** — sign in, sign up, **Google**, **Microsoft**, email + password, email verification, forgot and reset password. 11 frontend files, `18-authentication.md` | Magic link · MFA · account locked · session expired · invitation login | 🟩 |
| **2** | **First-time onboarding** | `POST /workspaces` · `no-workspace` component · App Shell §18 already specifies an activation checklist | Company info · industry · size · role · team size · business goals · AI personalisation · progress | 🟠 |
| **3** | **Workspace setup** | `POST`/`GET /workspaces` · `GET /workspaces/{id}` · workspace switcher | Branding · domain configuration · workspace URL · preferences | 🟠 |
| **4** | **Team & invitation** | **8 endpoints** — members `GET`/`POST`, invitations `GET`/`POST`/resend/revoke, ownership, role change, remove, history. Plus components and tests. `46-team-management.md` | **Structurally, almost nothing** | 🟩 |
| **5** | **Profile & preferences** | Theme provider · theme toggle | Profile · language · timezone · accessibility · AI preferences · connected accounts | 🟠 |
| **6** | **Security Center** | Password reset, via Better Auth | Sessions · devices · login history · **MFA** · backup codes · recovery · security alerts | 🔴 |
| **7** | **Notification Center** | **Nothing.** [ADR-0040](adr/0040-notifications.md) is `Proposed`; `MESSAGE_DELIVERY` is absent from `LIVE_CAPABILITIES` | The whole module | 🔴 |
| **8** | **Billing & subscription** | **Nothing.** [42-billing-and-entitlements.md](42-billing-and-entitlements.md) is discovery, **blocked on [C-200](../LANE_COORDINATION.md)** | The whole module | 🔴 |
| **9** | **Help & support** | **Nothing.** App Shell §15 specifies the keyboard-shortcut reference | The whole module | 🔴 |
| **10** | **Platform & system screens** | `error.tsx` · `not-found.tsx` · `ui/skeleton` · `ui/empty-state`. **App Shell §16, §17 and §18 already specify loading, errors and empty workspace** | 403 · 500 · maintenance · offline · permission required | 🟠 |

**Two of the ten are almost entirely built. Four have nothing at all.**

## 3 · The finding that is worth raising now rather than later

> **The ten incoming modules overlap the already-approved sixteen in at least seven places, and one place inside their own set.**

| Already approved | Incoming |
|---|---|
| **App Shell §10** — notifications popover, three tabs, unread state, AI-marked items | **Module 7** — Notification Center |
| **App Shell §11** — user menu: who you are, which workspace, which role, appearance | **Module 5** — Profile & preferences |
| **App Shell §15** — keyboard shortcuts, two families, `?` opens the reference | **Module 9** — keyboard shortcuts |
| **App Shell §16 · §17 · §18** — loading tiers, error pages inside the shell, empty workspace | **Module 10** — loading skeletons, 404/403/500, empty states |
| **App Shell §3** — workspace switcher, grouping, search, the two administrative escapes | **Module 3** — workspace switching, preferences |
| **Settings** — SSO enforcement, SCIM, API keys, webhooks, break-glass accounts, audit log | **Module 6** — Security Center |
| **Settings** — branding on exported artefacts, seats counted monthly, invoices | **Modules 3 and 8** |
| — | **Internal:** *Connected Accounts* appears in **both Module 5 and Module 6** |

> ⚠️ **Withdrawn 2026-08-04, when the designs arrived — and wrong in the best way.** **Every one of these surfaces defers explicitly.** Security Center: *"workspace-wide controls live in **Settings** and are shown here as context, **never as something you can change**."* System States: full-page errors *"keep the shell."* And the split is declared in each module's own subtitle — **`personal surface` versus `admin surface`.** **Nothing is specified twice.** The *Connected Accounts* internal overlap is withdrawn with it. **Evidence: [418](418-platform-foundation-assessment.md) §2.**

**This is `CLAUDE.md` §2 — *truth has exactly one authoritative representation* — arriving at the design layer.** Two approved specifications describing one surface will eventually disagree, and **the copy nobody is maintaining is the one somebody will read.**

> **Lane C is not asking for a redesign and is not proposing one.** It is reporting, at the cheapest possible moment, that seven surfaces will need one owner. **Raising it after both projects are ratified costs a reconciliation; raising it now costs a sentence in whichever document ends up owning each surface.**

**The App Shell itself already states the resolution rule**, which is why this is a clarification rather than a decision: *"Every capability a module thinks it needs from the shell is either already here or becomes an amendment to this document."*

## 4 · Effect on the existing decision queue

**Two open items change shape, and neither becomes more urgent.**

| | |
|---|---|
| **O2 — ratify [ADR-0040](adr/0040-notifications.md)** | **Recommend it now waits for Module 7.** O2 was framed on the App Shell's popover, which is a *surface*. **Module 7 is a whole notification module** — preferences, email, in-app, Slack, digests, alert rules, history. Ratifying a notifications ADR days before its approved design lands is how an ADR gets amended in its first week |
| **C-200 — is M14b one module, two, or three?** | **Module 8 is evidence for it, not a replacement.** C-200 asks a bounded-context question about billing, analytics and feature flags; **an approved billing design will show what the customer-visible half actually is.** Still the product owner's, still unchanged in form |

**O1 and O3 are untouched.** Person and the shell services have nothing to do with the platform foundation.

## 5 · Corrections to [413](413-migration-inventory.md)

**One classification made yesterday is now wrong, and one is weakened.**

| | |
|---|---|
| **Authentication pages — was `KEEP`, now `PENDING`** | 413 said *"the approved design project contains no authentication screens; nothing supersedes them."* **That was true of the first project and is false of the programme.** Module 1 specifies 16 authentication screens. **The 11 files are not KEEP and are not yet REPLACE** — they are pending a design |
| **`error.tsx` · `not-found.tsx` — `REPLACE`, but by whom** | Classified `REPLACE` under App Shell §17. **Module 10 also specifies them.** The classification stands; **which document governs it is §3's question** |

**Nothing else in 413 moves.** The 33 `lib/` files, the 6 API routes, the tests and the documentation audit are all unaffected — **none of them is a screen.**

## 6 · What must NOT happen while the designs are produced

| | Why |
|---|---|
| **No temporary UI, no placeholder screen specification** | It would become the contract before the real one arrives — **exactly what `no-mock-data.test.tsx` refuses in code, applied to specification** |
| **No redesign of these ten modules, and no proposed alternative** | They are being produced. **An unsolicited alternative is the redesign the transition directive prohibits** |
| **No second declaration surface in onboarding** | Module 2 lists *industry*, *company size*, *business goals*. **`commercial_profile` already owns ICP, focus, products and target accounts** — *"sentences somebody typed about their own business."* Onboarding must **write into that module**, never beside it |
| **No login route, private key or OAuth flow in the Python tier** | `CLAUDE.md` §13 — **Better Auth is the sole Authentication Authority; the Python tier only verifies RS256.** Module 1 has 16 screens and **none of them changes this** |
| **No wave placement for these ten** | A wave is argued from backend readiness *and* an approved design. **Half the argument is missing** |

## 7 · What continues unchanged

**Everything else.** Waves 1–7 stand ([412](412-backend-capability-matrix.md)), [414](414-wave-1-account-360.md) is unaffected — Account 360 consumes no platform-foundation surface — the documentation audit continues, and the packages for the sixteen business screens continue converging.

> **The ten incoming modules touch the App Shell and Settings. They touch none of the eleven 🟩 sections in wave 1**, which is the practical reason wave 1 was the right place to start and remains so.

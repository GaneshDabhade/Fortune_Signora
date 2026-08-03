# The Customer Experience Blueprint

> **The authoritative description of Signora as a customer meets it** — every screen, every route, every journey, and the gap between what the backend can do and what a customer can reach.
>
> **Created 2026-08-02** on the product owner's direction, after Human Review made the gap visible: *"the repository contains considerably more functionality than the application currently exposes."* This document measures that claim rather than restating it.
>
> **It is a living document.** Every figure was read out of the repository at the commit named below, and every one is re-measurable. **When a status here disagrees with the code, the code is right and this is a defect** (`CLAUDE.md` §2).

**Re-measured at `origin/integration` = `0632680`, 2026-08-02**, after CX-01, CX-02 and CX-03. *(First measured at `11280f0`; endpoints and modules unchanged, screens and reachability changed.)* Frontend routes from `frontend/app/`, endpoints from `backend/modules/*/interface/router.py`, mounts from `backend/apps/api/main.py`, guards from `frontend/lib/state/permissions.ts`, navigation from `frontend/components/shell/navigation.tsx`.

---

## 0 · The headline, before the detail

**Three numbers, and the third is the finding.**

| | |
|---|---|
| **Backend HTTP endpoints** | **31**, across **11 modules** |
| **Navigable application screens** | **5** — one attention list, one account brief, three settings pages *(plus five sign-in screens, and two dead-end states added by CX-02)* |
| **Screens a `member` can reach** | **2** — unchanged by CX-01/02/03, and the number that still matters most |

> **A signed-in salesperson who is not an owner can reach the attention list and an account brief. Nothing else.** Settings, Products, and the Connection Center are all behind `workspace:update`, and the navigation has exactly two entries — one of which is the guarded one.

**And one route has no entrance at all.**

> **`/settings/connections` is linked from nowhere in the product.** The only links to it in the entire codebase are the two OAuth redirect helpers *inside the connection flow itself* — so a customer can reach the Connection Center only by first being in the Connection Center. **A closed loop with no door.**

**This is not a criticism of the work.** Every module was built to its own milestone's Definition of Done, and each is correct. **It is the cost, now measurable, of the sequencing `31-m10-design-review-evidence.md` predicted before it was felt** — nine pipeline stages ahead of any user-visible surface. `CLAUDE.md` §2's *every completed slice is demoable by a non-engineer* was ratified to stop this growing; this document is what it looks like already grown.

---

## 1 · Navigation Map

### What exists

```
  sign-in ─────────────────────────────────────────────┐
  sign-up · forgot-password · reset · verify-email      │
                                                        ▼
                                          ┌──────────────────────────┐
                                          │   AuthenticatedShell     │
                                          │  ┌────────┬───────────┐  │
                                          │  │ aside  │  topbar   │  │  ← aside hidden < 768px
                                          │  │        │ workspace │  │     (B-019, C-026)
                                          │  │ Nav    │ theme     │  │
                                          │  │        │ sign-out  │  │
                                          └──┴────────┴───────────┴──┘
                                               │
              ┌────────────────────────────────┴───────────┐
              ▼                                            ▼
      /  Attention                              /settings  ← owner only
      (every role)                                   │
              │                                      ├─▶ /settings/products     linked
              ▼                                      └─▶ /settings/connections  linked  ← CX-01
      /accounts/[accountId]  Brief
      (reachable only from the list)
              │
              └─▶ account history, mounted inline  ← CX-03
```

### Every customer-accessible area, and how it is reached

| Area | Route | Reached by | Who |
|---|---|---|---|
| **Attention list** | `/` | Navigation · the wordmark · post-decision *"All accounts"* | Every role |
| **Account brief** | `/accounts/[id]` | A row on the attention list · `j`/`k` · the post-decision offer | Every role |
| **Settings** | `/settings` | Navigation | **Owner only** |
| **Products** | `/settings/products` | A link on Settings | **Owner only** |
| **Connection Center** | `/settings/connections` | A card on Settings — **CX-01** | **Owner only** |
| **Sign-in family** | `/(auth)/*` | Unauthenticated entry, and each other | Signed out |

### How the modules connect on screen

**Almost everything a customer sees is one screen deep.** The account brief composes **eight** modules — Knowledge Graph, Buying Score, Signal, Business Event, Opportunity, AI Reasoning, AI Research and Commercial Profile — into one page. **That is the product's real information architecture**, and it is a strength: D38 reduced navigation to two entries precisely because *"a signal is what explains an account; a company is what an account is"*, and both belong on the brief.

**The weakness is everything that is not an account.** Team, Timeline, connections, provider health, billing and notifications have no place in a two-entry information architecture, and **no decision has been taken about where they go.**

---

## 2 · Screen Inventory

| Screen | Route | Owning module(s) | Backend | Frontend | Workflow | Status |
|---|---|---|---|---|---|---|
| **Attention list** | `/` | Opportunity · Buying Score · Signal · Knowledge Graph · Commercial Profile | ✅ | ✅ | ✅ Complete | **Production** |
| **Account brief** | `/accounts/[id]` | 8 modules | ✅ | ✅ | ✅ Complete | **Production** |
| **Settings** | `/settings` | Workspace & Tenancy | ✅ | ✅ | ⚠️ Lists organizations; **does not link Connections** | **Incomplete navigation** |
| **Products** | `/settings/products` | Commercial Profile | ✅ | ✅ | ✅ Complete for an owner · ❌ unreachable for a member ([C-008](../LANE_COORDINATION.md)) | **Permissions gap** |
| **Connection Center** | `/settings/connections` | Integrations | ✅ | ✅ | ✅ Complete — **CX-01** | **Production** |
| **Sign-in · sign-up · forgot · reset · verify** | `/(auth)/*` | Better Auth | ✅ | ✅ | ✅ Complete | **Production** |
| **Address not found** | *any unmatched URL* | Product Surface | n/a | ✅ **CX-02** | ✅ Complete | **Production** |
| **Render failure, outside the shell** | *any* | Product Surface | n/a | ✅ **CX-02** | ✅ Complete | **Production** |
| **Team** | — | Workspace & Tenancy | ✅ endpoint | ❌ | ❌ | **Blocked — [C-024](../LANE_COORDINATION.md)** |
| **Account history** | on `/accounts/[id]` | Timeline | ⚠️ **served, never written** | ✅ **CX-03** | ⚠️ **Renders its empty state everywhere** | **Mounted; awaiting data** |
| **Provider health** | — | Provider Platform | ❌ **no router** | ❌ | ❌ | **No HTTP surface at all** |
| **Billing · plan · usage** | — | *undecided* | ❌ | ❌ | ❌ | **Blocked — [C-200](../LANE_COORDINATION.md)** |
| **Notifications** | — | *M14a, not started* | ❌ | ❌ | ❌ | **Not started** |
| **Recommendations** | — | Recommendation Engine | ❌ not started | ❌ | ❌ | **Not started** |
| **RevOps / workspace intelligence** | — | Revenue Intelligence Platform | ❌ not started | ❌ | ❌ | **Not started · no journey defined** |

### Production-quality checks on the five application screens

**Checked by reading each page and its tests, not by assumption.**

| | Attention | Brief | Settings | Products | Connections | Auth |
|---|---|---|---|---|---|---|
| **Loading state** | ✅ Skeleton | ✅ Skeleton | ✅ `SkeletonText` | ✅ | ✅ | ✅ |
| **Empty state** | ✅ **and it says *why*** (PS-06) | ✅ Per section (PS-01, PS-02) | ✅ `EmptyState` | ✅ | ✅ | n/a |
| **Error state** | ✅ | ✅ | ✅ Toast **with correlation id** | ✅ | ✅ **outcome-per-failure** | ✅ |
| **Permissions reflected** | ✅ | ✅ | ⚠️ Guarded as a whole | ❌ **[C-008](../LANE_COORDINATION.md)** | ⚠️ Owner-only, undecided | n/a |
| **Keyboard** | ✅ `j`/`k`, announced (PS-08) | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Responsive** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ **[C-026](../LANE_COORDINATION.md)** |
| **Demo-ready** | ✅ | ✅ | ⚠️ | ✅ | ❌ unreachable | ✅ |

> **The five application screens are of good quality.** Loading, empty and error states are present on every one, and the empty states *explain* rather than merely occupy — which is unusual and worth protecting. **The gap is not quality. It is coverage.**

---

## 3 · Capability Mapping

**Every capability falls into exactly one of four buckets. Nothing lives outside them** (product owner, 2026-08-02):

| | |
|---|---|
| **Reachable** | A customer can discover it, navigate to it and complete the workflow |
| **Blocked** | A decision or a dependency stands in the way, and it is **named** |
| **Missing implementation** | It should exist and does not |
| **Intentionally unreachable** | It correctly has no screen — and the entry **says why, what replaces it, and why exposing it would be wrong** |

> **The fourth must never become a dumping ground for unfinished work.** An entry that cannot answer all three questions is not intentional; it is *Blocked* or *Missing* wearing a calmer label. That test is applied to every row in the ⚪ table below.

**Every backend endpoint, against what a customer can actually do with it.** This is the roadmap for completing the customer experience.

### ✅ Production complete — backend, UI, navigation and workflow all present

| Capability | Endpoint | Where a customer meets it |
|---|---|---|
| Sign in, sign up, recover a password | Better Auth (Next tier) | `/(auth)/*` |
| See which accounts deserve attention | `GET /accounts` · `/account-identities` | Attention list |
| Understand why an account scores | `GET /accounts/{id}/score` | Brief |
| Read the evidence behind a claim | `GET /business-events/{id}` | Evidence drawer |
| Read Signora's explanation | `GET /accounts/{id}/narration` | Brief |
| See what the evidence cannot support | `GET /accounts/{id}/validation` | Brief |
| Commit to, or dismiss, an account | `POST /opportunities/{id}/states` | Decision dialog |
| See what has been decided, and why | `GET /accounts/{id}/opportunity` → `history` | Decision history (PS-05) |
| Ask for research, and read it | `POST`/`GET /accounts/{id}/research` | Brief |
| Declare products, ICP, committee, focus, targets | 10 × Commercial Profile | `/settings/products` |
| Create and switch organization | `GET`/`POST /workspaces` | Settings · workspace selector |
| Connect and disconnect a system | `GET /integrations` · `POST /connections/{id}/disconnect` | Connection Center |
| Learn what a signal type means | `GET /signal-catalog` | **Titles only** — the definitions are [C-025](../LANE_COORDINATION.md) |

### 🟠 Backend complete · UI missing

| Capability | Endpoint | What is missing | Blocked by |
|---|---|---|---|
| **See who is in my organization** | `GET /workspaces/{id}/members` | The whole screen. The hook exists and reaches nothing | **[C-024](../LANE_COORDINATION.md)** — nothing can render a person's name |
| **See connected systems as a list** | `GET /workspaces/{id}/connections` | **No consumer.** The Connection Center reads `/integrations` instead | Not blocked — an observation for the owning lane |
| **Read the entity graph** | `GET /knowledge-graph` *(1 endpoint)* | No dedicated surface; the brief consumes it indirectly | Not blocked — **no journey asks for one** |

### 🟠 Backend complete · navigation missing

| Capability | Where it lives | What is missing |
|---|---|---|
| **See what my company sells** *(as a seller)* | `/settings/products` | A member-reachable route — **[C-008](../LANE_COORDINATION.md)** |

### 🔴 Workflow incomplete — the customer starts something that cannot finish

| Journey | Where it stops | Blocked by |
|---|---|---|
| **Declare target accounts → Signora watches them** | The declaration is recorded, the event publishes, the consumer computes the delta — **and nothing starts a sync** | **[C-021](../LANE_COORDINATION.md)** |
| **Guided first run** | Ends by asking which companies to watch; the answer goes nowhere | [C-007](../LANE_COORDINATION.md) → [C-021](../LANE_COORDINATION.md) |
| **Use Signora on a phone** | No navigation below 768px | **[C-026](../LANE_COORDINATION.md)** · [B-019](../BUGS.md) |

### The measurement behind all of the above — 2026-08-02

**Every endpoint in the repository, checked against whether the frontend issues a request for it.** Mechanical, repeatable, and the check that found CX-01 and CX-03.

| | |
|---|---|
| **Endpoints** | **31**, across 11 modules |
| **Requested by the frontend** | **30** |
| **Not requested** | **1** — `GET /workspaces/{id}/connections` |

**The one is not a gap.** `/integrations` returns the catalog *and* what is connected; `/connections` returns only the latter. The Connection Center reads the superset, which is the correct choice. **Recorded as an observation for the owning lane, not opened as a defect** — an endpoint may legitimately outlive its first consumer.

> **An endpoint is not a capability — and this is the limit that cost most.** The census asks whether a route is *served* and *called*. It cannot ask whether **anything ever writes the data behind it**, and on 2026-08-02 that turned out to matter: `make runtime-composition` reports **1 of 9** modules declaring an event consumer is wired into the deployed worker. **Eight projections, including Timeline's, are never invoked outside a test** — a deliberate consequence of [C-012](../LANE_COORDINATION.md), not a defect, and invisible to every endpoint-level check.
>
> **The correction to the method: three questions, not two.** *Is it served* · *is it called* · **is anything writing what it serves.** The third is answered by `make runtime-composition`, and this document now cites it rather than assuming a served endpoint has data behind it.

> **A request is not a screen, and this is where the check stops being mechanical.** Two endpoints are *requested* and still reach no customer: `GET /members` is fetched only so the shell can resolve **your own** role (TS-02), and its list is rendered nowhere. **Automation can tell you a route is called. Only reading the pages tells you whether anybody sees the answer.**

### ⚪ Intentionally unreachable — capabilities that correctly have no screen

**The category that stops a future engineer "fixing" something that is not broken.** A capability with no UI is a defect *only if a customer should have been able to use it*, and most of this repository's capability is deliberately invisible.

| Capability | Why it has no screen, and should not gain one |
|---|---|
| **`observation_engine` · `provider_normalization` · `ai_reasoning_engine`** — no HTTP router | **Pipeline stages, event-driven by design.** A customer does not invoke them; they invoke themselves when evidence arrives. Their *output* is on the brief — the score, the narration, the ledger — which is the correct surface for a stage that has no verb of its own |
| **65 event types** on the internal bus | **Inter-module contracts, not customer capability.** `06-events.md` is an engineering artifact; a screen listing published events would be the platform describing itself to somebody who does not work here |
| **`dispatch_event`** — the only registered worker task | Infrastructure. **Its visible consequence is that the product is up to date**, which is the only form a customer should ever meet it in |
| **`GET /workspaces/{id}/connections`** | **Superseded by `/integrations`**, which returns the catalog and the connections together. An endpoint may legitimately outlive its first consumer |
| **`GET /workspaces/{id}` · `GET /workspaces`** | Consumed by the shell's workspace selector rather than by a page. **Reached, but never as a destination** |
| **The Playground and the Provider Simulation Framework** | **Test and demo instruments.** Exposing them would be a `if playground` branch in the product, which the Single Product Principle forbids outright |

> **Two things separate this list from the roadmap above it.** Each entry has a *reason it should stay unreachable*, not merely an absence of demand — and each names what a customer meets **instead**. An entry that can say neither belongs in the blocked list, not here.

**`provider_platform` is deliberately not on this list.** It has no HTTP router either, but **provider health is a customer question** — *"is Signora still getting data from my systems?"* — and today nobody, customer or operator, can answer it. **That is a gap, not a design.** It has no backend to expose, so it is not this lane's to build; it is recorded in the blocked table above.

### ⚫ No backend at all — not this document's gap, recorded for completeness

**Provider Platform · Provider Normalization · Observation Engine · AI Reasoning Engine have no HTTP router.** For the three pipeline modules that is correct — they are event-driven and a customer has no business calling them. **Provider Platform is the one worth noting**: `provider.health_changed` is published, `12-scalability.md` depends on its metrics, and **there is no way for anybody to see whether a provider is healthy.**

**Recommendation Engine · Timeline surfaces · Revenue Intelligence Platform · Notifications (M14a) · Billing (M14b)** are not started. **RIP's is a `README.md` unowned capability already**: *"the RevOps surface — RIP owns it, no journey defined."*

---

## 4 · Workflow Mapping

**Ten journeys, and where each one currently stops.** *(J10 was missed in the first pass — the audit looked at reading capabilities and not at writing ones. Recorded rather than quietly added.)*

```
  ✅ Sign in ──▶ ✅ Attention ──▶ ✅ Account Brief ──▶ ✅ Decision ──▶ ✅ Next account
                                        │
                                        ├──▶ ❌ Timeline          component built, not mounted
                                        ├──▶ ✅ Evidence           complete
                                        └──▶ ✅ Research           complete

  ✅ Sign in ──▶ ⚠️ Settings ──▶ ✅ Products ──▶ ✅ Declare targets ──▶ 🔴 nothing syncs
                       │
                       └──▶ ❌ Connections     no link exists
                       └──▶ ❌ Team            no screen exists
                       └──▶ ❌ Billing         no module exists
                       └──▶ ❌ Notifications   not started
```

| # | Journey | Status | Stops at |
|---|---|---|---|
| **J1** | Sign in and land somewhere useful | ✅ **Complete** | — |
| **J2** | Find the accounts that deserve attention | ✅ **Complete** | — |
| **J3** | Understand why, with evidence | ✅ **Complete** | — |
| **J4** | Decide, and record why | ✅ **Complete** | — |
| **J5** | Move to the next decision | ✅ **Complete** (PS-04) | — |
| **J6** | See an account's history over time | ⚠️ **Surfaced, not yet answerable** | **Nothing writes a timeline row outside a test.** The mount is done; `project_to_timeline` is not subscribed by the deployed worker and no seeder calls it ([C-012](../LANE_COORDINATION.md)) |
| **J7** | Tell Signora who we sell to | ⚠️ **Half** | An owner can declare; **a seller cannot read** |
| **J8** | Connect our systems | ⚠️ **Half** | Complete once reached; **unreachable** |
| **J9** | See who is on the team | ✅ **Complete — TM-01** | — |
| **J10** | **Invite a colleague** | 🔴 **Blocked** | **`POST /members` takes a `user_id: UUID`.** A customer cannot type one, and resolving an email to a user is Better Auth's, in the Next tier — **[C-024](../LANE_COORDINATION.md) again, from the write side** |

**Five of ten are complete.** J8 closed on 2026-08-02 when CX-01 gave the Connection Center a door. **J6 did not close, and the correction is worth more than the count.**

> **CX-03 mounted the feed, and the feed has nothing to render.** `make runtime-composition` reports 1 of 9 consumers wired; `project_to_timeline` is called from tests and nowhere else. **The section renders *"Nothing has been recorded about this company yet"* on every account, in every environment, including the demo stack.**
>
> **The mount is still right and is not being reverted.** It is what [C-024](../LANE_COORDINATION.md) asked for, and un-mounting would hide a wiring gap behind a missing feature — the exact inversion PS-01 and PS-02 exist to prevent. **What is wrong is the sentence the customer reads**: the product says it looked and found nothing, when it never looked. That copy belongs to Timeline's component and is not Product Surface's to change.

**The five that remain are each stopped by a decision, not by engineering:** J6 waits on `C-012`, and J7 waits on `C-008`, **J9 and J10 both on `C-024`**, and the responsive question on `C-026`. **C-024 now holds two journeys and both halves of team management** — reading who is there, and adding anybody — which makes it the highest-leverage decision on this page.

**Two of the six were closed by ten lines and a card**, which is the pattern worth carrying: *the gap between a shipped backend and a customer is usually smaller than it looks, and invisible to every test in the repository.*

---

## 5 · UX Principles

**These emerged from the reviews rather than being decided in advance**, and each one is here because a slice was built or refused on its strength. They are recorded for the next lane, not proposed as new rules — [38-product-design-principles.md](38-product-design-principles.md) remains the ratified set, and these are the ones this lane's reviews have kept reaching for.

| # | Principle | Where it was earned |
|---|---|---|
| **1** | **Intelligence suggests; humans commit.** Signora never claims ownership of a customer's decision | The workflow line says *"nobody has taken it yet"* · `decided_by` distinguishes Signora's opening entry from a person's (PS-05) |
| **2** | **Provenance is always visible.** Every claim can be traced to what produced it | The evidence drawer · citation protocol · *"Signora suggested this"* vs *"somebody here added it"* (PS-03) |
| **3** | **Navigation never surprises.** A customer is never moved somewhere they did not ask to go | PS-04 offers the next account and **also offers to stay** |
| **4** | **An empty state explains reality rather than hiding it.** *Nothing here* and *nothing yet* are different sentences | PS-01, PS-02, PS-06 — three slices, all the same defect: two states rendered as one blank space |
| **5** | **Information density is intentional.** Every section earns its place, and the page as a whole is somebody's judgement | The subtraction review — eleven sections, each with a written reason, nothing removed |
| **6** | **The same fact is said once.** Contextual reinforcement is not duplication, and the difference is whether it answers a different question | PS-07 |
| **7** | **Trust outranks automation.** A number with a shelf life says so; a contested reading is shown contested rather than averaged | *"Exactly correct until 20 Sep"* · the contested badge, note and *since* |
| **8** | **A control that goes nowhere costs more trust than an absent one** | Why [C-008](../LANE_COORDINATION.md) was not fixed by un-guarding a page full of controls that would 403 |
| **9** | **The product teaches its own vocabulary** | [ADR-0034](adr/0034-ubiquitous-language.md) · and its unfinished half, [C-025](../LANE_COORDINATION.md) |
| **10** | **A capability nobody can reach is not shipped** | **This document.** Timeline, Team and the Connection Center are each built and unreachable |

---

## 6 · UI Implementation Roadmap

**Ordered by the product owner's stated preference: complete existing workflows · surface existing backend · improve discoverability · improve navigation · refine production UX.** Nothing here is a new capability.

**Every slice below improves an end-to-end journey. None is an isolated screen.**

| # | Slice | Journey | Unlocks | Blocked? |
|---|---|---|---|---|
| **CX-01** | **The Connection Center gets an entrance** | **J8** | A whole shipped module a customer could not find. **Backend, screen, OAuth flow and disconnect were all complete** — this was a link and a card on Settings | ✅ **Shipped** |
| **CX-02** | **The two dead ends stop being Next.js's** | All | A bad address showed *"404 &#124; This page could not be found"* with no product, no theme and no way back; a render error **outside** the authenticated shell blanked the application, because `ErrorBoundary` wraps three regions *inside* it and `(auth)` has none | ✅ **Shipped** |
| **CX-03** | **Timeline mounts on the brief** | **J6** | An endpoint, a hook and a built component that reached nobody. **Ten lines** | ✅ **Shipped** |
| **CX-04** | **The signal glossary** | J2 · J3 | Nine words a first-time reader cannot look up. **Built and reverted** | **[C-025](../LANE_COORDINATION.md)** |
| **CX-05** | **A seller can read the commercial profile** | **J7** | Every AE and SDR, every day | **[C-008](../LANE_COORDINATION.md)** |
| **CX-06** | **The Team page** | **J9** | An owner cannot see who is in their organization | **[C-024](../LANE_COORDINATION.md)** |
| **CX-07** | **Responsive shell and screens** | All | The product on a device other than a laptop | **[C-026](../LANE_COORDINATION.md)** |
| **CX-08** | **Target accounts actually get watched** | J7 | The one place the product accepts an instruction and does nothing with it | **[C-021](../LANE_COORDINATION.md)** |
| **TM-03a** | **An organization can grow** | **J10** | Every workspace was permanently whoever created it. Invite · list · withdraw, with a Team card on Settings | ✅ **Shipped** |

> **CX-01 and CX-02 are shipped.** Everything below them is a decision away, and each decision is already recorded.
>
> **What the two had in common is worth naming, because it is how the next one will be found.** Neither was a missing feature. One was a complete module with no entrance; the other was two screens the framework supplied and the product never claimed. **Both were invisible to every test in the repository**, because a test asks *does this render correctly* and neither failure was about rendering — one was about reachability, the other about a file that did not exist. **The audit found them; no suite could have.**

**What is deliberately not on this list:** a Provider health screen, a RevOps dashboard, a notifications centre and a recommendations surface. **Three have no backend and one has no journey** — building any of them would be a new capability rather than the completion of an existing one, and that is the product owner's to schedule.

---

## 6a · The four questions every module must answer

**Set by the product owner, 2026-08-02, and the standard this document is now held to.** A module is covered here when all four have an answer — and the fourth is the one most easily skipped.

| | |
|---|---|
| **1 · What backend capabilities exist?** | §3, measured from `router.py` rather than remembered |
| **2 · Which customer journeys use them?** | §4, ten journeys |
| **3 · Which UI surfaces expose them?** | §2, screen inventory |
| **4 · Which capabilities are intentionally unreachable?** | **§3's ⚪ table.** *"Not every endpoint requires a direct screen. Documenting intentional non-consumption avoids future engineers fixing something that isn't broken."* |

**Coverage today: all four answered for every module with a router**, and for the four pipeline modules without one. **The gap is `provider_platform`**, which has no HTTP surface and, unlike the other four, *should* have one.

## 6b · Experience consistency — reviewed as one application

**A running record of patterns that are shared across screens, so a new screen inherits them rather than inventing its own.** Where a pattern is *deliberately* uniform, saying so stops the next reviewer filing it as a gap.

| Pattern | Where it holds | Verdict |
|---|---|---|
| **A save confirms itself by rendering the new value** | All five commercial editors — products, ICP, committee, focus, target accounts. **Each handles error and pending; none shows a success toast** | **Deliberate, and consistent.** For an inline editor the value appearing *is* the confirmation. A toast is right where the result is not visible — creating an organization does toast, because the dialog closes and one new row joins many |
| **An error names its reference** | Toasts and both dead-end pages carry `correlation_id` or `digest` | **Consistent.** It is what turns *"it broke"* into a request an engineer can find |
| **A section renders on failure rather than disappearing** | Narration, validation, research, decision history, account history | **Consistent, and load-bearing** — B-006 was an absent section reading as a feature the customer does not have |
| **A control the server would refuse is not shown** | Navigation, route guards, workflow actions | **Consistent.** Presentation, never enforcement (§20c) |
| **Colour comes from a token** | Everywhere except `integrations` and `timeline` | **🟠 Inconsistent — [B-200](../BUGS.md).** Two undefined token names on 44 lines |
| **Customer vocabulary at the edge** | Enforced repository-wide by `vocabulary.test.tsx` | **Consistent, and machine-checked** — the test walks the whole tree rather than a directory list, which is why it has never fallen behind |

> **The two rows that disagree are worth reading together.** `vocabulary.test.tsx` walks `app/` and `components/` entirely; `design-tokens.test.tsx` maintains a hand-written list of six directories and is behind for the third time. **Same repository, same problem, one solved structurally and one by memory** — which is the identifier lesson ([C-201](../LANE_COORDINATION.md)) in a different costume.

## 6c · QE Impact — the section every slice now carries

**Required by the product owner from 2026-08-02**, in the implementation report of every customer-visible change, so **automation evolves alongside the product instead of catching up afterward.**

**It answers five questions and nothing more. Concise and objective — this is a hand-off to QE, not a second Slice Handoff.**

| | |
|---|---|
| **1** | **What should QE validate?** |
| **2** | **Are new tests expected?** |
| **3** | **Are automation changes required?** |
| **4** | **Are visual or UI regression changes expected?** |
| **5** | **Does this affect certification?** |

**`none` is a valid answer to any of them, and silence is not.**

> **The lane does not write those tests.** Its responsibility is to describe the change precisely enough that QE can update, create or retire automation without reading the diff — the same reason the Slice Handoff exists, applied to validation instead of to status.

**It lives in the commit message beside the Slice Handoff**, for the same reason: a file would conflict between lanes, and a commit message travels with the change forever and is greppable.

## 7 · How to keep this document true

**It is a living reference, and the measurements are the part that rots.**

| When | Update |
|---|---|
| **A screen ships** | Its row in §2, and the journey it completes in §4 |
| **An endpoint is added** | §3 — and say which of the six statuses it lands in |
| **A coordination item is answered** | §3 and §6 — a blocked slice becomes executable, and the roadmap re-orders |
| **A navigation entry changes** | §1, including the diagram |
| **A review earns a new principle** | §5, with the slice that earned it |

**The three counts in §0 are the fastest check that this document has drifted:** endpoints, screens, and screens a member can reach. **If any of them is wrong, everything below it is suspect.**

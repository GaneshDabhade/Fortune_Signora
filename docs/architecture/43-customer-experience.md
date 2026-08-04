# The Customer Experience Blueprint

> **The authoritative description of Signora as a customer meets it** — every screen, every route, every journey, and the gap between what the backend can do and what a customer can reach.
>
> **Created 2026-08-02** on the product owner's direction, after Human Review made the gap visible: *"the repository contains considerably more functionality than the application currently exposes."* This document measures that claim rather than restating it.
>
> **It is a living document.** Every figure was read out of the repository at the commit named below, and every one is re-measurable. **When a status here disagrees with the code, the code is right and this is a defect** (`CLAUDE.md` §2).

**Re-measured at `lane-a-product-surface` = `fc59125`, 2026-08-03**, after TM-03a and the Sales Workspace slices. *(Previously `0632680`; first measured at `11280f0`.)* Frontend routes from `frontend/app/`, endpoints from `backend/modules/*/interface/router.py`, mounts from `backend/apps/api/main.py`, guards from `frontend/lib/state/permissions.ts`, navigation from `frontend/components/shell/navigation.tsx`.

---

## 0 · The headline, before the detail

**Four numbers now, and the fourth is the finding.**

| | 2026-08-02 | 2026-08-03, assessed | **2026-08-03, after CX-05** |
|---|---|---|---|
| **Backend HTTP endpoints** | 31, across 11 modules | 40, across 11 modules | **40** — CX-05 added none |
| **Navigable application screens** | 5 | 6 | **7** |
| **Screens a `member` can reach** | 2 | 2 | **3** |
| **Navigation entries a `member` sees** | *not measured* | **1** | **2** |

> **The assessment's finding, and what was done about it the same day.** Nine endpoints and one screen had arrived since 2026-08-02 and **the seller's half of the product had not moved** — every one of the nine was Team Management, behind `workspace:update`.

**The fourth number was the one to act on.**

> **A signed-in salesperson who was not an owner saw a sidebar with one item in it.** `Settings` is guarded by `workspace:update` and `Navigation` correctly declines to render a link the server would refuse — so of the two entries D38 reduced navigation to, a member saw one. **A navigation of one is not navigation; it is a label.**

**CX-05 answered it without adding a single endpoint.** `/business` reads the five declarations `policy.csv` had already granted a member for a year — see §8.7.

**The route-with-no-entrance class is closed.** Every route in `app/` now has an inbound link from somewhere a customer can already be — checked mechanically, not by memory, and the check is worth re-running rather than trusting: for each `page.tsx`, does any other source file name its path? CX-01 fixed the last one.

**What replaced it is harder to see, because nothing is missing.** The remaining gap is not a route without a door, it is **a role without a product**: every screen exists, every screen is linked, and the person Signora is built for can open two of them.

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
      /  Attention        /business            /settings  ← owner only
      (every role)        (every role)               │
              │            ← CX-05                   ├─▶ /settings/products     linked
              │                                      ├─▶ /settings/team         linked  ← TM-03a
              ▼                                      └─▶ /settings/connections  linked  ← CX-01
      /accounts/[accountId]  Brief
      (reachable only from the list)
              │
              └─▶ account history, mounted inline  ← CX-03
```

**What a `member` sees of that diagram is the first two columns** — `Settings` is filtered out of the sidebar by `guardFor`, taking its three children with it. Before CX-05 it was the first column alone (§8.1).

> **`/business` is deliberately absent from `GUARDED_ROUTES`, and that is the design rather than an omission.** `guardFor` is a **deny-list**: a route it does not name needs only a resolved workspace. So a top-level route is member-reachable *by construction* — which is why option C needed no change to `permissions.ts`, frozen frontend foundation under §20c, and option A did.

### Every customer-accessible area, and how it is reached

| Area | Route | Reached by | Who |
|---|---|---|---|
| **Attention list** | `/` | Navigation · the wordmark · post-decision *"All accounts"* | Every role |
| **Your business** | `/business` | Navigation — **CX-05** | **Every role** |
| **Account brief** | `/accounts/[id]` | A row on the attention list · `j`/`k` · the post-decision offer | Every role |
| **Settings** | `/settings` | Navigation | **Owner only** |
| **Products** | `/settings/products` | A link on Settings | **Owner only** |
| **Team** | `/settings/team` | A card on Settings — **TM-03a** | **Owner only** |
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
| **Your business** | `/business` | Commercial Profile · Workspace & Tenancy | ✅ **unchanged** | ✅ | ✅ Complete — read, for every role | **Production** — CX-05 |
| **Settings** | `/settings` | Workspace & Tenancy | ✅ | ✅ | ✅ Lists organizations, and **links all three children** | **Production** — CX-01 |
| **Products** | `/settings/products` | Commercial Profile | ✅ | ✅ | ✅ Complete for an owner · ❌ unreachable for a member ([C-008](../LANE_COORDINATION.md)) | **Permissions gap** |
| **Connection Center** | `/settings/connections` | Integrations | ✅ | ✅ | ✅ Complete — **CX-01** | **Production** |
| **Sign-in · sign-up · forgot · reset · verify** | `/(auth)/*` | Better Auth | ✅ | ✅ | ✅ Complete | **Production** |
| **Address not found** | *any unmatched URL* | Product Surface | n/a | ✅ **CX-02** | ✅ Complete | **Production** |
| **Render failure, outside the shell** | *any* | Product Surface | n/a | ✅ **CX-02** | ✅ Complete | **Production** |
| **Team** | `/settings/team` | Workspace & Tenancy | ✅ | ✅ | ✅ Complete — invite · list · role · remove · history | **Production** — TM-03a |
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
| ~~**See who is in my organization**~~ | `GET /workspaces/{id}/members` | ~~The whole screen~~ | **Closed** — `/settings/team`, TM-03a |
| **See connected systems as a list** | `GET /workspaces/{id}/connections` | **No consumer.** The Connection Center reads `/integrations` instead | Not blocked — an observation for the owning lane |
| **Read the entity graph** | `GET /knowledge-graph` *(1 endpoint)* | No dedicated surface; the brief consumes it indirectly | Not blocked — **no journey asks for one** |

### 🟠 Backend complete · navigation missing

| Capability | Where it lives | What is missing |
|---|---|---|
| ~~**See what my company sells** *(as a seller)*~~ | `/business` | **Closed 2026-08-03 — CX-05.** Five resources wide: `product` · `icp` · `buying_committee` · `commercial_focus` · `target_account`, all now member-reachable. §8.7 |

### 🔴 Workflow incomplete — the customer starts something that cannot finish

| Journey | Where it stops | Blocked by |
|---|---|---|
| **Declare target accounts → Signora watches them** | The declaration is recorded, the event publishes, the consumer computes the delta — **and nothing starts a sync** | **[C-021](../LANE_COORDINATION.md)** |
| **Guided first run** | Ends by asking which companies to watch; the answer goes nowhere | [C-007](../LANE_COORDINATION.md) → [C-021](../LANE_COORDINATION.md) |
| **Use Signora on a phone** | No navigation below 768px | **[C-026](../LANE_COORDINATION.md)** · [B-019](../BUGS.md) |

### The measurement behind all of the above — 2026-08-02

> **Re-measured 2026-08-03 in §8.1: 40 endpoints, 39 requested, the same one not.** The figures below are the 2026-08-02 reading and are kept as the record of what was true then (`CLAUDE.md` §2). **§8.1 also records why this census can no longer find the remaining gap** — it asks whether a route is called, and the gap is now about who is allowed on the page that calls it.

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
| **J9** | See who is on the team, and manage it | ✅ **Complete** — roster, roles, removal, ownership transfer, history | — |
| **J10** | **Invite a colleague** | 🔴 **Blocked** | **`POST /members` takes a `user_id: UUID`.** A customer cannot type one, and resolving an email to a user is Better Auth's, in the Next tier — **[C-024](../LANE_COORDINATION.md) again, from the write side** |

**Five of ten are complete.** J8 closed on 2026-08-02 when CX-01 gave the Connection Center a door. **J6 did not close, and the correction is worth more than the count.**

> **CX-03 mounted the feed, and the feed has nothing to render.** `make runtime-composition` reports 1 of 9 consumers wired; `project_to_timeline` is called from tests and nowhere else. **The section renders *"Nothing has been recorded about this company yet"* on every account, in every environment, including the demo stack.**
>
> **The mount is still right and is not being reverted.** It is what [C-024](../LANE_COORDINATION.md) asked for, and un-mounting would hide a wiring gap behind a missing feature — the exact inversion PS-01 and PS-02 exist to prevent. **What is wrong is the sentence the customer reads**: the product says it looked and found nothing, when it never looked. That copy belongs to Timeline's component and is not Product Surface's to change.

**The five that remain are each stopped by a decision, not by engineering:** J6 waits on `C-012`, and J7 waits on `C-008`, **J9 and J10 both on `C-024`**, and the responsive question on `C-026`. **C-024 now holds two journeys and both halves of team management** — reading who is there, and adding anybody — which makes it the highest-leverage decision on this page.

**Two of the six were closed by ten lines and a card**, which is the pattern worth carrying: *the gap between a shipped backend and a customer is usually smaller than it looks, and invisible to every test in the repository.*

---

## 4a · The supported viewport — *ruled 2026-08-03*

**[C-205](../LANE_COORDINATION.md) asked one question and it has an answer: a phone is in scope.** The repository had never stated a supported viewport, so every screen was reviewed against an assumption rather than a target — which is what the item said the value of ruling would be, whichever way it went.

| | |
|---|---|
| **Supported** | **`320px` and up.** A phone in portrait is a first-class viewport, not a courtesy |
| **The breakpoint that matters** | **`768px` (`md`)** — the sidebar appears above it, the bottom bar below it. **Exactly one navigation exists at any width** |
| **Touch target floor** | **`44px`** (`min-h-11`). A control smaller than that is one a thumb misses |
| **What this makes of [B-203](../BUGS.md)** | **A defect**, not a non-goal. It was 🟠 and explicitly undecided; the decision closes it |

**§20c permits the foundation change this needs, and names it.** *"An accessibility issue — a missing label, an unreachable control, a lost focus state. These are defects, not enhancements, and never wait for a business milestone to justify them."* **A navigation that vanishes below `768px` is an unreachable control**, which is that clause's own example.

**Responsiveness is now a defect class rather than a retrofit.** Every Product Surface slice from here carries it; the alternative is paying for it once per screen, later, on a surface that has grown.

### Measured before building — 2026-08-03

| | |
|---|---|
| **Files carrying any responsive rule** | **5** of 65 |
| **The shell's only rule** | **`hidden … md:block`** — the one that *removes* the navigation |
| **Tables at risk of horizontal overflow** | **None — the audit was wrong here.** `components/ui/table.tsx` already wraps every table in `overflow-x-auto`, *"so a wide table never forces the page body to scroll sideways"*. The one `overflow-x` container in the product is that wrapper, covering all three tables |

> **The product was not partly responsive; it was desktop-only with one line that hid a sidebar.** That is a cleaner starting point than a half-converted surface — there is no half-measure to unpick.

---

### What one column actually cost — slices 2 and 3, 2026-08-03

**Two structural changes, and the audit over-counted the work.** Most of the product is a single `max-w-3xl` column of stacked cards, which survives a narrow viewport unchanged. **What breaks is any row that pairs a name with a fixed-width block**, and there are exactly two:

| Where | What broke | The fix |
|---|---|---|
| **The attention row** | The right-hand block is `shrink-0` — four badges and a score, roughly 180px. At `320px` it takes more than half the row and **squeezes the account name to a few characters** | Stack below `sm`. The badges keep `justify-between`, so **the score is still the rightmost thing on the row** and the column property survives the reflow |
| **The brief's header** | Same shape: a company name — the longest string on the page — sharing a row with the score block | Stack below `sm` |

**The hierarchy is what the fix protects, not the layout.** *The account leads* is the attention row's whole design — *"a seller scans names, not numbers"* — and a name compressed to six characters inverts it. **Giving the name the full width and dropping the rest to a second line preserves the ordering; shrinking either would have broken it silently.**

**And the foundation was better than the audit credited.** `components/ui/table.tsx` already wraps every table in `overflow-x-auto` — the audit counted one `overflow-x` container and read it as a gap, when it is the library covering all three tables. **Corrected above rather than left standing.**

---

### CX-07 complete — the shape of the whole milestone, 2026-08-03

**Four slices, and the pattern is one sentence:** *the product is a column of stacked cards, and the only thing that broke was a row pairing a name with a fixed-width block.* That shape appeared **five times** — the attention row, the brief's header, and the headers on Settings, Team and Your business — and got the same fix each time: stack below `sm`, unchanged above it.

| Slice | What it was |
|---|---|
| **1** | **Navigation on a phone** — [B-203](../BUGS.md). The only *defect*; the rest were absences |
| **2 · 3** | The attention row and the brief's header, where the account name was being compressed to a few characters |
| **4** | Settings · Team · Your business — the same header shape, fixed identically |

**Nothing needed a new component, a new token, or a dependency.** The design system already carried what this needed: `Table` wraps itself in `overflow-x-auto`, `Card` and `EmptyState` are width-agnostic, and every screen was already a single `max-w-3xl` column.

> **The milestone's real cost was one line in the shell.** `hidden … md:block` removed the navigation and nothing replaced it — **that** was the reason the product could not be used on a phone, not the layouts. Everything after slice 1 was refinement, and saying so is more useful to the next lane than a list of five diffs.

**What is not covered, and it is the same gap throughout.** **No test in this repository can see a reflow.** jsdom computes no layout, so every assertion here is on markup and class strings; *what a screen looks like at 320px* is verifiable only in a browser, and Playwright cannot start on this machine. **A Playwright viewport check is the missing half**, recorded for QE rather than left implied.

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
| **11** | **A narrowed view has a different empty state from the whole.** Wherever a filter, search, segment, tab, scope, saved view or workspace can independently produce no rows, **that emptiness is its own state and needs its own words** | **SW-05a**, and set as a Product Surface rule by the product owner, 2026-08-03 |

### Principle 11, stated as the rule a slice is checked against

**Ratified by the product owner on 2026-08-03, after SW-05a.** It is principle **4** — *nothing here* and *nothing yet* are different sentences — extended to the case that produced three defects before anybody named it.

> **Whenever a screen gains a way to narrow itself, it gains a new empty state in the same change.** Not as a follow-up: the filter and its emptiness ship together, or the filter has shipped a blank.

**The failure is structural rather than careless, which is why a rule is worth having.** Two correct components leave a gap between them:

| | |
|---|---|
| **The control** | Correctly absent-when-empty — it hides a question nothing raises (principle · **R1-06 / D6**) |
| **The page's quiet state** | Correctly does not fire — the **unfiltered** list is not empty |
| **The list** | Renders zero rows, and **nothing says why** |

**Each component is right. The composition is blank.** No test failed, because every test asked *does this render correctly* and each one did. **A page that renders nothing is indistinguishable from a broken one** (D36) — and D36 was already fixed on this page once, through a door D36 did not cover.

**The three questions a narrowing control must answer before it ships:**

1. **Can this control produce zero rows while the unfiltered view has some?** If yes, it has its own empty state.
2. **Is that state reachable without using the control?** A shared link, a bookmark, browser-back and a stale tab all name a narrowing the evidence has since moved past. **It is reachable.**
3. **Does the surrounding copy still tell the truth when narrowed?** SW-05a's subtitle claimed *"accounts worth a look, most pressing first"* while showing one question's slice — the same defect class as a dashboard describing the previous milestone (`CLAUDE.md` §2).

**And the wording rule:** the state blames the evidence moving, never the reader and never *"no results"*. **Nothing raising a question any more is the product working**, and it says so.

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
| **CX-05** | **A seller can read the commercial profile** | **J7** | Every AE and SDR, every day | ✅ **Shipped** — stage 1. **Stage 2 (option D) remains** |
| **CX-06** | **The Team page** | **J9** | An owner cannot see who is in their organization | ✅ **Shipped** — as TM-03a |
| **CX-07** | **Responsive shell and screens** | All | The product on a device other than a laptop | ✅ **Shipped 2026-08-03** — [TASK-200](../BACKLOG.md), four slices. [B-203](../BUGS.md) fixed; the supported viewport recorded in §4a |
| **CX-08** | **Target accounts actually get watched** | J7 | The one place the product accepts an instruction and does nothing with it | **[C-021](../LANE_COORDINATION.md)** |
| **TM-03a** | **An organization can grow** | **J10** | Every workspace was permanently whoever created it. Invite · list · withdraw, with a Team card on Settings | ✅ **Shipped** |

> **Re-read 2026-08-03 (§8).** CX-01, CX-02, CX-03 and CX-06 are shipped. **Every remaining slice is a decision away, and every decision has been waiting since 2026-08-02** — the assessment's conclusion, and the reason it recommends ruling on [C-008](../LANE_COORDINATION.md) before anything else.
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

**The four counts in §0 are the fastest check that this document has drifted:** endpoints, screens, screens a member can reach, and **navigation entries a member sees**. **If any of them is wrong, everything below it is suspect.**

---

## 8 · Product Surface assessment — 2026-08-03

**Commissioned by the product owner** as an *implementation-driven* review: not another UX pass over screens that exist, but a reading of **how existing capability should be surfaced**. Six questions were asked. Each is answered below from the repository at `fc59125`, and each answer names how it was measured so the next lane can re-run it rather than believe it.

### 8.1 · Which implemented capabilities are not discoverable?

**One, and it is the same one that was here in August: the commercial profile.** Everything else a customer may read, they can find.

**The measurement.** Every endpoint against whether the frontend requests it, then — because *a request is not a screen* — every request against whether a page renders the answer.

| | |
|---|---|
| **Endpoints** | **40**, across 11 modules |
| **Requested by the frontend** | **39** |
| **Not requested** | **1** — `GET /workspaces/{id}/connections`, superseded by `/integrations`, which returns the catalog *and* the connections. **Still not a gap**, and still recorded rather than opened |

**The census now says almost nothing, and that is the finding.** When it was 31 endpoints and one unconsumed, the number was doing work. At 40 and one, **it has stopped being able to see the problem** — because the problem is no longer *is anything calling this*, it is *who is allowed to be on the page that calls it*. **A capability can be requested, rendered, linked and still unreachable, if the reader is a member.**

**The correction to the method: four questions, not three.** *Is it served* · *is it called* · *is anything writing what it serves* · **and can the person who needs it reach the screen.** The fourth is answered by crossing `policy.csv` with `GUARDED_ROUTES`, and it is the check that finds what is below.

**Crossed, the two disagree in exactly one place — and it is four rows wide:**

| Resource | `policy.csv` grants `member` read | Screen | Reachable by a member |
|---|---|---|---|
| `product` | ✅ | `/settings/products` | ❌ |
| `icp` | ✅ | `/settings/products` | ❌ |
| `buying_committee` | ✅ | `/settings/products` | ❌ |
| `commercial_focus` | ✅ | `/settings/products` | ❌ |
| `target_account` | ✅ | `/settings/products` | ❌ |

> **Five deliberate grants, each taken on the reasoning that every seller needs to see the catalog, and none of them reaches a seller.** This is [C-008](../LANE_COORDINATION.md), raised 2026-08-02, proposal accepted, **awaiting one choice.** The assessment did not find it — it confirms it, independently, from the other direction, and reports that it is now the **only** capability in this class.

> ✅ **Ruled and closed the same day.** The table above is the reading that prompted the ruling and is kept as it was measured. **All five are member-reachable at `/business` since CX-05** — §8.7.

### 8.2 · Which routes are unreachable through navigation?

**None.** The class CX-01 opened is closed, and it was re-checked mechanically rather than remembered.

| Route | Inbound links, from |
|---|---|
| `/` | Navigation · the wordmark · the brief's back link · sign-in · `not-found` · the triage strip · the OAuth start route |
| `/accounts/[accountId]` | The attention list row · `j`/`k` · the post-decision offer |
| `/settings` | Navigation · `no-workspace` |
| `/settings/products` · `/settings/team` · `/settings/connections` | A card on `/settings` — **the rule CX-01 set, held three times** |

**The rule that produced this is worth restating because it is cheap and it works:** *a settings page ships with its card on `/settings` in the same slice.* `/settings` is the only entrance to `/settings/*`, so a page not listed there is a page nobody can reach — and `/settings/team` was the first to ship under the rule rather than have it applied afterwards.

### 8.3 · Where do workflows require unnecessary clicks?

**The seller's daily loop is clean and should not be touched.** Walked end to end against the running product:

```
  sign in ─▶ attention list ─▶ [filter by question] ─▶ account ─▶ decide ─▶ next account
              ▲                                                              │
              └──────────────────────────────────────────────────────────────┘
```

**Zero avoidable clicks in it.** The triage strip filters in one click and clears in one; `j`/`k` moves between accounts without the list; the decision dialog offers the next account *and* offers to stay (PS-04). **Nothing here is a candidate.**

**The friction is not in the loop; it is the wall at the edge of it.** A seller who wants to know *why is this account a fit for us* — the question the brief is answering — has **no click at all**, at any count. That is 8.1, and it is a reachability problem wearing a workflow costume.

### 8.4 · Where can information hierarchy be improved?

**`/settings/products` — one heading, five bounded declarations, five editors, one scroll.**

| The page says | What is actually on it |
|---|---|
| *Your business* | The product catalog · the ideal customer · the buying committee · commercial focus · target accounts |

**Five independently-versioned declarations, from five endpoint pairs, stacked in a column with no hierarchy between them and no read mode for any.** The page is correct — each editor handles its own loading, its own failure and its own empty state, and B-006 is properly closed. **It is the composition that has no shape.**

**It is also the screen most likely to be described as feeling like a developer tool** (8.6), and the two observations have the same cause: **it was built one declaration per slice, and nothing has yet looked at all five together.**

**Not proposed as a slice here.** Restructuring it decides where the commercial profile lives, which is C-008's question 2 — **so the layout is downstream of the ruling, not a way to avoid it.**

**The account brief was measured and is not a candidate.** Its ordering — *what changed* → *how much attention* → *how long that holds* → *what to do next* → *why* → *what disagrees* — is progressive disclosure done on the page rather than behind a control, and the subtraction review already examined all eleven sections and removed none. **[TASK-011](../BACKLOG.md) holds the remaining hierarchy pass and is `WAITING` on a seller in the room**, which is the right owner for it.

### 8.5 · Where should related capabilities be composed into one experience?

**The commercial profile belongs on the account brief, not only in Settings — and this is the assessment's substantive recommendation.**

**The brief already composes eight modules into the one page a seller argues with.** The declarations that explain *why this account* are not among them, and they are the customer's own words about their own business:

| The seller is reading | And cannot see |
|---|---|
| Why this account scores | **Which of our products it is a fit for** |
| The evidence behind it | **The ideal customer it is being matched against** |
| Who holds it, and what to do next | **The buying committee roles they are meant to be selling into** |

> **Moving a settings entry into the sidebar would satisfy none of this.** It would leave a seller opening a configuration screen to answer a question they had while reading about an account — which is the shape of *navigation mirroring how modules are organised rather than how customers think about their work.*

**This is not a new idea and it is not this assessment's.** It is recorded in [C-008](../LANE_COORDINATION.md)'s own analysis — *"the declarations never reaching the surfaces where they would matter"* — and the assessment's contribution is to confirm it holds after nine more endpoints and to say that **it is now the highest-value Product Surface work available.**

> **Ruled as option C now, option D next — so this section is stage 2 and remains unbuilt.** Its unblocked half is *displaying* what we sell and who has to agree on the brief, with **no grading**; anything asserting a fit waits on [C-002](../LANE_COORDINATION.md). §8.7.

**It also composes with `sales_engagement`.** SE-02 already joins the declared Buying Committee Role to the observed appointment — a reasoning step whose *inputs* the seller is currently not permitted to see. **Surfacing the declarations on the brief puts the premise next to the conclusion**, which is the whole argument for provenance (principle 2).

### 8.6 · Which screens still feel like developer tools?

**Measured against one test: does the screen read as somebody's judgement about a job, or as a form over a data model?**

| Screen | Verdict |
|---|---|
| **Attention list** | **Commercial software.** It asks questions rather than reporting statistics, and it is absent when it has nothing to ask |
| **Account brief** | **Commercial software.** It is ordered to be stopped reading |
| **Team** | **Commercial software.** Invitations, roles and history, in the customer's words |
| **Connection Center** | **Commercial software**, and the outcome-per-failure error handling is better than most of the product |
| **Settings** | **Adequate.** An index of cards; it is honestly an index |
| **`/settings/products`** | **🟠 The one that reads as a tool.** Five editors in a column under one heading, no read mode, no hierarchy — 8.4 |

**One repository-wide gap, and it is not a screen.** No surface is responsive below 768px — [C-026](../LANE_COORDINATION.md) / [B-019](../BUGS.md). **A product a seller cannot open between meetings is a desk tool**, whatever the desktop layout looks like, and that is the largest single "feels like software for engineers" finding in the product. It is a decision, not a slice, and it has been open since 2026-08-02.

---

### The conclusion, stated plainly — and what happened to it

**Product Surface was not short of ideas. It was short of five decisions, four of them waiting since 2026-08-02.**

| Slice | Value | Was blocked by | Now |
|---|---|---|---|
| **CX-05** · a seller can read the commercial profile | **Every AE and SDR, every day** | [C-008](../LANE_COORDINATION.md) | ✅ **Ruled and shipped, 2026-08-03** — option C. §8.7 |
| **CX-07** · responsive shell and screens | The product on anything but a laptop | [C-026](../LANE_COORDINATION.md) | ✅ **Ruled 2026-08-03 — phone is in scope.** Executable, unbuilt |
| **CX-04** · the signal glossary | Nine words a first-time reader cannot look up. **Built, and reverted** | [C-025](../LANE_COORDINATION.md) | ⏳ Still waiting |
| **CX-08** · target accounts actually get watched | The one place the product accepts an instruction and does nothing | [C-021](../LANE_COORDINATION.md) | ⏳ Still waiting |
| **TASK-011** · the brief's hierarchy pass | Refinement, not capability | **A seller in the room** | ⏳ Correctly not a slice |

> **Two of the five were ruled on the day the assessment named them, and one of the two shipped the same day.** That is the assessment paying for itself: the work was never blocked on engineering, and putting the two decisions in front of the person who owns them was worth more than another slice would have been.

---

## 8.7 · CX-05, as built — *2026-08-03*

**[C-008](../LANE_COORDINATION.md) ruled by the product owner: option C now, option D next.** Stage 1 is `/business` — a read-only commercial profile at a top-level, member-reachable route.

### What it cost, and what it did not

| | |
|---|---|
| **Backend change** | **None.** Not an endpoint, not a policy line, not a migration |
| **Frozen files touched** | **None.** `permissions.ts` is untouched — a route absent from `GUARDED_ROUTES` is member-reachable by construction, which is the whole argument for C over A |
| **New navigation entries** | **One**, and D38's every test still holds: not a pipeline module with a menu item, not *show me all the X*, and it leads to something rather than to *coming soon* |
| **What a member gained** | **Five declarations `policy.csv` had granted them all along** |

### The shape is the customer's, not the API's

**The authoring screen renders five declarations as five editors in a column**, because each arrived in its own slice — §8.4's finding. **A reader does not have five questions; they have one, asked about each product.** Three of the five cite a product, so the product is the spine:

```
  what we are pushing            ← focus, if there is one — the only declaration that expires
  ├─ Product              name · description
  │    who buys it        industries · countries · size
  │    who has to agree   title · part
  └─ …
  companies we are chasing       ← target accounts, if there are any
```

**Focus leads because it is the only one with a shelf life.** The others describe what is permanently true of the business; focus says what is true this quarter, and a seller reading to decide their next move needs the perishable fact first.

### Three refusals

**It grades nothing.** No score, no rank, no *this account fits*. Comparing a real company to a description is **matching**, matching has no owner ([C-002](../LANE_COORDINATION.md)), and Commercial Profile computes nothing (ADR-0035). **That is the boundary the ruling drew between stage 1 and stage 2**, and it is what made stage 1 buildable in a day without settling one ownership question. Asserted by a test that walks the rendered text for *fit*, *match*, *score*, *rank* and *qualified*.

**A fact true of every product is said once, not once per product.** If no product has an ideal customer described, the page says so at the section rather than printing five identical notes — repeated identical text is what a reader learns to skip, and skipping is how they miss the one that appears when a colleague describes the sixth. When *some* product has one, the absence becomes informative and moves onto the product that lacks it.

**A member is offered no link they cannot follow.** The empty state teaches an owner how to fix it and tells a member who can — *a control that goes nowhere costs more trust than an absent one* (principle 8), which is the same reasoning that refused option A for the whole item.

### The gate that could not see the sidebar

**`infra/reachability.py` reported `/business` as having no entrance**, and it was wrong — the entry is in the sidebar. **The check could not see `navigation.tsx` at all**: it matches `href="…"`, `href={\`…\`}` and `router.push(…)`, and the navigation holds its routes in an array (`{ href: '/', label: 'Attention' }`) rendered through `<Link href={item.href}>`. **Neither half matched.**

**Nothing revealed it because both existing entries had a second, literal door.** `/` has six; **`/settings` has exactly one — `no-workspace.tsx`.** Delete that one file and the check calls the most-used screen in the product an orphan. **CX-05 surfaced it by adding the first navigation entry since the check was written.**

**Fixed, with the bias kept in the right direction.** A route named as an object property counts as a door **only in a file that also renders a link** — because `GUARDED_ROUTES` has the identical shape and the opposite meaning, and counting it would let a route be *reachable* because something forbade it. **A new form of declaration therefore stays unmatched, which reports a false orphan rather than hiding a real one.** Four tests, and the new condition was mutated to confirm it is load-bearing rather than decorative.

### What stage 2 still owes

**Option D — the declarations on the screens the seller already uses.** Its unblocked half is *displaying* what we sell and who has to agree on the account brief, with **no grading of the account against it**; anything saying *this account matches this ICP* waits on [C-002](../LANE_COORDINATION.md). §8.5 is the argument; the ruling is *next*, not *instead*.

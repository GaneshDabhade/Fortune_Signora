# The Customer Experience Blueprint

> **The authoritative description of Signora as a customer meets it** — every screen, every route, every journey, and the gap between what the backend can do and what a customer can reach.
>
> **Created 2026-08-02** on the product owner's direction, after Human Review made the gap visible: *"the repository contains considerably more functionality than the application currently exposes."* This document measures that claim rather than restating it.
>
> **It is a living document.** Every figure was read out of the repository at the commit named below, and every one is re-measurable. **When a status here disagrees with the code, the code is right and this is a defect** (`CLAUDE.md` §2).

**Measured at `origin/integration` = `11280f0`, 2026-08-02.** Frontend routes from `frontend/app/`, endpoints from `backend/modules/*/interface/router.py`, mounts from `backend/apps/api/main.py`, guards from `frontend/lib/state/permissions.ts`, navigation from `frontend/components/shell/navigation.tsx`.

---

## 0 · The headline, before the detail

**Three numbers, and the third is the finding.**

| | |
|---|---|
| **Backend HTTP endpoints** | **31**, across **11 modules** |
| **Application screens** | **5** — one attention list, one account brief, three settings pages *(plus the five sign-in screens)* |
| **Screens a `member` can reach** | **2** |

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
              ▼                                      └─▶ /settings/connections  NOT LINKED
      /accounts/[accountId]  Brief
      (reachable only from the list)                       ▲
                                                            │
                                              only via the OAuth callback,
                                              which starts here — a closed loop
```

### Every customer-accessible area, and how it is reached

| Area | Route | Reached by | Who |
|---|---|---|---|
| **Attention list** | `/` | Navigation · the wordmark · post-decision *"All accounts"* | Every role |
| **Account brief** | `/accounts/[id]` | A row on the attention list · `j`/`k` · the post-decision offer | Every role |
| **Settings** | `/settings` | Navigation | **Owner only** |
| **Products** | `/settings/products` | A link on Settings | **Owner only** |
| **Connection Center** | `/settings/connections` | **Nothing.** Only the OAuth redirect helpers | **Owner only** |
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
| **Connection Center** | `/settings/connections` | Integrations | ✅ | ✅ | ❌ **No entry point** | **Unreachable** |
| **Sign-in · sign-up · forgot · reset · verify** | `/(auth)/*` | Better Auth | ✅ | ✅ | ✅ Complete | **Production** |
| **Team** | — | Workspace & Tenancy | ✅ endpoint | ❌ | ❌ | **Blocked — [C-024](../LANE_COORDINATION.md)** |
| **Timeline** | — | Timeline | ✅ endpoint | ✅ **component built** | ❌ **not mounted** | **Blocked — [C-024 (Lane B's)](../LANE_COORDINATION.md)** |
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
| **See what has happened to an account over time** | `GET /accounts/{id}/timeline` | **Nothing.** Endpoint, hook *and* `components/timeline/feed.tsx` are all built — **no page imports the component** | **[C-024, Lane B's](../LANE_COORDINATION.md)** — a surface with nowhere to mount it |
| **See connected systems as a list** | `GET /workspaces/{id}/connections` | **No consumer.** The Connection Center reads `/integrations` instead | Not blocked — an observation for the owning lane |
| **Read the entity graph** | `GET /knowledge-graph` *(1 endpoint)* | No dedicated surface; the brief consumes it indirectly | Not blocked — **no journey asks for one** |

### 🟠 Backend complete · navigation missing

| Capability | Where it lives | What is missing |
|---|---|---|
| **Connect a CRM** | `/settings/connections` | **An entrance.** Nothing in the product links to it |
| **See what my company sells** *(as a seller)* | `/settings/products` | A member-reachable route — **[C-008](../LANE_COORDINATION.md)** |

### 🔴 Workflow incomplete — the customer starts something that cannot finish

| Journey | Where it stops | Blocked by |
|---|---|---|
| **Declare target accounts → Signora watches them** | The declaration is recorded, the event publishes, the consumer computes the delta — **and nothing starts a sync** | **[C-021](../LANE_COORDINATION.md)** |
| **Guided first run** | Ends by asking which companies to watch; the answer goes nowhere | [C-007](../LANE_COORDINATION.md) → [C-021](../LANE_COORDINATION.md) |
| **Use Signora on a phone** | No navigation below 768px | **[C-026](../LANE_COORDINATION.md)** · [B-019](../BUGS.md) |

### ⚫ No backend at all — not this document's gap, recorded for completeness

**Provider Platform · Provider Normalization · Observation Engine · AI Reasoning Engine have no HTTP router.** For the three pipeline modules that is correct — they are event-driven and a customer has no business calling them. **Provider Platform is the one worth noting**: `provider.health_changed` is published, `12-scalability.md` depends on its metrics, and **there is no way for anybody to see whether a provider is healthy.**

**Recommendation Engine · Timeline surfaces · Revenue Intelligence Platform · Notifications (M14a) · Billing (M14b)** are not started. **RIP's is a `README.md` unowned capability already**: *"the RevOps surface — RIP owns it, no journey defined."*

---

## 4 · Workflow Mapping

**Nine journeys, and where each one currently stops.**

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
| **J6** | See an account's history over time | 🔴 **Blocked** | The feed is built and mounted nowhere |
| **J7** | Tell Signora who we sell to | ⚠️ **Half** | An owner can declare; **a seller cannot read** |
| **J8** | Connect our systems | ⚠️ **Half** | Complete once reached; **unreachable** |
| **J9** | Manage who is on the team | 🔴 **Blocked** | No screen; no way to name a person |

**Five of nine are complete, and they are the five that matter most** — the daily loop of a salesperson is whole. **Four of nine are administrative or contextual, and all four are stopped by something already recorded.**

**Not one of the four is stopped by missing engineering.** J6 and J9 wait on `C-024`; J7 waits on `C-008`; J8 waits on a **link**.

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
| **CX-01** | **The Connection Center gets an entrance** | **J8** | A whole shipped module a customer cannot currently find. **Backend, screen, OAuth flow and disconnect are all complete** — this is a link and a card on Settings | **No.** Executable today |
| **CX-02** | **Settings becomes an index of what an administrator can do** | J7 · J8 · J9 | Today it lists organizations and links one page. It should say what is configurable and what is not yet | **No** |
| **CX-03** | **Timeline mounts on the brief** | **J6** | An endpoint, a hook and a built component that reach nobody | **[C-024, Lane B's](../LANE_COORDINATION.md)** — the mount point is Lane A's routing decision. **One sentence from executable** |
| **CX-04** | **The signal glossary** | J2 · J3 | Nine words a first-time reader cannot look up. **Built and reverted** | **[C-025](../LANE_COORDINATION.md)** |
| **CX-05** | **A seller can read the commercial profile** | **J7** | Every AE and SDR, every day | **[C-008](../LANE_COORDINATION.md)** |
| **CX-06** | **The Team page** | **J9** | An owner cannot see who is in their organization | **[C-024](../LANE_COORDINATION.md)** |
| **CX-07** | **Responsive shell and screens** | All | The product on a device other than a laptop | **[C-026](../LANE_COORDINATION.md)** |
| **CX-08** | **Target accounts actually get watched** | J7 | The one place the product accepts an instruction and does nothing with it | **[C-021](../LANE_COORDINATION.md)** |

> **CX-01 and CX-02 are executable today and unlock two shipped modules between them.** Everything below them is a decision away, and each decision is already recorded.

**What is deliberately not on this list:** a Provider health screen, a RevOps dashboard, a notifications centre and a recommendations surface. **Three have no backend and one has no journey** — building any of them would be a new capability rather than the completion of an existing one, and that is the product owner's to schedule.

---

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

# 486 · Cross-application experience readiness — can a customer complete the journey?

**Lane C · Product Office · 2026-08-07.** **[D-150](../DECISION_REGISTER.md), product owner.**

> ⚡ **The question changed.** **[484](484-ui-conformance-and-gap-audit.md) asked *is this screen implemented*; [485](485-ui-platform-readiness.md) asked *is this component reusable*. This asks *can a customer finish*.**

**Primary evidence: the 110 Playwright journeys on `origin/integration`, across 15 specs.** ⚡ **A journey test is the closest thing this repository has to a customer completing something**, and [§19](../../CLAUDE.md) already treats it as implementation evidence rather than as verification.

---

# 0 · The answer

> ## ✅ **Seven of the ten scenarios you named are executable today. Six are journey-tested.**
>
> ⛔ **Three are not, and each fails for the same reason: a *shell* capability that does not exist — notifications, a global search surface, an AI panel.** ⚡ **[485](485-ui-platform-readiness.md) predicted exactly this: the primitives are a platform and the shell is not.**

---

# 1 · The ten scenarios, measured

| Scenario | | Evidence |
|---|---|---|
| **Login → Dashboard** | ✅ **Executable, journey-tested** | `auth-journey.spec.ts` — *"the root path redirects to sign-in"*, *"`${path}` is not reachable without a session"* |
| **Dashboard → Accounts** | ✅ **Executable, journey-tested** | `daily-usage.spec.ts` — *"opens with accounts ranked by attention"*, *"the ranking is an ordering, not a coincidence"* |
| **Accounts → Account Details** | ✅ **Executable, journey-tested** | `accessibility.spec.ts` — *"an account can be opened with the keyboard alone"* · `consistency.spec.ts` — *"the score on the row is the score on the brief"* |
| **Workspace Switch → Data Refresh** | ✅ **Executable, journey-tested** | `resilience.spec.ts` — *"the active organization survives a reload"* |
| **Settings → Save → Confirmation** | ✅ **Executable, journey-tested** | `business-setup.spec.ts` — *"a customer can add a product and see it listed"* |
| **Invite Member → Accept Invitation** | ✅ **Executable, journey-tested** | `/join/[workspaceId]` route + `permissions.member.spec.ts` |
| **Search → Open Result** | 🟡 **Executable, NOT journey-tested** | `account-search.tsx` is substantial — debounced query, `useAccountSearch`, keyboard `active` index, aria listbox, `router.push` to the account. ⛔ **Zero e2e tests mention search** |
| **Registration → Verification → Login** | 🟡 **Executable, NOT journey-tested** | `sign-up`, `verify-email` routes exist and `sign-up-form` pushes to `verify-email`. ⛔ **No spec covers it** — only a fixture names it |
| ⛔ **Notification → Navigate to Context** | ⛔ **Not started** | **Zero files under `frontend/` mention notifications.** **Not a partial surface — an absent one** |
| ⛔ **AI Copilot → Execute Action** | ⛔ **Not started** | **No copilot component, no panel, no entry point.** ⚡ **`AI Copilot` is a finalized design with 24 distinct phrases and none in the code** ([484](484-ui-conformance-and-gap-audit.md)) |

---

# 2 · Experience by experience

| Experience | Status | Evidence |
|---|---|---|
| **Navigation** | ✅ **Functionally complete** | **15 journeys.** Global nav, page-to-page, back/forward *(`resilience`: "forward after back returns to the account")*, direct load, refresh, redirect, route guards. ⛔ **No breadcrumbs** — no component, no design conformance |
| **Authentication** | 🟡 **Partially working** | **12 journeys** covering session, unauthorized routing, token refusal, sign-out. ⛔ **No authentication *shell*** — `(auth)` has five `page.tsx` and no `layout.tsx` ([485](485-ui-platform-readiness.md) §6). ⛔ **Registration→verification untested** |
| **Workspace** | ✅ **Functionally complete** | Switching, creation dialog, invitation route, selection. **3 journeys** including *"the new-organization dialog is labelled and escapable"* |
| **Search** | 🟡 **Partially working** | ✅ **Account search is real.** ⛔ **No *global* search** — App Shell §08 specifies one and no component exists. ⛔ **No suggestions, filtering or persistence.** ⛔ **0 journeys** |
| **Notifications** | ⛔ **Not started** | **Nothing. No badge, no panel, no read/unread, no empty state.** App Shell §10 |
| **AI** | ⛔ **Not started** *(as an experience)* | ✅ **Reasoning and evidence *display* exist** — `narration.tsx`, `evidence.tsx`, `contributions.tsx`, and a labelled evidence drawer. ⛔ **No copilot entry, no side panel, no AI actions.** ⚡ **The intelligence is rendered; there is nowhere to ask it anything** |
| **Tables** | 🟡 **Partially working** | **7 journeys** on ranking and row content. ✅ Sorting *(ranking is asserted as an ordering)*. ⛔ **No pagination, bulk actions, row actions or column controls in `table.tsx`** |
| **Forms** | ✅ **Functionally complete** | **5 journeys**: validation *("a product with no name cannot be saved")*, save, cancel *("cancelling a decision records nothing")*, **and unsaved-changes** — `confidence.spec.ts`: *"a session that ends mid-edit does not silently discard"* |
| **Feedback** | ✅ **Functionally complete** | **10 journeys.** `toast.tsx` exists, confirmation dialogs, focus return, Escape semantics. ⚠️ **`toast` lives outside `components/ui/`** |
| **Global UX** | ✅ **Functionally complete** | **8 journeys**: empty states, slow API *("shows something rather than an empty frame")*, offline *("losing the connection mid-visit is recoverable")*, permission denied, error pages. ⛔ **No route-level `loading.tsx`** |
| **Accessibility** | ✅ **Production ready — the strongest area** | **11 dedicated `@a11y` journeys** plus `interaction-boundaries.spec.ts`: focus trapping, focus return, keyboard-only navigation, labelled inputs, *"the current page is announced, not only coloured"*, and `visual.spec.ts` asserting no sideways scroll and no clipped text on every screen |

---

# 3 · ⚡ What this says about the goal

**[D-150](../DECISION_REGISTER.md)'s objective: *new features built primarily by composing existing platform capabilities*.**

| | |
|---|---|
| ✅ **Already composition** | **Navigation · workspace · forms · feedback · global UX · accessibility · tables *(read)*** — a new screen inherits all of these without building anything |
| ⛔ **Still infrastructure** | **Notifications · AI panel · global search** — the next screen that needs one builds it |

> ⚡ **The reason is consistent and worth stating once: every complete experience is one a *screen* owns, and every missing one is one the *shell* owns.** **This repository built screens well and a shell partially, and the journeys show exactly that seam.**

---

# 4 · Backlog — [D-150](../DECISION_REGISTER.md) asks for actionable outcomes this time

⛔ **No cosmetic rows.** **Each below is a reusable capability whose absence stops a named journey.**

| Row | Capability | Blocks | Module |
|---|---|---|---|
| **[TASK-480](../BACKLOG.md)** | **Notification platform** — badge, panel, read/unread, empty state, navigate-to-context | ⛔ *Notification → Navigate to Context* | `product_surface` — **Lane A** |
| **[TASK-481](../BACKLOG.md)** | **Global search surface** — App Shell §08, composing the existing account search | ⛔ *Search across the application* | `product_surface` — **Lane A** |
| **[TASK-482](../BACKLOG.md)** | **AI Copilot entry and side panel** — App Shell §12 and §13 | ⛔ *AI Copilot → Execute Action* | `product_surface` — **Lane A** |
| **[TASK-483](../BACKLOG.md)** | **Authentication shell** — `(auth)/layout.tsx`, the shared card, branding and hierarchy | ⚠️ Five screens re-state one frame | ⛔ **Ownership unresolved — [C-430](../LANE_COORDINATION.md)** |
| **[TASK-484](../BACKLOG.md)** | **The two untested journeys** — *Search → Open Result*, *Registration → Verification → Login* | ⚠️ Both work and neither is verified ([D-113](../DECISION_REGISTER.md)) | `product_surface` — **Lane A** |

⛔ **Sequencing**: **TASK-484 first** *(it verifies what already exists and is the cheapest)*, then **TASK-481** *(composes a built component)*, then **TASK-480**, then **TASK-482** *(the largest, and the one whose design has the most unbuilt surface)*. **TASK-483 cannot be sequenced until [C-430](../LANE_COORDINATION.md) is ruled.**

⛔ **Not created, deliberately**: breadcrumbs, tabs, avatars, dropdowns, tooltips, charts. ⚡ **[485](485-ui-platform-readiness.md) lists them and none blocks a journey today** — a row for each would be the speculative work [§6](../../CLAUDE.md) forbids.

---

# 5 · The charting decision, as instructed

✅ **Not blocking anything, and no row created.** **[D-150](../DECISION_REGISTER.md): *do not block implementation waiting for a chart library decision… bring that decision only when we are actually ready to implement the first chart-heavy experience.***

⚡ **The first chart-heavy experience is `Executive Dashboard` or `Reports`, and neither has a route.** **An ADR comparing Recharts, Tremor, shadcn-compatible approaches and token-driven custom components is prepared when one of those is scheduled — not before.**

---

# 6 · What this audit did not do

⛔ **It did not run the journeys.** **They are QE's** — `clean_database` truncates every table. ⚡ **So *"journey-tested"* here means a spec exists and asserts the behaviour, not that it passed today.** **QE's last cycle reported the suite green at 3,931 passing.**
⛔ **It did not open a browser.** **Deep linking, browser history and refresh are asserted by `resilience.spec.ts` rather than observed.**
⛔ **It did not measure colour contrast.** **`visual.spec.ts` asserts no invisible text; contrast ratios are unmeasured.**

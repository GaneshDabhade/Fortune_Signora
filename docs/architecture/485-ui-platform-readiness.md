# 485 · UI Platform Readiness — is a new screen composition or bespoke work?

**Lane C · Product Office · 2026-08-07.** **[D-149](../DECISION_REGISTER.md), product owner.**

> ⛔ **A platform audit, not a feature audit.** **[484](484-ui-conformance-and-gap-audit.md) measured screens; this measures only what every screen composes from.** ⛔ **No implementation task is created — [D-149](../DECISION_REGISTER.md) says measure first.**

**Measured against `origin/integration`, and against the design snapshot as the only UI source of truth ([D-138](../DECISION_REGISTER.md)).**

---

# 0 · The answer

> ## ⚡ **No. A new screen today is roughly half composition and half bespoke work.**
>
> **The *primitives* are real and reused — 80 imports from `components/ui` across 44 files, and every page composes rather than duplicates.** ⛔ **The *shell* is not: nine of eighteen App Shell sections have no component at all, and the design specifies twenty-two.**

**A screen that needs a button, a table, an empty state or a skeleton reuses one today.** ⛔ **A screen that needs breadcrumbs, a user menu, a global filter, a notification surface, a utility panel or an AI entry point builds it — or does without.**

---

# 1 · Navigation platform

## 1a · What the design specifies against what exists

**`Fortune Signora App Shell.dc.html` enumerates itself: twenty-two numbered sections.** **Eighteen are components; `20 Responsive`, `21 Accessibility` and `22 Rationale` are properties, and `15 Keyboard shortcuts` is behaviour.**

| ✅ Component exists | ⛔ No component |
|---|---|
| `01 Assembled shell` · `02 Left navigation` · `03 Workspace switcher` · `09 Command palette` · `14 Context drawer` · `16 Global loading` · `17 Error pages` · `18 Empty workspace` · `19 Multi-workspace` | **`04 Top navigation` · `05 Breadcrumbs` · `06 Global filters` · `07 Banners and status` · `08 Global search` · `10 Notifications` · `11 User menu` · `12 AI assistant entry` · `13 Utility panel`** |

> ⛔ **Nine of eighteen. Half the shell the design specifies does not exist as a component.**

⚠️ **Measured by component file, not by string.** **A first pass searched the source for words like *banner* and *notification* and scored fifteen of eighteen present — [B-101](../BUGS.md)'s class, and discarded.** **`topbar`, `banner`, `notification` and `assistant` all appear in the codebase as words with no component behind them.**

## 1b · The navigation itself

| | |
|---|---|
| **Design** | **A left rail with eight primary entries**, four of which name screens the design set does not contain ([C-424](../LANE_COORDINATION.md)) |
| ⛔ **Implementation** | **Three: `Attention` · `Your business` · `Settings`** |

⛔ **Not audited, because no component exists to audit**: navigation groups · nested navigation · collapsed mode · badges · notification counters · dynamic counts · mobile navigation · breadcrumbs · organization menu.
✅ **Active state and route highlighting exist** in `navigation.tsx`. ✅ **Workspace switching exists** — `workspace-selector.tsx`. ⛔ **A user menu does not.**

---

# 2 · ⚡ Navigation completeness — the question you asked directly

> ## ✅ **Yes. Every implemented screen is reachable through the real navigation, except one, and that one is correct.**

**Measured by building the link graph — every `href=`, `href:` and `router.push` across `frontend/app` and `frontend/components`.**

| Screen | Route | |
|---|---|---|
| Attention · Your business · Settings | `/` · `/business` · `/settings` | ✅ **in the nav rail** |
| Connections · Products · Team | `/settings/*` | ✅ **linked from Settings** |
| Account 360 | `/accounts/[accountId]` | ✅ **linked from `decided`, `sequence`, `account-search`** |
| **Workspace invitation** | `/join/[workspaceId]` | ⛔ **no link — and correctly so: it arrives in an email** |

⛔ **No developer is opening routes directly.** ⚡ **That is a genuine strength and it is worth saying, because eight routes is a small enough surface that it could easily not have been true.**

---

# 3 · Routing

| | |
|---|---|
| **Implemented routes** | **13 `page.tsx`** — 8 application, 5 authentication |
| ⛔ **Missing routes** | **15 of 25 designs have no route** ([484](484-ui-conformance-and-gap-audit.md) §4) |
| ✅ **Placeholder routes** | **None found** — no route renders a stub |
| ✅ **Broken routes** | **None** — every internal destination resolves to a `page.tsx` |
| ✅ **Protected routes** | **`route-guard.tsx`, applied at `(app)/layout.tsx`** |
| ✅ **Error and not-found** | **`app/error.tsx`, `app/not-found.tsx`** |
| ⛔ **Loading transitions** | **No `loading.tsx` at any level.** ⚡ **`skeleton.tsx` exists and is used per-component; Next's route-level loading boundary is unused** |
| ⚠️ **Deep links · browser history · refresh** | ⛔ **Not measurable statically.** **They need a running browser, and [§2](../../CLAUDE.md) says no screen is complete until a human reviews it** — [TASK-455](../BACKLOG.md) makes that environment reachable and nobody has walked it |

---

# 4 · Layout system

✅ **Exists and is reused**: `card.tsx` · `dialog.tsx` · `drawer.tsx` · `empty-state.tsx` · `error-state.tsx` · `skeleton.tsx` · the `(app)/layout.tsx` shell.
⛔ **No component**: page header · page title · sticky header · split layout · side panel · section.
⚠️ **Content width, grid and spacing are Tailwind utilities applied per page**, not a layout primitive. **Nothing enforces one page width**, so each screen re-decides it.

---

# 5 · Design system — token by token, component by component

| ✅ Tokens, all six | `typography` `colors` `spacing` `elevation` `radius` `shadows` — in `tailwind.config.ts` and `globals.css`, enforced by `design-tokens.test.tsx` |
|---|---|
| ✅ **Components present** | `button` · `input` · `select` · `table` · `badge` · `empty-state` · `skeleton` · `error-state` · `card` · `dialog` · `drawer` · `command-palette` · `confidence` |
| 🟡 **Present, outside `ui/`** | **`toast`** — lives in `components/feedback/`, **and it is the one primitive a screen cannot find where it looks** |
| ⛔ **Missing** | **`icons` · `tabs` · `accordions` · `timeline` · `charts` · `avatars` · `breadcrumbs` · `dropdowns` · `tooltips`** |

> ⛔ **Nine of twenty-four primitives are missing, and `charts` and `timeline` are named by `Executive Dashboard`, `Reports`, `Account 360` and `Opportunity Intelligence`.**

---

# 6 · Authentication shell

⛔ **Not measurable as a shell, because there is no shell.** **`(auth)` has five `page.tsx` files and no `layout.tsx`** — **so there is no authentication layout, no shared card, no shared branding, and each of the five screens re-states its own frame.**

⚠️ **[478](478-design-conformance-audit.md) measured the *content*: 1 of 11 named elements, and five of eight screens predate the finalized design.** ⚡ **This adds the structural half — the thing that would make them consistent does not exist.**

---

# 7 · Global components

| | |
|---|---|
| ✅ **Command Palette** | `command-palette.tsx` — ⚡ **[TASK-478](../BACKLOG.md), and the only one built *from* the design** |
| ✅ **Right information panel** | `drawer.tsx` |
| ✅ **Global loading overlay** | `skeleton.tsx` *(per-component, not an overlay)* |
| ⛔ **Global Search** | **No component.** [C-424](../LANE_COORDINATION.md)'s rail names it |
| ⛔ **Notifications** · ⛔ **Activity Feed** · ⛔ **Global Filters** · ⛔ **User Profile Menu** · ⛔ **Help Center** · ⛔ **Feedback Widget** · ⛔ **AI Copilot Panel** | **None** |

**Three of eleven.**

---

# 8 · Component reuse — the healthiest finding here

**80 imports from `components/ui` across 44 files. Every one of the 8 pages composes and none uses raw markup.**

| | |
|---|---|
| 🟢 **Composes cleanly** | **31 files** |
| 🟡 **Mixed** — composes, and drops to a raw element once or twice | **9 files** — `committee`, `icp`, `contributions`, `decided`, `entity-name`, `evidence`, `narration`, `research`, `validation` |
| 🔴 **Raw markup only** | **4 files** — `toast.tsx`, `account-search.tsx`, `sequence.tsx`, `theme-toggle.tsx` |

**16 raw `<table|button|input|select|dialog>` elements in total.** ⚡ **That is a low number against 80 imports, and it clusters**: `account-search` and `sequence` both hand-roll an input, which is what a missing `combobox`/`search` primitive looks like from the inside.

> ✅ **The reuse discipline is working.** ⛔ **Where it breaks, it breaks because the primitive does not exist — not because a lane ignored the library.**

---

# 9 · Classification, as [D-149](../DECISION_REGISTER.md) asks

## ✅ Ready for new feature composition

**The six token scales · `button` · `input` · `select` · `table` · `badge` · `card` · `dialog` · `empty-state` · `error-state` · `skeleton` · `drawer` · `command-palette` · `route-guard` · `workspace-selector` · `app-shell`.**
⚡ **Reuse these unchanged.** **`design-tokens.test.tsx` already refuses a literal colour, radius or type size.**

## 🟠 Needs platform investment — before significant additional UI

**In the order the 26 designs demand them:**

**① Authentication layout** — `(auth)/layout.tsx`. **Five screens re-state one frame today.**
**② Page header / title / sticky header** — every one of the 25 designs has one.
**③ `tabs`** — `Settings`, `Account 360`, `Security Center`, `User Profile`.
**④ `avatars`** — `Team Management`, `User Profile`, `App Shell`'s user menu.
**⑤ `dropdowns` + `tooltips`** — prerequisites for the user menu and most tables.
**⑥ `charts` + `timeline`** — `Executive Dashboard`, `Reports`, `Account 360`, `Opportunity Intelligence`. ⚠️ **The largest single item, and probably a 🔴 dependency decision** ([§6](../../CLAUDE.md) forbids a new library without an ADR).
**⑦ Move `toast` into `components/ui/`** — ⚡ **the cheapest item here: it exists and cannot be found where a lane looks.**

## ⚠️ Legacy implementation — built before the finalized design

**The five `(auth)` screens** ([478](478-design-conformance-audit.md): five of eight predate it) · **`navigation.tsx`** — three entries against a designed eight · **`app-shell.tsx`** — assembled before nine of its eighteen sections existed.
⛔ **None is broken.** ⚡ **[D-149](../DECISION_REGISTER.md): *do not assume the older implementation is acceptable simply because it works.***

## ⛔ Missing platform capability

**Top navigation · breadcrumbs · global filters · banners · global search · notifications · user menu · AI assistant entry · utility panel · icons · tabs · accordions · timeline · charts · avatars · dropdowns · tooltips · page header · split layout · side panel · route-level loading.**

---

# 10 · What I could not determine, and the question I owe you

⛔ **Three things need a running browser and I did not open one**: **deep links · browser history · refresh behaviour.** ⚡ **[TASK-455](../BACKLOG.md) makes the demo environment reachable; nobody has walked it, and that walk is the only way these get answered.**

> ## ⚠️ **One targeted question, and it blocks the largest item in §9.**
>
> **`Executive Dashboard`, `Reports`, `Account 360` and `Opportunity Intelligence` all render charts. ⛔ The design set specifies what a chart *looks like* and never says what draws it.**
>
> **[§6](../../CLAUDE.md) forbids introducing a charting library without an ADR, and [§20c](../../CLAUDE.md) makes `components/ui` a 🔴 surface.** **So: is a charting dependency approved in principle, or should charts be built from the token scales?**
>
> ⛔ **I am not proposing an answer.** **It is a 🔴 dependency decision, it gates four screens, and guessing it would be the *"convenient assumption"* [D-140](../DECISION_REGISTER.md) forbids.**

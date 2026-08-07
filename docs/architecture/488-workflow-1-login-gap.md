# 488 · Workflow 1 — Login: the measurable gap against the approved design

**Lane C · Product Office · 2026-08-07.** **[D-153](../DECISION_REGISTER.md) — the UI Replacement Program, workflow-first.**

> ⛔ **This is the gap analysis [TASK-467](../BACKLOG.md) names as its own first act**, bounded to **Workflow 1 — Login** and to nothing else. **[D-129](../DECISION_REGISTER.md) permits exactly three derived artifacts and this is one of them: a measurable gap analysis.** ⛔ **No checklist, no translation, no intermediate specification.**

**Source of authority, opened rather than cited**: `docs/design-snapshot/screens/Fortune Signora Authentication.dc.html` — **73,936 bytes, 24 screens and states, `Platform foundation · Module 1`.** **Every number below is from that file or from the implementation, and nothing is inferred from either.**

---

## 0 · The answer in three lines

> ## ⛔ **① The login screen implements 3 of the 12 elements its design specifies. The card is 384px where the design says 400px, and there is not one breakpoint in `app/(auth)/`.**
>
> ## ✅ **② The palette is the whole of the visual gap and it is 26 values in one file. `globals.css` holds 78 custom properties and *zero* of the design's sixteen colours — because the current palette is Tailwind's default slate-and-blue ramp, which is the design's own critique, word for word.**
>
> ## ⚠️ **③ Three affordances the design draws on the sign-in card have no backend, and one of them changes an authentication semantic. That is [C-431](../LANE_COORDINATION.md) and it is the product owner's — D-153 says *do not guess*.**

---

## 1 · ✅ What is already right, said first

**[D-153](../DECISION_REGISTER.md) says to preserve everything below the presentation layer and to reuse any component that already conforms. Measured, four things do:**

| | Evidence |
|---|---|
| ✅ **Focus geometry is already exactly as specified** | `globals.css:205` — `:focus-visible { outline: 2px solid; outline-offset: 2px }`. **The design's SC 2.4.7 reads *"2px brand focus ring at 2px offset"*.** ⚡ **Only the colour differs.** ⛔ **Do not rebuild this** |
| ✅ **Reduced motion is handled globally** | `@media (prefers-reduced-motion: reduce)` over `*`, `*::before`, `*::after`. **The design lists it as the sixth motion row; the repository already honours it in the one place it cannot be forgotten** |
| ✅ **A dark theme already exists as a token swap** | `:root[data-theme='dark']` redefines the roles. **The design ships a full dark palette.** ⚡ **So dark mode is a second column of values, not a second implementation** |
| ✅ **The token architecture is right — it is the values that are wrong** | **78 custom properties · 26 semantic colour roles · `--radius-xl` · `--control-*` · `--shadow-*`**, enforced by §20c and held by `design-tokens.test.tsx`. ⚡ **This is what makes ② a one-file change instead of a rewrite** |

> ⚡ **Better Auth is untouched by everything below.** **Not one item in this document requires a change to `lib/auth/server.ts`, the RS256 verification, `requireEmailVerification`, or any route** — **except the one in §5, which is why §5 is a question rather than a task.**

---

## 2 · ⚡ The palette — the whole visual gap, in one file

**`app/globals.css` defines 78 custom properties. The design defines sixteen colours plus four elevations, four radii and an easing curve. `git grep` for each of the design's sixteen hex values across `globals.css` returns *zero*.**

**The three that decide how the screen reads:**

| Role | Implementation | The approved design | What the difference is |
|---|---|---|---|
| **Ground** | `--color-canvas: 248 250 252` — **#f8fafc** | `--bg: #faf8f6` | ⚡ **Cool grey against warm.** **Tailwind `slate-50`** |
| **Primary** | `--color-accent: 37 99 235` — **#2563eb** | `--brand: #134e76` | ⚡ **Tailwind `blue-600` against deep petrol** |
| **Text** | `--color-content: 15 23 42` — **#0f172a** | `--ink: #211f1d` | **`slate-900` against a warm near-black** |

> ## ⛔ **The current palette is Tailwind's default ramp, and Design System v2's `Critique of Version 1` names that exact failure twice — *"cool greys"* and *"accent-as-alarm"*. The screen the product owner reviewed does not look wrong by accident; it looks like the framework's defaults, because it is them.**

✅ **And this is the good news [487](487-legacy-ui-migration-status.md) predicted, now with a number attached.** ⚡ **The migration of the *look* is a rewrite of roughly 26 values inside one file that every surface already reads through.** ⛔ **It is not a rewrite of the application** — **no component in `components/ui` contains a literal colour, because `design-tokens.test.tsx` has never let one land.**

⚠️ **What the palette does *not* fix: §§3, 4 and 5. Correct colours on a screen missing nine of twelve elements is a correctly-coloured wrong screen.**

---

## 3 · ⛔ Screen `02 · Sign in` — 3 of 12

**The design's own enumeration, in the order the card renders it. Measured against `app/(auth)/sign-in/page.tsx`, `sign-in-form.tsx` and `auth-shell.tsx`.**

| # | The design specifies | Implementation |
|---|---|---|
| 1 | **Product mark above the card** — `FS` · *Fortune Signora* | ⛔ **Absent.** The card opens on the heading |
| 2 | **`Sign in` + the workspace beneath it** — *"to Northwind Global"* | ⚠️ **Heading present, subtitle is a tagline** — *"AI Revenue Intelligence"*, not the workspace |
| 3 | ⚡ **Provider buttons *above* the divider** — *Continue with Google* · *Continue with Microsoft* | ⛔ **Inverted.** **Password first, providers last** — **and `sign-in-form.tsx` argues for the inversion in a comment**, which is §4's subject |
| 4 | **An `or` divider** | ✅ **Present** |
| 5 | **`Work email`** | ⚠️ **`Email`** |
| 6 | **`Forgot password?` on the password label row** | ⚠️ **Present, but below the whole form** — a different element in a different place |
| 7 | **`Show` — a password reveal** | ⛔ **Absent** |
| 8 | **`Keep me signed in for 30 days`** | ⛔ **Absent — and see [§5](#5--c-431--the-three-affordances-with-no-backend)** |
| 9 | **`Sign in` — one primary action** | ✅ **Present** |
| 10 | **`Your company uses SSO?` → `Use single sign-on`** | ⛔ **Absent — [§5](#5--c-431--the-three-affordances-with-no-backend)** |
| 11 | **Region and status under the card** — *"`EU · eu.signora.app`, and a live status dot. Buyers check both"* | ⛔ **Absent** |
| 12 | **The legal line below the card** | ⛔ **Absent** |

**Card geometry — 1 of 4.**

| | Design | Implementation |
|---|---|---|
| **Width** | **400px**, *"one card width across every screen"* | ⚠️ **`max-w-sm` — 384px** |
| **Radius** | **`--r-xl` — 16px** | ⚠️ **`rounded-lg`** |
| **Elevation** | **`--e2`** | ⛔ **None** |
| **Padding** | **32px** | ✅ **`p-8` — 32px** |

### ⛔ Responsive behaviour — 0 of 3, and it is the largest single gap

**The design specifies three, and gives the reason for each:**

- **Desktop ≥ 1024px** — *"centred at 400px, vertically centred with a 64px floor so it never sits under the fold."*
- **Tablet 640–1023px** — *"top-aligned at 96px instead of centred, so the keyboard on a tablet in portrait never pushes the primary action off screen."*
- **Mobile < 640px** — *"card becomes the page: no border, no radius, no shadow, 20px gutters. Primary action pins to the bottom above the keyboard; provider buttons stack full-width at 44px."*

> ⛔ **`auth-shell.tsx` is `flex min-h-screen items-center justify-center p-6`, and `grep` for a Tailwind breakpoint prefix across `app/(auth)/` returns nothing.** ⚡ **The design's own sentence for why this matters is the mobile one: *"the border, radius and shadow are dropped rather than shrunk, which is what keeps it from looking like a website on a phone."***

---

## 4 · The component states engineering builds against

**The design is explicit that this is the contract: *"Only three components carry this module: field, button and card. Each is the v2 component with no new variants — these are the states engineering builds against."***

### Field — 2 of 6 · `components/ui/input.tsx`

| State | Design | Implementation |
|---|---|---|
| **Rest** | `1px --line` | ✅ `border-border-strong` |
| **Hover** | `1px --ink-4` | ⛔ **Absent** |
| **Focus** | **`--brand` border + a 3px tint ring** | ⚠️ **The global 2px outline** — correct geometry for a *button*, not the field treatment the design draws |
| **Invalid** | **`--risk` + 3px tint** | ⚠️ `border-danger`, **no ring** |
| **Valid** | **`--pos` + 3px tint** | ⛔ **Absent — there is no valid state at all** |
| **Disabled** | **sunken ground, 60%** | ⚠️ `disabled:opacity-50` — **opacity, not the sunken ground** |

### Primary button — 3 of 6 · `components/ui/button.tsx`

| State | Design | Implementation |
|---|---|---|
| **Rest** | `--brand` + `--e1` | ⚠️ `bg-accent`, **no elevation** |
| **Hover** | `--brand-strong` | ✅ `hover:bg-accent-hover` |
| **Pressed** | **no shadow, 98% scale** | ⛔ **Absent** |
| **Focus** | 2px ring, 2px offset | ✅ **Global rule — already exact** |
| **Loading** | ⚡ ***"label kept, width fixed"*** | ⚠️ **Label kept ✅, width not fixed ⛔.** ⛔ **And `sign-in-form.tsx` never passes the `loading` prop `button.tsx` already has** — it swaps the label by hand and sets `disabled` |
| **Disabled** | **42%, no pointer** | ⚠️ **50%**, `disabled:pointer-events-none` ✅ |

---

## 5 · ⚠️ [C-431](../LANE_COORDINATION.md) — the three affordances with no backend

**[D-153](../DECISION_REGISTER.md) is unambiguous about what to do here: *"No lane may simplify the design. No lane may reinterpret the design. If something in the design is unclear: STOP."*** ⛔ **So these are raised, not decided.**

**The sign-in card draws three controls whose backing capability does not exist. Measured, not assumed:**

| Affordance | The backend | Why it is a question |
|---|---|---|
| **`Use single sign-on`** *(and `Sign in with SSO` on `01 · Welcome`)* | ⛔ **Absent.** **[418 §1](418-platform-foundation-assessment.md) lists *per-workspace SSO enforcement* and *domain→IdP routing* by name** | **Journey 3 of the design's five is `SSO-enforced`.** ⛔ **A login journey "exactly as designed" contains an SSO branch point** |
| **`Keep me signed in for 30 days`** | ⚠️ **`lib/auth/server.ts:86` — `expiresIn: 60 * 60 * 24 * 7`. Seven days, not thirty, and not electable** | ⛔ **This is the one item in this document that is an authentication *semantic*.** **[D-151](../DECISION_REGISTER.md) ④: only the infrastructure boundary may change** |
| **The attempt counter** — *"You have 3 attempts left before the account locks for 15 minutes"* | ⛔ **Absent entirely.** **`grep -rn "rateLimit\|lockout\|maxAttempts\|failedAttempts"` across `frontend/lib/auth/` and `backend/` returns zero.** ⚠️ **418 does not list it, because 418 audited what the design *shows* and this is what it *implies*** | **Screen `03` is a Workflow 1 screen and its message is a lockout message.** **Screens `11 · Account locked` and `12 · Too many attempts` are the same capability** |

**The options, and this office's recommendation:**

| | |
|---|---|
| **A** | **Bound Workflow 1 to screens `02`, `03` and `15` and build all three affordances against real capability** — ⛔ **three backend capabilities with no rows. Workflow 1 stops being a presentation-layer replacement, which is the one thing D-153 says it is** |
| **B** | **Render the affordances and route them somewhere honest** — ⛔ **a control that does not do what it says is worse than an absent one, and `03`'s counter would be a fiction. [D-151](../DECISION_REGISTER.md) ⑤ permits simulating a provider *response*; it does not permit simulating our own product's behaviour** |
| ✅ **C — recommended** | **Workflow 1 delivers every element of `02`, `03` and `15` whose capability exists, and the three named above are carried as their own rows behind Login rather than inside it.** ⚡ **This is not simplification: it is the same distinction [TASK-467](../BACKLOG.md) already drew when it put magic link, MFA and session-expiry out of scope with the product owner's approval, and it leaves the human review gate reviewing a real screen** |

> ⚠️ **Whichever is chosen, the review gate is affected and that is why this is asked before Lane A starts.** ⛔ **Under C the product owner reviews a login screen with no SSO entry point, and should know that going in rather than discover it.**

---

## 6 · What Workflow 1 is not

**[D-153](../DECISION_REGISTER.md): *"Do not decompose later workflows until the current workflow reaches the human review gate."*** ✅ **Honoured. This document stops at Login.**

**The Authentication design contains 24 screens. Under D-153 they sequence as *later workflows* and are named here only so nobody re-derives the list:**

| Workflow | The design's screens |
|---|---|
| **1 · Login** *(this document)* | ⚡ **AMENDED 2026-08-07 by [D-156](../DECISION_REGISTER.md) ⑤ — three screens became four.** **`02` Sign in · `03` Sign in failed · `15` Authenticating · `17` Unauthorized**, plus the shell, palette and component states, **and every customer-visible state on that path**: validation messages · inline field errors · loading and skeleton states · success confirmations · toasts · focus management · keyboard interaction · the three responsive layouts |
| **2 · Registration** | `01` Welcome · `06` Create account · `07` Verify email |
| **3 · Recovery** | `08` Forgot · `09` Set new password · `10` Success |
| **4 · Invitation** | `13` Accept · `14` Expired · declined · wrong account |
| **5 · Blocked & interrupted** | `04` SSO discovery · `05` Magic link · `11` Locked · `12` Throttled · `16` Auth error · `17` Unauthorized · `18` Session expired |

⛔ **No rows are written for 2–5, and none should be until Login is reviewed.**

### ⚡ 6a · What [D-156](../DECISION_REGISTER.md) ⑤ added, and what it deliberately did not

**[D-156](../DECISION_REGISTER.md): *"do not focus only on the happy path… implement the entire user experience defined by the design—not just the primary screen layout."*** ⛔ **So the three-screen scope above was too narrow, and it is corrected rather than defended** ([D-141](../DECISION_REGISTER.md)).

| Screen | In Workflow 1? | Why |
|---|---|---|
| **`02` Sign in** | ✅ | The primary surface |
| **`03` Sign in — failed** | ✅ | ⛔ **Minus the attempt counter** — see below |
| **`15` Authenticating** | ✅ | **Named steps past 800ms, cancel past 8s.** ⚡ **The capability is the sign-in call itself; nothing new is needed** |
| **`17` Unauthorized** | ✅ **ADDED** | ⚡ **The capability already exists**: [§7](../../CLAUDE.md) requires server-side membership verification on every request, and a non-member gets `404` by design. **D-156 ⑤ names *session-related messages* and *authentication failures*** |
| **`16` Authentication error** | ⛔ | **It quotes an identity provider verbatim — *"Okta rejected the sign-in… user not assigned to this application"*.** **There is no SSO, so there is no provider to quote** |
| **`11` Locked · `12` Too many attempts** | ⛔ | ⚡ **Settled by ⑤'s own parenthetical — *where backed by implemented capability*.** **`rateLimit`, `lockout`, `maxAttempts` and `failedAttempts` return zero across the repository** |
| **`18` Session expired** | ⛔ | **The design calls it *"the only journey that starts inside the product"* and renders it over the current view.** **It needs the App Shell — [D-155](../DECISION_REGISTER.md) priority 5** |

> ⚡ **The distinction ⑥ draws, and it is the one worth holding onto.** **A state whose *data* is missing is built to the design against seeded data that matches the production shape.** ⛔ **A state whose *business rule* is missing is not built at all** — **because simulating a lockout counter simulates a security rule, and ④ forbids exactly that: *"Never simulate or weaken business rules, authentication semantics, authorization."*** **The attempt counter is the second kind. Seeded Companies are the first.**


---

## 7 · ⚠️ Two planning corrections this measurement forces

**① [TASK-483](../BACKLOG.md)'s premise is stale, and it is this office's row.** **It reads: *"There is no authentication layout at all: five `page.tsx` files, each re-stating its own frame."*** ⛔ **`app/(auth)/auth-shell.tsx` exists — 58 lines, exporting `AuthShell` and `AuthLink`, consumed by all five pages, and using semantic tokens throughout.** ⚡ **[C-428](../LANE_COORDINATION.md)'s exact lesson, one week on: a row was written from a directory listing rather than from the file.** ✅ **The row is corrected rather than deleted — the shell exists and is 3 of 12 against its design, so the work is real and the *reason* was wrong.**

**② [TASK-483](../BACKLOG.md) is `BLOCKED` on [C-430](../LANE_COORDINATION.md), and C-430 was closed yesterday by [D-151](../DECISION_REGISTER.md) ①.** ✅ **Released to `READY`, Lane A** — **`frontend/` is `product_surface` in [`modules.toml`](../coordination/modules.toml), so the row has an owner by machine.**

---

## 8 · The measurement that should be taken next, and by whom

⛔ **This office cannot see a rendered screen and says so again rather than once** ([487](487-legacy-ui-migration-status.md) §1). **Everything above is measured from files.**

> ⚡ **The one thing that would make Workflow 1 verifiable rather than reviewable is a screenshot diff against the design's own card — and the design ships at real width, which is what makes that possible.** ⚠️ **[D-153](../DECISION_REGISTER.md) gives QE *"visual regressions (where applicable)"*, and this is where it is applicable.** ⛔ **Not raised as a row: the harness is QE's, and how QE certifies is not this office's to specify.**

# 487 · Legacy UI migration status — how much of the application predates the finalized design

**Lane C · Product Office · 2026-08-07.** **[D-152](../DECISION_REGISTER.md), on the first human UI review.**

> ⛔ **This is not an implementation audit and not a defect report.** **It answers one question: *for every screen that has a surface, is that surface the finalized Signora design, an implementation that predates it, or a mix?***

---

## 0 · The three findings, before the evidence

> ## ⛔ **① Nine of the ten screens that have a surface show no evidence of derivation from the finalized design. Zero are Final UI. Zero are production ready.**
>
> ## ⚡ **② The worst case is `App Shell` — 0 of 29 distinctive phrases — and every other screen renders inside it. The human review saw the shell, which is why the finding generalises.**
>
> ## ✅ **③ And the migration is not a rewrite. The design says so itself: *"v1 is not deprecated; it is the substrate… almost all of it lands through tokens rather than markup."* Eleven of its fourteen corrections are token-level, and the repository already enforces token discipline.**

---

## 1 · ⚠️ What this audit can and cannot measure

**Stated first, because [D-152](../DECISION_REGISTER.md) asks for a *visual* conformance audit and this office cannot see a rendered screen.**

| | |
|---|---|
| ✅ **Measurable here** | **Derivation** — does the implementation contain language, structure and components that exist in exactly one design document? **Route existence. Component inventory. Token state.** |
| ⛔ **Not measurable here** | **Visual conformance.** ⚡ **Only a human looking at the running product can confirm that** — which is what produced [D-152](../DECISION_REGISTER.md) in the first place |

> ⛔ **So `Legacy UI` below means *no measurable evidence of derivation from the finalized design*, never *confirmed wrong on screen*.** ⚡ **The two agreed on the one screen a human has reviewed**, which is why the inference is offered — **and one agreement is not a validated method.**

**Method inherited from [484](484-ui-conformance-and-gap-audit.md) rather than reinvented**: a phrase counts only if it appears in **exactly one** of the twenty-six designs and is 12–44 characters. ⚠️ **[484](484-ui-conformance-and-gap-audit.md) threw away a capitalised-string count first — it scored `CRM Integrations` at 41% on the frequency of *Save* and *Settings*.** **[B-101](../BUGS.md)'s class, and the reason this audit does not report a conformance percentage: there is no honest denominator.**

---

## 2 · ⚡ The classification — every design, measured

**Ten designs have a surface. Fifteen do not.** **13 `page.tsx` routes against 26 designs.**

| Screen | Route | Distinctive phrases in code | Status |
|---|---|---|---|
| **Design System v2** | `components/ui` | **5 files reference the design** | 🟡 **Partially Migrated** — *the only one* |
| **Authentication** | ✅ 5 routes | **4 of 47** | 🔴 **Legacy UI** — ⚡ **human-confirmed** |
| **App Shell** | ✅ layout | **0 of 29** | 🔴 **Legacy UI** — ⛔ **and it is upstream of everything** |
| **Account 360** | ✅ | **0 of 30** | 🔴 **Legacy UI** |
| **Team Management** | ✅ | **0 of 40** | 🔴 **Legacy UI** |
| **Companies** | ✅ | **0** | 🔴 **Legacy UI** |
| **Settings** | ✅ | **0** | 🔴 **Legacy UI** |
| **CRM Integrations** | ✅ | **1** | 🔴 **Legacy UI** |
| **Workspace Setup** | ⚠️ partial | **1** | 🔴 **Legacy UI** — ⚡ **being replaced by [TASK-468](../BACKLOG.md), claimed** |
| **System States** | cross-cutting | **2 of 34** | 🔴 **Legacy UI** |
| **AI Copilot · AI Research · Billing · Design Review · Executive Dashboard · Global Search · Help Center · Notification Center · Onboarding · Opportunity Intelligence · Reports · Security Center · Signal Center · User Profile · Workflow Automation** | ⛔ **none** | — | ⬜ **Missing** *(15)* |

**Customer Reviewed: 1** — Authentication and the shell, by the product owner, **and the review is what found the defect.**
**Production Ready: 0.**

---

## 3 · The five questions [D-152](../DECISION_REGISTER.md) asks

### ① Which screens are still using legacy UI?

**Nine of the ten with a surface** — every one above except `Design System v2`.

### ② Which fully match the finalized design?

> ## ⛔ **None.**

### ③ Which are partially migrated?

**One: `Design System v2` itself**, through [TASK-448](../BACKLOG.md) slices 1–2 and [TASK-478](../BACKLOG.md) slice 3. ⚡ **`Drawer`, `CommandPalette`, `ErrorState`, `Confidence`, a `Badge` `ai` tone, `--radius-xl` and `--color-ai` — the first UI in this repository built *from* the design rather than beside it.**

### ④ Which shared layouts still require migration?

**All of them, and this is the finding that makes the others urgent.**

| Shared layout | File | Evidence |
|---|---|---|
| **App Shell** | `components/shell/app-shell.tsx` | ⛔ **0 of 29 distinctive phrases** |
| **Navigation** | `components/shell/navigation.tsx` | ⛔ **inside App Shell's zero** |
| **Authentication Shell** | `app/(auth)/auth-shell.tsx` | 🔴 **inside Authentication's 4 of 47** |
| **Page & record headers** | ⛔ **no component exists** | **the design names the section; `components/ui` has none** |

> ⛔ **A screen cannot match the approved design while the shell it renders inside does not.** ⚡ **That is why the product owner's review of *one* login screen is evidence about the application rather than about a screen.**

### ⑤ Which missing global components prevent the remaining screens from matching?

**`components/ui` holds thirteen: `badge` `button` `card` `command-palette` `confidence` `dialog` `drawer` `empty-state` `error-state` `input` `select` `skeleton` `table`.**

**The design system names twenty sections. The components absent from the library, and each is named by the design rather than invented here:**

| Missing | Named by the design as | Blocks |
|---|---|---|
| **Page & record header** | its own section | ⛔ **every screen** |
| **Inline-editable table cell** | critique ⑫ — *"reps edit close dates and amounts dozens of times a day"* | Companies · Account 360 · Opportunity Intelligence |
| **The twelve embedded AI patterns** | critique ⑨ — *"AI summary rows in tables, explain buttons on metrics, evidence…"* | AI Copilot · Executive Dashboard · Account 360 |
| **Agent workflow surface** | its own section | Workflow Automation |
| **Charting** | *(see below)* | Executive Dashboard · Reports · Billing · Signal Center |

> ⚠️ **Charting remains an unanswered dependency question, and it is [D-149](../DECISION_REGISTER.md)'s, not new here.** ⛔ **§6 forbids guessing a dependency**, and the first chart-heavy screen still has no route — so it stays a question rather than becoming a row.

---

## 4 · ✅ The correction to the migration model — and it is good news

**[D-152](../DECISION_REGISTER.md) proposes:** *Legacy implementation → Replace UI with finalized design → Validate customer journey → Production ready.*

⚡ **The design disagrees with "replace", in its own words:**

> **"v1 is not deprecated; it is the substrate. Its grid, breakpoints, spacing base, token tiers, status vocabulary and four rule sets are inherited verbatim. What changes is the surface language, and almost all of it lands through tokens rather than markup."**

**Its `Critique of Version 1` is fourteen findings, each naming the v1 decision and the v2 correction. Classified by where each lands:**

| | Findings | Where the work is |
|---|---|---|
| ✅ **Token / CSS only** | **11** — zero radius · flat planes · heavy rules · cool greys · 800-weight type · cramped copy · uppercase · accent-as-alarm · status pills · motion · contrast | **`globals.css` — 78 custom properties, already centralized** |
| ⚠️ **Component work** | **3** — bolted-on AI ⑨ · table chrome ⑪ · no inline editing ⑫ | **`components/ui`, and each is a named component above** |

**The lever is real and already enforced.** **§20c: *"Use design tokens, never literal colours… A theme change must be a token edit"*, held by `frontend/tests/components/design-tokens.test.tsx`.** ⚡ **`globals.css` already cites Design System v2 twice.** ⛔ **A repository that had let literal colours spread would face a rewrite; this one does not.**

> ## **So the path is: migrate the tokens once — every screen moves — then correct three component families, then the shells, then per-screen conformance.**

⚠️ **What this does *not* soften: eleven token findings still leave a screen using the wrong *components*, and nine screens have never been read against their design.** **Tokens make the surface right; they do not make `Team Management` contain the forty things its design specifies.**

---

## 5 · What this changes about sequencing

⛔ **This audit creates no new rows.** **The work it implies is already decomposed** — [TASK-448](../BACKLOG.md) and [TASK-478](../BACKLOG.md) are the Design System v2 slices and both are `IN VALIDATION`. ⚡ **[D-135](../DECISION_REGISTER.md): a finding becomes an owned action item, never an anonymous backlog row — and these already have an owner.**

**The one sequencing consequence, offered as a recommendation rather than taken:**

> ⚠️ **[D-152](../DECISION_REGISTER.md): *"I would not ask Lane A to continue implementing more business screens blindly."*** **Measured against that instruction, `TASK-480`–`TASK-484` are new business and shell surfaces, and they would be built on a shell that is 0 of 29.**
>
> ⛔ **Priority is the product owner's and this office does not reorder it** (§20e). **What is recorded is the cost: a screen built now inherits the legacy shell and is migrated twice.**

**The counter-argument, stated because it is not weak:** ⚡ **the token migration moves every screen at once *including* ones built meanwhile**, so a screen built today on correct *components* is not wasted — it is only its shell and its unread design that would need a second pass.

---

## 5a · ⚠️ One row already claims this work, and the measurement disagrees with it

**[TASK-447](../BACKLOG.md) — *"The App Shell the approved design describes"* — is `IN VALIDATION` with Lane A.** ⛔ **The shell measures 0 of 29 distinctive phrases from `Fortune Signora App Shell.dc.html`.**

> ⚡ **This is [D-152](../DECISION_REGISTER.md)'s point with a row number attached.** **A slice can satisfy every gate — tests, types, imports, a named audit gap closed — and still not be derived from the design whose name is in its title.**

⚠️ **Stated carefully, because the two measure different things.** **The row delivered *structure*: regions, the navigation rail, a structural test.** **This audit measures *derivation by language*, which is a proxy** — **a shell can be structurally right and share no distinctive phrase.** ⛔ **So this is not an assertion that `TASK-447` is wrong; it is an assertion that nothing has checked the question it names.**

| | |
|---|---|
| ⛔ **Not a defect row** | **The work is in flight and the state is Lane A's and QE's, never this office's** (§20e) |
| ✅ **What is asked** | **That QE's validation of [TASK-447](../BACKLOG.md) include design conformance, and that Lane A read the shell design against the implementation before the slice closes** |
| ⚡ **Why it is worth one sentence now** | **The shell is upstream of all sixteen screens.** **If it closes as legacy, every screen built on it inherits a second migration** |

---

## 6 · The lesson worth keeping

⚡ **[D-137](../DECISION_REGISTER.md) §7 already ratified the five product milestones and said this exact thing on 2026-08-06:** *"A screen can be **Implemented** and not **Design Compliant**, and on 2026-08-06 every screen audited was exactly that. Reporting one number for five questions is how that stayed invisible."*

> ⛔ **So the distinction was ratified, [478](478-design-conformance-audit.md) measured it on one screen, [484](484-ui-conformance-and-gap-audit.md) measured it on twenty-five — and the repository still reported those screens as implemented, because nothing downstream of the audits consumed them.**

**A measurement nobody's planning reads is the same as a measurement nobody took.** ⚡ **What made this actionable was a human opening the product**, which is [§20e](../../CLAUDE.md)'s own sentence returning with evidence: *"every defect that has mattered in this project was found by using the product, not by the suite."*

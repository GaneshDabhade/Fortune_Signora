# 498 · Common Platform Audit — does the shared foundation match the finalized design?

**Lane C · Product Office · 2026-08-09.** **[D-218](../DECISION_REGISTER.md), on the product owner's directive.**

> ⛔ **This is not a request to improve the existing implementation.** **It answers one question per component: *does the implementation match the finalized design authority?*** — and where it does not, it classifies rather than patches.

**Scope: the five areas the directive names** — Global Application Shell · Navigation · Shared Layout · Shared UI Components · Common Behaviours — **plus the reuse audit (§4) and the compliance table (§7).**

---

# 0 · What this audit is *not*, and why the boundary matters

**[D-217](../DECISION_REGISTER.md), issued earlier the same day on the same directive text, audited the Application Shell alone and produced seven rows** — `TASK-1439`–`TASK-1445`. **This audit is the remaining four areas, and it does not restate D-217's seven.** They are referenced where a finding depends on them and are otherwise closed.

⚠️ **The directive text arrived headed *"D-215"*. D-215 and D-216 were allocated earlier that day** — D-215 is the ruling that *narrowed* `TASK-1408`, which this audit's §2 finding turns on — **so the ruling is D-218 and [§2 of `CLAUDE.md`](../../CLAUDE.md) forbids renumbering a dated record to tidy the sequence.**

---

# 1 · ⚡ The headline, stated before the evidence because it reverses the directive's expectation

**§4 of the directive anticipates duplicate implementations and asks for every location. There are almost none, and that is a measured result rather than a courtesy.**

| Duplication probe | Files outside `components/ui` |
|---|---|
| Raw `<table>` markup | **0** |
| Raw `role="dialog"` | **0** |
| Inline `animate-pulse` skeletons | **0** |
| Locally defined `Button` · `Card` · `Badge` · `EmptyState` | **0** |
| **Workflow-local `role="tab"`** | ⚠️ **1** — `app/(app)/signals/signal-queue.tsx` |

> ## ✅ **Where a shared component exists, it is being used. Reuse discipline is holding.**
>
> ⛔ **The failure is the opposite shape: the library is incomplete, and four components that exist are mounted by nothing.**

**This changes what the remediation is.** A duplication problem is fixed by consolidation. **An absence problem is fixed by building the missing platform components before twenty more workflows each invent their own** — which is exactly the cost §9 of the directive names, arriving by a different route than expected.

⚠️ **The single `role="tab"` is the leading indicator.** There is no shared `Tabs`; one screen needed tabs and wrote them locally. **That is how the duplication the directive feared actually begins**, and it has begun once.

---

# 2 · Global Application Shell

**Design authority:** 📁 `screens/Fortune Signora App Shell.dc.html` — `navItems` · `topBarSlots` · `landmarks` · `breakpoints` · `Rules`.

## 2.1 Three of five declared regions render

**The frame's own constitution declares five regions.** 📁 [`lib/shell/constitution.ts`](../../frontend/lib/shell/constitution.ts):`SHELL_REGIONS`:

```
environment-banner   ✅ rendered   ShellBanners, app-shell.tsx:79
trial-banner         ✅ rendered   ShellBanners
top-bar              ✅ rendered   app-shell.tsx:113   (contents wrong — TASK-1440)
filter-strip         ⛔ NOT RENDERED
utility-panel        ⛔ NOT RENDERED
```

🔴 **The two absent regions are not merely unbuilt. Other code already depends on them:**

| Depends on the utility panel | Where |
|---|---|
| **Tab order** | 📁 [`lib/shell/rail.ts`](../../frontend/lib/shell/rail.ts):45 — `TAB_ORDER = ['rail', 'filter-strip', 'content', 'utility-panel']` |
| **Surface routing** | 📁 [`lib/shell/scope.ts`](../../frontend/lib/shell/scope.ts):117–126 — `Surface = 'utility-panel' \| 'drawer'`, and the resolver **returns `'utility-panel'` as its default branch** |
| **Shell rule 08** | 📁 *"Context that describes content goes in the utility panel; anything with a Save goes in a drawer"* |
| **A shipped screen** | 📁 `app/(app)/authenticated-shell.tsx`:161 — *"The design puts it in the App Shell's utility rail, which is Workflow 13 and not built; this row may not build that shell"* |

> ⛔ **A tab order that names a region the frame does not render, and a resolver whose default branch returns a surface that does not exist, are Decorative Logic** ([§2](../../CLAUDE.md)) — **implementation that appears to enforce a property whose removal changes nothing.** **This is not "a region we have not got to yet"; it is a contract with no counterpart.**

## 2.2 How the hole was made, and it was made deliberately and correctly

**`TASK-1408` — the Application Shell — is `VERIFIED`, certified and promoted at `e72b6af0`.** ⚡ **Its Status cell says exactly what was excluded:** 📁 ***"The filter strip and the utility panel are out of this row."*** **[D-215](../DECISION_REGISTER.md) narrowed it to release two rows that had been `BLOCKED` for four cycles.**

✅ **That was the right call at the time and this audit does not reverse it.** **The defect is what happened next: the two excluded regions became `TASK-1432` and `TASK-1433`, and both were parked `SEQUENCED` behind a consumer** — *"behind the first module that reads scope"* and *"behind the content its three tabs name"*.

🔴 **So the shell shipped 3/5, the exclusion was recorded honestly, and the remainder was sequenced behind demand that the shell itself is supposed to create.** ⚠️ **Nothing was hidden and nothing was wrong at any single step. The foundation is incomplete anyway** — which is the failure mode §9 of the directive describes.

## 2.3 The seven D-217 rows, unchanged

**Rail (3 entries vs 11) · top bar (1 of 5 design slots) · workspace switcher in the wrong region · `⌘K` bound to the wrong surface · breakpoints at Tailwind's 768/640 vs the design's 1600/1280/1024 · zero skip links · one keyboard shortcut of thirteen.** **Measured in [D-217](../DECISION_REGISTER.md); rows `TASK-1439`–`TASK-1445`.**

---

# 3 · Navigation

| Capability | Design authority | Status | Row |
|---|---|---|---|
| **Route hierarchy** | `/w/:workspace` tree | ⛔ **Missing** | `TASK-1438` |
| **Active navigation state** | `navSpecs` states | ⚠️ **Partial** — states exist, on the wrong entries | `TASK-1439` |
| **Nested navigation** | 2nd level indents 30px, never deeper | ⛔ **Missing** — no sub-entries ship | `TASK-1439` |
| **Deep-link behaviour** | route tree | ⛔ **Missing** | `TASK-1438` |
| **Workspace navigation** | switcher is the rail's first child | ⛔ **Incorrect region** | `TASK-1441` |
| **Back navigation** | `⌘[` `⌘]` | ⛔ **Missing** | `TASK-1445` |
| **Navigation persistence** | collapse per user and device class | ✅ **Fully compliant** — `use-rail-collapse.ts` | — |
| **Keyboard navigation** | `G H` `G F` `G P` `G A` | ⛔ **Missing** | `TASK-1445` |
| **Command palette integration** | shell rule 07 | 🔴 **Built and mounted by nothing** | `TASK-1442` |

**Measured:** `grep` for keyboard bindings across `app`, `components`, `lib` returns **`Escape`×2, `k`, `j`, `Enter`, `Backspace`, and four arrows.** 📁 **The design publishes thirteen shortcuts across three groups. One is implemented** — `[`, rail collapse, at `use-rail-collapse.ts`:80 — **and `k` is bound to account search rather than the palette.**

---

# 4 · Shared Layout

## 4.1 🔴 There is no page header component, and a shell rule governs it

📁 **Design System v2 §08 is an entire section — *"Page & record headers"*.** 📁 **Shell rule 03: *"One primary action per view, and it lives in the page header."***

```
grep -rl "PageHeader|RecordHeader" app components   →   0 files
```

> ⛔ **A shell rule constrains where the primary action lives, and the component it names does not exist.** **Every screen therefore places its own heading and its own primary action**, which is the state from which twenty inconsistent page headers emerge. **This is the highest-leverage absence in the audit** — it is inherited by literally every workflow.

## 4.2 Route-level states

| | Design | Implementation |
|---|---|---|
| **Loading** | specified per surface | 🔴 **0 `loading.tsx` across 26 routes** |
| **Error** | specified per surface | 🔴 **2 of 26 route directories render `ErrorState` or `SystemState`** |
| **Empty** | specified per surface | ⚠️ **7 of 26** |
| **Not found** | System States | ⚠️ **1, at the root** |

> 🔴 **This is [P-A](../DOMAIN_DISCOVERY_REGISTER.md) at platform scale** — *a failed read must never render as an empty result.* **[C-226](../LANE_COORDINATION.md) found it six times on one screen. The measurement above is the same defect across the product**: three and a half times more screens have designed *empty* states than have *error* states, so on most screens a failed read is indistinguishable from no data.

## 4.3 The rest

| Capability | Status |
|---|---|
| **Content region** | ✅ `main`, `app-shell.tsx`:155 |
| **Drawer behaviour** | 🔴 **`drawer.tsx` exists · imported by nothing** |
| **Modal behaviour** | ✅ `dialog.tsx`, 14 importers |
| **Confirmation dialog** | ⚠️ **No distinct component** — `disconnect-dialog.tsx` is one workflow's own |
| **Utility panel** | ⛔ **Missing** — §2.1 |
| **Responsive breakpoints** | ⛔ **Incorrect** — `TASK-1443` |

---

# 5 · Shared UI Components

**30 files in [`components/ui`](../../frontend/components/ui). Usage measured per exported symbol across `app`, `components`, `lib`, excluding the library itself.**

## 5.1 🔴 Built, and mounted by nothing

| Component | Importers | Note |
|---|---|---|
| **`CommandPalette`** | **0** | 📁 shell rule 07 depends on it · [C-259](../LANE_COORDINATION.md) · `TASK-1442` |
| **`Confidence`** | **0** | 📁 AI pattern 03 · [C-266](../LANE_COORDINATION.md) · first caller is `TASK-1427` |
| **`Drawer`** | **0** | 📁 AI pattern 08, the assistant drawer · shell rules 08 and 09 |
| **`CopyableId`** | **0** | — |

⚠️ **Four complete, tested components that no customer can reach.** **Three of them are named by a shell rule or an AI pattern**, so the rule is unenforceable and the pattern unshipped while the code sits in the tree looking done.

## 5.2 ⛔ Named by the design, absent from the library

| Component | Design authority | Consequence |
|---|---|---|
| **Page / record header** | DS v2 §08 | §4.1 — **shell rule 03 governs it** |
| **Tabs** | `tabs` spec; Account 360 | **already reimplemented locally once** |
| **Toast** | DS v2 `toasts` — three kinds | **exists at `components/feedback/toast.tsx`, outside the library** |
| **Avatar** | 📁 *"the avatar is the only circle in the shell"* | top-bar slot 5 |
| **Charts** | DS v2 `chartRamp` — 8 series | **`--c1`…`--c8` absent from `globals.css`; no chart component** |
| **Pagination** | table spec | every collection surface |
| **Filters** | filter strip | §2.1 |
| **Progress indicator** | DS v2 §13 | agent workflows |
| **Tooltip** | 📁 collapsed-rail tooltips, 1.4.13 | `TASK-1444` depends on it |

## 5.3 ✅ Present and genuinely reused

`Button` 36 · `Card` 41 (4 exports) · `EmptyState` 19 · `Input` 19 · `Skeleton` 16 · `Dialog` 14 · `Badge` 14 · `Table` 12 (6 exports) · `Select` 5 · `FieldOriginTag` 4 · `SystemState` 4.

> ✅ **The token layer is exact and is not a finding.** **[D-217](../DECISION_REGISTER.md) measured it**: the design's `#134e76` is `--color-accent`, `#1f7a5c` is `--color-success`, `RAIL_WIDTH` is 232/56 as drawn. **The names differ from the design's `--brand`/`--pos` and the values do not.** ⛔ **Do not "correct" the token names** — §6 of the directive is about implementations contradicting the design, and this one does not.

---

# 6 · Common Behaviours

| Behaviour | Status | Evidence |
|---|---|---|
| **Theme persistence** | ✅ | `localStorage`, 8 files |
| **Workspace persistence** | ✅ | shipped |
| **Panel persistence** | ✅ **rail** · ⛔ **utility panel does not exist** | `use-rail-collapse.ts` |
| **URL persistence** | ⚠️ **6 files use `useSearchParams`** | no shared convention |
| **Filter persistence** | ⛔ **Missing** | no filter strip |
| **Loading behaviour** | 🔴 **Missing at route level** | 0 `loading.tsx` / 26 |
| **Error recovery · retry** | 🔴 **2 of 26 routes** | §4.2 |
| **Route transitions** | ⛔ **Missing** | no announcement, no motion spec applied |
| **Keyboard shortcuts** | 🔴 **1 of 13** | §3 |
| **Focus management** | ⚠️ **Partial** — `.focus()` in 8 files, `tabIndex` in 3 | no shared focus utility |
| **Accessibility** | 🔴 **Missing** — 0 skip links of 3 required | `TASK-1444` |

---

# 7 · The compliance table (directive §7)

**Effort is this office's estimate and is not a commitment** ([§20e](../../CLAUDE.md) — *any progress figure is the lane's estimate and is marked as one*).

| Component | Design authority | Classification | Effort | Downstream workflows affected | Row |
|---|---|---|---|---|---|
| Navigation rail | App Shell `navItems` | 🔴 **Incorrect — rebuild** | M | **all** | `TASK-1439` |
| Top bar | App Shell `topBarSlots` | 🔴 **Incorrect — rebuild** | M | **all** | `TASK-1440` |
| Workspace switcher | App Shell `landmarks` | 🔴 **Incorrect region** | S | all | `TASK-1441` |
| Command palette | shell rule 07 | 🔴 **Built, unmounted** | S | all | `TASK-1442` |
| Breakpoints | App Shell `breakpoints` | 🔴 **Incorrect** | M | all | `TASK-1443` |
| Accessibility contract | App Shell `Rules` | ⛔ **Missing** | M | all | `TASK-1444` |
| Keyboard map | App Shell `shortcutGroups` | ⛔ **Missing** | M | all | `TASK-1445` |
| **Filter strip** | shell region 4 | ⛔ **Missing — declared, unrendered** | M | every collection surface | `TASK-1432` ⏸️ **needs a consumer — [C-1412](../LANE_COORDINATION.md)** |
| **Utility panel** | shell region 5 · rule 08 | ⛔ **Missing — declared, unrendered** | L | Account 360 · Copilot · Reports | `TASK-1433` ⏸️ **needs a consumer — [C-1412](../LANE_COORDINATION.md)** |
| **Page & record header** | DS v2 §08 · rule 03 | ⛔ **Missing** | M | **all** | **`TASK-1446`** |
| **Loading & error states** | DS v2 §13 · System States | 🔴 **Missing — 0/26 and 2/26** | L | **all** | **`TASK-1447`** |
| **Tabs · Avatar · Tooltip** | DS v2 §10 | ⛔ **Missing** | M | Account 360 · shell · all | **`TASK-1448`** |
| **Toast** | DS v2 `toasts` | ⚠️ **Misplaced — outside the library** | S | all | **`TASK-1449`** |
| **Charts + 8-series ramp** | DS v2 `chartRamp` | ⛔ **Missing** | L | Executive Dashboard · Reports | **`TASK-1450`** |
| **Unmounted-component guard** | ⚡ this audit | ⛔ **Missing** | S | prevents recurrence | **`TASK-1451`** |
| Route tree `/w/:workspace` | Authenticated Entry | ⛔ **Missing** | M | all | `TASK-1438` |
| Home compositions | Authenticated Entry | ⛔ **Missing** | L | Home | `TASK-1405` · `TASK-1406` |
| Design tokens | DS v2 §18 | ✅ **Fully compliant** | — | — | — |
| Rail collapse + persistence | App Shell | ✅ **Fully compliant** | — | — | — |
| `Button` `Card` `Table` `Dialog` `Input` `Badge` `EmptyState` `Skeleton` | DS v2 §09–13 | ✅ **Present and reused** | — | — | — |
| Error boundaries per region | shell rule 13 | ✅ **Fully compliant** | — | — | — |

---

# 8 · Work created (directive §8)

**Six new rows, created immediately rather than proposed** — the directive is explicit that gaps become work without a further review. **One coordination item, because one gap is a priority decision rather than an implementation one.**

| Row | Classification |
|---|---|
| **`TASK-1446`** | Page & record header — the component shell rule 03 already governs |
| **`TASK-1447`** | The loading and error states every route owes |
| **`TASK-1448`** | Tabs, Avatar and Tooltip — the three controls the design uses and the library lacks |
| **`TASK-1449`** | Toast joins the shared library and gains the design's three kinds |
| **`TASK-1450`** | Chart primitives and the eight-series ramp |
| **`TASK-1451`** | A guard: a `components/ui` export with no importer fails the suite |

## ⚠️ The two shell regions are NOT released, and the reason is worth stating

**§9 of the directive says the foundation comes first, and my first reading of it was to release `TASK-1432` and `TASK-1433` from `SEQUENCED`. That reading is wrong, and their own rows are what refute it.**

**Both already require a consumer in their Definition of Done:**

| Row | Definition of Done |
|---|---|
| `TASK-1432` | 📁 ***"Setting a chip changes what at least one module renders"*** |
| `TASK-1433` | 📁 ***"at least one tab renders real module content"*** |

⛔ **Releasing them to `READY` would make them claimable while their own Definition of Done is unsatisfiable** — **a lane claiming `TASK-1433` today could not finish it.** ✅ **They are not parked out of caution; they are parked behind a condition their completion genuinely requires**, and each row argues it better than this audit could: 📁 *"a seller who sets the period to Q3 and sees every figure unchanged learns the filter is broken, and that belief is harder to undo than a missing feature."*

🔴 **The real finding is one level up, and it is a scheduling gap rather than an implementation gap:**

> **Nothing in the backlog schedules a module that reads scope, and nothing schedules Insights, Activity or Notes.** **Measured:** `TASK-1432` and `TASK-1433` are **the only rows** that mention either. **So both shell regions are parked behind work that does not exist in the queue at all** — which is indistinguishable, from any instrument, from being parked indefinitely.

⛔ **Which module supplies the first scope consumer, and when, is a priority decision** ([§20e](../../CLAUDE.md) — *a lane never reorders the queue*). ✅ **Raised as [C-1412](../LANE_COORDINATION.md) for the product owner**, with the two candidate consumers named. **This audit does not resolve it and does not re-sequence anything.**

> ⚡ **The separate, smaller defect stands on its own and is fixed by `TASK-1451`:** `TAB_ORDER` and `scope.ts`'s default branch **name a region the frame does not render.** **That is Decorative Logic today, whatever the schedule turns out to be.**

---

# 9 · What this audit did not do

⛔ **It did not compare against the current implementation to decide what is correct** (directive §2) — every classification above cites a design document or a measurement against one.

⛔ **It did not enhance anything.** **Where a component is fundamentally different from the design it is classified `Incorrect — rebuild`**, per §5.

⛔ **It did not audit the twenty-six screen designs individually.** **That is [478](478-design-conformance-audit.md)'s subject and is separate work.** **This audit covers the shared foundation those screens inherit.**

⚠️ **It measured reuse by import graph, not by visual comparison.** **A component can be imported everywhere and still render wrongly** — `navigation.tsx` was, and D-217 found it by reading the design rather than the import count.

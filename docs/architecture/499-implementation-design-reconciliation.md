# 499 · Implementation ↔ finalized design reconciliation

**Lane C · Product Office · 2026-08-09.** **[D-220](../DECISION_REGISTER.md), product owner.**

> ⛔ **Not a design exercise.** **One question per capability: *does the existing implementation implement the finalized design as specified?*** — answered by opening both, never by checking that a similarly named component exists.

---

# 0 · 🔴 This audit's first finding is against its predecessor

**[498](498-common-platform-audit.md) classified `Button`, `Card`, `Table`, `Dialog`, `Badge`, `EmptyState` and `Skeleton` as *"Present and reused — fully compliant"*.** ⛔ **That judgement rested on import counts.**

📁 **[D-220](../DECISION_REGISTER.md) §10: *"A keyword search is not sufficient evidence."*** ⚡ **An import count is a weaker instrument than a keyword search: it measures whether a name is popular, not whether the thing behind it matches anything.**

**Re-tested against Design System v2 §05, §09, §11, §12. Three of the seven were misclassified**, and one of the three has twelve callers.

> ⚠️ **And it cut the other way too.** **I began this pass believing `Button` used `rounded-full` against a design that specifies 8px** — a `grep` for `rounded` returned `rounded-full` from **the loading spinner**. **Opening the file showed `rounded` on the control itself, which is `--radius` at 0.5rem, which is 8px, which is correct.** ⛔ **That would have been a manufactured finding of exactly the class §10 forbids, produced by the same shortcut that caused the original error.**

---

# 1 · Radius — measured value against measured value

📁 **Design System v2 §05 assigns a radius to each surface by name.** **Compared against `app/globals.css` and each component's own class.**

| Surface | Design | Token | Implementation | |
|---|---|---|---|---|
| Button, input, select, nav item | **8px** `--r-md` | `--radius-md: 0.5rem` | `button.tsx` `rounded` → `--radius` **0.5rem** | ✅ |
| Card, menu, popover, toast | **12px** `--r-lg` | `--radius-lg: 0.75rem` | `card.tsx` `rounded-lg` | ✅ |
| Status pill, badge, chip | **6px** `--r-sm` | `--radius-sm: 0.375rem` | `badge.tsx` `rounded-sm` | ✅ |
| Drawer, assistant panel | **16px** `--r-xl` | `--radius-xl: 1rem` | `drawer.tsx` `rounded-xl` | ✅ |
| **Dialog** | **16px** `--r-xl` | — | ⛔ **`dialog.tsx` `rounded-lg` = 12px** | ❌ |
| **Table plane** | **16px** `--r-xl` | — | ⛔ **`table.tsx` has no radius and no plane** | ❌ |
| Avatar, status dot, count badge | **999px** `--r-full` | ⛔ **no `--radius-full` token** | — | ❌ |

✅ **The five-step scale itself is exact — 4 · 6 · 8 · 12 · 16 in both.** ⛔ **Two components apply it wrongly and one step is missing.**

---

# 2 · 🔴 Typography — the scale is not the design's

📁 **Design System v2 §04, `typeRows`.** **Compared against `app/globals.css`:135–147.**

| Design role | Design | Implementation | |
|---|---|---|---|
| **Display** | **40 / 1.05 / 700 / −0.032em** | ⛔ **`--text-display: 2.25rem` = 36px** | ❌ **wrong value** |
| **Title** | **26 / 1.15 / 700 / −0.026em** | ⛔ **no token; nearest `--text-xl` = 20px** | ❌ **absent** |
| **Metric** | **30 / 1.05 / 700 / tabular** | ⛔ **no token, and no tabular-numeral role** | ❌ **absent** |
| Section | 18 / 1.3 / 600 | ✅ `--text-lg: 1.125rem` = 18px | ✅ **different name, same value** |
| Body | 14 / 1.6 / 400 | ✅ `--text-sm: 0.875rem` = 14px | ✅ **different name, same value** |

> 🔴 **This corrects [498](498-common-platform-audit.md) and [D-218](../DECISION_REGISTER.md), which said *"the token layer is exact"*.** ⚠️ **[D-217](../DECISION_REGISTER.md) measured the COLOUR tokens as exact and they are. I generalised that to the whole token layer without testing the type scale, and the type scale does not match.**
>
> ⚡ **Why it is not cosmetic.** **`Title` at 26px is the page header's title** — the component [TASK-1446](../BACKLOG.md) is about to build, which would otherwise be built against a scale missing the exact role it needs. **`Metric` at 30px with tabular numerals is every figure on the Executive Dashboard**, and tabular numerals are what stop a column of currency from jittering.

📁 **Names differ throughout and that is allowed** — §10: *"if the implementation uses a different internal name but faithfully implements the design, do not create a task."* ✅ **`--text-lg` is `Section`; `--text-sm` is `Body`. No task.** ⛔ **`Title` and `Metric` are absent at any name.**

---

# 3 · 🔴 The table is a v1 table

📁 **Design System v2 §11 states four rules. `components/ui/table.tsx` is 6 exports over a bare `<table className="w-full border-collapse text-sm">`.**

| §11 rule | Implementation |
|---|---|
| **Pinned identity** — first column pins with a 24px gradient fade, never a border | ⛔ **absent** |
| **Hover and selection** — hover is the sunken tint; selection adds a 2px brand edge and brand-tint fill, *distinguishable without colour vision* | ⛔ **absent** — `<tr>` carries `border-b` only |
| **Inline editing** — 6px focus ring, optimistic commit on ⏎, undo in the toast for 10s | ⛔ **absent** |
| **AI summary row** — pinned above the data, intelligence tint, dismissible, never counted as a data row | ⛔ **absent** |
| **One rounded plane** — 16px, quiet toolbar, sticky header on a tinted surface | ⛔ **absent** — no plane, no radius, no toolbar |

> ⛔ **Classification C.** 📁 **§11's own critique names what this is**: *"Toolbars, footers and headers all carried 2px rules… the data competed with its own container"*, and *"No inline editing — every correction meant opening a drawer. In practice reps edit close dates and amounts dozens of times a day."*
>
> ⚡ **The implementation is the thing v2 was written to replace.** **Twelve callers, so it is the highest-blast-radius rebuild in this audit** — and [D-220](../DECISION_REGISTER.md) §4 is explicit that twelve callers is not an argument for patching it.

---

# 4 · Card padding — half of it is still v1's

📁 **§05: card padding *"20–24px — was 16px in v1"*.** ⛔ **`card.tsx` is `px-5 py-4` — 20px horizontal and 16px vertical.** ⚠️ **The horizontal value moved to v2 and the vertical one did not**, which is the partial-migration shape §3 of the directive calls B.

---

# 5 · §8 — do the shipped workflows consume the foundation?

✅ **On the primitives that exist, yes, and it was measured in [498 §1](498-common-platform-audit.md)**: zero raw `<table>`, zero raw `role="dialog"`, zero inline skeletons, zero local `Button`/`Card`/`Badge`/`EmptyState` outside the library.

⛔ **On the primitives that do not exist, every workflow has improvised**, which is not a discipline failure — there was nothing to consume.

| Local pattern | Count | Where it goes |
|---|---|---|
| **Routes rendering their own `<h1>`** | **14** | [TASK-1446](../BACKLOG.md)'s adoption sweep |
| **…of which pair a heading with a primary action** — an unshared page header | **5** — `settings`, `settings/organization`, `settings/team`, `signals`, `join/[workspaceId]` | ⚡ **the migration list, measured, so the row inherits it** |
| **Workflow-local `role="tab"`** | **1** — `signals/signal-queue.tsx` | [TASK-1448](../BACKLOG.md) |
| **Toast outside the library** | **1** — `components/feedback/toast.tsx` | [TASK-1449](../BACKLOG.md) |

---

# 6 · The reconciliation matrix (§12)

| Capability | Finalized design | Existing implementation | Classification | Action | Task |
|---|---|---|---|---|---|
| **Application shell — regions** | 5 regions | 3 render | **D Missing** | Implement | `TASK-1432` `TASK-1433` |
| **Navigation rail** | 8 + 2 + 3 entries | 3 unrelated entries | **C Incorrect** | **Rebuild** | `TASK-1439` |
| **Top bar** | 5 slots | 1 of 5, plus 4 non-design controls | **C Incorrect** | **Rebuild** | `TASK-1440` |
| **Page header** | DS v2 §08 | ⛔ **none — 14 local `h1`** | **D Missing** | Implement + migrate | `TASK-1446` |
| **Workspace switcher** | rail's first child, grouped | top-bar `<select>` | **C Incorrect** | **Rebuild** | `TASK-1441` |
| **Utility panel** | 300/360px, docked | absent | **D Missing** | Implement | `TASK-1433` |
| **Filter strip** | 4 chips | absent | **D Missing** | Implement | `TASK-1432` |
| **Loading / error / empty** | DS v2 §13 | 0/26 · 2/26 · 7/26 | **D Missing** | Implement | `TASK-1447` |
| **Dialog** | 16px plane | **12px** | **B Partial** | Correct the token | **`TASK-1453`** |
| **Drawer** | 16px, 420px, non-modal | 16px ✅, **0 importers** | **A Correct, unmounted** | Mount | `TASK-1451` |
| **Toast** | 3 kinds | 1, outside the library | **B Partial** | Rebuild + relocate | `TASK-1449` |
| **Command palette** | shell rule 07 | built, **0 importers** | **A Correct, unmounted** | Mount | `TASK-1442` |
| **Table** | §11 — 4 rules, one plane | ⛔ **bare `<table>`, none of the four** | 🔴 **C Incorrect** | **SCRAP AND REBUILD** | **`TASK-1452`** |
| **Type scale** | display 40 · title 26 · metric 30 tabular | **36 · absent · absent** | **C Incorrect** | Correct + add | **`TASK-1453`** |
| **Radius scale** | 4·6·8·12·16 + full | exact, **`--radius-full` absent** | **B Partial** | Add the step | **`TASK-1453`** |
| **Card** | padding 20–24px | 20px / **16px** | **B Partial** | Correct | **`TASK-1453`** |
| **Colour tokens** | 9 roles | exact ([D-217](../DECISION_REGISTER.md)) | ✅ **A Correct** | **Keep** | — |
| **Button** | 8px, variants | 8px ✅ | ✅ **A Correct** | **Keep** | — |
| **Badge** | 6px pill | 6px ✅ | ✅ **A Correct** | **Keep** | — |
| **EmptyState · Skeleton · SystemState** | §13 | present, reused | ✅ **A Correct** | **Keep** | — |
| **Rail collapse + persistence** | 232/56, per device class | exact | ✅ **A Correct** | **Keep** | — |
| **Region error boundaries** | shell rule 13 | satisfied | ✅ **A Correct** | **Keep** | — |
| **Charts** | 8-series ramp | absent | **D Missing** | Implement | `TASK-1450` |
| **Tabs · Avatar · Tooltip** | §10 | absent; 1 local tab | **D Missing + E Duplicate** | Implement + migrate | `TASK-1448` |
| **Breakpoints** | 1600/1280/1024 | 768/640 | **C Incorrect** | **Rebuild** | `TASK-1443` |
| **Accessibility** | 9 rules | 0 skip links | **D Missing** | Implement | `TASK-1444` |
| **Keyboard map** | 13 shortcuts | 1 | **D Missing** | Implement | `TASK-1445` |

**E — Duplicate:** ⚡ **only one genuine instance in the repository** — the local `role="tab"` in `signal-queue.tsx`. **Authoritative implementation is the shared `Tabs` [TASK-1448](../BACKLOG.md) builds; migration is in that row's Definition of Done.**

---

# 7 · §14 — the nine questions, answered

**A · Have you actually audited the existing implementation against the finalized design documents?**
✅ **Yes, for the capabilities above** — Design System v2 §04, §05, §09, §11, §12, §13 and the App Shell document, opened and compared against `globals.css`, `tailwind.config.ts` and each component file. ⛔ **Not exhaustively across all 27 screens; this covers the shared foundation, which is §7's and §13's scope.**

**B · Which existing implementations are already fully compliant?**
**Colour tokens · the radius scale itself · `Button` · `Badge` · `Card` radius · `Drawer` · `EmptyState` · `Skeleton` · `SystemState` · region error boundaries · rail collapse and its persistence.** ⛔ **Do not touch these.**

**C · Which are based on the older design and must be scrapped and rebuilt?**
🔴 **`Table`** — none of §11's four rules ([TASK-1452](../BACKLOG.md)). **The navigation rail, the top bar and the workspace switcher** ([D-217](../DECISION_REGISTER.md)). **The type scale** ([TASK-1453](../BACKLOG.md)). **The breakpoints.**

**D · Which required capabilities are missing completely?**
**Page header · utility panel · filter strip · route loading and error states · charts and the ramp · Tabs, Avatar, Tooltip · the keyboard map · the accessibility contract · `--radius-full`.**

**E · Which implementations are duplicates?**
**One:** `role="tab"` in `signal-queue.tsx`. ⚡ **Toast is misplaced rather than duplicated — there is one of it.**

**F · Have you created an actual implementation task for every non-compliant or missing capability?**
✅ **Yes.** **Eight rows from [D-218](../DECISION_REGISTER.md)/[D-217](../DECISION_REGISTER.md) already existed; two are new here — [TASK-1452](../BACKLOG.md) and [TASK-1453](../BACKLOG.md).** ⛔ **Nothing in this document is left as an observation.**

**G · Have those tasks been assigned to the correct implementation owner?**
✅ **All to Lane A via `product_surface` in [`modules.toml`](../coordination/modules.toml)**, in Lane A's queue, published to `origin/coordination`. ⛔ **Product Office retains none of them.**

**H · Any already-shipped workflows that must be reworked?**
✅ **Yes, and the list is measured, not estimated: 14 routes render their own `<h1>`, 5 of them pairing it with a primary action.** ⚡ **Carried by [TASK-1446](../BACKLOG.md)'s adoption sweep rather than by a separate migration row, because the migration is only definable once the shared header exists.**

**I · Anything genuinely ambiguous requiring clarification?**
⛔ **No.** 📁 **Per §14, this office therefore proceeds to implementation and does not open a design exercise.** ⚠️ **One pre-existing item stays open and is not re-raised here: [C-306](../LANE_COORDINATION.md), whether the fourteen M12.3 product-review findings are inputs to the rail rebuild or an argument to amend the design.** ✅ **[D-217](../DECISION_REGISTER.md) §6 already sets the default meanwhile — the design wins — so nothing is blocked on it.**

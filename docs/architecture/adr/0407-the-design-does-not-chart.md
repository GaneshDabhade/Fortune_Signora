# ADR-0407 · No charting library — the design barely charts

**Status: PROPOSED.** **Drafted by Lane C, 2026-08-07, on [D-167](../../DECISION_REGISTER.md) §3.** ⛔ **A draft is a recommendation, never a ratification** (§20e) — **the product owner ratifies.**

> ⚡ **[D-167](../../DECISION_REGISTER.md) §2 asked for the design to be checked *before* a library was recommended: *"Do not assume a library simply because it is popular."*** **It was checked, and the answer inverts the question.**

---

## The recommendation, first

> ## ⛔ **Introduce no charting library.**
>
> ## ✅ **Build two purpose-built components in `components/ui`, as inline SVG reading design tokens — the same way the design itself draws them.**

---

## 1 · ⚡ The measurement that decides it

**Five screens have been described as *chart-heavy* since [D-149](../../DECISION_REGISTER.md): Executive Dashboard · Reports · Opportunity Intelligence · Signal Center · Account 360.** **Measured across all five in the snapshot** ([D-138](../../DECISION_REGISTER.md)):

| Screen | `<svg>` | **Icons** *(≤28px)* | **Data visualizations** | Library references |
|---|---|---|---|---|
| **Executive Dashboard** | 13 | **12** | **1** — `viewBox="0 0 760 220"` | **0** |
| **Account 360** | 9 | **8** | **1** — `viewBox="0 0 340 210"` | **0** |
| **Opportunity Intelligence** | 5 | **5** | ⛔ **0** | **0** |
| **Signal Center** | 3 | **3** | ⛔ **0** | **0** |
| **Reports** | 1 | **1** | ⛔ **0** | **0** |

> ## ⛔ **29 SVGs. 27 are icons. Two are data visualizations. Zero `<canvas>`. Zero references to Recharts, Chart.js, D3, visx, nivo, ECharts, Plotly, Victory or ApexCharts, in any of the twenty-six designs.**

⚠️ **One near-miss worth recording, because it is the [B-101](../../BUGS.md) family.** **A grep for `d3` returns a hit on the Executive Dashboard — and it is `d3a`, three characters inside a hex colour.** ⛔ **A naive search would have reported that the design uses D3.**

---

## 2 · What the two actually are

**Neither is a chart in the sense a library serves.**

| | **Executive Dashboard** | **Account 360** |
|---|---|---|
| **Canvas** | `760 × 220` | `340 × 210` |
| **Marks** | **5 `line` · 3 `rect` · 3 `text` · 2 `g`** — **13 total** | **7 `line` · 5 `circle` · 7 `text` · 1 `g`** — **20 total** |
| **Source** | **1,309 characters of hand-authored SVG** | **2,122 characters** |
| **What it is** | **A small column figure with gridlines and labels** | ⚡ **Labelled *"Relationship graph"* — a node-link diagram of the buying committee** |

> ## ⛔ **The second one is not a chart at all.** ⚡ **No charting library draws a relationship graph, so a library adopted for "the charts" would cover *one* figure of thirteen marks and leave the harder one untouched.**

---

## 3 · Why this is the design being coherent rather than incomplete

**Design System v2's thesis is *Quiet Premium*, and its `Critique of Version 1` is fourteen findings about restraint** — flat planes, heavy rules, 800-weight type, accent-as-alarm. ⚡ **A dashboard built from that thesis presents numbers as *type and layout*, not as a wall of plotted area.**

**The Executive Dashboard bears that out**: its metric sections are cards, figures and comparisons, with **one** small column figure among them. ⛔ **The screen is not under-specified; it simply does not chart much.**

---

## 4 · ⚠️ Evaluated against [D-167](../../DECISION_REGISTER.md) §3's own seven criteria

**And the recommendation wins on the criterion the ruling puts first, not on effort.**

| Criterion | A library | **Two components** |
|---|---|---|
| ⚡ **Visual fidelity** | ⛔ **Every library ships its own visual language** — default palette, tick style, tooltip chrome, legend shape — **and matching Signora then means overriding it.** ⚠️ **[D-161](../../DECISION_REGISTER.md) forbids exactly that direction: the design wins, and a screen must not fight its foundation** | ✅ **Tokens, directly. There is nothing to override** |
| **Accessibility** | ⚠️ **Varies, and is the most-reported weakness of every option** | ✅ **`role`, `aria-label` and a text alternative are ours to write** |
| **Performance** | ⛔ **A runtime for two figures** | ✅ **~30 DOM nodes total** |
| **Customization** | ✅ **Broad, and the wrong axis** — the need is fidelity to one design, not breadth | ✅ **Complete by construction** |
| **Responsiveness** | ⚠️ **Container queries or a resize observer** | ✅ **The design already solves it: `style="width:100%;height:auto"` on a `viewBox`** |
| ⚠️ **Long-term maintainability** | ⚠️ **A dependency, its major versions, its React-version coupling and its own breaking changes** | ⚠️ **Ours to maintain — and it is ~3,400 characters of SVG the design has already authored** |
| ⚡ **Consistency with the Design System** | ⛔ **A second visual language inside the product**, which is [D-154](../../DECISION_REGISTER.md)'s prohibition word for word | ✅ **One** |

---

## 5 · What this unblocks, and what it does not

✅ **[D-149](../../DECISION_REGISTER.md) closes.** **Workflows 19 (Executive Dashboard) and 22 (Reports) were marked blocked on charting in [`workflows.toml`](../../coordination/workflows.toml); neither is.** ⚡ **Reports has *no* data visualization at all** — its blocker was inherited from an assumption, never measured.

⛔ **This ADR decides nothing about the *data*.** **The metrics those screens present are a separate question and belong with [D-167](../../DECISION_REGISTER.md) §4**: seeded values through the production contract, so the UI cannot tell a seeded metric from a computed one.

⚠️ **And it is revisitable on evidence rather than permanently.** **If a later finalized design introduces a genuinely chart-heavy screen — a time series with brushing, a stacked area with a legend — this ADR is superseded by a new one.** ⛔ **What it refuses is adopting a dependency *ahead* of that evidence** (§6, *do not add abstractions for hypothetical future needs*).

---

## 6 · The two components, named so they are not invented twice

| | |
|---|---|
| **`MetricFigure`** | **The Executive Dashboard's column figure.** **Lines, rects, labels, tokens** |
| **`RelationshipGraph`** | **Account 360's buying-committee node-link diagram.** ⚡ **The harder of the two, and the one no library would have supplied** |

⛔ **Both belong in `components/ui` with their tokens and their tests** (§20c) — **never page-local.**

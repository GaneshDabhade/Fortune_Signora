# ADR-0407 · The charting library — visx

**Status: ACCEPTED — product owner, 2026-08-07, [D-168](../../DECISION_REGISTER.md) §1.** ⚡ ***"I approve the direction of preferring visx."*** **Approval was conditional on three re-verifications; all three are recorded in [§0](#0--the-three-re-verifications-d-168-1-required) below and all three hold.**

**Drafted by Lane C, 2026-08-07, on [D-167](../../DECISION_REGISTER.md) §3; revised the same day when the product owner overruled its first recommendation.**

---

## 0 · The three re-verifications [D-168](../../DECISION_REGISTER.md) §1 required

| Asked | Measured | |
|---|---|---|
| **Does any finalized design specify a different charting technology?** | ⛔ **No.** **All 26 screen documents *and* `design-system/styles.css` searched for fourteen names — Recharts · Chart.js · D3 · visx · nivo · ECharts · Plotly · Victory · ApexCharts · Highcharts · amCharts · Observable Plot · Vega.** **Zero hits.** | ✅ |
| **Does an existing dependency already satisfy it?** | ⛔ **No.** **33 dependencies; the only one adjacent to drawing is `lucide-react@^0.468.0`, which is an icon set.** **No `d3`, no SVG toolkit, nothing that plots** | ✅ |
| **Is visx still the best match on the six criteria?** | ✅ **Yes, and the deciding one is unchanged**: `@visx/network` renders the *Relationship graph* Account 360 specifies, and **Recharts has no node-link primitive at all.** ⚡ **On Design-System fit it also wins by construction rather than by effort — visx is unstyled, so tokens apply with nothing to override** | ✅ |

⚠️ **One thing the re-verification changed: nothing.** ⛔ **Recorded because a verification that never overturns anything is one nobody will run again** — **the searches, the file counts and the dependency list are above so the next reader can re-run them rather than trust this line.**

---


> ⚠️ **This ADR's first version recommended *no charting library*. The product owner overruled it: *"use either visx or Recharts."*** ⛔ **The earlier recommendation is recorded in [§4](#4--what-this-adr-first-recommended-and-why-it-was-overruled) rather than deleted** (§2, *a record of what was true then is dated, not rewritten*). ✅ **The measurement that produced it stands and is what decides between the two.**

---

## The decision

> ## ✅ **visx** — `@visx/scale` · `@visx/shape` · `@visx/group` · `@visx/axis` · `@visx/text` · **`@visx/network`**
>
> ## ⛔ **Not Recharts, and the reason is one of the two figures the design actually contains.**

---

## 1 · ⚡ What the design actually needs — measured, not assumed

**Across the five screens called *chart-heavy*: 29 `<svg>` elements, 27 of them icons ≤28px, and exactly two data visualizations.**

| | **Executive Dashboard** | **Account 360** |
|---|---|---|
| **Canvas** | `760 × 220` | `340 × 210` |
| **Marks** | **5 `line` · 3 `rect` · 3 `text` · 2 `g`** — 13 | **7 `line` · 5 `circle` · 7 `text` · 1 `g`** — 20 |
| **What it is** | **A column figure with gridlines and labels** | ⚡ **Labelled *"Relationship graph"* — a node-link diagram of the buying committee** |

⛔ **Opportunity Intelligence, Signal Center and Reports have *zero*.**

---

## 2 · ✅ Why visx, and it turns on the second figure

| | **visx** | **Recharts** |
|---|---|---|
| ⚡ **The relationship graph** | ✅ **`@visx/network` is a node-link renderer.** **This is the whole argument** | ⛔ **No node-link primitive exists.** **Recharts composes *charts* — line, bar, area, pie, radar, scatter — and a buying-committee graph is none of them.** ⚠️ **It would have to be hand-drawn beside the library, which is the worst of both** |
| ⚡ **Visual fidelity** — [D-167](../../DECISION_REGISTER.md) §3's first criterion | ✅ **Unstyled by design.** **You render the SVG elements and pass your own `className`, so `--color-brand` and `--ink-3` apply directly.** ⛔ **Nothing to override** | ⚠️ **Ships its own chrome** — default palette, tick style, tooltip, legend — **and matching Signora means overriding it.** ⚡ **That is the direction [D-161](../../DECISION_REGISTER.md) forbids: the screen must not fight its foundation** |
| **Consistency with the Design System** | ✅ **One visual language** | ⚠️ **Two, until every default is overridden** |
| **Accessibility** | ✅ **You own every element, so `role`, `aria-label` and a text alternative are yours to write** | ⚠️ **Partially generated; you work with what it emits** |
| **Bundle** | ✅ **Per-package.** **Install the five or six needed and nothing else** | ⚠️ **One larger package for one 13-mark figure** |
| **Responsiveness** | ✅ **`@visx/responsive`, or the design's own `width:100%; height:auto` on a `viewBox`** | ✅ **`ResponsiveContainer`** |
| ⚠️ **Cost, stated honestly** | ⛔ **More code for the plain column figure** — scale, axis and bars are composed by hand where Recharts is roughly ten lines | ✅ **Faster for that one figure** |

> ## ⚡ **The asymmetry decides it. The design has *one* column figure — the case Recharts wins — and *one* relationship graph, which Recharts cannot draw at all.**

⛔ **And the second reason is the one that outlives this screen**: **visx is the option that does not import a second visual language into a product whose entire migration is about having exactly one.**

---

## 3 · ⚠️ What Lane A must verify before installing

⛔ **This office has no `node_modules` and did not open either package.** **[D-137](../../DECISION_REGISTER.md): *accessible is a claim to be tested, never assumed in either direction*.**

**Measured from `package.json`: React `^19.0.0`, Next `^15.1.0`, TypeScript `^5.7.0`, Tailwind `^3.4.17`. Neither library is present, and no `d3` package is either.**

| | |
|---|---|
| ⚠️ **React 19 peer dependencies** | **Verify each `@visx/*` package resolves cleanly against React 19 before committing the install.** ⛔ **If one does not, that is a finding to raise, never a `--force`** |
| ✅ **Install only what is used** | **`@visx/scale` `@visx/shape` `@visx/group` `@visx/axis` `@visx/text` `@visx/network`.** ⛔ **Never the `@visx/visx` umbrella** — it pulls every package for two figures |
| 🔴 **Change Budget** | **A new dependency is 🔴 — product owner plus ADR** (§20e). ✅ **This ADR is that ADR, and [D-167](../../DECISION_REGISTER.md) §3 is the approval; ratification completes it** |

---

## 4 · What this ADR first recommended, and why it was overruled

**The first version recommended *no library*: two purpose-built components, inline SVG on tokens, on the grounds that 29 SVGs across five screens are 27 icons and two figures totalling ~3,400 characters the design had already authored.**

⛔ **The product owner overruled it, and the ruling is theirs to make** — **technology selection is a 🔴 decision and never a lane's** (§20e).

⚡ **Recorded because the reasoning still does work**: it is what sized the need, and **sizing the need is what picks visx over Recharts.** ⚠️ **A repository that deleted the superseded recommendation would keep the conclusion and lose the argument.**

---

## 5 · Scope, and what this does not decide

✅ **[D-149](../../DECISION_REGISTER.md) closes.** **Workflows 19 and 22 no longer carry a charting blocker** — ⚡ **and Reports never needed one, having no data visualization at all.**

⛔ **This decides nothing about the *data*.** **The metrics those screens present are [D-167](../../DECISION_REGISTER.md) §4's question**: seeded values arriving through the production contract, **so the UI cannot tell a seeded metric from a computed one.**

⛔ **And nothing is built yet.** **Both figures still belong in `components/ui` with their tokens and their tests** (§20c) — **`MetricFigure` and `RelationshipGraph`, composed *from* visx, never page-local.**

'use client';

/**
 * **`/reports`** — [TASK-1417](../../../../docs/BACKLOG.md), against 📁
 * `Fortune Signora Reports.dc.html`.
 *
 * ## 🔴 What this screen deliberately does NOT render, and why that is the rule
 *
 * 📁 **The design's screen is a Q3 board pack**: *"$42.8M commit"*, *"−$2.4M
 * vs. Friday"*, *"3,104 opportunities"*, three named deals that moved.
 * ⛔ **Every one of those is a figure from a query engine that does not
 * exist.**
 *
 * 🔴 **[§20c](../../../../CLAUDE.md) is explicit about what to do here**:
 * ***"Never introduce mock business data. Screens without a shipped module
 * behind them ship a designed empty state."*** ⚡ **So the builder is an empty
 * state rather than a board pack with invented numbers** — **a screen showing
 * a plausible $42.8M would be indistinguishable from a working report tool,
 * and somebody would eventually take a figure from it into a meeting.**
 *
 * ## ✅ What IS true today, and it is not nothing
 *
 * 📁 **The chart library is finalized product copy about what Signora draws**
 * — **eight types, each with the shape it suits** — ⛔ **and it contains no
 * customer data at all.** ⚡ **It is the part of this screen that is honest
 * today**, and it answers the question a buyer actually asks first: *what can
 * this thing show me, and will it pick the right one?*
 *
 * ## ⛔ Reports is NOT added to the rail by this row, and that is deliberate
 *
 * 📁 [`navigation.tsx`](../../../components/shell/navigation.tsx) says the
 * entry *"arrives as its route does"* — ⚠️ **but the same file records what
 * that cost last time**: ***"at M12.3, three of six said `coming soon` on the
 * screen a customer sees first."*** ⛔ **A rail entry leading to an empty state
 * is that defect again**, so the line is added when the builder can build.
 */

import { BarChart3 } from 'lucide-react';

import { CHART_TYPES, CHART_USE } from '@/lib/reports/chart-picker';
import { EmptyState, PageHeader } from '@/components/ui';

/**
 * 📁 **The design's own sentence under the chart library**, verbatim, because
 * it is the product's claim rather than a description of one: ***"The picker
 * recommends a type from the shape of the data and explains why. No doughnuts,
 * no dual axes, no 3D."***
 */
const PICKER_RULE =
  'The picker recommends a type from the shape of your data and explains why. No doughnuts, no dual axes, no 3D.';

export function ReportsScreen() {
  return (
    <div className="mx-auto w-full max-w-5xl">
      <PageHeader
        title="Reports"
        // 📁 The design's subtitle, and it is the architecture stated as a
        // promise: one definition, three renderings.
        description="Built once, read three ways — screen, presentation and board pack."
      />

      <section aria-labelledby="reports-builder" className="mb-8">
        <h2 id="reports-builder" className="mb-3 text-base font-semibold text-content">
          Your reports
        </h2>
        <EmptyState
          icon={BarChart3}
          title="No reports yet"
          /**
           * ⛔ **Names the one thing that is missing, in the customer's words**
           * ([ADR-0034](../../../../docs/architecture/adr/0034-ubiquitous-language.md))
           * — ⚡ **not *"the query engine is unbuilt"***, which is a sentence
           * about this repository rather than about their work.
           *
           * 📁 **The design's own rule is what makes the absence explicable**:
           * *"every block inherits this"* — **a report is one question first,
           * and blocks second.** ⛔ **An empty state that only reported
           * emptiness would leave somebody with no idea what a report even is
           * here.**
           */
          description="A report starts with one question — a period, a region, a segment — and every block on it inherits that question. Signora cannot answer one across your pipeline yet, so there is nothing to build a report from today."
        />
      </section>

      <section aria-labelledby="reports-charts">
        <h2 id="reports-charts" className="mb-1 text-base font-semibold text-content">
          Chart library
        </h2>
        <p className="mb-4 max-w-2xl text-sm leading-6 text-content-muted">{PICKER_RULE}</p>

        {/* ⚡ **A list, not a grid of cards** — 📁 the design pairs each name
            with the shape it suits, and the pairing is the content. A card
            layout would put the two on separate lines at the width where it
            matters most. */}
        <ul className="grid grid-cols-1 gap-px overflow-hidden rounded-xl border border-border bg-border phone:grid-cols-2">
          {CHART_TYPES.map((type) => (
            <li key={type} className="bg-surface px-4 py-3">
              <p className="text-sm font-semibold capitalize text-content">{type}</p>
              <p className="mt-0.5 text-sm text-content-muted">{CHART_USE[type]}</p>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

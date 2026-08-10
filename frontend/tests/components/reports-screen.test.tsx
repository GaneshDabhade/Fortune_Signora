/**
 * **What `/reports` may and may not put on screen** —
 * [TASK-1417](../../../docs/BACKLOG.md).
 *
 * 🔴 **The first block is the one that matters.** ⛔ **[§20c](../../../CLAUDE.md):
 * *"Never introduce mock business data."*** ⚠️ **This screen's design is full
 * of it** — *"$42.8M"*, *"−$2.4M vs. Friday"*, *"3,104 opportunities"*,
 * *"Vantage renewal"* — **and a screen showing those before a query engine
 * exists would be indistinguishable from a working report tool.**
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { ReportsScreen } from '@/app/(app)/reports/reports-screen';

describe('🔴 §20c — no figure on this screen came from nowhere', () => {
  it('⛔ renders NONE of the design’s illustrative figures', () => {
    render(<ReportsScreen />);

    // ⚡ **Named literally rather than by a pattern**, so the assertion says
    // which numbers it is refusing. 📁 Every one is from the design's own
    // mock, so a person reading this test can check it against the file.
    for (const invented of [
      '$42.8M',
      '−$2.4M',
      '3,104',
      '3.1×',
      'Vantage renewal',
      'Ashgrove platform',
      'Brightwater services',
      'Q3 board pack — EMEA',
    ]) {
      expect(screen.queryByText(invented, { exact: false }), invented).toBeNull();
    }
  });

  it('⚡ ships a DESIGNED empty state rather than an empty screen', () => {
    // 📁 §20c: *"Screens without a shipped module behind them ship a designed
    // empty state"* — and `EmptyState` requires a description for the reason
    // this asserts one: emptiness alone leaves somebody with no next step.
    render(<ReportsScreen />);

    expect(screen.getByText('No reports yet')).toBeVisible();
    expect(screen.getByText(/every block on it inherits that question/i)).toBeVisible();
  });

  it("⛔ the empty state speaks the customer's language, not this repository's", () => {
    /**
     * 📁 [ADR-0034](../../../docs/architecture/adr/0034-ubiquitous-language.md):
     * **the translation lives at the frontend edge.** ⚠️ *"the query engine is
     * unbuilt"* is a true sentence about this repository and a useless one
     * about somebody's quarter.
     */
    render(<ReportsScreen />);

    const body = document.body.textContent ?? '';
    for (const ours of ['query engine', 'workspace', 'module', 'endpoint', 'backend', 'API']) {
      expect(body.toLowerCase()).not.toContain(ours.toLowerCase());
    }
  });
});

describe('📁 the header states the architecture as a promise', () => {
  it('carries the design’s title and its subtitle', () => {
    render(<ReportsScreen />);

    expect(screen.getByRole('heading', { level: 1, name: 'Reports' })).toBeVisible();
    expect(screen.getByText(/built once, read three ways/i)).toBeVisible();
  });
});

describe("✅ the chart library is the half that IS true today", () => {
  it('lists the design’s eight types, each with the shape it suits', () => {
    render(<ReportsScreen />);

    for (const [type, use] of [
      ['line', 'A measure over time, one or two series'],
      ['bar', 'Comparison across categories'],
      ['waterfall', 'Signed contributions to one total'],
      ['funnel', 'Conversion through fixed stages'],
      ['cohort', 'Two dimensions, one density'],
      ['distribution', 'Where deals cluster, and the tail'],
      ['pace', 'Actual against required, same axes'],
      ['table', 'When the numbers are the point'],
    ] as const) {
      expect(screen.getByText(type), type).toBeVisible();
      expect(screen.getByText(use), use).toBeVisible();
    }
  });

  it('⛔ states the three the product refuses, because refusing them is a claim', () => {
    // 📁 *"No doughnuts, no dual axes, no 3D"* — the design says it out loud,
    // so the screen does too rather than leaving it as an absence.
    render(<ReportsScreen />);

    expect(screen.getByText(/no doughnuts, no dual axes, no 3d/i)).toBeVisible();
  });

  it('gives each region a heading, so the screen has an outline', () => {
    // ♿ A page whose sections are unlabelled is one a screen-reader user
    // cannot skim, and this screen has two distinct things on it.
    render(<ReportsScreen />);

    expect(screen.getByRole('heading', { level: 2, name: 'Your reports' })).toBeVisible();
    expect(screen.getByRole('heading', { level: 2, name: 'Chart library' })).toBeVisible();
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1);
  });
});

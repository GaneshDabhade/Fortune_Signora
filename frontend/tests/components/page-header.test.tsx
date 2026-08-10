import { render, screen } from '@testing-library/react';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

import { PageHeader, RecordHeader } from '@/components/ui';
import { SHELL_RULES } from '@/lib/shell/constitution';

/**
 * **The page and record headers** — [TASK-1446](../../../docs/BACKLOG.md),
 * against 📁 Design System v2 §08.
 *
 * ⛔ **The point of this row is that shell rule 03 stops being aspirational.**
 * 📁 `lib/shell/constitution.ts` exported *"one primary action per view, and it
 * lives in the page header"* as code **while no page header existed** — a rule
 * naming a place the product did not have.
 */

describe('🔴 shell rule 03 becomes assertable', () => {
  it('⚡ the rule is still the one this component answers to', () => {
    /**
     * ⛔ **Read from the constitution, not restated here.** ⚡ **If the rule is
     * reworded or removed, this fails** rather than going on asserting against
     * a copy — 📁 [D-137](../../../docs/DECISION_REGISTER.md): *"the copy is
     * always the one somebody reads."*
     */
    expect(SHELL_RULES.some((rule) => /one primary action per view/i.test(rule))).toBe(true);
    expect(SHELL_RULES.some((rule) => /page header/i.test(rule))).toBe(true);
  });

  it('✅ exactly one primary action is rendered, and it is marked', () => {
    const { container } = render(
      <PageHeader
        title="Your business"
        primaryAction={<button type="button">Change this</button>}
        secondaryActions={<button type="button">Export</button>}
      />,
    );
    expect(container.querySelectorAll('[data-primary-action]')).toHaveLength(1);
  });

  it('⛔ a second primary action is unrepresentable, not merely discouraged', () => {
    /**
     * 📁 [§2](../../../CLAUDE.md) — *prefer a violation that is
     * unrepresentable over one that is discouraged.* ⚡ **`primaryAction` is
     * one slot, so a second does not fail review — it fails to type-check**,
     * and the assertion that carries that is on the TYPE rather than the DOM.
     *
     * ⛔ **A runtime test cannot construct the violation**, so this reads the
     * source: `ReactNode`, never `ReactNode[]`. **A test that could not fail
     * would be exactly the Decorative Logic this row is replacing.**
     */
    const source = readFileSync(
      join(process.cwd(), 'components/ui/page-header.tsx'),
      'utf8',
    );
    expect(source).toMatch(/primaryAction\?: ReactNode;/);
    expect(source).not.toMatch(/primaryAction\?: ReactNode\[\]/);
    expect(source).not.toMatch(/primaryActions/);
  });

  it('✅ a screen with no primary action is not made to invent one', () => {
    // ⚡ 📁 The attention list has none. **`primaryAction` is optional so the
    // absence is expressible** — a required slot would produce a button whose
    // only reason to exist is the header's shape.
    const { container } = render(<PageHeader title="Attention" />);
    expect(container.querySelectorAll('[data-primary-action]')).toHaveLength(0);
  });
});

describe('📁 §08 — the page header', () => {
  it('✅ the title is the route\'s h1, at the design\'s Title role', () => {
    render(<PageHeader title="Your business" />);
    const heading = screen.getByRole('heading', { level: 1, name: 'Your business' });
    // ⚡ `text-title` is 26 / 1.15 / 700 / −0.026em — all four numbers, which
    // is why it is a tuple in the config. TASK-1453 added the token.
    expect(heading).toHaveClass('text-title');
  });

  it('✅ eyebrow and description are optional and render when given', () => {
    const { rerender } = render(<PageHeader title="Accounts" />);
    expect(screen.queryByText('Trail')).toBeNull();
    expect(screen.queryByText('A sentence')).toBeNull();

    rerender(
      <PageHeader title="Accounts" eyebrow={<span>Trail</span>} description="A sentence" />,
    );
    expect(screen.getByText('Trail')).toBeInTheDocument();
    expect(screen.getByText('A sentence')).toBeInTheDocument();
  });

  it('⛔ secondary actions render BEFORE the primary, which is the design\'s order', () => {
    /**
     * 📁 §08 renders `Export` — outlined — before `Log activity` — brand fill.
     * ⚡ **Asserted as document order**, because that is what a person scanning
     * left to right actually perceives.
     */
    const { container } = render(
      <PageHeader
        title="Vantage"
        secondaryActions={<button type="button">Export</button>}
        primaryAction={<button type="button">Log activity</button>}
      />,
    );
    const buttons = [...container.querySelectorAll('button')].map((b) => b.textContent);
    expect(buttons).toEqual(['Export', 'Log activity']);
  });
});

describe('📁 §08 — the record header', () => {
  const facts = [
    { label: 'Open ACV', value: '$1.24M' },
    { label: 'Signora score', value: '38' },
  ];

  it('✅ identity, status, facts and the health line all render', () => {
    render(
      <RecordHeader
        title="Vantage Logistics"
        initials="VL"
        status={<span>At risk</span>}
        facts={facts}
        health={<span>Score fell 24 points in three weeks.</span>}
      />,
    );

    expect(screen.getByRole('heading', { level: 1, name: 'Vantage Logistics' })).toBeInTheDocument();
    expect(screen.getByText('VL')).toBeInTheDocument();
    expect(screen.getByText('At risk')).toBeInTheDocument();
    expect(screen.getByText('Score fell 24 points in three weeks.')).toBeInTheDocument();

    // ⚡ **A `<dl>`, because they are pairs** — a screen reader reads them as
    // pairs rather than as four loose strings.
    for (const fact of facts) {
      expect(screen.getByText(fact.label).tagName).toBe('DT');
      expect(screen.getByText(fact.value).tagName).toBe('DD');
    }
  });

  it('✅ the fact label uses --text-label, the role TASK-1453 added', () => {
    /**
     * 🔴 **This is the token's first caller.** ⚠️
     * **[TASK-1453](../../../docs/BACKLOG.md)'s own measurement named three
     * missing roles and `Label` was not one of them** — it was added because
     * that row's Definition of Done says *every role in §04's `typeRows`*.
     *
     * ⛔ **CORRECTED.** This lane first justified it with *"§08's fact strip
     * renders its labels at 12.5px."* **It renders them at 11.5px** —
     * [C-1414](../../../docs/LANE_COORDINATION.md), measured directly rather
     * than taken on trust.
     *
     * ✅ **The justification never needed §08 and does not now**: 📁 §04's
     * `typeRows` carries `['Label', '--text-label', '12.5 / 1.45 / 600', …]`
     * verbatim, and `design-scale.test.ts` asserts the token against **that**,
     * parsed from the design document. ⚡ **§04 is the type authority and §08's
     * pixels are illustrative** ([C-1414](../../../docs/LANE_COORDINATION.md)).
     */
    render(<RecordHeader title="Vantage" facts={facts} />);
    expect(screen.getByText('Open ACV')).toHaveClass('text-label');
  });

  it('⛔ everything optional is absent rather than empty', () => {
    // ⚡ A record with no facts renders no strip, not an empty one — the same
    // rule the shell applies to its banner region and its notification slot.
    const { container } = render(<RecordHeader title="Bare" />);
    expect(container.querySelector('dl')).toBeNull();
    expect(container.querySelectorAll('[data-primary-action]')).toHaveLength(0);
  });

  it('⛔ the identity tile is not a circle', () => {
    /**
     * 📁 §05 reserves 999px for *"avatar, status dot, count badge, progress
     * track"*, and the App Shell says the top bar's avatar is **the only
     * circle in the shell** — 📁 *"the avatar's uniqueness is what makes it
     * findable without reading."* ⚡ §08 draws this tile at 12px.
     */
    const { container } = render(<RecordHeader title="Vantage" initials="VL" />);
    const tile = screen.getByText('VL');
    expect(tile).toHaveClass('rounded-lg');
    expect(container.querySelector('.rounded-full')).toBeNull();
  });
});

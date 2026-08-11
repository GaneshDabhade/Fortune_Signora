/**
 * **What a rep sees where Account 360 cannot be filled** —
 * [TASK-1415](../../../docs/BACKLOG.md).
 *
 * 🔴 **The assertion that matters is that these sections EXIST on the page.**
 * ⛔ **An omission is not a designed empty state** ([§20c](../../../CLAUDE.md)),
 * and a rep who has seen the design would read a missing section as a broken
 * screen.
 */
import { render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { AbsentSection, OnThisPage } from '@/components/accounts/sections';
import { ACCOUNT_SECTIONS, absent, supplied } from '@/lib/accounts/sections';

describe('⛔ a section nothing can fill still says what it would show', () => {
  it('renders its heading and its absence sentence', () => {
    const health = ACCOUNT_SECTIONS.find((s) => s.id === 'health')!;

    render(<AbsentSection section={health} />);

    expect(screen.getByRole('heading', { level: 2, name: 'Customer health' })).toBeVisible();
    expect(screen.getByText(/does not yet read how this customer uses your product/i)).toBeVisible();
  });

  it('🔴 is NOT an empty state, and the distinction is the point', () => {
    /**
     * 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md) one level up: **an
     * empty section means *this account has none*; an absent one means
     * *Signora cannot answer at all*.** ⚠️ **A rep who reads the first when
     * the second is true concludes their account is quiet** — a commercial
     * decision made on a false reading.
     */
    const intent = ACCOUNT_SECTIONS.find((s) => s.id === 'intent')!;

    render(<AbsentSection section={intent} />);

    const text = document.body.textContent ?? '';
    for (const wrong of ['No data', 'Nothing to show', 'coming soon', 'Empty']) {
      expect(text.toLowerCase()).not.toContain(wrong.toLowerCase());
    }
    // ⚡ It names the missing SOURCE, which is something a customer can act on.
    expect(screen.getByText(/no intent source is connected/i)).toBeVisible();
  });

  it('⛔ renders nothing at all for a section that IS supplied', () => {
    // ⚡ The component cannot be pointed at a section with real data and
    // quietly replace it with a placeholder.
    const { container } = render(<AbsentSection section={supplied()[0]!} />);

    expect(container).toBeEmptyDOMElement();
  });

  it('carries an id, so the rail can reach it', () => {
    const meetings = ACCOUNT_SECTIONS.find((s) => s.id === 'meetings')!;

    const { container } = render(<AbsentSection section={meetings} />);

    expect(container.querySelector('#meetings')).not.toBeNull();
  });
});

describe('📁 the "On this page" rail maps the WHOLE record', () => {
  it('lists every section, supplied or not', () => {
    /**
     * ⛔ **A rail that hid what cannot be filled would be a map with rooms
     * missing.** 📁 The same reasoning [`rail.ts`](../../lib/shell/rail.ts)
     * records for a restricted destination: *"a hidden destination teaches a
     * person the feature does not exist, so they ask for the wrong thing or
     * ask nobody."*
     */
    render(<OnThisPage />);

    const rail = screen.getByRole('navigation', { name: 'On this page' });
    for (const section of ACCOUNT_SECTIONS) {
      expect(within(rail).getByRole('link', { name: section.label }), section.id).toBeVisible();
    }
  });

  it('⚡ dims what cannot be filled rather than hiding it', () => {
    render(<OnThisPage />);

    const rail = screen.getByRole('navigation', { name: 'On this page' });
    const dimmed = within(rail).getByRole('link', { name: 'Buying intent' });
    const live = within(rail).getByRole('link', { name: 'Account score' });

    expect(dimmed.className).not.toBe(live.className);
  });

  it('every entry points at the section it names', () => {
    render(<OnThisPage />);

    const rail = screen.getByRole('navigation', { name: 'On this page' });
    for (const section of ACCOUNT_SECTIONS) {
      expect(within(rail).getByRole('link', { name: section.label })).toHaveAttribute(
        'href',
        `#${section.id}`,
      );
    }
  });

  it('⚠️ vacuity guard — the rail is not empty', () => {
    render(<OnThisPage />);

    expect(
      within(screen.getByRole('navigation', { name: 'On this page' })).getAllByRole('link').length,
    ).toBe(ACCOUNT_SECTIONS.length);
    expect(absent().length).toBeGreaterThan(0);
  });
});

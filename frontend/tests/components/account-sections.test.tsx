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
  it('🔴 links ONLY to sections this page actually renders', () => {
    /**
     * ⚠️ **Found in a headed review, and it is the defect this component
     * exists to prevent, one level up.** ⛔ **The first version linked every
     * section by id while only the ABSENT ones carried one** — so *Account
     * score* and *Summary* were links to nowhere.
     */
    render(<OnThisPage anchored={['score', 'meetings']} />);

    const rail = screen.getByRole('navigation', { name: 'On this page' });
    expect(within(rail).getAllByRole('link')).toHaveLength(2);
    expect(within(rail).queryByRole('link', { name: 'Summary' })).toBeNull();
  });

  it('lists every section it is given, supplied or not', () => {
    /**
     * ⛔ **A rail that hid what cannot be filled would be a map with rooms
     * missing.** 📁 The same reasoning [`rail.ts`](../../lib/shell/rail.ts)
     * records for a restricted destination: *"a hidden destination teaches a
     * person the feature does not exist, so they ask for the wrong thing or
     * ask nobody."*
     */
    render(<OnThisPage anchored={ACCOUNT_SECTIONS.map((s) => s.id)} />);

    const rail = screen.getByRole('navigation', { name: 'On this page' });
    for (const section of ACCOUNT_SECTIONS) {
      expect(within(rail).getByRole('link', { name: section.label }), section.id).toBeVisible();
    }
  });

  it('⚡ dims what cannot be filled rather than hiding it', () => {
    render(<OnThisPage anchored={ACCOUNT_SECTIONS.map((s) => s.id)} />);

    const rail = screen.getByRole('navigation', { name: 'On this page' });
    const dimmed = within(rail).getByRole('link', { name: 'Buying intent' });
    const live = within(rail).getByRole('link', { name: 'Account score' });

    expect(dimmed.className).not.toBe(live.className);
  });

  it('every entry points at the section it names', () => {
    render(<OnThisPage anchored={ACCOUNT_SECTIONS.map((s) => s.id)} />);

    const rail = screen.getByRole('navigation', { name: 'On this page' });
    for (const section of ACCOUNT_SECTIONS) {
      expect(within(rail).getByRole('link', { name: section.label })).toHaveAttribute(
        'href',
        `#${section.id}`,
      );
    }
  });

  it('⚠️ vacuity guard — the rail is not empty', () => {
    render(<OnThisPage anchored={ACCOUNT_SECTIONS.map((s) => s.id)} />);

    expect(
      within(screen.getByRole('navigation', { name: 'On this page' })).getAllByRole('link').length,
    ).toBe(ACCOUNT_SECTIONS.length);
    expect(absent().length).toBeGreaterThan(0);
  });
});

describe('🔴 every section the design’s page navigation declares is declared here', () => {
  /**
   * 📁 **`Account 360`'s `pageNav` names eighteen sections.** ⛔ **Six were
   * missing from this registry entirely** — *Emails · Files · Notes · Tasks ·
   * Custom fields · History* — **not marked `absent`, absent from the
   * declaration.**
   *
   * ⚠️ **Which is the one failure the file exists to prevent.** Its own
   * docstring: *"a page that omits a section nobody built is indistinguishable
   * from a page with a bug, and the next lane cannot tell which."*
   *
   * ⛔ **None of the six has a producer** — measured, not assumed: no mailbox,
   * no document store, no note entity, no task entity, no customer-defined
   * field schema, and no contract lifecycle. ⚡ **History is NOT the timeline**:
   * the design's points are *"First contract"*, *"Expansion +420 seats"*,
   * *"Renewal · 3 years"* — **commercial milestones**, where the timeline
   * carries activity.
   */
  it('declares a section for every anchor in the design’s rail', () => {
    const declared = new Set(ACCOUNT_SECTIONS.map((section) => section.id));

    for (const id of [
      'emails',
      'files',
      'notes',
      'tasks',
      'custom-fields',
      'history',
    ]) {
      expect(declared, `the design's rail names ${id} and this file does not`).toContain(id);
    }
  });

  it('⛔ says what each cannot answer, and never “coming soon”', () => {
    /**
     * ⚡ **The positive control.** ⛔ Adding six bare `absent` entries would
     * satisfy the test above and reintroduce what the rail *"already paid for
     * once — at M12.3, three of six said `coming soon` on the screen a
     * customer sees first."*
     */
    for (const section of ACCOUNT_SECTIONS) {
      if (section.supply !== 'absent') continue;
      expect(section.absence, `${section.id} is absent and says nothing`).toBeTruthy();
      expect(section.absence).not.toMatch(/coming soon/i);
    }
  });
});

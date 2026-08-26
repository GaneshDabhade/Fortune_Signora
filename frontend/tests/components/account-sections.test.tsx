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
      // ⚡ **The rail's own string, not the heading** — 📁
      // [B-299](../../../docs/BUGS.md) ⑤, and the fallback is the majority.
      const name = section.rail ?? section.label;
      expect(within(rail).getByRole('link', { name }), section.id).toBeVisible();
    }
  });

  it('⚡ dims what cannot be filled rather than hiding it', () => {
    render(<OnThisPage anchored={ACCOUNT_SECTIONS.map((s) => s.id)} />);

    const rail = screen.getByRole('navigation', { name: 'On this page' });
    const dimmed = within(rail).getByRole('link', { name: 'Buying intent' });
    // 📁 **`Score & health` is the design's RAIL label**; *Account score* is
    // its section heading, and the rail does not use it.
    const live = within(rail).getByRole('link', { name: 'Score & health' });

    expect(dimmed.className).not.toBe(live.className);
  });

  it('every entry points at the section it names', () => {
    render(<OnThisPage anchored={ACCOUNT_SECTIONS.map((s) => s.id)} />);

    const rail = screen.getByRole('navigation', { name: 'On this page' });
    for (const section of ACCOUNT_SECTIONS) {
      const name = section.rail ?? section.label;
      expect(within(rail).getByRole('link', { name })).toHaveAttribute(
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
  /**
   * 🔴 **The ids are the design's `href`s with the `#` removed, and this list
   * is where that stopped being a convention and became a guard** —
   * [B-299](../../../docs/BUGS.md) ④.
   *
   * ⛔ **Seven were the descriptive long form instead**: `#opportunities` for
   * `#opps`, `#org-chart` for `#org`, `#relationships` for `#graph`,
   * `#tech-stack` for `#tech`, `#competitors` for `#compete`, `#emails` for
   * `#email`, `#custom-fields` for `#fields`.
   *
   * ⚠️ **And the FIRST version of this very assertion asked for `emails` and
   * `custom-fields`** — the implementation's names, not the design's — **so
   * the guard written to prove the rail matches the design was itself checking
   * against the product.** ⚡ **The list below is transcribed from `pageNav`,
   * in `pageNav`'s order**, so a reader can diff it against the document.
   *
   * ⛔ **The order is asserted too.** 📁 The design puts *Emails* before
   * *Meetings* and this registry had them the other way round — an ordering
   * nothing else on the page could reveal, because both sections are absent
   * and render identically.
   */
  it('declares the design’s anchors, in the design’s order', () => {
    // 📁 `Fortune Signora Account 360.dc.html` → `pageNav`, verbatim.
    const PAGE_NAV = [
      'score',
      'signals',
      'research',
      'opps',
      'contacts',
      'org',
      'graph',
      'tech',
      'compete',
      'market',
      'activity',
      'email',
      'meetings',
      'files',
      'notes',
      'tasks',
      'fields',
      'history',
    ];

    const declared = ACCOUNT_SECTIONS.map((section) => section.id);
    for (const id of PAGE_NAV) {
      expect(declared, `the design's rail names #${id} and this file does not`).toContain(id);
    }

    // ⚡ **Order, asserted as the design's own subsequence** — ⛔ the registry
    // holds three sections `pageNav` does not name (`summary`, `health`,
    // `intent`), **so equality would be the wrong question**; what must hold
    // is that the eighteen it does name appear in its order.
    expect(declared.filter((id) => PAGE_NAV.includes(id))).toEqual(PAGE_NAV);
  });

  /**
   * 📁 **The rail's label and the section's heading are two strings on seven
   * sections, and both are the design's** — [B-299](../../../docs/BUGS.md) ⑤.
   *
   * ⛔ **The rail rendered the heading**, so *"Contacts & committee"*,
   * *"Tech stack"*, *"Org chart"*, *"Research"*, *"Opportunities"*,
   * *"Activity"*, *"Score & health"* and *"History"* reached no screen.
   */
  it('📁 carries the design’s rail vocabulary where it differs from the heading', () => {
    const byId = new Map(ACCOUNT_SECTIONS.map((section) => [section.id, section]));

    for (const [id, rail, heading] of [
      ['score', 'Score & health', 'Account score'],
      ['research', 'Research', 'Research summary'],
      ['opps', 'Opportunities', 'Open opportunities'],
      ['contacts', 'Contacts & committee', 'Contacts & decision makers'],
      ['org', 'Org chart', 'Organisation chart'],
      ['tech', 'Tech stack', 'Technology stack'],
      ['activity', 'Activity', 'Recent activity'],
      ['history', 'History', 'Historical timeline'],
    ] as const) {
      expect(byId.get(id)?.rail, `${id}'s rail entry`).toBe(rail);
      expect(byId.get(id)?.label, `${id}'s heading`).toBe(heading);
    }
  });

  /**
   * ⛔ **`rail` is stated ONLY where the two differ.** ⚡ Repeating the heading
   * into `rail` would be two copies of one string with nothing keeping them
   * equal ([§2](../../../CLAUDE.md)) — **and the seven divergences would stop
   * being visible in the file.**
   */
  it('⛔ and states nothing where the design uses one word for both', () => {
    for (const section of ACCOUNT_SECTIONS) {
      expect(section.rail, `${section.id} repeats its own heading`).not.toBe(section.label);
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

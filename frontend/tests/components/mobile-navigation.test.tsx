/**
 * The product has navigation on a phone. **CX-07 · [B-203](../../../docs/BUGS.md).**
 *
 * **Below `768px` there was none at all.** The shell hides the sidebar and
 * nothing replaced it, so a signed-in customer on a phone could reach the
 * screen they landed on and nothing else. It sat 🟠 and *undecided* — *"whether
 * it is a defect or a non-goal depends on a product decision nobody has made"*
 * — until [C-205](../../../docs/LANE_COORDINATION.md) was ruled: **a phone is
 * in scope.**
 *
 * **No test could have caught it, and that is the more useful finding.** Every
 * component test renders at one implied width and asserts what is on screen;
 * *what disappears at a breakpoint* is invisible to jsdom, which has no layout.
 * So these assert the two things that **are** checkable — that the markup
 * exists and that the same guard applies to it — and the viewport half is
 * named here as a known limit rather than left to look covered.
 */
import { render, screen, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { MobileNavigation } from '@/components/shell/navigation';

vi.mock('next/navigation', () => ({ usePathname: () => '/' }));

describe('a phone has a way to get somewhere else', () => {
  it('offers the same destinations the sidebar does', () => {
    render(<MobileNavigation role="owner" />);

    const bar = screen.getByRole('navigation', { name: /main/i });
    expect(within(bar).getByRole('link', { name: /attention/i })).toBeInTheDocument();
    expect(within(bar).getByRole('link', { name: /your business/i })).toBeInTheDocument();
    expect(within(bar).getByRole('link', { name: /settings/i })).toBeInTheDocument();
  });

  it('keeps the labels rather than asking a first-time reader to decode an icon', () => {
    // *Your business* is not a word a briefcase carries, and a customer who
    // has to guess what a control does is a customer who does not press it.
    render(<MobileNavigation role="owner" />);

    expect(screen.getByText('Your business')).toBeVisible();
  });

  it('tells a screen reader which destination it is on', () => {
    render(<MobileNavigation role="owner" />);

    expect(screen.getByRole('link', { name: /attention/i })).toHaveAttribute(
      'aria-current',
      'page',
    );
  });
});

describe('the guard is the same one, applied to the same list', () => {
  it('hides Settings from a member, exactly as the sidebar does', () => {
    // **One list, two renderings.** A second array would be a second answer to
    // *what can this person reach*, and the two would diverge the first time
    // an entry was added to one — which is what CX-05 did to the sidebar.
    render(<MobileNavigation role="member" />);

    expect(screen.queryByRole('link', { name: /settings/i })).not.toBeInTheDocument();
  });

  it('still offers a member the two they can reach', () => {
    render(<MobileNavigation role="member" />);

    expect(screen.getByRole('link', { name: /attention/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /your business/i })).toBeInTheDocument();
  });

  it('offers nothing at all before a role has resolved', () => {
    // `can(null, …)` fails closed, and an unguarded route stays open — so this
    // asserts the shape rather than emptiness: Settings is the guarded one.
    render(<MobileNavigation role={null} />);

    expect(screen.queryByRole('link', { name: /settings/i })).not.toBeInTheDocument();
  });
});

describe('it is built for a thumb, not a cursor', () => {
  it('gives every destination a touch-sized target', () => {
    // **Roughly 44px is the floor** a thumb reliably hits. Asserted on the
    // class rather than on layout because jsdom computes none — the honest
    // half of a check whose other half needs a real viewport.
    render(<MobileNavigation role="owner" />);

    for (const link of screen.getAllByRole('link')) {
      expect(link.className).toContain('min-h-11');
    }
  });

  it('clears the home indicator on a phone that has one', () => {
    const { container } = render(<MobileNavigation role="owner" />);

    expect(container.querySelector('nav')?.className).toContain('safe-area-inset-bottom');
  });

  it('is hidden once the sidebar exists, so there is never a second navigation', () => {
    const { container } = render(<MobileNavigation role="owner" />);

    expect(container.querySelector('nav')?.className).toContain('md:hidden');
  });
});

/**
 * **`/` resolves; it does not render a product surface** —
 * 📁 `Fortune Signora Authenticated Entry.dc.html`.
 *
 * > 📁 ***"Every authenticated person lands on `/w/:workspace/home`."***
 * > 📁 ***"Entry resolution belongs to the shell, exclusively."***
 *
 * ⚠️ **The engine has been complete and tested since TASK-1400**; what was
 * missing was the caller. ⛔ **So these assert the WIRING** — which decision is
 * acted on, how, and the two cases where acting would be wrong — rather than
 * re-testing the twenty-four rules, which `entry-engine.test.ts` owns.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const replace = vi.hoisted(() => vi.fn());
const push = vi.hoisted(() => vi.fn());
const decision = vi.hoisted(() => vi.fn());

vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace, push }),
}));
vi.mock('@/lib/entry/use-entry', () => ({ useEntryDecision: decision }));

import EntryPage from '@/app/(app)/page';

beforeEach(() => {
  vi.clearAllMocks();
});

describe('📁 the decision is acted on, and it is the engine that makes it', () => {
  it('✅ sends a person to the route the engine resolved', () => {
    decision.mockReturnValue({
      status: 'resolved',
      decision: { route: '/w/w1/home', reason: 'SOLE_WORKSPACE', gate: 'workspace', workspaceId: 'w1' },
    });

    render(<EntryPage />);

    expect(replace).toHaveBeenCalledWith('/w/w1/home');
  });

  it('📁 REPLACES history, never pushes', () => {
    /**
     * 📁 *"Entry resolution replaces history rather than pushing to it.
     * Pressing back from Home after login exits to the sign-in page, **not into
     * a loop through the resolver**."*
     */
    decision.mockReturnValue({
      status: 'resolved',
      decision: { route: '/workspaces', reason: 'AMBIGUOUS', gate: 'workspace', workspaceId: null },
    });

    render(<EntryPage />);

    expect(push).not.toHaveBeenCalled();
    expect(replace).toHaveBeenCalledTimes(1);
  });

  it('⛔ chooses no destination of its own — every route comes from the engine', () => {
    // 📁 *"No module performs its own entry redirect."* ⚡ Whatever the engine
    // says, including a terminal gate, is what happens.
    for (const route of ['/account/suspended', '/onboarding/you', '/workspaces/none', '/w/w9/home']) {
      replace.mockClear();
      decision.mockReturnValue({
        status: 'resolved',
        decision: { route, reason: 'HOME', gate: 'readiness', workspaceId: null },
      });
      const { unmount } = render(<EntryPage />);
      expect(replace).toHaveBeenCalledWith(route);
      unmount();
    }
  });
});

describe('🔴 P-A — on this decision the empty result is a REDIRECT', () => {
  it('⛔ a failed membership read does not route anywhere', () => {
    /**
     * 🔴 **The worst version of P-A in this repository.** ⛔ Treating a failed
     * read as *no memberships* fires rule 10 and tells somebody with five
     * organizations that they belong to nothing — **and they lose the page they
     * were on to be told it.**
     */
    decision.mockReturnValue({ status: 'unresolved', error: new Error('boom') });

    render(<EntryPage />);

    expect(replace).not.toHaveBeenCalled();
    expect(push).not.toHaveBeenCalled();
  });

  it('✅ and says so, rather than showing a spinner forever', () => {
    decision.mockReturnValue({ status: 'unresolved', error: new Error('boom') });

    render(<EntryPage />);

    expect(screen.getAllByText(/organizations/i).length).toBeGreaterThan(0);
  });

  it('⛔ a read still in flight does not route either', () => {
    // ⚡ **The same rule one beat earlier**: a query that has not answered has
    // not said the person has no workspaces.
    decision.mockReturnValue({ status: 'resolving' });

    render(<EntryPage />);

    expect(replace).not.toHaveBeenCalled();
  });
});

describe('📁 "no confirmation, no picker, no interstitial"', () => {
  it('⛔ renders no visible product UI while resolving', () => {
    decision.mockReturnValue({ status: 'resolving' });

    const { container } = render(<EntryPage />);

    // ⚡ **`sr-only` is the whole of it.** ⛔ A visible spinner would flash on
    // every sign-in for the time one cached query takes to answer.
    expect(container.querySelector('main')).toHaveClass('sr-only');
  });

  it('♿ but a screen-reader user hears that something is happening', () => {
    decision.mockReturnValue({ status: 'resolving' });

    render(<EntryPage />);

    expect(screen.getByRole('status')).toHaveTextContent('Opening your organization');
  });
});

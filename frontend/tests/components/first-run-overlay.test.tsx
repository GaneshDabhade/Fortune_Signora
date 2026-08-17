/**
 * **The first-run overlay** — [TASK-1424](../../../docs/BACKLOG.md), against 📁
 * `Fortune Signora Authenticated Entry.dc.html` rule 20.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const usePreferences = vi.fn();
const mutate = vi.fn();

vi.mock('@/lib/query/hooks/preferences', () => ({
  usePreferences: (...args: unknown[]) => usePreferences(...args),
  useDismissFirstRun: () => ({ mutate, isPending: false }),
}));

vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({ activeWorkspace: { id: 'w1' } }),
}));

const { FirstRunOverlay } = await import('@/components/home/first-run-overlay');

beforeEach(() => {
  usePreferences.mockReset();
  mutate.mockReset();
});

describe('📁 "one sentence on what this is, one on what to do"', () => {
  it('shows both to somebody who has not dismissed it', () => {
    usePreferences.mockReturnValue({ data: { first_run_dismissed: false } });

    render(<FirstRunOverlay composition="activation" />);

    expect(screen.getByRole('heading', { name: /which accounts need you/i })).toBeVisible();
    expect(screen.getByText(/Start by connecting a CRM below/i)).toBeVisible();
  });

  it('⛔ and it is a labelled region, not a dialog that traps', () => {
    // ⚡ **An orientation a person has to ESCAPE is not an orientation.** The
    // design says *overlay*, and rule 20's content is two sentences over the
    // composition.
    usePreferences.mockReturnValue({ data: { first_run_dismissed: false } });

    const { container } = render(<FirstRunOverlay composition="activation" />);

    expect(container.querySelector('[role="dialog"]')).toBeNull();
    expect(container.querySelector('section')?.getAttribute('aria-labelledby')).toBe(
      'first-run-heading',
    );
  });
});

describe('🔴 dismissal is forever, and absence is not a "no"', () => {
  it('renders nothing once it has been dismissed', () => {
    usePreferences.mockReturnValue({ data: { first_run_dismissed: true } });

    const { container } = render(<FirstRunOverlay composition="activation" />);

    expect(container).toBeEmptyDOMElement();
  });

  /**
   * 🔴 **P-A one level up, and the reason this test exists rather than a
   * loading spinner.** ⛔ **An UNREAD preference must never render as *not yet
   * dismissed***, because that shows the overlay again to somebody who closed
   * it — **on every slow connection, forever.**
   */
  it('⛔ renders nothing while the preference is still unknown', () => {
    usePreferences.mockReturnValue({ data: undefined, isLoading: true });

    const { container } = render(<FirstRunOverlay composition="activation" />);

    expect(container).toBeEmptyDOMElement();
  });

  it('⚠️ and a failed read is silence too, deliberately', () => {
    // ⚡ **A failed preference read is not something to tell a customer about on
    // the first screen they have ever seen**, and the cost of being wrong is
    // one missing greeting rather than a missing capability.
    usePreferences.mockReturnValue({ data: undefined, isError: true });

    const { container } = render(<FirstRunOverlay composition="activation" />);

    expect(container).toBeEmptyDOMElement();
  });
});

describe('✅ closing it records the dismissal on the server', () => {
  it('the control calls the mutation', async () => {
    usePreferences.mockReturnValue({ data: { first_run_dismissed: false } });

    render(<FirstRunOverlay composition="activation" />);
    screen.getByRole('button', { name: 'Dismiss' }).click();

    expect(mutate).toHaveBeenCalledTimes(1);
  });

  it('⛔ and nothing is written to localStorage', () => {
    // 📁 The design says it twice: *"nothing about activation lives in
    // localStorage"*, and the overlay is a sibling of those cards. ⚡ **A
    // dismissal in a browser is one a person loses when they change machine**,
    // which turns *forever* into *until Tuesday*.
    window.localStorage.clear();
    usePreferences.mockReturnValue({ data: { first_run_dismissed: false } });

    render(<FirstRunOverlay composition="activation" />);
    screen.getByRole('button', { name: 'Dismiss' }).click();

    expect(window.localStorage.length).toBe(0);
  });
});

describe('🔴 sentence two names something that is actually on the page', () => {
  /**
   * ⚠️ **The overlay renders *"over whichever composition resolved"*, and this
   * sentence said *"connect a CRM below"* on all four.** ⛔ **A seller whose
   * workspace was already connected was pointed at a card the composition
   * filters out** — the false-claim class [§2](../../../CLAUDE.md) refuses, and
   * one no type or lint could have seen.
   */
  it('⛔ never tells a data composition to connect a CRM', () => {
    usePreferences.mockReturnValue({ data: { first_run_dismissed: false } });
    for (const composition of ['seller', 'executive', 'revenue_operations'] as const) {
      const { unmount } = render(<FirstRunOverlay composition={composition} />);
      expect(screen.queryByText(/connecting a CRM/i)).not.toBeInTheDocument();
      unmount();
    }
  });

  it('✅ keeps the design-derived sentence on activation', () => {
    usePreferences.mockReturnValue({ data: { first_run_dismissed: false } });
    render(<FirstRunOverlay composition="activation" />);

    expect(screen.getByText(/Start by connecting a CRM below/)).toBeInTheDocument();
  });

  it('📁 stays at two sentences on every composition', () => {
    // 📁 *"One sentence on what this is, one on what to do."* ⛔ The count is
    // the specification — a third would make this the tour rule 20 refuses.
    usePreferences.mockReturnValue({ data: { first_run_dismissed: false } });
    for (const composition of ['activation', 'seller', 'executive', 'revenue_operations'] as const) {
      const { container, unmount } = render(<FirstRunOverlay composition={composition} />);
      expect(container.querySelectorAll('h2, p')).toHaveLength(2);
      unmount();
    }
  });
});

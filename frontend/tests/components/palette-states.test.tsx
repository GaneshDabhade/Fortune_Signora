import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { CommandPalette, type CommandItem } from '@/components/ui';

/**
 * **Four states, because they are four different facts** —
 * [TASK-481](../../../docs/BACKLOG.md).
 *
 * 📁 **The row's Definition of Done**: *"empty, loading, no-results and error
 * states are four distinct screens, and **no-results must never render as
 * error**."* 📁 **Its Component coverage**: *"a failed read renders the ERROR
 * state and not the empty one — [C-226](../../../docs/LANE_COORDINATION.md)
 * found that exact confusion six times on one screen."*
 *
 * 🔴 **On a search surface this is the most expensive version of the
 * confusion.** ⚡ ***"Nothing matches"* is a statement about the customer's
 * data**, and somebody who reads it about a request that never completed
 * concludes their record is gone.
 */

const noop = vi.fn();

function palette(over: Partial<Parameters<typeof CommandPalette>[0]> = {}) {
  const items: CommandItem[] = [];
  return render(
    <CommandPalette
      open
      onClose={noop}
      items={items}
      query="acme"
      onQueryChange={noop}
      onSelect={noop}
      {...over}
    />,
  );
}

describe('🔴 a failed search is never reported as an empty one', () => {
  it('⛔ error says the SEARCH failed, not that nothing matched', () => {
    palette({ status: 'error' });

    expect(screen.getByText(/could not search/i)).toBeInTheDocument();
    // 🔴 **The assertion the row is written about.**
    expect(screen.queryByText(/Nothing matches/i)).not.toBeInTheDocument();
  });

  it('⚡ and it is announced, because a failure nobody hears is a failure nobody retries', () => {
    palette({ status: 'error' });
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  it('⛔ error also says what is still true, and what to do', () => {
    // ⚡ The three-part sentence `StatedAbsence` established: what failed ·
    // what is still true · what to do. **The fear a failed read creates is
    // that the data is gone.**
    palette({ status: 'error' });
    expect(screen.getByText(/Nothing has changed/i)).toBeInTheDocument();
    expect(screen.getByText(/try again/i)).toBeInTheDocument();
  });
});

describe('📁 the other three are distinct from it and from each other', () => {
  it('⚡ loading says it is searching, not that it found nothing', () => {
    palette({ status: 'loading' });

    expect(screen.getByText(/Searching/i)).toBeInTheDocument();
    expect(screen.queryByText(/Nothing matches/i)).not.toBeInTheDocument();
    // ⛔ **Polite, not assertive** — a search that resolves in 200ms would
    // otherwise interrupt a screen reader mid-word on every keystroke.
    expect(screen.getByText(/Searching/i)).toHaveAttribute('aria-live', 'polite');
  });

  it('⛔ an untyped query is a prompt, not a verdict', () => {
    // ⚡ Saying *nothing matches ""* answers a question nobody asked.
    palette({ status: 'idle', query: '' });

    expect(screen.getByText(/Type to search/i)).toBeInTheDocument();
    expect(screen.queryByText(/Nothing matches/i)).not.toBeInTheDocument();
  });

  it('✅ and no-results still says exactly that, or the fix removed the feature', () => {
    // ⚡ **The discriminating case.** Three tests asserting an absence of
    // "Nothing matches" all pass if the sentence is deleted altogether.
    palette({ status: 'ready', query: 'acme' });

    expect(screen.getByText(/Nothing matches/i)).toBeInTheDocument();
    expect(screen.getByText(/acme/)).toBeInTheDocument();
  });

  it('⚡ all four render something — a blank box is not one of the states', () => {
    for (const status of ['idle', 'loading', 'ready', 'error'] as const) {
      const { container, unmount } = palette({ status });
      expect(container.textContent?.trim(), `${status} rendered nothing`).toBeTruthy();
      unmount();
    }
  });
});

describe('⚠️ the states only speak when there is nothing to show', () => {
  it('⛔ results are never replaced by a state screen', () => {
    /**
     * ⚡ **A stale-while-revalidating search still has rows worth reading**, and
     * replacing them with *"Searching…"* on every keystroke is the flicker that
     * makes a palette feel slower than it is.
     */
    const items: CommandItem[] = [{ id: 'nav:/settings', label: 'Settings' }];
    palette({ status: 'loading', items });

    expect(screen.getByText('Settings')).toBeInTheDocument();
    expect(screen.queryByText(/Searching/i)).not.toBeInTheDocument();
  });
});

describe('⚠️ the default keeps every existing caller working', () => {
  it('✅ omitting status behaves exactly as before', () => {
    // ⛔ §20c — this is additive to a frozen component, not a breaking change.
    palette({});
    expect(screen.getByText(/Nothing matches/i)).toBeInTheDocument();
  });
});

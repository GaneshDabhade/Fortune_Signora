/**
 * 📁 **Home → `card.pipeline`** — *Pipeline health*.
 *
 * ⚠️ **Two tests already touch this file and NEITHER renders it** — one reads
 * it with `readFileSync`, the other asserts the registry holds its id. ⛔ **Both
 * would pass if the card threw on mount.**
 *
 * ⚡ **`pipeline` here is the SELLER's word, not the platform's.** 📁 ADR-0034's
 * platform list names the *intelligence* pipeline — the processing stages — and
 * `INTERNAL_TERMS` deliberately omits the term for exactly this reason. **A
 * salesperson says *my pipeline* unprompted, which is the ADR's own test.**
 */
import { act, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import type { PipelineHealth, StageAgeing } from '@/lib/api/types';
import { GIVE_UP_AFTER_MS, SKELETON_AFTER_MS } from '@/lib/home/loading';

const usePipelineHealth = vi.hoisted(() => vi.fn());

vi.mock('@/lib/query/hooks/commercial', () => ({ usePipelineHealth }));
vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({ activeWorkspace: { id: 'w-1', name: 'Northwind' } }),
}));

import { PipelineHealthCard } from '@/components/home/pipeline-health-card';

/** ⚡ **The contract's own shape**, so a fixture cannot reach a state the API cannot send. */
function stage(over: Partial<StageAgeing> = {}): StageAgeing {
  return { stage: 'tracking', open_count: 3, median_days: 12.4, oldest_days: 40, ...over };
}

function health(over: Partial<PipelineHealth> = {}): PipelineHealth {
  return {
    conversions: [],
    ageing: [stage()],
    owners: [],
    movements: [],
    movements_since: '2026-08-01T00:00:00Z',
    ...over,
  };
}

const refetch = vi.fn();
function answer(over: Record<string, unknown> = {}) {
  return {
    isLoading: false,
    isError: false,
    isFetching: false,
    error: null,
    data: health(),
    refetch,
    ...over,
  };
}

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  vi.clearAllMocks();
  usePipelineHealth.mockReturnValue(answer());
});
afterEach(() => {
  vi.useRealTimers();
});

/** ⚡ Advance the card's own §09 clock inside `act`, or the phase never renders. */
function elapse(ms: number) {
  act(() => {
    vi.advanceTimersByTime(ms);
  });
}

describe('📁 §09 — the card says nothing before it says anything', () => {
  it(`⛔ renders NO placeholder for the first ${SKELETON_AFTER_MS}ms`, () => {
    // 📁 *"a placeholder shown and removed inside 300ms reads as a flicker."*
    usePipelineHealth.mockReturnValue(answer({ isLoading: true, data: undefined }));
    render(<PipelineHealthCard />);

    // ✅ **The pin** — the card itself is on screen; only its body is quiet.
    expect(screen.getByText('Pipeline health')).toBeInTheDocument();
    expect(screen.queryByRole('status')).toBeNull();
    expect(document.body.textContent ?? '').not.toMatch(/could not be read|No open deals/);
  });

  it('✅ and then a skeleton, which is the vacuity half of the assertion above', () => {
    usePipelineHealth.mockReturnValue(answer({ isLoading: true, data: undefined }));
    const { container } = render(<PipelineHealthCard />);

    elapse(SKELETON_AFTER_MS + 10);

    /**
     * ⚠️ **`[data-skeleton]`, never the animation class.** 🔴
     * [B-297](../../../docs/BUGS.md): the skeleton had fifteen implementations
     * and **six test locators selected it by `animate-pulse`** — ⛔ **which
     * also matched the app shell's refresh bar**, a `role="progressbar"` that
     * pulses and is not a placeholder. ⚡ **`skeleton-single-source.test.tsx`
     * refused this file until it was fixed**, which is a guard doing exactly
     * its job on a test written an hour ago.
     */
    expect(container.querySelectorAll('[data-skeleton]').length).toBeGreaterThan(0);
  });

  it(`🔴 a read still running at ${GIVE_UP_AFTER_MS}ms becomes a FAILURE, with a retry`, () => {
    /**
     * 📁 *"the card converts to its error state with a retry."* ⛔ **The read is
     * not aborted** — a late response still renders — **but a customer is not
     * left watching a skeleton forever.**
     */
    usePipelineHealth.mockReturnValue(answer({ isLoading: true, data: undefined }));
    render(<PipelineHealthCard />);

    elapse(GIVE_UP_AFTER_MS + 10);

    expect(screen.getByText(/could not be read/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });
});

describe('🔴 P-A — a failed read is a failure, never an empty pipeline', () => {
  it('⛔ offers a retry and never the empty state’s words', () => {
    /**
     * ⚠️ **This rendered `StatedAbsence`, which is the wrong half of the pair.**
     * 📁 *"`EmptyState` says there is nothing; a system state says something
     * failed… conflating them is how a broken widget renders as an empty one."*
     */
    usePipelineHealth.mockReturnValue(
      answer({ isError: true, error: new Error('down'), data: undefined }),
    );
    render(<PipelineHealthCard />);

    expect(screen.getByText(/How your pipeline is moving could not be read/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
    // ⛔ **Never the empty sentence** — that would claim the customer has no deals.
    expect(screen.queryByText(/No open deals to measure/)).toBeNull();
    expect(document.body.textContent ?? '').not.toMatch(/found nothing open/);
  });

  it('⚡ and it scopes the damage, rather than implying the page is broken', () => {
    // 📁 One card failing is not the page failing, and a customer cannot tell
    // unless the card says so.
    usePipelineHealth.mockReturnValue(
      answer({ isError: true, error: new Error('down'), data: undefined }),
    );
    render(<PipelineHealthCard />);

    expect(screen.getByText(/Nothing about your deals has changed/)).toBeInTheDocument();
    expect(screen.getByText(/Everything else on this page is unaffected/)).toBeInTheDocument();
  });
});

describe('✅ an empty pipeline names what was checked and when', () => {
  it('📁 says nothing is open, and dates it from the API rather than the clock', () => {
    /**
     * 📁 ***"Every empty card names what was checked and when."*** ⚡
     * **`movements_since` is ECHOED by the API** precisely so the card does not
     * have to remember what it asked for — ⛔ **a date from `Date.now()` here
     * would drift from the window actually queried.**
     */
    usePipelineHealth.mockReturnValue(
      answer({ data: health({ ageing: [stage({ open_count: 0 })] }) }),
    );
    render(<PipelineHealthCard />);

    expect(screen.getByText('No open deals to measure')).toBeInTheDocument();
    expect(screen.getByText(/checked every stage of your pipeline/)).toBeInTheDocument();
    expect(screen.getByText(/Movement has been read since/)).toBeInTheDocument();
    // ⛔ **Not the failure**, which is the vacuity half of the P-A pair above.
    expect(screen.queryByText(/could not be read/)).toBeNull();
  });
});

describe('⚡ the age is the point of a stage row, not the count', () => {
  it('📁 renders every stage with its open count and its median age', () => {
    // 📁 *"A stage holding four deals for two days and one holding four for
    // ninety are the same number and a different pipeline."*
    usePipelineHealth.mockReturnValue(
      answer({
        data: health({
          ageing: [
            stage({ stage: 'tracking', open_count: 4, median_days: 2.4 }),
            stage({ stage: 'engaged', open_count: 4, median_days: 89.6 }),
          ],
        }),
      }),
    );
    render(<PipelineHealthCard />);

    expect(screen.getByText('8')).toBeInTheDocument();
    expect(screen.getByText(/open deals across 2 stages/)).toBeInTheDocument();
    const rows = screen.getAllByRole('listitem');
    expect(rows).toHaveLength(2);
    expect(within(rows[0] as HTMLElement).getByText('median 2d')).toBeInTheDocument();
    expect(within(rows[1] as HTMLElement).getByText('median 90d')).toBeInTheDocument();
  });

  it('⚠️ counts in the reader’s grammar, singular and plural', () => {
    usePipelineHealth.mockReturnValue(
      answer({ data: health({ ageing: [stage({ open_count: 1 })] }) }),
    );
    render(<PipelineHealthCard />);
    expect(screen.getByText(/open deal across 1 stage$/)).toBeInTheDocument();
  });

  it('⛔ and says nothing moved rather than rendering an empty movement list', () => {
    usePipelineHealth.mockReturnValue(answer({ data: health({ movements: [] }) }));
    render(<PipelineHealthCard />);
    expect(screen.getByText(/Nothing has moved since/)).toBeInTheDocument();
  });
});

describe('⛔ coverage has no producer, and the card says so rather than inventing one', () => {
  it('📁 states the absence and renders no target figure', () => {
    // ⚡ **Nothing holds a target to measure against**, so a coverage number
    // here would have no author — 📁 §2's least-powerful-author rule.
    render(<PipelineHealthCard />);

    expect(
      screen.getByText(/Signora does not hold a target to measure your pipeline against/),
    ).toBeInTheDocument();
    expect(document.body.textContent ?? '').not.toMatch(/\d+\s?%|coverage ratio|\bquota\b/i);
  });
});

describe('🔴 C-1553 — the footprint is reserved WITHOUT clipping the stage list', () => {
  it('⛔ declares a minimum height and never a fixed one', () => {
    /**
     * 📁 The registry declares `1fr × 320px`, and the card jumped when data
     * landed because it declared nothing. ⚡ **`min-h` reserves the footprint.**
     *
     * ⛔ **`h-[320px]` with `overflow-hidden` is [C-1553](../../../docs/LANE_COORDINATION.md)**
     * — `card.recents` renders five rows into a box that fits two and clips
     * three silently. **The stage list here is unbounded**, so pinning the
     * height would put the same unresolved conflict on a second card.
     */
    const { container } = render(<PipelineHealthCard />);
    const card = container.firstElementChild as HTMLElement;

    expect(card.classList.contains('min-h-[320px]')).toBe(true);
    expect(card.className).not.toMatch(/(?:^|\s)h-\[320px\]/);
    expect(card.className).not.toContain('overflow-hidden');
  });
});

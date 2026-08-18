/**
 * **Home's two timed loading rules** — 📁 `Fortune Signora Home.dc.html` §09.
 *
 * > | | |
 * > |---|---|
 * > | **Under 300ms** | *"**No skeleton at all.** A placeholder shown and removed inside 300ms reads as a flicker."* |
 * > | **Over 8 seconds** | *"The card **converts to its error state with a retry**. Skeletons do not shimmer indefinitely."* |
 *
 * ⚡ **Fake timers, because the rules ARE the clock.** ⛔ Waiting 8 real seconds
 * per assertion would make the suite unrunnable, and sampling at 7.9 and 8.1
 * seconds would make it flaky on a loaded machine.
 */
import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { GIVE_UP_AFTER_MS, SKELETON_AFTER_MS, useCardPhase } from '@/lib/home/loading';

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
});

describe('📁 "under 300ms — no skeleton at all"', () => {
  it('🔴 is quiet for the first 300ms of a wait', () => {
    const { result } = renderHook(() => useCardPhase(true));

    expect(result.current).toBe('quiet');

    act(() => {
      vi.advanceTimersByTime(SKELETON_AFTER_MS - 1);
    });

    expect(result.current, 'a skeleton appeared inside the flicker window').toBe('quiet');
  });

  it('shows the skeleton once the wait outlasts the window', () => {
    const { result } = renderHook(() => useCardPhase(true));

    act(() => {
      vi.advanceTimersByTime(SKELETON_AFTER_MS);
    });

    expect(result.current).toBe('skeleton');
  });

  /**
   * ⚡ **The rule's whole point.** 📁 *"A placeholder shown and removed inside
   * 300ms reads as a flicker"* — so a read that settles quickly must never have
   * produced one.
   */
  it('🔴 a read that settles in 200ms never produced a skeleton', () => {
    let pending = true;
    const { result, rerender } = renderHook(() => useCardPhase(pending));

    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(result.current).toBe('quiet');

    pending = false;
    rerender();
    act(() => {
      vi.advanceTimersByTime(1_000);
    });

    expect(result.current).toBe('settled');
  });
});

describe('📁 "over 8 seconds — the card converts to its error state"', () => {
  it('🔴 times out at eight seconds', () => {
    const { result } = renderHook(() => useCardPhase(true));

    act(() => {
      vi.advanceTimersByTime(GIVE_UP_AFTER_MS - 1);
    });
    expect(result.current, 'the card gave up early').toBe('skeleton');

    act(() => {
      vi.advanceTimersByTime(1);
    });

    expect(result.current).toBe('timeout');
  });

  /**
   * ⛔ **The query is not aborted.** ⚡ *"Skeletons do not shimmer indefinitely"*
   * is a statement about what a person sees, not about the network — so a
   * response arriving at nine seconds still settles the card.
   */
  it('🔴 heals itself when a late response lands', () => {
    let pending = true;
    const { result, rerender } = renderHook(() => useCardPhase(pending));

    act(() => {
      vi.advanceTimersByTime(GIVE_UP_AFTER_MS + 500);
    });
    expect(result.current).toBe('timeout');

    pending = false;
    rerender();

    expect(result.current).toBe('settled');
  });

  /**
   * ⚡ **A refetch starts its own quiet window** rather than inheriting the last
   * attempt's verdict. ⛔ Otherwise a retry after a timeout would show its
   * skeleton instantly, which is the flicker the first rule forbids.
   */
  it('⛔ and a retry begins its own 300ms of quiet', () => {
    let pending = true;
    const { result, rerender } = renderHook(() => useCardPhase(pending));

    act(() => {
      vi.advanceTimersByTime(GIVE_UP_AFTER_MS + 100);
    });
    pending = false;
    rerender();

    pending = true;
    rerender();

    expect(result.current).toBe('quiet');
  });
});

describe('📁 "independence — one slow card holds its own skeleton"', () => {
  /**
   * ⛔ **No shared timer.** 📁 §09: *"No card waits for a sibling, and none is
   * disabled while a neighbour loads."* ⚡ Two cards that started their waits at
   * different moments must cross 300ms at different moments.
   */
  it('🔴 two cards keep separate clocks', () => {
    const first = renderHook(() => useCardPhase(true));

    act(() => {
      vi.advanceTimersByTime(200);
    });

    const second = renderHook(() => useCardPhase(true));

    act(() => {
      vi.advanceTimersByTime(150);
    });

    // The first card has waited 350ms; the second has waited 150ms.
    expect(first.result.current).toBe('skeleton');
    expect(second.result.current).toBe('quiet');
  });
});

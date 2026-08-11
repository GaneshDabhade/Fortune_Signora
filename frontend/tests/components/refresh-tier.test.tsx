/**
 * **§16 tier three — an in-place refresh** —
 * [TASK-1463](../../../docs/BACKLOG.md).
 *
 * > 📁 ***"In-place refreshes show a 2px bar under the top bar and dim stale
 * > figures to 60%; they never cover data that is already readable."***
 *
 * 🔴 **The tier boundary is the property under test**, not the bar. ⚡ **A
 * *something is fetching* boolean would light the bar during a cold boot too**
 * — and then tiers one and two would be showing a refresh indicator over a
 * skeleton, which says *stale* about content that is simply new.
 */
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import { useQuery } from '@tanstack/react-query';
import { describe, expect, it } from 'vitest';
import type { ReactNode } from 'react';

import { useIsRefreshing } from '@/lib/shell/refreshing';

function wrapper(client: QueryClient) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  };
}

function fresh() {
  return new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
}

/** A query whose promise this test resolves by hand, so *in flight* is a state
 *  the test holds rather than a race it hopes for. */
function deferred<T>() {
  let settle: (value: T) => void = () => {};
  const promise = new Promise<T>((resolve) => {
    settle = resolve;
  });
  return { promise, settle: (value: T) => settle(value) };
}

describe('⛔ a first load is not a refresh', () => {
  it('🔴 stays false while a query has no data yet', async () => {
    const client = fresh();
    const gate = deferred<string>();

    const { result } = renderHook(
      () => {
        useQuery({ queryKey: ['cold'], queryFn: () => gate.promise });
        return useIsRefreshing();
      },
      { wrapper: wrapper(client) },
    );

    // ⚡ **Fetching, and nothing readable** — 📁 tier one, whose answer is a
    // skeleton in the region that owns it.
    await waitFor(() => expect(client.isFetching()).toBe(1));
    expect(result.current).toBe(false);

    gate.settle('done');
    await waitFor(() => expect(client.isFetching()).toBe(0));
  });
});

describe('✅ a refetch over readable data is a refresh', () => {
  it('🔴 turns true only once the data is there and a fetch is running', async () => {
    const client = fresh();
    client.setQueryData(['warm'], 'a figure the reader can see');
    const gate = deferred<string>();

    const { result } = renderHook(
      () => {
        useQuery({
          queryKey: ['warm'],
          queryFn: () => gate.promise,
          staleTime: 0,
        });
        return useIsRefreshing();
      },
      { wrapper: wrapper(client) },
    );

    await waitFor(() => expect(result.current).toBe(true));

    gate.settle('a newer figure');
    await waitFor(() => expect(result.current).toBe(false));
  });

  /**
   * 🔴 **One first load anywhere on the screen switches the tier off.**
   *
   * ⚡ **Deliberate, and it is the whole boundary**: if anything on screen is
   * still unknown, the screen is in tier one or two, ⛔ **and dimming the rest
   * to 60% would mark content as stale next to a region that is loading for
   * the first time.**
   */
  it('⛔ a single cold query anywhere cancels it', async () => {
    const client = fresh();
    client.setQueryData(['warm'], 'readable');
    const warm = deferred<string>();
    const cold = deferred<string>();

    const { result } = renderHook(
      () => {
        useQuery({ queryKey: ['warm'], queryFn: () => warm.promise, staleTime: 0 });
        useQuery({ queryKey: ['cold'], queryFn: () => cold.promise });
        return useIsRefreshing();
      },
      { wrapper: wrapper(client) },
    );

    await waitFor(() => expect(client.isFetching()).toBe(2));
    expect(result.current).toBe(false);

    warm.settle('x');
    cold.settle('y');
    await waitFor(() => expect(client.isFetching()).toBe(0));
  });
});

describe('⛔ nothing in flight is not a refresh', () => {
  it('✅ false on a settled screen', () => {
    const client = fresh();
    client.setQueryData(['warm'], 'readable');

    const { result } = renderHook(() => useIsRefreshing(), { wrapper: wrapper(client) });

    expect(result.current).toBe(false);
  });
});

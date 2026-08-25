/**
 * 🔴 **[B-237](../../../docs/BUGS.md)'s second symptom, reproduced — `/` made
 * 22 workspace reads in 22 seconds and never stopped.**
 *
 * ⚡ **QE measured it in a browser and I could not**, so this reproduces the
 * INTERACTION in jsdom: a gate that mounts a child on the answer, a child that
 * observes the same query, and a query that always fails. **React Query and
 * React both run here, and so does the loop.**
 *
 * 🔴 **What the reproduction established, and it corrected my own model:**
 *
 * ```
 *   status=error    err=Y  loading=n  known=Y   → gate opens, child mounts
 *   status=pending  err=n  loading=Y  known=n   → gate shuts, child unmounts
 *   status=error    err=Y  loading=n  known=Y   → …forever
 * ```
 *
 * ⛔ **When a query holding NO data refetches, React Query returns it to
 * `pending` and CLEARS `error`.** ⚡ So a gate reading `error` directly can
 * never stay open — **which is why the first fix at `6871972b` was correct
 * about the mechanism and did not act on it.**
 *
 * ⛔ **And `refetchOnMount: false` does not help**: with no data at all a new
 * observer must fetch regardless. **Measured: 121 → 103.** The observer has to
 * stop unmounting.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import { render } from '@testing-library/react';
import { useEffect, useState } from 'react';
import { describe, expect, it } from 'vitest';

import { workspaceKnown } from '@/lib/shell/workspace-gate';

let calls = 0;

/** ⚡ **The real policy**: two retries for a 5xx, and the 30s default staleness. */
function useFailingWorkspaces() {
  return useQuery({
    queryKey: ['workspaces'],
    queryFn: () => {
      calls += 1;
      return Promise.reject(new Error('500'));
    },
    retry: (failureCount: number) => failureCount < 2,
    // ⚡ Compressed from the real 1s/2s so the test is fast; the SHAPE is what
    // reproduces, not the wall-clock.
    retryDelay: 5,
    staleTime: 30_000,
  });
}

/** The entry page's shape: a second observer on the same query. */
function Child() {
  useFailingWorkspaces();
  return <p>opened</p>;
}

function Shell({ latch }: { latch: boolean }) {
  const query = useFailingWorkspaces();

  const [readFailed, setReadFailed] = useState(false);
  useEffect(() => {
    if (query.error) setReadFailed(true);
  }, [query.error]);

  const known = workspaceKnown({
    isLoading: query.isLoading,
    // 🔴 **The whole finding in one ternary.**
    error: latch ? readFailed : query.error,
    activeWorkspace: null,
    workspaceCount: 0,
  });

  return known ? <Child /> : <p>Loading…</p>;
}

async function fetchesIn600ms(latch: boolean): Promise<number> {
  calls = 0;
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <Shell latch={latch} />
    </QueryClientProvider>,
  );
  await new Promise((resolve) => setTimeout(resolve, 600));
  return calls;
}

describe('🔴 a failed workspace read must settle, not cycle', () => {
  it('⛔ reading `error` directly cycles without end — the defect', async () => {
    /**
     * ⚠️ **This is the POSITIVE CONTROL, and it is the reason this file
     * exists.** ⛔ Without it, the passing test below could not distinguish
     * *"the latch works"* from *"jsdom never reproduced the loop at all"* —
     * which is [B-1073](../../../docs/BUGS.md)'s class, and the trap I have
     * already fallen into once on this row.
     */
    expect(await fetchesIn600ms(false)).toBeGreaterThan(40);
  });

  it('✅ latching the failure settles it', async () => {
    // Three attempts for the shell's observer and three for the child's, then
    // nothing. Measured at 6; bounded generously so retry timing cannot make
    // this brittle.
    expect(await fetchesIn600ms(true)).toBeLessThan(12);
  });
});

describe('⚠️ and the shell actually uses the latch', () => {
  /**
   * 🔴 **The tests above reproduce the SHAPE with a local `Shell`, so reverting
   * `authenticated-shell.tsx` leaves them green.** ⛔ **I checked, and it
   * does** — which is the wrong-population failure exactly: the assertion is
   * sound and its subject is not the thing that can break.
   *
   * ⚠️ **This is a SOURCE check and I am labelling it as one.** It cannot see
   * behaviour. ⚡ **What it can see is the one substitution that reintroduces
   * the loop** — passing the query's `error` where the latched value belongs —
   * and the repository already guards this class from source
   * (`no-mock-data`, `library-reachability`, `row-citations`).
   *
   * ⛔ **Testing the real `AuthenticatedShell` would need the session, the
   * provider, the viewer role and the route guard all stood up**, and a mock
   * of the provider is what made the first fix look verified when it was not.
   */
  it('🔴 passes the latched failure to the gate, never the raw query error', () => {
    const source = readFileSync(
      join(process.cwd(), 'app/(app)/authenticated-shell.tsx'),
      'utf8',
    );

    // The latch exists…
    expect(source).toMatch(/setReadFailed\(true\)/);

    /**
     * …and it is what the GATE CALL is given.
     *
     * ⚠️ **Scoped to the `workspaceKnown({…})` call, and the first draft was
     * not.** ⛔ It asserted `error: workspacesError` appeared nowhere — and
     * that string legitimately appears in the destructure of
     * `useWorkspaceContext()`, so the guard failed on correct code. **A
     * population too wide, which fails loudly**; the narrow version is the
     * one that says something true.
     */
    const call = /workspaceKnown\(\{[\s\S]*?\}\)/.exec(source)?.[0] ?? '';
    expect(call, 'no workspaceKnown call found').not.toBe('');
    expect(call).toMatch(/error:\s*readFailed/);
    expect(call).not.toMatch(/error:\s*workspacesError/);
  });
});

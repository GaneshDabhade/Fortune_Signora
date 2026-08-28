/**
 * 🔴 **[B-261](../../../docs/BUGS.md) — `/account-identities` now carries the
 * account's TYPE, and eight surfaces that only want a name did not move.**
 *
 * ## ⛔ The design rule the page could not satisfy
 *
 * 📁 **`Fortune Signora Account 360.dc.html` §*States*, Collapsed**: ***"State
 * persists per user and per account TYPE, not per record."***
 *
 * ⚡ **Keying by `accountId` is the obvious implementation and the one the rule
 * forbids** — a rep who collapses *Technology stack* has decided they do not
 * care about technology stacks **on companies**, not that they do not care
 * about it **on Acme**. ⛔ **Keyed per record, the preference is re-made on
 * every account opened, which is the same as having none.**
 *
 * ## ⚠️ Why this file exists rather than a wider assertion on the page
 *
 * 🔴 **The fix could have been a ripple.** `kind` must sit **beside** the
 * identity rather than inside it — 📁 an identity answers *who is this* and a
 * classification is a different question — **so the response became
 * `{account, kind}[]`, and `useAccountIdentities` has eight production
 * consumers, none of which want a type.**
 *
 * ⛔ **A shape change there would have moved eight surfaces to serve one page**,
 * which is what 📁 [§20c](../../../CLAUDE.md) bars: *"a component bent to suit
 * one caller is slightly wrong for every other."*
 *
 * ✅ **So `useAccountIdentities` is a `select` projection over
 * `useAccountEntries`, sharing its `queryKey`.** ⚡ **The property that makes
 * that safe is invisible in every other test**: two hooks, one request. **A
 * regression to two query keys would leave every assertion in this repository
 * green and double the network cost of every list that names its rows.**
 */
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { AccountIdentityEntry } from '@/lib/api/types';

const apiRequest = vi.hoisted(() => vi.fn());
vi.mock('@/lib/api/client', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/lib/api/client')>()),
  apiRequest,
}));

const { useAccountEntries, useAccountIdentities } = await import('@/lib/query/hooks');

const WORKSPACE = '11111111-1111-4111-8111-111111111111';
const ACME = '22222222-2222-4222-8222-222222222222';
const ADA = '33333333-3333-4333-8333-333333333333';

/**
 * ⛔ **Built from the product's own exported type, never hand-shaped.** ⚠️ **A
 * fixture is a second representation of a contract**, and this repository has
 * manufactured four findings from one that had drifted.
 */
function entry(id: string, name: string, kind: AccountIdentityEntry['kind']): AccountIdentityEntry {
  return {
    account: {
      account_id: id,
      name,
      agreement: 'agreed',
      source_count: 2,
      source: 'apollo',
      observed_at: '2026-08-01T00:00:00Z',
      last_observed_at: '2026-08-02T00:00:00Z',
    },
    kind,
  };
}

const PAGE: readonly AccountIdentityEntry[] = [
  entry(ACME, 'Acme Corporation', 'company'),
  entry(ADA, 'Ada Lovelace', 'person'),
];

function wrapper() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  };
}

beforeEach(() => {
  apiRequest.mockReset();
  apiRequest.mockResolvedValue([...PAGE]);
});

describe('🔴 the identity read carries a type, and the name-only callers did not move', () => {
  it('⛔ names and types come from ONE request, not two', async () => {
    /**
     * ⚡ **The whole design in one assertion.** ⛔ **Two hooks with two query
     * keys would pass every other test in this file** — the same bytes, twice
     * over the wire, for every list that names its rows.
     */
    const Wrapper = wrapper();
    const both = renderHook(
      () => ({
        names: useAccountIdentities(WORKSPACE, [ACME, ADA]),
        entries: useAccountEntries(WORKSPACE, [ACME, ADA]),
      }),
      { wrapper: Wrapper },
    );

    await waitFor(() => {
      expect(both.result.current.names.data).toBeDefined();
      expect(both.result.current.entries.data).toBeDefined();
    });

    expect(apiRequest).toHaveBeenCalledTimes(1);
    expect(apiRequest.mock.calls[0]?.[0]).toContain('/account-identities?');
  });

  it('✅ `useAccountIdentities` still returns identities, unchanged', async () => {
    /**
     * ⛔ **The eight consumers assert this by not having changed.** ⚠️ **So it
     * is asserted here explicitly**: a `select` that leaked the wrapper would
     * break them all, and nothing else in this file would notice.
     */
    const { result } = renderHook(() => useAccountIdentities(WORKSPACE, [ACME]), {
      wrapper: wrapper(),
    });

    await waitFor(() => expect(result.current.data).toBeDefined());

    const identity = result.current.data?.get(ACME);
    expect(identity?.name).toBe('Acme Corporation');
    expect(identity?.source_count).toBe(2);
    // ⛔ The projection hands back the identity itself, never the envelope.
    expect(identity).not.toHaveProperty('kind');
    expect(identity).not.toHaveProperty('account');
  });

  it('🔴 the kind is the ACCOUNT’s, and not a constant the endpoint invented', async () => {
    /**
     * ⚠️ **Two rows with two kinds, in one response.** ⛔ **Asserting only
     * `'company'` would pass on an endpoint that returned `'company'` for
     * everything** — which is exactly the shape B-261 exists to prevent: a
     * preference stored under a guessed type is one a rep cannot get back.
     */
    const { result } = renderHook(() => useAccountEntries(WORKSPACE, [ACME, ADA]), {
      wrapper: wrapper(),
    });

    await waitFor(() => expect(result.current.data).toBeDefined());

    expect(result.current.data?.get(ACME)?.kind).toBe('company');
    expect(result.current.data?.get(ADA)?.kind).toBe('person');
    expect(result.current.data?.get(ACME)?.account.name).toBe('Acme Corporation');
  });

  it('⛔ an account the workspace does not own is absent, never defaulted', async () => {
    /**
     * 📁 [B-1053](../../../docs/BUGS.md) — the identity read once answered for
     * every id in the request, so *"this account is not yours"* and *"nobody
     * has named it"* were the same reply. ⚡ **`kind` must not reintroduce
     * it**: an absent row stays absent rather than arriving with a guessed
     * type, and `null` is what makes Account 360 persist nothing.
     */
    apiRequest.mockResolvedValue([entry(ACME, 'Acme Corporation', 'company')]);

    const { result } = renderHook(() => useAccountEntries(WORKSPACE, [ACME, ADA]), {
      wrapper: wrapper(),
    });

    await waitFor(() => expect(result.current.data).toBeDefined());

    expect(result.current.data?.has(ACME)).toBe(true);
    expect(result.current.data?.get(ADA)).toBeUndefined();
  });
});

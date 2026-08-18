/**
 * Whether the shell knows who is actually signed in.
 *
 * **A `TODO(M2.1)` hardcoded `owner` for everybody, for four milestones.** Its
 * stated reason — that resolving a real role needed a `GET /workspaces/{id}/me`
 * that does not exist — was **not true of the data**: `Membership` already
 * carries `user_id` and `role`, so the hook read the members list and searched
 * it for the viewer.
 *
 * 🔴 **[B-284](../../docs/BUGS.md) — and that is where the real premise was
 * wrong.** The members list is a **page**: 50 rows, newest-first. **The
 * 51st-oldest member is not on it**, and searching a page you are not on
 * resolves to *"not a member"* — so an owner of a 51-person workspace was shown
 * *"Settings — restricted. Requires an owner."* and redirected off their own
 * screens. **The `/me` endpoint the TODO asked for was the right answer after
 * all**; what was wrong was the reason given for skipping it.
 *
 * **These assert presentation, never authorization.** Casbin on the server is
 * the decision (§20c); what is tested here is that the product stops offering a
 * member controls the server will refuse.
 */
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiRequest = vi.hoisted(() => vi.fn());

vi.mock('@/lib/api/client', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/lib/api/client')>()),
  apiRequest,
}));

import { useViewerRole } from '@/lib/query/hooks/team';

const WORKSPACE = 'aaaaaaaa-1111-4111-8111-111111111111';
const ME = 'user-me';

/** What `GET /workspaces/{id}/members/me` answers. */
function standing(role: 'owner' | 'member') {
  return { workspace_id: WORKSPACE, user_id: ME, role };
}

beforeEach(() => {
  apiRequest.mockReset();
});

describe('the signed-in role is read, not assumed', () => {
  it('resolves an owner as an owner', async () => {
    apiRequest.mockResolvedValue(standing('owner'));

    const { result } = renderHook(() => useViewerRole(WORKSPACE, ME), { wrapper });

    await waitFor(() => expect(result.current.resolved).toBe(true));
    expect(result.current.role).toBe('owner');
  });

  it('resolves a member as a member, which is the whole point', async () => {
    // The hardcoded value was `owner`, so this is the case that was wrong for
    // every non-owner in the product.
    apiRequest.mockResolvedValue(standing('member'));

    const { result } = renderHook(() => useViewerRole(WORKSPACE, ME), { wrapper });

    await waitFor(() => expect(result.current.resolved).toBe(true));
    expect(result.current.role).toBe('member');
  });

  it('asks for its own standing, never for the roster — B-284', async () => {
    /**
     * **The regression, stated as the request that is made.**
     *
     * A role read out of `GET .../members` is a role read out of *one page* of
     * it, and no assertion about the answer can distinguish a workspace of
     * three from a workspace of fifty-one. **What can be asserted is which
     * question was asked**, and the only question whose answer does not depend
     * on how many colleagues somebody has is this one.
     */
    apiRequest.mockResolvedValue(standing('owner'));

    const { result } = renderHook(() => useViewerRole(WORKSPACE, ME), { wrapper });
    await waitFor(() => expect(result.current.resolved).toBe(true));

    expect(apiRequest).toHaveBeenCalledTimes(1);
    expect(apiRequest.mock.calls[0]?.[0]).toBe(`/workspaces/${WORKSPACE}/members/me`);
    // ⛔ Not the roster, under any query string. A hook that fetched both would
    // pass every assertion above and still page.
    expect(
      apiRequest.mock.calls.some((call) => String(call[0]).endsWith('/members')),
    ).toBe(false);
  });
});

describe('unknown is distinct from none', () => {
  it('is unresolved while the answer is still in flight', () => {
    // **The distinction that matters.** `RouteGuard` fails closed and
    // *redirects*; treating "still loading" as "no role" would bounce an owner
    // off Settings in the moment before their own membership arrived.
    apiRequest.mockReturnValue(new Promise(() => {}));

    const { result } = renderHook(() => useViewerRole(WORKSPACE, ME), { wrapper });

    expect(result.current.resolved).toBe(false);
    expect(result.current.role).toBeNull();
  });

  it('resolves to no role when the request fails', async () => {
    // Fail closed: the alternative is showing controls on the strength of a
    // request that did not happen.
    apiRequest.mockRejectedValue(new Error('network down'));

    const { result } = renderHook(() => useViewerRole(WORKSPACE, ME), { wrapper });

    await waitFor(() => expect(result.current.resolved).toBe(true));
    expect(result.current.role).toBeNull();
  });

  it('resolves immediately when there is no workspace to have a role in', () => {
    // Otherwise a signed-in person with no organization waits forever on a
    // query that is disabled and will never run.
    const { result } = renderHook(() => useViewerRole(null, ME), { wrapper });

    expect(result.current.resolved).toBe(true);
    expect(result.current.role).toBeNull();
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('resolves to no role for somebody who is not a member', async () => {
    // The workspace boundary refuses a stranger before the handler runs, so
    // what reaches this hook is a rejection rather than an empty answer.
    apiRequest.mockRejectedValue(new Error('forbidden'));

    const { result } = renderHook(() => useViewerRole(WORKSPACE, ME), { wrapper });

    await waitFor(() => expect(result.current.resolved).toBe(true));
    expect(result.current.role).toBeNull();
  });
});

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

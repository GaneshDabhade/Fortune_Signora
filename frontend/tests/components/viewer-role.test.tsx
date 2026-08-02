/**
 * Whether the shell knows who is actually signed in.
 *
 * **A `TODO(M2.1)` hardcoded `owner` for everybody, for four milestones.** Its
 * stated reason — that resolving a real role needed a `GET /workspaces/{id}/me`
 * that does not exist — was **not true**: `Membership` already carries
 * `user_id` and `role`, the members endpoint already returns them, and the
 * session already carries the signed-in user's id.
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
const SOMEBODY_ELSE = 'user-other';

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

function members(...rows: { user_id: string; role: 'owner' | 'member' }[]) {
  return {
    items: rows.map((row, index) => ({
      id: `m${index}`,
      workspace_id: WORKSPACE,
      created_at: '2026-08-01T09:00:00Z',
      ...row,
    })),
    next_cursor: null,
    has_more: false,
  };
}

beforeEach(() => {
  apiRequest.mockReset();
});

describe('the signed-in role is read, not assumed', () => {
  it('resolves an owner as an owner', async () => {
    apiRequest.mockResolvedValue(members({ user_id: ME, role: 'owner' }));

    const { result } = renderHook(() => useViewerRole(WORKSPACE, ME), { wrapper });

    await waitFor(() => expect(result.current.resolved).toBe(true));
    expect(result.current.role).toBe('owner');
  });

  it('resolves a member as a member, which is the whole point', async () => {
    // The hardcoded value was `owner`, so this is the case that was wrong for
    // every non-owner in the product.
    apiRequest.mockResolvedValue(
      members({ user_id: SOMEBODY_ELSE, role: 'owner' }, { user_id: ME, role: 'member' }),
    );

    const { result } = renderHook(() => useViewerRole(WORKSPACE, ME), { wrapper });

    await waitFor(() => expect(result.current.resolved).toBe(true));
    expect(result.current.role).toBe('member');
  });

  it('finds the viewer among many, not the first row', async () => {
    apiRequest.mockResolvedValue(
      members(
        { user_id: 'a', role: 'owner' },
        { user_id: 'b', role: 'owner' },
        { user_id: ME, role: 'member' },
      ),
    );

    const { result } = renderHook(() => useViewerRole(WORKSPACE, ME), { wrapper });

    await waitFor(() => expect(result.current.resolved).toBe(true));
    expect(result.current.role).toBe('member');
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
    apiRequest.mockResolvedValue(members({ user_id: SOMEBODY_ELSE, role: 'owner' }));

    const { result } = renderHook(() => useViewerRole(WORKSPACE, ME), { wrapper });

    await waitFor(() => expect(result.current.resolved).toBe(true));
    expect(result.current.role).toBeNull();
  });
});

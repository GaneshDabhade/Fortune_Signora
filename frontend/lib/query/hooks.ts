'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import type {
  AccountAttention,
  AccountIdentity,
  AccountOpportunity,
  AccountScore,
  CursorPage,
  Workspace,
} from '@/lib/api/types';
import { ApiError, apiRequest } from '@/lib/api/client';
import { queryKeys } from '@/lib/query/keys';

/**
 * Query hooks for the endpoints that exist today.
 *
 * Deliberately thin and deliberately few: Workspace & Tenancy is the only
 * shipped module, so these are the only real endpoints. Hooks for business
 * resources arrive with those resources, built against real domain
 * contracts rather than guessed shapes.
 */

export function useWorkspaces() {
  return useQuery({
    queryKey: queryKeys.workspaces(),
    queryFn: () => apiRequest<CursorPage<Workspace>>('/workspaces'),
  });
}

export function useWorkspace(workspaceId: string | null) {
  return useQuery({
    queryKey: queryKeys.workspace(workspaceId ?? ''),
    queryFn: () =>
      apiRequest<Workspace>(`/workspaces/${workspaceId}`, {
        workspaceId: workspaceId ?? undefined,
      }),
    enabled: workspaceId !== null,
  });
}

/**
 * Accounts worth attention, most pressing first.
 *
 * One page, no infinite scroll: the list is a **triage surface**, and a
 * seller who needs to scroll past fifty accounts has a prioritisation
 * problem the product should be solving rather than a paging one.
 */
export function useAccounts(workspaceId: string | null) {
  return useQuery({
    queryKey: queryKeys.accounts(workspaceId ?? ''),
    queryFn: () =>
      apiRequest<CursorPage<AccountAttention>>(`/workspaces/${workspaceId}/accounts`, {
        workspaceId: workspaceId ?? undefined,
      }),
    enabled: workspaceId !== null,
  });
}

/**
 * Names for a set of accounts, in one request.
 *
 * **A second request rather than a field on the list, and that is
 * architectural.** No module may reach both workflow and entity names, so the
 * two are composed here. Batched by design: naming fifty rows one at a time is
 * fifty round trips.
 *
 * Returns a lookup rather than an array, because every caller joins it to rows
 * it already has.
 */
export function useAccountIdentities(workspaceId: string | null, accountIds: string[]) {
  const ids = [...new Set(accountIds)].sort();

  return useQuery({
    queryKey: queryKeys.identities(workspaceId ?? '', ids),
    queryFn: async () => {
      const query = ids.map((id) => `ids=${encodeURIComponent(id)}`).join('&');
      const identities = await apiRequest<AccountIdentity[]>(
        `/workspaces/${workspaceId}/account-identities?${query}`,
        { workspaceId: workspaceId ?? undefined },
      );
      return new Map(identities.map((identity) => [identity.account_id, identity]));
    },
    // Nothing to ask about, so nothing is asked — an empty request would be a
    // round trip whose answer is known.
    enabled: workspaceId !== null && ids.length > 0,
    // Names change far more slowly than scores. Holding them longer keeps a
    // list from re-requesting identities that cannot have moved.
    staleTime: 5 * 60_000,
  });
}

/**
 * One account's score, with the ledger that produced it.
 *
 * **Never retried on a 404.** An account that has never been scored is a
 * settled answer, not a transient failure, and retrying it three times before
 * showing the empty state makes a fast truthful response look like a slow
 * broken one.
 */
export function useAccountScore(workspaceId: string | null, accountId: string | null) {
  return useQuery({
    queryKey: queryKeys.accountScore(workspaceId ?? '', accountId ?? ''),
    queryFn: () =>
      apiRequest<AccountScore>(`/workspaces/${workspaceId}/accounts/${accountId}/score`, {
        workspaceId: workspaceId ?? undefined,
      }),
    enabled: workspaceId !== null && accountId !== null,
    retry: (attempt, error) =>
      !(error instanceof ApiError && error.status === 404) && attempt < 2,
  });
}

/**
 * What Signora committed to about one account, and what has happened since.
 *
 * **Not folded into `useAccountScore`.** The score belongs to the Buying Score
 * Engine and the commitment to the Opportunity Engine; no module in the
 * ratified graph reaches both, so the brief composes them here — the same
 * reason names arrive separately (37-product-surface.md §7).
 *
 * Not retried on a 404: an account with nothing open is a settled answer, and
 * retrying makes a fast truthful response look like a slow broken one.
 */
export function useAccountOpportunity(
  workspaceId: string | null,
  accountId: string | null,
) {
  return useQuery({
    queryKey: queryKeys.accountOpportunity(workspaceId ?? '', accountId ?? ''),
    queryFn: () =>
      apiRequest<AccountOpportunity>(
        `/workspaces/${workspaceId}/accounts/${accountId}/opportunity`,
        { workspaceId: workspaceId ?? undefined },
      ),
    enabled: workspaceId !== null && accountId !== null,
    retry: (attempt, error) =>
      !(error instanceof ApiError && error.status === 404) && attempt < 2,
  });
}

export function useCreateWorkspace() {
  const client = useQueryClient();

  return useMutation({
    mutationFn: (name: string) =>
      apiRequest<Workspace>('/workspaces', { method: 'POST', body: { name } }),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: queryKeys.workspaces() });
    },
  });
}

/**
 * Drops every cached entry belonging to a workspace.
 *
 * Called when the active workspace changes. Without it, a switch leaves
 * the previous tenant's data on screen under the new tenant's header until
 * each query independently goes stale — which looks exactly like a data
 * leak to anyone who sees it, and is indistinguishable from one in a
 * screenshot.
 */
export function useInvalidateWorkspaceScope() {
  const client = useQueryClient();

  return (workspaceId: string) =>
    client.invalidateQueries({ queryKey: queryKeys.workspaceScope(workspaceId) });
}

'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import type { AccountAttention, CursorPage, Workspace } from '@/lib/api/types';
import { apiRequest } from '@/lib/api/client';
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

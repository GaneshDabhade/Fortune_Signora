'use client';

/**
 * Query hooks for the Connection Center.
 *
 * Its own file, on the precedent `commercial.ts` set: adding a file is a use of
 * the frozen foundation rather than a change to it (§20c).
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiRequest } from '@/lib/api/client';
import type { Connection, IntegrationSystem } from '@/lib/api/types';
import { queryKeys } from '@/lib/query/keys';

/**
 * Every system Signora understands, with what this organization has of it.
 *
 * **Not paginated and not filtered.** A customer connects a handful of systems,
 * and the row that matters most is often the one they have *not* connected.
 */
export function useIntegrations(workspaceId: string | null) {
  return useQuery({
    queryKey: queryKeys.integrations(workspaceId ?? ''),
    enabled: Boolean(workspaceId),
    queryFn: () => apiRequest<IntegrationSystem[]>(`/workspaces/${workspaceId}/integrations`),
  });
}

export interface DisconnectResult {
  state: string;
  /** Whether the other system was told. False means the customer may still
   * want to remove Signora on that system's side, which the screen says. */
  revoked_at_provider: boolean;
  already_disconnected: boolean;
}

/**
 * Stop using a connected system.
 *
 * **No optimistic update.** Disconnecting is a security action, and showing it
 * as done before the server agrees would tell somebody their access was
 * withdrawn while it might not have been. The list is refetched instead — the
 * extra round trip costs a moment and buys a screen that is never wrong about
 * this.
 */
export function useDisconnect(workspaceId: string | null) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (connectionId: string) =>
      apiRequest<DisconnectResult>(
        `/workspaces/${workspaceId}/connections/${connectionId}/disconnect`,
        { method: 'POST' },
      ),
    onSuccess: () => {
      void client.invalidateQueries({
        queryKey: queryKeys.integrations(workspaceId ?? ''),
      });
    },
  });
}

/**
 * Check whether a connected system still works.
 *
 * **Not a read, which is why it is a mutation.** It spends a call against the
 * customer's own API quota and records the result, and a `GET` that did that
 * would be a `GET` a proxy could repeat.
 *
 * **A failed check resolves rather than rejects.** The server answers `200`
 * with the connection reading *not working*, because the customer's system
 * saying no is not Signora failing — and a screen that showed an error toast
 * for it would be blaming the wrong party.
 */
export function useCheckConnection(workspaceId: string | null) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (connectionId: string) =>
      apiRequest<Connection>(
        `/workspaces/${workspaceId}/connections/${connectionId}/check`,
        { method: 'POST' },
      ),
    onSuccess: () => {
      // Refetched rather than patched in place. Health is derived from the run
      // of probes, not from the one that just happened, so the authoritative
      // answer is the server's.
      void client.invalidateQueries({
        queryKey: queryKeys.integrations(workspaceId ?? ''),
      });
    },
  });
}

'use client';

/**
 * Query hooks for the Connection Center.
 *
 * Its own file, on the precedent `commercial.ts` set: adding a file is a use of
 * the frozen foundation rather than a change to it (§20c).
 */

import { useQuery } from '@tanstack/react-query';

import { apiRequest } from '@/lib/api/client';
import type { IntegrationSystem } from '@/lib/api/types';
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

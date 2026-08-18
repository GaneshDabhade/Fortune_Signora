/**
 * **What this person opened, and recording that they opened it** —
 * 📁 `Fortune Signora Session Continuity.dc.html`, **tier 4 · work context**.
 *
 * 📁 **Read by Home's `card.recents`** — *"Pick up where you left off · last
 * five records touched · context, never urgent."*
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiRequest } from '@/lib/api/client';
import type { ViewedRecord } from '@/lib/api/types';
import { queryKeys } from '@/lib/query/keys';

export function useRecentlyViewed(workspaceId: string | null) {
  return useQuery({
    queryKey: queryKeys.recentlyViewed(workspaceId ?? ''),
    queryFn: () =>
      apiRequest<ViewedRecord[]>(`/workspaces/${workspaceId}/recently-viewed`, {
        workspaceId: workspaceId ?? undefined,
      }),
    enabled: workspaceId !== null,
  });
}

/**
 * **Record that this person opened a record.**
 *
 * ⛔ **Fire-and-forget, and deliberately so.** 📁 Session Continuity's tier 4 is
 * *"silent where it only informs a list (recents)"* — **a person opening an
 * account must never wait on, or be interrupted by, the bookkeeping that
 * remembers they did.** ⚡ A failure here costs one row in a context card; it
 * must not cost the navigation.
 *
 * ⚡ **The list is invalidated on success**, so returning to Home shows the
 * record without a reload.
 */
export function useRecordView(workspaceId: string | null) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (record: { entityId: string; kind: ViewedRecord['kind'] }) =>
      apiRequest<void>(`/workspaces/${workspaceId}/recently-viewed`, {
        method: 'POST',
        workspaceId: workspaceId ?? undefined,
        body: { entity_id: record.entityId, kind: record.kind },
      }),
    onSuccess: () => {
      void client.invalidateQueries({
        queryKey: queryKeys.recentlyViewed(workspaceId ?? ''),
      });
    },
  });
}

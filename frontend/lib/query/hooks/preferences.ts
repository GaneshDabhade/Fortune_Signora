/**
 * **This person's preferences** — [TASK-1424](../../../../docs/BACKLOG.md).
 *
 * ⚡ **Workspace-scoped, because the record is.** 📁 `person_preferences` is
 * keyed by `(workspace_id, user_id)`, so somebody's answer in one organization
 * is not their answer in another — **and a query key that dropped the workspace
 * would show a returning customer's dismissal to them in a workspace they had
 * just joined.**
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiRequest } from '@/lib/api/client';
import type { PersonPreferences } from '@/lib/api/types';
import { queryKeys } from '@/lib/query/keys';

export function usePreferences(workspaceId: string | null) {
  return useQuery({
    queryKey: queryKeys.preferences(workspaceId ?? ''),
    queryFn: () =>
      apiRequest<PersonPreferences>(`/workspaces/${workspaceId}/preferences`, {
        workspaceId: workspaceId ?? undefined,
      }),
    enabled: workspaceId !== null,
  });
}

/**
 * 📁 ***"Dismissible forever."***
 *
 * ⛔ **No body, because the endpoint takes none.** ⚡ The only two facts are
 * *who* — the caller's verified identity — and *when*, which is the server's
 * clock. **A moment a browser supplied would let it decide when somebody
 * stopped being new.**
 *
 * ✅ **The response IS the new preferences**, so the cache is set from what the
 * server returned rather than invalidated and re-fetched. ⚡ **One round trip,
 * and no window in which the overlay reappears** between the write landing and
 * the read coming back.
 */
export function useDismissFirstRun(workspaceId: string | null) {
  const client = useQueryClient();

  return useMutation({
    mutationFn: () =>
      apiRequest<PersonPreferences>(
        `/workspaces/${workspaceId}/preferences/first-run-dismissal`,
        { method: 'POST', workspaceId: workspaceId ?? undefined },
      ),
    onSuccess: (preferences) => {
      client.setQueryData(queryKeys.preferences(workspaceId ?? ''), preferences);
    },
  });
}

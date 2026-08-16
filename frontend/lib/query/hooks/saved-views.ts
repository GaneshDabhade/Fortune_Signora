import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiRequest } from '@/lib/api/client';
import type { CursorPage, SavedView } from '@/lib/api/types';
import { queryKeys } from '@/lib/query/keys';

/**
 * **The views this organization shares** — `GET /workspaces/{id}/saved-views`.
 *
 * ## 📁 The design's tab row
 *
 * **The finalized Companies design opens with a row of saved views** — *My
 * at-risk renewals · EMEA enterprise · Whitespace · Board extract · All
 * companies* — **and this is the read behind it.**
 *
 * ## ⚡ Shared, and that is the endpoint's own word
 *
 * 📁 *"Everybody in the workspace sees the same list… there is deliberately no
 * **my views** filter, because filtering by author would make a shared
 * capability read as a private one."* ⛔ **So the tabs are not per-person**,
 * and the screen must not imply they are.
 *
 * ## ⛔ What this read does NOT carry, and the tabs must not invent
 *
 * 📁 **The design prints a count on every tab** — *41 · 312 · 1,104* — **and a
 * badge on some** — *Live · AI · Shared*. ⚠️ **`SavedViewResponse` publishes
 * neither.** A count needs the view's `declaration` executed against the book,
 * which no endpoint offers; **a badge is a classification nothing stores.**
 *
 * ✅ **The tabs render without them** rather than not rendering at all — 📁 the
 * product owner's ruling: *"do not invent tab counts if they aren't supplied,
 * but do not omit the entire tab system just because some metadata is
 * unavailable."*
 */
export function useSavedViews(workspaceId: string | null) {
  return useQuery({
    queryKey: queryKeys.savedViews(workspaceId ?? ''),
    enabled: workspaceId !== null,
    queryFn: () =>
      apiRequest<CursorPage<SavedView>>(`/workspaces/${workspaceId}/saved-views?limit=50`, {
        workspaceId: workspaceId ?? undefined,
      }),
  });
}


/**
 * **Saving the current view** — `POST /workspaces/{id}/saved-views`.
 *
 * 📁 **The design's *"Save to view"***, on the right of the filter row.
 *
 * ## ⛔ The declaration is the caller's, and this hook never looks inside it
 *
 * 📁 `SaveViewRequest`: *"`declaration` is `dict[str, Any]` and stays that
 * way — a typed schema here would make this module know what a filter is."*
 * ⚡ **The same boundary holds on this side**: the screen builds its own
 * declaration and this hook carries it.
 *
 * ## ⚡ It invalidates the list, because the tab row is that list
 *
 * ⛔ **Not an optimistic insert.** The server assigns the id, the author and
 * the time, **and a tab rendered from a guess would carry none of them** — a
 * refetch is one request and the row is then the real one.
 */
export function useSaveView(workspaceId: string | null) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (view: { name: string; declaration: Record<string, unknown> }) =>
      apiRequest<SavedView>(`/workspaces/${workspaceId}/saved-views`, {
        method: 'POST',
        body: view,
        workspaceId: workspaceId ?? undefined,
      }),
    onSuccess: () =>
      client.invalidateQueries({ queryKey: queryKeys.savedViews(workspaceId ?? '') }),
  });
}

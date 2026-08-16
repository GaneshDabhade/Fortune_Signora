import { useQuery } from '@tanstack/react-query';

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

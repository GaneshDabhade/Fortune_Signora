import { useInfiniteQuery } from '@tanstack/react-query';

import { apiRequest } from '@/lib/api/client';
import type { CursorPage, ListedAccount } from '@/lib/api/types';
import { queryKeys } from '@/lib/query/keys';

/**
 * **Every account this workspace knows, a page at a time** —
 * [TASK-440](../../../../docs/BACKLOG.md), `GET /workspaces/{id}/accounts-list`.
 *
 * ## 🔴 This is a different read from {@link useAccounts}, and the row exists because they were confused
 *
 * ⛔ **`/accounts` is `attention_list`** — 📁 *"accounts worth attention, most
 * pressing first"* — **a ranked, narrowed triage set.** ⚠️ **[446](../../../../docs/architecture/446-companies-traceability-audit.md)
 * described the Companies table as *"every company this workspace watches"* and
 * cited that endpoint**, and 🔴 **it returns open opportunities.** ⚡ **Two
 * lanes reached the same conclusion from opposite ends** —
 * [C-232](../../../../docs/LANE_COORDINATION.md) and this office's own
 * correction — **and [TASK-472](../../../../docs/BACKLOG.md) built the read
 * that was missing.**
 *
 * ## ⛔ Keyset, never offset — and the reason is in the endpoint, not here
 *
 * 📁 **Its own words**: *"the graph is written continuously: a resolution binds
 * a new provider identity and an account appears, so an offset page would skip
 * or repeat rows between two requests and a customer paging the list would
 * silently miss accounts."*
 *
 * ⚡ **`useInfiniteQuery` rather than manual state**, on the pattern
 * [`useAccountTimeline`](timeline.ts) already established: **the cursor is
 * opaque by contract** — pages are walked by echoing back what the last one
 * returned, never by computing anything.
 */
/** ⚡ **Exported because the pager states the row range** — 📁 the design's
 *  *"Rows 1–8 of 312"*. ⛔ **A second constant on the screen would drift from
 *  the one the request actually sends**, and the range would be wrong by
 *  exactly that difference ([§2](../../../CLAUDE.md)). */
export const PAGE_SIZE = 50;

export function useAccountsList(workspaceId: string | null) {
  return useInfiniteQuery({
    queryKey: queryKeys.accountsList(workspaceId ?? ''),
    enabled: workspaceId !== null,
    initialPageParam: null as string | null,
    queryFn: ({ pageParam }) => {
      const query = new URLSearchParams({ limit: String(PAGE_SIZE) });
      if (pageParam) query.set('cursor', pageParam);
      return apiRequest<CursorPage<ListedAccount>>(
        `/workspaces/${workspaceId}/accounts-list?${query}`,
        { workspaceId: workspaceId ?? undefined },
      );
    },
    // ⛔ **`has_more`, never `next_cursor != null`** — the server sends both,
    // and the explicit flag is the one that reads correctly at a page boundary
    // where a cursor exists and there is nothing after it. 📁 The same choice
    // `useAccountTimeline` documents, for the same reason.
    getNextPageParam: (last: CursorPage<ListedAccount>) =>
      last.has_more ? last.next_cursor : undefined,
  });
}
